"""OME error contract (M8 Slice 2).

Deliberately small - six classes, one shallow base. No CrossTenantReference:
a tenant-scoped lookup that finds nothing must never distinguish "does not
exist" from "exists but belongs to another company" (Founder Correction 3),
so every not-found/invalid-reference case below is exactly that: not found
inside the caller's own company, full stop.
"""

from __future__ import annotations


class OMEError(Exception):
    """Base for all OME service errors."""


class ReceiptNotFound(OMEError):
    """No reasoning receipt exists for this id inside the caller's company."""


class DecisionNotFound(OMEError):
    """No decision memory exists for this id inside the caller's company."""


class OutcomeNotFound(OMEError):
    """No outcome memory exists for this id inside the caller's company."""


class InvalidSupersession(OMEError):
    """The row being superseded does not exist inside the caller's
    company, is not currently active, or the supersession could not be
    committed."""


class InvalidMemoryInput(OMEError):
    """Caller-supplied input failed validation: blank required text, an
    unsupported evidence type, a malformed id, an invalid result_state, an
    evidence/situation/file reference that does not resolve inside the
    caller's company, or a non-timezone-aware/future observed_at."""
