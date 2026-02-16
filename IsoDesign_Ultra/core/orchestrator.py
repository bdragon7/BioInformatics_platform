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
    """Dependency-aware DAG orchestrator for plugin execution."""

    def __init__(self, plugins_dir: Path | str = "plugins") -> None:
        self.loader = PluginLoader(plugins_dir=plugins_dir)
        self.registry = self.loader.load_all()

    def _resolve_plugins(self, requested_outputs: list[str]) -> list[str]:
        output_to_plugin: dict[str, str] = {}
        for key, handle in self.registry.items():
            for out in handle.metadata.outputs:
                output_to_plugin.setdefault(out, key)

        selected: set[str] = set()
        queue = list(requested_outputs)
        while queue:
            needed_output = queue.pop(0)
            plugin_key = output_to_plugin.get(needed_output)
            if plugin_key is None:
                continue
            if plugin_key in selected:
                continue
            selected.add(plugin_key)
            queue.extend(self.registry[plugin_key].metadata.inputs)
        return list(selected)

    def build_graph(self, requested_outputs: list[str]) -> list[str]:
        selected = self._resolve_plugins(requested_outputs)
        if not selected:
            return []

        # Build producer map within selected plugins.
        producer: dict[str, str] = {}
        for key in selected:
            for out in self.registry[key].metadata.outputs:
                producer.setdefault(out, key)

        # Build adjacency + indegree for topological sorting.
        adjacency: dict[str, set[str]] = {k: set() for k in selected}
        indegree: dict[str, int] = {k: 0 for k in selected}

        for key in selected:
            for inp in self.registry[key].metadata.inputs:
                parent = producer.get(inp)
                if parent and parent != key and key not in adjacency[parent]:
                    adjacency[parent].add(key)
                    indegree[key] += 1

        ready = sorted([k for k, deg in indegree.items() if deg == 0])
        ordered: list[str] = []
        while ready:
            node = ready.pop(0)
            ordered.append(node)
            for child in sorted(adjacency[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)

        # Cycle fallback: append remaining nodes deterministically.
        if len(ordered) != len(selected):
            remaining = sorted(set(selected) - set(ordered))
            ordered.extend(remaining)
        return ordered

    def execute(self, payload: dict[str, Any], requested_outputs: list[str]) -> dict[str, Any]:
        order = self.build_graph(requested_outputs)
        current = dict(payload)
        current["execution_order"] = order
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
