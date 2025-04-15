import warnings
from collections import OrderedDict
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg

# from pyqtgraph import AxisItem, DateAxisItem
from pyqtgraph.graphicsItems.DateAxisItem import (
    DAY_SPACING,
    HMS_ZOOM_LEVEL,
    HOUR_SPACING,
    MINUTE_SPACING,
    MS_ZOOM_LEVEL,
    DateAxisItem,
    TickSpec,
    ZoomLevel,
    makeSStepper,
)
from pyqtgraph.GraphicsScene import mouseEvents
from pyqtgraph.Point import Point
from PySide6 import QtCore, QtGui, QtWidgets

import signal_viewer.type_defs as _t
from signal_viewer.enum_defs import MouseButtons
from signal_viewer.utils import make_qbrush, make_qpen

if TYPE_CHECKING:
    from pyqtgraph.GraphicsScene import mouseEvents


def _get_button_type(ev: "mouseEvents.MouseDragEvent") -> MouseButtons:
    if ev.button() == QtCore.Qt.MouseButton.MiddleButton:
        return MouseButtons.MiddleButton
    elif ev.button() == QtCore.Qt.MouseButton.LeftButton:
        if ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            return MouseButtons.LeftButtonWithControl
        else:
            return MouseButtons.LeftButton
    elif ev.button() == QtCore.Qt.MouseButton.RightButton:
        return MouseButtons.RightButton
    else:
        return MouseButtons.Unknown


class EditingViewBox(pg.ViewBox):
    """
    `pyqtgraph.ViewBox` that makes selection of data easier.
    """

    def __init__(self, *args: Any, **kargs: Any) -> None:
        super().__init__(*args, **kargs)
        self._selection_box: QtWidgets.QGraphicsRectItem | None = None
        self.mapped_selection_rect: QtCore.QRectF | None = None

    @property
    def selection_box(self) -> QtWidgets.QGraphicsRectItem:
        if self._selection_box is None:
            selection_box = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
            pen = make_qpen((255, 165, 0, 255))
            brush = make_qbrush((255, 165, 0, 100))
            selection_box.setPen(pen)
            selection_box.setBrush(brush)
            selection_box.setZValue(1e9)
            selection_box.hide()
            self._selection_box = selection_box
            self.addItem(selection_box, ignoreBounds=True)
        return self._selection_box

    @selection_box.setter
    def selection_box(self, selection_box: QtWidgets.QGraphicsRectItem | None) -> None:
        if self._selection_box is not None:
            self.removeItem(self._selection_box)
        self._selection_box = selection_box
        if selection_box is None:
            return
        selection_box.setZValue(1e9)
        selection_box.hide()
        self.addItem(selection_box, ignoreBounds=True)
        return

    def mouseDragEvent(self, ev: "mouseEvents.MouseDragEvent", axis: int | float | None = None) -> None:
        ev.accept()

        pos = ev.pos()
        last_pos = ev.lastPos()
        dif: Point = (pos - last_pos) * np.array([-1, -1])

        mouse_enabled = np.array(self.state["mouseEnabled"], dtype=np.float64)
        mask = mouse_enabled.copy()
        if axis is not None:
            mask[1 - axis] = 0.0  # type: ignore

        button_type = _get_button_type(ev)

        if button_type in {MouseButtons.MiddleButton, MouseButtons.LeftButtonWithControl}:
            if ev.isFinish():
                r = QtCore.QRectF(ev.pos(), ev.buttonDownPos())
                self.mapped_selection_rect = self.mapToView(r).boundingRect()
            else:
                self.updateSelectionBox(ev.pos(), ev.buttonDownPos())
                self.mapped_selection_rect = None
        elif button_type == MouseButtons.LeftButton:
            if self.state["mouseMode"] == pg.ViewBox.RectMode and axis is None:
                if ev.isFinish():
                    self._on_left_mouse_drag_finished(ev, pos)
                else:
                    self.updateScaleBox(ev.buttonDownPos(), ev.pos())
            else:
                self._on_left_mouse_drag(dif, mask)
        elif button_type == MouseButtons.RightButton:
            self._on_right_mouse_drag(mask, ev, mouse_enabled)

    def _on_right_mouse_drag(
        self,
        mask: npt.NDArray[np.float64],
        ev: "mouseEvents.MouseDragEvent",
        mouse_enabled: npt.NDArray[np.float64],
    ) -> None:
        if self.state["aspectLocked"] is not False:
            mask[0] = 0

        dif = np.array(
            [
                -(ev.screenPos().x() - ev.lastScreenPos().x()),
                ev.screenPos().y() - ev.lastScreenPos().y(),
            ]
        )
        s = ((mask * 0.02) + 1) ** dif

        tr = pg.invertQTransform(self.childGroup.transform())

        x = s[0] if mouse_enabled[0] == 1 else None
        y = s[1] if mouse_enabled[1] == 1 else None

        center = Point(tr.map(ev.buttonDownPos(QtCore.Qt.MouseButton.RightButton)))
        self._resetTarget()
        self.scaleBy(x=x, y=y, center=center)
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])

    def _on_left_mouse_drag(self, dif: Point, mask: npt.NDArray[np.float64]) -> None:
        tr = pg.invertQTransform(self.childGroup.transform())
        tr = tr.map(dif * mask) - tr.map(Point(0, 0))

        x = tr.x() if mask[0] == 1 else None
        y = tr.y() if mask[1] == 1 else None

        self._resetTarget()
        if x is not None or y is not None:
            self.translateBy(x=x, y=y)
        self.sigRangeChangedManually.emit(self.state["mouseEnabled"])

    def _on_left_mouse_drag_finished(self, ev: "mouseEvents.MouseDragEvent", pos: Point) -> None:
        self.rbScaleBox.hide()
        ax = QtCore.QRectF(Point(ev.buttonDownPos(ev.button())), Point(pos))
        ax = self.childGroup.mapRectFromParent(ax)
        self.showAxRect(ax)
        self.axHistoryPointer += 1
        self.axHistory = self.axHistory[: self.axHistoryPointer] + [ax]

    def updateSelectionBox(self, pos1: Point, pos2: Point) -> None:
        rect = QtCore.QRectF(pos1, pos2)
        rect = self.childGroup.mapRectFromParent(rect)
        self.selection_box.setPos(rect.topLeft())
        tr = QtGui.QTransform.fromScale(rect.width(), rect.height())
        self.selection_box.setTransform(tr)
        self.selection_box.show()


# class TimeAxisItem(AxisItem):
#     """
#     Custom `pyqtgraph.AxisItem` subclass for displaying millisecond timestamps in a human readable format.
#     """

#     def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:
#         strings: list[str] = []
#         for v in values:
#             vs = v * scale
#             minutes, seconds = divmod(int(vs), 60)
#             hours, minutes = divmod(minutes, 60)
#             vstr = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
#             strings.append(vstr)
#         return strings


def _format_hms_timedelta(
    seconds: int | float, show_seconds: bool = False, show_accuracy_warnings: bool = False
) -> str:
    seconds_whole = int(seconds)
    milliseconds = int((seconds - seconds_whole) * 1000)

    hours = seconds_whole // 3600
    minutes = (seconds_whole % 3600) // 60
    seconds = seconds_whole % 60

    if show_accuracy_warnings and milliseconds != 0:
        warnings.warn(f"Truncating milliseconds ({milliseconds} ms), this may lead to an incorrect label for the tick.")

    if show_seconds:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    if show_accuracy_warnings and not np.isclose(seconds, 0, atol=1e-10):
        warnings.warn(f"Truncating seconds ({seconds} s), this may lead to an incorrect label for the tick.")

    return f"{hours:02d}:{minutes:02d}"


def _format_day_timedelta(seconds: int | float, show_accuracy_warnings: bool = False) -> str:
    hours = int(seconds // (3600 * 24))
    missing_seconds = hours * 3600 * 24 - seconds
    if show_accuracy_warnings and missing_seconds != 0:
        warnings.warn(f"Truncating seconds ({missing_seconds} s), this may lead to an incorrect label for the tick.")
    return f"{hours:d} d"


DAY_DT_ZOOM_LEVEL = ZoomLevel(
    [TickSpec(DAY_SPACING, makeSStepper(DAY_SPACING), None, autoSkip=[2, 5, 10, 20, 30])],
    "123 d",
)

H_DT_ZOOM_LEVEL = ZoomLevel(
    [TickSpec(HOUR_SPACING, makeSStepper(HOUR_SPACING), None, autoSkip=[1, 5, 15, 30])],
    "99:99",
)
HM_DT_ZOOM_LEVEL = ZoomLevel(
    [TickSpec(MINUTE_SPACING, makeSStepper(MINUTE_SPACING), None, autoSkip=[1, 5, 15, 30])],
    "99:99",
)


class TimeDeltaAxisItem(DateAxisItem):
    def __init__(
        self,
        orientation: Literal["left", "right", "top", "bottom"] = "bottom",
        utcOffset: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(orientation, utcOffset, **kwargs)

        self.zoomLevels = OrderedDict(
            [
                (np.inf, DAY_DT_ZOOM_LEVEL),  # days
                (24 * 3600, H_DT_ZOOM_LEVEL),  # HH:00 with hour-spacing
                (1800, HM_DT_ZOOM_LEVEL),  # HH:MM
                (100, HMS_ZOOM_LEVEL),  # HH:MM:SS
                (10, MS_ZOOM_LEVEL),  # SS.ms
            ]
        )
        self.autoSIPrefix = False

    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:
        tickSpecs = self.zoomLevel.tickSpecs
        tickSpec = next((s for s in tickSpecs if s.spacing == spacing), None)
        if tickSpec is None:
            return super().tickStrings(values, scale, spacing)

        if tickSpec.spacing == DAY_SPACING:
            self.labelUnits = "day"
            self._updateLabel()
            return [_format_day_timedelta(value * scale) for value in values]
        elif tickSpec.spacing in [HOUR_SPACING, MINUTE_SPACING]:
            return self._format_tick_strings("hour:minute", values, scale, False)
        elif tickSpec.spacing == 1:
            return self._format_tick_strings("hour:minute:sec", values, scale, True)
        else:
            self.labelUnits = "seconds"
            self._updateLabel()
            return super().tickStrings(values, scale, spacing)

    def _format_tick_strings(
        self, label_units: str, values: list[float], scale: float, show_seconds: bool
    ) -> list[str]:
        self.labelUnits = label_units
        self._updateLabel()
        return [_format_hms_timedelta(value * scale, show_seconds=show_seconds) for value in values]


class ClickableRegionItem(pg.LinearRegionItem):
    """
    A clickable region item for pyqtgraph plots.

    This class extends `pg.LinearRegionItem` to allow for click events on the region.

    Attributes:
        sig_clicked (QtCore.Signal): Emitted when the region is clicked.
            The signal carries an integer value representing the section ID.
    """

    sig_clicked = QtCore.Signal(int)

    def __init__(
        self,
        values: Sequence[float] = (0, 1),
        orientation: Literal["vertical", "horizontal"] = "vertical",
        brush: _t.PGBrush | None = None,
        pen: _t.PGPen | None = None,
        hoverBrush: _t.PGBrush | None = None,
        hoverPen: _t.PGPen | None = None,
        movable: bool = True,
        bounds: Sequence[float] | None = None,
        span: Sequence[float] = (0, 1),
        swapMode: Literal["block", "push", "sort"] = "sort",
        clipItem: pg.GraphicsObject | None = None,
    ) -> None:
        super().__init__(
            values, orientation, brush, pen, hoverBrush, hoverPen, movable, bounds, span, swapMode, clipItem
        )

        self._section_id: int = 0

    @property
    def section_id(self) -> int:
        return self._section_id

    @section_id.setter
    def section_id(self, value: int) -> None:
        self._section_id = value

    def mouseClickEvent(self, ev: "mouseEvents.MouseClickEvent") -> None:
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            self.sig_clicked.emit(self._section_id)
            ev.accept()
        else:
            super().mouseClickEvent(ev)

    def hoverEvent(self, ev: "mouseEvents.HoverEvent") -> None:
        if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton):
            self.setMouseHover(True)
        else:
            self.setMouseHover(False)
