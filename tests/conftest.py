import secrets
from pathlib import Path

import pytest

from sc_referee.cache_auth import CACHE_AUTHENTICATION_ENV, encode_cache_authentication_key


@pytest.fixture(autouse=True)
def isolated_cache_authentication_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests and their subprocesses out of the user's platform credential store."""

    monkeypatch.setenv(
        CACHE_AUTHENTICATION_ENV,
        encode_cache_authentication_key(secrets.token_bytes(32)),
    )


@pytest.fixture(autouse=True)
def pin_frozen_stage1_projection_schema(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replay frozen Stage-1 controllers with the v0.20 record version they bind."""

    if request.path.name not in {
        "test_first_direct_three_case_stage1_codex_recovery.py",
        "test_first_direct_three_case_stage1_protocol.py",
        "test_first_direct_three_case_stage1_semantic_recovery_clean_recorder.py",
        "test_first_direct_three_case_stage1_semantic_recovery_recorder.py",
    }:
        return
    from sc_referee_evaluation import review_semantic_payload

    monkeypatch.setattr(review_semantic_payload, "SCHEMA_VERSION", "0.20.0")


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def schema_root(project_root: Path) -> Path:
    return project_root / "reference" / "schemas-v0.21.0"
