import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt
import pyside_config as qconfig
from loguru import logger
from PySide6 import QtCore, QtWidgets

from signal_viewer.enum_defs import SectionChange
from signal_viewer.sv_config import Config
from signal_viewer.sv_data.data_controller import DataController
from signal_viewer.sv_data.data_models import FileListModel
from signal_viewer.sv_data.file_io import read_annotation_file, write_xlsx
from signal_viewer.sv_gui import SVGUI
from signal_viewer.sv_help import HelpController
from signal_viewer.sv_plots.plot_controller import PlotController
from signal_viewer.sv_plots.result_plot import ResultPlotController
from signal_viewer.type_defs import (
    MetadataDict,
    PeakDetectionRequest,
    ProcessingRequest,
    RollingRateKwargs,
    UpdatePeaksAction,
)
from signal_viewer.utils import safe_multi_disconnect

if TYPE_CHECKING:
    from signal_viewer.sv_data.data_models import FileMetadata
    from signal_viewer.sv_data.section import Section


class SVApp(QtCore.QObject):
    """
    Routes GUI intent to `DataController` and refreshes views when the controller reports a change.

    Nothing here mutates a `Section` directly. Every data change goes through a `DataController` method, and every
    refresh comes back through `_on_section_changed`.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("SVApp")

        self.gui = SVGUI(self)
        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self.data: DataController
        self._new_data_controller()
        self.plot = PlotController(self, self.gui)
        self.result_plot = ResultPlotController(
            self.gui.ui.mpl_widget, lambda: self.data.sections.editable_sections, parent=self
        )
        self.help = HelpController(self)

        self.recent_data_files = FileListModel(Config.internal.recent_files, parent=self)
        self.gui.ui.lview_data_files.setModel(self.recent_data_files)

        self.recent_annotations_files = FileListModel(Config.internal.recent_annotation_files, parent=self)
        self.gui.ui.lview_annotation_files.setModel(self.recent_annotations_files)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.gui.ui.action_show_settings.triggered.connect(self._on_show_settings)
        self.gui.ui.action_open_file.triggered.connect(self._on_open_file)
        self.gui.ui.action_open_annotation_file.triggered.connect(self._load_annotations)
        self.gui.ui.action_edit_metadata.triggered.connect(self.show_metadata_dialog)
        self.gui.ui.action_about_qt.triggered.connect(QtWidgets.QApplication.aboutQt)
        self.gui.ui.action_close_file.triggered.connect(self.close_file)
        # self.gui.ui.action_show_user_guide.triggered.connect(self._on_show_user_guide)

        self.gui.dialog_meta.sig_property_has_changed.connect(self.update_metadata)

        self.gui.ui.btn_load_data.clicked.connect(self.read_data)

        self.gui.ui.combo_box_signal_column_import_page.currentTextChanged.connect(self.update_signal_column)
        self.gui.ui.combo_box_info_column_import_page.currentTextChanged.connect(self.update_info_column)
        self.gui.ui.spin_box_sampling_rate_import_page.editingFinished.connect(self.update_sampling_rate)

        self.gui.ui.lview_data_files.doubleClicked.connect(self._open_recent_file)

        self.gui.sig_export_result.connect(self.export_result)

        # Section actions
        self.gui.ui.action_create_new_section.toggled.connect(self._on_create_new_section)
        self.gui.dock_sections.btn_confirm.clicked.connect(self._on_confirm_section)
        self.gui.dock_sections.btn_cancel.clicked.connect(self._on_cancel_section)
        self.gui.ui.action_show_section_overview.toggled.connect(self.plot.set_regions_visible)

        self.gui.ui.action_toggle_auto_scaling.triggered.connect(self.plot.fit_y_axis)

        self.gui.dock_sections.list_view.sig_delete_item.connect(self.delete_section)
        self.gui.dock_sections.list_view.sig_show_summary.connect(self.show_section_summary)
        self.gui.ui.action_mark_section_done.triggered.connect(self._lock_section)
        self.gui.ui.action_unlock_section.triggered.connect(self._unlock_section)

        # GUI -> controller. These go through thin `SVApp` slots rather than straight to `self.data`, because the
        # controller is replaced on `close_file` and the widgets' connections must survive that.
        self.gui.dock_parameters.ui.sig_run_processing.connect(self.run_processing)
        self.gui.dock_parameters.ui.sig_reset_data.connect(self.reset_signal_data)
        self.gui.dock_parameters.ui.sig_run_peak_detection.connect(self.run_peak_detection)
        self.gui.dock_parameters.ui.sig_clear_peaks.connect(self.clear_peaks)
        self.gui.dock_parameters.ui.sig_rate_params_changed.connect(self._on_rate_params_changed)

        self.gui.ui.action_find_peaks_in_selection.triggered.connect(self._on_find_peaks_in_selection)
        self.gui.ui.action_remove_peaks_in_selection.triggered.connect(self.plot.remove_peaks_in_selection)

        self.plot.sig_scatter_data_changed.connect(self._on_sig_scatter_data_changed)
        self.plot.sig_section_clicked.connect(self._on_sig_section_clicked)

        # The result figure is only drawn once its tab is actually shown
        self.gui.ui.tab_widget_main.currentChanged.connect(self.result_plot.refresh)
        self.gui.ui.tab_widget_result_views.currentChanged.connect(self.result_plot.refresh)
        self.gui.combo_box_result_plot_scope.currentIndexChanged.connect(
            lambda: self.result_plot.set_scope(self.gui.combo_box_result_plot_scope.currentData())
        )
        self.gui.combo_box_result_plot_fit.currentIndexChanged.connect(
            lambda: self.result_plot.set_fit_model(self.gui.combo_box_result_plot_fit.currentData())
        )

    #### Event handlers ==========

    @QtCore.Slot()
    def _load_annotations(self) -> None:
        file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.gui, "Open Annotation File", "", filter="Annotation Files (*.csv)"
        )
        if not file:
            return
        self.gui.ui.table_annotations.setData(read_annotation_file(Path(file), self.data.active_section.sampling_rate))
        self.recent_annotations_files.add_file(file)

    # @QtCore.Slot()
    # def _on_show_user_guide(self) -> None:
    #     self.help.show_page("index.html")

    @QtCore.Slot()
    def _on_show_settings(self) -> None:
        snapshot = qconfig.create_snapshot()

        settings_dlg = qconfig.create_editor(self.gui, exclude=["Internal"])
        settings_dlg.accepted.connect(lambda: self.apply_settings(snapshot))
        settings_dlg.rejected.connect(lambda: qconfig.restore_snapshot(snapshot))
        settings_dlg.open()

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        self.data.clear_peaks()

    @QtCore.Slot()
    def _on_find_peaks_in_selection(self) -> None:
        rect = self.plot.get_selection_area()
        if rect is None or self.plot.block_clicks:
            self.plot.remove_selection_rect()
            return

        left, right = int(rect.left()), int(rect.right())
        self.plot.remove_selection_rect()

        request = self.gui.dock_parameters.ui.get_peak_detection_request()
        if request is None:
            logger.warning("Select a peak detection method first.")
            return

        self.data.detect_peaks_in_range(left, right, request)

    @QtCore.Slot(str, object)
    def _on_sig_scatter_data_changed(self, action: UpdatePeaksAction, indices: npt.NDArray[np.intp]) -> None:
        self.data.update_peaks(action, indices)

    @QtCore.Slot(dict)
    def _on_rate_params_changed(self, params: RollingRateKwargs) -> None:
        self.data.set_rate_params(params)

    @QtCore.Slot(object, object)
    def _on_section_changed(self, section: Section, flags: SectionChange) -> None:
        """
        The single refresh point. Redraws only what `flags` names, and only for the active section.

        Every controller method currently reports the active section; the identity check guards against a future
        emitter reporting a background one.
        """
        if section is not self.data.active_section:
            return

        self.plot.refresh_section(section, flags)

        if SectionChange.SIGNAL in flags:
            self.update_status_indicators()
        if flags & (SectionChange.SIGNAL | SectionChange.PEAKS):
            # `Section` reassigns `data` on every change, so the table model has to be handed the new frame.
            self.data.active_section_model.set_df(section.data)
        if SectionChange.LOCK in flags:
            self._update_lock_dependent_states(section)
            self.result_plot.invalidate()
        if SectionChange.RESULT in flags:
            self.update_result_views()

    def _update_lock_dependent_states(self, section: Section) -> None:
        """Enables the editing actions and the parameter dock only for an unlocked, non-base section."""
        is_base = section is self.data.get_base_section()
        editable = not is_base and not section.is_locked

        self.gui.ui.action_remove_section.setEnabled(editable)
        self.gui.ui.action_mark_section_done.setEnabled(editable)
        self.gui.ui.action_unlock_section.setEnabled(not is_base and section.is_locked)
        self.gui.dock_parameters.setEnabled(editable)

    def update_status_indicators(self) -> None:
        self.gui.dock_parameters.ui.ui.status_filter.setChecked(self.data.active_section.is_filtered)
        self.gui.dock_parameters.ui.ui.status_filter.setToolTip(f"Times filtered: {self.data.active_section.n_filters}")

        self.gui.dock_parameters.ui.ui.status_pipeline.setChecked(self.data.active_section.is_processed)
        self.gui.dock_parameters.ui.ui.status_standardization.setChecked(self.data.active_section.is_standardized)

    @QtCore.Slot(object)
    def run_processing(self, request: ProcessingRequest) -> None:
        self.data.apply_processing(request)

    @QtCore.Slot()
    def reset_signal_data(self) -> None:
        self.data.reset_signal()

    @QtCore.Slot(object)
    def run_peak_detection(self, request: PeakDetectionRequest) -> None:
        self.data.detect_peaks(request)

    @QtCore.Slot(object)
    def _on_task_failed(self, exc: Exception) -> None:
        # Routed through loguru so the status dock and the error dialog (`SVGUI.maybe_show_error_dialog`) pick it up.
        logger.opt(exception=exc).error(f"Background task failed: {exc}")

    @QtCore.Slot()
    def _on_sig_new_data(self) -> None:
        self.gui.dock_sections.list_view.setModel(self.data.sections)
        self.gui.dock_sections.list_view.setCurrentIndex(self.data.base_section_index)
        self.plot.bind_section_model(self.data.sections)
        self.plot.update_time_axis_scale(self.data.metadata.sampling_rate)

    def _new_data_controller(self) -> None:
        """
        Replaces `self.data` with a fresh `DataController` and wires its signals.

        This is the only place a controller is constructed, so the wiring cannot be skipped by a new call path.
        """
        self.data = DataController(self, thread_pool=self.thread_pool)
        self._connect_data_controller_signals()
        # Initial sync; later changes arrive through `sig_rate_params_changed`.
        self.data.set_rate_params(self.gui.dock_parameters.ui.get_rate_params())

    def _connect_data_controller_signals(self) -> None:
        self.data.sig_user_input_required.connect(self.show_metadata_dialog)
        self.data.sig_new_metadata.connect(self._bind_metadata)
        self.data.sig_new_data.connect(self._on_sig_new_data)
        self.gui.dock_sections.list_view.pressed.connect(self.data.set_active_section)
        self.data.sig_active_section_changed.connect(self._on_active_section_changed)
        self.data.sig_section_changed.connect(self._on_section_changed)
        self.data.sig_task_started.connect(self.gui.overlay_widget.show_overlay)
        self.data.sig_task_finished.connect(self.gui.overlay_widget.hide_overlay)
        self.data.sig_task_failed.connect(self._on_task_failed)

    def _disconnect_data_controller_signals(self) -> None:
        sender = self.data
        signal_slot_pairs: list[tuple[QtCore.SignalInstance, QtCore.Slot | Callable[..., Any]]] = [
            (sender.sig_user_input_required, self.show_metadata_dialog),
            (sender.sig_new_metadata, self._bind_metadata),
            (sender.sig_new_data, self._on_sig_new_data),
            (sender.sig_active_section_changed, self._on_active_section_changed),
            (sender.sig_section_changed, self._on_section_changed),
            (sender.sig_task_started, self.gui.overlay_widget.show_overlay),
            (sender.sig_task_finished, self.gui.overlay_widget.hide_overlay),
            (sender.sig_task_failed, self._on_task_failed),
            (self.gui.dock_sections.list_view.pressed, sender.set_active_section),
        ]
        safe_multi_disconnect(sender, signal_slot_pairs)

    @QtCore.Slot(bool)
    def _on_create_new_section(self, checked: bool) -> None:
        self.gui.show_section_confirm_cancel(checked)
        if not checked:
            self.plot.hide_region_selector()
            return
        bounds = (0, self.data.base_df.height - 1)
        initial_range = None
        if len(self.data.sections.editable_sections) > 0:
            prev_section = self.data.sections.editable_sections[-1]
            range_start = prev_section.global_bounds[1] + 1
            range_end = min(range_start + prev_section.data.height, bounds[1])
            initial_range = (range_start, range_end)
        self.plot.show_region_selector(bounds, initial_range)

    @QtCore.Slot()
    def _on_confirm_section(self) -> None:
        if self.plot.region_selector is None:
            return
        if not self.plot.region_selector.isVisible():
            return
        start, stop = self.plot.get_region_bounds()
        self.data.create_section(start, stop)  # the plot draws the region from the model's rowsInserted
        self.plot.hide_region_selector()
        self.gui.show_section_confirm_cancel(False)
        self.gui.ui.action_create_new_section.setChecked(False)

    @QtCore.Slot()
    def _on_cancel_section(self) -> None:
        self.plot.hide_region_selector()
        self.gui.show_section_confirm_cancel(False)
        self.gui.ui.action_create_new_section.setChecked(False)

    @QtCore.Slot(QtCore.QModelIndex)
    def delete_section(self, index: QtCore.QModelIndex) -> None:
        section = self.data.sections.get_section(index)
        if section is None or section is self.data.get_base_section():
            return
        name = section.section_id.pretty_name()
        self.data.delete_section(index)  # the plot removes the region from the model's rowsAboutToBeRemoved
        self.result_plot.invalidate()
        self.gui.dock_sections.list_view.setCurrentIndex(self.data.base_section_index)
        logger.info(f"Deleted {name}")

    @QtCore.Slot(QtCore.QModelIndex)
    def show_section_summary(self, index: QtCore.QModelIndex) -> None:
        s = self.data.sections.get_section(index)
        if s is None:
            return
        summary = s.get_summary()
        self.gui.show_section_summary_box(summary)

    @QtCore.Slot(object)
    def _on_active_section_changed(self, section: Section) -> None:
        is_base_section = section is self.data.get_base_section()

        self.gui.ui.action_create_new_section.setEnabled(is_base_section)
        self.gui.ui.action_show_section_overview.setEnabled(is_base_section)
        self.gui.ui.action_show_section_overview.setChecked(is_base_section)
        self.gui.set_active_section_label(section.section_id.pretty_name())
        self.gui.ui.table_view_import_data.setModel(self.data.active_section_model)

        # A newly active section is a complete change from the viewer's point of view.
        self._on_section_changed(section, SectionChange.ALL)
        self.plot.fit_y_axis()

    @QtCore.Slot(object)
    def _on_sig_section_clicked(self, section: Section) -> None:
        index = self.data.sections.index_of(section)
        if not index.isValid():
            return
        self.data.set_active_section(index)
        self.gui.dock_sections.list_view.setCurrentIndex(index)

    @QtCore.Slot(dict)
    def update_metadata(self, metadata_dict: MetadataDict) -> None:
        sampling_rate = metadata_dict.get("sampling_rate", None)
        info_col = metadata_dict.get("info_column", None)
        signal_col = metadata_dict.get("signal_column", None)
        self.data.update_metadata(sampling_rate, signal_col, info_col)

    # --- Metadata widgets -------------------------------------------------------------------------------------------
    # The import page and the metadata dialog show the same three values. `_bind_metadata` is the only code that
    # writes `FileMetadata` into them; user edits in either place flow back through `DataController.update_metadata`,
    # which re-emits `sig_new_metadata`, so both widget sets always agree.

    @property
    def _signal_column_combos(self) -> tuple[QtWidgets.QComboBox, ...]:
        return (self.gui.ui.combo_box_signal_column_import_page, self.gui.dialog_meta.combo_box_signal_column)

    @property
    def _info_column_combos(self) -> tuple[QtWidgets.QComboBox, ...]:
        return (self.gui.ui.combo_box_info_column_import_page, self.gui.dialog_meta.combo_box_info_column)

    @property
    def _sampling_rate_spin_boxes(self) -> tuple[QtWidgets.QSpinBox, ...]:
        return (self.gui.ui.spin_box_sampling_rate_import_page, self.gui.dialog_meta.spin_box_sampling_rate)

    @staticmethod
    def _set_combo_items(combo: QtWidgets.QComboBox, items: list[str], current: str) -> None:
        """Replaces the combo box items only when they differ, then selects `current`, without emitting signals."""
        with QtCore.QSignalBlocker(combo):
            if [combo.itemText(i) for i in range(combo.count())] != items:
                combo.clear()
                combo.addItems(items)
            combo.setCurrentText(current)

    @QtCore.Slot(object)
    def _bind_metadata(self, metadata: FileMetadata) -> None:
        """Pushes `metadata` into every widget that displays it."""
        for combo in self._signal_column_combos:
            self._set_combo_items(combo, metadata.valid_columns, metadata.signal_column)
        for combo in self._info_column_combos:
            self._set_combo_items(combo, metadata.column_names, metadata.info_column)
        for spin_box in self._sampling_rate_spin_boxes:
            with QtCore.QSignalBlocker(spin_box):
                spin_box.setValue(metadata.sampling_rate)

        dialog = self.gui.dialog_meta
        dialog.line_edit_file_name.setText(metadata.file_name)
        dialog.line_edit_file_type.setText(metadata.file_format)
        dialog.set_requires_input(dialog.spin_box_sampling_rate, "sampling_rate" in metadata.required_fields)
        dialog.set_requires_input(dialog.combo_box_signal_column, "signal_column" in metadata.required_fields)

        self.gui.data_tree_widget_additional_metadata.set_data(metadata.other_info, hide_root=True)
        self.gui.data_tree_widget_additional_metadata.collapseAll()

        self.plot.update_time_axis_scale(metadata.sampling_rate)

    def _clear_metadata_widgets(self) -> None:
        for combo in self._signal_column_combos + self._info_column_combos:
            with QtCore.QSignalBlocker(combo):
                combo.clear()
        for spin_box in self._sampling_rate_spin_boxes:
            with QtCore.QSignalBlocker(spin_box):
                spin_box.setValue(0)
        self.gui.dialog_meta.line_edit_file_name.clear()
        self.gui.dialog_meta.line_edit_file_type.clear()
        self.gui.data_tree_widget_additional_metadata.clear()

    def _set_metadata_editable(self, editable: bool) -> None:
        """Metadata can be changed between opening a file and loading its data, not afterwards."""
        for widget in self._signal_column_combos + self._info_column_combos + self._sampling_rate_spin_boxes:
            widget.setEnabled(editable)

    @QtCore.Slot()
    @QtCore.Slot(set)
    def show_metadata_dialog(self, required_fields: set[str] | None = None) -> None:
        # The dialog's widgets are kept current by `_bind_metadata`; nothing to fill here.
        self.gui.dialog_meta.open()

    @QtCore.Slot()
    def update_sampling_rate(self) -> None:
        sampling_rate = self.gui.ui.spin_box_sampling_rate_import_page.value()
        self.data.update_metadata(sampling_rate=sampling_rate)
        logger.info(f"Sampling rate set to {sampling_rate} Hz.")

    @QtCore.Slot(str)
    def update_signal_column(self, signal_column: str) -> None:
        self.data.update_metadata(signal_col=signal_column)
        logger.info(f"Signal column set to '{signal_column}'.")

    @QtCore.Slot(str)
    def update_info_column(self, info_column: str) -> None:
        self.data.update_metadata(info_col=info_column)
        logger.info(f"Info column set to '{info_column}'.")

    @QtCore.Slot()
    def _on_open_file(self) -> None:
        default_data_dir = Config.internal.last_input_dir
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.gui,
            "Open File",
            default_data_dir,
            filter="Supported Files (*.csv *.txt *.tsv *.xls *.xlsx *.feather *.edf)",
        )
        if not file_path:
            logger.info("File selection cancelled by user.")
            return

        self.close_file()

        Config.internal.last_input_dir = Path(file_path).parent.resolve().as_posix()
        self._on_file_opened(file_path)

    def _on_file_opened(self, file_path: str) -> None:
        fname = Path(file_path).name
        self.gui.ui.line_edit_active_file.setText(fname)
        self.gui.setWindowTitle(f"SignalViewer - {fname}")

        self.gui.ui.action_close_file.setEnabled(True)
        self.gui.ui.action_edit_metadata.setEnabled(True)
        self.gui.ui.btn_close_file.setEnabled(True)
        self.gui.ui.btn_load_data.setEnabled(True)

        self.data.open_file(file_path)  # fills the metadata widgets through sig_new_metadata -> _bind_metadata
        self.gui.ui.table_view_import_data.setModel(self.data.active_section_model)  # filled by `load_data`
        self.gui.ui.table_view_result_peaks.setModel(self.data.result_model_peaks)
        self.gui.ui.table_view_result_rate.setModel(self.data.result_model_rate)

        self.recent_data_files.add_file(file_path)
        self.gui.switch_to(self.gui.ui.tab_import)

        logger.info(f"Opened file: {file_path}")

    @QtCore.Slot(QtCore.QModelIndex)
    def _open_recent_file(self, index: QtCore.QModelIndex) -> None:
        file_path = self.recent_data_files.data(index, QtCore.Qt.ItemDataRole.UserRole)
        self.close_file()
        self._on_file_opened(file_path)

    @QtCore.Slot()
    def read_data(self) -> None:
        if self.data.has_data:
            # Reloading the same file: the controller discards its sections itself, the plot has to follow.
            self.plot.reset()
            self.result_plot.clear()

        self.data.load_data()
        self.gui.ui.table_view_import_data.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )

        self.gui.dock_sections.setEnabled(True)
        self._set_metadata_editable(False)

        _val = self.data.metadata.sampling_rate // 2
        self.gui.dock_parameters.ui.ui.peak_localmax_radius.setProperty("defaultValue", _val)
        self.gui.dock_parameters.ui.ui.peak_localmin_radius.setProperty("defaultValue", _val)
        self.gui.dock_parameters.ui.ui.peak_localmax_radius.setValue(_val)
        self.gui.dock_parameters.ui.ui.peak_localmin_radius.setValue(_val)

        logger.info(f"Read data from file: {self.data.metadata.file_name}")

        self.gui.switch_to(self.gui.ui.tab_edit)

    @QtCore.Slot()
    def close_file(self) -> None:
        self.gui.ui.table_view_import_data.setModel(None)
        self.gui.ui.table_view_result_peaks.setModel(None)
        self.gui.ui.table_view_result_rate.setModel(None)
        self._clear_metadata_widgets()
        self.gui.dock_sections.list_view.setModel(None)
        self.gui.dock_parameters.setEnabled(False)
        self.gui.dock_sections.setEnabled(False)

        with contextlib.suppress(Exception):
            self._disconnect_data_controller_signals()
            self.data.setParent(None)

        self._new_data_controller()

        self.plot.reset()
        self.result_plot.clear()

        self.gui.ui.action_close_file.setEnabled(False)
        self.gui.ui.action_edit_metadata.setEnabled(False)
        self.gui.ui.btn_close_file.setEnabled(False)
        self.gui.ui.btn_load_data.setEnabled(False)

        self.gui.set_active_section_label("-")
        self.gui.ui.line_edit_active_file.clear()

        self._set_metadata_editable(True)
        self.gui.setWindowTitle("SignalViewer")

        logger.info("Closed file")

    def apply_settings(self, previous: dict[str, Any]) -> None:
        """
        Applies the settings that changed since `previous` (a `qconfig.create_snapshot()` taken before the dialog).

        Only settings that are read once and cached need handling here; the rest are read from `Config` on use.
        """
        current = qconfig.create_snapshot()
        changed = {
            (group, key)
            for group, values in current.items()
            for key, value in values.items()
            if previous.get(group, {}).get(key) != value
        }
        if not changed:
            return
        logger.info("Settings changed: " + ", ".join(f"{group}.{key}" for group, key in sorted(changed)))

        if ("Processing", "rate_computation_method") in changed:
            self.data.recompute_rate_all()
        if ("Data", "float_precision") in changed:
            self.data.refresh_table_models()

    @QtCore.Slot()
    def update_result_views(self) -> None:
        self.data.result_model_peaks.set_df(self.data.active_section.peak_data)
        self.data.result_model_rate.set_df(self.data.active_section.rate_data)
        self.result_plot.set_section(self.data.active_section)

    @QtCore.Slot()
    def _lock_section(self) -> None:
        self.data.lock_active()

    @QtCore.Slot()
    def _unlock_section(self) -> None:
        self.data.unlock_active()

    def _confirm_xlsx_export(self) -> bool:
        """
        Checks that there is something to export and warns about unlocked sections.

        Returns `False` when the export should be aborted.
        """
        sections = self.data.sections.editable_sections
        if not sections:
            logger.warning("Nothing to export. Create at least one section, detect peaks, and lock it first.")
            return False

        unlocked = [s.section_id.pretty_name() for s in sections if not s.is_locked]
        if not unlocked:
            return True

        answer = QtWidgets.QMessageBox.question(
            self.gui,
            "Unlocked sections",
            "The following sections are not locked. Their peak and rate results are incomplete or missing:\n\n"
            + "\n".join(unlocked)
            + "\n\nExport anyway?",
        )
        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    @logger.catch()
    @QtCore.Slot(str)
    def export_result(self, format: str) -> None:
        if format == "xlsx" and not self._confirm_xlsx_export():
            return

        dir_path = (
            Path(Config.internal.last_output_dir)
            / f"Result_{self.data.active_section.signal_name.title()}_{Path(self.data.metadata.file_path).stem}"
        )
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.gui,
            f"Export {format.upper()}",
            dir_path.as_posix(),
            filter=f"{format.upper()} files (*.{format})",
        )
        if not out_path:
            return
        Config.internal.last_output_dir = Path(out_path).parent.resolve().as_posix()

        if format == "csv":
            if self.gui.ui.tab_widget_result_views.currentIndex() == 0:
                df = self.data.active_section.peak_data
            elif self.gui.ui.tab_widget_result_views.currentIndex() == 1:
                df = self.data.active_section.rate_data
            else:
                raise NotImplementedError

            df.write_csv(out_path)

        elif format == "xlsx":
            text, ok = QtWidgets.QInputDialog.getText(
                self.gui,
                "Add grouping column?",
                "Optional label for a 'group_var' column.<br>Useful when combining results from multiple files,<br>e.g. to perform further analysis in R.",
            )
            group_var = text if ok else None
            write_xlsx(self.data.sections.editable_sections, out_path, group_var)

        else:
            raise NotImplementedError

        QtWidgets.QMessageBox.information(self.gui, "Success!", f"Saved to '{out_path}'")
