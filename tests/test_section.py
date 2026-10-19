"""
Behavioral tests for `Section`: the data-frame layout it builds, peak bookkeeping, and rate computation.

These run without a Qt event loop. They pin behavior that the data-flow refactor (Phases B to G) must preserve.
"""

import numpy as np
import polars as pl
import pytest

from signal_viewer.constants import INDEX_COL, IS_MANUAL_COL, IS_PEAK_COL, SECTION_INDEX_COL
from signal_viewer.sv_data.section import Section

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


def test_locked_section_rejects_result_updates() -> None:
    s = Section(make_df(), "sig", FS, info_column="temp")
    s.set_peaks(sine_peaks(), update_rate=False)
    s._calc_rate_rolling(sec_new_window_every=10, sec_window_length=60)
    before = s.rate_data

    s.set_locked(True)
    s.rate_data = pl.DataFrame()

    assert s.is_locked
    assert s.rate_data.equals(before)
