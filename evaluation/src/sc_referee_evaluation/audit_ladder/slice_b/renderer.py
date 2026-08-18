"""Closed ASCII renderer for the development-only Slice-B component report.

This module deliberately starts below the manifest, CSV, observation-verifier,
scope-evidence, and composition boundaries.  It accepts only the closed records
defined by the Slice-B memo.  Builders V and C remain responsible for producing
those records from independently verified frozen inputs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Final, cast


class SliceBRendererNoReportError(ValueError):
    """Typed fail-closed result: the renderer produced no report bytes."""


class SliceBPrimaryRefusalReasonV1(StrEnum):
    """Ordered primary refusal vocabulary from binding memo Section 12.3."""

    MANIFEST_INPUT_ABSENT = "slice-b-manifest-input-absent"
    MANIFEST_DIGEST_INVALID = "slice-b-manifest-digest-invalid"
    MANIFEST_BIJECTION_INVALID = "slice-b-manifest-bijection-invalid"
    SELECTED_FILE_NOT_MATERIAL = "slice-b-selected-file-not-material"
    SELECTED_FILE_IDENTITY_INVALID = "slice-b-selected-file-identity-invalid"
    CSV_BYTE_BUDGET_EXCEEDED = "slice-b-csv-byte-budget-exceeded"
    CSV_BYTE_LANGUAGE_UNSUPPORTED = "slice-b-csv-byte-language-unsupported"
    CSV_HEADER_INVALID = "slice-b-csv-header-invalid"
    CSV_SHAPE_INVALID = "slice-b-csv-shape-invalid"
    CSV_ROW_BUDGET_EXCEEDED = "slice-b-csv-row-budget-exceeded"
    COLUMN_ROLE_INVALID = "slice-b-column-role-invalid"
    OBSERVATION_REDERIVATION_MISMATCH = "slice-b-observation-rederivation-mismatch"


PRIMARY_REFUSAL_PRECEDENCE: Final = tuple(SliceBPrimaryRefusalReasonV1)

_PRIMARY_COVERAGE_LINES: Final[dict[SliceBPrimaryRefusalReasonV1, bytes]] = {
    SliceBPrimaryRefusalReasonV1.MANIFEST_INPUT_ABSENT: b"- Evidence grade: COVERAGE LIMIT (slice-b-manifest-input-absent). No frozen file-manifest input was available for this audit scope.",
    SliceBPrimaryRefusalReasonV1.MANIFEST_DIGEST_INVALID: b"- Evidence grade: COVERAGE LIMIT (slice-b-manifest-digest-invalid). The frozen file-manifest bytes did not match one canonical declared digest.",
    SliceBPrimaryRefusalReasonV1.MANIFEST_BIJECTION_INVALID: b"- Evidence grade: COVERAGE LIMIT (slice-b-manifest-bijection-invalid). The frozen manifest and snapshot file records did not form the required exact bijection.",
    SliceBPrimaryRefusalReasonV1.SELECTED_FILE_NOT_MATERIAL: b"- Evidence grade: COVERAGE LIMIT (slice-b-selected-file-not-material). The selected CSV did not have exactly one intake-selected frozen regular-file material input.",
    SliceBPrimaryRefusalReasonV1.SELECTED_FILE_IDENTITY_INVALID: b"- Evidence grade: COVERAGE LIMIT (slice-b-selected-file-identity-invalid). The selected CSV material input did not have one matching full-digest snapshot identity.",
    SliceBPrimaryRefusalReasonV1.CSV_BYTE_BUDGET_EXCEEDED: b"- Evidence grade: COVERAGE LIMIT (slice-b-csv-byte-budget-exceeded). The selected CSV exceeded the accepted byte budget.",
    SliceBPrimaryRefusalReasonV1.CSV_BYTE_LANGUAGE_UNSUPPORTED: b"- Evidence grade: COVERAGE LIMIT (slice-b-csv-byte-language-unsupported). The selected CSV used bytes or CSV forms outside the accepted byte language.",
    SliceBPrimaryRefusalReasonV1.CSV_HEADER_INVALID: b"- Evidence grade: COVERAGE LIMIT (slice-b-csv-header-invalid). The selected CSV header did not meet the accepted width and uniqueness rules.",
    SliceBPrimaryRefusalReasonV1.CSV_SHAPE_INVALID: b"- Evidence grade: COVERAGE LIMIT (slice-b-csv-shape-invalid). The selected CSV rows did not have the accepted nonempty rectangular shape.",
    SliceBPrimaryRefusalReasonV1.CSV_ROW_BUDGET_EXCEEDED: b"- Evidence grade: COVERAGE LIMIT (slice-b-csv-row-budget-exceeded). The selected CSV exceeded the accepted data-row budget.",
    SliceBPrimaryRefusalReasonV1.COLUMN_ROLE_INVALID: b"- Evidence grade: COVERAGE LIMIT (slice-b-column-role-invalid). The selected column indices were not distinct in-range roles for the verified table.",
    SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH: b"- Evidence grade: COVERAGE LIMIT (slice-b-observation-rederivation-mismatch). The independently re-derived observations did not match the primary verifier records.",
}

_PERMANENT_COVERAGE_LINE: Final = b"- Evidence grade: COVERAGE LIMIT. Slice B does not assess repository-wide inventory completeness or whether the selected audit-scope CSV is used by an analysis."
_SECONDARY_SCOPE_LINE: Final = b"- Evidence grade: COVERAGE LIMIT (slice-b-question-scope-unresolved). The selected CSV lacked independently verified digest-bound explicit material-input selection evidence, so no material question was emitted."
_HASH_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z", flags=re.ASCII)


@dataclass(frozen=True, slots=True)
class CsvTableShapeObservationV1:
    observation_version: str
    observation_type: str
    verifier_id: str
    snapshot_digest: str
    file_record_ref_digest: str
    content_digest: str
    selected_file_ordinal: int
    review_scope_selection_evidence_digest: str
    data_row_count: int
    column_count: int
    observation_id: str
    finding_eligible: bool

    def to_dict(self) -> dict[str, object]:
        """Return the exact canonical observation mapping."""

        return {
            "observation_version": self.observation_version,
            "observation_type": self.observation_type,
            "verifier_id": self.verifier_id,
            "snapshot_digest": self.snapshot_digest,
            "file_record_ref_digest": self.file_record_ref_digest,
            "content_digest": self.content_digest,
            "selected_file_ordinal": self.selected_file_ordinal,
            "review_scope_selection_evidence_digest": (self.review_scope_selection_evidence_digest),
            "data_row_count": self.data_row_count,
            "column_count": self.column_count,
            "observation_id": self.observation_id,
            "finding_eligible": self.finding_eligible,
        }


@dataclass(frozen=True, slots=True)
class CsvSelectedCardinalitiesObservationV1:
    observation_version: str
    observation_type: str
    verifier_id: str
    snapshot_digest: str
    file_record_ref_digest: str
    content_digest: str
    selected_file_ordinal: int
    review_scope_selection_evidence_digest: str
    candidate_unit_column_index: int
    comparison_column_index: int
    candidate_unit_distinct_count: int
    comparison_distinct_count: int
    observation_id: str
    finding_eligible: bool

    def to_dict(self) -> dict[str, object]:
        """Return the exact canonical observation mapping."""

        return {
            "observation_version": self.observation_version,
            "observation_type": self.observation_type,
            "verifier_id": self.verifier_id,
            "snapshot_digest": self.snapshot_digest,
            "file_record_ref_digest": self.file_record_ref_digest,
            "content_digest": self.content_digest,
            "selected_file_ordinal": self.selected_file_ordinal,
            "review_scope_selection_evidence_digest": (self.review_scope_selection_evidence_digest),
            "candidate_unit_column_index": self.candidate_unit_column_index,
            "comparison_column_index": self.comparison_column_index,
            "candidate_unit_distinct_count": self.candidate_unit_distinct_count,
            "comparison_distinct_count": self.comparison_distinct_count,
            "observation_id": self.observation_id,
            "finding_eligible": self.finding_eligible,
        }


@dataclass(frozen=True, slots=True)
class CsvComparisonGroupSizesObservationV1:
    observation_version: str
    observation_type: str
    verifier_id: str
    snapshot_digest: str
    file_record_ref_digest: str
    content_digest: str
    selected_file_ordinal: int
    review_scope_selection_evidence_digest: str
    comparison_column_index: int
    sorted_group_sizes: tuple[int, ...]
    observation_id: str
    finding_eligible: bool

    def to_dict(self) -> dict[str, object]:
        """Return the exact canonical observation mapping."""

        return {
            "observation_version": self.observation_version,
            "observation_type": self.observation_type,
            "verifier_id": self.verifier_id,
            "snapshot_digest": self.snapshot_digest,
            "file_record_ref_digest": self.file_record_ref_digest,
            "content_digest": self.content_digest,
            "selected_file_ordinal": self.selected_file_ordinal,
            "review_scope_selection_evidence_digest": (self.review_scope_selection_evidence_digest),
            "comparison_column_index": self.comparison_column_index,
            "sorted_group_sizes": list(self.sorted_group_sizes),
            "observation_id": self.observation_id,
            "finding_eligible": self.finding_eligible,
        }


@dataclass(frozen=True, slots=True)
class CsvUnitComparisonIncidenceObservationV1:
    observation_version: str
    observation_type: str
    verifier_id: str
    snapshot_digest: str
    file_record_ref_digest: str
    content_digest: str
    selected_file_ordinal: int
    review_scope_selection_evidence_digest: str
    candidate_unit_column_index: int
    comparison_column_index: int
    repeated_candidate_value_count: int
    cross_comparison_candidate_value_count: int
    comparison_values_per_candidate_histogram: tuple[tuple[int, int], ...]
    observation_id: str
    finding_eligible: bool

    def to_dict(self) -> dict[str, object]:
        """Return the exact canonical observation mapping."""

        return {
            "observation_version": self.observation_version,
            "observation_type": self.observation_type,
            "verifier_id": self.verifier_id,
            "snapshot_digest": self.snapshot_digest,
            "file_record_ref_digest": self.file_record_ref_digest,
            "content_digest": self.content_digest,
            "selected_file_ordinal": self.selected_file_ordinal,
            "review_scope_selection_evidence_digest": (self.review_scope_selection_evidence_digest),
            "candidate_unit_column_index": self.candidate_unit_column_index,
            "comparison_column_index": self.comparison_column_index,
            "repeated_candidate_value_count": self.repeated_candidate_value_count,
            "cross_comparison_candidate_value_count": (self.cross_comparison_candidate_value_count),
            "comparison_values_per_candidate_histogram": [
                [comparison_count, candidate_count]
                for comparison_count, candidate_count in (
                    self.comparison_values_per_candidate_histogram
                )
            ],
            "observation_id": self.observation_id,
            "finding_eligible": self.finding_eligible,
        }


@dataclass(frozen=True, slots=True)
class SliceBQuestionRenderIRV1:
    ir_schema: str
    grade: str
    rule_id: str
    render_template_id: str
    basis_observation_ids: tuple[str, str, str, str]
    review_scope_selection_evidence_digest: str
    answer_domain_id: str
    unresolved_consequence_id: str
    finding_eligible: bool
    question_id: str


SliceBObservationV1 = (
    CsvTableShapeObservationV1
    | CsvSelectedCardinalitiesObservationV1
    | CsvComparisonGroupSizesObservationV1
    | CsvUnitComparisonIncidenceObservationV1
)
SliceBObservationSetV1 = tuple[
    CsvTableShapeObservationV1,
    CsvSelectedCardinalitiesObservationV1,
    CsvComparisonGroupSizesObservationV1,
    CsvUnitComparisonIncidenceObservationV1,
]
SliceBDigestRecordV1 = SliceBObservationV1 | SliceBQuestionRenderIRV1


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _record_digest(value: SliceBDigestRecordV1, identity_field: str) -> str:
    projection = asdict(value)  # exact concrete dataclass types are checked first
    del projection[identity_field]
    return _canonical_digest(projection)


def _require_hash(value: object, field: str) -> str:
    if type(value) is not str or _HASH_PATTERN.fullmatch(value) is None:
        raise SliceBRendererNoReportError(f"invalid closed hash slot: {field}")
    return value


def _require_uint(value: object, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise SliceBRendererNoReportError(f"invalid closed integer slot: {field}")
    return value


def _uint_bytes(value: int) -> bytes:
    return str(value).encode("ascii")


def _hash_bytes(value: str) -> bytes:
    return value.encode("ascii")


def _vector_bytes(values: tuple[int, ...]) -> bytes:
    return b"[" + b",".join(_uint_bytes(value) for value in values) + b"]"


def _histogram_bytes(values: tuple[tuple[int, int], ...]) -> bytes:
    return (
        b"["
        + b",".join(
            b"[" + _uint_bytes(first) + b"," + _uint_bytes(second) + b"]"
            for first, second in values
        )
        + b"]"
    )


def _validate_common(
    value: object,
    *,
    expected_type: type[object],
    observation_type: str,
    verifier_id: str,
) -> None:
    if type(value) is not expected_type:
        raise SliceBRendererNoReportError("observation concrete type or order mismatch")
    if (
        value.observation_version != "slice-b-observation-v1"  # type: ignore[attr-defined]
        or value.observation_type != observation_type  # type: ignore[attr-defined]
        or value.verifier_id != verifier_id  # type: ignore[attr-defined]
        or type(value.selected_file_ordinal) is not int  # type: ignore[attr-defined]
        or value.selected_file_ordinal != 1  # type: ignore[attr-defined]
        or value.finding_eligible is not False  # type: ignore[attr-defined]
    ):
        raise SliceBRendererNoReportError("observation closed literal mismatch")
    _require_hash(value.snapshot_digest, "snapshot_digest")  # type: ignore[attr-defined]
    _require_hash(value.file_record_ref_digest, "file_record_ref_digest")  # type: ignore[attr-defined]
    _require_hash(value.content_digest, "content_digest")  # type: ignore[attr-defined]
    scope_digest = value.review_scope_selection_evidence_digest  # type: ignore[attr-defined]
    if scope_digest != "unresolved":
        _require_hash(scope_digest, "review_scope_selection_evidence_digest")
    _require_hash(value.observation_id, "observation_id")  # type: ignore[attr-defined]
    if value.observation_id != _record_digest(  # type: ignore[attr-defined]
        cast(SliceBDigestRecordV1, value), "observation_id"
    ):
        raise SliceBRendererNoReportError("observation identity mismatch")


def _validate_observations(observations: object) -> SliceBObservationSetV1:
    if type(observations) is not tuple or len(observations) != 4:
        raise SliceBRendererNoReportError("exactly four ordered observations required")
    shape, cardinality, group_sizes, incidence = observations
    _validate_common(
        shape,
        expected_type=CsvTableShapeObservationV1,
        observation_type="csv-table-shape-v1",
        verifier_id="slice-b-csv-shape-verifier-v1",
    )
    _validate_common(
        cardinality,
        expected_type=CsvSelectedCardinalitiesObservationV1,
        observation_type="csv-selected-cardinalities-v1",
        verifier_id="slice-b-csv-cardinality-verifier-v1",
    )
    _validate_common(
        group_sizes,
        expected_type=CsvComparisonGroupSizesObservationV1,
        observation_type="csv-comparison-group-sizes-v1",
        verifier_id="slice-b-csv-group-size-verifier-v1",
    )
    _validate_common(
        incidence,
        expected_type=CsvUnitComparisonIncidenceObservationV1,
        observation_type="csv-unit-comparison-incidence-v1",
        verifier_id="slice-b-csv-incidence-verifier-v1",
    )

    typed = (shape, cardinality, group_sizes, incidence)
    common = {
        (
            item.snapshot_digest,
            item.file_record_ref_digest,
            item.content_digest,
            item.review_scope_selection_evidence_digest,
        )
        for item in typed
    }
    if len(common) != 1:
        raise SliceBRendererNoReportError("observation provenance mismatch")

    rows = _require_uint(shape.data_row_count, "data_row_count", 1, 100_000)
    columns = _require_uint(shape.column_count, "column_count", 2, 64)
    candidate_index = _require_uint(
        cardinality.candidate_unit_column_index,
        "candidate_unit_column_index",
        0,
        63,
    )
    comparison_index = _require_uint(
        cardinality.comparison_column_index,
        "comparison_column_index",
        0,
        63,
    )
    if (
        candidate_index == comparison_index
        or candidate_index >= columns
        or comparison_index >= columns
    ):
        raise SliceBRendererNoReportError("column role mismatch")
    candidate_distinct = _require_uint(
        cardinality.candidate_unit_distinct_count,
        "candidate_unit_distinct_count",
        1,
        rows,
    )
    comparison_distinct = _require_uint(
        cardinality.comparison_distinct_count,
        "comparison_distinct_count",
        1,
        rows,
    )
    if group_sizes.comparison_column_index != comparison_index:
        raise SliceBRendererNoReportError("group-size column mismatch")
    sizes = group_sizes.sorted_group_sizes
    if type(sizes) is not tuple or not 1 <= len(sizes) <= 100_000:
        raise SliceBRendererNoReportError("group-size vector bounds")
    for value in sizes:
        _require_uint(value, "sorted_group_size", 1, rows)
    if tuple(sorted(sizes)) != sizes or len(sizes) != comparison_distinct or sum(sizes) != rows:
        raise SliceBRendererNoReportError("group-size vector algebra mismatch")
    if (
        incidence.candidate_unit_column_index != candidate_index
        or incidence.comparison_column_index != comparison_index
    ):
        raise SliceBRendererNoReportError("incidence column mismatch")
    repeated = _require_uint(
        incidence.repeated_candidate_value_count,
        "repeated_candidate_value_count",
        0,
        candidate_distinct,
    )
    cross = _require_uint(
        incidence.cross_comparison_candidate_value_count,
        "cross_comparison_candidate_value_count",
        0,
        candidate_distinct,
    )
    histogram = incidence.comparison_values_per_candidate_histogram
    if type(histogram) is not tuple or not 1 <= len(histogram) <= 100_000:
        raise SliceBRendererNoReportError("histogram bounds")
    previous = 0
    candidate_total = 0
    derived_cross = 0
    for pair in histogram:
        if type(pair) is not tuple or len(pair) != 2:
            raise SliceBRendererNoReportError("histogram pair type")
        first = _require_uint(pair[0], "histogram comparison count", 1, comparison_distinct)
        second = _require_uint(pair[1], "histogram candidate count", 1, candidate_distinct)
        if first <= previous:
            raise SliceBRendererNoReportError("histogram order")
        previous = first
        candidate_total += second
        if first > 1:
            derived_cross += second
    if candidate_total != candidate_distinct or derived_cross != cross:
        raise SliceBRendererNoReportError("histogram algebra mismatch")
    if repeated > rows - candidate_distinct:
        # Each repeated value needs at least one row beyond its first occurrence.
        raise SliceBRendererNoReportError("repeated-count algebra mismatch")
    return typed


def _question_predicate(observations: SliceBObservationSetV1) -> bool:
    shape, cardinality, _, incidence = observations
    return (
        shape.data_row_count >= 2
        and cardinality.candidate_unit_distinct_count < shape.data_row_count
        and cardinality.comparison_distinct_count >= 2
        and incidence.repeated_candidate_value_count >= 1
        and incidence.cross_comparison_candidate_value_count >= 1
    )


def _validate_question(
    question: object,
    observations: SliceBObservationSetV1,
    scope_digest: str,
) -> SliceBQuestionRenderIRV1:
    if type(question) is not SliceBQuestionRenderIRV1:
        raise SliceBRendererNoReportError("question concrete type mismatch")
    if (
        question.ir_schema != "slice-b-question-render-ir-v1"
        or question.grade != "MATERIAL QUESTION"
        or question.rule_id != "csv-repeated-candidate-across-comparison-question-v1"
        or question.render_template_id != "slice-b-csv-question-block-v3"
        or question.answer_domain_id
        != "slice-b-used-unit-conclusion-comparison-dependence-answer-tree-v1"
        or question.unresolved_consequence_id
        != "slice-b-scientific-conclusion-support-unresolved-v1"
        or question.finding_eligible is not False
    ):
        raise SliceBRendererNoReportError("question closed literal mismatch")
    expected_basis = tuple(item.observation_id for item in observations)
    if (
        type(question.basis_observation_ids) is not tuple
        or question.basis_observation_ids != expected_basis
    ):
        raise SliceBRendererNoReportError("question basis mismatch")
    if question.review_scope_selection_evidence_digest != scope_digest:
        raise SliceBRendererNoReportError("question scope mismatch")
    _require_hash(question.review_scope_selection_evidence_digest, "question scope")
    _require_hash(question.question_id, "question_id")
    if question.question_id != _record_digest(question, "question_id"):
        raise SliceBRendererNoReportError("question identity mismatch")
    return question


def _question_lines(
    question: SliceBQuestionRenderIRV1,
    observations: SliceBObservationSetV1,
) -> list[bytes]:
    shape, cardinality, _, incidence = observations
    candidate = cardinality.candidate_unit_column_index + 1
    comparison = cardinality.comparison_column_index + 1
    sentence = (
        b"The intake-selected audit-scope CSV has "
        + _uint_bytes(shape.data_row_count)
        + b" verified data rows. Column C"
        + _uint_bytes(candidate)
        + b" has "
        + _uint_bytes(cardinality.candidate_unit_distinct_count)
        + b" distinct byte values; "
        + _uint_bytes(incidence.repeated_candidate_value_count)
        + b" values occur in multiple rows, and "
        + _uint_bytes(incidence.cross_comparison_candidate_value_count)
        + b" values occur with more than one distinct value of column C"
        + _uint_bytes(comparison)
        + b". Does the analysis under review use this CSV? If yes, does C"
        + _uint_bytes(candidate)
        + b" identify the scientific unit? If yes, does the scientific conclusion rely on a comparison organized by C"
        + _uint_bytes(comparison)
        + b"? If yes, does that comparison account for rows sharing one C"
        + _uint_bytes(candidate)
        + b" value as dependent observations?"
    )
    return [
        b"- Evidence grade: MATERIAL QUESTION. Question "
        + _hash_bytes(question.question_id)
        + b"; review-scope selection "
        + _hash_bytes(question.review_scope_selection_evidence_digest)
        + b". "
        + sentence,
        b"  Answer form: analysis uses selected CSV yes/no/unknown; C"
        + _uint_bytes(candidate)
        + b" is scientific unit yes/no/unknown/not-applicable; scientific conclusion relies on C"
        + _uint_bytes(comparison)
        + b" comparison yes/no/unknown/not-applicable; comparison accounts for shared-C"
        + _uint_bytes(candidate)
        + b" dependence yes/no/unknown/not-applicable.",
        b"  Why material: answers determine whether this selected CSV pattern is irrelevant to the scientific conclusion, resolved by dependence-aware treatment, or remains unresolved for conclusion support.",
        b"  Basis observations: "
        + b"; ".join(_hash_bytes(value) for value in question.basis_observation_ids)
        + b".",
    ]


def _observation_lines(observations: SliceBObservationSetV1) -> list[bytes]:
    shape, cardinality, group_sizes, incidence = observations
    candidate = cardinality.candidate_unit_column_index + 1
    comparison = cardinality.comparison_column_index + 1
    return [
        b"- Evidence grade: VERIFIED OBSERVATION. Type csv-table-shape-v1; observation "
        + _hash_bytes(shape.observation_id)
        + b"; content "
        + _hash_bytes(shape.content_digest)
        + b"; data rows "
        + _uint_bytes(shape.data_row_count)
        + b"; columns "
        + _uint_bytes(shape.column_count)
        + b".",
        b"- Evidence grade: VERIFIED OBSERVATION. Type csv-selected-cardinalities-v1; observation "
        + _hash_bytes(cardinality.observation_id)
        + b"; content "
        + _hash_bytes(cardinality.content_digest)
        + b"; candidate column C"
        + _uint_bytes(candidate)
        + b"; candidate distinct "
        + _uint_bytes(cardinality.candidate_unit_distinct_count)
        + b"; comparison column C"
        + _uint_bytes(comparison)
        + b"; comparison distinct "
        + _uint_bytes(cardinality.comparison_distinct_count)
        + b".",
        b"- Evidence grade: VERIFIED OBSERVATION. Type csv-comparison-group-sizes-v1; observation "
        + _hash_bytes(group_sizes.observation_id)
        + b"; content "
        + _hash_bytes(group_sizes.content_digest)
        + b"; comparison column C"
        + _uint_bytes(comparison)
        + b"; sorted group sizes "
        + _vector_bytes(group_sizes.sorted_group_sizes)
        + b".",
        b"- Evidence grade: VERIFIED OBSERVATION. Type csv-unit-comparison-incidence-v1; observation "
        + _hash_bytes(incidence.observation_id)
        + b"; content "
        + _hash_bytes(incidence.content_digest)
        + b"; candidate column C"
        + _uint_bytes(candidate)
        + b"; comparison column C"
        + _uint_bytes(comparison)
        + b"; repeated candidate values "
        + _uint_bytes(incidence.repeated_candidate_value_count)
        + b"; cross-comparison candidate values "
        + _uint_bytes(incidence.cross_comparison_candidate_value_count)
        + b"; comparison-values-per-candidate histogram "
        + _histogram_bytes(incidence.comparison_values_per_candidate_histogram)
        + b".",
    ]


def render_slice_b_component_v1(
    *,
    snapshot_digest: str,
    primary_refusal: SliceBPrimaryRefusalReasonV1 | None,
    observations: SliceBObservationSetV1 | None,
    question: SliceBQuestionRenderIRV1 | None,
    question_scope_unresolved: bool,
) -> bytes:
    """Render one closed Slice-B state or raise typed no-report.

    A valid primary refusal has precedence over every secondary/verified input and
    therefore never inspects or renders observations.  This lets the integration
    controller pass its first selected primary reason without laundering later state.
    """

    snapshot = _require_hash(snapshot_digest, "snapshot_digest")
    if primary_refusal is not None:
        if type(primary_refusal) is not SliceBPrimaryRefusalReasonV1:
            raise SliceBRendererNoReportError("unknown primary refusal")
        return _render_outer(
            snapshot_digest=snapshot,
            content_digest=None,
            question_lines=[b"None."],
            coverage_reason=_PRIMARY_COVERAGE_LINES[primary_refusal],
            observation_lines=[b"None."],
        )

    if type(question_scope_unresolved) is not bool:
        raise SliceBRendererNoReportError("scope state must be a concrete bool")
    verified = _validate_observations(observations)
    scope_digest = verified[0].review_scope_selection_evidence_digest
    predicate_fires = _question_predicate(verified)

    if question_scope_unresolved:
        if scope_digest != "unresolved" or question is not None:
            raise SliceBRendererNoReportError("unresolved scope state mismatch")
        rendered_question = [b"None."]
        coverage_reason = _SECONDARY_SCOPE_LINE
    else:
        _require_hash(scope_digest, "verified review scope")
        coverage_reason = None
        if predicate_fires:
            rendered_question = _question_lines(
                _validate_question(question, verified, scope_digest),
                verified,
            )
        else:
            if question is not None:
                raise SliceBRendererNoReportError("question emitted for false predicate")
            rendered_question = [b"None."]

    return _render_outer(
        snapshot_digest=snapshot,
        content_digest=verified[0].content_digest,
        question_lines=rendered_question,
        coverage_reason=coverage_reason,
        observation_lines=_observation_lines(verified),
    )


def _render_outer(
    *,
    snapshot_digest: str,
    content_digest: str | None,
    question_lines: list[bytes],
    coverage_reason: bytes | None,
    observation_lines: list[bytes],
) -> bytes:
    lines = [
        b"# sc-referee experimental Slice B report",
        b"",
        b"Input snapshot: " + _hash_bytes(snapshot_digest),
        b"Input CSV bytes: "
        + (b"UNVERIFIED" if content_digest is None else _hash_bytes(content_digest)),
        b"",
        b"## Findings",
        b"None.",
        b"",
        b"## Conditional concerns",
        b"None.",
        b"",
        b"## Material questions",
        *question_lines,
        b"",
        b"## Disclosures",
        b"None.",
        b"",
        b"## Coverage",
        _PERMANENT_COVERAGE_LINE,
    ]
    if coverage_reason is not None:
        lines.append(coverage_reason)
    lines.extend((b"", b"## Observation appendix", *observation_lines))
    report = b"\n".join(lines) + b"\n"
    if b"\r" in report or any(line.endswith(b" ") for line in report.split(b"\n")):
        raise AssertionError("closed renderer literal violated ASCII framing")
    return report
