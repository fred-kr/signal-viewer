# pyright: reportAssignmentType=false

import functools
from typing import NamedTuple

import attrs
import pyside_config as qconfig
from PySide6 import QtCore, QtWidgets
from pyside_config.helpers import make_combo_box_info, make_spin_box_info
from pyside_widgets import AnimatedToggleSwitch, EnumComboBox

from signal_viewer.enum_defs import RateComputationMethod, TextFileSeparator
from signal_viewer.utils import get_app_dir, search_enum

app_dir = get_app_dir()


@qconfig.config(group_name="Plot")
class PlotConfig:
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
                widget_factory=functools.partial(EnumComboBox, enum_class=RateComputationMethod),
                sig_value_changed="sig_current_enum_changed",
                set_value_method="set_current_enum",
            ),
            "description": "How to compute the signal rate from the detected peaks.",
        },
    )


editing: EditingConfig = qconfig.get_config("Processing")


@qconfig.config(group_name="Data")
class DataConfig:
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
                widget_factory=functools.partial(EnumComboBox, enum_class=TextFileSeparator),
                sig_value_changed="sig_current_enum_changed",
                set_value_method="set_current_enum",
            ),
            "description": "Character used to separate fields when reading from a text (.txt) file.",
        },
    )


data: DataConfig = qconfig.get_config("Data")


@qconfig.config(group_name="Internal")
class InternalConfig:
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
    recent_annotation_files: list[str] = attrs.field(
        factory=list,
        metadata={
            "description": "List of recently opened annotation files.",
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


internal: InternalConfig = qconfig.get_config("Internal")


class Config(NamedTuple):
    plot = plot
    editing = editing
    data = data
    internal = internal
