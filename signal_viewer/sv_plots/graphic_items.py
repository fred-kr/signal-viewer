from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from pyqtgraph import AxisItem
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


class TimeAxisItem(AxisItem):
    """
    Custom `pyqtgraph.AxisItem` subclass for displaying millisecond timestamps in a human readable format.
    """

    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:
        strings: list[str] = []
        for v in values:
            vs = v * scale
            minutes, seconds = divmod(int(vs), 60)
            hours, minutes = divmod(minutes, 60)
            vstr = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            strings.append(vstr)
        return strings


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


# class PlotScatterItem(pg.ScatterPlotItem):
#     """
#     Custom `pyqtgraph.ScatterPlotItem` subclass that fixes an issue where `num_pts` would error when `y` is a single
#     point not enclosed in an object with a `__len__` attribute.
#     """

#     def addPoints(self, *args: t.Any, **kargs: t.Unpack[_t.SpotItemSetDataKwargs]) -> None:
#         arg_keys = ["spots", "x", "y"]
#         for i, key in enumerate(arg_keys[: len(args)]):
#             kargs[key] = args[i]

#         pos = kargs.get("pos")
#         if pos is not None:
#             if isinstance(pos, np.ndarray):
#                 kargs["x"], kargs["y"] = pos[:, 0], pos[:, 1]
#             else:
#                 kargs["x"], kargs["y"] = zip(
#                     *((p.x(), p.y()) if isinstance(p, QtCore.QPointF) else p for p in pos), strict=True
#                 )

#         spots = kargs.get("spots")
#         x = kargs.get("x")
#         y = kargs.get("y")

#         # Determine how many spots we have
#         num_pts = (
#             len(spots)
#             if spots is not None
#             else len(y)
#             if y is not None and hasattr(y, "__len__")
#             else 1
#             if y is not None
#             else 0
#         )

#         # Initialize new data array
#         self.data["item"][...] = None

#         old_data = self.data
#         self.data = np.empty(len(old_data) + num_pts, dtype=self.data.dtype)

#         self.data[: len(old_data)] = old_data

#         new_data = self.data[len(old_data) :]
#         new_data["size"] = -1
#         new_data["visible"] = True

#         # Handle 'spots' parameter
#         if spots is not None:
#             for i, spot in enumerate(spots):
#                 for k, v in spot.items():
#                     if k == "pos":
#                         pos = v
#                         if isinstance(pos, QtCore.QPointF):
#                             x, y = pos.x(), pos.y()
#                         else:
#                             x, y = pos[0], pos[1]
#                         new_data[i]["x"] = x
#                         new_data[i]["y"] = y
#                     elif k == "pen":
#                         new_data[i][k] = make_qpen(v)
#                     elif k == "brush":
#                         new_data[i][k] = make_qbrush(v)
#                     elif k in ("x", "y", "size", "symbol", "data"):
#                         new_data[i][k] = v
#                     else:
#                         raise KeyError(f"Invalid key: {k}")
#         # Handle 'y' parameter
#         elif y is not None:
#             new_data["x"] = x
#             new_data["y"] = y

#         for k, v in kargs.items():
#             if k == "name":
#                 self.opts["name"] = v
#             elif k == "pxMode":
#                 self.setPxMode(v)
#             elif k == "antialias":
#                 self.opts["antialias"] = v
#             elif k == "hoverable":
#                 self.opts["hoverable"] = bool(v)
#             elif k == "tip":
#                 self.opts["tip"] = v
#             elif k == "useCache":
#                 self.opts["useCache"] = v
#             elif k in ("pen", "brush", "symbol", "size"):
#                 set_method = getattr(self, f"set{k.capitalize()}")
#                 set_method(v, update=False, dataSet=new_data, mask=kargs.get("mask", None))
#             elif k in ("hoverPen", "hoverBrush", "hoverSymbol", "hoverSize"):
#                 vh = kargs[k]
#                 if k == "hoverPen":
#                     vh = make_qpen(vh)
#                 elif k == "hoverBrush":
#                     vh = make_qbrush(vh)
#                 self.opts[k] = vh  # type: ignore
#             elif k == "data":
#                 self.setPointData(kargs["data"], dataSet=new_data)

#         # Update the scatter plot item
#         self.prepareGeometryChange()
#         self.informViewBoundsChanged()
#         self.bounds = [None, None]
#         self.invalidate()
#         self.updateSpots(new_data)
#         self.sigPlotChanged.emit(self)
