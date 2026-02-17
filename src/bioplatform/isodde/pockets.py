from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PocketPrediction:
    residue_start: int
    residue_end: int
    score: float
    is_cryptic: bool


class PocketIdentificationModule:
    """Pocket finder with simple cryptic-pocket heuristic."""

    def predict_pockets(self, protein_sequence: str, top_k: int = 3) -> list[PocketPrediction]:
        n = max(1, len(protein_sequence))
        window = max(8, n // 10)
        pockets: list[PocketPrediction] = []
        for i in range(top_k):
            start = 1 + (i * window)
            end = min(n, start + window)
            score = max(0.2, min(0.95, 0.55 + (i * 0.08) + (n % 7) * 0.01))
            is_cryptic = (i == top_k - 1 and n > 120) or score > 0.8
            pockets.append(PocketPrediction(start, end, score, is_cryptic))
        return pockets
