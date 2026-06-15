"""
Tests for KnowledgeService.

Pure unit tests: no DB, no async, no network.
Uses tempfile.mkdtemp() for temp directories (tmp_path has a Windows ACL issue
on this machine with the shared pytest temp root).
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from app.services.knowledge.knowledge_service import (
    CompanyKnowledge,
    KnowledgeDocument,
    KnowledgeService,
    _TYPE_COMPANY_BRAIN,
    _TYPE_DECISION_RULES,
    _TYPE_OPERATIONAL_SEMANTICS,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_knowledge_root():
    """Yield a fresh temporary directory, then remove it."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


def _populate_company(root: Path, company: str) -> None:
    """Write all three standard knowledge files for a company."""
    company_dir = root / company.lower()
    company_dir.mkdir(parents=True, exist_ok=True)
    prefix = company.upper()
    (company_dir / f"{prefix}_COMPANY_BRAIN.md").write_text(
        "# Company Brain\nCore values here.", encoding="utf-8"
    )
    (company_dir / f"{prefix}_OPERATIONAL_SEMANTICS.md").write_text(
        "# Operational Semantics\nField definitions here.", encoding="utf-8"
    )
    (company_dir / f"{prefix}_DECISION_RULES.md").write_text(
        "# Decision Rules\nIF quality conflicts THEN prioritize quality.", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# list_companies
# ---------------------------------------------------------------------------

def test_list_companies_returns_sorted_names(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "zebra")
    _populate_company(tmp_knowledge_root, "alpha")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    assert svc.list_companies() == ["alpha", "zebra"]


def test_list_companies_empty_root(tmp_knowledge_root: Path) -> None:
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    assert svc.list_companies() == []


def test_list_companies_missing_root(tmp_knowledge_root: Path) -> None:
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root / "does_not_exist")
    assert svc.list_companies() == []


def test_list_companies_ignores_hidden_dirs(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "dairtna")
    (tmp_knowledge_root / ".hidden").mkdir()
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    result = svc.list_companies()
    assert ".hidden" not in result
    assert "dairtna" in result


# ---------------------------------------------------------------------------
# load_company_brain
# ---------------------------------------------------------------------------

def test_load_company_brain_returns_document(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "dairtna")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    doc = svc.load_company_brain("dairtna")
    assert doc is not None
    assert doc.document_type == _TYPE_COMPANY_BRAIN
    assert doc.company_name == "dairtna"
    assert "Company Brain" in doc.content


def test_load_company_brain_missing_returns_none(tmp_knowledge_root: Path) -> None:
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    assert svc.load_company_brain("nonexistent") is None


# ---------------------------------------------------------------------------
# load_operational_semantics
# ---------------------------------------------------------------------------

def test_load_operational_semantics_returns_document(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "dairtna")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    doc = svc.load_operational_semantics("dairtna")
    assert doc is not None
    assert doc.document_type == _TYPE_OPERATIONAL_SEMANTICS
    assert "Operational Semantics" in doc.content


def test_load_operational_semantics_missing_returns_none(tmp_knowledge_root: Path) -> None:
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    assert svc.load_operational_semantics("nonexistent") is None


# ---------------------------------------------------------------------------
# load_decision_rules
# ---------------------------------------------------------------------------

def test_load_decision_rules_returns_document(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "dairtna")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    doc = svc.load_decision_rules("dairtna")
    assert doc is not None
    assert doc.document_type == _TYPE_DECISION_RULES
    assert "prioritize quality" in doc.content


def test_load_decision_rules_missing_returns_none(tmp_knowledge_root: Path) -> None:
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    assert svc.load_decision_rules("nonexistent") is None


# ---------------------------------------------------------------------------
# load_all_knowledge
# ---------------------------------------------------------------------------

def test_load_all_knowledge_all_present(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "dairtna")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    knowledge = svc.load_all_knowledge("dairtna")
    assert isinstance(knowledge, CompanyKnowledge)
    assert knowledge.company_name == "dairtna"
    assert knowledge.company_brain is not None
    assert knowledge.operational_semantics is not None
    assert knowledge.decision_rules is not None
    assert len(knowledge.documents) == 3
    assert not knowledge.is_empty


def test_load_all_knowledge_partial_presence(tmp_knowledge_root: Path) -> None:
    company_dir = tmp_knowledge_root / "dairtna"
    company_dir.mkdir()
    (company_dir / "DAIRTNA_COMPANY_BRAIN.md").write_text("# Brain", encoding="utf-8")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    knowledge = svc.load_all_knowledge("dairtna")
    assert knowledge.company_brain is not None
    assert knowledge.operational_semantics is None
    assert knowledge.decision_rules is None
    assert len(knowledge.documents) == 1


def test_load_all_knowledge_none_present(tmp_knowledge_root: Path) -> None:
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    knowledge = svc.load_all_knowledge("ghost")
    assert knowledge.is_empty
    assert knowledge.documents == []


# ---------------------------------------------------------------------------
# KnowledgeDocument properties
# ---------------------------------------------------------------------------

def test_knowledge_document_path_is_path_object(tmp_knowledge_root: Path) -> None:
    _populate_company(tmp_knowledge_root, "dairtna")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    doc = svc.load_company_brain("dairtna")
    assert doc is not None
    assert isinstance(doc.path, Path)
    assert doc.path.exists()


def test_knowledge_document_content_preserves_unicode(tmp_knowledge_root: Path) -> None:
    company_dir = tmp_knowledge_root / "dairtna"
    company_dir.mkdir()
    arabic_text = "# العقل الشركاتي\nالجودة أهم من الربح."
    (company_dir / "DAIRTNA_COMPANY_BRAIN.md").write_text(arabic_text, encoding="utf-8")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    doc = svc.load_company_brain("dairtna")
    assert doc is not None
    assert "الجودة أهم من الربح" in doc.content


# ---------------------------------------------------------------------------
# Case handling
# ---------------------------------------------------------------------------

def test_company_name_case_insensitive_folder(tmp_knowledge_root: Path) -> None:
    """Folder is resolved in lowercase; file prefix is uppercase."""
    _populate_company(tmp_knowledge_root, "dairtna")
    svc = KnowledgeService(knowledge_root=tmp_knowledge_root)
    doc = svc.load_company_brain("DAIRTNA")
    assert doc is not None
    assert "Company Brain" in doc.content


# ---------------------------------------------------------------------------
# Module-level default instance
# ---------------------------------------------------------------------------

def test_module_instance_is_knowledge_service() -> None:
    from app.services.knowledge.knowledge_service import knowledge_service
    assert isinstance(knowledge_service, KnowledgeService)
