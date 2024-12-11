import typing as t

import qfluentwidgets as qfw
from PySide6 import QtCore, QtGui, QtWidgets


class SectionListView(qfw.ListView):
    sig_delete_current_item: t.ClassVar[QtCore.Signal] = QtCore.Signal(QtCore.QModelIndex)
    sig_show_summary: t.ClassVar[QtCore.Signal] = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSelectRightClickedRow(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

    @QtCore.Slot()
    def emit_delete_current_request(self) -> None:
        index = self.currentIndex()
        self.sig_delete_current_item.emit(index)

    @QtCore.Slot()
    def emit_show_summary_request(self) -> None:
        index = self.currentIndex()
        self.sig_show_summary.emit(index)


class SectionListWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()

        self.list_view = SectionListView()

        label_active_section = qfw.StrongBodyLabel("Active Section: ", self)
        layout.addWidget(label_active_section)
        self.label_active_section = label_active_section

        command_bar = qfw.CommandBar()
        command_bar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        command_bar.setObjectName("command_bar_section_list")
        layout.addWidget(command_bar)
        self.command_bar = command_bar

        confirm_cancel_btns = QtWidgets.QWidget()
        confirm_cancel_layout = QtWidgets.QHBoxLayout(confirm_cancel_btns)
        confirm_cancel_layout.setContentsMargins(0, 0, 0, 0)

        confirm_btn = qfw.PushButton(icon=QtGui.QIcon("://icons/CheckmarkCircle.svg"), text="Confirm")
        confirm_cancel_layout.addWidget(confirm_btn)
        self.btn_confirm = confirm_btn

        cancel_btn = qfw.PushButton(icon=QtGui.QIcon("://icons/DismissCircle.svg"), text="Cancel")
        confirm_cancel_layout.addWidget(cancel_btn)
        self.btn_cancel = cancel_btn

        self.btn_container = confirm_cancel_btns
        confirm_cancel_btns.setLayout(confirm_cancel_layout)
        layout.addWidget(confirm_cancel_btns)

        layout.addWidget(self.list_view)
        self.main_layout = layout
        self.setLayout(layout)


class SectionListDock(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("SectionListDock")
        self.setWindowTitle("Section List")
        self.setWindowIcon(QtGui.QIcon("://icons/app_icon.svg"))

        self._widget = SectionListWidget()
        self.list_view = self._widget.list_view
        self.command_bar = self._widget.command_bar
        self.label_active_section = self._widget.label_active_section
        self.btn_confirm = self._widget.btn_confirm
        self.btn_cancel = self._widget.btn_cancel
        self.btn_container = self._widget.btn_container

        self.setWidget(self._widget)
