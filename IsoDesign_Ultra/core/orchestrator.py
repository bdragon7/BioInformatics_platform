from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .kernel import PluginLoader


@dataclass(slots=True)
class GraphNode:
    node_id: str
    plugin_key: str


class ExecutionOrchestrator:
    """Simple DAG orchestrator with optional networkx backend."""

    def __init__(self, plugins_dir: Path | str = "plugins") -> None:
        self.loader = PluginLoader(plugins_dir=plugins_dir)
        self.registry = self.loader.load_all()

    def build_graph(self, requested_outputs: list[str]) -> list[str]:
        # Lightweight fallback: topological list based on declared outputs/inputs.
        available = self.registry
        selected: list[str] = []
        needed = set(requested_outputs)
        for key, handle in available.items():
            if any(out in needed for out in handle.metadata.outputs):
                selected.append(key)
                needed.update(handle.metadata.inputs)
        return selected

    def execute(self, payload: dict[str, Any], requested_outputs: list[str]) -> dict[str, Any]:
        order = self.build_graph(requested_outputs)
        current = dict(payload)
        for key in order:
            handle = self.registry[key]
            exe = handle.executable
            if hasattr(exe, "execute"):
                out = exe.execute(current)
            elif callable(exe):
                out = exe(current)
            else:
                out = {"plugin": key, "warning": "non-callable plugin loaded"}
            if isinstance(out, dict):
                current.update(out)
        return current
