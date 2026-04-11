import typing as t

from PySide6 import QtCore, QtDesigner, QtGui, QtWidgets

from ._style_sheets import CARD_STYLE_SHEET
from ._utils import NOTHING, is_dark_theme


class PlaceholderWidget(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.setLineWidth(1)

        self.label = QtWidgets.QLabel(self)
        self.label.setText("Placeholder")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addWidget(self.label)

        self.setLayout(self._layout)

    def setPlaceholderText(self, text: str) -> None:
        self.label.setText(text)


class SettingCard(QtWidgets.QFrame):
    """
    A card widget with an icon, title, and text.

    Pretty much taken 1:1 from `qfluentwidgets.SettingCard`, but with some minor tweaks (also to avoid dependency on the
    entire `qfluentwidgets` package).
    """

    sig_reset_clicked = QtCore.Signal()

    def __init__(
        self,
        title: str = "",
        editor_widget: QtWidgets.QWidget | None = None,
        default_value: t.Any | None = NOTHING,
        set_value_name: str | None = None,
        description: str = "",
        icon: QtGui.QIcon | None = None,
        reset_button: bool = True,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.p_title = title
        self.p_description = description
        self.p_icon = icon or QtGui.QIcon()
        self.p_icon_size = QtCore.QSize(16, 16)
        self.p_reset_button = reset_button

        self._title_label = QtWidgets.QLabel(self.p_title, self)
        self._description_label = QtWidgets.QLabel(self.p_description, self)
        self._icon_label = QtWidgets.QLabel(self)
        self.editor_widget = editor_widget or PlaceholderWidget()
        self._default_value = default_value if default_value is not NOTHING else "Default Value"
        self._set_value_name = set_value_name or "setPlaceholderText"

        self.btn_reset = QtWidgets.QPushButton(self)
        self.btn_reset.setFlat(True)
        self.btn_reset.setToolTip("Reset to default value")
        self.btn_reset.setIcon(QtGui.QIcon("://Reset"))
        self.btn_reset.clicked.connect(self._on_reset_clicked)

        self.h_layout = QtWidgets.QHBoxLayout(self)
        self.v_layout = QtWidgets.QVBoxLayout()

        if not self.p_description:
            self._description_label.hide()

        if self.p_icon.isNull():
            self._icon_label.hide()
        else:
            self._icon_label.setPixmap(self.p_icon.pixmap(self.p_icon_size))

        if not self.p_reset_button:
            self.btn_reset.hide()

        self.setFixedHeight(70 if self.p_description else 50)

        self.h_layout.setSpacing(0)
        self.h_layout.setContentsMargins(16, 0, 0, 0)
        self.h_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.v_layout.setSpacing(0)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.h_layout.addWidget(self._icon_label, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.h_layout.addSpacing(16)

        self.h_layout.addLayout(self.v_layout, 1)
        self.v_layout.addWidget(self._title_label, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.v_layout.addWidget(self._description_label, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.h_layout.addSpacing(16)

        editor_layout = QtWidgets.QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        editor_layout.addStretch(1)

        editor_layout.addWidget(self.editor_widget, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        self.h_layout.addLayout(editor_layout, 1)
        self.h_layout.addSpacing(8)

        self.h_layout.addWidget(self.btn_reset)
        self.h_layout.addSpacing(16)

        # Set name so that it can be found in stylesheet
        self._description_label.setObjectName("textLabel")

        self.setStyleSheet(CARD_STYLE_SHEET)

    def get_title(self) -> str:
        return self.p_title

    def set_title(self, title: str) -> None:
        self.p_title = title
        self._title_label.setText(title)

    def get_description(self) -> str:
        return self.p_description

    def set_description(self, text: str) -> None:
        self.p_description = text
        if text:
            self.setFixedHeight(70)
        else:
            self.setFixedHeight(50)
        self._description_label.setText(text)
        self._description_label.setVisible(bool(text))

    def get_icon(self) -> QtGui.QIcon:
        return self.p_icon

    def set_icon(self, icon: QtGui.QIcon) -> None:
        self.p_icon = icon
        if icon.isNull():
            self._icon_label.hide()
            return
        self._icon_label.setPixmap(icon.pixmap(self.p_icon_size))

    def get_reset_shown(self) -> bool:
        return self.p_reset_button

    def set_reset_shown(self, shown: bool) -> None:
        self.p_reset_button = shown
        self.btn_reset.setVisible(shown)

    def get_icon_size(self) -> QtCore.QSize:
        return self.p_icon_size

    def set_icon_size(self, size: int) -> None:
        self.p_icon_size = QtCore.QSize(size, size)
        self._icon_label.setFixedSize(self.p_icon_size)

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)

        if is_dark_theme():
            painter.setBrush(QtGui.QColor(255, 255, 255, 13))
            painter.setPen(QtGui.QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QtGui.QColor(255, 255, 255, 170))
            painter.setPen(QtGui.QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

    @QtCore.Slot()
    def _on_reset_clicked(self) -> None:
        """
        Emits the `sig_reset_clicked` signal. If a default value and setter function have been
        """
        self.sig_reset_clicked.emit()
        if self._default_value is NOTHING or not self._set_value_name:
            return
        getattr(self.editor_widget, self._set_value_name)(self._default_value)

    title = QtCore.Property(str, get_title, set_title)
    description = QtCore.Property(str, get_description, set_description)
    icon = QtCore.Property(QtGui.QIcon, get_icon, set_icon)
    reset_shown = QtCore.Property(bool, get_reset_shown, set_reset_shown)
    icon_size = QtCore.Property(QtCore.QSize, get_icon_size, set_icon_size)


DOM_XML = f"""
<ui language='c++'>
    <widget class='SettingCard' name='settingCard'>
        <property name='title'>
            <string>Setting Card</string>
        </property>
        <property name='description'>
            <string></string>
        </property>
        <property name='icon'>
            <iconset>
                <normaloff>icons/ArrowReset.svg</normaloff>icons/ArrowReset.svg
            </iconset>
        </property>
        <property name='reset_shown'>
            <bool>true</bool>
        </property>
        <property name='icon_size'>
            <size>
                <width>16</width>
                <height>16</height>
            </size>
        </property>
        <property name='styleSheet'>
            <string notr='true'>{CARD_STYLE_SHEET}
            </string>
        </property>
    </widget>
</ui>
"""


class SettingCardPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def createWidget(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        return SettingCard(
            title="Setting Card",
            parent=parent,
        )

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
        return "SettingCard"

    def toolTip(self) -> str:
        return "Widget for displaying and editing a single setting value."

    def whatsThis(self) -> str:
        return self.toolTip()
