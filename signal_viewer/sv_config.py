"""
Persistent settings, declared as `pyside_config` groups.

Each group is an `attrs` class decorated with `@qconfig.config`. A field's `editor` is a callable returning the widget
the Settings dialog edits it with; its `label` and `description` are shown next to the editor and repeated in the user
guide (`doc/reference/settings.html`).
Values are stored through `QSettings` under the organization/application name set in `start.py` and coerced back to
the declared types on load; `--reset-settings` clears them. The "Internal" group is declared `hidden=True`: it is
stored but has no tab in the dialog.

Read a setting through `Config.<group>.<field>`, e.g. `Config.plot.click_radius`. Assigning one writes it to
`QSettings` and emits `qconfig.signals().sig_value_changed`, which `SVApp._on_setting_changed` listens to.
"""

import functools
from typing import NamedTuple

import pyside_config as qconfig
from PySide6 import QtCore, QtWidgets
from pyside_config import config_field
from pyside_widgets import AnimatedToggleSwitch, EnumComboBox

from signal_viewer.enum_defs import RateComputationMethod, TextFileSeparator
from signal_viewer.help_texts import enum_doc
from signal_viewer.utils import get_app_dir

app_dir = get_app_dir()


def _enum_combo_box[T: RateComputationMethod | TextFileSeparator](enum_class: type[T]) -> EnumComboBox[T]:
    """An `EnumComboBox` for a setting, with the member descriptions as item tooltips."""
    combo: EnumComboBox[T] = EnumComboBox()
    combo.set_enum_class(enum_class, doc_data=enum_doc)
    return combo


@qconfig.config(group="Plot")
class PlotConfig:
    """Settings of the editing plot on the Graph page."""

    line_click_width: int = config_field(
        default=70,
        label="Line click width",
        editor=lambda: QtWidgets.QSpinBox(minimum=3, maximum=1_000, suffix=" px"),
        description="The width in pixels orthogonal to the curve that will respond to a mouse click.",
    )
    click_radius: int = config_field(
        default=20,
        label="Click radius",
        editor=lambda: QtWidgets.QSpinBox(minimum=0, maximum=1_000, suffix=" px"),
        description=(
            "The radius in pixels around a click that will be searched for an extreme point when\n"
            "manually adding peaks / valleys."
        ),
    )


plot = qconfig.get_config(PlotConfig)


@qconfig.config(group="Processing")
class EditingConfig:
    """Settings that change how sections are processed."""

    filter_stacking: bool = config_field(
        default=False,
        label="Filter stacking",
        editor=AnimatedToggleSwitch,
        description="Whether to allow applying multiple filters to the same data.",
    )
    rate_computation_method: RateComputationMethod = config_field(
        default=RateComputationMethod.RollingWindow,
        label="Rate computation method",
        editor=functools.partial(_enum_combo_box, RateComputationMethod),
        description="How to compute the signal rate from the detected peaks.",
    )


editing = qconfig.get_config(EditingConfig)


@qconfig.config(group="Data")
class DataConfig:
    """Settings for reading files and displaying their values."""

    float_precision: int = config_field(
        default=3,
        label="Float precision",
        editor=lambda: QtWidgets.QSpinBox(minimum=0, maximum=10),
        description="Amount of decimal places to display when displaying data in tables.",
    )
    text_file_separator: TextFileSeparator = config_field(
        default=TextFileSeparator.Tab,
        label="Text file separator",
        editor=functools.partial(_enum_combo_box, TextFileSeparator),
        description="Character used to separate fields when reading from a text (.txt) file.",
    )


data = qconfig.get_config(DataConfig)


@qconfig.config(group="Internal", hidden=True)
class InternalConfig:
    """State the application remembers between runs. Not shown in the Settings dialog."""

    last_input_dir: str = config_field(
        default=app_dir, description="The directory from which the last file was loaded."
    )
    last_output_dir: str = config_field(default=app_dir, description="The directory to which the last file was saved.")
    last_sampling_rate: int = config_field(
        default=0, description="The sampling rate from which the last file was loaded."
    )
    recent_files: list[str] = config_field(factory=list, description="List of recently opened files.")
    last_signal_column: str = config_field(default="", description="The name of the signal column in the last file.")
    last_info_column: str = config_field(default="", description="The name of the info column in the last file.")
    window_geometry: QtCore.QByteArray = config_field(
        factory=QtCore.QByteArray, description="Geometry of the main window."
    )
    window_state: QtCore.QByteArray = config_field(factory=QtCore.QByteArray, description="State of the main window.")
    help_window_geometry: QtCore.QByteArray = config_field(
        factory=QtCore.QByteArray, description="Geometry of the user guide window."
    )


internal = qconfig.get_config(InternalConfig)


class Config(NamedTuple):
    """Namespace giving access to every settings group: `Config.plot`, `Config.editing`, `Config.data`, `Config.internal`."""

    plot = plot
    editing = editing
    data = data
    internal = internal
