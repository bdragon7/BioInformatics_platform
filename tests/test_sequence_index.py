from pathlib import Path

import pytest

from bioplatform.io.sequence_index import SequenceIndexer


def test_sequence_index_requires_open() -> None:
    idx = SequenceIndexer()
    with pytest.raises(RuntimeError):
        idx.get("seq1")


def test_sequence_index_open_and_get(tmp_path: Path) -> None:
    bio = pytest.importorskip("Bio")
    assert bio is not None

    fasta = tmp_path / "sample.fasta"
    fasta.write_text(">seq1\nACTGACTG\n>seq2\nTTAA\n", encoding="utf-8")

    idx = SequenceIndexer()
    count = idx.open(fasta, fmt="fasta")
    assert count == 2
    assert idx.ids() == ["seq1", "seq2"]
    rec = idx.get("seq1")
    assert rec.seq_id == "seq1"
    assert rec.length == 8
    idx.close()
    assert idx.ids() == []
