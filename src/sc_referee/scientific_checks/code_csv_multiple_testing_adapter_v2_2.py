"""Contract-bound CSV and Python-AST multiple-testing observation.

Only controller-frozen authority records, authorized CSV bytes, code structure, and exact API
identities enter the detector. Project code and prose are never executed or interpreted.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.adapter_common import adapter_implementation_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST,
    MultipleTestingDataflowFacts,
    analyze_code_csv_multiple_testing_dataflow,
    select_code_source_envelope,
)
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionReceipt,
    NormalizedMethodObservation,
    ObservationState,
    RecordRef,
    RoleBinding,
)
from sc_referee.scientific_checks.scope_joins import full_digest_identity_path

MULTIPLE_TESTING_CODE_CHECK_ID = (
    "check:authorized-complete-family-correction-over-code-test-battery"
)
MULTIPLE_TESTING_CODE_CHECK_VERSION = "2.2.0"
MULTIPLE_TESTING_CODE_CANDIDATE_ID = "complete-correction-over-authorized-outcome-family"
MULTIPLE_TESTING_CODE_ADAPTER_ID = (
    "adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1"
)
MULTIPLE_TESTING_CODE_ADAPTER_VERSION = "2.2.0"
COMPLETE_FAMILY_CORRECTION_OPERAND = "complete_family_correction_over_authorized_outcome_family"
NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND = "no_recognized_family_correction"
STRICT_SUBSET_FAMILY_CORRECTION_OPERAND = "recognized_strict_subset_family_correction"
MULTIPLE_TESTING_CODE_SEMANTIC_ROLES = (
    "authorized_test_family",
    "performed_test_battery",
    "multiplicity_correction_call",
    "selected_result_sink",
)
MULTIPLE_TESTING_CODE_ROLE_BINDINGS = (
    RoleBinding("authorized_test_family", "human_authorized_ordered_csv_family"),
    RoleBinding("performed_test_battery", "exact_registered_family_call_battery"),
    RoleBinding("multiplicity_correction_call", "completed_correction_membership_census"),
    RoleBinding("selected_result_sink", "proved_code_conclusion_sinks"),
)
MULTIPLE_TESTING_CODE_COUNTEREVIDENCE = (
    "verified-contract-authority",
    "authorized-family-shape",
    "frozen-authority-material",
    "authorized-family-csv-domain",
    "analysis-source-envelope",
    "api-resolution-and-helper-expansion",
    "single-authorized-reader-lineage",
    "exact-family-test-call-census",
    "uniform-registered-test-api",
    "family-test-operand-bijection",
    "complete-selected-group-row-lineage",
    "local-registered-pvalue-lineage",
    "family-extremum-census",
    "closed-correction-census",
    "closed-decision-threshold-census",
    "hierarchy-partition-resampling-prefix-census",
    "complete-pderived-conclusion-sink-census",
    "prose-free-source-view",
    "full-digest-snapshot-scope",
)

_PROFILE_VERSION = "1.2.0"
_AUTHORITY_ROLE = "authorized_test_family"
_ANSWER_DIGEST_PROFILE = "canonical-json-excluding-answer-digest-v1"
_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_SAFE_COLUMN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
_SAFE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_FAMILY_MEMBER_RULE = "one-two-group-test-per-named-outcome-column"
_CORRECTION_SCOPE = "complete-authorized-family"
_CLOSED_REASONS = frozenset(
    {
        "verified-contract-authority-unavailable",
        "authorized-test-family-shape-unsupported",
        "authorized-family-cardinality-below-three",
        "frozen-authority-material-mismatch",
        "authorized-family-csv-domain-unavailable",
        "authorized-group-domain-not-exactly-two",
        "analysis-source-envelope-unavailable",
        "alternate-analysis-file-present",
        "statistics-api-imported-outside-analysis-py",
        "api-resolution-ambiguous",
        "analysis-scope-structure-unsupported",
        "dataflow-definition-ceiling-exceeded",
        "helper-callee-not-simple-name",
        "helper-definition-unavailable-or-nonunique",
        "helper-parameter-shape-unsupported",
        "helper-parameter-default-unsupported",
        "helper-variadic-parameter-unsupported",
        "helper-argument-binding-unsupported",
        "helper-recursion-unsupported",
        "helper-return-count-unsupported",
        "helper-return-position-unsupported",
        "helper-return-expression-unsupported",
        "helper-global-nonlocal-unsupported",
        "helper-closure-or-nested-definition-unsupported",
        "helper-async-decorator-or-yield-unsupported",
        "helper-body-statement-unsupported",
        "helper-free-name-unbound",
        "helper-inlining-depth-exceeded",
        "helper-call-site-reentry-unsupported",
        "additional-accepted-reader-present",
        "authorized-reader-lineage-unavailable",
        "test-battery-cardinality-unresolved",
        "authorized-family-test-census-incomplete",
        "extra-registered-test-outside-authorized-family",
        "mixed-test-api-family",
        "test-operand-lineage-unresolved",
        "selected-group-row-completeness-unproven",
        "upstream-correction-lineage-unresolved",
        "pvalue-family-collection-unresolved",
        "unresolved-pvalue-consumer",
        "family-pvalue-extremum-reduction-present",
        "correction-family-lineage-unresolved",
        "unresolved-manual-correction-present",
        "pvalue-scalar-cast-or-rounding-unsupported",
        "unresolved-decision-threshold",
        "hierarchical-gatekeeping-present",
        "pvalue-control-dependence-unresolved",
        "multiple-family-partition-present",
        "resampling-cardinality-unresolved",
        "permutation-family-control-present",
        "unresolved-inference-sibling-present",
        "pderived-conclusion-family-incomplete",
        "conclusion-output-sink-unavailable",
        "multiple-testing-code-inspection-exception",
    }
)


@dataclass(frozen=True)
class _Authority:
    path: str
    group_column: str
    outcome_columns: tuple[str, ...]
    content_digest: str
    binding_digest: str


@dataclass(frozen=True)
class _CsvFacts:
    header: tuple[str, ...]
    row_count: int
    group_values: tuple[str, str]
    group_counts: tuple[int, int]


@dataclass(frozen=True)
class MultipleTestingCodeEvidenceProjection:
    material_input_path: str
    material_input_content_digest: str
    material_file_ref: RecordRef
    group_contrast_column: str
    outcome_columns: tuple[str, ...]
    group_value_domain_digest: str
    authorized_count: int
    performed_count: int
    corrected_count: int
    uncorrected_count: int
    registered_test_api: str
    correction_classification: str
    corrected_positions: tuple[int, ...]
    conclusion_positions: tuple[int, ...]
    analysis_path: str
    analysis_content_digest: str
    analysis_file_ref: RecordRef
    authority_binding_digest: str
    code_evidence_spans: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        positions = set(range(self.authorized_count))
        if (
            self.material_file_ref.record_type != "file_record"
            or self.analysis_file_ref.record_type != "file_record"
            or self.analysis_path != "analysis.py"
            or any(
                _SAFE_DIGEST.fullmatch(value) is None
                for value in (
                    self.material_input_content_digest,
                    self.group_value_domain_digest,
                    self.analysis_content_digest,
                    self.authority_binding_digest,
                )
            )
            or self.authorized_count < 3
            or self.performed_count != self.authorized_count
            or self.corrected_count != len(self.corrected_positions)
            or self.uncorrected_count != self.performed_count - self.corrected_count
            or self.uncorrected_count < 0
            or not set(self.corrected_positions).issubset(positions)
            or set(self.conclusion_positions) != positions
            or self.registered_test_api not in {"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"}
            or self.correction_classification not in {"none", "strict_subset", "complete"}
            or self.outcome_columns != tuple(dict.fromkeys(self.outcome_columns))
            or len(self.outcome_columns) != self.authorized_count
            or not self.code_evidence_spans
        ):
            raise ValueError("multiple-testing code fact is outside the closed profile")
        if self.correction_classification == "complete":
            if self.corrected_count != self.authorized_count or self.uncorrected_count != 0:
                raise ValueError("complete correction classification is inconsistent")
        elif self.correction_classification == "strict_subset":
            if not 0 < self.corrected_count < self.authorized_count:
                raise ValueError("strict-subset correction classification is inconsistent")
        elif self.corrected_count != 0:
            raise ValueError("none correction classification is inconsistent")

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "profile": "code_csv_multiple_testing_evidence_v1",
            "material_input_path": self.material_input_path,
            "material_input_content_digest": self.material_input_content_digest,
            "material_file_ref": self.material_file_ref.to_dict(),
            "group_contrast_column": self.group_contrast_column,
            "outcome_columns": list(self.outcome_columns),
            "group_value_domain_digest": self.group_value_domain_digest,
            "authorized_count": self.authorized_count,
            "performed_count": self.performed_count,
            "corrected_count": self.corrected_count,
            "uncorrected_count": self.uncorrected_count,
            "registered_test_api": self.registered_test_api,
            "correction_classification": self.correction_classification,
            "corrected_positions": list(self.corrected_positions),
            "conclusion_positions": list(self.conclusion_positions),
            "analysis_path": self.analysis_path,
            "analysis_content_digest": self.analysis_content_digest,
            "analysis_file_ref": self.analysis_file_ref.to_dict(),
            "authority_binding_digest": self.authority_binding_digest,
            "code_evidence_spans": [dict(item) for item in self.code_evidence_spans],
        }
        value["fact_digest"] = semantic_digest(value)
        return value


@dataclass(frozen=True)
class MultipleTestingCodeObservation(NormalizedMethodObservation):
    multiple_testing_evidence: MultipleTestingCodeEvidenceProjection | None = None

    def to_dict(self) -> dict[str, Any]:
        value = super().to_dict()
        if self.multiple_testing_evidence is not None:
            value["multiple_testing_evidence"] = self.multiple_testing_evidence.to_dict()
        return value


def code_csv_multiple_testing_grammar() -> dict[str, Any]:
    return {
        "grammar_id": "bounded-code-csv-multiple-testing-conflict-v1",
        "grammar_version": MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        "profile_version": _PROFILE_VERSION,
        "check_id": MULTIPLE_TESTING_CODE_CHECK_ID,
        "candidate_id": MULTIPLE_TESTING_CODE_CANDIDATE_ID,
        "source": {
            "path": "analysis.py",
            "parser": "parser:python-ast-tokenize@0.15.1",
            "bytes_max": 1 << 20,
            "ast_nodes_max": 50_000,
            "definition_nodes_max": 16,
            "prose_evidence": False,
        },
        "test_apis": ["scipy.stats.mannwhitneyu", "scipy.stats.ttest_ind"],
        "correction_apis": [
            "sc_referee.calculation_checks.bh.benjamini_hochberg",
            "scipy.stats.false_discovery_control",
            "statsmodels.stats.multitest.fdrcorrection",
            "statsmodels.stats.multitest.multipletests",
        ],
        "semantic_roles": [item.to_dict() for item in MULTIPLE_TESTING_CODE_ROLE_BINDINGS],
        "counterevidence": list(MULTIPLE_TESTING_CODE_COUNTEREVIDENCE),
        "closed_abstention_reasons": sorted(_CLOSED_REASONS),
        "dataflow_implementation_digest": (
            CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST
        ),
        "output_ceiling": "question_only",
        "project_authored_code_execution": False,
    }


def code_csv_multiple_testing_grammar_digest() -> str:
    return semantic_digest(code_csv_multiple_testing_grammar())


CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(
    Path(__file__)
)


@dataclass(frozen=True)
class CodeCsvMultipleTestingAdapter:
    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    complete_operand: CanonicalOperand
    none_operand: CanonicalOperand
    strict_subset_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...] = MULTIPLE_TESTING_CODE_ROLE_BINDINGS

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return code_csv_multiple_testing_grammar_digest()

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        try:
            return self._inspect(context)
        except (ArithmeticError, csv.Error, UnicodeError, ValueError):
            return self._abstain("unsupported", "multiple-testing-code-inspection-exception")

    def _inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        authority = _authority(context.shared_derivations, self.check_manifest)
        if authority is None:
            return self._abstain("unsupported", "verified-contract-authority-unavailable")
        if len(authority.outcome_columns) < 3:
            return self._abstain("unsupported", "authorized-family-cardinality-below-three")
        if len(context.material_inputs) != 1:
            return self._abstain("unsupported", "frozen-authority-material-mismatch")
        material = context.material_inputs[0]
        if material.path != authority.path or material.content_digest != authority.content_digest:
            return self._abstain("unsupported", "frozen-authority-material-mismatch")
        csv_facts = _parse_csv(
            material.content,
            group_column=authority.group_column,
            outcome_columns=authority.outcome_columns,
        )
        if isinstance(csv_facts, str):
            return self._abstain("unsupported", csv_facts)

        envelope = select_code_source_envelope(
            base_records=context.base_records,
            documents=context.documents,
        )
        if envelope.reason is not None or envelope.analysis is None:
            reason = {
                "alternate-analysis-file-present": "alternate-analysis-file-present",
                "statistics-api-imported-outside-analysis-py": (
                    "statistics-api-imported-outside-analysis-py"
                ),
                "api-resolution-ambiguous": "api-resolution-ambiguous",
            }.get(envelope.reason or "", "analysis-source-envelope-unavailable")
            return self._abstain("unsupported", reason)
        analysis = envelope.analysis
        snapshot_ref = _snapshot_ref(context)
        if snapshot_ref is None:
            return self._abstain("unsupported", "analysis-source-envelope-unavailable")
        proof = full_digest_identity_path(
            context.scope_join_graph,
            source_ref=analysis.file_ref,
            snapshot_ref=snapshot_ref,
        )
        if len(proof) != 1:
            return self._abstain("unsupported", "analysis-source-envelope-unavailable")

        dataflow = analyze_code_csv_multiple_testing_dataflow(
            analysis.content,
            authorized_path=authority.path,
            group_column=authority.group_column,
            outcome_columns=authority.outcome_columns,
            csv_header=csv_facts.header,
            group_values=csv_facts.group_values,
            csv_content=material.content,
        )
        if dataflow.reason is not None or dataflow.facts is None:
            reason = dataflow.reason or "multiple-testing-code-inspection-exception"
            if reason not in _CLOSED_REASONS:
                reason = "multiple-testing-code-inspection-exception"
            return self._abstain("unsupported", reason)
        facts = dataflow.facts
        evidence_spans = _evidence_spans(analysis, facts)
        if len(evidence_spans) != len(facts.evidence_spans):
            return self._abstain("unsupported", "analysis-source-envelope-unavailable")
        projection = _projection(
            authority=authority,
            material=material,
            analysis=analysis,
            csv_facts=csv_facts,
            facts=facts,
        )
        receipt_projection = {
            "authority_binding_digest": authority.binding_digest,
            "fact_digest": projection.to_dict()["fact_digest"],
            "scope_join_path": [item.edge.to_dict() for item in proof],
        }
        receipts = tuple(
            InspectionReceipt(
                receipt_id=receipt_id,
                kind="counterevidence",
                state="passed",
                evidence_digest=semantic_digest(
                    {"receipt_id": receipt_id, "projection": receipt_projection}
                ),
                description=f"The finite {receipt_id} check completed.",
            )
            for receipt_id in self.adapter_manifest.counterevidence_profiles
        )
        observed = {
            "complete": self.complete_operand,
            "none": self.none_operand,
            "strict_subset": self.strict_subset_operand,
        }[facts.correction_classification]
        return MultipleTestingCodeObservation(
            check_id=self.check_manifest.check_id,
            check_version=self.check_manifest.check_version,
            check_manifest_digest=self.check_manifest.manifest_digest,
            check_implementation_digest=self.check_manifest.implementation_digest,
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            adapter_manifest_digest=self.adapter_manifest.manifest_digest,
            adapter_implementation_digest=self.implementation_digest,
            parser_id=self.adapter_manifest.parser_id,
            parser_version=self.adapter_manifest.parser_version,
            applicability="applicable",
            completeness="complete",
            evidence_plane="static_source",
            method_target_ref=analysis.file_ref,
            role_bindings=self.role_bindings,
            observed_operand=observed,
            evidence_spans=evidence_spans,
            scope_join_path=tuple(item.edge for item in proof),
            receipts=receipts,
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            multiple_testing_evidence=projection,
        )

    def _abstain(self, state: ObservationState, reason: str) -> NormalizedMethodObservation:
        if reason not in _CLOSED_REASONS:
            reason = "multiple-testing-code-inspection-exception"
        return NormalizedMethodObservation(
            check_id=self.check_manifest.check_id,
            check_version=self.check_manifest.check_version,
            check_manifest_digest=self.check_manifest.manifest_digest,
            check_implementation_digest=self.check_manifest.implementation_digest,
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            adapter_manifest_digest=self.adapter_manifest.manifest_digest,
            adapter_implementation_digest=self.implementation_digest,
            parser_id=self.adapter_manifest.parser_id,
            parser_version=self.adapter_manifest.parser_version,
            applicability=state,
            completeness="not_applicable" if state == "not_applicable" else "incomplete",
            evidence_plane="static_source",
            method_target_ref=None,
            role_bindings=(),
            observed_operand=None,
            evidence_spans=(),
            scope_join_path=(),
            receipts=(
                InspectionReceipt(
                    receipt_id="closed-code-csv-multiple-testing-abstention",
                    kind="counterevidence",
                    state="not_applicable" if state == "not_applicable" else "unsupported",
                    evidence_digest=sha256_digest(reason),
                    description=reason,
                ),
            ),
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            abstention_reason=reason,
        )


def _authority(
    records: Sequence[FrozenBaseRecord], check_manifest: CheckManifest
) -> _Authority | None:
    if len(records) != 2:
        return None
    values: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        try:
            value = json.loads(record.canonical_payload)
        except (UnicodeError, json.JSONDecodeError):
            return None
        if not isinstance(value, dict) or value.get("record_type") != record.ref.record_type:
            return None
        values[record.ref.record_type].append(value)
    if len(values["answer"]) != 1 or len(values["semantic_assertion"]) != 1:
        return None
    answer = values["answer"][0]
    assertion = values["semantic_assertion"][0]
    answer_copy = dict(answer)
    answer_digest = answer_copy.pop("answer_digest", None)
    authority = answer.get("extensions", {}).get("x-semantic-role-authority")
    snapshot = assertion.get("extensions", {}).get("x-authority-binding-snapshot")
    if (
        answer.get("answer_digest_profile") != _ANSWER_DIGEST_PROFILE
        or not isinstance(answer_digest, str)
        or semantic_digest(answer_copy) != answer_digest
        or answer.get("respondent", {}).get("actor_kind") != "human"
        or answer.get("response_source") != "provided_answer_file"
        or answer.get("extensions", {}).get("x-scientific-check-id")
        != MULTIPLE_TESTING_CODE_CHECK_ID
        or answer.get("extensions", {}).get("x-scientific-check-manifest-digest")
        != check_manifest.manifest_digest
        or answer.get("extensions", {}).get("x-selected-candidate-id")
        != MULTIPLE_TESTING_CODE_CANDIDATE_ID
        or assertion.get("predicate") != "verified_intended_selection_process"
        or assertion.get("object") != COMPLETE_FAMILY_CORRECTION_OPERAND
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("semantic_role") != "intended"
        or assertion.get("extensions", {}).get("x-answer-ref")
        != {"record_type": "answer", "record_id": answer.get("answer_id")}
        or assertion.get("extensions", {}).get("x-answer-digest") != answer_digest
        or assertion.get("extensions", {}).get("x-profile-version") != _PROFILE_VERSION
        or assertion.get("extensions", {}).get("x-scientific-check-id")
        != MULTIPLE_TESTING_CODE_CHECK_ID
        or assertion.get("extensions", {}).get("x-scientific-check-manifest-digest")
        != check_manifest.manifest_digest
        or assertion.get("extensions", {}).get("x-semantic-role-authority") != authority
        or answer.get("answer_value")
        != {
            "selection_process": COMPLETE_FAMILY_CORRECTION_OPERAND,
            "semantic_role_authority": authority,
        }
        or not isinstance(authority, Mapping)
        or set(authority) != {_AUTHORITY_ROLE}
        or not isinstance(snapshot, Mapping)
        or set(snapshot) != {_AUTHORITY_ROLE}
    ):
        return None
    family = authority.get(_AUTHORITY_ROLE)
    bound = snapshot.get(_AUTHORITY_ROLE)
    if (
        not isinstance(family, Mapping)
        or set(family)
        != {
            "material_input_path",
            "group_contrast_column",
            "outcome_columns",
            "family_member_rule",
            "correction_scope",
        }
        or not isinstance(bound, Mapping)
        or set(bound)
        != {
            "material_input_path",
            "group_contrast_column",
            "outcome_columns",
            "family_member_rule",
            "correction_scope",
            "material_input_content_digest",
        }
        or {key: bound.get(key) for key in family} != dict(family)
    ):
        return None
    path = family.get("material_input_path")
    group = family.get("group_contrast_column")
    outcomes = family.get("outcome_columns")
    digest = bound.get("material_input_content_digest")
    if (
        not isinstance(path, str)
        or not _safe_path(path)
        or not isinstance(group, str)
        or _SAFE_COLUMN.fullmatch(group) is None
        or not isinstance(outcomes, list)
        or len(outcomes) < 3
        or not all(
            isinstance(item, str) and _SAFE_COLUMN.fullmatch(item) is not None for item in outcomes
        )
        or len(outcomes) != len(set(outcomes))
        or group in outcomes
        or family.get("family_member_rule") != _FAMILY_MEMBER_RULE
        or family.get("correction_scope") != _CORRECTION_SCOPE
        or not isinstance(digest, str)
        or _SAFE_DIGEST.fullmatch(digest) is None
    ):
        return None
    return _Authority(
        path,
        group,
        tuple(str(item) for item in outcomes),
        digest,
        semantic_digest(dict(snapshot)),
    )


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(
        value
        and len(value) <= 512
        and value.isascii()
        and not path.is_absolute()
        and path.as_posix() == value
        and path.suffix.lower() == ".csv"
        and all(
            part not in {".", ".."} and _SAFE_SEGMENT.fullmatch(part) is not None
            for part in path.parts
        )
    )


def _parse_csv(
    content: bytes,
    *,
    group_column: str,
    outcome_columns: tuple[str, ...],
) -> _CsvFacts | str:
    if content.startswith(b"\xef\xbb\xbf") or b"\x00" in content:
        return "authorized-family-csv-domain-unavailable"
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "authorized-family-csv-domain-unavailable"
    if re.search(r"\r(?!\n)", text):
        return "authorized-family-csv-domain-unavailable"
    old_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(1 << 20)
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    except (csv.Error, OverflowError):
        return "authorized-family-csv-domain-unavailable"
    finally:
        csv.field_size_limit(old_limit)
    if (
        not rows
        or not rows[0]
        or len(rows[0]) > 512
        or not 4 <= len(rows) <= 100_001
        or len(set(rows[0])) != len(rows[0])
        or any(len(row) != len(rows[0]) for row in rows[1:])
        or group_column not in rows[0]
        or any(column not in rows[0] for column in outcome_columns)
    ):
        return "authorized-family-csv-domain-unavailable"
    header = tuple(rows[0])
    group_index = header.index(group_column)
    outcome_indexes = [header.index(column) for column in outcome_columns]
    group_counts = Counter(row[group_index] for row in rows[1:])
    if len(group_counts) != 2 or any(not value for value in group_counts):
        return "authorized-group-domain-not-exactly-two"
    group_values = tuple(sorted(group_counts, key=lambda value: value.encode("utf-8")))
    assert len(group_values) == 2
    if any(group_counts[value] < 2 for value in group_values):
        return "authorized-family-csv-domain-unavailable"
    for row in rows[1:]:
        for index in outcome_indexes:
            try:
                value = Decimal(row[index])
            except InvalidOperation:
                return "authorized-family-csv-domain-unavailable"
            if not value.is_finite():
                return "authorized-family-csv-domain-unavailable"
    return _CsvFacts(
        header,
        len(rows) - 1,
        (group_values[0], group_values[1]),
        (group_counts[group_values[0]], group_counts[group_values[1]]),
    )


def _snapshot_ref(context: FrozenInspectionContext) -> RecordRef | None:
    matches = [
        record.ref
        for record in context.base_records
        if record.ref.record_type == "repository_snapshot"
    ]
    return matches[0] if len(matches) == 1 else None


def _evidence_spans(analysis: Any, facts: MultipleTestingDataflowFacts) -> tuple[EvidenceSpan, ...]:
    if analysis.parser_result_ref is None:
        return ()
    return tuple(
        EvidenceSpan(
            file_ref=analysis.file_ref,
            path=analysis.path,
            content_digest=analysis.content_digest,
            start_line=item.start_line,
            end_line=item.end_line,
            start_column=item.start_column,
            end_column=item.end_column,
            parser_result_ref=analysis.parser_result_ref,
        )
        for item in facts.evidence_spans
    )


def _projection(
    *,
    authority: _Authority,
    material: Any,
    analysis: Any,
    csv_facts: _CsvFacts,
    facts: MultipleTestingDataflowFacts,
) -> MultipleTestingCodeEvidenceProjection:
    authorized = len(authority.outcome_columns)
    corrected = len(facts.corrected_positions)
    return MultipleTestingCodeEvidenceProjection(
        material_input_path=authority.path,
        material_input_content_digest=material.content_digest,
        material_file_ref=material.file_ref,
        group_contrast_column=authority.group_column,
        outcome_columns=authority.outcome_columns,
        group_value_domain_digest=semantic_digest(list(csv_facts.group_values)),
        authorized_count=authorized,
        performed_count=facts.family_size,
        corrected_count=corrected,
        uncorrected_count=authorized - corrected,
        registered_test_api=facts.registered_test_api,
        correction_classification=facts.correction_classification,
        corrected_positions=facts.corrected_positions,
        conclusion_positions=facts.conclusion_positions,
        analysis_path=analysis.path,
        analysis_content_digest=analysis.content_digest,
        analysis_file_ref=analysis.file_ref,
        authority_binding_digest=authority.binding_digest,
        code_evidence_spans=tuple(
            {
                "role": item.role,
                "family_position": item.family_position,
                "path": "analysis.py",
                "start_line": item.start_line,
                "end_line": item.end_line,
                "start_column": item.start_column,
                "end_column": item.end_column,
            }
            for item in facts.evidence_spans
        ),
    )
