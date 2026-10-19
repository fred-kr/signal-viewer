"""
Tests for `SectionListModel`: ids follow rows, deletions renumber and report through `dataChanged`, and sections can
be found by identity. A `QAbstractListModel` works without a running `QApplication`.
"""

import numpy as np
import polars as pl
from PySide6 import QtCore

from signal_viewer.constants import INDEX_COL
from signal_viewer.sv_data.data_models import SectionListModel
from signal_viewer.sv_data.section import Section

FS = 100


def make_section(start: int, stop: int) -> Section:
    n = stop - start + 1
    df = pl.DataFrame({INDEX_COL: np.arange(start, stop + 1, dtype=np.uint32), "sig": np.zeros(n)})
    return Section(df, "sig", FS)


def make_model(n_editable: int) -> tuple[SectionListModel, list[Section]]:
    model = SectionListModel()
    sections = [make_section(0, 999)] + [make_section(i * 100, i * 100 + 99) for i in range(n_editable)]
    for s in sections:
        model.add_section(s)
    return model, sections


def test_add_assigns_row_ids_before_insertion() -> None:
    model = SectionListModel()
    seen_during_insert: list[str] = []
    model.rowsInserted.connect(
        lambda parent, first, last: seen_during_insert.append(str(model.get_section(model.index(first)).section_id))
    )

    sections = [make_section(0, 999), make_section(0, 99), make_section(100, 199)]
    for s in sections:
        model.add_section(s)

    assert seen_during_insert == ["Section_sig_000", "Section_sig_001", "Section_sig_002"], (
        "views see the final id already in rowsInserted"
    )
    assert model.editable_sections == sections[1:]
    assert model.get_base_section() is sections[0]


def test_remove_renumbers_following_rows_and_reports_them() -> None:
    model, sections = make_model(3)
    changed: list[tuple[int, int]] = []
    model.dataChanged.connect(lambda tl, br, roles=None: changed.append((tl.row(), br.row())))
    removed: list[tuple[int, int]] = []
    model.rowsAboutToBeRemoved.connect(lambda parent, first, last: removed.append((first, last)))

    model.remove_section(model.index(1))

    assert model.all_sections == [sections[0], sections[2], sections[3]]
    assert [s.section_id for s in model.all_sections] == ["Section_sig_000", "Section_sig_001", "Section_sig_002"]
    assert removed == [(1, 1)]
    assert changed == [(1, 2)], "only the rows after the deleted one were renamed"
    assert model.data(model.index(1), QtCore.Qt.ItemDataRole.DisplayRole) == "Section 001 (SIG)"

    # Removing the last row renames nothing.
    changed.clear()
    model.remove_section(model.index(2))
    assert changed == []


def test_index_of_and_notify() -> None:
    model, sections = make_model(2)
    assert model.index_of(sections[2]).row() == 2
    assert not model.index_of(make_section(0, 9)).isValid()

    changed: list[int] = []
    model.dataChanged.connect(lambda tl, br, roles=None: changed.append(tl.row()))
    model.notify_section_changed(sections[1])
    model.notify_section_changed(make_section(0, 9))  # unknown section: no emission
    assert changed == [1]
