"""Contract-bound CSV and Python-AST dependence observation.

The adapter reads only controller-frozen structured records, the authorized CSV
bytes, Python source bytes, and established API syntax.  Reports, Markdown,
comments, docstrings, and printed wording are never evidence or suppressors.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.adapter_common import adapter_implementation_digest
from sc_referee.scientific_checks.code_csv_dependence_dataflow import (
    CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST,
    CodeDataflowFacts,
    analyze_code_csv_dataflow,
    select_code_source_envelope,
)
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionReceipt,
    NormalizedMethodObservation,
    ObservationState,
    RecordRef,
    RoleBinding,
)
from sc_referee.scientific_checks.dependence_recognition_adapter import (
    DEPENDENCE_RECOGNITION_CANDIDATE_ID,
    DEPENDENCE_RECOGNITION_CHECK_ID,
)
from sc_referee.scientific_checks.report_csv_dependence_adapter import (
    _Authority,
    _authority,
    _CsvFacts,
    _parse_csv,
)
from sc_referee.scientific_checks.scope_joins import full_digest_identity_path

DEPENDENCE_RECOGNITION_CHECK_VERSION = "2.2.0"
CODE_CSV_DEPENDENCE_ADAPTER_ID = (
    "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
    "code-csv-rowwise-two-sample-v1"
)
CODE_CSV_DEPENDENCE_ADAPTER_VERSION = "2.2.0"
CODE_CSV_DEPENDENCE_SEMANTIC_ROLES = (
    "authorized_independent_unit_key",
    "analyzed_row_domain",
    "row_independent_procedure",
    "result_output_sink",
)
CODE_CSV_DEPENDENCE_ROLE_BINDINGS = (
    RoleBinding("authorized_independent_unit_key", "human_authorized_independent_unit_key"),
    RoleBinding("analyzed_row_domain", "complete_authorized_csv_row_partition"),
    RoleBinding("row_independent_procedure", "registered_row_independent_two_sample_call"),
    RoleBinding("result_output_sink", "registered_test_p_result_output_sink"),
)
CODE_CSV_DEPENDENCE_COUNTEREVIDENCE = (
    "verified-contract-authority",
    "exact-selected-full-csv",
    "complete-csv-domain",
    "d1-prime-composite-scan",
    "exact-two-group-domain",
    "analysis-source-envelope",
    "alternate-analysis-file-scan",
    "other-python-statistics-import-scan",
    "prose-free-source-view",
    "api-resolution-and-scope",
    "single-authorized-reader-lineage",
    "two-group-row-selection",
    "authorized-reader-operand-provenance",
    "direct-path-counterevidence",
    "reader-component-counterevidence",
    "tracked-control-flow",
    "test-result-output-sink",
    "code-lineage-uniqueness",
    "full-digest-snapshot-scope",
)

_SAFE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_READER_IDS = {
    "pandas_read_csv_v1",
    "numpy_genfromtxt_named_csv_v1",
    "csv_dictreader_materialized_v1",
    "csv_dictreader_bucket_loop_v1",
}
_PROCEDURES = {"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"}
_VARIANTS = {"student", "welch", "mannwhitneyu"}


@dataclass(frozen=True)
class CodeCsvRowEntryEvidenceProjection:
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
    analysis_path: str
    analysis_content_digest: str
    analysis_file_ref: RecordRef
    alternate_analysis_file_scan_complete: bool
    other_python_statistics_import_scan_complete: bool
    reader_api: str
    accepted_reader_count: int
    all_test_operand_paths_rooted_in_authorized_reader: bool
    selection_kinds: tuple[str, str]
    value_column: str
    group_values: tuple[str, str]
    group_row_counts: tuple[int, int]
    all_csv_rows_partitioned: bool
    procedure_id: str
    procedure_variant: str
    output_sink_kinds: tuple[str, ...]
    dataflow_max_definition_nodes: int
    descriptive_loop_count: int
    aggregation_path_scan_complete: bool
    dependence_guard_scan_complete: bool
    unsupported_call_scan_complete: bool
    unregistered_output_call_scan_complete: bool
    authority_binding_digest: str
    code_evidence_spans: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        arrays = (
            self.composite_key_candidate_columns,
            self.distinct_count_excluded_columns,
            self.within_unit_index_columns,
            self.unique_pair_within_unit_index_columns,
            self.unique_nonindex_authorized_unit_composite_columns,
            self.output_sink_kinds,
        )
        if (
            self.material_file_ref.record_type != "file_record"
            or self.analysis_file_ref.record_type != "file_record"
            or self.analysis_path != "analysis.py"
            or any(
                _SAFE_DIGEST.fullmatch(value) is None
                for value in (
                    self.material_input_content_digest,
                    self.analysis_content_digest,
                    self.authority_binding_digest,
                )
            )
            or not 2 <= self.distinct_unit_count < self.data_row_count
            or self.repeated_unit_count < 1
            or self.maximum_unit_multiplicity < 2
            or any(value != tuple(sorted(set(value))) for value in arrays)
            or self.unique_nonindex_authorized_unit_composite_columns
            or not set(self.within_unit_index_columns).issubset(
                self.composite_key_candidate_columns
            )
            or not set(self.unique_pair_within_unit_index_columns).issubset(
                self.within_unit_index_columns
            )
            or self.composite_key_scan_complete is not True
            or self.alternate_analysis_file_scan_complete is not True
            or self.other_python_statistics_import_scan_complete is not True
            or self.reader_api not in _READER_IDS
            or self.accepted_reader_count != 1
            or self.all_test_operand_paths_rooted_in_authorized_reader is not True
            or len(set(self.group_values)) != 2
            or any(not value for value in self.group_values)
            or any(value < 1 for value in self.group_row_counts)
            or sum(self.group_row_counts) != self.data_row_count
            or self.all_csv_rows_partitioned is not True
            or self.procedure_id not in _PROCEDURES
            or self.procedure_variant not in _VARIANTS
            or not 1 <= self.dataflow_max_definition_nodes <= 16
            or self.descriptive_loop_count < 0
            or any(
                value is not True
                for value in (
                    self.aggregation_path_scan_complete,
                    self.dependence_guard_scan_complete,
                    self.unsupported_call_scan_complete,
                    self.unregistered_output_call_scan_complete,
                )
            )
            or not self.code_evidence_spans
        ):
            raise ValueError("code/CSV row-entry fact is outside the closed profile")
        roles = [str(item.get("role")) for item in self.code_evidence_spans]
        if (
            roles.count("reader") != 1
            or roles.count("left_selection") != 1
            or roles.count("right_selection") != 1
            or roles.count("procedure") != 1
            or roles.count("output_sink") < 1
        ):
            raise ValueError("code/CSV row-entry evidence roles are incomplete")

    def to_dict(self) -> dict[str, Any]:
        projection: dict[str, Any] = {
            "profile": "code_csv_row_entry_evidence_v1",
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
            "analysis_path": self.analysis_path,
            "analysis_content_digest": self.analysis_content_digest,
            "analysis_file_ref": self.analysis_file_ref.to_dict(),
            "alternate_analysis_file_scan_complete": (self.alternate_analysis_file_scan_complete),
            "other_python_statistics_import_scan_complete": (
                self.other_python_statistics_import_scan_complete
            ),
            "reader_api": self.reader_api,
            "accepted_reader_count": self.accepted_reader_count,
            "all_test_operand_paths_rooted_in_authorized_reader": (
                self.all_test_operand_paths_rooted_in_authorized_reader
            ),
            "selection_kinds": list(self.selection_kinds),
            "value_column": self.value_column,
            "group_values": list(self.group_values),
            "group_row_counts": list(self.group_row_counts),
            "all_csv_rows_partitioned": self.all_csv_rows_partitioned,
            "procedure_id": self.procedure_id,
            "procedure_variant": self.procedure_variant,
            "output_sink_kinds": list(self.output_sink_kinds),
            "dataflow_max_definition_nodes": self.dataflow_max_definition_nodes,
            "descriptive_loop_count": self.descriptive_loop_count,
            "aggregation_path_scan_complete": self.aggregation_path_scan_complete,
            "dependence_guard_scan_complete": self.dependence_guard_scan_complete,
            "unsupported_call_scan_complete": self.unsupported_call_scan_complete,
            "unregistered_output_call_scan_complete": (self.unregistered_output_call_scan_complete),
            "authority_binding_digest": self.authority_binding_digest,
            "code_evidence_spans": [dict(item) for item in self.code_evidence_spans],
        }
        projection["fact_digest"] = semantic_digest(projection)
        return projection


@dataclass(frozen=True)
class CodeCsvNormalizedMethodObservation(NormalizedMethodObservation):
    row_entry_evidence: CodeCsvRowEntryEvidenceProjection | None = None

    def to_dict(self) -> dict[str, Any]:
        value = super().to_dict()
        if self.row_entry_evidence is not None:
            value["row_entry_evidence"] = self.row_entry_evidence.to_dict()
        return value


def code_csv_dependence_grammar() -> dict[str, Any]:
    """Return the complete digest-bound code/CSV recognition grammar."""

    return {
        "grammar_id": "bounded-code-csv-rowwise-two-sample-dependence-v1",
        "grammar_version": CODE_CSV_DEPENDENCE_ADAPTER_VERSION,
        "profile_version": "1.2.0",
        "check_id": DEPENDENCE_RECOGNITION_CHECK_ID,
        "candidate_id": DEPENDENCE_RECOGNITION_CANDIDATE_ID,
        "source": {
            "path": "analysis.py",
            "parser": "parser:python-ast-tokenize@0.15.1",
            "bytes_max": 1 << 20,
            "ast_nodes_max": 50_000,
            "definition_nodes_max": 16,
            "prose_evidence": False,
        },
        "reader_ids": sorted(_READER_IDS),
        "procedure_ids": sorted(_PROCEDURES),
        "semantic_roles": [item.to_dict() for item in CODE_CSV_DEPENDENCE_ROLE_BINDINGS],
        "counterevidence": list(CODE_CSV_DEPENDENCE_COUNTEREVIDENCE),
        "dataflow_implementation_digest": (CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST),
        "output_ceiling": "question_only",
        "project_authored_code_execution": False,
    }


def code_csv_dependence_grammar_digest() -> str:
    return semantic_digest(code_csv_dependence_grammar())


CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))


@dataclass(frozen=True)
class CodeCsvDependenceAdapter:
    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    one_row_operand: CanonicalOperand
    multiple_rows_operand: CanonicalOperand
    role_bindings: tuple[RoleBinding, ...] = CODE_CSV_DEPENDENCE_ROLE_BINDINGS

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return code_csv_dependence_grammar_digest()

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        try:
            return self._inspect(context)
        except (ArithmeticError, csv.Error, UnicodeError, ValueError):
            return self._abstain("unsupported", "code-csv-dependence-inspection-exception")

    def _inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        authority = _authority(context.shared_derivations, self.check_manifest)
        if authority is None:
            return self._abstain("unsupported", "verified-contract-authority-unavailable")
        material_result = self._material_and_csv(context, authority)
        if isinstance(material_result, NormalizedMethodObservation):
            return material_result
        material, csv_facts = material_result
        if csv_facts.unique_nonindex_columns:
            return self._abstain(
                "unsupported",
                "unique-nonindex-authorized-unit-composite-key-possible",
            )
        group_domain = _group_domain(
            material.content,
            csv_facts.header,
            authority.group_column,
        )
        if group_domain is None:
            return self._abstain("unsupported", "authorized-group-domain-not-exactly-two")

        envelope = select_code_source_envelope(
            base_records=context.base_records,
            documents=context.documents,
        )
        if envelope.reason is not None or envelope.analysis is None:
            return self._abstain(
                "unsupported", envelope.reason or "analysis-source-envelope-unavailable"
            )
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

        dataflow = analyze_code_csv_dataflow(
            analysis.content,
            authorized_path=authority.path,
            unit_column=authority.unit_column,
            group_column=authority.group_column,
            csv_header=csv_facts.header,
            group_values=(group_domain[0][0], group_domain[1][0]),
        )
        if dataflow.reason is not None or dataflow.facts is None:
            return self._abstain("unsupported", dataflow.reason or "code-dataflow-graph-incomplete")
        code = dataflow.facts
        counts = dict(group_domain)
        selected_counts = (
            counts.get(code.group_values[0], 0),
            counts.get(code.group_values[1], 0),
        )
        if (
            set(code.group_values) != set(counts)
            or any(value < 1 for value in selected_counts)
            or sum(selected_counts) != csv_facts.n
        ):
            return self._abstain("unsupported", "two-group-row-selection-unavailable")
        evidence_spans = tuple(
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
            for item in code.evidence_spans
            if analysis.parser_result_ref is not None
        )
        if len(evidence_spans) != len(code.evidence_spans):
            return self._abstain("unsupported", "analysis-source-envelope-unavailable")
        fact = _fact(
            authority=authority,
            material=material,
            csv_facts=csv_facts,
            analysis=analysis,
            code=code,
            group_counts=selected_counts,
        )
        receipt_projection = {
            "authority_binding_digest": authority.binding_digest,
            "fact_digest": fact.to_dict()["fact_digest"],
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
        return CodeCsvNormalizedMethodObservation(
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
            observed_operand=self.multiple_rows_operand,
            evidence_spans=evidence_spans,
            scope_join_path=tuple(item.edge for item in proof),
            receipts=receipts,
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            row_entry_evidence=fact,
        )

    def _material_and_csv(
        self, context: FrozenInspectionContext, authority: _Authority
    ) -> tuple[Any, _CsvFacts] | NormalizedMethodObservation:
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
        return material, csv_result

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
            evidence_plane="static_source",
            method_target_ref=None,
            role_bindings=(),
            observed_operand=None,
            evidence_spans=(),
            scope_join_path=(),
            receipts=(
                InspectionReceipt(
                    receipt_id="closed-code-csv-dependence-abstention",
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


def _group_domain(
    content: bytes,
    header: Sequence[str],
    group_column: str,
) -> tuple[tuple[str, int], tuple[str, int]] | None:
    try:
        text = content.decode("utf-8", errors="strict")
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    except (UnicodeError, csv.Error):
        return None
    if not rows or tuple(rows[0]) != tuple(header) or group_column not in header:
        return None
    index = tuple(header).index(group_column)
    values = [row[index] for row in rows[1:] if len(row) == len(header)]
    counts = Counter(values)
    if len(values) != len(rows) - 1 or len(counts) != 2 or any(not value for value in counts):
        return None
    order = tuple(dict.fromkeys(values))
    if len(order) != 2:
        return None
    return ((order[0], counts[order[0]]), (order[1], counts[order[1]]))


def _snapshot_ref(context: FrozenInspectionContext) -> RecordRef | None:
    matches = [
        record.ref
        for record in context.base_records
        if record.ref.record_type == "repository_snapshot"
    ]
    return matches[0] if len(matches) == 1 else None


def _fact(
    *,
    authority: _Authority,
    material: Any,
    csv_facts: _CsvFacts,
    analysis: Any,
    code: CodeDataflowFacts,
    group_counts: tuple[int, int],
) -> CodeCsvRowEntryEvidenceProjection:
    return CodeCsvRowEntryEvidenceProjection(
        material_input_path=material.path,
        material_input_content_digest=material.content_digest,
        material_file_ref=material.file_ref,
        authorized_unit_column=authority.unit_column,
        group_contrast_column=authority.group_column,
        data_row_count=csv_facts.n,
        distinct_unit_count=csv_facts.unit_count,
        repeated_unit_count=csv_facts.repeated_unit_count,
        maximum_unit_multiplicity=csv_facts.maximum_multiplicity,
        composite_key_scan_complete=True,
        composite_key_candidate_columns=csv_facts.candidate_columns,
        distinct_count_excluded_columns=csv_facts.distinct_excluded_columns,
        within_unit_index_columns=csv_facts.within_unit_index_columns,
        unique_pair_within_unit_index_columns=csv_facts.unique_pair_within_unit_index_columns,
        unique_nonindex_authorized_unit_composite_columns=(),
        analysis_path=analysis.path,
        analysis_content_digest=analysis.content_digest,
        analysis_file_ref=analysis.file_ref,
        alternate_analysis_file_scan_complete=True,
        other_python_statistics_import_scan_complete=True,
        reader_api=code.reader_api,
        accepted_reader_count=1,
        all_test_operand_paths_rooted_in_authorized_reader=True,
        selection_kinds=code.selection_kinds,
        value_column=code.value_column,
        group_values=code.group_values,
        group_row_counts=group_counts,
        all_csv_rows_partitioned=True,
        procedure_id=code.procedure_id,
        procedure_variant=code.procedure_variant,
        output_sink_kinds=code.output_sink_kinds,
        dataflow_max_definition_nodes=code.dataflow_max_definition_nodes,
        descriptive_loop_count=code.descriptive_loop_count,
        aggregation_path_scan_complete=True,
        dependence_guard_scan_complete=True,
        unsupported_call_scan_complete=True,
        unregistered_output_call_scan_complete=True,
        authority_binding_digest=authority.binding_digest,
        code_evidence_spans=tuple(
            {
                "role": item.role,
                "path": "analysis.py",
                "start_line": item.start_line,
                "end_line": item.end_line,
                "start_column": item.start_column,
                "end_column": item.end_column,
            }
            for item in code.evidence_spans
        ),
    )
