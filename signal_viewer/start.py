# This Python file uses the following encoding: utf-8

import sys

# import traceback
# from types import TracebackType
#
# from loguru import logger
from PySide6 import QtWidgets


# def _uncaught_exception_hook(exc_type: type, exc_value: Exception, exc_traceback: TracebackType | None) -> None:
#     logger.error("".join(traceback.format_tb(exc_traceback)) + str(exc_value))
#     sys.__excepthook__(exc_type, exc_value, exc_traceback)


# sys.excepthook = _uncaught_exception_hook


def _set_credentials(app: QtWidgets.QApplication) -> None:
    app.setOrganizationDomain("https://fred-kr.github.io/signal-viewer-v2/")
    app.setOrganizationName("QuackTech")
    app.setApplicationName("SignalViewer")
    # app.setApplicationVersion(sv_config.get_version())


def gui() -> None:
    QtWidgets.QApplication.setOrganizationDomain("https://fred-kr.github.io/signal-viewer-v2/")
    QtWidgets.QApplication.setOrganizationName("QuackTech")
    QtWidgets.QApplication.setApplicationName("SignalViewer")
    from signal_viewer.sv_app import SVApp
    app = QtWidgets.QApplication(sys.argv)

    # _set_credentials(app)

    sv_app = SVApp()
    sv_app.gui.show()

    app.exec()


if __name__ == "__main__":
    gui()
