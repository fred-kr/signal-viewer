"""
ResizableMessageBox — a QDialog-based drop-in replacement for QMessageBox
that supports resizing, selectable text, the same standard button API,
and an optional collapsible detail/traceback section.
"""

import sys
import traceback

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ResizableMessageBox(QDialog):
    class Icon:
        NoIcon = 0
        Information = 1
        Warning = 2
        Critical = 3
        Question = 4

    _DETAIL_BTN_SHOW = "Show Details"
    _DETAIL_BTN_HIDE = "Hide Details"

    def __init__(
        self,
        icon: int = 0,
        title: str = "",
        text: str = "",
        buttons=QDialogButtonBox.StandardButton.Ok,
        default_button=QDialogButtonBox.StandardButton.Ok,
        parent=None,
        min_size: tuple[int, int] = (480, 180),
        selectable_text: bool = True,
        detail_text: str = "",
    ):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setSizeGripEnabled(True)
        self.setMinimumSize(*min_size)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # ── Root layout ───────────────────────────────────────────────────────
        self._root = QVBoxLayout(self)
        self._root.setSpacing(10)
        self._root.setContentsMargins(16, 16, 16, 12)

        # ── Top row: icon + message ───────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        top.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._text_label = QLabel(text)
        self._text_label.setWordWrap(True)
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if selectable_text:
            self._text_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
            )

        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(self._text_label)
        il.addStretch()

        scroll.setWidget(inner)
        top.addWidget(scroll, 1)
        self._root.addLayout(top, 0)

        # ── Detail section ────────────────────────────────────────────────────
        self._detail_widget = self._build_detail_widget()
        self._detail_widget.setVisible(False)
        self._root.addWidget(self._detail_widget, 1)  # stretch=1 so it expands

        # ── Button row ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        self._detail_toggle = QPushButton(self._DETAIL_BTN_SHOW)
        self._detail_toggle.setIcon(QIcon("://icons/More"))
        self._detail_toggle.setFlat(True)
        self._detail_toggle.setVisible(False)
        self._detail_toggle.clicked.connect(self._toggle_detail)
        btn_row.addWidget(self._detail_toggle, 0)

        btn_row.addStretch(1)

        self._button_box = QDialogButtonBox(buttons)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        if default_button:
            btn = self._button_box.button(default_button)
            if btn:
                btn.setDefault(True)
        btn_row.addWidget(self._button_box, 0)

        self._root.addLayout(btn_row, 0)

        # ── Deferred init ─────────────────────────────────────────────────────
        self.set_icon(icon)
        if detail_text:
            self.set_detail_text(detail_text)

    # ── Detail widget builder ─────────────────────────────────────────────────

    def _build_detail_widget(self) -> QPlainTextEdit:
        ed = QPlainTextEdit()
        ed.setReadOnly(True)
        ed.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        ed.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ed.setMinimumHeight(120)

        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(9)
        ed.setFont(mono)

        # Subtle inset styling — inherits palette so it works in dark mode too
        ed.setStyleSheet(
            "QPlainTextEdit {"
            "  border: 1px solid palette(mid);"
            "  border-radius: 4px;"
            "  background: palette(base);"
            "  padding: 6px;"
            "}"
        )
        return ed

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle_detail(self) -> None:
        visible = not self._detail_widget.isVisible()
        self._detail_widget.setVisible(visible)
        self._detail_toggle.setText(self._DETAIL_BTN_HIDE if visible else self._DETAIL_BTN_SHOW)
        # Adjust the size after toggling
        cur = self.size()
        extra = max(200, self._detail_widget.minimumHeight() + 24)
        if not visible:
            extra = -extra
        self.resize(cur.width(), cur.height() + extra)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_icon(self, icon: int) -> None:
        from PySide6.QtWidgets import QStyle

        sp_map = {
            self.Icon.Information: QStyle.StandardPixmap.SP_MessageBoxInformation,
            self.Icon.Warning: QStyle.StandardPixmap.SP_MessageBoxWarning,
            self.Icon.Critical: QStyle.StandardPixmap.SP_MessageBoxCritical,
            self.Icon.Question: QStyle.StandardPixmap.SP_MessageBoxQuestion,
        }
        sp = sp_map.get(icon)
        if sp is not None:
            px = self.style().standardPixmap(sp, None, self)
            self._icon_label.setPixmap(
                px.scaled(
                    QSize(48, 48),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self._icon_label.setVisible(True)
        else:
            self._icon_label.setVisible(False)

    def set_text(self, text: str) -> None:
        self._text_label.setText(text)

    def text(self) -> str:
        return self._text_label.text()

    def set_detail_text(self, text: str) -> None:
        """Set raw detail text (stacktrace, log dump, etc.)."""
        self._detail_widget.setPlainText(text)
        self._detail_toggle.setVisible(bool(text))

    def set_exception(self, exc: BaseException) -> None:
        """Format and display an exception including its full traceback."""
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.set_detail_text(tb)

    def detail_text(self) -> str:
        return self._detail_widget.toPlainText()

    def clicked_button(self):
        return getattr(self, "_clicked", None)

    def button_box(self) -> QDialogButtonBox:
        return self._button_box

    # ── Static convenience methods ────────────────────────────────────────────

    @staticmethod
    def information(parent, title: str, text: str, buttons=QDialogButtonBox.StandardButton.Ok, detail: str = "") -> int:
        dlg = ResizableMessageBox(
            ResizableMessageBox.Icon.Information, title, text, buttons, parent=parent, detail_text=detail
        )
        return dlg.exec()

    @staticmethod
    def warning(
        parent,
        title: str,
        text: str,
        buttons=QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        detail: str = "",
    ) -> int:
        dlg = ResizableMessageBox(
            ResizableMessageBox.Icon.Warning, title, text, buttons, parent=parent, detail_text=detail
        )
        return dlg.exec()

    @staticmethod
    def critical(parent, title: str, text: str, buttons=QDialogButtonBox.StandardButton.Ok, detail: str = "") -> int:
        dlg = ResizableMessageBox(
            ResizableMessageBox.Icon.Critical, title, text, buttons, parent=parent, detail_text=detail
        )
        return dlg.exec()

    @staticmethod
    def question(
        parent,
        title: str,
        text: str,
        buttons=QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No,
        detail: str = "",
    ) -> int:
        dlg = ResizableMessageBox(
            ResizableMessageBox.Icon.Question, title, text, buttons, parent=parent, detail_text=detail
        )
        return dlg.exec()

    @staticmethod
    def from_exception(
        parent, title: str, text: str, exc: BaseException, buttons=QDialogButtonBox.StandardButton.Ok
    ) -> int:
        """Convenience: create a Critical dialog pre-loaded with a formatted exception."""
        dlg = ResizableMessageBox(ResizableMessageBox.Icon.Critical, title, text, buttons, parent=parent)
        dlg.set_exception(exc)
        return dlg.exec()


# ── Demo ──────────────────────────────────────────────────────────────────────


def _make_fake_exception() -> ZeroDivisionError:
    """Produce a real exception with a genuine traceback."""

    def inner():
        result = 1 / 0

    def outer():
        inner()

    try:
        outer()
        raise ValueError
    except ZeroDivisionError as e:
        return e


if __name__ == "__main__":
    app = QApplication(sys.argv)

    exc = _make_fake_exception()

    result = ResizableMessageBox.from_exception(
        None,
        "Unhandled Exception",
        "An unexpected error occurred while processing the request.\nThe operation has been aborted.",
        exc,
    )

    print("Dialog result:", result)
    sys.exit(0)
