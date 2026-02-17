import json
from pathlib import Path

from bioplatform.plugins.plugin_manager_complete import CompletePluginManager, PluginStatus


def _make_plugin(path: Path, plugin_id: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text(
        json.dumps({"id": plugin_id, "name": plugin_id, "version": "1.0.0", "author": "test"}),
        encoding="utf-8",
    )
    (path / "plugin.py").write_text("x = 1\n", encoding="utf-8")


def test_enable_disable_remove_user_plugin(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg"
    mgr = CompletePluginManager(config_dir=cfg)

    plugin_dir = mgr.user_plugins_dir / "demo"
    _make_plugin(plugin_dir, "demo")
    mgr.discover_plugins()

    assert "demo" in mgr.plugins
    ok, _ = mgr.disable_plugin("demo")
    assert ok and mgr.plugins["demo"].status == PluginStatus.DISABLED

    ok, _ = mgr.enable_plugin("demo")
    assert ok and mgr.plugins["demo"].status in {PluginStatus.ENABLED, PluginStatus.ERROR}

    ok, _ = mgr.remove_plugin("demo")
    assert ok
    assert "demo" not in mgr.plugins


def test_cannot_remove_builtin(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg"
    mgr = CompletePluginManager(config_dir=cfg)
    # explicit metadata to avoid relying on existing builtins
    from bioplatform.plugins.plugin_manager_complete import PluginMetadata
    mgr.plugins["builtin-x"] = PluginMetadata(
        plugin_id="builtin-x",
        name="builtin-x",
        version="1.0",
        author="x",
        description="x",
        status=PluginStatus.DISABLED,
        source="builtin",
        install_path=str(tmp_path / "builtin-x"),
    )
    ok, msg = mgr.remove_plugin("builtin-x")
    assert ok is False
    assert "built-in" in msg.lower()
