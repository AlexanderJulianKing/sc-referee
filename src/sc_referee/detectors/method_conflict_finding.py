from __future__ import annotations

import json
import re
from collections.abc import Mapping
from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.observed import controller_provenance
from sc_referee.scientific_checks.core import MethodConflictBinding
from sc_referee.version import SCHEMA_VERSION


class MethodConflictFindingDraftError(ValueError):
    """Raised when an evaluation result cannot support one bounded Finding draft."""


_DEPENDENCE_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
REPORT_CSV_DEPENDENCE_FINDING_PROFILE_ID = (
    "method-conflict-finding:report-csv-authorized-unit-requirement-conflict-v1"
)
_DEPENDENCE_TITLE = "Selected report contradicts the frozen one-row-per-authorized-unit requirement"
_DEPENDENCE_SEVERITY_RATIONALE = (
    "The selected report conflicts with one exact pre-authorized review requirement; the "
    "contract may be wrong, and execution, statistical invalidity, and numerical consequences "
    "were not established."
)
_DEPENDENCE_NEXT_ACTION = (
    "Align the selected report with the frozen requirement, or document an authorized amendment "
    "and re-audit the exact report and CSV."
)
_DEPENDENCE_NON_INFERENCES = (
    "The contract's scientific requirement is not established as correct.",
    "Project code execution and use of the CSV rows by the reported test are not established.",
    "Uninspected project code may have pseudobulked or otherwise transformed the table.",
    "Statistical invalidity, numerical causality, bias direction, universal scientific correctness, "
    "and invalidity outside the selected analysis are not established.",
)
_DEPENDENCE_SLOT_SCHEMA = {
    "COLUMN": "safe-authorized-column-string",
    "CSV_PATH": "safe-normalized-material-path-string",
    "REPORT_PATH": "safe-normalized-report-path-string",
    "N": "checked-positive-integer-equal-to-data-row-count",
    "U": "checked-positive-distinct-unit-count",
    "R": "checked-positive-repeated-unit-count",
}
_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_SAFE_COLUMN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
REPORT_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST = semantic_digest(
    {
        "profile_id": REPORT_CSV_DEPENDENCE_FINDING_PROFILE_ID,
        "title": _DEPENDENCE_TITLE,
        "summary_template": (
            "The frozen method contract requires one analyzed row per value of the human-authorized "
            "unit column `{COLUMN}` in full-digest `{CSV_PATH}`. For the selected analysis, "
            "`{REPORT_PATH}` states that all `{N}` CSV rows entered a two-sample "
            "`scipy.stats.ttest_ind`-family test as individual observations; `{COLUMN}` has `{U}` "
            "distinct nonempty values and `{R}` values repeat across those rows. Those two frozen "
            "representations conflict. This Finding is limited to that contract-versus-report "
            "conflict. It does not establish that the contract's scientific requirement is correct, "
            "that project code executed the reported analysis, or that the statistics are invalid. "
            "Uninspected project code may have pseudobulked or otherwise transformed the table. It "
            "also does not establish numerical causality, bias direction, universal scientific "
            "correctness, or invalidity outside this selected analysis."
        ),
        "slot_schema": _DEPENDENCE_SLOT_SCHEMA,
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "severity_rationale": _DEPENDENCE_SEVERITY_RATIONALE,
        "non_inferences": list(_DEPENDENCE_NON_INFERENCES),
        "next_action": _DEPENDENCE_NEXT_ACTION,
    }
)

CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID = (
    "method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v1"
)
_CODE_DEPENDENCE_TITLE = (
    "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"
)
_CODE_DEPENDENCE_SEVERITY_RATIONALE = (
    "The checked static code/dataflow representation conflicts with one exact pre-authorized "
    "review requirement; the contract may be wrong, and execution, statistical invalidity, and "
    "numerical consequences were not established."
)
_CODE_DEPENDENCE_NEXT_ACTION = (
    "Align the checked analysis code with the frozen requirement, or document an authorized "
    "amendment and re-audit the exact source and CSV."
)
_CODE_DEPENDENCE_NON_INFERENCES = (
    "The contract author may be wrong.",
    "Static source does not establish that project code executed.",
    "Statistical invalidity, numerical impact, bias direction, and the adequacy of unsupported or "
    "uninspected analysis paths are not established.",
    "Reaching an output sink does not establish selection, publication use, interpretation, or "
    "reliance on the checked result.",
)
_CODE_DEPENDENCE_SLOT_SCHEMA = {
    "CSV_PATH": "safe-normalized-material-path-string",
    "UNIT_COLUMN": "safe-authorized-column-string",
    "GROUP_COLUMN": "safe-authorized-column-string",
    "PROCEDURE_ID": "registered-two-sample-api-identity",
    "N_csv": "checked-positive-integer-equal-to-data-row-count",
    "U": "checked-positive-distinct-unit-count",
    "R": "checked-positive-repeated-unit-count",
    "M": "checked-positive-maximum-unit-multiplicity",
}

_MULTIPLE_TESTING_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
MULTIPLE_TESTING_CODE_FINDING_PROFILE_ID = (
    "method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1"
)
MULTIPLE_TESTING_CODE_FINDING_PROFILE_VERSION = "1.0.0"
_MULTIPLE_TESTING_TITLE = (
    "Analysis code contradicts the frozen complete-family correction requirement"
)
_MULTIPLE_TESTING_SUMMARY_TEMPLATE = (
    "The frozen requirement for `{CSV_PATH}` names the ordered outcome columns "
    "{OUTCOME_COLUMNS} under group column `{GROUP_COLUMN}` as one complete-correction family "
    "with {AUTHORIZED_COUNT} members. In `analysis.py`, static analysis establishes "
    "{PERFORMED_COUNT} matching `{TEST_API}` calls. For {UNCORRECTED_COUNT} registered "
    "`.pvalue` members, p-derived conclusions reach a supported code sink without entering a "
    "recognized correction anywhere in the analyzed source; {CORRECTED_COUNT} registered "
    "`.pvalue` members enter a recognized correction. This conflicts with the frozen "
    "complete-family-correction requirement."
)
_MULTIPLE_TESTING_SLOT_SCHEMA = {
    "CSV_PATH": "safe-normalized-authority-path-bound-to-material-digest",
    "GROUP_COLUMN": "safe-authority-column-byte-equal-to-contract-field",
    "OUTCOME_COLUMNS": "canonical-json-ordered-safe-authority-column-list",
    "AUTHORIZED_COUNT": "checked-integer-equal-to-contract-list-length-at-least-three",
    "PERFORMED_COUNT": "checked-integer-equal-to-call-census-and-authorized-count",
    "CORRECTED_COUNT": "checked-integer-zero-through-performed-count-minus-one",
    "UNCORRECTED_COUNT": "checked-integer-performed-minus-corrected-at-least-one",
    "TEST_API": "uniform-registered-two-sample-api-identity",
}
_MULTIPLE_TESTING_SEVERITY_RATIONALE = (
    "The checked static code representation conflicts with one exact pre-authorized "
    "complete-family correction requirement; the contract may be wrong, and execution, "
    "statistical invalidity, and numerical consequences were not established."
)
_MULTIPLE_TESTING_NEXT_ACTION = (
    "Align the checked code with the frozen complete-family correction requirement, or record "
    "an authorized amendment and re-audit the exact source and CSV."
)
_MULTIPLE_TESTING_NON_INFERENCES = (
    "The contract author may be wrong.",
    "Static source does not establish that project code executed.",
    "Absence of a recognized correction in the analyzed source does not establish that no "
    "correction was applied.",
    "Correction may occur in unsupported, uninspected, upstream, downstream, or external code.",
    "The detector does not establish runtime p-values, test assumptions, effect sizes, inflated "
    "error rates, statistical invalidity, selection, publication use, interpretation, or reliance.",
    "The detector does not establish that the named outcomes should scientifically form one family.",
)
MULTIPLE_TESTING_CODE_FINDING_PROFILE_DIGEST = semantic_digest(
    {
        "profile_id": MULTIPLE_TESTING_CODE_FINDING_PROFILE_ID,
        "profile_version": MULTIPLE_TESTING_CODE_FINDING_PROFILE_VERSION,
        "title": _MULTIPLE_TESTING_TITLE,
        "summary_template": _MULTIPLE_TESTING_SUMMARY_TEMPLATE,
        "slot_schema": _MULTIPLE_TESTING_SLOT_SCHEMA,
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "severity_rationale": _MULTIPLE_TESTING_SEVERITY_RATIONALE,
        "non_inferences": list(_MULTIPLE_TESTING_NON_INFERENCES),
        "next_action": _MULTIPLE_TESTING_NEXT_ACTION,
    }
)

MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_ID = (
    "method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v2"
)
MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_VERSION = "2.0.0"
_MULTIPLE_TESTING_V2_SUMMARY_TEMPLATE = (
    "The frozen requirement for `{CSV_PATH}` names the ordered outcome columns "
    "{OUTCOME_COLUMNS} under group column `{GROUP_COLUMN}` as one complete-correction family "
    "with {AUTHORIZED_COUNT} members. In `analysis.py`, static analysis maps every named outcome "
    "to exactly one registered two-group test call, for {PERFORMED_COUNT} calls in all. For "
    "{UNCORRECTED_COUNT} registered family p-value results, p-derived conclusions reach a "
    "supported code sink without entering a recognized correction anywhere in the analyzed "
    "source; {CORRECTED_COUNT} registered family p-value results enter a recognized correction. "
    "This conflicts with the frozen complete-family-correction requirement."
)
_MULTIPLE_TESTING_V2_SLOT_SCHEMA = {
    key: value for key, value in _MULTIPLE_TESTING_SLOT_SCHEMA.items() if key != "TEST_API"
}
MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_DIGEST = semantic_digest(
    {
        "profile_id": MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_ID,
        "profile_version": MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_VERSION,
        "title": _MULTIPLE_TESTING_TITLE,
        "summary_template": _MULTIPLE_TESTING_V2_SUMMARY_TEMPLATE,
        "slot_schema": _MULTIPLE_TESTING_V2_SLOT_SCHEMA,
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "severity_rationale": _MULTIPLE_TESTING_SEVERITY_RATIONALE,
        "non_inferences": list(_MULTIPLE_TESTING_NON_INFERENCES),
        "next_action": _MULTIPLE_TESTING_NEXT_ACTION,
    }
)


def _is_registered_code_dependence_binding(binding: MethodConflictBinding) -> bool:
    from sc_referee.scientific_checks.profiles import scientific_check_release_registry

    registry = scientific_check_release_registry()
    matches = [
        item
        for item in (
            *registry.method_conflict_bindings,
            *registry.development_method_conflict_bindings,
        )
        if item.binding_id == binding.binding_id
    ]
    live = bool(
        len(matches) == 1
        and matches[0].binding_digest == binding.binding_digest
        and binding.check_id == _DEPENDENCE_CHECK_ID
        and binding.detector_id == "detector:bounded-code-csv-dependence-conflict"
        and binding.required_evidence_planes == ("static_source",)
    )
    if live:
        return True
    from sc_referee.detectors.method_conflict_grant_pins import GRANT_PINS

    installed = GRANT_PINS.get(binding.binding_id)
    return bool(
        installed is not None
        and installed.binding_digest == binding.binding_digest
        and installed.check_id == binding.check_id == _DEPENDENCE_CHECK_ID
        and installed.check_version == binding.check_version
        and installed.check_manifest_digest == binding.check_manifest_digest
        and installed.detector_id
        == binding.detector_id
        == "detector:bounded-code-csv-dependence-conflict"
        and installed.detector_version == binding.detector_version == "2.1.0"
        and installed.detector_manifest_digest == binding.detector_manifest_digest
        and binding.required_evidence_planes == ("static_source",)
    )


def _is_registered_code_multiple_testing_binding(binding: MethodConflictBinding) -> bool:
    from sc_referee.scientific_checks.profiles import scientific_check_release_registry

    matches = [
        item
        for item in scientific_check_release_registry().development_method_conflict_bindings
        if item.binding_id == binding.binding_id
    ]
    return bool(
        len(matches) == 1
        and matches[0].binding_digest == binding.binding_digest
        and binding.check_id == _MULTIPLE_TESTING_CHECK_ID
        and binding.check_version in {"3.0.0", "3.1.0", "3.2.0"}
        and binding.detector_id == "detector:bounded-code-csv-multiple-testing-conflict"
        and binding.detector_version == binding.check_version
        and binding.required_evidence_planes == ("static_source",)
        and not binding.production_finding_permitted
    )


def code_dependence_wording_profile(
    binding: MethodConflictBinding,
) -> tuple[str, str, tuple[str, ...], bool] | None:
    if binding.detector_version == "2.1.0":
        return (
            CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID,
            CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
            _CODE_DEPENDENCE_NON_INFERENCES,
            False,
        )
    if binding.detector_version in {"2.3.0", "3.0.0", "3.1.0"}:
        return (
            CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
            CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
            _CODE_DEPENDENCE_NON_INFERENCES_V2,
            True,
        )
    return None


CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST = semantic_digest(
    {
        "profile_id": CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID,
        "title": _CODE_DEPENDENCE_TITLE,
        "summary_template": (
            "The frozen requirement for `{CSV_PATH}` permits one analyzed row per "
            "`{UNIT_COLUMN}`. In `analysis.py`, the two checked arguments to `{PROCEDURE_ID}` "
            "are direct `{GROUP_COLUMN}` row selections from that CSV and jointly cover all "
            "`{N_csv}` rows; the table contains `{U}` distinct `{UNIT_COLUMN}` values, `{R}` of "
            "them repeat, and the maximum multiplicity is `{M}`. The static contract "
            "representation and the checked code/dataflow representation therefore conflict. "
            "The contract author may be wrong, and static source does not establish execution, "
            "statistical invalidity, numerical impact, bias direction, or the adequacy of "
            "unsupported or uninspected analysis paths."
        ),
        "slot_schema": _CODE_DEPENDENCE_SLOT_SCHEMA,
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "severity_rationale": _CODE_DEPENDENCE_SEVERITY_RATIONALE,
        "non_inferences": list(_CODE_DEPENDENCE_NON_INFERENCES),
        "next_action": _CODE_DEPENDENCE_NEXT_ACTION,
    }
)

CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID = (
    "method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v2"
)
_CODE_DEPENDENCE_COMPOSITE_KEY_NON_INFERENCE = (
    "The declared unit column may be one component of a composite key."
)
_CODE_DEPENDENCE_NON_INFERENCES_V2 = (
    *_CODE_DEPENDENCE_NON_INFERENCES,
    _CODE_DEPENDENCE_COMPOSITE_KEY_NON_INFERENCE,
)
CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST = semantic_digest(
    {
        "profile_id": CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
        "title": _CODE_DEPENDENCE_TITLE,
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
        "slot_schema": _CODE_DEPENDENCE_SLOT_SCHEMA,
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "severity_rationale": _CODE_DEPENDENCE_SEVERITY_RATIONALE,
        "non_inferences": list(_CODE_DEPENDENCE_NON_INFERENCES_V2),
        "next_action": _CODE_DEPENDENCE_NEXT_ACTION,
    }
)


def draft_method_conflict_finding(
    result: Mapping[str, Any],
    binding: MethodConflictBinding,
    *,
    work_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the authority-neutral draft consumed only after qualification applies."""

    candidate = result.get("candidate")
    applicability = result.get("applicability")
    coverage = result.get("coverage")
    targets = result.get("target_refs")
    evidence = result.get("evidence")
    extensions = result.get("extensions")
    code_dependence_lane = _is_registered_code_dependence_binding(binding)
    multiple_testing_lane = _is_registered_code_multiple_testing_binding(binding)
    code_lane = code_dependence_lane or multiple_testing_lane
    if (
        result.get("record_type") != "detector_result"
        or result.get("detector_id") != binding.detector_id
        or result.get("detector_version") != binding.detector_version
        or result.get("state") not in {"evaluation_finding_candidate", "finding_candidate"}
        or not isinstance(candidate, Mapping)
        or candidate.get("assessment_type") != "finding"
        or not isinstance(applicability, Mapping)
        or applicability.get("status") != "applicable"
        or not isinstance(coverage, Mapping)
        or coverage.get("status") != "covered"
        or not isinstance(targets, list)
        or len(targets) != 1
        or not isinstance(targets[0], Mapping)
        or targets[0].get("record_type") != ("file_record" if code_lane else "publication_surface")
        or not isinstance(evidence, list)
        or not evidence
        or not isinstance(extensions, Mapping)
        or not isinstance(extensions.get("x-review-case-digest"), str)
    ):
        raise MethodConflictFindingDraftError(
            "detector result is outside the complete method-conflict draft envelope"
        )
    result_id = result.get("result_id")
    run_id = result.get("audit_run_id")
    created_at = result.get("evaluated_at")
    title = candidate.get("title")
    statement = candidate.get("bounded_statement")
    target = deepcopy(dict(targets[0]))
    target_id = target.get("record_id")
    if not all(
        isinstance(value, str) and value
        for value in (result_id, run_id, created_at, title, statement, target_id)
    ):
        raise MethodConflictFindingDraftError("detector result lacks stable Finding identities")
    draft: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "finding",
        "finding_id": stable_id(
            "finding-analysis-method-conflict",
            str(run_id),
            str(result_id),
            binding.binding_digest,
            str(extensions["x-review-case-digest"]),
        ),
        "audit_run_id": run_id,
        "grouping_key": f"{binding.detector_id}|{target_id}|{binding.dimension}",
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "title": title,
        "summary": statement,
        "demonstration_status": "demonstrated",
        "severity": {
            "level": "moderate",
            "rationale": (
                "The selected analysis declaration conflicts with one exact pre-authorized "
                "review requirement; numerical and broader scientific consequences were not "
                "established."
            ),
        },
        "publication_materiality": {
            "state": "assessed",
            "level": "local",
            "rationale": (
                "The demonstrated conflict is localized to the exact selected publication "
                "surface and is not projected to other claims or analyses."
            ),
            "publication_surface_ids": [] if code_lane else [target_id],
        },
        "root_cause": {
            "root_ref": target,
            "violated_semantic_dimension": binding.dimension,
            "explanation": (
                "The binding-required observed operand and the exact pre-analysis human "
                "requirement differ under the registered closed comparison relation."
            ),
        },
        "subject_refs": [target],
        "affected_descendants": [],
        "evidence": deepcopy(evidence),
        "logical_basis": (
            "One verified pre-analysis requirement and one binding-complete selected-analysis "
            "operand conflict after every finite applicability and counterevidence check "
            "completed."
        ),
        "detector_result_ids": [result_id],
        "coverage_limitations": [
            "Static evidence does not establish that project code executed.",
            "The Finding does not establish numerical causality, bias direction, universal "
            "scientific correctness, or effects outside the selected analysis.",
        ],
        "next_action": (
            "Align the selected analysis with the governing requirement or document an "
            "authorized amendment and re-audit."
        ),
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_analysis_method_finding_draft_v1", str(created_at)
        ),
        "extensions": {
            "x-method-conflict-binding-id": binding.binding_id,
            "x-method-conflict-binding-digest": binding.binding_digest,
            "x-review-case-digest": extensions["x-review-case-digest"],
        },
    }
    if binding.check_id == _DEPENDENCE_CHECK_ID:
        code_lane = code_dependence_lane
        facts = (
            _code_dependence_row_entry_facts(work_packet)
            if code_lane
            else _dependence_row_entry_facts(work_packet)
        )
        if facts is None:
            raise MethodConflictFindingDraftError(
                "dependence result lacks one exact contract-bound row-entry fact"
            )
        if code_lane:
            wording_profile = code_dependence_wording_profile(binding)
            if wording_profile is None:
                raise MethodConflictFindingDraftError(
                    "code dependence binding has no exact versioned wording profile"
                )
            profile_id, profile_digest, non_inferences, composite_key_limit = wording_profile
            draft["title"] = _CODE_DEPENDENCE_TITLE
            draft["summary"] = _code_dependence_summary(
                facts,
                composite_key_limit=composite_key_limit,
            )
            draft["publication_materiality"] = {
                "state": "unassessed",
                "reason": "no_selected_publication_surface",
                "rationale": (
                    "The reportless code lane establishes an output sink but no selected "
                    "publication surface, publication use, interpretation, or reliance."
                ),
                "candidate_publication_surface_ids": [],
            }
            draft["severity"]["rationale"] = _CODE_DEPENDENCE_SEVERITY_RATIONALE
            draft["coverage_limitations"] = list(non_inferences)
            draft["next_action"] = _CODE_DEPENDENCE_NEXT_ACTION
            draft["extensions"]["x-finding-wording-profile-id"] = profile_id
            draft["extensions"]["x-finding-wording-profile-digest"] = profile_digest
            draft["extensions"]["x-code-csv-row-entry-evidence-digest"] = facts["fact_digest"]
        else:
            draft["title"] = _DEPENDENCE_TITLE
            draft["summary"] = _dependence_summary(facts)
            draft["severity"]["rationale"] = _DEPENDENCE_SEVERITY_RATIONALE
            draft["coverage_limitations"] = list(_DEPENDENCE_NON_INFERENCES)
            draft["next_action"] = _DEPENDENCE_NEXT_ACTION
            draft["extensions"]["x-finding-wording-profile-id"] = (
                REPORT_CSV_DEPENDENCE_FINDING_PROFILE_ID
            )
            draft["extensions"]["x-finding-wording-profile-digest"] = (
                REPORT_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST
            )
            draft["extensions"]["x-report-csv-row-entry-evidence-digest"] = facts["fact_digest"]
    elif binding.check_id == _MULTIPLE_TESTING_CHECK_ID:
        if not multiple_testing_lane:
            raise MethodConflictFindingDraftError(
                "multiple-testing result lacks the exact development code binding"
            )
        facts = _multiple_testing_code_facts(work_packet)
        if facts is None:
            raise MethodConflictFindingDraftError(
                "multiple-testing result lacks one exact contract-bound code fact"
            )
        draft["title"] = _MULTIPLE_TESTING_TITLE
        draft["summary"] = _multiple_testing_v2_summary(facts)
        draft["publication_materiality"] = {
            "state": "unassessed",
            "reason": "no_selected_publication_surface",
            "rationale": (
                "The reportless code lane establishes supported code sinks but no selected "
                "publication surface, publication use, interpretation, or reliance."
            ),
            "candidate_publication_surface_ids": [],
        }
        draft["severity"]["rationale"] = _MULTIPLE_TESTING_SEVERITY_RATIONALE
        draft["coverage_limitations"] = list(_MULTIPLE_TESTING_NON_INFERENCES)
        draft["next_action"] = _MULTIPLE_TESTING_NEXT_ACTION
        draft["extensions"]["x-finding-wording-profile-id"] = (
            MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_ID
        )
        draft["extensions"]["x-finding-wording-profile-digest"] = (
            MULTIPLE_TESTING_CODE_FINDING_PROFILE_V2_DIGEST
        )
        draft["extensions"]["x-code-csv-multiple-testing-evidence-digest"] = facts["fact_digest"]
    return draft


def _dependence_row_entry_facts(
    work_packet: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(work_packet, Mapping):
        return None
    assertions = work_packet.get("semantic_assertions")
    answers = work_packet.get("answers")
    if not isinstance(assertions, list) or not isinstance(answers, list):
        return None
    reported = [
        item
        for item in assertions
        if isinstance(item, Mapping)
        and item.get("semantic_role") == "reported"
        and item.get("extensions", {}).get("x-scientific-check-id") == _DEPENDENCE_CHECK_ID
        and item.get("extensions", {}).get("x-report-csv-row-entry-evidence") is not None
    ]
    if len(reported) != 1 or len(answers) != 1 or not isinstance(answers[0], Mapping):
        return None
    assertion = reported[0]
    fact = assertion.get("extensions", {}).get("x-report-csv-row-entry-evidence")
    fact_digest = assertion.get("extensions", {}).get("x-report-csv-row-entry-evidence-digest")
    required = {
        "profile",
        "material_input_path",
        "material_input_content_digest",
        "material_file_ref",
        "authorized_unit_column",
        "group_contrast_column",
        "data_row_count",
        "distinct_unit_count",
        "repeated_unit_count",
        "maximum_unit_multiplicity",
        "composite_key_scan_complete",
        "composite_key_candidate_columns",
        "distinct_count_excluded_columns",
        "within_unit_index_columns",
        "unique_pair_within_unit_index_columns",
        "unique_nonindex_authorized_unit_composite_columns",
        "report_path",
        "report_content_digest",
        "procedure_id",
        "reported_n",
        "n_evidence_kind",
        "group_counts",
        "admission_template_id",
        "selected_path_binding_kind",
        "authority_binding_digest",
        "report_evidence_spans",
    }
    if (
        not isinstance(fact, Mapping)
        or set(fact) != required
        or not isinstance(fact_digest, str)
        or semantic_digest(fact) != fact_digest
        or fact.get("profile") != "report_csv_row_entry_evidence_v1"
        or fact.get("procedure_id") != "scipy.stats.ttest_ind_two_sample"
        or fact.get("composite_key_scan_complete") is not True
        or fact.get("unique_nonindex_authorized_unit_composite_columns") != []
        or not _valid_dependence_fact_shape(fact)
    ):
        return None
    integer_fields = (
        "data_row_count",
        "distinct_unit_count",
        "repeated_unit_count",
        "maximum_unit_multiplicity",
        "reported_n",
    )
    if any(
        not isinstance(fact.get(field), int) or isinstance(fact.get(field), bool)
        for field in integer_fields
    ):
        return None
    n = int(fact["data_row_count"])
    u = int(fact["distinct_unit_count"])
    r = int(fact["repeated_unit_count"])
    maximum = int(fact["maximum_unit_multiplicity"])
    if not (n == fact.get("reported_n") and n > u >= 2 and r >= 1 and maximum >= 2):
        return None
    for field in (
        "composite_key_candidate_columns",
        "distinct_count_excluded_columns",
        "within_unit_index_columns",
        "unique_pair_within_unit_index_columns",
    ):
        values = fact.get(field)
        if (
            not isinstance(values, list)
            or any(not isinstance(value, str) or not value for value in values)
            or values != sorted(set(values))
        ):
            return None
    answer = answers[0]
    authority = answer.get("extensions", {}).get("x-semantic-role-authority")
    snapshot = answer.get("extensions", {}).get("x-authority-binding-snapshot")
    if (
        not isinstance(authority, Mapping)
        or not isinstance(snapshot, Mapping)
        or set(authority) != {"authorized_independent_unit_key"}
        or set(snapshot) != {"authorized_independent_unit_key"}
        or semantic_digest(snapshot) != fact.get("authority_binding_digest")
    ):
        return None
    unit = authority.get("authorized_independent_unit_key")
    bound = snapshot.get("authorized_independent_unit_key")
    if (
        not isinstance(unit, Mapping)
        or not isinstance(bound, Mapping)
        or set(unit) != {"material_input_path", "column_name", "group_contrast_column"}
        or set(bound)
        != {
            "material_input_path",
            "column_name",
            "group_contrast_column",
            "material_input_content_digest",
        }
        or unit.get("material_input_path") != fact.get("material_input_path")
        or unit.get("column_name") != fact.get("authorized_unit_column")
        or unit.get("group_contrast_column") != fact.get("group_contrast_column")
        or bound.get("material_input_content_digest") != fact.get("material_input_content_digest")
        or answer.get("answer_value")
        != {
            "dependence_structure": "one_analyzed_row_per_authorized_independent_unit",
            "semantic_role_authority": dict(authority),
        }
    ):
        return None
    source_refs = assertion.get("source_refs")
    if not isinstance(source_refs, list) or not _fact_sources_resolve(fact, source_refs):
        return None
    return {**dict(fact), "fact_digest": fact_digest}


def _code_dependence_row_entry_facts(
    work_packet: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(work_packet, Mapping):
        return None
    assertions = work_packet.get("semantic_assertions")
    answers = work_packet.get("answers")
    if not isinstance(assertions, list) or not isinstance(answers, list):
        return None
    observed = [
        item
        for item in assertions
        if isinstance(item, Mapping)
        and item.get("semantic_role") == "observed"
        and item.get("extensions", {}).get("x-scientific-check-id") == _DEPENDENCE_CHECK_ID
        and item.get("extensions", {}).get("x-code-csv-row-entry-evidence") is not None
    ]
    if len(observed) != 1 or len(answers) != 1 or not isinstance(answers[0], Mapping):
        return None
    assertion = observed[0]
    extensions = assertion.get("extensions", {})
    fact = extensions.get("x-code-csv-row-entry-evidence")
    evidence_digest = extensions.get("x-code-csv-row-entry-evidence-digest")
    required = {
        "profile",
        "material_input_path",
        "material_input_content_digest",
        "material_file_ref",
        "authorized_unit_column",
        "group_contrast_column",
        "data_row_count",
        "distinct_unit_count",
        "repeated_unit_count",
        "maximum_unit_multiplicity",
        "composite_key_scan_complete",
        "composite_key_candidate_columns",
        "distinct_count_excluded_columns",
        "within_unit_index_columns",
        "unique_pair_within_unit_index_columns",
        "unique_nonindex_authorized_unit_composite_columns",
        "analysis_path",
        "analysis_content_digest",
        "analysis_file_ref",
        "alternate_analysis_file_scan_complete",
        "other_python_statistics_import_scan_complete",
        "reader_api",
        "accepted_reader_count",
        "all_test_operand_paths_rooted_in_authorized_reader",
        "selection_kinds",
        "value_column",
        "group_values",
        "group_row_counts",
        "all_csv_rows_partitioned",
        "procedure_id",
        "procedure_variant",
        "output_sink_kinds",
        "dataflow_max_definition_nodes",
        "descriptive_loop_count",
        "aggregation_path_scan_complete",
        "dependence_guard_scan_complete",
        "unsupported_call_scan_complete",
        "unregistered_output_call_scan_complete",
        "authority_binding_digest",
        "code_evidence_spans",
        "fact_digest",
    }
    if not isinstance(fact, Mapping) or set(fact) != required:
        return None
    fact_without_digest = dict(fact)
    fact_digest = fact_without_digest.pop("fact_digest", None)
    if (
        fact.get("profile") != "code_csv_row_entry_evidence_v1"
        or not isinstance(fact_digest, str)
        or semantic_digest(fact_without_digest) != fact_digest
        or not isinstance(evidence_digest, str)
        or semantic_digest(fact) != evidence_digest
        or not _valid_code_dependence_fact_shape(fact)
    ):
        return None
    answer = answers[0]
    authority = answer.get("extensions", {}).get("x-semantic-role-authority")
    snapshot = answer.get("extensions", {}).get("x-authority-binding-snapshot")
    if (
        not isinstance(authority, Mapping)
        or set(authority) != {"authorized_independent_unit_key"}
        or not isinstance(snapshot, Mapping)
        or set(snapshot) != {"authorized_independent_unit_key"}
        or semantic_digest(snapshot) != fact.get("authority_binding_digest")
    ):
        return None
    unit = authority.get("authorized_independent_unit_key")
    bound = snapshot.get("authorized_independent_unit_key")
    if (
        not isinstance(unit, Mapping)
        or set(unit) != {"material_input_path", "column_name", "group_contrast_column"}
        or not isinstance(bound, Mapping)
        or set(bound)
        != {
            "material_input_path",
            "column_name",
            "group_contrast_column",
            "material_input_content_digest",
        }
        or {key: bound.get(key) for key in unit} != dict(unit)
        or unit.get("material_input_path") != fact.get("material_input_path")
        or unit.get("column_name") != fact.get("authorized_unit_column")
        or unit.get("group_contrast_column") != fact.get("group_contrast_column")
        or bound.get("material_input_content_digest") != fact.get("material_input_content_digest")
        or answer.get("answer_value")
        != {
            "dependence_structure": "one_analyzed_row_per_authorized_independent_unit",
            "semantic_role_authority": dict(authority),
        }
    ):
        return None
    source_refs = assertion.get("source_refs")
    if not isinstance(source_refs, list) or not _code_fact_sources_resolve(fact, source_refs):
        return None
    return dict(fact)


def _multiple_testing_code_facts(
    work_packet: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(work_packet, Mapping):
        return None
    assertions = work_packet.get("semantic_assertions")
    answers = work_packet.get("answers")
    if not isinstance(assertions, list) or not isinstance(answers, list):
        return None
    observed = [
        item
        for item in assertions
        if isinstance(item, Mapping)
        and item.get("semantic_role") == "observed"
        and item.get("extensions", {}).get("x-scientific-check-id") == _MULTIPLE_TESTING_CHECK_ID
        and item.get("extensions", {}).get("x-code-csv-multiple-testing-evidence") is not None
    ]
    if len(observed) != 1 or len(answers) != 1 or not isinstance(answers[0], Mapping):
        return None
    assertion = observed[0]
    extensions = assertion.get("extensions", {})
    fact = extensions.get("x-code-csv-multiple-testing-evidence")
    evidence_digest = extensions.get("x-code-csv-multiple-testing-evidence-digest")
    required = {
        "profile",
        "material_input_path",
        "material_input_content_digest",
        "material_file_ref",
        "group_contrast_column",
        "outcome_columns",
        "group_value_domain_digest",
        "authorized_count",
        "performed_count",
        "corrected_count",
        "uncorrected_count",
        "registered_test_apis_by_position",
        "registered_test_api_set",
        "correction_classification",
        "corrected_positions",
        "conclusion_positions",
        "analysis_path",
        "analysis_content_digest",
        "analysis_file_ref",
        "authority_binding_digest",
        "code_evidence_spans",
        "fact_digest",
    }
    if not isinstance(fact, Mapping) or set(fact) != required:
        return None
    fact_without_digest = dict(fact)
    fact_digest = fact_without_digest.pop("fact_digest", None)
    if (
        fact.get("profile") != "code_csv_multiple_testing_evidence_v2"
        or not isinstance(fact_digest, str)
        or semantic_digest(fact_without_digest) != fact_digest
        or not isinstance(evidence_digest, str)
        or semantic_digest(fact) != evidence_digest
        or not _valid_multiple_testing_fact_shape(fact)
    ):
        return None
    answer = answers[0]
    authority = answer.get("extensions", {}).get("x-semantic-role-authority")
    snapshot = answer.get("extensions", {}).get("x-authority-binding-snapshot")
    if (
        not isinstance(authority, Mapping)
        or set(authority) != {"authorized_test_family"}
        or not isinstance(snapshot, Mapping)
        or set(snapshot) != {"authorized_test_family"}
        or semantic_digest(snapshot) != fact.get("authority_binding_digest")
    ):
        return None
    family = authority.get("authorized_test_family")
    bound = snapshot.get("authorized_test_family")
    authority_fields = {
        "material_input_path",
        "group_contrast_column",
        "outcome_columns",
        "family_member_rule",
        "correction_scope",
    }
    if (
        not isinstance(family, Mapping)
        or set(family) != authority_fields
        or not isinstance(bound, Mapping)
        or set(bound) != authority_fields | {"material_input_content_digest"}
        or {key: bound.get(key) for key in family} != dict(family)
        or family.get("material_input_path") != fact.get("material_input_path")
        or family.get("group_contrast_column") != fact.get("group_contrast_column")
        or family.get("outcome_columns") != fact.get("outcome_columns")
        or bound.get("material_input_content_digest") != fact.get("material_input_content_digest")
        or answer.get("answer_value")
        != {
            "selection_process": "complete_family_correction_over_authorized_outcome_family",
            "semantic_role_authority": dict(authority),
        }
    ):
        return None
    source_refs = assertion.get("source_refs")
    if not isinstance(source_refs, list) or not any(
        isinstance(source, Mapping)
        and source.get("path") == fact.get("analysis_path")
        and source.get("content_digest") == fact.get("analysis_content_digest")
        for source in source_refs
    ):
        return None
    return dict(fact)


def _valid_multiple_testing_fact_shape(fact: Mapping[str, Any]) -> bool:
    csv_path = fact.get("material_input_path")
    group = fact.get("group_contrast_column")
    outcomes = fact.get("outcome_columns")
    digests = (
        fact.get("material_input_content_digest"),
        fact.get("group_value_domain_digest"),
        fact.get("analysis_content_digest"),
        fact.get("authority_binding_digest"),
    )
    if (
        not _safe_path(csv_path, {".csv"})
        or fact.get("analysis_path") != "analysis.py"
        or not isinstance(group, str)
        or _SAFE_COLUMN.fullmatch(group) is None
        or not isinstance(outcomes, list)
        or len(outcomes) < 3
        or any(
            not isinstance(item, str) or _SAFE_COLUMN.fullmatch(item) is None for item in outcomes
        )
        or outcomes != list(dict.fromkeys(outcomes))
        or group in outcomes
        or any(not isinstance(value, str) or _SHA256.fullmatch(value) is None for value in digests)
        or not isinstance(fact.get("registered_test_apis_by_position"), list)
        or len(fact["registered_test_apis_by_position"]) != len(outcomes)
        or any(
            item not in {"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"}
            for item in fact["registered_test_apis_by_position"]
        )
        or fact.get("registered_test_api_set")
        != sorted(set(fact["registered_test_apis_by_position"]))
        or fact.get("correction_classification") not in {"none", "strict_subset"}
    ):
        return False
    integers = ("authorized_count", "performed_count", "corrected_count", "uncorrected_count")
    if any(
        not isinstance(fact.get(field), int) or isinstance(fact.get(field), bool)
        for field in integers
    ):
        return False
    authorized = int(fact["authorized_count"])
    performed = int(fact["performed_count"])
    corrected = int(fact["corrected_count"])
    uncorrected = int(fact["uncorrected_count"])
    corrected_positions = fact.get("corrected_positions")
    conclusion_positions = fact.get("conclusion_positions")
    if (
        authorized != len(outcomes)
        or performed != authorized
        or not 0 <= corrected < performed
        or uncorrected != performed - corrected
        or uncorrected < 1
        or not isinstance(corrected_positions, list)
        or corrected_positions != sorted(set(corrected_positions))
        or any(not isinstance(item, int) or isinstance(item, bool) for item in corrected_positions)
        or len(corrected_positions) != corrected
        or any(not 0 <= item < authorized for item in corrected_positions)
        or conclusion_positions != list(range(authorized))
        or (fact.get("correction_classification") == "none" and corrected != 0)
        or (fact.get("correction_classification") == "strict_subset" and corrected == 0)
    ):
        return False
    refs = (fact.get("material_file_ref"), fact.get("analysis_file_ref"))
    if any(
        not isinstance(ref, Mapping)
        or set(ref) != {"record_type", "record_id"}
        or ref.get("record_type") != "file_record"
        or not isinstance(ref.get("record_id"), str)
        for ref in refs
    ):
        return False
    spans = fact.get("code_evidence_spans")
    if not isinstance(spans, list) or not spans:
        return False
    for span in spans:
        if not isinstance(span, Mapping) or set(span) != {
            "role",
            "family_position",
            "path",
            "start_line",
            "end_line",
            "start_column",
            "end_column",
        }:
            return False
        coordinates = (
            span.get("start_line"),
            span.get("end_line"),
            span.get("start_column"),
            span.get("end_column"),
        )
        if (
            not isinstance(span.get("role"), str)
            or not span.get("role")
            or span.get("path") != "analysis.py"
            or (
                span.get("family_position") is not None
                and (
                    not isinstance(span.get("family_position"), int)
                    or isinstance(span.get("family_position"), bool)
                    or not 0 <= int(span["family_position"]) < authorized
                )
            )
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 1
                for value in coordinates
            )
            or int(span["end_line"]) < int(span["start_line"])
        ):
            return False
    return True


def _valid_code_dependence_fact_shape(fact: Mapping[str, Any]) -> bool:
    csv_path = fact.get("material_input_path")
    analysis_path = fact.get("analysis_path")
    unit = fact.get("authorized_unit_column")
    group = fact.get("group_contrast_column")
    digests = (
        fact.get("material_input_content_digest"),
        fact.get("analysis_content_digest"),
        fact.get("authority_binding_digest"),
    )
    if (
        not _safe_path(csv_path, {".csv"})
        or analysis_path != "analysis.py"
        or not isinstance(unit, str)
        or _SAFE_COLUMN.fullmatch(unit) is None
        or not isinstance(group, str)
        or _SAFE_COLUMN.fullmatch(group) is None
        or unit == group
        or any(not isinstance(value, str) or _SHA256.fullmatch(value) is None for value in digests)
        or fact.get("reader_api")
        not in {
            "pandas_read_csv_v1",
            "pandas_read_csv_parse_dates_v1",
            "numpy_genfromtxt_named_csv_v1",
            "csv_dictreader_materialized_v1",
            "csv_dictreader_bucket_loop_v1",
        }
        or fact.get("procedure_id") not in {"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"}
        or fact.get("procedure_variant") not in {"student", "welch", "mannwhitneyu"}
        or fact.get("accepted_reader_count") != 1
    ):
        return False
    true_fields = (
        "composite_key_scan_complete",
        "alternate_analysis_file_scan_complete",
        "other_python_statistics_import_scan_complete",
        "all_test_operand_paths_rooted_in_authorized_reader",
        "all_csv_rows_partitioned",
        "aggregation_path_scan_complete",
        "dependence_guard_scan_complete",
        "unsupported_call_scan_complete",
        "unregistered_output_call_scan_complete",
    )
    if any(fact.get(field) is not True for field in true_fields):
        return False
    integers = (
        "data_row_count",
        "distinct_unit_count",
        "repeated_unit_count",
        "maximum_unit_multiplicity",
        "dataflow_max_definition_nodes",
        "descriptive_loop_count",
    )
    if any(
        not isinstance(fact.get(field), int) or isinstance(fact.get(field), bool)
        for field in integers
    ):
        return False
    n = int(fact["data_row_count"])
    distinct = int(fact["distinct_unit_count"])
    repeated = int(fact["repeated_unit_count"])
    maximum = int(fact["maximum_unit_multiplicity"])
    depth = int(fact["dataflow_max_definition_nodes"])
    if not (
        n > distinct >= 2
        and repeated >= 1
        and maximum >= 2
        and 1 <= depth <= 16
        and int(fact["descriptive_loop_count"]) >= 0
    ):
        return False
    sorted_arrays = (
        "composite_key_candidate_columns",
        "distinct_count_excluded_columns",
        "within_unit_index_columns",
        "unique_pair_within_unit_index_columns",
        "unique_nonindex_authorized_unit_composite_columns",
        "output_sink_kinds",
    )
    for field in sorted_arrays:
        values = fact.get(field)
        if (
            not isinstance(values, list)
            or any(not isinstance(value, str) or not value for value in values)
            or values != sorted(set(values))
        ):
            return False
    if fact.get("unique_nonindex_authorized_unit_composite_columns") != []:
        return False
    selections = fact.get("selection_kinds")
    groups = fact.get("group_values")
    counts = fact.get("group_row_counts")
    if (
        not isinstance(selections, list)
        or len(selections) != 2
        or any(not isinstance(value, str) or not value for value in selections)
        or not isinstance(groups, list)
        or len(groups) != 2
        or any(not isinstance(value, str) or not value for value in groups)
        or len(set(groups)) != 2
        or not isinstance(counts, list)
        or len(counts) != 2
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in counts
        )
        or sum(counts) != n
    ):
        return False
    spans = fact.get("code_evidence_spans")
    if not isinstance(spans, list):
        return False
    roles: list[str] = []
    for span in spans:
        if not isinstance(span, Mapping) or set(span) != {
            "role",
            "path",
            "start_line",
            "end_line",
            "start_column",
            "end_column",
        }:
            return False
        role = span.get("role")
        roles.append(str(role))
        coordinates = [
            span.get("start_line"),
            span.get("end_line"),
            span.get("start_column"),
            span.get("end_column"),
        ]
        if (
            role not in {"reader", "left_selection", "right_selection", "procedure", "output_sink"}
            or span.get("path") != "analysis.py"
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 1
                for value in coordinates
            )
            or int(span["end_line"]) < int(span["start_line"])
        ):
            return False
    return bool(
        roles.count("reader") == 1
        and roles.count("left_selection") == 1
        and roles.count("right_selection") == 1
        and roles.count("procedure") == 1
        and roles.count("output_sink") >= 1
    )


def _code_fact_sources_resolve(fact: Mapping[str, Any], source_refs: list[object]) -> bool:
    return all(
        any(
            isinstance(source, Mapping)
            and source.get("path") == path
            and source.get("content_digest") == digest
            for source in source_refs
        )
        for path, digest in (
            (fact.get("material_input_path"), fact.get("material_input_content_digest")),
            (fact.get("analysis_path"), fact.get("analysis_content_digest")),
        )
    )


def _valid_dependence_fact_shape(fact: Mapping[str, Any]) -> bool:
    csv_path = fact.get("material_input_path")
    report_path = fact.get("report_path")
    column = fact.get("authorized_unit_column")
    group = fact.get("group_contrast_column")
    digests = (
        fact.get("material_input_content_digest"),
        fact.get("report_content_digest"),
        fact.get("authority_binding_digest"),
    )
    material_ref = fact.get("material_file_ref")
    if (
        not _safe_path(csv_path, {".csv"})
        or not _safe_path(report_path, {".md", ".markdown"})
        or not isinstance(column, str)
        or _SAFE_COLUMN.fullmatch(column) is None
        or not isinstance(group, str)
        or _SAFE_COLUMN.fullmatch(group) is None
        or column == group
        or any(not isinstance(value, str) or _SHA256.fullmatch(value) is None for value in digests)
        or not isinstance(material_ref, Mapping)
        or set(material_ref) != {"record_type", "record_id"}
        or material_ref.get("record_type") != "file_record"
        or not isinstance(material_ref.get("record_id"), str)
        or not material_ref.get("record_id")
        or fact.get("n_evidence_kind")
        not in {
            "admission_literal",
            "nearby_total_literal",
            "ttest_measurement_rows_literal",
            "two_group_sum",
        }
        or fact.get("admission_template_id")
        not in {
            "numbered_measurement_rows",
            "sampling_day_file_rows",
            "selected_path_nubbin_rows",
            "individual_chamber_readings",
        }
        or fact.get("selected_path_binding_kind")
        not in {"source_file_anchor", "the_file_records_anchor", "direct_admission_path"}
        or (
            fact.get("admission_template_id") == "selected_path_nubbin_rows"
            and fact.get("selected_path_binding_kind") != "direct_admission_path"
        )
        or (
            fact.get("admission_template_id") != "selected_path_nubbin_rows"
            and fact.get("selected_path_binding_kind") == "direct_admission_path"
        )
    ):
        return False
    arrays: dict[str, list[str]] = {}
    for field in (
        "composite_key_candidate_columns",
        "distinct_count_excluded_columns",
        "within_unit_index_columns",
        "unique_pair_within_unit_index_columns",
    ):
        value = fact.get(field)
        if (
            not isinstance(value, list)
            or any(not isinstance(item, str) or not item for item in value)
            or value != sorted(set(value))
        ):
            return False
        arrays[field] = value
    candidates = set(arrays["composite_key_candidate_columns"])
    excluded = set(arrays["distinct_count_excluded_columns"])
    within = set(arrays["within_unit_index_columns"])
    unique_within = set(arrays["unique_pair_within_unit_index_columns"])
    if (
        candidates & excluded
        or column in candidates | excluded
        or group in candidates | excluded
        or not within.issubset(candidates)
        or not unique_within.issubset(within)
    ):
        return False
    groups = fact.get("group_counts")
    if not isinstance(groups, list) or len(groups) not in {0, 2}:
        return False
    labels: list[str] = []
    group_total = 0
    for item in groups:
        if (
            not isinstance(item, Mapping)
            or set(item) != {"label", "n"}
            or not isinstance(item.get("label"), str)
            or not item.get("label")
            or not isinstance(item.get("n"), int)
            or isinstance(item.get("n"), bool)
            or int(item["n"]) < 1
        ):
            return False
        labels.append(str(item["label"]))
        group_total += int(item["n"])
    if labels and (len(set(labels)) != 2 or group_total != fact.get("reported_n")):
        return False
    spans = fact.get("report_evidence_spans")
    return (
        isinstance(spans, list)
        and bool(spans)
        and all(
            _valid_report_span(item, str(report_path), str(fact["report_content_digest"]))
            for item in spans
        )
    )


def _valid_report_span(value: object, report_path: str, report_digest: str) -> bool:
    if not isinstance(value, Mapping) or set(value) != {
        "file_ref",
        "path",
        "content_digest",
        "start_line",
        "end_line",
        "start_column",
        "end_column",
        "parser_result_ref",
    }:
        return False
    file_ref = value.get("file_ref")
    parser_ref = value.get("parser_result_ref")
    integers = [
        value.get("start_line"),
        value.get("end_line"),
        value.get("start_column"),
        value.get("end_column"),
    ]
    return bool(
        value.get("path") == report_path
        and value.get("content_digest") == report_digest
        and isinstance(file_ref, Mapping)
        and set(file_ref) == {"record_type", "record_id"}
        and file_ref.get("record_type") == "file_record"
        and isinstance(file_ref.get("record_id"), str)
        and file_ref.get("record_id")
        and isinstance(parser_ref, Mapping)
        and set(parser_ref) == {"record_type", "record_id"}
        and parser_ref.get("record_type") == "parser_result"
        and isinstance(parser_ref.get("record_id"), str)
        and parser_ref.get("record_id")
        and all(
            isinstance(item, int) and not isinstance(item, bool) and item >= 1 for item in integers
        )
        and int(value["end_line"]) >= int(value["start_line"])
        and (
            int(value["end_line"]) != int(value["start_line"])
            or int(value["end_column"]) >= int(value["start_column"])
        )
    )


def _fact_sources_resolve(fact: Mapping[str, Any], source_refs: list[object]) -> bool:
    csv_found = any(
        isinstance(source, Mapping)
        and source.get("path") == fact.get("material_input_path")
        and source.get("content_digest") == fact.get("material_input_content_digest")
        for source in source_refs
    )
    report_found = any(
        isinstance(source, Mapping)
        and source.get("path") == fact.get("report_path")
        and source.get("content_digest") == fact.get("report_content_digest")
        for source in source_refs
    )
    return csv_found and report_found


def _safe_path(value: object, suffixes: set[str]) -> bool:
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return bool(
        value
        and len(value) <= 512
        and value.isascii()
        and not path.is_absolute()
        and path.as_posix() == value
        and path.suffix.lower() in suffixes
        and all(
            part not in {".", ".."} and _SAFE_SEGMENT.fullmatch(part) is not None
            for part in path.parts
        )
    )


def _dependence_summary(facts: Mapping[str, Any]) -> str:
    column = _json_slot(str(facts["authorized_unit_column"]))
    csv_path = _json_slot(str(facts["material_input_path"]))
    report_path = _json_slot(str(facts["report_path"]))
    n = int(facts["data_row_count"])
    u = int(facts["distinct_unit_count"])
    r = int(facts["repeated_unit_count"])
    return (
        "The frozen method contract requires one analyzed row per value of the human-authorized "
        f"unit column `{column}` in full-digest `{csv_path}`. For the selected analysis, "
        f"`{report_path}` states that all `{n}` CSV rows entered a two-sample "
        f"`scipy.stats.ttest_ind`-family test as individual observations; `{column}` has `{u}` "
        f"distinct nonempty values and `{r}` values repeat across those rows. Those two frozen "
        "representations conflict. This Finding is limited to that contract-versus-report conflict. "
        "It does not establish that the contract's scientific requirement is correct, that project "
        "code executed the reported analysis, or that the statistics are invalid. Uninspected project "
        "code may have pseudobulked or otherwise transformed the table. It also does not establish "
        "numerical causality, bias direction, universal scientific correctness, or invalidity outside "
        "this selected analysis."
    )


def _code_dependence_summary(facts: Mapping[str, Any], *, composite_key_limit: bool = False) -> str:
    csv_path = _json_slot(str(facts["material_input_path"]))
    unit = _json_slot(str(facts["authorized_unit_column"]))
    group = _json_slot(str(facts["group_contrast_column"]))
    procedure = _json_slot(str(facts["procedure_id"]))
    n = int(facts["data_row_count"])
    distinct = int(facts["distinct_unit_count"])
    repeated = int(facts["repeated_unit_count"])
    maximum = int(facts["maximum_unit_multiplicity"])
    summary = (
        f"The frozen requirement for `{csv_path}` permits one analyzed row per `{unit}`. In "
        f"`analysis.py`, the two checked arguments to `{procedure}` are direct `{group}` row "
        f"selections from that CSV and jointly cover all `{n}` rows; the table contains "
        f"`{distinct}` distinct `{unit}` values, `{repeated}` of them repeat, and the maximum "
        "multiplicity is "
        f"`{maximum}`. The static contract representation and the checked code/dataflow "
        "representation therefore conflict. The contract author may be wrong, and static "
        "source does not establish execution, statistical invalidity, numerical impact, bias "
        "direction, or the adequacy of unsupported or uninspected analysis paths."
    )
    if composite_key_limit:
        summary += " The declared unit column may be one component of a composite key."
    return summary


def _multiple_testing_summary(facts: Mapping[str, Any]) -> str:
    return _MULTIPLE_TESTING_SUMMARY_TEMPLATE.format(
        CSV_PATH=_json_slot(str(facts["material_input_path"])),
        GROUP_COLUMN=_json_slot(str(facts["group_contrast_column"])),
        OUTCOME_COLUMNS=json.dumps(
            facts["outcome_columns"], ensure_ascii=True, separators=(",", ":")
        ),
        AUTHORIZED_COUNT=int(facts["authorized_count"]),
        PERFORMED_COUNT=int(facts["performed_count"]),
        CORRECTED_COUNT=int(facts["corrected_count"]),
        UNCORRECTED_COUNT=int(facts["uncorrected_count"]),
        TEST_API=_json_slot(str(facts["registered_test_api"])),
    )


def _multiple_testing_v2_summary(facts: Mapping[str, Any]) -> str:
    return _MULTIPLE_TESTING_V2_SUMMARY_TEMPLATE.format(
        CSV_PATH=_json_slot(str(facts["material_input_path"])),
        GROUP_COLUMN=_json_slot(str(facts["group_contrast_column"])),
        OUTCOME_COLUMNS=json.dumps(
            facts["outcome_columns"], ensure_ascii=True, separators=(",", ":")
        ),
        AUTHORIZED_COUNT=int(facts["authorized_count"]),
        PERFORMED_COUNT=int(facts["performed_count"]),
        CORRECTED_COUNT=int(facts["corrected_count"]),
        UNCORRECTED_COUNT=int(facts["uncorrected_count"]),
    )


def _json_slot(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)[1:-1]
