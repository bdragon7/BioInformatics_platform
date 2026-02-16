from __future__ import annotations

from dataclasses import dataclass
from math import isnan


@dataclass(slots=True)
class SanitizeResult:
    data: object
    warnings: list[str]


def smart_sanitize_sequence(sequence: str) -> SanitizeResult:
    allowed = {"A", "C", "G", "T", "U", "N"}
    cleaned: list[str] = []
    replaced = 0
    for ch in sequence.upper():
        if ch in allowed:
            cleaned.append(ch)
        elif ch.isspace():
            continue
        else:
            cleaned.append("N")
            replaced += 1

    warnings: list[str] = []
    if replaced:
        warnings.append(f"Replaced {replaced} unsupported bases with 'N'.")
    if not cleaned:
        warnings.append("Sequence became empty after sanitization.")
    return SanitizeResult(data="".join(cleaned), warnings=warnings)


def smart_sanitize_growth_values(values: list[float | None]) -> SanitizeResult:
    cleaned: list[float] = []
    warnings: list[str] = []
    replaced = 0
    last = 0.0
    for i, val in enumerate(values):
        numeric = float(val) if val is not None else float("nan")
        if isnan(numeric):
            replaced += 1
            warnings.append(f"NaN at index {i} replaced with previous value.")
            cleaned.append(last)
            continue
        cleaned.append(numeric)
        last = numeric
    if replaced:
        warnings.insert(0, f"Repaired {replaced} missing/NaN growth values.")
    return SanitizeResult(data=cleaned, warnings=warnings)


def lof_outliers(values: list[float], n_neighbors: int = 5) -> list[int]:
    if len(values) < 3:
        return []
    try:
        from sklearn.neighbors import LocalOutlierFactor  # type: ignore

        neighbors = min(max(2, n_neighbors), len(values) - 1)
        model = LocalOutlierFactor(n_neighbors=neighbors)
        labels = model.fit_predict([[v] for v in values])
        return [i for i, label in enumerate(labels) if label == -1]
    except Exception:
        # fallback robust z-score style behavior
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        if variance == 0:
            return []
        sd = variance**0.5
        return [i for i, x in enumerate(values) if abs((x - mean) / sd) > 2.5]


def universal_result(data: object, plots: object | None = None, outliers: list[int] | None = None, **meta: object) -> dict[str, object]:
    return {
        "data": data,
        "plots": plots,
        "outliers": outliers or [],
        "meta": meta,
    }
