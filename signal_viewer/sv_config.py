"""
Persistent settings, declared as `pyside_config` groups.

Each group is an `attrs` class whose fields carry an `editor` (how the Settings dialog edits the value) and a
`description` (shown under the editor and repeated in the user guide, `doc/reference/settings.html`). Values are
stored through `QSettings` under the organization/application name set in `start.py`; `--reset-settings` clears
them. The "Internal" group has no editors and is hidden from the dialog (`SVApp._on_show_settings`).

Read a setting through `Config.<group>.<field>`, e.g. `Config.plot.click_radius`.
"""

import functools
from typing import NamedTuple

import attrs
import pyside_config as qconfig
from PySide6 import QtCore, QtWidgets
from pyside_config.helpers import make_combo_box_info, make_spin_box_info
from pyside_widgets import AnimatedToggleSwitch, EnumComboBox

from signal_viewer.enum_defs import RateComputationMethod, TextFileSeparator
from signal_viewer.help_texts import enum_doc
from signal_viewer.utils import get_app_dir, search_enum

app_dir = get_app_dir()


def _enum_combo_box[T: RateComputationMethod | TextFileSeparator](enum_class: type[T]) -> EnumComboBox[T]:
    """An `EnumComboBox` for a setting, with the member descriptions as item tooltips."""
    combo: EnumComboBox[T] = EnumComboBox()
    combo.set_enum_class(enum_class, doc_data=enum_doc)
    return combo


@qconfig.config(group_name="Plot")
class PlotConfig:
    """Settings of the editing plot on the Graph page."""

    line_click_width: int = attrs.field(
        default=70,
        converter=int,
        metadata={
            "editor": make_spin_box_info(
                label="Line click width",
                widget_factory=QtWidgets.QSpinBox,
                minimum=3,
                maximum=1_000,
                singleStep=1,
                suffix=" px",
                hasFrame=True,
            ),
            "description": "The width in pixels orthogonal to the curve that will respond to a mouse click.",
        },
    )
    click_radius: int = attrs.field(
        default=20,
        converter=int,
        metadata={
            "editor": make_spin_box_info(
                label="Click radius",
                widget_factory=QtWidgets.QSpinBox,
                minimum=0,
                maximum=1_000,
                singleStep=1,
                suffix=" px",
                hasFrame=True,
            ),
            "description": (
                "The radius in pixels around a click that will be searched for an extreme point when\n"
                "manually adding peaks / valleys."
            ),
        },
    )


plot: PlotConfig = qconfig.get_config("Plot")


@qconfig.config(group_name="Processing")
class EditingConfig:
    """Settings that change how sections are processed."""

    filter_stacking: bool = attrs.field(
        default=False,
        converter=attrs.converters.to_bool,
        metadata={
            "editor": qconfig.EditorWidgetInfo(
                label="Filter stacking",
                widget_factory=AnimatedToggleSwitch,
                sig_value_changed="toggled",
                set_value_method="setChecked",
            ),
            "description": "Whether to allow applying multiple filters to the same data.",
        },
    )
    rate_computation_method: RateComputationMethod = attrs.field(
        default=RateComputationMethod.RollingWindow,
        converter=functools.partial(search_enum, enum_class=RateComputationMethod),
        metadata={
            "editor": make_combo_box_info(
                label="Rate computation method",
                widget_factory=functools.partial(_enum_combo_box, RateComputationMethod),
                sig_value_changed="sig_current_enum_changed",
                set_value_method="set_current_enum",
            ),
            "description": "How to compute the signal rate from the detected peaks.",
        },
    )


editing: EditingConfig = qconfig.get_config("Processing")


@qconfig.config(group_name="Data")
class DataConfig:
    """Settings for reading files and displaying their values."""

    float_precision: int = attrs.field(
        default=3,
        converter=int,
        metadata={
            "editor": make_spin_box_info(
                label="Float precision",
                widget_factory=QtWidgets.QSpinBox,
                minimum=0,
                maximum=10,
                singleStep=1,
                hasFrame=True,
            ),
            "description": "Amount of decimal places to display when displaying data in tables.",
        },
    )
    text_file_separator: TextFileSeparator = attrs.field(
        default=TextFileSeparator.Tab,
        converter=functools.partial(search_enum, enum_class=TextFileSeparator),
        metadata={
            "editor": make_combo_box_info(
                label="Text file separator",
                widget_factory=functools.partial(_enum_combo_box, TextFileSeparator),
                sig_value_changed="sig_current_enum_changed",
                set_value_method="set_current_enum",
            ),
            "description": "Character used to separate fields when reading from a text (.txt) file.",
        },
    )


data: DataConfig = qconfig.get_config("Data")


@qconfig.config(group_name="Internal")
class InternalConfig:
    """State the application remembers between runs. Not shown in the Settings dialog."""

    last_input_dir: str = attrs.field(
        default=app_dir,
        metadata={
            "description": "The directory from which the last file was loaded.",
        },
    )
    last_output_dir: str = attrs.field(
        default=app_dir,
        metadata={
            "description": "The directory to which the last file was saved.",
        },
    )
    last_sampling_rate: int = attrs.field(
        default=0,
        converter=int,
        metadata={
            "description": "The sampling rate from which the last file was loaded.",
        },
    )
    recent_files: list[str] = attrs.field(
        factory=list,
        metadata={
            "description": "List of recently opened files.",
        },
    )
    last_signal_column: str = attrs.field(
        default="",
        metadata={
            "description": "The name of the signal column in the last file.",
        },
    )
    last_info_column: str = attrs.field(
        default="",
        metadata={
            "description": "The name of the info column in the last file.",
        },
    )
    window_geometry: QtCore.QByteArray = attrs.field(
        factory=QtCore.QByteArray,
        metadata={
            "description": "Geometry of the main window.",
        },
    )
    window_state: QtCore.QByteArray = attrs.field(
        factory=QtCore.QByteArray,
        metadata={
            "description": "State of the main window.",
        },
    )
    help_window_geometry: QtCore.QByteArray = attrs.field(
        factory=QtCore.QByteArray,
        metadata={
            "description": "Geometry of the user guide window.",
        },
    )


internal: InternalConfig = qconfig.get_config("Internal")


class Config(NamedTuple):
    """Namespace giving access to every settings group: `Config.plot`, `Config.editing`, `Config.data`, `Config.internal`."""

    plot = plot
    editing = editing
    data = data
    internal = internal
