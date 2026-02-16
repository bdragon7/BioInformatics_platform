from bioplatform.workflow.models import WorkflowEdge, WorkflowGraph, WorkflowNode


def test_workflow_acyclic() -> None:
    graph = WorkflowGraph(
        nodes=[
            WorkflowNode("a", "import", "python", "module:fn"),
            WorkflowNode("b", "qc", "r", "script.R"),
        ],
        edges=[WorkflowEdge("a", "b")],
    )
    assert graph.validate_acyclic()


def test_workflow_cycle_detection() -> None:
    graph = WorkflowGraph(
        nodes=[
            WorkflowNode("a", "import", "python", "module:fn"),
            WorkflowNode("b", "qc", "r", "script.R"),
        ],
        edges=[WorkflowEdge("a", "b"), WorkflowEdge("b", "a")],
    )
    assert not graph.validate_acyclic()
