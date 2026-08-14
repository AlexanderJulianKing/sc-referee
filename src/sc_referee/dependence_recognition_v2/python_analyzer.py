"""Untrusted bounded analyzer for the dependence growth-1 shadow.

The analyzer never executes authored code.  It proves a small hygienic inlining
grammar, recognizes one total list-bucket accumulation, and proposes a
certificate.  Frozen-byte group facts are attached only by
``discharge_dependence_growth_analysis``.
"""

from __future__ import annotations

import ast
import copy
import re
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest
from sc_referee.dependence_recognition.python_analyzer import _trusted_authorizations
from sc_referee.dependence_recognition_v2.certificate import (
    verify_dependence_growth_certificate,
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
    DependenceGrowthCertificate,
    DischargedGrowthAnalysis,
    GroupValueSequenceObligation,
    GrowthAnalysis,
    GrowthConclusion,
    OperandGroupBinding,
    require_registered_v2_reason,
)
from sc_referee.scientific_checks.core import FrozenInspectionContext

_REGISTERED = {
    "scipy.stats.ttest_ind": 2,
    "scipy.stats.mannwhitneyu": 2,
}
_BUILTINS = frozenset({"list", "set", "float", "int", "sorted", "str", "len", "range", "enumerate"})
_SCIPY_PIN = re.compile(r"(?m)^\s*scipy\s*==\s*1\.14\.0\s*(?:#.*)?$")


class _Refusal(Exception):
    def __init__(self, *reasons: str) -> None:
        self.reasons = tuple(require_registered_v2_reason(reason) for reason in reasons)


def analyze_dependence_growth_python(context: FrozenInspectionContext) -> GrowthAnalysis:
    """Propose one growth certificate or return granular sorted abstentions."""

    reasons: set[str] = set()
    documents = [item for item in context.documents if item.media_type == "text/x-python"]
    if len(documents) != 1:
        return _unsupported("single-python-module-required")
    document = documents[0]
    if len(document.content) > MAX_V2_SOURCE_BYTES:
        return _unsupported("source-byte-ceiling")
    try:
        source = document.content.decode("utf-8", errors="strict")
        tree = ast.parse(source)
    except (UnicodeDecodeError, SyntaxError, ValueError, RecursionError):
        return _unsupported("python-parse-unsupported")
    if sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return _unsupported("ast-node-ceiling")

    authorities = _trusted_authorizations(context)
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
        _validate_import_uses(tree, imports)
        flattened, renames, dead = _flatten_functions(executable, functions, constants, imports)
    except _Refusal as refusal:
        reasons.update(refusal.reasons)
        # Report composition and multi-site are independently useful fuel.
        reasons.update(_independent_wall_scan(tree))
        return _unsupported(*reasons)

    reasons.update(_independent_wall_scan(tree))
    try:
        read = _recognize_reader(flattened, constants)
        grouping = _recognize_grouping(flattened, read[0], constants)
        procedure = _recognize_procedure(flattened, imports, grouping[0], constants)
        sink = _recognize_sink(flattened, procedure[2], constants)
        _verify_closed_flattened_statements(
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

    group_name, key_column, value_column, cast_kind, bucket_keys = grouping
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
        operand_bindings=argument_bindings,
        alpha_renames=tuple(renames),
        dead_syntactic_construct_tokens=tuple(sorted(dead)),
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
    if len(fact.groups) != _REGISTERED[certificate.resolved_callable]:
        return _discharged_unsupported("group-operand-arity-mismatch")
    keys = tuple(item.group_key for item in fact.groups)
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
        trusted_authorizations=_trusted_authorizations(context),
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


def _module_parts(
    tree: ast.Module,
) -> tuple[dict[str, str], dict[str, ast.Constant], dict[str, ast.FunctionDef], list[ast.stmt]]:
    imports: dict[str, str] = {}
    constants: dict[str, ast.Constant] = {}
    functions: dict[str, ast.FunctionDef] = {}
    executable: list[ast.stmt] = []
    for statement in _live_main_guard_body(tree.body):
        if isinstance(statement, ast.Import | ast.ImportFrom):
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
            functions[statement.name] = statement
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            name = statement.targets[0].id
            value = _module_constant(statement.value)
            if value is None or name in imports or name in constants or name in functions:
                raise _Refusal("module-constant-not-closed")
            constants[name] = value
        else:
            executable.append(statement)
    return imports, constants, functions, executable


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
    if statement.module == "scipy" and alias.name == "stats":
        return "stats", "scipy.stats"
    if statement.module == "scipy.stats" and f"scipy.stats.{alias.name}" in _REGISTERED:
        return alias.name, f"scipy.stats.{alias.name}"
    raise _Refusal("unsupported-import-form")


def _module_constant(value: ast.expr) -> ast.Constant | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return copy.deepcopy(value)
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


def _validate_import_uses(tree: ast.Module, imports: dict[str, str]) -> None:
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
        if target == "math":
            raise _Refusal("import-use-outside-grammar")
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
        if target == "numpy":
            if not (
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and parent.attr in {"array", "asarray"}
            ):
                if isinstance(parent, ast.Attribute) and parent.attr in {"mean", "var"}:
                    raise _Refusal("report-composition-not-modeled")
                raise _Refusal("import-use-outside-grammar")


def _flatten_functions(
    executable: list[ast.stmt],
    functions: dict[str, ast.FunctionDef],
    constants: dict[str, ast.Constant],
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
    call_sites = Counter(
        node.func.id
        for statement in [*executable, *functions.values()]
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    )
    if any(count > 1 for count in call_sites.values()):
        reasons.add("function-multiple-call-sites")
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
    flattened = _inline_statements(executable, functions, constants, 0, counter, renames)
    return _substitute_constants(flattened, constants), renames, dead


def _validate_function(
    function: ast.FunctionDef,
    constants: dict[str, ast.Constant],
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
        reasons.add("import-name-collision")
    if (parameters | locals_ | set(constants)) & set(imports):
        reasons.add("import-name-collision")
    loads = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    allowed = parameters | locals_ | set(constants) | set(imports) | function_names | set(_BUILTINS)
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
    constants: dict[str, ast.Constant],
    depth: int,
    counter: list[int],
    renames: list[AlphaRename],
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
            result.extend(_inline_call(call, target, functions, constants, depth, counter, renames))
        else:
            result.append(copy.deepcopy(statement))
    return result


def _inline_call(
    call: ast.Call,
    target: ast.expr | None,
    functions: dict[str, ast.FunctionDef],
    constants: dict[str, ast.Constant],
    depth: int,
    counter: list[int],
    renames: list[AlphaRename],
) -> list[ast.stmt]:
    assert isinstance(call.func, ast.Name)
    function = functions[call.func.id]
    if call.keywords or len(call.args) != len(function.args.args):
        raise _Refusal("function-argument-not-simple")
    if any(not _simple_argument(item, constants) for item in call.args):
        raise _Refusal("function-argument-not-simple")
    counter[0] += 1
    call_number = counter[0]
    call_token = f"inline-call:{call.func.id}:{call_number}"
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
        renames.append(AlphaRename(function.name, call_token, original, fresh))
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
    body = _inline_statements(body, functions, constants, depth + 1, counter, renames)
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
    def __init__(self, constants: dict[str, ast.Constant]) -> None:
        self.constants = constants

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.constants:
            return ast.copy_location(copy.deepcopy(self.constants[node.id]), node)
        return node


def _substitute_constants(
    statements: list[ast.stmt], constants: dict[str, ast.Constant]
) -> list[ast.stmt]:
    transformer = _ConstantTransformer(constants)
    return [
        ast.fix_missing_locations(cast(ast.stmt, transformer.visit(copy.deepcopy(item))))
        for item in statements
    ]


def _simple_argument(expression: ast.expr, constants: dict[str, ast.Constant]) -> bool:
    return isinstance(expression, ast.Constant) or (
        isinstance(expression, ast.Name)
        and (expression.id in constants or expression.id.isidentifier())
    )


def _recognize_reader(
    body: list[ast.stmt], constants: dict[str, ast.Constant]
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


def _open_call(expression: ast.expr, constants: dict[str, ast.Constant]) -> tuple[str, str] | None:
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
    expression: ast.expr, constants: dict[str, ast.Constant]
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


def _path_value(expression: ast.expr, constants: dict[str, ast.Constant]) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.Name) and expression.id in constants:
        return cast(str, constants[expression.id].value)
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


def _encoding(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Constant) and expression.value in {"utf-8", "UTF-8"}:
        return "utf-8"
    if isinstance(expression, ast.Constant) and expression.value == "ascii":
        return "ascii"
    return None


def _recognize_grouping(
    body: list[ast.stmt], rows_name: str, constants: dict[str, ast.Constant]
) -> tuple[str, str, str, str, tuple[str, ...]]:
    declarations: dict[str, tuple[str, ...]] = {}
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
        if not bucket_keys:
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
    return group_name, key_column, value_column, cast_kind, bucket_keys


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
    constants: dict[str, ast.Constant],
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
    expression: ast.expr, group_name: str, constants: dict[str, ast.Constant]
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
    if isinstance(key, ast.Name) and key.id in constants:
        return cast(str, constants[key.id].value)
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
    body: list[ast.stmt], result_name: str, constants: dict[str, ast.Constant]
) -> ast.Call:
    writes = [
        node
        for root in body
        for node in ast.walk(root)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if len(writes) != 1:
        raise _Refusal("report-composition-not-modeled")
    call = writes[0]
    if not (
        len(call.args) == 1
        and isinstance(call.args[0], ast.Call)
        and isinstance(call.args[0].func, ast.Name)
        and call.args[0].func.id == "str"
        and len(call.args[0].args) == 1
        and isinstance(call.args[0].args[0], ast.Name)
        and call.args[0].args[0].id == result_name
        and len(call.keywords) == 1
        and call.keywords[0].arg == "encoding"
        and _encoding(call.keywords[0].value) == "utf-8"
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, (ast.Constant, ast.Name, ast.Call))
    ):
        raise _Refusal("report-composition-not-modeled")
    function = call.func
    assert isinstance(function, ast.Attribute)
    if _path_value(function.value, constants) is None:
        raise _Refusal("report-composition-not-modeled")
    return call


def _verify_closed_flattened_statements(
    body: list[ast.stmt],
    *,
    rows_name: str,
    group_name: str,
    result_name: str,
    sink: ast.Call,
) -> None:
    """Require the live flattened module to contain only modeled statements."""

    for statement in body:
        if isinstance(statement, ast.With):
            if len(statement.items) != 1 or len(statement.body) != 1:
                raise _Refusal("noninterference-unproven:with-body")
            nested = statement.body[0]
            if not (
                isinstance(nested, ast.Assign)
                and len(nested.targets) == 1
                and isinstance(nested.targets[0], ast.Name)
                and isinstance(nested.value, ast.Call)
                and isinstance(nested.value.func, ast.Name)
                and nested.value.func.id == "list"
            ):
                raise _Refusal("noninterference-unproven:with-body")
            continue
        if isinstance(statement, ast.For):
            # _recognize_grouping has already proved the exact total append body.
            continue
        if isinstance(statement, ast.Expr):
            if statement.value is not sink:
                if isinstance(statement.value, ast.Call) and isinstance(
                    statement.value.func, ast.Attribute
                ):
                    raise _Refusal("noninterference-unproven:attribute-call")
                if isinstance(statement.value, ast.Call):
                    raise _Refusal("noninterference-unproven:name-call")
                raise _Refusal("noninterference-unproven:expression")
            continue
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            raise _Refusal("noninterference-unproven:statement")
        target = statement.targets[0]
        value = statement.value
        if isinstance(target, ast.Name) and target.id == rows_name:
            if isinstance(value, ast.Call | ast.Name):
                continue
        if isinstance(target, ast.Name) and target.id == group_name and isinstance(value, ast.Dict):
            continue
        if (
            isinstance(target, ast.Name)
            and target.id == result_name
            and isinstance(value, ast.Call)
        ):
            continue
        if isinstance(target, ast.Name) and _group_argument_key(value, group_name, {}) is not None:
            continue
        if isinstance(target, ast.Tuple) and _sorted_group_unpack(statement, group_name):
            continue
        if isinstance(value, ast.Name):
            raise _Refusal("noninterference-unproven:alias-assignment")
        raise _Refusal("noninterference-unproven:assignment")


def _independent_wall_scan(tree: ast.Module) -> set[str]:
    reasons: set[str] = set()
    function_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    counts = Counter(
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in function_names
    )
    if any(count > 1 for count in counts.values()):
        reasons.add("function-multiple-call-sites")
    writes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if writes and any(
        not (
            len(call.args) == 1
            and isinstance(call.args[0], ast.Call)
            and isinstance(call.args[0].func, ast.Name)
            and call.args[0].func.id == "str"
        )
        for call in writes
    ):
        reasons.add("report-composition-not-modeled")
    return reasons


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
