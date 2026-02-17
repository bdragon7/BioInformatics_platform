from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class PipelineNode(Generic[T]):
    name: str
    func: Callable[[dict[str, T]], T]
    depends_on: tuple[str, ...] = ()


class WorkflowDAGExecutor(Generic[T]):
    """Deterministic DAG execution with topological ordering."""

    def __init__(self) -> None:
        self._nodes: dict[str, PipelineNode[T]] = {}

    def add_node(self, node: PipelineNode[T]) -> None:
        self._nodes[node.name] = node

    def topological_order(self) -> list[str]:
        indegree: dict[str, int] = {name: 0 for name in self._nodes}
        edges: dict[str, list[str]] = defaultdict(list)

        for node in self._nodes.values():
            for dep in node.depends_on:
                if dep not in self._nodes:
                    raise ValueError(f"Unknown dependency '{dep}' for node '{node.name}'")
                edges[dep].append(node.name)
                indegree[node.name] += 1

        queue = deque(sorted([n for n, d in indegree.items() if d == 0]))
        order: list[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for nxt in sorted(edges[current]):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if len(order) != len(self._nodes):
            raise ValueError("Cycle detected in workflow DAG")
        return order

    def execute(self) -> dict[str, T]:
        outputs: dict[str, T] = {}
        for name in self.topological_order():
            node = self._nodes[name]
            outputs[name] = node.func(outputs)
        return outputs
