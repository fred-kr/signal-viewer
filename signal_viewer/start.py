def gui() -> None:
    import multiprocessing

    multiprocessing.freeze_support()
    import argparse
    import os
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-opengl", action="store_false", help="Don't use OpenGL for rendering")
    parser.add_argument("-c", "--console", action="store_true", help="Enable Jupyter console")
    parser.add_argument("--reset-settings", action="store_true", help="Cleans stored settings and resets to defaults")
    parser.add_argument("--version", action="store_true", help="Print the version and exit")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Build the application off-screen, then exit. Used to smoke-test packaged builds.",
    )
    args = parser.parse_args()

    if args.version:
        from importlib.metadata import PackageNotFoundError, version

        try:
            print(version("signal-viewer"))
        except PackageNotFoundError:
            print("unknown")
        return

    from loguru import logger

    logger.remove()

    app_name = "SignalViewer - Debug" if args.debug else "SignalViewer"
    org_name = "QuackTech"
    from PySide6 import QtCore, QtWidgets

    # Set before anything that depends on QStandardPaths or QSettings. The static setters work without an
    # application instance.
    QtWidgets.QApplication.setOrganizationName(org_name)
    QtWidgets.QApplication.setApplicationName(app_name)
    # QtWidgets.QApplication.setStyle("Fusion")

    if args.debug:
        logger.add(sys.stderr, colorize=True, backtrace=True, diagnose=True)
        # A frozen app may run from a read-only location (or "/" on macOS), so the log goes to the per-user app
        # data directory instead of the working directory.
        log_dir = Path(
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.AppLocalDataLocation)
        )
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(log_dir / "debug.log")
        logger.info(f"Debug log: {log_dir / 'debug.log'}")
        os.environ["QT_LOGGING_RULES"] = "qt.pyside.libpyside.warning=true"  # shows missing slot decorator warnings

    if args.reset_settings:
        log_id = logger.add(sys.stderr, colorize=True, backtrace=True, diagnose=True)
        logger.info(f"Removing stored settings for {org_name} - {app_name}...")
        try:
            import pyside_config

            pyside_config.clean()
            logger.success("Cleanup successful, app will use default settings.")
        except ImportError:
            logger.error("Error importing pyside_config module. Unable to reset settings.")
        logger.remove(log_id)

    use_opengl = args.no_opengl
    if use_opengl:
        os.environ["QSG_RHI_BACKEND"] = "opengl"

    if args.console:
        os.environ["DEV"] = "1"

    if args.self_test:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        use_opengl = False

    import pyqtgraph as pg

    pg.setConfigOptions(
        useOpenGL=use_opengl,
        enableExperimental=use_opengl,
        segmentedLineMode="auto",
    )
    from signal_viewer.sv_app import SVApp

    app = QtWidgets.QApplication(sys.argv)

    sv_app = SVApp()
    sv_app.gui.show()

    if args.self_test:
        QtCore.QTimer.singleShot(0, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    gui()
