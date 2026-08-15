"""Untrusted bounded analyzer for the dependence growth-1 shadow.

The analyzer never executes authored code.  It proves a small hygienic inlining
grammar, recognizes one total list-bucket accumulation, and proposes a
certificate.  Frozen-byte group facts are attached only by
``discharge_dependence_growth_analysis``.
"""

from __future__ import annotations

import ast
import copy
import json
import posixpath
import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal, cast

from sc_referee.core.ids import semantic_digest
from sc_referee.dependence_recognition.ir import HumanMethodAuthorization
from sc_referee.dependence_recognition.python_analyzer import _trusted_authorizations
from sc_referee.dependence_recognition_v2.certificate import (
    verify_count_dependence_certificate,
    verify_dependence_growth_certificate,
)
from sc_referee.dependence_recognition_v2.count_domain import (
    prove_count_procedure_domain_with_reason,
)
from sc_referee.dependence_recognition_v2.csv_domain import (
    prove_group_value_sequences_with_reason,
)
from sc_referee.dependence_recognition_v2.ir import (
    MAX_V2_AST_NODES,
    MAX_V2_INLINE_DEPTH,
    MAX_V2_SOURCE_BYTES,
    AlphaRename,
    CastKind,
    CountDependenceCertificate,
    CountGroupDomainObligation,
    CountOperandObligation,
    CountPredicateAtom,
    CountProcedureObligation,
    CountSetProof,
    DependenceGrowthCertificate,
    DischargedGrowthAnalysis,
    GroupValueSequenceObligation,
    GrowthAnalysis,
    GrowthConclusion,
    OperandGroupBinding,
    VerifiedCountDependenceCertificate,
    require_registered_v2_reason,
)
from sc_referee.scientific_checks.core import FrozenInspectionContext

_REGISTERED = {
    "scipy.stats.ttest_ind": 2,
    "scipy.stats.mannwhitneyu": 2,
    "scipy.stats.binomtest": 2,
    "scipy.stats.fisher_exact": 1,
}
_COUNT_PROCEDURES = frozenset({"scipy.stats.binomtest", "scipy.stats.fisher_exact"})
_BUILTINS = frozenset(
    {
        "list",
        "set",
        "float",
        "int",
        "sorted",
        "str",
        "len",
        "min",
        "max",
        "sum",
        "round",
        "abs",
        "range",
        "enumerate",
    }
)
_SCIPY_PIN = re.compile(r"(?m)^\s*scipy\s*==\s*1\.14\.0\s*(?:#.*)?$")
ModuleConstant = ast.Constant | ast.Tuple | ast.Dict


class _Refusal(Exception):
    def __init__(self, *reasons: str) -> None:
        self.reasons = tuple(require_registered_v2_reason(reason) for reason in reasons)


@dataclass(frozen=True)
class _CountDomain:
    kind: str
    atoms: tuple[CountPredicateAtom, ...]
    depth: int = 0


@dataclass(frozen=True)
class _CountDerivation:
    name: str
    domain: _CountDomain
    predicates: tuple[CountPredicateAtom, ...]
    node: ast.AST


def analyze_dependence_growth_python(context: FrozenInspectionContext) -> GrowthAnalysis:
    """Propose one growth certificate or return granular sorted abstentions."""

    reasons: set[str] = set()
    documents = [item for item in context.documents if item.media_type == "text/x-python"]
    if len(documents) != 1:
        return _unsupported("single-python-module-required")
    document = documents[0]
    if len(document.content) > MAX_V2_SOURCE_BYTES:
        return _unsupported("source-byte-ceiling")
    constants: dict[str, ModuleConstant] = {}
    try:
        source = document.content.decode("utf-8", errors="strict")
        tree = ast.parse(source)
    except (UnicodeDecodeError, SyntaxError, ValueError, RecursionError):
        return _unsupported("python-parse-unsupported")
    if sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return _unsupported("ast-node-ceiling")

    authorities = _trusted_v2_authorizations(context)
    if len(authorities) != 1:
        return GrowthAnalysis(
            state="question",
            certificate=None,
            obligation=None,
            abstention_reasons=(),
            candidate_key_columns=_candidate_columns(context),
            basis="Exactly one trusted independent-unit authorization was unavailable.",
        )
    authority = authorities[0]
    if len(authority.authorized_key_columns) != 1:
        return _unsupported("authorized-composite-unit-key-unsupported")
    material_matches = [
        item
        for item in context.material_inputs
        if item.path == authority.input_path
        and item.content_digest == authority.input_content_digest
    ]
    if len(material_matches) != 1:
        return _unsupported("authority-material-binding-mismatch")
    if not _scipy_is_pinned(context):
        return _unsupported("procedure-version-unpinned")

    try:
        imports, constants, functions, executable = _module_parts(tree)
        _validate_import_uses(tree, imports, constants)
        _validate_module_collection_uses(tree, constants)
        if _module_string_alternative_used(tree, imports, constants):
            raise _Refusal("procedure-alternative-not-default")
        flattened, renames, dead = _flatten_functions(executable, functions, constants, imports)
        flattened = _normalize_live_annotations(flattened, imports)
        _refuse_unsupported_live_assignment_syntax(flattened)
        if _core_construct_is_conditionally_wrapped(flattened, imports):
            raise _Refusal("sink-controls-operand-flow")
    except _Refusal as refusal:
        reasons.update(refusal.reasons)
        # Report composition and multi-site are independently useful fuel.
        reasons.update(_independent_wall_scan(tree, constants))
        return _unsupported(*reasons)

    reasons.update(_independent_wall_scan(tree, constants))
    if _count_procedure_present(flattened, imports):
        try:
            proposal = _analyze_count_proposal(
                document_path=document.path,
                document_digest=document.content_digest,
                source_length=len(document.content),
                body=flattened,
                imports=imports,
                constants=constants,
                authority=authority,
                renames=tuple(renames),
                dead=tuple(sorted(dead)),
                expected_result_path=_trusted_result_path(context),
            )
        except _Refusal as refusal:
            reasons.update(refusal.reasons)
            return _unsupported(*reasons)
        if reasons:
            return _unsupported(*reasons)
        return proposal
    try:
        read = _recognize_reader(flattened, constants)
        grouping = _recognize_grouping(flattened, read[0], constants)
        procedure = _recognize_procedure(flattened, imports, grouping[0], constants, grouping[5])
        sink = _recognize_sink(flattened, procedure[2], constants, _trusted_result_path(context))
        operand_tokens, sink_tokens = _verify_closed_flattened_statements(
            flattened,
            rows_name=read[0],
            group_name=grouping[0],
            result_name=procedure[2],
            sink=sink,
        )
    except _Refusal as refusal:
        reasons.update(refusal.reasons)
        return _unsupported(*reasons)
    if reasons:
        return _unsupported(*reasons)

    group_name, key_column, value_column, cast_kind, bucket_keys, container_kind = grouping
    if key_column == value_column:
        return _unsupported("group-key-equals-value-column")
    if key_column == authority.authorized_key_columns[0]:
        return _unsupported("group-key-is-unit-column")
    resolved_callable, argument_bindings, result_name, call_node = procedure
    obligation = GroupValueSequenceObligation(
        path=read[1],
        content_digest=authority.input_content_digest,
        line_model=read[3],
        reader_form=read[4],
        encoding=read[2],
        authorized_unit_column=authority.authorized_key_columns[0],
        group_key_column=key_column,
        value_column=value_column,
        cast_kind=cast(CastKind, cast_kind),
        predeclared_bucket_keys=bucket_keys,
    )
    placeholder_conclusion: GrowthConclusion = "one_observation_per_unit"
    certificate = DependenceGrowthCertificate(
        certificate_id="pending-controller-domain-proof",
        source_path=document.path,
        source_digest=document.content_digest,
        source_extent=(0, len(document.content)),
        analysis_target_ref=authority.analysis_target_ref,
        procedure_ref=authority.procedure_ref,
        authority_record_id=authority.record_id,
        independent_unit_definition_id=authority.independent_unit_definition_id,
        obligation=obligation,
        resolved_callable=resolved_callable,
        procedure_call_token=_node_token(document.path, call_node, "procedure-call"),
        result_name=result_name,
        sink_token=_node_token(document.path, sink, "selected-sink"),
        group_container_name=group_name,
        group_container_kind=container_kind,
        operand_bindings=argument_bindings,
        alpha_renames=tuple(renames),
        dead_syntactic_construct_tokens=tuple(sorted(dead)),
        operand_slice_statement_tokens=operand_tokens,
        sink_bound_statement_tokens=sink_tokens,
        conclusion=placeholder_conclusion,
    )
    return GrowthAnalysis(
        state="proposal",
        certificate=certificate,
        obligation=obligation,
        abstention_reasons=(),
        candidate_key_columns=authority.authorized_key_columns,
        basis="The bounded module, inlining, grouping, procedure, and sink grammar proposed a proof.",
    )


def discharge_dependence_growth_analysis(
    analysis: GrowthAnalysis, context: FrozenInspectionContext
) -> DischargedGrowthAnalysis:
    """Attach a frozen-byte fact, resolve group positions, and invoke the kernel."""

    if analysis.state != "proposal" or analysis.certificate is None or analysis.obligation is None:
        return DischargedGrowthAnalysis(
            state=cast(Any, analysis.state),
            verified_certificate=None,
            abstention_reasons=analysis.abstention_reasons,
            candidate_key_columns=analysis.candidate_key_columns,
            basis=analysis.basis,
        )
    certificate = analysis.certificate
    if isinstance(certificate, CountDependenceCertificate):
        return _discharge_count_analysis(analysis, certificate, context)
    assert isinstance(certificate, DependenceGrowthCertificate)
    assert isinstance(analysis.obligation, GroupValueSequenceObligation)
    materials = [
        item
        for item in context.material_inputs
        if item.path == analysis.obligation.path
        and item.content_digest == analysis.obligation.content_digest
    ]
    if len(materials) != 1:
        return _discharged_unsupported("group-domain-binding-mismatch")
    fact, reason = prove_group_value_sequences_with_reason(
        materials[0], obligation=analysis.obligation
    )
    if fact is None:
        return _discharged_unsupported(reason or "group-domain-unproven")
    keys = tuple(item.group_key for item in fact.groups)
    if certificate.group_container_kind == "defaultdict_list" and any(
        not item.group_key.startswith("__sorted_group_position_") and item.group_key not in keys
        for item in certificate.operand_bindings
    ):
        return _discharged_unsupported("defaultdict-key-not-proven")
    if len(fact.groups) != _REGISTERED[certificate.resolved_callable]:
        return _discharged_unsupported("group-operand-arity-mismatch")
    resolved_bindings: list[OperandGroupBinding] = []
    for binding in certificate.operand_bindings:
        key = binding.group_key
        if key.startswith("__sorted_group_position_"):
            position = int(key.removeprefix("__sorted_group_position_"))
            if position >= len(keys):
                return _discharged_unsupported("group-operand-arity-mismatch")
            key = keys[position]
        resolved_bindings.append(replace(binding, group_key=key))
    if len({item.group_key for item in resolved_bindings}) != len(resolved_bindings) or {
        item.group_key for item in resolved_bindings
    } != set(keys):
        return _discharged_unsupported("group-operand-arity-mismatch")

    unit_positions: dict[str, set[int]] = {}
    repeated: set[str] = set()
    by_key = {item.group_key: item for item in fact.groups}
    for binding in resolved_bindings:
        counts = Counter(by_key[binding.group_key].authorized_unit_ids)
        repeated.update(unit for unit, count in counts.items() if count > 1)
        for unit in counts:
            unit_positions.setdefault(unit, set()).add(binding.position)
    if any(len(positions) > 1 for positions in unit_positions.values()):
        return _discharged_unsupported("unit-spans-multiple-operands")
    conclusion: GrowthConclusion = "repeated_units" if repeated else "one_observation_per_unit"
    certificate = replace(
        certificate,
        operand_bindings=tuple(resolved_bindings),
        conclusion=conclusion,
    )
    certificate = replace(
        certificate,
        certificate_id=f"dependence-growth-certificate:{semantic_digest({'source_digest': certificate.source_digest, 'fact': fact.evidence_id, 'bindings': [asdict(item) for item in certificate.operand_bindings], 'conclusion': conclusion})}",
    )
    source_matches = [
        item
        for item in context.documents
        if item.path == certificate.source_path and item.content_digest == certificate.source_digest
    ]
    if len(source_matches) != 1:
        return _discharged_unsupported("source-binding-mismatch")
    kernel_failures: list[str] = []
    verified = verify_dependence_growth_certificate(
        certificate,
        trusted_group_facts=(fact,),
        trusted_authorizations=_trusted_v2_authorizations(context),
        source_bytes=source_matches[0].content,
        _failure_reasons=kernel_failures,
    )
    if verified is None:
        obligation = kernel_failures[0] if len(kernel_failures) == 1 else "unspecified"
        return _discharged_unsupported(f"certificate-kernel-refusal:{obligation}")
    return DischargedGrowthAnalysis(
        state="verified",
        verified_certificate=verified,
        abstention_reasons=(),
        candidate_key_columns=analysis.candidate_key_columns,
        basis="The trusted group fact and growth certificate kernel discharged every equation.",
    )


def _count_procedure_present(body: list[ast.stmt], imports: dict[str, str]) -> bool:
    return any(
        isinstance(node, ast.Call) and _resolved_procedure(node.func, imports) in _COUNT_PROCEDURES
        for statement in body
        for node in ast.walk(statement)
    )


def _core_construct_is_conditionally_wrapped(body: list[ast.stmt], imports: dict[str, str]) -> bool:
    """Reject control parents around reader, accumulation, procedure, or sink."""

    for statement in body:
        if not isinstance(statement, ast.If | ast.While | ast.Try | ast.Match):
            continue
        for node in ast.walk(statement):
            if node is statement:
                continue
            if isinstance(node, ast.With | ast.For):
                return True
            if isinstance(node, ast.Call):
                if _resolved_procedure(node.func, imports) in _REGISTERED:
                    return True
                if isinstance(node.func, ast.Attribute) and node.func.attr in {
                    "DictReader",
                    "write_text",
                }:
                    return True
    return False


def _refuse_unsupported_live_assignment_syntax(body: list[ast.stmt]) -> None:
    """Name every statement form excluded by both certified v2 paths."""

    nodes = tuple(node for statement in body for node in ast.walk(statement))
    if any(isinstance(node, ast.AnnAssign) for node in nodes):
        raise _Refusal("annotated-assignment-not-modeled")
    if any(isinstance(node, ast.AugAssign) for node in nodes):
        raise _Refusal("augmented-assignment-not-modeled")
    if any(isinstance(node, ast.NamedExpr) for node in nodes):
        raise _Refusal("named-expression-not-modeled")
    if any(isinstance(node, ast.Delete) for node in nodes):
        raise _Refusal("delete-not-modeled")


def _normalize_live_annotations(body: list[ast.stmt], imports: dict[str, str]) -> list[ast.stmt]:
    """Lower only annotations proven outside the existing operand partition."""

    procedures = [
        node
        for statement in body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call) and _resolved_procedure(node.func, imports) in _REGISTERED
    ]
    operand_names = {
        node.id
        for call in procedures
        for argument in call.args
        for node in ast.walk(argument)
        if isinstance(node, ast.Name)
    }
    definitions: dict[str, ast.expr] = {}
    for statement in body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            definitions[statement.targets[0].id] = statement.value
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            definitions.setdefault(statement.target.id, statement.value)
    changed = True
    while changed:
        changed = False
        for name in tuple(operand_names):
            value = definitions.get(name)
            if value is None:
                continue
            for node in ast.walk(value):
                if isinstance(node, ast.Name) and node.id not in operand_names:
                    operand_names.add(node.id)
                    changed = True
        for name, value in definitions.items():
            if (
                isinstance(value, ast.Name)
                and value.id in operand_names
                and name not in operand_names
            ):
                operand_names.add(name)
                changed = True
    normalized: list[ast.stmt] = []
    for statement in body:
        if not isinstance(statement, ast.AnnAssign):
            normalized.append(statement)
            continue
        if not isinstance(statement.target, ast.Name):
            raise _Refusal("annotated-assignment-not-modeled")
        if statement.value is None:
            continue
        if statement.target.id in operand_names:
            raise _Refusal("annotated-assignment-not-modeled")
        normalized.append(
            ast.copy_location(
                ast.Assign(targets=[copy.deepcopy(statement.target)], value=statement.value),
                statement,
            )
        )
    return normalized


def _trusted_v2_authorizations(
    context: FrozenInspectionContext,
) -> tuple[HumanMethodAuthorization, ...]:
    """Select the distinct v2 lock line without accepting arbitrary extra authority."""

    authorities = _trusted_authorizations(context)
    return tuple(item for item in authorities if item.record_id.startswith("authorization-v2:"))


def _trusted_result_path(context: FrozenInspectionContext) -> str | None:
    paths: list[tuple[str, str]] = []
    for record in context.base_records:
        if record.ref.record_type != "result":
            continue
        try:
            value = json.loads(record.canonical_payload)
        except (TypeError, ValueError):
            return None
        if isinstance(value, dict) and isinstance(value.get("path"), str):
            paths.append((record.ref.record_id, value["path"]))
    v2_paths = [path for record_id, path in paths if record_id.startswith("result-v2:")]
    if v2_paths:
        return v2_paths[0] if len(v2_paths) == 1 else None
    return paths[0][1] if len(paths) == 1 else None


def _analyze_count_proposal(
    *,
    document_path: str,
    document_digest: str,
    source_length: int,
    body: list[ast.stmt],
    imports: dict[str, str],
    constants: dict[str, ModuleConstant],
    authority: HumanMethodAuthorization,
    renames: tuple[AlphaRename, ...],
    dead: tuple[str, ...],
    expected_result_path: str | None,
) -> GrowthAnalysis:
    read = _recognize_reader(body, constants)
    rows_name = read[0]
    domains, group_domains = _count_row_domains(body, rows_name, constants)
    derivations = _count_derivations(body, domains, constants)
    matches = [
        (statement, statement.value, _resolved_procedure(statement.value.func, imports))
        for statement in body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, ast.Call)
        and _resolved_procedure(statement.value.func, imports) in _COUNT_PROCEDURES
    ]
    if len(matches) != 1:
        raise _Refusal("procedure-call-unresolved")
    statement, call, resolved_value = matches[0]
    assert isinstance(statement.targets[0], ast.Name)
    assert isinstance(resolved_value, str)
    resolved = cast(Literal["scipy.stats.binomtest", "scipy.stats.fisher_exact"], resolved_value)
    operands = _count_call_operands(call, resolved, derivations, body)
    result_name = statement.targets[0].id
    sink = _recognize_sink(body, result_name, constants, expected_result_path)
    operand_tokens, sink_tokens = _verify_closed_count_statements(
        body,
        rows_name=rows_name,
        domains=domains,
        derivations=derivations,
        procedure_statement=statement,
        sink=sink,
        constants=constants,
    )
    obligation = CountProcedureObligation(
        path=read[1],
        content_digest=authority.input_content_digest,
        line_model=read[3],
        reader_form=read[4],
        encoding=read[2],
        result_path=cast(str, expected_result_path),
        authorized_unit_column=authority.authorized_key_columns[0],
        resolved_callable=resolved,
        operands=operands,
        universe_atoms=_count_universe_atoms(operands, resolved),
        group_domains=group_domains,
    )
    certificate = CountDependenceCertificate(
        certificate_id="pending-controller-domain-proof",
        source_path=document_path,
        source_digest=document_digest,
        source_extent=(0, source_length),
        analysis_target_ref=authority.analysis_target_ref,
        procedure_ref=authority.procedure_ref,
        authority_record_id=authority.record_id,
        independent_unit_definition_id=authority.independent_unit_definition_id,
        obligation=obligation,
        resolved_callable=resolved,
        procedure_call_token=_node_token(document_path, call, "procedure-call"),
        result_name=result_name,
        sink_token=_node_token(document_path, sink, "selected-sink"),
        alpha_renames=renames,
        dead_syntactic_construct_tokens=dead,
        operand_slice_statement_tokens=operand_tokens,
        sink_bound_statement_tokens=sink_tokens,
        conclusion="one_observation_per_unit",
    )
    return GrowthAnalysis(
        state="proposal",
        certificate=certificate,
        obligation=obligation,
        abstention_reasons=(),
        candidate_key_columns=authority.authorized_key_columns,
        basis="The bounded growth-2 symbolic count grammar proposed a frozen-row proof.",
    )


def _count_row_domains(
    body: list[ast.stmt], rows_name: str, constants: dict[str, ModuleConstant]
) -> tuple[dict[str, _CountDomain], tuple[CountGroupDomainObligation, ...]]:
    domains: dict[str, _CountDomain] = {rows_name: _CountDomain("rows", ())}
    group_domains: list[CountGroupDomainObligation] = []
    for statement in body:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.ListComp)
        ):
            continue
        comprehension = statement.value
        if (
            len(comprehension.generators) != 1
            or comprehension.generators[0].is_async
            or len(comprehension.generators[0].ifs) != 1
            or not isinstance(comprehension.generators[0].target, ast.Name)
            or not isinstance(comprehension.elt, ast.Name)
            or comprehension.elt.id != comprehension.generators[0].target.id
        ):
            raise _Refusal("count-domain-not-row-bound")
        source = _count_domain_expression(comprehension.generators[0].iter, domains, constants)
        if source is None or source.depth != 0:
            raise _Refusal("count-domain-not-row-bound")
        atoms = _count_predicate(
            comprehension.generators[0].ifs[0], comprehension.generators[0].target.id
        )
        domains[statement.targets[0].id] = _CountDomain("filtered_rows", (*source.atoms, *atoms), 1)

    group_loops = [
        statement
        for statement in body
        if isinstance(statement, ast.For)
        and isinstance(statement.iter, ast.Name)
        and statement.iter.id == rows_name
        and isinstance(statement.target, ast.Name)
        and len(statement.body) == 1
        and isinstance(statement.body[0], ast.Expr)
        and isinstance(statement.body[0].value, ast.Call)
        and isinstance(statement.body[0].value.func, ast.Attribute)
        and statement.body[0].value.func.attr == "append"
    ]
    for loop in group_loops:
        call = cast(ast.Call, cast(ast.Expr, loop.body[0]).value)
        row_name = cast(ast.Name, loop.target).id
        if (
            len(call.args) != 1
            or call.keywords
            or not isinstance(call.args[0], ast.Name)
            or call.args[0].id != row_name
            or not isinstance(call.func, ast.Attribute)
            or not isinstance(call.func.value, ast.Subscript)
            or not isinstance(call.func.value.value, ast.Name)
        ):
            continue
        group_name = call.func.value.value.id
        column = _row_subscript(call.func.value.slice, row_name)
        if column is None:
            raise _Refusal("count-domain-not-row-bound")
        declarations = [
            item.value
            for item in body
            if isinstance(item, ast.Assign)
            and len(item.targets) == 1
            and isinstance(item.targets[0], ast.Name)
            and item.targets[0].id == group_name
            and isinstance(item.value, ast.Dict)
            and item.value.keys
            and all(
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and isinstance(value, ast.List)
                and not value.elts
                for key, value in zip(item.value.keys, item.value.values, strict=True)
            )
        ]
        if len(declarations) != 1:
            raise _Refusal("count-domain-not-row-bound")
        domains[f"__group__:{group_name}:{column}"] = _CountDomain("group_rows", ())
        declaration = declarations[0]
        assert isinstance(declaration, ast.Dict)
        group_domains.append(
            CountGroupDomainObligation(
                group_key_column=column,
                predeclared_bucket_keys=tuple(
                    cast(str, cast(ast.Constant, key).value) for key in declaration.keys
                ),
            )
        )
    return domains, tuple(sorted(group_domains))


def _count_domain_expression(
    expression: ast.expr,
    domains: dict[str, _CountDomain],
    constants: dict[str, ModuleConstant],
) -> _CountDomain | None:
    if isinstance(expression, ast.Name):
        return domains.get(expression.id)
    if isinstance(expression, ast.Subscript) and isinstance(expression.value, ast.Name):
        key = _constant_string(expression.slice, constants)
        candidates = [
            (token, domain)
            for token, domain in domains.items()
            if token.startswith(f"__group__:{expression.value.id}:")
        ]
        if key is None or len(candidates) != 1:
            return None
        token, domain = candidates[0]
        column = token.rsplit(":", 1)[1]
        return _CountDomain(
            domain.kind,
            (CountPredicateAtom(column=column, operator="eq", literal=key),),
        )
    return None


def _count_derivations(
    body: list[ast.stmt],
    domains: dict[str, _CountDomain],
    constants: dict[str, ModuleConstant],
) -> dict[str, _CountDerivation]:
    derivations: dict[str, _CountDerivation] = {}
    for statement in body:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            continue
        name = statement.targets[0].id
        derived = _count_expression(statement.value, name, domains, constants)
        if derived is not None:
            derivations[name] = replace(derived, node=statement)

    increment_sites: dict[str, list[ast.AugAssign]] = {}
    for statement in body:
        if not isinstance(statement, ast.For):
            continue
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.AugAssign)
                and isinstance(node.target, ast.Name)
                and isinstance(node.op, ast.Add)
            ):
                increment_sites.setdefault(node.target.id, []).append(node)
    if any(len(sites) > 1 for sites in increment_sites.values()):
        raise _Refusal("count-multiple-increment-sites")
    for name, sites in increment_sites.items():
        initializers = [
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
            and isinstance(statement.value, ast.Constant)
            and type(statement.value.value) is int
            and statement.value.value == 0
        ]
        loop = next(
            (
                statement
                for statement in body
                if isinstance(statement, ast.For) and sites[0] in set(ast.walk(statement))
            ),
            None,
        )
        if len(initializers) != 1 or loop is None:
            raise _Refusal("count-increment-not-total")
        derived = _count_increment_loop(name, loop, domains, constants)
        derivations[name] = replace(derived, node=loop)
    return derivations


def _count_expression(
    expression: ast.expr,
    name: str,
    domains: dict[str, _CountDomain],
    constants: dict[str, ModuleConstant],
) -> _CountDerivation | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "len"
        and len(expression.args) == 1
        and not expression.keywords
    ):
        domain = _count_domain_expression(expression.args[0], domains, constants)
        if domain is None:
            raise _Refusal("count-domain-not-row-bound")
        return _CountDerivation(name, domain, (), expression)
    if not (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "sum"
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.GeneratorExp)
    ):
        return None
    generator = expression.args[0]
    if (
        not isinstance(generator.elt, ast.Constant)
        or type(generator.elt.value) is not int
        or generator.elt.value != 1
        or len(generator.generators) != 1
        or generator.generators[0].is_async
        or len(generator.generators[0].ifs) > 1
        or not isinstance(generator.generators[0].target, ast.Name)
    ):
        raise _Refusal("count-increment-not-total")
    domain = _count_domain_expression(generator.generators[0].iter, domains, constants)
    if domain is None:
        raise _Refusal("count-domain-not-row-bound")
    predicates = (
        _count_predicate(generator.generators[0].ifs[0], generator.generators[0].target.id)
        if generator.generators[0].ifs
        else ()
    )
    return _CountDerivation(name, domain, predicates, expression)


def _count_increment_loop(
    name: str,
    loop: ast.For,
    domains: dict[str, _CountDomain],
    constants: dict[str, ModuleConstant],
) -> _CountDerivation:
    if (
        loop.orelse
        or not isinstance(loop.target, ast.Name)
        or len(loop.body) != 1
        or not isinstance(loop.body[0], ast.If)
        or loop.body[0].orelse
        or len(loop.body[0].body) != 1
        or not isinstance(loop.body[0].body[0], ast.AugAssign)
    ):
        raise _Refusal("count-increment-not-total")
    increment = loop.body[0].body[0]
    if not (
        isinstance(increment.target, ast.Name)
        and increment.target.id == name
        and isinstance(increment.op, ast.Add)
        and isinstance(increment.value, ast.Constant)
        and type(increment.value.value) is int
        and increment.value.value == 1
    ):
        raise _Refusal("count-increment-not-total")
    domain = _count_domain_expression(loop.iter, domains, constants)
    if domain is None:
        raise _Refusal("count-domain-not-row-bound")
    return _CountDerivation(
        name,
        domain,
        _count_predicate(loop.body[0].test, loop.target.id),
        loop,
    )


def _count_predicate(expression: ast.expr, row_name: str) -> tuple[CountPredicateAtom, ...]:
    parts = (
        expression.values
        if isinstance(expression, ast.BoolOp) and isinstance(expression.op, ast.And)
        else [expression]
    )
    atoms: list[CountPredicateAtom] = []
    for part in parts:
        if not (
            isinstance(part, ast.Compare)
            and len(part.ops) == len(part.comparators) == 1
            and isinstance(part.ops[0], ast.Eq | ast.NotEq)
        ):
            raise _Refusal("count-predicate-not-closed")
        column = _row_subscript(part.left, row_name)
        literal = part.comparators[0]
        if column is None:
            raise _Refusal("count-predicate-not-closed")
        if not isinstance(literal, ast.Constant) or not isinstance(literal.value, str):
            if isinstance(literal, ast.Constant):
                raise _Refusal("count-predicate-literal-not-string")
            raise _Refusal("count-predicate-not-closed")
        atoms.append(
            CountPredicateAtom(
                column=column,
                operator="eq" if isinstance(part.ops[0], ast.Eq) else "ne",
                literal=literal.value,
            )
        )
    return tuple(atoms)


def _count_call_operands(
    call: ast.Call,
    resolved: Literal["scipy.stats.binomtest", "scipy.stats.fisher_exact"],
    derivations: dict[str, _CountDerivation],
    body: list[ast.stmt],
) -> tuple[CountOperandObligation, ...]:
    keywords = {item.arg: item.value for item in call.keywords if item.arg is not None}
    if len(keywords) != len(call.keywords):
        raise _Refusal("procedure-call-unresolved")
    alternative = keywords.pop("alternative", None)
    if alternative is not None and not (
        isinstance(alternative, ast.Constant) and alternative.value == "two-sided"
    ):
        raise _Refusal("procedure-alternative-not-default")
    if resolved == "scipy.stats.binomtest":
        if len(call.args) not in {2, 3} or set(keywords) - {"p"}:
            raise _Refusal("procedure-call-unresolved")
        if len(call.args) == 3 and "p" in keywords:
            raise _Refusal("procedure-call-unresolved")
        p_value = call.args[2] if len(call.args) == 3 else keywords.get("p")
        if p_value is not None and not _numeric_constant(p_value):
            raise _Refusal("procedure-call-unresolved")
        expressions = call.args[:2]
    else:
        if len(call.args) != 1 or keywords:
            raise _Refusal("procedure-call-unresolved")
        table = call.args[0]
        if isinstance(table, ast.Name):
            assignments = [
                statement.value
                for statement in body
                if isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == table.id
            ]
            table = assignments[0] if len(assignments) == 1 else table
        if not (
            isinstance(table, ast.List)
            and len(table.elts) == 2
            and all(isinstance(row, ast.List) and len(row.elts) == 2 for row in table.elts)
        ):
            raise _Refusal("count-cells-not-partition")
        expressions = [cell for row in table.elts if isinstance(row, ast.List) for cell in row.elts]
    operands: list[CountOperandObligation] = []
    for position, expression in enumerate(expressions):
        if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Sub):
            raise _Refusal("count-cell-derived-by-arithmetic")
        if not isinstance(expression, ast.Name) or expression.id not in derivations:
            raise _Refusal("count-domain-not-row-bound")
        derivation = derivations[expression.id]
        operands.append(
            CountOperandObligation(
                operand_id=expression.id,
                position=position,
                domain_kind=cast(Any, derivation.domain.kind),
                domain_atoms=derivation.domain.atoms,
                predicate_atoms=derivation.predicates,
            )
        )
    return tuple(operands)


def _count_universe_atoms(
    operands: tuple[CountOperandObligation, ...],
    resolved: Literal["scipy.stats.binomtest", "scipy.stats.fisher_exact"],
) -> tuple[CountPredicateAtom, ...]:
    if resolved == "scipy.stats.binomtest":
        return operands[1].domain_atoms
    common = set(operands[0].domain_atoms)
    for operand in operands[1:]:
        common.intersection_update(operand.domain_atoms)
    return tuple(atom for atom in operands[0].domain_atoms if atom in common)


def _numeric_constant(expression: ast.expr) -> bool:
    return isinstance(expression, ast.Constant) and type(expression.value) in {int, float}


def _constant_string(expression: ast.expr, constants: dict[str, ModuleConstant]) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.Name) and isinstance(constants.get(expression.id), ast.Constant):
        value = cast(ast.Constant, constants[expression.id]).value
        return value if isinstance(value, str) else None
    return None


def _verify_closed_count_statements(
    body: list[ast.stmt],
    *,
    rows_name: str,
    domains: dict[str, _CountDomain],
    derivations: dict[str, _CountDerivation],
    procedure_statement: ast.Assign,
    sink: ast.Call,
    constants: dict[str, ModuleConstant],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    group_loops = [
        statement for statement in body if _closed_count_group_loop(statement, rows_name, domains)
    ]
    if len(group_loops) != len(
        {ast.dump(statement, include_attributes=False) for statement in group_loops}
    ):
        raise _Refusal("count-multiple-increment-sites")
    operand_names = {rows_name, *domains, *derivations}
    for node in ast.walk(procedure_statement.value):
        if isinstance(node, ast.Name):
            operand_names.add(node.id)
    return _partition_sink_bound(body, procedure_statement, sink, operand_names)


def _closed_count_group_loop(
    statement: ast.stmt, rows_name: str, domains: dict[str, _CountDomain]
) -> bool:
    if not (
        isinstance(statement, ast.For)
        and isinstance(statement.target, ast.Name)
        and isinstance(statement.iter, ast.Name)
        and statement.iter.id == rows_name
        and not statement.orelse
        and len(statement.body) == 1
        and isinstance(statement.body[0], ast.Expr)
        and isinstance(statement.body[0].value, ast.Call)
    ):
        return False
    call = statement.body[0].value
    return bool(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "append"
        and len(call.args) == 1
        and not call.keywords
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id == statement.target.id
        and isinstance(call.func.value, ast.Subscript)
        and isinstance(call.func.value.value, ast.Name)
        and (column := _row_subscript(call.func.value.slice, statement.target.id)) is not None
        and f"__group__:{call.func.value.value.id}:{column}" in domains
    )


def _unmodeled_statement_kind(statement: ast.stmt) -> str:
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
        return "attribute-call" if isinstance(statement.value.func, ast.Attribute) else "name-call"
    if isinstance(statement, ast.Assign):
        return "alias-assignment" if isinstance(statement.value, ast.Name) else "assignment"
    return "statement"


def _discharge_count_analysis(
    analysis: GrowthAnalysis,
    certificate: CountDependenceCertificate,
    context: FrozenInspectionContext,
) -> DischargedGrowthAnalysis:
    obligation = certificate.obligation
    materials = [
        item
        for item in context.material_inputs
        if item.path == obligation.path and item.content_digest == obligation.content_digest
    ]
    if len(materials) != 1:
        return _discharged_unsupported("group-domain-binding-mismatch")
    fact, reason = prove_count_procedure_domain_with_reason(materials[0], obligation=obligation)
    if fact is None:
        return _discharged_unsupported(reason or "group-domain-unproven")
    by_position = {item.position: item for item in fact.operands}
    relevant: tuple[CountSetProof, ...]
    if certificate.resolved_callable == "scipy.stats.binomtest":
        if any(not operand.row_indices for operand in fact.operands):
            return _discharged_unsupported("count-set-degenerate")
        if not set(by_position[0].row_indices) <= set(by_position[1].row_indices):
            return _discharged_unsupported("count-success-not-subset")
        relevant = (by_position[1],)
    else:
        if not fact.universe_row_indices:
            return _discharged_unsupported("count-set-degenerate")
        sets = [set(by_position[position].row_indices) for position in range(4)]
        if any(
            left & right for index, left in enumerate(sets) for right in sets[index + 1 :]
        ) or set().union(*sets) != set(fact.universe_row_indices):
            return _discharged_unsupported("count-cells-not-partition")
        if not _fisher_operands_are_factorial(certificate.obligation.operands):
            return _discharged_unsupported("count-cells-not-factorial")
        unit_cells: dict[str, set[int]] = {}
        for proof in fact.operands:
            for unit in proof.authorized_unit_ids:
                unit_cells.setdefault(unit, set()).add(proof.position)
        if any(len(cells) > 1 for cells in unit_cells.values()):
            return _discharged_unsupported("unit-spans-multiple-cells")
        relevant = tuple(fact.operands)
    repeated = {
        unit
        for proof in relevant
        for unit, count in Counter(proof.authorized_unit_ids).items()
        if count > 1
    }
    conclusion: GrowthConclusion = "repeated_units" if repeated else "one_observation_per_unit"
    certificate = replace(certificate, conclusion=conclusion)
    certificate = replace(
        certificate,
        certificate_id=(
            "dependence-growth-count-certificate:"
            + semantic_digest(
                {
                    "source_digest": certificate.source_digest,
                    "fact": fact.evidence_id,
                    "procedure": certificate.resolved_callable,
                    "conclusion": conclusion,
                }
            )
        ),
    )
    source_matches = [
        item
        for item in context.documents
        if item.path == certificate.source_path and item.content_digest == certificate.source_digest
    ]
    if len(source_matches) != 1:
        return _discharged_unsupported("source-binding-mismatch")
    failures: list[str] = []
    verified = verify_count_dependence_certificate(
        certificate,
        trusted_count_facts=(fact,),
        trusted_authorizations=_trusted_v2_authorizations(context),
        source_bytes=source_matches[0].content,
        _failure_reasons=failures,
    )
    if verified is None:
        obligation_name = failures[0] if len(failures) == 1 else "unspecified"
        return _discharged_unsupported(f"certificate-kernel-refusal:{obligation_name}")
    assert isinstance(verified, VerifiedCountDependenceCertificate)
    return DischargedGrowthAnalysis(
        state="verified",
        verified_certificate=verified,
        abstention_reasons=(),
        candidate_key_columns=analysis.candidate_key_columns,
        basis="The trusted count fact and growth-2 kernel discharged every symbolic equation.",
    )


def _fisher_operands_are_factorial(
    operands: tuple[CountOperandObligation, ...],
) -> bool:
    """Check the exact two-column, two-level product from predicate atoms only."""

    if len(operands) != 4:
        return False
    combinations: set[tuple[tuple[str, str], ...]] = set()
    values_by_column: dict[str, set[str]] = {}
    for operand in operands:
        atoms = operand.predicate_atoms
        if (
            len(atoms) != 2
            or any(atom.operator != "eq" for atom in atoms)
            or len({atom.column for atom in atoms}) != 2
        ):
            return False
        combination = tuple(sorted((atom.column, atom.literal) for atom in atoms))
        combinations.add(combination)
        for column, literal in combination:
            values_by_column.setdefault(column, set()).add(literal)
    if len(values_by_column) != 2 or any(len(values) != 2 for values in values_by_column.values()):
        return False
    columns = tuple(sorted(values_by_column))
    expected = {
        tuple(sorted(((columns[0], left), (columns[1], right))))
        for left in values_by_column[columns[0]]
        for right in values_by_column[columns[1]]
    }
    return len(combinations) == 4 and combinations == expected


def _module_parts(
    tree: ast.Module,
) -> tuple[dict[str, str], dict[str, ModuleConstant], dict[str, ast.FunctionDef], list[ast.stmt]]:
    imports: dict[str, str] = {}
    constants: dict[str, ModuleConstant] = {}
    functions: dict[str, ast.FunctionDef] = {}
    executable: list[ast.stmt] = []
    for statement in _live_main_guard_body(_without_leading_docstring(tree.body)):
        if isinstance(statement, ast.Import | ast.ImportFrom):
            if (
                isinstance(statement, ast.ImportFrom)
                and statement.level == 0
                and statement.module == "__future__"
                and len(statement.names) == 1
                and statement.names[0].name == "annotations"
                and statement.names[0].asname is None
            ):
                continue
            name, target = _closed_import(statement)
            if name in imports or name in constants or name in functions:
                raise _Refusal("import-name-collision")
            imports[name] = target
        elif isinstance(statement, ast.FunctionDef):
            if (
                statement.name in imports
                or statement.name in constants
                or statement.name in functions
            ):
                raise _Refusal("import-name-collision")
            function = copy.deepcopy(statement)
            function.body = _without_leading_docstring(function.body)
            functions[statement.name] = function
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            name = statement.targets[0].id
            value = _module_constant(statement.value, constants)
            if (
                value is None
                and isinstance(statement.value, ast.Name)
                and isinstance(constants.get(statement.value.id), ast.Tuple | ast.Dict)
            ):
                raise _Refusal("module-collection-use-not-modeled")
            if value is None or name in imports or name in constants or name in functions:
                raise _Refusal("module-constant-not-closed")
            constants[name] = value
        else:
            executable.append(statement)
    return imports, constants, functions, executable


def _without_leading_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    """Exclude only Python's inert leading string-literal docstring position."""

    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _closed_import(statement: ast.Import | ast.ImportFrom) -> tuple[str, str]:
    if isinstance(statement, ast.Import):
        if len(statement.names) != 1:
            raise _Refusal("unsupported-import-form")
        alias = statement.names[0]
        allowed = {
            ("numpy", "np"): ("np", "numpy"),
            ("math", None): ("math", "math"),
            ("pathlib", None): ("pathlib", "pathlib"),
            ("csv", None): ("csv", "csv"),
            ("os", None): ("os", "os"),
            ("statistics", None): ("statistics", "statistics"),
        }
        result = allowed.get((alias.name, alias.asname))
        if result is None:
            raise _Refusal("unsupported-import-form")
        return result
    if statement.level or len(statement.names) != 1:
        raise _Refusal("unsupported-import-form")
    alias = statement.names[0]
    if alias.asname is not None:
        raise _Refusal("unsupported-import-form")
    if statement.module == "pathlib" and alias.name == "Path":
        return "Path", "pathlib.Path"
    if statement.module == "collections" and alias.name == "defaultdict":
        return "defaultdict", "collections.defaultdict"
    if statement.module == "dataclasses" and alias.name == "dataclass":
        return "dataclass", "dataclasses.dataclass"
    if statement.module == "statistics" and alias.name in {
        "fmean",
        "mean",
        "stdev",
        "median",
        "variance",
    }:
        return alias.name, f"statistics.{alias.name}"
    if statement.module == "scipy" and alias.name == "stats":
        return "stats", "scipy.stats"
    if statement.module == "scipy.stats" and f"scipy.stats.{alias.name}" in _REGISTERED:
        return alias.name, f"scipy.stats.{alias.name}"
    raise _Refusal("unsupported-import-form")


def _module_constant(
    value: ast.expr, constants: dict[str, ModuleConstant]
) -> ModuleConstant | None:
    if isinstance(value, ast.Constant) and type(value.value) in {str, int, float}:
        return copy.deepcopy(value)
    if (
        isinstance(value, ast.Tuple)
        and value.elts
        and all(
            isinstance(item, ast.Constant) and isinstance(item.value, str) for item in value.elts
        )
    ):
        return copy.deepcopy(value)
    if (
        isinstance(value, ast.Dict)
        and value.keys
        and all(
            isinstance(key, ast.Constant)
            and isinstance(key.value, str)
            and isinstance(item, ast.Constant)
            and isinstance(item.value, str)
            for key, item in zip(value.keys, value.values, strict=True)
        )
        and len({cast(ast.Constant, key).value for key in value.keys}) == len(value.keys)
    ):
        return copy.deepcopy(value)
    if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
        collection = constants.get(value.value.id)
        if isinstance(collection, ast.Tuple | ast.Dict):
            return _module_collection_subscript(collection, value.slice, constants)
    folded_path = _path_value(value, constants)
    if folded_path is not None:
        return ast.Constant(value=folded_path)
    dirname = _dirname_value(value, constants)
    if dirname is not None:
        return ast.Constant(value=dirname)
    if (
        isinstance(value, ast.Call)
        and (
            (isinstance(value.func, ast.Name) and value.func.id == "Path")
            or (
                isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "pathlib"
                and value.func.attr == "Path"
            )
        )
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Constant)
        and isinstance(value.args[0].value, str)
    ):
        return copy.deepcopy(value.args[0])
    return None


def _live_main_guard_body(body: list[ast.stmt]) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for statement in body:
        if isinstance(statement, ast.If) and _main_guard(statement):
            result.extend(statement.body)
        elif (
            isinstance(statement, ast.If)
            and isinstance(statement.test, ast.Constant)
            and not statement.test.value
        ):
            continue
        else:
            result.append(statement)
    return result


def _main_guard(statement: ast.If) -> bool:
    test = statement.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == len(test.comparators) == 1
        and isinstance(test.ops[0], ast.Eq)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
        and not statement.orelse
    )


def _validate_import_uses(
    tree: ast.Module, imports: dict[str, str], constants: dict[str, ModuleConstant]
) -> None:
    parents: dict[ast.AST, ast.AST] = {
        child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Name)
            or not isinstance(node.ctx, ast.Load)
            or node.id not in imports
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.alias | ast.Import | ast.ImportFrom):
            continue
        target = imports[node.id]
        if target in _SINK_MODULE_CALLS:
            if not (isinstance(parent, ast.Call) and parent.func is node):
                raise _Refusal("import-use-outside-grammar")
            continue
        if target in {"math", "statistics"}:
            if not (
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and (
                    (target == "math" and parent.attr in {"sqrt", "isnan"})
                    or (
                        target == "statistics"
                        and parent.attr in {"mean", "fmean", "stdev", "median", "variance"}
                    )
                )
            ):
                raise _Refusal("import-use-outside-grammar")
            continue
        if target == "os":
            call = next(
                (
                    candidate
                    for candidate in ast.walk(tree)
                    if isinstance(candidate, ast.Call) and node in set(ast.walk(candidate.func))
                ),
                None,
            )
            if call is None or not (
                _path_value(call, constants) is not None
                or _dirname_value(call, constants) is not None
                or _closed_makedirs_call(call, constants)
            ):
                raise _Refusal("import-use-outside-grammar")
            continue
        if target == "pathlib" and not (
            isinstance(parent, ast.Attribute) and parent.value is node and parent.attr == "Path"
        ):
            raise _Refusal("import-use-outside-grammar")
        if target == "csv" and not (
            isinstance(parent, ast.Attribute)
            and parent.value is node
            and parent.attr == "DictReader"
        ):
            raise _Refusal("import-use-outside-grammar")
        if target == "scipy.stats" and not (
            isinstance(parent, ast.Attribute)
            and parent.value is node
            and f"scipy.stats.{parent.attr}" in _REGISTERED
        ):
            raise _Refusal("import-use-outside-grammar")
        if target in _REGISTERED and not (isinstance(parent, ast.Call) and parent.func is node):
            raise _Refusal("import-use-outside-grammar")
        if target == "pathlib.Path" and not (isinstance(parent, ast.Call) and parent.func is node):
            raise _Refusal("import-use-outside-grammar")
        if target == "collections.defaultdict" and not (
            isinstance(parent, ast.Call)
            and parent.func is node
            and len(parent.args) == 1
            and not parent.keywords
            and isinstance(parent.args[0], ast.Name)
            and parent.args[0].id in {"list", "set", "int"}
        ):
            raise _Refusal("import-use-outside-grammar")
        if target == "dataclasses.dataclass":
            raise _Refusal("dataclass-use-not-modeled")
        if target == "numpy":
            if not (
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and parent.attr in {"array", "asarray"}
            ):
                if isinstance(parent, ast.Attribute) and parent.attr in {
                    "mean",
                    "std",
                    "var",
                    "median",
                }:
                    continue
                raise _Refusal("import-use-outside-grammar")


def _validate_module_collection_uses(
    tree: ast.Module, constants: dict[str, ModuleConstant]
) -> None:
    """Permit collection constants only in the three reviewed plain-read positions."""

    collections = {
        name: value for name, value in constants.items() if isinstance(value, ast.Tuple | ast.Dict)
    }
    if not collections:
        return
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in collections
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Subscript) and parent.value is node:
            if _module_collection_subscript(collections[node.id], parent.slice, constants) is None:
                raise _Refusal("module-collection-use-not-modeled")
            continue
        if isinstance(parent, ast.For | ast.comprehension) and parent.iter is node:
            continue
        if (
            isinstance(parent, ast.Compare)
            and node in parent.comparators
            and any(isinstance(operator, ast.In | ast.NotIn) for operator in parent.ops)
        ):
            continue
        raise _Refusal("module-collection-use-not-modeled")


def _module_collection_subscript(
    collection: ast.Tuple | ast.Dict,
    key: ast.expr,
    constants: dict[str, ModuleConstant],
) -> ast.Constant | None:
    if isinstance(key, ast.Name):
        key = constants.get(key.id, key)
    if isinstance(collection, ast.Tuple):
        if not isinstance(key, ast.Constant) or type(key.value) is not int:
            return None
        index = key.value
        if index < 0 or index >= len(collection.elts):
            return None
        item = collection.elts[index]
        return copy.deepcopy(item) if isinstance(item, ast.Constant) else None
    if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
        return None
    matches = [
        item
        for candidate, item in zip(collection.keys, collection.values, strict=True)
        if isinstance(candidate, ast.Constant) and candidate.value == key.value
    ]
    return (
        copy.deepcopy(matches[0])
        if len(matches) == 1 and isinstance(matches[0], ast.Constant)
        else None
    )


def _flatten_functions(
    executable: list[ast.stmt],
    functions: dict[str, ast.FunctionDef],
    constants: dict[str, ModuleConstant],
    imports: dict[str, str],
) -> tuple[list[ast.stmt], list[AlphaRename], set[str]]:
    # This is a proof-oriented flattened IR, not executable Python: synthetic
    # fresh names and return carriers exist only for bounded semantic replay.
    if not functions:
        return _substitute_constants(executable, constants), [], set()
    reasons: set[str] = set()
    entry_call = (
        executable[0].value
        if len(executable) == 1
        and isinstance(executable[0], ast.Expr)
        and isinstance(executable[0].value, ast.Call)
        and isinstance(executable[0].value.func, ast.Name)
        and executable[0].value.func.id in functions
        else None
    )
    if entry_call is None:
        reasons.add("function-entry-not-closed")
    elif entry_call.args or entry_call.keywords:
        reasons.add("function-argument-not-simple")
    function_names = set(functions)
    for function in functions.values():
        reasons.update(_validate_function(function, constants, imports, function_names))
    if _user_helper_reaches_sink(functions, imports):
        reasons.add("sink-helper-call")
    graph = {
        name: {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
        }
        for name, function in functions.items()
    }
    if _cyclic(graph):
        reasons.add("function-recursive")
    roots = {
        node.func.id
        for statement in executable
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    }
    reachable = _reachable(roots, graph)
    dead: set[str] = set()
    for name in set(functions) - reachable:
        references = sum(
            1
            for statement in [*executable, *functions.values()]
            for node in ast.walk(statement)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == name
        )
        if references:
            reasons.add("function-not-provably-dead")
        else:
            dead.add(f"dead-function:{name}")
    if reasons:
        raise _Refusal(*reasons)
    renames: list[AlphaRename] = []
    counter = [0]
    flattened = _inline_statements(executable, functions, constants, 0, counter, renames, ())
    caller_visible = (
        {
            node.id
            for statement in [*executable, *functions.values()]
            for node in ast.walk(statement)
            if isinstance(node, ast.Name)
        }
        | set(functions)
        | set(constants)
        | set(imports)
    )
    fresh = [item.fresh_name for item in renames]
    if len(fresh) != len(set(fresh)) or set(fresh) & caller_visible:
        raise _Refusal("function-rename-collision")
    return _substitute_constants(flattened, constants), renames, dead


def _user_helper_reaches_sink(
    functions: dict[str, ast.FunctionDef], imports: dict[str, str]
) -> bool:
    for function in functions.values():
        definitions = {
            statement.targets[0].id: statement.value
            for statement in function.body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        }
        operand_names = {
            node.id
            for statement in function.body
            for node in ast.walk(statement)
            if isinstance(node, ast.Name)
            and (
                isinstance(statement, ast.With | ast.For)
                or any(
                    isinstance(call, ast.Call)
                    and _resolved_procedure(call.func, imports) in _REGISTERED
                    for call in ast.walk(statement)
                )
            )
        }
        changed = True
        while changed:
            changed = False
            for name in tuple(operand_names):
                if name not in definitions:
                    continue
                for node in ast.walk(definitions[name]):
                    if isinstance(node, ast.Name) and node.id not in operand_names:
                        operand_names.add(node.id)
                        changed = True
        writes = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_text"
        ]
        sink_names: set[str] = set()
        for write in writes:
            sink_names.update(_transitive_reads(write, definitions))
        for node in ast.walk(function):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in functions
            ):
                continue
            callee = functions[node.func.id]
            callee_writes = any(
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr == "write_text"
                for item in ast.walk(callee)
            )
            parent_assignment = next(
                (
                    statement
                    for statement in function.body
                    if isinstance(statement, ast.Assign) and node in set(ast.walk(statement.value))
                ),
                None,
            )
            assigned_sink = bool(
                parent_assignment is not None
                and len(parent_assignment.targets) == 1
                and isinstance(parent_assignment.targets[0], ast.Name)
                and parent_assignment.targets[0].id in sink_names - operand_names
            )
            if callee_writes or assigned_sink:
                return True
    return False


def _validate_function(
    function: ast.FunctionDef,
    constants: dict[str, ModuleConstant],
    imports: dict[str, str],
    function_names: set[str],
) -> set[str]:
    reasons: set[str] = set()
    args = function.args
    if args.posonlyargs or args.kwonlyargs:
        reasons.add("function-nonpositional-params")
    if args.defaults or args.kw_defaults:
        reasons.add("function-default-params")
    if args.vararg or args.kwarg:
        reasons.add("function-star-params")
    if any(isinstance(node, ast.Nonlocal | ast.Lambda) for node in ast.walk(function)):
        reasons.add("function-closure")
    if any(isinstance(node, ast.Global) for node in ast.walk(function)):
        reasons.add("function-globals-write")
    if any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        and node is not function
        for node in ast.walk(function)
    ):
        reasons.add("function-closure")
    parameters = {item.arg for item in args.args}
    stored = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    if parameters & stored:
        reasons.add("function-parameter-rebound")
    locals_ = stored - parameters
    if any(name.startswith("__dependence_v2_") for name in parameters | locals_):
        reasons.add("function-rename-collision")
    if (parameters | locals_ | set(constants)) & set(imports):
        reasons.add("import-name-collision")
    loads = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    definitions = {
        statement.targets[0].id: statement.value
        for statement in function.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }
    sink_expressions = [
        node.args[0]
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
        and node.args
    ]
    sink_reads = set().union(
        *(_transitive_reads(expression, definitions) for expression in sink_expressions)
    )
    # Defer only sink-position callable admission to the sink classifier, which
    # can issue the specific closed-whitelist reason.  Calls elsewhere retain
    # the module-data/global-read refusal.
    callable_loads = {
        node.func.id
        for statement in function.body
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in sink_reads
        )
        for node in ast.walk(statement.value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    callable_loads.update(
        node.func.id
        for expression in sink_expressions
        for node in ast.walk(expression)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    )
    allowed = (
        parameters
        | locals_
        | set(constants)
        | set(imports)
        | function_names
        | set(_BUILTINS)
        | callable_loads
    )
    if loads - allowed:
        reasons.add("function-globals-read")
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    if len(returns) > 1 or (returns and not _closed_final_return(function.body, returns[0])):
        reasons.add("function-return-shape")
    return reasons


def _closed_final_return(body: list[ast.stmt], target: ast.Return) -> bool:
    if body and body[-1] is target:
        return True
    return bool(
        body and isinstance(body[-1], ast.With) and body[-1].body and body[-1].body[-1] is target
    )


def _cyclic(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(name: str) -> bool:
        if name in visiting:
            return True
        if name in done:
            return False
        visiting.add(name)
        if any(visit(child) for child in graph[name]):
            return True
        visiting.remove(name)
        done.add(name)
        return False

    return any(visit(name) for name in graph)


def _reachable(roots: set[str], graph: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(graph[name])
    return seen


def _inline_statements(
    statements: list[ast.stmt],
    functions: dict[str, ast.FunctionDef],
    constants: dict[str, ModuleConstant],
    depth: int,
    counter: list[int],
    renames: list[AlphaRename],
    call_path: tuple[str, ...],
) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for statement in statements:
        target: ast.expr | None = None
        call: ast.Call | None = None
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            call = statement.value
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.value, ast.Call)
        ):
            target = statement.targets[0]
            call = statement.value
        if call is not None and isinstance(call.func, ast.Name) and call.func.id in functions:
            if depth >= MAX_V2_INLINE_DEPTH:
                raise _Refusal("function-inline-depth-exceeded")
            result.extend(
                _inline_call(
                    call,
                    target,
                    functions,
                    constants,
                    depth,
                    counter,
                    renames,
                    call_path,
                )
            )
        else:
            result.append(copy.deepcopy(statement))
    return result


def _inline_call(
    call: ast.Call,
    target: ast.expr | None,
    functions: dict[str, ast.FunctionDef],
    constants: dict[str, ModuleConstant],
    depth: int,
    counter: list[int],
    renames: list[AlphaRename],
    parent_call_path: tuple[str, ...],
) -> list[ast.stmt]:
    assert isinstance(call.func, ast.Name)
    function = functions[call.func.id]
    if call.keywords or len(call.args) != len(function.args.args):
        raise _Refusal("function-argument-not-simple")
    if any(not _simple_argument(item, constants) for item in call.args):
        raise _Refusal("function-argument-not-simple")
    counter[0] += 1
    call_number = counter[0]
    component = f"{call.func.id}:{call_number}"
    call_path = (*parent_call_path, component)
    call_path_id = "inline-call-path:" + "/".join(call_path)
    call_span = (
        getattr(call, "lineno", 0),
        getattr(call, "col_offset", 0),
        getattr(call, "end_lineno", 0),
        getattr(call, "end_col_offset", 0),
    )
    parameters = [item.arg for item in function.args.args]
    arguments = {
        name: copy.deepcopy(constants[item.id])
        if isinstance(item, ast.Name) and item.id in constants
        else copy.deepcopy(item)
        for name, item in zip(parameters, call.args, strict=True)
    }
    stored = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    locals_ = sorted(stored - set(parameters))
    local_map = {name: f"__dependence_v2_{call_number}_{name}" for name in [*parameters, *locals_]}
    for original, fresh in local_map.items():
        renames.append(AlphaRename(function.name, call_path_id, call_span, original, fresh))
    transformer = _InlineTransformer(arguments, local_map)
    body = [transformer.visit(copy.deepcopy(item)) for item in function.body]
    body = [ast.fix_missing_locations(cast(ast.stmt, item)) for item in body]
    return_value: ast.expr | None = None
    nested_return_name: str | None = None
    if body and isinstance(body[-1], ast.Return):
        returned = cast(ast.Return, body.pop())
        return_value = returned.value
    elif (
        body
        and isinstance(body[-1], ast.With)
        and body[-1].body
        and isinstance(body[-1].body[-1], ast.Return)
    ):
        with_statement = body[-1]
        returned = cast(ast.Return, with_statement.body.pop())
        if returned.value is not None:
            nested_return_name = f"__dependence_v2_{call_number}_return"
            with_statement.body.append(
                ast.Assign(
                    targets=[ast.Name(id=nested_return_name, ctx=ast.Store())],
                    value=returned.value,
                )
            )
    body = _inline_statements(body, functions, constants, depth + 1, counter, renames, call_path)
    if target is not None:
        body.append(
            ast.Assign(
                targets=[copy.deepcopy(target)],
                value=(
                    ast.Name(id=nested_return_name, ctx=ast.Load())
                    if nested_return_name is not None
                    else return_value
                    if return_value is not None
                    else ast.Constant(None)
                ),
            )
        )
    elif nested_return_name is not None:
        body.append(ast.Expr(value=ast.Name(id=nested_return_name, ctx=ast.Load())))
    elif return_value is not None:
        body.append(ast.Expr(value=return_value))
    return body


class _InlineTransformer(ast.NodeTransformer):
    def __init__(self, arguments: dict[str, ast.expr], locals_: dict[str, str]) -> None:
        self.arguments = arguments
        self.locals = locals_

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.arguments:
            return ast.copy_location(copy.deepcopy(self.arguments[node.id]), node)
        if node.id in self.locals:
            return ast.copy_location(ast.Name(id=self.locals[node.id], ctx=node.ctx), node)
        return node


class _ConstantTransformer(ast.NodeTransformer):
    def __init__(self, constants: dict[str, ModuleConstant]) -> None:
        self.constants = constants

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.constants:
            return ast.copy_location(copy.deepcopy(self.constants[node.id]), node)
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
        original_value = node.value
        visited = cast(ast.Subscript, self.generic_visit(node))
        if isinstance(original_value, ast.Name):
            collection = self.constants.get(original_value.id)
            if isinstance(collection, ast.Tuple | ast.Dict):
                folded = _module_collection_subscript(collection, visited.slice, self.constants)
                if folded is not None:
                    return ast.copy_location(folded, node)
        return visited


def _substitute_constants(
    statements: list[ast.stmt], constants: dict[str, ModuleConstant]
) -> list[ast.stmt]:
    transformer = _ConstantTransformer(constants)
    return [
        ast.fix_missing_locations(cast(ast.stmt, transformer.visit(copy.deepcopy(item))))
        for item in statements
    ]


def _simple_argument(expression: ast.expr, constants: dict[str, ModuleConstant]) -> bool:
    return isinstance(expression, ast.Constant) or (
        isinstance(expression, ast.Name)
        and (expression.id in constants or expression.id.isidentifier())
    )


def _recognize_reader(
    body: list[ast.stmt], constants: dict[str, ModuleConstant]
) -> tuple[str, str, str, str, str]:
    handles: dict[str, tuple[str, str]] = {}
    for node in (item for statement in body for item in ast.walk(statement)):
        if isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.optional_vars, ast.Name):
                    opened = _open_call(item.context_expr, constants)
                    if opened is not None:
                        handles[item.optional_vars.id] = opened
    matches: list[tuple[str, str, str, str, str]] = []
    for statement in (item for root in body for item in ast.walk(root)):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "list"
            and len(statement.value.args) == 1
            and not statement.value.keywords
        ):
            continue
        dict_call = statement.value.args[0]
        if not (
            isinstance(dict_call, ast.Call)
            and isinstance(dict_call.func, ast.Attribute)
            and isinstance(dict_call.func.value, ast.Name)
            and dict_call.func.value.id == "csv"
            and dict_call.func.attr == "DictReader"
            and len(dict_call.args) == 1
            and not dict_call.keywords
        ):
            continue
        source = dict_call.args[0]
        if isinstance(source, ast.Name) and source.id in handles:
            path, encoding = handles[source.id]
            matches.append(
                (statement.targets[0].id, path, encoding, "csv_newline", "csv_dictreader_file")
            )
        else:
            split = _splitlines_source(source, constants)
            if split is not None:
                path, encoding = split
                matches.append(
                    (
                        statement.targets[0].id,
                        path,
                        encoding,
                        "splitlines",
                        "csv_dictreader_splitlines",
                    )
                )
    if len(matches) != 1:
        raise _Refusal("reader-form-unsupported")
    match = matches[0]
    current = match[0]
    while True:
        aliases = [
            statement.targets[0].id
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Name)
            and statement.value.id == current
        ]
        if not aliases:
            break
        if len(aliases) != 1:
            raise _Refusal("reader-form-unsupported")
        current = aliases[0]
    return current, *match[1:]


def _open_call(
    expression: ast.expr, constants: dict[str, ModuleConstant]
) -> tuple[str, str] | None:
    if not (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == "open"
        and not expression.args
    ):
        return None
    path = _path_value(expression.func.value, constants)
    values = {item.arg: item.value for item in expression.keywords if item.arg is not None}
    if set(values) != {"newline", "encoding"} or not (
        isinstance(values["newline"], ast.Constant) and values["newline"].value == ""
    ):
        return None
    encoding = _encoding(values["encoding"])
    return (path, encoding) if path is not None and encoding is not None else None


def _splitlines_source(
    expression: ast.expr, constants: dict[str, ModuleConstant]
) -> tuple[str, str] | None:
    if not (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == "splitlines"
        and not expression.args
        and not expression.keywords
        and isinstance(expression.func.value, ast.Call)
    ):
        return None
    read = expression.func.value
    if not isinstance(read.func, ast.Attribute) or read.func.attr != "read_text" or read.args:
        return None
    values = {item.arg: item.value for item in read.keywords if item.arg is not None}
    if set(values) != {"encoding"}:
        return None
    path = _path_value(read.func.value, constants)
    encoding = _encoding(values["encoding"])
    return (path, encoding) if path is not None and encoding is not None else None


def _path_value(expression: ast.expr, constants: dict[str, ModuleConstant]) -> str | None:
    divided = _path_division_value(expression)
    if divided is not None:
        return divided
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.Name) and isinstance(constants.get(expression.id), ast.Constant):
        value = cast(ast.Constant, constants[expression.id]).value
        return value if isinstance(value, str) else None
    if (
        isinstance(expression, ast.Call)
        and _attribute_chain(expression.func) == ("os", "path", "join")
        and len(expression.args) >= 2
        and not expression.keywords
        and all(
            isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            for argument in expression.args
        )
    ):
        return posixpath.join(
            *(cast(str, cast(ast.Constant, argument).value) for argument in expression.args)
        )
    if (
        isinstance(expression, ast.Call)
        and (
            (isinstance(expression.func, ast.Name) and expression.func.id == "Path")
            or (
                isinstance(expression.func, ast.Attribute)
                and isinstance(expression.func.value, ast.Name)
                and expression.func.value.id == "pathlib"
                and expression.func.attr == "Path"
            )
        )
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.Constant)
        and isinstance(expression.args[0].value, str)
    ):
        return expression.args[0].value
    return None


def _path_division_value(expression: ast.expr) -> str | None:
    """Fold only ``Path(<literal>) / <literal>`` POSIX chains."""

    # pathlib can only shorten this literal chain through normalization; this
    # fold never normalizes, so fold == frozen path implies runtime == fold.

    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "Path"
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.Constant)
        and isinstance(expression.args[0].value, str)
    ):
        return expression.args[0].value
    if not (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Div)
        and isinstance(expression.right, ast.Constant)
        and isinstance(expression.right.value, str)
    ):
        return None
    left = _path_division_value(expression.left)
    return posixpath.join(left, expression.right.value) if left is not None else None


def _dirname_value(expression: ast.expr, constants: dict[str, ModuleConstant]) -> str | None:
    if not (
        isinstance(expression, ast.Call)
        and _attribute_chain(expression.func) == ("os", "path", "dirname")
        and len(expression.args) == 1
        and not expression.keywords
    ):
        return None
    path = _path_value(expression.args[0], constants)
    return posixpath.dirname(path) if path is not None else None


def _closed_makedirs_call(expression: ast.expr, constants: dict[str, ModuleConstant]) -> bool:
    if not (
        isinstance(expression, ast.Call)
        and _attribute_chain(expression.func) == ("os", "makedirs")
        and len(expression.args) == 1
        and len(expression.keywords) == 1
        and expression.keywords[0].arg == "exist_ok"
        and isinstance(expression.keywords[0].value, ast.Constant)
        and expression.keywords[0].value.value is True
    ):
        return False
    argument = expression.args[0]
    return (
        _path_value(argument, constants) is not None
        or _dirname_value(argument, constants) is not None
    )


def _attribute_chain(expression: ast.expr) -> tuple[str, ...] | None:
    parts: list[str] = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    if not isinstance(expression, ast.Name):
        return None
    return (expression.id, *reversed(parts))


def _encoding(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Constant) and expression.value in {"utf-8", "UTF-8"}:
        return "utf-8"
    if isinstance(expression, ast.Constant) and expression.value == "ascii":
        return "ascii"
    return None


def _recognize_grouping(
    body: list[ast.stmt], rows_name: str, constants: dict[str, ModuleConstant]
) -> tuple[str, str, str, str, tuple[str, ...], Literal["dict", "defaultdict_list"]]:
    declarations: dict[str, tuple[str, ...]] = {}
    defaultdict_names: set[str] = set()
    for statement in (item for root in body for item in ast.walk(root)):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Dict)
        ):
            name = statement.targets[0].id
            if any(
                not isinstance(value, ast.List) or value.elts for value in statement.value.values
            ):
                raise _Refusal("group-container-not-list")
            if any(
                not isinstance(key, ast.Constant) or not isinstance(key.value, str)
                for key in statement.value.keys
            ):
                raise _Refusal("group-set-not-closed")
            declarations[name] = tuple(
                key.value
                for key in statement.value.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            )
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "defaultdict"
        ):
            if (
                len(statement.value.args) != 1
                or statement.value.keywords
                or not isinstance(statement.value.args[0], ast.Name)
                or statement.value.args[0].id != "list"
            ):
                raise _Refusal("group-container-not-list")
            defaultdict_names.add(statement.targets[0].id)
        elif isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Set):
            raise _Refusal("group-container-not-list")
    loops = [
        node
        for root in body
        for node in ast.walk(root)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == rows_name
    ]
    if len(loops) != 1 or not isinstance(loops[0].target, ast.Name):
        raise _Refusal("group-accumulator-not-total")
    loop = loops[0]
    target = loop.target
    assert isinstance(target, ast.Name)
    row_name = target.id
    if any(isinstance(node, ast.Assign | ast.AugAssign) for node in ast.walk(loop)):
        raise _Refusal("group-accumulator-not-total")
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and (
            node.func.attr in {"add", "update"}
            or (
                node.func.attr == "setdefault"
                and len(node.args) == 2
                and isinstance(node.args[1], ast.Set)
            )
        )
        for node in ast.walk(loop)
    ):
        raise _Refusal("group-container-not-list")
    appends = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
    ]
    if len(appends) != 1 or len(appends[0].args) != 1 or appends[0].keywords:
        raise _Refusal("group-accumulator-not-total")
    append = appends[0]
    if (
        loop.orelse
        or len(loop.body) != 1
        or not isinstance(loop.body[0], ast.Expr)
        or loop.body[0].value is not append
    ):
        raise _Refusal("group-accumulator-not-total")
    parsed_value = _direct_row_value(append.args[0], row_name)
    if parsed_value is None:
        if _absent_or_string_cast(append.args[0], row_name):
            raise _Refusal("group-value-cast-absent")
        raise _Refusal("group-value-expression-unsupported")
    value_column, cast_kind = parsed_value
    receiver = cast(ast.Attribute, append.func).value
    bucket_keys: tuple[str, ...] = ()
    group_name: str | None = None
    key_column: str | None = None
    if (
        isinstance(receiver, ast.Call)
        and isinstance(receiver.func, ast.Attribute)
        and receiver.func.attr == "setdefault"
    ):
        if not isinstance(receiver.func.value, ast.Name):
            raise _Refusal("group-accumulator-not-total")
        group_name = receiver.func.value.id
        if (
            len(receiver.args) != 2
            or receiver.keywords
            or not isinstance(receiver.args[1], ast.List)
            or receiver.args[1].elts
        ):
            raise _Refusal("group-container-not-list")
        key_column = _row_subscript(receiver.args[0], row_name)
    elif isinstance(receiver, ast.Subscript) and isinstance(receiver.value, ast.Name):
        group_name = receiver.value.id
        key_column = _row_subscript(receiver.slice, row_name)
        bucket_keys = declarations.get(group_name, ())
        if not bucket_keys and group_name not in defaultdict_names:
            raise _Refusal("group-accumulator-not-total")
    if group_name is None or key_column is None:
        raise _Refusal("group-accumulator-not-total")
    for root in body:
        for node in ast.walk(root):
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.ctx, ast.Store)
                and isinstance(node.value, ast.Name)
                and node.value.id == group_name
            ):
                raise _Refusal("group-accumulator-not-total")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == group_name
                and node.func.attr not in {"setdefault", "items"}
            ):
                raise _Refusal("group-accumulator-not-total")
    return (
        group_name,
        key_column,
        value_column,
        cast_kind,
        bucket_keys,
        "defaultdict_list" if group_name in defaultdict_names else "dict",
    )


def _direct_row_value(expression: ast.expr, row_name: str) -> tuple[str, str] | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in {"float", "int"}
        and len(expression.args) == 1
        and not expression.keywords
    ):
        column = _row_subscript(expression.args[0], row_name)
        if column is not None:
            return column, expression.func.id
    return None


def _absent_or_string_cast(expression: ast.expr, row_name: str) -> bool:
    if _row_subscript(expression, row_name) is not None:
        return True
    return bool(
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "str"
        and len(expression.args) == 1
        and not expression.keywords
        and _row_subscript(expression.args[0], row_name) is not None
    )


def _row_subscript(expression: ast.expr, row_name: str) -> str | None:
    return (
        expression.slice.value
        if isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == row_name
        and isinstance(expression.slice, ast.Constant)
        and isinstance(expression.slice.value, str)
        else None
    )


def _recognize_procedure(
    body: list[ast.stmt],
    imports: dict[str, str],
    group_name: str,
    constants: dict[str, ModuleConstant],
    group_container_kind: Literal["dict", "defaultdict_list"] = "dict",
) -> tuple[str, tuple[OperandGroupBinding, ...], str, ast.Call]:
    container_aliases = {
        statement.targets[0].id
        for statement in (item for root in body for item in ast.walk(root))
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, ast.Name)
        and statement.value.id == group_name
    }
    aliases: dict[str, str] = {}
    for statement in (item for root in body for item in ast.walk(root)):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            key = _group_argument_key(statement.value, group_name, constants)
            if key is not None:
                aliases[statement.targets[0].id] = key
        if isinstance(statement, ast.Assign):
            if group_container_kind == "defaultdict_list" and _sorted_group_unpack(
                statement, group_name
            ):
                raise _Refusal("defaultdict-key-not-proven")
            unpacked = _sorted_group_unpack(statement, group_name)
            aliases.update(unpacked)
    matches: list[tuple[str, str, ast.Call]] = []
    for statement in (item for root in body for item in ast.walk(root)):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
        ):
            continue
        resolved = _resolved_procedure(statement.value.func, imports)
        if resolved is not None:
            matches.append((resolved, statement.targets[0].id, statement.value))
    if len(matches) != 1:
        raise _Refusal("procedure-call-unresolved")
    resolved, result_name, call = matches[0]
    if call.keywords or len(call.args) != _REGISTERED[resolved]:
        raise _Refusal("group-operand-arity-mismatch")
    if container_aliases and any(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in container_aliases
        for root in body
        for node in ast.walk(root)
    ):
        raise _Refusal("group-container-aliased")
    if any(_uses_group_container_alias(argument, container_aliases) for argument in call.args):
        raise _Refusal("group-container-aliased")
    if any(
        _group_operand_is_sliced(node, group_name)
        for root in body
        for node in ast.walk(root)
        if isinstance(node, ast.expr)
    ):
        raise _Refusal("group-operand-sliced")
    bindings: list[OperandGroupBinding] = []
    for position, argument in enumerate(call.args):
        key = _group_argument_key(argument, group_name, constants)
        argument_name = ast.unparse(argument)
        if isinstance(argument, ast.Name) and argument.id in aliases:
            key = aliases[argument.id]
        if key is None:
            raise _Refusal("group-operand-arity-mismatch")
        bindings.append(OperandGroupBinding(position, argument_name, key))
    return resolved, tuple(bindings), result_name, call


def _uses_group_container_alias(expression: ast.expr, aliases: set[str]) -> bool:
    return any(isinstance(node, ast.Name) and node.id in aliases for node in ast.walk(expression))


def _group_operand_is_sliced(expression: ast.expr, group_name: str) -> bool:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and isinstance(expression.func.value, ast.Name)
        and expression.func.value.id == "np"
        and expression.func.attr in {"array", "asarray"}
        and expression.args
    ):
        expression = expression.args[0]
    return bool(
        isinstance(expression, ast.Subscript)
        and isinstance(expression.slice, ast.Slice)
        and isinstance(expression.value, ast.Subscript)
        and isinstance(expression.value.value, ast.Name)
        and expression.value.value.id == group_name
    )


def _resolved_procedure(expression: ast.expr, imports: dict[str, str]) -> str | None:
    if isinstance(expression, ast.Name):
        value = imports.get(expression.id)
        return value if value in _REGISTERED else None
    if (
        isinstance(expression, ast.Attribute)
        and isinstance(expression.value, ast.Name)
        and imports.get(expression.value.id) == "scipy.stats"
    ):
        value = f"scipy.stats.{expression.attr}"
        return value if value in _REGISTERED else None
    return None


def _group_argument_key(
    expression: ast.expr, group_name: str, constants: dict[str, ModuleConstant]
) -> str | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and isinstance(expression.func.value, ast.Name)
        and expression.func.value.id == "np"
        and expression.func.attr in {"array", "asarray"}
    ):
        if len(expression.args) != 1 or any(item.arg != "dtype" for item in expression.keywords):
            return None
        if expression.keywords and not (
            len(expression.keywords) == 1
            and isinstance(expression.keywords[0].value, ast.Name)
            and expression.keywords[0].value.id == "float"
        ):
            return None
        expression = expression.args[0]
    if not (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == group_name
    ):
        return None
    key = expression.slice
    if isinstance(key, ast.Constant) and isinstance(key.value, str):
        return key.value
    if isinstance(key, ast.Name) and isinstance(constants.get(key.id), ast.Constant):
        value = cast(ast.Constant, constants[key.id]).value
        return value if isinstance(value, str) else None
    return None


def _sorted_group_unpack(statement: ast.Assign, group_name: str) -> dict[str, str]:
    if not (
        len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Tuple)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "sorted"
        and len(statement.value.args) == 1
        and not statement.value.keywords
        and isinstance(statement.value.args[0], ast.Call)
        and isinstance(statement.value.args[0].func, ast.Attribute)
        and isinstance(statement.value.args[0].func.value, ast.Name)
        and statement.value.args[0].func.value.id == group_name
        and statement.value.args[0].func.attr == "items"
        and not statement.value.args[0].args
        and not statement.value.args[0].keywords
    ):
        return {}
    result: dict[str, str] = {}
    for index, element in enumerate(statement.targets[0].elts):
        if not (
            isinstance(element, ast.Tuple)
            and len(element.elts) == 2
            and isinstance(element.elts[1], ast.Name)
        ):
            raise _Refusal("group-operand-arity-mismatch")
        result[element.elts[1].id] = f"__sorted_group_position_{index}"
    return result


def _recognize_sink(
    body: list[ast.stmt],
    result_name: str,
    constants: dict[str, ModuleConstant],
    expected_result_path: str | None,
) -> ast.Call:
    writes = [
        node
        for root in body
        for node in ast.walk(root)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    other_writes = [
        node
        for root in body
        for node in ast.walk(root)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write", "writelines"}
    ]
    if len(writes) != 1 or other_writes:
        raise _Refusal("sink-writes-outside-report")
    call = writes[0]
    if not (
        len(call.args) == 1
        and len(call.keywords) == 1
        and call.keywords[0].arg == "encoding"
        and _encoding(call.keywords[0].value) == "utf-8"
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, (ast.Constant, ast.Name, ast.Call))
    ):
        raise _Refusal("report-composition-not-modeled")
    function = call.func
    assert isinstance(function, ast.Attribute)
    if (
        expected_result_path is None
        or _path_value(function.value, constants) != expected_result_path
    ):
        raise _Refusal("report-composition-not-modeled")
    # The exact report expression is classified by the sink partition below.  At
    # this point require only a syntactic flow from the procedure result.
    if not any(
        isinstance(node, ast.Name) and node.id == result_name for node in ast.walk(call.args[0])
    ):
        definitions = _assignment_definitions(body)
        if result_name not in _transitive_reads(call.args[0], definitions):
            raise _Refusal("sink-flow-escapes")
    return call


def _verify_closed_flattened_statements(
    body: list[ast.stmt],
    *,
    rows_name: str,
    group_name: str,
    result_name: str,
    sink: ast.Call,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Partition the flattened module into operand and proven-sink-bound slices."""

    procedure = next(
        (
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and any(
                isinstance(node, ast.Name) and node.id == result_name for node in statement.targets
            )
        ),
        None,
    )
    if procedure is None:
        raise _Refusal("sink-controls-operand-flow")
    operand_names = {rows_name, group_name}
    operand_names.update(
        node.id for node in ast.walk(procedure.value) if isinstance(node, ast.Name)
    )
    procedure_reads = {node.id for node in ast.walk(procedure.value) if isinstance(node, ast.Name)}
    if any(
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, ast.Name)
        and statement.targets[0].id in procedure_reads
        and statement.value.id in procedure_reads
        for statement in body
    ):
        raise _Refusal("group-container-aliased")
    for statement in body:
        if isinstance(statement, ast.Assign) and (
            _sorted_group_unpack(statement, group_name)
            or _group_argument_key(statement.value, group_name, {}) is not None
        ):
            operand_names.update(
                node.id
                for target in statement.targets
                for node in ast.walk(target)
                if isinstance(node, ast.Name)
            )
    return _partition_sink_bound(body, procedure, sink, operand_names)


_SINK_NAME_CALLS = frozenset(
    {
        "len",
        "min",
        "max",
        "sum",
        "sorted",
        "round",
        "abs",
        "list",
        "str",
        "fmean",
        "mean",
        "stdev",
        "median",
        "variance",
    }
)
_SINK_MODULE_CALLS = frozenset(
    {
        "statistics.mean",
        "statistics.fmean",
        "statistics.stdev",
        "statistics.median",
        "statistics.variance",
        "np.mean",
        "np.std",
        "np.var",
        "np.median",
        "math.sqrt",
        "math.isnan",
    }
)
_SINK_STRING_METHODS = frozenset(
    {"format", "join", "lower", "upper", "strip", "lstrip", "rstrip", "replace", "split"}
)


def _statement_token(statement: ast.stmt, index: int) -> str:
    return "flattened-statement:" + semantic_digest(
        {"index": index, "syntax": ast.dump(statement, include_attributes=False)}
    )


def _assignment_definitions(body: list[ast.stmt]) -> dict[str, ast.expr]:
    result: dict[str, ast.expr] = {}
    for statement in body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            result[statement.targets[0].id] = statement.value
        elif (
            isinstance(statement, ast.If)
            and len(statement.body) == len(statement.orelse) == 1
            and isinstance(statement.body[0], ast.Assign)
            and isinstance(statement.orelse[0], ast.Assign)
            and len(statement.body[0].targets) == len(statement.orelse[0].targets) == 1
            and isinstance(statement.body[0].targets[0], ast.Name)
            and isinstance(statement.orelse[0].targets[0], ast.Name)
            and statement.body[0].targets[0].id == statement.orelse[0].targets[0].id
        ):
            result[statement.body[0].targets[0].id] = ast.IfExp(
                statement.test, statement.body[0].value, statement.orelse[0].value
            )
    return result


def _transitive_reads(expression: ast.AST, definitions: dict[str, ast.expr]) -> set[str]:
    pending = [node.id for node in ast.walk(expression) if isinstance(node, ast.Name)]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in definitions:
            pending.extend(
                node.id for node in ast.walk(definitions[name]) if isinstance(node, ast.Name)
            )
    return seen


def _sink_expression_closed(
    expression: ast.expr,
    operand_names: set[str],
    scalar_sequences: set[str],
) -> None:
    """Recognize only fresh/scalar report expressions; values are never certified."""

    if isinstance(expression, ast.Name | ast.Constant):
        return
    if isinstance(expression, ast.Slice):
        for item in (expression.lower, expression.upper, expression.step):
            if item is not None:
                _sink_expression_closed(item, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.Subscript):
        if isinstance(expression.value, ast.Name) and expression.value.id in operand_names:
            if not isinstance(expression.slice, ast.Slice):
                raise _Refusal("sink-classification-unresolved")
            if expression.value.id not in scalar_sequences:
                raise _Refusal("sink-classification-unresolved")
        _sink_expression_closed(expression.value, operand_names, scalar_sequences)
        _sink_expression_closed(expression.slice, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.List | ast.Tuple | ast.Set):
        for item in expression.elts:
            if isinstance(item, ast.Name) and item.id in operand_names:
                raise _Refusal("sink-classification-unresolved")
            _sink_expression_closed(item, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.Dict):
        for item in (*expression.keys, *expression.values):
            if item is not None:
                if isinstance(item, ast.Name) and item.id in operand_names:
                    raise _Refusal("sink-classification-unresolved")
                _sink_expression_closed(item, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.BinOp):
        _sink_expression_closed(expression.left, operand_names, scalar_sequences)
        _sink_expression_closed(expression.right, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.UnaryOp):
        _sink_expression_closed(expression.operand, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.BoolOp):
        for item in expression.values:
            _sink_expression_closed(item, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.Compare):
        _sink_expression_closed(expression.left, operand_names, scalar_sequences)
        for item in expression.comparators:
            _sink_expression_closed(item, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.JoinedStr):
        for item in expression.values:
            if isinstance(item, ast.FormattedValue):
                _sink_expression_closed(item.value, operand_names, scalar_sequences)
                if item.format_spec is not None:
                    _sink_expression_closed(item.format_spec, operand_names, scalar_sequences)
        return
    if isinstance(expression, ast.IfExp):
        for item in (expression.test, expression.body, expression.orelse):
            _sink_expression_closed(item, operand_names, scalar_sequences)
        return
    if not isinstance(expression, ast.Call):
        raise _Refusal("sink-classification-unresolved")
    if isinstance(expression.func, ast.Name):
        if expression.func.id not in _SINK_NAME_CALLS:
            raise _Refusal("sink-call-not-whitelisted")
        if expression.keywords:
            raise _Refusal("sink-call-keyword-argument")
        if (
            expression.func.id in {"list", "sorted"}
            and expression.args
            and isinstance(expression.args[0], ast.Name)
            and expression.args[0].id in operand_names
            and expression.args[0].id not in scalar_sequences
        ):
            raise _Refusal("sink-classification-unresolved")
    elif isinstance(expression.func, ast.Attribute):
        if isinstance(expression.func.value, ast.Name):
            resolved = f"{expression.func.value.id}.{expression.func.attr}"
            if resolved in _SINK_MODULE_CALLS:
                if expression.keywords:
                    raise _Refusal("sink-call-keyword-argument")
            elif expression.func.attr not in _SINK_STRING_METHODS:
                raise _Refusal("sink-call-not-whitelisted")
        elif expression.func.attr not in _SINK_STRING_METHODS:
            raise _Refusal("sink-call-not-whitelisted")
        _sink_expression_closed(expression.func.value, operand_names, scalar_sequences)
    else:
        raise _Refusal("sink-call-not-whitelisted")
    for item in expression.args:
        _sink_expression_closed(item, operand_names, scalar_sequences)
    for keyword in expression.keywords:
        _sink_expression_closed(keyword.value, operand_names, scalar_sequences)


def _partition_sink_bound(
    body: list[ast.stmt],
    procedure_statement: ast.Assign,
    sink: ast.Call,
    initial_operand_names: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not isinstance(procedure_statement.value, ast.Call):
        raise _Refusal("sink-classification-unresolved")
    scalar_sequences = {
        argument.id for argument in procedure_statement.value.args if isinstance(argument, ast.Name)
    }
    sink_statement = next(
        (statement for statement in body if sink in set(ast.walk(statement))), None
    )
    if not isinstance(sink_statement, ast.Expr):
        raise _Refusal("sink-classification-unresolved")
    if any(
        isinstance(statement, ast.If | ast.For | ast.With)
        and (procedure_statement in set(ast.walk(statement)) or sink in set(ast.walk(statement)))
        for statement in body
    ):
        raise _Refusal("sink-controls-operand-flow")
    definitions = _assignment_definitions(body)
    operand_names = set(initial_operand_names)
    operand_names.update(
        node.id for node in ast.walk(procedure_statement.value) if isinstance(node, ast.Name)
    )
    changed = True
    while changed:
        changed = False
        for name in tuple(operand_names):
            value = definitions.get(name)
            if value is None:
                continue
            for node in ast.walk(value):
                if isinstance(node, ast.Name) and node.id not in operand_names:
                    operand_names.add(node.id)
                    changed = True
    operand_indices: set[int] = set()
    for index, statement in enumerate(body):
        stores = {
            node.id
            for node in ast.walk(statement)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        }
        if (
            statement is procedure_statement
            or isinstance(statement, ast.With | ast.For)
            or stores & operand_names
        ):
            operand_indices.add(index)
    sink_indices: set[int] = {body.index(sink_statement)}
    sink_names = _transitive_reads(sink.args[0], definitions) - operand_names
    for index, statement in enumerate(body):
        if index in operand_indices or index in sink_indices:
            continue
        if isinstance(statement, ast.Expr) and _closed_makedirs_call(statement.value, {}):
            sink_indices.add(index)
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            call = statement.value
            if (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id in operand_names
                and call.func.attr
                in {"append", "extend", "insert", "pop", "remove", "clear", "sort", "update"}
            ):
                raise _Refusal("sink-mutates-operand-name")
        if isinstance(statement, ast.If):
            branches = [*statement.body, *statement.orelse]
            if len(statement.body) == len(statement.orelse) == 1 and all(
                isinstance(branch, ast.Assign)
                and len(branch.targets) == 1
                and isinstance(branch.targets[0], ast.Name)
                and branch.targets[0].id in sink_names
                for branch in branches
            ):
                _sink_expression_closed(statement.test, operand_names, scalar_sequences)
                for branch in branches:
                    assert isinstance(branch, ast.Assign)
                    _sink_expression_closed(branch.value, operand_names, scalar_sequences)
                sink_indices.add(index)
                continue
        if isinstance(statement, ast.Assign) and any(
            isinstance(node, ast.Subscript | ast.Attribute)
            for target in statement.targets
            for node in ast.walk(target)
        ):
            raise _Refusal("sink-flow-escapes")
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Name)
            and statement.value.id in operand_names
        ):
            # Object identity is disqualifying even when the alias is not on
            # the later report-value read chain.
            raise _Refusal("sink-aliases-operand-object")
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in sink_names
        ):
            raise _Refusal("sink-classification-unresolved")
        _sink_expression_closed(statement.value, operand_names, scalar_sequences)
        sink_indices.add(index)
    _sink_expression_closed(sink.args[0], operand_names, scalar_sequences)
    return (
        tuple(_statement_token(body[index], index) for index in sorted(operand_indices)),
        tuple(_statement_token(body[index], index) for index in sorted(sink_indices)),
    )


def _independent_wall_scan(
    tree: ast.Module, constants: dict[str, ModuleConstant] | None = None
) -> set[str]:
    reasons: set[str] = set()
    nonbyte_predicate_helpers = _nonbyte_predicate_helpers(tree)
    if any(
        _counting_predicate_is_outside_wall(node, nonbyte_predicate_helpers, constants or {})
        for node in ast.walk(tree)
    ):
        reasons.add("count-predicate-not-closed")
    return reasons


def _counting_predicate_is_outside_wall(
    node: ast.AST,
    nonbyte_predicate_helpers: frozenset[str],
    constants: dict[str, ModuleConstant],
) -> bool:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "sum"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.GeneratorExp)
        and len(node.args[0].generators) == 1
    ):
        generator = node.args[0].generators[0]
        return bool(
            generator.ifs
            and (
                not isinstance(generator.target, ast.Name)
                or any(
                    _wall_predicate_is_relevant_and_unclosed(
                        predicate, generator.target.id, nonbyte_predicate_helpers, constants
                    )
                    for predicate in generator.ifs
                )
            )
        )
    if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
        guarded = [statement for statement in node.body if isinstance(statement, ast.If)]
        return any(
            any(
                isinstance(statement, ast.AugAssign)
                and isinstance(statement.op, ast.Add)
                and isinstance(statement.value, ast.Constant)
                and type(statement.value.value) is int
                and statement.value.value == 1
                for statement in guard.body
            )
            and _wall_predicate_is_relevant_and_unclosed(
                guard.test, node.target.id, nonbyte_predicate_helpers, constants
            )
            for guard in guarded
        )
    return False


def _wall_predicate_is_relevant_and_unclosed(
    expression: ast.expr,
    row_name: str,
    nonbyte_predicate_helpers: frozenset[str],
    constants: dict[str, ModuleConstant],
) -> bool:
    if _wall_byte_predicate(expression, row_name, constants):
        return False
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in nonbyte_predicate_helpers
        for node in ast.walk(expression)
    ):
        return True
    return any(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == row_name
        for node in ast.walk(expression)
    )


def _nonbyte_predicate_helpers(tree: ast.Module) -> frozenset[str]:
    names: set[str] = set()
    for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
        parameters = {argument.arg for argument in function.args.args}
        for returned in (
            node.value
            for node in ast.walk(function)
            if isinstance(node, ast.Return) and node.value is not None
        ):
            if any(
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id in parameters
                for node in ast.walk(returned)
            ) and not any(_wall_byte_predicate(returned, parameter) for parameter in parameters):
                names.add(function.name)
    return frozenset(names)


def _module_string_alternative_used(
    tree: ast.Module,
    imports: dict[str, str],
    constants: dict[str, ModuleConstant],
) -> bool:
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        if _resolved_procedure(call.func, imports) not in _COUNT_PROCEDURES:
            continue
        alternative = next(
            (keyword.value for keyword in call.keywords if keyword.arg == "alternative"), None
        )
        if (
            isinstance(alternative, ast.Name)
            and isinstance(constants.get(alternative.id), ast.Constant)
            and isinstance(cast(ast.Constant, constants[alternative.id]).value, str)
        ):
            return True
    return False


def _wall_byte_predicate(
    expression: ast.expr,
    row_name: str,
    constants: dict[str, ModuleConstant] | None = None,
) -> bool:
    parts = (
        expression.values
        if isinstance(expression, ast.BoolOp) and isinstance(expression.op, ast.And)
        else [expression]
    )
    return bool(parts) and all(
        isinstance(part, ast.Compare)
        and len(part.ops) == len(part.comparators) == 1
        and isinstance(part.ops[0], ast.Eq | ast.NotEq)
        and _row_subscript(part.left, row_name) is not None
        and (
            (
                isinstance(part.comparators[0], ast.Constant)
                and isinstance(part.comparators[0].value, str)
            )
            or (
                isinstance(part.comparators[0], ast.Name)
                and isinstance((constants or {}).get(part.comparators[0].id), ast.Constant)
                and isinstance(
                    cast(ast.Constant, (constants or {})[part.comparators[0].id]).value, str
                )
            )
        )
        for part in parts
    )


def _candidate_columns(context: FrozenInspectionContext) -> tuple[str, ...]:
    material = next((item for item in context.material_inputs if item.path.endswith(".csv")), None)
    if material is None:
        return ()
    try:
        first = material.content.decode("utf-8", errors="strict").splitlines()[0]
    except (UnicodeDecodeError, IndexError):
        return ()
    return tuple(item for item in first.split(",") if item)


def _scipy_is_pinned(context: FrozenInspectionContext) -> bool:
    matches = []
    for material in context.material_inputs:
        if Path(material.path).name.lower().startswith("requirements"):
            try:
                text = material.content.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                return False
            if _SCIPY_PIN.search(text):
                matches.append(material)
    return len(matches) == 1


def _node_token(path: str, node: ast.AST, kind: str) -> str:
    return f"{kind}:{semantic_digest({'path': path, 'line': getattr(node, 'lineno', 0), 'column': getattr(node, 'col_offset', 0)})}"


def _unsupported(*reasons: str) -> GrowthAnalysis:
    values = tuple(sorted({require_registered_v2_reason(reason) for reason in reasons}))
    return GrowthAnalysis(
        state="unsupported",
        certificate=None,
        obligation=None,
        abstention_reasons=values,
        candidate_key_columns=(),
        basis="The source was outside the closed dependence growth-1 grammar: " + ", ".join(values),
    )


def _discharged_unsupported(reason: str) -> DischargedGrowthAnalysis:
    reason = require_registered_v2_reason(reason)
    return DischargedGrowthAnalysis(
        state="unsupported",
        verified_certificate=None,
        abstention_reasons=(reason,),
        candidate_key_columns=(),
        basis=f"The controller-side growth proof abstained: {reason}.",
    )
