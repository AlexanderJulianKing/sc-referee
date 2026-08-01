from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_digest(data: bytes | str) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def semantic_digest(value: Mapping[str, Any] | Sequence[Any]) -> str:
    return sha256_digest(canonical_json(value))


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"
