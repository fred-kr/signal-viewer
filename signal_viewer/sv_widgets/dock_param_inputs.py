"""
The "Parameter Inputs" dock: preprocessing, peak detection and rate calculation settings.

`ParameterInputs` owns the widgets compiled from `generated/param_inputs.ui`, sets their ranges and defaults, and
translates button presses into one request object per action (`ProcessingRequest`, `PeakDetectionRequest`,
`RollingRateKwargs`) that it emits for `SVApp` to forward to the `DataController`. It never touches data itself.

Help texts of every input live in `signal_viewer.help_texts` and are applied at the end of `_setup_widgets`.
"""

import decimal

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
from signal_viewer.help_texts import apply_help_texts, enum_doc
from signal_viewer.type_defs import (
    PeakDetectionAlgorithmParameters,
    PeakDetectionRequest,
    PeaksECGEmrich,
    PeaksECGGamboa,
    PeaksECGNeuroKit,
    PeaksECGPromac,
    PeaksECGXQRS,
    PeaksLocalMaxima,
    PeaksLocalMinima,
    PeaksPPGElgendi,
    ProcessingRequest,
    RollingRateKwargs,
    SignalFilterKwargs,
    SignalStandardizeKwargs,
)

D = decimal.Decimal
type SupportsDecimal = int | float | D


def _restore_default(w: QtWidgets.QWidget | QtCore.QObject) -> None:
    """Sets the widget back to its `defaultValue` property: an index for combo boxes, a value or checked state else."""
    if isinstance(w, QtWidgets.QComboBox):
        if default_idx := w.property("defaultValue"):
            w.setCurrentIndex(default_idx)
        else:
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
    correction_mode: DecimalSpinBox.CorrectionMode = DecimalSpinBox.CorrectionMode.CorrectToNearestValue,
    keyboard_tracking: bool = True,
) -> None:
    """
    Configures a spin box in one call and stores `default` as its `defaultValue` property.

    The property is what `_restore_default` and the help texts (`help_texts.default_and_range`) read, so the value
    shown in the tooltip is always the one "Restore Defaults" sets.
    """
    dec_sb.setRange(min, max)
    dec_sb.setSingleStep(step)
    dec_sb.setDecimals(precision)
    dec_sb.setProperty("defaultValue", default)
    dec_sb.setCorrectionMode(correction_mode)
    dec_sb.setKeyboardTracking(keyboard_tracking)
    _restore_default(dec_sb)


class ParameterInputs(QtWidgets.QWidget):
    """
    The widget inside `InputsDock`: three tabs (Preprocessing, Peak Detection, Rate Calculation) and their inputs.

    Reading the inputs happens in the `get_*` methods; each returns the typed dictionary the data layer expects.
    The widget emits one signal per user action with everything the action needs, so `SVApp` never reads widgets.
    """

    # Each user action maps to exactly one signal carrying everything the action needs.
    sig_run_processing = QtCore.Signal(object)  # ProcessingRequest
    sig_reset_data = QtCore.Signal()

    sig_run_peak_detection = QtCore.Signal(object)  # PeakDetectionRequest
    sig_clear_peaks = QtCore.Signal()

    sig_rate_params_changed = QtCore.Signal(dict)  # RollingRateKwargs, emitted whenever a rate input changes

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_containerParamInputs()
        self.ui.setupUi(self)

        self._setup_actions()
        self._setup_widgets()
        self._on_peak_method_changed(0)

    @property
    def sf_widgets(self) -> list[QtWidgets.QWidget]:
        """The custom filter parameter inputs, in the order they appear."""
        return [
            self.ui.sf_lower_cutoff,
            self.ui.sf_upper_cutoff,
            self.ui.sf_order,
            self.ui.sf_window_size,
            self.ui.sf_powerline,
        ]

    @property
    def std_widgets(self) -> list[QtWidgets.QWidget]:
        """The standardization parameter inputs."""
        return [
            self.ui.std_rolling_window,
            self.ui.std_window_size,
        ]

    def _setup_actions(self) -> None:
        # The tooltips of these actions come from `help_texts.HELP_TEXTS`, keyed by attribute name.
        self.action_sf_run = QtGui.QAction(QtGui.QIcon("://icons/Play.svg"), "Apply to Signal", self)
        self.action_sf_run.triggered.connect(self.run_processing)

        self.action_sf_reset_inputs = QtGui.QAction(QtGui.QIcon("://icons/ArrowReset.svg"), "Restore Defaults", self)
        self.action_sf_reset_inputs.triggered.connect(self.reset_inputs)
        self.action_sf_reset_data = QtGui.QAction(QtGui.QIcon("://icons/Broom.svg"), "Reset Signal", self)
        self.action_sf_reset_data.triggered.connect(self.reset_data)

        self.action_peak_run = QtGui.QAction(QtGui.QIcon("://icons/Play.svg"), "Run detection", self)
        self.action_peak_run.triggered.connect(self.run_peak_detection)
        self.action_peak_reset_inputs = QtGui.QAction(QtGui.QIcon("://icons/ArrowReset.svg"), "Restore Defaults", self)
        self.action_peak_reset_inputs.triggered.connect(self.reset_inputs)
        self.action_peak_reset_data = QtGui.QAction(QtGui.QIcon("://icons/Broom.svg"), "Reset Peaks", self)
        self.action_peak_reset_data.triggered.connect(self.clear_peaks)

    def _setup_widgets(self) -> None:
        # Signal Filter
        self.ui.sf_pipeline.setAllowNone(True)
        self.ui.sf_pipeline.set_enum_class(PreprocessPipeline, doc_data=enum_doc)
        self.ui.sf_pipeline.currentIndexChanged.connect(self._on_pipeline_changed)
        self.ui.sf_pipeline.setProperty("defaultValue", 1)
        self.ui.sf_pipeline.set_current_enum(PreprocessPipeline.PPG_Elgendi)

        self.ui.sf_method.setAllowNone(True)
        self.ui.sf_method.set_enum_class(FilterMethod, doc_data=enum_doc)
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
        self.ui.std_method.set_enum_class(StandardizationMethod, doc_data=enum_doc)
        self.ui.std_method.currentIndexChanged.connect(self._on_std_method_changed)

        self.ui.std_rolling_window.setChecked(False)
        self.ui.std_rolling_window.setProperty("defaultValue", False)
        self.ui.std_rolling_window.toggled.connect(self._on_rolling_window_toggled)
        _setup_spinbox(self.ui.std_window_size, 5, 999_999, 2, 100, 0)

        # Peak Detection
        self.ui.peak_method.set_enum_class(PeakDetectionAlgorithm, doc_data=enum_doc)
        self.ui.peak_method.currentIndexChanged.connect(self._on_peak_method_changed)

        self.ui.peak_xqrs_direction.set_enum_class(WFDBPeakDirection, doc_data=enum_doc)
        _setup_spinbox(self.ui.peak_xqrs_radius, 5, 99_999, 1, 90, 0)
        _setup_spinbox(self.ui.peak_xqrs_min_dist, 0, 100_000, 1, 10, 0)

        _setup_spinbox(self.ui.peak_ppg_elgendi_peakwindow, 0.05, 5.0, 0.001, 0.111, 3)
        _setup_spinbox(self.ui.peak_ppg_elgendi_beatwindow, 0.1, 5.0, 0.001, 0.667, 3)
        _setup_spinbox(self.ui.peak_ppg_elgendi_beatoffset, 0.0, 1.0, 0.01, 0.02, 2)
        _setup_spinbox(self.ui.peak_ppg_elgendi_mindelay, 0.0, 10.0, 0.01, 0.3, 2)

        # The radius defaults are replaced with half the sampling rate once a file is loaded (`SVApp.read_data`).
        _setup_spinbox(self.ui.peak_localmax_radius, 1, 10_000, 10, 111, 0)
        _setup_spinbox(self.ui.peak_localmin_radius, 1, 10_000, 10, 111, 0)

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
        self.ui.rate_handle_incomplete.set_enum_class(IncompleteWindowMethod, doc_data=enum_doc)
        _setup_spinbox(self.ui.rate_period, 1, 10_000, 1, 60, 0)
        _setup_spinbox(self.ui.rate_every, 1, 600, 1, 10, 0)
        self.ui.rate_period.valueChanged.connect(self._emit_rate_params)
        self.ui.rate_every.valueChanged.connect(self._emit_rate_params)
        self.ui.rate_handle_incomplete.sig_current_enum_changed.connect(self._emit_rate_params)

        # Last: the help texts read the ranges and defaults set above.
        self.refresh_help_texts()

    def refresh_help_texts(self) -> None:
        """Re-applies tooltips and What's This texts. Call after a `defaultValue` property was changed."""
        apply_help_texts(self)

    @QtCore.Slot()
    @QtCore.Slot(object)
    def _emit_rate_params(self, _value: object = None) -> None:
        self.sig_rate_params_changed.emit(self.get_rate_params())

    @QtCore.Slot()
    def reset_data(self) -> None:
        """Asks for the raw signal back ("Reset Signal")."""
        self.sig_reset_data.emit()

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        """Asks for all peaks to be removed ("Reset Peaks")."""
        self.sig_clear_peaks.emit()

    @QtCore.Slot()
    def reset_inputs(self) -> None:
        """
        Restores the defaults of the tab whose "Restore Defaults" action sent the signal.

        For the peak tab only the inputs of the currently shown method page are reset.
        """
        sender = self.sender()
        if sender is self.action_peak_reset_inputs:
            current_page = self.ui.stacked_widget_peak.currentWidget()
            if current_page is not None:
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
        # A pipeline replaces the custom steps (see `ProcessingRequest`), so their inputs are disabled meanwhile.
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
        """
        Enables the filter parameters the selected method uses, mirroring `neurokit2.signal_filter`.

        The `FilterMethod` member descriptions and the user guide state the same mapping; change all three together.
        """
        filter_method: FilterMethod | None = self.ui.sf_method.current_enum()
        if filter_method is None:
            for widget in self.sf_widgets:
                widget.setEnabled(False)
                _restore_default(widget)
            return

        uses_cutoffs = filter_method in {
            FilterMethod.Butterworth,
            FilterMethod.ButterworthLegacy,
            FilterMethod.ButterworthZI,
            FilterMethod.Bessel,
            FilterMethod.FIR,
        }
        uses_order = filter_method in {
            FilterMethod.Butterworth,
            FilterMethod.ButterworthLegacy,
            FilterMethod.ButterworthZI,
            FilterMethod.Bessel,
            FilterMethod.SavGol,
        }
        uses_window = filter_method in {FilterMethod.SavGol, FilterMethod.FIR}
        uses_powerline = filter_method == FilterMethod.Powerline

        self.ui.sf_lower_cutoff.setEnabled(uses_cutoffs)
        self.ui.sf_upper_cutoff.setEnabled(uses_cutoffs)
        self.ui.sf_order.setEnabled(uses_order)
        self.ui.sf_window_size.setEnabled(uses_window)
        self.ui.sf_powerline.setEnabled(uses_powerline)

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
            # Windowed MAD scaling is not supported (`signal_processing.standardize_signal`).
            self.ui.std_rolling_window.setChecked(False)
            self.ui.std_rolling_window.setEnabled(False)

    @QtCore.Slot()
    def run_processing(self) -> None:
        """Collects the selected processing steps into one `ProcessingRequest` and emits it."""
        pipeline: PreprocessPipeline | None = self.ui.sf_pipeline.current_enum()
        if pipeline is not None:
            self.sig_run_processing.emit(ProcessingRequest(pipeline=pipeline))
            return

        sf_method: FilterMethod | None = self.ui.sf_method.current_enum()
        std_method: StandardizationMethod | None = self.ui.std_method.current_enum()
        self.sig_run_processing.emit(
            ProcessingRequest(
                filter=self.get_filter_params(sf_method) if sf_method is not None else None,
                standardize=self.get_std_params(std_method) if std_method is not None else None,
            )
        )

    def get_filter_params(self, sf_method: FilterMethod) -> SignalFilterKwargs:
        """
        The custom filter inputs as keyword arguments for `signal_processing.filter_signal`.

        A window size at the spin box minimum is sent as `"default"`, which lets neurokit2 pick its own window.
        Cutoffs of 0 are sent as given; `filter_signal` turns them into `None` (no cutoff on that side).
        """
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
        """The standardization inputs as keyword arguments for `Section.standardize_signal`."""
        return {
            "method": std_method,
            "robust": std_method == StandardizationMethod.ZScoreRobust,
            "window_size": self.ui.std_window_size.intValue() if self.ui.std_rolling_window.isChecked() else None,
        }

    @QtCore.Slot()
    def run_peak_detection(self) -> None:
        """Emits a `PeakDetectionRequest` for the selected method; nothing happens when no method is selected."""
        request = self.get_peak_detection_request()
        if request is not None:
            self.sig_run_peak_detection.emit(request)

    def get_peak_detection_request(self) -> PeakDetectionRequest | None:
        """The currently selected peak detection method and its parameters, or `None` if no method is selected."""
        peak_method: PeakDetectionAlgorithm | None = self.ui.peak_method.current_enum()
        if peak_method is None:
            return None
        return PeakDetectionRequest(method=peak_method, params=self.get_peak_detection_params(peak_method))

    @QtCore.Slot(int)
    def _on_peak_method_changed(self, index: int) -> None:
        """Shows the parameter page of the selected method; methods without parameters share a placeholder page."""
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
        """
        The parameter inputs of `method` as the typed dictionary `peak_detection.find_peaks` expects.

        `None` for methods without adjustable parameters. The local-extrema methods use the radius both as search
        radius and as minimum peak distance.
        """
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
            radius = min_distance = self.ui.peak_localmax_radius.intValue()
            peak_params = PeaksLocalMaxima(
                search_radius=radius,
                min_distance=min_distance,
            )

        elif method == PeakDetectionAlgorithm.LocalMinima:
            radius = min_distance = self.ui.peak_localmin_radius.intValue()
            peak_params = PeaksLocalMinima(
                search_radius=radius,
                min_distance=min_distance,
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
        """The rate tab inputs as keyword arguments for `section.compute_rate_rolling`."""
        return RollingRateKwargs(
            sec_new_window_every=self.ui.rate_every.intValue(),
            sec_window_length=self.ui.rate_period.intValue(),
            incomplete_window_method=IncompleteWindowMethod(self.ui.rate_handle_incomplete.currentData()),
        )


class InputsDock(QtWidgets.QDockWidget):
    """
    Dock window holding `ParameterInputs`. Shown on the Graph page only; disabled while the active section is
    locked or is the base section (`SVApp._update_lock_dependent_states`).
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Parameter Inputs", parent=parent)
        self.setObjectName("DockWidgetParameterInputs")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWindowIcon(QtGui.QIcon("://icons/Options.svg"))
        self.toggleViewAction().setIcon(QtGui.QIcon("://icons/Options.svg"))
        self.toggleViewAction().setToolTip("Show or hide the Parameter Inputs dock")

        self.ui = ParameterInputs()
        self.setWidget(self.ui)
