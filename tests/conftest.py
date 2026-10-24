"""
Pytest bootstrap.

`signal_viewer.sv_config` declares its `pyside_config` groups at import time, which needs a `QSettings` store.
Before any test module imports the package, point `pyside_config` at an INI file in a fresh temporary directory, so
test runs never read or write the user's stored settings. The organization and application name are set as well
(for `QStandardPaths`); the application name differs from the real one ("SignalViewer") as a second safeguard.

Widget tests (help window, parameter dock) need a `QApplication`; the `offscreen` platform plugin lets it run
without a display, on CI included.
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pyside_config
from PySide6 import QtCore, QtWidgets

QtWidgets.QApplication.setOrganizationName("QuackTech")
QtWidgets.QApplication.setApplicationName("SignalViewer-Tests")

_SETTINGS_FILE = Path(tempfile.mkdtemp(prefix="signal-viewer-tests-")) / "settings.ini"
pyside_config.configure(lambda: QtCore.QSettings(str(_SETTINGS_FILE), QtCore.QSettings.Format.IniFormat))


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
