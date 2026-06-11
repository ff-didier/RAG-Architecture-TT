from pathlib import Path

from app.ingestion.pipeline import save_upload


def test_save_upload_writes_file(tmp_path: Path):
    path = save_upload(tmp_path, "demo.pdf", b"content")
    assert path.exists()
    assert path.read_bytes() == b"content"
    assert path.name.endswith("_demo.pdf")
