"""
Knowledge Service — read-only loader for company knowledge repositories.

Discovers and loads structured markdown documents from the project-level
knowledge/ directory. No database access. No AI integration. No side effects.

Directory layout expected:
    knowledge/
        <company_name>/
            <COMPANY_NAME>_COMPANY_BRAIN.md
            <COMPANY_NAME>_OPERATIONAL_SEMANTICS.md
            <COMPANY_NAME>_DECISION_RULES.md
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Project root / knowledge  (resolved relative to this file's location)
_KNOWLEDGE_ROOT: Path = Path(__file__).parent.parent.parent.parent / "knowledge"

_TYPE_COMPANY_BRAIN: str = "COMPANY_BRAIN"
_TYPE_OPERATIONAL_SEMANTICS: str = "OPERATIONAL_SEMANTICS"
_TYPE_DECISION_RULES: str = "DECISION_RULES"

_ALL_DOCUMENT_TYPES: tuple[str, ...] = (
    _TYPE_COMPANY_BRAIN,
    _TYPE_OPERATIONAL_SEMANTICS,
    _TYPE_DECISION_RULES,
)


@dataclass(frozen=True)
class KnowledgeDocument:
    """A single loaded knowledge document."""

    company_name: str
    document_type: str
    path: Path
    content: str


@dataclass(frozen=True)
class CompanyKnowledge:
    """All knowledge documents for one company, any of which may be absent."""

    company_name: str
    company_brain: Optional[KnowledgeDocument]
    operational_semantics: Optional[KnowledgeDocument]
    decision_rules: Optional[KnowledgeDocument]

    @property
    def documents(self) -> list[KnowledgeDocument]:
        """Return only the documents that were successfully loaded."""
        return [
            d for d in (self.company_brain, self.operational_semantics, self.decision_rules)
            if d is not None
        ]

    @property
    def is_empty(self) -> bool:
        return not self.documents


class KnowledgeService:
    """
    Read-only service for loading company knowledge repositories from disk.

    All methods are synchronous — knowledge files are local and small.
    Inject a custom ``knowledge_root`` in tests via the constructor.
    """

    def __init__(self, knowledge_root: Optional[Path] = None) -> None:
        self._root: Path = knowledge_root if knowledge_root is not None else _KNOWLEDGE_ROOT

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_companies(self) -> list[str]:
        """Return sorted names of all companies that have a knowledge folder."""
        if not self._root.exists():
            logger.warning(
                "knowledge_root_not_found",
                extra={"path": str(self._root)},
            )
            return []
        return sorted(
            entry.name
            for entry in self._root.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        )

    # ------------------------------------------------------------------
    # Public loaders
    # ------------------------------------------------------------------

    def load_company_brain(self, company_name: str) -> Optional[KnowledgeDocument]:
        """Load the Company Brain document for ``company_name``. Returns None if absent."""
        return self._load_document(company_name, _TYPE_COMPANY_BRAIN)

    def load_operational_semantics(self, company_name: str) -> Optional[KnowledgeDocument]:
        """Load the Operational Semantics document for ``company_name``. Returns None if absent."""
        return self._load_document(company_name, _TYPE_OPERATIONAL_SEMANTICS)

    def load_decision_rules(self, company_name: str) -> Optional[KnowledgeDocument]:
        """Load the Decision Rules document for ``company_name``. Returns None if absent."""
        return self._load_document(company_name, _TYPE_DECISION_RULES)

    def load_all_knowledge(self, company_name: str) -> CompanyKnowledge:
        """Load all three knowledge documents for ``company_name`` in one call."""
        brain = self.load_company_brain(company_name)
        semantics = self.load_operational_semantics(company_name)
        rules = self.load_decision_rules(company_name)

        knowledge = CompanyKnowledge(
            company_name=company_name,
            company_brain=brain,
            operational_semantics=semantics,
            decision_rules=rules,
        )

        logger.info(
            "knowledge_all_loaded",
            extra={
                "company": company_name,
                "loaded": len(knowledge.documents),
                "missing": len(_ALL_DOCUMENT_TYPES) - len(knowledge.documents),
            },
        )
        return knowledge

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_path(self, company_name: str, document_type: str) -> Path:
        filename = f"{company_name.upper()}_{document_type}.md"
        return self._root / company_name.lower() / filename

    def _load_document(self, company_name: str, document_type: str) -> Optional[KnowledgeDocument]:
        path = self._resolve_path(company_name, document_type)
        try:
            content = path.read_text(encoding="utf-8")
            logger.debug(
                "knowledge_document_loaded",
                extra={"company": company_name, "type": document_type},
            )
            return KnowledgeDocument(
                company_name=company_name,
                document_type=document_type,
                path=path,
                content=content,
            )
        except FileNotFoundError:
            logger.warning(
                "knowledge_document_not_found",
                extra={"company": company_name, "type": document_type, "path": str(path)},
            )
            return None
        except OSError:
            logger.warning(
                "knowledge_document_load_failed",
                extra={"company": company_name, "type": document_type, "path": str(path)},
                exc_info=True,
            )
            return None


# Module-level default instance pointing at the project knowledge/ directory.
knowledge_service = KnowledgeService()
