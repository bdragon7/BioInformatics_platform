from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(slots=True)
class AffinityPredictionResult:
    pKd: float
    uncertainty: float
    per_model: dict[str, float]


class AffinityPredictionModule:
    """Ensemble-like affinity estimator with deterministic model heads."""

    def __init__(self) -> None:
        self.models = ("transformer", "gnn", "cnn")

    @staticmethod
    def _score_head(name: str, protein: str, ligand: str) -> float:
        signal = (len(protein) * 0.03) + (len(ligand) * 0.02)
        bias = {"transformer": 5.1, "gnn": 5.4, "cnn": 5.0}[name]
        return max(3.0, min(10.0, bias + (signal % 2.2)))

    def predict_affinity(self, protein: str, ligand: str) -> AffinityPredictionResult:
        per_model = {name: self._score_head(name, protein, ligand) for name in self.models}
        values = list(per_model.values())
        return AffinityPredictionResult(pKd=mean(values), uncertainty=pstdev(values), per_model=per_model)
