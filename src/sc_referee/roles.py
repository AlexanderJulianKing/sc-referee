"""`Roles` — the ONLY thing an LLM is trusted to propose. (design doc 2026-07-08, §4.1)

A language model is good at semantic assignment ("which column is the condition?") and bad at,
and dangerous at, authoring executable statistical code. So the model fills `Roles` — column and
level assignments plus its evidence — and deterministic code (`init.synthesize_config`) derives
every formula, coefficient, and contrast from the roles and the DATA. A formula synthesized from
the data cannot contradict the data; an LLM-authored one can, and did (bug 4, 2026-07-08).

Frozen so the three producers (hard-signal / Claude / heuristic) cannot disagree on shape: a
missing or mistyped field is a construction error here, not a KeyError three frames into synthesis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True)
class Roles:
    analysis_type: str                       # one of the schema enum
    condition: Optional[str]                 # the column being contrasted
    replicate_unit: Tuple[str, ...]          # the independent experimental unit (donor/subject/…)
    batch: Tuple[str, ...]                    # declared technical batch column(s)
    analyst_adjusted_for: Optional[Tuple[str, ...]] = None  # analyst fit's column labels; None=uncaptured
    reference: Optional[str] = None          # a LEVEL of `condition` (the control arm), or None
    unit_of_test: Optional[str] = None       # "cell" | "sample" | None — deterministic wins (§4.4)
    type_confidence: str = "low"
    type_evidence: Tuple[str, ...] = ()
    plain_summary: str = ""
    confidence: Mapping[str, str] = field(default_factory=dict)  # {replicate_unit, condition, …}
    unresolved: Tuple[str, ...] = ()         # ROLE NAMES a human must settle before confirming
    # Closed, structure-only batch-component proposals. They carry no row digest or authority;
    # only the wizard projects confirmed answers into FittedDesignDeclaration.batch_modeling.
    batch_modeling: Tuple[Mapping[str, object], ...] = ()
    # Evidence-only seeds for registered CSP cards.  No scientific answer, scope digest,
    # confirmation state, or verdict can be represented here.
    csp_proposals: Tuple[Mapping[str, object], ...] = ()
