from __future__ import annotations

HELIX_QSS = """
QMainWindow {
    background: rgba(15, 23, 42, 210);
}

QWidget {
    color: #E2E8F0;
    font-size: 13px;
}

QFrame#GlassPanel {
    background: rgba(30, 41, 59, 170);
    border: 1px solid rgba(255, 255, 255, 40);
    border-radius: 24px;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #4F46E5);
    border: none;
    border-radius: 24px;
    padding: 8px 16px;
    font-weight: 600;
    color: #FFFFFF;
}

QPushButton:hover {
    background: #4F46E5;
}

QLineEdit {
    background: rgba(15, 23, 42, 180);
    border: 1px solid rgba(148, 163, 184, 120);
    border-radius: 24px;
    padding: 8px 12px;
}

QToolBar {
    background: rgba(17, 24, 39, 180);
    border: 1px solid rgba(255, 255, 255, 25);
    border-radius: 24px;
    spacing: 8px;
    padding: 6px;
}

QToolTip {
    background: rgba(30, 41, 59, 220);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 90);
    border-radius: 12px;
    padding: 12px;
}

QTableView {
    background: rgba(15, 23, 42, 200);
    border: 1px solid rgba(255, 255, 255, 35);
    border-radius: 12px;
    gridline-color: rgba(148, 163, 184, 90);
    alternate-background-color: rgba(30, 41, 59, 180);
}

QHeaderView::section {
    background: rgba(51, 65, 85, 220);
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 25);
    border-bottom: 1px solid rgba(255, 255, 255, 25);
    padding: 6px;
    font-weight: 700;
}

QSplitter::handle {
    background: rgba(203, 213, 225, 120);
    width: 1px;
    height: 1px;
}
"""


def helix_palette() -> dict[str, str]:
    return {
        "surface": "#0F172A",
        "surface_elevated": "#1E293B",
        "accent_indigo": "#6366F1",
        "accent_slate": "#334155",
        "text": "#E2E8F0",
    }
