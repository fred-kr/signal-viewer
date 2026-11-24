# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'param_inputs_new.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
    QSpacerItem, QToolButton, QVBoxLayout, QWidget)

from pyside_widgets import (CommandBar, EnumComboBox)
from . import rc_resources

class Ui_processingInputs(object):
    def setupUi(self, processingInputs):
        if not processingInputs.objectName():
            processingInputs.setObjectName(u"processingInputs")
        processingInputs.resize(280, 76)
        self.verticalLayout = QVBoxLayout(processingInputs)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cb_processing = CommandBar(processingInputs)
        self.cb_processing.setObjectName(u"cb_processing")
        self.cb_processing.setProperty(u"fill", True)
        self.cb_processing.setProperty(u"alignment", Qt.AlignmentFlag.AlignLeading)

        self.verticalLayout.addWidget(self.cb_processing)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_8 = QLabel(processingInputs)
        self.label_8.setObjectName(u"label_8")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy)
        self.label_8.setMinimumSize(QSize(0, 24))

        self.horizontalLayout.addWidget(self.label_8)

        self.pipeline = EnumComboBox(processingInputs)
        self.pipeline.setObjectName(u"pipeline")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pipeline.sizePolicy().hasHeightForWidth())
        self.pipeline.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.pipeline)

        self.toolButton = QToolButton(processingInputs)
        self.toolButton.setObjectName(u"toolButton")
        icon = QIcon()
        iconThemeName = u"EditSettings"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u":/icons/EditSettings.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.toolButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.toolButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(processingInputs)

        QMetaObject.connectSlotsByName(processingInputs)
    # setupUi

    def retranslateUi(self, processingInputs):
        processingInputs.setWindowTitle(QCoreApplication.translate("processingInputs", u"Form", None))
        self.label_8.setText(QCoreApplication.translate("processingInputs", u"Pipeline", None))
        self.toolButton.setText(QCoreApplication.translate("processingInputs", u"...", None))
    # retranslateUi

