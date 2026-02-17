from pathlib import Path

from bioplatform.core.feature_audit import FeatureAudit


def test_feature_audit_generates_structured_report() -> None:
    audit = FeatureAudit(Path.cwd())
    report = audit.generate_audit_report()
    assert "# FEATURE_AUDIT_REPORT" in report
    assert "Core Features" in report
    assert "Project creation and management" in report


def test_workflow_dag_marked_working() -> None:
    audit = FeatureAudit(Path.cwd())
    result = audit.audit_feature("Workflow DAG builder")
    assert result.works is True
