import decimal
import enum
from collections.abc import Callable, Sequence
from operator import attrgetter, methodcaller
from typing import TYPE_CHECKING, Any, Generic, NamedTuple, ParamSpec, TypedDict, TypeVar, Union, Unpack

import attrs
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import DecimalSpinBox, EnumComboBox

if TYPE_CHECKING:
    from pyside_config.properties import WidgetPropertiesBase

type WidgetOrAction = QtWidgets.QWidget | QtGui.QAction

P = ParamSpec("P")
T_Value = TypeVar("T_Value")
T_Editor = TypeVar("T_Editor", bound=WidgetOrAction, covariant=True)
_ValueChanged = Callable[[T_Editor], QtCore.SignalInstance]
_ValueGetter = Callable[[T_Editor], T_Value]
_ValueSetter = Callable[[T_Editor, T_Value], None]


# QComboBox
def _combo_box_updated(self: QtWidgets.QComboBox) -> QtCore.SignalInstance:
    return self.currentIndexChanged


def _combo_box_getter(self: QtWidgets.QComboBox) -> Any:
    return self.currentData()


def _combo_box_setter(self: QtWidgets.QComboBox, value: Any) -> None:
    self.setCurrentIndex(self.findData(value))


# EnumComboBox
def _enum_combo_box_updated[E: enum.Enum](self: EnumComboBox[E]) -> QtCore.SignalInstance:
    return self.sig_current_enum_changed


def _enum_combo_box_getter[E: enum.Enum](self: EnumComboBox[E]) -> E | None:
    return self.current_enum()


def _enum_combo_box_setter[E: enum.Enum](self: EnumComboBox[E], value: E) -> None:
    self.set_current_enum(value)


# QSpinBox
def _spin_box_updated(self: QtWidgets.QSpinBox) -> QtCore.SignalInstance:
    return self.valueChanged


def _spin_box_getter(self: QtWidgets.QSpinBox) -> int:
    return self.value()


def _spin_box_setter(self: QtWidgets.QSpinBox, value: int) -> None:
    self.setValue(value)


# QDoubleSpinBox
def _double_spin_box_updated(self: QtWidgets.QDoubleSpinBox) -> QtCore.SignalInstance:
    return self.valueChanged


def _double_spin_box_getter(self: QtWidgets.QDoubleSpinBox) -> float:
    return self.value()


def _double_spin_box_setter(self: QtWidgets.QDoubleSpinBox, value: float) -> None:
    self.setValue(value)


# DecimalSpinBox
def _decimal_spin_box_updated(self: DecimalSpinBox) -> QtCore.SignalInstance:
    return self.valueChanged


def _decimal_spin_box_getter(self: DecimalSpinBox) -> decimal.Decimal:
    return self.value()


def _decimal_spin_box_setter(self: DecimalSpinBox, value: decimal.Decimal) -> None:
    self.setValue(value)


# QSlider
def _slider_updated(self: QtWidgets.QSlider) -> QtCore.SignalInstance:
    return self.valueChanged


def _slider_getter(self: QtWidgets.QSlider) -> int:
    return self.value()


def _slider_setter(self: QtWidgets.QSlider, value: int) -> None:
    self.setValue(value)


# QCheckBox
def _check_box_updated(self: QtWidgets.QCheckBox) -> QtCore.SignalInstance:
    return self.stateChanged


def _check_box_getter(self: QtWidgets.QCheckBox) -> bool:
    return self.isChecked()


def _check_box_setter(self: QtWidgets.QCheckBox, value: bool) -> None:
    self.setChecked(value)


# QAction
def _action_updated(self: QtGui.QAction) -> QtCore.SignalInstance:
    return self.toggled


def _action_getter(self: QtGui.QAction) -> bool:
    return self.isChecked()


def _action_setter(self: QtGui.QAction, value: bool) -> None:
    self.setChecked(value)


# QPushButton
def _push_button_updated(self: QtWidgets.QPushButton) -> QtCore.SignalInstance:
    return self.clicked


def _push_button_getter(self: QtWidgets.QPushButton) -> bool:
    return self.isChecked()


def _push_button_setter(self: QtWidgets.QPushButton, value: bool) -> None:
    self.setChecked(value)


# QLineEdit
def _line_edit_updated(self: QtWidgets.QLineEdit) -> QtCore.SignalInstance:
    return self.textChanged


def _line_edit_getter(self: QtWidgets.QLineEdit) -> str:
    return self.text()


def _line_edit_setter(self: QtWidgets.QLineEdit, value: str) -> None:
    self.setText(value)


class EditorHooks(NamedTuple):
    """
    A data structure that holds references to key editor interactions.

    Attributes:
        value_changed (_ValueChanged): A callable that returns the signal instance which emits when the value in the editor changes.
        value_getter (_ValueGetter): A callable that retrieves the current value from the editor widge
        value_setter (_ValueSetter): A callable that sets a new value to the editor widge
    """

    value_changed: _ValueChanged[...]
    value_getter: _ValueGetter[..., ...]
    value_setter: _ValueSetter[..., ...]

    @classmethod
    def from_names(cls, value_changed: str, value_getter: str, value_setter: str) -> "EditorHooks":
        """
        Creates an `EditorHooks` instance using attribute and method names.

        Args:
            value_changed (str): The attribute name for the signal indicating a value change.
                Typically, this will be a PySide signal, such as `valueChanged`.
            value_getter (str): The method name for retrieving the current value from the editor widge
                For example, `text()` for a line edit widge
            value_setter (str): The method name for setting a new value on the editor widge
                For example, `setText()` for a line edit widge

        Returns:
            EditorHooks: An instance of `EditorHooks` that can be used to attach behaviors to the editor widge

        Example:
            ```python
            hooks = EditorHooks.from_names("valueChanged", "value", "setValue")
            ```
        """
        return cls(
            attrgetter(value_changed),
            methodcaller(value_getter),
            lambda editor, value: methodcaller(value_setter, value)(editor),
        )


DEFAULT_EDITORS: dict[type[WidgetOrAction], EditorHooks] = {
    DecimalSpinBox: EditorHooks(_decimal_spin_box_updated, _decimal_spin_box_getter, _decimal_spin_box_setter),
    EnumComboBox: EditorHooks(_enum_combo_box_updated, _enum_combo_box_getter, _enum_combo_box_setter),
    QtGui.QAction: EditorHooks(_action_updated, _action_getter, _action_setter),
    QtWidgets.QCheckBox: EditorHooks(_check_box_updated, _check_box_getter, _check_box_setter),
    QtWidgets.QComboBox: EditorHooks(_combo_box_updated, _combo_box_getter, _combo_box_setter),
    QtWidgets.QDoubleSpinBox: EditorHooks(_double_spin_box_updated, _double_spin_box_getter, _double_spin_box_setter),
    QtWidgets.QLineEdit: EditorHooks(_line_edit_updated, _line_edit_getter, _line_edit_setter),
    QtWidgets.QPushButton: EditorHooks(_push_button_updated, _push_button_getter, _push_button_setter),
    QtWidgets.QSlider: EditorHooks(_slider_updated, _slider_getter, _slider_setter),
    QtWidgets.QSpinBox: EditorHooks(_spin_box_updated, _spin_box_getter, _spin_box_setter),
}


def _to_editor_hooks(value: EditorHooks | tuple[str, str, str] | None) -> EditorHooks | None:
    if isinstance(value, EditorHooks) or value is None:
        return value
    return EditorHooks.from_names(*value)


class EditorData(NamedTuple, Generic[P, T_Editor]):
    """
    Information required to create an editor widget for a config entry.
    """

    factory: Callable[P, T_Editor]
    hooks: EditorHooks
    title: str
    description: str | None = None
    properties: "WidgetPropertiesBase[T_Editor] | None" = None
    icon: QtGui.QIcon | None = None

    # @overload
    # def create_widget(self, parent: QtWidgets.QWidget | None = ...) -> T_Editor: ...
    # @overload
    # def create_widget(self, *args: P.args, **kwargs: P.kwargs) -> T_Editor: ...
    # def create_widget(self, *args, **kwargs) -> T_Editor:
    #     w = self.widget_factory(*args, **kwargs)
    #     if self.widget_properties is not None:
    #         self.widget_properties.apply_to_widget(w)

    #     return w


EDITOR_KEY = "editor_data"

_EqOrderType = Union[bool, Callable[[Any], Any]]
_ValidatorType = Callable[[Any, "attrs.Attribute[T_Value]", T_Value], Any]
_ConverterType = Callable[[Any], Any]
_ReprType = Callable[[Any], str]
_ReprArgType = Union[bool, _ReprType]
_ValidatorArgType = Union[_ValidatorType[T_Value], Sequence[_ValidatorType[T_Value]]]


class FieldArgs(TypedDict, Generic[T_Value], total=False):
    validator: _ValidatorArgType[T_Value] | None
    repr: _ReprArgType
    hash: bool | None
    init: bool
    converter: _ConverterType | attrs.Converter[Any, T_Value] | None
    factory: Callable[[], T_Value] | None
    kw_only: bool
    eq: _EqOrderType | None
    order: _EqOrderType | None


def config_entry(
    *,
    default: T_Value = attrs.NOTHING,
    editor_data: EditorData[P, T_Editor] | None = None,
    **kwargs: Unpack[FieldArgs[T_Value]],
) -> T_Value:
    metadata = {EDITOR_KEY: editor_data}
    return attrs.field(default=default, metadata=metadata, **kwargs)
