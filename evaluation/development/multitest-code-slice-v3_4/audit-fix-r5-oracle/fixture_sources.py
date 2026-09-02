"""Deterministic source recipes for the MT 3.4 audit-fix round-5 oracle.

Every recipe is an anchored edit of one sealed envelope-17 case source, exactly as rounds 1 to 4
are.  The recipes own source selection and mutation only; the expected rows live in
`EXPECTED_ROWS.json` and are authored from the design, the frozen through-name sibling, and the
round-5 probe dispositions, never from analyzer output.

Round 5 works on the same classification side as rounds 3 and 4, so the sealed P3 comprehension is
again rewritten as the explicit loop the custodian's reproduction used.  That rewrite is one
anchored edit applied to every explicit-loop row, so the rows differ from one another only in the
helper the correction store travels into.

The correction blocks below are the whole point of the round.  Each one is a complete, correct
Bonferroni pass over the six declared outcomes: every declared outcome's p is multiplied by the
declared family size and capped before any verdict is read.  They differ only in how the record
being stored into reached the helper that stores it.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E17 = REPO / "evaluation/development/blind-envelope-17-2026-08-30/cases"
P3_KEY = "E17:P3:a2e031f79e31c80fd900"
P6_KEY = "E17:P6:b4e507c4b55954752f14"
P3 = E17 / "a2e031f79e31c80fd900/project/analysis.py"
P6 = E17 / "b4e507c4b55954752f14/project/analysis.py"

# The sealed P3 collection statement, and the explicit loop that builds the identical record
# collection one member at a time.  This is the round-3 and round-4 reproduction shape, carried
# unchanged so the round-5 rows differ from the round-4 rows only in the helper.
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
P3_ENTRY_ANCHOR = b'if __name__ == "__main__":\n'
P3_IMPORT_ANCHOR = b"from scipy import stats\n"
P3_ALPHA_LINE = (
    b'    print("Two-sample t-test per declared outcome, threshold alpha = {}".format(ALPHA))\n'
)
P3_VERDICT_LINE = b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA else "not significant"\n'

# The call site every record-in-helper row shares.  The record is bound by the round-4 iteration
# form the closure already enumerates; what round 5 decides is what the call does with it.
RECORD_HELPER_CALL = b"""
    for name, record in results.items():
        rescale(record, len(OUTCOMES))
"""

# --- Group 1: the record handed to a project-local helper that stores through its parameter ---
#
# Each helper writes the same complete Bonferroni pass.  The parameter is named `entry`, not
# `record`, so the round-4 module-wide name match does not reach it: this is exactly the row the
# round-4 oracle pinned as its named open residual.
HELPER_DEFINITIONS: dict[str, bytes] = {
    "distinct-parameter-name": b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    entry["p"] = min(entry["p"] * family_size, 1.0)


''',
    "storing-through-a-local-alias": b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    row = entry
    row["p"] = min(row["p"] * family_size, 1.0)


''',
    "storing-via-a-nested-helper": b'''def apply_factor(row, factor):
    """Multiply one collected p by a factor, capped at one."""
    row["p"] = min(row["p"] * factor, 1.0)


def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    apply_factor(entry, family_size)


''',
    "storing-conditionally": b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    if family_size > 1:
        entry["p"] = min(entry["p"] * family_size, 1.0)


''',
    "mutating-via-update": b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    entry.update({"p": min(entry["p"] * family_size, 1.0)})


''',
}

# --- Group 2: the binding at the call site, rather than the store inside the helper ----------
KEYWORD_HELPER_CALL = b"""
    for name, record in results.items():
        rescale(entry=record, family_size=len(OUTCOMES))
"""

FORWARDING_HELPER_CALL = b"""
    for name, record in results.items():
        forward(record, len(OUTCOMES))
"""
KEYWORD_FORWARDING_HELPER_CALL = b"""
    for name, record in results.items():
        forward(entry=record, family_size=len(OUTCOMES))
"""
STAR_ARGS_FORWARDER = b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    entry["p"] = min(entry["p"] * family_size, 1.0)


def forward(*args):
    """Forward the record and the declared family size to the correction helper."""
    rescale(*args)


'''
DOUBLE_STAR_FORWARDER = b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    entry["p"] = min(entry["p"] * family_size, 1.0)


def forward(**fields):
    """Forward the record and the declared family size to the correction helper."""
    rescale(**fields)


'''

# --- Group 3: the callable is not a `def` ---------------------------------------------------
LAMBDA_DEFINITION = b"""rescale = lambda entry, family_size: entry.update(
    {"p": min(entry["p"] * family_size, 1.0)})


"""
MAP_LAMBDA_CORRECTION = b"""
    _ = list(map(lambda entry: entry.update(
        {"p": min(entry["p"] * len(OUTCOMES), 1.0)}), results.values()))
"""

# --- Group 4: the callable is a method of a project-local class ------------------------------
STATIC_METHOD_CORRECTION = b"""
    for name, record in results.items():
        Bonferroni.rescale(record, len(OUTCOMES))
"""
STATIC_METHOD_DEFINITION = b'''class Bonferroni:
    """The declared-family correction, as a static method."""

    @staticmethod
    def rescale(entry, family_size):
        entry["p"] = min(entry["p"] * family_size, 1.0)


'''
INSTANCE_METHOD_CORRECTION = b"""
    adjuster = Bonferroni(len(OUTCOMES))
    for name, record in results.items():
        adjuster.rescale(record)
"""
INSTANCE_METHOD_DEFINITION = b'''class Bonferroni:
    """The declared-family correction, as an instance method."""

    def __init__(self, family_size):
        self.family_size = family_size

    def rescale(self, entry):
        entry["p"] = min(entry["p"] * self.family_size, 1.0)


'''

# --- Group 5: the helper receives the collection, not one record -----------------------------
COLLECTION_HELPER_CALL = b"""
    rescale_all(results, len(OUTCOMES))
"""
COLLECTION_HELPER_DEFINITION = b'''def rescale_all(table, family_size):
    """Multiply every collected p by the declared family size, capped at one."""
    for key in table:
        table[key]["p"] = min(table[key]["p"] * family_size, 1.0)


'''
VALUES_VIEW_HELPER_CALL = b"""
    rescale_all(results.values(), len(OUTCOMES))
"""
VALUES_VIEW_HELPER_DEFINITION = b'''def rescale_all(entries, family_size):
    """Multiply every collected p by the declared family size, capped at one."""
    for entry in entries:
        entry["p"] = min(entry["p"] * family_size, 1.0)


'''

# --- The reason authority ---------------------------------------------------------------------
#
# The store written through the collection's own name.  This is the frozen 3.3 reason authority
# for every refused row above: the identical program, differing only in where the store is
# written.  It carries the bytes the round-3 and round-4 oracles pin for the same purpose.
THROUGH_NAME_CORRECTION = b"""
    for name in results:
        results[name]["p"] = min(results[name]["p"] * len(OUTCOMES), 1.0)
"""

# --- The named open residual -------------------------------------------------------------------
#
# The identical correction, in a helper this recognizer never sees.  The recognizer reads one
# source file, so a callee defined in a sibling project module resolves to nothing, and the
# non-capture discipline that keeps `len(OUTCOMES)` admissible keeps this call admissible too.
SIBLING_MODULE_IMPORT = b"from scipy import stats\n\nfrom corrections import rescale\n"

# --- The read-only controls ---------------------------------------------------------------------
#
# Each block is inserted before the untouched declared-outcome presentation loop, so the family
# reconstruction is exactly the one the uncorrected baseline row carries and the row keeps its
# candidate.  The helper names avoid `verdict` and `result`, which P3's own presentation loop
# binds: a name this module binds twice is not a resolvable callee, and a control that passed
# for that reason would prove nothing about read-only helpers.
READ_ONLY_BLOCKS: dict[str, tuple[bytes, bytes]] = {
    "read-only-helper-on-uncorrected-family": (
        b"""    for name, record in results.items():
        print("  collected {}: {}".format(name, significance_label(record)))
""",
        b'''def significance_label(entry):
    """Report the verdict for one collected p at the declared threshold."""
    return "SIGNIFICANT" if entry["p"] < ALPHA else "not significant"


''',
    ),
    "read-only-helper-on-the-whole-collection": (
        b"""    print(collection_summary(results))
""",
        b'''def collection_summary(table):
    """One line naming how many declared outcomes were collected."""
    return "  collected {} of {} declared outcomes".format(len(table), len(OUTCOMES))


''',
    ),
    "builtin-calls-over-record-derived-names": (
        b"""    for name, record in sorted(results.items()):
        print(record)
        print("  " + ", ".join(OUTCOMES) + " of {}".format(len(OUTCOMES)))
""",
        b"",
    ),
}

# The measured conservative boundary: a helper that only READS its parameter, but reads it with a
# method call.  The frozen B1/B4 record-mutation census counts every method call whose receiver is
# a name as an in-place mutation, because a method may mutate its receiver and this recognizer
# never executes project code.  Round 5 reuses that census unchanged, so this row is refused even
# though the helper stores nothing.  The family here is genuinely uncorrected, so the row records
# a true accusation traded for the closure rather than a false one closed by it.
METHOD_READING_HELPER = (
    b"""    for name, record in results.items():
        print("  collected {}: {}".format(name, formatted_p(record)))
""",
    b'''def formatted_p(entry):
    """Read one collected p out of a record."""
    return "{:.6f}".format(entry.get("p"))


''',
)

# The coverage control: a complete correction carried out on the threshold rather than on the
# p-values, with a live read-only helper call alongside it.  The closure guards coverage
# classifications too, and this row is what shows guarding them costs nothing.  The helper it
# carries is the whole-collection one, which never names `ALPHA`: a read-only helper that
# compared against the threshold itself would leave the threshold unresolved and the row would
# abstain for a reason that has nothing to do with this closure.
COVERED_THRESHOLD_LINE = (
    b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA / len(OUTCOMES) '
    b'else "not significant"\n'
)


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def _p3_explicit_loop(name: str) -> bytes:
    """P3 with its collection comprehension written as the equivalent explicit loop."""

    return _replace_once(P3.read_bytes(), P3_COMPREHENSION, P3_EXPLICIT_LOOP, name)


def _p3_corrected(name: str, correction: bytes) -> bytes:
    """The explicit-loop P3 with one Bonferroni pass placed after the collection statement."""

    return _replace_once(
        _p3_explicit_loop(name), P3_EXPLICIT_LOOP, P3_EXPLICIT_LOOP + correction, name
    )


def _p3_read_only(name: str, block: bytes) -> bytes:
    """The explicit-loop P3 with one read-only block before the presentation loop."""

    return _replace_once(
        _p3_explicit_loop(name), P3_ALPHA_LINE, P3_ALPHA_LINE + b"\n" + block, name
    )


def _with_definition(source: bytes, definition: bytes, name: str, *, anchor: bytes) -> bytes:
    """Place a module-level definition immediately before one anchor line."""

    if not definition:
        return source
    return _replace_once(source, anchor, definition + anchor, name + "-definition")


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    sources: dict[str, tuple[str, bytes]] = {}

    # Group 1: the record reaches a project-local helper that stores through its parameter.
    for shape, definition in HELPER_DEFINITIONS.items():
        name = f"correct-record-in-helper-{shape}"
        sources[name] = (
            P3_KEY,
            _with_definition(
                _p3_corrected(name, RECORD_HELPER_CALL),
                definition,
                name,
                anchor=P3_MAIN_ANCHOR,
            ),
        )

    # The same helper, defined after the call that uses it.
    name = "correct-record-in-helper-defined-after-its-use"
    sources[name] = (
        P3_KEY,
        _with_definition(
            _p3_corrected(name, RECORD_HELPER_CALL),
            HELPER_DEFINITIONS["distinct-parameter-name"],
            name,
            anchor=P3_ENTRY_ANCHOR,
        ),
    )

    # Group 2: the binding at the call site.
    name = "correct-record-in-helper-keyword-argument"
    sources[name] = (
        P3_KEY,
        _with_definition(
            _p3_corrected(name, KEYWORD_HELPER_CALL),
            HELPER_DEFINITIONS["distinct-parameter-name"],
            name,
            anchor=P3_MAIN_ANCHOR,
        ),
    )
    for name, call, forwarder in (
        (
            "correct-record-in-helper-through-star-args-forwarding",
            FORWARDING_HELPER_CALL,
            STAR_ARGS_FORWARDER,
        ),
        (
            "correct-record-in-helper-through-double-star-forwarding",
            KEYWORD_FORWARDING_HELPER_CALL,
            DOUBLE_STAR_FORWARDER,
        ),
    ):
        sources[name] = (
            P3_KEY,
            _with_definition(_p3_corrected(name, call), forwarder, name, anchor=P3_MAIN_ANCHOR),
        )

    # Group 3: the callable is a lambda.
    name = "correct-record-in-lambda-bound-to-a-name"
    sources[name] = (
        P3_KEY,
        _with_definition(
            _p3_corrected(name, RECORD_HELPER_CALL),
            LAMBDA_DEFINITION,
            name,
            anchor=P3_MAIN_ANCHOR,
        ),
    )
    name = "correct-record-in-lambda-applied-through-map"
    sources[name] = (P3_KEY, _p3_corrected(name, MAP_LAMBDA_CORRECTION))

    # Group 4: the callable is a method of a project-local class.
    for name, correction, definition in (
        (
            "correct-record-in-static-method-of-a-project-local-class",
            STATIC_METHOD_CORRECTION,
            STATIC_METHOD_DEFINITION,
        ),
        (
            "correct-record-in-instance-method-of-a-project-local-class",
            INSTANCE_METHOD_CORRECTION,
            INSTANCE_METHOD_DEFINITION,
        ),
    ):
        sources[name] = (
            P3_KEY,
            _with_definition(
                _p3_corrected(name, correction), definition, name, anchor=P3_MAIN_ANCHOR
            ),
        )

    # Group 5: the helper receives the collection or one of its views.
    for name, correction, definition in (
        (
            "correct-collection-in-helper-iterating-internally",
            COLLECTION_HELPER_CALL,
            COLLECTION_HELPER_DEFINITION,
        ),
        (
            "correct-values-view-in-helper-iterating-internally",
            VALUES_VIEW_HELPER_CALL,
            VALUES_VIEW_HELPER_DEFINITION,
        ),
    ):
        sources[name] = (
            P3_KEY,
            _with_definition(
                _p3_corrected(name, correction), definition, name, anchor=P3_MAIN_ANCHOR
            ),
        )

    # The reason authority.
    sources["correct-explicit-loop-record-store-through-name"] = (
        P3_KEY,
        _p3_corrected("store-through-name", THROUGH_NAME_CORRECTION),
    )

    # The named open residual: the helper is defined in a module this recognizer never reads.
    name = "correct-record-in-helper-imported-from-a-sibling-module"
    sources[name] = (
        P3_KEY,
        _replace_once(
            _p3_corrected(name, RECORD_HELPER_CALL),
            P3_IMPORT_ANCHOR,
            SIBLING_MODULE_IMPORT,
            name + "-import",
        ),
    )

    # The measured conservative boundary.
    name = "boundary-read-only-helper-calling-a-method-on-its-parameter"
    block, definition = METHOD_READING_HELPER
    sources[name] = (
        P3_KEY,
        _with_definition(_p3_read_only(name, block), definition, name, anchor=P3_MAIN_ANCHOR),
    )

    # The read-only controls, each on the genuinely uncorrected family.
    for shape, (block, definition) in READ_ONLY_BLOCKS.items():
        name = f"positive-{shape}"
        sources[name] = (
            P3_KEY,
            _with_definition(_p3_read_only(name, block), definition, name, anchor=P3_MAIN_ANCHOR),
        )

    # The uncorrected baseline the read-only controls are measured against.
    sources["positive-explicit-loop-uncorrected-family"] = (
        P3_KEY,
        _p3_explicit_loop("uncorrected"),
    )

    # The coverage guard: complete correction on the threshold, with a live read-only helper call.
    name = "positive-covered-family-with-a-read-only-helper"
    block, definition = READ_ONLY_BLOCKS["read-only-helper-on-the-whole-collection"]
    sources[name] = (
        P3_KEY,
        _replace_once(
            _with_definition(_p3_read_only(name, block), definition, name, anchor=P3_MAIN_ANCHOR),
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
