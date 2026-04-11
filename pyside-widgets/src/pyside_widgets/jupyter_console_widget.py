import typing as t

from PySide6 import QtCore, QtGui, QtWidgets
from qtconsole import inprocess

if t.TYPE_CHECKING:
    import jupyter_client


class JupyterConsoleWidget(inprocess.QtInProcessRichJupyterWidget):
    def __init__(self, style: t.Literal["lightbg", "linux", "nocolor"] = "linux") -> None:
        super().__init__()
        self.set_default_style(style)

        self.kernel_manager: inprocess.QtInProcessKernelManager = inprocess.QtInProcessKernelManager()
        self.kernel_manager.start_kernel()

        self.kernel_client: jupyter_client.blocking.client.BlockingKernelClient = self.kernel_manager.client()

        self.kernel_client.start_channels()

        app_inst = QtWidgets.QApplication.instance()
        if app_inst is not None:
            app_inst.aboutToQuit.connect(self.shutdown_kernel)

    @QtCore.Slot()
    def shutdown_kernel(self) -> None:
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()


class JupyterConsoleWindow(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        namespace: dict[str, t.Any] | None = None,
        style: t.Literal["lightbg", "linux", "nocolor"] = "linux",
    ) -> None:
        super().__init__(parent)
        namespace = namespace or {}

        self.toggle_view_action = QtGui.QAction("Toggle Jupyter Console", self)
        self.toggle_view_action.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.Computer))
        self.toggle_view_action.setCheckable(True)
        self.toggle_view_action.toggled.connect(self.setVisible)

        self.console = JupyterConsoleWidget(style=style)
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.console)  # type: ignore
        self.setLayout(layout)

        self.setWindowTitle("Jupyter Console")
        self.resize(900, 600)

        self._prepare_console(namespace)

    def _prepare_console(self, namespace: dict[str, t.Any]) -> None:
        if self.console.kernel_manager.kernel is None:
            return
        if self.console.kernel_manager.kernel.shell is None:
            return
        self.console.kernel_manager.kernel.shell.push(namespace)
        self.console.execute("whos")

    @QtCore.Slot(QtGui.QCloseEvent)
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        with QtCore.QSignalBlocker(self.toggle_view_action):
            self.toggle_view_action.setChecked(False)
        return super().closeEvent(event)

    @QtCore.Slot(bool)
    def setVisible(self, visible: bool) -> None:
        self.toggle_view_action.setChecked(visible)
        super().setVisible(visible)
