from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TonalPalette:
    t0: str
    t10: str
    t20: str
    t30: str
    t40: str
    t50: str
    t60: str
    t70: str
    t80: str
    t90: str
    t95: str
    t99: str
    t100: str


def _fallback_tonal_palette() -> TonalPalette:
    return TonalPalette(
        t0="#000000",
        t10="#0F172A",
        t20="#1E293B",
        t30="#334155",
        t40="#475569",
        t50="#64748B",
        t60="#94A3B8",
        t70="#CBD5E1",
        t80="#E2E8F0",
        t90="#F1F5F9",
        t95="#F8FAFC",
        t99="#FCFDFF",
        t100="#FFFFFF",
    )


def _material_you_tonal_palette(seed_hex: str) -> TonalPalette | None:
    """Best-effort Material You palette generation using materialyoucolor.

    Falls back silently if library/API isn't available.
    """
    try:
        from materialyoucolor.hct.hct import Hct  # type: ignore
        from materialyoucolor.utils.color_utils import argb_from_hex, hex_from_argb  # type: ignore

        base = Hct.from_int(argb_from_hex(seed_hex))

        def tone(v: int) -> str:
            h = Hct.from_hct(base.hue, max(16, base.chroma), v)
            return hex_from_argb(h.to_int())

        return TonalPalette(
            t0=tone(0),
            t10=tone(10),
            t20=tone(20),
            t30=tone(30),
            t40=tone(40),
            t50=tone(50),
            t60=tone(60),
            t70=tone(70),
            t80=tone(80),
            t90=tone(90),
            t95=tone(95),
            t99=tone(99),
            t100=tone(100),
        )
    except Exception:
        return None


def generate_tonal_palette(seed_hex: str = "#4F7CFF") -> TonalPalette:
    return _material_you_tonal_palette(seed_hex) or _fallback_tonal_palette()


def build_helix_qss(dark_mode: bool, seed_hex: str = "#4F7CFF") -> str:
    tones = generate_tonal_palette(seed_hex)

    surface = tones.t12 if hasattr(tones, "t12") else (tones.t10 if dark_mode else tones.t90)
    elevated = tones.t20 if dark_mode else tones.t95
    text = tones.t90 if dark_mode else tones.t10

    return f"""
QMainWindow {{
    background: rgba(15, 23, 42, 210);
}}

QWidget {{
    color: {text};
    font-size: 13px;
}}

QFrame#DesktopSurface {{
    background: {surface};
    border-radius: 24px;
}}

QFrame#WorkbenchSurface {{
    background: rgba(255, 255, 255, 102);
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 40);
}}

QFrame#ModalGlass {{
    background: rgba(255, 255, 255, 178);
    border-radius: 24px;
    border-top: 1px solid rgba(255, 255, 255, 190);
    border-left: 1px solid rgba(255, 255, 255, 160);
}}

QFrame#GlassPanel {{
    background: rgba(30, 41, 59, 170);
    border: 1px solid rgba(255, 255, 255, 40);
    border-radius: 24px;
}}

QPushButton {{
    background: {tones.t40};
    border: none;
    border-radius: 24px;
    padding: 8px 16px;
    font-weight: 600;
    color: {tones.t100};
}}

QPushButton:hover {{
    background: rgba(255,255,255,0.08);
}}

QPushButton:pressed {{
    background: rgba(255,255,255,0.12);
}}

QLineEdit {{
    background: rgba(15, 23, 42, 180);
    border: 1px solid rgba(148, 163, 184, 120);
    border-radius: 24px;
    padding: 8px 12px;
}}

QToolBar {{
    background: rgba(17, 24, 39, 180);
    border: 1px solid rgba(255, 255, 255, 25);
    border-radius: 24px;
    spacing: 8px;
    padding: 6px;
}}

QToolTip {{
    background: rgba(30, 41, 59, 220);
    color: {tones.t100};
    border: 1px solid rgba(255, 255, 255, 90);
    border-radius: 12px;
    padding: 12px;
}}

QTableView {{
    background: {elevated};
    border: 1px solid rgba(255, 255, 255, 35);
    border-radius: 12px;
    gridline-color: rgba(148, 163, 184, 90);
    alternate-background-color: rgba(30, 41, 59, 180);
}}

QHeaderView::section {{
    background: rgba(51, 65, 85, 220);
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 25);
    border-bottom: 1px solid rgba(255, 255, 255, 25);
    padding: 6px;
    font-weight: 700;
}}

QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    border: none;
    margin: 2px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: rgba(148,163,184,0.55);
    border-radius: 10px;
    min-height: 24px;
    min-width: 24px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}

QSplitter::handle {{
    background: rgba(203, 213, 225, 120);
    width: 1px;
    height: 1px;
}}

QPlainTextEdit#SequenceViewer {{
    line-height: 150%;
    border-radius: 12px;
}}
"""


HELIX_QSS = build_helix_qss(dark_mode=True)


def helix_palette(seed_hex: str = "#4F7CFF") -> dict[str, str]:
    tones = generate_tonal_palette(seed_hex)
    return {
        "surface": tones.t10,
        "surface_elevated": tones.t20,
        "accent_indigo": tones.t40,
        "accent_slate": tones.t30,
        "text": tones.t90,
    }
