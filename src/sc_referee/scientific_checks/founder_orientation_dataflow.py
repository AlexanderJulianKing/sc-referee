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

v2.2.0 widens the whitelist by five narrow forms. Each is admitted in one
exact shape, and anything outside that shape abstains exactly as it did
before, so the default-deny trust model is unchanged.

- A ``csv`` reader may take a ``<path-like>.read_text(...).splitlines()``
  chain, inline or through a name single-assigned from it. Every keyword
  argument of ``read_text`` must be a string literal. Any other reader
  argument construction is read exactly as it was.
- A module-level name assigned exactly once in the whole module, to a numeric
  or string literal or the negation of a numeric one, resolves to that
  literal in the positions where a literal already decides: a string column
  subscript, a selector branch value, a binary-constant position, and the
  one-literal position of ``C - x``, ``x ^ C``, and ``abs(x - C)``. A name
  bound a second time anywhere in the module, under any binding form
  including a parameter or a loop target, is not a constant.
- ``vals = [<recode>(row[COL]) for row in rows]`` over a plainly named tagged
  row set, with no filter, is a column-values list carrying one column's
  path. ``zip(A, B)`` over two single-assignment column-values lists of the
  *same* named row set pairs them, and ``pair[0]`` / ``pair[1]`` under an
  integer literal read the respective paths. Any other index, a filter, a
  second source, or a rebound name abstains.
- ``A + (B - A) * FLAG`` in exactly that shape is a selector whose match
  branch is ``B`` and whose mismatch branch is ``A``, under the unchanged
  canonicity rule. A two-parameter helper may hold one single-assignment
  local bound to the comparison of its two bare parameters and return a
  canonical selector over that local; any other body shape stays banned.
- The whitelist admits exactly what those four need: the read-text chain as a
  readable right-hand side, a recognized ``zip`` pairing as a comprehension
  iterable, and integer-literal subscripts of a paired loop variable.

v2.2.2 widens it by four more, on the same terms: one exact shape each, and
anything outside that shape abstains exactly as it did before.

- ``dict(row)`` in the element position of a reader or row-set comprehension
  is the identity row rebuild, the same value ``{**row}`` already resolves
  to. ``dict`` must be the builtin, which the builtin-shadowing ban already
  guarantees, and the one argument must be the loop variable; a second
  argument or any keyword is a different construction and stays opaque.
- ``handle.close()`` on a name whose single binding in the whole module is
  the modelled ``open()`` -- as an assignment or as a ``with`` target -- is
  admitted as a bare expression statement and as an assignment right-hand
  side, because it returns ``None`` and touches no row value. Only ``close``
  is admitted: ``read`` and ``readlines`` deliver the file's contents and
  would need the reader-chain semantics this form does not model.
- A helper with exactly one plain parameter, whose body is an optional
  docstring, then at most one single-assignment local, then one return, and
  whose returned expression is a recognized recode or extraction over
  ``param[COL]``, is a column-extraction helper. ``helper(row)`` in a column
  position then reads that column, with the helper's parity, numeric proof,
  and boolean taint folded in. Rebinding the parameter, a second parameter,
  and every other body shape abstain as they did before.
- ``A * FLAG + B * (1 - FLAG)`` joins ``A + (B - A) * FLAG`` as a canonical
  arithmetic selector, with ``A`` the match value and ``B`` the mismatch
  value. Both products must carry the same flag expression, the complement
  must be exactly one minus that flag, and the canonicity rule over the
  resolved constants is unchanged.

v2.2.3 widens it by ten more, on the same terms. Every one is one exact
shape, and anything outside that shape abstains exactly as it did before.

- A module-level name assigned exactly once to ``Fraction(a, b)`` or
  ``Decimal('s')`` over literal arguments resolves to that value in selector
  branch positions, which is where the selector-constant grammar already
  reads such a constructor written inline. It resolves nowhere else: an
  exact-numeric constant is not the literal ``1`` the recode vocabulary
  tests for, so ``WEIGHT - x`` is still not an involution.
- A helper's parameter used as a path receiver is a filesystem path when
  every call site binds it to a provably path-like argument. The proof is
  the bind-and-check the helper-parity rule uses; a helper nothing calls, a
  name that escapes call position, and one call site handing over anything
  else all leave the parameter unproven.
- ``.splitlines()`` applied to a name assigned exactly once from a
  ``read_text(...)`` call is admitted wherever the inline chain is, which is
  what this module's grammar has always said and what its code did not do.
- ``<path-like>.mkdir(...)`` with no positional argument and literal keyword
  arguments joins ``close()`` in the admitted bare expression statements.
- A helper whose body is one return of ``path_parameter.write_text(payload)``
  over its other parameter, called with a provably path-like argument and a
  report-text name, seeds report-reachability exactly as the inline write
  does. Routing the write through a helper otherwise hides the report plane.
- ``[<recode>(v) for v in column_values]`` over a single-assignment
  column-values list is another column-values list of the same column over
  the same rows, with the recode's parity, numeric proof, and boolean taint
  folded in.
- ``[f(A[i], B[i]) for i in range(N)]`` and its loop form pair ``A`` and
  ``B`` exactly as ``zip(A, B)`` does, when both are single-assignment
  column-values lists of one single-assignment row-set name, the index
  appears nowhere but as their subscript, and ``N`` is provably ``len(A)``,
  ``len(B)``, or ``len(rows)``. Only those three forms prove that the walk
  covers each pair once and in order.
- ``for v in vals: total = total + v`` over a list of recognized per-element
  selectors classifies that list's comparison with the loop's reaching
  status, exactly as ``sum(vals)`` already does.
- The same loop over a single column-values list is recognized as consuming
  that list. It classifies nothing, because a count of one column carries no
  cross-panel orientation, but it no longer abstains.
- ``print`` with ``sep``, ``end``, or ``flush`` keyword arguments whose
  values are string literals or ``None`` joins the print-read form. ``file``
  stays banned: it redirects the write to a receiver this trace has not
  proven is a path.

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
from collections.abc import Iterator
from contextlib import contextmanager
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
# Inert Path operations: they touch filesystem metadata at most, never row
# data. ``mkdir`` creates the results directory a report is written into; it
# returns None and cannot reach any value this trace follows.
_SAFE_PATH_METHODS = frozenset({"resolve", "absolute", "expanduser", "joinpath", "mkdir"})
_BUILTIN_NAMES = frozenset(dir(builtins))

_REPAIRED = "repaired"
_DIRECT = "direct"


def founder_orientation_dataflow_grammar(
    direct_operand: str, repaired_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "founder-orientation-emission-dataflow",
        "grammar_version": "2.2.3",
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
            "comparison would. The body may also be an optional docstring, one "
            "single-assignment local bound to a comparison of the two bare "
            "parameters, and one return of a canonical selector over that "
            "local; parameter rebinding and every other body shape stay banned. "
            "Any other comparison between two bare names, "
            "anywhere, must have been recognized or the document abstains"
        ),
        "column_extraction_helpers": (
            "a helper with exactly one plain parameter whose body is an "
            "optional docstring, then at most one single-assignment local "
            "that does not rebind the parameter, then one return, and whose "
            "returned expression is a recognized recode or extraction over "
            "param[COL] with COL a string literal or a module constant, is a "
            "column-extraction helper; helper(row) in a column position "
            "reads that column with the helper's parity, numeric proof, and "
            "boolean taint folded in, and a comparison inside such a helper "
            "is marked recognized only when the trace actually classified "
            "it; a second parameter, a keyword call, a rebound parameter, "
            "and every other body shape abstain as before"
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
            "unsupported because payloads are evaluated; print may carry sep, end, "
            "and flush keyword arguments whose values are string literals or None, "
            "and file is banned because it redirects the write to an unproven "
            "receiver"
        ),
        "row_source_operations": [
            "csv.DictReader and csv.reader, only when the call resolves to the csv "
            "module through the module's own import table",
            "the reader's argument may be a path-like read_text chain, inline or "
            "through a name single-assigned from it: <path-like>.read_text(...) "
            "whose keyword arguments are all string literals, followed by "
            ".splitlines() applied either to that call or to a name assigned "
            "exactly once from it; every other argument construction is "
            "unchanged, and the reader call itself may be bound to a name and "
            "iterated from there",
            "close() with no argument on a name whose single binding in the whole "
            "module is the modelled open(), as a bare expression statement or an "
            "assignment right-hand side; every other file-handle method is "
            "outside the whitelist",
        ],
        "module_constants": (
            "a module-level name assigned exactly once in the whole module to a "
            "numeric or string literal, or the negation of a numeric literal, and "
            "never bound again under any form, resolves to that literal in string "
            "column subscripts, selector branch values, binary-constant positions, "
            "and the one-literal position of C - x, x ^ C, and abs(x - C); a name "
            "bound the same way to Fraction(a, b) or Decimal('s') over literal "
            "arguments resolves in selector branch positions only, because an "
            "exact-numeric constructor is not the literal one the recode "
            "vocabulary tests for; a name bound twice, augmented, or given any "
            "other value stays unresolvable"
        ),
        "column_value_pairing": (
            "an unfiltered list comprehension [<recode>(row[COL]) for row in rows] "
            "over a plainly named tagged row set is a column-values list carrying "
            "one column's source, parity, numeric proof, and boolean taint; "
            "zip(A, B), list(zip(A, B)), and the identity comprehension over "
            "either, where A and B are single-assignment column-values lists of "
            "the same named row set, pair them; iterating the pair and reading "
            "pair[0] or pair[1] under an integer literal yields the respective "
            "paths, which classify through the ordinary operand-path rule with "
            "the lists' parities folded in; an unfiltered [<recode>(v) for v in "
            "A] over such a list is another column-values list of the same "
            "column with the recode folded in; a comprehension or loop over "
            "range(N) reading exactly A[i] and B[i], with the index appearing "
            "nowhere else and N provably len(A), len(B), or len(rows), pairs "
            "them the same way; a filter, a differing source, a rebound name, "
            "tuple unpacking, an unprovable length, and every other index abstain"
        ),
        "path_receivers": (
            "a write, a mkdir, and a read_text chain are admitted only on a "
            "receiver that is provably a filesystem path under last-binding-wins "
            "tracking; a helper parameter counts as such a receiver when every "
            "call site of that helper binds it to a provably path-like argument, "
            "and a helper nothing calls, a helper name that escapes call "
            "position, and a single call site handing over anything else all "
            "leave the parameter unproven"
        ),
        "emission_comparison": (
            "an equality or inequality between two distinct columns of one "
            "staged row set, selecting between two numeric values inside a "
            "product or sum accumulation whose value reaches the written report"
        ),
        "selector_forms": [
            "conditional expression whose test is the comparison",
            "two-element list, tuple, or dict literal indexed by the comparison",
            "the arithmetic-encoded form A + (B - A) * FLAG in exactly that shape, "
            "with A and B resolved selector constants and FLAG a recognized "
            "emission comparison or a bool() or int() cast of one; the match "
            "branch is B and the mismatch branch is A",
            "the multiply-complement form A * FLAG + B * (1 - FLAG), in that shape "
            "and its commuted addend order, with A the match branch and B the "
            "mismatch branch; both products must carry the same flag expression "
            "and the complement must be exactly the literal or resolved-constant "
            "one minus that flag",
        ],
        "accumulation_forms": [
            "sum, prod, math.prod, or math.fsum over a comprehension",
            "a comprehension bound to a name that one of those consumes",
            "an elementwise multiply or add accumulation loop over the row set",
            "an elementwise multiply or add accumulation loop or comprehension "
            "over a recognized column-values pairing",
            "an accumulation loop whose payload is the bare loop variable over a "
            "single-assignment list a comprehension built, which consumes that "
            "comprehension exactly as sum of the same name does",
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
            "a one-parameter column-extraction helper applying any of the above to param[COL]",
            "a recognized elementwise accumulation loop applying any of the above",
        ],
        "identity_preserving_steps": [
            "int, float, and str casts",
            "strip, lstrip, and rstrip on a column value",
            "assignment and list materialization of a row set",
            "constant-string column subscripts, and the integer literals 0 and 1 "
            "subscripting a recognized paired loop variable",
            (
                "dict literals and dict-spread literals rebuilding a row, read "
                "strictly left to right so a later entry overrides an earlier one, "
                "and containing no call outside the recode and extraction vocabulary"
            ),
            "dict(row) on the loop variable, the identity row rebuild, with dict "
            "the builtin and exactly that one argument",
        ],
        "whitelisted_statements": [
            "import and from-import, recorded in an import table",
            "assignment to exactly one plain name from a fully readable expression",
            "function definition subject to the helper rules",
            "expression statement only as a docstring, a recognized report write, "
            "the recognized print-read form, close() on a modelled file handle, "
            "or mkdir() with literal keyword arguments on a proven path",
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
            "comprehensions and generators of the recognized shape over a name, "
            "a recognized reader call, or a recognized zip pairing of two names",
            "a path-like read_text chain closed by splitlines",
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
            "function reachable code actually calls; a call to a helper whose whole "
            "body is one such write of one parameter to another seeds the same way "
            "as the inline write, when the call site hands it a provably path-like "
            "argument and a report-text name; reachability excludes and never "
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
            "a name bound more than once anywhere in the module is neither a "
            "constant nor a pairable column-values list",
            "a pairing of column-values lists over different named row sets, or "
            "over a filtered comprehension, abstains",
            "a file handle admits close() and nothing else, and only through a "
            "name the modelled open() bound exactly once",
            "a one-parameter column-extraction helper resolves only in its exact "
            "body shape; a rebound parameter and a second local abstain",
            "the multiply-complement selector requires one and the same flag "
            "expression in both products and an exact one-minus complement",
            "an exact-numeric module constant resolves in selector branch "
            "positions and nowhere else",
            "a helper parameter is path-like only when every call site proves it",
            "a range-indexed pairing requires a provable length and an index "
            "used nowhere but as the two lists' subscript",
            "an accumulation loop over a rebound list name abstains",
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


@dataclass(frozen=True)
class _ColumnValues:
    """One column of one named row set, materialized as a parallel list.

    ``source_key`` is the plain name the comprehension iterated. Two lists
    pair only when they name the same row set through the same name: an
    alias of a row set is a second name for one runtime list, but proving
    that two differently named iterables walk the same rows in the same
    order is beyond this trace, so a differing key abstains.
    """

    source_key: str
    source: _Rows
    column: str
    parity: int
    numeric: bool | None
    boolean: bool

    @property
    def path(self) -> _Path:
        return _Path(self.column, self.parity, numeric=self.numeric, boolean=self.boolean)


@dataclass(frozen=True)
class _Paired:
    """Two column-values lists of one row set, zipped elementwise."""

    left: _ColumnValues
    right: _ColumnValues

    @property
    def source(self) -> _Rows:
        return self.left.source


@dataclass(frozen=True)
class _IndexedPair:
    """Two column-values lists read elementwise through one shared range index.

    ``[f(A[i], B[i]) for i in range(len(A))]`` walks the same two lists in the
    same order that ``zip(A, B)`` walks them, so it pairs them exactly as a
    zip does. ``names`` records the two list names, because the index reads
    them by name rather than through a tuple.
    """

    left: _ColumnValues
    right: _ColumnValues
    names: tuple[str, str]

    @property
    def source(self) -> _Rows:
        return self.left.source


_OPAQUE = _Opaque()
_EMPTY_LIST = _EmptyList()

_Value = _Rows | _Scalar | _EmptyList | _ColumnValues | _Paired | _IndexedPair | _Opaque


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
    constants: dict[str, int | float | str]
    selector_constants: dict[str, int | float | str]
    single_assignment: frozenset[str]
    single_bindings: dict[str, ast.expr]
    read_chain_call_ids: frozenset[int]
    mkdir_call_ids: frozenset[int]
    helper_write_calls: dict[int, ast.expr]
    open_handle_names: frozenset[str]


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
    recognized_pairings: set[int] = field(default_factory=set)
    # The second comparison node a multiply-complement selector writes, keyed
    # by the first. The two are the same flag; they are recognized together,
    # and only when the trace actually classifies the first.
    selector_siblings: dict[int, tuple[ast.Compare, ...]] = field(default_factory=dict)
    pair_paths: dict[str, tuple[_Path, _Path]] = field(default_factory=dict)
    # ``(list name, index name)`` to the column path that subscript reads,
    # for the range-indexed pairing form.
    indexed_paths: dict[tuple[str, str], _Path] = field(default_factory=dict)
    tagged_names: set[str] = field(default_factory=set)
    unresolved: bool = False

    @property
    def functions(self) -> dict[str, ast.FunctionDef]:
        return self.model.functions

    @property
    def constants(self) -> dict[str, int | float | str]:
        return self.model.constants

    @property
    def selector_constants(self) -> dict[str, int | float | str]:
        return self.model.selector_constants

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
        statement.value, ctx.model.write_call_ids, ctx.model.helper_write_calls
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
    indexed = _range_pairing(generator, [node.elt, *generator.ifs], env, ctx)
    tagged = indexed if indexed is not None else _tag(generator.iter, env, ctx)
    with _pair_scope(tagged, generator.target.id, ctx) as source:
        selectors = _selector_comparisons(node.elt, ctx)
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


@contextmanager
def _pair_scope(source: _Value, loop_var: str, ctx: _TraceContext) -> Iterator[_Value]:
    """Bind a paired loop variable's two halves for the body of one iteration.

    Outside a recognized pairing this yields the source unchanged, so every
    caller reads one code path. Inside one it yields the row set both columns
    came from, which is what the operand-path rule needs, and registers the
    two paths under the loop variable so ``pair[0]`` and ``pair[1]`` resolve.

    A range-indexed pairing registers its two paths under ``(list, index)``
    instead, because the two halves are read by list name rather than by
    tuple position.
    """

    if isinstance(source, _IndexedPair):
        keys = ((source.names[0], loop_var), (source.names[1], loop_var))
        previous_indexed = {key: ctx.indexed_paths.get(key) for key in keys}
        ctx.indexed_paths[keys[0]] = source.left.path
        ctx.indexed_paths[keys[1]] = source.right.path
        try:
            yield source.source
        finally:
            for key, held in previous_indexed.items():
                if held is None:
                    ctx.indexed_paths.pop(key, None)
                else:
                    ctx.indexed_paths[key] = held
        return
    if not isinstance(source, _Paired):
        yield source
        return
    previous = ctx.pair_paths.get(loop_var)
    ctx.pair_paths[loop_var] = (source.left.path, source.right.path)
    try:
        yield source.source
    finally:
        if previous is None:
            ctx.pair_paths.pop(loop_var, None)
        else:
            ctx.pair_paths[loop_var] = previous


def _range_pairing(
    node: ast.comprehension | ast.For,
    payloads: list[ast.expr] | list[ast.stmt],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _IndexedPair | None:
    """``for i in range(N)`` reading exactly ``A[i]`` and ``B[i]``, or None.

    This is the index-walked spelling of ``zip(A, B)``, and it is admitted on
    the same terms. Both lists must be single-assignment column-values lists
    of one single-assignment row-set name, the index may appear nowhere but as
    their subscript -- ``A[i + 1]`` or a bare ``i`` in the payload reads
    something this pairing does not describe -- and the length must be
    provably the length of one of the two lists or of the rows behind them.
    Only those three ``len`` forms prove that the walk covers each pair once
    and in order; a named constant, however plausible, does not.
    """

    target = node.target
    iterable = node.iter
    if not isinstance(target, ast.Name):
        return None
    index = target.id
    if not (
        isinstance(iterable, ast.Call)
        and _call_name(iterable) == "range"
        and _is_builtin_name("range", ctx)
        and len(iterable.args) == 1
        and not iterable.keywords
    ):
        return None
    subscripted: set[int] = set()
    order: list[str] = []
    for payload in payloads:
        for inner in ast.walk(payload):
            if (
                isinstance(inner, ast.Subscript)
                and isinstance(inner.value, ast.Name)
                and isinstance(inner.slice, ast.Name)
                and inner.slice.id == index
            ):
                subscripted.add(id(inner.slice))
                if inner.value.id not in order:
                    order.append(inner.value.id)
    if len(order) != 2:
        return None
    for payload in payloads:
        for inner in ast.walk(payload):
            if isinstance(inner, ast.Name) and inner.id == index and id(inner) not in subscripted:
                return None
    lists: list[_ColumnValues] = []
    for name in order:
        held = env.get(name)
        if not isinstance(held, _ColumnValues) or name not in ctx.model.single_assignment:
            return None
        lists.append(held)
    left, right = lists
    if left.source_key != right.source_key or left.source != right.source:
        return None
    if left.source_key not in ctx.model.single_assignment:
        return None
    if not _proven_pair_length(iterable.args[0], {*order, left.source_key}, ctx):
        return None
    ctx.recognized_pairings.add(id(iterable))
    return _IndexedPair(left, right, (order[0], order[1]))


def _proven_pair_length(node: ast.expr, allowed: set[str], ctx: _TraceContext) -> bool:
    """``len(A)``, ``len(B)``, or ``len(rows)``, directly or through one name."""

    if isinstance(node, ast.Name):
        if node.id not in ctx.model.single_assignment:
            return False
        bound = ctx.model.single_bindings.get(node.id)
        if bound is None:
            return False
        node = bound
    return (
        isinstance(node, ast.Call)
        and _call_name(node) == "len"
        and _is_builtin_name("len", ctx)
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id in allowed
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
    form = _helper_selector_form(ctx.functions[name], ctx)
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
    function: ast.FunctionDef, ctx: _TraceContext
) -> tuple[ast.Compare, str, str] | None:
    """The canonical selector a helper body is, or None.

    Returns the comparison node and the parameter names on its two sides
    when the body is a single return of a canonical selector over exactly
    the helper's two parameters.

    From v2.2.0 the body may also be one single-assignment local bound to the
    comparison of the two bare parameters followed by that one return, with
    the local standing in the selector's flag position. The local must be
    bound to nothing but the comparison and must not be a parameter name, so
    the parameter-rebinding ban is untouched: the value the caller passed is
    still what the comparison reads.
    """

    if not _straight_line_helper(function, ctx):
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
    # The body must be the one return, optionally preceded by the one flag
    # binding. Any other statement before the return can rebind a parameter
    # (``expected = 1 - expected``), and reading the comparison as if the
    # caller's argument arrived unchanged was a demonstrated wrong answer in
    # both directions.
    flag: tuple[str, ast.Compare] | None = None
    if len(statements) == 2:
        flag = _helper_flag_binding(statements[0], parameters)
        if flag is None:
            return None
        statements = statements[1:]
    if len(statements) != 1 or not isinstance(statements[0], ast.Return):
        return None
    if statements[0].value is None:
        return None
    value = statements[0].value
    resolved = _helper_selector_branches(value, ctx, flag)
    if resolved is None:
        return None
    compare, match_branch, mismatch_branch = resolved
    if not _is_canonical_selector(compare, match_branch, mismatch_branch, ctx.selector_constants):
        return None
    left, right = compare.left, compare.comparators[0]
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return None
    if {left.id, right.id} != set(parameters):
        return None
    return compare, left.id, right.id


def _helper_flag_binding(
    statement: ast.stmt, parameters: list[str]
) -> tuple[str, ast.Compare] | None:
    """``flag = a == b`` over the two bare parameters, bound to a fresh name."""

    if not (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return None
    name = statement.targets[0].id
    if name in parameters:
        return None
    compare = statement.value
    if not isinstance(compare, ast.Compare) or len(compare.ops) != 1:
        return None
    left, right = compare.left, compare.comparators[0]
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return None
    if {left.id, right.id} != set(parameters):
        return None
    return name, compare


def _helper_selector_branches(
    value: ast.expr, ctx: _TraceContext, flag: tuple[str, ast.Compare] | None
) -> tuple[ast.Compare, ast.expr, ast.expr] | None:
    """The comparison and the two branch expressions a helper's return holds."""

    if isinstance(value, ast.IfExp):
        compare = _flag_comparison(value.test, ctx, flag)
        if compare is None:
            return None
        return compare, value.body, value.orelse
    if isinstance(value, ast.Subscript) and isinstance(value.value, ast.List | ast.Tuple):
        if not _two_element_numeric_container(value.value):
            return None
        compare = _flag_comparison(value.slice, ctx, flag)
        if compare is None:
            return None
        return compare, value.value.elts[1], value.value.elts[0]
    return _arithmetic_selector(value, ctx, flag)


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
    for item in selectors:
        # A multiply-complement selector's second flag node is the same
        # comparison as its first, which this list already holds.
        recognized.update(id(sibling) for sibling in ctx.selector_siblings.get(id(item), ()))
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
        _recognize_compare(compare, ctx)
        return
    parity = (left.parity + left_source[1] + right.parity + right_source[1]) % 2
    _recognize_compare(compare, ctx)
    classifications.append(
        _Classification(
            node=span_node,
            state=_REPAIRED if parity else _DIRECT,
            reaching=reaching,
            dead=dead,
        )
    )


def _recognize_compare(compare: ast.Compare, ctx: _TraceContext) -> None:
    """Mark a classified comparison, and the sibling its selector wrote beside it.

    A multiply-complement selector may write its flag twice. The second node
    is the same comparison, so it is recognized exactly when the first is
    classified and never on its own.
    """

    ctx.recognized_compares.add(id(compare))
    for sibling in ctx.selector_siblings.get(id(compare), ()):
        ctx.recognized_compares.add(id(sibling))


def _selector_comparisons(element: ast.expr, ctx: _TraceContext) -> list[ast.Compare]:
    """Canonical selectors: comparisons choosing between two proven probabilities.

    A selector classifies only in its canonical form: an equality comparison
    whose match branch carries a strictly larger constant probability than
    its mismatch branch. Everything else -- an inequality operator, swapped
    branches, or branch values that stay unprovable -- computes a value that
    is extensionally a complement of a canonical selector's, and whether
    that complement is an orientation repair or a differently parameterized
    emission matrix is not statically decidable. Non-canonical selectors are
    therefore never recognized; an emission-like comparison inside one falls
    through to the module-wide belt and the document abstains.

    From v2.2.0 a branch value may be a module constant, and the
    arithmetic-encoded selector ``A + (B - A) * FLAG`` is recognized in that
    exact shape; the canonicity rule over the resolved constants is unchanged.
    """

    constants = ctx.selector_constants
    found: list[ast.Compare] = []
    for node in ast.walk(element):
        if isinstance(node, ast.IfExp) and isinstance(node.test, ast.Compare):
            if not _numeric_like(node.body) or not _numeric_like(node.orelse):
                continue
            if _is_canonical_selector(node.test, node.body, node.orelse, constants):
                found.append(node.test)
        elif isinstance(node, ast.BinOp):
            arithmetic = _arithmetic_selector(node, ctx, flag=None)
            if arithmetic is None:
                continue
            compare, match_branch, mismatch_branch = arithmetic
            if _is_canonical_selector(compare, match_branch, mismatch_branch, constants):
                found.append(compare)
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
            if _is_canonical_selector(index, node.value.elts[1], node.value.elts[0], constants):
                found.append(index)
    return found


def _flag_comparison(
    node: ast.expr, ctx: _TraceContext, flag: tuple[str, ast.Compare] | None
) -> ast.Compare | None:
    """The comparison a selector's boolean flag position holds, or None.

    A flag is the comparison itself, an ``int`` or ``bool`` cast of one, or,
    inside a recognized helper body, the single-assignment local that was
    bound to the comparison of the helper's two bare parameters.
    """

    if (
        isinstance(node, ast.Call)
        and _call_name(node) in {"int", "bool"}
        and len(node.args) == 1
        and not node.keywords
        and _is_builtin_name(_call_name(node), ctx)
    ):
        node = node.args[0]
    if isinstance(node, ast.Compare):
        return node
    if flag is not None and isinstance(node, ast.Name) and node.id == flag[0]:
        return flag[1]
    return None


def _arithmetic_selector(
    node: ast.expr, ctx: _TraceContext, flag: tuple[str, ast.Compare] | None
) -> tuple[ast.Compare, ast.expr, ast.expr] | None:
    """The arithmetic selector encodings modelled: two shapes, both exact.

    ``A + (B - A) * FLAG`` evaluates to ``A`` when the flag is false and to
    ``B`` when it is true; ``A * FLAG + B * (1 - FLAG)`` evaluates to ``A``
    on a match and to ``B`` on a mismatch. Nothing else about the arithmetic
    is folded; the branch order is judged by the unchanged canonicity rule
    over the resolved constants.
    """

    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
        return None
    shifted = _shifted_difference_selector(node, ctx, flag)
    if shifted is not None:
        return shifted
    return _multiply_complement_selector(node, ctx, flag)


def _shifted_difference_selector(
    node: ast.BinOp, ctx: _TraceContext, flag: tuple[str, ast.Compare] | None
) -> tuple[ast.Compare, ast.expr, ast.expr] | None:
    """``A + (B - A) * FLAG``, in exactly that shape.

    The mismatch constant must stand in both of its positions and resolve to
    the same value, so the expression provably evaluates to ``A`` when the
    flag is false and to ``B`` when it is true.
    """

    product = node.right
    if not isinstance(product, ast.BinOp) or not isinstance(product.op, ast.Mult):
        return None
    difference = product.left
    if not isinstance(difference, ast.BinOp) or not isinstance(difference.op, ast.Sub):
        return None
    mismatch_branch = node.left
    match_branch = difference.left
    constants = ctx.selector_constants
    mismatch_value = _selector_constant(mismatch_branch, constants)
    repeated_value = _selector_constant(difference.right, constants)
    if mismatch_value is None or repeated_value is None or mismatch_value != repeated_value:
        return None
    if _selector_constant(match_branch, constants) is None:
        return None
    compare = _flag_comparison(product.right, ctx, flag)
    if compare is None:
        return None
    return compare, match_branch, mismatch_branch


def _multiply_complement_selector(
    node: ast.BinOp, ctx: _TraceContext, flag: tuple[str, ast.Compare] | None
) -> tuple[ast.Compare, ast.expr, ast.expr] | None:
    """``A * FLAG + B * (1 - FLAG)``, in that shape and its commuted addend order.

    One product carries the flag and the other its complement, so exactly one
    addend survives: ``A`` when the comparison holds, ``B`` when it does not.
    The two products must carry the same flag expression, which is what makes
    the two addends exclusive; two structurally different flags are two
    different selectors added together, and this reads none of them. The
    complement must be exactly one minus that flag, with the one a literal or
    a resolved module constant.
    """

    for first, second in ((node.left, node.right), (node.right, node.left)):
        match = _flag_product(first, ctx, flag, complemented=False)
        mismatch = _flag_product(second, ctx, flag, complemented=True)
        if match is None or mismatch is None:
            continue
        match_branch, match_carrier, match_compare = match
        mismatch_branch, mismatch_carrier, mismatch_compare = mismatch
        if ast.dump(match_carrier) != ast.dump(mismatch_carrier):
            continue
        if match_compare is not mismatch_compare:
            # The flag is written out twice. The two comparison nodes are one
            # flag, so they are recognized together -- but only if and when
            # the trace actually classifies this selector.
            ctx.selector_siblings[id(match_compare)] = (mismatch_compare,)
        return match_compare, match_branch, mismatch_branch
    return None


def _flag_product(
    node: ast.expr,
    ctx: _TraceContext,
    flag: tuple[str, ast.Compare] | None,
    *,
    complemented: bool,
) -> tuple[ast.expr, ast.expr, ast.Compare] | None:
    """``A * FLAG`` or ``B * (1 - FLAG)``: the branch value, the flag, its comparison.

    The constant stands to the left of the multiply in both products. That is
    the shape this form is written in, and holding to it keeps the two
    positions distinguishable without folding any arithmetic.
    """

    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return None
    branch = node.left
    carrier: ast.expr = node.right
    if complemented:
        if not (isinstance(carrier, ast.BinOp) and isinstance(carrier.op, ast.Sub)):
            return None
        if not _is_one(carrier.left, ctx.constants):
            return None
        carrier = carrier.right
    if _selector_constant(branch, ctx.selector_constants) is None:
        return None
    compare = _flag_comparison(carrier, ctx, flag)
    if compare is None:
        return None
    return branch, carrier, compare


def _is_canonical_selector(
    compare: ast.Compare,
    match_branch: ast.expr,
    mismatch_branch: ast.expr,
    constants: dict[str, int | float | str],
) -> bool:
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq):
        return False
    match_value = _selector_constant(match_branch, constants)
    mismatch_value = _selector_constant(mismatch_branch, constants)
    if match_value is None or mismatch_value is None:
        return False
    if match_value <= 0 or mismatch_value < 0:
        # Probabilities are positive (a count's mismatch branch may be
        # exactly zero). A negative pair orders differently in linear and
        # log space, so its polarity is not decidable here.
        return False
    return match_value > mismatch_value


def _selector_constant(node: ast.expr, constants: dict[str, int | float | str]) -> float | None:
    """The provable constant value of a selector branch, or None.

    Only simple literal forms qualify: a numeric literal, its negation, or a
    one- or two-argument Fraction/Decimal of literals. Arithmetic is
    deliberately excluded -- folding it in binary floats mis-orders Decimal
    expressions against their runtime values (a demonstrated wrong answer),
    and no exact folder agrees with runtime for every constructor mix.

    From v2.2.0 a name resolves when it is a module constant: assigned once
    in the whole module to a literal and never bound again. Every other name
    is still unprovable, which leaves the branch order unprovable and the
    selector non-canonical.
    """

    named = _constant_name_value(node, constants)
    if isinstance(named, int | float):
        return float(named)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int | float) and not isinstance(node.value, bool):
            if isinstance(node.value, int) and abs(node.value) > 10**12:
                # ``float`` of a large enough integer raises OverflowError;
                # no real probability constant is this large.
                return None
            return float(node.value)
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _selector_constant(node.operand, constants)
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
                value = _selector_constant(argument, constants)
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
        return _UNRESOLVED if _touches_rows(expression, loop_var, carriers, ctx) else None

    if isinstance(expression, ast.Name):
        return carriers.get(expression.id)

    if isinstance(expression, ast.Subscript):
        if isinstance(expression.value, ast.Name) and isinstance(expression.slice, ast.Name):
            # One half of a range-indexed pairing, registered for the body of
            # this iteration only.
            indexed = ctx.indexed_paths.get((expression.value.id, expression.slice.id))
            if indexed is not None:
                return indexed
        if (
            loop_var is not None
            and isinstance(expression.value, ast.Name)
            and expression.value.id == loop_var
        ):
            pair = ctx.pair_paths.get(loop_var)
            if pair is not None:
                # The loop variable is one element of a recognized pairing,
                # so only the two integer literals that name its halves read
                # a column; every other index abstains through _unknown.
                index = expression.slice
                if (
                    isinstance(index, ast.Constant)
                    and isinstance(index.value, int)
                    and not isinstance(index.value, bool)
                    and index.value in {0, 1}
                ):
                    return pair[index.value]
            elif isinstance(expression.slice, ast.Constant) and isinstance(
                expression.slice.value, str
            ):
                return _Path(expression.slice.value, 0)
            else:
                column = _constant_name_value(expression.slice, ctx.constants)
                if isinstance(column, str):
                    return _Path(column, 0)
        table = _two_element_table(expression.value, ctx.constants)
        if table is not None:
            base = _column_parity(
                expression.slice, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
            )
            return _table_shift(table, base)
        return _unknown()

    if isinstance(expression, ast.Call):
        return _call_parity(expression, loop_var, carriers, env, ctx) or _unknown()

    if isinstance(expression, ast.BinOp):
        if isinstance(expression.op, ast.Sub) and _is_one(expression.left, ctx.constants):
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
                if _is_one(one, ctx.constants):
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
                if _is_one(one, ctx.constants):
                    return _shift(
                        _column_parity(
                            other, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                        ),
                        1,
                    )
        return None
    if name in ctx.functions:
        extraction = _column_extraction_helper_parity(
            ctx.functions[name], call, loop_var, carriers, env, ctx
        )
        if extraction is not None:
            return extraction
        return _helper_parity(ctx.functions[name], call, loop_var, carriers, env, ctx)
    return None


def _is_builtin_name(name: str, ctx: _TraceContext) -> bool:
    """Whether a builtin name still means the builtin in this module."""

    return name not in ctx.functions and name not in ctx.model.imports


def _column_extraction_helper_parity(
    function: ast.FunctionDef,
    call: ast.Call,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """``extract(row)``: a one-parameter helper that reads one column of the row.

    Pulling ``int(row[COLUMN])`` out into a named helper is the most ordinary
    way to write a per-column read, and it is invisible to the recode rule
    above, which reads helpers applied to a column *value* rather than to the
    row. The shape recognized here is exact: exactly one plain parameter,
    exactly one positional argument that is the iterated row itself, and a
    body of an optional docstring, then at most one single-assignment local
    that does not rebind the parameter, then one return. The returned
    expression is read by the ordinary operand-path rule with the parameter
    standing in for the row, so it admits exactly the recodes and extractions
    a comprehension element admits, module constants and all.

    ``None`` means the shape does not apply and the ordinary helper rule
    answers instead; the unresolved marker means it applied and the body
    touched the row through something unreadable.
    """

    if loop_var is None or loop_var in ctx.pair_paths:
        # A paired loop variable is a tuple of two column values, not a row,
        # so ``param[COL]`` inside the helper would not be a column read.
        return None
    if len(call.args) != 1 or call.keywords:
        return None
    argument = call.args[0]
    if not (isinstance(argument, ast.Name) and argument.id == loop_var):
        return None
    if argument.id in carriers:
        # The name carries a column value, not a row; the recode rule reads it.
        return None
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
        or function.args.defaults
        or len(function.args.args) != 1
    ):
        return None
    if not _straight_line_helper(function, ctx):
        return None
    parameter = function.args.args[0].arg
    statements = [
        item
        for item in _flatten_statements(function.body)
        if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant))
    ]
    local: ast.Assign | None = None
    if len(statements) == 2:
        first = statements[0]
        if not (
            isinstance(first, ast.Assign)
            and len(first.targets) == 1
            and isinstance(first.targets[0], ast.Name)
            and first.targets[0].id != parameter
        ):
            # A rebound parameter makes the return read a value the caller
            # never passed, and a second local is a body this shape does not
            # describe.
            return None
        local = first
        statements = statements[1:]
    if len(statements) != 1 or not isinstance(statements[0], ast.Return):
        return None
    returned = statements[0].value
    if returned is None:
        return None
    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _UNRESOLVED
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        locals_: dict[str, _Path] = {}
        if local is not None:
            target = local.targets[0]
            assert isinstance(target, ast.Name)
            bound = _column_parity(local.value, loop_var=parameter, carriers={}, env=env, ctx=ctx)
            if bound is None:
                return None
            if not bound.resolved:
                return _UNRESOLVED
            locals_[target.id] = bound
        result = _column_parity(returned, loop_var=parameter, carriers=locals_, env=env, ctx=ctx)
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)
    if result is None:
        # The body reads no column of the row at all, so this call is not a
        # column extraction.
        return None
    if not result.resolved:
        return _UNRESOLVED
    return _Path(
        str(result.column), result.parity % 2, numeric=result.numeric, boolean=result.boolean
    )


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
    if not _straight_line_helper(function, ctx):
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


def _straight_line_helper(function: ast.FunctionDef, ctx: _TraceContext) -> bool:
    """A helper body of assignments and one closing return, with no side effects."""

    for node in ast.walk(function):
        if isinstance(node, ast.NamedExpr):
            return False
    for statement in _flatten_statements(function.body):
        if isinstance(statement, ast.Expr) and not isinstance(statement.value, ast.Constant):
            # A bare expression statement exists for its side effect; only a
            # docstring and the modelled handle close are inert. Closing the
            # staged input handle returns None and reads no row value, and it
            # is where the loader idiom puts it.
            if not (
                isinstance(statement.value, ast.Call)
                and (
                    _is_handle_close_call(statement.value, ctx)
                    or id(statement.value) in ctx.model.mkdir_call_ids
                )
            ):
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
    body = _binary_constant(expression.body, ctx.constants)
    orelse = _binary_constant(expression.orelse, ctx.constants)
    if body is None or orelse is None or body == orelse:
        return None
    for constant_side, value_side in (
        (test.left, test.comparators[0]),
        (test.comparators[0], test.left),
    ):
        constant = _binary_constant(constant_side, ctx.constants)
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


def _two_element_table(
    node: ast.expr, constants: dict[str, int | float | str]
) -> tuple[int, int] | None:
    """A literal mapping of the domain {0, 1} onto {0, 1}."""

    if isinstance(node, ast.List | ast.Tuple) and len(node.elts) == 2:
        values = [_binary_constant(item, constants) for item in node.elts]
        if values[0] is not None and values[1] is not None:
            return (values[0], values[1])
        return None
    if isinstance(node, ast.Dict) and len(node.keys) == 2:
        entries: dict[int, int] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                return None
            index = _binary_constant(key, constants)
            mapped = _binary_constant(value, constants)
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


def _binary_constant(node: ast.expr, constants: dict[str, int | float | str]) -> int | None:
    """The literal 0 or 1 an expression is, resolving module constants."""

    named = _constant_name_value(node, constants)
    if isinstance(named, int) and not isinstance(named, bool) and named in {0, 1}:
        return int(named)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value in {0, 1}
    ):
        return int(node.value)
    return None


def _is_one(node: ast.expr, constants: dict[str, int | float | str]) -> bool:
    """Whether an expression is the literal 1, resolving module constants."""

    named = _constant_name_value(node, constants)
    if isinstance(named, int | float) and not isinstance(named, bool):
        return bool(named == 1)
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


def _touches_rows(
    expression: ast.expr,
    loop_var: str | None,
    carriers: dict[str, _Path],
    ctx: _TraceContext,
) -> bool:
    for node in ast.walk(expression):
        if (
            loop_var is not None
            and isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == loop_var
        ):
            return True
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and isinstance(node.slice, ast.Name)
            and (node.value.id, node.slice.id) in ctx.indexed_paths
        ):
            # A half of a range-indexed pairing wrapped in something this
            # trace does not read is an unresolved column, not a non-column.
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
        value = env.get(node.id, _OPAQUE)
        if isinstance(value, _ColumnValues | _Paired) and node.id not in (
            ctx.model.single_assignment
        ):
            # A column-values list or a pairing carries a claim about which
            # column sits at which position. A name bound more than once
            # anywhere in the module cannot carry that claim past the second
            # binding, so it never leaves the assignment that made it.
            return _OPAQUE
        return value
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
        if isinstance(inner, _Paired):
            # ``list(zip(a, b))`` materializes the pairing without changing it.
            return inner
        return _OPAQUE
    if name == "zip" and _is_builtin_name("zip", ctx):
        return _tag_zip(node, env, ctx)
    if name in _ACCUMULATOR_CALLS or name == "len":
        return _Scalar()
    if name in _IDENTITY_CASTS and len(node.args) == 1 and not node.keywords:
        inner = _tag(node.args[0], env, ctx)
        return inner if isinstance(inner, _Scalar) else _OPAQUE
    return _OPAQUE


def _tag_zip(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    """``zip(A, B)`` over two column-values lists of one named row set.

    Both arguments must be plain names assigned exactly once in the whole
    module, both lists must have been built over the same row-set name, and
    the row set itself must be the same value. Anything else -- a third
    argument, a keyword, an inline comprehension, a rebound name, or two
    different sources -- is opaque, and every downstream use of an opaque
    value fails the whitelist rather than the classifier.
    """

    if len(node.args) != 2 or node.keywords:
        return _OPAQUE
    if not all(isinstance(argument, ast.Name) for argument in node.args):
        return _OPAQUE
    names = [argument.id for argument in node.args if isinstance(argument, ast.Name)]
    if any(name not in ctx.model.single_assignment for name in names):
        return _OPAQUE
    values = [_tag(argument, env, ctx) for argument in node.args]
    left, right = values
    if not isinstance(left, _ColumnValues) or not isinstance(right, _ColumnValues):
        return _OPAQUE
    if left.source_key != right.source_key or left.source != right.source:
        return _OPAQUE
    if left.source_key not in ctx.model.single_assignment:
        # Two independent staged reads produce structurally equal _Rows
        # values, so a rebound row-set name satisfies the equality tests
        # while the two lists read two different files (a demonstrated
        # invariant breach). The source name must be bound exactly once.
        return _OPAQUE
    ctx.recognized_pairings.add(id(node))
    return _Paired(left, right)


def _tag_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, _Value], ctx: _TraceContext
) -> _Value:
    if len(node.generators) != 1:
        return _OPAQUE
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name):
        return _OPAQUE
    source = _tag(generator.iter, env, ctx)
    if isinstance(source, _Paired):
        # ``[pair for pair in zip(a, b)]`` materializes the pairing exactly as
        # ``list`` does; any other element expression is opaque.
        if isinstance(node.elt, ast.Name) and node.elt.id == generator.target.id:
            return source
        return _OPAQUE
    if isinstance(source, _ColumnValues):
        return _recoded_column_values(node, generator, source, env, ctx)
    if not isinstance(source, _Rows):
        return _OPAQUE
    built = _row_element_value(node.elt, generator.target.id, source, env, ctx)
    if not isinstance(built, _Opaque):
        return built
    return _column_values(node, generator, source, env, ctx)


def _column_values(
    node: ast.ListComp | ast.GeneratorExp,
    generator: ast.comprehension,
    source: _Rows,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """``[<recode>(row[COL]) for row in rows]`` as one column's parallel list.

    The iterable must be a plain name, because that name is the only identity
    two lists can be proven to share, and the comprehension must carry no
    filter: a filtered list has a different length from its unfiltered
    sibling, so zipping them would pair rows that never met.
    """

    assert isinstance(generator.target, ast.Name)
    if not isinstance(node, ast.ListComp):
        # A generator is consumed by whatever reads it first; only a
        # materialized list can be paired with a sibling list.
        return _OPAQUE
    if not isinstance(generator.iter, ast.Name) or generator.ifs:
        return _OPAQUE
    if _shadows_loop_var(node.elt, generator.target.id):
        return _OPAQUE
    path = _column_parity(node.elt, loop_var=generator.target.id, carriers={}, env=env, ctx=ctx)
    if path is None or not path.resolved:
        return _OPAQUE
    return _ColumnValues(
        source_key=generator.iter.id,
        source=source,
        column=str(path.column),
        parity=path.parity,
        numeric=path.numeric,
        boolean=path.boolean,
    )


def _recoded_column_values(
    node: ast.ListComp | ast.GeneratorExp,
    generator: ast.comprehension,
    source: _ColumnValues,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """``[<recode>(v) for v in column_values]`` as the recoded column's list.

    Recoding a column-values list elementwise produces another list of the
    same column over the same rows in the same order, so it stays pairable
    with its siblings; only the parity, the numeric proof, and the boolean
    taint move. The recode is read by the ordinary operand-path rule with the
    loop variable carrying the source list's path, so it admits exactly the
    recodes a comprehension element admits and nothing else.
    """

    assert isinstance(generator.target, ast.Name)
    if not isinstance(node, ast.ListComp):
        # A generator is consumed by whatever reads it first; only a
        # materialized list can be paired with a sibling list.
        return _OPAQUE
    if not isinstance(generator.iter, ast.Name) or generator.ifs:
        return _OPAQUE
    if _shadows_loop_var(node.elt, generator.target.id):
        return _OPAQUE
    path = _column_parity(
        node.elt,
        loop_var=None,
        carriers={generator.target.id: source.path},
        env=env,
        ctx=ctx,
    )
    if path is None or not path.resolved:
        return _OPAQUE
    return _ColumnValues(
        source_key=source.source_key,
        source=source.source,
        column=str(path.column),
        parity=path.parity,
        numeric=path.numeric,
        boolean=path.boolean,
    )


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
    if _is_identity_row_copy(element, loop_var, ctx):
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


def _is_identity_row_copy(element: ast.expr, loop_var: str, ctx: _TraceContext) -> bool:
    """``dict(row)``: the identity row rebuild, exactly as ``{**row}`` rebuilds it.

    ``dict`` of one mapping copies every entry and changes none of them, so
    the rebuilt row carries the source's provenance unchanged. The
    builtin-shadowing ban already guarantees the name is the builtin; the
    check is repeated here so the shape stands on its own. A second
    argument, any keyword, or an argument that is not the loop variable is a
    different construction and stays opaque.
    """

    return (
        isinstance(element, ast.Call)
        and isinstance(element.func, ast.Name)
        and element.func.id == "dict"
        and _is_builtin_name("dict", ctx)
        and len(element.args) == 1
        and not element.keywords
        and isinstance(element.args[0], ast.Name)
        and element.args[0].id == loop_var
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
    if not _straight_line_helper(function, ctx):
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
    indexed = _range_pairing(statement, list(statement.body), env, ctx)
    source = indexed if indexed is not None else _tag(statement.iter, env, ctx)
    if isinstance(source, _Paired | _IndexedPair):
        # A pairing is iterated, never appended into, so only the
        # accumulation shape applies to it.
        with _pair_scope(source, statement.target.id, ctx) as rows:
            assert isinstance(rows, _Rows)
            if _apply_accumulation_loop(statement, rows, env, ctx, classifications, dead=dead):
                ctx.recognized_loops.add(id(statement))
                return True
        return False
    if isinstance(source, _Rows):
        if _apply_row_building_loop(statement, source, env, aliases, ctx):
            ctx.recognized_loops.add(id(statement))
            return True
        if _apply_accumulation_loop(statement, source, env, ctx, classifications, dead=dead):
            ctx.recognized_loops.add(id(statement))
            return True
        return False
    if _apply_list_accumulation_loop(statement, env, ctx):
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


def _elementwise_accumulation_targets(loop: ast.For, element: str) -> frozenset[str] | None:
    """``for v in vals: total = total + v`` and its augmented form, or None.

    The payload has to be the bare loop variable. That is what makes the loop
    the sum or product of the list it walks and nothing else: no expression is
    computed per element, so the loop reads the list and never rewrites it.
    """

    targets: set[str] = set()
    for statement in loop.body:
        if (
            isinstance(statement, ast.AugAssign)
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.op, ast.Mult | ast.Add)
            and isinstance(statement.value, ast.Name)
            and statement.value.id == element
        ):
            targets.add(statement.target.id)
            continue
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.BinOp)
            and isinstance(statement.value.op, ast.Mult | ast.Add)
        ):
            target = statement.targets[0]
            assert isinstance(target, ast.Name)
            operands = (statement.value.left, statement.value.right)
            held = [
                item for item in operands if isinstance(item, ast.Name) and item.id == target.id
            ]
            payloads = [
                item for item in operands if isinstance(item, ast.Name) and item.id == element
            ]
            if len(held) == 1 and len(payloads) == 1:
                targets.add(target.id)
                continue
        return None
    return frozenset(targets) or None


def _apply_list_accumulation_loop(
    loop: ast.For, env: dict[str, _Value], ctx: _TraceContext
) -> bool:
    """An accumulation loop that consumes a recognized list element by element.

    ``for v in vals: total = total + v`` over a column-values list is the
    counting loop spelling of ``sum(vals)``, and over a list of recognized
    per-element selectors it is the accumulation spelling. Either way the loop
    itself computes nothing per element, so it classifies nothing; the
    comprehension that built the list is what the trace reads, and the loop is
    what marks that comprehension as consumed.

    The list name must be bound exactly once in the whole module. A rebound
    name would leave which list this loop walks a question about execution
    order, which is the same reason a rebound name cannot be paired.
    """

    assert isinstance(loop.target, ast.Name)
    if not isinstance(loop.iter, ast.Name):
        return False
    name = loop.iter.id
    if name not in ctx.model.single_assignment:
        return False
    held = env.get(name)
    binding = ctx.model.single_bindings.get(name)
    if not (isinstance(held, _ColumnValues) or isinstance(binding, ast.ListComp)):
        return False
    targets = _elementwise_accumulation_targets(loop, loop.target.id)
    if targets is None:
        return False
    for target in targets:
        if isinstance(env.get(target), _Rows | _ColumnValues | _Paired | _IndexedPair | _EmptyList):
            # An accumulator that already holds a row set or a list is not a
            # number being summed; rebinding it here is outside this shape.
            return False
    for target in targets:
        env[target] = _Scalar()
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
        selectors = _selector_comparisons(payload, ctx)
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
    single_assignment = _single_assignment_names(tree)
    paths = _path_call_model(tree, functions, single_assignment)
    write_call_ids = paths.writes
    helper_write_calls = _helper_write_call_sites(tree, functions, write_call_ids, paths.names)
    reaching = _report_reaching_names(
        tree, functions, write_call_ids, helper_write_calls, reachable
    )
    constants, selector_constants = _module_constants(tree, single_assignment)
    return _ModuleModel(
        imports=imports,
        functions=functions,
        opaque_callables=frozenset(opaque),
        reachable_functions=reachable,
        dead_functions=dead,
        write_call_ids=write_call_ids,
        reaching=frozenset(reaching),
        accumulated=frozenset(_accumulated_comprehension_ids(tree)),
        constants=constants,
        selector_constants=selector_constants,
        single_assignment=single_assignment,
        single_bindings=_single_bindings(tree, single_assignment),
        read_chain_call_ids=paths.read_chains,
        mkdir_call_ids=paths.mkdirs,
        helper_write_calls=helper_write_calls,
        open_handle_names=_open_handle_names(tree, functions, imports, single_assignment),
    )


def _single_bindings(tree: ast.Module, single_assignment: frozenset[str]) -> dict[str, ast.expr]:
    """The one module-level expression each single-assignment name is bound to."""

    bindings: dict[str, ast.expr] = {}
    for statement in tree.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in single_assignment
        ):
            bindings[statement.targets[0].id] = statement.value
    return bindings


def _binding_counts(tree: ast.Module) -> Counter[str]:
    """How often each name is bound anywhere in the module, under any form.

    Every binding form counts: assignment, augmented and annotated
    assignment, loop and comprehension targets, ``with`` targets, function
    names, parameters, lambda parameters, imports, and ``global``
    declarations. A name bound twice is a name whose value at any point is a
    question about execution order, so it is neither a constant nor a
    pairable list.
    """

    counts: Counter[str] = Counter()
    for node in ast.walk(tree):
        for name in _binding_names(node):
            counts[name] += 1
    return counts


def _single_assignment_names(tree: ast.Module) -> frozenset[str]:
    return frozenset(name for name, count in _binding_counts(tree).items() if count == 1)


def _module_constants(
    tree: ast.Module, single_assignment: frozenset[str]
) -> tuple[dict[str, int | float | str], dict[str, int | float | str]]:
    """Module-level names that provably hold one value for the whole run.

    The first mapping is the literal one: assigned exactly once in the entire
    module, at module level, to a numeric or string literal or the negation of
    a numeric one. A second binding anywhere -- a rebinding, a parameter, a
    loop target, an import -- disqualifies it, so no execution order decides
    what the name means. The builtin-shadowing ban already keeps these names
    off builtins.

    The second mapping adds the exact-numeric constructors ``Fraction(a, b)``
    and ``Decimal('s')`` over literal arguments, read by the selector-constant
    grammar. They resolve in selector branch positions only. A ``Fraction`` is
    the ordinary way to write an emission weight exactly, but it is not the
    literal ``1`` that the recode vocabulary tests for, and letting it stand
    in that position would read ``WEIGHT - x`` as an involution on the
    strength of a constructor call.
    """

    constants: dict[str, int | float | str] = {}
    selectors: dict[str, int | float | str] = {}
    for statement in tree.body:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            continue
        name = statement.targets[0].id
        if name not in single_assignment:
            continue
        value = _literal_value(statement.value)
        if value is not None:
            constants[name] = value
            selectors[name] = value
            continue
        exact = _selector_constant(statement.value, {})
        if exact is not None:
            selectors[name] = exact
    return constants, selectors


def _literal_value(node: ast.expr) -> int | float | str | None:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return None
        if isinstance(node.value, int | float | str):
            return node.value
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _literal_value(node.operand)
        if isinstance(inner, int | float):
            return -inner
    return None


def _constant_name_value(node: ast.expr, constants: dict[str, int | float | str]) -> object | None:
    return constants.get(node.id) if isinstance(node, ast.Name) else None


def _is_open_call(
    node: ast.expr, functions: dict[str, ast.FunctionDef], imports: dict[str, str]
) -> bool:
    """The ``open()`` constructions this trace models, as call or context manager."""

    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id == "open":
        return node.func.id not in functions and node.func.id not in imports
    return isinstance(node.func, ast.Attribute) and node.func.attr == "open"


def _open_handle_names(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef],
    imports: dict[str, str],
    single_assignment: frozenset[str],
) -> frozenset[str]:
    """Names whose one binding in the whole module is a modelled ``open()``.

    A file handle is admitted as a receiver for exactly one method, so the
    name has to denote one handle for the whole run. Requiring the single
    binding keeps that decidable without an execution order: a name bound a
    second time anywhere, under any form, is not a handle here.
    """

    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and _is_open_call(node.value, functions, imports)
        ):
            names.add(node.targets[0].id)
        elif (
            isinstance(node, ast.withitem)
            and isinstance(node.optional_vars, ast.Name)
            and _is_open_call(node.context_expr, functions, imports)
        ):
            names.add(node.optional_vars.id)
    return frozenset(names & single_assignment)


def _is_handle_close_call(call: ast.Call, ctx: _TraceContext) -> bool:
    """``handle.close()`` on a name the modelled ``open()`` pattern bound.

    Closing a staged input handle returns ``None`` and reads no row value, so
    the result is opaque and nothing this trace follows can flow through it.
    Only ``close`` is admitted; ``read`` and ``readlines`` deliver the file's
    contents and would need the reader-chain semantics this form omits.
    """

    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "close"
        and not call.args
        and not call.keywords
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id in ctx.model.open_handle_names
    )


def _is_read_text_call(node: ast.expr, path_names: set[str]) -> bool:
    """``<path-like>.read_text(...)`` with string-literal keyword arguments.

    The keyword arguments of ``read_text`` are encoding and error policy; a
    literal string cannot compute anything. A positional argument, a
    non-literal keyword, or a receiver that is not provably a filesystem
    path leaves the call unrecognized.
    """

    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "read_text"
        and not node.args
        and all(
            keyword.arg is not None
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
            for keyword in node.keywords
        )
        and _is_path_like(node.func.value, path_names)
    )


def _is_splitlines_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "splitlines"
        and not node.args
        and not node.keywords
    )


def _is_mkdir_call(node: ast.AST) -> bool:
    """``<receiver>.mkdir(...)`` with literal keyword arguments and no positional ones.

    ``parents`` and ``exist_ok`` are the whole keyword vocabulary a results
    directory needs, and a literal cannot compute anything. A positional
    argument, or a keyword whose value is an expression, is a call this shape
    does not describe.
    """

    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "mkdir"
        and not node.args
        and all(
            keyword.arg is not None and isinstance(keyword.value, ast.Constant)
            for keyword in node.keywords
        )
    )


@dataclass(frozen=True)
class _PathCalls:
    """Every path-receiver call the module admits, by node identity."""

    writes: frozenset[int]
    mkdirs: frozenset[int]
    read_chains: frozenset[int]
    names: frozenset[str]
    parameters: dict[str, frozenset[str]]


class _PathScan:
    """Last-binding-wins tracking of the names that hold a filesystem path.

    One pass records every report write, every ``mkdir``, and every
    ``read_text`` chain call the module admits, because all three ask the same
    question of the same receiver. ``sink = Path(...)`` followed by ``sink =
    io.StringIO()`` leaves ``sink`` an in-memory buffer, and the write that
    follows publishes nothing.

    ``text_names`` carries the second half of the read-text chain rule the
    grammar has always stated: a name assigned exactly once from a
    ``read_text`` call holds that call's string, so ``.splitlines()`` on the
    name reads exactly what the inline chain reads.
    """

    def __init__(self, single_assignment: frozenset[str]) -> None:
        self._single_assignment = single_assignment
        self.writes: set[int] = set()
        self.mkdirs: set[int] = set()
        self.chains: set[int] = set()
        self.ever: set[str] = set()
        self.broken: set[str] = set()
        self.text_ever: set[str] = set()

    def _rebind(
        self,
        name: str,
        path_like: bool,
        text_like: bool,
        names: set[str],
        text_names: set[str],
    ) -> None:
        if path_like:
            names.add(name)
            self.ever.add(name)
        else:
            names.discard(name)
            self.broken.add(name)
        if text_like:
            text_names.add(name)
            self.text_ever.add(name)
        else:
            text_names.discard(name)

    def _visit(self, node: ast.AST, names: set[str], text_names: set[str]) -> None:
        if _is_write_call(node):
            assert isinstance(node, ast.Call)
            assert isinstance(node.func, ast.Attribute)
            if _is_path_like(node.func.value, names):
                self.writes.add(id(node))
        if _is_mkdir_call(node):
            assert isinstance(node, ast.Call)
            assert isinstance(node.func, ast.Attribute)
            if _is_path_like(node.func.value, names):
                self.mkdirs.add(id(node))
        if _is_read_text_call(node, names):
            self.chains.add(id(node))
        if _is_splitlines_call(node):
            assert isinstance(node, ast.Call)
            assert isinstance(node.func, ast.Attribute)
            receiver = node.func.value
            named = (
                isinstance(receiver, ast.Name)
                and receiver.id in text_names
                and receiver.id in self._single_assignment
            )
            if named or _is_read_text_call(receiver, names):
                self.chains.add(id(node))

    def scan(self, statements: list[ast.stmt], names: set[str], text_names: set[str]) -> None:
        for statement in statements:
            if isinstance(statement, ast.With | ast.AsyncWith):
                for item in statement.items:
                    if isinstance(item.optional_vars, ast.Name):
                        self._rebind(
                            item.optional_vars.id,
                            _is_path_like(item.context_expr, names),
                            False,
                            names,
                            text_names,
                        )
                self.scan(list(statement.body), names, text_names)
                continue
            if isinstance(statement, ast.If | ast.For | ast.While):
                self.scan(list(statement.body), names, text_names)
                self.scan(list(statement.orelse), names, text_names)
                continue
            for inner in ast.walk(statement):
                self._visit(inner, names, text_names)
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                self._rebind(
                    statement.targets[0].id,
                    _is_path_like(statement.value, names),
                    _is_read_text_call(statement.value, names),
                    names,
                    text_names,
                )
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                bound = statement.value
                self._rebind(
                    statement.target.id,
                    bound is not None and _is_path_like(bound, names),
                    bound is not None and _is_read_text_call(bound, names),
                    names,
                    text_names,
                )


def _path_call_model(
    tree: ast.Module, functions: dict[str, ast.FunctionDef], single_assignment: frozenset[str]
) -> _PathCalls:
    """The path-receiver calls of one module, module level first then bodies.

    A function body cannot be placed in the module's binding order, so it sees
    only the names that were path-like and never rebound to anything else,
    plus its own parameters that every call site proved path-like.
    """

    scan = _PathScan(single_assignment)
    module_names: set[str] = set()
    module_text: set[str] = set()
    scan.scan(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        module_names,
        module_text,
    )
    stable = frozenset((module_names | scan.ever) - scan.broken)
    stable_text = frozenset((module_text | scan.text_ever) & single_assignment)
    parameters = _path_like_parameters(tree, functions, stable)
    for function in (item for item in tree.body if isinstance(item, ast.FunctionDef)):
        scan.scan(
            list(function.body),
            set(stable) | set(parameters.get(function.name, frozenset())),
            set(stable_text),
        )
    return _PathCalls(
        writes=frozenset(scan.writes),
        mkdirs=frozenset(scan.mkdirs),
        read_chains=frozenset(scan.chains),
        names=stable,
        parameters=parameters,
    )


def _path_like_parameters(
    tree: ast.Module, functions: dict[str, ast.FunctionDef], stable: frozenset[str]
) -> dict[str, frozenset[str]]:
    """Parameters a helper may treat as filesystem paths, proven at the call sites.

    A loader that reads ``source_path.read_text(...)`` and a writer that calls
    ``target_path.write_text(...)`` say nothing on their own about what they
    were handed: ``StringIO`` answers to both. The proof is the same
    bind-and-check the helper-parity rule uses -- bind every call site's
    arguments to the parameters and keep only the parameters every one of
    those sites proved path-like -- and it is required, so a helper nothing
    calls, or one whose name escapes call position and could be called through
    an alias, proves nothing.
    """

    escaping, _ = _name_occurrences(tree)
    sites: dict[str, list[ast.Call]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in functions:
                sites.setdefault(node.func.id, []).append(node)
    proven: dict[str, frozenset[str]] = {}
    for name, function in functions.items():
        if name in escaping or name not in sites:
            continue
        if (
            function.args.posonlyargs
            or function.args.kwonlyargs
            or function.args.vararg
            or function.args.kwarg
            or function.args.defaults
        ):
            continue
        parameters = [item.arg for item in function.args.args]
        if len(set(parameters)) != len(parameters):
            continue
        candidates = set(parameters) & _path_receiver_parameters(function)
        for call in sites[name]:
            bound = _bind_arguments(parameters, call)
            if bound is None:
                candidates = set()
                break
            candidates &= {
                parameter
                for parameter, argument in bound.items()
                if _is_path_like(argument, set(stable))
            }
        if candidates:
            proven[name] = frozenset(candidates)
    return proven


def _bind_arguments(parameters: list[str], call: ast.Call) -> dict[str, ast.expr] | None:
    """Positional and keyword binding of one call onto a plain parameter list."""

    if len(call.args) > len(parameters):
        return None
    bound: dict[str, ast.expr] = {}
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = argument
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return None
        bound[keyword.arg] = keyword.value
    if set(bound) != set(parameters):
        return None
    return bound


def _path_receiver_parameters(function: ast.FunctionDef) -> set[str]:
    """Parameters the body actually uses as a filesystem receiver."""

    found: set[str] = set()
    for node in ast.walk(function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in {"read_text", "write_text", "open"}:
            continue
        receiver: ast.expr = node.func.value
        while isinstance(receiver, ast.Attribute):
            receiver = receiver.value
        if isinstance(receiver, ast.Name):
            found.add(receiver.id)
    return found


def _helper_write_call_sites(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef],
    write_call_ids: frozenset[int],
    stable: frozenset[str],
) -> dict[int, ast.expr]:
    """Calls to a helper whose only job is to write the report, and their payloads.

    ``write_report(REPORT_PATH, report_text)`` publishes exactly what the
    inline ``REPORT_PATH.write_text(report_text)`` publishes, so it has to seed
    report-reachability the same way; routing the write through a helper
    otherwise hides the report plane from the trace entirely. The helper's body
    is one return of a recognized write on one parameter, whose payload is an
    inert expression over the other, and the call site must hand it a provably
    path-like argument.
    """

    helpers: dict[str, tuple[int, int]] = {}
    for name, function in functions.items():
        shape = _report_write_helper_shape(function, write_call_ids)
        if shape is not None:
            helpers[name] = shape
    if not helpers:
        return {}
    calls: dict[int, ast.expr] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        shape = helpers.get(node.func.id)
        if shape is None:
            continue
        path_index, payload_index = shape
        parameters = [item.arg for item in functions[node.func.id].args.args]
        bound = _bind_arguments(parameters, node)
        if bound is None:
            continue
        if not _is_path_like(bound[parameters[path_index]], set(stable)):
            continue
        payload = bound[parameters[payload_index]]
        if not isinstance(payload, ast.Name):
            continue
        calls[id(node)] = payload
    return calls


def _report_write_helper_shape(
    function: ast.FunctionDef, write_call_ids: frozenset[int]
) -> tuple[int, int] | None:
    """``(path parameter index, payload parameter index)`` of a write helper, or None.

    The body is one return of ``path_parameter.write_text(<payload>)``, with
    at most the inert bare-call statements the whitelist admits before it, and
    the payload reads the other parameter and nothing else. Two plain
    parameters exactly: the shape is a path and the text to put at it.
    """

    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
        or function.args.defaults
        or len(function.args.args) != 2
    ):
        return None
    parameters = [item.arg for item in function.args.args]
    if len(set(parameters)) != 2:
        return None
    statements = [
        item
        for item in _flatten_statements(function.body)
        if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant | ast.Call))
    ]
    if len(statements) != 1 or not isinstance(statements[0], ast.Return):
        return None
    returned = statements[0].value
    if not (isinstance(returned, ast.Call) and id(returned) in write_call_ids):
        return None
    if not (isinstance(returned.func, ast.Attribute) and returned.func.attr == "write_text"):
        return None
    if not isinstance(returned.func.value, ast.Name) or not returned.args:
        return None
    path_parameter = returned.func.value.id
    if path_parameter not in parameters:
        return None
    payload = returned.args[0]
    if not _print_argument(payload):
        return None
    free = {inner.id for inner in ast.walk(payload) if isinstance(inner, ast.Name)}
    payload_parameter = next(item for item in parameters if item != path_parameter)
    if free != {payload_parameter}:
        return None
    return parameters.index(path_parameter), parameters.index(payload_parameter)


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
        if not (
            isinstance(statement.iter, ast.Name) or id(statement.iter) in ctx.recognized_pairings
        ):
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

    return _is_open_call(node, ctx.functions, ctx.model.imports)


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
    if isinstance(value, ast.Call) and _is_handle_close_call(value, ctx):
        # Closing the staged input handle, the one file-handle method this
        # trace models. It computes nothing and returns None.
        return False
    if isinstance(value, ast.Call) and id(value) in ctx.model.mkdir_call_ids:
        # Creating the results directory a report is written into. The
        # receiver is a proven filesystem path, every argument is a literal,
        # and the call returns None, so nothing this trace follows passes
        # through it.
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
    if not _is_builtin_name("print", ctx):
        return False
    for keyword in call.keywords:
        # ``sep``, ``end``, and ``flush`` only change how the same arguments
        # are laid out on standard output. ``file`` redirects the write to a
        # receiver this trace has not proven, so it stays outside the form.
        if keyword.arg not in {"sep", "end", "flush"}:
            return False
        if not isinstance(keyword.value, ast.Constant):
            return False
        if not (isinstance(keyword.value.value, str) or keyword.value.value is None):
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
        # A zip is admitted here only when the trace itself recognized it as a
        # pairing of two column-values lists of one row set. A zip of anything
        # else stays outside the whitelist.
        or id(iterable) in ctx.recognized_pairings
        or (
            isinstance(iterable, ast.Call)
            and _call_name(iterable) == "list"
            and len(iterable.args) == 1
            and id(iterable.args[0]) in ctx.recognized_pairings
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
    if id(call) in model.read_chain_call_ids:
        # ``<path-like>.read_text(...)`` with string-literal keywords, and the
        # ``.splitlines()`` that closes it. The pre-pass proved the receiver
        # is a filesystem path under last-binding-wins tracking, so this reads
        # a staged file into strings and computes nothing else.
        return True
    if _is_handle_close_call(call, ctx):
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
        if not isinstance(node, ast.Compare):
            continue
        if id(node) in ctx.recognized_compares or id(node) in unreachable_regions:
            continue
        if len(node.ops) != 1:
            # ``a == b == 1`` is outside every classifier, and letting a
            # recognized decoy count answer for it was a demonstrated
            # wrong-answer route. A chained comparison over two distinct
            # staged extractions, or over operands reading different
            # names, abstains; a plain range check over one name passes.
            operands = [node.left, *node.comparators]
            extractions = {
                found
                for found in (_staged_extraction(item, ctx.constants) for item in operands)
                if found
            }
            if len(extractions) > 1:
                return True
            named = [_operand_names(item) for item in operands]
            named = [item for item in named if item]
            if len(named) > 1 and len(set(named)) > 1:
                return True
            continue
        if not isinstance(node.ops[0], ast.Eq | ast.NotEq):
            continue
        left = _staged_extraction(node.left, ctx.constants)
        right = _staged_extraction(node.comparators[0], ctx.constants)
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


def _staged_extraction(
    node: ast.expr, constants: dict[str, int | float | str]
) -> tuple[str, str] | None:
    """The staged extraction anywhere inside an operand's subtree, if any.

    This is a belt, so over-detection is safe (it can only force an
    abstention) and structural recursion is not: a keyword argument on a
    cast (``int(x, base=10)``) hid the operand from the previous
    shape-following version, a demonstrated wrong answer. The whole subtree
    is walked instead.
    """

    for inner in ast.walk(node):
        if not (isinstance(inner, ast.Subscript) and isinstance(inner.value, ast.Name)):
            continue
        if isinstance(inner.slice, ast.Constant) and isinstance(inner.slice.value, str):
            return (inner.value.id, inner.slice.value)
        # A column named by a module constant is the same extraction written
        # with a name; the belt has to see it too, and over-detection here can
        # only force an abstention.
        column = _constant_name_value(inner.slice, constants)
        if isinstance(column, str):
            return (inner.value.id, column)
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
        if (
            isinstance(node, ast.For)
            and isinstance(node.target, ast.Name)
            and isinstance(node.iter, ast.Name)
            and _elementwise_accumulation_targets(node, node.target.id) is not None
        ):
            # ``for weight in weights: total = total + weight`` is the loop
            # spelling of ``sum(weights)``, and it consumes the comprehension
            # bound to ``weights`` exactly as the call does.
            consumed.add(node.iter.id)
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


def _write_payloads(
    node: ast.AST,
    write_call_ids: frozenset[int],
    helper_write_calls: dict[int, ast.expr],
) -> list[ast.expr]:
    """The text every recognized report write in a subtree publishes.

    A direct write publishes its first argument; a call to a recognized
    report-write helper publishes the argument that reaches that helper's
    payload parameter.
    """

    payloads: list[ast.expr] = []
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        if id(inner) in write_call_ids:
            payloads.append(inner.args[0])
        routed = helper_write_calls.get(id(inner))
        if routed is not None:
            payloads.append(routed)
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
    helper_write_calls: dict[int, ast.expr],
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
            return
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
            # An accumulation loop's total depends on the list it walks, not
            # only on the loop variable that names one element of it.
            for inner in node.body:
                if isinstance(inner, ast.AugAssign) and isinstance(inner.target, ast.Name):
                    _depend(inner.target.id, [node.iter])
                elif (
                    isinstance(inner, ast.Assign)
                    and len(inner.targets) == 1
                    and isinstance(inner.targets[0], ast.Name)
                ):
                    target = inner.targets[0]
                    assert isinstance(target, ast.Name)
                    _depend(target.id, [node.iter])

    def _collect(statements: list[ast.stmt], *, seeding: bool) -> None:
        for statement in _flatten_statements(statements):
            if seeding:
                for payload in _write_payloads(statement, write_call_ids, helper_write_calls):
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
