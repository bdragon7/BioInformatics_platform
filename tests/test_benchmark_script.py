from pathlib import Path
import subprocess
import sys


def test_benchmark_script_generates_outputs(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(repo / "scripts" / "benchmark_open_source.py")]
    subprocess.run(cmd, cwd=tmp_path, check=True, capture_output=True, text=True)
    assert (tmp_path / "benchmark_results.json").exists()
    md = tmp_path / "BENCHMARK_REPORT.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "Open-Source Benchmark Report" in text
    assert "Reproduce" in text
