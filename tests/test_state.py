import pytest

from sc_referee.core.errors import InvalidTransitionError
from sc_referee.core.state import AuditState, transition


def test_legal_transition() -> None:
    assert transition(AuditState.CREATED, AuditState.SNAPSHOTTED) is AuditState.SNAPSHOTTED


def test_terminal_state_cannot_transition() -> None:
    with pytest.raises(InvalidTransitionError):
        transition(AuditState.COMPLETE, AuditState.CREATED)


@pytest.mark.parametrize(
    "state",
    [
        AuditState.CREATED,
        AuditState.SNAPSHOTTED,
        AuditState.INVENTORIED,
        AuditState.PARSED,
        AuditState.SEMANTICS_LOCKED,
        AuditState.DETECTED,
        AuditState.REPORTED,
    ],
)
@pytest.mark.parametrize(
    "terminal",
    [AuditState.PARTIAL_HOST_LIMIT, AuditState.CANCELLED, AuditState.FAILED_CONTROLLER],
)
def test_control_terminal_states_are_legal_from_every_active_state(state, terminal) -> None:
    assert transition(state, terminal) is terminal
