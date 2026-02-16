from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(slots=True)
class ChecklistItem:
    key: str
    label: str
    passed: bool
    detail: str


class AnalysisGuardrails:
    """Pre-analysis coaching/checklist engine to prevent common mistakes."""

    def build_checklist(
        self,
        *,
        normalized: bool,
        batch_effect_addressed: bool,
        outliers_reviewed: bool,
        sample_size_ok: bool,
        assumptions_met: bool,
    ) -> list[ChecklistItem]:
        return [
            ChecklistItem("normalized", "Data normalized", normalized, "Counts scale validated."),
            ChecklistItem("batch", "Batch effects addressed", batch_effect_addressed, "Batch covariates reviewed."),
            ChecklistItem("outliers", "Outliers reviewed", outliers_reviewed, "Outlier report checked."),
            ChecklistItem("sample_size", "Sample size adequate", sample_size_ok, "Power/sample size check completed."),
            ChecklistItem("assumptions", "Statistical assumptions met", assumptions_met, "Assumption diagnostics checked."),
        ]

    def recommendation(self, checklist: list[ChecklistItem]) -> str:
        failed = [item for item in checklist if not item.passed]
        if not failed:
            return "Proceed"
        keys = {f.key for f in failed}
        if "normalized" in keys:
            return "Apply normalization before continuing."
        if "assumptions" in keys:
            return "Switch to non-parametric alternatives or transform data."
        return "Proceed with caution; review failed checklist items."


class SpreadsheetValueGuard:
    """Validates spreadsheet entries before analysis/model updates."""

    _non_negative_markers = ("conc", "concentration", "dose", "molar", "molarity")

    def validate(self, header: str, value: str) -> tuple[bool, str]:
        text = str(value).strip()
        if not text or text.startswith("="):
            return True, ""

        key = header.lower().strip()
        try:
            numeric = float(text)
        except Exception:
            return True, ""

        if not isfinite(numeric):
            return False, "Non-finite numeric values are not allowed."

        if any(marker in key for marker in self._non_negative_markers) and numeric < 0:
            return False, f"{header or 'Value'} cannot be negative."
        return True, ""
