"""Fail-closed safety guard for the isolated Playwright E2E database.

Refuses to let E2E orchestration (migrations, backend startup) touch
anything but an explicitly, unambiguously approved end-to-end database.
See M7 Slice 3B (Browser E2E Infrastructure).
"""
from __future__ import annotations

from urllib.parse import urlparse

_REQUIRED_MARKER = "e2e"


class UnsafeE2EDatabaseError(RuntimeError):
    """Raised when a candidate database URL is not safe for E2E setup."""


def assert_safe_e2e_database_url(candidate: str, ambient_default_url: str = "") -> None:
    """Fail closed unless `candidate` is clearly an approved E2E database.

    All of the following must hold, or this raises `UnsafeE2EDatabaseError`:
    - `candidate` is a non-empty, well-formed `postgres(ql)://` URL with a
      host and a database name (mirrors `Settings.validate_database_url`)
    - the database name contains the literal marker "e2e" (case-insensitive),
      so an operator must explicitly name the database as E2E-only rather
      than E2E setup silently accepting whatever URL happens to be present
    - `candidate` does not equal `ambient_default_url` (the operator's
      normal/default DATABASE_URL), so a misconfigured run can never fall
      back to migrating or restarting against the developer's real database
    """
    if not candidate or not candidate.strip():
        raise UnsafeE2EDatabaseError(
            "E2E_DATABASE_URL is required; refusing to run E2E database setup without it"
        )

    parsed = urlparse(candidate)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise UnsafeE2EDatabaseError(
            "E2E_DATABASE_URL must use a PostgreSQL URL starting with postgres:// or postgresql://"
        )

    dbname = parsed.path.strip("/")
    if not parsed.hostname or not dbname:
        raise UnsafeE2EDatabaseError("E2E_DATABASE_URL must include a host and database name")

    if _REQUIRED_MARKER not in dbname.lower():
        raise UnsafeE2EDatabaseError(
            f"Refusing to run E2E database setup against database {dbname!r}: "
            f'database name must clearly identify itself as an E2E database (must contain "{_REQUIRED_MARKER}")'
        )

    if ambient_default_url.strip() and candidate.strip() == ambient_default_url.strip():
        raise UnsafeE2EDatabaseError(
            "Refusing to run E2E database setup: E2E_DATABASE_URL is identical to the "
            "ambient DATABASE_URL; supply a distinct, isolated E2E database"
        )
