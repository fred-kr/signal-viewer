"""
Tests for the help texts of the parameter dock and the documented enums: every input has a tooltip and a What's
This text, every `HELP_TEXTS` entry names a real widget and has a row on the reference page, the default/range
trailer quotes the widget, and every `DocumentedStrEnum` member describes itself.
"""

from __future__ import annotations

import inspect

import pytest
from PySide6 import QtWidgets
from pyside_widgets import DecimalSpinBox, EnumComboBox

from signal_viewer import enum_defs
from signal_viewer.enum_defs import DocumentedStrEnum, PeakDetectionAlgorithm
from signal_viewer.help_texts import HELP_TEXTS, PARAMETER_REFERENCE_PAGE, anchor_for, enum_doc
from signal_viewer.sv_site import DOCDIR
from signal_viewer.sv_widgets.dock_param_inputs import ParameterInputs

INPUT_TYPES = (DecimalSpinBox, EnumComboBox, QtWidgets.QCheckBox)


@pytest.fixture(scope="module")
def inputs(qapp: QtWidgets.QApplication) -> ParameterInputs:
    return ParameterInputs()


def input_widgets(inputs: ParameterInputs) -> list[QtWidgets.QWidget]:
    return [w for w in inputs.findChildren(QtWidgets.QWidget) if isinstance(w, INPUT_TYPES)]


def test_every_input_has_tooltip_and_whats_this(inputs: ParameterInputs) -> None:
    missing = [w.objectName() for w in input_widgets(inputs) if not (w.toolTip() and w.whatsThis())]
    assert not missing


def test_every_input_has_a_help_text(inputs: ParameterInputs) -> None:
    names = {w.objectName() for w in input_widgets(inputs)}
    assert names <= set(HELP_TEXTS), f"inputs without a HELP_TEXTS entry: {sorted(names - set(HELP_TEXTS))}"


def test_every_help_text_names_a_widget_or_action(inputs: ParameterInputs) -> None:
    unknown = [key for key in HELP_TEXTS if not (hasattr(inputs.ui, key) or hasattr(inputs, key))]
    assert not unknown


def test_reference_page_has_a_row_for_every_help_text() -> None:
    html = (DOCDIR / PARAMETER_REFERENCE_PAGE).read_text(encoding="utf-8")
    missing = [key for key in HELP_TEXTS if f'name="{anchor_for(key)}"' not in html]
    assert not missing


def test_whats_this_links_into_the_user_guide(inputs: ParameterInputs) -> None:
    for widget in input_widgets(inputs):
        assert f'href="help:{PARAMETER_REFERENCE_PAGE}#{anchor_for(widget.objectName())}"' in widget.whatsThis()


def test_spin_box_tooltip_quotes_default_range_and_unit(inputs: ParameterInputs) -> None:
    spin = inputs.ui.sf_lower_cutoff
    assert "Default 0.5 Hz" in spin.toolTip()
    assert "range 0.0 to 100000.0 Hz" in spin.toolTip()
    assert spin.suffix() == " Hz"
    assert spin.floatValue() == 0.5  # the suffix does not disturb the value


def test_sentinel_minimum_is_explained(inputs: ParameterInputs) -> None:
    assert "minimum value stands for" in inputs.ui.sf_window_size.toolTip()


def test_label_shares_the_tooltip(inputs: ParameterInputs) -> None:
    parent = inputs.ui.sf_lower_cutoff.parentWidget()
    assert parent is not None
    layout = parent.layout()
    assert isinstance(layout, QtWidgets.QFormLayout)
    label = layout.labelForField(inputs.ui.sf_lower_cutoff)
    assert label is not None
    assert label.toolTip() == inputs.ui.sf_lower_cutoff.toolTip()
    # Explicit label name in `HelpText`; the combo box itself appends the description of the selected member.
    assert inputs.ui.sf_pipeline.toolTip().startswith(inputs.ui.label.toolTip())
    assert inputs.ui.sf_pipeline.toolTip() != inputs.ui.label.toolTip()


def test_combo_box_tooltip_follows_selection(inputs: ParameterInputs) -> None:
    combo = inputs.ui.peak_method
    combo.set_current_enum(PeakDetectionAlgorithm.ECG_XQRS)
    assert enum_doc(PeakDetectionAlgorithm.ECG_XQRS) in combo.toolTip()
    combo.set_current_enum(PeakDetectionAlgorithm.LocalMaxima)
    assert enum_doc(PeakDetectionAlgorithm.LocalMaxima) in combo.toolTip()


def test_refresh_is_idempotent(inputs: ParameterInputs) -> None:
    before = {w.objectName(): (w.toolTip(), w.whatsThis()) for w in input_widgets(inputs)}
    inputs.refresh_help_texts()
    after = {w.objectName(): (w.toolTip(), w.whatsThis()) for w in input_widgets(inputs)}
    assert before == after


def test_refresh_picks_up_a_changed_default(inputs: ParameterInputs) -> None:
    spin = inputs.ui.peak_localmax_radius
    spin.setProperty("defaultValue", 250)
    inputs.refresh_help_texts()
    assert "Default 250 samples" in spin.toolTip()


def test_butterworth_zi_enables_cutoffs_and_order(inputs: ParameterInputs) -> None:
    inputs.ui.sf_pipeline.set_current_enum(None)
    inputs.ui.sf_method.set_current_enum(enum_defs.FilterMethod.ButterworthZI)
    assert inputs.ui.sf_lower_cutoff.isEnabled()
    assert inputs.ui.sf_order.isEnabled()
    assert not inputs.ui.sf_window_size.isEnabled()
    assert not inputs.ui.sf_powerline.isEnabled()


def documented_enums() -> list[type[DocumentedStrEnum]]:
    return [
        obj
        for obj in vars(enum_defs).values()
        if isinstance(obj, type) and issubclass(obj, DocumentedStrEnum) and obj is not DocumentedStrEnum
    ]


@pytest.mark.parametrize("enum_class", documented_enums(), ids=lambda cls: cls.__name__)
def test_documented_enum_members_describe_themselves(enum_class: type[DocumentedStrEnum]) -> None:
    class_doc = inspect.getdoc(enum_class)
    for member in enum_class:
        doc = enum_doc(member)
        assert doc, f"{enum_class.__name__}.{member.name} has no description"
        assert doc != class_doc, f"{enum_class.__name__}.{member.name} repeats the class docstring"
        assert "\n" not in doc, "member descriptions are single paragraphs"


def test_documented_enum_values_still_round_trip() -> None:
    assert enum_defs.FilterMethod("butterworth_zi") is enum_defs.FilterMethod.ButterworthZI
    assert str(enum_defs.PreprocessPipeline.ECG_Emrich_2023) == "vg"
    assert ".arrow" in enum_defs.InputFileFormat
