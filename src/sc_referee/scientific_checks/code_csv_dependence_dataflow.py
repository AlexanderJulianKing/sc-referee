"""Closed, prose-free AST dataflow for the contract-bound repeated-row check.

Only Python syntax, established API identities, and values occupying the exact
structural slots enumerated by ADR-0076 are inspected.  Project code is never
imported or executed.  Unsupported or nonunique dataflow returns one bounded
coverage reason rather than a partial positive.
"""

from __future__ import annotations

import ast
import copy
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, cast

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.core import FrozenBaseRecord, InspectionDocument

CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())

_SOURCE_BYTE_MAX = 1 << 20
_AST_NODE_MAX = 50_000
_DEFINITION_NODE_MAX = 16
_QUERY = re.compile(
    r"\A(?P<header>[A-Za-z_][A-Za-z0-9_]*) == "
    r"(?P<quote>['\"])(?P<value>[A-Za-z0-9_.-]+)(?P=quote)\Z"
)
_STATISTICS_PREFIXES = (
    "scipy",
    "scipy.stats",
    "statsmodels",
    "pingouin",
    "pymer4",
    "bambi",
    "linearmodels",
    "sklearn",
    "pymc",
    "numpyro",
    "stan",
    "cmdstanpy",
    "rpy2",
    "lifelines",
)
_SHADOW_MODULES = frozenset({"pandas", "numpy", "scipy", "statsmodels"})
_GROUP_REDUCERS = frozenset(
    {
        "agg",
        "aggregate",
        "mean",
        "median",
        "sum",
        "first",
        "last",
        "min",
        "max",
        "count",
        "size",
        "nunique",
        "prod",
        "std",
        "var",
        "sem",
        "quantile",
        "describe",
    }
)
_FRAME_REDUCERS = frozenset(
    {
        "mean",
        "median",
        "sum",
        "min",
        "max",
        "count",
        "nunique",
        "prod",
        "std",
        "var",
        "sem",
        "quantile",
        "pivot_table",
    }
)
_NUMPY_REDUCERS = frozenset(
    {
        "numpy.mean",
        "numpy.nanmean",
        "numpy.median",
        "numpy.nanmedian",
        "numpy.sum",
        "numpy.nansum",
        "numpy.average",
        "numpy.min",
        "numpy.nanmin",
        "numpy.max",
        "numpy.nanmax",
        "numpy.std",
        "numpy.nanstd",
        "numpy.var",
        "numpy.nanvar",
    }
)
_STATISTICS_REDUCERS = frozenset(
    {
        "statistics.mean",
        "statistics.fmean",
        "statistics.median",
        "statistics.median_low",
        "statistics.median_high",
    }
)
_DEPENDENCE_APIS = frozenset(
    {
        "scipy.stats.ttest_rel",
        "scipy.stats.wilcoxon",
        "statsmodels.formula.api.mixedlm",
        "statsmodels.api.MixedLM",
        "statsmodels.regression.mixed_linear_model.MixedLM",
        "statsmodels.api.GEE",
        "statsmodels.genmod.generalized_estimating_equations.GEE",
    }
)
_DEPENDENCE_CLASS_APIS = frozenset(
    {
        "statsmodels.api.MixedLM",
        "statsmodels.regression.mixed_linear_model.MixedLM",
        "statsmodels.api.GEE",
        "statsmodels.genmod.generalized_estimating_equations.GEE",
    }
)
_POSITIVE_APIS = frozenset({"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"})
_LOOP_METHOD_REDUCTIONS = frozenset({"mean", "std", "median", "min", "max", "count", "sum"})
_X3_METHOD_REDUCTIONS = _LOOP_METHOD_REDUCTIONS | {"var", "nunique"}
_UNSHADOWED_BUILTINS = frozenset(
    {
        "print",
        "len",
        "int",
        "float",
        "str",
        "round",
        "abs",
        "min",
        "max",
        "sum",
        "sorted",
        "range",
        "enumerate",
        "zip",
        "set",
        "list",
        "dict",
        "tuple",
        "bool",
        "isinstance",
        "format",
        "any",
        "all",
        "repr",
        "divmod",
        "open",
    }
)
_V2_R1_BUILTINS = _UNSHADOWED_BUILTINS - {"open"}
_V2_NUMPY_REDUCERS = frozenset(
    {
        "mean",
        "nanmean",
        "median",
        "nanmedian",
        "sum",
        "nansum",
        "average",
        "min",
        "nanmin",
        "max",
        "nanmax",
        "std",
        "nanstd",
        "var",
        "nanvar",
        "prod",
        "nanprod",
        "percentile",
        "nanpercentile",
        "quantile",
        "nanquantile",
        "ptp",
        "all",
        "any",
        "count_nonzero",
    }
)
_V2_NUMPY_ELEMENTWISE = frozenset(
    {
        "abs",
        "absolute",
        "sqrt",
        "square",
        "exp",
        "expm1",
        "log",
        "log1p",
        "log2",
        "log10",
        "power",
        "minimum",
        "maximum",
        "clip",
        "round",
        "around",
        "rint",
        "floor",
        "ceil",
        "trunc",
        "isfinite",
        "isnan",
        "isinf",
        "sign",
    }
)
_V2_NUMPY_CONSTRUCTORS = frozenset({"array", "asarray", "arange", "linspace", "concatenate"})
_V2_PANDAS_READONLY_METHODS = frozenset(
    {
        "mean",
        "std",
        "var",
        "median",
        "min",
        "max",
        "sum",
        "count",
        "nunique",
        "sem",
        "any",
        "all",
        "describe",
        "round",
        "head",
        "to_string",
        "unique",
        "value_counts",
        "isna",
        "notna",
        "items",
        "iterrows",
        "reset_index",
        "sort_values",
        "tolist",
        "quantile",
        "duplicated",
        "drop_duplicates",
        "reindex",
        "unstack",
        "to_numpy",
    }
)
_V2_PANDAS_READONLY_PROPERTIES = frozenset({"columns", "index", "shape", "size", "dtypes"})
_V2_STRING_METHODS = frozenset(
    {
        "join",
        "format",
        "lower",
        "upper",
        "strip",
        "lstrip",
        "rstrip",
        "replace",
        "split",
        "rsplit",
        "startswith",
        "endswith",
        "center",
        "ljust",
        "rjust",
        "zfill",
        "title",
        "capitalize",
        "casefold",
    }
)
_V2_EXCEPTION_NAMES = frozenset(
    {
        "Exception",
        "ValueError",
        "TypeError",
        "RuntimeError",
        "KeyError",
        "IndexError",
        "AssertionError",
        "FileNotFoundError",
    }
)
_V2_RESAMPLING_REDUCERS = frozenset(
    {
        "numpy.mean",
        "numpy.nanmean",
        "numpy.std",
        "numpy.nanstd",
        "numpy.percentile",
        "numpy.nanpercentile",
        "numpy.quantile",
        "numpy.nanquantile",
    }
)
_V2_RANDOM_MODULE_DRAWS = frozenset(
    {
        "numpy.random.choice",
        "numpy.random.randint",
        "numpy.random.random",
        "numpy.random.random_sample",
        "numpy.random.sample",
        "numpy.random.ranf",
        "numpy.random.standard_normal",
        "numpy.random.normal",
        "numpy.random.uniform",
    }
)
_V2_RANDOM_GENERATOR_METHODS = frozenset(
    {"choice", "integers", "random", "standard_normal", "normal", "uniform"}
)
_V2_RESAMPLING_MIN_TRIPS = 50


@dataclass(frozen=True, order=True)
class CodeEvidenceSpan:
    role: Literal["reader", "left_selection", "right_selection", "procedure", "output_sink"]
    start_line: int
    end_line: int
    start_column: int
    end_column: int


@dataclass(frozen=True)
class CodeDataflowFacts:
    reader_api: str
    selection_kinds: tuple[str, str]
    value_column: str
    group_values: tuple[str, str]
    procedure_id: str
    procedure_variant: str
    output_sink_kinds: tuple[str, ...]
    dataflow_max_definition_nodes: int
    descriptive_loop_count: int
    evidence_spans: tuple[CodeEvidenceSpan, ...]


@dataclass(frozen=True)
class CodeDataflowResult:
    facts: CodeDataflowFacts | None
    reason: str | None

    def __post_init__(self) -> None:
        if (self.facts is None) == (self.reason is None):
            raise ValueError("code dataflow result must contain facts or one reason")


@dataclass(frozen=True)
class SourceEnvelope:
    analysis: InspectionDocument | None
    reason: str | None


@dataclass(frozen=True)
class _Value:
    kind: str
    node: ast.AST
    root: str | None = None
    group_column: str | None = None
    group_value: str | None = None
    value_column: str | None = None
    selection_kind: str | None = None
    depth: int = 1
    aggregated: bool = False
    unknown: bool = False
    counter_node: ast.AST | None = None
    call_origins: frozenset[ast.Call] = frozenset()
    descriptive_members: frozenset[str | int] = frozenset()
    members: tuple[tuple[str | int, _Value], ...] = ()


@dataclass(frozen=True)
class _Reader:
    api: str
    path: str | None
    call: ast.Call
    target: str | None
    parsed_date_columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Test:
    api: str
    variant: str
    call: ast.Call
    target: ast.expr
    left_name: str
    right_name: str
    statistic_name: str | None
    p_name: str | None
    result_name: str | None


@dataclass(frozen=True)
class _Sink:
    call: ast.Call
    kind: str
    payloads: tuple[ast.expr, ...]
    p_result_eligible: bool


@dataclass
class _Resolver:
    imports: dict[str, str]
    constants: dict[str, str]
    literals: dict[str, int | float | bool]
    tuples: dict[str, tuple[object, ...]]
    sequence_kinds: dict[str, str]
    file_parents: set[str]
    builtins_shadowed: set[str]
    accepted_names: set[str]

    def qualified(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return self.imports.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            parent = self.qualified(node.value)
            return f"{parent}.{node.attr}" if parent else None
        return None

    def string(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return self.constants.get(node.id)
        return None

    def sequence(self, node: ast.expr) -> tuple[object, ...] | None:
        if isinstance(node, (ast.List, ast.Tuple)):
            values = _closed_sequence_elements(node.elts)
            return tuple(values) if values is not None else None
        if isinstance(node, ast.Name):
            return self.tuples.get(node.id)
        return None


@dataclass(frozen=True)
class _Expansion:
    scope: tuple[ast.stmt, ...] | None
    reason: str | None


def select_code_source_envelope(
    *,
    base_records: Sequence[FrozenBaseRecord],
    documents: Sequence[InspectionDocument],
) -> SourceEnvelope:
    """Select root ``analysis.py`` and complete the alternate-analysis scan."""

    paths = _regular_file_paths(base_records)
    if paths is None:
        return SourceEnvelope(None, "other-python-statistics-scan-unavailable")
    folded = [(path, PurePosixPath(path).suffix.lower()) for path in paths]
    if any(suffix in {".ipynb", ".r"} for _, suffix in folded):
        return SourceEnvelope(None, "alternate-analysis-file-present")
    if paths.count("analysis.py") != 1:
        return SourceEnvelope(None, "analysis-source-envelope-unavailable")
    matches = [item for item in documents if item.path == "analysis.py"]
    if len(matches) != 1 or not _valid_python_document(matches[0]):
        return SourceEnvelope(None, "analysis-source-envelope-unavailable")
    analysis = matches[0]
    try:
        analysis_tree = _bounded_parse(analysis.content)
    except (SyntaxError, UnicodeError, ValueError):
        return SourceEnvelope(None, "analysis-source-envelope-unavailable")

    other_paths = sorted(
        path for path, suffix in folded if suffix == ".py" and path != "analysis.py"
    )
    aggregate_bytes = len(analysis.content)
    aggregate_nodes = sum(1 for _ in ast.walk(analysis_tree))
    by_path: dict[str, list[InspectionDocument]] = defaultdict(list)
    for document in documents:
        if document.path in other_paths:
            by_path[document.path].append(document)
    for path in other_paths:
        candidates = by_path.get(path, [])
        if len(candidates) != 1 or not _valid_python_document(candidates[0]):
            return SourceEnvelope(None, "other-python-statistics-scan-unavailable")
        document = candidates[0]
        try:
            tree = _bounded_parse(document.content)
        except (SyntaxError, UnicodeError, ValueError):
            return SourceEnvelope(None, "other-python-statistics-scan-unavailable")
        aggregate_bytes += len(document.content)
        aggregate_nodes += sum(1 for _ in ast.walk(tree))
        if aggregate_bytes > _SOURCE_BYTE_MAX or aggregate_nodes > _AST_NODE_MAX:
            return SourceEnvelope(None, "other-python-statistics-scan-unavailable")
        imports = _import_candidates(tree)
        if imports is None:
            return SourceEnvelope(None, "other-python-statistics-scan-unavailable")
        if any(_prefix_hit(item, _STATISTICS_PREFIXES) for item in imports):
            return SourceEnvelope(None, "statistics-api-imported-outside-analysis-py")

    imports = _import_candidates(analysis_tree)
    if imports is None:
        return SourceEnvelope(None, "api-resolution-ambiguous")
    local_names = {PurePosixPath(path).stem for path in other_paths if "/" not in path}
    package_names = {
        path.split("/", 1)[0]
        for path in other_paths
        if path.endswith("/__init__.py") and "/" in path
    }
    imported_roots = {item.split(".", 1)[0] for item in imports}
    if imported_roots & (local_names | package_names):
        return SourceEnvelope(None, "api-resolution-ambiguous")
    if local_names & _SHADOW_MODULES or package_names & _SHADOW_MODULES:
        return SourceEnvelope(None, "api-resolution-ambiguous")
    return SourceEnvelope(analysis, None)


def analyze_code_csv_dataflow(
    content: bytes,
    *,
    authorized_path: str,
    unit_column: str,
    group_column: str,
    csv_header: Sequence[str],
    group_values: tuple[str, str],
) -> CodeDataflowResult:
    """Return one complete direct-row code fact or a closed coverage reason."""

    try:
        tree = _bounded_parse(content)
        if _definition_shadows_builtin(tree):
            return CodeDataflowResult(None, "api-resolution-ambiguous")
        scope, setup, helpers, reason = _chosen_scope(tree)
        if reason is not None:
            return CodeDataflowResult(None, reason)
        assert scope is not None
        if any(
            isinstance(node, (ast.Global, ast.Nonlocal))
            for statement in scope
            for node in ast.walk(statement)
        ):
            return CodeDataflowResult(None, "unsupported-control-flow-on-path")
        resolver, reason = _resolver((*setup, *scope))
        if reason is not None:
            return CodeDataflowResult(None, reason)
        assert resolver is not None
        normalization = _normalize_contract_domain_loops(
            scope=scope,
            resolver=resolver,
            group_values=group_values,
            helpers=helpers,
        )
        if normalization.reason is not None:
            return CodeDataflowResult(None, normalization.reason)
        assert normalization.scope is not None
        expansion = _expand_relevant_helpers(
            scope=normalization.scope,
            helpers=helpers,
            resolver=resolver,
            group_values=group_values,
        )
        if expansion.reason is not None:
            return CodeDataflowResult(None, expansion.reason)
        assert expansion.scope is not None
        expanded_resolver, reason = _resolver((*setup, *expansion.scope))
        if reason is not None:
            return CodeDataflowResult(None, reason)
        assert expanded_resolver is not None
        analyzer = _Analyzer(
            scope=expansion.scope,
            resolver=expanded_resolver,
            authorized_path=authorized_path,
            unit_column=unit_column,
            group_column=group_column,
            csv_header=tuple(csv_header),
            group_values=group_values,
        )
        return analyzer.run()
    except (ArithmeticError, RecursionError, UnicodeError, ValueError):
        return CodeDataflowResult(None, "code-csv-dependence-inspection-exception")


class _Analyzer:
    def __init__(
        self,
        *,
        scope: tuple[ast.stmt, ...],
        resolver: _Resolver,
        authorized_path: str,
        unit_column: str,
        group_column: str,
        csv_header: tuple[str, ...],
        group_values: tuple[str, str],
    ) -> None:
        self.scope = scope
        self.resolver = resolver
        self.authorized_path = authorized_path
        self.unit_column = unit_column
        self.group_column = group_column
        self.csv_header = csv_header
        self.group_values = group_values
        self.values: dict[str, _Value] = {}
        self.definitions: defaultdict[str, int] = defaultdict(int)
        self.tests: list[_Test] = []
        self.descriptive_loops = 0
        self.reasons: list[tuple[tuple[int, int, int], str]] = []
        self.loops: list[ast.For] = []
        self.assignments = _assignment_expressions(scope)
        self.sinks = _registered_sinks(scope, resolver)
        self.slice_names: set[str] = set()
        self.descriptive_names: set[str] = set()
        self.tainted_names: set[str] = set()
        self.reader: _Reader | None = None
        self.deferred_auxiliary_stores: list[tuple[ast.Assign, str]] = []
        self.reconstruction_names = {
            node.targets[0].value.id
            for node in _walk_statements(scope)
            if isinstance(node, ast.Assign)
            and bool(getattr(node, "_sc_v22_reconstruction_store", False))
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].value, ast.Name)
        }

    def run(self) -> CodeDataflowResult:
        readers = self._reader_census()
        if len(readers) > 1:
            return CodeDataflowResult(None, "additional-accepted-reader-present")
        if not readers:
            if self._relevant_helper_call_present():
                return CodeDataflowResult(None, "interprocedural-call-unresolved")
            return CodeDataflowResult(None, "authorized-reader-lineage-unavailable")
        reader = readers[0]
        if reader.path != self.authorized_path or reader.target is None:
            return CodeDataflowResult(None, "authorized-reader-lineage-unavailable")
        self.reader = reader
        self.values[reader.target] = _Value("reader", reader.call, root=reader.target)
        self.definitions[reader.target] = 1

        for statement in self.scope:
            if self._contains(reader.call, statement):
                continue
            self._statement(statement)

        self._census_inplace_mutations()
        self._census_nested_tests()

        candidates = [test for test in self.tests if self._candidate_operands(test) is not None]
        if self.deferred_auxiliary_stores:
            if len(candidates) != 1:
                return CodeDataflowResult(None, "tracked-value-mutation")
            operands = self._candidate_operands(candidates[0])
            if operands is None:
                return CodeDataflowResult(None, "tracked-value-mutation")
            protected_columns = {
                self.unit_column,
                self.group_column,
                str(operands[0].value_column),
                str(operands[1].value_column),
            }
            if any(column in protected_columns for _, column in self.deferred_auxiliary_stores):
                return CodeDataflowResult(None, "tracked-value-mutation")
        if self.reader.parsed_date_columns and candidates:
            operands = self._candidate_operands(candidates[0]) if len(candidates) == 1 else None
            if operands is None or set(self.reader.parsed_date_columns) & {
                str(operands[0].value_column),
                str(operands[1].value_column),
            }:
                return CodeDataflowResult(None, "authorized-reader-lineage-unavailable")
        first_mutation = min(
            (item for item in self.reasons if item[1] == "tracked-value-mutation"),
            default=None,
            key=lambda item: item[0],
        )
        if first_mutation is not None:
            aggregated_nodes = [
                value.counter_node or value.node
                for test in candidates
                for value in (self.values.get(test.left_name), self.values.get(test.right_name))
                if value is not None and value.aggregated
            ]
            if (
                not aggregated_nodes
                or min(map(_position, aggregated_nodes))[:2] >= first_mutation[0][:2]
            ):
                return CodeDataflowResult(None, "tracked-value-mutation")
        if len(candidates) > 1:
            return CodeDataflowResult(None, "multiple-rowwise-test-candidates")
        if not candidates:
            tested_values = [
                value
                for test in self.tests
                for value in (self.values.get(test.left_name), self.values.get(test.right_name))
                if value is not None
            ]
            if (
                len(self.tests) == 1
                and len(tested_values) == 2
                and all(value.aggregated for value in tested_values)
                and any(value.value_column not in self.csv_header for value in tested_values)
                and all(
                    isinstance(value.counter_node, ast.Call)
                    and isinstance(value.counter_node.func, ast.Attribute)
                    and value.counter_node.func.attr == "mean"
                    for value in tested_values
                )
            ):
                return CodeDataflowResult(None, "two-group-row-selection-unavailable")
            if any(value.aggregated for value in tested_values):
                return CodeDataflowResult(None, "aggregation-on-test-operand-path")
            if len(self.tests) == 1:
                provisional = self.tests[0]
                self.slice_names = self._backward_slice_names(provisional)
                self.tainted_names = self._tainted_name_closure()
                guard = self._component_guard_reason(provisional)
                if guard is not None:
                    return CodeDataflowResult(None, guard)
            if self.tests:
                return CodeDataflowResult(None, "two-group-row-selection-unavailable")
            reason = self._first_reason()
            return CodeDataflowResult(None, reason or "rowwise-two-sample-test-unavailable")
        test = candidates[0]
        left, right = self._candidate_operands(test) or (None, None)
        assert left is not None and right is not None
        if left.root != self.reader.target or right.root != self.reader.target:
            return CodeDataflowResult(None, "test-operands-not-from-authorized-reader")
        if (
            left.value_column not in self.csv_header or right.value_column not in self.csv_header
        ) and all(
            isinstance(value.counter_node, ast.Call)
            and isinstance(value.counter_node.func, ast.Attribute)
            and value.counter_node.func.attr == "mean"
            for value in (left, right)
        ):
            return CodeDataflowResult(None, "two-group-row-selection-unavailable")
        if left.aggregated or right.aggregated:
            return CodeDataflowResult(None, "aggregation-on-test-operand-path")
        if left.unknown or right.unknown:
            return CodeDataflowResult(None, "unrecognized-call-on-path")

        self.slice_names = self._backward_slice_names(test)
        if any(self.definitions[name] > 1 for name in self.slice_names):
            return CodeDataflowResult(None, "tracked-value-mutation")
        self.tainted_names = self._tainted_name_closure()
        if any(reason == "aggregation-on-test-operand-path" for _, reason in self.reasons):
            return CodeDataflowResult(None, "aggregation-on-test-operand-path")
        loop_reason = self._validate_loops()
        if loop_reason is not None:
            return CodeDataflowResult(None, loop_reason)
        sinks = self._result_sinks(test)
        p_depth = max(
            (
                depth
                for sink in sinks
                for payload in sink.payloads
                if (depth := _p_derived_depth(payload, test, self.resolver, self.assignments))
                is not None
            ),
            default=0,
        )
        component_depth = self._component_definition_depth(test)
        max_depth = max(left.depth, right.depth, p_depth + 1, component_depth, 3)
        if max_depth > _DEFINITION_NODE_MAX:
            return CodeDataflowResult(None, "dataflow-definition-ceiling-exceeded")

        guard = self._component_guard_reason(test)
        if guard is not None:
            return CodeDataflowResult(None, guard)
        admission_reason = self._admission_reason(test)
        if admission_reason is not None:
            return CodeDataflowResult(None, admission_reason)
        reason = self._first_reason(before_or_at=test.call)
        if reason is not None:
            return CodeDataflowResult(None, reason)
        if not sinks:
            return CodeDataflowResult(None, "test-result-output-sink-unavailable")
        ordered = sorted((left, right), key=lambda value: _position(value.node))
        evidence = (
            CodeEvidenceSpan("reader", *_span(self.reader.call)),
            CodeEvidenceSpan("left_selection", *_span(ordered[0].node)),
            CodeEvidenceSpan("right_selection", *_span(ordered[1].node)),
            CodeEvidenceSpan("procedure", *_span(test.call)),
            *(
                CodeEvidenceSpan("output_sink", *_span(node))
                for sink in sorted(sinks, key=lambda item: _position(item.call))
                for node in (sink.call.func,)
            ),
        )
        return CodeDataflowResult(
            CodeDataflowFacts(
                reader_api=self.reader.api,
                selection_kinds=(
                    str(ordered[0].selection_kind),
                    str(ordered[1].selection_kind),
                ),
                value_column=str(ordered[0].value_column),
                group_values=(str(ordered[0].group_value), str(ordered[1].group_value)),
                procedure_id=test.api,
                procedure_variant=test.variant,
                output_sink_kinds=tuple(sorted({sink.kind for sink in sinks})),
                dataflow_max_definition_nodes=max_depth,
                descriptive_loop_count=self.descriptive_loops,
                evidence_spans=evidence,
            ),
            None,
        )

    def _reader_census(self) -> list[_Reader]:
        result: list[_Reader] = []
        for node in _walk_statements(self.scope):
            if not isinstance(node, ast.Call):
                continue
            api = self.resolver.qualified(node.func)
            reader_id: str | None = None
            path: str | None = None
            if api == "pandas.read_csv" and len(node.args) == 1:
                if not node.keywords:
                    reader_id = "pandas_read_csv_v1"
                    path = _static_path(node.args[0], self.resolver)
                    parsed_dates: tuple[str, ...] = ()
                else:
                    parsed_dates = _parse_dates_columns(
                        node,
                        resolver=self.resolver,
                        csv_header=self.csv_header,
                        forbidden={self.unit_column, self.group_column},
                    )
                    if parsed_dates:
                        reader_id = "pandas_read_csv_parse_dates_v1"
                        path = _static_path(node.args[0], self.resolver)
            elif api == "numpy.genfromtxt" and len(node.args) == 1:
                expected = {
                    "delimiter": ",",
                    "names": True,
                    "dtype": None,
                    "encoding": "utf-8",
                }
                actual = _literal_keywords(node.keywords)
                if actual == expected:
                    reader_id = "numpy_genfromtxt_named_csv_v1"
                    path = _static_path(node.args[0], self.resolver)
            if reader_id is not None:
                result.append(
                    _Reader(
                        reader_id,
                        path,
                        node,
                        _assigned_name(self.scope, node),
                        parsed_dates if api == "pandas.read_csv" else (),
                    )
                )
        return sorted(result, key=lambda item: _position(item.call))

    def _statement(self, statement: ast.stmt) -> None:
        if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Pass)):
            return
        if _is_docstring(statement):
            return
        if isinstance(statement, ast.Assign):
            self._assign(statement)
            return
        if isinstance(statement, ast.AnnAssign):
            if statement.value is None:
                return
            synthetic = ast.Assign(targets=[statement.target], value=statement.value)
            ast.copy_location(synthetic, statement)
            self._assign(synthetic)
            return
        if isinstance(statement, (ast.AugAssign, ast.Delete)):
            if _reads_any(statement, self.values) or any(
                _root_name(target) in self.values
                for target in (
                    statement.targets if isinstance(statement, ast.Delete) else (statement.target,)
                )
            ):
                self._reason(statement, "tracked-value-mutation", 1)
            return
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            self._expression_call(statement.value)
            return
        if isinstance(statement, ast.For):
            self.loops.append(statement)
            self._bind_loop_target(statement)
            for child in (*statement.body, *statement.orelse):
                self._statement(child)
            return
        if isinstance(statement, (ast.If, ast.While)):
            if isinstance(statement, ast.If) and _exact_main_guard(statement):
                return
            for child in (*statement.body, *statement.orelse):
                self._statement(child)
            return
        if isinstance(statement, ast.Try):
            for child in (
                *statement.body,
                *(item for handler in statement.handlers for item in handler.body),
                *statement.orelse,
                *statement.finalbody,
            ):
                self._statement(child)
            return
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            for child in statement.body:
                self._statement(child)
            return
        if isinstance(statement, (ast.Assert, ast.Raise, ast.Return)):
            return
        if isinstance(statement, ast.If) and _exact_main_guard(statement):
            return
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        if _reads_any(statement, self.values):
            self._reason(statement, "control-flow-body-unadmitted", 12)

    def _bind_loop_target(self, statement: ast.For) -> None:
        parents = [
            self.values[item.id]
            for item in ast.walk(statement.iter)
            if isinstance(item, ast.Name) and item.id in self.values
        ]
        if (
            isinstance(statement.iter, ast.Call)
            and isinstance(statement.iter.func, ast.Attribute)
            and statement.iter.func.attr in {"items", "iterrows"}
            and isinstance(statement.iter.func.value, ast.Name)
            and statement.iter.func.value.id in self.values
        ):
            parents = [self.values[statement.iter.func.value.id]]
        if not parents:
            return
        parent = max(parents, key=lambda item: item.depth)
        for name in _store_names(statement.target):
            if name in self.values:
                self._reason(statement.target, "loop-target-aliases-tracked", 2)
                continue
            self.values[name] = _value_at_node(parent, statement.target, parent.depth + 1)
            self.definitions[name] = 1

    def _assign(self, statement: ast.Assign) -> None:
        if len(statement.targets) != 1:
            if _reads_any(statement.value, self.values):
                self._reason(statement, "code-dataflow-graph-incomplete", 9)
            return
        target = statement.targets[0]
        if isinstance(target, (ast.Subscript, ast.Attribute)):
            root = _root_name(target)
            parent = self.values.get(root) if root is not None else None
            if (
                isinstance(target, ast.Subscript)
                and parent is not None
                and parent.kind == "reader"
                and self.reader is not None
                and root == self.reader.target
                and (
                    column := _same_column_auxiliary_conversion(
                        target,
                        statement.value,
                        self.resolver,
                    )
                )
                is not None
            ):
                self.deferred_auxiliary_stores.append((statement, column))
                return
            if (
                isinstance(target, ast.Subscript)
                and bool(getattr(statement, "_sc_v22_reconstruction_store", False))
                and isinstance(target.value, ast.Name)
                and parent is not None
                and parent.kind == "reconstruction_container"
                and (member := _literal_subscript_member(target.slice)) is not None
                and member in self.group_values
                and member not in dict(parent.members)
                and (value := self._value(statement.value)) is not None
            ):
                members = (*parent.members, (member, value))
                self.values[target.value.id] = _Value(
                    "reconstruction_container",
                    parent.node,
                    root=(
                        value.root
                        if not parent.members
                        else parent.root
                        if parent.root == value.root
                        else None
                    ),
                    depth=max(parent.depth, value.depth),
                    aggregated=parent.aggregated or value.aggregated,
                    unknown=parent.unknown or value.unknown,
                    counter_node=parent.counter_node or value.counter_node,
                    call_origins=parent.call_origins | value.call_origins,
                    descriptive_members=frozenset(key for key, _ in members),
                    members=members,
                )
                return
            if parent is not None and parent.kind in {
                "reader",
                "selection",
                "identity",
                "derived",
                "grouped",
                "aggregation",
                "member_container",
                "reconstruction_container",
            }:
                self._reason(statement, "tracked-value-mutation", 1)
                return
        if isinstance(target, ast.Name):
            name = target.id
            if (
                isinstance(statement.value, ast.Name)
                and (parent := self.values.get(statement.value.id)) is not None
                and parent.kind == "reconstruction_container"
            ):
                self._reason(statement, "unregistered-component-consumer", 2)
                return
            if (
                name in self.reconstruction_names
                and isinstance(statement.value, ast.Dict)
                and not statement.value.keys
            ):
                self._bind(name, _Value("reconstruction_container", statement.value), statement)
                return
            if (
                isinstance(statement.value, ast.Call)
                and self.resolver.qualified(statement.value.func) in _POSITIVE_APIS
            ):
                self._maybe_test(statement.value, target)
                return
            descriptive = self._descriptive_value(statement.value)
            if descriptive is not None:
                self._bind(name, descriptive, statement)
                self.descriptive_names.add(name)
                return
            if bool(getattr(statement, "_sc_v2_return_root", False)):
                returned = self._value(statement.value)
                if returned is None:
                    returned = _Value(
                        "unknown",
                        statement.value,
                        root=_single_root(statement.value, self.values),
                        depth=_parent_depth(statement.value, self.values) + 1,
                        unknown=True,
                        call_origins=_call_origins_read(statement.value, self.values),
                    )
                self._bind(name, returned, statement)
                if returned.kind in {"descriptive_scalar", "descriptive_literal"}:
                    self.descriptive_names.add(name)
                return
            value = self._value(statement.value)
            if value is not None:
                self._bind(name, value, statement)
            return
        if isinstance(target, (ast.Tuple, ast.List)) and all(
            isinstance(item, ast.Name) for item in target.elts
        ):
            if (
                1 <= len(target.elts) <= 16
                and isinstance(statement.value, ast.Tuple)
                and len(statement.value.elts) == len(target.elts)
                and not any(isinstance(item, ast.Starred) for item in statement.value.elts)
            ):
                descriptive_values = [
                    self._descriptive_element_value(item) for item in statement.value.elts
                ]
                if all(item is not None for item in descriptive_values):
                    for target_item, value in zip(target.elts, descriptive_values, strict=True):
                        assert isinstance(target_item, ast.Name)
                        assert value is not None
                        self._bind(target_item.id, value, statement)
                        self.descriptive_names.add(target_item.id)
                    return
            if len(target.elts) == 2:
                self._maybe_test(statement.value, target)
                if any(test.target is target for test in self.tests):
                    return
            if _reads_any(statement.value, self.values):
                self._reason(statement, "admission-slice-reaches-operand", 10)
            return
        if _reads_any(statement.value, self.values):
            self._reason(statement, "unsupported-expression-on-path", 9)

    def _bind(self, name: str, value: _Value, node: ast.AST) -> None:
        self.definitions[name] += 1
        self.values[name] = value

    def _census_inplace_mutations(self) -> None:
        for call in (node for node in _walk_statements(self.scope) if isinstance(node, ast.Call)):
            if not isinstance(call.func, ast.Attribute):
                continue
            if not any(
                keyword.arg == "inplace"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in call.keywords
            ):
                continue
            if _reads_any(call.func.value, self.values):
                self._reason(call, "tracked-value-mutation", 1)

    def _value(self, expression: ast.expr) -> _Value | None:
        if isinstance(expression, ast.Name) and expression.id in self.values:
            parent = self.values[expression.id]
            return _Value(
                (
                    "identity"
                    if parent.kind
                    in {"reader", "selection", "identity", "derived", "grouped", "aggregation"}
                    else parent.kind
                ),
                expression,
                root=parent.root,
                group_column=parent.group_column,
                group_value=parent.group_value,
                value_column=parent.value_column,
                selection_kind=parent.selection_kind,
                depth=parent.depth + 1,
                aggregated=parent.aggregated,
                unknown=parent.unknown,
                counter_node=parent.counter_node,
                call_origins=parent.call_origins,
                descriptive_members=parent.descriptive_members,
                members=parent.members,
            )
        if (
            isinstance(expression, ast.Subscript)
            and (member := _literal_subscript_member(expression.slice)) is not None
        ):
            container = (
                self.values.get(expression.value.id)
                if isinstance(expression.value, ast.Name)
                else self._value(expression.value)
            )
            mapped = dict(container.members).get(member) if container is not None else None
            if mapped is not None and container is not None:
                return _value_at_node(mapped, expression, mapped.depth + 1)
            if container is not None and (
                container.kind == "descriptive_container"
                and member in container.descriptive_members
            ):
                return _Value(
                    "descriptive_scalar",
                    expression,
                    root=container.root,
                    depth=container.depth + 1,
                    call_origins=container.call_origins,
                )
        selection = self._selection(expression)
        if selection is not None:
            return selection
        column = _plain_column_read(expression, self.values, self.resolver, self.csv_header)
        if column is not None:
            return column
        label = _nonreader_label_read(expression, self.values, self.resolver)
        if label is not None:
            return label
        if isinstance(expression, ast.Call):
            return self._call_value(expression)
        if isinstance(expression, (ast.Dict, ast.Tuple, ast.List)):
            return self._container_value(expression)
        descriptive = self._descriptive_descendant(expression)
        if descriptive is not None:
            return descriptive
        if _reads_any(expression, self.values):
            parents = [
                self.values[item.id]
                for item in ast.walk(expression)
                if isinstance(item, ast.Name) and item.id in self.values
            ]
            return _Value(
                "unknown",
                expression,
                root=_single_root(expression, self.values),
                depth=_parent_depth(expression, self.values) + 1,
                aggregated=any(item.aggregated for item in parents),
                unknown=True,
                counter_node=next(
                    (item.counter_node for item in parents if item.counter_node is not None),
                    None,
                ),
                call_origins=_call_origins_read(expression, self.values),
            )
        return None

    def _container_value(self, expression: ast.Dict | ast.Tuple | ast.List) -> _Value | None:
        members: list[tuple[str | int, ast.expr]] = []
        if isinstance(expression, ast.Dict):
            if not (1 <= len(expression.keys) <= 16) or any(key is None for key in expression.keys):
                return None
            seen: set[str | int] = set()
            for key, item in zip(expression.keys, expression.values, strict=True):
                assert key is not None
                member = _literal_container_key(key)
                if member is None or member in seen:
                    return None
                seen.add(member)
                members.append((member, item))
        else:
            if not (1 <= len(expression.elts) <= 16) or any(
                isinstance(item, ast.Starred) for item in expression.elts
            ):
                return None
            members.extend(enumerate(expression.elts))
        resolved: list[tuple[str | int, _Value]] = []
        parents: list[_Value] = []
        for member, item in members:
            value: _Value | None
            if isinstance(item, ast.Constant):
                value = _Value("descriptive_literal", item)
            else:
                value = (
                    self._descriptive_value(item)
                    or self._value(item)
                    or self._test_payload_value(item)
                )
                if value is None:
                    if not _reads_any(item, self.values):
                        value = _Value("descriptive_literal", item)
                    else:
                        return None
            resolved.append((member, value))
            if value.root is not None:
                parents.append(value)
        return _Value(
            "member_container",
            expression,
            root=(
                parents[0].root if parents and len({item.root for item in parents}) == 1 else None
            ),
            depth=max((item.depth for item in parents), default=0) + 1,
            aggregated=any(item.aggregated for item in parents),
            unknown=any(item.unknown for item in parents),
            call_origins=frozenset(origin for item in parents for origin in item.call_origins),
            descriptive_members=frozenset(member for member, _ in resolved),
            members=tuple(resolved),
        )

    def _test_payload_value(self, expression: ast.expr) -> _Value | None:
        for test in self.tests:
            if _p_derived_depth(expression, test, self.resolver, self.assignments) is not None:
                return _Value("test_p_result", expression, depth=2)
            if (
                _statistic_derived_depth(expression, test, self.resolver, self.assignments)
                is not None
            ):
                return _Value("test_statistic", expression, depth=2)
        return None

    def _descriptive_value(self, expression: ast.expr) -> _Value | None:
        reduction = expression
        wrapper: ast.Call | None = None
        if (
            isinstance(expression, ast.Call)
            and self.resolver.qualified(expression.func) in {"int", "float"}
            and self.resolver.qualified(expression.func) not in self.resolver.builtins_shadowed
            and len(expression.args) == 1
            and not expression.keywords
            and not (
                isinstance(expression.args[0], ast.Call)
                and self.resolver.qualified(expression.args[0].func) in {"int", "float"}
            )
        ):
            wrapper = expression
            reduction = expression.args[0]
            parents = _descriptive_expression_parents(reduction, self.values, self.resolver)
            if parents:
                return _Value(
                    "descriptive_scalar",
                    expression,
                    root=(parents[0].root if len({item.root for item in parents}) == 1 else None),
                    depth=max(item.depth for item in parents) + 1,
                    call_origins=frozenset(
                        origin for item in parents for origin in item.call_origins
                    )
                    | frozenset(
                        item for item in ast.walk(expression) if isinstance(item, ast.Call)
                    ),
                )
        if (
            isinstance(reduction, ast.Call)
            and self.resolver.qualified(reduction.func) == "round"
            and "round" not in self.resolver.builtins_shadowed
            and not reduction.keywords
            and len(reduction.args) in {1, 2}
        ):
            if len(reduction.args) == 2 and not (
                isinstance(reduction.args[1], ast.Constant)
                and isinstance(reduction.args[1].value, int)
                and not isinstance(reduction.args[1].value, bool)
            ):
                return None
            reduction = reduction.args[0]
        attribute_parent = _x7_count_attribute_parent(reduction, self.values)
        if attribute_parent is not None:
            origins = attribute_parent.call_origins | (
                frozenset({wrapper}) if wrapper else frozenset()
            )
            return _Value(
                "descriptive_scalar",
                expression,
                root=attribute_parent.root,
                depth=attribute_parent.depth + 1,
                call_origins=origins,
            )
        if not isinstance(reduction, ast.Call):
            return None
        reduction_parent: _Value | None = None
        api = self.resolver.qualified(reduction.func)
        if api in {"len", "sum", "min", "max"}:
            if (
                len(reduction.args) != 1
                or reduction.keywords
                or not isinstance(reduction.args[0], ast.Name)
            ):
                return None
            reduction_parent = self.values.get(reduction.args[0].id)
        elif isinstance(reduction.func, ast.Attribute) and isinstance(
            reduction.func.value, ast.Name
        ):
            reduction_parent = self.values.get(reduction.func.value.id)
            method = reduction.func.attr
            if method not in _X3_METHOD_REDUCTIONS:
                return None
            if method in {"std", "var"}:
                if reduction.args:
                    return None
                if reduction.keywords and not (
                    len(reduction.keywords) == 1
                    and reduction.keywords[0].arg == "ddof"
                    and isinstance(reduction.keywords[0].value, ast.Constant)
                    and reduction.keywords[0].value.value == 1
                ):
                    return None
            elif reduction.args or reduction.keywords:
                return None
        if reduction_parent is None or reduction_parent.kind not in {"selection", "identity"}:
            return None
        if reduction_parent.unknown:
            return None
        return _Value(
            "descriptive_scalar",
            expression,
            root=reduction_parent.root,
            depth=reduction_parent.depth + 1,
            aggregated=reduction_parent.aggregated,
            counter_node=reduction_parent.counter_node,
            call_origins=reduction_parent.call_origins
            | frozenset({reduction})
            | (frozenset({wrapper}) if wrapper else frozenset()),
        )

    def _descriptive_element_value(self, expression: ast.expr) -> _Value | None:
        if isinstance(expression, ast.Constant):
            return _Value("descriptive_literal", expression)
        if (
            isinstance(expression, ast.Name)
            and self.resolver.constants.get(expression.id) in self.group_values
        ):
            return _Value("descriptive_literal", expression)
        return self._descriptive_value(expression) or self._descriptive_descendant(expression)

    def _descriptive_descendant(self, expression: ast.expr) -> _Value | None:
        parents = _descriptive_expression_parents(expression, self.values, self.resolver)
        if not parents:
            return None
        return _Value(
            "descriptive_scalar",
            expression,
            root=parents[0].root if len({item.root for item in parents}) == 1 else None,
            depth=max(item.depth for item in parents) + 1,
            call_origins=frozenset(origin for item in parents for origin in item.call_origins)
            | frozenset(item for item in ast.walk(expression) if isinstance(item, ast.Call)),
        )

    def _descriptive_container_value(self, expression: ast.expr) -> _Value | None:
        members: list[tuple[str | int, ast.expr]] = []
        if isinstance(expression, ast.Dict):
            if not (1 <= len(expression.keys) <= 16) or any(key is None for key in expression.keys):
                return None
            seen: set[str | int] = set()
            for key, value in zip(expression.keys, expression.values, strict=True):
                assert key is not None
                member = _literal_container_key(key)
                if member is None or member in seen:
                    return None
                seen.add(member)
                members.append((member, value))
        elif isinstance(expression, (ast.Tuple, ast.List)):
            if not (1 <= len(expression.elts) <= 16) or any(
                isinstance(item, ast.Starred) for item in expression.elts
            ):
                return None
            members.extend(enumerate(expression.elts))
        else:
            return None
        parents: list[_Value] = []
        for _, value in members:
            if isinstance(value, ast.Constant):
                continue
            if (
                isinstance(value, ast.Name)
                and self.resolver.constants.get(value.id) in self.group_values
            ):
                continue
            item_parents = _descriptive_expression_parents(value, self.values, self.resolver)
            if not item_parents:
                return None
            parents.extend(item_parents)
        return _Value(
            "descriptive_container",
            expression,
            root=(
                parents[0].root if parents and len({item.root for item in parents}) == 1 else None
            ),
            depth=max((item.depth for item in parents), default=0) + 1,
            call_origins=frozenset(origin for item in parents for origin in item.call_origins),
            descriptive_members=frozenset(member for member, _ in members),
        )

    def _selection(self, expression: ast.expr) -> _Value | None:
        parsed = _pandas_selection(expression, self.values, self.resolver)
        if parsed is None:
            return None
        receiver, group, group_value, value_column, kind = parsed
        parent = self.values.get(receiver)
        if self.reader is not None and self.reader.api == "numpy_genfromtxt_named_csv_v1":
            if kind != "pandas_boolean_mask_v1":
                return _Value(
                    "unknown",
                    expression,
                    root=parent.root if parent else None,
                    depth=(parent.depth if parent else 1) + 1,
                    unknown=True,
                    call_origins=parent.call_origins if parent else frozenset(),
                )
            kind = "numpy_named_boolean_mask_v1"
        if (
            parent is None
            or group != self.group_column
            or group_value not in self.group_values
            or (value_column not in self.csv_header and not parent.aggregated)
            or value_column in {self.group_column, self.unit_column}
        ):
            return _Value(
                "unknown",
                expression,
                root=parent.root if parent else None,
                group_column=group,
                group_value=group_value,
                value_column=value_column,
                selection_kind=kind,
                depth=(parent.depth if parent else 1) + 1,
                aggregated=bool(parent and parent.aggregated),
                unknown=True,
                call_origins=parent.call_origins if parent else frozenset(),
            )
        return _Value(
            "selection",
            expression,
            root=parent.root,
            group_column=group,
            group_value=group_value,
            value_column=value_column,
            selection_kind=kind,
            depth=parent.depth + 1,
            aggregated=parent.aggregated,
            unknown=parent.unknown,
            counter_node=parent.counter_node,
            call_origins=parent.call_origins,
        )

    def _call_value(self, call: ast.Call) -> _Value | None:
        api = self.resolver.qualified(call.func)
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "to_numpy"
            and _selection_preserving_to_numpy_shape(call, self.resolver)
        ):
            receiver = call.func.value
            if isinstance(receiver, ast.Name) and self.values.get(
                receiver.id, _Value("", receiver)
            ).kind not in {"selection", "identity"}:
                return None
            parent = self._value(receiver)
            if (
                parent is not None
                and parent.kind in {"selection", "identity"}
                and not parent.aggregated
                and not parent.unknown
                and parent.value_column is not None
            ):
                return _Value(
                    "identity",
                    call,
                    root=parent.root,
                    group_column=parent.group_column,
                    group_value=parent.group_value,
                    value_column=parent.value_column,
                    selection_kind=parent.selection_kind,
                    depth=parent.depth + 1,
                    counter_node=parent.counter_node,
                    call_origins=parent.call_origins | frozenset({call}),
                    descriptive_members=parent.descriptive_members,
                    members=parent.members,
                )
        roots = _roots_read(call, self.values)
        if not roots:
            return None
        root = next(iter(roots)) if len(roots) == 1 else None
        depth = _parent_depth(call, self.values) + 1
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "groupby"
            and isinstance(call.func.value, ast.Name)
            and len(call.args) == 1
            and not call.keywords
        ):
            group = self.resolver.string(call.args[0])
            parent = self.values.get(call.func.value.id)
            if parent is not None and group is not None:
                return _Value(
                    "grouped",
                    call,
                    root=parent.root,
                    group_column=group,
                    depth=depth,
                    aggregated=parent.aggregated,
                    unknown=parent.unknown,
                    call_origins=parent.call_origins,
                )
        if _aggregation_call(call, api, self.values, self.resolver):
            return _Value(
                "aggregation",
                call,
                root=root,
                depth=depth,
                aggregated=True,
                counter_node=call,
                call_origins=_call_origins_read(call, self.values) | frozenset({call}),
            )
        origins = _call_origins_read(call, self.values) | frozenset({call})
        if _dependence_api(api) or api in _POSITIVE_APIS:
            return _Value("call", call, root=root, depth=depth, call_origins=origins)
        parents = [
            self.values[item.id]
            for item in ast.walk(call)
            if isinstance(item, ast.Name) and item.id in self.values
        ]
        nested_aggregations = [
            item
            for item in ast.walk(call)
            if isinstance(item, ast.Call)
            and _aggregation_call(
                item,
                self.resolver.qualified(item.func),
                self.values,
                self.resolver,
            )
        ]
        return _Value(
            "unknown",
            call,
            root=root,
            depth=depth,
            aggregated=bool(nested_aggregations) or any(item.aggregated for item in parents),
            unknown=True,
            counter_node=(
                nested_aggregations[0]
                if nested_aggregations
                else next(
                    (item.counter_node for item in parents if item.counter_node is not None),
                    None,
                )
            ),
            call_origins=origins,
        )

    def _maybe_test(self, expression: ast.expr, target: ast.expr) -> None:
        if not isinstance(expression, ast.Call):
            return
        api = self.resolver.qualified(expression.func)
        if api not in _POSITIVE_APIS:
            return
        if len(expression.args) != 2:
            return
        left_arg, right_arg = expression.args
        left_name = self._test_operand_name(left_arg, 0)
        right_name = self._test_operand_name(right_arg, 1)
        if left_name is None or right_name is None:
            return
        if left_name == right_name:
            return
        variant = _test_variant(api, expression.keywords)
        if variant is None:
            return
        if any(
            self.values.get(name, _Value("", expression)).kind == "descriptive_scalar"
            for name in (left_name, right_name)
        ):
            self._reason(expression, "aggregation-on-test-operand-path", 4)
        p_name: str | None = None
        statistic_name: str | None = None
        result_name: str | None = None
        if isinstance(target, ast.Name):
            result_name = target.id
            self._bind(
                result_name,
                _Value("test_result", expression, depth=1),
                target,
            )
        elif isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) == 2:
            first, second = target.elts
            if not isinstance(first, ast.Name) or not isinstance(second, ast.Name):
                return
            if first.id in self.values or second.id in self.values:
                self._reason(target, "tracked-value-mutation", 1)
                return
            self.definitions[first.id] += 1
            self.definitions[second.id] += 1
            self.values[first.id] = _Value("test_statistic", expression, depth=1)
            self.values[second.id] = _Value("test_p_result", expression, depth=1)
            p_name = second.id
            statistic_name = first.id
        self.tests.append(
            _Test(
                api=api,
                variant=variant,
                call=expression,
                target=target,
                left_name=left_name,
                right_name=right_name,
                statistic_name=statistic_name,
                p_name=p_name,
                result_name=result_name,
            )
        )

    def _census_nested_tests(self) -> None:
        known = {id(test.call) for test in self.tests}
        for call in sorted(
            (
                node
                for node in _walk_statements(self.scope)
                if isinstance(node, ast.Call)
                and self.resolver.qualified(node.func) in _POSITIVE_APIS
                and id(node) not in known
            ),
            key=_position,
        ):
            target: ast.expr = call
            for statement in _walk_statements(self.scope):
                if isinstance(statement, ast.Assign) and statement.value is call:
                    if len(statement.targets) == 1:
                        target = statement.targets[0]
                    break
                if isinstance(statement, ast.AnnAssign) and statement.value is call:
                    target = statement.target
                    break
            self._maybe_test(call, target)

    def _tainted_name_closure(self) -> set[str]:
        assert self.reader is not None and self.reader.target is not None
        tainted = {self.reader.target}
        changed = True
        while changed:
            changed = False
            for node in _walk_statements(self.scope):
                if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                    continue
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                if value is None or not (_loaded_names(value) & tainted):
                    continue
                for target in targets:
                    for name in _store_names(target):
                        if name not in tainted:
                            tainted.add(name)
                            changed = True
            for loop in self.loops:
                if _loaded_names(loop.iter) & tainted:
                    for name in _store_names(loop.target):
                        if name not in tainted:
                            tainted.add(name)
                            changed = True
        tainted.update(
            name for name, value in self.values.items() if value.root == self.reader.target
        )
        return tainted

    def _test_operand_name(self, expression: ast.expr, index: int) -> str | None:
        if isinstance(expression, ast.Name):
            return expression.id
        value = self._value(expression)
        if value is None or value.kind not in {"selection", "identity"}:
            return None
        name = f"__sc_v2_operand_{expression.lineno}_{expression.col_offset}_{index}"
        self.values[name] = value
        self.definitions[name] = 1
        return name

    def _expression_call(self, call: ast.Call) -> None:
        # Version 2.0 classifies calls only after the complete candidate and
        # component slices exist.  The former visit-time output-use heuristic
        # emitted a retired 1.x reason and could not implement R1 directionality.
        return

    def _candidate_operands(self, test: _Test) -> tuple[_Value, _Value] | None:
        left = self.values.get(test.left_name)
        right = self.values.get(test.right_name)
        if left is None or right is None:
            return None
        if left.kind not in {"selection", "identity"} or right.kind not in {
            "selection",
            "identity",
        }:
            return None
        if (
            left.value_column is None
            or left.value_column != right.value_column
            or left.group_column != self.group_column
            or right.group_column != self.group_column
            or {left.group_value, right.group_value} != set(self.group_values)
        ):
            return None
        return left, right

    def _component_guard_reason(self, candidate: _Test) -> str | None:
        guards: list[tuple[tuple[int, int, int, int], int, str]] = []
        resampling = _v2_resampling_sibling(
            self.scope,
            self.values,
            self.resolver,
            self.sinks,
            self.assignments,
        )
        if resampling is not None:
            guards.append((_position(resampling), 8, "resampling-inference-sibling-present"))
        calls = sorted(
            (node for node in _walk_statements(self.scope) if isinstance(node, ast.Call)),
            key=_position,
        )
        for call in calls:
            if call is candidate.call:
                continue
            api = self.resolver.qualified(call.func)
            if not self._call_consumes_component(call):
                continue
            if _dependence_api(api):
                guards.append((_position(call), 6, "dependence-aware-sibling-present"))
                continue
            if api in _POSITIVE_APIS and _any_aggregated_argument(call, self.values):
                guards.append((_position(call), 7, "aggregated-sibling-test-present"))
                continue
            if api in _POSITIVE_APIS:
                sibling_values = [self._value(argument) for argument in call.args[:2]]
                if any(
                    value is not None and (value.aggregated or value.kind == "descriptive_scalar")
                    for value in sibling_values
                ):
                    guards.append((_position(call), 7, "aggregated-sibling-test-present"))
                    continue
            if self._inside_valid_descriptive_loop(call):
                continue
            if _accepted_selection_call(call, self.values, self.resolver):
                continue
            if _aggregation_call(call, api, self.values, self.resolver):
                continue
            if any(sink.call is call for sink in self.sinks):
                continue
            if self._r1_readonly_call(call, candidate):
                continue
            if resampling is None:
                guards.append((_position(call), 9, "unregistered-component-consumer"))
        return min(guards, default=((), 0, None), key=lambda item: (item[0], item[1]))[2]

    def _call_consumes_component(self, call: ast.Call) -> bool:
        return bool(_reads_any(call, self.values) or _loaded_names(call) & self.tainted_names)

    def _r1_readonly_call(self, call: ast.Call, candidate: _Test) -> bool:
        api = self.resolver.qualified(call.func)
        if any(
            self._contains(call, statement.value) for statement, _ in self.deferred_auxiliary_stores
        ):
            return True
        if self.reader is not None and self._contains(call, self.reader.call):
            return True
        if any(
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id
            in (set(self.resolver.file_parents) | set(self.resolver.constants))
            and self._contains(call, statement.value)
            for statement in self.scope
        ):
            return True
        if any(sink.call is call for sink in self.sinks):
            return True
        if api in {"pathlib.Path", "pathlib.PurePath", "pathlib.PurePosixPath"}:
            return _static_path(call, self.resolver) is not None
        if api == "open":
            return _write_open_call(call, self.resolver)
        if api in {"pandas.read_csv", "numpy.genfromtxt"} or api in _POSITIVE_APIS:
            return True
        if _accepted_selection_call(call, self.values, self.resolver):
            return True
        if api in _V2_R1_BUILTINS:
            return _v2_builtin_call(call, str(api), self.resolver)
        if api is not None and api.startswith("numpy."):
            return _v2_numpy_call(call, api, self.resolver)
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr in _V2_PANDAS_READONLY_METHODS
            and self._pandas_receiver(call.func.value)
            and not (
                call.func.attr in _GROUP_REDUCERS
                and _v2_grouped_receiver(call.func.value, self.values)
            )
        ):
            return _v2_pandas_call(call, call.func.attr, self.resolver)
        if _aggregation_call(call, api, self.values, self.resolver):
            return self._post_test_descriptive_aggregation(call, candidate)
        if api is not None and api.startswith("math."):
            return _v2_math_call(call, api)
        if api is not None and _v2_scipy_distribution_call(call, api):
            return True
        if api in _V2_EXCEPTION_NAMES:
            return not call.keywords and not any(isinstance(arg, ast.Starred) for arg in call.args)
        if api in {
            "os.path.join",
            "os.path.dirname",
            "os.path.abspath",
            "os.path.basename",
        }:
            return _v2_os_path_call(call, str(api), self.resolver)
        if isinstance(call.func, ast.Attribute):
            method = call.func.attr
            if method in _V2_STRING_METHODS and _v2_string_receiver(call.func.value, self.resolver):
                return not any(isinstance(arg, ast.Starred) for arg in call.args) and all(
                    keyword.arg is not None for keyword in call.keywords
                )
        return self._accepted_output_or_description(call, candidate)

    def _pandas_receiver(self, node: ast.expr) -> bool:
        if _loaded_names(node) & (set(self.values) | self.tainted_names):
            return True
        return isinstance(node, ast.Call) and bool(
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _V2_PANDAS_READONLY_METHODS
            and self._pandas_receiver(node.func.value)
        )

    def _post_test_descriptive_aggregation(self, call: ast.Call, candidate: _Test) -> bool:
        if any(
            call in value.call_origins and name in self.slice_names
            for name, value in self.values.items()
        ):
            return False
        return bool(
            _call_reaches_sink(call, self.sinks, self.values, self.assignments)
            or self._v22_helper_iterable_output(call)
            or any(
                self._inside_valid_descriptive_loop(origin)
                for value in self.values.values()
                if call in value.call_origins
                for origin in value.call_origins
            )
        )

    def _v22_helper_iterable_output(self, call: ast.Call) -> bool:
        loop_lines = {
            int(getattr(statement, "_sc_v22_iterable_prelude", -1))
            for statement in self.scope
            if int(getattr(statement, "_sc_v22_iterable_prelude", -1)) >= 0
            and self._contains(call, statement)
        }
        if not loop_lines:
            return False
        for loop in (item for item in self.scope if isinstance(item, ast.For)):
            if int(getattr(loop, "_sc_v22_helper_iterable", -2)) not in loop_lines:
                continue
            if loop.orelse or _store_names(loop.target) & self.slice_names:
                return False
            if not (
                isinstance(loop.iter, ast.Call)
                and isinstance(loop.iter.func, ast.Attribute)
                and loop.iter.func.attr in {"items", "iterrows"}
                and isinstance(loop.iter.func.value, ast.Name)
                and loop.iter.func.value.id in self.values
                and _v2_pandas_call(loop.iter, loop.iter.func.attr, self.resolver)
            ):
                return False
            if not all(
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and any(
                    sink.call is statement.value and sink.kind == "builtin_print"
                    for sink in self.sinks
                )
                for statement in loop.body
            ):
                return False
            return True
        return False

    def _admission_reason(self, candidate: _Test) -> str | None:
        for node in _walk_statements(self.scope):
            if isinstance(node, (ast.Break, ast.Continue, ast.Await, ast.Yield, ast.YieldFrom)):
                return "control-flow-body-unadmitted"
            if isinstance(node, ast.Try) and any(handler.type is None for handler in node.handlers):
                return "control-flow-body-unadmitted"
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for generator in node.generators:
                    if _loaded_names(generator.iter) & (
                        self.slice_names | self.tainted_names
                    ) and not (
                        isinstance(generator.iter, ast.Attribute)
                        and generator.iter.attr == "columns"
                        and isinstance(generator.iter.value, ast.Name)
                        and generator.iter.value.id in self.tainted_names
                    ):
                        return "admission-slice-reaches-operand"
        for call in sorted(
            (node for node in _walk_statements(self.scope) if isinstance(node, ast.Call)),
            key=_position,
        ):
            if _dependence_api(self.resolver.qualified(call.func)):
                continue
            if self._r1_readonly_call(call, candidate):
                continue
            if _aggregation_call(
                call,
                self.resolver.qualified(call.func),
                self.values,
                self.resolver,
            ):
                return "admission-call-off-list"
            if self._call_consumes_component(call):
                return "unregistered-component-consumer"
            return "admission-call-off-list"
        return _v2_read_reason(
            self.scope,
            self.values,
            self.resolver,
            self.csv_header,
            tuple(
                call
                for call in _walk_statements(self.scope)
                if isinstance(call, ast.Call) and self._r1_readonly_call(call, candidate)
            ),
            tuple(statement.value for statement, _ in self.deferred_auxiliary_stores),
        )

    def _accepted_output_or_description(self, call: ast.Call, candidate: _Test) -> bool:
        api = self.resolver.qualified(call.func)
        if api == "print":
            return True
        if any(
            value.kind == "descriptive_scalar" and call in value.call_origins
            for value in self.values.values()
        ):
            return True
        if (
            _inside_any(call, [sink.call for sink in self.sinks])
            and _p_derived_depth(
                call,
                candidate,
                self.resolver,
                self.assignments,
            )
            is not None
        ):
            return True
        if _straight_descriptive_call(call, candidate.call, self.values, self.sinks, self.resolver):
            return True
        if _statistic_derived_depth(call, candidate, self.resolver, self.assignments) is not None:
            return True
        if _descriptive_format_call(call, self.values, self.sinks, self.resolver):
            return True
        return False

    def _inside_valid_descriptive_loop(self, call: ast.Call) -> bool:
        for statement in self.scope:
            if (
                isinstance(statement, ast.For)
                and self._contains(call, statement)
                and _descriptive_loop(
                    statement,
                    self.values,
                    self.resolver,
                    self.slice_names,
                )
            ):
                return True
        return False

    def _result_sinks(self, test: _Test) -> list[_Sink]:
        return [
            sink
            for sink in self.sinks
            if sink.p_result_eligible
            and any(
                _p_derived_depth(payload, test, self.resolver, self.assignments) is not None
                for payload in sink.payloads
            )
        ]

    def _backward_slice_names(self, test: _Test) -> set[str]:
        pending = [test.left_name, test.right_name]
        result: set[str] = set()
        while pending:
            name = pending.pop()
            if name in result:
                continue
            result.add(name)
            expression = self.assignments.get(name)
            if expression is None:
                continue
            pending.extend(
                item.id
                for item in ast.walk(expression)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id in self.values
            )
        return result

    def _validate_loops(self) -> str | None:
        self.descriptive_loops = 0
        for loop in self.loops:
            bound = _store_names(loop.target)
            if bound & self.slice_names:
                return "loop-target-aliases-tracked"
            if any(
                isinstance(node, (ast.Break, ast.Continue, ast.Await, ast.Yield, ast.YieldFrom))
                for node in ast.walk(loop)
            ):
                return "control-flow-body-unadmitted"
            self.descriptive_loops += 1
        return None

    def _component_definition_depth(self, candidate: _Test) -> int:
        depths = [
            _component_expression_depth(call, self.values)
            for call in _walk_statements(self.scope)
            if isinstance(call, ast.Call)
            and call is not candidate.call
            and _reads_any(call, self.values)
        ]
        depths.extend(
            _component_expression_depth(payload, self.values) + 1
            for sink in self.sinks
            for payload in sink.payloads
            if _reads_any(payload, self.values)
        )
        return max(depths, default=1)

    def _reason(self, node: ast.AST, reason: str, rank: int) -> None:
        line, column, _, _ = _position(node)
        self.reasons.append(((line, column, rank), reason))

    def _first_reason(self, before_or_at: ast.AST | None = None) -> str | None:
        candidates = self.reasons
        if before_or_at is not None:
            limit = _position(before_or_at)[:2]
            candidates = [item for item in candidates if item[0][:2] <= limit]
        return min(candidates, default=((), None), key=lambda item: item[0])[1]

    def _relevant_helper_call_present(self) -> bool:
        return any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id not in self.resolver.imports
            and node.func.id not in _UNSHADOWED_BUILTINS
            for node in _walk_statements(self.scope)
        )

    @staticmethod
    def _contains(needle: ast.AST, haystack: ast.AST) -> bool:
        return any(item is needle for item in ast.walk(haystack))


def _normalize_contract_domain_loops(
    *,
    scope: tuple[ast.stmt, ...],
    resolver: _Resolver,
    group_values: tuple[str, str],
    helpers: Mapping[str, ast.FunctionDef],
) -> _Expansion:
    """Unroll only exact two-value contract-domain loops without executing source."""

    protected = (
        set(resolver.imports)
        | set(resolver.constants)
        | set(resolver.literals)
        | set(resolver.tuples)
        | set(resolver.file_parents)
        | set(helpers)
        | _UNSHADOWED_BUILTINS
    )
    comprehensions: list[ast.stmt] = []
    for statement in scope:
        normalized_comprehension = _normalize_contract_domain_dict_comprehension(
            statement,
            resolver=resolver,
            group_values=group_values,
            protected=protected,
        )
        comprehensions.extend(normalized_comprehension or (statement,))

    stores_outside_loop: defaultdict[str, int] = defaultdict(int)
    for statement in comprehensions:
        if isinstance(statement, ast.For):
            continue
        for name in _store_names(statement):
            stores_outside_loop[name] += 1

    normalized: list[ast.stmt] = []
    for statement in comprehensions:
        if not isinstance(statement, ast.For):
            normalized.append(statement)
            continue
        bindings = _contract_domain_loop_bindings(statement, resolver, group_values)
        if (
            bindings is None
            or not isinstance(statement.target, ast.Name)
            or statement.target.id in protected
            or stores_outside_loop[statement.target.id]
        ):
            normalized.append(statement)
            continue
        local_names = set().union(*(_store_names(item) for item in statement.body))
        local_names.discard(statement.target.id)
        for ordinal, binding in enumerate(bindings):
            rename = {
                name: f"__sc_loop_{statement.lineno}_{ordinal}_{name}"
                for name in sorted(local_names)
                if name not in protected
            }
            transformer = _ContractLoopBindingTransformer(
                target=statement.target.id,
                binding=binding,
                rename=rename,
            )
            for body_statement in statement.body:
                copied = transformer.visit(copy.deepcopy(body_statement))
                assert isinstance(copied, ast.stmt)
                if (
                    isinstance(copied, ast.Assign)
                    and len(copied.targets) == 1
                    and isinstance(copied.targets[0], ast.Subscript)
                    and isinstance(copied.targets[0].value, ast.Name)
                    and _literal_subscript_member(copied.targets[0].slice) == binding
                ):
                    copied.__dict__["_sc_v22_reconstruction_store"] = True
                for node in ast.walk(copied):
                    node.__dict__["_sc_v22_loop_binding_ordinal"] = ordinal
                normalized.append(copied)
    return _Expansion(tuple(normalized), None)


def _normalize_contract_domain_dict_comprehension(
    statement: ast.stmt,
    *,
    resolver: _Resolver,
    group_values: tuple[str, str],
    protected: set[str],
) -> tuple[ast.stmt, ...] | None:
    target: ast.Name | None = None
    expression: ast.expr | None = None
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        target = statement.targets[0]
        expression = statement.value
    elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        target = statement.target
        expression = statement.value
    if target is None or not isinstance(expression, ast.DictComp) or target.id in protected:
        return None
    if len(expression.generators) != 1:
        return None
    generator = expression.generators[0]
    if (
        generator.is_async
        or generator.ifs
        or not isinstance(generator.target, ast.Name)
        or not isinstance(expression.key, ast.Name)
        or expression.key.id != generator.target.id
        or generator.target.id in protected
    ):
        return None
    raw = resolver.sequence(generator.iter)
    if (
        raw is None
        or len(raw) != 2
        or not all(isinstance(item, str) for item in raw)
        or len(set(raw)) != 2
        or set(raw) != set(group_values)
    ):
        return None

    empty = ast.Assign(
        targets=[ast.Name(id=target.id, ctx=ast.Store())],
        value=ast.Dict(keys=[], values=[]),
    )
    ast.copy_location(empty, statement)
    result: list[ast.stmt] = [empty]
    for ordinal, value in enumerate(raw):
        assert isinstance(value, str)
        transformer = _ContractLoopBindingTransformer(
            target=generator.target.id,
            binding=value,
            rename={},
        )
        copied_value = transformer.visit(copy.deepcopy(expression.value))
        assert isinstance(copied_value, ast.expr)
        assignment = ast.Assign(
            targets=[
                ast.Subscript(
                    value=ast.Name(id=target.id, ctx=ast.Load()),
                    slice=ast.Constant(value=value),
                    ctx=ast.Store(),
                )
            ],
            value=copied_value,
        )
        ast.copy_location(assignment, statement)
        assignment.__dict__["_sc_v22_reconstruction_store"] = True
        for node in ast.walk(assignment):
            node.__dict__["_sc_v22_loop_binding_ordinal"] = ordinal
        result.append(assignment)
    return tuple(result)


def _contract_domain_loop_bindings(
    loop: ast.For,
    resolver: _Resolver,
    group_values: tuple[str, str],
) -> tuple[str, str] | None:
    if (
        loop.orelse
        or not isinstance(loop.target, ast.Name)
        or any(
            isinstance(
                node,
                (
                    ast.Break,
                    ast.Continue,
                    ast.Await,
                    ast.Yield,
                    ast.YieldFrom,
                    ast.Global,
                    ast.Nonlocal,
                ),
            )
            for node in ast.walk(loop)
        )
        or any(loop.target.id in _store_names(statement) for statement in loop.body)
    ):
        return None
    raw: tuple[object, ...] | None = None
    if isinstance(loop.iter, (ast.Tuple, ast.List)):
        resolved = tuple(resolver.string(item) for item in loop.iter.elts)
        if any(item is None for item in resolved):
            return None
        raw = resolved
    elif isinstance(loop.iter, ast.Name):
        raw = resolver.tuples.get(loop.iter.id)
    if (
        raw is None
        or len(raw) != 2
        or not all(isinstance(item, str) for item in raw)
        or len(set(raw)) != 2
        or set(raw) != set(group_values)
    ):
        return None
    return str(raw[0]), str(raw[1])


class _ContractLoopBindingTransformer(ast.NodeTransformer):
    def __init__(self, *, target: str, binding: str, rename: Mapping[str, str]) -> None:
        self.target = target
        self.binding = binding
        self.rename = rename

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Load) and node.id == self.target:
            return ast.copy_location(ast.Constant(value=self.binding), node)
        if node.id in self.rename:
            return ast.copy_location(
                ast.Name(id=self.rename[node.id], ctx=copy.deepcopy(node.ctx)),
                node,
            )
        return node


def _expand_relevant_helpers(
    *,
    scope: tuple[ast.stmt, ...],
    helpers: Mapping[str, ast.FunctionDef],
    resolver: _Resolver,
    group_values: tuple[str, str] = ("", ""),
) -> _Expansion:
    """Inline only the closed same-module helper grammar without executing source."""

    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in helpers
        for node in _walk_statements(scope)
    ):
        return _Expansion(None, "helper-callee-not-simple-name")
    expanded = list(scope)
    expanded_sites: set[tuple[int, int, str, int]] = set()
    while True:
        changed = False
        for index, statement in enumerate(expanded):
            site = _top_level_helper_site(statement, helpers)
            if site is None:
                continue
            call, target = site
            helper = helpers[call.func.id] if isinstance(call.func, ast.Name) else None
            if helper is None or not _helper_relevant(
                call=call,
                target=target,
                helper=helper,
                statements=expanded,
                statement_index=index,
                resolver=resolver,
            ):
                continue
            key = _helper_site_key(call, helper)
            if key in expanded_sites:
                return _Expansion(None, "helper-call-site-reentry-unsupported")
            depth = int(getattr(call, "_sc_inline_depth", 0)) + 1
            if depth > 2:
                return _Expansion(None, "helper-inlining-depth-exceeded")
            replacement, reason = _inline_helper_site(
                call=call,
                target=target,
                helper=helper,
                resolver=resolver,
                helpers=helpers,
                depth=depth,
                group_values=group_values,
            )
            if reason is not None:
                return _Expansion(None, reason)
            assert replacement is not None
            _propagate_reconstruction_marker(statement, replacement)
            expanded_sites.add(key)
            expanded[index : index + 1] = replacement
            changed = True
            break
        if not changed:
            nested = _nested_loop_helper_site(expanded, helpers, resolver)
            if nested is None:
                break
            container, index, call, target, iterable_owner = nested
            helper = helpers[call.func.id] if isinstance(call.func, ast.Name) else None
            assert helper is not None
            key = _helper_site_key(call, helper)
            if key in expanded_sites:
                return _Expansion(None, "helper-call-site-reentry-unsupported")
            depth = int(getattr(call, "_sc_inline_depth", 0)) + 1
            if depth > 2:
                return _Expansion(None, "helper-inlining-depth-exceeded")
            replacement_target = target
            if iterable_owner is not None:
                temporary = f"__sc_loop_iter_{call.lineno}_{call.col_offset}_{helper.lineno}"
                replacement_target = ast.Name(id=temporary, ctx=ast.Store())
            replacement, reason = _inline_helper_site(
                call=call,
                target=replacement_target,
                helper=helper,
                resolver=resolver,
                helpers=helpers,
                depth=depth,
                group_values=group_values,
            )
            if reason is not None:
                return _Expansion(None, reason)
            assert replacement is not None
            _propagate_reconstruction_marker(container[index], replacement)
            expanded_sites.add(key)
            if iterable_owner is None:
                container[index : index + 1] = replacement
            else:
                replacer = _IdentityNodeTransformer(
                    call,
                    ast.Name(
                        id=f"__sc_loop_iter_{call.lineno}_{call.col_offset}_{helper.lineno}",
                        ctx=ast.Load(),
                    ),
                )
                transformed = replacer.visit(iterable_owner.iter)
                assert isinstance(transformed, ast.expr)
                iterable_owner.iter = transformed
                iterable_owner.__dict__["_sc_v22_helper_iterable"] = iterable_owner.lineno
                for item in replacement:
                    item.__dict__["_sc_v22_iterable_prelude"] = iterable_owner.lineno
                container[index:index] = replacement
            changed = True
    return _Expansion(tuple(expanded), None)


def _propagate_reconstruction_marker(source: ast.stmt, replacement: Sequence[ast.stmt]) -> None:
    if not bool(getattr(source, "_sc_v22_reconstruction_store", False)):
        return
    source_target = source.targets[0] if isinstance(source, ast.Assign) else None
    if not isinstance(source_target, ast.Subscript):
        return
    for statement in reversed(replacement):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Subscript)
            and ast.dump(statement.targets[0], include_attributes=False)
            == ast.dump(source_target, include_attributes=False)
        ):
            statement.__dict__["_sc_v22_reconstruction_store"] = True
            return


def _helper_site_key(call: ast.Call, helper: ast.FunctionDef) -> tuple[int, int, str, int]:
    return (
        call.lineno,
        call.col_offset,
        helper.name,
        int(getattr(call, "_sc_v22_loop_binding_ordinal", -1)),
    )


def _nested_loop_helper_site(
    statements: list[ast.stmt],
    helpers: Mapping[str, ast.FunctionDef],
    resolver: _Resolver,
) -> tuple[list[ast.stmt], int, ast.Call, ast.expr | None, ast.For | None] | None:
    for index, statement in enumerate(statements):
        if not isinstance(statement, ast.For):
            continue
        iterable_calls = _loop_iterable_helper_calls(statement.iter, helpers)
        if len(iterable_calls) == 1:
            return statements, index, iterable_calls[0], None, statement
        if len(iterable_calls) > 1:
            return None
        for body_index, body_statement in enumerate(statement.body):
            site = _top_level_helper_site(body_statement, helpers)
            if site is None:
                continue
            call, target = site
            helper = helpers[call.func.id] if isinstance(call.func, ast.Name) else None
            if helper is not None and _helper_relevant(
                call=call,
                target=target,
                helper=helper,
                statements=statement.body,
                statement_index=body_index,
                resolver=resolver,
            ):
                return statement.body, body_index, call, target, None
        nested = _nested_loop_helper_site(statement.body, helpers, resolver)
        if nested is not None:
            return nested
    return None


def _loop_iterable_helper_calls(
    expression: ast.expr,
    helpers: Mapping[str, ast.FunctionDef],
) -> list[ast.Call]:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in helpers
    ):
        return [expression]
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and isinstance(expression.func.value, ast.Call)
        and isinstance(expression.func.value.func, ast.Name)
        and expression.func.value.func.id in helpers
    ):
        return [expression.func.value]
    return []


class _IdentityNodeTransformer(ast.NodeTransformer):
    def __init__(self, needle: ast.AST, replacement: ast.AST) -> None:
        self.needle = needle
        self.replacement = replacement

    def visit(self, node: ast.AST) -> ast.AST:
        if node is self.needle:
            return ast.copy_location(copy.deepcopy(self.replacement), node)
        return cast(ast.AST, super().visit(node))


def _top_level_helper_site(
    statement: ast.stmt, helpers: Mapping[str, ast.FunctionDef]
) -> tuple[ast.Call, ast.expr | None] | None:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id in helpers
    ):
        return statement.value, statement.targets[0]
    if (
        isinstance(statement, ast.AnnAssign)
        and statement.value is not None
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id in helpers
    ):
        return statement.value, statement.target
    if (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id in helpers
    ):
        return statement.value, None
    return None


def _helper_relevant(
    *,
    call: ast.Call,
    target: ast.expr | None,
    helper: ast.FunctionDef,
    statements: Sequence[ast.stmt],
    statement_index: int,
    resolver: _Resolver,
) -> bool:
    if _constant_only_print_helper(helper, resolver) and all(
        _closed_constant_expression(argument, resolver) for argument in call.args
    ):
        return False
    for node in _walk_helper_runtime(helper):
        if not isinstance(node, ast.Call):
            continue
        api = resolver.qualified(node.func)
        if (
            api in {"pandas.read_csv", "numpy.genfromtxt", "print"}
            or api in _POSITIVE_APIS
            or _dependence_api(api)
            or _aggregation_call(node, api, {}, resolver)
        ):
            return True
    if any(not _closed_constant_expression(argument, resolver) for argument in call.args):
        return True
    if target is not None:
        names = _store_names(target)
        return any(
            _reads_name(item, name) for item in statements[statement_index + 1 :] for name in names
        )
    return False


def _constant_only_print_helper(helper: ast.FunctionDef, resolver: _Resolver) -> bool:
    body = [item for item in helper.body if not _is_docstring(item)]
    if not body:
        return False
    parameters = {item.arg for item in helper.args.args}
    for statement in body:
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and resolver.qualified(statement.value.func) == "print"
        ):
            return False
        for node in ast.walk(statement.value):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id not in parameters
                and node.id not in resolver.constants
                and node.id not in resolver.tuples
                and node.id != "print"
            ):
                return False
    return True


def _inside_constant_only_helper_output(
    call: ast.Call,
    statements: Sequence[ast.stmt],
    helpers: Mapping[str, ast.FunctionDef],
    resolver: _Resolver,
) -> bool:
    return bool(
        isinstance(call.func, ast.Name)
        and (helper := helpers.get(call.func.id)) is not None
        and _constant_only_print_helper(helper, resolver)
        and any(
            call is site[0]
            for statement in statements
            if (site := _top_level_helper_site(statement, helpers))
        )
    )


def _closed_constant_expression(node: ast.expr, resolver: _Resolver) -> bool:
    return bool(
        isinstance(node, ast.Constant)
        or (
            isinstance(node, ast.Name)
            and (
                node.id in resolver.constants
                or node.id in resolver.literals
                or node.id in resolver.tuples
            )
        )
    )


def _walk_helper_runtime(helper: ast.FunctionDef) -> Iterable[ast.AST]:
    """Walk only executable helper statements, excluding annotation subtrees."""

    for statement in helper.body:
        yield from ast.walk(statement)


def _inline_helper_site(
    *,
    call: ast.Call,
    target: ast.expr | None,
    helper: ast.FunctionDef,
    resolver: _Resolver,
    helpers: Mapping[str, ast.FunctionDef],
    depth: int,
    group_values: tuple[str, str],
) -> tuple[list[ast.stmt] | None, str | None]:
    args = helper.args
    if args.posonlyargs or args.kwonlyargs or helper.type_comment is not None:
        return None, "helper-parameter-shape-unsupported"
    if args.vararg is not None or args.kwarg is not None or args.kw_defaults:
        return None, "helper-variadic-parameter-unsupported"
    parameter_names = [item.arg for item in args.args]
    if _helper_call_cycle(helper.name, helpers):
        return None, "helper-recursion-unsupported"
    if any(
        name in resolver.imports or name in resolver.file_parents or name in _UNSHADOWED_BUILTINS
        for name in parameter_names
    ):
        return None, "helper-parameter-shape-unsupported"
    defaults: dict[str, ast.expr] = {}
    default_start = len(parameter_names) - len(args.defaults)
    for name, default in zip(parameter_names[default_start:], args.defaults, strict=True):
        if not _closed_constant_expression(default, resolver):
            return None, "helper-parameter-default-unsupported"
        defaults[name] = default
    if helper.decorator_list or any(
        isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom))
        for node in _walk_helper_runtime(helper)
    ):
        return None, "helper-async-decorator-or-yield-unsupported"
    if any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in _walk_helper_runtime(helper)):
        return None, "helper-global-nonlocal-unsupported"
    if any(
        isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Lambda)) and node is not helper
        for node in _walk_helper_runtime(helper)
    ):
        return None, "helper-closure-or-nested-definition-unsupported"
    returns = [node for node in _walk_helper_runtime(helper) if isinstance(node, ast.Return)]
    if not returns and target is not None:
        return None, "helper-return-count-unsupported"
    if len(returns) > 1:
        return None, "helper-return-count-unsupported"
    final = helper.body[-1] if helper.body else None
    if returns and (final is not returns[0] or returns[0].value is None):
        return None, "helper-return-position-unsupported"
    local_names = set(parameter_names)
    body_without_return = helper.body[:-1] if returns else helper.body
    for statement in body_without_return:
        local_names.update(_store_names(statement))
    module_names = (
        set(resolver.imports)
        | set(resolver.constants)
        | set(resolver.literals)
        | set(resolver.tuples)
        | set(resolver.file_parents)
        | _UNSHADOWED_BUILTINS
        | _V2_EXCEPTION_NAMES
        | set(helpers)
        | {"__file__"}
    )
    for node in _walk_helper_runtime(helper):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id not in local_names
            and node.id not in module_names
        ):
            return None, "helper-free-name-unbound"
    bound, reason = _bind_helper_arguments(call, parameter_names, defaults)
    if reason is not None:
        return None, reason
    assert bound is not None
    binding = int(getattr(call, "_sc_v22_loop_binding_ordinal", -1))
    prefix = f"__sc_inline_{call.lineno}_{call.col_offset}_{helper.lineno}_{binding}_"
    rename = {name: prefix + name for name in local_names}
    transformer = _InlineNameTransformer(rename)
    replacement: list[ast.stmt] = []
    for name in parameter_names:
        value = copy.deepcopy(bound[name])
        assignment = ast.Assign(
            targets=[ast.Name(id=rename[name], ctx=ast.Store())],
            value=value,
        )
        ast.copy_location(assignment, call)
        replacement.append(assignment)
    for statement in body_without_return:
        if _is_docstring(statement):
            continue
        copied = transformer.visit(copy.deepcopy(statement))
        assert isinstance(copied, ast.stmt)
        _mark_inline_depth(copied, depth)
        replacement.append(copied)
    returned: ast.expr | None = None
    if returns:
        assert returns[0].value is not None
        transformed = transformer.visit(copy.deepcopy(returns[0].value))
        assert isinstance(transformed, ast.expr)
        returned = transformed
    if target is not None and returned is not None:
        assignment = ast.Assign(targets=[copy.deepcopy(target)], value=returned)
        ast.copy_location(assignment, call)
        _mark_inline_depth(assignment, depth)
        assignment.__dict__["_sc_v2_return_root"] = True
        replacement.append(assignment)
    elif (
        target is None
        and returned is not None
        and any(isinstance(item, ast.Call) for item in ast.walk(returned))
    ):
        expression = ast.Expr(value=returned)
        ast.copy_location(expression, call)
        _mark_inline_depth(expression, depth)
        replacement.append(expression)
    if binding >= 0:
        for statement in replacement:
            for node in ast.walk(statement):
                node.__dict__["_sc_v22_loop_binding_ordinal"] = binding
    return replacement, None


def _helper_call_cycle(start: str, helpers: Mapping[str, ast.FunctionDef]) -> bool:
    pending: list[tuple[str, tuple[str, ...]]] = [(start, ())]
    while pending:
        name, ancestry = pending.pop()
        if name in ancestry:
            return True
        helper = helpers.get(name)
        if helper is None:
            continue
        callees = {
            node.func.id
            for node in _walk_helper_runtime(helper)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in helpers
        }
        pending.extend((callee, (*ancestry, name)) for callee in callees)
    return False


def _helper_return_expression_supported(
    node: ast.expr, local_names: set[str], resolver: _Resolver
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in local_names
    if isinstance(node, ast.Call):
        api = resolver.qualified(node.func)
        return api in {"pandas.read_csv", "numpy.genfromtxt"} or api in _POSITIVE_APIS
    if isinstance(node, ast.Subscript):
        return any(isinstance(item, ast.Name) and item.id in local_names for item in ast.walk(node))
    return False


def _x5_return_candidate(node: ast.expr, local_names: set[str], resolver: _Resolver) -> bool:
    if isinstance(node, (ast.Dict, ast.Tuple, ast.List, ast.BinOp, ast.UnaryOp)):
        return True
    if _x3_count_attribute_shape(node):
        return True
    if isinstance(node, ast.Call):
        api = resolver.qualified(node.func)
        return api not in {"pandas.read_csv", "numpy.genfromtxt"} and api not in _POSITIVE_APIS
    return False


def _x5_return_expression_supported(
    node: ast.expr,
    body: Sequence[ast.stmt],
    parameters: set[str],
    resolver: _Resolver,
    group_values: tuple[str, str],
) -> bool:
    assignments: dict[str, ast.expr] = {}
    duplicates: set[str] = set()
    for statement in body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        bound: list[tuple[str, ast.expr]] = []
        if isinstance(target, ast.Name):
            bound.append((target.id, statement.value))
        elif (
            isinstance(target, (ast.Tuple, ast.List))
            and isinstance(statement.value, ast.Tuple)
            and 1 <= len(target.elts) <= 16
            and len(target.elts) == len(statement.value.elts)
            and all(isinstance(item, ast.Name) for item in target.elts)
            and not any(isinstance(item, ast.Starred) for item in statement.value.elts)
        ):
            bound.extend(
                (target_item.id, value_item)
                for target_item, value_item in zip(target.elts, statement.value.elts, strict=True)
                if isinstance(target_item, ast.Name)
            )
        for name, expression in bound:
            if name in assignments:
                duplicates.add(name)
            assignments[name] = expression
    for name in duplicates:
        assignments.pop(name, None)

    def selection_name(name: str, pending: frozenset[str] = frozenset()) -> bool:
        if name in parameters:
            return True
        if name in pending:
            return False
        expression = assignments.get(name)
        if expression is None:
            return False
        if isinstance(expression, ast.Name):
            return selection_name(expression.id, pending | {name})
        loaded = {
            item.id
            for item in ast.walk(expression)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        }
        return any(selection_name(item, pending | {name}) for item in loaded)

    def descriptive_shape(expression: ast.expr) -> bool:
        if _x3_count_attribute_shape(expression):
            receiver = _x3_count_attribute_receiver_name(expression)
            return receiver is not None and selection_name(receiver)
        if not _x3_reduction_shape(expression, resolver):
            return False
        receiver = _x3_reduction_receiver_name(expression, resolver)
        return receiver is not None and selection_name(receiver)

    def descriptive_name(name: str, pending: frozenset[str] = frozenset()) -> bool:
        if name in pending or name in parameters:
            return False
        expression = assignments.get(name)
        if expression is None:
            return False
        if descriptive_shape(expression):
            return True
        if isinstance(expression, ast.Name):
            return descriptive_name(expression.id, pending | {name})
        valid, contains_descriptive = descriptive_arithmetic(
            expression, pending | {name}, allow_wrapper=True
        )
        return valid and contains_descriptive

    def descriptive_arithmetic(
        expression: ast.expr,
        pending: frozenset[str] = frozenset(),
        *,
        allow_wrapper: bool,
    ) -> tuple[bool, bool]:
        if _finite_numeric_constant(expression):
            return True, False
        if descriptive_shape(expression):
            return True, True
        if isinstance(expression, ast.Name):
            descriptive = descriptive_name(expression.id, pending)
            return descriptive, descriptive
        if (
            allow_wrapper
            and isinstance(expression, ast.Call)
            and resolver.qualified(expression.func) in {"int", "float"}
            and resolver.qualified(expression.func) not in resolver.builtins_shadowed
            and len(expression.args) == 1
            and not expression.keywords
        ):
            return descriptive_arithmetic(expression.args[0], pending, allow_wrapper=False)
        if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, (ast.UAdd, ast.USub)):
            return descriptive_arithmetic(expression.operand, pending, allow_wrapper=allow_wrapper)
        if isinstance(expression, ast.BinOp) and isinstance(
            expression.op,
            (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow),
        ):
            left_valid, left_descriptive = descriptive_arithmetic(
                expression.left, pending, allow_wrapper=allow_wrapper
            )
            right_valid, right_descriptive = descriptive_arithmetic(
                expression.right, pending, allow_wrapper=allow_wrapper
            )
            return left_valid and right_valid, left_descriptive or right_descriptive
        return False, False

    def element(expression: ast.expr) -> bool:
        if isinstance(expression, ast.Constant):
            return True
        if isinstance(expression, ast.Name):
            return bool(
                descriptive_name(expression.id)
                or resolver.constants.get(expression.id) in group_values
            )
        valid, contains_descriptive = descriptive_arithmetic(expression, allow_wrapper=True)
        return valid and contains_descriptive

    if isinstance(node, ast.Name):
        return descriptive_name(node.id)
    if isinstance(node, ast.Dict):
        if not (1 <= len(node.keys) <= 16) or any(key is None for key in node.keys):
            return False
        keys = [_literal_container_key(key) for key in node.keys if key is not None]
        return bool(
            all(key is not None for key in keys)
            and len(set(keys)) == len(keys)
            and all(element(value) for value in node.values)
        )
    if isinstance(node, (ast.Tuple, ast.List)):
        return bool(
            1 <= len(node.elts) <= 16
            and not any(isinstance(item, ast.Starred) for item in node.elts)
            and all(element(item) for item in node.elts)
        )
    valid, contains_descriptive = descriptive_arithmetic(node, allow_wrapper=True)
    return valid and contains_descriptive


def _x3_reduction_shape(expression: ast.expr, resolver: _Resolver) -> bool:
    reduction = expression
    if (
        isinstance(expression, ast.Call)
        and resolver.qualified(expression.func) == "round"
        and "round" not in resolver.builtins_shadowed
        and len(expression.args) in {1, 2}
        and not expression.keywords
    ):
        if len(expression.args) == 2 and not (
            isinstance(expression.args[1], ast.Constant)
            and isinstance(expression.args[1].value, int)
            and not isinstance(expression.args[1].value, bool)
        ):
            return False
        reduction = expression.args[0]
    if not isinstance(reduction, ast.Call):
        return False
    api = resolver.qualified(reduction.func)
    if api in {"len", "sum", "min", "max"}:
        return bool(
            api not in resolver.builtins_shadowed
            and len(reduction.args) == 1
            and not reduction.keywords
            and isinstance(reduction.args[0], ast.Name)
        )
    if not (
        isinstance(reduction.func, ast.Attribute)
        and isinstance(reduction.func.value, ast.Name)
        and reduction.func.attr in _X3_METHOD_REDUCTIONS
    ):
        return False
    if reduction.func.attr in {"std", "var"}:
        return bool(
            not reduction.args
            and (
                not reduction.keywords
                or (
                    len(reduction.keywords) == 1
                    and reduction.keywords[0].arg == "ddof"
                    and isinstance(reduction.keywords[0].value, ast.Constant)
                    and reduction.keywords[0].value.value == 1
                )
            )
        )
    return not reduction.args and not reduction.keywords


def _x3_count_attribute_shape(expression: ast.expr) -> bool:
    return bool(
        (
            isinstance(expression, ast.Attribute)
            and expression.attr == "size"
            and isinstance(expression.value, ast.Name)
        )
        or (
            isinstance(expression, ast.Subscript)
            and isinstance(expression.value, ast.Attribute)
            and expression.value.attr == "shape"
            and isinstance(expression.value.value, ast.Name)
            and isinstance(expression.slice, ast.Constant)
            and expression.slice.value == 0
            and not isinstance(expression.slice.value, bool)
        )
    )


def _x3_count_attribute_receiver_name(expression: ast.expr) -> str | None:
    if not _x3_count_attribute_shape(expression):
        return None
    if isinstance(expression, ast.Attribute):
        return expression.value.id if isinstance(expression.value, ast.Name) else None
    assert isinstance(expression, ast.Subscript)
    attribute = expression.value
    assert isinstance(attribute, ast.Attribute)
    return attribute.value.id if isinstance(attribute.value, ast.Name) else None


def _x5_output_use_graph(
    statements: Sequence[ast.stmt],
    resolver: _Resolver,
    group_values: tuple[str, str],
) -> bool:
    roots = {
        statement.targets[0].id
        for statement in statements
        if bool(getattr(statement, "_sc_x5_return_root", False))
        and isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }
    marked = [
        statement
        for statement in statements
        if bool(getattr(statement, "_sc_x5_return_root", False))
    ]
    if not marked:
        return True
    if len(roots) != len(marked):
        return False
    store_counts: defaultdict[str, int] = defaultdict(int)
    for statement in statements:
        for node in ast.walk(statement):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                store_counts[node.id] += 1
    active: set[str] = set()
    consumed: set[str] = set()
    for statement in statements:
        if bool(getattr(statement, "_sc_x5_return_root", False)):
            assert isinstance(statement, ast.Assign)
            assert isinstance(statement.targets[0], ast.Name)
            active.add(statement.targets[0].id)
            continue
        if _loaded_names(statement) & (roots - active):
            return False
        loaded = _loaded_names(statement) & active
        if not loaded:
            continue
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id not in active
            and store_counts[statement.targets[0].id] == 1
            and _x5_graph_expression(statement.value, active, resolver)
        ):
            consumed.update(loaded)
            active.add(statement.targets[0].id)
            continue
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _x5_print_terminal(statement.value, active, resolver, group_values)
        ):
            consumed.update(loaded)
            continue
        return False
    return bool(roots.issubset(consumed) and active.issubset(consumed))


def _x5_graph_expression(expression: ast.expr, active: set[str], resolver: _Resolver) -> bool:
    if _finite_numeric_constant(expression):
        return True
    if isinstance(expression, ast.Name):
        return expression.id in active
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id in active
    ):
        return _literal_subscript_member(expression.slice) is not None
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, (ast.UAdd, ast.USub)):
        return _x5_graph_expression(expression.operand, active, resolver)
    if isinstance(expression, ast.BinOp) and isinstance(
        expression.op,
        (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow),
    ):
        return _x5_graph_expression(expression.left, active, resolver) and _x5_graph_expression(
            expression.right, active, resolver
        )
    return False


def _x5_print_terminal(
    call: ast.Call,
    active: set[str],
    resolver: _Resolver,
    group_values: tuple[str, str],
) -> bool:
    if (
        resolver.qualified(call.func) != "print"
        or "print" in resolver.builtins_shadowed
        or call.keywords
    ):
        return False
    return all(
        _x5_print_payload(argument, active, resolver, group_values) for argument in call.args
    )


def _x5_print_payload(
    expression: ast.expr,
    active: set[str],
    resolver: _Resolver,
    group_values: tuple[str, str],
) -> bool:
    if not (_loaded_names(expression) & active):
        return _closed_constant_expression(expression, resolver)
    if _x5_graph_expression(expression, active, resolver):
        return True
    if (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Mod)
        and isinstance(expression.left, ast.Constant)
        and isinstance(expression.left.value, str)
    ):
        operands = (
            expression.right.elts if isinstance(expression.right, ast.Tuple) else [expression.right]
        )
        return bool(
            operands
            and all(_x5_terminal_operand(item, active, resolver, group_values) for item in operands)
        )
    if isinstance(expression, ast.JoinedStr):
        return all(
            isinstance(item, ast.Constant)
            or (
                isinstance(item, ast.FormattedValue)
                and item.conversion == -1
                and (item.format_spec is None or _constant_fstring_format_spec(item.format_spec))
                and _x5_terminal_operand(item.value, active, resolver, group_values)
            )
            for item in expression.values
        )
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == "format"
        and isinstance(expression.func.value, ast.Constant)
        and isinstance(expression.func.value.value, str)
        and expression.args
        and not expression.keywords
    ):
        return all(
            _x5_terminal_operand(item, active, resolver, group_values) for item in expression.args
        )
    return False


def _x5_terminal_operand(
    expression: ast.expr,
    active: set[str],
    resolver: _Resolver,
    group_values: tuple[str, str],
) -> bool:
    if isinstance(expression, ast.Constant):
        return True
    if isinstance(expression, ast.Name) and resolver.constants.get(expression.id) in group_values:
        return True
    return _x5_graph_expression(expression, active, resolver)


def _constant_fstring_format_spec(expression: ast.expr) -> bool:
    return bool(
        isinstance(expression, ast.JoinedStr)
        and all(isinstance(item, ast.Constant) for item in expression.values)
    )


def _loaded_names(node: ast.AST) -> set[str]:
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    }


def _literal_container_key(node: ast.expr) -> str | int | None:
    if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
        return None
    return node.value if isinstance(node.value, (str, int)) else None


def _literal_subscript_member(node: ast.expr) -> str | int | None:
    return _literal_container_key(node)


def _assigned_target(statements: Sequence[ast.stmt], needle: ast.AST) -> ast.expr | None:
    for node in _walk_statements(statements):
        if isinstance(node, ast.Assign) and any(item is needle for item in ast.walk(node.value)):
            return node.targets[0] if len(node.targets) == 1 else None
        if (
            isinstance(node, ast.AnnAssign)
            and node.value is not None
            and any(item is needle for item in ast.walk(node.value))
        ):
            return node.target
    return None


def _v2_builtin_call(call: ast.Call, api: str, resolver: _Resolver) -> bool:
    if api in resolver.builtins_shadowed or any(isinstance(arg, ast.Starred) for arg in call.args):
        return False
    if any(keyword.arg is None for keyword in call.keywords):
        return False
    keyword_names = {str(keyword.arg) for keyword in call.keywords}
    if api == "print":
        return bool(
            keyword_names <= {"sep", "end"}
            and all(
                isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str)
                for keyword in call.keywords
            )
        )
    if api in {"len", "int", "float", "str", "abs", "sum", "any", "all", "repr", "bool"}:
        return len(call.args) == 1 and not call.keywords
    if api == "round":
        return bool(
            len(call.args) in {1, 2}
            and not call.keywords
            and (
                len(call.args) == 1
                or (
                    isinstance(call.args[1], ast.Constant)
                    and isinstance(call.args[1].value, int)
                    and not isinstance(call.args[1].value, bool)
                )
            )
        )
    if api == "isinstance":
        return len(call.args) == 2 and not call.keywords and _v2_literal_type(call.args[1])
    if api == "divmod":
        return len(call.args) == 2 and not call.keywords
    if api in {"min", "max"}:
        return bool(call.args and not call.keywords)
    if api == "sorted":
        return bool(
            len(call.args) == 1
            and keyword_names <= {"reverse"}
            and all(
                isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, bool)
                for keyword in call.keywords
            )
        )
    if api == "range":
        return bool(
            1 <= len(call.args) <= 3
            and not call.keywords
            and all(_closed_int(arg, resolver.literals) is not None for arg in call.args)
        )
    if api == "enumerate":
        return bool(
            len(call.args) in {1, 2}
            and not call.keywords
            and (len(call.args) == 1 or _closed_int(call.args[1], resolver.literals) is not None)
        )
    if api == "zip":
        return not call.keywords
    if api in {"list", "set", "tuple"}:
        return len(call.args) <= 1 and not call.keywords
    if api == "dict":
        return len(call.args) <= 1 and all(keyword.arg is not None for keyword in call.keywords)
    if api == "format":
        return bool(
            len(call.args) == 2
            and not call.keywords
            and isinstance(call.args[1], ast.Constant)
            and isinstance(call.args[1].value, str)
        )
    return False


def _v2_literal_type(node: ast.expr) -> bool:
    allowed = {"bool", "dict", "float", "int", "list", "set", "str", "tuple"}
    if isinstance(node, ast.Name):
        return node.id in allowed
    return bool(
        isinstance(node, ast.Tuple)
        and 1 <= len(node.elts) <= 16
        and all(isinstance(item, ast.Name) and item.id in allowed for item in node.elts)
    )


def _v2_math_call(call: ast.Call, api: str) -> bool:
    parts = api.split(".")
    return bool(
        len(parts) == 2
        and parts[0] == "math"
        and parts[1]
        and not parts[1].startswith("_")
        and not any(isinstance(arg, ast.Starred) for arg in call.args)
        and all(keyword.arg is not None for keyword in call.keywords)
    )


def _v2_numpy_call(call: ast.Call, api: str, resolver: _Resolver) -> bool:
    if not api.startswith("numpy.") or api.count(".") != 1:
        return False
    name = api.split(".", 1)[1]
    if any(isinstance(arg, ast.Starred) for arg in call.args) or any(
        keyword.arg is None for keyword in call.keywords
    ):
        return False
    keyword_names = {str(keyword.arg) for keyword in call.keywords}
    if keyword_names & {"out", "where", "casting", "order", "subok", "signature", "extobj"}:
        return False
    if name in _V2_NUMPY_ELEMENTWISE:
        arity = 2 if name in {"power", "minimum", "maximum"} else 3 if name == "clip" else 1
        max_arity = arity + (1 if name in {"round", "around"} else 0)
        return bool(
            arity <= len(call.args) <= max_arity
            and not call.keywords
            and (
                len(call.args) == arity
                or (
                    isinstance(call.args[-1], ast.Constant)
                    and isinstance(call.args[-1].value, int)
                    and not isinstance(call.args[-1].value, bool)
                )
            )
        )
    if name in _V2_NUMPY_REDUCERS:
        if name in {"percentile", "nanpercentile", "quantile", "nanquantile"}:
            positional_limit = 3
        elif name in {"median", "nanmedian"}:
            positional_limit = 2
        else:
            positional_limit = 2
        if not (1 <= len(call.args) <= positional_limit):
            return False
        if name in {
            "percentile",
            "nanpercentile",
            "quantile",
            "nanquantile",
            "median",
            "nanmedian",
        } and ("overwrite_input" in keyword_names or len(call.args) > positional_limit):
            return False
        allowed = {"axis", "ddof", "dtype", "keepdims", "initial"}
        if name in {"percentile", "nanpercentile", "quantile", "nanquantile"}:
            allowed |= {"method", "interpolation"}
        return keyword_names <= allowed
    if name in _V2_NUMPY_CONSTRUCTORS:
        if name in {"array", "asarray"}:
            return bool(1 <= len(call.args) <= 2 and keyword_names <= {"dtype"})
        if name == "arange":
            return bool(1 <= len(call.args) <= 3 and keyword_names <= {"dtype"})
        if name == "linspace":
            return bool(
                2 <= len(call.args) <= 3
                and keyword_names <= {"num", "dtype", "endpoint", "retstep"}
            )
        return bool(
            name == "concatenate" and len(call.args) in {1, 2} and keyword_names <= {"axis"}
        )
    return False


def _v2_scipy_distribution_call(call: ast.Call, api: str) -> bool:
    parts = api.split(".")
    return bool(
        len(parts) == 4
        and parts[:2] == ["scipy", "stats"]
        and parts[2]
        and not parts[2].startswith("_")
        and parts[3] in {"ppf", "cdf", "sf", "isf"}
        and not any(isinstance(arg, ast.Starred) for arg in call.args)
        and all(keyword.arg is not None for keyword in call.keywords)
    )


def _v2_os_path_call(call: ast.Call, api: str, resolver: _Resolver) -> bool:
    expected = 2 if api == "os.path.join" else 1
    return bool(
        len(call.args) == expected
        and not call.keywords
        and all(
            (isinstance(arg, ast.Name) and arg.id == "__file__") or resolver.string(arg) is not None
            for arg in call.args
        )
    )


def _closed_dtype(node: ast.expr, resolver: _Resolver) -> bool:
    if isinstance(node, ast.Name) and node.id in {"bool", "float", "int", "str"}:
        return node.id not in resolver.builtins_shadowed
    value = resolver.string(node)
    return bool(value is not None and "\x00" not in value and len(value.encode("utf-8")) <= 64)


def _selection_preserving_to_numpy_shape(call: ast.Call, resolver: _Resolver) -> bool:
    if any(isinstance(argument, ast.Starred) for argument in call.args) or any(
        keyword.arg is None for keyword in call.keywords
    ):
        return False
    if not call.args and not call.keywords:
        return True
    if len(call.args) == 1 and not call.keywords:
        return _closed_dtype(call.args[0], resolver)
    return bool(
        not call.args
        and len(call.keywords) == 1
        and call.keywords[0].arg == "dtype"
        and _closed_dtype(call.keywords[0].value, resolver)
    )


def _v2_pandas_call(call: ast.Call, method: str, resolver: _Resolver) -> bool:
    if any(isinstance(arg, ast.Starred) for arg in call.args) or any(
        keyword.arg is None for keyword in call.keywords
    ):
        return False
    keywords = {str(item.arg): item.value for item in call.keywords}
    if "inplace" in keywords:
        return False
    if method in {"std", "var", "sem"}:
        return bool(
            not call.args
            and (
                not keywords
                or (
                    set(keywords) == {"ddof"}
                    and isinstance(keywords["ddof"], ast.Constant)
                    and keywords["ddof"].value in {0, 1}
                )
            )
        )
    if method == "round":
        return bool(len(call.args) <= 1 and not keywords)
    if method == "head":
        return bool(len(call.args) <= 1 and not keywords)
    if method == "to_string":
        return bool(not call.args and set(keywords) <= {"index"})
    if method == "value_counts":
        return bool(not call.args and set(keywords) <= {"normalize", "sort", "ascending", "dropna"})
    if method == "quantile":
        return bool(len(call.args) <= 1 and not keywords)
    if method == "reset_index":
        return bool(not call.args and set(keywords) <= {"drop", "names"})
    if method == "sort_values":
        return bool(len(call.args) == 1 and set(keywords) <= {"ascending", "na_position"})
    if method == "drop_duplicates":
        return bool(len(call.args) <= 1 and set(keywords) <= {"keep"})
    if method == "reindex":
        selector: ast.expr | None = None
        if len(call.args) == 1 and not keywords:
            selector = call.args[0]
        elif not call.args and set(keywords) == {"index"}:
            selector = keywords["index"]
        return selector is not None and _v2_reindex_selector(selector, resolver)
    if method == "unstack":
        if not call.args and not keywords:
            return True
        level: ast.expr | None = None
        if len(call.args) == 1 and not keywords:
            level = call.args[0]
        elif not call.args and set(keywords) == {"level"}:
            level = keywords["level"]
        return level is not None and _v2_literal_level(level)
    if method == "to_numpy":
        return _selection_preserving_to_numpy_shape(call, resolver)
    if method == "describe":
        return not call.args and not keywords
    if method in {
        "mean",
        "median",
        "min",
        "max",
        "sum",
        "count",
        "nunique",
        "any",
        "all",
        "unique",
        "isna",
        "notna",
        "items",
        "iterrows",
        "tolist",
        "duplicated",
    }:
        return not call.args and not keywords
    return False


def _v2_reindex_selector(node: ast.expr, resolver: _Resolver) -> bool:
    if isinstance(node, (ast.List, ast.Tuple)):
        return bool(
            len(node.elts) <= 16
            and all(
                isinstance(item, ast.Constant)
                and (item.value is None or isinstance(item.value, (str, int, float, bool)))
                for item in node.elts
            )
        )
    if isinstance(node, ast.Name):
        return node.id in resolver.tuples
    return bool(
        isinstance(node, ast.Call)
        and resolver.qualified(node.func) == "list"
        and "list" not in resolver.builtins_shadowed
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id in resolver.tuples
    )


def _v2_literal_level(node: ast.expr) -> bool:
    return bool(
        isinstance(node, ast.Constant)
        and (
            isinstance(node.value, str)
            or (isinstance(node.value, int) and not isinstance(node.value, bool))
        )
    )


def _v2_grouped_receiver(node: ast.expr, values: Mapping[str, _Value]) -> bool:
    if isinstance(node, ast.Name):
        value = values.get(node.id)
        return value is not None and value.kind in {"grouped", "resampler"}
    if isinstance(node, ast.Subscript):
        return _v2_grouped_receiver(node.value, values)
    if isinstance(node, ast.Attribute):
        return _v2_grouped_receiver(node.value, values)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr in {"groupby", "resample", "agg", "aggregate", "pivot_table"}:
            return True
        return _v2_grouped_receiver(node.func.value, values)
    return False


def _v2_string_receiver(node: ast.expr, resolver: _Resolver) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if isinstance(node, ast.Name) and resolver.string(node) is not None:
        return True
    if isinstance(node, ast.Call):
        api = resolver.qualified(node.func)
        return api == "str" or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _V2_STRING_METHODS
            and _v2_string_receiver(node.func.value, resolver)
        )
    return False


def _closed_int(node: ast.expr, literals: Mapping[str, int | float | bool]) -> int | None:
    value: object | None = None
    if isinstance(node, ast.Constant):
        value = node.value
    elif isinstance(node, ast.Name):
        value = literals.get(node.id)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _v2_read_reason(
    statements: Sequence[ast.stmt],
    values: Mapping[str, _Value],
    resolver: _Resolver,
    csv_header: Sequence[str],
    admitted_calls: Sequence[ast.Call],
    admitted_read_subtrees: Sequence[ast.AST] = (),
) -> str | None:
    for node in _walk_statements(statements):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if _inside_any(node, admitted_read_subtrees):
                continue
            if any(call.func is node for call in admitted_calls):
                continue
            if isinstance(node.parent if hasattr(node, "parent") else None, ast.Call):
                continue
            if node.attr in _V2_PANDAS_READONLY_PROPERTIES:
                continue
            if node.attr in {"name", "parent", "stem"} and _v2_path_receiver(node.value, resolver):
                continue
            if node.attr in {"loc", "iloc", "at", "pvalue", "statistic"}:
                continue
            if isinstance(node.value, ast.Name) and node.value.id in resolver.imports:
                continue
            if _loaded_names(node) & set(values):
                return "admission-call-off-list"
        if not isinstance(node, ast.Subscript) or not isinstance(node.ctx, ast.Load):
            continue
        if _inside_any(node, admitted_read_subtrees):
            continue
        if _inside_any(
            node,
            _member_value_nodes(values, {"selection", "identity"}),
        ):
            continue
        if _plain_column_read(node, values, resolver, csv_header) is not None:
            continue
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr in {"groupby", "drop_duplicates"}
            and (column := resolver.string(node.slice)) is not None
            and column in csv_header
        ):
            continue
        if (
            isinstance(node.value, ast.Name)
            and (result_value := values.get(node.value.id)) is not None
            and result_value.kind in {"test_result", "test_p_result", "test_statistic"}
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in {0, 1}
        ):
            continue
        if _nonreader_label_read(node, values, resolver) is not None:
            continue
        if (
            isinstance(node.value, ast.Attribute)
            and node.value.attr == "shape"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id in values
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, int)
            and not isinstance(node.slice.value, bool)
        ):
            continue
        if _resolved_member_read(node, values) is not None:
            continue
        if _literal_loop_label_read(node, statements, values, resolver):
            continue
        if _loaded_names(node) & set(values):
            return "admission-call-off-list"
    return None


def _member_value_nodes(values: Mapping[str, _Value], kinds: set[str]) -> list[ast.AST]:
    result: list[ast.AST] = []
    pending = list(values.values())
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if value.kind in kinds:
            result.append(value.node)
        pending.extend(member for _, member in value.members)
    return result


def _resolved_member_read(
    node: ast.Subscript,
    values: Mapping[str, _Value],
) -> _Value | None:
    member = _literal_subscript_member(node.slice)
    if member is None:
        return None
    container: _Value | None = None
    if isinstance(node.value, ast.Name):
        container = values.get(node.value.id)
    elif isinstance(node.value, ast.Subscript):
        container = _resolved_member_read(node.value, values)
    if container is None:
        return None
    mapped = dict(container.members).get(member)
    if mapped is not None:
        return mapped
    if container.kind == "descriptive_container" and member in container.descriptive_members:
        return container
    return None


def _literal_loop_label_read(
    node: ast.Subscript,
    statements: Sequence[ast.stmt],
    values: Mapping[str, _Value],
    resolver: _Resolver,
) -> bool:
    if not (
        isinstance(node.value, ast.Attribute)
        and node.value.attr in {"loc", "at"}
        and isinstance(node.value.value, ast.Name)
        and values.get(node.value.value.id, _Value("", node)).aggregated
        and isinstance(node.slice, ast.Name)
    ):
        return False
    return any(
        node.slice.id in _store_names(loop.target)
        and isinstance(loop.iter, (ast.Tuple, ast.List))
        and all(resolver.string(item) is not None for item in loop.iter.elts)
        for loop in (item for item in _walk_statements(statements) if isinstance(item, ast.For))
    )


def _v2_path_receiver(node: ast.expr, resolver: _Resolver) -> bool:
    if isinstance(node, ast.Name):
        return node.id in resolver.constants or node.id in resolver.file_parents
    if (
        isinstance(node, ast.Call)
        and resolver.qualified(node.func) == "pathlib.Path"
        and len(node.args) == 1
        and not node.keywords
    ):
        return resolver.string(node.args[0]) is not None or (
            isinstance(node.args[0], ast.Name) and node.args[0].id == "__file__"
        )
    return False


def _v2_resampling_sibling(
    statements: Sequence[ast.stmt],
    values: Mapping[str, _Value],
    resolver: _Resolver,
    sinks: Sequence[_Sink],
    assignments: Mapping[str, ast.expr],
) -> ast.AST | None:
    tracked = {
        name
        for name, value in values.items()
        if value.root is not None
        or value.kind in {"reader", "selection", "identity", "reconstruction_container"}
    }
    tracked = _guard_name_closure(statements, tracked)
    generated: list[tuple[ast.AST, set[str]]] = []
    for node in _walk_statements(statements):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            generators = node.generators
            if len(generators) != 1 or generators[0].is_async:
                continue
            cardinality = _v2_iterator_cardinality(generators[0].iter, resolver)
            if cardinality is None or cardinality < _V2_RESAMPLING_MIN_TRIPS:
                continue
            payloads: list[ast.AST]
            if isinstance(node, ast.DictComp):
                payloads = [node.key, node.value, *generators[0].ifs]
            else:
                payloads = [node.elt, *generators[0].ifs]
            if not any(_loaded_names(item) & tracked for item in payloads):
                continue
            target = _assigned_target(statements, node)
            generated.append((node, _guard_store_names(target) if target is not None else set()))
        elif isinstance(node, ast.For):
            cardinality = _v2_iterator_cardinality(node.iter, resolver)
            if cardinality is None or cardinality < _V2_RESAMPLING_MIN_TRIPS:
                continue
            if not any(_loaded_names(item) & tracked for item in node.body):
                continue
            outputs: set[str] = set()
            for item in ast.walk(node):
                if (
                    isinstance(item, ast.Call)
                    and isinstance(item.func, ast.Attribute)
                    and item.func.attr == "append"
                    and isinstance(item.func.value, ast.Name)
                ):
                    outputs.add(item.func.value.id)
                if isinstance(item, (ast.Assign, ast.AugAssign, ast.NamedExpr)):
                    targets = item.targets if isinstance(item, ast.Assign) else (item.target,)
                    for target in targets:
                        outputs.update(_guard_store_names(target))
            generated.append((node, outputs))
        elif isinstance(node, ast.Call):
            cardinality = _v2_random_draw_cardinality(node, resolver, assignments)
            if cardinality is None or cardinality < _V2_RESAMPLING_MIN_TRIPS:
                continue
            target = _assigned_target(statements, node)
            outputs = _guard_store_names(target) if target is not None else set()
            if outputs:
                generated.append((node, outputs))

    for origin, output_names in generated:
        if not output_names:
            continue
        derived = _guard_name_closure(statements, set(output_names))
        if isinstance(origin, ast.Call) and not any(
            _loaded_names(expression) & tracked and _loaded_names(expression) & derived
            for expression in assignments.values()
        ):
            continue
        for call in (item for item in _walk_statements(statements) if isinstance(item, ast.Call)):
            api = resolver.qualified(call.func)
            pandas_reducer = bool(
                isinstance(call.func, ast.Attribute)
                and call.func.attr in {"mean", "std", "quantile"}
            )
            if api not in _V2_RESAMPLING_REDUCERS and not pandas_reducer:
                continue
            if not (_loaded_names(call) & derived):
                continue
            if _call_reaches_sink(call, sinks, values) or any(
                any(item is call for item in ast.walk(payload))
                for sink in sinks
                for payload in sink.payloads
            ):
                return origin
            assigned = _assigned_target(statements, call)
            if assigned is not None:
                reduction_names = _guard_store_names(assigned)
                reduction_names = _guard_name_closure(statements, reduction_names)
                if any(
                    _loaded_names(payload) & reduction_names
                    for sink in sinks
                    for payload in sink.payloads
                ):
                    return origin
    return None


def _guard_store_names(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    result = _store_names(node)
    if isinstance(node, (ast.Subscript, ast.Attribute)):
        root = _root_name(node)
        if root is not None:
            result.add(root)
    return result


def _guard_name_closure(statements: Sequence[ast.stmt], seeds: set[str]) -> set[str]:
    """Follow guard-only name/member/destructuring edges in the fully inlined AST."""

    derived = set(seeds)
    changed = True
    while changed:
        changed = False
        for node in _walk_statements(statements):
            value: ast.AST | None = None
            targets: Sequence[ast.AST] = ()
            if isinstance(node, ast.Assign):
                value = node.value
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = (node.target,)
            elif isinstance(node, ast.NamedExpr):
                value = node.value
                targets = (node.target,)
            elif isinstance(node, ast.AugAssign):
                value = node.value
                targets = (node.target,)
            if value is None or not (_loaded_names(value) & derived):
                continue
            for target in targets:
                for name in _guard_store_names(target):
                    if name not in derived:
                        derived.add(name)
                        changed = True
        for loop in (node for node in _walk_statements(statements) if isinstance(node, ast.For)):
            if not (_loaded_names(loop.iter) & derived):
                continue
            for name in _guard_store_names(loop.target):
                if name not in derived:
                    derived.add(name)
                    changed = True
    return derived


def _v2_iterator_cardinality(node: ast.expr, resolver: _Resolver) -> int | None:
    if isinstance(node, (ast.Tuple, ast.List)):
        return len(node.elts)
    if not isinstance(node, ast.Call):
        return None
    api = resolver.qualified(node.func)
    if api not in {"range", "numpy.arange"} or node.keywords:
        return None
    values = [_closed_int(item, resolver.literals) for item in node.args]
    if not values or any(item is None for item in values):
        return None
    integers = [int(item) for item in values if item is not None]
    if len(integers) == 1:
        start, stop, step = 0, integers[0], 1
    elif len(integers) == 2:
        start, stop, step = integers[0], integers[1], 1
    elif len(integers) == 3:
        start, stop, step = integers
    else:
        return None
    if step != 1:
        return None
    return max(0, stop - start)


def _v2_random_draw_cardinality(
    call: ast.Call,
    resolver: _Resolver,
    assignments: Mapping[str, ast.expr],
) -> int | None:
    api = resolver.qualified(call.func)
    recognized = api in _V2_RANDOM_MODULE_DRAWS
    if (
        not recognized
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
    ):
        generator = assignments.get(call.func.value.id)
        recognized = bool(
            call.func.attr in _V2_RANDOM_GENERATOR_METHODS
            and isinstance(generator, ast.Call)
            and resolver.qualified(generator.func) == "numpy.random.default_rng"
            and len(generator.args) <= 1
            and not generator.keywords
        )
    if not recognized:
        return None
    size_node: ast.expr | None = None
    for keyword in call.keywords:
        if keyword.arg == "size":
            size_node = keyword.value
    if size_node is None:
        return None
    if isinstance(size_node, (ast.Tuple, ast.List)):
        dimensions = [_closed_int(item, resolver.literals) for item in size_node.elts]
        if not dimensions or any(item is None or item < 0 for item in dimensions):
            return None
        return math.prod(int(item) for item in dimensions if item is not None)
    value = _closed_int(size_node, resolver.literals)
    return value if value is not None and value >= 0 else None


def _value_at_node(value: _Value, node: ast.AST, depth: int) -> _Value:
    return _Value(
        value.kind,
        node,
        root=value.root,
        group_column=value.group_column,
        group_value=value.group_value,
        value_column=value.value_column,
        selection_kind=value.selection_kind,
        depth=max(depth, value.depth + 1),
        aggregated=value.aggregated,
        unknown=value.unknown,
        counter_node=value.counter_node,
        call_origins=value.call_origins,
        descriptive_members=value.descriptive_members,
        members=value.members,
    )


def _plain_column_read(
    node: ast.expr,
    values: Mapping[str, _Value],
    resolver: _Resolver,
    csv_header: Sequence[str],
) -> _Value | None:
    if not (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and isinstance(node.ctx, ast.Load)
    ):
        return None
    parent = values.get(node.value.id)
    column = resolver.string(node.slice)
    if parent is None or column is None or column not in csv_header:
        return None
    return _Value(
        "derived",
        node,
        root=parent.root,
        value_column=column,
        depth=parent.depth + 1,
        aggregated=parent.aggregated,
        unknown=parent.unknown,
        counter_node=parent.counter_node,
        call_origins=parent.call_origins,
    )


def _nonreader_label_read(
    node: ast.expr,
    values: Mapping[str, _Value],
    resolver: _Resolver,
) -> _Value | None:
    receiver: ast.expr | None = None
    label: ast.expr | None = None
    if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
        label = node.slice
        if isinstance(node.value, ast.Attribute) and node.value.attr in {"loc", "at"}:
            receiver = node.value.value
        elif isinstance(node.value, ast.Name):
            receiver = node.value
    if not isinstance(receiver, ast.Name) or label is None or resolver.string(label) is None:
        return None
    parent = values.get(receiver.id)
    if parent is None or not parent.aggregated:
        return None
    return _Value(
        "derived",
        node,
        root=parent.root,
        depth=parent.depth + 1,
        aggregated=True,
        unknown=parent.unknown,
        counter_node=parent.counter_node,
        call_origins=parent.call_origins,
    )


def _finite_numeric_constant(node: ast.expr) -> bool:
    return bool(
        isinstance(node, ast.Constant)
        and not isinstance(node.value, bool)
        and isinstance(node.value, (int, float))
        and (not isinstance(node.value, float) or math.isfinite(node.value))
    )


def _bind_helper_arguments(
    call: ast.Call,
    parameter_names: list[str],
    defaults: Mapping[str, ast.expr],
) -> tuple[dict[str, ast.expr] | None, str | None]:
    if any(isinstance(item, ast.Starred) for item in call.args) or any(
        item.arg is None for item in call.keywords
    ):
        return None, "helper-argument-binding-unsupported"
    if len(call.args) > len(parameter_names):
        return None, "helper-argument-binding-unsupported"
    bound = dict(zip(parameter_names, call.args, strict=False))
    for keyword in call.keywords:
        assert keyword.arg is not None
        if keyword.arg not in parameter_names or keyword.arg in bound:
            return None, "helper-argument-binding-unsupported"
        bound[keyword.arg] = keyword.value
    for name in parameter_names:
        if name not in bound:
            default = defaults.get(name)
            if default is None:
                return None, "helper-argument-binding-unsupported"
            bound[name] = default
    return bound, None


class _InlineNameTransformer(ast.NodeTransformer):
    def __init__(self, rename: Mapping[str, str]) -> None:
        self.rename = rename

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id not in self.rename:
            return node
        return ast.copy_location(
            ast.Name(id=self.rename[node.id], ctx=copy.deepcopy(node.ctx)),
            node,
        )


def _mark_inline_depth(node: ast.AST, depth: int) -> None:
    for item in ast.walk(node):
        item.__dict__["_sc_inline_depth"] = depth


def _bounded_parse(content: bytes) -> ast.Module:
    if len(content) > _SOURCE_BYTE_MAX or content.startswith(b"\xef\xbb\xbf") or b"\x00" in content:
        raise ValueError("source outside byte envelope")
    text = content.decode("utf-8", errors="strict")
    tree = ast.parse(text, filename="analysis.py", mode="exec", type_comments=True)
    if sum(1 for _ in ast.walk(tree)) > _AST_NODE_MAX:
        raise ValueError("source outside AST envelope")
    return tree


def _definition_shadows_builtin(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name in _UNSHADOWED_BUILTINS
        ):
            return True
        if isinstance(node, ast.arg) and node.arg in _UNSHADOWED_BUILTINS:
            return True
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if node.id in _UNSHADOWED_BUILTINS:
                return True
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                if bound in _UNSHADOWED_BUILTINS:
                    return True
    return False


def _dependence_api(api: str | None) -> bool:
    return bool(
        api in _DEPENDENCE_APIS
        or any(api.startswith(root + ".") for root in _DEPENDENCE_CLASS_APIS)
        if api is not None
        else False
    )


def _assignment_expressions(statements: Sequence[ast.stmt]) -> dict[str, ast.expr]:
    result: dict[str, ast.expr] = {}
    duplicates: set[str] = set()
    for node in _walk_statements(statements):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            name = node.targets[0].id
            if name in result:
                duplicates.add(name)
            result[name] = node.value
    for name in duplicates:
        result.pop(name, None)
    return result


def _registered_sinks(statements: Sequence[ast.stmt], resolver: _Resolver) -> tuple[_Sink, ...]:
    handle_scopes: dict[str, ast.With] = {}
    for node in _walk_statements(statements):
        if not isinstance(node, ast.With) or len(node.items) != 1 or node.type_comment is not None:
            continue
        item = node.items[0]
        if not isinstance(item.optional_vars, ast.Name):
            continue
        if _write_open_call(item.context_expr, resolver):
            handle_scopes[item.optional_vars.id] = node

    result: list[_Sink] = []
    for call in (node for node in _walk_statements(statements) if isinstance(node, ast.Call)):
        api = resolver.qualified(call.func)
        if _print_sink(call, api, resolver):
            result.append(_Sink(call, "builtin_print", tuple(call.args), True))
            continue
        if _path_write_text_sink(call, resolver):
            result.append(_Sink(call, "path_write_text_utf8", (call.args[0],), True))
            continue
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "write"
            and isinstance(call.func.value, ast.Name)
            and (scope := handle_scopes.get(call.func.value.id)) is not None
            and _inside_any(call, (scope,))
            and len(call.args) == 1
            and not call.keywords
        ):
            result.append(_Sink(call, "bounded_text_handle_write", (call.args[0],), True))
            continue
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "to_csv"
            and len(call.args) == 1
            and not call.keywords
            and _static_path(call.args[0], resolver) is not None
        ):
            result.append(_Sink(call, "pandas_to_csv_terminal", (call.func.value,), False))
            continue
        if (
            api == "numpy.savetxt"
            and len(call.args) == 2
            and not call.keywords
            and _static_path(call.args[0], resolver) is not None
        ):
            result.append(_Sink(call, "numpy_savetxt_terminal", (call.args[1],), False))
            continue
        if (
            api == "json.dump"
            and len(call.args) == 2
            and not call.keywords
            and isinstance(call.args[1], ast.Name)
            and (scope := handle_scopes.get(call.args[1].id)) is not None
            and _inside_any(call, (scope,))
        ):
            result.append(_Sink(call, "json_dump_terminal", (call.args[0],), False))
    return tuple(sorted(result, key=lambda item: _position(item.call)))


def _print_sink(call: ast.Call, api: str | None, resolver: _Resolver) -> bool:
    if api != "print" or "print" in resolver.builtins_shadowed:
        return False
    if any(isinstance(argument, ast.Starred) for argument in call.args):
        return False
    return all(
        keyword.arg in {"sep", "end"}
        and isinstance(keyword.value, ast.Constant)
        and isinstance(keyword.value.value, str)
        for keyword in call.keywords
    )


def _path_write_text_sink(call: ast.Call, resolver: _Resolver) -> bool:
    return bool(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "write_text"
        and _static_path(call.func.value, resolver) is not None
        and len(call.args) == 1
        and len(call.keywords) == 1
        and call.keywords[0].arg == "encoding"
        and isinstance(call.keywords[0].value, ast.Constant)
        and call.keywords[0].value.value == "utf-8"
    )


def _write_open_call(node: ast.expr, resolver: _Resolver) -> bool:
    if not isinstance(node, ast.Call):
        return False
    api = resolver.qualified(node.func)
    path: str | None = None
    mode: str | None = None
    if api == "open" and len(node.args) == 2:
        path = _static_path(node.args[0], resolver)
        mode = resolver.string(node.args[1])
    elif isinstance(node.func, ast.Attribute) and node.func.attr == "open" and len(node.args) == 1:
        path = _static_path(node.func.value, resolver)
        mode = resolver.string(node.args[0])
    if path is None or mode not in {"w", "wt"}:
        return False
    keywords = _literal_keywords(node.keywords)
    return bool(
        keywords is not None
        and keywords.get("encoding") == "utf-8"
        and set(keywords) in ({"encoding"}, {"encoding", "newline"})
        and ("newline" not in keywords or keywords["newline"] == "")
    )


def _p_derived_depth(
    node: ast.AST,
    test: _Test,
    resolver: _Resolver,
    assignments: Mapping[str, ast.expr],
    seen: frozenset[str] = frozenset(),
) -> int | None:
    member = _container_member_expression(node, assignments)
    if member is not None:
        depth = _p_derived_depth(member, test, resolver, assignments, seen)
        return depth + 1 if depth is not None else None
    if isinstance(node, ast.Name):
        if test.p_name is not None and node.id == test.p_name:
            return 1
        if node.id in seen or node.id == test.result_name:
            return None
        assigned = assignments.get(node.id)
        if assigned is None:
            return None
        depth = _p_derived_depth(assigned, test, resolver, assignments, seen | {node.id})
        return depth + 1 if depth is not None else None
    if test.result_name is not None:
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and _name_resolves_to(node.value.id, test.result_name, assignments)
            and node.attr == "pvalue"
        ):
            return 1
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and _name_resolves_to(node.value.id, test.result_name, assignments)
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == 1
        ):
            return 1
    if isinstance(node, ast.Attribute) and node.value is test.call and node.attr == "pvalue":
        return 1
    if isinstance(node, (ast.Dict, ast.Tuple, ast.List)):
        expressions = node.values if isinstance(node, ast.Dict) else node.elts
        depths = [
            depth
            for expression in expressions
            if (depth := _p_derived_depth(expression, test, resolver, assignments, seen))
            is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.FormattedValue):
        return _p_derived_depth(node.value, test, resolver, assignments, seen)
    if isinstance(node, ast.JoinedStr):
        depths = [
            depth
            for item in node.values
            if isinstance(item, ast.FormattedValue)
            if (depth := _p_derived_depth(item, test, resolver, assignments, seen)) is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.BinOp):
        if not (
            isinstance(node.op, ast.Mod)
            and isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
        ):
            return None
        return _p_derived_depth(node.right, test, resolver, assignments, seen)
    if isinstance(node, ast.Call):
        api = resolver.qualified(node.func)
        if api in {"str", "float"} and len(node.args) == 1 and not node.keywords:
            depth = _p_derived_depth(node.args[0], test, resolver, assignments, seen)
            return depth + 1 if depth is not None else None
        if api == "round" and not node.keywords and len(node.args) in {1, 2}:
            if len(node.args) == 2 and not (
                isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, int)
            ):
                return None
            depth = _p_derived_depth(node.args[0], test, resolver, assignments, seen)
            return depth + 1 if depth is not None else None
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
            and node.args
            and not node.keywords
        ):
            depths = [
                depth
                for argument in node.args
                if (depth := _p_derived_depth(argument, test, resolver, assignments, seen))
                is not None
            ]
            return max(depths, default=None)
    return None


def _statistic_derived_depth(
    node: ast.AST,
    test: _Test,
    resolver: _Resolver,
    assignments: Mapping[str, ast.expr],
    seen: frozenset[str] = frozenset(),
) -> int | None:
    member = _container_member_expression(node, assignments)
    if member is not None:
        depth = _statistic_derived_depth(member, test, resolver, assignments, seen)
        return depth + 1 if depth is not None else None
    if isinstance(node, ast.Name):
        if test.statistic_name is not None and node.id == test.statistic_name:
            return 1
        if node.id in seen or node.id == test.result_name:
            return None
        assigned = assignments.get(node.id)
        if assigned is None:
            return None
        depth = _statistic_derived_depth(assigned, test, resolver, assignments, seen | {node.id})
        return depth + 1 if depth is not None else None
    if test.result_name is not None:
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and _name_resolves_to(node.value.id, test.result_name, assignments)
            and node.attr == "statistic"
        ):
            return 1
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and _name_resolves_to(node.value.id, test.result_name, assignments)
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == 0
        ):
            return 1
    if isinstance(node, ast.Attribute) and node.value is test.call and node.attr == "statistic":
        return 1
    if isinstance(node, (ast.Dict, ast.Tuple, ast.List)):
        expressions = node.values if isinstance(node, ast.Dict) else node.elts
        depths = [
            depth
            for expression in expressions
            if (depth := _statistic_derived_depth(expression, test, resolver, assignments, seen))
            is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.FormattedValue):
        return _statistic_derived_depth(node.value, test, resolver, assignments, seen)
    if isinstance(node, ast.JoinedStr):
        depths = [
            depth
            for item in node.values
            if isinstance(item, ast.FormattedValue)
            if (depth := _statistic_derived_depth(item, test, resolver, assignments, seen))
            is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.BinOp):
        depths = [
            depth
            for child in (node.left, node.right)
            if (depth := _statistic_derived_depth(child, test, resolver, assignments, seen))
            is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.Call):
        api = resolver.qualified(node.func)
        if api in {"str", "float"} and len(node.args) == 1 and not node.keywords:
            depth = _statistic_derived_depth(node.args[0], test, resolver, assignments, seen)
            return depth + 1 if depth is not None else None
        if api == "round" and not node.keywords and len(node.args) in {1, 2}:
            if len(node.args) == 2 and not (
                isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, int)
            ):
                return None
            depth = _statistic_derived_depth(node.args[0], test, resolver, assignments, seen)
            return depth + 1 if depth is not None else None
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
            and node.args
            and not node.keywords
        ):
            depths = [
                depth
                for argument in node.args
                if (depth := _statistic_derived_depth(argument, test, resolver, assignments, seen))
                is not None
            ]
            return max(depths, default=None)
    return None


def _container_member_expression(
    node: ast.AST, assignments: Mapping[str, ast.expr]
) -> ast.expr | None:
    if not (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and (key := _literal_subscript_member(node.slice)) is not None
    ):
        return None
    container = assignments.get(node.value.id)
    if isinstance(container, ast.Dict):
        for raw_key, value in zip(container.keys, container.values, strict=True):
            if raw_key is not None and _literal_container_key(raw_key) == key:
                return value
    if isinstance(container, (ast.Tuple, ast.List)) and isinstance(key, int):
        if 0 <= key < len(container.elts):
            return container.elts[key]
    if isinstance(container, ast.Name):
        return _container_member_expression(
            ast.Subscript(value=container, slice=node.slice, ctx=ast.Load()), assignments
        )
    return None


def _name_resolves_to(
    name: str,
    target: str | None,
    assignments: Mapping[str, ast.expr],
    seen: frozenset[str] = frozenset(),
) -> bool:
    if target is None or name in seen:
        return False
    if name == target:
        return True
    expression = assignments.get(name)
    return bool(
        isinstance(expression, ast.Name)
        and _name_resolves_to(expression.id, target, assignments, seen | {name})
    )


def _component_expression_depth(node: ast.AST, values: Mapping[str, _Value]) -> int:
    depths = [
        values[item.id].depth
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in values
    ]
    base = max(depths, default=1)
    if isinstance(node, ast.Call) and depths:
        child_calls = [
            _component_expression_depth(item, values)
            for item in ast.iter_child_nodes(node)
            if isinstance(item, ast.Call) or _reads_any(item, values)
        ]
        return max((base, *child_calls), default=base) + 1
    return base


def _valid_python_document(document: InspectionDocument) -> bool:
    if (
        document.media_type != "text/x-python"
        or document.parser_result_ref is None
        or document.parser_result_payload is None
        or len(document.content) > _SOURCE_BYTE_MAX
    ):
        return False
    try:
        parser = json.loads(document.parser_result_payload)
    except (UnicodeError, json.JSONDecodeError):
        return False
    source = parser.get("source_ref", {}) if isinstance(parser, Mapping) else {}
    return bool(
        isinstance(parser, Mapping)
        and parser.get("parser_id") == "parser:python-ast-tokenize"
        and parser.get("parser_version") == "0.15.1"
        and parser.get("coverage_status") == "covered"
        and source.get("path") == document.path
        and source.get("content_digest") == document.content_digest
    )


def _regular_file_paths(records: Sequence[FrozenBaseRecord]) -> list[str] | None:
    result: list[str] = []
    try:
        for record in records:
            if record.ref.record_type != "file_record":
                continue
            value = json.loads(record.canonical_payload)
            if not isinstance(value, Mapping):
                return None
            path = value.get("path")
            if value.get("entry_kind") == "regular_file":
                if not isinstance(path, str) or not _safe_path(path):
                    return None
                result.append(path)
    except (UnicodeError, json.JSONDecodeError):
        return None
    return result if len(result) == len(set(result)) else None


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(
        value
        and "\x00" not in value
        and "\\" not in value
        and not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _import_candidates(tree: ast.Module) -> tuple[str, ...] | None:
    result: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "importlib" or alias.name.startswith("importlib.")
                for alias in node.names
            ):
                return None
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if (
                node.level
                or node.module is None
                or node.module == "importlib"
                or node.module.startswith("importlib.")
                or any(alias.name == "*" for alias in node.names)
            ):
                return None
            result.extend(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name) and node.func.id == "__import__"
        ):
            return None
    return tuple(sorted(result))


def _prefix_hit(candidate: str, prefixes: Sequence[str]) -> bool:
    return any(candidate == prefix or candidate.startswith(prefix + ".") for prefix in prefixes)


def _chosen_scope(
    tree: ast.Module,
) -> tuple[
    tuple[ast.stmt, ...] | None,
    tuple[ast.stmt, ...],
    dict[str, ast.FunctionDef],
    str | None,
]:
    body = tuple(item for item in tree.body if not _is_docstring(item))
    mains = [item for item in body if isinstance(item, ast.FunctionDef) and item.name == "main"]
    async_mains = [
        item for item in body if isinstance(item, ast.AsyncFunctionDef) and item.name == "main"
    ]
    guards = [item for item in body if isinstance(item, ast.If) and _exact_main_guard(item)]
    if mains or async_mains or guards:
        if len(mains) != 1 or async_mains or len(guards) != 1 or not _valid_main(mains[0]):
            return None, (), {}, "analysis-scope-ambiguous"
        main_loads = {
            node.id
            for node in ast.walk(mains[0])
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        setup = tuple(
            item
            for item in body
            if isinstance(item, (ast.Import, ast.ImportFrom))
            or _module_setup_assignment(item, main_loads)
        )
        others = [
            item
            for item in body
            if item not in setup and item is not mains[0] and item is not guards[0]
        ]
        if any(
            not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for item in others
        ):
            return None, (), {}, "analysis-scope-ambiguous"
        helpers = {
            item.name: item
            for item in others
            if isinstance(item, ast.FunctionDef) and item.name != "main"
        }
        synchronous = [item for item in others if isinstance(item, ast.FunctionDef)]
        if len(helpers) != len(synchronous):
            duplicates = {
                item.name
                for item in synchronous
                if sum(other.name == item.name for other in synchronous) > 1
            }
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in duplicates
                for node in ast.walk(mains[0])
            ):
                return None, (), {}, "helper-definition-unavailable-or-nonunique"
            return None, (), {}, "analysis-scope-ambiguous"
        async_names = {item.name for item in others if isinstance(item, ast.AsyncFunctionDef)}
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in async_names
            for node in ast.walk(mains[0])
        ):
            return None, (), {}, "helper-async-decorator-or-yield-unsupported"
        return (
            tuple(item for item in mains[0].body if not _is_docstring(item)),
            setup,
            helpers,
            None,
        )
    return body, (), {}, None


def _valid_main(node: ast.FunctionDef) -> bool:
    args = node.args
    return bool(
        not node.decorator_list
        and node.type_comment is None
        and not args.posonlyargs
        and not args.args
        and not args.kwonlyargs
        and args.vararg is None
        and args.kwarg is None
        and not args.defaults
        and not args.kw_defaults
    )


def _exact_main_guard(node: ast.If) -> bool:
    test = node.test
    return bool(
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Call)
        and isinstance(node.body[0].value.func, ast.Name)
        and node.body[0].value.func.id == "main"
        and not node.body[0].value.args
        and not node.body[0].value.keywords
        and not node.orelse
    )


def _module_setup_assignment(node: ast.stmt, relevant_names: set[str]) -> bool:
    if not (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return False
    value = node.value
    if isinstance(value, ast.Constant):
        return True
    if isinstance(value, (ast.Tuple, ast.List)):
        return bool(_closed_sequence_elements(value.elts) is not None)
    if _file_path_expression_syntax(value):
        return True
    name = node.targets[0].id
    return name not in relevant_names and _pure_module_expression(value)


def _pure_module_expression(node: ast.expr) -> bool:
    collection_nodes = [
        item
        for item in ast.walk(node)
        if isinstance(item, (ast.Tuple, ast.List, ast.Set, ast.Dict))
    ]
    return bool(
        all(
            isinstance(
                item,
                (
                    ast.Constant,
                    ast.Name,
                    ast.Load,
                    ast.Tuple,
                    ast.List,
                    ast.Set,
                    ast.Dict,
                    ast.UnaryOp,
                    ast.UAdd,
                    ast.USub,
                    ast.Invert,
                    ast.BinOp,
                    ast.Add,
                    ast.Sub,
                    ast.Mult,
                    ast.Div,
                    ast.FloorDiv,
                    ast.Mod,
                    ast.Pow,
                    ast.BitOr,
                    ast.BitAnd,
                    ast.BitXor,
                    ast.LShift,
                    ast.RShift,
                ),
            )
            for item in ast.walk(node)
        )
        and all(
            len(getattr(item, "elts", getattr(item, "keys", ()))) <= 16 for item in collection_nodes
        )
    )


def _file_path_expression_syntax(node: ast.expr) -> bool:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return bool(
            isinstance(node.left, (ast.Name, ast.Attribute, ast.Call))
            and isinstance(node.right, (ast.Name, ast.Constant))
        )
    if isinstance(node, ast.Call):
        return bool(
            (isinstance(node.func, ast.Attribute) and node.func.attr in {"join", "dirname"})
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "Path")
        )
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        return isinstance(node.value, (ast.Call, ast.Name))
    return False


def _module_constant(node: ast.stmt) -> bool:
    return bool(
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
    )


def _closed_sequence_elements(elements: Sequence[ast.expr]) -> list[object] | None:
    if not 1 <= len(elements) <= 16:
        return None
    values: list[object] = []
    for item in elements:
        if not isinstance(item, ast.Constant) or isinstance(item.value, complex):
            return None
        value = item.value
        if isinstance(value, str):
            if not value or len(value.encode("utf-8")) > 128 or "\x00" in value:
                return None
        elif isinstance(value, float):
            if not math.isfinite(value):
                return None
        elif value is not None and not isinstance(value, (int, bool)):
            return None
        values.append(value)
    return values


def _resolver(statements: Sequence[ast.stmt]) -> tuple[_Resolver | None, str | None]:
    imports: dict[str, str] = {}
    constants: dict[str, str] = {}
    literals: dict[str, int | float | bool] = {}
    tuples: dict[str, tuple[object, ...]] = {}
    sequence_kinds: dict[str, str] = {}
    file_parents: set[str] = set()
    accepted_names: set[str] = set()
    for statement in statements:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                qualified = alias.name if alias.asname else alias.name.split(".", 1)[0]
                if bound in imports:
                    return None, "api-resolution-ambiguous"
                imports[bound] = qualified
                accepted_names.add(bound)
        elif isinstance(statement, ast.ImportFrom):
            if (
                statement.level
                or statement.module is None
                or any(item.name == "*" for item in statement.names)
            ):
                return None, "api-resolution-ambiguous"
            for alias in statement.names:
                bound = alias.asname or alias.name
                if bound in imports:
                    return None, "api-resolution-ambiguous"
                imports[bound] = f"{statement.module}.{alias.name}"
                accepted_names.add(bound)
    resolver = _Resolver(
        imports,
        constants,
        literals,
        tuples,
        sequence_kinds,
        file_parents,
        set(accepted_names & _UNSHADOWED_BUILTINS),
        accepted_names,
    )
    for statement in statements:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
        ):
            continue
        name = statement.targets[0].id
        if isinstance(statement.value, ast.Constant) and isinstance(
            statement.value.value, (int, float, bool)
        ):
            if name in constants or name in literals or name in tuples or name in imports:
                return None, "api-resolution-ambiguous"
            literals[name] = statement.value.value
            continue
        if isinstance(statement.value, ast.Name) and statement.value.id in literals:
            if name in constants or name in literals or name in tuples or name in imports:
                return None, "api-resolution-ambiguous"
            literals[name] = literals[statement.value.id]
            continue
        if (
            isinstance(statement.value, (ast.Tuple, ast.List))
            and (sequence := _closed_sequence_elements(statement.value.elts)) is not None
        ):
            if name in constants or name in literals or name in tuples or name in imports:
                return None, "api-resolution-ambiguous"
            tuples[name] = tuple(sequence)
            sequence_kinds[name] = "list" if isinstance(statement.value, ast.List) else "tuple"
            continue
        if _file_parent_expression(statement.value, resolver):
            if (
                name in constants
                or name in literals
                or name in tuples
                or name in imports
                or name in file_parents
            ):
                return None, "api-resolution-ambiguous"
            file_parents.add(name)
            continue
        string = resolver.string(statement.value)
        if string is None:
            path = _static_path(statement.value, resolver)
            string = path
        if string is not None:
            if (
                name in constants
                or name in literals
                or name in tuples
                or name in imports
                or name in file_parents
            ):
                return None, "api-resolution-ambiguous"
            constants[name] = string
        if name in _UNSHADOWED_BUILTINS:
            resolver.builtins_shadowed.add(name)
    for node in _walk_statements(statements):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets: Iterable[ast.AST]
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = (node.target,)
            if any(name in accepted_names for target in targets for name in _store_names(target)):
                return None, "api-resolution-ambiguous"
    if resolver.builtins_shadowed:
        return None, "api-resolution-ambiguous"
    return resolver, None


def _static_path(node: ast.expr, resolver: _Resolver) -> str | None:
    value = resolver.string(node)
    if value is not None:
        return value if _safe_path(value) else None
    if (
        isinstance(node, ast.Call)
        and resolver.qualified(node.func) == "pathlib.Path"
        and len(node.args) == 1
        and not node.keywords
    ):
        value = resolver.string(node.args[0])
        return value if value is not None and _safe_path(value) else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if _file_parent_expression(node.left, resolver):
            right = resolver.string(node.right)
            return right if right is not None and _safe_path(right) else None
        left = _static_path(node.left, resolver)
        right = resolver.string(node.right)
        if left is None or right is None or "/" in right or right in {"", ".", ".."}:
            return None
        joined = f"{left}/{right}"
        return joined if _safe_path(joined) else None
    if (
        isinstance(node, ast.Call)
        and resolver.qualified(node.func) == "os.path.join"
        and len(node.args) == 2
        and not node.keywords
        and _file_parent_expression(node.args[0], resolver)
    ):
        right = resolver.string(node.args[1])
        return right if right is not None and _safe_path(right) else None
    return None


def _file_parent_expression(node: ast.expr, resolver: _Resolver) -> bool:
    if isinstance(node, ast.Name):
        return node.id in resolver.file_parents
    if (
        isinstance(node, ast.Call)
        and resolver.qualified(node.func) == "os.path.dirname"
        and len(node.args) == 1
        and not node.keywords
    ):
        inner = node.args[0]
        return bool(
            isinstance(inner, ast.Call)
            and resolver.qualified(inner.func) == "os.path.abspath"
            and len(inner.args) == 1
            and not inner.keywords
            and isinstance(inner.args[0], ast.Name)
            and inner.args[0].id == "__file__"
        )
    if not (isinstance(node, ast.Attribute) and node.attr == "parent"):
        return False
    value = node.value
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "resolve"
        and not value.args
        and not value.keywords
    ):
        value = value.func.value
    return bool(
        isinstance(value, ast.Call)
        and resolver.qualified(value.func) == "pathlib.Path"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Name)
        and value.args[0].id == "__file__"
    )


def _literal_keywords(keywords: Sequence[ast.keyword]) -> dict[str, object] | None:
    result: dict[str, object] = {}
    for keyword in keywords:
        if (
            keyword.arg is None
            or keyword.arg in result
            or not isinstance(keyword.value, ast.Constant)
        ):
            return None
        result[keyword.arg] = keyword.value.value
    return result


def _parse_dates_columns(
    call: ast.Call,
    *,
    resolver: _Resolver,
    csv_header: Sequence[str],
    forbidden: set[str],
) -> tuple[str, ...]:
    if (
        len(call.keywords) != 1
        or call.keywords[0].arg != "parse_dates"
        or len(call.args) != 1
        or any(isinstance(argument, ast.Starred) for argument in call.args)
    ):
        return ()
    date_columns = call.keywords[0].value
    if not isinstance(date_columns, (ast.List, ast.Name)) or (
        isinstance(date_columns, ast.Name)
        and resolver.sequence_kinds.get(date_columns.id) != "list"
    ):
        return ()
    raw = resolver.sequence(date_columns)
    if raw is None or not 1 <= len(raw) <= 16 or not all(isinstance(item, str) for item in raw):
        return ()
    columns = tuple(str(item) for item in raw)
    if (
        len(set(columns)) != len(columns)
        or any(csv_header.count(column) != 1 for column in columns)
        or set(columns) & forbidden
    ):
        return ()
    return columns


def _same_column_auxiliary_conversion(
    target: ast.Subscript,
    expression: ast.expr,
    resolver: _Resolver,
) -> str | None:
    if not isinstance(target.value, ast.Name):
        return None
    column = resolver.string(target.slice)
    if column is None:
        return None

    if (
        isinstance(expression, ast.Attribute)
        and expression.attr == "date"
        and isinstance(expression.value, ast.Attribute)
        and expression.value.attr == "dt"
        and isinstance(expression.value.value, ast.Call)
    ):
        call = expression.value.value
        if (
            resolver.qualified(call.func) == "pandas.to_datetime"
            and len(call.args) == 1
            and not call.keywords
            and _same_frame_column_read(call.args[0], target.value.id, column, resolver)
        ):
            return column

    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == "astype"
        and _same_frame_column_read(expression.func.value, target.value.id, column, resolver)
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.Name)
        and expression.args[0].id in {"str", "int", "float"}
        and expression.args[0].id not in resolver.builtins_shadowed
    ):
        return column
    return None


def _same_frame_column_read(
    node: ast.expr,
    frame: str,
    column: str,
    resolver: _Resolver,
) -> bool:
    return bool(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == frame
        and resolver.string(node.slice) == column
    )


def _pandas_selection(
    expression: ast.expr,
    values: Mapping[str, _Value],
    resolver: _Resolver,
) -> tuple[str, str, str, str, str] | None:
    # FRAME.loc[FRAME[GROUP] == G, VALUE]
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Attribute)
        and expression.value.attr == "loc"
        and isinstance(expression.value.value, ast.Name)
        and isinstance(expression.slice, ast.Tuple)
        and len(expression.slice.elts) == 2
    ):
        receiver = expression.value.value.id
        mask, projection = expression.slice.elts
        parsed = _mask(mask, receiver, resolver)
        value = resolver.string(projection)
        if receiver in values and parsed is not None and value is not None:
            return receiver, parsed[0], parsed[1], value, "pandas_loc_boolean_mask_v1"
    # FRAME[FRAME[GROUP] == G][VALUE]
    if isinstance(expression, ast.Subscript):
        value_column = resolver.string(expression.slice)
        inner = expression.value
        if (
            value_column is not None
            and isinstance(inner, ast.Subscript)
            and isinstance(inner.value, ast.Name)
        ):
            receiver = inner.value.id
            parsed = _mask(inner.slice, receiver, resolver)
            if receiver in values and parsed is not None:
                return receiver, parsed[0], parsed[1], value_column, "pandas_boolean_mask_v1"
    # FRAME.query("GROUP == 'G'")[VALUE]
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Call)
        and isinstance(expression.value.func, ast.Attribute)
        and expression.value.func.attr == "query"
        and isinstance(expression.value.func.value, ast.Name)
        and len(expression.value.args) == 1
        and not expression.value.keywords
    ):
        receiver = expression.value.func.value.id
        query = resolver.string(expression.value.args[0])
        value = resolver.string(expression.slice)
        match = _QUERY.fullmatch(query or "")
        if receiver in values and match is not None and value is not None:
            return receiver, match["header"], match["value"], value, "pandas_query_v1"
    # GROUPED.get_group(G)[VALUE], with GROUPED = FRAME.groupby(GROUP)
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Call)
        and isinstance(expression.value.func, ast.Attribute)
        and expression.value.func.attr == "get_group"
        and isinstance(expression.value.func.value, ast.Name)
        and len(expression.value.args) == 1
        and not expression.value.keywords
    ):
        grouped = expression.value.func.value.id
        parent = values.get(grouped)
        group_value = resolver.string(expression.value.args[0])
        value = resolver.string(expression.slice)
        if (
            parent is not None
            and parent.kind == "grouped"
            and group_value is not None
            and value is not None
        ):
            return (
                grouped,
                str(parent.group_column),
                group_value,
                value,
                "pandas_groupby_get_group_v1",
            )
    return None


def _mask(node: ast.expr, receiver: str, resolver: _Resolver) -> tuple[str, str] | None:
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Subscript)
        and isinstance(node.left.value, ast.Name)
        and node.left.value.id == receiver
    ):
        group = resolver.string(node.left.slice)
        value = resolver.string(node.comparators[0])
        if group is not None and value is not None:
            return group, value
    return None


def _reads_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id == name
        for item in ast.walk(node)
    )


def _aggregation_call(
    call: ast.Call,
    api: str | None,
    values: Mapping[str, _Value],
    resolver: _Resolver,
) -> bool:
    if api in _NUMPY_REDUCERS or api in _STATISTICS_REDUCERS:
        return _reads_any(call, values)
    if api == "sum" and "sum" not in resolver.builtins_shadowed:
        return _reads_any(call, values)
    if isinstance(call.func, ast.Attribute):
        method = call.func.attr
        receiver = call.func.value
        if method in _FRAME_REDUCERS and _reads_any(receiver, values):
            return True
        if method in _GROUP_REDUCERS:
            if any(
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr in {"groupby", "resample"}
                for item in ast.walk(receiver)
            ) and _reads_any(receiver, values):
                return True
            if (
                isinstance(receiver, ast.Call)
                and isinstance(receiver.func, ast.Attribute)
                and receiver.func.attr in {"groupby", "resample"}
                and _reads_any(receiver, values)
            ):
                return True
            if isinstance(receiver, ast.Name) and values.get(
                receiver.id, _Value("", receiver)
            ).kind in {"grouped", "resampler"}:
                return True
    return False


def _accepted_selection_call(
    call: ast.Call, values: Mapping[str, _Value], resolver: _Resolver
) -> bool:
    if isinstance(call.func, ast.Attribute) and call.func.attr in {"query", "groupby", "get_group"}:
        return _reads_any(call, values)
    return False


def _test_variant(api: str, keywords: Sequence[ast.keyword]) -> str | None:
    if api == "scipy.stats.ttest_ind":
        if not keywords:
            return "student"
        if (
            len(keywords) != 1
            or keywords[0].arg != "equal_var"
            or not isinstance(keywords[0].value, ast.Constant)
        ):
            return None
        if keywords[0].value.value is True:
            return "student"
        if keywords[0].value.value is False:
            return "welch"
        return None
    if api == "scipy.stats.mannwhitneyu":
        if not keywords:
            return "mannwhitneyu"
        if (
            len(keywords) != 1
            or keywords[0].arg != "alternative"
            or not isinstance(keywords[0].value, ast.Constant)
        ):
            return None
        return (
            "mannwhitneyu" if keywords[0].value.value in {"two-sided", "less", "greater"} else None
        )
    return None


def _descriptive_loop(
    node: ast.For,
    values: Mapping[str, _Value],
    resolver: _Resolver,
    backward_slice_names: set[str],
) -> bool:
    if node.orelse or not isinstance(node.target, (ast.Tuple, ast.List)):
        return False
    bound = _store_names(node.target)
    if not bound or bound & (set(values) | backward_slice_names):
        return False
    tracked_iter_names = {
        item.id for item in ast.walk(node.iter) if isinstance(item, ast.Name) and item.id in values
    }
    if not tracked_iter_names:
        return False
    for item in ast.walk(node.iter):
        if isinstance(item, ast.Call):
            return False
        if (
            isinstance(item, ast.Name)
            and item.id not in values
            and item.id not in resolver.constants
        ):
            return False
    for statement in node.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            return False
        call = statement.value
        if resolver.qualified(call.func) != "print" or "print" in resolver.builtins_shadowed:
            return False
        for inner in ast.walk(call):
            if isinstance(
                inner,
                (
                    ast.For,
                    ast.While,
                    ast.If,
                    ast.Break,
                    ast.Continue,
                    ast.Await,
                    ast.Yield,
                    ast.YieldFrom,
                    ast.comprehension,
                ),
            ):
                return False
            if (
                isinstance(inner, ast.Call)
                and inner is not call
                and not _loop_reduction(inner, bound, resolver)
            ):
                return False
            if isinstance(inner, ast.Name) and isinstance(inner.ctx, (ast.Store, ast.Del)):
                return False
            if (
                isinstance(inner, ast.Name)
                and isinstance(inner.ctx, ast.Load)
                and inner.id not in bound
                and inner.id not in values
                and inner.id not in resolver.constants
                and inner.id not in _UNSHADOWED_BUILTINS
            ):
                return False
    return True


def _loop_reduction(call: ast.Call, bound: set[str], resolver: _Resolver) -> bool:
    api = resolver.qualified(call.func)
    if (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id in bound
    ):
        if call.func.attr not in _LOOP_METHOD_REDUCTIONS:
            return False
        if call.func.attr == "std":
            if not call.args and not call.keywords:
                return True
            return bool(
                not call.args
                and len(call.keywords) == 1
                and call.keywords[0].arg == "ddof"
                and isinstance(call.keywords[0].value, ast.Constant)
                and call.keywords[0].value.value == 1
            )
        return not call.args and not call.keywords
    if api in {"len", "sum", "min", "max"} and api not in resolver.builtins_shadowed:
        return (
            len(call.args) == 1
            and not call.keywords
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id in bound
        )
    if api == "round" and "round" not in resolver.builtins_shadowed:
        return bool(
            len(call.args) in {1, 2}
            and not call.keywords
            and isinstance(call.args[0], ast.Call)
            and _loop_reduction(call.args[0], bound, resolver)
            and (
                len(call.args) == 1
                or (isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, int))
            )
        )
    return False


def _straight_descriptive_call(
    call: ast.Call,
    test: ast.Call,
    values: Mapping[str, _Value],
    outputs: Sequence[_Sink],
    resolver: _Resolver,
) -> bool:
    if _position(call) <= _position(test) or not _inside_any(call, [item.call for item in outputs]):
        return False
    if (
        isinstance(call.func, ast.Name)
        and call.func.id == "len"
        and "len" not in resolver.builtins_shadowed
    ):
        return (
            len(call.args) == 1
            and not call.keywords
            and isinstance(call.args[0], ast.Name)
            and values.get(call.args[0].id, _Value("", call)).kind in {"selection", "identity"}
        )
    if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
        value = values.get(call.func.value.id)
        if value is None or value.kind not in {"selection", "identity"}:
            return False
        if call.func.attr == "mean":
            return not call.args and not call.keywords
        if call.func.attr == "std":
            return bool(
                not call.args
                and len(call.keywords) == 1
                and call.keywords[0].arg == "ddof"
                and isinstance(call.keywords[0].value, ast.Constant)
                and call.keywords[0].value.value == 1
            )
    return False


def _descriptive_format_call(
    call: ast.Call,
    values: Mapping[str, _Value],
    outputs: Sequence[_Sink],
    resolver: _Resolver,
) -> bool:
    if not (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "format"
        and isinstance(call.func.value, ast.Constant)
        and isinstance(call.func.value.value, str)
        and call.args
        and not call.keywords
        and _inside_any(call, [item.call for item in outputs if item.kind == "builtin_print"])
    ):
        return False
    for argument in call.args:
        if isinstance(argument, ast.Constant):
            continue
        if isinstance(argument, ast.Name):
            value = values.get(argument.id)
            if value is not None and value.kind == "descriptive_scalar":
                continue
            if argument.id in resolver.constants:
                continue
        if _descriptive_expression_parents(argument, values, resolver):
            continue
        return False
    return True


def _descriptive_expression_parents(
    expression: ast.expr,
    values: Mapping[str, _Value],
    resolver: _Resolver,
) -> list[_Value] | None:
    if _finite_numeric_constant(expression):
        return []
    if isinstance(expression, ast.Name):
        value = values.get(expression.id)
        if value is not None and value.kind == "descriptive_scalar":
            return [value]
        if value is not None and value.kind == "descriptive_literal":
            return []
        if expression.id in resolver.constants:
            return []
        return None
    if (parent := _x7_count_attribute_parent(expression, values)) is not None:
        return [parent]
    if _x3_reduction_shape(expression, resolver):
        receiver = _x3_reduction_receiver_name(expression, resolver)
        parent = values.get(receiver) if receiver is not None else None
        if (
            parent is not None
            and parent.kind in {"selection", "identity"}
            and not parent.aggregated
            and not parent.unknown
        ):
            return [parent]
        return None
    if (
        isinstance(expression, ast.Call)
        and resolver.qualified(expression.func) in {"int", "float"}
        and resolver.qualified(expression.func) not in resolver.builtins_shadowed
        and len(expression.args) == 1
        and not expression.keywords
        and not (
            isinstance(expression.args[0], ast.Call)
            and resolver.qualified(expression.args[0].func) in {"int", "float"}
        )
    ):
        parents = _descriptive_expression_parents(expression.args[0], values, resolver)
        return parents if parents else None
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and (container := values.get(expression.value.id)) is not None
        and container.kind == "descriptive_container"
        and (member := _literal_subscript_member(expression.slice)) is not None
        and member in container.descriptive_members
    ):
        return [container]
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, (ast.UAdd, ast.USub)):
        return _descriptive_expression_parents(expression.operand, values, resolver)
    if isinstance(expression, ast.BinOp) and isinstance(
        expression.op,
        (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow),
    ):
        left = _descriptive_expression_parents(expression.left, values, resolver)
        right = _descriptive_expression_parents(expression.right, values, resolver)
        if left is None or right is None:
            return None
        parents = [*left, *right]
        return parents
    return None


def _x7_count_attribute_parent(
    expression: ast.expr,
    values: Mapping[str, _Value],
) -> _Value | None:
    receiver: str | None = None
    if (
        isinstance(expression, ast.Attribute)
        and expression.attr == "size"
        and isinstance(expression.value, ast.Name)
    ):
        receiver = expression.value.id
    elif (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Attribute)
        and expression.value.attr == "shape"
        and isinstance(expression.value.value, ast.Name)
        and isinstance(expression.slice, ast.Constant)
        and expression.slice.value == 0
        and not isinstance(expression.slice.value, bool)
    ):
        receiver = expression.value.value.id
    parent = values.get(receiver) if receiver is not None else None
    if (
        parent is None
        or parent.kind not in {"selection", "identity"}
        or parent.aggregated
        or parent.unknown
    ):
        return None
    return parent


def _x3_reduction_receiver_name(expression: ast.expr, resolver: _Resolver) -> str | None:
    reduction = expression
    if (
        isinstance(reduction, ast.Call)
        and resolver.qualified(reduction.func) == "round"
        and reduction.args
    ):
        reduction = reduction.args[0]
    if not isinstance(reduction, ast.Call):
        return None
    if resolver.qualified(reduction.func) in {"len", "sum", "min", "max"}:
        first = reduction.args[0] if reduction.args else None
        return first.id if isinstance(first, ast.Name) else None
    if isinstance(reduction.func, ast.Attribute) and isinstance(reduction.func.value, ast.Name):
        return reduction.func.value.id
    return None


def _any_aggregated_argument(call: ast.Call, values: Mapping[str, _Value]) -> bool:
    return any(
        isinstance(item, ast.Name) and values.get(item.id, _Value("", item)).aggregated
        for item in call.args
    )


def _call_reaches_sink(
    call: ast.Call,
    sinks: Sequence[_Sink],
    values: Mapping[str, _Value],
    assignments: Mapping[str, ast.expr] | None = None,
) -> bool:
    for sink in sinks:
        for payload in sink.payloads:
            if _inside_any(call, (payload,)):
                return True
            if any(
                call in values[item.id].call_origins
                for item in ast.walk(payload)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id in values
            ):
                return True
            if assignments is not None and any(
                _inside_any(call, (expression,))
                for item in ast.walk(payload)
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
                if (expression := assignments.get(item.id)) is not None
            ):
                return True
    return False


def _inside_any(needle: ast.AST, haystacks: Sequence[ast.AST]) -> bool:
    return any(any(item is needle for item in ast.walk(haystack)) for haystack in haystacks)


def _reads_any(node: ast.AST, values: Mapping[str, _Value]) -> bool:
    return any(
        isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in values
        for item in ast.walk(node)
    )


def _call_origins_read(node: ast.AST, values: Mapping[str, _Value]) -> frozenset[ast.Call]:
    return frozenset(
        origin
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        if (value := values.get(item.id)) is not None
        for origin in value.call_origins
    )


def _roots_read(node: ast.AST, values: Mapping[str, _Value]) -> set[str]:
    return {
        value.root
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        if (value := values.get(item.id)) is not None and value.root is not None
    }


def _single_root(node: ast.AST, values: Mapping[str, _Value]) -> str | None:
    roots = _roots_read(node, values)
    return next(iter(roots)) if len(roots) == 1 else None


def _parent_depth(node: ast.AST, values: Mapping[str, _Value]) -> int:
    depths = [
        values[item.id].depth
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in values
    ]
    return max(depths, default=1)


def _root_name(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _store_names(node: ast.AST) -> set[str]:
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del))
    }


def _assigned_name(statements: Sequence[ast.stmt], needle: ast.Call) -> str | None:
    for statement in statements:
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.Assign)
                and node.value is needle
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                return node.targets[0].id
    return None


def _walk_statements(statements: Sequence[ast.stmt]) -> Iterable[ast.AST]:
    for statement in statements:
        yield from ast.walk(statement)


def _is_docstring(node: ast.stmt) -> bool:
    return bool(
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _position(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        int(getattr(node, "lineno", 0)),
        int(getattr(node, "col_offset", 0)),
        int(getattr(node, "end_lineno", getattr(node, "lineno", 0))),
        int(getattr(node, "end_col_offset", getattr(node, "col_offset", 0))),
    )


def _span(node: ast.AST) -> tuple[int, int, int, int]:
    line, column, end_line, end_column = _position(node)
    return line, end_line, column + 1, end_column + 1
