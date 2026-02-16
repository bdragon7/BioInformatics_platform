from __future__ import annotations

from dataclasses import dataclass


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
