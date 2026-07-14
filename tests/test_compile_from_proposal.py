"""Proposal-driven compilation of the registered GB-P07 derivation."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.compiler.binding_proposal import (
    BindingProposal,
    Destination,
    Evidence,
    Locator,
    RequestedBinding,
)
from sc_referee.compiler.table_bindings import TableBinding, parse_table_binding
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations.gbp07_compile import (
    CompilationAbstentionReason,
    Gbp07Compilation,
    ProposalCompilationAbstention,
    compile_from_proposal,
    compile_gbp07_tables,
    _table_source_digests,
)
from sc_referee.derivations.genebench_gbp07_public_estimator import (
    CellCountsView,
    EmptyDropletCountsView,
)


DERIVATION_ID = "genebench_gbp07_public_estimator/v1"
GBP07_ZIP = Path(os.environ.get(
    "GBP07_ZIP", "~/Desktop/genebench_phase1_inputs/GB-P07-data.zip"
)).expanduser()


def _digest(char: str) -> str:
    return "sha256:" + char * 64


def _answers(value=CondensedAnswer.YES):
    return {group: value for group in CondensedGroup}


def _evidence(path: str, column: str = "binding") -> tuple[Evidence, ...]:
    return (Evidence(
        artifact_identity=_digest("b"),
        path=path,
        locator=Locator("header", column),
        evidence_digest=_digest("c"),
    ),)


def _proposal(
    *,
    cell_donor="donor",
    donor_id="donor",
    genotype="g",
    method="CXCL10 ~ genotype; no ambient adjustment",
    derivation_id=DERIVATION_ID,
) -> BindingProposal:
    values = (
        ("design", "analysis_type", "eqtl", "method.txt"),
        ("detector_input", "cell_table", {
            "artifact_path": "cells.csv.gz",
            "columns": {
                "cell_id": "cell_id", "donor": cell_donor,
                "total_umi": "total_umi", "hbb": "HBB",
            },
        }, "cells.csv.gz"),
        ("detector_input", "donor_table", {
            "artifact_path": "donors.csv.gz",
            "columns": {"donor": donor_id, "genotype": genotype},
        }, "donors.csv.gz"),
        ("empty_droplet", "empty_droplet_table", {
            "artifact_path": "empty_drops.csv.gz",
            "columns": {
                "total_umi": "total_umi",
                "panel": {gene: gene for gene in ("HBB", "IFI6", "ISG15", "LST1", "CXCL10")},
            },
        }, "empty_drops.csv.gz"),
        ("design", "genotype_column", genotype, "donors.csv.gz"),
        ("design", "target_feature", "CXCL10", "submission.csv"),
        ("reported_claim", "submitted_result_artifact", "submission.csv", "submission.csv"),
        ("reported_claim", "target_coefficient", "+0.4839", "submission.csv"),
        ("fitted_design", "method_evidence_span", method, "method.txt"),
        ("detector_input", "derivation_id", derivation_id, "method.txt"),
    )
    bindings = tuple(RequestedBinding(
        binding_id=f"binding-{index}",
        destination=Destination(authority, field),
        candidate_value=value,
        confidence="high",
        evidence=_evidence(path),
    ) for index, (authority, field, value, path) in enumerate(values))
    return BindingProposal(
        schema_id="sc-referee/compiler-binding-proposal/v1",
        proposal_id=_digest("a"),
        revision=2,
        inventory_identity=_digest("d"),
        confirmed_organizational_bindings=True,
        requested_bindings=bindings,
    )


def _with_empty_columns(
    proposal: BindingProposal, columns: dict[str, object]
) -> BindingProposal:
    bindings = tuple(
        replace(
            binding,
            candidate_value={
                "artifact_path": binding.candidate_value["artifact_path"],
                "columns": columns,
            },
        )
        if binding.destination.field == "empty_droplet_table"
        else binding
        for binding in proposal.requested_bindings
    )
    return replace(proposal, requested_bindings=bindings)


def _unpack_real_folder(folder: Path) -> None:
    with ZipFile(GBP07_ZIP) as archive:
        for member in ("cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz"):
            (folder / member).write_bytes(archive.read(member))
    pd.DataFrame({"feature": ["CXCL10"], "coefficient": [0.4839]}).to_csv(
        folder / "submission.csv", index=False
    )
    (folder / "method.txt").write_text(
        "CXCL10 ~ genotype; no ambient adjustment", encoding="utf-8"
    )


@pytest.mark.skipif(not GBP07_ZIP.exists(), reason="GB-P07 data not present — set GBP07_ZIP")
@pytest.mark.parametrize("included, expected", [(False, S.MAJOR), (True, S.PASS)])
def test_real_proposal_compiles_to_same_conditional_verdict(tmp_path, included, expected):
    _unpack_real_folder(tmp_path)
    method = (
        "CXCL10 ~ genotype + high_contamination; ambient adjustment included"
        if included else "CXCL10 ~ genotype; no ambient adjustment"
    )

    result = compile_from_proposal(_proposal(method=method), tmp_path, _answers())

    assert isinstance(result, Gbp07Compilation)
    assert result.proposal_identity == _digest("a")
    assert result.finding.status == expected
    assert result.finding.metrics["column_space_state"] == (
        "certified" if included else "not_certified"
    )
    assert result.finding.conditional_on is not None
    assert set(result.source_digests) == {
        "digest_policy_version", "cell_table", "donor_table",
        "empty_droplet_table", "artifact_paths"
    }


@pytest.mark.skipif(not GBP07_ZIP.exists(), reason="GB-P07 data not present — set GBP07_ZIP")
def test_real_proposal_without_enumerated_empty_panel_compiles_to_major(tmp_path):
    _unpack_real_folder(tmp_path)
    proposal = _with_empty_columns(
        _proposal(), {"total_umi": "total_umi", "marker": "HBB"}
    )

    result = compile_from_proposal(proposal, tmp_path, _answers())

    assert isinstance(result, Gbp07Compilation)
    assert result.finding.status == S.MAJOR


@pytest.mark.skipif(not GBP07_ZIP.exists(), reason="GB-P07 data not present — set GBP07_ZIP")
def test_non_yes_answer_never_becomes_a_verdict(tmp_path):
    _unpack_real_folder(tmp_path)
    answers = _answers()
    answers[CondensedGroup.MEASUREMENT] = CondensedAnswer.NO

    result = compile_from_proposal(_proposal(), tmp_path, answers)

    assert isinstance(result, Gbp07Compilation)
    assert (result.finding.status, result.finding.coverage, S.human_state(result.finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )


def _write_synthetic(folder: Path) -> None:
    panel = ("HBB", "IFI6", "ISG15", "LST1", "CXCL10")
    cells = pd.DataFrame({
        "cell_id": ["c1", "c2", "c3", "c4"],
        "subject": ["s1", "s2", "s3", "s4"],
        "total_umi": [100, 100, 100, 100],
        "HBB": [1, 3, 1, 3],
        "IFI6": [0, 0, 0, 0], "ISG15": [0, 0, 0, 0],
        "LST1": [0, 0, 0, 0], "CXCL10": [1, 1, 1, 1],
    })
    donors = pd.DataFrame({"subject": ["s1", "s2", "s3", "s4"], "dose": [0, 0, 1, 1]})
    empty = pd.DataFrame({
        "total_umi": [100], "HBB": [10], "IFI6": [0], "ISG15": [0],
        "LST1": [0], "CXCL10": [0],
    })
    cells.to_csv(folder / "cells.csv.gz", index=False, compression="gzip")
    donors.to_csv(folder / "donors.csv.gz", index=False, compression="gzip")
    empty.to_csv(folder / "empty_drops.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"coefficient": [0.4839]}).to_csv(folder / "submission.csv", index=False)
    (folder / "method.txt").write_text("no ambient adjustment", encoding="utf-8")
    assert set(panel).issubset(cells.columns)


def test_synthetic_renamed_columns_reach_same_detector_without_aliases(tmp_path):
    _write_synthetic(tmp_path)

    result = compile_from_proposal(
        _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
        tmp_path,
        _answers(),
    )

    assert isinstance(result, Gbp07Compilation)
    assert result.design.genotype_column == "dose"
    assert result.design.replicate_unit == ["subject"]
    assert {"subject", "dose", "high_contamination"}.issubset(result.bundle.observations)
    assert result.finding.status == S.MAJOR
    assert result.finding.metrics["excluded_exposure_columns"] == ["dose"]


def test_donor_authority_order_is_reindexed_to_fitted_row_order(tmp_path):
    _write_synthetic(tmp_path)
    proposal = _proposal(cell_donor="subject", donor_id="subject", genotype="dose")
    aligned = compile_from_proposal(proposal, tmp_path, _answers())
    donors_path = tmp_path / "donors.csv.gz"
    donors = pd.read_csv(donors_path).iloc[::-1].reset_index(drop=True)
    donors.to_csv(donors_path, index=False, compression="gzip")

    reordered = compile_from_proposal(proposal, tmp_path, _answers())

    assert isinstance(aligned, Gbp07Compilation)
    assert isinstance(reordered, Gbp07Compilation)
    assert aligned.finding.status == reordered.finding.status == S.MAJOR
    assert (
        aligned.scope.contract_scope["basis_output_digest"]
        == reordered.scope.contract_scope["basis_output_digest"]
    )


def test_estimator_fitted_donor_set_mismatch_is_typed_abstention(tmp_path):
    _write_synthetic(tmp_path)
    from sc_referee.derivations import gbp07_compile as module

    original = module.estimate_genebench_gbp07_public_contamination

    def missing_basis_row(*args, **kwargs):
        result = original(*args, **kwargs)
        assert isinstance(result, module.Estimated)
        artifact = replace(
            result.artifact, donor_table=result.artifact.donor_table[:-1]
        )
        return module.Estimated(artifact)

    with patch.object(
        module, "estimate_genebench_gbp07_public_contamination", missing_basis_row
    ):
        result = compile_from_proposal(
            _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
            tmp_path,
            _answers(),
        )

    assert isinstance(result, ProposalCompilationAbstention)
    assert result.reason_code is CompilationAbstentionReason.BASIS_LEDGER_MISMATCH
    assert "missing=['s4']" in result.message


def test_in_memory_source_digest_uses_canonical_typed_encoding():
    cells = pd.DataFrame({"id": ["a", "b"], "value": [0.0, 1.25]})
    same = cells.copy()
    same.index = pd.Index([10, 20])
    same.loc[0 if 0 in same.index else 10, "value"] = -0.0
    donors = pd.DataFrame({"donor": [1, 2]})
    empty = pd.DataFrame({"count": [3, 4]})

    first = _table_source_digests(cells, donors, empty)
    second = _table_source_digests(same, donors.copy(), empty.copy())
    changed_cells = cells.copy()
    changed_cells.loc[1, "value"] = 1.5
    changed = _table_source_digests(changed_cells, donors, empty)

    assert first["digest_policy_version"] == "gbp07-source-digest-v2"
    assert first == second
    assert first["cells"] != changed["cells"]


@pytest.mark.parametrize("bad_value", [-1, 1.5, None])
def test_invalid_original_cell_count_values_have_typed_abstention(tmp_path, bad_value):
    _write_synthetic(tmp_path)
    cell_path = tmp_path / "cells.csv.gz"
    cells = pd.read_csv(cell_path)
    cells["HBB"] = cells["HBB"].astype(float)
    cells.loc[0, "HBB"] = bad_value
    cells.to_csv(cell_path, index=False, compression="gzip")

    result = compile_from_proposal(
        _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
        tmp_path,
        _answers(),
    )

    assert isinstance(result, ProposalCompilationAbstention)
    assert result.reason_code is CompilationAbstentionReason.INVALID_SOURCE_VALUES
    assert "HBB" in result.message


def test_feature_count_above_int64_range_has_typed_abstention(tmp_path):
    _write_synthetic(tmp_path)
    cell_path = tmp_path / "cells.csv.gz"
    cells = pd.read_csv(cell_path)
    cells["overflow_feature"] = pd.Series(
        [2**63, 0, 0, 0], dtype="uint64"
    )
    cells.to_csv(cell_path, index=False, compression="gzip")

    result = compile_from_proposal(
        _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
        tmp_path,
        _answers(),
    )

    assert isinstance(result, ProposalCompilationAbstention)
    assert result.reason_code is CompilationAbstentionReason.INVALID_SOURCE_VALUES
    assert "overflow_feature" in result.message


def test_direct_table_compile_returns_typed_source_value_abstention(tmp_path):
    _write_synthetic(tmp_path)
    cells = pd.read_csv(tmp_path / "cells.csv.gz").rename(columns={"subject": "donor"})
    donors = pd.read_csv(tmp_path / "donors.csv.gz").rename(
        columns={"subject": "donor", "dose": "g"}
    )
    empty = pd.read_csv(tmp_path / "empty_drops.csv.gz")
    empty.loc[0, "total_umi"] = -1

    result = compile_gbp07_tables(cells, donors, empty)

    assert isinstance(result, ProposalCompilationAbstention)
    assert result.reason_code is CompilationAbstentionReason.INVALID_SOURCE_VALUES
    assert result.proposal_identity is None
    assert "total_umi" in result.message


@pytest.mark.parametrize(
    ("table_name", "column"),
    [("cells.csv.gz", "cell_id"), ("cells.csv.gz", "subject"),
     ("donors.csv.gz", "subject")],
)
def test_null_original_identity_has_typed_abstention(tmp_path, table_name, column):
    _write_synthetic(tmp_path)
    table_path = tmp_path / table_name
    frame = pd.read_csv(table_path)
    frame.loc[0, column] = None
    frame.to_csv(table_path, index=False, compression="gzip")

    result = compile_from_proposal(
        _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
        tmp_path,
        _answers(),
    )

    assert isinstance(result, ProposalCompilationAbstention)
    assert result.reason_code is CompilationAbstentionReason.MISSING_SOURCE_ID
    assert column in result.message
    assert "'nan'" not in result.message
    assert "'None'" not in result.message


def test_empty_table_missing_bound_marker_has_typed_abstention(tmp_path):
    _write_synthetic(tmp_path)
    empty_path = tmp_path / "empty_drops.csv.gz"
    empty = pd.read_csv(empty_path).drop(columns="HBB")
    empty.to_csv(empty_path, index=False, compression="gzip")

    result = compile_from_proposal(_proposal(), tmp_path, _answers())

    assert isinstance(result, ProposalCompilationAbstention)
    assert (
        result.reason_code
        is CompilationAbstentionReason.EMPTY_DROPLET_TABLE_MISSING_MARKER
    )
    assert "required marker column 'HBB'" in result.message


def test_advisory_panel_may_omit_marker_when_data_contains_it(tmp_path):
    _write_synthetic(tmp_path)
    proposal = _with_empty_columns(
        _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
        {
            "total_umi": "total_umi",
            "panel": {
                gene: gene for gene in ("IFI6", "ISG15", "LST1", "CXCL10")
            },
        },
    )

    result = compile_from_proposal(proposal, tmp_path, _answers())

    assert isinstance(result, Gbp07Compilation)
    assert result.finding.status == S.MAJOR


@pytest.mark.parametrize("field", ["cell_table", "donor_table", "empty_droplet_table"])
def test_all_table_destinations_parse_through_shared_helper(field):
    binding = next(item for item in _proposal().requested_bindings if item.destination.field == field)

    parsed = parse_table_binding(binding.candidate_value, field)

    assert isinstance(parsed, TableBinding)
    assert parsed.artifact_path.endswith(".csv.gz")
    assert parsed.columns


def test_unknown_derivation_and_unresolved_proposal_abstain(tmp_path):
    unknown = compile_from_proposal(
        _proposal(derivation_id="not-registered/v1"), tmp_path, _answers()
    )
    unresolved_proposal = replace(
        _proposal(), confirmed_organizational_bindings=False,
        unresolved=("design.genotype_column",),
    )
    unresolved = compile_from_proposal(unresolved_proposal, tmp_path, _answers())

    assert isinstance(unknown, ProposalCompilationAbstention)
    assert unknown.reason_code is CompilationAbstentionReason.UNKNOWN_DERIVATION
    assert isinstance(unresolved, ProposalCompilationAbstention)
    assert unresolved.reason_code is CompilationAbstentionReason.UNRESOLVED_PROPOSAL


def test_estimator_receives_only_closed_views_through_proposal_path(tmp_path):
    _write_synthetic(tmp_path)
    from sc_referee.derivations import gbp07_compile as module

    original = module.estimate_genebench_gbp07_public_contamination

    def guarded(empty_view, cell_view, donor_order):
        assert isinstance(empty_view, EmptyDropletCountsView)
        assert isinstance(cell_view, CellCountsView)
        assert not hasattr(empty_view, "genotype")
        assert not hasattr(cell_view, "genotype")
        assert not hasattr(cell_view, "submitted_result")
        assert not hasattr(cell_view, "reference")
        return original(empty_view, cell_view, donor_order)

    with patch.object(module, "estimate_genebench_gbp07_public_contamination", guarded):
        result = compile_from_proposal(
            _proposal(cell_donor="subject", donor_id="subject", genotype="dose"),
            tmp_path,
            _answers(),
        )

    assert isinstance(result, Gbp07Compilation)
