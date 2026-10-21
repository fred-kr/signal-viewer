"""
The matplotlib figure of the Results page and the models fitted into it.

`fit_glm` and `fit_spline_gam` are plain functions over numpy arrays; `ResultPlotController` decides what to draw
(active section or every locked section) and only draws while the figure is visible.
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import attrs
import numpy as np
import numpy.typing as npt
import polars as pl
from loguru import logger
from matplotlib.ticker import FuncFormatter
from PySide6 import QtCore

from signal_viewer.constants import SECTION_INDEX_COL
from signal_viewer.enum_defs import SVGColors

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
    from sklearn.preprocessing import SplineTransformer

    from signal_viewer.sv_data.section import Section

_COLOR_RATE = SVGColors.IndianRed
_COLOR_INTERVALS = SVGColors.DodgerBlue
_COLOR_INFO = SVGColors.GoldenRod
_COLOR_SCATTER = SVGColors.SlateGray
_COLOR_FIT = SVGColors.DarkSlateGray
_COLOR_SECTION_BAND = "#000000"
_GRID_KWARGS = {"color": "#d0d0d0", "linewidth": 0.5}
_NO_RESULT_TEXT = "No results for the active section.\nMark a section as done to create its result."
_NO_LOCKED_SECTIONS_TEXT = "No locked sections yet.\nMark at least one section as done to create a result."


class ResultPlotScope(enum.StrEnum):
    """Which sections the result figure covers."""

    ActiveSection = "active"
    AllLockedSections = "all"


class ResultFitModel(enum.StrEnum):
    """Model fitted to the window-level rate against the info-column mean."""

    NoFit = "none"
    Linear = "linear"
    """Gaussian GLM with identity link: rate = a + b * x (ordinary least squares)."""
    LogLinear = "log_linear"
    """Gamma GLM with log link: rate = exp(a + b * x). The usual shape of a rate-temperature relationship."""
    Spline = "spline"
    """Spline GAM: Gamma GLM with log link on a cubic B-spline basis of x, ridge penalty chosen by cross-validation."""


@attrs.frozen
class GLMFit:
    """A fitted single-predictor GLM (`fit_glm`): `rate = intercept + slope * x`, exponentiated for the Gamma/log-link model."""

    model: ResultFitModel
    intercept: float
    slope: float
    n_points: int

    def predict(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Fitted rate at `x`."""
        eta = self.intercept + self.slope * x
        return np.exp(eta) if self.model == ResultFitModel.LogLinear else eta

    def describe(self, x_name: str) -> list[str]:
        """Short human-readable lines; `x` stands for the info column named by `x_name`."""
        if self.model == ResultFitModel.LogLinear:
            lines = [f"Gamma GLM (log link): rate = exp({self.intercept:.3g} + {self.slope:.3g}\u00b7x)"]
            if "temp" in x_name.lower():
                # Q10: factor by which the rate changes per 10 degree increase; exp(10 * slope) under a log link.
                lines.append(f"Q10 = {np.exp(10 * self.slope):.2f}  (n = {self.n_points})")
            else:
                lines.append(f"n = {self.n_points}")
            return lines
        return [f"Linear (Gaussian GLM): rate = {self.intercept:.3g} + {self.slope:.3g}\u00b7x", f"n = {self.n_points}"]


def fit_glm(x: npt.NDArray[np.float64], y: npt.NDArray[np.float64], model: ResultFitModel) -> GLMFit | None:
    """
    Fits a single-predictor GLM of `y` on `x`. Returns None when the fit is not possible (too few points, no
    spread in `x`, or non-positive responses for the Gamma family).

    Unpenalized, with an intercept. The Gamma fit uses the module's own IRLS (`_fit_pspline_gamma` with a
    zero penalty) rather than scikit-learn's `GammaRegressor`: the latter sizes a thread pool through
    `joblib.cpu_count()`, which on Windows spawns a subprocess and stalls the GUI for over a second on first use.
    """
    mask = np.isfinite(x) & np.isfinite(y)
    if model == ResultFitModel.LogLinear:
        mask &= y > 0
    x, y = x[mask], y[mask]
    if x.size < 3 or np.ptp(x) == 0:
        return None

    if model == ResultFitModel.Linear:
        slope, intercept = np.polyfit(x, y, deg=1)
        return GLMFit(model, float(intercept), float(slope), x.size)

    design = np.column_stack([np.ones_like(x), x])
    intercept, slope = _fit_pspline_gamma(design, y, np.zeros((2, 2)))
    return GLMFit(model, float(intercept), float(slope), x.size)


@attrs.frozen
class SplineGAMFit:
    """A fitted P-spline GAM (`fit_spline_gam`): B-spline basis, penalized coefficients and the fit diagnostics shown in the title."""

    basis: SplineTransformer
    coef: npt.NDArray[np.float64]
    n_knots: int
    k_auto: bool
    """Whether `n_knots` was derived from the sample size rather than given by the caller."""
    lam: float
    edf: float
    n_points: int

    def predict(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Fitted rate at `x` (linear extrapolation outside the fitted range)."""
        return np.exp(self.basis.transform(x.reshape(-1, 1)) @ self.coef)

    def describe(self, x_name: str) -> list[str]:
        """Short human-readable lines for the panel title: knots, effective degrees of freedom, penalty, n."""
        k_source = "auto" if self.k_auto else "user"
        return [
            f"P-spline GAM (Gamma, log link), k = {self.n_knots} knots ({k_source}), EDF = {self.edf:.1f}",
            f"2nd-order difference penalty, λ = {self.lam:.3g} by 5-fold CV  (n = {self.n_points})",
        ]


_SPLINE_LAMBDAS = np.logspace(-3, 5, 17)
_SPLINE_MIN_POINTS = 20
SPLINE_K_MIN = 4
"""Smallest knot count that leaves the cubic P-spline a non-trivial penalized part (n_knots + 2 coefficients)."""
SPLINE_K_MAX = 50
"""Upper bound for a user-chosen knot count; beyond this the basis is far richer than any window-mean data set."""


def _gamma_deviance(y: npt.NDArray[np.float64], mu: npt.NDArray[np.float64]) -> float:
    return float(2.0 * np.sum((y - mu) / mu - np.log(y / mu)))


def _fit_pspline_gamma(
    basis: npt.NDArray[np.float64],
    y: npt.NDArray[np.float64],
    penalty: npt.NDArray[np.float64],
    max_iter: int = 100,
    tol: float = 1e-8,
) -> npt.NDArray[np.float64]:
    """
    Penalized IRLS for a Gamma GLM with log link: minimizes deviance + coef' @ penalty @ coef.

    With the log link the Gamma working weights are constant, so every step is a penalized least-squares fit
    to the working response z = eta + (y - mu) / mu.
    """
    lhs_penalty = basis.T @ basis + penalty
    eta = basis @ np.linalg.lstsq(basis, np.log(y), rcond=None)[0]
    coef = np.zeros(basis.shape[1])
    for _ in range(max_iter):
        mu = np.exp(eta)
        z = eta + (y - mu) / mu
        coef = np.linalg.solve(lhs_penalty, basis.T @ z)
        eta_new = basis @ coef
        converged = np.max(np.abs(eta_new - eta)) < tol
        eta = eta_new
        if converged:
            break
    return coef


def fit_spline_gam(x: npt.NDArray[np.float64], y: npt.NDArray[np.float64], k: int | None = None) -> SplineGAMFit | None:
    """
    Fits a one-smooth GAM as a P-spline (Eilers & Marx): a Gamma GLM with log link on a rich cubic B-spline
    basis of `x`, with a second-order difference penalty on the coefficients. The penalty weight is chosen from
    `_SPLINE_LAMBDAS` by 5-fold cross-validated Gamma deviance, so the smoothness adapts to the data; as the
    weight grows the fit tends to the log-linear GLM.

    `k` is the basis dimension (mgcv's `k`): the number of knots of the B-spline basis, giving `k + 2`
    coefficients. With `k=None` it is derived from the sample size (one knot per ten points, 6 to 20). An
    explicit `k` is clamped to `[SPLINE_K_MIN, SPLINE_K_MAX]`. Because the penalty controls the effective
    smoothness, `k` mostly sets an upper bound on the wiggliness the fit can reach.

    Returns None with fewer than `_SPLINE_MIN_POINTS` usable points or no spread in `x`.
    """
    mask = np.isfinite(x) & np.isfinite(y) & (y > 0)
    x, y = x[mask], y[mask]
    if x.size < _SPLINE_MIN_POINTS or np.ptp(x) == 0:
        return None

    from sklearn.model_selection import KFold
    from sklearn.preprocessing import SplineTransformer

    # A deliberately rich basis; the penalty, not the knot count, controls smoothness.
    if k is None:
        n_knots = int(np.clip(x.size // 10, 6, 20))
    else:
        n_knots = int(np.clip(k, SPLINE_K_MIN, SPLINE_K_MAX))
    transformer = SplineTransformer(
        n_knots=n_knots, degree=3, knots="uniform", include_bias=True, extrapolation="linear"
    )
    x_col = x.reshape(-1, 1)
    basis = transformer.fit_transform(x_col)
    n_coef = basis.shape[1]
    diff2 = np.diff(np.eye(n_coef), n=2, axis=0)
    roughness = diff2.T @ diff2

    folds = list(KFold(n_splits=5, shuffle=True, random_state=0).split(x_col))
    cv_deviance: list[float] = []
    for lam in _SPLINE_LAMBDAS:
        total = 0.0
        for train, test in folds:
            coef = _fit_pspline_gamma(basis[train], y[train], lam * roughness)
            total += _gamma_deviance(y[test], np.exp(basis[test] @ coef))
        cv_deviance.append(total)
    lam = float(_SPLINE_LAMBDAS[int(np.argmin(cv_deviance))])

    coef = _fit_pspline_gamma(basis, y, lam * roughness)
    gram = basis.T @ basis
    edf = float(np.trace(np.linalg.solve(gram + lam * roughness, gram)))
    return SplineGAMFit(
        basis=transformer, coef=coef, n_knots=n_knots, k_auto=k is None, lam=lam, edf=edf, n_points=x.size
    )


RateFit = GLMFit | SplineGAMFit


def fit_rate_model(
    x: npt.NDArray[np.float64],
    y: npt.NDArray[np.float64],
    model: ResultFitModel,
    spline_k: int | None = None,
) -> RateFit | None:
    """
    Dispatches to the fit for `model`; None for `NoFit` and whenever the chosen fit is not possible.

    `spline_k` is the knot count for the spline GAM (None = derived from the sample size); other models ignore it.
    """
    if model == ResultFitModel.NoFit:
        return None
    if model == ResultFitModel.Spline:
        return fit_spline_gam(x, y, k=spline_k)
    return fit_glm(x, y, model)


def _format_hms(seconds: float, _pos: int | None = None) -> str:
    total = round(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


@attrs.define
class _Segment:
    """The plottable part of one locked section, with time already converted to seconds on the figure's axis."""

    label: str
    rate_t: npt.NDArray[np.float64]
    rate: npt.NDArray[np.float64]
    interval_t: npt.NDArray[np.float64]
    intervals: npt.NDArray[np.float64]
    info_mean: npt.NDArray[np.float64] | None

    @property
    def t_start(self) -> float:
        starts = [arr[0] for arr in (self.rate_t, self.interval_t) if arr.size]
        return float(min(starts)) if starts else 0.0

    @property
    def t_end(self) -> float:
        ends = [arr[-1] for arr in (self.rate_t, self.interval_t) if arr.size]
        return float(max(ends)) if ends else 0.0


def _has_result(section: Section) -> bool:
    return not section.peak_data.is_empty() and not section.rate_data.is_empty()


def _make_segment(section: Section, time_offset_samples: int) -> _Segment:
    fs = section.sampling_rate
    rate_df = section.rate_data
    peak_df = section.peak_data
    info_mean_col = f"{section.info_name}_mean" if section.info_name is not None else None

    rate_idx = rate_df.get_column(SECTION_INDEX_COL).to_numpy().astype(np.float64)
    peak_idx = peak_df.get_column(SECTION_INDEX_COL).to_numpy().astype(np.float64)

    info_mean = None
    if info_mean_col is not None and info_mean_col in rate_df.columns:
        info_mean = rate_df.get_column(info_mean_col).to_numpy().astype(np.float64)

    return _Segment(
        label=str(section.section_id.as_num()),
        rate_t=(rate_idx + time_offset_samples) / fs,
        rate=rate_df.get_column("rate_bpm").to_numpy().astype(np.float64),
        interval_t=(peak_idx[1:] + time_offset_samples) / fs,
        intervals=np.diff(peak_idx) / fs,
        info_mean=info_mean,
    )


def _mean_rate_per_info_step(segments: Sequence[_Segment]) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Pools all segments and averages the rate per 0.1 step of the info-column mean."""
    frames = [
        pl.DataFrame({"info": seg.info_mean, "rate_bpm": seg.rate}) for seg in segments if seg.info_mean is not None
    ]
    pooled = (
        pl.concat(frames)
        .drop_nulls()
        .group_by(pl.col("info").round(1))
        .agg(pl.mean("rate_bpm").alias("rate_mean"))
        .sort("info")
    )
    return pooled.get_column("info").to_numpy(), pooled.get_column("rate_mean").to_numpy()


class ResultPlotController(QtCore.QObject):
    """
    Draws section results (rate over time, peak intervals, rate against the info column) into the Matplotlib
    widget on the results page.

    Two scopes exist: the active section on its own time axis, or every locked section placed on the file's
    time axis with the sections marked. Drawing is deferred until the widget is actually visible, so changes
    while the tab is hidden cost nothing.
    """

    def __init__(
        self,
        widget: MatplotlibWidget,
        locked_sections_provider: Callable[[], Sequence[Section]],
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._widget = widget
        self._locked_sections_provider = locked_sections_provider
        self._section: Section | None = None
        self._scope = ResultPlotScope.ActiveSection
        self._fit_model = ResultFitModel.LogLinear
        self._spline_k: int | None = None
        self._dirty = False
        self._draw_placeholder(_NO_RESULT_TEXT)

    @property
    def figure(self):
        """The matplotlib `Figure` of the widget."""
        return self._widget.getFigure()

    @property
    def scope(self) -> ResultPlotScope:
        """Whether the active section or every locked section is drawn."""
        return self._scope

    def set_section(self, section: Section | None) -> None:
        """Set the active section and redraw if the widget is visible."""
        self._section = section
        self.invalidate()

    @QtCore.Slot(object)
    def set_scope(self, scope: ResultPlotScope | str) -> None:
        """Changes the scope and redraws if visible."""
        scope = ResultPlotScope(scope)
        if scope == self._scope:
            return
        self._scope = scope
        self.invalidate()

    @property
    def fit_model(self) -> ResultFitModel:
        """The model fitted into the rate-vs-info panel."""
        return self._fit_model

    @QtCore.Slot(object)
    def set_fit_model(self, model: ResultFitModel | str) -> None:
        """Changes the fitted model and redraws if visible."""
        model = ResultFitModel(model)
        if model == self._fit_model:
            return
        self._fit_model = model
        self.invalidate()

    @property
    def spline_k(self) -> int | None:
        """Knot count of the spline GAM; None lets the fit derive it from the sample size."""
        return self._spline_k

    @QtCore.Slot(object)
    def set_spline_k(self, k: int | None) -> None:
        """Sets the knot count of the spline GAM (`None` = automatic); redraws only while the spline model is selected."""
        k = None if k is None else int(k)
        if k == self._spline_k:
            return
        self._spline_k = k
        if self._fit_model == ResultFitModel.Spline:
            self.invalidate()

    def invalidate(self) -> None:
        """Mark the figure stale (e.g. after a section was locked, unlocked or deleted) and redraw if visible."""
        self._dirty = True
        self.refresh()

    def clear(self) -> None:
        """Forgets the section and shows the placeholder text (file closed)."""
        self._section = None
        self._dirty = False
        self._draw_placeholder(_NO_RESULT_TEXT)

    @QtCore.Slot()
    def refresh(self) -> None:
        """Redraw the figure if its content is stale and the widget is currently shown."""
        if not self._dirty or not self._widget.isVisible():
            return
        self._dirty = False
        try:
            if self._scope == ResultPlotScope.AllLockedSections:
                self._draw_all_locked()
            else:
                self._draw_active()
        except Exception:  # noqa: BLE001 - any drawing failure must leave the UI usable
            logger.exception("Unable to draw result plot")
            self._draw_placeholder("Unable to draw the result plot. See the log for details.")

    def _draw_active(self) -> None:
        section = self._section
        if section is None or not _has_result(section):
            self._draw_placeholder(_NO_RESULT_TEXT)
            return
        self._draw(
            segments=[_make_segment(section, time_offset_samples=0)],
            title=f"{section.section_id.pretty_name()}  |  {section.signal_name}",
            info_name=section.info_name,
            time_label="Time since section start [h:mm:ss]",
            mark_sections=False,
        )

    def _draw_all_locked(self) -> None:
        sections = [s for s in self._locked_sections_provider() if s.is_locked and _has_result(s)]
        if not sections:
            self._draw_placeholder(_NO_LOCKED_SECTIONS_TEXT)
            return
        sections.sort(key=lambda s: s.global_bounds[0])
        first = sections[0]
        self._draw(
            segments=[_make_segment(s, time_offset_samples=s.global_bounds[0]) for s in sections],
            title=f"All locked sections (n = {len(sections)})  |  {first.signal_name}",
            info_name=first.info_name,
            time_label="Time since start of file [h:mm:ss]",
            mark_sections=True,
        )

    def _draw_placeholder(self, text: str) -> None:
        fig = self.figure
        fig.clear()
        fig.set_layout_engine("constrained")
        fig.text(0.5, 0.5, text, ha="center", va="center", color="#707070")
        self._widget.draw()

    def _draw(
        self,
        segments: Sequence[_Segment],
        title: str,
        info_name: str | None,
        time_label: str,
        mark_sections: bool,
    ) -> None:
        has_info = info_name is not None and all(seg.info_mean is not None for seg in segments)
        n_peaks = sum(seg.intervals.size + 1 for seg in segments)

        fig = self.figure
        fig.clear()
        fig.set_layout_engine("constrained")
        fig.suptitle(title, fontsize=10)

        if has_info:
            grid = fig.add_gridspec(3, 2, width_ratios=[3, 2])
            ax_rate = fig.add_subplot(grid[0, 0])
            ax_info = fig.add_subplot(grid[1, 0], sharex=ax_rate)
            ax_intervals = fig.add_subplot(grid[2, 0], sharex=ax_rate)
            ax_scatter = fig.add_subplot(grid[:, 1])
        else:
            grid = fig.add_gridspec(2, 1)
            ax_rate = fig.add_subplot(grid[0, 0])
            ax_info = None
            ax_intervals = fig.add_subplot(grid[1, 0], sharex=ax_rate)
            ax_scatter = None

        time_axes: list[Axes] = [ax_rate, ax_intervals]
        if ax_info is not None:
            time_axes.insert(1, ax_info)

        # One series per panel; segments are drawn separately so no line bridges the gap between sections.
        for seg in segments:
            ax_rate.plot(seg.rate_t, seg.rate, color=_COLOR_RATE, linewidth=1.2)
            if ax_info is not None and seg.info_mean is not None:
                ax_info.plot(seg.rate_t, seg.info_mean, color=_COLOR_INFO, linewidth=1.2)
            ax_intervals.plot(
                seg.interval_t, seg.intervals, color=_COLOR_INTERVALS, linestyle="none", marker=".", markersize=3
            )

        ax_rate.set_ylabel("Rate [bpm]")
        ax_rate.set_title("Rate over time", fontsize=9, loc="left")
        if ax_info is not None:
            ax_info.set_ylabel(f"{info_name} (window mean)")
            ax_info.set_title(f"{info_name} over time", fontsize=9, loc="left")
        ax_intervals.set_ylabel("Peak interval [s]")
        ax_intervals.set_title(f"Interval between consecutive peaks (n = {n_peaks})", fontsize=9, loc="left")
        ax_intervals.set_xlabel(time_label)

        if mark_sections:
            # Alternate a faint band behind every other section and label each one on the top panel.
            for i, seg in enumerate(segments):
                if i % 2 == 1:
                    for ax in time_axes:
                        ax.axvspan(seg.t_start, seg.t_end, color=_COLOR_SECTION_BAND, alpha=0.05, linewidth=0)
                ax_rate.annotate(
                    seg.label,
                    xy=((seg.t_start + seg.t_end) / 2, 1.0),
                    xycoords=("data", "axes fraction"),
                    xytext=(0, -3),
                    textcoords="offset points",
                    ha="center",
                    va="top",
                    fontsize=7,
                    color="#505050",
                )

        for ax in time_axes:
            ax.grid(True, **_GRID_KWARGS)
            ax.xaxis.set_major_formatter(FuncFormatter(_format_hms))
            ax.spines[["top", "right"]].set_visible(False)
        for ax in time_axes[:-1]:
            ax.tick_params(labelbottom=False)
        t_min = min(seg.t_start for seg in segments) if mark_sections else 0.0
        t_max = max(seg.t_end for seg in segments)
        ax_rate.set_xlim(t_min, t_max)

        if ax_scatter is not None:
            info_all = np.concatenate([seg.info_mean for seg in segments if seg.info_mean is not None])
            rate_all = np.concatenate([seg.rate for seg in segments])
            ax_scatter.scatter(info_all, rate_all, s=10, color=_COLOR_SCATTER, alpha=0.6, linewidths=0)
            info_steps, rate_means = _mean_rate_per_info_step(segments)
            if info_steps.size > 1:
                ax_scatter.plot(
                    info_steps, rate_means, color=_COLOR_RATE, linewidth=1.2, label="Mean rate per 0.1 step"
                )
            scatter_title = f"Rate vs. {info_name}"
            if self._fit_model != ResultFitModel.NoFit:
                fit = fit_rate_model(info_all, rate_all, self._fit_model, spline_k=self._spline_k)
                if fit is None:
                    logger.warning(f"Not enough usable points to fit a {self._fit_model.name} model.")
                else:
                    x_fit = np.linspace(float(np.nanmin(info_all)), float(np.nanmax(info_all)), 200)
                    ax_scatter.plot(x_fit, fit.predict(x_fit), color=_COLOR_FIT, linewidth=1.8, label="Fitted model")
                    # The equation goes into the title: a legend entry that long would cover the data.
                    scatter_title = "\n".join([scatter_title, *fit.describe(str(info_name))])
            if ax_scatter.get_legend_handles_labels()[0]:
                ax_scatter.legend(loc="best", fontsize=8, frameon=False)
            ax_scatter.set_xlabel(f"{info_name} (window mean)")
            ax_scatter.set_ylabel("Rate [bpm]")
            ax_scatter.set_title(scatter_title, fontsize=9, loc="left")
            ax_scatter.grid(True, **_GRID_KWARGS)
            ax_scatter.spines[["top", "right"]].set_visible(False)

        self._widget.draw()
