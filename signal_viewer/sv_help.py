"""
The in-app user guide.

The guide is a set of plain HTML pages in `DOCDIR` (`signal_viewer/doc/`). `HelpWindow` shows them in a
`QTextBrowser` with a table of contents and a keyword index, both read from the manifest `signalviewer.qhp` (a Qt
Help project file kept only as the declarative list of pages and keywords; nothing compiles it). The same pages open
in any web browser, which the window offers as "Open in browser".

`HelpController` is the application's single entry point: `show_page` opens (and raises) the window at a page, and
an application-wide event filter turns clicks on `help:` links inside What's This texts
(`help_texts.HELP_URL_SCHEME`) into `show_page` calls.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import cast

import attrs
from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets

from signal_viewer.help_texts import HELP_URL_SCHEME
from signal_viewer.sv_config import Config
from signal_viewer.sv_site import DOCDIR

MANIFEST_NAME = "signalviewer.qhp"
HOME_PAGE = "index.html"
STYLESHEET_NAME = "stylesheet.css"


@attrs.frozen
class TocEntry:
    """One `<section>` of the manifest's table of contents."""

    title: str
    ref: str
    """Page path relative to `DOCDIR`, possibly with `#anchor`; empty for a heading without a page."""
    children: tuple[TocEntry, ...] = ()


@attrs.frozen
class Manifest:
    """The parts of `signalviewer.qhp` the help window uses."""

    toc: tuple[TocEntry, ...]
    keywords: tuple[tuple[str, str], ...]
    """`(keyword, ref)` pairs sorted by keyword, case-insensitively."""


def read_manifest(path: Path) -> Manifest:
    """
    Parses the table of contents and the keyword index out of a Qt Help project file.

    Only `filterSection/toc` and `filterSection/keywords` are read; the `files` list is irrelevant because the pages
    are served straight from disk.
    """
    root = ET.parse(path).getroot()

    def walk(element: ET.Element) -> tuple[TocEntry, ...]:
        return tuple(
            TocEntry(title=s.get("title", ""), ref=s.get("ref", ""), children=walk(s))
            for s in element.findall("section")
        )

    toc_element = root.find("./filterSection/toc")
    keywords_element = root.find("./filterSection/keywords")
    toc = walk(toc_element) if toc_element is not None else ()
    keywords: list[tuple[str, str]] = []
    if keywords_element is not None:
        keywords = [(k.get("name", ""), k.get("ref", "")) for k in keywords_element.findall("keyword")]
    keywords.sort(key=lambda pair: pair[0].lower())
    return Manifest(toc=toc, keywords=tuple(keywords))


def split_ref(ref: str) -> tuple[str, str]:
    """Splits `"page.html#anchor"` into `("page.html", "anchor")`; the anchor is empty when there is none."""
    page, _, anchor = ref.partition("#")
    return page, anchor


class HelpWindow(QtWidgets.QMainWindow):
    """
    Browser window for the bundled user guide: contents and index on the left, the page on the right.

    Navigation inside the guide stays in the window (`QTextBrowser` follows relative links itself); `http(s)` links
    open in the system browser. The window remembers its geometry in `Config.internal.help_window_geometry`.
    """

    def __init__(self, doc_dir: Path = DOCDIR, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HelpWindow")
        self.setWindowTitle("SignalViewer User Guide")
        self.setWindowIcon(QtGui.QIcon("://icons/BookQuestionMark.svg"))
        self._doc_dir = doc_dir
        self._items_by_page: dict[str, QtWidgets.QTreeWidgetItem] = {}

        self.browser = QtWidgets.QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setSearchPaths([str(doc_dir)])
        stylesheet = doc_dir / STYLESHEET_NAME
        if stylesheet.is_file():
            self.browser.document().setDefaultStyleSheet(stylesheet.read_text(encoding="utf-8"))
        self.browser.sourceChanged.connect(self._on_source_changed)

        self.toc = QtWidgets.QTreeWidget()
        self.toc.setHeaderHidden(True)
        self.toc.currentItemChanged.connect(self._on_toc_item_changed)

        self.index_filter = QtWidgets.QLineEdit()
        self.index_filter.setPlaceholderText("Filter keywords")
        self.index_filter.setClearButtonEnabled(True)
        self.index_filter.textChanged.connect(self._filter_index)
        self.index_list = QtWidgets.QListWidget()
        self.index_list.itemActivated.connect(self._on_index_item_activated)
        self.index_list.itemClicked.connect(self._on_index_item_activated)
        index_widget = QtWidgets.QWidget()
        index_layout = QtWidgets.QVBoxLayout(index_widget)
        index_layout.setContentsMargins(0, 0, 0, 0)
        index_layout.addWidget(self.index_filter)
        index_layout.addWidget(self.index_list)

        side = QtWidgets.QTabWidget()
        side.addTab(self.toc, "Contents")
        side.addTab(index_widget, "Index")

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.addWidget(side)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 760])
        self.setCentralWidget(splitter)

        self._setup_toolbar()
        self.manifest = self._load_manifest()
        self._populate_toc()
        self._populate_index()

        self.resize(1040, 720)
        self.restoreGeometry(Config.internal.help_window_geometry)

    # --- Setup -------------------------------------------------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        toolbar = QtWidgets.QToolBar("help_toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        theme = QtGui.QIcon.ThemeIcon
        self.action_back = QtGui.QAction(QtGui.QIcon.fromTheme(theme.GoPrevious), "Back", self)
        self.action_back.setShortcut(QtGui.QKeySequence.StandardKey.Back)
        self.action_back.setEnabled(False)
        self.action_back.triggered.connect(self.browser.backward)
        self.browser.backwardAvailable.connect(self.action_back.setEnabled)

        self.action_forward = QtGui.QAction(QtGui.QIcon.fromTheme(theme.GoNext), "Forward", self)
        self.action_forward.setShortcut(QtGui.QKeySequence.StandardKey.Forward)
        self.action_forward.setEnabled(False)
        self.action_forward.triggered.connect(self.browser.forward)
        self.browser.forwardAvailable.connect(self.action_forward.setEnabled)

        self.action_home = QtGui.QAction(QtGui.QIcon.fromTheme(theme.GoHome), "Home", self)
        self.action_home.setToolTip("Open the start page of the user guide")
        self.action_home.triggered.connect(lambda: self.show_page(HOME_PAGE))

        self.action_open_in_browser = QtGui.QAction(QtGui.QIcon("://icons/ArrowExportLtr"), "Open in browser", self)
        self.action_open_in_browser.setToolTip("Open the current page in the system web browser")
        self.action_open_in_browser.triggered.connect(self.open_current_in_browser)

        toolbar.addActions([self.action_back, self.action_forward, self.action_home])
        toolbar.addSeparator()
        toolbar.addAction(self.action_open_in_browser)

    def _load_manifest(self) -> Manifest:
        path = self._doc_dir / MANIFEST_NAME
        try:
            return read_manifest(path)
        except (OSError, ET.ParseError) as exc:
            logger.error(f"Cannot read the help manifest {path}: {exc}")
            return Manifest(toc=(), keywords=())

    def _populate_toc(self) -> None:
        self.toc.clear()
        self._items_by_page.clear()

        def add(entries: tuple[TocEntry, ...], parent: QtWidgets.QTreeWidgetItem | None) -> None:
            for entry in entries:
                item = QtWidgets.QTreeWidgetItem([entry.title])
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry.ref)
                if parent is None:
                    self.toc.addTopLevelItem(item)
                else:
                    parent.addChild(item)
                page, _anchor = split_ref(entry.ref)
                # The first entry naming a page represents it in the tree; anchored sub-entries do not replace it.
                if page and page not in self._items_by_page:
                    self._items_by_page[page] = item
                add(entry.children, item)

        with QtCore.QSignalBlocker(self.toc):
            add(self.manifest.toc, None)
            self.toc.expandAll()

    def _populate_index(self) -> None:
        self.index_list.clear()
        for keyword, ref in self.manifest.keywords:
            item = QtWidgets.QListWidgetItem(keyword)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, ref)
            item.setToolTip(ref)
            self.index_list.addItem(item)

    # --- Navigation --------------------------------------------------------------------------------------------------

    def show_page(self, ref: str) -> bool:
        """
        Loads `ref` (a page path relative to the doc folder, optionally with `#anchor`) into the browser.

        Returns `False` and logs an error when the page does not exist; the window then keeps its current page.
        """
        page, anchor = split_ref(ref)
        target = self._doc_dir / page
        if not target.is_file():
            logger.error(f"Help page not found: {target}")
            return False
        url = QtCore.QUrl.fromLocalFile(str(target))
        if anchor:
            url.setFragment(anchor)
        if url == self.browser.source():
            # Same page again: `setSource` would not scroll, so jump to the anchor (or the top) by hand.
            if anchor:
                self.browser.scrollToAnchor(anchor)
            else:
                self.browser.verticalScrollBar().setValue(0)
        else:
            self.browser.setSource(url)
        return True

    def current_page(self) -> str:
        """The shown page relative to the doc folder, with its anchor if any; empty before the first page loads."""
        return self._page_of(self.browser.source())

    def _page_of(self, url: QtCore.QUrl) -> str:
        """`url` as a page reference relative to the doc folder, or an empty string for anything outside it."""
        if not url.isLocalFile():
            return ""
        try:
            rel = Path(url.toLocalFile()).resolve().relative_to(self._doc_dir.resolve()).as_posix()
        except ValueError:
            return ""
        return f"{rel}#{url.fragment()}" if url.hasFragment() else rel

    @QtCore.Slot()
    def open_current_in_browser(self) -> None:
        """Opens the shown page in the system web browser (or the start page when nothing is shown yet)."""
        page, _anchor = split_ref(self.current_page() or HOME_PAGE)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self._doc_dir / page)))

    @QtCore.Slot(QtCore.QUrl)
    def _on_source_changed(self, url: QtCore.QUrl) -> None:
        # `self.browser.source()` still holds the previous URL while this signal is delivered; use the argument.
        page, _anchor = split_ref(self._page_of(url))
        item = self._items_by_page.get(page)
        with QtCore.QSignalBlocker(self.toc):
            if item is None:
                self.toc.setCurrentIndex(QtCore.QModelIndex())
            else:
                self.toc.setCurrentItem(item)

    @QtCore.Slot(QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidgetItem)
    def _on_toc_item_changed(
        self, current: QtWidgets.QTreeWidgetItem | None, previous: QtWidgets.QTreeWidgetItem | None
    ) -> None:
        if current is None:
            return
        ref = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if ref:
            self.show_page(str(ref))

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _on_index_item_activated(self, item: QtWidgets.QListWidgetItem) -> None:
        ref = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if ref:
            self.show_page(str(ref))

    @QtCore.Slot(str)
    def _filter_index(self, text: str) -> None:
        needle = text.strip().lower()
        for row in range(self.index_list.count()):
            item = self.index_list.item(row)
            item.setHidden(bool(needle) and needle not in item.text().lower())

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        Config.internal.help_window_geometry = self.saveGeometry()
        super().closeEvent(event)


class HelpController(QtCore.QObject):
    """
    Opens the user guide at a page and resolves `help:` links.

    The window is created on first use. The controller installs itself as an event filter on the application so
    that a click on a `help:...` link in any What's This text (see `help_texts.whats_this_html`) opens that page; Qt
    delivers those clicks as `QEvent.Type.WhatsThisClicked` to the widget showing the text, which is why an
    application-wide filter is needed.
    """

    def __init__(self, parent: QtCore.QObject | None = None, doc_dir: Path = DOCDIR) -> None:
        super().__init__(parent)
        self._doc_dir = doc_dir
        self._window: HelpWindow | None = None
        app = QtCore.QCoreApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    @property
    def window(self) -> HelpWindow:
        """The help window, created on first access."""
        if self._window is None:
            self._window = HelpWindow(self._doc_dir)
        return self._window

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.WhatsThisClicked:
            href = cast(QtGui.QWhatsThisClickedEvent, event).href()
            if href.startswith(HELP_URL_SCHEME):
                QtWidgets.QWhatsThis.hideText()
                self.show_page(href[len(HELP_URL_SCHEME) :])
                return True
        return super().eventFilter(watched, event)

    @QtCore.Slot()
    @QtCore.Slot(str)
    def show_page(self, ref: str = HOME_PAGE) -> None:
        """Shows the help window at `ref` (page path relative to the doc folder, optionally with `#anchor`)."""
        window = self.window
        if window.show_page(ref) or window.current_page():
            window.show()
            window.raise_()
            window.activateWindow()

    def open_in_browser(self, ref: str = HOME_PAGE) -> None:
        """Opens `ref` in the system web browser instead of the help window."""
        page, _anchor = split_ref(ref)
        target = self._doc_dir / page
        if not target.is_file():
            logger.error(f"Help page not found: {target}")
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(target)))

    def close(self) -> None:
        """Closes the help window if it is open. Called when the main window closes."""
        if self._window is not None:
            self._window.close()
