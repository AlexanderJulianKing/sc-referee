"""Write the input-determined MT 3.3 prototype-sweep manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    paths = sorted(
        (
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.name != "MANIFEST.json" and "__pycache__" not in path.parts
        ),
        key=lambda path: path.relative_to(ROOT).as_posix().encode("utf-8"),
    )
    rows = []
    for path in paths:
        payload = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }
        )
    manifest = {
        "schema": "multitest-v3.3-terminal-presentation-prototype-manifest-v1",
        "file_count": len(rows),
        "files": rows,
    }
    (ROOT / "MANIFEST.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
