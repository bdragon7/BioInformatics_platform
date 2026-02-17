from __future__ import annotations

from dataclasses import dataclass

from .affinity import AffinityPredictionModule, AffinityPredictionResult
from .pockets import PocketIdentificationModule, PocketPrediction
from .structure import StructurePredictionModule, StructurePredictionResult


@dataclass(slots=True)
class WorkflowResult:
    structures: list[StructurePredictionResult]
    affinity: AffinityPredictionResult | None
    pockets: list[PocketPrediction]


class IsoDDEPipeline:
    """Unified lightweight workflow inspired by IsoDDE module orchestration."""

    def __init__(self) -> None:
        self.structure = StructurePredictionModule()
        self.affinity = AffinityPredictionModule()
        self.pockets = PocketIdentificationModule()

    def predict_full_workflow(self, protein: str, ligand: str | None = None) -> WorkflowResult:
        pockets = self.pockets.predict_pockets(protein)
        structures = self.structure.predict_structure({"protein": protein, "ligand": ligand or ""})
        affinity = self.affinity.predict_affinity(protein, ligand or "") if ligand else None
        return WorkflowResult(structures=structures, affinity=affinity, pockets=pockets)
