from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import subprocess

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

    def install_github_plugin(self, manifest: PluginManifest, plugins_dir: Path, mode: str = "portable") -> Path:
        """Install plugin repo into local folder; optionally run full pip install."""
        if not manifest.id.startswith("github:"):
            raise ValueError("install_github_plugin expects github manifest")

        owner_repo = manifest.id.replace("github:", "", 1)
        target = plugins_dir / owner_repo.split("/")[-1]
        plugins_dir.mkdir(parents=True, exist_ok=True)

        if target.exists() and any(target.iterdir()):
            subprocess.run(["git", "-C", str(target), "pull", "--ff-only"], check=False)
        else:
            subprocess.run(["git", "clone", f"https://github.com/{owner_repo}.git", str(target)], check=False)

        if mode == "full":
            subprocess.run(["python", "-m", "pip", "install", "-e", str(target)], check=False)

        self.install_manifest(manifest)
        return target
