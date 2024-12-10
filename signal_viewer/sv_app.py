# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

from PySide6 import QtCore
from signal_viewer.sv_gui import SVGui

class SVApp(QtCore.QObject):
    def __init__(self) -> None:
        super().__init__()

        self.gui = SVGui(self, "0.0.1")