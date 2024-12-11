import datetime
import typing as t
from pathlib import Path

import polars as pl
from PySide6 import QtCore, QtGui

import signal_viewer.type_defs as _t
from signal_viewer.constants import COMBO_BOX_NO_SELECTION, RESERVED_COLUMN_NAMES
from signal_viewer.enum_defs import InputFileFormat
from signal_viewer.sv_config import Config

# from .gui.icons import AppIcons
from signal_viewer.sv_logic.section import Section, SectionID
from signal_viewer.utils import format_file_path, human_readable_timedelta

ItemDataRole = QtCore.Qt.ItemDataRole
type ModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class DataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.df = pl.DataFrame()
        self._float_precision = Config.data.float_precision

    def set_df(self, df: pl.DataFrame) -> None:
        self.beginResetModel()
        self._float_precision = Config.data.float_precision
        self.df = df
        self.endResetModel()

    def rowCount(self, parent: ModelIndex | None = None) -> int:
        return self.df.height

    def columnCount(self, parent: ModelIndex | None = None) -> int:
        return self.df.width

    def data(
        self,
        index: ModelIndex,
        role: int = ItemDataRole.DisplayRole,
    ) -> t.Any:
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
        elif role == ItemDataRole.ToolTipRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self.df.schema[self.df.columns[section]])
        return None


class FileListModel(QtCore.QAbstractListModel):
    sig_files_changed = QtCore.Signal()

    def __init__(
        self, recent_files: list[str] | None = None, validate_files: bool = True, max_files: int = 10, parent: QtCore.QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._recent_files = recent_files or []
        self._max_files = max_files

        self.sig_files_changed.connect(self.update_config)

        if validate_files:
            self.validate_files()

    def rowCount(self, parent: ModelIndex | None = None) -> int:
        return len(self._recent_files)

    def data(self, index: ModelIndex, role: int = ItemDataRole.DisplayRole) -> t.Any:
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

    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: int = ItemDataRole.DisplayRole
    ) -> t.Any:
        if role != ItemDataRole.DisplayRole:
            return None

        if orientation == QtCore.Qt.Orientation.Horizontal:
            return "Recent Files"

        return str(section + 1)

    def add_file(self, file_path: str) -> None:
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
        row = index.row()
        parent = self.index(0, 0)
        self.beginRemoveRows(parent, row, row)
        del self._recent_files[row]
        self.endRemoveRows()

        self.sig_files_changed.emit()

    def clear(self) -> None:
        self.beginResetModel()
        self._recent_files.clear()
        self.endResetModel()

        self.sig_files_changed.emit()

    def set_recent_files(self, recent_files: list[str]) -> None:
        self.beginResetModel()
        self._recent_files = recent_files
        self.endResetModel()

        self.sig_files_changed.emit()

    def get_recent_files(self) -> list[str]:
        return self._recent_files

    def validate_files(self) -> None:
        for i, file_path in enumerate(self._recent_files):
            if not Path(file_path).is_file():
                self.remove_file(self.index(i))

    @QtCore.Slot()
    def update_config(self) -> None:
        Config.internal.recent_files = self._recent_files


class SectionListModel(QtCore.QAbstractListModel):
    def __init__(
        self,
        sections: list["Section"] | None = None,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sections = sections or []

    @property
    def editable_sections(self) -> list["Section"]:
        return list(self._sections)[1:]

    def rowCount(self, parent: ModelIndex | None = None) -> int:
        return len(self._sections)

    def data(
        self,
        index: ModelIndex,
        role: int = ItemDataRole.DisplayRole,
    ) -> t.Any:
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

    def add_section(self, section: "Section") -> None:
        parent = self.index(0, 0)
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._sections.append(section)
        self.refresh_section_ids()
        self.endInsertRows()

    def remove_section(self, index: QtCore.QModelIndex) -> None:
        row = index.row()
        parent = self.index(0, 0)
        self.beginRemoveRows(parent, row, row)
        self._sections.remove(self._sections[row])
        self.refresh_section_ids()
        self.endRemoveRows()

    def get_section(self, index: QtCore.QModelIndex) -> "Section | None":
        return self._sections[index.row()] if index.isValid() else None

    def get_base_section(self) -> "Section | None":
        return self._sections[0] if self._sections else None

    def clear(self) -> None:
        self.beginResetModel()
        self._sections.clear()
        self.endResetModel()

    def refresh_section_ids(self) -> None:
        for i, section in enumerate(self._sections):
            section.section_id = SectionID(f"Section_{section.signal_name}_{i:03}")


class FileMetadata:
    __slots__ = (
        "required_fields",
        "file_info",
        "_sampling_rate",
        "_columns",
        "_signal_column",
        "_info_column",
        "other_info",
    )

    def __init__(self, file_path: Path | str, columns: list[str], sampling_rate: int) -> None:
        self.required_fields: list[str] = []
        self.file_info = QtCore.QFileInfo(file_path)
        self._sampling_rate = sampling_rate
        if self._sampling_rate == 0:
            self.required_fields.append("sampling_rate")

        self._columns = columns
        signal_col = Config.internal.last_signal_column
        if signal_col not in self._columns or signal_col in RESERVED_COLUMN_NAMES:
            self.required_fields.append("signal_column")
            signal_col = self._columns[0]
        self._signal_column = signal_col

        info_col = Config.internal.last_info_column
        if info_col not in self._columns:
            info_col = COMBO_BOX_NO_SELECTION
        self._info_column = info_col

        self.other_info: dict[str, t.Any] = {}

    @property
    def file_name(self) -> str:
        return self.file_info.fileName()

    @property
    def file_path(self) -> str:
        return self.file_info.canonicalFilePath()

    @property
    def file_format(self) -> InputFileFormat:
        return InputFileFormat(f".{self.file_info.suffix()}")

    @property
    def column_names(self) -> list[str]:
        return [COMBO_BOX_NO_SELECTION] + self._columns

    @column_names.setter
    def column_names(self, value: list[str]) -> None:
        self._columns = value

    @property
    def valid_columns(self) -> list[str]:
        return self._columns

    @property
    def sampling_rate(self) -> int:
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
        return self._signal_column

    @signal_column.setter
    def signal_column(self, value: str) -> None:
        if value in RESERVED_COLUMN_NAMES:
            self.required_fields.append("signal_column")
        elif "signal_column" in self.required_fields:
            self.required_fields.remove("signal_column")
        self._signal_column = value

    @property
    def info_column(self) -> str:
        return self._info_column

    @info_column.setter
    def info_column(self, value: str | None) -> None:
        if value is None:
            value = COMBO_BOX_NO_SELECTION
        self._info_column = value

    def to_dict(self) -> _t.MetadataDict:
        return {
            "file_path": self.file_path,
            "sampling_rate": self.sampling_rate,
            "signal_column": self.signal_column,
            "info_column": self.info_column,
            "column_names": self.column_names,
        }
