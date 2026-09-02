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


class ActionNotFound(OMEError):
    """No Action exists for this id inside the caller's company (M9 Slice 2)."""


class InvalidActionTransition(OMEError):
    """A status transition or reassignment was rejected because it is not
    a valid move from the Action's actual current state: an unlisted
    status transition, a self-transition, a mutation attempted on a
    terminal (completed/cancelled) Action, or a no-op reassignment
    (M9 Slice 2, Architecture Contract Sec 8 / Sec 7.5 / Sec 24.1)."""


class InvalidAssignee(OMEError):
    """The target assigned_user_id does not exist, has no active
    membership in the Action's company, or belongs to another company -
    resolves identically to a generic 404 (Architecture Contract Sec
    11.3), never distinguishing which case applied (M9 Slice 2)."""
