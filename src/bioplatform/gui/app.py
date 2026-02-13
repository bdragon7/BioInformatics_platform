from __future__ import annotations

import sys
from pathlib import Path

from ..plugins.discovery import PluginIndexAggregator, PluginQuery
from ..plugins.manager import PluginRegistry
from .color_tools import PaletteStore, pick_color
from .data_table import create_data_viewer_widget
from .themes import THEMES


def run(
    project: Path | None = None,
    data: Path | None = None,
    workflow: str | None = None,
    debug: bool = False,
) -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QApplication,
            QDockWidget,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QSplitter,
            QVBoxLayout,
            QWidget,
            QComboBox,
        )
    except Exception:
        print("PySide6 is not installed. Install with: pip install '.[gui]'")
        return 1

    DataViewerWidget = create_data_viewer_widget()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Bioinformatics Studio")

            self.aggregator = PluginIndexAggregator()
            self.registry = PluginRegistry(Path("config/plugins.json"))
            self.palette_store = PaletteStore()

            shell = QWidget(self)
            shell_layout = QVBoxLayout(shell)

            top = QHBoxLayout()
            self.project_label = QLabel(f"Project: {project if project else 'default'}")
            top.addWidget(self.project_label)

            self.global_search = QLineEdit()
            self.global_search.setPlaceholderText("Command/search (Ctrl+K style)")
            self.global_search.setToolTip("Global search placeholder for actions, datasets, and workflows.")
            top.addWidget(self.global_search)

            self.theme_combo = QComboBox()
            self.theme_combo.addItems(list(THEMES.keys()))
            self.theme_combo.currentTextChanged.connect(self.apply_theme)
            self.theme_combo.setToolTip("Switch visual theme instantly.")
            top.addWidget(self.theme_combo)

            color_btn = QPushButton("Pick Color")
            color_btn.setToolTip("Open scientific color picker with alpha support.")
            color_btn.clicked.connect(self.choose_color)
            top.addWidget(color_btn)

            shell_layout.addLayout(top)

            splitter = QSplitter(Qt.Horizontal)

            nav = QListWidget()
            nav.addItems(["📊 Data", "🔬 Analysis", "📈 Visualizations", "📦 Plugins", "⚙️ Settings"])
            nav.setMaximumWidth(220)
            nav.setToolTip("Primary navigation zones")
            splitter.addWidget(nav)

            self.data_viewer = DataViewerWidget()
            self.data_viewer.selection_changed.connect(self._on_selection_count)
            splitter.addWidget(self.data_viewer)

            self.info_panel = QListWidget()
            self.info_panel.addItem("Selection summary will appear here.")
            self.info_panel.setMaximumWidth(280)
            splitter.addWidget(self.info_panel)
            splitter.setSizes([180, 900, 240])

            shell_layout.addWidget(splitter)
            self.setCentralWidget(shell)

            plugin_dock = QDockWidget("Plugin Manager", self)
            plugin_widget = QWidget()
            plugin_layout = QVBoxLayout(plugin_widget)

            self.plugin_query = QLineEdit()
            self.plugin_query.setPlaceholderText("Search CRAN/Bioconductor or paste GitHub repo")
            self.plugin_query.setToolTip("Find bioinformatics plugins. GitHub fallback is supported.")
            plugin_layout.addWidget(self.plugin_query)

            plugin_search_btn = QPushButton("Search Plugins")
            plugin_search_btn.clicked.connect(self.search_plugins)
            plugin_layout.addWidget(plugin_search_btn)

            self.plugin_results = QListWidget()
            self.plugin_results.itemDoubleClicked.connect(self.install_selected)
            plugin_layout.addWidget(self.plugin_results)

            plugin_dock.setWidget(plugin_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, plugin_dock)

            self.statusBar().showMessage("Ready")

            if data:
                self.data_viewer.load_file(data)
                self.statusBar().showMessage(f"Loaded data: {data}")
            if workflow:
                self.info_panel.addItem(f"Requested workflow: {workflow}")
            if debug:
                self.info_panel.addItem("Debug mode enabled")

        def apply_theme(self, name: str) -> None:
            theme = THEMES[name]
            QApplication.instance().setStyleSheet(theme.stylesheet)
            self.statusBar().showMessage(f"Theme: {name}", 2500)

        def choose_color(self) -> None:
            color = pick_color(self, self.palette_store)
            if color:
                self.info_panel.addItem(f"Picked color: {color} | recent={', '.join(self.palette_store.recent[:4])}")

        def _on_selection_count(self, count: int) -> None:
            self.info_panel.addItem(f"Selected rows updated: {count}")

        def search_plugins(self) -> None:
            query = self.plugin_query.text().strip()
            if not query:
                self.statusBar().showMessage("Enter a plugin query", 2500)
                return
            manifests = self.aggregator.search_all(PluginQuery(query, limit=25))
            self.plugin_results.clear()
            if not manifests and ("/" in query or query.startswith("http")):
                gh = self.aggregator.import_from_github(query)
                self.plugin_results.addItem(f"{gh.id} | {gh.description}")
                self.statusBar().showMessage("GitHub fallback entry created", 3000)
                return
            for item in manifests:
                self.plugin_results.addItem(f"{item.id} | {item.version} | {item.description}")
            self.statusBar().showMessage(f"Found {len(manifests)} plugin candidates", 3000)

        def install_selected(self, item) -> None:  # type: ignore[no-untyped-def]
            raw = item.text().split(" | ")[0]
            if raw.startswith("github:"):
                manifest = self.aggregator.import_from_github(raw.replace("github:", ""))
            else:
                QMessageBox.information(self, "Install", "MVP install currently supports GitHub fallback entries.")
                return
            self.registry.install_manifest(manifest)
            self.statusBar().showMessage(f"Installed {manifest.id}", 3500)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1400, 860)
    win.apply_theme("dark")
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
