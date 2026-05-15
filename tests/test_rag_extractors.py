from pathlib import Path

import pytest

from app.services.rag.extractors import extract_text


def _pdf_bytes(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Length {len(f'BT /F1 24 Tf 72 720 Td ({escaped_text}) Tj ET'.encode('utf-8'))} >>\n"
            f"stream\nBT /F1 24 Tf 72 720 Td ({escaped_text}) Tj ET\nendstream"
        ).encode("utf-8"),
    ]

    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{index} 0 obj\n".encode("ascii"))
        data.extend(obj)
        data.extend(b"\nendobj\n")

    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(data)


def test_valid_pdf_extraction(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    path.write_bytes(_pdf_bytes("AIMX PDF knowledge policy"))

    result = extract_text(path, filename="sample.pdf", content_type="application/pdf")

    assert "AIMX PDF knowledge policy" in result["text"]
    assert result["metadata"]["extension"] == ".pdf"


def test_valid_docx_extraction(tmp_path: Path):
    from docx import Document

    path = tmp_path / "sample.docx"
    document = Document()
    document.add_paragraph("AIMX DOCX onboarding policy")
    document.save(path)

    result = extract_text(
        path,
        filename="sample.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert "AIMX DOCX onboarding policy" in result["text"]
    assert result["metadata"]["extension"] == ".docx"


def test_corrupted_file_failure(tmp_path: Path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a real pdf")

    with pytest.raises(ValueError, match="file text extraction failed"):
        extract_text(path, filename="broken.pdf", content_type="application/pdf")


def test_unsupported_file_still_fails_safely(tmp_path: Path):
    path = tmp_path / "sample.exe"
    path.write_bytes(b"not supported")

    with pytest.raises(ValueError, match="unsupported file type"):
        extract_text(path, filename="sample.exe", content_type="application/octet-stream")
