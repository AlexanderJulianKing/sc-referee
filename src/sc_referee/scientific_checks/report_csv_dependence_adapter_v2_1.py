"""Closed report-plus-CSV dependence observation for row-wise two-sample t tests.

This adapter consumes only immutable controller-frozen bytes.  It never imports or
executes project code, never infers scientific authority from project content, and
abstains whenever the exact contract, CSV, Markdown, lexical, or scope envelope is
not complete.
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
from itertools import pairwise
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.adapter_common import adapter_implementation_digest
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    InspectionReceipt,
    NormalizedMethodObservation,
    ObservationState,
    RecordRef,
    RoleBinding,
)
from sc_referee.scientific_checks.dependence_recognition_adapter import (
    DEPENDENCE_RECOGNITION_CANDIDATE_ID,
    DEPENDENCE_RECOGNITION_CHECK_ID,
    DEPENDENCE_RECOGNITION_ROLE_BINDINGS,
    DEPENDENCE_RECOGNITION_SEMANTIC_ROLES,
    MULTIPLE_ROWS_PER_AUTHORIZED_UNIT,
    ONE_ROW_PER_AUTHORIZED_UNIT,
)
from sc_referee.scientific_checks.scope_joins import selected_publication_path

DEPENDENCE_RECOGNITION_CHECK_VERSION = "1.2.0"
REPORT_CSV_DEPENDENCE_ADAPTER_ID = (
    "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
    "report-csv-rowwise-ttest-v1"
)
REPORT_CSV_DEPENDENCE_ADAPTER_VERSION = "1.0.0"
REPORT_CSV_DEPENDENCE_COUNTEREVIDENCE = (
    "verified-contract-authority",
    "exact-selected-full-csv",
    "complete-csv-domain",
    "d1-prime-composite-scan",
    "parsed-selected-markdown",
    "report-wide-suppressor-scan",
    "selected-result-test-co-reference",
    "literal-path-bound-row-entry-admission",
    "exact-report-row-count",
    "bounded-minimal-join",
    "inferential-result-witness",
    "selected-publication-scope",
)

_PROFILE_VERSION = "1.1.0"
_UNIT_ROLE = "authorized_independent_unit_key"
_ANSWER_DIGEST_PROFILE = "canonical-json-excluding-answer-digest-v1"
_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_SAFE_COLUMN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")
_TOKEN = re.compile(r"[a-z0-9]+")
_UNSIGNED_N = re.compile(r"[1-9][0-9]*\Z")
_DEC = r"[+-]?(?:(?:0|[1-9][0-9]*)(?:\.[0-9]+)?|\.[0-9]+)"
_SCI = r"[+-]?(?:(?:0|[1-9][0-9]*)(?:\.[0-9]+)?|\.[0-9]+)[eE][+-]?(?:0|[1-9][0-9]*)"
_NUMBER_BOUNDARY_LEFT = r"(?<![A-Za-z0-9_.])"
_NUMBER_BOUNDARY_RIGHT = r"(?![A-Za-z0-9_])(?!\.[0-9])"
_PATH_BOUNDARY_RIGHT = r"(?![A-Za-z0-9_/-])(?!\.[A-Za-z0-9_/-])"
_CSV_PATH = re.compile(
    r"(?<![A-Za-z0-9._/-])(?:[A-Za-z0-9][A-Za-z0-9._-]*/)*"
    rf"[A-Za-z0-9][A-Za-z0-9._-]*\.[cC][sS][vV]{_PATH_BOUNDARY_RIGHT}",
)
_ATX = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_LIST = re.compile(r"^ {0,3}(?:[-+*]|[1-9][0-9]*[.)])[ \t]+(.*)$")
_TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")

_TEST_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("student", re.compile(r"(?<![a-z0-9])two-sample student t-test(?![a-z0-9])")),
    ("student", re.compile(r"(?<![a-z0-9])two-sample student t test(?![a-z0-9])")),
    ("welch", re.compile(r"(?<![a-z0-9])welch's two-sample t-test(?![a-z0-9])")),
    ("welch", re.compile(r"(?<![a-z0-9])welch's two-sample t test(?![a-z0-9])")),
    ("neutral", re.compile(r"(?<![a-z0-9_.])scipy\.stats\.ttest_ind(?![a-z0-9_.])")),
)

_COMPETING_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\bpaired t-test\b",
        r"\bttest_rel\b",
        r"\banova\b",
        r"\bregression\b",
        r"\bmann-whitney\b",
        r"\bwilcoxon\b",
        r"\bchi-square\b",
        r"\bfisher's exact\b",
        r"\bbinomtest\b",
        r"\bpermutation test\b",
    )
)

_FIXED_UNIT_NOUNS = frozenset(
    {
        "unit",
        "subject",
        "donor",
        "patient",
        "animal",
        "plot",
        "colony",
        "reactor",
        "cage",
        "well",
        "site",
        "litter",
        "participant",
        "cluster",
        "mouse",
        "tank",
    }
)
_FINAL_STEM_TOKENS = frozenset(
    {"id", "ids", "identifier", "identifiers", "code", "codes", "key", "keys"}
)


@dataclass(frozen=True)
class _Authority:
    answer: dict[str, Any]
    assertion: dict[str, Any]
    path: str
    unit_column: str
    group_column: str
    content_digest: str
    binding_digest: str


@dataclass(frozen=True)
class _CsvFacts:
    header: tuple[str, ...]
    n: int
    unit_count: int
    repeated_unit_count: int
    maximum_multiplicity: int
    candidate_columns: tuple[str, ...]
    distinct_excluded_columns: tuple[str, ...]
    within_unit_index_columns: tuple[str, ...]
    unique_pair_within_unit_index_columns: tuple[str, ...]
    unique_nonindex_columns: tuple[str, ...]


@dataclass(frozen=True)
class _VisibleBlock:
    block_id: int
    kind: str
    start_line: int
    end_line: int
    text: str
    exact_text: str


@dataclass(frozen=True)
class _Node:
    role: str
    family: str
    block_ids: tuple[int, ...]
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    normalized_match: str


@dataclass(frozen=True)
class _ReportFacts:
    spans: tuple[EvidenceSpan, ...]
    reported_n: int
    n_evidence_kind: str
    group_counts: tuple[tuple[str, int], ...]
    admission_template_id: str
    selected_path_binding_kind: str


@dataclass(frozen=True)
class RowEntryEvidenceProjection:
    material_input_path: str
    material_input_content_digest: str
    material_file_ref: RecordRef
    authorized_unit_column: str
    group_contrast_column: str
    data_row_count: int
    distinct_unit_count: int
    repeated_unit_count: int
    maximum_unit_multiplicity: int
    composite_key_scan_complete: bool
    composite_key_candidate_columns: tuple[str, ...]
    distinct_count_excluded_columns: tuple[str, ...]
    within_unit_index_columns: tuple[str, ...]
    unique_pair_within_unit_index_columns: tuple[str, ...]
    unique_nonindex_authorized_unit_composite_columns: tuple[str, ...]
    report_path: str
    report_content_digest: str
    procedure_id: str
    reported_n: int
    n_evidence_kind: str
    group_counts: tuple[tuple[str, int], ...]
    admission_template_id: str
    selected_path_binding_kind: str
    authority_binding_digest: str
    report_evidence_spans: tuple[EvidenceSpan, ...]

    def __post_init__(self) -> None:
        digests = (
            self.material_input_content_digest,
            self.report_content_digest,
            self.authority_binding_digest,
        )
        arrays = (
            self.composite_key_candidate_columns,
            self.distinct_count_excluded_columns,
            self.within_unit_index_columns,
            self.unique_pair_within_unit_index_columns,
            self.unique_nonindex_authorized_unit_composite_columns,
        )
        if (
            self.material_file_ref.record_type != "file_record"
            or any(re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None for value in digests)
            or not self.material_input_path
            or not self.report_path
            or not self.authorized_unit_column
            or not self.group_contrast_column
            or self.authorized_unit_column == self.group_contrast_column
            or self.data_row_count < 2
            or not 2 <= self.distinct_unit_count < self.data_row_count
            or self.repeated_unit_count < 1
            or self.maximum_unit_multiplicity < 2
            or self.reported_n != self.data_row_count
            or self.composite_key_scan_complete is not True
            or any(value != tuple(sorted(set(value))) for value in arrays)
            or self.unique_nonindex_authorized_unit_composite_columns
            or not set(self.within_unit_index_columns).issubset(
                self.composite_key_candidate_columns
            )
            or not set(self.unique_pair_within_unit_index_columns).issubset(
                self.within_unit_index_columns
            )
            or self.procedure_id != "scipy.stats.ttest_ind_two_sample"
            or self.n_evidence_kind
            not in {
                "admission_literal",
                "nearby_total_literal",
                "ttest_measurement_rows_literal",
                "two_group_sum",
            }
            or len(self.group_counts) not in {0, 2}
            or any(not label or count < 1 for label, count in self.group_counts)
            or (
                bool(self.group_counts)
                and sum(count for _, count in self.group_counts) != self.reported_n
            )
            or self.admission_template_id
            not in {
                "numbered_measurement_rows",
                "sampling_day_file_rows",
                "selected_path_nubbin_rows",
                "individual_chamber_readings",
            }
            or self.selected_path_binding_kind
            not in {
                "source_file_anchor",
                "the_file_records_anchor",
                "direct_admission_path",
            }
            or not self.report_evidence_spans
        ):
            raise ValueError("row-entry evidence projection is outside the exact closed profile")

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": "report_csv_row_entry_evidence_v1",
            "material_input_path": self.material_input_path,
            "material_input_content_digest": self.material_input_content_digest,
            "material_file_ref": self.material_file_ref.to_dict(),
            "authorized_unit_column": self.authorized_unit_column,
            "group_contrast_column": self.group_contrast_column,
            "data_row_count": self.data_row_count,
            "distinct_unit_count": self.distinct_unit_count,
            "repeated_unit_count": self.repeated_unit_count,
            "maximum_unit_multiplicity": self.maximum_unit_multiplicity,
            "composite_key_scan_complete": self.composite_key_scan_complete,
            "composite_key_candidate_columns": list(self.composite_key_candidate_columns),
            "distinct_count_excluded_columns": list(self.distinct_count_excluded_columns),
            "within_unit_index_columns": list(self.within_unit_index_columns),
            "unique_pair_within_unit_index_columns": list(
                self.unique_pair_within_unit_index_columns
            ),
            "unique_nonindex_authorized_unit_composite_columns": list(
                self.unique_nonindex_authorized_unit_composite_columns
            ),
            "report_path": self.report_path,
            "report_content_digest": self.report_content_digest,
            "procedure_id": self.procedure_id,
            "reported_n": self.reported_n,
            "n_evidence_kind": self.n_evidence_kind,
            "group_counts": [{"label": label, "n": count} for label, count in self.group_counts],
            "admission_template_id": self.admission_template_id,
            "selected_path_binding_kind": self.selected_path_binding_kind,
            "authority_binding_digest": self.authority_binding_digest,
            "report_evidence_spans": [
                item.to_dict() for item in sorted(self.report_evidence_spans)
            ],
        }


@dataclass(frozen=True)
class ReportCsvNormalizedMethodObservation(NormalizedMethodObservation):
    row_entry_evidence: RowEntryEvidenceProjection | None = None

    def to_dict(self) -> dict[str, Any]:
        value = super().to_dict()
        if self.row_entry_evidence is not None:
            value["row_entry_evidence"] = self.row_entry_evidence.to_dict()
        return value


def report_csv_dependence_grammar() -> dict[str, Any]:
    """Return the complete digest-bound recognition grammar and thresholds."""

    return {
        "grammar_id": "bounded-report-csv-rowwise-ttest-dependence-v1",
        "grammar_version": REPORT_CSV_DEPENDENCE_ADAPTER_VERSION,
        "profile_version": _PROFILE_VERSION,
        "check_id": DEPENDENCE_RECOGNITION_CHECK_ID,
        "candidate_id": DEPENDENCE_RECOGNITION_CANDIDATE_ID,
        "csv": {
            "encoding": "strict-utf8-without-bom",
            "dialect": "csv.excel-strict-newline-empty",
            "rows": [2, 100000],
            "columns": [1, 512],
            "field_length_max": 1048576,
            "d1_prime_candidate": ("not unit, not contract group/contrast, distinct_count <= U"),
            "d1_prime_suppressor": (
                "unique(unit,C) and not byte-identical-sorted-within-unit-index"
            ),
        },
        "accepted_test_spellings": [
            "two-sample Student t-test",
            "two-sample Student t test",
            "Welch's two-sample t-test",
            "Welch's two-sample t test",
            "scipy.stats.ttest_ind",
        ],
        "admission_templates": [
            "each of the <N> measurement rows entered the test as one observation",
            "each sampling-day measurement in the file was entered as one observation",
            "every nubbin record in <SELECTED_PATH> contributed one observation to the test",
            "<TTEST_NAME> on the <N> individual chamber readings",
        ],
        "join": {
            "adjacent_gap_max": 16,
            "headings_per_adjacent_pair_max": 1,
            "envelope_lines_max": 40,
            "result_list_gap_max": 4,
        },
        "semantic_roles": [item.to_dict() for item in DEPENDENCE_RECOGNITION_ROLE_BINDINGS],
        "counterevidence": list(REPORT_CSV_DEPENDENCE_COUNTEREVIDENCE),
        "output_ceiling": "question_only",
        "project_authored_code_execution": False,
    }


def report_csv_dependence_grammar_digest() -> str:
    return semantic_digest(report_csv_dependence_grammar())


REPORT_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))


@dataclass(frozen=True)
class ReportCsvDependenceAdapter:
    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    one_row_operand: CanonicalOperand
    multiple_rows_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...] = DEPENDENCE_RECOGNITION_ROLE_BINDINGS

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return REPORT_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return report_csv_dependence_grammar_digest()

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        try:
            return self._inspect(context)
        except (ArithmeticError, csv.Error, UnicodeError, ValueError):
            return self._abstain("unsupported", "report-csv-dependence-inspection-exception")

    def _inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        authority = _authority(context.shared_derivations, self.check_manifest)
        if authority is None:
            return self._abstain("unsupported", "verified-contract-authority-unavailable")
        if len(context.material_inputs) != 1:
            return self._abstain("unsupported", "selected-material-input-cardinality-mismatch")
        material = context.material_inputs[0]
        if material.path != authority.path or material.content_digest != authority.content_digest:
            return self._abstain("unsupported", "frozen-authority-material-mismatch")
        csv_result = _parse_csv(
            material.content,
            authority.unit_column,
            authority.group_column,
        )
        if isinstance(csv_result, str):
            state: ObservationState = (
                "not_applicable" if csv_result == "no-repeated-authorized-unit" else "unsupported"
            )
            return self._abstain(state, csv_result)
        if csv_result.unique_nonindex_columns:
            return self._abstain(
                "unsupported", "unique-nonindex-authorized-unit-composite-key-possible"
            )
        report = _selected_parsed_report(context)
        if report is None:
            return self._abstain("unsupported", "exact-selected-parsed-markdown-unavailable")
        path = selected_publication_path(
            context.scope_join_graph,
            selected_artifact_ref=context.selected_artifact_ref,
            selected_surface_ref=context.selected_surface_ref,
            relation="selected_by_publication_surface",
        )
        if len(path) != 1:
            return self._abstain("unsupported", "selected-publication-scope-unavailable")
        report_result = _inspect_report(
            report,
            selected_csv_path=authority.path,
            unit_column=authority.unit_column,
            n_csv=csv_result.n,
        )
        if isinstance(report_result, str):
            return self._abstain("unsupported", report_result)
        row_entry = RowEntryEvidenceProjection(
            material_input_path=material.path,
            material_input_content_digest=material.content_digest,
            material_file_ref=material.file_ref,
            authorized_unit_column=authority.unit_column,
            group_contrast_column=authority.group_column,
            data_row_count=csv_result.n,
            distinct_unit_count=csv_result.unit_count,
            repeated_unit_count=csv_result.repeated_unit_count,
            maximum_unit_multiplicity=csv_result.maximum_multiplicity,
            composite_key_scan_complete=True,
            composite_key_candidate_columns=csv_result.candidate_columns,
            distinct_count_excluded_columns=csv_result.distinct_excluded_columns,
            within_unit_index_columns=csv_result.within_unit_index_columns,
            unique_pair_within_unit_index_columns=(
                csv_result.unique_pair_within_unit_index_columns
            ),
            unique_nonindex_authorized_unit_composite_columns=(),
            report_path=report.path,
            report_content_digest=report.content_digest,
            procedure_id="scipy.stats.ttest_ind_two_sample",
            reported_n=report_result.reported_n,
            n_evidence_kind=report_result.n_evidence_kind,
            group_counts=report_result.group_counts,
            admission_template_id=report_result.admission_template_id,
            selected_path_binding_kind=report_result.selected_path_binding_kind,
            authority_binding_digest=authority.binding_digest,
            report_evidence_spans=report_result.spans,
        )
        receipt_projection = {
            "authority_binding_digest": authority.binding_digest,
            "csv": row_entry.to_dict(),
            "scope_join_path": [item.to_dict() for item in path],
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
        return ReportCsvNormalizedMethodObservation(
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
            evidence_plane="reported_text",
            method_target_ref=context.selected_artifact_ref,
            role_bindings=self.role_bindings,
            observed_operand=self.multiple_rows_operand,
            evidence_spans=report_result.spans,
            scope_join_path=path,
            receipts=receipts,
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            row_entry_evidence=row_entry,
        )

    def _abstain(self, state: ObservationState, reason: str) -> NormalizedMethodObservation:
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
            evidence_plane="reported_text",
            method_target_ref=None,
            role_bindings=(),
            observed_operand=None,
            evidence_spans=(),
            scope_join_path=(),
            receipts=(
                InspectionReceipt(
                    receipt_id="closed-report-csv-dependence-abstention",
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
        != DEPENDENCE_RECOGNITION_CHECK_ID
        or answer.get("extensions", {}).get("x-scientific-check-manifest-digest")
        != check_manifest.manifest_digest
        or answer.get("extensions", {}).get("x-selected-candidate-id")
        != DEPENDENCE_RECOGNITION_CANDIDATE_ID
        or assertion.get("predicate") != "verified_intended_dependence_structure"
        or assertion.get("object") != ONE_ROW_PER_AUTHORIZED_UNIT
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("semantic_role") != "intended"
        or assertion.get("extensions", {}).get("x-answer-ref")
        != {"record_type": "answer", "record_id": answer.get("answer_id")}
        or assertion.get("extensions", {}).get("x-answer-digest") != answer_digest
        or assertion.get("extensions", {}).get("x-profile-version") != _PROFILE_VERSION
        or assertion.get("extensions", {}).get("x-scientific-check-id")
        != DEPENDENCE_RECOGNITION_CHECK_ID
        or assertion.get("extensions", {}).get("x-scientific-check-manifest-digest")
        != check_manifest.manifest_digest
        or assertion.get("extensions", {}).get("x-semantic-role-authority") != authority
        or answer.get("answer_value")
        != {
            "dependence_structure": ONE_ROW_PER_AUTHORIZED_UNIT,
            "semantic_role_authority": authority,
        }
        or not isinstance(authority, Mapping)
        or set(authority) != {_UNIT_ROLE}
        or not isinstance(snapshot, Mapping)
        or set(snapshot) != {_UNIT_ROLE}
    ):
        return None
    unit = authority.get(_UNIT_ROLE)
    bound = snapshot.get(_UNIT_ROLE)
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
    ):
        return None
    path = unit.get("material_input_path")
    column = unit.get("column_name")
    group = unit.get("group_contrast_column")
    digest = bound.get("material_input_content_digest")
    if (
        not isinstance(path, str)
        or not _safe_path(path, {".csv"})
        or not isinstance(column, str)
        or _SAFE_COLUMN.fullmatch(column) is None
        or not isinstance(group, str)
        or _SAFE_COLUMN.fullmatch(group) is None
        or group == column
        or not isinstance(digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
    ):
        return None
    return _Authority(
        answer=answer,
        assertion=assertion,
        path=path,
        unit_column=column,
        group_column=group,
        content_digest=digest,
        binding_digest=semantic_digest(dict(snapshot)),
    )


def _parse_csv(content: bytes, unit_column: str, group_column: str) -> _CsvFacts | str:
    if content.startswith(b"\xef\xbb\xbf") or b"\x00" in content:
        return "unsupported-csv-encoding"
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "unsupported-csv-encoding"
    if re.search(r"\r(?!\n)", text):
        return "unsupported-csv-newline"
    old_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(1 << 20)
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    except (csv.Error, OverflowError):
        return "malformed-csv"
    finally:
        csv.field_size_limit(old_limit)
    if not rows or not rows[0] or len(rows[0]) > 512:
        return "malformed-csv-header"
    header = rows[0]
    data = rows[1:]
    if not 2 <= len(data) <= 100000:
        return "csv-row-count-outside-bound"
    if (
        any(not value or value != value.strip() or len(value) > (1 << 20) for value in header)
        or len(set(header)) != len(header)
        or any(len(row) != len(header) for row in data)
        or any(len(value) > (1 << 20) for row in data for value in row)
        or header.count(unit_column) != 1
        or header.count(group_column) != 1
    ):
        return "malformed-csv-domain"
    unit_index = header.index(unit_column)
    units = [row[unit_index] for row in data]
    if any(not value or value != value.strip() for value in units):
        return "missing-or-trimmed-authorized-unit"
    multiplicities = Counter(units)
    if len(multiplicities) < 2:
        return "fewer-than-two-authorized-units"
    if len(data) == len(multiplicities):
        return "no-repeated-authorized-unit"
    candidates: list[str] = []
    excluded: list[str] = []
    within_indexes: list[str] = []
    unique_within: list[str] = []
    unique_nonindex: list[str] = []
    unit_count = len(multiplicities)
    for column_index, column in enumerate(header):
        if column in {unit_column, group_column}:
            continue
        values = [row[column_index] for row in data]
        if len(set(values)) > unit_count:
            excluded.append(column)
            continue
        candidates.append(column)
        by_unit: dict[str, list[str]] = defaultdict(list)
        pairs: list[tuple[str, str]] = []
        for unit, value in zip(units, values, strict=True):
            by_unit[unit].append(value)
            pairs.append((unit, value))
        tuples = [tuple(sorted(by_unit[unit])) for unit in sorted(by_unit)]
        within = bool(tuples) and all(value == tuples[0] for value in tuples[1:])
        unique = len(set(pairs)) == len(pairs)
        if within:
            within_indexes.append(column)
        if within and unique:
            unique_within.append(column)
        if unique and not within:
            unique_nonindex.append(column)
    return _CsvFacts(
        header=tuple(header),
        n=len(data),
        unit_count=unit_count,
        repeated_unit_count=sum(count > 1 for count in multiplicities.values()),
        maximum_multiplicity=max(multiplicities.values()),
        candidate_columns=tuple(sorted(candidates)),
        distinct_excluded_columns=tuple(sorted(excluded)),
        within_unit_index_columns=tuple(sorted(within_indexes)),
        unique_pair_within_unit_index_columns=tuple(sorted(unique_within)),
        unique_nonindex_columns=tuple(sorted(unique_nonindex)),
    )


def _selected_parsed_report(context: FrozenInspectionContext) -> InspectionDocument | None:
    artifact = _base_record(context.base_records, context.selected_artifact_ref)
    if artifact is None or artifact.get("kind") != "report":
        return None
    path = artifact.get("path")
    if not isinstance(path, str) or not _safe_path(path, {".md", ".markdown"}):
        return None
    documents = [
        item
        for item in context.documents
        if item.path == path
        and item.media_type == "text/markdown"
        and item.parser_result_payload is not None
        and item.parser_result_ref is not None
    ]
    if len(documents) != 1:
        return None
    document = documents[0]
    identity_ref = artifact.get("asset_identity_ref")
    if not isinstance(identity_ref, Mapping):
        return None
    identity = _base_record(
        context.base_records,
        RecordRef(str(identity_ref.get("record_type")), str(identity_ref.get("record_id"))),
    )
    try:
        parser = json.loads(document.parser_result_payload or b"{}")
    except (UnicodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(identity, dict)
        or identity.get("tier") != "full_digest"
        or identity.get("identity_evidence", {}).get("digest") != document.content_digest
        or parser.get("parser_id") != "parser:markdown-inventory"
        or parser.get("parser_version") != "0.2.0"
        or parser.get("state") != "parsed"
    ):
        return None
    return document


def _base_record(records: Sequence[FrozenBaseRecord], ref: RecordRef) -> dict[str, Any] | None:
    matches = [item for item in records if item.ref == ref]
    if len(matches) != 1:
        return None
    try:
        value = json.loads(matches[0].canonical_payload)
    except (UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _safe_path(value: str, suffixes: set[str]) -> bool:
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


def _inspect_report(
    document: InspectionDocument,
    *,
    selected_csv_path: str,
    unit_column: str,
    n_csv: int,
) -> _ReportFacts | str:
    try:
        text = document.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "unsupported-report-encoding"
    if b"\x00" in document.content or re.search(r"\r(?!\n)", text):
        return "unsupported-report-encoding"
    parsed = _visible_blocks(text)
    if isinstance(parsed, str):
        return parsed
    blocks, headings, table_groups = parsed
    if not blocks:
        return "no-visible-report-text"
    suppressor = _report_suppressor(blocks, unit_column)
    if suppressor is not None:
        return suppressor
    if any("binomtest" in _TOKEN.findall(block.text) for block in blocks):
        return "procedure-outside-report-csv-rowwise-ttest-envelope"
    if any(pattern.search(block.text) for block in blocks for pattern in _COMPETING_PATTERNS):
        return "competing-procedure-present"
    test_occurrences = _test_occurrences(blocks)
    result_nodes = _result_nodes(blocks)
    if not result_nodes:
        return "inferential-result-witness-unavailable"
    if len(result_nodes) != 1:
        return "multiple-or-conflicting-results"
    result = result_nodes[0]
    classes = {item.family for item in test_occurrences if item.family != "neutral"}
    if not test_occurrences or len(classes) > 1:
        return "selected-result-test-co-reference-unavailable"
    visible_paths = {
        match.group(0) for block in blocks for match in _CSV_PATH.finditer(block.exact_text)
    }
    if visible_paths != {selected_csv_path}:
        return "selected-csv-path-ambiguous"
    admissions = _admission_nodes(blocks, headings, test_occurrences, selected_csv_path)
    if len(admissions) != 1:
        return "literal-path-bound-row-entry-admission-unavailable"
    admission, admission_n, template_id, binding_kind = admissions[0]
    n_nodes = _n_nodes(blocks, test_occurrences, table_groups)
    if admission_n is not None:
        n_nodes.insert(
            0,
            (
                _Node(
                    "N witness",
                    "admission_literal",
                    admission.block_ids,
                    admission.start_line,
                    admission.end_line,
                    admission.start_byte,
                    admission.end_byte,
                    str(admission_n),
                ),
                admission_n,
                (),
            ),
        )
    qualifying = [item for item in n_nodes if item[1] == n_csv]
    if not qualifying or any(item[1] != n_csv for item in n_nodes):
        return "report-row-count-mismatch-or-ambiguous"
    n_node, reported_n, group_counts = min(
        qualifying,
        key=lambda item: (
            0 if item[0].family == "admission_literal" else 1,
            0 if set(item[0].block_ids) & set(admission.block_ids) else 1,
            abs(item[0].start_line - admission.start_line),
            item[0].start_byte,
            item[0].end_byte,
            item[0].normalized_match,
        ),
    )
    role_rank = {"method": 0, "admission": 1, "N witness": 2, "group labels": 3, "result": 4}
    joins: list[tuple[tuple[Any, ...], list[_Node], tuple[tuple[str, int], ...]]] = []
    failures: set[str] = set()
    for method in test_occurrences:
        roles = [method, admission, n_node, result]
        selected_group_counts = group_counts
        group_source_node = n_node
        if not selected_group_counts:
            base_start = min(node.start_line for node in roles)
            base_end = max(node.end_line for node in roles)
            corroborating = [
                item
                for item in table_groups
                if item[1] == n_csv
                and base_start <= item[0].start_line
                and item[0].end_line <= base_end
            ]
            if len(corroborating) > 1:
                failures.add("multiple-corroborating-group-tables")
                continue
            if corroborating:
                group_source_node, _total, selected_group_counts = corroborating[0]
        if selected_group_counts:
            group_node = _Node(
                "group labels",
                "two_group_sum",
                group_source_node.block_ids,
                group_source_node.start_line,
                group_source_node.end_line,
                group_source_node.start_byte,
                group_source_node.end_byte,
                "|".join(label for label, _ in selected_group_counts),
            )
            joined_non_table_text = " ".join(
                block.text
                for block in blocks
                if min(node.start_line for node in roles)
                <= block.start_line
                <= max(node.end_line for node in roles)
                and block.kind != "table_cell"
            )
            tokens = set(_TOKEN.findall(joined_non_table_text))
            if any(label not in tokens for label, _ in selected_group_counts):
                failures.add("unmatched-group-labels")
                continue
            roles.append(group_node)
        ordered = sorted(
            roles,
            key=lambda node: (
                node.start_line,
                node.start_byte,
                node.end_line,
                node.end_byte,
                role_rank[node.role],
                node.family,
            ),
        )
        gaps: list[int] = []
        adjacency_failed = False
        for left, right in pairwise(ordered):
            gap = max(0, right.start_line - left.end_line - 1)
            gaps.append(gap)
            if gap > 16 or sum(left.end_line < line < right.start_line for line in headings) > 1:
                adjacency_failed = True
                break
        if adjacency_failed:
            failures.add("bounded-minimal-join-adjacency-failed")
            continue
        envelope_start = ordered[0].start_line
        envelope_end = ordered[-1].end_line
        envelope_lines = envelope_end - envelope_start + 1
        if envelope_lines > 40:
            failures.add("bounded-minimal-join-envelope-failed")
            continue
        coordinates = tuple(
            (
                node.start_line,
                node.start_byte,
                node.end_line,
                node.end_byte,
                role_rank[node.role],
                node.family,
            )
            for node in ordered
        )
        key = (
            envelope_lines,
            sum(gaps),
            max(gaps, default=0),
            coordinates,
            tuple(node.normalized_match for node in ordered),
        )
        joins.append((key, ordered, selected_group_counts))
    if not joins:
        for reason in (
            "multiple-corroborating-group-tables",
            "unmatched-group-labels",
            "bounded-minimal-join-adjacency-failed",
            "bounded-minimal-join-envelope-failed",
        ):
            if reason in failures:
                return reason
        return "bounded-minimal-join-adjacency-failed"
    _key, ordered, group_counts = min(joins, key=lambda item: item[0])
    spans = tuple(sorted({_span(document, node.start_line, node.end_line) for node in ordered}))
    return _ReportFacts(
        spans=spans,
        reported_n=reported_n,
        n_evidence_kind=n_node.family,
        group_counts=group_counts,
        admission_template_id=template_id,
        selected_path_binding_kind=binding_kind,
    )


def _visible_blocks(
    text: str,
) -> (
    tuple[
        list[_VisibleBlock], tuple[int, ...], list[tuple[_Node, int, tuple[tuple[str, int], ...]]]
    ]
    | str
):
    lines = text.splitlines()
    if any(
        re.match(r"^ {0,3}(?:```|~~~)", line)
        or line.startswith("    ")
        or line.startswith("\t")
        or re.match(r"^ {0,3}>", line)
        or re.match(r"^ {0,3}</?[A-Za-z][^>]*>", line)
        for line in lines
    ):
        return "unsupported-report-composition"
    blocks: list[_VisibleBlock] = []
    headings: list[int] = []
    table_groups: list[tuple[_Node, int, tuple[tuple[str, int], ...]]] = []
    index = 0
    block_id = 0
    while index < len(lines):
        line = lines[index]
        line_number = index + 1
        if not line.strip():
            index += 1
            continue
        heading = _ATX.match(line)
        if heading:
            visible = _visible_inline(heading.group(2))
            if visible is None:
                return "unsupported-report-composition"
            headings.append(line_number)
            blocks.append(
                _VisibleBlock(
                    block_id,
                    "heading",
                    line_number,
                    line_number,
                    _ascii_fold(visible),
                    visible,
                )
            )
            block_id += 1
            index += 1
            continue
        if "|" in line and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
            header = _table_cells(line)
            if header is None:
                return "malformed-markdown-table"
            body_start = index + 2
            body: list[list[str]] = []
            cursor = body_start
            while cursor < len(lines) and "|" in lines[cursor] and lines[cursor].strip():
                cells = _table_cells(lines[cursor])
                if cells is None or len(cells) != len(header):
                    return "malformed-markdown-table"
                body.append(cells)
                cursor += 1
            for row_line, cells in [
                (line_number, header),
                *[(value + 1, body[value - body_start]) for value in range(body_start, cursor)],
            ]:
                for cell in cells:
                    blocks.append(
                        _VisibleBlock(
                            block_id,
                            "table_cell",
                            row_line,
                            row_line,
                            _ascii_fold(cell),
                            cell,
                        )
                    )
                    block_id += 1
            witness = _table_n_witness(header, body, line_number, max(line_number, cursor))
            if witness is not None:
                table_groups.append(witness)
            index = cursor
            continue
        list_match = _LIST.match(line)
        kind = "list" if list_match else "paragraph"
        contents = [list_match.group(1) if list_match else line]
        end = index
        cursor = index + 1
        while cursor < len(lines) and lines[cursor].strip():
            if _ATX.match(lines[cursor]) or _LIST.match(lines[cursor]):
                break
            if (
                "|" in lines[cursor]
                and cursor + 1 < len(lines)
                and _is_table_separator(lines[cursor + 1])
            ):
                break
            contents.append(lines[cursor].strip())
            end = cursor
            cursor += 1
        visible = _visible_inline("\n".join(contents))
        if visible is None:
            return "unsupported-report-composition"
        blocks.append(
            _VisibleBlock(
                block_id,
                kind,
                line_number,
                end + 1,
                _ascii_fold(visible),
                visible,
            )
        )
        block_id += 1
        index = cursor
    return blocks, tuple(headings), table_groups


def _visible_inline(value: str) -> str | None:
    if "``" in value or value.count("`") % 2 or re.search(r"<[/!?]?[A-Za-z][^>]*>", value):
        return None
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    if "](" in value:
        return None
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", value)
    value = re.sub(r"(?<![A-Za-z0-9])_([^_]+)_(?![A-Za-z0-9])", r"\1", value)
    if any(character.isspace() and character not in " \t\r\n\f\v" for character in value):
        return None
    return _ASCII_SPACE.sub(" ", value).strip(" ")


def _ascii_fold(value: str) -> str:
    return value.translate(
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
    )


def _is_table_separator(value: str) -> bool:
    cells = _table_cells(value)
    return (
        cells is not None
        and bool(cells)
        and all(_TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in cells)
    )


def _table_cells(value: str) -> list[str] | None:
    stripped = value.strip()
    if not stripped or "\\|" in stripped:
        return None
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    raw = stripped.split("|")
    cells = [_visible_inline(cell.strip()) for cell in raw]
    return None if any(cell is None for cell in cells) else [str(cell) for cell in cells]


def _table_n_witness(
    header: list[str], body: list[list[str]], start_line: int, end_line: int
) -> tuple[_Node, int, tuple[tuple[str, int], ...]] | None:
    folded_header = [_ascii_fold(value) for value in header]
    accepted = [
        index
        for index, value in enumerate(folded_header)
        if value in {"n", "rows", "measurements", "measurement rows"}
    ]
    if len(accepted) != 1 or len(body) != 2 or not header or len(header) < 2:
        return None
    n_index = accepted[0]
    labels = [_ascii_fold(row[0]) for row in body]
    counts = [row[n_index] for row in body]
    if (
        any(not label for label in labels)
        or len(set(labels)) != 2
        or any(_UNSIGNED_N.fullmatch(value) is None for value in counts)
    ):
        return None
    group_counts = tuple((label, int(count)) for label, count in zip(labels, counts, strict=True))
    total = sum(count for _, count in group_counts)
    node = _Node(
        "N witness",
        "two_group_sum",
        (),
        start_line,
        end_line,
        0,
        0,
        f"{group_counts[0][1]}+{group_counts[1][1]}",
    )
    return node, total, group_counts


def _test_occurrences(blocks: Sequence[_VisibleBlock]) -> list[_Node]:
    values: list[_Node] = []
    for block in blocks:
        for family, pattern in _TEST_PATTERNS:
            for match in pattern.finditer(block.text):
                values.append(
                    _Node(
                        "method",
                        family,
                        (block.block_id,),
                        block.start_line,
                        block.end_line,
                        match.start(),
                        match.end(),
                        match.group(0),
                    )
                )
    return values


def _result_nodes(blocks: Sequence[_VisibleBlock]) -> list[_Node]:
    t_pattern = re.compile(
        _NUMBER_BOUNDARY_LEFT
        + rf"(?:t\(({_DEC})\)|welch t|t)\s*=\s*({_DEC})"
        + _NUMBER_BOUNDARY_RIGHT
    )
    p_pattern = re.compile(
        _NUMBER_BOUNDARY_LEFT + rf"p\s*(<=|>=|<|=|>)\s*({_SCI}|{_DEC})" + _NUMBER_BOUNDARY_RIGHT
    )
    facts: list[tuple[_Node, tuple[str, str, str, str]]] = []
    for index, block in enumerate(blocks):
        candidates: list[tuple[_VisibleBlock, ...]] = [(block,)]
        if block.kind == "list" and index + 1 < len(blocks):
            other = blocks[index + 1]
            if other.kind == "list" and other.start_line - block.end_line - 1 <= 4:
                candidates.append((block, other))
        for chosen in candidates:
            joined = " ".join(item.text for item in chosen)
            t_matches = list(t_pattern.finditer(joined))
            p_matches = list(p_pattern.finditer(joined))
            if not t_matches or not p_matches:
                continue
            if any(
                not _finite_decimal(match.group(2), nonnegative=False)
                or (
                    match.group(1) is not None
                    and not _finite_decimal(match.group(1), nonnegative=True)
                )
                for match in t_matches
            ) or any(not _finite_decimal(match.group(2), nonnegative=True) for match in p_matches):
                continue
            t_facts = {(match.group(1) or "", match.group(2)) for match in t_matches}
            p_facts = {(match.group(1), match.group(2)) for match in p_matches}
            if len(t_facts) != 1 or len(p_facts) != 1:
                continue
            df_value, t_value = next(iter(t_facts))
            p_comparator, p_value = next(iter(p_facts))
            fact = (df_value, t_value, p_comparator, p_value)
            facts.append(
                (
                    _Node(
                        "result",
                        "inferential_t_p",
                        tuple(item.block_id for item in chosen),
                        chosen[0].start_line,
                        chosen[-1].end_line,
                        min(
                            *(match.start() for match in t_matches),
                            *(match.start() for match in p_matches),
                        ),
                        max(
                            *(match.end() for match in t_matches),
                            *(match.end() for match in p_matches),
                        ),
                        "|".join(fact),
                    ),
                    fact,
                )
            )
    unique: dict[tuple[int, ...], tuple[_Node, tuple[str, str, str, str]]] = {}
    for item in facts:
        unique[item[0].block_ids] = item
    values = list(unique.values())
    if not values:
        return []
    if len({fact for _, fact in values}) != 1:
        return [node for node, _ in values]
    return [
        min((node for node, _ in values), key=lambda node: (len(node.block_ids), node.start_line))
    ]


def _finite_decimal(value: str, *, nonnegative: bool) -> bool:
    if len(value) > 64:
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite() and (not nonnegative or parsed >= 0)


def _admission_nodes(
    blocks: Sequence[_VisibleBlock],
    headings: Sequence[int],
    test_occurrences: Sequence[_Node],
    selected_path: str,
) -> list[tuple[_Node, int | None, str, str]]:
    escaped = re.escape(_ascii_fold(selected_path))
    anchors: list[tuple[_VisibleBlock, str, re.Match[str]]] = []
    for block in blocks:
        for binding, pattern in (
            (
                "source_file_anchor",
                re.compile(rf"source file: (?P<path>{escaped}){_PATH_BOUNDARY_RIGHT}"),
            ),
            (
                "the_file_records_anchor",
                re.compile(rf"the file (?P<path>{escaped}) records{_PATH_BOUNDARY_RIGHT}"),
            ),
        ):
            anchors.extend(
                (block, binding, match)
                for match in pattern.finditer(block.text)
                if block.exact_text[match.start("path") : match.end("path")] == selected_path
            )
    values: list[tuple[_Node, int | None, str, str]] = []
    forms: tuple[tuple[str, re.Pattern[str]], ...] = (
        (
            "numbered_measurement_rows",
            re.compile(
                r"each of the ([1-9][0-9]*) measurement rows entered the test as one observation"
            ),
        ),
        (
            "sampling_day_file_rows",
            re.compile(r"each sampling-day measurement in the file was entered as one observation"),
        ),
    )
    for template, pattern in forms:
        for block in blocks:
            for match in pattern.finditer(block.text):
                if len(anchors) != 1:
                    continue
                anchor_block, binding, _ = anchors[0]
                start = min(anchor_block.start_line, block.start_line)
                end = max(anchor_block.end_line, block.end_line)
                if (
                    max(
                        0,
                        max(anchor_block.start_line, block.start_line)
                        - min(anchor_block.end_line, block.end_line)
                        - 1,
                    )
                    > 16
                    or sum(start < line < end for line in headings) > 1
                ):
                    continue
                values.append(
                    (
                        _Node(
                            "admission",
                            template,
                            (anchor_block.block_id, block.block_id),
                            start,
                            end,
                            match.start(),
                            match.end(),
                            match.group(0),
                        ),
                        int(match.group(1)) if match.lastindex else None,
                        template,
                        binding,
                    )
                )
    direct = re.compile(
        rf"every nubbin record in (?P<path>{escaped}) contributed one observation to the test"
    )
    for block in blocks:
        for match in direct.finditer(block.text):
            if block.exact_text[match.start("path") : match.end("path")] != selected_path:
                continue
            values.append(
                (
                    _Node(
                        "admission",
                        "selected_path_nubbin_rows",
                        (block.block_id,),
                        block.start_line,
                        block.end_line,
                        match.start(),
                        match.end(),
                        match.group(0),
                    ),
                    None,
                    "selected_path_nubbin_rows",
                    "direct_admission_path",
                )
            )
    chamber = re.compile(
        r"(?:two-sample student t-test|two-sample student t test|welch's two-sample t-test|welch's two-sample t test|scipy\.stats\.ttest_ind) on the ([1-9][0-9]*) individual chamber readings"
    )
    for block in blocks:
        for match in chamber.finditer(block.text):
            if len(anchors) != 1 or not any(
                test.block_ids[0] == block.block_id for test in test_occurrences
            ):
                continue
            anchor_block, binding, _ = anchors[0]
            start = min(anchor_block.start_line, block.start_line)
            end = max(anchor_block.end_line, block.end_line)
            if (
                max(
                    0,
                    max(anchor_block.start_line, block.start_line)
                    - min(anchor_block.end_line, block.end_line)
                    - 1,
                )
                > 16
                or sum(start < line < end for line in headings) > 1
            ):
                continue
            values.append(
                (
                    _Node(
                        "admission",
                        "individual_chamber_readings",
                        (anchor_block.block_id, block.block_id),
                        start,
                        end,
                        match.start(),
                        match.end(),
                        match.group(0),
                    ),
                    int(match.group(1)),
                    "individual_chamber_readings",
                    binding,
                )
            )
    return values


def _n_nodes(
    blocks: Sequence[_VisibleBlock],
    test_occurrences: Sequence[_Node],
    table_groups: Sequence[tuple[_Node, int, tuple[tuple[str, int], ...]]],
) -> list[tuple[_Node, int, tuple[tuple[str, int], ...]]]:
    values = list(table_groups)
    nearby = re.compile(r"measurement rows analys(?:ed|zed): ([1-9][0-9]*)")
    measurement = re.compile(
        r"(?:two-sample student t-test|two-sample student t test|welch's two-sample t-test|welch's two-sample t test|scipy\.stats\.ttest_ind) on the ([1-9][0-9]*) measurement rows"
    )
    for block in blocks:
        for family, pattern in (
            ("nearby_total_literal", nearby),
            ("ttest_measurement_rows_literal", measurement),
        ):
            for match in pattern.finditer(block.text):
                if family.startswith("ttest") and not any(
                    test.block_ids[0] == block.block_id for test in test_occurrences
                ):
                    continue
                values.append(
                    (
                        _Node(
                            "N witness",
                            family,
                            (block.block_id,),
                            block.start_line,
                            block.end_line,
                            match.start(),
                            match.end(),
                            match.group(0),
                        ),
                        int(match.group(1)),
                        (),
                    )
                )
    return values


def _report_suppressor(blocks: Sequence[_VisibleBlock], unit_column: str) -> str | None:
    stem = _authorized_stem(unit_column)
    for block in blocks:
        tokens = _TOKEN.findall(block.text)
        exact_sequences = (
            ("pseudo", "bulk"),
            ("within", "subject"),
            ("within", "unit"),
            ("within", "donor"),
            ("within", "patient"),
            ("within", "plot"),
            ("within", "colony"),
            ("blocked", "test"),
            ("split", "plot"),
            ("sub", "plot"),
            ("whole", "plot"),
            ("random", "intercept"),
            ("random", "slope"),
            ("cluster", "robust"),
            ("correlation", "structure"),
            ("exchangeable", "correlation"),
            ("autoregressive", "correlation"),
            ("subject", "level", "covariance"),
            ("sensitivity", "analysis"),
            ("sensitivity", "only"),
            ("secondary", "analysis"),
            ("descriptive", "only"),
            ("illustrative", "only"),
            ("not", "the", "primary", "analysis"),
            ("approved", "deviation"),
            ("protocol", "amendment"),
            ("amended", "protocol"),
            ("revised", "protocol"),
            ("revised", "analysis", "plan"),
            ("revised", "sap"),
            ("randomized", "at"),
            ("randomised", "at"),
        )
        if any(_has_token_sequence(tokens, sequence) for sequence in exact_sequences):
            return "report-wide-scientific-suppressor-present"
        if any(
            token == "pseudobulk"
            or token == "paired"
            or token == "nested"
            or (token == "ttest" and index + 1 < len(tokens) and tokens[index + 1] == "rel")
            or token in {"lmer", "glmer", "exploratory"}
            for index, token in enumerate(tokens)
        ):
            return "report-wide-scientific-suppressor-present"
        if any(
            token == "technical"
            and index + 1 < len(tokens)
            and tokens[index + 1].startswith("replicate")
            for index, token in enumerate(tokens)
        ):
            return "report-wide-scientific-suppressor-present"
        if any(
            token == "random" and index + 1 < len(tokens) and tokens[index + 1].startswith("effect")
            for index, token in enumerate(tokens)
        ):
            return "report-wide-scientific-suppressor-present"
        if any(
            token == "matched" and index + 1 < len(tokens) and tokens[index + 1].startswith("pair")
            for index, token in enumerate(tokens)
        ):
            return "report-wide-scientific-suppressor-present"
        if any(token.startswith("aggregat") for token in tokens):
            return "report-wide-scientific-suppressor-present"
        unit_tokens = stem | _FIXED_UNIT_NOUNS
        operations = {"mean", "median", "sum"}
        for index, token in enumerate(tokens):
            if token in unit_tokens:
                window = tokens[max(0, index - 4) : index + 5]
                if any(
                    value in operations
                    or value.startswith(
                        (
                            "aggregat",
                            "collapse",
                            "pool",
                            "bootstrap",
                            "permut",
                            "resampl",
                            "shuffle",
                        )
                    )
                    for value in window
                ):
                    return "report-wide-scientific-suppressor-present"
        if any(
            token in {"mixed", "repeated", "correlated"}
            and index + 1 < len(tokens)
            and (
                (token == "mixed" and tokens[index + 1].startswith("effect"))
                or (token == "repeated" and tokens[index + 1].startswith("measure"))
                or (token == "correlated" and tokens[index + 1].startswith("error"))
            )
            for index, token in enumerate(tokens)
        ):
            return "report-wide-scientific-suppressor-present"
        if any(
            token == "gee"
            or (
                token == "generalized"
                and index + 2 < len(tokens)
                and tokens[index + 1] == "estimating"
                and tokens[index + 2].startswith("equation")
            )
            or (
                token == "clustered"
                and index + 2 < len(tokens)
                and tokens[index + 1] == "standard"
                and tokens[index + 2].startswith("error")
            )
            for index, token in enumerate(tokens)
        ):
            return "report-wide-scientific-suppressor-present"
        for index, token in enumerate(tokens):
            if token == "sandwich" and any(
                value in {"variance", "se", "estimator"}
                or (
                    value == "standard"
                    and offset + 1 < len(tokens)
                    and tokens[offset + 1].startswith("error")
                )
                for offset, value in enumerate(tokens)
                if abs(offset - index) <= 4
            ):
                return "report-wide-scientific-suppressor-present"
    return None


def _has_token_sequence(tokens: Sequence[str], sequence: Sequence[str]) -> bool:
    width = len(sequence)
    return any(
        tuple(tokens[index : index + width]) == tuple(sequence) for index in range(len(tokens))
    )


def _authorized_stem(column_name: str) -> set[str]:
    tokens = [value for value in re.split(r"[_.-]+", _ascii_fold(column_name)) if value]
    if tokens and tokens[-1] in _FINAL_STEM_TOKENS:
        tokens.pop()
    return set(tokens)


def _span(document: InspectionDocument, start_line: int, end_line: int) -> EvidenceSpan:
    lines = document.content.decode("utf-8").splitlines()
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.content_digest,
        start_line=start_line,
        end_line=end_line,
        start_column=1,
        end_column=max(1, len(lines[end_line - 1])),
        parser_result_ref=document.parser_result_ref or RecordRef("parser_result", "unavailable"),
    )


__all__ = [
    "DEPENDENCE_RECOGNITION_CHECK_VERSION",
    "DEPENDENCE_RECOGNITION_SEMANTIC_ROLES",
    "MULTIPLE_ROWS_PER_AUTHORIZED_UNIT",
    "ONE_ROW_PER_AUTHORIZED_UNIT",
    "REPORT_CSV_DEPENDENCE_ADAPTER_ID",
    "REPORT_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST",
    "REPORT_CSV_DEPENDENCE_ADAPTER_VERSION",
    "REPORT_CSV_DEPENDENCE_COUNTEREVIDENCE",
    "ReportCsvDependenceAdapter",
    "report_csv_dependence_grammar_digest",
]
