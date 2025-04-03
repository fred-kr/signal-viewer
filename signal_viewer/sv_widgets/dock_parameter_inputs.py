import enum
import decimal

import qfluentwidgets as qfw
from PySide6 import QtCore, QtGui, QtWidgets

import signal_viewer.type_defs as _t
from signal_viewer.constants import COMBO_BOX_NO_SELECTION
from signal_viewer.enum_defs import (
    FilterMethod,
    IncompleteWindowMethod,
    NK2ECGPeakDetectionMethod,
    PeakDetectionMethod,
    PreprocessPipeline,
    StandardizationMethod,
    WFDBPeakDirection,
)
from signal_viewer.generated.ui_parameter_inputs import Ui_ParameterInputs

D = decimal.Decimal

"""
Default values for input widgets.
"""

PEAK_DETECTION = {
    "peak_elgendi_ppg": {
        "peakwindow": 0.111,
        "beatwindow": 0.667,
        "beatoffset": 0.02,
        "mindelay": 0.3,
    },
    "peak_neurokit2": {
        "smoothwindow": 0.1,
        "avgwindow": 0.75,
        "gradthreshweight": 1.5,
        "minlenweight": 0.4,
        "mindelay": 0.3,
    },
    "peak_local_max": {
        "radius": 100,
        "min_dist": 15,
    },
    "peak_local_min": {
        "radius": 100,
        "min_dist": 15,
    },
    "peak_xqrs": {
        "search_radius": 50,
        "min_peak_distance": 10,
        # "peak_dir": 0,  # Index
    },
    "peak_promac": {
        "threshold": 0.33,
        "gaussian_sd": 100,
    },
    "peak_gamboa": {
        "tol": 0.002,
    },
    "peak_ssf": {
        "threshold": 20,
        "before": 0.03,
        "after": 0.01,
    },
    "peak_emrich": {
        "window_seconds": 2,
        "window_overlap": 0.5,
        "accelerated": True,
    },
    # "combo_peak_method": 0,  # Index
    # "peak_neurokit2_algorithm_used": 0,  # Index
}


PROCESSING = {
    "dbl_sb_powerline": 50,
    "dbl_sb_lower_cutoff": 0,
    "dbl_sb_upper_cutoff": 0,
    "sb_filter_order": 3,
    "sb_filter_window_size": 5,
    "sb_standardize_window_size": 333,
    # "combo_pipeline": 0,  # Index
    "switch_btn_standardize_rolling_window": False,
    # "combo_filter_method": 0,  # Index
}


def _fill_combo_box_with_enum(combo_box: qfw.ComboBox, enum_class: type[enum.Enum], allow_none: bool = False) -> None:
    combo_box.clear()
    for enum_value in enum_class:
        combo_box.addItem(enum_value.name, userData=enum_value.value)

    if allow_none:
        combo_box.insertItem(0, COMBO_BOX_NO_SELECTION, userData=None)


def _reset_widget(widget: QtWidgets.QWidget | QtCore.QObject) -> None:
    if isinstance(widget, (qfw.ComboBox, QtWidgets.QComboBox)):
        widget.setCurrentIndex(0)
        return
    if not hasattr(widget, "default_value"):
        return
    if isinstance(widget, (qfw.CheckBox, QtWidgets.QCheckBox, qfw.SwitchButton)):
        widget.setChecked(widget.default_value)  # type: ignore
    else:
        widget.setValue(widget.default_value)  # type: ignore


class ParameterInputs(QtWidgets.QWidget, Ui_ParameterInputs):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupUi(self)


class ParameterInputsDock(QtWidgets.QDockWidget):
    sig_pipeline_requested = QtCore.Signal(enum.StrEnum)  # PreprocessPipeline
    sig_filter_requested = QtCore.Signal(dict)  # _t.SignalFilterParameters
    sig_standardization_requested = QtCore.Signal(dict)  # _t.StandardizationParameters
    sig_data_reset_requested = QtCore.Signal()

    sig_peak_detection_requested = QtCore.Signal(enum.StrEnum, dict)
    sig_clear_peaks_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("DockWidgetParameterInputs")
        self.setWindowTitle("Parameter Inputs")
        self.toggleViewAction().setIcon(QtGui.QIcon("://icons/Options.svg"))
        self.setWindowIcon(QtGui.QIcon("://icons/Options.svg"))
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)

        self.ui = ParameterInputs()
        self.setWidget(self.ui)

        self._peak_defaults = PEAK_DETECTION
        self._processing_defaults = PROCESSING
        self._assign_defaults()

        self._setup_enum_combo_boxes()
        self._setup_command_bars()
        self._setup_status_indicators()
        self._setup_actions()

        self._on_filter_method_changed()
        self._on_pipeline_changed()
        self._on_peak_detection_method_changed(self.ui.combo_peak_method.currentData())

    @property
    def filter_inputs(self) -> list[QtWidgets.QWidget]:
        return [
            self.ui.dbl_sb_lower_cutoff,
            self.ui.dbl_sb_upper_cutoff,
            self.ui.sb_filter_order,
            self.ui.sb_filter_window_size,
            self.ui.dbl_sb_powerline,
        ]

    @property
    def standardization_inputs(self) -> list[QtWidgets.QWidget]:
        return [
            self.ui.switch_btn_standardize_rolling_window,
            self.ui.sb_standardize_window_size,
        ]

    def _setup_status_indicators(self) -> None:
        self.ui.icon_pipeline_status.setFixedSize(20, 20)
        self.ui.icon_filter_status.setFixedSize(20, 20)
        self.ui.icon_standardize_status.setFixedSize(20, 20)
        self.reset_status_indicators()

    def set_pipeline_status(self, status: bool) -> None:
        self.ui.icon_pipeline_status.setIcon(
            QtGui.QIcon("://icons/CheckmarkCircle.svg") if status else QtGui.QIcon("://icons/Circle.svg")
        )

    def set_filter_status(self, status: bool, times_filtered: int) -> None:
        self.ui.icon_filter_status.setIcon(
            QtGui.QIcon("://icons/CheckmarkCircle.svg") if status else QtGui.QIcon("://icons/Circle.svg")
        )
        self.ui.icon_filter_status.setToolTip(f"Filtered {times_filtered} times")

    def set_standardization_status(self, status: bool) -> None:
        self.ui.icon_standardize_status.setIcon(
            QtGui.QIcon("://icons/CheckmarkCircle.svg") if status else QtGui.QIcon("://icons/Circle.svg")
        )

    def reset_status_indicators(self, status: bool = False) -> None:
        self.ui.icon_pipeline_status.setIcon(
            QtGui.QIcon("://icons/CheckmarkCircle.svg") if status else QtGui.QIcon("://icons/Circle.svg")
        )
        self.ui.icon_filter_status.setIcon(
            QtGui.QIcon("://icons/CheckmarkCircle.svg") if status else QtGui.QIcon("://icons/Circle.svg")
        )
        self.ui.icon_standardize_status.setIcon(
            QtGui.QIcon("://icons/CheckmarkCircle.svg") if status else QtGui.QIcon("://icons/Circle.svg")
        )

    def _assign_defaults(self) -> None:
        # Peak Detection
        for name_prefix, param_map in self._peak_defaults.items():
            for name_suffix, default_value in param_map.items():
                name = f"{name_prefix}_{name_suffix}"
                widget = getattr(self.ui, name)
                widget.default_value = default_value

        # Processing
        for name, default_value in self._processing_defaults.items():
            widget = getattr(self.ui, name)
            widget.default_value = default_value

    def _setup_enum_combo_boxes(self) -> None:
        _fill_combo_box_with_enum(self.ui.combo_pipeline, PreprocessPipeline, allow_none=True)
        _fill_combo_box_with_enum(self.ui.combo_filter_method, FilterMethod, allow_none=True)
        _fill_combo_box_with_enum(self.ui.combo_peak_method, PeakDetectionMethod)
        _fill_combo_box_with_enum(self.ui.combo_standardize_method, StandardizationMethod, allow_none=True)
        _fill_combo_box_with_enum(self.ui.peak_neurokit2_algorithm_used, NK2ECGPeakDetectionMethod)
        _fill_combo_box_with_enum(self.ui.peak_xqrs_peak_dir, WFDBPeakDirection)
        _fill_combo_box_with_enum(self.ui.combo_incomplete_window_method, IncompleteWindowMethod)

    def _setup_actions(self) -> None:
        # Peak Detection
        # Actions
        self.ui.action_clear_peaks.triggered.connect(self.sig_clear_peaks_requested)
        self.ui.action_run_peak_detection.triggered.connect(self._on_run_peak_detection)
        self.ui.action_restore_defaults_peak_detection.triggered.connect(self._on_restore_defaults_peak_detection)
        # Widgets
        self.ui.combo_peak_method.currentIndexChanged.connect(
            lambda: self._on_peak_detection_method_changed(self.ui.combo_peak_method.currentData())
        )
        self.ui.peak_neurokit2_algorithm_used.currentIndexChanged.connect(
            lambda: self._show_nk_peak_algorithm_inputs(self.ui.peak_neurokit2_algorithm_used.currentData())
        )

        # Processing
        # Actions
        self.ui.action_run_processing.triggered.connect(self._on_run_processing)
        self.ui.action_restore_defaults_processing.triggered.connect(self._on_restore_defaults_processing)
        self.ui.action_restore_original_values.triggered.connect(self.sig_data_reset_requested)
        # Widgets
        self.ui.combo_pipeline.currentIndexChanged.connect(lambda: self._on_pipeline_changed())
        self.ui.combo_filter_method.currentIndexChanged.connect(lambda: self._on_filter_method_changed())
        self.ui.combo_standardize_method.currentIndexChanged.connect(lambda: self._on_standardize_method_changed())
        self.ui.switch_btn_standardize_rolling_window.checkedChanged.connect(self._on_switch_toggled)

    @QtCore.Slot(bool)
    def _on_switch_toggled(self, checked: bool) -> None:
        self.ui.container_standardize_rolling_window.setEnabled(checked)
        self.ui.sb_standardize_window_size.setEnabled(checked)

    def _setup_command_bars(self) -> None:
        # Peak Detection
        self.ui.command_bar_peak_detection.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.ui.command_bar_peak_detection.addActions(
            [
                self.ui.action_run_peak_detection,
                self.ui.action_clear_peaks,
                self.ui.action_restore_defaults_peak_detection,
            ]
        )

        # Processing
        self.ui.command_bar_processing.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.ui.command_bar_processing.addActions(
            [
                self.ui.action_run_processing,
                self.ui.action_restore_original_values,
                self.ui.action_restore_defaults_processing,
            ]
        )

    @QtCore.Slot()
    def _on_pipeline_changed(self) -> None:
        pipeline = self.ui.combo_pipeline.currentData()
        if pipeline is None:
            self.ui.combo_filter_method.setEnabled(True)
            self.ui.combo_standardize_method.setEnabled(True)
        else:
            self.ui.combo_filter_method.setCurrentIndex(0)
            self.ui.combo_standardize_method.setCurrentIndex(0)
            self.ui.combo_filter_method.setEnabled(False)
            self.ui.combo_standardize_method.setEnabled(False)

    @QtCore.Slot()
    def _on_filter_method_changed(self) -> None:
        filter_method = self.ui.combo_filter_method.currentData()
        if filter_method is None:
            for widget in self.filter_inputs:
                widget.setEnabled(False)
                _reset_widget(widget)
        elif filter_method in [FilterMethod.Butterworth, FilterMethod.ButterworthLegacy, FilterMethod.Bessel]:
            self.ui.dbl_sb_lower_cutoff.setEnabled(True)
            self.ui.dbl_sb_upper_cutoff.setEnabled(True)
            self.ui.sb_filter_order.setEnabled(True)
            self.ui.sb_filter_window_size.setEnabled(False)
            self.ui.dbl_sb_powerline.setEnabled(False)
        elif filter_method == FilterMethod.SavGol:
            self.ui.dbl_sb_lower_cutoff.setEnabled(False)
            self.ui.dbl_sb_upper_cutoff.setEnabled(False)
            self.ui.sb_filter_order.setEnabled(True)
            self.ui.sb_filter_window_size.setEnabled(True)
            self.ui.dbl_sb_powerline.setEnabled(False)
        elif filter_method == FilterMethod.FIR:
            self.ui.dbl_sb_lower_cutoff.setEnabled(True)
            self.ui.dbl_sb_upper_cutoff.setEnabled(True)
            self.ui.sb_filter_order.setEnabled(False)
            self.ui.sb_filter_window_size.setEnabled(True)
            self.ui.dbl_sb_powerline.setEnabled(False)
        elif filter_method == FilterMethod.Powerline:
            self.ui.dbl_sb_lower_cutoff.setEnabled(False)
            self.ui.dbl_sb_upper_cutoff.setEnabled(False)
            self.ui.sb_filter_order.setEnabled(False)
            self.ui.sb_filter_window_size.setEnabled(False)
            self.ui.dbl_sb_powerline.setEnabled(True)

    @QtCore.Slot()
    def _on_standardize_method_changed(self) -> None:
        standardize_method = self.ui.combo_standardize_method.currentData()
        if standardize_method is None:
            for widget in self.standardization_inputs:
                widget.setEnabled(False)
                _reset_widget(widget)
        elif standardize_method == StandardizationMethod.ZScore:
            self.ui.switch_btn_standardize_rolling_window.setEnabled(True)
        else:
            self.ui.switch_btn_standardize_rolling_window.setChecked(False)
            self.ui.switch_btn_standardize_rolling_window.setEnabled(False)

    @QtCore.Slot()
    def _on_run_processing(self) -> None:
        pipeline = self.ui.combo_pipeline.currentData()
        # logger.debug(f"Pipeline: {pipeline}")
        if pipeline is not None:
            pipeline = PreprocessPipeline(pipeline)
            self.sig_pipeline_requested.emit(pipeline)
        else:
            filter_method = self.ui.combo_filter_method.currentData()
            if filter_method is not None:
                filter_method = FilterMethod(filter_method)
                filter_params = self._get_filter_params(filter_method)
                self.sig_filter_requested.emit(filter_params)
            standardize_method = self.ui.combo_standardize_method.currentData()
            if standardize_method is not None:
                standardize_method = StandardizationMethod(standardize_method)
                standardize_params = self._get_standardize_params(standardize_method)
                self.sig_standardization_requested.emit(standardize_params)

    def _get_filter_params(self, method: FilterMethod) -> _t.SignalFilterParameters:
        window = self.ui.sb_filter_window_size
        if window.value() == window.minimum():
            window_size = "default"
        else:
            window_size = window.value()
        return {
            "lowcut": self.ui.dbl_sb_lower_cutoff.value(),
            "highcut": self.ui.dbl_sb_upper_cutoff.value(),
            "method": method,
            "order": self.ui.sb_filter_order.value(),
            "window_size": window_size,
            "powerline": self.ui.dbl_sb_powerline.value(),
        }

    def _get_standardize_params(self, method: StandardizationMethod) -> _t.StandardizationParameters:
        return {
            "method": method,
            "window_size": self.ui.sb_standardize_window_size.value()
            if self.ui.switch_btn_standardize_rolling_window.isChecked()
            else None,
        }

    @QtCore.Slot()
    def _on_run_peak_detection(self) -> None:
        peak_method = PeakDetectionMethod(self.ui.combo_peak_method.currentData())
        peak_params = self.get_peak_detection_params(peak_method)
        self.sig_peak_detection_requested.emit(peak_method, peak_params)

    @QtCore.Slot(str)
    def _on_peak_detection_method_changed(self, method: str) -> None:
        peak_method = PeakDetectionMethod(method)
        if peak_method == PeakDetectionMethod.PPGElgendi:
            self.ui.stacked_peak_parameters.setCurrentWidget(self.ui.page_peak_elgendi_ppg)
        elif peak_method == PeakDetectionMethod.ECGNeuroKit2:
            self.ui.stacked_peak_parameters.setCurrentWidget(self.ui.page_peak_neurokit2)
            self._show_nk_peak_algorithm_inputs(self.ui.peak_neurokit2_algorithm_used.currentData())
        elif peak_method == PeakDetectionMethod.LocalMaxima:
            self.ui.stacked_peak_parameters.setCurrentWidget(self.ui.page_peak_local_max)
        elif peak_method == PeakDetectionMethod.LocalMinima:
            self.ui.stacked_peak_parameters.setCurrentWidget(self.ui.page_peak_local_min)
        elif peak_method == PeakDetectionMethod.WFDBXQRS:
            self.ui.stacked_peak_parameters.setCurrentWidget(self.ui.page_peak_xqrs)

    @QtCore.Slot(str)
    def _show_nk_peak_algorithm_inputs(self, method: str) -> None:
        method = NK2ECGPeakDetectionMethod(method)
        if method == NK2ECGPeakDetectionMethod.Default:
            self.ui.stacked_nk2_method_parameters.setCurrentWidget(self.ui.nk2_page_neurokit)
        elif method == NK2ECGPeakDetectionMethod.Promac:
            self.ui.stacked_nk2_method_parameters.setCurrentWidget(self.ui.nk2_page_promac)
        elif method == NK2ECGPeakDetectionMethod.Gamboa2008:
            self.ui.stacked_nk2_method_parameters.setCurrentWidget(self.ui.nk2_page_gamboa)
        elif method == NK2ECGPeakDetectionMethod.Emrich2023:
            self.ui.stacked_nk2_method_parameters.setCurrentWidget(self.ui.nk2_page_emrich)
        else:
            self.ui.stacked_nk2_method_parameters.setCurrentWidget(self.ui.nk2_page_no_params)

    def get_peak_detection_params(self, method: PeakDetectionMethod) -> _t.PeakDetectionMethodParameters:
        if method == PeakDetectionMethod.PPGElgendi:
            peak_params = _t.PeaksPPGElgendi(
                peakwindow=self.ui.peak_elgendi_ppg_peakwindow.value(),
                beatwindow=self.ui.peak_elgendi_ppg_beatwindow.value(),
                beatoffset=self.ui.peak_elgendi_ppg_beatoffset.value(),
                mindelay=self.ui.peak_elgendi_ppg_mindelay.value(),
            )
        elif method == PeakDetectionMethod.ECGNeuroKit2:
            nk_algorithm = NK2ECGPeakDetectionMethod(self.ui.peak_neurokit2_algorithm_used.currentData())
            if nk_algorithm == NK2ECGPeakDetectionMethod.Default:
                nk_params = _t.NK2PeaksNeuroKit(
                    smoothwindow=self.ui.peak_neurokit2_smoothwindow.value(),
                    avgwindow=self.ui.peak_neurokit2_avgwindow.value(),
                    gradthreshweight=self.ui.peak_neurokit2_gradthreshweight.value(),
                    minlenweight=self.ui.peak_neurokit2_minlenweight.value(),
                    mindelay=self.ui.peak_neurokit2_mindelay.value(),
                )
            elif nk_algorithm == NK2ECGPeakDetectionMethod.Promac:
                nk_params = _t.NK2PeaksPromac(
                    threshold=self.ui.peak_promac_threshold.value(),
                    gaussian_sd=self.ui.peak_promac_gaussian_sd.value(),
                )
            elif nk_algorithm == NK2ECGPeakDetectionMethod.Gamboa2008:
                nk_params = _t.NK2PeaksGamboa(tol=self.ui.peak_gamboa_tol.value())
            elif nk_algorithm == NK2ECGPeakDetectionMethod.Emrich2023:
                nk_params = _t.NK2PeaksEmrich(
                    window_seconds=self.ui.peak_emrich_window_seconds.value(),
                    window_overlap=self.ui.peak_emrich_window_overlap.value(),
                    accelerated=self.ui.peak_emrich_accelerated.isChecked(),
                )
            else:
                nk_params = None

            peak_params = _t.PeaksECGNeuroKit2(method=nk_algorithm, params=nk_params)

        elif method == PeakDetectionMethod.LocalMaxima:
            peak_params = _t.PeaksLocalMaxima(
                search_radius=self.ui.peak_local_max_radius.value(),
                min_distance=self.ui.peak_local_max_min_dist.value(),
            )

        elif method == PeakDetectionMethod.LocalMinima:
            peak_params = _t.PeaksLocalMinima(
                search_radius=self.ui.peak_local_min_radius.value(),
                min_distance=self.ui.peak_local_min_min_dist.value(),
            )

        elif method == PeakDetectionMethod.WFDBXQRS:
            peak_params = _t.PeaksWFDBXQRS(
                search_radius=self.ui.peak_xqrs_search_radius.value(),
                peak_dir=WFDBPeakDirection(self.ui.peak_xqrs_peak_dir.currentData()),
                min_peak_distance=self.ui.peak_xqrs_min_peak_distance.value(),
            )

        return peak_params

    def get_rate_calculation_params(self) -> _t.RollingRateKwargsDict:
        new_window_every = self.ui.sb_every_seconds.value()
        window_length = self.ui.sb_period_seconds.value()
        incomplete_window_method = IncompleteWindowMethod(self.ui.combo_incomplete_window_method.currentData())

        return {
            "sec_new_window_every": new_window_every,
            "sec_window_length": window_length,
            "incomplete_window_method": incomplete_window_method,
        }

    @QtCore.Slot()
    def _on_restore_defaults_peak_detection(self) -> None:
        current_input_page = self.ui.stacked_peak_parameters.currentWidget()
        for child in current_input_page.children():
            _reset_widget(child)

        if current_input_page == self.ui.page_peak_neurokit2:
            for child in self.ui.stacked_nk2_method_parameters.currentWidget().children():
                _reset_widget(child)

    @QtCore.Slot()
    def _on_restore_defaults_processing(self) -> None:
        for cb in [self.ui.combo_pipeline, self.ui.combo_filter_method, self.ui.combo_standardize_method]:
            cb.setCurrentIndex(0)

        for widget_name, default_value in self._processing_defaults.items():
            widget = getattr(self.ui, widget_name)
            if isinstance(default_value, bool):
                widget.setChecked(default_value)
            else:
                widget.setValue(default_value)


# type SupportsDecimal = decimal.Decimal | int | float

# def make_spinbox(minimum: SupportsDecimal, maximum: SupportsDecimal, step: SupportsDecimal, default: SupportsDecimal, decimals: int = 0) -> pw.DecimalSpinBox:
#     spinbox = pw.DecimalSpinBox()
#     spinbox.setDecimals(decimals)
#     spinbox.setMinimum(minimum)
#     spinbox.setMaximum(maximum)
#     spinbox.setSingleStep(step)
#     spinbox.setValue(default)
#     spinbox.setProperty("defaultValue", default)
#     return spinbox


# def restore_default(widget: QtWidgets.QWidget) -> None:
#     if default_value := widget.property("defaultValue"):
#         if isinstance(widget, pw.DecimalSpinBox):
#             widget.setValue(default_value)
#         elif isinstance(widget, pw.AnimatedToggle):
#             widget.setChecked(default_value)

#     if isinstance(widget, QtWidgets.QComboBox):
#         widget.setCurrentIndex(0)

# class ParamInputsWidget(QtWidgets.QWidget):
#     sig_run_pipeline = QtCore.Signal(PreprocessPipeline)
#     sig_run_filter = QtCore.Signal(dict)
#     sig_run_standardization = QtCore.Signal(dict)
#     sig_reset_data = QtCore.Signal()
    
#     sig_run_peak_detection = QtCore.Signal(enum.StrEnum, dict)
#     sig_clear_peaks = QtCore.Signal()
    
#     def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
#         super().__init__(parent)

#         self.create_actions()
#         self.create_widgets()

#     @property
#     def sf_widgets(self) -> list[QtWidgets.QWidget]:
#         return [
#             self.sf_lower_cutoff,
#             self.sf_upper_cutoff,
#             self.sf_order,
#             self.sf_window_size,
#             self.sf_powerline,
#         ]

#     @property
#     def std_widgets(self) -> list[QtWidgets.QWidget]:
#         return [
#             self.std_rolling_window,
#             self.std_window_size,
#         ]

#     def create_actions(self) -> None:
#         # Signal Filter
#         self.action_sf_run = QtGui.QAction(QtGui.QIcon("://icons/Play.svg"), "Run", self)
#         self.action_sf_run.triggered.connect(self.run_processing)
        
#         self.action_sf_reset_inputs = QtGui.QAction(QtGui.QIcon("://icons/ArrowReset.svg"), "Reset Inputs", self)
#         self.action_sf_reset_inputs.triggered.connect(self.reset_inputs)
#         self.action_sf_reset_data = QtGui.QAction(QtGui.QIcon("://icons/Broom.svg"), "Reset Data", self)
#         self.action_sf_reset_data.triggered.connect(self.reset_data)

#         # Peak Detection
#         self.action_peak_run = QtGui.QAction(QtGui.QIcon("://icons/Play.svg"), "Run", self)
#         self.action_peak_run.triggered.connect(self.run_peak_detection)
#         self.action_peak_reset_inputs = QtGui.QAction(QtGui.QIcon("://icons/ArrowReset.svg"), "Reset Inputs", self)
#         self.action_peak_reset_inputs.triggered.connect(self.reset_inputs)
#         self.action_peak_reset_data = QtGui.QAction(QtGui.QIcon("://icons/Broom.svg"), "Clear Peaks", self)
#         self.action_peak_reset_data.triggered.connect(self.reset_data)
        
#     def create_widgets(self) -> None:
#         # Signal Filter
#         self.sf_pipeline = pw.EnumComboBox(PreprocessPipeline, allow_none=True)
#         self.sf_pipeline.sig_current_enum_changed.connect(self._on_pipeline_changed)

#         self.sf_method = pw.EnumComboBox(FilterMethod, allow_none=True)
#         self.sf_method.sig_current_enum_changed.connect(self._on_filter_method_changed)
        
#         self.sf_lower_cutoff = make_spinbox(0, 100_000, 0.1, 0.5, 1)
#         self.sf_upper_cutoff = make_spinbox(0, 100_000, 0.1, 8.0, 1)
#         self.sf_order = make_spinbox(1, 10, 1, 3, 0)
#         self.sf_window_size = make_spinbox(5, 1_000_000, 10, 100, 0)
#         self.sf_powerline = make_spinbox(0, 100_000, 0.1, 50.0, 1)
#         self.sf_commands = pw.CommandBar()
#         self.sf_commands.addActions([self.action_sf_run, self.action_sf_reset_inputs, self.action_sf_reset_data])

#         # Standardization
#         self.std_method = pw.EnumComboBox(StandardizationMethod, allow_none=True)
#         self.std_method.sig_current_enum_changed.connect(self._on_std_method_changed)
        
#         self.std_rolling_window = pw.AnimatedToggle()
#         self.std_rolling_window.setChecked(False)
#         self.std_rolling_window.setProperty("defaultValue", False)
#         self.std_rolling_window.toggled.connect(self._on_rolling_window_toggled)
#         self.std_window_size = make_spinbox(5, 999_999, 2, 100, 0)

#         # Peak Detection
#         self.peak_method = pw.EnumComboBox(PeakDetectionMethod)
#         self.peak_method.sig_current_enum_changed.connect(self._on_peak_method_changed)
#         self.peak_nk_method = pw.EnumComboBox(NK2ECGPeakDetectionMethod)
#         self.peak_nk_method.sig_current_enum_changed.connect(self._on_nk_peak_method_changed)
        
#         self.peak_xqrs_direction = pw.EnumComboBox(WFDBPeakDirection)
#         self.peak_xqrs_radius = make_spinbox(5, 99_999, 1, 90, 0)
#         self.peak_xqrs_min_dist = make_spinbox(0, 100_000, 1, 10, 0)

#         self.peak_elgendi_ppg_peakwindow = make_spinbox(0.05, 5.0, 0.001, 0.111, 3)
#         self.peak_elgendi_ppg_beatwindow = make_spinbox(0.1, 5.0, 0.001, 0.667, 3)
#         self.peak_elgendi_ppg_beatoffset = make_spinbox(0.0, 1.0, 0.01, 0.02, 2)
#         self.peak_elgendi_ppg_mindelay = make_spinbox(0.0, 10.0, 0.01, 0.3, 2)

#         self.peak_localmax_radius = make_spinbox(5, 9_999, 1, 111, 0)
#         self.peak_localmax_min_dist = make_spinbox(0, 1_000_000, 1, 15, 0)

#         self.peak_localmin_radius = make_spinbox(5, 9_999, 1, 111, 0)
#         self.peak_localmin_min_dist = make_spinbox(0, 1_000_000, 1, 15, 0)

#         self.peak_nk_smoothwindow = make_spinbox(0.01, 10.0, 0.01, 0.01, 2)
#         self.peak_nk_avgwindow = make_spinbox(0.01, 10.0, 0.01, 0.75, 2)
#         self.peak_nk_gradthreshweight = make_spinbox(0.1, 10.0, 0.1, 1.5, 1)
#         self.peak_nk_minlenweight = make_spinbox(0.01, 10.0, 0.01, 0.3, 2)
#         self.peak_nk_mindelay = make_spinbox(0.01, 10.0, 0.01, 0.3, 2)

#         self.peak_gamboa_tol = make_spinbox(0.001, 0.01, 0.001, 0.002, 3)

#         self.peak_emrich_window_seconds = make_spinbox(1.0, 100.0, 0.1, 2.0, 1)
#         self.peak_emrich_window_overlap = make_spinbox(0.01, 1.0, 0.01, 0.5, 2)
#         self.peak_emrich_accelerated = pw.AnimatedToggle()
#         self.peak_emrich_accelerated.setChecked(True)
#         self.peak_emrich_accelerated.setProperty("defaultValue", True)

#         self.peak_promac_threshold = make_spinbox(0.0, 1.0, 0.01, 0.33, 2)
#         self.peak_promac_gaussian_sd = make_spinbox(0.0, 100_000, 1, 100, 0)

#         self.peak_commands = pw.CommandBar()
#         self.peak_commands.addActions([self.action_peak_run, self.action_peak_reset_inputs, self.action_peak_reset_data])

#         # Rate Calculation
#         self.rate_handle_incomplete = pw.EnumComboBox(IncompleteWindowMethod)
#         self.rate_period = make_spinbox(1, 10_000, 1, 60, 0)
#         self.rate_every = make_spinbox(1, 600, 1, 10, 0)

#     @QtCore.Slot(bool)
#     def _on_rolling_window_toggled(self, checked: bool) -> None:
#         self.std_container.setEnabled(checked)
#         self.std_window_size.setEnabled(checked)

#     @QtCore.Slot(enum.Enum)
#     def _on_pipeline_changed(self, pipeline: PreprocessPipeline | None = None) -> None:
#         if pipeline is None:
#             self.sf_method.setEnabled(True)
#             self.std_method.setEnabled(True)
#         else:
#             self.sf_method.setCurrentIndex(0)
#             self.std_method.setCurrentIndex(0)
#             self.sf_method.setEnabled(False)
#             self.std_method.setEnabled(False)

#     @QtCore.Slot(enum.Enum)
#     def _on_filter_method_changed(self, filter_method: FilterMethod | None = None) -> None:
#         if filter_method is None:
#             for widget in self.sf_widgets:
#                 widget.setEnabled(False)
#                 restore_default(widget)
#         elif filter_method in [FilterMethod.Butterworth, FilterMethod.ButterworthLegacy, FilterMethod.Bessel]:
#             self.sf_lower_cutoff.setEnabled(True)
#             self.sf_upper_cutoff.setEnabled(True)
#             self.sf_order.setEnabled(True)
#             self.sf_window_size.setEnabled(False)
#             self.sf_powerline.setEnabled(False)
#         elif filter_method == FilterMethod.SavGol:
#             self.sf_lower_cutoff.setEnabled(False)
#             self.sf_upper_cutoff.setEnabled(False)
#             self.sf_order.setEnabled(True)
#             self.sf_window_size.setEnabled(True)
#             self.sf_powerline.setEnabled(False)
#         elif filter_method == FilterMethod.FIR:
#             self.sf_lower_cutoff.setEnabled(True)
#             self.sf_upper_cutoff.setEnabled(True)
#             self.sf_order.setEnabled(False)
#             self.sf_window_size.setEnabled(True)
#             self.sf_powerline.setEnabled(False)
#         elif filter_method == FilterMethod.Powerline:
#             self.sf_lower_cutoff.setEnabled(False)
#             self.sf_upper_cutoff.setEnabled(False)
#             self.sf_order.setEnabled(False)
#             self.sf_window_size.setEnabled(False)
#             self.sf_powerline.setEnabled(True)

#     @QtCore.Slot(enum.Enum)
#     def _on_standardize_method_changed(self, std_method: StandardizationMethod | None = None) -> None:
#         if std_method is None:
#             for widget in self.std_widgets:
#                 widget.setEnabled(False)
#                 restore_default(widget)
#         elif std_method == StandardizationMethod.ZScore:
#             self.std_rolling_window.setEnabled(True)
#         else:
#             self.std_rolling_window.setChecked(False)
#             self.std_rolling_window.setEnabled(False)

#     @QtCore.Slot()
#     def run_processing(self) -> None:
#         pipeline = self.sf_pipeline.current_enum()
#         if pipeline is not None:
#             self.sig_run_pipeline.emit(pipeline)
#         else:
#             sf_method = self.sf_method.current_enum()
#             if sf_method is not None:
#                 sf_params = self.get_filter_params(sf_method)
#                 self.sig_run_filter.emit(sf_params)

#             std_method = self.std_method.current_enum()
#             if std_method is not None:
#                 std_params = self.get_standardize_params(std_method)
#                 self.sig_run_standardization.emit(std_params)

#     def get_filter_params(self, sf_method: FilterMethod) -> _t.SignalFilterParameters:
#         window = self.sf_window_size
#         if window.value() == window.minimum():
#             window_size = "default"
#         else:
#             window_size = window.intValue()
#         return {
#             "lowcut": self.sf_lower_cutoff.floatValue(),
#             "highcut": self.sf_upper_cutoff.floatValue(),
#             "method": sf_method,
#             "order": self.sf_order.intValue(),
#             "window_size": window_size,
#             "powerline": self.sf_powerline.floatValue(),
#         }

#     def get_standardize_params(self, std_method: StandardizationMethod) -> _t.StandardizationParameters:
#         return {
#             "method": std_method,
#             "window_size": self.std_window_size.intValue() if self.std_rolling_window.isChecked() else None,
#         }
        
#     @QtCore.Slot()
#     def run_peak_detection(self) -> None:
#         peak_method = self.peak_method.current_enum()
#         if peak_method is not None:
#             peak_params = self.get_peak_detection_params(peak_method)
#             self.sig_run_peak_detection.emit(peak_method, peak_params)

#     @QtCore.Slot(enum.Enum)
#     def _on_peak_method_changed(self, peak_method: PeakDetectionMethod) -> None:
#         if peak_method == PeakDetectionMethod.PPGElgendi:
#             pass
#             # TODO: Finish recreating parameter input UI

#     def get_peak_detection_params(self, method: PeakDetectionMethod) -> _t.PeakDetectionMethodParameters:
#         if method == PeakDetectionMethod.PPGElgendi:
#             peak_params = _t.PeaksPPGElgendi(
#                 peakwindow=self.peak_elgendi_ppg_peakwindow.floatValue(),
#                 beatwindow=self.peak_elgendi_ppg_beatwindow.floatValue(),
#                 beatoffset=self.peak_elgendi_ppg_beatoffset.floatValue(),
#                 mindelay=self.peak_elgendi_ppg_mindelay.floatValue(),
#             )
#         elif method == PeakDetectionMethod.ECGNeuroKit2:
#             nk_algorithm = self.peak_nk_method.current_enum()
#             if nk_algorithm is None:
#                 nk_algorithm = NK2ECGPeakDetectionMethod.Default
#             if nk_algorithm == NK2ECGPeakDetectionMethod.Default:
#                 nk_params = _t.NK2PeaksNeuroKit(
#                     smoothwindow=self.peak_nk_smoothwindow.floatValue(),
#                     avgwindow=self.peak_nk_avgwindow.floatValue(),
#                     gradthreshweight=self.peak_nk_gradthreshweight.floatValue(),
#                     minlenweight=self.peak_nk_minlenweight.floatValue(),
#                     mindelay=self.peak_nk_mindelay.floatValue(),
#                 )
#             elif nk_algorithm == NK2ECGPeakDetectionMethod.Promac:
#                 nk_params = _t.NK2PeaksPromac(
#                     threshold=self.peak_promac_threshold.floatValue(),
#                     gaussian_sd=self.peak_promac_gaussian_sd.intValue(),
#                 )
#             elif nk_algorithm == NK2ECGPeakDetectionMethod.Gamboa2008:
#                 nk_params = _t.NK2PeaksGamboa(tol=self.peak_gamboa_tol.floatValue())
#             elif nk_algorithm == NK2ECGPeakDetectionMethod.Emrich2023:
#                 nk_params = _t.NK2PeaksEmrich(
#                     window_seconds=self.peak_emrich_window_seconds.floatValue(),
#                     window_overlap=self.peak_emrich_window_overlap.floatValue(),
#                     accelerated=self.peak_emrich_accelerated.isChecked(),
#                 )
#             else:
#                 nk_params = None

#             peak_params = _t.PeaksECGNeuroKit2(method=nk_algorithm, params=nk_params)

#         elif method == PeakDetectionMethod.LocalMaxima:
#             peak_params = _t.PeaksLocalMaxima(
#                 search_radius=self.peak_localmax_radius.intValue(),
#                 min_distance=self.peak_localmax_min_dist.intValue(),
#             )

#         elif method == PeakDetectionMethod.LocalMinima:
#             peak_params = _t.PeaksLocalMinima(
#                 search_radius=self.peak_localmin_radius.intValue(),
#                 min_distance=self.peak_localmin_min_dist.intValue(),
#             )

#         elif method == PeakDetectionMethod.WFDBXQRS:
#             peak_dir = self.peak_xqrs_direction.current_enum()
#             if peak_dir is None:
#                 peak_dir = WFDBPeakDirection.Up
#             peak_params = _t.PeaksWFDBXQRS(
#                 search_radius=self.peak_xqrs_radius.intValue(),
#                 peak_dir=peak_dir,
#                 min_peak_distance=self.peak_xqrs_min_dist.intValue(),
#             )

#         return peak_params