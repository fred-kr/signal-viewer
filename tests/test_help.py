"""
Tests for the bundled user guide: the manifest points at existing pages and anchors, every internal link of every
page resolves, no page is unreachable, and the help window / controller load the pages.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest
from PySide6 import QtWidgets

from signal_viewer.sv_help import (
    HOME_PAGE,
    MANIFEST_NAME,
    HelpController,
    HelpWindow,
    TocEntry,
    read_manifest,
    split_ref,
)
from signal_viewer.sv_site import DOCDIR

EXTERNAL_SCHEMES = ("http://", "https://", "mailto:")


class _PageScanner(HTMLParser):
    """Collects the `href`s and the anchor targets (`id` of any tag, `name` of `<a>`) of one page."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a":
            if attributes.get("href"):
                self.hrefs.append(attributes["href"] or "")
            if attributes.get("name"):
                self.anchors.add(attributes["name"] or "")
        if attributes.get("id"):
            self.anchors.add(attributes["id"] or "")


def scan(page: Path) -> _PageScanner:
    scanner = _PageScanner()
    scanner.feed(page.read_text(encoding="utf-8"))
    return scanner


def all_pages() -> list[Path]:
    return sorted(DOCDIR.rglob("*.html"))


def toc_refs(entries: tuple[TocEntry, ...]) -> list[str]:
    refs: list[str] = []
    for entry in entries:
        if entry.ref:
            refs.append(entry.ref)
        refs.extend(toc_refs(entry.children))
    return refs


def count_entries(entries: tuple[TocEntry, ...]) -> int:
    return sum(1 + count_entries(e.children) for e in entries)


def assert_ref_exists(ref: str, base: Path) -> None:
    page, anchor = split_ref(ref)
    target = (base / page).resolve() if page else base.resolve()
    assert target.is_file(), f"{ref!r}: {target} does not exist"
    if anchor:
        assert anchor in scan(target).anchors, f"{ref!r}: anchor {anchor!r} not in {target.name}"


def test_manifest_refs_exist() -> None:
    manifest = read_manifest(DOCDIR / MANIFEST_NAME)
    assert manifest.toc, "the manifest has no table of contents"
    assert manifest.keywords, "the manifest has no keywords"
    for ref in toc_refs(manifest.toc) + [ref for _keyword, ref in manifest.keywords]:
        assert_ref_exists(ref, DOCDIR)


def test_manifest_keywords_are_sorted_and_unique() -> None:
    manifest = read_manifest(DOCDIR / MANIFEST_NAME)
    names = [keyword for keyword, _ref in manifest.keywords]
    assert names == sorted(names, key=str.lower)
    assert len(set(names)) == len(names)


@pytest.mark.parametrize("page", all_pages(), ids=lambda p: p.relative_to(DOCDIR).as_posix())
def test_internal_links_resolve(page: Path) -> None:
    scanner = scan(page)
    for href in scanner.hrefs:
        if href.startswith(EXTERNAL_SCHEMES):
            continue
        if href.startswith("#"):
            assert href[1:] in scanner.anchors, f"{page.name}: anchor {href!r} missing"
            continue
        assert_ref_exists(href, page.parent)


def test_every_page_links_the_stylesheet() -> None:
    for page in all_pages():
        text = page.read_text(encoding="utf-8")
        assert "stylesheet.css" in text, f"{page.name} does not link the stylesheet"
        assert text.lstrip().startswith("<!DOCTYPE html>"), f"{page.name} lacks the doctype"


def test_every_page_is_reachable_from_the_manifest() -> None:
    manifest = read_manifest(DOCDIR / MANIFEST_NAME)
    referenced = {split_ref(ref)[0] for ref in toc_refs(manifest.toc)}
    referenced |= {split_ref(ref)[0] for _keyword, ref in manifest.keywords}
    pages = {p.relative_to(DOCDIR).as_posix() for p in all_pages()}
    assert pages <= referenced, f"pages missing from the manifest: {sorted(pages - referenced)}"


def test_help_window_shows_toc_and_pages(qapp: QtWidgets.QApplication) -> None:
    window = HelpWindow(DOCDIR)
    manifest = read_manifest(DOCDIR / MANIFEST_NAME)

    def tree_count(item: QtWidgets.QTreeWidgetItem | None) -> int:
        if item is None:
            return 0
        return 1 + sum(tree_count(item.child(i)) for i in range(item.childCount()))

    shown = sum(tree_count(window.toc.topLevelItem(i)) for i in range(window.toc.topLevelItemCount()))
    assert shown == count_entries(manifest.toc)
    assert window.index_list.count() == len(manifest.keywords)

    assert window.show_page("user_guide/sections.html#lock")
    assert window.current_page() == "user_guide/sections.html#lock"
    current = window.toc.currentItem()
    assert current is not None and current.text(0) == "Working with sections"
    assert window.browser.toPlainText().strip()

    assert not window.show_page("does_not_exist.html")
    assert window.current_page() == "user_guide/sections.html#lock"  # unchanged after the failed call

    window.index_filter.setText("lock")
    visible = [
        window.index_list.item(i).text()
        for i in range(window.index_list.count())
        if not window.index_list.item(i).isHidden()
    ]
    assert visible and all("lock" in text.lower() for text in visible)
    window.close()


def test_help_controller_opens_home_page(qapp: QtWidgets.QApplication) -> None:
    controller = HelpController()
    controller.show_page()
    assert controller.window.current_page() == HOME_PAGE
    controller.show_page("reference/dock_parameters.html#sf-lower-cutoff")
    assert controller.window.current_page() == "reference/dock_parameters.html#sf-lower-cutoff"
    controller.close()
