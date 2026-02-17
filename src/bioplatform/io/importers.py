from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


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


class ChunkedCSVReader:
    """Read large CSV files in chunks to reduce peak memory usage."""

    def read_csv(
        self,
        path: Path,
        chunk_size: int = 50_000,
        progress: Callable[[int], None] | None = None,
    ) -> object:
        try:
            import pandas as pd  # type: ignore

            chunks: list[object] = []
            processed = 0
            for chunk in pd.read_csv(path, chunksize=chunk_size):
                chunks.append(chunk)
                processed += len(chunk)
                if progress is not None:
                    progress(processed)
            if not chunks:
                return pd.DataFrame()
            return pd.concat(chunks, ignore_index=True)
        except Exception:
            # Fallback path for minimal environments without pandas.
            import csv

            rows: list[dict[str, str]] = []
            processed = 0
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    rows.append(row)
                    processed += 1
                    if processed % max(chunk_size, 1) == 0 and progress is not None:
                        progress(processed)
            if progress is not None:
                progress(processed)
            return rows
