import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from signal_viewer.sv_site import DOCDIR


class HelpController(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)

        self.help_process = QtCore.QProcess(self)
        self.help_process.finished.connect(self.finished)

    @QtCore.Slot(str)
    def show_page(self, file: str) -> None:
        if not self.start_assistant():
            return
        ba = QtCore.QByteArray(b"setSource qthelp://com.quacktech.signalviewer/signalviewer/")
        ba += file.encode("utf-8") + b"\n"
        self.help_process.write(ba)

    @QtCore.Slot()
    def start_assistant(self) -> bool:
        if self.help_process.state() != QtCore.QProcess.ProcessState.Running:
            app = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PrefixPath)
            if sys.platform != "darwin":
                app += "/assistant"
            else:
                app += "/Assistant.app/Contents/MacOS/Assistant"
            args = ["-collectionFile", Path(DOCDIR / "signalviewer.qhc").as_posix(), "-enableRemoteControl"]

            self.help_process.start(app, args)

            if not self.help_process.waitForStarted(3000):
                error_msg = f"Failed to start assistant.exe: {self.help_process.errorString()}"
                self.show_error(error_msg)
                return False

        return True

    def show_error(self, error_msg: str) -> None:
        QtWidgets.QMessageBox.critical(QtWidgets.QApplication.activeWindow(), "Error", error_msg)

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
