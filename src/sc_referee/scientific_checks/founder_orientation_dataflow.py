"""ADR-0069 static dataflow resolution of founder-panel orientation before emission.

This library works backward from the per-marker equality that selects an
emission probability. It reads each Python workflow source statically, tags
the provenance of every row set read from a staged CSV input, and tracks, per
column, whether the value reaching that equality is the staged value or its
involution (0 <-> 1). Both operands of the equality must be columns of the
same row set; the parity of the recognized value-inverting steps on the two
operand paths, taken together, is the answer. An odd total parity means one
panel was complement-repaired before the comparison; an even total parity
means the comparison reads the two panels in the same coding. Variable
names, function names, and column names never matter; only the operations do.

v2.1.0 inverts the trust model. Versions through v2.0.1 enumerated dangerous
forms and treated every unlisted piece of Python as safe; a second
adversarial review demonstrated thirteen ordinary workflows where that
deny-list produced a confident answer opposite to what the workflow computes
at run time. This version holds an explicit whitelist instead. The module
states the statement forms and the expression forms it models completely,
and any form outside that whitelist, anywhere in the module, leaves the
document unsupported. No statement is exempted for "not touching anything
interesting": an unlisted statement type is unsupported whatever it mentions,
which closes ``match``, ``try``, ``while``, ``class``, ``del``, ``global``,
``raise``, ``assert``, every ``async`` form, and everything else in one rule
rather than one enumeration at a time.

The whitelist, at module top level:

- ``import`` and ``from ... import``, recorded in an import table.
- ``Assign`` with exactly one plain ``Name`` target and a fully readable
  right-hand side. Tuple, starred, chained, subscript, attribute, and
  annotated targets, and augmented assignment, are unsupported.
- ``FunctionDef``, subject to the helper rules. A name defined by ``def``
  more than once, whose name appears anywhere outside call position, or that
  calls one of its own parameters, is an opaque callable, and any call to an
  opaque callable is unsupported. A body binds only its parameters, so every
  other free name it reads is opaque rather than the module's binding, and a
  body referencing a tagged row set is unsupported outright.
- ``Expr`` statements only as a docstring constant, a recognized report
  write, or a call to ``print`` whose whole argument subtree is names,
  constants, f-strings over them, and ``str``/``repr`` of a name.
- ``With`` only in the modelled ``open()``-as pattern, ``If`` only as the
  ``__main__`` guard, and ``For`` only in the recognized counter and
  accumulator forms.
- A walrus anywhere in any statement's complete subtree is unsupported.

A tagged or aliased row set may appear only as the iterable of a recognized
comprehension or recognized loop, as the argument of ``len``, as the
right-hand side of a plain alias assignment, or inside the recognized
print-read form. Every other occurrence -- an argument to any other call, an
element of a container, the receiver of any method call, a reference from
inside a function body -- is unsupported. Mutation is no longer modelled at
all, because every syntactic route to mutating a tagged row set now dies at
the whitelist instead.

Three belts run independently of the whitelist:

- The emission scan walks the entire module tree for comparisons between two
  staged-column extractions. If the document resolves, every such comparison
  must have been recognized by the trace; an unrecognized one anywhere is
  unsupported.
- Reachability excludes and never selects. Writes and returns seed the
  report-reaching set only from functions reachable code actually calls,
  path-likeness is tracked with last-binding-wins so rebinding a path name to
  an in-memory buffer removes it, and orientation readings are collected
  module-wide: readings that disagree resolve only when every disagreeing
  reading sits in a function with no occurrence besides its own definition.
- Parsing is guarded. ``RecursionError`` and ``MemoryError`` from a source
  too deep or too large for the parser abstain instead of crashing.

Soundness rules (each backed by a demonstrated counterexample in
``tests/test_founder_orientation_soundness.py``):

- ``direct`` is never a fallthrough. An unrecognized transform on an operand
  path abstains; it never reads as the direct orientation.
- Inversions on both operands compose to no net change, and classify as the
  direct reading only when both paths are otherwise identity-proven.
- A transform that is not on either operand's path has no effect, unless it
  produces a second orientation reading that disagrees.
- Any statement or expression form outside the whitelist abstains.
- Any occurrence of a tagged row set outside its four permitted positions
  abstains.
- The reader vocabulary applies only to a call that provably resolves to the
  ``csv`` module through the import table.
- Helper tracing is depth-bounded with cycle detection, expression tracing
  carries its own depth bound, and parsing is guarded; recursion abstains
  instead of crashing.

The report-reaching closure, the statement flattening, the ``__main__``
guard recognition, the call-binding shape, and the evidence-span projection
are modelled on ``quantity_dataflow_adapter``; they are copied rather than
imported so the two recognizers stay independently versionable and neither
module's identity moves when the other changes.
"""

from __future__ import annotations

import ast
import builtins
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
)

FOUNDER_ORIENTATION_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())

_MAX_CALL_DEPTH = 2
_MAX_EXPRESSION_DEPTH = 100
_READER_ORIGINS = {"csv.DictReader", "csv.reader"}
_READER_ATTRIBUTES = {"DictReader", "reader"}
_PATH_CALLS = {"Path", "pathlib.Path", "PurePath", "pathlib.PurePath"}
_ACCUMULATOR_CALLS = {"sum", "prod", "math.prod", "fsum", "math.fsum"}
_IDENTITY_CASTS = {"int", "float", "str"}
_STRIP_METHODS = {"strip", "lstrip", "rstrip"}
_WRITE_METHODS = {"write", "writelines", "write_text"}
_EXACT_NUMERIC_CALLS = {
    "Fraction",
    "fractions.Fraction",
    "Decimal",
    "decimal.Decimal",
}
# Calls admitted inside a container literal. A container literal is where a
# row is rebuilt, so anything evaluated there can mutate the row being read;
# only the recode and extraction vocabulary is allowed.
_CONTAINER_VALUE_CALLS = _IDENTITY_CASTS | _EXACT_NUMERIC_CALLS | {"abs"}
# Reflection and dynamic-dispatch builtins. Any of these anywhere -- called,
# referenced, or aliased -- makes runtime behavior unknowable to a static
# trace: ``globals()["rows"]`` mutates a tagged row set without naming it,
# ``type()`` builds an object whose ``__str__`` runs arbitrary code inside an
# admitted ``print``, and ``getattr`` dispatches to anything.
_BANNED_NAMES = frozenset(
    {
        "globals",
        "locals",
        "vars",
        "eval",
        "exec",
        "compile",
        "breakpoint",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "type",
        "super",
        "object",
        "memoryview",
        "classmethod",
        "staticmethod",
        "property",
        "__builtins__",
        "__loader__",
        "__spec__",
    }
)
# Importing a module executes it. Only these stdlib modules may be imported;
# anything else -- including a relative import, which resolves inside an
# unmodelled package -- leaves the document unsupported.
_ALLOWED_IMPORT_MODULES = frozenset(
    {"csv", "math", "pathlib", "fractions", "decimal", "statistics"}
)
# Inert string methods: safe on builtin-typed receivers, and user-defined
# types cannot exist here (class statements and ``type()`` are banned).
_SAFE_STR_METHODS = frozenset({"join", "format"})
# Inert Path navigation: reads filesystem metadata at most, never row data.
_SAFE_PATH_METHODS = frozenset({"resolve", "absolute", "expanduser", "joinpath"})
_BUILTIN_NAMES = frozenset(dir(builtins))

_REPAIRED = "repaired"
_DIRECT = "direct"


def founder_orientation_dataflow_grammar(
    direct_operand: str, repaired_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "founder-orientation-emission-dataflow",
        "grammar_version": "2.1.5",
        "trust_model": (
            "default deny: the trace holds an explicit whitelist of the statement and "
            "expression forms it models completely, and any form outside that whitelist "
            "anywhere in the module leaves the document unsupported; an unlisted "
            "statement type is unsupported whatever names it mentions, and an "
            "unrecognized call is unsupported whether or not it names traced state"
        ),
        "module_bans": [
            "reflection and dynamic-dispatch builtins (globals, eval, getattr, type, "
            "and kin) anywhere, referenced or called",
            "any binding that shadows a Python builtin name",
            "any parameter or return annotation",
            "imports outside an allowlisted stdlib set (csv, math, pathlib, fractions, "
            "decimal, statistics); every relative and star import; any import whose "
            "name matches any path component of any document in the case (flat "
            "modules, packages, and namespace directories all shadow the stdlib)",
        ],
        "helper_selectors": (
            "the one recognized factoring: an accumulated element or loop "
            "payload that is exactly one call to a local straight-line helper "
            "whose whole body returns one canonical selector comparing its two "
            "parameters; the call's operand paths classify as an inline "
            "comparison would. Any other comparison between two bare names, "
            "anywhere, must have been recognized or the document abstains"
        ),
        "canonical_selectors": (
            "a selector classifies only as an equality comparison whose match "
            "branch is a strictly larger proven numeric constant than its "
            "mismatch branch; inequality operators, swapped branches, and "
            "name-valued branches are extensionally ambiguous between an "
            "orientation repair and a reparameterized emission matrix, so "
            "they are never recognized and emission-like comparisons inside "
            "them abstain"
        ),
        "numeric_provenance": (
            "a parity inversion (1-x, x^1, abs(x-1), not x, a lookup table) counts "
            "only on a value proven numeric by an int or float cast; a raw CSV string "
            "under these operations is a crash or a constant, never a recode; the "
            "numeric proof rides through row rebuilds, and a comparison whose two "
            "sides differ in effective runtime type abstains"
        ),
        "output_inertness": (
            "print and report-write payloads are names, constants, f-strings, "
            "arithmetic over those, and str/repr of names; a call inside a payload is "
            "unsupported because payloads are evaluated"
        ),
        "row_source_operations": [
            "csv.DictReader and csv.reader, only when the call resolves to the csv "
            "module through the module's own import table"
        ],
        "emission_comparison": (
            "an equality or inequality between two distinct columns of one "
            "staged row set, selecting between two numeric values inside a "
            "product or sum accumulation whose value reaches the written report"
        ),
        "selector_forms": [
            "conditional expression whose test is the comparison",
            "two-element list, tuple, or dict literal indexed by the comparison",
        ],
        "accumulation_forms": [
            "sum, prod, math.prod, or math.fsum over a comprehension",
            "a comprehension bound to a name that one of those consumes",
            "an elementwise multiply or add accumulation loop over the row set",
        ],
        "involutive_recode_forms": [
            "1 - x",
            "x ^ 1",
            "abs(x - 1)",
            "not x and int(not x)",
            "1 if x == 0 else 0 and its mirrored forms",
            "{0: 1, 1: 0}[x]",
            "a two-element list or tuple literal indexed by x with a reversed domain",
            "a row-column comprehension applying any of the above",
            "a straight-line local helper applying any of the above",
            "a recognized elementwise accumulation loop applying any of the above",
        ],
        "identity_preserving_steps": [
            "int, float, and str casts",
            "strip, lstrip, and rstrip on a column value",
            "assignment and list materialization of a row set",
            "constant-string column subscripts",
            (
                "dict literals and dict-spread literals rebuilding a row, read "
                "strictly left to right so a later entry overrides an earlier one, "
                "and containing no call outside the recode and extraction vocabulary"
            ),
        ],
        "whitelisted_statements": [
            "import and from-import, recorded in an import table",
            "assignment to exactly one plain name from a fully readable expression",
            "function definition subject to the helper rules",
            "expression statement only as a docstring, a recognized report write, "
            "or the recognized print-read form",
            "with only in the modelled open()-as pattern",
            "if only as the __main__ guard",
            "for only in the recognized counter and accumulator forms",
        ],
        "unsupported_statements": (
            "every statement type not on the whitelist, including match, try, while, "
            "class, del, global, nonlocal, raise, assert, and every async form; a "
            "walrus anywhere in any statement subtree is unsupported"
        ),
        "readable_expressions": [
            "comprehensions and generators of the recognized shape over a name or "
            "a recognized reader call",
            "dict, list, set, and tuple literals with constant keys whose values "
            "contain no call outside the recode and extraction vocabulary",
            "the recognized reader calls",
            "the recognized accumulation calls over recognized generators",
            "arithmetic, comparison, and f-string composition over readable parts",
            "a plain name, which creates an alias group",
        ],
        "unreadable_expressions": (
            "an unrecognized call or attribute access referencing a tagged or aliased "
            "name is unsupported; the same without any tagged reference leaves the "
            "assignment target opaque"
        ),
        "tagged_name_positions": (
            "a tagged or aliased row set may appear only as the iterable of a "
            "recognized comprehension or recognized loop, as the argument of len, as "
            "the right-hand side of a plain alias assignment, or inside the "
            "recognized print-read form; every other occurrence is unsupported, and "
            "mutation is not modelled because no syntactic route to it survives"
        ),
        "classification_rule": (
            "odd total parity over both operand paths is the repaired "
            "orientation; even total parity is the direct orientation, and only "
            "when every step on both paths is recognized; anything unrecognized, "
            "unresolved, or conflicting abstains"
        ),
        "operand_by_parity": {
            "odd_total_parity": repaired_operand,
            "even_total_parity_with_proven_paths": direct_operand,
        },
        "conditional_repair": (
            "not recognized; a branch is not a whitelisted statement and a "
            "conditional expression over row sets is not a permitted position for a "
            "tagged name, so either leaves the document unsupported"
        ),
        "control_flow": (
            "straight-line assignments, comprehensions, the modelled with-block, "
            "functions, the __main__ guard, and recognized accumulation and "
            "row-building loops; every other statement type leaves the document "
            "unsupported"
        ),
        "function_support": (
            "straight-line bodies whose first top-level return is the last "
            "statement; positional and keyword call binding; parameters mask all "
            "globals, so calling a parameter makes the helper opaque; a body may "
            "reference only its own parameters, safe builtins, the import table, and "
            "other module functions, and referencing a tagged row set is unsupported; "
            "a duplicated or non-call-position name is opaque everywhere and any call "
            "to it is unsupported; depth-bounded with cycle detection"
        ),
        "assignment_support": (
            "single-name assignment only; names bound to one another share an "
            "alias group; every other assignment form leaves the document unsupported"
        ),
        "report_reachability": (
            "a write whose receiver resolves to a filesystem path under "
            "last-binding-wins path tracking, or a return, and either only from a "
            "function reachable code actually calls; reachability excludes and never "
            "selects, and orientation readings collected module-wide must agree "
            "unless every disagreeing reading is provably dead"
        ),
        "parse_guard": (
            "RecursionError and MemoryError raised while parsing or analysing a "
            "source abstain as unsupported"
        ),
        "soundness": [
            "default deny: unlisted statement and expression forms abstain",
            "direct is never a fallthrough",
            "unrecognized operand-path transforms abstain",
            "joint operand inversions compose to the direct reading only when proven",
            "tagged row sets abstain outside their four permitted positions",
            "unrecognized report-reaching emission selectors abstain",
            "an unrecognized staged-column comparison anywhere abstains",
            "guarded row-set rebinding abstains",
            "report-reaching value linkage with last-binding-wins path tracking",
            "module-wide conflicting classifications abstain",
            "opaque callables abstain instead of resolving to a body",
            "the reader vocabulary requires a proven csv import",
            "bounded call depth with cycle abstention",
            "bounded expression-tracing depth",
            "guarded parsing",
        ],
        "nomenclature_authority": "none",
    }


def founder_orientation_dataflow_grammar_digest(direct_operand: str, repaired_operand: str) -> str:
    return semantic_digest(founder_orientation_dataflow_grammar(direct_operand, repaired_operand))


# ---------------------------------------------------------------------------
# Value model.


@dataclass(frozen=True)
class _Rows:
    """A row set, with per-column provenance relative to the staged read.

    ``overrides`` maps an output column to the staged column it came from,
    the parity of the recognized inverting steps on the way, and whether the
    stored value is numerically proven (a rebuilt column holds whatever type
    its expression produced, not the CSV's string), or to ``None`` when the
    column passed through something this library cannot read.
    ``default_identity`` says whether a column absent from ``overrides``
    passes through unchanged.
    """

    overrides: tuple[tuple[str, tuple[str, int, bool] | None], ...] = ()
    default_identity: bool = True
    iterator: bool = False


@dataclass(frozen=True)
class _Scalar:
    pass


@dataclass(frozen=True)
class _EmptyList:
    pass


@dataclass(frozen=True)
class _Opaque:
    pass


_OPAQUE = _Opaque()
_EMPTY_LIST = _EmptyList()

_Value = _Rows | _Scalar | _EmptyList | _Opaque


@dataclass(frozen=True)
class _Path:
    """A resolved column origin, or the unresolved marker when ``column`` is None.

    ``numeric`` records whether the value has passed through a numeric cast.
    A raw CSV column value is a string, and every parity-inverting operation
    is arithmetic over 0 and 1: ``not "0"`` is ``False`` for any non-empty
    string, ``1 - "0"`` raises, and ``x == 0`` is constantly false. An
    inversion therefore counts only on a numerically-proven value; on
    anything else the path is unresolved and the document abstains.
    """

    column: str | None
    parity: int = 0
    numeric: bool | None = None
    boolean: bool = False

    @property
    def resolved(self) -> bool:
        return self.column is not None


_UNRESOLVED = _Path(None)


@dataclass(frozen=True)
class _Classification:
    node: ast.AST
    state: str
    reaching: bool = True
    dead: bool = False


@dataclass(frozen=True)
class FounderDataflowResolution:
    """The outcome of the bounded source trace across every Python document."""

    state: str  # "unique" | "none" | "ambiguous" | "unsupported"
    orientation: str | None  # "repaired" | "direct" | None
    operand_value: str | None
    spans: tuple[EvidenceSpan, ...]
    source_path: str | None


@dataclass(frozen=True)
class _ModuleModel:
    """Everything about a module that the trace and the whitelist both need."""

    imports: dict[str, str]
    functions: dict[str, ast.FunctionDef]
    opaque_callables: frozenset[str]
    reachable_functions: frozenset[str]
    dead_functions: frozenset[str]
    write_call_ids: frozenset[int]
    reaching: frozenset[str]
    accumulated: frozenset[int]


@dataclass
class _TraceContext:
    model: _ModuleModel
    accumulated: set[int] = field(default_factory=set)
    reaching: set[str] = field(default_factory=set)
    depth: int = 0
    expression_depth: int = 0
    visiting: set[str] = field(default_factory=set)
    recognized_loops: set[int] = field(default_factory=set)
    recognized_compares: set[int] = field(default_factory=set)
    tagged_names: set[str] = field(default_factory=set)
    unresolved: bool = False

    @property
    def functions(self) -> dict[str, ast.FunctionDef]:
        return self.model.functions

    @property
    def opaque_callables(self) -> frozenset[str]:
        return self.model.opaque_callables


class _Aliases:
    """Names that are known to reference one runtime row-set object.

    A plain ``alias = rows`` binds two names to the same list. Mutation is no
    longer modelled -- every syntactic route to mutating a tagged row set is
    outside the whitelist -- but the groups still record which names denote
    one panel, so the tagged-name position rules cover all of them.
    """

    def __init__(self, groups: dict[str, set[str]] | None = None) -> None:
        self._groups: dict[str, set[str]] = groups or {}

    def copy(self) -> _Aliases:
        copied: dict[str, set[str]] = {}
        for group in self._groups.values():
            shared = set(group)
            for name in shared:
                copied[name] = shared
        return _Aliases(copied)

    def group(self, name: str) -> set[str]:
        return set(self._groups.get(name, {name}))

    def detach(self, name: str) -> None:
        group = self._groups.pop(name, None)
        if group is not None:
            group.discard(name)

    def link(self, name: str, other: str) -> None:
        merged = self._groups.get(name, {name}) | self._groups.get(other, {other})
        merged = set(merged)
        for member in merged:
            self._groups[member] = merged


# ---------------------------------------------------------------------------
# The public resolver.


def _guarded_parse(source: str, *, filename: str) -> ast.Module | None:
    """Parse a source, or return ``None`` when parsing cannot complete.

    A deeply nested but perfectly valid expression exhausts the interpreter
    stack inside ``ast`` itself, and an enormous one exhausts memory. Either
    is an abstention, never a crash.
    """

    try:
        return ast.parse(source, filename=filename)
    except (SyntaxError, ValueError, RecursionError, MemoryError, OverflowError):
        return None


def resolve_founder_orientation_dataflow(
    context: FrozenInspectionContext,
    *,
    direct_operand: str,
    repaired_operand: str,
    parser_id: str,
    parser_version: str,
) -> FounderDataflowResolution:
    classifications: list[tuple[InspectionDocument, _Classification]] = []
    unsupported = False
    parse_failure = False
    # Every path component of every document is a shadowable module name: a
    # flat ``csv.py``, a package ``csv/__init__.py``, and even a bare data
    # directory named ``csv`` (a namespace package) all shadow the stdlib at
    # runtime. The package form reaching an import undetected was a
    # demonstrated wrong answer.
    case_module_names: set[str] = set()
    for document in context.documents:
        parts = Path(document.path).parts
        case_module_names.update(parts[:-1])
        if document.path.endswith(".py"):
            stem = Path(document.path).stem
            if stem != "__init__":
                case_module_names.add(stem)
    for document in context.documents:
        if document.media_type != "text/x-python" or not _python_parser_supported(
            document, parser_id, parser_version
        ):
            continue
        try:
            source = document.content.decode("utf-8")
        except UnicodeDecodeError:
            parse_failure = True
            continue
        tree = _guarded_parse(source, filename=document.path)
        if tree is None:
            parse_failure = True
            continue
        if _imports_case_module(tree, case_module_names - {Path(document.path).stem}):
            # An import that resolves to another document in this very case
            # shadows the stdlib module of the same name at runtime; what
            # such a module does on import is outside this trace.
            unsupported = True
            continue
        outcome = _document_orientations(tree)
        unsupported = unsupported or bool(outcome["unsupported"])
        classifications.extend((document, item) for item in outcome["classifications"])
    states = sorted({item.state for _, item in classifications})
    if unsupported or parse_failure:
        # A resolved comparison next to an unreadable transform or an
        # untraceable statement could be rebound by it; abstain rather than
        # guess.
        return FounderDataflowResolution("unsupported", None, None, (), None)
    if len(states) > 1:
        return FounderDataflowResolution("ambiguous", None, None, (), None)
    if not classifications:
        return FounderDataflowResolution("none", None, None, (), None)
    orientation = states[0]
    spans = tuple(
        _ast_node_evidence_span(item_document, item.node) for item_document, item in classifications
    )
    return FounderDataflowResolution(
        "unique",
        orientation,
        repaired_operand if orientation == _REPAIRED else direct_operand,
        spans,
        classifications[0][0].path,
    )


def _imports_case_module(tree: ast.Module, other_stems: set[str]) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in other_stems for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in other_stems:
                return True
    return False


def _python_parser_supported(
    document: InspectionDocument, parser_id: str, parser_version: str
) -> bool:
    if document.parser_result_payload is None:
        return False
    value = json.loads(document.parser_result_payload)
    return (
        isinstance(value, dict)
        and value.get("parser_id") == parser_id
        and value.get("parser_version") == parser_version
        and value.get("state") == "parsed"
    )


# ---------------------------------------------------------------------------
# The per-document trace engine.


def _document_orientations(tree: ast.Module) -> dict[str, Any]:
    """Trace report-reaching emission comparisons across module and function scopes."""

    try:
        return _document_orientations_inner(tree)
    except (RecursionError, MemoryError, OverflowError):
        # A source too deep or too large for the analysis abstains; it never
        # crashes the inspection.
        return {"classifications": [], "unsupported": True}


def _document_orientations_inner(tree: ast.Module) -> dict[str, Any]:
    if any(isinstance(node, ast.NamedExpr) for node in ast.walk(tree)):
        # A walrus binds a name from inside an arbitrary expression. The
        # environment cannot follow that, and tying the check to assignment
        # handling is how ``print(rows := panel)`` escaped in v2.0.1, so the
        # scan is over every statement's complete subtree.
        return {"classifications": [], "unsupported": True}
    if _module_bans(tree):
        return {"classifications": [], "unsupported": True}

    model = _module_model(tree)
    ctx = _TraceContext(
        model=model,
        accumulated=set(model.accumulated),
        reaching=set(model.reaching),
    )
    classifications: list[_Classification] = []

    module_env: dict[str, _Value] = {}
    module_aliases = _Aliases()
    _scan_scope(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        module_env,
        module_aliases,
        ctx,
        classifications,
        returns_reach=False,
        dead=False,
    )
    for function in model.functions.values():
        # Function bodies are scanned with parameters masked, so a module
        # global can never stand in for an unbound parameter.
        env: dict[str, _Value] = dict(module_env)
        aliases = module_aliases.copy()
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ):
            aliases.detach(parameter.arg)
            env[parameter.arg] = _OPAQUE
        _scan_scope(
            function.body,
            env,
            aliases,
            ctx,
            classifications,
            returns_reach=function.name in model.reachable_functions,
            dead=function.name in model.dead_functions,
        )

    unsupported = (
        ctx.unresolved
        or _iterator_reconsumed(tree, ctx)
        or _whitelist_violation(tree, ctx)
        or _tagged_name_escape(tree, ctx)
        or _emission_scan_violation(tree, ctx)
    )
    if unsupported:
        return {"classifications": [], "unsupported": True}
    return {
        "classifications": _resolving_classifications(classifications),
        "unsupported": False,
    }


def _module_bans(tree: ast.Module) -> bool:
    """Module-wide bans that need no trace context.

    Each closes a demonstrated wrong-answer family: reflection names reach
    and mutate tagged state without naming it; a binding that shadows any
    builtin silently changes what the recode vocabulary means; an annotation
    is an arbitrary expression executed at definition time; an import outside
    the allowlisted stdlib modules executes unmodelled code on import, and a
    relative import resolves inside a package this trace cannot see.
    """

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in _BANNED_NAMES:
            return True
        if isinstance(node, ast.Attribute) and node.attr in _BANNED_NAMES:
            return True
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.returns is not None:
                return True
            all_args = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
                *([node.args.vararg] if node.args.vararg else []),
                *([node.args.kwarg] if node.args.kwarg else []),
            ]
            if any(item.annotation is not None for item in all_args):
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in _ALLOWED_IMPORT_MODULES:
                    return True
        if isinstance(node, ast.ImportFrom):
            if node.level:
                return True
            root = (node.module or "").split(".")[0]
            if root not in _ALLOWED_IMPORT_MODULES:
                return True
            if any(alias.name == "*" for alias in node.names):
                # A star import binds names this trace never sees.
                return True
        for name in _binding_names(node):
            if name in _BUILTIN_NAMES:
                return True
    return False


def _binding_names(node: ast.AST) -> set[str]:
    """Every name a node binds, for the builtin-shadowing ban."""

    names: set[str] = set()
    if isinstance(node, ast.Assign):
        for target in node.targets:
            names |= _target_names(target)
    elif isinstance(node, ast.AugAssign | ast.AnnAssign | ast.For | ast.AsyncFor):
        names |= _target_names(node.target)
    elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        names.add(node.name)
        names |= _parameter_names(node)  # type: ignore[arg-type]
    elif isinstance(node, ast.Lambda):
        names |= _parameter_names(node)  # type: ignore[arg-type]
    elif isinstance(node, ast.comprehension):
        names |= _target_names(node.target)
    elif isinstance(node, ast.withitem) and node.optional_vars is not None:
        names |= _target_names(node.optional_vars)
    elif isinstance(node, ast.Import | ast.ImportFrom):
        for alias in node.names:
            names.add(alias.asname or alias.name.split(".")[0])
    elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        names.add(node.target.id)
    elif isinstance(node, ast.Global | ast.Nonlocal):
        names |= set(node.names)
    return names


def _resolving_classifications(classifications: list[_Classification]) -> list[_Classification]:
    """The readings that decide, or every live reading when they disagree.

    Reachability excludes and never selects: a reading that cannot reach the
    written report never answers on its own, but it still counts against a
    reading that does, unless it sits in a function with no occurrence
    besides its own definition and is therefore provably dead.
    """

    live = [item for item in classifications if not item.dead]
    resolving = [item for item in live if item.reaching]
    if not resolving:
        return []
    if len({item.state for item in live}) > 1:
        return live
    return resolving


def _scan_scope(
    statements: list[ast.stmt],
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    returns_reach: bool,
    dead: bool,
) -> None:
    for statement in _flatten_statements(statements):
        if _apply_recognized_loop(statement, env, aliases, ctx, classifications, dead=dead):
            continue
        reaching = _statement_reaches(statement, ctx, returns_reach=returns_reach)
        for node in _walk_skipping_lambdas(statement):
            if isinstance(node, ast.ListComp | ast.GeneratorExp) and id(node) in ctx.accumulated:
                _classify_comprehension(
                    node, env, ctx, classifications, reaching=reaching, dead=dead
                )
        _apply_assign(statement, env, aliases, ctx)


def _statement_reaches(statement: ast.stmt, ctx: _TraceContext, *, returns_reach: bool) -> bool:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return statement.targets[0].id in ctx.reaching
    if isinstance(statement, ast.Expr) and _write_payloads(
        statement.value, ctx.model.write_call_ids
    ):
        return True
    return returns_reach and isinstance(statement, ast.Return)


def _bind(name: str, value: _Value, env: dict[str, _Value], aliases: _Aliases) -> None:
    aliases.detach(name)
    env[name] = value


def _target_names(target: ast.expr) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _apply_assign(
    statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases, ctx: _TraceContext
) -> None:
    """Update the environment for one assignment.

    Only a single ``Name`` target is modelled. Every other assignment form is
    outside the whitelist and the document is already unsupported by the time
    this runs; the environment still drops the names it cannot follow so no
    stale provenance survives.
    """

    if not isinstance(statement, ast.Assign | ast.AugAssign | ast.AnnAssign):
        return
    simple = (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    )
    if not simple:
        targets: list[ast.expr] = (
            list(statement.targets) if isinstance(statement, ast.Assign) else [statement.target]
        )
        for target in targets:
            for name in _target_names(target):
                _bind(name, _OPAQUE, env, aliases)
        return
    assert isinstance(statement, ast.Assign)
    target = statement.targets[0]
    assert isinstance(target, ast.Name)
    value = _tag(statement.value, env, ctx)
    _bind(target.id, value, env, aliases)
    if isinstance(value, _Rows):
        ctx.tagged_names.add(target.id)
    if isinstance(statement.value, ast.Name) and isinstance(value, _Rows | _EmptyList):
        # An alias of an empty list matters as much as an alias of a row
        # set: two names appending into one runtime list was a demonstrated
        # wrong answer when only row sets were grouped.
        aliases.link(target.id, statement.value.id)
        if isinstance(value, _Rows):
            ctx.tagged_names.update(aliases.group(target.id))


# ---------------------------------------------------------------------------
# Emission comparison recognition.


def _classify_comprehension(
    node: ast.ListComp | ast.GeneratorExp,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    reaching: bool,
    dead: bool,
) -> None:
    if len(node.generators) != 1:
        return
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name):
        return
    if _shadows_loop_var(node.elt, generator.target.id):
        ctx.unresolved = True
        return
    selectors = _selector_comparisons(node.elt)
    source = _tag(generator.iter, env, ctx)
    _classify_helper_selector_call(
        node.elt,
        generator.target.id,
        source,
        env,
        ctx,
        classifications,
        reaching=reaching,
        dead=dead,
    )
    _flag_unrecognized_selectors(node.elt, selectors, generator.target.id, env, ctx)
    if not selectors:
        return
    for compare in selectors:
        _classify_compare(
            compare,
            generator.target.id,
            source,
            env,
            ctx,
            classifications,
            reaching=reaching,
            dead=dead,
        )


def _shadows_loop_var(element: ast.expr, loop_var: str) -> bool:
    """Whether a nested comprehension rebinds the enclosing target name.

    Every comprehension has its own scope in Python 3, so a ``row['col']``
    inside a nested ``for row in panel`` reads the inner panel while this
    trace would classify it against the outer iterable -- a demonstrated
    wrong answer in both directions. Such an element is unreadable.
    """

    for node in ast.walk(element):
        if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp):
            for generator in node.generators:
                for name in ast.walk(generator.target):
                    if isinstance(name, ast.Name) and name.id == loop_var:
                        return True
    return False


def _classify_helper_selector_call(
    element: ast.expr,
    loop_var: str,
    source: _Value,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    reaching: bool,
    dead: bool,
) -> None:
    """Classify ``emit(int(row['call']), int(row['founder']))`` factorings.

    Factoring the emission into a two-parameter helper is the most natural
    way to write this code, and an unreviewed helper hid the real emission
    from both the classifier and the belt (a demonstrated wrong answer). The
    recognized shape is deliberately narrow: the element is exactly one call
    to a local straight-line helper whose whole body returns one canonical
    selector comparing its two parameters; the call's two operand paths then
    classify exactly as an inline comparison would.
    """

    if not isinstance(element, ast.Call):
        return
    if not isinstance(element.func, ast.Name):
        return
    name = element.func.id
    if name not in ctx.functions or name in ctx.opaque_callables:
        return
    if len(element.args) != 2 or element.keywords:
        return
    form = _helper_selector_form(ctx.functions[name])
    if form is None:
        return
    compare, left_param, right_param = form
    parameters = [item.arg for item in ctx.functions[name].args.args]
    left_argument = element.args[parameters.index(left_param)]
    right_argument = element.args[parameters.index(right_param)]
    left = _column_parity(left_argument, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    right = _column_parity(right_argument, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    if left is None or right is None:
        ctx.unresolved = True
        return
    _classify_operand_paths(
        compare,
        element,
        left,
        right,
        source,
        ctx,
        classifications,
        reaching=reaching,
        dead=dead,
    )


def _helper_selector_form(
    function: ast.FunctionDef,
) -> tuple[ast.Compare, str, str] | None:
    """The canonical selector a helper body is, or None.

    Returns the comparison node and the parameter names on its two sides
    when the body is a single return of a canonical selector over exactly
    the helper's two parameters.
    """

    if not _straight_line_helper(function):
        return None
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
        or function.args.defaults
    ):
        return None
    parameters = [item.arg for item in function.args.args]
    if len(parameters) != 2 or len(set(parameters)) != 2:
        return None
    statements = [
        item
        for item in _flatten_statements(function.body)
        if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant))
    ]
    # The whole body must be the one return. A statement before it can
    # rebind a parameter (``expected = 1 - expected``), and reading the
    # comparison as if the caller's argument arrived unchanged was a
    # demonstrated wrong answer in both directions.
    if len(statements) != 1 or not isinstance(statements[0], ast.Return):
        return None
    if statements[0].value is None:
        return None
    value = statements[0].value
    if isinstance(value, ast.IfExp) and isinstance(value.test, ast.Compare):
        compare = value.test
        match_branch: ast.expr = value.body
        mismatch_branch: ast.expr = value.orelse
    elif isinstance(value, ast.Subscript) and isinstance(value.value, ast.List | ast.Tuple):
        if not _two_element_numeric_container(value.value):
            return None
        index = value.slice
        if (
            isinstance(index, ast.Call)
            and _call_name(index) == "int"
            and len(index.args) == 1
            and not index.keywords
        ):
            index = index.args[0]
        if not isinstance(index, ast.Compare):
            return None
        compare = index
        match_branch = value.value.elts[1]
        mismatch_branch = value.value.elts[0]
    else:
        return None
    if not _is_canonical_selector(compare, match_branch, mismatch_branch):
        return None
    left, right = compare.left, compare.comparators[0]
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return None
    if {left.id, right.id} != set(parameters):
        return None
    return compare, left.id, right.id


def _flag_unrecognized_selectors(
    element: ast.expr,
    selectors: list[ast.Compare],
    loop_var: str,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> None:
    """Abstain for the document when an emission-like selector is unreadable.

    An accumulation whose element compares two staged columns is an emission
    selector whatever it selects between. If this library cannot read the
    selected values, skipping the accumulation would let a recognized
    comparison elsewhere -- a match count over a different panel, say --
    answer in its place.
    """

    recognized = {id(item) for item in selectors}
    for node in ast.walk(element):
        if not isinstance(node, ast.Compare) or id(node) in recognized:
            continue
        if _is_emission_like_comparison(node, loop_var, env, ctx):
            ctx.unresolved = True
            return


def _is_emission_like_comparison(
    compare: ast.Compare,
    loop_var: str,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> bool:
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq | ast.NotEq):
        return False
    left = _column_parity(compare.left, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    right = _column_parity(compare.comparators[0], loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    if left is None or right is None:
        return False
    return not (left.resolved and right.resolved and left.column == right.column)


def _classify_compare(
    compare: ast.Compare,
    loop_var: str,
    source: _Value,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    reaching: bool,
    dead: bool,
) -> None:
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq | ast.NotEq):
        return
    left = _column_parity(compare.left, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    right = _column_parity(compare.comparators[0], loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    if left is None or right is None:
        # At least one side is not a column of the iterated rows at all, so
        # this is a filter or a literal test, not an emission comparison.
        return
    _classify_operand_paths(
        compare,
        compare,
        left,
        right,
        source,
        ctx,
        classifications,
        reaching=reaching,
        dead=dead,
    )


def _classify_operand_paths(
    compare: ast.Compare,
    span_node: ast.AST,
    left: _Path,
    right: _Path,
    source: _Value,
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    reaching: bool,
    dead: bool,
) -> None:
    """Classify one emission comparison from its two resolved operand paths."""

    if not left.resolved or not right.resolved:
        ctx.unresolved = True
        return
    if not isinstance(source, _Rows):
        # The comparison reads columns, but the row set they came from is not
        # a traceable staged read; the orientation is unknowable here.
        ctx.unresolved = True
        return
    left_source = _rows_column(source, str(left.column))
    right_source = _rows_column(source, str(right.column))
    if left_source is None or right_source is None:
        ctx.unresolved = True
        return
    left_effective = left.numeric if left.numeric is not None else left_source[2]
    right_effective = right.numeric if right.numeric is not None else right_source[2]
    if left_effective != right_effective:
        # The effective runtime type joins the read-site cast with the
        # provenance the rebuild stored: a column rebuilt as a number
        # compared against a raw string column is constantly unequal at
        # runtime, so whatever this selector selects, it is not the emission
        # comparison it appears to be. Both-string and both-numeric
        # comparisons are real.
        ctx.unresolved = True
        return
    if left_source[0] == right_source[0]:
        # A column compared with itself carries no cross-panel orientation.
        ctx.recognized_compares.add(id(compare))
        return
    parity = (left.parity + left_source[1] + right.parity + right_source[1]) % 2
    ctx.recognized_compares.add(id(compare))
    classifications.append(
        _Classification(
            node=span_node,
            state=_REPAIRED if parity else _DIRECT,
            reaching=reaching,
            dead=dead,
        )
    )


def _selector_comparisons(element: ast.expr) -> list[ast.Compare]:
    """Canonical selectors: comparisons choosing between two proven probabilities.

    A selector classifies only in its canonical form: an equality comparison
    whose match branch carries a strictly larger constant probability than
    its mismatch branch. Everything else -- an inequality operator, swapped
    branches, or branch values hidden behind names -- computes a value that
    is extensionally a complement of a canonical selector's, and whether
    that complement is an orientation repair or a differently parameterized
    emission matrix is not statically decidable. Non-canonical selectors are
    therefore never recognized; an emission-like comparison inside one falls
    through to the module-wide belt and the document abstains.
    """

    found: list[ast.Compare] = []
    for node in ast.walk(element):
        if isinstance(node, ast.IfExp) and isinstance(node.test, ast.Compare):
            if not _numeric_like(node.body) or not _numeric_like(node.orelse):
                continue
            if _is_canonical_selector(node.test, node.body, node.orelse):
                found.append(node.test)
        elif isinstance(node, ast.Subscript):
            if not _two_element_numeric_container(node.value):
                continue
            index = node.slice
            if (
                isinstance(index, ast.Call)
                and _call_name(index) == "int"
                and len(index.args) == 1
                and not index.keywords
            ):
                index = index.args[0]
            if not isinstance(index, ast.Compare):
                continue
            assert isinstance(node.value, ast.List | ast.Tuple)
            # A true comparison indexes element one, so element one is the
            # match branch of the container form.
            if _is_canonical_selector(index, node.value.elts[1], node.value.elts[0]):
                found.append(index)
    return found


def _is_canonical_selector(
    compare: ast.Compare, match_branch: ast.expr, mismatch_branch: ast.expr
) -> bool:
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq):
        return False
    match_value = _selector_constant(match_branch)
    mismatch_value = _selector_constant(mismatch_branch)
    if match_value is None or mismatch_value is None:
        return False
    if match_value <= 0 or mismatch_value < 0:
        # Probabilities are positive (a count's mismatch branch may be
        # exactly zero). A negative pair orders differently in linear and
        # log space, so its polarity is not decidable here.
        return False
    return match_value > mismatch_value


def _selector_constant(node: ast.expr) -> float | None:
    """The provable constant value of a selector branch, or None.

    Only simple literal forms qualify: a numeric literal, its negation, or a
    one- or two-argument Fraction/Decimal of literals. Arithmetic is
    deliberately excluded -- folding it in binary floats mis-orders Decimal
    expressions against their runtime values (a demonstrated wrong answer),
    and no exact folder agrees with runtime for every constructor mix.
    Names are not constants: an unprovable value leaves the branch order
    unprovable and the selector non-canonical.
    """

    if isinstance(node, ast.Constant):
        if isinstance(node.value, int | float) and not isinstance(node.value, bool):
            if isinstance(node.value, int) and abs(node.value) > 10**12:
                # ``float`` of a large enough integer raises OverflowError;
                # no real probability constant is this large.
                return None
            return float(node.value)
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _selector_constant(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.Call) and not node.keywords and node.args:
        name = _call_name(node)
        if name in _EXACT_NUMERIC_CALLS and len(node.args) <= 2:
            values: list[float] = []
            for argument in node.args:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    try:
                        values.append(float(argument.value))
                    except (ValueError, OverflowError):
                        return None
                    continue
                value = _selector_constant(argument)
                if value is None:
                    return None
                values.append(value)
            try:
                return values[0] / values[1] if len(values) == 2 else values[0]
            except (ZeroDivisionError, OverflowError):
                return None
    return None


def _two_element_numeric_container(node: ast.expr) -> bool:
    """A two-element literal of emission probabilities indexed by a boolean."""

    return (
        isinstance(node, ast.List | ast.Tuple)
        and len(node.elts) == 2
        and all(_numeric_like(item) for item in node.elts)
    )


def _numeric_like(node: ast.expr, depth: int = 0) -> bool:
    """A numeric emission probability: a literal, a name, or arithmetic over them.

    ``Fraction(99, 100)`` and ``Decimal("0.99")`` are ordinary stdlib ways of
    writing an emission probability, so they read as numeric here; leaving
    them out made a legitimate emission selector invisible.
    """

    if depth >= _MAX_EXPRESSION_DEPTH:
        return False
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int | float) and not isinstance(node.value, bool)
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.UnaryOp):
        return _numeric_like(node.operand, depth + 1)
    if isinstance(node, ast.BinOp):
        return _numeric_like(node.left, depth + 1) and _numeric_like(node.right, depth + 1)
    if isinstance(node, ast.Call) and not node.keywords:
        name = _call_name(node)
        if name in _EXACT_NUMERIC_CALLS:
            return (
                bool(node.args)
                and len(node.args) <= 2
                and all(_numeric_argument(item, depth + 1) for item in node.args)
            )
        if name in {"float", "int"}:
            return len(node.args) == 1 and _numeric_like(node.args[0], depth + 1)
    return False


def _numeric_argument(node: ast.expr, depth: int) -> bool:
    """A numeric constructor argument, including the decimal string form."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            float(node.value)
        except ValueError:
            return False
        return True
    return _numeric_like(node, depth)


def _rows_column(rows: _Rows, column: str) -> tuple[str, int, bool] | None:
    """The staged column, recode parity, and stored numeric proof for one column.

    A column read straight from the CSV is a string, so the default-identity
    fallback carries no numeric proof.
    """

    for key, value in rows.overrides:
        if key == column:
            return value
    return (column, 0, False) if rows.default_identity else None


# ---------------------------------------------------------------------------
# Per-column parity of one expression.


def _column_parity(
    expression: ast.expr,
    *,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """The staged column an expression reads and the parity of its recoding.

    Returns ``None`` when the expression has no row-column origin at all,
    the unresolved marker when it touches one through an operation this
    library does not recognize, and a resolved path otherwise.

    The recursion carries an explicit depth bound: a long enough composed
    expression would otherwise exhaust the interpreter stack, and abstaining
    beyond the bound is the only sound answer.
    """

    if ctx.expression_depth >= _MAX_EXPRESSION_DEPTH:
        return _UNRESOLVED
    ctx.expression_depth += 1
    try:
        return _column_parity_inner(
            expression, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
        )
    finally:
        ctx.expression_depth -= 1


def _column_parity_inner(
    expression: ast.expr,
    *,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    def _unknown() -> _Path | None:
        return _UNRESOLVED if _touches_rows(expression, loop_var, carriers) else None

    if isinstance(expression, ast.Name):
        return carriers.get(expression.id)

    if isinstance(expression, ast.Subscript):
        if (
            loop_var is not None
            and isinstance(expression.value, ast.Name)
            and expression.value.id == loop_var
            and isinstance(expression.slice, ast.Constant)
            and isinstance(expression.slice.value, str)
        ):
            return _Path(expression.slice.value, 0)
        table = _two_element_table(expression.value)
        if table is not None:
            base = _column_parity(
                expression.slice, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
            )
            return _table_shift(table, base)
        return _unknown()

    if isinstance(expression, ast.Call):
        return _call_parity(expression, loop_var, carriers, env, ctx) or _unknown()

    if isinstance(expression, ast.BinOp):
        if isinstance(expression.op, ast.Sub) and _is_one(expression.left):
            return _shift(
                _column_parity(
                    expression.right, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                ),
                1,
            )
        if isinstance(expression.op, ast.BitXor):
            for one, other in (
                (expression.right, expression.left),
                (expression.left, expression.right),
            ):
                if _is_one(one):
                    return _shift(
                        _column_parity(
                            other, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                        ),
                        1,
                    )
        return _unknown()

    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
        shifted = _shift(
            _column_parity(
                expression.operand, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
            ),
            1,
        )
        if shifted is None or not shifted.resolved:
            return shifted
        # ``not`` produces a bool; only a numeric cast turns it back into a
        # digit. A syntactic str(not x) test missed the helper-wrapped form.
        return _Path(shifted.column, shifted.parity, numeric=shifted.numeric, boolean=True)

    if isinstance(expression, ast.IfExp):
        return _ifexp_parity(expression, loop_var, carriers, env, ctx) or _unknown()

    return _unknown()


def _call_parity(
    call: ast.Call,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    name = _call_name(call)
    if name in ctx.opaque_callables:
        # The name is rebound or escapes call position somewhere in the
        # module, so which body runs here is a runtime question.
        return None
    if (
        isinstance(call.func, ast.Attribute)
        and call.func.attr in _STRIP_METHODS
        and not call.args
        and not call.keywords
    ):
        base = _column_parity(
            call.func.value, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
        )
        if base is None or not base.resolved:
            return base
        # ``strip`` exists on strings and returns one.
        return _Path(base.column, base.parity, numeric=False)
    if (
        name in _IDENTITY_CASTS
        and len(call.args) == 1
        and not call.keywords
        and _is_builtin_name(name, ctx)
    ):
        base = _column_parity(call.args[0], loop_var=loop_var, carriers=carriers, env=env, ctx=ctx)
        if base is None or not base.resolved:
            return base
        if name == "str":
            if base.boolean:
                # ``str`` of a bool is 'True' or 'False', which no
                # digit-string column ever equals, however the bool was
                # produced; the comparison is degenerate.
                return _UNRESOLVED
            # ``str`` keeps the value but drops the numeric proof: ``not``
            # and arithmetic over the result no longer mean inversion.
            return _Path(base.column, base.parity, numeric=False)
        # ``int``/``float`` of a bool is an ordinary digit again.
        return _Path(base.column, base.parity, numeric=True)
    if name == "abs" and len(call.args) == 1 and not call.keywords and _is_builtin_name("abs", ctx):
        inner = call.args[0]
        if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Sub):
            for one, other in ((inner.right, inner.left), (inner.left, inner.right)):
                if _is_one(one):
                    return _shift(
                        _column_parity(
                            other, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                        ),
                        1,
                    )
        return None
    if name in ctx.functions:
        return _helper_parity(ctx.functions[name], call, loop_var, carriers, env, ctx)
    return None


def _is_builtin_name(name: str, ctx: _TraceContext) -> bool:
    """Whether a builtin name still means the builtin in this module."""

    return name not in ctx.functions and name not in ctx.model.imports


def _helper_parity(
    function: ast.FunctionDef,
    call: ast.Call,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """Parity of a straight-line helper applied to exactly one column value."""

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _UNRESOLVED
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
    ):
        return _UNRESOLVED
    parameters = [item.arg for item in function.args.args]
    bound: dict[str, ast.expr] = {}
    if len(call.args) > len(parameters):
        return _UNRESOLVED
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = argument
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return _UNRESOLVED
        bound[keyword.arg] = keyword.value
    if set(bound) != set(parameters):
        return _UNRESOLVED
    carried: dict[str, _Path] = {}
    for parameter, argument in bound.items():
        path = _column_parity(argument, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx)
        if path is None:
            continue
        if not path.resolved:
            return _UNRESOLVED
        carried[parameter] = path
    if len(carried) != 1:
        # A helper carrying no column, or two of them, is not a recode of one
        # panel value; abstain rather than pick a side.
        return None if not carried else _UNRESOLVED
    if not _straight_line_helper(function):
        return _UNRESOLVED
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        local = dict(carried)
        statements = _flatten_statements(function.body)
        for index, statement in enumerate(statements):
            if isinstance(statement, ast.Return):
                # Statements after the first return are dead code the value
                # never sees, and a body that keeps going is not the
                # straight line this analysis assumes.
                if statement.value is None or index != len(statements) - 1:
                    return _UNRESOLVED
                path = _column_parity(
                    statement.value, loop_var=None, carriers=local, env=env, ctx=ctx
                )
                if path is None or not path.resolved:
                    return _UNRESOLVED
                return _Path(
                    str(path.column), path.parity % 2, numeric=path.numeric, boolean=path.boolean
                )
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                path = _column_parity(
                    statement.value, loop_var=None, carriers=local, env=env, ctx=ctx
                )
                if path is not None:
                    local[statement.targets[0].id] = path
                else:
                    local.pop(statement.targets[0].id, None)
                continue
            if isinstance(statement, ast.Pass):
                continue
            return _UNRESOLVED
        return _UNRESOLVED
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


def _straight_line_helper(function: ast.FunctionDef) -> bool:
    """A helper body of assignments and one closing return, with no side effects."""

    for node in ast.walk(function):
        if isinstance(node, ast.NamedExpr):
            return False
    for statement in _flatten_statements(function.body):
        if isinstance(statement, ast.Expr) and not isinstance(statement.value, ast.Constant):
            # A bare expression statement exists for its side effect; only a
            # docstring is inert.
            return False
        if not isinstance(statement, ast.Assign | ast.Return | ast.Pass | ast.Expr):
            return False
    return True


def _ifexp_parity(
    expression: ast.IfExp,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """``1 if x == 0 else 0`` and its three mirrored forms."""

    test = expression.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return None
    if not isinstance(test.ops[0], ast.Eq | ast.NotEq):
        return None
    body = _binary_constant(expression.body)
    orelse = _binary_constant(expression.orelse)
    if body is None or orelse is None or body == orelse:
        return None
    for constant_side, value_side in (
        (test.left, test.comparators[0]),
        (test.comparators[0], test.left),
    ):
        constant = _binary_constant(constant_side)
        if constant is None:
            continue
        base = _column_parity(value_side, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx)
        if base is None:
            return None
        matched, unmatched = (body, orelse) if isinstance(test.ops[0], ast.Eq) else (orelse, body)
        table = [0, 0]
        table[constant] = matched
        table[1 - constant] = unmatched
        return _table_shift((table[0], table[1]), base)
    return None


def _two_element_table(node: ast.expr) -> tuple[int, int] | None:
    """A literal mapping of the domain {0, 1} onto {0, 1}."""

    if isinstance(node, ast.List | ast.Tuple) and len(node.elts) == 2:
        values = [_binary_constant(item) for item in node.elts]
        if values[0] is not None and values[1] is not None:
            return (values[0], values[1])
        return None
    if isinstance(node, ast.Dict) and len(node.keys) == 2:
        entries: dict[int, int] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                return None
            index = _binary_constant(key)
            mapped = _binary_constant(value)
            if index is None or mapped is None:
                return None
            entries[index] = mapped
        if set(entries) == {0, 1}:
            return (entries[0], entries[1])
    return None


def _table_shift(table: tuple[int, int], base: _Path | None) -> _Path | None:
    if base is None:
        return None
    if not base.resolved:
        return base
    if not base.numeric:
        # Indexing a table with a raw string is a crash or a key error at
        # runtime, never a recode; without numeric proof the path abstains.
        return _UNRESOLVED
    if table == (0, 1):
        return _Path(base.column, base.parity, numeric=True)
    if table == (1, 0):
        return _Path(base.column, base.parity + 1, numeric=True)
    return _UNRESOLVED


def _binary_constant(node: ast.expr) -> int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value in {0, 1}
    ):
        return int(node.value)
    return None


def _is_one(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
        and node.value == 1
    )


def _shift(base: _Path | None, amount: int) -> _Path | None:
    """Add inverting steps to a path; an inversion demands numeric provenance.

    Arithmetic shifts (1-x, x^1, abs(x-1)) produce ints, so any boolean
    taint clears; only ``not`` re-taints at its own call site.
    """

    if base is None or not base.resolved:
        return base
    if amount % 2 and not base.numeric:
        return _UNRESOLVED
    return _Path(base.column, base.parity + amount, numeric=True)


def _touches_rows(expression: ast.expr, loop_var: str | None, carriers: dict[str, _Path]) -> bool:
    for node in ast.walk(expression):
        if (
            loop_var is not None
            and isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == loop_var
        ):
            return True
        if isinstance(node, ast.Name) and node.id in carriers:
            return True
    return False


# ---------------------------------------------------------------------------
# Row-set tagging.


def _tag(node: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if ctx.expression_depth >= _MAX_EXPRESSION_DEPTH:
        return _OPAQUE
    ctx.expression_depth += 1
    try:
        return _tag_inner(node, env, ctx)
    finally:
        ctx.expression_depth -= 1


def _tag_inner(node: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if isinstance(node, ast.Name):
        return env.get(node.id, _OPAQUE)
    if isinstance(node, ast.Constant):
        return _Scalar() if isinstance(node.value, int | float) else _OPAQUE
    if isinstance(node, ast.List | ast.Tuple) and not node.elts:
        return _EMPTY_LIST
    if isinstance(node, ast.Call):
        return _tag_call(node, env, ctx)
    if isinstance(node, ast.ListComp | ast.GeneratorExp):
        return _tag_comprehension(node, env, ctx)
    if isinstance(node, ast.BinOp | ast.UnaryOp | ast.Compare):
        return _Scalar()
    return _OPAQUE


def _tag_call(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    name = _call_name(node)
    if name in ctx.opaque_callables:
        return _OPAQUE
    if isinstance(node.func, ast.Name) and node.func.id in env:
        # The callable name is bound to a value this trace is following, so
        # the built-in vocabulary below does not describe it.
        return _OPAQUE
    if name in ctx.functions:
        # A project definition shadows the reader vocabulary; its body, not
        # its name, says what it returns.
        return _bound_return_value(ctx.functions[name], node, env, ctx)
    if _is_reader_call(node, ctx.model):
        return _Rows(iterator=True)
    if (
        name == "list"
        and len(node.args) == 1
        and not node.keywords
        and _is_builtin_name("list", ctx)
    ):
        inner = _tag(node.args[0], env, ctx)
        if isinstance(inner, _Rows):
            return _Rows(inner.overrides, inner.default_identity, iterator=False)
        return _OPAQUE
    if name in _ACCUMULATOR_CALLS or name == "len":
        return _Scalar()
    if name in _IDENTITY_CASTS and len(node.args) == 1 and not node.keywords:
        inner = _tag(node.args[0], env, ctx)
        return inner if isinstance(inner, _Scalar) else _OPAQUE
    return _OPAQUE


def _tag_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, _Value], ctx: _TraceContext
) -> _Value:
    if len(node.generators) != 1:
        return _OPAQUE
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name):
        return _OPAQUE
    source = _tag(generator.iter, env, ctx)
    if not isinstance(source, _Rows):
        return _OPAQUE
    return _row_element_value(node.elt, generator.target.id, source, env, ctx)


def _row_element_value(
    element: ast.expr,
    loop_var: str,
    source: _Rows,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """The row set a per-row element expression builds, or opaque.

    Dict construction is order-sensitive: ``{"founder": ..., **row}`` keeps
    the spread's value for ``founder`` and ``{**row, "founder": ...}`` keeps
    the explicit one. Entries are therefore applied strictly left to right,
    and a later spread overwrites an earlier explicit key with whatever that
    spread carries -- opaque when the spread's own contents do not say. An
    entry that evaluates a call outside the recode vocabulary is outside the
    whitelist entirely, so no evaluation-order side effect can hide here.
    """

    if isinstance(element, ast.Name) and element.id == loop_var:
        return _Rows(source.overrides, source.default_identity, iterator=False)
    if not isinstance(element, ast.Dict):
        return _OPAQUE
    built: dict[str, tuple[str, int, bool] | None] = {}
    default_identity = False
    for key, value in zip(element.keys, element.values, strict=True):
        if key is None:
            if not (isinstance(value, ast.Name) and value.id == loop_var):
                return _OPAQUE
            for existing in list(built):
                # The spread overwrites an earlier explicit key only if the
                # source rows actually carry that column, and the staged
                # CSV's columns are runtime data this trace cannot see. An
                # explicit override is trusted; the default-identity guess
                # is not -- ``{'founder': repair, **row}`` over a CSV with
                # no ``founder`` column keeps the repair at runtime, and
                # modelling it as overwritten was a demonstrated wrong
                # answer.
                explicit = dict(source.overrides)
                built[existing] = explicit.get(existing, None)
            built.update(dict(source.overrides))
            default_identity = source.default_identity
            continue
        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
            return _OPAQUE
        path = _column_parity(value, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
        if path is None or not path.resolved:
            built[key.value] = None
            continue
        resolved = _rows_column(source, str(path.column))
        if resolved is None:
            built[key.value] = None
            continue
        # The stored numeric proof is what the rebuilt column actually
        # holds at runtime: the read path's cast, or the proof the source
        # column already carried. Dropping it here let a rebuilt integer
        # column read as a string and defeat the mixed-type guard (a
        # demonstrated wrong answer).
        stored_numeric = path.numeric if path.numeric is not None else resolved[2]
        built[key.value] = (
            resolved[0],
            (resolved[1] + path.parity) % 2,
            stored_numeric,
        )
    return _Rows(
        tuple(sorted(built.items())),
        default_identity=default_identity,
        iterator=False,
    )


def _bind_call(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> dict[str, _Value] | None:
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
    ):
        return None
    parameters = [item.arg for item in function.args.args]
    if len(call.args) > len(parameters):
        return None
    bound: dict[str, _Value] = {}
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = _tag(argument, env, ctx)
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return None
        bound[keyword.arg] = _tag(keyword.value, env, ctx)
    for parameter in parameters[len(parameters) - len(function.args.defaults) :]:
        bound.setdefault(parameter, _OPAQUE)
    if set(bound) != set(parameters):
        return None
    return bound


def _bound_return_value(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """The return value of a callee with its parameters bound.

    Statements are processed in order and the first top-level return decides;
    a body that continues past its return is not the straight line this
    analysis assumes and reads as opaque.
    """

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _OPAQUE
    if not _straight_line_helper(function):
        return _OPAQUE
    callee_env = _bind_call(function, call, env, ctx)
    if callee_env is None:
        return _OPAQUE
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        callee_aliases = _Aliases()
        statements = _flatten_statements(function.body)
        for index, statement in enumerate(statements):
            if isinstance(statement, ast.Return):
                if statement.value is None or index != len(statements) - 1:
                    return _OPAQUE
                return _tag(statement.value, callee_env, ctx)
            _apply_assign(statement, callee_env, callee_aliases, ctx)
        return _OPAQUE
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


# ---------------------------------------------------------------------------
# Recognized loops.


def _apply_recognized_loop(
    statement: ast.stmt,
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    dead: bool,
) -> bool:
    if not isinstance(statement, ast.For) or statement.orelse:
        return False
    if not isinstance(statement.target, ast.Name):
        return False
    source = _tag(statement.iter, env, ctx)
    if not isinstance(source, _Rows):
        return False
    if _apply_row_building_loop(statement, source, env, aliases, ctx):
        ctx.recognized_loops.add(id(statement))
        return True
    if _apply_accumulation_loop(statement, source, env, ctx, classifications, dead=dead):
        ctx.recognized_loops.add(id(statement))
        return True
    return False


def _apply_row_building_loop(
    loop: ast.For,
    source: _Rows,
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
) -> bool:
    """``out = []`` then ``for row in rows: out.append(<row expression>)``."""

    assert isinstance(loop.target, ast.Name)
    built: dict[str, set[_Value]] = {}
    for statement in loop.body:
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Attribute)
            and statement.value.func.attr == "append"
            and isinstance(statement.value.func.value, ast.Name)
            and len(statement.value.args) == 1
            and not statement.value.keywords
        ):
            return False
        name = statement.value.func.value.id
        if not isinstance(env.get(name), _EmptyList):
            return False
        built.setdefault(name, set()).add(
            _row_element_value(statement.value.args[0], loop.target.id, source, env, ctx)
        )
    if not built:
        return False
    for name in built:
        if aliases.group(name) != {name}:
            # Two receiver names in one alias group are one runtime list;
            # assigning them separate provenances was a demonstrated wrong
            # answer. An aliased receiver is outside this recognized shape.
            return False
    for name, values in built.items():
        if len(values) != 1:
            return False
        value = next(iter(values))
        if not isinstance(value, _Rows):
            return False
        env[name] = value
        ctx.tagged_names.add(name)
    return True


def _apply_accumulation_loop(
    loop: ast.For,
    source: _Rows,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    dead: bool,
) -> bool:
    """``for row in rows: total = total * <selector>`` and its augmented form."""

    assert isinstance(loop.target, ast.Name)
    targets: set[str] = set()
    payloads: list[ast.expr] = []
    for statement in loop.body:
        if (
            isinstance(statement, ast.AugAssign)
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.op, ast.Mult | ast.Add)
        ):
            targets.add(statement.target.id)
            payloads.append(statement.value)
            continue
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.BinOp)
            and isinstance(statement.value.op, ast.Mult | ast.Add)
        ):
            name = statement.targets[0].id
            operands = (statement.value.left, statement.value.right)
            if any(isinstance(item, ast.Name) and item.id == name for item in operands):
                targets.add(name)
                payloads.extend(
                    item
                    for item in operands
                    if not (isinstance(item, ast.Name) and item.id == name)
                )
                continue
        return False
    if not targets or any(not isinstance(env.get(name), _Scalar) for name in targets):
        return False
    reaching = bool(targets & ctx.reaching)
    for payload in payloads:
        if _shadows_loop_var(payload, loop.target.id):
            ctx.unresolved = True
            return True
        selectors = _selector_comparisons(payload)
        _classify_helper_selector_call(
            payload,
            loop.target.id,
            source,
            env,
            ctx,
            classifications,
            reaching=reaching,
            dead=dead,
        )
        _flag_unrecognized_selectors(payload, selectors, loop.target.id, env, ctx)
        for compare in selectors:
            _classify_compare(
                compare,
                loop.target.id,
                source,
                env,
                ctx,
                classifications,
                reaching=reaching,
                dead=dead,
            )
    for name in targets:
        env[name] = _Scalar()
    return True


# ---------------------------------------------------------------------------
# The module model: imports, callables, reachability.


def _module_model(tree: ast.Module) -> _ModuleModel:
    imports = _import_table(tree)
    functions: dict[str, ast.FunctionDef] = {}
    definitions: Counter[str] = Counter()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
            definitions[node.name] += 1
    escaping, occurrences = _name_occurrences(tree)
    opaque = {name for name in functions if definitions[name] > 1}
    opaque |= escaping & set(functions)
    opaque |= {name for name, function in functions.items() if _calls_a_parameter(function)}
    called = _called_function_names(tree, functions)
    reachable = frozenset(called | (escaping & set(functions)))
    dead = frozenset(name for name in functions if occurrences[name] == 0)
    write_call_ids = _report_write_call_ids(tree)
    reaching = _report_reaching_names(tree, functions, write_call_ids, reachable)
    return _ModuleModel(
        imports=imports,
        functions=functions,
        opaque_callables=frozenset(opaque),
        reachable_functions=reachable,
        dead_functions=dead,
        write_call_ids=write_call_ids,
        reaching=frozenset(reaching),
        accumulated=frozenset(_accumulated_comprehension_ids(tree)),
    )


def _import_table(tree: ast.Module) -> dict[str, str]:
    """Local name to dotted origin for every import in the module."""

    table: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    table[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    table[root] = root
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                origin = f"{module}.{alias.name}" if module else alias.name
                table[alias.asname or alias.name] = origin
    return table


def _name_occurrences(tree: ast.Module) -> tuple[set[str], Counter[str]]:
    """Names used outside call position, and how often every name occurs.

    The ``def`` itself contributes no ``Name`` node, so a count of zero means
    a function nothing in the module ever mentions.
    """

    call_functions = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    escaping: set[str] = set()
    occurrences: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            occurrences[node.id] += 1
            if id(node) not in call_functions:
                escaping.add(node.id)
    return escaping, occurrences


def _parameter_names(function: ast.FunctionDef) -> set[str]:
    names = {
        item.arg
        for item in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if function.args.vararg is not None:
        names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.add(function.args.kwarg.arg)
    return names


def _calls_a_parameter(function: ast.FunctionDef) -> bool:
    """Whether the body calls one of its own parameters.

    Parameters mask every global, so which body such a call runs is decided
    by the caller's argument, not by any definition this trace can read.
    """

    parameters = _parameter_names(function)
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in parameters:
                return True
    return False


def _function_local_names(function: ast.FunctionDef) -> set[str]:
    """Names a function body binds for itself.

    Comprehension targets and loop targets are deliberately absent: a
    comprehension target has its own scope in Python 3, so ``[0 for rows in
    trigger]`` does not make ``rows`` local -- treating it as local masked
    the tagged-global ban and was a demonstrated wrong answer. Reusing a
    tagged name as a loop or comprehension target now reads as a reference
    to the tagged global and abstains, which is over-strict but sound.
    """

    names = _parameter_names(function)
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                names |= _target_names(target)
        elif isinstance(node, ast.AugAssign | ast.AnnAssign):
            names |= _target_names(node.target)
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            names |= _target_names(node.optional_vars)
        elif isinstance(node, ast.Lambda):
            names |= _parameter_names(node)  # type: ignore[arg-type]
        elif isinstance(node, ast.FunctionDef) and node is not function:
            names.add(node.name)
    return names


def _is_reader_call(call: ast.Call, model: _ModuleModel) -> bool:
    """Whether a call provably resolves to a ``csv`` row reader.

    An imported ``reader`` from any other module is an ordinary opaque
    callable; only the import table can promote a name into this vocabulary.
    """

    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return (
            func.value.id not in model.functions
            and model.imports.get(func.value.id) == "csv"
            and func.attr in _READER_ATTRIBUTES
        )
    if isinstance(func, ast.Name):
        return func.id not in model.functions and model.imports.get(func.id) in _READER_ORIGINS
    return False


# ---------------------------------------------------------------------------
# The whitelist.


def _iterator_reconsumed(tree: ast.Module, ctx: _TraceContext) -> bool:
    """Whether one reader iterator is used as an iterable more than once.

    ``csv.DictReader`` not materialized by ``list`` is exhausted by its
    first pass, and ``alias = reader`` names the same exhausted iterator
    (the alias-blind version of this guard was a demonstrated wrong
    answer). Uses are counted per alias group, one group per reader
    binding; two distinct readers each consumed once stay supported.
    """

    group_of: dict[str, int] = {}
    next_group = 0
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            continue
        target = node.targets[0].id
        if isinstance(node.value, ast.Call) and _is_reader_call(node.value, ctx.model):
            group_of[target] = next_group
            next_group += 1
        elif isinstance(node.value, ast.Name) and node.value.id in group_of:
            group_of[target] = group_of[node.value.id]
    if not group_of:
        return False
    uses: Counter[int] = Counter()
    for node in ast.walk(tree):
        iterable: ast.expr | None = None
        if isinstance(node, ast.comprehension):
            iterable = node.iter
        elif isinstance(node, ast.For):
            iterable = node.iter
        if isinstance(iterable, ast.Name) and iterable.id in group_of:
            uses[group_of[iterable.id]] += 1
    return any(count > 1 for count in uses.values())


def _whitelist_violation(tree: ast.Module, ctx: _TraceContext) -> bool:
    """Whether any statement or expression sits outside the modelled forms."""

    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef):
            if _function_violation(statement, ctx):
                return True
            continue
        if _statement_violation(statement, ctx, scope="module"):
            return True
    return False


def _function_violation(function: ast.FunctionDef, ctx: _TraceContext) -> bool:
    if function.decorator_list:
        return True
    # Default expressions are evaluated once at definition time and are not
    # part of the modelled call binding, so only constants are admitted.
    defaults = [*function.args.defaults, *[item for item in function.args.kw_defaults if item]]
    if any(not isinstance(item, ast.Constant) for item in defaults):
        return True
    tagged = ctx.tagged_names
    locals_ = _function_local_names(function)
    for node in ast.walk(function):
        if isinstance(node, ast.Name) and node.id in tagged and node.id not in locals_:
            # Closures may not see tagged globals: the panel a body reads is
            # whatever the module bound by the time the call ran.
            return True
    for statement in function.body:
        if _statement_violation(statement, ctx, scope="function"):
            return True
    return False


def _statement_violation(statement: ast.stmt, ctx: _TraceContext, *, scope: str) -> bool:
    if isinstance(statement, ast.Import | ast.ImportFrom):
        return scope != "module"
    if isinstance(statement, ast.Pass):
        return False
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            return True
        return _expression_violation(statement.value, ctx)
    if isinstance(statement, ast.Return):
        if scope != "function":
            return True
        return statement.value is not None and _expression_violation(statement.value, ctx)
    if isinstance(statement, ast.Expr):
        return _expression_statement_violation(statement, ctx)
    if isinstance(statement, ast.With):
        for item in statement.items:
            if not _is_modelled_context(item.context_expr, ctx):
                return True
            if item.optional_vars is not None and not isinstance(item.optional_vars, ast.Name):
                return True
        return any(_statement_violation(inner, ctx, scope=scope) for inner in statement.body)
    if isinstance(statement, ast.If):
        if not _is_main_guard(statement) or statement.orelse:
            return True
        return any(_statement_violation(inner, ctx, scope=scope) for inner in statement.body)
    if isinstance(statement, ast.For):
        if id(statement) not in ctx.recognized_loops:
            return True
        if not isinstance(statement.iter, ast.Name):
            return True
        # A recognized loop shape says nothing about the expressions inside
        # it; ``operator.setitem(row, ...) or 1.0`` in a loop payload was a
        # demonstrated wrong answer. Every expression in the body passes the
        # same whitelist a comprehension element does.
        return _loop_body_violation(statement, ctx)
    # Every other statement type -- match, try, while, class, delete, global,
    # nonlocal, raise, assert, every async form, and nested definitions -- is
    # outside the whitelist whatever names it mentions.
    return True


def _loop_body_violation(loop: ast.For, ctx: _TraceContext) -> bool:
    """The expression whitelist applied inside a recognized loop body."""

    for statement in loop.body:
        if isinstance(statement, ast.Expr):
            # The recognized row-building append; its argument rebuilds a
            # row, so the container-literal discipline applies to it.
            if not isinstance(statement.value, ast.Call) or not statement.value.args:
                return True
            if _expression_violation(statement.value.args[0], ctx, in_literal=True):
                return True
            continue
        if isinstance(statement, ast.AugAssign):
            if _expression_violation(statement.value, ctx):
                return True
            continue
        if isinstance(statement, ast.Assign):
            if _expression_violation(statement.value, ctx):
                return True
            continue
        return True
    return False


def _is_modelled_context(node: ast.expr, ctx: _TraceContext) -> bool:
    """The ``open()``-as pattern, the only context manager this trace models."""

    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id == "open" and _is_builtin_name("open", ctx):
        return True
    return isinstance(node.func, ast.Attribute) and node.func.attr == "open"


def _expression_statement_violation(statement: ast.Expr, ctx: _TraceContext) -> bool:
    value = statement.value
    if isinstance(value, ast.Constant):
        # A docstring is inert.
        return False
    if isinstance(value, ast.Call) and id(value) in ctx.model.write_call_ids:
        # The write's receiver must be readable and its payload inert: a
        # payload is evaluated before writing, so a call inside it runs
        # arbitrary admitted code -- ``write_text(swap_rows())`` was a
        # demonstrated wrong answer. Names, constants, f-strings, and
        # ``str``/``repr`` of names publish values without computing them.
        if not all(_print_argument(item) for item in value.args):
            return True
        if isinstance(value.func, ast.Attribute) and _expression_violation(value.func.value, ctx):
            return True
        return False
    if isinstance(value, ast.Call) and _is_print_read(value, ctx):
        return False
    if (
        isinstance(value, ast.Call)
        and _call_name(value) in ctx.model.functions
        and _call_name(value) not in ctx.model.opaque_callables
    ):
        # A bare call to a whitelisted module function, the shape the
        # ``__main__`` guard exists to hold. Such a call cannot change
        # anything the trace models: a body may not reference a tagged row
        # set, may not receive one as an argument, and rebinds only its own
        # locals, because ``global`` and ``nonlocal`` are unsupported
        # statements and every side-effecting statement form is too.
        return _expression_violation(value, ctx)
    return True


def _is_print_read(call: ast.Call, ctx: _TraceContext) -> bool:
    """``print`` over names, constants, f-strings, and ``str``/``repr`` of names."""

    if not (isinstance(call.func, ast.Name) and call.func.id == "print"):
        return False
    if not _is_builtin_name("print", ctx) or call.keywords:
        return False
    return all(_print_argument(item) for item in call.args)


def _print_argument(node: ast.expr, depth: int = 0) -> bool:
    if depth >= _MAX_EXPRESSION_DEPTH:
        return False
    if isinstance(node, ast.Name | ast.Constant):
        return True
    if isinstance(node, ast.JoinedStr):
        return all(_print_argument(item, depth + 1) for item in node.values)
    if isinstance(node, ast.FormattedValue):
        return _print_argument(node.value, depth + 1) and (
            node.format_spec is None or _print_argument(node.format_spec, depth + 1)
        )
    if isinstance(node, ast.BinOp):
        # Arithmetic over builtin-typed values is inert: user-defined
        # operator hooks would need a class, and classes cannot exist here.
        return _print_argument(node.left, depth + 1) and _print_argument(node.right, depth + 1)
    if isinstance(node, ast.UnaryOp):
        return _print_argument(node.operand, depth + 1)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"str", "repr"}
        and len(node.args) == 1
        and not node.keywords
    ):
        return isinstance(node.args[0], ast.Name)
    return False


def _expression_violation(
    node: ast.expr, ctx: _TraceContext, *, in_literal: bool = False, depth: int = 0
) -> bool:
    """Whether an expression sits outside the readable forms.

    ``in_literal`` marks the inside of a container literal, where a row is
    rebuilt and any evaluated call could mutate the row being read; only the
    recode and extraction vocabulary survives there.
    """

    if depth >= _MAX_EXPRESSION_DEPTH:
        return True

    def _recurse(*children: ast.expr | None, literal: bool = in_literal) -> bool:
        return any(
            _expression_violation(child, ctx, in_literal=literal, depth=depth + 1)
            for child in children
            if child is not None
        )

    if isinstance(node, ast.Name | ast.Constant):
        return False
    if isinstance(node, ast.JoinedStr):
        return _recurse(*node.values)
    if isinstance(node, ast.FormattedValue):
        return _recurse(node.value, node.format_spec)
    if isinstance(node, ast.BinOp):
        return _recurse(node.left, node.right)
    if isinstance(node, ast.UnaryOp):
        return _recurse(node.operand)
    if isinstance(node, ast.BoolOp):
        return _recurse(*node.values)
    if isinstance(node, ast.Compare):
        return _recurse(node.left, *node.comparators)
    if isinstance(node, ast.IfExp):
        return _recurse(node.test, node.body, node.orelse)
    if isinstance(node, ast.Subscript):
        return _recurse(node.value, node.slice)
    if isinstance(node, ast.Slice):
        return _recurse(node.lower, node.upper, node.step)
    if isinstance(node, ast.Attribute):
        return _recurse(node.value)
    if isinstance(node, ast.Dict):
        for key in node.keys:
            if key is None:
                continue
            if not isinstance(key, ast.Constant):
                return True
        return _recurse(
            *[item for item in node.keys if item is not None], literal=True
        ) or _recurse(*node.values, literal=True)
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return _recurse(*node.elts, literal=True)
    if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp):
        return _comprehension_violation(node, node.elt, None, ctx, depth)
    if isinstance(node, ast.DictComp):
        return _comprehension_violation(node, node.key, node.value, ctx, depth)
    if isinstance(node, ast.Call):
        return _call_violation(node, ctx, in_literal=in_literal, depth=depth)
    return True


def _comprehension_violation(
    node: ast.expr,
    element: ast.expr,
    second: ast.expr | None,
    ctx: _TraceContext,
    depth: int,
) -> bool:
    generators = getattr(node, "generators", [])
    if len(generators) != 1:
        return True
    generator = generators[0]
    if generator.is_async or not isinstance(generator.target, ast.Name):
        return True
    iterable = generator.iter
    if not (
        isinstance(iterable, ast.Name)
        or (isinstance(iterable, ast.Call) and _is_reader_call(iterable, ctx.model))
        or (
            isinstance(iterable, ast.Call)
            and _call_name(iterable) == "list"
            and len(iterable.args) == 1
            and isinstance(iterable.args[0], ast.Call)
            and _is_reader_call(iterable.args[0], ctx.model)
        )
    ):
        return True
    children = [element, *([second] if second is not None else []), *generator.ifs]
    return any(_expression_violation(item, ctx, depth=depth + 1) for item in children)


def _call_violation(call: ast.Call, ctx: _TraceContext, *, in_literal: bool, depth: int) -> bool:
    name = _call_name(call)
    model = ctx.model
    if name in model.opaque_callables:
        # A duplicated definition, an escaping callable name, a helper that
        # calls one of its own parameters, or a body reading state this trace
        # never saw: which code runs here is a runtime question.
        return True
    arguments = [*call.args, *[item.value for item in call.keywords]]
    if any(isinstance(item, ast.Starred) for item in call.args):
        return True
    if any(item.arg is None for item in call.keywords):
        return True
    recognized = _recognized_call(call, ctx)
    if in_literal and not _container_value_call(call, ctx):
        return True
    if not recognized:
        # Default deny for calls. Admitting an unrecognized call because it
        # named no tagged row set is how ``globals()["rows"].clear()`` and
        # ``row.update(...)`` mutated tagged state invisibly: neither
        # mentions a tagged name syntactically. If this trace cannot say
        # what a call does, the document abstains.
        return True
    return any(
        _expression_violation(item, ctx, in_literal=False, depth=depth + 1) for item in arguments
    ) or (
        isinstance(call.func, ast.Attribute)
        and _expression_violation(call.func.value, ctx, in_literal=False, depth=depth + 1)
    )


def _recognized_call(call: ast.Call, ctx: _TraceContext) -> bool:
    name = _call_name(call)
    model = ctx.model
    if _is_reader_call(call, model):
        return True
    if name in model.functions:
        return True
    if name in _PATH_CALLS or name in _EXACT_NUMERIC_CALLS:
        return True
    if name in _ACCUMULATOR_CALLS or name in _IDENTITY_CASTS or name in {"len", "list", "abs"}:
        return True
    if name in {
        "open",
        "print",
        "repr",
        "round",
        "bool",
        "min",
        "max",
        "sorted",
        "range",
        "zip",
        "enumerate",
        "dict",
        "tuple",
        "set",
        "all",
        "any",
    }:
        return True
    if isinstance(call.func, ast.Attribute) and call.func.attr in (
        _STRIP_METHODS | _WRITE_METHODS | _SAFE_STR_METHODS | _SAFE_PATH_METHODS | {"open"}
    ):
        return True
    return False


def _container_value_call(call: ast.Call, ctx: _TraceContext) -> bool:
    """The only calls admitted inside a container literal."""

    name = _call_name(call)
    if name in ctx.model.functions and name not in ctx.model.opaque_callables:
        return True
    if name in _CONTAINER_VALUE_CALLS:
        return True
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr in _STRIP_METHODS
        and not call.args
        and not call.keywords
    )


# ---------------------------------------------------------------------------
# The tagged-name position rule.


def _tagged_name_escape(tree: ast.Module, ctx: _TraceContext) -> bool:
    """Whether a tagged row set appears outside its four permitted positions."""

    tagged = ctx.tagged_names
    if not tagged:
        return False
    allowed = _permitted_tagged_positions(tree, ctx)
    shadowed: set[int] = set()
    for function in ctx.model.functions.values():
        locals_ = _function_local_names(function)
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and node.id in locals_:
                shadowed.add(id(node))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or node.id not in tagged:
            continue
        if id(node) in allowed or id(node) in shadowed:
            continue
        return True
    return False


def _permitted_tagged_positions(tree: ast.Module, ctx: _TraceContext) -> set[int]:
    allowed: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.comprehension):
            if isinstance(node.iter, ast.Name):
                allowed.add(id(node.iter))
        elif isinstance(node, ast.For):
            if id(node) not in ctx.recognized_loops:
                continue
            if isinstance(node.iter, ast.Name):
                allowed.add(id(node.iter))
            # The row-building loop is recognized as one whole shape, so the
            # accumulator it appends into is a modelled position, not an
            # unmodelled method receiver.
            for inner in node.body:
                if (
                    isinstance(inner, ast.Expr)
                    and isinstance(inner.value, ast.Call)
                    and isinstance(inner.value.func, ast.Attribute)
                    and inner.value.func.attr == "append"
                    and isinstance(inner.value.func.value, ast.Name)
                ):
                    allowed.add(id(inner.value.func.value))
        elif isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "len"
                and len(node.args) == 1
                and not node.keywords
                and isinstance(node.args[0], ast.Name)
            ):
                allowed.add(id(node.args[0]))
            if _is_print_read(node, ctx):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Name):
                        allowed.add(id(inner))
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                allowed.add(id(target))
                if isinstance(node.value, ast.Name):
                    allowed.add(id(node.value))
    return allowed


# ---------------------------------------------------------------------------
# The emission scan belt.


def _emission_scan_violation(tree: ast.Module, ctx: _TraceContext) -> bool:
    """Whether any staged-column comparison anywhere went unrecognized.

    This runs independently of the whitelist and of reachability. A document
    that resolves must have read every comparison between two staged-column
    extractions in it; one the trace never reached could be the emission the
    report describes.
    """

    # A comparison inside a function no reachable code can call never
    # executes; the belt may skip it. Reachability here is the model's own
    # conservative set (module-level transitive calls plus every escaping
    # name), so anything skippable is provably dead code.
    unreachable_regions: set[int] = set()
    for statement in tree.body:
        if (
            isinstance(statement, ast.FunctionDef)
            and statement.name not in ctx.model.reachable_functions
        ):
            unreachable_regions.update(id(inner) for inner in ast.walk(statement))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.Eq | ast.NotEq):
            continue
        if id(node) in ctx.recognized_compares or id(node) in unreachable_regions:
            continue
        left = _staged_extraction(node.left)
        right = _staged_extraction(node.comparators[0])
        if left is not None and right is not None and left != right:
            return True
        if _name_pair_comparison(node):
            # A comparison whose two operand subtrees read different names
            # has operands this belt cannot place -- a helper comparing its
            # two parameters is the emission's most natural factoring, and
            # wrapping the operands (``abs(a) == abs(b)``) must not hide it.
            # Unless the trace classified it through the recognized
            # helper-selector shape, the document abstains rather than let a
            # match count elsewhere answer for it.
            return True
    return False


def _name_pair_comparison(node: ast.Compare) -> bool:
    left_names = _operand_names(node.left)
    right_names = _operand_names(node.comparators[0])
    if not left_names or not right_names:
        return False
    if left_names != right_names:
        return True
    # ``value(item, 'call') == value(item, 'founder')`` reads the same
    # names on both sides; the differing string constants are what make it
    # an emission comparison the trace did not read.
    return _operand_constants(node.left) != _operand_constants(node.comparators[0])


def _operand_names(node: ast.expr) -> frozenset[str]:
    return frozenset(inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name))


def _operand_constants(node: ast.expr) -> frozenset[object]:
    return frozenset(
        inner.value
        for inner in ast.walk(node)
        if isinstance(inner, ast.Constant) and isinstance(inner.value, str | int | float | bool)
    )


def _staged_extraction(node: ast.expr) -> tuple[str, str] | None:
    """The staged extraction anywhere inside an operand's subtree, if any.

    This is a belt, so over-detection is safe (it can only force an
    abstention) and structural recursion is not: a keyword argument on a
    cast (``int(x, base=10)``) hid the operand from the previous
    shape-following version, a demonstrated wrong answer. The whole subtree
    is walked instead.
    """

    for inner in ast.walk(node):
        if (
            isinstance(inner, ast.Subscript)
            and isinstance(inner.value, ast.Name)
            and isinstance(inner.slice, ast.Constant)
            and isinstance(inner.slice.value, str)
        ):
            return (inner.value.id, inner.slice.value)
    return None


# ---------------------------------------------------------------------------
# Report reachability and control-flow bounds.
#
# Copied from ``quantity_dataflow_adapter`` so the two recognizers stay
# independently versionable; see this module's docstring.


def _accumulated_comprehension_ids(tree: ast.Module) -> set[int]:
    """Comprehensions whose elements a product or sum accumulates."""

    ids: set[int] = set()
    assigned: dict[str, list[ast.expr]] = {}
    consumed: set[str] = set()
    renames: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and _call_name(node) in _ACCUMULATOR_CALLS
            and len(node.args) == 1
        ):
            argument = node.args[0]
            if isinstance(argument, ast.GeneratorExp | ast.ListComp):
                ids.add(id(argument))
            elif isinstance(argument, ast.Name):
                consumed.add(argument.id)
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            if isinstance(node.value, ast.GeneratorExp | ast.ListComp):
                assigned.setdefault(node.targets[0].id, []).append(node.value)
            elif isinstance(node.value, ast.Name):
                # ``scores = weights`` then ``math.prod(scores)`` consumes
                # the comprehension bound to ``weights``; missing the rename
                # left that comprehension unclassified, a demonstrated
                # wrong answer.
                renames.setdefault(node.targets[0].id, set()).add(node.value.id)
    changed = True
    while changed:
        changed = False
        for target, values in renames.items():
            if target in consumed:
                fresh = values - consumed
                if fresh:
                    consumed |= fresh
                    changed = True
    for name in consumed:
        for comprehension in assigned.get(name, []):
            ids.add(id(comprehension))
    return ids


def _walk_skipping_lambdas(statement: ast.AST) -> list[ast.AST]:
    found: list[ast.AST] = []
    stack: list[ast.AST] = [statement]
    while stack:
        node = stack.pop()
        found.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Lambda):
                continue
            stack.append(child)
    return found


def _is_path_like(node: ast.expr, path_names: set[str], depth: int = 0) -> bool:
    """Whether an expression resolves to a filesystem path or a handle on one.

    A ``StringIO`` buffer also answers to ``write``, so a diagnostic string
    written into memory would otherwise look exactly like the published
    report. Only a ``Path`` call chain, a name currently bound from one, or
    an ``open`` on one counts.
    """

    if depth >= _MAX_EXPRESSION_DEPTH:
        return False
    if isinstance(node, ast.Name):
        return node.id in path_names
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name in _PATH_CALLS:
            return True
        if name == "open" and node.args:
            return _is_path_like(node.args[0], path_names, depth + 1)
        if isinstance(node.func, ast.Attribute):
            return _is_path_like(node.func.value, path_names, depth + 1)
        return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_path_like(node.left, path_names, depth + 1) or _is_path_like(
            node.right, path_names, depth + 1
        )
    if isinstance(node, ast.Attribute):
        return _is_path_like(node.value, path_names, depth + 1)
    return False


def _is_write_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _WRITE_METHODS
        and bool(node.args)
    )


def _report_write_call_ids(tree: ast.Module) -> frozenset[int]:
    """Write calls whose receiver is a filesystem path at that point in the module.

    Path-likeness is tracked with last binding wins. ``sink = Path(...)``
    followed by ``sink = io.StringIO()`` leaves ``sink`` an in-memory buffer,
    and the write that follows publishes nothing.
    """

    write_ids: set[int] = set()
    ever: set[str] = set()
    broken: set[str] = set()

    def _rebind(name: str, path_like: bool, names: set[str]) -> None:
        if path_like:
            names.add(name)
            ever.add(name)
        else:
            names.discard(name)
            broken.add(name)

    def _scan(statements: list[ast.stmt], names: set[str]) -> None:
        for statement in statements:
            if isinstance(statement, ast.With | ast.AsyncWith):
                for item in statement.items:
                    if isinstance(item.optional_vars, ast.Name):
                        _rebind(
                            item.optional_vars.id,
                            _is_path_like(item.context_expr, names),
                            names,
                        )
                _scan(list(statement.body), names)
                continue
            if isinstance(statement, ast.If | ast.For | ast.While):
                _scan(list(statement.body), names)
                _scan(list(statement.orelse), names)
                continue
            for inner in ast.walk(statement):
                if _is_write_call(inner):
                    assert isinstance(inner, ast.Call)
                    assert isinstance(inner.func, ast.Attribute)
                    if _is_path_like(inner.func.value, names):
                        write_ids.add(id(inner))
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                _rebind(
                    statement.targets[0].id,
                    _is_path_like(statement.value, names),
                    names,
                )
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                _rebind(
                    statement.target.id,
                    statement.value is not None and _is_path_like(statement.value, names),
                    names,
                )

    module_names: set[str] = set()
    _scan([item for item in tree.body if not isinstance(item, ast.FunctionDef)], module_names)
    # A function body cannot be placed in the module's binding order, so it
    # sees only the names that were path-like and never rebound to anything
    # else.
    stable = (module_names | ever) - broken
    for function in (item for item in tree.body if isinstance(item, ast.FunctionDef)):
        _scan(list(function.body), set(stable))
    return frozenset(write_ids)


def _write_payloads(node: ast.AST, write_call_ids: frozenset[int]) -> list[ast.expr]:
    payloads: list[ast.expr] = []
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call) and id(inner) in write_call_ids:
            payloads.append(inner.args[0])
    return payloads


def _called_function_names(
    tree: ast.Module, functions: dict[str, ast.FunctionDef]
) -> frozenset[str]:
    """Module-level functions some reachable caller actually calls.

    A return statement inside a function nobody calls never delivers a value
    anywhere, and neither does a write inside one, so neither seeds the
    report-reaching set.
    """

    frontier: set[str] = set()
    for statement in (item for item in tree.body if not isinstance(item, ast.FunctionDef)):
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and _call_name(node) in functions:
                frontier.add(_call_name(node))
    reached: set[str] = set()
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        reached.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call):
                callee = _call_name(node)
                if callee in functions and callee not in reached:
                    frontier.add(callee)
    return frozenset(reached)


def _report_reaching_names(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef],
    write_call_ids: frozenset[int],
    reachable: frozenset[str],
) -> set[str]:
    """Names whose values can flow into a written report payload.

    This is a permit gate only. Widening it can admit a comparison that never
    reaches the report, which costs an abstention, and can never change which
    orientation a classified comparison reports.
    """

    dependencies: dict[str, set[str]] = {}
    seeds: set[str] = set()

    def _depend(target: str, values: list[ast.expr]) -> None:
        free: set[str] = set()
        for value in values:
            free.update(name.id for name in ast.walk(value) if isinstance(name, ast.Name))
        dependencies.setdefault(target, set()).update(free)

    def _collect_edge(node: ast.AST) -> None:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            _depend(node.targets[0].id, [node.value])
            return
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            if node.func.attr in {"append", "extend"}:
                _depend(node.func.value.id, list(node.args))
            elif node.func.attr == "insert":
                _depend(node.func.value.id, list(node.args[1:]))
            return
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.op, ast.Add | ast.Mult)
        ):
            _depend(node.target.id, [node.value])

    def _collect(statements: list[ast.stmt], *, seeding: bool) -> None:
        for statement in _flatten_statements(statements):
            if seeding:
                for payload in _write_payloads(statement, write_call_ids):
                    for name in ast.walk(payload):
                        if isinstance(name, ast.Name):
                            seeds.add(name.id)
                if isinstance(statement, ast.Return) and statement.value is not None:
                    for name in ast.walk(statement.value):
                        if isinstance(name, ast.Name):
                            seeds.add(name.id)
        for statement in statements:
            for node in ast.walk(statement):
                _collect_edge(node)

    _collect(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        seeding=True,
    )
    for function in functions.values():
        _collect(function.body, seeding=function.name in reachable)

    reaching = set(seeds)
    changed = True
    while changed:
        changed = False
        for target, free in dependencies.items():
            if target in reaching and not free <= reaching:
                reaching.update(free)
                changed = True
    return reaching


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _flatten_statements(statements: list[ast.stmt]) -> list[ast.stmt]:
    flat: list[ast.stmt] = []
    for statement in statements:
        if isinstance(statement, ast.With):
            flat.extend(_flatten_statements(statement.body))
        elif isinstance(statement, ast.If) and _is_main_guard(statement):
            flat.extend(_flatten_statements(statement.body))
        else:
            flat.append(statement)
    return flat


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _ast_node_evidence_span(document: InspectionDocument, node: ast.AST) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    lines = document.content.decode("utf-8").splitlines()
    start_column = getattr(node, "col_offset", 0) + 1
    end_offset = getattr(node, "end_col_offset", None)
    if end_offset is None:
        end_column = len(lines[end_line - 1]) if 1 <= end_line <= len(lines) else 1
    else:
        end_column = end_offset + 1
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=start_line + document.line_offset,
        end_line=end_line + document.line_offset,
        start_column=start_column,
        end_column=end_column,
        parser_result_ref=document.parser_result_ref,
    )
