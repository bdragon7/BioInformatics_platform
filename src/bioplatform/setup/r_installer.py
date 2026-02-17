from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Callable


class RInstaller:
    """Automatic R detection and best-effort installation helpers."""

    REQUIRED_R_PACKAGES = [
        "ggplot2",
        "dplyr",
        "tidyr",
        "DESeq2",
        "edgeR",
        "limma",
        "BiocManager",
    ]

    def __init__(self) -> None:
        self.system = platform.system().lower()
        self.r_home: str | None = None
        self.r_executable: str | None = None

    def check_r_installation(self) -> tuple[bool, str, str | None]:
        found = self.find_r_installation()
        if not found:
            return False, "R not found", None
        exe = found["executable"]
        proc = subprocess.run([exe, "--version"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return False, "R found but not working", None
        first = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else "R"
        self.r_home = found["home"]
        self.r_executable = exe
        return True, first, found["home"]

    def find_r_installation(self) -> dict[str, str] | None:
        if self.system == "windows":
            roots = [
                Path(os.environ.get("R_HOME", "")),
                Path("C:/Program Files/R"),
                Path("C:/Program Files (x86)/R"),
                Path.home() / "AppData" / "Local" / "Programs" / "R",
            ]
            for root in roots:
                if not str(root):
                    continue
                if root.is_file():
                    continue
                if root.name.startswith("R-"):
                    cand = root / "bin" / "x64" / "R.exe"
                    if cand.exists():
                        return {"home": str(root), "executable": str(cand)}
                if root.exists():
                    for d in root.glob("R-*"):
                        cand = d / "bin" / "x64" / "R.exe"
                        if cand.exists():
                            return {"home": str(d), "executable": str(cand)}
            return None

        which = subprocess.run(["which", "R"], capture_output=True, text=True, check=False)
        if which.returncode != 0:
            return None
        exe = which.stdout.strip()
        home = subprocess.run([exe, "RHOME"], capture_output=True, text=True, check=False).stdout.strip()
        if not home:
            home = str(Path(exe).resolve().parents[1])
        return {"home": home, "executable": exe}

    def install_r_automatic(self, progress_callback: Callable[[int, str], None] | None = None) -> tuple[bool, str]:
        if progress_callback:
            progress_callback(5, "Checking existing R installation")
        ok, version, home = self.check_r_installation()
        if ok:
            if progress_callback:
                progress_callback(100, f"R already installed: {version}")
            self.install_required_packages(progress_callback)
            return True, f"R already installed at {home}"

        # Best-effort auto install commands per platform.
        cmd = self._install_command()
        if not cmd:
            return False, "Unsupported platform for automatic installation"

        if progress_callback:
            progress_callback(20, "Installing R runtime")
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return False, f"Automatic installation failed: {proc.stderr.strip() or proc.stdout.strip()}"

        ok, version, home = self.check_r_installation()
        if not ok:
            return False, "Installation finished but R could not be detected"

        if progress_callback:
            progress_callback(80, "Installing required R packages")
        self.install_required_packages(progress_callback)
        if progress_callback:
            progress_callback(100, f"R ready: {version}")
        return True, f"R installed at {home}"

    def _install_command(self) -> list[str] | None:
        if self.system == "windows":
            return ["winget", "install", "RProject.R"]
        if self.system == "darwin":
            return ["brew", "install", "r"]
        if self.system == "linux":
            if Path("/etc/debian_version").exists():
                return ["sudo", "apt-get", "install", "-y", "r-base", "r-base-dev"]
            if Path("/etc/fedora-release").exists():
                return ["sudo", "dnf", "install", "-y", "R", "R-devel"]
            if Path("/etc/arch-release").exists():
                return ["sudo", "pacman", "-S", "--noconfirm", "r"]
        return None

    def install_required_packages(self, progress_callback: Callable[[int, str], None] | None = None) -> bool:
        if not self.r_executable:
            ok, _v, _h = self.check_r_installation()
            if not ok or not self.r_executable:
                return False
        total = len(self.REQUIRED_R_PACKAGES)
        for i, pkg in enumerate(self.REQUIRED_R_PACKAGES):
            if progress_callback:
                progress_callback(80 + int((i / max(total, 1)) * 20), f"Installing {pkg}")
            if pkg in {"DESeq2", "edgeR", "limma"}:
                code = (
                    'if (!requireNamespace("BiocManager", quietly=TRUE)) '
                    'install.packages("BiocManager", repos="https://cran.r-project.org"); '
                    f'BiocManager::install("{pkg}", update=FALSE, ask=FALSE)'
                )
            else:
                code = f'if (!requireNamespace("{pkg}", quietly=TRUE)) install.packages("{pkg}", repos="https://cran.r-project.org")'
            subprocess.run([self.r_executable, "--vanilla", "--slave", "-e", code], capture_output=True, text=True, check=False)
        return True


def ensure_r_installed() -> bool:
    if os.environ.get("BIOPLATFORM_SKIP_AUTO_SETUP") == "1":
        return True
    installer = RInstaller()
    ok, _version, home = installer.check_r_installation()
    if ok and home:
        os.environ["R_HOME"] = home
        installer.install_required_packages()
        return True
    success, _message = installer.install_r_automatic()
    if not success:
        return False
    ok, _version, home = installer.check_r_installation()
    if ok and home:
        os.environ["R_HOME"] = home
    return ok
