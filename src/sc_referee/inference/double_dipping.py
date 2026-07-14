"""Parse-only, exact-summary double-dipping evidence for the live flagship policy.

This module is deliberately a narrow supported subset.  It proves only straight-line flows from a
code-owned selection summary, through one exact ``obs`` field write, into one exact Scanpy marker
sink and a measured p-value report.  Every unresolved call, branch, dynamic field, ambiguous sink,
or unknown feature region leaves at least one policy premise ``UNKNOWN``.
"""
from __future__ import annotations

import ast
import hashlib
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from sc_referee.inference.analysis.dependence import (
    Alternative,
    Atom,
    DependenceProgram,
    Derivation,
    Guard,
    TransformBinding,
)
from sc_referee.inference.claims.inventory import ClaimRootGrade, ReportClaim
from sc_referee.inference.claims.slice import ClaimSlice, slice_claim
from sc_referee.inference.contracts.registry import SummaryRegistry, resolve_summary
from sc_referee.inference.contracts.schema import (
    CalleeBinding,
    EffectContract,
    FunctionSummary,
    SummaryBinding,
)
from sc_referee.inference.domains.calibration import Naive, infer_calibration
from sc_referee.inference.domains.selection import SelectionEvent, infer_selection_event
from sc_referee.source_ast import (
    callsite_id,
    const_str,
    iter_call_sites,
    parse_sources,
    resolve_callee,
    source_env,
)


DOUBLE_DIPPING_PREMISES = (
    "ClaimMustProducedByTest",
    "GroupingMustProducedBySelection",
    "TestDefinitelyNaive",
    "RelevantRegionOverlapDefinite",
    "SelectionReuseDependentUnderNull",
    "PinnedReachable",
)


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class ScientificSummary:
    summary: FunctionSummary
    kind: str
    calibration: str | None = None


def _summary(module: str, symbol: str, version: str, kind: str,
             *, calibration: str | None = None) -> ScientificSummary:
    identity = f"{module}|{symbol}|{version}|double-dipping-summary-v2"
    semantics = f"{identity}|kind={kind}|calibration={calibration or 'none'}"
    binding = SummaryBinding(
        module,
        symbol,
        version,
        _digest(identity),
        _digest(semantics),
    )
    return ScientificSummary(FunctionSummary(binding, EffectContract()), kind, calibration)


# Code-owned, immutable contracts.  Names alone never resolve these: callers must first prove the
# canonical module/symbol through source_ast's import-aware resolver.
_SCIENTIFIC_SUMMARIES = (
    _summary("scanpy.tl", "rank_genes_groups", ">=1.9,<2", "marker_test"),
    _summary("sklearn.mixture", "GaussianMixture.fit_predict", ">=1.2,<2", "selection"),
    _summary("sklearn.cluster", "KMeans.fit_predict", ">=1.2,<2", "selection"),
    _summary("scanpy.tl", "leiden", ">=1.9,<2", "selection"),
    _summary("scanpy.tl", "louvain", ">=1.9,<2", "selection"),
    _summary("scanpy.pp", "neighbors", ">=1.9,<2", "expression_graph"),
    _summary("scanpy", "read_h5ad", ">=1.9,<2", "artifact_read"),
    _summary("scanpy.get", "rank_genes_groups_df", ">=1.9,<2", "marker_extract"),
    _summary("pandas.core.generic", "DataFrame.to_csv", ">=1.5,<3", "report_egress"),
)
_BY_IDENTITY = {
    (item.summary.binding.module, item.summary.binding.symbol): item
    for item in _SCIENTIFIC_SUMMARIES
}
_SUMMARY_REGISTRY = SummaryRegistry(item.summary for item in _SCIENTIFIC_SUMMARIES)


def _resolve_scientific(module: str, symbol: str) -> ScientificSummary | None:
    item = _BY_IDENTITY.get((module, symbol))
    if item is None:
        return None
    binding = item.summary.binding
    resolution = resolve_summary(CalleeBinding(
        binding.module,
        binding.symbol,
        binding.version,
        binding.package_or_source_digest,
        binding.summary_digest,
    ), _SUMMARY_REGISTRY)
    return item if resolution.status == "exact" else None


@dataclass(frozen=True)
class FeatureRegion:
    kind: str  # all | exact | external | unknown
    object_id: str | None = None
    ids: frozenset[str] = frozenset()
    data_partition: str | None = None


@dataclass(frozen=True)
class _SelectionValue:
    producer: str
    region: FeatureRegion
    summary: ScientificSummary


@dataclass(frozen=True)
class _MarkerTest:
    producer: str
    object_id: str
    grouping_field: str
    region: FeatureRegion
    summary: ScientificSummary
    callsite: str
    method: str | None
    calibration: str | None
    result_key: str
    groups: frozenset[str] | None


@dataclass(frozen=True)
class _MarkerResultValue:
    producer: str
    binding: SummaryBinding
    result_key: str
    groups: frozenset[str] | None


@dataclass(frozen=True)
class _ReportEgress:
    path: str
    producer: str
    callsite: str
    binding: SummaryBinding
    result_key: str
    groups: frozenset[str] | None


@dataclass(frozen=True)
class DoubleDippingEvidence:
    relations: Mapping[str, str]
    premise_sources: Mapping[str, str]
    claim_slice: ClaimSlice
    grouping_slice: ClaimSlice
    summary_bindings: tuple[SummaryBinding, ...]
    test_producer: str | None
    selection_producer: str | None
    producing_value_digest: str | None
    inventory_complete: bool
    unknown_reasons: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "relations", MappingProxyType(dict(self.relations)))
        object.__setattr__(self, "premise_sources", MappingProxyType(dict(self.premise_sources)))


def _literal_strings(node: ast.AST) -> frozenset[str] | None:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    values = []
    for item in node.elts:
        value = const_str(item)
        if value is None:
            return None
        values.append(value)
    return frozenset(values)


def _subscript_key(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Subscript):
        return None
    return const_str(node.slice)


def _feature_region(node: ast.AST, known_objects: set[str],
                    invalid_fields: set[tuple[str, str, str]]) -> FeatureRegion:
    """Recognize only exact expression inputs and exact literal feature subsets."""
    if isinstance(node, ast.Name):
        # A bare object is a response only after an exact artifact read bound its identity.  Its
        # spelling is never evidence.
        if node.id in known_objects:
            return FeatureRegion("all", node.id, data_partition="expression")
        return FeatureRegion("unknown")
    if isinstance(node, ast.Attribute) and node.attr == "X":
        if (isinstance(node.value, ast.Name) and node.value.id in known_objects
                and (node.value.id, "attribute", "X") not in invalid_fields):
            return FeatureRegion("all", node.value.id, data_partition="expression")
        if (isinstance(node.value, ast.Attribute) and node.value.attr == "raw"
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id in known_objects):
            return FeatureRegion("all", node.value.value.id, data_partition="raw")
        if (isinstance(node.value, ast.Subscript) and isinstance(node.value.value, ast.Name)
                and node.value.value.id in known_objects):
            # adata[:, ['g1', ...]].X
            index = node.value.slice
            if isinstance(index, ast.Tuple) and len(index.elts) == 2:
                features = _literal_strings(index.elts[1])
                if features is not None:
                    return FeatureRegion("exact", node.value.value.id, features, "expression")
        return FeatureRegion("unknown")
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
        base = node.value.value
        key = _subscript_key(node)
        if isinstance(base, ast.Name) and base.id in known_objects and node.value.attr == "obsm":
            if key is not None and (base.id, "obsm", key) in invalid_fields:
                return FeatureRegion("unknown")
            if key is not None and key.startswith("X_"):
                return FeatureRegion("all", base.id, data_partition="expression")
            if key == "spatial":
                return FeatureRegion("external", base.id, data_partition="spatial")
        if (isinstance(base, ast.Name) and base.id in known_objects
                and node.value.attr == "layers" and key is not None):
            if (base.id, "layers", key) in invalid_fields:
                return FeatureRegion("unknown")
            return FeatureRegion("all", base.id, data_partition=f"layer:{key}")
    return FeatureRegion("unknown")


def _definite_overlap(left: FeatureRegion, right: FeatureRegion) -> bool | None:
    if left.kind in {"unknown", "external"} or right.kind in {"unknown", "external"}:
        return None
    if left.object_id != right.object_id:
        return None
    if left.data_partition != right.data_partition:
        comparable = {left.data_partition, right.data_partition} <= {"expression", "raw"}
        if not comparable:
            # Distinct literal layers/matrices are not assumed dependent or independent.  A future
            # exact count-split summary may refute reuse; without it, neither direction is proved.
            return None
    if left.kind == "all" and right.kind == "all":
        return True
    if left.kind == "all" and right.kind == "exact":
        return bool(right.ids)
    if left.kind == "exact" and right.kind == "all":
        return bool(left.ids)
    if left.kind == right.kind == "exact":
        return bool(left.ids & right.ids)
    return None


def _keyword(call: ast.Call, name: str) -> ast.AST | None:
    return next((item.value for item in call.keywords if item.arg == name), None)


def _arg(call: ast.Call, name: str, index: int) -> ast.AST | None:
    return _keyword(call, name) or (call.args[index] if len(call.args) > index else None)


def _obs_field(node: ast.AST) -> tuple[str, str] | None:
    if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Attribute):
        return None
    if node.value.attr != "obs" or not isinstance(node.value.value, ast.Name):
        return None
    field = const_str(node.slice)
    return (node.value.value.id, field) if field is not None else None


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _literal_bool(node: ast.AST | None) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


_UNKNOWN_SELECTOR = object()


def _group_selector(node: ast.AST | None):
    """None means the complete group family; a frozenset is an exact requested subset."""
    if node is None or (isinstance(node, ast.Constant) and node.value is None):
        return None
    value = const_str(node)
    if value is not None:
        return frozenset({value})
    values = _literal_strings(node)
    return values if values is not None else _UNKNOWN_SELECTOR


def _groups_correspond(test_groups, extracted_groups) -> bool:
    if test_groups is _UNKNOWN_SELECTOR or extracted_groups is _UNKNOWN_SELECTOR:
        return False
    if test_groups is None or extracted_groups is None:
        return True
    return bool(extracted_groups) and extracted_groups <= test_groups


def _reported_feature_ids(reported) -> frozenset[str] | None:
    if reported is None or not hasattr(reported, "columns") or "feature_id" not in reported.columns:
        return None
    values = []
    for item in reported["feature_id"]:
        if item is None:
            continue
        value = str(item).strip()
        if value and value.lower() not in {"nan", "<na>"}:
            values.append(value)
    return frozenset(values) if values else None


def _fit_predict_summary(call: ast.Call, env, constructed: Mapping[str, tuple[str, str]]):
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "fit_predict":
        return None
    if "fit_predict" in env.patched_attrs:
        return None
    receiver = call.func.value
    identity = None
    if isinstance(receiver, ast.Call):
        fake_site = SimpleCallSite(receiver)
        resolved = resolve_callee(fake_site, env)
        if resolved in {("sklearn.mixture", "GaussianMixture"),
                        ("sklearn.cluster", "KMeans")}:
            identity = (resolved[0], f"{resolved[1]}.fit_predict")
    elif isinstance(receiver, ast.Name):
        base = constructed.get(receiver.id)
        if base is not None:
            identity = (base[0], f"{base[1]}.fit_predict")
    return _resolve_scientific(*identity) if identity is not None else None


class SimpleCallSite:
    """Minimal source_ast call-site view for resolving a constructor expression."""

    def __init__(self, call: ast.Call):
        self.call = call
        self.symbol_cased = (call.func.attr if isinstance(call.func, ast.Attribute)
                             else call.func.id if isinstance(call.func, ast.Name) else "")


def _identity_program(root: str, producer: str | None, source_id: str) -> DependenceProgram:
    if producer is None:
        return DependenceProgram({}, {}, frozenset())
    alternative = Alternative(
        f"alternative:{source_id}",
        Guard(f"guard:{source_id}", True, True),
        f"definition:{source_id}",
        Atom(producer),
        TransformBinding("affine_linear_q.v1", "identity"),
    )
    return DependenceProgram(
        {root: Derivation(root, (alternative,))},
        {},
        frozenset({producer}),
    )


def _empty_slice(claim_id: str, root: str) -> ClaimSlice:
    claim = ReportClaim(claim_id, root, "pvalue", ClaimRootGrade.DIAGNOSTIC_ONLY, False)
    return slice_claim(DependenceProgram(), claim)


def _claims_pvalue(reported) -> bool:
    if reported is None or not hasattr(reported, "columns"):
        return False
    pvalue_columns = {
        "padj", "pvalue", "p_value", "p-value", "pval", "pvals", "pvals_adj",
        "adj_p_value", "adj_pval", "adjusted_pvalue", "qvalue", "qval", "qvals", "fdr",
        "adj_p", "p_val", "p_val_adj", "adj.p.val", "p.value",
    }
    matching = [item for item in reported.columns
                if str(item).strip().lower() in pvalue_columns]
    for column in matching:
        for item in reported[column]:
            try:
                value = float(item)
            except (TypeError, ValueError):
                continue
            if math.isfinite(value) and 0 <= value <= 1:
                return True
    return False


def compute_double_dipping_evidence(
    sources: tuple[str, ...],
    reported,
    *,
    report_relative_path: str | None = None,
    data_relative_path: str | None = None,
) -> DoubleDippingEvidence:
    """Compute the six policy relations from real parsed code and a real report object."""
    parsed = parse_sources(sources)
    sites = iter_call_sites(parsed)
    sites_by_node = {id(site.call): site for site in sites}
    reported_features = _reported_feature_ids(reported)
    variables: dict[str, _SelectionValue] = {}
    constructed: dict[str, tuple[str, str]] = {}
    obs: dict[tuple[str, str], _SelectionValue] = {}
    selections: list[_SelectionValue] = []
    tests: list[_MarkerTest] = []
    marker_values: dict[str, _MarkerResultValue] = {}
    known_objects: set[str] = set()
    invalid_fields: set[tuple[str, str, str]] = set()
    selection_bases: dict[str, FeatureRegion] = {}
    report_egresses: list[_ReportEgress] = []
    literal_csv_writes: list[str] = []
    unknown_csv_write = False
    summaries: list[SummaryBinding] = []
    unknown_reasons: list[str] = []

    for parsed_source in parsed:
        if parsed_source.tree is None:
            unknown_reasons.append(f"parse_error:{parsed_source.source_index}")
            continue
        env = source_env(parsed_source)
        for statement in parsed_source.tree.body:
            value = statement.value if isinstance(statement, (ast.Assign, ast.AnnAssign)) else None
            targets = (statement.targets if isinstance(statement, ast.Assign)
                       else (statement.target,) if isinstance(statement, ast.AnnAssign) else ())

            if value is not None:
                aliased_marker_values = {
                    node.id for node in ast.walk(value)
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
                    and node.id in marker_values
                }
                for marker_name in aliased_marker_values:
                    marker_values.pop(marker_name, None)
                    unknown_reasons.append("possible_marker_result_mutation")

            # A strong name assignment kills every prior exact facet before the new RHS is
            # interpreted.  Keeping a stale constructor/selection/egress value here would turn an
            # intervening overwrite into a false must-flow witness.
            for target in targets:
                target_root = _root_name(target)
                if target_root in marker_values:
                    marker_values.pop(target_root, None)
                    unknown_reasons.append("possible_marker_result_mutation")
                if isinstance(target, ast.Name):
                    constructed.pop(target.id, None)
                    variables.pop(target.id, None)
                    marker_values.pop(target.id, None)
                    known_objects.discard(target.id)
                elif (isinstance(target, ast.Subscript)
                      and isinstance(target.value, ast.Attribute)
                      and target.value.attr in {"obsp", "uns", "obsm", "layers"}
                      and isinstance(target.value.value, ast.Name)):
                    selection_bases.pop(target.value.value.id, None)
                    key = const_str(target.slice)
                    if target.value.attr in {"obsm", "layers"} and key is not None:
                        invalid_fields.add((target.value.value.id, target.value.attr, key))
                elif (isinstance(target, ast.Attribute) and target.attr == "X"
                      and isinstance(target.value, ast.Name)):
                    invalid_fields.add((target.value.id, "attribute", "X"))

            # Track exact fitted selector construction for a later model.fit_predict call.
            if isinstance(value, ast.Call) and len(targets) == 1 and isinstance(targets[0], ast.Name):
                site = sites_by_node.get(id(value))
                resolved = resolve_callee(site, env) if site is not None else None
                if resolved == ("scanpy", "read_h5ad"):
                    summary = _resolve_scientific(*resolved)
                    path_node = _arg(value, "filename", 0)
                    path = const_str(path_node) if path_node is not None else None
                    if summary is not None and path is not None and path == data_relative_path:
                        known_objects.add(targets[0].id)
                        invalid_fields = {item for item in invalid_fields
                                          if item[0] != targets[0].id}
                        summaries.append(summary.summary.binding)
                if resolved in {("sklearn.mixture", "GaussianMixture"),
                                ("sklearn.cluster", "KMeans")}:
                    constructed[targets[0].id] = resolved

            # Exact selection event returning labels.
            if isinstance(value, ast.Call):
                summary = _fit_predict_summary(value, env, constructed)
                if summary is not None and len(targets) == 1 and isinstance(targets[0], ast.Name):
                    input_node = value.args[0] if value.args else None
                    region = (_feature_region(input_node, known_objects, invalid_fields)
                              if input_node is not None else FeatureRegion("unknown"))
                    site = sites_by_node.get(id(value))
                    if region.kind not in {"unknown", "external"} and site is not None:
                        producer = f"selection:{site.id}"
                        event = SelectionEvent(
                            producer, "clustering", (ast.dump(input_node),), targets[0].id,
                            features=region, summary_binding=summary.summary.binding,
                        )
                        inferred = infer_selection_event(
                            event, method_name="fit_predict", binding=summary.summary.binding,
                            ratified=False,
                        )
                        if event in inferred.must:
                            selected = _SelectionValue(producer, region, summary)
                            variables[targets[0].id] = selected
                            selections.append(selected)
                            summaries.append(summary.summary.binding)

            # Exact extraction of the latest sole marker result into a DataFrame-like value.
            if (isinstance(value, ast.Call) and len(targets) == 1
                    and isinstance(targets[0], ast.Name)):
                site = sites_by_node.get(id(value))
                resolved = resolve_callee(site, env) if site is not None else None
                summary = (_resolve_scientific(*resolved)
                           if resolved == ("scanpy.get", "rank_genes_groups_df") else None)
                response = _arg(value, "adata", 0)
                response_region = (_feature_region(response, known_objects, invalid_fields)
                                   if response is not None
                                   else FeatureRegion("unknown"))
                if (summary is not None and len(tests) == 1
                        and response_region.object_id == tests[0].region.object_id):
                    test = tests[0]
                    key_node = _keyword(value, "key")
                    extracted_key = ("rank_genes_groups" if key_node is None
                                     else const_str(key_node))
                    extracted_groups = _group_selector(_arg(value, "group", 1))
                    if extracted_key != test.result_key:
                        unknown_reasons.append("marker_result_key_mismatch")
                    elif not _groups_correspond(test.groups, extracted_groups):
                        unknown_reasons.append("marker_result_group_mismatch")
                    else:
                        marker_values[targets[0].id] = _MarkerResultValue(
                            test.producer,
                            summary.summary.binding,
                            test.result_key,
                            extracted_groups,
                        )
                        summaries.append(summary.summary.binding)

            # Exact strong write labels -> literal obs field.  Anything else strongly replaces it.
            for target in targets:
                object_field = _obs_field(target)
                if object_field is None:
                    continue
                selected = variables.get(value.id) if isinstance(value, ast.Name) else None
                if selected is not None:
                    obs[object_field] = selected
                else:
                    obs.pop(object_field, None)

            # Scanpy's implicit selection calls write a literal/default obs field.
            call = statement.value if isinstance(statement, ast.Expr) else None
            if isinstance(call, ast.Call):
                site = sites_by_node.get(id(call))
                resolved = resolve_callee(site, env) if site is not None else None
                if (isinstance(call.func, ast.Attribute)
                        and isinstance(call.func.value, ast.Name)
                        and call.func.value.id in marker_values
                        and call.func.attr != "to_csv"):
                    marker_values.pop(call.func.value.id, None)
                    unknown_reasons.append("possible_marker_result_mutation")
                for argument in (*call.args, *(item.value for item in call.keywords)):
                    if isinstance(argument, ast.Name) and argument.id in marker_values:
                        marker_values.pop(argument.id, None)
                        unknown_reasons.append("possible_marker_result_mutation")
                if resolved == ("scanpy.pp", "neighbors"):
                    summary = _resolve_scientific(*resolved)
                    response = _arg(call, "adata", 0)
                    response_region = (_feature_region(response, known_objects, invalid_fields)
                                       if response is not None
                                       else FeatureRegion("unknown"))
                    use_rep = _keyword(call, "use_rep")
                    if use_rep is not None:
                        rep = const_str(use_rep)
                        response_region = (FeatureRegion("all", response_region.object_id,
                                                         data_partition="expression")
                                           if rep is not None and rep.startswith("X_")
                                           and response_region.object_id is not None
                                           else FeatureRegion("unknown"))
                    if (summary is not None and response_region.kind == "all"
                            and response_region.object_id is not None):
                        selection_bases[response_region.object_id] = response_region
                        summaries.append(summary.summary.binding)
                is_csv_write = (isinstance(call.func, ast.Attribute)
                                and call.func.attr == "to_csv")
                csv_path_node = _arg(call, "path_or_buf", 0) if is_csv_write else None
                csv_path = const_str(csv_path_node) if csv_path_node is not None else None
                if is_csv_write:
                    if csv_path is None:
                        unknown_csv_write = True
                    else:
                        literal_csv_writes.append(csv_path)
                # A report root is exact only when the exact extracted marker value is serialized to
                # the literal report path.  A method-shaped call on any other value is not evidence.
                if (isinstance(call.func, ast.Attribute) and call.func.attr == "to_csv"
                        and isinstance(call.func.value, ast.Name)
                        and call.func.value.id in marker_values and "to_csv" not in env.patched_attrs
                        and site is not None):
                    path = csv_path
                    summary = _resolve_scientific(
                        "pandas.core.generic", "DataFrame.to_csv"
                    )
                    if path is not None and summary is not None:
                        marker = marker_values[call.func.value.id]
                        report_egresses.append(_ReportEgress(
                            path,
                            marker.producer,
                            site.id,
                            summary.summary.binding,
                            marker.result_key,
                            marker.groups,
                        ))
                        summaries.extend((marker.binding, summary.summary.binding))
                if resolved in {("scanpy.tl", "leiden"), ("scanpy.tl", "louvain")}:
                    summary = _resolve_scientific(*resolved)
                    response = _arg(call, "adata", 0)
                    adjacency = _keyword(call, "adjacency")
                    response_region = (_feature_region(response, known_objects, invalid_fields)
                                       if response is not None
                                       else FeatureRegion("unknown"))
                    region = (selection_bases.get(response_region.object_id,
                                                  FeatureRegion("unknown"))
                              if adjacency is None else FeatureRegion("unknown"))
                    key = const_str(_keyword(call, "key_added")) or resolved[1]
                    if summary is not None and region.kind == "all" and site is not None:
                        producer = f"selection:{site.id}"
                        event = SelectionEvent(
                            producer, "clustering", (ast.dump(response),), key,
                            features=region, summary_binding=summary.summary.binding,
                        )
                        inferred = infer_selection_event(
                            event, method_name=resolved[1], binding=summary.summary.binding,
                            ratified=False,
                        )
                        if event in inferred.must:
                            selected = _SelectionValue(producer, region, summary)
                            obs[(region.object_id, key)] = selected
                            selections.append(selected)
                            summaries.append(summary.summary.binding)

                if resolved == ("scanpy.tl", "rank_genes_groups"):
                    summary = _resolve_scientific(*resolved)
                    grouping_node = _arg(call, "groupby", 1)
                    grouping = const_str(grouping_node) if grouping_node is not None else None
                    response = _arg(call, "adata", 0)
                    region = (_feature_region(response, known_objects, invalid_fields)
                              if response is not None
                              else FeatureRegion("unknown"))
                    layer_node = _keyword(call, "layer")
                    use_raw_node = _keyword(call, "use_raw")
                    if layer_node is not None:
                        layer = const_str(layer_node)
                        region = (FeatureRegion(region.kind, region.object_id, region.ids,
                                                f"layer:{layer}")
                                  if layer is not None and region.object_id is not None
                                  else FeatureRegion("unknown"))
                    if use_raw_node is not None:
                        use_raw = _literal_bool(use_raw_node)
                        if use_raw is True and layer_node is None and region.object_id is not None:
                            region = FeatureRegion(region.kind, region.object_id, region.ids, "raw")
                        elif use_raw is not False:
                            region = FeatureRegion("unknown")
                    mask = _keyword(call, "mask_var")
                    if mask is not None:
                        exact = _literal_strings(mask)
                        region = (FeatureRegion("exact", region.object_id, exact,
                                                region.data_partition)
                                  if exact is not None and region.object_id is not None
                                  else FeatureRegion("unknown"))
                    if reported_features is not None and region.object_id is not None:
                        claim_features = (reported_features if region.kind == "all"
                                          else region.ids & reported_features
                                          if region.kind == "exact" else None)
                        if claim_features is not None:
                            region = FeatureRegion("exact", region.object_id, claim_features,
                                                   region.data_partition)
                    method = const_str(_keyword(call, "method"))
                    calibration = ("naive" if method in {
                        "t-test", "t-test_overestim_var", "wilcoxon",
                    } else None)
                    result_key_node = _keyword(call, "key_added")
                    result_key = ("rank_genes_groups" if result_key_node is None
                                  else const_str(result_key_node))
                    groups = _group_selector(_keyword(call, "groups"))
                    if (summary is not None and grouping is not None and site is not None
                            and region.kind in {"all", "exact"} and result_key is not None
                            and groups is not _UNKNOWN_SELECTOR and region.object_id is not None):
                        tests.append(_MarkerTest(
                            f"test:{site.id}", region.object_id, grouping, region, summary,
                            site.id, method, calibration, result_key, groups,
                        ))
                        summaries.append(summary.summary.binding)

    exact_test = tests[0] if len(tests) == 1 else None
    pvalue_claim = bool(
        exact_test is not None and exact_test.calibration == "naive"
        and reported_features is not None and _claims_pvalue(reported)
    )
    selection = (obs.get((exact_test.object_id, exact_test.grouping_field))
                 if exact_test is not None else None)
    test_producer = exact_test.producer if exact_test is not None else None
    selection_producer = selection.producer if selection is not None else None

    matching_egresses = [item for item in report_egresses
                         if report_relative_path is not None and item.path == report_relative_path]
    competing_report_write = bool(
        unknown_csv_write
        or (report_relative_path is not None
            and literal_csv_writes.count(report_relative_path) != 1)
    )
    exact_egress = (matching_egresses[0] if len(matching_egresses) == 1
                    and len(report_egresses) == 1 and not competing_report_write else None)
    egress_test_producer = exact_egress.producer if exact_egress is not None else None
    claim_root = "report:marker-pvalue"
    claim_program = _identity_program(
        claim_root,
        egress_test_producer if pvalue_claim and egress_test_producer == test_producer else None,
        "claim",
    )
    claim = ReportClaim("claim:marker-pvalue", claim_root, "pvalue",
                        ClaimRootGrade.ACCUSATION_GRADE,
                        bool(pvalue_claim and exact_test and exact_egress
                             and egress_test_producer == test_producer))
    claim_slice = slice_claim(claim_program, claim)

    grouping_root = (f"grouping:{exact_test.object_id}:{exact_test.grouping_field}"
                     if exact_test else "grouping:unknown")
    grouping_program = _identity_program(grouping_root, selection_producer, "grouping")
    grouping_claim = ReportClaim("claim:grouping", grouping_root, "grouping",
                                 ClaimRootGrade.ACCUSATION_GRADE, selection is not None)
    grouping_slice = slice_claim(grouping_program, grouping_claim)

    relations = {premise: "UNKNOWN" for premise in DOUBLE_DIPPING_PREMISES}
    sources_by_premise: dict[str, str] = {}
    if test_producer is not None and test_producer in claim_slice.unavoidable_producers:
        relations["ClaimMustProducedByTest"] = "PROVED"
        sources_by_premise["ClaimMustProducedByTest"] = "backward_must_slice:report_claim"
    if selection_producer is not None and selection_producer in grouping_slice.unavoidable_producers:
        relations["GroupingMustProducedBySelection"] = "PROVED"
        sources_by_premise["GroupingMustProducedBySelection"] = "backward_must_slice:grouping_field"
    if exact_test is not None:
        calibration = infer_calibration(
            contract_id=exact_test.summary.summary.binding.summary_digest,
            handling=exact_test.calibration,
            binding=exact_test.summary.summary.binding,
        )
        if any(isinstance(mode, Naive) for mode in calibration.modes.must):
            relations["TestDefinitelyNaive"] = "PROVED"
            sources_by_premise["TestDefinitelyNaive"] = "calibration:exact_sink_summary"
        relations["PinnedReachable"] = "PROVED"
        sources_by_premise["PinnedReachable"] = "cfg:unconditional_top_level_call"
    overlap = (_definite_overlap(selection.region, exact_test.region)
               if selection is not None and exact_test is not None else None)
    if overlap is True:
        relations["RelevantRegionOverlapDefinite"] = "PROVED"
        sources_by_premise["RelevantRegionOverlapDefinite"] = \
            "region:definite_feature_intersection"
        # The exact selection/test summaries jointly state that reusing the same expression object
        # under the marker null is dependent.  This rule is unavailable for external/unknown inputs.
        relations["SelectionReuseDependentUnderNull"] = "PROVED"
        sources_by_premise["SelectionReuseDependentUnderNull"] = \
            "selection_reuse:exact_shared_expression_contract"
    elif overlap is False:
        relations["RelevantRegionOverlapDefinite"] = "REFUTED"
        relations["SelectionReuseDependentUnderNull"] = "REFUTED"

    if len(tests) != 1:
        unknown_reasons.append("claim_has_zero_or_multiple_exact_marker_tests")
    if not pvalue_claim:
        unknown_reasons.append("report_has_no_pvalue_claim")
    if reported_features is None:
        unknown_reasons.append("report_feature_identity_unknown")
    if exact_test is not None and exact_test.calibration is None:
        unknown_reasons.append("marker_method_calibration_unknown")
    if exact_egress is None or egress_test_producer != test_producer:
        unknown_reasons.append("report_has_no_exact_test_egress")
    if competing_report_write:
        unknown_reasons.append("possible_report_overwrite")
    if exact_test is not None and selection is None:
        unknown_reasons.append("grouping_has_no_exact_must_selection_producer")
    if overlap is None:
        unknown_reasons.append("selection_test_overlap_unknown")

    egress_groups = ("all" if exact_egress is not None and exact_egress.groups is None
                     else ",".join(sorted(exact_egress.groups)) if exact_egress is not None
                     else "unknown")
    report_features_token = (",".join(sorted(reported_features))
                             if reported_features is not None else "unknown")
    producing_digest = (_digest("|".join((test_producer, selection_producer,
                                          exact_test.object_id, exact_test.grouping_field,
                                          exact_test.method or "unknown",
                                          exact_egress.result_key, egress_groups,
                                          report_features_token, exact_egress.callsite)))
                        if exact_test is not None and selection_producer is not None
                        and exact_egress is not None else None)
    inventory_complete = bool(
        pvalue_claim and len(tests) == 1 and claim_slice.coverage_complete
        and grouping_slice.coverage_complete
    )
    return DoubleDippingEvidence(
        relations,
        sources_by_premise,
        claim_slice,
        grouping_slice,
        tuple(dict.fromkeys(summaries)),
        test_producer,
        selection_producer,
        producing_digest,
        inventory_complete,
        tuple(dict.fromkeys(unknown_reasons)),
    )
