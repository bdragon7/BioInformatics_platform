from __future__ import annotations

from dataclasses import dataclass
import colorsys


@dataclass(frozen=True)
class SchrodingerMD3ColorScheme:
    """Professional dark palette inspired by Schrödinger + Material Design 3."""

    primary_30: str = "#004F5C"
    primary_40: str = "#00697A"
    primary_50: str = "#0891B2"
    primary_60: str = "#06B6D4"
    primary_90: str = "#CFFAFE"

    secondary_50: str = "#7C3AED"
    tertiary_50: str = "#F59E0B"

    neutral_10: str = "#1A1C1E"
    neutral_17: str = "#24262A"
    neutral_20: str = "#2D3035"
    neutral_24: str = "#33373D"
    neutral_30: str = "#44474E"
    neutral_40: str = "#5C5F66"
    neutral_60: str = "#8E9099"
    neutral_70: str = "#A9ABB3"
    neutral_90: str = "#E0E2EB"

    error_50: str = "#DC362E"
    success_50: str = "#10B981"

    glass_overlay_light: str = "rgba(255, 255, 255, 0.08)"
    glass_overlay_medium: str = "rgba(255, 255, 255, 0.12)"
    glass_border: str = "rgba(255, 255, 255, 0.10)"


class MaterialColorGenerator:
    """Small utility for generating tonal variants from a seed color."""

    @staticmethod
    def generate_tonal_palette(seed_color_hex: str) -> dict[int, str]:
        hue, chroma, _ = MaterialColorGenerator.hex_to_hct(seed_color_hex)
        tones = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]
        return {tone: MaterialColorGenerator.hct_to_hex(hue, chroma, tone) for tone in tones}

    @staticmethod
    def hex_to_hct(hex_color: str) -> tuple[float, float, float]:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return h * 360, s * 100, v * 100

    @staticmethod
    def hct_to_hex(hue: float, chroma: float, tone: float) -> str:
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, chroma / 100.0, tone / 100.0)
        return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def build_schrodinger_md3_stylesheet(colors: SchrodingerMD3ColorScheme | None = None) -> str:
    colors = colors or SchrodingerMD3ColorScheme()
    return f"""
QWidget {{ background: {colors.neutral_17}; color: {colors.neutral_90}; font-size: 13px; }}
QMainWindow {{ background: {colors.neutral_10}; }}
QToolBar {{
  background: {colors.neutral_20}; border: none; spacing: 8px; padding: 8px;
  border-bottom: 1px solid {colors.neutral_40};
}}
QStatusBar {{ background: {colors.neutral_20}; color: {colors.neutral_70}; border-top: 1px solid {colors.neutral_40}; }}
QMenuBar, QMenu {{
  background: {colors.neutral_20}; color: {colors.neutral_90};
  border: 1px solid {colors.neutral_40};
}}
QMenu::item:selected {{ background: {colors.primary_30}; color: {colors.primary_90}; }}
QPushButton {{
  background: {colors.primary_50}; color: {colors.neutral_10};
  border: none; border-radius: 18px; padding: 8px 18px; font-weight: 600;
}}
QPushButton:hover {{ background: {colors.primary_60}; }}
QPushButton:pressed {{ background: {colors.primary_40}; }}
QLineEdit, QComboBox, QPlainTextEdit {{
  background: {colors.neutral_24}; border: 1px solid {colors.neutral_40};
  border-radius: 8px; padding: 7px; color: {colors.neutral_90};
}}
QListWidget, QTableView {{
  background: {colors.neutral_24}; border: 1px solid {colors.neutral_40}; border-radius: 10px;
  alternate-background-color: {colors.neutral_20}; gridline-color: {colors.neutral_40};
}}
QHeaderView::section {{
  background: {colors.neutral_20}; color: {colors.neutral_90};
  border: 0; border-right: 1px solid {colors.neutral_40}; border-bottom: 1px solid {colors.neutral_40};
  padding: 7px; font-weight: 700;
}}
QSplitter::handle {{ background: {colors.neutral_40}; }}
QSplitter::handle:hover {{ background: {colors.primary_50}; }}
QFrame#Card {{
  background: {colors.neutral_24};
  border: 1px solid {colors.glass_border};
  border-radius: 12px;
}}
QLabel#AppHeading {{ font-size: 16px; font-weight: 700; color: {colors.primary_90}; }}
QLabel#SectionTitle {{ font-size: 14px; font-weight: 700; color: {colors.neutral_90}; }}
QLabel#StatusSuccess {{ color: {colors.success_50}; font-weight: 600; }}
QLabel#StatusError {{ color: {colors.error_50}; font-weight: 600; }}
QToolTip {{
  background: {colors.neutral_90}; color: {colors.neutral_10}; border: none; border-radius: 6px; padding: 6px 10px;
}}
"""
