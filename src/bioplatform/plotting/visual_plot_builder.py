from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PlotType(Enum):
    SCATTER = "scatter"
    LINE = "line"
    BAR = "bar"
    VOLCANO = "volcano"
    GROWTH_CURVE = "growth_curve"
    DOSE_RESPONSE = "dose_response"


@dataclass(slots=True)
class PlotConfiguration:
    plot_type: PlotType = PlotType.SCATTER
    data_source: str = "dataset.csv"
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: str = "Untitled Plot"
    x_label: str = ""
    y_label: str = ""
    color_palette: str = "viridis"
    marker_size: int = 6
    line_width: float = 1.5
    transparency: float = 0.8
    show_trendline: bool = False
    figure_size: tuple[int, int] = (10, 6)
    dpi: int = 300
    legend_position: str = "best"
    output_path: Optional[str] = None


def generate_matplotlib_code(config: PlotConfiguration) -> str:
    x_col = config.x_column or "x"
    y_col = config.y_column or "y"
    output = config.output_path or "plot.png"
    code: list[str] = [
        "import matplotlib.pyplot as plt",
        "import pandas as pd",
        "import numpy as np",
        "",
        f"df = pd.read_csv('{config.data_source}')",
        f"fig, ax = plt.subplots(figsize={config.figure_size}, dpi={config.dpi})",
        "",
    ]
    if config.plot_type == PlotType.SCATTER:
        code.extend(
            [
                "ax.scatter(",
                f"    df['{x_col}'],",
                f"    df['{y_col}'],",
                f"    s={config.marker_size * 10},",
                f"    alpha={config.transparency},",
                f"    cmap='{config.color_palette}',",
                ")",
            ]
        )
    elif config.plot_type == PlotType.LINE:
        code.extend(
            [
                f"ax.plot(df['{x_col}'], df['{y_col}'], linewidth={config.line_width})",
            ]
        )
    elif config.plot_type == PlotType.BAR:
        code.extend([f"ax.bar(df['{x_col}'], df['{y_col}'], alpha={config.transparency})"])
    elif config.plot_type == PlotType.VOLCANO:
        code.extend(
            [
                "# expects columns: log2fc and pvalue",
                "ax.scatter(df['log2fc'], -np.log10(df['pvalue']), alpha=0.7)",
                "ax.axvline(-1, linestyle='--', linewidth=1)",
                "ax.axvline(1, linestyle='--', linewidth=1)",
                "ax.axhline(-np.log10(0.05), linestyle='--', linewidth=1)",
            ]
        )
    elif config.plot_type == PlotType.GROWTH_CURVE:
        code.extend(
            [
                f"ax.plot(df['{x_col}'], df['{y_col}'], marker='o', linewidth={config.line_width})",
                "ax.set_ylabel('OD600')",
            ]
        )
    elif config.plot_type == PlotType.DOSE_RESPONSE:
        code.extend(
            [
                f"ax.semilogx(df['{x_col}'], df['{y_col}'], marker='o')",
                "ax.set_xlabel('Dose')",
            ]
        )

    if config.show_trendline and config.plot_type in {PlotType.SCATTER, PlotType.LINE}:
        code.extend(
            [
                "coef = np.polyfit(df['%s'], df['%s'], 1)" % (x_col, y_col),
                "trend = np.poly1d(coef)",
                "ax.plot(df['%s'], trend(df['%s']), '--', linewidth=1.2)" % (x_col, x_col),
            ]
        )

    code.extend(
        [
            f"ax.set_xlabel('{config.x_label}')",
            f"ax.set_ylabel('{config.y_label}')",
            f"ax.set_title('{config.title}')",
            f"ax.legend(loc='{config.legend_position}')",
            "plt.tight_layout()",
            f"plt.savefig('{output}', dpi={config.dpi}, bbox_inches='tight')",
            "plt.show()",
        ]
    )
    return "\n".join(code)


def explain_plot_error(error: Exception) -> str:
    error_type = type(error).__name__
    msg = str(error)
    if error_type == "KeyError":
        return "A required column is missing from the selected dataset."
    if error_type == "ValueError" and "convert" in msg.lower():
        return "A numeric axis contains text values. Clean or convert the column before plotting."
    if error_type == "MemoryError":
        return "The current plot size exceeds available memory. Reduce rows or DPI and try again."
    if error_type in {"ImportError", "ModuleNotFoundError"}:
        return "A plotting dependency is missing in the environment."
    return f"Unexpected plotting error: {msg}"


def suggest_plot_solutions(error: Exception) -> list[str]:
    error_type = type(error).__name__
    if error_type == "KeyError":
        return [
            "Check the Data Source preview for exact column names.",
            "Map X/Y columns again in the Plot Builder panel.",
        ]
    if error_type == "ValueError":
        return [
            "Run Data Cleaning to coerce numeric columns.",
            "Filter missing/invalid rows before generating the plot.",
        ]
    if error_type == "MemoryError":
        return [
            "Downsample the dataset for preview mode.",
            "Lower export DPI from 300 to 150.",
        ]
    return [
        "Open Runtime Status and inspect logs.",
        "Retry with a simpler plot type to isolate the issue.",
    ]
