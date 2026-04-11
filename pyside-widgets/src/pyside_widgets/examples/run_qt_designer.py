import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets


def run_qt_designer() -> None:
    main_path = Path(__file__).parent.parent.absolute()
    env = QtCore.QProcessEnvironment.systemEnvironment()
    env.insert("PYSIDE_DESIGNER_PLUGINS", os.path.join(main_path, "registrars"))

    app = QtWidgets.QApplication(sys.argv)  # type: ignore # noqa: F841
    QtWidgets.QMessageBox.information(
        None,  # type: ignore
        "PySide6 Designer",
        f"""<p> This example will attempt to run Qt Designer, including the custom pyside-widgets. </p>
		<p>After clicking <b>OK</b>, Qt Designer should be started.</p>
		<p>This example assumes that you are using the right python environment in which PySide6 is installed.
		This means that Qt Designer can be launched by running: <tt>pyside6-designer</tt> -
		if not, this example will not work.</p>
		<p>This script automatically sets the <tt>PYSIDE_DESIGNER_PLUGINS</tt> environment variable to <tt>./registrars</tt>
		so that all of the widgets in this repository should appear in the widget box in the <b>pyside-widgets
		</b>group-box.</p>

		<p>Currently looking for Widgets/Registrars using path: <tt>{main_path}</tt></p>
		""",
    )

    designer_process = QtCore.QProcess()
    designer_process.setProcessEnvironment(env)
    designer_process.setProcessChannelMode(
        QtCore.QProcess.ProcessChannelMode.ForwardedChannels
    )  # Show output in console
    designer_process.start("pyside6-designer")

    if not designer_process.waitForStarted():
        print("Designer process failed to start")
        QtWidgets.QMessageBox.critical(
            None,  # type: ignore
            "PySide6 Designer",
            f"<p>Qt Designer (pyside6-designer) could not be started.  Please check that it is "
            f"installed and that the <tt>designer</tt> executable is in your "
            f"path.</p>"
            f"<p>The error message returned was:</p>"
            f"<p><tt>{designer_process.errorString()}</tt></p>",
        )
        sys.exit(1)

    designer_process.waitForFinished(-1)

    sys.exit(designer_process.exitCode())


if __name__ == "__main__":
    run_qt_designer()
