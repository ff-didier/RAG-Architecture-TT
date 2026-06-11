from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    pass


def parse_document(file_path: Path, mime_type: str | None = None) -> str:
    suffix = file_path.suffix.lower()
    mime = (mime_type or "").lower()

    if suffix == ".pdf" or "pdf" in mime:
        return _parse_pdf(file_path)
    if suffix == ".docx" or "wordprocessingml" in mime:
        return _parse_docx(file_path)
    raise UnsupportedFileTypeError(f"Unsupported file type: {suffix or mime}")


def _parse_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def _parse_docx(file_path: Path) -> str:
    doc = DocxDocument(str(file_path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs).strip()
