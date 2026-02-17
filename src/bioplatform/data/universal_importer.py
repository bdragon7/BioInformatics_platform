from __future__ import annotations

import csv
from pathlib import Path
import sqlite3
from typing import Any


class UniversalDataImporter:
    SUPPORTED_EXTENSIONS = [
        ".csv", ".tsv", ".txt", ".dat", ".tab",
        ".xlsx", ".xlsm", ".xls", ".xlsb", ".ods",
        ".sav", ".zsav", ".dta", ".sas7bdat", ".xpt",
        ".json", ".xml", ".parquet", ".feather", ".h5", ".hdf5",
        ".db", ".sqlite", ".sql",
    ]

    def can_import(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def import_file(self, file_path: Path, **kwargs: Any) -> tuple[bool, object | None, str]:
        file_path = Path(file_path)
        if not file_path.exists():
            return False, None, f"File not found: {file_path}"
        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False, None, f"Unsupported format: {ext}"

        try:
            import pandas as pd  # type: ignore
        except Exception:
            return self._fallback_import_without_pandas(file_path, **kwargs)

        try:
            if ext in [".csv", ".tsv", ".txt", ".dat", ".tab"]:
                delim = kwargs.pop("delimiter", None) or ("\t" if ext == ".tsv" else ",")
                df = pd.read_csv(file_path, delimiter=delim, **kwargs)
            elif ext in [".xlsx", ".xlsm", ".xls", ".xlsb", ".ods"]:
                engine = "odf" if ext == ".ods" else None
                df = pd.read_excel(file_path, engine=engine, **kwargs)
            elif ext in [".sav", ".zsav"]:
                df = pd.read_spss(file_path, **kwargs)
            elif ext == ".dta":
                df = pd.read_stata(file_path, **kwargs)
            elif ext in [".sas7bdat", ".xpt"]:
                fmt = "xport" if ext == ".xpt" else "sas7bdat"
                df = pd.read_sas(file_path, format=fmt, **kwargs)
            elif ext == ".json":
                df = pd.read_json(file_path, **kwargs)
            elif ext == ".xml":
                df = pd.read_xml(file_path, **kwargs)
            elif ext == ".parquet":
                df = pd.read_parquet(file_path, **kwargs)
            elif ext == ".feather":
                df = pd.read_feather(file_path, **kwargs)
            elif ext in [".h5", ".hdf5"]:
                df = pd.read_hdf(file_path, **kwargs)
            else:
                table_name = kwargs.get("table_name")
                conn = sqlite3.connect(file_path)
                try:
                    if not table_name:
                        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                        row = cur.fetchone()
                        if row is None:
                            return False, None, "No tables found in database"
                        table_name = row[0]
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                finally:
                    conn.close()
            df = self._clean_dataframe(df)
            return True, df, f"Imported {len(df)} rows from {file_path.name}"
        except Exception as exc:
            return False, None, f"Import error: {exc}"

    def _fallback_import_without_pandas(self, file_path: Path, **kwargs: Any) -> tuple[bool, object | None, str]:
        ext = file_path.suffix.lower()
        if ext in [".csv", ".tsv", ".txt", ".dat", ".tab"]:
            delim = kwargs.get("delimiter") or ("\t" if ext == ".tsv" else ",")
            with file_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter=delim)
                rows = list(reader)
            return True, rows, f"Imported {len(rows)} rows from {file_path.name} (fallback mode)"
        return False, None, "This format requires pandas and optional IO dependencies"

    def _clean_dataframe(self, df):  # type: ignore[no-untyped-def]
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        df.columns = [str(c).strip() for c in df.columns]
        return df
