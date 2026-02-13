from __future__ import annotations

import sys
from pathlib import Path

from ..io.importers import ImportInspector
from ..plugins.discovery import PluginIndexAggregator, PluginQuery
from ..plugins.manager import PluginRegistry


def run() -> int:
    try:
        from PySide6.QtWidgets import (
            QApplication,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except Exception:
        print("PySide6 is not installed. Install with: pip install '.[gui]'")
        return 1

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("BioPlatform MVP")

            self.inspector = ImportInspector()
            self.aggregator = PluginIndexAggregator()
            self.registry = PluginRegistry(Path("config/plugins.json"))

            container = QWidget(self)
            layout = QVBoxLayout(container)

            top = QHBoxLayout()
            self.plugin_query = QLineEdit()
            self.plugin_query.setPlaceholderText("Search plugins (CRAN/Bioconductor)")
            self.plugin_query.setToolTip("Search package repositories for bioinformatics plugins.")
            top.addWidget(self.plugin_query)

            search_btn = QPushButton("Search")
            search_btn.setToolTip("Find plugins. If unavailable, import from GitHub URL.")
            search_btn.clicked.connect(self.search_plugins)
            top.addWidget(search_btn)
            layout.addLayout(top)

            self.results = QListWidget()
            self.results.setToolTip("Search results. Double-click to install manifest in local registry.")
            self.results.itemDoubleClicked.connect(self.install_selected)
            layout.addWidget(self.results)

            import_btn = QPushButton("Inspect Files")
            import_btn.setToolTip("Preview and validate local files before import.")
            import_btn.clicked.connect(self.inspect_files)
            layout.addWidget(import_btn)

            self.info = QLabel("Ready")
            self.info.setToolTip("Status area with quick guidance.")
            layout.addWidget(self.info)

            self.setCentralWidget(container)

        def search_plugins(self) -> None:
            query = self.plugin_query.text().strip()
            if not query:
                self.info.setText("Enter a plugin search query.")
                return
            manifests = self.aggregator.search_all(PluginQuery(query, limit=25))
            self.results.clear()
            if not manifests and ("/" in query or query.startswith("http")):
                gh = self.aggregator.import_from_github(query)
                self.results.addItem(f"{gh.id} | {gh.description}")
                self.info.setText("Added GitHub fallback entry.")
                return
            for item in manifests:
                self.results.addItem(f"{item.id} | {item.version} | {item.description}")
            self.info.setText(f"Found {len(manifests)} plugin candidates.")

        def install_selected(self, item) -> None:  # type: ignore[no-untyped-def]
            raw = item.text().split(" | ")[0]
            if raw.startswith("github:"):
                manifest = self.aggregator.import_from_github(raw.replace("github:", ""))
            else:
                QMessageBox.information(self, "Install", "MVP install is implemented for GitHub fallback entries.")
                return
            self.registry.install_manifest(manifest)
            self.info.setText(f"Installed {manifest.id}")

        def inspect_files(self) -> None:
            files, _ = QFileDialog.getOpenFileNames(self, "Select files")
            if not files:
                return
            previews = self.inspector.batch_inspect([Path(f) for f in files])
            valid = sum(1 for p in previews if p.valid)
            self.info.setText(f"Validated {valid}/{len(previews)} files")

    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(900, 600)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
