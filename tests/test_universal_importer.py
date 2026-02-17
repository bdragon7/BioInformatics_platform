from pathlib import Path

from bioplatform.data.universal_importer import UniversalDataImporter


def test_universal_importer_can_import_extensions() -> None:
    imp = UniversalDataImporter()
    assert imp.can_import(Path("x.csv"))
    assert imp.can_import(Path("x.xlsx"))
    assert not imp.can_import(Path("x.docx"))


def test_universal_importer_csv_fallback_without_pandas(tmp_path: Path) -> None:
    p = tmp_path / "demo.csv"
    p.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    imp = UniversalDataImporter()
    ok, data, msg = imp._fallback_import_without_pandas(p)
    assert ok is True
    assert len(data) == 2
    assert "fallback" in msg.lower()
