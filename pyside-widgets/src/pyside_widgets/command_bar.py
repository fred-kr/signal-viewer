from PySide6 import QtCore, QtDesigner, QtGui, QtWidgets


class CommandBar(QtWidgets.QToolBar):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        fill: bool = True,
        alignment: QtCore.Qt.AlignmentFlag = QtCore.Qt.AlignmentFlag.AlignLeft,
    ) -> None:
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # When fill is True the actions will be stretched to fill the toolbar.
        # When fill is False the actions will use their sizeHint, and be aligned according to _alignment.
        self._fill = fill
        self._alignment = alignment

    def set_fill(self, fill: bool) -> None:
        """Enable or disable filling the toolbar with evenly distributed buttons."""
        self._fill = fill
        self.update()

    def get_fill(self) -> bool:
        return self._fill

    def set_alignment(self, alignment: QtCore.Qt.AlignmentFlag) -> None:
        """Set the alignment (e.g. Qt.AlignLeft or Qt.AlignRight) for non-fill mode."""
        self._alignment = alignment
        self.update()

    def get_alignment(self) -> QtCore.Qt.AlignmentFlag:
        return self._alignment

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        actions = self.actions()
        if not actions:
            return

        total_width = self.width()

        if self._fill:
            self._resize_fill(actions, total_width)
        else:
            self._resize_align(actions, total_width)

    def _resize_align(self, actions: list[QtGui.QAction], total_width: int) -> None:
        # --- NON-FILL MODE: Use each widget's natural size and align the group ---
        # First, compute the total width required by the visible widgets.
        total_required_width = 0
        widget_geometries: list[tuple[QtWidgets.QWidget, int]] = []  # Store tuples of (widget, width)
        for action in actions:
            widget = self.widgetForAction(action)
            if not widget:
                continue
            w = widget.sizeHint().width()
            widget_geometries.append((widget, w))
            total_required_width += w

        # Determine starting x based on alignment.
        if total_required_width > total_width:
            # If actions exceed available width, simply start at 0.
            start_x = 0
        elif self._alignment == QtCore.Qt.AlignmentFlag.AlignRight:
            start_x = total_width - total_required_width
        else:
            # Default to left alignment.
            start_x = 0

        x = start_x
        for widget, w in widget_geometries:
            widget.setGeometry(x, 0, w, self.height())
            x += w

    def _resize_fill(self, actions: list[QtGui.QAction], total_width: int) -> None:
        # --- FILL MODE: Evenly distribute non-separator actions across the full width ---
        non_separator_actions = [a for a in actions if not a.isSeparator()]
        num_non_separator = len(non_separator_actions)

        # Calculate the total fixed width taken by separator widgets.
        separator_total_width = 0
        for action in actions:
            if action.isSeparator():
                if widget := self.widgetForAction(action):
                    separator_total_width += widget.sizeHint().width()

        remaining_width = total_width - separator_total_width
        if remaining_width < 0:
            remaining_width = total_width  # Fallback if separators exceed total width

        base_width = remaining_width // num_non_separator if num_non_separator > 0 else 0
        remainder = remaining_width % num_non_separator if num_non_separator > 0 else 0

        x = 0
        for action in actions:
            widget = self.widgetForAction(action)
            if not widget:
                continue

            if action.isSeparator():
                w = widget.sizeHint().width()
            else:
                # Distribute any extra pixel(s) to the first few non-separator buttons.
                w = base_width + (1 if remainder > 0 else 0)
                if remainder > 0:
                    remainder -= 1

            widget.setGeometry(x, 0, w, self.height())
            x += w

    fill = QtCore.Property(bool, get_fill, set_fill)
    alignment = QtCore.Property(QtCore.Qt.AlignmentFlag, get_alignment, set_alignment)


DOM_XML = """
<ui language='c++'>
    <widget class='CommandBar' name='commandBar'>
        <property name='fill'>
            <bool>true</bool>
        </property>
        <property name='alignment'>
            <enum>AlignLeft</enum>
        </property>
    </widget>
</ui>
"""


class CommandBarPlugin(QtDesigner.QDesignerCustomWidgetInterface):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def createWidget(self, parent: QtWidgets.QWidget) -> CommandBar:
        return CommandBar(parent=parent)

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
        return "CommandBar"

    def toolTip(self) -> str:
        return ""

    def whatsThis(self) -> str:
        return self.toolTip()
