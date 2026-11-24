"""
The parameters dialog: custom preprocessing, peak detection and rate calculation inputs.

`ParameterDialog` owns the widgets compiled from `generated/dialog_param_inputs.ui`, sets their ranges and defaults,
and turns their values into the typed dictionaries and request objects the data layer expects. It never touches data
itself. `ParameterInputs` (the dock) creates exactly one instance, opens it from two places and reads it whenever a
run is requested, so the dialog's widgets are the single store of every parameter value.

Help texts of every input live in `signal_viewer.help_texts`; `ParameterInputs.refresh_help_texts` applies them.
"""

import decimal

import attrs
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import AnimatedToggleSwitch, DecimalSpinBox, EnumComboBox, ToggleSwitch

from signal_viewer.enum_defs import (
    FilterMethod,
    IncompleteWindowMethod,
    PeakDetectionAlgorithm,
    StandardizationMethod,
    WFDBPeakDirection,
)
from signal_viewer.generated.ui_dialog_param_inputs import Ui_paramDialog
from signal_viewer.help_texts import enum_doc
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

_CHECK_TYPES = (ToggleSwitch, AnimatedToggleSwitch, QtWidgets.QCheckBox)
_SPIN_TYPES = (DecimalSpinBox, QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)

PIPELINE_LOCK_TOOLTIP = "Locked while a pipeline is selected. Choose 'Custom' in the Pipeline dropdown to edit."
"""Tooltip of the Preprocessing tab while it is disabled."""


def _restore_default(w: QtWidgets.QWidget | QtCore.QObject) -> None:
    """Sets the widget back to its `defaultValue` property: an index for combo boxes, a value or checked state else."""
    default = w.property("defaultValue")
    if isinstance(w, QtWidgets.QComboBox):
        w.setCurrentIndex(default or 0)
    elif default is None:
        return
    elif isinstance(w, _SPIN_TYPES):
        w.setValue(default)
    elif isinstance(w, _CHECK_TYPES):
        w.setChecked(default)


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


@attrs.frozen
class _Snapshot:
    """The value of every input of the dialog at one moment; what Cancel puts back."""

    combos: dict[EnumComboBox, int]
    checks: dict[QtWidgets.QCheckBox, bool]
    spins: dict[DecimalSpinBox, decimal.Decimal]


class ParameterDialog(QtWidgets.QDialog):
    """
    Three tabs of inputs (Preprocessing, Peak detection, Rate calculation) behind four buttons.

    - **Run** keeps the edits and emits `sig_run_requested`; the dialog stays open, so a parameter can be tuned
      against the plot behind it. It is the default button: Enter in an input runs instead of closing.
    - **OK** keeps the edits and closes without running.
    - **Cancel** (and closing the window) puts every input back to its value at the last `open_tab` or Run.
    - **Restore Defaults** resets the inputs of the visible tab; on the Peak detection tab only those of the shown
      method.

    Reading the inputs happens in the `get_*` methods; each returns what the data layer expects.
    """

    sig_run_requested = QtCore.Signal()
    sig_rate_params_changed = QtCore.Signal(dict)  # RollingRateKwargs, emitted whenever a rate input changes

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_paramDialog()
        self.ui.setupUi(self)
        # The form still carries Designer's placeholders for these two.
        self.setWindowTitle("Processing Parameters")
        self.ui.groupBox.setTitle("Rolling window")

        self._snapshot: _Snapshot | None = None

        self._setup_buttons()
        self._setup_widgets()

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

    @property
    def rate_widgets(self) -> list[QtWidgets.QWidget]:
        """The rate calculation inputs."""
        return [
            self.ui.rate_handle_incomplete,
            self.ui.rate_every,
            self.ui.rate_period,
        ]

    def _setup_buttons(self) -> None:
        # The tooltips of these buttons come from `help_texts.HELP_TEXTS`, keyed by attribute name.
        button_box = self.ui.buttonBox
        self.btn_run = button_box.addButton("Run", QtWidgets.QDialogButtonBox.ButtonRole.ApplyRole)
        self.btn_run.setIcon(QtGui.QIcon("://icons/Play.svg"))
        self.btn_run.setDefault(True)
        self.btn_run.clicked.connect(self._on_run_clicked)

        self.btn_restore_defaults = button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults)
        self.btn_restore_defaults.clicked.connect(self.restore_defaults)

    def _setup_widgets(self) -> None:
        # Signal Filter
        self.ui.sf_method.setAllowNone(True)
        self.ui.sf_method.set_enum_class(FilterMethod, doc_data=enum_doc)
        self.ui.sf_method.currentIndexChanged.connect(self._on_filter_method_changed)

        _setup_spinbox(self.ui.sf_lower_cutoff, 0, 100_000, 0.1, 0.5, 1)
        _setup_spinbox(self.ui.sf_upper_cutoff, 0, 100_000, 0.1, 8.0, 1)
        _setup_spinbox(self.ui.sf_order, 1, 10, 1, 3, 0)
        _setup_spinbox(self.ui.sf_window_size, 5, 1_000_000, 10, 100, 0)
        _setup_spinbox(self.ui.sf_powerline, 0, 100_000, 0.1, 50.0, 1)

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

        # Rate Calculation
        self.ui.rate_handle_incomplete.set_enum_class(IncompleteWindowMethod, doc_data=enum_doc)
        _setup_spinbox(self.ui.rate_period, 1, 10_000, 1, 60, 0)
        _setup_spinbox(self.ui.rate_every, 1, 600, 1, 10, 0)
        self.ui.rate_period.valueChanged.connect(self._emit_rate_params)
        self.ui.rate_every.valueChanged.connect(self._emit_rate_params)
        self.ui.rate_handle_incomplete.sig_current_enum_changed.connect(self._emit_rate_params)

        # The combo boxes were filled before their handlers were connected; bring the dependent inputs in line.
        self._on_filter_method_changed(self.ui.sf_method.currentIndex())
        self._on_std_method_changed(self.ui.std_method.currentIndex())
        self._on_peak_method_changed(self.ui.peak_method.currentIndex())

    # --- Opening, committing, reverting ------------------------------------------------------------------------------

    def open_tab(self, tab: QtWidgets.QWidget, preprocessing_enabled: bool = True) -> None:
        """
        Opens the dialog (window-modal) showing `tab`, one of `ui.tab_processing`, `ui.tab_peak`, `ui.tab_rate`.

        `preprocessing_enabled=False` disables the Preprocessing tab, for the case that a pipeline replaces the
        custom steps. Asking for that tab while it is disabled shows the Peak detection tab instead. The values at
        this moment are what Cancel restores.
        """
        tabs = self.ui.tab_widget_params
        processing_index = tabs.indexOf(self.ui.tab_processing)
        tabs.setTabEnabled(processing_index, preprocessing_enabled)
        tabs.setTabToolTip(processing_index, "" if preprocessing_enabled else PIPELINE_LOCK_TOOLTIP)
        if tab is self.ui.tab_processing and not preprocessing_enabled:
            tab = self.ui.tab_peak
        tabs.setCurrentWidget(tab)

        self._snapshot = self._take_snapshot()
        self.open()

    def _take_snapshot(self) -> _Snapshot:
        widgets = self.findChildren(QtWidgets.QWidget)
        return _Snapshot(
            combos={w: w.currentIndex() for w in widgets if isinstance(w, EnumComboBox)},
            checks={w: w.isChecked() for w in widgets if isinstance(w, QtWidgets.QCheckBox)},
            spins={w: w.value() for w in widgets if isinstance(w, DecimalSpinBox)},
        )

    def _restore(self, snapshot: _Snapshot) -> None:
        # Selecting "no method" resets the inputs that depend on the method, so the method combo boxes are restored
        # before the check boxes and spin boxes.
        for combo, index in snapshot.combos.items():
            combo.setCurrentIndex(index)
        for check, checked in snapshot.checks.items():
            check.setChecked(checked)
        for spin, value in snapshot.spins.items():
            spin.setValue(value)

    @QtCore.Slot()
    def _on_run_clicked(self) -> None:
        # A run uses the edits, so they are no longer something Cancel should take back.
        self._snapshot = self._take_snapshot()
        self.sig_run_requested.emit()

    @QtCore.Slot()
    def reject(self) -> None:
        """Cancel, Esc and the window's close button: restores the values of the last `open_tab` or Run, then closes."""
        if self._snapshot is not None:
            self._restore(self._snapshot)
        super().reject()

    @QtCore.Slot()
    def restore_defaults(self) -> None:
        """
        "Restore Defaults": resets the inputs of the visible tab. Does not touch the signal or the peaks.

        On the Peak detection tab only the inputs of the shown method page are reset; the method stays selected.
        """
        current = self.ui.tab_widget_params.currentWidget()
        if current is self.ui.tab_processing:
            targets: list[QtCore.QObject] = [self.ui.sf_method, self.ui.std_method, *self.sf_widgets, *self.std_widgets]
        elif current is self.ui.tab_peak:
            page = self.ui.stacked_widget_peak.currentWidget()
            targets = list(page.children()) if page is not None else []
        else:
            targets = list(self.rate_widgets)
        for target in targets:
            _restore_default(target)

    def set_peak_method(self, method: PeakDetectionAlgorithm) -> None:
        """Selects `method` on the Peak detection tab, as the dock does when a pipeline is chosen."""
        self.ui.peak_method.set_current_enum(method)

    def set_default_search_radius(self, samples: int) -> None:
        """
        Makes `samples` the value and the default of both local-extrema radius inputs.

        The tooltips quote the default, so the caller re-applies the help texts afterwards
        (`ParameterInputs.set_default_search_radius` does).
        """
        for spin in (self.ui.peak_localmax_radius, self.ui.peak_localmin_radius):
            spin.setProperty("defaultValue", samples)
            spin.setValue(samples)

    # --- Dependent inputs --------------------------------------------------------------------------------------------

    @QtCore.Slot()
    @QtCore.Slot(object)
    def _emit_rate_params(self, _value: object = None) -> None:
        self.sig_rate_params_changed.emit(self.get_rate_params())

    @QtCore.Slot(bool)
    def _on_rolling_window_toggled(self, checked: bool) -> None:
        self.ui.std_window_size.setEnabled(checked)

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

    # --- Reading the inputs ------------------------------------------------------------------------------------------

    def get_custom_processing_request(self) -> ProcessingRequest:
        """
        The Preprocessing tab as a `ProcessingRequest`: the selected filter, then the selected standardization.

        With neither selected the request is empty, which resets the signal to the raw one.
        """
        sf_method: FilterMethod | None = self.ui.sf_method.current_enum()
        std_method: StandardizationMethod | None = self.ui.std_method.current_enum()
        return ProcessingRequest(
            filter=self.get_filter_params(sf_method) if sf_method is not None else None,
            standardize=self.get_std_params(std_method) if std_method is not None else None,
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

    def get_peak_detection_request(self) -> PeakDetectionRequest | None:
        """The currently selected peak detection method and its parameters, or `None` if no method is selected."""
        peak_method: PeakDetectionAlgorithm | None = self.ui.peak_method.current_enum()
        if peak_method is None:
            return None
        return PeakDetectionRequest(method=peak_method, params=self.get_peak_detection_params(peak_method))

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
