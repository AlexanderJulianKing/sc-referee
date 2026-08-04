from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once

FROZEN_AT = "2026-08-04T18:27:10Z"
CONTROLLER_DIGEST = "sha256:a298b7fe43ce30e4a00bd3d4e089a4e265c9d3094d0e930aabf1ebd80deb7cd3"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object: {path}")
    return value


def build_selected_result_verifier_runner_freeze(
    project_root: Path,
    pre_case_root: Path,
    assignments: Path,
    output: Path,
    *,
    frozen_at: str = FROZEN_AT,
) -> dict[str, Any]:
    """Freeze the target runner and comparison bytes before any target output exists."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Qualification runner freeze already exists: {output}")
    profile = _load(pre_case_root / "qualification-profile.json")
    assignment = _load(assignments)
    if (
        assignment.get("profile_ref")
        != {
            "profile_id": profile.get("profile_id"),
            "profile_digest": profile.get("profile_digest"),
        }
        or assignment.get("case_bytes_present") is not False
        or assignment.get("target_outputs_present") is not False
    ):
        raise ValueError("Opaque qualification assignments do not bind the frozen profile.")
    module = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "selected_result_verifier_qualification.py"
    )
    observed_digest = sha256_digest(module.read_bytes())
    if observed_digest != CONTROLLER_DIGEST:
        raise ValueError("Selected-result qualification controller has drifted.")
    result: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_runner_freeze",
        "runner_version": "1.0.1",
        "profile_ref": assignment["profile_ref"],
        "assignment_ref": {
            "assignment_digest": assignment["assignment_digest"],
            "case_count": assignment["case_count"],
        },
        "controller_module": {
            "path": module.relative_to(project_root).as_posix(),
            "content_digest": observed_digest,
            "entry_points": [
                "freeze_oracle_proof",
                "freeze_target_output",
                "freeze_verifier_comparison",
                "load_construction_certificate",
            ],
        },
        "chronology": {
            "oracle_proof_before_target_output": True,
            "target_output_before_comparison": True,
            "held_out_after_pilot_decision": True,
        },
        "target_input_allowlist": [
            "case_id",
            "profile_id",
            "selected_report_path",
            "validator_identity",
            "derived_at",
            "frozen_at",
            "case_bytes",
        ],
        "target_input_forbidden": [
            "construction_certificate",
            "oracle_state",
            "reason_codes",
            "positive_binding",
            "cell_label",
            "target_expectation",
        ],
        "comparison_outcomes": profile["comparison_outcomes"],
        "frozen_at": frozen_at,
        "target_outputs_present": False,
        "qualification_authority": "none_runner_freeze_only",
    }
    result["runner_freeze_digest"] = semantic_digest(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze the selected-result qualification runner before target execution."
    )
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--project-root", type=Path, default=project_root)
    parser.add_argument(
        "--pre-case-root",
        type=Path,
        default=(
            project_root
            / "evaluation"
            / "qualification"
            / "selected-result-verifier-v1.0.0-precase"
        ),
    )
    parser.add_argument("--assignments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frozen-at", default=FROZEN_AT)
    arguments = parser.parse_args()
    result = build_selected_result_verifier_runner_freeze(
        arguments.project_root.resolve(),
        arguments.pre_case_root.resolve(),
        arguments.assignments.resolve(),
        arguments.output.resolve(),
        frozen_at=arguments.frozen_at,
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
