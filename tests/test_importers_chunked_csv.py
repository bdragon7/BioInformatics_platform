from pathlib import Path

from bioplatform.io.importers import ChunkedCSVReader


def test_chunked_csv_reader_reads_all_rows_and_reports_progress(tmp_path: Path) -> None:
    path = tmp_path / "big.csv"
    path.write_text("x,y\n" + "\n".join(f"{i},{i+1}" for i in range(105)), encoding="utf-8")

    marks: list[int] = []
    frame = ChunkedCSVReader().read_csv(path, chunk_size=20, progress=marks.append)

    assert len(frame) == 105
    assert marks
    assert marks[-1] == 105
