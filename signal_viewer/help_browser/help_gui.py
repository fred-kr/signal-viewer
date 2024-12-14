from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.sv_site import DOCDIR

if TYPE_CHECKING:
    from signal_viewer.help_browser.help_controller import HelpController


class HelpGUI(QtWidgets.QMainWindow):
    def __init__(self, sv_help: "HelpController", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.sv_help = sv_help
        self.setWindowTitle("SignalViewer - User Guide")
        self.setWindowIcon(QtGui.QIcon("://icons/app_icon.svg"))
        self.text_browser = QtWidgets.QTextBrowser()
        self.text_browser.setSearchPaths([DOCDIR.as_posix()])

        self.setCentralWidget(self.text_browser)
        self.text_browser.setAcceptRichText(True)
        self.text_browser.setReadOnly(True)

        self.resize(800, 600)

    @QtCore.Slot(QtGui.QCloseEvent)
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.sv_help.exit_help()
        super().closeEvent(event)
