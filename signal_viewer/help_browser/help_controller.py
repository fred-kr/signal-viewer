from pathlib import Path

from PySide6 import QtCore

from signal_viewer.sv_site import BINDIR, DOCDIR


class HelpController(QtCore.QObject):
    sig_assistant_error = QtCore.Signal(str)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("HelpController")
        self.help_process = QtCore.QProcess(self)
        self.help_process.finished.connect(self.finished)

    @QtCore.Slot(str)
    def show_page(self, file: str) -> None:
        if not self.start_assistant():
            return
        ba = QtCore.QByteArray(b"setSource qthelp://com.quacktech.signalviewer/doc/")
        ba += file.encode("utf-8") + b"\n"
        self.help_process.write(ba)

    @QtCore.Slot()
    def start_assistant(self) -> bool:
        if self.help_process.state() != QtCore.QProcess.ProcessState.Running:
            bin_path = Path(BINDIR / "pyside6-assistant.exe").as_posix()
            cli_flags = ["-collectionFile", Path(DOCDIR / "signalviewer.qhc").as_posix(), "-enableRemoteControl"]
            self.help_process.start(bin_path, cli_flags)

            if not self.help_process.waitForStarted(3000):
                error_msg = f"Failed to start pyside6-assistant.exe: {self.help_process.errorString()}"
                self.sig_assistant_error.emit(error_msg)
                return False

        return True

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def finished(self, exit_code: int, status: QtCore.QProcess.ExitStatus) -> None:
        std_err = self.help_process.readAllStandardError().data().decode("utf-8", errors="replace")
        if status != QtCore.QProcess.ExitStatus.NormalExit:
            self.sig_assistant_error.emit(f"pyside6-assistant.exe crashed: {std_err}")
        elif exit_code != 0:
            self.sig_assistant_error.emit(f"pyside6-assistant.exe exited with code {exit_code}: {std_err}")
