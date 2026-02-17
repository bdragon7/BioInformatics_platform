from pathlib import Path

from bioplatform.plugins.base import BioPlugin, PluginContext
from bioplatform.plugins.runtime import LocalPluginRuntime


def test_local_plugin_runtime_lists_and_persists_state(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugin_dir = plugins_dir / "demo"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        '{"id":"demo.plugin","name":"Demo Plugin","description":"test plugin"}',
        encoding="utf-8",
    )
    (plugin_dir / "plugin.py").write_text(
        """
from bioplatform.plugins.base import BioPlugin

class Plugin(BioPlugin):
    plugin_id = "demo.plugin"
    plugin_name = "Demo Plugin"

    def register_ui(self, context):
        return {"title": context.app_name}

    def execute_logic(self, payload):
        return {"ok": True, "payload": payload}
""".strip(),
        encoding="utf-8",
    )

    runtime = LocalPluginRuntime(plugins_dir=plugins_dir, state_file=tmp_path / "config" / "enabled.json")
    plugins = runtime.list_plugins()
    assert len(plugins) == 1
    assert plugins[0].plugin_id == "demo.plugin"
    assert plugins[0].enabled is True

    runtime.set_enabled("demo.plugin", False)
    assert runtime.list_plugins()[0].enabled is False


def test_local_plugin_runtime_loads_enabled_instances(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugin_dir = plugins_dir / "live"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text('{"id":"live.plugin","name":"Live"}', encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(
        """
from bioplatform.plugins.base import BioPlugin

class Plugin(BioPlugin):
    plugin_id = "live.plugin"
    plugin_name = "Live"

    def register_ui(self, context):
        return {"workspace": context.workspace}

    def execute_logic(self, payload):
        return {"result": "done"}
""".strip(),
        encoding="utf-8",
    )

    runtime = LocalPluginRuntime(plugins_dir=plugins_dir, state_file=tmp_path / "enabled.json")
    instances = runtime.load_enabled_instances(PluginContext(app_name="Bio", workspace="default"))
    assert len(instances) == 1
    assert isinstance(instances[0], BioPlugin)
    assert instances[0].execute_logic({"x": 1})["result"] == "done"


def test_runtime_seeds_builtin_pymol_plugin(tmp_path: Path) -> None:
    runtime = LocalPluginRuntime(plugins_dir=tmp_path / "plugins", state_file=tmp_path / "enabled.json", seed_builtins=True)
    ids = {p.plugin_id for p in runtime.list_plugins()}
    assert "structure.pymol_bridge" in ids
