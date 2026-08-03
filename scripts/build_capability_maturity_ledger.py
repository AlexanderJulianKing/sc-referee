from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sc_referee.capability_maturity_ledger import (  # noqa: E402
    build_capability_maturity_ledger,
    default_capability_maturity_source_root,
)
from sc_referee.core.ids import canonical_json  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the private capability maturity ledger")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/implementation/CAPABILITY_MATURITY_LEDGER.json"),
    )
    args = parser.parse_args()
    ledger = build_capability_maturity_ledger(default_capability_maturity_source_root())
    args.output.write_text(canonical_json(ledger) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
