from pathlib import Path

from bioplatform.validation import BenchmarkingSuite


def test_benchmarking_suite_runs_and_summarizes(tmp_path: Path) -> None:
    suite = BenchmarkingSuite(tmp_path)
    results = suite.benchmark_differential_expression()
    assert results
    summary = suite.summarize(results)
    assert summary["accuracy_mean"] > 0
    assert summary["runtime_mean_s"] > 0


def test_validation_report_written(tmp_path: Path) -> None:
    suite = BenchmarkingSuite(tmp_path)
    results = suite.benchmark_differential_expression()
    report = suite.write_validation_report(results)
    assert report.exists()
    assert (tmp_path / "validation_report.json").exists()
    content = report.read_text(encoding="utf-8")
    assert "Validation Report" in content
    assert "Detailed Results" in content
