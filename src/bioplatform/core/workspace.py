from __future__ import annotations

from pathlib import Path

from .models import ProjectPaths


class WorkspaceManager:
    """Creates and validates project directory structure in app-local paths."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_id: str) -> ProjectPaths:
        project_root = self.workspace_root / project_id
        paths = ProjectPaths(project_root)
        for p in [
            paths.root,
            paths.raw,
            paths.intermediate,
            paths.results,
            paths.figures,
            paths.logs,
            paths.metadata,
        ]:
            p.mkdir(parents=True, exist_ok=True)
        return paths
