from PySide6 import QtCore, QtDesigner, QtGui, QtWidgets

type ColorLike = QtCore.Qt.GlobalColor | QtGui.QColor | str


class ToggleSwitch(QtWidgets.QCheckBox):
    _transparent_pen = QtGui.QPen(QtCore.Qt.GlobalColor.transparent)
    _light_gray_pen = QtGui.QPen(QtCore.Qt.GlobalColor.lightGray)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        bar_color: ColorLike = QtCore.Qt.GlobalColor.gray,
        checked_color: ColorLike = "#00B0FF",
        handle_color: ColorLike = QtCore.Qt.GlobalColor.white,
    ) -> None:
        super().__init__(parent)

        self._bar_brush = QtGui.QBrush(bar_color)
        self._bar_checked_brush = QtGui.QBrush(QtGui.QColor(checked_color).lighter())

        self._handle_brush = QtGui.QBrush(handle_color)
        self._handle_checked_brush = QtGui.QBrush(QtGui.QColor(checked_color))

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)

        self.stateChanged.connect(self.handle_state_change)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(58, 45)

    def hitButton(self, pos: QtCore.QPoint) -> bool:
        return self.contentsRect().contains(pos)

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        cont_rect = self.contentsRect()
        handle_radius = round(0.24 * cont_rect.height())

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        p.setPen(self._transparent_pen)
        bar_rect = QtCore.QRectF(0, 0, cont_rect.width() - handle_radius, 0.40 * cont_rect.height())
        bar_rect.moveCenter(cont_rect.center().toPointF())
        rounding = bar_rect.height() / 2

        trail_length = cont_rect.width() - 2 * handle_radius
        x_pos = cont_rect.x() + handle_radius + trail_length * self._handle_position

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(bar_rect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(bar_rect, rounding, rounding)
            p.setPen(self._light_gray_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(QtCore.QPointF(x_pos, bar_rect.center().y()), handle_radius, handle_radius)

        p.end()

    @QtCore.Slot(int)
    def handle_state_change(self, value: int) -> None:
        self._handle_position = 1 if value else 0

    @QtCore.Property(float)
    def handle_position(self) -> float:  # type: ignore
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos: float) -> None:
        self._handle_position = pos
        self.update()

    @QtCore.Property(float)
    def pulse_radius(self) -> float:  # type: ignore
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos: float) -> None:
        self._pulse_radius = pos
        self.update()


class AnimatedToggleSwitch(ToggleSwitch):
    _transparent_pen = QtGui.QPen(QtCore.Qt.GlobalColor.transparent)
    _light_gray_pen = QtGui.QPen(QtCore.Qt.GlobalColor.lightGray)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        bar_color: ColorLike = QtCore.Qt.GlobalColor.gray,
        checked_color: ColorLike = "#00B0FF",
        handle_color: ColorLike = QtCore.Qt.GlobalColor.white,
        pulse_unchecked_color: ColorLike = "#44999999",
        pulse_checked_color: ColorLike = "#4400B0EE",
    ) -> None:
        self._pulse_radius = 0
        super().__init__(parent, bar_color, checked_color, handle_color)

        self.animation = QtCore.QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)

        self.pulse_anim = QtCore.QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group = QtCore.QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self._pulse_unchecked_animation = QtGui.QBrush(QtGui.QColor(pulse_unchecked_color))
        self._pulse_checked_animation = QtGui.QBrush(QtGui.QColor(pulse_checked_color))

    @QtCore.Slot(int)
    def handle_state_change(self, value: int) -> None:
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)

        self.animations_group.start()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        cont_rect = self.contentsRect()
        handle_radius = round(0.24 * cont_rect.height())

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        p.setPen(self._transparent_pen)
        bar_rect = QtCore.QRectF(0, 0, cont_rect.width() - handle_radius, 0.40 * cont_rect.height())
        bar_rect.moveCenter(cont_rect.center().toPointF())
        rounding = bar_rect.height() / 2

        trail_length = cont_rect.width() - 2 * handle_radius
        x_pos = cont_rect.x() + handle_radius + trail_length * self._handle_position

        if self.pulse_anim.state() == QtCore.QPropertyAnimation.State.Running:
            p.setBrush(self._pulse_checked_animation if self.isChecked() else self._pulse_unchecked_animation)
            p.drawEllipse(QtCore.QPointF(x_pos, bar_rect.center().y()), self._pulse_radius, self._pulse_radius)

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(bar_rect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(bar_rect, rounding, rounding)
            p.setPen(self._light_gray_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(QtCore.QPointF(x_pos, bar_rect.center().y()), handle_radius, handle_radius)

        p.end()


DOM_XML = """
<ui language='c++'>
    <widget class='ToggleSwitch' name='toggleSwitch'>
    </widget>
</ui>
"""


class ToggleSwitchPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def createWidget(self, parent: QtWidgets.QWidget) -> ToggleSwitch:
        return ToggleSwitch(parent=parent)

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
        return "ToggleSwitch"

    def toolTip(self) -> str:
        return "QCheckBox displayed as a toggle switch"

    def whatsThis(self) -> str:
        return self.toolTip()
