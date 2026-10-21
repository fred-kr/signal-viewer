import os
import traceback
from typing import TYPE_CHECKING

import pyside_config as qconfig
from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import OverlayWidget, ResizableMessageBox, SearchableDataTreeWidget

from signal_viewer.enum_defs import LogLevel
from signal_viewer.generated.ui_main_window import Ui_MainWindow
from signal_viewer.sv_config import Config
from signal_viewer.sv_plots.result_plot import SPLINE_K_MAX, SPLINE_K_MIN, ResultFitModel, ResultPlotScope
from signal_viewer.sv_widgets.dlg_metadata import MetadataDialog
from signal_viewer.sv_widgets.dock_log_window import StatusMessageDock
from signal_viewer.sv_widgets.dock_param_inputs import InputsDock
from signal_viewer.sv_widgets.dock_sections import SectionsDock
from signal_viewer.type_defs import LogRecordDict, SectionSummaryDict
from signal_viewer.utils import get_app

if TYPE_CHECKING:
    from signal_viewer.sv_app import SVApp


class SVGUI(QtWidgets.QMainWindow):
    sig_export_result = QtCore.Signal(str)

    def __init__(self, sv_app: SVApp, version: str = "0.0.0") -> None:
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
        self.setWindowIcon(QtGui.QIcon("://icons/app_icon.png"))

        desktop = QtWidgets.QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        if w < 1600 or h < 900:
            self.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        else:
            self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def switch_to(self, widget: QtWidgets.QWidget) -> None:
        self.ui.tab_widget_main.setCurrentWidget(widget)

    def _setup_widgets(self) -> None:
        self.dialog_meta = MetadataDialog(self)

        self.ui.table_view_import_data.horizontalHeader().setDefaultAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.ui.table_view_import_data.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

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

        # Names the required metadata that is still missing; `SVApp._bind_metadata` keeps it current.
        self.label_metadata_status = QtWidgets.QLabel()
        self.label_metadata_status.setObjectName("label_metadata_status")
        self.label_metadata_status.setWordWrap(True)
        self.ui.formLayout.addRow(self.label_metadata_status)  # the form of `grp_box_required_info`

        self.combo_box_result_plot_scope = QtWidgets.QComboBox()
        self.combo_box_result_plot_scope.addItem("Active section", ResultPlotScope.ActiveSection)
        self.combo_box_result_plot_scope.addItem("All locked sections", ResultPlotScope.AllLockedSections)
        self.combo_box_result_plot_scope.setToolTip(
            "Show the result of the active section only, or of every locked section on the file's time axis."
        )
        scope_row = QtWidgets.QHBoxLayout()
        scope_row.addWidget(QtWidgets.QLabel("Show:"))
        scope_row.addWidget(self.combo_box_result_plot_scope)

        self.combo_box_result_plot_fit = QtWidgets.QComboBox()
        self.combo_box_result_plot_fit.addItem("Exponential (Gamma GLM, log link)", ResultFitModel.LogLinear)
        self.combo_box_result_plot_fit.addItem("Linear (Gaussian GLM)", ResultFitModel.Linear)
        self.combo_box_result_plot_fit.addItem("Smooth (spline GAM, Gamma log link)", ResultFitModel.Spline)
        self.combo_box_result_plot_fit.addItem("None", ResultFitModel.NoFit)
        self.combo_box_result_plot_fit.setToolTip(
            "Model fitted to the rate against the info column (window means) in the 'Rate vs. ...' panel."
        )
        scope_row.addSpacing(12)
        scope_row.addWidget(QtWidgets.QLabel("Fit:"))
        scope_row.addWidget(self.combo_box_result_plot_fit)

        # Basis dimension of the spline GAM. The minimum shows as "Auto" and stands for "derive from the data";
        # `SVApp` maps it to None. Only meaningful while the spline model is selected.
        self.spin_box_result_plot_spline_k = QtWidgets.QSpinBox()
        self.spin_box_result_plot_spline_k.setRange(SPLINE_K_MIN - 1, SPLINE_K_MAX)
        self.spin_box_result_plot_spline_k.setSpecialValueText("Auto")
        self.spin_box_result_plot_spline_k.setValue(self.spin_box_result_plot_spline_k.minimum())
        self.spin_box_result_plot_spline_k.setToolTip(
            "Basis dimension k of the spline GAM: the number of knots of the B-spline basis. "
            "'Auto' uses one knot per ten points (6 to 20). The cross-validated penalty still controls the "
            "smoothness, so k mainly caps how wiggly the fit can get."
        )
        label_spline_k = QtWidgets.QLabel("k:")
        label_spline_k.setToolTip(self.spin_box_result_plot_spline_k.toolTip())
        scope_row.addSpacing(12)
        scope_row.addWidget(label_spline_k)
        scope_row.addWidget(self.spin_box_result_plot_spline_k)
        self._sync_spline_k_enabled()
        self.combo_box_result_plot_fit.currentIndexChanged.connect(self._sync_spline_k_enabled)
        scope_row.addStretch()
        self.ui.verticalLayout.insertLayout(0, scope_row)  # the layout of `tab_result_mpl_widget`

        self.ui.tab_widget_main.setCurrentIndex(0)

    @QtCore.Slot()
    def _sync_spline_k_enabled(self) -> None:
        is_spline = self.combo_box_result_plot_fit.currentData() == ResultFitModel.Spline
        self.spin_box_result_plot_spline_k.setEnabled(is_spline)

    def _setup_docks(self) -> None:
        dwa = QtCore.Qt.DockWidgetArea

        dock_status = StatusMessageDock()
        self.addDockWidget(dwa.BottomDockWidgetArea, dock_status)
        self.dock_status_log = dock_status

        dock_sections = SectionsDock()
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
            namespace={
                "sv": sv,
                "sv_app": get_app(),
                "sv_gui": self,
            }
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

        # self.ui.action_toggle_auto_scaling.setChecked(False)

    def _setup_toolbars(self) -> None:
        # Channel switcher. Filled by `SVApp` once a file is loaded; the toolbar itself is only enabled on the edit page.
        self.combo_box_channel = QtWidgets.QComboBox()
        self.combo_box_channel.setObjectName("combo_box_channel")
        self.combo_box_channel.setMinimumWidth(160)
        self.combo_box_channel.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.combo_box_channel.setToolTip(
            "Switch the channel (signal column) being edited. Sections and results of the other channels are kept."
        )
        self.combo_box_channel.setEnabled(True)
        self.tb_main = self._setup_toolbar("tb_main", actions=[self.ui.action_open_file, self.ui.action_show_settings])
        self.tb_main.addSeparator()
        self.tb_main.addWidget(QtWidgets.QLabel("Channel: "))
        self.tb_main.addWidget(self.combo_box_channel)

        self.tool_bar_help = self._setup_toolbar(
            "tool_bar_help", [self.action_toggle_whats_this_mode, self.ui.action_show_user_guide]
        )

        self.dock_sections.command_bar.addActions(
            [
                self.ui.action_create_new_section,
                self.ui.action_mark_section_done,
                self.ui.action_unlock_section,
                self.ui.action_remove_section,
                self.action_show_section_summary,
                self.ui.action_show_section_overview,
            ]
        )

        self.command_bar_section_list = self.dock_sections.command_bar

        self.ui.action_remove_section.triggered.connect(self.dock_sections.list_view.emit_sig_delete_item)
        self.action_show_section_summary.triggered.connect(self.dock_sections.list_view.emit_sig_show_summary)
        self.dock_sections.list_view.customContextMenuRequested.connect(self.show_section_list_context_menu)

    def _setup_toolbar(
        self,
        name: str,
        actions: list[QtGui.QAction] | None = None,
        widgets: list[QtWidgets.QWidget] | None = None,
        movable: bool = False,
    ) -> QtWidgets.QToolBar:
        tb = QtWidgets.QToolBar(name)
        tb.setIconSize(QtCore.QSize(24, 24))
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setObjectName(name)
        tb.setMovable(movable)
        if actions is not None:
            tb.addActions(actions)
        if widgets is not None:
            for w in widgets:
                tb.addWidget(w)
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
        self.ui.menu_help.addActions([self.action_toggle_whats_this_mode, self.ui.action_show_user_guide])

        self.menu_export = QtWidgets.QMenu()
        self.menu_export.addActions([self.action_export_to_csv, self.action_export_to_xlsx])

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

        self.dock_status_log.log_text_box.sig_log_message.connect(self.maybe_show_error_dialog)

        self.action_export_to_csv.triggered.connect(lambda: self.sig_export_result.emit("csv"))
        self.action_export_to_xlsx.triggered.connect(lambda: self.sig_export_result.emit("xlsx"))
        self.ui.btn_export_to_excel.clicked.connect(lambda: self.sig_export_result.emit("xlsx"))

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
            triggered=lambda: table_view.model().df.write_clipboard(),
        )
        menu.addAction(action_copy_table)
        menu.addAction(self.action_export_to_csv)
        menu.addAction(self.action_export_to_xlsx)
        menu.exec(QtGui.QCursor.pos())

    def show_section_summary_box(self, summary: SectionSummaryDict) -> None:
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
            # self.tb_main.setEnabled(True)
            self.command_bar_section_list.setEnabled(True)
            self.dock_sections.show()
            self.dock_parameters.show()
        else:
            # self.tb_main.setEnabled(False)
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
        record_dict: LogRecordDict,
        threshold: LogLevel = LogLevel.WARNING,
    ) -> None:
        if os.environ.get("DEBUG") == "1":
            threshold = LogLevel.DEBUG

        if msg_log_level < threshold:
            return

        parent = self
        if self.dialog_meta.isVisible():
            parent = self.dialog_meta

        # Map log level to dialog icon
        if msg_log_level >= LogLevel.ERROR:
            icon = ResizableMessageBox.Icon.Critical
        elif msg_log_level >= LogLevel.WARNING:
            icon = ResizableMessageBox.Icon.Warning
        else:
            icon = ResizableMessageBox.Icon.Information

        detail_parts = [message]
        if record_dict["exception"] is not None:
            tb = "".join(traceback.format_exception(*record_dict["exception"]))
            detail_parts.append(tb)
        detail_text = "\n\n".join(detail_parts)

        dlg = ResizableMessageBox(
            icon=icon,
            title="Error",
            text=f"{record_dict['level'].name}: {record_dict['message']}",
            buttons=QtWidgets.QDialogButtonBox.StandardButton.Ok,
            default_button=QtWidgets.QDialogButtonBox.StandardButton.Ok,
            parent=parent,
            detail_text=detail_text,
        )
        dlg.exec()

    def set_active_section_label(self, label_text: str) -> None:
        self.dock_sections.label_active_section.setText(f"Active Section: {label_text}")
        self.ui.label_showing_section_result.setText(label_text)
        self.ui.label_showing_data_table.setText(f"Showing: {label_text}")
