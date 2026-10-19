"""
End-to-end tests for `DataController` on a real CSV file: open, edit metadata, load, section, reload.

`DataController` is a `QObject`, which works without a running `QApplication`.
"""

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from signal_viewer.constants import COMBO_BOX_NO_SELECTION, INDEX_COL
from signal_viewer.enum_defs import IncompleteWindowMethod
from signal_viewer.sv_data.data_controller import DataController
from signal_viewer.sv_data.section import DEFAULT_RATE_PARAMS
from signal_viewer.type_defs import RollingRateKwargs

FS = 100
N = FS * 20


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """20 s at 100 Hz with a float `time` column so the sampling rate can be detected."""
    t = np.arange(N) / FS
    pl.DataFrame(
        {
            "time": t,
            "Alpha Sig": np.sin(2 * np.pi * t),
            "Beta Temp": np.linspace(20.0, 30.0, N),
        }
    ).write_csv(tmp_path / "recording.csv")
    return tmp_path / "recording.csv"


def test_open_file_reads_schema_and_sampling_rate(csv_file: Path) -> None:
    dc = DataController()
    emitted: list[object] = []
    dc.sig_new_metadata.connect(emitted.append)

    dc.open_file(csv_file)

    assert dc.metadata.valid_columns == ["time", "Alpha Sig", "Beta Temp"]
    assert dc.metadata.sampling_rate == FS
    assert not dc.has_data
    assert emitted == [dc.metadata]


def test_load_data_keeps_metadata_and_uses_cleaned_names(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")

    dc.load_data()

    assert dc.has_data
    assert dc.base_df.columns == [INDEX_COL, "alpha_sig", "beta_temp"]
    assert dc.base_df.height == N
    # The metadata still describes the file; only the data frame carries cleaned names.
    assert dc.metadata.signal_column == "Alpha Sig"
    assert dc.metadata.info_column == "Beta Temp"

    base = dc.get_base_section()
    assert dc.sections.rowCount() == 1
    assert dc.active_section is base
    assert base.signal_name == "alpha_sig"
    assert base.info_name == "beta_temp"
    assert base.sampling_rate == FS
    assert base.is_locked


def test_load_data_without_info_column(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col=COMBO_BOX_NO_SELECTION)

    dc.load_data()

    assert dc.base_df.columns == [INDEX_COL, "alpha_sig"]
    assert dc.get_base_section().info_name is None


def test_create_section_and_reload(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    dc.load_data()

    dc.create_section(100, 299)
    assert dc.sections.rowCount() == 2
    section = dc.sections.editable_sections[0]
    assert section.global_bounds == (100, 299)
    assert section.data.height == 200
    assert section.signal_name == "alpha_sig"
    assert not section.is_locked

    # Loading again discards sections but keeps the user's metadata choices.
    dc.load_data()
    assert dc.sections.rowCount() == 1
    assert dc.sections.editable_sections == []
    assert dc.metadata.signal_column == "Alpha Sig"
    assert dc.active_section is dc.get_base_section()


def test_rate_params_reach_existing_and_new_sections(csv_file: Path) -> None:
    dc = DataController()
    dc.open_file(csv_file)
    dc.update_metadata(signal_col="Alpha Sig", info_col="Beta Temp")
    dc.load_data()
    dc.create_section(100, 299)
    assert all(s.rate_params == DEFAULT_RATE_PARAMS for s in dc.sections.all_sections)

    params: RollingRateKwargs = {
        "sec_new_window_every": 5,
        "sec_window_length": 30,
        "incomplete_window_method": IncompleteWindowMethod.Approximate,
    }
    dc.set_rate_params(params)
    assert dc.rate_params == params
    assert all(s.rate_params == params for s in dc.sections.all_sections)

    dc.create_section(300, 499)
    assert dc.sections.editable_sections[-1].rate_params == params
