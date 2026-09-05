"""Deterministic source recipes for the MT 3.4 audit-fix round-7 oracle.

Every recipe is an anchored edit of one sealed envelope-17 case source, exactly as rounds 1 to 6
are.  The recipes own source selection and mutation only; the expected rows live in
`EXPECTED_ROWS.json` and are authored from the design, the frozen through-name sibling, and the
round-7 probe dispositions, never from analyzer output.

Round 7 works on the same classification side as rounds 3 to 6, so the sealed P3 comprehension is
again rewritten as the explicit loop the audit's reproduction used.  That rewrite is one anchored
edit applied to every row, and each row then differs from the others only in the block placed
immediately after the collection statement, in the definitions placed before `def main():`, and in
the imports placed after `from scipy import stats`.  That is the exact construction the round-6
audit ledger specifies, so the rows here are the same programs the custodian ran through the real
contract and audit pipeline.

Three kinds of row live side by side and must not be confused.

* A `correct-` row is a complete, correct Bonferroni pass over the six declared outcomes: every
  declared outcome's p is multiplied by the declared family size and capped before any verdict is
  read.  These may never be classified `candidate`.
* A `positive-` row leaves the family uncorrected and only reads it.  These must keep their
  accusation, and each one is a true accusation the round-6 closure lost or could have lost.
* A `boundary-` row also leaves the family uncorrected and only reads it, and is nevertheless
  refused.  Each is a cost this round pays and pins by name rather than hides, and each is
  inherited from an earlier round's rule rather than introduced here.
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

#: The per-record Bonferroni body the helper rows share, written through a parameter named `entry`
#: so no module-wide name match can reach it.
CORRECTION_BODY = b'    entry["p"] = min(entry["p"] * len(OUTCOMES), 1.0)\n'
RESCALE_DEFINITION = b"def rescale(entry):\n" + CORRECTION_BODY + b"\n\n"
#: The store the value-flow rows write through a container element.
SETITEM = b'operator.setitem(target, "p", min(target["p"] * len(OUTCOMES), 1.0))'

# --- Group 1: rule A(1), a record inserted into a container -----------------------------------
#
# `append`, `extend`, and a subscript store all put the collection's own record objects somewhere
# else without copying them, so a store written through an element of that container is a store
# into the family.  Round 6 read the insertion as read-only and dropped the record's role.
VALUE_FLOW_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "held-append-then-setitem": (
        b"""
    held = []
    for name, record in results.items():
        held.append(record)
    for target in held:
        """
        + SETITEM
        + b"\n",
        b"",
        b"import operator\n",
    ),
    "held-extend-then-setitem": (
        b"""
    held = []
    held.extend(results.values())
    for target in held:
        """
        + SETITEM
        + b"\n",
        b"",
        b"import operator\n",
    ),
    "held-container-subscript-store": (
        b"""
    held = []
    held.extend(results.values())
    for index in range(len(held)):
        held[index]["p"] = min(held[index]["p"] * len(OUTCOMES), 1.0)
""",
        b"",
        b"",
    ),
    "a-set-display-then-iterated": (
        b"""
    for name, record in results.items():
        for target in {record}:
            """
        + SETITEM
        + b"\n",
        b"",
        b"import operator\n",
    ),
    "a-dict-display-values-view": (
        b"""
    for name, record in results.items():
        holder = {"row": record}
        for target in holder.values():
            """
        + SETITEM
        + b"\n",
        b"",
        b"import operator\n",
    ),
    "a-registry-dict-insertion": (
        b"""
    registry = {}
    for name, record in results.items():
        registry[name] = record
    for key in registry:
        registry[key]["p"] = min(registry[key]["p"] * len(OUTCOMES), 1.0)
""",
        b"",
        b"",
    ),
}

# --- Group 2: rule A(2), the lazy displays a helper can hand back -----------------------------
LAZY_DISPLAY_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "a-returned-generator-expression": (
        b"""
    for name, record in results.items():
        for target in stream(record):
            """
        + SETITEM
        + b"\n",
        b"def stream(entry):\n    return (entry for _ in range(1))\n\n\n",
        b"import operator\n",
    ),
    "a-returned-lambda": (
        b"""
    for name, record in results.items():
        target = getter(record)()
        """
        + SETITEM
        + b"\n",
        b"def getter(entry):\n    return lambda: entry\n\n\n",
        b"import operator\n",
    ),
    "a-lambda-in-a-dict-literal": (
        b"""
    for name, record in results.items():
        table = {"fn": rescale, "row": record}
        table["fn"](table["row"])
""",
        RESCALE_DEFINITION,
        b"",
    ),
    "a-sequence-parameter-sorted": (
        b"""
    ordered = ordering(list(results.values()))
    ordered[0]["p"] = min(ordered[0]["p"] * len(OUTCOMES), 1.0)
    ordered[1]["p"] = min(ordered[1]["p"] * len(OUTCOMES), 1.0)
    ordered[2]["p"] = min(ordered[2]["p"] * len(OUTCOMES), 1.0)
    ordered[3]["p"] = min(ordered[3]["p"] * len(OUTCOMES), 1.0)
    ordered[4]["p"] = min(ordered[4]["p"] * len(OUTCOMES), 1.0)
    ordered[5]["p"] = min(ordered[5]["p"] * len(OUTCOMES), 1.0)
""",
        b"def ordering(rows):\n    return sorted(rows, key=len)\n\n\n",
        b"",
    ),
}

# --- Group 3a: rule B, the callable standing in a callable position ---------------------------
#
# Every one of these hands a callback-bearing call a callable that stores through the record it is
# given, and every one is decided by the callable classification: `transform`, `map`, `sorted`, and
# the `map` builtin all reach it.  Round 6 asked whether the callable was known to store and
# admitted everything it could not read.
CALLABLE_POSITION_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "transform-through-a-storing-wrapper": (
        b"""
    pd.Series(list(results.values())).transform(wrapper)
""",
        b'def direct(entry):\n    operator.setitem(entry, "p", min(entry["p"] * len(OUTCOMES), 1.0))'
        b"\n\n\ndef wrapper(entry):\n    direct(entry)\n\n\n",
        b"import operator\n",
    ),
    "series-map-through-an-attribute-callable": (
        b"""
    holder = Holder()
    holder.fn = rescale
    pd.Series(list(results.values())).map(holder.fn)
""",
        b"class Holder:\n    pass\n\n\n" + RESCALE_DEFINITION,
        b"",
    ),
    "sorted-key-through-a-dict-get-callable": (
        b"""
    print(sorted(results.values(), key=ADJUSTERS.get("bonferroni")))
""",
        RESCALE_DEFINITION + b'ADJUSTERS = {"bonferroni": rescale}\n\n\n',
        b"",
    ),
    "map-through-an-identity-chain": (
        b"""
    print(list(map(pass_two(rescale), results.values())))
""",
        RESCALE_DEFINITION + b"def pass_one(func):\n    return func\n\n\ndef pass_two(func):\n"
        b"    return pass_one(func)\n\n\n",
        b"",
    ),
}

# --- Group 3b: the receiver a callback-bearing call writes through ----------------------------
#
# `apply` is on the never-allowlisted callee set, so the callable beside it is never consulted.
# What round 6 missed on these rows is the other half: a callback-bearing call writes through its
# RECEIVER, and the receiver of `pd.Series(list(results.values())).apply(...)` is the collection's
# own records.  Round 6 reached the receiver's roots only when it already knew the argument carried
# a storing callable, which is exactly the thing it could not decide.
CALLBACK_RECEIVER_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "apply-through-a-storing-wrapper": (
        b"""
    pd.Series(list(results.values())).apply(wrapper)
""",
        b'def direct(entry):\n    operator.setitem(entry, "p", min(entry["p"] * len(OUTCOMES), 1.0))'
        b"\n\n\ndef wrapper(entry):\n    direct(entry)\n\n\n",
        b"import operator\n",
    ),
    "apply-through-an-attribute-callable": (
        b"""
    holder = Holder()
    holder.fn = rescale
    pd.Series(list(results.values())).apply(holder.fn)
""",
        b"class Holder:\n    pass\n\n\n" + RESCALE_DEFINITION,
        b"",
    ),
    "apply-through-a-dict-get-callable": (
        b"""
    pd.Series(list(results.values())).apply(ADJUSTERS.get("bonferroni"))
""",
        RESCALE_DEFINITION + b'ADJUSTERS = {"bonferroni": rescale}\n\n\n',
        b"",
    ),
    "apply-through-an-identity-chain": (
        b"""
    pd.Series(list(results.values())).apply(pass_two(rescale))
""",
        RESCALE_DEFINITION + b"def pass_one(func):\n    return func\n\n\ndef pass_two(func):\n"
        b"    return pass_one(func)\n\n\n",
        b"",
    ),
    "apply-through-a-comprehension-callable": (
        b"""
    adjusters = [
        lambda entry, n=n: operator.setitem(entry, "p", min(entry["p"] * n, 1.0))
        for n in [len(OUTCOMES)]
    ]
    pd.Series(list(results.values())).apply(adjusters[0])
""",
        b"",
        b"import operator\n",
    ),
    "apply-through-functools-partial": (
        b"""
    pd.Series(list(results.values())).apply(functools.partial(rescale_n, n=len(OUTCOMES)))
""",
        b'def rescale_n(entry, n):\n    entry["p"] = min(entry["p"] * n, 1.0)\n\n\n',
        b"import functools\n",
    ),
}

# --- Group 4: rule C, the allowlist keyed on import-resolved targets --------------------------
IMPORT_RESOLUTION_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "a-json-namespace-masquerade": (
        b"""
    for name, record in results.items():
        json.dumps(record, len(OUTCOMES))
""",
        b"class Mutator:\n    @staticmethod\n    def dumps(entry, family_size):\n"
        b'        entry["p"] = min(entry["p"] * family_size, 1.0)\n\n\njson = Mutator\n\n\n',
        b"",
    ),
    "an-aliased-storing-library-function": (
        b"""
    for name, record in results.items():
        put(record, "p", min(record["p"] * len(OUTCOMES), 1.0))
""",
        b"",
        b"from operator import setitem as put\n",
    ),
    "a-writer-rebound-to-a-project-class": (
        b"""
    writer = LocalWriter()
    for name, record in results.items():
        writer.writerow(record)
""",
        b"class LocalWriter:\n    def writerow(self, entry):\n"
        b'        entry["p"] = min(entry["p"] * len(OUTCOMES), 1.0)\n\n\n',
        b"import csv\n",
    ),
}

# --- Group 5: the correct rows an earlier gate refuses before this closure is reached ----------
#
# Each is a complete correct Bonferroni pass, so none of them may be accused; each lands on a
# different frozen reason than the through-name sibling because the pipeline declines earlier.
UPSTREAM_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "a-masquerade-beside-a-real-import": (
        b"""
    for name, record in results.items():
        json.dumps(record, len(OUTCOMES))
""",
        b"class Mutator:\n    @staticmethod\n    def dumps(entry, family_size):\n"
        b'        entry["p"] = min(entry["p"] * family_size, 1.0)\n\n\njson = Mutator\n\n\n',
        b"import json\n",
    ),
    "a-yield-helper": (
        b"""
    for name, record in results.items():
        for target in stream(record):
            """
        + SETITEM
        + b"\n",
        b"def stream(entry):\n    yield entry\n\n\n",
        b"import operator\n",
    ),
    "map-over-a-held-container": (
        b"""
    held = []
    held.extend(results.values())
    list(map(rescale, held))
""",
        RESCALE_DEFINITION,
        b"",
    ),
}

# --- Group 6: the Direction-2 true accusations round 7 recovers --------------------------------
RECOVERED_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "import-alias-json": (
        b"""
    print(payload.dumps(results))
""",
        b"",
        b"import json as payload\n",
    ),
    "from-import-alias-dumps": (
        b"""
    print(serialize(results))
""",
        b"",
        b"from json import dumps as serialize\n",
    ),
    "json-dumps-through-a-plain-import": (
        b"""
    print(json.dumps(results))
""",
        b"",
        b"import json\n",
    ),
    "copy-deepcopy-of-the-collection": (
        b"""
    snapshot = copy.deepcopy(results)
    print(len(snapshot))
""",
        b"",
        b"import copy\n",
    ),
    "copy-copy-and-math-log": (
        b"""
    snapshot = copy.copy(results)
    print(len(snapshot), math.log(len(results)))
""",
        b"",
        b"import copy\nimport math\n",
    ),
    "pprint-of-the-collection": (
        b"""
    pprint.pprint(results)
""",
        b"",
        b"import pprint\n",
    ),
    "csv-dictwriter-writerow": (
        b"""
    with open("summary.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["park_mean", "roadside_mean", "t", "p"])
        writer.writeheader()
        for name, record in results.items():
            writer.writerow(record)
""",
        b"",
        b"import csv\n",
    ),
    "seen-index-and-count": (
        b"""
    seen = []
    for name, record in results.items():
        seen.append(record)
        print(seen.index(record), seen.count(record))
""",
        b"",
        b"",
    ),
    "sorted-key-bound-method": (
        b"""
    print(sorted(results, key=results.get))
""",
        b"",
        b"",
    ),
    "transform-with-a-read-only-project-helper": (
        b"""
    print(pd.Series(list(results.values())).transform(reader).sum())
""",
        b'def reader(entry):\n    return entry["p"]\n\n\n',
        b"",
    ),
    "sorted-key-read-only-lambda": (
        b"""
    print(sorted(results.values(), key=lambda row: row["p"]))
""",
        b"",
        b"",
    ),
    "functools-wraps-read-only-helper": (
        b"""
    for name, record in results.items():
        print(show(record))
""",
        b"def logged(func):\n    @functools.wraps(func)\n    def wrapper(entry):\n"
        b"        return func(entry)\n    return wrapper\n\n\n@logged\ndef show(entry):\n"
        b'    return entry["p"]\n\n\n',
        b"import functools\n",
    ),
    "summarize-keys-fresh": (
        b"""
    summary = summarize(results)
    summary["scratch"] = 1
    print(summary)
""",
        b'def summarize(table):\n    return {"names": list(table)}\n\n\n',
        b"",
    ),
    "summarize-sorted-keys-fresh": (
        b"""
    summary = summarize(results)
    summary["scratch"] = 1
    print(summary)
""",
        b'def summarize(table):\n    return {"names": sorted(table)}\n\n\n',
        b"",
    ),
    "class-scope-lookup": (
        b"""
    report = Report()
    for name, record in results.items():
        print(report.show(record))
""",
        b'def inspect(entry):\n    return entry["p"]\n\n\nclass Report:\n    def inspect(self):\n'
        b'        self["p"] = 1.0\n\n    def show(self, entry):\n'
        b"        return inspect(entry)\n\n\n",
        b"",
    ),
}

# --- Group 7: the costs, each inherited from an earlier round's rule and pinned by name --------
COST_ROWS: dict[str, tuple[bytes, bytes, bytes]] = {
    "unawaited-async-call": (
        b"""
    for name, record in results.items():
        inspect(record)
""",
        b'async def inspect(entry):\n    entry["scratch"] = 1\n\n\n',
        b"",
    ),
    "lru-cache-decorated-read-only-helper": (
        b"""
    for name, record in results.items():
        print(show(record))
""",
        b'@functools.lru_cache(maxsize=None)\ndef show(entry):\n    return entry["p"]\n\n\n',
        b"import functools\n",
    ),
    "record-inserted-by-subscript-into-a-second-mapping": (
        b"""
    registry = {}
    for name, record in results.items():
        registry[name] = record
    print(len(registry))
""",
        b"",
        b"",
    ),
    "read-only-helper-calling-values-on-its-parameter": (
        b"""
    print(collect(results))
""",
        b'def collect(table):\n    return [row["p"] for row in table.values()]\n\n\n',
        b"",
    ),
    "read-only-pandas-apply": (
        b"""
    print(pd.Series(list(results.values())).apply(reader).sum())
""",
        b'def reader(entry):\n    return entry["p"]\n\n\n',
        b"",
    ),
}

# --- The reason authority ----------------------------------------------------------------------
#
# The store written through the collection's own name: the identical program, differing only in
# where the store is written.  Every closed row above names it, and its frozen 3.3 reason is the
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


_GROUPS: tuple[tuple[str, dict[str, tuple[bytes, bytes, bytes]]], ...] = (
    ("correct-record-in-", VALUE_FLOW_ROWS),
    ("correct-record-through-", LAZY_DISPLAY_ROWS),
    ("correct-record-in-", CALLABLE_POSITION_ROWS),
    ("correct-record-in-", CALLBACK_RECEIVER_ROWS),
    ("correct-record-in-", IMPORT_RESOLUTION_ROWS),
    ("correct-record-in-", UPSTREAM_ROWS),
    ("positive-", RECOVERED_ROWS),
    ("boundary-", COST_ROWS),
)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    sources: dict[str, tuple[str, bytes]] = {}

    for prefix, group in _GROUPS:
        for shape, (block, definition, imports) in group.items():
            name = f"{prefix}{shape}"
            sources[name] = (P3_KEY, _p3_row(name, block, definition, imports))

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
