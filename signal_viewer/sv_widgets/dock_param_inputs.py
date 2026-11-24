"""
The "Parameter Inputs" dock: a command bar, the pipeline dropdown and the way into the parameters dialog.

`ParameterInputs` owns the widgets compiled from `generated/param_inputs_new.ui` and one `ParameterDialog`, which
holds every other input. It translates button presses into one request object per action (`RunRequest`,
`RollingRateKwargs`) that it emits for `SVApp` to forward to the `DataController`. It never touches data itself.

Help texts of every input live in `signal_viewer.help_texts` and are applied at the end of `_setup_widgets`.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.enum_defs import PIPELINE_PEAK_METHODS, PreprocessPipeline
from signal_viewer.generated.ui_param_inputs_new import Ui_processingInputs
from signal_viewer.help_texts import apply_help_texts, enum_doc
from signal_viewer.sv_widgets.dlg_param_inputs import ParameterDialog
from signal_viewer.type_defs import PeakDetectionRequest, ProcessingRequest, RollingRateKwargs, RunRequest

CUSTOM_PIPELINE_TEXT = "Custom"
"""Label of the dropdown entry that stands for "no pipeline": the Preprocessing tab of the dialog is used instead."""

CUSTOM_PIPELINE_DOC = (
    "No ready-made pipeline. The filter and standardization chosen on the Preprocessing tab of the parameters dialog "
    "are applied instead; with neither chosen, the raw signal is used. Open the dialog with the button on the right."
)


class ParameterInputs(QtWidgets.QWidget):
    """
    The widget inside `InputsDock`: Run, Peak Settings, Clear Peaks and Reset Signal above the pipeline dropdown.

    Selecting a pipeline selects the peak detector it was made for (`PIPELINE_PEAK_METHODS`), so one press of Run
    produces a processed signal with peaks. The edit button next to the dropdown is enabled for the "Custom" entry
    only and opens the parameters dialog on the Preprocessing tab. "Peak Settings" opens the same dialog on the
    Peak detection tab whatever is selected; the Preprocessing tab is then disabled unless "Custom" is selected.

    The widget emits one signal per user action with everything the action needs, so `SVApp` never reads widgets.
    """

    # Each user action maps to exactly one signal carrying everything the action needs.
    sig_run = QtCore.Signal(object)  # RunRequest
    sig_reset_data = QtCore.Signal()
    sig_clear_peaks = QtCore.Signal()

    sig_rate_params_changed = QtCore.Signal(dict)  # RollingRateKwargs, emitted whenever a rate input changes

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_processingInputs()
        self.ui.setupUi(self)

        # A child, so it is disabled together with the dock and found by `findChildren` (help text tests).
        self.dialog = ParameterDialog(self)
        self.dialog.sig_run_requested.connect(self.run)
        self.dialog.sig_rate_params_changed.connect(self.sig_rate_params_changed)

        self._setup_actions()
        self._setup_widgets()

    def _setup_actions(self) -> None:
        # The tooltips of these actions come from `help_texts.HELP_TEXTS`, keyed by attribute name.
        self.action_run = QtGui.QAction(QtGui.QIcon.fromTheme("Play"), "Run", self)
        self.action_run.triggered.connect(self.run)

        self.action_peak_settings = QtGui.QAction(QtGui.QIcon.fromTheme("Options"), "Peak Settings", self)
        self.action_peak_settings.triggered.connect(self.edit_peak_settings)

        self.action_clear_peaks = QtGui.QAction(QtGui.QIcon.fromTheme("Eraser"), "Clear Peaks", self)
        self.action_clear_peaks.triggered.connect(self.clear_peaks)

        self.action_reset_data = QtGui.QAction(QtGui.QIcon.fromTheme("Broom"), "Reset Signal", self)
        self.action_reset_data.triggered.connect(self.reset_data)

        self.ui.cb_processing.addActions(
            [self.action_run, self.action_peak_settings, self.action_clear_peaks, self.action_reset_data]
        )

    def _setup_widgets(self) -> None:
        combo = self.ui.pipeline
        combo.setAllowNone(True)
        combo.set_enum_class(PreprocessPipeline, doc_data=enum_doc)
        # The "no selection" row of `EnumComboBox` is the custom entry; only its label and tooltip differ.
        combo.setItemText(0, CUSTOM_PIPELINE_TEXT)
        combo.setItemData(0, CUSTOM_PIPELINE_DOC, QtCore.Qt.ItemDataRole.ToolTipRole)
        combo.set_current_enum(PreprocessPipeline.PPG_Elgendi)
        combo.currentIndexChanged.connect(self._on_pipeline_changed)
        self._on_pipeline_changed(combo.currentIndex())

        self.ui.toolButton.clicked.connect(self.edit_custom_pipeline)

        # Last: the help texts read the ranges and defaults the dialog set.
        self.refresh_help_texts()

    def refresh_help_texts(self) -> None:
        """Re-applies tooltips and What's This texts. Call after a `defaultValue` property was changed."""
        apply_help_texts(self)

    def set_default_search_radius(self, samples: int) -> None:
        """Makes `samples` the value and default of the local-extrema radius inputs and updates their tooltips."""
        self.dialog.set_default_search_radius(samples)
        self.refresh_help_texts()  # the tooltips quote the default

    @QtCore.Slot(int)
    def _on_pipeline_changed(self, index: int) -> None:
        # A pipeline replaces the custom steps (see `ProcessingRequest`), so there is nothing to edit for it, and it
        # brings its own detector. The custom inputs keep their values for the next time "Custom" is selected.
        pipeline: PreprocessPipeline | None = self.ui.pipeline.current_enum()
        self.ui.toolButton.setEnabled(pipeline is None)
        if pipeline is not None:
            self.dialog.set_peak_method(PIPELINE_PEAK_METHODS[pipeline])

    @QtCore.Slot()
    def edit_custom_pipeline(self) -> None:
        """The edit button: opens the parameters dialog on the Preprocessing tab. Only reachable with "Custom"."""
        self.dialog.open_tab(
            self.dialog.ui.tab_processing, preprocessing_enabled=self.ui.pipeline.current_enum() is None
        )

    @QtCore.Slot()
    def edit_peak_settings(self) -> None:
        """
        "Peak Settings": opens the parameters dialog on the Peak detection tab.

        While a pipeline is selected the Preprocessing tab is disabled, so only detection and rate inputs can change.
        """
        self.dialog.open_tab(self.dialog.ui.tab_peak, preprocessing_enabled=self.ui.pipeline.current_enum() is None)

    @QtCore.Slot()
    def reset_data(self) -> None:
        """Asks for the raw signal back ("Reset Signal")."""
        self.sig_reset_data.emit()

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        """Asks for all peaks to be removed ("Clear Peaks")."""
        self.sig_clear_peaks.emit()

    @QtCore.Slot()
    def run(self) -> None:
        """ "Run" (dock and dialog): emits a `RunRequest` for the selected pipeline or custom steps and the detector."""
        self.sig_run.emit(self.get_run_request())

    def get_processing_request(self) -> ProcessingRequest:
        """The selected pipeline, or the custom steps of the dialog when "Custom" is selected."""
        pipeline: PreprocessPipeline | None = self.ui.pipeline.current_enum()
        if pipeline is not None:
            return ProcessingRequest(pipeline=pipeline)
        return self.dialog.get_custom_processing_request()

    def get_run_request(self) -> RunRequest:
        """Everything one press of "Run" does: the processing, then the detection with the selected method."""
        return RunRequest(processing=self.get_processing_request(), detection=self.get_peak_detection_request())

    def get_peak_detection_request(self) -> PeakDetectionRequest | None:
        """The currently selected peak detection method and its parameters, or `None` if no method is selected."""
        return self.dialog.get_peak_detection_request()

    def get_rate_params(self) -> RollingRateKwargs:
        """The rate tab inputs as keyword arguments for `section.compute_rate_rolling`."""
        return self.dialog.get_rate_params()


class InputsDock(QtWidgets.QDockWidget):
    """
    Dock window holding `ParameterInputs`. Shown on the Graph page only; disabled while the active section is
    locked or is the base section (`SVApp._update_lock_dependent_states`).
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Parameter Inputs", parent=parent)
        self.setObjectName("DockWidgetParameterInputs")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWindowIcon(QtGui.QIcon.fromTheme("Options"))
        self.toggleViewAction().setIcon(QtGui.QIcon.fromTheme("Options"))
        self.toggleViewAction().setToolTip("Show or hide the Parameter Inputs dock")

        self.ui = ParameterInputs()
        self.setWidget(self.ui)
