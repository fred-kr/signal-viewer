from PySide6 import QtCore, QtDesigner, QtGui, QtWidgets

from pyside_widgets._utils import get_text_color


class ColorPickerButton(QtWidgets.QPushButton):
    """
    A button that opens a color picker dialog when clicked.
    """

    sig_color_changed = QtCore.Signal(QtGui.QColor)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        color: QtGui.QColor | None = None,
        show_alpha: bool = False,
        show_icon: bool = True,
        show_text: bool = True,
    ) -> None:
        super().__init__(parent)

        self._default_color = super().palette().color(QtGui.QPalette.ColorRole.Button)
        self._color = color or self._default_color
        self._show_alpha = show_alpha
        self._show_icon = show_icon
        self._show_text = show_text

        self.set_color(self._color)
        self.pressed.connect(self._on_clicked)

    @property
    def text_fmt(self) -> QtGui.QColor.NameFormat:
        """Returns the appropriate color name format based on the visibility of the alpha channel."""
        return QtGui.QColor.NameFormat.HexArgb if self._show_alpha else QtGui.QColor.NameFormat.HexRgb

    def showAlphaChannel(self) -> bool:
        """Whether to show the alpha channel in the color picker."""
        return self._show_alpha

    def setShowAlphaChannel(self, value: bool) -> None:
        """Setter of property `showAlphaChannel`."""
        self._show_alpha = value
        self.set_color(self._color)

    def showAsIcon(self) -> bool:
        """Whether to show the current color as an icon or as the button background color."""
        return self._show_icon

    def setShowAsIcon(self, value: bool) -> None:
        """Setter of property `showAsIcon`."""
        self._show_icon = value
        self.set_color(self._color)

    def showText(self) -> bool:
        """Whether to show the current color's name in Hex(A)RGB format as the button text."""
        return self._show_text

    def setShowText(self, value: bool) -> None:
        """Setter of property `showText`."""
        self._show_text = value
        self.set_color(self._color)

    def set_color(self, color: QtGui.QColor) -> None:
        """Sets the current color of the button.

        Emits `sig_color_changed` if the color actually changes.

        Args:
            color: The new color to set.
        """
        if not color.isValid():
            return

        if color != self._color:
            self._color = color
            self.sig_color_changed.emit(self._color)

        if self._show_text:
            self.setText(self._color.name(self.text_fmt))
        else:
            self.setText("")

        if self._show_icon:
            self.setStyleSheet("")
            icon = QtGui.QPixmap(self.iconSize())
            icon.fill(self._color)
            self.setIcon(icon)
        else:
            self.setIcon(QtGui.QIcon())
            text_color = get_text_color(self._color)
            self.setStyleSheet(
                f"ColorPickerButton {{ background-color: {self._color.name()}; color: {text_color.name()}; }}"
            )

    def color(self) -> QtGui.QColor:
        return self._color

    @QtCore.Slot()
    def _on_clicked(self) -> None:
        """Launches a color selection dialog when the button is clicked.

        Allows the user to choose a new color with optional alpha channel visibility based on configuration.
        """
        if self._show_alpha:
            new_color = QtWidgets.QColorDialog.getColor(
                self._color, self, options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel
            )
        else:
            new_color = QtWidgets.QColorDialog.getColor(self._color, self)
        self.set_color(new_color)

    showAlphaChannel = QtCore.Property(bool, showAlphaChannel, setShowAlphaChannel)  # type: ignore
    showAsIcon = QtCore.Property(bool, showAsIcon, setShowAsIcon)  # type: ignore
    showText = QtCore.Property(bool, showText, setShowText)  # type: ignore


DOM_XML = """
<ui language='c++'>
    <widget class='ColorPickerButton' name='colorPickerButton'>
        <property name='showAlphaChannel'>
            <bool>false</bool>
        </property>
        <property name='showAsIcon'>
            <bool>true</bool>
        </property>
        <property name='showText'>
            <bool>false</bool>
        </property>
    </widget>
</ui>
"""


class ColorPickerButtonPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def createWidget(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        return ColorPickerButton(parent=parent)

    def domXml(self) -> str:
        return DOM_XML

    def group(self) -> str:
        return ""

    def icon(self) -> QtGui.QIcon:
        return QtGui.QIcon()

    def includeFile(self) -> str:
        return __name__

    def initialize(self, core: QtDesigner.QDesignerFormEditorInterface) -> None:
        if self._initialized:
            return

        self._initialized = True

    def isContainer(self) -> bool:
        return False

    def isInitialized(self) -> bool:
        return self._initialized

    def name(self) -> str:
        return "ColorPickerButton"

    def toolTip(self) -> str:
        return "Select a color using a color picker dialog."

    def whatsThis(self) -> str:
        return self.toolTip()
