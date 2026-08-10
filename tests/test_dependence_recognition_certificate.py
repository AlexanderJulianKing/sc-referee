"""Hand-built proof, mutation, and adversarial regressions for the v1 kernel."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.dependence_core import SAFEGUARD_IDS
from sc_referee.dependence_recognition.certificate import (
    dependence_replay_digest,
    verify_dependence_certificate,
)
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
    BoundPackageVersion,
    DependenceCaseBinding,
    DependenceCertificate,
    EvidenceDeclaration,
    EvidencePoint,
    FrameLineage,
    FrameTransform,
    FrameTransformOperation,
    HumanMethodAuthorization,
    MaterialInputBinding,
    ProcedureCall,
    ReaderBinding,
    RecordRef,
    SafeguardCheckObligation,
    SinkLineageObligation,
    UnitKeyMultiplicityFact,
    UnitKeyMultiplicityObligation,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import Effect, Unknown

_SOURCE_DIGEST = "sha256:" + "1" * 64
_DATA_DIGEST = "sha256:" + "2" * 64
_CLOSURE_DIGEST = "sha256:" + "3" * 64
_CASE_DIGEST = "sha256:" + "4" * 64


@dataclass(frozen=True)
class _Fixture:
    certificate: DependenceCertificate
    trusted_facts: tuple[UnitKeyMultiplicityFact, ...]


def _unit_id(key_columns: tuple[str, ...], key: tuple[str, ...]) -> str:
    return f"unit-key:{semantic_digest({'key_columns': key_columns, 'key_values': key})}"


def _fact_with_keys(
    fact: UnitKeyMultiplicityFact,
    *,
    key_columns: tuple[str, ...],
    key_value_tuples: tuple[tuple[str, ...], ...],
) -> UnitKeyMultiplicityFact:
    unit_ids = tuple(_unit_id(key_columns, key) for key in key_value_tuples)
    counts = Counter(unit_ids)
    multiplicities = tuple(sorted(counts.items()))
    repeated = tuple(sorted(unit_id for unit_id, count in counts.items() if count > 1))
    return replace(
        fact,
        key_columns=key_columns,
        key_value_tuples=key_value_tuples,
        unit_ids=unit_ids,
        distinct_key_count=len(counts),
        multiplicities=multiplicities,
        repeated_unit_ids=repeated,
    )


def _refresh_replay(certificate: DependenceCertificate) -> DependenceCertificate:
    return replace(certificate, replay_digest=dependence_replay_digest(certificate))


def _fixture(
    *,
    resolved_callable: str = "scipy.stats.ttest_ind",
    aggregation: FrameTransformOperation | None = None,
    key_columns: tuple[str, ...] = ("participant_id",),
    key_value_tuples: tuple[tuple[str, ...], ...] = (
        ("unit-a",),
        ("unit-a",),
        ("unit-b",),
    ),
    line_model: str = "csv_newline",
) -> _Fixture:
    analysis_ref = RecordRef("analysis", "analysis:primary")
    procedure_ref = RecordRef("procedure", "procedure:comparison")
    affected_ref = RecordRef("result", "result:primary")
    file_ref = RecordRef("file_record", "file:inputs/data.csv")
    asset_ref = RecordRef("asset_identity", "asset:inputs/data.csv@sha256")
    authority = HumanMethodAuthorization(
        record_type="human_method_authorization",
        record_id="authorization:participant",
        actor_id="human:reviewer",
        authority_state="authorized",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        independent_unit_definition_id="unit-definition:participant",
        authorized_key_columns=key_columns,
        input_path="inputs/data.csv",
        input_content_digest=_DATA_DIGEST,
    )
    case_binding = DependenceCaseBinding(
        case_id="dependence-case:primary",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        affected_target_ref=affected_ref,
        independent_unit_definition_id="unit-definition:participant",
        authorized_key_columns=key_columns,
        authority=authority,
    )
    input_binding = MaterialInputBinding(
        path=authority.input_path,
        content_digest=authority.input_content_digest,
        file_ref=file_ref,
        asset_identity_ref=asset_ref,
    )
    reader_form = (
        "csv_dictreader_splitlines" if line_model == "splitlines" else "csv_dictreader_file"
    )
    reader = ReaderBinding(
        token="reader:data",
        reader_form=reader_form,  # type: ignore[arg-type]
        line_model=line_model,  # type: ignore[arg-type]
        dialect="excel",
    )
    observation_ids = tuple(f"observation-{index}" for index in range(len(key_value_tuples)))
    unit_ids = tuple(_unit_id(key_columns, key) for key in key_value_tuples)
    counts = Counter(unit_ids)
    multiplicities = tuple(sorted(counts.items()))
    repeated_unit_ids = tuple(sorted(unit_id for unit_id, count in counts.items() if count > 1))
    header = tuple(dict.fromkeys(("observation_id", *key_columns, "value")))
    fact = UnitKeyMultiplicityFact(
        evidence_id="domain-proof:participant",
        path=input_binding.path,
        content_digest=input_binding.content_digest,
        file_ref=file_ref,
        asset_identity_ref=asset_ref,
        reader_form=reader.reader_form,
        line_model=reader.line_model,
        splitlines_only_separators_absent=True,
        dialect=reader.dialect,
        row_domain="rows:source",
        source_byte_count=max(128, len(key_value_tuples) * 4),
        header=header,
        key_columns=key_columns,
        normalization="byte_exact_utf8",
        declared_missing_value_tokens=("NA",),
        missing_key_value_count=0,
        row_shape_complete=True,
        row_count=len(key_value_tuples),
        observation_ids=observation_ids,
        key_value_tuples=key_value_tuples,
        unit_ids=unit_ids,
        distinct_key_count=len(counts),
        multiplicities=multiplicities,
        repeated_unit_ids=repeated_unit_ids,
    )
    transforms: tuple[FrameTransform, ...] = ()
    analyzed_row_domain = fact.row_domain
    analyzed_observation_ids = fact.observation_ids
    if aggregation == "identity":
        transforms = (
            FrameTransform(
                token="transform:identity",
                operation=aggregation,
                input_row_domain=fact.row_domain,
                output_row_domain=fact.row_domain,
                grouping_columns=(),
                evidence_ids=("evidence:identity",),
            ),
        )
    elif aggregation is not None:
        transforms = (
            FrameTransform(
                token="transform:aggregate",
                operation=aggregation,
                input_row_domain=fact.row_domain,
                output_row_domain="rows:unit",
                grouping_columns=case_binding.authorized_key_columns,
                evidence_ids=("evidence:aggregate",),
            ),
        )
        analyzed_row_domain = "rows:unit"
        analyzed_observation_ids = tuple(dict.fromkeys(fact.unit_ids))
    output_token = transforms[-1].token if transforms else reader.token
    lineage_relevant_origins = {
        input_binding.path,
        fact.row_domain,
        analyzed_row_domain,
        *(item.input_row_domain for item in transforms),
        *(item.output_row_domain for item in transforms),
    }
    lineage_relevant_bindings = {
        reader.token,
        "lineage:data-to-call",
        output_token,
        "call:test",
        "result:test",
        "group-a",
        "group-b",
        "frame",
        *(item.token for item in transforms),
    }
    lineage = FrameLineage(
        token="lineage:data-to-call",
        input_binding=input_binding,
        reader=reader,
        source_row_domain=fact.row_domain,
        transforms=transforms,
        analyzed_row_domain=analyzed_row_domain,
        source_observation_ids=fact.observation_ids,
        analyzed_observation_ids=analyzed_observation_ids,
        output_token=output_token,
        procedure_call_token="call:test",
        relevant_origins=frozenset(lineage_relevant_origins),
        relevant_bindings=frozenset(lineage_relevant_bindings),
    )
    procedure = ProcedureCall(
        token="call:test",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        resolved_callable=resolved_callable,
        positional_argument_tokens=("group-a", "group-b"),
        positional_argument_frame_bindings=(
            ("group-a", output_token),
            ("group-b", output_token),
        ),
        keyword_argument_names=(),
        frame_lineage_token=lineage.token,
        analyzed_row_domain=analyzed_row_domain,
        package_version=BoundPackageVersion(
            package_name="scipy",
            version="1.14.0",
            evidence_ids=("lock:scipy",),
        ),
        unit_operand_columns=key_columns if resolved_callable == "scipy.stats.ttest_rel" else (),
        result_token="result:test",
        evidence_ids=("evidence:call",),
    )
    analyzed_repeated = (
        ()
        if aggregation
        in {
            "unit_groupby_mean",
            "unit_groupby_first",
        }
        else repeated_unit_ids
    )
    conclusion = "repeated_units" if analyzed_repeated else "one_observation_per_unit"
    sink = SinkLineageObligation(
        token="sink:report",
        path="results/report.md",
        affected_target_ref=affected_ref,
        procedure_call_token=procedure.token,
        procedure_result_token=procedure.result_token,
        payload_tokens=frozenset({procedure.result_token}),
        selected_result=True,
        conclusion=conclusion,
        evidence_ids=("evidence:sink",),
        relevant_origins=frozenset({input_binding.path, analyzed_row_domain}),
        relevant_bindings=frozenset({procedure.result_token, "report"}),
    )
    construct_tokens = frozenset(
        {
            reader.token,
            lineage.token,
            procedure.token,
            sink.token,
            *(transform.token for transform in transforms),
        }
    )
    expected_matches = {safeguard_id: frozenset() for safeguard_id in SAFEGUARD_IDS}
    if aggregation in {"unit_groupby_mean", "unit_groupby_first"}:
        expected_matches["safeguard:unit-level-aggregation"] = frozenset({transforms[0].token})
    if resolved_callable == "scipy.stats.ttest_rel":
        expected_matches["safeguard:paired-or-blocked-procedure"] = frozenset({procedure.token})
    safeguard_checks = tuple(
        SafeguardCheckObligation(
            safeguard_id=safeguard_id,
            state="present" if expected_matches[safeguard_id] else "absent",
            analysis_target_ref=analysis_ref,
            procedure_ref=procedure_ref,
            independent_unit_definition_id=case_binding.independent_unit_definition_id,
            evidence_ids=(f"evidence:{safeguard_id}",),
            basis=(
                "recognized-collapse"
                if expected_matches[safeguard_id]
                and safeguard_id == "safeguard:unit-level-aggregation"
                else "registry-match"
                if expected_matches[safeguard_id]
                else "completeness-equation"
            ),
            complete_syntactic_construct_tokens=construct_tokens,
            modeled_construct_tokens=construct_tokens,
            proven_dead_construct_tokens=frozenset(),
            matched_construct_tokens=expected_matches[safeguard_id],
        )
        for safeguard_id in SAFEGUARD_IDS
    )
    obligation = UnitKeyMultiplicityObligation(
        input_binding=input_binding,
        reader=reader,
        row_domain=fact.row_domain,
        key_columns=case_binding.authorized_key_columns,
    )
    evidence_ids = {
        fact.evidence_id,
        "lock:scipy",
        "evidence:call",
        "evidence:sink",
        *(item for transform in transforms for item in transform.evidence_ids),
        *(item for check in safeguard_checks for item in check.evidence_ids),
    }
    evidence = tuple(
        EvidenceDeclaration(
            evidence_id=evidence_id,
            point=EvidencePoint(
                fact.path if evidence_id == fact.evidence_id else "workflow/analysis.py",
                1,
                max(1, fact.row_count + 1) if evidence_id == fact.evidence_id else 20,
                1,
                1,
            ),
        )
        for evidence_id in sorted(evidence_ids)
    )
    certificate = DependenceCertificate(
        source_path="workflow/analysis.py",
        source_digest=_SOURCE_DIGEST,
        parser_id="python-ast",
        parser_version="3.11",
        dependency_closure_digest=_CLOSURE_DIGEST,
        proposed_case_digest=_CASE_DIGEST,
        replay_digest="sha256:" + "0" * 64,
        case_binding=case_binding,
        frame_lineage=lineage,
        procedure_call=procedure,
        multiplicity_obligations=(obligation,),
        safeguard_checks=safeguard_checks,
        sinks=(sink,),
        all_syntactic_construct_tokens=construct_tokens,
        dead_syntactic_construct_tokens=frozenset(),
        all_sink_tokens=frozenset({sink.token}),
        dead_sink_tokens=frozenset(),
        reaching_path_conclusions=(frozenset({conclusion}),),
        effects=(),
        unknowns=(),
        safeguard_registry_ids=SAFEGUARD_IDS,
        output_ceiling="evaluation_candidate",
        wording_ceiling="static_code_relationship_only",
        evidence=evidence,
    )
    return _Fixture(_refresh_replay(certificate), (fact,))


def _verify(fixture: _Fixture) -> object | None:
    return verify_dependence_certificate(
        fixture.certificate,
        trusted_multiplicity_facts=fixture.trusted_facts,
    )


def _with_certificate(fixture: _Fixture, certificate: DependenceCertificate) -> _Fixture:
    return replace(fixture, certificate=certificate)


def _with_fact(fixture: _Fixture, fact: UnitKeyMultiplicityFact) -> _Fixture:
    return replace(fixture, trusted_facts=(fact,))


@pytest.mark.parametrize(
    ("resolved_callable", "aggregation", "expected_conclusion", "expected_safeguards"),
    [
        ("scipy.stats.ttest_ind", None, "repeated_units", ()),
        ("scipy.stats.ttest_ind", "identity", "repeated_units", ()),
        ("scipy.stats.mannwhitneyu", None, "repeated_units", ()),
        (
            "scipy.stats.ttest_rel",
            None,
            "repeated_units",
            ("safeguard:paired-or-blocked-procedure",),
        ),
        (
            "scipy.stats.ttest_ind",
            "unit_groupby_mean",
            "one_observation_per_unit",
            ("safeguard:unit-level-aggregation",),
        ),
        (
            "scipy.stats.ttest_ind",
            "unit_groupby_first",
            "one_observation_per_unit",
            ("safeguard:unit-level-aggregation",),
        ),
    ],
)
def test_kernel_accepts_each_frozen_procedure_and_transform_form(
    resolved_callable: str,
    aggregation: FrameTransformOperation | None,
    expected_conclusion: str,
    expected_safeguards: tuple[str, ...],
) -> None:
    fixture = _fixture(resolved_callable=resolved_callable, aggregation=aggregation)
    verified = _verify(fixture)
    assert verified is not None
    assert verified.conclusion == expected_conclusion
    assert verified.applicable_safeguard_ids == expected_safeguards
    if aggregation in {"unit_groupby_mean", "unit_groupby_first"}:
        assert verified.repeated_unit_ids == ()
        assert verified.source_frame_repeated_unit_ids


def test_kernel_accepts_nonrepetition_and_both_reader_models() -> None:
    unique = (("a",), ("b",), ("c",))
    for line_model in ("csv_newline", "splitlines"):
        verified = _verify(_fixture(key_value_tuples=unique, line_model=line_model))
        assert verified is not None
        assert verified.conclusion == "one_observation_per_unit"
        assert verified.repeated_unit_ids == ()


def test_kernel_accepts_not_applicable_and_exact_dead_set_equation() -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    all_constructs = certificate.all_syntactic_construct_tokens | {"dead:branch"}
    dead = frozenset({"dead:branch"})
    checks = tuple(
        replace(
            check,
            state="not_applicable" if check.state == "absent" else check.state,
            complete_syntactic_construct_tokens=all_constructs,
            modeled_construct_tokens=certificate.all_syntactic_construct_tokens,
            proven_dead_construct_tokens=dead,
        )
        for check in certificate.safeguard_checks
    )
    mutated = _refresh_replay(
        replace(
            certificate,
            all_syntactic_construct_tokens=all_constructs,
            dead_syntactic_construct_tokens=dead,
            safeguard_checks=checks,
        )
    )
    assert _verify(_with_certificate(fixture, mutated)) is not None


def test_kernel_enforces_analyzed_membership_cap_without_rejecting_a_collapsed_source() -> None:
    at = (("a",),) * MAX_V1_MEMBERSHIPS
    above = (("a",),) * (MAX_V1_MEMBERSHIPS + 1)
    assert _verify(_fixture(key_value_tuples=at)) is not None
    assert _verify(_fixture(key_value_tuples=above)) is None
    assert _verify(_fixture(key_value_tuples=above, aggregation="unit_groupby_mean")) is not None


@pytest.mark.parametrize("obligation", [f"O{index}" for index in range(1, 14)])
def test_kernel_rejects_single_field_corruption_for_each_obligation(obligation: str) -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    fact = fixture.trusted_facts[0]
    if obligation == "O1":
        fixture = _with_fact(fixture, replace(fact, content_digest="sha256:" + "9" * 64))
    elif obligation == "O2":
        fixture = _with_fact(fixture, replace(fact, line_model="splitlines"))
    elif obligation == "O3":
        fixture = _with_fact(fixture, replace(fact, row_shape_complete=False))
    elif obligation == "O4":
        fixture = replace(fixture, trusted_facts=())
    elif obligation == "O5":
        fixture = _with_fact(fixture, replace(fact, source_byte_count=0))
    elif obligation == "O6":
        fixture = _with_fact(fixture, replace(fact, multiplicities=((fact.unit_ids[0], 1),)))
    elif obligation == "O7":
        fixture = _with_fact(fixture, replace(fact, normalization="strip"))
    elif obligation == "O8":
        lineage = replace(certificate.frame_lineage, source_observation_ids=("other",))
        fixture = _with_certificate(fixture, replace(certificate, frame_lineage=lineage))
    elif obligation == "O9":
        procedure = replace(certificate.procedure_call, keyword_argument_names=("axis",))
        fixture = _with_certificate(fixture, replace(certificate, procedure_call=procedure))
    elif obligation == "O10":
        first = replace(certificate.safeguard_checks[0], modeled_construct_tokens=frozenset())
        mutated = replace(
            certificate,
            safeguard_checks=(first, *certificate.safeguard_checks[1:]),
        )
        fixture = _with_certificate(fixture, _refresh_replay(mutated))
    elif obligation == "O11":
        effect = Effect(
            reads=frozenset(),
            writes=frozenset({"frame"}),
            aliases=frozenset(),
            may_raise=False,
            opaque=False,
            reason="relevant write",
        )
        fixture = _with_certificate(fixture, replace(certificate, effects=(effect,)))
    elif obligation == "O12":
        sink = replace(certificate.sinks[0], payload_tokens=frozenset())
        fixture = _with_certificate(fixture, replace(certificate, sinks=(sink,)))
    else:
        fixture = _with_certificate(
            fixture,
            replace(
                certificate,
                reaching_path_conclusions=(
                    frozenset({"repeated_units", "one_observation_per_unit"}),
                ),
            ),
        )
    assert _verify(fixture) is None


# --- Verbatim Opus finding regressions ---------------------------------------


def test_regression_f1_authority_refuses_measurement_column_substitution() -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    fact = _fact_with_keys(
        fixture.trusted_facts[0],
        key_columns=("value",),
        key_value_tuples=(("1",), ("1",), ("2",)),
    )
    obligation = replace(certificate.multiplicity_obligations[0], key_columns=("value",))
    mutated = replace(certificate, multiplicity_obligations=(obligation,))
    assert _verify(_Fixture(mutated, (fact,))) is None


def test_regression_f2_certificate_has_no_embedded_trusted_fact_channel() -> None:
    fixture = _fixture()
    assert not hasattr(fixture.certificate, "proven_multiplicity_facts")
    assert not hasattr(fixture.certificate.multiplicity_obligations[0], "fact")
    assert verify_dependence_certificate(fixture.certificate) is None


@pytest.mark.parametrize(
    "write",
    ["inputs/data.csv", "rows:source", "reader:data", "transform:aggregate"],
)
def test_regression_f3_writes_to_any_origin_or_binding_refuse(write: str) -> None:
    fixture = _fixture(aggregation="unit_groupby_mean")
    effect = Effect(
        reads=frozenset(),
        writes=frozenset({write}),
        aliases=frozenset(),
        may_raise=False,
        opaque=True,
        reason="reviewer repro",
    )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, effects=(effect,)))) is None
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, effects=(replace(effect, opaque=False),)),
            )
        )
        is None
    )


@pytest.mark.parametrize("alias", ["inputs/data.csv", "rows:source", "group-a", "reader:data"])
def test_regression_f3_aliases_to_any_origin_or_binding_refuse(alias: str) -> None:
    fixture = _fixture()
    effect = Effect(
        reads=frozenset(),
        writes=frozenset(),
        aliases=frozenset({alias}),
        may_raise=False,
        opaque=False,
        reason="reviewer union repro",
    )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, effects=(effect,)))) is None
    )


@pytest.mark.parametrize("origin", ["group-a", "frame"])
def test_regression_f4_unknown_over_relevant_binding_refuses(origin: str) -> None:
    fixture = _fixture()
    unknown = Unknown("unresolved subset selector", frozenset({origin}))
    mutated = replace(fixture.certificate, unknowns=(unknown,))
    assert _verify(_with_certificate(fixture, mutated)) is None


def test_regression_f5_opaque_effect_without_wildcard_write_refuses() -> None:
    fixture = _fixture()
    effect = Effect(
        reads=frozenset({"frame"}),
        writes=frozenset(),
        aliases=frozenset(),
        may_raise=False,
        opaque=True,
        reason="unmodelable subtree",
    )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, effects=(effect,)))) is None
    )


def test_regression_f6_shrunken_analyzer_slice_cannot_hide_operand_write() -> None:
    fixture = _fixture()
    lineage = replace(fixture.certificate.frame_lineage, relevant_bindings=frozenset({"frame"}))
    effect = Effect(
        reads=frozenset(),
        writes=frozenset({"group-a"}),
        aliases=frozenset(),
        may_raise=False,
        opaque=True,
        reason="opaque operand rebind",
    )
    mutated = replace(fixture.certificate, frame_lineage=lineage, effects=(effect,))
    assert _verify(_with_certificate(fixture, mutated)) is None


def test_regression_f7_composite_label_join_collision_refuses() -> None:
    fixture = _fixture(
        key_columns=("site", "subject"),
        key_value_tuples=(("a|b", "c"), ("a", "b|c")),
    )
    fact = replace(
        fixture.trusted_facts[0],
        unit_ids=("a|b|c", "a|b|c"),
        distinct_key_count=1,
        multiplicities=(("a|b|c", 2),),
        repeated_unit_ids=("a|b|c",),
    )
    assert _verify(_with_fact(fixture, fact)) is None


def test_regression_f8_live_diagnostic_sink_cannot_be_laundered_as_dead() -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    diagnostic = "sink:diagnostic"
    all_constructs = certificate.all_syntactic_construct_tokens | {diagnostic}
    checks = tuple(
        replace(
            check,
            complete_syntactic_construct_tokens=all_constructs,
            modeled_construct_tokens=all_constructs,
        )
        for check in certificate.safeguard_checks
    )
    mutated = _refresh_replay(
        replace(
            certificate,
            all_syntactic_construct_tokens=all_constructs,
            safeguard_checks=checks,
            all_sink_tokens=certificate.all_sink_tokens | {diagnostic},
            dead_sink_tokens=frozenset({diagnostic}),
        )
    )
    assert _verify(_with_certificate(fixture, mutated)) is None


def test_regression_f9_collapsed_analysis_cannot_carry_source_repetition_conclusion() -> None:
    fixture = _fixture(aggregation="unit_groupby_mean")
    sink = replace(fixture.certificate.sinks[0], conclusion="repeated_units")
    mutated = replace(
        fixture.certificate,
        sinks=(sink,),
        reaching_path_conclusions=(frozenset({"repeated_units"}),),
    )
    assert _verify(_with_certificate(fixture, mutated)) is None


@pytest.mark.parametrize(
    "digest",
    [
        "sha256:0x" + "0" * 62,
        "sha256:1_" + "0" * 62,
        "sha256: " + "0" * 63,
        "sha256:\n" + "0" * 63,
        "sha256:+" + "0" * 63,
        "sha256:-" + "0" * 63,
        "sha256:" + "A" * 64,
    ],
)
def test_regression_f10_noncanonical_sha256_spellings_refuse(digest: str) -> None:
    fixture = _fixture()
    mutated = _refresh_replay(replace(fixture.certificate, source_digest=digest))
    assert _verify(_with_certificate(fixture, mutated)) is None


@pytest.mark.parametrize(
    "path",
    ["..\\evil.csv", "a\\..\\..\\etc\\passwd", "   ", "\t", "x\x00y"],
)
def test_regression_f11_unsafe_sink_paths_refuse(path: str) -> None:
    fixture = _fixture()
    sink = replace(fixture.certificate.sinks[0], path=path)
    assert _verify(_with_certificate(fixture, replace(fixture.certificate, sinks=(sink,)))) is None


def test_regression_f12_splitlines_fact_requires_separator_absence_proof() -> None:
    fixture = _fixture(line_model="splitlines")
    fact = replace(fixture.trusted_facts[0], splitlines_only_separators_absent=False)
    assert _verify(_with_fact(fixture, fact)) is None


def test_regression_f13_free_text_basis_and_undeclared_evidence_refuse() -> None:
    fixture = _fixture()
    check = fixture.certificate.safeguard_checks[0]
    bad_basis = replace(check, basis=cast(Any, "ZZZ"))
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    safeguard_checks=(bad_basis, *fixture.certificate.safeguard_checks[1:]),
                ),
            )
        )
        is None
    )

    undeclared_fact = replace(
        fixture.trusted_facts[0],
        evidence_id="membership:not-declared",
    )
    assert _verify(_with_fact(fixture, undeclared_fact)) is None
    bad_evidence = replace(check, evidence_ids=("evidence:not-declared",))
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    safeguard_checks=(bad_evidence, *fixture.certificate.safeguard_checks[1:]),
                ),
            )
        )
        is None
    )


@pytest.mark.parametrize("version", ["0", "1e9", "1_2", "9" * 400])
def test_regression_f14_version_pin_must_be_in_explicit_supported_set(version: str) -> None:
    fixture = _fixture()
    procedure = replace(
        fixture.certificate.procedure_call,
        package_version=replace(
            fixture.certificate.procedure_call.package_version, version=version
        ),
    )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, procedure_call=procedure)))
        is None
    )


# --- Spec-concern closures and held refusal inventory ------------------------


def test_regression_sc1_replay_digest_binds_parser_and_completeness_sets() -> None:
    fixture = _fixture()
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, parser_id="mutant")))
        is None
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    all_syntactic_construct_tokens=fixture.certificate.all_syntactic_construct_tokens
                    | {"mutant"},
                ),
            )
        )
        is None
    )


def test_regression_sc2_every_positional_argument_requires_frame_output_binding() -> None:
    fixture = _fixture()
    procedure = replace(
        fixture.certificate.procedure_call,
        positional_argument_frame_bindings=(
            ("group-a", fixture.certificate.frame_lineage.output_token),
        ),
    )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, procedure_call=procedure)))
        is None
    )


def test_regression_sc3_unknown_safeguard_state_refuses_a_certificate() -> None:
    fixture = _fixture()
    check = replace(fixture.certificate.safeguard_checks[0], state="unknown")
    mutated = replace(
        fixture.certificate,
        safeguard_checks=(check, *fixture.certificate.safeguard_checks[1:]),
    )
    assert _verify(_with_certificate(fixture, mutated)) is None


def test_regression_sc4_paired_operand_must_equal_authorized_key() -> None:
    fixture = _fixture(resolved_callable="scipy.stats.ttest_rel")
    procedure = replace(
        fixture.certificate.procedure_call,
        unit_operand_columns=("observation_id",),
    )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, procedure_call=procedure)))
        is None
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "unregistered-callable",
        "trailing-callable-space",
        "three-arguments",
        "keyword",
        "non-scipy",
        "unit-operand-independent",
    ],
)
def test_held_procedure_refusals(mutation: str) -> None:
    fixture = _fixture()
    procedure = fixture.certificate.procedure_call
    if mutation == "unregistered-callable":
        procedure = replace(procedure, resolved_callable="scipy.stats.f_oneway")
    elif mutation == "trailing-callable-space":
        procedure = replace(procedure, resolved_callable="scipy.stats.ttest_ind ")
    elif mutation == "three-arguments":
        procedure = replace(
            procedure,
            positional_argument_tokens=("group-a", "group-b", "group-c"),
            positional_argument_frame_bindings=(
                *procedure.positional_argument_frame_bindings,
                ("group-c", fixture.certificate.frame_lineage.output_token),
            ),
        )
    elif mutation == "keyword":
        procedure = replace(procedure, keyword_argument_names=("axis",))
    elif mutation == "non-scipy":
        procedure = replace(
            procedure,
            package_version=replace(procedure.package_version, package_name="numpy"),
        )
    else:
        procedure = replace(procedure, unit_operand_columns=("participant_id",))
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, procedure_call=procedure)))
        is None
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "unsupported",
        "present-unmatched",
        "missing-check",
        "duplicate-check",
        "mismatched-binding",
        "absent-no-evidence",
        "recognized-claimed-absent",
    ],
)
def test_held_safeguard_refusals(mutation: str) -> None:
    fixture = _fixture(
        aggregation="unit_groupby_mean" if mutation == "recognized-claimed-absent" else None
    )
    checks = fixture.certificate.safeguard_checks
    first = checks[0]
    if mutation in {"unknown", "unsupported"}:
        first = replace(first, state=mutation)
        checks = (first, *checks[1:])
    elif mutation == "present-unmatched":
        first = replace(first, state="present")
        checks = (first, *checks[1:])
    elif mutation == "missing-check":
        checks = checks[:-1]
    elif mutation == "duplicate-check":
        checks = (*checks, first)
    elif mutation == "mismatched-binding":
        first = replace(first, independent_unit_definition_id="unit-definition:other")
        checks = (first, *checks[1:])
    elif mutation == "absent-no-evidence":
        first = replace(first, evidence_ids=())
        checks = (first, *checks[1:])
    else:
        index = next(
            index
            for index, check in enumerate(checks)
            if check.safeguard_id == "safeguard:unit-level-aggregation"
        )
        checks = tuple(
            replace(check, state="absent") if item == index else check
            for item, check in enumerate(checks)
        )
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, safeguard_checks=checks)))
        is None
    )


def test_held_reader_registry_and_ceiling_refusals() -> None:
    fixture = _fixture()
    reader = replace(fixture.certificate.frame_lineage.reader, line_model="splitlines")
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    frame_lineage=replace(fixture.certificate.frame_lineage, reader=reader),
                ),
            )
        )
        is None
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, output_ceiling=cast(Any, "production_finding")),
            )
        )
        is None
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, wording_ceiling=cast(Any, "scientific_invalidity")),
            )
        )
        is None
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(fixture.certificate, safeguard_registry_ids=tuple(reversed(SAFEGUARD_IDS))),
            )
        )
        is None
    )


def test_held_sink_and_control_flow_refusals() -> None:
    fixture = _fixture()
    sink = fixture.certificate.sinks[0]
    for bad_sink in (
        replace(sink, selected_result=False),
        replace(sink, payload_tokens=frozenset()),
        replace(sink, affected_target_ref=RecordRef("result", "result:other")),
    ):
        assert (
            _verify(_with_certificate(fixture, replace(fixture.certificate, sinks=(bad_sink,))))
            is None
        )
    wildcard = Effect(frozenset(), frozenset({"*"}), frozenset(), False, True, "opaque")
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, effects=(wildcard,))))
        is None
    )
    unknown = Unknown("unknown input", frozenset({"inputs/data.csv"}))
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, unknowns=(unknown,))))
        is None
    )


def test_held_competing_sink_colliding_tokens_and_dead_set_refusals() -> None:
    fixture = _fixture()
    certificate = fixture.certificate
    sink = certificate.sinks[0]

    competing = replace(
        sink,
        token="sink:competing",
        affected_target_ref=RecordRef("result", "result:other"),
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    certificate,
                    sinks=(sink, competing),
                    all_sink_tokens=frozenset({sink.token, competing.token}),
                ),
            )
        )
        is None
    )

    colliding = replace(sink, token=certificate.procedure_call.token)
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    certificate,
                    sinks=(colliding,),
                    all_sink_tokens=frozenset({colliding.token}),
                ),
            )
        )
        is None
    )

    outside_dead = frozenset({"dead:not-in-complete-set"})
    checks = tuple(
        replace(check, proven_dead_construct_tokens=outside_dead)
        for check in certificate.safeguard_checks
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                _refresh_replay(
                    replace(
                        certificate,
                        dead_syntactic_construct_tokens=outside_dead,
                        safeguard_checks=checks,
                    )
                ),
            )
        )
        is None
    )

    all_dead = certificate.all_syntactic_construct_tokens
    checks = tuple(
        replace(
            check,
            modeled_construct_tokens=frozenset(),
            proven_dead_construct_tokens=all_dead,
        )
        for check in certificate.safeguard_checks
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                _refresh_replay(
                    replace(
                        certificate,
                        dead_syntactic_construct_tokens=all_dead,
                        safeguard_checks=checks,
                    )
                ),
            )
        )
        is None
    )


def test_held_fact_channel_refusals() -> None:
    fixture = _fixture()
    fact = fixture.trusted_facts[0]
    assert verify_dependence_certificate(fixture.certificate, trusted_multiplicity_facts=()) is None
    assert (
        verify_dependence_certificate(
            fixture.certificate,
            trusted_multiplicity_facts=(fact, fact),
        )
        is None
    )
    extra = replace(fact, row_domain="rows:extra")
    assert (
        verify_dependence_certificate(
            fixture.certificate,
            trusted_multiplicity_facts=(fact, extra),
        )
        is None
    )


def test_held_evidence_and_token_refusals() -> None:
    fixture = _fixture()
    declaration = fixture.certificate.evidence[0]
    bad_declaration = replace(
        declaration,
        point=replace(declaration.point, path="other/file.py"),
    )
    evidence = (bad_declaration, *fixture.certificate.evidence[1:])
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, evidence=evidence))) is None
    )
    lineage = replace(fixture.certificate.frame_lineage, procedure_call_token="call:other")
    assert (
        _verify(_with_certificate(fixture, replace(fixture.certificate, frame_lineage=lineage)))
        is None
    )


def test_held_transform_refusals() -> None:
    fixture = _fixture(aggregation="unit_groupby_mean")
    transform = fixture.certificate.frame_lineage.transforms[0]
    bad_group = replace(transform, grouping_columns=("value",))
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    frame_lineage=replace(
                        fixture.certificate.frame_lineage, transforms=(bad_group,)
                    ),
                ),
            )
        )
        is None
    )

    wrong_domain = "rows:not-the-chain-output"
    lineage = replace(
        fixture.certificate.frame_lineage,
        analyzed_row_domain=wrong_domain,
        relevant_origins=fixture.certificate.frame_lineage.relevant_origins | {wrong_domain},
    )
    procedure = replace(fixture.certificate.procedure_call, analyzed_row_domain=wrong_domain)
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    frame_lineage=lineage,
                    procedure_call=procedure,
                ),
            )
        )
        is None
    )

    double = (
        transform,
        replace(
            transform,
            token="transform:second",
            input_row_domain="rows:unit",
            output_row_domain="rows:twice",
        ),
    )
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    frame_lineage=replace(fixture.certificate.frame_lineage, transforms=double),
                ),
            )
        )
        is None
    )
    unsupported = replace(transform, operation=cast(Any, "filter"))
    assert (
        _verify(
            _with_certificate(
                fixture,
                replace(
                    fixture.certificate,
                    frame_lineage=replace(
                        fixture.certificate.frame_lineage, transforms=(unsupported,)
                    ),
                ),
            )
        )
        is None
    )


def test_held_kernel_fact_ceilings_accept_boundary_and_refuse_boundary_plus_one() -> None:
    fixture = _fixture()
    fact = fixture.trusted_facts[0]

    assert _verify(
        _with_fact(fixture, replace(fact, source_byte_count=MAX_DEPENDENCE_CSV_DOMAIN_BYTES))
    )
    assert (
        _verify(
            _with_fact(
                fixture,
                replace(fact, source_byte_count=MAX_DEPENDENCE_CSV_DOMAIN_BYTES + 1),
            )
        )
        is None
    )

    boundary_header = (
        *fact.header,
        *(f"field-{index}" for index in range(MAX_DEPENDENCE_CSV_DOMAIN_FIELDS - len(fact.header))),
    )
    assert len(boundary_header) == MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
    assert _verify(_with_fact(fixture, replace(fact, header=boundary_header)))
    assert (
        _verify(_with_fact(fixture, replace(fact, header=(*boundary_header, "one-too-many"))))
        is None
    )

    boundary_field = "x" * MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
    assert _verify(_with_fact(fixture, replace(fact, header=(*fact.header, boundary_field))))
    assert (
        _verify(_with_fact(fixture, replace(fact, header=(*fact.header, boundary_field + "x"))))
        is None
    )

    at_row_ceiling = (("unit-a",),) * MAX_DEPENDENCE_CSV_DOMAIN_ROWS
    above_row_ceiling = (*at_row_ceiling, ("unit-a",))
    assert _verify(_fixture(key_value_tuples=at_row_ceiling, aggregation="unit_groupby_mean"))
    assert (
        _verify(_fixture(key_value_tuples=above_row_ceiling, aggregation="unit_groupby_mean"))
        is None
    )
