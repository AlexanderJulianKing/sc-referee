from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import tree_sitter_r
from tree_sitter import Language, Node, Parser

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks.adapter_common import adapter_implementation_digest
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
    InspectionReceipt,
    NormalizedMethodObservation,
    RoleBinding,
    ScopeJoinEdge,
)
from sc_referee.scientific_checks.scope_joins import (
    selected_container_path,
    selected_review_path,
    selected_static_writer_path,
)

STATIC_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST = adapter_implementation_digest(Path(__file__))

_PYTHON_MEDIA_TYPE = "text/x-python"
_R_MEDIA_TYPE = "text/x-r"
_PYTHON_PARSER_ID = "parser:python-ast-tokenize"
_PYTHON_PARSER_VERSION = "0.15.1"
_R_PARSER_ID = "parser:r-tree-sitter-inventory"
_R_PARSER_VERSION = "0.1.0"
_MAX_LOCAL_SUMMARY_PASSES = 12

_COPY_HARD = "integer_hard_copy_state_as_numeric_dosage"
_COPY_EXPECTED = "continuous_posterior_expected_copy_dosage"
_COPY_CONTINUOUS = "direct_continuous_calibrated_copy_dosage"
_LD_WHITENED = "ld_covariance_cholesky_whitening_before_robust_fit"

_MODEL_CLASSIFIER = "model:classifier"
_MODEL_CONTINUOUS = "model:continuous"
_PROBABILITIES = "value:class-probabilities"
_CLASS_VECTOR = "value:ordered-copy-state-vector"

_CLASSIFIER_CONSTRUCTORS = frozenset(
    {
        "sklearn.linear_model.LogisticRegression",
        "sklearn.ensemble.RandomForestClassifier",
        "sklearn.ensemble.GradientBoostingClassifier",
    }
)
_CONTINUOUS_CONSTRUCTORS = frozenset(
    {
        "sklearn.linear_model.ElasticNet",
        "sklearn.linear_model.LinearRegression",
        "sklearn.linear_model.Ridge",
        "sklearn.linear_model.RidgeCV",
    }
)
_PIPELINE_CONSTRUCTORS = frozenset(
    {
        "sklearn.pipeline.make_pipeline",
        "sklearn.pipeline.Pipeline",
    }
)
_PYTHON_CHOL_CALLS = frozenset({"numpy.linalg.cholesky", "scipy.linalg.cholesky"})
_PYTHON_SOLVE_CALLS = frozenset({"numpy.linalg.solve", "scipy.linalg.solve_triangular"})
_PYTHON_ROBUST_CALLS = frozenset(
    {
        "statsmodels.api.RLM",
        "statsmodels.robust.robust_linear_model.RLM",
    }
)
_PYTHON_REDESCENDING_CALLS = frozenset(
    {
        "statsmodels.api.robust.norms.TukeyBiweight",
        "statsmodels.robust.norms.TukeyBiweight",
    }
)

_COPY_OPERANDS = {
    _COPY_HARD: CanonicalOperand.scalar(_COPY_HARD),
    _COPY_EXPECTED: CanonicalOperand.scalar(_COPY_EXPECTED),
    _COPY_CONTINUOUS: CanonicalOperand.scalar(_COPY_CONTINUOUS),
}
_LD_OPERANDS = {_LD_WHITENED: CanonicalOperand.scalar(_LD_WHITENED)}

SourceLanguage = Literal["python", "r"]
Recognizer = Literal["classifier_copy_dosage", "ld_whitening"]


@dataclass(frozen=True)
class _SourceShape:
    operand: CanonicalOperand
    start_line: int
    end_line: int
    start_column: int
    end_column: int


@dataclass(frozen=True)
class _ScanOutcome:
    shapes: tuple[_SourceShape, ...]
    triggered: bool
    boundary: str | None = None


@dataclass(frozen=True)
class StaticSourceMethodAdapter:
    """Normalize one closed Python or R source shape without executing target code."""

    check_manifest: CheckManifest
    adapter_manifest: AdapterManifest
    language: SourceLanguage
    recognizer: Recognizer
    role_bindings: tuple[RoleBinding, ...]

    @property
    def adapter_id(self) -> str:
        return self.adapter_manifest.adapter_id

    @property
    def adapter_version(self) -> str:
        return self.adapter_manifest.adapter_version

    @property
    def implementation_digest(self) -> str:
        return STATIC_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST

    @property
    def recognition_grammar_digest(self) -> str:
        return static_source_recognition_grammar_digest(
            language=self.language,
            recognizer=self.recognizer,
            role_bindings=self.role_bindings,
        )

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        media_type = _PYTHON_MEDIA_TYPE if self.language == "python" else _R_MEDIA_TYPE
        candidates: list[tuple[InspectionDocument, _SourceShape]] = []
        triggered = False
        boundaries: list[str] = []
        for document in context.documents:
            if document.media_type != media_type:
                continue
            parser_boundary = _parser_boundary(document, self.language)
            if parser_boundary is not None:
                boundaries.append(parser_boundary)
                continue
            outcome = _scan_document(document, self.language, self.recognizer)
            triggered = triggered or outcome.triggered
            if outcome.boundary is not None:
                boundaries.append(outcome.boundary)
            candidates.extend((document, shape) for shape in outcome.shapes)

        if boundaries:
            return self._abstain(
                "unsupported",
                "A finite static-source boundary remained unresolved: " + sorted(boundaries)[0],
            )
        if len(candidates) > 1:
            return self._abstain(
                "ambiguous",
                "More than one supported source method target or operand is present.",
            )
        if not candidates:
            return self._abstain(
                "unsupported" if triggered else "not_applicable",
                (
                    "Method-like source syntax is present, but its exact operand is unsupported."
                    if triggered
                    else "No exact source trigger for this method check is present."
                ),
            )

        document, shape = candidates[0]
        span = _shape_span(document, shape)
        scope_path = _source_scope_path(context, document)
        scoped = bool(scope_path)
        receipts = (
            InspectionReceipt(
                receipt_id="exact-static-method-role-binding",
                kind="counterevidence",
                state="passed",
                evidence_digest=semantic_digest(span.to_dict()),
                description=(
                    "One enumerated static call, argument, formula, and assignment shape binds "
                    "the existing normalized method operand."
                ),
            ),
            InspectionReceipt(
                receipt_id="alternative-static-method-targets-absent",
                kind="sibling",
                state="passed",
                evidence_digest=semantic_digest(
                    {"path": document.path, "content_digest": document.content_digest}
                ),
                description="No competing supported source operand was present.",
            ),
            InspectionReceipt(
                receipt_id="complete-static-control-flow",
                kind="counterevidence",
                state="passed",
                evidence_digest=document.parser_result_digest or document.content_digest,
                description=(
                    "The admitted method-defining source shape is outside unsupported branching, "
                    "shadowing, computed dispatch, and parser-disagreement boundaries."
                ),
            ),
            InspectionReceipt(
                receipt_id="source-to-analysis-scope-join",
                kind="counterevidence",
                state="passed" if scoped else "unsupported",
                evidence_digest=semantic_digest(
                    {
                        "file_ref": document.file_ref.to_dict(),
                        "scope_join_path": [edge.to_dict() for edge in scope_path],
                        "selected_surface_ref": context.selected_surface_ref.to_dict(),
                    }
                ),
                description=(
                    "The source is connected to the selected analysis by one accepted static "
                    "scope proof; this does not establish execution or primary-analysis status."
                    if scoped
                    else "No accepted static path connects this source to the selected analysis."
                ),
            ),
        )
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
            applicability="applicable" if scoped else "unsupported",
            completeness="complete" if scoped else "incomplete",
            evidence_plane="static_source",
            method_target_ref=document.file_ref,
            role_bindings=self.role_bindings,
            observed_operand=shape.operand,
            evidence_spans=(span,),
            scope_join_path=scope_path,
            receipts=receipts,
            non_inferences=self.check_manifest.prohibited_inferences,
            output_ceiling="question_only",
            abstention_reason=(
                None
                if scoped
                else (
                    "The exact source operand is preserved only as an unscoped suppressor; no "
                    "accepted source-to-analysis join is available."
                )
            ),
        )

    def _abstain(self, state: str, reason: str) -> NormalizedMethodObservation:
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
            applicability=state,  # type: ignore[arg-type]
            completeness="not_applicable" if state == "not_applicable" else "incomplete",
            evidence_plane="static_source",
            method_target_ref=None,
            role_bindings=(),
            observed_operand=None,
            evidence_spans=(),
            scope_join_path=(),
            receipts=(
                InspectionReceipt(
                    receipt_id="closed-abstention",
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


def static_source_recognition_grammar_digest(
    *,
    language: SourceLanguage,
    recognizer: Recognizer,
    role_bindings: tuple[RoleBinding, ...],
) -> str:
    grammar: dict[str, Any] = {
        "profile": "bounded-cross-language-static-method-observation-v1",
        "language": language,
        "recognizer": recognizer,
        "role_bindings": [item.to_dict() for item in role_bindings],
        "scope_profiles": [
            "selected-analysis-source-for-review",
            "verified-active-cell-containment",
            "unique-reachable-static-writer-source",
        ],
        "shadowing_supported": False,
        "computed_dispatch_supported": False,
        "method_defining_branches_supported": False,
        "project_execution": False,
    }
    if recognizer == "classifier_copy_dosage":
        grammar["operands"] = {key: value.to_dict() for key, value in _COPY_OPERANDS.items()}
        grammar["python_calls"] = {
            "classifier_constructors": sorted(_CLASSIFIER_CONSTRUCTORS),
            "continuous_constructors": sorted(_CONTINUOUS_CONSTRUCTORS),
            "pipeline_constructors": sorted(_PIPELINE_CONSTRUCTORS),
            "prediction_methods": ["predict", "predict_proba"],
        }
        grammar["r_calls"] = {
            "classifier_constructors": ["nnet::multinom"],
            "continuous_constructors": ["glmnet::cv.glmnet", "stats::lm"],
            "prediction_calls": ["predict", "stats::predict"],
            "prediction_types": ["class", "probs", "response"],
        }
    else:
        grammar["operands"] = {key: value.to_dict() for key, value in _LD_OPERANDS.items()}
        grammar["python_calls"] = {
            "cholesky": sorted(_PYTHON_CHOL_CALLS),
            "triangular_solve": sorted(_PYTHON_SOLVE_CALLS),
            "robust_fit": sorted(_PYTHON_ROBUST_CALLS),
            "redescending_norm": sorted(_PYTHON_REDESCENDING_CALLS),
        }
        grammar["r_calls"] = {
            "cholesky": ["base::chol", "chol"],
            "triangular_solve": ["base::forwardsolve", "forwardsolve"],
            "robust_fit": ["MASS::rlm", "rlm"],
            "redescending_norm": ["MASS::psi.bisquare", "psi.bisquare"],
        }
    return semantic_digest(grammar)


def make_static_source_adapter(
    *,
    check_manifest: CheckManifest,
    language: SourceLanguage,
    recognizer: Recognizer,
    role_bindings: tuple[RoleBinding, ...],
) -> tuple[AdapterManifest, StaticSourceMethodAdapter]:
    parser_id, parser_version = (
        (_PYTHON_PARSER_ID, _PYTHON_PARSER_VERSION)
        if language == "python"
        else (_R_PARSER_ID, _R_PARSER_VERSION)
    )
    grammar_digest = static_source_recognition_grammar_digest(
        language=language,
        recognizer=recognizer,
        role_bindings=role_bindings,
    )
    check_name = check_manifest.check_id.removeprefix("check:")
    manifest = AdapterManifest(
        adapter_id=f"adapter:{check_name}:{language}-static-source-v1",
        adapter_version="1.0.0",
        implementation_digest=STATIC_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=grammar_digest,
        parser_id=parser_id,
        parser_version=parser_version,
        source_language=language,
        evidence_plane="static_source",
        semantic_roles=check_manifest.semantic_roles,
        applicability_profile=f"bounded-{recognizer.replace('_', '-')}-{language}-ast-v1",
        counterevidence_profiles=(
            "exact-static-method-role-binding",
            "alternative-static-method-targets-absent",
            "complete-static-control-flow",
            "source-to-analysis-scope-join",
        ),
        known_gaps=(
            "dynamic dispatch, shadowing, generated formulas, and general interprocedural flow",
            "static source does not establish runtime values, package behavior, execution, dead-code absence, or primary-analysis status",
            "only the enumerated call, argument, formula, and assignment grammar is recognized",
        ),
    )
    return manifest, StaticSourceMethodAdapter(
        check_manifest=check_manifest,
        adapter_manifest=manifest,
        language=language,
        recognizer=recognizer,
        role_bindings=role_bindings,
    )


def _scan_document(
    document: InspectionDocument,
    language: SourceLanguage,
    recognizer: Recognizer,
) -> _ScanOutcome:
    try:
        text = document.content.decode("utf-8")
    except UnicodeDecodeError:
        return _ScanOutcome((), False, "source is not strict UTF-8")
    if language == "python":
        try:
            tree = ast.parse(text, filename=document.path, type_comments=True)
        except SyntaxError:
            return _ScanOutcome((), False, "Python AST parsing was incomplete")
        return (
            _python_copy_dosage_scan(tree)
            if recognizer == "classifier_copy_dosage"
            else _python_ld_whitening_scan(tree)
        )
    payload = text.encode("utf-8")
    r_tree = Parser(Language(tree_sitter_r.language())).parse(payload)
    if r_tree.root_node.has_error:
        return _ScanOutcome((), False, "Tree-sitter-R parsing was incomplete")
    return (
        _r_copy_dosage_scan(r_tree.root_node, payload)
        if recognizer == "classifier_copy_dosage"
        else _r_ld_whitening_scan(r_tree.root_node, payload)
    )


def _parser_boundary(document: InspectionDocument, language: SourceLanguage) -> str | None:
    if document.parser_result_payload is None:
        return "controller parser receipt is unavailable"
    try:
        result = json.loads(document.parser_result_payload)
    except json.JSONDecodeError:
        return "controller parser receipt is invalid"
    parser_id, parser_version = (
        (_PYTHON_PARSER_ID, _PYTHON_PARSER_VERSION)
        if language == "python"
        else (_R_PARSER_ID, _R_PARSER_VERSION)
    )
    if result.get("parser_id") != parser_id or result.get("parser_version") != parser_version:
        return "controller parser identity does not match the adapter"
    if result.get("state") != "parsed" or result.get("syntax_issues"):
        return "controller parser did not completely accept the source"
    if language == "r" and result.get("parser_disagreement") is not None:
        return "Tree-sitter-R and base-R call inventories disagree"
    return None


def _source_scope_path(
    context: FrozenInspectionContext, document: InspectionDocument
) -> tuple[ScopeJoinEdge, ...]:
    container = selected_container_path(
        context.scope_join_graph,
        document=document,
        selected_artifact_ref=context.selected_artifact_ref,
        selected_surface_ref=context.selected_surface_ref,
    )
    if container:
        return container
    writer = selected_static_writer_path(
        context.scope_join_graph,
        document=document,
        selected_artifact_ref=context.selected_artifact_ref,
        selected_surface_ref=context.selected_surface_ref,
    )
    if writer:
        return writer
    review = selected_review_path(
        context.scope_join_graph,
        kind="analysis_source",
        source_ref=document.file_ref,
        selected_surface_ref=context.selected_surface_ref,
    )
    return tuple(item.edge for item in review)


def _shape_span(document: InspectionDocument, shape: _SourceShape) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=shape.start_line + document.line_offset,
        end_line=shape.end_line + document.line_offset,
        start_column=shape.start_column,
        end_column=shape.end_column,
        parser_result_ref=document.parser_result_ref,
    )


def _python_copy_dosage_scan(tree: ast.Module) -> _ScanOutcome:
    resolver, binding_boundary = _python_import_resolver(tree)
    triggered = any(
        isinstance(node, ast.Call)
        and _python_terminal_name(node.func) in {"predict", "predict_proba"}
        for node in ast.walk(tree)
    ) or any(
        isinstance(node, (ast.Name, ast.Constant))
        and "dosage" in str(getattr(node, "id", getattr(node, "value", ""))).casefold()
        for node in ast.walk(tree)
    )
    if binding_boundary:
        return _ScanOutcome((), triggered, binding_boundary)

    summaries: dict[str, tuple[str | None, ...]] = {}
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for _ in range(_MAX_LOCAL_SUMMARY_PASSES):
        changed = False
        for name, function in functions.items():
            value = _python_function_summary(function, resolver, summaries)
            if value is not None and summaries.get(name) != value:
                summaries[name] = value
                changed = True
        if not changed:
            break

    shapes: list[_SourceShape] = []
    boundary: str | None = None
    for scope in (tree, *functions.values()):
        env: dict[str, str] = {}
        for node in _python_ordered_assignments(scope):
            if _python_in_method_branch(node, scope):
                if _python_target_mentions_dosage(node):
                    boundary = "a dosage-defining assignment is branch-dependent"
                continue
            categories = _python_assignment_categories(node, env, resolver, summaries)
            for target, category in categories:
                root = _python_target_root(target)
                if root is not None and category is not None:
                    env[root] = category
                if category in _COPY_OPERANDS and _python_target_mentions_dosage_target(target):
                    shapes.append(_python_shape(_COPY_OPERANDS[category], node))
    return _collapse_shapes(shapes, triggered, boundary)


def _python_ld_whitening_scan(tree: ast.Module) -> _ScanOutcome:
    resolver, binding_boundary = _python_import_resolver(tree)
    robust_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _python_call_path(node, resolver) in _PYTHON_ROBUST_CALLS
    ]
    triggered = bool(robust_calls)
    if binding_boundary:
        return _ScanOutcome((), triggered, binding_boundary)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    shapes: list[_SourceShape] = []
    for call in robust_calls:
        if _python_has_branch_ancestor(call, parents):
            return _ScanOutcome((), True, "the robust-fit call is branch-dependent")
        scope = _python_nearest_scope(call, parents)
        assignments = _python_unique_expression_bindings(scope)
        if assignments is None:
            return _ScanOutcome((), True, "source assignments are ambiguous")
        if not _python_redescending_argument(call, resolver):
            continue
        y_arg = _python_bound_argument(call, 0, ("endog", "y"))
        x_arg = _python_bound_argument(call, 1, ("exog", "x"))
        if y_arg is None or x_arg is None:
            continue
        y_solve = _python_resolved_solve(y_arg, assignments, resolver)
        x_solve = _python_resolved_solve(x_arg, assignments, resolver)
        if y_solve is None or x_solve is None or y_solve[0] != x_solve[0]:
            continue
        factor_name = y_solve[0]
        factor = assignments.get(factor_name)
        if (
            not isinstance(factor, ast.Call)
            or _python_call_path(factor, resolver) not in _PYTHON_CHOL_CALLS
        ):
            continue
        shapes.append(
            _python_shape(_LD_OPERANDS[_LD_WHITENED], call, factor, y_solve[1], x_solve[1])
        )
    return _collapse_shapes(shapes, triggered, None)


def _python_import_resolver(tree: ast.Module) -> tuple[dict[str, str], str | None]:
    aliases: dict[str, str] = {}
    import_names: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for item in statement.names:
                local = item.asname or item.name.split(".")[0]
                aliases[local] = item.name if item.asname else item.name.split(".")[0]
                import_names.add(local)
        elif isinstance(statement, ast.ImportFrom):
            if any(item.name == "*" for item in statement.names):
                return {}, "a wildcard import prevents closed call binding"
            if statement.module is None or statement.level:
                continue
            for item in statement.names:
                local = item.asname or item.name
                aliases[local] = f"{statement.module}.{item.name}"
                import_names.add(local)
    stored = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
    }
    argument_names = {
        argument.arg
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
        for argument in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
    }
    shadowed = sorted(import_names & (stored | argument_names))
    if shadowed:
        return aliases, f"an admitted import alias is shadowed: {shadowed[0]}"
    return aliases, None


def _python_call_path(call: ast.Call, resolver: dict[str, str]) -> str:
    return _python_expression_path(call.func, resolver)


def _python_expression_path(node: ast.AST, resolver: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return resolver.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _python_expression_path(node.value, resolver)
        return f"{base}.{node.attr}" if base else node.attr
    return "<dynamic>"


def _python_terminal_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return "<dynamic>"


def _python_function_summary(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    resolver: dict[str, str],
    summaries: dict[str, tuple[str | None, ...]],
) -> tuple[str | None, ...] | None:
    env: dict[str, str] = {}
    for node in _python_ordered_assignments(function):
        if _python_in_method_branch(node, function):
            continue
        for target, category in _python_assignment_categories(node, env, resolver, summaries):
            root = _python_target_root(target)
            if root is not None and category is not None:
                env[root] = category
    returns = [
        node
        for node in _python_scope_nodes(function)
        if isinstance(node, ast.Return) and not _python_in_method_branch(node, function)
    ]
    projected: list[tuple[str | None, ...]] = []
    for returned in returns:
        if returned.value is None:
            projected.append((None,))
        elif isinstance(returned.value, (ast.Tuple, ast.List)):
            projected.append(
                tuple(
                    _python_expression_category(item, env, resolver, summaries)
                    for item in returned.value.elts
                )
            )
        else:
            projected.append(
                (_python_expression_category(returned.value, env, resolver, summaries),)
            )
    return projected[0] if projected and all(item == projected[0] for item in projected) else None


def _python_ordered_assignments(scope: ast.AST) -> list[ast.Assign | ast.AnnAssign]:
    values = [
        node for node in _python_scope_nodes(scope) if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    return sorted(values, key=lambda item: (item.lineno, item.col_offset))


def _python_scope_nodes(scope: ast.AST) -> list[ast.AST]:
    """Walk one lexical scope while excluding nested function, class, and lambda bodies."""

    roots: list[ast.AST]
    if isinstance(scope, ast.Module):
        roots = list(scope.body)
    elif isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        roots = list(scope.body)
    else:
        roots = list(ast.iter_child_nodes(scope))
    values: list[ast.AST] = []
    stack = list(reversed(roots))
    while stack:
        node = stack.pop()
        values.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))
    return values


def _python_assignment_categories(
    node: ast.Assign | ast.AnnAssign,
    env: dict[str, str],
    resolver: dict[str, str],
    summaries: dict[str, tuple[str | None, ...]],
) -> list[tuple[ast.expr, str | None]]:
    targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
    value = node.value
    if value is None:
        return []
    if len(targets) == 1 and isinstance(targets[0], (ast.Tuple, ast.List)):
        target_items = list(targets[0].elts)
        categories = _python_expression_categories(value, env, resolver, summaries)
        if len(categories) != len(target_items):
            return []
        return list(zip(target_items, categories, strict=True))
    category = _python_expression_category(value, env, resolver, summaries)
    return [(target, category) for target in targets]


def _python_expression_categories(
    node: ast.expr,
    env: dict[str, str],
    resolver: dict[str, str],
    summaries: dict[str, tuple[str | None, ...]],
) -> tuple[str | None, ...]:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in summaries:
        return summaries[node.func.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(
            _python_expression_category(item, env, resolver, summaries) for item in node.elts
        )
    return (_python_expression_category(node, env, resolver, summaries),)


def _python_expression_category(
    node: ast.expr,
    env: dict[str, str],
    resolver: dict[str, str],
    summaries: dict[str, tuple[str | None, ...]],
) -> str | None:
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if _python_copy_state_vector(node, env, resolver, summaries):
        return _CLASS_VECTOR
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
        left = _python_expression_category(node.left, env, resolver, summaries)
        right = _python_expression_category(node.right, env, resolver, summaries)
        if {left, right} == {_PROBABILITIES, _CLASS_VECTOR}:
            return _COPY_EXPECTED
    if isinstance(node, ast.Call):
        path = _python_call_path(node, resolver)
        if path in _CLASSIFIER_CONSTRUCTORS:
            return _MODEL_CLASSIFIER
        if path in _CONTINUOUS_CONSTRUCTORS:
            return _MODEL_CONTINUOUS
        if path in _PIPELINE_CONSTRUCTORS:
            categories = [
                _python_expression_category(item, env, resolver, summaries) for item in node.args
            ]
            if _MODEL_CLASSIFIER in categories:
                return _MODEL_CLASSIFIER
            if _MODEL_CONTINUOUS in categories:
                return _MODEL_CONTINUOUS
        if isinstance(node.func, ast.Name) and node.func.id in summaries:
            values = summaries[node.func.id]
            return values[0] if len(values) == 1 else None
        terminal = _python_terminal_name(node.func)
        if terminal == "fit" and isinstance(node.func, ast.Attribute):
            return _python_expression_category(node.func.value, env, resolver, summaries)
        if terminal in {"astype", "clip", "asarray", "array"}:
            candidates = [
                *(node.args[:1]),
                *([node.func.value] if isinstance(node.func, ast.Attribute) else []),
            ]
            for candidate in candidates:
                category = _python_expression_category(candidate, env, resolver, summaries)
                if category is not None:
                    return category
        if terminal in {"predict", "predict_proba"} and isinstance(node.func, ast.Attribute):
            model = _python_expression_category(node.func.value, env, resolver, summaries)
            if terminal == "predict_proba" and (
                model == _MODEL_CLASSIFIER or isinstance(node.func.value, ast.Name)
            ):
                return _PROBABILITIES
            if terminal == "predict" and model == _MODEL_CLASSIFIER:
                return _COPY_HARD
            if terminal == "predict" and model == _MODEL_CONTINUOUS:
                return _COPY_CONTINUOUS
        if terminal == "sum":
            products = [
                item
                for item in ast.walk(node)
                if isinstance(item, ast.BinOp) and isinstance(item.op, ast.Mult)
            ]
            if any(
                {
                    _python_expression_category(item.left, env, resolver, summaries),
                    _python_expression_category(item.right, env, resolver, summaries),
                }
                == {_PROBABILITIES, _CLASS_VECTOR}
                for item in products
            ):
                return _COPY_EXPECTED
    if isinstance(node, ast.Attribute) and node.attr == "classes_":
        return _CLASS_VECTOR
    return None


def _python_copy_state_vector(
    node: ast.expr,
    env: dict[str, str],
    resolver: dict[str, str],
    summaries: dict[str, tuple[str | None, ...]],
) -> bool:
    del env, summaries
    values: list[object] | None = None
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [item.value for item in node.elts if isinstance(item, ast.Constant)]
        if len(values) != len(node.elts):
            values = None
    elif (
        isinstance(node, ast.Call)
        and _python_terminal_name(node.func) in {"array", "asarray"}
        and node.args
    ):
        return _python_copy_state_vector(node.args[0], {}, resolver, {})
    return values is not None and [
        float(item) for item in values if isinstance(item, (int, float))
    ] == [0.0, 1.0, 2.0]


def _python_target_root(node: ast.expr) -> str | None:
    current: ast.AST = node
    while isinstance(current, (ast.Subscript, ast.Attribute)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _python_target_mentions_dosage(node: ast.Assign | ast.AnnAssign) -> bool:
    targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
    return any(_python_target_mentions_dosage_target(target) for target in targets)


def _python_target_mentions_dosage_target(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return "dosage" in node.id.casefold()
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_python_target_mentions_dosage_target(item) for item in node.elts)
    if isinstance(node, ast.Subscript):
        value = node.slice.value if isinstance(node.slice, ast.Constant) else None
        return isinstance(value, str) and "dosage" in value.casefold()
    if isinstance(node, ast.Attribute):
        return "dosage" in node.attr.casefold()
    return False


def _python_in_method_branch(node: ast.AST, scope: ast.AST) -> bool:
    parents = {
        child: parent for parent in ast.walk(scope) for child in ast.iter_child_nodes(parent)
    }
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.If, ast.IfExp, ast.Try, ast.Match)):
            return True
    return False


def _python_has_branch_ancestor(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.If, ast.IfExp, ast.Try, ast.Match)):
            return True
    return False


def _python_nearest_scope(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return node


def _python_unique_expression_bindings(scope: ast.AST) -> dict[str, ast.expr] | None:
    values: dict[str, list[ast.expr]] = {}
    for node in _python_ordered_assignments(scope):
        if _python_in_method_branch(node, scope) or node.value is None:
            continue
        targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
        if len(targets) == 1 and isinstance(targets[0], ast.Name):
            values.setdefault(targets[0].id, []).append(node.value)
    if any(len(items) > 1 for items in values.values()):
        return None
    return {name: items[0] for name, items in values.items()}


def _python_redescending_argument(call: ast.Call, resolver: dict[str, str]) -> bool:
    values = [item.value for item in call.keywords if item.arg in {"M", "norm", "psi"}]
    return (
        len(values) == 1
        and isinstance(values[0], ast.Call)
        and _python_call_path(values[0], resolver) in _PYTHON_REDESCENDING_CALLS
    )


def _python_bound_argument(
    call: ast.Call, position: int, names: tuple[str, ...]
) -> ast.expr | None:
    named = [item.value for item in call.keywords if item.arg in names]
    if len(named) == 1:
        return named[0]
    if not named and len(call.args) > position:
        return call.args[position]
    return None


def _python_resolved_solve(
    node: ast.expr,
    assignments: dict[str, ast.expr],
    resolver: dict[str, str],
) -> tuple[str, ast.Call] | None:
    value = assignments.get(node.id) if isinstance(node, ast.Name) else node
    if (
        not isinstance(value, ast.Call)
        or _python_call_path(value, resolver) not in _PYTHON_SOLVE_CALLS
        or len(value.args) < 2
    ):
        return None
    factor = value.args[0]
    return (factor.id, value) if isinstance(factor, ast.Name) else None


def _python_shape(operand: CanonicalOperand, *nodes: ast.AST) -> _SourceShape:
    first = min(
        nodes, key=lambda item: (getattr(item, "lineno", 1), getattr(item, "col_offset", 0))
    )
    last = max(
        nodes,
        key=lambda item: (
            getattr(item, "end_lineno", getattr(item, "lineno", 1)),
            getattr(item, "end_col_offset", getattr(item, "col_offset", 0)),
        ),
    )
    return _SourceShape(
        operand,
        getattr(first, "lineno", 1),
        getattr(last, "end_lineno", getattr(last, "lineno", 1)),
        getattr(first, "col_offset", 0) + 1,
        getattr(last, "end_col_offset", getattr(last, "col_offset", 0)) + 1,
    )


def _r_copy_dosage_scan(root: Node, payload: bytes) -> _ScanOutcome:
    bindings, aliases, libraries, boundary = _r_bindings(root, payload)
    triggered = any(
        "dosage" in _r_text(node, payload).casefold() for node in _r_assignment_nodes(root)
    ) or any(
        _r_call_target(node, payload, aliases, libraries) in {"predict", "stats::predict"}
        for node in _r_call_nodes(root)
    )
    if boundary:
        return _ScanOutcome((), triggered, boundary)
    categories: dict[str, str] = {}
    shapes: list[_SourceShape] = []
    for assignment in _r_assignment_nodes(root):
        lhs = assignment.child_by_field_name("lhs")
        rhs = assignment.child_by_field_name("rhs")
        if lhs is None or rhs is None:
            continue
        if _r_has_branch_ancestor(assignment):
            if "dosage" in _r_text(lhs, payload).casefold():
                return _ScanOutcome((), True, "an R dosage-defining assignment is branch-dependent")
            continue
        category = _r_expression_category(rhs, payload, bindings, categories, aliases, libraries)
        name = _r_assignment_name(lhs, payload)
        if name is not None and category is not None:
            categories[name] = category
        if category in _COPY_OPERANDS and "dosage" in _r_text(lhs, payload).casefold():
            shapes.append(_r_shape(_COPY_OPERANDS[category], assignment))
    return _collapse_shapes(shapes, triggered, None)


def _r_ld_whitening_scan(root: Node, payload: bytes) -> _ScanOutcome:
    bindings, aliases, libraries, boundary = _r_bindings(root, payload)
    calls = [
        node
        for node in _r_call_nodes(root)
        if _r_call_target(node, payload, aliases, libraries) == "MASS::rlm"
    ]
    if boundary:
        return _ScanOutcome((), bool(calls), boundary)
    shapes: list[_SourceShape] = []
    for call in calls:
        if _r_has_branch_ancestor(call):
            return _ScanOutcome((), True, "the R robust-fit call is branch-dependent")
        arguments = _r_arguments(call, payload)
        psi = arguments.get("psi")
        if (
            psi is None
            or _r_expression_target(psi, payload, aliases, libraries) != "MASS::psi.bisquare"
        ):
            continue
        x_name: str | None = None
        y_name: str | None = None
        if "x" in arguments and "y" in arguments:
            x_name = _r_identifier(arguments["x"], payload)
            y_name = _r_identifier(arguments["y"], payload)
        elif "" in arguments:
            y_name, x_name = _r_formula_names(arguments[""], payload)
        if x_name is None or y_name is None:
            continue
        x_solve = _r_solve_binding(x_name, bindings, payload, aliases, libraries)
        y_solve = _r_solve_binding(y_name, bindings, payload, aliases, libraries)
        if x_solve is None or y_solve is None or x_solve[0] != y_solve[0]:
            continue
        factor = bindings.get(x_solve[0])
        if (
            factor is None
            or _r_expression_target(factor, payload, aliases, libraries) != "base::chol"
        ):
            continue
        shapes.append(_r_shape(_LD_OPERANDS[_LD_WHITENED], factor, x_solve[1], y_solve[1], call))
    return _collapse_shapes(shapes, bool(calls), None)


def _r_bindings(
    root: Node, payload: bytes
) -> tuple[dict[str, Node], dict[str, str], set[str], str | None]:
    bindings: dict[str, Node] = {}
    aliases: dict[str, str] = {}
    libraries: set[str] = set()
    counts: dict[str, int] = {}
    for call in _r_call_nodes(root):
        target = _r_literal_call_target(call, payload)
        if target in {"library", "base::library"}:
            positional = _r_arguments(call, payload).get("")
            package = _r_identifier(positional, payload) if positional is not None else None
            if package:
                libraries.add(package)
    for assignment in _r_assignment_nodes(root):
        lhs = assignment.child_by_field_name("lhs")
        rhs = assignment.child_by_field_name("rhs")
        if lhs is None or rhs is None or lhs.type != "identifier":
            continue
        name = _r_text(lhs, payload)
        counts[name] = counts.get(name, 0) + 1
        bindings[name] = rhs
        literal = _r_literal_target(rhs, payload)
        if literal and "::" in literal:
            aliases[name] = literal
    repeated_alias = sorted(name for name in aliases if counts.get(name) != 1)
    if repeated_alias:
        return bindings, aliases, libraries, f"an R namespace alias is rebound: {repeated_alias[0]}"
    admitted_direct = {"chol", "forwardsolve", "rlm", "psi.bisquare", "predict"}
    shadowed = sorted(admitted_direct & set(bindings) - set(aliases))
    if shadowed:
        return bindings, aliases, libraries, f"an admitted R direct call is shadowed: {shadowed[0]}"
    return bindings, aliases, libraries, None


def _r_expression_category(
    node: Node,
    payload: bytes,
    bindings: dict[str, Node],
    categories: dict[str, str],
    aliases: dict[str, str],
    libraries: set[str],
) -> str | None:
    if node.type == "identifier":
        return categories.get(_r_text(node, payload))
    if node.type == "binary_operator" and _r_operator(node, payload) == "%*%":
        lhs = node.child_by_field_name("lhs")
        rhs = node.child_by_field_name("rhs")
        if lhs is not None and rhs is not None:
            left = _r_expression_category(lhs, payload, bindings, categories, aliases, libraries)
            right = _r_expression_category(rhs, payload, bindings, categories, aliases, libraries)
            if {left, right} == {_PROBABILITIES, _CLASS_VECTOR}:
                return _COPY_EXPECTED
    if node.type == "call":
        target = _r_call_target(node, payload, aliases, libraries)
        arguments = _r_arguments(node, payload)
        if target == "nnet::multinom":
            return _MODEL_CLASSIFIER
        if target in {"glmnet::cv.glmnet", "stats::lm"}:
            return _MODEL_CONTINUOUS
        if target in {"c", "base::c"} and _r_numeric_vector(node, payload) == [0.0, 1.0, 2.0]:
            return _CLASS_VECTOR
        if target in {"as.numeric", "base::as.numeric", "as.vector", "base::as.vector"}:
            value = arguments.get("")
            return (
                None
                if value is None
                else _r_expression_category(
                    value, payload, bindings, categories, aliases, libraries
                )
            )
        if target in {"predict", "stats::predict"}:
            positional = _r_positional_arguments(node)
            if not positional:
                return None
            model_name = _r_identifier(positional[0], payload)
            model = categories.get(model_name or "")
            prediction_type = _r_string(arguments.get("type"), payload)
            if prediction_type == "probs" and model == _MODEL_CLASSIFIER:
                return _PROBABILITIES
            if prediction_type == "class" and model == _MODEL_CLASSIFIER:
                return _COPY_HARD
            if prediction_type == "response" and model == _MODEL_CONTINUOUS:
                return _COPY_CONTINUOUS
    return None


def _r_assignment_nodes(root: Node) -> list[Node]:
    return sorted(
        [
            node
            for node in _r_walk(root)
            if node.type == "binary_operator" and _r_operator_from_children(node) in {"<-", "="}
        ],
        key=lambda item: item.start_byte,
    )


def _r_call_nodes(root: Node) -> list[Node]:
    return [node for node in _r_walk(root) if node.type == "call"]


def _r_walk(root: Node) -> list[Node]:
    values: list[Node] = []
    stack = [root]
    while stack:
        node = stack.pop()
        values.append(node)
        stack.extend(reversed(node.named_children))
    return values


def _r_operator_from_children(node: Node) -> str:
    for child in node.children:
        if not child.is_named:
            value = child.type
            if value not in {"(", ")", ","}:
                return value
    return ""


def _r_operator(node: Node, payload: bytes) -> str:
    for child in node.children:
        if not child.is_named and child.type not in {"(", ")", ","}:
            return _r_text(child, payload)
    return ""


def _r_text(node: Node, payload: bytes) -> str:
    return payload[node.start_byte : node.end_byte].decode("utf-8")


def _r_literal_target(node: Node, payload: bytes) -> str | None:
    if node.type == "identifier":
        return _r_text(node, payload)
    if node.type == "namespace_operator":
        named = node.named_children
        if len(named) == 2 and all(item.type == "identifier" for item in named):
            operator = "::" if any(item.type == "::" for item in node.children) else ":::"
            return f"{_r_text(named[0], payload)}{operator}{_r_text(named[1], payload)}"
    return None


def _r_literal_call_target(call: Node, payload: bytes) -> str | None:
    function = call.child_by_field_name("function")
    return None if function is None else _r_literal_target(function, payload)


def _r_call_target(call: Node, payload: bytes, aliases: dict[str, str], libraries: set[str]) -> str:
    literal = _r_literal_call_target(call, payload)
    if literal is None:
        return "<dynamic>"
    if literal in aliases:
        return aliases[literal]
    if "::" in literal:
        return literal
    if literal in {"chol", "forwardsolve"}:
        return f"base::{literal}"
    if literal in {"rlm", "psi.bisquare"} and "MASS" in libraries:
        return f"MASS::{literal}"
    if literal == "predict":
        return "stats::predict" if "stats" in libraries else "predict"
    return literal


def _r_expression_target(
    node: Node, payload: bytes, aliases: dict[str, str], libraries: set[str]
) -> str:
    if node.type == "call":
        return _r_call_target(node, payload, aliases, libraries)
    literal = _r_literal_target(node, payload)
    if literal in aliases:
        return aliases[literal]
    if literal in {"psi.bisquare"} and "MASS" in libraries:
        return f"MASS::{literal}"
    return literal or "<dynamic>"


def _r_arguments(call: Node, payload: bytes) -> dict[str, Node]:
    arguments = call.child_by_field_name("arguments")
    result: dict[str, Node] = {}
    positional: list[Node] = []
    if arguments is None:
        return result
    for argument in arguments.named_children:
        if argument.type != "argument":
            continue
        name = argument.child_by_field_name("name")
        value = argument.child_by_field_name("value")
        if value is None:
            continue
        if name is None:
            positional.append(value)
        else:
            result[_r_text(name, payload)] = value
    if positional:
        result[""] = positional[0]
    return result


def _r_positional_arguments(call: Node) -> list[Node]:
    arguments = call.child_by_field_name("arguments")
    if arguments is None:
        return []
    return [
        value
        for argument in arguments.named_children
        if argument.type == "argument" and argument.child_by_field_name("name") is None
        for value in [argument.child_by_field_name("value")]
        if value is not None
    ]


def _r_assignment_name(node: Node, payload: bytes) -> str | None:
    if node.type == "identifier":
        return _r_text(node, payload)
    if node.type in {"subset", "subset2"}:
        base = node.named_child(0)
        return _r_text(base, payload) if base is not None and base.type == "identifier" else None
    return None


def _r_identifier(node: Node | None, payload: bytes) -> str | None:
    return _r_text(node, payload) if node is not None and node.type == "identifier" else None


def _r_string(node: Node | None, payload: bytes) -> str | None:
    if node is None or node.type != "string":
        return None
    value = _r_text(node, payload)
    return (
        value[1:-1]
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}
        else None
    )


def _r_numeric_vector(node: Node | None, payload: bytes) -> list[float] | None:
    if node is None:
        return None
    call = node if node.type == "call" else None
    if call is None or _r_literal_call_target(call, payload) not in {"c", "base::c"}:
        return None
    values: list[float] = []
    for argument in _r_positional_arguments(call):
        try:
            values.append(float(_r_text(argument, payload).removesuffix("L")))
        except ValueError:
            return None
    return values


def _r_formula_names(node: Node, payload: bytes) -> tuple[str | None, str | None]:
    if node.type != "binary_operator" or _r_operator(node, payload) != "~":
        return None, None
    lhs = node.child_by_field_name("lhs")
    rhs = node.child_by_field_name("rhs")
    y_name = _r_identifier(lhs, payload)
    names = [
        _r_text(item, payload)
        for item in (() if rhs is None else _r_walk(rhs))
        if item.type == "identifier"
    ]
    return y_name, names[0] if len(set(names)) == 1 else None


def _r_solve_binding(
    name: str,
    bindings: dict[str, Node],
    payload: bytes,
    aliases: dict[str, str],
    libraries: set[str],
) -> tuple[str, Node] | None:
    node = bindings.get(name)
    if (
        node is None
        or node.type != "call"
        or _r_call_target(node, payload, aliases, libraries) != "base::forwardsolve"
    ):
        return None
    positional = _r_positional_arguments(node)
    factor = _r_identifier(positional[0], payload) if positional else None
    return (factor, node) if factor is not None else None


def _r_has_branch_ancestor(node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type in {"if_statement", "while_statement", "repeat_statement"}:
            return True
        current = current.parent
    return False


def _r_shape(operand: CanonicalOperand, *nodes: Node) -> _SourceShape:
    first = min(nodes, key=lambda item: item.start_byte)
    last = max(nodes, key=lambda item: item.end_byte)
    return _SourceShape(
        operand,
        first.start_point.row + 1,
        last.end_point.row + 1,
        first.start_point.column + 1,
        last.end_point.column + 1,
    )


def _collapse_shapes(
    shapes: list[_SourceShape], triggered: bool, boundary: str | None
) -> _ScanOutcome:
    if not shapes:
        return _ScanOutcome((), triggered, boundary)
    operands = {canonical_json(item.operand.to_dict()) for item in shapes}
    if len(operands) != 1:
        return _ScanOutcome(tuple(shapes), True, boundary)
    first = min(shapes, key=lambda item: (item.start_line, item.start_column))
    last = max(shapes, key=lambda item: (item.end_line, item.end_column))
    merged = _SourceShape(
        first.operand,
        first.start_line,
        last.end_line,
        first.start_column,
        last.end_column,
    )
    return _ScanOutcome((merged,), True, boundary)


__all__ = [
    "STATIC_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST",
    "StaticSourceMethodAdapter",
    "make_static_source_adapter",
    "static_source_recognition_grammar_digest",
]
