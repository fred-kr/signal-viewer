# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'parameter_inputs.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QAbstractSpinBox, QApplication, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QSizePolicy,
    QSpacerItem, QStackedWidget, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget)

from qfluentwidgets import (BodyLabel, CheckBox, ComboBox, CommandBar,
    DoubleSpinBox, IconWidget, SimpleCardWidget, SpinBox,
    StrongBodyLabel, SwitchButton)
from . import resources_rc

class Ui_ParameterInputs(object):
    def setupUi(self, ParameterInputs):
        if not ParameterInputs.objectName():
            ParameterInputs.setObjectName(u"ParameterInputs")
        ParameterInputs.resize(475, 620)
        self.action_restore_defaults_processing = QAction(ParameterInputs)
        self.action_restore_defaults_processing.setObjectName(u"action_restore_defaults_processing")
        icon = QIcon()
        icon.addFile(u":/icons/fluent-icons/ArrowReset.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.action_restore_defaults_processing.setIcon(icon)
        self.action_restore_defaults_processing.setMenuRole(QAction.MenuRole.NoRole)
        self.action_restore_original_values = QAction(ParameterInputs)
        self.action_restore_original_values.setObjectName(u"action_restore_original_values")
        icon1 = QIcon()
        icon1.addFile(u":/icons/fluent-icons/Eraser.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.action_restore_original_values.setIcon(icon1)
        self.action_restore_original_values.setMenuRole(QAction.MenuRole.NoRole)
        self.action_run_processing = QAction(ParameterInputs)
        self.action_run_processing.setObjectName(u"action_run_processing")
        icon2 = QIcon()
        icon2.addFile(u":/icons/fluent-icons/Play.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.action_run_processing.setIcon(icon2)
        self.action_run_processing.setMenuRole(QAction.MenuRole.NoRole)
        self.action_run_peak_detection = QAction(ParameterInputs)
        self.action_run_peak_detection.setObjectName(u"action_run_peak_detection")
        self.action_run_peak_detection.setIcon(icon2)
        self.action_run_peak_detection.setMenuRole(QAction.MenuRole.NoRole)
        self.action_restore_defaults_peak_detection = QAction(ParameterInputs)
        self.action_restore_defaults_peak_detection.setObjectName(u"action_restore_defaults_peak_detection")
        self.action_restore_defaults_peak_detection.setIcon(icon)
        self.action_restore_defaults_peak_detection.setMenuRole(QAction.MenuRole.NoRole)
        self.action_clear_peaks = QAction(ParameterInputs)
        self.action_clear_peaks.setObjectName(u"action_clear_peaks")
        icon3 = QIcon()
        icon3.addFile(u":/icons/fluent-icons/Broom.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.action_clear_peaks.setIcon(icon3)
        self.action_clear_peaks.setMenuRole(QAction.MenuRole.NoRole)
        self.layout_parameter_inputs = QVBoxLayout(ParameterInputs)
        self.layout_parameter_inputs.setObjectName(u"layout_parameter_inputs")
        self.tab_widget_parameter_inputs = QTabWidget(ParameterInputs)
        self.tab_widget_parameter_inputs.setObjectName(u"tab_widget_parameter_inputs")
        self.tab_widget_parameter_inputs.setMovable(True)
        self.tab_processing = QWidget()
        self.tab_processing.setObjectName(u"tab_processing")
        self.gridLayout_2 = QGridLayout(self.tab_processing)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_15 = BodyLabel(self.tab_processing)
        self.label_15.setObjectName(u"label_15")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_15.sizePolicy().hasHeightForWidth())
        self.label_15.setSizePolicy(sizePolicy)
        self.label_15.setMinimumSize(QSize(0, 31))

        self.gridLayout_2.addWidget(self.label_15, 7, 0, 1, 3)

        self.switch_btn_standardize_rolling_window = SwitchButton(self.tab_processing)
        self.switch_btn_standardize_rolling_window.setObjectName(u"switch_btn_standardize_rolling_window")
        self.switch_btn_standardize_rolling_window.setMinimumSize(QSize(51, 31))

        self.gridLayout_2.addWidget(self.switch_btn_standardize_rolling_window, 8, 0, 1, 2, Qt.AlignmentFlag.AlignTop)

        self.combo_pipeline = ComboBox(self.tab_processing)
        self.combo_pipeline.setObjectName(u"combo_pipeline")
        self.combo_pipeline.setMinimumSize(QSize(0, 31))

        self.gridLayout_2.addWidget(self.combo_pipeline, 1, 1, 1, 3)

        self.command_bar_processing = CommandBar(self.tab_processing)
        self.command_bar_processing.setObjectName(u"command_bar_processing")
        self.command_bar_processing.setMinimumSize(QSize(0, 31))
        self.command_bar_processing.setStyleSheet(u"background: transparent;")
        self.command_bar_processing.setFrameShape(QFrame.Shape.NoFrame)
        self.command_bar_processing.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_2.addWidget(self.command_bar_processing, 0, 0, 1, 6)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer_5, 9, 0, 1, 4)

        self.container_filter_parameters = QFrame(self.tab_processing)
        self.container_filter_parameters.setObjectName(u"container_filter_parameters")
        self.gridLayout = QGridLayout(self.container_filter_parameters)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = BodyLabel(self.container_filter_parameters)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(0, 31))

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_2 = BodyLabel(self.container_filter_parameters)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QSize(0, 31))

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.dbl_sb_powerline = DoubleSpinBox(self.container_filter_parameters)
        self.dbl_sb_powerline.setObjectName(u"dbl_sb_powerline")
        self.dbl_sb_powerline.setMinimumSize(QSize(0, 31))
        self.dbl_sb_powerline.setFrame(False)
        self.dbl_sb_powerline.setDecimals(1)
        self.dbl_sb_powerline.setMaximum(999999.000000000000000)
        self.dbl_sb_powerline.setSingleStep(0.100000000000000)
        self.dbl_sb_powerline.setValue(50.000000000000000)

        self.gridLayout.addWidget(self.dbl_sb_powerline, 4, 1, 1, 1)

        self.label_13 = BodyLabel(self.container_filter_parameters)
        self.label_13.setObjectName(u"label_13")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy1)
        self.label_13.setMinimumSize(QSize(0, 31))

        self.gridLayout.addWidget(self.label_13, 2, 0, 1, 1)

        self.dbl_sb_upper_cutoff = DoubleSpinBox(self.container_filter_parameters)
        self.dbl_sb_upper_cutoff.setObjectName(u"dbl_sb_upper_cutoff")
        self.dbl_sb_upper_cutoff.setMinimumSize(QSize(0, 31))
        self.dbl_sb_upper_cutoff.setFrame(False)
        self.dbl_sb_upper_cutoff.setDecimals(1)
        self.dbl_sb_upper_cutoff.setMaximum(999999.000000000000000)
        self.dbl_sb_upper_cutoff.setSingleStep(0.100000000000000)
        self.dbl_sb_upper_cutoff.setValue(8.000000000000000)

        self.gridLayout.addWidget(self.dbl_sb_upper_cutoff, 1, 1, 1, 1)

        self.sb_filter_order = SpinBox(self.container_filter_parameters)
        self.sb_filter_order.setObjectName(u"sb_filter_order")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.sb_filter_order.sizePolicy().hasHeightForWidth())
        self.sb_filter_order.setSizePolicy(sizePolicy2)
        self.sb_filter_order.setMinimumSize(QSize(0, 31))
        self.sb_filter_order.setFrame(False)
        self.sb_filter_order.setMinimum(1)
        self.sb_filter_order.setMaximum(10)
        self.sb_filter_order.setValue(3)

        self.gridLayout.addWidget(self.sb_filter_order, 2, 1, 1, 1)

        self.label_3 = BodyLabel(self.container_filter_parameters)
        self.label_3.setObjectName(u"label_3")
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setMinimumSize(QSize(0, 31))

        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)

        self.dbl_sb_lower_cutoff = DoubleSpinBox(self.container_filter_parameters)
        self.dbl_sb_lower_cutoff.setObjectName(u"dbl_sb_lower_cutoff")
        self.dbl_sb_lower_cutoff.setMinimumSize(QSize(0, 31))
        self.dbl_sb_lower_cutoff.setFrame(False)
        self.dbl_sb_lower_cutoff.setDecimals(1)
        self.dbl_sb_lower_cutoff.setMaximum(999999.000000000000000)
        self.dbl_sb_lower_cutoff.setSingleStep(0.100000000000000)
        self.dbl_sb_lower_cutoff.setValue(0.500000000000000)

        self.gridLayout.addWidget(self.dbl_sb_lower_cutoff, 0, 1, 1, 1)

        self.sb_filter_window_size = SpinBox(self.container_filter_parameters)
        self.sb_filter_window_size.setObjectName(u"sb_filter_window_size")
        sizePolicy2.setHeightForWidth(self.sb_filter_window_size.sizePolicy().hasHeightForWidth())
        self.sb_filter_window_size.setSizePolicy(sizePolicy2)
        self.sb_filter_window_size.setMinimumSize(QSize(0, 31))
        self.sb_filter_window_size.setFrame(False)
        self.sb_filter_window_size.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.sb_filter_window_size.setMinimum(5)
        self.sb_filter_window_size.setMaximum(999999)
        self.sb_filter_window_size.setSingleStep(10)
        self.sb_filter_window_size.setValue(5)

        self.gridLayout.addWidget(self.sb_filter_window_size, 3, 1, 1, 1)

        self.label_4 = BodyLabel(self.container_filter_parameters)
        self.label_4.setObjectName(u"label_4")
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setMinimumSize(QSize(0, 31))

        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)


        self.gridLayout_2.addWidget(self.container_filter_parameters, 5, 0, 1, 6)

        self.combo_standardize_method = ComboBox(self.tab_processing)
        self.combo_standardize_method.setObjectName(u"combo_standardize_method")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.combo_standardize_method.sizePolicy().hasHeightForWidth())
        self.combo_standardize_method.setSizePolicy(sizePolicy3)
        self.combo_standardize_method.setMinimumSize(QSize(0, 31))

        self.gridLayout_2.addWidget(self.combo_standardize_method, 7, 3, 1, 1)

        self.combo_filter_method = ComboBox(self.tab_processing)
        self.combo_filter_method.setObjectName(u"combo_filter_method")
        self.combo_filter_method.setMinimumSize(QSize(0, 31))

        self.gridLayout_2.addWidget(self.combo_filter_method, 3, 2, 1, 2)

        self.label_6 = StrongBodyLabel(self.tab_processing)
        self.label_6.setObjectName(u"label_6")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy4)
        self.label_6.setMinimumSize(QSize(0, 31))
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_6, 4, 0, 1, 6)

        self.container_standardize_rolling_window = QWidget(self.tab_processing)
        self.container_standardize_rolling_window.setObjectName(u"container_standardize_rolling_window")
        self.container_standardize_rolling_window.setEnabled(False)
        self.horizontalLayout = QHBoxLayout(self.container_standardize_rolling_window)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, 0, 0)
        self.label_16 = BodyLabel(self.container_standardize_rolling_window)
        self.label_16.setObjectName(u"label_16")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy5)
        self.label_16.setMinimumSize(QSize(0, 31))
        self.label_16.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))

        self.horizontalLayout.addWidget(self.label_16)

        self.sb_standardize_window_size = SpinBox(self.container_standardize_rolling_window)
        self.sb_standardize_window_size.setObjectName(u"sb_standardize_window_size")
        sizePolicy2.setHeightForWidth(self.sb_standardize_window_size.sizePolicy().hasHeightForWidth())
        self.sb_standardize_window_size.setSizePolicy(sizePolicy2)
        self.sb_standardize_window_size.setMinimumSize(QSize(0, 31))
        self.sb_standardize_window_size.setFrame(False)
        self.sb_standardize_window_size.setMinimum(5)
        self.sb_standardize_window_size.setMaximum(999999)
        self.sb_standardize_window_size.setSingleStep(2)
        self.sb_standardize_window_size.setValue(333)

        self.horizontalLayout.addWidget(self.sb_standardize_window_size)


        self.gridLayout_2.addWidget(self.container_standardize_rolling_window, 8, 2, 1, 4)

        self.label_5 = BodyLabel(self.tab_processing)
        self.label_5.setObjectName(u"label_5")
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.label_5, 1, 0, 1, 1)

        self.line_2 = QFrame(self.tab_processing)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line_2, 6, 0, 1, 4)

        self.line = QFrame(self.tab_processing)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line, 2, 0, 1, 6)

        self.label_14 = BodyLabel(self.tab_processing)
        self.label_14.setObjectName(u"label_14")
        sizePolicy.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.label_14, 3, 0, 1, 2)

        self.icon_pipeline_status = IconWidget(self.tab_processing)
        self.icon_pipeline_status.setObjectName(u"icon_pipeline_status")

        self.gridLayout_2.addWidget(self.icon_pipeline_status, 1, 4, 1, 2)

        self.icon_filter_status = IconWidget(self.tab_processing)
        self.icon_filter_status.setObjectName(u"icon_filter_status")

        self.gridLayout_2.addWidget(self.icon_filter_status, 3, 4, 1, 2)

        self.icon_standardize_status = IconWidget(self.tab_processing)
        self.icon_standardize_status.setObjectName(u"icon_standardize_status")

        self.gridLayout_2.addWidget(self.icon_standardize_status, 7, 4, 1, 2)

        self.tab_widget_parameter_inputs.addTab(self.tab_processing, "")
        self.tab_peak_detection = QWidget()
        self.tab_peak_detection.setObjectName(u"tab_peak_detection")
        self.gridLayout_3 = QGridLayout(self.tab_peak_detection)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.command_bar_peak_detection = CommandBar(self.tab_peak_detection)
        self.command_bar_peak_detection.setObjectName(u"command_bar_peak_detection")
        self.command_bar_peak_detection.setMinimumSize(QSize(0, 31))
        self.command_bar_peak_detection.setStyleSheet(u"background: transparent;")
        self.command_bar_peak_detection.setFrameShape(QFrame.Shape.NoFrame)
        self.command_bar_peak_detection.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.command_bar_peak_detection, 0, 0, 1, 2)

        self.label_7 = StrongBodyLabel(self.tab_peak_detection)
        self.label_7.setObjectName(u"label_7")
        sizePolicy5.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy5)
        self.label_7.setMinimumSize(QSize(0, 31))

        self.gridLayout_3.addWidget(self.label_7, 1, 0, 1, 1)

        self.combo_peak_method = ComboBox(self.tab_peak_detection)
        self.combo_peak_method.setObjectName(u"combo_peak_method")
        self.combo_peak_method.setMinimumSize(QSize(0, 31))

        self.gridLayout_3.addWidget(self.combo_peak_method, 1, 1, 1, 1)

        self.stacked_peak_parameters = QStackedWidget(self.tab_peak_detection)
        self.stacked_peak_parameters.setObjectName(u"stacked_peak_parameters")
        self.stacked_peak_parameters.setFrameShape(QFrame.Shape.NoFrame)
        self.page_peak_elgendi_ppg = QWidget()
        self.page_peak_elgendi_ppg.setObjectName(u"page_peak_elgendi_ppg")
        self.formLayout_2 = QFormLayout(self.page_peak_elgendi_ppg)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.peak_elgendi_ppg_info = QTextBrowser(self.page_peak_elgendi_ppg)
        self.peak_elgendi_ppg_info.setObjectName(u"peak_elgendi_ppg_info")
        self.peak_elgendi_ppg_info.setMaximumSize(QSize(16777215, 90))
        self.peak_elgendi_ppg_info.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.formLayout_2.setWidget(0, QFormLayout.SpanningRole, self.peak_elgendi_ppg_info)

        self.label_peak_window = BodyLabel(self.page_peak_elgendi_ppg)
        self.label_peak_window.setObjectName(u"label_peak_window")
        self.label_peak_window.setMinimumSize(QSize(0, 31))

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_peak_window)

        self.peak_elgendi_ppg_peakwindow = DoubleSpinBox(self.page_peak_elgendi_ppg)
        self.peak_elgendi_ppg_peakwindow.setObjectName(u"peak_elgendi_ppg_peakwindow")
        self.peak_elgendi_ppg_peakwindow.setMinimumSize(QSize(0, 31))
        self.peak_elgendi_ppg_peakwindow.setFrame(False)
        self.peak_elgendi_ppg_peakwindow.setDecimals(3)
        self.peak_elgendi_ppg_peakwindow.setMinimum(0.050000000000000)
        self.peak_elgendi_ppg_peakwindow.setMaximum(5.000000000000000)
        self.peak_elgendi_ppg_peakwindow.setSingleStep(0.001000000000000)
        self.peak_elgendi_ppg_peakwindow.setValue(0.111000000000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.peak_elgendi_ppg_peakwindow)

        self.beatWindowLabel = BodyLabel(self.page_peak_elgendi_ppg)
        self.beatWindowLabel.setObjectName(u"beatWindowLabel")
        self.beatWindowLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.beatWindowLabel)

        self.peak_elgendi_ppg_beatwindow = DoubleSpinBox(self.page_peak_elgendi_ppg)
        self.peak_elgendi_ppg_beatwindow.setObjectName(u"peak_elgendi_ppg_beatwindow")
        self.peak_elgendi_ppg_beatwindow.setMinimumSize(QSize(0, 31))
        self.peak_elgendi_ppg_beatwindow.setFrame(False)
        self.peak_elgendi_ppg_beatwindow.setDecimals(3)
        self.peak_elgendi_ppg_beatwindow.setMinimum(0.100000000000000)
        self.peak_elgendi_ppg_beatwindow.setMaximum(5.000000000000000)
        self.peak_elgendi_ppg_beatwindow.setSingleStep(0.001000000000000)
        self.peak_elgendi_ppg_beatwindow.setStepType(QAbstractSpinBox.StepType.DefaultStepType)
        self.peak_elgendi_ppg_beatwindow.setValue(0.667000000000000)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.peak_elgendi_ppg_beatwindow)

        self.beatOffsetLabel = BodyLabel(self.page_peak_elgendi_ppg)
        self.beatOffsetLabel.setObjectName(u"beatOffsetLabel")
        self.beatOffsetLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.beatOffsetLabel)

        self.peak_elgendi_ppg_beatoffset = DoubleSpinBox(self.page_peak_elgendi_ppg)
        self.peak_elgendi_ppg_beatoffset.setObjectName(u"peak_elgendi_ppg_beatoffset")
        self.peak_elgendi_ppg_beatoffset.setMinimumSize(QSize(0, 31))
        self.peak_elgendi_ppg_beatoffset.setFrame(False)
        self.peak_elgendi_ppg_beatoffset.setDecimals(2)
        self.peak_elgendi_ppg_beatoffset.setMaximum(1.000000000000000)
        self.peak_elgendi_ppg_beatoffset.setSingleStep(0.010000000000000)
        self.peak_elgendi_ppg_beatoffset.setStepType(QAbstractSpinBox.StepType.DefaultStepType)
        self.peak_elgendi_ppg_beatoffset.setValue(0.020000000000000)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.peak_elgendi_ppg_beatoffset)

        self.minimumDelayLabel = BodyLabel(self.page_peak_elgendi_ppg)
        self.minimumDelayLabel.setObjectName(u"minimumDelayLabel")
        self.minimumDelayLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.minimumDelayLabel)

        self.peak_elgendi_ppg_mindelay = DoubleSpinBox(self.page_peak_elgendi_ppg)
        self.peak_elgendi_ppg_mindelay.setObjectName(u"peak_elgendi_ppg_mindelay")
        self.peak_elgendi_ppg_mindelay.setMinimumSize(QSize(0, 31))
        self.peak_elgendi_ppg_mindelay.setFrame(False)
        self.peak_elgendi_ppg_mindelay.setDecimals(2)
        self.peak_elgendi_ppg_mindelay.setMaximum(10.000000000000000)
        self.peak_elgendi_ppg_mindelay.setSingleStep(0.010000000000000)
        self.peak_elgendi_ppg_mindelay.setStepType(QAbstractSpinBox.StepType.DefaultStepType)
        self.peak_elgendi_ppg_mindelay.setValue(0.300000000000000)

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.peak_elgendi_ppg_mindelay)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_2.setItem(5, QFormLayout.SpanningRole, self.verticalSpacer_2)

        self.stacked_peak_parameters.addWidget(self.page_peak_elgendi_ppg)
        self.page_peak_local_max = QWidget()
        self.page_peak_local_max.setObjectName(u"page_peak_local_max")
        self.formLayout_5 = QFormLayout(self.page_peak_local_max)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.label_22 = BodyLabel(self.page_peak_local_max)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setMinimumSize(QSize(0, 31))

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.label_22)

        self.peak_local_max_radius = SpinBox(self.page_peak_local_max)
        self.peak_local_max_radius.setObjectName(u"peak_local_max_radius")
        self.peak_local_max_radius.setMinimumSize(QSize(0, 31))
        self.peak_local_max_radius.setFrame(False)
        self.peak_local_max_radius.setAccelerated(True)
        self.peak_local_max_radius.setMinimum(5)
        self.peak_local_max_radius.setMaximum(9999)
        self.peak_local_max_radius.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.peak_local_max_radius.setValue(111)

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.peak_local_max_radius)

        self.peak_local_max_info = QTextBrowser(self.page_peak_local_max)
        self.peak_local_max_info.setObjectName(u"peak_local_max_info")
        self.peak_local_max_info.setMaximumSize(QSize(16777215, 90))
        self.peak_local_max_info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.peak_local_max_info.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.formLayout_5.setWidget(0, QFormLayout.SpanningRole, self.peak_local_max_info)

        self.minDistanceLabel = BodyLabel(self.page_peak_local_max)
        self.minDistanceLabel.setObjectName(u"minDistanceLabel")
        self.minDistanceLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.minDistanceLabel)

        self.peak_local_max_min_dist = SpinBox(self.page_peak_local_max)
        self.peak_local_max_min_dist.setObjectName(u"peak_local_max_min_dist")
        self.peak_local_max_min_dist.setMinimumSize(QSize(0, 31))
        self.peak_local_max_min_dist.setFrame(False)
        self.peak_local_max_min_dist.setMinimum(0)
        self.peak_local_max_min_dist.setMaximum(1000000)
        self.peak_local_max_min_dist.setValue(15)

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.peak_local_max_min_dist)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_5.setItem(3, QFormLayout.SpanningRole, self.verticalSpacer_3)

        self.stacked_peak_parameters.addWidget(self.page_peak_local_max)
        self.page_peak_local_min = QWidget()
        self.page_peak_local_min.setObjectName(u"page_peak_local_min")
        self.formLayout = QFormLayout(self.page_peak_local_min)
        self.formLayout.setObjectName(u"formLayout")
        self.peak_local_min_info = QTextBrowser(self.page_peak_local_min)
        self.peak_local_min_info.setObjectName(u"peak_local_min_info")
        self.peak_local_min_info.setMaximumSize(QSize(16777215, 90))
        self.peak_local_min_info.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.peak_local_min_info.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.formLayout.setWidget(0, QFormLayout.SpanningRole, self.peak_local_min_info)

        self.label_23 = BodyLabel(self.page_peak_local_min)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setMinimumSize(QSize(0, 31))

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_23)

        self.peak_local_min_radius = SpinBox(self.page_peak_local_min)
        self.peak_local_min_radius.setObjectName(u"peak_local_min_radius")
        self.peak_local_min_radius.setMinimumSize(QSize(0, 31))
        self.peak_local_min_radius.setFrame(False)
        self.peak_local_min_radius.setAccelerated(True)
        self.peak_local_min_radius.setMinimum(5)
        self.peak_local_min_radius.setMaximum(9999)
        self.peak_local_min_radius.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.peak_local_min_radius.setValue(111)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.peak_local_min_radius)

        self.minDistanceLabel_2 = BodyLabel(self.page_peak_local_min)
        self.minDistanceLabel_2.setObjectName(u"minDistanceLabel_2")
        self.minDistanceLabel_2.setMinimumSize(QSize(0, 31))

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.minDistanceLabel_2)

        self.peak_local_min_min_dist = SpinBox(self.page_peak_local_min)
        self.peak_local_min_min_dist.setObjectName(u"peak_local_min_min_dist")
        self.peak_local_min_min_dist.setMinimumSize(QSize(0, 31))
        self.peak_local_min_min_dist.setFrame(False)
        self.peak_local_min_min_dist.setMaximum(1000000)
        self.peak_local_min_min_dist.setValue(15)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.peak_local_min_min_dist)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(3, QFormLayout.SpanningRole, self.verticalSpacer_4)

        self.stacked_peak_parameters.addWidget(self.page_peak_local_min)
        self.page_peak_neurokit2 = QWidget()
        self.page_peak_neurokit2.setObjectName(u"page_peak_neurokit2")
        self.gridLayout_4 = QGridLayout(self.page_peak_neurokit2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.peak_neurokit2_info = QTextBrowser(self.page_peak_neurokit2)
        self.peak_neurokit2_info.setObjectName(u"peak_neurokit2_info")
        self.peak_neurokit2_info.setMaximumSize(QSize(16777215, 90))
        self.peak_neurokit2_info.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout_4.addWidget(self.peak_neurokit2_info, 0, 0, 1, 2)

        self.stacked_nk2_method_parameters = QStackedWidget(self.page_peak_neurokit2)
        self.stacked_nk2_method_parameters.setObjectName(u"stacked_nk2_method_parameters")
        self.nk2_page_no_params = QWidget()
        self.nk2_page_no_params.setObjectName(u"nk2_page_no_params")
        self.verticalLayout_2 = QVBoxLayout(self.nk2_page_no_params)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_10 = StrongBodyLabel(self.nk2_page_no_params)
        self.label_10.setObjectName(u"label_10")

        self.verticalLayout_2.addWidget(self.label_10, 0, Qt.AlignmentFlag.AlignTop)

        self.stacked_nk2_method_parameters.addWidget(self.nk2_page_no_params)
        self.nk2_page_neurokit = QWidget()
        self.nk2_page_neurokit.setObjectName(u"nk2_page_neurokit")
        self.formLayout_4 = QFormLayout(self.nk2_page_neurokit)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.smoothingWindowLabel = BodyLabel(self.nk2_page_neurokit)
        self.smoothingWindowLabel.setObjectName(u"smoothingWindowLabel")
        self.smoothingWindowLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.smoothingWindowLabel)

        self.peak_neurokit2_smoothwindow = DoubleSpinBox(self.nk2_page_neurokit)
        self.peak_neurokit2_smoothwindow.setObjectName(u"peak_neurokit2_smoothwindow")
        self.peak_neurokit2_smoothwindow.setMinimumSize(QSize(0, 31))
        self.peak_neurokit2_smoothwindow.setFrame(False)
        self.peak_neurokit2_smoothwindow.setMinimum(0.010000000000000)
        self.peak_neurokit2_smoothwindow.setMaximum(10.000000000000000)
        self.peak_neurokit2_smoothwindow.setSingleStep(0.010000000000000)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.peak_neurokit2_smoothwindow)

        self.label_27 = BodyLabel(self.nk2_page_neurokit)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setMinimumSize(QSize(0, 31))

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_27)

        self.peak_neurokit2_avgwindow = DoubleSpinBox(self.nk2_page_neurokit)
        self.peak_neurokit2_avgwindow.setObjectName(u"peak_neurokit2_avgwindow")
        self.peak_neurokit2_avgwindow.setMinimumSize(QSize(0, 31))
        self.peak_neurokit2_avgwindow.setFrame(False)
        self.peak_neurokit2_avgwindow.setDecimals(2)
        self.peak_neurokit2_avgwindow.setMinimum(0.010000000000000)
        self.peak_neurokit2_avgwindow.setMaximum(10.000000000000000)
        self.peak_neurokit2_avgwindow.setSingleStep(0.010000000000000)
        self.peak_neurokit2_avgwindow.setValue(0.750000000000000)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.peak_neurokit2_avgwindow)

        self.label_28 = BodyLabel(self.nk2_page_neurokit)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setMinimumSize(QSize(0, 31))

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_28)

        self.peak_neurokit2_gradthreshweight = DoubleSpinBox(self.nk2_page_neurokit)
        self.peak_neurokit2_gradthreshweight.setObjectName(u"peak_neurokit2_gradthreshweight")
        self.peak_neurokit2_gradthreshweight.setMinimumSize(QSize(0, 31))
        self.peak_neurokit2_gradthreshweight.setFrame(False)
        self.peak_neurokit2_gradthreshweight.setDecimals(1)
        self.peak_neurokit2_gradthreshweight.setMinimum(0.100000000000000)
        self.peak_neurokit2_gradthreshweight.setMaximum(10.000000000000000)
        self.peak_neurokit2_gradthreshweight.setSingleStep(0.100000000000000)
        self.peak_neurokit2_gradthreshweight.setValue(1.500000000000000)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.peak_neurokit2_gradthreshweight)

        self.label_29 = BodyLabel(self.nk2_page_neurokit)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setMinimumSize(QSize(0, 31))

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.label_29)

        self.peak_neurokit2_minlenweight = DoubleSpinBox(self.nk2_page_neurokit)
        self.peak_neurokit2_minlenweight.setObjectName(u"peak_neurokit2_minlenweight")
        self.peak_neurokit2_minlenweight.setMinimumSize(QSize(0, 31))
        self.peak_neurokit2_minlenweight.setFrame(False)
        self.peak_neurokit2_minlenweight.setDecimals(1)
        self.peak_neurokit2_minlenweight.setMinimum(0.100000000000000)
        self.peak_neurokit2_minlenweight.setMaximum(10.000000000000000)
        self.peak_neurokit2_minlenweight.setSingleStep(0.100000000000000)
        self.peak_neurokit2_minlenweight.setValue(0.400000000000000)

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.peak_neurokit2_minlenweight)

        self.label_30 = BodyLabel(self.nk2_page_neurokit)
        self.label_30.setObjectName(u"label_30")
        self.label_30.setMinimumSize(QSize(0, 31))

        self.formLayout_4.setWidget(4, QFormLayout.LabelRole, self.label_30)

        self.peak_neurokit2_mindelay = DoubleSpinBox(self.nk2_page_neurokit)
        self.peak_neurokit2_mindelay.setObjectName(u"peak_neurokit2_mindelay")
        self.peak_neurokit2_mindelay.setMinimumSize(QSize(0, 31))
        self.peak_neurokit2_mindelay.setFrame(False)
        self.peak_neurokit2_mindelay.setMinimum(0.010000000000000)
        self.peak_neurokit2_mindelay.setMaximum(10.000000000000000)
        self.peak_neurokit2_mindelay.setSingleStep(0.010000000000000)
        self.peak_neurokit2_mindelay.setValue(0.300000000000000)

        self.formLayout_4.setWidget(4, QFormLayout.FieldRole, self.peak_neurokit2_mindelay)

        self.card_nk2_expected_signal = SimpleCardWidget(self.nk2_page_neurokit)
        self.card_nk2_expected_signal.setObjectName(u"card_nk2_expected_signal")
        self.card_nk2_expected_signal.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_nk2_expected_signal.setFrameShadow(QFrame.Shadow.Raised)

        self.formLayout_4.setWidget(5, QFormLayout.LabelRole, self.card_nk2_expected_signal)

        self.stacked_nk2_method_parameters.addWidget(self.nk2_page_neurokit)
        self.nk2_page_ssf = QWidget()
        self.nk2_page_ssf.setObjectName(u"nk2_page_ssf")
        self.formLayout_10 = QFormLayout(self.nk2_page_ssf)
        self.formLayout_10.setObjectName(u"formLayout_10")
        self.label_8 = BodyLabel(self.nk2_page_ssf)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMinimumSize(QSize(0, 31))

        self.formLayout_10.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.peak_ssf_threshold = SpinBox(self.nk2_page_ssf)
        self.peak_ssf_threshold.setObjectName(u"peak_ssf_threshold")
        self.peak_ssf_threshold.setMinimumSize(QSize(0, 31))
        self.peak_ssf_threshold.setFrame(False)
        self.peak_ssf_threshold.setMinimum(1)
        self.peak_ssf_threshold.setMaximum(150)
        self.peak_ssf_threshold.setValue(20)

        self.formLayout_10.setWidget(0, QFormLayout.FieldRole, self.peak_ssf_threshold)

        self.beforeLabel = BodyLabel(self.nk2_page_ssf)
        self.beforeLabel.setObjectName(u"beforeLabel")
        self.beforeLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_10.setWidget(1, QFormLayout.LabelRole, self.beforeLabel)

        self.peak_ssf_before = DoubleSpinBox(self.nk2_page_ssf)
        self.peak_ssf_before.setObjectName(u"peak_ssf_before")
        self.peak_ssf_before.setMinimumSize(QSize(0, 31))
        self.peak_ssf_before.setFrame(False)
        self.peak_ssf_before.setMinimum(0.010000000000000)
        self.peak_ssf_before.setMaximum(0.100000000000000)
        self.peak_ssf_before.setSingleStep(0.010000000000000)
        self.peak_ssf_before.setValue(0.030000000000000)

        self.formLayout_10.setWidget(1, QFormLayout.FieldRole, self.peak_ssf_before)

        self.afterLabel = BodyLabel(self.nk2_page_ssf)
        self.afterLabel.setObjectName(u"afterLabel")
        self.afterLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_10.setWidget(2, QFormLayout.LabelRole, self.afterLabel)

        self.peak_ssf_after = DoubleSpinBox(self.nk2_page_ssf)
        self.peak_ssf_after.setObjectName(u"peak_ssf_after")
        self.peak_ssf_after.setMinimumSize(QSize(0, 31))
        self.peak_ssf_after.setFrame(False)
        self.peak_ssf_after.setDecimals(3)
        self.peak_ssf_after.setMinimum(0.005000000000000)
        self.peak_ssf_after.setMaximum(0.050000000000000)
        self.peak_ssf_after.setSingleStep(0.001000000000000)
        self.peak_ssf_after.setValue(0.010000000000000)

        self.formLayout_10.setWidget(2, QFormLayout.FieldRole, self.peak_ssf_after)

        self.stacked_nk2_method_parameters.addWidget(self.nk2_page_ssf)
        self.nk2_page_gamboa = QWidget()
        self.nk2_page_gamboa.setObjectName(u"nk2_page_gamboa")
        self.formLayout_11 = QFormLayout(self.nk2_page_gamboa)
        self.formLayout_11.setObjectName(u"formLayout_11")
        self.windowLabel = BodyLabel(self.nk2_page_gamboa)
        self.windowLabel.setObjectName(u"windowLabel")
        self.windowLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_11.setWidget(0, QFormLayout.LabelRole, self.windowLabel)

        self.peak_gamboa_tol = DoubleSpinBox(self.nk2_page_gamboa)
        self.peak_gamboa_tol.setObjectName(u"peak_gamboa_tol")
        self.peak_gamboa_tol.setMinimumSize(QSize(0, 31))
        self.peak_gamboa_tol.setFrame(False)
        self.peak_gamboa_tol.setDecimals(3)
        self.peak_gamboa_tol.setMinimum(0.001000000000000)
        self.peak_gamboa_tol.setMaximum(0.010000000000000)
        self.peak_gamboa_tol.setSingleStep(0.001000000000000)
        self.peak_gamboa_tol.setValue(0.002000000000000)

        self.formLayout_11.setWidget(0, QFormLayout.FieldRole, self.peak_gamboa_tol)

        self.stacked_nk2_method_parameters.addWidget(self.nk2_page_gamboa)
        self.nk2_page_emrich = QWidget()
        self.nk2_page_emrich.setObjectName(u"nk2_page_emrich")
        self.formLayout_12 = QFormLayout(self.nk2_page_emrich)
        self.formLayout_12.setObjectName(u"formLayout_12")
        self.label_9 = BodyLabel(self.nk2_page_emrich)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMinimumSize(QSize(0, 31))

        self.formLayout_12.setWidget(0, QFormLayout.LabelRole, self.label_9)

        self.peak_emrich_window_seconds = DoubleSpinBox(self.nk2_page_emrich)
        self.peak_emrich_window_seconds.setObjectName(u"peak_emrich_window_seconds")
        self.peak_emrich_window_seconds.setMinimumSize(QSize(0, 31))
        self.peak_emrich_window_seconds.setFrame(False)
        self.peak_emrich_window_seconds.setDecimals(1)
        self.peak_emrich_window_seconds.setMinimum(1.000000000000000)
        self.peak_emrich_window_seconds.setSingleStep(0.100000000000000)
        self.peak_emrich_window_seconds.setValue(2.000000000000000)

        self.formLayout_12.setWidget(0, QFormLayout.FieldRole, self.peak_emrich_window_seconds)

        self.windowOverlapLabel = BodyLabel(self.nk2_page_emrich)
        self.windowOverlapLabel.setObjectName(u"windowOverlapLabel")
        self.windowOverlapLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_12.setWidget(1, QFormLayout.LabelRole, self.windowOverlapLabel)

        self.peak_emrich_window_overlap = DoubleSpinBox(self.nk2_page_emrich)
        self.peak_emrich_window_overlap.setObjectName(u"peak_emrich_window_overlap")
        self.peak_emrich_window_overlap.setMinimumSize(QSize(0, 31))
        self.peak_emrich_window_overlap.setFrame(False)
        self.peak_emrich_window_overlap.setDecimals(2)
        self.peak_emrich_window_overlap.setMinimum(0.010000000000000)
        self.peak_emrich_window_overlap.setMaximum(1.000000000000000)
        self.peak_emrich_window_overlap.setSingleStep(0.010000000000000)
        self.peak_emrich_window_overlap.setValue(0.500000000000000)

        self.formLayout_12.setWidget(1, QFormLayout.FieldRole, self.peak_emrich_window_overlap)

        self.acceleratedLabel = BodyLabel(self.nk2_page_emrich)
        self.acceleratedLabel.setObjectName(u"acceleratedLabel")
        self.acceleratedLabel.setMinimumSize(QSize(0, 31))

        self.formLayout_12.setWidget(2, QFormLayout.LabelRole, self.acceleratedLabel)

        self.peak_emrich_accelerated = CheckBox(self.nk2_page_emrich)
        self.peak_emrich_accelerated.setObjectName(u"peak_emrich_accelerated")
        self.peak_emrich_accelerated.setMinimumSize(QSize(0, 31))
        self.peak_emrich_accelerated.setChecked(True)

        self.formLayout_12.setWidget(2, QFormLayout.FieldRole, self.peak_emrich_accelerated)

        self.stacked_nk2_method_parameters.addWidget(self.nk2_page_emrich)
        self.nk2_page_promac = QWidget()
        self.nk2_page_promac.setObjectName(u"nk2_page_promac")
        self.formLayout_13 = QFormLayout(self.nk2_page_promac)
        self.formLayout_13.setObjectName(u"formLayout_13")
        self.thresholdLabel_2 = BodyLabel(self.nk2_page_promac)
        self.thresholdLabel_2.setObjectName(u"thresholdLabel_2")
        self.thresholdLabel_2.setMinimumSize(QSize(0, 31))

        self.formLayout_13.setWidget(0, QFormLayout.LabelRole, self.thresholdLabel_2)

        self.peak_promac_threshold = DoubleSpinBox(self.nk2_page_promac)
        self.peak_promac_threshold.setObjectName(u"peak_promac_threshold")
        self.peak_promac_threshold.setMinimumSize(QSize(0, 31))
        self.peak_promac_threshold.setFrame(False)
        self.peak_promac_threshold.setMaximum(1.000000000000000)
        self.peak_promac_threshold.setSingleStep(0.010000000000000)
        self.peak_promac_threshold.setValue(0.330000000000000)

        self.formLayout_13.setWidget(0, QFormLayout.FieldRole, self.peak_promac_threshold)

        self.qRSComplexSizeLabel_2 = BodyLabel(self.nk2_page_promac)
        self.qRSComplexSizeLabel_2.setObjectName(u"qRSComplexSizeLabel_2")
        self.qRSComplexSizeLabel_2.setMinimumSize(QSize(0, 31))

        self.formLayout_13.setWidget(1, QFormLayout.LabelRole, self.qRSComplexSizeLabel_2)

        self.peak_promac_gaussian_sd = SpinBox(self.nk2_page_promac)
        self.peak_promac_gaussian_sd.setObjectName(u"peak_promac_gaussian_sd")
        self.peak_promac_gaussian_sd.setMinimumSize(QSize(0, 31))
        self.peak_promac_gaussian_sd.setFrame(False)
        self.peak_promac_gaussian_sd.setMaximum(100000)
        self.peak_promac_gaussian_sd.setValue(100)

        self.formLayout_13.setWidget(1, QFormLayout.FieldRole, self.peak_promac_gaussian_sd)

        self.stacked_nk2_method_parameters.addWidget(self.nk2_page_promac)

        self.gridLayout_4.addWidget(self.stacked_nk2_method_parameters, 2, 0, 1, 2)

        self.peak_neurokit2_algorithm_used = ComboBox(self.page_peak_neurokit2)
        self.peak_neurokit2_algorithm_used.setObjectName(u"peak_neurokit2_algorithm_used")
        self.peak_neurokit2_algorithm_used.setMinimumSize(QSize(0, 31))

        self.gridLayout_4.addWidget(self.peak_neurokit2_algorithm_used, 1, 1, 1, 1)

        self.algorithmLabel = StrongBodyLabel(self.page_peak_neurokit2)
        self.algorithmLabel.setObjectName(u"algorithmLabel")
        self.algorithmLabel.setEnabled(False)
        sizePolicy5.setHeightForWidth(self.algorithmLabel.sizePolicy().hasHeightForWidth())
        self.algorithmLabel.setSizePolicy(sizePolicy5)
        self.algorithmLabel.setMinimumSize(QSize(0, 31))

        self.gridLayout_4.addWidget(self.algorithmLabel, 1, 0, 1, 1)

        self.stacked_peak_parameters.addWidget(self.page_peak_neurokit2)
        self.page_peak_xqrs = QWidget()
        self.page_peak_xqrs.setObjectName(u"page_peak_xqrs")
        self.gridLayout_5 = QGridLayout(self.page_peak_xqrs)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.peak_xqrs_peak_dir = ComboBox(self.page_peak_xqrs)
        self.peak_xqrs_peak_dir.setObjectName(u"peak_xqrs_peak_dir")
        self.peak_xqrs_peak_dir.setMinimumSize(QSize(0, 31))

        self.gridLayout_5.addWidget(self.peak_xqrs_peak_dir, 2, 1, 1, 1)

        self.searchRadiusLabel = BodyLabel(self.page_peak_xqrs)
        self.searchRadiusLabel.setObjectName(u"searchRadiusLabel")
        sizePolicy5.setHeightForWidth(self.searchRadiusLabel.sizePolicy().hasHeightForWidth())
        self.searchRadiusLabel.setSizePolicy(sizePolicy5)
        self.searchRadiusLabel.setMinimumSize(QSize(0, 31))

        self.gridLayout_5.addWidget(self.searchRadiusLabel, 1, 0, 1, 1)

        self.adjustPeaksLabel = BodyLabel(self.page_peak_xqrs)
        self.adjustPeaksLabel.setObjectName(u"adjustPeaksLabel")
        sizePolicy5.setHeightForWidth(self.adjustPeaksLabel.sizePolicy().hasHeightForWidth())
        self.adjustPeaksLabel.setSizePolicy(sizePolicy5)
        self.adjustPeaksLabel.setMinimumSize(QSize(0, 31))

        self.gridLayout_5.addWidget(self.adjustPeaksLabel, 2, 0, 1, 1)

        self.peak_xqrs_info = QTextBrowser(self.page_peak_xqrs)
        self.peak_xqrs_info.setObjectName(u"peak_xqrs_info")
        self.peak_xqrs_info.setMaximumSize(QSize(16777215, 90))
        self.peak_xqrs_info.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout_5.addWidget(self.peak_xqrs_info, 0, 0, 1, 2)

        self.peak_xqrs_search_radius = SpinBox(self.page_peak_xqrs)
        self.peak_xqrs_search_radius.setObjectName(u"peak_xqrs_search_radius")
        self.peak_xqrs_search_radius.setMinimumSize(QSize(0, 31))
        self.peak_xqrs_search_radius.setFrame(False)
        self.peak_xqrs_search_radius.setMinimum(5)
        self.peak_xqrs_search_radius.setMaximum(99999)
        self.peak_xqrs_search_radius.setValue(90)

        self.gridLayout_5.addWidget(self.peak_xqrs_search_radius, 1, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer, 4, 0, 1, 2)

        self.peak_xqrs_min_peak_distance = SpinBox(self.page_peak_xqrs)
        self.peak_xqrs_min_peak_distance.setObjectName(u"peak_xqrs_min_peak_distance")
        self.peak_xqrs_min_peak_distance.setMinimumSize(QSize(0, 31))
        self.peak_xqrs_min_peak_distance.setFrame(False)
        self.peak_xqrs_min_peak_distance.setMaximum(100000)
        self.peak_xqrs_min_peak_distance.setValue(10)

        self.gridLayout_5.addWidget(self.peak_xqrs_min_peak_distance, 3, 1, 1, 1)

        self.label_17 = BodyLabel(self.page_peak_xqrs)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_5.addWidget(self.label_17, 3, 0, 1, 1)

        self.stacked_peak_parameters.addWidget(self.page_peak_xqrs)

        self.gridLayout_3.addWidget(self.stacked_peak_parameters, 2, 0, 1, 2)

        self.tab_widget_parameter_inputs.addTab(self.tab_peak_detection, "")
        self.tab_rate_calculation = QWidget()
        self.tab_rate_calculation.setObjectName(u"tab_rate_calculation")
        self.gridLayout_6 = QGridLayout(self.tab_rate_calculation)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label_18 = BodyLabel(self.tab_rate_calculation)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_6.addWidget(self.label_18, 2, 0, 1, 2)

        self.sb_period_seconds = SpinBox(self.tab_rate_calculation)
        self.sb_period_seconds.setObjectName(u"sb_period_seconds")
        self.sb_period_seconds.setMinimumSize(QSize(0, 31))
        self.sb_period_seconds.setFrame(False)
        self.sb_period_seconds.setMinimum(1)
        self.sb_period_seconds.setMaximum(10000)
        self.sb_period_seconds.setValue(60)

        self.gridLayout_6.addWidget(self.sb_period_seconds, 1, 1, 1, 1)

        self.sb_every_seconds = SpinBox(self.tab_rate_calculation)
        self.sb_every_seconds.setObjectName(u"sb_every_seconds")
        self.sb_every_seconds.setMinimumSize(QSize(0, 31))
        self.sb_every_seconds.setFrame(False)
        self.sb_every_seconds.setMinimum(1)
        self.sb_every_seconds.setMaximum(600)
        self.sb_every_seconds.setValue(10)

        self.gridLayout_6.addWidget(self.sb_every_seconds, 0, 1, 1, 1)

        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_6.addItem(self.verticalSpacer_6, 4, 0, 1, 2)

        self.combo_incomplete_window_method = ComboBox(self.tab_rate_calculation)
        self.combo_incomplete_window_method.setObjectName(u"combo_incomplete_window_method")
        self.combo_incomplete_window_method.setMinimumSize(QSize(0, 31))

        self.gridLayout_6.addWidget(self.combo_incomplete_window_method, 3, 0, 1, 2)

        self.label_11 = BodyLabel(self.tab_rate_calculation)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setMinimumSize(QSize(0, 31))

        self.gridLayout_6.addWidget(self.label_11, 0, 0, 1, 1)

        self.label_12 = BodyLabel(self.tab_rate_calculation)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMinimumSize(QSize(0, 31))

        self.gridLayout_6.addWidget(self.label_12, 1, 0, 1, 1)

        self.tab_widget_parameter_inputs.addTab(self.tab_rate_calculation, "")

        self.layout_parameter_inputs.addWidget(self.tab_widget_parameter_inputs)


        self.retranslateUi(ParameterInputs)

        self.tab_widget_parameter_inputs.setCurrentIndex(0)
        self.stacked_peak_parameters.setCurrentIndex(0)
        self.stacked_nk2_method_parameters.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ParameterInputs)
    # setupUi

    def retranslateUi(self, ParameterInputs):
        ParameterInputs.setWindowTitle(QCoreApplication.translate("ParameterInputs", u"Parameter Inputs", None))
        self.action_restore_defaults_processing.setText(QCoreApplication.translate("ParameterInputs", u"Restore Defaults", None))
#if QT_CONFIG(tooltip)
        self.action_restore_defaults_processing.setToolTip(QCoreApplication.translate("ParameterInputs", u"Reset all input fields to their default values", None))
#endif // QT_CONFIG(tooltip)
        self.action_restore_original_values.setText(QCoreApplication.translate("ParameterInputs", u"Reset Data", None))
#if QT_CONFIG(tooltip)
        self.action_restore_original_values.setToolTip(QCoreApplication.translate("ParameterInputs", u"Reset current section data to the original (unprocessed) values", None))
#endif // QT_CONFIG(tooltip)
        self.action_run_processing.setText(QCoreApplication.translate("ParameterInputs", u"Run Processing", None))
#if QT_CONFIG(tooltip)
        self.action_run_processing.setToolTip(QCoreApplication.translate("ParameterInputs", u"Apply selected processing steps to the active section", None))
#endif // QT_CONFIG(tooltip)
        self.action_run_peak_detection.setText(QCoreApplication.translate("ParameterInputs", u"Run Peak Detection", None))
#if QT_CONFIG(tooltip)
        self.action_run_peak_detection.setToolTip(QCoreApplication.translate("ParameterInputs", u"Detects location of peak indices in the signal using the selected method and parameters", None))
#endif // QT_CONFIG(tooltip)
        self.action_restore_defaults_peak_detection.setText(QCoreApplication.translate("ParameterInputs", u"Restore Defaults", None))
#if QT_CONFIG(tooltip)
        self.action_restore_defaults_peak_detection.setToolTip(QCoreApplication.translate("ParameterInputs", u"Reset current input fields to their default values", None))
#endif // QT_CONFIG(tooltip)
        self.action_clear_peaks.setText(QCoreApplication.translate("ParameterInputs", u"Clear Peaks", None))
#if QT_CONFIG(tooltip)
        self.action_clear_peaks.setToolTip(QCoreApplication.translate("ParameterInputs", u"Clear all detected peak values from the active section", None))
#endif // QT_CONFIG(tooltip)
        self.label_15.setText(QCoreApplication.translate("ParameterInputs", u"Standardization Method:", None))
#if QT_CONFIG(tooltip)
        self.combo_pipeline.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Clean the signal using a pre-defined signal processing pipeline</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.combo_pipeline.setWhatsThis(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Different signal cleaning pipelines. For sources see 'Help'.</p><p>Implemented via the `neurokit2` python package.</p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.combo_pipeline.setText("")
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("ParameterInputs", u"Lower cutoff frequency in Hz", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("ParameterInputs", u"Lower cutoff frequency", None))
#if QT_CONFIG(tooltip)
        self.label_2.setToolTip(QCoreApplication.translate("ParameterInputs", u"Upper cutoff frequency in Hz", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("ParameterInputs", u"Upper cutoff frequency", None))
#if QT_CONFIG(tooltip)
        self.dbl_sb_powerline.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Only used if <span style=\" font-weight:700;\">Filter Method</span> is &quot;Powerline&quot;.</p><p>The powerline frequency (normally 50 Hz or 60 Hz).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.dbl_sb_powerline.setSuffix(QCoreApplication.translate("ParameterInputs", u" Hz", None))
#if QT_CONFIG(tooltip)
        self.label_13.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Only used if <span style=\" font-weight:700;\">Filter Method</span> is &quot;Butterworth&quot; or &quot;SavGol&quot;. </p><p>Order of the filter (default is 2).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_13.setText(QCoreApplication.translate("ParameterInputs", u"Select Filter Order", None))
#if QT_CONFIG(tooltip)
        self.dbl_sb_upper_cutoff.setToolTip(QCoreApplication.translate("ParameterInputs", u"Upper cutoff frequency in Hz", None))
#endif // QT_CONFIG(tooltip)
        self.dbl_sb_upper_cutoff.setSpecialValueText(QCoreApplication.translate("ParameterInputs", u"None", None))
        self.dbl_sb_upper_cutoff.setSuffix(QCoreApplication.translate("ParameterInputs", u" Hz", None))
#if QT_CONFIG(tooltip)
        self.sb_filter_order.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Only used if <span style=\" font-weight:700;\">Filter Method</span> is &quot;Butterworth&quot; or &quot;SavGol&quot;. </p><p>Order of the filter (default is 2).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_3.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Only used if <span style=\" font-weight:700;\">Filter Method</span> is &quot;SavGol&quot; (length of the filter window i.e. the number of coefficients) or &quot;FIR&quot; (length of the filter). </p><p>Must be an odd integer. If &quot;Auto&quot;, a fitting size is chosen automatically.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("ParameterInputs", u"Filter Window Size", None))
#if QT_CONFIG(tooltip)
        self.dbl_sb_lower_cutoff.setToolTip(QCoreApplication.translate("ParameterInputs", u"Lower cutoff frequency in Hz", None))
#endif // QT_CONFIG(tooltip)
        self.dbl_sb_lower_cutoff.setSpecialValueText(QCoreApplication.translate("ParameterInputs", u"None", None))
        self.dbl_sb_lower_cutoff.setSuffix(QCoreApplication.translate("ParameterInputs", u" Hz", None))
#if QT_CONFIG(tooltip)
        self.sb_filter_window_size.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Only used if <span style=\" font-weight:700;\">Filter Method</span> is &quot;SavGol&quot; (length of the filter window i.e. the number of coefficients) or &quot;FIR&quot; (length of the filter). </p><p>Must be an odd integer. If &quot;Auto&quot;, a fitting size is chosen automatically.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sb_filter_window_size.setSpecialValueText(QCoreApplication.translate("ParameterInputs", u"Auto", None))
#if QT_CONFIG(tooltip)
        self.label_4.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Only used if <span style=\" font-weight:700;\">Filter Method</span> is &quot;Powerline&quot;.</p><p>The powerline frequency (normally 50 Hz or 60 Hz).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("ParameterInputs", u"Powerline Frequency", None))
        self.combo_standardize_method.setText("")
        self.combo_filter_method.setText("")
        self.label_6.setText(QCoreApplication.translate("ParameterInputs", u"Method Parameters", None))
        self.label_16.setText(QCoreApplication.translate("ParameterInputs", u"Window Size:", None))
#if QT_CONFIG(tooltip)
        self.label_5.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Clean the signal using a pre-defined signal processing pipeline</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.label_5.setWhatsThis(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Different signal cleaning pipelines. For sources see 'Help'.</p><p>Implemented via the `neurokit2` python package.</p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.label_5.setText(QCoreApplication.translate("ParameterInputs", u"Pipeline:", None))
        self.label_14.setText(QCoreApplication.translate("ParameterInputs", u"Filter Method:", None))
#if QT_CONFIG(tooltip)
        self.icon_pipeline_status.setToolTip(QCoreApplication.translate("ParameterInputs", u"Shows a checkmark if the current section has been processed using a pipeline", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.icon_filter_status.setToolTip(QCoreApplication.translate("ParameterInputs", u"Shows a checkmark if the current section has been filtered", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.icon_standardize_status.setToolTip(QCoreApplication.translate("ParameterInputs", u"Shows a checkmark if the current section has been standardized", None))
#endif // QT_CONFIG(tooltip)
        self.tab_widget_parameter_inputs.setTabText(self.tab_widget_parameter_inputs.indexOf(self.tab_processing), QCoreApplication.translate("ParameterInputs", u"Pre-Processing", None))
        self.label_7.setText(QCoreApplication.translate("ParameterInputs", u"Detection Method:", None))
        self.combo_peak_method.setText("")
        self.peak_elgendi_ppg_info.setHtml(QCoreApplication.translate("ParameterInputs", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Algorithm for detecting peaks in a PPG signal, described <a href=\"https://doi.org/10.1371/journal.pone.0076585\"><span style=\" text-decoration: underline; color:#1e3260;\">here</span></a></p></body></html>", None))
        self.label_peak_window.setText(QCoreApplication.translate("ParameterInputs", u"Peak Window", None))
        self.peak_elgendi_ppg_peakwindow.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.beatWindowLabel.setText(QCoreApplication.translate("ParameterInputs", u"Beat Window", None))
        self.peak_elgendi_ppg_beatwindow.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.beatOffsetLabel.setText(QCoreApplication.translate("ParameterInputs", u"Beat Offset", None))
        self.peak_elgendi_ppg_beatoffset.setSuffix("")
        self.minimumDelayLabel.setText(QCoreApplication.translate("ParameterInputs", u"Minimum Delay", None))
        self.peak_elgendi_ppg_mindelay.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.label_22.setText(QCoreApplication.translate("ParameterInputs", u"Search Radius", None))
        self.peak_local_max_info.setHtml(QCoreApplication.translate("ParameterInputs", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Detects peaks by finding the highest point in a window of the selected size around the current point.</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.minDistanceLabel.setToolTip(QCoreApplication.translate("ParameterInputs", u"Minimum allowed distance between two consecutive peaks", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.minDistanceLabel.setWhatsThis(QCoreApplication.translate("ParameterInputs", u"After a peak is detected, how many values to skip ahead before starting to search for the next peak", None))
#endif // QT_CONFIG(whatsthis)
        self.minDistanceLabel.setText(QCoreApplication.translate("ParameterInputs", u"Min. Distance", None))
        self.peak_local_min_info.setHtml(QCoreApplication.translate("ParameterInputs", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Detects peaks by finding the lowest point in a window of the selected size around the current point.</p></body></html>", None))
        self.label_23.setText(QCoreApplication.translate("ParameterInputs", u"Search Radius", None))
#if QT_CONFIG(tooltip)
        self.minDistanceLabel_2.setToolTip(QCoreApplication.translate("ParameterInputs", u"Minimum allowed distance between two consecutive minima", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.minDistanceLabel_2.setWhatsThis(QCoreApplication.translate("ParameterInputs", u"After a minimum is detected, how many values to skip ahead before starting to search for the next minimum", None))
#endif // QT_CONFIG(whatsthis)
        self.minDistanceLabel_2.setText(QCoreApplication.translate("ParameterInputs", u"Min. Distance", None))
        self.peak_neurokit2_info.setHtml(QCoreApplication.translate("ParameterInputs", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Finds R-peaks in an ECG signal using the specified method/algorithm.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">More Info: <a href=\"https://github.com/neuropsychology/NeuroKit/issues/476\"><span style=\" text-decoration: underline; color:#038387;\">Github Discussion</span></a></p>\n"
"<p style=\" margin-top:0px; mar"
                        "gin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Algorithms: <a href=\"https://neuropsychology.github.io/NeuroKit/functions/ecg.html#ecg-peaks\"><span style=\" text-decoration: underline; color:#038387;\">Function documentation</span></a></p></body></html>", None))
        self.label_10.setText(QCoreApplication.translate("ParameterInputs", u"No adjustable parameters", None))
        self.smoothingWindowLabel.setText(QCoreApplication.translate("ParameterInputs", u"Smoothing Window", None))
        self.peak_neurokit2_smoothwindow.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.label_27.setText(QCoreApplication.translate("ParameterInputs", u"Average Window", None))
        self.peak_neurokit2_avgwindow.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.label_28.setText(QCoreApplication.translate("ParameterInputs", u"Grad. Thresh. Weight", None))
        self.label_29.setText(QCoreApplication.translate("ParameterInputs", u"Min. Length Weight", None))
        self.label_30.setText(QCoreApplication.translate("ParameterInputs", u"Minimum Delay", None))
        self.peak_neurokit2_mindelay.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
#if QT_CONFIG(tooltip)
        self.label_8.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Set the minimum squared slope change to detect R-peaks in the ECG signal. </p><p>Higher values reduce noise detections but may miss some peaks; lower values increase sensitivity but may include noise. </p><p>The unit is (volts/sample)^2.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_8.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Threshold</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_ssf_threshold.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Set the minimum squared slope change to detect R-peaks in the ECG signal. </p><p>Higher values reduce noise detections but may miss some peaks; lower values increase sensitivity but may include noise. </p><p>The unit is (volts/sample)^2.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.beforeLabel.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Search window size (in seconds) before R-peak candidate</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.beforeLabel.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Before</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_ssf_before.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Search window size (in seconds) before R-peak candidate</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.peak_ssf_before.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
#if QT_CONFIG(tooltip)
        self.afterLabel.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Search window size (in seconds) after R-peak candidate</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.afterLabel.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>After</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_ssf_after.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Search window size (in seconds) after R-peak candidate</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.peak_ssf_after.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
#if QT_CONFIG(tooltip)
        self.windowLabel.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Set the threshold for detecting significant changes in the second derivative of the normalized ECG signal.</p><p>Lower values increase sensitivity to minor variations, while higher values focus on more prominent features.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.windowLabel.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Tolerance</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_gamboa_tol.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Set the threshold for detecting significant changes in the second derivative of the normalized ECG signal.</p><p>Lower values increase sensitivity to minor variations, while higher values focus on more prominent features.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_9.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Length of one data segment (in seconds) used in the segment-wise processing of the ECG signal.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Window Seconds</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_emrich_window_seconds.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Length of one data segment (in seconds) used in the segment-wise processing of the ECG signal.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.peak_emrich_window_seconds.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
#if QT_CONFIG(tooltip)
        self.windowOverlapLabel.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Overlap percentage (0 = 0%, 1 = 100%) of the data segments used in the segment-wise computation.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.windowOverlapLabel.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Window Overlap</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_emrich_window_overlap.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Overlap percentage (0 = 0%, 1 = 100%) of the data segments used in the segment-wise computation.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.acceleratedLabel.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Enables the data pre-processing in which the input signal is reduced only to local maxima which reduces the computation time by one order of magnitude while the performance remains comparable.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.acceleratedLabel.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Accelerated</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_emrich_accelerated.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Enables the data pre-processing in which the input signal is reduced only to local maxima which reduces the computation time by one order of magnitude while the performance remains comparable.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.thresholdLabel_2.setToolTip(QCoreApplication.translate("ParameterInputs", u"The tolerance for peak acceptance. This value is a percentage of the signal's maximum value. Only peaks found above this tolerance will be finally considered as actual peaks.", None))
#endif // QT_CONFIG(tooltip)
        self.thresholdLabel_2.setText(QCoreApplication.translate("ParameterInputs", u"Threshold", None))
#if QT_CONFIG(tooltip)
        self.peak_promac_threshold.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>The tolerance for peak acceptance. This value is a percentage of the signal's maximum value. </p><p>Only peaks found above this tolerance will be finally considered as actual peaks.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.qRSComplexSizeLabel_2.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>The standard deviation of the Gaussian distribution used to represent the peak location probability. </p><p>This value should be in milliseconds and is usually taken as the size of QRS complexes.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.qRSComplexSizeLabel_2.setText(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>Gaussian SD</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.peak_promac_gaussian_sd.setToolTip(QCoreApplication.translate("ParameterInputs", u"<html><head/><body><p>The standard deviation of the Gaussian distribution used to represent the peak location probability. </p><p>This value should be in milliseconds and is usually taken as the size of QRS complexes.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.peak_promac_gaussian_sd.setSuffix(QCoreApplication.translate("ParameterInputs", u" ms", None))
        self.peak_neurokit2_algorithm_used.setText("")
        self.algorithmLabel.setText(QCoreApplication.translate("ParameterInputs", u"Algorithm", None))
        self.peak_xqrs_peak_dir.setText("")
        self.searchRadiusLabel.setText(QCoreApplication.translate("ParameterInputs", u"Search Radius", None))
        self.adjustPeaksLabel.setText(QCoreApplication.translate("ParameterInputs", u"Adjust Peaks", None))
        self.peak_xqrs_info.setHtml(QCoreApplication.translate("ParameterInputs", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Uses XQRS detection from the 'wfdb' library, with a slightly modified peak correction step afterwards.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Can take a while to finish when used on sections longer than 1e6 samples.</p></body></html>", None))
        self.label_17.setText(QCoreApplication.translate("ParameterInputs", u"Min. Distance", None))
        self.tab_widget_parameter_inputs.setTabText(self.tab_widget_parameter_inputs.indexOf(self.tab_peak_detection), QCoreApplication.translate("ParameterInputs", u"Peak Detection", None))
        self.label_18.setText(QCoreApplication.translate("ParameterInputs", u"How to handle incomplete windows (i.e. those at the end of the signal):", None))
        self.sb_period_seconds.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.sb_every_seconds.setSuffix(QCoreApplication.translate("ParameterInputs", u" s", None))
        self.combo_incomplete_window_method.setText("")
        self.label_11.setText(QCoreApplication.translate("ParameterInputs", u"Create a new window every:", None))
        self.label_12.setText(QCoreApplication.translate("ParameterInputs", u"Window length:", None))
        self.tab_widget_parameter_inputs.setTabText(self.tab_widget_parameter_inputs.indexOf(self.tab_rate_calculation), QCoreApplication.translate("ParameterInputs", u"Rate Calculation", None))
    # retranslateUi

