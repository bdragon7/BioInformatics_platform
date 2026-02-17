from pathlib import Path

from bioplatform.plugins.discovery import PluginIndexAggregator, PluginQuery
from bioplatform.plugins.manager import PluginRegistry


def test_github_import_manifest() -> None:
    agg = PluginIndexAggregator()
    m = agg.import_from_github("https://github.com/org/repo")
    assert m.id == "github:org/repo"


def test_registry_install(tmp_path: Path) -> None:
    registry = PluginRegistry(tmp_path / "plugins.json")
    manifest = PluginIndexAggregator().import_from_github("org/repo")
    registry.install_manifest(manifest)
    installed = registry.list_installed()
    assert installed and installed[0].id == "github:org/repo"


def test_search_all_prefers_github_repo_query() -> None:
    agg = PluginIndexAggregator()
    results = agg.search_all(PluginQuery("org/repo", limit=5))
    assert results
    assert results[0].id.startswith("github:")


def test_builtin_pymol_plugin_files_present() -> None:
    base = Path("src/bioplatform/plugins/builtin/pymol_bridge")
    assert (base / "manifest.json").exists()
    assert (base / "plugin.py").exists()
