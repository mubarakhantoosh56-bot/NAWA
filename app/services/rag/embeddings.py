"""Embedding helpers for NAWA semantic RAG retrieval."""

import logging
from uuid import UUID

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

EmbeddingVector = list[float]


class EmbeddingService:
    """Small OpenAI embedding wrapper for text-only RAG chunks."""

    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self.client = client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model or settings.EMBEDDING_MODEL
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS

    async def embed_text(self, text: str) -> EmbeddingVector:
        normalized_text = " ".join((text or "").split())
        if not normalized_text:
            raise ValueError("embedding text is required")

        response = await self.client.embeddings.create(
            model=self.model,
            input=normalized_text,
        )
        embedding = list(response.data[0].embedding)
        self._validate_embedding(embedding)
        return embedding

    async def embed_chunks(self, chunks: list[dict[str, object]]) -> list[EmbeddingVector | None]:
        embeddings: list[EmbeddingVector | None] = []
        for chunk in chunks:
            content = str(chunk.get("content") or "")
            try:
                embeddings.append(await self.embed_text(content))
            except Exception as exc:
                logger.warning(
                    "rag_embedding_chunk_failed",
                    extra={"error_type": type(exc).__name__},
                )
                embeddings.append(None)
        return embeddings

    def _validate_embedding(self, embedding: EmbeddingVector) -> None:
        if len(embedding) != self.dimensions:
            raise ValueError("unexpected embedding dimensions")
        if not all(isinstance(value, int | float) for value in embedding):
            raise ValueError("invalid embedding vector")


def vector_to_pg_literal(embedding: EmbeddingVector) -> str:
    """Return a pgvector-compatible literal without logging or storing content."""
    return "[" + ",".join(str(float(value)) for value in embedding) + "]"


async def store_chunk_embeddings(
    db,
    company_id: UUID,
    file_id: UUID,
    department_id: UUID | None,
    chunks: list[dict[str, object]],
    embedding_service: EmbeddingService | None = None,
) -> int:
    """Generate and store embeddings for chunks; caller decides failure policy."""
    if not chunks:
        return 0

    service = embedding_service or EmbeddingService()
    embeddings = await service.embed_chunks(chunks)
    stored_count = 0

    for chunk, embedding in zip(chunks, embeddings, strict=False):
        if embedding is None:
            continue

        await db.execute(
            """
            INSERT INTO file_chunk_embeddings (
                company_id,
                file_id,
                chunk_id,
                department_id,
                embedding_model,
                embedding_dimensions,
                embedding,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::vector, '{}'::jsonb)
            ON CONFLICT (chunk_id, embedding_model)
            WHERE deleted_at IS NULL
            DO UPDATE SET
                embedding = EXCLUDED.embedding,
                embedding_dimensions = EXCLUDED.embedding_dimensions,
                department_id = EXCLUDED.department_id,
                updated_at = NOW(),
                deleted_at = NULL
            """,
            company_id,
            file_id,
            chunk["id"],
            department_id,
            service.model,
            service.dimensions,
            vector_to_pg_literal(embedding),
        )
        stored_count += 1

    return stored_count
