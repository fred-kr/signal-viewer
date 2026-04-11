from abc import abstractmethod
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, Protocol, Self, TypeVar, overload

import attrs
from attr._make import Factory
from bidict import bidict
from PySide6 import QtCore, QtGui, QtWidgets
from pyside_widgets import SettingCard

if TYPE_CHECKING:
    from .properties import WidgetPropertiesBase

QTYPE_KEY = "__qtype"  # This key's value should be a valid argument to the `type` argument of `QtCore.QSettings.value`

_C = TypeVar("_C", bound=type)


class ConfigInstance(attrs.AttrsInstance, Protocol):
    """
    Protocol for a config class.
    """

    __group_prefix__: ClassVar[str]

    @classmethod
    @abstractmethod
    def from_qsettings(cls) -> Self: ...

    @abstractmethod
    def to_qsettings(self) -> None: ...

    @abstractmethod
    def restore_defaults(self) -> None: ...

    @abstractmethod
    def create_editor(self, **kwargs: Any) -> QtWidgets.QScrollArea: ...


def _get_fields(cls: type[attrs.AttrsInstance]) -> tuple["attrs.Attribute[Any]", ...]:
    """Wrapper around `attrs.fields` with more specific return type."""
    return attrs.fields(cls)


_config_registry: bidict[str, ConfigInstance] = bidict()


def _register(config_class: type[ConfigInstance], overwrite: bool = False) -> None:
    """
    Adds an instance of the provided config class to the `_config_registry` dictionary.

    If an instance of the passed config class already exists as a value in the `_config_registry` dictionary, the
    existing instance is removed. A new instance of the provided config class is created via its `from_qsettings` method
    and added to the `_config_registry` dictionary with the provided name.

    Args:
        config_class (Type[ConfigInstance]): The config class to add to the `_config_registry` dictionary.
        overwrite (bool, optional): Whether to overwrite an existing config class with the same name. Defaults to False.
    """
    name = config_class.__group_prefix__
    config_instance = config_class.from_qsettings()

    if overwrite or name not in _config_registry:
        _config_registry[name] = config_instance
    else:
        raise ValueError(f"A config class with name '{name}' already exists. To replace it, set `overwrite=True`.")

    config_instance.to_qsettings()


def get_config(name: str) -> ConfigInstance:
    """
    Returns the config class registered under the provided name.

    Args:
        name (str): The name under which the config class is registered.

    Returns:
        ConfigInstance: The config class registered under the provided name.
    """
    return _config_registry[name]


def save() -> None:
    """
    Saves the current values of all registered configuration classes to QSettings.
    """
    for config_class in _config_registry.values():
        config_class.to_qsettings()


def reset(exclude: Iterable[str] | None = None) -> None:
    """
    Resets the values of all registered configs to their default values, excluding the provided names.

    If no names are provided, all registered configs are reset to their default values.

    Args:
        exclude (Iterable[str] | None, optional): An iterable of config names to exclude from resetting or `None` to reset all configs.
    """
    if not exclude:
        for config_class in _config_registry.values():
            config_class.restore_defaults()
    else:
        for name, config_class in _config_registry.items():
            if name not in exclude:
                config_class.restore_defaults()


def clean(exclude: Iterable[str] | None = None) -> None:
    """
    Cleans QSettings by removing all settings or only specific registered config groups.

    If no `exclude` list is provided, all settings are cleared. Otherwise, only the settings related to the
    specified config names are kep

    Args:
        exclude (Iterable[str] | None, optional): A list of registered config names to exclude from cleaning or `None` to clean all settings.
    """
    qsettings = QtCore.QSettings()

    if not exclude:
        qsettings.clear()
    else:
        for name in list(qsettings.childGroups()):
            if name not in exclude:
                qsettings.remove(name)

    qsettings.sync()


def update_value(group: str, key: str, value: Any) -> None:
    """
    Updates the value of a specific attribute in a registered config class.

    Args:
        group (str): The name of the config class.
        key (str): The name of the attribute to update.
        value (Any): The new value for the attribute.

    Raises:
        ValueError: If the config class or attribute does not exis
    """
    try:
        config_class = get_config(group)
    except KeyError as e:
        raise ValueError(f"No config class registered with name '{group}'") from e

    if hasattr(config_class, key):
        setattr(config_class, key, value)
    else:
        raise ValueError(f"No attribute '{key}' in config class '{group}'")

    config_class.to_qsettings()


def create_snapshot() -> dict[str, Any]:
    """
    Creates a snapshot of the current state of all registered configuration groups.

    The snapshot contains the current values of all attributes in each configuration group.

    Returns:
        dict[str, Any]: A dictionary where keys are the names of registered configuration groups and values are
        dictionaries representing the current state of each group's attributes.
    """
    return {key: attrs.asdict(inst) for key, inst in _config_registry.items()}


def restore_snapshot(snapshot: dict[str, Any]) -> None:
    """
    Restores the state of all registered configuration groups from a snapsho

    The snapshot should be a dictionary where keys are group names and values are dictionaries representing the
    state of the group's attributes. Each attribute in the snapshot is restored to its value in the provided
    snapsho

    Args:
        snapshot (dict[str, Any]): A dictionary representing the snapshot of the configuration groups' state to
        restore.
    """
    for grp, grp_dict in snapshot.items():
        for key, value in grp_dict.items():
            update_value(grp, key, value)


def create_editor(
    parent: QtWidgets.QWidget | None = None, exclude: Iterable[str] | None = None, window_title: str = "Settings"
) -> QtWidgets.QDialog:
    """
    Creates a QDialog with tabs for each registered config class.

    If no `exclude` list is provided, all registered configs are created. Otherwise, only the configs not related
    to the specified config names are created.

    Args:
        parent (QtWidgets.QWidget | None, optional): The parent widget for the dialog. Defaults to None.
        exclude (Iterable[str] | None, optional): An iterable of config names to exclude from the editor.
        window_title (str, optional): The title of the dialog window. Defaults to "Settings".

    Returns:
        QtWidgets.QDialog: A QDialog with tabs for each registered config class.
    """
    dlg = QtWidgets.QDialog(parent)
    dlg.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
    dlg.setModal(True)
    dlg.setWindowTitle(window_title)

    btn_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
    )
    btn_box.accepted.connect(dlg.accept)
    btn_box.rejected.connect(dlg.reject)

    tab_widget = QtWidgets.QTabWidget()
    for name, inst in _config_registry.items():
        if exclude is None or name not in exclude:
            tab = inst.create_editor()
            tab_widget.addTab(tab, name)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(tab_widget)
    layout.addWidget(btn_box)

    dlg.setLayout(layout)
    dlg.resize(800, 600)

    return dlg


class EditorWidgetInfo[W: QtWidgets.QWidget](NamedTuple):
    label: str
    widget_factory: Callable[..., W]
    sig_value_changed: str
    set_value_method: str
    icon: QtGui.QIcon | None = None
    widget_properties: "WidgetPropertiesBase[W] | None" = None


def _get_setting_path(inst_or_cls: ConfigInstance | type[ConfigInstance], attr: "attrs.Attribute[Any]") -> str:
    """
    Returns the QSettings path for the specified attribute.

    The path is composed of the group prefix (specified via the `group_name` argument of the `@config_define` decorator)
    and the name of the field being accessed. If no `group_name` is provided, the name of the class is used as the group
    prefix.

    Args:
        inst_or_cls (ConfigInstance | type[ConfigInstance]): A `@config_define` decorated class or an instance of that
        class.
        attr (attrs.Attribute): The attribute to get the path for.

    Returns:
        str: The QSettings path for the specified attribute.
    """
    return f"{inst_or_cls.__group_prefix__}/{attr.name}"


def _update_qsettings(inst: ConfigInstance, attr: "attrs.Attribute[Any]", value: Any) -> Any:
    """
    Updates the QSettings with the specified attribute and value.

    Args:
        inst (ConfigInstance):
            The instance of the ConfigInstance-based class containing the attribute to update.
        attr (attrs.Attribute):
            The attribute being updated.
        value (Any):
            The value to set for the given attribute, can be any type supported by QSettings.

    Returns:
        Any: The value that was se
    """
    path = _get_setting_path(inst, attr)
    settings = QtCore.QSettings()
    if path:
        settings.setValue(path, value)
        settings.sync()
    return value


def _get_field_default(field: "attrs.Attribute[Any]") -> Any | None:
    default = field.default
    return default.factory() if isinstance(default, Factory) else default  # type: ignore


def _from_qsettings(cls: type[ConfigInstance]) -> ConfigInstance:
    settings = QtCore.QSettings()
    init_values = {}
    for field in _get_fields(cls):
        path = _get_setting_path(cls, field)
        default = _get_field_default(field)
        qtype: type | None = field.metadata.get(QTYPE_KEY, None)
        if qtype is not None:
            value = settings.value(path, defaultValue=default, type=qtype)
        else:
            value = settings.value(path, defaultValue=default)
        init_values[field.name] = value
    return cls(**init_values)


def _to_qsettings(self: ConfigInstance) -> None:
    settings = QtCore.QSettings()
    for field in _get_fields(self.__class__):
        path = _get_setting_path(self, field)
        value = getattr(self, field.name)
        settings.setValue(path, value)
    settings.sync()


def _restore_defaults(self: ConfigInstance) -> None:
    for field in _get_fields(self.__class__):
        _reset_field(self, field)


def _reset_field(self: ConfigInstance, field: "attrs.Attribute[Any]") -> None:
    default = _get_field_default(field)
    setattr(self, field.name, default)


def _create_editor(self: ConfigInstance, **kwargs: Any) -> QtWidgets.QScrollArea:
    container_widget = QtWidgets.QWidget()

    layout = QtWidgets.QVBoxLayout(container_widget)
    layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

    for field in _get_fields(self.__class__):
        editor_info: "EditorWidgetInfo[QtWidgets.QWidget] | None" = field.metadata.get("editor", None)
        if not editor_info:
            continue

        editor_widget = editor_info.widget_factory(**kwargs)
        editor_widget_properties = editor_info.widget_properties

        value = getattr(self, field.name)

        # Set the initial value of the editor
        getattr(editor_widget, editor_info.set_value_method)(value)

        # Update the config value whenever the editor's valueChanged (varies depending on the widget type) signal is emitted
        getattr(editor_widget, editor_info.sig_value_changed).connect(lambda val, f=field: setattr(self, f.name, val))

        if editor_widget_properties is not None:
            editor_widget_properties.apply_to_widget(editor_widget)

        description = field.metadata.get("description", None)

        default_value = _get_field_default(field)

        card = SettingCard(
            title=editor_info.label,
            default_value=default_value,
            set_value_name=editor_info.set_value_method,
            editor_widget=editor_widget,
            description=description,
            icon=editor_info.icon,
        )
        card.sig_reset_clicked.connect(lambda f=field: _reset_field(self, f))
        layout.addWidget(card)

    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(container_widget)
    return scroll_area


@overload
def config(target_cls: _C) -> _C: ...
@overload
def config(*, group_name: str | None = None, register: bool = True) -> Callable[[_C], _C]: ...
def config(
    target_cls: _C | None = None, *, group_name: str | None = None, register: bool = True
) -> _C | Callable[[_C], _C]:
    def wrap(cls: _C) -> _C:
        cls.__group_prefix__ = group_name or cls.__name__
        cls.from_qsettings = classmethod(_from_qsettings)
        cls.to_qsettings = _to_qsettings
        cls.restore_defaults = _restore_defaults
        cls.create_editor = _create_editor

        attrs_class = attrs.define(cls, eq=False, on_setattr=_update_qsettings)
        if register:
            _register(attrs_class)
        return attrs_class

    return wrap if target_cls is None else wrap(target_cls)


# def rename_config(old_name: str, new_name: str) -> None:
#     """
#     Updates the name under which a config class is registered.

#     Args:
#         old_name (str): The old name of the config class.
#         new_name (str): The new name of the config class.
#     """
#     if old_name not in _config_registry:
#         raise ValueError(f"No config class registered with name '{old_name}'")

#     keys = list(_config_registry.keys())
#     values = list(_config_registry.values())
#     index = keys.index(old_name)
#     keys[index] = new_name
#     _config_registry.clear()
#     _config_registry.update(zip(keys, values, strict=True))
#     _config_registry[new_name].__class__.__group_prefix__ = new_name

#     _config_registry[new_name].to_qsettings()
#     QtCore.QSettings().remove(old_name)
