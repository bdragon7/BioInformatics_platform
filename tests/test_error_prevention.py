from bioplatform.core.error_prevention import AnalysisGuardrails


def test_checklist_recommendation() -> None:
    g = AnalysisGuardrails()
    checklist = g.build_checklist(
        normalized=False,
        batch_effect_addressed=True,
        outliers_reviewed=True,
        sample_size_ok=True,
        assumptions_met=True,
    )
    assert g.recommendation(checklist).startswith("Apply normalization")
