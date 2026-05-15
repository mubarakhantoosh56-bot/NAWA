"""Text extraction helpers for MVP RAG ingestion."""

import json
from pathlib import Path

RowDict = dict[str, object]

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".pdf", ".docx"}
SUPPORTED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def extract_text(path: str | Path, filename: str, content_type: str) -> RowDict:
    """Extract text and metadata from a supported text-like file."""
    file_path = Path(path)
    extension = Path(filename).suffix.lower()
    normalized_content_type = content_type.strip().lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("unsupported file type")
    if normalized_content_type and normalized_content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValueError("unsupported file type")

    if extension == ".pdf":
        text = _extract_pdf_text(file_path)
    elif extension == ".docx":
        text = _extract_docx_text(file_path)
    else:
        raw_text = _read_text_with_fallback(file_path)
        if extension == ".json":
            text = _normalize_json_text(raw_text)
        else:
            text = raw_text

    return {
        "text": text,
        "metadata": {
            "filename": filename,
            "content_type": normalized_content_type,
            "extension": extension,
            "size_bytes": file_path.stat().st_size,
            "line_count": _count_lines(text),
        },
    }


def _read_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _normalize_json_text(text: str) -> str:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=True)


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        page_text = []
        for page in reader.pages:
            page_text.append(page.extract_text() or "")
        return "\n".join(text for text in page_text if text).strip()
    except Exception as exc:
        raise ValueError("file text extraction failed") from exc


def _extract_docx_text(path: Path) -> str:
    try:
        from docx import Document

        document = Document(str(path))
        blocks = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text for cell in row.cells if cell.text]
                if cells:
                    blocks.append("\t".join(cells))
        return "\n".join(blocks).strip()
    except Exception as exc:
        raise ValueError("file text extraction failed") from exc


def _count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1
