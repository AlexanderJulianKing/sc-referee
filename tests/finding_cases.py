"""Real emitted-finding cases used by the canonical projection inventory."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from tests.factories import make_design, paired_count_bundle


SemanticClass = str


@dataclass(frozen=True)
class FindingCase:
    emitter_id: str
    check_id: str
    scenario: Callable[[], Finding]
    expected: tuple[str, str, str, str | None]
    semantic_class: SemanticClass
    expected_human_state: str


def _case(emitter_id, check_id, scenario, expected, semantic_class, human_state):
    return FindingCase(emitter_id, check_id, scenario, expected, semantic_class, human_state)


def _confounding(name):
    from sc_referee.checks.confounding import ConfoundingCheck
    from tests.frozen_oracles.cases import confounding_cases

    _, observations, design = next(row for row in confounding_cases() if row[0] == name)
    bundle = paired_count_bundle(n_donors=4)
    bundle.observations = observations
    return ConfoundingCheck().run(design, bundle)


def _effect(effects, padj):
    from sc_referee.checks.effect_size import EffectSizeCheck

    table = pd.DataFrame({
        "feature_id": [f"g{i}" for i in range(len(effects))],
        "pvalue": padj,
        "padj": padj,
        "effect": effects,
    })
    bundle = paired_count_bundle(n_donors=4)
    bundle.reported_results = table
    return EffectSizeCheck().run(make_design(), bundle, table)


def _multiple(kind):
    from sc_referee.checks.multiple_testing import MultipleTestingCheck
    from tests.test_multiple_testing import _reported

    design = make_design(confirmed=kind != "unconfirmed")
    table = (_reported([1e-12] * 30) if kind == "harmless"
             else _reported([0.04] * 40))
    bundle = paired_count_bundle(n_donors=4)
    bundle.reported_results = table
    return MultipleTestingCheck().run(design, bundle, table)


def _pairing(kind):
    from sc_referee.checks.pairing import PairingCheck
    from tests.factories import paired_crossed_obs
    from tests.test_pairing import _bundle, _dup_obs, _paired_design, _unpaired_design

    if kind == "omitted":
        return PairingCheck().run(_unpaired_design(), _bundle(paired_crossed_obs()))
    if kind == "partial":
        obs = paired_crossed_obs()
        obs = obs[~((obs["donor_id"] == "D4") & (obs["condition"] == "stim"))]
        return PairingCheck().run(_paired_design(), _bundle(obs))
    design = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                         aggregation_key=["donor_id", "condition", "batch"])
    return PairingCheck().run(design, _bundle(_dup_obs()))


def _double(kind):
    from sc_referee.checks.double_dipping import DoubleDippingCheck
    from tests.test_double_dipping import _marker_bundle

    bundle = _marker_bundle(
        safeguards=("countsplit",) if kind == "safeguard" else (),
        pvalues=kind != "descriptive",
    )
    design = make_design(analysis_type="marker_detection", unit_of_test="cell")
    return DoubleDippingCheck().run(design, bundle, bundle.reported_results)


def _pseudobulk(kind):
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    from tests.test_pseudobulk_integrity import _DDS, _bundle, _dds_bundle
    from tests.factories import paired_crossed_obs

    if kind == "scale":
        bundle = _bundle("normalized", _DDS.format(resp="adata.X"))
        design = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    else:
        bundle = _dds_bundle(paired_crossed_obs())
        design = make_design(unit_of_test="sample", sample_unit=["donor_id"],
                             aggregation_key=["donor_id"], confirmed=False)
    return PseudobulkIntegrityCheck().run(design, bundle)


def _allele(kind):
    from tests.test_allele_orientation import _evaluate
    from tests.factories import make_eqtl_design

    if kind == "agreement_gap":
        return _evaluate(make_eqtl_design(allele_orientation_confidence_high=False))
    if kind == "mismatch_gap":
        return _evaluate(make_eqtl_design(allele_orientation_confidence_high=False), effect=-0.5)
    return _evaluate(make_eqtl_design(), effect=-0.5)


def _hic(kind):
    from sc_referee.checks.hic_loop_strength import HiCLoopStrengthCheck
    from tests.factories import hic_contact_bundle, make_hic_design

    bundle = hic_contact_bundle(report_delta=-1.0 if kind in {"mismatch_gap", "violation"} else None,
                                seed=89)
    design = make_hic_design(hic_loop_strength_confidence_high=kind == "violation")
    if kind == "agreement_gap":
        design = make_hic_design(confirmed=False)
    return HiCLoopStrengthCheck().run(design, bundle, bundle.reported_results)


def _strong_abstention():
    from sc_referee.checks.confounding_strong import ConfoundingStrongCheck
    from tests.factories import pseudobulk_confounding_bundle
    from tests.test_confounding_strong import _strong_design

    bundle = pseudobulk_confounding_bundle()
    return ConfoundingStrongCheck().run(
        _strong_design(adjusted=["condition"], operator="random_intercept_only"), bundle
    )


def _stage1_abstention():
    from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck
    from tests.factories import pseudobulk_confounding_bundle, random_intercept_design

    bundle = pseudobulk_confounding_bundle()
    return ConfoundingRandomInterceptCheck().run(
        random_intercept_design(bundle, adjusted=["condition"]), bundle
    )


def _stage2_abstention():
    from sc_referee.checks.confounding_random_intercept_conditional import (
        ConfoundingRandomInterceptConditionalCheck,
    )
    from tests.test_confounding_random_intercept_conditional import _material_case

    design, bundle = _material_case(ratified=False)
    return ConfoundingRandomInterceptConditionalCheck().run(design, bundle)


def _experimental_abstention():
    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck

    bundle = paired_count_bundle(n_donors=4)
    return ExperimentalUnitCheck(engine="simple").run(make_design(), bundle, None)


def _count_model_abstention():
    from sc_referee.checks.count_model import CountModelCheck

    bundle = paired_count_bundle(n_donors=4)
    return CountModelCheck(engine="simple").run(make_design(unit_of_test="sample"), bundle, None)


def _live_double_dipping_abstention():
    from tests.inference.test_computed_double_dipping_live import PBMC_DEX_SOURCE, _run

    source = PBMC_DEX_SOURCE.replace("adata.obsm['X_pca']", "adata.raw.X").replace(
        "method='wilcoxon'", "method='wilcoxon', use_raw=False"
    )
    return _run(source, confirmed=True)


def _contamination(kind):
    from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
    from sc_referee.csp import CspFieldState
    from tests.contamination_factories import contamination_case

    if kind == "missing":
        design, bundle = contamination_case(ratified=False)
    elif kind == "contained":
        design, bundle = contamination_case(
            adjusted=("condition", "rho_external"), ratified=True
        )
    elif kind == "noncontained":
        design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    elif kind == "unbindable":
        design, bundle = contamination_case(ratified=True, operator_kind="random_intercept_only")
    elif kind == "ambiguous":
        design, bundle = contamination_case(ratified=True, rho_values=[0.] * 8)
    else:
        design, bundle = contamination_case(ratified=True)
        record = design.csp_contracts[0]
        if kind == "benign":
            field = replace(
                record.fields["required_adjustment"],
                state=CspFieldState.DECLINED_FOR_CONSUMER, confidence="low", value=None,
            )
            record = replace(record, fields={**record.fields, "required_adjustment": field})
        elif kind == "stale":
            record = replace(record, component_identities={
                **record.component_identities,
                "causal_contract_identity": "sha256:" + "0" * 64,
            })
        elif kind == "outside":
            design = replace(design, analysis_type="marker_detection")
        design = replace(design, csp_contracts=(record,))
    return ContaminationConfoundCheck().run(design, bundle)


def finding_cases() -> list[FindingCase]:
    specs = [
        ("confounding.alias_unconfirmed", "confounding", lambda: _confounding("alias_unconfirmed"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("confounding.adjusted_vif", "confounding", lambda: _confounding("near_adjusted"), (S.PASS, S.COMPLETE, S.APPLIES, S.CONFORMANT), "non_defect", S.CLEAR),
        ("confounding.omitted_material", "confounding", lambda: _confounding("partial_omitted"), (S.MAJOR, S.COMPLETE, S.APPLIES, S.CONCERN), "concern", S.FLAGGED),
        ("effect_size.policy_note", "effect_size_threshold", lambda: _effect([0.01] + [1.0] * 9, [1e-4] * 10), (S.INFORMATIONAL, S.COMPLETE, S.APPLIES, None), "non_defect", S.CLEAR),
        ("effect_size.no_effect", "effect_size_threshold", lambda: _effect([np.nan], [1e-4]), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("multiple_testing.harmless", "multiple_testing", lambda: _multiple("harmless"), (S.INFORMATIONAL, S.COMPLETE, S.APPLIES, None), "non_defect", S.CLEAR),
        ("multiple_testing.unconfirmed", "multiple_testing", lambda: _multiple("unconfirmed"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("experimental_unit.no_report", "experimental_unit", _experimental_abstention, (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("count_model.no_report", "count_model", _count_model_abstention, (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("pairing.omitted", "pairing", lambda: _pairing("omitted"), (S.NEEDS_EVIDENCE, S.COMPLETE, S.APPLIES, S.CONCERN), "concern", S.FLAGGED),
        ("pairing.partial", "pairing", lambda: _pairing("partial"), (S.INFORMATIONAL, S.COMPLETE, S.APPLIES, None), "non_defect", S.CLEAR),
        ("pairing.unentitled_duplicate", "pairing", lambda: _pairing("duplicate_gap"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("double_dipping.descriptive", "double_dipping", lambda: _double("descriptive"), (S.INFORMATIONAL, S.COMPLETE, S.APPLIES, None), "non_defect", S.CLEAR),
        ("double_dipping.safeguard", "double_dipping", lambda: _double("safeguard"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("double_dipping.live_independent", "double_dipping", _live_double_dipping_abstention, (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("pseudobulk.final_x", "pseudobulk_integrity", lambda: _pseudobulk("scale"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("pseudobulk.unconfirmed_merge", "pseudobulk_integrity", lambda: _pseudobulk("merge"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("allele.agreement_gap", "allele_orientation", lambda: _allele("agreement_gap"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("allele.mismatch_gap", "allele_orientation", lambda: _allele("mismatch_gap"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("allele.entitled_mismatch", "allele_orientation", lambda: _allele("violation"), (S.BLOCKER, S.COMPLETE, S.APPLIES, S.VIOLATION), "violation", S.FLAGGED),
        ("hic.agreement_gap", "hic_loop_strength", lambda: _hic("agreement_gap"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("hic.mismatch_gap", "hic_loop_strength", lambda: _hic("mismatch_gap"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("hic.entitled_mismatch", "hic_loop_strength", lambda: _hic("violation"), (S.BLOCKER, S.COMPLETE, S.APPLIES, S.VIOLATION), "violation", S.FLAGGED),
        ("confounding_strong.explicit_abstention", "confounding_strong", _strong_abstention, (S.NOT_AUDITED, S.NOT_RUN, S.APPLIES, None), "abstention", S.NOT_CHECKED),
        ("confounding_stage1.explicit_abstention", "confounding_random_intercept", _stage1_abstention, (S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, None), "abstention", S.NOT_CHECKED),
        ("confounding_stage2.explicit_abstention", "confounding_random_intercept_conditional", _stage2_abstention, (S.NOT_AUDITED, S.NOT_RUN, S.UNKNOWN, None), "abstention", S.NOT_CHECKED),
        ("contamination_confound.outside_scope", "contamination_confound", lambda: _contamination("outside"), (S.NOT_AUDITED, S.NOT_RUN, S.NOT_APPLICABLE, S.UNRESOLVED), "n_a", S.N_A),
        ("contamination_confound.missing_premise", "contamination_confound", lambda: _contamination("missing"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, S.UNRESOLVED), "abstention", S.NOT_CHECKED),
        ("contamination_confound.benign_refutation", "contamination_confound", lambda: _contamination("benign"), (S.NOT_AUDITED, S.NOT_RUN, S.UNKNOWN, S.UNRESOLVED), "abstention", S.NOT_CHECKED),
        ("contamination_confound.unbindable_fit", "contamination_confound", lambda: _contamination("unbindable"), (S.NOT_AUDITED, S.NOT_RUN, S.APPLIES, S.UNRESOLVED), "abstention", S.NOT_CHECKED),
        ("contamination_confound.ambiguous_geometry", "contamination_confound", lambda: _contamination("ambiguous"), (S.NOT_AUDITED, S.NOT_RUN, S.APPLIES, S.UNRESOLVED), "abstention", S.NOT_CHECKED),
        ("contamination_confound.stale_identity", "contamination_confound", lambda: _contamination("stale"), (S.NEEDS_EVIDENCE, S.NOT_RUN, S.UNKNOWN, S.UNRESOLVED), "abstention", S.NOT_CHECKED),
        ("contamination_confound.contained", "contamination_confound", lambda: _contamination("contained"), (S.PASS, S.COMPLETE, S.APPLIES, S.CONFORMANT), "non_defect", S.CLEAR),
        ("contamination_confound.noncontained", "contamination_confound", lambda: _contamination("noncontained"), (S.MAJOR, S.COMPLETE, S.APPLIES, S.VIOLATION), "violation", S.FLAGGED),
    ]
    return [_case(*spec) for spec in specs]


# Stable source identities are path + containing function + status + lexical ordinal. Adding a new
# literal emitter creates a new identity and fails the source guard until this classification is edited.
LITERAL_EMITTER_CLASSIFICATION = {
    **{f"contamination_confound.py:run:NEEDS_EVIDENCE:{i}": "abstention"
       for i in range(1, 6)},
    **{f"allele_orientation.py:evaluate_allele_orientation:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 5)},
    **{f"confounding.py:evaluate_confounding:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 10)},
    "confounding_random_intercept.py:run:NEEDS_EVIDENCE:1": "abstention",
    **{f"count_model.py:evaluate_count_model:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 8)},
    "double_dipping.py:evaluate_double_dipping:INFORMATIONAL:1": "non_defect",
    "double_dipping.py:evaluate_double_dipping:NEEDS_EVIDENCE:1": "abstention",
    "double_dipping.py:evaluate_double_dipping:NEEDS_EVIDENCE:2": "abstention",
    "double_dipping.py:evaluate_double_dipping:NEEDS_EVIDENCE:3": "concern",
    **{f"effect_size.py:evaluate_effect_size:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 6)},
    "effect_size.py:evaluate_effect_size:INFORMATIONAL:1": "non_defect",
    **{f"experimental_unit.py:evaluate_experimental_unit:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 4)},
    **{f"hic_loop_strength.py:evaluate_hic_loop_strength:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 6)},
    # Includes the raw- and adjusted-p-value domain gates. Invalid evidence is an abstention that
    # blocks certification, not a proved scientific violation.
    **{f"multiple_testing.py:evaluate_multiple_testing:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 10)},
    **{f"multiple_testing.py:evaluate_multiple_testing:INFORMATIONAL:{i}": "non_defect" for i in range(1, 3)},
    "pairing.py:evaluate_pairing:NEEDS_EVIDENCE:1": "abstention",
    "pairing.py:evaluate_pairing:NEEDS_EVIDENCE:2": "concern",
    "pairing.py:evaluate_pairing:NEEDS_EVIDENCE:3": "abstention",
    "pairing.py:evaluate_pairing:NEEDS_EVIDENCE:4": "abstention",
    "pairing.py:evaluate_pairing:NEEDS_EVIDENCE:5": "concern",
    "pairing.py:evaluate_pairing:NEEDS_EVIDENCE:6": "abstention",
    "pairing.py:evaluate_pairing:INFORMATIONAL:1": "non_defect",
    **{f"pseudobulk_integrity.py:_merge_finding:NEEDS_EVIDENCE:{i}": "abstention" for i in range(1, 4)},
    "pseudobulk_integrity.py:evaluate_pseudobulk_integrity:NEEDS_EVIDENCE:1": "concern",
    "pseudobulk_integrity.py:evaluate_pseudobulk_integrity:NEEDS_EVIDENCE:2": "abstention",
}
