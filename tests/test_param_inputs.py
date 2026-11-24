"""
Tests for the parameter dock (`ParameterInputs`) and its parameters dialog (`ParameterDialog`): the pipeline dropdown
selects the matching peak detector, "Custom" unlocks the edit button, one press of Run asks for processing and
detection together, and the dialog commits or reverts edits as its buttons promise.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from PySide6 import QtWidgets

from signal_viewer.enum_defs import (
    PIPELINE_PEAK_METHODS,
    FilterMethod,
    PeakDetectionAlgorithm,
    PreprocessPipeline,
    StandardizationMethod,
)
from signal_viewer.sv_widgets.dock_param_inputs import CUSTOM_PIPELINE_TEXT, ParameterInputs
from signal_viewer.type_defs import ProcessingRequest, RunRequest


@pytest.fixture
def inputs(qapp: QtWidgets.QApplication) -> Iterator[ParameterInputs]:
    widget = ParameterInputs()
    yield widget
    widget.dialog.close()
    widget.deleteLater()


def run_requests(inputs: ParameterInputs) -> list[RunRequest]:
    received: list[RunRequest] = []
    inputs.sig_run.connect(received.append)
    return received


def test_every_pipeline_has_a_peak_method() -> None:
    assert set(PIPELINE_PEAK_METHODS) == set(PreprocessPipeline)


def test_default_is_the_ppg_pipeline_with_its_detector(inputs: ParameterInputs) -> None:
    assert inputs.ui.pipeline.current_enum() is PreprocessPipeline.PPG_Elgendi
    assert inputs.dialog.ui.peak_method.current_enum() is PeakDetectionAlgorithm.PPG_Elgendi
    assert not inputs.ui.toolButton.isEnabled()


@pytest.mark.parametrize("pipeline", list(PreprocessPipeline), ids=lambda p: p.name)
def test_selecting_a_pipeline_selects_its_peak_method(inputs: ParameterInputs, pipeline: PreprocessPipeline) -> None:
    inputs.ui.pipeline.set_current_enum(None)
    inputs.ui.pipeline.set_current_enum(pipeline)

    assert inputs.dialog.ui.peak_method.current_enum() is PIPELINE_PEAK_METHODS[pipeline]
    assert not inputs.ui.toolButton.isEnabled()


def test_custom_entry_enables_the_edit_button_and_keeps_the_peak_method(inputs: ParameterInputs) -> None:
    combo = inputs.ui.pipeline
    combo.set_current_enum(PreprocessPipeline.ECG_NeuroKit)

    combo.set_current_enum(None)

    assert combo.currentText() == CUSTOM_PIPELINE_TEXT
    assert combo.current_enum() is None
    assert inputs.ui.toolButton.isEnabled()
    assert inputs.dialog.ui.peak_method.current_enum() is PeakDetectionAlgorithm.ECG_NeuroKit


def test_run_asks_for_the_pipeline_and_its_detector(inputs: ParameterInputs) -> None:
    received = run_requests(inputs)
    inputs.ui.pipeline.set_current_enum(PreprocessPipeline.ECG_BioSPPy)

    inputs.action_run.trigger()

    assert len(received) == 1
    request = received[0]
    assert request.processing == ProcessingRequest(pipeline=PreprocessPipeline.ECG_BioSPPy)
    assert request.detection is not None
    assert request.detection.method is PeakDetectionAlgorithm.ECG_Hamilton_2002
    assert request.detection.params is None


def test_run_uses_a_peak_method_chosen_after_the_pipeline(inputs: ParameterInputs) -> None:
    received = run_requests(inputs)
    inputs.ui.pipeline.set_current_enum(PreprocessPipeline.PPG_Elgendi)
    inputs.dialog.ui.peak_method.set_current_enum(PeakDetectionAlgorithm.LocalMaxima)
    inputs.dialog.ui.peak_localmax_radius.setValue(40)

    inputs.action_run.trigger()

    detection = received[0].detection
    assert detection is not None
    assert detection.method is PeakDetectionAlgorithm.LocalMaxima
    assert detection.params == {"search_radius": 40, "min_distance": 40}


def test_run_with_custom_carries_the_dialog_inputs(inputs: ParameterInputs) -> None:
    received = run_requests(inputs)
    ui = inputs.dialog.ui
    inputs.ui.pipeline.set_current_enum(None)
    ui.sf_method.set_current_enum(FilterMethod.Butterworth)
    ui.sf_lower_cutoff.setValue(1.5)
    ui.std_method.set_current_enum(StandardizationMethod.ZScore)

    inputs.action_run.trigger()

    processing = received[0].processing
    assert processing.pipeline is None
    assert processing.filter is not None
    assert processing.filter["method"] == FilterMethod.Butterworth
    assert processing.filter["lowcut"] == 1.5
    assert processing.standardize == {"method": StandardizationMethod.ZScore, "robust": False, "window_size": None}


def test_custom_inputs_are_ignored_and_kept_while_a_pipeline_is_selected(inputs: ParameterInputs) -> None:
    received = run_requests(inputs)
    ui = inputs.dialog.ui
    inputs.ui.pipeline.set_current_enum(None)
    ui.sf_method.set_current_enum(FilterMethod.Bessel)

    inputs.ui.pipeline.set_current_enum(PreprocessPipeline.PPG_Elgendi)
    inputs.action_run.trigger()

    assert received[0].processing == ProcessingRequest(pipeline=PreprocessPipeline.PPG_Elgendi)
    assert ui.sf_method.current_enum() is FilterMethod.Bessel


def test_run_with_custom_and_no_steps_resets_the_signal(inputs: ParameterInputs) -> None:
    received = run_requests(inputs)
    inputs.ui.pipeline.set_current_enum(None)

    inputs.action_run.trigger()

    assert received[0].processing == ProcessingRequest()


def test_peak_settings_opens_the_peak_tab_with_preprocessing_locked(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    tabs = dialog.ui.tab_widget_params
    inputs.ui.pipeline.set_current_enum(PreprocessPipeline.PPG_Elgendi)

    inputs.action_peak_settings.trigger()

    assert dialog.isVisible()
    assert tabs.currentWidget() is dialog.ui.tab_peak
    assert not tabs.isTabEnabled(tabs.indexOf(dialog.ui.tab_processing))
    assert tabs.isTabEnabled(tabs.indexOf(dialog.ui.tab_rate))


def test_peak_settings_leaves_preprocessing_editable_for_custom(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    tabs = dialog.ui.tab_widget_params
    inputs.ui.pipeline.set_current_enum(None)

    inputs.action_peak_settings.trigger()

    assert tabs.currentWidget() is dialog.ui.tab_peak
    assert tabs.isTabEnabled(tabs.indexOf(dialog.ui.tab_processing))


def test_edit_button_opens_the_preprocessing_tab(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    inputs.ui.pipeline.set_current_enum(None)

    inputs.ui.toolButton.click()

    assert dialog.isVisible()
    assert dialog.ui.tab_widget_params.currentWidget() is dialog.ui.tab_processing


def test_cancel_restores_the_values_at_open(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    ui = dialog.ui
    inputs.ui.pipeline.set_current_enum(None)
    ui.sf_method.set_current_enum(FilterMethod.Butterworth)
    ui.sf_lower_cutoff.setValue(2.0)
    dialog.open_tab(ui.tab_processing)

    ui.sf_method.set_current_enum(None)  # resets the cutoff to its default as a side effect
    ui.peak_method.set_current_enum(PeakDetectionAlgorithm.ECG_XQRS)
    ui.peak_ecg_emrich_accelerated.setChecked(False)
    ui.rate_every.setValue(25)
    dialog.reject()

    assert not dialog.isVisible()
    assert ui.sf_method.current_enum() is FilterMethod.Butterworth
    assert ui.sf_lower_cutoff.floatValue() == 2.0
    assert ui.peak_method.current_enum() is PeakDetectionAlgorithm.PPG_Elgendi
    assert ui.peak_ecg_emrich_accelerated.isChecked()
    assert ui.rate_every.intValue() == 10


def test_ok_keeps_the_edits(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    dialog.open_tab(dialog.ui.tab_peak, preprocessing_enabled=False)

    dialog.ui.peak_ppg_elgendi_mindelay.setValue(0.5)
    dialog.accept()

    assert not dialog.isVisible()
    assert dialog.ui.peak_ppg_elgendi_mindelay.floatValue() == 0.5


def test_dialog_run_emits_a_request_and_commits_the_edits(inputs: ParameterInputs) -> None:
    received = run_requests(inputs)
    dialog = inputs.dialog
    dialog.open_tab(dialog.ui.tab_peak, preprocessing_enabled=False)

    dialog.ui.peak_ppg_elgendi_mindelay.setValue(0.5)
    dialog.btn_run.click()

    assert dialog.isVisible()  # stays open for the next try
    detection = received[0].detection
    assert detection is not None and detection.params is not None
    assert dict(detection.params)["mindelay"] == 0.5

    # Cancel now only takes back what was edited after the run.
    dialog.ui.peak_ppg_elgendi_mindelay.setValue(0.9)
    dialog.reject()
    assert dialog.ui.peak_ppg_elgendi_mindelay.floatValue() == 0.5


def test_restore_defaults_resets_only_the_visible_tab(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    ui = dialog.ui
    ui.peak_method.set_current_enum(PeakDetectionAlgorithm.PPG_Elgendi)
    ui.peak_ppg_elgendi_mindelay.setValue(0.5)
    ui.peak_xqrs_radius.setValue(50)  # on another method page
    ui.rate_every.setValue(25)
    dialog.open_tab(ui.tab_peak)

    dialog.btn_restore_defaults.click()

    assert ui.peak_ppg_elgendi_mindelay.floatValue() == 0.3
    assert ui.peak_method.current_enum() is PeakDetectionAlgorithm.PPG_Elgendi
    assert ui.peak_xqrs_radius.intValue() == 50
    assert ui.rate_every.intValue() == 25

    ui.tab_widget_params.setCurrentWidget(ui.tab_rate)
    dialog.btn_restore_defaults.click()
    assert ui.rate_every.intValue() == 10


def test_restore_defaults_unchecks_the_rolling_window(inputs: ParameterInputs) -> None:
    dialog = inputs.dialog
    ui = dialog.ui
    inputs.ui.pipeline.set_current_enum(None)
    ui.std_method.set_current_enum(StandardizationMethod.ZScore)
    ui.std_rolling_window.setChecked(True)
    dialog.open_tab(ui.tab_processing)

    dialog.btn_restore_defaults.click()

    assert ui.std_method.current_enum() is None
    assert not ui.std_rolling_window.isChecked()
    assert not ui.std_window_size.isEnabled()


def test_rate_inputs_are_forwarded_from_the_dialog(inputs: ParameterInputs) -> None:
    received: list[dict[str, object]] = []
    inputs.sig_rate_params_changed.connect(received.append)

    inputs.dialog.ui.rate_period.setValue(30)

    assert received[-1]["sec_window_length"] == 30
    assert inputs.get_rate_params()["sec_window_length"] == 30


def test_set_default_search_radius_updates_value_default_and_tooltip(inputs: ParameterInputs) -> None:
    inputs.set_default_search_radius(250)

    for spin in (inputs.dialog.ui.peak_localmax_radius, inputs.dialog.ui.peak_localmin_radius):
        assert spin.intValue() == 250
        assert spin.property("defaultValue") == 250
        assert "Default 250 samples" in spin.toolTip()


def test_dialog_is_disabled_together_with_the_dock_widget(inputs: ParameterInputs) -> None:
    inputs.setEnabled(False)
    assert not inputs.dialog.isEnabled()
    inputs.setEnabled(True)
    assert inputs.dialog.isEnabled()
