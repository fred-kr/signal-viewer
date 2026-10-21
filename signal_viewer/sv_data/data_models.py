"""
Qt item models and the file metadata.

`DataFrameModel` shows a polars frame in a table view, `FileListModel` the recent-files list, `SectionListModel` the
sections of one channel (and assigns their ids). `FileMetadata` holds what is known about the open file before and
after loading: columns, sampling rate, the chosen signal and info column, and which required fields are still
missing.
"""

import datetime
from collections.abc import Mapping
from pathlib import Path
from typing import Any, override

import polars as pl

# from janitor.polars.clean_names import _clean_column_names
from PySide6 import QtCore, QtGui

from signal_viewer.constants import COMBO_BOX_NO_SELECTION, RESERVED_COLUMN_NAMES
from signal_viewer.enum_defs import InputFileFormat
from signal_viewer.sv_config import Config
from signal_viewer.sv_data.section import Section, SectionID
from signal_viewer.type_defs import MetadataDict
from signal_viewer.utils import _clean_column_names, format_file_path, human_readable_timedelta

ItemDataRole = QtCore.Qt.ItemDataRole
type ModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex

# Display names of `FileMetadata.required_fields` entries.
REQUIRED_FIELD_LABELS = {"sampling_rate": "Sampling rate", "signal_column": "Signal column"}


class DataFrameModel(QtCore.QAbstractTableModel):
    """
    Read-only table model over a polars frame.

    Floats are shown with `Config.data.float_precision` decimals (read on every `set_df`), integers with thousands
    separators, durations as `human_readable_timedelta`. The tooltip of a cell is the `repr` of the value, that of
    a header the column dtype.
    """

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.df = pl.DataFrame()
        self._float_precision = Config.data.float_precision

    def set_df(self, df: pl.DataFrame) -> None:
        """Replaces the frame (full model reset) and re-reads the float precision setting."""
        self.beginResetModel()
        self._float_precision = Config.data.float_precision
        self.df = df
        self.endResetModel()

    @override
    def rowCount(self, parent: ModelIndex | None = None) -> int:
        return self.df.height

    @override
    def columnCount(self, parent: ModelIndex | None = None) -> int:
        return self.df.width

    @override
    def data(
        self,
        index: ModelIndex,
        role: int = ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        if index.row() >= self.rowCount() or index.column() >= self.columnCount():
            return None
        if self.df.is_empty():
            return None

        col_idx = index.column()
        row_idx = index.row()

        col_name = self.df.columns[col_idx]

        value = self.df.item(row_idx, col_idx)
        if role == ItemDataRole.DisplayRole:
            value_type = self.df.schema[col_name]

            if value_type.is_integer():
                return f"{value:_}"
            elif value_type.is_float():
                return f"{value:.{self._float_precision}f}"
            elif value_type.is_temporal():
                if isinstance(value, datetime.timedelta):
                    return human_readable_timedelta(value)
                else:
                    return str(value)
            elif value is None:
                return ""
            else:
                return str(value)
        elif role == ItemDataRole.UserRole:
            return value
        elif role == ItemDataRole.ToolTipRole:
            return repr(value)

        return None

    @override
    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = ItemDataRole.DisplayRole,
    ) -> str | None:
        if self.df.is_empty():
            return None
        if role == ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self.df.columns[section]
        elif role == ItemDataRole.ToolTipRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return str(self.df.schema[self.df.columns[section]])
        return None


class FileListModel(QtCore.QAbstractListModel):
    """
    The recent-files list: newest first, at most `max_files` entries, persisted in `Config.internal.recent_files`.

    Files that no longer exist are dropped on construction (`validate_files`). Display text is the shortened path,
    the tooltip and `UserRole` the full path.
    """

    sig_files_changed = QtCore.Signal()

    def __init__(
        self,
        recent_files: list[str] | None = None,
        validate_files: bool = True,
        max_files: int = 10,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._recent_files = recent_files or []
        self._max_files = max_files

        self.sig_files_changed.connect(self.update_config)

        if validate_files:
            self.validate_files()

    @override
    def rowCount(self, parent: ModelIndex | None = None) -> int:
        return len(self._recent_files)

    @override
    def data(self, index: ModelIndex, role: int = ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not self._recent_files:
            return None

        row = index.row()
        if row >= self.rowCount():
            return None

        file_path = self._recent_files[row]

        if role == ItemDataRole.DisplayRole:
            return format_file_path(file_path, max_len=70)
        elif role in [ItemDataRole.UserRole, ItemDataRole.ToolTipRole]:
            return file_path
        return None

    @override
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ItemDataRole.DisplayRole) -> Any:
        if role != ItemDataRole.DisplayRole:
            return None

        if orientation == QtCore.Qt.Orientation.Horizontal:
            return "Recent Files"

        return str(section + 1)

    def add_file(self, file_path: str) -> None:
        """Moves `file_path` to the top (or inserts it), drops the oldest entry beyond `max_files`. Ignores missing files."""
        if not Path(file_path).is_file():
            return
        parent = QtCore.QModelIndex()

        if file_path in self._recent_files:
            file_index = self._recent_files.index(file_path)
            self.beginRemoveRows(parent, file_index, file_index)
            self._recent_files.remove(file_path)
            self.endRemoveRows()

        self.beginInsertRows(parent, 0, 0)
        self._recent_files.insert(0, file_path)
        self.endInsertRows()

        if self.rowCount() > self._max_files:
            # Remove the oldest file, i.e. the last one
            self.beginRemoveRows(parent, self.rowCount() - 1, self.rowCount() - 1)
            self._recent_files.pop()
            self.endRemoveRows()

        self.sig_files_changed.emit()

    def remove_file(self, index: ModelIndex) -> None:
        """Removes the entry at `index`."""
        row = index.row()
        parent = self.index(0, 0)
        self.beginRemoveRows(parent, row, row)
        del self._recent_files[row]
        self.endRemoveRows()

        self.sig_files_changed.emit()

    def clear(self) -> None:
        """Removes every entry."""
        self.beginResetModel()
        self._recent_files.clear()
        self.endResetModel()

        self.sig_files_changed.emit()

    def set_recent_files(self, recent_files: list[str]) -> None:
        """Replaces the whole list."""
        self.beginResetModel()
        self._recent_files = recent_files
        self.endResetModel()

        self.sig_files_changed.emit()

    def get_recent_files(self) -> list[str]:
        """The paths, newest first."""
        return self._recent_files

    def validate_files(self) -> None:
        """Removes entries whose file no longer exists."""
        for i, file_path in enumerate(self._recent_files):
            if not Path(file_path).is_file():
                self.remove_file(self.index(i))

    @QtCore.Slot()
    def update_config(self) -> None:
        """Writes the list to `Config.internal.recent_files`; connected to `sig_files_changed`."""
        Config.internal.recent_files = self._recent_files


class SectionListModel(QtCore.QAbstractListModel):
    """
    The sections of one channel, base section first.

    Owns the section ids: `add_section` names a section after its row, `remove_section` renumbers the rest. The
    display role is the pretty name, the decoration a lock icon, `UserRole` the `Section` itself.
    """

    def __init__(
        self,
        sections: list[Section] | None = None,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sections = sections or []

    @property
    def all_sections(self) -> list[Section]:
        """Base section first, then the user-created sections in creation order."""
        return list(self._sections)

    @property
    def editable_sections(self) -> list[Section]:
        """The user-created sections (everything but the base section), in creation order."""
        return list(self._sections)[1:]

    @override
    def rowCount(self, parent: ModelIndex | None = None) -> int:
        return len(self._sections)

    @override
    def data(
        self,
        index: ModelIndex,
        role: int = ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or not self._sections:
            return None
        row = index.row()
        if row >= self.rowCount():
            return None

        section = self._sections[row]

        if role == ItemDataRole.DisplayRole:
            return section.section_id.pretty_name()
        elif role == ItemDataRole.SizeHintRole:
            return QtCore.QSize(100, 31)
        elif role == ItemDataRole.UserRole:
            return section
        elif role == ItemDataRole.ToolTipRole:
            return repr(section)
        elif role == ItemDataRole.DecorationRole:
            return QtGui.QIcon(":icons/LockClosed.svg") if section.is_locked else QtGui.QIcon(":icons/LockOpen.svg")
        return None

    @staticmethod
    def _make_id(section: Section, row: int) -> SectionID:
        return SectionID(f"Section_{section.signal_name}_{row:03}")

    def add_section(self, section: Section) -> None:
        """Appends `section`, giving it the id for its row before the view sees it."""
        row = self.rowCount()
        section.section_id = self._make_id(section, row)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self._sections.append(section)
        self.endInsertRows()

    def remove_section(self, index: QtCore.QModelIndex) -> None:
        """Removes the section at `index` and renumbers the ones after it (see `refresh_section_ids`)."""
        row = index.row()
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._sections[row]
        self.endRemoveRows()
        self.refresh_section_ids()

    def get_section(self, index: QtCore.QModelIndex) -> Section | None:
        """The section at `index`, or `None` for an invalid index."""
        return self._sections[index.row()] if index.isValid() else None

    def get_base_section(self) -> Section | None:
        """Row 0, or `None` when the model is empty."""
        return self._sections[0] if self._sections else None

    def index_of(self, section: Section) -> QtCore.QModelIndex:
        """The model index of `section`, or an invalid index when it is not in the model."""
        for row, candidate in enumerate(self._sections):
            if candidate is section:
                return self.index(row)
        return QtCore.QModelIndex()

    def notify_section_changed(self, section: Section) -> None:
        """Tells the views that a section's display data (name, lock icon) changed."""
        index = self.index_of(section)
        if index.isValid():
            self.dataChanged.emit(index, index)

    def clear(self) -> None:
        """Removes every section (full reset)."""
        self.beginResetModel()
        self._sections.clear()
        self.endResetModel()

    def refresh_section_ids(self) -> None:
        """
        Re-derives every section id from its row and emits `dataChanged` for the rows whose id changed.

        Ids encode the row number, so deleting a section renames every section after it. Views and plot regions
        pick up the new names through `dataChanged`.
        """
        changed_rows: list[int] = []
        for row, section in enumerate(self._sections):
            new_id = self._make_id(section, row)
            if section.section_id != new_id:
                section.section_id = new_id
                changed_rows.append(row)
        if changed_rows:
            self.dataChanged.emit(self.index(changed_rows[0]), self.index(changed_rows[-1]))


class FileMetadata:
    """
    What is known about the open file: its columns and dtypes, the sampling rate, and the user's choice of signal
    and info column.

    Column names exist in two forms: as in the file (shown in the GUI, stored in `Config.internal`) and cleaned
    (`name_map`, used inside the data frames). `required_fields` lists what still blocks loading; the setters keep it
    current.
    """

    __slots__ = (
        "_columns",
        "_info_column",
        "_sampling_rate",
        "_schema",
        "_signal_column",
        "file_info",
        "name_map",
        "other_info",
        "required_fields",
    )

    def __init__(
        self,
        file_path: Path | str,
        columns: list[str],
        sampling_rate: int,
        schema: Mapping[str, pl.DataType] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        file_path
            Path of the file the metadata describes.
        columns
            Every column name in the file, in file order.
        sampling_rate
            Detected sampling rate, `0` when unknown (the field is then required).
        schema
            Column name to polars dtype. Only numeric columns are offered as signal or info column. Without a schema
            every non-reserved column counts as numeric.
        """
        self.required_fields: list[str] = []
        self.file_info = QtCore.QFileInfo(file_path)
        self._sampling_rate = sampling_rate
        if self._sampling_rate == 0:
            self.required_fields.append("sampling_rate")

        self._columns = columns
        self._schema: dict[str, pl.DataType] = dict(schema) if schema is not None else {}

        numeric = self.numeric_columns
        signal_col = Config.internal.last_signal_column
        if signal_col not in numeric:
            # The first numeric column is a valid default the user can change on the import page. Only a file
            # without any numeric column leaves the field unset, which blocks loading.
            signal_col = numeric[0] if numeric else ""
            if not numeric:
                self.required_fields.append("signal_column")
        self._signal_column = signal_col

        info_col = Config.internal.last_info_column
        if info_col not in numeric:
            info_col = COMBO_BOX_NO_SELECTION
        self._info_column = info_col

        self.name_map = {
            c: _clean_column_names(
                c,
                strip_underscores=True,
                case_type="lower",
                remove_special=True,
                strip_accents=True,
                truncate_limit=None,  # type: ignore
            )
            for c in self._columns
        }

        self.other_info: dict[str, Any] = {}

    @property
    def file_name(self) -> str:
        """File name with extension."""
        return self.file_info.fileName()

    @property
    def file_path(self) -> str:
        """Canonical absolute path."""
        return self.file_info.canonicalFilePath()

    @property
    def file_format(self) -> InputFileFormat:
        """The extension as `InputFileFormat`."""
        return InputFileFormat(f".{self.file_info.suffix()}")

    @property
    def all_columns(self) -> list[str]:
        """Every column of the file, whatever its dtype."""
        return list(self._columns)

    @property
    def numeric_columns(self) -> list[str]:
        """
        The columns that can be a signal or info column: numeric dtype and not a reserved name.

        Without a schema (see `__init__`) every non-reserved column is included.
        """
        return [
            c
            for c in self._columns
            if c not in RESERVED_COLUMN_NAMES and (c not in self._schema or self._schema[c].is_numeric())
        ]

    @property
    def column_names(self) -> list[str]:
        """Choices for the info column: the no-selection sentinel followed by the numeric columns."""
        return [COMBO_BOX_NO_SELECTION] + self.numeric_columns

    @property
    def valid_columns(self) -> list[str]:
        """Choices for the signal column: the numeric columns."""
        return self.numeric_columns

    @property
    def sampling_rate(self) -> int:
        """Samples per second; `0` while unknown, which makes it a required field."""
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, value: int) -> None:
        if "sampling_rate" in self.required_fields and value > 0:
            self.required_fields.remove("sampling_rate")
        elif value == 0 and "sampling_rate" not in self.required_fields:
            self.required_fields.append("sampling_rate")
        self._sampling_rate = value

    @property
    def signal_column(self) -> str:
        """File column name of the signal. A name that is not a numeric column makes it a required field."""
        return self._signal_column

    @signal_column.setter
    def signal_column(self, value: str) -> None:
        if value not in self.numeric_columns:
            if "signal_column" not in self.required_fields:
                self.required_fields.append("signal_column")
        elif "signal_column" in self.required_fields:
            self.required_fields.remove("signal_column")
        self._signal_column = value

    @property
    def info_column(self) -> str:
        """File column name of the info channel, or `COMBO_BOX_NO_SELECTION`. See `info_column_or_none`."""
        return self._info_column

    @info_column.setter
    def info_column(self, value: str | None) -> None:
        if value is None:
            value = COMBO_BOX_NO_SELECTION
        self._info_column = value

    @property
    def info_column_or_none(self) -> str | None:
        """
        The info column as the data layer expects it: `None` when the user made no selection.

        `info_column` keeps the `COMBO_BOX_NO_SELECTION` sentinel because the combo boxes display it. Everything that
        builds a `Section` must use this property instead so the sentinel never reaches the data frame.
        """
        return None if self._info_column == COMBO_BOX_NO_SELECTION else self._info_column

    @property
    def data_signal_column(self) -> str:
        """
        Name of the signal column inside the loaded data frame.

        `signal_column` is the name as it appears in the file and in the combo boxes. `DataController` renames every
        column through `name_map`, so the data layer must address columns by this cleaned name.
        """
        return self.name_map.get(self._signal_column, self._signal_column)

    @property
    def data_info_column(self) -> str | None:
        """Cleaned name of the info column inside the loaded data frame, or `None` when none is selected."""
        info = self.info_column_or_none
        return None if info is None else self.name_map.get(info, info)

    def missing_fields_text(self) -> str:
        """Human-readable list of the required fields that are still unset, or an empty string."""
        if not self.required_fields:
            return ""
        labels = [REQUIRED_FIELD_LABELS.get(f, f) for f in self.required_fields]
        return "Missing: " + ", ".join(labels)

    def to_dict(self) -> MetadataDict:
        """Plain-dictionary form for the metadata dialog."""
        return {
            "file_path": self.file_path,
            "sampling_rate": self.sampling_rate,
            "signal_column": self.signal_column,
            "info_column": self.info_column,
            "column_names": self.column_names,
        }
