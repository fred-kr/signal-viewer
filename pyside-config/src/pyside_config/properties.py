import decimal

import attrs
from PySide6 import QtWidgets, QtGui

SETTER_KEY = "__setter"


@attrs.define
class WidgetPropertiesBase[W: QtWidgets.QWidget | QtGui.QAction]:
    """
    Base class for widget properties.
    """

    styleSheet: str | None = attrs.field(default="", metadata={SETTER_KEY: "setStyleSheet"})

    def apply_to_widget(self, widget: W) -> None:
        """
        Applies the current values of the class attributes to the specified widget.

        This method iterates through the fields of the class and sets the corresponding properties on the provided
        widget, using defined setter methods.

        Args:
            widget (W): The widget to which the attribute values will be applied.
        """
        for field in attrs.fields(self.__class__):
            property_value = getattr(self, field.name)
            if field.name == "styleSheet" and property_value == "":  # allow using None to clear a style sheet
                continue
            getattr(widget, field.metadata[SETTER_KEY])(property_value)


@attrs.define
class SpinBoxProperties[T: int | float | decimal.Decimal](WidgetPropertiesBase[QtWidgets.QAbstractSpinBox]):
    minimum: T = attrs.field(default=0, metadata={SETTER_KEY: "setMinimum"})
    maximum: T = attrs.field(default=1_000_000, metadata={SETTER_KEY: "setMaximum"})
    singleStep: T = attrs.field(default=1, metadata={SETTER_KEY: "setSingleStep"})
    prefix: str | None = attrs.field(default=None, metadata={SETTER_KEY: "setPrefix"})
    suffix: str | None = attrs.field(default=None, metadata={SETTER_KEY: "setSuffix"})
    hasFrame: bool = attrs.field(default=False, metadata={SETTER_KEY: "setFrame"})


@attrs.define
class DecimalSpinBoxProperties[T: float | decimal.Decimal](SpinBoxProperties[T]):
    decimals: int = attrs.field(default=2, metadata={SETTER_KEY: "setDecimals"})


@attrs.define
class LineEditProperties(WidgetPropertiesBase[QtWidgets.QLineEdit]):
    clearButtonEnabled: bool = attrs.field(default=True, converter=bool, metadata={SETTER_KEY: "setClearButtonEnabled"})
    completer: QtWidgets.QCompleter | None = attrs.field(default=None, metadata={SETTER_KEY: "setCompleter"})
    hasFrame: bool = attrs.field(default=False, metadata={SETTER_KEY: "setFrame"})


@attrs.define
class ComboBoxProperties(WidgetPropertiesBase[QtWidgets.QComboBox]):
    isEditable: bool = attrs.field(default=False, metadata={SETTER_KEY: "setEditable"})
    hasFrame: bool = attrs.field(default=False, metadata={SETTER_KEY: "setFrame"})


@attrs.define
class CheckBoxProperties(WidgetPropertiesBase[QtWidgets.QCheckBox]):
    isTristate: bool = attrs.field(default=False, metadata={SETTER_KEY: "setTristate"})
