"""
The Status Log dock: a read-only text view that receives every loguru record.

`LoggingWindow` registers itself as a loguru sink. Records arrive on whatever thread logged them, so the sink only
emits `sig_log_message`; the queued connection to `append` moves the text to the GUI thread, and `SVGUI` connects the
same signal to its error dialog.
"""

import enum

from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.enum_defs import LogLevel
from signal_viewer.type_defs import LogRecordDict


class LoggingWindow(QtWidgets.QTextEdit):
    """
    Read-only log view that is also a loguru sink.

    `append_html` is the sink; it may be called from any thread and therefore only emits `sig_log_message` (message,
    level, record). The queued connection to `append` writes on the GUI thread. A context menu offers "Clear Log".
    """

    sig_log_message: QtCore.Signal = QtCore.Signal(str, enum.IntEnum, dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        logger.add(
            self.append_html,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
            # backtrace=True,
            # diagnose=True,
        )

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.sig_log_message.connect(self.append)
        self.action_clear_log = QtGui.QAction("Clear Log", parent=self)
        self.action_clear_log.triggered.connect(self.clear)

    @QtCore.Slot(QtCore.QPoint)
    def show_context_menu(self, pos: QtCore.QPoint) -> None:
        """Context menu with the Clear Log action."""
        menu = QtWidgets.QMenu(parent=self)
        menu.addAction(self.action_clear_log)
        menu.exec(self.mapToGlobal(pos))

    def append_html(self, message: str) -> None:
        """loguru sink: converts the record's level to `LogLevel` and emits `sig_log_message`. Thread-safe (only emits)."""
        record_dict: LogRecordDict = message.record  # type: ignore
        level = LogLevel[record_dict["level"].name]

        self.sig_log_message.emit(message, level, record_dict)

    @QtCore.Slot(str)
    def append(self, message: str) -> None:
        """Appends one formatted record at the end of the view. GUI thread only."""
        self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.textCursor().insertHtml(f"{message}<br>")
        self.moveCursor(QtGui.QTextCursor.MoveOperation.End)


class StatusMessageDock(QtWidgets.QDockWidget):
    """Dock holding the `LoggingWindow`; hidden by default, toggled from the View and Help menus."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusMessageDock")
        self.setWindowTitle("Status Log")
        self.setVisible(False)
        self.toggleViewAction().setIcon(QtGui.QIcon("://icons/Status.svg"))

        self.log_text_box = LoggingWindow(self)
        self.setWindowIcon(QtGui.QIcon("://icons/History.svg"))
        self.setWidget(self.log_text_box)
