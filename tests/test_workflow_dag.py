import pytest

from bioplatform.core.workflow_dag import PipelineNode, WorkflowDAGExecutor


def test_workflow_dag_executes_in_topological_order() -> None:
    dag: WorkflowDAGExecutor[int] = WorkflowDAGExecutor()
    dag.add_node(PipelineNode("a", lambda _out: 1))
    dag.add_node(PipelineNode("b", lambda out: out["a"] + 1, depends_on=("a",)))
    dag.add_node(PipelineNode("c", lambda out: out["b"] + 1, depends_on=("b",)))

    outputs = dag.execute()
    assert outputs == {"a": 1, "b": 2, "c": 3}


def test_workflow_dag_detects_cycle() -> None:
    dag: WorkflowDAGExecutor[int] = WorkflowDAGExecutor()
    dag.add_node(PipelineNode("a", lambda _out: 1, depends_on=("b",)))
    dag.add_node(PipelineNode("b", lambda _out: 2, depends_on=("a",)))
    with pytest.raises(ValueError, match="Cycle"):
        dag.topological_order()
