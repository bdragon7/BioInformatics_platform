from IsoDesign_Ultra.engine.doe import AutoDoE


def test_auto_doe_suggest_next_shape() -> None:
    doe = AutoDoE(
        {
            "variables": [
                {"name": "pH", "vtype": "continuous", "lower": 5.0, "upper": 9.0},
                {"name": "temperature", "vtype": "integer", "lower": 20, "upper": 40},
                {"name": "organism", "vtype": "categorical", "choices": ["E. coli", "S. aureus"]},
            ]
        }
    )
    points = doe.suggest_next(3)
    assert len(points) == 3
    assert all("pH" in p and "temperature" in p and "organism" in p for p in points)
