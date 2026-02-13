from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TABULAR_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".ods"}
BIO_EXTENSIONS = {
    ".fasta",
    ".fa",
    ".fastq",
    ".fq",
    ".bam",
    ".sam",
    ".vcf",
    ".gff",
    ".gtf",
}


@dataclass(slots=True)
class FilePreview:
    path: Path
    category: str
    valid: bool
    message: str


class ImportInspector:
    def inspect(self, path: Path) -> FilePreview:
        suffix = path.suffix.lower()
        if suffix in TABULAR_EXTENSIONS:
            return FilePreview(path, "tabular", True, "Supported spreadsheet/tabular format")
        if suffix in BIO_EXTENSIONS:
            return FilePreview(path, "bioinformatics", True, "Supported bioinformatics format")
        return FilePreview(path, "unknown", False, "Unsupported file type")

    def batch_inspect(self, files: list[Path]) -> list[FilePreview]:
        return [self.inspect(f) for f in files]
