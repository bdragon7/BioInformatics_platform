from pathlib import Path
from bioplatform.core.feature_audit import FeatureAudit


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = FeatureAudit(root).generate_audit_report()
    (root / "FEATURE_AUDIT_REPORT.md").write_text(report, encoding="utf-8")
    print("Generated FEATURE_AUDIT_REPORT.md")
