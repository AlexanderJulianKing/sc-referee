#!/usr/bin/env python3
"""Create the canonical first production-Finding demonstration artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation/src"))

from sc_referee_evaluation.production_finding_demonstration import (  # noqa: E402
    build_production_finding_demonstration,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation/production-finding-demonstration-v1",
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=ROOT / "reference/schemas-v0.19.0",
    )
    args = parser.parse_args()
    record = build_production_finding_demonstration(
        args.output.resolve(), schema_root=args.schema_root.resolve()
    )
    print(record["record_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
