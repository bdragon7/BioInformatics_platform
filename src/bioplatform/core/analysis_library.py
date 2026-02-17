from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
from statistics import mean, median
from typing import Callable


@dataclass(slots=True)
class AnalysisFunction:
    func_id: str
    language: str
    domain: str
    title: str
    description: str
    callable_name: str | None = None


class AnalysisLibrary:
    """Curated Python/R analysis-function catalog for bioinformatics workflows."""

    def __init__(self) -> None:
        self._python_functions: dict[str, Callable[[list[float]], float | dict[str, float]]] = {
            "python.stats.mean": lambda xs: mean(xs) if xs else 0.0,
            "python.stats.median": lambda xs: median(xs) if xs else 0.0,
            "python.stats.stddev": self._sample_stddev,
            "python.microbiology.growth_rate": self._growth_rate,
            "python.pharmacology.ic50_logit": self._ic50_logit,
            "python.genomics.gc_content": self._gc_content,
        }

    def catalog(self) -> list[AnalysisFunction]:
        return [
            AnalysisFunction(
                func_id="python.stats.mean",
                language="python",
                domain="bioinformatics",
                title="Mean",
                description="Compute mean over numeric replicates.",
                callable_name="statistics.mean",
            ),
            AnalysisFunction(
                func_id="python.stats.median",
                language="python",
                domain="bioinformatics",
                title="Median",
                description="Compute median over numeric replicates.",
                callable_name="statistics.median",
            ),
            AnalysisFunction(
                func_id="python.stats.stddev",
                language="python",
                domain="bioinformatics",
                title="Sample standard deviation",
                description="Compute sample standard deviation (n-1 denominator).",
                callable_name="analysis_library._sample_stddev",
            ),
            AnalysisFunction(
                func_id="python.microbiology.growth_rate",
                language="python",
                domain="microbiology",
                title="Growth rate (mu)",
                description="Estimate μ from two-point OD values.",
                callable_name="analysis_library._growth_rate",
            ),
            AnalysisFunction(
                func_id="python.pharmacology.ic50_logit",
                language="python",
                domain="pharmacology",
                title="IC50 approximation",
                description="Approximate IC50 from logistic-like dose-response points.",
                callable_name="analysis_library._ic50_logit",
            ),
            AnalysisFunction(
                func_id="python.genomics.gc_content",
                language="python",
                domain="genomics",
                title="GC content",
                description="Compute GC% from ASCII base counts encoded as [G,C,total].",
                callable_name="analysis_library._gc_content",
            ),
            AnalysisFunction(
                func_id="r.deseq2.differential_expression",
                language="r",
                domain="genomics",
                title="DESeq2 differential expression",
                description="Template for DESeq2 count matrix differential expression.",
            ),
            AnalysisFunction(
                func_id="r.limma.batch_correction",
                language="r",
                domain="bioinformatics",
                title="limma batch correction",
                description="Template using limma::removeBatchEffect.",
            ),
            AnalysisFunction(
                func_id="r.cobrapy.metabolic_flux",
                language="python",
                domain="microbiology",
                title="COBRApy flux balance",
                description="Template for COBRApy model optimization in Python runtime.",
            ),
            AnalysisFunction(
                func_id="r.nls.growth_curve",
                language="r",
                domain="microbiology",
                title="Growth curve nls fit",
                description="Template for microbial growth fit via R nls().",
            ),
        ]

    def catalog_by_domain(self, domain: str) -> list[AnalysisFunction]:
        key = domain.strip().lower()
        return [item for item in self.catalog() if item.domain == key]

    def execute_python(self, func_id: str, values: list[float]) -> float | dict[str, float]:
        if func_id not in self._python_functions:
            raise ValueError(f"Unknown Python analysis function: {func_id}")
        return self._python_functions[func_id](values)

    def r_template(self, func_id: str) -> str:
        templates = {
            "r.deseq2.differential_expression": (
                "library(DESeq2)\n"
                "dds <- DESeqDataSetFromMatrix(countData=counts, colData=meta, design=~condition)\n"
                "dds <- DESeq(dds)\n"
                "res <- results(dds)\n"
                "write.csv(as.data.frame(res), 'deseq2_results.csv')\n"
            ),
            "r.limma.batch_correction": (
                "library(limma)\n"
                "expr_bc <- removeBatchEffect(expr, batch=batch, design=design)\n"
                "write.csv(expr_bc, 'batch_corrected.csv')\n"
            ),
            "r.nls.growth_curve": (
                "fit <- nls(od ~ K/(1+exp((4*mu/K)*(lambda-t)+2)), data=df,\n"
                "           start=list(K=1, mu=0.3, lambda=2))\n"
                "summary(fit)\n"
            ),
            "r.cobrapy.metabolic_flux": (
                "# Python template:\n"
                "from cobra.io import load_json_model\n"
                "model = load_json_model('model.json')\n"
                "solution = model.optimize()\n"
                "print(solution.objective_value)\n"
            ),
        }
        if func_id not in templates:
            raise ValueError(f"No template available for: {func_id}")
        return templates[func_id]

    @staticmethod
    def _sample_stddev(values: list[float]) -> float:
        if len(values) <= 1:
            return 0.0
        avg = sum(values) / len(values)
        return ((sum((v - avg) ** 2 for v in values)) / (len(values) - 1)) ** 0.5

    @staticmethod
    def _growth_rate(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        y0 = max(values[0], 1e-6)
        y1 = max(values[1], 1e-6)
        return log(y1 / y0)

    @staticmethod
    def _ic50_logit(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        low = min(values)
        high = max(values)
        mid = (low + high) / 2
        return 1 / (1 + exp(-mid))

    @staticmethod
    def _gc_content(values: list[float]) -> float:
        if len(values) < 3:
            return 0.0
        g, c, total = values[0], values[1], max(values[2], 1e-9)
        return ((g + c) / total) * 100
