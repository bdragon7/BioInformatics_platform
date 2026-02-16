from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import BioPlugin, PluginContext


@dataclass(slots=True)
class LocalPlugin:
    plugin_id: str
    name: str
    path: Path
    enabled: bool
    description: str = ""


class LocalPluginRuntime:
    def __init__(self, plugins_dir: Path, state_file: Path) -> None:
        self.plugins_dir = plugins_dir
        self.state_file = state_file
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self.state_file.write_text("{}", encoding="utf-8")

    def _load_state(self) -> dict[str, bool]:
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self, state: dict[str, bool]) -> None:
        self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def list_plugins(self) -> list[LocalPlugin]:
        state = self._load_state()
        out: list[LocalPlugin] = []
        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir():
                continue
            manifest = entry / "manifest.json"
            plugin_py = entry / "plugin.py"
            if not (manifest.exists() and plugin_py.exists()):
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except Exception:
                continue
            pid = str(data.get("id", entry.name))
            out.append(
                LocalPlugin(
                    plugin_id=pid,
                    name=str(data.get("name", pid)),
                    path=entry,
                    enabled=bool(state.get(pid, True)),
                    description=str(data.get("description", "")),
                )
            )
        return out

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        state = self._load_state()
        state[plugin_id] = enabled
        self._save_state(state)

    def load_enabled_instances(self, context: PluginContext) -> list[BioPlugin]:
        instances: list[BioPlugin] = []
        for plugin in self.list_plugins():
            if not plugin.enabled:
                continue
            module_path = plugin.path / "plugin.py"
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin.plugin_id}", module_path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls = getattr(module, "Plugin", None)
            if cls is None:
                continue
            obj: Any = cls()
            if isinstance(obj, BioPlugin):
                obj.register_ui(context)
                instances.append(obj)
        return instances
