"""Deterministic source recipes for the independent MT 3.4 audit-fix oracle.

Every recipe is a single anchored edit of one sealed envelope-17 case source.  The recipes own
source selection and mutation only; the expected rows live in `EXPECTED_ROWS.json` and are
authored from the design and the audit disposition, never from analyzer output.
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
MAIN_ANCHOR = b"def main():\n"
JOIN_ANCHOR = b'", ".join(MUSCULOSKELETAL)'
P3_GENERATOR = b"        for outcome in OUTCOMES\n"
P3_LABELS = b"LABELS = {"

# A flat list literal holding the same six declared outcomes in a different order.  Nothing
# upstream of the order-equality predicate can refuse it: it is a resolvable module sequence of
# the right length whose member set is exactly the contract family.
P3_SHUFFLED = b"""SHUFFLED = [
    "lichen_cover_pct",
    "chla_phaeo_ratio",
    "zinc_mg_kg",
    "lead_mg_kg",
    "sulfur_pct",
    "nitrogen_pct",
]

"""

# The auditor's shape: a project-local definition that binds the name `enumerate` in the module.
SHADOW_AGREEING = b'''def enumerate(sequence, start=0):
    """Number the declared outcomes for the printed report."""
    pairs = []
    index = start
    for item in sequence:
        pairs.append((index, item))
        index = index + 1
    return pairs


'''

# The same binding, where the project-local definition does not agree with the builtin: it drops
# the final declared outcome, so the family the loop actually visits is not the declared family.
SHADOW_DIVERGING = b'''def enumerate(sequence, start=0):
    """Number the declared outcomes, skipping the engagement measure."""
    pairs = []
    index = start
    for item in sequence[:-1]:
        pairs.append((index, item))
        index = index + 1
    return pairs


'''


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def _mutated_selection_sequence(name: str, tail: bytes) -> bytes:
    """P6 with one statement appended to the selection-sequence block."""

    return _replace_once(P6.read_bytes(), MUSCULOSKELETAL_BLOCK, MUSCULOSKELETAL_BLOCK + tail, name)


def _shadowed_enumerate(name: str, definition: bytes) -> bytes:
    return _replace_once(P6.read_bytes(), MAIN_ANCHOR, definition + MAIN_ANCHOR, name)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    alias_positive = _replace_once(
        _mutated_selection_sequence(
            "alias-without-mutation", b"CORRECTED_OUTCOMES = MUSCULOSKELETAL\n"
        ),
        JOIN_ANCHOR,
        b'", ".join(CORRECTED_OUTCOMES)',
        "alias-without-mutation-join",
    )
    shuffled = _replace_once(
        _replace_once(P3.read_bytes(), P3_LABELS, P3_SHUFFLED + P3_LABELS, "shuffled-literal"),
        P3_GENERATOR,
        b"        for outcome in SHUFFLED\n",
        "shuffled-generator",
    )
    return {
        "correct-ap-selection-sequence-direct-extend": (
            P6_KEY,
            _mutated_selection_sequence(
                "direct-extend", b"MUSCULOSKELETAL.extend(OUTCOMES[3:])\n"
            ),
        ),
        "correct-ap-selection-sequence-alias-extend": (
            P6_KEY,
            _mutated_selection_sequence(
                "alias-extend",
                b"CORRECTED_OUTCOMES = MUSCULOSKELETAL\n"
                b"CORRECTED_OUTCOMES.extend(OUTCOMES[3:])\n",
            ),
        ),
        "correct-ap-selection-sequence-alias-augmented-assign": (
            P6_KEY,
            _mutated_selection_sequence(
                "alias-augmented-assign",
                b"CORRECTED_OUTCOMES = MUSCULOSKELETAL\nCORRECTED_OUTCOMES += OUTCOMES[3:]\n",
            ),
        ),
        "correct-ap-selection-sequence-alias-slice-assign": (
            P6_KEY,
            _mutated_selection_sequence(
                "alias-slice-assign",
                b"CORRECTED_OUTCOMES = MUSCULOSKELETAL\nCORRECTED_OUTCOMES[:] = OUTCOMES\n",
            ),
        ),
        "shadowed-enumerate-definition-agreeing": (
            P6_KEY,
            _shadowed_enumerate("shadow-agreeing", SHADOW_AGREEING),
        ),
        "correct-ap-shadowed-enumerate-definition-diverging": (
            P6_KEY,
            _shadowed_enumerate("shadow-diverging", SHADOW_DIVERGING),
        ),
        "correct-comprehension-flat-literal-out-of-contract-order": (P3_KEY, shuffled),
        "positive-ap-unmutated-sequence-genuine-enumerate": (P6_KEY, P6.read_bytes()),
        "positive-ap-selection-sequence-alias-without-mutation": (P6_KEY, alias_positive),
    }
