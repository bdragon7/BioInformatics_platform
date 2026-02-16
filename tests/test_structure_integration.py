from bioplatform.core.structure_integration import alphafold_prediction_url, detect_pymol


def test_alphafold_prediction_url() -> None:
    assert alphafold_prediction_url("p69905").endswith("/entry/P69905")


def test_alphafold_prediction_url_requires_value() -> None:
    try:
        alphafold_prediction_url("  ")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty UniProt ID")


def test_detect_pymol_returns_status() -> None:
    status = detect_pymol()
    assert isinstance(status.available, bool)
    assert isinstance(status.message, str)
