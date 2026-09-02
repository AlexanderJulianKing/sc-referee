"""Deterministic source recipes for the MT 3.4 audit-fix round-4 oracle.

Every recipe is an anchored edit of one sealed envelope-17 case source, exactly as rounds 1 to 3
are.  The recipes own source selection and mutation only; the expected rows live in
`EXPECTED_ROWS.json` and are authored from the design, the frozen through-name sibling, and the
round-4 probe dispositions, never from analyzer output.

Round 4 works on the same classification side as round 3, so the sealed P3 comprehension is again
rewritten as the explicit loop the custodian's reproduction used.  That rewrite is one anchored
edit applied to every explicit-loop row, so the rows differ from one another only in the binding
the correction store travels through.

The correction blocks below are the whole point of the round.  Each one is a complete, correct
Bonferroni pass over the six declared outcomes: every declared outcome's p is multiplied by the
declared family size and capped before any verdict is read.  They differ only in how the record
being stored into was named.
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
# collection one member at a time.  This is the round-3 reproduction shape, carried unchanged.
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
P3_ALPHA_LINE = (
    b'    print("Two-sample t-test per declared outcome, threshold alpha = {}".format(ALPHA))\n'
)
P3_VERDICT_LINE = b'        verdict = "SIGNIFICANT" if result["p"] < ALPHA else "not significant"\n'

# --- Group 1: the correction store reaches a record through an iteration target ---------
#
# `for name, record in results.items()` is the shape the round-3 audit confirmed as a false
# accusation that round 3's closure does not cover.  A loop target is not an alias edge, so the
# record mutation was invisible to it.  The rest of the group is the same binding written through
# every other view, wrapper, and unpack that hands out the same record objects.
ITERATION_CORRECTIONS: dict[str, bytes] = {
    "items-unpack": b"""
    for name, record in results.items():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "values-loop": b"""
    for record in results.values():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "iter-values": b"""
    for record in iter(results.values()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "enumerate-values": b"""
    for index, record in enumerate(results.values()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "enumerate-items-nested-unpack": b"""
    for index, (name, record) in enumerate(results.items()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "zip-values": b"""
    for record, label in zip(results.values(), OUTCOMES):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "sorted-items": b"""
    for name, record in sorted(results.items()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "sorted-values-keyed": b"""
    for record in sorted(results.values(), key=lambda item: item["t"]):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "list-values": b"""
    for record in list(results.values()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "reversed-list-values": b"""
    for record in reversed(list(results.values())):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "tuple-values": b"""
    for record in tuple(results.values()):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "dict-copy-items": b"""
    for name, record in dict(results).items():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "comprehension-target": b"""
    _ = [record.update({"p": min(record["p"] * len(OUTCOMES), 1.0)})
         for record in results.values()]
""",
}

# --- Group 2: the correction store reaches a record through a subscript or a lookup ------
SUBSCRIPT_CORRECTIONS: dict[str, bytes] = {
    "subscript-bound": b"""
    for name in OUTCOMES:
        record = results[name]
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "get-bound": b"""
    for name in OUTCOMES:
        record = results.get(name)
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "setdefault-bound": b"""
    for name in OUTCOMES:
        record = results.setdefault(name, {"p": 1.0})
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "list-values-index": b"""
    for index in range(len(OUTCOMES)):
        record = list(results.values())[index]
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
}

# One record reached through `next(iter(...))`.  This is a store into the family that corrects a
# single member, so it is not a complete correction and the row is not a correct analysis.  It is
# carried because it is the only spelling that binds a record with no loop at all.
SINGLE_RECORD_CORRECTION = b"""
    first = next(iter(results.values()))
    first["p"] = min(first["p"] * len(OUTCOMES), 1.0)
"""

# --- Group 3: the walrus spellings of groups 1 and 2 -------------------------------------
WALRUS_CORRECTIONS: dict[str, bytes] = {
    "walrus-get-bound": b"""
    for name in OUTCOMES:
        if (record := results.get(name)) is not None:
            record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "walrus-container-loop": b"""
    for record in (family := list(results.values())):
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
}

# --- Group 4: chains -- a binding derived from another derived binding -------------------
CHAINED_CORRECTIONS: dict[str, bytes] = {
    "alias-items-unpack": b"""
    adjusted = results
    for name, record in adjusted.items():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "container-name-then-loop": b"""
    family = list(results.values())
    for record in family:
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "record-rebound-to-a-third-name": b"""
    for name, record in results.items():
        target = record
        target["p"] = min(target["p"] * len(OUTCOMES), 1.0)
""",
    "nested-loop-inside-items-unpack": b"""
    for name, record in results.items():
        for field in ("p",):
            record[field] = min(record[field] * len(OUTCOMES), 1.0)
""",
}

# --- Group 5: the build agent's own adversarial inventions -------------------------------
INVENTED_CORRECTIONS: dict[str, bytes] = {
    "collection-copy-method-items": b"""
    copied = results.copy()
    for name, record in copied.items():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "collection-dict-unpack-display-items": b"""
    copied = {**results}
    for name, record in copied.items():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "generator-expression-consumed-later": b"""
    pending = (entry for entry in results.values())
    for record in pending:
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
""",
    "record-update-method": b"""
    for record in results.values():
        record.update({"p": min(record["p"] * len(OUTCOMES), 1.0)})
""",
    "record-dunder-setitem": b"""
    for record in results.values():
        record.__setitem__("p", min(record["p"] * len(OUTCOMES), 1.0))
""",
    "record-subscript-augmented-assign": b"""
    for record in results.values():
        record["p"] *= len(OUTCOMES)
        record["p"] = min(record["p"], 1.0)
""",
    "record-escapes-into-a-container-display": b"""
    for name, record in results.items():
        REGISTRY = {"latest": record}
        REGISTRY["latest"]["p"] = min(REGISTRY["latest"]["p"] * len(OUTCOMES), 1.0)
""",
}

# --- The reason authority, and the two helper dispositions --------------------------------
#
# The store written through the collection's own name.  This is the frozen 3.3 reason authority
# for every refused row above: the identical program, differing only in the name the store
# travels through.  It carries the same bytes the round-3 oracle pins for the same purpose.
THROUGH_NAME_CORRECTION = b"""
    for name in results:
        results[name]["p"] = min(results[name]["p"] * len(OUTCOMES), 1.0)
"""
# `X.keys()` hands out keys, and the store a key reaches is written through the collection's own
# name.  This row verifies that: the frozen pipeline already refuses it, so there is no false
# accusation here and nothing for the key half of the closure to add.
KEYS_LOOP_CORRECTION = b"""
    for name in results.keys():
        results[name]["p"] = min(results[name]["p"] * len(OUTCOMES), 1.0)
"""

# The same correction carried out inside a helper the RECORD is passed to.  Argument passing is a
# non-capture under the frozen discipline, so nothing binds the helper's parameter to the record.
# Whether the row refuses turns on whether the parameter happens to reuse the caller's name, and
# both spellings are carried so that dependence is pinned rather than discovered later.
RECORD_HELPER_CALL = b"""
    for name, record in results.items():
        rescale(record, len(OUTCOMES))
"""
RECORD_HELPER_SHARED_NAME = b'''def rescale(record, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    record["p"] = min(record["p"] * family_size, 1.0)


'''
RECORD_HELPER_DISTINCT_NAME = b'''def rescale(entry, family_size):
    """Multiply one collected p by the declared family size, capped at one."""
    entry["p"] = min(entry["p"] * family_size, 1.0)


'''

# --- The read-only controls -----------------------------------------------------------------
#
# Each block is inserted before the untouched declared-outcome presentation loop, so the family
# reconstruction is exactly the one the uncorrected baseline row carries and the row keeps its
# candidate.  Every one of them binds a record through a form the closure enumerates and then
# only reads it.  A closure that refused binding rather than storing would lose all six.
READ_ONLY_SUMMARIES: dict[str, bytes] = {
    "items-loop-summary": b"""    for name, record in results.items():
        print("  collected {} raw p = {:.6f}".format(name, record["p"]))
""",
    "values-loop-summary": b"""    for record in results.values():
        print("  collected raw p = {:.6f}".format(record["p"]))
""",
    "enumerate-values-loop-summary": b"""    for position, record in enumerate(results.values()):
        print("  collected {} of {}: raw p = {:.6f}".format(
            position + 1, len(OUTCOMES), record["p"]))
""",
    "items-loop-key-method-call": b"""    for name, record in results.items():
        print("  " + name.replace("_", " ") + " raw p = {:.6f}".format(record["p"]))
""",
    "items-loop-record-verdict": b"""    for name, record in results.items():
        flag = "SIGNIFICANT" if record["p"] < ALPHA else "not significant"
        print("  collected {}: {}".format(name, flag))
""",
    "list-values-loop-summary": b"""    family = list(results.values())
    for record in family:
        print("  collected raw p = {:.6f}".format(record["p"]))
""",
}

# The coverage control: a complete correction carried out on the threshold rather than on the
# p-values, with a live read-only record iteration alongside it.  The closure guards coverage
# classifications too, and this row is what shows guarding them costs nothing.
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
    """The explicit-loop P3 with one read-only record iteration before the presentation loop."""

    return _replace_once(
        _p3_explicit_loop(name), P3_ALPHA_LINE, P3_ALPHA_LINE + b"\n" + block, name
    )


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    sources: dict[str, tuple[str, bytes]] = {}

    for shape, correction in ITERATION_CORRECTIONS.items():
        sources[f"correct-iteration-{shape}-record-store"] = (
            P3_KEY,
            _p3_corrected(f"iteration-{shape}", correction),
        )
    for shape, correction in SUBSCRIPT_CORRECTIONS.items():
        sources[f"correct-subscript-{shape}-record-store"] = (
            P3_KEY,
            _p3_corrected(f"subscript-{shape}", correction),
        )
    for shape, correction in WALRUS_CORRECTIONS.items():
        sources[f"correct-{shape}-record-store"] = (P3_KEY, _p3_corrected(shape, correction))
    for shape, correction in CHAINED_CORRECTIONS.items():
        sources[f"correct-chained-{shape}-record-store"] = (
            P3_KEY,
            _p3_corrected(f"chained-{shape}", correction),
        )
    for shape, correction in INVENTED_CORRECTIONS.items():
        sources[f"correct-invented-{shape}-record-store"] = (
            P3_KEY,
            _p3_corrected(f"invented-{shape}", correction),
        )

    sources["partial-next-iter-values-single-record-store"] = (
        P3_KEY,
        _p3_corrected("next-iter-single-record", SINGLE_RECORD_CORRECTION),
    )

    # The reason authority and the keys-view verification row.
    sources["correct-explicit-loop-record-store-through-name"] = (
        P3_KEY,
        _p3_corrected("store-through-name", THROUGH_NAME_CORRECTION),
    )
    sources["correct-keys-view-store-through-name"] = (
        P3_KEY,
        _p3_corrected("keys-view-through-name", KEYS_LOOP_CORRECTION),
    )

    # The two record-in-helper spellings.
    for suffix, helper in (
        ("shared-parameter-name", RECORD_HELPER_SHARED_NAME),
        ("distinct-parameter-name", RECORD_HELPER_DISTINCT_NAME),
    ):
        sources[f"correct-record-in-helper-{suffix}"] = (
            P3_KEY,
            _replace_once(
                _p3_corrected(f"record-in-helper-{suffix}", RECORD_HELPER_CALL),
                P3_MAIN_ANCHOR,
                helper + P3_MAIN_ANCHOR,
                f"record-in-helper-{suffix}-definition",
            ),
        )

    # The read-only controls, each on the genuinely uncorrected family.
    for shape, block in READ_ONLY_SUMMARIES.items():
        sources[f"positive-read-only-{shape}"] = (
            P3_KEY,
            _p3_read_only(f"read-only-{shape}", block),
        )

    # The uncorrected baseline the read-only controls are measured against.
    sources["positive-explicit-loop-uncorrected-family"] = (
        P3_KEY,
        _p3_explicit_loop("uncorrected"),
    )

    # The coverage guard: complete correction on the threshold, with a live read-only record
    # iteration bound through the same enumerated form.
    sources["positive-covered-family-with-read-only-record-iteration"] = (
        P3_KEY,
        _replace_once(
            _p3_read_only("covered-read-only", READ_ONLY_SUMMARIES["items-loop-summary"]),
            P3_VERDICT_LINE,
            COVERED_THRESHOLD_LINE,
            "covered-read-only-threshold",
        ),
    )

    # The two sealed E17 sources, carried unaltered: both pinned 3.4 movements land on the
    # classification path this closure sits directly on.
    sources["positive-comprehension-e17-p3-unaltered"] = (P3_KEY, P3.read_bytes())
    sources["positive-ap-e17-p6-unaltered"] = (P6_KEY, P6.read_bytes())
    return sources
