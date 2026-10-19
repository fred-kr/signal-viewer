"""
Behavioral tests for `Section`: the data-frame layout it builds, peak bookkeeping, and rate computation.

These run without a Qt event loop. They pin behavior that the data-flow refactor (Phases B to G) must preserve.
"""

import numpy as np
import polars as pl
import pytest

from signal_viewer.constants import INDEX_COL, IS_MANUAL_COL, IS_PEAK_COL, SECTION_INDEX_COL
from signal_viewer.enum_defs import (
    FilterMethod,
    IncompleteWindowMethod,
    PeakDetectionAlgorithm,
    PreprocessPipeline,
    RateComputationMethod,
    StandardizationMethod,
)
from signal_viewer.sv_data.section import (
    DEFAULT_RATE_PARAMS,
    Section,
    compute_peak_data,
    compute_rate_data,
    compute_rate_instant,
)
from signal_viewer.type_defs import PeaksLocalMaxima, ProcessingRequest, RollingRateKwargs

FS = 100  # Hz
SECONDS = 120
N = FS * SECONDS


def make_df(with_info: bool = True) -> pl.DataFrame:
    """A 1 Hz sine sampled at 100 Hz for 120 s, so one peak per second (60 bpm) at sample 25 + 100k."""
    t = np.arange(N) / FS
    cols: dict[str, np.ndarray] = {
        INDEX_COL: np.arange(N, dtype=np.uint32),
        "sig": np.sin(2 * np.pi * t),
    }
    if with_info:
        cols["temp"] = np.linspace(20.0, 30.0, N)
    return pl.DataFrame(cols)


def sine_peaks() -> np.ndarray:
    return np.arange(25, N, FS)


def test_section_adds_bookkeeping_columns() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")

    assert s.data.columns == [
        INDEX_COL,
        SECTION_INDEX_COL,
        "sig",
        "temp",
        "sig_processed",
        IS_PEAK_COL,
        IS_MANUAL_COL,
    ]
    assert s.data.schema[INDEX_COL] == pl.Int32
    assert s.data.schema[SECTION_INDEX_COL] == pl.Int32
    assert s.sampling_rate == FS
    assert s.global_bounds == (0, N - 1)
    assert s.processed_signal.equals(s.raw_signal)
    assert s.peaks_local.is_empty()


def test_section_without_info_column() -> None:
    s = Section(make_df(with_info=False), "sig", FS)

    assert s.info_name is None
    assert s.info_data is None

    s.set_peaks(sine_peaks(), update_rate=False)
    s._calc_rate_rolling(sec_new_window_every=10, sec_window_length=60)

    # Without an info column there is nothing to group by: one placeholder row with no values.
    per_temp = s.get_mean_rate_per_temperature()
    assert per_temp.height == 1
    rate_mean = per_temp.get_column("rate_mean")
    assert (rate_mean.is_null() | rate_mean.is_nan()).all()

    simple = s.get_simple_result(step_size=10)
    assert simple.columns == [INDEX_COL, "rate_bpm", "group_var"]


def test_unknown_columns_raise() -> None:
    with pytest.raises(ValueError, match="Info column"):
        Section(make_df(), "sig", FS, info_column="<No Selection>")
    with pytest.raises(ValueError, match="Signal column"):
        Section(make_df(), "missing", FS)


def test_set_peaks_marks_rows() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(np.array([100, 200, 300]), update_rate=False)

    assert s.peaks_local.to_list() == [100, 200, 300]
    assert s.peaks_global.to_list() == [100, 200, 300]
    assert s.data.get_column(IS_PEAK_COL).sum() == 3

    pos = s.get_peak_pos()
    assert pos.columns == [SECTION_INDEX_COL, "sig_processed"]
    assert pos.height == 3


def test_update_peaks_tracks_manual_edits() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(np.array([100, 200, 300]), update_rate=False)

    s.update_peaks("add", np.array([400]), update_rate=False)
    assert s.peaks_local.to_list() == [100, 200, 300, 400]
    assert s.manual_peak_edits.added == [400]
    assert s.manual_peak_edits.removed == []

    s.update_peaks("remove", np.array([100]), update_rate=False)
    assert s.peaks_local.to_list() == [200, 300, 400]
    assert s.manual_peak_edits.removed == [100]

    # Removing a manually added peak cancels the addition instead of recording a removal.
    s.update_peaks("remove", np.array([400]), update_rate=False)
    assert s.peaks_local.to_list() == [200, 300]
    assert s.manual_peak_edits.added == []
    assert s.manual_peak_edits.removed == [100]

    # Adding an index that is already a peak changes nothing.
    s.update_peaks("add", np.array([200]), update_rate=False)
    assert s.manual_peak_edits.added == []


def test_reset_peaks_clears_peaks_and_edits() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(np.array([100, 200, 300]), update_rate=False)
    s.update_peaks("add", np.array([400]), update_rate=False)

    s.reset_peaks()

    assert s.peaks_local.is_empty()
    assert s.manual_peak_edits.added == []
    assert s.manual_peak_edits.removed == []
    assert s.data.get_column(IS_MANUAL_COL).sum() == 0


def test_rolling_rate_with_and_without_info() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(sine_peaks(), update_rate=False)

    # 120 s of data, 60 s windows every 10 s, incomplete windows dropped: 7 windows of exactly 60 peaks each.
    s._calc_rate_rolling(sec_new_window_every=10, sec_window_length=60)
    rate = s.rate_data
    assert rate.columns == [SECTION_INDEX_COL, "rate_bpm"]
    assert rate.height == 7
    assert rate.get_column("rate_bpm").to_list() == pytest.approx([60.0] * 7)

    s._calc_rate_rolling(sec_new_window_every=10, sec_window_length=60, full_info=True)
    full = s.rate_data
    assert full.height == 7
    assert {"temp_mean", "temp_std", "temp_min", "temp_max"} <= set(full.columns)

    per_temp = s.get_mean_rate_per_temperature()
    assert per_temp.height == 7
    assert per_temp.get_column("rate_mean").to_list() == pytest.approx([60.0] * 7)


def test_apply_processing_resets_then_applies_steps() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(sine_peaks(), update_rate=False)

    s.apply_processing(ProcessingRequest(pipeline=PreprocessPipeline.PPG_Elgendi))
    assert s.is_processed
    assert not s.is_filtered
    assert s.peaks_local.is_empty(), "processing starts from a clean signal, so peaks are dropped"

    s.apply_processing(
        ProcessingRequest(
            filter={"lowcut": 0.5, "highcut": 8.0, "method": FilterMethod.Butterworth, "order": 3},
            standardize={"method": StandardizationMethod.ZScore, "robust": False, "window_size": None},
        )
    )
    assert s.is_filtered
    assert s.is_standardized
    assert not s.is_processed
    mean = s.processed_signal.mean()
    assert isinstance(mean, float)
    assert abs(mean) < 1e-6

    s.apply_processing(ProcessingRequest())
    assert not (s.is_filtered or s.is_standardized or s.is_processed)
    assert s.processed_signal.equals(s.raw_signal)


def test_detect_peaks_in_range_adds_to_existing_peaks() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(np.array([25, 125]), update_rate=False)

    s.detect_peaks_in_range(
        1000,
        2000,
        PeakDetectionAlgorithm.LocalMaxima,
        PeaksLocalMaxima(search_radius=40, min_distance=40),
    )

    peaks = s.peaks_local.to_list()
    assert peaks[:2] == [25, 125]
    # Sine maxima inside [1010, 1990) after trimming the 10-sample edge buffer.
    assert peaks[2:] == list(range(1025, 2000, 100))
    assert s.manual_peak_edits.added == peaks[2:]


def test_rate_params_live_on_the_section() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    assert s.rate_params == DEFAULT_RATE_PARAMS
    s.set_peaks(sine_peaks(), update_rate=False)

    s._calc_rate_rolling(**s.rate_params)
    assert s.rate_data.height == 7

    s._rate_is_synced = True
    new_params: RollingRateKwargs = {
        "sec_new_window_every": 5,
        "sec_window_length": 30,
        "incomplete_window_method": IncompleteWindowMethod.Drop,
    }
    s.set_rate_params(new_params)
    assert s.rate_params == new_params
    assert s.rate_params is not new_params, "the section keeps its own copy"
    assert not s._rate_is_synced, "changing parameters invalidates the computed rate"

    s._calc_rate_rolling(**s.rate_params)
    # 30 s windows every 5 s over 120 s: starts 0, 5, ..., 90 are complete.
    assert s.rate_data.height == 19
    assert s.rate_data.get_column("rate_bpm").to_list() == pytest.approx([60.0] * 19)

    # Without the full-info rate there is no info mean to attach; with it there is.
    simple = s.get_simple_result()
    assert simple.columns == [INDEX_COL, "rate_bpm", "group_var"]
    assert simple.get_column(INDEX_COL).to_list()[:3] == [0, 500, 1000], "step defaults to the section's params"

    s._calc_rate_rolling(full_info=True, **s.rate_params)
    simple = s.get_simple_result(group_var="A")
    assert simple.columns == [INDEX_COL, "temp_mean", "rate_bpm", "group_var"]
    assert simple.get_column("group_var").to_list() == ["A"] * 19


def test_locked_section_rejects_result_updates() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(sine_peaks(), update_rate=False)
    s._calc_rate_rolling(sec_new_window_every=10, sec_window_length=60)
    before = s.rate_data

    s.set_locked(True)
    s.rate_data = pl.DataFrame()

    assert s.is_locked
    assert s.rate_data.equals(before)


def test_reset_peaks_empties_result_frames() -> None:
    """Views redraw from `rate_data`, so discarding the peaks must also discard the rate computed from them."""
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(sine_peaks())
    assert not s.rate_data.is_empty()

    s.reset_peaks()
    assert s.rate_data.is_empty()
    assert s.peak_data.is_empty()

    s.set_peaks(sine_peaks())
    s.reset_signal()
    assert s.rate_data.is_empty()


def test_compute_helpers_are_pure() -> None:
    """The threaded result worker uses these on a frame snapshot; they must not touch the section."""
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(sine_peaks(), update_rate=False)
    snapshot = s.data

    with pytest.raises(RuntimeError, match="at least 3"):
        compute_peak_data(make_df().pipe(lambda df: Section(df, "sig", FS).data), "sig_processed", FS, None)

    peak_df = compute_peak_data(snapshot, "sig_processed", FS, "temp", include_global=True, include_info=True)
    assert peak_df.columns == [SECTION_INDEX_COL, "sig_processed", "global_index", "temp"]
    assert peak_df.height == len(sine_peaks())

    rate_df = compute_rate_data(
        snapshot, FS, "temp", s.rate_params, RateComputationMethod.RollingWindow, full_info=True
    )
    assert rate_df.height == 7
    assert "temp_mean" in rate_df.columns

    inst = compute_rate_data(snapshot, FS, "temp", s.rate_params, RateComputationMethod.Instantaneous)
    assert inst.height == N
    assert compute_rate_instant(Section(make_df(), "sig", FS).data, FS).is_empty(), "no peaks, no rate"

    assert s.peak_data.is_empty() and s.rate_data.is_empty(), "nothing was assigned to the section"
    assert s.data is snapshot

    s.apply_lock_result(peak_df, rate_df)
    assert s.is_locked
    assert s.peak_data.equals(peak_df) and s.rate_data.equals(rate_df)
