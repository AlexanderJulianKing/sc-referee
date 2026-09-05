"""Re-execute the MT 3.5 sweep and prove it reproduces the pinned bytes and digests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    frozen_results = (ROOT / "results.json").read_bytes()
    frozen_instrumentation = (ROOT / "instrument_results.json").read_bytes()
    from sweep import execute

    execute()
    if (ROOT / "results.json").read_bytes() != frozen_results:
        raise SystemExit("results.json did not reproduce byte-for-byte")
    if (ROOT / "instrument_results.json").read_bytes() != frozen_instrumentation:
        raise SystemExit("instrument_results.json did not reproduce byte-for-byte")
    mismatched = [
        name
        for name, digest in MANIFEST["files"].items()
        if _digest(ROOT / name) != digest
    ]
    if mismatched:
        raise SystemExit(f"manifest digests do not match: {mismatched}")
    payload = json.loads(frozen_results)
    print(
        json.dumps(
            {
                "cases": payload["case_count"],
                "fixtures": payload["fixture_count"],
                "movement_set": payload["movement_set"],
                "none_flip": payload["none_flip"],
                "admission_totals": payload["admission_totals"],
                "manifest_files": MANIFEST["file_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
