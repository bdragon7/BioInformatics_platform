from bioplatform.core.provenance import ProvenanceRecord, hash_dataset


def test_hash_dataset_is_deterministic() -> None:
    h1 = hash_dataset([1.0, 2.0, 3.0])
    h2 = hash_dataset([1.0, 2.0, 3.0])
    assert h1 == h2


def test_provenance_to_dict_contains_required_fields() -> None:
    rec = ProvenanceRecord(
        dataset_sha256="abc",
        parameters={"a": 1},
        units={"value": "a.u."},
        software_version="0.1.0",
        git_commit="deadbeef",
        random_seed=7,
        deterministic=True,
    )
    payload = rec.to_dict()
    assert payload["dataset_sha256"] == "abc"
    assert payload["deterministic"] is True
