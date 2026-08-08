import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CONFLICT_STATUSES = ("conflict_replaced", "conflict_kept")


def _parse_jsonb(value: Any) -> Any:
    """asyncpg returns jsonb columns as raw text unless a codec is registered
    on the pool (none is, here). Decode defensively rather than touching pool
    setup, which is shared by unrelated readers."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


class MemoryRepository:
    def __init__(self, db):
        # asyncpg pool
        self.db = db

    # -------------------------
    # Events (memory_events)
    # -------------------------
    async def insert_event(self, event: Dict[str, Any]) -> None:
        query = """
        INSERT INTO public.memory_events
        (company_id, session_id, event_type, user_message, executive_summary, logic_json, context, tags, idempotency_key)
        VALUES
        ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::text[],$9)
        ON CONFLICT (idempotency_key) DO NOTHING
        """
        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                event.get("company_id"),
                event.get("session_id"),
                event.get("event_type"),
                event.get("user_message"),
                event.get("executive_summary"),
                json.dumps(event.get("logic_json", {}), ensure_ascii=False),
                json.dumps(event.get("context", {}), ensure_ascii=False),
                event.get("tags") or [],
                event.get("idempotency_key"),
            )

    async def fetch_recent_events(
        self,
        company_id: str,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if session_id:
            query = """
            SELECT created_at, event_type, user_message, executive_summary, logic_json, context
            FROM public.memory_events
            WHERE company_id=$1 AND session_id=$2
            ORDER BY created_at DESC
            LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, session_id, limit)
        else:
            query = """
            SELECT created_at, event_type, user_message, executive_summary, logic_json, context
            FROM public.memory_events
            WHERE company_id=$1
            ORDER BY created_at DESC
            LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, limit)

        return [
            {
                "created_at": r["created_at"],
                "event_type": r["event_type"],
                "user_message": r["user_message"],
                "executive_summary": r["executive_summary"],
                "logic_json": r["logic_json"],
                "context": r["context"],
            }
            for r in rows
        ]

    # -------------------------
    # Facts (memory_facts)
    # -------------------------
    async def get_fact_by_key(
        self,
        company_id: str,
        fact_key: str,
    ) -> Optional[Dict[str, Any]]:
        query = """
        SELECT fact_type, fact_key, fact_value, confidence, source_event_id, updated_at
        FROM public.memory_facts
        WHERE company_id=$1 AND fact_key=$2
        LIMIT 1
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, company_id, fact_key)

        if not row:
            return None

        conflict_state = await self._latest_conflict_state(company_id=company_id, fact_key=fact_key)

        return {
            "fact_type": row["fact_type"],
            "fact_key": row["fact_key"],
            "fact_value": row["fact_value"],
            "confidence": row["confidence"],
            "source_event_id": row["source_event_id"],
            "updated_at": row["updated_at"],
            "has_conflict": conflict_state["has_conflict"],
            "residual_uncertainty": conflict_state["residual_uncertainty"],
        }

    async def _latest_conflict_state(self, company_id: str, fact_key: str) -> Dict[str, Any]:
        """Coordinated read-path helper (ENG-CONF-001 S2).

        has_conflict is defined as: this fact_key has at least one recorded
        conflict event (status conflict_replaced or conflict_kept) in
        memory_fact_history -- ever, not merely as the most recent write. It
        does not reset to False just because a later same-value reinforcement
        touched memory_facts; reinforcement never writes to
        memory_fact_history at all (see _upsert_normal_fact), so there is
        nothing that could mask a real conflict here.

        expansion_market is excluded on purpose: it has no conflict semantics
        (multiple concurrent values are allowed by design), and this key is
        never the subject of a conflict_replaced/conflict_kept row.
        """
        query = """
        SELECT residual_uncertainty
        FROM public.memory_fact_history
        WHERE company_id=$1 AND fact_key=$2 AND fact_key <> 'expansion_market'
          AND status IN ('conflict_replaced', 'conflict_kept')
        ORDER BY created_at DESC
        LIMIT 1
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, company_id, fact_key)

        if not row:
            return {"has_conflict": False, "residual_uncertainty": None}

        return {"has_conflict": True, "residual_uncertainty": row["residual_uncertainty"]}

    async def upsert_fact(
        self,
        company_id: str,
        session_id: Optional[str],
        fact_type: str,
        fact_key: str,
        fact_value: str,
        confidence: int = 0,
        source_event_id: Optional[str] = None,
    ) -> None:
        """
        Confidence Evolution + Conflict Detection + Expansion Markets

        Rules:
        - If same fact_key and same fact_value:
            raise confidence slightly
        - If same fact_key but different fact_value:
            print conflict warning
            if new confidence >= existing confidence:
                replace value
            else:
                keep old value
        - expansion_market is special:
            allow multiple rows with different fact_value

        ENG-CONF-001 (S1/S2): a genuine conflict -- new confidence replacing
        the existing value, or a conflicting new value being rejected -- is
        recorded as an immutable memory_fact_history row before this method
        returns, with both sides of the conflict captured in sources_weighed,
        so neither the superseded nor the rejected assertion is silently
        discarded. The memory_facts write and the history write happen on one
        connection inside one transaction, and the existing row is locked
        (SELECT ... FOR UPDATE) before the decision is made, so concurrent
        conflicting upserts serialize instead of racing on a stale read.

        This deliberately does NOT record a history row for every update.
        Plain inserts and same-value reinforcements are not conflicts, and a
        general history-of-every-update ledger is adjacent finding AF-1
        (Founder Decision R4), which remains excluded from ENG-CONF-001
        scope. Only the conflicting event itself is recorded, and it captures
        the pre-conflict/current assertion inline (sources_weighed) rather
        than depending on a separately preserved non-conflict trail.
        """
        fact_type = (fact_type or "other").strip().lower()
        fact_key = (fact_key or "").strip()
        fact_value = (fact_value or "").strip()

        if not fact_key or not fact_value:
            return

        conf = int(confidence or 0)
        if conf < 0:
            conf = 0
        if conf > 100:
            conf = 100

        provenance = {
            "session_id": session_id,
            "source_event_id": source_event_id,
            "recorded_via": "upsert_fact",
        }

        if fact_key == "expansion_market":
            await self._upsert_expansion_market_fact(
                company_id=company_id,
                session_id=session_id,
                fact_type=fact_type,
                fact_value=fact_value,
                conf=conf,
                source_event_id=source_event_id,
            )
            return

        await self._upsert_normal_fact(
            company_id=company_id,
            session_id=session_id,
            fact_type=fact_type,
            fact_key=fact_key,
            fact_value=fact_value,
            conf=conf,
            source_event_id=source_event_id,
            provenance=provenance,
        )

    async def _upsert_expansion_market_fact(
        self,
        *,
        company_id: str,
        session_id: Optional[str],
        fact_type: str,
        fact_value: str,
        conf: int,
        source_event_id: Optional[str],
    ) -> None:
        """expansion_market allows multiple concurrent values per company and
        never conflicts -- there is no "wrong" expansion market, so no
        memory_fact_history row is ever written for this key (see the
        exclusion in _latest_conflict_state and fetch_facts).

        NOTE (pre-existing, out of ENG-CONF-001 scope): memory_facts has a
        UNIQUE (company_id, fact_key) constraint, which the "allow multiple
        rows" comment above contradicts for any second distinct
        expansion_market value -- the INSERT below will raise
        UniqueViolationError in that case, exactly as it did before this
        task. That defect predates ENG-CONF-001, is not among the S1-S4
        surfaces, and is not touched here; callers already catch and log it.
        """
        fact_key = "expansion_market"

        async with self.db.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchrow(
                    """
                    SELECT confidence
                    FROM public.memory_facts
                    WHERE company_id=$1 AND fact_key=$2 AND LOWER(fact_value)=LOWER($3)
                    FOR UPDATE
                    """,
                    company_id, fact_key, fact_value,
                )

                if existing is not None:
                    existing_conf = int(existing["confidence"] or 0)
                    new_conf = min(100, max(existing_conf, conf) + 5)

                    await conn.execute(
                        """
                        UPDATE public.memory_facts
                        SET
                            confidence = $4,
                            session_id = $5,
                            fact_type = $6,
                            source_event_id = $7,
                            updated_at = NOW()
                        WHERE company_id=$1 AND fact_key=$2 AND LOWER(fact_value)=LOWER($3)
                        """,
                        company_id, fact_key, fact_value, new_conf, session_id, fact_type, source_event_id,
                    )

                    logger.info(
                        "Expansion market confidence increased",
                        extra={"company_id": company_id, "fact_key": fact_key, "confidence": new_conf},
                    )
                    return

                await conn.execute(
                    """
                    INSERT INTO public.memory_facts
                    (company_id, session_id, fact_type, fact_key, fact_value, confidence, source_event_id)
                    VALUES
                    ($1,$2,$3,$4,$5,$6,$7)
                    """,
                    company_id, session_id, fact_type, fact_key, fact_value, conf, source_event_id,
                )

                logger.info(
                    "Inserted expansion market fact",
                    extra={"company_id": company_id, "fact_key": fact_key},
                )

    async def _upsert_normal_fact(
        self,
        *,
        company_id: str,
        session_id: Optional[str],
        fact_type: str,
        fact_key: str,
        fact_value: str,
        conf: int,
        source_event_id: Optional[str],
        provenance: Dict[str, Any],
    ) -> None:
        async with self.db.acquire() as conn:
            async with conn.transaction():
                inserted = await conn.fetchrow(
                    """
                    INSERT INTO public.memory_facts
                    (company_id, session_id, fact_type, fact_key, fact_value, confidence, source_event_id)
                    VALUES
                    ($1,$2,$3,$4,$5,$6,$7)
                    ON CONFLICT ON CONSTRAINT memory_facts_company_key_unique DO NOTHING
                    RETURNING company_id
                    """,
                    company_id, session_id, fact_type, fact_key, fact_value, conf, source_event_id,
                )

                if inserted is not None:
                    # Won the race to create this fact_key: genuinely the
                    # first assertion, not a conflict. No history row (AF-1
                    # stays out of scope).
                    return

                # Someone already holds this key (a pre-existing row, or a
                # concurrent transaction that just won the INSERT race
                # above). Lock it for the remainder of this transaction so
                # concurrent conflicting upserts serialize on this row
                # instead of both deciding from a stale read.
                existing = await conn.fetchrow(
                    """
                    SELECT fact_type, fact_value, confidence, source_event_id
                    FROM public.memory_facts
                    WHERE company_id=$1 AND fact_key=$2
                    FOR UPDATE
                    """,
                    company_id, fact_key,
                )
                existing_value = (existing["fact_value"] or "").strip()
                existing_conf = int(existing["confidence"] or 0)
                existing_source_event_id = existing["source_event_id"]

                if existing_value.lower() == fact_value.lower():
                    new_conf = min(100, max(existing_conf, conf) + 5)
                    await conn.execute(
                        """
                        UPDATE public.memory_facts
                        SET
                          session_id = $3,
                          fact_type = $4,
                          confidence = $5,
                          source_event_id = $6,
                          updated_at = NOW()
                        WHERE company_id = $1 AND fact_key = $2
                        """,
                        company_id, fact_key, session_id, fact_type, new_conf, source_event_id,
                    )
                    logger.info(
                        "Fact confidence increased",
                        extra={"company_id": company_id, "fact_key": fact_key, "confidence": new_conf},
                    )
                    return

                # Different value while holding the row lock -> a real conflict.
                logger.warning(
                    "Fact conflict detected",
                    extra={
                        "company_id": company_id,
                        "fact_key": fact_key,
                        "existing_confidence": existing_conf,
                        "new_confidence": conf,
                    },
                )

                # conflict_with must identify the history row that made the
                # CURRENT assertion current -- i.e. the most recent
                # conflict_replaced row for this key -- never a conflict_kept
                # row (a conflict_kept row is a rejected assertion; it was
                # never the winner and must not become the reference point
                # for a later conflict against the still-current value).
                conflict_with = await conn.fetchval(
                    """
                    SELECT id FROM public.memory_fact_history
                    WHERE company_id=$1 AND fact_key=$2 AND status='conflict_replaced'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    company_id, fact_key,
                )

                sources_weighed = [
                    {
                        "role": "existing",
                        "fact_value": existing_value,
                        "confidence": existing_conf,
                        "source_event_id": existing_source_event_id,
                    },
                    {
                        "role": "incoming",
                        "fact_value": fact_value,
                        "confidence": conf,
                        "source_event_id": source_event_id,
                    },
                ]

                if conf >= existing_conf:
                    await conn.execute(
                        """
                        UPDATE public.memory_facts
                        SET
                          session_id = $3,
                          fact_type = $4,
                          fact_value = $5,
                          confidence = $6,
                          source_event_id = $7,
                          updated_at = NOW()
                        WHERE company_id = $1 AND fact_key = $2
                        """,
                        company_id, fact_key, session_id, fact_type, fact_value, conf, source_event_id,
                    )
                    status = "conflict_replaced"
                    resolution_basis = "new_confidence_gte_existing"
                    residual_uncertainty = (
                        f"Prior assertion '{existing_value}' (confidence {existing_conf}) was superseded "
                        f"on a confidence-threshold basis by '{fact_value}' (confidence {conf}); the prior "
                        "assertion is preserved in memory_fact_history, not destroyed."
                    )
                    log_msg = "Fact conflict resolved with replacement"
                else:
                    # memory_facts is intentionally left untouched here.
                    status = "conflict_kept"
                    resolution_basis = "existing_confidence_gt_new"
                    residual_uncertainty = (
                        f"Conflicting assertion '{fact_value}' (confidence {conf}) was received but not "
                        f"adopted because the existing assertion '{existing_value}' has confidence "
                        f"{existing_conf}; the rejected assertion is preserved in memory_fact_history "
                        "for future reconciliation."
                    )
                    log_msg = "Fact conflict kept existing value"

                await conn.execute(
                    """
                    INSERT INTO public.memory_fact_history
                    (company_id, session_id, fact_type, fact_key, fact_value, confidence,
                     source_event_id, status, conflict_with, resolution_basis,
                     sources_weighed, residual_uncertainty, provenance)
                    VALUES
                    ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12,$13::jsonb)
                    """,
                    company_id,
                    session_id,
                    fact_type,
                    fact_key,
                    fact_value,
                    conf,
                    source_event_id,
                    status,
                    conflict_with,
                    resolution_basis,
                    json.dumps(sources_weighed, ensure_ascii=False),
                    residual_uncertainty,
                    json.dumps(provenance, ensure_ascii=False),
                )

                logger.info(log_msg, extra={"company_id": company_id, "fact_key": fact_key})

    async def fetch_facts(self, company_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        query = """
        WITH latest_conflict AS (
            SELECT DISTINCT ON (fact_key) fact_key, residual_uncertainty
            FROM public.memory_fact_history
            WHERE company_id = $1
              AND status IN ('conflict_replaced', 'conflict_kept')
              AND fact_key <> 'expansion_market'
            ORDER BY fact_key, created_at DESC
        )
        SELECT
            f.fact_type, f.fact_key, f.fact_value, f.confidence, f.updated_at,
            (lc.fact_key IS NOT NULL) AS has_conflict,
            lc.residual_uncertainty
        FROM public.memory_facts f
        LEFT JOIN latest_conflict lc ON lc.fact_key = f.fact_key
        WHERE f.company_id = $1
        ORDER BY f.updated_at DESC
        LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, company_id, limit)

        return [
            {
                "fact_type": r["fact_type"],
                "fact_key": r["fact_key"],
                "fact_value": r["fact_value"],
                "confidence": r["confidence"],
                "updated_at": r["updated_at"],
                "has_conflict": r["has_conflict"],
                "residual_uncertainty": r["residual_uncertainty"],
            }
            for r in rows
        ]

    async def fetch_fact_history(
        self,
        company_id: str,
        fact_key: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """ENG-CONF-001 S3: conflicts and resolutions retrievable after the fact.

        Returns recorded conflict events for a company (optionally scoped to
        one fact_key), most recent first -- each with resolution basis,
        sources weighed (both the superseded/rejected and winning sides),
        residual uncertainty, and provenance. This is a conflict ledger, not
        a general update history: non-conflicting assertions (plain inserts,
        same-value reinforcements, expansion_market) are not recorded here
        (AF-1 remains out of scope; see upsert_fact).
        """
        if fact_key:
            query = """
            SELECT id, fact_type, fact_key, fact_value, confidence, session_id,
                   source_event_id, status, conflict_with, resolution_basis,
                   sources_weighed, residual_uncertainty, provenance, created_at
            FROM public.memory_fact_history
            WHERE company_id=$1 AND fact_key=$2
            ORDER BY created_at DESC
            LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, fact_key, limit)
        else:
            query = """
            SELECT id, fact_type, fact_key, fact_value, confidence, session_id,
                   source_event_id, status, conflict_with, resolution_basis,
                   sources_weighed, residual_uncertainty, provenance, created_at
            FROM public.memory_fact_history
            WHERE company_id=$1
            ORDER BY created_at DESC
            LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, limit)

        return [
            {
                "id": str(r["id"]),
                "fact_type": r["fact_type"],
                "fact_key": r["fact_key"],
                "fact_value": r["fact_value"],
                "confidence": r["confidence"],
                "session_id": r["session_id"],
                "source_event_id": r["source_event_id"],
                "status": r["status"],
                "conflict_with": str(r["conflict_with"]) if r["conflict_with"] else None,
                "resolution_basis": r["resolution_basis"],
                "sources_weighed": _parse_jsonb(r["sources_weighed"]),
                "residual_uncertainty": r["residual_uncertainty"],
                "provenance": _parse_jsonb(r["provenance"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    async def build_company_profile(self, company_id: str) -> Dict[str, Any]:
        facts = await self.fetch_facts(company_id=company_id, limit=100)

        profile = {
            "product_name": None,
            "product_type": None,
            "target_market": None,
            "primary_market": None,
            "expansion_markets": [],
            "stage": None,
            "goal": None,
            "launch_timeline": None,
            "revenue": None,
            "team_size": None,
        }
        conflicts: Dict[str, Any] = {}

        for f in facts:
            key = (f.get("fact_key") or "").strip()
            value = (f.get("fact_value") or "").strip()

            if not value:
                continue

            if key == "expansion_market":
                if value not in profile["expansion_markets"]:
                    profile["expansion_markets"].append(value)
                continue

            if key in profile:
                if profile[key] is None:
                    profile[key] = value
                    if f.get("has_conflict"):
                        conflicts[key] = {
                            "residual_uncertainty": f.get("residual_uncertainty"),
                        }

        profile["conflicts"] = conflicts
        return profile
