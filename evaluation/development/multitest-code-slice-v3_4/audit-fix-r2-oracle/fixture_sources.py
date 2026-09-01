"""Deterministic source recipes for the MT 3.4 audit-fix round-2 oracle.

Every recipe is a single anchored edit of one sealed envelope-17 case source.  The recipes own
source selection and mutation only; the expected rows live in `EXPECTED_ROWS.json` and are
authored from the design and the round-2 probe dispositions, never from analyzer output.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E17 = REPO / "evaluation/development/blind-envelope-17-2026-08-30/cases"
P3_KEY = "E17:P3:a2e031f79e31c80fd900"
P6_KEY = "E17:P6:b4e507c4b55954752f14"
P3 = E17 / "a2e031f79e31c80fd900/project/analysis.py"
P6 = E17 / "b4e507c4b55954752f14/project/analysis.py"

# The three-element selection sequence the P6 membership guard reads.
MUSCULOSKELETAL_BLOCK = b"""# The musculoskeletal outcomes the evaluation was commissioned to answer.
MUSCULOSKELETAL = [
    "neck_shoulder_discomfort_0_10",
    "lower_back_discomfort_0_10",
    "sitting_time_min",
]
"""

# P3 anchors: the module-level insertion point, the comprehension statement, and the two
# report lines the positive controls read.
P3_MODULE_ANCHOR = b"LABELS = {"
P3_COMPREHENSION = b"""    results = {
        outcome: compare_settings(roadside[outcome], park[outcome])
        for outcome in OUTCOMES
    }
"""
P3_ALPHA_LINE = (
    b'    print("Two-sample t-test per declared outcome, threshold alpha = {}".format(ALPHA))\n'
)

# One Bonferroni pass over the collected comprehension result.  The two spellings differ only
# in whether the store is written through the collected name or through a second name for it.
BONFERRONI_THROUGH_ALIAS = b"""    adjusted = results
    for name in adjusted:
        adjusted[name]["p"] = min(adjusted[name]["p"] * len(OUTCOMES), 1.0)
"""
BONFERRONI_THROUGH_NAME = b"""    for name in results:
        results[name]["p"] = min(results[name]["p"] * len(OUTCOMES), 1.0)
"""


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def _p3_module_prelude(name: str, block: bytes) -> bytes:
    """P3 with one module-level block inserted above the label table."""

    return _replace_once(P3.read_bytes(), P3_MODULE_ANCHOR, block + P3_MODULE_ANCHOR, name)


def _p6_selection_prelude(name: str, tail: bytes) -> bytes:
    """P6 with one statement appended to the selection-sequence block."""

    return _replace_once(P6.read_bytes(), MUSCULOSKELETAL_BLOCK, MUSCULOSKELETAL_BLOCK + tail, name)


def _p3_after_comprehension(name: str, tail: bytes) -> bytes:
    return _replace_once(P3.read_bytes(), P3_COMPREHENSION, P3_COMPREHENSION + tail, name)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    alias_positive = _replace_once(
        _p3_module_prelude("alias-without-mutation", b"PRIMARY_OUTCOMES = OUTCOMES\n\n"),
        P3_ALPHA_LINE,
        P3_ALPHA_LINE + b'    print("Declared outcomes: {}".format(len(PRIMARY_OUTCOMES)))\n',
        "alias-without-mutation-report",
    )
    return {
        # The round-1 residual: a container display captures the selection sequence, and the
        # mutation is written through the container.  No Store, no augmented assignment, and no
        # method call on a Name moves, so the round-1 census sees nothing.
        "correct-ap-selection-sequence-dict-display-escape": (
            P6_KEY,
            _p6_selection_prelude(
                "dict-display-escape",
                b'PLAN = {"family": MUSCULOSKELETAL}\nPLAN["family"].extend(OUTCOMES[3:])\n',
            ),
        ),
        "correct-ap-selection-sequence-list-display-escape": (
            P6_KEY,
            _p6_selection_prelude(
                "list-display-escape",
                b"PLAN = [MUSCULOSKELETAL]\nPLAN[0].extend(OUTCOMES[3:])\n",
            ),
        ),
        # The comprehension lane's own false accusations.  In each one the runtime family is cut
        # to a single outcome before the comprehension runs, so no correction is owed at all.
        "correct-comprehension-dict-display-escape-shrunk-to-one": (
            P3_KEY,
            _p3_module_prelude(
                "dict-display-escape-shrunk",
                b"# The survey plan was cut to the single primary outcome before the run.\n"
                b'PLAN = {"family": OUTCOMES}\n'
                b'PLAN["family"][1:] = []\n\n',
            ),
        ),
        "correct-comprehension-attribute-escape-shrunk-to-one": (
            P3_KEY,
            _p3_module_prelude(
                "attribute-escape-shrunk",
                b"class _Plan:\n    pass\n\n\nPLAN = _Plan()\nPLAN.family = OUTCOMES\n"
                b"PLAN.family[1:] = []\n\n",
            ),
        ),
        "correct-comprehension-walrus-escape-shrunk-to-one": (
            P3_KEY,
            _p3_module_prelude(
                "walrus-escape-shrunk",
                b"_PLAN = (PRIMARY := OUTCOMES)\nPRIMARY[1:] = []\n\n",
            ),
        ),
        # The reported probe: a plain Name alias of the generator sequence, receiver-mutated.
        "comprehension-sequence-alias-remove": (
            P3_KEY,
            _p3_module_prelude(
                "sequence-alias-remove",
                b'SCREENED = OUTCOMES\nSCREENED.remove("zinc_mg_kg")\n\n',
            ),
        ),
        # The round-1 escape half, reached from the comprehension lane: a subscript store binds
        # the sequence into a container that is then mutated.
        "comprehension-subscript-escape-remove": (
            P3_KEY,
            _p3_module_prelude(
                "subscript-escape-remove",
                b"REGISTRY = {}\n"
                b'REGISTRY["family"] = OUTCOMES\n'
                b'REGISTRY["family"].remove("zinc_mg_kg")\n\n',
            ),
        ),
        # Section 4.2's collected-name clause, evaded by a second name for the collection.
        "comprehension-collected-target-alias-store": (
            P3_KEY,
            _p3_after_comprehension("collected-target-alias-store", BONFERRONI_THROUGH_ALIAS),
        ),
        # Non-vacuity controls.
        "positive-comprehension-e17-p3-unaltered": (P3_KEY, P3.read_bytes()),
        "positive-comprehension-sequence-alias-without-mutation": (P3_KEY, alias_positive),
        "positive-comprehension-collected-target-store-through-name": (
            P3_KEY,
            _p3_after_comprehension("collected-target-store-through-name", BONFERRONI_THROUGH_NAME),
        ),
        "positive-ap-e17-p6-unaltered": (P6_KEY, P6.read_bytes()),
    }
