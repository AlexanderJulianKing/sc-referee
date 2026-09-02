"""Deterministic source recipes for the MT 3.4 audit-fix round-3 oracle.

Every recipe is an anchored edit of one sealed envelope-17 case source.  The recipes own source
selection and mutation only; the expected rows live in `EXPECTED_ROWS.json` and are authored from
the design, the frozen through-name sibling, and the round-3 probe dispositions, never from
analyzer output.

Round 3 works on the *classification* side, so the sealed P3 comprehension is first rewritten as
the explicit loop the custodian's reproduction used.  That rewrite is itself one anchored edit and
is applied to every explicit-loop row, so the rows differ from one another only in how the
correction store reaches the record collection.
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
# collection one member at a time.  This is the custodian's reproduction shape.
P3_COMPREHENSION = b"""    results = {
        outcome: compare_settings(roadside[outcome], park[outcome])
        for outcome in OUTCOMES
    }
"""
P3_EXPLICIT_LOOP = b"""    results = {}
    for outcome in OUTCOMES:
        results[outcome] = compare_settings(roadside[outcome], park[outcome])
"""
# The same collection opened with one descriptive key already in it.  The extra key changes
# nothing about how the family is built or corrected.
P3_EMPTY_SEED = b"    results = {}\n"
P3_SEEDED = b'    results = {"_method": "two-sample t-test per declared outcome"}\n'

# The module-level insertion point and the report line the read-only control reads.
P3_MODULE_ANCHOR = b"LABELS = {"
P3_ALPHA_LINE = (
    b'    print("Two-sample t-test per declared outcome, threshold alpha = {}".format(ALPHA))\n'
)
P3_VERDICT_LINE = b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA else "not significant"\n'
P3_RESULT_LINE = b"        result = results[outcome]\n"
P3_MAIN_ANCHOR = b"def main():\n"
P3_ENTRY_POINT = b"""

if __name__ == "__main__":
    main()
"""

# One complete, correct Bonferroni pass over the collected record table.  The spellings differ
# only in which name the store travels through; every one of them multiplies every declared
# outcome's p by the declared family size before any verdict is read.
BONFERRONI_THROUGH_NAME = b"""
    for name in results:
        results[name]["p"] = min(results[name]["p"] * len(OUTCOMES), 1.0)
"""
BONFERRONI_THROUGH_ALIAS = b"""
    adjusted = results
    for name in adjusted:
        adjusted[name]["p"] = min(adjusted[name]["p"] * len(OUTCOMES), 1.0)
"""
BONFERRONI_THROUGH_SECOND_ALIAS = b"""
    adjusted = results
    corrected = adjusted
    for name in corrected:
        corrected[name]["p"] = min(corrected[name]["p"] * len(OUTCOMES), 1.0)
"""
BONFERRONI_THROUGH_CONTAINER = b"""
    REGISTRY = {"family": results}
    for name in REGISTRY["family"]:
        REGISTRY["family"][name]["p"] = min(
            REGISTRY["family"][name]["p"] * len(OUTCOMES), 1.0)
"""
BONFERRONI_THROUGH_ATTRIBUTE = b"""
    plan = _Plan()
    plan.family = results
    for name in plan.family:
        plan.family[name]["p"] = min(plan.family[name]["p"] * len(OUTCOMES), 1.0)
"""
PLAN_CLASS = b"""class _Plan:
    pass


"""
# The same correction written inside a helper the collection is passed to as an argument.
BONFERRONI_HELPER_CALL = b"""
    bonferroni(results, len(OUTCOMES))
"""
BONFERRONI_HELPER = b'''def bonferroni(table, family_size):
    """Multiply every collected p by the declared family size, capped at one."""
    for name in table:
        table[name]["p"] = min(table[name]["p"] * family_size, 1.0)


'''


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def _p3_explicit_loop(name: str) -> bytes:
    """P3 with its collection comprehension written as the equivalent explicit loop."""

    return _replace_once(P3.read_bytes(), P3_COMPREHENSION, P3_EXPLICIT_LOOP, name)


def _p3_corrected(name: str, correction: bytes) -> bytes:
    """The explicit-loop P3 with one complete Bonferroni pass after the collection statement."""

    return _replace_once(
        _p3_explicit_loop(name), P3_EXPLICIT_LOOP, P3_EXPLICIT_LOOP + correction, name
    )


def _p3_module_prelude(source: bytes, name: str, block: bytes) -> bytes:
    return _replace_once(source, P3_MODULE_ANCHOR, block + P3_MODULE_ANCHOR, name)


def _p3_module_scope(name: str, correction: bytes) -> bytes:
    """The same corrected program with every statement at module scope.

    The rewrite is mechanical: the `main` header and its trailing entry-point guard are removed
    and the function body is dedented by exactly four columns.  The collection, its alias, and
    the correction store therefore all live in the module body, which is the shape a closure
    restricted to function scopes would miss.
    """

    source = _p3_corrected(name, correction)
    head, _, tail = source.partition(P3_MAIN_ANCHOR)
    if not tail:
        raise ValueError(f"{name}: main anchor is absent")
    body = _replace_once(tail, P3_ENTRY_POINT, b"\n", f"{name}-entry-point")
    lines: list[bytes] = []
    for line in body.split(b"\n"):
        if line.startswith(b"    "):
            lines.append(line[4:])
        elif not line.strip():
            lines.append(b"")
        else:
            raise ValueError(f"{name}: main body line is not indented: {line!r}")
    return head + b"\n".join(lines)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    read_only_alias = _replace_once(
        _replace_once(
            _p3_explicit_loop("alias-read-only"),
            P3_EXPLICIT_LOOP,
            P3_EXPLICIT_LOOP + b"\n    adjusted = results\n",
            "alias-read-only-binding",
        ),
        P3_RESULT_LINE,
        b"        result = adjusted[outcome]\n",
        "alias-read-only-read",
    )
    reported_alias = _replace_once(
        _replace_once(
            _p3_explicit_loop("alias-reported"),
            P3_EXPLICIT_LOOP,
            P3_EXPLICIT_LOOP + b"\n    adjusted = results\n",
            "alias-reported-binding",
        ),
        P3_ALPHA_LINE,
        P3_ALPHA_LINE + b'    print("Outcomes collected: {}".format(len(adjusted)))\n',
        "alias-reported-report",
    )
    covered_alias = _replace_once(
        _replace_once(
            _p3_explicit_loop("covered-alias"),
            P3_EXPLICIT_LOOP,
            P3_EXPLICIT_LOOP + b"\n    adjusted = results\n",
            "covered-alias-binding",
        ),
        P3_VERDICT_LINE,
        b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA / len(OUTCOMES) '
        b'else "not significant"\n',
        "covered-alias-threshold",
    )
    seeded_alias = _replace_once(
        _p3_corrected("seeded-alias", BONFERRONI_THROUGH_ALIAS),
        P3_EMPTY_SEED,
        P3_SEEDED,
        "seeded-alias-display",
    )
    seeded_through_name = _replace_once(
        _p3_corrected("seeded-through-name", BONFERRONI_THROUGH_NAME),
        P3_EMPTY_SEED,
        P3_SEEDED,
        "seeded-through-name-display",
    )
    dead_store = _replace_once(
        _p3_explicit_loop("alias-dead-store"),
        P3_ENTRY_POINT,
        BONFERRONI_THROUGH_ALIAS + P3_ENTRY_POINT,
        "alias-dead-store-tail",
    )
    dead_store_through_name = _replace_once(
        _p3_explicit_loop("name-dead-store"),
        P3_ENTRY_POINT,
        BONFERRONI_THROUGH_NAME + P3_ENTRY_POINT,
        "name-dead-store-tail",
    )
    helper_argument = _replace_once(
        _p3_corrected("helper-argument", BONFERRONI_HELPER_CALL),
        P3_MAIN_ANCHOR,
        BONFERRONI_HELPER + P3_MAIN_ANCHOR,
        "helper-argument-definition",
    )
    attribute_escape = _replace_once(
        _p3_corrected("attribute-escape", BONFERRONI_THROUGH_ATTRIBUTE),
        P3_MAIN_ANCHOR,
        PLAN_CLASS + P3_MAIN_ANCHOR,
        "attribute-escape-class",
    )
    return {
        # The custodian's confirmed route, and the identical program spelled through the
        # collection name.  Both are complete, correct six-outcome Bonferroni corrections.
        "correct-explicit-loop-collection-alias-store": (
            P3_KEY,
            _p3_corrected("alias-store", BONFERRONI_THROUGH_ALIAS),
        ),
        "correct-explicit-loop-collection-store-through-name": (
            P3_KEY,
            _p3_corrected("store-through-name", BONFERRONI_THROUGH_NAME),
        ),
        # The adversarial variants: the alias bound before the collection loop runs, an alias of
        # an alias, the same program at module scope, and the two display-escape spellings.
        "correct-explicit-loop-collection-alias-before-loop": (
            P3_KEY,
            _replace_once(
                _p3_corrected("alias-before-loop", BONFERRONI_THROUGH_ALIAS),
                b'    results = {}\n    for outcome in OUTCOMES:\n        results[outcome] = '
                b"compare_settings(roadside[outcome], park[outcome])\n\n    adjusted = results\n",
                b'    results = {}\n    adjusted = results\n    for outcome in OUTCOMES:\n'
                b"        results[outcome] = compare_settings(roadside[outcome], park[outcome])\n\n",
                "alias-before-loop-hoist",
            ),
        ),
        "correct-explicit-loop-collection-alias-of-alias": (
            P3_KEY,
            _p3_corrected("alias-of-alias", BONFERRONI_THROUGH_SECOND_ALIAS),
        ),
        "correct-explicit-loop-collection-alias-module-scope": (
            P3_KEY,
            _p3_module_scope("alias-module-scope", BONFERRONI_THROUGH_ALIAS),
        ),
        "correct-explicit-loop-collection-container-escape": (
            P3_KEY,
            _p3_corrected("container-escape", BONFERRONI_THROUGH_CONTAINER),
        ),
        "correct-explicit-loop-collection-attribute-escape": (P3_KEY, attribute_escape),
        "correct-explicit-loop-seeded-collection-alias-store": (P3_KEY, seeded_alias),
        "correct-explicit-loop-seeded-collection-store-through-name": (
            P3_KEY,
            seeded_through_name,
        ),
        # A store through an alias that cannot have reached any conclusion, and the same dead
        # store written through the collection name.  The pair pins the two spellings together.
        "explicit-loop-collection-alias-dead-store": (P3_KEY, dead_store),
        "explicit-loop-collection-dead-store-through-name": (P3_KEY, dead_store_through_name),
        # The helper-argument shape, carried to pin what the frozen pipeline does with it.
        "correct-explicit-loop-collection-helper-argument": (P3_KEY, helper_argument),
        # Non-vacuity controls.
        "positive-explicit-loop-collection-alias-read-only": (P3_KEY, read_only_alias),
        "positive-explicit-loop-collection-alias-reported-not-stored": (P3_KEY, reported_alias),
        "positive-explicit-loop-covered-family-with-read-only-alias": (P3_KEY, covered_alias),
        "positive-explicit-loop-uncorrected-family": (P3_KEY, _p3_explicit_loop("uncorrected")),
        "positive-explicit-loop-uncorrected-family-unrelated-alias": (
            P3_KEY,
            _p3_module_prelude(
                _p3_explicit_loop("uncorrected-unrelated-alias"),
                "uncorrected-unrelated-alias",
                b"PRIMARY_OUTCOMES = OUTCOMES\n\n",
            ),
        ),
        "positive-comprehension-e17-p3-unaltered": (P3_KEY, P3.read_bytes()),
        "positive-ap-e17-p6-unaltered": (P6_KEY, P6.read_bytes()),
    }
