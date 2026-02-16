from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .analysis_library import AnalysisLibrary
from .data_cleaning import lof_outliers, smart_sanitize_growth_values
from .runtime import HardwareAbstractionLayer


@dataclass(slots=True)
class PipelineResult:
    cleaned: list[float]
    stats: dict[str, float]
    outliers: list[int]
    figure: object | None
    backend: str = "cpu"


class PythonRPipelineEngine:
    """Hybrid automation engine chaining clean -> stats -> outliers -> figure."""

    def __init__(self, analysis_library: AnalysisLibrary | None = None) -> None:
        self.analysis_library = analysis_library or AnalysisLibrary()
        self.hal = HardwareAbstractionLayer()

    def run_growth_pipeline(self, raw_values: list[float | None]) -> PipelineResult:
        sanitized = smart_sanitize_growth_values(raw_values)
        cleaned = [float(v) for v in sanitized.data]

        stats, backend = self._compute_stats(cleaned)
        outliers = self._accelerated_outliers(cleaned)
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
