from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec


ALPHAFOLD_SERVER = "https://alphafold.ebi.ac.uk"


@dataclass(slots=True)
class PyMOLStatus:
    available: bool
    message: str


def detect_pymol() -> PyMOLStatus:
    """Detect whether PyMOL can be imported in the current environment."""
    if find_spec("pymol") is not None:
        return PyMOLStatus(available=True, message="PyMOL module detected and ready.")
    return PyMOLStatus(
        available=False,
        message="PyMOL not installed. Install with: pip install pymol-open-source",
    )


def alphafold_prediction_url(uniprot_id: str) -> str:
    uid = uniprot_id.strip().upper()
    if not uid:
        raise ValueError("UniProt ID is required")
    return f"{ALPHAFOLD_SERVER}/entry/{uid}"
