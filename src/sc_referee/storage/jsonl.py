from __future__ import annotations

import fcntl
import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json

from .atomic import fsync_directory

_RECORD_TYPE_FILENAMES = {"file_record": "files"}
_FILENAME_RECORD_TYPES = {value: key for key, value in _RECORD_TYPE_FILENAMES.items()}


class JsonlIntegrityError(ValueError):
    """Raised for torn, malformed, noncanonical, or misfiled JSONL records."""


class JsonlRecordStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, record_type: str) -> Path:
        filename = _RECORD_TYPE_FILENAMES.get(record_type, record_type.replace("_", "-"))
        return self.root / f"{filename}.jsonl"

    def append(self, record: Mapping[str, Any]) -> None:
        record_type = record.get("record_type")
        if not isinstance(record_type, str):
            raise ValueError("record_type is required")
        path = self._path(record_type)
        payload = (canonical_json(dict(record)) + "\n").encode("utf-8")
        existed = path.exists()
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            size_bytes = os.lseek(descriptor, 0, os.SEEK_END)
            if size_bytes > 0:
                read_descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                try:
                    final_byte = os.pread(read_descriptor, 1, size_bytes - 1)
                finally:
                    os.close(read_descriptor)
                if final_byte != b"\n":
                    raise JsonlIntegrityError(f"refusing to append after torn JSONL tail: {path}")
            _write_all(descriptor, payload)
            os.fsync(descriptor)
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        if not existed:
            fsync_directory(path.parent)

    def iter_records(self, record_type: str | None = None) -> Iterator[dict[str, Any]]:
        paths = [self._path(record_type)] if record_type else sorted(self.root.glob("*.jsonl"))
        for path in paths:
            if not path.exists():
                continue
            yield from _iter_verified_file(path)

    def verify_integrity(self) -> int:
        return sum(1 for _ in self.iter_records())


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("append-only JSONL write made no progress")
        offset += written


def _iter_verified_file(path: Path) -> Iterator[dict[str, Any]]:
    expected_type = _FILENAME_RECORD_TYPES.get(path.stem, path.stem.replace("-", "_"))
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.endswith(b"\n"):
                raise JsonlIntegrityError(f"torn JSONL tail at {path}:{line_number}")
            try:
                decoded = line[:-1].decode("utf-8")
                record = json.loads(decoded)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise JsonlIntegrityError(
                    f"malformed JSONL record at {path}:{line_number}"
                ) from error
            if not isinstance(record, dict):
                raise JsonlIntegrityError(f"JSONL record is not an object at {path}:{line_number}")
            if canonical_json(record) != decoded:
                raise JsonlIntegrityError(f"noncanonical JSONL record at {path}:{line_number}")
            if record.get("record_type") != expected_type:
                raise JsonlIntegrityError(
                    f"record type does not match JSONL path at {path}:{line_number}"
                )
            yield record
