from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.utils import set_font


class SectionListView(QtWidgets.QListView):
    sig_delete_current_item = QtCore.Signal(QtCore.QModelIndex)
    sig_show_summary = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._select_right_clicked_row = True
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton or self._select_right_clicked_row:
            super().mousePressEvent(event)

        QtWidgets.QWidget.mousePressEvent(self, event)

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

        self.command_bar_section_list = QtWidgets.QToolBar("command_bar_section_list")
        self.command_bar_section_list.setIconSize(QtCore.QSize(16, 16))
        self.command_bar_section_list.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        layout.addWidget(self.command_bar_section_list)

        self.btn_confirm = QtWidgets.QPushButton("Confirm")
        self.btn_cancel = QtWidgets.QPushButton("Cancel")

        l_btn_container = QtWidgets.QHBoxLayout()
        l_btn_container.setContentsMargins(0, 0, 0, 0)
        l_btn_container.addWidget(self.btn_confirm)
        l_btn_container.addWidget(self.btn_cancel)
        self.btn_container = QtWidgets.QWidget()
        self.btn_container.setLayout(l_btn_container)
        layout.addWidget(self.btn_container)

        self.label_active_section = QtWidgets.QLabel("Active Section:")
        set_font(self.label_active_section, font_size=14, weight=QtGui.QFont.Weight.DemiBold)
        layout.addWidget(self.label_active_section)

        self.section_list = SectionListView()
        layout.addWidget(self.section_list)

        self.setLayout(layout)


class SectionListDock(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("SectionListDock")
        self.setWindowTitle("Section List")
        self.setWindowIcon(QtGui.QIcon("://icons/app_icon.svg"))

        self._widget = SectionListWidget()
        self.list_view = self._widget.section_list
        self.command_bar = self._widget.command_bar_section_list
        self.label_active_section = self._widget.label_active_section
        self.btn_confirm = self._widget.btn_confirm
        self.btn_cancel = self._widget.btn_cancel
        self.btn_container = self._widget.btn_container

        self.setWidget(self._widget)
