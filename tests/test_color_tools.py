from bioplatform.gui.color_tools import PaletteStore


def test_recent_palette_tracking() -> None:
    store = PaletteStore()
    store.add_recent("#123456")
    store.add_recent("#abcdef")
    store.add_recent("#123456")
    assert store.recent[0] == "#123456"
    assert "#ABCDEF" in store.recent
