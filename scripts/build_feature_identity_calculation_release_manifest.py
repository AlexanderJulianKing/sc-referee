from __future__ import annotations

from pathlib import Path

from sc_referee.calculation_checks.profiles import (
    feature_identity_calculation_check_registry,
    feature_identity_calculation_release_projection,
)
from sc_referee.core.ids import canonical_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "src" / "sc_referee" / "resources" / "calculation-check-manifests-v13" / "registry.json"
)


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(
            f"Feature-identity calculation-check manifest already exists: {OUTPUT}"
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    value = feature_identity_calculation_release_projection(
        feature_identity_calculation_check_registry()
    )
    OUTPUT.write_text(canonical_json(value) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
