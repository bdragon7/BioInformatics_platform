from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


REQUIRED_FIELDS = ("sample_id", "group")


@dataclass(slots=True)
class MetadataRecord:
    sample_id: str
    group: str
    fields: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass(slots=True)
class MetadataValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]


class MetadataSchemaManager:
    """Schema and validation for reproducible experimental metadata."""

    def __init__(self) -> None:
        self.allowed_fields: dict[str, str] = {"sample_id": "text", "group": "categorical"}

    def add_field(self, name: str, field_type: str) -> None:
        self.allowed_fields[name] = field_type

    def validate(self, records: list[MetadataRecord]) -> MetadataValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        seen_ids: set[str] = set()
        for idx, rec in enumerate(records):
            if not rec.sample_id:
                errors.append(f"Row {idx + 1}: sample_id missing")
            if not rec.group:
                errors.append(f"Row {idx + 1}: group missing")
            if rec.sample_id in seen_ids:
                errors.append(f"Duplicate sample_id: {rec.sample_id}")
            seen_ids.add(rec.sample_id)
            for key in rec.fields:
                if key not in self.allowed_fields:
                    warnings.append(f"Unknown field '{key}' in sample {rec.sample_id}")
        return MetadataValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def standardize_category(self, value: str) -> str:
        normalized = value.strip().lower()
        mapping = {"tumour": "tumor", "ctrl": "control", "treated": "treatment"}
        return mapping.get(normalized, normalized)
