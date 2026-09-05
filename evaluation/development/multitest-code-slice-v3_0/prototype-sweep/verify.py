"""Replay and byte-verify the checked-in MT 3.0 prototype sweep."""

from __future__ import annotations

import hashlib
import json

from sweep import RESULTS, ROOT, execute


def main() -> None:
    expected = RESULTS.read_bytes()
    execute()
    observed = RESULTS.read_bytes()
    if observed != expected:
        raise AssertionError("prototype sweep replay bytes changed")
    manifest_path = ROOT / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in manifest["files"]:
        path = ROOT / row["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise AssertionError(f"manifest mismatch: {row['path']}")
    print(
        json.dumps(
            {
                "results_sha256": hashlib.sha256(observed).hexdigest(),
                "verified_files": len(manifest["files"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
