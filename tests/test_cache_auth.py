from __future__ import annotations

import secrets

import pytest

import sc_referee.cache_auth as cache_auth
from sc_referee.cache_auth import (
    CACHE_AUTHENTICATION_ENV,
    CACHE_AUTHENTICATION_PROFILE,
    EnvironmentOrPlatformCacheKeyProvider,
    InMemoryCacheKeyProvider,
    authenticate_cache_document,
    encode_cache_authentication_key,
    verify_cache_document,
)
from sc_referee.records.normalization import normalized_json_bytes


def test_authenticated_document_rejects_canonical_tamper_and_key_rotation() -> None:
    first = InMemoryCacheKeyProvider(secrets.token_bytes(32)).resolve().key
    second = InMemoryCacheKeyProvider(secrets.token_bytes(32)).resolve().key
    assert first is not None and second is not None
    content = {
        "cache_format": "test-cache-v1",
        "project_identity": "sha256:project",
        "payload": {"value": 1},
    }
    document = authenticate_cache_document(content, first)
    payload = normalized_json_bytes(document)

    assert verify_cache_document(payload, first) == content
    assert verify_cache_document(payload, second) is None

    document["payload"]["value"] = 2
    assert verify_cache_document(normalized_json_bytes(document), first) is None
    assert document["authentication"]["profile"] == CACHE_AUTHENTICATION_PROFILE
    assert first.secret not in payload


def test_explicit_environment_key_is_exact_and_invalid_input_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = secrets.token_bytes(32)
    monkeypatch.setenv(CACHE_AUTHENTICATION_ENV, encode_cache_authentication_key(secret))

    resolved = EnvironmentOrPlatformCacheKeyProvider().resolve()

    assert resolved.key is not None
    assert resolved.key.secret == secret
    assert resolved.key.provider_id == "environment"
    assert resolved.unavailable_reason is None

    monkeypatch.setenv(CACHE_AUTHENTICATION_ENV, "not-a-valid-key")
    rejected = EnvironmentOrPlatformCacheKeyProvider().resolve()
    assert rejected.key is None
    assert CACHE_AUTHENTICATION_ENV in str(rejected.unavailable_reason)


def test_macos_keychain_generation_keeps_secret_off_the_command_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], bytes | None]] = []
    responses = iter([None, b""])

    def fake_credential_command(
        command: list[str], *, input_bytes: bytes | None = None, accept_empty: bool = False
    ) -> bytes | None:
        calls.append((command, input_bytes))
        return next(responses)

    monkeypatch.setattr(cache_auth.os.path, "isfile", lambda value: True)
    monkeypatch.setattr(cache_auth.os, "access", lambda path, mode: True)
    monkeypatch.setattr(cache_auth, "_run_credential_command", fake_credential_command)

    resolved = cache_auth._resolve_macos_keychain()

    assert resolved.key is not None
    assert resolved.key.provider_id == "macos_keychain"
    assert calls[0][1] is None
    assert calls[1][0][-1] == "-w"
    assert calls[1][1] is not None
    assert resolved.key.secret not in b"\0".join(
        argument.encode("utf-8") for argument in calls[1][0]
    )
