from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
from inspect import getsource
import json


def _invoke(registry, provider_id, relation, inputs, *, version="1", digest=None):
    from sc_referee.inference.policy.schema import ProviderInvocation

    provider = next((item for item in registry.providers if item.identity.id == provider_id), None)
    digest = digest or (provider.identity.implementation_digest if provider is not None else "sha256:missing")
    invocation = ProviderInvocation(provider_id, version, digest, {}, relation)
    return registry.invoke(invocation, inputs)


def test_registry_requires_exact_id_version_and_implementation_digest():
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    assert {provider.identity.id for provider in registry.providers} == {
        "exact_rational_rank.v1", "confounding_metrics_q.v1", "ora_joint_correction.v1",
        "sign_parity.v1", "finite_set_relations.v1", "interval_bounds.v1", "unit_partition.v1",
    }
    provider = registry.providers[0]
    assert registry.resolve_exact(provider.identity.id, "1",
                                  provider.identity.implementation_digest) is provider
    assert registry.resolve_exact(provider.identity.id, "2",
                                  provider.identity.implementation_digest) is None
    assert registry.resolve_exact(provider.identity.id, "1", "sha256:mutated") is None


def test_provider_identity_digests_bind_implementation_and_typed_schemas():
    import sc_referee.inference.proof.discharge as discharge_module
    from sc_referee.inference.proof.discharge import builtin_registry

    for provider in builtin_registry().providers:
        source_digest = "sha256:" + sha256(getsource(discharge_module).encode()).hexdigest()
        input_digest = "sha256:" + sha256(json.dumps(
            sorted(provider.input_fields), separators=(",", ":")
        ).encode()).hexdigest()
        output_digest = "sha256:" + sha256(json.dumps(
            sorted(provider.output_relations), separators=(",", ":")
        ).encode()).hexdigest()
        assert provider.identity.implementation_digest == source_digest
        assert provider.identity.input_schema_digest == input_digest
        assert provider.identity.output_schema_digest == output_digest


def test_exact_rank_provider_reuses_closed_solver_and_replays_stably():
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    inputs = {"matrix": ((1, 0), (0, 1)), "target_column": 1}
    first = _invoke(registry, "exact_rational_rank.v1", "TargetEstimable", inputs)
    replay = _invoke(registry, "exact_rational_rank.v1", "TargetEstimable", inputs)
    aliased = _invoke(registry, "exact_rational_rank.v1", "TargetAliased",
                      {"matrix": ((1, 1), (2, 2)), "target_column": 1})
    unsupported = _invoke(registry, "exact_rational_rank.v1", "TargetEstimable",
                          {"matrix": ((1.5, 0), (0, 1)), "target_column": 1})

    assert first.status == "PROVED" and first.typed_outputs["rank"] == 2
    assert replay.derivation == first.derivation and replay.input_digest == first.input_digest
    assert aliased.status == "PROVED"
    assert unsupported.status == "UNKNOWN"
    assert aliased.input_digest != first.input_digest


def test_provider_input_digest_is_relation_independent_but_derivation_is_not():
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    inputs = {"matrix": ((1, 0), (0, 1)), "target_column": 1}
    estimable = _invoke(registry, "exact_rational_rank.v1", "TargetEstimable", inputs)
    aliased = _invoke(registry, "exact_rational_rank.v1", "TargetAliased", inputs)
    assert estimable.input_digest == aliased.input_digest
    assert estimable.derivation != aliased.derivation


def test_confounding_metrics_q_matches_exact_partial_r2_vif_ovb_and_thresholds():
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    target = (0, 0, 0, 1, 0, 1, 1, 1)
    run = ((0,), (0,), (0,), (0,), (1,), (1,), (1,), (1,))
    inputs = {
        "target": target, "included": tuple(() for _ in target), "omitted": run,
        "nuisance": run, "omitted_r2_threshold": Fraction(1, 100),
        "vif_threshold": Fraction(10, 1),
    }
    major = _invoke(registry, "confounding_metrics_q.v1", "OmittedPartialR2AtLeast", inputs)
    advisory = _invoke(registry, "confounding_metrics_q.v1", "VifAtLeast", inputs)

    assert major.status == "PROVED"
    assert major.typed_outputs["omitted_partial_r2"] == Fraction(1, 4)
    assert major.typed_outputs["vif"] == Fraction(4, 3)
    assert tuple(major.typed_outputs["ovb_multipliers"].values()) == (Fraction(1, 2),)
    assert advisory.status == "REFUTED"

    at_boundary = dict(inputs, omitted_r2_threshold=Fraction(1, 4))
    assert _invoke(registry, "confounding_metrics_q.v1",
                   "OmittedPartialR2AtLeast", at_boundary).status == "PROVED"
    bad = dict(inputs, target=tuple(float(value) for value in target))
    assert _invoke(registry, "confounding_metrics_q.v1",
                   "OmittedPartialR2AtLeast", bad).status == "UNKNOWN"


def test_ora_provider_recomputes_the_declared_complete_bh_family_and_materiality():
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    inputs = {
        "population": 100, "term_size": 10, "draws": 5, "overlap": 2,
        "family_raw_pvalues": (Fraction(1, 1000), Fraction(1, 50), Fraction(1, 20)),
        "target_index": 0, "procedure": "bh", "alpha": Fraction(1, 20),
        "reported_adjusted_p": Fraction(3, 1000), "reported_significant": True,
        "family_complete": True,
    }
    result = _invoke(registry, "ora_joint_correction.v1",
                     "ReportedMoreSignificantThanCorrected", inputs)
    assert result.status == "PROVED"
    assert isinstance(result.typed_outputs["tail_p"], Fraction)
    assert result.typed_outputs["corrected_adjusted_p"] >= result.typed_outputs["tail_p"]
    assert result.typed_outputs["original_adjusted_p"] == Fraction(3, 1000)
    assert result.typed_outputs["procedure"] == "bh"
    assert {"population", "term_size", "draws", "overlap"} <= set(result.typed_outputs)

    impossible = dict(inputs, overlap=11)
    assert _invoke(registry, "ora_joint_correction.v1",
                   "ReportedMoreSignificantThanCorrected", impossible).status == "UNKNOWN"


def test_ora_provider_does_not_substitute_bonferroni_for_a_correct_bh_analysis():
    from math import comb

    from sc_referee.inference.proof.discharge import builtin_registry

    denominator = comb(100, 5)
    tail = sum(
        (Fraction(comb(10, k) * comb(90, 5 - k), denominator)
         for k in range(3, 6)),
        Fraction(0),
    )
    # This exact BH family remains significant after recomputing the target from the corrected cells.
    reported_bh = min(Fraction(1), tail * 3)
    inputs = {
        "population": 100, "term_size": 10, "draws": 5, "overlap": 3,
        "family_raw_pvalues": (tail, Fraction(1, 5), Fraction(1, 2)),
        "target_index": 0, "procedure": "bh", "alpha": Fraction(1, 20),
        "reported_adjusted_p": reported_bh, "reported_significant": True,
        "family_complete": True,
    }

    result = _invoke(builtin_registry(), "ora_joint_correction.v1",
                     "ReportedMoreSignificantThanCorrected", inputs)

    assert result.status == "REFUTED"
    assert result.typed_outputs["corrected_adjusted_p"] == reported_bh


def test_ora_provider_is_unknown_for_unsupported_procedure_or_incomplete_family():
    from sc_referee.inference.proof.discharge import builtin_registry

    base = {
        "population": 100, "term_size": 10, "draws": 5, "overlap": 2,
        "family_raw_pvalues": (Fraction(1, 100),), "target_index": 0,
        "procedure": "storey", "alpha": Fraction(1, 20),
        "reported_adjusted_p": Fraction(1, 100), "reported_significant": True,
        "family_complete": True,
    }
    assert _invoke(builtin_registry(), "ora_joint_correction.v1",
                   "ReportedMoreSignificantThanCorrected", base).status == "UNKNOWN"
    incomplete = dict(base, procedure="bh", family_complete=False)
    assert _invoke(builtin_registry(), "ora_joint_correction.v1",
                   "ReportedMoreSignificantThanCorrected", incomplete).status == "UNKNOWN"


def test_sign_parity_is_joint_not_per_source():
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    joint = {"required_factors": (-1, -1), "applied_multiplier": 1}
    assert _invoke(registry, "sign_parity.v1", "JointSignConsistent", joint).status == "PROVED"
    assert _invoke(registry, "sign_parity.v1", "JointSignInconsistent", joint).status == "REFUTED"
    assert _invoke(registry, "sign_parity.v1", "JointSignConsistent",
                   {"required_factors": (-1, 0), "applied_multiplier": 1}).status == "UNKNOWN"


def test_finite_set_interval_and_unit_providers_are_exact_and_typed():
    from sc_referee.inference.domains.unit import (
        RelationSource, UnitRef, UnitRelationFact, UnitRelationKind,
    )
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    sets = {"left": frozenset({1, 2}), "right": frozenset({2, 3})}
    assert _invoke(registry, "finite_set_relations.v1", "Intersects", sets).status == "PROVED"
    assert _invoke(registry, "finite_set_relations.v1", "Disjoint", sets).status == "REFUTED"

    legal_sentinel = {
        "value": 101,
        "contig_length": 101,
        "coordinate_role": "slice_boundary",
        "consumer_contract_id": "past_end_sentinel.linear.v1",
    }
    assert _invoke(registry, "interval_bounds.v1", "CoordinateLegal", legal_sentinel).status == "PROVED"
    assert _invoke(registry, "interval_bounds.v1", "CoordinateIllegal", legal_sentinel).status == "REFUTED"

    forged = dict(legal_sentinel, consumer_contract_id="my_inclusive_contract")
    assert _invoke(registry, "interval_bounds.v1", "CoordinateLegal", forged).status == "UNKNOWN"
    wrong_role = dict(legal_sentinel, coordinate_role="base_coordinate")
    assert _invoke(registry, "interval_bounds.v1", "CoordinateLegal", wrong_role).status == "UNKNOWN"

    rows = UnitRef("artifact", ("row",), "cell", "observation")
    donors = UnitRef("artifact", ("donor",), "donor", "replication")
    relation = UnitRelationFact(rows, donors, UnitRelationKind.STRICTLY_REFINES,
                                RelationSource.RATIFIED_FACT, "fact:unit")
    unit_inputs = {"relation": relation, "expected_kind": "strictly_refines"}
    assert _invoke(registry, "unit_partition.v1", "UnitRelationProved", unit_inputs).status == "PROVED"
    assert _invoke(registry, "unit_partition.v1", "UnitRelationProved",
                   {"relation": None, "expected_kind": "strictly_refines"}).status == "UNKNOWN"


def test_finite_set_member_does_not_require_an_unrelated_right_set():
    from sc_referee.inference.proof.discharge import builtin_registry

    result = _invoke(
        builtin_registry(), "finite_set_relations.v1", "Member",
        {"left": frozenset({"a"}), "member": "a"},
    )
    assert result.status == "PROVED"


def test_unknown_binding_returns_unknown_result_not_exception():
    from sc_referee.inference.policy.schema import ProviderInvocation
    from sc_referee.inference.proof.discharge import builtin_registry

    registry = builtin_registry()
    invocation = ProviderInvocation("missing.v1", "1", "sha256:missing", {}, "Anything")
    result = registry.invoke(invocation, {})
    assert result.status == "UNKNOWN"
    assert "provider" in result.obligations[0].lower()
