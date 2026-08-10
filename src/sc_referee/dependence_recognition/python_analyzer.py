"""Fail-closed static proposing analyzer for dependence recognition v1.

The module imports the four guarded-parse helpers permitted by Resolution 7
from ``founder_orientation_dataflow``.  The founder module ban is applied to
the live tree after the three explicitly supported SciPy import forms have
been independently validated and removed from that guard's stdlib-only view.
No project-authored module is imported or executed by the analysis.

This analyzer is deliberately untrusted.  It proposes a provisional
``DependenceCertificate`` whose fact-derived observation identities and sink
conclusion are empty/placeholders.  ``discharge_dependence_proposal`` is the
controller-side boundary: it calls the digest-bound CSV prover over frozen
bytes, fills only fields determined by the returned fact, supplies that fact
to the certificate kernel through the external trusted-fact argument, and
only then constructs a domain-neutral ``DependenceCase``.
"""

from __future__ import annotations

import ast
import csv
import io
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, cast

from sc_referee.core.ids import semantic_digest
from sc_referee.dependence_core import (
    SAFEGUARD_IDS,
    DependenceCase,
    EvidenceState,
    Membership,
    SafeguardCheck,
)
from sc_referee.dependence_core import (
    RecordRef as CoreRecordRef,
)
from sc_referee.dependence_recognition.certificate import (
    dependence_replay_digest,
    verify_dependence_certificate,
)
from sc_referee.dependence_recognition.csv_domain import (
    certified_unit_key_row_count,
    prove_unit_key_multiplicity,
    unit_key_row_domain,
)
from sc_referee.dependence_recognition.ir import (
    MAX_V1_MEMBERSHIPS,
    SPLITLINES_ONLY_SEPARATORS,
    BoundPackageVersion,
    DependenceCaseBinding,
    DependenceCertificate,
    DependenceConclusion,
    EvidenceDeclaration,
    FrameLineage,
    FrameTransform,
    FrameTransformOperation,
    HumanMethodAuthorization,
    MaterialInputBinding,
    ProcedureCall,
    ReaderBinding,
    ReaderForm,
    RecordRef,
    SafeguardBasis,
    SafeguardCheckObligation,
    SinkLineageObligation,
    UnitKeyMultiplicityFact,
    UnitKeyMultiplicityObligation,
    VerifiedDependenceCertificate,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
)
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    _guarded_parse,
    _imports_case_module,
    _module_bans,
    _python_parser_supported,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    Effect,
    EvidencePoint,
    LineModel,
)

AnalysisState = Literal["proposal", "question", "unsupported", "not_applicable"]
DischargeState = Literal["verified", "question", "unsupported", "not_applicable"]

_MAX_SOURCE_BYTES = 1 * 1024 * 1024
_MAX_AST_NODES = 50_000
_DIALECT = "excel"
_SUPPORTED_VERSION = "1.14.0"
_PROCEDURES = frozenset(
    {
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
        "scipy.stats.ttest_rel",
    }
)
_AGGREGATION_SAFEGUARD = "safeguard:unit-level-aggregation"
_PAIRED_SAFEGUARD = "safeguard:paired-or-blocked-procedure"
_PIN_RE = re.compile(r"^\s*scipy\s*==\s*([A-Za-z0-9.!+_-]+)\s*(?:#.*)?$")


@dataclass(frozen=True)
class PythonDependenceAnalysis:
    """One untrusted static-analysis outcome before trusted data discharge."""

    state: AnalysisState
    certificate: DependenceCertificate | None
    case: DependenceCase | None
    candidate_key_columns: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...]
    unsupported_constructs: tuple[str, ...]
    effects: tuple[Effect, ...]
    basis: str


@dataclass(frozen=True)
class DischargedDependenceAnalysis:
    """Controller result after trusted data proof and certificate verification."""

    state: DischargeState
    certificate: DependenceCertificate | None
    trusted_multiplicity_facts: tuple[UnitKeyMultiplicityFact, ...]
    verified_certificate: VerifiedDependenceCertificate | None
    case: DependenceCase | None
    basis: str


@dataclass(frozen=True)
class _AuthorityResolution:
    authority: HumanMethodAuthorization | None
    ambiguous: bool


@dataclass(frozen=True)
class _Read:
    name: str
    path: str
    reader_form: str
    line_model: str
    token: str
    node: ast.AST


@dataclass(frozen=True)
class _Procedure:
    target_name: str
    resolved_callable: str
    argument_tokens: tuple[str, ...]
    node: ast.Call
    statement: ast.Assign
    token: str
    result_token: str


@dataclass(frozen=True)
class _Sink:
    path: str
    result_token: str
    node: ast.Call
    token: str


@dataclass(frozen=True)
class _OpenHandle:
    path: str
    mode: str


class _TraceEngine:
    """A deliberately small, single-module abstract interpreter."""

    def __init__(self, document: InspectionDocument) -> None:
        self.document = document
        self.bound_names: set[str] = set()
        self.bindings: dict[str, str] = {}
        self.path_values: dict[str, str] = {}
        self.open_handles: dict[str, _OpenHandle] = {}
        self.frame_names: set[str] = set()
        self.operand_frames: dict[str, str] = {}
        self.result_tokens: dict[str, str] = {}
        self.read: _Read | None = None
        self.current_frame_name: str | None = None
        self.current_output_token: str | None = None
        self.transforms: list[FrameTransform] = []
        self.transform_nodes: list[ast.AST] = []
        self.procedures: list[_Procedure] = []
        self.sinks: list[_Sink] = []
        self.unsupported: set[str] = set()
        self.effects: list[Effect] = []
        self.live_statements: list[ast.stmt] = []
        self.dead_statements: list[ast.stmt] = []

    def analyze(self, tree: ast.Module) -> None:
        self._process_sequence(tree.body, dead=False)

    def _process_sequence(self, statements: list[ast.stmt], *, dead: bool) -> None:
        for statement in statements:
            if dead:
                self.dead_statements.extend(_statement_subtree(statement))
                continue
            self.live_statements.append(statement)
            if isinstance(statement, ast.If) and _is_false_guard(statement):
                self._process_sequence(statement.body, dead=True)
                if statement.orelse:
                    self._unsupported(statement, "conditional-control-flow")
                continue
            if isinstance(statement, ast.If) and _is_main_guard(statement):
                self._process_sequence(statement.body, dead=False)
                continue
            if isinstance(statement, ast.Import):
                self._import(statement)
            elif isinstance(statement, ast.ImportFrom):
                self._import_from(statement)
            elif isinstance(statement, ast.Assign):
                self._assign(statement)
            elif isinstance(statement, ast.Expr):
                if isinstance(statement.value, ast.Constant) and isinstance(
                    statement.value.value, str
                ):
                    continue
                if not self._sink(statement.value):
                    self._unsupported(statement, "unsupported-expression-statement")
            elif isinstance(statement, ast.With):
                self._with(statement)
            elif isinstance(statement, ast.Pass):
                continue
            else:
                self._unsupported(statement, _unsupported_kind(statement))

    def _import(self, statement: ast.Import) -> None:
        for alias in statement.names:
            local = alias.asname or alias.name.split(".")[0]
            if not self._reserve_name(local, statement):
                continue
            if alias.name == "csv":
                self.bindings[local] = "csv"
            elif alias.name == "pathlib":
                self.bindings[local] = "pathlib"
            elif alias.name == "scipy.stats":
                self.bindings[local] = "scipy.stats" if alias.asname else "scipy"
            elif alias.name.split(".")[0] == "pandas":
                self._unsupported(statement, "pandas-frame-model")
            else:
                self._unsupported(statement, "unsupported-import")

    def _import_from(self, statement: ast.ImportFrom) -> None:
        if statement.level:
            self._unsupported(statement, "relative-import")
            return
        module = statement.module or ""
        for alias in statement.names:
            local = alias.asname or alias.name
            if not self._reserve_name(local, statement):
                continue
            if module == "pathlib" and alias.name == "Path":
                self.bindings[local] = "pathlib.Path"
            elif module == "scipy" and alias.name == "stats":
                self.bindings[local] = "scipy.stats"
            elif module == "scipy.stats" and alias.name in {
                "ttest_ind",
                "mannwhitneyu",
                "ttest_rel",
            }:
                self.bindings[local] = f"scipy.stats.{alias.name}"
            elif module.split(".")[0] == "pandas":
                self._unsupported(statement, "pandas-frame-model")
            else:
                self._unsupported(statement, "unsupported-import")

    def _assign(self, statement: ast.Assign) -> None:
        tuple_identity = _tuple_identity_assignment(statement)
        if tuple_identity is not None:
            target, source = tuple_identity
            if not self._reserve_name(target, statement):
                return
            self._identity_alias(source, target, statement)
            return
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            self._unsupported(statement, "mutation-or-complex-assignment")
            return
        target = statement.targets[0].id
        if not self._reserve_name(target, statement):
            return
        value = statement.value
        qualified = self._qualified(value)
        if isinstance(value, ast.Name) and value.id in self.bindings:
            origin = self.bindings[value.id]
            if origin == "scipy.stats":
                self._bind_once(target, origin, statement)
                return
            self._unsupported(statement, "callable-or-import-rebinding")
            return
        if target in self.bindings:
            self._unsupported(statement, "callable-or-import-rebinding")
            return
        path = self._path_expression(value)
        if path is not None:
            self.path_values[target] = path
            return
        read = self._reader(value, target, statement)
        if read is not None:
            if self.read is not None:
                self._unsupported(statement, "multiple-reader-lineages")
                return
            self.read = read
            self.current_frame_name = target
            self.current_output_token = read.token
            self.frame_names = {target}
            self.operand_frames[target] = read.token
            return
        if isinstance(value, ast.Name) and value.id in self.frame_names:
            self._identity_alias(value.id, target, statement)
            return
        aggregation = self._aggregation(value, target, statement)
        if aggregation is not None:
            self.transforms.append(aggregation)
            self.transform_nodes.append(statement)
            self.current_frame_name = target
            self.current_output_token = aggregation.token
            self.frame_names = {target}
            self.operand_frames[target] = aggregation.token
            return
        operand_frame = self._full_row_projection(value)
        if operand_frame is not None:
            self.operand_frames[target] = operand_frame
            return
        procedure = self._procedure(value, target, statement)
        if procedure is not None:
            self.procedures.append(procedure)
            self.result_tokens[target] = procedure.result_token
            return
        if isinstance(value, ast.Name) and value.id in self.result_tokens:
            self.result_tokens[target] = self.result_tokens[value.id]
            return
        if qualified is not None and qualified.startswith("pandas."):
            self._unsupported(statement, "pandas-frame-model")
            return
        self._unsupported(statement, "unsupported-assignment")

    def _with(self, statement: ast.With) -> None:
        if len(statement.items) != 1:
            self._unsupported(statement, "unsupported-with-statement")
            return
        item = statement.items[0]
        if not isinstance(item.optional_vars, ast.Name):
            self._unsupported(statement, "unsupported-with-binding")
            return
        opened = self._open_expression(item.context_expr)
        if opened is None:
            self._unsupported(statement, "unsupported-with-resource")
            return
        name = item.optional_vars.id
        if not self._reserve_name(name, statement):
            return
        self.open_handles[name] = opened
        self._process_sequence(statement.body, dead=False)
        self.open_handles.pop(name, None)

    def _reader(
        self,
        expression: ast.expr,
        target: str,
        statement: ast.Assign,
    ) -> _Read | None:
        value = expression
        materialized = (
            isinstance(value, ast.Call)
            and self._qualified(value.func) == "list"
            and len(value.args) == 1
            and not value.keywords
        )
        if materialized:
            assert isinstance(value, ast.Call)
            value = value.args[0]
        else:
            if isinstance(value, ast.Call) and self._qualified(value.func) == "csv.DictReader":
                self._unsupported(statement, "unmaterialized-csv-reader-iterator")
            return None
        if not isinstance(value, ast.Call) or self._qualified(value.func) != "csv.DictReader":
            return None
        if len(value.args) != 1 or value.keywords:
            self._unsupported(statement, "unsupported-csv-reader-arguments")
            return None
        source = value.args[0]
        split_path = self._splitlines_source(source)
        if split_path is not None:
            form = "csv_dictreader_splitlines"
            line_model = "splitlines"
            path = split_path
        else:
            opened = self._reader_open_source(source)
            if opened is None:
                self._unsupported(statement, "unsupported-csv-reader-source")
                return None
            form = "csv_dictreader_file"
            line_model = "csv_newline"
            path = opened.path
        return _Read(
            name=target,
            path=path,
            reader_form=form,
            line_model=line_model,
            token=_token(self.document.path, statement, "reader"),
            node=value,
        )

    def _splitlines_source(self, expression: ast.expr) -> str | None:
        if not (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Attribute)
            and expression.func.attr == "splitlines"
            and not expression.args
            and not expression.keywords
        ):
            return None
        read_text = expression.func.value
        if not (
            isinstance(read_text, ast.Call)
            and isinstance(read_text.func, ast.Attribute)
            and read_text.func.attr == "read_text"
            and not read_text.args
            and _only_utf8_encoding(read_text.keywords)
        ):
            return None
        return self._path_expression(read_text.func.value)

    def _reader_open_source(self, expression: ast.expr) -> _OpenHandle | None:
        if isinstance(expression, ast.Name):
            opened = self.open_handles.get(expression.id)
        else:
            opened = self._open_expression(expression)
        if opened is None or opened.mode not in {"r", "rt"}:
            return None
        return opened

    def _open_expression(self, expression: ast.expr) -> _OpenHandle | None:
        if not isinstance(expression, ast.Call):
            return None
        qualified = self._qualified(expression.func)
        path: str | None = None
        positionals = list(expression.args)
        if qualified == "open":
            if not positionals:
                return None
            path_expression = positionals.pop(0)
            path = (
                path_expression.value
                if isinstance(path_expression, ast.Constant)
                and isinstance(path_expression.value, str)
                else self._path_expression(path_expression)
            )
        elif isinstance(expression.func, ast.Attribute) and expression.func.attr == "open":
            path = self._path_expression(expression.func.value)
        if path is None or len(positionals) > 1:
            return None
        mode = "r"
        if positionals:
            if not isinstance(positionals[0], ast.Constant) or not isinstance(
                positionals[0].value, str
            ):
                return None
            mode = positionals[0].value
        keyword_values = {item.arg: item.value for item in expression.keywords if item.arg}
        if len(keyword_values) != len(expression.keywords):
            return None
        if set(keyword_values) - {"mode", "encoding", "newline"}:
            return None
        if "mode" in keyword_values:
            mode_value = keyword_values["mode"]
            if not isinstance(mode_value, ast.Constant) or not isinstance(mode_value.value, str):
                return None
            mode = mode_value.value
        if "encoding" in keyword_values and not _utf8_literal(keyword_values["encoding"]):
            return None
        if "encoding" not in keyword_values:
            return None
        if "newline" not in keyword_values or not _empty_string(keyword_values["newline"]):
            return None
        return _OpenHandle(path, mode)

    def _aggregation(
        self,
        expression: ast.expr,
        target: str,
        statement: ast.Assign,
    ) -> FrameTransform | None:
        del target
        if not (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Attribute)
            and expression.func.attr in {"mean", "first"}
            and not expression.args
            and not expression.keywords
            and isinstance(expression.func.value, ast.Call)
        ):
            return None
        groupby = expression.func.value
        if not (
            isinstance(groupby.func, ast.Attribute)
            and groupby.func.attr == "groupby"
            and isinstance(groupby.func.value, ast.Name)
            and groupby.func.value.id == self.current_frame_name
            and len(groupby.args) == 1
            and not groupby.keywords
        ):
            self._unsupported(statement, "unsupported-frame-transform")
            return None
        columns = _string_columns(groupby.args[0])
        if columns is None:
            self._unsupported(statement, "dynamic-grouping-operand")
            return None
        operation: FrameTransformOperation = cast(
            FrameTransformOperation,
            f"unit_groupby_{expression.func.attr}",
        )
        token = _token(self.document.path, statement, f"transform:{operation}")
        return FrameTransform(
            token=token,
            operation=operation,
            input_row_domain="pending",
            output_row_domain=f"pending:{token}",
            grouping_columns=columns,
            evidence_ids=(_evidence_id(self.document.path, statement, operation),),
        )

    def _full_row_projection(self, expression: ast.expr) -> str | None:
        if not isinstance(expression, ast.ListComp) or len(expression.generators) != 1:
            return None
        generator = expression.generators[0]
        if (
            generator.is_async
            or generator.ifs
            or not isinstance(generator.target, ast.Name)
            or not isinstance(generator.iter, ast.Name)
            or generator.iter.id != self.current_frame_name
            or self.current_output_token is None
        ):
            return None
        element = expression.elt
        if (
            isinstance(element, ast.Call)
            and self._qualified(element.func) in {"int", "float", "str"}
            and len(element.args) == 1
            and not element.keywords
        ):
            element = element.args[0]
        if not (
            isinstance(element, ast.Subscript)
            and isinstance(element.value, ast.Name)
            and element.value.id == generator.target.id
            and isinstance(element.slice, ast.Constant)
            and isinstance(element.slice.value, str)
            and element.slice.value
        ):
            return None
        return self.current_output_token

    def _procedure(
        self,
        expression: ast.expr,
        target: str,
        statement: ast.Assign,
    ) -> _Procedure | None:
        if not isinstance(expression, ast.Call):
            return None
        resolved = self._qualified(expression.func)
        if resolved not in _PROCEDURES:
            if resolved and (
                resolved.startswith("scipy.")
                or resolved.startswith("statsmodels.")
                or any(
                    isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                    for arg in expression.args
                )
            ):
                self._unsupported(statement, "unsupported-procedure-or-string-formula")
            return None
        if len(expression.args) != 2 or expression.keywords:
            self._unsupported(statement, "unsupported-procedure-signature")
            return None
        bound_frames: list[str] = []
        argument_tokens: list[str] = []
        for index, argument in enumerate(expression.args):
            if not isinstance(argument, ast.Name):
                self._unsupported(statement, "dynamic-procedure-operand")
                return None
            frame = self.operand_frames.get(argument.id)
            if frame is None or frame != self.current_output_token:
                self._unsupported(statement, "procedure-operand-not-bound-to-frame")
                return None
            bound_frames.append(frame)
            argument_tokens.append(
                _token(self.document.path, argument, f"procedure-argument:{index}:{argument.id}")
            )
        del bound_frames
        token = _token(self.document.path, statement, "procedure-call")
        return _Procedure(
            target_name=target,
            resolved_callable=resolved,
            argument_tokens=tuple(argument_tokens),
            node=expression,
            statement=statement,
            token=token,
            result_token=_token(self.document.path, statement, f"procedure-result:{target}"),
        )

    def _sink(self, expression: ast.expr) -> bool:
        if not isinstance(expression, ast.Call):
            return False
        path: str | None = None
        payload: ast.expr | None = None
        if isinstance(expression.func, ast.Attribute) and expression.func.attr == "write_text":
            path = self._path_expression(expression.func.value)
            if len(expression.args) != 1 or not _only_utf8_encoding(expression.keywords):
                return False
            payload = expression.args[0]
        elif (
            isinstance(expression.func, ast.Attribute)
            and expression.func.attr in {"write", "writelines"}
            and isinstance(expression.func.value, ast.Name)
        ):
            handle = self.open_handles.get(expression.func.value.id)
            if handle is None or handle.mode not in {"w", "wt"} or len(expression.args) != 1:
                return False
            if expression.keywords:
                return False
            path = handle.path
            payload = expression.args[0]
        if path is None or payload is None:
            return False
        result_token = self._payload_result(payload)
        if result_token is None:
            return False
        self.sinks.append(
            _Sink(
                path=path,
                result_token=result_token,
                node=expression,
                token=_token(self.document.path, expression, "sink"),
            )
        )
        return True

    def _payload_result(self, expression: ast.expr) -> str | None:
        value = expression
        if (
            isinstance(value, ast.Call)
            and self._qualified(value.func) == "str"
            and len(value.args) == 1
            and not value.keywords
        ):
            value = value.args[0]
        if isinstance(value, ast.Name):
            return self.result_tokens.get(value.id)
        if isinstance(value, ast.JoinedStr):
            formatted = [item for item in value.values if isinstance(item, ast.FormattedValue)]
            if (
                len(formatted) != 1
                or any(
                    not isinstance(item, ast.Constant | ast.FormattedValue) for item in value.values
                )
                or not isinstance(formatted[0].value, ast.Name)
                or formatted[0].conversion != -1
                or formatted[0].format_spec is not None
            ):
                return None
            return self.result_tokens.get(formatted[0].value.id)
        return None

    def _path_expression(self, expression: ast.expr) -> str | None:
        if isinstance(expression, ast.Name):
            return self.path_values.get(expression.id)
        if not isinstance(expression, ast.Call) or len(expression.args) != 1 or expression.keywords:
            return None
        if self._qualified(expression.func) != "pathlib.Path":
            return None
        argument = expression.args[0]
        return (
            argument.value
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            else None
        )

    def _qualified(self, expression: ast.expr) -> str | None:
        if isinstance(expression, ast.Name):
            return self.bindings.get(expression.id, expression.id)
        if isinstance(expression, ast.Attribute):
            prefix = self._qualified(expression.value)
            return f"{prefix}.{expression.attr}" if prefix else None
        return None

    def _bind_once(self, target: str, origin: str, node: ast.AST) -> None:
        if target in self.bindings:
            self._unsupported(node, "callable-or-import-rebinding")
        else:
            self.bindings[target] = origin

    def _reserve_name(self, name: str, node: ast.AST) -> bool:
        if name in self.bound_names:
            self._unsupported(node, "name-rebinding")
            return False
        self.bound_names.add(name)
        return True

    def _identity_alias(self, source: str, target: str, statement: ast.Assign) -> None:
        if source != self.current_frame_name or self.current_output_token is None:
            self._unsupported(statement, "nonlinear-frame-alias")
            return
        token = _token(self.document.path, statement, "transform:identity")
        evidence_id = _evidence_id(self.document.path, statement, "identity")
        self.transforms.append(
            FrameTransform(
                token=token,
                operation="identity",
                input_row_domain="pending",
                output_row_domain="pending",
                grouping_columns=(),
                evidence_ids=(evidence_id,),
            )
        )
        self.transform_nodes.append(statement)
        self.current_frame_name = target
        self.current_output_token = token
        self.frame_names = {target}
        self.operand_frames[target] = token

    def _unsupported(self, node: ast.AST, kind: str) -> None:
        self.unsupported.add(kind)
        reads = frozenset(
            child.id
            for child in ast.walk(node)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
        )
        self.effects.append(
            Effect(
                reads=reads,
                writes=frozenset({"*"}),
                aliases=frozenset(),
                may_raise=True,
                opaque=True,
                reason=f"unmodeled subtree: {kind}",
            )
        )


def analyze_dependence_python(
    context: FrozenInspectionContext,
    *,
    parser_id: str = "python-ast",
    parser_version: str = "3.11",
) -> PythonDependenceAnalysis:
    """Analyze frozen Python bytes and propose at most one closed v1 lineage."""

    python_documents = tuple(
        document for document in context.documents if document.media_type == "text/x-python"
    )
    if not python_documents:
        return _analysis_without_certificate(
            "not_applicable",
            context,
            basis="No frozen Python document was available.",
        )
    selected_report_path = _selected_artifact_path(context)
    if selected_report_path is None:
        return _analysis_without_certificate(
            "question",
            context,
            unresolved=("selected-result-sink",),
            basis="The selected artifact did not bind one exact report path.",
        )
    traces: list[tuple[InspectionDocument, _TraceEngine]] = []
    case_module_names = _case_module_names(context)
    for document in python_documents:
        if (
            not _parser_is_supported(document, parser_id, parser_version)
            or len(document.content) > _MAX_SOURCE_BYTES
        ):
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=("unsupported-python-parser-or-source-ceiling",),
                basis="A Python document lacked the exact guarded parser result or exceeded the source ceiling.",
            )
        try:
            source = document.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=("non-utf8-python-source",),
                basis="A Python document was not strict UTF-8.",
            )
        tree = _guarded_parse(source, filename=document.path)
        if tree is None or sum(1 for _ in ast.walk(tree)) > _MAX_AST_NODES:
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=("python-parse-or-ast-ceiling",),
                basis="Guarded parsing failed or the AST exceeded the v1 ceiling.",
            )
        live_tree = _live_guard_tree(tree)
        other_modules = case_module_names - {Path(document.path).stem}
        if _imports_pandas(live_tree):
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=("pandas-frame-model",),
                effects=(_opaque_effect(live_tree, "pandas-frame-model"),),
                basis="Pandas frame semantics are outside the named v1 reader coverage.",
            )
        if (
            _imports_case_module(live_tree, other_modules)
            or _dependence_module_bans(live_tree)
            or any(isinstance(node, ast.NamedExpr) for node in ast.walk(live_tree))
        ):
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=("module-ban-or-dynamic-binding",),
                effects=(_opaque_effect(live_tree, "module-ban-or-dynamic-binding"),),
                basis="A live module construct escaped the v1 static binding discipline.",
            )
        engine = _TraceEngine(document)
        try:
            engine.analyze(tree)
        except (RecursionError, MemoryError, OverflowError):
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=("analyzer-resource-ceiling",),
                basis="Static analysis exceeded a bounded resource ceiling.",
            )
        if engine.unsupported:
            return _analysis_without_certificate(
                "unsupported",
                context,
                unsupported=tuple(sorted(engine.unsupported)),
                effects=tuple(engine.effects),
                basis="At least one live subtree was outside the v1 grammar.",
            )
        if engine.read is not None or engine.procedures or engine.sinks:
            traces.append((document, engine))
    if not traces:
        return _analysis_without_certificate(
            "not_applicable",
            context,
            basis="No dependence-recognition procedure lineage was present.",
        )
    if len(traces) != 1:
        return _analysis_without_certificate(
            "question",
            context,
            unresolved=("multiple-python-lineages",),
            basis="More than one Python document contributed a candidate lineage.",
        )
    document, trace = traces[0]
    if trace.read is None or not trace.procedures or not trace.sinks:
        return _analysis_without_certificate(
            "unsupported",
            context,
            unsupported=("incomplete-reader-procedure-sink-lineage",),
            basis="The reader, procedure, and selected report sink were not all statically closed.",
        )
    if len(trace.procedures) != 1:
        return _analysis_without_certificate(
            "question",
            context,
            unresolved=("conflicting-procedure-calls",),
            basis="Multiple procedure calls cannot be resolved to one dependence conclusion.",
        )
    procedure = trace.procedures[0]
    selected_sinks = tuple(
        sink
        for sink in trace.sinks
        if sink.path == selected_report_path and sink.result_token == procedure.result_token
    )
    if len(selected_sinks) != 1 or len(trace.sinks) != 1:
        return _analysis_without_certificate(
            "question",
            context,
            unresolved=("selected-result-sink",),
            basis="The exact selected result sink was absent, competing, or ambiguous.",
        )

    read = trace.read
    authority_resolution = _authority(context)
    candidates = _candidate_key_columns(context, read)
    authority = authority_resolution.authority
    if authority_resolution.ambiguous or authority is None:
        unresolved = (
            "independent_unit_definition",
            *(f"candidate_unit_key:{column}" for column in candidates),
            "candidate_unit_key:none-of-these",
        )
        return _analysis_without_certificate(
            "question",
            context,
            candidate_columns=candidates,
            unresolved=unresolved,
            basis="No single matching human authorization selected an ordered unit key.",
        )
    if not _authority_refs_exist_once(context, authority) or not _procedure_record_allows(
        context,
        authority.procedure_ref,
        procedure.resolved_callable,
    ):
        unresolved = (
            "authorized-analysis-procedure-binding",
            *(f"candidate_unit_key:{column}" for column in candidates),
            "candidate_unit_key:none-of-these",
        )
        return _analysis_without_certificate(
            "question",
            context,
            candidate_columns=candidates,
            unresolved=unresolved,
            basis="The authority did not match extant analysis and procedure records.",
            authority=authority,
        )
    if authority.input_path != read.path:
        unresolved = (
            "authorized-input-binding",
            *(f"candidate_unit_key:{column}" for column in candidates),
            "candidate_unit_key:none-of-these",
        )
        return _analysis_without_certificate(
            "question",
            context,
            candidate_columns=candidates,
            unresolved=unresolved,
            basis="The authorized input does not equal the statically read input.",
            authority=authority,
        )
    path_materials = [item for item in context.material_inputs if item.path == read.path]
    if (
        len(path_materials) == 1
        and path_materials[0].content_digest != authority.input_content_digest
    ):
        unresolved = (
            "authorized-input-binding",
            *(f"candidate_unit_key:{column}" for column in candidates),
            "candidate_unit_key:none-of-these",
        )
        return _analysis_without_certificate(
            "question",
            context,
            candidate_columns=candidates,
            unresolved=unresolved,
            basis="The authority digest does not equal the frozen input digest.",
            authority=authority,
        )
    material = _material(context.material_inputs, read.path, authority.input_content_digest)
    if material is None:
        return _analysis_without_certificate(
            "unsupported",
            context,
            unsupported=("digest-bound-input-unavailable",),
            basis="The authorized source input was not present once with its full digest.",
            authority=authority,
        )
    if any(
        transform.operation != "identity"
        and transform.grouping_columns != authority.authorized_key_columns
        for transform in trace.transforms
    ):
        return _analysis_without_certificate(
            "unsupported",
            context,
            unsupported=("groupby-operand-not-authorized-unit-key",),
            basis="A collapsing transform grouped by a non-authorized operand.",
            authority=authority,
        )
    if (
        sum(
            transform.operation in {"unit_groupby_mean", "unit_groupby_first"}
            for transform in trace.transforms
        )
        > 1
    ):
        return _analysis_without_certificate(
            "unsupported",
            context,
            unsupported=("multiple-unit-collapsing-transforms",),
            basis="V1 models at most one unit-collapsing transform.",
            authority=authority,
        )
    version_material = _pinned_scipy_version(context.material_inputs)
    if version_material is None or version_material[0] != _SUPPORTED_VERSION:
        return _analysis_without_certificate(
            "unsupported",
            context,
            unsupported=("unsupported-or-unpinned-scipy-version",),
            basis="No unique bound requirements material pinned SciPy 1.14.0.",
            authority=authority,
        )
    affected_ref = _affected_target_ref(context, selected_report_path)
    if affected_ref is None:
        return _analysis_without_certificate(
            "question",
            context,
            unresolved=("affected_target",),
            basis="No unique result or claim record was bound to the selected report sink.",
            authority=authority,
        )
    certificate = _certificate(
        context=context,
        document=document,
        trace=trace,
        authority=authority,
        material=material,
        procedure=procedure,
        sink=selected_sinks[0],
        affected_ref=affected_ref,
        parser_id=parser_id,
        parser_version=parser_version,
        version_material=version_material[1],
    )
    return PythonDependenceAnalysis(
        state="proposal",
        certificate=certificate,
        case=None,
        candidate_key_columns=authority.authorized_key_columns,
        unresolved_dimensions=(),
        unsupported_constructs=(),
        effects=(),
        basis="One static lineage is inside the v1 envelope and awaits trusted CSV discharge.",
    )


def discharge_dependence_proposal(
    analysis: PythonDependenceAnalysis,
    context: FrozenInspectionContext,
) -> DischargedDependenceAnalysis:
    """Discharge data obligations over controller-frozen bytes and invoke the kernel."""

    if analysis.state != "proposal" or analysis.certificate is None:
        return DischargedDependenceAnalysis(
            state=cast(DischargeState, analysis.state),
            certificate=None,
            trusted_multiplicity_facts=(),
            verified_certificate=None,
            case=analysis.case,
            basis=analysis.basis,
        )
    certificate = analysis.certificate
    if not _proposal_matches_context(certificate, context):
        return _failed_discharge(certificate, "frozen-context-drift")
    facts: list[UnitKeyMultiplicityFact] = []
    for obligation in certificate.multiplicity_obligations:
        material = _material(
            context.material_inputs,
            obligation.input_binding.path,
            obligation.input_binding.content_digest,
        )
        if material is None:
            return _failed_discharge(certificate, "digest-bound-input-unavailable")
        fact = prove_unit_key_multiplicity(
            material,
            path=obligation.input_binding.path,
            content_digest=obligation.input_binding.content_digest,
            key_columns=obligation.key_columns,
            line_model=obligation.reader.line_model,
        )
        if fact is None:
            row_count = certified_unit_key_row_count(
                material,
                path=obligation.input_binding.path,
                content_digest=obligation.input_binding.content_digest,
                key_columns=obligation.key_columns,
                line_model=obligation.reader.line_model,
            )
            if row_count is not None and row_count > MAX_V1_MEMBERSHIPS:
                return _failed_discharge(certificate, "membership-scale-above-v1-bound")
            return _failed_discharge(certificate, "unit-key-multiplicity-proof-unavailable")
        facts.append(fact)
    if len(facts) != 1 or len(set(facts)) != 1:
        return _failed_discharge(certificate, "non-singleton-multiplicity-discharge")
    fact = facts[0]
    aggregation = any(
        transform.operation in {"unit_groupby_mean", "unit_groupby_first"}
        for transform in certificate.frame_lineage.transforms
    )
    analyzed_unit_ids = tuple(dict.fromkeys(fact.unit_ids)) if aggregation else fact.unit_ids
    analyzed_observations = analyzed_unit_ids if aggregation else fact.observation_ids
    if len(analyzed_observations) > MAX_V1_MEMBERSHIPS:
        return _failed_discharge(certificate, "membership-scale-above-v1-bound")
    repeated = tuple(
        sorted(unit_id for unit_id, count in Counter(analyzed_unit_ids).items() if count > 1)
    )
    conclusion: DependenceConclusion = "repeated_units" if repeated else "one_observation_per_unit"
    lineage = replace(
        certificate.frame_lineage,
        source_observation_ids=fact.observation_ids,
        analyzed_observation_ids=analyzed_observations,
    )
    sinks = tuple(replace(sink, conclusion=conclusion) for sink in certificate.sinks)
    data_declaration = EvidenceDeclaration(
        evidence_id=fact.evidence_id,
        point=EvidencePoint(fact.path, 1, 1, 1, 1),
    )
    evidence = tuple(
        sorted(
            {
                *certificate.evidence,
                data_declaration,
            }
        )
    )
    discharged = replace(
        certificate,
        frame_lineage=lineage,
        sinks=sinks,
        reaching_path_conclusions=(frozenset({conclusion}),),
        evidence=evidence,
    )
    discharged = replace(discharged, replay_digest=dependence_replay_digest(discharged))
    trusted_facts = tuple(facts)
    verified = verify_dependence_certificate(
        discharged,
        trusted_multiplicity_facts=trusted_facts,
    )
    if verified is None:
        return _failed_discharge(discharged, "certificate-kernel-refusal")
    case = _verified_case(verified, discharged)
    return DischargedDependenceAnalysis(
        state="verified",
        certificate=discharged,
        trusted_multiplicity_facts=trusted_facts,
        verified_certificate=verified,
        case=case,
        basis="The trusted CSV fact and certificate kernel closed the static dependence case.",
    )


def _certificate(
    *,
    context: FrozenInspectionContext,
    document: InspectionDocument,
    trace: _TraceEngine,
    authority: HumanMethodAuthorization,
    material: FrozenMaterialInput,
    procedure: _Procedure,
    sink: _Sink,
    affected_ref: RecordRef,
    parser_id: str,
    parser_version: str,
    version_material: FrozenMaterialInput,
) -> DependenceCertificate:
    assert trace.read is not None
    read = trace.read
    analysis_ref = authority.analysis_target_ref
    procedure_ref = authority.procedure_ref
    case_binding = DependenceCaseBinding(
        case_id=f"dependence-case:{semantic_digest({'source': document.content_digest, 'call': procedure.token})}",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        affected_target_ref=affected_ref,
        independent_unit_definition_id=authority.independent_unit_definition_id,
        authorized_key_columns=authority.authorized_key_columns,
        authority=authority,
    )
    input_binding = MaterialInputBinding(
        path=material.path,
        content_digest=material.content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type,
            material.asset_identity_ref.record_id,
        ),
    )
    reader = ReaderBinding(
        token=read.token,
        reader_form=cast(ReaderForm, read.reader_form),
        line_model=cast(LineModel, read.line_model),
        dialect=_DIALECT,
    )
    source_domain = unit_key_row_domain(material.path, material.content_digest, read.line_model)
    transforms: list[FrameTransform] = []
    current_domain = source_domain
    for transform in trace.transforms:
        output_domain = (
            current_domain
            if transform.operation == "identity"
            else semantic_digest(
                {
                    "kind": "dependence-frame-transform-v1",
                    "input_row_domain": current_domain,
                    "operation": transform.operation,
                    "grouping_columns": transform.grouping_columns,
                    "token": transform.token,
                }
            )
        )
        transforms.append(
            replace(
                transform,
                input_row_domain=current_domain,
                output_row_domain=output_domain,
            )
        )
        current_domain = output_domain
    output_token = transforms[-1].token if transforms else reader.token
    lineage_token = _token(document.path, read.node, "frame-lineage")
    result = ProcedureCall(
        token=procedure.token,
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        resolved_callable=procedure.resolved_callable,
        positional_argument_tokens=procedure.argument_tokens,
        positional_argument_frame_bindings=tuple(
            (argument, output_token) for argument in procedure.argument_tokens
        ),
        keyword_argument_names=(),
        frame_lineage_token=lineage_token,
        analyzed_row_domain=current_domain,
        package_version=BoundPackageVersion(
            package_name="scipy",
            version=_SUPPORTED_VERSION,
            evidence_ids=(_package_pin_evidence_id(version_material, _SUPPORTED_VERSION),),
        ),
        unit_operand_columns=(
            authority.authorized_key_columns
            if procedure.resolved_callable == "scipy.stats.ttest_rel"
            else ()
        ),
        result_token=procedure.result_token,
        evidence_ids=(_evidence_id(document.path, procedure.node, "procedure-call"),),
    )
    relevant_origins = {
        material.path,
        source_domain,
        current_domain,
        *(item.input_row_domain for item in transforms),
        *(item.output_row_domain for item in transforms),
    }
    relevant_bindings = {
        reader.token,
        lineage_token,
        output_token,
        result.token,
        result.result_token,
        *result.positional_argument_tokens,
        *(item.token for item in transforms),
    }
    lineage = FrameLineage(
        token=lineage_token,
        input_binding=input_binding,
        reader=reader,
        source_row_domain=source_domain,
        transforms=tuple(transforms),
        analyzed_row_domain=current_domain,
        source_observation_ids=(),
        analyzed_observation_ids=(),
        output_token=output_token,
        procedure_call_token=result.token,
        relevant_origins=frozenset(relevant_origins),
        relevant_bindings=frozenset(relevant_bindings),
    )
    sink_evidence_id = _evidence_id(document.path, sink.node, "selected-sink")
    sink_record = SinkLineageObligation(
        token=sink.token,
        path=sink.path,
        affected_target_ref=affected_ref,
        procedure_call_token=result.token,
        procedure_result_token=result.result_token,
        payload_tokens=frozenset({result.result_token}),
        selected_result=True,
        conclusion="one_observation_per_unit",
        evidence_ids=(sink_evidence_id,),
        relevant_origins=frozenset({material.path, current_domain}),
        relevant_bindings=frozenset({result.result_token}),
    )
    synthetic_constructs = {
        reader.token,
        lineage.token,
        result.token,
        sink_record.token,
        *(item.token for item in transforms),
    }
    statement_constructs = {
        _token(document.path, statement, "syntax") for statement in trace.live_statements
    }
    dead_constructs = {
        _token(document.path, statement, "syntax") for statement in trace.dead_statements
    }
    all_constructs = frozenset(synthetic_constructs | statement_constructs | dead_constructs)
    dead = frozenset(dead_constructs)
    active = all_constructs - dead
    expected_matches: dict[str, frozenset[str]] = {item: frozenset() for item in SAFEGUARD_IDS}
    aggregate_tokens = frozenset(
        item.token
        for item in transforms
        if item.operation in {"unit_groupby_mean", "unit_groupby_first"}
    )
    expected_matches[_AGGREGATION_SAFEGUARD] = aggregate_tokens
    if result.resolved_callable == "scipy.stats.ttest_rel":
        expected_matches[_PAIRED_SAFEGUARD] = frozenset({result.token})
    checks: list[SafeguardCheckObligation] = []
    declarations: set[EvidenceDeclaration] = set()
    transform_node_by_token = dict(
        zip((item.token for item in transforms), _transform_nodes(trace), strict=True)
    )
    for safeguard_id in SAFEGUARD_IDS:
        evidence_id = f"safeguard-check:{semantic_digest({'source': document.content_digest, 'safeguard': safeguard_id})}"
        matched = expected_matches[safeguard_id]
        basis: SafeguardBasis = (
            "recognized-collapse"
            if matched and safeguard_id == _AGGREGATION_SAFEGUARD
            else "registry-match"
            if matched
            else "completeness-equation"
        )
        checks.append(
            SafeguardCheckObligation(
                safeguard_id=safeguard_id,
                state="present" if matched else "absent",
                analysis_target_ref=analysis_ref,
                procedure_ref=procedure_ref,
                independent_unit_definition_id=authority.independent_unit_definition_id,
                evidence_ids=(evidence_id,),
                basis=basis,
                complete_syntactic_construct_tokens=all_constructs,
                modeled_construct_tokens=active,
                proven_dead_construct_tokens=dead,
                matched_construct_tokens=matched,
            )
        )
        if matched and safeguard_id == _AGGREGATION_SAFEGUARD:
            evidence_point = _point(document.path, transform_node_by_token[next(iter(matched))])
        elif matched:
            evidence_point = _point(document.path, procedure.node)
        else:
            evidence_point = _module_point(document)
        declarations.add(EvidenceDeclaration(evidence_id, evidence_point))
    evidence_nodes = [
        *(item for transform in transforms for item in transform.evidence_ids),
        *result.package_version.evidence_ids,
        *result.evidence_ids,
        *sink_record.evidence_ids,
    ]
    node_by_evidence = {
        **{
            evidence_id: transform_node
            for transform, transform_node in zip(transforms, _transform_nodes(trace), strict=True)
            for evidence_id in transform.evidence_ids
        },
        **{evidence_id: procedure.node for evidence_id in result.package_version.evidence_ids},
        **{evidence_id: procedure.node for evidence_id in result.evidence_ids},
        **{evidence_id: sink.node for evidence_id in sink_record.evidence_ids},
    }
    declarations.update(
        EvidenceDeclaration(evidence_id, _point(document.path, node_by_evidence[evidence_id]))
        for evidence_id in evidence_nodes
    )
    obligation = UnitKeyMultiplicityObligation(
        input_binding=input_binding,
        reader=reader,
        row_domain=source_domain,
        key_columns=authority.authorized_key_columns,
    )
    certificate = DependenceCertificate(
        source_path=document.path,
        source_digest=document.content_digest,
        parser_id=parser_id,
        parser_version=parser_version,
        dependency_closure_digest=_dependency_closure_digest(context.material_inputs),
        proposed_case_digest=semantic_digest(
            {
                "case_binding": {
                    "case_id": case_binding.case_id,
                    "analysis_target_ref": {
                        "record_type": case_binding.analysis_target_ref.record_type,
                        "record_id": case_binding.analysis_target_ref.record_id,
                    },
                    "procedure_ref": {
                        "record_type": case_binding.procedure_ref.record_type,
                        "record_id": case_binding.procedure_ref.record_id,
                    },
                    "affected_target_ref": {
                        "record_type": case_binding.affected_target_ref.record_type,
                        "record_id": case_binding.affected_target_ref.record_id,
                    },
                    "independent_unit_definition_id": case_binding.independent_unit_definition_id,
                    "authorized_key_columns": case_binding.authorized_key_columns,
                    "authority_record_id": case_binding.authority.record_id,
                },
                "source_digest": document.content_digest,
                "reader": {
                    "token": reader.token,
                    "reader_form": reader.reader_form,
                    "line_model": reader.line_model,
                    "dialect": reader.dialect,
                },
                "procedure": result.resolved_callable,
                "sink": sink.path,
            }
        ),
        replay_digest="sha256:" + "0" * 64,
        case_binding=case_binding,
        frame_lineage=lineage,
        procedure_call=result,
        multiplicity_obligations=(obligation,),
        safeguard_checks=tuple(checks),
        sinks=(sink_record,),
        all_syntactic_construct_tokens=all_constructs,
        dead_syntactic_construct_tokens=dead,
        all_sink_tokens=frozenset({sink_record.token}),
        dead_sink_tokens=frozenset(),
        reaching_path_conclusions=(frozenset({"one_observation_per_unit"}),),
        effects=(),
        unknowns=(),
        safeguard_registry_ids=SAFEGUARD_IDS,
        output_ceiling="evaluation_candidate",
        wording_ceiling="static_code_relationship_only",
        evidence=tuple(sorted(declarations)),
    )
    return replace(certificate, replay_digest=dependence_replay_digest(certificate))


def _verified_case(
    verified: VerifiedDependenceCertificate,
    certificate: DependenceCertificate,
) -> DependenceCase:
    fact = verified.domain_fact
    aggregation = any(
        transform.operation in {"unit_groupby_mean", "unit_groupby_first"}
        for transform in verified.frame_lineage.transforms
    )
    if aggregation:
        memberships = tuple(
            Membership(item, item, (fact.evidence_id,))
            for item in verified.frame_lineage.analyzed_observation_ids
        )
        separate_state: EvidenceState = "refuted"
    else:
        memberships = tuple(
            Membership(observation, unit, (fact.evidence_id,))
            for observation, unit in zip(fact.observation_ids, fact.unit_ids, strict=True)
        )
        separate_state = "established"
    binding = verified.case_binding
    safeguards = tuple(
        SafeguardCheck(
            safeguard_id=check.safeguard_id,
            state=check.state,
            analysis_target_ref=_core_ref(check.analysis_target_ref),
            procedure_ref=_core_ref(check.procedure_ref),
            independent_unit_definition_id=check.independent_unit_definition_id,
            evidence_ids=check.evidence_ids,
            basis=check.basis,
        )
        for check in certificate.safeguard_checks
    )
    paired = verified.procedure_call.resolved_callable == "scipy.stats.ttest_rel"
    return DependenceCase(
        case_id=binding.case_id,
        analyzed_observation_ids=verified.frame_lineage.analyzed_observation_ids,
        independent_unit_definition_id=binding.independent_unit_definition_id,
        unit_definition_state="established",
        memberships=memberships,
        membership_state="established",
        analysis_target_ref=_core_ref(binding.analysis_target_ref),
        analysis_input_binding_state="established",
        separate_observation_entry_state=separate_state,
        procedure_ref=_core_ref(binding.procedure_ref),
        procedure_binding_state="established",
        row_independence_state="refuted" if paired else "established",
        safeguard_checks=safeguards,
        affected_target_ref=_core_ref(binding.affected_target_ref),
        affected_target_state="established",
        unresolved_dimensions=(),
        unsupported_constructs=(),
        output_ceiling="evaluation_candidate",
    )


def _failed_discharge(
    certificate: DependenceCertificate,
    construct: str,
) -> DischargedDependenceAnalysis:
    authority = certificate.case_binding.authority
    case = _state_case(
        state="unsupported",
        authority=authority,
        unsupported=(construct,),
    )
    return DischargedDependenceAnalysis(
        state="unsupported",
        certificate=certificate,
        trusted_multiplicity_facts=(),
        verified_certificate=None,
        case=case,
        basis=f"Controller discharge abstained: {construct}.",
    )


def _proposal_matches_context(
    certificate: DependenceCertificate,
    context: FrozenInspectionContext,
) -> bool:
    source_matches = [
        document
        for document in context.documents
        if document.path == certificate.source_path
        and document.content_digest == certificate.source_digest
    ]
    authority = _authority(context)
    selected_path = _selected_artifact_path(context)
    pinned = _pinned_scipy_version(context.material_inputs)
    return (
        len(source_matches) == 1
        and _parser_is_supported(
            source_matches[0], certificate.parser_id, certificate.parser_version
        )
        and _dependency_closure_digest(context.material_inputs)
        == certificate.dependency_closure_digest
        and authority.authority == certificate.case_binding.authority
        and not authority.ambiguous
        and pinned is not None
        and certificate.procedure_call.package_version.package_name == "scipy"
        and certificate.procedure_call.package_version.version == pinned[0] == _SUPPORTED_VERSION
        and certificate.procedure_call.package_version.evidence_ids
        == (_package_pin_evidence_id(pinned[1], pinned[0]),)
        and selected_path is not None
        and {sink.path for sink in certificate.sinks} == {selected_path}
    )


def _dependency_closure_digest(
    materials: tuple[FrozenMaterialInput, ...],
) -> str:
    return semantic_digest(
        [
            item.digest_projection()
            for item in sorted(
                materials,
                key=lambda value: (
                    value.path,
                    value.content_digest,
                    value.file_ref.record_id,
                    value.asset_identity_ref.record_id,
                ),
            )
        ]
    )


def _package_pin_evidence_id(material: FrozenMaterialInput, version: str) -> str:
    return f"dependency-pin:{semantic_digest({'path': material.path, 'digest': material.content_digest, 'version': version})}"


def _analysis_without_certificate(
    state: AnalysisState,
    context: FrozenInspectionContext,
    *,
    candidate_columns: tuple[str, ...] = (),
    unresolved: tuple[str, ...] = (),
    unsupported: tuple[str, ...] = (),
    effects: tuple[Effect, ...] = (),
    basis: str,
    authority: HumanMethodAuthorization | None = None,
) -> PythonDependenceAnalysis:
    del context
    case = (
        None
        if state == "not_applicable"
        else _state_case(
            state=state,
            authority=authority,
            unresolved=unresolved,
            unsupported=unsupported,
        )
    )
    return PythonDependenceAnalysis(
        state=state,
        certificate=None,
        case=case,
        candidate_key_columns=candidate_columns,
        unresolved_dimensions=tuple(dict.fromkeys(unresolved)),
        unsupported_constructs=tuple(dict.fromkeys(unsupported)),
        effects=effects,
        basis=basis,
    )


def _state_case(
    *,
    state: AnalysisState,
    authority: HumanMethodAuthorization | None,
    unresolved: tuple[str, ...] = (),
    unsupported: tuple[str, ...] = (),
) -> DependenceCase:
    analysis_ref = _core_ref(authority.analysis_target_ref) if authority else None
    procedure_ref = _core_ref(authority.procedure_ref) if authority else None
    unit_id = (
        authority.independent_unit_definition_id if authority else "unit-definition:unresolved"
    )
    evidence_state: EvidenceState = "unsupported" if state == "unsupported" else "unknown"
    return DependenceCase(
        case_id=f"dependence-case:{semantic_digest({'state': state, 'unresolved': unresolved, 'unsupported': unsupported})}",
        analyzed_observation_ids=("observation:unresolved",),
        independent_unit_definition_id=unit_id,
        unit_definition_state=evidence_state,
        memberships=(),
        membership_state=evidence_state,
        analysis_target_ref=analysis_ref,
        analysis_input_binding_state=evidence_state,
        separate_observation_entry_state=evidence_state,
        procedure_ref=procedure_ref,
        procedure_binding_state=evidence_state,
        row_independence_state=evidence_state,
        safeguard_checks=(),
        affected_target_ref=None,
        affected_target_state=evidence_state,
        unresolved_dimensions=tuple(dict.fromkeys(unresolved)),
        unsupported_constructs=tuple(dict.fromkeys(unsupported)),
        output_ceiling="evaluation_candidate",
    )


def _authority(context: FrozenInspectionContext) -> _AuthorityResolution:
    authorities: list[HumanMethodAuthorization] = []
    malformed = False
    for record in context.base_records:
        if record.ref.record_type != "human_method_authorization":
            continue
        value = _record_value(record)
        authority = _parse_authority(value)
        if authority is not None:
            authorities.append(authority)
        else:
            malformed = True
    return _AuthorityResolution(
        authority=authorities[0] if len(authorities) == 1 and not malformed else None,
        ambiguous=len(authorities) > 1 or malformed,
    )


def _parse_authority(value: object) -> HumanMethodAuthorization | None:
    if not isinstance(value, dict) or value.get("record_type") != "human_method_authorization":
        return None
    analysis_ref = _recognition_ref(value.get("analysis_target_ref"), "analysis")
    procedure_ref = _recognition_ref(value.get("procedure_ref"), "procedure")
    columns = value.get("authorized_key_columns")
    if not (
        analysis_ref
        and procedure_ref
        and isinstance(value.get("record_id"), str)
        and bool(value["record_id"])
        and value["record_id"] == value["record_id"].strip()
        and isinstance(value.get("actor_id"), str)
        and bool(value["actor_id"])
        and value["actor_id"] == value["actor_id"].strip()
        and value.get("authority_state") == "authorized"
        and isinstance(value.get("independent_unit_definition_id"), str)
        and bool(value["independent_unit_definition_id"])
        and value["independent_unit_definition_id"]
        == value["independent_unit_definition_id"].strip()
        and isinstance(columns, list)
        and columns
        and all(isinstance(item, str) and item for item in columns)
        and len(columns) == len(set(columns))
        and isinstance(value.get("input_path"), str)
        and _relative_analysis_path(value["input_path"])
        and isinstance(value.get("input_content_digest"), str)
        and _sha256_literal(value["input_content_digest"])
    ):
        return None
    return HumanMethodAuthorization(
        record_type="human_method_authorization",
        record_id=value["record_id"],
        actor_id=value["actor_id"],
        authority_state="authorized",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        independent_unit_definition_id=value["independent_unit_definition_id"],
        authorized_key_columns=tuple(columns),
        input_path=value["input_path"],
        input_content_digest=value["input_content_digest"],
    )


def _pinned_scipy_version(
    materials: tuple[FrozenMaterialInput, ...],
) -> tuple[str, FrozenMaterialInput] | None:
    matches: list[tuple[str, FrozenMaterialInput]] = []
    for material in materials:
        name = Path(material.path).name.lower()
        if not (name.startswith("requirements") and name.endswith(".txt")):
            continue
        try:
            text = material.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
        versions: list[str] = []
        for line in text.splitlines():
            match = _PIN_RE.fullmatch(line)
            if match is not None:
                versions.append(match.group(1))
            elif _mentions_scipy_requirement(line):
                # A second, ranged, editable, extras-qualified, or otherwise
                # unmodelled SciPy declaration defeats the exact-version proof.
                return None
        if len(versions) > 1:
            return None
        if versions:
            matches.append((versions[0], material))
    return matches[0] if len(matches) == 1 else None


def _mentions_scipy_requirement(line: str) -> bool:
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#"):
        return False
    return re.match(r"(?i)^scipy(?:\b|\[|[<>=!~])", stripped) is not None


def _candidate_key_columns(context: FrozenInspectionContext, read: _Read) -> tuple[str, ...]:
    matches = [item for item in context.material_inputs if item.path == read.path]
    if len(matches) != 1:
        return ()
    try:
        text = matches[0].content.decode("utf-8", errors="strict")
        if text.startswith("\ufeff"):
            return ()
        if read.line_model == "splitlines":
            if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
                return ()
            reader = csv.DictReader(text.splitlines())
        else:
            reader = csv.DictReader(io.StringIO(text, newline=""))
        header = reader.fieldnames
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return ()
    if not header or any(not item for item in header) or len(header) != len(set(header)):
        return ()
    return tuple(header)


def _material(
    materials: tuple[FrozenMaterialInput, ...],
    path: str,
    digest: str,
) -> FrozenMaterialInput | None:
    matches = [item for item in materials if item.path == path and item.content_digest == digest]
    return matches[0] if len(matches) == 1 else None


def _affected_target_ref(
    context: FrozenInspectionContext,
    selected_report_path: str,
) -> RecordRef | None:
    exact: list[RecordRef] = []
    for record in context.base_records:
        if record.ref.record_type not in {"result", "claim"}:
            continue
        ref = RecordRef(record.ref.record_type, record.ref.record_id)
        value = _record_value(record)
        if isinstance(value, dict) and value.get("path") == selected_report_path:
            exact.append(ref)
    return exact[0] if len(exact) == 1 else None


def _selected_artifact_path(context: FrozenInspectionContext) -> str | None:
    for record in context.base_records:
        if record.ref == context.selected_artifact_ref:
            value = _record_value(record)
            if (
                isinstance(value, dict)
                and isinstance(value.get("path"), str)
                and _relative_analysis_path(value["path"])
            ):
                return cast(str, value["path"])
    return None


def _authority_refs_exist_once(
    context: FrozenInspectionContext,
    authority: HumanMethodAuthorization,
) -> bool:
    return all(
        sum(_same_ref(record.ref, ref) for record in context.base_records) == 1
        for ref in (authority.analysis_target_ref, authority.procedure_ref)
    )


def _procedure_record_allows(
    context: FrozenInspectionContext,
    procedure_ref: RecordRef,
    resolved_callable: str,
) -> bool:
    matches = [record for record in context.base_records if _same_ref(record.ref, procedure_ref)]
    if len(matches) != 1:
        return False
    value = _record_value(matches[0])
    if not isinstance(value, dict):
        return False
    declared = value.get("resolved_callable")
    return "resolved_callable" not in value or declared == resolved_callable


def _case_module_names(context: FrozenInspectionContext) -> set[str]:
    names: set[str] = set()
    for document in context.documents:
        parts = Path(document.path).parts
        names.update(parts[:-1])
        if document.path.endswith(".py") and Path(document.path).stem != "__init__":
            names.add(Path(document.path).stem)
    return names


def _dependence_module_bans(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "pandas" for alias in node.names):
                return True
            if any(
                alias.name.split(".")[0] == "scipy" and alias.name != "scipy.stats"
                for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] == "pandas":
                return True
            if (node.module or "").split(".")[0] == "scipy" and not (
                (node.module == "scipy" and all(alias.name == "stats" for alias in node.names))
                or (
                    node.module == "scipy.stats"
                    and all(
                        alias.name in {"ttest_ind", "mannwhitneyu", "ttest_rel"}
                        for alias in node.names
                    )
                )
            ):
                return True
    guarded_body = [
        statement
        for statement in tree.body
        if not (
            isinstance(statement, ast.Import)
            and all(alias.name.split(".")[0] == "scipy" for alias in statement.names)
        )
        and not (
            isinstance(statement, ast.ImportFrom)
            and (statement.module or "").split(".")[0] == "scipy"
        )
    ]
    return _module_bans(ast.Module(body=guarded_body, type_ignores=[]))


def _imports_pandas(tree: ast.Module) -> bool:
    return any(
        (
            isinstance(node, ast.Import)
            and any(alias.name.split(".")[0] == "pandas" for alias in node.names)
        )
        or (isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "pandas")
        for node in ast.walk(tree)
    )


def _live_guard_tree(tree: ast.Module) -> ast.Module:
    body: list[ast.stmt] = []
    for statement in tree.body:
        if isinstance(statement, ast.If) and _is_false_guard(statement):
            body.append(ast.Pass())
        elif isinstance(statement, ast.If) and _is_main_guard(statement):
            body.extend(statement.body)
        else:
            body.append(statement)
    return ast.Module(body=body, type_ignores=[])


def _is_false_guard(statement: ast.If) -> bool:
    if not isinstance(statement.test, ast.Constant):
        return False
    value = statement.test.value
    return value is False or value is None or (type(value) is int and value == 0)


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


def _unsupported_kind(statement: ast.stmt) -> str:
    if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
        return "helper-or-wrapper-function"
    if isinstance(statement, ast.For | ast.AsyncFor | ast.While):
        return "loop-carried-state"
    if isinstance(statement, ast.Try | ast.TryStar):
        return "try-except-around-analysis"
    if isinstance(statement, ast.If):
        return "conditional-control-flow"
    return "unsupported-statement"


def _statement_subtree(statement: ast.stmt) -> list[ast.stmt]:
    return [node for node in ast.walk(statement) if isinstance(node, ast.stmt)]


def _string_columns(expression: ast.expr) -> tuple[str, ...] | None:
    if (
        isinstance(expression, ast.Constant)
        and isinstance(expression.value, str)
        and expression.value
    ):
        return (expression.value,)
    if isinstance(expression, ast.Tuple | ast.List) and expression.elts:
        values = tuple(
            item.value
            for item in expression.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value
        )
        return (
            values
            if len(values) == len(expression.elts) and len(values) == len(set(values))
            else None
        )
    return None


def _tuple_identity_assignment(statement: ast.Assign) -> tuple[str, str] | None:
    if len(statement.targets) != 1:
        return None
    target = statement.targets[0]
    value = statement.value
    if not (
        isinstance(target, ast.Tuple)
        and isinstance(value, ast.Tuple)
        and len(target.elts) == len(value.elts) == 1
        and isinstance(target.elts[0], ast.Name)
        and isinstance(value.elts[0], ast.Name)
    ):
        return None
    return target.elts[0].id, value.elts[0].id


def _only_utf8_encoding(keywords: list[ast.keyword]) -> bool:
    if any(item.arg is None for item in keywords):
        return False
    values = {item.arg: item.value for item in keywords}
    return set(values) == {"encoding"} and _utf8_literal(values["encoding"])


def _utf8_literal(expression: ast.expr) -> bool:
    return isinstance(expression, ast.Constant) and expression.value in {"utf-8", "UTF-8"}


def _empty_string(expression: ast.expr) -> bool:
    return isinstance(expression, ast.Constant) and expression.value == ""


def _recognition_ref(value: object, expected_type: str) -> RecordRef | None:
    if not isinstance(value, dict):
        return None
    record_type = value.get("record_type")
    record_id = value.get("record_id")
    if record_type != expected_type or not isinstance(record_id, str) or not record_id:
        return None
    return RecordRef(record_type, record_id)


def _core_ref(value: RecordRef) -> CoreRecordRef:
    return CoreRecordRef(value.record_type, value.record_id)


def _record_value(record: FrozenBaseRecord) -> object:
    try:
        return json.loads(record.canonical_payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _parser_is_supported(
    document: InspectionDocument,
    parser_id: str,
    parser_version: str,
) -> bool:
    try:
        return _python_parser_supported(document, parser_id, parser_version)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
        return False


def _same_ref(value: object, expected: RecordRef) -> bool:
    return (
        getattr(value, "record_type", None) == expected.record_type
        and getattr(value, "record_id", None) == expected.record_id
    )


def _relative_analysis_path(value: str) -> bool:
    return (
        bool(value)
        and value == value.strip()
        and not value.startswith("/")
        and "\\" not in value
        and "\x00" not in value
        and not any(unicodedata.category(character).startswith("C") for character in value)
        and ".." not in value.split("/")
    )


def _sha256_literal(value: str) -> bool:
    payload = value.removeprefix("sha256:")
    return (
        value.startswith("sha256:")
        and len(payload) == 64
        and all(character in "0123456789abcdef" for character in payload)
    )


def _transform_nodes(trace: _TraceEngine) -> tuple[ast.AST, ...]:
    return tuple(trace.transform_nodes)


def _point(path: str, node: ast.AST) -> EvidencePoint:
    return EvidencePoint(
        path=path,
        start_line=getattr(node, "lineno", 1),
        end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        start_column=getattr(node, "col_offset", 0) + 1,
        end_column=max(
            getattr(node, "col_offset", 0) + 1,
            getattr(node, "end_col_offset", getattr(node, "col_offset", 0)) + 1,
        ),
    )


def _module_point(document: InspectionDocument) -> EvidencePoint:
    text = document.content.decode("utf-8", errors="strict")
    lines = text.splitlines()
    if not lines:
        return EvidencePoint(document.path, 1, 1, 1, 1)
    return EvidencePoint(document.path, 1, len(lines), 1, max(1, len(lines[-1]) + 1))


def _evidence_id(path: str, node: ast.AST, kind: str) -> str:
    return f"evidence:{semantic_digest({'path': path, 'line': getattr(node, 'lineno', 1), 'column': getattr(node, 'col_offset', 0), 'kind': kind})}"


def _token(path: str, node: ast.AST, kind: str) -> str:
    return f"{kind}:{semantic_digest({'path': path, 'line': getattr(node, 'lineno', 1), 'column': getattr(node, 'col_offset', 0), 'kind': kind})}"


def _opaque_effect(node: ast.AST, reason: str) -> Effect:
    reads = frozenset(
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    )
    return Effect(reads, frozenset({"*"}), frozenset(), True, True, reason)
