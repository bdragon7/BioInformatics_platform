from __future__ import annotations

import os
import subprocess
import sys


class PyMOLInstaller:
    def check_pymol(self) -> tuple[bool, str]:
        try:
            import pymol  # type: ignore

            return True, getattr(pymol, "__version__", "unknown")
        except Exception:
            return False, "Not installed"

    def install_pymol_automatic(self) -> tuple[bool, str]:
        primary = [sys.executable, "-m", "pip", "install", "pymol-open-source"]
        fallback = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "git+https://github.com/schrodinger/pymol-open-source.git",
        ]
        for cmd in (primary, fallback):
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode == 0:
                ok, version = self.check_pymol()
                if ok:
                    return True, f"PyMOL {version} installed"
        return False, "PyMOL installation failed"


def ensure_pymol_installed() -> bool:
    if os.environ.get("BIOPLATFORM_SKIP_AUTO_SETUP") == "1":
        return True
    installer = PyMOLInstaller()
    ok, _ = installer.check_pymol()
    if ok:
        return True
    installer.install_pymol_automatic()
    return True
