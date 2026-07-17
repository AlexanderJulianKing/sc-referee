"""Donor-level eQTL OLS sign recompute — arithmetic only, no Finding/status policy."""
from __future__ import annotations

import pytest
from scipy import sparse

from tests.factories import eqtl_count_bundle, make_eqtl_design


@pytest.mark.parametrize("matrix_type", [sparse.csr_matrix, sparse.csc_matrix])
def test_sparse_counts_match_dense_orientation_result(matrix_type):
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    bundle = eqtl_count_bundle(effect_direction=1, effect_strength=0.9, seed=17)
    dense = recompute_eqtl_sign(bundle, make_eqtl_design(), transform="identity")
    bundle.measure.counts = matrix_type(bundle.measure.counts)
    observed = recompute_eqtl_sign(bundle, make_eqtl_design(), transform="identity")
    assert observed.identified == dense.identified
    assert observed.sign == dense.sign
    assert observed.slope == pytest.approx(dense.slope)


@pytest.mark.parametrize("seed,strength", [(0, 0.7), (3, 1.0), (11, 0.85)])
def test_identity_orientation_recovers_positive_sign(seed, strength):
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    result = recompute_eqtl_sign(
        eqtl_count_bundle(effect_direction=1, effect_strength=strength, seed=seed),
        make_eqtl_design(),
        transform="identity",
    )
    assert result.identified
    assert result.sign == 1
    assert result.ci_low > 0
    assert result.transform == "identity"


@pytest.mark.parametrize("seed,strength", [(1, 0.75), (7, 0.9), (13, 1.1)])
def test_complement_orientation_recovers_positive_sign(seed, strength):
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    result = recompute_eqtl_sign(
        eqtl_count_bundle(effect_direction=-1, effect_strength=strength, seed=seed),
        make_eqtl_design(effect_allele="A", dosage_counts_allele="G"),
        transform="complement",
    )
    assert result.identified
    assert result.sign == 1
    assert result.ci_low > 0
    assert result.transform == "complement"


def test_exact_audited_donor_frequency_uniquely_resolves_complement():
    from sc_referee.engines.eqtl_sign import resolve_orientation

    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="audited_donors",
    )
    # class counts 3/3/6 -> p_raw=0.625, complement=0.375
    resolution = resolve_orientation(design, raw_frequency=0.625)
    assert resolution.resolved
    assert resolution.transform == "complement"
    assert resolution.source == "exact_cohort_frequency"


def test_external_panel_frequency_never_resolves_orientation():
    from sc_referee.engines.eqtl_sign import resolve_orientation

    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="external_panel",
    )
    resolution = resolve_orientation(design, raw_frequency=0.625)
    assert not resolution.resolved
    assert resolution.reason == "frequency_scope_not_audited_donors"


def test_exact_cohort_frequency_with_neither_candidate_matching_is_unresolved():
    from sc_referee.engines.eqtl_sign import resolve_orientation

    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.10, 0.20),
        effect_allele_frequency_scope="audited_donors",
    )
    resolution = resolve_orientation(design, raw_frequency=0.625)
    assert not resolution.resolved
    assert resolution.reason == "frequency_orientation_no_match"


def test_direct_and_frequency_footprints_can_agree():
    from sc_referee.engines.eqtl_sign import resolve_orientation

    design = make_eqtl_design(
        dosage_counts_allele="G", effect_allele="A",
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="audited_donors",
    )
    resolution = resolve_orientation(design, raw_frequency=0.625)
    assert resolution.resolved
    assert resolution.transform == "complement"
    assert resolution.source == "direct_and_frequency"


@pytest.mark.parametrize(
    "class_counts,reason",
    [((6, 0, 0), "fewer_than_3_donors_in_2_genotype_classes"),
     ((2, 2, 2), "fewer_than_3_donors_in_2_genotype_classes")],
)
def test_genotype_class_replication_gate_abstains(class_counts, reason):
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    result = recompute_eqtl_sign(
        eqtl_count_bundle(class_counts=class_counts, effect_direction=1, seed=2),
        make_eqtl_design(), transform="identity")
    assert not result.identified
    assert result.reason == reason


def test_near_zero_association_is_not_sign_identified():
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    result = recompute_eqtl_sign(
        eqtl_count_bundle(class_counts=(8, 8, 8), effect_strength=0, seed=21),
        make_eqtl_design(), transform="identity")
    assert not result.identified
    assert result.reason == "slope_sign_not_identified"


def test_nonconstant_cell_dosage_within_donor_abstains_before_aggregation():
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    bundle = eqtl_count_bundle(seed=5)
    bundle.observations.iloc[0, bundle.observations.columns.get_loc("dosage")] = 2
    result = recompute_eqtl_sign(bundle, make_eqtl_design(), transform="identity")
    assert not result.identified
    assert result.reason == "dosage_not_constant_within_donor"


def test_monomorphic_target_outcome_is_not_sign_identified():
    from sc_referee.engines.eqtl_sign import recompute_eqtl_sign

    bundle = eqtl_count_bundle(seed=9)
    bundle.measure.counts[:, 0] = 0
    result = recompute_eqtl_sign(bundle, make_eqtl_design(), transform="identity")
    assert not result.identified
    assert result.reason == "genotype_or_outcome_has_no_variation"
