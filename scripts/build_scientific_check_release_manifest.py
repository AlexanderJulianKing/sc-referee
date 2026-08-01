from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import canonical_json
from sc_referee.scientific_checks.profiles import (
    scientific_check_release_projection,
    scientific_check_release_registry,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "src" / "sc_referee" / "resources" / "scientific-check-manifests-v1" / "registry.json"
)


def main() -> None:
    projection = scientific_check_release_projection(scientific_check_release_registry())
    OUTPUT.write_text(canonical_json(projection) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
