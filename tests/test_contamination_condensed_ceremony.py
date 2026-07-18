"""The four-answer contamination ceremony is the sole GB-P07 ratification gate."""
from __future__ import annotations

from dataclasses import replace
import inspect
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from sc_referee import statuses as S
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.csp import (
    CspAbstention,
    CspFieldState,
    CspReadRequest,
    RatifiedFactSet,
    read_ratified_contract,
)
from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
    CONTRACT_TYPE, MANIFEST, REQUIRED_FIELDS,
)
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAbstention,
    CondensedAnswer,
    CondensedGroup,
    ratify_contamination_condensed,
)
from sc_referee.derivations import contamination_compile
from sc_referee.derivations.contamination_compile import (
    ColumnBindings,
    DEFAULT_RELEASE_ZIP,
    compile_contamination,
    ratify_contamination,
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
    not _contamination_zip().exists(), reason="GB-P07 data not present — set GBP07_ZIP"
)


@pytest.fixture(scope="module")
def compiled_pair():
    return (
        compile_contamination(_contamination_zip(), **GBP07_METHOD, include_basis=False),
        compile_contamination(_contamination_zip(), **GBP07_METHOD, include_basis=True),
    )


def _proposal(compilation):
    return compilation.proposal_values, compilation.scope


def _read(record):
    return read_ratified_contract(
        (record,),
        CspReadRequest(CONTRACT_TYPE, record.scope, REQUIRED_FIELDS, MANIFEST.authorized_consumer),
    )


def _answers(changed_group=None, changed_answer=CondensedAnswer.YES):
    result = {group: CondensedAnswer.YES for group in CondensedGroup}
    if changed_group is not None:
        result[changed_group] = changed_answer
    return result


def test_all_four_yes_authorize_and_drive_conditional_major_and_pass(compiled_pair):
    omitted, included = compiled_pair
    for compilation, expected in ((omitted, S.MAJOR), (included, S.PASS)):
        translated_design = ratify_contamination(compilation, _answers())
        translated = translated_design.csp_contracts[0]
        assert isinstance(_read(translated), RatifiedFactSet)
        finding = ContaminationConfoundCheck().run(
            translated_design, compilation.bundle
        )
        assert (finding.status, finding.coverage) == (expected, S.COMPLETE)


@pytest.mark.parametrize("group", tuple(CondensedGroup))
@pytest.mark.parametrize("answer", (CondensedAnswer.NO, CondensedAnswer.NOT_SURE))
def test_each_single_non_yes_abstains_and_geometry_is_unreachable(
    compiled_pair, group, answer
):
    compilation = compiled_pair[0]
    values, scope = _proposal(compilation)
    translated = ratify_contamination_condensed(
        values, scope, _answers(group, answer)
    )
    assert isinstance(translated, CondensedAbstention)
    assert isinstance(_read(translated), CspAbstention)
    design = replace(compilation.design, csp_contracts=(translated,))
    with patch(
        "sc_referee.checks.contamination_confound.certify_column_space",
        side_effect=AssertionError("geometry unreachable"),
    ):
        finding = ContaminationConfoundCheck().run(design, compilation.bundle)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED,
    )


def test_missing_answers_default_to_not_sure(compiled_pair):
    values, scope = _proposal(compiled_pair[0])
    translated = ratify_contamination_condensed(values, scope, {})
    assert isinstance(translated, CondensedAbstention)
    assert isinstance(_read(translated), CspAbstention)


def test_all_yes_preserves_values_and_adversarial_validation(compiled_pair):
    values, scope = _proposal(compiled_pair[0])
    translated = ratify_contamination_condensed(values, scope, _answers())
    assert MANIFEST.validate_values(values) == ()
    assert {field: translated.fields[field].value for field in REQUIRED_FIELDS} == values

    invalid = dict(values)
    invalid["required_adjustment"] = {
        "required": True, "basis": "association", "evidence_id": "evidence:bad:v1",
    }
    with pytest.raises(ValueError, match="design_based_adjustment_reason_missing"):
        ratify_contamination_condensed(invalid, scope, _answers())


def test_compiler_defaults_to_unratified_and_explicit_path_is_conditional(compiled_pair):
    compilation = compile_contamination(_contamination_zip(), **GBP07_METHOD, include_basis=False)
    assert compilation.design.csp_contracts == ()
    with patch(
        "sc_referee.checks.contamination_confound.certify_column_space",
        side_effect=AssertionError("geometry unreachable"),
    ):
        finding = ContaminationConfoundCheck().run(compilation.design, compilation.bundle)
    assert (finding.status, finding.coverage) == (S.NEEDS_EVIDENCE, S.NOT_RUN)

    explicit_design = ratify_contamination(compiled_pair[0], _answers())
    explicit = ContaminationConfoundCheck().run(explicit_design, compiled_pair[0].bundle)
    assert (explicit.status, explicit.coverage) == (S.MAJOR, S.COMPLETE)


def test_compiler_contains_no_direct_confirmed_high_constructor():
    source = inspect.getsource(contamination_compile)
    assert "CspFieldRecord(" not in source
    assert "CspFieldState.CONFIRMED_HIGH" not in source
    assert "ratify_contamination_condensed(" in source
    assert "CondensedAnswer.YES" not in source
    assert "ratified=" not in source


def test_condensed_abstention_cannot_attest_authority(compiled_pair):
    values, scope = _proposal(compiled_pair[0])
    abstention = ratify_contamination_condensed(
        values, scope, {CondensedGroup.AUTHORITY: CondensedAnswer.NO}
    )
    assert isinstance(abstention, CondensedAbstention)
    with pytest.raises(ValueError, match="cannot attest authority"):
        replace(abstention, authority_attested=True)

    field_id = next(iter(abstention.fields))
    fields = dict(abstention.fields)
    fields[field_id] = replace(fields[field_id], state=CspFieldState.CONFIRMED_HIGH)
    with pytest.raises(ValueError, match="cannot contain confirmed fields"):
        replace(abstention, fields=fields)
