from bioplatform.core.metadata import MetadataRecord, MetadataSchemaManager


def test_metadata_validation_duplicate_and_required() -> None:
    mgr = MetadataSchemaManager()
    records = [
        MetadataRecord(sample_id="S1", group="tumour"),
        MetadataRecord(sample_id="S1", group="control"),
        MetadataRecord(sample_id="", group="control"),
    ]
    result = mgr.validate(records)
    assert not result.valid
    assert any("Duplicate sample_id" in e for e in result.errors)


def test_metadata_standardization() -> None:
    mgr = MetadataSchemaManager()
    assert mgr.standardize_category("Tumour") == "tumor"
