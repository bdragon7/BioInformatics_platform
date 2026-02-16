from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FormulationAssessment:
    green_solubility_index: float
    hansen_distance: float
    risk: str



def smiles_to_feature_tensor(smiles_list: list[str]) -> list[list[float]]:
    """Convert SMILES to fixed-size features; uses RDKit if available, otherwise heuristics."""
    try:
        from rdkit import Chem  # type: ignore
        from rdkit.Chem import AllChem, MACCSkeys  # type: ignore

        tensor: list[list[float]] = []
        for smi in smiles_list:
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                tensor.append([0.0] * 16)
                continue
            morgan = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=8)
            maccs = MACCSkeys.GenMACCSKeys(mol)
            row = [float(int(morgan[i])) for i in range(8)] + [float(int(maccs[i])) for i in range(8)]
            tensor.append(row)
        return tensor
    except Exception:
        def heuristic(s: str) -> list[float]:
            return [
                float(len(s)),
                float(s.count("C")),
                float(s.count("N")),
                float(s.count("O")),
                float(s.count("=")),
                float(s.count("#")),
                float(s.count("(")),
                float(s.count(")")),
            ] + [0.0] * 8

        return [heuristic(s) for s in smiles_list]


class FormulationValidator:
    """Validator using Green Solubility Index + Hansen distance approximation."""

    def assess(self, api_smiles: str, excipient_smiles: str, ratio: float = 1.0) -> FormulationAssessment:
        api_feat = smiles_to_feature_tensor([api_smiles])[0]
        exc_feat = smiles_to_feature_tensor([excipient_smiles])[0]

        # Lightweight approximations for scaffold purposes.
        polarity_gap = abs(api_feat[2] + api_feat[3] - (exc_feat[2] + exc_feat[3]))
        hydro_gap = abs(api_feat[1] - exc_feat[1])
        hansen_distance = (polarity_gap**2 + hydro_gap**2) ** 0.5 / max(1.0, ratio)
        gsi = max(0.0, 100.0 - hansen_distance * 10.0)

        if hansen_distance < 2:
            risk = "low"
        elif hansen_distance < 5:
            risk = "moderate"
        else:
            risk = "high"

        return FormulationAssessment(
            green_solubility_index=gsi,
            hansen_distance=hansen_distance,
            risk=risk,
        )
