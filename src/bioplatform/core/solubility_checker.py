from __future__ import annotations

"""Solubility and stability intelligence helpers for formulation safety checks."""

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List
import json
import math


@dataclass(slots=True)
class SolubilityWarning:
    ingredient: str
    warning: str


@dataclass(slots=True)
class StabilityEstimate:
    retest_date: str
    estimated_half_life_days: float


class SolubilityChecker:
    def __init__(self, database_path: Path | None = None) -> None:
        path = database_path or Path(__file__).with_name("data").joinpath("solubility_database.json")
        self.database: Dict[str, Dict[str, float | str]] = {}
        if path.exists():
            self.database = json.loads(path.read_text(encoding="utf-8"))

        self.incompatibility_pairs = {
            tuple(sorted(["sodium hypochlorite", "citric acid"])): "Oxidizer-acid pair may evolve hazardous chlorine species.",
            tuple(sorted(["hydrogen peroxide", "chlorhexidine"])): "Oxidizer may degrade biguanide antiseptic activity.",
            tuple(sorted(["benzalkonium chloride", "sodium lauryl sulfate"])): "Cationic/anionic pair can precipitate or lose efficacy.",
        }

    def check_solubility(self, ingredient: str, concentration_g_l: float, temperature_c: float = 25.0) -> SolubilityWarning | None:
        row = self.database.get(ingredient.lower())
        if row is None:
            return None
        sat_25 = float(row.get("solubility_g_l_25c", 0.0))
        temp_coeff = float(row.get("temp_coeff_per_c", 0.0))
        sat_at_t = sat_25 * (1 + temp_coeff * (temperature_c - 25.0))
        sat_at_t = max(1e-9, sat_at_t)
        if concentration_g_l >= 0.8 * sat_at_t:
            return SolubilityWarning(
                ingredient=ingredient,
                warning=(
                    f"High crystallization risk: concentration {concentration_g_l:.3f} g/L is >= 80% of "
                    f"estimated saturation ({sat_at_t:.3f} g/L at {temperature_c:.1f}C)."
                ),
            )
        return None

    def check_incompatibilities(self, ingredients: List[str]) -> List[str]:
        names = [x.lower().strip() for x in ingredients if x.strip()]
        warnings: List[str] = []
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                key = tuple(sorted([left, right]))
                note = self.incompatibility_pairs.get(key)
                if note:
                    warnings.append(f"{left} + {right}: {note}")
        return warnings

    def estimate_retest_date(
        self,
        activation_energy_kj_mol: float,
        storage_temp_c: float,
        baseline_half_life_days: float,
        baseline_temp_c: float = 25.0,
    ) -> StabilityEstimate:
        """Arrhenius-based relative half-life estimate.

        k ~ exp(-Ea/RT), half-life inversely proportional to k.
        """
        if activation_energy_kj_mol <= 0 or baseline_half_life_days <= 0:
            raise ValueError("activation energy and baseline half-life must be positive")
        r = 8.314
        ea = activation_energy_kj_mol * 1000.0
        t_ref = baseline_temp_c + 273.15
        t_use = storage_temp_c + 273.15
        if t_use <= 0:
            raise ValueError("invalid absolute temperature")

        ln_k_ratio = (-ea / r) * ((1.0 / t_use) - (1.0 / t_ref))
        k_ratio = math.exp(ln_k_ratio)
        half_life = baseline_half_life_days / max(k_ratio, 1e-9)

        retest = date.today() + timedelta(days=max(1, int(round(half_life))))
        return StabilityEstimate(retest_date=str(retest), estimated_half_life_days=half_life)
