"""Re-execute and byte-verify the checked-in MT 3.2 AP prototype sweep."""

from __future__ import annotations

import hashlib
import json

from sweep import RESULTS, ROOT, execute


def main() -> None:
    expected = RESULTS.read_bytes()
    execute()
    observed = RESULTS.read_bytes()
    if observed != expected:
        raise AssertionError("MT 3.2 prototype replay bytes changed")
    manifest_path = ROOT / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = {row["path"]: row for row in manifest["files"]}
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json" and "__pycache__" not in path.parts
    }
    if set(rows) != actual_paths:
        raise AssertionError("MT 3.2 manifest inventory changed")
    for relative, row in rows.items():
        payload = (ROOT / relative).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise AssertionError(f"manifest digest mismatch: {relative}")
        if len(payload) != row["size_bytes"]:
            raise AssertionError(f"manifest size mismatch: {relative}")
    print(
        json.dumps(
            {
                "results_sha256": hashlib.sha256(observed).hexdigest(),
                "verified_files": len(rows),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
