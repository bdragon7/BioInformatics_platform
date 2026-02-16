from pathlib import Path

from bioplatform.io.importers import ImportInspector


def test_file_classification() -> None:
    inspector = ImportInspector()
    assert inspector.inspect(Path("a.csv")).valid
    assert inspector.inspect(Path("reads.fastq")).category == "bioinformatics"
    assert not inspector.inspect(Path("notes.docx")).valid
