"""Canonical, domain-separated identities for the fitted-row ledger."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import math
import struct
from types import MappingProxyType


POLICY_VERSION = "row-ledger-digest-v1"


def _length(value: int) -> bytes:
    return struct.pack("<Q", value)


def canonical_bytes(value) -> bytes:
    """Encode only closed, ordered values without Python equality collapses."""
    if value is None:
        return b"n"
    if isinstance(value, bool):
        return b"b\x01" if value else b"b\x00"
    if isinstance(value, int):
        raw = str(value).encode("ascii")
        return b"i" + _length(len(raw)) + raw
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float is not canonical")
        return b"f" + struct.pack("<d", value)
    if isinstance(value, str):
        raw = value.encode("utf-8")
        return b"s" + _length(len(raw)) + raw
    if isinstance(value, bytes):
        return b"y" + _length(len(value)) + value
    if isinstance(value, Enum):
        return b"e" + canonical_bytes(type(value).__qualname__) + canonical_bytes(value.value)
    if isinstance(value, tuple):
        return b"t" + _length(len(value)) + b"".join(canonical_bytes(item) for item in value)
    if isinstance(value, list):
        raise TypeError("lists must be frozen to tuples before canonicalization")
    if isinstance(value, (dict, MappingProxyType, set, frozenset)):
        raise TypeError("unordered values are not canonical")
    if is_dataclass(value) and not isinstance(value, type):
        encoded = [b"r", canonical_bytes(type(value).__qualname__), _length(len(fields(value)))]
        for field in fields(value):
            encoded.extend((canonical_bytes(field.name), canonical_bytes(getattr(value, field.name))))
        return b"".join(encoded)
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def ledger_digest(domain: str, value) -> str:
    if not isinstance(domain, str) or not domain:
        raise ValueError("digest domain must be a non-empty string")
    payload = canonical_bytes((POLICY_VERSION, domain, value))
    return "sha256:" + hashlib.sha256(payload).hexdigest()
