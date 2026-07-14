"""The single source of truth for Finding statuses.

Conservative by construction: `blocker` fires only when the recompute/algebra
unambiguously earns it; everything uncertain is advisory.
"""
from __future__ import annotations

BLOCKER = "blocker"
MAJOR = "major"
NEEDS_EVIDENCE = "needs_evidence"
# A measured, reportable fact that is NOT a defect — e.g. `confounding` finds the design
# estimable but near-collinear (VIF ≥ 10): an efficiency cost, not a confound. Never fails CI.
INFORMATIONAL = "informational"
NOT_AUDITED = "not_audited"
PASS = "pass"

STATUSES = (BLOCKER, MAJOR, NEEDS_EVIDENCE, INFORMATIONAL, NOT_AUDITED, PASS)

# Severity ordering (higher = more attention) — for sorting a report and picking the
# worst finding. NOT the CI conclusion (see FAIL_ON_DEFAULT).
SEVERITY = {
    BLOCKER: 5,
    MAJOR: 4,
    NEEDS_EVIDENCE: 3,
    NOT_AUDITED: 2,
    INFORMATIONAL: 1,
    PASS: 0,
}

# Statuses that fail CI by default. `not_audited`/`needs_evidence` are posted as
# neutral annotations, never a silent green.
FAIL_ON_DEFAULT = (BLOCKER,)


# Canonical report-ledger axes. These classify a Finding for presentation only; the shipped
# status vocabulary above remains the sole input to severity, CI, and audit-completeness logic.
APPLIES = "applies"
NOT_APPLICABLE = "not_applicable"
UNKNOWN = "unknown"
APPLICABILITIES = (APPLIES, NOT_APPLICABLE, UNKNOWN)

CONFORMANT = "conformant"
VIOLATION = "violation"
CONCERN = "concern"
UNRESOLVED = "unresolved"
JUDGMENTS = (CONFORMANT, VIOLATION, CONCERN, UNRESOLVED)

COMPLETE = "complete"
PARTIAL = "partial"
NOT_RUN = "not_run"
COVERAGES = (COMPLETE, PARTIAL, NOT_RUN)

EXACT = "exact"
RECOMPUTED = "recomputed"
STRUCTURAL = "structural"
ADVISORY = "advisory"
PROOF_GRADES = (EXACT, RECOMPUTED, STRUCTURAL, ADVISORY)

CLEAR = "clear"
FLAGGED = "flagged"
NOT_CHECKED = "not_checked"
N_A = "n_a"
HUMAN_STATES = (CLEAR, FLAGGED, NOT_CHECKED, N_A)


def human_state(finding) -> str:
    """Derive the report label without participating in verdict gating.

    A supported concern always wins over incomplete coverage. Judgmentless NEEDS_EVIDENCE is a
    compatibility abstention, while complete INFORMATIONAL findings are descriptive non-defects.
    """
    applicability = getattr(finding, "applicability", APPLIES)
    judgment = getattr(finding, "judgment", None)
    coverage = getattr(finding, "coverage", COMPLETE)

    if applicability == NOT_APPLICABLE:
        return N_A
    if judgment in (VIOLATION, CONCERN):
        return FLAGGED
    # Adverse statuses remain adverse even if a contradictory coverage annotation is present.
    if getattr(finding, "status", None) in (BLOCKER, MAJOR):
        return FLAGGED
    if applicability == UNKNOWN or coverage in (PARTIAL, NOT_RUN):
        return NOT_CHECKED
    if judgment == UNRESOLVED:
        return NOT_CHECKED
    if applicability == APPLIES and judgment == CONFORMANT and coverage == COMPLETE:
        return CLEAR

    # Safe compatibility projection for shipped/default-axis findings. Unknown statuses fail closed.
    return {
        PASS: CLEAR,
        NOT_AUDITED: NOT_CHECKED,
        NEEDS_EVIDENCE: NOT_CHECKED,
        MAJOR: FLAGGED,
        BLOCKER: FLAGGED,
        INFORMATIONAL: CLEAR,
    }.get(getattr(finding, "status", None), FLAGGED)
