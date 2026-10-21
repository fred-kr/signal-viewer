"""
Pytest bootstrap.

`pyside_config` (imported by `signal_viewer.sv_config`) refuses to import until a Qt organization and application
name are set, because it stores settings through `QSettings`. Set them here, before any test module imports the
package. The application name differs from the real one ("SignalViewer") so test runs never read or write the
user's stored settings.

Widget tests (help window, parameter dock) need a `QApplication`; the `offscreen` platform plugin lets it run
without a display, on CI included.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets

QtWidgets.QApplication.setOrganizationName("QuackTech")
QtWidgets.QApplication.setApplicationName("SignalViewer-Tests")


import pytest


@pytest.fixture(scope="session")
def qapp() -> QtWidgets.QApplication:
    """
    The one `QApplication` of the test session (off-screen).

    A `QApplication` is also a `QCoreApplication`, so tests that only need queued signal delivery (worker threads)
    use the same fixture.
    """
    app = QtWidgets.QApplication.instance()
    if isinstance(app, QtWidgets.QApplication):
        return app
    return QtWidgets.QApplication([])
