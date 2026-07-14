"""Shared test factories: Design builder + factor-table fixtures of known structure."""
from dataclasses import replace
import numpy as np
import pandas as pd

from sc_referee.bundle import Bundle, Measure
from sc_referee.design import (
    BatchComponentScope,
    BatchModelingDeclaration,
    Design,
    FittedDesignDeclaration,
)


def make_design(
    reference="ctrl",
    test="stim",
    condition="condition",
    batch=("run",),
    replicate_unit=("donor_id",),
    model="~ condition",
    confirmed=True,
    confidence_high=True,
    condition_confidence_high=True,
    sample_unit=None,
    pairing_unit=None,
    subset=None,
    target_coefficient=None,
    unit_of_test="cell",
    analyst_adjusted_for=None,
    confidence=None,
    analysis_type="condition_contrast_DE",
    aggregation_key=None,
    fitted_design=None,
    row_ledger=None,
    aggregation_key_confidence_high=True,
    pairing_estimand=None,
    pairing_mechanics=None,
    effect_relevance_contract=None,
    multiplicity_contract=None,
    report_inference_contract=None,
    allele_orientation_confidence_high=True,
    hic_loop_strength_confidence_high=True,
    variant_id=None,
    genotype_column=None,
    target_feature=None,
    effect_allele=None,
    dosage_counts_allele=None,
    variant_alleles=None,
    dosage_ploidy=None,
    effect_allele_frequency_interval=None,
    effect_allele_frequency_scope=None,
    eqtl_estimator=None,
    eqtl_outcome_scale=None,
    hic_genome_assembly=None,
    hic_resolution_bp=None,
    hic_target_bin_i=None,
    hic_target_bin_j=None,
    hic_background_view_start=None,
    hic_background_view_end=None,
    hic_contact_scale=None,
    hic_expected_model=None,
    hic_mask_policy=None,
    hic_zero_policy=None,
    hic_pseudocount=None,
    hic_target_statistic=None,
    hic_replicate_functional=None,
    hic_report_delta_tolerance=None,
    hic_report_delta_tolerance_authority=None,
    estimand_id=None,
    csp_contracts=(),
):
    return Design(
        analysis_type=analysis_type,
        confirmed_by_human=confirmed,
        confidence=confidence or {
            "replicate_unit": "high" if confidence_high else "low",
            "condition": "high" if condition_confidence_high else "low",
            "analyst_adjusted_for": "high" if analyst_adjusted_for is not None else "low",
            "aggregation_key": "high" if aggregation_key_confidence_high else "low",
            "allele_orientation": "high" if allele_orientation_confidence_high else "low",
            "hic_loop_strength": "high" if hic_loop_strength_confidence_high else "low",
        },
        condition=condition,
        batch=list(batch),
        replicate_unit=list(replicate_unit),
        reference=reference,
        test=test,
        model=model,
        target_coefficient=(target_coefficient if target_coefficient is not None
                            else (None if analysis_type == "eqtl" else f"{condition}[T.{test}]")),
        sample_unit=list(sample_unit or replicate_unit),
        pairing_unit=list(replicate_unit if pairing_unit is None else pairing_unit),
        subset=subset,
        unit_of_test=unit_of_test,
        analyst_adjusted_for=analyst_adjusted_for,
        aggregation_key=list(aggregation_key) if aggregation_key is not None else None,
        fitted_design=fitted_design,
        row_ledger=row_ledger,
        pairing_estimand=pairing_estimand,
        pairing_mechanics=pairing_mechanics,
        effect_relevance_contract=effect_relevance_contract,
        multiplicity_contract=multiplicity_contract,
        report_inference_contract=report_inference_contract,
        variant_id=variant_id,
        genotype_column=genotype_column,
        target_feature=target_feature,
        effect_allele=effect_allele,
        dosage_counts_allele=dosage_counts_allele,
        variant_alleles=tuple(variant_alleles) if variant_alleles is not None else None,
        dosage_ploidy=dosage_ploidy,
        effect_allele_frequency_interval=(tuple(effect_allele_frequency_interval)
                                          if effect_allele_frequency_interval is not None else None),
        effect_allele_frequency_scope=effect_allele_frequency_scope,
        eqtl_estimator=eqtl_estimator,
        eqtl_outcome_scale=eqtl_outcome_scale,
        hic_genome_assembly=hic_genome_assembly,
        hic_resolution_bp=hic_resolution_bp,
        hic_target_bin_i=hic_target_bin_i,
        hic_target_bin_j=hic_target_bin_j,
        hic_background_view_start=hic_background_view_start,
        hic_background_view_end=hic_background_view_end,
        hic_contact_scale=hic_contact_scale,
        hic_expected_model=hic_expected_model,
        hic_mask_policy=hic_mask_policy,
        hic_zero_policy=hic_zero_policy,
        hic_pseudocount=hic_pseudocount,
        hic_target_statistic=hic_target_statistic,
        hic_replicate_functional=hic_replicate_functional,
        hic_report_delta_tolerance=hic_report_delta_tolerance,
        hic_report_delta_tolerance_authority=hic_report_delta_tolerance_authority,
        estimand_id=estimand_id,
        csp_contracts=tuple(csp_contracts),
    )


def fitted_design_declaration(**overrides):
    base = dict(
        rows_exact=True,
        operator_kind="ordinary_fixed_effects",
        intercept=True,
        column_kinds={"condition": "categorical", "run": "categorical"},
        categorical_levels={"condition": ("ctrl", "stim"), "run": ("R1", "R2")},
        transforms={"condition": "identity", "run": "identity"},
    )
    base.update(overrides)
    return FittedDesignDeclaration(**base)


def random_intercept_batch_declaration(**overrides):
    base = dict(
        source_column="run", modeled_as="random_intercept", random_group_column="run",
        fixed_source_columns=(), rows_exact=True, row_ledger_identity=None,
        component_scope=BatchComponentScope(
            contrast_name="contrast", target_coefficient="condition[T.stim]",
            fitted_result_id="fixture-results#contrast",
        ),
        unsupported_components=(),
        field_confidence={
            "source_column": "high", "modeled_as": "high", "random_group_column": "high",
            "fixed_source_columns": "high", "rows_exact": "high",
            "row_ledger_identity": "high", "component_scope": "high",
            "unsupported_components": "high",
        },
        evidence_locations={"modeled_as": ("tests/fixture-model.R:1",)},
    )
    base.update(overrides)
    return BatchModelingDeclaration(**base)


def pseudobulk_confounding_bundle(*, with_w=False):
    observations = pd.DataFrame({
        "donor_id": [f"D{i}" for i in range(1, 9)],
        "condition": ["ctrl"] * 4 + ["stim"] * 4,
        "run": ["R1", "R1", "R1", "R2", "R1", "R2", "R2", "R2"],
    }, index=[f"cell-{i}" for i in range(1, 9)])
    if with_w:
        observations["W"] = ["A", "A", "A", "B", "C", "B", "B", "C"]
    counts = np.asarray([[10 + i, 20 - i] for i in range(8)], dtype=np.int64)
    return Bundle(
        observations=observations,
        measure=Measure("counts", counts, None, ["g1", "g2"]),
        feature_metadata=pd.DataFrame(index=["g1", "g2"]),
        replicate_var="donor_id",
    )


def random_intercept_design(bundle, *, adjusted, with_w=False, operator_kind="random_intercept_only",
                            **entry_overrides):
    entry = random_intercept_batch_declaration(**entry_overrides)
    kinds = {"condition": "categorical", "run": "categorical"}
    levels = {"condition": ("ctrl", "stim"), "run": ("R1", "R2")}
    if with_w:
        kinds["W"] = "categorical"
        levels["W"] = ("A", "B", "C")
    declaration = fitted_design_declaration(
        operator_kind=operator_kind,
        column_kinds=kinds, categorical_levels=levels,
        transforms={source: "identity" for source in kinds},
        batch_modeling={"run": entry},
    )
    design = make_design(
        batch=("run",), sample_unit=("donor_id",), aggregation_key=("donor_id",),
        analyst_adjusted_for=list(adjusted), fitted_design=declaration,
        confidence={
            "condition": "high", "batch": "high", "analyst_adjusted_for": "high",
            "aggregation_key": "high", "fitted_design": "high",
        },
    )
    rows = __import__("sc_referee.engine", fromlist=["build_pseudobulk_sample_rows"]).build_pseudobulk_sample_rows(
        bundle.observations, design
    )
    bound = replace(entry, row_ledger_identity=rows.row_ledger_identity)
    return replace(design, fitted_design=replace(declaration, batch_modeling={"run": bound}))


def fixed_and_random_certified_fixture():
    bundle = pseudobulk_confounding_bundle()
    design = random_intercept_design(
        bundle, adjusted=["run", "condition"], operator_kind="ordinary_fixed_effects",
        modeled_as="fixed_and_random_intercept", fixed_source_columns=("run",),
    )
    return design, bundle


def make_eqtl_design(**overrides):
    """Complete, high-confidence OLS/log-CPM eQTL contract; tests override one fact at a time."""
    base = dict(
        analysis_type="eqtl", condition=None, reference=None, test=None, batch=(),
        replicate_unit=("donor_id",), sample_unit=("donor_id",), pairing_unit=(),
        model=None, target_coefficient=None, unit_of_test="sample",
        variant_id="rs1", genotype_column="dosage", target_feature="TARGET",
        effect_allele="A", dosage_counts_allele="A", variant_alleles=("A", "G"),
        dosage_ploidy=2, eqtl_estimator="ols", eqtl_outcome_scale="log2_cpm_plus_1",
    )
    base.update(overrides)
    return make_design(**base)


def make_hic_design(**overrides):
    """Complete supported Hi-C loop-strength contract; tests override one fact at a time."""
    base = dict(
        analysis_type="hic_loop_strength", condition="condition", reference="ctrl", test="stim",
        batch=(), replicate_unit=("replicate",), sample_unit=("replicate", "condition"),
        pairing_unit=(), model="~ condition", target_coefficient="condition[T.stim]",
        unit_of_test="sample", hic_genome_assembly="hg38", hic_resolution_bp=10_000,
        hic_target_bin_i="b20", hic_target_bin_j="b25", hic_background_view_start=0,
        hic_background_view_end=640_000,
        hic_contact_scale="raw_unbalanced_integer_counts",
        hic_expected_model="cis_exact_distance_arithmetic_mean_target_excluded_v1",
        hic_mask_policy="exclude_if_either_bin_masked_v1",
        hic_zero_policy="dense_including_zeros", hic_pseudocount=0.0,
        hic_target_statistic="single_pixel",
        hic_replicate_functional="equal_weight_mean_log2_oe_v1",
        hic_report_delta_tolerance=1e-6,
        hic_report_delta_tolerance_authority="rounding_absolute_log2_ratio_delta",
    )
    base.update(overrides)
    return make_design(**base)


def hic_contact_bundle(
    *,
    reference_strengths=(1, 1, 1),
    test_strengths=(2, 2, 2),
    background_counts=None,
    n_bins=64,
    distance_bins=5,
    resolution=10_000,
    masked_indices=(2, 50),
    seed=0,
    report_delta=None,
    reverse_report_pair=False,
):
    """Dense exact-distance synthetic Hi-C relation with analytically known log2(O/E)."""
    from sc_referee.bundle import HiCBundle, HiCContactData

    rng = np.random.default_rng(seed)
    bin_ids = [f"b{i}" for i in range(n_bins)]
    masked = np.zeros(n_bins, dtype=bool)
    masked[list(masked_indices)] = True
    bins = pd.DataFrame({
        "bin_id": bin_ids,
        "chrom": ["chr1"] * n_bins,
        "start": np.arange(n_bins, dtype=int) * resolution,
        "masked": masked,
    })
    target = ("b20", f"b{20 + distance_bins}")
    samples = [
        *(('ctrl', f'C{i + 1}', strength) for i, strength in enumerate(reference_strengths)),
        *(('stim', f'S{i + 1}', strength) for i, strength in enumerate(test_strengths)),
    ]
    if background_counts is None:
        background_counts = [16] * len(samples)
    rows = []
    for (condition, replicate, strength), background in zip(samples, background_counts):
        for i in range(n_bins - distance_bins):
            left, right = bin_ids[i], bin_ids[i + distance_bins]
            count = int(background)
            if (left, right) == target:
                count = int(background * (2 ** strength))
            if rng.integers(0, 2):
                left, right = right, left
            rows.append((replicate, condition, left, right, count))
    contacts = pd.DataFrame(
        rows, columns=["replicate", "condition", "bin_i", "bin_j", "observed_count"])
    if report_delta is None:
        report_delta = float(np.mean(test_strengths) - np.mean(reference_strengths))
    report_i, report_j = target[::-1] if reverse_report_pair else target
    reported = pd.DataFrame({
        "genome_assembly": ["hg38"], "resolution_bp": [resolution],
        "bin_i": [report_i], "bin_j": [report_j], "reference": ["ctrl"], "test": ["stim"],
        "delta": [report_delta],
    })
    return HiCBundle(
        hic=HiCContactData(contacts=contacts, bins=bins),
        reported_results=reported,
    )


def alias_obs():
    """condition completely aliased with `run` (batch): all ctrl in R1, all stim in R2."""
    return pd.DataFrame(
        {
            "donor_id": [f"D{i}" for i in range(1, 9)],
            "condition": ["ctrl"] * 4 + ["stim"] * 4,
            "run": ["R1"] * 4 + ["R2"] * 4,
        }
    )


def paired_crossed_obs():
    """Paired design, batch crossed with condition (each run has both conditions)."""
    return pd.DataFrame(
        {
            "donor_id": ["D1", "D1", "D2", "D2", "D3", "D3", "D4", "D4"],
            "condition": ["ctrl", "stim"] * 4,
            "run": ["R1", "R1", "R2", "R2", "R1", "R1", "R2", "R2"],
        }
    )


def unpaired_crossed_obs():
    """VALID unpaired design: donors unique per condition, but batch CROSSED with
    condition (each run holds both conditions). Must PASS — this is the case the buggy
    'union replicate_unit into nuisance' rule would false-flag."""
    return pd.DataFrame(
        {
            "donor_id": [f"D{i}" for i in range(1, 9)],
            "condition": ["ctrl"] * 4 + ["stim"] * 4,
            # R1 = D1,D2 (ctrl) + D5,D6 (stim); R2 = D3,D4 (ctrl) + D7,D8 (stim)
            "run": ["R1", "R1", "R2", "R2", "R1", "R1", "R2", "R2"],
        }
    )


def unpaired_nobatch_obs():
    """VALID unpaired design, no batch factor at all. Must PASS."""
    return pd.DataFrame(
        {
            "donor_id": [f"D{i}" for i in range(1, 7)],
            "condition": ["ctrl", "stim"] * 3,
        }
    )


def paired_count_bundle(n_donors=8, cells=12, n_bg=30, up_ctrl=10, up_stim=40, seed=1):
    """A paired condition-contrast bundle: each donor has ctrl+stim cells. `G_up` is a
    strong, donor-consistent effect (~log2(up_stim/up_ctrl)); `G_null` and the background
    are null. Used to test the recompute engines + experimental_unit end-to-end."""
    rng = np.random.default_rng(seed)
    genes = ["G_up", "G_null"] + [f"bg{i}" for i in range(n_bg)]
    obs_rows, counts_rows = [], []
    for di in range(n_donors):
        donor = f"D{di + 1}"
        for cond in ("ctrl", "stim"):
            for _ in range(cells):
                obs_rows.append((donor, cond))
                up = rng.poisson(up_ctrl if cond == "ctrl" else up_stim)
                null = rng.poisson(20)
                bg = rng.poisson(30, size=n_bg)
                counts_rows.append([up, null, *bg])
    obs = pd.DataFrame(obs_rows, columns=["donor_id", "condition"],
                       index=[f"c{i}" for i in range(len(obs_rows))])
    counts = np.array(counts_rows, dtype="int64")
    return Bundle(
        observations=obs,
        measure=Measure("counts", counts, None, genes),
        feature_metadata=pd.DataFrame(index=genes),
        replicate_var="donor_id",
    )


def eqtl_count_bundle(class_counts=(4, 4, 4), cells=8, effect_direction=1,
                      effect_strength=0.8, seed=0):
    """Synthetic donor eQTL raw counts. Only the sign relation is stable/pinned; fitted magnitudes vary."""
    rng = np.random.default_rng(seed)
    genes = ["TARGET"] + [f"bg{i}" for i in range(20)]
    obs_rows, count_rows = [], []
    donor_i = 0
    for dosage, n_donors in enumerate(class_counts):
        for _ in range(n_donors):
            donor = f"D{donor_i + 1}"
            donor_i += 1
            donor_shift = rng.normal(0, 0.08)
            log_mu = np.log(18.0) + effect_direction * effect_strength * (dosage - 1) + donor_shift
            for _ in range(cells):
                obs_rows.append((donor, dosage))
                target = rng.poisson(np.exp(log_mu))
                background = rng.poisson(90, size=20)
                count_rows.append([target, *background])
    obs = pd.DataFrame(obs_rows, columns=["donor_id", "dosage"],
                       index=[f"c{i}" for i in range(len(obs_rows))])
    counts = np.asarray(count_rows, dtype="int64")
    return Bundle(
        observations=obs,
        measure=Measure("counts", counts, None, genes),
        feature_metadata=pd.DataFrame(index=genes),
        replicate_var="donor_id",
    )


def single_bridge_obs():
    """Only ONE run contains both conditions (a single bridging stratum) -> major."""
    return pd.DataFrame(
        {
            "donor_id": [f"D{i}" for i in range(1, 9)],
            # R1 bridges (ctrl+stim); R2 ctrl-only; R3 stim-only
            "condition": ["ctrl", "ctrl", "stim", "stim", "ctrl", "ctrl", "stim", "stim"],
            "run": ["R1", "R1", "R1", "R1", "R2", "R2", "R3", "R3"],
        }
    )
