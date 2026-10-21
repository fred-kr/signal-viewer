"""
Tests for the xlsx export: one workbook with four sheets and a `channel` column, one unlocked section does not break
it, several channels in one workbook or one workbook each.
"""

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from signal_viewer.constants import INDEX_COL
from signal_viewer.sv_data.file_io import per_channel_xlsx_paths, write_xlsx, write_xlsx_per_channel
from signal_viewer.sv_data.section import Section

FS = 100
N = FS * 120


def make_section(start: int, stop: int, signal: str = "sig") -> Section:
    t = np.arange(start, stop + 1) / FS
    df = pl.DataFrame(
        {
            INDEX_COL: np.arange(start, stop + 1, dtype=np.uint32),
            signal: np.sin(2 * np.pi * t),
            "temp": np.linspace(20.0, 30.0, stop - start + 1),
        }
    )
    return Section(df, signal, FS, info_column="temp")


def make_locked(start: int, stop: int, signal: str = "sig") -> Section:
    section = make_section(start, stop, signal)
    section.set_peaks(np.arange(start + 25, stop + 1, FS) - start, update_rate=False)
    section.lock_result()
    return section


def test_write_xlsx_combines_sections(tmp_path: Path) -> None:
    locked = make_locked(0, N - 1)
    unlocked = make_section(N, 2 * N - 1)
    out = tmp_path / "result.xlsx"

    write_xlsx({"Sig A": [locked, unlocked]}, out, group_var="run A")

    sheets = pl.read_excel(out, sheet_id=0)
    assert set(sheets) == {"r_data", "Detected Peaks", "Rate Data", "Global Bounds"}
    assert all(df.columns[0] == "channel" for df in sheets.values())

    peaks = sheets["Detected Peaks"]
    assert peaks.get_column("channel").unique().to_list() == ["Sig A"]
    assert peaks.get_column("section_id").unique().to_list() == [1], "the unlocked section has no result rows"
    assert peaks.height == 120
    assert "global_index" in peaks.columns and "temp" in peaks.columns

    rate = sheets["Rate Data"]
    assert rate.height == 7
    assert "temp_mean" in rate.columns

    r_data = sheets["r_data"]
    assert r_data.columns == ["channel", INDEX_COL, "temp_mean", "rate_bpm", "group_var"]
    assert r_data.get_column("group_var").unique().to_list() == ["run A"]
    assert r_data.get_column(INDEX_COL).to_list()[:3] == [0, 1000, 2000], "step from the section's rate_params"

    bounds = sheets["Global Bounds"]
    assert bounds.get_column("global_start").to_list() == [0, N]
    assert bounds.get_column("global_end").to_list() == [N - 1, 2 * N - 1]

    # The section frames are not modified by the export, so exporting twice works.
    assert locked.peak_data.columns[0] != "section_id"
    write_xlsx({"Sig A": [locked, unlocked]}, out, group_var="run A")


def test_write_xlsx_numbers_sections_per_channel(tmp_path: Path) -> None:
    a1, a2 = make_locked(0, N - 1, "sig_a"), make_locked(N, 2 * N - 1, "sig_a")
    b1 = make_locked(0, N - 1, "sig_b")
    out = tmp_path / "result.xlsx"

    write_xlsx({"Sig A": [a1, a2], "Sig B": [b1]}, out)

    peaks = pl.read_excel(out, sheet_name="Detected Peaks")
    assert peaks.select("channel", "section_id").unique(maintain_order=True).rows() == [
        ("Sig A", 1),
        ("Sig A", 2),
        ("Sig B", 1),
    ]
    assert peaks.height == 3 * 120
    bounds = pl.read_excel(out, sheet_name="Global Bounds")
    assert bounds.get_column("channel").to_list() == ["Sig A", "Sig A", "Sig B"]


def test_write_xlsx_per_channel(tmp_path: Path) -> None:
    by_channel = {"Sig A": [make_locked(0, N - 1, "sig_a")], "Sig B": [make_locked(0, N - 1, "sig_b")]}

    assert per_channel_xlsx_paths(by_channel, tmp_path, "rec") == {
        "Sig A": tmp_path / "Result_Sig_A_rec.xlsx",
        "Sig B": tmp_path / "Result_Sig_B_rec.xlsx",
    }

    written = write_xlsx_per_channel(by_channel, tmp_path, "rec", group_var="g")

    assert written == [tmp_path / "Result_Sig_A_rec.xlsx", tmp_path / "Result_Sig_B_rec.xlsx"]
    for channel, path in zip(by_channel, written, strict=True):
        r_data = pl.read_excel(path, sheet_name="r_data")
        assert r_data.get_column("channel").unique().to_list() == [channel]
        assert r_data.get_column("group_var").unique().to_list() == ["g"]


def test_write_xlsx_refuses_empty_input(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Nothing to export"):
        write_xlsx({}, tmp_path / "x.xlsx")
    with pytest.raises(ValueError, match="Nothing to export"):
        write_xlsx({"Sig A": []}, tmp_path / "x.xlsx")
    with pytest.raises(ValueError, match="Nothing to export"):
        write_xlsx_per_channel({"Sig A": []}, tmp_path, "rec")
