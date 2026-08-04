from __future__ import annotations

from scripts.verify_handoff import verify_built_evaluation_wheel


def test_built_evaluation_wheel_contains_and_runs_v1_1_qualification() -> None:
    verify_built_evaluation_wheel()
