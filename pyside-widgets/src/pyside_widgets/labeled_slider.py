import enum
import typing as t

from PySide6 import QtCore, QtGui, QtWidgets


class ValueSlider(QtWidgets.QSlider):
    """
    A custom QSlider that displays its current value above the slider handle.

    This class extends QSlider to provide a visual representation of the current value directly on the slider. It's
    oriented horizontally by default and expands horizontally while maintaining a minimum vertical size.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)

    def setTickPosition(self, position: QtWidgets.QSlider.TickPosition) -> None:
        super().setTickPosition(position)
        self.updateGeometry()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        super().paintEvent(ev)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        painter.setPen(QtGui.QColor(0, 0, 0))

        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)

        # Get the rectangle of the slider handle
        handle_rect = self.style().subControlRect(
            QtWidgets.QStyle.ComplexControl.CC_Slider, opt, QtWidgets.QStyle.SubControl.SC_SliderHandle, self
        )
        slider_thickness = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_SliderThickness, opt, self)
        handle_center = handle_rect.center()
        handle_bbox = QtCore.QRect(
            handle_rect.left(), handle_center.y() - slider_thickness // 2 + 1, handle_rect.width(), slider_thickness - 1
        )

        value_text = str(self.value())

        width_value_text = painter.fontMetrics().horizontalAdvance(value_text)
        height_text = painter.fontMetrics().height()

        # Ensure that the value text isn't cut off at the edges of the slider
        value_text_left = max(handle_bbox.center().x() - width_value_text // 2, 0)
        if value_text_left + width_value_text > self.width():
            value_text_left = self.width() - width_value_text
        value_text_top = handle_bbox.top() - height_text

        # Create the rectangle for the value text
        text_rect = QtCore.QRect(value_text_left, value_text_top, width_value_text, height_text)

        painter.drawText(text_rect, value_text, QtCore.Qt.AlignmentFlag.AlignCenter)

    def minimumSizeHint(self) -> QtCore.QSize:
        tick_pos = self.tickPosition()
        if tick_pos == QtWidgets.QSlider.TickPosition.NoTicks:
            return QtCore.QSize(0, 50)
        elif tick_pos in (QtWidgets.QSlider.TickPosition.TicksBelow, QtWidgets.QSlider.TickPosition.TicksAbove):
            return QtCore.QSize(0, 75)
        elif tick_pos == QtWidgets.QSlider.TickPosition.TicksBothSides:
            return QtCore.QSize(0, 100)

        return super().minimumSizeHint()


class LabeledSlider(QtWidgets.QWidget):
    """
    A compound widget that combines a ValueSlider with labels for title, minimum, and maximum values.

    This widget provides a customizable slider with an optional title and min/max labels. It allows for various
    positioning options for the title label and can show or hide the min/max labels as needed.
    """

    # Wrapped slider signals
    actionTriggered: t.ClassVar = QtCore.Signal(int)  # QtWidgets.QAbstractSlider.SliderAction
    rangeChanged: t.ClassVar = QtCore.Signal(int, int)  # min, max
    sliderMoved: t.ClassVar = QtCore.Signal(int)  # new slider position
    sliderPressed: t.ClassVar = QtCore.Signal()
    sliderReleased: t.ClassVar = QtCore.Signal()
    valueChanged: t.ClassVar = QtCore.Signal(int)  # new slider value

    class TitleLabelPosition(enum.Enum):
        TOP_LEFT = QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
        TOP_CENTER = QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter
        TOP_RIGHT = QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignRight
        BOTTOM_LEFT = QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignLeft
        BOTTOM_CENTER = QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter
        BOTTOM_RIGHT = QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignRight
        LEFT = QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft
        RIGHT = QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        title: str = "",
        title_pos: TitleLabelPosition = TitleLabelPosition.TOP_LEFT,
        show_min_max: bool = True,
    ) -> None:
        super().__init__(parent)

        self._slider = ValueSlider(self)
        self._slider.actionTriggered.connect(self.actionTriggered.emit)
        self._slider.rangeChanged.connect(self.rangeChanged.emit)
        self._slider.sliderMoved.connect(self.sliderMoved.emit)
        self._slider.sliderPressed.connect(self.sliderPressed.emit)
        self._slider.sliderReleased.connect(self.sliderReleased.emit)
        self._slider.valueChanged.connect(self.valueChanged.emit)

        self.title_label = QtWidgets.QLabel(self)
        if not title:
            self.title_label.hide()

        self.title_label.setText(title)

        self.minimum_label = QtWidgets.QLabel(self)
        self.maximum_label = QtWidgets.QLabel(self)

        if not show_min_max:
            self.minimum_label.hide()
            self.maximum_label.hide()

        self.minimum_label.setText(f"{self._slider.minimum()}")
        self.maximum_label.setText(f"{self._slider.maximum()}")

        main_layout = QtWidgets.QGridLayout()
        main_layout.setVerticalSpacing(0)

        tlp = self.TitleLabelPosition
        alignment = title_pos.value

        h_layout_slider = QtWidgets.QHBoxLayout()

        h_layout_slider.addWidget(self.minimum_label, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        h_layout_slider.addWidget(self._slider, 1)
        h_layout_slider.addWidget(self.maximum_label, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        if title_pos in (tlp.TOP_LEFT, tlp.TOP_CENTER, tlp.TOP_RIGHT):
            main_layout.addWidget(self.title_label, 0, 1, alignment)
            main_layout.addWidget(self.minimum_label, 1, 0, QtCore.Qt.AlignmentFlag.AlignRight)
            main_layout.addWidget(self._slider, 1, 1)
            main_layout.addWidget(self.maximum_label, 1, 2, QtCore.Qt.AlignmentFlag.AlignLeft)
        elif title_pos in (tlp.BOTTOM_LEFT, tlp.BOTTOM_CENTER, tlp.BOTTOM_RIGHT):
            main_layout.addWidget(self.minimum_label, 0, 0, QtCore.Qt.AlignmentFlag.AlignRight)
            main_layout.addWidget(self._slider, 0, 1)
            main_layout.addWidget(self.maximum_label, 0, 2, QtCore.Qt.AlignmentFlag.AlignLeft)
            main_layout.addWidget(self.title_label, 1, 1, alignment)
        elif title_pos == tlp.LEFT:
            h_layout_slider.insertWidget(0, self.title_label, 0, alignment)
            h_layout_slider.insertSpacing(1, 16)
            main_layout = h_layout_slider
        elif title_pos == tlp.RIGHT:
            h_layout_slider.addSpacing(16)
            h_layout_slider.addWidget(self.title_label, 0, alignment)
            main_layout = h_layout_slider

        self.setLayout(main_layout)

    def hasTracking(self) -> bool:
        return self._slider.hasTracking()

    def setTracking(self, tracking: bool) -> None:
        self._slider.setTracking(tracking)

    def invertedAppearance(self) -> bool:
        return self._slider.invertedAppearance()

    def setInvertedAppearance(self, inverted: bool) -> None:
        self._slider.setInvertedAppearance(inverted)

    def invertedControls(self) -> bool:
        return self._slider.invertedControls()

    def setInvertedControls(self, inverted: bool) -> None:
        self._slider.setInvertedControls(inverted)

    def isSliderDown(self) -> bool:
        return self._slider.isSliderDown()

    def setSliderDown(self, down: bool) -> None:
        self._slider.setSliderDown(down)

    def maximum(self) -> int:
        return self._slider.maximum()

    def setMaximum(self, value: int) -> None:
        self._slider.setMaximum(value)
        self.maximum_label.setText(f"{value}")

    def minimum(self) -> int:
        return self._slider.minimum()

    def setMinimum(self, value: int) -> None:
        self._slider.setMinimum(value)
        self.minimum_label.setText(f"{value}")

    def orientation(self) -> QtCore.Qt.Orientation:
        return QtCore.Qt.Orientation.Horizontal

    def setOrientation(self, orientation: QtCore.Qt.Orientation) -> None:
        raise NotImplementedError("LabeledSlider does not support vertical orientation yet.")

    def pageStep(self) -> int:
        return self._slider.pageStep()

    def setPageStep(self, step: int) -> None:
        self._slider.setPageStep(step)

    def repeatAction(self) -> QtWidgets.QAbstractSlider.SliderAction:
        return self._slider.repeatAction()

    def setRepeatAction(
        self, action: QtWidgets.QAbstractSlider.SliderAction, thresholdTime: int = 500, repeatTime: int = 50
    ) -> None:
        self._slider.setRepeatAction(action, thresholdTime, repeatTime)

    def singleStep(self) -> int:
        return self._slider.singleStep()

    def setSingleStep(self, step: int) -> None:
        self._slider.setSingleStep(step)

    def sliderPosition(self) -> int:
        return self._slider.sliderPosition()

    def setSliderPosition(self, position: int) -> None:
        self._slider.setSliderPosition(position)

    def triggerAction(self, action: QtWidgets.QAbstractSlider.SliderAction) -> None:
        self._slider.triggerAction(action)

    def value(self) -> int:
        return self._slider.value()

    def setValue(self, value: int) -> None:
        self._slider.setValue(value)

    def setRange(self, min: int, max: int) -> None:
        self._slider.setRange(min, max)
        self.minimum_label.setText(f"{min}")
        self.maximum_label.setText(f"{max}")

    def tickInterval(self) -> int:
        return self._slider.tickInterval()

    def setTickInterval(self, interval: int) -> None:
        self._slider.setTickInterval(interval)

    def tickPosition(self) -> QtWidgets.QSlider.TickPosition:
        return self._slider.tickPosition()

    def setTickPosition(self, position: QtWidgets.QSlider.TickPosition) -> None:
        self._slider.setTickPosition(position)
