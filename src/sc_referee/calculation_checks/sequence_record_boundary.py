from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

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

SEQUENCE_RECORD_BOUNDARY_CHECK_ID = "calculation-check:selected-sequence-record-boundary-v1"

_AMINO_ACID_ALPHABET = frozenset("ACDEFGHIKLMNPQRSTVWYBXZJUO")
_MIN_SEQUENCE_LENGTH = 20
_MAX_SEQUENCE_LENGTH = 10_000
_MAX_LABEL_LENGTH = 256
_MAX_RECORD_BYTES = 64 * 1024
_MAX_QUOTED_SOURCE_LENGTH = 4_096
_RECOGNITION_GRAMMAR_DIGEST = semantic_digest(
    {
        "source_language": "python_ast_no_execution",
        "source_suffix": ".py",
        "record_byte_ceiling": _MAX_RECORD_BYTES,
        "record_shape": "exactly_two_nonempty_strict_utf8_lines",
        "sequence_line": {
            "alphabet": "ACDEFGHIKLMNPQRSTVWYBXZJUO",
            "minimum_length": _MIN_SEQUENCE_LENGTH,
            "maximum_length": _MAX_SEQUENCE_LENGTH,
        },
        "label_line": {
            "shape": "contains_alphabetic_text_and_at_least_one_non_sequence_character",
            "maximum_length": _MAX_LABEL_LENGTH,
            "fasta_header_excluded": True,
        },
        "source_binding": (
            "unique_exact_selected_record_path_flow_to_unique_python_read_text_splitline_join"
        ),
        "adverse_shape": "empty_string_join_over_every_nonempty_or_non_fasta_header_splitline",
        "ambiguity_rule": "multiple_source_record_pairs_emit_unknown",
        "unsupported_rule": "unique_selected_python_parse_failure_emits_unknown",
        "quoted_source_character_ceiling": _MAX_QUOTED_SOURCE_LENGTH,
    }
)


@dataclass(frozen=True)
class _RecordShape:
    item: FrozenCalculationInput
    sequence: str
    label: str


@dataclass(frozen=True)
class _JoinShape:
    start_line: int
    end_line: int
    quoted_text: str


class SelectedSequenceRecordBoundaryAdapter:
    """Compare selected two-line sequence records with closed Python join shapes."""

    def __init__(self) -> None:
        self.manifest = CalculationAdapterManifest(
            adapter_id="calculation-adapter:selected-sequence-record-boundary-v1",
            adapter_version="1.0.0",
            implementation_digest=sha256_digest(Path(__file__).read_bytes()),
            recognition_grammar_digest=_RECOGNITION_GRAMMAR_DIGEST,
        )

    def inspect(self, context: CalculationContext) -> CalculationObservation | None:
        if not isinstance(context, MaterialCalculationContext):
            return None
        records = tuple(
            shape
            for item in context.material_inputs
            if (shape := _sequence_record_shape(item)) is not None
        )
        python_inputs = tuple(
            item for item in context.material_inputs if item.path.casefold().endswith(".py")
        )
        parsed_sources: list[tuple[FrozenCalculationInput, ast.Module]] = []
        parse_failures: list[FrozenCalculationInput] = []
        for item in python_inputs:
            parsed = _parse_python(item)
            if parsed is None:
                parse_failures.append(item)
            else:
                parsed_sources.append((item, parsed))
        pairs: list[tuple[_RecordShape, FrozenCalculationInput, _JoinShape]] = []
        ambiguous_sources: list[FrozenCalculationInput] = []
        for record in records:
            basename = PurePosixPath(record.item.path).name
            for source, tree in parsed_sources:
                joins = _unsafe_line_joins(
                    tree,
                    source.content.decode("utf-8"),
                    record_path=record.item.path,
                    basename=basename,
                )
                if len(joins) == 1:
                    pairs.append((record, source, joins[0]))
                elif len(joins) > 1:
                    ambiguous_sources.append(source)
        if (
            not pairs
            and not ambiguous_sources
            and len(records) == 1
            and len(python_inputs) == 1
            and parse_failures
        ):
            record = records[0]
            source = parse_failures[0]
            unsupported_refs = (record.item.source_ref, source.source_ref)
            return CalculationObservation(
                applicability="unsupported",
                comparison_outcome="unknown",
                target_ref=context.selected_surface_ref,
                input_refs=(
                    context.selected_artifact_ref,
                    record.item.artifact_ref,
                    source.artifact_ref,
                ),
                source_refs=unsupported_refs,
                operands=(),
                receipts=(
                    ObservationReceipt(
                        "completeness",
                        "selected_python_ast_available",
                        "unsupported",
                        (source.source_ref,),
                        "The unique selected Python material input could not be parsed as inert Python AST.",
                    ),
                ),
                lineage_status="incomplete",
                limitations=(
                    "The selected record has the bounded two-line shape, but its selected Python consumer could not be parsed; no boundary conclusion was drawn.",
                    "This localized unsupported state does not establish execution, use, or an analysis issue.",
                ),
            )
        if not pairs and not ambiguous_sources:
            return None
        if len(pairs) != 1 or ambiguous_sources:
            input_items = tuple(
                sorted(
                    {
                        item.path: item
                        for item in (
                            *(record.item for record in records),
                            *python_inputs,
                        )
                    }.values(),
                    key=lambda item: item.path,
                )
            )
            ambiguous_refs = tuple(item.source_ref for item in input_items)
            return CalculationObservation(
                applicability="ambiguous",
                comparison_outcome="unknown",
                target_ref=context.selected_surface_ref,
                input_refs=(
                    context.selected_artifact_ref,
                    *(item.artifact_ref for item in input_items),
                ),
                source_refs=ambiguous_refs,
                operands=(),
                receipts=(
                    ObservationReceipt(
                        "ambiguity",
                        "unique_sequence_record_parser_pair",
                        "triggered",
                        ambiguous_refs,
                        "The selected material view contains more than one exactly bound record/parser pair or consuming join shape.",
                    ),
                ),
                lineage_status="incomplete",
                limitations=(
                    "A unique exact path from one selected two-line record to one Python join shape could not be established; no boundary conclusion was drawn.",
                ),
            )
        record, source, join = pairs[0]
        record_ref = _record_source_ref(record)
        join_ref = _join_source_ref(source, join)
        sources_refs = (record_ref, join_ref)
        return CalculationObservation(
            applicability="applicable",
            comparison_outcome="nonconformant",
            target_ref=context.selected_surface_ref,
            input_refs=(
                context.selected_artifact_ref,
                record.item.artifact_ref,
                source.artifact_ref,
            ),
            source_refs=sources_refs,
            operands=(
                NamedOperand("record_path", "string", record.item.path),
                NamedOperand("source_path", "string", source.path),
                NamedOperand("record_line_count", "integer", 2),
                NamedOperand("sequence_line_length", "integer", len(record.sequence)),
                NamedOperand("non_sequence_line", "string", record.label),
                NamedOperand("joined_nonheader_lines", "boolean", True),
                NamedOperand("join_start_line", "integer", join.start_line),
            ),
            receipts=(
                ObservationReceipt(
                    "applicability",
                    "selected_two_line_sequence_record",
                    "passed",
                    (record_ref,),
                    "The exact selected UTF-8 record has two nonempty lines: a bounded amino-acid-alphabet-only line followed by non-FASTA-header text containing a character outside that alphabet.",
                ),
                ObservationReceipt(
                    "completeness",
                    "selected_record_path_flow",
                    "passed",
                    (record_ref, source.source_ref),
                    "A closed inert-AST path binds the selected record's exact path or basename to the read feeding the unique join.",
                ),
                ObservationReceipt(
                    "completeness",
                    "unique_splitline_join_shape",
                    "passed",
                    (join_ref,),
                    "One closed AST shape joins every nonempty or non-FASTA-header line from a text split into lines.",
                ),
                ObservationReceipt(
                    "counterevidence",
                    "alternate_record_or_parser_shape",
                    "passed",
                    sources_refs,
                    "Wrapped sequence lines, FASTA records, all-sequence second lines, corrected first-line selection, dynamic parsing, and non-unique pairs do not produce this comparison.",
                ),
            ),
            lineage_status="complete",
            limitations=(
                "The exact static shape does not prove execution, runtime path selection, downstream model use, numerical impact, or publication use.",
                "The initial grammar covers one unique Python join with a direct or single-call exact path binding to a selected bounded two-line record; dynamic helpers, other languages, structured formats, and ambiguous sequence alphabets abstain.",
                "This module emits a Disclosure only and cannot emit a Finding.",
            ),
        )


def sequence_record_boundary_registry() -> CalculationCheckRegistry:
    adapter = SelectedSequenceRecordBoundaryAdapter()
    check = CalculationCheckManifest(
        check_id=SEQUENCE_RECORD_BOUNDARY_CHECK_ID,
        check_version="1.0.0",
        implementation_digest=sha256_digest(Path(__file__).read_bytes()),
        comparison_relation="selected_two_line_sequence_record_vs_python_line_join_boundary",
        output_ceiling="disclosure_only",
        permitted_wording=(
            "The uniquely path-bound selected Python parser includes a second non-FASTA-header record line containing text outside the amino-acid alphabet in its joined sequence value."
        ),
    )
    return CalculationCheckRegistry(
        (CalculationCheckModule(check, (adapter,)),),
        profile_id="deterministic_sequence_record_boundary_v1",
    )


def _sequence_record_shape(item: FrozenCalculationInput) -> _RecordShape | None:
    if item.path.casefold().endswith(".py") or len(item.content) > _MAX_RECORD_BYTES:
        return None
    try:
        text = item.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    lines = text.splitlines()
    if len(lines) != 2 or any(not line or line != line.strip() for line in lines):
        return None
    sequence = lines[0]
    label = lines[1]
    if not _MIN_SEQUENCE_LENGTH <= len(sequence) <= _MAX_SEQUENCE_LENGTH:
        return None
    if not set(sequence.upper()) <= _AMINO_ACID_ALPHABET:
        return None
    if (
        len(label) > _MAX_LABEL_LENGTH
        or label.startswith(">")
        or not any(char.isalpha() for char in label)
    ):
        return None
    if set(label.upper()) <= _AMINO_ACID_ALPHABET:
        return None
    return _RecordShape(item=item, sequence=sequence, label=label)


def _parse_python(item: FrozenCalculationInput) -> ast.Module | None:
    try:
        text = item.content.decode("utf-8", errors="strict")
        tree = ast.parse(text, filename=item.path, type_comments=True)
    except (UnicodeDecodeError, SyntaxError):
        return None
    return tree


def _unsafe_line_joins(
    tree: ast.Module,
    text: str,
    *,
    record_path: str,
    basename: str,
) -> tuple[_JoinShape, ...]:
    shapes: list[_JoinShape] = []
    scopes: tuple[ast.Module | ast.FunctionDef, ...] = (
        tree,
        *(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)),
    )
    for scope in scopes:
        assignments = _simple_assignments(scope)
        for node in _walk_scope_body(scope):
            if not isinstance(node, ast.Call) or not _empty_string_join(node):
                continue
            value = _resolve_name(node.args[0], assignments)
            if not isinstance(value, (ast.GeneratorExp, ast.ListComp)):
                continue
            if len(value.generators) != 1:
                continue
            generator = value.generators[0]
            if not isinstance(generator.target, ast.Name):
                continue
            iterator = _resolve_name(generator.iter, assignments)
            receiver = _read_text_receiver(iterator)
            if receiver is None or not _path_expression_binds_record(
                receiver,
                assignments=assignments,
                tree=tree,
                scope=scope,
                record_path=record_path,
                basename=basename,
            ):
                continue
            line_name = generator.target.id
            if not _line_projection(value.elt, line_name):
                continue
            if not all(_permitted_line_filter(condition, line_name) for condition in generator.ifs):
                continue
            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            quoted = "\n".join(text.splitlines()[start_line - 1 : end_line])
            if len(quoted) > _MAX_QUOTED_SOURCE_LENGTH:
                continue
            shapes.append(_JoinShape(start_line, end_line, quoted))
    unique = {(shape.start_line, shape.end_line, shape.quoted_text): shape for shape in shapes}
    return tuple(unique[key] for key in sorted(unique))


def _walk_scope_body(scope: ast.Module | ast.FunctionDef) -> tuple[ast.AST, ...]:
    nodes: list[ast.AST] = []
    for statement in scope.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        nodes.extend(ast.walk(statement))
    return tuple(nodes)


def _path_expression_binds_record(
    expression: ast.expr,
    *,
    assignments: dict[str, ast.expr],
    tree: ast.Module,
    scope: ast.Module | ast.FunctionDef,
    record_path: str,
    basename: str,
) -> bool:
    if _direct_path_expression_binds_record(
        expression,
        assignments=assignments,
        record_path=record_path,
        basename=basename,
        seen=frozenset(),
    ):
        return True
    resolved = _resolve_name(expression, assignments)
    if isinstance(resolved, ast.Attribute):
        return _attribute_binds_record(
            resolved,
            assignments=assignments,
            tree=tree,
            record_path=record_path,
            basename=basename,
        )
    if not isinstance(scope, ast.FunctionDef) or not isinstance(resolved, ast.Name):
        return False
    parameters = (*scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs)
    if resolved.id not in {parameter.arg for parameter in parameters}:
        return False
    call = _unique_direct_call(tree, scope.name)
    if call is None:
        return False
    argument = _call_argument(call, parameters, resolved.id)
    if argument is None:
        return False
    call_scope = _containing_scope(tree, call)
    call_assignments = _simple_assignments(call_scope)
    if _direct_path_expression_binds_record(
        argument,
        assignments=call_assignments,
        record_path=record_path,
        basename=basename,
        seen=frozenset(),
    ):
        return True
    return isinstance(argument, ast.Attribute) and _attribute_binds_record(
        argument,
        assignments=call_assignments,
        tree=tree,
        record_path=record_path,
        basename=basename,
    )


def _direct_path_expression_binds_record(
    expression: ast.expr,
    *,
    assignments: dict[str, ast.expr],
    record_path: str,
    basename: str,
    seen: frozenset[str],
) -> bool:
    if isinstance(expression, ast.Name) and expression.id in assignments:
        if expression.id in seen:
            return False
        return _direct_path_expression_binds_record(
            assignments[expression.id],
            assignments=assignments,
            record_path=record_path,
            basename=basename,
            seen=seen | {expression.id},
        )
    fragments = _literal_path_fragments(
        expression,
        assignments=assignments,
        seen=seen,
    )
    if not fragments:
        return False
    candidate = "/".join(part.strip("/") for part in fragments if part.strip("/"))
    return _path_literal_matches(candidate, record_path, basename)


def _literal_path_fragments(
    expression: ast.expr,
    *,
    assignments: dict[str, ast.expr],
    seen: frozenset[str],
) -> tuple[str, ...]:
    if isinstance(expression, ast.Name):
        if expression.id in seen or expression.id not in assignments:
            return ()
        return _literal_path_fragments(
            assignments[expression.id],
            assignments=assignments,
            seen=seen | {expression.id},
        )
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return (expression.value.replace("\\", "/"),)
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, (ast.Name, ast.Attribute))
        and (expression.func.id if isinstance(expression.func, ast.Name) else expression.func.attr)
        in {"Path", "PurePath", "PurePosixPath"}
        and len(expression.args) == 1
        and not expression.keywords
    ):
        return _literal_path_fragments(
            expression.args[0],
            assignments=assignments,
            seen=seen,
        )
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Div):
        left = _literal_path_fragments(
            expression.left,
            assignments=assignments,
            seen=seen,
        )
        right = _literal_path_fragments(
            expression.right,
            assignments=assignments,
            seen=seen,
        )
        if not left or not right:
            return ()
        return (*left, *right)
    return ()


def _path_literal_matches(candidate: str, record_path: str, basename: str) -> bool:
    normalized_candidate = candidate.replace("\\", "/")
    normalized_record = record_path.replace("\\", "/")
    return (
        normalized_candidate == normalized_record
        or normalized_candidate == basename
        or (
            normalized_candidate.endswith(f"/{basename}")
            and normalized_record.endswith(normalized_candidate)
        )
    )


def _attribute_binds_record(
    expression: ast.Attribute,
    *,
    assignments: dict[str, ast.expr],
    tree: ast.Module,
    record_path: str,
    basename: str,
) -> bool:
    caller_assignments = assignments
    base = _resolve_name(expression.value, assignments)
    if not isinstance(base, ast.Call):
        return False
    candidates = [keyword.value for keyword in base.keywords if keyword.arg == expression.attr]
    if not candidates and isinstance(base.func, ast.Name):
        function = _unique_function_definition(tree, base.func.id)
        if function is None:
            return False
        function_assignments = _simple_assignments(function)
        parameters = (*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs)
        for parameter in parameters:
            argument = _call_argument(base, parameters, parameter.arg)
            if argument is not None and parameter.arg not in function_assignments:
                function_assignments[parameter.arg] = _resolve_name(argument, caller_assignments)
        option_name = f"--{expression.attr.replace('_', '-')}"
        parser_defaults: list[tuple[str, ast.expr]] = []
        returned_parser_names: set[str] = set()
        constructor_candidates: list[ast.expr] = []
        for node in _walk_scope_body(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
                and any(
                    isinstance(argument, ast.Constant) and argument.value == option_name
                    for argument in node.args
                )
                and isinstance(node.func.value, ast.Name)
            ):
                parser_defaults.extend(
                    (node.func.value.id, keyword.value)
                    for keyword in node.keywords
                    if keyword.arg == "default"
                )
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
                if (
                    isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == "parse_args"
                    and isinstance(node.value.func.value, ast.Name)
                ):
                    returned_parser_names.add(node.value.func.value.id)
                constructor_candidates.extend(
                    keyword.value
                    for keyword in node.value.keywords
                    if keyword.arg == expression.attr
                )
        candidates.extend(constructor_candidates)
        candidates.extend(
            value for parser_name, value in parser_defaults if parser_name in returned_parser_names
        )
        assignments = function_assignments
    if len(candidates) != 1:
        return False
    return _direct_path_expression_binds_record(
        candidates[0],
        assignments=assignments,
        record_path=record_path,
        basename=basename,
        seen=frozenset(),
    )


def _unique_function_definition(tree: ast.Module, function_name: str) -> ast.FunctionDef | None:
    functions = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    return functions[0] if len(functions) == 1 else None


def _unique_direct_call(tree: ast.Module, function_name: str) -> ast.Call | None:
    calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == function_name
    )
    return calls[0] if len(calls) == 1 else None


def _call_argument(
    call: ast.Call,
    parameters: tuple[ast.arg, ...],
    parameter_name: str,
) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == parameter_name:
            return keyword.value
    position = next(
        (index for index, parameter in enumerate(parameters) if parameter.arg == parameter_name),
        None,
    )
    if position is None or position >= len(call.args):
        return None
    return call.args[position]


def _containing_scope(tree: ast.Module, target: ast.AST) -> ast.Module | ast.FunctionDef:
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and any(child is target for child in ast.walk(node))
    ]
    if not candidates:
        return tree
    return min(
        candidates,
        key=lambda node: getattr(node, "end_lineno", node.lineno) - node.lineno,
    )


def _simple_assignments(scope: ast.AST) -> dict[str, ast.expr]:
    assignments: dict[str, ast.expr] = {}
    repeated: set[str] = set()
    body = getattr(scope, "body", ())
    for statement in body:
        name: str | None = None
        value: ast.expr | None = None
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            name = statement.targets[0].id
            value = statement.value
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            name = statement.target.id
            value = statement.value
        if name is None or value is None:
            continue
        if name in assignments:
            repeated.add(name)
        assignments[name] = value
    return {name: value for name, value in assignments.items() if name not in repeated}


def _resolve_name(node: ast.expr, assignments: dict[str, ast.expr]) -> ast.expr:
    seen: set[str] = set()
    current = node
    while isinstance(current, ast.Name) and current.id in assignments and current.id not in seen:
        seen.add(current.id)
        current = assignments[current.id]
    return current


def _empty_string_join(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        and isinstance(node.func.value, ast.Constant)
        and node.func.value.value == ""
        and len(node.args) == 1
        and not node.keywords
    )


def _read_text_receiver(node: ast.expr) -> ast.expr | None:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "splitlines"
        and not node.args
        and not node.keywords
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Attribute)
        and node.func.value.func.attr == "read_text"
    ):
        return None
    return node.func.value.func.value


def _line_projection(node: ast.expr, line_name: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == line_name
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"strip", "upper"}
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == line_name
        and not node.args
        and not node.keywords
    )


def _permitted_line_filter(node: ast.expr, line_name: str) -> bool:
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        return bool(node.values) and all(
            _permitted_line_filter(value, line_name) for value in node.values
        )
    if isinstance(node, ast.Call):
        return _line_method_call(node, line_name, "strip", None)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _line_method_call(node.operand, line_name, "startswith", ">") or _line_method_call(
            node.operand, line_name, "lstrip_startswith", ">"
        )
    return False


def _line_method_call(node: ast.expr, line_name: str, method: str, literal: str | None) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if method == "lstrip_startswith":
        receiver = node.func.value
        return (
            node.func.attr == "startswith"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == literal
            and isinstance(receiver, ast.Call)
            and isinstance(receiver.func, ast.Attribute)
            and receiver.func.attr == "lstrip"
            and isinstance(receiver.func.value, ast.Name)
            and receiver.func.value.id == line_name
            and not receiver.args
            and not receiver.keywords
            and not node.keywords
        )
    return (
        node.func.attr == method
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == line_name
        and (
            (literal is None and not node.args)
            or (
                len(node.args) == 1
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == literal
            )
        )
        and not node.keywords
    )


def _record_source_ref(record: _RecordShape) -> dict[str, Any]:
    return {
        **record.item.source_ref,
        "locator": f"{record.item.path}:1-2",
        "start_line": 1,
        "end_line": 2,
        "quoted_text": f"{record.sequence}\n{record.label}",
    }


def _join_source_ref(source: FrozenCalculationInput, join: _JoinShape) -> dict[str, Any]:
    return {
        **source.source_ref,
        "locator": f"{source.path}:{join.start_line}-{join.end_line}",
        "start_line": join.start_line,
        "end_line": join.end_line,
        "quoted_text": join.quoted_text,
    }
