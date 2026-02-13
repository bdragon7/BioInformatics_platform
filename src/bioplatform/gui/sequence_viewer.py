from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SequenceColors:
    a: str = "#60A5FA"
    c: str = "#34D399"
    g: str = "#F59E0B"
    t: str = "#F472B6"


def sequence_color_map() -> dict[str, str]:
    colors = SequenceColors()
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
    from PySide6.QtWidgets import QPlainTextEdit

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
            font = QFont("Roboto Mono", 10)
            font.setStyleHint(QFont.StyleHint.Monospace)
            self.setFont(font)
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            self.setPlaceholderText("Paste FASTA/sequence data here...")
            self._highlighter = SequenceHighlighter(self.document())

    return SequenceViewer
