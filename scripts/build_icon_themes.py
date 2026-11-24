"""Usage: python build_icon_themes.py signal_viewer

Writes icons/dark/*.svg (white copies of the black icons), one index.theme per theme and icon_themes.qrc.
"""

import re
import sys
from pathlib import Path

PACKAGE = Path(sys.argv[1])
ICONS = PACKAGE / "icons"
DARK = ICONS / "dark"
INDEX = (
    "[Icon Theme]\nName={name}\nDirectories=scalable\n\n[scalable]\nSize=24\nMinSize=8\nMaxSize=512\nType=Scalable\n"
)

DARK.mkdir(exist_ok=True)
names = sorted(p.name for p in ICONS.glob("*.svg"))
for name in names:
    svg = (ICONS / name).read_text(encoding="utf-8")
    (DARK / name).write_text(re.sub(r"#(?:000000|212121)\b|currentColor", "#ffffff", svg), encoding="utf-8")

lines = ["<RCC>"]
for theme, folder in (("light", "icons"), ("dark", "icons/dark")):
    (ICONS / f"{theme}.index.theme").write_text(INDEX.format(name=theme), encoding="utf-8")
    lines.append(f'  <qresource prefix="/icon-themes/{theme}">')
    lines.append(f'    <file alias="index.theme">icons/{theme}.index.theme</file>')
    lines += [f'    <file alias="scalable/{n}">{folder}/{n}</file>' for n in names]
    lines.append("  </qresource>")
lines.append("</RCC>")
(PACKAGE / "icon_themes.qrc").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{len(names)} icons per theme")
