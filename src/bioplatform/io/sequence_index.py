from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SequenceRecordLite:
    seq_id: str
    length: int


class SequenceIndexer:
    """High-volume sequence access using Biopython SeqIO.index when available."""

    def __init__(self) -> None:
        self._index = None

    def open(self, path: Path, fmt: str = "fasta") -> int:
        try:
            from Bio import SeqIO  # type: ignore
        except Exception as exc:
            raise RuntimeError("Biopython is required for indexed sequence access") from exc

        self._index = SeqIO.index(str(path), fmt)
        return len(self._index)

    def ids(self) -> list[str]:
        if self._index is None:
            return []
        return list(self._index.keys())

    def get(self, seq_id: str) -> SequenceRecordLite:
        if self._index is None:
            raise RuntimeError("Sequence index not initialized")
        rec = self._index[seq_id]
        return SequenceRecordLite(seq_id=str(rec.id), length=len(rec.seq))

    def close(self) -> None:
        if self._index is not None:
            self._index.close()
            self._index = None
