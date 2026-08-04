from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.analysis_method_qualification import freeze_protocol_artifact

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_create_bytes

FROZEN_AT = "2026-08-04T18:02:51Z"
TARGET_VERSION = "1.0.0"
TARGET_PROFILE_ID = "selected-result-profile:python-static-marked-report-v1"
TARGET_PROFILE_DIGEST = "sha256:12478b6b21fb12be7388a7a570adadd8ffc68ea09ab2803074dfc77feb6699d0"
TARGET_SOURCE_DIGEST = "sha256:d34ad9b7a85bf78840fb9109bd764a26e5a25a4e89484ce2788436120ead7eac"
PROFILE_ID = "selected-result-verifier-qualification-profile:v1"
PROTOCOL_ID = "selection-protocol:selected-result-verifier-v1-precase"

TARGET_PROFILE: dict[str, Any] = {
    "candidate_enumeration": "all-strict-utf8-python-files-in-complete-case-tree",
    "case_file_roles": "every-file-is-python-producer-selected-report-or-rederived-operand",
    "dynamic_or_unparsed_flow": "unsupported",
    "module_statement_budget": "64-top-level-statements",
    "non_python_source_artifacts": "unsupported",
    "operand_grammar": "finite-static-python-expression-evaluation-v1",
    "producer_grammar": "python-path-literal-write-text-v1",
    "profile_id": TARGET_PROFILE_ID,
    "profile_version": "1.0.0",
    "python_source_budget": "1048576-bytes-and-50000-ast-nodes",
    "python_source_encoding": "default-utf8-without-bom-or-pep263-cookie",
    "selected_report_role": "nonexecutable-nonshebang-ascii-lf-md-or-txt-v1",
    "selected_result_grammar": "one-or-more-exact-prefixed-report-lines",
    "selected_result_prefix": "[selected-result]",
    "source_operand_grammar": "nonexecutable-nonshebang-ascii-lf-csv-or-tsv-v1",
    "static_evaluation_budget": "100000-steps-10485760-value-bytes-4096-integer-bits",
    "text_line_budget": "10000-lines-before-splitting",
    "tree_budgets": "32-files-32-directories-64-entries-depth-8",
    "writer_payload": "exact-retained-report-byte-equality-and-source-operand-required",
    "writer_scope": "unconditional-module-level-only",
}

CASE_AUTHOR_PROMPT = """Create only the assigned selected-result conformance case and its typed construction certificate. Follow the frozen profile and private assignment exactly. Do not inspect or run the target verifier, its source, its tests, another case, or any target output. Retain the complete case tree, exact bytes, construction family and cluster, expected V/A/I/U state, reason code, and positive byte spans when applicable. Do not replace or repair an assigned case after target output exists."""

ORACLE_VALIDATOR_PROMPT = """Validate the supplied construction certificate against the complete retained case bytes before any target output is revealed. Check the assigned state and construction claim mechanically, check every file and span identity, and record disagreement rather than voting or repairing. Do not inspect the target verifier, its tests, or target output."""

TARGET_RUNNER_PROMPT = """Run the exact frozen selected-result verifier tuple on the opaque assigned case. Supply only case identity, selected report path, frozen profile identity, validator identity, and case bytes. Do not expose the construction certificate, oracle state, cell, reason, or expected binding. Freeze the complete output before comparison."""


def _normalized_prompt(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").split("\n")).strip()


def _module_record(
    project_root: Path, relative_path: str, *, entry_points: list[str]
) -> dict[str, Any]:
    path = project_root / relative_path
    payload = path.read_bytes()
    return {
        "path": relative_path,
        "content_digest": sha256_digest(payload),
        "size_bytes": len(payload),
        "entry_points": entry_points,
    }


def build_selected_result_verifier_qualification_freeze(
    project_root: Path,
    output: Path,
    *,
    frozen_at: str = FROZEN_AT,
) -> dict[str, Any]:
    """Freeze the exact verifier-qualification boundary before any case is assigned."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Qualification freeze output already exists: {output}")
    if semantic_digest(TARGET_PROFILE) != TARGET_PROFILE_DIGEST:
        raise ValueError("The selected-result profile literal has drifted.")

    target = _module_record(
        project_root,
        "evaluation/src/sc_referee_evaluation/prospective_selected_result_verifier.py",
        entry_points=[
            "freeze_independent_selected_result_derivation",
            "freeze_selected_result_validation",
            "revalidate_independent_selected_result_derivation",
            "validate_selected_result_validation",
        ],
    )
    if target["content_digest"] != TARGET_SOURCE_DIGEST:
        raise ValueError("The selected-result verifier implementation has drifted.")
    oracle = _module_record(
        project_root,
        "evaluation/src/sc_referee_evaluation/selected_result_qualification_oracle.py",
        entry_points=["seal_construction_certificate", "verify_construction_certificate"],
    )
    prompts = {
        "case-author": _normalized_prompt(CASE_AUTHOR_PROMPT),
        "oracle-validator": _normalized_prompt(ORACLE_VALIDATOR_PROMPT),
        "target-runner": _normalized_prompt(TARGET_RUNNER_PROMPT),
    }
    block_matrix: list[dict[str, Any]] = [
        {"oracle_state": "V", "cell": "unique_exact_and_allowed_static_variants", "count": 12},
        {"oracle_state": "A", "cell": "multiple_supported_bindings_or_results", "count": 8},
        {"oracle_state": "I", "cell": "missing_or_byte_mismatched_required_evidence", "count": 8},
        {"oracle_state": "U", "cell": "dynamic_opaque_or_unsupported_producer", "count": 4},
        {"oracle_state": "U", "cell": "file_role_or_source_artifact_boundary", "count": 4},
        {"oracle_state": "U", "cell": "encoding_newline_or_runtime_boundary", "count": 4},
        {"oracle_state": "U", "cell": "syntax_value_line_tree_or_budget_boundary", "count": 4},
        {"oracle_state": "U", "cell": "replay_mutation_path_or_filesystem_boundary", "count": 4},
    ]
    if sum(int(item["count"]) for item in block_matrix) != 48:
        raise ValueError("Selected-result qualification block must contain exactly 48 cases.")
    protocol = freeze_protocol_artifact(
        "corpus_selection_protocol",
        PROTOCOL_ID,
        frozen_at,
        {
            "assignment_status": "not_started",
            "blocks": ["pilot", "held_out"],
            "cases_per_block": 48,
            "block_matrix": block_matrix,
            "provider_families_per_block": 2,
            "cases_per_provider_per_block": 24,
            "minimum_construction_clusters_per_state": 4,
            "maximum_block_fraction_per_construction_family": "1/2",
            "case_replacement": False,
            "target_implementation_visible_to_case_authors": False,
            "target_tests_visible_to_case_authors": False,
            "target_output_visible_before_oracle_freeze": False,
            "oracle_certificate_visible_to_target_runner": False,
            "held_out_open_before_pilot_decision": False,
            "project_code_execution": False,
            "finding_permission": False,
            "scientific_detector_qualification": False,
            "prompt_digests": {
                name: sha256_digest(value.encode("utf-8")) for name, value in prompts.items()
            },
            "pass_rule": {
                "false_completions": 0,
                "false_rejections_or_wrong_bindings": 0,
                "exact_state_and_reason_matches": "48/48_per_block",
                "uncaught_exceptions_or_omissions": 0,
                "valid_oracle_certificates_before_reveal": "48/48_per_block",
                "complete_identity_chronology_inventory_and_digests": "48/48_per_block",
                "fresh_location_byte_identical_replays": 2,
                "threshold_relaxation_after_pilot": False,
            },
        },
    )
    profile: dict[str, Any] = {
        "artifact_kind": "selected_result_verifier_qualification_profile",
        "profile_id": PROFILE_ID,
        "profile_version": "1.0.0",
        "target_verifier": {
            "verifier_version": TARGET_VERSION,
            "module": target,
            "selected_result_profile": TARGET_PROFILE,
            "selected_result_profile_digest": TARGET_PROFILE_DIGEST,
            "runtime_contract": {
                "python": ">=3.11",
                "line_separator": "LF",
                "text_encoding": "ASCII codepoints preserve exact bytes",
                "per_run_exact_runtime_lock_required": True,
            },
        },
        "independent_oracle": {
            "oracle_kind": "typed-construction-certificate-byte-oracle-v1",
            "module": oracle,
            "forbidden_imports": [
                "prospective_selected_result_verifier",
                "prospective_qualification_v2",
                "sc_referee production parsers or detectors",
            ],
            "allowed_shared_operations": [
                "canonical JSON",
                "SHA-256",
                "byte reads",
                "lexical relative-path normalization",
            ],
            "qualification_authority": "none_tooling_only",
        },
        "selection_protocol": {
            "artifact_id": protocol["artifact_id"],
            "content_digest": protocol["content_digest"],
        },
        "oracle_states": {
            "V": "verified_unique",
            "A": "ambiguous",
            "I": "insufficient",
            "U": "unsupported",
        },
        "comparison_outcomes": [
            "exact_match",
            "false_complete",
            "false_incomplete",
            "binding_mismatch",
            "state_or_reason_mismatch",
            "uncontrolled_failure",
        ],
        "frozen_at": frozen_at,
        "qualification_authority": "none_precase_profile_only",
    }
    profile["profile_digest"] = semantic_digest(profile)

    output.mkdir(parents=True)
    write_normalized_json_once(output / "selection-protocol.json", protocol)
    write_normalized_json_once(output / "qualification-profile.json", profile)
    for name, prompt in prompts.items():
        atomic_create_bytes(output / f"{name}-prompt.txt", (prompt + "\n").encode("utf-8"))

    inventory = [
        {
            "path": path.name,
            "content_digest": sha256_digest(path.read_bytes()),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(output.iterdir(), key=lambda item: item.name)
    ]
    manifest: dict[str, Any] = {
        "freeze_kind": "selected_result_verifier_v1_precase",
        "frozen_at": frozen_at,
        "profile_id": profile["profile_id"],
        "profile_digest": profile["profile_digest"],
        "target_implementation_digest": target["content_digest"],
        "oracle_implementation_digest": oracle["content_digest"],
        "selection_protocol_artifact_id": protocol["artifact_id"],
        "selection_protocol_content_digest": protocol["content_digest"],
        "inventory": inventory,
        "inventory_digest": semantic_digest(inventory),
        "limitations": [
            "No qualification case, assignment, oracle proof, target output, metric, or decision is present.",
            "This freeze cannot qualify a scientific detector or authorize a Finding.",
            "The byte oracle validates independently authored construction certificates; it does not infer scientific meaning.",
            "Passing future cases supports only the exact frozen selected-result profile and implementation tuple.",
        ],
    }
    write_normalized_json_once(output / "FREEZE_MANIFEST.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze selected-result verifier qualification before any case assignment."
    )
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frozen-at", default=FROZEN_AT)
    arguments = parser.parse_args()
    result = build_selected_result_verifier_qualification_freeze(
        arguments.project_root.resolve(), arguments.output.resolve(), frozen_at=arguments.frozen_at
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
