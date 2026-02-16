from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    stylesheet: str


LIGHT = Theme(
    name="light",
    stylesheet="""
QWidget { background: #f6f2e8; color: #2f2a23; font-size: 13px; }
QMainWindow { background: #efe7d8; }
QToolBar { background: #fdf8ee; border: none; spacing: 8px; padding: 6px; }
QStatusBar { background: #fdf8ee; border-top: 1px solid #ded4c2; }
QPushButton {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7a8de8, stop:1 #667de0);
  color: white; border: none; border-radius: 8px; padding: 7px 14px; font-weight: 600;
}
QPushButton:hover { background: #5e75d8; }
QLineEdit, QComboBox, QPlainTextEdit {
  background: #fffaf1; border: 1px solid #d8cdb8; border-radius: 8px; padding: 6px;
}
QListWidget, QTableView {
  background: #fffaf1; border: 1px solid #d8cdb8; border-radius: 10px;
  alternate-background-color: #faf3e5; gridline-color: #e1d7c6;
}
QHeaderView::section {
  background: #efe6d5; border: 0; border-right: 1px solid #ddcfb8; border-bottom: 1px solid #ddcfb8;
  padding: 7px; font-weight: 700;
}
QDockWidget::title { background: #eadfc9; padding: 6px; font-weight: 700; }
QFrame#Card { background: #fffaf1; border: 1px solid #d9ceb9; border-radius: 12px; }
QLabel#AppHeading { font-size: 16px; font-weight: 700; color: #3a3128; }
QLabel#SectionTitle { font-size: 14px; font-weight: 700; color: #3a3128; }
""",
)

DARK = Theme(
    name="dark",
    stylesheet="""
QWidget { background: #0f172a; color: #e2e8f0; font-size: 13px; }
QMainWindow { background: #0b1220; }
QToolBar { background: #111827; border: none; spacing: 8px; padding: 6px; }
QStatusBar { background: #111827; border-top: 1px solid #1f2937; color: #cbd5e1; }
QPushButton {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #0284c7);
  color: white; border: none; border-radius: 8px; padding: 7px 14px; font-weight: 600;
}
QPushButton:hover { background: #0284c7; }
QLineEdit, QComboBox, QPlainTextEdit {
  background: #111827; border: 1px solid #334155; border-radius: 8px; padding: 6px; color: #e2e8f0;
}
QListWidget, QTableView {
  background: #111827; border: 1px solid #233042; border-radius: 10px;
  alternate-background-color: #0f172a; gridline-color: #334155;
}
QHeaderView::section {
  background: #162032; color: #e2e8f0; border: 0; border-right: 1px solid #334155; border-bottom: 1px solid #334155;
  padding: 7px; font-weight: 700;
}
QDockWidget::title { background: #111827; padding: 6px; font-weight: 700; }
QFrame#Card { background: #111827; border: 1px solid #233042; border-radius: 12px; }
QLabel#AppHeading { font-size: 16px; font-weight: 700; color: #e2e8f0; }
QLabel#SectionTitle { font-size: 14px; font-weight: 700; color: #f1f5f9; }
""",
)

HIGH_CONTRAST = Theme(
    name="high_contrast",
    stylesheet="""
QWidget { background: #000000; color: #ffffff; font-size: 14px; }
QPushButton { background: #ffff00; color: #000; border: 2px solid #fff; border-radius: 4px; padding: 6px 10px; }
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTableView { background: #000; color: #fff; border: 2px solid #fff; }
QHeaderView::section { background: #000; color: #fff; border: 1px solid #fff; padding: 6px; font-weight: 700; }
QFrame#Card { background: #000; border: 2px solid #fff; border-radius: 4px; }
QLabel#AppHeading, QLabel#SectionTitle { color: #fff; font-weight: 700; }
""",
)

THEMES = {t.name: t for t in [LIGHT, DARK, HIGH_CONTRAST]}
