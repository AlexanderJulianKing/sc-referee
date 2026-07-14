"""Two coupling fixes surfaced during the dogfood:

1. `confidence_high` gated ALL blocking on the *replicate* confidence — including `confounding`,
   which reasons about condition/batch. Each check should gate on the confidence of the role IT
   uses: confounding on `condition`, experimental_unit on `replicate_unit`.
2. `experimental_unit` required the ADAPTER to have name-detected a replicate column
   (`bundle.replicate_var`), so a confirmed design that NAMES the replicate could still be skipped
   if the adapter's heuristic missed it. The human-confirmed design is authoritative: the replicate
   is recorded iff `design.replicate_unit` names column(s) present in `.obs`.
"""
from sc_referee import statuses as S
from tests.factories import alias_obs, make_design, paired_count_bundle


def test_confounding_blocker_is_gated_by_condition_confidence_not_replicate():
    # LOW replicate confidence must NOT downgrade a confounding blocker — confounding never uses the replicate
    from sc_referee.checks.confounding import evaluate_confounding

    hi = evaluate_confounding(alias_obs(), make_design(sample_unit=("donor_id",),
                              confidence_high=False, condition_confidence_high=True))
    assert hi.status == S.BLOCKER

    # LOW condition confidence DOES downgrade — that is the role confounding depends on
    lo = evaluate_confounding(alias_obs(), make_design(sample_unit=("donor_id",),
                              confidence_high=True, condition_confidence_high=False))
    assert lo.status == S.NEEDS_EVIDENCE


def test_experimental_unit_trusts_the_confirmed_replicate_even_if_the_adapter_missed_it():
    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck

    b = paired_count_bundle(n_donors=4)
    b.replicate_var = None                       # the adapter's name-heuristic FAILED to detect it
    d = make_design(unit_of_test="cell", replicate_unit=("donor_id",))   # ...but the design NAMES it, and it's in .obs

    chk = ExperimentalUnitCheck()
    assert chk.applies_to(d, b) is True          # the replicate IS recorded (design + .obs), so we run
    assert chk.cannot_evaluate(d, b) is None


def test_experimental_unit_abstains_when_the_named_replicate_is_absent_from_obs():
    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck

    b = paired_count_bundle(n_donors=4)
    b.replicate_var = None
    d = make_design(unit_of_test="cell", replicate_unit=("nonexistent_col",))
    assert ExperimentalUnitCheck().applies_to(d, b) is False
    assert ExperimentalUnitCheck().cannot_evaluate(d, b)     # says so, not a silent skip
