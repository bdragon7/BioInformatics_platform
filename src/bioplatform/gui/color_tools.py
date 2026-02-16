from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PaletteStore:
    recent: list[str] = field(default_factory=list)
    favorites: list[str] = field(default_factory=lambda: ["#0072B2", "#009E73", "#D55E00", "#CC79A7"])

    def add_recent(self, color_hex: str) -> None:
        clean = color_hex.upper()
        if clean in self.recent:
            self.recent.remove(clean)
        self.recent.insert(0, clean)
        self.recent = self.recent[:12]


SCIENTIFIC_PALETTES: dict[str, list[str]] = {
    "viridis_like": ["#440154", "#414487", "#2A788E", "#22A884", "#7AD151", "#FDE725"],
    "colorblind_safe": ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"],
    "diverging_blue_orange": ["#2166AC", "#67A9CF", "#D1E5F0", "#FDDBC7", "#EF8A62", "#B2182B"],
}


def pick_color(parent, store: PaletteStore):  # type: ignore[no-untyped-def]
    from PySide6.QtWidgets import QColorDialog

    dialog = QColorDialog(parent)
    dialog.setOption(QColorDialog.ShowAlphaChannel, True)
    if dialog.exec():
        color = dialog.selectedColor()
        value = color.name().upper()
        store.add_recent(value)
        return value
    return None
