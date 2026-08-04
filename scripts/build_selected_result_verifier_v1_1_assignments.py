from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once

ASSIGNED_AT = "2026-08-04T22:00:00Z"
ASSIGNMENT_SEED = "selected-result-verifier-qualification-assignments-v1.1"
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


def _self_digested(value: dict[str, Any], digest_field: str) -> dict[str, Any]:
    result = dict(value)
    supplied = result.pop(digest_field, None)
    if supplied != semantic_digest(result):
        raise ValueError(f"{digest_field} does not replay.")
    result[digest_field] = supplied
    return result


def _case_id(contract_digest: str, block: str, position: int) -> str:
    payload = f"{ASSIGNMENT_SEED}\0{contract_digest}\0{block}\0{position}".encode()
    return "case:" + hashlib.sha256(payload).hexdigest()[:20]


def build_selected_result_verifier_v1_1_assignments(
    semantic_contract_path: Path,
    output: Path,
    *,
    assigned_at: str = ASSIGNED_AT,
) -> dict[str, Any]:
    """Freeze new label-free v1.1 assignments before case authoring."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Qualification assignment output already exists: {output}")
    contract = _self_digested(_load(semantic_contract_path), "contract_digest")
    matrix = contract.get("block_matrix")
    if (
        contract.get("artifact_kind") != "selected_result_verifier_semantic_review_contract"
        or contract.get("contract_version") != "1.1.0"
        or contract.get("qualification_authority") != "none_semantic_review_contract_only"
        or not isinstance(matrix, dict)
        or matrix.get("cases_per_block") != 48
        or matrix.get("cases_per_provider_per_block") != 24
        or matrix.get("replacement_permitted") is not False
    ):
        raise ValueError("Semantic review contract is not the v1.1 pre-case contract.")

    frozen_blocks: list[dict[str, Any]] = []
    all_ids: set[str] = set()
    for block in BLOCKS:
        assignments: list[dict[str, Any]] = []
        for position in range(1, 49):
            case_id = _case_id(str(contract["contract_digest"]), block, position)
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
                        "profile_id": contract["target_profile_id"],
                        "selected_report_path": REPORT_PATHS[(position - 1) % len(REPORT_PATHS)],
                    },
                    "case_replacement_permitted": False,
                }
            )
        frozen_blocks.append(
            {
                "block": block,
                "status": (
                    "assigned_case_bytes_absent_and_sealed"
                    if block == "held_out"
                    else "assigned_case_bytes_absent"
                ),
                "assignments": assignments,
            }
        )

    result: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_opaque_assignments",
        "assignment_version": "1.1.0",
        "semantic_review_contract_ref": {
            "contract_version": contract["contract_version"],
            "contract_digest": contract["contract_digest"],
        },
        "target_profile_id": contract["target_profile_id"],
        "assignment_seed_digest": semantic_digest(ASSIGNMENT_SEED),
        "assignment_order_rule": (
            "map each provider's retained ordered submission to its provider-slot assignments in "
            "ascending assignment_position; never select or replace by state, review, or target result"
        ),
        "assigned_at": assigned_at,
        "blocks": frozen_blocks,
        "case_count": 96,
        "case_replacement_permitted": False,
        "case_bytes_present": False,
        "oracle_states_present": False,
        "cell_labels_present": False,
        "semantic_attestations_present": False,
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
        description="Freeze v1.1 selected-result verifier pilot and held-out assignments."
    )
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--semantic-contract",
        type=Path,
        default=(
            project_root
            / "evaluation"
            / "qualification"
            / "selected-result-verifier-v1.1.0-precase"
            / "semantic-review-contract.json"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assigned-at", default=ASSIGNED_AT)
    arguments = parser.parse_args()
    result = build_selected_result_verifier_v1_1_assignments(
        arguments.semantic_contract.resolve(),
        arguments.output.resolve(),
        assigned_at=arguments.assigned_at,
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
