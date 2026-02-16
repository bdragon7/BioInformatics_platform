from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analysis_library import AnalysisLibrary
from .data_cleaning import lof_outliers, smart_sanitize_growth_values


@dataclass(slots=True)
class PipelineResult:
    cleaned: list[float]
    stats: dict[str, float]
    outliers: list[int]
    figure: object | None


class PythonRPipelineEngine:
    """Simple automation engine chaining clean -> stats -> figure (+ optional R template)."""

    def __init__(self, analysis_library: AnalysisLibrary | None = None) -> None:
        self.analysis_library = analysis_library or AnalysisLibrary()

    def run_growth_pipeline(self, raw_values: list[float | None]) -> PipelineResult:
        sanitized = smart_sanitize_growth_values(raw_values)
        cleaned = [float(v) for v in sanitized.data]

        mean_v = float(self.analysis_library.execute_python("python.stats.mean", cleaned))
        median_v = float(self.analysis_library.execute_python("python.stats.median", cleaned))
        std_v = float(self.analysis_library.execute_python("python.stats.stddev", cleaned))

        stats = {
            "mean": mean_v,
            "median": median_v,
            "stddev": std_v,
            "min": min(cleaned) if cleaned else 0.0,
            "max": max(cleaned) if cleaned else 0.0,
        }
        outliers = lof_outliers(cleaned)
        fig = self._build_editable_figure(cleaned, outliers)
        return PipelineResult(cleaned=cleaned, stats=stats, outliers=outliers, figure=fig)

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

    @staticmethod
    def _build_editable_figure(values: list[float], outliers: list[int]) -> object | None:
        try:
            import matplotlib.pyplot as plt  # type: ignore
        except Exception:
            return None

        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        x = list(range(1, len(values) + 1))
        ax.plot(x, values, marker="o", linewidth=1.8, label="Signal")
        if outliers:
            ox = [x[i] for i in outliers if 0 <= i < len(x)]
            oy = [values[i] for i in outliers if 0 <= i < len(values)]
            if ox and oy:
                ax.scatter(ox, oy, color="#dc2626", s=60, label="Outliers", zorder=3)
        ax.set_title("Automated Analysis Pipeline")
        ax.set_xlabel("Sample")
        ax.set_ylabel("Value")
        ax.grid(alpha=0.25)
        ax.legend()
        return fig
