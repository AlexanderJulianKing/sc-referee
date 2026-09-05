from __future__ import annotations

import ast
import functools
import hashlib
import inspect
import json
import runpy
import sys
import types
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen_v3
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_4 import (
    _CLOSED_REASONS,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_4 import (
    ADMISSION_KINDS,
    admission_census,
    admission_spans,
    recording_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_comprehension_v3_4 import (
    admitted_comprehensions,
    module_sequences,
    normalize_comprehensions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
    _ENUMERATE_COUNTER,
    _complete_rows,
    _enumerate_is_the_unshadowed_builtin,
    _module_sequences,
    _positions_for,
    _static_bool,
    admitted_caps,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowResult,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v33,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v34,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_4/prototype-sweep").resolve()
_PINNED = {
    "instrument_results.json": "ee90ff2717d244cffd5faa6372a0fe04f81d28d2c76044ced9317b2756168c86",
    "results.json": "2bf626534a513e951e1c8a559a2538594f6dbb60e6bfda8e0787e0cd704a3cf2",
    "MANIFEST.json": "e4236167657801613b79f55b1a57edeef770da4f3fdf0bf261d6f1673ff15790",
}
_P3_KEY = "E17:P3:a2e031f79e31c80fd900"
_P6_KEY = "E17:P6:b4e507c4b55954752f14"

# The two correct-analysis rows on which the final implementation is deliberately STRICTER than
# the design prototype.  The prototype spliced normalized source text, so its AP recognizer read
# the normalized bytes; production supplies the normalization as a graph fact only and never
# rewrites source, so its AP recognizer reads the original bytes and the fold is not resolved.
# Both rows stay non-candidates and byte-identical to their frozen 3.3 abstention, which is the
# safe direction of the asymmetric prototype/final fidelity rule in design section 0.3.
_STRICTER_THAN_PROTOTYPE = {
    "correct-comprehension-corrected-family": ["abstain", "unresolved-decision-threshold"],
    "correct-terminal-verdict-rebound-into-name": ["abstain", "unresolved-decision-threshold"],
}

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_ROOT / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
    _catalog = runpy.run_path(str(_ROOT / "fixture_catalog.py"))
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness


@functools.cache
def _catalog_population() -> tuple[tuple[Any, ...], frozenset[str]]:
    """Build the 245-row catalog once per process, on first use rather than at import.

    Building it runs `harness.all_cases`, which baselines all 170 evidence sources through the
    shipped 3.3 analyzer and anchors each against the frozen 3.3 prototype row.  That evidence
    work is unchanged; only its timing moves, from module import to the first test that asks
    for a fixture.  Collection needs fixture *names*, and the byte-pinned `results.json` below
    already carries one row per fixture in catalog order, so pytest can collect this file
    without executing anything.
    """

    previous = sys.modules.pop("harness", None)
    sys.modules["harness"] = _harness_module
    try:
        fixtures = tuple(_catalog["all_fixtures"]())
        new_names = frozenset(item.name for item in _catalog["new_fixtures"]())
    finally:
        sys.modules.pop("harness", None)
        if previous is not None:
            sys.modules["harness"] = previous
    return fixtures, new_names


def _fixtures() -> tuple[Any, ...]:
    return _catalog_population()[0]


def _new_fixture_names() -> frozenset[str]:
    return _catalog_population()[1]


# `reference_case` rescans every case directory on each call, and the round-3 and round-4
# oracles ask for the same two keys a few hundred times between them.  The lookup is pure,
# so memoizing it is a runtime trim and not a change of evidence.
_REFERENCE_CASE = functools.lru_cache(maxsize=None)(
    cast("Callable[[str], Any]", _harness["reference_case"])
)
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[MultipleTestingDataflowResult], Any], _harness["classify"])
_RESULTS = json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))
_PROTOTYPE_FIXTURE_ROWS = {row["name"]: row for row in _RESULTS["fixtures"]}
# The collection-time populations.  `results.json` is byte-pinned immediately above and carries
# one row per fixture, in catalog order, with the same labels the catalog carries.  The census
# test compares the two row by row, so the catalog stays the authority for what a fixture is
# while collection itself stays free of analyzer work.
_PINNED_FIXTURE_ROWS = tuple(_RESULTS["fixtures"])
_PINNED_FIXTURE_NAMES = tuple(str(row["name"]) for row in _PINNED_FIXTURE_ROWS)
_PINNED_CORRECT_NAMES = tuple(
    str(row["name"]) for row in _PINNED_FIXTURE_ROWS if row["correct_analysis"]
)
_INSTRUMENT = json.loads((_ROOT / "instrument_results.json").read_text(encoding="utf-8"))

# The round-1 audit-fix oracle lives outside the prototype sweep, whose manifest bytes are
# pinned above and may not carry a post-hoc fixture.
_AUDIT_FIX_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r1-oracle"
).resolve()
_AUDIT_FIX_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_ORACLE = json.loads((_AUDIT_FIX_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_AUDIT_FIX_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_ORACLE["rows"])
_AUDIT_FIX_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_ROWS}
_MUTATED_SEQUENCE_ROWS = (
    "correct-ap-selection-sequence-direct-extend",
    "correct-ap-selection-sequence-alias-extend",
    "correct-ap-selection-sequence-alias-augmented-assign",
    "correct-ap-selection-sequence-alias-slice-assign",
)
_SHADOWED_ENUMERATE_ROWS = (
    "shadowed-enumerate-definition-agreeing",
    "correct-ap-shadowed-enumerate-definition-diverging",
)

# The round-2 audit-fix oracle: the comprehension lane's sequence-object closure, the container
# display residual left open by round 1, and the collected-name clause evaded through an alias.
_AUDIT_FIX_R2_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r2-oracle"
).resolve()
_AUDIT_FIX_R2_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_R2_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_R2_ORACLE = json.loads(
    (_AUDIT_FIX_R2_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_AUDIT_FIX_R2_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_R2_ORACLE["rows"])
_AUDIT_FIX_R2_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_R2_ROWS}
_ESCAPED_SEQUENCE_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R2_ROWS
    if row["expected_gate"] == "sequence-object-stability"
)
_R2_MOVEMENT_ROWS = {
    "positive-comprehension-e17-p3-unaltered": ("candidate", "none", (), 6),
    "positive-comprehension-sequence-alias-without-mutation": ("candidate", "none", (), 6),
    "positive-ap-e17-p6-unaltered": ("candidate", "strict_subset", (0, 1, 2), 7),
}

# The round-3 audit-fix oracle: the classification-path closure.  Rounds 1 and 2 withheld a 3.4
# admission; round 3 refuses a classification the byte-frozen 3.3 pipeline reaches on its own.
_AUDIT_FIX_R3_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r3-oracle"
).resolve()
_AUDIT_FIX_R3_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_R3_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_R3_ORACLE = json.loads(
    (_AUDIT_FIX_R3_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_AUDIT_FIX_R3_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_R3_ORACLE["rows"])
_AUDIT_FIX_R3_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_R3_ROWS}
_COLLECTION_ALIAS_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R3_ROWS
    if row["expected_gate"] == "record-collection-alias"
)
_R3_MOVEMENT_ROWS = {
    "positive-comprehension-e17-p3-unaltered": ("candidate", "none", (), 6),
    "positive-ap-e17-p6-unaltered": ("candidate", "strict_subset", (0, 1, 2), 7),
    "positive-explicit-loop-uncorrected-family": ("candidate", "none", (), 6),
    "positive-explicit-loop-uncorrected-family-unrelated-alias": ("candidate", "none", (), 6),
    "positive-explicit-loop-collection-alias-reported-not-stored": ("candidate", "none", (), 6),
    "positive-explicit-loop-covered-family-with-read-only-alias": (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    ),
}


# The round-4 audit-fix oracle: the record-derived binding closure.  Round 3 followed the bare
# Name-to-Name alias edges that make a second *name for the collection*; round 4 enumerates every
# binding that reaches a *record inside it*, which is how the reported blocker got through.
_AUDIT_FIX_R4_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r4-oracle"
).resolve()
_AUDIT_FIX_R4_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_R4_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_R4_ORACLE = json.loads(
    (_AUDIT_FIX_R4_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_AUDIT_FIX_R4_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_R4_ORACLE["rows"])
_AUDIT_FIX_R4_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_R4_ROWS}
_RECORD_DERIVED_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R4_ROWS
    if row["expected_gate"] == "record-derived-binding"
)
# Round 4 left exactly one correct-analysis row accused: the record handed to a helper storing
# through its own differently named parameter.  Round 5 closes it, so the round-4 residual set is
# now empty and the row is pinned again in the round-5 oracle as the confirmed probe.
_R4_CLOSED_IN_ROUND_5 = {"correct-record-in-helper-distinct-parameter-name"}
_R4_OPEN_RESIDUAL: set[str] = set()
# The round-4 oracle rows the round-5 closure moves, as (round-4 pin, round-5 disposition).  The
# oracle files are evidence and stay unedited: the round-4 pin records what round 4 measured, and
# this map is where the move is declared, so a silent edit of either side fails.
_R5_MOVES_R4_ROWS: dict[str, tuple[tuple[str, str, tuple[int, ...], int | None], ...]] = {
    "correct-record-in-helper-distinct-parameter-name": (
        ("candidate", "none", (), 6),
        ("abstain", "pvalue-family-collection-unresolved", (), None),
    ),
}
_R4_READ_ONLY_ROWS = frozenset(
    name for name in _AUDIT_FIX_R4_SOURCES if name.startswith("positive-read-only-")
)
# The binding each fixture introduces, named rather than inferred from its outcome.
_R4_NAMED_BINDINGS = {
    "correct-iteration-items-unpack-record-store": {"record"},
    "correct-iteration-values-loop-record-store": {"record"},
    "correct-iteration-iter-values-record-store": {"record"},
    "correct-iteration-enumerate-values-record-store": {"record"},
    "correct-iteration-enumerate-items-nested-unpack-record-store": {"record"},
    "correct-iteration-zip-values-record-store": {"record"},
    "correct-iteration-sorted-items-record-store": {"record"},
    "correct-iteration-sorted-values-keyed-record-store": {"record"},
    "correct-iteration-list-values-record-store": {"record"},
    "correct-iteration-reversed-list-values-record-store": {"record"},
    "correct-iteration-tuple-values-record-store": {"record"},
    "correct-iteration-dict-copy-items-record-store": {"record"},
    "correct-iteration-comprehension-target-record-store": {"record"},
    "correct-subscript-subscript-bound-record-store": {"record"},
    "correct-subscript-get-bound-record-store": {"record"},
    "correct-subscript-setdefault-bound-record-store": {"record"},
    "correct-subscript-list-values-index-record-store": {"record"},
    "correct-walrus-get-bound-record-store": {"record"},
    "correct-walrus-container-loop-record-store": {"family", "record"},
    "correct-chained-alias-items-unpack-record-store": {"adjusted", "record"},
    "correct-chained-container-name-then-loop-record-store": {"family", "record"},
    "correct-chained-record-rebound-to-a-third-name-record-store": {"record", "target"},
    "correct-chained-nested-loop-inside-items-unpack-record-store": {"record"},
    "correct-invented-collection-copy-method-items-record-store": {"copied", "record"},
    "correct-invented-generator-expression-consumed-later-record-store": {
        "entry",
        "pending",
        "record",
    },
    "correct-invented-record-update-method-record-store": {"record"},
    "correct-invented-record-dunder-setitem-record-store": {"record"},
    "correct-invented-record-subscript-augmented-assign-record-store": {"record"},
    "correct-invented-record-escapes-into-a-container-display-record-store": {"record"},
    "partial-next-iter-values-single-record-store": {"first"},
    "correct-record-in-helper-shared-parameter-name": {"record"},
}
_R4_MOVEMENT_ROWS = {
    "positive-comprehension-e17-p3-unaltered": ("candidate", "none", (), 6),
    "positive-ap-e17-p6-unaltered": ("candidate", "strict_subset", (0, 1, 2), 7),
    "positive-explicit-loop-uncorrected-family": ("candidate", "none", (), 6),
    "positive-read-only-items-loop-summary": ("candidate", "none", (), 6),
    "positive-read-only-values-loop-summary": ("candidate", "none", (), 6),
    "positive-read-only-enumerate-values-loop-summary": ("candidate", "none", (), 6),
    "positive-read-only-items-loop-key-method-call": ("candidate", "none", (), 6),
    "positive-read-only-items-loop-record-verdict": ("candidate", "none", (), 6),
    "positive-read-only-list-values-loop-summary": ("candidate", "none", (), 6),
    "positive-covered-family-with-read-only-record-iteration": (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    ),
}


# The round-5 audit-fix oracle: the project-local storing-helper closure.  Round 4 enumerates
# every binding a correction store can travel through inside one scope; round 5 follows the store
# into another scope, which is the one route round 4 named and left open.
_AUDIT_FIX_R5_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r5-oracle"
).resolve()
_AUDIT_FIX_R5_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_R5_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_R5_ORACLE = json.loads(
    (_AUDIT_FIX_R5_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_AUDIT_FIX_R5_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_R5_ORACLE["rows"])
_AUDIT_FIX_R5_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_R5_ROWS}
_HELPER_STORE_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R5_ROWS
    if row["expected_gate"] == "helper-parameter-store"
)
# The one correct-analysis row round 5 left accused: this recognizer reads a single source file,
# so a helper defined in a sibling project module resolved to nothing it could read.  Round 6
# decides it without widening what the recognizer reads -- a callee it can neither resolve nor
# allowlist is a mutation of what it is handed -- so the round-5 residual set is now empty.
_R5_CLOSED_IN_ROUND_6 = {"correct-record-in-helper-imported-from-a-sibling-module"}
_R5_OPEN_RESIDUAL: set[str] = set()
# The name each refused row hands to a storing helper, named rather than inferred from its
# outcome.  `results` is the collection itself, which the closure checks for capture even though
# its own stores are excluded from the mutation census.
_R5_CAPTURING_ROWS = {
    "correct-record-in-helper-distinct-parameter-name": {"record"},
    "correct-record-in-helper-storing-through-a-local-alias": {"record"},
    "correct-record-in-helper-storing-via-a-nested-helper": {"record"},
    "correct-record-in-helper-storing-conditionally": {"record"},
    "correct-record-in-helper-mutating-via-update": {"record"},
    "correct-record-in-helper-defined-after-its-use": {"record"},
    "correct-record-in-helper-keyword-argument": {"record"},
    "correct-record-in-helper-through-star-args-forwarding": {"record"},
    "correct-record-in-helper-through-double-star-forwarding": {"record"},
    "correct-record-in-lambda-bound-to-a-name": {"record"},
    "correct-record-in-lambda-applied-through-map": {"results"},
    "correct-record-in-static-method-of-a-project-local-class": {"record"},
    "correct-collection-in-helper-iterating-internally": {"results"},
    "correct-values-view-in-helper-iterating-internally": {"results"},
    "boundary-read-only-helper-calling-a-method-on-its-parameter": {"record"},
}
# The rows whose every call over a record-derived name is a read or a builtin.
_R5_NON_CAPTURING_ROWS = frozenset(
    {
        "positive-read-only-helper-on-uncorrected-family",
        "positive-read-only-helper-on-the-whole-collection",
        "positive-builtin-calls-over-record-derived-names",
        "positive-explicit-loop-uncorrected-family",
        "positive-covered-family-with-a-read-only-helper",
        "positive-comprehension-e17-p3-unaltered",
        "positive-ap-e17-p6-unaltered",
    }
)
_R5_MOVEMENT_ROWS = {
    "positive-comprehension-e17-p3-unaltered": ("candidate", "none", (), 6),
    "positive-ap-e17-p6-unaltered": ("candidate", "strict_subset", (0, 1, 2), 7),
    "positive-explicit-loop-uncorrected-family": ("candidate", "none", (), 6),
    "positive-read-only-helper-on-uncorrected-family": ("candidate", "none", (), 6),
    "positive-read-only-helper-on-the-whole-collection": ("candidate", "none", (), 6),
    "positive-builtin-calls-over-record-derived-names": ("candidate", "none", (), 6),
    "positive-covered-family-with-a-read-only-helper": (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    ),
}


# The round-6 audit-fix oracle: the call-disposition closure.  Round 5 read every callee it could
# not resolve as a non-capture; round 6 decides those calls in both directions, because the audit
# demonstrated a live false accusation and a live lost accusation on each side of that boundary.
_AUDIT_FIX_R6_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r6-oracle"
).resolve()
_AUDIT_FIX_R6_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_R6_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_R6_ORACLE = json.loads(
    (_AUDIT_FIX_R6_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_AUDIT_FIX_R6_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_R6_ORACLE["rows"])
_AUDIT_FIX_R6_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_R6_ROWS}
# The gates whose rows are complete correct Bonferroni passes the round-5 closure left accused.
_R6_FALSE_ACCUSATION_GATES = frozenset(
    {
        "unresolvable-callee-fail-closed",
        "callee-shadowing-census",
        "call-return-flow",
        "closure-definition-escape",
    }
)
_R6_CLOSED_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R6_ROWS
    if row["correct_analysis"] and row["expected_gate"] in _R6_FALSE_ACCUSATION_GATES
)
# The true accusations the round-5 closure lost, one per soundness fix and per half of rule D.
_R6_RECOVERED_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R6_ROWS
    if row["expected_gate"]
    in {
        "parameter-role-seeding",
        "starred-argument-binding",
        "scalar-subscript-argument",
        "dead-nested-definition",
        "shadowed-wrapper-resolution",
    }
    or (row["expected_gate"] == "parameter-rebinding" and row["expected_outcome"] == "candidate")
)
# The rows whose every call over a tracked name is a read, a builtin, or an allowlisted library
# API.  Each is one call away from the uncorrected baseline and must reach the same disposition.
_R6_READ_ONLY_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R6_ROWS
    if row["expected_gate"] == "read-only-allowlist"
)
# The costs round 6 pays, recorded rather than hidden.
_R6_COST_ROWS = {
    "boundary-helper-parameter-rebound-inside-a-branch": "a rebinding inside a branch",
    "boundary-overwritten-class-method": "a class body binding one method name twice",
    "boundary-read-only-helper-calling-keys-on-its-parameter": "the frozen receiver census",
    "boundary-read-only-helper-calling-items-on-its-parameter": "the frozen receiver census",
    "boundary-read-only-helper-calling-copy-on-its-parameter": "the frozen receiver census",
}
# The round-5 oracle rows the round-6 closure moves, as (round-5 pin, round-6 disposition).  The
# oracle files are evidence and stay unedited: the round-5 pin records what round 5 measured, and
# this map is where the move is declared, so a silent edit of either side fails.
_R6_MOVES_R5_ROWS: dict[str, tuple[tuple[str, str, tuple[int, ...], int | None], ...]] = {
    "correct-record-in-helper-imported-from-a-sibling-module": (
        ("candidate", "none", (), 6),
        ("abstain", "pvalue-family-collection-unresolved", (), None),
    ),
}
_R6_MOVEMENT_ROWS = {
    "positive-comprehension-e17-p3-unaltered": ("candidate", "none", (), 6),
    "positive-ap-e17-p6-unaltered": ("candidate", "strict_subset", (0, 1, 2), 7),
    "positive-explicit-loop-uncorrected-family": ("candidate", "none", (), 6),
    "positive-covered-family-with-a-library-call": (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    ),
}
# The name each refused false-accusation row hands to a call that writes into it, named here
# rather than inferred from the row's outcome.
_R6_CAPTURING_ROWS = {
    "correct-record-in-unbound-dict-update": {"record"},
    "correct-record-in-operator-setitem": {"record"},
    "correct-record-in-getattr-setitem": {"record"},
    "correct-record-in-functools-partial": {"record"},
    "correct-record-in-static-method-stored-in-a-name": {"record"},
    "correct-record-in-dict-dispatch-table": {"record"},
    "correct-record-in-lambda-stored-in-a-list": {"record"},
    "correct-record-in-decorator-supplied-wrapper": {"record"},
    "correct-record-in-setattr-property-setter": {"record"},
    "correct-record-in-pandas-apply-over-the-values-view": {"results"},
    "correct-record-in-helper-receiving-a-subscript-display": {"results"},
    "correct-record-in-helper-imported-from-a-sibling-module": {"record"},
    "correct-record-in-helper-beside-an-unrelated-parameter": {"record"},
    "correct-record-in-helper-beside-a-class-attribute": {"record"},
    "correct-record-in-helper-beside-a-second-nested-definition": {"record"},
    "correct-record-in-helper-beside-an-unused-nested-definition": {"record"},
    "correct-record-in-helper-defined-twice-conditionally": {"record"},
    "correct-record-in-helper-imported-then-defined": {"record"},
    "correct-record-in-a-nested-closure-over-the-collection": {"results"},
    "correct-record-in-a-default-argument-capture": {"record"},
    "correct-record-in-a-returned-nested-helper": {"record"},
}


# --- Round 7 ----------------------------------------------------------------------------------
#
# Round 6 fails closed on a callee it cannot resolve.  It did not fail closed on a value it cannot
# follow or on a callable it cannot resolve, and it keyed its library allowlist on the spelling of
# a name rather than on what the imports say the name is.  Round 7 makes the three sides uniform.
_AUDIT_FIX_R7_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r7-oracle"
).resolve()
_AUDIT_FIX_R7_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_R7_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_R7_ORACLE = json.loads(
    (_AUDIT_FIX_R7_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8")
)
_AUDIT_FIX_R7_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_R7_ORACLE["rows"])
_AUDIT_FIX_R7_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_R7_ROWS}
# The gates whose rows are complete correct Bonferroni passes the round-6 closure left accused and
# whose refusal this round's own rules produce, so the through-name reason authority applies.
_R7_FALSE_ACCUSATION_GATES = frozenset(
    {
        "value-flow-fail-closed",
        "lazy-display-return-flow",
        "callable-position-fail-closed",
        "callback-receiver-roots",
        "inherited-closure",
        "import-resolved-allowlist",
    }
)
_R7_CLOSED_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R7_ROWS
    if row["correct_analysis"] and row["expected_gate"] in _R7_FALSE_ACCUSATION_GATES
)
# The correct analyses an upstream gate declines before this closure is reached.  They may not be
# accused either, and each carries the reason its own gate gives rather than the sibling's.
_R7_UPSTREAM_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R7_ROWS
    if row["expected_gate"] == "earlier-gate-refusal"
)
# The true accusations the round-6 closure lost, one per recovered rule.
_R7_RECOVERED_ROWS = tuple(
    str(row["fixture_name"])
    for row in _AUDIT_FIX_R7_ROWS
    if row["expected_gate"]
    in {
        "read-only-allowlist",
        "mapping-key-freshness",
        "forwarding-decorator",
        "class-scope-resolution",
    }
)
# The costs round 7 pays, each inherited from an earlier round's rule and recorded not hidden.
_R7_COST_ROWS = {
    "boundary-unawaited-async-call": "a bare call to an async def runs no body",
    "boundary-lru-cache-decorated-read-only-helper": "an unreadable library decorator",
    "boundary-record-inserted-by-subscript-into-a-second-mapping": "the round-1 field escape",
    "boundary-read-only-helper-calling-values-on-its-parameter": "the frozen receiver census",
    "boundary-read-only-pandas-apply": "the never-allowlisted callee set",
}
# The round-6 and round-5 oracle rows the round-7 closure moves.  Both are empty: round 7 narrows
# the classification side without moving a single earlier oracle row, and the constants are here so
# that a later round declares a move rather than editing an oracle that is evidence.
_R7_MOVES_R6_ROWS: dict[str, tuple[tuple[str, str, tuple[int, ...], int | None], ...]] = {}
_R7_MOVES_R5_ROWS: dict[str, tuple[tuple[str, str, tuple[int, ...], int | None], ...]] = {}
_R7_MOVEMENT_ROWS = {
    "positive-comprehension-e17-p3-unaltered": ("candidate", "none", (), 6),
    "positive-ap-e17-p6-unaltered": ("candidate", "strict_subset", (0, 1, 2), 7),
    "positive-explicit-loop-uncorrected-family": ("candidate", "none", (), 6),
    "positive-covered-family-with-a-library-call": (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    ),
}
# The name each closed row hands to a call that writes into it, or that a store is written
# through, named here rather than inferred from the row's outcome.
_R7_CAPTURING_ROWS = {
    "correct-record-in-held-append-then-setitem": {"target"},
    "correct-record-in-held-extend-then-setitem": {"target"},
    "correct-record-in-a-set-display-then-iterated": {"target"},
    "correct-record-in-a-dict-display-values-view": {"target"},
    "correct-record-through-a-returned-generator-expression": {"target"},
    "correct-record-through-a-returned-lambda": {"target"},
    "correct-record-in-transform-through-a-storing-wrapper": {"results"},
    "correct-record-in-series-map-through-an-attribute-callable": {"results"},
    "correct-record-in-sorted-key-through-a-dict-get-callable": {"results"},
    "correct-record-in-map-through-an-identity-chain": {"results"},
    "correct-record-in-apply-through-a-storing-wrapper": {"results"},
    "correct-record-in-apply-through-an-attribute-callable": {"results"},
    "correct-record-in-apply-through-a-dict-get-callable": {"results"},
    "correct-record-in-apply-through-an-identity-chain": {"results"},
    "correct-record-in-apply-through-a-comprehension-callable": {"results"},
    "correct-record-in-apply-through-functools-partial": {"results"},
    "correct-record-in-a-json-namespace-masquerade": {"record"},
    "correct-record-in-an-aliased-storing-library-function": {"record"},
    "correct-record-in-a-writer-rebound-to-a-project-class": {"record"},
}


def _outcome_tuple(value: Any) -> tuple[str, str, tuple[int, ...], int | None]:
    return (
        value.state,
        value.reason_or_classification,
        tuple(value.corrected_positions),
        value.authorized_count,
    )


_CORPUS_INPUTS: dict[str, dict[str, Any]] = {}


def _corpus_outcome(case_key: str) -> tuple[str, str, tuple[int, ...], int | None]:
    """The shipped 3.4 row for one open-corpus case, by key."""

    if case_key not in _CORPUS_INPUTS:
        _CORPUS_INPUTS[case_key] = _INPUTS(_REFERENCE_CASE(case_key), None)
    values = dict(_CORPUS_INPUTS[case_key])
    content = cast(bytes, values.pop("content"))
    return _outcome_tuple(_CLASSIFY(analyze_v34(content, **values)))


def _run_source(case_key: str, source: bytes) -> tuple[Any, dict[str, int]]:
    """Execute the shipped 3.4 analyzer once and return its outcome and admission census."""

    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    with recording_admissions():
        result = analyze_v34(content, **values)
        census = admission_census()
    return _CLASSIFY(result), census


def _run_v33(case_key: str, source: bytes) -> Any:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    return _CLASSIFY(analyze_v33(content, **values))


@pytest.fixture(scope="session")
def executed_rows() -> dict[str, dict[str, Any]]:
    """Execute every one of the 245 fixture sources through the real shipped 3.4 analyzer."""

    rows: dict[str, dict[str, Any]] = {}
    for fixture in _fixtures():
        outcome, census = _run_source(fixture.case_key, fixture.source)
        rows[fixture.name] = {
            "fixture": fixture,
            "outcome": outcome,
            "census": census,
            "json": outcome.as_json(),
        }
    return rows


def test_pinned_prototype_evidence_is_immutable() -> None:
    assert {
        name: hashlib.sha256((_ROOT / name).read_bytes()).hexdigest() for name in _PINNED
    } == _PINNED


def test_fixture_census_and_correct_analysis_populations_are_exact() -> None:
    fixtures = _fixtures()
    new_fixture_names = _new_fixture_names()
    # The collection-time populations are read from the pinned prototype rows.  Nothing about
    # them is taken on trust: the catalog's own name, category and label for every row is
    # compared against the pinned row here, in order, so a divergence fails rather than
    # silently reshaping what the parametrized tests cover.
    assert [
        (
            item.name,
            item.category,
            item.correct_analysis,
            getattr(item, "refused_admission", None),
            getattr(item, "admitted", None),
        )
        for item in fixtures
    ] == [
        (
            str(row["name"]),
            str(row["category"]),
            bool(row["correct_analysis"]),
            row["refused_admission"],
            row["required_admission"],
        )
        for row in _PINNED_FIXTURE_ROWS
    ]
    assert len(fixtures) == 245
    assert len(new_fixture_names) == 42
    counts = Counter(item.category for item in fixtures)
    assert counts == {
        "frozen-v3-original": 48,
        "audit-fix-r1": 14,
        "audit-fix-r2": 4,
        "audit-fix-r3": 5,
        "b5-expression-variant": 63,
        "v3.1-laundering-adjacent": 16,
        "ap-v3.2": 20,
        "frozen-gatekeeping": 12,
        "terminal-positive": 3,
        "terminal-adversary": 10,
        "helper-positive": 1,
        "helper-adversary": 7,
        "comprehension-positive": 3,
        "comprehension-adversary": 11,
        "comprehension-fa-control": 2,
        "terminal-ifexp-rejected-grammar": 3,
        "iterator-positive": 3,
        "iterator-adversary": 5,
        "iterator-fa-control": 3,
        "cap-positive": 1,
        "cap-adversary": 8,
        "cap-fa-control": 1,
        "reason-routing-adversary": 2,
    }
    assert sum(item.correct_analysis for item in fixtures) == 194
    assert sum(item.correct_analysis for item in fixtures if item.name in new_fixture_names) == 11


@pytest.mark.parametrize("name", _PINNED_FIXTURE_NAMES)
def test_all_245_fixture_rows_execute(name: str, executed_rows: dict[str, dict[str, Any]]) -> None:
    row = executed_rows[name]
    expected = _STRICTER_THAN_PROTOTYPE.get(name, _PROTOTYPE_FIXTURE_ROWS[name]["outcome"])
    assert row["json"] == expected


@pytest.mark.parametrize("name", sorted(_STRICTER_THAN_PROTOTYPE))
def test_named_strictness_residual_is_never_an_accusation(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """The two rows where production abstains and the prototype covered stay non-candidates.

    The gate is directional: if production ever became looser than this pin, or produced a
    candidate here, the assertion fails.  A `covered` prototype row and an `abstain` production
    row are both non-accusations, and production's row is byte-identical to frozen 3.3.
    """

    row = executed_rows[name]
    fixture = row["fixture"]
    assert fixture.correct_analysis is True
    assert _PROTOTYPE_FIXTURE_ROWS[name]["outcome"][0] == "covered"
    assert row["json"][0] == "abstain"
    assert row["json"] == _STRICTER_THAN_PROTOTYPE[name]
    assert _outcome_tuple(_run_v33(fixture.case_key, fixture.source)) == _outcome_tuple(
        row["outcome"]
    )


@pytest.mark.parametrize("name", _PINNED_CORRECT_NAMES)
def test_no_correct_analysis_fixture_becomes_a_candidate(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    assert executed_rows[name]["outcome"].state != "candidate"


_REFUSED = tuple(
    str(row["name"]) for row in _PINNED_FIXTURE_ROWS if row["refused_admission"] is not None
)
_ADMITTED = tuple(
    str(row["name"]) for row in _PINNED_FIXTURE_ROWS if row["required_admission"] is not None
)


@pytest.mark.parametrize("name", _REFUSED)
def test_named_disqualifiers_refuse_their_admission(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """A disqualifier is proved by an empty admission census, not by a downstream abstention.

    The non-vacuity half matters just as much: a fixture whose shipped 3.3 baseline already
    classifies would have an empty census for free, because the ordering rule attempts no 3.4
    admission on a classified row.
    """

    fixture = _fixture(name)
    baseline = _run_v33(fixture.case_key, fixture.source)
    assert baseline.state == "abstain", "the disqualifier assertion would be vacuous"
    census = executed_rows[fixture.name]["census"]
    assert census[fixture.refused_admission] == 0


@pytest.mark.parametrize("name", _ADMITTED)
def test_named_admissions_actually_fire(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    fixture = _fixture(name)
    assert executed_rows[fixture.name]["census"][fixture.admitted] > 0


def test_admission_census_totals_and_rows_match_the_executed_design_evidence(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    rows = {
        kind: sorted(name for name, row in executed_rows.items() if row["census"][kind])
        for kind in ADMISSION_KINDS
    }
    expected = {
        kind: sorted(row["name"] for row in _RESULTS["fixtures"] if row["admission_census"][kind])
        for kind in ADMISSION_KINDS
    }
    assert rows == expected
    assert rows["terminal-ifexp"] == []


_POSITIVE_CONTROLS = {
    "positive-comprehension-dict-helper-record": (
        "comprehension",
        ("candidate", "none", (), 6),
    ),
    "positive-ap-enumerate-start-one": (
        "enumerate",
        ("candidate", "strict_subset", (0, 1, 2), 7),
    ),
    "positive-ap-enumerate-no-start": (
        "enumerate",
        ("candidate", "strict_subset", (0, 1, 2), 7),
    ),
    "positive-ap-enumerate-start-zero": (
        "enumerate",
        ("candidate", "strict_subset", (0, 1, 2), 7),
    ),
}


@pytest.mark.parametrize("name", sorted(_POSITIVE_CONTROLS))
def test_positive_controls_admit_and_reach_their_pinned_outcome(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    kind, expected = _POSITIVE_CONTROLS[name]
    row = executed_rows[name]
    assert row["census"][kind] > 0
    assert _outcome_tuple(row["outcome"]) == expected


def test_min_form_stays_admitted_without_the_cap_admission_firing(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    row = executed_rows["positive-ap-cap-min-form-unchanged"]
    assert _outcome_tuple(row["outcome"]) == ("candidate", "strict_subset", (0, 1, 2), 7)
    assert row["census"]["cap"] == 0
    assert row["census"]["enumerate"] == 1


def test_if_cap_and_min_spellings_produce_identical_coverage_records(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """Extension D's whole claim: two spellings of the same arithmetic agree exactly."""

    if_cap = executed_rows["correct-ap-cap-complete-correction"]
    minimum = executed_rows["correct-ap-enumerate-complete-correction-min"]
    assert _outcome_tuple(if_cap["outcome"]) == ("covered", "complete", (0, 1, 2, 3, 4, 5, 6), 7)
    assert _outcome_tuple(if_cap["outcome"]) == _outcome_tuple(minimum["outcome"])
    assert if_cap["census"]["cap"] == 1
    assert minimum["census"]["cap"] == 0


def test_list_form_is_admitted_and_its_record_model_residual_is_recorded(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    row = executed_rows["positive-comprehension-list-form"]
    assert row["census"]["comprehension"] == 1
    assert row["outcome"].state == "abstain"
    assert row["outcome"].reason_or_classification == "pderived-conclusion-family-incomplete"


def test_inline_flat_record_element_resolves_through_the_global_census(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    row = executed_rows["positive-comprehension-inline-flat-record"]
    assert row["census"]["comprehension"] == 1
    assert row["outcome"].reason_or_classification == (
        "extra-registered-test-outside-authorized-family"
    )


def test_a_normalized_family_never_hides_a_later_p_gated_test(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """The whole-module census runs on original bytes, so the extra registered call is seen."""

    row = executed_rows["correct-comprehension-gates-later-test"]
    assert row["census"]["comprehension"] == 1
    assert row["outcome"].state == "abstain"
    assert row["outcome"].reason_or_classification == "authorized-family-test-census-incomplete"


# --------------------------------------------------------------------------------------
# Extension A grammar, at the grammar's own gate
# --------------------------------------------------------------------------------------


def _fixture(name: str) -> Any:
    return next(item for item in _fixtures() if item.name == name)


def _outcome_columns(case_key: str, source: bytes) -> tuple[str, ...]:
    return tuple(_INPUTS(_REFERENCE_CASE(case_key), source)["outcome_columns"])


@pytest.mark.parametrize(
    "name",
    [
        "correct-comprehension-with-filter",
        "correct-comprehension-over-non-contract-sequence",
        "correct-comprehension-key-not-loop-variable",
        "correct-comprehension-two-generators",
        "correct-comprehension-conditional-element",
        "correct-comprehension-nested-element",
        "correct-comprehension-keyword-argument-element",
        "correct-comprehension-out-of-contract-order",
        "correct-comprehension-target-rebound",
        "correct-comprehension-collection-mutated",
        "correct-comprehension-element-ignores-loop-variable",
    ],
)
def test_comprehension_disqualifiers_refuse_at_the_grammar_gate(name: str) -> None:
    """Mutation kill: admitting a filtered or otherwise disqualified comprehension here fails."""

    fixture = _fixture(name)
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    assert admitted_comprehensions(tree, columns) == ()
    assert normalize_comprehensions(fixture.source, columns) is None


def test_the_pinned_p3_comprehension_is_admitted_with_its_exact_structural_evidence() -> None:
    fixture = _fixture("positive-comprehension-dict-helper-record")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    admitted = admitted_comprehensions(ast.parse(fixture.source), columns)
    assert len(admitted) == 1
    item = admitted[0]
    assert item.kind == "dict"
    assert item.element_kind == "call"
    assert item.target == "results"
    assert item.sequence_name == "OUTCOMES"
    assert item.loop_variable == "outcome"
    assert module_sequences(ast.parse(fixture.source))["OUTCOMES"] == columns


def test_lowering_is_graph_preserving_and_idempotent() -> None:
    fixture = _fixture("positive-comprehension-dict-helper-record")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    original = ast.parse(fixture.source)
    admitted = admitted_comprehensions(original, columns)
    element_dump = ast.dump(admitted[0].element, include_attributes=True)

    first = normalize_comprehensions(fixture.source, columns)
    second = normalize_comprehensions(fixture.source, columns)
    assert first is not None and second is not None
    assert ast.dump(first.tree, include_attributes=True) == ast.dump(
        second.tree, include_attributes=True
    )
    assert first.admissions == second.admissions

    # The lowered element is the same graph as the original element.
    lowered_loop = next(
        node
        for node in ast.walk(first.tree)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == "OUTCOMES"
    )
    stored = lowered_loop.body[0]
    assert isinstance(stored, ast.Assign)
    assert ast.dump(stored.value, include_attributes=True) == element_dump

    # An already-normalized module admits nothing and lowers to itself.
    assert admitted_comprehensions(first.tree, columns) == ()


def test_normalization_produces_a_graph_fact_and_leaves_the_source_bytes_alone() -> None:
    fixture = _fixture("positive-comprehension-dict-helper-record")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    normalization = normalize_comprehensions(fixture.source, columns)
    assert normalization is not None
    assert isinstance(normalization.tree, ast.Module)
    assert fixture.source == _fixture("positive-comprehension-dict-helper-record").source


# --------------------------------------------------------------------------------------
# Extension C: the counter is opaque
# --------------------------------------------------------------------------------------


def test_enumerate_counter_binding_is_opaque_to_static_bool_and_positions() -> None:
    """Mutation kill: binding the counter to an int makes `_static_bool` resolve and admits it."""

    fixture = _fixture("positive-ap-enumerate-start-one")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    loop = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call)
    )
    owner = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and loop in ast.walk(node)
    )
    with recording_admissions():
        rows = _complete_rows(
            loop, tree=tree, owner=owner, sequences=sequences, outcome_columns=columns
        )
        assert admission_census()["enumerate"] == 1
    assert rows is not None and len(rows) == len(columns)
    assert tuple(row["outcome"] for row in rows) == columns
    assert all(row["position"] is _ENUMERATE_COUNTER for row in rows)
    assert not isinstance(_ENUMERATE_COUNTER, bool)
    assert _ENUMERATE_COUNTER not in columns

    counter_guard = ast.parse("position <= 3", mode="eval").body
    for row in rows:
        assert _static_bool(counter_guard, row, owner=owner, sequences=sequences) is None
        assert (
            _static_bool(
                ast.Name(id="position", ctx=ast.Load()),
                row,
                owner=owner,
                sequences=sequences,
            )
            is None
        )


def test_counter_use_in_a_decision_admits_the_row_table_and_still_refuses(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    decision = executed_rows["correct-ap-counter-used-in-decision"]
    factor = executed_rows["correct-ap-counter-used-as-factor"]
    assert decision["census"]["enumerate"] == 1
    assert decision["outcome"].state == "abstain"
    assert decision["outcome"].reason_or_classification == "unresolved-manual-correction-present"
    assert factor["outcome"].state == "abstain"
    assert factor["outcome"].reason_or_classification == "unresolved-manual-correction-present"


def test_positions_refuse_when_a_branch_is_guarded_on_the_counter() -> None:
    fixture = _fixture("correct-ap-counter-used-in-decision")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    guard = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "position"
    )
    owner = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and guard in ast.walk(node)
    )
    target = guard.body[0]
    with recording_admissions():
        assert (
            _positions_for(
                target,
                tree=tree,
                owner=owner,
                parents=parents,
                sequences=sequences,
                outcome_columns=columns,
            )
            is None
        )


def test_a_membership_guard_on_the_counter_can_never_select_positions() -> None:
    """Mutation kill: bind the counter to a row value the predicates can read and this resolves.

    A membership test is the one comparison form `_static_bool` can decide, so it is the exact
    shape that would let a counter select family positions if the binding were transparent.
    """

    fixture = _fixture("positive-ap-enumerate-start-one")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    loop = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call)
    )
    owner = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and loop in ast.walk(node)
    )
    with recording_admissions():
        rows = _complete_rows(
            loop, tree=tree, owner=owner, sequences=sequences, outcome_columns=columns
        )
    assert rows is not None
    counter_membership = ast.parse("position in MUSCULOSKELETAL", mode="eval").body
    outcome_membership = ast.parse("outcome in MUSCULOSKELETAL", mode="eval").body
    counter_values = [
        _static_bool(counter_membership, row, owner=owner, sequences=sequences) for row in rows
    ]
    outcome_values = [
        _static_bool(outcome_membership, row, owner=owner, sequences=sequences) for row in rows
    ]
    # The outcome element decides.  The counter is never a member of any contract name set, so
    # a membership guard on it selects the empty set on every row and can never carve a family.
    assert outcome_values == [True, True, True, False, False, False, False]
    assert counter_values == [False] * len(rows)
    assert len(set(counter_values)) == 1


@pytest.mark.parametrize(
    "name",
    [
        "correct-ap-enumerate-over-non-contract-sequence",
        "correct-ap-enumerate-over-zip",
        "correct-ap-enumerate-single-target",
        "correct-ap-enumerate-nonliteral-start",
        "correct-ap-enumerate-reversed-sequence",
    ],
)
def test_enumerate_disqualifiers_refuse_at_the_row_table_gate(name: str) -> None:
    """Mutation kill: admitting a non-bare-Name or non-literal-start iterator fails here."""

    fixture = _fixture(name)
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    owner = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    with recording_admissions():
        for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
            _complete_rows(
                loop, tree=tree, owner=owner, sequences=sequences, outcome_columns=columns
            )
        assert admission_census()["enumerate"] == 0


# --------------------------------------------------------------------------------------
# Extension D: the adjacent if-cap
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "correct-ap-cap-non-adjacent",
        "correct-ap-cap-guard-on-different-name",
        "correct-ap-cap-guard-not-literal-one",
        "correct-ap-cap-body-extra-statement",
        "correct-ap-cap-with-else",
        "correct-ap-cap-assigns-other-value",
        "correct-ap-cap-augmented-reassignment",
        "correct-ap-cap-reassigns-other-name",
    ],
)
def test_cap_disqualifiers_refuse_at_the_cap_grammar_gate(name: str) -> None:
    """Mutation kill: dropping the adjacency, guard, or sole-statement proof admits these."""

    fixture = _fixture(name)
    assert admitted_caps(ast.parse(fixture.source)) == ()


def test_the_pinned_p6_cap_is_admitted_with_its_exact_shape() -> None:
    fixture = _fixture("positive-ap-enumerate-start-one")
    caps = admitted_caps(ast.parse(fixture.source))
    assert len(caps) == 1
    cap = caps[0]
    assert cap.name == "corrected_p"
    assert isinstance(cap.product.value, ast.BinOp)
    assert isinstance(cap.guard.test, ast.Compare)
    assert cap.guard.orelse == []
    assert cap.guard.body == [cap.reassignment]


@pytest.mark.parametrize("form", ["X > 1.0", "X >= 1.0", "1.0 < X", "1.0 <= X"])
def test_all_four_admitted_cap_comparison_forms_are_one_fold(form: str) -> None:
    source = (
        f"def main():\n    X = raw * factor\n    if {form}:\n        X = 1.0\n    print(X)\n"
    ).encode()
    caps = admitted_caps(ast.parse(source))
    assert len(caps) == 1
    assert caps[0].name == "X"


# --------------------------------------------------------------------------------------
# Extension B is specified and NOT shipped; extension E is measured and NOT applied
# --------------------------------------------------------------------------------------


def test_extension_b_is_not_in_the_shipped_recognizer_set(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """No 3.4 module widens the terminal-`IfExp` proof, and no row admits a position."""

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )
    from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_4 as dataflow

    for module in (comprehension, correction, dataflow):
        text = Path(module.__file__ or "").read_text(encoding="utf-8")
        assert "_terminal_ifexp_positions" not in text
        assert "_reaches_print" not in text
        assert "_dict_field_for_name" not in text
    # The only terminal-presentation entry point 3.4 uses is the byte-frozen 3.3 proof.
    dataflow_text = Path(dataflow.__file__ or "").read_text(encoding="utf-8")
    assert "code_csv_multiple_testing_terminal_presentation_v3_3" in dataflow_text
    assert "prove_terminal_presentation" in dataflow_text
    assert all(row["census"]["terminal-ifexp"] == 0 for row in executed_rows.values())


@pytest.mark.parametrize(
    "name",
    [
        "correct-terminal-verdict-stored-then-printed",
        "correct-terminal-verdict-rebound-into-name",
        "correct-terminal-verdict-returned-from-helper",
    ],
)
def test_the_specified_section_5_verdict_store_shapes_stay_refused(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """The three named store shapes remain non-candidates and admit no terminal position."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 import (
        prove_terminal_presentation,
    )

    fixture = _fixture(name)
    assert prove_terminal_presentation(fixture.source) is None
    row = executed_rows[name]
    assert row["census"]["terminal-ifexp"] == 0
    assert row["outcome"].state != "candidate"
    probe = {
        item["fixture"]: item["v34_admitted_positions"]
        for item in _INSTRUMENT["terminal_ifexp_refusal_probe"]["rows"]
    }
    assert probe[name] == []


def test_e16_p4_keeps_its_pinned_candidate_under_the_shipped_recognizer_set() -> None:
    """The measured extension-B collision is the reason B is not shipped; the pin holds."""

    key = "E16:P4:9ced761b41ef93485acf"
    case = _REFERENCE_CASE(key)
    outcome, census = _run_source(key, case.source_path.read_bytes())
    assert _outcome_tuple(outcome) == ("candidate", "none", (), 7)
    assert census["terminal-ifexp"] == 0
    collision = next(
        row for row in _INSTRUMENT["extension_b_collision_probe"]["rows"] if row["case_key"] == key
    )
    assert collision["extension_b_regresses_row"] is True
    assert collision["outcome_with_extension_b"] == ["abstain", "hierarchical-gatekeeping-present"]


@pytest.mark.parametrize(
    "name", ["correct-outcome-headers-genuine-screen", "correct-outcome-headers-early-exit"]
)
def test_genuine_gatekeeping_keeps_its_reason_and_admits_no_comprehension(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """Extension E is not applied: no reason string is routed anywhere in 3.4."""

    row = executed_rows[name]
    assert row["census"]["comprehension"] == 0
    assert row["outcome"].state == "abstain"
    assert (
        row["outcome"].reason_or_classification
        == _run_v33(row["fixture"].case_key, row["fixture"].source).reason_or_classification
    )


def test_no_row_anywhere_emits_the_specified_reason_routing(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """The ten measured relabel rows keep `hierarchical-gatekeeping-present` unchanged."""

    measured = sorted(
        row["name"]
        for row in _RESULTS["fixtures"]
        if row["outcome_with_reason_routing"] != row["outcome"]
    )
    assert len(measured) == 10
    for name in measured:
        row = executed_rows[name]
        assert row["json"] == _PROTOTYPE_FIXTURE_ROWS[name]["outcome"]
        assert row["outcome"].reason_or_classification != "pvalue-control-dependence-unresolved"
    assert [row["key"] for row in _RESULTS["cases"] if row["relabeled"]] == []


# --------------------------------------------------------------------------------------
# The ordering rule
# --------------------------------------------------------------------------------------


def test_a_row_the_frozen_pipeline_classifies_is_returned_untouched() -> None:
    """Step 3: no 3.4 admission is even attempted on a frozen 3.3 classification."""

    key = "E16:P3:5a9c5b4377c33916d672"
    case = _REFERENCE_CASE(key)
    source = case.source_path.read_bytes()
    frozen = _run_v33(key, source)
    outcome, census = _run_source(key, source)
    assert frozen.state == "candidate"
    assert _outcome_tuple(outcome) == _outcome_tuple(frozen)
    assert census == dict.fromkeys(ADMISSION_KINDS, 0)


#: Rows where the 3.4 re-analysis reaches a DIFFERENT wall than the frozen 3.3 pipeline did.
#: These are the rows on which the ordering rule is load-bearing rather than decorative: if the
#: dataflow adopted the re-analysis abstention, every one of these public reasons would change.
_REANALYSIS_DIVERGES = {
    "positive-comprehension-list-form": (
        "pderived-conclusion-family-incomplete",
        "test-battery-cardinality-unresolved",
    ),
    "correct-helper-record-mutates-nonlocal-state": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-conclusion-recomputed-from-raw-p": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-conditional-store": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-nested-record": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-unresolved-consumer": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
}


@pytest.mark.parametrize("name", sorted(_REANALYSIS_DIVERGES))
def test_an_abstaining_reanalysis_returns_the_frozen_reason_byte_for_byte(name: str) -> None:
    """Step 5: a 3.4 re-analysis that abstains never replaces the frozen 3.3 reason.

    Mutation kill: letting the 3.4 dataflow adopt a re-analysis abstention reason changes the
    emitted reason on exactly these rows, because the re-analysis really does reach a different
    wall.  The pinned pair records both reasons, so the assertion cannot pass by accident.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _reanalyze_with_v34_admissions,
    )

    frozen_reason, reanalysis_reason = _REANALYSIS_DIVERGES[name]
    fixture = _fixture(name)
    values = _INPUTS(_REFERENCE_CASE(fixture.case_key), fixture.source)
    content = cast(bytes, values.pop("content"))

    assert _run_v33(fixture.case_key, fixture.source).reason_or_classification == frozen_reason
    with recording_admissions():
        attempted = _CLASSIFY(_reanalyze_with_v34_admissions(content, **values))
        census = admission_census()
    assert census["comprehension"] == 1, "the re-analysis really did run and admit"
    assert attempted.state == "abstain"
    assert attempted.reason_or_classification == reanalysis_reason
    assert reanalysis_reason != frozen_reason

    shipped, _shipped_census = _run_source(fixture.case_key, fixture.source)
    assert shipped.state == "abstain"
    assert shipped.reason_or_classification == frozen_reason


def test_every_frozen_3_3_abstention_reason_survives_across_the_new_fixture_rows(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """No new fixture row that stays an abstention may carry a reason 3.3 did not emit."""

    for name in sorted(_new_fixture_names()):
        row = executed_rows[name]
        if row["outcome"].state != "abstain":
            continue
        frozen = _run_v33(row["fixture"].case_key, row["fixture"].source)
        assert frozen.state == "abstain", name
        assert row["outcome"].reason_or_classification == frozen.reason_or_classification, name


# --------------------------------------------------------------------------------------
# Observed trigger attribution, closed reasons, and frozen anchors
# --------------------------------------------------------------------------------------


def test_the_real_guard_attribution_at_the_e17_p3_control_is_outcome_headers_only() -> None:
    """Run the shipped hierarchy guard and record every control it actually tracked."""

    case = _REFERENCE_CASE(_P3_KEY)
    values = _INPUTS(case, None)
    content = cast(bytes, values.pop("content"))
    observed: list[dict[str, Any]] = []
    original_control = frozen_v3._MtEngine._control_tracked
    original_guard = frozen_v3._MtEngine._hierarchy_guard
    registry: dict[int, set[int]] = {}

    def _registry_expressions(scope: tuple[Any, ...]) -> set[int]:
        result: set[int] = set()
        for node in frozen_v3._walk_statements(scope):
            if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
                result.add(id(node.test))
            elif isinstance(node, ast.Match):
                result.add(id(node.subject))
                result.update(id(item.guard) for item in node.cases if item.guard is not None)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                result.add(id(node.iter))
            elif isinstance(node, ast.comprehension):
                result.add(id(node.iter))
                result.update(id(item) for item in node.ifs)
        return result

    state = {"active": False}

    def control(self: Any, node: ast.expr, **kwargs: Any) -> bool:
        tracked = original_control(self, node, **kwargs)
        if state["active"] and tracked:
            if id(self) not in registry:
                registry[id(self)] = _registry_expressions((*self.original_scope, *self.scope))
            observed.append(
                {
                    "position": list(
                        (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)
                    ),
                    "node_type": type(node).__name__,
                    "p_origins": len(self._p_origins(node)),
                    "correction_control": bool(self._correction_control_present(node)),
                    "outcome_headers": sorted(self._outcome_headers(node, set(), 0)),
                    "registry_control": id(node) in registry[id(self)],
                }
            )
        return tracked

    def guard(self: Any) -> str | None:
        state["active"] = True
        try:
            return original_guard(self)
        finally:
            state["active"] = False

    frozen_v3._MtEngine._control_tracked = control
    frozen_v3._MtEngine._hierarchy_guard = guard
    try:
        result = analyze_v33(content, **values)
    finally:
        frozen_v3._MtEngine._control_tracked = original_control
        frozen_v3._MtEngine._hierarchy_guard = original_guard

    assert result.reason == "hierarchical-gatekeeping-present"
    assert len(observed) == 1
    control_row = observed[0]
    assert control_row["position"] == [71, 35, 71, 54]
    assert control_row["node_type"] == "Compare"
    assert control_row["p_origins"] == 0
    assert control_row["correction_control"] is False
    assert control_row["registry_control"] is True
    assert control_row["outcome_headers"] == sorted(values["outcome_columns"])
    assert len(control_row["outcome_headers"]) == 6
    pinned = _INSTRUMENT["traces"][0]
    assert pinned["case_key"] == _P3_KEY
    assert pinned["first_tracked_control"]["position"] == [71, 35, 71, 54]
    assert pinned["first_tracked_control"]["p_origins"] == 0


def test_closed_reason_set_remains_exactly_frozen_61() -> None:
    from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_3 import (
        _CLOSED_REASONS as FROZEN_REASONS,
    )

    assert _CLOSED_REASONS == FROZEN_REASONS
    assert len(_CLOSED_REASONS) == 61


def test_frozen_3_1_3_2_3_3_anchor_bytes_are_exact() -> None:
    root = Path(__file__).resolve().parents[1]
    pinned = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3.py": "0388b4a1d3a28b7549af85362d0d4e7f13ffc2b4807dc129d242c4927870c0d1",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_2.py": "38f74309c4ba082dceb335d95691401b7f9b780958d1c0b82bdb63e496fc29c2",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_2.py": "b7c182a9bac2e6e3eb015c2902e607201a5bfdca5f0889413b1145911d30b239",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_3.py": "ddcb29549dda5dcf164848730679027161e34692282cfeaabf84e089db58b857",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3_3.py": "d9d919b5289c767a39dd62edea8fc17563a6ad76aa627c49e427b6201f81bf4a",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_3.py": "de46498474b0043231a66b6adeb779e799b3736afce162b6919dc0eebc516242",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_terminal_presentation_v3_3.py": "d1b9463235494ae54d4c5d2bbc3eb4f0d1b73568a4c5625993dd87dbee4b5c78",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_helper_record_v3_3.py": "f3c5e8fb9ec52f8e2d13a6de11849f63b08a073e4208f9d5936fbcf177c76033",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_3.py": "7c3ce13e3e10fcf012bf4c803f6a5e3bd88aa30146059873710b8a549550efcc",
        "src/sc_referee/scientific_checks/integration_multiple_testing_v3_3.py": "edc5b3d94329a15c263dbab167bc623be7f778bca5b867d771f9538642719557",
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_3.py": "0b7505fb42d191be0916f287eeea72dfc4d579edbc2a367ec413b503e1670e4c",
        "src/sc_referee/scientific_checks/multiple_testing_scope_questions_v3_3.py": "b060f34c52c64db7f36ca1e2469239e6a6920404ecee87c13e986f526c59ff3b",
        "docs/implementation/MULTITEST-3.3-TERMINAL-PRESENTATION-DESIGN-2026-08-30.md": "cbc37990e9a713c486bf903cefef03c08ad264e7b6112383330b56a0c3f6c224",
        "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/results.json": "be9ddd1ea4b8bd27faff92392865cbb76f14fbf6b162f847523fe5900d1bd7ad",
        "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/MANIFEST.json": "10e94f5a056e50662bfc65bfafc2ebec0ea519a4c7bef1f5269caddf6523bf5f",
        "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/instrument_results.json": "03c7aa815b8728bf9452afe666f9738e9501f345903ce7ef7fe3f520c320134f",
        "evaluation/development/multitest-code-slice-v3_3/adapter_replay_records_v3_3.json": "4b42ee3a517bd95591eac9f0d7bb9a497728f9df708c57fc99298d7205df83ce",
        "evaluation/development/blind-envelope-17-2026-08-30/ROLE_MAP.json": "004a87be3448c1736f24ac48d0deb155694ee7da08670d02918ac8e09d4cea9e",
        "evaluation/development/blind-envelope-17-2026-08-30/AUDIT_RESULTS.json": "ca9cb2caf2b4fd0c4047a7758f0351278f7bd66f79f1dacaf6af0754a47b4b6e",
        "docs/implementation/MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md": "2f7bd77e1020777c9fcdc5573edc87c43567ba153fd3fc1f801926752993c854",
    }
    assert {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in pinned
    } == pinned


def test_production_uses_graph_facts_without_source_rewrite_or_monkeypatch() -> None:
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )
    from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_4 as dataflow

    comprehension_source = Path(comprehension.__file__ or "").read_text(encoding="utf-8")
    dataflow_source = Path(dataflow.__file__ or "").read_text(encoding="utf-8")
    assert "ast.unparse" not in comprehension_source
    assert "ast.unparse" not in dataflow_source
    for text in (comprehension_source, dataflow_source):
        assert "monkeypatch" not in text
        assert "setattr(" not in text
    # The versioned correction model owns the recognizers outright; it never rebinds a frozen one.
    correction_source = Path(correction.__file__ or "").read_text(encoding="utf-8")
    assert "setattr(" not in correction_source
    assert "_COMPLETE_ROWS_V33" not in correction_source

    ordering = inspect.getsource(dataflow.analyze_code_csv_multiple_testing_dataflow)
    assert "_frozen_v33_analyze" in ordering
    assert "return frozen" in ordering


def test_the_admission_census_is_write_only_and_never_reaches_a_proof() -> None:
    """The census records evidence; no recognizer reads it back to decide anything."""

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    for module in (comprehension, correction):
        text = Path(module.__file__ or "").read_text(encoding="utf-8")
        # The recognizers write to the census and never call either reader back.
        assert "admission_census(" not in text
        assert "admission_spans(" not in text
        assert "record_admission(" in text

    fixture = _fixture("positive-ap-enumerate-start-one")
    inside, census_inside = _run_source(fixture.case_key, fixture.source)
    assert census_inside["enumerate"] == 1
    # Recording outside an open census is ignored, so no count can leak between analyses.
    outside, _ = _run_source(fixture.case_key, fixture.source)
    assert _outcome_tuple(inside) == _outcome_tuple(outside)
    assert set(admission_spans()) == set(ADMISSION_KINDS)


# --------------------------------------------------------------------------------------
# Audit fix round 1: sequence-object stability, the unshadowed builtin, contract order
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def audit_fix_rows() -> dict[str, dict[str, Any]]:
    """Execute every audit-fix source through the shipped 3.4 analyzer and the frozen 3.3 one."""

    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_1_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_ROWS) == 9
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_ROWS) == 4
    assert set(_AUDIT_FIX_ROWS_BY_NAME) == set(_AUDIT_FIX_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_SOURCES.items()
    } == {name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_ROWS_BY_NAME.items()}


@pytest.mark.parametrize("row", _AUDIT_FIX_ROWS, ids=lambda row: row["fixture_name"])
def test_all_9_audit_fix_round_1_rows_execute(
    row: dict[str, Any], audit_fix_rows: dict[str, dict[str, Any]]
) -> None:
    observed = audit_fix_rows[str(row["fixture_name"])]
    assert _outcome_tuple(observed["outcome"]) == (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    assert observed["census"] == row["expected_admission_census"]
    # Design section 3.3 steps 5 and 6: a refused admission returns the frozen 3.3 row unchanged.
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v33_identical"])


def test_no_audit_fix_correct_analysis_row_becomes_a_candidate(
    audit_fix_rows: dict[str, dict[str, Any]],
) -> None:
    """The four mutated-sequence rows are complete seven-outcome corrections, never subsets."""

    correct = [row for row in _AUDIT_FIX_ROWS if row["correct_analysis"]]
    assert len(correct) == 4
    assert not [
        str(row["fixture_name"])
        for row in correct
        if audit_fix_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    ]


@pytest.mark.parametrize("name", _MUTATED_SEQUENCE_ROWS)
def test_mutated_selection_sequence_refuses_at_the_sequence_object_stability_gate(
    name: str,
) -> None:
    """Mutation kill: dropping the object-stability closure readmits the mutated sequence here.

    The accusation this closes is a complete seven-outcome correction reported as a strict
    subset of three, so the assertion is that the mutated sequence never enters the module
    sequence table at all.  A downstream abstention would not distinguish the fix from a
    coincidence.
    """

    row = _AUDIT_FIX_ROWS_BY_NAME[name]
    _case_key, source = _AUDIT_FIX_SOURCES[name]
    unstable = [str(item) for item in row["expected_unstable_sequence_names"]]
    sequences = _module_sequences(ast.parse(source))
    assert [item for item in unstable if item in sequences] == []
    # Non-vacuity: every one of those names resolves on the unmutated source.
    _control_key, control = _AUDIT_FIX_SOURCES["positive-ap-unmutated-sequence-genuine-enumerate"]
    assert set(unstable) <= set(_module_sequences(ast.parse(control)))


@pytest.mark.parametrize("name", _SHADOWED_ENUMERATE_ROWS)
def test_shadowed_enumerate_refuses_at_the_unshadowed_builtin_gate(
    name: str, audit_fix_rows: dict[str, dict[str, Any]]
) -> None:
    """Mutation kill: proving the builtin by `node.func.id` alone readmits a project-local def."""

    _case_key, source = _AUDIT_FIX_SOURCES[name]
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.FunctionDef) and node.name == "enumerate" for node in ast.walk(tree)
    )
    assert _enumerate_is_the_unshadowed_builtin(tree) is False
    assert audit_fix_rows[name]["census"]["enumerate"] == 0
    # Non-vacuity: the same predicate admits the genuine builtin on the unaltered source.
    _control_key, control = _AUDIT_FIX_SOURCES["positive-ap-unmutated-sequence-genuine-enumerate"]
    assert _enumerate_is_the_unshadowed_builtin(ast.parse(control)) is True


def test_flat_equal_length_sequence_refuses_at_the_contract_order_equality_gate() -> None:
    """Mutation kill: matching the generator sequence by length instead of order admits this.

    The pinned out-of-contract-order row cannot kill that mutant.  It builds its sequence with
    `list(reversed(OUTCOMES))`, which never resolves to a module sequence, so it refuses before
    the order comparison is reached.  This row resolves, carries the contract length, and
    carries exactly the contract member set, so order equality is the only predicate left.
    """

    name = "correct-comprehension-flat-literal-out-of-contract-order"
    row = _AUDIT_FIX_ROWS_BY_NAME[name]
    case_key, source = _AUDIT_FIX_SOURCES[name]
    columns = _outcome_columns(case_key, source)
    tree = ast.parse(source)
    sequence = module_sequences(tree).get("SHUFFLED")
    upstream = row["expected_upstream_gates_pass"]
    assert (sequence is not None) is upstream["sequence_is_a_resolvable_module_sequence"]
    assert sequence is not None
    assert (len(sequence) == len(columns)) is upstream["sequence_length_equals_contract_length"]
    assert (set(sequence) == set(columns)) is upstream["member_set_equals_contract"]
    assert (tuple(sequence) == columns) is upstream["sequence_order_equals_contract_order"]
    assert admitted_comprehensions(tree, columns) == ()
    assert normalize_comprehensions(source, columns) is None


@pytest.mark.parametrize(
    "name",
    [
        "positive-ap-unmutated-sequence-genuine-enumerate",
        "positive-ap-selection-sequence-alias-without-mutation",
    ],
)
def test_both_narrowings_keep_the_pinned_e17_p6_movement(
    name: str, audit_fix_rows: dict[str, dict[str, Any]]
) -> None:
    """Mutation kill: a closure that refused every sequence, or refused a live alias, loses this."""

    row = audit_fix_rows[name]
    assert _outcome_tuple(row["outcome"]) == ("candidate", "strict_subset", (0, 1, 2), 7)
    assert row["census"]["enumerate"] == 1
    assert row["census"]["cap"] == 1


# --------------------------------------------------------------------------------------
# Audit fix round 2: the comprehension lane's sequence object, and the collected name
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def audit_fix_r2_rows() -> dict[str, dict[str, Any]]:
    """Execute every round-2 source through the shipped 3.4 analyzer and the frozen 3.3 one."""

    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_R2_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_2_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_R2_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_R2_ROWS) == 12
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_R2_ROWS) == 5
    assert set(_AUDIT_FIX_R2_ROWS_BY_NAME) == set(_AUDIT_FIX_R2_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_R2_SOURCES.items()
    } == {
        name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_R2_ROWS_BY_NAME.items()
    }


@pytest.mark.parametrize("row", _AUDIT_FIX_R2_ROWS, ids=lambda row: row["fixture_name"])
def test_all_12_audit_fix_round_2_rows_execute(
    row: dict[str, Any], audit_fix_r2_rows: dict[str, dict[str, Any]]
) -> None:
    observed = audit_fix_r2_rows[str(row["fixture_name"])]
    assert _outcome_tuple(observed["outcome"]) == (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    assert observed["census"] == row["expected_admission_census"]
    # Design section 3.3 steps 5 and 6: a refused admission returns the frozen 3.3 row unchanged.
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v33_identical"])


def test_no_audit_fix_round_2_correct_analysis_row_becomes_a_candidate(
    audit_fix_r2_rows: dict[str, dict[str, Any]],
) -> None:
    """The five correct-analysis rows are complete corrections or single-outcome tests."""

    correct = [row for row in _AUDIT_FIX_R2_ROWS if row["correct_analysis"]]
    assert len(correct) == 5
    assert not [
        str(row["fixture_name"])
        for row in correct
        if audit_fix_r2_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    ]


@pytest.mark.parametrize("name", _ESCAPED_SEQUENCE_ROWS)
def test_escaped_sequence_object_refuses_at_the_comprehension_sequence_gate(name: str) -> None:
    """Mutation kill: dropping the alias half of the comprehension closure readmits these.

    The assertion is that the escaped sequence never enters the comprehension lane's own
    sequence table.  A downstream abstention would not distinguish the fix from the upstream
    frozen scope census arriving first, which is exactly what happened on the reported probe.
    """

    row = _AUDIT_FIX_R2_ROWS_BY_NAME[name]
    case_key, source = _AUDIT_FIX_R2_SOURCES[name]
    escaped = [str(item) for item in row["expected_escaped_sequence_names"]]
    assert escaped, "the row pins no escaped sequence, so the assertion would be vacuous"
    sequences = module_sequences(ast.parse(source))
    assert [item for item in escaped if item in sequences] == []
    # Non-vacuity: every one of those names resolves on the unaltered source of the same case.
    control = next(
        other
        for other, (other_key, _other_source) in _AUDIT_FIX_R2_SOURCES.items()
        if other_key == case_key and other.startswith("positive-") and other.endswith("-unaltered")
    )
    _control_key, control_source = _AUDIT_FIX_R2_SOURCES[control]
    assert set(escaped) <= set(module_sequences(ast.parse(control_source)))


@pytest.mark.parametrize("name", _ESCAPED_SEQUENCE_ROWS)
def test_escaped_sequence_object_refuses_in_the_correction_lane_too(name: str) -> None:
    """Mutation kill: dropping the whole closure readmits these in both lanes at once.

    The two lanes share one closure by import rather than by restatement, so the escape is
    asserted against the correction lane's sequence table as well.  A closure that diverged
    would leave one of the two assertions standing.
    """

    row = _AUDIT_FIX_R2_ROWS_BY_NAME[name]
    _case_key, source = _AUDIT_FIX_R2_SOURCES[name]
    escaped = [str(item) for item in row["expected_escaped_sequence_names"]]
    assert [item for item in escaped if item in _module_sequences(ast.parse(source))] == []


def test_the_two_lanes_share_one_sequence_object_closure() -> None:
    """The comprehension lane calls the round-1 helpers themselves, not a copy of them."""

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    assert comprehension.cm is correction
    for helper in ("_alias_edges", "_object_mutated_names", "_sequence_object_is_stable"):
        assert getattr(comprehension.cm, helper) is getattr(correction, helper)


def test_collected_name_alias_refuses_where_the_same_store_through_the_name_admits(
    audit_fix_r2_rows: dict[str, dict[str, Any]],
) -> None:
    """Mutation kill: dropping the collected-name alias closure readmits the aliased store.

    The pair is the whole argument.  The two sources carry the identical nested store; they
    differ only in whether it is written through the collected name or through a second name
    for the same collection.  Section 4.2 permits the first, which is the shape the pinned
    corpus row uses, and forbids the second, which its census cannot see.
    """

    aliased = "comprehension-collected-target-alias-store"
    through_name = "positive-comprehension-collected-target-store-through-name"
    for name, admitted in ((aliased, 0), (through_name, 1)):
        case_key, source = _AUDIT_FIX_R2_SOURCES[name]
        columns = _outcome_columns(case_key, source)
        assert len(admitted_comprehensions(ast.parse(source), columns)) == admitted, name
        assert audit_fix_r2_rows[name]["census"]["comprehension"] == admitted, name
    # Both abstain to the same frozen reason, so the closure changes the admission, not the row.
    assert _outcome_tuple(audit_fix_r2_rows[aliased]["outcome"]) == _outcome_tuple(
        audit_fix_r2_rows[through_name]["outcome"]
    )


@pytest.mark.parametrize("name", sorted(_R2_MOVEMENT_ROWS))
def test_round_2_narrowings_keep_every_pinned_movement(
    name: str, audit_fix_r2_rows: dict[str, dict[str, Any]]
) -> None:
    """Mutation kill: a closure that refused a live alias, or every display, loses these."""

    assert _outcome_tuple(audit_fix_r2_rows[name]["outcome"]) == _R2_MOVEMENT_ROWS[name]
    assert audit_fix_r2_rows[name]["outcome"] != audit_fix_r2_rows[name]["frozen"]


# --------------------------------------------------------------------------------------
# Audit fix round 3: the record-collection alias closure on the classification path
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def audit_fix_r3_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_R3_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_3_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_R3_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_R3_ROWS) == 19
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_R3_ROWS) == 11
    assert set(_AUDIT_FIX_R3_ROWS_BY_NAME) == set(_AUDIT_FIX_R3_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_R3_SOURCES.items()
    } == {
        name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_R3_ROWS_BY_NAME.items()
    }
    # Every fixture is a syntactically valid program, so no row can pass on a parse failure.
    for _name, (_case_key, source) in _AUDIT_FIX_R3_SOURCES.items():
        ast.parse(source)


@pytest.mark.parametrize("row", _AUDIT_FIX_R3_ROWS, ids=lambda row: row["fixture_name"])
def test_all_19_audit_fix_round_3_rows_execute(
    row: dict[str, Any], audit_fix_r3_rows: dict[str, dict[str, Any]]
) -> None:
    observed = audit_fix_r3_rows[str(row["fixture_name"])]
    assert _outcome_tuple(observed["outcome"]) == (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v33_identical"])


def test_no_audit_fix_round_3_correct_analysis_row_becomes_a_candidate(
    audit_fix_r3_rows: dict[str, dict[str, Any]],
) -> None:
    """The eleven correct-analysis rows are complete Bonferroni corrections over the family."""

    correct = [row for row in _AUDIT_FIX_R3_ROWS if row["correct_analysis"]]
    assert len(correct) == 11
    assert not [
        str(row["fixture_name"])
        for row in correct
        if audit_fix_r3_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    ]


@pytest.mark.parametrize("name", _COLLECTION_ALIAS_ROWS)
def test_an_aliased_store_lands_on_its_through_name_siblings_frozen_reason(
    name: str, audit_fix_r3_rows: dict[str, dict[str, Any]]
) -> None:
    """The reason pin is recomputed from the sibling rather than transcribed from 3.4 output.

    3.3 classifies these rows, so the round-1/round-2 authority -- the frozen reason for the row
    itself -- is unavailable.  The authority is the frozen 3.3 reason for the identical program
    with the same store written through the collection's own name.  The equality is asserted
    three ways: shipped 3.4 on the aliased row, the oracle pin, and the live frozen 3.3 row of
    the sibling.
    """

    row = _AUDIT_FIX_R3_ROWS_BY_NAME[name]
    sibling = str(row["expected_reason_sibling"])
    assert sibling in _AUDIT_FIX_R3_SOURCES, name
    sibling_key, sibling_source = _AUDIT_FIX_R3_SOURCES[sibling]
    sibling_frozen = _run_v33(sibling_key, sibling_source)
    observed = audit_fix_r3_rows[name]["outcome"]
    assert sibling_frozen.state == "abstain"
    assert observed.state == "abstain"
    assert (
        observed.reason_or_classification
        == sibling_frozen.reason_or_classification
        == str(row["expected_reason"])
    )
    # The pair really is the same program up to the name the store travels through: the frozen
    # pipeline classifies the aliased spelling and refuses the through-name one.
    assert audit_fix_r3_rows[name]["frozen"].state == "candidate"


def test_the_closed_reason_set_is_unchanged_by_round_3() -> None:
    """Round 3 adds no reason: the emitted reason is already in the closed 3.3 set of 61."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _COLLECTION_ALIAS_REASON,
    )

    assert _COLLECTION_ALIAS_REASON in _CLOSED_REASONS
    assert len(_CLOSED_REASONS) == 61
    for row in _AUDIT_FIX_R3_ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in _CLOSED_REASONS


def test_the_record_collection_predicate_stays_narrow() -> None:
    """Only a collection the module opens empty and fills, or one comprehension, is tracked."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_collection_names,
    )

    for name, expected in (
        ("correct-explicit-loop-collection-alias-store", {"results"}),
        ("positive-comprehension-e17-p3-unaltered", {"results"}),
        # The declared outcome list and the label table are literal displays, not collections
        # the module fills, so an alias of either can never reach the closure.
        ("positive-explicit-loop-uncorrected-family-unrelated-alias", {"results"}),
        # A seeded display is the same collection; the store requirement, not the seed, is what
        # keeps the declared outcome list and the label table out.
        ("correct-explicit-loop-seeded-collection-alias-store", {"results"}),
    ):
        _case_key, source = _AUDIT_FIX_R3_SOURCES[name]
        assert record_collection_names(ast.parse(source)) == expected, name


@pytest.mark.parametrize(
    "name",
    (
        "positive-explicit-loop-collection-alias-read-only",
        "positive-explicit-loop-collection-alias-reported-not-stored",
    ),
)
def test_a_read_only_alias_of_the_collection_is_never_refused(name: str) -> None:
    """The closure is over stores and mutations.  A live second name that is only read is clean."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_collection_alias_unresolved,
    )

    _case_key, source = _AUDIT_FIX_R3_SOURCES[name]
    tree = ast.parse(source)
    # Non-vacuity: the alias really is bound in the source under test.
    assert any(
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Name)
        and node.value.id == "results"
        for node in ast.walk(tree)
    ), name
    assert record_collection_alias_unresolved(tree) is False


@pytest.mark.parametrize("name", sorted(_R3_MOVEMENT_ROWS))
def test_round_3_keeps_every_pinned_movement_and_every_true_accusation(
    name: str, audit_fix_r3_rows: dict[str, dict[str, Any]]
) -> None:
    """A closure that refused aliasing rather than storing would lose all five of these."""

    assert _outcome_tuple(audit_fix_r3_rows[name]["outcome"]) == _R3_MOVEMENT_ROWS[name]


# --- Named mutation kills: apply, confirm, revert, record ------------------------------


def _r3_outcome(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _AUDIT_FIX_R3_SOURCES[name]
    outcome, _census = _run_source(case_key, source)
    return _outcome_tuple(outcome)


_R3_PROBE = "correct-explicit-loop-collection-alias-store"
_R3_ACCUSED = ("candidate", "none", (), 6)
_R3_REFUSED = ("abstain", "pvalue-family-collection-unresolved", (), None)


def test_mutation_kill_a_dropping_the_classification_path_closure_readmits_the_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the classification path returns the frozen row with no closure at all.

    Apply the mutant, confirm the confirmed false accusation comes back exactly as the custodian
    reproduced it, revert, and confirm the refusal returns.  Recorded: this is the whole fix, so
    removing it must lose the probe and nothing else needs to change to see that.
    """

    from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_4 as dataflow

    assert _r3_outcome(_R3_PROBE) == _R3_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(dataflow, "_record_collection_alias_unresolved", lambda content: False)
        assert _r3_outcome(_R3_PROBE) == _R3_ACCUSED
    assert _r3_outcome(_R3_PROBE) == _R3_REFUSED


def test_mutation_kill_b_a_function_scope_only_closure_loses_the_module_scope_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the closure runs over function bodies only, not over the whole module.

    Apply the mutant, confirm the module-scope spelling of the identical program is readmitted
    while its function-scope twin still refuses, revert, and confirm both refuse.  Recorded: a
    closure that is not whole-module splits one program into two verdicts on indentation.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    module_scope = "correct-explicit-loop-collection-alias-module-scope"
    real = correction.record_collection_alias_unresolved

    def function_scope_only(tree: ast.Module) -> bool:
        bodies = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        return real(ast.Module(body=cast("list[ast.stmt]", bodies), type_ignores=[]))

    assert _r3_outcome(module_scope) == _R3_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction, "record_collection_alias_unresolved", function_scope_only)
        assert _r3_outcome(module_scope) == _R3_ACCUSED
        assert _r3_outcome(_R3_PROBE) == _R3_REFUSED, "the function-scope twin still refuses"
    assert _r3_outcome(module_scope) == _R3_REFUSED


@pytest.mark.parametrize(
    "name",
    (
        "correct-explicit-loop-collection-container-escape",
        "correct-explicit-loop-collection-attribute-escape",
    ),
)
def test_mutation_kill_c_treating_a_display_escape_as_safe_readmits_the_escaped_rows(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutant: the closure keeps its alias edges and drops the display-escape set.

    Apply the mutant, confirm the container and field escapes are readmitted while the plain
    alias still refuses, revert, and confirm the refusal returns.  Recorded: without the escape
    half the whole false accusation is reachable through one extra pair of braces.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real_edges = correction._alias_edges

    def edges_without_escapes(tree: ast.Module) -> tuple[dict[str, set[str]], frozenset[str]]:
        edges, _escaped = real_edges(tree)
        return edges, frozenset()

    assert _r3_outcome(name) == _R3_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction, "_alias_edges", edges_without_escapes)
        assert _r3_outcome(name) == _R3_ACCUSED
        assert _r3_outcome(_R3_PROBE) == _R3_REFUSED, "the plain-alias row still refuses"
    assert _r3_outcome(name) == _R3_REFUSED


# --- Round 4: the record-derived binding closure -----------------------------------------


@pytest.fixture(scope="session")
def audit_fix_r4_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_R4_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_4_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_R4_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_R4_ROWS) == 45
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_R4_ROWS) == 35
    assert set(_AUDIT_FIX_R4_ROWS_BY_NAME) == set(_AUDIT_FIX_R4_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_R4_SOURCES.items()
    } == {
        name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_R4_ROWS_BY_NAME.items()
    }
    # Every fixture is a syntactically valid program, so no row can pass on a parse failure.
    for _name, (_case_key, source) in _AUDIT_FIX_R4_SOURCES.items():
        ast.parse(source)


@pytest.mark.parametrize("row", _AUDIT_FIX_R4_ROWS, ids=lambda row: row["fixture_name"])
def test_all_45_audit_fix_round_4_rows_execute(
    row: dict[str, Any], audit_fix_r4_rows: dict[str, dict[str, Any]]
) -> None:
    name = str(row["fixture_name"])
    observed = audit_fix_r4_rows[name]
    pinned = (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    if name in _R5_MOVES_R4_ROWS:
        before, after = _R5_MOVES_R4_ROWS[name]
        assert pinned == before, "the round-4 oracle pin is evidence and may not be edited"
        expected, expected_identical = after, False
    else:
        expected, expected_identical = pinned, bool(row["expected_frozen_v33_identical"])
    assert _outcome_tuple(observed["outcome"]) == expected
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is expected_identical


def test_no_correct_analysis_row_in_the_round_4_oracle_is_left_accused(
    audit_fix_r4_rows: dict[str, dict[str, Any]],
) -> None:
    """Thirty-five rows are complete Bonferroni corrections.  None of them is still accused.

    Round 4 left exactly one accused -- `correct-record-in-helper-distinct-parameter-name`, the
    record handed to a helper storing through its own, differently named parameter -- and pinned
    it as an open false accusation rather than leaving it to a later audit.  Round 5 closes it,
    so the residual set is empty and this test is what keeps it from growing quietly.  The row
    the oracle still declares open is asserted to be exactly the one round 5 closed, so the
    declaration cannot be quietly edited away either.
    """

    accused = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R4_ROWS
        if row["correct_analysis"]
        and audit_fix_r4_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    }
    assert accused == _R4_OPEN_RESIDUAL == set()
    declared = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R4_ROWS
        if row.get("expected_open_false_accusation")
    }
    assert declared == _R4_CLOSED_IN_ROUND_5
    assert _outcome_tuple(audit_fix_r4_rows[next(iter(_R4_CLOSED_IN_ROUND_5))]["outcome"]) == (
        "abstain",
        "pvalue-family-collection-unresolved",
        (),
        None,
    )


@pytest.mark.parametrize("name", _RECORD_DERIVED_ROWS)
def test_a_record_derived_store_lands_on_its_through_name_siblings_frozen_reason(
    name: str, audit_fix_r4_rows: dict[str, dict[str, Any]]
) -> None:
    """The reason pin is recomputed from the sibling rather than transcribed from 3.4 output.

    3.3 classifies these rows, so the round-1/round-2 authority -- the frozen reason for the row
    itself -- is unavailable.  The authority is the frozen 3.3 reason for the identical program
    with the same store written through the collection's own name.  The equality is asserted
    three ways: shipped 3.4 on the derived row, the oracle pin, and the live frozen 3.3 row of
    the sibling.
    """

    row = _AUDIT_FIX_R4_ROWS_BY_NAME[name]
    sibling = str(row["expected_reason_sibling"])
    assert sibling in _AUDIT_FIX_R4_SOURCES, name
    sibling_key, sibling_source = _AUDIT_FIX_R4_SOURCES[sibling]
    sibling_frozen = _run_v33(sibling_key, sibling_source)
    observed = audit_fix_r4_rows[name]["outcome"]
    assert sibling_frozen.state == "abstain"
    assert observed.state == "abstain"
    assert (
        observed.reason_or_classification
        == sibling_frozen.reason_or_classification
        == str(row["expected_reason"])
    )
    # The pair really is the same program up to the binding the store travels through: the
    # frozen pipeline classifies the derived spelling and refuses the through-name one.
    assert audit_fix_r4_rows[name]["frozen"].state == "candidate"


def test_the_closed_reason_set_is_unchanged_by_round_4() -> None:
    """Round 4 adds no reason: it emits the same reason round 3 does, already in the set of 61."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _COLLECTION_ALIAS_REASON,
    )

    assert _COLLECTION_ALIAS_REASON in _CLOSED_REASONS
    assert len(_CLOSED_REASONS) == 61
    for row in _AUDIT_FIX_R4_ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in _CLOSED_REASONS


def test_the_keys_view_needs_no_closure_because_its_store_is_through_the_name() -> None:
    """`X.keys()` hands out keys, and the store a key reaches is written through `X` itself.

    The frozen pipeline already refuses that row, so there is no false accusation for a key rule
    to close, and the closure deliberately leaves the key half of every unpack alone.
    """

    name = "correct-keys-view-store-through-name"
    case_key, source = _AUDIT_FIX_R4_SOURCES[name]
    frozen = _run_v33(case_key, source)
    assert frozen.state == "abstain"
    assert frozen.reason_or_classification == "pvalue-family-collection-unresolved"
    tree = ast.parse(source)
    # Non-vacuity: the keys view really is the iterator under test.
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "keys"
        for node in ast.walk(tree)
    )


@pytest.mark.parametrize("name", sorted(_R4_READ_ONLY_ROWS))
def test_a_read_only_record_derived_binding_is_never_refused(name: str) -> None:
    """The closure is over stores and mutations.  A live binding that is only read is clean."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_collection_alias_unresolved,
        record_derived_names,
    )

    _case_key, source = _AUDIT_FIX_R4_SOURCES[name]
    tree = ast.parse(source)
    # Non-vacuity: the binding really is present, and the closure really does enumerate it.
    assert record_derived_names(tree, frozenset({"results"})) > {"results"}, name
    assert record_collection_alias_unresolved(tree) is False


def test_the_record_derived_enumeration_covers_every_named_form() -> None:
    """Each enumerated binding form binds the name the fixture spells it with.

    The refusal rows above prove the closure fires; this proves it fires for the reason claimed,
    by naming the binding each fixture introduces rather than only its outcome.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_derived_names,
    )

    for name, expected in _R4_NAMED_BINDINGS.items():
        _case_key, source = _AUDIT_FIX_R4_SOURCES[name]
        assert expected <= record_derived_names(ast.parse(source), frozenset({"results"})), name


def test_a_bare_iteration_target_is_not_enumerated_as_a_record() -> None:
    """The boundary that keeps four pinned true accusations alive.

    Iterating a mapping yields keys and iterating a collected p-value table yields floats, and
    the collection's seed does not say which, so a bare `for x in X` target is not a record.
    Where a bare iteration really does hand out records, the store it reaches is written through
    the collection's own name and the frozen engine already refuses it, which the
    `correct-keys-view-store-through-name` row pins.  Both halves are asserted on hand-written
    modules so neither depends on a fixture.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_collection_alias_unresolved,
        record_derived_names,
    )

    bare = ast.parse(
        "results = [score(name) for name in NAMES]\nfor value in results:\n    value.round(2)\n"
    )
    through_name = ast.parse(
        'results = {}\nresults[name] = row\nfor key in results:\n    results[key]["p"] = 1.0\n'
    )
    assert record_derived_names(bare, frozenset({"results"})) == {"results"}
    assert record_collection_alias_unresolved(bare) is False
    # The through-name store is what a bare iteration over a real record table reaches, and the
    # collection's own stores are excluded because the frozen engine already judges them.
    assert record_derived_names(through_name, frozenset({"results"})) == {"results"}


def test_an_async_for_over_a_record_view_binds_the_record() -> None:
    """`async for` is the same binding form as `for` and is enumerated with it."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        record_derived_names,
    )

    tree = ast.parse(
        "results = {}\n"
        "results[name] = row\n"
        "async def rescale():\n"
        "    async for record in results.values():\n"
        '        record["p"] = 1.0\n'
    )
    assert "record" in record_derived_names(tree, frozenset({"results"}))


@pytest.mark.parametrize("name", sorted(_R4_MOVEMENT_ROWS))
def test_round_4_keeps_every_pinned_movement_and_every_true_accusation(
    name: str, audit_fix_r4_rows: dict[str, dict[str, Any]]
) -> None:
    """A closure that refused binding rather than storing would lose all nine of these."""

    assert _outcome_tuple(audit_fix_r4_rows[name]["outcome"]) == _R4_MOVEMENT_ROWS[name]


def test_round_3_rows_are_unmoved_by_round_4(
    audit_fix_r3_rows: dict[str, dict[str, Any]],
) -> None:
    """Round 4 widens which names the round-3 walk covers and moves no round-3 row.

    The round-3 oracle is re-executed against the widened closure here rather than only in its
    own block, so a round-4 widening that happened to flip a round-3 row fails in the round-4
    block that caused it.
    """

    for row in _AUDIT_FIX_R3_ROWS:
        name = str(row["fixture_name"])
        assert _outcome_tuple(audit_fix_r3_rows[name]["outcome"]) == (
            str(row["expected_outcome"]),
            str(row["expected_reason"]),
            tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
            cast("int | None", row.get("expected_authorized_count")),
        ), name


# --- Round-4 named mutation kills: apply, confirm, revert, record ----------------------


def _r4_outcome(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _AUDIT_FIX_R4_SOURCES[name]
    outcome, _census = _run_source(case_key, source)
    return _outcome_tuple(outcome)


_R4_PROBE = "correct-iteration-items-unpack-record-store"
_R4_SUBSCRIPT_PROBE = "correct-subscript-subscript-bound-record-store"
_R4_ACCUSED = ("candidate", "none", (), 6)
_R4_REFUSED = ("abstain", "pvalue-family-collection-unresolved", (), None)


def test_mutation_kill_d_dropping_the_record_derived_edges_readmits_the_whole_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the closure keeps the round-3 alias component and enumerates nothing beyond it.

    Apply the mutant, confirm the reported blocker and every other newly closed row come back as
    the accusations the audit reproduced, revert, and confirm the refusals return.  Recorded:
    this is the whole round-4 delta, and the round-3 probe still refuses under it, so the two
    rounds are shown to close different routes rather than the same one twice.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    def no_derivation(
        tree: ast.Module, aliases: frozenset[str], census: Any = None
    ) -> tuple[frozenset[str], frozenset[str]]:
        # Round 7 renamed the entry point the closure calls to `record_derived_roles`, which
        # returns the derived names beside the subset rule A(1) reached only by an insertion.
        # The mutant is unchanged in meaning: enumerate nothing beyond the alias component.
        return aliases, frozenset()

    assert _r4_outcome(_R4_PROBE) == _R4_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction, "record_derived_roles", no_derivation)
        assert _r4_outcome(_R4_PROBE) == _R4_ACCUSED
        assert _r4_outcome(_R4_SUBSCRIPT_PROBE) == _R4_ACCUSED
        # The round-3 route is a different one and is untouched by this mutant.
        assert _r3_outcome("correct-explicit-loop-collection-alias-store") == _R3_REFUSED, (
            "the round-3 alias probe still refuses"
        )
    assert _r4_outcome(_R4_PROBE) == _R4_REFUSED


def test_mutation_kill_e_dropping_the_subscript_half_loses_the_lookup_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: only a Name already known to be a record counts as a record expression.

    Apply the mutant, confirm the subscript, `get`, `setdefault`, and walrus-lookup rows are
    readmitted while every iteration row still refuses, revert, and confirm the refusals return.
    Recorded: the iteration half and the subscript half are independent, so neither alone is the
    closure.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    def name_only(self: Any, node: ast.expr) -> bool:
        return isinstance(node, ast.Name) and node.id in self.records

    subscript_rows = (
        _R4_SUBSCRIPT_PROBE,
        "correct-subscript-get-bound-record-store",
        "correct-subscript-setdefault-bound-record-store",
        "correct-walrus-get-bound-record-store",
    )
    for row in subscript_rows:
        assert _r4_outcome(row) == _R4_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction._RecordDerivation, "is_record", name_only)
        for row in subscript_rows:
            assert _r4_outcome(row) == _R4_ACCUSED, row
        assert _r4_outcome(_R4_PROBE) == _R4_REFUSED, "the iteration half still refuses"
    for row in subscript_rows:
        assert _r4_outcome(row) == _R4_REFUSED


def test_mutation_kill_f_dropping_the_iteration_half_loses_the_view_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: iterating anything yields an opaque element.

    Apply the mutant, confirm the reported blocker and the other view and wrapper rows are
    readmitted while the subscript row still refuses, revert, and confirm the refusals return.
    Recorded: this is the other half of the pair mutation kill E opens.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    iteration_rows = (
        _R4_PROBE,
        "correct-iteration-values-loop-record-store",
        "correct-iteration-enumerate-values-record-store",
        "correct-iteration-zip-values-record-store",
    )
    for row in iteration_rows:
        assert _r4_outcome(row) == _R4_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._RecordDerivation,
            "element_shape",
            lambda self, node: correction._OPAQUE,
        )
        for row in iteration_rows:
            assert _r4_outcome(row) == _R4_ACCUSED, row
        assert _r4_outcome(_R4_SUBSCRIPT_PROBE) == _R4_REFUSED, "the subscript half still refuses"
    for row in iteration_rows:
        assert _r4_outcome(row) == _R4_REFUSED


def test_mutation_kill_g_treating_the_key_element_as_a_record_swallows_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: both halves of an `items()` unpack are records.

    Apply the mutant, confirm the read-only presentation loop that calls a method on the key is
    refused -- a true accusation swallowed -- while the real probes still refuse for their own
    reason, revert, and confirm the accusation returns.  Recorded: the key half is not a record,
    and the over-refusal it would cause is a lost finding rather than a harmless extra abstention.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._RecordDerivation._call_element_shape

    def key_is_a_record(self: Any, node: ast.Call) -> object:
        shape = real(self, node)
        if isinstance(shape, tuple):
            return tuple(correction._RECORD for _ in shape)
        return shape

    guard = "positive-read-only-items-loop-key-method-call"
    assert _r4_outcome(guard) == _R4_ACCUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction._RecordDerivation, "_call_element_shape", key_is_a_record)
        assert _r4_outcome(guard) == _R4_REFUSED
        assert _r4_outcome(_R4_PROBE) == _R4_REFUSED, "the real probe refuses either way"
    assert _r4_outcome(guard) == _R4_ACCUSED


def test_mutation_kill_h_treating_a_bare_iteration_target_as_a_record_costs_four_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a bare `for x in X` target is enumerated as a record.

    Apply the mutant, confirm two envelope positives and two open-corpus missteps lose their
    accusations, revert, and confirm all four come back.  Recorded: the boundary is not a
    stylistic choice.  E10 P5 and E12 P5 write a partial Holm adjustment as
    `for row, adjusted in zip(primary, p_adjusted): row["p_adjusted"] = ...` with the correction
    terminal itself plainly visible, and the two corpus rows read a loop variable of a tracked
    list into a display; refusing on either would trade four real findings for no closed route.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._RecordDerivation.element_shape

    def bare_name_is_a_record(self: Any, node: ast.expr) -> object:
        if isinstance(node, ast.Name) and node.id in self.mappings:
            return self.sequences.get(node.id, correction._RECORD)
        return real(self, node)

    rows = (
        "E10:P5:c51d08801b3d0ba4e532",
        "E12:P5:54667dd7c39067c8c2c8",
        "corpus:spec-21",
        "corpus:spec-45",
    )
    for key in rows:
        assert _corpus_outcome(key)[0] == "candidate", key
    with monkeypatch.context() as patch:
        patch.setattr(correction._RecordDerivation, "element_shape", bare_name_is_a_record)
        for key in rows:
            assert _corpus_outcome(key) == _R4_REFUSED, key
        assert _r4_outcome(_R4_PROBE) == _R4_REFUSED, "the real probe refuses either way"
    for key in rows:
        assert _corpus_outcome(key)[0] == "candidate", key


# --- Round 5: the project-local storing-helper closure ---------------------------------


@pytest.fixture(scope="session")
def audit_fix_r5_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_R5_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_5_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_R5_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_R5_ROWS) == 25
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_R5_ROWS) == 18
    assert set(_AUDIT_FIX_R5_ROWS_BY_NAME) == set(_AUDIT_FIX_R5_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_R5_SOURCES.items()
    } == {
        name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_R5_ROWS_BY_NAME.items()
    }
    # Every fixture is a syntactically valid program, so no row can pass on a parse failure.
    for _name, (_case_key, source) in _AUDIT_FIX_R5_SOURCES.items():
        ast.parse(source)


@pytest.mark.parametrize("row", _AUDIT_FIX_R5_ROWS, ids=lambda row: row["fixture_name"])
def test_all_25_audit_fix_round_5_rows_execute(
    row: dict[str, Any], audit_fix_r5_rows: dict[str, dict[str, Any]]
) -> None:
    name = str(row["fixture_name"])
    observed = audit_fix_r5_rows[name]
    pinned = (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    if name in _R6_MOVES_R5_ROWS:
        before, after = _R6_MOVES_R5_ROWS[name]
        assert pinned == before, "the round-5 oracle pin is evidence and may not be edited"
        expected, expected_identical = after, False
    else:
        expected, expected_identical = pinned, bool(row["expected_frozen_v33_identical"])
    assert _outcome_tuple(observed["outcome"]) == expected
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is expected_identical


def test_the_round_5_open_residual_is_the_imported_helper_and_round_6_closes_it(
    audit_fix_r5_rows: dict[str, dict[str, Any]],
) -> None:
    """Eighteen rows are correct analyses.  Round 5 left exactly one accused; round 6 leaves none.

    The one was `correct-record-in-helper-imported-from-a-sibling-module`: this recognizer reads a
    single source file, so a callee defined in another module resolves to nothing it can read.
    Round 5 declined to refuse on an unresolvable callee because that would have refused every
    builtin and library call the pinned evidence rows depend on.  Round 6 refuses on an
    unresolvable callee only when it is handed a tracked object and only when it is not on the
    measured read-only allowlist, so the row is decided without widening what the recognizer
    reads.  The round-5 oracle still declares it as its open false accusation, and the move is
    declared here rather than by editing that oracle.
    """

    accused = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R5_ROWS
        if row["correct_analysis"]
        and audit_fix_r5_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    }
    assert accused == _R5_OPEN_RESIDUAL
    declared = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R5_ROWS
        if row.get("expected_open_false_accusation")
    }
    assert declared == _R5_CLOSED_IN_ROUND_6
    assert declared == set(_R6_MOVES_R5_ROWS)


@pytest.mark.parametrize("name", _HELPER_STORE_ROWS)
def test_a_helper_parameter_store_lands_on_its_through_name_siblings_frozen_reason(
    name: str, audit_fix_r5_rows: dict[str, dict[str, Any]]
) -> None:
    """The reason pin is recomputed from the sibling rather than transcribed from 3.4 output.

    3.3 classifies these rows, so the round-1/round-2 authority -- the frozen reason for the row
    itself -- is unavailable.  The authority is the frozen 3.3 reason for the identical program
    with the same correction written through the collection's own name.  The equality is
    asserted three ways: shipped 3.4 on the helper row, the oracle pin, and the live frozen 3.3
    row of the sibling.
    """

    row = _AUDIT_FIX_R5_ROWS_BY_NAME[name]
    sibling = str(row["expected_reason_sibling"])
    assert sibling in _AUDIT_FIX_R5_SOURCES, name
    sibling_key, sibling_source = _AUDIT_FIX_R5_SOURCES[sibling]
    sibling_frozen = _run_v33(sibling_key, sibling_source)
    observed = audit_fix_r5_rows[name]["outcome"]
    assert sibling_frozen.state == "abstain"
    assert observed.state == "abstain"
    assert (
        observed.reason_or_classification
        == sibling_frozen.reason_or_classification
        == str(row["expected_reason"])
    )
    # The pair really is the same program up to where the store is written: the frozen pipeline
    # classifies the helper spelling and refuses the through-name one.
    assert audit_fix_r5_rows[name]["frozen"].state == "candidate"


def test_the_closed_reason_set_is_unchanged_by_round_5() -> None:
    """Round 5 adds no reason: it emits the reason rounds 3 and 4 do, already in the set of 61."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _COLLECTION_ALIAS_REASON,
    )

    assert _COLLECTION_ALIAS_REASON in _CLOSED_REASONS
    assert len(_CLOSED_REASONS) == 61
    for row in _AUDIT_FIX_R5_ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in _CLOSED_REASONS


@pytest.mark.parametrize("name", sorted(_R5_CAPTURING_ROWS))
def test_every_refused_row_names_a_captured_binding(name: str) -> None:
    """Non-vacuity: the closure fires because a helper captured a name, not by accident.

    Each refused row is asserted to hand a specific name to a storing helper, named here rather
    than inferred from the row's outcome, and each read-only control is asserted to capture
    nothing at all.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
    )

    _case_key, source = _AUDIT_FIX_R5_SOURCES[name]
    assert _R5_CAPTURING_ROWS[name] <= helper_captured_names(ast.parse(source)), name


@pytest.mark.parametrize("name", sorted(_R5_NON_CAPTURING_ROWS))
def test_a_read_only_or_builtin_call_captures_no_tracked_name(name: str) -> None:
    """The closure is over stores.  A live helper call that only reads captures no tracked name.

    The capture set itself is not empty on these rows and is not meant to be: P3's own
    `compare_settings(roadside[outcome], park[outcome])` calls a project-local helper that reads
    `park_values.mean()`, which the frozen receiver-method census counts as a mutation of the
    two data frames.  Neither of those names is the record collection or anything derived from
    it, and that is exactly the assertion: no name the round-3 and round-4 closures track is
    captured here.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
        record_collection_alias_unresolved,
        record_collection_names,
        record_derived_names,
    )

    _case_key, source = _AUDIT_FIX_R5_SOURCES[name]
    tree = ast.parse(source)
    captured = helper_captured_names(tree)
    for collection in record_collection_names(tree):
        tracked = record_derived_names(tree, frozenset({collection}))
        assert captured & tracked == frozenset(), (name, collection)
    assert record_collection_alias_unresolved(tree) is False, name


def test_the_read_only_controls_really_do_resolve_their_callee() -> None:
    """The controls must hold because the helper only reads, not because the name never resolved.

    P3's own presentation loop binds `verdict` and `result`, and a name this module binds twice
    is not a resolvable callee.  A control spelled with one of those names would pass for the
    wrong reason, so the two read-only helpers are asserted to be resolvable definitions this
    module binds exactly once.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        _HelperStores,
    )

    for name, helper in (
        ("positive-read-only-helper-on-uncorrected-family", "significance_label"),
        ("positive-read-only-helper-on-the-whole-collection", "collection_summary"),
    ):
        _case_key, source = _AUDIT_FIX_R5_SOURCES[name]
        tree = ast.parse(source)
        resolved = _HelperStores(tree)
        definitions = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and id(node) in resolved._definitions
        }
        assert helper in definitions, name
        # And the call really is in the source, so the row is not passing on a missing edit.
        assert helper.encode("utf-8") + b"(" in source, name


def test_recursion_and_mutual_recursion_resolve_to_a_fixpoint() -> None:
    """A cyclic callee graph converges rather than needing a conservative refusal.

    Mutual recursion that never stores stays non-storing; mutual recursion that stores at one hop
    makes both sides storing and captures the caller's argument.  Both are asserted on
    hand-written modules so neither depends on a fixture.  The storing cycle also captures
    `entry`, the helpers' own parameter name, because names are matched module-wide exactly as
    they are in rounds 1 to 4: a name reused in two scopes can only add captures.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
    )

    read_only_cycle = ast.parse(
        "def left(entry):\n"
        "    return right(entry)\n"
        "\n"
        "def right(entry):\n"
        "    return left(entry)\n"
        "\n"
        "left(record)\n"
    )
    storing_cycle = ast.parse(
        "def left(entry):\n"
        '    entry["p"] = 1.0\n'
        "    return right(entry)\n"
        "\n"
        "def right(entry):\n"
        "    return left(entry)\n"
        "\n"
        "right(record)\n"
    )
    assert helper_captured_names(read_only_cycle) == frozenset()
    assert helper_captured_names(storing_cycle) == frozenset({"record", "entry"})


def test_rounds_3_and_4_rows_are_unmoved_by_round_5(
    audit_fix_r3_rows: dict[str, dict[str, Any]],
    audit_fix_r4_rows: dict[str, dict[str, Any]],
) -> None:
    """Round 5 adds one edge and moves no earlier row except the residual it was written to close.

    The round-3 canary `correct-explicit-loop-collection-helper-argument` -- the collection handed
    to a helper that stores through its parameter -- keeps the frozen reason the round-3 oracle
    pins for it, so the disposition round 3 left open is decided without moving the row.
    """

    for row in _AUDIT_FIX_R3_ROWS:
        name = str(row["fixture_name"])
        assert _outcome_tuple(audit_fix_r3_rows[name]["outcome"]) == (
            str(row["expected_outcome"]),
            str(row["expected_reason"]),
            tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
            cast("int | None", row.get("expected_authorized_count")),
        ), name
    assert _outcome_tuple(
        audit_fix_r3_rows["correct-explicit-loop-collection-helper-argument"]["outcome"]
    ) == ("abstain", "unresolved-manual-correction-present", (), None)
    moved = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R4_ROWS
        if _outcome_tuple(audit_fix_r4_rows[str(row["fixture_name"])]["outcome"])
        != (
            str(row["expected_outcome"]),
            str(row["expected_reason"]),
            tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
            cast("int | None", row.get("expected_authorized_count")),
        )
    }
    assert moved == set(_R5_MOVES_R4_ROWS)


@pytest.mark.parametrize("name", sorted(_R5_MOVEMENT_ROWS))
def test_round_5_keeps_every_pinned_movement_and_every_true_accusation(
    name: str, audit_fix_r5_rows: dict[str, dict[str, Any]]
) -> None:
    """A closure that refused on the call rather than on the store would lose all seven."""

    assert _outcome_tuple(audit_fix_r5_rows[name]["outcome"]) == _R5_MOVEMENT_ROWS[name]


# --- Round-5 named mutation kills: apply, confirm, revert, record ----------------------


def _r5_outcome(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _AUDIT_FIX_R5_SOURCES[name]
    outcome, _census = _run_source(case_key, source)
    return _outcome_tuple(outcome)


_R5_PROBE = "correct-record-in-helper-distinct-parameter-name"
_R5_READ_ONLY_PROBE = "positive-read-only-helper-on-uncorrected-family"
_R5_ACCUSED = ("candidate", "none", (), 6)
_R5_REFUSED = ("abstain", "pvalue-family-collection-unresolved", (), None)


def test_mutation_kill_i_dropping_the_interprocedural_edge_readmits_the_confirmed_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: no call is ever a capture, which is the pre-round-5 discipline exactly.

    Apply the mutant, confirm the confirmed blocker and every other newly closed row come back as
    the accusations the audit reproduced, revert, and confirm the refusals return.  Recorded:
    this is the whole round-5 delta, and the round-4 probe still refuses under it, so the two
    rounds are shown to close different routes rather than the same one twice.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    for name in _HELPER_STORE_ROWS:
        assert _r5_outcome(name) == _R5_REFUSED, name
    with monkeypatch.context() as patch:
        # Round 6 reads the capture census off the call-disposition object the classification path
        # already builds, so the mutant is injected there.  It is the same mutant: no call is ever
        # a capture.
        patch.setattr(correction._HelperStores, "captured_names", lambda self: frozenset())
        for name in _HELPER_STORE_ROWS:
            assert _r5_outcome(name) == _R5_ACCUSED, name
        # The round-4 route is a different one and is untouched by this mutant.
        assert _r4_outcome("correct-iteration-items-unpack-record-store") == _R4_REFUSED, (
            "the round-4 iteration probe still refuses"
        )
    for name in _HELPER_STORE_ROWS:
        assert _r5_outcome(name) == _R5_REFUSED, name


def test_mutation_kill_j_treating_every_call_argument_as_a_capture_loses_the_e17_p6_movement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a name read into any call argument is a capture, builtins and library calls too.

    Round 5 could have been written that way and would have closed the same probe.  Apply the
    mutant, confirm the pinned E17 P6 `strict_subset` movement is LOST and the read-only control
    on the uncorrected family loses its accusation, revert, and confirm both come back.
    Recorded: the frozen `len(OUTCOMES)` and `", ".join(MUSCULOSKELETAL)` non-capture discipline
    is what callee resolution exists to preserve, and the cost of dropping it is a pinned
    movement, not a stylistic difference.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._object_mutated_names

    def every_call_argument_is_a_capture(tree: ast.Module) -> frozenset[str]:
        extra = {
            argument.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for argument in (*node.args, *(item.value for item in node.keywords))
            if isinstance(argument, ast.Name) and isinstance(argument.ctx, ast.Load)
        }
        return real(tree) | frozenset(extra)

    assert _r5_outcome("positive-ap-e17-p6-unaltered") == (
        "candidate",
        "strict_subset",
        (0, 1, 2),
        7,
    )
    assert _r5_outcome(_R5_READ_ONLY_PROBE) == _R5_ACCUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction, "_object_mutated_names", every_call_argument_is_a_capture)
        assert _r5_outcome("positive-ap-e17-p6-unaltered") == (
            "abstain",
            "unresolved-manual-correction-present",
            (),
            None,
        ), "the pinned E17 P6 strict_subset movement is lost"
        assert _r5_outcome(_R5_READ_ONLY_PROBE) == _R5_REFUSED
        assert _r5_outcome(_R5_PROBE) == _R5_REFUSED, "the real probe refuses either way"
    assert _r5_outcome("positive-ap-e17-p6-unaltered") == (
        "candidate",
        "strict_subset",
        (0, 1, 2),
        7,
    )
    assert _r5_outcome(_R5_READ_ONLY_PROBE) == _R5_ACCUSED


def test_mutation_kill_k_treating_a_read_only_helper_as_storing_costs_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: every parameter of every resolvable callee is treated as stored through.

    Apply the mutant, confirm the read-only helper control on a genuinely uncorrected family and
    the read-only helper on the whole collection both lose their accusations, revert, and confirm
    both come back.  Recorded: the closure is over stores, not over calls, and this is also the
    non-vacuity proof that those two controls resolve their callee -- a control whose helper name
    never resolved would be unmoved by this mutant.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    controls = (_R5_READ_ONLY_PROBE, "positive-read-only-helper-on-the-whole-collection")
    for name in controls:
        assert _r5_outcome(name) == _R5_ACCUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_reaches_a_store",
            lambda self, *arguments: True,
        )
        for name in controls:
            assert _r5_outcome(name) == _R5_REFUSED, name
        assert _r5_outcome("positive-explicit-loop-uncorrected-family") == _R5_ACCUSED, (
            "the baseline with no helper at all is unmoved"
        )
        assert _r5_outcome(_R5_PROBE) == _R5_REFUSED, "the real probe refuses either way"
    for name in controls:
        assert _r5_outcome(name) == _R5_ACCUSED, name


# --- Round 6: the call-disposition closure ---------------------------------------------


@pytest.fixture(scope="session")
def audit_fix_r6_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_R6_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_6_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_R6_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_R6_ROWS) == 48
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_R6_ROWS) == 25
    assert set(_AUDIT_FIX_R6_ROWS_BY_NAME) == set(_AUDIT_FIX_R6_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_R6_SOURCES.items()
    } == {
        name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_R6_ROWS_BY_NAME.items()
    }
    # Every fixture is a syntactically valid program, so no row can pass on a parse failure.
    for _name, (_case_key, source) in _AUDIT_FIX_R6_SOURCES.items():
        ast.parse(source)


@pytest.mark.parametrize("row", _AUDIT_FIX_R6_ROWS, ids=lambda row: row["fixture_name"])
def test_all_48_audit_fix_round_6_rows_execute(
    row: dict[str, Any], audit_fix_r6_rows: dict[str, dict[str, Any]]
) -> None:
    observed = audit_fix_r6_rows[str(row["fixture_name"])]
    assert _outcome_tuple(observed["outcome"]) == (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v33_identical"])


def test_no_correct_analysis_row_in_the_round_6_oracle_is_left_accused(
    audit_fix_r6_rows: dict[str, dict[str, Any]],
) -> None:
    """Twenty-five rows are correct analyses.  None of them is accused, and none is pinned open.

    Round 5 left exactly one open false accusation, the helper defined in a sibling module.  Rule
    A decides it and the whole class it belongs to, so the residual set is empty and the oracle
    declares no row as an open false accusation.
    """

    accused = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R6_ROWS
        if row["correct_analysis"]
        and audit_fix_r6_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    }
    assert accused == set()
    declared = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R6_ROWS
        if row.get("expected_open_false_accusation")
    }
    assert declared == set()


@pytest.mark.parametrize("name", _R6_CLOSED_ROWS)
def test_a_refused_call_lands_on_its_through_name_siblings_frozen_reason(
    name: str, audit_fix_r6_rows: dict[str, dict[str, Any]]
) -> None:
    """The reason pin is recomputed from the sibling rather than transcribed from 3.4 output.

    3.3 classifies these rows, so the round-1/round-2 authority -- the frozen reason for the row
    itself -- is unavailable.  The authority is the frozen 3.3 reason for the identical program
    with the same correction written through the collection's own name.  The equality is asserted
    three ways: shipped 3.4 on the refused row, the oracle pin, and the live frozen 3.3 row of the
    sibling.
    """

    row = _AUDIT_FIX_R6_ROWS_BY_NAME[name]
    sibling = str(row["expected_reason_sibling"])
    assert sibling in _AUDIT_FIX_R6_SOURCES, name
    sibling_key, sibling_source = _AUDIT_FIX_R6_SOURCES[sibling]
    sibling_frozen = _run_v33(sibling_key, sibling_source)
    observed = audit_fix_r6_rows[name]["outcome"]
    assert sibling_frozen.state == "abstain"
    assert observed.state == "abstain"
    assert (
        observed.reason_or_classification
        == sibling_frozen.reason_or_classification
        == str(row["expected_reason"])
    )
    # The pair really is the same program up to what the call does: the frozen pipeline classifies
    # this spelling and refuses the through-name one.
    assert audit_fix_r6_rows[name]["frozen"].state == "candidate"


def test_the_closed_reason_set_is_unchanged_by_round_6() -> None:
    """Round 6 adds no reason: it emits the reason rounds 3 to 5 do, already in the set of 61."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _COLLECTION_ALIAS_REASON,
    )

    assert _COLLECTION_ALIAS_REASON in _CLOSED_REASONS
    assert len(_CLOSED_REASONS) == 61
    for row in _AUDIT_FIX_R6_ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in _CLOSED_REASONS


@pytest.mark.parametrize("name", sorted(_R6_CAPTURING_ROWS))
def test_every_refused_round_6_row_names_the_binding_its_call_writes_into(name: str) -> None:
    """Non-vacuity: the closure fires because a call writes into a named tracked object.

    Each refused row is asserted to hand a specific name to a call that writes into it, named here
    rather than inferred from the row's outcome.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
    )

    _case_key, source = _AUDIT_FIX_R6_SOURCES[name]
    assert _R6_CAPTURING_ROWS[name] <= helper_captured_names(ast.parse(source)), name


@pytest.mark.parametrize("name", _R6_READ_ONLY_ROWS + _R6_RECOVERED_ROWS)
def test_a_read_only_or_recovered_row_captures_no_tracked_name(name: str) -> None:
    """The rows that keep their accusation capture nothing the round-3 and round-4 closures track.

    The capture set itself is not empty on these rows and is not meant to be: P3's own
    `compare_settings(roadside[outcome], park[outcome])` calls a project-local helper that reads
    `park_values.mean()`, which the frozen receiver-method census counts as a mutation of the two
    data frames.  Neither of those names is the record collection or anything derived from it.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
        record_collection_alias_unresolved,
        record_collection_names,
        record_derived_names,
    )

    _case_key, source = _AUDIT_FIX_R6_SOURCES[name]
    tree = ast.parse(source)
    captured = helper_captured_names(tree)
    for collection in record_collection_names(tree):
        tracked = record_derived_names(tree, frozenset({collection}))
        assert captured & tracked == frozenset(), (name, collection)
    assert record_collection_alias_unresolved(tree) is False, name


def test_the_read_only_allowlist_is_a_closed_measured_constant() -> None:
    """The allowlist is a closed set, and the callees the audit named are not on it.

    A recognizer that allowlisted by module prefix, or by "looks like a library call", would admit
    the whole Direction-1 class again.  The named mutators stay off it whatever else is on it.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        _CALLBACK_BEARING_BUILTINS,
        _NEVER_READ_ONLY_CALLEES,
        _READ_ONLY_BUILTIN_CALLEES,
        _READ_ONLY_IMPORTED_CALLEES,
        _READ_ONLY_MODULE_APIS,
    )

    for forbidden in ("getattr", "setattr", "delattr", "exec", "eval", "vars", "globals"):
        assert forbidden in _NEVER_READ_ONLY_CALLEES
        assert forbidden not in _READ_ONLY_BUILTIN_CALLEES
        assert forbidden not in _READ_ONLY_IMPORTED_CALLEES
    assert not any(receiver == "operator" for receiver, _attribute in _READ_ONLY_MODULE_APIS)
    assert "partial" not in _READ_ONLY_BUILTIN_CALLEES | _READ_ONLY_IMPORTED_CALLEES
    # The measured builtins the evidence base depends on really are on it.  `sorted`, `min`, and
    # `max` carry a `key=` callable, so they live in the callback-bearing constant and are
    # read-only only while that callable is.
    assert {"len", "zip", "list", "enumerate", "set", "iter"} <= _READ_ONLY_BUILTIN_CALLEES
    assert {"sorted", "min", "max", "map", "filter"} <= _CALLBACK_BEARING_BUILTINS
    # And the measured library callees are too.
    assert "multipletests" in _READ_ONLY_IMPORTED_CALLEES
    assert {"mean", "stdev"} <= _READ_ONLY_IMPORTED_CALLEES
    # Round 7 keys the qualified half on the identity the imports give a name rather than on the
    # spelling at the call site, so the canonical receiver is what the entries carry: `pd` is
    # `pandas` because `import pandas as pd` says so, and a receiver spelled `pd` that no import
    # binds resolves to nothing and fails closed.
    assert {("statistics", "mean"), ("stats", "ttest_ind"), ("pandas", "DataFrame")} <= (
        _READ_ONLY_MODULE_APIS
    )
    assert not any(receiver == "pd" for receiver, _attribute in _READ_ONLY_MODULE_APIS)


def test_callee_resolution_is_per_scope_chain() -> None:
    """An unrelated parameter does not shadow a module-level definition; a rebinding does.

    Asserted on hand-written modules so neither half depends on a fixture.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        _HelperStores,
    )

    module = ast.parse(
        "def rescale(entry):\n"
        '    entry["p"] = 1.0\n'
        "\n"
        "def unrelated(rescale):\n"
        "    return rescale\n"
        "\n"
        "class Report:\n"
        '    rescale = "bonferroni"\n'
        "\n"
        "rescale(record)\n"
    )
    ambiguous = ast.parse(
        "if True:\n"
        "    def rescale(entry):\n"
        '        entry["p"] = 1.0\n'
        "else:\n"
        "    def rescale(entry):\n"
        "        return entry\n"
        "\n"
        "rescale(record)\n"
    )
    census = _HelperStores(module)
    call = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    )
    assert census._enclosing_scope(call) == 0
    assert census._scopes.resolve("rescale", 0) is not None
    # The unrelated parameter binds only inside its own function.
    unrelated = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef) and node.name == "unrelated"
    )
    assert census._scopes.resolve("rescale", id(unrelated)) is None
    # Two conditional definitions are ambiguous, so the callee resolves to nothing.
    ambiguous_census = _HelperStores(ambiguous)
    assert ambiguous_census._scopes.resolve("rescale", 0) is None


def test_a_definition_is_an_escape_and_a_dead_nested_definition_is_not() -> None:
    """Rule D, both halves, on hand-written modules."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
    )

    closure = ast.parse(
        "results = {}\n"
        "results[name] = row\n"
        "def rescale_all():\n"
        '    results[name]["p"] = 1.0\n'
        "rescale_all()\n"
    )
    dead = ast.parse(
        "results = {}\n"
        "results[name] = row\n"
        "def inspect(entry):\n"
        "    def never_called():\n"
        '        entry["p"] = 1.0\n'
        '    return entry["p"]\n'
        "inspect(results[name])\n"
    )
    assert "results" in helper_captured_names(closure)
    assert helper_captured_names(dead) & {"results", "entry"} == frozenset()


def test_rounds_3_to_5_rows_are_unmoved_by_round_6(
    audit_fix_r3_rows: dict[str, dict[str, Any]],
    audit_fix_r4_rows: dict[str, dict[str, Any]],
    audit_fix_r5_rows: dict[str, dict[str, Any]],
) -> None:
    """Round 6 moves exactly one earlier oracle row, and it is declared by name."""

    for rows, oracle in (
        (audit_fix_r3_rows, _AUDIT_FIX_R3_ROWS),
        (audit_fix_r4_rows, _AUDIT_FIX_R4_ROWS),
    ):
        for row in oracle:
            name = str(row["fixture_name"])
            pinned = (
                str(row["expected_outcome"]),
                str(row["expected_reason"]),
                tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
                cast("int | None", row.get("expected_authorized_count")),
            )
            expected = _R5_MOVES_R4_ROWS[name][1] if name in _R5_MOVES_R4_ROWS else pinned
            assert _outcome_tuple(rows[name]["outcome"]) == expected, name
    moved = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R5_ROWS
        if _outcome_tuple(audit_fix_r5_rows[str(row["fixture_name"])]["outcome"])
        != (
            str(row["expected_outcome"]),
            str(row["expected_reason"]),
            tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
            cast("int | None", row.get("expected_authorized_count")),
        )
    }
    assert moved == set(_R6_MOVES_R5_ROWS)


@pytest.mark.parametrize("name", sorted(_R6_MOVEMENT_ROWS))
def test_round_6_keeps_every_pinned_movement_and_every_true_accusation(
    name: str, audit_fix_r6_rows: dict[str, dict[str, Any]]
) -> None:
    """A closure that refused one library call too many would lose all four."""

    assert _outcome_tuple(audit_fix_r6_rows[name]["outcome"]) == _R6_MOVEMENT_ROWS[name]


@pytest.mark.parametrize("name", sorted(_R6_COST_ROWS))
def test_every_round_6_cost_is_pinned_by_name(
    name: str, audit_fix_r6_rows: dict[str, dict[str, Any]]
) -> None:
    """The five costs are refusals of genuinely uncorrected families, recorded not hidden."""

    row = _AUDIT_FIX_R6_ROWS_BY_NAME[name]
    assert row["correct_analysis"] is False
    assert _outcome_tuple(audit_fix_r6_rows[name]["outcome"]) == _R6_REFUSED


# --- Round-6 named mutation kills: apply, confirm, revert, record ----------------------


def _r6_outcome(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _AUDIT_FIX_R6_SOURCES[name]
    outcome, _census = _run_source(case_key, source)
    return _outcome_tuple(outcome)


_R6_ACCUSED = ("candidate", "none", (), 6)
_R6_REFUSED = ("abstain", "pvalue-family-collection-unresolved", (), None)
#: The rows rule A alone decides.  Every other refused row is reached by another round-6 rule as
#: well, so it stays refused under the rule-A mutant and is not evidence about rule A.
_R6_FAIL_CLOSED_PROBES = (
    "correct-record-in-unbound-dict-update",
    "correct-record-in-operator-setitem",
    "correct-record-in-getattr-setitem",
    "correct-record-in-functools-partial",
    "correct-record-in-static-method-stored-in-a-name",
    "correct-record-in-dict-dispatch-table",
    "correct-record-in-lambda-stored-in-a-list",
    "correct-record-in-decorator-supplied-wrapper",
    "correct-record-in-helper-imported-from-a-sibling-module",
    "correct-record-in-helper-defined-twice-conditionally",
    "correct-record-in-helper-imported-then-defined",
)
#: Rule A off also readmits the pandas callback row; allowlisting everything does not, because
#: rule C still carries the store from the callback to the collection.
_R6_FAIL_CLOSED_ONLY = ("correct-record-in-pandas-apply-over-the-values-view",)


def test_mutation_kill_a_dropping_the_fail_closed_rule_readmits_the_named_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: an unresolvable callee is a non-capture again, which is round 5 exactly.

    Apply the mutant, confirm the four named Direction-1 probes come back as the accusations the
    audit reproduced through the real pipeline, revert, and confirm the refusals return.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    for name in _R6_FAIL_CLOSED_PROBES:
        assert _r6_outcome(name) == _R6_REFUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_record_unresolvable",
            lambda self, node, owner: None,
        )
        for name in _R6_FAIL_CLOSED_PROBES + _R6_FAIL_CLOSED_ONLY:
            assert _r6_outcome(name) == _R6_ACCUSED, name
    for name in _R6_FAIL_CLOSED_PROBES + _R6_FAIL_CLOSED_ONLY:
        assert _r6_outcome(name) == _R6_REFUSED, name


def test_mutation_kill_b_allowlisting_every_callee_readmits_the_same_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: every callee is read-only, so the allowlist decides nothing.

    Apply the mutant, confirm the same four probes readmit, revert, and confirm the refusals
    return.  Recorded: the allowlist is what rule A rests on, and widening it to everything is the
    same defect round 5 had.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    with monkeypatch.context() as patch:
        patch.setattr(correction._HelperStores, "_read_only_callee", lambda self, node: True)
        for name in _R6_FAIL_CLOSED_PROBES:
            assert _r6_outcome(name) == _R6_ACCUSED, name
    for name in _R6_FAIL_CLOSED_PROBES:
        assert _r6_outcome(name) == _R6_REFUSED, name


def test_mutation_kill_c_refusing_every_library_call_loses_named_evidence_accusations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: no callee is ever read-only, so every library call with a tracked argument refuses.

    Round 6 could have been written that way and would have closed every Direction-1 probe.  Apply
    the mutant, confirm three DEPLOYED evidence rows lose their accusations -- E13:P5 and E17:P5
    their `candidate`/`strict_subset` rows and E15:N1 its `covered`/`complete` row -- along with
    the coverage guard and the read-only library controls, revert, and confirm all of them come
    back.  Recorded: the allowlist is measured from the callees the evidence base actually hands a
    tracked argument to, and the cost of dropping it is five named rows, not a stylistic
    difference.  E13:P5 is the row that puts the container-insertion entry on the list:
    `secondary_results.append(result)` stores the record somewhere else without writing into it.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    deployed = {
        "E13:P5:80091f37c722eba28e18": ("candidate", "strict_subset", (0, 1), 7),
        "E17:P5:f3217e701e0f2452afab": ("candidate", "strict_subset", (2, 3), 8),
        "E15:N1:f846b07b1d11131cec4d": ("covered", "complete", (0, 1, 2, 3), 4),
    }
    controls = (
        "positive-library-calls-over-the-collection",
        "positive-sorted-key-and-map-read-only-callbacks",
        "positive-collected-p-into-a-separate-output-dict",
    )
    for key, expected in deployed.items():
        assert _corpus_outcome(key) == expected, key
    for name in controls:
        assert _r6_outcome(name) == _R6_ACCUSED, name
    assert _r6_outcome("positive-covered-family-with-a-library-call") == (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    )
    with monkeypatch.context() as patch:
        patch.setattr(correction._HelperStores, "_read_only_callee", lambda self, node: False)
        for key in deployed:
            assert _corpus_outcome(key) == _R6_REFUSED, f"{key} loses its accusation"
        for name in controls:
            assert _r6_outcome(name) == _R6_REFUSED, name
        assert _r6_outcome("positive-covered-family-with-a-library-call") == _R6_REFUSED
        # The Direction-1 probes refuse either way, so the mutant is not a weaker closure.
        assert _r6_outcome("correct-record-in-functools-partial") == _R6_REFUSED
    for key, expected in deployed.items():
        assert _corpus_outcome(key) == expected, key
    for name in controls:
        assert _r6_outcome(name) == _R6_ACCUSED, name
    assert _r6_outcome("positive-covered-family-with-a-library-call") == (
        "covered",
        "complete",
        (0, 1, 2, 3, 4, 5),
        6,
    )


def test_mutation_kill_d_dropping_return_flow_readmits_the_identity_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: no call ever hands one of its arguments back.

    Apply the mutant, confirm both identity-helper rows readmit as accusations, revert, and
    confirm the refusals return.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    rows = ("correct-record-through-an-identity-helper",)
    for name in rows:
        assert _r6_outcome(name) == _R6_REFUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(correction._HelperStores, "hands_back_an_argument", lambda self, node: False)
        for name in rows:
            assert _r6_outcome(name) == _R6_ACCUSED, name
    for name in rows:
        assert _r6_outcome(name) == _R6_REFUSED, name


def test_mutation_kill_e_dropping_storing_callable_propagation_readmits_the_pandas_apply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a callable held in a name or a container is never a storing callable.

    Recorded: rule A alone does not reach a receiver's roots; rule C is what carries the store from
    the callback to the collection the receiver was built from.  Round 7 gave the same row a second
    and independent closure -- a callback-bearing call reaches its receiver's roots whether or not
    the callable beside it is readable -- so each mutant alone now leaves the row refused and the
    readmission needs both off.  The single-mutant assertions are kept, because "still refused" is
    the statement that the two rules overlap rather than that either one has stopped working.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    name = "correct-record-in-pandas-apply-over-the-values-view"
    assert _r6_outcome(name) == _R6_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores, "_carries_storing_callable", lambda self, node: False
        )
        assert _r6_outcome(name) == _R6_REFUSED, "round 7's receiver roots still close it"
    with monkeypatch.context() as patch:
        patch.setattr(correction._HelperStores, "_is_callback_bearing", lambda self, node: False)
        assert _r6_outcome(name) == _R6_REFUSED, "rule C still closes it"
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores, "_carries_storing_callable", lambda self, node: False
        )
        patch.setattr(correction._HelperStores, "_is_callback_bearing", lambda self, node: False)
        assert _r6_outcome(name) == _R6_ACCUSED
    assert _r6_outcome(name) == _R6_REFUSED


def test_mutation_kill_f_seeding_parameters_as_both_roles_loses_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a helper parameter is seeded as a mapping AND a sequence of records, as round 5 did.

    Apply the mutant, confirm the read-only bare-iteration row loses its accusation, revert, and
    confirm it comes back.  Recorded: the module-level bare-iteration boundary that keeps four
    pinned true accusations alive has to hold one scope in as well.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._HelperStores._reached_names
    name = "positive-helper-bare-iteration-over-the-collection"
    assert _r6_outcome(name) == _R6_ACCUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_reached_names",
            lambda self, callee, parameter, role: real(self, callee, parameter, None),
        )
        assert _r6_outcome(name) == _R6_REFUSED, "the bare-iteration accusation is lost"
    assert _r6_outcome(name) == _R6_ACCUSED


def test_mutation_kill_g_binding_starred_arguments_to_everything_loses_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a starred argument binds every parameter whatever it forwards, as round 5 did.

    Apply the mutant, confirm the `*record` forwarding row loses its accusation, revert, and
    confirm it comes back.  Recorded: `*record` forwards the dictionary's keys, and treating it as
    a handover of the record refuses a family that really was left uncorrected.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._HelperStores._argument_role
    name = "positive-helper-star-keys-forwarding"
    assert _r6_outcome(name) == _R6_ACCUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_argument_role",
            lambda self, node: None if isinstance(node, ast.Starred) else real(self, node),
        )
        assert _r6_outcome(name) == _R6_REFUSED, "the star-keys accusation is lost"
    assert _r6_outcome(name) == _R6_ACCUSED


def test_mutation_kill_h_the_round_5_module_wide_shadow_census_loses_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a name bound as a parameter or a store anywhere in the module is unresolvable.

    That is round 5's shadow census exactly.  It was harmless while an unresolvable callee was a
    non-capture; under rule A it is not, because an unresolvable callee handed a tracked object
    now fails closed.  Apply the mutant, confirm the read-only helper standing beside an unrelated
    parameter of the same name loses its accusation on a genuinely uncorrected family, revert, and
    confirm it comes back.  Recorded: per-scope resolution is not a refinement of the census, it
    is what stops rule A from refusing correct read-only code.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._ScopeCensus.resolve

    def module_wide_census(self: Any, name: str, scope_id: int) -> tuple[str, ast.AST] | None:
        for table in self.bindings.values():
            for kind, _node in table.get(name, ()):
                if kind in {"param", "store", "import"}:
                    return None
        return cast("tuple[str, ast.AST] | None", real(self, name, scope_id))

    name = "positive-read-only-helper-beside-an-unrelated-parameter"
    assert _r6_outcome(name) == _R6_ACCUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction._ScopeCensus, "resolve", module_wide_census)
        assert _r6_outcome(name) == _R6_REFUSED, "the read-only helper accusation is lost"
    assert _r6_outcome(name) == _R6_ACCUSED


# --- Round 7: the uniform fail-closed closure ------------------------------------------


@pytest.fixture(scope="session")
def audit_fix_r7_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_R7_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_7_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_R7_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_R7_ROWS) == 51
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_R7_ROWS) == 27
    assert set(_AUDIT_FIX_R7_ROWS_BY_NAME) == set(_AUDIT_FIX_R7_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_R7_SOURCES.items()
    } == {
        name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_R7_ROWS_BY_NAME.items()
    }
    # Every fixture is a syntactically valid program, so no row can pass on a parse failure.
    for _name, (_case_key, source) in _AUDIT_FIX_R7_SOURCES.items():
        ast.parse(source)


@pytest.mark.parametrize("row", _AUDIT_FIX_R7_ROWS, ids=lambda row: row["fixture_name"])
def test_all_51_audit_fix_round_7_rows_execute(
    row: dict[str, Any], audit_fix_r7_rows: dict[str, dict[str, Any]]
) -> None:
    observed = audit_fix_r7_rows[str(row["fixture_name"])]
    assert _outcome_tuple(observed["outcome"]) == (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v33_identical"])


def test_no_correct_analysis_row_in_the_round_7_oracle_is_left_accused(
    audit_fix_r7_rows: dict[str, dict[str, Any]],
) -> None:
    """Twenty-seven rows are correct analyses.  None is accused, and none is pinned open.

    Three of them are refused by a gate upstream of this closure rather than by it, and they are
    counted here too: what a correct analysis may never be is accused, whichever gate is what keeps
    it from being accused.
    """

    accused = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R7_ROWS
        if row["correct_analysis"]
        and audit_fix_r7_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    }
    assert accused == set()
    declared = {
        str(row["fixture_name"])
        for row in _AUDIT_FIX_R7_ROWS
        if row.get("expected_open_false_accusation")
    }
    assert declared == set()


@pytest.mark.parametrize("name", _R7_CLOSED_ROWS)
def test_a_round_7_refusal_lands_on_its_through_name_siblings_frozen_reason(
    name: str, audit_fix_r7_rows: dict[str, dict[str, Any]]
) -> None:
    """The reason pin is recomputed from the sibling rather than transcribed from 3.4 output.

    3.3 classifies these rows, so the round-1/round-2 authority -- the frozen reason for the row
    itself -- is unavailable.  The authority is the frozen 3.3 reason for the identical program
    with the same correction written through the collection's own name.
    """

    row = _AUDIT_FIX_R7_ROWS_BY_NAME[name]
    sibling = str(row["expected_reason_sibling"])
    assert sibling in _AUDIT_FIX_R7_SOURCES, name
    sibling_key, sibling_source = _AUDIT_FIX_R7_SOURCES[sibling]
    sibling_frozen = _run_v33(sibling_key, sibling_source)
    observed = audit_fix_r7_rows[name]["outcome"]
    assert sibling_frozen.state == "abstain"
    assert observed.state == "abstain"
    assert (
        observed.reason_or_classification
        == sibling_frozen.reason_or_classification
        == str(row["expected_reason"])
    )
    # The pair really is the same program up to what the call does: the frozen pipeline classifies
    # this spelling and refuses the through-name one.
    assert audit_fix_r7_rows[name]["frozen"].state == "candidate"


@pytest.mark.parametrize("name", _R7_UPSTREAM_ROWS)
def test_an_earlier_gate_row_is_refused_by_that_gate_and_not_by_this_closure(
    name: str, audit_fix_r7_rows: dict[str, dict[str, Any]]
) -> None:
    """A correct analysis an upstream gate declines carries that gate's reason, unchanged by 3.4.

    Asserting the frozen 3.3 row is byte-identical is what shows the refusal is inherited rather
    than produced here, so the row is honest evidence about the absence of an accusation and not
    about this round's rules.
    """

    row = _AUDIT_FIX_R7_ROWS_BY_NAME[name]
    observed = audit_fix_r7_rows[name]
    assert _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert observed["outcome"].state == "abstain"
    assert observed["outcome"].reason_or_classification == str(row["expected_reason"])
    assert str(row["expected_reason"]) in _CLOSED_REASONS
    assert str(row["expected_reason"]) != "pvalue-family-collection-unresolved"


def test_the_closed_reason_set_is_unchanged_by_round_7() -> None:
    """Round 7 adds no reason: every refusal it produces emits the reason rounds 3 to 6 do."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _COLLECTION_ALIAS_REASON,
    )

    assert _COLLECTION_ALIAS_REASON in _CLOSED_REASONS
    assert len(_CLOSED_REASONS) == 61
    for row in _AUDIT_FIX_R7_ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in _CLOSED_REASONS


@pytest.mark.parametrize("name", sorted(_R7_CAPTURING_ROWS))
def test_every_refused_round_7_row_names_the_binding_its_store_travels_through(name: str) -> None:
    """Non-vacuity: the closure fires because a named tracked object is written into.

    Each closed row names either the object handed to a call that writes into it, or the object a
    store is written through, rather than having the name inferred from the row's outcome.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
        record_collection_names,
        record_derived_names,
    )

    _case_key, source = _AUDIT_FIX_R7_SOURCES[name]
    tree = ast.parse(source)
    reached = helper_captured_names(tree)
    for collection in record_collection_names(tree):
        reached |= record_derived_names(tree, frozenset({collection}))
    assert _R7_CAPTURING_ROWS[name] <= reached, name


@pytest.mark.parametrize("name", _R7_RECOVERED_ROWS)
def test_a_recovered_round_7_row_captures_no_tracked_name(name: str) -> None:
    """The recovered rows capture nothing the round-3 and round-4 closures track.

    The capture set itself is not empty on these rows and is not meant to be: P3's own
    `compare_settings(roadside[outcome], park[outcome])` calls a project-local helper that reads
    `park_values.mean()`, which the frozen receiver-method census counts as a mutation of the two
    data frames.  Neither of those names is the record collection or anything derived from it.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        helper_captured_names,
        record_collection_alias_unresolved,
        record_collection_names,
        record_derived_names,
    )

    _case_key, source = _AUDIT_FIX_R7_SOURCES[name]
    tree = ast.parse(source)
    captured = helper_captured_names(tree)
    for collection in record_collection_names(tree):
        tracked = record_derived_names(tree, frozenset({collection}))
        assert captured & tracked == frozenset(), (name, collection)
    assert record_collection_alias_unresolved(tree) is False, name


def test_the_read_only_allowlist_is_keyed_on_import_resolved_targets() -> None:
    """The identity table is closed, and the forbidden callee set is kept exactly as it was."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        _CSV_WRITER_CONSTRUCTORS,
        _NEVER_READ_ONLY_CALLEES,
        _READ_ONLY_BOUND_CALLABLES,
        _READ_ONLY_CONTAINER_INSERTIONS,
        _READ_ONLY_MODULE_APIS,
        _READ_ONLY_MODULE_IDENTITIES,
        _HelperStores,
        _import_identity,
    )

    # Every canonical receiver an entry names is one the identity table can produce, so no entry
    # is dead and no entry can be reached by a spelling the imports do not justify.
    canonical = set(_READ_ONLY_MODULE_IDENTITIES.values())
    assert {receiver for receiver, _attribute in _READ_ONLY_MODULE_APIS} <= canonical
    assert _CSV_WRITER_CONSTRUCTORS <= _READ_ONLY_MODULE_APIS
    # The forbidden set is unchanged, and `update` stays off the insertion allowlist because
    # `dict.update(record, p=...)` is the measured round-6 unbound-mutation route.
    for forbidden in ("apply", "getattr", "setattr", "delattr", "exec", "eval", "vars", "globals"):
        assert forbidden in _NEVER_READ_ONLY_CALLEES
    assert "update" not in _READ_ONLY_CONTAINER_INSERTIONS
    # A bound method may stand in a callable position only if it cannot write into its receiver.
    assert {"pop", "setdefault"} & _READ_ONLY_BOUND_CALLABLES == set()
    assert {"get", "keys", "items", "values", "copy"} <= _READ_ONLY_BOUND_CALLABLES

    # Alias resolution, asserted on hand-written imports so it depends on no fixture.
    module = ast.parse(
        "import json as payload\n"
        "from json import dumps as serialize\n"
        "from operator import setitem as put\n"
        "from scipy import stats\n"
        "import pandas as pd\n"
        "payload.dumps(x)\n"
    )
    statements = {
        "payload": module.body[0],
        "serialize": module.body[1],
        "put": module.body[2],
        "stats": module.body[3],
        "pd": module.body[4],
    }
    assert _import_identity(statements["payload"], "payload") == "json"
    assert _import_identity(statements["serialize"], "serialize") == "json.dumps"
    assert _import_identity(statements["put"], "put") == "operator.setitem"
    assert _import_identity(statements["stats"], "stats") == "scipy.stats"
    assert _import_identity(statements["pd"], "pd") == "pandas"
    census = _HelperStores(module)
    call = next(node for node in ast.walk(module) if isinstance(node, ast.Call))
    assert census._qualified_target(cast("ast.Attribute", call.func), call) == ("json", "dumps")
    assert census._imported_target_is_read_only("json.dumps") is True
    assert census._imported_target_is_read_only("operator.setitem") is False


def test_class_bodies_are_off_the_function_lexical_chain() -> None:
    """Semantics fix D(1) and D(2), asserted on hand-written modules."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        _HelperStores,
    )

    module = ast.parse(
        "def inspect(entry):\n"
        '    return entry["p"]\n'
        "\n"
        "class Report:\n"
        "    def inspect(self):\n"
        '        self["p"] = 1.0\n'
        "\n"
        "    def show(self, entry):\n"
        "        return inspect(entry)\n"
    )
    census = _HelperStores(module)
    show = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef) and node.name == "show"
    )
    module_inspect = module.body[0]
    resolved = census._scopes.resolve("inspect", id(show))
    assert resolved is not None and resolved[1] is module_inspect
    # A name written directly in the class body still resolves in the class namespace.
    report = next(node for node in ast.walk(module) if isinstance(node, ast.ClassDef))
    class_resolved = census._scopes.resolve("inspect", id(report))
    assert class_resolved is not None and class_resolved[1] is not module_inspect

    declared = ast.parse(
        "def inspect(entry):\n"
        '    return entry["p"]\n'
        "\n"
        "def show(entry):\n"
        "    global inspect\n"
        "    return inspect(entry)\n"
    )
    declared_census = _HelperStores(declared)
    declared_show = next(
        node
        for node in ast.walk(declared)
        if isinstance(node, ast.FunctionDef) and node.name == "show"
    )
    declared_resolved = declared_census._scopes.resolve("inspect", id(declared_show))
    assert declared_resolved is not None and declared_resolved[1] is declared.body[0]

    ambiguous = ast.parse(
        "def inspect(entry):\n"
        '    return entry["p"]\n'
        "\n"
        "def rebind():\n"
        "    global inspect\n"
        "    inspect = None\n"
        "\n"
        "def show(entry):\n"
        "    global inspect\n"
        "    return inspect(entry)\n"
    )
    ambiguous_census = _HelperStores(ambiguous)
    rebind = next(
        node
        for node in ast.walk(ambiguous)
        if isinstance(node, ast.FunctionDef) and node.name == "rebind"
    )
    assert ambiguous_census._scopes.resolve("inspect", id(rebind)) is None


def test_rounds_3_to_6_rows_are_unmoved_by_round_7(
    audit_fix_r3_rows: dict[str, dict[str, Any]],
    audit_fix_r4_rows: dict[str, dict[str, Any]],
    audit_fix_r5_rows: dict[str, dict[str, Any]],
    audit_fix_r6_rows: dict[str, dict[str, Any]],
) -> None:
    """Round 7 moves no earlier oracle row, and the two move maps are empty by declaration.

    The oracle files are evidence and stay unedited.  A row that moves has to be declared here, so
    a silent edit of either side fails rather than passing quietly.
    """

    for rows, oracle, declared in (
        (audit_fix_r3_rows, _AUDIT_FIX_R3_ROWS, {}),
        (audit_fix_r4_rows, _AUDIT_FIX_R4_ROWS, _R5_MOVES_R4_ROWS),
        (audit_fix_r5_rows, _AUDIT_FIX_R5_ROWS, _R6_MOVES_R5_ROWS | _R7_MOVES_R5_ROWS),
        (audit_fix_r6_rows, _AUDIT_FIX_R6_ROWS, _R7_MOVES_R6_ROWS),
    ):
        for row in oracle:
            name = str(row["fixture_name"])
            pinned = (
                str(row["expected_outcome"]),
                str(row["expected_reason"]),
                tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
                cast("int | None", row.get("expected_authorized_count")),
            )
            expected = declared[name][1] if name in declared else pinned
            assert _outcome_tuple(rows[name]["outcome"]) == expected, name
    assert _R7_MOVES_R5_ROWS == {}
    assert _R7_MOVES_R6_ROWS == {}


@pytest.mark.parametrize("name", sorted(_R7_MOVEMENT_ROWS))
def test_round_7_keeps_every_pinned_movement_and_every_true_accusation(
    name: str, audit_fix_r7_rows: dict[str, dict[str, Any]]
) -> None:
    """A closure that refused one library call too many would lose all four."""

    assert _outcome_tuple(audit_fix_r7_rows[name]["outcome"]) == _R7_MOVEMENT_ROWS[name]


@pytest.mark.parametrize("name", sorted(_R7_COST_ROWS))
def test_every_round_7_cost_is_pinned_by_name(
    name: str, audit_fix_r7_rows: dict[str, dict[str, Any]]
) -> None:
    """The five costs are refusals of genuinely uncorrected families, recorded not hidden."""

    row = _AUDIT_FIX_R7_ROWS_BY_NAME[name]
    assert row["correct_analysis"] is False
    assert row["expected_gate"] == "inherited-boundary"
    assert _outcome_tuple(audit_fix_r7_rows[name]["outcome"]) == _R7_REFUSED


# --- Round-7 named mutation kills: apply, confirm, revert, record ----------------------


def _r7_outcome(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _AUDIT_FIX_R7_SOURCES[name]
    outcome, _census = _run_source(case_key, source)
    return _outcome_tuple(outcome)


_R7_ACCUSED = ("candidate", "none", (), 6)
_R7_REFUSED = ("abstain", "pvalue-family-collection-unresolved", (), None)
#: The four routes the callable classification alone decides.  Each reaches a callback-bearing
#: callee that is NOT on the never-allowlisted set, so the callable beside it really is consulted,
#: and none of them is a name, a display, or a `partial` of a storing definition, so the round-6
#: storing-callable propagation says nothing about them either.
_R7_CALLABLE_POSITION_PROBES = (
    "correct-record-in-transform-through-a-storing-wrapper",
    "correct-record-in-series-map-through-an-attribute-callable",
    "correct-record-in-sorted-key-through-a-dict-get-callable",
    "correct-record-in-map-through-an-identity-chain",
)
#: The four routes the receiver half decides.  `apply` is on the never-allowlisted set, so what
#: closes these is that a callback-bearing call writes through its receiver.
_R7_CALLBACK_RECEIVER_PROBES = (
    "correct-record-in-apply-through-a-storing-wrapper",
    "correct-record-in-apply-through-an-attribute-callable",
    "correct-record-in-apply-through-a-dict-get-callable",
    "correct-record-in-apply-through-an-identity-chain",
)
#: The two `apply` rows an earlier round already closes, carried as controls: the comprehension
#: lambda by the round-6 definition escape, the `partial` by the round-6 storing-callable
#: propagation.  Both stay refused under the round-7 receiver mutant, which is what separates them
#: from the four above.
_R7_INHERITED_APPLY_ROWS = (
    "correct-record-in-apply-through-a-comprehension-callable",
    "correct-record-in-apply-through-functools-partial",
)


def test_mutation_kill_a_dropping_value_flow_fail_closed_readmits_the_named_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a container insertion propagates no role and a lazy display is fresh again.

    That is round 6 exactly on the value side.  Apply the mutant, confirm the append route and the
    returned generator expression come back as the accusations the audit reproduced, revert, and
    confirm the refusals return.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._capture_roots
    lazy = (ast.Lambda, ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)

    def no_lazy_displays(
        node: ast.expr,
        records: frozenset[str] = frozenset(),
        mappings: frozenset[str] = frozenset(),
    ) -> frozenset[str]:
        if isinstance(node, lazy):
            return frozenset()
        return cast("frozenset[str]", real(node, records, mappings))

    rows = (
        "correct-record-in-held-append-then-setitem",
        "correct-record-through-a-returned-generator-expression",
    )
    for name in rows:
        assert _r7_outcome(name) == _R7_REFUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(correction._RecordDerivation, "_bind_insertion", lambda self, node: False)
        patch.setattr(correction, "_capture_roots", no_lazy_displays)
        for name in rows:
            assert _r7_outcome(name) == _R7_ACCUSED, name
    for name in rows:
        assert _r7_outcome(name) == _R7_REFUSED, name


def test_mutation_kill_b_dropping_callable_position_fail_closed_readmits_the_apply_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a callable position is read-only unless it is known to store, as round 6 asked.

    Apply the mutant, confirm all four apply routes rule C cannot see come back as accusations,
    revert, and confirm the refusals return.  Recorded: asking whether a callable is known to store
    admits every callable this recognizer cannot read, which is the whole defect.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    for name in _R7_CALLABLE_POSITION_PROBES:
        assert _r7_outcome(name) == _R7_REFUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_callable_arguments_are_read_only",
            lambda self, node: not self._carries_a_storing_callable(node),
        )
        for name in _R7_CALLABLE_POSITION_PROBES:
            assert _r7_outcome(name) == _R7_ACCUSED, name
        # The read-only controls are unmoved: the mutant admits more, never less.
        assert _r7_outcome("positive-transform-with-a-read-only-project-helper") == _R7_ACCUSED
        # The apply routes are decided by the receiver half and stay refused under this mutant.
        for name in _R7_CALLBACK_RECEIVER_PROBES:
            assert _r7_outcome(name) == _R7_REFUSED, name
    for name in _R7_CALLABLE_POSITION_PROBES:
        assert _r7_outcome(name) == _R7_REFUSED, name


def test_mutation_kill_c_keying_the_allowlist_on_spellings_costs_both_directions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a library callee is recognized by how it is spelled, as round 6 recognized it.

    Apply the mutant, confirm the namespace masquerade readmits as an accusation AND both import
    alias controls lose the accusations their uncorrected families earned, revert, and confirm all
    three come back.  Recorded: keying on spellings is one defect with two faces, and the mutant
    shows both at once.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    def by_spelling(self: Any, name: str, at: ast.AST) -> tuple[str | None, str | None]:
        for scope in self._scopes.scope_chain(self._enclosing_scope(at)):
            entries = self._scopes.bindings.get(scope, {}).get(name)
            if entries is None:
                continue
            if all(kind == "import" for kind, _node in entries):
                return "builtin", name
            return None, None
        return "builtin", name

    masquerade = "correct-record-in-a-json-namespace-masquerade"
    aliases = ("positive-import-alias-json", "positive-from-import-alias-dumps")
    assert _r7_outcome(masquerade) == _R7_REFUSED
    for name in aliases:
        assert _r7_outcome(name) == _R7_ACCUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(correction._HelperStores, "_bare_callee_target", by_spelling)
        patch.setattr(
            correction._HelperStores,
            "_qualified_target",
            lambda self, function, at: correction._module_api(function),
        )
        patch.setattr(
            correction._HelperStores, "_class_alias", lambda self, receiver, node, methods: None
        )
        assert _r7_outcome(masquerade) == _R7_ACCUSED, "the masquerade readmits"
        for name in aliases:
            assert _r7_outcome(name) == _R7_REFUSED, f"{name} loses its accusation"
    assert _r7_outcome(masquerade) == _R7_REFUSED
    for name in aliases:
        assert _r7_outcome(name) == _R7_ACCUSED, name


def test_mutation_kill_d_class_bodies_on_the_lexical_chain_lose_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a class body is an enclosing scope again, which is not what Python does.

    Apply the mutant, confirm the read-only method whose bare call resolves to the module function
    loses its accusation, revert, and confirm it comes back.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    def with_class_scopes(self: Any, scope_id: int) -> Any:
        current: int | None = scope_id
        while current is not None:
            yield current
            if current == 0:
                return
            current = self.scope_of.get(current)

    name = "positive-class-scope-lookup"
    assert _r7_outcome(name) == _R7_ACCUSED
    with monkeypatch.context() as patch:
        patch.setattr(correction._ScopeCensus, "scope_chain", with_class_scopes)
        assert _r7_outcome(name) == _R7_REFUSED, "the class-scope accusation is lost"
    assert _r7_outcome(name) == _R7_ACCUSED


def test_mutation_kill_e_classifying_callables_before_the_fixpoint_readmits_the_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a callable is judged by its own body census, without the storing fixpoint.

    Apply the mutant, confirm the wrapper that stores only by calling a storing helper readmits,
    revert, and confirm the refusal returns.  Recorded: the ordering is the rule, not an
    implementation detail -- the three other apply routes are unmoved by this mutant, because they
    fail on resolution rather than on what the callable does.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    name = "correct-record-in-transform-through-a-storing-wrapper"
    assert _r7_outcome(name) == _R7_REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_definition_is_storing",
            lambda self, definition: self._definition_stores(definition),
        )
        assert _r7_outcome(name) == _R7_ACCUSED
        for other in _R7_CALLABLE_POSITION_PROBES[1:]:
            assert _r7_outcome(other) == _R7_REFUSED, other
    assert _r7_outcome(name) == _R7_REFUSED


def test_mutation_kill_f_dropping_the_mapping_key_boundary_loses_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the freshness test forgets which parameters are mappings.

    Apply the mutant, confirm both fresh-key summaries lose their accusations, revert, and confirm
    they come back.  Recorded: the module-level bare-iteration boundary that keeps four pinned true
    accusations alive has to hold one scope in as well.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._HelperStores._body_roles
    rows = ("positive-summarize-keys-fresh", "positive-summarize-sorted-keys-fresh")
    for name in rows:
        assert _r7_outcome(name) == _R7_ACCUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(
            correction._HelperStores,
            "_body_roles",
            lambda self, callee, parameter, role: (
                real(self, callee, parameter, role)[0],
                frozenset(),
            ),
        )
        for name in rows:
            assert _r7_outcome(name) == _R7_REFUSED, f"{name} loses its accusation"
    for name in rows:
        assert _r7_outcome(name) == _R7_ACCUSED, name


def test_mutation_kill_g_dropping_the_callback_receiver_roots_readmits_the_apply_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a callback-bearing call reaches its receiver's roots only when round 6 said so.

    Round 6 added the receiver's roots when it already knew the argument carried a storing
    callable, which is exactly the question it could not answer for these six shapes.  Apply the
    mutant, confirm all six `apply` routes come back as the accusations the audit reproduced,
    revert, and confirm the refusals return.  Recorded: `apply` is on the never-allowlisted callee
    set and stays there, so what closes these rows is reaching the receiver at all.
    """

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    real = correction._HelperStores._is_callback_bearing
    for name in _R7_CALLBACK_RECEIVER_PROBES:
        assert _r7_outcome(name) == _R7_REFUSED, name
    with monkeypatch.context() as patch:
        # `_record_unresolvable` reads this predicate to decide whether to reach the receiver;
        # answering `False` there is round 6's disposition exactly, and the deferred pass is
        # unaffected because a call it never defers is a call it never re-asks.
        patch.setattr(correction._HelperStores, "_is_callback_bearing", lambda self, node: False)
        for name in _R7_CALLBACK_RECEIVER_PROBES:
            assert _r7_outcome(name) == _R7_ACCUSED, name
        # The two rows an earlier round already closes are unmoved, which is what makes them
        # controls for the four above rather than four more instances of the same closure.
        for name in _R7_INHERITED_APPLY_ROWS:
            assert _r7_outcome(name) == _R7_REFUSED, name
        assert real is not None
    for name in _R7_CALLBACK_RECEIVER_PROBES:
        assert _r7_outcome(name) == _R7_REFUSED, name
