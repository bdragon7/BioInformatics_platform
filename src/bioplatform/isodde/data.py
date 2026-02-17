from __future__ import annotations

import json
from pathlib import Path


class DataManager:
    """Minimal dataset and benchmark helper for IsoDDE toolkit."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_benchmarks(self) -> Path:
        path = self.data_dir / "benchmarks_manifest.json"
        path.write_text(
            json.dumps(
                {
                    "datasets": ["runs_n_poses", "foldbench", "fep_plus_4", "openfe", "chembl35"],
                    "status": "manifest-only",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return path
