from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once

ASSIGNED_AT = "2026-08-04T18:10:00Z"
ASSIGNMENT_SEED = "selected-result-verifier-qualification-assignments-v1"
PROFILE_ID = "selected-result-verifier-qualification-profile:v1"
PROTOCOL_ID = "selection-protocol:selected-result-verifier-v1-precase"
BLOCKS = ("pilot", "held_out")
PROVIDERS = ("provider-family-1", "provider-family-2")
REPORT_PATHS = (
    "results/report.md",
    "outputs/final.txt",
    "artifacts/selected.md",
    "report/result.txt",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object: {path}")
    return value


def _case_id(protocol_digest: str, block: str, position: int) -> str:
    payload = f"{ASSIGNMENT_SEED}\0{protocol_digest}\0{block}\0{position}".encode()
    return "case:" + hashlib.sha256(payload).hexdigest()[:20]


def build_selected_result_verifier_qualification_assignments(
    freeze_root: Path,
    output: Path,
    *,
    assigned_at: str = ASSIGNED_AT,
) -> dict[str, Any]:
    """Freeze label-free, no-replacement assignments before any case is authored."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Qualification assignment output already exists: {output}")
    profile = _load(freeze_root / "qualification-profile.json")
    protocol = _load(freeze_root / "selection-protocol.json")
    manifest = _load(freeze_root / "FREEZE_MANIFEST.json")
    if (
        profile.get("profile_id") != PROFILE_ID
        or profile.get("profile_digest") != manifest.get("profile_digest")
        or protocol.get("artifact_id") != PROTOCOL_ID
        or protocol.get("content_digest") != manifest.get("selection_protocol_content_digest")
        or profile.get("selection_protocol")
        != {
            "artifact_id": protocol.get("artifact_id"),
            "content_digest": protocol.get("content_digest"),
        }
    ):
        raise ValueError("Selected-result qualification freeze does not replay.")
    payload = protocol.get("payload")
    if not isinstance(payload, dict) or payload.get("assignment_status") != "not_started":
        raise ValueError("Selected-result selection protocol is not pre-assignment.")
    if payload.get("cases_per_block") != 48 or payload.get("cases_per_provider_per_block") != 24:
        raise ValueError("Selected-result qualification case quotas have drifted.")

    frozen_blocks: list[dict[str, Any]] = []
    all_ids: set[str] = set()
    for block in BLOCKS:
        assignments: list[dict[str, Any]] = []
        for position in range(1, 49):
            case_id = _case_id(str(protocol["content_digest"]), block, position)
            if case_id in all_ids:
                raise ValueError("Opaque assignment case identities must be globally unique.")
            all_ids.add(case_id)
            assignments.append(
                {
                    "assignment_position": position,
                    "case_id": case_id,
                    "provider_slot": PROVIDERS[(position - 1) % len(PROVIDERS)],
                    "target_packet": {
                        "case_id": case_id,
                        "profile_id": profile["target_verifier"]["selected_result_profile"][
                            "profile_id"
                        ],
                        "selected_report_path": REPORT_PATHS[(position - 1) % len(REPORT_PATHS)],
                    },
                    "case_replacement_permitted": False,
                }
            )
        frozen_blocks.append(
            {
                "block": block,
                "status": "assigned_case_bytes_absent_and_sealed"
                if block == "held_out"
                else "assigned_case_bytes_absent",
                "assignments": assignments,
            }
        )

    result: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_opaque_assignments",
        "assignment_version": "1.0.0",
        "profile_ref": {
            "profile_id": profile["profile_id"],
            "profile_digest": profile["profile_digest"],
        },
        "selection_protocol_ref": {
            "artifact_id": protocol["artifact_id"],
            "content_digest": protocol["content_digest"],
        },
        "assignment_seed_digest": semantic_digest(ASSIGNMENT_SEED),
        "assignment_order_rule": (
            "map each provider's retained ordered submission to its provider-slot assignments in "
            "ascending assignment_position; never select or replace by state or target result"
        ),
        "assigned_at": assigned_at,
        "blocks": frozen_blocks,
        "case_count": 96,
        "case_replacement_permitted": False,
        "case_bytes_present": False,
        "oracle_states_present": False,
        "cell_labels_present": False,
        "oracle_proofs_present": False,
        "target_outputs_present": False,
        "qualification_authority": "none_assignment_only",
    }
    result["assignment_digest"] = semantic_digest(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze opaque selected-result verifier pilot and held-out assignments."
    )
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--freeze-root",
        type=Path,
        default=(
            project_root
            / "evaluation"
            / "qualification"
            / "selected-result-verifier-v1.0.0-precase"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assigned-at", default=ASSIGNED_AT)
    arguments = parser.parse_args()
    result = build_selected_result_verifier_qualification_assignments(
        arguments.freeze_root.resolve(),
        arguments.output.resolve(),
        assigned_at=arguments.assigned_at,
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
