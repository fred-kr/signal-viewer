def gui() -> None:
    import multiprocessing

    multiprocessing.freeze_support()
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-opengl", action="store_false", help="Don't use OpenGL for rendering")
    parser.add_argument("-c", "--console", action="store_true", help="Enable Jupyter console")
    parser.add_argument("--reset-settings", action="store_true", help="Cleans stored settings and resets to defaults")
    args = parser.parse_args()

    from loguru import logger

    logger.remove()

    if args.debug:
        logger.add(sys.stderr, colorize=True, backtrace=True, diagnose=True)
        logger.add("debug.log")
        app_name = "SignalViewer - Debug"
        os.environ["QT_LOGGING_RULES"] = "qt.pyside.libpyside.warning=true" # shows missing slot decorator warnings
    else:
        app_name = "SignalViewer"
    org_name = "QuackTech"
    from PySide6 import QtWidgets

    QtWidgets.QApplication.setOrganizationName(org_name)
    QtWidgets.QApplication.setApplicationName(app_name)
    QtWidgets.QApplication.setStyle("Fusion")

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

    import pyqtgraph as pg

    pg.setConfigOptions(
        useOpenGL=use_opengl,
        enableExperimental=use_opengl,
        segmentedLineMode="on",
    )
    from signal_viewer.sv_app import SVApp

    app = QtWidgets.QApplication(sys.argv)

    sv_app = SVApp()
    sv_app.gui.show()

    app.exec()


if __name__ == "__main__":
    gui()
