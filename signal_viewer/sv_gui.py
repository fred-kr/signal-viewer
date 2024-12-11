# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
import os

import pyside_config as qconfig
import qfluentwidgets as qfw
from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import OverlayWidget, SearchableDataTreeWidget
from qfluentwidgets import NavigationInterface, NavigationItemPosition, qrouter

import signal_viewer.type_defs as _t
from signal_viewer.constants import INDEX_COL
from signal_viewer.enum_defs import LogLevel
from signal_viewer.generated.ui_main_window import Ui_MainWindow
from signal_viewer.sv_config import Config
from signal_viewer.sv_widgets.dlg_metadata import MetadataDialog
from signal_viewer.sv_widgets.dock_log_window import StatusMessageDock
from signal_viewer.sv_widgets.dock_parameter_inputs import ParameterInputsDock
from signal_viewer.sv_widgets.dock_sections import SectionListDock

# class SVGui(QtWidgets.QMainWindow):
#     def __init__(self, sv_app: QtCore.QObject, version: str) -> None:
#         super().__init__()
#         self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
#         self._version = version

#         self.sv_app = sv_app

#         self.central_widget = QtWidgets.QWidget()
#         self.setCentralWidget(self.central_widget)


class SVGui(QtWidgets.QMainWindow, Ui_MainWindow):
    sig_metadata_changed = QtCore.Signal(dict)
    sig_table_refresh_requested = QtCore.Signal()
    sig_export_requested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        # self._msg_box_icons = {
        #     LogLevel.DEBUG: QtGui.QIcon("://icons/Wrench"),
        #     LogLevel.INFO: QtGui.QIcon("://icons/Info"),
        #     LogLevel.WARNING: QtGui.QIcon("://icons/Warning"),
        #     LogLevel.ERROR: QtGui.QIcon("://icons/ErrorCircle"),
        #     LogLevel.CRITICAL: QtGui.QIcon("://icons/Important"),
        #     LogLevel.SUCCESS: QtGui.QIcon("://icons/CheckmarkCircle"),
        # }
        # self.setWindowIcon(QtGui.QIcon("://icons/SignalEditor"))

        self.new_central_widget = QtWidgets.QWidget()
        self._h_layout = QtWidgets.QHBoxLayout(self.new_central_widget)
        self.navigation_interface = NavigationInterface(self, showMenuButton=True)
        self.navigation_interface.panel.expandAni.setDuration(0)

        self._setup_layout()
        self.setCentralWidget(self.new_central_widget)
        self._setup_navigation()
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
        self.setWindowTitle("Signal Editor")

        desktop = QtWidgets.QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def _setup_layout(self) -> None:
        self._h_layout.setSpacing(0)
        self._h_layout.setContentsMargins(0, 0, 0, 0)
        self._h_layout.addWidget(self.navigation_interface)
        self._h_layout.addWidget(self.stackedWidget)
        self._h_layout.setStretchFactor(self.stackedWidget, 1)

    def _setup_navigation(self) -> None:
        self.add_sub_interface(self.stacked_page_import, QtGui.QIcon("://icons/DocumentArrowLeft.svg"), "Input Data")
        self.add_sub_interface(self.stacked_page_edit, QtGui.QIcon("://icons/Edit.svg"), "View & Edit")
        self.add_sub_interface(self.stacked_page_export, QtGui.QIcon("://icons/DocumentArrowRight.svg"), "Results")

        qrouter.setDefaultRouteKey(self.stackedWidget, self.stacked_page_import.objectName())
        self.navigation_interface.setExpandWidth(250)

        self.stackedWidget.currentChanged.connect(self._on_current_interface_changed)
        self.stackedWidget.setCurrentIndex(0)
        self.navigation_interface.setCurrentItem(self.stackedWidget.currentWidget().objectName())

    def add_sub_interface(
        self,
        widget: QtWidgets.QWidget,
        icon: QtGui.QIcon,
        text: str,
        position: NavigationItemPosition = NavigationItemPosition.TOP,
    ) -> None:
        if self.stackedWidget.indexOf(widget) == -1:
            self.stackedWidget.addWidget(widget)
        self.navigation_interface.addItem(
            routeKey=widget.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switch_to(widget),
            position=position,
            tooltip=text,
        )

    def switch_to(self, widget: QtWidgets.QWidget) -> None:
        self.stackedWidget.setCurrentWidget(widget)

    @QtCore.Slot(int)
    def _on_current_interface_changed(self, index: int) -> None:
        widget = self.stackedWidget.widget(index)
        self.navigation_interface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

    def _setup_widgets(self) -> None:
        self.dialog_meta = MetadataDialog(self)

        self.table_view_import_data.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.table_view_import_data.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_view_import_data.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view_import_data.customContextMenuRequested.connect(self.show_data_view_context_menu)

        self.table_view_result_peaks.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.table_view_result_peaks.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_view_result_peaks.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view_result_peaks.customContextMenuRequested.connect(self.show_result_view_context_menu)

        self.table_view_result_rate.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.table_view_result_rate.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_view_result_rate.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view_result_rate.customContextMenuRequested.connect(self.show_result_view_context_menu)

        layout = QtWidgets.QVBoxLayout()
        data_tree_widget = SearchableDataTreeWidget()
        data_tree_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addWidget(data_tree_widget)
        self.dialog_meta.container_additional_metadata.setLayout(layout)
        self.data_tree_widget_additional_metadata = data_tree_widget

        # self.btn_export_all_results.setIcon(QtGui.QIcon("://icons/ArrowExportLtr"))
        self.btn_export_all_results.clicked.connect(lambda: self.sig_export_requested.emit("hdf5"))

        self.stackedWidget.setCurrentIndex(0)

    def _setup_docks(self) -> None:  # sourcery skip: extract-duplicate-method
        dwa = QtCore.Qt.DockWidgetArea

        dock_status = StatusMessageDock()
        self.addDockWidget(dwa.BottomDockWidgetArea, dock_status)
        self.dock_status_log = dock_status

        dock_sections = SectionListDock()
        self.addDockWidget(dwa.RightDockWidgetArea, dock_sections)
        self.dock_sections = dock_sections
        self.dock_sections.setEnabled(False)

        dock_parameters = ParameterInputsDock()
        self.addDockWidget(dwa.RightDockWidgetArea, dock_parameters)
        self.dock_parameters = dock_parameters
        self.dock_parameters.setEnabled(False)

    def _add_console_dock(self) -> None:
        try:
            from pyside_widgets import JupyterConsoleWindow
        except ImportError:
            logger.warning("Unable to import the console widget. Console is unavailable.")
            return

        console_window = JupyterConsoleWindow()
        console_window.setVisible(False)

        self.menu_view.addSeparator()
        self.menu_view.addAction(console_window.toggle_view_action)
        self.console_window = console_window

    def _setup_actions(self) -> None:
        self.action_show_section_summary = QtGui.QAction(QtGui.QIcon("://icons/Info"), "Show Section Summary", self)

        self.action_toggle_whats_this_mode = QtWidgets.QWhatsThis().createAction(self)
        self.action_toggle_whats_this_mode.setIcon(QtGui.QIcon("://icons/Question"))

        self.action_export_to_csv = qfw.Action(QtGui.QIcon("://icons/ArrowExportLtr"), "Export to CSV")
        self.action_export_to_xlsx = qfw.Action(QtGui.QIcon("://icons/ArrowExportLtr"), "Export to XLSX")
        self.action_export_to_hdf5 = qfw.Action(QtGui.QIcon("://icons/ArrowExportLtr"), "Export to HDF5")

        self.action_toggle_auto_scaling.setChecked(True)

    def _setup_toolbars(self) -> None:
        self.tool_bar_editing = self._setup_toolbar(
            "tool_bar_editing", [self.action_toggle_auto_scaling, self.action_show_section_overview]
        )

        self.tool_bar_help = self._setup_toolbar(
            "tool_bar_help", [self.action_show_user_guide, self.action_toggle_whats_this_mode]
        )

        self.dock_sections.command_bar.addActions(
            [self.action_create_new_section, self.action_remove_section, self.action_mark_section_done]
        )
        self.dock_sections.command_bar.addHiddenActions(
            [self.action_unlock_section, self.action_show_section_summary, self.action_show_section_overview]
        )

        self.command_bar_section_list = self.dock_sections.command_bar

        self.action_remove_section.triggered.connect(self.dock_sections.list_view.emit_delete_current_request)
        self.action_show_section_summary.triggered.connect(self.dock_sections.list_view.emit_show_summary_request)
        self.dock_sections.list_view.customContextMenuRequested.connect(self.show_section_list_context_menu)

    def _setup_toolbar(self, name: str, actions: list[QtGui.QAction], movable: bool = False) -> QtWidgets.QToolBar:
        tb = QtWidgets.QToolBar(name)
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setObjectName(name)
        tb.setMovable(movable)
        tb.addActions(actions)
        self.addToolBar(tb)
        return tb

    @QtCore.Slot(QtCore.QPoint)
    def show_section_list_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = qfw.RoundMenu(parent=self.dock_sections.list_view)
        menu.addAction(self.action_remove_section)
        menu.addAction(self.action_show_section_summary)
        menu.exec(QtGui.QCursor.pos())

    def _setup_menus(self) -> None:
        self.menu_view.addActions(
            [
                self.dock_sections.toggleViewAction(),
                self.dock_status_log.toggleViewAction(),
                self.dock_parameters.toggleViewAction(),
            ]
        )

        self.menu_plot.insertSeparator(self.action_show_section_overview)

        self.menu_help.addSeparator()
        self.menu_help.addAction(self.dock_status_log.toggleViewAction())
        self.menu_help.insertAction(self.action_show_user_guide, self.action_toggle_whats_this_mode)

        self.menu_export = qfw.RoundMenu()
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
        self.stackedWidget.currentChanged.connect(self._on_page_changed)

        self.spin_box_sampling_rate_import_page.valueChanged.connect(self.dialog_meta.spin_box_sampling_rate.setValue)
        self.combo_box_info_column_import_page.currentTextChanged.connect(
            self.dialog_meta.combo_box_info_column.setCurrentText
        )
        self.combo_box_signal_column_import_page.currentTextChanged.connect(
            self.dialog_meta.combo_box_signal_column.setCurrentText
        )
        self.dialog_meta.spin_box_sampling_rate.valueChanged.connect(self._on_dialog_sampling_rate_changed)
        self.dialog_meta.combo_box_info_column.currentTextChanged.connect(
            self.combo_box_info_column_import_page.setCurrentText
        )
        self.dialog_meta.combo_box_signal_column.currentTextChanged.connect(self._on_dialog_signal_column_changed)

        self.dock_status_log.log_text_box.sig_log_message.connect(self.maybe_show_error_dialog)
        self.dock_sections.btn_confirm.clicked.connect(self.action_confirm_section.trigger)
        self.dock_sections.btn_cancel.clicked.connect(self.action_cancel_section.trigger)

        self.action_export_to_csv.triggered.connect(lambda: self.sig_export_requested.emit("csv"))
        self.action_export_to_xlsx.triggered.connect(lambda: self.sig_export_requested.emit("xlsx"))
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

        self.spin_box_sampling_rate_import_page.setValue(value)

    @QtCore.Slot(str)
    def _on_dialog_signal_column_changed(self, value: str) -> None:
        if value != INDEX_COL:
            self.dialog_meta.combo_box_signal_column.setProperty("requiresInput", False)
        else:
            self.dialog_meta.combo_box_signal_column.setProperty("requiresInput", True)
        self.dialog_meta.combo_box_signal_column.style().unpolish(self.dialog_meta.combo_box_signal_column)
        self.dialog_meta.combo_box_signal_column.style().polish(self.dialog_meta.combo_box_signal_column)
        self.dialog_meta.combo_box_signal_column.update()
        self.combo_box_signal_column_import_page.setCurrentText(value)

    @QtCore.Slot(QtCore.QPoint)
    def show_data_view_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = qfw.RoundMenu(parent=self.table_view_import_data)
        action = QtGui.QAction(QtGui.QIcon("://icons/ArrowSync"), "Refresh", self.table_view_import_data)
        action.triggered.connect(self.sig_table_refresh_requested.emit)
        menu.addAction(action)
        menu.exec(QtGui.QCursor.pos())

    @QtCore.Slot(QtCore.QPoint)
    def show_result_view_context_menu(self, pos: QtCore.QPoint) -> None:
        current_result_tab = self.tab_widget_result_views.currentIndex()
        if current_result_tab == 0:
            table_view = self.table_view_result_peaks
        elif current_result_tab == 1:
            table_view = self.table_view_result_rate
        else:
            return
        menu = qfw.RoundMenu(parent=table_view)
        action_copy_table = qfw.Action(
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

        if hasattr(self, "console_window"):
            self.console_window.close()
        return super().closeEvent(event)

    def show_success(self, title: str, text: str) -> None:
        qfw.InfoBar.success(
            title=title,
            content=text,
            duration=5000,
            position=qfw.InfoBarPosition.TOP,
            parent=self,
        )

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
        self.label_showing_section_result.setText(label_text)
        self.label_showing_data_table.setText(f"Showing: {label_text}")
