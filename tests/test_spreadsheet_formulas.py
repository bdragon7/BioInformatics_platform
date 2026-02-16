from bioplatform.gui.data_table import evaluate_formula


def test_formula_arithmetic_with_cell_refs() -> None:
    rows = [
        ["2", "3", "=A1+B1"],
    ]
    assert evaluate_formula(rows, rows[0][2], (0, 2)) == "5.0"


def test_formula_sum_range() -> None:
    rows = [
        ["1", "2"],
        ["3", "4"],
        ["=SUM(A1:B2)", ""],
    ]
    assert evaluate_formula(rows, rows[2][0], (2, 0)) == "10.0"


def test_formula_average_range() -> None:
    rows = [
        ["1", "2"],
        ["3", "4"],
        ["=AVERAGE(A1:B2)", ""],
    ]
    assert evaluate_formula(rows, rows[2][0], (2, 0)) == "2.5"


def test_formula_stddev_range() -> None:
    rows = [
        ["1"],
        ["2"],
        ["3"],
        ["=STDDEV(A1:A3)"],
    ]
    # sample stddev of [1,2,3] is 1
    assert evaluate_formula(rows, rows[3][0], (3, 0)) == "1.0"


def test_formula_sqrt() -> None:
    rows = [["9", "=SQRT(A1)"]]
    assert evaluate_formula(rows, rows[0][1], (0, 1)) == "3.0"


def test_formula_detects_direct_cycle() -> None:
    rows = [["=A1"]]
    assert evaluate_formula(rows, rows[0][0], (0, 0)) == "#CYCLE"


def test_formula_detects_indirect_cycle() -> None:
    rows = [["=B1", "=A1"]]
    assert evaluate_formula(rows, rows[0][0], (0, 0)) == "#CYCLE"


def test_formula_handles_nested_dependency_chain() -> None:
    rows = [["1", "=A1+1", "=B1+1", "=C1+1"]]
    assert evaluate_formula(rows, rows[0][3], (0, 3)) == "4.0"
