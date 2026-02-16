from __future__ import annotations

"""Structural-thermodynamic bridge utilities for PDB-centric analytics."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class PDBAtom:
    residue_id: int
    residue_name: str
    atom_name: str
    x: float
    y: float
    z: float
    b_factor: float


@dataclass(frozen=True, slots=True)
class StructureMetrics:
    residue_ids: NDArray[np.int64]
    residue_rmsf: NDArray[np.float64]
    residue_bfactor_mean: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SASAResult:
    total_sasa: float
    hydrophobic_sasa: float
    hydrophilic_sasa: float


@dataclass(frozen=True, slots=True)
class EnergeticMap:
    residue_ids: NDArray[np.int64]
    delta_g_contrib_j_mol: NDArray[np.float64]


def parse_pdb_atoms(path: Path) -> list[PDBAtom]:
    if not path.exists():
        raise FileNotFoundError(path)
    atoms: list[PDBAtom] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        residue_id = int(line[22:26].strip() or "0")
        residue_name = line[17:20].strip()
        atom_name = line[12:16].strip()
        x = float(line[30:38].strip() or "0")
        y = float(line[38:46].strip() or "0")
        z = float(line[46:54].strip() or "0")
        b = float(line[60:66].strip() or "0")
        atoms.append(PDBAtom(residue_id=residue_id, residue_name=residue_name, atom_name=atom_name, x=x, y=y, z=z, b_factor=b))
    return atoms


def residue_rmsf(atoms: list[PDBAtom]) -> StructureMetrics:
    if not atoms:
        raise ValueError("atoms required")
    residue_ids = np.array([a.residue_id for a in atoms], dtype=np.int64)
    coords = np.array([[a.x, a.y, a.z] for a in atoms], dtype=np.float64)
    b_factors = np.array([a.b_factor for a in atoms], dtype=np.float64)

    unique_res = np.unique(residue_ids)
    rmsf_vals: list[float] = []
    b_mean_vals: list[float] = []
    for rid in unique_res:
        mask = residue_ids == rid
        xyz = coords[mask]
        centroid = xyz.mean(axis=0)
        sq = ((xyz - centroid) ** 2).sum(axis=1)
        rmsf_vals.append(float(np.sqrt(sq.mean())))
        b_mean_vals.append(float(b_factors[mask].mean()))
    return StructureMetrics(
        residue_ids=unique_res.astype(np.int64),
        residue_rmsf=np.array(rmsf_vals, dtype=np.float64),
        residue_bfactor_mean=np.array(b_mean_vals, dtype=np.float64),
    )


def sasa_rolling_ball(atoms: list[PDBAtom], probe_radius: float = 1.4) -> SASAResult:
    """Portable approximate SASA estimator.

    Uses atomic-count approximation per residue class as a pragmatic placeholder.
    """
    if probe_radius <= 0:
        raise ValueError("probe_radius must be positive")
    if not atoms:
        return SASAResult(total_sasa=0.0, hydrophobic_sasa=0.0, hydrophilic_sasa=0.0)

    hydrophobic = {"ALA", "VAL", "ILE", "LEU", "MET", "PHE", "TRP", "PRO"}
    base_area = 4.0 * np.pi * (1.7 + probe_radius) ** 2

    residue_names = np.array([a.residue_name for a in atoms], dtype=object)
    total = float(base_area * len(atoms))
    hydrophobic_mask = np.isin(residue_names, np.array(list(hydrophobic), dtype=object))
    hydro = float(base_area * hydrophobic_mask.sum())
    philic = max(0.0, total - hydro)
    return SASAResult(total_sasa=total, hydrophobic_sasa=hydro, hydrophilic_sasa=philic)


def energetic_mapping(metrics: StructureMetrics, kd_by_residue_m: NDArray[np.float64], temperature_k: float = 298.15) -> EnergeticMap:
    if kd_by_residue_m.shape[0] != metrics.residue_ids.shape[0]:
        raise ValueError("kd_by_residue_m size must match residue count")
    if np.any(kd_by_residue_m <= 0):
        raise ValueError("kd values must be positive")
    r = 8.31446261815324
    dg = r * temperature_k * np.log(kd_by_residue_m)
    return EnergeticMap(residue_ids=metrics.residue_ids, delta_g_contrib_j_mol=dg.astype(np.float64))
