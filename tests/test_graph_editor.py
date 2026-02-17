from bioplatform.visualization.editor_state import GraphEditorState, GraphElement


def test_undo_redo() -> None:
    state = GraphEditorState()
    state.upsert(GraphElement(id="p1", kind="point"))
    state.set_property("p1", "color", "red")
    assert state.elements["p1"].properties["color"] == "red"
    assert state.undo()
    assert "color" not in state.elements["p1"].properties
    assert state.redo()
    assert state.elements["p1"].properties["color"] == "red"
