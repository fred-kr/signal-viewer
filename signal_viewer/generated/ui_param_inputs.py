# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'param_inputs.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from pyside_widgets.decimal_spin_box import DecimalSpinBox
from pyside_widgets.enum_combo_box import EnumComboBox

from .. import rc_resources  # noqa


class Ui_containerParamInputs(object):
    def setupUi(self, containerParamInputs):
        if not containerParamInputs.objectName():
            containerParamInputs.setObjectName("containerParamInputs")
        containerParamInputs.resize(422, 619)
        self.verticalLayout = QVBoxLayout(containerParamInputs)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget_params = QTabWidget(containerParamInputs)
        self.tab_widget_params.setObjectName("tab_widget_params")
        self.tab_widget_params.setDocumentMode(False)
        self.tab_processing = QWidget()
        self.tab_processing.setObjectName("tab_processing")
        self.gridLayout = QGridLayout(self.tab_processing)
        self.gridLayout.setObjectName("gridLayout")
        self.status_filter = QToolButton(self.tab_processing)
        self.status_filter.setObjectName("status_filter")
        self.status_filter.setEnabled(False)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.status_filter.sizePolicy().hasHeightForWidth())
        self.status_filter.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(":/icons/CheckboxUnchecked.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(":/icons/CheckboxChecked.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        icon.addFile(":/icons/CheckboxChecked.svg", QSize(), QIcon.Mode.Disabled, QIcon.State.On)
        icon.addFile(":/icons/CheckboxChecked.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.status_filter.setIcon(icon)
        self.status_filter.setCheckable(True)
        self.status_filter.setAutoRaise(True)

        self.gridLayout.addWidget(self.status_filter, 4, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.label_8 = QLabel(self.tab_processing)
        self.label_8.setObjectName("label_8")
        sizePolicy.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy)
        self.label_8.setMinimumSize(QSize(0, 24))

        self.gridLayout.addWidget(self.label_8, 8, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 11, 0, 1, 2)

        self.std_method = EnumComboBox(self.tab_processing)
        self.std_method.setObjectName("std_method")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.std_method.sizePolicy().hasHeightForWidth())
        self.std_method.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.std_method, 9, 0, 1, 2)

        self.status_pipeline = QToolButton(self.tab_processing)
        self.status_pipeline.setObjectName("status_pipeline")
        self.status_pipeline.setEnabled(False)
        sizePolicy.setHeightForWidth(self.status_pipeline.sizePolicy().hasHeightForWidth())
        self.status_pipeline.setSizePolicy(sizePolicy)
        self.status_pipeline.setIcon(icon)
        self.status_pipeline.setCheckable(True)
        self.status_pipeline.setChecked(False)
        self.status_pipeline.setAutoRaise(True)

        self.gridLayout.addWidget(self.status_pipeline, 1, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.status_standardization = QToolButton(self.tab_processing)
        self.status_standardization.setObjectName("status_standardization")
        self.status_standardization.setEnabled(False)
        sizePolicy.setHeightForWidth(self.status_standardization.sizePolicy().hasHeightForWidth())
        self.status_standardization.setSizePolicy(sizePolicy)
        self.status_standardization.setIcon(icon)
        self.status_standardization.setCheckable(True)
        self.status_standardization.setAutoRaise(True)

        self.gridLayout.addWidget(self.status_standardization, 8, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.groupBox = QGroupBox(self.tab_processing)
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupBox.setFlat(False)
        self.formLayout_2 = QFormLayout(self.groupBox)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.sf_lower_cutoff = DecimalSpinBox(self.groupBox)
        self.sf_lower_cutoff.setObjectName("sf_lower_cutoff")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.sf_lower_cutoff)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.sf_upper_cutoff = DecimalSpinBox(self.groupBox)
        self.sf_upper_cutoff.setObjectName("sf_upper_cutoff")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.sf_upper_cutoff)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.sf_order = DecimalSpinBox(self.groupBox)
        self.sf_order.setObjectName("sf_order")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.sf_order)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName("label_6")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.sf_window_size = DecimalSpinBox(self.groupBox)
        self.sf_window_size.setObjectName("sf_window_size")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.sf_window_size)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.sf_powerline = DecimalSpinBox(self.groupBox)
        self.sf_powerline.setObjectName("sf_powerline")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.FieldRole, self.sf_powerline)

        self.gridLayout.addWidget(self.groupBox, 6, 0, 1, 2)

        self.groupBox_3 = QGroupBox(self.tab_processing)
        self.groupBox_3.setObjectName("groupBox_3")
        self.groupBox_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_3 = QFormLayout(self.groupBox_3)
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_10 = QLabel(self.groupBox_3)
        self.label_10.setObjectName("label_10")
        sizePolicy.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy)
        self.label_10.setMinimumSize(QSize(0, 24))

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.std_rolling_window = QCheckBox(self.groupBox_3)
        self.std_rolling_window.setObjectName("std_rolling_window")
        self.std_rolling_window.setMinimumSize(QSize(0, 24))

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.std_rolling_window)

        self.label_9 = QLabel(self.groupBox_3)
        self.label_9.setObjectName("label_9")
        sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy)
        self.label_9.setMinimumSize(QSize(0, 24))

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.std_window_size = DecimalSpinBox(self.groupBox_3)
        self.std_window_size.setObjectName("std_window_size")
        self.std_window_size.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.std_window_size.sizePolicy().hasHeightForWidth())
        self.std_window_size.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.std_window_size)

        self.gridLayout.addWidget(self.groupBox_3, 10, 0, 1, 2)

        self.line = QFrame(self.tab_processing)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 3, 0, 1, 2)

        self.label_2 = QLabel(self.tab_processing)
        self.label_2.setObjectName("label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QSize(0, 24))

        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 1)

        self.label = QLabel(self.tab_processing)
        self.label.setObjectName("label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(0, 24))

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.sf_pipeline = EnumComboBox(self.tab_processing)
        self.sf_pipeline.setObjectName("sf_pipeline")
        sizePolicy1.setHeightForWidth(self.sf_pipeline.sizePolicy().hasHeightForWidth())
        self.sf_pipeline.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.sf_pipeline, 2, 0, 1, 2)

        self.line_2 = QFrame(self.tab_processing)
        self.line_2.setObjectName("line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 7, 0, 1, 2)

        self.sf_method = EnumComboBox(self.tab_processing)
        self.sf_method.setObjectName("sf_method")
        sizePolicy1.setHeightForWidth(self.sf_method.sizePolicy().hasHeightForWidth())
        self.sf_method.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.sf_method, 5, 0, 1, 2)

        self.sf_command_bar = QWidget(self.tab_processing)
        self.sf_command_bar.setObjectName("sf_command_bar")

        self.gridLayout.addWidget(self.sf_command_bar, 0, 0, 1, 2)

        icon1 = QIcon()
        icon1.addFile(":/icons/BeakerEdit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget_params.addTab(self.tab_processing, icon1, "")
        self.tab_peak = QWidget()
        self.tab_peak.setObjectName("tab_peak")
        self.gridLayout_2 = QGridLayout(self.tab_peak)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.peak_method = EnumComboBox(self.tab_peak)
        self.peak_method.setObjectName("peak_method")

        self.gridLayout_2.addWidget(self.peak_method, 2, 0, 1, 1)

        self.groupBox_2 = QGroupBox(self.tab_peak)
        self.groupBox_2.setObjectName("groupBox_2")
        self.groupBox_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.stacked_widget_peak = QStackedWidget(self.groupBox_2)
        self.stacked_widget_peak.setObjectName("stacked_widget_peak")
        self.page_peak_ppg_elgendi = QWidget()
        self.page_peak_ppg_elgendi.setObjectName("page_peak_ppg_elgendi")
        self.formLayout = QFormLayout(self.page_peak_ppg_elgendi)
        self.formLayout.setObjectName("formLayout")
        self.label_11 = QLabel(self.page_peak_ppg_elgendi)
        self.label_11.setObjectName("label_11")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_11)

        self.peak_ppg_elgendi_peakwindow = DecimalSpinBox(self.page_peak_ppg_elgendi)
        self.peak_ppg_elgendi_peakwindow.setObjectName("peak_ppg_elgendi_peakwindow")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_ppg_elgendi_peakwindow)

        self.label_12 = QLabel(self.page_peak_ppg_elgendi)
        self.label_12.setObjectName("label_12")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_12)

        self.peak_ppg_elgendi_beatwindow = DecimalSpinBox(self.page_peak_ppg_elgendi)
        self.peak_ppg_elgendi_beatwindow.setObjectName("peak_ppg_elgendi_beatwindow")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_ppg_elgendi_beatwindow)

        self.label_13 = QLabel(self.page_peak_ppg_elgendi)
        self.label_13.setObjectName("label_13")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_13)

        self.peak_ppg_elgendi_beatoffset = DecimalSpinBox(self.page_peak_ppg_elgendi)
        self.peak_ppg_elgendi_beatoffset.setObjectName("peak_ppg_elgendi_beatoffset")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.peak_ppg_elgendi_beatoffset)

        self.label_14 = QLabel(self.page_peak_ppg_elgendi)
        self.label_14.setObjectName("label_14")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_14)

        self.peak_ppg_elgendi_mindelay = DecimalSpinBox(self.page_peak_ppg_elgendi)
        self.peak_ppg_elgendi_mindelay.setObjectName("peak_ppg_elgendi_mindelay")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.peak_ppg_elgendi_mindelay)

        self.stacked_widget_peak.addWidget(self.page_peak_ppg_elgendi)
        self.page_peak_localmax = QWidget()
        self.page_peak_localmax.setObjectName("page_peak_localmax")
        self.formLayout_5 = QFormLayout(self.page_peak_localmax)
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_15 = QLabel(self.page_peak_localmax)
        self.label_15.setObjectName("label_15")

        self.formLayout_5.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_15)

        self.peak_localmax_radius = DecimalSpinBox(self.page_peak_localmax)
        self.peak_localmax_radius.setObjectName("peak_localmax_radius")

        self.formLayout_5.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_localmax_radius)

        self.label_16 = QLabel(self.page_peak_localmax)
        self.label_16.setObjectName("label_16")

        self.formLayout_5.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_16)

        self.peak_localmax_min_dist = DecimalSpinBox(self.page_peak_localmax)
        self.peak_localmax_min_dist.setObjectName("peak_localmax_min_dist")

        self.formLayout_5.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_localmax_min_dist)

        self.stacked_widget_peak.addWidget(self.page_peak_localmax)
        self.page_peak_localmin = QWidget()
        self.page_peak_localmin.setObjectName("page_peak_localmin")
        self.formLayout_6 = QFormLayout(self.page_peak_localmin)
        self.formLayout_6.setObjectName("formLayout_6")
        self.label_17 = QLabel(self.page_peak_localmin)
        self.label_17.setObjectName("label_17")

        self.formLayout_6.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_17)

        self.peak_localmin_radius = DecimalSpinBox(self.page_peak_localmin)
        self.peak_localmin_radius.setObjectName("peak_localmin_radius")

        self.formLayout_6.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_localmin_radius)

        self.label_18 = QLabel(self.page_peak_localmin)
        self.label_18.setObjectName("label_18")

        self.formLayout_6.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_18)

        self.peak_localmin_min_dist = DecimalSpinBox(self.page_peak_localmin)
        self.peak_localmin_min_dist.setObjectName("peak_localmin_min_dist")

        self.formLayout_6.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_localmin_min_dist)

        self.stacked_widget_peak.addWidget(self.page_peak_localmin)
        self.page_peak_xqrs = QWidget()
        self.page_peak_xqrs.setObjectName("page_peak_xqrs")
        self.formLayout_7 = QFormLayout(self.page_peak_xqrs)
        self.formLayout_7.setObjectName("formLayout_7")
        self.label_21 = QLabel(self.page_peak_xqrs)
        self.label_21.setObjectName("label_21")

        self.formLayout_7.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_21)

        self.peak_xqrs_direction = EnumComboBox(self.page_peak_xqrs)
        self.peak_xqrs_direction.setObjectName("peak_xqrs_direction")

        self.formLayout_7.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_xqrs_direction)

        self.label_19 = QLabel(self.page_peak_xqrs)
        self.label_19.setObjectName("label_19")

        self.formLayout_7.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_19)

        self.peak_xqrs_radius = DecimalSpinBox(self.page_peak_xqrs)
        self.peak_xqrs_radius.setObjectName("peak_xqrs_radius")

        self.formLayout_7.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_xqrs_radius)

        self.label_20 = QLabel(self.page_peak_xqrs)
        self.label_20.setObjectName("label_20")

        self.formLayout_7.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_20)

        self.peak_xqrs_min_dist = DecimalSpinBox(self.page_peak_xqrs)
        self.peak_xqrs_min_dist.setObjectName("peak_xqrs_min_dist")

        self.formLayout_7.setWidget(2, QFormLayout.ItemRole.FieldRole, self.peak_xqrs_min_dist)

        self.stacked_widget_peak.addWidget(self.page_peak_xqrs)
        self.page_peak_ecg_nk = QWidget()
        self.page_peak_ecg_nk.setObjectName("page_peak_ecg_nk")
        self.formLayout_8 = QFormLayout(self.page_peak_ecg_nk)
        self.formLayout_8.setObjectName("formLayout_8")
        self.label_24 = QLabel(self.page_peak_ecg_nk)
        self.label_24.setObjectName("label_24")

        self.formLayout_8.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_24)

        self.peak_ecg_nk_smoothwindow = DecimalSpinBox(self.page_peak_ecg_nk)
        self.peak_ecg_nk_smoothwindow.setObjectName("peak_ecg_nk_smoothwindow")
        self.peak_ecg_nk_smoothwindow.setProperty("decimals", 0)
        self.peak_ecg_nk_smoothwindow.setProperty("f_minimum", 0.000000000000000)
        self.peak_ecg_nk_smoothwindow.setProperty("f_singleStep", 0.000000000000000)

        self.formLayout_8.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_ecg_nk_smoothwindow)

        self.label_25 = QLabel(self.page_peak_ecg_nk)
        self.label_25.setObjectName("label_25")

        self.formLayout_8.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_25)

        self.peak_ecg_nk_avgwindow = DecimalSpinBox(self.page_peak_ecg_nk)
        self.peak_ecg_nk_avgwindow.setObjectName("peak_ecg_nk_avgwindow")

        self.formLayout_8.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_ecg_nk_avgwindow)

        self.label_22 = QLabel(self.page_peak_ecg_nk)
        self.label_22.setObjectName("label_22")

        self.formLayout_8.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_22)

        self.peak_ecg_nk_gradthreshweight = DecimalSpinBox(self.page_peak_ecg_nk)
        self.peak_ecg_nk_gradthreshweight.setObjectName("peak_ecg_nk_gradthreshweight")

        self.formLayout_8.setWidget(2, QFormLayout.ItemRole.FieldRole, self.peak_ecg_nk_gradthreshweight)

        self.label_23 = QLabel(self.page_peak_ecg_nk)
        self.label_23.setObjectName("label_23")

        self.formLayout_8.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_23)

        self.peak_ecg_nk_minlenweight = DecimalSpinBox(self.page_peak_ecg_nk)
        self.peak_ecg_nk_minlenweight.setObjectName("peak_ecg_nk_minlenweight")

        self.formLayout_8.setWidget(3, QFormLayout.ItemRole.FieldRole, self.peak_ecg_nk_minlenweight)

        self.label_26 = QLabel(self.page_peak_ecg_nk)
        self.label_26.setObjectName("label_26")

        self.formLayout_8.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_26)

        self.peak_ecg_nk_mindelay = DecimalSpinBox(self.page_peak_ecg_nk)
        self.peak_ecg_nk_mindelay.setObjectName("peak_ecg_nk_mindelay")

        self.formLayout_8.setWidget(4, QFormLayout.ItemRole.FieldRole, self.peak_ecg_nk_mindelay)

        self.stacked_widget_peak.addWidget(self.page_peak_ecg_nk)
        self.page_peak_ecg_gamboa = QWidget()
        self.page_peak_ecg_gamboa.setObjectName("page_peak_ecg_gamboa")
        self.formLayout_9 = QFormLayout(self.page_peak_ecg_gamboa)
        self.formLayout_9.setObjectName("formLayout_9")
        self.label_28 = QLabel(self.page_peak_ecg_gamboa)
        self.label_28.setObjectName("label_28")

        self.formLayout_9.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_28)

        self.peak_ecg_gamboa_tol = DecimalSpinBox(self.page_peak_ecg_gamboa)
        self.peak_ecg_gamboa_tol.setObjectName("peak_ecg_gamboa_tol")

        self.formLayout_9.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_ecg_gamboa_tol)

        self.stacked_widget_peak.addWidget(self.page_peak_ecg_gamboa)
        self.page_peak_ecg_emrich = QWidget()
        self.page_peak_ecg_emrich.setObjectName("page_peak_ecg_emrich")
        self.formLayout_10 = QFormLayout(self.page_peak_ecg_emrich)
        self.formLayout_10.setObjectName("formLayout_10")
        self.label_30 = QLabel(self.page_peak_ecg_emrich)
        self.label_30.setObjectName("label_30")

        self.formLayout_10.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_30)

        self.peak_ecg_emrich_window_overlap = DecimalSpinBox(self.page_peak_ecg_emrich)
        self.peak_ecg_emrich_window_overlap.setObjectName("peak_ecg_emrich_window_overlap")

        self.formLayout_10.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_ecg_emrich_window_overlap)

        self.label_27 = QLabel(self.page_peak_ecg_emrich)
        self.label_27.setObjectName("label_27")

        self.formLayout_10.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_27)

        self.peak_ecg_emrich_window_seconds = DecimalSpinBox(self.page_peak_ecg_emrich)
        self.peak_ecg_emrich_window_seconds.setObjectName("peak_ecg_emrich_window_seconds")

        self.formLayout_10.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_ecg_emrich_window_seconds)

        self.peak_ecg_emrich_accelerated = QCheckBox(self.page_peak_ecg_emrich)
        self.peak_ecg_emrich_accelerated.setObjectName("peak_ecg_emrich_accelerated")

        self.formLayout_10.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.peak_ecg_emrich_accelerated)

        self.stacked_widget_peak.addWidget(self.page_peak_ecg_emrich)
        self.page_peak_ecg_promac = QWidget()
        self.page_peak_ecg_promac.setObjectName("page_peak_ecg_promac")
        self.formLayout_11 = QFormLayout(self.page_peak_ecg_promac)
        self.formLayout_11.setObjectName("formLayout_11")
        self.label_31 = QLabel(self.page_peak_ecg_promac)
        self.label_31.setObjectName("label_31")

        self.formLayout_11.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_31)

        self.peak_ecg_promac_threshold = DecimalSpinBox(self.page_peak_ecg_promac)
        self.peak_ecg_promac_threshold.setObjectName("peak_ecg_promac_threshold")

        self.formLayout_11.setWidget(0, QFormLayout.ItemRole.FieldRole, self.peak_ecg_promac_threshold)

        self.label_29 = QLabel(self.page_peak_ecg_promac)
        self.label_29.setObjectName("label_29")

        self.formLayout_11.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_29)

        self.peak_ecg_promac_gaussian_sd = DecimalSpinBox(self.page_peak_ecg_promac)
        self.peak_ecg_promac_gaussian_sd.setObjectName("peak_ecg_promac_gaussian_sd")

        self.formLayout_11.setWidget(1, QFormLayout.ItemRole.FieldRole, self.peak_ecg_promac_gaussian_sd)

        self.stacked_widget_peak.addWidget(self.page_peak_ecg_promac)
        self.page_peak_no_params = QWidget()
        self.page_peak_no_params.setObjectName("page_peak_no_params")
        self.verticalLayout_2 = QVBoxLayout(self.page_peak_no_params)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_32 = QLabel(self.page_peak_no_params)
        self.label_32.setObjectName("label_32")
        self.label_32.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_32.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.label_32)

        self.stacked_widget_peak.addWidget(self.page_peak_no_params)

        self.verticalLayout_3.addWidget(self.stacked_widget_peak)

        self.gridLayout_2.addWidget(self.groupBox_2, 3, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 254, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer_2, 4, 0, 1, 1)

        self.detectionMethodLabel = QLabel(self.tab_peak)
        self.detectionMethodLabel.setObjectName("detectionMethodLabel")

        self.gridLayout_2.addWidget(self.detectionMethodLabel, 1, 0, 1, 1)

        self.peak_command_bar = QWidget(self.tab_peak)
        self.peak_command_bar.setObjectName("peak_command_bar")

        self.gridLayout_2.addWidget(self.peak_command_bar, 0, 0, 1, 1)

        icon2 = QIcon()
        icon2.addFile(":/icons/Search.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget_params.addTab(self.tab_peak, icon2, "")
        self.tab_rate = QWidget()
        self.tab_rate.setObjectName("tab_rate")
        self.formLayout_4 = QFormLayout(self.tab_rate)
        self.formLayout_4.setObjectName("formLayout_4")
        self.label_35 = QLabel(self.tab_rate)
        self.label_35.setObjectName("label_35")

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.label_35)

        self.label_34 = QLabel(self.tab_rate)
        self.label_34.setObjectName("label_34")

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_34)

        self.rate_every = DecimalSpinBox(self.tab_rate)
        self.rate_every.setObjectName("rate_every")

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.FieldRole, self.rate_every)

        self.label_33 = QLabel(self.tab_rate)
        self.label_33.setObjectName("label_33")

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_33)

        self.rate_period = DecimalSpinBox(self.tab_rate)
        self.rate_period.setObjectName("rate_period")

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.FieldRole, self.rate_period)

        self.rate_handle_incomplete = EnumComboBox(self.tab_rate)
        self.rate_handle_incomplete.setObjectName("rate_handle_incomplete")

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.rate_handle_incomplete)

        icon3 = QIcon()
        icon3.addFile(":/icons/Pulse.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget_params.addTab(self.tab_rate, icon3, "")

        self.verticalLayout.addWidget(self.tab_widget_params)

        # if QT_CONFIG(shortcut)
        self.label_24.setBuddy(self.peak_ecg_nk_smoothwindow)
        self.label_25.setBuddy(self.peak_ecg_nk_avgwindow)
        self.label_22.setBuddy(self.peak_ecg_nk_gradthreshweight)
        self.label_23.setBuddy(self.peak_ecg_nk_minlenweight)
        self.label_26.setBuddy(self.peak_ecg_nk_mindelay)
        self.label_28.setBuddy(self.peak_ecg_nk_smoothwindow)
        self.label_30.setBuddy(self.peak_ecg_nk_avgwindow)
        self.label_27.setBuddy(self.peak_ecg_nk_gradthreshweight)
        self.label_31.setBuddy(self.peak_ecg_nk_avgwindow)
        self.label_29.setBuddy(self.peak_ecg_nk_gradthreshweight)
        # endif // QT_CONFIG(shortcut)

        self.retranslateUi(containerParamInputs)

        self.tab_widget_params.setCurrentIndex(0)
        self.stacked_widget_peak.setCurrentIndex(4)

        QMetaObject.connectSlotsByName(containerParamInputs)

    # setupUi

    def retranslateUi(self, containerParamInputs):
        containerParamInputs.setWindowTitle(QCoreApplication.translate("containerParamInputs", "Form", None))
        self.label_8.setText(QCoreApplication.translate("containerParamInputs", "Standardization Method", None))
        self.groupBox.setTitle(QCoreApplication.translate("containerParamInputs", "Filter Parameters", None))
        self.label_3.setText(QCoreApplication.translate("containerParamInputs", "Lower cutoff", None))
        self.label_4.setText(QCoreApplication.translate("containerParamInputs", "Upper cutoff", None))
        self.label_5.setText(QCoreApplication.translate("containerParamInputs", "Order", None))
        self.label_6.setText(QCoreApplication.translate("containerParamInputs", "Window Size", None))
        self.label_7.setText(QCoreApplication.translate("containerParamInputs", "Powerline", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("containerParamInputs", "Standardization Parameters", None))
        self.label_10.setText(QCoreApplication.translate("containerParamInputs", "Use rolling window", None))
        self.std_rolling_window.setText("")
        self.label_9.setText(QCoreApplication.translate("containerParamInputs", "Window Size", None))
        self.label_2.setText(QCoreApplication.translate("containerParamInputs", "Filter Method", None))
        self.label.setText(QCoreApplication.translate("containerParamInputs", "Pipeline", None))
        self.tab_widget_params.setTabText(
            self.tab_widget_params.indexOf(self.tab_processing),
            QCoreApplication.translate("containerParamInputs", "Preprocessing", None),
        )
        self.groupBox_2.setTitle(QCoreApplication.translate("containerParamInputs", "Method Parameters", None))
        self.label_11.setText(QCoreApplication.translate("containerParamInputs", "Peak Window", None))
        self.label_12.setText(QCoreApplication.translate("containerParamInputs", "Beat Window", None))
        self.label_13.setText(QCoreApplication.translate("containerParamInputs", "Beat Offset", None))
        self.label_14.setText(QCoreApplication.translate("containerParamInputs", "Minimum Delay", None))
        self.label_15.setText(QCoreApplication.translate("containerParamInputs", "Radius", None))
        self.label_16.setText(QCoreApplication.translate("containerParamInputs", "Min. Distance", None))
        self.label_17.setText(QCoreApplication.translate("containerParamInputs", "Radius", None))
        self.label_18.setText(QCoreApplication.translate("containerParamInputs", "Min. Distance", None))
        self.label_21.setText(QCoreApplication.translate("containerParamInputs", "Peak Adjustment", None))
        self.label_19.setText(QCoreApplication.translate("containerParamInputs", "Radius", None))
        self.label_20.setText(QCoreApplication.translate("containerParamInputs", "Min. Distance", None))
        self.label_24.setText(QCoreApplication.translate("containerParamInputs", "Smooth Window", None))
        self.label_25.setText(QCoreApplication.translate("containerParamInputs", "Average Window", None))
        self.label_22.setText(QCoreApplication.translate("containerParamInputs", "Grad. Thresh. Weight", None))
        self.label_23.setText(QCoreApplication.translate("containerParamInputs", "Min. Length Weight", None))
        self.label_26.setText(QCoreApplication.translate("containerParamInputs", "Minimum Delay", None))
        self.label_28.setText(QCoreApplication.translate("containerParamInputs", "Tolerance", None))
        self.label_30.setText(QCoreApplication.translate("containerParamInputs", "Window Overlap", None))
        self.label_27.setText(QCoreApplication.translate("containerParamInputs", "Window Seconds", None))
        self.peak_ecg_emrich_accelerated.setText(
            QCoreApplication.translate("containerParamInputs", "Accelerated", None)
        )
        self.label_31.setText(QCoreApplication.translate("containerParamInputs", "Threshold", None))
        self.label_29.setText(QCoreApplication.translate("containerParamInputs", "Gaussian SD", None))
        self.label_32.setText(
            QCoreApplication.translate(
                "containerParamInputs", "Selected method doesn't have any adjustable parameters.", None
            )
        )
        self.detectionMethodLabel.setText(QCoreApplication.translate("containerParamInputs", "Detection Method", None))
        self.tab_widget_params.setTabText(
            self.tab_widget_params.indexOf(self.tab_peak),
            QCoreApplication.translate("containerParamInputs", "Peak Detection", None),
        )
        self.label_35.setText(
            QCoreApplication.translate("containerParamInputs", "Incomplete window handling method", None)
        )
        self.label_34.setText(QCoreApplication.translate("containerParamInputs", "New window every", None))
        self.label_33.setText(QCoreApplication.translate("containerParamInputs", "Window Length", None))
        self.tab_widget_params.setTabText(
            self.tab_widget_params.indexOf(self.tab_rate),
            QCoreApplication.translate("containerParamInputs", "Rate Calculation", None),
        )

    # retranslateUi
