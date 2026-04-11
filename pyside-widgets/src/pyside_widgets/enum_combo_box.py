import enum
import typing as t
from collections.abc import Callable

from PySide6 import QtCore, QtDesigner, QtGui, QtWidgets

ItemDataRole = QtCore.Qt.ItemDataRole

PLACEHOLDER_TEXT: t.Final = "Select..."
NO_SELECTION_TEXT: t.Final = "<No Selection>"


class EnumComboBox[T: enum.Enum](QtWidgets.QComboBox):
    """
    QComboBox variant that uses the provided python Enum class to populate the combo box items.

    Inspired by [`superqt.QEnumComboBox`](https://pyapp-kit.github.io/superqt/widgets/qenumcombobox/#qenumcombobox).
    """

    sig_current_enum_changed = QtCore.Signal(object)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        enum_class: type[T] | None = None,
        allow_none: bool = False,
    ) -> None:
        super().__init__(parent)

        self._enum_class = enum_class
        self._enum_model = QtGui.QStandardItemModel(self)
        self._allow_none = allow_none

        self.setPlaceholderText(PLACEHOLDER_TEXT)

        self.set_enum_class(enum_class)
        self.currentIndexChanged.connect(self._on_current_index_changed)

    def allowNone(self) -> bool:
        """Whether to allow the combo box to have no selection."""
        return self._allow_none

    def setAllowNone(self, allow_none: bool) -> None:
        """Setter of property `allowNone`."""
        self._allow_none = allow_none

    def set_enum_class(
        self,
        enum_class: type[enum.Enum] | None,
        text_data: Callable[[enum.Enum], str] | None = None,
        icon_data: Callable[[enum.Enum], QtGui.QIcon] | None = None,
        doc_data: Callable[[enum.Enum], str] | None = None,
    ) -> None:
        """
        Sets the enum class for the combo box and populates it with the enum members.

        Args:
            enum_class: The enum class to be used in the combo box.
            text_data: Optional callable to provide custom text for each enum member.
                Defaults to None, using the enum member's name if not provided.
            icon_data: Optional callable to provide custom icon for each enum member.
                Defaults to None, using the default icon if not provided.
            doc_data: Optional callable to provide custom documentation for each enum member.
                Defaults to None, using the enum member's docstring if not provided.
        """
        self._enum_model.clear()
        self._enum_class = enum_class
        if enum_class is None:
            return

        for enum_member in enum_class:
            name = text_data(enum_member) if text_data is not None else enum_member.name
            item = QtGui.QStandardItem(name)
            item.setData(enum_member, role=ItemDataRole.UserRole)
            if icon_data is not None:
                item.setIcon(icon_data(enum_member))
            if doc_data is not None:
                item.setToolTip(doc_data(enum_member))
            self._enum_model.appendRow(item)

        if self._allow_none:
            none_item = QtGui.QStandardItem(NO_SELECTION_TEXT)
            none_item.setData(None, role=ItemDataRole.UserRole)
            self._enum_model.insertRow(0, none_item)

        self.setModel(self._enum_model)

    def current_enum(self) -> T | None:
        """Returns the currently selected enum value.

        If the data associated with the current item in the combo box is not a member of the enum class, returns None.

        Returns:
            The current enum value if it exists in the enum class, otherwise None.
        """
        if self._enum_class is None:
            return None
        if self._allow_none and self.currentIndex() == 0:
            return None
        return self.currentData(role=ItemDataRole.UserRole)
        # return None if data not in self._enum_class else data

    def set_current_enum(self, value: T | None) -> None:
        """Sets the current combo box item to the provided enum member.

        Args:
            value (T): The enum member to be set as the current item.
        """
        if self._enum_class is None:
            raise ValueError("Enum class not set")
        if value is None and not self._allow_none:
            raise ValueError("Cannot set None if allow_none is False")
        index = self.findData(value, role=ItemDataRole.UserRole)
        if index >= 0:
            self.setCurrentIndex(index)

    @QtCore.Slot(int)
    def _on_current_index_changed(self, index: int) -> None:
        # enum_member = self.current_enum()
        # if enum_member is not None:
        self.sig_current_enum_changed.emit(self.current_enum())

    allowNone = QtCore.Property(bool, allowNone, setAllowNone)  # type: ignore


DOM_XML = """
<ui language='c++'>
    <widget class='EnumComboBox' name='enumComboBox'>
        <property name='allowNone'>
            <bool>false</bool>
        </property>
    </widget>
</ui>
"""


class EnumComboBoxPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def createWidget(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        return EnumComboBox(parent=parent)

    def domXml(self) -> str:
        return DOM_XML

    def group(self) -> str:
        return ""

    def icon(self) -> QtGui.QIcon:
        return QtGui.QIcon()

    def includeFile(self) -> str:
        return __name__

    def initialize(self, core: QtDesigner.QDesignerFormEditorInterface) -> None:
        if self._initialized:
            return

        self._initialized = True

    def isContainer(self) -> bool:
        return False

    def isInitialized(self) -> bool:
        return self._initialized

    def name(self) -> str:
        return "EnumComboBox"

    def toolTip(self) -> str:
        return "QComboBox variant that uses a python Enum class to populate the combo box items."

    def whatsThis(self) -> str:
        return self.toolTip()
