from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(slots=True)
class UserPreferences:
    project_root: str = "projects"
    output_dir: str = "outputs"


class PreferencesManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(UserPreferences())

    def load(self) -> UserPreferences:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return UserPreferences()
        return UserPreferences(
            project_root=str(raw.get("project_root", "projects")),
            output_dir=str(raw.get("output_dir", "outputs")),
        )

    def save(self, prefs: UserPreferences) -> None:
        self.path.write_text(json.dumps(asdict(prefs), indent=2), encoding="utf-8")
