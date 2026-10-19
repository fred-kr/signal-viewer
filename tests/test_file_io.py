"""
Tests for the xlsx export: one workbook, four sheets, one unlocked section does not break it.
"""

from pathlib import Path

import numpy as np
import polars as pl

from signal_viewer.constants import INDEX_COL
from signal_viewer.sv_data.file_io import write_xlsx
from signal_viewer.sv_data.section import Section

FS = 100
N = FS * 120


def make_section(start: int, stop: int) -> Section:
    t = np.arange(start, stop + 1) / FS
    df = pl.DataFrame(
        {
            INDEX_COL: np.arange(start, stop + 1, dtype=np.uint32),
            "sig": np.sin(2 * np.pi * t),
            "temp": np.linspace(20.0, 30.0, stop - start + 1),
        }
    )
    return Section(df, "sig", FS, info_column="temp")


def test_write_xlsx_combines_sections(tmp_path: Path) -> None:
    locked = make_section(0, N - 1)
    locked.set_peaks(np.arange(25, N, FS), update_rate=False)
    locked.lock_result()
    unlocked = make_section(N, 2 * N - 1)
    out = tmp_path / "result.xlsx"

    write_xlsx([locked, unlocked], out, group_var="run A")

    sheets = pl.read_excel(out, sheet_id=0)
    assert set(sheets) == {"r_data", "Detected Peaks", "Rate Data", "Global Bounds"}

    peaks = sheets["Detected Peaks"]
    assert peaks.get_column("section_id").unique().to_list() == [1], "the unlocked section has no result rows"
    assert peaks.height == 120
    assert "global_index" in peaks.columns and "temp" in peaks.columns

    rate = sheets["Rate Data"]
    assert rate.height == 7
    assert "temp_mean" in rate.columns

    r_data = sheets["r_data"]
    assert r_data.columns == [INDEX_COL, "temp_mean", "rate_bpm", "group_var"]
    assert r_data.get_column("group_var").unique().to_list() == ["run A"]
    assert r_data.get_column(INDEX_COL).to_list()[:3] == [0, 1000, 2000], "step from the section's rate_params"

    bounds = sheets["Global Bounds"]
    assert bounds.get_column("global_start").to_list() == [0, N]
    assert bounds.get_column("global_end").to_list() == [N - 1, 2 * N - 1]
