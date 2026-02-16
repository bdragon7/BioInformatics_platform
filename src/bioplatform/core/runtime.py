from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RuntimeConfig:
    python_exe: str = "python"
    rscript_exe: str = "Rscript"
    cwd: Path | None = None


class DualRuntimeBridge:
    """Executes Python and R tasks using subprocess for portability and isolation."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()

    def run_python(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.config.python_exe, str(script_path), *args],
            cwd=str(self.config.cwd) if self.config.cwd else None,
            check=False,
            capture_output=True,
            text=True,
        )

    def run_r(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.config.rscript_exe, str(script_path), *args],
            cwd=str(self.config.cwd) if self.config.cwd else None,
            check=False,
            capture_output=True,
            text=True,
        )
