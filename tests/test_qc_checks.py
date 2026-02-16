from bioplatform.core.qc_checks import detect_outliers, detect_sample_mixup_by_correlation, qc_traffic_light


def test_outlier_detection() -> None:
    flags = detect_outliers({"s1": 1.0, "s2": 1.2, "s3": 1.1, "s4": 10.0}, z_threshold=1.4)
    assert any("Outlier" in f.issue for f in flags)


def test_mixup_detection_and_traffic_light() -> None:
    groups = {"a": "control", "b": "control", "c": "treated"}
    corr = {
        "a": {"b": 0.1, "c": 0.95},
        "b": {"a": 0.1, "c": 0.2},
        "c": {"a": 0.95, "b": 0.2},
    }
    flags = detect_sample_mixup_by_correlation(groups, corr, threshold=0.9)
    assert flags
    assert qc_traffic_light(flags) == "red"
