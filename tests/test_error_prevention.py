from bioplatform.core.error_prevention import AnalysisGuardrails, SpreadsheetValueGuard


def test_recommendation_prefers_normalization() -> None:
    guard = AnalysisGuardrails()
    checklist = guard.build_checklist(
        normalized=False,
        batch_effect_addressed=True,
        outliers_reviewed=True,
        sample_size_ok=True,
        assumptions_met=True,
    )
    assert "normalization" in guard.recommendation(checklist).lower()


def test_spreadsheet_value_guard_blocks_negative_concentration() -> None:
    guard = SpreadsheetValueGuard()
    ok, message = guard.validate("Concentration (mM)", "-1")
    assert ok is False
    assert "cannot be negative" in message.lower()
