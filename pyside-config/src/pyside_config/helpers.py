import decimal
from collections.abc import Callable
from typing import TypedDict, Unpack

from PySide6 import QtGui, QtWidgets
from pyside_widgets import DecimalSpinBox

from pyside_config._pyside_config import EditorWidgetInfo
from pyside_config.properties import (
    CheckBoxProperties,
    ComboBoxProperties,
    DecimalSpinBoxProperties,
    LineEditProperties,
    SpinBoxProperties,
)


class LineEditKwargs(TypedDict, total=False):
    clearButtonEnabled: bool
    completer: QtWidgets.QCompleter | None
    hasFrame: bool


class CheckBoxKwargs(TypedDict, total=False):
    isTristate: bool


class _CommonSpinBoxKwargs(TypedDict, total=False):
    prefix: str
    suffix: str
    hasFrame: bool


class IntSpinBoxKwargs(_CommonSpinBoxKwargs, total=False):
    minimum: int
    maximum: int
    singleStep: int


class DoubleSpinBoxKwargs(_CommonSpinBoxKwargs, total=False):
    minimum: float
    maximum: float
    singleStep: float
    decimals: int


class DecimalSpinBoxKwargs(_CommonSpinBoxKwargs, total=False):
    minimum: decimal.Decimal
    maximum: decimal.Decimal
    singleStep: decimal.Decimal
    decimals: int


class ComboBoxKwargs(TypedDict, total=False):
    isEditable: bool
    hasFrame: bool


def make_line_edit_info(
    label: str,
    widget_factory: Callable[..., QtWidgets.QLineEdit] = QtWidgets.QLineEdit,
    sig_value_changed: str = "textChanged",
    set_value_method: str = "setText",
    icon: QtGui.QIcon | None = None,
    **kwargs: Unpack[LineEditKwargs],
) -> EditorWidgetInfo[QtWidgets.QLineEdit]:
    return EditorWidgetInfo(
        label=label,
        widget_factory=widget_factory,
        sig_value_changed=sig_value_changed,
        set_value_method=set_value_method,
        icon=icon,
        widget_properties=LineEditProperties(**kwargs),
    )


def make_check_box_info(
    label: str,
    widget_factory: Callable[..., QtWidgets.QCheckBox] = QtWidgets.QCheckBox,
    sig_value_changed: str = "toggled",
    set_value_method: str = "setChecked",
    icon: QtGui.QIcon | None = None,
    **kwargs: Unpack[CheckBoxKwargs],
) -> EditorWidgetInfo[QtWidgets.QCheckBox]:
    return EditorWidgetInfo(
        label=label,
        widget_factory=widget_factory,
        sig_value_changed=sig_value_changed,
        set_value_method=set_value_method,
        icon=icon,
        widget_properties=CheckBoxProperties(**kwargs),
    )


def make_spin_box_info(
    label: str,
    widget_factory: Callable[..., QtWidgets.QSpinBox] = QtWidgets.QSpinBox,
    sig_value_changed: str = "valueChanged",
    set_value_method: str = "setValue",
    icon: QtGui.QIcon | None = None,
    **kwargs: Unpack[IntSpinBoxKwargs],
) -> EditorWidgetInfo[QtWidgets.QSpinBox]:
    return EditorWidgetInfo(
        label=label,
        widget_factory=widget_factory,
        sig_value_changed=sig_value_changed,
        set_value_method=set_value_method,
        icon=icon,
        widget_properties=SpinBoxProperties(**kwargs),
    )


def make_double_spin_box_info(
    label: str,
    widget_factory: Callable[..., QtWidgets.QDoubleSpinBox] = QtWidgets.QDoubleSpinBox,
    sig_value_changed: str = "valueChanged",
    set_value_method: str = "setValue",
    icon: QtGui.QIcon | None = None,
    **kwargs: Unpack[DoubleSpinBoxKwargs],
) -> EditorWidgetInfo[QtWidgets.QDoubleSpinBox]:
    return EditorWidgetInfo(
        label=label,
        widget_factory=widget_factory,
        sig_value_changed=sig_value_changed,
        set_value_method=set_value_method,
        icon=icon,
        widget_properties=DecimalSpinBoxProperties(**kwargs),
    )


def make_decimal_spin_box_info(
    label: str,
    widget_factory: Callable[..., DecimalSpinBox] = DecimalSpinBox,
    sig_value_changed: str = "valueChanged",
    set_value_method: str = "setValue",
    icon: QtGui.QIcon | None = None,
    **kwargs: Unpack[DecimalSpinBoxKwargs],
) -> EditorWidgetInfo[DecimalSpinBox]:
    return EditorWidgetInfo(
        label=label,
        widget_factory=widget_factory,
        sig_value_changed=sig_value_changed,
        set_value_method=set_value_method,
        icon=icon,
        widget_properties=DecimalSpinBoxProperties(**kwargs),
    )


def make_combo_box_info(
    label: str,
    widget_factory: Callable[..., QtWidgets.QComboBox] = QtWidgets.QComboBox,
    sig_value_changed: str = "currentIndexChanged",
    set_value_method: str = "setCurrentIndex",
    icon: QtGui.QIcon | None = None,
    **kwargs: Unpack[ComboBoxKwargs],
) -> EditorWidgetInfo[QtWidgets.QComboBox]:
    return EditorWidgetInfo(
        label=label,
        widget_factory=widget_factory,
        sig_value_changed=sig_value_changed,
        set_value_method=set_value_method,
        icon=icon,
        widget_properties=ComboBoxProperties(**kwargs),
    )
