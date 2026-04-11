import traceback
import types
import typing as t

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

ItemDataRole = QtCore.Qt.ItemDataRole
type ModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class DataTreeWidget(QtWidgets.QTreeWidget):
    """
    Widget for displaying hierarchical python data structures (eg. nested dicts, lists, arrays, etc.)

    Based on `pyqtgraph.widgets.DataTreeWidget`.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        data: dict[str, t.Any] | None = None,
        allow_edit: bool = False,
        hide_root: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setColumnCount(3)
        self.setHeaderLabels(["Name", "Type", "Value"])
        self.setAlternatingRowColors(True)

        self._allow_edit = allow_edit

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        if data is not None:
            self.set_data(data, hide_root=hide_root)

    def set_data(self, data: dict[str, t.Any], hide_root: bool = True) -> None:
        """
        Set the data to be displayed.

        Args:
            data (dict[str, Any]): The data to be displayed.
            hide_root (bool, optional): Whether to hide the root node. Defaults to True.
        """
        self.clear()

        self._widgets: list[QtWidgets.QWidget] = []
        self._nodes: dict[tuple[str | int, ...], QtWidgets.QTreeWidgetItem] = {}
        self.build_tree(data, self.invisibleRootItem(), hide_root=hide_root)
        self.expandToDepth(3)
        self.resizeColumnToContents(0)

    def build_tree(
        self,
        data: dict[str, t.Any],
        parent: QtWidgets.QTreeWidgetItem,
        name: str = "",
        hide_root: bool = True,
        path: tuple[str | int, ...] = (),
    ) -> None:
        """
        Recursively build the tree from the given data.

        Args:
            data (dict[str, Any]): A dictionary containing the data to be displayed.
            parent (QtWidgets.QTreeWidgetItem): The parent item under which the data will be displayed.
            name (str, optional): The name to be displayed for the current node. Defaults to "".
            hide_root (bool, optional): Whether to hide the root node. Defaults to True.
            path (tuple[str | int, ...], optional): A tuple containing the path to the current node. Defaults to ().
        """
        if hide_root:
            node = parent
        else:
            node = QtWidgets.QTreeWidgetItem([name, "", ""])
            parent.addChild(node)

        self._nodes[path] = node

        type_str, desc, childs, widget = self.parse_data(data)

        node.setText(1, type_str)
        node.setData(2, ItemDataRole.UserRole, data)

        if len(desc) > 100:
            desc = f"{desc[:97]}..."
            if widget is None:
                widget = QtWidgets.QPlainTextEdit()
                widget.setReadOnly(True)
                widget.setPlainText(desc)
        else:
            node.setText(2, desc)

        if widget is not None:
            self._widgets.append(widget)
            sub_node = QtWidgets.QTreeWidgetItem(["", "", ""])
            node.addChild(sub_node)
            self.setItemWidget(sub_node, 0, widget)
            sub_node.setFirstColumnSpanned(True)

        for key, child_data in childs.items():
            self.build_tree(child_data, node, str(key), path=path + (key,))

    def parse_data(self, data: t.Any) -> tuple[str, str, dict[int, t.Any], QtWidgets.QWidget | None]:
        """
        Parse the given data and return its type, description, children, and widget.

        Args:
            data (Any): Data to be parsed.

        Returns:
            tuple ((str, str, dict[int, Any], QtWidgets.QWidget | None)): type string, description text, dictionary of
            child data to recursively parse, widget to display the data if supported
        """
        type_str = type(data).__name__
        if type_str == "instance":
            type_str += f": {data.__class__.__name__}"
        widget = None
        desc = ""
        childs: dict[int, t.Any] = {}

        if isinstance(data, dict):
            desc = f"length={len(data)}"  # type: ignore
            childs = dict(data.items())  # type: ignore
        elif isinstance(data, (list, tuple)):
            desc = f"length={len(data)}"  # type: ignore
            childs = dict(enumerate(data))  # type: ignore
        elif isinstance(data, np.ndarray):
            desc = f"shape={data.shape} dtype={data.dtype}"
            if data.size > 1000:
                summary = f"min={data.min()}, max={data.max()}, mean={data.mean():.2f}"
                widget = QtWidgets.QPushButton(f"Array summary: {summary}")
                widget.clicked.connect(lambda: self.show_full_array(data))  # type: ignore
            else:
                table = pg.TableWidget()
                table.setData(data)
                table.setMaximumHeight(200)
                widget = table
        elif isinstance(data, types.TracebackType):
            frames = list(map(str.strip, traceback.format_list(traceback.extract_tb(data))))
            widget = QtWidgets.QPlainTextEdit()
            widget.setPlainText("\n".join(frames))
            widget.setMaximumHeight(200)
            widget.setReadOnly(True)
        else:
            desc = str(data)

        return type_str, desc, childs, widget

    def filter_tree(self, text: str) -> None:
        """
        Search the tree for items containing the given text and hide/show them accordingly.

        Args:
            text (str): The text to search for.
        """
        for item in self._nodes.values():
            item.setHidden(item.text(0).lower().find(text.lower()) == -1)

    def toggle_sort(self) -> None:
        self.sortItems(0, QtCore.Qt.SortOrder.AscendingOrder)

    def show_context_menu(self, pos: QtCore.QPoint) -> None:
        item = self.itemAt(pos)
        if not item:
            return

        menu = QtWidgets.QMenu(self)
        copy_name_action = QtGui.QAction("Copy Name")
        copy_type_action = QtGui.QAction("Copy Type")
        copy_value_action = QtGui.QAction("Copy Value")

        menu.addAction(copy_name_action)
        menu.addAction(copy_type_action)
        menu.addAction(copy_value_action)

        copy_name_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(item.text(0)))
        copy_type_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(item.text(1)))
        copy_value_action.triggered.connect(lambda: QtWidgets.QApplication.clipboard().setText(item.text(2)))
        if self._allow_edit:
            edit_action = QtGui.QAction("Edit Value")
            menu.addAction(edit_action)
            edit_action.triggered.connect(lambda: self.edit_item_value(item))

        menu.exec(self.mapToGlobal(pos))

    def edit_item_value(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """
        Edit the value of the given item.

        Args:
            item (QtWidgets.QTreeWidgetItem): The item to edit.
        """
        if not self._allow_edit:
            return
        data = item.data(2, ItemDataRole.UserRole)
        if isinstance(data, (int, float, str, bool)):
            new_value, ok = QtWidgets.QInputDialog.getText(
                self,
                "Edit Value",
                "Enter new value:",
                text=str(data),
            )
            if ok:
                try:
                    if isinstance(data, bool):
                        new_data = new_value.lower() in ("true", "1", "yes")
                    else:
                        new_data = type(data)(new_value)

                    item.setData(2, ItemDataRole.UserRole, new_data)
                    item.setText(2, str(new_data))
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "Invalid Input", "Could not convert input to correct type")

    def toggle_full_text(self, item: QtWidgets.QTreeWidgetItem, widget: QtWidgets.QWidget) -> None:
        widget.setVisible(not widget.isVisible())

    def show_full_array(self, data: npt.NDArray[t.Any]) -> None:
        dialog = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        table = pg.TableWidget()
        table.setData(data)
        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec()


class SearchableDataTreeWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, allow_edit: bool = False) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.filter_tree)

        self.btn_sort = QtWidgets.QPushButton("Sort")
        self.btn_sort.clicked.connect(self.toggle_sort)

        self.data_tree = DataTreeWidget(allow_edit=allow_edit)

        layout.addWidget(self.search_bar)
        layout.addWidget(self.btn_sort)
        layout.addWidget(self.data_tree)

        self.setLayout(layout)

    def filter_tree(self, text: str) -> None:
        self.data_tree.filter_tree(text)

    def toggle_sort(self) -> None:
        self.data_tree.toggle_sort()

    def set_data(self, data: dict[str, t.Any], hide_root: bool = False) -> None:
        self.data_tree.set_data(data, hide_root)

    def collapseAll(self) -> None:
        self.data_tree.collapseAll()

    def clear(self) -> None:
        self.data_tree.clear()
