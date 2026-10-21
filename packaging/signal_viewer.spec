# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build definition for SignalViewer (Windows and macOS).

Build from the repo root:

    uv run pyinstaller packaging/signal_viewer.spec --noconfirm --clean

Output: `dist/SignalViewer/` (one-directory bundle); on macOS additionally `dist/SignalViewer.app`.
"""

import sys
import tomllib
from pathlib import Path

import PySide6
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

ROOT = Path(SPECPATH).parent  # SPECPATH is injected by PyInstaller: the directory holding this file
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
PYSIDE_DIR = Path(PySide6.__file__).parent
ICON_DIR = ROOT / "packaging" / "icons"

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# --- data files -------------------------------------------------------------------------------------------------
# The user guide (plain HTML, shown by sv_help.HelpWindow in a QTextBrowser) is located at runtime via
# Path(__file__).parent / "doc" (see sv_site.py), so it has to land at the same relative location inside the bundle.
datas = [
    (str(ROOT / "signal_viewer" / "doc"), "signal_viewer/doc"),
    *collect_data_files("mne"),
    *copy_metadata("signal-viewer"),  # makes importlib.metadata.version("signal-viewer") work (--version flag)
]

# --- extra binaries ---------------------------------------------------------------------------------------------
binaries = []

# --- hidden imports -------------------------------------------------------------------------------------------
hiddenimports = [
    *collect_submodules("mne"),  # mne resolves submodules through lazy_loader, invisible to static analysis
    *collect_submodules("ts2vg"),  # neurokit2's ECG_Emrich_2023 method imports ts2vg inside a try block; its
    # Cython modules import ts2vg.graph._base at C level, which the analysis cannot see
    "PySide6.QtSvg",  # pulls in the qsvgicon/qsvg plugins needed for the SVG icons compiled into rc_resources
    "sklearn.linear_model",  # imported inside functions in sv_plots/result_plot.py
    "sklearn.model_selection",
    "sklearn.preprocessing",
]

# --- excludes -------------------------------------------------------------------------------------------------
# Unused pieces that would otherwise inflate the bundle. The Qt entries are a safety net: PyInstaller only bundles
# imported Qt modules, but a transitive import would silently add hundreds of MB.
#
# Not excluded on purpose:
# - pyarrow: polars' Excel reader (fastexcel) returns data through pyarrow.
excludes = [
    "tkinter",
    "tables",  # optional pandas HDF5 backend, never used here
    "numexpr",  # optional pandas accelerator, never used here
    # The Jupyter console (View menu, DEV=1 only) lives behind a lazy import in pyside-widgets, so static analysis
    # does not pull the Jupyter stack in; listing it keeps a stray transitive import from adding ~30 MB.
    "qtconsole",
    "IPython",
    "ipykernel",
    "jupyter_client",
    "jupyter_core",
    "PySide6.QtDesigner",  # only pyside_widgets.plugins (Qt Designer plugins) import it; never at runtime
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtLocation",
    "PySide6.QtPositioning",
    "PySide6.QtBluetooth",
    "PySide6.QtRemoteObjects",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebSockets",
    "PySide6.QtWebChannel",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
# Plugins that PyInstaller's Qt hooks collect wholesale but that nothing here uses. Each drags in extra Qt
# libraries: the virtual keyboard pulls Qt6Quick and Qt6Qml, and the Designer plugin folder (should QtDesigner ever
# be imported again) contains a web-view plugin that pulls the 200 MB Qt WebEngine.
_STRAY_QT = (
    "plugins/designer/",
    "plugins/platforminputcontexts/qtvirtualkeyboard",
    "plugins/imageformats/qpdf",
    "plugins/sqldrivers/qsqlodbc",
    "plugins/sqldrivers/qsqlpsql",
    "plugins/sqldrivers/qsqlmimer",
    "plugins/sqldrivers/qsqloci",
    "plugins/sqldrivers/qsqlibase",
    "Qt6Quick",
    "Qt6Qml",
    "Qt6VirtualKeyboard",
    "Qt6Pdf.",
    "Qt6WebEngine",
    "Qt6WebChannel",
    "Qt6Positioning",
    "QtWebEngineProcess",
    "resources/qtwebengine",
    "translations/qtwebengine",
    "libQt6Quick",
    "libQt6Qml",
    "libQt6VirtualKeyboard",
    "libQt6Pdf.",
    "QtQuick.framework",
    "QtQml",
    "QtWebEngine",
    "QtWebChannel.framework",
    "QtPositioning.framework",
    "QtVirtualKeyboard.framework",
    "QtPdf.framework",
)


def _is_stray_qt(dest: str) -> bool:
    dest = dest.replace("\\", "/")
    return dest.startswith(("PySide6/", "PySide6/Qt/")) and any(token in dest for token in _STRAY_QT)


a.binaries = [entry for entry in a.binaries if not _is_stray_qt(entry[0])]
a.datas = [entry for entry in a.datas if not _is_stray_qt(entry[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="SignalViewer",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # GUI app: no console window on Windows. Diagnostics go to --debug's log file.
    icon=str(ICON_DIR / ("app_icon.ico" if IS_WIN else "app_icon.icns")),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SignalViewer",
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name="SignalViewer.app",
        icon=str(ICON_DIR / "app_icon.icns"),
        bundle_identifier="com.quacktech.signalviewer",
        version=VERSION,
        info_plist={
            "CFBundleName": "SignalViewer",
            "CFBundleDisplayName": "SignalViewer",
            "CFBundleShortVersionString": VERSION,
            "NSHighResolutionCapable": True,
            "NSPrincipalClass": "NSApplication",
            "LSMinimumSystemVersion": "12.0",
        },
    )
