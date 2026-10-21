"""
User-facing help texts of the parameter dock, and the code that puts them on the widgets.

Every input of `ParameterInputs` has one entry in `HELP_TEXTS`, keyed by the widget's object name in
`generated/param_inputs.ui` (or the attribute name of a command-bar action). `apply_help_texts` turns an entry into
the widget's tooltip and What's This text, repeats both on the widget's label, appends the default value and range
read from the spin box itself (so the numbers cannot drift from the code in `ParameterInputs._setup_widgets`), and
shows the unit as the spin box suffix.

The reference page `doc/reference/dock_parameters.html` describes the same inputs in the same words. Its row
anchors are the keys of `HELP_TEXTS` with `-` in place of `_`; the "Open the user guide" link that ends every What's
This text points there through the `help:` scheme, which `sv_help.HelpController` resolves to a page of the bundled
guide. `tests/test_help_texts.py` checks that every input has an entry and every entry names a real widget.
"""

from __future__ import annotations

import decimal
import inspect
from typing import TYPE_CHECKING

import attrs
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import DecimalSpinBox, EnumComboBox

if TYPE_CHECKING:
    from signal_viewer.sv_widgets.dock_param_inputs import ParameterInputs

HELP_URL_SCHEME = "help:"
"""Prefix of a link in a What's This text that opens a page of the bundled user guide (`sv_help.HelpController`)."""

PARAMETER_REFERENCE_PAGE = "reference/dock_parameters.html"
"""Help page that documents every input of the parameter dock, one anchored row per `HELP_TEXTS` key."""

_BOUND_PROPERTY = "helpTextTooltipBound"


def help_url(page: str, anchor: str = "") -> str:
    """A `help:` link to `page` (relative to `DOCDIR`), optionally scrolled to `anchor`."""
    return f"{HELP_URL_SCHEME}{page}#{anchor}" if anchor else f"{HELP_URL_SCHEME}{page}"


def enum_doc(member: object) -> str:
    """The member's own description (see `enum_defs.DocumentedStrEnum`), or an empty string."""
    return inspect.getdoc(member) or ""


def anchor_for(widget_name: str) -> str:
    """Anchor of `widget_name`'s row on the parameter reference page."""
    return widget_name.replace("_", "-")


@attrs.frozen
class HelpText:
    """Help texts of one input. Plain text; `apply_help_texts` wraps it in the HTML Qt needs for word wrapping."""

    tooltip: str
    """One to three sentences: what the input does and how to choose a value."""
    whats_this: str = ""
    """Longer explanation for What's This mode. Defaults to `tooltip`."""
    unit: str = ""
    """Unit shown as the spin box suffix and after the default/range numbers, e.g. "s", "Hz", "samples"."""
    minimum_means: str = ""
    """What the minimum value stands for when it is a sentinel rather than a real value."""
    label: str = ""
    """Object name of the input's label when `QFormLayout.labelForField` cannot find it (grid layouts)."""
    page: str = PARAMETER_REFERENCE_PAGE
    """Help page the What's This link opens."""


_RADIUS = (
    "Half-width of the search window in samples. A sample is a peak when it is the {extreme} value within this many "
    "samples on either side; peaks closer together than the radius are merged into one. When a file is loaded the "
    "default is set to half the sampling rate; values between a quarter and three times the sampling rate are "
    "worth trying, as is running the detection on the unprocessed signal."
)

HELP_TEXTS: dict[str, HelpText] = {
    # --- Preprocessing tab ---------------------------------------------------------------------------------------
    "action_sf_run": HelpText(
        "Apply the selected processing steps to the raw signal of the active section. Earlier processing and all "
        "peaks are discarded first."
    ),
    "action_sf_reset_inputs": HelpText(
        "Restore the default values of the pipeline, filter and standardization inputs."
    ),
    "action_sf_reset_data": HelpText(
        "Restore the raw signal of the active section. Every processing step and every peak is removed."
    ),
    "status_pipeline": HelpText("Checked while the signal of the active section was cleaned with a pipeline."),
    "status_filter": HelpText(
        "Checked while the signal of the active section is filtered. The tooltip counts the filters applied in turn."
    ),
    "status_standardization": HelpText("Checked while the signal of the active section is standardized."),
    "sf_pipeline": HelpText(
        "Ready-made cleaning pipeline from neurokit2. The tooltip of each entry names the filters it applies. "
        "Selecting a pipeline disables the custom filter and standardization inputs below; choose the empty entry "
        "to use them.",
        label="label",
    ),
    "sf_method": HelpText(
        "Filter applied to the raw signal when no pipeline is selected. Each method uses a different subset of the "
        "filter parameters; inputs the method does not use are disabled.",
        label="label_2",
    ),
    "sf_lower_cutoff": HelpText(
        "Lower cutoff frequency. Frequencies below it are removed (the high-pass part of a band-pass). 0 means no "
        "lower cutoff. Used by the Butterworth, Bessel and FIR methods.",
        unit="Hz",
    ),
    "sf_upper_cutoff": HelpText(
        "Upper cutoff frequency. Frequencies above it are removed (the low-pass part of a band-pass). 0 means no "
        "upper cutoff. Used by the Butterworth, Bessel and FIR methods.",
        unit="Hz",
    ),
    "sf_order": HelpText(
        "Filter order. Higher orders cut off more sharply but can ring near steep edges; 2 to 5 is typical. For "
        "Savitzky-Golay it is the degree of the fitted polynomial. Used by the Butterworth, Bessel and "
        "Savitzky-Golay methods."
    ),
    "sf_window_size": HelpText(
        "Window length for the FIR filter (number of taps) and for Savitzky-Golay smoothing. Longer windows smooth "
        "more. Used by the FIR and Savitzky-Golay methods.",
        unit="samples",
        minimum_means="The minimum value stands for the neurokit2 default, about a third of a second of samples.",
    ),
    "sf_powerline": HelpText(
        "Mains frequency to remove: 50 Hz in Europe and most of the world, 60 Hz in North America. Used by the "
        "Powerline method only.",
        unit="Hz",
    ),
    "std_method": HelpText(
        "Rescales the filtered signal to zero centre and unit spread, which makes the amplitude thresholds of the "
        "peak detectors comparable between recordings. Applied after the filter.",
        label="label_8",
    ),
    "std_rolling_window": HelpText(
        "Compute the mean and standard deviation inside a moving window instead of over the whole section. Removes "
        "slow drift of baseline and amplitude. Z-score only."
    ),
    "std_window_size": HelpText(
        "Length of the moving window for rolling standardization. Should span several beats; a few seconds of "
        "samples is a good start.",
        unit="samples",
    ),
    # --- Peak detection tab --------------------------------------------------------------------------------------
    "action_peak_run": HelpText(
        "Run the selected detection method on the processed signal of the active section. Existing peaks, including "
        "manual edits, are replaced."
    ),
    "action_peak_reset_inputs": HelpText("Restore the default parameter values of the selected detection method."),
    "action_peak_reset_data": HelpText("Remove every peak of the active section. The processed signal is kept."),
    "peak_method": HelpText(
        "Algorithm used to find peaks in the processed signal. The tooltip of each entry describes the method; the "
        "inputs below change with the selection. The same method is used by Find Peaks in Selection (Ctrl+F).",
        label="detectionMethodLabel",
    ),
    "peak_ppg_elgendi_peakwindow": HelpText(
        "Length of the moving average that smooths the squared signal to bring out systolic peaks. About the "
        "duration of one systolic peak.",
        unit="s",
    ),
    "peak_ppg_elgendi_beatwindow": HelpText(
        "Length of the moving average that follows whole beats. About the duration of one heartbeat; it forms the "
        "threshold the peak average has to exceed.",
        unit="s",
    ),
    "peak_ppg_elgendi_beatoffset": HelpText(
        "Fraction of the mean of the squared signal that is added to the beat average to form the detection "
        "threshold. Larger values reject smaller peaks."
    ),
    "peak_ppg_elgendi_mindelay": HelpText(
        "Minimum time between two peaks. Of two peaks closer than this, the later one is dropped. 0.3 s corresponds "
        "to 200 beats per minute.",
        unit="s",
    ),
    "peak_localmax_radius": HelpText(_RADIUS.format(extreme="highest"), unit="samples"),
    "peak_localmin_radius": HelpText(_RADIUS.format(extreme="lowest"), unit="samples"),
    "peak_xqrs_direction": HelpText(
        "Where each QRS location found by XQRS is moved within the search radius: to the highest sample, the lowest, "
        "the largest absolute value, or whichever of the first two fits the recording better."
    ),
    "peak_xqrs_radius": HelpText(
        "Samples searched on either side of every XQRS location for the actual peak.",
        unit="samples",
    ),
    "peak_xqrs_min_dist": HelpText(
        "Minimum distance between two peaks. Of two closer peaks the smaller one is dropped; afterwards peaks whose "
        "amplitude is far from that of their neighbours are removed as well.",
        unit="samples",
    ),
    "peak_ecg_nk_smoothwindow": HelpText(
        "Length of the moving average that smooths the absolute gradient of the signal. The neurokit2 default is "
        "0.1 s.",
        unit="s",
    ),
    "peak_ecg_nk_avgwindow": HelpText(
        "Length of the moving average that tracks the local level of the smoothed gradient. The detection threshold "
        "follows it.",
        unit="s",
    ),
    "peak_ecg_nk_gradthreshweight": HelpText(
        "Factor applied to the averaged gradient to form the QRS threshold. Larger values demand steeper QRS "
        "complexes and reject more candidates."
    ),
    "peak_ecg_nk_minlenweight": HelpText(
        "QRS candidates shorter than this fraction of the mean candidate length are rejected."
    ),
    "peak_ecg_nk_mindelay": HelpText(
        "Minimum time between two R-peaks. 0.3 s corresponds to 200 beats per minute.",
        unit="s",
    ),
    "peak_ecg_gamboa_tol": HelpText(
        "Tolerance of the histogram-based amplitude threshold, as a fraction of the amplitude range. Gamboa (2008) "
        "uses 0.002."
    ),
    "peak_ecg_emrich_window_seconds": HelpText(
        "Length of the segments the signal is cut into before each is turned into a visibility graph.",
        unit="s",
    ),
    "peak_ecg_emrich_window_overlap": HelpText(
        "Overlap of consecutive segments as a fraction of the segment length (0.5 = half a segment)."
    ),
    "peak_ecg_emrich_accelerated": HelpText(
        "Build the visibility graph from the local maxima only instead of from every sample (FastNVG). Many times "
        "faster with the same peaks in practice."
    ),
    "peak_ecg_promac_threshold": HelpText(
        "Fraction of the maximum of the summed detector curves that a location has to reach to count as a peak."
    ),
    "peak_ecg_promac_gaussian_sd": HelpText(
        "Standard deviation of the Gaussian placed on every peak of every detector before the curves are summed. "
        "Wider Gaussians let detectors agree on peaks that lie a little apart.",
        unit="ms",
    ),
    # --- Rate calculation tab ------------------------------------------------------------------------------------
    "rate_handle_incomplete": HelpText(
        "What to do with the windows at the end of a section that are shorter than the window length: drop them, "
        "scale their peak count up to a full window, or repeat the rate of the last complete window.",
        label="label_35",
    ),
    "rate_every": HelpText(
        "Time between the starts of consecutive rate windows. Sets how many rate values a section produces; the "
        "export table has one row per window.",
        unit="s",
    ),
    "rate_period": HelpText(
        "Length of each rate window. The peaks inside it are counted and scaled to beats per minute. Longer windows "
        "give a smoother rate.",
        unit="s",
    ),
}


def _format_value(spin: DecimalSpinBox, value: object) -> str:
    try:
        return spin.textFromValue(decimal.Decimal(str(value)))
    except decimal.InvalidOperation, TypeError, ValueError:
        return str(value)


def default_and_range(widget: QtWidgets.QWidget, text: HelpText) -> str:
    """
    The sentence describing the default value and range of `widget`, read from the widget itself.

    Spin boxes give "Default 0.5 Hz, range 0 to 100000 Hz."; check boxes "Default: on." or "Default: off."; other
    widgets an empty string. `text.minimum_means` is appended when set.
    """
    unit = f" {text.unit}" if text.unit else ""
    parts: list[str] = []
    if isinstance(widget, DecimalSpinBox):
        low = _format_value(widget, widget.minimum())
        high = _format_value(widget, widget.maximum())
        default = widget.property("defaultValue")
        if default is not None:
            parts.append(f"Default {_format_value(widget, default)}{unit}, range {low} to {high}{unit}.")
        else:
            parts.append(f"Range {low} to {high}{unit}.")
    elif isinstance(widget, QtWidgets.QCheckBox):
        default = widget.property("defaultValue")
        if default is not None:
            parts.append(f"Default: {'on' if default else 'off'}.")
    if text.minimum_means:
        parts.append(text.minimum_means)
    return " ".join(parts)


def tooltip_html(text: HelpText, trailer: str = "") -> str:
    """Rich-text tooltip. Qt wraps rich text at a readable width; plain text it shows on one line."""
    html = f"<p>{text.tooltip}</p>"
    if trailer:
        html += f"<p><i>{trailer}</i></p>"
    return html


def whats_this_html(text: HelpText, trailer: str, anchor: str) -> str:
    """Rich-text What's This: the long explanation, the default/range line and the link into the user guide."""
    html = f"<p>{text.whats_this or text.tooltip}</p>"
    if trailer:
        html += f"<p>{trailer}</p>"
    html += f'<p><a href="{help_url(text.page, anchor)}">Open the user guide</a></p>'
    return html


def _label_for(inputs: ParameterInputs, widget: QtWidgets.QWidget, label_name: str) -> QtWidgets.QLabel | None:
    if label_name:
        label = getattr(inputs.ui, label_name, None)
        return label if isinstance(label, QtWidgets.QLabel) else None
    parent = widget.parentWidget()
    layout = parent.layout() if parent is not None else None
    if isinstance(layout, QtWidgets.QFormLayout):
        label = layout.labelForField(widget)
        if isinstance(label, QtWidgets.QLabel):
            return label
    return None


def _bind_enum_tooltip(combo: EnumComboBox, base_html: str) -> None:
    """
    Appends the description of the selected member to the combo box tooltip and keeps it current.

    The description is read from the item's tooltip role, which `EnumComboBox.set_enum_class(doc_data=enum_doc)`
    filled: `current_enum()` returns the value after a round trip through `QVariant`, i.e. a plain `str` without
    the member's docstring.
    """

    def refresh(*_args: object) -> None:
        doc = combo.itemData(combo.currentIndex(), QtCore.Qt.ItemDataRole.ToolTipRole) or ""
        combo.setToolTip(base_html + (f"<p><b>Selected:</b> {doc}</p>" if doc else ""))

    refresh()
    if not combo.property(_BOUND_PROPERTY):
        combo.sig_current_enum_changed.connect(refresh)
        combo.setProperty(_BOUND_PROPERTY, True)


def apply_help_texts(inputs: ParameterInputs) -> None:
    """
    Sets tooltip, What's This and unit suffix on every input of `inputs` from `HELP_TEXTS`.

    Call after the spin box ranges and `defaultValue` properties are set, and again whenever a default changes
    (`SVApp.read_data` does, for the local-extrema radius). Idempotent.

    Raises
    ------
    AttributeError
        If a key of `HELP_TEXTS` names nothing on `inputs.ui` or `inputs`.
    TypeError
        If it names something that is neither a `QWidget` nor a `QAction`.
    """
    for name, text in HELP_TEXTS.items():
        target = getattr(inputs.ui, name, None)
        if target is None:
            target = getattr(inputs, name, None)
        if target is None:
            raise AttributeError(f"HELP_TEXTS names '{name}', which is not a widget or action of ParameterInputs")
        anchor = anchor_for(name)

        if isinstance(target, QtGui.QAction):
            target.setToolTip(text.tooltip)
            target.setWhatsThis(whats_this_html(text, "", anchor))
            continue
        if not isinstance(target, QtWidgets.QWidget):
            raise TypeError(f"HELP_TEXTS names '{name}', which is neither a QWidget nor a QAction")

        widget = target
        if isinstance(widget, DecimalSpinBox) and text.unit:
            widget.setSuffix(f" {text.unit}")
        trailer = default_and_range(widget, text)
        tip = tooltip_html(text, trailer)
        whats = whats_this_html(text, trailer, anchor)
        widget.setToolTip(tip)
        widget.setWhatsThis(whats)
        if isinstance(widget, EnumComboBox):
            _bind_enum_tooltip(widget, tip)

        label = _label_for(inputs, widget, text.label)
        if label is not None:
            label.setToolTip(tip)
            label.setWhatsThis(whats)
