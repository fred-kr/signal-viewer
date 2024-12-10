import typing as t

import numpy as np
import numpy.typing as npt
import polars as pl
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.sv_config import Config
from signal_viewer.enum_defs import PointSymbols, SVGColors
from signal_viewer.sv_plots.graphic_items import ClickableRegionItem, CustomScatterPlotItem, EditingViewBox, TimeAxisItem
from signal_viewer.utils import make_qbrush, make_qcolor, make_qpen, safe_disconnect

if t.TYPE_CHECKING:
    from pyqtgraph.GraphicsScene import mouseEvents

    from signal_viewer.sv_gui import SVGui


class PlotController(QtCore.QObject):
    sig_scatter_data_changed = QtCore.Signal(str, object)
    sig_section_clicked = QtCore.Signal(int)

    def __init__(
        self,
        parent: QtCore.QObject | None,
        main_window: "SVGui",
    ) -> None:
        super().__init__(parent)

        self._mw_ref = main_window
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
        self._mw_ref.plot_container.setLayout(widget_layout)
        self.pw_main = main_plot_widget
        self.pw_rate = rate_plot_widget
        self.mpw_result = self._mw_ref.mpl_widget

    def _setup_plot_items(self) -> None:
        for plt_item in (self.pw_main.getPlotItem(), self.pw_rate.getPlotItem()):
            vb = plt_item.getViewBox()
            plt_item.setAxisItems({"top": TimeAxisItem(orientation="top")})
            plt_item.showGrid(x=False, y=True)
            plt_item.setDownsampling(auto=True)
            plt_item.setClipToView(True)
            plt_item.addLegend(colCount=2)
            plt_item.addLegend().anchor(itemPos=(0, 1), parentPos=(0, 1), offset=(5, -5))
            plt_item.setMouseEnabled(x=True, y=False)
            vb.enableAutoRange("y", enable=0.99)
            vb.setAutoVisible(y=False)

        self.pw_main.getPlotItem().getViewBox().setXLink("rate_plot")

        self.set_background_color(Config.plot.background_color)
        self.set_foreground_color(Config.plot.foreground_color)

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

    def remove_region_selector(self) -> None:
        """
        Remove the region selector from the main plot widget.
        """
        if self.region_selector:
            self.pw_main.removeItem(self.region_selector)
            self.region_selector.setParent(None)
            self.region_selector = None

    def _setup_plot_data_items(self) -> None:
        self._init_signal_curve()
        self._init_peak_scatter()
        self._init_rate_curve()
        self._setup_region_selector()

    def _init_signal_curve(self) -> None:
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

    def remove_signal_curve(self) -> None:
        if self.signal_curve is None:
            return
        self.signal_curve.sigClicked.disconnect(self._on_curve_clicked)
        self.signal_curve.sigPlotChanged.disconnect(self.set_view_limits)
        self.pw_main.removeItem(self.signal_curve)
        self.signal_curve.setParent(None)
        self.signal_curve = None

    def _init_peak_scatter(
        self,
    ) -> None:
        brush = make_qbrush(SVGColors.GoldenRod)
        hover_brush = make_qbrush(SVGColors.Red)
        hover_pen = make_qpen(SVGColors.Black, width=1)

        scatter = CustomScatterPlotItem(
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

    def remove_peak_scatter(self) -> None:
        if self.peak_scatter is None:
            return
        self.peak_scatter.sigClicked.disconnect(self._on_scatter_clicked)
        self.pw_main.removeItem(self.peak_scatter)
        self.peak_scatter.setParent(None)
        self.peak_scatter = None

    def _init_rate_curve(self) -> None:
        pen = make_qpen(SVGColors.IndianRed, width=1)
        rate_curve = pg.PlotDataItem(
            pen=pen,
            skipFiniteCheck=True,
            autoDownsample=True,
            name="Rate",
        )
        self.rate_curve = rate_curve
        self.pw_rate.addItem(self.rate_curve)

    def remove_rate_curve(self) -> None:
        if self.rate_curve is None:
            return
        self.pw_rate.removeItem(self.rate_curve)
        self.rate_curve.setParent(None)
        self.rate_curve = None

    def remove_plot_data_items(self) -> None:
        self.remove_signal_curve()
        self.remove_peak_scatter()
        self.remove_rate_curve()
        self.remove_region_selector()

    @QtCore.Slot(int)
    def update_time_axis_scale(self, sampling_rate: int) -> None:
        if sampling_rate == 0:
            return
        for plt_item in (self.pw_main.getPlotItem(), self.pw_rate.getPlotItem()):
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
        self.pw_main.clear()
        if self.pw_main.plotItem.legend:
            self.pw_main.plotItem.legend.clear()
        self.pw_rate.clear()
        if self.pw_rate.plotItem.legend:
            self.pw_rate.plotItem.legend.clear()

        self.mpw_result.fig.clear()

        self.clear_regions()
        self.remove_plot_data_items()
        self._setup_plot_data_items()

    @QtCore.Slot(bool)
    def toggle_regions(self, visible: bool) -> None:
        # Start at 1 since section 0 is the base from which all others are added
        for i, region in enumerate(self.regions, start=1):
            region.section_id = i
            region.setToolTip(f"Section {i:03}")
            region.setVisible(visible)
        self._show_regions = visible

    def remove_region(self, section_index: QtCore.QModelIndex) -> None:
        if section_index.row() > 0:
            for region in self.regions:
                if region.section_id == section_index.row():
                    safe_disconnect(region, region.sig_clicked, self._on_region_clicked)
                    region.setParent(None)
                    self.regions.remove(region)
                    self.pw_main.removeItem(region)

        self.toggle_regions(self._show_regions)

    def clear_regions(self) -> None:
        for region in self.regions:
            region.setParent(None)
            if region in self.pw_main.plotItem.items:
                safe_disconnect(region, region.sig_clicked, self._on_region_clicked)
                self.pw_main.removeItem(region)
        self.regions.clear()

    @QtCore.Slot(int)
    def _on_region_clicked(self, section_id: int) -> None:
        self.sig_section_clicked.emit(section_id)

    def show_region_selector(self, bounds: tuple[float, float]) -> None:
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
        if self.region_selector:
            self.region_selector.setVisible(False)

    @QtCore.Slot(int, int)
    def mark_region(self, x1: int, x2: int) -> None:
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
        self.toggle_regions(self._show_regions)

    def set_signal_data(self, y_data: npt.NDArray[np.float64] | pl.Series, clear: bool = False) -> None:
        if self.signal_curve is None:
            return
        if clear:
            self.signal_curve.clear()
            self.clear_peaks()

        self.signal_curve.setData(y_data)

    def set_rate_data(
        self,
        y_data: npt.NDArray[np.float64 | np.intp] | pl.Series,
        x_data: npt.NDArray[np.intp] | pl.Series | None = None,
        clear: bool = False,
    ) -> None:
        if self.rate_curve is None:
            return
        if clear:
            self.rate_curve.clear()

        if x_data is not None:
            self.rate_curve.setData(x_data, y_data)
        else:
            self.rate_curve.setData(y_data)

    def set_peak_data(
        self, x_data: npt.NDArray[np.intp | np.uintp] | pl.Series, y_data: npt.NDArray[np.float64] | pl.Series
    ) -> None:
        if self.peak_scatter is None:
            return
        self.peak_scatter.setData(x=x_data, y=y_data)

    @QtCore.Slot()
    def clear_peaks(self) -> None:
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
        sender: CustomScatterPlotItem,
        points: t.Sequence[pg.SpotItem],
        ev: "mouseEvents.MouseClickEvent",
    ) -> None:
        ev.accept()
        if not self.peak_scatter or len(points) == 0 or self.block_clicks:
            return

        point = points[0]
        point_x = int(point.pos().x())
        point_index = point.index()

        scatter_data = self.peak_scatter.data
        new_x = np.delete(scatter_data["x"], point_index)
        new_y = np.delete(scatter_data["y"], point_index)
        self.peak_scatter.setData(x=new_x, y=new_y)

        self.sig_scatter_data_changed.emit("remove", np.array([point_x], dtype=np.int32))

    @QtCore.Slot(object, object)
    def _on_curve_clicked(self, sender: pg.PlotCurveItem, ev: "mouseEvents.MouseClickEvent") -> None:
        ev.accept()
        if self.signal_curve is None or self.peak_scatter is None or self.block_clicks:
            return

        click_x = int(ev.pos().x())
        click_y = ev.pos().y()
        x_data = self.signal_curve.xData
        y_data = self.signal_curve.yData
        if x_data is None or y_data is None:
            return

        scatter_search_radius = Config.plot.click_radius

        left_index = np.searchsorted(x_data, click_x - scatter_search_radius, side="left")
        right_index = np.searchsorted(x_data, click_x + scatter_search_radius, side="right")

        valid_x = x_data[left_index:right_index]
        valid_y = y_data[left_index:right_index]

        # Find the index of the nearest extreme point to the click position
        extreme_index = left_index + np.argmin(np.abs(valid_x - click_x))
        extreme_value = valid_y[np.argmin(np.abs(valid_x - click_x))]

        # Find the index of the nearest extreme point to the click position in the y direction
        extreme_index_y = left_index + np.argmin(np.abs(valid_y - click_y))
        extreme_value_y = valid_y[np.argmin(np.abs(valid_y - click_y))]

        # Use the index of the nearest extreme point in the y direction if it is closer to the click position
        if np.abs(extreme_value_y - click_y) < np.abs(extreme_value - click_y):
            extreme_index = extreme_index_y
            extreme_value = extreme_value_y

        if extreme_index in self.peak_scatter.data["x"]:
            return

        x_new, y_new = x_data[extreme_index], extreme_value
        self.peak_scatter.addPoints(x=x_new, y=y_new)
        self.sig_scatter_data_changed.emit("add", np.array([x_new], dtype=np.int32))

    @QtCore.Slot()
    def remove_peaks_in_selection(self) -> None:
        vb: EditingViewBox = self.pw_main.plotItem.vb  # type: ignore
        if vb.mapped_selection_rect is None or self.peak_scatter is None or self.block_clicks:
            self.remove_selection_rect()
            return

        r = vb.mapped_selection_rect
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        scatter_x, scatter_y = self.peak_scatter.getData()

        mask = (scatter_x < rx) | (scatter_x > rx + rw) | (scatter_y < ry) | (scatter_y > ry + rh)

        self.peak_scatter.setData(x=scatter_x[mask], y=scatter_y[mask])
        self.sig_scatter_data_changed.emit("remove", scatter_x[~mask].astype(np.int32))
        self.remove_selection_rect()

    def get_selection_area(self) -> QtCore.QRectF | None:
        return self.pw_main.plotItem.vb.mapped_selection_rect  # type: ignore

    def set_background_color(self, color: str | QtGui.QColor) -> None:
        self.pw_main.setBackground(make_qcolor(color))
        self.pw_rate.setBackground(make_qcolor(color))

    def set_foreground_color(self, color: str | QtGui.QColor) -> None:
        color = make_qcolor(color)
        for ax in {"left", "top", "right", "bottom"}:
            edit_axis = self.pw_main.plotItem.getAxis(ax)
            rate_axis = self.pw_rate.plotItem.getAxis(ax)

            if edit_axis.isVisible():
                edit_axis.setPen(color)
                edit_axis.setTextPen(color)
            if rate_axis.isVisible():
                rate_axis.setPen(color)
                rate_axis.setTextPen(color)

    def apply_settings(self) -> None:
        bg_color = make_qcolor(Config.plot.background_color)
        fg_color = make_qcolor(Config.plot.foreground_color)

        self.set_background_color(bg_color)
        self.set_foreground_color(fg_color)

    @QtCore.Slot(bool)
    def toggle_auto_scaling(self, state: bool) -> None:
        self.pw_main.enableAutoRange(y=state)
        self.pw_rate.enableAutoRange(y=state)
