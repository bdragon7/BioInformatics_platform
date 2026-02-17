from bioplatform.core.error_handling import WorkplaceErrorHandler


def test_workplace_error_handler_formats_actionable_message() -> None:
    handler = WorkplaceErrorHandler()
    text = handler.to_plaintext("FILE_NOT_FOUND", filename="missing.csv")
    assert "File Not Found" in text
    assert "missing.csv" in text
    assert "How to fix it" in text


def test_support_snapshot_contains_context() -> None:
    handler = WorkplaceErrorHandler()
    payload = handler.support_snapshot({"feature": "pipeline"})
    assert "pipeline" in payload
    assert "platform" in payload
