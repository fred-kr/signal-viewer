from PySide6 import QtDesigner

from pyside_widgets.enum_combo_box import (
    EnumComboBox,  # noqa: F401 # type: ignore
    EnumComboBoxPlugin,
)

if __name__ == "__main__":
    QtDesigner.QPyDesignerCustomWidgetCollection.addCustomWidget(EnumComboBoxPlugin())
