"""Real-byte M1 compilation of the recovered GB-P07 contamination basis."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from sc_referee import statuses as S
from sc_referee.checks.base import ConditionalPremise
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations.contamination_compile import (
    ColumnBindings,
    DEFAULT_RELEASE_ZIP,
    compile_contamination,
    compile_contamination_tables,
    ratify_contamination,
    read_release,
)


# GB-P07's own declared analysis: which column carries which role, its ambient marker and
# panel, its target, and its method parameters. The engine assumes none of this, so the
# benchmark's tests declare the benchmark's.
GBP07_BINDINGS = ColumnBindings(
    cell_id="cell_id",
    cell_donor="donor",
    cell_total_umi="total_umi",
    cell_marker="HBB",
    donor_id="donor",
    donor_genotype="g",
    exposure_column="genotype",
    empty_total_umi="total_umi",
    empty_id_columns=("barcode",),
    empty_panel_columns=("HBB", "IFI6", "ISG15", "LST1", "CXCL10"),
    marker_gene="HBB",
    threshold=0.18,
    provenance=(
        "GeneBench-Pro problems/statgen_scrna_ambient_state_eqtl/"
        "report_public.pdf equations 18-23"
    ),
)
GBP07_METHOD = {
    "columns": GBP07_BINDINGS,
    "target_feature": "CXCL10",
    "target_coefficient": "genotype",
}

def _contamination_zip() -> Path:
    override = os.environ.get("GBP07_ZIP")
    return Path(override).expanduser() if override else DEFAULT_RELEASE_ZIP


pytestmark = pytest.mark.skipif(
    not _contamination_zip().exists(),
    reason="GB-P07 data not present — set GBP07_ZIP; see bench/gbp07_anchor.py",
)


def _explicit_yes_answers():
    return {
        CondensedGroup.MEASUREMENT: CondensedAnswer.YES,
        CondensedGroup.TIMING: CondensedAnswer.YES,
        CondensedGroup.ESTIMAND: CondensedAnswer.YES,
        CondensedGroup.AUTHORITY: CondensedAnswer.YES,
    }


def _finding(*, include_basis=False, answers=None):
    compilation = compile_contamination(_contamination_zip(), **GBP07_METHOD, include_basis=include_basis)
    design = ratify_contamination(
        compilation, _explicit_yes_answers() if answers is None else answers
    )
    finding = ContaminationConfoundCheck().run(
        design, compilation.bundle
    )
    return compilation, design, finding


def _basis_digest(design) -> str:
    record = design.csp_contracts[0]
    return record.fields["basis_identity"].value["output_digest"]


def test_real_omitted_basis_is_conditional_major():
    compilation, _, finding = _finding(include_basis=False)

    assert len(compilation.bundle.observations) == 588
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.MAJOR, S.COMPLETE, S.FLAGGED,
    )
    assert finding.metrics["column_space_state"] == "not_certified"
    assert finding.metrics["excluded_exposure_columns"] == ["genotype"]
    assert isinstance(finding.conditional_on, ConditionalPremise)


def test_real_included_basis_is_conditional_pass():
    _, _, finding = _finding(include_basis=True)

    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.PASS, S.COMPLETE, S.CLEAR,
    )
    assert finding.metrics["column_space_state"] == "certified"
    assert finding.metrics["excluded_exposure_columns"] == ["genotype"]
    assert isinstance(finding.conditional_on, ConditionalPremise)


def test_proposal_only_compile_never_reaches_column_space_geometry():
    compilation = compile_contamination(_contamination_zip(), **GBP07_METHOD, include_basis=False)
    assert compilation.design.csp_contracts == ()
    assert compilation.proposal_values
    assert compilation.scope
    with patch(
        "sc_referee.checks.contamination_confound.certify_column_space",
        side_effect=AssertionError("geometry unreachable"),
    ):
        finding = ContaminationConfoundCheck().run(
            compilation.design, compilation.bundle
        )

    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )
    assert finding.conditional_on is None


@pytest.mark.parametrize("answer", (CondensedAnswer.NO, CondensedAnswer.NOT_SURE))
def test_explicit_non_yes_answer_remains_not_checked(answer):
    answers = _explicit_yes_answers()
    answers[CondensedGroup.MEASUREMENT] = answer
    compilation, _, finding = _finding(include_basis=False, answers=answers)

    assert compilation.design.csp_contracts == ()
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )


def test_source_poison_cannot_change_recovered_basis_or_containment_identities():
    cells, donors, empty_drops = read_release(_contamination_zip())
    baseline = compile_contamination_tables(cells, donors, empty_drops, **GBP07_METHOD)
    baseline_design = ratify_contamination(baseline, _explicit_yes_answers())
    baseline_finding = ContaminationConfoundCheck().run(
        baseline_design, baseline.bundle
    )

    poisoned_cells = cells.copy()
    poisoned_donors = donors.copy()
    poisoned_donors["g"] = 2 - poisoned_donors["g"]
    poisoned_cells["fake_submitted_effect"] = np.linspace(
        -1e12, 1e12, len(poisoned_cells)
    )
    poisoned_cells["fake_reference_answer"] = "deliberately-wrong"
    poisoned = compile_contamination_tables(poisoned_cells, poisoned_donors, empty_drops, **GBP07_METHOD)
    poisoned_design = ratify_contamination(poisoned, _explicit_yes_answers())
    poisoned_finding = ContaminationConfoundCheck().run(
        poisoned_design, poisoned.bundle
    )

    assert poisoned.artifact.artifact_identity.encode("ascii") == (
        baseline.artifact.artifact_identity.encode("ascii")
    )
    for metric in ("row_ledger_identity", "fitted_design_identity"):
        assert poisoned_finding.metrics[metric].encode("ascii") == (
            baseline_finding.metrics[metric].encode("ascii")
        )
    assert _basis_digest(poisoned_design).encode("ascii") == _basis_digest(baseline_design).encode(
        "ascii"
    )


def test_archive_compilation_binds_exact_source_bytes_and_member_set():
    first = compile_contamination(_contamination_zip(), **GBP07_METHOD)
    second = compile_contamination(_contamination_zip(), **GBP07_METHOD)

    assert set(first.source_digests) == {
        "digest_policy_version", "cells", "donors", "empty_drops",
        "archive_members", "archive_member_set"
    }
    assert first.source_digests == second.source_digests
    assert all(
        first.source_digests[name].startswith("sha256:")
        for name in ("cells", "donors", "empty_drops", "archive_member_set")
    )
    assert {"cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz"}.issubset(
        first.source_digests["archive_members"]
    )


def test_real_donor_geometry_matches_the_companion_plan():
    cells, donors, empty_drops = read_release(_contamination_zip())
    compilation = compile_contamination_tables(cells, donors, empty_drops, **GBP07_METHOD)
    artifact = compilation.artifact

    assert len(artifact.donor_table) == 24
    high = np.asarray(
        [float(row.high_contamination) for row in artifact.donor_table],
        dtype=np.float64,
    )
    assert int(high.sum()) == 12
    assert int(len(high) - high.sum()) == 12

    genotype_by_donor = donors.assign(donor=donors["donor"].astype(str)).set_index(
        "donor"
    )["g"]
    genotype = np.asarray(
        [genotype_by_donor.loc[row.fitted_unit_id.value] for row in artifact.donor_table],
        dtype=np.float64,
    )
    submitted = np.column_stack([np.ones(len(genotype)), genotype])
    included = np.column_stack([submitted, high])
    submitted_rank = int(np.linalg.matrix_rank(submitted))
    included_rank = int(np.linalg.matrix_rank(included))
    assert submitted_rank == 2
    assert included_rank == 3
    assert included_rank - submitted_rank == 1

    fitted = submitted @ np.linalg.lstsq(submitted, high, rcond=None)[0]
    residual = high - fitted
    residual_norm = float(np.linalg.norm(residual))
    r_squared = float(1.0 - residual @ residual / ((high - high.mean()) @ (high - high.mean())))
    assert residual_norm == pytest.approx(np.sqrt(2.0), rel=0.0, abs=1e-12)
    assert r_squared == pytest.approx(2.0 / 3.0, rel=0.0, abs=1e-12)

    assignments = {
        dosage: (
            int(np.sum(high[genotype == dosage] == 0)),
            int(np.sum(high[genotype == dosage] == 1)),
        )
        for dosage in (0, 1, 2)
    }
    assert assignments == {0: (8, 0), 1: (4, 4), 2: (0, 8)}
