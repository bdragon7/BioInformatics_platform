from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class CommandRecord:
    engine: str
    command: str
    output: str
    timestamp: datetime


class DualConsoleSession:
    """Backend model for Python/R command history and transcript."""

    def __init__(self) -> None:
        self.history: list[CommandRecord] = []

    def run_python(self, command: str) -> CommandRecord:
        output = f"python:{command.strip()}"
        return self._record("python", command, output)

    def run_r(self, command: str) -> CommandRecord:
        output = f"r:{command.strip()}"
        return self._record("r", command, output)

    def search(self, text: str) -> list[CommandRecord]:
        token = text.lower().strip()
        if not token:
            return list(self.history)
        return [r for r in self.history if token in r.command.lower() or token in r.output.lower()]

    def _record(self, engine: str, command: str, output: str) -> CommandRecord:
        record = CommandRecord(engine=engine, command=command, output=output, timestamp=datetime.utcnow())
        self.history.append(record)
        return record
