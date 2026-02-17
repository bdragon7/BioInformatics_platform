from pathlib import Path

from bioplatform.plugins.models import PluginManifest
from bioplatform.services.plugins import FakePluginIndexClient, PluginService


def test_fake_plugin_index_client_search() -> None:
    client = FakePluginIndexClient(
        manifests=[
            PluginManifest(
                id="github:org/repo",
                name="repo",
                version="git",
                language="mixed",
                source="github",
                entrypoint="org/repo",
                description="x",
            )
        ]
    )
    out = client.search("org", limit=5)
    assert len(out) == 1
    assert out[0].id == "github:org/repo"


def test_plugin_service_install_selected(monkeypatch, tmp_path: Path) -> None:
    service = PluginService.default(config_dir=tmp_path / "config", plugins_dir=tmp_path / "plugins")

    def fake_install(manifest, plugins_dir, mode="portable"):
        target = plugins_dir / "repo"
        target.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(service.registry, "install_github_plugin", fake_install)
    target = service.install_selected("github:org/repo", mode="portable")
    assert target.name == "repo"
