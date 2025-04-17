# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_metadata.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class Ui_MetadataDialog(object):
    def setupUi(self, MetadataDialog):
        if not MetadataDialog.objectName():
            MetadataDialog.setObjectName("MetadataDialog")
        MetadataDialog.resize(648, 400)
        MetadataDialog.setMinimumSize(QSize(600, 400))
        icon = QIcon()
        icon.addFile("://icons/app_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MetadataDialog.setWindowIcon(icon)
        MetadataDialog.setStyleSheet("")
        self.gridLayout = QGridLayout(MetadataDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 0, 1, 1)

        self.btn_reject = QPushButton(MetadataDialog)
        self.btn_reject.setObjectName("btn_reject")

        self.gridLayout.addWidget(self.btn_reject, 1, 2, 1, 1)

        self.btn_accept = QPushButton(MetadataDialog)
        self.btn_accept.setObjectName("btn_accept")

        self.gridLayout.addWidget(self.btn_accept, 1, 1, 1, 1)

        self.container_tabWidget = QTabWidget(MetadataDialog)
        self.container_tabWidget.setObjectName("container_tabWidget")
        self.tab_required_metadata = QWidget()
        self.tab_required_metadata.setObjectName("tab_required_metadata")
        self.verticalLayout = QVBoxLayout(self.tab_required_metadata)
        self.verticalLayout.setObjectName("verticalLayout")
        self.container_form_layout = QWidget(self.tab_required_metadata)
        self.container_form_layout.setObjectName("container_form_layout")
        self.formLayout = QFormLayout(self.container_form_layout)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QLabel(self.container_form_layout)
        self.label_2.setObjectName("label_2")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.line_edit_file_name = QLineEdit(self.container_form_layout)
        self.line_edit_file_name.setObjectName("line_edit_file_name")
        self.line_edit_file_name.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.line_edit_file_name)

        self.label_4 = QLabel(self.container_form_layout)
        self.label_4.setObjectName("label_4")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.line_edit_file_type = QLineEdit(self.container_form_layout)
        self.line_edit_file_type.setObjectName("line_edit_file_type")
        self.line_edit_file_type.setReadOnly(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.line_edit_file_type)

        self.label_3 = QLabel(self.container_form_layout)
        self.label_3.setObjectName("label_3")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.spin_box_sampling_rate = QSpinBox(self.container_form_layout)
        self.spin_box_sampling_rate.setObjectName("spin_box_sampling_rate")
        self.spin_box_sampling_rate.setStyleSheet("")
        self.spin_box_sampling_rate.setMaximum(10000)
        self.spin_box_sampling_rate.setProperty("mandatoryField", True)
        self.spin_box_sampling_rate.setProperty("requiresInput", False)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spin_box_sampling_rate)

        self.label_5 = QLabel(self.container_form_layout)
        self.label_5.setObjectName("label_5")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.label_6 = QLabel(self.container_form_layout)
        self.label_6.setObjectName("label_6")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.combo_box_signal_column = QComboBox(self.container_form_layout)
        self.combo_box_signal_column.setObjectName("combo_box_signal_column")
        self.combo_box_signal_column.setProperty("mandatoryField", True)
        self.combo_box_signal_column.setProperty("requiresInput", False)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.combo_box_signal_column)

        self.combo_box_info_column = QComboBox(self.container_form_layout)
        self.combo_box_info_column.setObjectName("combo_box_info_column")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.combo_box_info_column)

        self.verticalLayout.addWidget(self.container_form_layout)

        self.label_8 = QLabel(self.tab_required_metadata)
        self.label_8.setObjectName("label_8")

        self.verticalLayout.addWidget(self.label_8, 0, Qt.AlignmentFlag.AlignTop)

        self.container_tabWidget.addTab(self.tab_required_metadata, "")
        self.tab_additional_metadata = QWidget()
        self.tab_additional_metadata.setObjectName("tab_additional_metadata")
        self.verticalLayout_2 = QVBoxLayout(self.tab_additional_metadata)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.container_additional_metadata = QWidget(self.tab_additional_metadata)
        self.container_additional_metadata.setObjectName("container_additional_metadata")

        self.verticalLayout_2.addWidget(self.container_additional_metadata)

        self.container_tabWidget.addTab(self.tab_additional_metadata, "")

        self.gridLayout.addWidget(self.container_tabWidget, 0, 0, 1, 3, Qt.AlignmentFlag.AlignTop)

        QWidget.setTabOrder(self.line_edit_file_name, self.line_edit_file_type)
        QWidget.setTabOrder(self.line_edit_file_type, self.spin_box_sampling_rate)
        QWidget.setTabOrder(self.spin_box_sampling_rate, self.btn_accept)
        QWidget.setTabOrder(self.btn_accept, self.btn_reject)

        self.retranslateUi(MetadataDialog)

        self.container_tabWidget.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(MetadataDialog)

    # setupUi

    def retranslateUi(self, MetadataDialog):
        MetadataDialog.setWindowTitle(QCoreApplication.translate("MetadataDialog", "File Metadata", None))
        self.btn_reject.setText(QCoreApplication.translate("MetadataDialog", "Cancel", None))
        self.btn_accept.setText(QCoreApplication.translate("MetadataDialog", "Save", None))
        self.label_2.setText(QCoreApplication.translate("MetadataDialog", "File Name", None))
        self.label_4.setText(QCoreApplication.translate("MetadataDialog", "File Type", None))
        self.label_3.setText(QCoreApplication.translate("MetadataDialog", "Sampling Rate*", None))
        self.spin_box_sampling_rate.setSpecialValueText(QCoreApplication.translate("MetadataDialog", "<Not set>", None))
        self.spin_box_sampling_rate.setSuffix(QCoreApplication.translate("MetadataDialog", " Hz", None))
        # if QT_CONFIG(tooltip)
        self.label_5.setToolTip(
            QCoreApplication.translate(
                "MetadataDialog",
                "<html><head/><body><p>The column / channel in the file containing the signal values</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("MetadataDialog", "Data Source*", None))
        # if QT_CONFIG(tooltip)
        self.label_6.setToolTip(
            QCoreApplication.translate(
                "MetadataDialog",
                "<html><head/><body><p>A column / channel in the file containing supplementary data, e.g. temperature or O2-saturation recordings</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("MetadataDialog", "Info Source", None))
        # if QT_CONFIG(tooltip)
        self.combo_box_signal_column.setToolTip(
            QCoreApplication.translate(
                "MetadataDialog",
                "<html><head/><body><p>The column / channel in the file containing the signal values</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.combo_box_info_column.setToolTip(
            QCoreApplication.translate(
                "MetadataDialog",
                "<html><head/><body><p>A column / channel in the file containing supplementary data, e.g. temperature or O2-saturation recordings</p></body></html>",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_8.setText(QCoreApplication.translate("MetadataDialog", "*Field is required", None))
        self.container_tabWidget.setTabText(
            self.container_tabWidget.indexOf(self.tab_required_metadata),
            QCoreApplication.translate("MetadataDialog", "Required Metadata", None),
        )
        self.container_tabWidget.setTabText(
            self.container_tabWidget.indexOf(self.tab_additional_metadata),
            QCoreApplication.translate("MetadataDialog", "Additional Metadata", None),
        )

    # retranslateUi
