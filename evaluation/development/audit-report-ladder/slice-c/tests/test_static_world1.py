from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import H5AD_PATH, SOURCE_PATH, StaticWorld1Case
from sc_referee_evaluation.audit_ladder.slice_c.composition import compose_world1_v1
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    GroupSizeV1,
    ObsGroupSizesFactV1,
    SliceCContractError,
    SliceCRequestV1,
    WorkerControllerResultV1,
)
from sc_referee_evaluation.audit_ladder.slice_c.observations import (
    build_observations_v1,
    validate_observations_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.renderer import (
    SliceCRendererError,
    render_world1_report_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.source import (
    SourceVerificationError,
    verify_world1_source_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.transaction import render_slice_c_report_v1


def _hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def test_exact_fixture_observations_appendix_and_report(
    static_world1_case: StaticWorld1Case,
) -> None:
    case = static_world1_case
    assert (len(SOURCE_PATH.read_bytes()), _hex(SOURCE_PATH.read_bytes())) == (
        1_015,
        "c5f3bb51457ace3e4b979b69739f212b9d0c7a12baba62033859d31f5b2ade18",
    )
    assert (len(H5AD_PATH.read_bytes()), _hex(H5AD_PATH.read_bytes())) == (
        330_008,
        "f94ddd1bc2c7d1d690d5c054caf924a2c531a0e7d191da9ca7a7b786fee0e887",
    )
    assert case.request_digest == (
        "sha256:f99eeb5740c53cf66e701cf06be40ad041c854f7f610f0bba7c90362dcf19f3b"
    )
    assert [item.observation_id for item in case.observations] == [
        "obs:1d6a83a034d0d3b0705b",
        "obs:232ffa8bb5506c13888e",
        "obs:08dd62bb5effa4255b37",
        "obs:761e7b80857df5fde69a",
        "obs:56249cd61506b8fb3f02",
    ]
    rendered = render_world1_report_v1(
        registry=case.registry,
        materials=case.materials,
        request_digest=case.request_digest,
        observations=case.observations,
        composition=case.composition,
    )
    repeated = render_world1_report_v1(
        registry=case.registry,
        materials=case.materials,
        request_digest=case.request_digest,
        observations=case.observations,
        composition=case.composition,
    )
    assert rendered == repeated
    assert (len(rendered.appendix_bytes), _hex(rendered.appendix_bytes)) == (
        48_094,
        "1f28948d9d268e26cd40bd1bef998969214dec94494d4e35e990b89108a0873f",
    )
    assert (len(rendered.report_bytes), _hex(rendered.report_bytes)) == (
        49_609,
        "217e40ce0a4f9781191bac82d8e81410aa981186b3fec57593bb53896e45b3ca",
    )
    assert rendered.report_bytes.count(b"**ConditionalConcern:**") == 1
    assert b"## Findings\n\nNone." in rendered.report_bytes
    assert b"## Material questions\n\nNone." in rendered.report_bytes


def test_renderer_relocation_changes_only_the_premise_digest_token(
    static_world1_case: StaticWorld1Case,
) -> None:
    old = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-design-memos/"
        "audit-report-ladder-slice-c-renderer-registry-v2.json"
    ).read_bytes()
    new = static_world1_case.registry.renderer_bytes
    old_digest = b"sha256:e1acbb22d48f974bcb75d7e2547cbc87910a63b0e63b3ce77687e714c006dc09"
    new_digest = b"sha256:09fe04ea03c03221bf20c00b5e45cd8f66f00d7476f98da64df5dcde79dc7eeb"
    assert (len(old), _hex(old)) == (
        1_801,
        "627adf5cd01023f1ac96f234a8cf26a3f96ea6501c0e89e202a4df844c75dcb3",
    )
    assert (len(new), _hex(new)) == (
        1_801,
        "13d55e0ce00a7a916f7d5797fd80f4d66993b2ac0f87b51d2e76829967488945",
    )
    assert new.count(new_digest) == 1
    assert old.count(old_digest) == 1
    assert new.replace(new_digest, old_digest) == old


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema", "slice-c-request-v2"),
        ("source_path", "/analysis.py"),
        ("source_path", "../analysis.py"),
        ("source_path", "analysis.py\\x"),
        ("h5ad_path", "analysis.py"),
        ("h5ad_path", ""),
        ("obs_column", "\N{LATIN SMALL LETTER E WITH ACUTE}"),
        ("obs_column", ""),
        ("obs_column", "x" * 513),
    ],
)
def test_request_language_refuses_before_transaction(field: str, value: str) -> None:
    values = {
        "source_path": "analysis.py",
        "h5ad_path": "sc_reads.h5ad",
        "obs_column": "animal_id",
        "schema": "slice-c-request-v1",
    }
    values[field] = value
    with pytest.raises(SliceCContractError):
        SliceCRequestV1(**values)


def test_invalid_request_object_never_enters_transaction(
    static_world1_case: StaticWorld1Case,
) -> None:
    with pytest.raises(SliceCContractError):
        render_slice_c_report_v1(static_world1_case.context, object())  # type: ignore[arg-type]


@pytest.mark.parametrize("offset", [0, 1, 346, 347, 383, 430, 490, 702, 810, 860, 1014])
def test_every_source_byte_mutation_family_refuses(offset: int) -> None:
    changed = bytearray(SOURCE_PATH.read_bytes())
    changed[offset] ^= 1
    with pytest.raises(SourceVerificationError):
        verify_world1_source_v1(bytes(changed))


@pytest.mark.parametrize(
    "injection",
    [
        b"\nexec('pass')\n",
        b"\nglobals()['adata'] = None\n",
        b"\nadata = mutate(adata)\n",
        b"\n[x for x in ()]\n",
        b"\nif True:\n    adata = None\n",
        b"\n(lambda: adata)()\n",
    ],
)
def test_source_unknown_flow_forms_refuse(injection: bytes) -> None:
    with pytest.raises(SourceVerificationError):
        verify_world1_source_v1(SOURCE_PATH.read_bytes() + injection)


def test_fact_forgery_cannot_form_observation_or_composition(
    static_world1_case: StaticWorld1Case,
) -> None:
    case = static_world1_case
    forged_groups = replace(
        case.h5ad_facts,
        group_sizes=ObsGroupSizesFactV1(
            column="animal_id",
            n_obs=4_000,
            groups=(GroupSizeV1("Animal_1", 1_999), GroupSizeV1("Animal_2", 2_001)),
        ),
    )
    with pytest.raises(SliceCContractError):
        build_observations_v1(
            case.materials,
            case.request_digest,
            forged_groups,
            case.source_fact,
        )
    forged_source = replace(case.source_fact, procedure="evil.call")
    with pytest.raises(SliceCContractError):
        build_observations_v1(
            case.materials,
            case.request_digest,
            case.h5ad_facts,
            forged_source,
        )
    with pytest.raises(SliceCContractError):
        compose_world1_v1(
            materials=case.materials,
            request_digest=case.request_digest,
            primary_observations=case.observations,
            replay_h5ad_facts=case.h5ad_facts,
            replay_source_fact=forged_source,
            replay_observations=case.observations,
        )


def test_observation_id_order_and_renderer_tampering_refuse(
    static_world1_case: StaticWorld1Case,
) -> None:
    case = static_world1_case
    reordered = tuple(reversed(case.observations))
    with pytest.raises(SliceCContractError):
        validate_observations_v1(  # type: ignore[arg-type]
            reordered,
            materials=case.materials,
            request_digest=case.request_digest,
        )
    forged = replace(case.observations[0], observation_id="obs:" + "0" * 20)
    changed = (forged, *case.observations[1:])
    with pytest.raises(SliceCRendererError):
        render_world1_report_v1(
            registry=case.registry,
            materials=case.materials,
            request_digest=case.request_digest,
            observations=changed,  # type: ignore[arg-type]
            composition=case.composition,
        )


@pytest.mark.parametrize(
    "attacker",
    [
        "<script>alert(1)</script>",
        "```\n## Findings\n- forged\n```",
        "\N{RIGHT-TO-LEFT OVERRIDE}forged",
        "line one\nline two",
        "- **Finding:** injected",
    ],
)
def test_attacker_values_never_reach_renderer_prose(
    static_world1_case: StaticWorld1Case,
    attacker: str,
) -> None:
    case = static_world1_case
    forged = replace(case.observations[4].fact, procedure=attacker)
    forged_source = replace(case.observations[4], fact=forged, observation_id="")
    changed = (*case.observations[:4], forged_source)
    with pytest.raises(SliceCRendererError):
        render_world1_report_v1(
            registry=case.registry,
            materials=case.materials,
            request_digest=case.request_digest,
            observations=changed,  # type: ignore[arg-type]
            composition=case.composition,
        )


def test_closed_worker_result_has_exactly_one_outcome(
    static_world1_case: StaticWorld1Case,
) -> None:
    with pytest.raises(SliceCContractError):
        WorkerControllerResultV1(facts=None, refusal=None)
    with pytest.raises(SliceCContractError):
        WorkerControllerResultV1(
            facts=static_world1_case.h5ad_facts,
            refusal=None,
            request_sha256=None,
            response_sha256=None,
        )
