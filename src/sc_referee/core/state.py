from __future__ import annotations

from enum import StrEnum

from .errors import InvalidTransitionError


class AuditState(StrEnum):
    CREATED = "created"
    SNAPSHOTTED = "snapshotted"
    INVENTORIED = "inventoried"
    PARSED = "parsed"
    SEMANTICS_PROPOSED = "semantics_proposed"
    AWAITING_ANSWERS = "awaiting_answers"
    SEMANTICS_RESOLVED = "semantics_resolved"
    SEMANTICS_LOCKED = "semantics_locked"
    DETECTED = "detected"
    REPORTED = "reported"
    COMPLETE = "complete"
    PARTIAL_DEADLINE = "partial_deadline"
    PARTIAL_HOST_LIMIT = "partial_host_limit"
    CANCELLED = "cancelled"
    FAILED_CONTROLLER = "failed_controller"


_TERMINAL = {
    AuditState.COMPLETE,
    AuditState.PARTIAL_DEADLINE,
    AuditState.PARTIAL_HOST_LIMIT,
    AuditState.CANCELLED,
    AuditState.FAILED_CONTROLLER,
}

_ALLOWED: dict[AuditState, set[AuditState]] = {
    AuditState.CREATED: {
        AuditState.SNAPSHOTTED,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.SNAPSHOTTED: {
        AuditState.INVENTORIED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.INVENTORIED: {
        AuditState.PARSED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.PARSED: {
        AuditState.SEMANTICS_PROPOSED,
        AuditState.SEMANTICS_LOCKED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.SEMANTICS_PROPOSED: {
        AuditState.AWAITING_ANSWERS,
        AuditState.SEMANTICS_RESOLVED,
        AuditState.SEMANTICS_LOCKED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.AWAITING_ANSWERS: {
        AuditState.SEMANTICS_RESOLVED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.SEMANTICS_RESOLVED: {
        AuditState.SEMANTICS_LOCKED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.SEMANTICS_LOCKED: {
        AuditState.DETECTED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.DETECTED: {
        AuditState.REPORTED,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
    AuditState.REPORTED: {
        AuditState.COMPLETE,
        AuditState.PARTIAL_DEADLINE,
        AuditState.PARTIAL_HOST_LIMIT,
        AuditState.CANCELLED,
        AuditState.FAILED_CONTROLLER,
    },
}


def transition(current: AuditState, target: AuditState) -> AuditState:
    if current in _TERMINAL:
        raise InvalidTransitionError(f"Cannot transition from terminal state {current}")
    if target not in _ALLOWED.get(current, set()):
        raise InvalidTransitionError(f"Illegal transition: {current} -> {target}")
    return target
