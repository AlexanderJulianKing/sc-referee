from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee.storage.atomic import atomic_create_bytes, atomic_write_bytes


def normalized_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def write_normalized_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, normalized_json_bytes(value))


def write_normalized_json_once(path: Path, value: Any) -> None:
    """Create canonical JSON atomically and refuse every pre-existing path."""

    atomic_create_bytes(path, normalized_json_bytes(value))
