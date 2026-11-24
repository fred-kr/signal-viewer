# Notes

An assortment of things that might be useful to know at some point when working with the codebase.

## Adding a theme-aware icon via designer

In Designer, give the icon both a resource file and an XDG theme name equal to the file stem, then regenerate the form. The theme name makes it switch with light and dark. The file is only the fallback that Designer previews and that is used when no theme is set.

### An icon that already exists in `signal_viewer/icons/light/`

1. Select the widget or action and expand the `icon` property in the Property Editor.
2. Set **Normal Off** through **Choose Resource...** to the icon, for example `:/icons/Eraser.svg`.
3. Type the file stem into the **XDG Theme** sub-property, for example `Eraser`. The name is case-sensitive and has no extension.
4. Save, then regenerate the form:

```
.venv/Scripts/pyside6-uic.exe --from-imports --rc-prefix signal_viewer/generated/main_window.ui -o signal_viewer/generated/ui_main_window.py
```

The saved form then contains this, which is the same shape as the ten converted icons:

```xml
<iconset theme="Eraser" resource="../resources.qrc">
 <normaloff>:/icons/Eraser.svg</normaloff>:/icons/Eraser.svg</iconset>
```

Designer keeps showing the black file, because it does not know your themes. The colour switch only shows in the running app. I confirmed the two labels exist in your Designer build, but I did not click through Designer itself.

### A new icon file

Do these before the Designer steps above:

1. Save the SVG to `signal_viewer/icons/light/`. It must be single-colour, drawn in `#000000`, `#212121` or `currentColor`. The script recolours only those three, so any other colour stays unchanged in the dark copy.
2. Add it to [resources.qrc](signal_viewer/resources.qrc) (Designer's Resource Browser does this) and recompile, so the fallback path exists:

```
.venv/Scripts/pyside6-rcc.exe signal_viewer/resources.qrc -o signal_viewer/generated/rc_resources.py
```

3. Rebuild the two themes, so the name resolves at runtime:

```
uv run python scripts/build_icon_themes.py signal_viewer
.venv/Scripts/pyside6-rcc.exe signal_viewer/icon_themes.qrc -o signal_viewer/generated/rc_icon_themes.py
```

### Two ways it goes wrong

- **The icon stays black in dark mode.** Either the XDG Theme name does not match a file stem exactly, or step 3 was skipped. The generated code then finds no theme icon and silently uses the black fallback.
- **Use XDG Theme, not Theme.** The **Theme** dropdown above it selects Qt's built-in platform icons such as `DocumentOpen`, not yours.