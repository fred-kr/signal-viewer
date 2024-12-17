# from pathlib import Path
# from typing import TYPE_CHECKING

# from PySide6 import QtCore, QtGui, QtHelp, QtWidgets

# from signal_viewer.sv_site import DOCDIR

# if TYPE_CHECKING:
#     from signal_viewer.help_browser.help_controller import HelpController


# class HelpBrowser(QtWidgets.QTextBrowser):
#     def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
#         super().__init__(parent)

#         collection_file = Path(DOCDIR / "signalviewer.qhc").as_posix()

#         self.help_engine = QtHelp.QHelpEngine(collection_file, self)
#         self.help_engine.setReadOnly(True)

#         if not self.help_engine.setupData():
#             # If the help engine cannot be set up (e.g. missing files), clean up
#             self.help_engine = None

#     def search_keyword(self, keyword: str) -> None:
#         """
#         Shows available help documents for the given keyword. If multiple documents match, the first one will be displayed.
#         """
#         if self.help_engine:
#             if documents := self.help_engine.documentsForKeyword(keyword):
#                 self.setSource(documents[0].url)

#     def loadResource(self, type_: int, name: QtCore.QUrl | str) -> QtCore.QByteArray:  # pyright: ignore[reportIncompatibleMethodOverride]
#         if type_ < 4 and self.help_engine:
#             name = QtCore.QUrl(name)
#             url = self.source().resolved(name) if name.isRelative() else name
#             return self.help_engine.fileData(url)

#         return super().loadResource(type_, name)


# class HelpGUI(QtWidgets.QMainWindow):
#     def __init__(self, sv_help: "HelpController", parent: QtWidgets.QWidget | None = None) -> None:
#         super().__init__(parent)

#         self.sv_help = sv_help
#         self.setWindowTitle("SignalViewer - User Guide")
#         self.setWindowIcon(QtGui.QIcon("://icons/app_icon.png"))
#         self.text_browser = QtWidgets.QTextBrowser()
#         self.text_browser.setSearchPaths([DOCDIR.as_posix()])
#         self.text_browser.setAcceptRichText(True)
#         self.text_browser.setReadOnly(True)

#         self.nav_widget = QtHelp.QHelpContentWidget()

#         self.setCentralWidget(self.text_browser)

#         self.resize(800, 600)

#     @QtCore.Slot(QtGui.QCloseEvent)
#     def closeEvent(self, event: QtGui.QCloseEvent) -> None:
#         self.sv_help.exit_help()
#         super().closeEvent(event)
