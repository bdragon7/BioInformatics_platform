from bioplatform.core.data_cleaning import (
    lof_outliers,
    smart_sanitize_growth_values,
    smart_sanitize_sequence,
    universal_result,
)


def test_sanitize_sequence_replaces_unknown_bases() -> None:
    result = smart_sanitize_sequence("ACGTXYZ")
    assert result.data == "ACGTNNN"
    assert result.warnings


def test_sanitize_growth_values_repairs_missing() -> None:
    result = smart_sanitize_growth_values([0.1, None, 0.3])
    assert result.data == [0.1, 0.1, 0.3]
    assert result.warnings


def test_lof_outliers_returns_indices() -> None:
    outliers = lof_outliers([0.1, 0.11, 0.09, 0.12, 1.5])
    assert isinstance(outliers, list)


def test_universal_result_shape() -> None:
    out = universal_result(data={"ok": True}, outliers=[1, 2], source="unit")
    assert set(out.keys()) == {"data", "plots", "outliers", "meta"}
    assert out["outliers"] == [1, 2]
