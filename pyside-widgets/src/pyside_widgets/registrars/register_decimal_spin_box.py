from PySide6 import QtDesigner

from pyside_widgets.decimal_spin_box import (
    DecimalSpinBox,  # noqa: F401 # type: ignore
    DecimalSpinBoxPlugin,
)

if __name__ == "__main__":
    QtDesigner.QPyDesignerCustomWidgetCollection.addCustomWidget(DecimalSpinBoxPlugin())
