from PySide6 import QtCore, QtDesigner, QtGui, QtWidgets

type ColorLike = QtCore.Qt.GlobalColor | QtGui.QColor | str


class IndeterminateSpinner(QtWidgets.QProgressBar):
    """
    Indeterminate progress ring, based on `qfluentwidgets.IndeterminateProgressRing`.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None, start: bool = True) -> None:
        super().__init__(parent)

        self._bg_color = QtGui.QColor(0, 0, 0, 0)
        self._bar_color = QtGui.QColor()
        self._stroke_width = 6

        self._startAngle = -180
        self._spanAngle = 0

        self.start_angle_ani1 = QtCore.QPropertyAnimation(self, b"startAngle", self)
        self.start_angle_ani2 = QtCore.QPropertyAnimation(self, b"startAngle", self)
        self.span_angle_ani1 = QtCore.QPropertyAnimation(self, b"spanAngle", self)
        self.span_angle_ani2 = QtCore.QPropertyAnimation(self, b"spanAngle", self)

        self.start_angle_ani_group = QtCore.QSequentialAnimationGroup(self)
        self.span_angle_ani_group = QtCore.QSequentialAnimationGroup(self)
        self.ani_group = QtCore.QParallelAnimationGroup(self)

        # Initialize start angle animation
        self.start_angle_ani1.setDuration(1000)
        self.start_angle_ani1.setStartValue(0)
        self.start_angle_ani1.setEndValue(450)

        self.start_angle_ani2.setDuration(1000)
        self.start_angle_ani2.setStartValue(450)
        self.start_angle_ani2.setEndValue(1080)

        self.start_angle_ani_group.addAnimation(self.start_angle_ani1)
        self.start_angle_ani_group.addAnimation(self.start_angle_ani2)

        # Initialize span angle animation
        self.span_angle_ani1.setDuration(1000)
        self.span_angle_ani1.setStartValue(0)
        self.span_angle_ani1.setEndValue(180)

        self.span_angle_ani2.setDuration(1000)
        self.span_angle_ani2.setStartValue(180)
        self.span_angle_ani2.setEndValue(0)

        self.span_angle_ani_group.addAnimation(self.span_angle_ani1)
        self.span_angle_ani_group.addAnimation(self.span_angle_ani2)

        self.ani_group.addAnimation(self.start_angle_ani_group)
        self.ani_group.addAnimation(self.span_angle_ani_group)
        self.ani_group.setLoopCount(-1)

        self.setFixedSize(80, 80)

        if start:
            self.start()

    @QtCore.Property(int)
    def startAngle(self) -> int:  # type: ignore
        return self._startAngle

    @startAngle.setter
    def startAngle(self, angle: int) -> None:
        self._startAngle = angle
        self.update()

    @QtCore.Property(int)
    def spanAngle(self) -> int:  # type: ignore
        return self._spanAngle

    @spanAngle.setter
    def spanAngle(self, angle: int) -> None:
        self._spanAngle = angle
        self.update()

    def get_stroke_width(self) -> int:
        return self._stroke_width

    def set_stroke_width(self, width: int) -> None:
        self._stroke_width = width
        self.update()

    def start(self) -> None:
        self._startAngle = 0
        self._spanAngle = 0
        self.ani_group.start()

    def stop(self) -> None:
        self.ani_group.stop()
        self._startAngle = 0
        self._spanAngle = 0

    def set_bg_color(self, color: QtGui.QColor | str) -> None:
        bg_color = QtGui.QColor(color)
        if not bg_color.isValid():
            return
        self._bg_color = bg_color
        self.update()

    def set_bar_color(self, color: QtGui.QColor | str) -> None:
        bar_color = QtGui.QColor(color)
        if not bar_color.isValid():
            return
        self._bar_color = bar_color
        self.update()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)

        cw = self._stroke_width
        w = min(self.height(), self.width()) - cw
        rc = QtCore.QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # Draw background
        bc = self._bg_color
        pen = QtGui.QPen(
            bc,
            cw,
            QtCore.Qt.PenStyle.SolidLine,
            QtCore.Qt.PenCapStyle.RoundCap,
            QtCore.Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.drawArc(rc, 0, 360 * 16)

        # Draw bar
        pen.setColor(self._bar_color)
        painter.setPen(pen)

        start_angle = -self.startAngle + 180  # type: ignore
        painter.drawArc(rc, (start_angle % 360) * 16, -self.spanAngle * 16)  # type: ignore

    stroke_width = QtCore.Property(int, get_stroke_width, set_stroke_width)


class OverlayWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.hide()
        self._target = parent

        self._bg_color = QtGui.QColor(0, 0, 0, 128)
        self._bar_color = QtGui.QColor("cornflowerblue")

        self._container = QtWidgets.QWidget(self)
        self._container.setStyleSheet(f"background: {self._bg_color.name()};")

        self._layout = QtWidgets.QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._content = QtWidgets.QWidget(self._container)
        self._content.setStyleSheet("background: rgba(0, 0, 0, 0);")

        self._layout_content = QtWidgets.QVBoxLayout(self._content)
        self._layout_content.setSpacing(12)

        font = self.parentWidget().font()
        font.setPointSize(28)
        font.setWeight(QtGui.QFont.Weight.DemiBold)

        self._text = QtWidgets.QLabel(self._content)
        self._text.setFont(font)
        self._text.setStyleSheet("background: transparent; color: white;")
        self._text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._spinner = IndeterminateSpinner(self._content)
        self._spinner.set_bar_color(self._bar_color)

        self._layout_content.addWidget(
            self._text,
            0,
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self._layout_content.addWidget(
            self._spinner,
            0,
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter,
        )

        self._layout.addWidget(
            self._content,
            0,
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter,
        )

    def get_bg_color(self) -> QtGui.QColor:
        return self._bg_color

    def set_bg_color(self, color: ColorLike) -> None:
        """
        Set the background color of the container widget to the provided rgba values.

        Args:
            color (ColorLike): The color to set the background to
        """
        self._bg_color = QtGui.QColor(color)
        self._container.setStyleSheet(f"background: {self._bg_color.name()};")

    def get_text(self) -> str:
        return self._text.text()

    def set_text(self, text: str) -> None:
        """
        Set the text of the label

        Args:
            text (str): The text to display
        """
        self._text.setText(text)

    def get_bar_color(self) -> QtGui.QColor:
        return self._bar_color

    def set_bar_color(self, color: ColorLike) -> None:
        """Set the color of the spinner"""
        self._bar_color = QtGui.QColor(color)
        self._spinner.set_bar_color(self._bar_color)

    def show_overlay(self, text: str | None = None) -> None:
        """
        Disables the target widget, updates the label text if provided, and shows the overlay

        Args:
            text: The text to display, defaults to None
        """
        self._target.setEnabled(False)

        if text is not None:
            self._text.setText(text)

        self.setGeometry(self._target.geometry())
        self._container.move(0, 0)
        self._container.resize(self._target.size())
        self.move(0, 0)
        self.raise_()
        self.show()

    def hide_overlay(self) -> None:
        """
        Enables the target widget and hides the overlay
        """
        self._target.setEnabled(True)
        self.hide()

    @QtCore.Slot(bool)
    def toggle_overlay(self, visible: bool) -> None:
        if visible:
            self.show_overlay()
        else:
            self.hide_overlay()

    text = QtCore.Property(str, get_text, set_text)
    bg_color = QtCore.Property(QtGui.QColor, get_bg_color, set_bg_color)
    bar_color = QtCore.Property(QtGui.QColor, get_bar_color, set_bar_color)


DOM_XML = """
<ui language='c++'>
    <widget class='OverlayWidget' name='overlayWidget'>
        <property name='text'>
            <string>Running...</string>
        </property>
        <property name='bg_color'>
            <color alpha='128'>
                <red>0</red>
                <green>0</green>
                <blue>0</blue>
            </color>
        </property>
        <property name='bar_color'>
            <color alpha='255'>
                <red>100</red>
                <green>149</green>
                <blue>237</blue>
            </color>
        </property>
    </widget>
</ui>
"""


class OverlayWidgetPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def createWidget(self, parent: QtWidgets.QWidget) -> OverlayWidget:
        return OverlayWidget(parent=parent)

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
        return "OverlayWidget"

    def toolTip(self) -> str:
        return "Can be used to lock the UI while an operation is running"

    def whatsThis(self) -> str:
        return self.toolTip()
