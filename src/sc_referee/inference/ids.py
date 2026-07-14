"""Deterministic identifiers derived only from source positions and local ordinals."""
from __future__ import annotations

from hashlib import sha256


def stable_id(kind: str, source_index: int, lineno: int, col: int,
              end_lineno: int, end_col: int, ordinal: int = 0) -> str:
    return f"{kind}:{source_index}:{lineno}:{col}:{end_lineno}:{end_col}:{ordinal}"


def content_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()

