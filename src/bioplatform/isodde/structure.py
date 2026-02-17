from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1


@dataclass(slots=True)
class StructurePredictionResult:
    modality: str
    model_source: str
    pseudo_pdb: str
    confidence: float
    violation_free: bool


class StructurePredictionModule:
    """Lightweight IsoDDE-style structure prediction facade."""

    def __init__(self, model_source: str = "openfold3") -> None:
        self.model_source = model_source

    def predict_structure(
        self,
        input_data: dict[str, str],
        modality: str = "protein-ligand",
        num_seeds: int = 25,
    ) -> list[StructurePredictionResult]:
        protein = input_data.get("protein", "")
        ligand = input_data.get("ligand", "")
        digest = sha1(f"{protein}|{ligand}|{modality}".encode("utf-8")).hexdigest()
        base_conf = min(0.98, max(0.45, 0.45 + (len(protein) % 50) / 100 + (0.03 if ligand else 0.0)))

        results: list[StructurePredictionResult] = []
        for idx in range(max(1, min(num_seeds, 8))):
            confidence = max(0.0, min(1.0, base_conf - idx * 0.02))
            pseudo = (
                f"HEADER    ISODDE PREDICTION\n"
                f"REMARK    MODEL={self.model_source} MODALITY={modality} CONF={confidence:.3f}\n"
                f"REMARK    HASH={digest[:16]} SEED={idx}\n"
            )
            results.append(
                StructurePredictionResult(
                    modality=modality,
                    model_source=self.model_source,
                    pseudo_pdb=pseudo,
                    confidence=confidence,
                    violation_free=confidence >= 0.5,
                )
            )
        return self.filter_violations(results)

    @staticmethod
    def filter_violations(structures: list[StructurePredictionResult]) -> list[StructurePredictionResult]:
        return [item for item in structures if item.violation_free]
