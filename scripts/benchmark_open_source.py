from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean as stdlib_mean, median as stdlib_median
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bioplatform.core.analysis_library import AnalysisLibrary
from bioplatform.core.data_cleaning import lof_outliers, smart_sanitize_growth_values


@dataclass(slots=True)
class BenchRow:
    category: str
    function: str
    implementation: str
    seconds: float
    relative_to_fastest: float
    notes: str = ""


def _time_call(fn, iterations: int = 2000) -> float:  # type: ignore[no-untyped-def]
    t0 = perf_counter()
    for _ in range(iterations):
        fn()
    return perf_counter() - t0


def _safe_float(values):  # type: ignore[no-untyped-def]
    return [float(v) for v in values]


def run_benchmarks() -> dict[str, object]:
    lib = AnalysisLibrary()
    numeric = [((i * 37) % 1000) / 17.0 for i in range(1, 500)]
    growth = [0.03, None, 0.07, float("nan"), 0.12, 0.19, None, 0.24, 0.31, float("nan"), 0.42]
    outlier_data = [0.12, 0.13, 0.11, 0.14, 0.15, 3.2, 0.12, 0.14, 0.13, 0.12, 2.9, 0.11, 0.13]

    rows: list[BenchRow] = []
    availability: dict[str, bool] = {}

    # stats benchmarks
    stats_runs = [
        ("BioPlatform", lambda: lib.execute_python("python.stats.mean", numeric)),
        ("stdlib.statistics.mean", lambda: stdlib_mean(numeric)),
    ]
    try:
        import numpy as np  # type: ignore

        availability["numpy"] = True
        arr = np.array(numeric)
        stats_runs.append(("numpy.mean", lambda: float(np.mean(arr))))
    except Exception:
        availability["numpy"] = False

    timing = [(name, _time_call(fn)) for name, fn in stats_runs]
    fastest = min(t for _, t in timing)
    for name, sec in timing:
        rows.append(BenchRow("statistics", "mean", name, sec, sec / fastest))

    med_runs = [
        ("BioPlatform", lambda: lib.execute_python("python.stats.median", numeric)),
        ("stdlib.statistics.median", lambda: stdlib_median(numeric)),
    ]
    if availability.get("numpy"):
        import numpy as np  # type: ignore

        arr = np.array(numeric)
        med_runs.append(("numpy.median", lambda: float(np.median(arr))))
    timing = [(name, _time_call(fn)) for name, fn in med_runs]
    fastest = min(t for _, t in timing)
    for name, sec in timing:
        rows.append(BenchRow("statistics", "median", name, sec, sec / fastest))

    std_runs = [
        ("BioPlatform", lambda: lib.execute_python("python.stats.stddev", numeric)),
    ]
    if availability.get("numpy"):
        import numpy as np  # type: ignore

        arr = np.array(numeric)
        std_runs.append(("numpy.std(ddof=1)", lambda: float(np.std(arr, ddof=1))))
    timing = [(name, _time_call(fn)) for name, fn in std_runs]
    fastest = min(t for _, t in timing)
    for name, sec in timing:
        rows.append(BenchRow("statistics", "stddev", name, sec, sec / fastest))

    # sanitize benchmark
    sanitize_runs = [
        ("BioPlatform.smart_sanitize_growth_values", lambda: smart_sanitize_growth_values(growth).data),
    ]
    try:
        import pandas as pd  # type: ignore

        availability["pandas"] = True

        def pandas_clean():
            s = pd.Series(growth, dtype="float64").ffill().fillna(0.0)
            return _safe_float(s.tolist())

        sanitize_runs.append(("pandas.Series.ffill+fillna", pandas_clean))
    except Exception:
        availability["pandas"] = False

    timing = [(name, _time_call(fn)) for name, fn in sanitize_runs]
    fastest = min(t for _, t in timing)
    for name, sec in timing:
        rows.append(BenchRow("data_cleaning", "growth_sanitize", name, sec, sec / fastest))

    # outlier benchmark
    lof_runs = [("BioPlatform.lof_outliers", lambda: lof_outliers(outlier_data))]
    try:
        from sklearn.neighbors import LocalOutlierFactor  # type: ignore

        availability["sklearn"] = True

        def sklearn_lof():
            model = LocalOutlierFactor(n_neighbors=5)
            labels = model.fit_predict([[v] for v in outlier_data])
            return [i for i, lbl in enumerate(labels) if lbl == -1]

        lof_runs.append(("sklearn.LocalOutlierFactor", sklearn_lof))
    except Exception:
        availability["sklearn"] = False

    timing = [(name, _time_call(fn, iterations=400)) for name, fn in lof_runs]
    fastest = min(t for _, t in timing)
    for name, sec in timing:
        rows.append(BenchRow("outliers", "lof", name, sec, sec / fastest))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "availability": availability,
        "rows": [asdict(r) for r in rows],
    }


def write_markdown(report: dict[str, object], path: Path) -> None:
    rows = report["rows"]
    availability = report["availability"]
    lines = [
        "# Open-Source Benchmark Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Python: {report['python']}",
        f"Platform: {report['platform']}",
        "",
        "## Library availability",
        "",
        f"- numpy: {'yes' if availability.get('numpy') else 'no'}",
        f"- pandas: {'yes' if availability.get('pandas') else 'no'}",
        f"- sklearn: {'yes' if availability.get('sklearn') else 'no'}",
        "",
        "> Note: benchmark comparisons include the strongest available open-source implementation in this environment.",
        "",
        "## Results",
        "",
        "| Category | Function | Implementation | Seconds | Relative to fastest |",
        "|---|---|---|---:|---:|",
    ]
    for row in rows:  # type: ignore[assignment]
        lines.append(
            f"| {row['category']} | {row['function']} | {row['implementation']} | {row['seconds']:.6f} | {row['relative_to_fastest']:.2f}x |"
        )

    lines.extend([
        "",
        "## Reproduce",
        "",
        "```bash",
        "python scripts/benchmark_open_source.py",
        "```",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run_benchmarks()
    out_json = Path("benchmark_results.json")
    out_md = Path("BENCHMARK_REPORT.md")
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, out_md)
    print(f"Wrote {out_json} and {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
