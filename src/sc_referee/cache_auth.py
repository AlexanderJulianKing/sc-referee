from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Protocol

from sc_referee.records.normalization import normalized_json_bytes

CACHE_AUTHENTICATION_PROFILE = "hmac_sha256_external_key_v1"
CACHE_AUTHENTICATION_ENV = "SC_REFEREE_CACHE_AUTH_KEY"
_KEY_BYTES = 32
_KEYCHAIN_SERVICE = "org.sc-referee.cache-auth.v1"
_KEYCHAIN_ACCOUNT = "default"


@dataclass(frozen=True)
class CacheAuthenticationKey:
    """A non-project cache key whose bytes must never enter durable audit records."""

    key_id: str
    secret: bytes
    provider_id: str

    def __post_init__(self) -> None:
        if len(self.secret) != _KEY_BYTES:
            raise ValueError("cache authentication keys must contain exactly 32 bytes")
        if not self.key_id.startswith("cache-key:") or len(self.key_id) != 34:
            raise ValueError("cache authentication key identifier is malformed")
        if not self.provider_id:
            raise ValueError("cache authentication provider identifier is required")


@dataclass(frozen=True)
class CacheKeyResolution:
    key: CacheAuthenticationKey | None
    unavailable_reason: str | None

    def __post_init__(self) -> None:
        if (self.key is None) == (self.unavailable_reason is None):
            raise ValueError("cache key resolution must contain exactly one outcome")


class CacheKeyProvider(Protocol):
    def resolve(self) -> CacheKeyResolution: ...


@dataclass(frozen=True)
class InMemoryCacheKeyProvider:
    """Injectable provider for tests and embedding; it never persists the supplied secret."""

    secret: bytes
    provider_id: str = "in_memory"

    def resolve(self) -> CacheKeyResolution:
        return CacheKeyResolution(
            key=_key_from_secret(self.secret, self.provider_id),
            unavailable_reason=None,
        )


@dataclass(frozen=True)
class UnavailableCacheKeyProvider:
    """Explicit fail-closed provider used when an embedding forbids persistent cache reuse."""

    reason: str = "No cache authentication credential was supplied."

    def resolve(self) -> CacheKeyResolution:
        return CacheKeyResolution(key=None, unavailable_reason=self.reason)


@dataclass(frozen=True)
class EnvironmentOrPlatformCacheKeyProvider:
    """Resolve an explicit CI key, then a supported platform credential store."""

    def resolve(self) -> CacheKeyResolution:
        supplied = os.environ.get(CACHE_AUTHENTICATION_ENV)
        if supplied is not None:
            secret = _decode_secret(supplied)
            if secret is None:
                return CacheKeyResolution(
                    key=None,
                    unavailable_reason=(
                        f"{CACHE_AUTHENTICATION_ENV} must be URL-safe base64 for exactly "
                        "32 key bytes."
                    ),
                )
            return CacheKeyResolution(
                key=_key_from_secret(secret, "environment"),
                unavailable_reason=None,
            )
        if os.environ.get("CI", "").lower() in {"1", "true", "yes"}:
            return CacheKeyResolution(
                key=None,
                unavailable_reason=(
                    f"Headless CI requires an explicit {CACHE_AUTHENTICATION_ENV} credential."
                ),
            )
        if sys.platform == "darwin":
            return _resolve_macos_keychain()
        if sys.platform.startswith("linux"):
            return _resolve_linux_secret_service()
        return CacheKeyResolution(
            key=None,
            unavailable_reason="No supported platform credential store is available.",
        )


def authenticate_cache_document(
    content: dict[str, Any], key: CacheAuthenticationKey
) -> dict[str, Any]:
    """Return a canonicalizable HMAC envelope without exposing key bytes."""

    authentication = {
        "profile": CACHE_AUTHENTICATION_PROFILE,
        "key_id": key.key_id,
        "mac": _cache_mac(content, key),
    }
    return {**content, "authentication": authentication}


def verify_cache_document(payload: bytes, key: CacheAuthenticationKey) -> dict[str, Any] | None:
    """Authenticate normalized outer bytes before a caller consumes scientific payload fields."""

    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or normalized_json_bytes(value) != payload:
        return None
    authentication = value.get("authentication")
    if not isinstance(authentication, dict):
        return None
    if (
        authentication.get("profile") != CACHE_AUTHENTICATION_PROFILE
        or authentication.get("key_id") != key.key_id
        or not isinstance(authentication.get("mac"), str)
    ):
        return None
    content = {name: child for name, child in value.items() if name != "authentication"}
    if not hmac.compare_digest(str(authentication["mac"]), _cache_mac(content, key)):
        return None
    return content


def encode_cache_authentication_key(secret: bytes) -> str:
    """Encode an exact 32-byte key for the explicit headless/CI environment contract."""

    if len(secret) != _KEY_BYTES:
        raise ValueError("cache authentication keys must contain exactly 32 bytes")
    return base64.urlsafe_b64encode(secret).decode("ascii")


def _cache_mac(content: dict[str, Any], key: CacheAuthenticationKey) -> str:
    message = normalized_json_bytes(
        {
            "profile": CACHE_AUTHENTICATION_PROFILE,
            "key_id": key.key_id,
            "content": content,
        }
    )
    return "sha256:" + hmac.new(key.secret, message, hashlib.sha256).hexdigest()


def _key_from_secret(secret: bytes, provider_id: str) -> CacheAuthenticationKey:
    identifier = hashlib.sha256(b"sc-referee-cache-key-id-v1\0" + secret).hexdigest()[:24]
    return CacheAuthenticationKey(
        key_id=f"cache-key:{identifier}",
        secret=secret,
        provider_id=provider_id,
    )


def _decode_secret(value: str) -> bytes | None:
    if len(value) > 256:
        return None
    try:
        secret = base64.b64decode(value, altchars=b"-_", validate=True)
    except (ValueError, binascii.Error):
        return None
    return secret if len(secret) == _KEY_BYTES else None


def _resolve_macos_keychain() -> CacheKeyResolution:
    executable = "/usr/bin/security"
    if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
        return CacheKeyResolution(
            key=None,
            unavailable_reason="The macOS Keychain command is unavailable.",
        )
    existing = _run_credential_command(
        [
            executable,
            "find-generic-password",
            "-a",
            _KEYCHAIN_ACCOUNT,
            "-s",
            _KEYCHAIN_SERVICE,
            "-w",
        ]
    )
    if existing is not None:
        secret = _decode_secret(existing.decode("ascii", errors="ignore").strip())
        if secret is None:
            return CacheKeyResolution(
                key=None,
                unavailable_reason="The macOS Keychain cache credential is malformed.",
            )
        return CacheKeyResolution(
            key=_key_from_secret(secret, "macos_keychain"),
            unavailable_reason=None,
        )
    generated = secrets.token_bytes(_KEY_BYTES)
    encoded = encode_cache_authentication_key(generated).encode("ascii") + b"\n"
    stored = _run_credential_command(
        [
            executable,
            "add-generic-password",
            "-a",
            _KEYCHAIN_ACCOUNT,
            "-s",
            _KEYCHAIN_SERVICE,
            "-D",
            "application password",
            "-l",
            "sc-referee project-cache authentication",
            "-w",
        ],
        input_bytes=encoded,
        accept_empty=True,
    )
    if stored is None:
        return CacheKeyResolution(
            key=None,
            unavailable_reason="A macOS Keychain cache credential could not be created.",
        )
    return CacheKeyResolution(
        key=_key_from_secret(generated, "macos_keychain"),
        unavailable_reason=None,
    )


def _resolve_linux_secret_service() -> CacheKeyResolution:
    executable = shutil.which("secret-tool")
    if executable is None:
        return CacheKeyResolution(
            key=None,
            unavailable_reason="The Linux Secret Service client is unavailable.",
        )
    existing = _run_credential_command(
        [executable, "lookup", "service", "sc-referee", "purpose", "cache-auth-v1"]
    )
    if existing is not None:
        secret = _decode_secret(existing.decode("ascii", errors="ignore").strip())
        if secret is None:
            return CacheKeyResolution(
                key=None,
                unavailable_reason="The Linux Secret Service cache credential is malformed.",
            )
        return CacheKeyResolution(
            key=_key_from_secret(secret, "linux_secret_service"),
            unavailable_reason=None,
        )
    generated = secrets.token_bytes(_KEY_BYTES)
    stored = _run_credential_command(
        [
            executable,
            "store",
            "--label=sc-referee project-cache authentication",
            "service",
            "sc-referee",
            "purpose",
            "cache-auth-v1",
        ],
        input_bytes=encode_cache_authentication_key(generated).encode("ascii") + b"\n",
        accept_empty=True,
    )
    if stored is None:
        return CacheKeyResolution(
            key=None,
            unavailable_reason="A Linux Secret Service cache credential could not be created.",
        )
    return CacheKeyResolution(
        key=_key_from_secret(generated, "linux_secret_service"),
        unavailable_reason=None,
    )


def _run_credential_command(
    command: list[str], *, input_bytes: bytes | None = None, accept_empty: bool = False
) -> bytes | None:
    try:
        completed = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0 or (not accept_empty and not completed.stdout.strip()):
        return None
    return completed.stdout
