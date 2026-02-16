from IsoDesign_Ultra.chem.informatics import FormulationValidator, qsar_live_feedback, smiles_to_feature_tensor
from IsoDesign_Ultra.data.bridge import DataBuffer, r_interop


def test_smiles_tensor_and_validator() -> None:
    tensor = smiles_to_feature_tensor(["CCO", "NCCO"])
    assert len(tensor) == 2
    assert len(tensor[0]) >= 8
    validator = FormulationValidator()
    res = validator.assess("CCO", "NCCO", ratio=1.0)
    assert res.risk in {"low", "moderate", "high"}


def test_data_buffer_arrow_roundtrip() -> None:
    buf = DataBuffer()
    payload = {"a": [1, 2], "b": [3, 4]}
    buf.put("x", payload)
    table = buf.to_arrow("x")
    df2 = buf.from_arrow("y", table)
    if hasattr(df2, "columns"):
        assert list(df2.columns) == ["a", "b"]
    else:
        assert set(df2.keys()) == {"a", "b"}


def test_r_interop_decorator_fallback_works() -> None:
    @r_interop
    def consume(obj):
        return obj

    data = {"a": [1]}
    out = consume(data)
    assert out == data


def test_qsar_live_feedback_payload() -> None:
    payload = qsar_live_feedback(["CCO", "NCCO"], [-24000.0, -18000.0])
    assert len(payload) == 2
    assert payload[0]["highlight_intensity"] >= payload[1]["highlight_intensity"]
    assert payload[0]["state_label"] in {"high-affinity", "mid-affinity", "low-affinity"}
