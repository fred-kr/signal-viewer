# QStyleOption members are initialized as needed (i think), meaning pyright can't infer their types, so we disable some
# pyright checks for this file.

# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportUnknownVariableType=false

import enum
import typing as t

from PySide6 import QtCore, QtGui, QtWidgets

ItemDataRole = QtCore.Qt.ItemDataRole

ItemTypeRole = ItemDataRole.UserRole + 1

type ModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class ItemType(enum.Enum):
    SEPARATOR = enum.auto()
    PARENT = enum.auto()
    CHILD = enum.auto()


class GroupedComboBox(QtWidgets.QComboBox):
    """
    A QComboBox variant that allows grouping of items under a header.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._model = QtGui.QStandardItemModel(self)
        self._view = QtWidgets.QTreeView(self)
        self._view.setHeaderHidden(True)
        self._view.setRootIsDecorated(False)

        self.setModel(self._model)
        self.setView(self._view)
        self.setItemDelegate(GroupedComboBoxDelegate(self))

    def add_separator(self) -> None:
        """
        Add a separator item to the combo box.
        """
        item = QtGui.QStandardItem()
        item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
        item.setData(ItemType.SEPARATOR, ItemTypeRole)
        self._model.appendRow(item)

    def add_parent_item(self, text: str) -> None:
        """
        Add a parent item to the combo box.

        :param text: The text to be displayed for the parent item.
        :type text: str
        """
        item = QtGui.QStandardItem(text)
        flags = item.flags()
        flags &= ~QtCore.Qt.ItemFlag.ItemIsSelectable
        item.setFlags(flags)
        item.setData(ItemType.PARENT, ItemTypeRole)

        font = item.font()
        font.setBold(True)
        item.setFont(font)

        self._model.appendRow(item)

    def add_child_item(self, text: str, data: t.Any | None = None) -> None:
        """
        Add a child item to the combo box.

        :param text: The text to be displayed for the child item.
        :type text: str
        :param data: The data associated with the child item.
        :type data: Any
        """
        item = QtGui.QStandardItem(text)
        item.setData(data, ItemDataRole.UserRole)
        item.setData(ItemType.CHILD, ItemTypeRole)

        self._model.appendRow(item)

    def currentData(self, role: int = ItemDataRole.UserRole) -> t.Any | None:
        """
        Returns the data associated with the currently selected item in the combo box.

        :param role: The role for which to retrieve the data, defaults to ItemDataRole.UserRole
        :type role: int, optional
        :return: The data associated with the currently selected (child) item, or None if no item is selected or the
            selected item is not a child item.
        :rtype: Any | None
        """
        index = self.currentIndex()
        if index >= 0:
            item = self._model.item(index)
            if item.data(ItemTypeRole) == ItemType.CHILD:
                return item.data(ItemDataRole.UserRole)

        return None


class GroupedComboBoxDelegate(QtWidgets.QStyledItemDelegate):
    def sizeHint(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: ModelIndex,
    ) -> QtCore.QSize:
        item_type = index.data(ItemTypeRole)
        if item_type == ItemType.SEPARATOR:
            return QtCore.QSize(0, 5)
        else:
            return super().sizeHint(option, index)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: ModelIndex,
    ) -> None:
        item_type = index.data(ItemTypeRole)
        if item_type == ItemType.SEPARATOR:
            y = (option.rect.top() + option.rect.bottom()) // 2
            painter.setPen(option.palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Dark))
            painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        elif item_type == ItemType.PARENT:
            painter.save()
            painter.fillRect(option.rect, option.palette.midlight())
            option.font.setBold(True)
            option.state &= ~QtWidgets.QStyle.StateFlag.State_Selected
            super().paint(painter, option, index)
            painter.restore()
        elif item_type == ItemType.CHILD:
            indent = 20  # Pixels to indent child items by
            option.rect.adjust(indent, 0, 0, 0)
            super().paint(painter, option, index)
        else:
            super().paint(painter, option, index)

    def editorEvent(
        self,
        event: QtCore.QEvent,
        model: QtCore.QAbstractItemModel,
        option: QtWidgets.QStyleOptionViewItem,
        index: ModelIndex,
    ) -> bool:
        item_type = index.data(ItemTypeRole)
        if item_type != ItemType.CHILD:
            return False  # Prevent selection of non-child items

        return super().editorEvent(event, model, option, index)
