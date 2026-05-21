"""Service layer for NAWA operational situations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.repositories.department_repository import DepartmentRepository
from app.repositories.operational_situation_repository import OperationalSituationRepository


VALID_SITUATION_STATUSES = {"active", "monitoring", "resolved"}
VALID_SITUATION_SOURCE_TYPES = {"manual_rule", "scheduled_rule", "future_ai"}
GROUPING_WINDOW_HOURS = 72
PROXIMITY_GAP_HOURS = 36
MAX_GROUPING_EVENTS = 500


@dataclass(frozen=True)
class EventCluster:
    """Structured operational event cluster selected for situation creation."""

    events: list[dict[str, Any]]
    department_id: UUID | None
    category: str
    priority: str
    event_type: str


class OperationalSituationService:
    """Business logic for tenant-scoped operational situations."""

    def __init__(self, db: Any) -> None:
        """Initialize the service with situation and department repositories."""
        self.situation_repo = OperationalSituationRepository(db)
        self.department_repo = DepartmentRepository(db)

    async def group_recent_events(
        self,
        *,
        company_id: UUID,
        source_type: str = "manual_rule",
    ) -> dict[str, Any]:
        """Group recent operational events into rule-based operational situations."""
        normalized_source_type = _normalize_source_type(source_type)
        window_end = datetime.now(timezone.utc)
        window_start = window_end - timedelta(hours=GROUPING_WINDOW_HOURS)
        events = await self.situation_repo.list_recent_events_for_grouping(
            company_id=company_id,
            since=window_start,
            limit=MAX_GROUPING_EVENTS,
        )

        created: list[dict[str, Any]] = []
        duplicate_clusters = 0
        clusters = _build_clusters(events)
        for cluster in clusters:
            event_ids = [event["id"] for event in cluster.events]
            duplicates = await self.situation_repo.find_active_situations_for_events(
                company_id=company_id,
                event_ids=event_ids,
            )
            if duplicates:
                duplicate_clusters += 1
                continue

            situation = await self._create_cluster_situation(
                company_id=company_id,
                cluster=cluster,
                source_type=normalized_source_type,
            )
            created.append(situation)

        return {
            "created_situations": created,
            "created_count": len(created),
            "duplicate_clusters_skipped": duplicate_clusters,
            "analyzed_event_count": len(events),
            "window_start": window_start,
            "window_end": window_end,
        }

    async def list_situations(
        self,
        *,
        company_id: UUID,
        status: str | None = None,
        department_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return operational situations visible inside one company."""
        if department_id is not None:
            department = await self.department_repo.get_by_id(
                company_id=company_id,
                department_id=department_id,
            )
            if department is None:
                raise ValueError("Invalid department_id")

        normalized_status = _normalize_status(status) if status else None
        return await self.situation_repo.list_situations(
            company_id=company_id,
            status=normalized_status,
            department_id=department_id,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )

    async def get_situation(
        self,
        *,
        company_id: UUID,
        situation_id: UUID,
    ) -> dict[str, Any] | None:
        """Return one operational situation with linked events."""
        situation = await self.situation_repo.get_situation(
            company_id=company_id,
            situation_id=situation_id,
        )
        if situation is None:
            return None

        events = await self.situation_repo.list_situation_events(
            company_id=company_id,
            situation_id=situation_id,
        )
        return {**situation, "events": events}

    async def _create_cluster_situation(
        self,
        *,
        company_id: UUID,
        cluster: EventCluster,
        source_type: str,
    ) -> dict[str, Any]:
        event_count = len(cluster.events)
        time_window_start = min(event["event_timestamp"] for event in cluster.events)
        time_window_end = max(event["event_timestamp"] for event in cluster.events)
        situation_type = _determine_situation_type(cluster.category, cluster.event_type)
        severity = _determine_severity(cluster.events, situation_type)
        title = _build_title(
            situation_type=situation_type,
            category=cluster.category,
            priority=cluster.priority,
            event_type=cluster.event_type,
            event_count=event_count,
        )
        summary = _build_summary(
            category=cluster.category,
            priority=cluster.priority,
            event_type=cluster.event_type,
            event_count=event_count,
            department_id=cluster.department_id,
        )
        situation = await self.situation_repo.create_situation(
            company_id=company_id,
            title=title,
            summary=summary,
            situation_type=situation_type,
            severity=severity,
            status="active",
            time_window_start=time_window_start,
            time_window_end=time_window_end,
            department_id=cluster.department_id,
            detection_method="rule_based",
            source_type=source_type,
        )
        await self.situation_repo.link_situation_events(
            company_id=company_id,
            situation_id=situation["id"],
            event_links=[
                {"event_id": event["id"], "role": _event_role(index)}
                for index, event in enumerate(cluster.events)
            ],
        )
        situation["event_count"] = event_count
        return situation


def _build_clusters(events: list[dict[str, Any]]) -> list[EventCluster]:
    grouped: dict[tuple[UUID | None, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        key = (
            event.get("department_id"),
            _clean_key(event.get("category")),
            _clean_key(event.get("priority")),
            _clean_key(event.get("event_type")),
        )
        grouped[key].append(event)

    clusters: list[EventCluster] = []
    for (department_id, category, priority, event_type), grouped_events in grouped.items():
        sorted_events = sorted(grouped_events, key=lambda item: item["event_timestamp"])
        current: list[dict[str, Any]] = []
        previous_timestamp: datetime | None = None
        for event in sorted_events:
            event_timestamp = event["event_timestamp"]
            if (
                previous_timestamp is not None
                and event_timestamp - previous_timestamp > timedelta(hours=PROXIMITY_GAP_HOURS)
            ):
                _append_cluster(
                    clusters=clusters,
                    events=current,
                    department_id=department_id,
                    category=category,
                    priority=priority,
                    event_type=event_type,
                )
                current = []
            current.append(event)
            previous_timestamp = event_timestamp

        _append_cluster(
            clusters=clusters,
            events=current,
            department_id=department_id,
            category=category,
            priority=priority,
            event_type=event_type,
        )

    clusters.sort(
        key=lambda cluster: (
            _severity_rank(_determine_severity(cluster.events, "risk")),
            len(cluster.events),
            max(event["event_timestamp"] for event in cluster.events),
        ),
        reverse=True,
    )
    return clusters


def _append_cluster(
    *,
    clusters: list[EventCluster],
    events: list[dict[str, Any]],
    department_id: UUID | None,
    category: str,
    priority: str,
    event_type: str,
) -> None:
    if len(events) < 2:
        return
    clusters.append(
        EventCluster(
            events=list(events),
            department_id=department_id,
            category=category,
            priority=priority,
            event_type=event_type,
        )
    )


def _determine_situation_type(category: str, event_type: str) -> str:
    structured_text = f"{category} {event_type}".lower()
    positive_tokens = ("positive", "improvement", "resolved", "recovery", "completed", "success")
    bottleneck_tokens = ("delay", "shortage", "distribution", "bottleneck", "blocked", "capacity")
    risk_tokens = ("risk", "mortality", "medicine", "complaint", "absence", "quality", "health")

    if any(token in structured_text for token in positive_tokens):
        return "positive_signal"
    if any(token in structured_text for token in bottleneck_tokens):
        return "bottleneck"
    if any(token in structured_text for token in risk_tokens):
        return "risk"
    return "anomaly"


def _determine_severity(events: list[dict[str, Any]], situation_type: str) -> str:
    priorities = [_clean_key(event.get("priority")) for event in events]
    event_count = len(events)
    if "critical" in priorities:
        return "critical"
    if event_count >= 4 and priorities.count("high") >= 2:
        return "critical" if situation_type != "positive_signal" else "medium"
    if "high" in priorities or event_count >= 3:
        return "high" if situation_type != "positive_signal" else "medium"
    if any(priority in {"watch", "normal"} for priority in priorities):
        return "medium" if situation_type != "positive_signal" else "low"
    return "low"


def _build_title(
    *,
    situation_type: str,
    category: str,
    priority: str,
    event_type: str,
    event_count: int,
) -> str:
    label = _display_label(category or event_type or "operational event")
    type_label = _display_label(situation_type)
    priority_label = _display_label(priority or "priority")
    return f"{type_label}: {label} {priority_label} cluster ({event_count} events)"


def _build_summary(
    *,
    category: str,
    priority: str,
    event_type: str,
    event_count: int,
    department_id: UUID | None,
) -> str:
    scope = f"department {department_id}" if department_id else "company-wide scope"
    return (
        f"Rule-based grouping found {event_count} related operational events in {scope}. "
        f"Cluster key: category={category}, priority={priority}, event_type={event_type}."
    )


def _event_role(index: int) -> str:
    return "primary" if index == 0 else "supporting"


def _clean_key(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _display_label(value: str) -> str:
    return value.replace("_", " ").replace(".", " ").title()


def _normalize_status(value: str) -> str:
    normalized = _clean_key(value)
    if normalized not in VALID_SITUATION_STATUSES:
        raise ValueError("Invalid situation status")
    return normalized


def _normalize_source_type(value: str) -> str:
    normalized = _clean_key(value)
    if normalized not in VALID_SITUATION_SOURCE_TYPES:
        raise ValueError("Invalid situation source_type")
    return normalized


def _severity_rank(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 0)
