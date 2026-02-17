from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DoEVariable:
    name: str
    vtype: str
    lower: float | None = None
    upper: float | None = None
    choices: list[str] | None = None


class AutoDoE:
    """Adaptive DoE scaffold with optional BoTorch/Ax backend."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.variables = [DoEVariable(**item) for item in config.get("variables", [])]
        self.objective = str(config.get("objective", "maximize"))
        self._history: list[dict[str, Any]] = []
        self._backend = self._init_backend()

    def _init_backend(self) -> str:
        try:
            import ax  # type: ignore
            import botorch  # type: ignore

            _ = (ax, botorch)
            return "botorch"
        except Exception:
            return "fallback"

    def observe(self, point: dict[str, Any], objective_value: float) -> None:
        row = dict(point)
        row["objective_value"] = float(objective_value)
        self._history.append(row)

    def suggest_next(self, n: int = 5) -> list[dict[str, Any]]:
        if self._backend == "botorch":
            # Dependency-aware placeholder: keeps scaffold import-safe when Ax/Botorch are absent.
            return self._fallback_suggestions(n)
        return self._fallback_suggestions(n)

    def _fallback_suggestions(self, n: int) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []
        for _ in range(max(1, n)):
            row: dict[str, Any] = {}
            for var in self.variables:
                if var.vtype == "continuous":
                    lo = float(var.lower if var.lower is not None else 0.0)
                    hi = float(var.upper if var.upper is not None else 1.0)
                    row[var.name] = lo + (hi - lo) * random.random()
                elif var.vtype == "integer":
                    lo = int(var.lower if var.lower is not None else 0)
                    hi = int(var.upper if var.upper is not None else 10)
                    row[var.name] = random.randint(lo, hi)
                elif var.vtype == "categorical":
                    options = var.choices or ["A", "B"]
                    row[var.name] = random.choice(options)
                else:
                    row[var.name] = None
            suggestions.append(row)
        return suggestions
