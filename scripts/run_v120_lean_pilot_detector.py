from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, cast

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.method_contract_run import run_method_contract
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)
from scripts.build_v120_lean_pilot_authoring import V120_AUTHORING_RELATIVE
from scripts.build_v120_lean_review import V120_REVIEW_RELATIVE
from scripts.freeze_v120_lean_pilot_labels import V120_LABELS_RELATIVE
from scripts.run_record_v120_lean_review import _protocol as _review_protocol
from scripts.run_v120_lean_pilot_authors import PROTOCOL_DIGEST as AUTHORING_PROTOCOL_DIGEST

V120_DETECTOR_RUN_RELATIVE = V120_REVIEW_RELATIVE.parent / "pilot-v120-lean-detector-run-three-case"
ADR_0066 = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
ADR_0067 = "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md"
LABEL_LEDGER_DIGEST = "sha256:d5de03da75dc81ab89e4f7895f2cb19703ca2eb8199500110af21244dc2b8cd0"
CHECK_ID = "check:complete-domain-exposure-denominator"
CHECK_VERSION = "1.2.0"
DETECTOR_ID = "detector:bounded-analysis-method-conflict"
CONFLICTING_OPERAND = "retained_observed_subset_exposure_only"
RUN_AT = "2026-08-07T21:41:30Z"

# The scientist-authorized requirement for each case is the frozen v120 brief's
# declared target: the error-bearing and corrected-twin briefs declare the
# complete planned unit set as the target; the valid-alternative brief declares
# the retained post-screening subset as the explicit target.
CANDIDATE_BY_ROLE = {
    "error_bearing": "complete-declared-domain-exposure",
    "corrected_twin": "complete-declared-domain-exposure",
    "valid_alternative": "retained-observed-subset-exposure",
}
EXPECTED_LABEL_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "valid_alternative": "verified_good_eligible",
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay_digest(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _check_results(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for result in bundle.get("detector_results", []):
        if result.get("detector_id") != DETECTOR_ID:
            continue
        ledger = next(
            (
                item
                for item in result.get("evidence", [])
                if item.get("evidence_id") == "evidence:analysis-method-ledger"
            ),
            None,
        )
        if ledger is not None:
            results.append(result)
    return results


def run_v120_lean_pilot_detector(project_root: Path) -> dict[str, Any]:
    output_root = project_root / V120_DETECTOR_RUN_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Detector-run output already exists: {output_root}")
    schema_root = project_root / "reference/schemas-v0.18.0"

    authoring = _load(project_root / V120_AUTHORING_RELATIVE / "PILOT_AUTHORING_PROTOCOL.json")
    _replay_digest(
        authoring,
        "protocol_digest",
        cast(str, AUTHORING_PROTOCOL_DIGEST),
        "The v120 authoring protocol",
    )
    detector_tuple = authoring["detector_tuple"]
    if detector_tuple["check_version"] != CHECK_VERSION:
        raise ValueError("The v120 authoring protocol does not bind detector v1.2.0.")
    profiles_path = project_root / str(detector_tuple["profile_source_path"])
    if sha256_digest(profiles_path.read_bytes()) != detector_tuple["profile_source_digest"]:
        raise ValueError("The current profile source drifted from the frozen v1.2.0 binding.")
    roles = {
        str(case_id): str(role) for case_id, role in authoring["case_role_assignments"].items()
    }

    label_ledger = _load(project_root / V120_LABELS_RELATIVE / "SCIENTIFIC_LABEL_LEDGER.json")
    _replay_digest(
        label_ledger, "ledger_digest", LABEL_LEDGER_DIGEST, "The v120 scientific-label ledger"
    )
    if label_ledger["detector_output_observed"] is not False:
        raise ValueError("The v120 labels were not frozen before detector observation.")
    labels_by_case = {str(row["case_id"]): row for row in label_ledger["entries"]}
    for case_id, role in roles.items():
        if labels_by_case[case_id]["label_status"] != EXPECTED_LABEL_BY_ROLE[role]:
            raise ValueError("The frozen v120 labels do not match the role expectation map.")

    review_protocol = _review_protocol(project_root)
    bindings = {str(item["case_id"]): item for item in review_protocol["source_case_bindings"]}
    if sorted(bindings) != sorted(roles):
        raise ValueError("The v120 review bindings do not cover the exact authored cases.")

    output_root.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    try:
        for case_id in sorted(roles):
            slug = case_id.removeprefix("case:")
            role = roles[case_id]
            binding = bindings[case_id]
            workspace_root = project_root / str(binding["source_workspace_relative_path"])
            case_root = output_root / "runs" / slug
            repository = case_root / "project"
            repository.mkdir(parents=True)
            for path_value, digest in sorted(dict(binding["visible_content_digests"]).items()):
                content = (workspace_root / path_value).read_bytes()
                if sha256_digest(content) != digest:
                    raise ValueError(f"Workspace bytes drifted for {case_id} {path_value}.")
                destination = repository / path_value
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)

            contract = run_method_contract(
                repository,
                "task.md",
                case_root / "contract",
                schema_root,
                profile={
                    "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
                    "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                    "check_id": CHECK_ID,
                    "candidate_id": CANDIDATE_BY_ROLE[role],
                },
                actor_id="scientist:frozen-v120-lean-brief-v5",
            )
            if contract["findings"]:
                raise ValueError(f"The method-contract step emitted findings for {case_id}.")
            lock_path = case_root / "contract" / "semantic.lock.json"

            bundle = run_audit(
                repository,
                case_root / "audit",
                schema_root,
                report="results/report.md",
                method_contract_lock=lock_path,
            )
            replayed = replay(
                case_root / "audit" / "semantic.lock.json", case_root / "replay", schema_root
            )
            if replayed["detector_results"] != bundle["detector_results"]:
                raise ValueError(f"The detector run does not replay for {case_id}.")

            check_results = _check_results(bundle)
            fired = [
                result
                for result in check_results
                if result.get("state") == "evaluation_finding_candidate"
            ]
            operands = [
                next(
                    item
                    for item in result["evidence"]
                    if item["evidence_id"] == "evidence:analysis-method-ledger"
                )["observed_value"].get("observed")
                for result in fired
            ]
            localizations = [
                {
                    "result_id": result["result_id"],
                    "state": result["state"],
                    "observed_operand": operand,
                    "source_refs": [
                        {
                            "path": ref.get("path"),
                            "start_line": ref.get("start_line"),
                            "end_line": ref.get("end_line"),
                        }
                        for item in result.get("evidence", [])
                        for ref in item.get("source_refs", [])
                    ],
                }
                for result, operand in zip(fired, operands, strict=True)
            ]

            label_status = str(labels_by_case[case_id]["label_status"])
            detector_positive = bool(fired)
            expected_positive = label_status == "positive_demonstrated"
            outcome = (
                "true_positive"
                if detector_positive and expected_positive
                else "false_accusation"
                if detector_positive and not expected_positive
                else "missed_error"
                if not detector_positive and expected_positive
                else "true_negative"
            )
            rows.append(
                {
                    "case_id": case_id,
                    "case_role": role,
                    "frozen_label_status": label_status,
                    "frozen_review_digest": labels_by_case[case_id]["review_digest"],
                    "contract_candidate_id": CANDIDATE_BY_ROLE[role],
                    "detector_result_count": len(check_results),
                    "finding_candidate_count": len(fired),
                    "detector_positive": detector_positive,
                    "comparison_outcome": outcome,
                    "localizations": localizations,
                    "production_findings": len(bundle.get("findings", [])),
                    "project_code_executions": len(bundle.get("executions", [])),
                    "audit_lock_digest": sha256_digest(
                        (case_root / "audit" / "semantic.lock.json").read_bytes()
                    ),
                    "replay_equal": True,
                }
            )

        outcomes = [str(row["comparison_outcome"]) for row in rows]
        metrics = {
            "opportunity_count": len(rows),
            "true_positive_count": outcomes.count("true_positive"),
            "true_negative_count": outcomes.count("true_negative"),
            "false_accusation_count": outcomes.count("false_accusation"),
            "missed_error_count": outcomes.count("missed_error"),
            "sensitivity": (
                outcomes.count("true_positive")
                / max(1, outcomes.count("true_positive") + outcomes.count("missed_error"))
            ),
            "false_accusation_rate": (
                outcomes.count("false_accusation")
                / max(
                    1,
                    outcomes.count("false_accusation") + outcomes.count("true_negative"),
                )
            ),
            "precision": (
                outcomes.count("true_positive")
                / max(
                    1,
                    outcomes.count("true_positive") + outcomes.count("false_accusation"),
                )
            ),
        }
        ledger: dict[str, Any] = {
            "artifact_kind": "direct_qualification_v120_lean_detector_run_ledger",
            "ledger_version": "1.0.0",
            "adr_references": [ADR_0066, ADR_0067],
            "authoring_protocol_digest": AUTHORING_PROTOCOL_DIGEST,
            "detector_tuple_digest": authoring["detector_tuple_digest"],
            "scientific_label_ledger_digest": LABEL_LEDGER_DIGEST,
            "labels_frozen_before_detector_observation": True,
            "check_id": CHECK_ID,
            "check_version": CHECK_VERSION,
            "detector_id": DETECTOR_ID,
            "expected_conflicting_operand": CONFLICTING_OPERAND,
            "requirement_profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "requirement_profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "entries": rows,
            "pilot_metrics": metrics,
            "production_finding_count": sum(int(row["production_findings"]) for row in rows),
            "project_code_executed": False,
            "deterministic_replay_verified": True,
            "scientific_label_count": 0,
            "detector_outcome_count": len(rows),
            "run_at": RUN_AT,
            "qualification_authority": "none_pilot_detector_run_only",
        }
        ledger["ledger_digest"] = semantic_digest(ledger)
        write_normalized_json_once(output_root / "DETECTOR_RUN_LEDGER.json", ledger)
        return ledger
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    ledger = run_v120_lean_pilot_detector(arguments.project_root.resolve())
    print(json.dumps(ledger["pilot_metrics"], sort_keys=True))
    for row in ledger["entries"]:
        print(row["case_id"], row["case_role"], "->", row["comparison_outcome"])
    print(ledger["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
