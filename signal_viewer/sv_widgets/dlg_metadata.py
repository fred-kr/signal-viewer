from PySide6 import QtCore, QtWidgets

from signal_viewer.constants import RESERVED_COLUMN_NAMES
from signal_viewer.generated.ui_dialog_metadata import Ui_MetadataDialog
from signal_viewer.sv_data.data_models import REQUIRED_FIELD_LABELS


class MetadataDialog(QtWidgets.QDialog, Ui_MetadataDialog):
    """
    Lets the user edit the sampling rate and the signal / info column before loading.

    The widgets are filled by `SVApp._bind_metadata`. The dialog validates its own widgets while the user edits
    (`validate`): the missing fields are listed in `label_validation` and "Save" stays disabled until none are left.
    """

    sig_property_has_changed = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        self.label_validation = QtWidgets.QLabel(self.container_form_layout)
        self.label_validation.setObjectName("label_validation")
        self.label_validation.setWordWrap(True)
        self.label_validation.setVisible(False)
        # Row 4 of the form is empty in the .ui file (between the signal and the info column).
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.SpanningRole, self.label_validation)

        self.btn_accept.clicked.connect(self.accept)
        self.btn_reject.clicked.connect(self.reject)
        self.spin_box_sampling_rate.valueChanged.connect(self.validate)
        self.combo_box_signal_column.currentTextChanged.connect(self.validate)
        self.validate()

    def missing_fields(self) -> list[str]:
        """Required fields (`FileMetadata.required_fields` keys) whose widget holds no usable value."""
        missing: list[str] = []
        if self.spin_box_sampling_rate.value() <= 0:
            missing.append("sampling_rate")
        signal_column = self.combo_box_signal_column.currentText()
        if not signal_column or signal_column in RESERVED_COLUMN_NAMES:
            missing.append("signal_column")
        return missing

    @QtCore.Slot()
    def validate(self) -> None:
        """Updates the status text and the "Save" button from the current widget values."""
        missing = self.missing_fields()
        if missing:
            self.label_validation.setText("Missing: " + ", ".join(REQUIRED_FIELD_LABELS.get(f, f) for f in missing))
        else:
            self.label_validation.clear()
        self.label_validation.setVisible(bool(missing))
        self.btn_accept.setEnabled(not missing)

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
