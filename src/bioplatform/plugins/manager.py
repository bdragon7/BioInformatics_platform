from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import PluginManifest


class PluginRegistry:
    def __init__(self, registry_path: Path) -> None:
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self.registry_path.write_text("[]", encoding="utf-8")

    def list_installed(self) -> list[PluginManifest]:
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return [PluginManifest(**item) for item in data]

    def install_manifest(self, manifest: PluginManifest) -> None:
        current = self.list_installed()
        current = [p for p in current if p.id != manifest.id]
        current.append(manifest)
        self.registry_path.write_text(
            json.dumps([asdict(p) for p in current], indent=2), encoding="utf-8"
        )
