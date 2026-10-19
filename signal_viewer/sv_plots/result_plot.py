from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from loguru import logger
from matplotlib.ticker import FuncFormatter
from PySide6 import QtCore

from signal_viewer.constants import SECTION_INDEX_COL
from signal_viewer.enum_defs import SVGColors

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

    from signal_viewer.sv_data.section import Section

_COLOR_RATE = SVGColors.IndianRed
_COLOR_INTERVALS = SVGColors.DodgerBlue
_COLOR_INFO = SVGColors.GoldenRod
_COLOR_SCATTER = SVGColors.SlateGray
_GRID_KWARGS = {"color": "#d0d0d0", "linewidth": 0.5}
_NO_RESULT_TEXT = "No results for the active section.\nMark a section as done to create its result."


def _format_hms(seconds: float, _pos: int | None = None) -> str:
    total = round(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


class ResultPlotController(QtCore.QObject):
    """
    Draws the result of a locked section (rate over time, peak intervals, rate against the info column)
    into the Matplotlib widget on the results page.

    Drawing is deferred until the widget is actually visible, so switching sections while the tab is hidden
    costs nothing.
    """

    def __init__(self, widget: MatplotlibWidget, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._widget = widget
        self._section: Section | None = None
        self._dirty = False
        self._draw_placeholder(_NO_RESULT_TEXT)

    @property
    def figure(self):
        return self._widget.getFigure()

    def set_section(self, section: Section | None) -> None:
        """Set the section whose result should be shown and redraw if the widget is visible."""
        self._section = section
        self._dirty = True
        self.refresh()

    def clear(self) -> None:
        self._section = None
        self._dirty = False
        self._draw_placeholder(_NO_RESULT_TEXT)

    @QtCore.Slot()
    def refresh(self) -> None:
        """Redraw the figure if its content is stale and the widget is currently shown."""
        if not self._dirty or not self._widget.isVisible():
            return
        self._dirty = False
        section = self._section
        if section is None or section.peak_data.is_empty() or section.rate_data.is_empty():
            self._draw_placeholder(_NO_RESULT_TEXT)
            return
        try:
            self._draw_section(section)
        except Exception:  # noqa: BLE001 - any drawing failure must leave the UI usable
            logger.exception("Unable to draw result plot")
            self._draw_placeholder("Unable to draw the result plot. See the log for details.")

    def _draw_placeholder(self, text: str) -> None:
        fig = self.figure
        fig.clear()
        fig.set_layout_engine("constrained")
        fig.text(0.5, 0.5, text, ha="center", va="center", color="#707070")
        self._widget.draw()

    def _draw_section(self, section: Section) -> None:
        fs = section.sampling_rate
        rate_df = section.rate_data
        peak_df = section.peak_data
        info_mean_col = f"{section.info_name}_mean" if section.info_name is not None else None
        has_info = info_mean_col is not None and info_mean_col in rate_df.columns

        rate_t = rate_df.get_column(SECTION_INDEX_COL).to_numpy() / fs
        rate = rate_df.get_column("rate_bpm").to_numpy()

        peak_idx = peak_df.get_column(SECTION_INDEX_COL).to_numpy()
        interval_t = peak_idx[1:] / fs
        intervals = np.diff(peak_idx) / fs

        fig = self.figure
        fig.clear()
        fig.set_layout_engine("constrained")
        fig.suptitle(f"{section.section_id.pretty_name()}  |  {section.signal_name}", fontsize=10)

        n_rows = 3 if has_info else 2
        if has_info:
            grid = fig.add_gridspec(n_rows, 2, width_ratios=[3, 2])
            ax_rate = fig.add_subplot(grid[0, 0])
            ax_info = fig.add_subplot(grid[1, 0], sharex=ax_rate)
            ax_intervals = fig.add_subplot(grid[2, 0], sharex=ax_rate)
            ax_scatter = fig.add_subplot(grid[:, 1])
        else:
            grid = fig.add_gridspec(n_rows, 1)
            ax_rate = fig.add_subplot(grid[0, 0])
            ax_info = None
            ax_intervals = fig.add_subplot(grid[1, 0], sharex=ax_rate)
            ax_scatter = None

        time_axes: list[Axes] = [ax_rate, ax_intervals]

        ax_rate.plot(rate_t, rate, color=_COLOR_RATE, linewidth=1.2)
        ax_rate.set_ylabel("Rate [bpm]")
        ax_rate.set_title("Rate over time", fontsize=9, loc="left")

        if ax_info is not None and info_mean_col is not None:
            info_mean = rate_df.get_column(info_mean_col).to_numpy()
            ax_info.plot(rate_t, info_mean, color=_COLOR_INFO, linewidth=1.2)
            ax_info.set_ylabel(f"{section.info_name} (window mean)")
            ax_info.set_title(f"{section.info_name} over time", fontsize=9, loc="left")
            time_axes.insert(1, ax_info)

        ax_intervals.plot(interval_t, intervals, color=_COLOR_INTERVALS, linestyle="none", marker=".", markersize=3)
        ax_intervals.set_ylabel("Peak interval [s]")
        ax_intervals.set_title(f"Interval between consecutive peaks (n = {peak_idx.size})", fontsize=9, loc="left")
        ax_intervals.set_xlabel("Time since section start [h:mm:ss]")

        for ax in time_axes:
            ax.grid(True, **_GRID_KWARGS)
            ax.xaxis.set_major_formatter(FuncFormatter(_format_hms))
            ax.spines[["top", "right"]].set_visible(False)
        for ax in time_axes[:-1]:
            ax.tick_params(labelbottom=False)
        ax_rate.set_xlim(
            0, max(float(rate_t[-1]) if rate_t.size else 0.0, float(interval_t[-1]) if interval_t.size else 0.0)
        )

        if ax_scatter is not None and info_mean_col is not None:
            info_mean = rate_df.get_column(info_mean_col).to_numpy()
            ax_scatter.scatter(info_mean, rate, s=10, color=_COLOR_SCATTER, alpha=0.6, linewidths=0)
            per_info = section.get_mean_rate_per_temperature()
            if info_mean_col in per_info.columns and per_info.height > 1:
                ax_scatter.plot(
                    per_info.get_column(info_mean_col).to_numpy(),
                    per_info.get_column("rate_mean").to_numpy(),
                    color=_COLOR_RATE,
                    linewidth=1.5,
                    label="Mean rate per 0.1 step",
                )
                ax_scatter.legend(loc="best", fontsize=8, frameon=False)
            ax_scatter.set_xlabel(f"{section.info_name} (window mean)")
            ax_scatter.set_ylabel("Rate [bpm]")
            ax_scatter.set_title(f"Rate vs. {section.info_name}", fontsize=9, loc="left")
            ax_scatter.grid(True, **_GRID_KWARGS)
            ax_scatter.spines[["top", "right"]].set_visible(False)

        self._widget.draw()
