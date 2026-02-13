from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RStatus:
    available: bool
    executable: str | None
    version: str | None
    message: str


@dataclass(frozen=True, slots=True)
class FeatureGate:
    feature_id: str
    label: str
    requires_r: bool
    python_alternative: str | None = None


FEATURE_GATES: tuple[FeatureGate, ...] = (
    FeatureGate("de_deseq2", "Differential Expression (DESeq2)", True, "PyDESeq2"),
    FeatureGate("de_edger", "Differential Expression (edgeR)", True, "diffxpy"),
    FeatureGate("single_cell_seurat", "Single-cell (Seurat)", True, "scanpy"),
    FeatureGate("stats_lm", "Linear Models", False, "statsmodels"),
)


class RIntegrationManager:
    """Python-first R integration: app remains fully usable without R."""

    def __init__(self, preferred_executable: str | None = None, app_dir: Path | None = None) -> None:
        self.preferred_executable = preferred_executable or "Rscript"
        self.app_dir = app_dir or Path.cwd()

    def detect_r(self) -> RStatus:
        exe = shutil.which(self.preferred_executable)
        if not exe:
            portable = self.app_dir / "R" / "bin" / "Rscript.exe"
            if portable.exists():
                exe = str(portable)
        if not exe:
            return RStatus(
                available=False,
                executable=None,
                version=None,
                message="⚠️ R not detected - advanced R-only features are limited.",
            )
        try:
            proc = subprocess.run([exe, "--version"], check=False, capture_output=True, text=True)
            first_line = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else "R detected"
            return RStatus(True, exe, first_line, "R detected and ready.")
        except Exception:
            return RStatus(True, exe, None, "R detected but version query failed.")

    def feature_availability(self) -> dict[str, str]:
        status = self.detect_r()
        out: dict[str, str] = {}
        for gate in FEATURE_GATES:
            if gate.requires_r and not status.available:
                alt = f" Use Python alternative: {gate.python_alternative}." if gate.python_alternative else ""
                out[gate.feature_id] = f"R Required.{alt}"
            else:
                out[gate.feature_id] = "Available"
        return out

    def installer_plan(self) -> dict[str, object]:
        return {
            "title": "Install R (optional)",
            "estimated_size_mb": 250,
            "no_admin_required": True,
            "steps": [
                "Download portable R bundle",
                "Extract to ./R",
                "Validate Rscript availability",
                "Install BiocManager and selected packages",
            ],
            "recommended_packages": ["DESeq2", "edgeR", "limma", "clusterProfiler", "ComplexHeatmap"],
        }
