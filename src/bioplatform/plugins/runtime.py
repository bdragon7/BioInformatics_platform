from __future__ import annotations

import hashlib
import importlib.util
import json
import multiprocessing as mp
import shutil
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
    trusted: bool
    description: str = ""
    source: str = "local"
    hash_sha256: str = ""
    permissions: tuple[str, ...] = ()


@dataclass(slots=True)
class PluginSecurityState:
    enabled: bool = False
    trusted: bool = False


class LocalPluginRuntime:
    def __init__(self, plugins_dir: Path, state_file: Path, *, seed_builtins: bool = False) -> None:
        self.plugins_dir = plugins_dir
        self.state_file = state_file
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self.state_file.write_text("{}", encoding="utf-8")
        if seed_builtins:
            self._seed_builtin_plugins()

    def _seed_builtin_plugins(self) -> None:
        builtin_root = Path(__file__).with_name("builtin")
        if not builtin_root.exists():
            return
        for entry in builtin_root.iterdir():
            if not entry.is_dir():
                continue
            target = self.plugins_dir / entry.name
            manifest = entry / "manifest.json"
            plugin_py = entry / "plugin.py"
            if not (manifest.exists() and plugin_py.exists()):
                continue
            if not target.exists():
                shutil.copytree(entry, target)

    def _load_state(self) -> dict[str, PluginSecurityState]:
        try:
            raw = json.loads(self.state_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {}
            state: dict[str, PluginSecurityState] = {}
            for plugin_id, info in raw.items():
                if isinstance(info, bool):  # backward compatibility
                    state[plugin_id] = PluginSecurityState(enabled=info, trusted=info)
                    continue
                if isinstance(info, dict):
                    state[plugin_id] = PluginSecurityState(
                        enabled=bool(info.get("enabled", False)),
                        trusted=bool(info.get("trusted", False)),
                    )
            return state
        except Exception:
            return {}

    def _save_state(self, state: dict[str, PluginSecurityState]) -> None:
        payload = {
            plugin_id: {"enabled": info.enabled, "trusted": info.trusted}
            for plugin_id, info in state.items()
        }
        self.state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _hash_plugin(self, plugin_dir: Path) -> str:
        digest = hashlib.sha256()
        for rel in ["manifest.json", "plugin.py"]:
            file_path = plugin_dir / rel
            if not file_path.exists():
                continue
            digest.update(file_path.read_bytes())
        return digest.hexdigest()

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
            plugin_state = state.get(pid, PluginSecurityState())
            permissions = data.get("permissions", [])
            out.append(
                LocalPlugin(
                    plugin_id=pid,
                    name=str(data.get("name", pid)),
                    path=entry,
                    enabled=plugin_state.enabled,
                    trusted=plugin_state.trusted,
                    description=str(data.get("description", "")),
                    source=str(data.get("source", "local")),
                    hash_sha256=self._hash_plugin(entry),
                    permissions=tuple(str(x) for x in permissions) if isinstance(permissions, list) else (),
                )
            )
        return out

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        state = self._load_state()
        current = state.get(plugin_id, PluginSecurityState())
        state[plugin_id] = PluginSecurityState(enabled=enabled, trusted=current.trusted)
        self._save_state(state)

    def set_trusted(self, plugin_id: str, trusted: bool) -> None:
        state = self._load_state()
        current = state.get(plugin_id, PluginSecurityState())
        state[plugin_id] = PluginSecurityState(enabled=current.enabled and trusted, trusted=trusted)
        self._save_state(state)

    def load_enabled_instances(self, context: PluginContext) -> list[BioPlugin]:
        instances: list[BioPlugin] = []
        for plugin in self.list_plugins():
            if not plugin.enabled or not plugin.trusted:
                continue
            module_path = plugin.path / "plugin.py"
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin.plugin_id}", module_path)
            if spec is None or spec.loader is None:
                continue
            try:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                cls = getattr(module, "Plugin", None)
                if cls is None:
                    continue
                obj: Any = cls()
                if isinstance(obj, BioPlugin):
                    obj.register_ui(context)
                    instances.append(obj)
            except Exception:
                continue
        return instances

    def execute_plugin_isolated(self, plugin_id: str, payload: dict[str, object], timeout: float = 5.0) -> dict[str, object]:
        plugin = next((p for p in self.list_plugins() if p.plugin_id == plugin_id), None)
        if plugin is None:
            return {"ok": False, "error": "plugin-not-found"}
        if not plugin.enabled:
            return {"ok": False, "error": "plugin-disabled"}
        if not plugin.trusted:
            return {"ok": False, "error": "plugin-untrusted"}

        queue: mp.Queue[dict[str, object]] = mp.Queue()
        proc = mp.Process(target=_plugin_subprocess_entry, args=(plugin.path, payload, queue), daemon=True)
        proc.start()
        proc.join(timeout)
        if proc.is_alive():
            proc.terminate()
            proc.join(1.0)
            return {"ok": False, "error": "plugin-timeout"}
        if queue.empty():
            return {"ok": False, "error": "plugin-no-result"}
        return queue.get()


def _plugin_subprocess_entry(plugin_path: Path, payload: dict[str, object], queue: mp.Queue[dict[str, object]]) -> None:
    try:
        module_path = plugin_path / "plugin.py"
        spec = importlib.util.spec_from_file_location(f"plugin_exec_{plugin_path.name}", module_path)
        if spec is None or spec.loader is None:
            queue.put({"ok": False, "error": "invalid-plugin-module"})
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = getattr(module, "Plugin", None)
        if cls is None:
            queue.put({"ok": False, "error": "missing-plugin-class"})
            return
        obj = cls()
        if not isinstance(obj, BioPlugin):
            queue.put({"ok": False, "error": "invalid-plugin-class"})
            return
        result = obj.execute_logic(payload)
        if isinstance(result, dict):
            queue.put({"ok": True, "result": result})
            return
        queue.put({"ok": True, "result": {"value": result}})
    except Exception as exc:
        queue.put({"ok": False, "error": str(exc)})
