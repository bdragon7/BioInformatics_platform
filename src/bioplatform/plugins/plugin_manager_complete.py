from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


class PluginStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    NOT_LOADED = "not_loaded"


@dataclass(slots=True)
class PluginMetadata:
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    status: PluginStatus
    source: str
    github_url: str | None = None
    install_path: str | None = None
    dependencies: list[str] = field(default_factory=list)
    error_message: str | None = None


class CompletePluginManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or (Path.home() / ".bioinformatics_platform")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.builtin_plugins_dir = Path("src/bioplatform/plugins/builtin")
        self.user_plugins_dir = self.config_dir / "plugins"
        self.user_plugins_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.config_dir / "plugin_state.json"
        self.plugins: dict[str, PluginMetadata] = {}
        self.loaded_modules: dict[str, Any] = {}
        self.plugin_state: dict[str, dict[str, Any]] = {}
        self.load_plugin_state()
        self.discover_plugins()

    def load_plugin_state(self) -> None:
        if self.state_file.exists():
            self.plugin_state = json.loads(self.state_file.read_text(encoding="utf-8"))

    def save_plugin_state(self) -> None:
        payload = {pid: {"enabled": p.status == PluginStatus.ENABLED, "status": p.status.value} for pid, p in self.plugins.items()}
        self.state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def discover_plugins(self) -> None:
        self.plugins.clear()
        self._discover_plugins_in_dir(self.builtin_plugins_dir, "builtin")
        self._discover_plugins_in_dir(self.user_plugins_dir, "github")

    def _discover_plugins_in_dir(self, root: Path, source: str) -> None:
        if not root.exists():
            return
        for plugin_dir in root.iterdir():
            if not plugin_dir.is_dir():
                continue
            manifest_path = plugin_dir / "manifest.json"
            plugin_py = plugin_dir / "plugin.py"
            if not manifest_path.exists() or not plugin_py.exists():
                continue
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            plugin_id = data.get("id", plugin_dir.name)
            enabled = self.plugin_state.get(plugin_id, {}).get("enabled", True)
            meta = PluginMetadata(
                plugin_id=plugin_id,
                name=data.get("name", plugin_id),
                version=data.get("version", "1.0.0"),
                author=data.get("author", "Unknown"),
                description=data.get("description", ""),
                status=PluginStatus.ENABLED if enabled else PluginStatus.DISABLED,
                source=source,
                github_url=data.get("github_url"),
                install_path=str(plugin_dir),
                dependencies=list(data.get("dependencies", [])),
            )
            self.plugins[plugin_id] = meta
            if enabled:
                self._load_plugin(meta)

    def _load_plugin(self, metadata: PluginMetadata) -> None:
        try:
            plugin_file = Path(metadata.install_path or "") / "plugin.py"
            spec = importlib.util.spec_from_file_location(metadata.plugin_id, plugin_file)
            if spec is None or spec.loader is None:
                raise RuntimeError("Failed to build import spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.loaded_modules[metadata.plugin_id] = module
            metadata.status = PluginStatus.ENABLED
            metadata.error_message = None
        except Exception as exc:
            metadata.status = PluginStatus.ERROR
            metadata.error_message = str(exc)

    def enable_plugin(self, plugin_id: str) -> tuple[bool, str]:
        meta = self.plugins.get(plugin_id)
        if not meta:
            return False, "Plugin not found"
        self._load_plugin(meta)
        self.save_plugin_state()
        return (meta.status == PluginStatus.ENABLED, f"Plugin '{meta.name}' {'enabled' if meta.status == PluginStatus.ENABLED else 'failed to enable'}")

    def disable_plugin(self, plugin_id: str) -> tuple[bool, str]:
        meta = self.plugins.get(plugin_id)
        if not meta:
            return False, "Plugin not found"
        if plugin_id in self.loaded_modules:
            module = self.loaded_modules.pop(plugin_id)
            cleanup = getattr(module, "cleanup", None)
            if callable(cleanup):
                cleanup()
        meta.status = PluginStatus.DISABLED
        self.save_plugin_state()
        return True, f"Plugin '{meta.name}' disabled"

    def remove_plugin(self, plugin_id: str) -> tuple[bool, str]:
        meta = self.plugins.get(plugin_id)
        if not meta:
            return False, "Plugin not found"
        if meta.source == "builtin":
            return False, "Cannot remove built-in plugins"
        self.disable_plugin(plugin_id)
        if meta.install_path:
            shutil.rmtree(meta.install_path, ignore_errors=True)
        self.plugins.pop(plugin_id, None)
        self.plugin_state.pop(plugin_id, None)
        self.save_plugin_state()
        return True, f"Plugin '{meta.name}' removed"

    def install_from_github(self, github_url: str, progress_callback=None) -> tuple[bool, str]:
        if "github.com" not in github_url:
            return False, "Invalid GitHub URL"
        repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
        temp_dir = self.user_plugins_dir / f".tmp_{repo_name}"
        target_dir = self.user_plugins_dir / repo_name
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if progress_callback:
            progress_callback(30, "Cloning repository")
        proc = subprocess.run(["git", "clone", "--depth", "1", github_url, str(temp_dir)], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return False, proc.stderr.strip() or "git clone failed"
        if not (temp_dir / "manifest.json").exists() or not (temp_dir / "plugin.py").exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False, "Invalid plugin structure (manifest.json/plugin.py required)"
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.move(str(temp_dir), str(target_dir))
        if progress_callback:
            progress_callback(90, "Plugin installed, refreshing registry")
        self.discover_plugins()
        self.save_plugin_state()
        return True, repo_name

    def get_all_plugins(self) -> list[PluginMetadata]:
        return list(self.plugins.values())

    def get_enabled_plugins(self) -> list[PluginMetadata]:
        return [p for p in self.plugins.values() if p.status == PluginStatus.ENABLED]
