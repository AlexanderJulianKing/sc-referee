"""Bind every checked-in file in this directory, except the manifest and caches."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.json"
SKIP_DIRECTORIES = {"__pycache__"}


def entries() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        if any(part in SKIP_DIRECTORIES for part in path.relative_to(ROOT).parts):
            continue
        payload = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }
        )
    return rows


def execute() -> dict[str, object]:
    rows = entries()
    manifest = {
        "schema": "multitest-v3.4-comprehension-iterator-prototype-manifest-v1",
        "file_count": len(rows),
        "files": rows,
    }
    MANIFEST.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    result = execute()
    total = sum(int(row["size_bytes"]) for row in result["files"])  # type: ignore[index]
    print(
        json.dumps(
            {
                "file_count": result["file_count"],
                "total_bytes": total,
                "manifest_sha256": "sha256:" + hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
            },
            indent=2,
            sort_keys=True,
        )
    )
