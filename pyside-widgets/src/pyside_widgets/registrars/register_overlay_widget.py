from PySide6 import QtDesigner

from pyside_widgets.overlay_widget import (
    OverlayWidget,  # noqa: F401 # type: ignore
    OverlayWidgetPlugin,
)

if __name__ == "__main__":
    QtDesigner.QPyDesignerCustomWidgetCollection.addCustomWidget(OverlayWidgetPlugin())
