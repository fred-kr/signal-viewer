from PySide6 import QtDesigner

from pyside_widgets.toggle_switch import (
    ToggleSwitch,  # noqa: F401 # type: ignore
    ToggleSwitchPlugin,
)

if __name__ == "__main__":
    QtDesigner.QPyDesignerCustomWidgetCollection.addCustomWidget(ToggleSwitchPlugin())
