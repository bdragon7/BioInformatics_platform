from pathlib import Path

from IsoDesign_Ultra.core.kernel import PluginLoader, health_check


def test_plugin_loader_discovers_and_loads_python_plugin(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"
    p = plugins / "toy"
    p.mkdir(parents=True)
    (p / "toy_plugin.py").write_text(
        """
__plugin_info__ = {
  'name': 'toy',
  'version': '1.0',
  'inputs': ['x'],
  'outputs': ['y'],
  'language': 'python'
}

def run(payload):
    return {'y': payload.get('x', 0)}
""",
        encoding="utf-8",
    )
    loader = PluginLoader(plugins)
    registry = loader.load_all()
    assert registry
    handle = next(iter(registry.values()))
    assert handle.metadata.name == "toy"
    out = handle.executable({"x": 7})
    assert out["y"] == 7


def test_health_check_has_expected_keys() -> None:
    result = health_check()
    assert "python" in result
    assert "rdkit" in result
    assert "rpy2" in result
    assert "compute_backend" in result
