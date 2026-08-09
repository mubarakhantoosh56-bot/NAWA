"""Validation rules for feed mill raw-material inventory records."""

from __future__ import annotations

from dataclasses import dataclass

from app.oip.models.feed_mill_inventory_record import FeedMillInventoryRecord


@dataclass(frozen=True)
class FeedMillValidationIssue:
    """One validation issue found in a normalized feed mill record."""

    row_number: int
    field_name: str
    message: str


class FeedMillValidationError(ValueError):
    """Raised when feed mill inventory records fail OIP validation."""

    def __init__(self, issues: list[FeedMillValidationIssue]) -> None:
        self.issues = issues
        details = "; ".join(
            f"row {issue.row_number} {issue.field_name}: {issue.message}"
            for issue in issues
        )
        super().__init__(details)


class FeedMillInventoryValidator:
    """Validate the minimum foundation rule for feed mill inventory records."""

    def validate(
        self,
        records: list[FeedMillInventoryRecord],
    ) -> list[FeedMillValidationIssue]:
        """Return all validation issues without mutating records."""
        issues: list[FeedMillValidationIssue] = []
        for record in records:
            if not record.material_name.strip():
                issues.append(
                    FeedMillValidationIssue(
                        row_number=record.row_number,
                        field_name="material_name",
                        message="material name must exist",
                    )
                )
        return issues

    def validate_or_raise(self, records: list[FeedMillInventoryRecord]) -> None:
        """Raise FeedMillValidationError when any record is invalid."""
        issues = self.validate(records)
        if issues:
            raise FeedMillValidationError(issues)
