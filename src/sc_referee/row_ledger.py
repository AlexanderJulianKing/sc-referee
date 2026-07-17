"""Deterministic exact-or-abstain fitted/evaluation row reconstruction.

This primitive deliberately has no finding or policy surface.  It publishes an atomic
artifact only after candidate replay reproduces the ordered bound source roster.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping

import numpy as np
import pandas as pd
from scipy import sparse

from sc_referee.row_ledger_digest import ledger_digest


class RowLedgerState(Enum):
    CERTIFIED_ROWS_RATIFIED = "certified_rows_ratified"
    NOT_AUDITED = "not_audited"


class RowLedgerMachineReason(str, Enum):
    ROW_LEDGER_NOT_DECLARED = "row_ledger_not_declared"
    ROW_LEDGER_NOT_RATIFIED = "row_ledger_not_ratified"
    FIT_ROWS_NOT_ATTESTED = "fit_rows_not_attested"
    SOURCE_BINDING_UNAVAILABLE = "source_binding_unavailable"
    SOURCE_COUNT_LENGTH_MISMATCH = "source_count_length_mismatch"
    SOURCE_OCCURRENCE_IDENTITY_UNAVAILABLE = "source_occurrence_identity_unavailable"
    AMBIGUOUS_DUPLICATE_OCCURRENCE = "ambiguous_duplicate_occurrence"
    UNEXPLAINED_OCCURRENCE_LOSS = "unexplained_occurrence_loss"
    UNSUPPORTED_PIPELINE_OPERATION = "unsupported_pipeline_operation"
    DECLARED_COLUMN_UNAVAILABLE = "declared_column_unavailable"
    THRESHOLD_SEMANTICS_UNAVAILABLE = "threshold_semantics_unavailable"
    OPERATION_ORDER_UNAVAILABLE = "operation_order_unavailable"
    AMBIGUOUS_TERMINAL_EXCLUSION = "ambiguous_terminal_exclusion"
    AGGREGATION_KEY_UNAVAILABLE = "aggregation_key_unavailable"
    AGGREGATION_NOT_EXACT = "aggregation_not_exact"
    AGGREGATION_MEMBERSHIP_MISMATCH = "aggregation_membership_mismatch"
    ZERO_COUNT_SEMANTICS_UNAVAILABLE = "zero_count_semantics_unavailable"
    LINEAGE_NOT_EXACT = "lineage_not_exact"
    FITTED_ROW_ORDER_UNAVAILABLE = "fitted_row_order_unavailable"
    EVALUATION_RELATION_NOT_RATIFIED = "evaluation_relation_not_ratified"
    SEPARATE_EVALUATION_ROSTER_UNSUPPORTED = "separate_evaluation_roster_unsupported"
    EVALUATION_ROWS_NOT_EXACT = "evaluation_rows_not_exact"
    UNSUPPORTED_LIBRARY_DROP = "unsupported_library_drop"
    FITTED_OBJECT_BINDING_UNSUPPORTED = "fitted_object_binding_unsupported"
    LEDGER_INTEGRITY_FAILURE = "ledger_integrity_failure"
    CERTIFIED_ROWS_RATIFIED = "certified_rows_ratified"


class RowsExactBasis(Enum):
    HUMAN_DECLARED = "human_declared"
    RECONSTRUCTED_CERTIFIED = "reconstructed_certified"
    UNAVAILABLE = "unavailable"


class Stage(Enum):
    FIT = "fit"
    EVALUATION = "evaluation"


class EvaluationRelation(Enum):
    VERIFIED_SAME_AS_FITTED = "verified_same_as_fitted"
    SEPARATE = "separate"
    NOT_APPLICABLE = "not_applicable"


class SupportedOperationKind(Enum):
    DECLARED_SUBSET = "declared_subset"
    DECLARED_QC_THRESHOLD = "declared_qc_threshold"
    COMPLETE_CASE = "complete_case"
    AGGREGATION = "aggregation"
    ZERO_COUNT_ROW = "zero_count_row"


class TerminalReason(Enum):
    DECLARED_SUBSET = "declared_subset"
    DECLARED_QC_THRESHOLD = "declared_qc_threshold"
    COMPLETE_CASE_MISSING_COVARIATE = "complete_case_missing_covariate"
    ZERO_COUNT_ROW = "zero_count_row"


_CONFIDENCE_FIELDS = frozenset({
    "source_snapshot_identity", "count_layer_identity", "source_occurrence_id_columns",
    "fitted_source_occurrence_ids", "evaluation_relation", "fitted_result_id",
    "target_coefficient",
})


@dataclass(frozen=True)
class TypedScalar:
    tag: str
    value: object

    def __post_init__(self):
        if self.tag not in {"null", "bool", "int", "float64", "str", "bytes"}:
            raise ValueError("invalid typed scalar tag")
        valid = {
            "null": self.value is None,
            "bool": isinstance(self.value, bool),
            "int": isinstance(self.value, int) and not isinstance(self.value, bool),
            "float64": isinstance(self.value, float) and math.isfinite(self.value),
            "str": isinstance(self.value, str),
            "bytes": isinstance(self.value, bytes),
        }[self.tag]
        if not valid:
            raise ValueError(f"value does not match typed scalar tag {self.tag}")

    @classmethod
    def from_value(cls, value):
        if isinstance(value, np.generic):
            value = value.item()
        if value is None or value is pd.NA:
            return cls("null", None)
        if isinstance(value, bool):
            return cls("bool", value)
        if isinstance(value, int):
            return cls("int", value)
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("non-finite scalar")
            return cls("float64", value)
        if isinstance(value, str):
            return cls("str", value)
        if isinstance(value, bytes):
            return cls("bytes", value)
        raise TypeError(f"unsupported scalar type: {type(value).__name__}")

    def to_value(self):
        return self.value


def _closed(value, enum_type, field):
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}") from exc


def _label(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty exact label")
    return value


@dataclass(frozen=True)
class SubsetOperation:
    operation_id: str
    column_id: str
    allowed_values: tuple[TypedScalar, ...]
    confidence: str

    def __post_init__(self):
        _label(self.operation_id, "operation_id"); _label(self.column_id, "column_id")
        values = tuple(self.allowed_values)
        if not values or any(not isinstance(v, TypedScalar) for v in values):
            raise ValueError("allowed_values must be non-empty typed scalars")
        if self.confidence not in ("high", "low"): raise ValueError("invalid confidence")
        object.__setattr__(self, "allowed_values", values)

    @property
    def kind(self): return SupportedOperationKind.DECLARED_SUBSET


@dataclass(frozen=True)
class QcThresholdOperation:
    operation_id: str
    column_id: str
    comparison: str
    threshold: TypedScalar
    missing_policy: str
    confidence: str

    def __post_init__(self):
        _label(self.operation_id, "operation_id"); _label(self.column_id, "column_id")
        if self.comparison not in {"ge", "gt", "le", "lt", "eq"}: raise ValueError("invalid comparison")
        if self.missing_policy not in {"drop", "keep"}: raise ValueError("invalid missing_policy")
        if not isinstance(self.threshold, TypedScalar): raise TypeError("threshold must be TypedScalar")
        if self.confidence not in ("high", "low"): raise ValueError("invalid confidence")

    @property
    def kind(self): return SupportedOperationKind.DECLARED_QC_THRESHOLD


@dataclass(frozen=True)
class CompleteCaseOperation:
    operation_id: str
    column_ids: tuple[str, ...]
    confidence: str

    def __post_init__(self):
        _label(self.operation_id, "operation_id")
        values = tuple(self.column_ids)
        if not values or len(set(values)) != len(values) or any(not isinstance(x, str) or not x for x in values):
            raise ValueError("column_ids must be unique exact labels")
        if self.confidence not in ("high", "low"): raise ValueError("invalid confidence")
        object.__setattr__(self, "column_ids", values)

    @property
    def kind(self): return SupportedOperationKind.COMPLETE_CASE


@dataclass(frozen=True)
class AggregationOperation:
    operation_id: str
    key_columns: tuple[str, ...]
    order: str
    confidence: str

    def __post_init__(self):
        _label(self.operation_id, "operation_id")
        keys = tuple(self.key_columns)
        if not keys or len(set(keys)) != len(keys) or any(not isinstance(x, str) or not x for x in keys):
            raise ValueError("key_columns must be unique exact labels")
        if self.order != "stable_first_occurrence": raise ValueError("invalid aggregation order")
        if self.confidence not in ("high", "low"): raise ValueError("invalid confidence")
        object.__setattr__(self, "key_columns", keys)

    @property
    def kind(self): return SupportedOperationKind.AGGREGATION


@dataclass(frozen=True)
class ZeroCountOperation:
    operation_id: str
    policy: str
    count_layer_identity: str
    confidence: str

    def __post_init__(self):
        _label(self.operation_id, "operation_id"); _label(self.count_layer_identity, "count_layer_identity")
        if self.policy != "total_library_equals_zero": raise ValueError("invalid zero-count policy")
        if self.confidence not in ("high", "low"): raise ValueError("invalid confidence")

    @property
    def kind(self): return SupportedOperationKind.ZERO_COUNT_ROW


SupportedOperation = (SubsetOperation, QcThresholdOperation, CompleteCaseOperation,
                      AggregationOperation, ZeroCountOperation)


@dataclass(frozen=True)
class RowLedgerDeclaration:
    schema_version: str
    source_snapshot_identity: str
    count_layer_identity: str
    source_occurrence_id_columns: tuple[str, ...]
    fitted_source_occurrence_ids: tuple[tuple[TypedScalar, ...], ...]
    operations: tuple[object, ...]
    evaluation_relation: EvaluationRelation
    evaluation_relation_confidence: str
    fitted_result_id: str
    target_coefficient: str
    field_confidence: Mapping[str, str]

    def __post_init__(self):
        if self.schema_version != "row-ledger-schema-v1": raise ValueError("invalid schema_version")
        for value, field in ((self.source_snapshot_identity, "source_snapshot_identity"),
                             (self.count_layer_identity, "count_layer_identity"),
                             (self.fitted_result_id, "fitted_result_id"),
                             (self.target_coefficient, "target_coefficient")):
            _label(value, field)
        columns = tuple(self.source_occurrence_id_columns)
        if not columns or len(set(columns)) != len(columns) or any(not isinstance(x, str) or not x for x in columns):
            raise ValueError("source_occurrence_id_columns must be unique exact labels")
        roster = tuple(tuple(item) for item in self.fitted_source_occurrence_ids)
        if any(len(item) != len(columns) or any(not isinstance(x, TypedScalar) for x in item) for item in roster):
            raise ValueError("fitted roster must contain typed occurrence IDs")
        operations = tuple(self.operations)
        if any(not isinstance(op, SupportedOperation) for op in operations):
            raise TypeError("operations must use the closed row-ledger operation types")
        ids = [op.operation_id for op in operations]
        if len(set(ids)) != len(ids): raise ValueError("operation IDs must be unique")
        relation = _closed(self.evaluation_relation, EvaluationRelation, "evaluation_relation")
        if self.evaluation_relation_confidence not in ("high", "low"): raise ValueError("invalid confidence")
        confidence = dict(self.field_confidence)
        if set(confidence) != _CONFIDENCE_FIELDS or any(v not in ("high", "low") for v in confidence.values()):
            raise ValueError("field_confidence must cover every row-ledger semantic field")
        object.__setattr__(self, "source_occurrence_id_columns", columns)
        object.__setattr__(self, "fitted_source_occurrence_ids", roster)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "evaluation_relation", relation)
        object.__setattr__(self, "field_confidence", MappingProxyType(confidence))


OccurrenceId = tuple[TypedScalar, ...]


@dataclass(frozen=True)
class SourceOccurrence:
    source_position: int
    source_occurrence_id: OccurrenceId
    unit_id: tuple[TypedScalar, ...]
    source_snapshot_identity: str


@dataclass(frozen=True)
class FittedOccurrence:
    fitted_position: int
    canonical_row_key: tuple[TypedScalar, ...]
    occurrence_ordinal: int
    source_occurrence_ids: tuple[OccurrenceId, ...]
    carried_values: tuple[tuple[str, TypedScalar], ...]


@dataclass(frozen=True)
class EvaluationLedger:
    relation: EvaluationRelation
    occurrences: tuple[FittedOccurrence, ...]
    row_identity: str | None


@dataclass(frozen=True)
class TerminalExclusion:
    stage: Stage
    operation_id: str
    reason: TerminalReason
    affected_occurrence_id: OccurrenceId
    operands: tuple[tuple[str, object], ...]
    antecedent_operation_ids: tuple[str, ...]


@dataclass(frozen=True)
class LineageEdge:
    parent_occurrence_id: OccurrenceId
    operation_id: str
    child_fitted_position: int
    edge_role: str = "member_of_aggregation"


@dataclass(frozen=True)
class OperationBoundary:
    operation_id: str
    kind: SupportedOperationKind
    ordered_input_identity: str
    ordered_survivor_identity: str
    ordered_terminal_removal_identity: str
    ordered_derived_identity: str | None


@dataclass(frozen=True)
class RowLedgerArtifact:
    candidate_occurrences: tuple[SourceOccurrence, ...]
    fitted_occurrences: tuple[FittedOccurrence, ...]
    evaluation: EvaluationLedger
    exclusions: tuple[TerminalExclusion, ...]
    lineage_edges: tuple[LineageEdge, ...]
    operation_trace: tuple[OperationBoundary, ...]
    core_pseudobulk_row_identity: str
    fitted_row_identity: str
    evaluation_row_identity: str | None
    exclusion_identity: str
    lineage_identity: str
    confirmed_facts_identity: str
    row_ledger_identity: str
    reconstruction_policy_version: str = "row-ledger-reconstruction-v1"
    digest_policy_version: str = "row-ledger-digest-v1"


@dataclass(frozen=True)
class RowLedgerDiagnostic:
    last_reconciled_operation_id: str | None
    expected_occurrence_ids: tuple[OccurrenceId, ...]
    observed_occurrence_ids: tuple[OccurrenceId, ...]


@dataclass(frozen=True)
class RowLedgerResult:
    state: RowLedgerState
    reason: str
    machine_reason: RowLedgerMachineReason
    certified_stages: tuple[Stage, ...]
    artifact: RowLedgerArtifact | None
    diagnostic: RowLedgerDiagnostic | None


@dataclass(frozen=True)
class SourceReplay:
    candidate_occurrences: tuple[SourceOccurrence, ...]
    survivor_ids: tuple[OccurrenceId, ...]
    survivor_source_positions: tuple[int, ...]
    survivor_rows: pd.DataFrame
    exclusions: tuple[TerminalExclusion, ...]
    operation_trace: tuple[OperationBoundary, ...]


def _not(reason, text=None, diagnostic=None):
    reason = RowLedgerMachineReason(reason)
    return RowLedgerResult(RowLedgerState.NOT_AUDITED, text or reason.value.replace("_", " "), reason,
                           (), None, diagnostic)


def _typed(value):
    if pd.isna(value): return TypedScalar("null", None)
    return TypedScalar.from_value(value)


def _identity_rows(source, declaration):
    if source.columns.duplicated().any(): raise _LedgerIssue("source_occurrence_identity_unavailable")
    if any(col not in source.columns for col in declaration.source_occurrence_id_columns):
        raise _LedgerIssue("source_occurrence_identity_unavailable")
    ids = []
    for _, row in source.iterrows():
        try: oid = tuple(_typed(row[col]) for col in declaration.source_occurrence_id_columns)
        except (TypeError, ValueError): raise _LedgerIssue("source_occurrence_identity_unavailable")
        if any(value.tag == "null" for value in oid): raise _LedgerIssue("source_occurrence_identity_unavailable")
        ids.append(oid)
    if len(set(ids)) != len(ids): raise _LedgerIssue("ambiguous_duplicate_occurrence")
    return tuple(ids)


class _LedgerIssue(Exception):
    def __init__(self, reason, diagnostic=None): self.reason, self.diagnostic = reason, diagnostic


def _boundary(op, before, after, removed, derived=None):
    return OperationBoundary(op.operation_id, op.kind,
        ledger_digest("operation-input", before), ledger_digest("operation-survivors", after),
        ledger_digest("operation-terminal-removals", removed),
        None if derived is None else ledger_digest("operation-derived", derived))


def _compare(value, threshold, comparison):
    if isinstance(value, np.generic): value = value.item()
    if isinstance(value, bool) or isinstance(threshold, bool):
        if comparison != "eq": raise _LedgerIssue("threshold_semantics_unavailable")
    if type(value) is not type(threshold) and not (
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and isinstance(threshold, (int, float)) and not isinstance(threshold, bool)
    ):
        raise _LedgerIssue("threshold_semantics_unavailable")
    try:
        return {"ge": value >= threshold, "gt": value > threshold, "le": value <= threshold,
                "lt": value < threshold, "eq": value == threshold}[comparison]
    except (TypeError, ValueError): raise _LedgerIssue("threshold_semantics_unavailable")


def replay_source_operations(source, counts, design, declaration):
    if not isinstance(source, pd.DataFrame): raise _LedgerIssue("source_binding_unavailable")
    count_rows = counts.shape[0] if sparse.issparse(counts) else len(counts)
    if len(source) != count_rows: raise _LedgerIssue("source_count_length_mismatch")
    ids = _identity_rows(source, declaration)
    agg = next((op for op in declaration.operations if isinstance(op, AggregationOperation)), None)
    unit_columns = () if agg is None else agg.key_columns
    occurrences = tuple(SourceOccurrence(i, oid,
        tuple(_typed(source.iloc[i][col]) for col in unit_columns if col in source.columns),
        declaration.source_snapshot_identity) for i, oid in enumerate(ids))
    active = list(range(len(source))); exclusions=[]; trace=[]; antecedents=[]
    for op in declaration.operations:
        if isinstance(op, (AggregationOperation, ZeroCountOperation)): continue
        columns = ((op.column_id,) if isinstance(op, (SubsetOperation, QcThresholdOperation))
                   else op.column_ids)
        if source.columns.duplicated().any() or any(col not in source.columns for col in columns):
            raise _LedgerIssue("declared_column_unavailable")
        before = tuple(ids[i] for i in active); keep=[]; removed=[]
        for pos in active:
            row = source.iloc[pos]
            if isinstance(op, SubsetOperation):
                try: scalar = _typed(row[op.column_id])
                except (TypeError, ValueError): raise _LedgerIssue("source_occurrence_identity_unavailable")
                survives = scalar in op.allowed_values
                operands = (("column_id", op.column_id), ("observed", scalar),
                            ("allowed_values", op.allowed_values))
                reason = TerminalReason.DECLARED_SUBSET
            elif isinstance(op, QcThresholdOperation):
                raw = row[op.column_id]
                missing = bool(pd.isna(raw))
                survives = op.missing_policy == "keep" if missing else _compare(raw, op.threshold.value, op.comparison)
                operands = (("column_id", op.column_id), ("comparison", op.comparison),
                            ("threshold", op.threshold), ("observed", _typed(raw)))
                reason = TerminalReason.DECLARED_QC_THRESHOLD
            else:
                missing_columns = tuple(col for col in op.column_ids if pd.isna(row[col]))
                survives = not missing_columns
                operands = (("missing_columns", missing_columns),)
                reason = TerminalReason.COMPLETE_CASE_MISSING_COVARIATE
            if survives: keep.append(pos)
            else:
                removed.append(ids[pos])
                exclusions.append(TerminalExclusion(Stage.FIT, op.operation_id, reason, ids[pos],
                                                    operands, tuple(antecedents)))
        active = keep
        after = tuple(ids[i] for i in active); trace.append(_boundary(op, before, after, tuple(removed)))
        antecedents.append(op.operation_id)
    rows = source.iloc[active].reset_index(drop=True)
    return SourceReplay(occurrences, tuple(ids[i] for i in active), tuple(active), rows,
                        tuple(exclusions), tuple(trace))


def aggregate_positions(counts, group_positions):
    matrix = sparse.csr_matrix(counts) if sparse.issparse(counts) else np.asarray(counts)
    if sparse.issparse(matrix):
        rows = [sparse.csr_matrix(matrix[np.asarray(pos, dtype=int)].sum(axis=0))
                for pos in group_positions]
        return sparse.vstack(rows, format="csr") if rows else sparse.csr_matrix((0, matrix.shape[1]))
    rows = [matrix[np.asarray(pos, dtype=int)].sum(axis=0) for pos in group_positions]
    return np.asarray(rows)


def _make_artifact(replay, grouped, aggregated, declaration, required_stages):
    agg_op = next(op for op in declaration.operations if isinstance(op, AggregationOperation))
    zero_op = next((op for op in declaration.operations if isinstance(op, ZeroCountOperation)), None)
    fitted=[]; edges=[]; exclusions=list(replay.exclusions); derived=[]; ordinals={}
    for group_pos, positions in enumerate(grouped.group_positions):
        key = tuple(_typed(grouped.rows.iloc[group_pos][col]) for col in agg_op.key_columns)
        ordinal = ordinals.get(key, 0); ordinals[key] = ordinal + 1
        derived_id = key + (TypedScalar.from_value(ordinal),)
        derived.append(derived_id)
        if zero_op is not None and aggregated[group_pos].sum() == 0:
            exclusions.append(TerminalExclusion(Stage.FIT, zero_op.operation_id,
                TerminalReason.ZERO_COUNT_ROW, derived_id,
                (("policy", zero_op.policy), ("count_layer_identity", zero_op.count_layer_identity)), (agg_op.operation_id,)))
            continue
        fitted_pos = len(fitted)
        members = tuple(replay.survivor_ids[int(i)] for i in positions)
        carried = tuple((str(col), _typed(grouped.rows.iloc[group_pos][col])) for col in grouped.rows.columns)
        fitted.append(FittedOccurrence(fitted_pos, key, ordinal, members, carried))
        edges.extend(LineageEdge(parent, agg_op.operation_id, fitted_pos) for parent in members)
    trace = list(replay.operation_trace)
    trace.append(_boundary(agg_op, replay.survivor_ids, tuple(derived), (), tuple(derived)))
    if zero_op is not None:
        kept = tuple(row.canonical_row_key + (TypedScalar.from_value(row.occurrence_ordinal),) for row in fitted)
        removed = tuple(x.affected_occurrence_id for x in exclusions if x.operation_id == zero_op.operation_id)
        trace.append(_boundary(zero_op, tuple(derived), kept, removed))
    fitted = tuple(fitted); edges=tuple(edges); exclusions=tuple(exclusions); trace=tuple(trace)
    fit_id=ledger_digest("fitted-occurrences", fitted)
    if Stage.EVALUATION in required_stages and declaration.evaluation_relation is EvaluationRelation.VERIFIED_SAME_AS_FITTED:
        eval_id=ledger_digest("evaluation-occurrences", fitted)
        evaluation=EvaluationLedger(declaration.evaluation_relation, fitted, eval_id)
    else:
        eval_id=None; evaluation=EvaluationLedger(EvaluationRelation.NOT_APPLICABLE, (), None)
    exclusion_id=ledger_digest("terminal-exclusions", exclusions)
    lineage_id=ledger_digest("lineage-edges", edges)
    facts=(declaration.schema_version, declaration.source_snapshot_identity, declaration.count_layer_identity,
           declaration.source_occurrence_id_columns, declaration.fitted_source_occurrence_ids,
           declaration.operations, declaration.evaluation_relation, declaration.evaluation_relation_confidence,
           declaration.fitted_result_id, declaration.target_coefficient,
           tuple(sorted(declaration.field_confidence.items())))
    facts_id=ledger_digest("confirmed-facts", facts)
    components=(replay.candidate_occurrences, fitted, evaluation, exclusions, edges, trace,
                grouped.row_ledger_identity, fit_id, eval_id, exclusion_id, lineage_id, facts_id,
                "row-ledger-reconstruction-v1", "row-ledger-digest-v1")
    identity=ledger_digest("row-ledger-artifact", components)
    return RowLedgerArtifact(replay.candidate_occurrences, fitted, evaluation, exclusions, edges, trace,
        grouped.row_ledger_identity, fit_id, eval_id, exclusion_id, lineage_id, facts_id, identity)


def build_aggregation_ledger(replay, grouped, aggregated, declaration,
                             required_stages=(Stage.FIT,)):
    return _make_artifact(replay, grouped, aggregated, declaration, tuple(required_stages))


def reconstruct_row_ledger(source, counts, design, declaration=None, *, required_stages=(Stage.FIT,)):
    if declaration is None: return _not("row_ledger_not_declared")
    if not isinstance(declaration, RowLedgerDeclaration): return _not("unsupported_pipeline_operation")
    if any(not isinstance(op, SupportedOperation) for op in declaration.operations):
        kinds = {getattr(op, "kind", None) for op in declaration.operations}
        if kinds & {"library_size_factor_drop", "weight_drop", "offset_drop", "rank_drop"}:
            return _not("unsupported_library_drop")
        return _not("unsupported_pipeline_operation")
    stages = tuple(required_stages)
    if any(not isinstance(stage, Stage) for stage in stages): return _not("fitted_object_binding_unsupported")
    if any(value != "high" for value in declaration.field_confidence.values()) or any(
        op.confidence != "high" for op in declaration.operations
    ): return _not("row_ledger_not_ratified")
    if not getattr(design, "confirmed_by_human", False): return _not("fit_rows_not_attested")
    if getattr(design, "fitted_design", None) is None or design.fitted_design.rows_exact is not True \
            or design.confidence.get("fitted_design") != "high":
        return _not("fit_rows_not_attested")
    if design.target_coefficient != declaration.target_coefficient:
        return _not("source_binding_unavailable")
    if not declaration.source_snapshot_identity.startswith("sha256:") or not declaration.count_layer_identity.startswith("sha256:"):
        return _not("source_binding_unavailable")
    operations=declaration.operations
    if sum(isinstance(op, AggregationOperation) for op in operations) != 1:
        return _not("operation_order_unavailable")
    agg_index=next(i for i,op in enumerate(operations) if isinstance(op,AggregationOperation))
    if any(isinstance(op,(SubsetOperation,QcThresholdOperation,CompleteCaseOperation)) for op in operations[agg_index+1:]):
        return _not("operation_order_unavailable")
    if any(isinstance(op,ZeroCountOperation) for op in operations[:agg_index]):
        return _not("operation_order_unavailable")
    if sum(isinstance(op,ZeroCountOperation) for op in operations) > 1:
        return _not("operation_order_unavailable")
    zero=next((op for op in operations if isinstance(op,ZeroCountOperation)),None)
    if zero is not None and zero.count_layer_identity != declaration.count_layer_identity:
        return _not("zero_count_semantics_unavailable")
    if Stage.EVALUATION in stages:
        if declaration.evaluation_relation_confidence != "high": return _not("evaluation_relation_not_ratified")
        if declaration.evaluation_relation is EvaluationRelation.SEPARATE:
            return _not("separate_evaluation_roster_unsupported")
        if declaration.evaluation_relation is not EvaluationRelation.VERIFIED_SAME_AS_FITTED:
            return _not("evaluation_rows_not_exact")
    try:
        if counts is None:
            return _not("zero_count_semantics_unavailable" if zero is not None else "source_binding_unavailable")
        matrix=sparse.csr_matrix(counts) if sparse.issparse(counts) else np.asarray(counts)
        if getattr(matrix, "ndim", 2) != 2 or matrix.shape[0] != len(source):
            return _not("source_count_length_mismatch")
        values = matrix.data if sparse.issparse(matrix) else matrix
        if zero is not None and (not np.issubdtype(matrix.dtype,np.number)
                                 or not np.isfinite(values).all() or (values < 0).any()):
            return _not("zero_count_semantics_unavailable")
        replay=replay_source_operations(source,matrix,design,declaration)
        if replay.survivor_ids != declaration.fitted_source_occurrence_ids:
            source_ops=[op for op in operations if isinstance(op,(SubsetOperation,QcThresholdOperation,CompleteCaseOperation))]
            last=(source_ops[-2].operation_id if len(source_ops)>1 else None)
            diagnostic=RowLedgerDiagnostic(last,replay.survivor_ids,declaration.fitted_source_occurrence_ids)
            return _not("unexplained_occurrence_loss", diagnostic=diagnostic)
        from sc_referee.engine import build_pseudobulk_sample_rows
        grouped=build_pseudobulk_sample_rows(replay.survivor_rows,design)
        if not grouped.exact:
            reason="aggregation_not_exact" if grouped.machine_reason=="within_sample_column_variation" else "aggregation_key_unavailable"
            return _not(reason)
        agg=next(op for op in operations if isinstance(op,AggregationOperation))
        if tuple(design.aggregation_key or ()) != agg.key_columns:
            return _not("aggregation_membership_mismatch")
        aggregated=aggregate_positions(matrix[np.asarray(replay.survivor_source_positions)],grouped.group_positions)
        artifact=_make_artifact(replay,grouped,aggregated,declaration,stages)
        certified=tuple(stage for stage in (Stage.FIT,Stage.EVALUATION) if stage in stages)
        return RowLedgerResult(RowLedgerState.CERTIFIED_ROWS_RATIFIED,
            "Exact fitted rows reconstructed from ratified facts.", RowLedgerMachineReason.CERTIFIED_ROWS_RATIFIED,
            certified, artifact, None)
    except _LedgerIssue as exc:
        return _not(exc.reason, diagnostic=exc.diagnostic)
    except (TypeError, ValueError, IndexError, KeyError, OverflowError):
        return _not("ledger_integrity_failure")
