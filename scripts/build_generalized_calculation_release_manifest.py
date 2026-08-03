from __future__ import annotations

import argparse
from pathlib import Path

from sc_referee.calculation_checks.profiles import (
    generalized_calculation_check_registry,
    generalized_calculation_release_projection,
)
from sc_referee.records.normalization import write_normalized_json_once

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "src" / "sc_referee" / "resources" / "calculation-check-manifests-v10" / "registry.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the generalized deterministic calculation-check registry"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Generalized calculation-check manifest already exists: {output}")
    write_normalized_json_once(
        output,
        generalized_calculation_release_projection(generalized_calculation_check_registry()),
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
