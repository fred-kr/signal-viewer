import os
from typing import TYPE_CHECKING

import pyside_config as qconfig
from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import OverlayWidget, SearchableDataTreeWidget

import signal_viewer.type_defs as _t
from signal_viewer.constants import INDEX_COL
from signal_viewer.enum_defs import LogLevel
from signal_viewer.generated.ui_main_window import Ui_MainWindow
from signal_viewer.sv_config import Config
from signal_viewer.sv_widgets.dlg_metadata import MetadataDialog
from signal_viewer.sv_widgets.dock_log_window import StatusMessageDock
from signal_viewer.sv_widgets.dock_param_inputs import InputsDock
from signal_viewer.sv_widgets.dock_sections import SectionListDock
from signal_viewer.utils import get_app

if TYPE_CHECKING:
    from signal_viewer.sv_app import SVApp


class SVGUI(QtWidgets.QMainWindow):
    sig_metadata_changed = QtCore.Signal(dict)
    sig_table_refresh_requested = QtCore.Signal()
    sig_export_requested = QtCore.Signal(str)

    def __init__(self, sv_app: "SVApp", version: str = "0.0.0") -> None:
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setObjectName("SVGUI")

        self.sv_app = sv_app

        self._setup_window()

        self.overlay_widget = OverlayWidget(self)
        self.overlay_widget.hide()

        self._setup_docks()
        self._setup_actions()
        self._setup_toolbars()
        self._setup_menus()
        self._setup_widgets()
        self._finalize_setup()
        if os.environ.get("DEV", "0") == "1":
            self._add_console_dock()

    def _setup_window(self) -> None:
        self.setWindowTitle("SignalViewer")
        self.setWindowIcon(QtGui.QIcon("://icons/app_icon.svg"))

        desktop = QtWidgets.QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def switch_to(self, widget: QtWidgets.QWidget) -> None:
        self.ui.tab_widget_main.setCurrentWidget(widget)

    def _setup_widgets(self) -> None:
        self.dialog_meta = MetadataDialog(self)

        self.ui.table_view_import_data.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.ui.table_view_import_data.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.table_view_import_data.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.table_view_import_data.customContextMenuRequested.connect(self.show_data_view_context_menu)

        self.ui.table_view_result_peaks.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.ui.table_view_result_peaks.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.ui.table_view_result_peaks.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.table_view_result_peaks.customContextMenuRequested.connect(self.show_result_view_context_menu)

        self.ui.table_view_result_rate.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.ui.table_view_result_rate.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.table_view_result_rate.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.table_view_result_rate.customContextMenuRequested.connect(self.show_result_view_context_menu)

        layout = QtWidgets.QVBoxLayout()
        data_tree_widget = SearchableDataTreeWidget()
        data_tree_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addWidget(data_tree_widget)
        self.dialog_meta.container_additional_metadata.setLayout(layout)
        self.data_tree_widget_additional_metadata = data_tree_widget

        # self.btn_export_all_results.setIcon(QtGui.QIcon("://icons/ArrowExportLtr"))
        self.ui.btn_export_all_results.clicked.connect(lambda: self.sig_export_requested.emit("hdf5"))

        self.ui.tab_widget_main.setCurrentIndex(0)

    def _setup_docks(self) -> None:  # sourcery skip: extract-duplicate-method
        dwa = QtCore.Qt.DockWidgetArea

        dock_status = StatusMessageDock()
        self.addDockWidget(dwa.BottomDockWidgetArea, dock_status)
        self.dock_status_log = dock_status

        dock_sections = SectionListDock()
        self.addDockWidget(dwa.RightDockWidgetArea, dock_sections)
        self.dock_sections = dock_sections
        self.dock_sections.setEnabled(False)

        dock_parameters = InputsDock()
        self.addDockWidget(dwa.RightDockWidgetArea, dock_parameters)
        self.dock_parameters = dock_parameters
        self.dock_parameters.setEnabled(False)

    def _add_console_dock(self) -> None:
        try:
            from pyside_widgets import JupyterConsoleWindow

            import signal_viewer as sv
        except ImportError:
            logger.warning("Unable to import the console widget. Console is unavailable.")
            return

        console_window = JupyterConsoleWindow(
            namespace=dict(
                sv=sv,
                sv_app=get_app(),
                sv_gui=self,
            )
        )
        console_window.setVisible(False)

        self.ui.menu_view.addSeparator()
        self.ui.menu_view.addAction(console_window.toggle_view_action)
        self.console_window = console_window

    def _setup_actions(self) -> None:
        self.action_show_section_summary = QtGui.QAction(QtGui.QIcon("://icons/Info"), "Show Section Summary", self)

        self.action_toggle_whats_this_mode = QtWidgets.QWhatsThis.createAction(self)
        self.action_toggle_whats_this_mode.setIcon(QtGui.QIcon("://icons/Question"))

        self.action_export_to_csv = QtGui.QAction(QtGui.QIcon("://icons/ArrowExportLtr"), "Export to CSV")
        self.action_export_to_xlsx = QtGui.QAction(QtGui.QIcon("://icons/ArrowExportLtr"), "Export to XLSX")
        self.action_export_to_hdf5 = QtGui.QAction(QtGui.QIcon("://icons/ArrowExportLtr"), "Export to HDF5")

        self.ui.action_toggle_auto_scaling.setChecked(True)

    def _setup_toolbars(self) -> None:
        self.tool_bar_editing = self._setup_toolbar(
            "tool_bar_editing", [self.ui.action_toggle_auto_scaling, self.ui.action_show_section_overview]
        )

        self.tool_bar_help = self._setup_toolbar(
            "tool_bar_help", [self.ui.action_show_user_guide, self.action_toggle_whats_this_mode]
        )

        self.dock_sections.command_bar.addActions(
            [
                self.ui.action_create_new_section,
                self.ui.action_remove_section,
                self.ui.action_mark_section_done,
                self.ui.action_unlock_section,
                self.action_show_section_summary,
                self.ui.action_show_section_overview,
            ]
        )

        self.command_bar_section_list = self.dock_sections.command_bar

        self.ui.action_remove_section.triggered.connect(self.dock_sections.list_view.emit_delete_current_request)
        self.action_show_section_summary.triggered.connect(self.dock_sections.list_view.emit_show_summary_request)
        self.dock_sections.list_view.customContextMenuRequested.connect(self.show_section_list_context_menu)

    def _setup_toolbar(self, name: str, actions: list[QtGui.QAction], movable: bool = False) -> QtWidgets.QToolBar:
        tb = QtWidgets.QToolBar(name)
        tb.setIconSize(QtCore.QSize(16, 16))
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setObjectName(name)
        tb.setMovable(movable)
        tb.addActions(actions)
        self.addToolBar(tb)
        return tb

    @QtCore.Slot(QtCore.QPoint)
    def show_section_list_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(parent=self.dock_sections.list_view)
        menu.addAction(self.ui.action_remove_section)
        menu.addAction(self.action_show_section_summary)
        menu.exec(QtGui.QCursor.pos())

    def _setup_menus(self) -> None:
        self.ui.menu_view.addActions(
            [
                self.dock_sections.toggleViewAction(),
                self.dock_status_log.toggleViewAction(),
                self.dock_parameters.toggleViewAction(),
            ]
        )

        self.ui.menu_plot.insertSeparator(self.ui.action_show_section_overview)

        self.ui.menu_help.addSeparator()
        self.ui.menu_help.addAction(self.dock_status_log.toggleViewAction())
        self.ui.menu_help.insertAction(self.ui.action_show_user_guide, self.action_toggle_whats_this_mode)

        self.menu_export = QtWidgets.QMenu()
        self.menu_export.addActions([self.action_export_to_csv, self.action_export_to_xlsx, self.action_export_to_hdf5])

    def hide_all_docks(self) -> None:
        self.dock_status_log.hide()
        self.dock_parameters.hide()
        self.dock_sections.hide()

    def _finalize_setup(self) -> None:
        self.read_settings()
        self._connect_signals()
        self.show_section_confirm_cancel(False)
        self.hide_all_docks()
        self._on_page_changed(0)

    def _connect_signals(self) -> None:
        self.ui.tab_widget_main.currentChanged.connect(self._on_page_changed)

        self.ui.spin_box_sampling_rate_import_page.valueChanged.connect(
            self.dialog_meta.spin_box_sampling_rate.setValue
        )
        self.ui.combo_box_info_column_import_page.currentTextChanged.connect(
            self.dialog_meta.combo_box_info_column.setCurrentText
        )
        self.ui.combo_box_signal_column_import_page.currentTextChanged.connect(
            self.dialog_meta.combo_box_signal_column.setCurrentText
        )

        self.dialog_meta.spin_box_sampling_rate.valueChanged.connect(self._on_dialog_sampling_rate_changed)
        self.dialog_meta.combo_box_info_column.currentTextChanged.connect(
            self.ui.combo_box_info_column_import_page.setCurrentText
        )
        self.dialog_meta.combo_box_signal_column.currentTextChanged.connect(self._on_dialog_signal_column_changed)

        self.dock_status_log.log_text_box.sig_log_message.connect(self.maybe_show_error_dialog)
        self.dock_sections.btn_confirm.clicked.connect(self.ui.action_confirm_section.trigger)
        self.dock_sections.btn_cancel.clicked.connect(self.ui.action_cancel_section.trigger)

        self.action_export_to_csv.triggered.connect(lambda: self.sig_export_requested.emit("csv"))
        self.action_export_to_xlsx.triggered.connect(lambda: self.sig_export_requested.emit("xlsx"))
        self.ui.btn_export_to_excel.clicked.connect(lambda: self.sig_export_requested.emit("xlsx"))
        self.action_export_to_hdf5.triggered.connect(lambda: self.sig_export_requested.emit("hdf5"))

    @QtCore.Slot(int)
    def _on_dialog_sampling_rate_changed(self, value: int) -> None:
        if value > 0:
            self.dialog_meta.spin_box_sampling_rate.setProperty("requiresInput", False)
        else:
            self.dialog_meta.spin_box_sampling_rate.setProperty("requiresInput", True)
        self.dialog_meta.spin_box_sampling_rate.style().unpolish(self.dialog_meta.spin_box_sampling_rate)
        self.dialog_meta.spin_box_sampling_rate.style().polish(self.dialog_meta.spin_box_sampling_rate)
        self.dialog_meta.spin_box_sampling_rate.update()

        self.ui.spin_box_sampling_rate_import_page.setValue(value)

    @QtCore.Slot(str)
    def _on_dialog_signal_column_changed(self, value: str) -> None:
        if value != INDEX_COL:
            self.dialog_meta.combo_box_signal_column.setProperty("requiresInput", False)
        else:
            self.dialog_meta.combo_box_signal_column.setProperty("requiresInput", True)
        self.dialog_meta.combo_box_signal_column.style().unpolish(self.dialog_meta.combo_box_signal_column)
        self.dialog_meta.combo_box_signal_column.style().polish(self.dialog_meta.combo_box_signal_column)
        self.dialog_meta.combo_box_signal_column.update()
        self.ui.combo_box_signal_column_import_page.setCurrentText(value)

    @QtCore.Slot(QtCore.QPoint)
    def show_data_view_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(parent=self.ui.table_view_import_data)
        action = QtGui.QAction(QtGui.QIcon("://icons/ArrowSync"), "Refresh", self.ui.table_view_import_data)
        action.triggered.connect(self.sig_table_refresh_requested.emit)
        menu.addAction(action)
        menu.exec(QtGui.QCursor.pos())

    @QtCore.Slot(QtCore.QPoint)
    def show_result_view_context_menu(self, pos: QtCore.QPoint) -> None:
        current_result_tab = self.ui.tab_widget_result_views.currentIndex()
        if current_result_tab == 0:
            table_view = self.ui.table_view_result_peaks
        elif current_result_tab == 1:
            table_view = self.ui.table_view_result_rate
        else:
            return
        menu = QtWidgets.QMenu(parent=table_view)
        action_copy_table = QtGui.QAction(
            QtGui.QIcon("://icons/Copy"),
            "Copy to Clipboard",
            triggered=lambda: table_view.model().df.write_clipboard(),  # type: ignore
        )
        menu.addAction(action_copy_table)
        menu.addAction(self.action_export_to_csv)
        menu.addAction(self.action_export_to_xlsx)
        menu.exec(QtGui.QCursor.pos())

    def show_section_summary_box(self, summary: _t.SectionSummaryDict) -> None:
        dlg = QtWidgets.QDialog(self)
        dlg.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        dlg.setModal(True)

        summary_tree = SearchableDataTreeWidget(allow_edit=False)
        summary_tree.set_data(dict(summary), hide_root=True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(summary_tree)

        dlg.setLayout(layout)
        dlg.resize(600, 400)
        dlg.open()

    @QtCore.Slot(int)
    def _on_page_changed(self, index: int) -> None:
        self.show_section_confirm_cancel(False)
        if index == 1:
            self.tool_bar_editing.setEnabled(True)
            self.command_bar_section_list.setEnabled(True)
            self.dock_sections.show()
            self.dock_parameters.show()
        else:
            self.tool_bar_editing.setEnabled(False)
            self.command_bar_section_list.setEnabled(False)
            self.dock_parameters.hide()

    def show_section_confirm_cancel(self, show: bool) -> None:
        self.dock_sections.btn_container.setVisible(show)

    def write_settings(self) -> None:
        Config.internal.window_geometry = self.saveGeometry()
        Config.internal.window_state = self.saveState()

        qconfig.save()

    def read_settings(self) -> None:
        self.restoreGeometry(Config.internal.window_geometry)
        self.restoreState(Config.internal.window_state)

    @QtCore.Slot(QtGui.QCloseEvent)
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.write_settings()
        self.dock_status_log.close()
        self.dock_parameters.close()
        self.dock_sections.close()

        self.sv_app.help.close()

        if hasattr(self, "console_window"):
            self.console_window.close()

        return super().closeEvent(event)

    @QtCore.Slot(str, int, str)
    def maybe_show_error_dialog(
        self,
        message: str,
        msg_log_level: LogLevel,
        record_dict: _t.LogRecordDict,
        threshold: LogLevel = LogLevel.WARNING,
    ) -> None:
        if os.environ.get("DEBUG") == "1":
            threshold = LogLevel.DEBUG

        if msg_log_level < threshold:
            return

        parent = self
        if self.dialog_meta.isVisible():
            parent = self.dialog_meta

        msg_box = QtWidgets.QMessageBox(parent)
        msg_box.setText(record_dict["level"].name)
        # msg_box.setIconPixmap(self._msg_box_icons[msg_log_level].pixmap(48, 48))
        msg_box.setInformativeText(message)

        if msg_log_level >= threshold:
            traceback_text = "No details available"
            if record_dict["exception"] is not None:
                traceback_text = str(record_dict["exception"])

            msg_box.setDetailedText(traceback_text)

        msg_box.exec()

    def set_active_section_label(self, label_text: str) -> None:
        self.dock_sections.label_active_section.setText(f"Active Section: {label_text}")
        self.ui.label_showing_section_result.setText(label_text)
        self.ui.label_showing_data_table.setText(f"Showing: {label_text}")
