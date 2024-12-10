import sys

from PySide6.QtWidgets import QApplication

from signal_editor.sv_gui import SVGui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SVGui(app, "0.0.1")
    window.show()
    sys.exit(app.exec())
