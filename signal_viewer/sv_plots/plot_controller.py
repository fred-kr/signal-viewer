# pyright: reportOptionalMemberAccess=false

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from loguru import logger
from PySide6 import QtCore, QtWidgets

from signal_viewer.enum_defs import PointSymbols, SVGColors
from signal_viewer.sv_config import Config
from signal_viewer.sv_plots.graphic_items import (
    ClickableRegionItem,
    EditingViewBox,
    TimeDeltaAxisItem,
)
from signal_viewer.utils import make_qbrush, make_qpen, safe_disconnect

if TYPE_CHECKING:
    from pyqtgraph.GraphicsScene import mouseEvents

    from signal_viewer.sv_gui import SVGUI


class PlotController(QtCore.QObject):
    sig_scatter_data_changed = QtCore.Signal(str, object)
    sig_section_clicked = QtCore.Signal(int)

    def __init__(self, parent: QtCore.QObject | None, gui: "SVGUI") -> None:
        super().__init__(parent)

        self._gui = gui
        self.regions: list[ClickableRegionItem] = []
        self._show_regions = False

        self._setup_plot_widgets()
        self._setup_plot_items()
        self._setup_plot_data_items()

        self.block_clicks = False

    def _setup_plot_widgets(self) -> None:
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(2)
        main_plot_widget = pg.PlotWidget(viewBox=EditingViewBox(name="main_plot"))
        rate_plot_widget = pg.PlotWidget(viewBox=pg.ViewBox(name="rate_plot"))

        widget_layout.addWidget(main_plot_widget)
        widget_layout.addWidget(rate_plot_widget)
        self._gui.ui.plot_container.setLayout(widget_layout)
        self.pw_main = main_plot_widget
        self.pw_rate = rate_plot_widget
        self.mpw_result = self._gui.ui.mpl_widget

    def _setup_plot_items(self) -> None:
        for plt_item in (self.pw_main.getPlotItem(), self.pw_rate.getPlotItem()):
            if plt_item is None:
                continue
            plt_item.setAxisItems({"top": TimeDeltaAxisItem(orientation="top")})
            plt_item.showGrid(x=False, y=True)
            plt_item.setDownsampling(auto=True)
            plt_item.setClipToView(True)
            plt_item.addLegend(colCount=2)
            plt_item.addLegend().anchor(itemPos=(0, 1), parentPos=(0, 1), offset=(5, -5))
            plt_item.setMouseEnabled(x=True, y=False)  # type: ignore

        self.pw_main.getPlotItem().getViewBox().enableAutoRange(pg.ViewBox.YAxis, enable=0.99)  # type: ignore
        self.pw_main.getPlotItem().getViewBox().setAutoPan(y=True)

        self.pw_rate.getPlotItem().getViewBox().enableAutoRange(pg.ViewBox.YAxis, enable=True)
        self.pw_rate.getPlotItem().getViewBox().setAutoVisible(y=False)

        self.pw_main.getPlotItem().getViewBox().setXLink("rate_plot")

    def _setup_plot_data_items(self) -> None:
        self._setup_signal_curve()
        self._setup_peak_scatter()
        self._setup_rate_curve()
        self._setup_region_selector()

    def _remove_plot_data_items(self) -> None:
        self._remove_signal_curve()
        self._remove_peak_scatter()
        self._remove_rate_curve()
        self._remove_region_selector()

    def _setup_signal_curve(self) -> None:
        pen = make_qpen(SVGColors.DodgerBlue, width=1)
        click_width = Config.plot.line_click_width
        signal = pg.PlotDataItem(
            pen=pen,
            skipFiniteCheck=True,
            autoDownsample=True,
            name="Signal",
        )
        signal.setCurveClickable(True, width=click_width)
        signal.sigClicked.connect(self._on_curve_clicked)
        signal.sigPlotChanged.connect(self.set_view_limits)
        self.signal_curve = signal
        self.pw_main.addItem(self.signal_curve)

    def _remove_signal_curve(self) -> None:
        if self.signal_curve is None:
            return
        self.signal_curve.sigClicked.disconnect(self._on_curve_clicked)
        self.signal_curve.sigPlotChanged.disconnect(self.set_view_limits)
        self.pw_main.removeItem(self.signal_curve)
        self.signal_curve.setParent(None)
        self.signal_curve = None

    def _setup_region_selector(self) -> None:
        brush_col = SVGColors.LimeGreen.qcolor()
        hover_brush_col = brush_col
        hover_brush_col.setAlpha(90)

        brush = make_qbrush(brush_col)
        line_pen = make_qpen(SVGColors.DarkGreen, width=3)

        hover_brush = make_qbrush(hover_brush_col)
        hover_pen = make_qpen(SVGColors.GreenYellow, width=5)
        self.region_selector = pg.LinearRegionItem(
            brush=brush,
            pen=line_pen,
            hoverBrush=hover_brush,
            hoverPen=hover_pen,
        )
        self.region_selector.setVisible(False)
        self.region_selector.setZValue(1e3)
        for line in self.region_selector.lines:
            line.addMarker("<|>", position=0.5, size=15)

        self.pw_main.addItem(self.region_selector)

    def _remove_region_selector(self) -> None:
        if self.region_selector:
            self.pw_main.removeItem(self.region_selector)
            self.region_selector.setParent(None)
            self.region_selector = None

    def _setup_peak_scatter(self) -> None:
        brush = make_qbrush(SVGColors.GoldenRod)
        hover_brush = make_qbrush(SVGColors.Red)
        hover_pen = make_qpen(SVGColors.Black, width=1)

        scatter = pg.ScatterPlotItem(
            pxMode=True,
            size=10,
            pen=None,
            brush=brush,
            useCache=True,
            name="Peaks",
            hoverable=True,
            hoverPen=hover_pen,
            hoverSymbol=PointSymbols.Cross,
            hoverBrush=hover_brush,
            hoverSize=15,
            tip=None,
        )
        scatter.setZValue(60)
        scatter.sigClicked.connect(self._on_scatter_clicked)
        self.peak_scatter = scatter
        self.pw_main.addItem(self.peak_scatter)

    def _remove_peak_scatter(self) -> None:
        if self.peak_scatter is None:
            return
        self.peak_scatter.sigClicked.disconnect(self._on_scatter_clicked)
        self.pw_main.removeItem(self.peak_scatter)
        self.peak_scatter.setParent(None)
        self.peak_scatter = None

    def _setup_rate_curve(self) -> None:
        pen = make_qpen(SVGColors.IndianRed, width=1)
        rate_curve = pg.PlotDataItem(
            pen=pen,
            skipFiniteCheck=True,
            autoDownsample=True,
            name="Rate",
        )
        self.rate_curve = rate_curve
        self.pw_rate.addItem(self.rate_curve)

    def _remove_rate_curve(self) -> None:
        if self.rate_curve is None:
            return
        self.pw_rate.removeItem(self.rate_curve)
        self.rate_curve.setParent(None)
        self.rate_curve = None

    @QtCore.Slot(int)
    def update_time_axis_scale(self, sampling_rate: int) -> None:
        if sampling_rate == 0:
            return
        for plt_item in (self.pw_main.getPlotItem(), self.pw_rate.getPlotItem()):
            if plt_item is None:
                continue
            plt_item.getAxis("top").setScale(1 / sampling_rate)

    @QtCore.Slot(object)
    def set_view_limits(self, plt_data_item: pg.PlotDataItem) -> None:
        if plt_data_item.xData is None or plt_data_item.xData.size == 0:
            return
        len_data = plt_data_item.xData.size
        self.pw_main.plotItem.vb.setLimits(xMin=-0.25 * len_data, xMax=1.25 * len_data, maxYRange=1e5, minYRange=0.1)
        self.pw_rate.plotItem.vb.setLimits(xMin=-0.25 * len_data, xMax=1.25 * len_data, maxYRange=1e5, minYRange=0.1)
        self.pw_main.plotItem.vb.setRange(xRange=(0, len_data), disableAutoRange=False)
        self.pw_rate.plotItem.vb.setRange(xRange=(0, len_data), disableAutoRange=False)

    def reset(self) -> None:
        """Resets all plot items, regions, and data items to initial state."""
        self.pw_main.clear()
        if self.pw_main.plotItem.legend:
            self.pw_main.plotItem.legend.clear()
        self.pw_rate.clear()
        if self.pw_rate.plotItem.legend:
            self.pw_rate.plotItem.legend.clear()

        self.mpw_result.fig.clear()

        self.clear_regions()
        self._remove_plot_data_items()
        self._setup_plot_data_items()

    @QtCore.Slot(bool)
    def update_regions(self, visible: bool) -> None:
        """Updates IDs and visibility of regions."""
        # Start at 1 since section 0 is the base from which all others are added
        for i, region in enumerate(self.regions, start=1):
            region.section_id = i
            region.setToolTip(f"Section {i:03}")
            region.setVisible(visible)
        self._show_regions = visible

    def remove_region(self, section_index: QtCore.QModelIndex) -> None:
        """Removes a region from the plot and list of regions."""
        if section_index.row() > 0:
            for region in self.regions:
                if region.section_id == section_index.row():
                    safe_disconnect(region, region.sig_clicked, self._on_region_clicked)
                    region.setParent(None)
                    self.regions.remove(region)
                    self.pw_main.removeItem(region)

        self.update_regions(self._show_regions)

    def clear_regions(self) -> None:
        """Removes all regions from the plot and list of regions."""
        for region in self.regions:
            region.setParent(None)
            if region in self.pw_main.plotItem.items:
                safe_disconnect(region, region.sig_clicked, self._on_region_clicked)
                self.pw_main.removeItem(region)
        self.regions.clear()

    @QtCore.Slot(int)
    def _on_region_clicked(self, section_id: int) -> None:
        """Emits the `sig_section_clicked` signal when a region is clicked."""
        self.sig_section_clicked.emit(section_id)

    def show_region_selector(self, bounds: tuple[float, float]) -> None:
        """
        Shows the region selector.

        Parameters
        ----------
        bounds : tuple[float, float]
            The min and max boundaries in plot coordinates in which the region selector is allowed.
        """
        if not self.region_selector:
            return

        self.region_selector.setBounds(bounds)
        view_range = self.pw_main.plotItem.vb.viewRange()[0]
        span = view_range[1] - view_range[0]
        initial_region = (view_range[0], view_range[0] + 0.33 * span)
        self.region_selector.setRegion(initial_region)
        if self.region_selector not in self.pw_main.plotItem.items:
            self.pw_main.addItem(self.region_selector)

        self.region_selector.setVisible(True)

    def hide_region_selector(self) -> None:
        """Hides the region selector."""
        if self.region_selector:
            self.region_selector.setVisible(False)

    @QtCore.Slot(int, int)
    def mark_region(self, x1: int, x2: int) -> None:
        """
        Marks a region on the plot.

        Parameters
        ----------
        x1 : int
            Plot coordinate of the start of the region
        x2 : int
            Plot coordinate of the end of the region
        """
        brush_color = SVGColors.Aquamarine.qcolor()
        brush_color.setAlpha(50)
        brush = make_qbrush(brush_color)

        hover_brush = make_qbrush(brush_color.lighter(180))

        pen_color = SVGColors.Orange.qcolor()
        pen = make_qpen(pen_color, width=3, style=QtCore.Qt.PenStyle.DashLine)

        hover_pen = make_qpen(pen_color.darker(200), width=5, style=QtCore.Qt.PenStyle.DashLine)

        marked_region = ClickableRegionItem(
            values=(x1, x2),
            brush=brush,
            hoverBrush=hover_brush,
            pen=pen,
            hoverPen=hover_pen,
            movable=False,
        )
        marked_region.setVisible(self._show_regions)
        marked_region.setZValue(10)
        marked_region.sig_clicked.connect(self._on_region_clicked)
        self.regions.append(marked_region)
        self.pw_main.addItem(marked_region)
        self.hide_region_selector()
        self.update_regions(self._show_regions)

    def set_signal_data(self, y_data: npt.ArrayLike, clear: bool = False) -> None:
        """
        Sets the values of the signal curve.

        Parameters
        ----------
        y_data : npt.ArrayLike
            1D array of signal values
        clear : bool, optional
            Whether to clear the existing signal and peak data before setting, by default False
        """
        if self.signal_curve is None:
            return
        if clear:
            self.signal_curve.clear()
            self.clear_peaks()

        self.signal_curve.setData(y_data)
        self.pw_main.plotItem.vb.menu.autoRange()  # calling autoRange() on the vb menu ignores the region when switching to base section, not sure why but it works

    def set_rate_data(self, y_data: npt.ArrayLike, x_data: npt.ArrayLike | None = None, clear: bool = False) -> None:
        """
        Sets the values of the rate curve.

        Parameters
        ----------
        y_data : npt.ArrayLike
            1D array of rate values
        x_data : npt.ArrayLike, optional
            1D array of same length as `y_data`. If `None`, x is automatically set to `np.arange(len(y_data))`, by
            default `None`
        clear : bool, optional
            If `True`, explicitly calls `clear()` on the rate curve before setting, by default False
        """
        if self.rate_curve is None:
            return
        if clear:
            self.rate_curve.clear()

        if x_data is not None:
            self.rate_curve.setData(x_data, y_data)
        else:
            self.rate_curve.setData(y_data)

    def set_peak_data(self, x_data: npt.ArrayLike, y_data: npt.ArrayLike) -> None:
        """
        Sets the values of the peak scatter plot.

        Parameters
        ----------
        x_data : npt.ArrayLike
            1D array of x-axis positions of the peaks
        y_data : npt.ArrayLike
            1D array of y-axis positions of the peaks
        """
        if self.peak_scatter is None:
            return
        self.peak_scatter.setData(x=x_data, y=y_data)

    @QtCore.Slot()
    def clear_peaks(self) -> None:
        """Clears the peak scatter plot and rate curve."""
        if self.peak_scatter is None:
            return
        self.peak_scatter.clear()
        if self.rate_curve is not None:
            self.rate_curve.clear()
        # ? Unclear if this is a good way of forcing a redraw
        self.pw_main.invalidateScene()
        self.pw_rate.invalidateScene()

    def remove_selection_rect(self) -> None:
        vb: EditingViewBox = self.pw_main.plotItem.vb  # type: ignore
        vb.selection_box = None
        vb.mapped_selection_rect = None

    @QtCore.Slot(object, object, object)
    def _on_scatter_clicked(
        self,
        sender: pg.ScatterPlotItem,
        points: Sequence[pg.SpotItem],
        ev: "mouseEvents.MouseClickEvent",
    ) -> None:
        """
        Handles click events on the peak scatter plot.

        Removes the clicked point from the scatter plot and emits the `sig_scatter_data_changed` signal.

        Parameters
        ----------
        sender : pg.ScatterPlotItem
            The scatter plot item that was clicked. Not used.
        points : Sequence[pg.SpotItem]
            A sequence of spot items that were under the cursor when the click occurred.
        ev : mouseEvents.MouseClickEvent
            The mouse click event.
        """
        ev.accept()
        if not self.peak_scatter or len(points) == 0 or self.block_clicks:
            return

        point = points[0]
        point_x = int(point.pos().x())
        point_index = point.index()

        scatter_data: npt.NDArray[np.void] = self.peak_scatter.data  # type: ignore
        new_x = np.delete(scatter_data["x"], point_index)
        new_y = np.delete(scatter_data["y"], point_index)
        self.peak_scatter.setData(x=new_x, y=new_y)

        self.sig_scatter_data_changed.emit("remove", np.array([point_x], dtype=np.int32))

    def _nearest_extreme_point(self, pos: QtCore.QPointF) -> tuple[int | float, int | float] | None:
        """
        Returns the x and y coordinates of the nearest point on the signal curve to the given position.

        Parameters
        ----------
        pos : QtCore.QPointF
            The position to find the nearest point to

        Returns
        -------
        tuple[int | float, int | float] | None
            The x and y coordinates of the nearest point, or `None` if no point is found
        """
        if self.signal_curve is None or self.block_clicks:
            return None

        radius_px = Config.plot.click_radius

        w = h = radius_px
        px, py = self.signal_curve.curve.pixelVectors()
        px = 0 if px is None else px.length()
        py = 0 if py is None else py.length()

        w *= px
        h *= py

        x = pos.x()
        y = pos.y()

        x_data, y_data = self.signal_curve.getOriginalDataset()
        if x_data is None or y_data is None:
            return None

        mask = (x_data + w > x) & (x_data - w < x) & (y_data + h > y) & (y_data - h < y)

        if not np.any(mask):
            return None

        closest_index = np.argmin(np.abs(y_data[mask] - y))

        x_pos = x_data[mask][closest_index]
        if self.peak_scatter is not None and x_pos in self.peak_scatter.data["x"]:  # type: ignore
            return None

        return x_pos, y_data[mask][closest_index]

    @QtCore.Slot(object, object)
    def _on_curve_clicked(self, sender: pg.PlotCurveItem, ev: "mouseEvents.MouseClickEvent") -> None:
        """
        Handles click events on the signal curve.

        Searches for the nearest peak/valley to the click position. If one is found, adds it to the peak scatter plot
        and emits the `sig_scatter_data_changed` signal.

        Parameters
        ----------
        sender : pg.PlotCurveItem
            The curve item that was clicked. Not used.
        ev : mouseEvents.MouseClickEvent
            The mouse click event.
        """
        ev.accept()
        if self.block_clicks:
            logger.info("Click interaction is blocked for this section.")
            return
        if self.peak_scatter is None:
            return

        closest_extreme = self._nearest_extreme_point(ev.pos())
        if closest_extreme is None:
            logger.info("No peaks found within click radius.")
            return

        x_new, y_new = closest_extreme

        self.peak_scatter.addPoints(x=[x_new], y=[y_new])
        self.sig_scatter_data_changed.emit("add", np.array([x_new], dtype=np.int32))

    @QtCore.Slot()
    def remove_peaks_in_selection(self) -> None:
        """
        Removes all peaks in the selection rectangle from the peak scatter plot and emits the `sig_scatter_data_changed`
        signal.
        """
        # vb: EditingViewBox = self.pw_main.plotItem.vb  # type: ignore
        r = self.get_selection_area()
        if r is None or self.peak_scatter is None or self.block_clicks:
            self.remove_selection_rect()
            return

        # r = vb.mapped_selection_rect
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        scatter_x, scatter_y = self.peak_scatter.getData()

        mask = (scatter_x < rx) | (scatter_x > rx + rw) | (scatter_y < ry) | (scatter_y > ry + rh)

        self.peak_scatter.setData(x=scatter_x[mask], y=scatter_y[mask])
        self.sig_scatter_data_changed.emit("remove", scatter_x[~mask].astype(np.int32))
        self.remove_selection_rect()

    def get_selection_area(self) -> QtCore.QRectF | None:
        """
        Get the current selection rectangle.

        Returns
        -------
        QtCore.QRectF | None
            The selection rectangle, or `None` if no selection rectangle is currently active.
        """
        return self.pw_main.plotItem.vb.mapped_selection_rect  # type: ignore

    @QtCore.Slot(bool)
    def toggle_auto_scaling(self, state: bool) -> None:
        # TODO: Update implementation so that scaling and panning are independent and correctly communicated to the user
        enable = 0.99 if state else state
        self.pw_main.getPlotItem().getViewBox().enableAutoRange(pg.ViewBox.YAxis, enable=enable)  # type: ignore
        self.pw_main.getPlotItem().getViewBox().setAutoPan(y=True)
