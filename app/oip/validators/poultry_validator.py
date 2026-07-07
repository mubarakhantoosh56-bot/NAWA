"""Validation rules for normalized poultry operational records."""

from __future__ import annotations

from dataclasses import dataclass

from app.oip.models.operational_record import PoultryOperationalRecord


@dataclass(frozen=True)
class ValidationIssue:
    """One validation issue found in a normalized record."""

    row_number: int
    field_name: str
    message: str


class PoultryValidationError(ValueError):
    """Raised when poultry records fail OIP validation."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        details = "; ".join(
            f"row {issue.row_number} {issue.field_name}: {issue.message}"
            for issue in issues
        )
        super().__init__(details)


class PoultryValidator:
    """Validate the first foundation rules for Dairtna poultry records."""

    def validate(self, records: list[PoultryOperationalRecord]) -> list[ValidationIssue]:
        """Return all validation issues without mutating records."""
        issues: list[ValidationIssue] = []
        for record in records:
            issues.extend(self._validate_record(record))
        return issues

    def validate_or_raise(self, records: list[PoultryOperationalRecord]) -> None:
        """Raise PoultryValidationError when any record is invalid."""
        issues = self.validate(records)
        if issues:
            raise PoultryValidationError(issues)

    def _validate_record(self, record: PoultryOperationalRecord) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if record.date is None:
            issues.append(_issue(record, "date", "date must exist"))
        if record.bird_balance is None or record.bird_balance <= 0:
            issues.append(_issue(record, "bird_balance", "bird balance must be positive"))
        for field_name in ("daily_mortality", "weekly_mortality"):
            value = getattr(record, field_name)
            if value is not None and value < 0:
                issues.append(_issue(record, field_name, "mortality cannot be negative"))
        for field_name in ("daily_production_rate", "standard_production_rate"):
            value = getattr(record, field_name)
            if value is not None and not 0 <= value <= 100:
                issues.append(_issue(record, field_name, "production rate must be between 0 and 100"))
        return issues


def _issue(record: PoultryOperationalRecord, field_name: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        row_number=record.row_number,
        field_name=field_name,
        message=message,
    )

