from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.workspace import WorkspaceManager


@dataclass(slots=True)
class WorkspaceService:
    manager: WorkspaceManager

    @classmethod
    def from_root(cls, root: Path) -> WorkspaceService:
        root.mkdir(parents=True, exist_ok=True)
        return cls(manager=WorkspaceManager(root))
