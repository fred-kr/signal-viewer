# pyright: reportOptionalMemberAccess=false

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from loguru import logger
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from PySide6 import QtCore, QtWidgets

from signal_viewer.constants import SECTION_INDEX_COL
from signal_viewer.enum_defs import PointSymbols, SectionChange, SVGColors
from signal_viewer.sv_config import Config
from signal_viewer.sv_plots.graphic_items import (
    ClickableRegionItem,
    EditingViewBox,
    TimeDeltaAxisItem,
)
from signal_viewer.utils import make_qbrush, make_qpen, safe_disconnect

if TYPE_CHECKING:
    from pyqtgraph.GraphicsScene import mouseEvents

    from signal_viewer.sv_data.data_models import SectionListModel
    from signal_viewer.sv_data.section import Section
    from signal_viewer.sv_gui import SVGUI


class PlotController(QtCore.QObject):
    """
    Draws the active section and reports user intent.

    The plot never edits data itself: a click on a peak or on the curve only emits `sig_scatter_data_changed`, and
    the redraw comes back through `refresh_section` once the model has changed. Section regions are driven by the
    `SectionListModel` passed to `bind_section_model`; nothing else adds or removes them.
    """

    sig_scatter_data_changed = QtCore.Signal(str, object)  # (UpdatePeaksAction, section indices)
    sig_section_clicked = QtCore.Signal(object)  # the clicked Section

    def __init__(self, parent: QtCore.QObject | None, gui: SVGUI) -> None:
        super().__init__(parent)

        self._gui = gui
        self.regions: list[ClickableRegionItem] = []
        self._show_regions = False
        self._section_model: SectionListModel | None = None

        self._setup_plot_widgets()
        self._setup_plot_items()
        self._setup_plot_data_items()

        self.block_clicks = False

    def _setup_plot_widgets(self) -> None:
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(2)
        main_plot_widget = pg.PlotWidget(viewBox=EditingViewBox(name="main_plot"))
        rate_plot_widget = pg.PlotWidget(viewBox=ViewBox(name="rate_plot"))

        widget_layout.addWidget(main_plot_widget)
        widget_layout.addWidget(rate_plot_widget)
        self._gui.ui.plot_container.setLayout(widget_layout)
        self.pw_main = main_plot_widget
        self.pw_rate = rate_plot_widget
        self.vb_info = ViewBox(name="info_vb")

        self.update_views()
        self.pw_main.plotItem.vb.sigResized.connect(self.update_views)

    def _setup_plot_items(self) -> None:
        p_main = self.pw_main.getPlotItem()
        p_rate = self.pw_rate.getPlotItem()
        for plt_item in (p_main, p_rate):
            if plt_item is None:
                continue
            plt_item.setAxisItems({"top": TimeDeltaAxisItem(orientation="top")})
            plt_item.showGrid(x=False, y=True)
            plt_item.setDownsampling(auto=True)
            plt_item.setClipToView(True)
            plt_item.addLegend(colCount=3)
            plt_item.addLegend().anchor(itemPos=(0, 1), parentPos=(0, 1), offset=(5, -5))
            plt_item.setMouseEnabled(x=True, y=False)

        p_main.showAxis("right")
        p_main.scene().addItem(self.vb_info)
        p_main.getAxis("right").linkToView(self.vb_info)
        self.vb_info.setXLink(p_main)

        # self.pw_main.getPlotItem().getViewBox().enableAutoRange(ViewBox.YAxis, enable=0.99)  # pyright: ignore[reportArgumentType]
        p_main.vb.enableAutoRange(EditingViewBox.YAxis, enable=True)
        # self.pw_main.getPlotItem().getViewBox().setAutoPan(y=True)
        p_main.vb.setAutoPan(y=True)

        p_rate.vb.enableAutoRange(ViewBox.YAxis, enable=True)
        p_rate.vb.setAutoVisible(y=False)

        p_main.vb.setXLink("rate_plot")

    @QtCore.Slot()
    def update_views(self) -> None:
        p_main = self.pw_main.plotItem
        vb_info = self.vb_info

        vb_info.setGeometry(p_main.vb.sceneBoundingRect())
        vb_info.linkedViewChanged(p_main.vb, vb_info.XAxis)

    def _setup_plot_data_items(self) -> None:
        self._setup_signal_curve()
        self._setup_info_curve()
        self._setup_peak_scatter()
        self._setup_rate_curve()
        self._setup_region_selector()

    def _remove_plot_data_items(self) -> None:
        self._remove_signal_curve()
        self._remove_info_curve()
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

    def _setup_info_curve(self) -> None:
        pen = make_qpen(SVGColors.FireBrick, width=1)
        info = pg.PlotDataItem(
            pen=pen,
            skipFiniteCheck=True,
            autoDownsample=True,
            name="Info",
        )
        self.info_curve = info
        self.vb_info.addItem(self.info_curve)

    def _remove_info_curve(self) -> None:
        if self.info_curve is None:
            return
        self.vb_info.removeItem(self.info_curve)
        self.info_curve.setParent(None)
        self.info_curve = None

    def _setup_peak_scatter(self) -> None:
        brush = make_qbrush(SVGColors.GoldenRod)
        hover_brush = make_qbrush(SVGColors.Red)
        hover_pen = make_qpen(SVGColors.Black, width=1)

        scatter = pg.PlotDataItem(
            pxMode=True,
            symbolSize=10,
            pen=None,
            symbolPen=None,
            symbolBrush=brush,
            useCache=True,
            name="Peaks",
        )
        scatter.scatter.opts.update(
            {
                "hoverable": True,
                "hoverPen": hover_pen,
                "hoverSymbol": PointSymbols.Cross,
                "hoverBrush": hover_brush,
                "hoverSize": 14,
                "tip": None,
            }
        )
        scatter.setZValue(60)
        scatter.sigPointsClicked.connect(self._on_scatter_clicked)
        self.peak_scatter = scatter
        self.pw_main.addItem(self.peak_scatter)

    def _remove_peak_scatter(self) -> None:
        if self.peak_scatter is None:
            return
        self.peak_scatter.sigPointsClicked.disconnect(self._on_scatter_clicked)
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

    def _setup_region_selector(self) -> None:
        brush_col = SVGColors.LightGrey.qcolor()
        hover_brush_col = brush_col
        hover_brush_col.setAlpha(60)

        brush = make_qbrush(brush_col)
        line_pen = make_qpen(SVGColors.DarkGrey, width=3)

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
        """
        Sets the plot view limits to fit the data.

        Parameters
        ----------
        plt_data_item : pg.PlotDataItem
            The plot data item used to determine the view limits.
        """
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

        self.unbind_section_model()
        self.clear_regions()
        self._remove_plot_data_items()
        self._setup_plot_data_items()

    # --- Section regions ---------------------------------------------------------------------------------------------

    def bind_section_model(self, model: SectionListModel) -> None:
        """
        Mirrors `model` as regions on the main plot: one region per editable section, kept in sync with the model's
        row insertions, removals, renames and resets. Replaces any previous binding.
        """
        self.unbind_section_model()
        self._section_model = model
        model.rowsInserted.connect(self._on_sections_inserted)
        model.rowsAboutToBeRemoved.connect(self._on_sections_about_to_be_removed)
        model.modelReset.connect(self.clear_regions)
        model.dataChanged.connect(self._on_sections_data_changed)

        self.clear_regions()
        for section in model.editable_sections:
            self.mark_region(section)

    def unbind_section_model(self) -> None:
        model = self._section_model
        if model is None:
            return
        safe_disconnect(model, model.rowsInserted, self._on_sections_inserted)
        safe_disconnect(model, model.rowsAboutToBeRemoved, self._on_sections_about_to_be_removed)
        safe_disconnect(model, model.modelReset, self.clear_regions)
        safe_disconnect(model, model.dataChanged, self._on_sections_data_changed)
        self._section_model = None

    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def _on_sections_inserted(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        if self._section_model is None:
            return
        base = self._section_model.get_base_section()
        for row in range(first, last + 1):
            section = self._section_model.get_section(self._section_model.index(row))
            if section is not None and section is not base:
                self.mark_region(section)

    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def _on_sections_about_to_be_removed(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        if self._section_model is None:
            return
        for row in range(first, last + 1):
            section = self._section_model.get_section(self._section_model.index(row))
            if section is not None:
                self.remove_region(section)

    @QtCore.Slot(QtCore.QModelIndex, QtCore.QModelIndex, object)
    def _on_sections_data_changed(
        self, top_left: QtCore.QModelIndex, bottom_right: QtCore.QModelIndex, roles: object = None
    ) -> None:
        for region in self.regions:
            region.refresh_tooltip()

    @QtCore.Slot(bool)
    def set_regions_visible(self, visible: bool) -> None:
        for region in self.regions:
            region.setVisible(visible)
        self._show_regions = visible

    def _find_region(self, section: Section) -> ClickableRegionItem | None:
        return next((r for r in self.regions if r.section is section), None)

    def remove_region(self, section: Section) -> None:
        """Removes the region marking `section`, if there is one."""
        region = self._find_region(section)
        if region is None:
            return
        safe_disconnect(region, region.sig_clicked, self._on_region_clicked)
        self.regions.remove(region)
        self.pw_main.removeItem(region)
        region.setParent(None)

    def clear_regions(self) -> None:
        """Removes all regions from the plot and list of regions."""
        for region in self.regions:
            region.setParent(None)
            if region in self.pw_main.plotItem.items:
                safe_disconnect(region, region.sig_clicked, self._on_region_clicked)
                self.pw_main.removeItem(region)
        self.regions.clear()

    @QtCore.Slot(object)
    def _on_region_clicked(self, section: Section) -> None:
        self.sig_section_clicked.emit(section)

    def show_region_selector(
        self, bounds: tuple[float, float], selected_range: tuple[float, float] | None = None
    ) -> None:
        """
        Shows the region selector.

        Parameters
        ----------
        bounds : tuple[float, float]
            The min and max boundaries in plot coordinates in which the region selector is allowed.
        selected_range : tuple[float, float] | None or None
            The initial selected region, defaults to the lower third of the plot's x-axis.
        """
        if not self.region_selector:
            return

        self.region_selector.setBounds(bounds)
        view_range = self.pw_main.plotItem.vb.viewRange()[0]
        span = view_range[1] - view_range[0]
        initial_region = selected_range or (view_range[0], view_range[0] + 0.33 * span)
        self.region_selector.setRegion(initial_region)
        if self.region_selector not in self.pw_main.plotItem.items:
            self.pw_main.addItem(self.region_selector)

        self.region_selector.setVisible(True)

    def hide_region_selector(self) -> None:
        """Hides the region selector."""
        if self.region_selector:
            self.region_selector.setVisible(False)

    def mark_region(self, section: Section) -> None:
        """Draws a region spanning `section.global_bounds` on the main plot. Idempotent per section."""
        if self._find_region(section) is not None:
            return
        x1, x2 = section.global_bounds
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
            section=section,
        )
        marked_region.setVisible(self._show_regions)
        marked_region.setZValue(10)
        marked_region.sig_clicked.connect(self._on_region_clicked)
        self.regions.append(marked_region)
        self.pw_main.addItem(marked_region)

    def get_region_bounds(self) -> tuple[int, int]:
        """
        Returns the current bounds of the region selector.

        Returns
        -------
        tuple[float, float]
            The min and max boundaries of the region selector.
        """
        x1, x2 = int(self.region_selector.getRegion()[0]), int(self.region_selector.getRegion()[1])  # pyright: ignore[reportArgumentType]
        return x1, x2

    def refresh_section(self, section: Section, flags: SectionChange) -> None:
        """
        Redraws the parts of `section` named by `flags`.

        This is the only entry point `SVApp` uses after a model change; the individual `set_*` methods stay public for
        tests and for the initial draw.
        """
        if SectionChange.SIGNAL in flags:
            self.set_signal_data(section.processed_signal)
        if SectionChange.PEAKS in flags:
            pos = section.get_peak_pos()
            self.set_peak_data(pos.get_column(SECTION_INDEX_COL), pos.get_column(section.processed_signal_name))
        if SectionChange.RATE in flags:
            rate = section.rate_data
            if rate.is_empty() or "rate_bpm" not in rate.columns:
                if self.rate_curve is not None:
                    self.rate_curve.clear()
            else:
                self.set_rate_data(x_data=rate.get_column(SECTION_INDEX_COL), y_data=rate.get_column("rate_bpm"))
        if SectionChange.LOCK in flags:
            # The base section is created locked, so this also blocks edits on it.
            self.block_clicks = section.is_locked

    def set_signal_data(self, y_data: npt.ArrayLike, clear: bool = False) -> None:
        """
        Sets the values of the signal curve.

        Parameters
        ----------
        y_data : ArrayLike
            1D array of signal values
        clear : bool, default False
            Whether to clear the existing signal and peak data before setting, by default False
        """
        if self.signal_curve is None:
            return
        if clear:
            self.signal_curve.clear()
            self.clear_peaks()

        self.signal_curve.setData(y_data)
        self.pw_main.plotItem.vb.menu.autoRange()  # calling autoRange() on the vb menu ignores the region when switching to base section, not sure why but it works

    def set_info_data(self, y_data: npt.ArrayLike, clear: bool = False) -> None:
        """
        Sets the values of the info curve.

        Parameters
        ----------
        y_data : ArrayLike
            1D array of info values
        clear : bool, default False
            Whether to clear the existing info data before setting, by default False
        """
        if self.info_curve is None:
            return
        if clear:
            self.info_curve.clear()

        self.info_curve.setData(y_data)
        self.pw_main.plotItem.vb.menu.autoRange()

    def set_rate_data(self, y_data: npt.ArrayLike, x_data: npt.ArrayLike | None = None, clear: bool = False) -> None:
        """
        Sets the values of the rate curve.

        Parameters
        ----------
        y_data : ArrayLike
            1D array of rate values
        x_data : ArrayLike or None, default None
            1D array of same length as `y_data`. If `None`, x is automatically set to `np.arange(len(y_data))`, by
            default `None`
        clear : bool, default False
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
        x_data : ArrayLike
            1D array of x-axis positions of the peaks
        y_data : ArrayLike
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
        sender: pg.PlotDataItem,
        points: Sequence[pg.SpotItem],
        ev: mouseEvents.MouseClickEvent,
    ) -> None:
        """
        Handles click events on the peak scatter plot.

        Emits `sig_scatter_data_changed("remove", [x])` for the clicked point. The scatter itself is redrawn by
        `refresh_section` once the model has removed the peak.

        Parameters
        ----------
        sender : pg.PlotDataItem
            The scatter plot item that was clicked. Not used.
        points : Sequence[pg.SpotItem]
            A sequence of spot items that were under the cursor when the click occurred.
        ev : mouseEvents.MouseClickEvent
            The mouse click event.
        """
        ev.accept()
        if not self.peak_scatter or len(points) == 0 or self.block_clicks:
            return

        point_x = int(points[0].pos().x())
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
        if self.peak_scatter is not None:
            peak_x, _ = self.peak_scatter.getOriginalDataset()
            if peak_x is not None and x_pos in peak_x:
                return None

        return x_pos, y_data[mask][closest_index]

    @QtCore.Slot(object, object)
    def _on_curve_clicked(self, sender: pg.PlotCurveItem, ev: mouseEvents.MouseClickEvent) -> None:
        """
        Handles click events on the signal curve.

        Searches for the nearest peak/valley to the click position. If one is found, emits
        `sig_scatter_data_changed("add", [x])`. The scatter is redrawn by `refresh_section` once the model has added
        the peak.

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

        x_new, _ = closest_extreme
        self.sig_scatter_data_changed.emit("add", np.array([x_new], dtype=np.int32))

    @QtCore.Slot()
    def remove_peaks_in_selection(self) -> None:
        """
        Emits `sig_scatter_data_changed("remove", xs)` for every peak inside the selection rectangle, then clears the
        rectangle.
        """
        r = self.get_selection_area()
        if r is None or self.peak_scatter is None or self.block_clicks:
            self.remove_selection_rect()
            return

        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        # The full peak set, not `self.peak_scatter.scatter.getData()`: the child scatter holds the auto-downsampled
        # points, so when zoomed out it misses most peaks inside the rectangle.
        scatter_x, scatter_y = self.peak_scatter.getOriginalDataset()
        if scatter_x is None or scatter_y is None:
            self.remove_selection_rect()
            return

        inside = (scatter_x >= rx) & (scatter_x <= rx + rw) & (scatter_y >= ry) & (scatter_y <= ry + rh)

        self.remove_selection_rect()
        if np.any(inside):
            self.sig_scatter_data_changed.emit("remove", scatter_x[inside].astype(np.int32))

    def get_selection_area(self) -> QtCore.QRectF | None:
        """
        Get the current selection rectangle.

        Returns
        -------
        QtCore.QRectF | None
            The selection rectangle, or `None` if no selection rectangle is currently active.
        """
        return self.pw_main.plotItem.vb.mapped_selection_rect  # type: ignore

    @QtCore.Slot()
    def fit_y_axis(self) -> None:
        # TODO: Update implementation so that scaling and panning are independent and correctly communicated to the user
        # enable = 0.99
        # self.pw_main.getPlotItem().getViewBox().enableAutoRange(pg.ViewBox.YAxis, enable=enable)  # type: ignore
        self.pw_main.getPlotItem().getViewBox().autoRange()
        # self.pw_main.plotItem.vb.menu.autoRange()
