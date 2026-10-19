import functools
from pathlib import Path
from typing import Any

import mne.io
import numpy as np
import numpy.typing as npt
import polars as pl
from loguru import logger
from PySide6 import QtCore

from signal_viewer.constants import COMBO_BOX_NO_SELECTION
from signal_viewer.enum_defs import InputFileFormat, SectionChange, TextFileSeparator
from signal_viewer.sv_config import Config
from signal_viewer.sv_data.data_models import DataFrameModel, FileMetadata, SectionListModel
from signal_viewer.sv_data.file_io import detect_sampling_rate, read_edf
from signal_viewer.sv_data.section import DEFAULT_RATE_PARAMS, Section
from signal_viewer.type_defs import PeakDetectionRequest, ProcessingRequest, RollingRateKwargs, UpdatePeaksAction


class DataController(QtCore.QObject):
    """
    Owns the loaded file, its metadata, and every `Section`.

    It is the only object that calls mutating methods on a `Section`. Every mutation of the active section ends in
    exactly one `sig_section_changed(section, flags)` emission, where `flags` is a `SectionChange` naming what
    changed, so views refresh only the parts named.
    """

    sig_user_input_required = QtCore.Signal(set)
    sig_new_metadata = QtCore.Signal(object)  # FileMetadata
    sig_new_data = QtCore.Signal()
    sig_active_section_changed = QtCore.Signal(object)  # the now-active Section
    sig_section_changed = QtCore.Signal(object, object)  # (Section, SectionChange)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.has_data = False

        self.data_model = DataFrameModel(self)

        self._metadata: FileMetadata | None = None

        self._sections = SectionListModel(parent=self)
        self._active_section: Section | None = None
        self.active_section_model = DataFrameModel(self)
        self._base_section: Section | None = None
        self.result_model_peaks = DataFrameModel(self)
        self.result_model_rate = DataFrameModel(self)

        # Rolling-rate parameters shared by every section. The GUI pushes changes here via `set_rate_params`.
        self._rate_params: RollingRateKwargs = DEFAULT_RATE_PARAMS.copy()

        try:
            self._txt_separator = Config.data.text_file_separator
        except Exception:
            self._txt_separator = TextFileSeparator.Tab
        self._reader_funcs = {
            ".csv": functools.partial(pl.scan_csv, separator=TextFileSeparator.Comma),
            ".txt": functools.partial(pl.scan_csv, separator=self._txt_separator),
            ".tsv": functools.partial(pl.scan_csv, separator=TextFileSeparator.Tab),
            ".feather": pl.scan_ipc,
            ".arrow": pl.scan_ipc,
            ".ipc": pl.scan_ipc,
        }

    @property
    def base_df(self) -> pl.DataFrame:
        return self.data_model.df

    @property
    def sections(self) -> SectionListModel:
        return self._sections

    @property
    def metadata(self) -> FileMetadata:
        if self._metadata is None:
            raise ValueError("No data available.")
        return self._metadata

    @property
    def rate_params(self) -> RollingRateKwargs:
        return self._rate_params

    @QtCore.Slot(dict)
    def set_rate_params(self, params: RollingRateKwargs) -> None:
        """
        Applies new rolling-rate parameters to every existing section and to sections created later.

        The active section's rate is recomputed right away when it has peaks and is not locked; other sections
        recompute lazily on their next `update_rate_data` call.
        """
        self._rate_params = params.copy()
        for section in self.sections.all_sections:
            section.set_rate_params(self._rate_params)

        if not self.has_data:
            return
        section = self.active_section
        if section.is_locked or section.peaks_local.is_empty():
            return
        section.update_rate_data()
        self.sig_section_changed.emit(section, SectionChange.RATE)

    def get_base_section(self) -> Section:
        if self._base_section is None:
            try:
                self._base_section = Section(
                    self.base_df,
                    signal_name=self.metadata.data_signal_column,
                    sampling_rate=self.metadata.sampling_rate,
                    info_column=self.metadata.data_info_column,
                    rate_params=self._rate_params,
                )
                self._base_section.set_locked(True)
            except Exception as e:
                raise ValueError("No data available. Select a valid file to load, and try again.") from e
        return self._base_section

    @property
    def active_section(self) -> Section:
        if self._active_section is None:
            self._active_section = self.get_base_section()
        return self._active_section

    @QtCore.Slot(QtCore.QModelIndex)
    def set_active_section(self, model_index: QtCore.QModelIndex) -> None:
        section = self.sections.data(model_index, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(section, Section):
            self._active_section = section
            self.active_section_model.set_df(section.data)
            self.sig_active_section_changed.emit(section)

    @property
    def base_section_index(self) -> QtCore.QModelIndex:
        return self.sections.index(0)

    def update_metadata(
        self,
        sampling_rate: int | None = None,
        signal_col: str | None = None,
        info_col: str | None = None,
    ) -> None:
        if self._metadata is None:
            return

        if sampling_rate is not None:
            self.metadata.sampling_rate = sampling_rate
        if signal_col is not None:
            self.metadata.signal_column = signal_col
        if info_col is not None:
            self.metadata.info_column = info_col

        self.sig_new_metadata.emit(self.metadata)

    @QtCore.Slot(str)
    def open_file(self, file_path: Path | str) -> None:
        file_path = Path(file_path)
        if not file_path.is_file():
            logger.error(
                f"Path: {file_path} \n\nNo file exists at the specified path. Please check the path and try again."
            )
        if file_path.suffix not in InputFileFormat:
            logger.error(f"Unsupported file format: {file_path.suffix}. Allowed formats: {', '.join(InputFileFormat)}")

        other_info: dict[str, Any] = {}

        if file_path.suffix == ".edf":
            edf_info = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
            sampling_rate = int(edf_info.info["sfreq"])
            column_names: list[str] = edf_info.ch_names  # type: ignore
            other_info = dict(edf_info.info)
        elif file_path.suffix in {".feather", ".arrow", ".ipc", ".csv", ".txt", ".tsv"}:
            lf = self._reader_funcs[file_path.suffix](file_path)
            column_names = lf.collect_schema().names()
            try:
                sampling_rate = detect_sampling_rate(lf)
            except Exception:
                sampling_rate = 0
        elif file_path.suffix in {".xls", ".xlsx"}:
            lf = pl.read_excel(file_path).lazy()
            column_names = lf.collect_schema().names()
            try:
                sampling_rate = detect_sampling_rate(lf)
            except Exception:
                sampling_rate = 0
        elif file_path.suffix == ".hdf5":
            raise NotImplementedError("Reading HDF5 files is not yet supported.")
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}. Please select a valid file format.")

        # `FileMetadata.__init__` pre-selects the columns and sampling rate remembered in `Config.internal`.
        metadata = FileMetadata(file_path, column_names, sampling_rate)
        metadata.other_info = other_info
        self._metadata = metadata

        # Widgets are filled first, so the dialog opened by the second signal already shows the current values.
        self.sig_new_metadata.emit(self.metadata)
        if self.metadata.required_fields:
            self.sig_user_input_required.emit(set(self.metadata.required_fields))

    def _reset_sections(self) -> None:
        """Drops every section and result so `load_data` can be called again on the same file."""
        self.sections.clear()
        self._base_section = None
        self._active_section = None
        self.active_section_model.set_df(pl.DataFrame())
        self.result_model_peaks.set_df(pl.DataFrame())
        self.result_model_rate.set_df(pl.DataFrame())
        self.has_data = False

    def load_data(self) -> None:
        """
        Reads the selected columns from the file described by `metadata` and creates the base section.

        Safe to call repeatedly: an earlier load of the same file is discarded first. The metadata itself is not
        modified, so the user's column and sampling-rate choices survive a reload.
        """
        if self._metadata is None:
            return
        suffix = self.metadata.file_format
        file_path = self.metadata.file_path
        separator = Config.data.text_file_separator

        # The only place the "last used" values are persisted. They hold the raw file column names so they can be
        # matched against the next file's columns.
        Config.internal.last_signal_column = self.metadata.signal_column
        Config.internal.last_info_column = self.metadata.info_column
        Config.internal.last_sampling_rate = self.metadata.sampling_rate

        signal_col = self.metadata.signal_column
        info_col = self.metadata.info_column
        columns = [signal_col]
        if info_col != COMBO_BOX_NO_SELECTION:
            columns.append(info_col)
        row_index_col = "index"
        if row_index_col in columns:
            logger.exception("Column name 'index' is reserved for internal use and cannot be used as a column name.")
            return

        if suffix == ".csv":
            df = pl.read_csv(file_path, columns=columns, row_index_name=row_index_col)
        elif suffix == ".txt":
            df = pl.read_csv(file_path, columns=columns, separator=separator, row_index_name=row_index_col)
        elif suffix == ".tsv":
            df = pl.read_csv(
                file_path,
                columns=columns,
                separator=TextFileSeparator.Tab,
                row_index_name=row_index_col,
            )
        elif suffix == ".feather":
            df = pl.read_ipc(file_path, columns=columns, row_index_name=row_index_col)
        elif suffix == ".edf":
            df = read_edf(Path(file_path), signal_col, info_col)
        elif suffix == ".hdf5":
            raise NotImplementedError("Reading HDF5 files is not yet supported.")
        elif suffix in {".xls", ".xlsx"}:
            df = pl.read_excel(file_path, columns=columns)
        else:
            raise NotImplementedError(f"Unsupported file format: {suffix}.")

        df = df.rename(self.metadata.name_map, strict=False)

        self._reset_sections()
        self.data_model.set_df(df)
        self._base_section = self.get_base_section()
        self.sections.add_section(self._base_section)
        self.set_active_section(self.base_section_index)
        self.has_data = True
        self.sig_new_data.emit()

    def create_section(self, start: float, stop: float) -> None:
        if self._metadata is None:
            return
        data = self.base_df.filter(pl.col("index").is_between(start, stop))
        section = Section(
            data,
            self.metadata.data_signal_column,
            sampling_rate=self.metadata.sampling_rate,
            info_column=self.metadata.data_info_column,
            rate_params=self._rate_params,
        )
        self.sections.add_section(section)

    def delete_section(self, idx: QtCore.QModelIndex) -> None:
        self.sections.remove_section(idx)
        self.set_active_section(self.base_section_index)

    # --- Active-section mutations ------------------------------------------------------------------------------------
    # Each method below is the single entry point for one kind of change. It mutates the active section and emits
    # `sig_section_changed` once with the flags describing what changed. `detect_peaks` and `lock_active` are also
    # called from worker threads (see `sv_app`); the signal is then delivered queued to the GUI thread.

    @QtCore.Slot(object)
    def apply_processing(self, request: ProcessingRequest) -> None:
        """Resets the active section's signal and peaks, then applies `request`."""
        section = self.active_section
        section.apply_processing(request)
        self.sig_section_changed.emit(section, SectionChange.SIGNAL | SectionChange.PEAKS | SectionChange.RATE)

    @QtCore.Slot()
    def reset_signal(self) -> None:
        """Restores the raw signal and discards peaks and processing parameters."""
        self.apply_processing(ProcessingRequest())

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        section = self.active_section
        section.reset_peaks()
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    def detect_peaks(self, request: PeakDetectionRequest) -> None:
        """Runs peak detection on the whole processed signal and replaces the existing peaks."""
        section = self.active_section
        section.detect_peaks(request.method, request.params)
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    def detect_peaks_in_range(self, start: int, stop: int, request: PeakDetectionRequest) -> None:
        """Runs peak detection on section indices `[start, stop]` and adds the result to the existing peaks."""
        section = self.active_section
        section.detect_peaks_in_range(start, stop, request.method, request.params)
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    @QtCore.Slot(str, object)
    def update_peaks(self, action: UpdatePeaksAction, indices: npt.NDArray[np.intp]) -> None:
        """Adds or removes single peaks at section indices `indices` (manual edits from the plot)."""
        section = self.active_section
        section.update_peaks(action, indices)
        self.sig_section_changed.emit(section, SectionChange.PEAKS | SectionChange.RATE)

    def lock_active(self) -> None:
        """
        Computes the final peak and rate result for the active section and locks it against further edits.

        Raises
        ------
        RuntimeError
            If the section has fewer than three peaks. Nothing is emitted in that case.
        """
        section = self.active_section
        section.lock_result()
        self.sections.notify_section_changed(section)  # lock icon in the list view
        self.sig_section_changed.emit(section, SectionChange.LOCK | SectionChange.RESULT)

    @QtCore.Slot()
    def unlock_active(self) -> None:
        section = self.active_section
        section.set_locked(False)
        self.sections.notify_section_changed(section)
        self.sig_section_changed.emit(section, SectionChange.LOCK)
