"""Proof-producing semantic abstract interpreter for founder orientation v3.

The v2 recognizer is intentionally frozen.  This module lives beside it and
models operations compositionally: a primitive transfer is implemented once,
helpers are evaluated with call-site abstract arguments, loop locals are
ordinary scoped bindings, and report writes are discovered by their effects.
The analyzer only proposes certificates.  The independent kernel in
``founder_orientation_certificate`` is the sole authorization boundary.
"""

from __future__ import annotations

import ast
import builtins
import json
import math
import operator
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Any, Literal, TypeAlias

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
)
from sc_referee.scientific_checks.founder_orientation_certificate import (
    verify_orientation_certificate,
)
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    _guarded_parse,
    _imports_case_module,
    _module_bans,
    _python_parser_supported,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    Effect,
    Eq,
    EvidencePoint,
    ExactNumber,
    Fold,
    Gated,
    Orientation,
    OrientationCertificate,
    Predicate,
    PrimitiveTransform,
    Projection,
    Selector,
    Sequence,
    SinkProof,
    Unknown,
    VerifiedOrientationCertificate,
)

FOUNDER_ORIENTATION_SEMANTIC_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())

_MAX_EXPRESSION_DEPTH = 120
_MAX_CALL_DEPTH = 8
_MAX_SOURCE_BYTES = 2_000_000
_MAX_AST_NODES = 20_000
_MAX_HELPERS = 256
_MAX_EXACT_INTEGER_BITS = 4_096
_MAX_POW_EXPONENT = 1_024
_STDLIB_IMPORTS = frozenset({"csv", "math", "pathlib", "fractions", "decimal", "statistics"})
_BUILTINS = frozenset(dir(builtins))
_NUMERIC_RUNTIME_TYPES = frozenset({"int", "float", "decimal", "fraction"})


@dataclass(frozen=True)
class SemanticResolution:
    """The public v3 source-plane answer."""

    state: str
    orientation: Orientation | None
    operand_value: str | None
    spans: tuple[EvidenceSpan, ...]
    source_path: str | None
    certificate: VerifiedOrientationCertificate | None = None


@dataclass(frozen=True)
class _ExactString:
    value: str


@dataclass(frozen=True)
class _ExactBool:
    value: bool


@dataclass(frozen=True)
class _NoneValue:
    pass


@dataclass(frozen=True)
class _ModuleValue:
    origin: str


@dataclass(frozen=True)
class _PathValue:
    parts: tuple[str, ...]
    exact: bool = True

    @property
    def normalized(self) -> str:
        return _normalize_posix_parts(self.parts)


@dataclass(frozen=True)
class _InputText:
    path: _PathValue


@dataclass(frozen=True)
class _InputLines:
    path: _PathValue


@dataclass(frozen=True)
class _FileHandle:
    path: _PathValue
    mode: str


@dataclass(frozen=True)
class _RowValue:
    asset: str
    row_domain: str
    index_map: str


@dataclass(frozen=True)
class _PairValue:
    items: tuple[_Tracked, ...]


@dataclass(frozen=True)
class _ContainerValue:
    items: tuple[_Tracked, ...]


@dataclass(frozen=True)
class _IndexValue:
    index_map: str
    row_domain: str


@dataclass(frozen=True)
class _LengthValue:
    index_map: str
    row_domain: str


@dataclass(frozen=True)
class _SequenceState:
    semantic: Sequence
    row_domain: str
    token: str
    single_pass: bool = False


@dataclass(frozen=True)
class _DependentValue:
    predicate: Predicate
    false_value: ExactNumber
    true_value: ExactNumber


@dataclass(frozen=True)
class _DerivedValue:
    operation: str


@dataclass(frozen=True)
class _TextValue:
    field_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class _AccumulatorValue:
    name: str
    row_domain: str
    index_map: str
    initial_value: ExactNumber
    operation: Literal["sum", "product"] | None = None


@dataclass(frozen=True)
class _FunctionValue:
    name: str


@dataclass(frozen=True)
class _ReportField:
    value: _Tracked
    selected_result: bool


_NONE = _NoneValue()

_Value: TypeAlias = (
    ExactNumber
    | _ExactString
    | _ExactBool
    | _NoneValue
    | _ModuleValue
    | _PathValue
    | _InputText
    | _InputLines
    | _FileHandle
    | _RowValue
    | _PairValue
    | _ContainerValue
    | _IndexValue
    | _LengthValue
    | _SequenceState
    | Projection
    | Predicate
    | Selector
    | _DependentValue
    | Gated
    | Fold
    | _DerivedValue
    | _TextValue
    | _AccumulatorValue
    | _FunctionValue
    | Unknown
)


@dataclass(frozen=True)
class _Tracked:
    value: _Value
    origins: frozenset[str] = frozenset()
    folds: frozenset[str] = frozenset()
    selectors: frozenset[str] = frozenset()
    predicates: frozenset[str] = frozenset()
    bindings: frozenset[str] = frozenset()
    unknowns: frozenset[str] = frozenset()
    index_map: str | None = None

    def with_binding(self, name: str) -> _Tracked:
        return replace(self, bindings=self.bindings | {name})


@dataclass(frozen=True)
class _WriteEvent:
    path: _PathValue
    payload: _Tracked
    branch: str


@dataclass
class _ExecResult:
    returned: _Tracked | None = None
    stopped: bool = False


@dataclass
class _Analyzer:
    document: InspectionDocument
    tree: ast.Module
    selected_report_path: str
    imports: dict[str, str] = field(default_factory=dict)
    functions: dict[str, ast.FunctionDef] = field(default_factory=dict)
    global_env: dict[str, _Tracked] = field(default_factory=dict)
    versions: dict[str, int] = field(default_factory=dict)
    comparisons: dict[str, Eq] = field(default_factory=dict)
    selectors: dict[str, Selector] = field(default_factory=dict)
    folds: dict[str, Fold] = field(default_factory=dict)
    evidence: dict[str, EvidencePoint] = field(default_factory=dict)
    effects: list[Effect] = field(default_factory=list)
    writes: list[_WriteEvent] = field(default_factory=list)
    consumed_sequences: set[str] = field(default_factory=set)
    invalidated_origins: set[str] = field(default_factory=set)
    invalidated_bindings: set[str] = field(default_factory=set)
    call_stack: list[str] = field(default_factory=list)
    expression_depth: int = 0
    branch: str = "module"
    selected_sink_seen: bool = False
    report_fields: dict[str, _ReportField] = field(default_factory=dict)
    fail_closed: bool = False

    def analyze(self) -> OrientationCertificate | None:
        self._index_module()
        env: dict[str, _Tracked] = {}
        self.global_env = env
        self._exec_statements(self.tree.body, env, local=False)
        matching = [event for event in self.writes if self._is_selected_path(event.path)]
        self.selected_sink_seen = bool(matching)
        if not matching or self.fail_closed:
            return None
        sinks: list[SinkProof] = []
        orientations: list[frozenset[Orientation]] = []
        report_comparisons: set[str] = set()
        evidence_tokens: set[str] = set()
        for event in matching:
            payload = self._selected_result_payload(event.payload)
            if payload is None:
                return None
            if (
                payload.unknowns
                or payload.origins & self.invalidated_origins
                or payload.bindings & self.invalidated_bindings
            ):
                return None
            fold_tokens = payload.folds & self.folds.keys()
            selector_tokens = {
                selector
                for fold_token in fold_tokens
                for selector in self.folds[fold_token].selector_tokens
            }
            predicate_tokens = {
                self.selectors[token].predicate.expression.token
                for token in selector_tokens
                if token in self.selectors
            }
            if not fold_tokens or not selector_tokens or not predicate_tokens:
                return None
            # Completeness is computed independently from every tracked value
            # in the selected-result field set.  The sink lineage above comes
            # only from closed selector folds.  A direct/non-fold comparison,
            # or a competing fold, therefore makes the kernel's equality fail
            # instead of letting a nearby diagnostic count answer for the
            # selected result.
            report_comparisons.update(payload.predicates)
            evidence_tokens.update(predicate_tokens)
            path_orientations = {
                self._orientation(self.comparisons[token])
                for token in predicate_tokens
                if token in self.comparisons
            }
            if None in path_orientations:
                return None
            orientations.append(frozenset(item for item in path_orientations if item is not None))
            sinks.append(
                SinkProof(
                    path=event.path.normalized,
                    fold_tokens=frozenset(fold_tokens),
                    selector_tokens=frozenset(selector_tokens),
                    predicate_tokens=frozenset(predicate_tokens),
                    relevant_origins=payload.origins,
                    relevant_bindings=payload.bindings,
                )
            )
        comparisons = tuple(
            self.comparisons[token]
            for token in sorted(report_comparisons)
            if token in self.comparisons
        )
        selector_tokens = {token for sink in sinks for token in sink.selector_tokens}
        all_fold_tokens = {token for sink in sinks for token in sink.fold_tokens}
        return OrientationCertificate(
            source_path=self.document.path,
            comparisons=comparisons,
            selectors=tuple(self.selectors[token] for token in sorted(selector_tokens)),
            folds=tuple(self.folds[token] for token in sorted(all_fold_tokens)),
            sinks=tuple(sinks),
            reaching_path_orientations=tuple(orientations),
            effects=tuple(self.effects),
            all_report_comparison_tokens=frozenset(report_comparisons),
            dead_comparison_tokens=frozenset(),
            evidence=tuple(
                self.evidence[token] for token in sorted(evidence_tokens) if token in self.evidence
            ),
        )

    def _index_module(self) -> None:
        for statement in self.tree.body:
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    local = alias.asname or alias.name.split(".")[0]
                    self.imports[local] = alias.name if alias.asname else alias.name.split(".")[0]
            elif isinstance(statement, ast.ImportFrom):
                module = statement.module or ""
                for alias in statement.names:
                    self.imports[alias.asname or alias.name] = f"{module}.{alias.name}"
            elif isinstance(statement, ast.FunctionDef):
                self.functions[statement.name] = statement

    def _exec_statements(
        self, statements: list[ast.stmt], env: dict[str, _Tracked], *, local: bool
    ) -> _ExecResult:
        for statement in statements:
            result = self._exec_statement(statement, env, local=local)
            if result.stopped:
                return result
        return _ExecResult()

    def _exec_statement(
        self, statement: ast.stmt, env: dict[str, _Tracked], *, local: bool
    ) -> _ExecResult:
        if isinstance(statement, ast.Import | ast.ImportFrom):
            return _ExecResult()
        if isinstance(statement, ast.FunctionDef):
            if not local:
                self._bind(statement.name, self._tracked(_FunctionValue(statement.name)), env)
            return _ExecResult()
        if isinstance(statement, ast.Pass):
            return _ExecResult()
        if isinstance(statement, ast.Assign):
            value = self._eval(statement.value, env)
            if len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                self._bind(statement.targets[0].id, value, env)
            else:
                names = self._target_names(statement)
                self._give_up(statement, env, "unmodelled assignment", value)
                for name in names:
                    self._bind(name, self._unknown("unmodelled assignment", value), env)
            return _ExecResult()
        if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            left = env.get(statement.target.id, self._unknown("unbound augmented target"))
            right = self._eval(statement.value, env)
            value = self._binary(statement.op, left, right, statement)
            self._bind(statement.target.id, value, env)
            return _ExecResult()
        if isinstance(statement, ast.Expr):
            self._eval(statement.value, env)
            return _ExecResult()
        if isinstance(statement, ast.Return):
            value = (
                self._tracked(_NONE)
                if statement.value is None
                else self._eval(statement.value, env)
            )
            return _ExecResult(value, True)
        if isinstance(statement, ast.With):
            for item in statement.items:
                value = self._eval(item.context_expr, env)
                if isinstance(item.optional_vars, ast.Name):
                    self._bind(item.optional_vars.id, value, env)
                elif item.optional_vars is not None:
                    self._opaque_effect(
                        statement,
                        value,
                        writes=self._target_names(item.optional_vars),
                        reason="unmodelled with target",
                    )
            return self._exec_statements(statement.body, env, local=local)
        if isinstance(statement, ast.If) and self._is_main_guard(statement):
            return self._exec_statements(statement.body, env, local=local)
        if isinstance(statement, ast.If):
            condition = self._eval(statement.test, env)
            if isinstance(condition.value, _ExactBool):
                chosen = statement.body if condition.value.value else statement.orelse
                return self._exec_statements(chosen, env, local=local)
            writes = self._bound_names(statement.body + statement.orelse)
            touched = self._merge_tracked(
                [condition, *[env[name] for name in writes if name in env]]
            )
            self._give_up(statement, env, "unresolved control-flow join", touched)
            for name in writes:
                self._bind(name, self._unknown("unresolved control-flow join", touched), env)
            return _ExecResult()
        if isinstance(statement, ast.For):
            self._exec_for(statement, env, local=local)
            return _ExecResult()
        writes = self._bound_names([statement])
        reads = self._tracked_from_names(statement, env)
        self._give_up(statement, env, "unmodelled statement", reads)
        for name in writes:
            self._bind(name, self._unknown("unmodelled statement", reads), env)
        return _ExecResult()

    def _exec_for(self, statement: ast.For, env: dict[str, _Tracked], *, local: bool) -> None:
        iterable = self._eval(statement.iter, env)
        sequence = iterable.value
        if not isinstance(sequence, _SequenceState) or statement.orelse:
            touched = self._merge_tracked([iterable, self._tracked_from_names(statement, env)])
            writes = self._bound_names(statement.body + statement.orelse)
            self._give_up(statement, env, "unresolved loop", touched)
            for name in writes:
                self._bind(name, self._unknown("unresolved loop", touched), env)
            return
        if self._loop_has_unsupported_control(statement):
            touched = self._merge_tracked([iterable, self._tracked_from_names(statement, env)])
            writes = self._bound_names(statement.body)
            self._give_up(statement, env, "unsupported loop control transfer", touched)
            for name in writes:
                self._bind(name, self._unknown("unsupported loop control transfer", touched), env)
            return
        if sequence.single_pass and not self._consume(sequence):
            touched = self._merge_tracked([iterable])
            self._give_up(statement, env, "reconsumed iterator", touched)
            return
        if not isinstance(statement.target, ast.Name):
            touched = self._merge_tracked([iterable])
            self._give_up(statement, env, "unmodelled loop target", touched)
            return
        before = dict(env)
        element = sequence.semantic.element_value
        if not isinstance(element, _Tracked):
            self._give_up(statement, env, "invalid loop element", iterable)
            return
        self._bind(
            statement.target.id, replace(element, index_map=sequence.semantic.index_map), env
        )
        assigned = self._bound_names(statement.body)
        if not self._loop_bindings_are_sound(statement, before, assigned):
            touched = self._merge_tracked([iterable, self._tracked_from_names(statement, env)])
            self._give_up(statement, env, "unsupported loop-carried binding", touched)
            for name in assigned:
                self._bind(name, self._unknown("unsupported loop-carried binding", touched), env)
            return
        for name in assigned:
            if name in before and name != statement.target.id:
                seed = before[name]
                operation: Literal["sum", "product"] | None = None
                if _is_zero(seed.value):
                    operation = "sum"
                elif _is_one(seed.value):
                    operation = "product"
                if operation is not None:
                    env[name] = replace(
                        seed,
                        value=_AccumulatorValue(
                            name,
                            sequence.row_domain,
                            sequence.semantic.index_map,
                            seed.value,  # type: ignore[arg-type]
                            operation,
                        ),
                    )
        self._exec_statements(statement.body, env, local=local)
        for name in assigned:
            value = env.get(name)
            if value is None:
                continue
            if isinstance(value.value, _AccumulatorValue):
                env[name] = before.get(name, self._unknown("unmodified accumulator"))
            elif name not in before or name == statement.target.id:
                # CSV and other symbolic sequences may be empty.  A loop-local
                # or target value is therefore not available after the loop.
                self._bind(name, self._unknown("possibly empty loop binding", value), env)

    def _eval(self, node: ast.expr, env: dict[str, _Tracked]) -> _Tracked:
        if self.expression_depth >= _MAX_EXPRESSION_DEPTH:
            result = self._unknown("expression depth exceeded")
            self._give_up(node, env, "expression depth exceeded", result)
            return result
        self.expression_depth += 1
        try:
            result = self._eval_inner(node, env)
        except (ArithmeticError, InvalidOperation, ValueError, TypeError, OverflowError):
            result = self._unknown("primitive evaluation failed")
        finally:
            self.expression_depth -= 1
        if isinstance(result.value, Unknown):
            self._give_up(node, env, result.value.reason, result)
        return result

    def _eval_inner(self, node: ast.expr, env: dict[str, _Tracked]) -> _Tracked:
        if isinstance(node, ast.Name):
            if node.id == "__file__":
                return self._tracked(_PathValue(tuple(PurePosixPath(self.document.path).parts)))
            value = env.get(node.id)
            if value is not None:
                return value.with_binding(node.id)
            origin = self.imports.get(node.id)
            if origin is not None:
                return self._tracked(_ModuleValue(origin))
            return self._unknown(f"unbound name:{node.id}")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return self._tracked(_ExactBool(node.value))
            if node.value is None:
                return self._tracked(_NONE)
            if isinstance(node.value, str):
                return self._tracked(_ExactString(node.value))
            if isinstance(node.value, int):
                if node.value.bit_length() > _MAX_EXACT_INTEGER_BITS:
                    return self._unknown("integer magnitude exceeded")
                return self._tracked(_number(node.value))
            if isinstance(node.value, float) and math.isfinite(node.value):
                return self._tracked(_number(node.value))
            return self._unknown("unsupported constant")
        if isinstance(node, ast.List | ast.Tuple):
            items = tuple(self._eval(item, env) for item in node.elts)
            return self._compose(_ContainerValue(items), items)
        if isinstance(node, ast.Dict):
            return self._eval_dict(node, env)
        if isinstance(node, ast.Attribute):
            return self._eval_attribute(node, env)
        if isinstance(node, ast.Subscript):
            return self._eval_subscript(node, env)
        if isinstance(node, ast.Call):
            return self._eval_call(node, env)
        if isinstance(node, ast.UnaryOp):
            operand_value = self._eval(node.operand, env)
            if isinstance(node.op, ast.USub):
                return self._exact_unary(operator.neg, operand_value)
            if isinstance(node.op, ast.UAdd):
                return self._exact_unary(operator.pos, operand_value)
            if isinstance(node.op, ast.Not):
                return self._logical_not(operand_value, node)
            return self._unknown("unsupported unary operation", operand_value)
        if isinstance(node, ast.BinOp):
            return self._binary(
                node.op, self._eval(node.left, env), self._eval(node.right, env), node
            )
        if isinstance(node, ast.Compare):
            return self._compare(node, env)
        if isinstance(node, ast.IfExp):
            return self._if_expression(node, env)
        if isinstance(node, ast.ListComp | ast.GeneratorExp):
            return self._comprehension(node, env)
        if isinstance(node, ast.JoinedStr):
            return self._eval_joined_string(node, env)
        if isinstance(node, ast.FormattedValue):
            parts = [self._eval(node.value, env)]
            if node.format_spec is not None:
                parts.append(self._eval(node.format_spec, env))
            return self._compose(_TextValue(), parts)
        return self._unknown(f"unsupported expression:{type(node).__name__}")

    def _eval_joined_string(self, node: ast.JoinedStr, env: dict[str, _Tracked]) -> _Tracked:
        parts: list[_Tracked] = []
        field_tokens: list[str] = []
        selected_line = False
        for item in node.values:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                part = self._tracked(_ExactString(item.value))
                parts.append(part)
                tail = item.value.rsplit("\n", 1)[-1]
                if "\n" in item.value:
                    selected_line = "[selected-result]" in tail
                elif "[selected-result]" in item.value:
                    selected_line = True
                continue
            if isinstance(item, ast.FormattedValue):
                value = self._eval(item.value, env)
                parts.append(value)
                if item.format_spec is not None:
                    parts.append(self._eval(item.format_spec, env))
                token = self._node_token(item, "report-field")
                self.report_fields[token] = _ReportField(value, selected_line)
                field_tokens.append(token)
                continue
            value = self._eval(item, env)
            parts.append(value)
        return self._compose(_TextValue(tuple(field_tokens)), parts)

    def _eval_dict(self, node: ast.Dict, env: dict[str, _Tracked]) -> _Tracked:
        if len(node.keys) == 1 and node.keys[0] is None:
            spread = self._eval(node.values[0], env)
            if isinstance(spread.value, _RowValue):
                return spread
        values = [self._eval(value, env) for value in node.values]
        return self._unknown("dictionary construction is not an identity row copy", *values)

    def _eval_attribute(self, node: ast.Attribute, env: dict[str, _Tracked]) -> _Tracked:
        base = self._eval(node.value, env)
        if isinstance(base.value, _PathValue):
            if node.attr == "parent":
                return replace(base, value=_PathValue(base.value.parts[:-1], base.value.exact))
        if node.attr in {"numerator", "denominator"}:
            return self._compose(_DerivedValue(node.attr), [base])
        if isinstance(base.value, _ModuleValue):
            return self._tracked(_ModuleValue(f"{base.value.origin}.{node.attr}"))
        return self._unknown(f"unsupported attribute:{node.attr}", base)

    def _eval_subscript(self, node: ast.Subscript, env: dict[str, _Tracked]) -> _Tracked:
        base = self._eval(node.value, env)
        index = self._eval(node.slice, env)
        if isinstance(base.value, _RowValue) and isinstance(index.value, _ExactString):
            transform = PrimitiveTransform("csv_subscript", "row", "str", 0)
            projection = Projection(
                asset=base.value.asset,
                row_domain=base.value.row_domain,
                column=index.value.value,
                parity=0,
                runtime_type="str",
                transforms=(transform,),
            )
            projected = self._compose(
                projection,
                [base, index],
                origins={base.value.asset, base.value.row_domain},
                index_map=base.value.index_map,
            )
            self._record_transform_domain_effect(
                projection,
                "csv_subscript may be absent or None for a ragged DictReader row",
            )
            return projected
        if isinstance(base.value, _SequenceState) and isinstance(index.value, _IndexValue):
            if index.value.index_map != base.value.semantic.index_map:
                return self._unknown("misaligned sequence index", base, index)
            element = base.value.semantic.element_value
            if isinstance(element, _Tracked):
                return self._compose(
                    element.value,
                    [base, index, element],
                    index_map=base.value.semantic.index_map,
                )
        if isinstance(base.value, _PairValue | _ContainerValue):
            numeric = _exact_integer(index.value)
            if numeric is not None and 0 <= numeric < len(base.value.items):
                item = base.value.items[numeric]
                return self._compose(item.value, [base, index, item], index_map=item.index_map)
            predicate = self._predicate_of(index, exact_index=True)
            if predicate is not None and len(base.value.items) == 2:
                return self._dependent(
                    predicate,
                    base.value.items[0],
                    base.value.items[1],
                    node,
                    parents=[base, index],
                )
        return self._unknown("unsupported subscript", base, index)

    def _eval_call(self, node: ast.Call, env: dict[str, _Tracked]) -> _Tracked:
        key = self._call_key(node.func)
        function_value = self._eval(node.func, env) if isinstance(node.func, ast.Name) else None
        if function_value is not None and isinstance(function_value.value, _FunctionValue):
            return self._call_helper(function_value.value.name, node, env)
        if isinstance(node.func, ast.Name) and node.func.id in env:
            # The indexed definition is not runtime authority: any live
            # reassignment makes dispatch opaque.
            key = ""
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in env
        ):
            key = ""
        args = [self._eval(argument, env) for argument in node.args]
        keywords = {item.arg: self._eval(item.value, env) for item in node.keywords if item.arg}
        if any(item.arg is None for item in node.keywords):
            return self._unknown("starred call arguments", *args, *keywords.values())
        if key in {"Path", "pathlib.Path", "PurePath", "pathlib.PurePath"} and not keywords:
            return self._path_constructor(args)
        if key in {"Fraction", "fractions.Fraction"} and not keywords:
            return self._numeric_constructor("fraction", args)
        if key in {"Decimal", "decimal.Decimal"} and not keywords:
            return self._numeric_constructor("decimal", args)
        if key in {"int", "float", "str", "bool"} and not keywords:
            return self._builtin_cast(key, args, node)
        if key == "abs" and len(args) == 1 and not keywords:
            return self._absolute(node.args[0], args[0], env)
        if (
            key == "len"
            and len(args) == 1
            and not keywords
            and isinstance(args[0].value, _SequenceState)
        ):
            sequence = args[0].value
            return self._compose(
                _LengthValue(sequence.semantic.index_map, sequence.row_domain), args
            )
        if key == "len" and len(args) == 1 and not keywords:
            if isinstance(args[0].value, (_ContainerValue, _ExactString, _TextValue)):
                return self._compose(_DerivedValue("len"), args)
            return self._unknown("len operand is not an exact builtin container", *args)
        if (
            key == "range"
            and len(args) == 1
            and not keywords
            and isinstance(args[0].value, _LengthValue)
        ):
            length = args[0].value
            element = self._tracked(
                _IndexValue(length.index_map, length.row_domain), index_map=length.index_map
            )
            sequence = _SequenceState(
                Sequence(length.index_map, element),
                length.row_domain,
                self._node_token(node, "range"),
            )
            return self._compose(sequence, args, index_map=length.index_map)
        if (
            key == "list"
            and len(args) == 1
            and not keywords
            and isinstance(args[0].value, _SequenceState)
        ):
            sequence = args[0].value
            if sequence.single_pass and not self._consume(sequence):
                return self._unknown("reconsumed iterator", args[0])
            materialized = replace(
                sequence,
                token=self._node_token(node, "list"),
                single_pass=False,
            )
            return self._compose(materialized, args, index_map=sequence.semantic.index_map)
        if key == "open" and args:
            opened_path = self._path_from_value(args[0].value)
            if opened_path is None:
                self._opaque_effect(
                    node,
                    self._merge_tracked(args + list(keywords.values())),
                    writes={"*"},
                    reason="open on unresolved path",
                )
                return self._unknown("open path is not exact", *args, *keywords.values())
            mode = "r"
            if len(args) > 1 and isinstance(args[1].value, _ExactString):
                mode = args[1].value.value
            elif "mode" in keywords and isinstance(keywords["mode"].value, _ExactString):
                mode = keywords["mode"].value.value
            handle = self._compose(_FileHandle(opened_path, mode), args + list(keywords.values()))
            if self._is_write_mode(mode) and self._is_selected_path(opened_path):
                self._opaque_effect(
                    node,
                    handle,
                    writes={"*"},
                    reason="selected report opened in a mutating mode",
                )
            return handle
        if key == "csv.DictReader" and len(args) == 1 and not keywords:
            source = args[0].value
            path: _PathValue | None = None
            if isinstance(source, _InputLines):
                path = source.path
            elif isinstance(source, _FileHandle) and not self._is_write_mode(source.mode):
                path = source.path
            if path is None:
                return self._unknown("csv reader input is not bound to an exact path", *args)
            asset = path.normalized
            row_domain = semantic_digest(
                {
                    "asset": asset,
                    "path": self.document.path,
                    "line": getattr(node, "lineno", 0),
                    "reader": key,
                }
            )
            index_map = semantic_digest({"row_domain": row_domain, "order": "csv"})
            row = self._tracked(
                _RowValue(asset, row_domain, index_map),
                index_map=index_map,
            )
            row = replace(row, origins=frozenset({asset, row_domain}))
            state = _SequenceState(
                Sequence(index_map, row),
                row_domain,
                self._node_token(node, "csv-reader"),
                single_pass=True,
            )
            return self._compose(
                state,
                args,
                origins={asset, row_domain},
                index_map=index_map,
            )
        if (
            key == "dict"
            and len(args) == 1
            and not keywords
            and isinstance(args[0].value, _RowValue)
        ):
            return args[0]
        if key == "zip" and len(args) == 2 and not keywords:
            return self._zip(args, node)
        if key in {"sum", "prod", "math.prod"} and len(args) == 1 and not keywords:
            operation: Literal["sum", "product"] = "product" if "prod" in key else "sum"
            return self._fold_call(args[0], operation, node)
        if key == "print":
            target = keywords.get("file")
            if target is not None:
                if isinstance(target.value, _FileHandle) and args:
                    self.writes.append(_WriteEvent(target.value.path, args[0], self.branch))
                else:
                    self._opaque_effect(
                        node,
                        self._merge_tracked(args + list(keywords.values())),
                        writes={"*"},
                        reason="print target is not an exact file handle",
                    )
            return self._compose(_NONE, args + list(keywords.values()))
        if key == "json.dump" and len(args) >= 2:
            if isinstance(args[1].value, _FileHandle):
                self.writes.append(_WriteEvent(args[1].value.path, args[0], self.branch))
                return self._compose(_NONE, args + list(keywords.values()))
            self._opaque_effect(
                node,
                self._merge_tracked(args + list(keywords.values())),
                writes={"*"},
                reason="json.dump target is not an exact file handle",
            )
            return self._unknown("json.dump target is not exact", *args)
        if isinstance(node.func, ast.Attribute):
            return self._method_call(node, env, args, keywords)
        tracked = self._merge_tracked(args + list(keywords.values()))
        pure_stdlib = key.startswith(("statistics.", "math."))
        if pure_stdlib:
            return self._unknown(f"unmodelled stdlib call:{key}", tracked)
        # An unmodelled call into an allowlisted module can still alter global
        # process state used by the certified slice (for example decimal
        # context or CSV parser limits).  With no operation summary, that is
        # an all-bindings effect, even when its arguments are unrelated.
        self._opaque_effect(
            node,
            tracked,
            writes={"*"},
            reason=f"opaque call:{key or 'dynamic'}",
        )
        return self._unknown(f"opaque call:{key or 'dynamic'}", tracked)

    def _method_call(
        self,
        node: ast.Call,
        env: dict[str, _Tracked],
        args: list[_Tracked],
        keywords: dict[str, _Tracked],
    ) -> _Tracked:
        assert isinstance(node.func, ast.Attribute)
        receiver = self._eval(node.func.value, env)
        method = node.func.attr
        all_values = [receiver, *args, *keywords.values()]
        if isinstance(receiver.value, _PathValue):
            if method in {"resolve", "absolute", "expanduser"} and not args:
                return self._unknown(f"runtime-dependent path normalization:{method}", receiver)
            if method == "mkdir":
                return self._compose(_NONE, all_values)
            if method == "read_text":
                return self._compose(_InputText(receiver.value), all_values)
            if method == "open":
                mode = "r"
                if args and isinstance(args[0].value, _ExactString):
                    mode = args[0].value.value
                elif args:
                    return self._unknown("Path.open mode is not exact", *all_values)
                elif "mode" in keywords and isinstance(keywords["mode"].value, _ExactString):
                    mode = keywords["mode"].value.value
                elif "mode" in keywords:
                    return self._unknown("Path.open mode is not exact", *all_values)
                handle = self._compose(_FileHandle(receiver.value, mode), all_values)
                if self._is_write_mode(mode) and self._is_selected_path(receiver.value):
                    self._opaque_effect(
                        node,
                        handle,
                        writes={"*"},
                        reason="selected report opened in a mutating mode",
                    )
                return handle
            if method in {"write_text", "write", "writelines"} and args:
                self.writes.append(_WriteEvent(receiver.value, args[0], self.branch))
                return self._compose(_DerivedValue("write_length"), all_values)
        if isinstance(receiver.value, _InputText) and method == "splitlines":
            return self._compose(_InputLines(receiver.value.path), all_values)
        if isinstance(receiver.value, _FileHandle):
            if method == "close":
                return self._compose(_NONE, all_values)
            if method in {"write", "writelines"} and args:
                self.writes.append(_WriteEvent(receiver.value.path, args[0], self.branch))
                return self._compose(_DerivedValue("write_length"), all_values)
        if isinstance(receiver.value, _ExactString) and method in {"join", "format"}:
            field_tokens: list[str] = []
            if method == "join" and len(args) == 1 and isinstance(args[0].value, _ContainerValue):
                if not all(
                    isinstance(item.value, (_ExactString, _TextValue))
                    for item in args[0].value.items
                ):
                    return self._unknown("join item is not proven text", *all_values)
                for item in args[0].value.items:
                    if isinstance(item.value, _TextValue):
                        field_tokens.extend(item.value.field_tokens)
            elif method == "format":
                return self._unknown("str.format placeholder binding is not modelled", *all_values)
            return self._compose(_TextValue(tuple(field_tokens)), all_values)
        if method in {"quantize"}:
            return self._unknown("decimal quantize is context-dependent", *all_values)
        if (
            method in {"strip", "lstrip", "rstrip"}
            and not args
            and not keywords
            and isinstance(receiver.value, (Projection, _ExactString))
        ):
            if isinstance(receiver.value, Projection) and receiver.value.runtime_type == "str":
                projection = self._transform_projection(
                    receiver.value, "whitespace_strip", "str", 0
                )
                return self._compose(projection, all_values, index_map=receiver.index_map)
            assert isinstance(receiver.value, _ExactString)
            stripped = getattr(receiver.value.value, method)()
            return self._compose(_ExactString(stripped), all_values)
        tracked = self._merge_tracked(all_values)
        sink_mutation = method in {
            "write",
            "writelines",
            "write_text",
            "rename",
            "replace",
            "unlink",
            "touch",
            "truncate",
        }
        if sink_mutation and (
            not isinstance(receiver.value, _PathValue) or self._is_selected_path(receiver.value)
        ):
            self._opaque_effect(
                node,
                tracked,
                writes={"*"},
                reason=f"unresolved report mutation:{method}",
            )
            return self._unknown(f"unresolved report mutation:{method}", tracked)
        mutating = method in {
            "append",
            "extend",
            "insert",
            "clear",
            "update",
            "pop",
            "remove",
            "setdefault",
            "sort",
            "reverse",
        }
        aliases = tracked.origins if mutating else frozenset()
        self.effects.append(
            Effect(
                reads=tracked.origins | tracked.bindings | self._syntactic_reads(node),
                writes=frozenset({"*"}),
                aliases=frozenset(aliases),
                may_raise=True,
                opaque=True,
                reason=f"opaque method:{method}",
            )
        )
        self.fail_closed = True
        self.invalidated_origins.update(aliases)
        self.invalidated_bindings.update(tracked.bindings)
        return self._unknown(f"opaque method:{method}", tracked)

    def _call_helper(self, name: str, node: ast.Call, env: dict[str, _Tracked]) -> _Tracked:
        function = self.functions.get(name)
        if function is None or len(self.call_stack) >= _MAX_CALL_DEPTH or name in self.call_stack:
            self._opaque_effect(
                node,
                self._tracked_from_names(node, env),
                writes={"*"},
                reason="recursive or unavailable helper",
            )
            return self._unknown("recursive or unavailable helper")
        parameters = [
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ]
        if function.args.vararg or function.args.kwarg:
            self._opaque_effect(
                node,
                self._tracked_from_names(node, env),
                writes={"*"},
                reason="variadic helper",
            )
            return self._unknown("variadic helper")
        arguments = [self._eval(argument, env) for argument in node.args]
        bound: dict[str, _Tracked] = {}
        for parameter, value in zip(parameters, arguments, strict=False):
            bound[parameter.arg] = value
        for keyword in node.keywords:
            if keyword.arg is None or keyword.arg in bound:
                return self._unknown("unsupported helper argument binding", *arguments)
            if keyword.arg not in {item.arg for item in parameters}:
                return self._unknown("unknown helper keyword", *arguments)
            bound[keyword.arg] = self._eval(keyword.value, env)
        defaults = list(function.args.defaults)
        for parameter, default in zip(parameters[-len(defaults) :], defaults, strict=False):
            if parameter.arg not in bound:
                if not self._static_helper_default(default):
                    return self._unknown("non-literal helper default", *arguments)
                bound[parameter.arg] = self._eval(default, env)
        if set(bound) != {item.arg for item in parameters}:
            return self._unknown("incomplete helper binding", *arguments)
        previous_branch = self.branch
        self.branch = f"{previous_branch}/{name}@{getattr(node, 'lineno', 0)}"
        local_env = dict(self.global_env)
        self.call_stack.append(name)
        try:
            for parameter in parameters:
                self._bind(parameter.arg, bound[parameter.arg], local_env)
            result = self._exec_statements(function.body, local_env, local=True)
        finally:
            self.branch = previous_branch
            self.call_stack.pop()
        if result.returned is None:
            return self._tracked(_NONE)
        return result.returned

    def _comprehension(
        self, node: ast.ListComp | ast.GeneratorExp, env: dict[str, _Tracked]
    ) -> _Tracked:
        if len(node.generators) != 1:
            return self._unknown("multiple comprehension generators")
        generator = node.generators[0]
        source = self._eval(generator.iter, env)
        sequence = source.value
        if not isinstance(sequence, _SequenceState) or not isinstance(generator.target, ast.Name):
            return self._unknown("unresolved comprehension source", source)
        if generator.ifs or generator.is_async:
            return self._unknown("filtered or asynchronous comprehension", source)
        if sequence.single_pass and not self._consume(sequence):
            return self._unknown("reconsumed iterator", source)
        local_env = dict(env)
        element = sequence.semantic.element_value
        if not isinstance(element, _Tracked):
            return self._unknown("invalid sequence element", source)
        self._bind(
            generator.target.id,
            replace(element, index_map=sequence.semantic.index_map),
            local_env,
        )
        built = self._eval(node.elt, local_env)
        token = self._node_token(node, "sequence")
        state = _SequenceState(
            Sequence(sequence.semantic.index_map, built),
            sequence.row_domain,
            token,
            single_pass=isinstance(node, ast.GeneratorExp),
        )
        return self._compose(state, [source, built], index_map=sequence.semantic.index_map)

    def _compare(self, node: ast.Compare, env: dict[str, _Tracked]) -> _Tracked:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            return self._unknown("chained comparison")
        left = self._eval(node.left, env)
        right = self._eval(node.comparators[0], env)
        if isinstance(node.ops[0], ast.Eq):
            if isinstance(left.value, Projection) and isinstance(right.value, Projection):
                index_map = left.index_map if left.index_map == right.index_map else None
                if index_map is None:
                    return self._unknown("misaligned projection equality", left, right)
                payload = {
                    "path": self.document.path,
                    "line": getattr(node, "lineno", 0),
                    "left": repr(left.value),
                    "right": repr(right.value),
                    "index_map": index_map,
                }
                token = semantic_digest(payload)
                comparison = Eq(left.value, right.value, index_map, token)
                self.comparisons[token] = comparison
                self.evidence[token] = self._evidence_point(node)
                return self._compose(
                    Predicate(comparison),
                    [left, right],
                    predicates={token},
                    index_map=index_map,
                )
            exact = _exact_compare(left.value, right.value)
            if exact is not None:
                return self._compose(_ExactBool(exact), [left, right])
        return self._unknown("unsupported comparison", left, right)

    def _if_expression(self, node: ast.IfExp, env: dict[str, _Tracked]) -> _Tracked:
        test = self._eval(node.test, env)
        if isinstance(test.value, _ExactBool):
            chosen = self._eval(node.body if test.value.value else node.orelse, env)
            return self._compose(chosen.value, [test, chosen], index_map=chosen.index_map)
        predicate = self._predicate_of(test)
        if predicate is None:
            return self._unknown("non-predicate conditional", test)
        return self._dependent(
            predicate,
            self._eval(node.orelse, env),
            self._eval(node.body, env),
            node,
            parents=[test],
        )

    def _binary(self, op: ast.operator, left: _Tracked, right: _Tracked, node: ast.AST) -> _Tracked:
        if (
            isinstance(op, ast.Div)
            and isinstance(left.value, _PathValue)
            and isinstance(right.value, _ExactString)
        ):
            return self._compose(
                _PathValue((*left.value.parts, right.value.value), left.value.exact), [left, right]
            )
        if (
            isinstance(op, ast.Add)
            and isinstance(left.value, (_ExactString, _TextValue))
            and isinstance(right.value, (_ExactString, _TextValue))
        ):
            field_tokens = (
                left.value.field_tokens if isinstance(left.value, _TextValue) else ()
            ) + (right.value.field_tokens if isinstance(right.value, _TextValue) else ())
            return self._compose(_TextValue(field_tokens), [left, right])
        projection = self._projection_binary(op, left, right)
        if projection is not None:
            return projection
        if isinstance(left.value, _AccumulatorValue):
            operation: Literal["sum", "product"] | None
            if isinstance(op, ast.Add):
                operation = "sum"
            elif isinstance(op, ast.Mult):
                operation = "product"
            else:
                operation = None
            if operation is not None and operation == left.value.operation:
                if right.selectors:
                    return self._make_fold(left.value, right, operation, node)
            if operation == left.value.operation:
                return self._compose(_DerivedValue(f"non-selector-{operation}"), [left, right])
        if isinstance(right.value, _AccumulatorValue) and isinstance(op, ast.Add):
            if right.value.operation == "sum" and left.selectors:
                return self._make_fold(right.value, left, "sum", node)
            if right.value.operation == "sum":
                return self._compose(_DerivedValue("non-selector-sum"), [left, right])
        if isinstance(op, ast.Mult):
            selector_tokens = left.selectors | right.selectors
            projection_operand = (
                left
                if isinstance(left.value, Projection)
                else right
                if isinstance(right.value, Projection)
                else None
            )
            if selector_tokens and projection_operand is not None:
                gated_projection = projection_operand.value
                assert isinstance(gated_projection, Projection)
                comparisons = [
                    self.selectors[token].predicate.expression
                    for token in selector_tokens
                    if token in self.selectors
                ]
                if (
                    len(comparisons) == len(selector_tokens)
                    and all(
                        item.left.row_domain == gated_projection.row_domain
                        and item.index_map == projection_operand.index_map
                        for item in comparisons
                    )
                    and projection_operand.index_map is not None
                ):
                    return self._compose(
                        Gated(
                            gated_projection,
                            gated_projection.row_domain,
                            projection_operand.index_map,
                            selector_tokens,
                        ),
                        [left, right],
                    )
        dependent = self._lift_dependent(op, left, right, node)
        if dependent is not None:
            return dependent
        exact = _exact_binary(op, left.value, right.value)
        if exact is not None:
            return self._compose(exact, [left, right])
        if isinstance(op, ast.Pow):
            return self._unknown("power is not within the exact arithmetic budget", left, right)
        if isinstance(op, (ast.Div, ast.FloorDiv, ast.Mod)):
            return self._unknown("division domain is not proven", left, right)
        if isinstance(left.value, ExactNumber) and isinstance(right.value, ExactNumber):
            return self._unknown("exact arithmetic is not within the supported domain", left, right)
        if left.folds or right.folds or left.selectors or right.selectors:
            return self._compose(_DerivedValue(type(op).__name__), [left, right])
        if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
            return self._compose(_DerivedValue(type(op).__name__), [left, right])
        return self._unknown(f"unsupported binary operation:{type(op).__name__}", left, right)

    def _projection_binary(
        self, op: ast.operator, left: _Tracked, right: _Tracked
    ) -> _Tracked | None:
        one_left = _is_one(left.value)
        one_right = _is_one(right.value)
        if isinstance(op, ast.Sub) and one_left and isinstance(right.value, Projection):
            if right.value.runtime_type in _NUMERIC_RUNTIME_TYPES:
                projection = self._transform_projection(
                    right.value, "one_minus", right.value.runtime_type, 1
                )
                return self._compose(projection, [left, right], index_map=right.index_map)
        if isinstance(op, ast.BitXor):
            projection_value = right if one_left else left if one_right else None
            if projection_value is not None and isinstance(projection_value.value, Projection):
                if projection_value.value.runtime_type == "int":
                    projection = self._transform_projection(
                        projection_value.value, "bitxor_one", "int", 1
                    )
                    return self._compose(
                        projection, [left, right], index_map=projection_value.index_map
                    )
        return None

    def _logical_not(self, value: _Tracked, node: ast.AST) -> _Tracked:
        predicate = self._predicate_of(value)
        if predicate is not None:
            false = self._tracked(self._number(1))
            true = self._tracked(self._number(0))
            return self._dependent(predicate, false, true, node, parents=[value])
        if isinstance(value.value, _ExactBool):
            return self._compose(_ExactBool(not value.value.value), [value])
        if isinstance(value.value, Projection) and value.value.runtime_type in (
            _NUMERIC_RUNTIME_TYPES | {"bool"}
        ):
            projection = self._transform_projection(value.value, "boolean_not", "bool", 1)
            return self._compose(projection, [value], index_map=value.index_map)
        return self._unknown("unsupported logical not", value)

    def _absolute(
        self,
        argument_node: ast.expr,
        value: _Tracked,
        env: dict[str, _Tracked],
    ) -> _Tracked:
        if isinstance(argument_node, ast.BinOp) and isinstance(argument_node.op, ast.Sub):
            # Re-evaluate the two children so the exact one/projection roles are explicit.
            left = self._eval(argument_node.left, env)
            right = self._eval(argument_node.right, env)
            projection_value = (
                right if _is_one(left.value) else left if _is_one(right.value) else None
            )
            if projection_value is not None and isinstance(projection_value.value, Projection):
                projection = projection_value.value
                if projection.runtime_type in _NUMERIC_RUNTIME_TYPES:
                    shifted = self._transform_projection(
                        projection,
                        "abs_difference_one",
                        projection.runtime_type,
                        1,
                    )
                    return self._compose(shifted, [value], index_map=projection_value.index_map)
        exact = _exact_unary_value(abs, value.value)
        return (
            self._compose(exact, [value])
            if exact is not None
            else self._unknown("unsupported abs", value)
        )

    def _lift_dependent(
        self, op: ast.operator, left: _Tracked, right: _Tracked, node: ast.AST
    ) -> _Tracked | None:
        left_dep = self._as_dependent(left)
        right_dep = self._as_dependent(right)
        if left_dep is None and right_dep is None:
            return None
        predicates = {
            item.predicate.expression.token for item in (left_dep, right_dep) if item is not None
        }
        if len(predicates) != 1:
            return self._unknown("selector depends on multiple predicates", left, right)
        predicate = left_dep.predicate if left_dep is not None else right_dep.predicate  # type: ignore[union-attr]
        left_false = left_dep.false_value if left_dep is not None else left.value
        left_true = left_dep.true_value if left_dep is not None else left.value
        right_false = right_dep.false_value if right_dep is not None else right.value
        right_true = right_dep.true_value if right_dep is not None else right.value
        false = _exact_binary(op, left_false, right_false)
        true = _exact_binary(op, left_true, right_true)
        if false is None or true is None:
            return self._unknown("selector branch is not exact numeric", left, right)
        return self._dependent(
            predicate,
            self._tracked(false),
            self._tracked(true),
            node,
            parents=[left, right],
        )

    def _dependent(
        self,
        predicate: Predicate,
        false: _Tracked,
        true: _Tracked,
        node: ast.AST,
        *,
        parents: list[_Tracked],
    ) -> _Tracked:
        if not isinstance(false.value, ExactNumber) or not isinstance(true.value, ExactNumber):
            return self._unknown("selector branch is not an exact number", false, true)
        combined = [false, true, *parents]
        dependent = _DependentValue(predicate, false.value, true.value)
        false_fraction = _number_fraction(false.value)
        true_fraction = _number_fraction(true.value)
        if (
            false.value.number_type != true.value.number_type
            or false_fraction is None
            or true_fraction is None
            or true_fraction <= false_fraction
        ):
            return self._compose(
                dependent,
                combined,
                predicates={predicate.expression.token},
            )
        token = semantic_digest(
            {
                "predicate": predicate.expression.token,
                "false": {
                    "type": false.value.number_type,
                    "value": false.value.value,
                },
                "true": {
                    "type": true.value.number_type,
                    "value": true.value.value,
                },
                "path": self.document.path,
                "line": getattr(node, "lineno", 0),
                "column": getattr(node, "col_offset", 0),
            }
        )
        selector = Selector(predicate, false.value, true.value, token)
        self.selectors[token] = selector
        return replace(
            self._compose(
                selector,
                combined,
                predicates={predicate.expression.token},
            ),
            # The selector for the complete expression supersedes selectors
            # produced by its algebraic subexpressions.  Keeping both would
            # falsely describe intermediate values as independent fold
            # elements rather than proof steps for this one producer.
            selectors=frozenset({token}),
        )

    def _as_dependent(self, value: _Tracked) -> _DependentValue | None:
        if isinstance(value.value, _DependentValue):
            return value.value
        if isinstance(value.value, Selector):
            return _DependentValue(
                value.value.predicate, value.value.false_value, value.value.true_value
            )
        if isinstance(value.value, Predicate):
            return _DependentValue(
                value.value,
                self._number(0),
                self._number(1),
            )
        return None

    def _predicate_of(self, value: _Tracked, *, exact_index: bool = False) -> Predicate | None:
        if isinstance(value.value, Predicate):
            return value.value
        dependent = self._as_dependent(value)
        if dependent is not None:
            false = _number_fraction(dependent.false_value)
            true = _number_fraction(dependent.true_value)
            if false != 0:
                return None
            if exact_index:
                if (
                    dependent.false_value.number_type == "int"
                    and dependent.true_value.number_type == "int"
                    and true == 1
                ):
                    return dependent.predicate
                return None
            if true is not None and true != 0:
                return dependent.predicate
        return None

    def _builtin_cast(self, key: str, args: list[_Tracked], node: ast.AST) -> _Tracked:
        if len(args) != 1:
            return self._unknown(f"unsupported {key} arity", *args)
        value = args[0]
        if key in {"int", "bool"}:
            predicate = self._predicate_of(value, exact_index=key == "int")
            if predicate is not None:
                return self._dependent(
                    predicate,
                    self._tracked(self._number(0)),
                    self._tracked(self._number(1)),
                    node,
                    parents=args,
                )
        if isinstance(value.value, Projection):
            projection = value.value
            if key == "int" and projection.runtime_type in {"str", "bool", "int"}:
                transformed = self._transform_projection(projection, "builtin_int", "int", 0)
                return self._compose(transformed, args, index_map=value.index_map)
            if key == "float" and projection.runtime_type in {"str", "bool", "int", "float"}:
                transformed = self._transform_projection(projection, "builtin_float", "float", 0)
                return self._compose(transformed, args, index_map=value.index_map)
            if key == "str":
                transformed = self._transform_projection(projection, "builtin_str", "str", 0)
                return self._compose(transformed, args, index_map=value.index_map)
        if isinstance(value.value, ExactNumber):
            converted = _convert_number(value.value, key)
            if converted is not None:
                return self._compose(converted, args)
        if value.folds or value.selectors:
            return self._unknown(f"{key} cast domain is not proven", *args)
        if key == "str" and isinstance(value.value, _ExactString):
            return value
        return self._unknown(f"unsupported {key} cast", value)

    def _numeric_constructor(self, kind: str, args: list[_Tracked]) -> _Tracked:
        if any(item.folds or item.selectors for item in args):
            return self._unknown(f"{kind} constructor domain is not proven", *args)
        if len(args) == 1 and isinstance(args[0].value, Projection):
            projection = args[0].value
            if kind == "decimal" and projection.runtime_type in {"str", "int", "decimal"}:
                transformed = self._transform_projection(
                    projection, "builtin_decimal", "decimal", 0
                )
                return self._compose(transformed, args, index_map=args[0].index_map)
            if kind == "fraction" and projection.runtime_type in {"str", "int", "fraction"}:
                transformed = self._transform_projection(
                    projection, "builtin_fraction", "fraction", 0
                )
                return self._compose(transformed, args, index_map=args[0].index_map)
        if any(
            isinstance(item.value, (_DerivedValue, _LengthValue, Fold, _AccumulatorValue))
            for item in args
        ):
            return self._compose(_DerivedValue(kind), args)
        try:
            if kind == "fraction":
                if len(args) == 1:
                    raw = _python_exact(args[0].value)
                    if raw is None:
                        return self._unknown("non-exact Fraction argument", *args)
                    value = Fraction(raw)
                elif len(args) == 2:
                    numerator = _python_exact(args[0].value)
                    denominator = _python_exact(args[1].value)
                    if not isinstance(numerator, int) or not isinstance(denominator, int):
                        return self._unknown("non-integer Fraction arguments", *args)
                    value = Fraction(numerator, denominator)
                else:
                    return self._unknown("unsupported Fraction arity", *args)
                return self._compose(self._number(value), args)
            if len(args) != 1:
                return self._unknown("unsupported Decimal arity", *args)
            raw = _python_exact(args[0].value)
            if not isinstance(raw, (str, int, float)):
                return self._unknown("non-exact Decimal argument", *args)
            return self._compose(self._number(Decimal(raw)), args)
        except (ValueError, ZeroDivisionError, InvalidOperation):
            return self._unknown(f"invalid {kind} constructor", *args)

    def _path_constructor(self, args: list[_Tracked]) -> _Tracked:
        if len(args) != 1:
            return self._unknown("unsupported Path constructor", *args)
        value = args[0].value
        if isinstance(value, _ExactString):
            return self._compose(_PathValue(tuple(PurePosixPath(value.value).parts)), args)
        if isinstance(value, _PathValue):
            return args[0]
        return self._unknown("non-literal Path constructor", *args)

    def _zip(self, args: list[_Tracked], node: ast.AST) -> _Tracked:
        left, right = args
        if not isinstance(left.value, _SequenceState) or not isinstance(
            right.value, _SequenceState
        ):
            return self._unknown("zip operands are not sequences", left, right)
        if left.value.semantic.index_map != right.value.semantic.index_map:
            return self._unknown("zip index maps differ", left, right)
        left_element = left.value.semantic.element_value
        right_element = right.value.semantic.element_value
        if not isinstance(left_element, _Tracked) or not isinstance(right_element, _Tracked):
            return self._unknown("invalid zip element", left, right)
        pair = self._compose(
            _PairValue((left_element, right_element)), [left_element, right_element]
        )
        state = _SequenceState(
            Sequence(left.value.semantic.index_map, pair),
            left.value.row_domain,
            self._node_token(node, "zip"),
            single_pass=True,
        )
        return self._compose(state, args, index_map=left.value.semantic.index_map)

    def _fold_call(
        self, source: _Tracked, operation: Literal["sum", "product"], node: ast.AST
    ) -> _Tracked:
        sequence = source.value
        if not isinstance(sequence, _SequenceState):
            return self._unknown("fold source is not a sequence", source)
        if sequence.single_pass and not self._consume(sequence):
            return self._unknown("reconsumed fold iterator", source)
        element = sequence.semantic.element_value
        if not isinstance(element, _Tracked) or not element.selectors:
            return self._compose(_DerivedValue(operation), [source])
        accumulator = _AccumulatorValue(
            self._node_token(node, "accumulator"),
            sequence.row_domain,
            sequence.semantic.index_map,
            self._number(1 if operation == "product" else 0),
            operation,
        )
        return self._make_fold(accumulator, element, operation, node)

    def _make_fold(
        self,
        accumulator: _AccumulatorValue,
        element: _Tracked,
        operation: Literal["sum", "product"],
        node: ast.AST,
    ) -> _Tracked:
        selector_tokens = element.selectors & self.selectors.keys()
        if not selector_tokens:
            return self._unknown("fold has no exact selector", element)
        token = semantic_digest(
            {
                "path": self.document.path,
                "line": getattr(node, "lineno", 0),
                "column": getattr(node, "col_offset", 0),
                "operation": operation,
                "row_domain": accumulator.row_domain,
                "index_map": accumulator.index_map,
                "selectors": sorted(selector_tokens),
            }
        )
        fold = Fold(
            operation,
            accumulator.row_domain,
            element.value,
            accumulator.initial_value,
            accumulator.index_map,
            token,
            frozenset(selector_tokens),
        )
        self.folds[token] = fold
        return self._compose(fold, [element], folds={token})

    def _exact_unary(self, operation: Any, value: _Tracked) -> _Tracked:
        exact = _exact_unary_value(operation, value.value)
        return (
            self._compose(exact, [value])
            if exact is not None
            else self._unknown("unsupported exact unary", value)
        )

    def _transform_projection(
        self,
        projection: Projection,
        operation: str,
        output_type: str,
        parity_delta: int,
    ) -> Projection:
        step = PrimitiveTransform(
            operation,
            projection.runtime_type,
            output_type,
            parity_delta,
        )
        if operation in {
            "builtin_int",
            "builtin_float",
            "builtin_decimal",
            "builtin_fraction",
            "one_minus",
            "bitxor_one",
            "abs_difference_one",
            "boolean_not",
        }:
            self._record_transform_domain_effect(
                projection,
                f"{operation} runtime domain is not proven for the staged column",
            )
        return Projection(
            projection.asset,
            projection.row_domain,
            projection.column,
            (projection.parity + parity_delta) % 2,
            output_type,  # type: ignore[arg-type]
            (*projection.transforms, step),
        )

    def _consume(self, sequence: _SequenceState) -> bool:
        if sequence.token in self.consumed_sequences:
            self.invalidated_origins.add(sequence.row_domain)
            return False
        self.consumed_sequences.add(sequence.token)
        return True

    def _bind(self, name: str, value: _Tracked, env: dict[str, _Tracked]) -> None:
        scoped_name = f"{self.branch}:{name}"
        version = self.versions.get(scoped_name, 0) + 1
        self.versions[scoped_name] = version
        env[name] = value.with_binding(f"{scoped_name}@{version}")

    def _compose(
        self,
        value: _Value,
        parents: list[_Tracked] | tuple[_Tracked, ...],
        *,
        origins: set[str] | frozenset[str] = frozenset(),
        folds: set[str] | frozenset[str] = frozenset(),
        selectors: set[str] | frozenset[str] = frozenset(),
        predicates: set[str] | frozenset[str] = frozenset(),
        unknowns: set[str] | frozenset[str] = frozenset(),
        index_map: str | None = None,
    ) -> _Tracked:
        return _Tracked(
            value,
            frozenset(origins).union(*(item.origins for item in parents)),
            frozenset(folds).union(*(item.folds for item in parents)),
            frozenset(selectors).union(*(item.selectors for item in parents)),
            frozenset(predicates).union(*(item.predicates for item in parents)),
            frozenset().union(*(item.bindings for item in parents)),
            frozenset(unknowns).union(*(item.unknowns for item in parents)),
            index_map
            if index_map is not None
            else next((item.index_map for item in parents if item.index_map is not None), None),
        )

    def _tracked(self, value: _Value, *, index_map: str | None = None) -> _Tracked:
        return _Tracked(value, index_map=index_map)

    def _unknown(self, reason: str, *parents: _Tracked) -> _Tracked:
        merged = self._merge_tracked(list(parents))
        origins = merged.origins
        return _Tracked(
            Unknown(reason, origins),
            origins,
            merged.folds,
            merged.selectors,
            merged.predicates,
            merged.bindings,
            merged.unknowns | {reason},
            merged.index_map,
        )

    def _merge_tracked(self, values: list[_Tracked]) -> _Tracked:
        if not values:
            return self._tracked(_NONE)
        return self._compose(_DerivedValue("merge"), values)

    def _selected_result_payload(self, payload: _Tracked) -> _Tracked | None:
        """Return independently tracked fields from the selected-result line.

        Text-wide lineage is deliberately not sufficient: a diagnostic fold
        elsewhere in the report cannot stand in for the selected emission.
        """

        if not isinstance(payload.value, _TextValue):
            return None
        values = [
            field.value
            for token in payload.value.field_tokens
            if (field := self.report_fields.get(token)) is not None and field.selected_result
        ]
        if not values:
            return None
        selected = self._merge_tracked(values)
        return replace(
            selected,
            origins=selected.origins | payload.origins,
            bindings=selected.bindings | payload.bindings,
            unknowns=selected.unknowns | payload.unknowns,
        )

    def _give_up(
        self,
        node: ast.AST,
        env: dict[str, _Tracked],
        reason: str,
        *parents: _Tracked,
    ) -> None:
        """Emit the one fail-closed lowering effect for an unevaluated subtree."""

        touched = self._merge_tracked([*parents, self._tracked_from_names(node, env)])
        reads = touched.origins | touched.bindings | self._syntactic_reads(node)
        self.effects.append(
            Effect(
                reads=frozenset(reads),
                writes=frozenset({"*"}),
                aliases=touched.origins,
                may_raise=True,
                opaque=True,
                reason=reason,
            )
        )
        self.fail_closed = True
        self.invalidated_origins.update(touched.origins)
        self.invalidated_bindings.update(touched.bindings)

    def _opaque_effect(
        self,
        node: ast.AST,
        touched: _Tracked,
        *,
        writes: set[str],
        reason: str,
    ) -> None:
        del writes
        aliases = touched.origins
        self.effects.append(
            Effect(
                reads=touched.origins | touched.bindings | self._syntactic_reads(node),
                writes=frozenset({"*"}),
                aliases=frozenset(aliases),
                may_raise=True,
                opaque=True,
                reason=reason,
            )
        )
        self.fail_closed = True
        self.invalidated_origins.update(touched.origins)
        self.invalidated_bindings.update(touched.bindings)

    @staticmethod
    def _syntactic_reads(node: ast.AST) -> frozenset[str]:
        reads: set[str] = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load):
                reads.add(f"name:{item.id}")
            elif isinstance(item, ast.Attribute) and isinstance(item.ctx, ast.Load):
                reads.add(f"attribute:{item.attr}")
            elif isinstance(item, ast.Subscript) and isinstance(item.ctx, ast.Load):
                reads.add("subscript")
        return frozenset(reads)

    def _record_transform_domain_effect(self, projection: Projection, reason: str) -> None:
        self.effects.append(
            Effect(
                reads=frozenset({projection.asset, projection.row_domain}),
                writes=frozenset(),
                aliases=frozenset(),
                may_raise=True,
                opaque=False,
                reason=reason,
            )
        )

    def _tracked_from_names(self, node: ast.AST, env: dict[str, _Tracked]) -> _Tracked:
        return self._merge_tracked(
            [
                env[item.id]
                for item in ast.walk(node)
                if isinstance(item, ast.Name) and item.id in env
            ]
        )

    def _target_names(self, node: ast.AST) -> set[str]:
        return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}

    def _bound_names(self, statements: list[ast.stmt]) -> set[str]:
        names: set[str] = set()
        for statement in statements:
            for node in ast.walk(statement):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        names.update(self._target_names(target))
                elif isinstance(node, ast.AugAssign | ast.AnnAssign | ast.For):
                    names.update(self._target_names(node.target))
                elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    names.add(node.name)
        return names

    def _may_have_global_or_sink_effect(self, statement: ast.stmt) -> bool:
        """Whether an opaque statement can dispatch into global or sink mutation.

        Ordinary unused constructs are never executed and do not reach this
        function.  For an executable opaque region, a local helper call can
        close over globals and a write-like method can replace the selected
        report, so either has an all-bindings effect until a compositional
        summary exists.  A class with bases, keywords, decorators, or an
        executable body has the same metaclass/class-body boundary.
        """

        if isinstance(statement, ast.ClassDef):
            inert_body = all(
                isinstance(item, (ast.Pass, ast.FunctionDef)) for item in statement.body
            )
            if statement.bases or statement.keywords or statement.decorator_list or not inert_body:
                return True
        if isinstance(statement, ast.Assign):
            if any(not isinstance(target, ast.Name) for target in statement.targets):
                return True
        if isinstance(statement, ast.AugAssign | ast.AnnAssign | ast.Delete):
            return True
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in self.functions:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "write",
                "writelines",
                "write_text",
            }:
                return True
            key = self._call_key(node.func)
            if key in {
                "Decimal",
                "decimal.Decimal",
                "Fraction",
                "fractions.Fraction",
                "Path",
                "pathlib.Path",
                "PurePath",
                "pathlib.PurePath",
                "abs",
                "bool",
                "float",
                "int",
                "len",
                "list",
                "print",
                "range",
                "str",
                "sum",
                "zip",
            } or key.startswith(("math.", "statistics.")):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr == "mkdir":
                continue
            return True
        return False

    @staticmethod
    def _loop_has_unsupported_control(statement: ast.For) -> bool:
        stack: list[ast.AST] = list(statement.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
                continue
            if isinstance(
                node,
                ast.Break
                | ast.Continue
                | ast.Return
                | ast.Raise
                | ast.Yield
                | ast.YieldFrom
                | ast.Try
                | ast.TryStar,
            ):
                return True
            stack.extend(ast.iter_child_nodes(node))
        return False

    def _loop_bindings_are_sound(
        self,
        statement: ast.For,
        before: dict[str, _Tracked],
        assigned: set[str],
    ) -> bool:
        """Admit only exact associative loop-carried accumulator updates."""

        for name in assigned & before.keys():
            updates = [item for item in statement.body if self._statement_binds_name(item, name)]
            if len(updates) != 1:
                return False
            update = updates[0]
            operation: Literal["sum", "product"] | None = None
            if isinstance(update, ast.AugAssign) and isinstance(update.target, ast.Name):
                if isinstance(update.op, ast.Add):
                    operation = "sum"
                elif isinstance(update.op, ast.Mult):
                    operation = "product"
            elif (
                isinstance(update, ast.Assign)
                and len(update.targets) == 1
                and isinstance(update.targets[0], ast.Name)
                and isinstance(update.value, ast.BinOp)
            ):
                operands = (update.value.left, update.value.right)
                if not any(
                    isinstance(operand, ast.Name) and operand.id == name for operand in operands
                ):
                    return False
                if isinstance(update.value.op, ast.Add):
                    operation = "sum"
                elif isinstance(update.value.op, ast.Mult):
                    operation = "product"
            if operation == "sum" and _is_zero(before[name].value):
                continue
            if operation == "product" and _is_one(before[name].value):
                continue
            return False
        return True

    def _statement_binds_name(self, statement: ast.stmt, name: str) -> bool:
        return name in self._bound_names([statement])

    @staticmethod
    def _static_helper_default(node: ast.expr) -> bool:
        return all(
            isinstance(item, (ast.Constant, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.Load))
            for item in ast.walk(node)
        )

    @staticmethod
    def _path_from_value(value: _Value) -> _PathValue | None:
        if isinstance(value, _PathValue):
            return value
        if isinstance(value, _ExactString):
            return _PathValue(tuple(PurePosixPath(value.value).parts))
        return None

    @staticmethod
    def _is_write_mode(mode: str) -> bool:
        return any(flag in mode for flag in "wax+")

    def _call_key(self, function: ast.expr) -> str:
        if isinstance(function, ast.Name):
            return self.imports.get(function.id, function.id)
        if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            origin = self.imports.get(function.value.id, function.value.id)
            return f"{origin}.{function.attr}"
        return ""

    def _is_selected_path(self, path: _PathValue) -> bool:
        if not path.exact:
            return False
        actual = path.normalized
        selected = _normalize_posix_parts(PurePosixPath(self.selected_report_path).parts)
        return actual == selected

    def _node_token(self, node: ast.AST, kind: str) -> str:
        return semantic_digest(
            {
                "kind": kind,
                "path": self.document.path,
                "line": getattr(node, "lineno", 0),
                "column": getattr(node, "col_offset", 0),
            }
        )

    def _evidence_point(self, node: ast.AST) -> EvidencePoint:
        return EvidencePoint(
            path=self.document.path,
            start_line=getattr(node, "lineno", 1),
            end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            start_column=getattr(node, "col_offset", 0) + 1,
            end_column=getattr(node, "end_col_offset", getattr(node, "col_offset", 0)) + 1,
        )

    def _orientation(self, comparison: Eq) -> Orientation | None:
        if comparison.left.row_domain != comparison.right.row_domain:
            return None
        return "repaired" if (comparison.left.parity + comparison.right.parity) % 2 else "direct"

    @staticmethod
    def _is_main_guard(statement: ast.If) -> bool:
        test = statement.test
        return (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
            and not statement.orelse
        )

    @staticmethod
    def _number(value: int | float | Decimal | Fraction) -> ExactNumber:
        return _number(value)


def resolve_founder_orientation_semantic(
    context: FrozenInspectionContext,
    *,
    direct_operand: str,
    repaired_operand: str,
    parser_id: str,
    parser_version: str,
) -> SemanticResolution:
    """Resolve v3 certificates over the exact immutable Python documents."""

    selected_report_path = _selected_artifact_path(context)
    certificates: list[tuple[InspectionDocument, VerifiedOrientationCertificate]] = []
    saw_blocked_candidate = False
    case_module_names: set[str] = set()
    for document in context.documents:
        parts = Path(document.path).parts
        case_module_names.update(parts[:-1])
        if document.path.endswith(".py"):
            stem = Path(document.path).stem
            if stem != "__init__":
                case_module_names.add(stem)
    for document in context.documents:
        if document.media_type != "text/x-python":
            continue
        if not _python_parser_supported(document, parser_id, parser_version):
            saw_blocked_candidate = True
            continue
        if len(document.content) > _MAX_SOURCE_BYTES:
            saw_blocked_candidate = True
            continue
        try:
            source = document.content.decode("utf-8")
        except UnicodeDecodeError:
            saw_blocked_candidate = True
            continue
        tree = _guarded_parse(source, filename=document.path)
        if tree is None:
            saw_blocked_candidate = True
            continue
        other_modules = case_module_names - {Path(document.path).stem}
        if (
            _semantic_resource_bans(tree)
            or _imports_case_module(tree, other_modules)
            or _semantic_module_bans(tree)
        ):
            saw_blocked_candidate = True
            continue
        analyzer = _Analyzer(document, tree, selected_report_path)
        try:
            proposal = analyzer.analyze()
        except (RecursionError, MemoryError, OverflowError):
            # Resource/depth failure is localized to this document, but a
            # document that defeated the analyzer cannot contribute a proof.
            saw_blocked_candidate = True
            continue
        if proposal is None:
            saw_blocked_candidate = (
                saw_blocked_candidate or analyzer.selected_sink_seen or analyzer.fail_closed
            )
            continue
        verified = verify_orientation_certificate(proposal)
        if verified is not None:
            certificates.append((document, verified))
        else:
            saw_blocked_candidate = True
    orientations = {certificate.orientation for _, certificate in certificates}
    if saw_blocked_candidate:
        return SemanticResolution("unsupported", None, None, (), None)
    if len(orientations) > 1:
        return SemanticResolution("ambiguous", None, None, (), None)
    if not certificates:
        state = "unsupported" if saw_blocked_candidate else "none"
        return SemanticResolution(state, None, None, (), None)
    orientation = next(iter(orientations))
    spans = tuple(
        _evidence_span(document, point)
        for document, certificate in certificates
        for point in certificate.evidence
    )
    first = certificates[0][1]
    return SemanticResolution(
        "unique",
        orientation,
        repaired_operand if orientation == "repaired" else direct_operand,
        spans,
        first.source_path,
        first,
    )


def founder_orientation_semantic_grammar(
    direct_operand: str, repaired_operand: str
) -> dict[str, Any]:
    """Canonical public description of the v3 proof language."""

    return {
        "grammar_id": "founder-orientation-semantic-certificate",
        "grammar_version": "3.0.1",
        "operands": {"direct": direct_operand, "repaired": repaired_operand},
        "abstract_values": [
            "Projection(asset,row_domain,column,parity,runtime_type)",
            "Sequence(index_map,element_value)",
            "Predicate(Eq(left,right))",
            "ExactNumber(type,value)",
            "Selector(predicate,false_value,true_value)",
            "Fold(op,row_domain,element)",
            "Effect(reads,writes,aliases,may_raise)",
            "Unknown(reason,origins)",
        ],
        "selector_recovery": (
            "evaluate every pure one-predicate expression extensionally at False and True; "
            "require two distinct exact numeric branches and a strictly larger equality branch"
        ),
        "helper_summary": (
            "evaluate one helper body with its parameters bound to call-site abstract values; "
            "reader, selector, recode, and writer behavior share this mechanism"
        ),
        "opaque_effect_policy": (
            "an opaque ordinary construct blocks only when its reads, writes, aliases, or "
            "raising behavior intersects the certified report-reaching slice"
        ),
        "module_bans": (
            "the frozen v2 reflection, builtin-shadowing, executable-annotation, star-import, "
            "and non-stdlib import bans, plus duplicate or higher-order dynamic dispatch"
        ),
        "certificate_kernel": "founder_orientation_certificate.verify_orientation_certificate",
        "csv_refinement": (
            "not enabled in 3.0.1; an unresolved parity bit remains an abstention rather than "
            "using report-number uniqueness"
        ),
        "fusion": "v2 and v3 are independent adapters; disagreement abstains and never votes",
    }


def founder_orientation_semantic_grammar_digest(direct_operand: str, repaired_operand: str) -> str:
    return semantic_digest(founder_orientation_semantic_grammar(direct_operand, repaired_operand))


def _semantic_module_bans(tree: ast.Module) -> bool:
    """The frozen v2 hard bans plus dynamic-dispatch noninterference bans."""

    if _module_bans(tree):
        return True
    nodes = list(ast.walk(tree))
    definitions: dict[str, int] = {}
    function_names: set[str] = set()
    parameter_names: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.FunctionDef):
            definitions[node.name] = definitions.get(node.name, 0) + 1
            function_names.add(node.name)
            if node.decorator_list:
                return True
            parameters = (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
                *([node.args.vararg] if node.args.vararg else []),
                *([node.args.kwarg] if node.args.kwarg else []),
            )
            parameter_names.update(item.arg for item in parameters)
            defaults = [*node.args.defaults, *[item for item in node.args.kw_defaults if item]]
            if any(not _Analyzer._static_helper_default(default) for default in defaults):
                return True
        if isinstance(
            node,
            ast.AnnAssign | ast.Global | ast.Nonlocal | ast.Lambda | ast.NamedExpr,
        ):
            return True
        if isinstance(node, ast.AsyncFunctionDef | ast.AsyncFor | ast.AsyncWith | ast.Await):
            return True
        if _semantic_binding_names(node) & _BUILTINS:
            return True
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in parameter_names
        for node in nodes
    ):
        return True
    if any(count != 1 for count in definitions.values()):
        return True
    call_positions = {id(node.func) for node in nodes if isinstance(node, ast.Call)}
    for node in nodes:
        if (
            isinstance(node, ast.Name)
            and node.id in function_names
            and isinstance(node.ctx, ast.Load)
        ):
            if id(node) not in call_positions:
                return True
    return False


def _semantic_binding_names(node: ast.AST) -> set[str]:
    """V3 supplement for binding forms omitted by the frozen v2 scanner."""

    if isinstance(node, ast.ClassDef):
        return {node.name}
    if isinstance(node, ast.ExceptHandler) and node.name:
        return {node.name}
    if isinstance(node, ast.MatchAs) and node.name:
        return {node.name}
    if isinstance(node, ast.MatchStar) and node.name:
        return {node.name}
    if isinstance(node, ast.MatchMapping) and node.rest:
        return {node.rest}
    return set()


def _semantic_resource_bans(tree: ast.Module) -> bool:
    count = 0
    helpers = 0
    stack: list[ast.AST] = [tree]
    while stack:
        node = stack.pop()
        count += 1
        if count > _MAX_AST_NODES:
            return True
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            helpers += 1
            if helpers > _MAX_HELPERS:
                return True
        stack.extend(ast.iter_child_nodes(node))
    return False


def _normalize_posix_parts(parts: tuple[str, ...]) -> str:
    """Lexically normalize runtime-equivalent relative POSIX path aliases."""

    absolute = bool(parts and parts[0] == "/")
    normalized: list[str] = []
    for part in parts:
        if part in {"", ".", "/"}:
            continue
        if part == "..":
            if normalized and normalized[-1] != "..":
                normalized.pop()
            elif not absolute:
                normalized.append(part)
            continue
        normalized.append(part)
    text = "/".join(normalized)
    if absolute:
        return f"/{text}" if text else "/"
    return text or "."


def _number(value: int | float | Decimal | Fraction) -> ExactNumber:
    if isinstance(value, bool):
        raise TypeError("bool is not an ExactNumber")
    if isinstance(value, int):
        fraction = Fraction(value)
        kind = "int"
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float")
        fraction = Fraction.from_float(value)
        kind = "float"
    elif isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite decimal")
        fraction = Fraction(value)
        kind = "decimal"
    else:
        fraction = value
        kind = "fraction"
    if (
        abs(fraction.numerator).bit_length() > _MAX_EXACT_INTEGER_BITS
        or fraction.denominator.bit_length() > _MAX_EXACT_INTEGER_BITS
    ):
        raise OverflowError("exact number magnitude exceeded")
    return ExactNumber(kind, f"{fraction.numerator}/{fraction.denominator}")  # type: ignore[arg-type]


def _number_fraction(value: ExactNumber) -> Fraction | None:
    try:
        numerator, denominator = value.value.split("/", 1)
        fraction = Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError):
        return None
    return fraction if f"{fraction.numerator}/{fraction.denominator}" == value.value else None


def _python_exact(value: _Value) -> int | float | Decimal | Fraction | str | None:
    if isinstance(value, _ExactString):
        return value.value
    if not isinstance(value, ExactNumber):
        return None
    fraction = _number_fraction(value)
    if fraction is None:
        return None
    if value.number_type == "int":
        return fraction.numerator if fraction.denominator == 1 else None
    if value.number_type == "float":
        return float(fraction)
    if value.number_type == "decimal":
        return _decimal_from_fraction(fraction)
    return fraction


def _decimal_from_fraction(value: Fraction) -> Decimal | None:
    """Reconstruct a finite Decimal exactly, without consulting its context."""

    denominator = value.denominator
    powers_of_two = 0
    powers_of_five = 0
    while denominator % 2 == 0:
        powers_of_two += 1
        denominator //= 2
    while denominator % 5 == 0:
        powers_of_five += 1
        denominator //= 5
    if denominator != 1:
        return None
    scale = max(powers_of_two, powers_of_five)
    coefficient = value.numerator
    coefficient *= 2 ** (scale - powers_of_two)
    coefficient *= 5 ** (scale - powers_of_five)
    sign = 1 if coefficient < 0 else 0
    digits = tuple(int(digit) for digit in str(abs(coefficient)))
    return Decimal((sign, digits, -scale))


def _exact_binary(op: ast.operator, left: _Value, right: _Value) -> ExactNumber | None:
    left_value = _python_exact(left)
    right_value = _python_exact(right)
    if not isinstance(left_value, (int, float, Decimal, Fraction)) or not isinstance(
        right_value, (int, float, Decimal, Fraction)
    ):
        return None
    if isinstance(left_value, Decimal) or isinstance(right_value, Decimal):
        # Decimal arithmetic consults mutable process context.  Exact
        # constructor values alone do not authorize replaying that context.
        return None
    if isinstance(op, ast.Pow):
        exponent = right_value
        if not isinstance(exponent, int) or abs(exponent) > _MAX_POW_EXPONENT:
            return None
        if isinstance(left_value, int) and left_value not in {-1, 0, 1}:
            estimated_bits = max(1, abs(left_value).bit_length()) * max(exponent, 0)
            if estimated_bits > _MAX_EXACT_INTEGER_BITS:
                return None
    operation = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
    }.get(type(op))
    if operation is None:
        return None
    result = operation(left_value, right_value)
    if isinstance(result, bool) or not isinstance(result, (int, float, Decimal, Fraction)):
        return None
    return _number(result)


def _exact_unary_value(operation: Any, value: _Value) -> ExactNumber | None:
    python_value = _python_exact(value)
    if not isinstance(python_value, (int, float, Decimal, Fraction)):
        return None
    result = operation(python_value)
    return _number(result) if isinstance(result, (int, float, Decimal, Fraction)) else None


def _convert_number(value: ExactNumber, kind: str) -> ExactNumber | None:
    python_value = _python_exact(value)
    if not isinstance(python_value, (int, float, Decimal, Fraction)):
        return None
    if kind == "int":
        return _number(int(python_value))
    if kind == "float":
        return _number(float(python_value))
    if kind == "bool":
        return _number(int(bool(python_value)))
    return None


def _exact_compare(left: _Value, right: _Value) -> bool | None:
    if isinstance(left, _ExactString) and isinstance(right, _ExactString):
        return left.value == right.value
    left_value = _python_exact(left)
    right_value = _python_exact(right)
    if left_value is None or right_value is None:
        return None
    return bool(left_value == right_value)


def _exact_integer(value: _Value) -> int | None:
    python_value = _python_exact(value)
    return (
        python_value
        if isinstance(python_value, int) and not isinstance(python_value, bool)
        else None
    )


def _is_zero(value: _Value) -> bool:
    fraction = _number_fraction(value) if isinstance(value, ExactNumber) else None
    return fraction == 0


def _is_one(value: _Value) -> bool:
    fraction = _number_fraction(value) if isinstance(value, ExactNumber) else None
    return fraction == 1


def _row_domain(value: _Tracked) -> str | None:
    if isinstance(value.value, Projection):
        return value.value.row_domain
    if isinstance(value.value, Gated):
        return value.value.row_domain
    return None


def _selected_artifact_path(context: FrozenInspectionContext) -> str:
    for record in context.base_records:
        if record.ref == context.selected_artifact_ref:
            value = json.loads(record.canonical_payload)
            if isinstance(value, dict) and isinstance(value.get("path"), str):
                return str(value["path"])
    for document in context.documents:
        if document.media_type == "text/markdown":
            return document.path
    return "report.md"


def _evidence_span(document: InspectionDocument, point: EvidencePoint) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=point.start_line + document.line_offset,
        end_line=point.end_line + document.line_offset,
        start_column=point.start_column,
        end_column=point.end_column,
        parser_result_ref=document.parser_result_ref,
    )
