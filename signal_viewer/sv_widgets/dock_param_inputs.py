import decimal
import enum
import inspect

from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import AnimatedToggleSwitch, DecimalSpinBox, ToggleSwitch

from signal_viewer.enum_defs import (
    FilterMethod,
    IncompleteWindowMethod,
    PeakDetectionAlgorithm,
    PreprocessPipeline,
    StandardizationMethod,
    WFDBPeakDirection,
)
from signal_viewer.generated.ui_param_inputs import Ui_containerParamInputs
from signal_viewer.type_defs import (
    PeakDetectionAlgorithmParameters,
    PeaksECGEmrich,
    PeaksECGGamboa,
    PeaksECGNeuroKit,
    PeaksECGPromac,
    PeaksECGXQRS,
    PeaksLocalMaxima,
    PeaksLocalMinima,
    PeaksPPGElgendi,
    RollingRateKwargs,
    SignalFilterKwargs,
    SignalStandardizeKwargs,
)

D = decimal.Decimal
type SupportsDecimal = int | float | D


def _restore_default(w: QtWidgets.QWidget | QtCore.QObject) -> None:
    if isinstance(w, QtWidgets.QComboBox):
        w.setCurrentIndex(0)
        return

    if default_value := w.property("defaultValue"):
        if isinstance(w, (DecimalSpinBox, QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            w.setValue(default_value)
            return
        elif isinstance(w, (ToggleSwitch, AnimatedToggleSwitch, QtWidgets.QCheckBox)):
            w.setChecked(default_value)
            return


def _setup_spinbox(
    dec_sb: DecimalSpinBox,
    min: SupportsDecimal,
    max: SupportsDecimal,
    step: SupportsDecimal,
    default: SupportsDecimal,
    precision: int,
) -> None:
    dec_sb.setRange(min, max)
    dec_sb.setSingleStep(step)
    dec_sb.setDecimals(precision)
    dec_sb.setProperty("defaultValue", default)
    _restore_default(dec_sb)


def _get_docstring(obj: object) -> str:
    return inspect.getdoc(obj) or ""


class ParameterInputs(QtWidgets.QWidget):
    sig_run_pipeline = QtCore.Signal(enum.StrEnum)  # PreprocessPipeline
    sig_run_filter = QtCore.Signal(dict)  # SignalFilterParameters
    sig_run_standardization = QtCore.Signal(dict)  # StandardizationParameters
    sig_reset_data = QtCore.Signal()

    sig_run_peak_detection = QtCore.Signal(enum.StrEnum, dict)
    sig_clear_peaks = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_containerParamInputs()
        self.ui.setupUi(self)

        self._setup_actions()
        self._setup_widgets()
        self._on_peak_method_changed(0)

    @property
    def sf_widgets(self) -> list[QtWidgets.QWidget]:
        return [
            self.ui.sf_lower_cutoff,
            self.ui.sf_upper_cutoff,
            self.ui.sf_order,
            self.ui.sf_window_size,
            self.ui.sf_powerline,
        ]

    @property
    def std_widgets(self) -> list[QtWidgets.QWidget]:
        return [
            self.ui.std_rolling_window,
            self.ui.std_window_size,
        ]

    def _setup_actions(self) -> None:
        # Signal Filter
        self.action_sf_run = QtGui.QAction(QtGui.QIcon("://icons/Play.svg"), "Process Signal", self)
        self.action_sf_run.setToolTip("Apply the selected processing steps to the signal data.")
        self.action_sf_run.triggered.connect(self.run_processing)

        self.action_sf_reset_inputs = QtGui.QAction(QtGui.QIcon("://icons/ArrowReset.svg"), "Restore Defaults", self)
        self.action_sf_reset_inputs.setToolTip("Reset all inputs to their default values.")
        self.action_sf_reset_inputs.triggered.connect(self.reset_inputs)
        self.action_sf_reset_data = QtGui.QAction(QtGui.QIcon("://icons/Broom.svg"), "Reset Signal", self)
        self.action_sf_reset_data.setToolTip("Reset the signal data to its original, unprocessed state.")
        self.action_sf_reset_data.triggered.connect(self.reset_data)

        # Peak Detection
        self.action_peak_run = QtGui.QAction(QtGui.QIcon("://icons/Play.svg"), "Detect Peaks", self)
        self.action_peak_run.setToolTip("Run the selected peak detection algorithm.")
        self.action_peak_run.triggered.connect(self.run_peak_detection)
        self.action_peak_reset_inputs = QtGui.QAction(QtGui.QIcon("://icons/ArrowReset.svg"), "Restore Defaults", self)
        self.action_peak_reset_inputs.setToolTip("Reset all inputs to their default values.")
        self.action_peak_reset_inputs.triggered.connect(self.reset_inputs)
        self.action_peak_reset_data = QtGui.QAction(QtGui.QIcon("://icons/Broom.svg"), "Reset Peaks", self)
        self.action_peak_reset_data.setToolTip("Remove all peaks. Does not reset the signal data.")
        self.action_peak_reset_data.triggered.connect(self.clear_peaks)

    def _setup_widgets(self) -> None:
        # Signal Filter
        self.ui.sf_pipeline.setAllowNone(True)
        self.ui.sf_pipeline.set_enum_class(PreprocessPipeline)
        self.ui.sf_pipeline.currentIndexChanged.connect(self._on_pipeline_changed)

        self.ui.sf_method.setAllowNone(True)
        self.ui.sf_method.set_enum_class(FilterMethod)
        self.ui.sf_method.currentIndexChanged.connect(self._on_filter_method_changed)

        _setup_spinbox(self.ui.sf_lower_cutoff, 0, 100_000, 0.1, 0.5, 1)
        _setup_spinbox(self.ui.sf_upper_cutoff, 0, 100_000, 0.1, 8.0, 1)
        _setup_spinbox(self.ui.sf_order, 1, 10, 1, 3, 0)
        _setup_spinbox(self.ui.sf_window_size, 5, 1_000_000, 10, 100, 0)
        _setup_spinbox(self.ui.sf_powerline, 0, 100_000, 0.1, 50.0, 1)

        sf_tb = QtWidgets.QToolBar("sf_command_bar")
        sf_tb.setIconSize(QtCore.QSize(16, 16))
        sf_tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        sf_tb.addActions([self.action_sf_run, self.action_sf_reset_inputs, self.action_sf_reset_data])

        sf_tb_l = QtWidgets.QVBoxLayout()
        sf_tb_l.setContentsMargins(0, 0, 0, 0)
        sf_tb_l.setSpacing(0)
        sf_tb_l.addWidget(sf_tb)
        self.ui.sf_command_bar.setLayout(sf_tb_l)

        # Standardization
        self.ui.std_method.setAllowNone(True)
        self.ui.std_method.set_enum_class(StandardizationMethod)
        self.ui.std_method.currentIndexChanged.connect(self._on_std_method_changed)

        self.ui.std_rolling_window.setChecked(False)
        self.ui.std_rolling_window.setProperty("defaultValue", False)
        self.ui.std_rolling_window.toggled.connect(self._on_rolling_window_toggled)
        _setup_spinbox(self.ui.std_window_size, 5, 999_999, 2, 100, 0)

        # Peak Detection
        self.ui.peak_method.set_enum_class(PeakDetectionAlgorithm, doc_data=_get_docstring)
        self.ui.peak_method.currentIndexChanged.connect(self._on_peak_method_changed)

        self.ui.peak_xqrs_direction.set_enum_class(WFDBPeakDirection)
        _setup_spinbox(self.ui.peak_xqrs_radius, 5, 99_999, 1, 90, 0)
        _setup_spinbox(self.ui.peak_xqrs_min_dist, 0, 100_000, 1, 10, 0)

        _setup_spinbox(self.ui.peak_ppg_elgendi_peakwindow, 0.05, 5.0, 0.001, 0.111, 3)
        _setup_spinbox(self.ui.peak_ppg_elgendi_beatwindow, 0.1, 5.0, 0.001, 0.667, 3)
        _setup_spinbox(self.ui.peak_ppg_elgendi_beatoffset, 0.0, 1.0, 0.01, 0.02, 2)
        _setup_spinbox(self.ui.peak_ppg_elgendi_mindelay, 0.0, 10.0, 0.01, 0.3, 2)

        _setup_spinbox(self.ui.peak_localmax_radius, 5, 9_999, 1, 111, 0)
        _setup_spinbox(self.ui.peak_localmax_min_dist, 0, 1_000_000, 1, 15, 0)

        _setup_spinbox(self.ui.peak_localmin_radius, 5, 9_999, 1, 111, 0)
        _setup_spinbox(self.ui.peak_localmin_min_dist, 0, 1_000_000, 1, 15, 0)

        _setup_spinbox(self.ui.peak_ecg_nk_smoothwindow, 0.01, 10.0, 0.01, 0.01, 2)
        _setup_spinbox(self.ui.peak_ecg_nk_avgwindow, 0.01, 10.0, 0.01, 0.75, 2)
        _setup_spinbox(self.ui.peak_ecg_nk_gradthreshweight, 0.1, 10.0, 0.1, 1.5, 1)
        _setup_spinbox(self.ui.peak_ecg_nk_minlenweight, 0.01, 10.0, 0.01, 0.3, 2)
        _setup_spinbox(self.ui.peak_ecg_nk_mindelay, 0.01, 10.0, 0.01, 0.3, 2)

        _setup_spinbox(self.ui.peak_ecg_gamboa_tol, 0.001, 0.01, 0.001, 0.002, 3)

        _setup_spinbox(self.ui.peak_ecg_emrich_window_seconds, 1.0, 100.0, 0.1, 2.0, 1)
        _setup_spinbox(self.ui.peak_ecg_emrich_window_overlap, 0.01, 1.0, 0.01, 0.5, 2)
        self.ui.peak_ecg_emrich_accelerated.setChecked(True)
        self.ui.peak_ecg_emrich_accelerated.setProperty("defaultValue", True)

        _setup_spinbox(self.ui.peak_ecg_promac_threshold, 0.0, 1.0, 0.01, 0.33, 2)
        _setup_spinbox(self.ui.peak_ecg_promac_gaussian_sd, 0.0, 100_000, 1, 100, 0)

        peak_tb = QtWidgets.QToolBar("peak_command_bar")
        peak_tb.setIconSize(QtCore.QSize(16, 16))
        peak_tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        peak_tb.addActions(
            [
                self.action_peak_run,
                self.action_peak_reset_inputs,
                self.action_peak_reset_data,
            ]
        )

        peak_tb_l = QtWidgets.QVBoxLayout()
        peak_tb_l.setContentsMargins(0, 0, 0, 0)
        peak_tb_l.setSpacing(0)
        peak_tb_l.addWidget(peak_tb)
        self.ui.peak_command_bar.setLayout(peak_tb_l)

        # Rate Calculation
        self.ui.rate_handle_incomplete.set_enum_class(IncompleteWindowMethod)
        _setup_spinbox(self.ui.rate_period, 1, 10_000, 1, 60, 0)
        _setup_spinbox(self.ui.rate_every, 1, 600, 1, 10, 0)

    @QtCore.Slot()
    def reset_data(self) -> None:
        self.sig_reset_data.emit()

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        self.sig_clear_peaks.emit()

    @QtCore.Slot()
    def reset_inputs(self) -> None:
        sender = self.sender()
        if sender is self.action_peak_reset_inputs:
            current_page = self.ui.stacked_widget_peak.currentWidget()
            for c in current_page.children():
                _restore_default(c)
        elif sender is self.action_sf_reset_inputs:
            for c in self.sf_widgets + self.std_widgets + [self.ui.sf_pipeline, self.ui.sf_method, self.ui.std_method]:
                _restore_default(c)

    @QtCore.Slot(bool)
    def _on_rolling_window_toggled(self, checked: bool) -> None:
        self.ui.std_window_size.setEnabled(checked)

    @QtCore.Slot(int)
    def _on_pipeline_changed(self, index: int) -> None:
        pipeline: PreprocessPipeline | None = self.ui.sf_pipeline.current_enum()
        if pipeline is None:
            self.ui.sf_method.setEnabled(True)
            self.ui.std_method.setEnabled(True)
        else:
            self.ui.sf_method.setCurrentIndex(0)
            self.ui.std_method.setCurrentIndex(0)
            self.ui.sf_method.setEnabled(False)
            self.ui.std_method.setEnabled(False)

    @QtCore.Slot(int)
    def _on_filter_method_changed(self, index: int) -> None:
        filter_method: FilterMethod | None = self.ui.sf_method.current_enum()
        if filter_method is None:
            for widget in self.sf_widgets:
                widget.setEnabled(False)
                _restore_default(widget)
        elif filter_method in [
            FilterMethod.Butterworth,
            FilterMethod.ButterworthLegacy,
            FilterMethod.Bessel,
        ]:
            self.ui.sf_lower_cutoff.setEnabled(True)
            self.ui.sf_upper_cutoff.setEnabled(True)
            self.ui.sf_order.setEnabled(True)
            self.ui.sf_window_size.setEnabled(False)
            self.ui.sf_powerline.setEnabled(False)
        elif filter_method == FilterMethod.SavGol:
            self.ui.sf_lower_cutoff.setEnabled(False)
            self.ui.sf_upper_cutoff.setEnabled(False)
            self.ui.sf_order.setEnabled(True)
            self.ui.sf_window_size.setEnabled(True)
            self.ui.sf_powerline.setEnabled(False)
        elif filter_method == FilterMethod.FIR:
            self.ui.sf_lower_cutoff.setEnabled(True)
            self.ui.sf_upper_cutoff.setEnabled(True)
            self.ui.sf_order.setEnabled(False)
            self.ui.sf_window_size.setEnabled(True)
            self.ui.sf_powerline.setEnabled(False)
        elif filter_method == FilterMethod.Powerline:
            self.ui.sf_lower_cutoff.setEnabled(False)
            self.ui.sf_upper_cutoff.setEnabled(False)
            self.ui.sf_order.setEnabled(False)
            self.ui.sf_window_size.setEnabled(False)
            self.ui.sf_powerline.setEnabled(True)

    @QtCore.Slot(int)
    def _on_std_method_changed(self, index: int) -> None:
        std_method: StandardizationMethod | None = self.ui.std_method.current_enum()
        if std_method is None:
            for widget in self.std_widgets:
                widget.setEnabled(False)
                _restore_default(widget)
        elif std_method == StandardizationMethod.ZScore:
            self.ui.std_rolling_window.setEnabled(True)
        else:
            self.ui.std_rolling_window.setChecked(False)
            self.ui.std_rolling_window.setEnabled(False)

    @QtCore.Slot()
    def run_processing(self) -> None:
        pipeline: PreprocessPipeline | None = self.ui.sf_pipeline.current_enum()
        if pipeline is not None:
            self.sig_run_pipeline.emit(pipeline)
        else:
            sf_method = self.ui.sf_method.current_enum()
            if sf_method is not None:
                sf_params = self.get_filter_params(sf_method)
                self.sig_run_filter.emit(sf_params)

            std_method = self.ui.std_method.current_enum()
            if std_method is not None:
                std_params = self.get_std_params(std_method)
                self.sig_run_standardization.emit(std_params)

    def get_filter_params(self, sf_method: FilterMethod) -> SignalFilterKwargs:
        window = self.ui.sf_window_size
        if window.value() == window.minimum():
            window_size = "default"
        else:
            window_size = window.intValue()
        return {
            "lowcut": self.ui.sf_lower_cutoff.floatValue(),
            "highcut": self.ui.sf_upper_cutoff.floatValue(),
            "method": sf_method,
            "order": self.ui.sf_order.intValue(),
            "window_size": window_size,
            "powerline": self.ui.sf_powerline.floatValue(),
        }

    def get_std_params(self, std_method: StandardizationMethod) -> SignalStandardizeKwargs:
        return {
            "method": std_method,
            "window_size": self.ui.std_window_size.intValue() if self.ui.std_rolling_window.isChecked() else None,
        }

    @QtCore.Slot()
    def run_peak_detection(self) -> None:
        peak_method: PeakDetectionAlgorithm | None = self.ui.peak_method.current_enum()
        if peak_method is not None:
            peak_params = self.get_peak_detection_params(peak_method)
            self.sig_run_peak_detection.emit(peak_method, peak_params)

    @QtCore.Slot(int)
    def _on_peak_method_changed(self, index: int) -> None:
        peak_method: PeakDetectionAlgorithm | None = self.ui.peak_method.current_enum()
        if peak_method == PeakDetectionAlgorithm.PPG_Elgendi:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_ppg_elgendi)
        elif peak_method == PeakDetectionAlgorithm.ECG_NeuroKit:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_ecg_nk)
        elif peak_method == PeakDetectionAlgorithm.ECG_Promac:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_ecg_promac)
        elif peak_method == PeakDetectionAlgorithm.ECG_Emrich_2023:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_ecg_emrich)
        elif peak_method == PeakDetectionAlgorithm.ECG_Gamboa_2008:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_ecg_gamboa)
        elif peak_method == PeakDetectionAlgorithm.LocalMaxima:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_localmax)
        elif peak_method == PeakDetectionAlgorithm.LocalMinima:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_localmin)
        elif peak_method == PeakDetectionAlgorithm.ECG_XQRS:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_xqrs)
        else:
            self.ui.stacked_widget_peak.setCurrentWidget(self.ui.page_peak_no_params)

    def get_peak_detection_params(self, method: PeakDetectionAlgorithm) -> PeakDetectionAlgorithmParameters | None:
        peak_params = None
        if method == PeakDetectionAlgorithm.PPG_Elgendi:
            peak_params = PeaksPPGElgendi(
                peakwindow=self.ui.peak_ppg_elgendi_peakwindow.floatValue(),
                beatwindow=self.ui.peak_ppg_elgendi_beatwindow.floatValue(),
                beatoffset=self.ui.peak_ppg_elgendi_beatoffset.floatValue(),
                mindelay=self.ui.peak_ppg_elgendi_mindelay.floatValue(),
            )
        elif method == PeakDetectionAlgorithm.ECG_NeuroKit:
            peak_params = PeaksECGNeuroKit(
                smoothwindow=self.ui.peak_ecg_nk_smoothwindow.floatValue(),
                avgwindow=self.ui.peak_ecg_nk_avgwindow.floatValue(),
                gradthreshweight=self.ui.peak_ecg_nk_gradthreshweight.floatValue(),
                minlenweight=self.ui.peak_ecg_nk_minlenweight.floatValue(),
                mindelay=self.ui.peak_ecg_nk_mindelay.floatValue(),
            )
        elif method == PeakDetectionAlgorithm.ECG_Promac:
            peak_params = PeaksECGPromac(
                threshold=self.ui.peak_ecg_promac_threshold.floatValue(),
                gaussian_sd=self.ui.peak_ecg_promac_gaussian_sd.intValue(),
            )
        elif method == PeakDetectionAlgorithm.ECG_Gamboa_2008:
            peak_params = PeaksECGGamboa(tol=self.ui.peak_ecg_gamboa_tol.floatValue())
        elif method == PeakDetectionAlgorithm.ECG_Emrich_2023:
            peak_params = PeaksECGEmrich(
                window_seconds=self.ui.peak_ecg_emrich_window_seconds.floatValue(),
                window_overlap=self.ui.peak_ecg_emrich_window_overlap.floatValue(),
                accelerated=self.ui.peak_ecg_emrich_accelerated.isChecked(),
            )
        elif method == PeakDetectionAlgorithm.LocalMaxima:
            peak_params = PeaksLocalMaxima(
                search_radius=self.ui.peak_localmax_radius.intValue(),
                min_distance=self.ui.peak_localmax_min_dist.intValue(),
            )

        elif method == PeakDetectionAlgorithm.LocalMinima:
            peak_params = PeaksLocalMinima(
                search_radius=self.ui.peak_localmin_radius.intValue(),
                min_distance=self.ui.peak_localmin_min_dist.intValue(),
            )

        elif method == PeakDetectionAlgorithm.ECG_XQRS:
            peak_dir: WFDBPeakDirection | None = self.ui.peak_xqrs_direction.current_enum()
            if peak_dir is None:
                peak_dir = WFDBPeakDirection.Up
            peak_params = PeaksECGXQRS(
                search_radius=self.ui.peak_xqrs_radius.intValue(),
                peak_dir=peak_dir,
                min_peak_distance=self.ui.peak_xqrs_min_dist.intValue(),
            )

        return peak_params

    def get_rate_params(self) -> RollingRateKwargs:
        return RollingRateKwargs(
            sec_new_window_every=self.ui.rate_every.intValue(),
            sec_window_length=self.ui.rate_period.intValue(),
            incomplete_window_method=IncompleteWindowMethod(self.ui.rate_handle_incomplete.currentData()),
        )


class InputsDock(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Parameter Inputs", parent=parent)
        self.setObjectName("DockWidgetParameterInputs")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWindowIcon(QtGui.QIcon("://icons/Options.svg"))
        self.toggleViewAction().setIcon(QtGui.QIcon("://icons/Options.svg"))

        self.ui = ParameterInputs()
        self.setWidget(self.ui)
