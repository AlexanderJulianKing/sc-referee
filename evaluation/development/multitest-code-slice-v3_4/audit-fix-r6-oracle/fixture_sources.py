"""Deterministic source recipes for the MT 3.4 audit-fix round-6 oracle.

Every recipe is an anchored edit of one sealed envelope-17 case source, exactly as rounds 1 to 5
are.  The recipes own source selection and mutation only; the expected rows live in
`EXPECTED_ROWS.json` and are authored from the design, the frozen through-name sibling, and the
round-6 probe dispositions, never from analyzer output.

Round 6 works on the same classification side as rounds 3, 4, and 5, so the sealed P3
comprehension is again rewritten as the explicit loop the audit's reproduction used.  That
rewrite is one anchored edit applied to every row, and each row then differs from the others only
in the block placed immediately after the collection statement and in the definitions placed
before `def main():`.  That is the exact construction the audit ledger specifies, so the rows here
are the same programs the custodian ran through the real contract and audit pipeline.

Two kinds of row live side by side and must not be confused.

* A `correct-` row is a complete, correct Bonferroni pass over the six declared outcomes: every
  declared outcome's p is multiplied by the declared family size and capped before any verdict is
  read.  These may never be classified `candidate`.
* A `positive-` row leaves the family uncorrected and only reads it.  These must keep their
  accusation, and each one is a true accusation the round-5 closure lost or could have lost.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E17 = REPO / "evaluation/development/blind-envelope-17-2026-08-30/cases"
P3_KEY = "E17:P3:a2e031f79e31c80fd900"
P6_KEY = "E17:P6:b4e507c4b55954752f14"
P3 = E17 / "a2e031f79e31c80fd900/project/analysis.py"
P6 = E17 / "b4e507c4b55954752f14/project/analysis.py"

P3_COMPREHENSION = b"""    results = {
        outcome: compare_settings(roadside[outcome], park[outcome])
        for outcome in OUTCOMES
    }
"""
P3_EXPLICIT_LOOP = b"""    results = {}
    for outcome in OUTCOMES:
        results[outcome] = compare_settings(roadside[outcome], park[outcome])
"""
P3_MAIN_ANCHOR = b"def main():\n"
P3_IMPORT_ANCHOR = b"from scipy import stats\n"
P3_VERDICT_LINE = b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA else "not significant"\n'

#: The per-record Bonferroni body every helper row shares, written through a parameter named
#: `entry` so no module-wide name match can reach it.
CORRECTION_BODY = b'    entry["p"] = min(entry["p"] * family_size, 1.0)\n'
RESCALE_DEFINITION = b"def rescale(entry, family_size):\n" + CORRECTION_BODY + b"\n\n"
RESCALE_CALL = b"""
    for name, record in results.items():
        rescale(record, len(OUTCOMES))
"""

# --- Group 1: the callee this recognizer cannot resolve ---------------------------------------
#
# Each block is a complete, correct Bonferroni pass whose store is written by a callee round 5
# read as a non-capture.  Round 6 fails closed on all of them.
UNRESOLVABLE_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "unbound-dict-update": (
        b"""
    for name, record in results.items():
        dict.update(record, p=min(record["p"] * len(OUTCOMES), 1.0))
""",
        b"",
        b"",
    ),
    "operator-setitem": (
        b"""
    for name, record in results.items():
        operator.setitem(record, "p", min(record["p"] * len(OUTCOMES), 1.0))
""",
        b"",
        b"import operator\n",
    ),
    "getattr-setitem": (
        b"""
    for name, record in results.items():
        getattr(record, "__setitem__")("p", min(record["p"] * len(OUTCOMES), 1.0))
""",
        b"",
        b"",
    ),
    "functools-partial": (
        b"""
    adjust = functools.partial(rescale, family_size=len(OUTCOMES))
    for name, record in results.items():
        adjust(record)
""",
        RESCALE_DEFINITION,
        b"import functools\n",
    ),
    "static-method-stored-in-a-name": (
        b"""
    adjust = Bonferroni.rescale
    for name, record in results.items():
        adjust(record, len(OUTCOMES))
""",
        b"class Bonferroni:\n    @staticmethod\n    def rescale(entry, family_size):\n    "
        + CORRECTION_BODY
        + b"\n\n",
        b"",
    ),
    "dict-dispatch-table": (
        b"""
    for name, record in results.items():
        ADJUSTERS["bonferroni"](record, len(OUTCOMES))
""",
        b"def rescale(entry, family_size):\n"
        + CORRECTION_BODY
        + b'\n\nADJUSTERS = {"bonferroni": rescale}\n\n\n',
        b"",
    ),
    "lambda-stored-in-a-list": (
        b"""
    for name, record in results.items():
        ADJUSTERS[0](record, len(OUTCOMES))
""",
        b"ADJUSTERS = [lambda entry, family_size: entry.update(\n"
        b'    {"p": min(entry["p"] * family_size, 1.0)})]\n\n\n',
        b"",
    ),
    "decorator-supplied-wrapper": (
        RESCALE_CALL,
        b"def bonferroni(func):\n    def wrapper(entry, family_size):\n"
        b'        entry["p"] = min(entry["p"] * family_size, 1.0)\n'
        b"        return func(entry, family_size)\n    return wrapper\n\n\n"
        b'@bonferroni\ndef rescale(entry, family_size):\n    return entry["p"]\n\n\n',
        b"",
    ),
    "setattr-property-setter": (
        b"""
    for name, record in results.items():
        setattr(PSetter(record), "p", min(record["p"] * len(OUTCOMES), 1.0))
""",
        b"class PSetter:\n    def __init__(self, entry):\n        self._entry = entry\n\n"
        b'    @property\n    def p(self):\n        return self._entry["p"]\n\n'
        b'    @p.setter\n    def p(self, value):\n        self._entry["p"] = value\n\n\n',
        b"",
    ),
    "pandas-apply-over-the-values-view": (
        b"""
    pd.Series(list(results.values())).apply(rescale)
""",
        b'def rescale(entry):\n    entry["p"] = min(entry["p"] * len(OUTCOMES), 1.0)\n\n\n',
        b"",
    ),
    "helper-receiving-a-subscript-display": (
        b"""
    for name in results:
        rescale_all([results[name]], len(OUTCOMES))
""",
        b"def rescale_all(entries, family_size):\n    for entry in entries:\n    "
        + CORRECTION_BODY
        + b"\n\n",
        b"",
    ),
    "helper-imported-from-a-sibling-module": (
        RESCALE_CALL,
        b"",
        b"\nfrom corrections import rescale\n",
    ),
}

# --- Group 2: the shadowing census ------------------------------------------------------------
#
# Each row defines the correcting helper exactly once in the scope the call site reads it from.
# Round 5 gathered every parameter and every store module-wide and refused to resolve any of them,
# so the correction stayed invisible and the row was published as an accusation.  The two rows at
# the end are genuinely ambiguous and fail closed instead.
SHADOWING_ROWS: dict[str, bytes] = {
    "beside-an-unrelated-parameter": b"def rescale(entry, family_size):\n"
    + CORRECTION_BODY
    + b"\n\ndef unrelated(rescale):\n    return rescale\n\n\n",
    "beside-a-class-attribute": b"def rescale(entry, family_size):\n"
    + CORRECTION_BODY
    + b'\n\nclass Report:\n    rescale = "bonferroni"\n\n\n',
    "beside-a-second-nested-definition": b"def rescale(entry, family_size):\n"
    + CORRECTION_BODY
    + b'\n\ndef report():\n    def rescale(entry):\n        return entry["p"]\n'
    b"    return rescale\n\n\n",
    "beside-an-unused-nested-definition": b"def rescale(entry, family_size):\n"
    + CORRECTION_BODY
    + b"\n\ndef unused():\n    def rescale(entry, family_size):\n        return entry\n\n\n",
    "defined-twice-conditionally": b"if True:\n    def rescale(entry, family_size):\n    "
    + CORRECTION_BODY
    + b"else:\n    def rescale(entry, family_size):\n        return entry\n\n\n",
}
IMPORTED_THEN_DEFINED_IMPORT = b"from operator import getitem as rescale\n"

# --- Group 3: return flow ---------------------------------------------------------------------
RETURN_FLOW_ROWS: dict[str, tuple[bytes, bytes]] = {
    "record-through-an-identity-helper": (
        b"""
    for name, record in results.items():
        target = identity(record)
        target["p"] = min(target["p"] * len(OUTCOMES), 1.0)
""",
        b"def identity(entry):\n    return entry\n\n\n",
    ),
    "values-view-through-an-identity-helper": (
        b"""
    for record in identity(results.values()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
        b"def identity(entries):\n    return entries\n\n\n",
    ),
}

# --- Group 4: a definition is an escape -------------------------------------------------------
CLOSURE_ROWS: dict[str, tuple[bytes, bytes]] = {
    "nested-closure-over-the-collection": (
        b"""
    def rescale_all():
        for name in results:
            results[name]["p"] = min(
                results[name]["p"] * len(OUTCOMES), 1.0
            )
    rescale_all()
""",
        b"",
    ),
    "default-argument-capture": (
        b"""
    for name, record in results.items():
        def rescale(entry=record, family_size=len(OUTCOMES)):
            entry["p"] = min(entry["p"] * family_size, 1.0)
        rescale()
""",
        b"",
    ),
    "returned-nested-helper": (
        b"""
    for name, record in results.items():
        maker(record)(len(OUTCOMES))
""",
        b"def maker(entry):\n    def apply(family_size):\n"
        b'        entry["p"] = min(entry["p"] * family_size, 1.0)\n    return apply\n\n\n',
    ),
}

# --- Group 5: the true accusations the round-5 closure lost -----------------------------------
#
# Every block below leaves the family uncorrected and only reads it, so each row must keep the
# accusation the uncorrected baseline carries.
RECOVERED_ROWS: dict[str, tuple[bytes, bytes]] = {
    "helper-bare-iteration-over-the-collection": (
        b"""
    inspect_table(results)
""",
        b"def inspect_table(table):\n    for key in table:\n        print(key.upper())\n\n\n",
    ),
    "helper-star-keys-forwarding": (
        b"""
    scratch = {}
    for name, record in results.items():
        print(inspect_keys(*record, target=scratch))
""",
        b'def inspect_keys(*values, target):\n    target["count"] = len(values)\n'
        b"    return values\n\n\n",
    ),
    "helper-double-star-forwarding": (
        b"""
    scratch = {}
    for name, record in results.items():
        print(inspect_fields(target=scratch, **record))
""",
        b'def inspect_fields(target, **fields):\n    target["count"] = len(fields)\n'
        b'    return fields["p"]\n\n\n',
    ),
    "helper-scalar-subscript-argument": (
        b"""
    for name, record in results.items():
        print(inspect_float(record["p"]))
""",
        b"def inspect_float(value):\n    return value.as_integer_ratio()\n\n\n",
    ),
    "helper-parameter-rebound-to-a-fresh-dict": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b'def inspect_record(entry):\n    entry = {}\n    entry["scratch"] = 1\n'
        b"    return entry\n\n\n",
    ),
    "helper-parameter-rebound-to-a-shallow-copy": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b"def inspect_record(entry):\n    entry = dict(entry)\n"
        b'    entry["scratch"] = entry["p"]\n    return entry\n\n\n',
    ),
    "never-called-nested-store": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b'def inspect_record(entry):\n    def never_called():\n        entry["p"] = 1.0\n'
        b'    return entry["p"]\n\n\n',
    ),
    "project-local-sorted-returning-fresh-records": (
        b"""
    for record in sorted(results.values()):
        record["scratch"] = 1
""",
        b'def sorted(values):\n    return [{"scratch": 0}]\n\n\n',
    ),
}

# --- Group 6: the read-only controls the allowlist exists to keep -----------------------------
READ_ONLY_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "library-calls-over-the-collection": (
        b"""
    logging.info("%s", results)
    print(json.dumps(sorted(results)))
    print(len(pd.DataFrame(results)))
""",
        b"",
        b"import json\nimport logging\n",
    ),
    "read-only-helper-returning-a-new-dict-the-caller-stores-into": (
        b"""
    for name, record in results.items():
        summary = summarize(record)
        summary["scratch"] = 1
        print(summary)
""",
        b'def summarize(entry):\n    return {"p": entry["p"]}\n\n\n',
        b"",
    ),
    "decorated-read-only-helper": (
        b"""
    for name, record in results.items():
        print(labelled(record))
""",
        b"def trace(func):\n    return func\n\n\n@trace\ndef labelled(entry):\n"
        b'    return "{:.6f}".format(entry["p"])\n\n\n',
        b"",
    ),
    "sorted-key-and-map-read-only-callbacks": (
        b"""
    print(len(sorted(results.values(), key=lambda row: row["p"])))
    print(len(list(map(lambda row: row["p"], results.values()))))
""",
        b"",
        b"",
    ),
    "star-entries-read-only-helper": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b'def inspect_record(*entries):\n    return entries[0]["p"]\n\n\n',
        b"",
    ),
    "read-only-helper-beside-an-unrelated-parameter": (
        b"""
    for name, record in results.items():
        print("  {}: {}".format(name, significance_label(record)))
""",
        b"def significance_label(entry):\n"
        b'    return "SIGNIFICANT" if entry["p"] < ALPHA else "not significant"\n\n\n'
        b"def unrelated(significance_label):\n    return significance_label\n\n\n",
        b"",
    ),
    "collected-p-into-a-separate-output-dict": (
        b"""
    output = {}
    for name, record in results.items():
        output[name] = "p={:.6f}".format(record["p"])
    print(len(output))
""",
        b"",
        b"",
    ),
}

# --- Group 7: the measured costs, recorded rather than hidden ---------------------------------
COST_ROWS: dict[str, tuple[bytes, bytes]] = {
    "helper-parameter-rebound-inside-a-branch": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b"def inspect_record(entry):\n    if len(OUTCOMES) > 99:\n        entry = {}\n"
        b'    entry["scratch"] = 1\n    return entry\n\n\n',
    ),
    "overwritten-class-method": (
        b"""
    presenter = Presenter()
    for name, record in results.items():
        print(presenter.show(record))
""",
        b'def harmless(self, entry):\n    return entry["p"]\n\n\nclass Presenter:\n'
        b'    def show(self, entry):\n        entry["p"] = 1.0\n\n    show = harmless\n\n\n',
    ),
    "read-only-helper-calling-keys-on-its-parameter": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b"def inspect_record(entry):\n    return tuple(entry.keys())\n\n\n",
    ),
    "read-only-helper-calling-items-on-its-parameter": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b"def inspect_record(entry):\n    return tuple(entry.items())\n\n\n",
    ),
    "read-only-helper-calling-copy-on-its-parameter": (
        b"""
    for name, record in results.items():
        print(inspect_record(record))
""",
        b"def inspect_record(entry):\n    return entry.copy()\n\n\n",
    ),
}

# --- The reason authority ---------------------------------------------------------------------
#
# The store written through the collection's own name: the identical program, differing only in
# where the store is written.  Every refused row above names it, and its frozen 3.3 reason is the
# reason each of them carries.
THROUGH_NAME_CORRECTION = b"""
    for name in results:
        results[name]["p"] = min(results[name]["p"] * len(OUTCOMES), 1.0)
"""

#: The coverage guard: a complete correction carried out on the threshold rather than on the
#: p-values, with a live read-only library call beside it.  The closure guards coverage
#: classifications too, and this row is what shows guarding them costs nothing.
COVERED_THRESHOLD_LINE = (
    b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA / len(OUTCOMES) '
    b'else "not significant"\n'
)
COVERED_BLOCK = b"""
    print(len(results))
"""


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def _p3_explicit_loop(name: str) -> bytes:
    """P3 with its collection comprehension written as the equivalent explicit loop."""

    return _replace_once(P3.read_bytes(), P3_COMPREHENSION, P3_EXPLICIT_LOOP, name)


def _p3_row(name: str, block: bytes = b"", definition: bytes = b"", imports: bytes = b"") -> bytes:
    """The explicit-loop P3 with one block after the collection and one definition before main."""

    source = _p3_explicit_loop(name)
    if imports:
        source = _replace_once(
            source, P3_IMPORT_ANCHOR, P3_IMPORT_ANCHOR + imports, name + "-imports"
        )
    if definition:
        source = _replace_once(
            source, P3_MAIN_ANCHOR, definition + P3_MAIN_ANCHOR, name + "-definition"
        )
    if block:
        source = _replace_once(source, P3_EXPLICIT_LOOP, P3_EXPLICIT_LOOP + block, name + "-block")
    return source


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    sources: dict[str, tuple[str, bytes]] = {}

    for shape, (block, definition, imports) in UNRESOLVABLE_ROWS.items():
        name = f"correct-record-in-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, block, definition, imports))

    for shape, definition in SHADOWING_ROWS.items():
        name = f"correct-record-in-helper-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, RESCALE_CALL, definition))
    name = "correct-record-in-helper-imported-then-defined"
    sources[name] = (
        P3_KEY,
        _p3_row(name, RESCALE_CALL, RESCALE_DEFINITION, IMPORTED_THEN_DEFINED_IMPORT),
    )

    for shape, (block, definition) in RETURN_FLOW_ROWS.items():
        name = f"correct-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, block, definition))

    for shape, (block, definition) in CLOSURE_ROWS.items():
        name = f"correct-record-in-a-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, block, definition))

    for shape, (block, definition) in RECOVERED_ROWS.items():
        name = f"positive-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, block, definition))

    for shape, (block, definition, imports) in READ_ONLY_ROWS.items():
        name = f"positive-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, block, definition, imports))

    for shape, (block, definition) in COST_ROWS.items():
        name = f"boundary-{shape}"
        sources[name] = (P3_KEY, _p3_row(name, block, definition))

    sources["correct-explicit-loop-record-store-through-name"] = (
        P3_KEY,
        _p3_row("store-through-name", THROUGH_NAME_CORRECTION),
    )
    sources["positive-explicit-loop-uncorrected-family"] = (
        P3_KEY,
        _p3_explicit_loop("uncorrected"),
    )

    name = "positive-covered-family-with-a-library-call"
    sources[name] = (
        P3_KEY,
        _replace_once(
            _p3_row(name, COVERED_BLOCK),
            P3_VERDICT_LINE,
            COVERED_THRESHOLD_LINE,
            name + "-threshold",
        ),
    )

    # The two sealed E17 sources, carried unaltered: both pinned 3.4 movements land on the
    # classification path this closure sits directly on.
    sources["positive-comprehension-e17-p3-unaltered"] = (P3_KEY, P3.read_bytes())
    sources["positive-ap-e17-p6-unaltered"] = (P6_KEY, P6.read_bytes())
    return sources
