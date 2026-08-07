"""Seed the ADR-0068 calibration registry from retained calibration ledgers.

Calibration binds to (model id, pinned binary version, calibration suite) and
is reused across participant labels until one bound component changes. This
seeder records the already-executed six-vignette calibration passes as
registry entries pointing at their retained evidence ledgers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.lean_pipeline import (
    CALIBRATION_REGISTRY_RELATIVE,
    calibration_key,
)

from sc_referee.core.ids import canonical_json, semantic_digest

LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
SUITE = "six-vignette-v1"
BINARY_VERSION = "2.1.221"
# The retained v12 lean calibration: one Claude Fable 5 and one Claude Opus 5
# configuration, each 6/6 on the unchanged six-vignette suite.
V12_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v12-v120-lean"
MODEL_BY_PARTICIPANT = {
    "actor:v120-reviewer-fable-01": "claude-fable-5",
    "actor:v120-reviewer-opus-01": "claude-opus-5",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def seed_calibration_registry(project_root: Path) -> dict[str, Any]:
    registry_path = project_root / CALIBRATION_REGISTRY_RELATIVE
    if registry_path.exists():
        raise FileExistsError(f"Calibration registry already exists: {registry_path}")
    ledger_path = project_root / V12_RELATIVE / "CALIBRATION_LEDGER.json"
    ledger = _load(ledger_path)
    supplied = ledger.pop("ledger_digest", None)
    if supplied != semantic_digest(ledger):
        raise ValueError("The v12 calibration ledger does not replay.")
    ledger["ledger_digest"] = supplied
    entries = []
    for row in ledger["entries"]:
        participant_id = str(row["participant_id"])
        model_id = MODEL_BY_PARTICIPANT.get(participant_id)
        if model_id is None:
            continue
        if row.get("calibration_status") != "passed":
            raise ValueError(f"The v12 calibration for {participant_id} did not pass.")
        entries.append(
            {
                "key": calibration_key(model_id, BINARY_VERSION, SUITE),
                "model_id": model_id,
                "binary_version": BINARY_VERSION,
                "calibration_suite": SUITE,
                "passed": True,
                "evidence_ledger_digest": supplied,
                "evidence_relative_path": V12_RELATIVE.as_posix() + "/CALIBRATION_LEDGER.json",
                "source_participant_id": participant_id,
            }
        )
    if len(entries) != 2:
        raise ValueError("The v12 calibration ledger did not yield both model entries.")
    registry: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_calibration_registry",
        "registry_version": "1.0.0",
        "adr_reference": "ADR-0068-QUALIFICATION-PROCESS-CONSOLIDATION.md",
        "entries": sorted(entries, key=lambda item: str(item["key"])),
    }
    registry["registry_digest"] = semantic_digest(registry)
    registry_path.write_text(canonical_json(registry) + "\n", encoding="utf-8")
    return registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    registry = seed_calibration_registry(arguments.project_root.resolve())
    for entry in registry["entries"]:
        print(entry["key"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
