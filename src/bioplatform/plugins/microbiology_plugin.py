from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..core.microbiology import (
    analyze_growth_curve,
    contamination_flags,
    detect_outliers_zscore,
    fit_standard_curve,
)
from .base import BioPlugin, PluginContext


@dataclass(slots=True)
class ASTResult:
    interpretation: str
    standard_used: str


class MicrobiologyPlugin(BioPlugin):
    plugin_id = "microbiology.intelligence"
    plugin_name = "Microbiology Intelligence"

    def __init__(self, standards_path: Path | None = None) -> None:
        self.standards_path = standards_path or Path(__file__).with_name("data") / "ast_standards.json"

    def register_ui(self, context: PluginContext) -> dict[str, str]:
        return {
            "title": "Microbiology",
            "subtitle": "Outliers, growth kinetics, and AST interpretation",
            "workspace": context.workspace,
        }

    def execute_logic(self, payload: dict[str, object]) -> dict[str, object]:
        mode = str(payload.get("mode", ""))
        if mode == "outliers":
            values = [float(v) for v in payload.get("values", [])]
            return {"outlier_indices": detect_outliers_zscore(values)}

        if mode == "growth":
            time = [float(v) for v in payload.get("time_hours", [])]
            od = [float(v) for v in payload.get("od600", [])]
            metrics = analyze_growth_curve(time, od)
            return {
                "mu_max": metrics.mu_max,
                "generation_time": metrics.generation_time,
                "carrying_capacity": metrics.carrying_capacity,
                "lag_phase_hours": metrics.lag_phase_hours,
                "flags": contamination_flags(od),
            }

        if mode == "standard_curve":
            concentrations = [float(v) for v in payload.get("concentrations", [])]
            signals = [float(v) for v in payload.get("signals", [])]
            fit = fit_standard_curve(concentrations, signals)
            return {"slope": fit.slope, "intercept": fit.intercept, "r2": fit.r_squared}

        if mode == "ast_zone":
            return self._interpret_ast(
                organism=str(payload["organism"]),
                antibiotic=str(payload["antibiotic"]),
                value=float(payload["zone_mm"]),
                metric="zone_mm",
            )

        if mode == "ast_mic":
            return self._interpret_ast(
                organism=str(payload["organism"]),
                antibiotic=str(payload["antibiotic"]),
                value=float(payload["mic_ug_ml"]),
                metric="mic_ug_ml",
            )

        raise ValueError("Unsupported microbiology mode")

    def _interpret_ast(self, organism: str, antibiotic: str, value: float, metric: str) -> dict[str, object]:
        standards = json.loads(self.standards_path.read_text(encoding="utf-8"))
        org_data = standards.get(organism.lower())
        if not org_data:
            raise ValueError(f"No AST standards for organism: {organism}")
        ab_data = org_data.get(antibiotic.lower())
        if not ab_data:
            raise ValueError(f"No AST standards for antibiotic: {antibiotic}")

        m = ab_data[metric]
        if metric == "zone_mm":
            if value >= float(m["susceptible_min"]):
                interp = "Susceptible"
            elif value <= float(m["resistant_max"]):
                interp = "Resistant"
            else:
                interp = "Intermediate"
        else:
            if value <= float(m["susceptible_max"]):
                interp = "Susceptible"
            elif value >= float(m["resistant_min"]):
                interp = "Resistant"
            else:
                interp = "Intermediate"

        return {
            "interpretation": interp,
            "standard": f"{organism}/{antibiotic}/{metric}",
            "input_value": value,
        }
