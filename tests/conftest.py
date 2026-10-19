"""
Pytest bootstrap.

`pyside_config` (imported by `signal_viewer.sv_config`) refuses to import until a Qt organization and application
name are set, because it stores settings through `QSettings`. Set them here, before any test module imports the
package. The application name differs from the real one ("SignalViewer") so test runs never read or write the
user's stored settings.
"""

from PySide6 import QtWidgets

QtWidgets.QApplication.setOrganizationName("QuackTech")
QtWidgets.QApplication.setApplicationName("SignalViewer-Tests")
