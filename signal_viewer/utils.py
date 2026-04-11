import datetime
import enum
import re
import sys
import unicodedata
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Unpack

import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from pyqtgraph.Point import Point
from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.type_defs import PGBrush, PGBrushKwargs, PGColor, PGPen, PGPenKwargs

MICRO = "\u03bc"

if TYPE_CHECKING:
    from signal_viewer.sv_app import SVApp
    from signal_viewer.sv_gui import SVGUI


def human_readable_timedelta(
    time_delta: datetime.timedelta | None = None,
    seconds: int | None = None,
    microseconds: int | None = None,
) -> str:
    """
    Convert a timedelta to a human-readable string of the form '1d 02h 30m 00s 000000us'.
    """
    if time_delta is None:
        if seconds is None or microseconds is None:
            raise ValueError("Either 'time_delta' or 'seconds' and 'microseconds' must be provided.")
        time_delta = datetime.timedelta(seconds=seconds, microseconds=microseconds)

    days = time_delta.days
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    microseconds = time_delta.microseconds
    day_str = f"{days}d " if days > 0 else ""

    return f"{day_str}{hours:02d}h {minutes:02d}m {seconds:02d}s {microseconds:06d}{MICRO}s"


def get_app_dir() -> str:
    """
    Get the absolute path to the application's working directory in POSIX format.
    """
    app_instance = QtWidgets.QApplication.instance()

    return (
        QtCore.QDir(app_instance.applicationDirPath()).canonicalPath()
        if hasattr(sys, "frozen") and app_instance is not None
        else QtCore.QDir.current().canonicalPath()
    )


def safe_disconnect(
    sender: QtCore.QObject,
    signal: QtCore.SignalInstance,
    slot: QtCore.Slot | Callable[..., Any],
) -> None:
    """
    Checks if the provided signal and slot are connected, and disconnects them if they are.
    """
    meta_signal = QtCore.QMetaMethod.fromSignal(signal)
    if sender.isSignalConnected(meta_signal):
        signal.disconnect(slot)


def safe_multi_disconnect(
    sender: QtCore.QObject,
    signal_slot_pairs: list[tuple[QtCore.SignalInstance, QtCore.Slot | Callable[..., Any]]],
) -> None:
    """
    Checks if the provided signal/slot pairs are connected, and disconnects them if they are.
    """
    for signal, slot in signal_slot_pairs:
        safe_disconnect(sender, signal, slot)


def sequence_repr(seq: Sequence[int | float]) -> str:
    """
    Improves readibility of large, numerical sequences when printed to the console by only showing the start and end values.
    """
    if len(seq) > 10:
        return f"[{', '.join(map(str, seq[:5]))}, ..., {', '.join(map(str, seq[-5:]))}]"
    else:
        return str(seq)


def make_qcolor(*args: PGColor) -> QtGui.QColor:
    """Creates a QColor from the provided arguments."""
    return args[0] if isinstance(args[0], QtGui.QColor) else pg.mkColor(*args)


def make_qpen(*args: PGPen, **kwargs: Unpack[PGPenKwargs]) -> QtGui.QPen:
    """Creates a QPen from the provided arguments."""
    if len(args) == 1 and isinstance(args[0], QtGui.QPen):
        return args[0]
    return pg.mkPen(*args, **kwargs)


def make_qbrush(*args: PGBrush, **kwargs: Unpack[PGBrushKwargs]) -> QtGui.QBrush:
    """Creates a QBrush from the provided arguments."""
    if len(args) == 1 and isinstance(args[0], QtGui.QBrush):
        return args[0]
    return pg.mkBrush(*args, **kwargs)


def format_file_path(path: str, max_len: int = 50) -> str:
    """Shortens `path` to fit within `max_len` characters by replacing the middle part of the path with ellipsis."""
    path_obj = Path(path).resolve()

    len_name = len(path_obj.name)
    if len_name >= max_len:
        name = f"{path_obj.name[: max_len - 3]}..."
        len_prefix = 0
    else:
        name = path_obj.name
        len_prefix = max_len - len_name - 4

    prefix = path_obj.parent.as_posix()[:len_prefix]
    return f"{prefix}.../{name}"


def search_enum[T: enum.Enum](value: Any, enum_class: type[T]) -> T:
    """
    Searches for `value` in both names and values of `enum_class` and returns the corresponding enum member if found.
    """
    try:
        return enum_class[value]
    except KeyError:
        return enum_class(value)


def get_app() -> "SVApp":
    """
    Get a reference to the `SVApp` instance.
    """
    if sv_apps := [w.sv_app for w in QtWidgets.QApplication.topLevelWidgets() if w.objectName() == "SVGUI"]:  # type: ignore
        return sv_apps[0]  # type: ignore
    else:
        # Probably never happens
        raise RuntimeError("SVApp instance not found. Ensure the GUI is running and the SVGUI widget is present.")


def get_gui() -> "SVGUI":
    """Get a reference to the `SVGUI` (main window) instance."""
    return get_app().gui


def set_font(
    widget: QtWidgets.QWidget,
    font_size: int = 14,
    weight: QtGui.QFont.Weight = QtGui.QFont.Weight.Normal,
    family: str | None = None,
) -> None:
    font = widget.font()
    font.setPointSize(font_size)
    font.setWeight(weight)
    if family:
        font.setFamily(family)
    widget.setFont(font)


type IsPlottable = np.float64 | np.intp | np.uintp


def find_nearest_extrema[T: IsPlottable](
    x_data: npt.NDArray[T],
    y_data: npt.NDArray[T],
    cursor_pos: "Point | QtCore.QPoint | QtCore.QPointF",
    search_radius: int,
) -> tuple[T, T] | None:
    cursor_x, cursor_y = cursor_pos.x(), cursor_pos.y()
    left_idx = np.searchsorted(x_data, cursor_x - search_radius, side="left")
    right_idx = np.searchsorted(x_data, cursor_x + search_radius, side="right")

    valid_x = x_data[left_idx:right_idx]
    valid_y = y_data[left_idx:right_idx]

    x_distances = np.abs(valid_x - cursor_x)
    y_distances = np.abs(valid_y - cursor_y)

    extrema_idx = left_idx + np.argmin(x_distances)
    extrema_val = y_data[extrema_idx]

    extrema_idx_y = left_idx + np.argmin(y_distances)
    extrema_val_y = y_data[extrema_idx_y]

    if np.abs(extrema_val_y - cursor_y) < np.abs(extrema_val - cursor_y):
        extrema_idx = extrema_idx_y
        extrema_val = extrema_val_y

    return x_data[extrema_idx], extrema_val


def _clean_column_names(
    obj: str,
    strip_underscores: Literal["left", "right", "both", "l", "r", True] | None,
    case_type: str,
    remove_special: bool,
    strip_accents: bool,
    truncate_limit: int,
) -> str:
    """
    Function to clean the column names of a polars DataFrame.
    """
    obj = _change_case(obj=obj, case_type=case_type)
    obj = _normalize_1(obj=obj)
    if remove_special:
        obj = _remove_special(obj=obj)
    if strip_accents:
        obj = _strip_accents(obj=obj)
    obj = re.sub(pattern="_+", repl="_", string=obj)
    obj = _strip_underscores_func(
        obj,
        strip_underscores=strip_underscores,
    )
    obj = obj[:truncate_limit]
    return obj


def _change_case(obj: str, case_type: str) -> str:
    case_types = {"preserve", "upper", "lower"}
    if case_type not in case_types:
        raise ValueError(f"type must be one of: {case_types}")
    if case_type == "preserve":
        return obj
    if case_type == "upper":
        return obj.upper()
    if case_type == "lower":
        return obj.lower()
    # Implementation taken from: https://gist.github.com/jaytaylor/3660565
    # by @jtaylor
    return obj.replace(r"(.)([A-Z][a-z]+)", r"\1_\2").replace(r"([a-z0-9])([A-Z])", r"\1_\2").lower()


def _normalize_1(obj: str) -> str:
    FIXES = [(r"[ /:,?()\.-]", "_"), (r"['’]", ""), (r"[\xa0]", "_")]
    for search, replace in FIXES:
        obj = re.sub(pattern=search, repl=replace, string=obj)
    return obj


def _remove_special(obj: str) -> str:
    return re.sub(pattern="[^A-Za-z_\\d]", repl="", string=obj).strip("_")


def _strip_accents(obj: str) -> str:
    """Remove accents from the labels in obj.

    Inspired from [StackOverflow][so].

    [so]: https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-strin
    """  # noqa: E501
    # TODO: possible implementation in Rust
    # or use a pyarrow implementation?
    # https://github.com/pola-rs/polars/issues/11455
    return "".join(letter for letter in unicodedata.normalize("NFD", obj) if not unicodedata.combining(letter))


def _strip_underscores_func(
    obj: str,
    strip_underscores: Literal["left", "right", "both", "l", "r", True] | None = None,
) -> str:
    """Strip underscores from obj."""
    underscore_options = {None, "left", "right", "both", "l", "r", True}
    if strip_underscores not in underscore_options:
        raise ValueError(f"strip_underscores must be one of: {underscore_options}")
    if strip_underscores in {"left", "l"}:
        return obj.strip("_")
    if strip_underscores in {"right", "r"}:
        return obj.rstrip("_")
    if strip_underscores in {True, "both"}:
        return obj.strip("_")
    return obj
