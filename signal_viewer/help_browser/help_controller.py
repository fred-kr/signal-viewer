from PySide6 import QtCore

from signal_viewer.help_browser.help_gui import HelpGUI
from signal_viewer.sv_site import DOCDIR
from signal_viewer.utils import get_app


class HelpController(QtCore.QObject):
    def __init__(self) -> None:
        super().__init__()

        self.sv_app = get_app()

        self.gui = HelpGUI(self, parent=self.sv_app.gui)

        self.doc_path = DOCDIR
        self.display_src("index.html")

        self.gui.show()

    @QtCore.Slot(str)
    def display_src(self, src: str) -> None:
        """
        Display a html source file in the help browser window.
        """
        src_path = self.doc_path / src
        url = QtCore.QUrl.fromLocalFile(src_path)

        self.gui.text_browser.setSource(url)

    @QtCore.Slot()
    def exit_help(self) -> None:
        self.sv_app.help = None
        self.gui.close()
