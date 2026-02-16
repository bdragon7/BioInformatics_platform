from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(slots=True)
class QCFlag:
    sample_id: str
    severity: str
    issue: str
    recommendation: str


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def detect_outliers(samples: dict[str, float], z_threshold: float = 3.0) -> list[QCFlag]:
    values = list(samples.values())
    m = _mean(values)
    s = _std(values)
    if s == 0:
        return []
    flags: list[QCFlag] = []
    for sample_id, value in samples.items():
        z = abs((value - m) / s)
        if z >= z_threshold:
            flags.append(
                QCFlag(
                    sample_id=sample_id,
                    severity="warning",
                    issue=f"Outlier detected (z={z:.2f})",
                    recommendation="Inspect sample quality and consider exclusion or robust methods.",
                )
            )
    return flags


def detect_sample_mixup_by_correlation(
    sample_to_group: dict[str, str], correlation_matrix: dict[str, dict[str, float]], threshold: float = 0.9
) -> list[QCFlag]:
    flags: list[QCFlag] = []
    for sample, group in sample_to_group.items():
        corr_row = correlation_matrix.get(sample, {})
        best_other = None
        best_corr = -1.0
        for other, corr in corr_row.items():
            if other == sample:
                continue
            if corr > best_corr:
                best_corr = corr
                best_other = other
        if best_other and best_corr >= threshold:
            other_group = sample_to_group.get(best_other, group)
            if other_group != group:
                flags.append(
                    QCFlag(
                        sample_id=sample,
                        severity="error",
                        issue=f"Possible sample mix-up: best correlation with {best_other} ({best_corr:.2f}) in group {other_group}",
                        recommendation="Verify sample sheet and replicate labels before differential analysis.",
                    )
                )
    return flags


def qc_traffic_light(flags: list[QCFlag]) -> str:
    if any(f.severity == "error" for f in flags):
        return "red"
    if flags:
        return "yellow"
    return "green"
