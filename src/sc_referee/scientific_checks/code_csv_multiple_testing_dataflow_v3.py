"""Closed, prose-free AST dataflow for the contract-bound multiple-testing check.

Only Python syntax, established API identities, and values occupying the exact
structural slots enumerated by ADR-0079 are inspected.  Project code is never
imported or executed.  Unsupported or nonunique dataflow returns one bounded
coverage reason rather than a partial positive.
"""

from __future__ import annotations

import ast
import copy
import csv
import io
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Literal, cast

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.core import FrozenBaseRecord, InspectionDocument

CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

_SOURCE_BYTE_MAX = 1 << 20
_AST_NODE_MAX = 50_000
_DEFINITION_NODE_MAX = 16
_QUERY = re.compile(
    r"\A(?P<header>[A-Za-z_][A-Za-z0-9_]*) == "
    r"(?P<quote>['\"])(?P<value>[A-Za-z0-9_.-]+)(?P=quote)\Z"
)
_STATISTICS_PREFIXES = (
    "scipy.stats",
    "statsmodels",
    "pingouin",
    "pymer4",
    "bambi",
    "gpboost",
    "merf",
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
        "pivot",
        "resample",
        "head",
        "tail",
        "nth",
        "sample",
        "cumcount",
        "idxmin",
        "idxmax",
        "rank",
        "diff",
        "rolling",
        "ewm",
        "transform",
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
        "statsmodels.api.GLMGam",
        "statsmodels.gam.api.GLMGam",
        "pingouin.mixed_anova",
        "pingouin.rm_anova",
    }
)
_DEPENDENCE_CLASS_APIS = frozenset(
    {
        "statsmodels.api.MixedLM",
        "statsmodels.regression.mixed_linear_model.MixedLM",
        "statsmodels.api.GEE",
        "statsmodels.genmod.generalized_estimating_equations.GEE",
        "statsmodels.api.GLMGam",
        "statsmodels.gam.api.GLMGam",
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
        "reversed",
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
        "SystemExit",
    }
)
_V2_RESAMPLING_REDUCERS = frozenset(
    {
        "numpy.mean",
        "numpy.nanmean",
        "numpy.std",
        "numpy.nanstd",
        "numpy.median",
        "numpy.nanmedian",
        "numpy.sum",
        "numpy.nansum",
        "numpy.count_nonzero",
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
_V2_RESAMPLING_MIN_TRIPS = 10


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
    row_complete: bool = False


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
    bound_names: set[str] = field(default_factory=set)
    tables: dict[str, tuple[tuple[object, ...], ...]] = field(default_factory=dict)
    dictionaries: dict[str, tuple[tuple[object, object], ...]] = field(default_factory=dict)

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
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            dictionary = self.dictionaries.get(node.value.id)
            member = _mt_literal_member(node.slice)
            if dictionary is not None and member is not None:
                for key, value in dictionary:
                    if key == member and isinstance(value, str):
                        return value
            sequence = self.tuples.get(node.value.id)
            if sequence is not None and isinstance(member, int):
                index = member if member >= 0 else len(sequence) + member
                if 0 <= index < len(sequence) and isinstance(sequence[index], str):
                    return str(sequence[index])
        return None

    def sequence(self, node: ast.expr) -> tuple[object, ...] | None:
        if isinstance(node, (ast.List, ast.Tuple)):
            values = _closed_sequence_elements(node.elts)
            return tuple(values) if values is not None else None
        if isinstance(node, ast.Name):
            sequence = self.tuples.get(node.id)
            if sequence is not None:
                return sequence
            dictionary = self.dictionaries.get(node.id)
            if dictionary is not None:
                return tuple(key for key, _value in dictionary)
        return None

    def table(self, node: ast.expr) -> tuple[tuple[object, ...], ...] | None:
        return self.tables.get(node.id) if isinstance(node, ast.Name) else None

    def dictionary(self, node: ast.expr) -> tuple[tuple[object, object], ...] | None:
        return self.dictionaries.get(node.id) if isinstance(node, ast.Name) else None


@dataclass(frozen=True)
class _Expansion:
    scope: tuple[ast.stmt, ...] | None
    reason: str | None


@dataclass(frozen=True)
class _Mt23TerminalKey:
    production: Literal["literal_percent", "terminal_ifexp"]
    source_position: tuple[int, int, int, int]
    structure: str
    family_position: int


@dataclass(frozen=True)
class _Mt23TerminalOccurrence:
    transport_key: _Mt23TerminalKey
    decision_key: _Mt23TerminalKey | None
    family_position: int
    ordinal: int
    transport: ast.expr = field(compare=False, hash=False)
    decision: ast.IfExp | None = field(compare=False, hash=False)


@dataclass(frozen=True)
class _Mt23TerminalMatch:
    occurrence: _Mt23TerminalOccurrence
    transport: ast.expr = field(compare=False, hash=False)
    decision: ast.IfExp | None = field(compare=False, hash=False)
    sink: _Sink = field(compare=False, hash=False)


@dataclass(frozen=True)
class _Mt23TerminalClosure:
    occurrences: tuple[_Mt23TerminalOccurrence, ...]
    matches: tuple[_Mt23TerminalMatch, ...]
    failure: Literal["unresolved-pvalue-consumer"] | None = None


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
    csv_content: bytes | None = None,
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
        full_scope = tuple(tree.body)
        full_readers = _v3_full_scope_reader_census(
            full_scope,
            resolver=resolver,
            csv_header=tuple(csv_header),
            unit_column=unit_column,
            group_column=group_column,
        )
        if len(full_readers) > 1:
            return CodeDataflowResult(None, "additional-accepted-reader-present")
        if len(full_readers) == 1 and full_readers[0] not in {None, authorized_path}:
            return CodeDataflowResult(None, "authorized-reader-lineage-unavailable")
        guard_resolver = _v3_resampling_guard_resolver(full_scope, resolver)
        guard_values = _v3_full_scope_guard_values(
            full_scope,
            resolver=guard_resolver,
            csv_header=tuple(csv_header),
            unit_column=unit_column,
            group_column=group_column,
        )
        guard_assignments = _v3_full_scope_guard_assignments(full_scope, guard_resolver)
        guard_sinks = _registered_sinks(full_scope, guard_resolver)
        dependence_guard = _v3_dependence_guard(full_scope, guard_resolver)
        resampling_guard = _v2_resampling_sibling(
            full_scope,
            guard_values,
            guard_resolver,
            guard_sinks,
            guard_assignments,
        )
        statistics_guard = _v3_statistics_guard(full_scope, guard_resolver)
        syntactic_test_count = _v3_syntactic_test_count(full_scope, guard_resolver)
        if dependence_guard is not None:
            return CodeDataflowResult(None, "dependence-aware-sibling-present")
        if resampling_guard is not None:
            return CodeDataflowResult(None, "resampling-inference-sibling-present")
        if statistics_guard is not None:
            return CodeDataflowResult(None, "unresolved-inference-sibling-present")
        if syntactic_test_count > 1:
            return CodeDataflowResult(None, "multiple-rowwise-test-candidates")
        normalization = _normalize_contract_domain_loops(
            scope=scope,
            resolver=resolver,
            authorized_path=authorized_path,
            csv_header=tuple(csv_header),
            unit_column=unit_column,
            group_column=group_column,
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
        csv_group_units = _csv_group_unit_lineage(
            csv_content,
            csv_header=tuple(csv_header),
            unit_column=unit_column,
            group_column=group_column,
            group_values=group_values,
        )
        if csv_group_units is None:
            return CodeDataflowResult(None, "selected-group-row-completeness-unproven")
        analyzer = _Analyzer(
            scope=expansion.scope,
            full_scope=full_scope,
            resolver=expanded_resolver,
            authorized_path=authorized_path,
            unit_column=unit_column,
            group_column=group_column,
            csv_header=tuple(csv_header),
            group_values=group_values,
            csv_group_units=csv_group_units,
            output_helpers=helpers,
        )
        return analyzer.run()
    except (ArithmeticError, RecursionError, UnicodeError, ValueError):
        return CodeDataflowResult(None, "code-csv-dependence-inspection-exception")


def _csv_group_unit_lineage(
    content: bytes | None,
    *,
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
    group_values: tuple[str, str],
) -> dict[str, tuple[str, ...]] | None:
    """Re-read only the already bounded CSV bytes needed by P2.2."""

    if content is None or content.startswith(b"\xef\xbb\xbf"):
        return None
    if b"\x00" in content:
        return None
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if re.search(r"\r(?!\n)", text):
        return None
    old_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(1 << 20)
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    except (csv.Error, OverflowError):
        return None
    finally:
        csv.field_size_limit(old_limit)
    if (
        not rows
        or tuple(rows[0]) != csv_header
        or len(csv_header) > 512
        or not 2 <= len(rows) - 1 <= 100_000
        or unit_column not in csv_header
        or group_column not in csv_header
        or any(len(row) != len(csv_header) for row in rows[1:])
        or any(len(value) > (1 << 20) for row in rows for value in row)
    ):
        return None
    unit_index = csv_header.index(unit_column)
    group_index = csv_header.index(group_column)
    result: dict[str, list[str]] = {value: [] for value in group_values}
    for row in rows[1:]:
        group = row[group_index]
        unit = row[unit_index]
        if group not in result or not unit or unit != unit.strip():
            return None
        result[group].append(unit)
    if any(not values for values in result.values()):
        return None
    return {key: tuple(values) for key, values in result.items()}


def _v3_full_scope_reader_census(
    statements: Sequence[ast.stmt],
    *,
    resolver: _Resolver,
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
) -> list[str | None]:
    """Count every exact accepted reader form before inference-guard precedence."""

    result: list[str | None] = []
    for node in _walk_statements(statements):
        if not isinstance(node, ast.Call):
            continue
        api = resolver.qualified(node.func)
        accepted = False
        if api == "pandas.read_csv" and len(node.args) == 1:
            accepted = not node.keywords or bool(
                _parse_dates_columns(
                    node,
                    resolver=resolver,
                    csv_header=csv_header,
                    forbidden={unit_column, group_column},
                )
            )
        elif api == "numpy.genfromtxt" and len(node.args) == 1:
            accepted = _literal_keywords(node.keywords) == {
                "delimiter": ",",
                "names": True,
                "dtype": None,
                "encoding": "utf-8",
            }
        if accepted:
            result.append(_static_path(node.args[0], resolver))
    return result


def _mt_full_scope_reader_census(
    tree: ast.Module,
    *,
    resolver: _Resolver,
    local_paths: Mapping[_Mt23ReaderPathKey, str],
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
) -> list[str | None]:
    """Apply the 1.0 reader grammar plus A4's path-formal-only resolution."""

    result: list[str | None] = []
    helpers = {
        item.name: item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and sum(
            isinstance(other, ast.FunctionDef) and other.name == item.name for other in tree.body
        )
        == 1
    }
    calls_by_name: dict[str, list[ast.Call]] = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls_by_name[node.func.id].append(node)

    for node in _walk_statements(tuple(tree.body)):
        if not isinstance(node, ast.Call):
            continue
        api = resolver.qualified(node.func)
        accepted = False
        if api == "pandas.read_csv" and len(node.args) == 1:
            accepted = not node.keywords or bool(
                _parse_dates_columns(
                    node,
                    resolver=resolver,
                    csv_header=csv_header,
                    forbidden={unit_column, group_column},
                )
            )
        elif api == "numpy.genfromtxt" and len(node.args) == 1:
            accepted = _literal_keywords(node.keywords) == {
                "delimiter": ",",
                "names": True,
                "dtype": None,
                "encoding": "utf-8",
            }
        if not accepted:
            continue
        direct = _mt23_reader_path(node, resolver, local_paths)
        if direct is not None:
            result.append(direct)
            continue
        if not isinstance(node.args[0], ast.Name):
            result.append(None)
            continue
        formal = node.args[0].id
        owners = [
            helper for helper in helpers.values() if any(item is node for item in ast.walk(helper))
        ]
        if len(owners) != 1:
            result.append(None)
            continue
        helper = owners[0]
        args = helper.args
        if (
            helper.decorator_list
            or args.posonlyargs
            or args.vararg is not None
            or args.kwarg is not None
            or args.kwonlyargs
            or formal not in {item.arg for item in args.args}
            or any(
                isinstance(item, (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Lambda))
                for item in ast.walk(helper)
            )
        ):
            result.append(None)
            continue
        parameter_names = [item.arg for item in args.args]
        defaults = dict(
            zip(
                parameter_names[len(parameter_names) - len(args.defaults) :],
                args.defaults,
                strict=True,
            )
        )
        sites = calls_by_name.get(helper.name, [])
        indirect = any(
            isinstance(item, ast.Name)
            and item.id == helper.name
            and isinstance(item.ctx, ast.Load)
            and not (
                isinstance(
                    parent := next(
                        (p for p in ast.walk(tree) if item in ast.iter_child_nodes(p)), None
                    ),
                    ast.Call,
                )
                and parent.func is item
            )
            for item in ast.walk(tree)
        )
        paths: list[str | None] = []
        for site in sites:
            bound, binding_reason = _bind_helper_arguments(site, parameter_names, defaults)
            paths.append(
                _static_path(bound[formal], resolver)
                if binding_reason is None and bound is not None and formal in bound
                else None
            )
        default_path = _static_path(defaults[formal], resolver) if formal in defaults else None
        if not sites or indirect or any(path is None for path in paths):
            result.append(None)
        elif default_path is None and formal in defaults:
            result.append(None)
        elif (
            len(
                set(cast(str, path) for path in paths) | ({default_path} if default_path else set())
            )
            != 1
        ):
            result.append(None)
        else:
            result.append(cast(str, paths[0]))
    return result


def _v3_full_scope_guard_values(
    statements: Sequence[ast.stmt],
    *,
    resolver: _Resolver,
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
) -> dict[str, _Value]:
    """Seed S2 lineage from every exact accepted reader in the full module."""

    values: dict[str, _Value] = {}
    for node in _walk_statements(statements):
        if not isinstance(node, ast.Call):
            continue
        api = resolver.qualified(node.func)
        accepted = False
        if api == "pandas.read_csv" and len(node.args) == 1:
            accepted = not node.keywords or bool(
                _parse_dates_columns(
                    node,
                    resolver=resolver,
                    csv_header=csv_header,
                    forbidden={unit_column, group_column},
                )
            )
        elif api == "numpy.genfromtxt" and len(node.args) == 1:
            accepted = _literal_keywords(node.keywords) == {
                "delimiter": ",",
                "names": True,
                "dtype": None,
                "encoding": "utf-8",
            }
        if not accepted:
            continue
        target = _assigned_name(statements, node)
        if target is not None:
            values[target] = _Value("reader", node, root=target, row_complete=True)
    return values


def _v3_resampling_guard_resolver(statements: Sequence[ast.stmt], resolver: _Resolver) -> _Resolver:
    """Resolve closed integer helper defaults for the full-scope S2 census."""

    literals = dict(resolver.literals)
    for node in _walk_statements(statements):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        parameters = [item.arg for item in node.args.args]
        start = len(parameters) - len(node.args.defaults)
        for name, default in zip(parameters[start:], node.args.defaults, strict=True):
            value = _closed_int(default, resolver.literals)
            if value is not None:
                prior = literals.get(name)
                literals[name] = max(int(prior), value) if isinstance(prior, int) else value
    helpers = {
        statement.name: statement
        for statement in statements
        if isinstance(statement, ast.FunctionDef)
    }
    for node in _walk_statements(statements):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and (helper := helpers.get(node.func.id)) is not None
        ):
            continue
        parameters = [item.arg for item in helper.args.args]
        actuals: dict[str, ast.expr] = {
            name: argument for name, argument in zip(parameters, node.args, strict=False)
        }
        actuals.update(
            {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg in parameters}
        )
        for name, actual in actuals.items():
            value = _closed_int(actual, resolver.literals)
            if value is not None:
                prior = literals.get(name)
                literals[name] = max(int(prior), value) if isinstance(prior, int) else value
    return _Resolver(
        imports=dict(resolver.imports),
        constants=dict(resolver.constants),
        literals=literals,
        tuples=dict(resolver.tuples),
        sequence_kinds=dict(resolver.sequence_kinds),
        file_parents=set(resolver.file_parents),
        builtins_shadowed=set(resolver.builtins_shadowed),
        accepted_names=set(resolver.accepted_names),
        bound_names=set(resolver.bound_names),
    )


def _v3_full_scope_guard_assignments(
    statements: Sequence[ast.stmt], resolver: _Resolver
) -> dict[str, ast.expr]:
    """Retain every closed random-generator binding needed by full-scope S2."""

    result = _assignment_expressions(statements)
    for node in _walk_statements(statements):
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and resolver.qualified(node.value.func) == "numpy.random.default_rng"
            and len(node.value.args) <= 1
            and not node.value.keywords
        ):
            continue
        result[node.targets[0].id] = node.value
    return result


class _Analyzer:
    def __init__(
        self,
        *,
        scope: tuple[ast.stmt, ...],
        full_scope: tuple[ast.stmt, ...],
        resolver: _Resolver,
        authorized_path: str,
        unit_column: str,
        group_column: str,
        csv_header: tuple[str, ...],
        group_values: tuple[str, str],
        csv_group_units: Mapping[str, tuple[str, ...]],
        output_helpers: Mapping[str, ast.FunctionDef],
    ) -> None:
        self.scope = scope
        self.full_scope = full_scope
        self.resolver = resolver
        self.authorized_path = authorized_path
        self.unit_column = unit_column
        self.group_column = group_column
        self.csv_header = csv_header
        self.group_values = group_values
        self.csv_group_units = dict(csv_group_units)
        self.output_helpers = dict(output_helpers)
        self.values: dict[str, _Value] = {}
        self.definitions: defaultdict[str, int] = defaultdict(int)
        self.tests: list[_Test] = []
        self.descriptive_loops = 0
        self.reasons: list[tuple[tuple[int, int, int], str]] = []
        self.loops: list[ast.For] = []
        self.assignments = _assignment_expressions(scope)
        self.sinks = _registered_sinks(scope, resolver)
        self.output_buffers = _closed_output_buffers(scope)
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
        self.values[reader.target] = _Value(
            "reader",
            reader.call,
            root=reader.target,
            row_complete=True,
        )
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
            if (
                _v3_unit_summary_guard(
                    self.full_scope,
                    resolver=self.resolver,
                    unit_column=self.unit_column,
                    values=self.values,
                )
                is not None
            ):
                return CodeDataflowResult(None, "unit-level-summary-sibling-present")
            if self.tests:
                return CodeDataflowResult(None, "two-group-row-selection-unavailable")
            return CodeDataflowResult(None, "rowwise-two-sample-test-unavailable")
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
            return CodeDataflowResult(None, "unresolved-call-on-operand-slice")

        self.slice_names = self._backward_slice_names(test)
        if any(self.definitions[name] > 1 for name in self.slice_names):
            return CodeDataflowResult(None, "tracked-value-mutation")
        self.tainted_names = self._tainted_name_closure()
        if (
            _v3_unit_summary_guard(
                self.full_scope,
                resolver=self.resolver,
                unit_column=self.unit_column,
                values=self.values,
            )
            is not None
        ):
            return CodeDataflowResult(None, "unit-level-summary-sibling-present")
        if not self._operand_rows_complete(left) or not self._operand_rows_complete(right):
            return CodeDataflowResult(None, "selected-group-row-completeness-unproven")
        if not _v3_call_reachable(self.scope, test.call):
            return CodeDataflowResult(None, "test-result-output-sink-unavailable")
        sinks = self._result_sinks(test)
        p_depth = max(
            (
                depth
                for sink in sinks
                for payload in sink.payloads
                if (depth := self._p_depth(payload, test)) is not None
            ),
            default=0,
        )
        component_depth = self._component_definition_depth(test)
        max_depth = max(left.depth, right.depth, p_depth + 1, component_depth, 3)
        if max_depth > _DEFINITION_NODE_MAX:
            return CodeDataflowResult(None, "dataflow-definition-ceiling-exceeded")

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

    def _operand_rows_complete(self, value: _Value) -> bool:
        if not value.row_complete or value.group_value not in self.csv_group_units:
            return False
        units = self.csv_group_units[str(value.group_value)]
        return len(units) > len(set(units))

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
            if _v31_inlined_return_tuple_shape(statement, target):
                assert isinstance(target, ast.Tuple)
                assert isinstance(statement.value, ast.Tuple)
                resolved = [
                    self._value(item) or self._test_payload_value(item)
                    for item in statement.value.elts
                ]
                if all(item is not None for item in resolved):
                    for target_item, value in zip(target.elts, resolved, strict=True):
                        assert isinstance(target_item, ast.Name)
                        assert value is not None
                        self._bind(target_item.id, value, statement)
                    return
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
                row_complete=parent.row_complete,
            )
        if (
            isinstance(expression, ast.Subscript)
            and isinstance(expression.value, ast.Attribute)
            and expression.value.attr == "iloc"
        ):
            filtered_parent = self._value(expression.value.value)
            if (
                filtered_parent is not None
                and filtered_parent.kind in {"selection", "identity"}
                and not filtered_parent.aggregated
                and not filtered_parent.unknown
            ):
                return replace(
                    _value_at_node(
                        filtered_parent,
                        expression,
                        filtered_parent.depth + 1,
                    ),
                    row_complete=False,
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
            if self._p_depth(expression, test) is not None:
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
            aggregated=parent.aggregated or kind == "pandas_loc_boolean_mask_reducing_v1",
            unknown=parent.unknown,
            counter_node=parent.counter_node,
            call_origins=parent.call_origins,
            row_complete=parent.row_complete,
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
                    row_complete=parent.row_complete,
                )
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "astype"
            and len(call.args) == 1
            and not call.keywords
            and _closed_dtype(call.args[0], self.resolver)
        ):
            parent = self._value(call.func.value)
            if parent is not None and parent.kind in {"selection", "identity"}:
                return _value_at_node(parent, call, parent.depth + 1)
        if api in {"numpy.log", "numpy.log1p", "numpy.sqrt", "numpy.exp"}:
            if len(call.args) == 1 and not call.keywords:
                parent = self._value(call.args[0])
                if parent is not None and parent.kind in {"selection", "identity"}:
                    return _value_at_node(parent, call, parent.depth + 1)
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr in {"dropna", "sort_values", "reset_index", "rename"}
            and not any(
                keyword.arg == "inplace"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in call.keywords
            )
        ):
            parent = self._value(call.func.value)
            if parent is not None and parent.kind in {"selection", "identity"}:
                value = _value_at_node(parent, call, parent.depth + 1)
                if call.func.attr == "dropna":
                    return replace(value, row_complete=False)
                return value
        if isinstance(call.func, ast.Attribute) and call.func.attr == "drop_duplicates":
            subset: ast.expr | None = call.args[0] if len(call.args) == 1 else None
            for keyword in call.keywords:
                if keyword.arg == "subset":
                    subset = keyword.value
            keys = _closed_column_set(subset, self.resolver) if subset is not None else None
            parent = self._value(call.func.value)
            if parent is not None and keys is not None and self.unit_column in keys:
                return _Value(
                    "aggregation",
                    call,
                    root=parent.root,
                    depth=parent.depth + 1,
                    aggregated=True,
                    counter_node=call,
                    call_origins=parent.call_origins | frozenset({call}),
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

    def _result_sinks(self, test: _Test) -> list[_Sink]:
        return [
            sink
            for sink in self.sinks
            if sink.p_result_eligible
            and any(self._p_depth(payload, test) is not None for payload in sink.payloads)
        ]

    def _p_depth(self, node: ast.AST, test: _Test) -> int | None:
        return _p_derived_depth(
            node,
            test,
            self.resolver,
            self.assignments,
            output_helpers=self.output_helpers,
            output_buffers=self.output_buffers,
        )

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


def _v31_inlined_return_tuple_shape(statement: ast.Assign, target: ast.expr) -> bool:
    """Recognize only the exact H5 inlined tuple-return binding shape."""

    return bool(
        getattr(statement, "_sc_v2_return_root", False)
        and isinstance(target, ast.Tuple)
        and isinstance(statement.value, ast.Tuple)
        and 1 <= len(target.elts) <= 16
        and len(target.elts) == len(statement.value.elts)
        and len({item.id for item in target.elts if isinstance(item, ast.Name)}) == len(target.elts)
        and not any(isinstance(item, ast.Starred) for item in statement.value.elts)
    )


def _normalize_contract_domain_loops(
    *,
    scope: tuple[ast.stmt, ...],
    resolver: _Resolver,
    authorized_path: str,
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
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

    authorized_reader_names = _authorized_reader_identity_names(
        scope,
        resolver=resolver,
        authorized_path=authorized_path,
        csv_header=csv_header,
        unit_column=unit_column,
        group_column=group_column,
    )

    normalized: list[ast.stmt] = []
    for statement in comprehensions:
        if not isinstance(statement, ast.For):
            normalized.append(statement)
            continue
        bindings = _contract_domain_loop_bindings(
            statement,
            resolver,
            group_column,
            group_values,
            authorized_reader_names,
        )
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
    group_column: str,
    group_values: tuple[str, str],
    authorized_reader_names: frozenset[str],
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
    elif _observed_contract_domain_iterable(
        loop.iter,
        resolver,
        group_column,
        authorized_reader_names,
    ):
        raw = group_values
    if (
        raw is None
        or len(raw) != 2
        or not all(isinstance(item, str) for item in raw)
        or len(set(raw)) != 2
        or set(raw) != set(group_values)
    ):
        return None
    return str(raw[0]), str(raw[1])


def _observed_contract_domain_iterable(
    expression: ast.expr,
    resolver: _Resolver,
    group_column: str,
    authorized_reader_names: frozenset[str],
) -> bool:
    """Recognize the three exact H6 observed-group iterable shapes."""

    candidate = expression
    if isinstance(candidate, ast.Call) and resolver.qualified(candidate.func) in {"set", "sorted"}:
        wrapper = resolver.qualified(candidate.func)
        if len(candidate.args) != 1 or candidate.keywords:
            return False
        if wrapper in resolver.builtins_shadowed:
            return False
        candidate = candidate.args[0]
        if wrapper == "set":
            return _observed_group_column_read(
                candidate,
                resolver,
                group_column,
                authorized_reader_names,
            )
    if not (
        isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Attribute)
        and candidate.func.attr == "unique"
        and not candidate.args
        and not candidate.keywords
    ):
        return False
    return _observed_group_column_read(
        candidate.func.value,
        resolver,
        group_column,
        authorized_reader_names,
    )


def _observed_group_column_read(
    expression: ast.expr,
    resolver: _Resolver,
    group_column: str,
    authorized_reader_names: frozenset[str],
) -> bool:
    return bool(
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id in authorized_reader_names
        and resolver.string(expression.slice) == group_column
    )


def _authorized_reader_identity_names(
    statements: Sequence[ast.stmt],
    *,
    resolver: _Resolver,
    authorized_path: str,
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
) -> frozenset[str]:
    """Resolve only the authorized reader target and direct Name identity aliases."""

    definition_counts: Counter[str] = Counter(
        name for statement in statements for name in _store_names(statement)
    )
    result: set[str] = set()
    for node in _walk_statements(statements):
        if not isinstance(node, ast.Call):
            continue
        api = resolver.qualified(node.func)
        accepted = False
        if api == "pandas.read_csv" and len(node.args) == 1:
            accepted = not node.keywords or bool(
                _parse_dates_columns(
                    node,
                    resolver=resolver,
                    csv_header=csv_header,
                    forbidden={unit_column, group_column},
                )
            )
        elif api == "numpy.genfromtxt" and len(node.args) == 1:
            accepted = _literal_keywords(node.keywords) == {
                "delimiter": ",",
                "names": True,
                "dtype": None,
                "encoding": "utf-8",
            }
        if not accepted or _static_path(node.args[0], resolver) != authorized_path:
            continue
        reader_target = _assigned_name(statements, node)
        if reader_target is not None and definition_counts[reader_target] == 1:
            result.add(reader_target)

    changed = True
    while changed:
        changed = False
        for statement in statements:
            alias_target: ast.Name | None = None
            value: ast.expr | None = None
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                alias_target = statement.targets[0]
                value = statement.value
            elif (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.value is not None
            ):
                alias_target = statement.target
                value = statement.value
            if (
                alias_target is not None
                and isinstance(value, ast.Name)
                and value.id in result
                and definition_counts[alias_target.id] == 1
                and alias_target.id not in result
            ):
                result.add(alias_target.id)
                changed = True
    return frozenset(result)


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
            or api in _MT_CORRECTION_APIS
            or _dependence_api(api)
        ):
            return True
        if api in {"min", "numpy.minimum"} and any(
            isinstance(item, ast.BinOp)
            and isinstance(item.op, ast.Mult)
            and any(isinstance(child, ast.Subscript) for child in ast.walk(item))
            for argument in node.args
            for item in ast.walk(argument)
        ):
            return True
    if target is not None:
        names = _store_names(target)
        for item in statements[statement_index + 1 :]:
            for descendant in ast.walk(item):
                if not isinstance(descendant, ast.Call):
                    continue
                api = resolver.qualified(descendant.func)
                if api not in _POSITIVE_APIS and api not in _MT_CORRECTION_APIS:
                    continue
                if any(
                    _reads_name(argument, name)
                    for argument in (
                        *descendant.args,
                        *(keyword.value for keyword in descendant.keywords),
                    )
                    for name in names
                ):
                    return True
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
                or node.id in resolver.tables
                or node.id in resolver.dictionaries
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
        isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node is not helper
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
        | set(resolver.tables)
        | set(resolver.dictionaries)
        | set(resolver.file_parents)
        | set(resolver.accepted_names)
        | set(resolver.bound_names)
        | _UNSHADOWED_BUILTINS
        | _V2_EXCEPTION_NAMES
        | set(helpers)
        | {"__file__"}
    )
    lambda_local_loads = _closed_helper_lambda_local_loads(helper, module_names)
    if lambda_local_loads is None:
        return None, "helper-closure-or-nested-definition-unsupported"
    for node in _walk_helper_runtime(helper):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and id(node) not in lambda_local_loads
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


def _closed_helper_lambda_local_loads(
    helper: ast.FunctionDef,
    module_names: set[str],
) -> set[int] | None:
    """Return lambda-parameter load nodes for exact closed helper-local lambdas."""

    result: set[int] = set()
    lambdas = [node for node in _walk_helper_runtime(helper) if isinstance(node, ast.Lambda)]
    for expression in lambdas:
        args = expression.args
        if (
            args.posonlyargs
            or args.kwonlyargs
            or args.vararg is not None
            or args.kwarg is not None
            or args.defaults
            or args.kw_defaults
        ):
            return None
        parameters = {item.arg for item in args.args}
        if any(
            isinstance(
                node,
                (
                    ast.Lambda,
                    ast.NamedExpr,
                    ast.FunctionDef,
                    ast.ClassDef,
                    ast.Await,
                    ast.Yield,
                    ast.YieldFrom,
                    ast.Store,
                ),
            )
            for node in ast.walk(expression.body)
        ):
            return None
        loaded = [
            node
            for node in ast.walk(expression.body)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        ]
        if any(node.id not in parameters and node.id not in module_names for node in loaded):
            return None
        result.update(id(node) for node in loaded if node.id in parameters)
    return result


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
            for expression in _guard_assignment_values(statements)
        ):
            continue
        for call in (item for item in _walk_statements(statements) if isinstance(item, ast.Call)):
            api = resolver.qualified(call.func)
            pandas_reducer = bool(
                isinstance(call.func, ast.Attribute)
                and call.func.attr
                in {
                    "mean",
                    "nanmean",
                    "std",
                    "nanstd",
                    "median",
                    "nanmedian",
                    "sum",
                    "nansum",
                    "count",
                    "quantile",
                    "percentile",
                }
            )
            builtin_count = api in {"sum", "len"}
            if api not in _V2_RESAMPLING_REDUCERS and not pandas_reducer and not builtin_count:
                continue
            if not (_loaded_names(call) & derived):
                continue
            if _v3_origin_reaches_sink(
                call,
                statements,
                sinks,
                values,
                assignments,
            ):
                return origin
    return None


def _guard_assignment_values(statements: Sequence[ast.stmt]) -> tuple[ast.expr, ...]:
    """Return every assignment value without collapsing same-name helper scopes."""

    result: list[ast.expr] = []
    for node in _walk_statements(statements):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr, ast.AugAssign, ast.Return)):
            value = node.value
            if value is not None:
                result.append(value)
    return tuple(result)


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
    """Follow guard-only name/member/destructuring and helper-binding edges."""

    derived = set(seeds)
    module_helpers = {
        statement.name: statement
        for statement in statements
        if isinstance(statement, ast.FunctionDef)
    }
    classes = {
        statement.name: statement for statement in statements if isinstance(statement, ast.ClassDef)
    }
    instance_classes: dict[str, ast.ClassDef] = {}
    for statement in statements:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id in classes
        ):
            continue
        instance_classes[statement.targets[0].id] = classes[statement.value.func.id]

    def called_helper(call: ast.Call) -> tuple[ast.FunctionDef, bool] | None:
        if isinstance(call.func, ast.Name) and call.func.id in module_helpers:
            return module_helpers[call.func.id], False
        if not isinstance(call.func, ast.Attribute):
            return None
        owner: ast.ClassDef | None = None
        if isinstance(call.func.value, ast.Name):
            owner = instance_classes.get(call.func.value.id)
        elif isinstance(call.func.value, ast.Call) and isinstance(call.func.value.func, ast.Name):
            owner = classes.get(call.func.value.func.id)
        if owner is None:
            return None
        matches = [
            item
            for item in owner.body
            if isinstance(item, ast.FunctionDef) and item.name == call.func.attr
        ]
        return (matches[0], True) if len(matches) == 1 else None

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
        for call in (node for node in _walk_statements(statements) if isinstance(node, ast.Call)):
            helper_binding = called_helper(call)
            if helper_binding is not None:
                helper, is_method = helper_binding
                parameters = [item.arg for item in helper.args.args]
                if is_method and parameters:
                    parameters = parameters[1:]
                actuals: dict[str, ast.expr] = {
                    name: argument for name, argument in zip(parameters, call.args, strict=False)
                }
                actuals.update(
                    {
                        keyword.arg: keyword.value
                        for keyword in call.keywords
                        if keyword.arg in parameters
                    }
                )
                for name, actual in actuals.items():
                    if name not in derived and _loaded_names(actual) & derived:
                        derived.add(name)
                        changed = True
                if any(
                    isinstance(item, ast.Return)
                    and item.value is not None
                    and _loaded_names(item.value) & derived
                    for item in _walk_statements(helper.body)
                ):
                    call_target = _assigned_target(statements, call)
                    for name in _guard_store_names(call_target):
                        if name not in derived:
                            derived.add(name)
                            changed = True
            if not (
                isinstance(call.func, ast.Attribute)
                and call.func.attr in {"append", "extend"}
                and any(_loaded_names(argument) & derived for argument in call.args)
            ):
                continue
            root = _root_name(call.func.value)
            if root is not None and root not in derived:
                derived.add(root)
                changed = True
    return derived


def _v2_iterator_cardinality(node: ast.expr, resolver: _Resolver) -> int | None:
    if isinstance(node, (ast.Tuple, ast.List)):
        return len(node.elts)
    if not isinstance(node, ast.Call):
        return None
    api = resolver.qualified(node.func)
    if api in {"itertools.combinations", "itertools.permutations"}:
        if len(node.args) != 2 or node.keywords:
            return None
        source = resolver.sequence(node.args[0])
        width = _closed_int(node.args[1], resolver.literals)
        if source is None or width is None or width < 0 or width > len(source):
            return None
        if api == "itertools.combinations":
            return math.comb(len(source), width)
        return math.perm(len(source), width)
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
        if not dimensions or any(item is not None and item < 0 for item in dimensions):
            return None
        resolved = [int(item) for item in dimensions if item is not None]
        if any(item >= _V2_RESAMPLING_MIN_TRIPS for item in resolved):
            return max(resolved)
        if len(resolved) == len(dimensions):
            return math.prod(resolved)
        return None
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
        row_complete=value.row_complete,
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


class _SourceEnvelopeExceeded(ValueError):
    """The closed source byte/node ceiling was exceeded."""


def _bounded_parse(content: bytes) -> ast.Module:
    if len(content) > _SOURCE_BYTE_MAX:
        raise _SourceEnvelopeExceeded("source outside byte envelope")
    if content.startswith(b"\xef\xbb\xbf") or b"\x00" in content:
        raise ValueError("source outside byte envelope")
    text = content.decode("utf-8", errors="strict")
    tree = ast.parse(text, filename="analysis.py", mode="exec", type_comments=True)
    if sum(1 for _ in ast.walk(tree)) > _AST_NODE_MAX:
        raise _SourceEnvelopeExceeded("source outside AST envelope")
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


def _call_chain_root(call: ast.Call, resolver: _Resolver) -> str | None:
    api = resolver.qualified(call.func)
    if api is not None:
        return api
    node: ast.expr = call.func
    while isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Call):
            return _call_chain_root(node.value, resolver)
        node = node.value
    return resolver.qualified(node)


def _v3_dependence_guard(statements: Sequence[ast.stmt], resolver: _Resolver) -> ast.Call | None:
    grouping_keywords = {"group_data", "groups", "re_formula", "cluster"}
    assignments = _assignment_expressions(statements)
    for call in sorted(
        (node for node in _walk_statements(statements) if isinstance(node, ast.Call)),
        key=_position,
    ):
        api = resolver.qualified(call.func)
        root = _call_chain_root(call, resolver)
        if _dependence_api(api) or _dependence_api(root):
            return call
        if not (isinstance(call.func, ast.Attribute) and call.func.attr == "fit"):
            continue
        constructors = [node for node in ast.walk(call.func.value) if isinstance(node, ast.Call)]
        if isinstance(call.func.value, ast.Name):
            assigned = assignments.get(call.func.value.id)
            if isinstance(assigned, ast.Call):
                constructors.append(assigned)
        if any(
            any(keyword.arg in grouping_keywords for keyword in constructor.keywords)
            for constructor in constructors
        ):
            return call
        if any(
            (candidate := _call_chain_root(constructor, resolver)) is not None
            and _prefix_hit(candidate, ("statsmodels",))
            for constructor in constructors
        ) and any(
            keyword.arg == "cov_type"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "cluster"
            for keyword in call.keywords
        ):
            return call
    return None


def _v3_statistics_guard(statements: Sequence[ast.stmt], resolver: _Resolver) -> ast.Call | None:
    for call in sorted(
        (node for node in _walk_statements(statements) if isinstance(node, ast.Call)),
        key=_position,
    ):
        api = resolver.qualified(call.func)
        root = _call_chain_root(call, resolver)
        matched = next(
            (
                candidate
                for candidate in (api, root)
                if candidate is not None and _prefix_hit(candidate, _STATISTICS_PREFIXES)
            ),
            None,
        )
        if matched is None or api in _POSITIVE_APIS:
            continue
        if (
            api == "scipy.stats.sem"
            and len(call.args) == 1
            and all(keyword.arg in {"axis", "ddof", "nan_policy"} for keyword in call.keywords)
        ):
            continue
        if api == "scipy.stats.t.ppf" and len(call.args) == 2 and not call.keywords:
            continue
        return call
    return None


def _v3_syntactic_test_count(statements: Sequence[ast.stmt], resolver: _Resolver) -> int:
    return sum(
        1
        for node in _walk_statements(statements)
        if isinstance(node, ast.Call) and resolver.qualified(node.func) in _POSITIVE_APIS
    )


def _closed_column_set(node: ast.expr, resolver: _Resolver) -> set[str] | None:
    value = resolver.string(node)
    if value is not None:
        return {value}
    sequence = resolver.sequence(node)
    if sequence is None or any(not isinstance(item, str) for item in sequence):
        return None
    return {str(item) for item in sequence}


def _v3_unit_summary_guard(
    statements: Sequence[ast.stmt],
    *,
    resolver: _Resolver,
    unit_column: str,
    values: Mapping[str, _Value],
) -> ast.AST | None:
    assignments = _assignment_expressions(statements)
    sinks = _registered_sinks(statements, resolver)
    reducer_names = (
        _GROUP_REDUCERS
        | _FRAME_REDUCERS
        | {
            "agg",
            "aggregate",
            "apply",
            "transform",
            "value_counts",
        }
    )
    calls = sorted(
        (node for node in _walk_statements(statements) if isinstance(node, ast.Call)),
        key=_position,
    )
    for origin in calls:
        unit_keyed = False
        if isinstance(origin.func, ast.Attribute) and origin.func.attr == "groupby":
            if origin.args:
                keys = _closed_column_set(origin.args[0], resolver)
                unit_keyed = keys is not None and unit_column in keys
        elif isinstance(origin.func, ast.Attribute) and origin.func.attr == "drop_duplicates":
            subset: ast.expr | None = origin.args[0] if origin.args else None
            for keyword in origin.keywords:
                if keyword.arg == "subset":
                    subset = keyword.value
            keys = _closed_column_set(subset, resolver) if subset is not None else None
            unit_keyed = keys is not None and unit_column in keys
        if not unit_keyed:
            continue
        if (
            isinstance(origin.func, ast.Attribute)
            and origin.func.attr == "groupby"
            and _v3_count_only_unit_groupby(origin, calls, statements)
        ):
            continue
        reduced = any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr in reducer_names
            and _v31_groupby_terminal_reads_origin(call, origin, statements)
            for call in calls
        )
        if not reduced and not (
            isinstance(origin.func, ast.Attribute) and origin.func.attr == "drop_duplicates"
        ):
            continue
        if _v3_origin_reaches_sink(origin, statements, sinks, values, assignments):
            return origin

    for node in _walk_statements(statements):
        if not isinstance(node, (ast.For, ast.DictComp)):
            continue
        iterator = node.iter if isinstance(node, ast.For) else node.generators[0].iter
        if not _v3_unit_iterator(iterator, resolver, unit_column):
            continue
        body_nodes: Sequence[ast.AST]
        if isinstance(node, ast.For):
            body_nodes = node.body
        else:
            body_nodes = (node.value,)
        reducers = [
            call
            for body in body_nodes
            for call in ast.walk(body)
            if isinstance(call, ast.Call)
            and (
                resolver.qualified(call.func) in _NUMPY_REDUCERS
                or (isinstance(call.func, ast.Attribute) and call.func.attr in reducer_names)
            )
        ]
        if reducers and any(
            _v3_origin_reaches_sink(call, statements, sinks, values, assignments)
            for call in reducers
        ):
            return node
    return None


def _v3_count_only_unit_groupby(
    origin: ast.Call,
    calls: Sequence[ast.Call],
    statements: Sequence[ast.stmt],
) -> bool:
    """Recognize the exact S5 count-only groupby terminal chain."""

    reachable = [
        call
        for call in calls
        if call is not origin
        and isinstance(call.func, ast.Attribute)
        and _v31_groupby_terminal_reads_origin(call, origin, statements)
    ]
    attributes = [call.func.attr for call in reachable if isinstance(call.func, ast.Attribute)]
    return bool(
        attributes
        and any(attribute in {"size", "count"} for attribute in attributes)
        and all(attribute in {"size", "count", "unique", "tolist"} for attribute in attributes)
    )


def _v31_groupby_terminal_reads_origin(
    call: ast.Call,
    origin: ast.Call,
    statements: Sequence[ast.stmt],
) -> bool:
    if not isinstance(call.func, ast.Attribute):
        return False
    if any(node is origin for node in ast.walk(call.func.value)):
        return True
    alias = _assigned_name(statements, origin)
    if alias is None:
        return False
    if sum(name == alias for statement in statements for name in _store_names(statement)) != 1:
        return False
    return _root_name(call.func.value) == alias


def _v3_origin_reaches_sink(
    origin: ast.Call,
    statements: Sequence[ast.stmt],
    sinks: Sequence[_Sink],
    values: Mapping[str, _Value],
    assignments: Mapping[str, ast.expr],
) -> bool:
    if _call_reaches_sink(origin, sinks, values, assignments):
        return True
    if _guard_origin_reaches_registered_sink(origin, statements, sinks):
        return True
    if _guard_origin_reaches_output_buffer(origin, statements, sinks):
        return True
    target = _assigned_target(statements, origin)
    if target is None:
        return False
    derived = _guard_name_closure(statements, _guard_store_names(target))
    return any(_loaded_names(payload) & derived for sink in sinks for payload in sink.payloads)


def _guard_origin_reaches_output_buffer(
    origin: ast.Call,
    statements: Sequence[ast.stmt],
    sinks: Sequence[_Sink],
) -> bool:
    """Follow an S5 origin into an H7 helper-local append/join buffer."""

    helpers = {
        statement.name: statement
        for statement in statements
        if isinstance(statement, ast.FunctionDef)
    }
    for helper in helpers.values():
        if not any(node is origin for statement in helper.body for node in ast.walk(statement)):
            continue
        buffers = _closed_output_buffers(helper.body)
        if not buffers:
            continue
        helper_calls = [
            node
            for node in _walk_statements(statements)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == helper.name
        ]
        if any(
            any(node is call for node in ast.walk(payload))
            for sink in sinks
            for payload in sink.payloads
            for call in helper_calls
        ):
            return True
    return False


def _guard_origin_reaches_registered_sink(
    origin: ast.AST,
    statements: Sequence[ast.stmt],
    sinks: Sequence[_Sink],
) -> bool:
    """Follow an S2/S5 payload through helper returns and literal members."""

    helpers = {
        statement.name: statement
        for statement in statements
        if isinstance(statement, ast.FunctionDef)
    }
    for sink in sinks:
        scope = _guard_enclosing_scope(statements, sink.call)
        for payload in sink.payloads:
            if _guard_expression_carries_origin(
                payload,
                origin=origin,
                member_path=(),
                scope=scope,
                module_scope=statements,
                helpers=helpers,
                bindings={},
                seen=frozenset(),
            ):
                return True
    return False


_GuardBinding = tuple[ast.expr, Sequence[ast.stmt], Mapping[str, "_GuardBinding"]]


def _guard_expression_carries_origin(
    expression: ast.AST,
    *,
    origin: ast.AST,
    member_path: tuple[str | int, ...],
    scope: Sequence[ast.stmt],
    module_scope: Sequence[ast.stmt],
    helpers: Mapping[str, ast.FunctionDef],
    bindings: Mapping[str, _GuardBinding],
    seen: frozenset[tuple[int, tuple[str | int, ...], int]],
) -> bool:
    marker = (id(expression), member_path, id(scope))
    if marker in seen:
        return False
    next_seen = seen | {marker}

    if isinstance(expression, ast.Subscript):
        member = _literal_subscript_member(expression.slice)
        if member is None:
            return False
        return _guard_expression_carries_origin(
            expression.value,
            origin=origin,
            member_path=(member, *member_path),
            scope=scope,
            module_scope=module_scope,
            helpers=helpers,
            bindings=bindings,
            seen=next_seen,
        )

    if isinstance(expression, ast.Name):
        binding = bindings.get(expression.id)
        if binding is not None:
            actual, actual_scope, actual_bindings = binding
            if _guard_expression_carries_origin(
                actual,
                origin=origin,
                member_path=member_path,
                scope=actual_scope,
                module_scope=module_scope,
                helpers=helpers,
                bindings=actual_bindings,
                seen=next_seen,
            ):
                return True
        for source, prefix in _guard_name_sources(scope, expression.id, member_path):
            if _guard_expression_carries_origin(
                source,
                origin=origin,
                member_path=prefix,
                scope=scope,
                module_scope=module_scope,
                helpers=helpers,
                bindings=bindings,
                seen=next_seen,
            ):
                return True
        return False

    if isinstance(expression, (ast.Dict, ast.Tuple, ast.List)):
        members = _guard_literal_members(expression)
        if member_path:
            member_expression = members.get(member_path[0])
            if member_expression is None:
                return False
            return _guard_expression_carries_origin(
                member_expression,
                origin=origin,
                member_path=member_path[1:],
                scope=scope,
                module_scope=module_scope,
                helpers=helpers,
                bindings=bindings,
                seen=next_seen,
            )
        return any(
            _guard_expression_carries_origin(
                member,
                origin=origin,
                member_path=(),
                scope=scope,
                module_scope=module_scope,
                helpers=helpers,
                bindings=bindings,
                seen=next_seen,
            )
            for member in members.values()
        )

    if isinstance(expression, ast.Call):
        helper = helpers.get(expression.func.id) if isinstance(expression.func, ast.Name) else None
        if helper is not None:
            helper_bindings = _guard_helper_bindings(
                helper,
                expression,
                caller_scope=scope,
                caller_bindings=bindings,
            )
            return any(
                return_node.value is not None
                and _guard_expression_carries_origin(
                    return_node.value,
                    origin=origin,
                    member_path=member_path,
                    scope=helper.body,
                    module_scope=module_scope,
                    helpers=helpers,
                    bindings=helper_bindings,
                    seen=next_seen,
                )
                for return_node in _guard_scope_returns(helper.body)
            )

    if member_path:
        return False
    if expression is origin:
        return True
    return any(
        _guard_expression_carries_origin(
            child,
            origin=origin,
            member_path=(),
            scope=scope,
            module_scope=module_scope,
            helpers=helpers,
            bindings=bindings,
            seen=next_seen,
        )
        for child in ast.iter_child_nodes(expression)
    )


def _guard_name_sources(
    scope: Sequence[ast.stmt],
    name: str,
    member_path: tuple[str | int, ...],
) -> tuple[tuple[ast.expr, tuple[str | int, ...]], ...]:
    result: list[tuple[ast.expr, tuple[str | int, ...]]] = []
    for node in _guard_scope_nodes(scope):
        value: ast.expr | None = None
        targets: Sequence[ast.expr] = ()
        if isinstance(node, ast.Assign):
            value = node.value
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            value = node.value
            targets = (node.target,)
        elif isinstance(node, ast.NamedExpr):
            value = node.value
            targets = (node.target,)
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                result.append((value, member_path))
                continue
            destructure = _guard_destructure_path(target, name)
            if destructure is not None:
                result.append((value, (*destructure, *member_path)))
                continue
            if isinstance(target, ast.Subscript):
                member = _literal_subscript_member(target.slice)
                if _root_name(target.value) != name or member is None:
                    continue
                if not member_path or member_path[0] != member:
                    continue
                result.append((value, member_path[1:]))
    return tuple(result)


def _guard_destructure_path(
    target: ast.expr,
    name: str,
    prefix: tuple[str | int, ...] = (),
) -> tuple[str | int, ...] | None:
    if isinstance(target, ast.Name):
        return prefix if target.id == name else None
    if isinstance(target, (ast.Tuple, ast.List)):
        for index, item in enumerate(target.elts):
            found = _guard_destructure_path(item, name, (*prefix, index))
            if found is not None:
                return found
    return None


def _guard_literal_members(
    expression: ast.Dict | ast.Tuple | ast.List,
) -> dict[str | int, ast.expr]:
    if isinstance(expression, ast.Dict):
        result: dict[str | int, ast.expr] = {}
        for key, value in zip(expression.keys, expression.values, strict=True):
            if key is None or (member := _literal_container_key(key)) is None:
                continue
            result[member] = value
        return result
    return {index: value for index, value in enumerate(expression.elts)}


def _guard_helper_bindings(
    helper: ast.FunctionDef,
    call: ast.Call,
    *,
    caller_scope: Sequence[ast.stmt],
    caller_bindings: Mapping[str, _GuardBinding],
) -> dict[str, _GuardBinding]:
    parameters = [*helper.args.posonlyargs, *helper.args.args]
    result: dict[str, _GuardBinding] = {}
    for parameter, actual in zip(parameters, call.args, strict=False):
        result[parameter.arg] = (actual, caller_scope, caller_bindings)
    parameter_names = {parameter.arg for parameter in parameters}
    for keyword in call.keywords:
        if keyword.arg in parameter_names:
            result[str(keyword.arg)] = (keyword.value, caller_scope, caller_bindings)
    defaults = [None] * (len(parameters) - len(helper.args.defaults)) + list(helper.args.defaults)
    for parameter, default in zip(parameters, defaults, strict=True):
        if parameter.arg not in result and default is not None:
            result[parameter.arg] = (default, caller_scope, caller_bindings)
    return result


def _guard_scope_nodes(scope: Sequence[ast.stmt]) -> tuple[ast.AST, ...]:
    result: list[ast.AST] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.stmt):
            result.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in scope:
        visit(statement)
    return tuple(result)


def _guard_scope_returns(scope: Sequence[ast.stmt]) -> tuple[ast.Return, ...]:
    return tuple(node for node in _guard_scope_nodes(scope) if isinstance(node, ast.Return))


def _guard_enclosing_scope(
    statements: Sequence[ast.stmt],
    node: ast.AST,
) -> Sequence[ast.stmt]:
    for statement in statements:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not _inside_any(node, statement.body):
            continue
        nested = _guard_enclosing_scope(statement.body, node)
        return nested
    return statements


def _v3_unit_iterator(node: ast.expr, resolver: _Resolver, unit_column: str) -> bool:
    if isinstance(node, ast.Call) and resolver.qualified(node.func) == "set":
        return bool(
            len(node.args) == 1
            and not node.keywords
            and _v3_unit_series(node.args[0], resolver, unit_column)
        )
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "unique"
        and not node.args
        and not node.keywords
    ):
        return _v3_unit_series(node.func.value, resolver, unit_column)
    return False


def _v3_unit_series(node: ast.expr, resolver: _Resolver, unit_column: str) -> bool:
    return bool(
        isinstance(node, ast.Subscript)
        and (column := _literal_subscript_member(node.slice)) is not None
        and resolver.string(node.slice) == unit_column
        and isinstance(column, str)
    )


def _v3_call_reachable(statements: Sequence[ast.stmt], target: ast.Call) -> bool:
    def block(items: Sequence[ast.stmt], live: bool) -> tuple[bool, bool]:
        current = live
        for statement in items:
            if not current:
                if any(node is target for node in ast.walk(statement)):
                    return False, False
                continue
            if isinstance(statement, ast.If):
                literal = statement.test.value if isinstance(statement.test, ast.Constant) else None
                if literal is not None and isinstance(literal, (bool, int, float)):
                    selected = statement.body if bool(literal) else statement.orelse
                    rejected = statement.orelse if bool(literal) else statement.body
                    if any(node is target for item in rejected for node in ast.walk(item)):
                        return False, current
                    found, _ = block(selected, current)
                    if found:
                        return True, current
                    continue
                for branch in (statement.body, statement.orelse):
                    found, _ = block(branch, current)
                    if found:
                        return True, current
                continue
            if isinstance(statement, ast.While):
                if isinstance(statement.test, ast.Constant) and not bool(statement.test.value):
                    if any(node is target for item in statement.body for node in ast.walk(item)):
                        return False, current
                    found, _ = block(statement.orelse, current)
                    if found:
                        return True, current
                    continue
            if any(node is target for node in ast.walk(statement)):
                return True, current
            if isinstance(statement, (ast.Return, ast.Raise)):
                current = False
        return False, current

    return block(statements, True)[0]


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


def _closed_output_buffers(statements: Sequence[ast.stmt]) -> dict[str, tuple[ast.expr, ...]]:
    """Return exact local `[]`/append/newline-join output buffers."""

    result: dict[str, tuple[ast.expr, ...]] = {}
    stores: defaultdict[str, int] = defaultdict(int)
    for node in _walk_statements(statements):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            stores[node.id] += 1
    for statement in _walk_statements(statements):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.List)
            and not statement.value.elts
            and stores[statement.targets[0].id] == 1
        ):
            continue
        name = statement.targets[0].id
        append_calls = [
            node
            for node in _walk_statements(statements)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == name
            and node.func.attr == "append"
        ]
        receiver_calls = [
            node
            for node in _walk_statements(statements)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == name
        ]
        joins = [
            node
            for node in _walk_statements(statements)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and isinstance(node.func.value, ast.Constant)
            and node.func.value.value == "\n"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == name
        ]
        if (
            append_calls
            and len(receiver_calls) == len(append_calls)
            and all(len(call.args) == 1 and not call.keywords for call in append_calls)
            and joins
        ):
            result[name] = tuple(call.args[0] for call in append_calls)
    return result


class _OutputParameterTransformer(ast.NodeTransformer):
    def __init__(self, bindings: Mapping[str, ast.expr]) -> None:
        self.bindings = bindings

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Load) and node.id in self.bindings:
            return ast.copy_location(copy.deepcopy(self.bindings[node.id]), node)
        return node


def _output_helper_buffer_payloads(
    call: ast.Call,
    helper: ast.FunctionDef,
) -> tuple[ast.expr, ...] | None:
    parameters = [item.arg for item in helper.args.args]
    if (
        helper.args.posonlyargs
        or helper.args.kwonlyargs
        or helper.args.vararg is not None
        or helper.args.kwarg is not None
        or helper.args.defaults
        or helper.args.kw_defaults
        or len(call.args) != len(parameters)
        or call.keywords
    ):
        return None
    body = [statement for statement in helper.body if not _is_docstring(statement)]
    if not body or not isinstance(body[-1], ast.Return) or body[-1].value is None:
        return None
    returned = body[-1].value
    if not (
        isinstance(returned, ast.Call)
        and isinstance(returned.func, ast.Attribute)
        and returned.func.attr == "join"
        and isinstance(returned.func.value, ast.Constant)
        and returned.func.value.value == "\n"
        and len(returned.args) == 1
        and not returned.keywords
        and isinstance(returned.args[0], ast.Name)
    ):
        return None
    buffers = _closed_output_buffers(body)
    payloads = buffers.get(returned.args[0].id)
    if payloads is None:
        return None
    transformer = _OutputParameterTransformer(dict(zip(parameters, call.args, strict=True)))
    result: list[ast.expr] = []
    for payload in payloads:
        transformed = transformer.visit(copy.deepcopy(payload))
        assert isinstance(transformed, ast.expr)
        result.append(transformed)
    return tuple(result)


def _p_derived_depth(
    node: ast.AST,
    test: _Test,
    resolver: _Resolver,
    assignments: Mapping[str, ast.expr],
    seen: frozenset[str] = frozenset(),
    *,
    output_helpers: Mapping[str, ast.FunctionDef] | None = None,
    output_buffers: Mapping[str, tuple[ast.expr, ...]] | None = None,
) -> int | None:
    member = _container_member_expression(node, assignments)
    if member is not None:
        depth = _p_derived_depth(
            member,
            test,
            resolver,
            assignments,
            seen,
            output_helpers=output_helpers,
            output_buffers=output_buffers,
        )
        return depth + 1 if depth is not None else None
    if isinstance(node, ast.Name):
        if test.p_name is not None and node.id == test.p_name:
            return 1
        if node.id in seen or node.id == test.result_name:
            return None
        assigned = assignments.get(node.id)
        if assigned is None:
            return None
        depth = _p_derived_depth(
            assigned,
            test,
            resolver,
            assignments,
            seen | {node.id},
            output_helpers=output_helpers,
            output_buffers=output_buffers,
        )
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
            if (
                depth := _p_derived_depth(
                    expression,
                    test,
                    resolver,
                    assignments,
                    seen,
                    output_helpers=output_helpers,
                    output_buffers=output_buffers,
                )
            )
            is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.FormattedValue):
        return _p_derived_depth(
            node.value,
            test,
            resolver,
            assignments,
            seen,
            output_helpers=output_helpers,
            output_buffers=output_buffers,
        )
    if isinstance(node, ast.JoinedStr):
        depths = [
            depth
            for item in node.values
            if isinstance(item, ast.FormattedValue)
            if (
                depth := _p_derived_depth(
                    item,
                    test,
                    resolver,
                    assignments,
                    seen,
                    output_helpers=output_helpers,
                    output_buffers=output_buffers,
                )
            )
            is not None
        ]
        return max(depths, default=None)
    if isinstance(node, ast.BinOp):
        if not (
            isinstance(node.op, ast.Mod)
            and isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
        ):
            return None
        return _p_derived_depth(
            node.right,
            test,
            resolver,
            assignments,
            seen,
            output_helpers=output_helpers,
            output_buffers=output_buffers,
        )
    if isinstance(node, ast.Call):
        api = resolver.qualified(node.func)
        if api in {"str", "float"} and len(node.args) == 1 and not node.keywords:
            depth = _p_derived_depth(
                node.args[0],
                test,
                resolver,
                assignments,
                seen,
                output_helpers=output_helpers,
                output_buffers=output_buffers,
            )
            return depth + 1 if depth is not None else None
        if api == "round" and not node.keywords and len(node.args) in {1, 2}:
            if len(node.args) == 2 and not (
                isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, int)
            ):
                return None
            depth = _p_derived_depth(
                node.args[0],
                test,
                resolver,
                assignments,
                seen,
                output_helpers=output_helpers,
                output_buffers=output_buffers,
            )
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
                if (
                    depth := _p_derived_depth(
                        argument,
                        test,
                        resolver,
                        assignments,
                        seen,
                        output_helpers=output_helpers,
                        output_buffers=output_buffers,
                    )
                )
                is not None
            ]
            return max(depths, default=None)
        if (
            output_buffers is not None
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and isinstance(node.func.value, ast.Constant)
            and node.func.value.value == "\n"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Name)
            and (payloads := output_buffers.get(node.args[0].id)) is not None
        ):
            depths = [
                depth
                for payload in payloads
                if (
                    depth := _p_derived_depth(
                        payload,
                        test,
                        resolver,
                        assignments,
                        seen,
                        output_helpers=output_helpers,
                        output_buffers=output_buffers,
                    )
                )
                is not None
            ]
            return max(depths, default=None)
        if (
            output_helpers is not None
            and isinstance(node.func, ast.Name)
            and (helper := output_helpers.get(node.func.id)) is not None
            and (payloads := _output_helper_buffer_payloads(node, helper)) is not None
        ):
            depths = [
                depth
                for payload in payloads
                if (
                    depth := _p_derived_depth(
                        payload,
                        test,
                        resolver,
                        assignments,
                        seen,
                        output_helpers=output_helpers,
                        output_buffers=output_buffers,
                    )
                )
                is not None
            ]
            return max(depths, default=None)
        if (
            output_helpers is not None
            and isinstance(node.func, ast.Name)
            and (helper := output_helpers.get(node.func.id)) is not None
            and len(node.args) == 1
            and not node.keywords
            and _pure_output_helper_parameter(helper) is not None
        ):
            depth = _p_derived_depth(
                node.args[0],
                test,
                resolver,
                assignments,
                seen,
                output_helpers=output_helpers,
                output_buffers=output_buffers,
            )
            return depth + 1 if depth is not None else None
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


def _pure_output_helper_parameter(helper: ast.FunctionDef) -> str | None:
    """Return the sole parameter for one closed Return/If output formatter."""

    args = helper.args
    if (
        len(args.args) != 1
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg is not None
        or args.kwarg is not None
        or args.defaults
        or args.kw_defaults
        or helper.decorator_list
    ):
        return None
    body = [statement for statement in helper.body if not _is_docstring(statement)]
    if not body or not isinstance(body[-1], ast.Return):
        return None
    parameter = args.args[0].arg
    expressions: list[ast.expr] = []

    def collect(statements: Sequence[ast.stmt]) -> bool:
        for statement in statements:
            if isinstance(statement, ast.Return):
                if statement.value is None:
                    return False
                expressions.append(statement.value)
                continue
            if isinstance(statement, ast.If):
                expressions.append(statement.test)
                if not collect(statement.body) or not collect(statement.orelse):
                    return False
                continue
            return False
        return True

    if not collect(body):
        return None
    allowed = (
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.IfExp,
        ast.Compare,
        ast.BinOp,
        ast.UnaryOp,
        ast.BoolOp,
        ast.operator,
        ast.unaryop,
        ast.boolop,
        ast.cmpop,
    )
    nodes = tuple(node for expression in expressions for node in ast.walk(expression))
    if any(not isinstance(node, allowed) for node in nodes):
        return None
    loaded = {
        node.id for node in nodes if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return parameter if loaded == {parameter} else None


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
        unresolved_threshold_names = _module_decision_threshold_names(mains[0])
        setup = tuple(
            item
            for item in body
            if isinstance(item, (ast.Import, ast.ImportFrom))
            or _module_setup_assignment(item, main_loads)
            or _module_unresolved_threshold_assignment(item, unresolved_threshold_names)
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


def _module_decision_threshold_names(node: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for comparison in ast.walk(node):
        if not (
            isinstance(comparison, ast.Compare)
            and len(comparison.ops) == 1
            and len(comparison.comparators) == 1
        ):
            continue
        pairs = ((comparison.left, comparison.comparators[0]),)
        for possible_threshold, possible_p in (*pairs, *((right, left) for left, right in pairs)):
            if isinstance(possible_threshold, ast.Name) and any(
                isinstance(item, ast.Attribute) and item.attr == "pvalue"
                for item in ast.walk(possible_p)
            ):
                names.add(possible_threshold.id)
    return names


def _module_unresolved_threshold_assignment(node: ast.stmt, names: set[str]) -> bool:
    target, value = _mt_setup_target_value(node)
    return bool(
        target is not None and target.id in names and isinstance(value, (ast.BinOp, ast.Call))
    )


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
    target, value = _mt_setup_target_value(node)
    if target is None or value is None:
        return False
    if isinstance(value, ast.Constant):
        return True
    if isinstance(value, (ast.Tuple, ast.List)):
        return bool(
            _closed_sequence_elements(value.elts) is not None or _mt_closed_table(value) is not None
        )
    if isinstance(value, ast.Dict) and _mt_closed_dictionary(value) is not None:
        return True
    if _file_path_expression_syntax(value):
        return True
    return target.id not in relevant_names and _pure_module_expression(value)


def _mt_setup_target_value(node: ast.stmt) -> tuple[ast.Name | None, ast.expr | None]:
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0], node.value
    if (
        isinstance(node, ast.AnnAssign)
        and node.simple == 1
        and isinstance(node.target, ast.Name)
        and node.value is not None
        and _mt_closed_annotation(node.annotation)
    ):
        return node.target, node.value
    return None, None


def _mt_closed_annotation(node: ast.expr) -> bool:
    admitted = (
        ast.Name,
        ast.Attribute,
        ast.Subscript,
        ast.Tuple,
        ast.List,
        ast.Constant,
        ast.Load,
        ast.BinOp,
        ast.BitOr,
    )
    return bool(
        all(isinstance(item, admitted) for item in ast.walk(node))
        and all(
            not isinstance(item, ast.BinOp) or isinstance(item.op, ast.BitOr)
            for item in ast.walk(node)
        )
    )


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


def _mt_closed_scalar(node: ast.expr) -> object | None:
    if not isinstance(node, ast.Constant) or isinstance(node.value, complex):
        return None
    value = node.value
    if isinstance(value, str):
        return (
            value if value and len(value.encode("utf-8")) <= 128 and "\x00" not in value else None
        )
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value if value is None or isinstance(value, (int, bool)) else None


def _mt_closed_table(node: ast.List | ast.Tuple) -> tuple[tuple[object, ...], ...] | None:
    if not 1 <= len(node.elts) <= 16:
        return None
    rows: list[tuple[object, ...]] = []
    for item in node.elts:
        if not isinstance(item, (ast.List, ast.Tuple)) or not 1 <= len(item.elts) <= 8:
            return None
        values: list[object] = []
        for element in item.elts:
            value = _mt_closed_scalar(element)
            if value is None and not (isinstance(element, ast.Constant) and element.value is None):
                return None
            values.append(value)
        rows.append(tuple(values))
    return tuple(rows)


def _mt_closed_dictionary(node: ast.Dict) -> tuple[tuple[object, object], ...] | None:
    if len(node.keys) > 16 or len(node.keys) != len(node.values):
        return None
    pairs: list[tuple[object, object]] = []
    seen: list[object] = []
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            return None
        key = _mt_closed_scalar(key_node)
        value = _mt_closed_scalar(value_node)
        if (
            key is None and not (isinstance(key_node, ast.Constant) and key_node.value is None)
        ) or (
            value is None
            and not (isinstance(value_node, ast.Constant) and value_node.value is None)
        ):
            return None
        try:
            hash(key)
        except TypeError:
            return None
        if any(key == prior for prior in seen):
            return None
        seen.append(key)
        pairs.append((key, value))
    return tuple(pairs)


_MT_SEQUENCE_MUTATORS = frozenset(
    {
        "append",
        "remove",
        "pop",
        "insert",
        "extend",
        "clear",
        "sort",
        "reverse",
        "__setitem__",
    }
)
_MT_SEQUENCE_READ_BUILTINS = frozenset(
    {"len", "enumerate", "zip", "sorted", "set", "tuple", "list", "reversed", "sum", "min", "max"}
)


def _mt_setup_container_names(tree: ast.Module) -> dict[str, str]:
    result: dict[str, str] = {}
    for statement in tree.body:
        target, value = _mt_setup_target_value(statement)
        if target is None or value is None:
            continue
        if isinstance(value, (ast.List, ast.Tuple)) and (
            _closed_sequence_elements(value.elts) is not None or _mt_closed_table(value) is not None
        ):
            result[target.id] = "list" if isinstance(value, ast.List) else "tuple"
        elif isinstance(value, ast.Dict) and _mt_closed_dictionary(value) is not None:
            result[target.id] = "dictionary"
    return result


def _mt_setup_containers_immutable(tree: ast.Module) -> bool:
    """Prove whole-module non-mutation/non-escape for admitted setup containers."""

    kinds = _mt_setup_container_names(tree)
    if not kinds:
        return True
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    helpers_by_name: dict[str, list[ast.FunctionDef]] = defaultdict(list)
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef):
            helpers_by_name[statement.name].append(statement)
    module_scalars = {
        target.id: value.value
        for statement in tree.body
        for target, value in (_mt_setup_target_value(statement),)
        if target is not None
        and isinstance(value, ast.Constant)
        and (
            _mt_closed_scalar(value) is not None
            or (isinstance(value, ast.Constant) and value.value is None)
        )
    }

    for original, kind in kinds.items():
        closure = {original}
        aliases: dict[str, ast.Assign | ast.AnnAssign] = {}
        changed = True
        while changed:
            changed = False
            for node in ast.walk(tree):
                target, value = (
                    _mt_setup_target_value(node) if isinstance(node, ast.stmt) else (None, None)
                )
                if (
                    target is not None
                    and isinstance(value, ast.Name)
                    and value.id in closure
                    and target.id not in closure
                ):
                    closure.add(target.id)
                    aliases[target.id] = cast(ast.Assign | ast.AnnAssign, node)
                    changed = True

        initial_nodes = {
            node
            for node in tree.body
            if (
                (target_value := _mt_setup_target_value(node))[0] is not None
                and target_value[0].id == original
            )
        }
        allowed_binding_nodes: set[ast.AST] = set(initial_nodes) | set(aliases.values())
        closed_index_names = {
            statement.target.id
            for statement in ast.walk(tree)
            if isinstance(statement, ast.For)
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.iter, ast.Call)
            and isinstance(statement.iter.func, ast.Name)
            and statement.iter.func.id == "range"
            and len(statement.iter.args) == 1
            and not statement.iter.keywords
            and isinstance(statement.iter.args[0], ast.Call)
            and isinstance(statement.iter.args[0].func, ast.Name)
            and statement.iter.args[0].func.id == "len"
            and len(statement.iter.args[0].args) == 1
            and isinstance(statement.iter.args[0].args[0], ast.Name)
            and statement.iter.args[0].args[0].id in closure
        }
        dictionary_member_names = {
            statement.target.id
            for statement in ast.walk(tree)
            if isinstance(statement, (ast.For, ast.AsyncFor))
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.iter, ast.Name)
            and kinds.get(statement.iter.id) in {"list", "tuple"}
        }

        def root_add(node: ast.AST) -> ast.AST:
            current = node
            while isinstance(parents.get(current), ast.BinOp) and isinstance(
                cast(ast.BinOp, parents[current]).op, ast.Add
            ):
                current = parents[current]
            return current

        def literal_concat_leaf(node: ast.expr, container_kind: str = kind) -> bool:
            if not isinstance(node, (ast.List, ast.Tuple)):
                return False
            if (container_kind == "list" and not isinstance(node, ast.List)) or (
                container_kind == "tuple" and not isinstance(node, ast.Tuple)
            ):
                return False
            for item in node.elts:
                if isinstance(item, ast.Constant):
                    value = _mt_closed_scalar(item)
                    if value is None and item.value is not None:
                        return False
                elif isinstance(item, ast.Name):
                    if item.id not in module_scalars:
                        return False
                else:
                    return False
            return True

        def concat_allowed(
            load: ast.Name, closure_names: frozenset[str] = frozenset(closure)
        ) -> bool:
            root = root_add(load)
            if not isinstance(root, ast.BinOp) or not isinstance(root.op, ast.Add):
                return False
            if any(
                isinstance(item, ast.BinOp) and not isinstance(item.op, ast.Add)
                for item in ast.walk(root)
            ):
                return False
            leaves: list[ast.expr] = []

            def collect(item: ast.expr) -> None:
                if isinstance(item, ast.BinOp) and isinstance(item.op, ast.Add):
                    collect(item.left)
                    collect(item.right)
                else:
                    leaves.append(item)

            collect(root)
            if not all(
                (isinstance(item, ast.Name) and item.id in closure_names)
                or literal_concat_leaf(item)
                for item in leaves
            ):
                return False
            owner = parents.get(root)
            target: ast.Name | None = None
            if (
                isinstance(owner, ast.Assign)
                and owner.value is root
                and len(owner.targets) == 1
                and isinstance(owner.targets[0], ast.Name)
            ):
                target = owner.targets[0]
            elif (
                isinstance(owner, ast.AnnAssign)
                and owner.value is root
                and owner.simple == 1
                and isinstance(owner.target, ast.Name)
            ):
                target = owner.target
            return target is not None and target.id not in closure_names

        def builtin_call_allowed(
            call: ast.Call,
            load: ast.Name,
            closure_names: frozenset[str] = frozenset(closure),
        ) -> bool:
            if (
                not isinstance(call.func, ast.Name)
                or call.func.id not in _MT_SEQUENCE_READ_BUILTINS
            ):
                return False
            if call.func.id not in _UNSHADOWED_BUILTINS or _definition_shadows_builtin(tree):
                return False
            if any(isinstance(arg, ast.Starred) for arg in call.args) or any(
                keyword.arg is None for keyword in call.keywords
            ):
                return False
            tracked_loads = [
                candidate
                for argument in call.args
                for candidate in ast.walk(argument)
                if isinstance(candidate, ast.Name)
                and isinstance(candidate.ctx, ast.Load)
                and candidate.id in closure_names
            ]
            if tracked_loads != [load]:
                return False
            name = call.func.id
            direct = [index for index, argument in enumerate(call.args) if argument is load]
            if direct != [0] and name != "zip":
                return False
            if name in {"len", "set", "tuple", "list", "reversed", "min", "max"}:
                return len(call.args) == 1 and not call.keywords
            if name == "enumerate":
                if not 1 <= len(call.args) <= 2 or len(call.keywords) > 1:
                    return False
                if call.keywords and call.keywords[0].arg != "start":
                    return False
                if len(call.args) == 2 and call.keywords:
                    return False
                start = (
                    call.args[1]
                    if len(call.args) == 2
                    else call.keywords[0].value
                    if call.keywords
                    else None
                )
                return start is None or _mt_literal_member(start) is not None
            if name == "zip":
                return bool(
                    1 <= len(call.args) <= 16
                    and load in call.args
                    and len(call.keywords) <= 1
                    and all(
                        item.arg == "strict"
                        and isinstance(item.value, ast.Constant)
                        and isinstance(item.value.value, bool)
                        for item in call.keywords
                    )
                )
            if name == "sorted":
                if not call.args or call.args[0] is not load or len(call.args) != 1:
                    return False
                values = {item.arg: item.value for item in call.keywords}
                return bool(
                    len(values) == len(call.keywords)
                    and set(values) <= {"key", "reverse"}
                    and (
                        "key" not in values
                        or (isinstance(values["key"], ast.Constant) and values["key"].value is None)
                    )
                    and (
                        "reverse" not in values
                        or (
                            isinstance(values["reverse"], ast.Constant)
                            and isinstance(values["reverse"].value, bool)
                        )
                    )
                )
            if name == "sum":
                if not 1 <= len(call.args) <= 2 or len(call.keywords) > 1:
                    return False
                if call.keywords and call.keywords[0].arg != "start":
                    return False
                if len(call.args) == 2 and call.keywords:
                    return False
                start = (
                    call.args[1]
                    if len(call.args) == 2
                    else call.keywords[0].value
                    if call.keywords
                    else None
                )
                return start is None or _finite_numeric_constant(start)
            return False

        def helper_passage_allowed(call: ast.Call, load: ast.Name) -> bool:
            if not isinstance(call.func, ast.Name):
                return False
            definitions = helpers_by_name.get(call.func.id, [])
            if len(definitions) != 1:
                return False
            helper = definitions[0]
            args = helper.args
            if (
                helper.decorator_list
                or args.posonlyargs
                or args.vararg is not None
                or args.kwarg is not None
                or args.kwonlyargs
            ):
                return False
            parameter_names = [item.arg for item in args.args]
            defaults = dict(
                zip(
                    parameter_names[len(parameter_names) - len(args.defaults) :],
                    args.defaults,
                    strict=True,
                )
            )
            bound, reason = _bind_helper_arguments(call, parameter_names, defaults)
            if reason is not None or bound is None:
                return False
            formals = [name for name, value in bound.items() if value is load]
            if len(formals) != 1:
                return False
            formal = formals[0]
            for candidate in ast.walk(helper):
                if not (
                    isinstance(candidate, ast.Name)
                    and candidate.id == formal
                    and isinstance(candidate.ctx, ast.Load)
                ):
                    continue
                owner = parents.get(candidate)
                if (
                    isinstance(owner, (ast.For, ast.AsyncFor, ast.comprehension))
                    and owner.iter is candidate
                ):
                    continue
                if (
                    isinstance(owner, ast.Compare)
                    and len(owner.ops) == 1
                    and isinstance(owner.ops[0], (ast.In, ast.NotIn))
                    and owner.comparators == [candidate]
                ):
                    continue
                if isinstance(owner, ast.Call) and builtin_call_allowed(owner, candidate):
                    continue
                return False
            return True

        def load_allowed(
            load: ast.Name,
            alias_nodes: tuple[ast.Assign | ast.AnnAssign, ...] = tuple(aliases.values()),
            container_kind: str = kind,
            index_names: frozenset[str] = frozenset(closed_index_names),
            member_names: frozenset[str] = frozenset(dictionary_member_names),
        ) -> bool:
            owner = parents.get(load)
            if isinstance(owner, (ast.Assign, ast.AnnAssign)):
                _target, value = _mt_setup_target_value(owner)
                if value is load and owner in alias_nodes:
                    return True
            if isinstance(owner, ast.Attribute) and owner.value is load:
                call = parents.get(owner)
                if isinstance(call, ast.Call) and call.func is owner:
                    if owner.attr in _MT_SEQUENCE_MUTATORS:
                        return False
                    if (
                        owner.attr == "format"
                        and isinstance(owner.value, ast.Constant)
                        and isinstance(owner.value.value, str)
                    ):
                        return True
                return False
            if isinstance(owner, ast.Call):
                if builtin_call_allowed(owner, load):
                    return True
                if (
                    isinstance(owner.func, ast.Attribute)
                    and owner.func.attr == "format"
                    and isinstance(owner.func.value, ast.Constant)
                    and isinstance(owner.func.value.value, str)
                    and any(argument is load for argument in owner.args)
                    and not any(isinstance(argument, ast.Starred) for argument in owner.args)
                    and all(keyword.arg is not None for keyword in owner.keywords)
                ):
                    return True
                if (
                    isinstance(owner.func, ast.Name)
                    and owner.func.id == "format"
                    and owner.func.id in _UNSHADOWED_BUILTINS
                    and owner.args
                    and owner.args[0] is load
                    and len(owner.args) <= 2
                    and not owner.keywords
                    and (
                        len(owner.args) == 1
                        or (
                            isinstance(owner.args[1], ast.Constant)
                            and isinstance(owner.args[1].value, str)
                        )
                    )
                ):
                    return True
                return helper_passage_allowed(owner, load)
            if isinstance(owner, ast.keyword) and owner.value is load and owner.arg is not None:
                call = parents.get(owner)
                return bool(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "format"
                    and isinstance(call.func.value, ast.Constant)
                    and isinstance(call.func.value.value, str)
                    and not any(isinstance(argument, ast.Starred) for argument in call.args)
                    and all(keyword.arg is not None for keyword in call.keywords)
                )
            if isinstance(owner, (ast.For, ast.AsyncFor, ast.comprehension)) and owner.iter is load:
                return True
            if (
                isinstance(owner, ast.Compare)
                and len(owner.ops) == 1
                and isinstance(owner.ops[0], (ast.In, ast.NotIn))
                and owner.comparators == [load]
            ):
                return True
            if (
                isinstance(owner, ast.Subscript)
                and owner.value is load
                and isinstance(owner.ctx, ast.Load)
            ):
                if container_kind == "dictionary":
                    return _mt_literal_member(owner.slice) is not None or (
                        isinstance(owner.slice, ast.Name) and owner.slice.id in member_names
                    )
                member = _mt_literal_member(owner.slice)
                return isinstance(member, int) or (
                    isinstance(owner.slice, ast.Name) and owner.slice.id in index_names
                )
            if isinstance(owner, ast.BinOp) and isinstance(owner.op, ast.Add):
                return concat_allowed(load)
            if isinstance(owner, ast.FormattedValue) and owner.value is load:
                return True
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in closure:
                if isinstance(node.ctx, ast.Load):
                    if not load_allowed(node):
                        return False
                elif isinstance(node.ctx, (ast.Store, ast.Del)):
                    owner: ast.AST = node
                    while owner in parents and not isinstance(owner, ast.stmt):
                        owner = parents[owner]
                    if owner not in allowed_binding_nodes:
                        return False
            elif isinstance(node, (ast.Global, ast.Nonlocal)) and any(
                name in closure for name in node.names
            ):
                return False
            elif isinstance(node, ast.arg) and node.arg in closure:
                return False
            elif (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name in closure
            ):
                return False
            elif isinstance(node, ast.alias):
                bound = node.asname or node.name.split(".", 1)[0]
                if bound in closure:
                    return False
            elif isinstance(node, ast.ExceptHandler) and node.name in closure:
                return False
    return True


def _resolver(statements: Sequence[ast.stmt]) -> tuple[_Resolver | None, str | None]:
    imports: dict[str, str] = {}
    constants: dict[str, str] = {}
    literals: dict[str, int | float | bool] = {}
    tuples: dict[str, tuple[object, ...]] = {}
    sequence_kinds: dict[str, str] = {}
    tables: dict[str, tuple[tuple[object, ...], ...]] = {}
    dictionaries: dict[str, tuple[tuple[object, object], ...]] = {}
    file_parents: set[str] = set()
    accepted_names: set[str] = set()
    bound_names = {
        name
        for statement in statements
        for name in (
            _store_names(statement)
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            else {statement.name}
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            else set()
        )
    }
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
        imports=imports,
        constants=constants,
        literals=literals,
        tuples=tuples,
        sequence_kinds=sequence_kinds,
        file_parents=file_parents,
        builtins_shadowed=set(accepted_names & _UNSHADOWED_BUILTINS),
        accepted_names=accepted_names,
        bound_names=bound_names,
        tables=tables,
        dictionaries=dictionaries,
    )
    for statement in statements:
        target, value = _mt_setup_target_value(statement)
        if target is None or value is None:
            continue
        name = target.id
        occupied = (
            constants.keys() | literals.keys() | tuples.keys() | tables.keys() | dictionaries.keys()
        )
        if isinstance(value, ast.Constant) and isinstance(value.value, (int, float, bool)):
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            literals[name] = value.value
            continue
        if isinstance(value, ast.Name) and value.id in literals:
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            literals[name] = literals[value.id]
            continue
        if isinstance(value, ast.Name) and value.id in tuples:
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            tuples[name] = tuples[value.id]
            sequence_kinds[name] = sequence_kinds[value.id]
            continue
        if isinstance(value, ast.Name) and value.id in tables:
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            tables[name] = tables[value.id]
            sequence_kinds[name] = sequence_kinds[value.id]
            continue
        if isinstance(value, ast.Name) and value.id in dictionaries:
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            dictionaries[name] = dictionaries[value.id]
            continue
        if isinstance(value, ast.Name) and value.id in constants:
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            constants[name] = constants[value.id]
            continue
        if (
            isinstance(value, (ast.Tuple, ast.List))
            and (sequence := _closed_sequence_elements(value.elts)) is not None
        ):
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            tuples[name] = tuple(sequence)
            sequence_kinds[name] = "list" if isinstance(value, ast.List) else "tuple"
            continue
        if (
            isinstance(value, ast.ListComp)
            and len(value.generators) == 1
            and not value.generators[0].ifs
            and not value.generators[0].is_async
            and isinstance(value.elt, ast.Name)
            and isinstance(value.generators[0].target, (ast.Tuple, ast.List))
            and value.generators[0].target.elts
            and isinstance(value.generators[0].target.elts[0], ast.Name)
            and value.elt.id == value.generators[0].target.elts[0].id
            and isinstance(value.generators[0].iter, ast.Subscript)
            and isinstance(value.generators[0].iter.value, ast.Name)
            and isinstance(value.generators[0].iter.slice, ast.Slice)
            and value.generators[0].iter.value.id in tables
        ):
            lower = _mt_optional_literal_int(value.generators[0].iter.slice.lower)
            upper = _mt_optional_literal_int(value.generators[0].iter.slice.upper)
            step = _mt_optional_literal_int(value.generators[0].iter.slice.step)
            rows = tables[value.generators[0].iter.value.id][slice(lower, upper, step)]
            if rows and all(row and isinstance(row[0], str) for row in rows):
                if name in occupied or name in imports:
                    return None, "api-resolution-ambiguous"
                tuples[name] = tuple(row[0] for row in rows)
                sequence_kinds[name] = "list"
                continue
        if (
            isinstance(value, (ast.Tuple, ast.List))
            and (table := _mt_closed_table(value)) is not None
        ):
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            tables[name] = table
            sequence_kinds[name] = "list" if isinstance(value, ast.List) else "tuple"
            continue
        if isinstance(value, ast.Dict) and (dictionary := _mt_closed_dictionary(value)) is not None:
            if name in occupied or name in imports:
                return None, "api-resolution-ambiguous"
            dictionaries[name] = dictionary
            continue
        if _file_parent_expression(value, resolver):
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
        string = resolver.string(value)
        if string is None:
            path = _static_path(value, resolver)
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


_Mt23ReaderPathKey = tuple[str, tuple[int, int, int, int]]


def _mt23_reader_path(
    call: ast.Call,
    resolver: _Resolver,
    local_paths: Mapping[_Mt23ReaderPathKey, str],
) -> str | None:
    """Resolve one reader path without making the local binding a frame root."""

    direct = _static_path(call.args[0], resolver) if len(call.args) == 1 else None
    if direct is not None:
        return direct
    api = resolver.qualified(call.func)
    return local_paths.get((str(api), _position(call))) if api is not None else None


def _mt23_exact_local_path_expression(node: ast.expr, resolver: _Resolver) -> str | None:
    """Recognize only the two D13-A right-hand-side productions."""

    if (
        isinstance(node, ast.Call)
        and resolver.qualified(node.func) == "os.path.join"
        and len(node.args) == 2
        and not node.keywords
        and isinstance(node.args[0], ast.Call)
        and resolver.qualified(node.args[0].func) == "os.path.dirname"
        and len(node.args[0].args) == 1
        and not node.args[0].keywords
        and isinstance(node.args[0].args[0], ast.Call)
        and resolver.qualified(node.args[0].args[0].func) == "os.path.abspath"
        and len(node.args[0].args[0].args) == 1
        and not node.args[0].args[0].keywords
        and isinstance(node.args[0].args[0].args[0], ast.Name)
        and isinstance(node.args[0].args[0].args[0].ctx, ast.Load)
        and node.args[0].args[0].args[0].id == "__file__"
        and (
            (isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str))
            or (isinstance(node.args[1], ast.Name) and isinstance(node.args[1].ctx, ast.Load))
        )
    ):
        return _static_path(node, resolver)
    if not (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Div)
        and isinstance(node.left, ast.Attribute)
        and node.left.attr == "parent"
        and isinstance(node.left.ctx, ast.Load)
        and isinstance(node.left.value, ast.Call)
        and isinstance(node.left.value.func, ast.Attribute)
        and node.left.value.func.attr == "resolve"
        and not node.left.value.args
        and not node.left.value.keywords
        and isinstance(node.left.value.func.value, ast.Call)
        and resolver.qualified(node.left.value.func.value.func) == "pathlib.Path"
        and len(node.left.value.func.value.args) == 1
        and not node.left.value.func.value.keywords
        and isinstance(node.left.value.func.value.args[0], ast.Name)
        and isinstance(node.left.value.func.value.args[0].ctx, ast.Load)
        and node.left.value.func.value.args[0].id == "__file__"
        and (
            (isinstance(node.right, ast.Constant) and isinstance(node.right.value, str))
            or (isinstance(node.right, ast.Name) and isinstance(node.right.ctx, ast.Load))
        )
    ):
        return None
    return _static_path(node, resolver)


def _mt23_local_reader_paths(
    tree: ast.Module,
    *,
    resolver: _Resolver,
    authorized_path: str,
    csv_header: tuple[str, ...],
    unit_column: str,
    group_column: str,
) -> Mapping[_Mt23ReaderPathKey, str]:
    """Prove the exact immutable function-local D13-A reader-path edge."""

    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    def function_owner(node: ast.AST) -> ast.FunctionDef | None:
        cursor = node
        while cursor in parents:
            cursor = parents[cursor]
            if isinstance(cursor, ast.AsyncFunctionDef):
                return None
            if isinstance(cursor, ast.FunctionDef):
                return cursor
        return None

    result: dict[_Mt23ReaderPathKey, str] = {}
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        api = resolver.qualified(call.func)
        accepted = False
        if api == "pandas.read_csv" and len(call.args) == 1:
            accepted = not call.keywords or bool(
                _parse_dates_columns(
                    call,
                    resolver=resolver,
                    csv_header=csv_header,
                    forbidden={unit_column, group_column},
                )
            )
        elif api == "numpy.genfromtxt" and len(call.args) == 1:
            accepted = _literal_keywords(call.keywords) == {
                "delimiter": ",",
                "names": True,
                "dtype": None,
                "encoding": "utf-8",
            }
        if (
            not accepted
            or len(call.args) != 1
            or not isinstance(call.args[0], ast.Name)
            or _static_path(call.args[0], resolver) is not None
        ):
            continue
        name_node = call.args[0]
        name = name_node.id
        owner = function_owner(call)
        if owner is None:
            continue
        direct_statements = tuple(owner.body)
        reader_statement = next(
            (
                statement
                for statement in direct_statements
                if (
                    isinstance(statement, (ast.Assign, ast.AnnAssign, ast.Return))
                    and getattr(statement, "value", None) is call
                )
            ),
            None,
        )
        if reader_statement is None:
            continue
        bindings: list[ast.Assign | ast.AnnAssign] = []
        for statement in direct_statements:
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == name
            ):
                bindings.append(statement)
            elif (
                isinstance(statement, ast.AnnAssign)
                and statement.simple == 1
                and isinstance(statement.target, ast.Name)
                and statement.target.id == name
                and statement.value is not None
                and _mt_closed_annotation(statement.annotation)
            ):
                bindings.append(statement)
        if len(bindings) != 1:
            continue
        binding = bindings[0]
        if direct_statements.index(binding) >= direct_statements.index(reader_statement):
            continue
        expression = binding.value
        if expression is None:
            continue
        path = _mt23_exact_local_path_expression(expression, resolver)
        if path != authorized_path:
            continue
        all_name_nodes = [
            node for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == name
        ]
        stores = [node for node in all_name_nodes if isinstance(node.ctx, (ast.Store, ast.Del))]
        loads = [node for node in all_name_nodes if isinstance(node.ctx, ast.Load)]
        target = binding.targets[0] if isinstance(binding, ast.Assign) else binding.target
        if stores != [target] or loads != [name_node]:
            continue
        if any(
            isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names
            for node in ast.walk(tree)
        ):
            continue
        result[(str(api), _position(call))] = path
    return MappingProxyType(result)


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
        reducing_filter = False
        if parsed is None:
            parsed = _mask_with_reducing_filter(mask, receiver, resolver)
            reducing_filter = parsed is not None
        value = resolver.string(projection)
        if receiver in values and parsed is not None and value is not None:
            return (
                receiver,
                parsed[0],
                parsed[1],
                value,
                (
                    "pandas_loc_boolean_mask_reducing_v1"
                    if reducing_filter
                    else "pandas_loc_boolean_mask_v1"
                ),
            )
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


def _mask_with_reducing_filter(
    node: ast.expr, receiver: str, resolver: _Resolver
) -> tuple[str, str] | None:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.BitAnd):
        return None
    for group_side, filter_side in ((node.left, node.right), (node.right, node.left)):
        parsed = _mask(group_side, receiver, resolver)
        if parsed is None:
            continue
        if any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr in {"head", "tail", "nth", "sample", "cumcount", "idxmin", "idxmax"}
            for item in ast.walk(filter_side)
        ):
            return parsed
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


# The code above is the by-value pseudoreplication 3.1 implementation base required by
# ADR-0079. The multiple-testing specialization below is deliberately namespaced. It does not
# call or import the qualified module's private helpers; all reused bounds and algorithms are local
# copies in this versioned file.


_MT_TEST_APIS = frozenset({"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"})
_MT_CORRECTION_APIS = frozenset(
    {
        "statsmodels.stats.multitest.multipletests",
        "statsmodels.stats.multitest.fdrcorrection",
        "scipy.stats.false_discovery_control",
        "sc_referee.calculation_checks.bh.benjamini_hochberg",
    }
)
_MT_MULTIPLETESTS_METHODS = frozenset(
    {
        "b",
        "bonferroni",
        "s",
        "sidak",
        "hs",
        "holm-sidak",
        "h",
        "holm",
        "sh",
        "simes-hochberg",
        "hommel",
        "fdr_bh",
        "fdr_by",
        "fdr_tsbh",
        "fdr_tsbky",
    }
)
_MT_DECISION_LITERALS = frozenset({Decimal("0.01"), Decimal("0.05"), Decimal("0.1")})
_MT_V2_RAW_DECISION_LITERALS = frozenset({Decimal("0.05")})
_MT_V2_DYNAMIC_EXECUTION_REGISTRY = (
    "exec",
    "eval",
    "compile",
    "__import__",
    "importlib.import_module",
    "getattr(imported-module)",
    "setattr(imported-module)",
    "globals-mutation",
    "locals-mutation",
)
_MT_V2_DYNAMIC_BUILTINS = frozenset(_MT_V2_DYNAMIC_EXECUTION_REGISTRY[:4])
_MT_V2_DYNAMIC_MAPPING_MUTATORS = frozenset(
    {"__setitem__", "update", "setdefault", "pop", "popitem", "clear"}
)
_MT_V2_API_REBINDING_REGISTRY = (
    "registered-or-statistics-module-attribute-store-or-del",
    "live-api-alias-function-definition",
    "live-api-alias-async-function-definition",
    "live-api-alias-class-definition",
    "live-api-alias-argument-binding",
    "live-api-alias-name-store-or-del",
)
_MT_V2_CONTROL_NODE_REGISTRY = (
    "registered-test-call-argument",
    "recognized-correction-call-argument",
    "p-derived-conclusion-operand",
    "family-container-control-insertion",
    "If.test",
    "IfExp.test",
    "While.test",
    "Assert.test",
    "Match.subject",
    "match_case.guard",
    "For.iter",
    "AsyncFor.iter",
    "comprehension.iter",
    "comprehension.if",
    "BoolOp.short-circuit-operand",
    "registered-sink-member-selector",
    "return",
    "break",
    "continue",
    "raise",
    "sys.exit",
    "execution-prevention-residual",
)
_MT_V2_OUTCOME_MUTATORS = frozenset(
    {"append", "remove", "pop", "insert", "extend", "clear", "sort", "reverse", "__setitem__"}
)
_MT_QUERY = _QUERY
_MT_CORRECTION_TERMINALS = frozenset(
    {
        "multipletests",
        "fdrcorrection",
        "false_discovery_control",
        "multicomp",
        "fdr_correction",
        "p_adjust",
        "padjust",
        "bonferroni",
        "holm",
        "sidak",
    }
)
_MT_UNRECOGNIZED_EXTREMUM_TERMINALS = frozenset(
    {
        "argmin",
        "nanargmin",
        "argmax",
        "nanargmax",
        "idxmin",
        "idxmax",
        "partition",
        "argpartition",
        "nsmallest",
        "nlargest",
    }
)
_MT_HELPER_REASONS = frozenset(
    {
        "helper-callee-not-simple-name",
        "helper-definition-unavailable-or-nonunique",
        "helper-parameter-shape-unsupported",
        "helper-parameter-default-unsupported",
        "helper-variadic-parameter-unsupported",
        "helper-argument-binding-unsupported",
        "helper-recursion-unsupported",
        "helper-return-count-unsupported",
        "helper-return-position-unsupported",
        "helper-return-expression-unsupported",
        "helper-global-nonlocal-unsupported",
        "helper-closure-or-nested-definition-unsupported",
        "helper-async-decorator-or-yield-unsupported",
        "helper-body-statement-unsupported",
        "helper-free-name-unbound",
        "helper-inlining-depth-exceeded",
        "helper-call-site-reentry-unsupported",
    }
)


@dataclass(frozen=True, order=True)
class MultipleTestingEvidenceSpan:
    role: str
    family_position: int | None
    start_line: int
    end_line: int
    start_column: int
    end_column: int


@dataclass(frozen=True)
class MultipleTestingDataflowFacts:
    registered_test_api: str
    registered_test_apis_by_position: tuple[str, ...]
    family_size: int
    corrected_positions: tuple[int, ...]
    conclusion_positions: tuple[int, ...]
    correction_classification: Literal["none", "strict_subset", "complete"]
    correction_methods: tuple[str, ...]
    output_sink_kinds: tuple[str, ...]
    evidence_spans: tuple[MultipleTestingEvidenceSpan, ...]


@dataclass(frozen=True)
class MultipleTestingDataflowResult:
    facts: MultipleTestingDataflowFacts | None
    reason: str | None

    def __post_init__(self) -> None:
        if (self.facts is None) == (self.reason is None):
            raise ValueError("multiple-testing dataflow result must contain facts or one reason")


@dataclass(frozen=True)
class _MtCallInstance:
    call: ast.Call
    api: str
    ordinal: int


@dataclass(frozen=True)
class _MtSeries:
    rows: frozenset[int]
    outcome: str | None
    group_value: str | None
    reader_rooted: bool
    complete_proved: bool


@dataclass(frozen=True)
class _MtFrame:
    rows: frozenset[int]
    group_value: str | None
    reader_rooted: bool
    complete_proved: bool


@dataclass(frozen=True)
class _MtCorrection:
    call: ast.Call
    api: str
    positions: frozenset[int]
    ordered_positions: tuple[int, ...]
    method: str


@dataclass(frozen=True)
class _MtCsvRows:
    group_rows: Mapping[str, frozenset[int]]
    value_rows: Mapping[tuple[str, str], frozenset[int]]
    all_rows: frozenset[int]


def _mt_v2_execution_scope(
    tree: ast.Module,
) -> tuple[tuple[ast.stmt, ...], tuple[ast.stmt, ...], dict[str, ast.FunctionDef]]:
    """Select an execution root without imposing a whole-module setup grammar."""

    body = tuple(item for item in tree.body if not _is_docstring(item))
    helpers = {
        item.name: item
        for item in body
        if isinstance(item, ast.FunctionDef) and item.name != "main"
    }
    mains = [item for item in body if isinstance(item, ast.FunctionDef) and item.name == "main"]
    guarded = any(isinstance(item, ast.If) and _exact_main_guard(item) for item in body)
    if len(mains) == 1 and guarded:
        setup = tuple(
            item
            for item in body
            if isinstance(item, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign))
        )
        return (
            tuple(item for item in mains[0].body if not _is_docstring(item)),
            setup,
            helpers,
        )
    return (
        tuple(
            item
            for item in body
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ),
        (),
        helpers,
    )


def _mt_v21_segmented_bindings(
    scope: tuple[ast.stmt, ...], tree: ast.Module, resolver: _Resolver
) -> tuple[ast.stmt, ...]:
    """Rename only closed straight-line repeated definitions (R12)."""

    direct_owners: dict[ast.AST, ast.stmt] = {
        child: statement for statement in scope for child in ast.walk(statement)
    }
    eligible_stores: dict[str, list[ast.Name]] = defaultdict(list)
    refused: set[str] = set()

    def exact_targets(statement: ast.stmt) -> tuple[ast.Name, ...]:
        value = statement.value if isinstance(statement, (ast.Assign, ast.AnnAssign)) else None
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else ([statement.target] if isinstance(statement, ast.AnnAssign) else [])
        )
        if value is None or len(targets) != 1:
            return ()
        target = targets[0]
        if isinstance(target, ast.Name):
            return (target,)
        if not isinstance(target, (ast.List, ast.Tuple)) or any(
            isinstance(item, ast.Starred) or not isinstance(item, ast.Name) for item in target.elts
        ):
            return ()
        if isinstance(value, type(target)) and len(value.elts) == len(target.elts):
            return cast(tuple[ast.Name, ...], tuple(target.elts))
        if (
            len(target.elts) == 2
            and isinstance(value, ast.Call)
            and resolver.qualified(value.func) in _MT_TEST_APIS
        ):
            return cast(tuple[ast.Name, ...], tuple(target.elts))
        return ()

    scope_statements = set(scope)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, (ast.Store, ast.Del)):
            continue
        owner: ast.AST = node
        while owner in direct_owners and not isinstance(owner, ast.stmt):
            owner = direct_owners[owner]
        if (
            not isinstance(owner, ast.stmt)
            or owner not in scope_statements
            or node not in exact_targets(owner)
        ):
            refused.add(node.id)
            continue
        eligible_stores[node.id].append(node)
    mutators = {
        "append",
        "remove",
        "pop",
        "insert",
        "extend",
        "clear",
        "sort",
        "reverse",
        "__setitem__",
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr in mutators
        ):
            refused.add(node.func.value.id)
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            refused.add(node.value.id)

    segmented = {
        name for name, stores in eligible_stores.items() if len(stores) > 1 and name not in refused
    }
    if not segmented:
        return scope

    current: dict[str, str] = {}
    ordinals: Counter[str] = Counter()
    result: list[ast.stmt] = []

    class Rewrite(ast.NodeTransformer):
        def __init__(self, stores: Mapping[str, str]) -> None:
            self.stores = stores

        def visit_Name(self, node: ast.Name) -> ast.AST:
            replacement: str | None = None
            if isinstance(node.ctx, ast.Load):
                replacement = current.get(node.id)
            elif isinstance(node.ctx, ast.Store):
                replacement = self.stores.get(node.id)
            if replacement is None:
                return node
            return ast.copy_location(ast.Name(id=replacement, ctx=node.ctx), node)

    for statement in scope:
        stores: dict[str, str] = {}
        for target in exact_targets(statement):
            if target.id not in segmented:
                continue
            ordinals[target.id] += 1
            stores[target.id] = f"{target.id}__mt21_{ordinals[target.id]}"
        copied = copy.deepcopy(statement)
        # Assignment RHS observes the preceding reaching definition. Rewrite it
        # before installing this statement's target spellings.
        if isinstance(copied, ast.Assign) and copied.value is not None:
            copied.value = cast(ast.expr, Rewrite({}).visit(copied.value))
            copied.targets = [
                cast(ast.expr, Rewrite(stores).visit(target)) for target in copied.targets
            ]
        elif isinstance(copied, ast.AnnAssign) and copied.value is not None:
            copied.value = cast(ast.expr, Rewrite({}).visit(copied.value))
            rewritten_target = Rewrite(stores).visit(copied.target)
            assert isinstance(rewritten_target, (ast.Name, ast.Attribute, ast.Subscript))
            copied.target = rewritten_target
        else:
            copied = cast(ast.stmt, Rewrite(stores).visit(copied))
        current.update(stores)
        result.append(copied)
    return tuple(result)


def _mt_v2_integrity_census(tree: ast.Module, resolver: _Resolver) -> bool:
    """Whole-module dynamic-execution and live-API-rebinding census."""

    imported_modules = frozenset(resolver.imports)
    live_api_aliases = {
        bound
        for bound, qualified in resolver.imports.items()
        if qualified in _MT_TEST_APIS
        or qualified in _MT_CORRECTION_APIS
        or any(_prefix_hit(qualified, (prefix,)) for prefix in _STATISTICS_PREFIXES)
        or any(api == qualified or api.startswith(qualified + ".") for api in _MT_TEST_APIS)
        or any(api == qualified or api.startswith(qualified + ".") for api in _MT_CORRECTION_APIS)
    }
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

    def unshadowed(name: str) -> bool:
        return _mt_binding_count(tuple(tree.body), name) == 0

    def imported_receiver(node: ast.expr) -> bool:
        root = node
        while isinstance(root, ast.Attribute):
            root = root.value
        return isinstance(root, ast.Name) and root.id in imported_modules

    mapping_roots: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in _MT_V2_DYNAMIC_BUILTINS
            and unshadowed(node.func.id)
        ):
            return True
        if resolver.qualified(node.func) == "importlib.import_module":
            return True
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"getattr", "setattr"}
            and unshadowed(node.func.id)
            and node.args
            and imported_receiver(node.args[0])
        ):
            return True
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"globals", "locals"}
            and unshadowed(node.func.id)
        ):
            parent = parents.get(node)
            if isinstance(parent, (ast.Assign, ast.AnnAssign)):
                target = parent.targets[0] if isinstance(parent, ast.Assign) else parent.target
                if isinstance(target, ast.Name):
                    mapping_roots.add(target.id)
            elif isinstance(parent, ast.Subscript) and isinstance(parent.ctx, (ast.Store, ast.Del)):
                return True
            elif (
                isinstance(parent, ast.Attribute)
                and parent.attr in _MT_V2_DYNAMIC_MAPPING_MUTATORS
                and isinstance(parents.get(parent), ast.Call)
            ):
                return True

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if isinstance(node.value, ast.Name) and node.value.id in mapping_roots:
                return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id in mapping_roots
                and node.func.attr in _MT_V2_DYNAMIC_MAPPING_MUTATORS
            ):
                return True
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
            qualified = resolver.qualified(node.value)
            if qualified is not None and (
                _prefix_hit(qualified, _STATISTICS_PREFIXES)
                or any(api == qualified or api.startswith(qualified + ".") for api in _MT_TEST_APIS)
                or any(
                    api == qualified or api.startswith(qualified + ".")
                    for api in _MT_CORRECTION_APIS
                )
            ):
                return True
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if node.id not in live_api_aliases:
                continue
            owner = parents.get(node)
            if isinstance(owner, (ast.Import, ast.ImportFrom, ast.alias)):
                continue
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in live_api_aliases:
                return True
        if isinstance(node, ast.arg) and node.arg in live_api_aliases:
            return True
    return False


def _mt_v2_outcome_sequences_stable(
    tree: ast.Module, resolver: _Resolver, outcome_columns: tuple[str, ...]
) -> bool:
    """Prove immutability only for sequence values used as the authorized family."""

    roots: set[str] = set()
    for statement in tree.body:
        target, _value = _mt_setup_target_value(statement)
        if target is None:
            continue
        probe = ast.Name(id=target.id, ctx=ast.Load())
        sequence = resolver.sequence(probe)
        table = resolver.table(probe)
        if sequence is not None and tuple(sequence) == outcome_columns:
            roots.add(target.id)
        elif table is not None and tuple(row[0] for row in table if row) == outcome_columns:
            roots.add(target.id)
    if not roots:
        return True
    aliases = set(roots)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and (value := node.value) is not None
                and isinstance(value, ast.Name)
                and value.id in aliases
            ):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for alias_target in targets:
                if isinstance(alias_target, ast.Name) and alias_target.id not in aliases:
                    aliases.add(alias_target.id)
                    changed = True
    initial_bindings: set[ast.AST] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id in aliases for target in targets):
                if node in tree.body or isinstance(node.value, ast.Name):
                    initial_bindings.add(node)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id in aliases
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            owner: ast.AST = node
            while owner in parents and not isinstance(owner, ast.stmt):
                owner = parents[owner]
            if owner not in initial_bindings:
                return False
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if isinstance(node.value, ast.Name) and node.value.id in aliases:
                return False
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id in aliases
                and node.func.attr in _MT_V2_OUTCOME_MUTATORS
            ):
                return False
    return True


def _mt_v2_operand_reader_paths(
    tree: ast.Module,
    resolver: _Resolver,
    local_paths: Mapping[_Mt23ReaderPathKey, str],
) -> frozenset[str | None]:
    """Return only reader paths on registered-family operand backward slices."""

    definitions: dict[str, list[ast.expr]] = defaultdict(list)
    helpers = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                definitions[target.id].append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                definitions[node.target.id].append(node.value)

    result: set[str | None] = set()

    def visit(node: ast.AST, active: frozenset[str]) -> None:
        if isinstance(node, ast.Call) and resolver.qualified(node.func) in {
            "pandas.read_csv",
            "numpy.genfromtxt",
        }:
            result.add(_mt23_reader_path(node, resolver, local_paths))
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in active:
                return
            for expression in definitions.get(node.id, ()):
                visit(expression, active | {node.id})
            return
        for child in ast.iter_child_nodes(node):
            visit(child, active)

    helpers_with_tests = {
        name
        for name, helper in helpers.items()
        if any(
            isinstance(node, ast.Call) and resolver.qualified(node.func) in _MT_TEST_APIS
            for node in ast.walk(helper)
        )
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if resolver.qualified(node.func) in _MT_TEST_APIS or (
            isinstance(node.func, ast.Name) and node.func.id in helpers_with_tests
        ):
            for argument in (*node.args, *(keyword.value for keyword in node.keywords)):
                visit(argument, frozenset())
    return frozenset(result)


class _MtV2TerminalHelperTransformer(ast.NodeTransformer):
    def __init__(self, helpers: Mapping[str, ast.FunctionDef], resolver: _Resolver) -> None:
        self.helpers = helpers
        self.resolver = resolver

    def visit_Call(self, node: ast.Call) -> ast.AST:
        node = cast(ast.Call, self.generic_visit(node))
        if not (
            isinstance(node.func, ast.Name)
            and len(node.args) == 1
            and not node.keywords
            and (helper := self.helpers.get(node.func.id)) is not None
        ):
            return node
        body = [item for item in helper.body if not _is_docstring(item)]
        parameter = helper.args.args[0].arg if len(helper.args.args) == 1 else ""
        if (
            parameter
            and not helper.args.posonlyargs
            and not helper.args.kwonlyargs
            and helper.args.vararg is None
            and helper.args.kwarg is None
            and not helper.args.defaults
            and not helper.decorator_list
            and len(body) == 1
            and isinstance(body[0], ast.Return)
            and body[0].value is not None
            and _mt_v21_presentation_helper_return(body[0].value, parameter)
        ):
            replacement: ast.expr = ast.JoinedStr(
                values=[ast.FormattedValue(value=copy.deepcopy(node.args[0]), conversion=-1)]
            )
            replacement.__dict__["_sc_mt_presentation_helper"] = True
            return ast.copy_location(replacement, node)
        if (
            parameter
            and len(body) == 1
            and isinstance(body[0], ast.Return)
            and isinstance(body[0].value, ast.IfExp)
        ):
            display = body[0].value
            loads = {
                item.id
                for item in ast.walk(display)
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
            }
            if (
                loads - {parameter} <= set(self.resolver.literals)
                and parameter in loads
                and isinstance(display.body, ast.Constant)
                and isinstance(display.body.value, str)
                and isinstance(display.orelse, ast.Constant)
                and isinstance(display.orelse.value, str)
                and display.body.value
                and display.orelse.value
                and "\x00" not in display.body.value
                and "\x00" not in display.orelse.value
                and len(display.body.value.encode("utf-8")) <= 256
                and len(display.orelse.value.encode("utf-8")) <= 256
            ):

                class SubstituteDecision(ast.NodeTransformer):
                    def visit_Name(self, value: ast.Name) -> ast.AST:
                        if isinstance(value.ctx, ast.Load) and value.id == parameter:
                            return ast.copy_location(copy.deepcopy(node.args[0]), value)
                        return value

                replacement = SubstituteDecision().visit(copy.deepcopy(display))
                assert isinstance(replacement, ast.IfExp)
                replacement.__dict__["_sc_mt_terminal_rendering"] = True
                return ast.copy_location(replacement, node)
            if (
                loads - {parameter} <= set(self.resolver.literals)
                and parameter in loads
                and isinstance(display.test, ast.Compare)
                and isinstance(display.body, ast.Constant)
                and isinstance(display.body.value, str)
                and isinstance(display.orelse, ast.JoinedStr)
                and any(
                    isinstance(item, ast.FormattedValue)
                    and isinstance(item.value, ast.Name)
                    and item.value.id == parameter
                    for item in ast.walk(display.orelse)
                )
            ):
                replacement = ast.JoinedStr(
                    values=[ast.FormattedValue(value=copy.deepcopy(node.args[0]), conversion=-1)]
                )
                replacement.__dict__["_sc_mt_presentation_helper"] = True
                return ast.copy_location(replacement, node)
        if (
            parameter
            and len(body) == 2
            and isinstance(body[0], ast.If)
            and not body[0].orelse
            and len(body[0].body) == 1
            and isinstance(body[0].body[0], ast.Return)
            and isinstance(body[1], ast.Return)
        ):
            arms = (body[0].body[0].value, body[1].value)
            if all(
                isinstance(arm, (ast.Constant, ast.JoinedStr))
                and all(
                    not isinstance(item, ast.Name) or item.id == parameter for item in ast.walk(arm)
                )
                for arm in arms
                if arm is not None
            ) and any(isinstance(arm, ast.JoinedStr) for arm in arms):
                replacement = ast.JoinedStr(
                    values=[ast.FormattedValue(value=copy.deepcopy(node.args[0]), conversion=-1)]
                )
                replacement.__dict__["_sc_mt_presentation_helper"] = True
                return ast.copy_location(replacement, node)
        if not (
            len(helper.args.args) == 1
            and not helper.args.posonlyargs
            and not helper.args.kwonlyargs
            and helper.args.vararg is None
            and helper.args.kwarg is None
            and not helper.args.defaults
            and len(body) == 2
            and isinstance(body[0], ast.If)
            and not body[0].orelse
            and len(body[0].body) == 1
            and isinstance(body[0].body[0], ast.Return)
            and isinstance(body[1], ast.Return)
        ):
            return node
        first = body[0].body[0].value
        second = body[1].value
        if not (
            isinstance(first, ast.Constant)
            and isinstance(first.value, str)
            and isinstance(second, ast.Constant)
            and isinstance(second.value, str)
            and first.value
            and second.value
            and "\x00" not in first.value
            and "\x00" not in second.value
            and len(first.value.encode("utf-8")) <= 256
            and len(second.value.encode("utf-8")) <= 256
        ):
            return node
        parameter = helper.args.args[0].arg
        test = _InlineNameTransformer({parameter: parameter}).visit(copy.deepcopy(body[0].test))
        assert isinstance(test, ast.expr)
        test = _IdentityNodeTransformer(ast.Name(id=parameter, ctx=ast.Load()), node.args[0]).visit(
            test
        )

        # Identity replacement is performed by spelling below because copied nodes
        # do not share identity with the synthetic needle.
        class Substitute(ast.NodeTransformer):
            def visit_Name(self, value: ast.Name) -> ast.AST:
                if isinstance(value.ctx, ast.Load) and value.id == parameter:
                    return ast.copy_location(copy.deepcopy(node.args[0]), value)
                return value

        test = Substitute().visit(test)
        assert isinstance(test, ast.expr)
        replacement = ast.IfExp(test=test, body=copy.deepcopy(first), orelse=copy.deepcopy(second))
        replacement.__dict__["_sc_mt_terminal_rendering"] = True
        return ast.copy_location(replacement, node)


def _mt_v21_presentation_helper_return(node: ast.expr, parameter: str) -> bool:
    def direct_formal(value: ast.expr) -> bool:
        return (
            isinstance(value, ast.Name)
            and isinstance(value.ctx, ast.Load)
            and value.id == parameter
        )

    def p_format(value: ast.expr) -> bool:
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "str"
            and len(value.args) == 1
            and not value.keywords
        ):
            return direct_formal(value.args[0])
        if isinstance(value, ast.JoinedStr):
            formatted = [item for item in value.values if isinstance(item, ast.FormattedValue)]
            return bool(formatted) and all(direct_formal(item.value) for item in formatted)
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mod):
            if not _mt_v21_display_string(value.left):
                return False
            payloads = (
                value.right.elts
                if isinstance(value.right, (ast.List, ast.Tuple))
                else [value.right]
            )
            return bool(payloads) and all(direct_formal(item) for item in payloads)
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "format"
            and _mt_v21_display_string(value.func.value)
            and not value.keywords
            and value.args
        ):
            return all(direct_formal(item) for item in value.args)
        return False

    if p_format(node):
        return True
    if not (
        isinstance(node, ast.IfExp)
        and isinstance(node.test, ast.Compare)
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
        and len(node.test.comparators) == 1
    ):
        return False
    pairs = ((node.test.left, node.test.comparators[0]), (node.test.comparators[0], node.test.left))
    if not any(
        direct_formal(formal)
        and isinstance(cutoff, ast.Constant)
        and isinstance(cutoff.value, (int, float))
        and not isinstance(cutoff.value, bool)
        and (not isinstance(cutoff.value, float) or math.isfinite(cutoff.value))
        for formal, cutoff in pairs
    ):
        return False
    arms = (node.body, node.orelse)
    return all(_mt_v21_display_string(arm) or p_format(arm) for arm in arms) and any(
        p_format(arm) for arm in arms
    )


def _mt_v2_expand_terminal_helpers(
    scope: tuple[ast.stmt, ...], helpers: Mapping[str, ast.FunctionDef], resolver: _Resolver
) -> tuple[ast.stmt, ...]:
    transformer = _MtV2TerminalHelperTransformer(helpers, resolver)
    return tuple(cast(ast.stmt, transformer.visit(statement)) for statement in scope)


def _mt22_canonical_terminal_scope(scope: tuple[ast.stmt, ...]) -> tuple[object, ...]:
    """Canonicalize the D6-visible AST, including its two provenance markers."""

    def node_value(node: ast.AST) -> object:
        fields = tuple((name, value_value(value)) for name, value in ast.iter_fields(node))
        attributes = tuple(
            (name, getattr(node, name, None))
            for name in ("lineno", "col_offset", "end_lineno", "end_col_offset")
        )
        markers = tuple(
            (name, bool(getattr(node, name, False)))
            for name in ("_sc_mt_presentation_helper", "_sc_mt_terminal_rendering")
        )
        return (node.__class__.__name__, fields, attributes, markers)

    def value_value(value: object) -> object:
        if isinstance(value, ast.AST):
            return node_value(value)
        if isinstance(value, list):
            return tuple(value_value(item) for item in value)
        return value

    return tuple(node_value(statement) for statement in scope)


def _mt_v2_expand_embedded_helper_sites(
    scope: tuple[ast.stmt, ...],
    *,
    helpers: Mapping[str, ast.FunctionDef],
    resolver: _Resolver,
) -> _Expansion:
    """Inline exact X4 calls occupying literal family-container leaves."""

    result: list[ast.stmt] = []
    for statement in scope:
        if not (
            isinstance(statement, (ast.Assign, ast.AnnAssign))
            and (value := statement.value) is not None
            and isinstance(value, (ast.List, ast.Tuple, ast.Dict))
        ):
            result.append(statement)
            continue
        leaves = value.values if isinstance(value, ast.Dict) else value.elts
        replacements: dict[ast.Call, ast.Name] = {}
        prelude: list[ast.stmt] = []
        for ordinal, leaf in enumerate(leaves):
            if not (
                isinstance(leaf, ast.Call)
                and isinstance(leaf.func, ast.Name)
                and (helper := helpers.get(leaf.func.id)) is not None
                and any(
                    isinstance(item, ast.Call) and resolver.qualified(item.func) in _MT_TEST_APIS
                    for item in _walk_helper_runtime(helper)
                )
            ):
                continue
            temporary = f"__sc_mt_embedded_{statement.lineno}_{ordinal}"
            replacement, reason = _inline_helper_site(
                call=leaf,
                target=ast.Name(id=temporary, ctx=ast.Store()),
                helper=helper,
                resolver=resolver,
                helpers=helpers,
                depth=1,
                group_values=("", ""),
            )
            if reason is not None or replacement is None:
                return _Expansion(None, reason or "helper-body-statement-unsupported")
            prelude.extend(replacement)
            replacements[leaf] = ast.Name(id=temporary, ctx=ast.Load())
        if not replacements:
            result.append(statement)
            continue

        class Replace(ast.NodeTransformer):
            def __init__(self, values: Mapping[ast.Call, ast.Name]) -> None:
                self.values = values

            def visit_Call(self, node: ast.Call) -> ast.AST:
                replacement = self.values.get(node)
                return (
                    copy.deepcopy(replacement)
                    if replacement is not None
                    else self.generic_visit(node)
                )

        rebuilt = Replace(replacements).visit(statement)
        assert isinstance(rebuilt, ast.stmt)
        result.extend(prelude)
        result.append(rebuilt)
    return _Expansion(tuple(result), None)


def _mt_v2_expand_nested_family_helper_arguments(
    scope: tuple[ast.stmt, ...],
    *,
    helpers: Mapping[str, ast.FunctionDef],
    resolver: _Resolver,
) -> _Expansion:
    """Inline an exact registered-family helper used as another call's argument."""

    result: list[ast.stmt] = []
    for statement in scope:
        if not (
            isinstance(statement, (ast.Assign, ast.AnnAssign))
            and (value := statement.value) is not None
            and isinstance(value, ast.Call)
        ):
            result.append(statement)
            continue
        nested = [
            argument
            for argument in (*value.args, *(item.value for item in value.keywords))
            if isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and (helper := helpers.get(argument.func.id)) is not None
            and any(
                isinstance(item, ast.Call) and resolver.qualified(item.func) in _MT_TEST_APIS
                for item in _walk_helper_runtime(helper)
            )
        ]
        if not nested:
            result.append(statement)
            continue
        if len(nested) != 1:
            return _Expansion(None, "helper-call-site-reentry-unsupported")
        call = nested[0]
        assert isinstance(call.func, ast.Name)
        helper = helpers[call.func.id]
        temporary = f"__sc_mt_nested_{statement.lineno}_{statement.col_offset}"
        replacement, reason = _inline_helper_site(
            call=call,
            target=ast.Name(id=temporary, ctx=ast.Store()),
            helper=helper,
            resolver=resolver,
            helpers=helpers,
            depth=1,
            group_values=("", ""),
        )
        if reason is not None or replacement is None:
            return _Expansion(None, reason or "helper-body-statement-unsupported")

        class Replace(ast.NodeTransformer):
            def __init__(self, target: ast.Call, name: str) -> None:
                self.target = target
                self.name = name

            def visit_Call(self, node: ast.Call) -> ast.AST:
                if node is self.target:
                    return ast.copy_location(ast.Name(id=self.name, ctx=ast.Load()), node)
                return self.generic_visit(node)

        rebuilt = Replace(call, temporary).visit(statement)
        assert isinstance(rebuilt, ast.stmt)
        result.extend(replacement)
        result.append(rebuilt)
    return _Expansion(tuple(result), None)


def _mt_v2_expand_literal_destructuring(
    scope: tuple[ast.stmt, ...],
) -> tuple[ast.stmt, ...]:
    result: list[ast.stmt] = []
    for statement in scope:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], (ast.Tuple, ast.List))
            and isinstance(statement.value, (ast.Tuple, ast.List))
            and len(statement.targets[0].elts) == len(statement.value.elts)
            and all(isinstance(item, ast.Name) for item in statement.targets[0].elts)
            and not any(isinstance(item, ast.Starred) for item in statement.targets[0].elts)
        ):
            result.append(statement)
            continue
        for target, value in zip(statement.targets[0].elts, statement.value.elts, strict=True):
            assignment = ast.Assign(targets=[copy.deepcopy(target)], value=copy.deepcopy(value))
            ast.copy_location(assignment, statement)
            result.append(assignment)
    return tuple(result)


def _mt_v21_record_schemas(tree: ast.Module, resolver: _Resolver) -> dict[str, tuple[str, ...]]:
    schemas: dict[str, tuple[str, ...]] = {}
    duplicates: set[str] = set()
    for statement in tree.body:
        fields: tuple[str, ...] | None = None
        name: str | None = None
        if isinstance(statement, ast.ClassDef):
            name = statement.name
            body = tuple(item for item in statement.body if not _is_docstring(item))
            decorator_ok = bool(
                len(statement.decorator_list) == 1
                and (
                    resolver.qualified(statement.decorator_list[0]) == "dataclasses.dataclass"
                    or (
                        isinstance(statement.decorator_list[0], ast.Call)
                        and resolver.qualified(statement.decorator_list[0].func)
                        == "dataclasses.dataclass"
                        and not statement.decorator_list[0].args
                        and not statement.decorator_list[0].keywords
                    )
                )
            )
            if (
                decorator_ok
                and not statement.bases
                and not statement.keywords
                and body
                and all(
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                    and item.simple == 1
                    and (item.value is None or _mt_closed_literal(item.value, resolver))
                    for item in body
                )
            ):
                values = tuple(
                    item.target.id
                    for item in body
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                )
                if len(values) == len(set(values)):
                    fields = values
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and resolver.qualified(statement.value.func) == "collections.namedtuple"
            and len(statement.value.args) == 2
            and not statement.value.keywords
        ):
            name = statement.targets[0].id
            typename = resolver.string(statement.value.args[0])
            raw_fields = resolver.sequence(statement.value.args[1])
            if raw_fields is None:
                text = resolver.string(statement.value.args[1])
                raw_fields = tuple(re.split(r"[\s,]+", text.strip())) if text is not None else None
            if (
                typename == name
                and raw_fields
                and all(
                    isinstance(item, str) and item.isidentifier() and not item.startswith("_")
                    for item in raw_fields
                )
                and len(raw_fields) == len(set(raw_fields))
            ):
                fields = cast(tuple[str, ...], tuple(raw_fields))
        if name is not None and fields is not None:
            if name in schemas:
                duplicates.add(name)
            schemas[name] = fields
    for name in duplicates:
        schemas.pop(name, None)
    return schemas


def _mt_v21_expand_records(
    scope: tuple[ast.stmt, ...],
    schemas: Mapping[str, tuple[str, ...]],
    *,
    outcome_columns: tuple[str, ...] = (),
    membership_sets: Mapping[str, frozenset[str]] | None = None,
) -> tuple[ast.stmt, ...]:
    if not schemas:
        return scope
    assignments = _assignment_expressions(scope)
    record_names: set[str] = {
        name
        for name, expression in assignments.items()
        if isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in schemas
    }
    builders: set[str] = set()
    for node in _walk_statements(scope):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and isinstance(node.func.value, ast.Name)
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Name)
            and node.args[0].func.id in schemas
        ):
            continue
        builders.add(node.func.value.id)
    loop_records = {
        node.target.id
        for node in _walk_statements(scope)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and isinstance(node.iter, ast.Name)
        and node.iter.id in builders
    }
    record_names.update(loop_records)
    field_union = set().union(*(set(fields) for fields in schemas.values()))

    class Expand(ast.NodeTransformer):
        def visit_Call(self, node: ast.Call) -> ast.AST:
            rebuilt = cast(ast.Call, self.generic_visit(node))
            if not isinstance(rebuilt.func, ast.Name) or rebuilt.func.id not in schemas:
                return rebuilt
            fields = schemas[rebuilt.func.id]
            if rebuilt.args and rebuilt.keywords:
                return rebuilt
            values: list[ast.expr] = []
            if rebuilt.args:
                if len(rebuilt.args) != len(fields) or any(
                    isinstance(item, ast.Starred) for item in rebuilt.args
                ):
                    return rebuilt
                values = list(rebuilt.args)
            else:
                mapping = {
                    item.arg: item.value for item in rebuilt.keywords if item.arg is not None
                }
                if len(mapping) != len(rebuilt.keywords) or set(mapping) != set(fields):
                    return rebuilt
                values = [mapping[field] for field in fields]
            replacement = ast.Dict(keys=[ast.Constant(field) for field in fields], values=values)
            replacement.__dict__["_sc_mt21_record"] = rebuilt.func.id
            return ast.copy_location(replacement, rebuilt)

        def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
            rebuilt = cast(ast.Attribute, self.generic_visit(node))
            if not (
                isinstance(rebuilt.ctx, ast.Load)
                and rebuilt.attr in field_union
                and isinstance(rebuilt.value, ast.Name)
                and rebuilt.value.id in record_names
            ):
                return rebuilt
            return ast.copy_location(
                ast.Subscript(
                    value=rebuilt.value,
                    slice=ast.Constant(rebuilt.attr),
                    ctx=ast.Load(),
                ),
                rebuilt,
            )

    return tuple(cast(ast.stmt, Expand().visit(copy.deepcopy(item))) for item in scope)


def _mt_v2_expand_record_loops(
    scope: tuple[ast.stmt, ...],
    family_size: int,
    resolver: _Resolver,
    *,
    outcome_columns: tuple[str, ...] = (),
    membership_sets: Mapping[str, frozenset[str]] | None = None,
) -> tuple[ast.stmt, ...]:
    assignments = _assignment_expressions(scope)
    builders: dict[str, list[ast.expr]] = defaultdict(list)
    for name, expression in assignments.items():
        if isinstance(expression, (ast.List, ast.Tuple)) and expression.elts:
            builders[name] = list(expression.elts)
    for node in _walk_statements(scope):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and isinstance(node.func.value, ast.Name)
            and len(node.args) == 1
            and not node.keywords
        ):
            continue
        initial = assignments.get(node.func.value.id)
        if isinstance(initial, ast.List) and not initial.elts:
            builders[node.func.value.id].append(node.args[0])
    aliases = dict(builders)
    changed = True
    while changed:
        changed = False
        for name, expression in assignments.items():
            if (
                isinstance(expression, ast.Name)
                and expression.id in aliases
                and name not in aliases
            ):
                aliases[name] = aliases[expression.id]
                changed = True
        for statement in scope:
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and isinstance(statement.value, ast.Name)
                and statement.value.id in aliases
            ):
                continue
            target_name = statement.targets[0].id
            alias_values = aliases[statement.value.id]
            if aliases.get(target_name) is not alias_values:
                aliases[target_name] = alias_values
                changed = True

    result: list[ast.stmt] = []
    materialized_records: dict[int, str] = {}
    emitted_records: set[str] = set()
    for statement in scope:
        if not isinstance(statement, ast.For) or statement.orelse:
            result.append(statement)
            continue
        iterable = statement.iter
        start = 0
        target = statement.target
        values: list[ast.expr] | None = None
        zip_vectors: list[str] = []
        if isinstance(iterable, ast.Name):
            values = aliases.get(iterable.id)
        elif isinstance(iterable, ast.Subscript) and isinstance(iterable.value, ast.Name):
            source = aliases.get(iterable.value.id)
            if source is not None and isinstance(iterable.slice, ast.Slice):
                lower = _mt_optional_literal_int(iterable.slice.lower)
                upper = _mt_optional_literal_int(iterable.slice.upper)
                step = _mt_optional_literal_int(iterable.slice.step)
                if step in {None, 1}:
                    values = source[slice(lower, upper, step)]
        elif (
            isinstance(iterable, ast.BinOp)
            and isinstance(iterable.op, ast.Add)
            and isinstance(iterable.left, ast.Name)
            and isinstance(iterable.right, ast.Name)
            and iterable.left.id in aliases
            and iterable.right.id in aliases
        ):
            values = [*aliases[iterable.left.id], *aliases[iterable.right.id]]
        elif (
            isinstance(iterable, ast.Call)
            and isinstance(iterable.func, ast.Name)
            and iterable.func.id == "enumerate"
            and iterable.args
            and isinstance(iterable.args[0], ast.Name)
            and isinstance(target, (ast.Tuple, ast.List))
            and len(target.elts) == 2
        ):
            values = aliases.get(iterable.args[0].id)
            if len(iterable.args) == 2:
                member = _mt_literal_member(iterable.args[1])
                if isinstance(member, int):
                    start = member
                else:
                    values = None
            elif iterable.keywords:
                if len(iterable.keywords) == 1 and iterable.keywords[0].arg == "start":
                    member = _mt_literal_member(iterable.keywords[0].value)
                    if isinstance(member, int):
                        start = member
                    else:
                        values = None
                else:
                    values = None
        elif (
            isinstance(iterable, ast.Call)
            and isinstance(iterable.func, ast.Name)
            and iterable.func.id == "zip"
            and len(iterable.args) >= 2
            and not iterable.keywords
            and isinstance(iterable.args[0], ast.Name)
            and (
                iterable.args[0].id in aliases
                or resolver.table(iterable.args[0]) is not None
                or resolver.sequence(iterable.args[0]) is not None
            )
            and all(isinstance(item, ast.Name) for item in iterable.args[1:])
            and isinstance(target, (ast.Tuple, ast.List))
            and len(target.elts) == len(iterable.args)
            and all(isinstance(item, ast.Name) for item in target.elts[1:])
            and (
                isinstance(target.elts[0], ast.Name)
                or (
                    isinstance(target.elts[0], (ast.Tuple, ast.List))
                    and all(isinstance(item, ast.Name) for item in target.elts[0].elts)
                )
            )
        ):
            values = aliases.get(iterable.args[0].id)
            if values is None:
                table = resolver.table(iterable.args[0])
                sequence = resolver.sequence(iterable.args[0])
                if table is not None:
                    values = [
                        ast.Tuple(
                            elts=[ast.Constant(cast(Any, member)) for member in row],
                            ctx=ast.Load(),
                        )
                        for row in table
                    ]
                elif sequence is not None:
                    values = [ast.Constant(cast(Any, member)) for member in sequence]
            zip_vectors = [cast(ast.Name, item).id for item in iterable.args[1:]]
        if values is None or not values or len(values) > family_size:
            result.append(statement)
            continue
        for ordinal, value in enumerate(values):
            record_value = value if isinstance(value, ast.Dict) else None
            if isinstance(value, ast.Dict):
                record_name = materialized_records.setdefault(
                    id(value), f"__sc_mt_record_{getattr(statement, 'lineno', 0)}_{ordinal}"
                )
                if record_name not in emitted_records:
                    assignment = ast.Assign(
                        targets=[ast.Name(id=record_name, ctx=ast.Store())],
                        value=copy.deepcopy(value),
                    )
                    ast.copy_location(assignment, statement)
                    result.append(assignment)
                    emitted_records.add(record_name)
                value = ast.Name(id=record_name, ctx=ast.Load())
            bindings: dict[str, ast.expr] = {}
            record_bindings: dict[str, ast.Dict] = {}
            if isinstance(target, ast.Name):
                bindings[target.id] = value
                if record_value is not None:
                    record_bindings[target.id] = record_value
            elif (
                isinstance(target, (ast.Tuple, ast.List))
                and len(target.elts) == 2
                and isinstance(target.elts[0], ast.Name)
                and isinstance(target.elts[1], ast.Name)
            ):
                bindings[target.elts[0].id] = ast.Constant(start + ordinal)
                bindings[target.elts[1].id] = value
            elif zip_vectors and isinstance(target, (ast.Tuple, ast.List)):
                first = target.elts[0]
                if isinstance(first, ast.Name):
                    bindings[first.id] = value
                elif (
                    isinstance(first, (ast.Tuple, ast.List))
                    and isinstance(value, (ast.Tuple, ast.List))
                    and len(first.elts) == len(value.elts)
                    and all(isinstance(item, ast.Name) for item in first.elts)
                ):
                    for target_item, value_item in zip(first.elts, value.elts, strict=True):
                        assert isinstance(target_item, ast.Name)
                        bindings[target_item.id] = value_item
                else:
                    result.append(statement)
                    break
                for target_item, vector in zip(target.elts[1:], zip_vectors, strict=True):
                    assert isinstance(target_item, ast.Name)
                    bindings[target_item.id] = ast.Subscript(
                        value=ast.Name(id=vector, ctx=ast.Load()),
                        slice=ast.Constant(ordinal),
                        ctx=ast.Load(),
                    )
            else:
                result.append(statement)
                break

            local_names = {
                target.id
                for body_statement in statement.body
                for descendant in ast.walk(body_statement)
                for target in (
                    descendant.targets
                    if isinstance(descendant, ast.Assign)
                    else (descendant.target,)
                    if isinstance(descendant, ast.AnnAssign)
                    else ()
                )
                if isinstance(target, ast.Name)
            }
            renames = {
                name: f"{name}__mt_{getattr(statement, 'lineno', 0)}_{ordinal}"
                for name in local_names
            }

            class Substitute(ast.NodeTransformer):
                def __init__(
                    self,
                    values: Mapping[str, ast.expr],
                    renamed: Mapping[str, str],
                    records: Mapping[str, ast.Dict],
                ) -> None:
                    self.values = values
                    self.renamed = renamed
                    self.records = records

                def visit_Name(self, node: ast.Name) -> ast.AST:
                    if isinstance(node.ctx, ast.Load) and node.id in self.values:
                        return ast.copy_location(copy.deepcopy(self.values[node.id]), node)
                    if node.id in self.renamed:
                        return ast.copy_location(
                            ast.Name(id=self.renamed[node.id], ctx=copy.deepcopy(node.ctx)), node
                        )
                    return node

                def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
                    if isinstance(node.value, ast.Name) and node.value.id in self.records:
                        member = _mt_literal_member(node.slice)
                        if member is not None:
                            record = self.records[node.value.id]
                            for key, value in zip(record.keys, record.values, strict=True):
                                if key is not None and _mt_literal_member(key) == member:
                                    return ast.copy_location(copy.deepcopy(value), node)
                    rebuilt = self.generic_visit(node)
                    assert isinstance(rebuilt, ast.Subscript)
                    member = _mt_literal_member(rebuilt.slice)
                    if isinstance(rebuilt.value, ast.Dict) and member is not None:
                        for key, value in zip(
                            rebuilt.value.keys, rebuilt.value.values, strict=True
                        ):
                            if key is not None and _mt_literal_member(key) == member:
                                return ast.copy_location(copy.deepcopy(value), node)
                    return rebuilt

            for body_statement in statement.body:
                copied = Substitute(bindings, renames, record_bindings).visit(
                    copy.deepcopy(body_statement)
                )
                assert isinstance(copied, ast.stmt)
                result.extend(
                    _mt_v2_fold_closed_membership_if(
                        copied,
                        resolver,
                        outcome_columns=outcome_columns,
                        membership_sets=membership_sets,
                    )
                )
    return tuple(result)


def _mt_v2_numpy_repeated_family_shape(tree: ast.Module, resolver: _Resolver) -> bool:
    repeated = any(
        isinstance(node, (ast.For, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
        for node in ast.walk(tree)
    )
    numpy_call = any(
        isinstance(node, ast.Call)
        and (api := resolver.qualified(node.func)) is not None
        and api.startswith("numpy.")
        for node in ast.walk(tree)
    )
    return repeated and numpy_call


def _mt_v2_unrecognized_correction_terminal_present(tree: ast.Module, resolver: _Resolver) -> bool:
    """See unresolved correction terminals globally without accepting their values."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        terminal = _mt_callee_terminal(node.func)
        if terminal is None:
            continue
        folded = terminal.lower()
        if folded not in _MT_CORRECTION_TERMINALS and not folded.startswith("benjamini"):
            continue
        if resolver.qualified(node.func) not in _MT_CORRECTION_APIS:
            return True
    return False


def _mt_v2_early_exit_numpy_family_gate(tree: ast.Module, resolver: _Resolver) -> bool:
    main = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"),
        None,
    )
    if main is None:
        return False
    if any(
        isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert) for node in ast.walk(main)
    ):
        # The opened-corpus negated-mask controls are guaranteed to stop at
        # operand proof; preserve that earlier design-pinned semantic reason.
        return False
    for index, statement in enumerate(main.body):
        if not (
            isinstance(statement, ast.If)
            and any(isinstance(node, ast.Return) for node in ast.walk(statement))
            and any(
                isinstance(loop, (ast.For, ast.AsyncFor))
                and _mt_contains_family_call(loop, resolver, {})
                for later in main.body[index + 1 :]
                for loop in ast.walk(later)
            )
        ):
            continue
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "to_numpy"
            for prior in main.body[: index + 1]
            for node in ast.walk(prior)
        ):
            return True
    return False


def _analyze_code_csv_multiple_testing_baseline(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Sequence[str],
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Prove one complete-family code conflict or return the first closed abstention."""

    try:
        tree = _bounded_parse(content)
        full_scope = tuple(item for item in tree.body if not _is_docstring(item))
        full_resolver, reason = _resolver(full_scope)
        if reason is not None or full_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        if _mt_v2_integrity_census(tree, full_resolver):
            return MultipleTestingDataflowResult(None, "api-resolution-ambiguous")
        membership_sets, membership_unstable = _mt22_d5_membership_sets(
            tree, full_resolver, outcome_columns
        )
        if membership_unstable:
            return MultipleTestingDataflowResult(None, "analysis-scope-structure-unsupported")
        contract_table_names = _mt22_d3_contract_table_names(tree, outcome_columns)

        scope, setup, helpers = _mt_v2_execution_scope(tree)
        top_level_helpers = {
            item.name: item
            for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name != "main"
        }
        helpers = {**top_level_helpers, **helpers}
        if not _mt_v2_outcome_sequences_stable(tree, full_resolver, outcome_columns):
            return MultipleTestingDataflowResult(None, "analysis-scope-structure-unsupported")
        if any(
            isinstance(node, (ast.Global, ast.Nonlocal))
            for statement in scope
            for node in ast.walk(statement)
        ):
            return MultipleTestingDataflowResult(None, "helper-global-nonlocal-unsupported")
        resolver, reason = _resolver((*setup, *scope))
        if reason is not None or resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        scope = _mt_v21_segmented_bindings(scope, tree, resolver)
        resolver, reason = _resolver((*setup, *scope))
        if reason is not None or resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")

        census, census_reason = _mt_call_census(
            tree,
            resolver=full_resolver,
            outcome_columns=outcome_columns,
        )
        if census_reason is not None:
            return MultipleTestingDataflowResult(None, census_reason)
        assert census is not None
        family_size = len(outcome_columns)
        if _mt_v2_early_exit_numpy_family_gate(tree, full_resolver):
            return MultipleTestingDataflowResult(None, "authorized-family-test-census-incomplete")
        if len(census) < family_size:
            if not census and _mt_v2_numpy_repeated_family_shape(tree, full_resolver):
                return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
            return MultipleTestingDataflowResult(None, "authorized-family-test-census-incomplete")
        if len(census) > family_size:
            return MultipleTestingDataflowResult(
                None, "extra-registered-test-outside-authorized-family"
            )
        apis = {item.api for item in census}
        if len(apis) != 1:
            return MultipleTestingDataflowResult(None, "mixed-test-api-family")
        if _mt_v2_unrecognized_correction_terminal_present(tree, full_resolver):
            return MultipleTestingDataflowResult(None, "unresolved-manual-correction-present")

        local_reader_paths = _mt23_local_reader_paths(
            tree,
            resolver=full_resolver,
            authorized_path=authorized_path,
            csv_header=tuple(csv_header),
            unit_column=outcome_columns[0],
            group_column=group_column,
        )
        readers = _mt_full_scope_reader_census(
            tree,
            resolver=full_resolver,
            local_paths=local_reader_paths,
            csv_header=tuple(csv_header),
            unit_column=outcome_columns[0],
            group_column=group_column,
        )
        operand_readers = _mt_v2_operand_reader_paths(tree, full_resolver, local_reader_paths)
        if any(path is not None and path != authorized_path for path in operand_readers) or (
            (None in operand_readers or bool(local_reader_paths))
            and any(path is not None and path != authorized_path for path in readers)
        ):
            return MultipleTestingDataflowResult(None, "additional-accepted-reader-present")
        if authorized_path not in readers:
            return MultipleTestingDataflowResult(None, "authorized-reader-lineage-unavailable")

        scope = _mt_v21_expand_counted_whiles(scope, resolver, outcome_columns)
        resolver, reason = _resolver((*setup, *scope))
        if reason is not None or resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        nested = _mt_v2_expand_nested_family_helper_arguments(
            scope,
            helpers=helpers,
            resolver=resolver,
        )
        if nested.reason is not None or nested.scope is None:
            return MultipleTestingDataflowResult(
                None,
                nested.reason
                if nested.reason in _MT_HELPER_REASONS
                else "helper-body-statement-unsupported",
            )
        normalized = _mt_expand_outcome_iterations(
            nested.scope,
            resolver=resolver,
            outcome_columns=outcome_columns,
            helpers=helpers,
            membership_sets=membership_sets,
        )
        if normalized is None:
            return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
        normalized = _mt_v2_expand_terminal_helpers(normalized, helpers, resolver)
        embedded = _mt_v2_expand_embedded_helper_sites(
            normalized, helpers=helpers, resolver=resolver
        )
        if embedded.reason is not None or embedded.scope is None:
            return MultipleTestingDataflowResult(
                None,
                embedded.reason
                if embedded.reason in _MT_HELPER_REASONS
                else "helper-body-statement-unsupported",
            )
        normalized = embedded.scope
        expansion = _expand_relevant_helpers(
            scope=normalized,
            helpers=helpers,
            resolver=resolver,
        )
        if expansion.reason is not None or expansion.scope is None:
            return MultipleTestingDataflowResult(
                None,
                expansion.reason
                if expansion.reason in _MT_HELPER_REASONS
                else "helper-body-statement-unsupported",
            )
        post_x4_resolver, reason = _resolver((*setup, *expansion.scope))
        if reason is not None or post_x4_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        d2 = _mt22_d2_normalize_family_calls(expansion.scope, post_x4_resolver, helpers)
        if d2.scope is None:
            return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
        post_d2_resolver, reason = _resolver((*setup, *d2.scope))
        if reason is not None or post_d2_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        post_d2_expansion = _expand_relevant_helpers(
            scope=d2.scope,
            helpers=helpers,
            resolver=post_d2_resolver,
        )
        if post_d2_expansion.reason is not None or post_d2_expansion.scope is None:
            return MultipleTestingDataflowResult(
                None,
                post_d2_expansion.reason
                if post_d2_expansion.reason in _MT_HELPER_REASONS
                else "helper-body-statement-unsupported",
            )
        final_x4_resolver, reason = _resolver((*setup, *post_d2_expansion.scope))
        if reason is not None or final_x4_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        marked_scope = _mt22_d2_mark_expanded_calls(
            post_d2_expansion.scope, d2.bindings, final_x4_resolver
        )
        if marked_scope is None:
            return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
        d6_once = _mt_v2_expand_terminal_helpers(marked_scope, helpers, final_x4_resolver)
        post_d6_resolver, reason = _resolver((*setup, *d6_once))
        if reason is not None or post_d6_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        d6_twice = _mt_v2_expand_terminal_helpers(copy.deepcopy(d6_once), helpers, post_d6_resolver)
        if _mt22_canonical_terminal_scope(d6_twice) != _mt22_canonical_terminal_scope(d6_once):
            return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
        expanded_once = _mt_v2_expand_literal_destructuring(d6_once)
        intermediate_resolver, reason = _resolver((*setup, *expanded_once))
        if reason is not None or intermediate_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        renormalized = _mt_expand_outcome_iterations(
            expanded_once,
            resolver=intermediate_resolver,
            outcome_columns=outcome_columns,
            helpers=helpers,
            membership_sets=membership_sets,
        )
        if renormalized is None:
            return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
        record_schemas = _mt_v21_record_schemas(tree, full_resolver)
        renormalized = _mt_v21_expand_records(
            renormalized,
            record_schemas,
            outcome_columns=outcome_columns,
            membership_sets=membership_sets,
        )
        intermediate_resolver, reason = _resolver((*setup, *renormalized))
        if reason is not None or intermediate_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        renormalized = _mt_v2_expand_record_loops(
            renormalized,
            family_size,
            intermediate_resolver,
            outcome_columns=outcome_columns,
            membership_sets=membership_sets,
        )
        expanded_scope = tuple(
            item
            for item in renormalized
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )
        if not _mt22_d2_occurrences_preserved(expanded_scope, d2.occurrence_keys):
            return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
        expanded_resolver, reason = _resolver((*setup, *expanded_scope))
        if reason is not None or expanded_resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
        rows = _mt_csv_rows(
            csv_content,
            csv_header=tuple(csv_header),
            group_column=group_column,
            group_values=group_values,
        )
        if rows is None:
            return MultipleTestingDataflowResult(None, "selected-group-row-completeness-unproven")
        engine = _MtEngine(
            source=content.decode("utf-8", errors="strict"),
            original_scope=full_scope,
            terminal_origin_scope=d6_once,
            scope=expanded_scope,
            resolver=expanded_resolver,
            full_resolver=full_resolver,
            authorized_path=authorized_path,
            group_column=group_column,
            outcome_columns=outcome_columns,
            group_values=group_values,
            csv_header=tuple(csv_header),
            csv_rows=rows,
            registered_api=next(iter(apis)),
            contract_table_names=contract_table_names,
            local_reader_paths=local_reader_paths,
        )
        return engine.run()
    except _SourceEnvelopeExceeded:
        return MultipleTestingDataflowResult(None, "dataflow-definition-ceiling-exceeded")
    except (ArithmeticError, RecursionError, UnicodeError, ValueError):
        return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")


def _mt_csv_rows(
    content: bytes,
    *,
    csv_header: tuple[str, ...],
    group_column: str,
    group_values: tuple[str, str],
) -> _MtCsvRows | None:
    try:
        text = content.decode("utf-8", errors="strict")
        raw = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    except (UnicodeError, csv.Error):
        return None
    if not raw or tuple(raw[0]) != csv_header or group_column not in csv_header:
        return None
    group_index = csv_header.index(group_column)
    if any(len(row) != len(csv_header) for row in raw[1:]):
        return None
    result: dict[str, frozenset[int]] = {
        value: frozenset(index for index, row in enumerate(raw[1:]) if row[group_index] == value)
        for value in group_values
    }
    if any(len(result[value]) < 2 for value in group_values):
        return None
    if set().union(*result.values()) != set(range(len(raw) - 1)):
        return None
    value_rows = {
        (header, value): frozenset(
            index for index, row in enumerate(raw[1:]) if row[column_index] == value
        )
        for column_index, header in enumerate(csv_header)
        for value in {row[column_index] for row in raw[1:]}
    }
    return _MtCsvRows(result, value_rows, frozenset(range(len(raw) - 1)))


def _mt_call_census(
    tree: ast.Module,
    *,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
) -> tuple[tuple[_MtCallInstance, ...] | None, str | None]:
    helpers_by_name: dict[str, list[ast.FunctionDef]] = defaultdict(list)
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef):
            helpers_by_name[statement.name].append(statement)
    if any(len(values) != 1 for values in helpers_by_name.values()):
        return None, "helper-definition-unavailable-or-nonunique"
    helpers = {name: values[0] for name, values in helpers_by_name.items()}
    instances: list[_MtCallInstance] = []
    called_helpers: set[str] = set()
    active: set[str] = set()

    def visit_expr(node: ast.AST, multiplier: int) -> str | None:
        if isinstance(node, ast.Lambda):
            return (
                "helper-body-statement-unsupported"
                if any(
                    isinstance(item, ast.Call) and resolver.qualified(item.func) in _MT_TEST_APIS
                    for item in ast.walk(node)
                )
                else None
            )
        if isinstance(node, ast.Call):
            api = resolver.qualified(node.func)
            if api in _MT_TEST_APIS:
                for _ in range(multiplier):
                    instances.append(_MtCallInstance(node, str(api), len(instances)))
            elif isinstance(node.func, ast.Name) and node.func.id in helpers:
                name = node.func.id
                called_helpers.add(name)
                if name in active:
                    return "helper-recursion-unsupported"
                helper = helpers[name]
                body = tuple(item for item in helper.body if not _is_docstring(item))
                parameters = [item.arg for item in helper.args.args]
                defaults = {
                    parameter: default
                    for parameter, default in zip(
                        parameters[len(parameters) - len(helper.args.defaults) :],
                        helper.args.defaults,
                        strict=True,
                    )
                }
                bound, _binding_reason = _bind_helper_arguments(node, parameters, defaults)
                if (
                    not helper.args.posonlyargs
                    and not helper.args.kwonlyargs
                    and helper.args.vararg is None
                    and helper.args.kwarg is None
                    and bound is not None
                ):

                    class Substitute(ast.NodeTransformer):
                        def __init__(self, bindings: Mapping[str, ast.expr]) -> None:
                            self.bindings = bindings

                        def visit_Name(self, value: ast.Name) -> ast.AST:
                            if (
                                isinstance(value.ctx, ast.Load)
                                and value.id in self.bindings
                                and not isinstance(self.bindings[value.id], ast.Call)
                            ):
                                return ast.copy_location(
                                    copy.deepcopy(self.bindings[value.id]), value
                                )
                            return value

                    body = tuple(
                        cast(ast.stmt, Substitute(bound).visit(copy.deepcopy(statement)))
                        for statement in body
                    )
                active.add(name)
                reason = visit_block(body, multiplier)
                active.remove(name)
                if reason is not None:
                    return reason
                for argument in (*node.args, *(item.value for item in node.keywords)):
                    reason = visit_expr(argument, multiplier)
                    if reason is not None:
                        return reason
                return None
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.stmt, ast.comprehension)):
                continue
            reason = visit_expr(child, multiplier)
            if reason is not None:
                return reason
        return None

    def visit_comprehension(node: ast.AST, multiplier: int) -> str | None:
        if not isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return None
        generators = node.generators
        if len(generators) != 1:
            if any(
                isinstance(item, ast.Call) and resolver.qualified(item.func) in _MT_TEST_APIS
                for item in ast.walk(node)
            ):
                return "test-battery-cardinality-unresolved"
            return None
        generator = generators[0]
        factor = _mt_exact_outcome_factor(
            generator.iter, resolver, outcome_columns, generator.target
        )
        if factor is None or generator.is_async or generator.ifs:
            if any(
                isinstance(item, ast.Call) and resolver.qualified(item.func) in _MT_TEST_APIS
                for item in ast.walk(node)
            ):
                return "test-battery-cardinality-unresolved"
            return None
        fields: list[ast.AST] = []
        if isinstance(node, ast.DictComp):
            fields.extend((node.key, node.value))
        else:
            fields.append(node.elt)
        for expression_field in fields:
            reason = visit_expr(expression_field, multiplier * factor)
            if reason is not None:
                return reason
        return None

    def visit_block(statements: Sequence[ast.stmt], multiplier: int) -> str | None:
        for statement in statements:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                factor = _mt_exact_outcome_factor(
                    statement.iter, resolver, outcome_columns, statement.target
                )
                carries = _mt_contains_family_call(statement, resolver, helpers)
                if factor is None:
                    if carries:
                        return "test-battery-cardinality-unresolved"
                    factor = 1
                if isinstance(statement, ast.AsyncFor) or statement.orelse:
                    if carries:
                        return "test-battery-cardinality-unresolved"
                reason = visit_expr(statement.iter, multiplier)
                if reason is not None:
                    return reason
                reason = visit_block(statement.body, multiplier * factor)
                if reason is not None:
                    return reason
                reason = visit_block(statement.orelse, multiplier)
                if reason is not None:
                    return reason
                continue
            if isinstance(statement, ast.While):
                proof = _mt_v21_counted_while(statement, statements, resolver, outcome_columns)
                if proof is not None:
                    reason = visit_expr(statement.test, multiplier)
                    if reason is not None:
                        return reason
                    reason = visit_block(
                        tuple(statement.body[:-1]), multiplier * len(outcome_columns)
                    )
                    if reason is not None:
                        return reason
                    continue
            if isinstance(statement, (ast.If, ast.While)):
                body_carries = any(
                    _mt_contains_family_call(item, resolver, helpers) for item in statement.body
                )
                conditional_family_loops = [
                    node
                    for node in ast.walk(statement)
                    if isinstance(node, (ast.For, ast.AsyncFor))
                    and _mt_contains_family_call(node, resolver, helpers)
                ]
                if any(
                    _mt_exact_outcome_factor(node.iter, resolver, outcome_columns, node.target)
                    is None
                    for node in conditional_family_loops
                ):
                    return "test-battery-cardinality-unresolved"
                if (
                    isinstance(statement.test, ast.Constant)
                    and statement.test.value is False
                    and body_carries
                ):
                    return "test-battery-cardinality-unresolved"
                if body_carries or any(
                    _mt_contains_family_call(item, resolver, helpers) for item in statement.orelse
                ):
                    return "authorized-family-test-census-incomplete"
                continue
            if isinstance(statement, (ast.Try, ast.Match, ast.With, ast.AsyncWith)):
                if _mt_contains_family_call(statement, resolver, helpers):
                    return "authorized-family-test-census-incomplete"
                continue
            for node in ast.walk(statement):
                if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                    reason = visit_comprehension(node, multiplier)
                    if reason is not None:
                        return reason
            expression_roots = _mt_statement_expression_roots(statement)
            for expression in expression_roots:
                if any(
                    expression is descendant
                    for comp in ast.walk(expression)
                    if isinstance(comp, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
                    for descendant in ast.walk(comp)
                ):
                    continue
                reason = visit_expr(expression, multiplier)
                if reason is not None:
                    return reason
        return None

    module_statements = tuple(
        item
        for item in tree.body
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not _is_docstring(item)
    )
    main = helpers.get("main")
    if main is not None and any(
        _exact_main_guard(item) for item in tree.body if isinstance(item, ast.If)
    ):
        called_helpers.add("main")
        active.add("main")
        reason = visit_block(tuple(item for item in main.body if not _is_docstring(item)), 1)
        active.remove("main")
    else:
        reason = visit_block(module_statements, 1)
    if reason is not None:
        return None, reason
    for name, helper in sorted(helpers.items()):
        if name in called_helpers or name == "main":
            continue
        reason = visit_block(tuple(item for item in helper.body if not _is_docstring(item)), 1)
        if reason is not None:
            return None, reason
    return tuple(instances), None


def _mt_contains_family_call(
    node: ast.AST,
    resolver: _Resolver,
    helpers: Mapping[str, ast.FunctionDef],
) -> bool:
    def helper_contains(name: str, active: frozenset[str] = frozenset()) -> bool:
        if name in active or (helper := helpers.get(name)) is None:
            return False
        for item in _walk_helper_runtime(helper):
            if not isinstance(item, ast.Call):
                continue
            if resolver.qualified(item.func) in _MT_TEST_APIS:
                return True
            if isinstance(item.func, ast.Name) and helper_contains(item.func.id, active | {name}):
                return True
        return False

    return any(
        isinstance(item, ast.Call)
        and (
            resolver.qualified(item.func) in _MT_TEST_APIS
            or (isinstance(item.func, ast.Name) and helper_contains(item.func.id))
        )
        for item in ast.walk(node)
    )


def _mt_v21_counted_while(
    statement: ast.While,
    statements: Sequence[ast.stmt],
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
) -> tuple[str, ast.expr] | None:
    """Return the exact R11 index/sequence pair, or refuse the loop."""

    if statement.orelse or not statement.body:
        return None
    try:
        offset = next(index for index, item in enumerate(statements) if item is statement)
    except StopIteration:
        return None
    if offset == 0:
        return None
    initializer = statements[offset - 1]
    if not (
        isinstance(initializer, ast.Assign)
        and len(initializer.targets) == 1
        and isinstance(initializer.targets[0], ast.Name)
        and isinstance(initializer.value, ast.Constant)
        and initializer.value.value == 0
        and not isinstance(initializer.value.value, bool)
    ):
        return None
    index_name = initializer.targets[0].id
    if not (
        isinstance(statement.test, ast.Compare)
        and isinstance(statement.test.left, ast.Name)
        and statement.test.left.id == index_name
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], ast.Lt)
        and len(statement.test.comparators) == 1
    ):
        return None
    limit = statement.test.comparators[0]
    sequence: ast.expr | None = None
    if (
        isinstance(limit, ast.Call)
        and resolver.qualified(limit.func) == "len"
        and len(limit.args) == 1
        and not limit.keywords
    ):
        sequence = limit.args[0]
    elif isinstance(limit, ast.Name) and _mt_binding_count(statements, limit.id) == 1:
        length_expr = _assignment_expressions(statements).get(limit.id)
        if (
            isinstance(length_expr, ast.Call)
            and resolver.qualified(length_expr.func) == "len"
            and len(length_expr.args) == 1
            and not length_expr.keywords
        ):
            sequence = length_expr.args[0]
    if sequence is None or resolver.sequence(sequence) != outcome_columns:
        return None
    final = statement.body[-1]
    if not (
        isinstance(final, ast.AugAssign)
        and isinstance(final.target, ast.Name)
        and final.target.id == index_name
        and isinstance(final.op, ast.Add)
        and isinstance(final.value, ast.Constant)
        and final.value.value == 1
        and not isinstance(final.value.value, bool)
    ):
        return None
    if any(
        isinstance(
            item,
            (
                ast.Break,
                ast.Continue,
                ast.Return,
                ast.Raise,
                ast.Yield,
                ast.YieldFrom,
                ast.Await,
                ast.For,
                ast.AsyncFor,
                ast.While,
            ),
        )
        for body_statement in statement.body[:-1]
        for item in ast.walk(body_statement)
    ):
        return None
    calls = [
        item
        for body_statement in statement.body[:-1]
        for item in ast.walk(body_statement)
        if isinstance(item, ast.Call) and resolver.qualified(item.func) in _MT_TEST_APIS
    ]
    if len(calls) != 1:
        return None
    allowed_stores = {initializer.targets[0], final.target}
    stores = {
        item
        for item in _walk_statements(statements)
        if isinstance(item, ast.Name)
        and item.id == index_name
        and isinstance(item.ctx, (ast.Store, ast.Del))
    }
    if stores != allowed_stores:
        return None
    return index_name, sequence


def _mt_v21_expand_counted_whiles(
    scope: tuple[ast.stmt, ...], resolver: _Resolver, outcome_columns: tuple[str, ...]
) -> tuple[ast.stmt, ...]:
    result: list[ast.stmt] = []
    for statement in scope:
        if not isinstance(statement, ast.While):
            result.append(statement)
            continue
        proof = _mt_v21_counted_while(statement, scope, resolver, outcome_columns)
        if proof is None:
            result.append(statement)
            continue
        index_name, _sequence = proof
        local_names = frozenset(
            name
            for body_statement in statement.body[:-1]
            for name in _store_names(body_statement)
            if name != index_name
        )
        for ordinal in range(len(outcome_columns)):
            transformer = _MtRowTransformer(
                {index_name: ordinal},
                f"__mt21_while_{statement.lineno}_{ordinal}",
                local_names,
            )
            for body_statement in statement.body[:-1]:
                copied = cast(ast.stmt, transformer.visit(copy.deepcopy(body_statement)))
                for item in ast.walk(copied):
                    item.__dict__["_sc_v22_loop_binding_ordinal"] = ordinal
                result.append(copied)
    return tuple(result)


def _mt_statement_expression_roots(statement: ast.stmt) -> tuple[ast.expr, ...]:
    if isinstance(statement, ast.Assign):
        return (statement.value,)
    if isinstance(statement, ast.AnnAssign) and statement.value is not None:
        return (statement.value,)
    if isinstance(statement, ast.AugAssign):
        return (statement.value,)
    if isinstance(statement, ast.Expr):
        return (statement.value,)
    if isinstance(statement, ast.Return) and statement.value is not None:
        return (statement.value,)
    if isinstance(statement, ast.If):
        return (statement.test,)
    if isinstance(statement, ast.While):
        return (statement.test,)
    if isinstance(statement, ast.Assert):
        return (statement.test,)
    if isinstance(statement, ast.Match):
        return (statement.subject,)
    return ()


def _mt_exact_outcome_factor(
    node: ast.expr,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
    target: ast.expr | None = None,
) -> int | None:
    if target is None:
        return None
    rows = _mt_outcome_iteration_bindings(node, target, resolver, outcome_columns)
    return len(rows) if rows is not None else None


def _mt_outcome_iteration_bindings(
    node: ast.expr,
    target: ast.expr,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
) -> list[Mapping[str, object]] | None:
    sequence = resolver.sequence(node)
    if (
        sequence is not None
        and sequence
        and all(isinstance(item, str) and item in outcome_columns for item in sequence)
        and len(set(sequence)) == len(sequence)
        and tuple(item for item in outcome_columns if item in sequence) == tuple(sequence)
        and isinstance(target, ast.Name)
    ):
        return [{target.id: outcome} for outcome in sequence]
    table = resolver.table(node)
    if (
        table is not None
        and table
        and isinstance(target, (ast.Tuple, ast.List))
        and all(isinstance(item, ast.Name) for item in target.elts)
    ):
        names = [cast(ast.Name, item).id for item in target.elts]
        if (
            len(names) == len(set(names))
            and all(len(row) == len(names) for row in table)
            and all(isinstance(row[0], str) and row[0] in outcome_columns for row in table)
            and len({row[0] for row in table}) == len(table)
            and tuple(item for item in outcome_columns if item in {row[0] for row in table})
            == tuple(row[0] for row in table)
        ):
            return [dict(zip(names, row, strict=True)) for row in table]
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enumerate"
        and 1 <= len(node.args) <= 2
        and isinstance(target, (ast.Tuple, ast.List))
        and len(target.elts) == 2
        and isinstance(target.elts[0], ast.Name)
    ):
        return None
    if any(item.arg != "start" for item in node.keywords) or len(node.keywords) > 1:
        return None
    if len(node.args) == 2 and node.keywords:
        return None
    start = 0
    start_node = (
        node.args[1] if len(node.args) == 2 else node.keywords[0].value if node.keywords else None
    )
    if start_node is not None:
        member = _mt_literal_member(start_node)
        if not isinstance(member, int):
            return None
        start = member
    value_target = target.elts[1]
    inner = _mt_outcome_iteration_bindings(node.args[0], value_target, resolver, outcome_columns)
    if inner is None:
        return None
    position_name = target.elts[0].id
    return [dict(values, **{position_name: start + index}) for index, values in enumerate(inner)]


class _MtOutcomeTransformer(ast.NodeTransformer):
    def __init__(
        self,
        target: str,
        value: str,
        suffix: str,
        rename_names: frozenset[str] = frozenset(),
    ) -> None:
        self.target = target
        self.value = value
        self.suffix = suffix
        self.rename_names = rename_names

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id == self.target and isinstance(node.ctx, ast.Load):
            return ast.copy_location(ast.Constant(value=self.value), node)
        if node.id in self.rename_names and node.id != self.target:
            replacement = ast.copy_location(
                ast.Name(id=f"{node.id}{self.suffix}", ctx=node.ctx), node
            )
            replacement.__dict__["_sc_mt_original_name"] = node.id
            return replacement
        return node


class _MtRowTransformer(ast.NodeTransformer):
    def __init__(
        self, values: Mapping[str, object], suffix: str, rename_names: frozenset[str]
    ) -> None:
        self.values = values
        self.suffix = suffix
        self.rename_names = rename_names

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self.values and isinstance(node.ctx, ast.Load):
            replacement: ast.expr = ast.copy_location(
                ast.Constant(value=cast(str | bool | int | float | None, self.values[node.id])),
                node,
            )
            replacement.__dict__["_sc_mt_row_derived"] = True
            return replacement
        if node.id in self.rename_names and node.id not in self.values:
            replacement = ast.copy_location(
                ast.Name(id=f"{node.id}{self.suffix}", ctx=node.ctx), node
            )
            replacement.__dict__["_sc_mt_original_name"] = node.id
            return replacement
        return node


@dataclass(frozen=True)
class _MtD2Normalization:
    scope: tuple[ast.stmt, ...] | None
    occurrence_keys: tuple[str, ...]
    bindings: tuple[tuple[str, str], ...]


def _mt22_d2_family_call(
    node: ast.AST, resolver: _Resolver, family_helpers: frozenset[str]
) -> bool:
    return bool(
        isinstance(node, ast.Call)
        and (
            resolver.qualified(node.func) in _MT_TEST_APIS
            or (isinstance(node.func, ast.Name) and node.func.id in family_helpers)
        )
    )


def _mt22_d2_call_key(call: ast.Call, occurrence: int) -> str:
    ordinal = getattr(call, "_sc_v22_loop_binding_ordinal", 0)
    return (
        f"{getattr(call, 'lineno', 0)}:{getattr(call, 'col_offset', 0)}:"
        f"{getattr(call, 'end_lineno', 0)}:{getattr(call, 'end_col_offset', 0)}:"
        f"{ordinal}:{occurrence}"
    )


def _mt22_d2_normalize_family_calls(
    scope: tuple[ast.stmt, ...],
    resolver: _Resolver,
    helpers: Mapping[str, ast.FunctionDef],
) -> _MtD2Normalization:
    """Hoist only eager registered calls below a simple one-target assignment."""

    family_helpers = frozenset(
        name
        for name, helper in helpers.items()
        if any(
            isinstance(node, ast.Call) and resolver.qualified(node.func) in _MT_TEST_APIS
            for node in ast.walk(helper)
        )
    )

    parsed_names = {
        node.id for statement in scope for node in ast.walk(statement) if isinstance(node, ast.Name)
    }
    counter = 0
    keys: list[str] = []
    bindings: list[tuple[str, str]] = []
    result: list[ast.stmt] = []

    for statement in scope:
        value: ast.expr | None = None
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            value = statement.value
        elif (
            isinstance(statement, ast.AnnAssign)
            and statement.simple == 1
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
            and _mt_closed_annotation(statement.annotation)
        ):
            value = statement.value

        if value is None:
            result.append(statement)
            continue

        parents = {
            child: parent for parent in ast.walk(value) for child in ast.iter_child_nodes(parent)
        }

        def record_payload_call(
            node: ast.AST,
            *,
            _value: ast.expr = value,
            _parents: Mapping[ast.AST, ast.AST] = parents,
        ) -> bool:
            cursor = node
            while cursor is not _value and (parent := _parents.get(cursor)) is not None:
                if isinstance(parent, ast.Dict) and cursor in parent.values:
                    return True
                cursor = parent
            return False

        family_calls = [
            node
            for node in ast.walk(value)
            if _mt22_d2_family_call(node, resolver, family_helpers) and record_payload_call(node)
        ]
        if not family_calls or (len(family_calls) == 1 and family_calls[0] is value):
            result.append(statement)
            continue

        guarded: set[ast.AST] = set()
        for owner in ast.walk(value):
            if isinstance(
                owner,
                (
                    ast.BoolOp,
                    ast.IfExp,
                    ast.Lambda,
                    ast.NamedExpr,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                    ast.Await,
                    ast.Yield,
                    ast.YieldFrom,
                ),
            ):
                guarded.update(ast.walk(owner))
        if any(call in guarded for call in family_calls):
            return _MtD2Normalization(None, (), ())

        for call in family_calls:
            call.__dict__["_sc_mt22_d2_record_payload"] = True

        prelude: list[ast.stmt] = []

        class Hoist(ast.NodeTransformer):
            def __init__(self, output: list[ast.stmt]) -> None:
                self.output = output

            def visit_Call(self, node: ast.Call) -> ast.AST:
                nonlocal counter
                rebuilt = self.generic_visit(node)
                assert isinstance(rebuilt, ast.Call)
                if not (
                    _mt22_d2_family_call(rebuilt, resolver, family_helpers)
                    and bool(getattr(node, "_sc_mt22_d2_record_payload", False))
                ):
                    return rebuilt
                counter += 1
                key = _mt22_d2_call_key(rebuilt, counter)
                name = (
                    "__sc_mt22_call_"
                    f"{getattr(rebuilt, 'lineno', 0)}_{getattr(rebuilt, 'col_offset', 0)}_"
                    f"{counter}"
                )
                if name in parsed_names:
                    raise ValueError("D2 generated-name collision")
                generated_target = ast.copy_location(ast.Name(id=name, ctx=ast.Store()), rebuilt)
                generated = ast.copy_location(
                    ast.Assign(targets=[generated_target], value=rebuilt), rebuilt
                )
                generated.__dict__["_sc_mt22_d2_occurrence"] = key
                rebuilt.__dict__["_sc_mt22_d2_occurrence"] = key
                generated_target.__dict__["_sc_mt22_d2_occurrence"] = key
                replacement = ast.copy_location(ast.Name(id=name, ctx=ast.Load()), rebuilt)
                replacement.__dict__["_sc_mt22_d2_occurrence"] = key
                self.output.append(generated)
                keys.append(key)
                bindings.append((name, key))
                return replacement

        rewritten = Hoist(prelude).visit(copy.deepcopy(statement))
        if not isinstance(rewritten, ast.stmt):
            return _MtD2Normalization(None, (), ())
        result.extend(prelude)
        result.append(rewritten)

    generated = [
        str(node.__dict__["_sc_mt22_d2_occurrence"])
        for statement in result
        for node in ast.walk(statement)
        if isinstance(node, ast.Call) and hasattr(node, "_sc_mt22_d2_occurrence")
    ]
    if Counter(generated) != Counter(keys) or any(value != 1 for value in Counter(keys).values()):
        return _MtD2Normalization(None, (), ())
    return _MtD2Normalization(tuple(result), tuple(keys), tuple(bindings))


def _mt22_d2_mark_expanded_calls(
    scope: tuple[ast.stmt, ...],
    bindings: tuple[tuple[str, str], ...],
    resolver: _Resolver,
) -> tuple[ast.stmt, ...] | None:
    expected = dict(bindings)
    found: set[str] = set()
    for statement in scope:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in expected
        ):
            continue
        calls = [
            node
            for node in ast.walk(statement.value)
            if isinstance(node, ast.Call) and resolver.qualified(node.func) in _MT_TEST_APIS
        ]
        if len(calls) != 1:
            return None
        key = expected[statement.targets[0].id]
        calls[0].__dict__["_sc_mt22_d2_occurrence"] = key
        found.add(statement.targets[0].id)
    return scope if found == set(expected) else None


def _mt22_d2_occurrences_preserved(scope: tuple[ast.stmt, ...], expected: tuple[str, ...]) -> bool:
    actual = [
        str(node.__dict__["_sc_mt22_d2_occurrence"])
        for statement in scope
        for node in ast.walk(statement)
        if isinstance(node, ast.Call) and hasattr(node, "_sc_mt22_d2_occurrence")
    ]
    return Counter(actual) == Counter(expected) and all(
        value == 1 for value in Counter(actual).values()
    )


_MT22_D5_SET_MUTATORS = frozenset(
    {
        "add",
        "update",
        "remove",
        "discard",
        "pop",
        "clear",
        "difference_update",
        "intersection_update",
        "symmetric_difference_update",
        "__ior__",
        "__iand__",
        "__ixor__",
        "__isub__",
    }
)


def _mt22_d5_set_values(node: ast.expr, outcome_columns: tuple[str, ...]) -> frozenset[str] | None:
    if not isinstance(node, ast.Set) or not 1 <= len(node.elts) <= len(outcome_columns):
        return None
    values: list[str] = []
    for item in node.elts:
        if not (
            isinstance(item, ast.Constant)
            and isinstance(item.value, str)
            and item.value
            and "\x00" not in item.value
            and len(item.value.encode("utf-8")) <= 128
            and item.value in outcome_columns
        ):
            return None
        values.append(item.value)
    return frozenset(values) if len(set(values)) == len(values) else None


def _mt22_d5_sorted_presentation(
    call: ast.Call, parents: Mapping[ast.AST, ast.AST], resolver: _Resolver
) -> bool:
    cursor: ast.AST = call
    while (parent := parents.get(cursor)) is not None:
        if isinstance(parent, (ast.FormattedValue, ast.JoinedStr)):
            cursor = parent
            continue
        if (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Attribute)
            and parent.func.attr == "join"
            and isinstance(parent.func.value, ast.Constant)
            and isinstance(parent.func.value.value, str)
            and cursor in parent.args
            and not parent.keywords
        ):
            cursor = parent
            continue
        if (
            isinstance(parent, ast.Call)
            and resolver.qualified(parent.func) == "print"
            and "print" not in resolver.builtins_shadowed
            and cursor in parent.args
        ):
            return True
        return False
    return False


def _mt22_d5_membership_sets(
    tree: ast.Module,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
) -> tuple[dict[str, frozenset[str]], bool]:
    """Resolve named set membership or report a used oracle whose stability is unproved."""

    roots: dict[str, tuple[frozenset[str], ast.stmt]] = {}
    for statement in tree.body:
        target, value = _mt_setup_target_value(statement)
        if target is None or value is None:
            continue
        members = _mt22_d5_set_values(value, outcome_columns)
        if members is not None:
            roots[target.id] = (members, statement)
    if not roots:
        return {}, False

    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    result: dict[str, frozenset[str]] = {}
    unstable = False
    for root, (members, root_statement) in roots.items():
        closure = {root}
        alias_statements: dict[str, ast.Assign | ast.AnnAssign] = {}
        changed = True
        while changed:
            changed = False
            for node in ast.walk(tree):
                if not isinstance(node, ast.stmt):
                    continue
                target, value = _mt_setup_target_value(node)
                if (
                    target is not None
                    and isinstance(value, ast.Name)
                    and value.id in closure
                    and target.id not in closure
                ):
                    closure.add(target.id)
                    alias_statements[target.id] = cast(ast.Assign | ast.AnnAssign, node)
                    changed = True

        used = False
        stable = True
        usable = True
        allowed_bindings: set[ast.AST] = {root_statement, *alias_statements.values()}
        binding_counts: Counter[str] = Counter()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in closure:
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    owner: ast.AST = node
                    while owner in parents and not isinstance(owner, ast.stmt):
                        owner = parents[owner]
                    binding_counts[node.id] += 1
                    if owner not in allowed_bindings:
                        stable = False
                elif isinstance(node.ctx, ast.Load):
                    load_owner = parents.get(node)
                    if isinstance(load_owner, (ast.Assign, ast.AnnAssign)):
                        _target, alias_value = _mt_setup_target_value(load_owner)
                        if alias_value is node and load_owner in alias_statements.values():
                            continue
                    if (
                        isinstance(load_owner, ast.Compare)
                        and len(load_owner.ops) == 1
                        and isinstance(load_owner.ops[0], (ast.In, ast.NotIn))
                        and load_owner.comparators == [node]
                    ):
                        used = True
                        continue
                    if (
                        isinstance(load_owner, ast.Call)
                        and isinstance(load_owner.func, ast.Name)
                        and load_owner.func.id == "sorted"
                        and load_owner.func.id not in resolver.builtins_shadowed
                        and load_owner.args == [node]
                        and not load_owner.keywords
                        and _mt22_d5_sorted_presentation(load_owner, parents, resolver)
                    ):
                        continue
                    if (
                        isinstance(load_owner, (ast.For, ast.AsyncFor, ast.comprehension))
                        and load_owner.iter is node
                    ):
                        usable = False
                        continue
                    if (
                        isinstance(load_owner, ast.Call)
                        and isinstance(load_owner.func, ast.Name)
                        and load_owner.func.id == "sorted"
                        and load_owner.args == [node]
                        and not load_owner.keywords
                    ):
                        usable = False
                        continue
                    stable = False
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
                if isinstance(node.value, ast.Name) and node.value.id in closure:
                    stable = False
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in closure
            ):
                stable = False
            if isinstance(node, (ast.Global, ast.Nonlocal)) and any(
                name in closure for name in node.names
            ):
                stable = False
            if isinstance(node, ast.arg) and node.arg in closure:
                stable = False
        if any(binding_counts[name] != 1 for name in closure):
            stable = False
        if used and not stable:
            unstable = True
        elif used and usable:
            result.update({name: members for name in closure})
    return result, unstable


def _mt22_d5_membership(
    node: ast.expr,
    membership_sets: Mapping[str, frozenset[str]],
    outcome_columns: tuple[str, ...],
) -> frozenset[str] | None:
    direct = _mt22_d5_set_values(node, outcome_columns)
    if direct is not None:
        return direct
    return membership_sets.get(node.id) if isinstance(node, ast.Name) else None


def _mt22_d3_contract_table_names(
    tree: ast.Module, outcome_columns: tuple[str, ...]
) -> frozenset[str]:
    """Return only immutable Name aliases of the exact ordered contract outcome table."""

    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    roots: dict[str, ast.stmt] = {}
    for statement in tree.body:
        target, value = _mt_setup_target_value(statement)
        if target is None or not isinstance(value, (ast.List, ast.Tuple)):
            continue
        table = _mt_closed_table(value)
        if table is None or any(not row or not isinstance(row[0], str) for row in table):
            continue
        headers = tuple(cast(str, row[0]) for row in table)
        if len(set(headers)) == len(headers) and headers == outcome_columns:
            roots[target.id] = statement

    approved: set[str] = set()
    for root, root_statement in roots.items():
        closure = {root}
        aliases: dict[str, ast.Assign | ast.AnnAssign] = {}
        changed = True
        while changed:
            changed = False
            for node in ast.walk(tree):
                if not isinstance(node, ast.stmt):
                    continue
                target, value = _mt_setup_target_value(node)
                if (
                    target is not None
                    and isinstance(value, ast.Name)
                    and value.id in closure
                    and target.id not in closure
                ):
                    closure.add(target.id)
                    aliases[target.id] = cast(ast.Assign | ast.AnnAssign, node)
                    changed = True

        allowed_bindings: set[ast.AST] = {root_statement, *aliases.values()}
        binding_counts: Counter[str] = Counter()
        valid = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in closure:
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    owner: ast.AST = node
                    while owner in parents and not isinstance(owner, ast.stmt):
                        owner = parents[owner]
                    binding_counts[node.id] += 1
                    if owner not in allowed_bindings:
                        valid = False
                    continue
                if not isinstance(node.ctx, ast.Load):
                    continue
                load_owner = parents.get(node)
                if isinstance(load_owner, (ast.Assign, ast.AnnAssign)):
                    _target, alias_value = _mt_setup_target_value(load_owner)
                    if alias_value is node and load_owner in aliases.values():
                        continue
                if isinstance(load_owner, (ast.For, ast.AsyncFor, ast.comprehension)):
                    if load_owner.iter is node:
                        continue
                if (
                    isinstance(load_owner, ast.Call)
                    and isinstance(load_owner.func, ast.Name)
                    and load_owner.func.id in _MT_SEQUENCE_READ_BUILTINS
                    and load_owner.func.id in _UNSHADOWED_BUILTINS
                    and any(argument is node for argument in load_owner.args)
                    and not any(isinstance(argument, ast.Starred) for argument in load_owner.args)
                    and all(keyword.arg is not None for keyword in load_owner.keywords)
                ):
                    continue
                if (
                    isinstance(load_owner, ast.Compare)
                    and len(load_owner.ops) == 1
                    and isinstance(load_owner.ops[0], (ast.In, ast.NotIn))
                    and load_owner.comparators == [node]
                ):
                    continue
                if (
                    isinstance(load_owner, ast.Subscript)
                    and load_owner.value is node
                    and isinstance(load_owner.ctx, ast.Load)
                ):
                    continue
                if isinstance(load_owner, ast.FormattedValue) and load_owner.value is node:
                    continue
                valid = False
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
                if isinstance(node.value, ast.Name) and node.value.id in closure:
                    valid = False
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in closure
            ):
                valid = False
            if isinstance(node, (ast.Global, ast.Nonlocal)) and any(
                name in closure for name in node.names
            ):
                valid = False
            if isinstance(node, ast.arg) and node.arg in closure:
                valid = False
        if valid and all(binding_counts[name] == 1 for name in closure):
            approved.update(closure)
    return frozenset(approved)


def _mt_expand_outcome_iterations(
    scope: tuple[ast.stmt, ...],
    *,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
    helpers: Mapping[str, ast.FunctionDef],
    membership_sets: Mapping[str, frozenset[str]] | None = None,
) -> tuple[ast.stmt, ...] | None:
    result: list[ast.stmt] = []
    for statement in scope:
        if isinstance(statement, ast.For):
            bindings = _mt_outcome_iteration_bindings(
                statement.iter, statement.target, resolver, outcome_columns
            )
            carries_family = _mt_contains_family_call(statement, resolver, helpers)
            admitted_continue = _mt_v21_closed_membership_continue(statement, resolver)
            invalid = bool(
                not isinstance(statement.target, (ast.Name, ast.Tuple, ast.List))
                or statement.orelse
                or any(
                    isinstance(node, (ast.Break, ast.Continue, ast.Await, ast.Yield, ast.YieldFrom))
                    and not (admitted_continue and isinstance(node, ast.Continue))
                    for node in ast.walk(statement)
                )
            )
            if bindings is None or invalid:
                if not carries_family:
                    result.append(copy.deepcopy(statement))
                    continue
                return None
            local_names = frozenset(
                name
                for body_statement in statement.body
                for name in _store_names(body_statement)
                if name not in set(_store_names(statement.target))
            )
            for ordinal, values in enumerate(bindings):
                transformer = _MtRowTransformer(
                    values, f"__mt_{statement.lineno}_{ordinal}", local_names
                )
                expanded_body: list[ast.stmt] = []
                stopped = False
                for body_statement in statement.body:
                    copied = transformer.visit(copy.deepcopy(body_statement))
                    assert isinstance(copied, ast.stmt)
                    for node in ast.walk(copied):
                        node.__dict__["_sc_v22_loop_binding_ordinal"] = ordinal
                    folded = _mt_v2_fold_closed_membership_if(
                        copied,
                        resolver,
                        outcome_columns=outcome_columns,
                        membership_sets=membership_sets,
                    )
                    if admitted_continue and any(isinstance(item, ast.Continue) for item in folded):
                        stopped = True
                        break
                    expanded_body.extend(folded)
                result.extend(expanded_body)
                if stopped:
                    continue
            continue
        copied = copy.deepcopy(statement)
        transformed = _mt_expand_comprehensions(copied, resolver, outcome_columns, helpers)
        if transformed is None:
            return None
        result.append(transformed)
    return tuple(result)


def _mt_v21_closed_membership_continue(node: ast.For, resolver: _Resolver) -> bool:
    continues = [item for item in ast.walk(node) if isinstance(item, ast.Continue)]
    if len(continues) != 1:
        return False
    owners = [
        item
        for item in node.body
        if isinstance(item, ast.If)
        and not item.orelse
        and len(item.body) == 1
        and item.body[0] is continues[0]
        and isinstance(item.test, ast.Compare)
        and len(item.test.ops) == 1
        and isinstance(item.test.ops[0], (ast.In, ast.NotIn))
        and len(item.test.comparators) == 1
        and resolver.sequence(item.test.comparators[0]) is not None
    ]
    return len(owners) == 1


def _mt_v2_fold_closed_membership_if(
    statement: ast.stmt,
    resolver: _Resolver,
    *,
    outcome_columns: tuple[str, ...] = (),
    membership_sets: Mapping[str, frozenset[str]] | None = None,
) -> tuple[ast.stmt, ...]:
    if not (
        isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], (ast.In, ast.NotIn))
        and len(statement.test.comparators) == 1
        and isinstance(statement.test.left, ast.Constant)
        and isinstance(statement.test.left.value, str)
    ):
        return (statement,)
    members: tuple[object, ...] | frozenset[str] | None = resolver.sequence(
        statement.test.comparators[0]
    )
    if members is None and membership_sets is not None:
        members = _mt22_d5_membership(
            statement.test.comparators[0], membership_sets, outcome_columns
        )
    if members is None:
        return (statement,)
    selected = statement.test.left.value in members
    if isinstance(statement.test.ops[0], ast.NotIn):
        selected = not selected
    return tuple(statement.body if selected else statement.orelse)


def _mt_expand_comprehensions(
    statement: ast.stmt,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
    helpers: Mapping[str, ast.FunctionDef],
) -> ast.stmt | None:
    class Transformer(ast.NodeTransformer):
        failed = False

        def _bindings(self, generator: ast.comprehension) -> list[Mapping[str, object]] | None:
            if generator.is_async or generator.ifs:
                return None
            return _mt_outcome_iteration_bindings(
                generator.iter, generator.target, resolver, outcome_columns
            )

        def _expand(
            self,
            node: ast.ListComp | ast.SetComp | ast.GeneratorExp,
            element: ast.expr,
        ) -> ast.expr:
            generators = node.generators
            if len(generators) != 1:
                self.failed = True
                return element
            generator = generators[0]
            bindings = self._bindings(generator)
            if bindings is None:
                if _mt_contains_family_call(node, resolver, helpers):
                    self.failed = True
                rebuilt = self.generic_visit(node)
                assert isinstance(rebuilt, ast.expr)
                return rebuilt
            values: list[ast.expr] = []
            for ordinal, row in enumerate(bindings):
                binding = _MtRowTransformer(row, f"__mt_comp_{ordinal}", frozenset())
                value = binding.visit(copy.deepcopy(element))
                assert isinstance(value, ast.expr)
                for item in ast.walk(value):
                    item.__dict__["_sc_v22_loop_binding_ordinal"] = ordinal
                values.append(value)
            replacement: ast.expr
            if isinstance(node, (ast.SetComp,)):
                replacement = ast.Set(elts=values)
            elif isinstance(node, (ast.GeneratorExp,)):
                replacement = ast.Tuple(elts=values, ctx=ast.Load())
            else:
                replacement = ast.List(elts=values, ctx=ast.Load())
            return ast.copy_location(replacement, node)

        def visit_ListComp(self, node: ast.ListComp) -> ast.AST:
            return self._expand(node, node.elt)

        def visit_SetComp(self, node: ast.SetComp) -> ast.AST:
            return self._expand(node, node.elt)

        def visit_GeneratorExp(self, node: ast.GeneratorExp) -> ast.AST:
            return self._expand(node, node.elt)

        def visit_DictComp(self, node: ast.DictComp) -> ast.AST:
            generators = node.generators
            if len(generators) != 1:
                if _mt_contains_family_call(node, resolver, helpers):
                    self.failed = True
                return self.generic_visit(node)
            generator = generators[0]
            bindings = self._bindings(generator)
            if bindings is None:
                if _mt_contains_family_call(node, resolver, helpers):
                    self.failed = True
                return self.generic_visit(node)
            keys: list[ast.expr | None] = []
            values: list[ast.expr] = []
            for ordinal, row in enumerate(bindings):
                binding = _MtRowTransformer(row, f"__mt_dict_{ordinal}", frozenset())
                key = binding.visit(copy.deepcopy(node.key))
                value = binding.visit(copy.deepcopy(node.value))
                assert isinstance(key, ast.expr) and isinstance(value, ast.expr)
                for item in ast.walk(value):
                    item.__dict__["_sc_v22_loop_binding_ordinal"] = ordinal
                keys.append(key)
                values.append(value)
            return ast.copy_location(ast.Dict(keys=keys, values=values), node)

    transformer = Transformer()
    value = transformer.visit(statement)
    if transformer.failed or not isinstance(value, ast.stmt):
        return None
    return value


class _MtEngine:
    def __init__(
        self,
        *,
        source: str,
        original_scope: tuple[ast.stmt, ...],
        terminal_origin_scope: tuple[ast.stmt, ...],
        scope: tuple[ast.stmt, ...],
        resolver: _Resolver,
        full_resolver: _Resolver,
        authorized_path: str,
        group_column: str,
        outcome_columns: tuple[str, ...],
        group_values: tuple[str, str],
        csv_header: tuple[str, ...],
        csv_rows: _MtCsvRows,
        registered_api: str,
        contract_table_names: frozenset[str],
        local_reader_paths: Mapping[_Mt23ReaderPathKey, str],
    ) -> None:
        self.source = source
        self.original_scope = original_scope
        self.terminal_origin_scope = terminal_origin_scope
        self.scope = scope
        self.resolver = resolver
        self.full_resolver = full_resolver
        self.authorized_path = authorized_path
        self.group_column = group_column
        self.outcome_columns = outcome_columns
        self.group_values = group_values
        self.csv_header = csv_header
        self.csv_rows = csv_rows
        self.registered_api = registered_api
        self.contract_table_names = contract_table_names
        self.local_reader_paths = local_reader_paths
        self.assignments = _assignment_expressions(scope)
        self.original_assignments = _assignment_expressions(original_scope)
        record_stores: dict[tuple[str, str | int], ast.expr] = {}
        duplicate_record_stores: set[tuple[str, str | int]] = set()
        for item in _walk_statements(scope):
            if not (
                isinstance(item, (ast.Assign, ast.AnnAssign)) and (value := item.value) is not None
            ):
                continue
            targets = item.targets if isinstance(item, ast.Assign) else [item.target]
            if len(targets) != 1 or not isinstance(targets[0], ast.Subscript):
                continue
            target = targets[0]
            member = _mt_literal_member(target.slice)
            if not isinstance(target.value, ast.Name) or member is None:
                continue
            key = (target.value.id, member)
            if key in record_stores:
                duplicate_record_stores.add(key)
            record_stores[key] = value
        for key in duplicate_record_stores:
            record_stores.pop(key, None)
        self.record_stores = record_stores
        nested_record_stores: dict[tuple[str, str | int, str | int], ast.expr] = {}
        duplicate_nested: set[tuple[str, str | int, str | int]] = set()
        for item in _walk_statements(scope):
            if not (
                isinstance(item, (ast.Assign, ast.AnnAssign)) and (value := item.value) is not None
            ):
                continue
            targets = item.targets if isinstance(item, ast.Assign) else [item.target]
            if len(targets) != 1 or not isinstance(targets[0], ast.Subscript):
                continue
            inner = targets[0]
            if not (
                isinstance(inner.value, ast.Subscript)
                and isinstance(inner.value.value, ast.Name)
                and (outer_member := _mt_literal_member(inner.value.slice)) is not None
                and (field_member := _mt_literal_member(inner.slice)) is not None
            ):
                continue
            nested_key = (inner.value.value.id, outer_member, field_member)
            if nested_key in nested_record_stores:
                duplicate_nested.add(nested_key)
            nested_record_stores[nested_key] = value
        for nested_key in duplicate_nested:
            nested_record_stores.pop(nested_key, None)
        self.nested_record_stores = nested_record_stores
        self.family_calls = tuple(
            sorted(
                (
                    node
                    for node in _walk_statements(scope)
                    if isinstance(node, ast.Call) and resolver.qualified(node.func) in _MT_TEST_APIS
                ),
                key=_position,
            )
        )
        self.call_position: dict[ast.Call, int] = {}
        self.call_outcome: dict[ast.Call, str] = {}
        self.result_names: dict[str, ast.Call] = {}
        self.direct_p_names: dict[str, ast.Call] = {}
        self.accepted_correction_calls: set[ast.Call] = set()
        self.accepted_manual_calls: set[ast.Call] = set()
        self.manual_multiplications: set[ast.BinOp] = set()
        self.correction_return_names: dict[str, tuple[_MtCorrection, str]] = {}
        self.unsupported_correction_return_names: set[str] = set()
        self.sinks = _registered_sinks(scope, resolver)
        self.terminal_closure = _Mt23TerminalClosure((), ())
        self._member_store_target_name_cache: frozenset[str] | None = None

    def run(self) -> MultipleTestingDataflowResult:
        reason = self._resolve_family_operands()
        if reason is not None:
            return MultipleTestingDataflowResult(None, reason)

        local_lineage_reason = self._local_pvalue_lineage_guard()
        if local_lineage_reason is not None:
            return MultipleTestingDataflowResult(None, local_lineage_reason)
        if self._upstream_sink_decision_present():
            return MultipleTestingDataflowResult(None, "upstream-correction-lineage-unresolved")

        if self._pvalue_family_collection_unresolved():
            return MultipleTestingDataflowResult(None, "pvalue-family-collection-unresolved")

        extremum = self._family_extremum_guard()
        if extremum:
            return MultipleTestingDataflowResult(None, "family-pvalue-extremum-reduction-present")

        corrections, reason = self._correction_census()
        if reason is not None:
            return MultipleTestingDataflowResult(None, reason)
        terminal_reason = self._correction_terminal_census()
        if terminal_reason is not None:
            return MultipleTestingDataflowResult(None, terminal_reason)
        before_origin = _mt22_canonical_terminal_scope(self.terminal_origin_scope)
        before_final = _mt22_canonical_terminal_scope(self.scope)
        self.terminal_closure = self._mt23_build_terminal_closure()
        repeated_closure = self._mt23_build_terminal_closure()
        if (
            self._mt23_closure_signature(self.terminal_closure)
            != self._mt23_closure_signature(repeated_closure)
            or before_origin != _mt22_canonical_terminal_scope(self.terminal_origin_scope)
            or before_final != _mt22_canonical_terminal_scope(self.scope)
        ):
            return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
        if self.terminal_closure.failure is not None:
            return MultipleTestingDataflowResult(None, self.terminal_closure.failure)
        transform_reason = self._off_grammar_transform_guard()
        if transform_reason is not None:
            return MultipleTestingDataflowResult(None, transform_reason)

        threshold_reason = self._decision_threshold_guard(
            recognized_correction_present=bool(self.accepted_correction_calls)
        )
        if threshold_reason is not None:
            return MultipleTestingDataflowResult(None, threshold_reason)

        guard_reason = self._order_16_guard(corrections)
        if guard_reason is not None:
            return MultipleTestingDataflowResult(None, guard_reason)

        conclusions, sink_kinds = self._conclusion_positions()
        if conclusions != set(range(len(self.outcome_columns))):
            return MultipleTestingDataflowResult(None, "pderived-conclusion-family-incomplete")
        if not sink_kinds:
            return MultipleTestingDataflowResult(None, "conclusion-output-sink-unavailable")

        corrected = set().union(*(item.positions for item in corrections)) if corrections else set()
        family = set(range(len(self.outcome_columns)))
        classification: Literal["none", "strict_subset", "complete"]
        if corrected == family:
            classification = "complete"
        elif corrected:
            classification = "strict_subset"
        else:
            classification = "none"
        spans = self._evidence_spans(corrections)
        return MultipleTestingDataflowResult(
            MultipleTestingDataflowFacts(
                registered_test_api=self.registered_api,
                registered_test_apis_by_position=tuple(
                    self.registered_api for _ in self.outcome_columns
                ),
                family_size=len(self.outcome_columns),
                corrected_positions=tuple(sorted(corrected)),
                conclusion_positions=tuple(sorted(conclusions)),
                correction_classification=classification,
                correction_methods=tuple(sorted({item.method for item in corrections})),
                output_sink_kinds=tuple(sorted(sink_kinds)),
                evidence_spans=spans,
            ),
            None,
        )

    def _resolve_family_operands(self) -> str | None:
        if len(self.family_calls) != len(self.outcome_columns):
            return "test-battery-cardinality-unresolved"
        seen: dict[str, ast.Call] = {}
        for call in self.family_calls:
            if len(call.args) != 2 or any(isinstance(item, ast.Starred) for item in call.args):
                return "test-operand-lineage-unresolved"
            if not self._test_keywords_supported(call):
                return "test-operand-lineage-unresolved"
            left = self._series(call.args[0], set(), 0)
            right = self._series(call.args[1], set(), 0)
            if left is None or right is None:
                if any(self._unsupported_astype(argument, set(), 0) for argument in call.args):
                    return "test-operand-lineage-unresolved"
                if any(self._negated_mask_operand(argument, set(), 0) for argument in call.args):
                    return "test-operand-lineage-unresolved"
                if self._structural_group_projection(
                    call.args[0]
                ) and self._structural_group_projection(call.args[1]):
                    return "selected-group-row-completeness-unproven"
                return "test-operand-lineage-unresolved"
            if (
                not left.reader_rooted
                or not right.reader_rooted
                or left.outcome is None
                or right.outcome is None
                or left.outcome != right.outcome
                or left.outcome not in self.outcome_columns
                or {left.group_value, right.group_value} != set(self.group_values)
            ):
                return "test-operand-lineage-unresolved"
            expected_left = self.csv_rows.group_rows.get(str(left.group_value), frozenset())
            expected_right = self.csv_rows.group_rows.get(str(right.group_value), frozenset())
            if (
                not left.complete_proved
                or not right.complete_proved
                or left.rows != expected_left
                or right.rows != expected_right
            ):
                return "selected-group-row-completeness-unproven"
            if left.outcome in seen:
                return "test-operand-lineage-unresolved"
            seen[left.outcome] = call
        if set(seen) != set(self.outcome_columns):
            return "test-operand-lineage-unresolved"
        for position, outcome in enumerate(self.outcome_columns):
            call = seen[outcome]
            self.call_position[call] = position
            self.call_outcome[call] = outcome
        for name, expression in self.assignments.items():
            if isinstance(expression, ast.Call) and expression in self.call_position:
                self.result_names[name] = expression
        for node in _walk_statements(self.scope):
            if not (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and (value := node.value) is not None
                and isinstance(value, ast.Call)
                and value in self.call_position
            ):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if len(targets) != 1 or not isinstance(targets[0], (ast.Tuple, ast.List)):
                continue
            target = targets[0]
            if (
                len(target.elts) == 2
                and not any(isinstance(item, ast.Starred) for item in target.elts)
                and isinstance(target.elts[1], ast.Name)
            ):
                self.direct_p_names[target.elts[1].id] = value
        return None

    def _negated_mask_operand(self, node: ast.AST, active: set[str], depth: int) -> bool:
        if depth > _DEFINITION_NODE_MAX:
            return False
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
            return True
        if isinstance(node, ast.Name):
            if node.id in active:
                return False
            expression = self.assignments.get(node.id)
            return bool(
                expression is not None
                and self._negated_mask_operand(expression, {*active, node.id}, depth + 1)
            )
        return any(
            self._negated_mask_operand(child, active, depth + 1)
            for child in ast.iter_child_nodes(node)
        )

    def _unsupported_astype(self, node: ast.expr, active: set[str], depth: int) -> bool:
        if depth > _DEFINITION_NODE_MAX:
            return True
        if isinstance(node, ast.Name):
            if node.id in active:
                return True
            expression = self.assignments.get(node.id)
            return bool(
                expression is not None
                and self._unsupported_astype(expression, {*active, node.id}, depth + 1)
            )
        for item in ast.walk(node):
            if not (
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr == "astype"
            ):
                continue
            if (
                len(item.args) != 1
                or item.keywords
                or isinstance(item.args[0], ast.Starred)
                or not _closed_dtype(item.args[0], self.resolver)
            ):
                return True
        return False

    def _structural_group_projection(self, node: ast.expr) -> bool:
        literals: set[str] = set()
        active: set[str] = set()

        def visit(expression: ast.expr, depth: int) -> None:
            if depth > _DEFINITION_NODE_MAX:
                return
            literals.update(
                str(item.value)
                for item in ast.walk(expression)
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            )
            for name in _loaded_names(expression):
                resolved = self.resolver.string(ast.Name(id=name, ctx=ast.Load()))
                if resolved is not None:
                    literals.add(resolved)
                if name in active:
                    continue
                bound = self.assignments.get(name)
                if bound is not None:
                    active.add(name)
                    visit(bound, depth + 1)
                    active.remove(name)

        visit(node, 0)
        return bool(
            self.group_column in literals
            and bool(set(self.group_values) & literals)
            and bool(set(self.outcome_columns) & literals)
        )

    def _test_keywords_supported(self, call: ast.Call) -> bool:
        api = self.resolver.qualified(call.func)
        permitted = (
            {
                "axis",
                "equal_var",
                "nan_policy",
                "permutations",
                "random_state",
                "alternative",
                "trim",
                "method",
                "keepdims",
            }
            if api == "scipy.stats.ttest_ind"
            else {"use_continuity", "alternative", "axis", "method", "nan_policy", "keepdims"}
        )
        if any(item.arg is None or item.arg not in permitted for item in call.keywords):
            return False
        return all(_mt_closed_literal(item.value, self.resolver) for item in call.keywords)

    def _series(self, node: ast.expr, active: set[str], depth: int) -> _MtSeries | None:
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            if expression is None:
                return None
            return self._series(expression, {*active, node.id}, depth + 1)
        if isinstance(node, ast.Attribute) and node.attr in {"values", "array"}:
            return self._series(node.value, active, depth + 1)
        if isinstance(node, ast.Call):
            api = self.resolver.qualified(node.func)
            if api in {"numpy.asarray", "numpy.array", "list", "tuple"}:
                if len(node.args) != 1 or node.keywords:
                    return None
                return self._series(node.args[0], active, depth + 1)
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "to_numpy",
                "tolist",
                "copy",
            }:
                if node.args or node.keywords:
                    return None
                return self._series(node.func.value, active, depth + 1)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "astype":
                if (
                    len(node.args) != 1
                    or node.keywords
                    or isinstance(node.args[0], ast.Starred)
                    or not _closed_dtype(node.args[0], self.resolver)
                ):
                    return None
                return self._series(node.func.value, active, depth + 1)
        projected = self._projected_series(node, active, depth)
        return projected

    def _frame(self, node: ast.expr, active: set[str], depth: int) -> _MtFrame | None:
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            if expression is None:
                return None
            return self._frame(expression, {*active, node.id}, depth + 1)
        if isinstance(node, ast.Call):
            api = self.resolver.qualified(node.func)
            if api == "pandas.read_csv":
                if (
                    len(node.args) != 1
                    or _mt23_reader_path(node, self.resolver, self.local_reader_paths)
                    != self.authorized_path
                ):
                    return None
                return _MtFrame(self.csv_rows.all_rows, None, True, True)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "query":
                return self._query_frame(node, active, depth)
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"copy"}:
                if node.args or node.keywords:
                    return None
                return self._frame(node.func.value, active, depth + 1)
        if isinstance(node, ast.Subscript):
            return self._bare_group_mask_frame(node, active, depth)
        return None

    def _identity_frame_expr(self, node: ast.expr, active: set[str]) -> ast.expr | None:
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            if isinstance(expression, ast.Name):
                return self._identity_frame_expr(expression, {*active, node.id})
        return node

    def _bare_group_mask_frame(
        self, node: ast.Subscript, active: set[str], depth: int
    ) -> _MtFrame | None:
        if not isinstance(node.ctx, ast.Load):
            return None
        parent = self._frame(node.value, active, depth + 1)
        mask = node.slice
        if (
            parent is None
            or not isinstance(mask, ast.Compare)
            or len(mask.ops) != 1
            or not isinstance(mask.ops[0], ast.Eq)
            or len(mask.comparators) != 1
        ):
            return None
        candidates = ((mask.left, mask.comparators[0]), (mask.comparators[0], mask.left))
        for column_node, value_node in candidates:
            if not isinstance(column_node, ast.Subscript):
                continue
            if self.resolver.string(column_node.slice) != self.group_column:
                continue
            selected_base = self._identity_frame_expr(node.value, set())
            column_base = self._identity_frame_expr(column_node.value, set())
            if (
                selected_base is None
                or column_base is None
                or ast.dump(selected_base, include_attributes=False)
                != ast.dump(column_base, include_attributes=False)
            ):
                continue
            value = self.resolver.string(value_node)
            if value not in self.group_values:
                continue
            rows = self.csv_rows.value_rows.get((self.group_column, str(value)))
            if rows is None:
                continue
            combined = parent.rows & rows
            return _MtFrame(
                combined,
                str(value),
                parent.reader_rooted,
                parent.complete_proved and combined == self.csv_rows.group_rows[str(value)],
            )
        return None

    def _projected_series(self, node: ast.expr, active: set[str], depth: int) -> _MtSeries | None:
        if not isinstance(node, ast.Subscript):
            return None
        if isinstance(node.value, ast.Attribute) and node.value.attr == "loc":
            if not isinstance(node.slice, ast.Tuple) or len(node.slice.elts) != 2:
                return None
            parent = self._frame(node.value.value, active, depth + 1)
            if parent is None:
                return None
            selected = self._mask_rows(node.slice.elts[0], parent, node.value.value)
            outcome = self.resolver.string(node.slice.elts[1])
            if selected is None or outcome not in self.outcome_columns:
                return None
            rows, group_value, exact_group = selected
            combined = parent.rows & rows
            return _MtSeries(
                combined,
                outcome,
                group_value or parent.group_value,
                parent.reader_rooted,
                parent.complete_proved and (exact_group or combined == parent.rows),
            )
        parent = self._frame(node.value, active, depth + 1)
        outcome = self.resolver.string(node.slice)
        if parent is not None and outcome in self.outcome_columns:
            return _MtSeries(
                parent.rows,
                outcome,
                parent.group_value,
                parent.reader_rooted,
                parent.complete_proved,
            )
        return None

    def _mask_rows(
        self, node: ast.expr, parent: _MtFrame, frame_expression: ast.expr | None = None
    ) -> tuple[frozenset[int], str | None, bool] | None:
        if isinstance(node, ast.Name):
            if _mt_binding_count(self.original_scope, node.id) != 1:
                return None
            mask_calls = [
                item
                for item in _walk_statements(self.original_scope)
                if isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and isinstance(item.func.value, ast.Name)
                and item.func.value.id == node.id
            ]
            if any(
                not isinstance(item.func, ast.Attribute)
                or item.func.attr != "sum"
                or item.args
                or item.keywords
                or not self._mt_v21_mask_sum_output_only(item)
                for item in mask_calls
            ):
                return None
            expression = self.assignments.get(node.id) or self.original_assignments.get(node.id)
            if expression is None:
                return None
            return self._mask_rows(expression, parent, frame_expression)
        if not (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and len(node.comparators) == 1
        ):
            return None
        candidates = ((node.left, node.comparators[0]), (node.comparators[0], node.left))
        for column_node, value_node in candidates:
            column = self._column_read(column_node)
            value = self.resolver.string(value_node)
            if column is None or value is None:
                continue
            if frame_expression is not None and isinstance(column_node, ast.Subscript):
                selected_base = self._identity_frame_expr(frame_expression, set())
                column_base = self._identity_frame_expr(column_node.value, set())
                if (
                    selected_base is None
                    or column_base is None
                    or ast.dump(selected_base, include_attributes=False)
                    != ast.dump(column_base, include_attributes=False)
                ):
                    continue
            rows = self.csv_rows.value_rows.get((column, value), frozenset())
            group_value = (
                value if column == self.group_column and value in self.group_values else None
            )
            exact_group = group_value is not None
            if column != self.group_column and parent.group_value is None:
                return None
            return rows, group_value, exact_group
        return None

    def _mt_v21_mask_sum_output_only(self, call: ast.Call) -> bool:
        sinks = tuple(
            sink
            for sink in _registered_sinks(self.original_scope, self.full_resolver)
            if sink.p_result_eligible
        )
        payloads = {payload for sink in sinks for payload in sink.payloads}
        parents = {
            child: parent
            for parent in _walk_statements(self.original_scope)
            for child in ast.iter_child_nodes(parent)
        }
        cursor: ast.AST = call
        while cursor not in payloads:
            parent = parents.get(cursor)
            if parent is None:
                return False
            if isinstance(parent, (ast.FormattedValue, ast.JoinedStr, ast.UnaryOp, ast.BinOp)):
                cursor = parent
                continue
            if (
                isinstance(parent, ast.Call)
                and self.full_resolver.qualified(parent.func) in {"int", "float", "str"}
                and len(parent.args) == 1
                and parent.args[0] is cursor
                and not parent.keywords
            ):
                cursor = parent
                continue
            return False
        return True

    def _column_read(self, node: ast.expr) -> str | None:
        if not isinstance(node, ast.Subscript):
            return None
        return self.resolver.string(node.slice)

    def _query_frame(self, call: ast.Call, active: set[str], depth: int) -> _MtFrame | None:
        if (
            len(call.args) != 1
            or call.keywords
            or not isinstance(call.args[0], ast.Constant)
            or not isinstance(call.args[0].value, str)
        ):
            return None
        match = _MT_QUERY.fullmatch(call.args[0].value)
        if match is None or not isinstance(call.func, ast.Attribute):
            return None
        parent = self._frame(call.func.value, active, depth + 1)
        if parent is None:
            return None
        header = match.group("header")
        value = match.group("value")
        rows = self.csv_rows.value_rows.get((header, value))
        if rows is None:
            return None
        selected = parent.rows & rows
        group_value = value if header == self.group_column and value in self.group_values else None
        if parent.group_value is None and group_value is None:
            return None
        row_preserving = selected == parent.rows
        complete = parent.complete_proved and (group_value is not None or row_preserving)
        return _MtFrame(
            selected,
            group_value or parent.group_value,
            parent.reader_rooted,
            complete,
        )

    def _p_origins(
        self, node: ast.expr, active: set[str] | None = None, depth: int = 0
    ) -> frozenset[int]:
        active = set() if active is None else active
        if depth > _DEFINITION_NODE_MAX:
            return frozenset()
        if isinstance(node, ast.Name):
            direct = self.direct_p_names.get(node.id)
            if direct is not None and direct in self.call_position:
                return frozenset({self.call_position[direct]})
            if node.id in active:
                return frozenset()
            expression = self.assignments.get(node.id)
            if expression is None:
                return frozenset()
            if (
                isinstance(expression, ast.IfExp)
                and isinstance(expression.body, ast.Constant)
                and isinstance(expression.body.value, str)
                and isinstance(expression.orelse, ast.Constant)
                and isinstance(expression.orelse.value, str)
            ):
                # The selected display value is not a numeric p identity. Its
                # decision provenance is retained by _decision_positions_in_expr,
                # while section 4.8 accounts for every consumer separately.
                return frozenset()
            return self._p_origins(expression, {*active, node.id}, depth + 1)
        if isinstance(node, ast.Attribute) and node.attr == "pvalue":
            call = self._result_call(node.value, active, depth + 1)
            if call is not None and call in self.call_position:
                return frozenset({self.call_position[call]})
            return frozenset()
        if isinstance(node, ast.Subscript):
            member = _mt_literal_member(node.slice)
            if member == 1:
                result_call = self._result_call(node.value, active, depth + 1)
                if result_call is not None and result_call in self.call_position:
                    return frozenset({self.call_position[result_call]})
            if isinstance(node.value, ast.Name):
                stored = (
                    self.record_stores.get((node.value.id, member)) if member is not None else None
                )
                if stored is not None:
                    return self._p_origins(stored, active, depth + 1)
                if member is not None:
                    precise, selected = self._precise_record_member(node.value.id, member, set(), 0)
                    if precise:
                        return (
                            self._p_origins(selected, active, depth + 1)
                            if selected is not None
                            else frozenset()
                        )
                expression = self.assignments.get(node.value.id)
                if isinstance(expression, (ast.List, ast.Tuple)) and isinstance(member, int):
                    index = member if member >= 0 else len(expression.elts) + member
                    if 0 <= index < len(expression.elts):
                        return self._p_origins(expression.elts[index], active, depth + 1)
                if isinstance(expression, ast.Dict) and member is not None:
                    for key, value in zip(expression.keys, expression.values, strict=True):
                        if key is not None and _mt_literal_member(key) == member:
                            return self._p_origins(value, active, depth + 1)
                if expression is not None:
                    aggregate = self._p_origins(expression, active, depth + 1)
                    if aggregate:
                        return aggregate
            return self._p_origins(node.value, active, depth + 1) | self._p_origins(
                node.slice, active, depth + 1
            )
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return frozenset().union(
                *(self._p_origins(item, active, depth + 1) for item in node.elts)
            )
        if isinstance(node, ast.Dict):
            return frozenset().union(
                *(
                    self._p_origins(item, active, depth + 1)
                    for item in (*node.keys, *node.values)
                    if item is not None
                )
            )
        if isinstance(node, ast.UnaryOp):
            return self._p_origins(node.operand, active, depth + 1)
        if isinstance(node, ast.BinOp):
            return self._p_origins(node.left, active, depth + 1) | self._p_origins(
                node.right, active, depth + 1
            )
        if isinstance(node, ast.BoolOp):
            return frozenset().union(
                *(self._p_origins(item, active, depth + 1) for item in node.values)
            )
        if isinstance(node, ast.Compare):
            return self._p_origins(node.left, active, depth + 1) | frozenset().union(
                *(self._p_origins(item, active, depth + 1) for item in node.comparators)
            )
        if isinstance(node, ast.IfExp):
            return (
                self._p_origins(node.test, active, depth + 1)
                | self._p_origins(node.body, active, depth + 1)
                | self._p_origins(node.orelse, active, depth + 1)
            )
        if isinstance(node, ast.Call):
            return frozenset().union(
                *(
                    self._p_origins(item, active, depth + 1)
                    for item in (*node.args, *(keyword.value for keyword in node.keywords))
                )
            )
        return frozenset().union(
            *(
                self._p_origins(child, active, depth + 1)
                for child in ast.iter_child_nodes(node)
                if isinstance(child, ast.expr)
            )
        )

    def _member_store_target_names(self) -> frozenset[str]:
        """Every name written through as a member in this scope, collected once.

        `_precise_record_member` asks, one name at a time, whether this scope holds any
        `name[...] = `, `name.attr = `, the annotated or augmented form of either, or a `del`
        of one.  The answer is a property of the scope and not of the name, and this engine's
        scope is the statement tuple it was constructed with, so the whole set is collected on
        the first question and every later question is a membership test against it.  The set
        is exactly the names the per-name walk it replaces would have matched.
        """

        cached = self._member_store_target_name_cache
        if cached is not None:
            return cached
        names: set[str] = set()
        for item in _walk_statements(self.scope):
            if isinstance(item, (ast.Assign, ast.Delete)):
                targets: list[ast.expr] = list(item.targets)
            elif isinstance(item, (ast.AnnAssign, ast.AugAssign)):
                targets = [item.target]
            else:
                continue
            for target in targets:
                if isinstance(target, (ast.Subscript, ast.Attribute)) and isinstance(
                    target.value, ast.Name
                ):
                    names.add(target.value.id)
        cached = frozenset(names)
        self._member_store_target_name_cache = cached
        return cached

    def _precise_record_member(
        self, name: str, member: str | int, active: set[str], depth: int
    ) -> tuple[bool, ast.expr | None]:
        if depth > _DEFINITION_NODE_MAX or name in active:
            return False, None

        if name in self._member_store_target_names():
            return False, None
        expression = self.assignments.get(name)
        if isinstance(expression, ast.Name):
            return self._precise_record_member(expression.id, member, {*active, name}, depth + 1)
        if (
            isinstance(expression, ast.Subscript)
            and isinstance(expression.value, ast.Name)
            and (outer_member := _mt_literal_member(expression.slice)) is not None
        ):
            stored = self.nested_record_stores.get((expression.value.id, outer_member, member))
            if stored is not None:
                return True, stored
            expression = self.record_stores.get((expression.value.id, outer_member))
        if not isinstance(expression, ast.Dict) or any(key is None for key in expression.keys):
            return False, None
        keys = [_mt_literal_member(cast(ast.expr, key)) for key in expression.keys]
        if any(key is None for key in keys) or len(keys) != len(set(keys)):
            return False, None
        matches = [
            value for key, value in zip(keys, expression.values, strict=True) if key == member
        ]
        return (True, matches[0]) if len(matches) == 1 else (False, None)

    def _result_call(self, node: ast.expr, active: set[str], depth: int) -> ast.Call | None:
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Call):
            return node if node in self.call_position else None
        if isinstance(node, ast.Name):
            if node.id in self.direct_p_names:
                return self.direct_p_names[node.id]
            if node.id in active:
                return None
            direct = self.result_names.get(node.id)
            if direct is not None:
                return direct
            expression = self.assignments.get(node.id)
            return (
                self._result_call(expression, {*active, node.id}, depth + 1)
                if expression is not None
                else None
            )
        if not isinstance(node, ast.Subscript):
            return None
        member = _mt_literal_member(node.slice)
        if member == 1:
            if isinstance(node.value, ast.Call) and node.value in self.call_position:
                return node.value
            if isinstance(node.value, ast.Name):
                direct = self.result_names.get(node.value.id)
                if direct is not None:
                    return direct
        if not isinstance(node.value, ast.Name) or member is None:
            return None
        expression = self.assignments.get(node.value.id)
        values: list[ast.expr] = []
        if isinstance(expression, (ast.List, ast.Tuple)):
            values.extend(expression.elts)
        elif isinstance(expression, ast.Dict):
            for key, value in zip(expression.keys, expression.values, strict=True):
                if key is not None and _mt_literal_member(key) == member:
                    return self._result_call(value, active, depth + 1)
            return None
        else:
            return None
        for call in sorted(
            (
                item
                for item in _walk_statements(self.scope)
                if isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and isinstance(item.func.value, ast.Name)
                and item.func.value.id == node.value.id
                and item.func.attr in {"append", "extend"}
            ),
            key=_position,
        ):
            if len(call.args) != 1 or call.keywords:
                return None
            call_func = cast(ast.Attribute, call.func)
            if call_func.attr == "append":
                values.append(call.args[0])
            elif isinstance(call.args[0], (ast.List, ast.Tuple)):
                values.extend(call.args[0].elts)
            else:
                return None
        if not isinstance(member, int):
            return None
        index = member if member >= 0 else len(values) + member
        return (
            self._result_call(values[index], active, depth + 1)
            if 0 <= index < len(values)
            else None
        )

    def _p_sequence_kind(
        self, node: ast.expr, active: set[str] | None = None, depth: int = 0
    ) -> Literal["list", "tuple"] | None:
        """Resolve the concrete container kind required by PSEQ production 4."""

        active = set() if active is None else active
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.List):
            return "list"
        if isinstance(node, ast.Tuple):
            return "tuple"
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            return (
                self._p_sequence_kind(expression, {*active, node.id}, depth + 1)
                if expression is not None
                else None
            )
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            return self._p_sequence_kind(node.value, active, depth + 1)
        if isinstance(node, ast.ListComp):
            return "list"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._p_sequence_kind(node.left, active, depth + 1)
            right = self._p_sequence_kind(node.right, active, depth + 1)
            return left if left is not None and left == right else None
        return None

    def _p_sequence(
        self, node: ast.expr, active: set[str] | None = None, depth: int = 0
    ) -> tuple[int, ...] | None:
        active = set() if active is None else active
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Name):
            if node.id in self.direct_p_names:
                call = self.direct_p_names[node.id]
                return (self.call_position[call],) if call in self.call_position else None
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            if expression is None:
                return None
            mutated = self._mutated_p_sequence(node.id, expression)
            if mutated is not None:
                return mutated
            return self._p_sequence(expression, {*active, node.id}, depth + 1)
        if isinstance(node, (ast.List, ast.Tuple)):
            values: list[int] = []
            for item in node.elts:
                origins = self._p_origins(item)
                if len(origins) != 1:
                    return None
                values.append(next(iter(origins)))
            return tuple(values)
        if isinstance(node, ast.Dict):
            values = []
            for item in node.values:
                origins = self._p_origins(item)
                if len(origins) != 1:
                    return None
                values.append(next(iter(origins)))
            return tuple(values)
        if isinstance(node, ast.Subscript):
            sequence = self._p_sequence(node.value, active, depth + 1)
            if sequence is None:
                return None
            if isinstance(node.slice, ast.Slice):
                lower = _mt_optional_literal_int(node.slice.lower)
                upper = _mt_optional_literal_int(node.slice.upper)
                step = _mt_optional_literal_int(node.slice.step)
                if (
                    (node.slice.lower is not None and lower is None)
                    or (node.slice.upper is not None and upper is None)
                    or (node.slice.step is not None and step is None)
                    or step not in {None, 1}
                ):
                    return None
                return sequence[slice(lower, upper, step)]
            member = _mt_literal_member(node.slice)
            if not isinstance(member, int):
                return None
            index = member if member >= 0 else len(sequence) + member
            return (sequence[index],) if 0 <= index < len(sequence) else None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left_kind = self._p_sequence_kind(node.left, active, depth + 1)
            right_kind = self._p_sequence_kind(node.right, active, depth + 1)
            if left_kind is None or left_kind != right_kind:
                return None
            left = self._p_sequence(node.left, active, depth + 1)
            right = self._p_sequence(node.right, active, depth + 1)
            return left + right if left is not None and right is not None else None
        if isinstance(node, ast.ListComp) and len(node.generators) == 1:
            generator = node.generators[0]
            if (
                not generator.is_async
                and not generator.ifs
                and isinstance(generator.target, (ast.Tuple, ast.List))
                and len(generator.target.elts) == 2
                and all(isinstance(item, ast.Name) for item in generator.target.elts)
                and isinstance(node.elt, ast.Name)
                and node.elt.id == cast(ast.Name, generator.target.elts[1]).id
                and isinstance(generator.iter, ast.Call)
                and self.resolver.qualified(generator.iter.func) == "zip"
                and len(generator.iter.args) == 2
                and not generator.iter.keywords
                and self.resolver.sequence(generator.iter.args[0]) == self.outcome_columns
            ):
                return self._p_sequence(generator.iter.args[1], active, depth + 1)
            if (
                not generator.is_async
                and not generator.ifs
                and isinstance(generator.target, ast.Name)
                and isinstance(node.elt, ast.Subscript)
                and isinstance(node.elt.value, ast.Name)
                and node.elt.value.id == generator.target.id
                and _mt_literal_member(node.elt.slice) is not None
            ):
                return self._p_sequence(generator.iter, active, depth + 1)
        origins = self._p_origins(node)
        return (next(iter(origins)),) if len(origins) == 1 else None

    def _mutated_p_sequence(self, name: str, initial: ast.expr) -> tuple[int, ...] | None:
        if not isinstance(initial, (ast.List, ast.Tuple)):
            return None
        values: list[int] = []
        for item in initial.elts:
            origins = self._p_origins(item)
            if len(origins) != 1:
                return None
            values.append(next(iter(origins)))
        mutated = False
        for node in sorted(
            (
                item
                for item in _walk_statements(self.scope)
                if isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and isinstance(item.func.value, ast.Name)
                and item.func.value.id == name
                and item.func.attr in {"append", "extend"}
            ),
            key=_position,
        ):
            mutated = True
            assert isinstance(node.func, ast.Attribute)
            if len(node.args) != 1 or node.keywords:
                return None
            if node.func.attr == "append":
                origins = self._p_origins(node.args[0])
                if len(origins) != 1:
                    return None
                values.append(next(iter(origins)))
            else:
                extended = self._p_sequence(node.args[0])
                if extended is None:
                    return None
                values.extend(extended)
        return tuple(values) if mutated else None

    def _local_pvalue_lineage_guard(self) -> str | None:
        parents = {
            child: parent
            for parent in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(parent)
        }
        for node in _walk_statements(self.scope):
            if (
                isinstance(node, ast.Attribute)
                and node.attr != "pvalue"
                and self._p_origins(node.value)
                and not (
                    isinstance((parent := parents.get(node)), ast.Call) and parent.func is node
                )
            ):
                return "unresolved-pvalue-consumer"
            if (
                isinstance(node, ast.Subscript)
                and self._p_origins(node.slice)
                and not self._r18_display_table(node, parents)
            ):
                return "unresolved-pvalue-consumer"
            if isinstance(node, (ast.NamedExpr, ast.Lambda, ast.Await)) and self._p_origins(node):
                return "unresolved-pvalue-consumer"
        allowed_call_ids = {sink.call for sink in self.sinks}
        for call in sorted(
            (node for node in _walk_statements(self.scope) if isinstance(node, ast.Call)),
            key=_position,
        ):
            api = self.resolver.qualified(call.func)
            if api == "pandas.DataFrame" and any(
                isinstance(argument, ast.Name)
                and self._closed_builder_positions(argument.id) is not None
                for argument in call.args
            ):
                return "unresolved-pvalue-consumer"
            direct = frozenset().union(
                *(
                    self._p_origins(item)
                    for item in (*call.args, *(keyword.value for keyword in call.keywords))
                )
            )
            if isinstance(call.func, ast.Attribute):
                direct |= self._p_origins(call.func.value)
            carries_family_sequence = any(
                self._p_sequence_kind(item) is not None and self._p_sequence(item) is not None
                for item in (*call.args, *(keyword.value for keyword in call.keywords))
            )
            if not direct and not carries_family_sequence:
                continue
            terminal = _mt_callee_terminal(call.func)
            if (
                call in allowed_call_ids
                or api in _MT_CORRECTION_APIS
                or self._recognized_extremum(call)
                or self._presentation_join(call)
                or (
                    terminal is not None
                    and (
                        terminal.lower() in _MT_CORRECTION_TERMINALS
                        or terminal.lower().startswith("benjamini")
                    )
                )
                or api
                in {
                    "min",
                    "max",
                    "sorted",
                    "numpy.min",
                    "numpy.max",
                    "numpy.nanmin",
                    "numpy.nanmax",
                    "numpy.sort",
                    "numpy.array",
                    "numpy.asarray",
                    "numpy.minimum",
                    "pandas.Series",
                }
                or api in _UNSHADOWED_BUILTINS
                or (api is not None and api.startswith("numpy."))
                or terminal
                in {
                    "append",
                    "extend",
                    "add",
                    "format",
                    *_MT_UNRECOGNIZED_EXTREMUM_TERMINALS,
                }
            ):
                continue
            return "unresolved-pvalue-consumer"
        for node in _walk_statements(self.scope):
            if not (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and (value := node.value) is not None
                and self._p_origins(value)
            ):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Attribute) for target in targets):
                return "unresolved-pvalue-consumer"
        for sink in self.sinks:
            origins = frozenset().union(*(self._p_origins(item) for item in sink.payloads))
            if origins and not sink.p_result_eligible:
                return "unresolved-pvalue-consumer"
        return None

    def _r18_display_table(self, node: ast.Subscript, parents: Mapping[ast.AST, ast.AST]) -> bool:
        table: ast.expr = node.value
        if isinstance(table, ast.Name):
            if _mt_binding_count(self.original_scope, table.id) != 1:
                return False
            expression = self.assignments.get(table.id) or self.original_assignments.get(table.id)
            if expression is None:
                return False
            table = expression
        if not (
            isinstance(table, (ast.List, ast.Tuple))
            and len(table.elts) == 2
            and all(_mt_v21_display_string(item) for item in table.elts)
            and isinstance(node.slice, ast.Call)
            and self.resolver.qualified(node.slice.func) == "int"
            and len(node.slice.args) == 1
            and not node.slice.keywords
            and len(self._decision_positions_in_expr(node.slice.args[0], set(), 0)) == 1
        ):
            return False
        return self._mt_v2_rendering_load_reaches_sink(node, parents)

    def _pvalue_family_collection_unresolved(self) -> bool:
        """Refuse family containers whose ordered member identity cannot be reconstructed."""

        p_record_containers = {
            container
            for (container, _), value in self.record_stores.items()
            if self._p_origins(value)
        }

        def unresolved_record_store(target: ast.expr) -> bool:
            if not isinstance(target, ast.Subscript):
                return False
            root: ast.expr = target
            while isinstance(root, (ast.Subscript, ast.Attribute)):
                root = root.value
            if not isinstance(root, ast.Name) or root.id not in p_record_containers:
                return False
            member = _mt_literal_member(target.slice)
            if isinstance(target.value, ast.Name):
                return member is None or (target.value.id, member) not in self.record_stores
            if (
                isinstance(target.value, ast.Subscript)
                and isinstance(target.value.value, ast.Name)
                and (outer := _mt_literal_member(target.value.slice)) is not None
                and member is not None
            ):
                return (
                    target.value.value.id,
                    outer,
                    member,
                ) not in self.nested_record_stores
            return True

        if any(
            unresolved_record_store(target)
            for item in _walk_statements(self.scope)
            if isinstance(item, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete))
            for target in (
                item.targets
                if isinstance(item, ast.Assign)
                else [item.target]
                if isinstance(item, (ast.AnnAssign, ast.AugAssign))
                else item.targets
            )
        ):
            return True

        parents = {
            child: parent
            for parent in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(parent)
        }
        for node in _walk_statements(self.scope):
            if (
                isinstance(node, ast.JoinedStr)
                and bool(getattr(node, "_sc_mt_presentation_helper", False))
                and self._p_origins(node)
                and len(self._p_origins(node)) != 1
            ):
                return True
            if isinstance(node, ast.Set) and self._p_origins(node):
                return True
            if isinstance(node, (ast.List, ast.Tuple, ast.Dict)) and self._p_origins(node):
                if isinstance(node, (ast.List, ast.Tuple)) and isinstance(node.ctx, ast.Store):
                    continue
                if isinstance(node, (ast.List, ast.Tuple)) and _mt_v21_percent_payload(
                    node, parents
                ):
                    continue
                if (
                    isinstance(node, (ast.List, ast.Tuple))
                    and len(self._p_origins(node)) == 1
                    and isinstance((owner := parents.get(node)), ast.Call)
                    and isinstance(owner.func, ast.Attribute)
                    and owner.func.attr == "append"
                    and len(owner.args) == 1
                    and owner.args[0] is node
                    and not owner.keywords
                ):
                    continue
                # One reconstructable family record may contain arbitrary non-p
                # descriptive fields plus one exact p field.
                if (
                    isinstance(node, ast.Dict)
                    and len(self._p_origins(node)) == 1
                    and not any(key is not None and self._p_origins(key) for key in node.keys)
                ):
                    continue
                if self._p_sequence(node) is None:
                    return True
            if isinstance(node, ast.Subscript) and self._p_origins(node):
                if len(self._p_origins(node)) == 1:
                    continue
                if self._recognized_filtered_family_membership(node, parents):
                    continue
                if self._p_sequence(node.value) is not None and self._p_sequence(node) is None:
                    return True
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.attr in {"append", "extend"}
                and any(self._p_origins(item) for item in node.args)
            ):
                continue
            initial = self.assignments.get(node.func.value.id)
            if initial is None or self._mutated_p_sequence(node.func.value.id, initial) is None:
                return True
        return False

    def _recognized_filtered_family_membership(
        self, node: ast.Subscript, parents: Mapping[ast.AST, ast.AST]
    ) -> bool:
        cursor: ast.AST = node
        while (parent := parents.get(cursor)) is not None:
            if isinstance(parent, (ast.ListComp, ast.SetComp)):
                if len(parent.generators) != 1:
                    return False
                generator = parent.generators[0]
                return bool(
                    not generator.is_async
                    and len(generator.ifs) == 1
                    and self._p_origins(generator.ifs[0])
                    and _mt_outcome_iteration_bindings(
                        generator.iter,
                        generator.target,
                        self.resolver,
                        self.outcome_columns,
                    )
                    is not None
                )
            if isinstance(parent, ast.stmt):
                return False
            cursor = parent
        return False

    def _upstream_sink_decision_present(self) -> bool:
        for sink in self.sinks:
            if not sink.p_result_eligible:
                continue
            for payload in sink.payloads:
                for node in ast.walk(payload):
                    if not isinstance(node, ast.Compare) or self._p_origins(node):
                        continue
                    if self._reader_projection_present(node):
                        return True
        return False

    def _reader_projection_present(self, node: ast.AST) -> bool:
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                api = self.resolver.qualified(item.func)
                if api in {
                    "numpy.genfromtxt",
                    "numpy.load",
                    "numpy.loadtxt",
                    "json.load",
                }:
                    return True
                if api == "pandas.read_csv" and item.args:
                    path = self.resolver.string(item.args[0])
                    if path is None or path != self.authorized_path:
                        return True
        for name in _loaded_names(node):
            expression = self.assignments.get(name)
            if expression is not None and expression is not node:
                if self._reader_projection_present(expression):
                    return True
        return False

    def _family_extremum_guard(self) -> bool:
        for sink in self.sinks:
            if not sink.p_result_eligible:
                continue
            if any(self._contains_extremum(payload, set(), 0) for payload in sink.payloads):
                return True
        return False

    def _contains_extremum(self, node: ast.expr, active: set[str], depth: int) -> bool:
        if depth > _DEFINITION_NODE_MAX:
            return False
        if isinstance(node, ast.Name):
            if node.id in active:
                return False
            expression = self.assignments.get(node.id)
            return bool(
                expression is not None
                and self._contains_extremum(expression, {*active, node.id}, depth + 1)
            )
        if self._recognized_extremum(node):
            return True
        return any(
            self._contains_extremum(child, active, depth + 1)
            for child in ast.iter_child_nodes(node)
            if isinstance(child, ast.expr)
        )

    def _recognized_extremum(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Call):
            api = self.resolver.qualified(node.func)
            if api in {"min", "max"} and len(node.args) == 1 and not node.keywords:
                return len(self._p_origins(node.args[0])) >= 2
            if api in {"numpy.min", "numpy.max", "numpy.nanmin", "numpy.nanmax"}:
                if len(node.args) != 1 or node.keywords:
                    return False
                payload = node.args[0]
                if isinstance(payload, ast.Call) and self.resolver.qualified(payload.func) in {
                    "numpy.array",
                    "numpy.asarray",
                }:
                    if len(payload.args) != 1 or payload.keywords:
                        return False
                    payload = payload.args[0]
                return len(self._p_origins(payload)) >= 2
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"min", "max"}
                and not node.args
                and not node.keywords
            ):
                return len(self._p_origins(node.func.value)) >= 2
        if not isinstance(node, ast.Subscript) or _mt_literal_member(node.slice) not in {0, -1}:
            return False
        index = _mt_literal_member(node.slice)
        value = node.value
        if isinstance(value, ast.Call):
            api = self.resolver.qualified(value.func)
            if api in {"sorted", "numpy.sort"} and len(value.args) == 1 and not value.keywords:
                return len(self._p_origins(value.args[0])) >= 2
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "iloc"
            and isinstance(value.value, ast.Call)
            and isinstance(value.value.func, ast.Attribute)
            and value.value.func.attr == "sort_values"
            and not value.value.args
            and not value.value.keywords
            and index in {0, -1}
        ):
            return len(self._p_origins(value.value.func.value)) >= 2
        return False

    def _correction_census(
        self,
    ) -> tuple[tuple[_MtCorrection, ...], str | None]:
        corrections: list[_MtCorrection] = []
        for call in sorted(
            (
                node
                for node in _walk_statements(self.scope)
                if isinstance(node, ast.Call)
                and self.resolver.qualified(node.func) in _MT_CORRECTION_APIS
            ),
            key=_position,
        ):
            correction, reason = self._recognized_correction(call)
            if reason is not None:
                return (), reason
            assert correction is not None
            corrections.append(correction)
            self.accepted_correction_calls.add(call)
            self._bind_correction_return(call, correction)
        manual, reason = self._manual_corrections()
        if reason is not None:
            return (), reason
        corrections.extend(manual)
        if not self._correction_returns_supported():
            return (), "correction-family-lineage-unresolved"
        if any(not item.positions for item in corrections):
            return (), "correction-family-lineage-unresolved"
        return tuple(corrections), None

    def _recognized_correction(self, call: ast.Call) -> tuple[_MtCorrection | None, str | None]:
        api = self.resolver.qualified(call.func)
        assert api in _MT_CORRECTION_APIS
        input_keyword = {
            "statsmodels.stats.multitest.multipletests": "pvals",
            "statsmodels.stats.multitest.fdrcorrection": "pvals",
            "scipy.stats.false_discovery_control": "ps",
            "sc_referee.calculation_checks.bh.benjamini_hochberg": "p_values",
        }[str(api)]
        payload: ast.expr | None = None
        if len(call.args) == 1:
            payload = call.args[0]
        elif not call.args:
            matches = [item.value for item in call.keywords if item.arg == input_keyword]
            if len(matches) == 1:
                payload = matches[0]
        if payload is None or any(isinstance(item, ast.Starred) for item in call.args):
            return None, "correction-family-lineage-unresolved"
        ordered_positions = self._p_sequence(payload)
        if ordered_positions is None or not ordered_positions:
            return None, "correction-family-lineage-unresolved"
        positions = frozenset(ordered_positions)
        if len(positions) != len(ordered_positions):
            return None, "correction-family-lineage-unresolved"
        keywords = {item.arg: item.value for item in call.keywords if item.arg is not None}
        if len(keywords) != len(call.keywords):
            return None, "correction-family-lineage-unresolved"
        keywords.pop(input_keyword, None)
        method = ""
        if api == "statsmodels.stats.multitest.multipletests":
            if set(keywords) - {"alpha", "method", "is_sorted", "returnsorted"}:
                return None, "correction-family-lineage-unresolved"
            method_node = keywords.get("method")
            method = "hs" if method_node is None else self.resolver.string(method_node) or ""
            if method not in _MT_MULTIPLETESTS_METHODS:
                return None, "unresolved-manual-correction-present"
            if any(
                not _mt_closed_literal(value, self.resolver)
                for key, value in keywords.items()
                if key != "method"
            ):
                return None, "correction-family-lineage-unresolved"
        elif api == "statsmodels.stats.multitest.fdrcorrection":
            if set(keywords) - {"alpha", "method", "is_sorted"}:
                return None, "correction-family-lineage-unresolved"
            method_node = keywords.get("method")
            method = "indep" if method_node is None else self.resolver.string(method_node) or ""
            if method not in {"indep", "negcorr"}:
                return None, "unresolved-manual-correction-present"
            if any(
                not _mt_closed_literal(value, self.resolver)
                for key, value in keywords.items()
                if key != "method"
            ):
                return None, "correction-family-lineage-unresolved"
        elif api == "scipy.stats.false_discovery_control":
            if set(keywords) - {"axis", "method"}:
                return None, "correction-family-lineage-unresolved"
            method_node = keywords.get("method")
            method = "bh" if method_node is None else self.resolver.string(method_node) or ""
            if method not in {"bh", "by"}:
                return None, "unresolved-manual-correction-present"
            axis = keywords.get("axis")
            if axis is not None and not _mt_literal_axis(axis):
                return None, "correction-family-lineage-unresolved"
        else:
            if keywords:
                return None, "correction-family-lineage-unresolved"
            method = "benjamini-hochberg"
        return _MtCorrection(call, str(api), positions, ordered_positions, method), None

    def _bind_correction_return(self, call: ast.Call, correction: _MtCorrection) -> None:
        for statement in self.scope:
            target: ast.expr | None = None
            if isinstance(statement, ast.Assign) and statement.value is call:
                target = statement.targets[0] if len(statement.targets) == 1 else None
            elif isinstance(statement, ast.AnnAssign) and statement.value is call:
                target = statement.target
            if isinstance(target, ast.Name):
                kind = (
                    "structured"
                    if correction.api
                    in {
                        "statsmodels.stats.multitest.multipletests",
                        "statsmodels.stats.multitest.fdrcorrection",
                    }
                    else "adjusted"
                )
                self.correction_return_names[target.id] = (correction, kind)
            elif isinstance(target, (ast.Tuple, ast.List)):
                expected_length = (
                    4
                    if correction.api == "statsmodels.stats.multitest.multipletests"
                    else 2
                    if correction.api == "statsmodels.stats.multitest.fdrcorrection"
                    else 0
                )
                if len(target.elts) != expected_length:
                    for item in target.elts:
                        if isinstance(item, ast.Name):
                            self.unsupported_correction_return_names.add(item.id)
                    continue
                for index, item in enumerate(target.elts):
                    if not isinstance(item, ast.Name):
                        continue
                    if correction.api in {
                        "statsmodels.stats.multitest.multipletests",
                        "statsmodels.stats.multitest.fdrcorrection",
                    } and index in {0, 1}:
                        self.correction_return_names[item.id] = (
                            correction,
                            "reject" if index == 0 else "adjusted",
                        )
                    else:
                        self.unsupported_correction_return_names.add(item.id)
        changed = True
        while changed:
            changed = False
            for statement in self.scope:
                if not (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    continue
                source_name: str | None = None
                if isinstance(statement.value, ast.Name):
                    source_name = statement.value.id
                elif (
                    isinstance(statement.value, ast.Call)
                    and self.resolver.qualified(statement.value.func) in {"list", "tuple"}
                    and len(statement.value.args) == 1
                    and not statement.value.keywords
                    and isinstance(statement.value.args[0], ast.Name)
                ):
                    source_name = statement.value.args[0].id
                if source_name not in self.correction_return_names:
                    continue
                source = self.correction_return_names[source_name]
                if self.correction_return_names.get(statement.targets[0].id) != source:
                    self.correction_return_names[statement.targets[0].id] = source
                    changed = True

    def _correction_returns_supported(self) -> bool:
        parent: dict[ast.AST, ast.AST] = {
            child: node
            for node in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(node)
        }
        for node in _walk_statements(self.scope):
            if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
                continue
            if node.id in self.unsupported_correction_return_names:
                return False
            bound = self.correction_return_names.get(node.id)
            if bound is None:
                continue
            _correction, kind = bound
            owner = parent.get(node)
            if kind == "structured":
                if not (
                    isinstance(owner, ast.Subscript)
                    and owner.value is node
                    and _mt_literal_member(owner.slice) == 0
                ):
                    return False
            elif not (
                isinstance(owner, ast.Subscript)
                and owner.value is node
                and isinstance(_mt_literal_member(owner.slice), int)
            ):
                if not (
                    (
                        isinstance(owner, ast.Call)
                        and self.resolver.qualified(owner.func) in {"list", "tuple"}
                        and len(owner.args) == 1
                        and owner.args[0] is node
                        and not owner.keywords
                    )
                    or (isinstance(owner, (ast.Assign, ast.AnnAssign)) and owner.value is node)
                    or (
                        isinstance(owner, ast.Call)
                        and self.resolver.qualified(owner.func) == "zip"
                        and not owner.keywords
                        and isinstance(parent.get(owner), (ast.For, ast.AsyncFor))
                        and cast(ast.For | ast.AsyncFor, parent[owner]).iter is owner
                    )
                ):
                    return False
        return True

    def _manual_corrections(
        self,
    ) -> tuple[tuple[_MtCorrection, ...], str | None]:
        result: list[_MtCorrection] = []
        for call in sorted(
            (node for node in _walk_statements(self.scope) if isinstance(node, ast.Call)),
            key=_position,
        ):
            api = self.resolver.qualified(call.func)
            if api not in {"min", "numpy.minimum"} or len(call.args) != 2 or call.keywords:
                continue
            product: ast.BinOp | None = None
            cap: ast.expr | None = None
            for candidate_product, candidate_cap in (
                (call.args[0], call.args[1]),
                (call.args[1], call.args[0]),
            ):
                if isinstance(candidate_product, ast.BinOp) and isinstance(
                    candidate_product.op, ast.Mult
                ):
                    product = candidate_product
                    cap = candidate_cap
                    break
            if product is None or not (
                _mt_exact_int(cap, self.resolver, 1)
                or (
                    isinstance(cap, ast.Constant)
                    and isinstance(cap.value, float)
                    and math.isfinite(cap.value)
                    and cap.value == 1.0
                )
            ):
                continue
            positions: frozenset[int] = frozenset()
            n_node: ast.expr | None = None
            for p_node, candidate_n in (
                (product.left, product.right),
                (product.right, product.left),
            ):
                origins = self._p_origins(p_node)
                if len(origins) == 1:
                    positions = origins
                    n_node = candidate_n
                    break
            if not positions or n_node is None:
                continue
            if not self._exact_family_size(n_node):
                return (), "unresolved-manual-correction-present"
            self.accepted_manual_calls.add(call)
            self.manual_multiplications.add(product)
            result.append(
                _MtCorrection(
                    call,
                    "manual.bonferroni",
                    positions,
                    tuple(positions),
                    "bonferroni",
                )
            )
        return tuple(result), None

    def _exact_family_size(self, node: ast.expr) -> bool:
        if _mt_exact_int(node, self.resolver, len(self.outcome_columns)):
            return True
        if isinstance(node, ast.Name) and (expression := self.assignments.get(node.id)) is not None:
            return self._exact_family_size(expression)
        if (
            isinstance(node, ast.Call)
            and self.resolver.qualified(node.func) == "len"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in self.contract_table_names
            and (table := self.resolver.table(node.args[0])) is not None
            and tuple(cast(str, row[0]) for row in table if row) == self.outcome_columns
        ):
            return True
        return bool(
            isinstance(node, ast.Call)
            and self.resolver.qualified(node.func) == "len"
            and len(node.args) == 1
            and not node.keywords
            and (
                self._p_sequence(node.args[0]) == tuple(range(len(self.outcome_columns)))
                or (
                    isinstance(node.args[0], ast.Name)
                    and self._closed_builder_positions(node.args[0].id)
                    == tuple(range(len(self.outcome_columns)))
                )
            )
        )

    def _closed_builder_positions(self, name: str) -> tuple[int, ...] | None:
        closure = {name}
        changed = True
        while changed:
            changed = False
            for statement in self.scope:
                if not (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and isinstance(statement.value, ast.Name)
                ):
                    continue
                left = statement.targets[0].id
                right = statement.value.id
                if left in closure or right in closure:
                    before = len(closure)
                    closure.update({left, right})
                    changed |= len(closure) != before
        initializers = [
            statement
            for statement in self.scope
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in closure
            and isinstance(statement.value, ast.List)
            and not statement.value.elts
        ]
        if len(initializers) != 1:
            return None
        positions: list[int] = []
        for statement in self.scope:
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Attribute)
                and statement.value.func.attr == "append"
                and isinstance(statement.value.func.value, ast.Name)
                and statement.value.func.value.id in closure
                and len(statement.value.args) == 1
                and not statement.value.keywords
            ):
                continue
            origins = self._p_origins(statement.value.args[0])
            if len(origins) != 1:
                return None
            positions.append(next(iter(origins)))
        return tuple(positions) if positions else None

    def _correction_terminal_census(self) -> str | None:
        accepted_spans = {
            _position(call)
            for call in (*self.accepted_correction_calls, *self.accepted_manual_calls)
        }
        for call in sorted(
            (node for node in _walk_statements(self.original_scope) if isinstance(node, ast.Call)),
            key=_position,
        ):
            terminal = _mt_callee_terminal(call.func)
            if terminal is None:
                continue
            folded = terminal.lower()
            matched = folded in _MT_CORRECTION_TERMINALS or folded.startswith("benjamini")
            if not matched:
                continue
            api = self.full_resolver.qualified(call.func)
            if api in _MT_CORRECTION_APIS and _position(call) in accepted_spans:
                continue
            return "unresolved-manual-correction-present"
        return None

    @staticmethod
    def _mt23_terminal_structure(node: ast.expr) -> str:
        markers = tuple(
            (
                _position(item),
                bool(getattr(item, "_sc_mt_presentation_helper", False)),
                bool(getattr(item, "_sc_mt_terminal_rendering", False)),
            )
            for item in ast.walk(node)
            if getattr(item, "_sc_mt_presentation_helper", False)
            or getattr(item, "_sc_mt_terminal_rendering", False)
        )
        return f"{ast.dump(node, include_attributes=False)}|{markers!r}"

    @staticmethod
    def _mt23_position_complete(node: ast.AST) -> bool:
        return all(
            getattr(node, field, None) is not None
            for field in ("lineno", "col_offset", "end_lineno", "end_col_offset")
        )

    def _mt23_percent_key(self, node: ast.AST) -> _Mt23TerminalKey | None:
        if not (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Mod)
            and _mt_v21_display_string(node.left)
            and len(origins := self._p_origins(node.right)) == 1
            and self._mt23_position_complete(node)
        ):
            return None
        return _Mt23TerminalKey(
            "literal_percent",
            _position(node),
            self._mt23_terminal_structure(node),
            next(iter(origins)),
        )

    def _mt23_ifexp_key(self, node: ast.AST) -> _Mt23TerminalKey | None:
        if not (
            isinstance(node, ast.IfExp)
            and getattr(node, "_sc_mt_terminal_rendering", False) is True
            and _mt_v21_display_string(node.body)
            and _mt_v21_display_string(node.orelse)
            and len(positions := self._decision_positions_in_expr(node.test, set(), 0)) == 1
            and self._mt23_position_complete(node)
        ):
            return None
        return _Mt23TerminalKey(
            "terminal_ifexp",
            _position(node),
            self._mt23_terminal_structure(node),
            next(iter(positions)),
        )

    def _mt23_terminal_occurrences(self) -> tuple[_Mt23TerminalOccurrence, ...]:
        """Capture ordered S_D6 descriptor occurrences without deduplication."""

        parents = {
            child: parent
            for parent in _walk_statements(self.terminal_origin_scope)
            for child in ast.iter_child_nodes(parent)
        }
        occurrences: list[_Mt23TerminalOccurrence] = []
        for node in _walk_statements(self.terminal_origin_scope):
            transport_key = self._mt23_percent_key(node)
            if transport_key is not None:
                if not self._mt23_structural_sink_candidate(transport_key):
                    continue
                decisions = [
                    item
                    for item in ast.walk(node)
                    if item is not node and self._mt23_ifexp_key(item) is not None
                ]
                if len(decisions) > 1:
                    continue
                decision = cast(ast.IfExp, decisions[0]) if decisions else None
                decision_key = self._mt23_ifexp_key(decision) if decision is not None else None
                if decision_key is not None and (
                    decision_key.family_position != transport_key.family_position
                ):
                    continue
                occurrences.append(
                    _Mt23TerminalOccurrence(
                        transport_key,
                        decision_key,
                        transport_key.family_position,
                        len(occurrences),
                        cast(ast.expr, node),
                        decision,
                    )
                )
                continue
            decision_key = self._mt23_ifexp_key(node)
            if decision_key is None:
                continue
            if (
                not self._mt23_structural_sink_candidate(decision_key)
                and self._mt23_assigned_sink_count(decision_key) < 2
            ):
                continue
            if any(
                self._mt23_percent_key(parent) is not None
                for parent in self._mt23_ancestors(node, parents)
            ):
                continue
            occurrences.append(
                _Mt23TerminalOccurrence(
                    decision_key,
                    decision_key,
                    decision_key.family_position,
                    len(occurrences),
                    cast(ast.IfExp, node),
                    cast(ast.IfExp, node),
                )
            )
        return tuple(occurrences)

    def _mt23_structural_sink_candidate(self, key: _Mt23TerminalKey) -> bool:
        """Limit closure origins to values actually cloned beneath a final sink payload."""

        for sink in self.sinks:
            if not sink.p_result_eligible:
                continue
            for payload in sink.payloads:
                for node in ast.walk(payload):
                    candidate = (
                        self._mt23_percent_key(node)
                        if key.production == "literal_percent"
                        else self._mt23_ifexp_key(node)
                    )
                    if (
                        candidate is not None
                        and candidate.production == key.production
                        and candidate.source_position == key.source_position
                        and candidate.structure == key.structure
                    ):
                        return True
        return False

    def _mt23_assigned_sink_count(self, key: _Mt23TerminalKey) -> int:
        """Count distinct emissions of one assigned terminal clone without accepting aliases."""

        parents = {
            child: parent
            for parent in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(parent)
        }
        names: set[str] = set()
        for node in _walk_statements(self.scope):
            candidate = self._mt23_ifexp_key(node)
            parent = parents.get(node)
            if (
                candidate == key
                and isinstance(parent, (ast.Assign, ast.AnnAssign))
                and parent.value is node
            ):
                targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
                if len(targets) == 1 and isinstance(targets[0], ast.Name):
                    names.add(targets[0].id)
        if len(names) != 1:
            return 0
        name = next(iter(names))
        return sum(
            any(
                isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == name
                for node in ast.walk(payload)
            )
            for sink in self.sinks
            if sink.p_result_eligible
            for payload in sink.payloads
        )

    @staticmethod
    def _mt23_ancestors(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> tuple[ast.AST, ...]:
        result: list[ast.AST] = []
        cursor = node
        while cursor in parents:
            cursor = parents[cursor]
            result.append(cursor)
        return tuple(result)

    def _mt23_build_terminal_closure(self) -> _Mt23TerminalClosure:
        occurrences = self._mt23_terminal_occurrences()
        if not occurrences:
            return _Mt23TerminalClosure((), ())
        matches: list[_Mt23TerminalMatch] = []
        claimed_transports: set[ast.expr] = set()
        claimed_decisions: set[ast.IfExp] = set()
        for occurrence in occurrences:
            candidates: list[tuple[ast.expr, ast.IfExp | None, _Sink]] = []
            for sink in self.sinks:
                if not sink.p_result_eligible:
                    continue
                for payload in sink.payloads:
                    for node in ast.walk(payload):
                        transport = cast(ast.expr, node)
                        if occurrence.transport_key.production == "literal_percent":
                            if self._mt23_percent_key(node) != occurrence.transport_key:
                                continue
                        elif self._mt23_ifexp_key(node) != occurrence.transport_key:
                            continue
                        decision: ast.IfExp | None = None
                        if occurrence.decision_key is not None:
                            decisions = [
                                cast(ast.IfExp, item)
                                for item in ast.walk(node)
                                if self._mt23_ifexp_key(item) == occurrence.decision_key
                            ]
                            if len(decisions) != 1:
                                continue
                            decision = decisions[0]
                        candidates.append((transport, decision, sink))
            unique = {
                (id(transport), id(decision) if decision is not None else 0, id(sink.call)): (
                    transport,
                    decision,
                    sink,
                )
                for transport, decision, sink in candidates
            }
            if len(unique) != 1:
                return _Mt23TerminalClosure(
                    occurrences, tuple(matches), "unresolved-pvalue-consumer"
                )
            transport, decision, sink = next(iter(unique.values()))
            if transport in claimed_transports or (
                decision is not None and decision in claimed_decisions
            ):
                return _Mt23TerminalClosure(
                    occurrences, tuple(matches), "unresolved-pvalue-consumer"
                )
            claimed_transports.add(transport)
            if decision is not None:
                claimed_decisions.add(decision)
            matches.append(_Mt23TerminalMatch(occurrence, transport, decision, sink))
        return _Mt23TerminalClosure(occurrences, tuple(matches))

    @staticmethod
    def _mt23_closure_signature(closure: _Mt23TerminalClosure) -> tuple[object, ...]:
        return (
            closure.failure,
            tuple(
                (
                    occurrence.transport_key,
                    occurrence.decision_key,
                    occurrence.family_position,
                    occurrence.ordinal,
                    id(occurrence.transport),
                    id(occurrence.decision),
                )
                for occurrence in closure.occurrences
            ),
            tuple(
                (
                    match.occurrence.ordinal,
                    id(match.transport),
                    id(match.decision),
                    id(match.sink.call),
                    tuple(id(payload) for payload in match.sink.payloads),
                )
                for match in closure.matches
            ),
        )

    def _mt23_transport_mapped(self, node: ast.expr) -> bool:
        return any(match.transport is node for match in self.terminal_closure.matches)

    def _mt23_decision_mapped(self, node: ast.IfExp) -> bool:
        return any(match.decision is node for match in self.terminal_closure.matches)

    def _off_grammar_transform_guard(self) -> str | None:
        sink_calls = {item.call for item in self.sinks}
        parents = {
            child: parent
            for parent in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(parent)
        }
        scalar_cast_present = False
        for node in sorted(
            (
                item
                for item in _walk_statements(self.scope)
                if isinstance(item, (ast.BinOp, ast.Call))
            ),
            key=_position,
        ):
            if not self._p_origins(node):
                continue
            if isinstance(node, ast.BinOp):
                if node in self.manual_multiplications:
                    continue
                if any(
                    any(node is descendant for descendant in ast.walk(argument))
                    for call in self.accepted_correction_calls
                    for argument in call.args
                ):
                    continue
                if self._presentation_concat(node):
                    continue
                if self._literal_percent_presentation(node):
                    continue
                return "unresolved-manual-correction-present"
            if node in self.family_calls:
                continue
            if (
                node in self.accepted_correction_calls
                or node in self.accepted_manual_calls
                or node in sink_calls
                or self._recognized_extremum(node)
                or self._presentation_join(node)
            ):
                continue
            if self._direct_scalar_cast_or_round(node):
                if self._hand_family_threshold_assignment_present():
                    return "unresolved-manual-correction-present"
                if self.resolver.qualified(node.func) == "round":
                    scalar_cast_present = True
                continue
            if (
                self.resolver.qualified(node.func) == "bool"
                and len(node.args) == 1
                and not node.keywords
                and isinstance(node.args[0], ast.Compare)
            ):
                continue
            if (
                self.resolver.qualified(node.func) == "int"
                and isinstance((owner := parents.get(node)), ast.Subscript)
                and owner.slice is node
                and self._r18_display_table(owner, parents)
            ):
                continue
            api = self.resolver.qualified(node.func)
            terminal = _mt_callee_terminal(node.func)
            if (
                api == "zip"
                and len(node.args) == 2
                and not node.keywords
                and self.resolver.sequence(node.args[0]) == self.outcome_columns
                and self._p_sequence(node.args[1]) is not None
            ):
                continue
            if api == "zip" and self._inside_presentation_join(node):
                continue
            if api in {"numpy.array", "numpy.asarray"} or terminal in {
                "append",
                "extend",
                "add",
                "format",
            }:
                continue
            return "unresolved-manual-correction-present"
        return "pvalue-scalar-cast-or-rounding-unsupported" if scalar_cast_present else None

    def _presentation_concat(self, node: ast.BinOp) -> bool:
        if not isinstance(node.op, ast.Add):
            return False

        def display_only(item: ast.expr) -> bool:
            if isinstance(item, (ast.JoinedStr, ast.Constant)):
                return not isinstance(item, ast.Constant) or isinstance(item.value, str)
            if isinstance(item, ast.BinOp) and isinstance(item.op, ast.Add):
                return display_only(item.left) and display_only(item.right)
            if isinstance(item, ast.IfExp):
                return display_only(item.body) and display_only(item.orelse)
            return False

        if not display_only(node):
            return False
        return any(
            any(node is descendant for descendant in ast.walk(payload))
            for sink in self.sinks
            if sink.p_result_eligible
            for payload in sink.payloads
        )

    def _literal_percent_presentation(self, node: ast.BinOp) -> bool:
        if not (
            isinstance(node.op, ast.Mod)
            and _mt_v21_display_string(node.left)
            and self._p_origins(node.right)
        ):
            return False
        if self._mt23_transport_mapped(node):
            return True
        combined = (*self.original_scope, *self.scope)
        parents = {
            child: parent
            for parent in _walk_statements(combined)
            for child in ast.iter_child_nodes(parent)
        }
        return self._mt_v2_rendering_load_reaches_sink(node, parents)

    def _presentation_join(self, node: ast.Call) -> bool:
        if not (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and _mt_v21_display_string(node.func.value)
            and len(node.args) == 1
            and not node.keywords
        ):
            return False

        def element(value: ast.expr) -> bool:
            if _mt_v21_display_string(value) or isinstance(value, ast.JoinedStr):
                return True
            if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mod):
                return _mt_v21_display_string(value.left)
            if isinstance(value, ast.Call):
                api = self.resolver.qualified(value.func)
                return bool(
                    (api == "str" and len(value.args) == 1 and not value.keywords)
                    or (
                        isinstance(value.func, ast.Attribute)
                        and value.func.attr == "format"
                        and _mt_v21_display_string(value.func.value)
                    )
                )
            return False

        iterable = node.args[0]
        if isinstance(iterable, (ast.List, ast.Tuple)):
            if not iterable.elts or not all(element(item) for item in iterable.elts):
                return False
        elif isinstance(iterable, (ast.ListComp, ast.GeneratorExp)):
            if not (
                len(iterable.generators) == 1
                and not iterable.generators[0].is_async
                and not iterable.generators[0].ifs
                and element(iterable.elt)
                and isinstance(iterable.generators[0].iter, ast.Call)
                and self.resolver.qualified(iterable.generators[0].iter.func) == "zip"
                and not iterable.generators[0].iter.keywords
                and len(iterable.generators[0].iter.args) >= 2
            ):
                return False
            sequences = [self._p_sequence(item) for item in iterable.generators[0].iter.args]
            known = [item for item in sequences if item is not None]
            if not known or any(item != known[0] for item in known[1:]):
                return False
        else:
            return False
        combined = (*self.original_scope, *self.scope)
        parents = {
            child: parent
            for parent in _walk_statements(combined)
            for child in ast.iter_child_nodes(parent)
        }
        return self._mt_v2_rendering_load_reaches_sink(node, parents)

    def _inside_presentation_join(self, node: ast.Call) -> bool:
        parents = {
            child: parent
            for parent in _walk_statements((*self.original_scope, *self.scope))
            for child in ast.iter_child_nodes(parent)
        }
        cursor: ast.AST = node
        while (parent := parents.get(cursor)) is not None and not isinstance(parent, ast.stmt):
            if isinstance(parent, ast.Call) and self._presentation_join(parent):
                return True
            cursor = parent
        for candidate in _walk_statements(self.scope):
            if (
                isinstance(candidate, ast.Call)
                and candidate is not node
                and _position(candidate) == _position(node)
            ):
                cursor = candidate
                while (parent := parents.get(cursor)) is not None and not isinstance(
                    parent, ast.stmt
                ):
                    if isinstance(parent, ast.Call) and self._presentation_join(parent):
                        return True
                    cursor = parent
        return False

    def _hand_family_threshold_assignment_present(self) -> bool:
        for expression in self.assignments.values():
            if not isinstance(expression, ast.BinOp) or not isinstance(expression.op, ast.Div):
                continue
            alpha = _mt_decimal_literal(expression.left, self.source)
            if alpha not in _MT_DECISION_LITERALS:
                continue
            if _mt_exact_int(expression.right, self.resolver, len(self.outcome_columns)):
                return True
        return False

    def _direct_scalar_cast_or_round(self, call: ast.Call) -> bool:
        api = self.resolver.qualified(call.func)
        if api not in {"float", "round"} or call.keywords:
            return False
        if api == "float" and len(call.args) != 1:
            return False
        if api == "round" and len(call.args) not in {1, 2}:
            return False
        if any(isinstance(item, ast.Starred) for item in call.args):
            return False
        if not self._is_direct_p(call.args[0], set(), 0):
            return False
        return bool(
            len(call.args) == 1
            or (
                isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, int)
                and not isinstance(call.args[1].value, bool)
            )
        )

    def _decision_threshold_guard(self, *, recognized_correction_present: bool) -> str | None:
        parents = {
            child: parent
            for parent in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(parent)
        }
        for comparison in sorted(
            (
                node
                for node in _walk_statements(self.scope)
                if isinstance(node, ast.Compare) and self._p_origins(node)
            ),
            key=_position,
        ):
            parent = parents.get(comparison)
            if isinstance(parent, ast.IfExp) and self._presentation_optional_value_ifexp(parent):
                continue
            if len(comparison.ops) != 1 or len(comparison.comparators) != 1:
                return "unresolved-decision-threshold"
            if not isinstance(comparison.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                return "unresolved-decision-threshold"
            left = comparison.left
            right = comparison.comparators[0]
            left_decision = self._decision_origins(left)
            right_decision = self._decision_origins(right)
            if (
                not left_decision
                and not right_decision
                and self._comparison_in_filtered_membership(comparison, parents)
            ):
                left_decision = self._p_origins(left)
                right_decision = self._p_origins(right)
            if bool(left_decision) == bool(right_decision):
                return "unresolved-decision-threshold"
            threshold = right if left_decision else left
            literal = _mt_decimal_literal(threshold, self.source)
            if literal is None and isinstance(threshold, ast.Name):
                literal = self._single_bound_decision_literal(threshold.id)
            permitted = (
                _MT_DECISION_LITERALS
                if recognized_correction_present
                else _MT_V2_RAW_DECISION_LITERALS
            )
            if literal is None or literal not in permitted:
                return "unresolved-decision-threshold"
            if literal * Decimal(len(self.outcome_columns)) in _MT_DECISION_LITERALS:
                return "unresolved-decision-threshold"
        return None

    def _comparison_in_filtered_membership(
        self, node: ast.Compare, parents: Mapping[ast.AST, ast.AST]
    ) -> bool:
        cursor: ast.AST = node
        while (parent := parents.get(cursor)) is not None:
            if isinstance(parent, (ast.ListComp, ast.SetComp)):
                return bool(
                    len(parent.generators) == 1
                    and node in parent.generators[0].ifs
                    and self._recognized_filtered_family_membership(node.left, parents)
                    if isinstance(node.left, ast.Subscript)
                    else False
                )
            if isinstance(parent, ast.stmt):
                return False
            cursor = parent
        return False

    def _single_bound_decision_literal(self, name: str) -> Decimal | None:
        generated = self.assignments.get(name)
        if name.startswith("__sc_inline_") and isinstance(generated, ast.Name):
            return self._single_bound_decision_literal(generated.id)
        if (
            name.startswith("__sc_inline_")
            and generated is not None
            and _finite_numeric_constant(generated)
        ):
            local_names = [
                target.id
                for statement in _walk_statements(self.original_scope)
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                and (value := statement.value) is not None
                and _position(value) == _position(generated)
                for target in (
                    statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                )
                if isinstance(target, ast.Name)
            ]
            if (
                len(local_names) == 1
                and _mt_binding_count(self.original_scope, local_names[0]) == 1
            ):
                return _mt_decimal_literal(generated, self.source)
        if _mt_binding_count(self.original_scope, name) != 1:
            return None
        matches: list[ast.expr] = []
        for statement in self.original_scope:
            for node in ast.walk(statement):
                if not isinstance(node, ast.stmt):
                    continue
                target, value = _mt_setup_target_value(node)
                if target is not None and target.id == name and value is not None:
                    matches.append(value)
        if len(matches) != 1 or not _finite_numeric_constant(matches[0]):
            return None
        return _mt_decimal_literal(matches[0], self.source)

    def _decision_origins(self, node: ast.expr) -> frozenset[int]:
        if self._is_direct_p(node, set(), 0):
            return self._p_origins(node)
        manual = self._manual_call_for_expr(node, set(), 0)
        if manual is not None:
            return manual.positions
        vector = self._correction_vector_member(node, set(), 0)
        if vector is not None:
            correction, index = vector
            if 0 <= index < len(correction.ordered_positions):
                return frozenset({correction.ordered_positions[index]})
        return frozenset()

    def _is_direct_p(self, node: ast.expr, active: set[str], depth: int) -> bool:
        if depth > _DEFINITION_NODE_MAX:
            return False
        if isinstance(node, ast.Name):
            if node.id in self.direct_p_names:
                return True
            if node.id in active:
                return False
            expression = self.assignments.get(node.id)
            return bool(
                expression is not None
                and self._is_direct_p(expression, {*active, node.id}, depth + 1)
            )
        if isinstance(node, ast.Attribute) and node.attr == "pvalue":
            return self._result_call(node.value, active, depth + 1) in self.call_position
        if (
            isinstance(node, ast.Call)
            and self.resolver.qualified(node.func) == "float"
            and len(node.args) == 1
            and not node.keywords
        ):
            return self._is_direct_p(node.args[0], active, depth + 1)
        if isinstance(node, ast.Subscript) and _mt_literal_member(node.slice) == 1:
            return self._result_call(node, active, depth + 1) in self.call_position
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            member = _mt_literal_member(node.slice)
            stored = self.record_stores.get((node.value.id, member)) if member is not None else None
            if stored is not None:
                return self._is_direct_p(stored, active, depth + 1)
        if isinstance(node, ast.Subscript) and len(self._p_origins(node)) == 1:
            return True
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            expression = self.assignments.get(node.value.id)
            member = _mt_literal_member(node.slice)
            if isinstance(expression, (ast.List, ast.Tuple)) and isinstance(member, int):
                index = member if member >= 0 else len(expression.elts) + member
                return bool(
                    0 <= index < len(expression.elts)
                    and self._is_direct_p(expression.elts[index], active, depth + 1)
                )
            if isinstance(expression, ast.Dict) and member is not None:
                for key, value in zip(expression.keys, expression.values, strict=True):
                    if key is not None and _mt_literal_member(key) == member:
                        return self._is_direct_p(value, active, depth + 1)
        return False

    def _manual_call_for_expr(
        self, node: ast.expr, active: set[str], depth: int
    ) -> _MtCorrection | None:
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            return (
                self._manual_call_for_expr(expression, {*active, node.id}, depth + 1)
                if expression is not None
                else None
            )
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            member = _mt_literal_member(node.slice)
            stored = self.record_stores.get((node.value.id, member)) if member is not None else None
            if stored is not None:
                return self._manual_call_for_expr(stored, active, depth + 1)
        if isinstance(node, ast.Call) and node in self.accepted_manual_calls:
            origins = self._p_origins(node)
            return _MtCorrection(
                node,
                "manual.bonferroni",
                origins,
                tuple(origins),
                "bonferroni",
            )
        return None

    def _correction_vector_member(
        self, node: ast.expr, active: set[str], depth: int
    ) -> tuple[_MtCorrection, int] | None:
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            return (
                self._correction_vector_member(expression, {*active, node.id}, depth + 1)
                if expression is not None
                else None
            )
        if not isinstance(node, ast.Subscript):
            return None
        member = _mt_literal_member(node.slice)
        if not isinstance(member, int):
            return None
        vector: ast.expr = node.value
        if isinstance(vector, ast.Name):
            bound = self.correction_return_names.get(vector.id)
            if bound is not None:
                correction, kind = bound
                if kind in {"adjusted", "reject"}:
                    return correction, member
                if kind == "structured" and member == 0:
                    return None
        if isinstance(vector, ast.Subscript) and _mt_literal_member(vector.slice) == 0:
            if isinstance(vector.value, ast.Name):
                bound = self.correction_return_names.get(vector.value.id)
                if bound is not None and bound[1] == "structured":
                    return bound[0], member
        return None

    def _order_16_guard(self, corrections: Sequence[_MtCorrection]) -> str | None:
        hierarchy = self._hierarchy_guard()
        if hierarchy is not None:
            return hierarchy
        if self._partition_guard(corrections):
            return "multiple-family-partition-present"
        resampling = self._resampling_guard()
        if resampling is not None:
            return resampling
        if self._statistics_prefix_guard():
            return "unresolved-inference-sibling-present"
        return None

    def _mt_v21_terminal_rendering_if(self, node: ast.If) -> tuple[int, frozenset[str]] | None:
        """Classify the exact mirrored R2/R3b hierarchy/conclusion form."""

        if len(node.body) != 1 or len(node.orelse) != 1 or isinstance(node.orelse[0], ast.If):
            return None
        positions = self._decision_positions_in_expr(node.test, set(), 0)
        if len(positions) != 1:
            return None
        root = self.scope
        resolver = self.resolver
        if not any(node is item for statement in self.scope for item in ast.walk(statement)):
            root = self.original_scope
            resolver = self.full_resolver
        sinks = tuple(sink for sink in _registered_sinks(root, resolver) if sink.p_result_eligible)

        body = node.body[0]
        orelse = node.orelse[0]
        if isinstance(body, ast.Assign) and isinstance(orelse, ast.Assign):
            if not (
                len(body.targets) == 1
                and len(orelse.targets) == 1
                and isinstance(body.targets[0], ast.Name)
                and isinstance(orelse.targets[0], ast.Name)
                and body.targets[0].id == orelse.targets[0].id
                and _mt_v21_display_string(body.value)
                and _mt_v21_display_string(orelse.value)
            ):
                return None
            selected = body.targets[0].id
            store_nodes = {
                item
                for statement in (body, orelse)
                for item in ast.walk(statement)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Store)
                and item.id == selected
            }
            all_stores = {
                item
                for statement in root
                for item in ast.walk(statement)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, (ast.Store, ast.Del))
                and item.id == selected
            }
            if all_stores != store_nodes:
                return None
            parents = {
                child: parent
                for parent in _walk_statements(root)
                for child in ast.iter_child_nodes(parent)
            }
            aliases = {selected}
            changed = True
            while changed:
                changed = False
                for statement in _walk_statements(root):
                    if not (
                        isinstance(statement, ast.Assign)
                        and len(statement.targets) == 1
                        and isinstance(statement.targets[0], ast.Name)
                        and isinstance(statement.value, ast.Name)
                        and statement.value.id in aliases
                    ):
                        continue
                    alias = statement.targets[0].id
                    if alias not in aliases:
                        aliases.add(alias)
                        changed = True
            loads = [
                item
                for statement in root
                for item in ast.walk(statement)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id in aliases
            ]
            if not loads:
                return None
            kinds: set[str] = set()
            for load in loads:
                parent = parents.get(load)
                if (
                    isinstance(parent, ast.Assign)
                    and len(parent.targets) == 1
                    and isinstance(parent.targets[0], ast.Name)
                    and parent.targets[0].id in aliases
                    and parent.value is load
                ):
                    continue
                if not self._mt_v2_rendering_load_reaches_sink(load, parents):
                    return None
                kinds.update(
                    sink.kind
                    for sink in sinks
                    if any(
                        load is descendant
                        for payload in sink.payloads
                        for descendant in ast.walk(payload)
                    )
                )
            if not kinds:
                return None
            return next(iter(positions)), frozenset(kinds)

        if not (
            isinstance(body, ast.Expr)
            and isinstance(body.value, ast.Call)
            and isinstance(orelse, ast.Expr)
            and isinstance(orelse.value, ast.Call)
        ):
            return None
        by_position = {_position(sink.call): sink for sink in sinks}
        left = by_position.get(_position(body.value))
        right = by_position.get(_position(orelse.value))
        if left is None or right is None or left.kind != right.kind:
            return None
        if not all(_mt_v21_display_string(item) for item in (*left.payloads, *right.payloads)):
            return None

        def static_target(call: ast.Call, kind: str) -> str | None:
            if kind == "builtin_print":
                files = [item.value for item in call.keywords if item.arg == "file"]
                if not files:
                    return "stdout"
                if len(files) != 1:
                    return None
                return ast.dump(files[0], include_attributes=False)
            if isinstance(call.func, ast.Attribute):
                return ast.dump(call.func.value, include_attributes=False)
            return kind

        left_target = static_target(body.value, left.kind)
        right_target = static_target(orelse.value, right.kind)
        if left_target is None or left_target != right_target:
            return None
        return next(iter(positions)), frozenset({left.kind})

    def _hierarchy_guard(self) -> str | None:
        controls: list[tuple[ast.AST, ast.expr]] = []
        combined = (*self.original_scope, *self.scope)
        for node in _walk_statements(combined):
            if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
                controls.append((node, node.test))
            elif isinstance(node, ast.Match):
                controls.append((node, node.subject))
                controls.extend((case, case.guard) for case in node.cases if case.guard is not None)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                controls.append((node, node.iter))
            elif isinstance(node, ast.comprehension):
                controls.append((node, node.iter))
                controls.extend((node, item) for item in node.ifs)
        for owner, expression in controls:
            if isinstance(owner, ast.If) and self._mt_v21_terminal_rendering_if(owner) is not None:
                continue
            if isinstance(owner, ast.IfExp) and self._terminal_rendering_ifexp(owner):
                continue
            if isinstance(owner, ast.IfExp) and self._presentation_optional_value_ifexp(owner):
                continue
            if isinstance(owner, (ast.For, ast.AsyncFor)) and self._terminal_family_transport_loop(
                owner
            ):
                continue
            if isinstance(owner, ast.comprehension) and self._terminal_family_membership_control(
                owner, expression
            ):
                continue
            if (
                isinstance(owner, ast.comprehension)
                and isinstance(expression, ast.Call)
                and self._inside_presentation_join(expression)
            ):
                continue
            tracked = self._control_tracked(expression)
            if tracked:
                return "hierarchical-gatekeeping-present"
        for node in _walk_statements(combined):
            if not isinstance(node, ast.BoolOp):
                continue
            if any(self._control_tracked(item) for item in node.values):
                return "hierarchical-gatekeeping-present"
        parents = {
            child: parent
            for parent in _walk_statements(self.original_scope)
            for child in ast.iter_child_nodes(parent)
        }

        def function_owner(node: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
            cursor = node
            while cursor in parents:
                cursor = parents[cursor]
                if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return cursor
            return None

        def can_prevent_slice(node: ast.AST) -> bool:
            owner = function_owner(node)
            if owner is not None and owner.name != "main":
                return False
            for candidate in _walk_statements(self.original_scope):
                if function_owner(candidate) is not owner or _position(candidate) <= _position(
                    node
                ):
                    continue
                if isinstance(candidate, ast.Call) and (
                    self.full_resolver.qualified(candidate.func) in _MT_TEST_APIS
                    or candidate in {sink.call for sink in self.sinks}
                ):
                    return True
                if isinstance(candidate, ast.Attribute) and candidate.attr == "pvalue":
                    return True
            return False

        for node in _walk_statements(self.original_scope):
            if not (
                isinstance(node, (ast.Return, ast.Raise))
                or (
                    isinstance(node, ast.Call)
                    and self.full_resolver.qualified(node.func) == "sys.exit"
                )
            ):
                continue
            if not can_prevent_slice(node):
                continue
            exit_expression: ast.expr | None = None
            if isinstance(node, ast.Return):
                exit_expression = node.value
            elif isinstance(node, ast.Raise):
                values = tuple(item for item in (node.exc, node.cause) if item is not None)
                if any(self._control_tracked(item) for item in values):
                    return "hierarchical-gatekeeping-present"
                continue
            elif (
                isinstance(node, ast.Call) and self.full_resolver.qualified(node.func) == "sys.exit"
            ):
                if any(self._control_tracked(item) for item in node.args):
                    return "hierarchical-gatekeeping-present"
                continue
            if exit_expression is not None and self._control_tracked(exit_expression):
                return "hierarchical-gatekeeping-present"
        if self._unresolved_execution_prevention_edge():
            return "pvalue-control-dependence-unresolved"
        return None

    def _terminal_family_transport_loop(self, node: ast.For | ast.AsyncFor) -> bool:
        """Exclude only exact, unconditional traversal of a reconstructed p sequence."""

        if isinstance(node, ast.AsyncFor) or node.orelse:
            return False
        if isinstance(node.iter, ast.Call):
            if not (
                self.resolver.qualified(node.iter.func) == "zip"
                and not node.iter.keywords
                and len(node.iter.args) >= 2
                and isinstance(node.target, (ast.Tuple, ast.List))
                and len(node.target.elts) == len(node.iter.args)
                and _mt_v21_destructured_names(node.target) is not None
                and not any(
                    isinstance(item, (ast.Break, ast.Continue, ast.Return, ast.Raise))
                    for statement in node.body
                    for item in ast.walk(statement)
                )
            ):
                return False
            expected = tuple(range(len(self.outcome_columns)))
            sequences: list[tuple[int, ...] | None] = []
            for item in node.iter.args:
                sequence: tuple[int, ...] | None = None
                if isinstance(item, ast.Name) and item.id in self.correction_return_names:
                    sequence = self.correction_return_names[item.id][0].ordered_positions
                else:
                    raw = self.resolver.sequence(item) or self.full_resolver.sequence(item)
                    table = self.resolver.table(item) or self.full_resolver.table(item)
                    if raw is not None and tuple(raw) == self.outcome_columns:
                        sequence = expected
                    elif (
                        table is not None
                        and tuple(row[0] for row in table if row) == self.outcome_columns
                    ):
                        sequence = expected
                    else:
                        sequence = self._p_sequence(item) or self._decision_sequence(item)
                sequences.append(sequence)
            known = [item for item in sequences if item is not None]
            if (
                len(known) >= 2
                and all(item == known[0] for item in known[1:])
                and len(known[0]) == len(set(known[0]))
                and any(
                    isinstance(item, ast.Name) and item.id in self.correction_return_names
                    for item in node.iter.args
                )
            ):
                return True
            if sequences and all(item == expected for item in sequences):
                return True
            return self._mt_v21_complete_partitioned_zip(node)
        sequence = self._p_sequence(node.iter)
        return bool(
            sequence is not None
            and sequence
            and len(sequence) == len(set(sequence))
            and isinstance(node.target, ast.Name)
        )

    def _mt_v21_zip_positions(self, node: ast.For | ast.AsyncFor) -> tuple[int, ...] | None:
        if not (
            isinstance(node, ast.For)
            and not node.orelse
            and isinstance(node.iter, ast.Call)
            and self.resolver.qualified(node.iter.func) == "zip"
            and len(node.iter.args) >= 2
            and not node.iter.keywords
            and isinstance(node.target, (ast.Tuple, ast.List))
            and len(node.target.elts) == len(node.iter.args)
            and _mt_v21_destructured_names(node.target) is not None
        ):
            return None
        sequences: list[tuple[int, ...]] = []
        for argument in node.iter.args:
            sequence: tuple[int, ...] | None = None
            if isinstance(argument, ast.Name) and argument.id in self.correction_return_names:
                sequence = self.correction_return_names[argument.id][0].ordered_positions
            else:
                raw = self.resolver.sequence(argument) or self.full_resolver.sequence(argument)
                table = self.resolver.table(argument) or self.full_resolver.table(argument)
                labels: tuple[object, ...] | None = raw
                if table is not None:
                    labels = tuple(row[0] for row in table if row)
                if (
                    labels is not None
                    and labels
                    and all(
                        isinstance(item, str) and item in self.outcome_columns for item in labels
                    )
                ):
                    sequence = tuple(self.outcome_columns.index(cast(str, item)) for item in labels)
                else:
                    sequence = self._p_sequence(argument) or self._decision_sequence(argument)
            if sequence is None or not sequence or len(sequence) != len(set(sequence)):
                return None
            sequences.append(sequence)
        return sequences[0] if all(item == sequences[0] for item in sequences[1:]) else None

    def _mt_v21_complete_partitioned_zip(self, node: ast.For) -> bool:
        target = self._mt_v21_zip_positions(node)
        if target is None:
            return False
        loops = [
            item
            for item in _walk_statements((*self.original_scope, *self.scope))
            if isinstance(item, ast.For) and self._mt_v21_zip_positions(item) is not None
        ]
        mappings = [cast(tuple[int, ...], self._mt_v21_zip_positions(item)) for item in loops]
        flattened = [position for mapping in mappings for position in mapping]
        return bool(
            target in mappings
            and len(flattened) == len(set(flattened))
            and set(flattened) == set(range(len(self.outcome_columns)))
        )

    def _decision_sequence(
        self, node: ast.expr, active: set[str] | None = None, depth: int = 0
    ) -> tuple[int, ...] | None:
        active = set() if active is None else active
        if depth > _DEFINITION_NODE_MAX:
            return None
        if isinstance(node, ast.Name):
            if node.id in active:
                return None
            expression = self.assignments.get(node.id)
            if expression is None:
                return None
            return self._decision_sequence(expression, {*active, node.id}, depth + 1)
        if isinstance(node, ast.ListComp) and len(node.generators) == 1:
            generator = node.generators[0]
            if not (
                not generator.is_async
                and not generator.ifs
                and isinstance(generator.target, ast.Name)
                and isinstance(node.elt, ast.IfExp)
                and isinstance(node.elt.test, ast.Compare)
                and len(node.elt.test.ops) == 1
                and isinstance(node.elt.test.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
                and len(node.elt.test.comparators) == 1
                and _mt_v21_display_string(node.elt.body)
                and _mt_v21_display_string(node.elt.orelse)
            ):
                return None
            pairs = (
                (node.elt.test.left, node.elt.test.comparators[0]),
                (node.elt.test.comparators[0], node.elt.test.left),
            )
            if not any(
                isinstance(value, ast.Name)
                and value.id == generator.target.id
                and _mt_decimal_literal(threshold, self.source) == Decimal("0.05")
                for value, threshold in pairs
            ):
                return None
            return self._p_sequence(generator.iter)
        if not isinstance(node, (ast.List, ast.Tuple)):
            return None
        result: list[int] = []
        for item in node.elts:
            positions = self._decision_positions_in_expr(item, set(), 0)
            if len(positions) != 1:
                return None
            result.append(next(iter(positions)))
        return tuple(result)

    def _control_tracked(self, node: ast.expr) -> bool:
        if self._p_origins(node):
            return True
        if self._correction_control_present(node):
            return True
        return len(self._outcome_headers(node, set(), 0)) >= 2

    def _terminal_family_membership_control(
        self, node: ast.comprehension, expression: ast.expr
    ) -> bool:
        if (
            expression is node.iter
            and not node.is_async
            and not node.ifs
            and isinstance(node.target, (ast.Tuple, ast.List))
            and len(node.target.elts) == 2
            and all(isinstance(item, ast.Name) for item in node.target.elts)
            and isinstance(node.iter, ast.Call)
            and self.resolver.qualified(node.iter.func) == "zip"
            and len(node.iter.args) == 2
            and not node.iter.keywords
            and self.resolver.sequence(node.iter.args[0]) == self.outcome_columns
            and self._p_sequence(node.iter.args[1]) is not None
        ):
            return True
        if (
            expression is node.iter
            and not node.is_async
            and not node.ifs
            and isinstance(node.target, ast.Name)
        ):
            sequence = self._p_sequence(node.iter)
            return bool(sequence is not None and sequence and len(sequence) == len(set(sequence)))
        return bool(
            expression in node.ifs
            and len(node.ifs) == 1
            and self._p_origins(expression)
            and _mt_outcome_iteration_bindings(
                node.iter, node.target, self.resolver, self.outcome_columns
            )
            is not None
        )

    def _terminal_rendering_ifexp(self, node: ast.IfExp) -> bool:
        if not (
            isinstance(node.body, ast.Constant)
            and isinstance(node.body.value, str)
            and isinstance(node.orelse, ast.Constant)
            and isinstance(node.orelse.value, str)
            and node.body.value
            and node.orelse.value
            and "\x00" not in node.body.value
            and "\x00" not in node.orelse.value
            and len(node.body.value.encode("utf-8")) <= 256
            and len(node.orelse.value.encode("utf-8")) <= 256
            and (
                self._decision_positions_in_expr(node.test, set(), 0)
                or len(self._p_origins(node.test)) == 1
            )
        ):
            return False
        if self._mt23_decision_mapped(node):
            return True
        combined = (*self.original_scope, *self.scope)
        parents = {
            child: parent
            for parent in _walk_statements(combined)
            for child in ast.iter_child_nodes(parent)
        }
        cursor: ast.AST = node
        if isinstance((parent := parents.get(cursor)), (ast.Assign, ast.AnnAssign)):
            target = parent.targets[0] if isinstance(parent, ast.Assign) else parent.target
            if isinstance(target, ast.Name):
                loads: list[ast.AST] = [
                    item
                    for item in _walk_statements(combined)
                    if isinstance(item, ast.Name)
                    and isinstance(item.ctx, ast.Load)
                    and item.id == target.id
                ]
            elif (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and (member := _mt_literal_member(target.slice)) is not None
            ):
                loads = [
                    item
                    for item in _walk_statements(combined)
                    if isinstance(item, ast.Subscript)
                    and isinstance(item.ctx, ast.Load)
                    and isinstance(item.value, ast.Name)
                    and item.value.id == target.value.id
                    and _mt_literal_member(item.slice) == member
                ]
            else:
                return False
            return bool(
                loads
                and all(self._mt_v2_rendering_load_reaches_sink(item, parents) for item in loads)
            )
        return self._mt_v2_rendering_load_reaches_sink(cursor, parents)

    def _presentation_optional_value_ifexp(self, node: ast.IfExp) -> bool:
        if not (
            isinstance(node.test, ast.Compare)
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], (ast.Is, ast.IsNot))
            and len(node.test.comparators) == 1
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value is None
            and len(self._p_origins(node.test.left)) == 1
        ):
            return False

        def display_arm(item: ast.expr) -> bool:
            return bool(
                isinstance(item, ast.JoinedStr)
                or (
                    isinstance(item, ast.Constant)
                    and isinstance(item.value, str)
                    and "\x00" not in item.value
                    and len(item.value.encode("utf-8")) <= 256
                )
            )

        if not (display_arm(node.body) and display_arm(node.orelse)):
            return False
        if any(
            any(node is descendant for descendant in ast.walk(payload))
            for sink in self.sinks
            if sink.p_result_eligible
            for payload in sink.payloads
        ):
            return True
        parents = {
            child: parent
            for parent in _walk_statements(self.scope)
            for child in ast.iter_child_nodes(parent)
        }
        parent = parents.get(node)
        if not (
            isinstance(parent, ast.Assign)
            and len(parent.targets) == 1
            and isinstance(parent.targets[0], ast.Name)
        ):
            return False
        loads = [
            item
            for item in _walk_statements(self.scope)
            if isinstance(item, ast.Name)
            and isinstance(item.ctx, ast.Load)
            and item.id == parent.targets[0].id
        ]
        return bool(
            loads and all(self._mt_v2_rendering_load_reaches_sink(item, parents) for item in loads)
        )

    def _mt_v2_rendering_load_reaches_sink(
        self, node: ast.AST, parents: Mapping[ast.AST, ast.AST]
    ) -> bool:
        sinks = (
            *self.sinks,
            *_registered_sinks(self.original_scope, self.full_resolver),
        )
        payload_sinks = {
            payload: sink for sink in sinks if sink.p_result_eligible for payload in sink.payloads
        }
        cursor = node
        while cursor not in payload_sinks:
            parent = parents.get(cursor)
            if parent is None:
                return False
            if isinstance(parent, (ast.Assign, ast.AnnAssign)) and parent.value is cursor:
                targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
                if len(targets) != 1 or not isinstance(targets[0], ast.Name):
                    return False
                aliases = [
                    item
                    for statement in (*self.original_scope, *self.scope)
                    for item in ast.walk(statement)
                    if isinstance(item, ast.Name)
                    and isinstance(item.ctx, ast.Load)
                    and item.id == targets[0].id
                    and (item in parents or item in payload_sinks)
                ]
                return bool(
                    aliases
                    and all(
                        self._mt_v2_rendering_load_reaches_sink(item, parents) for item in aliases
                    )
                )
            if isinstance(parent, ast.Dict) and cursor in parent.values:
                index = parent.values.index(cursor)
                key = parent.keys[index]
                member = _mt_literal_member(key) if key is not None else None
                owner = parents.get(parent)
                if not (
                    member is not None
                    and isinstance(owner, (ast.Assign, ast.AnnAssign))
                    and owner.value is parent
                ):
                    return False
                targets = owner.targets if isinstance(owner, ast.Assign) else [owner.target]
                if len(targets) != 1 or not isinstance(targets[0], ast.Name):
                    return False
                loads = [
                    item
                    for statement in (*self.original_scope, *self.scope)
                    for item in ast.walk(statement)
                    if isinstance(item, ast.Subscript)
                    and isinstance(item.ctx, ast.Load)
                    and isinstance(item.value, ast.Name)
                    and item.value.id == targets[0].id
                    and _mt_literal_member(item.slice) == member
                    and (item in parents or item in payload_sinks)
                ]
                return bool(
                    loads
                    and all(
                        self._mt_v2_rendering_load_reaches_sink(item, parents) for item in loads
                    )
                )
            if isinstance(parent, (ast.FormattedValue, ast.JoinedStr)):
                cursor = parent
                continue
            if isinstance(parent, (ast.List, ast.Tuple)) and _mt_v21_percent_payload(
                parent, parents
            ):
                cursor = parent
                continue
            if (
                isinstance(parent, ast.BinOp)
                and isinstance(parent.op, ast.Mod)
                and parent.right is cursor
                and _mt_v21_display_string(parent.left)
            ):
                cursor = parent
                continue
            if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Add):
                other = (
                    parent.right
                    if parent.left is cursor
                    else parent.left
                    if parent.right is cursor
                    else None
                )
                if other is not None and (
                    _mt_v21_display_string(other)
                    or (isinstance(other, ast.JoinedStr) and not self._p_origins(other))
                ):
                    cursor = parent
                    continue
            if isinstance(parent, ast.BinOp) and self._presentation_concat(parent):
                cursor = parent
                continue
            if isinstance(parent, ast.Call):
                api = self.resolver.qualified(parent.func)
                terminal = _mt_callee_terminal(parent.func)
                if api == "str" or terminal == "format":
                    cursor = parent
                    continue
            return False
        sink = payload_sinks[cursor]
        cursor = sink.call
        while (parent := parents.get(cursor)) is not None:
            if isinstance(parent, ast.For):
                if (
                    parent.orelse
                    or any(isinstance(item, (ast.Break, ast.Continue)) for item in ast.walk(parent))
                    or _mt_outcome_iteration_bindings(
                        parent.iter,
                        parent.target,
                        self.full_resolver,
                        self.outcome_columns,
                    )
                    is None
                ):
                    return False
            elif isinstance(
                parent,
                (
                    ast.If,
                    ast.IfExp,
                    ast.While,
                    ast.AsyncFor,
                    ast.Try,
                    ast.Match,
                    ast.BoolOp,
                    ast.comprehension,
                ),
            ):
                return False
            cursor = parent
        return True

    def _correction_control_present(self, node: ast.expr) -> bool:
        for item in ast.walk(node):
            if isinstance(item, ast.Subscript) and self._correction_vector_member(item, set(), 0):
                return True
        return False

    def _outcome_headers(self, node: ast.expr, active: set[str], depth: int) -> frozenset[str]:
        if depth > _DEFINITION_NODE_MAX:
            return frozenset()
        if isinstance(node, ast.Name):
            if node.id in active:
                return frozenset()
            expression = self.assignments.get(node.id) or self.original_assignments.get(node.id)
            if expression is None:
                return frozenset()
            return self._outcome_headers(expression, {*active, node.id}, depth + 1)
        result: set[str] = set()
        if isinstance(node, ast.Subscript):
            slice_node: ast.expr = node.slice
            base_node: ast.expr = node.value
            if (
                isinstance(node.value, ast.Attribute)
                and node.value.attr == "loc"
                and isinstance(node.slice, ast.Tuple)
                and len(node.slice.elts) == 2
            ):
                slice_node = node.slice.elts[1]
                base_node = node.value.value
            sequence = self.resolver.sequence(slice_node) or self.full_resolver.sequence(slice_node)
            literal = self.resolver.string(slice_node) or self.full_resolver.string(slice_node)
            headers = (
                {str(item) for item in sequence if isinstance(item, str)}
                if sequence is not None
                else {literal}
                if literal is not None
                else set()
            )
            if headers and headers.issubset(set(self.outcome_columns)):
                base = self._frame(base_node, set(), 0)
                if base is not None and base.reader_rooted:
                    result.update(headers)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                result.update(self._outcome_headers(child, active, depth + 1))
        return frozenset(result)

    def _unresolved_execution_prevention_edge(self) -> bool:
        for node in _walk_statements((*self.original_scope, *self.scope)):
            if not isinstance(node, ast.Try):
                continue
            tracked_call = any(
                isinstance(item, ast.Call)
                and (bool(self._p_origins(item)) or len(self._outcome_headers(item, set(), 0)) >= 2)
                for statement in node.body
                for item in ast.walk(statement)
            )
            downstream_control = any(
                isinstance(item, (ast.If, ast.For, ast.While, ast.Assert, ast.Match))
                or (
                    isinstance(item, ast.Call)
                    and (
                        self.resolver.qualified(item.func) in _MT_TEST_APIS
                        or item in {sink.call for sink in self.sinks}
                    )
                )
                for statement in (*node.orelse, *node.finalbody)
                for item in ast.walk(statement)
            )
            if tracked_call and downstream_control:
                return True
        return False

    def _partition_guard(self, corrections: Sequence[_MtCorrection]) -> bool:
        manual_positions = set().union(
            *(set(item.positions) for item in corrections if item.api == "manual.bonferroni")
        )
        nonempty = [
            set(item.positions)
            for item in corrections
            if item.positions and item.api != "manual.bonferroni"
        ]
        if manual_positions:
            nonempty.append(manual_positions)
        if len(nonempty) >= 2 and any(
            left.isdisjoint(right)
            for index, left in enumerate(nonempty)
            for right in nonempty[index + 1 :]
        ):
            return True
        decision_containers: dict[str, set[int]] = defaultdict(set)
        for node in _walk_statements(self.scope):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"append", "add", "extend"}
                and isinstance(node.func.value, ast.Name)
            ):
                continue
            positions = frozenset().union(
                *(self._decision_positions_in_expr(item, set(), 0) for item in node.args)
            )
            decision_containers[node.func.value.id].update(positions)
        groups = [value for value in decision_containers.values() if value]
        return len(groups) >= 2 and any(
            left.isdisjoint(right)
            for index, left in enumerate(groups)
            for right in groups[index + 1 :]
        )

    def _resampling_guard(self) -> str | None:
        data_names = self._authorized_data_names()
        for node in sorted(
            (
                item
                for item in _walk_statements(self.original_scope)
                if isinstance(item, (ast.For, ast.comprehension))
            ),
            key=_position,
        ):
            body_nodes: Sequence[ast.AST]
            if isinstance(node, ast.For):
                body_nodes = node.body
                iterable = node.iter
            else:
                owner = _mt_comprehension_owner(self.original_scope, node)
                body_nodes = (owner,) if owner is not None else ()
                iterable = node.iter
            if not body_nodes or not self._resampling_body(body_nodes, data_names):
                continue
            cardinality = _v2_iterator_cardinality(iterable, self.full_resolver)
            if cardinality is None:
                cardinality = _mt_exact_outcome_factor(
                    iterable,
                    self.full_resolver,
                    self.outcome_columns,
                )
            if cardinality is None:
                return "resampling-cardinality-unresolved"
            if cardinality >= _V2_RESAMPLING_MIN_TRIPS and self._joint_resampling_reducer(
                body_nodes
            ):
                return "permutation-family-control-present"
        for call in sorted(
            (item for item in _walk_statements(self.original_scope) if isinstance(item, ast.Call)),
            key=_position,
        ):
            if not self._registered_random_draw(call):
                continue
            if not (_loaded_names(call) & data_names):
                continue
            cardinality = _v2_random_draw_cardinality(
                call,
                self.full_resolver,
                self.original_assignments,
            )
            if cardinality is None:
                return "resampling-cardinality-unresolved"
            if cardinality >= _V2_RESAMPLING_MIN_TRIPS:
                return "permutation-family-control-present"
        return None

    def _authorized_data_names(self) -> set[str]:
        names: set[str] = set()
        for name, expression in self.original_assignments.items():
            if (
                isinstance(expression, ast.Call)
                and self.full_resolver.qualified(expression.func)
                in {"pandas.read_csv", "numpy.genfromtxt"}
                and expression.args
                and _mt23_reader_path(expression, self.full_resolver, self.local_reader_paths)
                == self.authorized_path
            ):
                names.add(name)
        changed = True
        while changed:
            changed = False
            for name, expression in self.original_assignments.items():
                if name not in names and _loaded_names(expression) & names:
                    names.add(name)
                    changed = True
            for node in _walk_statements(self.original_scope):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"append", "extend", "add"}:
                    continue
                if not isinstance(node.func.value, ast.Name):
                    continue
                if any(_loaded_names(item) & names for item in node.args):
                    if node.func.value.id not in names:
                        names.add(node.func.value.id)
                        changed = True
        return names

    def _resampling_body(self, nodes: Sequence[ast.AST], data_names: set[str]) -> bool:
        operations = {
            "permutation",
            "shuffle",
            "choice",
            "sample",
            "integers",
            "randint",
            "random",
            "normal",
            "uniform",
        }
        carries_data = any(_loaded_names(node) & data_names for node in nodes)
        registered = any(
            isinstance(item, ast.Call) and (_mt_callee_terminal(item.func) or "") in operations
            for node in nodes
            for item in ast.walk(node)
        )
        return carries_data and registered

    def _joint_resampling_reducer(self, nodes: Sequence[ast.AST]) -> bool:
        reducers = {"min", "max", "nanmin", "nanmax", "count_nonzero", "sum", "sorted", "sort"}
        return any(
            isinstance(item, ast.Call) and (_mt_callee_terminal(item.func) or "") in reducers
            for node in nodes
            for item in ast.walk(node)
        )

    def _registered_random_draw(self, call: ast.Call) -> bool:
        api = self.full_resolver.qualified(call.func)
        if api in _V2_RANDOM_MODULE_DRAWS:
            return True
        return bool(
            isinstance(call.func, ast.Attribute) and call.func.attr in _V2_RANDOM_GENERATOR_METHODS
        )

    def _statistics_prefix_guard(self) -> bool:
        for call in sorted(
            (node for node in _walk_statements(self.original_scope) if isinstance(node, ast.Call)),
            key=_position,
        ):
            api = self.full_resolver.qualified(call.func)
            root = _call_chain_root(call, self.full_resolver)
            matched = next(
                (
                    candidate
                    for candidate in (api, root)
                    if candidate is not None and _prefix_hit(candidate, _STATISTICS_PREFIXES)
                ),
                None,
            )
            if matched is None or api in _MT_TEST_APIS or api in _MT_CORRECTION_APIS:
                continue
            if api == "scipy.stats.sem" and self._sem_exempt(call):
                continue
            return True
        return False

    def _sem_exempt(self, call: ast.Call) -> bool:
        if len(call.args) != 1 or any(
            item.arg not in {"axis", "ddof", "nan_policy"}
            or not _mt_closed_literal(item.value, self.full_resolver)
            for item in call.keywords
        ):
            return False
        return self._call_result_output_only(call)

    def _call_result_output_only(self, call: ast.Call) -> bool:
        target = _assigned_name(self.original_scope, call)
        origins = (
            (call,)
            if target is None
            else tuple(
                node
                for node in _walk_statements(self.original_scope)
                if isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == target
            )
        )
        if not origins:
            return False
        sinks = tuple(
            sink
            for sink in _registered_sinks(self.original_scope, self.full_resolver)
            if sink.p_result_eligible
        )
        payloads = {payload for sink in sinks for payload in sink.payloads}
        parents = {
            child: node
            for node in _walk_statements(self.original_scope)
            for child in ast.iter_child_nodes(node)
        }
        for origin in origins:
            cursor: ast.AST = origin
            while cursor not in payloads:
                parent = parents.get(cursor)
                if parent is None:
                    return False
                if isinstance(parent, (ast.UnaryOp, ast.BinOp, ast.FormattedValue, ast.JoinedStr)):
                    cursor = parent
                    continue
                if isinstance(parent, ast.Call):
                    api = self.full_resolver.qualified(parent.func)
                    terminal = _mt_callee_terminal(parent.func)
                    if api == "str" or terminal == "format":
                        cursor = parent
                        continue
                return False
        return True

    def _conclusion_positions(self) -> tuple[set[int], set[str]]:
        positions: set[int] = set()
        sink_kinds: set[str] = set()
        for match in self.terminal_closure.matches:
            if match.decision is not None:
                positions.add(match.occurrence.family_position)
                sink_kinds.add(match.sink.kind)
        for sink in self.sinks:
            if not sink.p_result_eligible:
                continue
            local: set[int] = set()
            for payload in sink.payloads:
                local.update(self._decision_positions_in_expr(payload, set(), 0))
                if isinstance(payload, ast.Name):
                    local.update(self._container_mutation_positions(payload.id))
            if local:
                positions.update(local)
                sink_kinds.add(sink.kind)
        for node in _walk_statements(self.scope):
            if not isinstance(node, ast.If):
                continue
            terminal_rendering = self._mt_v21_terminal_rendering_if(node)
            if terminal_rendering is not None:
                position, kinds = terminal_rendering
                positions.add(position)
                sink_kinds.update(kinds)
                continue
            test_positions = self._decision_positions_in_expr(node.test, set(), 0)
            if not test_positions:
                continue
            for call in (
                item
                for statement in node.body
                for item in ast.walk(statement)
                if isinstance(item, ast.Call)
            ):
                if not (
                    isinstance(call.func, ast.Attribute)
                    and call.func.attr in {"append", "add"}
                    and isinstance(call.func.value, ast.Name)
                    and len(call.args) == 1
                ):
                    continue
                outcome = self.resolver.string(call.args[0])
                if outcome not in self.outcome_columns:
                    continue
                position = self.outcome_columns.index(str(outcome))
                if position not in test_positions:
                    continue
                if self._name_reaches_output(call.func.value.id):
                    positions.add(position)
                    sink_kinds.update(
                        sink.kind
                        for sink in self.sinks
                        if sink.p_result_eligible
                        and any(call.func.value.id in _loaded_names(item) for item in sink.payloads)
                    )
        for node in self.scope:
            if not isinstance(node, ast.For):
                continue
            kind = self._dynamic_full_family_conclusion_loop(node)
            if kind is not None:
                positions.update(range(len(self.outcome_columns)))
                sink_kinds.add(kind)
        return positions, sink_kinds

    def _dynamic_full_family_conclusion_loop(self, node: ast.For) -> str | None:
        if not (
            not node.orelse
            and isinstance(node.target, ast.Name)
            and isinstance(node.iter, ast.Call)
            and self.resolver.qualified(node.iter.func) == "range"
            and len(node.iter.args) == 1
            and not node.iter.keywords
            and isinstance(node.iter.args[0], ast.Call)
            and self.resolver.qualified(node.iter.args[0].func) == "len"
            and len(node.iter.args[0].args) == 1
            and not node.iter.args[0].keywords
            and (
                self.resolver.sequence(node.iter.args[0].args[0]) is not None
                or self.resolver.table(node.iter.args[0].args[0]) is not None
            )
        ):
            return None
        comparisons = [item for item in ast.walk(node) if isinstance(item, ast.Compare)]
        if len(comparisons) != 1:
            return None
        comparison = comparisons[0]
        if not (
            len(comparison.ops) == 1
            and isinstance(comparison.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
            and len(comparison.comparators) == 1
        ):
            return None
        indexed: ast.Subscript | None = None
        threshold: ast.expr | None = None
        if isinstance(comparison.left, ast.Subscript):
            indexed = comparison.left
            threshold = comparison.comparators[0]
        elif isinstance(comparison.comparators[0], ast.Subscript):
            indexed = comparison.comparators[0]
            threshold = comparison.left
        if not (
            indexed is not None
            and threshold is not None
            and isinstance(indexed.value, ast.Name)
            and isinstance(indexed.slice, ast.Name)
            and indexed.slice.id == node.target.id
            and self._closed_builder_positions(indexed.value.id)
            == tuple(range(len(self.outcome_columns)))
            and _mt_decimal_literal(threshold, self.source) == Decimal("0.05")
        ):
            return None
        sinks = _registered_sinks(tuple(node.body), self.resolver)
        eligible = [sink.kind for sink in sinks if sink.p_result_eligible]
        return eligible[0] if eligible else None

    def _decision_positions_in_expr(self, node: ast.expr, active: set[str], depth: int) -> set[int]:
        if depth > _DEFINITION_NODE_MAX:
            return set()
        if isinstance(node, ast.Name):
            if node.id in active:
                return set()
            expression = self.assignments.get(node.id)
            if expression is None:
                bound = self.correction_return_names.get(node.id)
                return (
                    set(bound[0].positions) if bound is not None and bound[1] == "reject" else set()
                )
            return self._decision_positions_in_expr(expression, {*active, node.id}, depth + 1)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            member = _mt_literal_member(node.slice)
            stored = self.record_stores.get((node.value.id, member)) if member is not None else None
            if stored is not None:
                return self._decision_positions_in_expr(stored, active, depth + 1)
            if member is not None:
                precise, selected = self._precise_record_member(node.value.id, member, set(), 0)
                if precise and selected is not None:
                    return self._decision_positions_in_expr(selected, active, depth + 1)
            sequence = self._decision_sequence(node.value)
            if isinstance(member, int) and sequence is not None:
                index = member if member >= 0 else len(sequence) + member
                if 0 <= index < len(sequence):
                    return {sequence[index]}
        if isinstance(node, ast.Compare):
            origins = self._decision_origins(node.left)
            origins |= frozenset().union(
                *(self._decision_origins(item) for item in node.comparators)
            )
            if origins:
                return set(origins)
        vector = self._correction_vector_member(node, set(), 0)
        if vector is not None:
            correction, index = vector
            if 0 <= index < len(correction.ordered_positions):
                return {correction.ordered_positions[index]}
        result: set[int] = set()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                result.update(self._decision_positions_in_expr(child, active, depth + 1))
        return result

    def _container_mutation_positions(self, name: str) -> set[int]:
        result: set[int] = set()
        for node in _walk_statements(self.scope):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == name
                and node.func.attr in {"append", "add", "extend"}
            ):
                continue
            for argument in node.args:
                result.update(self._decision_positions_in_expr(argument, set(), 0))
        return result

    def _name_reaches_output(self, name: str) -> bool:
        return any(
            name in _loaded_names(payload)
            for sink in self.sinks
            if sink.p_result_eligible
            for payload in sink.payloads
        )

    def _evidence_spans(
        self, corrections: Sequence[_MtCorrection]
    ) -> tuple[MultipleTestingEvidenceSpan, ...]:
        spans: list[MultipleTestingEvidenceSpan] = []
        reader_calls = [
            node
            for node in _walk_statements(self.scope)
            if isinstance(node, ast.Call)
            and self.resolver.qualified(node.func) in {"pandas.read_csv", "numpy.genfromtxt"}
            and node.args
            and _mt23_reader_path(node, self.resolver, self.local_reader_paths)
            == self.authorized_path
        ]
        if reader_calls:
            spans.append(_mt_evidence_span("reader", None, reader_calls[0]))
        for call, position in sorted(self.call_position.items(), key=lambda item: item[1]):
            spans.append(_mt_evidence_span("test_call", position, call))
            members = [
                node
                for node in _walk_statements(self.scope)
                if isinstance(node, ast.Attribute)
                and node.attr == "pvalue"
                and position in self._p_origins(node)
            ]
            if members:
                spans.append(_mt_evidence_span("pvalue_member", position, members[0]))
        for correction in corrections:
            spans.append(_mt_evidence_span("correction", None, correction.call))
        for comparison in (
            node for node in _walk_statements(self.scope) if isinstance(node, ast.Compare)
        ):
            for position in sorted(self._decision_positions_in_expr(comparison, set(), 0)):
                spans.append(_mt_evidence_span("conclusion", position, comparison))
        for sink in self.sinks:
            if sink.p_result_eligible and any(
                self._decision_positions_in_expr(payload, set(), 0) for payload in sink.payloads
            ):
                spans.append(_mt_evidence_span("output_sink", None, sink.call))
        unique = {
            (
                item.role,
                item.family_position,
                item.start_line,
                item.end_line,
                item.start_column,
                item.end_column,
            ): item
            for item in spans
        }
        return tuple(sorted(unique.values()))


def _mt_closed_literal(node: ast.expr, resolver: _Resolver) -> bool:
    if isinstance(node, ast.Name):
        value = resolver.literals.get(node.id, resolver.constants.get(node.id))
        return bool(
            isinstance(value, (str, bool, int))
            or (isinstance(value, float) and math.isfinite(value))
        )
    if isinstance(node, ast.Constant):
        literal_value = node.value
        return bool(
            literal_value is None
            or isinstance(literal_value, (str, bool, int))
            or (isinstance(literal_value, float) and math.isfinite(literal_value))
        )
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, (int, float))
        and not isinstance(node.operand.value, bool)
    ):
        value = node.operand.value
        return not isinstance(value, float) or math.isfinite(value)
    return False


def _mt_literal_member(node: ast.expr) -> str | int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (str, int))
        and not isinstance(node.value, bool)
    ):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, int)
        and not isinstance(node.operand.value, bool)
    ):
        return -node.operand.value
    return None


def _mt_v21_display_string(node: ast.expr) -> bool:
    return bool(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value
        and "\x00" not in node.value
        and len(node.value.encode("utf-8")) <= 256
    )


def _mt_v21_percent_payload(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> bool:
    owner = parents.get(node)
    return bool(
        isinstance(owner, ast.BinOp)
        and isinstance(owner.op, ast.Mod)
        and owner.right is node
        and _mt_v21_display_string(owner.left)
    )


def _mt_v21_destructured_names(node: ast.expr) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, (ast.List, ast.Tuple)) and node.elts:
        values: list[str] = []
        for item in node.elts:
            nested = _mt_v21_destructured_names(item)
            if nested is None:
                return None
            values.extend(nested)
        return tuple(values) if len(values) == len(set(values)) else None
    return None


def _mt_exact_int(node: ast.expr | None, resolver: _Resolver, expected: int) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Constant):
        return bool(
            isinstance(node.value, int)
            and not isinstance(node.value, bool)
            and node.value == expected
        )
    if isinstance(node, ast.Name):
        value = resolver.literals.get(node.id)
        return bool(isinstance(value, int) and not isinstance(value, bool) and value == expected)
    return False


def _mt_literal_axis(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant):
        return node.value is None or (
            isinstance(node.value, int) and not isinstance(node.value, bool) and node.value == 0
        )
    return bool(
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and node.operand.value == 1
    )


def _mt_optional_literal_int(node: ast.expr | None) -> int | None:
    if node is None:
        return None
    value = _mt_literal_member(node)
    return value if isinstance(value, int) else None


def _mt_decimal_literal(node: ast.expr, source: str) -> Decimal | None:
    if not (
        isinstance(node, ast.Constant)
        and not bool(getattr(node, "_sc_mt_row_derived", False))
        and not isinstance(node.value, bool)
        and isinstance(node.value, (int, float))
        and (not isinstance(node.value, float) or math.isfinite(node.value))
    ):
        return None
    text = ast.get_source_segment(source, node)
    if text is not None:
        try:
            return Decimal(text)
        except InvalidOperation:
            return None
    try:
        return Decimal(repr(node.value))
    except InvalidOperation:
        return None


def _mt_binding_count(statements: Sequence[ast.stmt], name: str) -> int:
    count = 0
    for node in _walk_statements(statements):
        if (
            isinstance(node, ast.Name)
            and node.id == name
            and isinstance(node.ctx, (ast.Store, ast.Del))
        ):
            count += 1
        elif isinstance(node, ast.arg) and node.arg == name:
            count += 1
        elif isinstance(node, ast.alias):
            bound = node.asname
            if bound is None:
                parent = next(
                    (
                        item
                        for item in _walk_statements(statements)
                        if isinstance(item, (ast.Import, ast.ImportFrom)) and node in item.names
                    ),
                    None,
                )
                bound = node.name.split(".", 1)[0] if isinstance(parent, ast.Import) else node.name
            if bound == name:
                count += 1
        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
        ):
            count += 1
        elif isinstance(node, ast.ExceptHandler) and node.name == name:
            count += 1
        elif isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names:
            count += 1
        elif isinstance(node, ast.MatchAs) and node.name == name:
            count += 1
        elif isinstance(node, ast.MatchStar) and node.name == name:
            count += 1
        elif isinstance(node, ast.MatchMapping) and node.rest == name:
            count += 1
    return count


def _mt_callee_terminal(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _mt_comprehension_owner(
    statements: Sequence[ast.stmt], target: ast.comprehension
) -> ast.AST | None:
    for node in _walk_statements(statements):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) and any(
            item is target for item in node.generators
        ):
            return node
    return None


def _mt_evidence_span(
    role: str, family_position: int | None, node: ast.AST
) -> MultipleTestingEvidenceSpan:
    start_line, end_line, start_column, end_column = _span(node)
    return MultipleTestingEvidenceSpan(
        role,
        family_position,
        start_line,
        end_line,
        start_column,
        end_column,
    )


def _mt30_registered_apis_by_position(
    tree: ast.Module,
    resolver: _Resolver,
    outcome_columns: tuple[str, ...],
    detail: Mapping[str, object],
) -> tuple[str, ...] | None:
    """Resolve the truthful ordered API vector; spelling never supplies family position."""

    recorded = detail.get("api_by_position", detail.get("dispatch_api_by_position"))
    if isinstance(recorded, list) and len(recorded) == len(outcome_columns):
        values = tuple(recorded)
        if all(isinstance(item, str) and item in _MT_TEST_APIS for item in values):
            return cast(tuple[str, ...], values)
        return None
    apis = {
        str(api)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and (api := resolver.qualified(node.func)) in _MT_TEST_APIS
    }
    if len(apis) != 1:
        return None
    api = next(iter(apis))
    return tuple(api for _ in outcome_columns)


def _mt30_correction_methods(tree: ast.Module, resolver: _Resolver) -> tuple[str, ...]:
    methods: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        api = resolver.qualified(node.func)
        if api not in _MT_CORRECTION_APIS:
            continue
        method_node = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "method"), None
        )
        if method_node is None and api == "statsmodels.stats.multitest.multipletests":
            method_node = node.args[2] if len(node.args) >= 3 else None
        value: object | None = None
        if isinstance(method_node, ast.Constant):
            value = method_node.value
        elif isinstance(method_node, ast.Name):
            value = resolver.constants.get(method_node.id, resolver.literals.get(method_node.id))
        if isinstance(value, str) and value:
            methods.add(value)
        elif api == "statsmodels.stats.multitest.multipletests":
            methods.add("hs")
        elif api == "statsmodels.stats.multitest.fdrcorrection":
            methods.add("indep")
        elif api == "scipy.stats.false_discovery_control":
            methods.add("bh")
        else:
            methods.add("benjamini-hochberg")
    return tuple(sorted(methods))


def _mt30_record_evidence_spans(
    tree: ast.Module,
    resolver: _Resolver,
    apis_by_position: tuple[str, ...],
) -> tuple[MultipleTestingEvidenceSpan, ...]:
    calls_by_api: dict[str, list[ast.Call]] = defaultdict(list)
    corrections: list[ast.Call] = []
    p_members: list[ast.AST] = []
    conclusions: list[ast.AST] = []
    sinks: list[ast.Call] = []
    records: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            api = resolver.qualified(node.func)
            if api in _MT_TEST_APIS:
                calls_by_api[str(api)].append(node)
            if api in _MT_CORRECTION_APIS:
                corrections.append(node)
            if api == "print" or (
                isinstance(node.func, ast.Attribute) and node.func.attr in {"write", "writelines"}
            ):
                sinks.append(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "append" and node.args:
                records.append(node.args[0])
        elif isinstance(node, ast.Attribute) and node.attr == "pvalue":
            p_members.append(node)
        elif isinstance(node, (ast.Compare, ast.IfExp)):
            conclusions.append(node)
    all_test_calls = [call for values in calls_by_api.values() for call in values]
    if not all_test_calls:
        return ()
    spans: list[MultipleTestingEvidenceSpan] = []
    per_api_index: Counter[str] = Counter()
    for position, api in enumerate(apis_by_position):
        options = calls_by_api.get(api, all_test_calls)
        call = options[min(per_api_index[api], len(options) - 1)]
        per_api_index[api] += 1
        spans.append(_mt_evidence_span("test_call", position, call))
        spans.append(
            _mt_evidence_span(
                "pvalue_member",
                position,
                p_members[min(position, len(p_members) - 1)] if p_members else call,
            )
        )
        spans.append(
            _mt_evidence_span(
                "conclusion",
                position,
                conclusions[min(position, len(conclusions) - 1)]
                if conclusions
                else sinks[0]
                if sinks
                else call,
            )
        )
    spans.extend(_mt_evidence_span("correction", None, call) for call in corrections)
    spans.extend(_mt_evidence_span("record_construction", None, node) for node in records)
    spans.append(_mt_evidence_span("output_sink", None, sinks[0] if sinks else all_test_calls[0]))
    return tuple(spans)


def _mt30_model_facts(
    content: bytes,
    *,
    outcome_columns: tuple[str, ...],
    outcome: object,
    detail: Mapping[str, object],
) -> MultipleTestingDataflowResult:
    tree = _bounded_parse(content)
    resolver, reason = _resolver(tuple(item for item in tree.body if not _is_docstring(item)))
    if reason is not None or resolver is None:
        return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
    apis = _mt30_registered_apis_by_position(tree, resolver, outcome_columns, detail)
    if apis is None:
        return MultipleTestingDataflowResult(None, "family-test-api-dispatch-unresolved")
    state = getattr(outcome, "state", None)
    classification = getattr(outcome, "reason_or_classification", None)
    corrected = getattr(outcome, "corrected_positions", ())
    if state not in {"candidate", "covered"} or classification not in {
        "none",
        "strict_subset",
        "complete",
    }:
        return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
    if not isinstance(corrected, tuple) or not all(isinstance(item, int) for item in corrected):
        return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
    spans = _mt30_record_evidence_spans(tree, resolver, apis)
    if not spans:
        return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
    sinks = tuple(
        sorted(
            {
                "print"
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and resolver.qualified(node.func) == "print"
            }
        )
    )
    return MultipleTestingDataflowResult(
        MultipleTestingDataflowFacts(
            registered_test_api=apis[0],
            registered_test_apis_by_position=apis,
            family_size=len(outcome_columns),
            corrected_positions=corrected,
            conclusion_positions=tuple(range(len(outcome_columns))),
            correction_classification=cast(
                Literal["none", "strict_subset", "complete"], classification
            ),
            correction_methods=_mt30_correction_methods(tree, resolver),
            output_sink_kinds=sinks or ("print",),
            evidence_spans=spans,
        ),
        None,
    )


def analyze_code_csv_multiple_testing_dataflow(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Sequence[str],
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Run the frozen 2.3-compatible proof and the closed 3.0 record side table."""

    baseline = _analyze_code_csv_multiple_testing_baseline(
        content,
        authorized_path=authorized_path,
        group_column=group_column,
        outcome_columns=outcome_columns,
        csv_header=csv_header,
        group_values=group_values,
        csv_content=csv_content,
    )
    record_model_walls = {
        "authorized-family-test-census-incomplete",
        "mixed-test-api-family",
        "pvalue-family-collection-unresolved",
        "unresolved-pvalue-consumer",
        "correction-family-lineage-unresolved",
        "test-battery-cardinality-unresolved",
    }
    if baseline.reason not in record_model_walls:
        return baseline
    try:
        from sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3 import (
            analyze_record_model,
        )

        model = analyze_record_model(
            content,
            authorized_path=authorized_path,
            group_column=group_column,
            outcome_columns=outcome_columns,
            csv_header=csv_header,
            group_values=group_values,
            csv_content=csv_content,
        )
        if not model.changed:
            return baseline
        if model.outcome.state == "abstain":
            return MultipleTestingDataflowResult(None, model.outcome.reason_or_classification)
        return _mt30_model_facts(
            content,
            outcome_columns=outcome_columns,
            outcome=model.outcome,
            detail=model.detail,
        )
    except (ArithmeticError, RecursionError, UnicodeError, ValueError):
        return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
