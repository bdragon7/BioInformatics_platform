from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WorkflowNode:
    id: str
    name: str
    language: str
    entrypoint: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkflowEdge:
    source: str
    target: str


@dataclass(slots=True)
class WorkflowGraph:
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)

    def validate_acyclic(self) -> bool:
        graph: dict[str, list[str]] = {n.id: [] for n in self.nodes}
        for edge in self.edges:
            graph.setdefault(edge.source, []).append(edge.target)

        temp: set[str] = set()
        perm: set[str] = set()

        def visit(node: str) -> bool:
            if node in perm:
                return True
            if node in temp:
                return False
            temp.add(node)
            for nxt in graph.get(node, []):
                if not visit(nxt):
                    return False
            temp.remove(node)
            perm.add(node)
            return True

        return all(visit(node_id) for node_id in graph)
