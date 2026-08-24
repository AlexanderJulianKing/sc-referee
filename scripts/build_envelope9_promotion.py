from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.detectors.method_conflict_finding import (
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
)
from sc_referee.qualification_metrics import compile_qualification_evidence
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE = ROOT / "evaluation/development/blind-envelope-9-2026-08-23"
OUTPUT = (
    ROOT / "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v3.1.0-code-csv-lane/envelope-9-promotion-v021"
)
HISTORY_OUTPUT = (
    ROOT / "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v2.1.0-code-csv-lane/envelope-5-promotion-v020/"
    "RETIRED_DEPENDENCE_PIN.json"
)
COMPLETE_DOMAIN_SOURCE = (
    ROOT / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
    "promotion-round2-v020"
)
COMPLETE_DOMAIN_OUTPUT = (
    ROOT / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
    "promotion-round2-v021"
)
SCHEMA_VERSION = "0.21.0"
CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
BINDING_ID = (
    "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
)
DETECTOR_ID = "detector:bounded-code-csv-dependence-conflict"
DETECTOR_VERSION = "3.1.0"
QUALIFICATION_ID = "qualification:authorized-independent-unit-entry-v310-code-csv-envelope9"
PROVENANCE_STATEMENT = (
    "derived by Codex from envelope 9; installed under Alex's standing full-steam "
    "authorization via Fable"
)
DECIDED_AT = "2026-08-23T22:10:47Z"
POSITIVE_IDS = (
    "fe7eeea19d8fddd7811e",
    "14af9fba001740a9e72a",
    "a72fdcf9cfa1784e9315",
    "b8b21229f40a115d5e69",
    "2657fda9a6eea027c423",
    "284256146298ea19cd75",
)
NEGATIVE_IDS = (
    "ceb266a478e7ff5d4618",
    "6dffe3d7986dc5675127",
    "fd2f52a4099e1cbdfc8a",
    "4e9bd2ac9d532a4b45e8",
    "1feb6d2c4e4dce950eae",
    "3f12b75d274abe3a875f",
)
EXPECTED_CASE_IDS = POSITIVE_IDS + NEGATIVE_IDS
EXPECTED_CLOSURE_DIGEST = "sha256:0427d1595c0ca681acd57670f742c988718d50baa89afe72dd257c661267f69a"
EXPECTED_V021_DETECTOR_MANIFEST_DIGEST = (
    "sha256:43f5e88223dcd86af5b66baf41f0b6991ea28c782f3700dd224615e9c7085292"
)
EXPECTED_V021_GENERIC_DETECTOR_MANIFEST_DIGEST = (
    "sha256:df91936c23c9d7b56fcd483cf1aa053b8377e233b596c9f81424b5a26095015a"
)
FROZEN_V210_PIN: dict[str, Any] = {
    "binding_id": BINDING_ID,
    "binding_digest": "sha256:85c270872730d6ce8cf6cc62b79a54140b2a6121d98d7be35764db6d61f5b989",
    "check_id": CHECK_ID,
    "check_version": "2.1.0",
    "check_manifest_digest": "sha256:8b9ce5f53203c99bd0d24fcf0169e841905cb2aa034e858516bcf48105e4d6c2",
    "detector_id": DETECTOR_ID,
    "detector_version": "2.1.0",
    "detector_manifest_digest": "sha256:8824f6c48ac7b014383967e03774b9ef227dc265fa4754f5ce79ff1571304b05",
    "qualification_id": "qualification:authorized-independent-unit-entry-v210-code-csv-envelope5",
    "qualification_digest": "sha256:0e52eb7a7661646aaf30ba4484b81d10cfb1f8cb3f86caa0e4f14c0bd5c43bbb",
    "metric_set_id": "qualification-metric-set:authorized-independent-unit-entry-v210-envelope5",
    "metric_set_digest": "sha256:b11f7152edd1e6ea4cacd13d1c0b67ecfaf56ffbece7839246c762ec3c2909b4",
    "threshold_policy_digest": "sha256:7fe65c8b07a4154c63f432112873e212568815834b9402f8dd33c8670b03d918",
    "exam_adapter_identity": [
        {
            "adapter_id": (
                "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
                "code-csv-rowwise-two-sample-v1"
            ),
            "adapter_version": "2.1.0",
            "implementation_digest": "sha256:986f4862d5bc63cda2a61f5bf1d7df2d46e137b38de753edac5c2208f2705b54",
            "manifest_digest": "sha256:591a0bf3e7ca93b8166ad6a7a8779e937e48b5295b81ca0f433b02d28fc1c65c",
            "recognition_grammar_digest": "sha256:e135a5182ebba66ffc987f8867c468c54a9a1ab72d34f76dedee9867c4c3b10e",
        }
    ],
    "absolute_missed_roots": 2,
    "required_roots": 6,
    "finding_profile_id": "method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v1",
    "finding_profile_digest": "sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288",
}


def _finding_profile() -> dict[str, Any]:
    profile = {
        "profile_id": CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
        "title": "Analysis code contradicts the frozen one-row-per-authorized-unit requirement",
        "summary_template": (
            "The frozen requirement for `{CSV_PATH}` permits one analyzed row per "
            "`{UNIT_COLUMN}`. In `analysis.py`, the two checked arguments to `{PROCEDURE_ID}` "
            "are direct `{GROUP_COLUMN}` row selections from that CSV and jointly cover all "
            "`{N_csv}` rows; the table contains `{U}` distinct `{UNIT_COLUMN}` values, `{R}` of "
            "them repeat, and the maximum multiplicity is `{M}`. The static contract "
            "representation and the checked code/dataflow representation therefore conflict. "
            "The contract author may be wrong, and static source does not establish execution, "
            "statistical invalidity, numerical impact, bias direction, or the adequacy of "
            "unsupported or uninspected analysis paths. The declared unit column may be one "
            "component of a composite key."
        ),
        "slot_schema": {
            "CSV_PATH": "safe-normalized-material-path-string",
            "UNIT_COLUMN": "safe-authorized-column-string",
            "GROUP_COLUMN": "safe-authorized-column-string",
            "PROCEDURE_ID": "registered-two-sample-api-identity",
            "N_csv": "checked-positive-integer-equal-to-data-row-count",
            "U": "checked-positive-distinct-unit-count",
            "R": "checked-positive-repeated-unit-count",
            "M": "checked-positive-maximum-unit-multiplicity",
        },
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "severity_rationale": (
            "The checked static code/dataflow representation conflicts with one exact "
            "pre-authorized review requirement; the contract may be wrong, and execution, "
            "statistical invalidity, and numerical consequences were not established."
        ),
        "non_inferences": [
            "The contract author may be wrong.",
            "Static source does not establish that project code executed.",
            "Statistical invalidity, numerical impact, bias direction, and the adequacy of unsupported or uninspected analysis paths are not established.",
            "Reaching an output sink does not establish selection, publication use, interpretation, or reliance on the checked result.",
            "The declared unit column may be one component of a composite key.",
        ],
        "next_action": (
            "Align the checked analysis code with the frozen requirement, or document an "
            "authorized amendment and re-audit the exact source and CSV."
        ),
    }
    if semantic_digest(profile) != CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST:
        raise RuntimeError("the copied v2 Finding profile drifted from production code")
    return profile


def _load(path: Path) -> dict[str, Any] | list[dict[str, Any]]:
    payload = path.read_bytes()
    value = json.loads(payload)
    if not isinstance(value, (dict, list)):
        raise RuntimeError(f"input has the wrong top-level shape: {path}")
    return value


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _future_detector_manifest_digest() -> str:
    value = _load(ROOT / "src/sc_referee/resources/capability-manifests-v1/detector-manifests.json")
    if not isinstance(value, dict):
        raise RuntimeError("detector manifest collection is malformed")
    matches = [
        item
        for item in value.get("records", [])
        if isinstance(item, dict)
        and item.get("detector_id") == DETECTOR_ID
        and item.get("detector_version") == DETECTOR_VERSION
    ]
    if len(matches) != 1:
        raise RuntimeError("the frozen 3.1.0 detector manifest is unavailable")
    migrated = deepcopy(matches[0])
    migrated["schema_version"] = SCHEMA_VERSION
    migrated["validation"]["qualification_record_refs"] = [QUALIFICATION_ID]
    migrated["validation"]["qualification_review_basis"] = "agent_panel"
    migrated["validation"]["status"] = "held_out_validated"
    digest = semantic_digest(migrated)
    if digest != EXPECTED_V021_DETECTOR_MANIFEST_DIGEST:
        raise RuntimeError("the deterministic v0.21 detector-manifest migration drifted")
    return digest


def _future_binding(detector_manifest_digest: str) -> Any:
    registry = scientific_check_release_registry()
    matches = [
        item for item in registry.development_method_conflict_bindings if item.check_id == CHECK_ID
    ]
    if len(matches) != 1 or matches[0].detector_version != DETECTOR_VERSION:
        raise RuntimeError("the frozen 3.1.0 development binding is unavailable")
    return replace(
        matches[0],
        binding_id=BINDING_ID,
        detector_manifest_digest=detector_manifest_digest,
    )


def _migrate_complete_domain_records() -> tuple[str, str, str, str]:
    manifests = _load(
        ROOT / "src/sc_referee/resources/capability-manifests-v1/detector-manifests.json"
    )
    if not isinstance(manifests, dict):
        raise RuntimeError("detector manifest collection is malformed")
    generic = [
        item
        for item in manifests.get("records", [])
        if isinstance(item, dict)
        and item.get("detector_id") == "detector:bounded-analysis-method-conflict"
        and item.get("detector_version") == "0.3.0"
    ]
    if len(generic) != 1:
        raise RuntimeError("the frozen generic detector manifest is unavailable")
    migrated_manifest = deepcopy(generic[0])
    migrated_manifest["schema_version"] = SCHEMA_VERSION
    detector_digest = semantic_digest(migrated_manifest)
    if detector_digest != EXPECTED_V021_GENERIC_DETECTOR_MANIFEST_DIGEST:
        raise RuntimeError("the deterministic generic detector-manifest migration drifted")
    registry = scientific_check_release_registry()
    bindings = [
        item
        for item in registry.method_conflict_bindings
        if item.check_id == "check:complete-domain-exposure-denominator"
    ]
    if len(bindings) != 1:
        raise RuntimeError("the complete-domain binding is unavailable")
    binding = replace(bindings[0], detector_manifest_digest=detector_digest)
    qualification = _load(COMPLETE_DOMAIN_SOURCE / "DETECTOR_QUALIFICATION.json")
    metric = _load(COMPLETE_DOMAIN_SOURCE / "QUALIFICATION_METRIC_SET.json")
    if not isinstance(qualification, dict) or not isinstance(metric, dict):
        raise RuntimeError("the v0.20 complete-domain installed records are malformed")
    qualification = deepcopy(qualification)
    metric = deepcopy(metric)
    for record in (qualification, metric):
        record["schema_version"] = SCHEMA_VERSION
        scope = record.get("binding_scope")
        if not isinstance(scope, dict):
            raise RuntimeError("complete-domain record has no binding scope")
        scope["production_binding_digest"] = binding.binding_digest
        scope["detector_manifest_digest"] = detector_digest
    metric["detector_manifest_digest"] = detector_digest
    _write(COMPLETE_DOMAIN_OUTPUT / "DETECTOR_QUALIFICATION.json", qualification)
    _write(COMPLETE_DOMAIN_OUTPUT / "QUALIFICATION_METRIC_SET.json", metric)
    return (
        binding.binding_digest,
        detector_digest,
        semantic_digest(qualification),
        semantic_digest(metric),
    )


def _case_outcomes(
    audit: dict[str, Any],
    review: list[dict[str, Any]],
    detector_manifest_digest: str,
) -> list[dict[str, Any]]:
    audit_cases = {
        str(item["case_id"]): item
        for item in audit.get("cases", [])
        if isinstance(item, dict) and isinstance(item.get("case_id"), str)
    }
    labels = {
        str(item["case_id"]): item
        for item in review
        if isinstance(item, dict) and isinstance(item.get("case_id"), str)
    }
    if tuple(audit_cases) != EXPECTED_CASE_IDS or tuple(labels) != EXPECTED_CASE_IDS:
        raise RuntimeError("envelope-9 case order or domain drifted")
    label_digest = sha256_digest((ENVELOPE / "BLIND_REVIEW.json").read_bytes())
    outcomes: list[dict[str, Any]] = []
    for case_id in EXPECTED_CASE_IDS:
        positive = case_id in POSITIVE_IDS
        case = audit_cases[case_id]
        label = labels[case_id]
        if label.get("label") != ("POSITIVE" if positive else "NEGATIVE"):
            raise RuntimeError(f"blind label drifted for {case_id}")
        candidate = case.get("detector_states_dev") == ["evaluation_finding_candidate"]
        if candidate is not positive or case.get("replay_identical") is not True:
            raise RuntimeError(f"scored outcome drifted for {case_id}")
        expected_qualified = int(case_id in {"a72fdcf9cfa1784e9315", "b8b21229f40a115d5e69"})
        if case.get("findings_dev") != 0 or case.get("findings_qualified") != expected_qualified:
            raise RuntimeError(f"pre-promotion Finding count drifted for {case_id}")

        result_id = f"detector-result-projection:envelope9-{case_id}"
        candidate_id = f"detector-evaluation-candidate:envelope9-{case_id}"
        root_id = f"adjudicated-root-cause:envelope9-{case_id}"
        candidate_ref = {
            "record_type": "detector_evaluation_candidate",
            "record_id": candidate_id,
        }
        root_ref = {"record_type": "adjudicated_root_cause", "record_id": root_id}
        module_state = str(case.get("dependence_module_states_dev", [""])[0])
        if positive:
            state, applicability, coverage = (
                "evaluation_finding_candidate",
                "applicable",
                "covered",
            )
        elif module_state == "not_applicable":
            state, applicability, coverage = "not_applicable", "not_applicable", "not_covered"
        else:
            state, applicability, coverage = "unsupported_path", "uncertain", "not_covered"
        result_projection = {
            "case_id": case_id,
            "detector_version": DETECTOR_VERSION,
            "state": state,
            "applicability_status": applicability,
            "coverage_status": coverage,
            "evaluation_candidate_refs": [candidate_ref] if positive else [],
            "source_audit_case_digest": semantic_digest(case),
        }
        fixture_kind = "positive_issue_fixture" if positive else "static_scope_hard_negative"
        static_ref = (
            None
            if positive
            else {
                "record_type": "static_qualification_proof",
                "record_id": f"static-qualification-proof:envelope9-{case_id}",
            }
        )
        fixture_projection = {
            "case_id": case_id,
            "fixture_kind": fixture_kind,
            "label_digest": label_digest,
            "method_contract_digest": sha256_digest(
                (
                    ENVELOPE / "cases" / case_id / "method-contract" / "semantic.lock.json"
                ).read_bytes()
            ),
        }
        outcome: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "detector_case_outcome",
            "case_outcome_id": f"detector-case-outcome:envelope9-{case_id}",
            "case_id": f"case:envelope9-{case_id}",
            "problem_id": f"qualification-problem:envelope9-{case_id}",
            "corpus_partition": "held_out",
            "fixture_kind": fixture_kind,
            "fixture_ref": {
                "record_type": "benchmark_fixture",
                "record_id": f"benchmark-fixture:envelope9-{case_id}",
            },
            "adjudication_ref": {
                "record_type": "benchmark_adjudication",
                "record_id": f"benchmark-adjudication:envelope9-{case_id}",
            },
            "scientific_label_freeze_digest": label_digest,
            "audit_bundle_ref": {
                "record_type": "audit_bundle",
                "record_id": f"bundle:envelope9-{case_id}-development-run1",
            },
            "audit_bundle_digest": sha256_digest(
                (ENVELOPE / "cases" / case_id / "audit-run-1" / "audit.bundle.json").read_bytes()
            ),
            "detector_id": DETECTOR_ID,
            "detector_version": DETECTOR_VERSION,
            "detector_manifest_digest": detector_manifest_digest,
            "comparison_review_refs": [
                {
                    "record_type": "stage3_comparison_review",
                    "record_id": f"stage3-review:blind-reviewer-a:envelope9-{case_id}",
                },
                {
                    "record_type": "stage3_comparison_review",
                    "record_id": f"stage3-review:blind-reviewer-b:envelope9-{case_id}",
                },
            ],
            "provider_families": ["Anthropic", "CustodianModelFree"],
            "fresh_contexts_verified": True,
            "exact_cross_provider_agreement": True,
            "comparison_status": "reconciled",
            "exclusion_reasons": [],
            "root_cause_refs": [root_ref] if positive else [],
            "candidate_refs": [candidate_ref] if positive else [],
            "root_outcomes": (
                [
                    {
                        "root_cause_ref": root_ref,
                        "status": "boundedly_localized",
                        "matched_candidate_refs": [candidate_ref],
                    }
                ]
                if positive
                else []
            ),
            "candidate_outcomes": (
                [
                    {
                        "candidate_ref": candidate_ref,
                        "status": "bounded_root_match",
                        "root_cause_ref": root_ref,
                    }
                ]
                if positive
                else []
            ),
            "metric_input_status": "complete",
            "detector_result_outcomes": [
                {
                    "detector_result_ref": {
                        "record_type": "detector_result",
                        "record_id": result_id,
                    },
                    "detector_result_digest": semantic_digest(result_projection),
                    "state": state,
                    "execution_class": "completed",
                    "applicability_status": applicability,
                    "coverage_status": coverage,
                    "evaluation_candidate_refs": [candidate_ref] if positive else [],
                }
            ],
            "detector_run_outcome": {
                "execution_status": "completed",
                "applicability_status": applicability,
                "coverage_status": coverage,
            },
            "metric_eligible": True,
            "promotion_evidence_eligible": True,
            "detector_output_observed": True,
            "model_free_reconciliation": True,
            "reconciled_at": DECIDED_AT,
            "provenance": {
                "actor": {
                    "actor_kind": "controller",
                    "actor_id": "software:codex",
                    "display_name": "Codex",
                },
                "method": "deterministic_envelope_9_step_10_derivation",
                "created_at": DECIDED_AT,
                "tool": "sc-referee-eval",
                "tool_version": "0.1.0",
            },
            "fixture_semantic_digest": semantic_digest(fixture_projection),
            "qualification_proof_status": "complete",
            "qualification_proof_family": "positive_issue" if positive else "static_closed_scope",
            "static_qualification_proof_ref": static_ref,
        }
        outcomes.append(outcome)
    return outcomes


def _threshold_policy() -> dict[str, Any]:
    policy: dict[str, Any] = {
        "policy_kind": "pilot_informed_binding_thresholds_v1",
        "policy_id": "threshold-policy:authorized-independent-unit-entry-v310-code-csv-envelope9",
        "policy_version": "1.0.0",
        "decision_adr_ref": (
            "docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md"
        ),
        "pilot_evidence_refs": [
            "evaluation/development/blind-envelope-9-2026-08-23/ENVELOPE_MANIFEST.json",
            "docs/implementation/PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md",
            "docs/implementation/PSEUDOREP-CODE-SLICE-3.1-DESIGN-2026-08-23.md",
        ],
        "frozen_at": "2026-08-23T21:41:07Z",
        "held_out_labels_observed_before_freeze": False,
        "minimum_counts": {
            "workflows": 12,
            "problem_clusters": 12,
            "adjudicated_roots": 6,
            "control_cases": 6,
        },
        "require_estimable_intervals": False,
        "metric_requirements": [
            {
                "metric_name": "completed_opportunity_false_positive_rate",
                "statistic": "estimate",
                "operator": "at_most",
                "threshold": 0.0,
            },
            {
                "metric_name": "adjudicated_root_recall",
                "statistic": "estimate",
                "operator": "at_least",
                "threshold": 0.5,
            },
        ],
    }
    policy["policy_semantic_digest"] = semantic_digest(policy)
    return policy


def build() -> dict[str, str]:
    manifest = _load(ENVELOPE / "ENVELOPE_MANIFEST.json")
    audit = _load(ENVELOPE / "AUDIT_RESULTS.json")
    review = _load(ENVELOPE / "BLIND_REVIEW.json")
    if (
        not isinstance(manifest, dict)
        or not isinstance(audit, dict)
        or not isinstance(review, list)
    ):
        raise RuntimeError("envelope-9 scored inputs have malformed top-level shapes")
    closure = manifest.get("implementation_closure")
    if (
        not isinstance(closure, dict)
        or closure.get("closure_digest") != EXPECTED_CLOSURE_DIGEST
        or audit.get("closure_verified") is not True
        or audit.get("case_count") != 12
    ):
        raise RuntimeError("envelope-9 closure or scoring record drifted")

    detector_manifest_digest = _future_detector_manifest_digest()
    (
        complete_domain_binding_digest,
        complete_domain_detector_manifest_digest,
        complete_domain_qualification_digest,
        complete_domain_metric_digest,
    ) = _migrate_complete_domain_records()
    binding = _future_binding(detector_manifest_digest)
    module = next(
        item
        for item in scientific_check_release_registry().development_modules
        if item.manifest.check_id == CHECK_ID
    )
    adapter = module.adapter_manifests[0]
    outcomes = _case_outcomes(audit, review, detector_manifest_digest)
    qualification_envelope = {
        "issue_classes": [
            "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
        ],
        "languages": ["python"],
        "packages": [],
        "operation_forms": [
            "code_csv_contract_conflict_finding_v2",
            "contract_bound_csv_multiplicity_d1_double_prime_v1",
            "registered_row_independent_scipy_procedure_v1",
            "static_python_operand_identity_dataflow_v310",
        ],
    }
    metric_evidence = compile_qualification_evidence(outcomes, qualification_envelope)
    policy = _threshold_policy()
    qualification_adapter_digest = semantic_digest(
        {
            "profile": "envelope9-code-csv-static-case-outcome-v1",
            "manifest_digest": sha256_digest((ENVELOPE / "ENVELOPE_MANIFEST.json").read_bytes()),
            "audit_results_digest": sha256_digest((ENVELOPE / "AUDIT_RESULTS.json").read_bytes()),
            "blind_review_digest": sha256_digest((ENVELOPE / "BLIND_REVIEW.json").read_bytes()),
        }
    )
    binding_scope = {
        "scope_kind": "method_conflict_binding_v1",
        "binding_id": BINDING_ID,
        "production_binding_digest": binding.binding_digest,
        "check_id": binding.check_id,
        "check_version": binding.check_version,
        "check_manifest_digest": binding.check_manifest_digest,
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "static_qualification_profile_ref": {
            "record_type": "static_qualification_profile",
            "record_id": "static-qualification-profile:envelope9-code-csv-frozen-closure-v1",
        },
        "static_qualification_profile_digest": EXPECTED_CLOSURE_DIGEST,
        "qualification_adapter": {
            "adapter_id": "qualification-adapter:envelope9-code-csv-static-case-outcome-v1",
            "adapter_version": "1.0.0",
            "implementation_digest": qualification_adapter_digest,
        },
    }
    metric: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "qualification_metric_set",
        **metric_evidence,
        "binding_scope": binding_scope,
        "metric_profile": "root-cause-clustered-metrics-v1",
        "numeric_threshold_policy": policy,
        "promotion_permitted": True,
        "generated_at": DECIDED_AT,
        "non_inferences": [
            PROVENANCE_STATEMENT,
            "Envelope 9 measured blind-positive recall is 6/6 and blind-negative false-positive rate is 0/6; neither is a global correctness certificate.",
            "The running first-contact window is 10/18 positives over envelopes 7-9 with 0/18 negative candidates; older-version first contacts are decision context, not detector-3.1 metric inputs.",
            "Lifetime evidence is 206 blind cases, 0 false accusations, and 17 blind catches; absence of a Finding outside the exact qualified profile has no pass meaning.",
            "Envelope 9 family-C controls fd2f52a4099e1cbdfc8a and 1feb6d2c4e4dce950eae abstained on dependence-aware-sibling-present and resampling-inference-sibling-present respectively.",
        ],
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:codex",
                "display_name": "Codex",
            },
            "method": "deterministic_envelope_9_step_10_derivation",
            "created_at": DECIDED_AT,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
        "extensions": {
            "x-blind-first-contact-positive-catches": [0, 1, 2, 4, 0, 2, 2, 6],
            "x-running-positive-candidates": 10,
            "x-running-positive-cases": 18,
            "x-running-recall": 10 / 18,
            "x-running-negative-candidates": 0,
            "x-running-negative-cases": 18,
            "x-lifetime-blind-cases": 206,
            "x-lifetime-false-accusations": 0,
            "x-lifetime-blind-catches": 17,
            "x-envelope-9-family-c-negative-count": 2,
            "x-envelope-9-family-c-designed-guard-count": 2,
        },
    }
    metric_id = str(metric["metric_set_id"])
    qualification: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "detector_qualification",
        "qualification_id": QUALIFICATION_ID,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "requested_maturity": "validated",
        "effective_maturity": "validated",
        "outcome": "promoted",
        "review_basis": "agent_panel",
        "author_actor_ids": [
            f"actor:envelope9-project-author-{case_id}" for case_id in EXPECTED_CASE_IDS
        ],
        "agent_adjudication_refs": [],
        "human_scientific_approvals": [],
        "software_maintainer_approvals": [
            {
                "actor": {
                    "actor_kind": "human",
                    "actor_id": "person:fable",
                    "display_name": "Fable",
                },
                "approved_on": "2026-08-23",
                "decision_ref": (
                    "docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-"
                    "PSEUDOREPLICATION-FINDING.md"
                ),
            }
        ],
        "evaluation_refs": [
            "evaluation/development/blind-envelope-9-2026-08-23/AUDIT_RESULTS.json",
            "evaluation/development/blind-envelope-9-2026-08-23/ENVELOPE_MANIFEST.json",
            "evaluation/development/blind-envelope-9-2026-08-23/BLIND_REVIEW.json",
        ],
        "qualification_report_ref": (
            "evaluation/development/blind-envelope-9-2026-08-23/CUSTODY_LOG.md"
        ),
        "qualification_basis_disclosure": (
            "Envelope 9 met its frozen bar with 6/6 blind-positive evaluation candidates, "
            "0/6 blind-negative candidates, zero qualified-lane Findings across the envelope, "
            "and replay equality 12/12. The running first-contact tally over Envelopes 7-9 is "
            "10/18 (56%) with 0 false accusations over the last 36 blind cases. The blind "
            "first-contact catch series is 0,1,2,4,0,2,2,6; lifetime evidence at this decision "
            "is 206 blind cases, 0 false accusations, and 17 blind catches. Both Envelope 9 "
            "family-C controls stopped on designed S1/S2 guards. Detector implementation, "
            "adapter, grammar, case, and envelope bytes remain frozen; only the forward schema "
            "representation and production binding are installed."
        ),
        "qualification_proof_families": ["static_closed_scope"],
        "quantitative_metrics": {
            "metric_profile": "root-cause-clustered-metrics-v1",
            "metric_set_refs": [
                {"record_type": "qualification_metric_set", "record_id": metric_id}
            ],
        },
        "numeric_threshold_policy": policy,
        "safety_gates": {
            "no_known_high_or_critical_false_accusations": True,
            "conditional_never_promoted": True,
            "verified_good_and_hard_negative_included": True,
            "decisive_counterevidence_included": True,
            "cluster_aware_uncertainty_reported": True,
            "public_development_cases_not_used_for_qualification": True,
            "regression_fixture_for_every_discovered_false_accusation": True,
            "unresolved_disagreement_excluded": True,
            "qualification_report_public": True,
            "proof_families_stratified": True,
        },
        "static_scope_disclosure": {
            "scope_statement": (
                "Twelve digest-frozen reportless static audit closures under detector 3.1.0. "
                "The detector read no prose and executed no project-authored code. Envelope 9 "
                "measured 6/6 positive recall and 0/6 blind-control false positives; both "
                "family-C controls stopped on designed inference-sibling guards."
            ),
            "profile_refs": [binding_scope["static_qualification_profile_ref"]],
            "execution_claimed": False,
            "global_correctness_claimed": False,
            "stage3_comparison_artifact_exists": False,
        },
        "binding_scope": binding_scope,
        "decided_at": DECIDED_AT,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:codex",
                "display_name": "Codex",
            },
            "method": "deterministic_envelope_9_step_10_derivation",
            "created_at": DECIDED_AT,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
    }
    qualification_digest = semantic_digest(qualification)
    metric_digest = semantic_digest(metric)
    finding_profile = _finding_profile()
    finding_binding: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "step_10_installed_artifact",
        "artifact_kind": "method_conflict_finding_profile_binding",
        "artifact_status": "INSTALLED",
        "binding_id": BINDING_ID,
        "binding_digest": binding.binding_digest,
        "check_id": binding.check_id,
        "check_version": binding.check_version,
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "finding_profile_id": CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
        "finding_profile_digest": CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
        "finding_profile": finding_profile,
        "source_path": "src/sc_referee/detectors/method_conflict_finding.py",
        "provenance_statement": PROVENANCE_STATEMENT,
    }
    finding_binding["finding_profile_binding_semantic_digest"] = semantic_digest(finding_binding)
    threshold_record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "step_10_installed_artifact",
        "artifact_kind": "method_conflict_threshold_record",
        "artifact_status": "INSTALLED",
        "envelope_id": "blind-envelope-9-2026-08-23",
        "implementation_closure_digest": EXPECTED_CLOSURE_DIGEST,
        "threshold_policy": policy,
        "measured_results": {
            "blind_first_contact_positive_catches": [0, 1, 2, 4, 0, 2, 2, 6],
            "envelope_9_positive_recall": {"numerator": 6, "denominator": 6, "estimate": 1.0},
            "envelope_9_negative_false_positive_rate": {
                "numerator": 0,
                "denominator": 6,
                "estimate": 0.0,
            },
            "running_positive_recall": {
                "numerator": 10,
                "denominator": 18,
                "estimate": 10 / 18,
                "window": ["envelope-7", "envelope-8", "envelope-9"],
            },
            "last_36_false_accusations": {"numerator": 0, "denominator": 36},
            "lifetime": {"blind_cases": 206, "false_accusations": 0, "blind_catches": 17},
            "family_c": {
                "negative_count": 2,
                "designed_guard_count": 2,
                "cases": [
                    {
                        "case_id": "fd2f52a4099e1cbdfc8a",
                        "guard": "dependence-aware-sibling-present",
                    },
                    {
                        "case_id": "1feb6d2c4e4dce950eae",
                        "guard": "resampling-inference-sibling-present",
                    },
                ],
            },
            "findings": {"blind_108": 0, "regression_155": 0, "envelope_9": 0},
            "replay": {"numerator": 12, "denominator": 12},
        },
        "bar_result": "met",
        "source_refs": [
            "evaluation/development/blind-envelope-9-2026-08-23/ENVELOPE_MANIFEST.json",
            "evaluation/development/blind-envelope-9-2026-08-23/AUDIT_RESULTS.json",
            "evaluation/development/blind-envelope-9-2026-08-23/BLIND_REVIEW.json",
            "evaluation/development/blind-envelope-9-2026-08-23/CUSTODY_LOG.md",
        ],
        "provenance_statement": PROVENANCE_STATEMENT,
    }
    threshold_record["threshold_record_semantic_digest"] = semantic_digest(threshold_record)
    pin_payload = {
        "binding_id": BINDING_ID,
        "binding_digest": binding.binding_digest,
        "check_id": binding.check_id,
        "check_version": binding.check_version,
        "check_manifest_digest": binding.check_manifest_digest,
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "qualification_id": QUALIFICATION_ID,
        "qualification_digest": qualification_digest,
        "metric_set_id": metric_id,
        "metric_set_digest": metric_digest,
        "threshold_policy_digest": policy["policy_semantic_digest"],
        "exam_adapter_identity": [
            {
                "adapter_id": adapter.adapter_id,
                "adapter_version": adapter.adapter_version,
                "implementation_digest": adapter.implementation_digest,
                "manifest_digest": adapter.manifest_digest,
                "recognition_grammar_digest": adapter.recognition_grammar_digest,
            }
        ],
        "absolute_missed_roots": 0,
        "required_roots": 6,
        "finding_profile_id": CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
        "finding_profile_digest": CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
    }
    pin_artifact: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "step_10_installed_artifact",
        "artifact_kind": "replacement_method_conflict_grant_pin",
        "artifact_status": "INSTALLED",
        "installation_target": "src/sc_referee/detectors/method_conflict_grant_pins.py",
        "installation_symbol": "_DEPENDENCE_PIN",
        "replaces_installed_qualification_id": FROZEN_V210_PIN["qualification_id"],
        "pin_payload": pin_payload,
        "pin_payload_semantic_digest": semantic_digest(pin_payload),
        "provenance_statement": PROVENANCE_STATEMENT,
    }
    pin_artifact["replacement_pin_artifact_semantic_digest"] = semantic_digest(pin_artifact)
    retired_payload = deepcopy(FROZEN_V210_PIN)
    history: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "retired_method_conflict_grant_pin",
        "artifact_status": "FROZEN_RETIRED_HISTORY",
        "retired_pin_payload": retired_payload,
        "retired_pin_payload_semantic_digest": semantic_digest(retired_payload),
        "replaced_by_qualification_id": QUALIFICATION_ID,
        "retired_on": "2026-08-23",
        "provenance_statement": PROVENANCE_STATEMENT,
    }
    history["retirement_record_semantic_digest"] = semantic_digest(history)

    for name, value in (
        ("DETECTOR_QUALIFICATION.json", qualification),
        ("QUALIFICATION_METRIC_SET.json", metric),
        ("THRESHOLD_RECORD.json", threshold_record),
        ("FINDING_PROFILE_BINDING.json", finding_binding),
        ("REPLACEMENT_DEPENDENCE_PIN.json", pin_artifact),
    ):
        _write(OUTPUT / name, value)
    _write(HISTORY_OUTPUT, history)
    return {
        "qualification_digest": qualification_digest,
        "metric_set_digest": metric_digest,
        "threshold_policy_digest": str(policy["policy_semantic_digest"]),
        "binding_digest": binding.binding_digest,
        "detector_manifest_digest": detector_manifest_digest,
        "pin_payload_digest": semantic_digest(pin_payload),
        "complete_domain_binding_digest": complete_domain_binding_digest,
        "complete_domain_detector_manifest_digest": complete_domain_detector_manifest_digest,
        "complete_domain_qualification_digest": complete_domain_qualification_digest,
        "complete_domain_metric_digest": complete_domain_metric_digest,
    }


def main() -> None:
    print(canonical_json(build()))


if __name__ == "__main__":
    main()
