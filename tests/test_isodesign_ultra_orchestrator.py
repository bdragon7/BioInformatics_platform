from pathlib import Path

from IsoDesign_Ultra.core.orchestrator import ExecutionOrchestrator, FormulationState


def test_orchestrator_builds_dependency_order(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"

    p1 = plugins / "desc"
    p1.mkdir(parents=True)
    (p1 / "plugin.py").write_text(
        """
__plugin_info__ = {'name':'desc','version':'1.0','inputs':['smiles'],'outputs':['descriptors'],'language':'python'}
def run(payload):
    return {'descriptors': [1,2,3]}
""",
        encoding="utf-8",
    )

    p2 = plugins / "plot"
    p2.mkdir(parents=True)
    (p2 / "plugin.py").write_text(
        """
__plugin_info__ = {'name':'plot','version':'1.0','inputs':['descriptors'],'outputs':['plot'],'language':'python'}
def run(payload):
    return {'plot': 'ok'}
""",
        encoding="utf-8",
    )

    orch = ExecutionOrchestrator(plugins)
    order = orch.build_graph(["plot"])
    assert len(order) == 2
    # descriptor plugin must execute before plot plugin
    assert "python:desc@1.0" in order[0]
    assert "python:plot@1.0" in order[1]

    result = orch.execute({"smiles": "CCO"}, ["plot"])
    assert result["plot"] == "ok"
    assert result["execution_order"] == order


def test_orchestrator_injects_formulation_state(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"
    p = plugins / "consumer"
    p.mkdir(parents=True)
    (p / "plugin.py").write_text(
        """
__plugin_info__ = {'name':'consumer','version':'1.0','inputs':['formulation_state'],'outputs':['state_seen'],'language':'python'}
def run(payload):
    fs = payload.get('formulation_state')
    return {'state_seen': fs.theoretical_ph if fs else None}
""",
        encoding="utf-8",
    )

    orch = ExecutionOrchestrator(plugins)
    orch.set_formulation_state(FormulationState(final_volume_ml=1000.0, theoretical_ph=6.8, ionic_strength_m=0.1))

    result = orch.execute({}, ["state_seen"])
    assert result["state_seen"] == 6.8
