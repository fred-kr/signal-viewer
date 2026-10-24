"""
The settings reference page (`doc/reference/settings.html`) is written by hand. These tests keep it in step with the
declarations in `sv_config`: every setting shown in the dialog has a row under its group heading, and every row
belongs to a declared setting.
"""

from __future__ import annotations

import re

import pyside_config as qconfig

import signal_viewer.sv_config  # noqa: F401  (registers the groups)
from signal_viewer.sv_site import DOCDIR

PAGE = DOCDIR / "reference" / "settings.html"


def page_sections() -> dict[str, set[str]]:
    """`{group heading: {setting labels in its table}}`."""
    html = PAGE.read_text(encoding="utf-8")
    sections: dict[str, set[str]] = {}
    for heading, body in re.findall(
        r'<h2 id="[^"]*">(?:<a name="[^"]*"></a>)?([^<]+)</h2>(.*?)(?=<h2 |\Z)', html, re.DOTALL
    ):
        sections[heading.strip()] = set(re.findall(r"<tr><td>([^<]+)</td>", body))
    return sections


def declared_sections() -> dict[str, set[str]]:
    sections: dict[str, set[str]] = {}
    for field in qconfig.iter_fields(include_hidden=False):
        if field.label is not None:
            sections.setdefault(field.group, set()).add(field.label)
    return sections


def test_every_editable_setting_is_documented() -> None:
    documented = page_sections()
    for group, labels in declared_sections().items():
        assert group in documented, f"no section for settings group {group!r} in {PAGE.name}"
        missing = labels - documented[group]
        assert not missing, f"{group}: settings without a row in {PAGE.name}: {sorted(missing)}"


def test_no_stale_rows() -> None:
    declared = declared_sections()
    for group, labels in page_sections().items():
        stale = labels - declared.get(group, set())
        assert not stale, f"{group}: rows in {PAGE.name} without a declared setting: {sorted(stale)}"


def test_hidden_group_is_not_documented_as_a_setting() -> None:
    hidden = {f.group for f in qconfig.iter_fields() if f.hidden}
    assert hidden == {"Internal"}
    assert not hidden & set(page_sections())
