from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    stylesheet: str


LIGHT = Theme(
    name="light",
    stylesheet="""
QWidget { background: #f7f9fc; color: #1f2937; font-size: 13px; }
QMainWindow { background: #f3f4f6; }
QPushButton { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 6px 12px; }
QPushButton:hover { background: #1d4ed8; }
QLineEdit, QComboBox, QPlainTextEdit { background: white; border: 1px solid #d1d5db; border-radius: 6px; padding: 4px; }
QTableView { background: white; alternate-background-color: #f9fafb; gridline-color: #e5e7eb; }
QHeaderView::section { background: #eef2ff; border: 0; border-right: 1px solid #dbeafe; border-bottom: 1px solid #dbeafe; padding: 6px; font-weight: 600; }
QDockWidget::title { background: #e5e7eb; padding: 6px; }
""",
)

DARK = Theme(
    name="dark",
    stylesheet="""
QWidget { background: #111827; color: #e5e7eb; font-size: 13px; }
QMainWindow { background: #0f172a; }
QPushButton { background: #0ea5e9; color: white; border: none; border-radius: 6px; padding: 6px 12px; }
QPushButton:hover { background: #0284c7; }
QLineEdit, QComboBox, QPlainTextEdit { background: #1f2937; border: 1px solid #334155; border-radius: 6px; padding: 4px; color: #e5e7eb; }
QTableView { background: #1f2937; alternate-background-color: #111827; gridline-color: #334155; }
QHeaderView::section { background: #0f172a; color: #e5e7eb; border: 0; border-right: 1px solid #334155; border-bottom: 1px solid #334155; padding: 6px; font-weight: 600; }
QDockWidget::title { background: #1e293b; padding: 6px; }
""",
)

HIGH_CONTRAST = Theme(
    name="high_contrast",
    stylesheet="""
QWidget { background: #000000; color: #ffffff; font-size: 14px; }
QPushButton { background: #ffff00; color: #000; border: 2px solid #fff; border-radius: 4px; padding: 6px 10px; }
QLineEdit, QComboBox, QPlainTextEdit, QTableView { background: #000; color: #fff; border: 2px solid #fff; }
QHeaderView::section { background: #000; color: #fff; border: 1px solid #fff; padding: 6px; font-weight: 700; }
""",
)

THEMES = {t.name: t for t in [LIGHT, DARK, HIGH_CONTRAST]}
