from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from sc_referee.inference.policy.evaluate import PolicySnapshot, evaluate
from sc_referee.inference.policy.purity import (
    PolicyPurityError,
    lint_policy_source,
    policy_definition_files,
    validate_policy_module,
)
from sc_referee.inference.policy.schema import ValidityPolicy


POLICY_MODULES = (
    "double_dipping",
    "pseudoreplication",
    "confounding",
    "allele_harmonization",
    "enrichment_universe",
    "coordinate_consumption",
    "spatial_iid",
    "trajectory_circularity",
)


def _policies() -> tuple[ValidityPolicy, ...]:
    values = []
    for module_name in POLICY_MODULES:
        module = __import__(
            f"sc_referee.inference.policy.definitions.{module_name}", fromlist=["POLICY"]
        )
        values.append(module.POLICY)
    return tuple(values)


def _snapshot(*relations: str) -> PolicySnapshot:
    return PolicySnapshot(
        inventory_complete=True,
        possible_producers=frozenset({"producer"}),
        covered_producers=frozenset({"producer"}),
        unknown_producers=frozenset(),
        coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
        relations={name: "PROVED" for name in relations},
        facts={},
    )


@dataclass(frozen=True)
class _ProviderResult:
    status: str = "PROVED"


class _ProvingRegistry:
    def __init__(self, relations=()):
        self.relations = frozenset(relations)

    def invoke(self, _invocation, _bound):
        return _ProviderResult("PROVED" if _invocation.expected_relation in self.relations else "REFUTED")


def test_policy_modules_are_pure_and_provider_bound():
    paths = policy_definition_files()
    assert {path.stem for path in paths} == set(POLICY_MODULES)
    for path in paths:
        validate_policy_module(path)


def test_purity_lint_demonstrably_rejects_an_impure_fixture_outside_definitions():
    impure = """
import numpy
from sc_referee.inference.policy.schema import ValidityPolicy
def solve(values):
    return [value for value in values if value]
POLICY = ValidityPolicy('bad', (), (), frozenset())
"""
    with pytest.raises(PolicyPurityError) as error:
        lint_policy_source(impure, filename="deliberately_impure_policy.py")
    message = str(error.value)
    assert "numpy" in message
    assert "FunctionDef" in message
    assert "ListComp" in message


def test_purity_lint_rejects_computation_and_unapproved_calls_without_imports():
    impure = """
from sc_referee.inference.policy.schema import ValidityPolicy
LIMIT = 1 + 2
FLAG = 1 < 2
DATA = open('secret')
POLICY = ValidityPolicy('bad', (), (), frozenset())
"""
    with pytest.raises(PolicyPurityError) as error:
        lint_policy_source(impure, filename="computed_policy.py")
    message = str(error.value)
    assert "BinOp" in message and "Compare" in message and "open" in message


@pytest.mark.parametrize("policy", _policies(), ids=lambda item: item.id)
def test_each_policy_has_isolated_clean_violation_and_abstain_cases(policy):
    clean = next(rule for rule in policy.rules if rule.outcome == "CLEAN_PROOF")
    violation = next(rule for rule in policy.rules if rule.outcome == "VIOLATION_WITNESS")
    scope = tuple(premise.relation for premise in policy.scope)
    clean_judgment = evaluate(
        policy, "claim", _snapshot(*scope, *(p.relation for p in clean.premises)),
        _ProvingRegistry(item.expected_relation for item in clean.discharge),
    )
    assert clean_judgment.outcome == "CLEAN_PROOF"
    violation_judgment = evaluate(
        policy,
        "claim",
        _snapshot(*scope, *(p.relation for p in violation.premises)),
        _ProvingRegistry(item.expected_relation for item in violation.discharge),
    )
    assert violation_judgment.outcome == "VIOLATION_WITNESS"
    assert violation_judgment.max_external_status == violation.max_external_status
    assert evaluate(policy, "claim", _snapshot(*scope), _ProvingRegistry()).outcome == "ABSTAIN"


@pytest.mark.parametrize(
    ("policy_id", "insufficient_relation"),
    (
        ("double_dipping.v1", "GroupingDataDerived"),
        ("pseudoreplication.v1", "RowsStrictlyRefineReplicationUnit"),
        ("confounding.v2", "SetupConfirmed"),
        ("allele_harmonization.v1", "PerSourceSignMismatch"),
        ("enrichment_universe.v1", "InflatedK"),
        ("coordinate_consumption.v1", "CoordinateAboveContigLength"),
        ("spatial_iid.v1", "PoweredPseudobulkCollapse"),
        ("trajectory_circularity.v1", "SameObjectOnly"),
    ),
)
def test_necessary_but_not_sufficient_math_never_accuses(policy_id, insufficient_relation):
    policy = next(item for item in _policies() if item.id == policy_id)
    scope = tuple(premise.relation for premise in policy.scope)
    judgment = evaluate(policy, "claim", _snapshot(*scope, insufficient_relation), _ProvingRegistry())
    assert judgment.outcome == "ABSTAIN"


def test_policy_definitions_encode_joint_and_consumer_contract_providers():
    policies = {policy.id: policy for policy in _policies()}
    expectations = {
        "allele_harmonization.v1": ("sign_parity.v1", "JointSignInconsistent"),
        "enrichment_universe.v1": (
            "ora_joint_correction.v1", "ReportedMoreSignificantThanCorrected"
        ),
        "coordinate_consumption.v1": ("interval_bounds.v1", "CoordinateIllegal"),
    }
    for policy_id, expected in expectations.items():
        violation = next(
            rule for rule in policies[policy_id].rules if rule.outcome == "VIOLATION_WITNESS"
        )
        assert {(item.provider_id, item.expected_relation) for item in violation.discharge} == {expected}
    trajectory = policies["trajectory_circularity.v1"]
    violation = next(rule for rule in trajectory.rules if rule.outcome == "VIOLATION_WITNESS")
    assert violation.max_external_status == "needs_evidence"


def test_confounding_r1_r4_bind_every_computed_premise_to_exact_providers():
    policy = next(item for item in _policies() if item.id == "confounding.v2")
    rules = {rule.id: rule for rule in policy.rules}
    assert {item.expected_relation for item in rules["R1_STRUCTURAL_ALIAS"].discharge} == {
        "TargetAliased"
    }
    assert {item.expected_relation for item in rules["R2_GRADED_OMITTED_CONFOUNDING"].discharge} == {
        "OmittedNuisancePresent", "OmittedPartialR2AtLeast"
    }
    assert {item.expected_relation for item in rules["R3_NEAR_COLLINEAR"].discharge} == {
        "VifAtLeast"
    }
    assert {item.expected_relation for item in rules["R4_ESTIMABLE"].discharge} == {
        "TargetEstimable", "OmittedPartialR2Below", "VifBelow"
    }
    metric_calls = tuple(
        invocation for rule in rules.values() for invocation in rule.discharge
        if invocation.provider_id == "confounding_metrics_q.v1"
    )
    assert metric_calls
    assert all(item.inputs["omitted_r2_threshold"] == (1, 100) for item in metric_calls)
    assert all(item.inputs["vif_threshold"] == 10 for item in metric_calls)


def test_policy_definition_directory_contains_no_impure_fixture():
    assert not any("impure" in path.name for path in policy_definition_files())
    assert all("definitions" in Path(path).parts for path in policy_definition_files())
