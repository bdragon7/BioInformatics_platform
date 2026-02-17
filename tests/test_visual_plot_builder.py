from bioplatform.plotting.visual_plot_builder import (
    PlotConfiguration,
    PlotType,
    explain_plot_error,
    generate_matplotlib_code,
    suggest_plot_solutions,
)


def test_generate_matplotlib_code_scatter_has_core_lines() -> None:
    config = PlotConfiguration(
        plot_type=PlotType.SCATTER,
        data_source="demo.csv",
        x_column="time",
        y_column="signal",
        title="Demo",
    )
    code = generate_matplotlib_code(config)
    assert "pd.read_csv('demo.csv')" in code
    assert "ax.scatter(" in code
    assert "ax.set_title('Demo')" in code


def test_generate_matplotlib_code_volcano_contains_threshold_guides() -> None:
    config = PlotConfiguration(plot_type=PlotType.VOLCANO)
    code = generate_matplotlib_code(config)
    assert "log2fc" in code
    assert "np.log10(0.05)" in code


def test_error_explanation_and_solutions_are_contextual() -> None:
    exc = KeyError("missing")
    explanation = explain_plot_error(exc)
    solutions = suggest_plot_solutions(exc)
    assert "missing" in explanation.lower() or "column" in explanation.lower()
    assert len(solutions) >= 2
