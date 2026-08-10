"""Hand-built proof and mutation tests for the dependence v1 kernel."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sc_referee.dependence_core import SAFEGUARD_IDS
from sc_referee.dependence_recognition.certificate import verify_dependence_certificate
from sc_referee.dependence_recognition.ir import (
    MAX_V1_MEMBERSHIPS,
    BoundPackageVersion,
    DependenceCaseBinding,
    DependenceCertificate,
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


def _certificate(
    *,
    resolved_callable: str = "scipy.stats.ttest_ind",
    aggregation: FrameTransformOperation | None = None,
    unit_ids: tuple[str, ...] = ("unit-a", "unit-a", "unit-b"),
) -> DependenceCertificate:
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
    )
    case_binding = DependenceCaseBinding(
        case_id="dependence-case:primary",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        affected_target_ref=affected_ref,
        independent_unit_definition_id="unit-definition:participant",
        authorized_key_columns=("participant_id",),
        authority=authority,
    )
    input_binding = MaterialInputBinding(
        path="inputs/data.csv",
        content_digest=_DATA_DIGEST,
        file_ref=file_ref,
        asset_identity_ref=asset_ref,
    )
    reader = ReaderBinding(
        token="reader:data",
        reader_form="csv_dictreader_file",
        line_model="csv_newline",
        dialect="excel",
    )
    observation_ids = tuple(f"observation-{index}" for index in range(len(unit_ids)))
    multiplicities = tuple(sorted((unit_id, unit_ids.count(unit_id)) for unit_id in set(unit_ids)))
    repeated_unit_ids = tuple(unit_id for unit_id, count in multiplicities if count > 1)
    fact = UnitKeyMultiplicityFact(
        evidence_id="domain-proof:participant",
        path=input_binding.path,
        content_digest=input_binding.content_digest,
        file_ref=file_ref,
        asset_identity_ref=asset_ref,
        reader_form=reader.reader_form,
        line_model=reader.line_model,
        dialect=reader.dialect,
        row_domain="rows:source",
        source_byte_count=max(128, len(unit_ids) * 4),
        header=("observation_id", "participant_id", "value"),
        key_columns=("participant_id",),
        normalization="byte_exact_utf8",
        declared_missing_value_tokens=("NA",),
        missing_key_value_count=0,
        row_shape_complete=True,
        row_count=len(unit_ids),
        observation_ids=observation_ids,
        unit_ids=unit_ids,
        distinct_key_count=len(set(unit_ids)),
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
    lineage = FrameLineage(
        token="lineage:data-to-call",
        input_binding=input_binding,
        reader=reader,
        source_row_domain=fact.row_domain,
        transforms=transforms,
        analyzed_row_domain=analyzed_row_domain,
        source_observation_ids=fact.observation_ids,
        analyzed_observation_ids=analyzed_observation_ids,
        procedure_call_token="call:test",
        relevant_origins=frozenset({input_binding.path, fact.row_domain}),
        relevant_bindings=frozenset({"frame", "group-a", "group-b"}),
    )
    procedure = ProcedureCall(
        token="call:test",
        analysis_target_ref=analysis_ref,
        procedure_ref=procedure_ref,
        resolved_callable=resolved_callable,
        positional_argument_tokens=("group-a", "group-b"),
        keyword_argument_names=(),
        frame_lineage_token=lineage.token,
        analyzed_row_domain=analyzed_row_domain,
        package_version=BoundPackageVersion(
            package_name="scipy",
            version="1.14.0",
            evidence_ids=("lock:scipy",),
        ),
        unit_operand_columns=("participant_id",)
        if resolved_callable == "scipy.stats.ttest_rel"
        else (),
        result_token="result:test",
        evidence_ids=("evidence:call",),
    )
    conclusion = "repeated_units" if repeated_unit_ids else "one_observation_per_unit"
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
            basis="complete finite syntactic check",
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
        fact=fact,
    )
    return DependenceCertificate(
        source_path="workflow/analysis.py",
        source_digest=_SOURCE_DIGEST,
        parser_id="python-ast",
        parser_version="3.11",
        dependency_closure_digest=_CLOSURE_DIGEST,
        proposed_case_digest=_CASE_DIGEST,
        case_binding=case_binding,
        frame_lineage=lineage,
        procedure_call=procedure,
        multiplicity_obligations=(obligation,),
        proven_multiplicity_facts=(fact,),
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
        evidence=(EvidencePoint("workflow/analysis.py", 1, 20, 1, 1),),
    )


def _verify(certificate: DependenceCertificate) -> object | None:
    return verify_dependence_certificate(
        certificate,
        trusted_multiplicity_facts=certificate.proven_multiplicity_facts,
    )


@pytest.mark.parametrize(
    ("resolved_callable", "aggregation", "expected_safeguards"),
    [
        ("scipy.stats.ttest_ind", None, ()),
        ("scipy.stats.ttest_ind", "identity", ()),
        ("scipy.stats.mannwhitneyu", None, ()),
        (
            "scipy.stats.ttest_rel",
            None,
            ("safeguard:paired-or-blocked-procedure",),
        ),
        (
            "scipy.stats.ttest_ind",
            "unit_groupby_mean",
            ("safeguard:unit-level-aggregation",),
        ),
        (
            "scipy.stats.ttest_ind",
            "unit_groupby_first",
            ("safeguard:unit-level-aggregation",),
        ),
    ],
)
def test_kernel_accepts_each_frozen_procedure_and_transform_form(
    resolved_callable: str,
    aggregation: FrameTransformOperation | None,
    expected_safeguards: tuple[str, ...],
) -> None:
    certificate = _certificate(
        resolved_callable=resolved_callable,
        aggregation=aggregation,
    )
    verified = _verify(certificate)
    assert verified is not None
    assert verified.conclusion == "repeated_units"
    assert verified.applicable_safeguard_ids == expected_safeguards


def test_kernel_accepts_a_closed_one_observation_per_unit_certificate() -> None:
    certificate = _certificate(unit_ids=("unit-a", "unit-b", "unit-c"))
    verified = _verify(certificate)
    assert verified is not None
    assert verified.conclusion == "one_observation_per_unit"
    assert verified.repeated_unit_ids == ()


def test_kernel_accepts_the_splitlines_dictreader_model() -> None:
    certificate = _certificate()
    fact = replace(
        certificate.proven_multiplicity_facts[0],
        reader_form="csv_dictreader_splitlines",
        line_model="splitlines",
    )
    reader = replace(
        certificate.frame_lineage.reader,
        reader_form="csv_dictreader_splitlines",
        line_model="splitlines",
    )
    obligation = replace(
        certificate.multiplicity_obligations[0],
        reader=reader,
        fact=fact,
    )
    mutated = replace(
        certificate,
        frame_lineage=replace(certificate.frame_lineage, reader=reader),
        proven_multiplicity_facts=(fact,),
        multiplicity_obligations=(obligation,),
    )
    assert _verify(mutated) is not None


def test_kernel_accepts_not_applicable_only_with_the_complete_absence_proof() -> None:
    certificate = _certificate()
    checks = tuple(
        replace(check, state="not_applicable") if check.state == "absent" else check
        for check in certificate.safeguard_checks
    )
    assert _verify(replace(certificate, safeguard_checks=checks)) is not None


def test_kernel_accepts_the_exact_complete_minus_dead_set_equation() -> None:
    certificate = _certificate()
    all_constructs = certificate.all_syntactic_construct_tokens | {"dead:branch"}
    dead_constructs = frozenset({"dead:branch"})
    checks = tuple(
        replace(
            check,
            complete_syntactic_construct_tokens=all_constructs,
            proven_dead_construct_tokens=dead_constructs,
        )
        for check in certificate.safeguard_checks
    )
    mutated = replace(
        certificate,
        all_syntactic_construct_tokens=all_constructs,
        dead_syntactic_construct_tokens=dead_constructs,
        safeguard_checks=checks,
    )
    assert _verify(mutated) is not None


def test_kernel_enforces_the_v1_membership_cap() -> None:
    at_ceiling = _certificate(unit_ids=("unit-a",) * MAX_V1_MEMBERSHIPS)
    above_ceiling = _certificate(unit_ids=("unit-a",) * (MAX_V1_MEMBERSHIPS + 1))
    collapsed_above_source_ceiling = _certificate(
        unit_ids=("unit-a",) * (MAX_V1_MEMBERSHIPS + 1),
        aggregation="unit_groupby_mean",
    )
    assert _verify(at_ceiling) is not None
    assert _verify(above_ceiling) is None
    assert _verify(collapsed_above_source_ceiling) is not None


@pytest.mark.parametrize(
    "obligation",
    [
        "O1-bound-file",
        "O2-reader-model",
        "O3-frame-shape",
        "O4-fact-equality",
        "O5-fact-closure",
        "O6-multiplicity",
        "O7-key-domain",
        "O8-frame-lineage",
        "O9-procedure",
        "O10-safeguard-completeness",
        "O11-noninterference",
        "O12-affected-sink",
        "O13-singleton-resolution",
    ],
)
def test_kernel_rejects_a_single_field_corruption_for_each_obligation(
    obligation: str,
) -> None:
    certificate = _certificate()
    fact = certificate.proven_multiplicity_facts[0]
    domain_obligation = certificate.multiplicity_obligations[0]
    if obligation == "O1-bound-file":
        fact = replace(fact, content_digest="sha256:" + "9" * 64)
        certificate = replace(
            certificate,
            proven_multiplicity_facts=(fact,),
            multiplicity_obligations=(replace(domain_obligation, fact=fact),),
        )
    elif obligation == "O2-reader-model":
        fact = replace(fact, line_model="splitlines")
        certificate = replace(
            certificate,
            proven_multiplicity_facts=(fact,),
            multiplicity_obligations=(replace(domain_obligation, fact=fact),),
        )
    elif obligation == "O3-frame-shape":
        fact = replace(fact, row_shape_complete=False)
        certificate = replace(
            certificate,
            proven_multiplicity_facts=(fact,),
            multiplicity_obligations=(replace(domain_obligation, fact=fact),),
        )
    elif obligation == "O4-fact-equality":
        certificate = replace(certificate, proven_multiplicity_facts=())
    elif obligation == "O5-fact-closure":
        fact = replace(fact, source_byte_count=0)
        certificate = replace(
            certificate,
            proven_multiplicity_facts=(fact,),
            multiplicity_obligations=(replace(domain_obligation, fact=fact),),
        )
    elif obligation == "O6-multiplicity":
        fact = replace(fact, multiplicities=(("unit-a", 1), ("unit-b", 1)))
        certificate = replace(
            certificate,
            proven_multiplicity_facts=(fact,),
            multiplicity_obligations=(replace(domain_obligation, fact=fact),),
        )
    elif obligation == "O7-key-domain":
        fact = replace(fact, normalization="strip")
        certificate = replace(
            certificate,
            proven_multiplicity_facts=(fact,),
            multiplicity_obligations=(replace(domain_obligation, fact=fact),),
        )
    elif obligation == "O8-frame-lineage":
        certificate = replace(
            certificate,
            frame_lineage=replace(
                certificate.frame_lineage,
                source_observation_ids=("other-observation",),
            ),
        )
    elif obligation == "O9-procedure":
        certificate = replace(
            certificate,
            procedure_call=replace(
                certificate.procedure_call,
                keyword_argument_names=("axis",),
            ),
        )
    elif obligation == "O10-safeguard-completeness":
        check = certificate.safeguard_checks[0]
        certificate = replace(
            certificate,
            safeguard_checks=(
                replace(check, modeled_construct_tokens=frozenset()),
                *certificate.safeguard_checks[1:],
            ),
        )
    elif obligation == "O11-noninterference":
        certificate = replace(
            certificate,
            effects=(
                Effect(
                    reads=frozenset(),
                    writes=frozenset({"frame"}),
                    aliases=frozenset(),
                    may_raise=False,
                    opaque=True,
                    reason="unresolved write",
                ),
            ),
        )
    elif obligation == "O12-affected-sink":
        sink = certificate.sinks[0]
        certificate = replace(
            certificate,
            sinks=(replace(sink, payload_tokens=frozenset()),),
        )
    else:
        certificate = replace(
            certificate,
            reaching_path_conclusions=(frozenset({"repeated_units", "one_observation_per_unit"}),),
        )
    assert _verify(certificate) is None


def test_kernel_rejects_an_absent_safeguard_without_evidence() -> None:
    certificate = _certificate()
    check = certificate.safeguard_checks[0]
    assert check.state == "absent"
    mutated = replace(
        certificate,
        safeguard_checks=(
            replace(check, evidence_ids=()),
            *certificate.safeguard_checks[1:],
        ),
    )
    assert _verify(mutated) is None


@pytest.mark.parametrize(
    "binding",
    ["analysis", "procedure", "unit-definition"],
)
def test_kernel_rejects_any_mismatched_safeguard_operand_binding(binding: str) -> None:
    certificate = _certificate()
    check = certificate.safeguard_checks[0]
    if binding == "analysis":
        check = replace(check, analysis_target_ref=RecordRef("analysis", "analysis:other"))
    elif binding == "procedure":
        check = replace(check, procedure_ref=RecordRef("procedure", "procedure:other"))
    else:
        check = replace(
            check,
            independent_unit_definition_id="unit-definition:other",
        )
    mutated = replace(
        certificate,
        safeguard_checks=(check, *certificate.safeguard_checks[1:]),
    )
    assert _verify(mutated) is None


def test_kernel_rejects_a_non_byte_bound_multiplicity_fact() -> None:
    certificate = _certificate()
    fact = replace(certificate.proven_multiplicity_facts[0], content_digest="unbound")
    obligation = replace(certificate.multiplicity_obligations[0], fact=fact)
    mutated = replace(
        certificate,
        proven_multiplicity_facts=(fact,),
        multiplicity_obligations=(obligation,),
    )
    assert _verify(mutated) is None


def test_kernel_rejects_a_unit_key_not_bound_by_the_human_authority() -> None:
    certificate = _certificate()
    mismatched_binding = replace(
        certificate.case_binding,
        authorized_key_columns=("observation_id",),
    )
    assert _verify(replace(certificate, case_binding=mismatched_binding)) is None


@pytest.mark.parametrize("version", [">=1.14", "1.*", "", " scipy-1.14 "])
def test_kernel_rejects_a_non_exact_or_unpinned_scipy_version(version: str) -> None:
    certificate = _certificate()
    procedure = replace(
        certificate.procedure_call,
        package_version=replace(certificate.procedure_call.package_version, version=version),
    )
    assert _verify(replace(certificate, procedure_call=procedure)) is None


def test_kernel_rejects_trusted_facts_that_do_not_equal_declared_facts() -> None:
    certificate = _certificate()
    assert verify_dependence_certificate(certificate, trusted_multiplicity_facts=()) is None


def test_kernel_rejects_an_unresolved_authority_or_relevant_unknown() -> None:
    certificate = _certificate()
    unresolved_authority = replace(
        certificate.case_binding.authority,
        authority_state="proposed",
    )
    assert (
        _verify(
            replace(
                certificate,
                case_binding=replace(
                    certificate.case_binding,
                    authority=unresolved_authority,
                ),
            )
        )
        is None
    )
    extra_fact = replace(
        certificate.proven_multiplicity_facts[0],
        evidence_id="domain-proof:extraneous",
    )
    assert (
        verify_dependence_certificate(
            certificate,
            trusted_multiplicity_facts=(
                *certificate.proven_multiplicity_facts,
                extra_fact,
            ),
        )
        is None
    )


def test_kernel_rejects_a_paired_operand_not_bound_to_the_authorized_key() -> None:
    certificate = _certificate(resolved_callable="scipy.stats.ttest_rel")
    procedure = replace(
        certificate.procedure_call,
        unit_operand_columns=("observation_id",),
    )
    assert _verify(replace(certificate, procedure_call=procedure)) is None


def test_kernel_rejects_a_recognized_safeguard_claimed_absent() -> None:
    certificate = _certificate(aggregation="unit_groupby_mean")
    checks = tuple(
        replace(check, state="absent")
        if check.safeguard_id == "safeguard:unit-level-aggregation"
        else check
        for check in certificate.safeguard_checks
    )
    assert _verify(replace(certificate, safeguard_checks=checks)) is None
    assert (
        _verify(
            replace(
                certificate,
                unknowns=(Unknown("unresolved input", frozenset({"inputs/data.csv"})),),
            )
        )
        is None
    )


def test_kernel_requires_exactly_one_check_for_every_live_safeguard_id() -> None:
    certificate = _certificate()
    assert len(certificate.safeguard_checks) == len(SAFEGUARD_IDS)
    assert _verify(replace(certificate, safeguard_checks=certificate.safeguard_checks[:-1])) is None
    assert (
        _verify(
            replace(
                certificate,
                safeguard_checks=(
                    *certificate.safeguard_checks,
                    certificate.safeguard_checks[0],
                ),
            )
        )
        is None
    )


def test_kernel_rejects_colliding_syntactic_construct_tokens() -> None:
    certificate = _certificate(aggregation="identity")
    transform = replace(
        certificate.frame_lineage.transforms[0],
        token=certificate.procedure_call.token,
    )
    all_constructs = certificate.all_syntactic_construct_tokens - {
        certificate.frame_lineage.transforms[0].token
    }
    checks = tuple(
        replace(
            check,
            complete_syntactic_construct_tokens=all_constructs,
            modeled_construct_tokens=all_constructs,
        )
        for check in certificate.safeguard_checks
    )
    mutated = replace(
        certificate,
        frame_lineage=replace(certificate.frame_lineage, transforms=(transform,)),
        all_syntactic_construct_tokens=all_constructs,
        safeguard_checks=checks,
    )
    assert _verify(mutated) is None
