from pathlib import Path

from bioplatform.plugins.discovery import PluginIndexAggregator
from bioplatform.plugins.manager import PluginRegistry


def test_install_github_plugin_portable(monkeypatch, tmp_path: Path) -> None:
    registry = PluginRegistry(tmp_path / "plugins.json")
    manifest = PluginIndexAggregator().import_from_github("org/repo")

    def fake_run(args, check=False):  # type: ignore[no-untyped-def]
        if args[:2] == ["git", "clone"]:
            target = Path(args[-1])
            target.mkdir(parents=True, exist_ok=True)
        class P:  # simple stub
            returncode = 0
        return P()

    monkeypatch.setattr("subprocess.run", fake_run)

    target = registry.install_github_plugin(manifest, tmp_path / "plugins", mode="portable")
    assert target.exists()
    assert registry.list_installed()[0].id == "github:org/repo"
