from __future__ import annotations

from dataclasses import dataclass

from .helix_theme import generate_tonal_palette


@dataclass(frozen=True)
class SequenceColors:
    a: str
    c: str
    g: str
    t: str


def _default_sequence_colors() -> SequenceColors:
    tones = generate_tonal_palette("#4F7CFF")
    return SequenceColors(a=tones.t70, c="#34D399", g="#F59E0B", t="#F472B6")


def sequence_color_map() -> dict[str, str]:
    colors = _default_sequence_colors()
    return {
        "A": colors.a,
        "C": colors.c,
        "G": colors.g,
        "T": colors.t,
        "a": colors.a,
        "c": colors.c,
        "g": colors.g,
        "t": colors.t,
    }


def create_sequence_viewer_widget():
    from PySide6.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter
    from PySide6.QtWidgets import QGraphicsDropShadowEffect, QPlainTextEdit

    color_map = sequence_color_map()

    class SequenceHighlighter(QSyntaxHighlighter):
        def __init__(self, document) -> None:  # type: ignore[no-untyped-def]
            super().__init__(document)

        def highlightBlock(self, text: str) -> None:  # type: ignore[override]
            for idx, ch in enumerate(text):
                color = color_map.get(ch)
                if not color:
                    continue
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(color))
                fmt.setFontWeight(QFont.Weight.Bold)
                self.setFormat(idx, 1, fmt)

    class SequenceViewer(QPlainTextEdit):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("SequenceViewer")
            font = QFont("JetBrains Mono", 10)
            font.setStyleHint(QFont.StyleHint.Monospace)
            self.setFont(font)
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            self.setPlaceholderText("Paste FASTA/sequence data here...")
            self._highlighter = SequenceHighlighter(self.document())
            self._bloom = QGraphicsDropShadowEffect(self)
            self._bloom.setBlurRadius(15)
            self._bloom.setOffset(0, 0)
            self._bloom.setColor(QColor(96, 165, 250, 180))
            self.cursorPositionChanged.connect(self._update_bloom)

        def _update_bloom(self) -> None:
            if self.textCursor().hasSelection():
                self.setGraphicsEffect(self._bloom)
            else:
                self.setGraphicsEffect(None)

    return SequenceViewer
