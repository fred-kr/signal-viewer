import pprint
import re
from collections.abc import Sequence
from typing import Literal, Unpack

import attrs
import neurokit2 as nk
import numpy as np
import numpy.typing as npt
import polars as pl
import polars.selectors as ps
from loguru import logger

from signal_viewer.constants import INDEX_COL, IS_MANUAL_COL, IS_PEAK_COL, SECTION_INDEX_COL
from signal_viewer.enum_defs import (
    IncompleteWindowMethod,
    PeakDetectionAlgorithm,
    PreprocessPipeline,
    RateComputationMethod,
)
from signal_viewer.sv_config import Config
from signal_viewer.sv_data.peak_detection import find_peaks
from signal_viewer.sv_data.signal_processing import apply_cleaning_pipeline, filter_signal, standardize_signal
from signal_viewer.type_defs import (
    DetailedSectionResultDict,
    ManualPeakEditsDict,
    PeakDetectionAlgorithmParameters,
    ProcessingParametersDict,
    RollingRateKwargs,
    SectionMetadataDict,
    SectionResultDict,
    SectionSummaryDict,
    SignalFilterKwargs,
    SignalStandardizeKwargs,
    UpdatePeaksAction,
)
from signal_viewer.utils import sequence_repr


@attrs.define
class ProcessingParameters:
    sampling_rate: int = attrs.field()
    processing_pipeline: PreprocessPipeline | None = attrs.field(default=None)
    filter_parameters: list[SignalFilterKwargs] = attrs.field(factory=list)
    standardization_parameters: SignalStandardizeKwargs | None = attrs.field(default=None)
    peak_detection_method: PeakDetectionAlgorithm | None = attrs.field(default=None)
    peak_detection_method_parameters: PeakDetectionAlgorithmParameters | None = attrs.field(default=None)
    rate_computation_method: RateComputationMethod = attrs.field(default=Config.editing.rate_computation_method)

    def to_dict(self) -> ProcessingParametersDict:
        return {
            "sampling_rate": self.sampling_rate,
            "processing_pipeline": str(self.processing_pipeline),
            "filter_parameters": self.filter_parameters,
            "standardization_parameters": self.standardization_parameters,
            "peak_detection_method": str(self.peak_detection_method),
            "peak_detection_method_parameters": self.peak_detection_method_parameters,
            "rate_computation_method": str(self.rate_computation_method),
        }

    def reset(self, peaks_only: bool = False) -> None:
        if peaks_only:
            self.peak_detection_method = None
            self.peak_detection_method_parameters = None
            return
        self.processing_pipeline = None
        self.filter_parameters = []
        self.standardization_parameters = None
        self.peak_detection_method = None
        self.peak_detection_method_parameters = None
        self.rate_computation_method = Config.editing.rate_computation_method

    def __repr__(self) -> str:
        return pprint.pformat(self.to_dict(), indent=2, width=120, underscore_numbers=True)


@attrs.define
class ManualPeakEdits:
    added: list[int] = attrs.field(factory=list)
    removed: list[int] = attrs.field(factory=list)

    def __repr__(self) -> str:
        return f"Added Peaks [{len(self.added)}]: {sequence_repr(self.added)}\nRemoved Peaks [{len(self.removed)}]: {sequence_repr(self.removed)}"

    def clear(self) -> None:
        self.added.clear()
        self.removed.clear()

    def new_added(self, value: int | Sequence[int] | pl.Series) -> None:
        if isinstance(value, int):
            if value in self.removed:
                self.removed.remove(value)
            else:
                self.added.append(value)
        else:
            for v in value:
                if v in self.removed:
                    self.removed.remove(v)
                else:
                    self.added.append(v)

    def new_removed(self, value: int | Sequence[int] | pl.Series) -> None:
        if isinstance(value, int):
            if value in self.added:
                self.added.remove(value)
            else:
                self.removed.append(value)
        else:
            for v in value:
                if v in self.added:
                    self.added.remove(v)
                else:
                    self.removed.append(v)

    def sort_and_deduplicate(self) -> None:
        self.added = sorted(set(self.added))
        self.removed = sorted(set(self.removed))

    def get_joined(self) -> list[int]:
        return sorted(set(self.added) | set(self.removed))

    def to_dict(self) -> ManualPeakEditsDict:
        self.sort_and_deduplicate()
        return ManualPeakEditsDict(
            added=self.added,
            removed=self.removed,
        )


class SectionID(str):
    def __init__(self, value: str) -> None:
        if not re.match(r"^Section_[a-zA-Z0-9]+_[0-9]{3}$", value):
            raise ValueError(f"SectionID must be of the form 'Section_<signal_name>_000', got '{value}'")
        super().__init__()

    @staticmethod
    def default() -> "SectionID":
        return SectionID("Section_DEFAULT_000")

    def pretty_name(self) -> str:
        """UI friendly name for the section"""
        sig_name = self.split("_")[1]
        return f"Section {self[-3:]} ({sig_name.upper()})"

    def as_num(self) -> int:
        """Get the section number as an int"""
        return int(self.split("_")[2])


@attrs.define
class SectionMetadata:
    signal_name: str = attrs.field()
    section_id: SectionID = attrs.field()
    global_bounds: tuple[int, int] = attrs.field()
    sampling_rate: int = attrs.field()
    processing_parameters: ProcessingParameters = attrs.field()
    rate_computation_method: RateComputationMethod = attrs.field()

    def to_dict(self) -> SectionMetadataDict:
        return SectionMetadataDict(
            signal_name=self.signal_name,
            section_id=self.section_id,
            global_bounds=self.global_bounds,
            sampling_rate=self.sampling_rate,
            processing_parameters=self.processing_parameters.to_dict(),
            rate_computation_method=str(self.rate_computation_method),
        )

    def __repr__(self) -> str:
        return pprint.pformat(self.to_dict(), indent=2, width=120, underscore_numbers=True)


@attrs.define(repr=True)
class SectionResult:
    """
    Stores the detected peaks along with the computed rate data for a single section. Created for each new section.
    """

    peak_data: pl.DataFrame = attrs.field(factory=pl.DataFrame)
    rate_data: pl.DataFrame = attrs.field(factory=pl.DataFrame)
    is_locked: bool = attrs.field(default=False)

    def has_peak_data(self) -> bool:
        return not self.peak_data.is_empty()

    def has_rate_data(self) -> bool:
        return not self.rate_data.is_empty()

    def to_dict(self) -> SectionResultDict:
        return SectionResultDict(
            peak_data=self.peak_data.to_numpy(structured=True),
            rate_data=self.rate_data.to_numpy(structured=True),
        )


@attrs.define(frozen=True, repr=True)
class DetailedSectionResult:
    """
    Class containing detailed information about a section. Created when a complete result is requested by the user.
    """

    metadata: "SectionMetadata" = attrs.field()
    section_dataframe: pl.DataFrame = attrs.field()
    manual_peak_edits: "ManualPeakEdits" = attrs.field()
    section_result: SectionResult = attrs.field()
    rate_per_temperature: pl.DataFrame = attrs.field()

    def to_dict(self) -> DetailedSectionResultDict:
        return DetailedSectionResultDict(
            metadata=self.metadata.to_dict(),
            section_dataframe=self.section_dataframe.to_numpy(structured=True),
            manual_peak_edits=self.manual_peak_edits.to_dict(),
            section_result=self.section_result.to_dict(),
            rate_per_temperature=self.rate_per_temperature.to_numpy(structured=True),
        )


class Section:
    __slots__ = (
        "signal_name",
        "processed_signal_name",
        "info_name",
        "section_id",
        "_is_filtered",
        "_is_standardized",
        "_is_processed",
        "data",
        "sampling_rate",
        "global_bounds",
        "_result_data",
        "_rate_is_synced",
        "_processing_parameters",
        "_manual_peak_edits",
    )

    def __init__(self, data: pl.DataFrame, signal_name: str, info_column: str | None = None) -> None:
        self.signal_name = signal_name
        self.processed_signal_name = f"{self.signal_name}_processed"
        self.info_name = info_column
        self.section_id = SectionID.default()
        self._is_filtered: bool = False
        self._is_standardized: bool = False
        self._is_processed: bool = False  # flag to indicate if the section has been processed using a pipeline

        if SECTION_INDEX_COL in data.columns:
            data.drop_in_place(SECTION_INDEX_COL)

        self.data = (
            data.with_row_index(SECTION_INDEX_COL)
            .lazy()
            .select(ps.by_name(INDEX_COL, SECTION_INDEX_COL).cast(pl.Int32), ~ps.by_name(INDEX_COL, SECTION_INDEX_COL))
            .set_sorted(INDEX_COL)
            .set_sorted(SECTION_INDEX_COL)
            .with_columns(
                pl.col(signal_name).alias(self.processed_signal_name),
                pl.lit(0, pl.Int8).alias(IS_PEAK_COL),
                pl.lit(0, pl.Int8).alias(IS_MANUAL_COL),
            )
            .collect()
        )

        self.sampling_rate = Config.internal.last_sampling_rate
        self.global_bounds: tuple[int, int] = (
            self.data.item(0, INDEX_COL),
            self.data.item(-1, INDEX_COL),
        )

        self._rate_is_synced = False

        self._result_data = SectionResult()

        self._processing_parameters = ProcessingParameters(self.sampling_rate)
        self._manual_peak_edits = ManualPeakEdits()

    @property
    def rate_data(self) -> pl.DataFrame:
        return self._result_data.rate_data

    @rate_data.setter
    def rate_data(self, value: pl.DataFrame) -> None:
        if self._result_data.is_locked:
            logger.warning(
                "Unable to update rate data because the section is locked. Please unlock the section and try again."
            )
            return
        self._result_data.rate_data = value

    @property
    def peak_data(self) -> pl.DataFrame:
        return self._result_data.peak_data

    @peak_data.setter
    def peak_data(self, value: pl.DataFrame) -> None:
        if self._result_data.is_locked:
            logger.warning(
                "Unable to update peak data because the section is locked. Please unlock the section and try again."
            )
            return
        self._result_data.peak_data = value

    @property
    def is_locked(self) -> bool:
        return self._result_data.is_locked

    def set_locked(self, value: bool) -> None:
        self._result_data.is_locked = value

    @property
    def n_filters(self) -> int:
        return len(self._processing_parameters.filter_parameters)

    @property
    def raw_signal(self) -> pl.Series:
        """The raw (unprocessed) signal data for the section."""
        return self.data.get_column(self.signal_name)

    @property
    def processed_signal(self) -> pl.Series:
        """The processed (filtered, standardized, etc) signal data for the section."""
        return self.data.get_column(self.processed_signal_name)

    @property
    def is_filtered(self) -> bool:
        """Flag indicating if the section values were processed using a custom filter."""
        return self._is_filtered

    @property
    def is_standardized(self) -> bool:
        """Flag indicating if the section values were standardized."""
        return self._is_standardized

    @property
    def is_processed(self) -> bool:
        """Flag indicating if the section values were processed using a pipeline."""
        return self._is_processed

    @property
    def peaks_local(self) -> pl.Series:
        """Returns the indices of the peaks in the processed signal."""
        return (
            self.data.lazy()
            .filter(pl.col(IS_PEAK_COL) == 1)
            .select(SECTION_INDEX_COL)
            .collect()
            .get_column(SECTION_INDEX_COL)
        )

    @property
    def peaks_global(self) -> pl.Series:
        """Returns the indices of the peaks relative to the entire signal."""
        return self.data.lazy().filter(pl.col(IS_PEAK_COL) == 1).select(INDEX_COL).collect().get_column(INDEX_COL)

    @property
    def manual_peak_edits(self) -> ManualPeakEdits:
        """Object holding information about manually added/removed peaks."""
        self._manual_peak_edits.sort_and_deduplicate()
        return self._manual_peak_edits

    @logger.catch(message="Signal filtering failed. Please check the parameters and try again.")
    def filter_signal(
        self,
        pipeline: PreprocessPipeline | None = None,
        **kwargs: Unpack[SignalFilterKwargs],
    ) -> None:
        """
        Filter this section's signal using the specified pipeline / custom filter parameters.

        Parameters
        ----------
        pipeline : PreprocessPipeline | None, optional
            The filter pipeline to apply, by default None

        The keyword arguments are used to apply a custom filter to the signal if pipeline is None:

        lowcut : float | None
            The lower cutoff frequency for the filter, by default None
        highcut : float | None
            The upper cutoff frequency for the filter, by default None
        method : str
            Which filter method to use, see `neurokit2.signal_filter` for more information
        order : int
            The filter order to use
        window_size : int | "default"
            The window size to use for FIR filters
        powerline : int | float
            The powerline frequency to use, only used with method="powerline"
        """
        allow_stacking = Config.editing.filter_stacking
        if self.is_filtered and not allow_stacking:
            logger.warning(
                "Applying filter to raw signal. To apply to already processed signal, enable\n\n'Settings > Preferences > Editing > FilterStacking'."
            )
            sig_data = self.raw_signal.to_numpy(allow_copy=False)
        else:
            sig_data = self.processed_signal.to_numpy(allow_copy=False)
        method = kwargs.get("method", None)
        filter_params: SignalFilterKwargs = {}
        additional_params: SignalFilterKwargs | None = None

        if pipeline is None:
            self._processing_parameters.processing_pipeline = pipeline
            if method is None:
                filtered = sig_data
            else:
                filtered, filter_params = filter_signal(sig_data, self.sampling_rate, **kwargs)
                self._is_filtered = True
        else:
            result = apply_cleaning_pipeline(sig_data, self.sampling_rate, pipeline)
            filtered = result.cleaned
            filter_params = result.parameters
            additional_params = result.additional_parameters
            self._is_processed = True

        self._processing_parameters.processing_pipeline = pipeline
        self._processing_parameters.filter_parameters.append(filter_params)
        if additional_params is not None:
            self._processing_parameters.filter_parameters.append(additional_params)

        self.data = self.data.with_columns(pl.Series(self.processed_signal_name, filtered))

    def standardize_signal(self, **kwargs: Unpack[SignalStandardizeKwargs]) -> None:
        """
        Standardize this section's signal using the specified parameters. Based on `neurokit2.standardize`.

        Parameters
        ----------
        robust : bool
            If True, uses median absolute deviation (MAD) instead of standard deviation
        window_size : int
            If using rolling standardization, the window size to use
        """
        if self._is_standardized:
            logger.warning("Signal is already standardized. Skipping standardization.")
            return
        window_size = kwargs.get("window_size", None)
        robust = kwargs.get("robust", False)
        if robust and window_size:
            window_size = None

        standardized = standardize_signal(self.processed_signal, robust=robust, window_size=window_size)

        self.data = self.data.with_columns(
            standardized.replace([float("inf"), float("-inf")], None)
            .fill_nan(None)
            .fill_null(strategy="backward")
            .alias(self.processed_signal_name)
        )
        self._is_standardized = True

        self._processing_parameters.standardization_parameters = kwargs

    @logger.catch(message="Peak detection failed. Please check the parameters and try again.")
    def detect_peaks(
        self,
        method: PeakDetectionAlgorithm,
        method_parameters: PeakDetectionAlgorithmParameters,
        *,
        rr_params: RollingRateKwargs | None = None,
    ) -> None:
        """
        Find peaks in the processed signal using the specified method and parameters.

        Parameters
        ----------
        method : PeakDetectionMethod
            The method to use for peak detection
        method_parameters : PeakDetectionAlgorithmParameters
            The parameters to use for the peak detection method
        """
        peaks = find_peaks(
            self.processed_signal.to_numpy(allow_copy=False),
            self.sampling_rate,
            method,
            method_parameters,
        )

        self._processing_parameters.peak_detection_method = method
        self._processing_parameters.peak_detection_method_parameters = method_parameters

        self.set_peaks(peaks, rr_params=rr_params)

    def set_peaks(
        self,
        peaks: npt.NDArray[np.intp],
        update_rate: bool = True,
        *,
        rr_params: RollingRateKwargs | None = None,
    ) -> None:
        """
        Sets the `is_peak` column in `self.data` to 1 at the indices provided in `peaks`, and to 0
        everywhere else.

        Parameters
        ----------
        peaks : NDArray[np.int32]
            A 1D array of integers representing the indices of the peaks in the processed signal.
        update_rate : bool
            Whether to recalculate the signal rate based on the new peaks. Defaults to True.
        """
        peaks = peaks[peaks >= 0]

        pl_peaks = pl.Series("", peaks, pl.Int32)

        self.data = self.data.with_columns(
            pl.when(pl.col(SECTION_INDEX_COL).is_in(pl_peaks))
            .then(pl.lit(1))
            .otherwise(pl.lit(0))
            .cast(pl.Int8)
            .alias(IS_PEAK_COL)
        )

        self.manual_peak_edits.clear()
        self._rate_is_synced = False
        if update_rate:
            self.update_rate_data(rr_params=rr_params)

    def update_peaks(
        self,
        action: UpdatePeaksAction,
        peaks: npt.NDArray[np.intp],
        update_rate: bool = True,
        *,
        rr_params: RollingRateKwargs | None = None,
    ) -> None:
        """
        Updates the `is_peak` column in `self.data` at the given indices according to the provided
        action, while keeping the rest of the column values the same.

        Parameters
        ----------
        action : {"add", "remove"}
            How the peaks should be updated:
            - "add" : Set the `is_peak` column to 1 at the indices provided in `peaks`.
            - "remove" : Set the `is_peak` column to 0 at the indices provided in `peaks`.

        peaks : ndarray
            A 1D array of integers representing the indices of the peaks in the processed signal.
        update_rate : bool
            Whether to recalculate the signal rate based on the new peaks. Defaults to True.

        """
        pl_peaks = pl.Series("peaks", peaks, pl.Int32)
        then_value = 1 if action in ["a", "add"] else 0

        updated_data = (
            self.data.lazy()
            .select(
                pl.when(pl.col(SECTION_INDEX_COL).is_in(pl_peaks))
                .then(pl.lit(then_value))
                .otherwise(pl.col(IS_PEAK_COL))
                .cast(pl.Int8)
                .alias(IS_PEAK_COL)
            )
            .collect()
            .get_column(IS_PEAK_COL)
        )

        changed_indices = pl.arg_where(updated_data != self.data.get_column(IS_PEAK_COL), eager=True)

        self.data = self.data.with_columns(is_peak=updated_data)

        if action == "add":
            self.manual_peak_edits.new_added(changed_indices)
        else:
            self.manual_peak_edits.new_removed(changed_indices)

        self._rate_is_synced = False
        if update_rate and self.peaks_local.len() > 3:
            self.update_rate_data(rr_params=rr_params)

    def update_rate_data(
        self, full_info: bool = False, force: bool = False, *, rr_params: RollingRateKwargs | None = None
    ) -> None:
        """
        Recalculates the signal rate based on the current peaks.

        Parameters
        ----------
        full_info : bool, optional
            If True, calculates summary statistics in addition to the rate, by default False
        force : bool, optional
            If True, recalculates the rate even if the `_rate_is_synced` flag is True, by default False
        rr_params : dict, optional
            Additional parameters to pass to the `rolling_rate` function, by default None
        """
        if not force and (self._rate_is_synced or self.is_locked):
            logger.debug("Rate data is already up to date.")
            return

        method = Config.editing.rate_computation_method
        if method == RateComputationMethod.RollingWindow:
            if rr_params is None:
                rr_params = {}
            self._calc_rate_rolling(full_info=full_info, **rr_params)
        elif method == RateComputationMethod.Instantaneous:
            self._calc_rate_instant()

        self._rate_is_synced = True

    def _calc_rate_instant(self, desired_length: int | None = None) -> None:
        """
        Calculate signal rate (per minute) from the detected peaks. See `neurokit2.signal_rate` for more details.

        Parameters
        ----------
        desired_length : int, optional
            The desired length of the output array, by default None. See `neurokit2.signal_rate` for more details.
        """
        peaks = self.peaks_local.to_numpy()
        if peaks.shape[0] < 2:
            logger.warning(
                "The currently selected peak detection method finds less than 2 peaks. "
                "Please change the current methods parameters (if available), or use "
                "a different method."
            )
            return
        if desired_length is None:
            desired_length = len(self.processed_signal)
        inst_rate = nk.signal_rate(peaks, sampling_rate=self.sampling_rate, desired_length=desired_length)  # type: ignore

        self.rate_data = pl.DataFrame(
            {SECTION_INDEX_COL: self.data.get_column(SECTION_INDEX_COL), "rate_bpm": inst_rate},
            schema_overrides={SECTION_INDEX_COL: pl.Int32, "rate_bpm": pl.Float64},
        )

    def _calc_rate_rolling(
        self,
        grp_col: str = SECTION_INDEX_COL,
        sec_new_window_every: int = 10,
        sec_window_length: int = 60,
        sec_start_at: int = 0,
        full_info: bool = False,
        label: Literal["left", "right", "datapoint"] = "datapoint",
        incomplete_window_method: IncompleteWindowMethod = IncompleteWindowMethod.Drop,
    ) -> None:
        sampling_rate = self.sampling_rate

        every = sec_new_window_every * sampling_rate
        period = sec_window_length * sampling_rate
        offset = sec_start_at * sampling_rate

        samples_in_minute = 60 * sampling_rate
        peaks_in_window_to_peaks_per_minute = samples_in_minute / period
        # Sampling rate: 400 Hz, window length: 90 seconds:
        # samples_in_minute = 60 * 400 = 24000
        # period = 90 * 400 = 36000
        # peaks_in_window_to_peaks_per_minute = 24000 / 36000 = 0.666
        # rate_bpm = peaks_in_window * 0.666

        rr_df = (
            self.data.lazy()
            .sort(grp_col)
            .with_columns(pl.col(grp_col).cast(pl.Int64))
            .group_by_dynamic(
                pl.col(grp_col),
                every=f"{every}i",
                period=f"{period}i",
                offset=f"{offset}i",
                label=label,
            )
        )
        if (self.info_name in self.data.columns) and full_info:
            info_col = self.info_name
            rr_df = rr_df.agg(
                pl.sum(IS_PEAK_COL).alias("peaks_in_window"),
                pl.len().alias("rows_in_window"),
                pl.mean(info_col).round(1).name.suffix("_mean"),
                pl.std(info_col).name.suffix("_std"),
                pl.min(info_col).name.suffix("_min"),
                pl.max(info_col).name.suffix("_max"),
                pl.var(info_col).name.suffix("_var"),
            )
        else:
            rr_df = rr_df.agg(
                pl.sum(IS_PEAK_COL).alias("peaks_in_window"),
                pl.len().alias("rows_in_window"),
            )

        if incomplete_window_method == IncompleteWindowMethod.Drop:
            rr_df = rr_df.filter(pl.col("rows_in_window") == period).with_columns(
                (pl.col("peaks_in_window") * peaks_in_window_to_peaks_per_minute).alias("rate_bpm")
            )
        elif incomplete_window_method == IncompleteWindowMethod.Approximate:
            rr_df = rr_df.with_columns(
                (
                    (pl.col("peaks_in_window") * period / pl.col("rows_in_window"))
                    * peaks_in_window_to_peaks_per_minute
                ).alias("rate_bpm")
            )
        elif incomplete_window_method == IncompleteWindowMethod.RepeatLast:
            rr_df = rr_df.with_columns(
                (
                    pl.when(pl.col("rows_in_window") != period).then(None).otherwise(pl.col("peaks_in_window"))
                    * peaks_in_window_to_peaks_per_minute
                ).alias("rate_bpm")
            ).with_columns(pl.col("rate_bpm").forward_fill())

        if not full_info:
            rr_df = rr_df.select(
                pl.col(grp_col).cast(pl.Int32),
                pl.col("rate_bpm").cast(pl.Float64),
            )

        self.rate_data = rr_df.collect().shrink_to_fit()

    def get_mean_rate_per_temperature(self) -> pl.DataFrame:
        info_col = self.info_name
        return (
            self.rate_data.group_by(pl.col(f"{info_col}_mean").round(1))
            .agg(
                pl.mean("rate_bpm").alias("rate_mean"),
                pl.median("rate_bpm").alias("rate_median"),
                pl.std("rate_bpm").alias("rate_std"),
                pl.min("rate_bpm").alias("rate_min"),
                pl.max("rate_bpm").alias("rate_max"),
            )
            .sort(f"{info_col}_mean")
        )

    def _add_manual_peak_edits_column(self) -> None:
        pl_added = pl.Series("added", self.manual_peak_edits.added, pl.Int32)
        pl_removed = pl.Series("removed", self.manual_peak_edits.removed, pl.Int32)

        self.data = self.data.with_columns(
            pl.when(pl.col(SECTION_INDEX_COL).is_in(pl_added))
            .then(pl.lit(1))
            .when(pl.col(SECTION_INDEX_COL).is_in(pl_removed))
            .then(pl.lit(-1))
            .otherwise(pl.lit(0))
            .cast(pl.Int8)
            .alias(IS_MANUAL_COL)
        )

    def get_metadata(self) -> SectionMetadata:
        return SectionMetadata(
            signal_name=self.signal_name,
            section_id=self.section_id,
            sampling_rate=self.sampling_rate,
            global_bounds=self.global_bounds,
            processing_parameters=self._processing_parameters,
            rate_computation_method=Config.editing.rate_computation_method,
        )

    def get_peak_pos(self) -> pl.DataFrame:
        return (
            self.data.lazy()
            .filter(pl.col(IS_PEAK_COL) == 1)
            .select(
                pl.col(SECTION_INDEX_COL),
                pl.col(self.processed_signal_name),
            )
            .collect()
        )

    def lock_result(self, *, rr_params: RollingRateKwargs | None = None) -> None:
        self.update_peak_data(include_global=True, include_info=True)
        self.update_rate_data(full_info=True, force=True, rr_params=rr_params)
        self.set_locked(True)

    def get_result(self) -> DetailedSectionResult:
        metadata = self.get_metadata()
        self._add_manual_peak_edits_column()
        section_df = self.data
        manual_edits = self.manual_peak_edits

        section_result = self._result_data
        rate_per_temperature = self.get_mean_rate_per_temperature()
        return DetailedSectionResult(
            metadata=metadata,
            section_dataframe=section_df,
            manual_peak_edits=manual_edits,
            section_result=section_result,
            rate_per_temperature=rate_per_temperature,
        )

    def update_peak_data(
        self,
        include_global: bool = False,
        include_times: bool = False,
        include_intervals: bool = False,
        include_info: bool = False,
    ) -> None:
        """
        Update the peak data for the section.

        Parameters
        ----------
        include_global : bool, optional
            Whether to add the global index values to the peak dataframe, by default False
        include_times : bool, optional
            Whether to add the time values to the peak dataframe, by default False
        include_intervals : bool, optional
            Whether to add a column for the intervals between peaks, by default False
        include_info : bool, optional
            Whether to add a column with the values in the `info_name` column, by default False

        Raises
        ------
        RuntimeError
            If the number of detected peaks is less than 3.
        """
        section_peaks = self.peaks_local

        if section_peaks.len() < 3:
            raise RuntimeError(f"Need at least 3 detected peaks to create a result, got {section_peaks.len()}")

        peak_df = self.get_peak_pos()

        if include_global:
            peak_df = peak_df.with_columns(self.peaks_global.alias("global_index"))
        if include_times:
            peak_df = peak_df.with_columns(
                (pl.col(SECTION_INDEX_COL) / self.sampling_rate).alias("seconds_since_section_start")
            )
        if include_intervals:
            peak_df = peak_df.with_columns(section_peaks.diff().fill_null(0).alias("peak_intervals"))

        if self.info_name in self.data.columns and include_info:
            peak_df = peak_df.with_columns(
                self.data.get_column(self.info_name).gather(section_peaks).alias(self.info_name)
            )

        self.peak_data = peak_df

    def reset_signal(self) -> None:
        """
        Resets the signal data and processing parameters to their initial state.

        This function clears any manual peak edits, resets various flags related to the signal processing, and updates
        the signal data to its default values. It ensures that the signal is in a clean state for further processing.
        """
        self.data = (
            self.data.lazy()
            .with_columns(
                pl.col(self.signal_name).alias(self.processed_signal_name),
                pl.lit(0, pl.Int8).alias(IS_PEAK_COL),
                pl.lit(0, pl.Int8).alias(IS_MANUAL_COL),
            )
            .collect()
        )
        self.manual_peak_edits.clear()
        self._is_filtered = False
        self._is_standardized = False
        self._is_processed = False
        self._processing_parameters.reset()

    def reset_peaks(self) -> None:
        """
        Resets the peak indicators in the signal data to their default values.

        This function clears any manual peak edits and updates the signal data to indicate that there are no peaks. It
        also resets the processing parameters specifically related to peak detection.
        """
        self.data = (
            self.data.lazy()
            .with_columns(
                pl.lit(0, pl.Int8).alias(IS_PEAK_COL),
                pl.lit(0, pl.Int8).alias(IS_MANUAL_COL),
            )
            .collect()
        )
        self.manual_peak_edits.clear()
        self._processing_parameters.reset(peaks_only=True)

    def get_summary(self) -> SectionSummaryDict:
        return {
            "name": self.section_id.pretty_name(),
            "size": self.data.height,
            "sampling_rate": self.sampling_rate,
            "start_index": self.global_bounds[0],
            "end_index": self.global_bounds[1],
            "peak_count": self.peaks_local.len(),
            "processing_parameters": self._processing_parameters.to_dict(),
        }

    def __repr__(self) -> str:
        # Section stats
        metadata = self.get_metadata()
        size = self.data.height
        processing_history: dict[str, str] = {
            f"Run {i}": repr(hist) for i, hist in enumerate(self._processing_parameters.filter_parameters, start=1)
        }
        stat_dict = {
            "Name": self.section_id.pretty_name(),
            "Size": f"{size} samples",
            "Sampling rate": f"{metadata.sampling_rate} Hz",
            "Start Index": str(metadata.global_bounds[0]),
            "End Index": str(metadata.global_bounds[1]),
            "Peak Count": str(self.peaks_local.len()),
            "Processing History": pprint.pformat(processing_history),
        }

        return pprint.pformat(stat_dict, indent=2, width=120, underscore_numbers=True)
