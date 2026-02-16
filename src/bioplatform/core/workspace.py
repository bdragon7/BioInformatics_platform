from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import ProjectPaths


class WorkspaceManager:
    """Creates and validates project directory structure in app-local paths."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self._audit_file = self.workspace_root / "audit_log.jsonl"

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

    def append_audit_entry(self, *, event: str, payload: dict[str, object]) -> dict[str, object]:
        previous_hash = "GENESIS"
        if self._audit_file.exists():
            last = self._audit_file.read_text(encoding="utf-8").strip().splitlines()
            if last:
                try:
                    previous_hash = json.loads(last[-1]).get("hash", "GENESIS")
                except Exception:
                    previous_hash = "GENESIS"

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
            "prev_hash": previous_hash,
        }
        digest = hashlib.sha256(json.dumps(entry, sort_keys=True).encode("utf-8")).hexdigest()
        entry["hash"] = digest
        with self._audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    @property
    def audit_log_path(self) -> Path:
        return self._audit_file
