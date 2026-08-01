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


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def schema_root(project_root: Path) -> Path:
    return project_root / "reference" / "schemas-v0.18.0"
