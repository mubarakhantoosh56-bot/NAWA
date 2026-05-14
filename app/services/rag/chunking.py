"""Deterministic text chunking utilities for RAG ingestion."""

RowDict = dict[str, object]


def chunk_text(
    text: str,
    chunk_size_chars: int = 4000,
    overlap_chars: int = 500,
) -> list[RowDict]:
    """Split text into ordered overlapping chunks."""
    if chunk_size_chars <= 0:
        raise ValueError("chunk_size_chars must be positive")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be nonnegative")
    if overlap_chars >= chunk_size_chars:
        raise ValueError("overlap_chars must be smaller than chunk_size_chars")

    stripped_text = text.strip()
    if not stripped_text:
        return []

    chunks = []
    start = 0
    chunk_index = 0
    text_length = len(stripped_text)

    while start < text_length:
        end = min(start + chunk_size_chars, text_length)
        content = stripped_text[start:end].strip()
        if content:
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": content,
                    "token_count": None,
                    "metadata": {
                        "start_char": start,
                        "end_char": end,
                    },
                }
            )
            chunk_index += 1

        if end >= text_length:
            break
        start = end - overlap_chars

    return chunks
