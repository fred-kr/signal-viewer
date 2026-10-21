import sys
from pathlib import Path

from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.sv_site import DOCDIR
from signal_viewer.utils import get_gui


class HelpController(QtCore.QObject):
    """
    Shows help pages in Qt Assistant when it is available, otherwise in the system browser.

    Qt Assistant ships with the PySide6 wheel but is not part of a packaged build on every platform. The HTML
    sources of the help collection live next to the compiled `.qch` in `DOCDIR`, so the same relative page path
    works for both viewers.
    """

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)

        self.help_process = QtCore.QProcess(self)
        self.help_process.finished.connect(self.finished)

    @staticmethod
    def assistant_path() -> Path | None:
        """Returns the path to the Qt Assistant executable, or `None` if it is not installed."""
        prefix = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PrefixPath)
        if sys.platform == "win32":
            candidate = Path(prefix, "assistant.exe")
        elif sys.platform == "darwin":
            candidate = Path(prefix, "Assistant.app", "Contents", "MacOS", "Assistant")
        else:
            candidate = Path(prefix, "assistant")
        return candidate if candidate.is_file() else None

    @QtCore.Slot(str)
    def show_page(self, file: str) -> None:
        if self.assistant_path() is None:
            self.open_in_browser(file)
            return
        if not self.start_assistant():
            return
        ba = QtCore.QByteArray(b"setSource qthelp://com.quacktech.signalviewer/signalviewer/")
        ba += file.encode("utf-8") + b"\n"
        self.help_process.write(ba)

    def open_in_browser(self, file: str) -> None:
        page = DOCDIR / file
        if not page.is_file():
            self.show_error(f"Help page not found: {page}")
            return
        logger.debug(f"Qt Assistant not available, opening {page} in the system browser.")
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(page)))

    @QtCore.Slot()
    def start_assistant(self) -> bool:
        if self.help_process.state() != QtCore.QProcess.ProcessState.Running:
            app = self.assistant_path()
            if app is None:
                return False
            args = [
                "-collectionFile",
                Path(DOCDIR / "signalviewer.qhc").as_posix(),
                "-enableRemoteControl",
                "-style",
                "fusion",
            ]

            self.help_process.start(str(app), args)

            if not self.help_process.waitForStarted(3000):
                error_msg = f"Failed to start {app.name}: {self.help_process.errorString()}"
                self.show_error(error_msg)
                return False

        return True

    def show_error(self, error_msg: str) -> None:
        QtWidgets.QMessageBox.critical(QtWidgets.QApplication.activeWindow() or get_gui(), "Error", error_msg)

    def close(self) -> None:
        if self.help_process.state() == QtCore.QProcess.ProcessState.Running:
            self.help_process.finished.disconnect()
            self.help_process.terminate()
            self.help_process.waitForFinished(3000)

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def finished(self, exit_code: int, exit_status: QtCore.QProcess.ExitStatus) -> None:
        std_err = self.help_process.readAllStandardError()
        if exit_status != QtCore.QProcess.ExitStatus.NormalExit:
            self.show_error(f"assistant crashed: {std_err}")
        elif exit_code != 0:
            self.show_error(f"assistant exited with code {exit_code}: {std_err}")
