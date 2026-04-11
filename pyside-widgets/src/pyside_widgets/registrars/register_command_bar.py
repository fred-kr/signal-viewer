from PySide6 import QtDesigner

from pyside_widgets.command_bar import (
    CommandBar,  # noqa: F401 # type: ignore
    CommandBarPlugin,
)

if __name__ == "__main__":
    QtDesigner.QPyDesignerCustomWidgetCollection.addCustomWidget(CommandBarPlugin())
