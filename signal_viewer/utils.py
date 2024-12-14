import datetime
import enum
import sys
import typing as t
from pathlib import Path

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

import signal_viewer.type_defs as _t

MICRO: t.Final = "\u03bc"

if t.TYPE_CHECKING:
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
    slot: QtCore.Slot | t.Callable[..., t.Any],
) -> None:
    """
    Checks if the provided signal and slot are connected, and disconnects them if they are.
    """
    meta_signal = QtCore.QMetaMethod.fromSignal(signal)
    if sender.isSignalConnected(meta_signal):
        signal.disconnect(slot)


def safe_multi_disconnect(
    sender: QtCore.QObject,
    signal_slot_pairs: list[tuple[QtCore.SignalInstance, QtCore.Slot | t.Callable[..., t.Any]]],
) -> None:
    """
    Checks if the provided signal/slot pairs are connected, and disconnects them if they are.
    """
    for signal, slot in signal_slot_pairs:
        safe_disconnect(sender, signal, slot)


def sequence_repr(seq: t.Sequence[int | float]) -> str:
    """
    Improves readibility of large, numerical sequences when printed to the console by only showing the start and end values.
    """
    if len(seq) > 10:
        return f"[{', '.join(map(str, seq[:5]))}, ..., {', '.join(map(str, seq[-5:]))}]"
    else:
        return str(seq)


def make_qcolor(*args: _t.PGColor) -> QtGui.QColor:
    """Creates a QColor from the provided arguments."""
    return args[0] if isinstance(args[0], QtGui.QColor) else pg.mkColor(*args)


def make_qpen(*args: _t.PGPen, **kwargs: t.Unpack[_t.PGPenKwargs]) -> QtGui.QPen:
    """Creates a QPen from the provided arguments."""
    if len(args) == 1 and isinstance(args[0], QtGui.QPen):
        return args[0]
    return pg.mkPen(*args, **kwargs)


def make_qbrush(*args: _t.PGBrush, **kwargs: t.Unpack[_t.PGBrushKwargs]) -> QtGui.QBrush:
    """Creates a QBrush from the provided arguments."""
    if len(args) == 1 and isinstance(args[0], QtGui.QBrush):
        return args[0]
    return pg.mkBrush(*args, **kwargs)


def format_file_path(path: str, max_len: int = 50) -> str:
    """Shortens `path` to fit within `max_len` characters by replacing the middle part of the path with ellipsis."""
    path_obj = Path(path).resolve()

    len_name = len(path_obj.name)
    if len_name >= max_len:
        name = f"{path_obj.name[:max_len - 3]}..."
        len_prefix = 0
    else:
        name = path_obj.name
        len_prefix = max_len - len_name - 4

    prefix = path_obj.parent.as_posix()[:len_prefix]
    return f"{prefix}.../{name}"


def search_enum[T: enum.Enum](value: t.Any, enum_class: type[T]) -> T:
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
        return sv_apps[0]
    else:
        # Probably never happens
        raise RuntimeError("SVApp instance not found. Ensure the GUI is running and the SVGUI widget is present.")


def get_gui() -> "SVGUI":
    """Get a reference to the `SVGUI` (main window) instance."""
    return get_app().gui
