from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import (
    AUTHORIZED_CONSUMER,
    CONTRACT_TYPE,
    REQUIRED_FIELDS,
    validate_values,
)


def test_two_question_manifest_requires_the_meant_obligation():
    assert CONTRACT_TYPE == "between_group_adjustment_obligation/v1"
    assert REQUIRED_FIELDS == (
        "between_group_policy", "may_rely_on_re_exogeneity",
    )
    assert AUTHORIZED_CONSUMER == "confounding_random_intercept_conditional"
    assert validate_values({
        "between_group_policy": "remove_arbitrary",
        "may_rely_on_re_exogeneity": False,
    }) == ()
    assert validate_values({
        "between_group_policy": "remove_arbitrary",
        "may_rely_on_re_exogeneity": True,
    }) == ("re_exogeneity_is_permitted",)


def test_contract_manifest_contains_no_formula_or_verdict_vocabulary():
    from sc_referee.csp_contracts import get_manifest

    manifest = get_manifest(CONTRACT_TYPE)
    rendered = repr(manifest).lower()
    assert "formula" not in rendered
    assert "verdict" not in rendered


def test_manifest_states_exact_fixed_effect_equivalence_boundary():
    from sc_referee.csp_contracts import get_manifest

    rendered = repr(get_manifest(CONTRACT_TYPE)).lower()
    assert "exact fixed-effect-equivalent projection" in rendered
    assert "random intercept never" in rendered
    assert "tolerance-level" in rendered
