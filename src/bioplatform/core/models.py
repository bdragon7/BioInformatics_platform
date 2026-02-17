from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProjectPaths:
    root: Path
    raw: Path = field(init=False)
    intermediate: Path = field(init=False)
    results: Path = field(init=False)
    figures: Path = field(init=False)
    logs: Path = field(init=False)
    metadata: Path = field(init=False)

    def __post_init__(self) -> None:
        self.raw = self.root / "raw"
        self.intermediate = self.root / "intermediate"
        self.results = self.root / "results"
        self.figures = self.root / "figures"
        self.logs = self.root / "logs"
        self.metadata = self.root / "metadata"


@dataclass(slots=True)
class RunRecord:
    node_id: str
    language: str
    command: str
    params: dict[str, Any]
    status: str
