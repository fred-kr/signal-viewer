import enum
import types

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from pyside_widgets import (
    AnimatedToggleSwitch,
    ColorPickerButton,
    CommandBar,
    DataTreeWidget,
    DecimalSpinBox,
    EnumComboBox,
    GroupedComboBox,
    JupyterConsoleWindow,
    LabeledSlider,
    OverlayWidget,
    SearchableDataTreeWidget,
    SettingCard,
    ToggleSwitch,
)


class EnumA(enum.Enum):
    A = 1
    B = 2
    C = 3


class SettingEnum(enum.Enum):
    DEFAULT = enum.auto()
    SETTING_A = enum.auto()
    SETTING_B = enum.auto()
    SETTING_C = enum.auto()


def example_func1() -> types.TracebackType | None:
    return example_func2()


def example_func2() -> types.TracebackType | None:
    try:
        raise ValueError("Some error")
    except ValueError:
        import sys

        return sys.exc_info()[2]


example_data = {
    "a list": [1, 2, 3, 4, 5, 6, {"nested1": "aaaaa", "nested2": "bbbbb"}, "seven"],
    "a dict": {"x": 1, "y": 2, "z": "three"},
    "an array": np.random.randint(10, size=(40, 10)),
    "a traceback": example_func2(),
    "a function": example_func1,
    "a class": DataTreeWidget,
}


def main() -> None:
    # print(QtWidgets.QStyleFactory.keys())
    QtWidgets.QApplication.setStyle("Fusion")
    app = QtWidgets.QApplication([])

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Widget Gallery")

    tab_widget = QtWidgets.QTabWidget()

    # GroupedComboBox
    grouped_cb_container = QtWidgets.QWidget()
    grouped_cb_layout = QtWidgets.QVBoxLayout(grouped_cb_container)
    grouped_combo_box = GroupedComboBox()
    grouped_combo_box.add_parent_item("Group 1")
    grouped_combo_box.add_child_item("Item 1", EnumA.A)
    grouped_combo_box.add_child_item("Item 2", EnumA.B)
    grouped_combo_box.add_child_item("Item 3", EnumA.C)
    grouped_combo_box.add_separator()
    grouped_combo_box.add_parent_item("Group 2")
    grouped_combo_box.add_child_item("Item 4", EnumA.A.value)
    grouped_combo_box.add_child_item("Item 5", EnumA.B.value)
    grouped_combo_box.add_child_item("Item 6", EnumA.C.value)
    grouped_combo_box.setCurrentIndex(1)
    grouped_combo_box.currentIndexChanged.connect(
        lambda: print(f"Selected item: {grouped_combo_box.currentText()}, item data: {grouped_combo_box.currentData()}")
    )

    grouped_cb_layout.addWidget(grouped_combo_box)
    grouped_cb_layout.addStretch()
    tab_widget.addTab(grouped_cb_container, "GroupedComboBox")

    # JupyterConsoleWindow
    jupyter_console = JupyterConsoleWindow(style="lightbg")
    jupyter_console.console.execute("print('Hello from Jupyter Console!')", True)
    tab_widget.addTab(jupyter_console, "JupyterConsoleWindow")

    # OverlayWidget
    base_widget = QtWidgets.QTextEdit("This is the base widget")
    overlay_widget = OverlayWidget(parent=base_widget)
    overlay_button = QtWidgets.QPushButton("Toggle Overlay")
    overlay_button.clicked.connect(
        lambda: overlay_widget.hide_overlay() if overlay_widget.isVisible() else overlay_widget.show_overlay()
    )
    overlay_button_container = QtWidgets.QWidget()
    layout_overlay = QtWidgets.QVBoxLayout(overlay_button_container)
    layout_overlay.addWidget(overlay_button)
    layout_overlay.addWidget(base_widget)

    tab_widget.addTab(overlay_button_container, "OverlayWidget")

    # EnumComboBox
    enum_cb_container = QtWidgets.QWidget()
    enum_cb_layout = QtWidgets.QVBoxLayout(enum_cb_container)
    enum_combo_box = EnumComboBox(enum_class=EnumA)
    enum_combo_box_2 = EnumComboBox(enum_class=SettingEnum, allow_none=True)

    btn_change_enum_class = QtWidgets.QPushButton("Change enum class")
    btn_change_enum_class.clicked.connect(lambda: enum_combo_box.set_enum_class(None))

    enum_cb_layout.addWidget(btn_change_enum_class)
    enum_cb_layout.addWidget(enum_combo_box, 1)
    enum_cb_layout.addWidget(enum_combo_box_2, 1)
    enum_cb_layout.addStretch()
    tab_widget.addTab(enum_cb_container, "EnumComboBox")
    # SettingCard
    setting_card_container = QtWidgets.QWidget()
    setting_card_layout = QtWidgets.QVBoxLayout(setting_card_container)
    setting_widget = EnumComboBox(enum_class=SettingEnum)
    setting_card = SettingCard(
        title="Example Setting",
        editor_widget=setting_widget,
        default_value=SettingEnum.DEFAULT,
        set_value_name="set_current_enum",
        description="This is a setting card with EnumComboBox as the editor widget",
        icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.Computer),
        reset_button=True,
    )

    setting_card_layout.addWidget(setting_card, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
    setting_card_layout.addStretch()
    tab_widget.addTab(setting_card_container, "SettingCard")

    # DataTreeWidget
    data_tree_container = QtWidgets.QWidget()
    data_tree_layout = QtWidgets.QVBoxLayout(data_tree_container)
    data_tree = DataTreeWidget(data=example_data)
    data_tree_layout.addWidget(data_tree)
    data_tree_layout.addStretch()
    tab_widget.addTab(data_tree_container, "DataTreeWidget")

    # SearchableDataTreeWidget
    searchable_data_tree_container = QtWidgets.QWidget()
    searchable_data_tree_layout = QtWidgets.QVBoxLayout(searchable_data_tree_container)
    searchable_data_tree = SearchableDataTreeWidget()
    searchable_data_tree.set_data(example_data)
    searchable_data_tree_layout.addWidget(searchable_data_tree)
    searchable_data_tree_layout.addStretch()
    tab_widget.addTab(searchable_data_tree_container, "SearchableDataTreeWidget")

    # DecimalSpinBox
    decimal_spin_box_container = QtWidgets.QWidget()
    decimal_spin_box_layout = QtWidgets.QVBoxLayout()
    decimal_spin_box = DecimalSpinBox()
    decimal_spin_box.setRange(0, 100)
    decimal_spin_box.setDecimals(2)
    decimal_spin_box.setValue(50.25)

    output = QtWidgets.QTextEdit()
    output.setReadOnly(True)

    decimal_spin_box.valueChanged.connect(lambda value: output.append(str(value)))  # type: ignore

    min_input = LabeledSlider(title="Minimum", title_pos=LabeledSlider.TitleLabelPosition.TOP_LEFT)
    min_input.setRange(-1_000, 1_000)
    min_input.setSingleStep(10)
    min_input.setValue(0)
    min_input.valueChanged.connect(decimal_spin_box.setMinimum)

    max_input = LabeledSlider(title="Maximum", title_pos=LabeledSlider.TitleLabelPosition.TOP_CENTER)
    # max_input.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignBottom)
    max_input.setRange(-1_000, 1_000)
    max_input.setSingleStep(10)
    max_input.setValue(100)
    max_input.valueChanged.connect(decimal_spin_box.setMaximum)

    step_input = LabeledSlider(title="Step Size", title_pos=LabeledSlider.TitleLabelPosition.LEFT)
    step_input.setRange(1, 1_000)
    step_input.setSingleStep(10)
    step_input.setValue(10)
    step_input.valueChanged.connect(decimal_spin_box.setSingleStep)

    controls_layout = QtWidgets.QVBoxLayout()
    controls_layout.addWidget(min_input)
    controls_layout.addWidget(max_input)
    controls_layout.addWidget(step_input)

    decimal_spin_box_layout.addWidget(decimal_spin_box)
    decimal_spin_box_layout.addWidget(output)
    decimal_spin_box_layout.addLayout(controls_layout)
    decimal_spin_box_layout.addStretch()
    decimal_spin_box_container.setLayout(decimal_spin_box_layout)

    tab_widget.addTab(decimal_spin_box_container, "DecimalSpinBox")

    # pyqtgraph.SpinBox
    spin_box_container = QtWidgets.QWidget()
    spin_box_layout = QtWidgets.QVBoxLayout()
    spin_box = pg.SpinBox(compactHeight=False)
    spin_box.setRange(-1_000, 1_000)
    spin_box.setSingleStep(10)
    spin_box.setValue(50)

    output = QtWidgets.QTextEdit()
    output.setReadOnly(True)

    spin_box.valueChanged.connect(lambda value: output.append(str(value)))

    spin_box_layout.addWidget(spin_box)
    spin_box_layout.addWidget(output)
    spin_box_layout.addStretch()
    spin_box_container.setLayout(spin_box_layout)

    tab_widget.addTab(spin_box_container, "pyqtgraph.SpinBox")

    # LabeledSlider
    labeled_slider_container = QtWidgets.QWidget()
    labeled_slider_layout = QtWidgets.QVBoxLayout()
    labeled_slider_1 = LabeledSlider(title="Slider 1", title_pos=LabeledSlider.TitleLabelPosition.TOP_LEFT)
    labeled_slider_1.setRange(-1_000, 1_000)
    labeled_slider_2 = LabeledSlider(title="Slider 2", title_pos=LabeledSlider.TitleLabelPosition.TOP_CENTER)
    labeled_slider_3 = LabeledSlider(title="Slider 3", title_pos=LabeledSlider.TitleLabelPosition.TOP_RIGHT)
    labeled_slider_3.setRange(0, 1000)
    labeled_slider_3.setSingleStep(100)
    labeled_slider_3.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
    labeled_slider_layout.addWidget(labeled_slider_1)
    labeled_slider_layout.addWidget(labeled_slider_2)
    labeled_slider_layout.addWidget(labeled_slider_3)
    labeled_slider_layout.addStretch()
    labeled_slider_container.setLayout(labeled_slider_layout)

    tab_widget.addTab(labeled_slider_container, "LabeledSlider")

    # ColorPickerButton
    color_picker_container = QtWidgets.QWidget()
    color_picker_layout = QtWidgets.QVBoxLayout()
    color_picker = ColorPickerButton()
    color_picker.setFlat(True)
    color_picker.sig_color_changed.connect(lambda color: print(f"Color 1: {color.name()}"))

    color_picker2 = ColorPickerButton()
    color_picker2.setShowAlphaChannel(True)
    color_picker2.setShowText(True)
    color_picker2.sig_color_changed.connect(
        lambda color: print(f"Color 2: {color.name(QtGui.QColor.NameFormat.HexArgb)}")
    )

    btn_set_invalid_color = QtWidgets.QPushButton("Set Invalid Color")
    btn_set_invalid_color.clicked.connect(lambda: color_picker.set_color(QtGui.QColor("invalid_color")))

    color_picker_layout.addWidget(color_picker, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
    color_picker_layout.addWidget(color_picker2, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
    color_picker_layout.addWidget(btn_set_invalid_color, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
    color_picker_layout.addStretch()
    color_picker_container.setLayout(color_picker_layout)

    tab_widget.addTab(color_picker_container, "ColorPickerButton")

    # Toggle / AnimatedToggle
    toggle_button_container = QtWidgets.QWidget()
    toggle_button_layout = QtWidgets.QVBoxLayout()

    toggle = ToggleSwitch()
    toggle_button = AnimatedToggleSwitch(checked_color="#1abc9c", pulse_checked_color="#4400B0EE")

    toggle_button_layout.addWidget(toggle)
    toggle_button_layout.addWidget(toggle_button)

    toggle_button_layout.addStretch()
    toggle_button_container.setLayout(toggle_button_layout)

    tab_widget.addTab(toggle_button_container, "Toggle / AnimatedToggle")

    # CommandBar
    command_bar_container = QtWidgets.QWidget()
    command_bar_layout = QtWidgets.QVBoxLayout()
    command_bar = CommandBar()
    action1 = QtGui.QAction(QtGui.QIcon("://More"), "Action 1")
    action2 = QtGui.QAction("Action 2")
    action3 = QtGui.QAction("Action 3")
    hidden_action = QtGui.QAction("Hidden Action")
    action1.triggered.connect(lambda: print("Action 1 triggered"))
    action2.triggered.connect(lambda: print("Action 2 triggered"))
    action3.triggered.connect(lambda: print("Action 3 triggered"))
    hidden_action.triggered.connect(lambda: print("Hidden Action triggered"))

    command_bar.addActions([action1, action2])
    command_bar.addSeparator()
    command_bar.addAction(action3)

    command_bar_layout.addWidget(command_bar)
    command_bar_layout.addStretch()
    command_bar_container.setLayout(command_bar_layout)

    tab_widget.addTab(command_bar_container, "CommandBar")

    window.setCentralWidget(tab_widget)
    window.resize(1920, 1080)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
