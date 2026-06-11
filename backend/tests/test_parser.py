from pathlib import Path

import pytest

from app.ingestion.parser import UnsupportedFileTypeError, parse_document


def test_parse_docx(sample_docx: Path):
    text = parse_document(sample_docx)
    assert "Hybrid search" in text


def test_parse_pdf(sample_pdf: Path):
    text = parse_document(sample_pdf)
    assert isinstance(text, str)


def test_unsupported_type(tmp_path: Path):
    bad = tmp_path / "notes.txt"
    bad.write_text("plain text")
    with pytest.raises(UnsupportedFileTypeError):
        parse_document(bad)
