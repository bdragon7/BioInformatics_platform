from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GraphElement:
    id: str
    kind: str
    properties: dict[str, object] = field(default_factory=dict)


class GraphEditorState:
    """In-memory element store with undo/redo stacks for style edits."""

    def __init__(self) -> None:
        self.elements: dict[str, GraphElement] = {}
        self._undo: list[tuple[str, str, object, object]] = []
        self._redo: list[tuple[str, str, object, object]] = []

    def upsert(self, element: GraphElement) -> None:
        self.elements[element.id] = element

    def set_property(self, element_id: str, key: str, value: object) -> None:
        element = self.elements[element_id]
        old_value = element.properties.get(key)
        element.properties[key] = value
        self._undo.append((element_id, key, old_value, value))
        self._redo.clear()

    def undo(self) -> bool:
        if not self._undo:
            return False
        element_id, key, old, new = self._undo.pop()
        element = self.elements[element_id]
        if old is None and key in element.properties:
            del element.properties[key]
        else:
            element.properties[key] = old
        self._redo.append((element_id, key, old, new))
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        element_id, key, old, new = self._redo.pop()
        element = self.elements[element_id]
        element.properties[key] = new
        self._undo.append((element_id, key, old, new))
        return True
