"""
Tests for `FileMetadata`: column naming, the info-column sentinel boundary, and required-field tracking.
"""

from pathlib import Path

import pytest

from signal_viewer.constants import COMBO_BOX_NO_SELECTION
from signal_viewer.enum_defs import InputFileFormat
from signal_viewer.sv_data.data_models import FileMetadata

COLUMNS = ["Alpha Sig", "Beta Temp"]


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "recording.csv"
    path.write_text("Alpha Sig,Beta Temp\n1,2\n", encoding="utf-8")
    return path


def test_file_properties(csv_file: Path) -> None:
    md = FileMetadata(csv_file, COLUMNS, sampling_rate=100)

    assert md.file_name == "recording.csv"
    assert md.file_format == InputFileFormat.CSV
    assert md.valid_columns == COLUMNS
    assert md.column_names == [COMBO_BOX_NO_SELECTION, *COLUMNS]


def test_info_column_or_none_hides_the_sentinel(csv_file: Path) -> None:
    md = FileMetadata(csv_file, COLUMNS, sampling_rate=100)

    md.info_column = None
    assert md.info_column == COMBO_BOX_NO_SELECTION
    assert md.info_column_or_none is None

    md.info_column = "Beta Temp"
    assert md.info_column == "Beta Temp"
    assert md.info_column_or_none == "Beta Temp"


def test_name_map_and_apply(csv_file: Path) -> None:
    md = FileMetadata(csv_file, COLUMNS, sampling_rate=100)
    md.signal_column = "Alpha Sig"
    md.info_column = "Beta Temp"

    assert md.name_map == {"Alpha Sig": "alpha_sig", "Beta Temp": "beta_temp"}

    md.apply_name_map()
    assert md.signal_column == "alpha_sig"
    assert md.info_column == "beta_temp"


def test_apply_name_map_leaves_no_selection_alone(csv_file: Path) -> None:
    md = FileMetadata(csv_file, COLUMNS, sampling_rate=100)
    md.signal_column = "Alpha Sig"
    md.info_column = None

    md.apply_name_map()
    assert md.info_column == COMBO_BOX_NO_SELECTION
    assert md.info_column_or_none is None


def test_required_fields_track_sampling_rate(csv_file: Path) -> None:
    md = FileMetadata(csv_file, COLUMNS, sampling_rate=0)
    assert "sampling_rate" in md.required_fields

    md.sampling_rate = 100
    assert "sampling_rate" not in md.required_fields

    md.sampling_rate = 0
    assert "sampling_rate" in md.required_fields
