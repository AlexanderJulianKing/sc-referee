"""The check registry — the growing checklist.

Each check recomputes rather than opines:
  confounding        exact design-matrix algebra; the power-independent blocker
  experimental_unit  replicate-aware recompute + earned verdict (cell-level reports only)
  multiple_testing   BH recomputed over the analyst's own p-values; needs no data or code
  count_model        NB recompute when a sample-level analysis used a non-count test
  double_dipping     static provenance escalation for inference after clustering
  allele_orientation donor-level OLS sign conformance under a ratified effect-allele contract

Still unbuilt: compositional_method.
"""
from __future__ import annotations

from sc_referee.checks.confounding import ConfoundingCheck
from sc_referee.checks.confounding_strong import ConfoundingStrongCheck
from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck
from sc_referee.checks.confounding_random_intercept_conditional import ConfoundingRandomInterceptConditionalCheck
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.checks.allele_orientation import AlleleOrientationCheck
from sc_referee.checks.count_model import CountModelCheck
from sc_referee.checks.double_dipping import DoubleDippingCheck
from sc_referee.checks.effect_size import EffectSizeCheck
from sc_referee.checks.eqtl_design_support import EqtlDesignSupportCheck
from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
from sc_referee.checks.hic_loop_strength import HiCLoopStrengthCheck
from sc_referee.checks.multiple_testing import MultipleTestingCheck
from sc_referee.checks.pairing import PairingCheck
from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
from sc_referee.audit_dimensions import AUDIT_DIMENSIONS
from sc_referee.citations import CITATIONS
from sc_referee.inference.live import build_engine_verifiers

CHECK_CLASSES = (ConfoundingCheck, ConfoundingStrongCheck, ConfoundingRandomInterceptCheck, ConfoundingRandomInterceptConditionalCheck, ContaminationConfoundCheck, ExperimentalUnitCheck, MultipleTestingCheck, CountModelCheck,
                 DoubleDippingCheck, EffectSizeCheck, PseudobulkIntegrityCheck, PairingCheck,
                 AlleleOrientationCheck, HiCLoopStrengthCheck, EqtlDesignSupportCheck)

# THE EXTENSION POINT. Each entry is a factory `engine -> Check`. To add an analysis type, append
# its verifier factories here; each verifier declares the `analysis_types` it applies to and the
# audit routes by `applies_to`, so a new type needs no change to the audit loop or existing checks.
# (Only recompute-based verifiers consume `engine`; structural/advisory ones ignore it.)
_VERIFIER_FACTORIES = (
    lambda engine: ConfoundingCheck(),
    lambda engine: ConfoundingStrongCheck(),
    lambda engine: ConfoundingRandomInterceptCheck(),
    lambda engine: ConfoundingRandomInterceptConditionalCheck(),
    lambda engine: ContaminationConfoundCheck(),
    lambda engine: ExperimentalUnitCheck(engine=engine),
    lambda engine: MultipleTestingCheck(),
    lambda engine: CountModelCheck(engine=engine),
    lambda engine: DoubleDippingCheck(),   # marker_detection: structural double-dipping detector
    lambda engine: EffectSizeCheck(),      # significance without an effect-size gate (advisory)
    lambda engine: PseudobulkIntegrityCheck(),  # count-model assay contract + aggregation-key integrity
    lambda engine: PairingCheck(),         # omitted pairing / pair-matching structure (diagnostic)
    lambda engine: AlleleOrientationCheck(),  # eQTL effect-allele sign contract + OLS recompute
    lambda engine: HiCLoopStrengthCheck(),  # report-bound exact Hi-C O/E delta conformance
    # eQTL donor/genotype support. Certifies only the structure that makes a donor-level genotype
    # coefficient estimable, and says nothing about the reported effect. Entitled to at most
    # `not_audited`, so it can award a positive certification but can never accuse.
    lambda engine: EqtlDesignSupportCheck(),
)


def build_checks(engine: str = "pydeseq2") -> list:
    """Instantiate the checklist, replacing only the proven double-dipping live surface.

    The inference verifier delegates every unsupported double-dipping program back to the shipped
    implementation, so this is a one-id router rather than two competing findings.
    """
    legacy = [make(engine) for make in _VERIFIER_FACTORIES]
    legacy = [check for check in legacy if not isinstance(check, DoubleDippingCheck)]
    return legacy + build_engine_verifiers()


# Compatibility inventory used by legacy proof metadata and citation/dimension pinning. The live
# audit calls ``build_checks`` and therefore receives the additive engine verifiers; keeping CHECKS
# legacy-exact avoids silently redefining existing proof-report contracts during partial migration.
CHECKS = [make("pydeseq2") for make in _VERIFIER_FACTORIES]

_missing_dimensions = [check.id for check in CHECKS
                       if not tuple(getattr(check, "audit_dimensions", ()))]
_unknown_dimensions = {
    check.id: sorted(set(check.audit_dimensions) - AUDIT_DIMENSIONS)
    for check in CHECKS
    if set(getattr(check, "audit_dimensions", ())) - AUDIT_DIMENSIONS
}
if _missing_dimensions or _unknown_dimensions:
    raise RuntimeError(
        "registered checks must declare a non-empty, code-owned audit_dimensions tuple "
        f"(missing={_missing_dimensions}, unknown={_unknown_dimensions})"
    )

# The anti-hallucination guard fires HERE, at import, not mid-audit. `CITATIONS[CHECK_ID]` is
# looked up when a Finding is constructed, so a check with no citation entry used to pass import,
# pass registration, run a pydeseq2 recompute, and only then raise KeyError — costing the user
# every finding from every check that had already succeeded. (Opus review 2026-07-08.)
_missing = {c.id for c in CHECKS} - set(CITATIONS)
if _missing:
    raise RuntimeError(f"checks with no hard-mapped citation: {sorted(_missing)} — add them to "
                       f"sc_referee.citations.CITATIONS before registering.")


def checks_for(design, bundle) -> list:
    return [c for c in build_checks() if c.applies_to(design, bundle)]
