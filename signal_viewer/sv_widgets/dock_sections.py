"""
The Sections dock: the list of sections of the active channel, its command bar, and the Confirm / Cancel buttons
shown while a new section is being selected on the plot.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.utils import set_font


class SectionListView(QtWidgets.QListView):
    """
    List view of the sections with a context menu.

    Emits `sig_delete_item` / `sig_show_summary` with the current index when the corresponding actions fire, so the
    actions can live on the dock's command bar and in the context menu alike.
    """

    sig_delete_item = QtCore.Signal(QtCore.QModelIndex)
    sig_show_summary = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._select_right_clicked_row = True
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Selects the row under the cursor on right-click too, so the context menu acts on the clicked section."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton or self._select_right_clicked_row:
            super().mousePressEvent(event)

        QtWidgets.QWidget.mousePressEvent(self, event)

    @QtCore.Slot()
    def emit_sig_delete_item(self) -> None:
        """
        Emit `sig_delete_item` signal with the current (selected) item index
        """
        self.sig_delete_item.emit(self.currentIndex())

    @QtCore.Slot()
    def emit_sig_show_summary(self) -> None:
        """
        Emit `sig_show_summary` signal with the current (selected) item index
        """
        self.sig_show_summary.emit(self.currentIndex())


class SectionsWidget(QtWidgets.QWidget):
    """Contents of the dock: command bar, Confirm / Cancel buttons, active-section label and the list view."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.command_bar_section_list = QtWidgets.QToolBar("command_bar_section_list")
        self.command_bar_section_list.setIconSize(QtCore.QSize(16, 16))
        self.command_bar_section_list.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        layout.addWidget(self.command_bar_section_list)

        self.btn_confirm = QtWidgets.QPushButton("Confirm")
        self.btn_cancel = QtWidgets.QPushButton("Cancel")

        btns_layout = QtWidgets.QHBoxLayout()
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.addWidget(self.btn_confirm)
        btns_layout.addWidget(self.btn_cancel)
        self.btn_container = QtWidgets.QWidget()
        self.btn_container.setLayout(btns_layout)
        layout.addWidget(self.btn_container)

        self.label_active_section = QtWidgets.QLabel("Active Section:")
        set_font(self.label_active_section, font_size=14, weight=QtGui.QFont.Weight.DemiBold)
        layout.addWidget(self.label_active_section)

        self.section_list_view = SectionListView()
        layout.addWidget(self.section_list_view, stretch=1)

        self.setLayout(layout)


class SectionsDock(QtWidgets.QDockWidget):
    """
    The Sections dock. Exposes the inner widgets (`list_view`, `command_bar`, `btn_confirm`, `btn_cancel`,
    `btn_container`, `label_active_section`) as attributes for `SVGUI` and `SVApp` to wire up.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("SectionsDock")
        self.setWindowTitle("Sections")
        self.setWindowIcon(QtGui.QIcon("://icons/app_icon.png"))

        self._widget = SectionsWidget()
        self.list_view = self._widget.section_list_view
        self.command_bar = self._widget.command_bar_section_list
        self.label_active_section = self._widget.label_active_section
        self.btn_confirm = self._widget.btn_confirm
        self.btn_cancel = self._widget.btn_cancel
        self.btn_container = self._widget.btn_container

        self.setWidget(self._widget)
