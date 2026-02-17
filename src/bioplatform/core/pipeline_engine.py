from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import csv
from dataclasses import dataclass
import json
from statistics import correlation
from pathlib import Path
from typing import Callable

from .analysis_library import AnalysisLibrary
from .data_cleaning import lof_outliers, smart_sanitize_growth_values
from .runtime import HardwareAbstractionLayer
from ..visualization.editor_state import GraphEditorState, GraphElement


def infer_numeric_series(records: list[dict[str, object]]) -> list[float]:
    """Auto-map first usable numeric column from row dictionaries."""
    if not records:
        return []
    keys = list(records[0].keys())
    for key in keys:
        values: list[float] = []
        numeric_hits = 0
        for row in records:
            raw = row.get(key, 0.0)
            try:
                num = float(raw)
                numeric_hits += 1
            except Exception:
                num = 0.0
            values.append(num)
        if numeric_hits > 0:
            return values
    return [0.0 for _ in records]




@dataclass(slots=True)
class PipelineResult:
    cleaned: list[float]
    stats: dict[str, float]
    outliers: list[int]
    figure: object | None
    backend: str = "cpu"


@dataclass(slots=True)
class PlotSuggestion:
    name: str
    rationale: str
    advanced: bool = False



class PythonRPipelineEngine:
    """Hybrid automation engine chaining clean -> stats -> outliers -> figure."""

    def __init__(self, analysis_library: AnalysisLibrary | None = None) -> None:
        self.analysis_library = analysis_library or AnalysisLibrary()
        self.hal = HardwareAbstractionLayer()
        self.graph_editor_state = GraphEditorState()
        self.graph_editor_state.upsert(GraphElement(id="pipeline-series", kind="line", properties={"line_width": 2, "symbol": "o"}))

    def load_values_from_file(self, path: Path) -> list[float]:
        """Read CSV/JSON and infer a numeric series without manual mapping."""
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            return infer_numeric_series(rows)
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                if payload and isinstance(payload[0], dict):
                    return infer_numeric_series(payload)
                return [float(x or 0.0) for x in payload]
            if isinstance(payload, dict):
                records = payload.get("rows")
                if isinstance(records, list) and records and isinstance(records[0], dict):
                    return infer_numeric_series(records)
            raise ValueError("Unsupported JSON structure. Expected list of numbers or list of objects.")
        raise ValueError(f"Unsupported file type: {suffix}")

    def run_growth_pipeline(self, raw_values: list[float | None]) -> PipelineResult:
        sanitized = smart_sanitize_growth_values(raw_values)
        cleaned = [float(v) for v in sanitized.data]

        stats, backend = self._compute_stats(cleaned)
        outliers = self._accelerated_outliers(cleaned)
        self.graph_editor_state.set_property("pipeline-series", "last_outlier_count", len(outliers))
        fig = self._build_editable_figure(cleaned, outliers)
        return PipelineResult(cleaned=cleaned, stats=stats, outliers=outliers, figure=fig, backend=backend)

    def run_growth_pipeline_stream(
        self,
        batches: list[list[float | None]],
        prefetch_next: Callable[[int], list[float | None] | None] | None = None,
    ) -> list[PipelineResult]:
        """Process batches while prefetching next batch on CPU thread.

        This keeps CPU I/O active while current compute job executes.
        """
        if not batches:
            return []

        results: list[PipelineResult] = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            pending: Future[list[float | None] | None] | None = None
            for idx, batch in enumerate(batches):
                if prefetch_next is not None:
                    pending = executor.submit(prefetch_next, idx)

                results.append(self.run_growth_pipeline(batch))

                if pending is not None:
                    try:
                        prefetched = pending.result(timeout=5)
                        if prefetched:
                            batches.append(prefetched)
                    except Exception:
                        pass
                    finally:
                        pending = None
        return results


    def interactive_plot_payload(self, cleaned: list[float], outliers: list[int]) -> dict[str, object]:
        """Return Canvas-X payload linked to GraphEditorState for undo/redo."""
        style = self.graph_editor_state.elements["pipeline-series"].properties
        suggestions = [
            {"name": s.name, "rationale": s.rationale, "advanced": s.advanced}
            for s in self.suggest_insightful_plot_types(cleaned)
        ]
        return {
            "x": list(range(len(cleaned))),
            "y": cleaned,
            "outliers": outliers,
            "style": dict(style),
            "editor_undo_depth": len(self.graph_editor_state._undo),
            "suggestions": suggestions,
            "style_guide": self.world_class_plot_style_guide(),
        }

    def suggest_insightful_plot_types(self, cleaned: list[float]) -> list[PlotSuggestion]:
        """Return three ranked plot ideas (including one advanced/custom view)."""
        if not cleaned:
            return [
                PlotSuggestion("Line trend", "Best baseline for sparse sequential data."),
                PlotSuggestion("Distribution histogram", "Shows spread and central tendency quickly."),
                PlotSuggestion(
                    "Residual control map",
                    "Advanced: overlays deviation zones for anomaly localization once data arrives.",
                    advanced=True,
                ),
            ]

        n = len(cleaned)
        spread = max(cleaned) - min(cleaned)
        trend_strength = 0.0
        if n > 2:
            try:
                x = list(range(n))
                trend_strength = abs(float(correlation(x, cleaned)))
            except Exception:
                trend_strength = 0.0

        first = PlotSuggestion(
            "Annotated trend line",
            "Highlights progression over time with direct labels and outlier overlays.",
        )
        second = PlotSuggestion(
            "Distribution + target-zone band",
            "Reveals variance and whether observations remain within operating bounds.",
        )
        advanced_text = "Advanced: mini-map + linked residual heat-strip for fast outlier navigation."
        if trend_strength < 0.35 and spread > 0:
            first = PlotSuggestion(
                "Change-point sparkline",
                "Weak linear trend detected; change-point view better reveals regime shifts.",
            )
        if n >= 50:
            second = PlotSuggestion(
                "Hex-binned density trend",
                "Large series benefits from density view to reduce overplotting.",
            )
        return [
            first,
            second,
            PlotSuggestion("Residual navigator map", advanced_text, advanced=True),
        ]

    @staticmethod
    def world_class_plot_style_guide() -> dict[str, object]:
        return {
            "palette": ["#2E5A88", "#A93226", "#38BDF8", "#0F172A"],
            "font_family": "Helvetica, Roboto, Arial, sans-serif",
            "grid_alpha": 0.12,
            "remove_spines": ["top", "right"],
            "target_zone_alpha": 0.08,
            "direct_label": True,
        }

    def export_figure_high_quality(self, figure: object | None, output_base: Path) -> dict[str, str]:
        if figure is None:
            return {}
        paths: dict[str, str] = {}
        output_base.parent.mkdir(parents=True, exist_ok=True)
        png = output_base.with_suffix(".png")
        svg = output_base.with_suffix(".svg")
        pdf = output_base.with_suffix(".pdf")

        figure.savefig(png, dpi=600, bbox_inches="tight")
        figure.savefig(svg, bbox_inches="tight")
        figure.savefig(pdf, bbox_inches="tight")

        paths["png"] = str(png)
        paths["svg"] = str(svg)
        paths["pdf"] = str(pdf)
        return paths

    def r_pipeline_template(self) -> str:
        return (
            "# R pipeline template: clean -> stats -> figure\n"
            "library(ggplot2)\n"
            "df <- data.frame(value=values)\n"
            "df <- df[!is.na(df$value), ]\n"
            "stats <- data.frame(mean=mean(df$value), median=median(df$value), sd=sd(df$value))\n"
            "p <- ggplot(df, aes(x=seq_along(value), y=value)) + geom_line() + geom_point()\n"
            "ggsave('pipeline_plot.svg', p, width=10, height=6, dpi=600)\n"
            "write.csv(stats, 'pipeline_stats.csv', row.names=FALSE)\n"
        )

    def _compute_stats(self, cleaned: list[float]) -> tuple[dict[str, float], str]:
        ctx = self.hal.detect()

        if len(cleaned) >= 100_000 and ctx.backend in {"torch-cuda", "cupy"}:
            try:
                if ctx.backend == "torch-cuda":
                    import torch  # type: ignore

                    tensor = torch.tensor(cleaned, dtype=torch.float32, device="cuda", pin_memory=False)
                    mean_v = float(tensor.mean().item())
                    median_v = float(tensor.median().item())
                    std_v = float(tensor.std(unbiased=False).item())
                else:
                    import cupy as cp  # type: ignore

                    arr = cp.asarray(cleaned, dtype=cp.float32)
                    mean_v = float(cp.mean(arr).get())
                    median_v = float(cp.median(arr).get())
                    std_v = float(cp.std(arr).get())
                return (
                    {
                        "mean": mean_v,
                        "median": median_v,
                        "stddev": std_v,
                        "min": min(cleaned) if cleaned else 0.0,
                        "max": max(cleaned) if cleaned else 0.0,
                    },
                    ctx.backend,
                )
            except Exception:
                pass

        mean_v = float(self.analysis_library.execute_python("python.stats.mean", cleaned))
        median_v = float(self.analysis_library.execute_python("python.stats.median", cleaned))
        std_v = float(self.analysis_library.execute_python("python.stats.stddev", cleaned))
        return (
            {
                "mean": mean_v,
                "median": median_v,
                "stddev": std_v,
                "min": min(cleaned) if cleaned else 0.0,
                "max": max(cleaned) if cleaned else 0.0,
            },
            "cpu",
        )

    def _accelerated_outliers(self, cleaned: list[float]) -> list[int]:
        """Best-effort accelerated outlier detector with robust fallback."""
        ctx = self.hal.detect()
        if len(cleaned) >= 100_000 and ctx.backend == "torch-cuda":
            try:
                import torch  # type: ignore

                x = torch.tensor(cleaned, dtype=torch.float32, device="cuda")
                mean = x.mean()
                sd = x.std(unbiased=False)
                z = torch.abs((x - mean) / torch.clamp(sd, min=1e-6))
                idx = torch.where(z > 2.5)[0].tolist()
                return [int(i) for i in idx]
            except Exception:
                pass
        return lof_outliers(cleaned)

    @staticmethod
    def _build_editable_figure(values: list[float], outliers: list[int]) -> object | None:
        try:
            import matplotlib.pyplot as plt  # type: ignore
        except Exception:
            return None

        fig, ax = plt.subplots(figsize=(10, 6), dpi=170)
        x = list(range(1, len(values) + 1))
        line_color = "#2E5A88"
        accent_color = "#A93226"
        ax.plot(x, values, marker="o", markersize=4.2, linewidth=2.0, color=line_color)

        if values:
            mean_v = sum(values) / len(values)
            std_v = (sum((v - mean_v) ** 2 for v in values) / max(len(values), 1)) ** 0.5
            low = mean_v - std_v
            high = mean_v + std_v
            ax.axhspan(low, high, color="#38BDF8", alpha=0.08)
            ax.axhline(mean_v, color="#94A3B8", linewidth=1.0, linestyle="--", alpha=0.7)
            ax.text(x[-1], values[-1], "  Signal", va="center", color=line_color, fontsize=9)

        if outliers:
            ox = [x[i] for i in outliers if 0 <= i < len(x)]
            oy = [values[i] for i in outliers if 0 <= i < len(values)]
            if ox and oy:
                ax.scatter(ox, oy, color=accent_color, s=65, zorder=4)
                for px, py in zip(ox[:3], oy[:3]):
                    ax.annotate("outlier", (px, py), textcoords="offset points", xytext=(6, 6), fontsize=8, color=accent_color)

        ax.set_title("Automated Analysis Pipeline", loc="left", fontsize=13, fontweight="bold")
        ax.set_xlabel("Sample")
        ax.set_ylabel("Value")
        ax.grid(alpha=0.12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        return fig
