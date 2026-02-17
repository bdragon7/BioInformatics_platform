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
    assert plugins[0].enabled is False
    assert plugins[0].trusted is False

    runtime.set_trusted("demo.plugin", True)
    runtime.set_enabled("demo.plugin", True)
    enabled = runtime.list_plugins()[0]
    assert enabled.enabled is True and enabled.trusted is True


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
    runtime.set_trusted("live.plugin", True)
    runtime.set_enabled("live.plugin", True)
    instances = runtime.load_enabled_instances(PluginContext(app_name="Bio", workspace="default"))
    assert len(instances) == 1
    assert isinstance(instances[0], BioPlugin)
    assert instances[0].execute_logic({"x": 1})["result"] == "done"


def test_runtime_seeds_builtin_pymol_plugin(tmp_path: Path) -> None:
    runtime = LocalPluginRuntime(plugins_dir=tmp_path / "plugins", state_file=tmp_path / "enabled.json", seed_builtins=True)
    ids = {p.plugin_id for p in runtime.list_plugins()}
    assert "structure.pymol_bridge" in ids



def test_runtime_executes_plugin_in_isolated_process(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugin_dir = plugins_dir / "iso"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text('{"id":"iso.plugin","name":"Iso"}', encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(
        """
from bioplatform.plugins.base import BioPlugin

class Plugin(BioPlugin):
    plugin_id = "iso.plugin"
    plugin_name = "Iso"

    def register_ui(self, context):
        return {}

    def execute_logic(self, payload):
        return {"echo": payload.get("msg", "")}
""".strip(),
        encoding="utf-8",
    )

    runtime = LocalPluginRuntime(plugins_dir=plugins_dir, state_file=tmp_path / "enabled.json")
    runtime.set_trusted("iso.plugin", True)
    runtime.set_enabled("iso.plugin", True)

    result = runtime.execute_plugin_isolated("iso.plugin", {"msg": "ok"})
    assert result["ok"] is True
    assert result["result"]["echo"] == "ok"


def test_runtime_blocks_untrusted_plugin_execution(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugin_dir = plugins_dir / "blocked"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text('{"id":"blocked.plugin","name":"Blocked"}', encoding="utf-8")
    (plugin_dir / "plugin.py").write_text("pass\n", encoding="utf-8")

    runtime = LocalPluginRuntime(plugins_dir=plugins_dir, state_file=tmp_path / "enabled.json")
    runtime.set_enabled("blocked.plugin", True)
    out = runtime.execute_plugin_isolated("blocked.plugin", {"x": 1})
    assert out["ok"] is False
    assert out["error"] == "plugin-untrusted"



def test_runtime_skips_broken_plugin_imports(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugin_dir = plugins_dir / "broken"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text('{"id":"broken.plugin","name":"Broken"}', encoding="utf-8")
    (plugin_dir / "plugin.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")

    runtime = LocalPluginRuntime(plugins_dir=plugins_dir, state_file=tmp_path / "enabled.json")
    runtime.set_trusted("broken.plugin", True)
    runtime.set_enabled("broken.plugin", True)

    instances = runtime.load_enabled_instances(PluginContext(app_name="Bio", workspace="default"))
    assert instances == []
