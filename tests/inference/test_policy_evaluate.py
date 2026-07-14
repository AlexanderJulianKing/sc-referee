from __future__ import annotations

import pytest


def _premise(name):
    from sc_referee.inference.policy.schema import RelationPremise

    return RelationPremise(name, ())


def _rule(rule_id, outcome, relation, cap="pass"):
    from sc_referee.inference.policy.schema import ProofRule

    return ProofRule(rule_id, (_premise(relation),), (), outcome, cap, ())


def _policy(*rules):
    from sc_referee.inference.policy.schema import ValidityPolicy

    return ValidityPolicy("test.policy", (), tuple(rules), frozenset({"claims", "effects"}))


def _snapshot(**overrides):
    from sc_referee.inference.policy.evaluate import PolicySnapshot

    base = dict(
        inventory_complete=True,
        possible_producers=frozenset({"p1", "p2"}),
        covered_producers=frozenset({"p1", "p2"}),
        unknown_producers=frozenset(),
        coverage=frozenset({"claims", "effects"}),
        relations={},
        facts={},
    )
    base.update(overrides)
    return PolicySnapshot(**base)


def test_policy_schema_is_declarative_and_rejects_callables_recursively():
    from sc_referee.inference.policy.schema import (
        FactRef, RelationPremise, ValidityPolicy, assert_no_callables, canonical_policy_json,
    )

    policy = ValidityPolicy("pure", (RelationPremise("Exact", (FactRef("X", {"claim": "$claim"}),)),),
                            (), frozenset())
    assert '"id":"pure"' in canonical_policy_json(policy)
    assert_no_callables(policy)

    impure = ValidityPolicy("impure", (RelationPremise("Bad", (lambda: True,)),), (), frozenset())
    with pytest.raises(TypeError, match="callable"):
        assert_no_callables(impure)


def test_policy_schema_freezes_nested_selector_and_provider_input_mappings():
    from sc_referee.inference.policy.schema import FactRef, ProviderInvocation

    fact = FactRef("X", {"claim": "$claim"})
    invocation = ProviderInvocation("p", "1", "sha256:p", {"x": fact}, "Exact")
    with pytest.raises(TypeError):
        fact.selector["claim"] = "changed"
    with pytest.raises(TypeError):
        invocation.inputs["x"] = "changed"


def test_both_clean_and_violation_rules_proved_abstains_inconsistent():
    from sc_referee.inference.policy.evaluate import evaluate

    policy = _policy(
        _rule("clean", "CLEAN_PROOF", "CleanRelation"),
        _rule("violation", "VIOLATION_WITNESS", "ViolationRelation", "blocker"),
    )
    snapshot = _snapshot(relations={"CleanRelation": "PROVED", "ViolationRelation": "PROVED"})
    judgment = evaluate(policy, "claim:1", snapshot)
    assert judgment.outcome == "ABSTAIN"
    assert "INCONSISTENT_EVIDENCE" in judgment.obligations


def test_explicit_violation_rule_is_required_for_violation_witness():
    from sc_referee.inference.policy.evaluate import evaluate

    policy = _policy(_rule("violation", "VIOLATION_WITNESS", "ViolationRelation", "major"))
    proved = evaluate(policy, "claim:1", _snapshot(relations={"ViolationRelation": "PROVED"}))
    unknown = evaluate(policy, "claim:1", _snapshot(relations={"ViolationRelation": "UNKNOWN"}))
    refuted = evaluate(policy, "claim:1", _snapshot(relations={"ViolationRelation": "REFUTED"}))
    assert proved.outcome == "VIOLATION_WITNESS" and proved.max_external_status == "major"
    assert unknown.outcome == "ABSTAIN"
    assert refuted.outcome == "ABSTAIN"  # clean not proved is never converted into accusation


def test_clean_requires_complete_inventory_coverage_no_unknown_and_rule_per_producer():
    from sc_referee.inference.policy.evaluate import evaluate

    policy = _policy(_rule("clean", "CLEAN_PROOF", "ProducerClean"))
    relations = {("ProducerClean", "p1"): "PROVED", ("ProducerClean", "p2"): "PROVED"}
    clean = evaluate(policy, "claim:1", _snapshot(relations=relations))
    assert clean.outcome == "CLEAN_PROOF"

    cases = (
        _snapshot(relations=relations, inventory_complete=False),
        _snapshot(relations=relations, covered_producers=frozenset({"p1"})),
        _snapshot(relations=relations, unknown_producers=frozenset({"unknown:1"})),
        _snapshot(relations={("ProducerClean", "p1"): "PROVED"}),
        _snapshot(relations=relations, coverage=frozenset({"claims"})),
    )
    for snapshot in cases:
        judgment = evaluate(policy, "claim:1", snapshot)
        assert judgment.outcome == "ABSTAIN"


def test_scope_and_required_assumptions_are_total_abstention_gates():
    from sc_referee.inference.policy.evaluate import PolicySnapshot, evaluate
    from sc_referee.inference.policy.schema import ProofRule, ValidityPolicy

    rule = ProofRule("clean", (_premise("Clean"),), (), "CLEAN_PROOF", "pass", ("A",))
    policy = ValidityPolicy("scoped", (_premise("InScope"),), (rule,), frozenset())
    base = PolicySnapshot(True, frozenset(), frozenset(), frozenset(), frozenset(),
                          {"InScope": "PROVED", "Clean": "PROVED"}, {}, frozenset())
    assert evaluate(policy, "claim", base).outcome == "ABSTAIN"

    with_assumption = PolicySnapshot(
        base.inventory_complete, base.possible_producers, base.covered_producers,
        base.unknown_producers, base.coverage, base.relations, base.facts,
        frozenset({"A"}),
    )
    assert evaluate(policy, "claim", with_assumption).outcome == "CLEAN_PROOF"

    out_of_scope = PolicySnapshot(
        True, frozenset(), frozenset(), frozenset(), frozenset(),
        {"InScope": "REFUTED", "Clean": "PROVED"}, {}, frozenset({"A"}),
    )
    assert evaluate(policy, "claim", out_of_scope).outcome == "ABSTAIN"


def test_provider_failure_is_a_total_abstention_not_an_evaluator_exception():
    from sc_referee.inference.policy.evaluate import evaluate
    from sc_referee.inference.policy.schema import ProviderInvocation, ProofRule

    class BrokenRegistry:
        def invoke(self, _invocation, _facts):
            raise RuntimeError("provider unavailable")

    invocation = ProviderInvocation("provider.v1", "1", "sha256:test", {}, "Exact")
    rule = ProofRule("clean", (), (invocation,), "CLEAN_PROOF", "pass", ())
    judgment = evaluate(_policy(rule), "claim", _snapshot(), BrokenRegistry())
    assert judgment.outcome == "ABSTAIN"
    assert "CLEAN_RULE_UNPROVED" in judgment.obligations


def test_relation_premise_arguments_are_exactly_bound_not_ignored():
    from sc_referee.inference.policy.evaluate import evaluate
    from sc_referee.inference.policy.schema import FactRef, ProofRule, RelationPremise, ValidityPolicy

    premise = RelationPremise("ExactMatch", (FactRef("ExpectedValue", {}), "$claim"))
    rule = ProofRule("clean", (premise,), (), "CLEAN_PROOF", "pass", ())
    policy = ValidityPolicy("argument-bound", (), (rule,), frozenset())
    exact = _snapshot(
        facts={"ExpectedValue": 3},
        relations={("ExactMatch", (3, "claim:1"), "p1"): "PROVED",
                   ("ExactMatch", (3, "claim:1"), "p2"): "PROVED"},
    )
    misleading = _snapshot(facts={"ExpectedValue": 3}, relations={"ExactMatch": "PROVED"})
    assert evaluate(policy, "claim:1", exact).outcome == "CLEAN_PROOF"
    assert evaluate(policy, "claim:1", misleading).outcome == "ABSTAIN"
