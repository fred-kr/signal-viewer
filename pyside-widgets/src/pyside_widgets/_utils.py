import enum

import darkdetect
from PySide6 import QtGui, QtWidgets


class Theme(enum.Enum):
    LIGHT = "Light"
    DARK = "Dark"
    AUTO = "Auto"


def is_dark_theme() -> bool:
    t = darkdetect.theme()
    t = Theme(t) if t else Theme.LIGHT
    return t == Theme.DARK


class _Nothing(enum.Enum):
    NOTHING = enum.auto()

    def __repr__(self) -> str:
        return "NOTHING"

    def __bool__(self) -> bool:
        return False


NOTHING = _Nothing.NOTHING


def set_font(
    widget: QtWidgets.QWidget | QtGui.QStandardItem,
    font_size: int = 14,
    weight: QtGui.QFont.Weight = QtGui.QFont.Weight.Normal,
    family: str = "Segoe UI",
) -> None:
    font = widget.font()
    font.setPointSize(font_size)
    font.setWeight(weight)
    font.setFamily(family)
    widget.setFont(font)


def get_text_color(background_color: QtGui.QColor) -> QtGui.QColor:
    """
    Determines an appropriate text color (black or white) that contrasts well with the given background color.
    """
    luminance = (
        (background_color.red() * 299) + (background_color.green() * 587) + (background_color.blue() * 114)
    ) // 1000

    return QtGui.QColor(255, 255, 255) if luminance < 128 else QtGui.QColor(0, 0, 0)
