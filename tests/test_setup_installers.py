import os
from pathlib import Path

from bioplatform.setup.pymol_installer import ensure_pymol_installed
from bioplatform.setup.r_installer import RInstaller, ensure_r_installed


def test_ensure_helpers_honor_skip_env(monkeypatch) -> None:
    monkeypatch.setenv("BIOPLATFORM_SKIP_AUTO_SETUP", "1")
    assert ensure_r_installed() is True
    assert ensure_pymol_installed() is True


def test_r_installer_builds_linux_command(monkeypatch, tmp_path: Path) -> None:
    installer = RInstaller()
    monkeypatch.setattr(installer, "system", "linux")

    debian = tmp_path / "debian_version"
    debian.write_text("12", encoding="utf-8")

    orig_exists = Path.exists

    def fake_exists(self: Path) -> bool:  # type: ignore[override]
        if str(self) == "/etc/debian_version":
            return True
        return orig_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    assert installer._install_command()[:3] == ["sudo", "apt-get", "install"]


def test_r_installer_reports_not_found(monkeypatch) -> None:
    installer = RInstaller()
    monkeypatch.setattr(installer, "find_r_installation", lambda: None)
    ok, msg, home = installer.check_r_installation()
    assert ok is False
    assert "not found" in msg.lower()
    assert home is None
