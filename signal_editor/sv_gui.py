# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6 import QtCore, QtWidgets


class SVGui(QtWidgets.QMainWindow):
    def __init__(self, sv_app: QtWidgets.QApplication, version: str) -> None:
        super().__init__()
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self._version = version

        self.sv_app = sv_app

        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)

        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
