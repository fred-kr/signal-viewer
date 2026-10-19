from PySide6 import QtCore, QtWidgets

from signal_viewer.generated.ui_dialog_metadata import Ui_MetadataDialog

STYLE_SHEET_SPIN_BOX = """
QSpinBox[requiresInput="false"] {
    background-color: rgba(0, 200, 100, 0.3);
}
QSpinBox[requiresInput="false"]:focus {
    background-color: rgba(0, 200, 100, 0.3);
}

QSpinBox[requiresInput="true"] {
    background-color: rgba(200, 0, 100, 0.3);
}
QSpinBox[requiresInput="true"]:focus {
    background-color: rgba(200, 0, 100, 0.3);
}
"""
STYLE_SHEET_COMBO_BOX = """
QComboBox[requiresInput="false"] {
    background-color: rgba(0, 200, 100, 0.3);
}
QComboBox[requiresInput="true"] {
    background-color: rgba(200, 0, 100, 0.3);
}

QComboBox[requiresInput="false"]:hover {
    background-color: rgba(0, 200, 100, 0.3);
}
QComboBox[requiresInput="true"]:hover {
    background-color: rgba(200, 0, 100, 0.3);
}

QComboBox[requiresInput="false"]:pressed {
    background-color: rgba(0, 200, 100, 0.3);
}
QComboBox[requiresInput="true"]:pressed {
    background-color: rgba(200, 0, 100, 0.3);
}

QComboBox:disabled {
    color: rgba(0, 0, 0, 0.36);
    background: rgba(249, 249, 249, 0.3);
    border: 1px solid rgba(0, 0, 0, 0.06);
}

QComboBox {
    color: rgba(0, 0, 0, 0.6063);
}
"""


class MetadataDialog(QtWidgets.QDialog, Ui_MetadataDialog):
    sig_property_has_changed = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.combo_box_signal_column.setStyleSheet(STYLE_SHEET_COMBO_BOX)
        self.spin_box_sampling_rate.setStyleSheet(STYLE_SHEET_SPIN_BOX)
        self.btn_accept.clicked.connect(self.accept)
        self.btn_reject.clicked.connect(self.reject)

    @staticmethod
    def set_requires_input(widget: QtWidgets.QWidget, required: bool) -> None:
        """Toggles the `requiresInput` style property and forces the stylesheet to re-apply."""
        widget.setProperty("requiresInput", required)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    @QtCore.Slot()
    def accept(self) -> None:
        # Only reports the user's choice. Persisting it is `DataController.load_data`'s job.
        metadata_dict: dict[str, int | str] = {
            "sampling_rate": self.spin_box_sampling_rate.value(),
            "signal_column": self.combo_box_signal_column.currentText(),
            "info_column": self.combo_box_info_column.currentText(),
        }
        self.sig_property_has_changed.emit(metadata_dict)

        super().accept()
