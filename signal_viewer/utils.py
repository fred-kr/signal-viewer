import datetime
import enum
import typing as t
from pathlib import Path

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

import signal_viewer.type_defs as _t

MICRO: t.Final = "\u03bc"


def human_readable_timedelta(
    time_delta: datetime.timedelta | None = None,
    seconds: int | None = None,
    microseconds: int | None = None,
) -> str:
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


@t.overload
def get_app_dir(as_string: t.Literal[False]) -> QtCore.QDir: ...
@t.overload
def get_app_dir(as_string: t.Literal[True]) -> str: ...
def get_app_dir(as_string: bool = False) -> QtCore.QDir | str:
    app_instance = QtWidgets.QApplication.instance()
    import sys

    if hasattr(sys, "frozen") and app_instance is not None:
        out = QtCore.QDir(app_instance.applicationDirPath())
    else:
        out = QtCore.QDir.current()

    return out.canonicalPath() if as_string else out


def app_dir_posix() -> str:
    app_instance = QtWidgets.QApplication.instance()
    import sys

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
    meta_signal = QtCore.QMetaMethod.fromSignal(signal)
    if sender.isSignalConnected(meta_signal):
        signal.disconnect(slot)


def safe_multi_disconnect(
    sender: QtCore.QObject,
    signal_slot_pairs: list[tuple[QtCore.SignalInstance, QtCore.Slot | t.Callable[..., t.Any]]],
) -> None:
    for signal, slot in signal_slot_pairs:
        safe_disconnect(sender, signal, slot)


def format_long_sequence(seq: t.Sequence[int | float]) -> str:
    if len(seq) > 10:
        return f"[{', '.join(map(str, seq[:5]))}, ..., {', '.join(map(str, seq[-5:]))}]"
    else:
        return str(seq)


def make_qcolor(*args: _t.PGColor) -> QtGui.QColor:
    return args[0] if isinstance(args[0], QtGui.QColor) else pg.mkColor(*args)


def make_qpen(*args: _t.PGPen, **kwargs: t.Unpack[_t.PGPenKwargs]) -> QtGui.QPen:
    if len(args) == 1 and isinstance(args[0], QtGui.QPen):
        return args[0]
    return pg.mkPen(*args, **kwargs)


def make_qbrush(*args: _t.PGBrush, **kwargs: t.Unpack[_t.PGBrushKwargs]) -> QtGui.QBrush:
    if len(args) == 1 and isinstance(args[0], QtGui.QBrush):
        return args[0]
    return pg.mkBrush(*args, **kwargs)


def format_file_path(path: str, max_len: int = 50) -> str:
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


def search_enum[T: enum.Enum](value: t.Any, enum_class: t.Type[T]) -> T:
    try:
        return enum_class[value]
    except KeyError:
        return enum_class(value)
