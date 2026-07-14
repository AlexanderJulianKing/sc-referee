"""Safe path and full-source-byte helpers."""
from __future__ import annotations

from pathlib import Path, PurePosixPath

from .digest import hash_file_bytes


def resolve_within(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("source path must be a non-empty relative path")
    lexical = PurePosixPath(relative_path)
    if lexical.is_absolute() or ".." in lexical.parts or lexical.as_posix() != relative_path:
        raise ValueError("source path must be canonical and relative")
    root = Path(root).resolve(strict=True)
    candidate = root.joinpath(*lexical.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("confirmed source is missing or unreadable") from exc
    if resolved != root and root not in resolved.parents:
        raise ValueError("confirmed source escapes ingestion root")
    if not resolved.is_file():
        raise ValueError("confirmed source must be one file")
    return resolved


def source_byte_hash(root: Path, relative_path: str) -> str:
    return hash_file_bytes(resolve_within(root, relative_path))
