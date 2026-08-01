from __future__ import annotations

import ast
import csv
import io
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from sc_referee.calculation_checks.core import (
    CalculationAdapterManifest,
    CalculationCheckManifest,
    CalculationCheckModule,
    CalculationCheckRegistry,
    CalculationContext,
    CalculationObservation,
    FrozenCalculationInput,
    NamedOperand,
    ObservationReceipt,
)
from sc_referee.calculation_checks.material_context import MaterialCalculationContext
from sc_referee.core.ids import semantic_digest, sha256_digest

MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_TABLE_BYTES = 8 * 1024 * 1024
MAX_TABLE_ROWS = 50_000
MAX_TABLE_COLUMNS = 64

_BLOCK = re.compile(
    r"```sc-referee-selection-reuse-v1\s*\n(?P<body>.*?)\n```",
    re.IGNORECASE | re.DOTALL,
)
_REQUIRED_KEYS = {
    "source_file",
    "results_table",
    "selection_object",
    "test_object",
    "groupby_key",
    "pvalue_column",
    "analysis_mode",
    "data_relationship",
    "safeguard",
    "producer_binding",
}
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "block_pattern": _BLOCK.pattern,
        "required_keys": sorted(_REQUIRED_KEYS),
        "analysis_mode": [
            "de_novo_marker_inference",
            "predefined_group_inference",
            "descriptive_marker_ranking",
            "unresolved",
        ],
        "data_relationship": [
            "same_expression_object",
            "disjoint_heldout_expression",
            "unresolved",
        ],
        "safeguard": ["none", "selection_aware", "unresolved"],
        "producer_binding": ["exact", "unresolved"],
        "static_profile": [
            "import scanpy as sc",
            "sc.pp.neighbors",
            "sc.tl.leiden",
            "sc.tl.rank_genes_groups",
        ],
        "ceilings": {
            "source_bytes": MAX_SOURCE_BYTES,
            "table_bytes": MAX_TABLE_BYTES,
            "table_rows": MAX_TABLE_ROWS,
            "table_columns": MAX_TABLE_COLUMNS,
        },
    }
)


class SelectionReuseError(ValueError):
    """Raised when a selection-reuse input escapes the closed contract."""


@dataclass(frozen=True)
class _Contract:
    source_file: str
    results_table: str
    selection_object: str
    test_object: str
    groupby_key: str
    pvalue_column: str
    analysis_mode: str
    data_relationship: str
    safeguard: str
    producer_binding: str
    source_ref: dict[str, Any]


@dataclass(frozen=True)
class _StaticPattern:
    neighbors_line: int
    cluster_line: int
    marker_test_line: int
    source_refs: tuple[dict[str, Any], ...]


class DeclaredSelectionReuseAdapter:
    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:declared-scanpy-selection-reuse-v1",
            adapter_version="1.0.0",
            implementation_digest=semantic_digest(
                {
                    "adapter_source": sha256_digest(Path(__file__).read_bytes()),
                    "recognition_grammar_digest": _RECOGNITION_GRAMMAR_DIGEST,
                }
            ),
            recognition_grammar_digest=_RECOGNITION_GRAMMAR_DIGEST,
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        try:
            report = context.selected_report.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise SelectionReuseError("selected report is not strict UTF-8") from error
        matches = list(_BLOCK.finditer(report))
        if not matches:
            return None
        if len(matches) != 1:
            return self._unsupported(
                context,
                context.selected_report.source_ref,
                "unique_selection_reuse_contract",
                "The selected report contains more than one selection-reuse contract.",
            )
        match = matches[0]
        source_ref = _block_source(context.selected_report, report, match)
        try:
            contract = _parse_contract(match.group("body"), source_ref)
        except SelectionReuseError as error:
            return self._unsupported(
                context,
                source_ref,
                "selection_reuse_contract_valid",
                str(error),
            )
        if contract.analysis_mode in {
            "predefined_group_inference",
            "descriptive_marker_ranking",
        }:
            return self._not_applicable(context, contract)
        if (
            contract.analysis_mode == "unresolved"
            or contract.data_relationship == "unresolved"
            or contract.safeguard == "unresolved"
            or contract.producer_binding == "unresolved"
        ):
            return self._unsupported(
                context,
                source_ref,
                "selection_test_semantics_resolved",
                "The analysis mode, data relationship, safeguard, or producer binding remains unresolved.",
            )
        if contract.safeguard == "selection_aware":
            return self._unsupported(
                context,
                source_ref,
                "selection_aware_safeguard_verified",
                "A selection-aware safeguard is declared, but this initial module does not verify its implementation contract.",
            )
        if not isinstance(context, MaterialCalculationContext):
            return self._unsupported(
                context,
                source_ref,
                "material_calculation_context_available",
                "The explicitly selected source and result table were not available in the frozen material-input view.",
            )
        source = _unique_material(context, contract.source_file)
        table = _unique_material(context, contract.results_table)
        if source is None or table is None:
            return self._unsupported(
                context,
                source_ref,
                "declared_selection_inputs_bound",
                "Exactly one fully identified source and result table could not be bound.",
                inputs=tuple(item for item in (source, table) if item is not None),
            )
        try:
            pattern = _inspect_source(source, contract)
            pvalue_count = _count_pvalues(table, contract)
        except SelectionReuseError as error:
            return self._unsupported(
                context,
                source_ref,
                "complete_selection_reuse_pattern",
                str(error),
                inputs=(source, table),
            )
        same_object = contract.selection_object == contract.test_object
        if contract.data_relationship == "same_expression_object" and not same_object:
            return self._unsupported(
                context,
                source_ref,
                "declared_same_object_matches_source",
                "The declared same-object relationship conflicts with the distinct bound source symbols.",
                inputs=(source, table),
            )
        if contract.data_relationship == "disjoint_heldout_expression" and same_object:
            return self._unsupported(
                context,
                source_ref,
                "declared_disjoint_objects_match_source",
                "The declared held-out relationship conflicts with reuse of one bound source symbol.",
                inputs=(source, table),
            )
        reused = contract.data_relationship == "same_expression_object"
        sources = (source_ref, *pattern.source_refs, table.source_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="nonconformant" if reused else "conformant",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, source.artifact_ref, table.artifact_ref),
            source_refs=sources,
            operands=(
                NamedOperand("source_path", "string", source.path),
                NamedOperand("results_table_path", "string", table.path),
                NamedOperand("selection_object", "string", contract.selection_object),
                NamedOperand("test_object", "string", contract.test_object),
                NamedOperand("groupby_key", "string", contract.groupby_key),
                NamedOperand("calibrated_pvalue_count", "integer", pvalue_count),
                NamedOperand("neighbors_line", "integer", pattern.neighbors_line),
                NamedOperand("cluster_line", "integer", pattern.cluster_line),
                NamedOperand("marker_test_line", "integer", pattern.marker_test_line),
                NamedOperand("same_expression_object_reused", "boolean", reused),
                NamedOperand("safeguard", "string", contract.safeguard),
                NamedOperand("data_relationship", "string", contract.data_relationship),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "explicit_de_novo_marker_inference_contract",
                    "passed",
                    (source_ref,),
                    "One closed declaration binds de-novo marker inference, data relationship, safeguard status, exact source, and result table.",
                ),
                ObservationReceipt(
                    "completeness",
                    "unique_ordered_scanpy_calls",
                    "passed",
                    pattern.source_refs,
                    "Unique neighbors, Leiden clustering, and marker-test calls use the declared objects and group key in source order.",
                ),
                ObservationReceipt(
                    "completeness",
                    "calibrated_result_column_present",
                    "passed",
                    (table.source_ref,),
                    f"The complete bounded table contains {pvalue_count} finite values in the declared p-value column.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "predefined_descriptive_or_safeguarded_analysis",
                    "passed",
                    (source_ref,),
                    "Predefined groups, descriptive rankings, unresolved semantics, and declared safeguards are separate non-adverse paths.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "This exact static pattern does not prove runtime object identity, execution, calibrated-p-value invalidity, numerical impact, or whether an unobserved safeguard exists.",
                "The initial adapter covers one explicit Scanpy call shape and does not generalize to arbitrary aliases, wrappers, Seurat, generated code, or notebook cross-cell mutation.",
                "No project-authored code was executed, and this module cannot emit a Finding.",
            ),
        )

    def _not_applicable(
        self, context: CalculationContext, contract: _Contract
    ) -> CalculationObservation:
        return CalculationObservation(
            applicability="not_applicable",
            comparison_outcome="not_applicable",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref,),
            source_refs=(contract.source_ref,),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "analysis_is_predefined_or_descriptive",
                    "not_applicable",
                    (contract.source_ref,),
                    "Predefined-group inference and descriptive marker rankings are outside the same-data de-novo inference pattern.",
                ),
            ),
            lineage_status="not_applicable",
            limitations=("No selection-reuse inference comparison applies to this declared mode.",),
        )

    def _unsupported(
        self,
        context: CalculationContext,
        source_ref: dict[str, Any],
        predicate: str,
        detail: str,
        *,
        inputs: tuple[FrozenCalculationInput, ...] = (),
    ) -> CalculationObservation:
        return CalculationObservation(
            applicability="unsupported",
            comparison_outcome="unknown",
            target_ref=context.selected_surface_ref,
            input_refs=(context.selected_artifact_ref, *(item.artifact_ref for item in inputs)),
            source_refs=(source_ref, *(item.source_ref for item in inputs)),
            operands=(),
            receipts=(
                ObservationReceipt(
                    "completeness",
                    predicate,
                    "unsupported",
                    (source_ref, *(item.source_ref for item in inputs)),
                    detail,
                ),
            ),
            lineage_status="incomplete",
            limitations=(detail, "No same-data selection/test incompatibility was inferred."),
        )


def selection_reuse_registry() -> CalculationCheckRegistry:
    adapter = DeclaredSelectionReuseAdapter()
    check = CalculationCheckManifest(
        check_id="calculation-check:scanpy-selection-reuse-v1",
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="declared_de_novo_selection_and_marker_test_data_separation",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The exact declared Scanpy source shape reuses one expression object for de-novo clustering and calibrated marker testing without a declared safeguard."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_scanpy_selection_reuse_v1",
    )


def _parse_contract(body: str, source_ref: dict[str, Any]) -> _Contract:
    try:
        value = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise SelectionReuseError("selection-reuse contract is not valid YAML") from error
    if not isinstance(value, dict) or set(value) != _REQUIRED_KEYS:
        raise SelectionReuseError("selection-reuse contract keys are missing or extra")
    if any(not isinstance(value[key], str) or not value[key].strip() for key in _REQUIRED_KEYS):
        raise SelectionReuseError("selection-reuse contract values must be nonempty strings")
    for key, suffixes in {
        "source_file": {".py"},
        "results_table": {".csv", ".tsv"},
    }.items():
        path = PurePosixPath(str(value[key]))
        if path.is_absolute() or ".." in path.parts or path.suffix.casefold() not in suffixes:
            raise SelectionReuseError(f"{key} is not one bounded supported path")
    for key in ("selection_object", "test_object", "groupby_key", "pvalue_column"):
        if not str(value[key]).isidentifier():
            raise SelectionReuseError(f"{key} must be one literal identifier")
    if value["analysis_mode"] not in {
        "de_novo_marker_inference",
        "predefined_group_inference",
        "descriptive_marker_ranking",
        "unresolved",
    }:
        raise SelectionReuseError("analysis mode is outside the closed vocabulary")
    if value["data_relationship"] not in {
        "same_expression_object",
        "disjoint_heldout_expression",
        "unresolved",
    }:
        raise SelectionReuseError("data relationship is outside the closed vocabulary")
    if value["safeguard"] not in {"none", "selection_aware", "unresolved"}:
        raise SelectionReuseError("safeguard is outside the closed vocabulary")
    if value["producer_binding"] not in {"exact", "unresolved"}:
        raise SelectionReuseError("producer binding is outside the closed vocabulary")
    return _Contract(
        **{key: str(value[key]).strip() for key in _REQUIRED_KEYS},
        source_ref=source_ref,
    )


def _inspect_source(source: FrozenCalculationInput, contract: _Contract) -> _StaticPattern:
    if len(source.content) > MAX_SOURCE_BYTES:
        raise SelectionReuseError("declared Python source exceeds the byte ceiling")
    try:
        text = source.content.decode("utf-8", errors="strict")
        tree = ast.parse(text, filename=source.path)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise SelectionReuseError("declared Python source did not parse completely") from error
    imports = [
        node
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "scanpy" and alias.asname == "sc"
    ]
    if len(imports) != 1 or any(
        isinstance(node, ast.Name) and node.id == "sc" and isinstance(node.ctx, ast.Store)
        for node in ast.walk(tree)
    ):
        raise SelectionReuseError("one stable `import scanpy as sc` binding was not established")
    wanted: dict[str, list[ast.Call]] = {
        "sc.pp.neighbors": [],
        "sc.tl.leiden": [],
        "sc.tl.rank_genes_groups": [],
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _attribute_name(node.func)
            if name in wanted:
                wanted[name].append(node)
    if any(len(nodes) != 1 for nodes in wanted.values()):
        raise SelectionReuseError("required Scanpy calls were absent or non-unique")
    neighbors = wanted["sc.pp.neighbors"][0]
    cluster = wanted["sc.tl.leiden"][0]
    marker = wanted["sc.tl.rank_genes_groups"][0]
    if not (
        _first_name(neighbors) == contract.selection_object
        and _first_name(cluster) == contract.selection_object
        and _first_name(marker) == contract.test_object
    ):
        raise SelectionReuseError("Scanpy call objects do not match the declared bindings")
    cluster_key = _literal_keyword(cluster, "key_added") or "leiden"
    marker_key = _literal_keyword(marker, "groupby")
    if cluster_key != contract.groupby_key or marker_key != contract.groupby_key:
        raise SelectionReuseError("cluster output key and marker groupby key do not match")
    if not (neighbors.lineno < cluster.lineno < marker.lineno):
        raise SelectionReuseError("selection and marker-test calls are not in the required order")
    bound_names = {contract.selection_object, contract.test_object}
    if any(
        isinstance(node, ast.Name)
        and node.id in bound_names
        and isinstance(node.ctx, (ast.Store, ast.Del))
        and neighbors.lineno < node.lineno < marker.lineno
        for node in ast.walk(tree)
    ):
        raise SelectionReuseError("a bound data symbol is reassigned between selection and testing")
    nodes = (neighbors, cluster, marker)
    refs = tuple(_node_source(source, text, node) for node in nodes)
    return _StaticPattern(neighbors.lineno, cluster.lineno, marker.lineno, refs)


def _count_pvalues(table: FrozenCalculationInput, contract: _Contract) -> int:
    if len(table.content) > MAX_TABLE_BYTES:
        raise SelectionReuseError("declared result table exceeds the byte ceiling")
    try:
        text = table.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SelectionReuseError("declared result table is not strict UTF-8") from error
    reader = csv.DictReader(
        io.StringIO(text, newline=""),
        delimiter="\t" if table.path.casefold().endswith(".tsv") else ",",
    )
    header = reader.fieldnames
    if (
        header is None
        or len(header) > MAX_TABLE_COLUMNS
        or len(set(header)) != len(header)
        or contract.pvalue_column not in header
    ):
        raise SelectionReuseError("declared p-value column is unavailable or ambiguous")
    count = 0
    rows = 0
    for rows, row in enumerate(reader, start=1):
        if rows > MAX_TABLE_ROWS:
            raise SelectionReuseError("declared result table exceeds the row ceiling")
        try:
            value = float(str(row.get(contract.pvalue_column, "")).strip())
        except ValueError as error:
            raise SelectionReuseError(
                "declared p-value column contains a nonnumeric value"
            ) from error
        if not math.isfinite(value) or value < 0 or value > 1:
            raise SelectionReuseError("declared p-value column contains a value outside [0, 1]")
        count += 1
    if rows == 0 or count == 0:
        raise SelectionReuseError("declared result table has no calibrated p-values")
    return count


def _attribute_name(node: ast.expr) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    return ".".join([current.id, *reversed(parts)])


def _first_name(call: ast.Call) -> str | None:
    return call.args[0].id if call.args and isinstance(call.args[0], ast.Name) else None


def _literal_keyword(call: ast.Call, name: str) -> str | None:
    values = [item.value for item in call.keywords if item.arg == name]
    if len(values) != 1 or not isinstance(values[0], ast.Constant):
        return None
    return values[0].value if isinstance(values[0].value, str) else None


def _node_source(source: FrozenCalculationInput, text: str, node: ast.Call) -> dict[str, Any]:
    start = int(node.lineno)
    end = int(getattr(node, "end_lineno", start))
    lines = text.splitlines()
    return {
        "source_kind": "file_span",
        "locator": f"{source.path}:{start}-{end}",
        "path": source.path,
        "content_digest": source.content_digest,
        "start_line": start,
        "end_line": end,
        "quoted_text": "\n".join(lines[start - 1 : end]),
    }


def _unique_material(
    context: MaterialCalculationContext, path: str
) -> FrozenCalculationInput | None:
    matches = [item for item in context.material_inputs if item.path == path]
    return matches[0] if len(matches) == 1 else None


def _block_source(
    report: FrozenCalculationInput, text: str, match: re.Match[str]
) -> dict[str, Any]:
    start = text.count("\n", 0, match.start()) + 1
    end = text.count("\n", 0, match.end()) + 1
    return {
        "source_kind": "file_span",
        "locator": f"{report.path}:{start}-{end}",
        "path": report.path,
        "content_digest": report.content_digest,
        "start_line": start,
        "end_line": end,
        "quoted_text": match.group(0),
    }
