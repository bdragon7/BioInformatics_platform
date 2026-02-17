from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path


@dataclass(slots=True)
class LogEntry:
    timestamp: str
    level: str
    message: str
    context: str = ""


class BioInformaticsLogger:
    """Simple structured logger for GUI and background diagnostics."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self.log_dir = log_dir or (Path.home() / ".bioinformatics_platform" / "logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.log_dir / f"session_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
        self._entries: list[LogEntry] = []

    def log(self, level: str, message: str, context: str = "") -> LogEntry:
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
            level=level.upper(),
            message=message,
            context=context,
        )
        self._entries.append(entry)
        self.session_file.open("a", encoding="utf-8").write(json.dumps(asdict(entry)) + "\n")
        return entry

    def recent(self, level: str = "ALL", limit: int = 100) -> list[LogEntry]:
        level = level.upper()
        data = self._entries if level == "ALL" else [e for e in self._entries if e.level == level]
        return data[-limit:]

    def export_json(self, output_path: Path) -> None:
        output_path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2), encoding="utf-8")
