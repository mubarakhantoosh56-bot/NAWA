from pathlib import Path
from uuid import uuid4

from app.services.file_ingestion_service import FileIngestionService
from app.services.rag.embeddings import store_chunk_embeddings, vector_to_pg_literal


class _FakeFileRepo:
    def __init__(self):
        self.created_file_id = uuid4()
        self.updated_metadata = None

    async def create_file(self, **kwargs):
        return {
            "id": self.created_file_id,
            "company_id": kwargs["company_id"],
            "department_id": kwargs.get("department_id"),
            "metadata": {},
        }

    async def update_file_status(self, **kwargs):
        self.updated_metadata = kwargs["metadata"]
        return {
            "id": kwargs["file_id"],
            "company_id": kwargs["company_id"],
            "status": kwargs["status"],
            "metadata": kwargs["metadata"],
        }


class _FakeChunkRepo:
    async def create_chunks(self, **kwargs):
        return [
            {
                "id": uuid4(),
                "file_id": kwargs["file_id"],
                "company_id": kwargs["company_id"],
                "department_id": kwargs.get("department_id"),
                "chunk_index": 0,
                "content": "AIMX semantic ingestion policy",
                "metadata": {},
            }
        ]


class _FakeDepartmentRepo:
    async def get_by_id(self, **kwargs):
        return {"id": kwargs["department_id"]}


def test_vector_to_pg_literal():
    assert vector_to_pg_literal([0, 1.25, -2]) == "[0.0,1.25,-2.0]"


def test_store_chunk_embeddings_is_tenant_scoped():
    company_id = uuid4()
    file_id = uuid4()
    chunk_id = uuid4()
    captured = {}

    class FakeDb:
        async def execute(self, sql, *args):
            captured["sql"] = sql
            captured["args"] = args
            return "INSERT 0 1"

    class FakeEmbeddingService:
        model = "test-embedding"
        dimensions = 3

        async def embed_chunks(self, chunks):
            return [[0.1, 0.2, 0.3]]

    import asyncio

    count = asyncio.run(
        store_chunk_embeddings(
            db=FakeDb(),
            company_id=company_id,
            file_id=file_id,
            department_id=None,
            chunks=[{"id": chunk_id, "content": "policy"}],
            embedding_service=FakeEmbeddingService(),
        )
    )

    assert count == 1
    assert "INSERT INTO file_chunk_embeddings" in captured["sql"]
    assert captured["args"][0] == company_id
    assert captured["args"][1] == file_id
    assert captured["args"][2] == chunk_id
    assert captured["args"][6] == "[0.1,0.2,0.3]"


def test_file_ingestion_generates_embeddings_metadata(monkeypatch, tmp_path: Path):
    import asyncio

    company_id = uuid4()
    user_id = uuid4()
    source = tmp_path / "source.txt"
    source.write_text("AIMX semantic ingestion policy", encoding="utf-8")

    service = FileIngestionService(db=object(), storage_root=tmp_path / "storage")
    fake_file_repo = _FakeFileRepo()
    service.file_repo = fake_file_repo
    service.file_chunk_repo = _FakeChunkRepo()
    service.department_repo = _FakeDepartmentRepo()

    async def fake_store_chunk_embeddings(**kwargs):
        assert kwargs["company_id"] == company_id
        assert kwargs["file_id"] == fake_file_repo.created_file_id
        assert len(kwargs["chunks"]) == 1
        return 1

    monkeypatch.setattr(
        "app.services.file_ingestion_service.store_chunk_embeddings",
        fake_store_chunk_embeddings,
    )

    result = asyncio.run(
        service.ingest_file(
            company_id=company_id,
            uploaded_by_user_id=user_id,
            source_path=source,
            filename="source.txt",
            content_type="text/plain",
        )
    )

    assert result["file"]["status"] == "ready"
    assert fake_file_repo.updated_metadata["embedding_status"] == "ready"
    assert fake_file_repo.updated_metadata["embedding_count"] == 1


def test_file_ingestion_embedding_failure_does_not_fail_file(monkeypatch, tmp_path: Path):
    import asyncio

    company_id = uuid4()
    user_id = uuid4()
    source = tmp_path / "source.txt"
    source.write_text("AIMX semantic ingestion policy", encoding="utf-8")

    service = FileIngestionService(db=object(), storage_root=tmp_path / "storage")
    fake_file_repo = _FakeFileRepo()
    service.file_repo = fake_file_repo
    service.file_chunk_repo = _FakeChunkRepo()
    service.department_repo = _FakeDepartmentRepo()

    async def fake_store_chunk_embeddings(**kwargs):
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(
        "app.services.file_ingestion_service.store_chunk_embeddings",
        fake_store_chunk_embeddings,
    )

    result = asyncio.run(
        service.ingest_file(
            company_id=company_id,
            uploaded_by_user_id=user_id,
            source_path=source,
            filename="source.txt",
            content_type="text/plain",
        )
    )

    assert result["file"]["status"] == "ready"
    assert fake_file_repo.updated_metadata["embedding_status"] == "failed"
    assert fake_file_repo.updated_metadata["embedding_count"] == 0
