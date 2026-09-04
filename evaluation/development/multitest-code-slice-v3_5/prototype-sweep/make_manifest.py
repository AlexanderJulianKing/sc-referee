"""Bind every file in this directory except the manifest itself and interpreter caches."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.json"


def main() -> None:
    files: dict[str, str] = {}
    total = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path == MANIFEST or "__pycache__" in path.parts or path.name.endswith(".pyc"):
            continue
        payload = path.read_bytes()
        total += len(payload)
        files[path.relative_to(ROOT).as_posix()] = "sha256:" + hashlib.sha256(payload).hexdigest()
    MANIFEST.write_text(
        json.dumps(
            {
                "schema": "multitest-v3.5-prototype-sweep-manifest-v1",
                "file_count": len(files),
                "total_bytes": total,
                "files": files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{len(files)} files, {total} bytes")


if __name__ == "__main__":
    main()
