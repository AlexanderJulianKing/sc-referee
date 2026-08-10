"""Adversarial tests for the dependence v1 static proposing analyzer."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.dependence_core import evaluate_dependence_case
from sc_referee.dependence_recognition.certificate import verify_dependence_certificate
from sc_referee.dependence_recognition.python_analyzer import (
    analyze_dependence_python,
    discharge_dependence_proposal,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)

_DATA_PATH = "inputs/data.csv"
_REPORT_PATH = "results/report.txt"


def _source(
    *,
    scipy_import: str = "import scipy.stats as st",
    callable_name: str = "st.ttest_ind",
    reader: str | None = None,
    before_operands: str = "",
    frame_name: str = "rows",
    before_call: str = "",
    call: str | None = None,
    after_call: str = "",
) -> str:
    reader = reader or (
        'rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", encoding="utf-8")))'
    )
    call = call or f"result = {callable_name}(group_a, group_b)"
    return "\n".join(
        item
        for item in (
            "import csv",
            "from pathlib import Path",
            scipy_import,
            reader,
            before_operands,
            f'group_a = [float(row["a"]) for row in {frame_name}]',
            f'group_b = [float(row["b"]) for row in {frame_name}]',
            before_call,
            call,
            after_call,
            'Path("results/report.txt").write_text(str(result), encoding="utf-8")',
            "",
        )
        if item
    )


def _context(
    source: str,
    *,
    data: bytes = b"participant_id,site_id,a,b\np1,s1,1,2\np1,s1,2,3\np2,s2,4,5\n",
    authority: bool = True,
    key_columns: tuple[str, ...] = ("participant_id",),
    requirements: bytes = b"scipy==1.14.0\n",
    second_authority: bool = False,
    authority_analysis_id: str = "analysis:primary",
    authority_procedure_id: str = "procedure:test",
    authority_input_path: str = _DATA_PATH,
    authority_input_digest: str | None = None,
    procedure_callable: str | None = None,
) -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "surface:primary")
    artifact_ref = RecordRef("artifact", "artifact:report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:primary")
    analysis_file_ref = RecordRef("file_record", "file:analysis")
    parser_ref = RecordRef("parser_result", "parser:analysis")
    data_file_ref = RecordRef("file_record", "file:data")
    data_identity_ref = RecordRef("asset_identity", "asset:data")
    requirements_file_ref = RecordRef("file_record", "file:requirements")
    requirements_identity_ref = RecordRef("asset_identity", "asset:requirements")
    analysis_ref = RecordRef("analysis", "analysis:primary")
    procedure_ref = RecordRef("procedure", "procedure:test")
    result_ref = RecordRef("result", "result:report")
    data_digest = sha256_digest(data)
    requirements_digest = sha256_digest(requirements)
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    source_bytes = source.encode()

    records: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": _REPORT_PATH,
            },
        ),
        (
            snapshot_ref,
            {
                "snapshot_id": snapshot_ref.record_id,
                "extensions": {"x-material-full-digest-paths": [_DATA_PATH, "requirements.txt"]},
            },
        ),
        (
            data_file_ref,
            {
                "file_record_id": data_file_ref.record_id,
                "path": _DATA_PATH,
                "entry_kind": "regular_file",
                "asset_identity_ref": data_identity_ref.to_dict(),
            },
        ),
        (
            data_identity_ref,
            {
                "asset_identity_id": data_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": data_file_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
        (
            requirements_file_ref,
            {
                "file_record_id": requirements_file_ref.record_id,
                "path": "requirements.txt",
                "entry_kind": "regular_file",
                "asset_identity_ref": requirements_identity_ref.to_dict(),
            },
        ),
        (
            requirements_identity_ref,
            {
                "asset_identity_id": requirements_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": requirements_file_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": requirements_digest,
                },
            },
        ),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
        (analysis_ref, {"analysis_id": analysis_ref.record_id}),
        (
            procedure_ref,
            {
                "procedure_id": procedure_ref.record_id,
                **(
                    {"resolved_callable": procedure_callable}
                    if procedure_callable is not None
                    else {}
                ),
            },
        ),
        (result_ref, {"result_id": result_ref.record_id, "path": _REPORT_PATH}),
    ]
    if authority:
        records.append(
            (
                RecordRef("human_method_authorization", "authorization:primary"),
                {
                    "record_type": "human_method_authorization",
                    "record_id": "authorization:primary",
                    "actor_id": "human:method-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": {
                        "record_type": "analysis",
                        "record_id": authority_analysis_id,
                    },
                    "procedure_ref": {
                        "record_type": "procedure",
                        "record_id": authority_procedure_id,
                    },
                    "independent_unit_definition_id": "unit-definition:participant",
                    "authorized_key_columns": list(key_columns),
                    "input_path": authority_input_path,
                    "input_content_digest": authority_input_digest or data_digest,
                },
            )
        )
    if second_authority:
        records.append(
            (
                RecordRef("human_method_authorization", "authorization:second"),
                {
                    "record_type": "human_method_authorization",
                    "record_id": "authorization:second",
                    "actor_id": "human:second",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis_ref.to_dict(),
                    "procedure_ref": procedure_ref.to_dict(),
                    "independent_unit_definition_id": "unit-definition:site",
                    "authorized_key_columns": ["site_id"],
                    "input_path": _DATA_PATH,
                    "input_content_digest": data_digest,
                },
            )
        )
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=analysis_file_ref,
                content=source_bytes,
                content_digest=sha256_digest(source_bytes),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
        material_inputs=(
            FrozenMaterialInput(
                path=_DATA_PATH,
                file_ref=data_file_ref,
                asset_identity_ref=data_identity_ref,
                content=data,
                content_digest=data_digest,
            ),
            FrozenMaterialInput(
                path="requirements.txt",
                file_ref=requirements_file_ref,
                asset_identity_ref=requirements_identity_ref,
                content=requirements,
                content_digest=requirements_digest,
            ),
        ),
    )


def _analyze(source: str, **context_kwargs: object):
    return analyze_dependence_python(_context(source, **context_kwargs))


@pytest.mark.parametrize(
    ("scipy_import", "callable_name"),
    [
        ("import scipy.stats as st", "st.ttest_ind"),
        ("from scipy import stats", "stats.mannwhitneyu"),
        ("from scipy import stats\nstats2 = stats", "stats2.ttest_ind"),
    ],
)
def test_exact_import_aliases_and_sc2_operand_bindings_are_proposed(
    scipy_import: str,
    callable_name: str,
) -> None:
    analysis = _analyze(_source(scipy_import=scipy_import, callable_name=callable_name))
    assert analysis.state == "proposal"
    assert analysis.certificate is not None
    procedure = analysis.certificate.procedure_call
    assert procedure.resolved_callable == (
        "scipy.stats.mannwhitneyu"
        if callable_name.endswith("mannwhitneyu")
        else "scipy.stats.ttest_ind"
    )
    assert set(procedure.positional_argument_tokens) == {
        item[0] for item in procedure.positional_argument_frame_bindings
    }
    assert {item[1] for item in procedure.positional_argument_frame_bindings} == {
        analysis.certificate.frame_lineage.output_token
    }


@pytest.mark.parametrize(
    ("scipy_import", "callable_name", "expected_outcome"),
    [
        ("import scipy.stats as st", "st.ttest_ind", "evaluation_candidate"),
        ("from scipy import stats", "stats.mannwhitneyu", "evaluation_candidate"),
    ],
)
def test_row_independent_registry_entries_reach_the_expected_core_outcome(
    scipy_import: str,
    callable_name: str,
    expected_outcome: str,
) -> None:
    context = _context(_source(scipy_import=scipy_import, callable_name=callable_name))
    discharged = discharge_dependence_proposal(analyze_dependence_python(context), context)
    assert discharged.state == "verified"
    assert discharged.case is not None
    assert evaluate_dependence_case(discharged.case).outcome == expected_outcome


def test_regression_n8_paired_procedure_operand_is_a_named_gap() -> None:
    data = b"participant_id,site_id,a,b\np1,s1,1,2\np1,s1,2,3\np2,s2,4,5\np2,s2,5,6\n"
    context = _context(
        _source(callable_name="st.ttest_rel"),
        data=data,
    )
    analysis = analyze_dependence_python(context)
    discharged = discharge_dependence_proposal(analysis, context)
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert analysis.unsupported_constructs == ("paired-procedure-operand-unverified",)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert evaluate_dependence_case(discharged.case).outcome == "unsupported"


def test_regression_n8_controller_refuses_forged_required_safeguard_proposal() -> None:
    context = _context(_source())
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    assert analysis.certificate is not None
    certificate = analysis.certificate
    forged_procedure = replace(
        certificate.procedure_call,
        resolved_callable="scipy.stats.ttest_rel",
        unit_operand_columns=certificate.case_binding.authorized_key_columns,
    )
    forged = replace(
        analysis,
        certificate=replace(certificate, procedure_call=forged_procedure),
    )
    discharged = discharge_dependence_proposal(forged, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("paired-procedure-operand-unverified",)


@pytest.mark.parametrize(
    "reader",
    [
        'rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", encoding="utf-8")))',
        'rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))',
        'rows = list(csv.DictReader(open("inputs/data.csv", encoding="utf-8", newline="")))',
        'with Path("inputs/data.csv").open(newline="", encoding="utf-8") as handle:\n'
        "    rows = list(csv.DictReader(handle))",
    ],
)
def test_only_the_two_certified_reader_models_reach_trusted_discharge(reader: str) -> None:
    context = _context(_source(reader=reader))
    analysis = analyze_dependence_python(context)
    discharged = discharge_dependence_proposal(analysis, context)
    assert discharged.state == "verified"
    assert discharged.verified_certificate is not None


@pytest.mark.parametrize(
    "injected",
    [
        "def helper(value):\n    return value",
        "def wrapper(left, right):\n    return st.ttest_ind(left, right)",
        "rows.append({})",
        "rows[0] = rows[1]",
        "for row in rows:\n    rows = rows",
        "while rows:\n    break",
    ],
)
def test_helpers_wrappers_mutation_and_loop_carried_state_abstain(injected: str) -> None:
    analysis = _analyze(_source(before_operands=injected))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert analysis.effects
    assert all(effect.opaque and effect.writes == frozenset({"*"}) for effect in analysis.effects)


def test_walrus_anywhere_in_the_live_tree_abstains() -> None:
    analysis = _analyze(_source(before_operands="changed = (copy := rows)"))
    assert analysis.state == "unsupported"
    assert "module-ban-or-dynamic-binding" in analysis.unsupported_constructs


@pytest.mark.parametrize(
    "injected",
    [
        "st = csv",
        "test = st.ttest_ind",
        "st.ttest_ind = st.mannwhitneyu",
    ],
)
def test_callable_rebinding_or_callable_aliasing_abstains(injected: str) -> None:
    analysis = _analyze(_source(before_call=injected))
    assert analysis.state == "unsupported"


def test_repeated_import_binding_and_bare_scipy_import_abstain() -> None:
    rebound = _source(scipy_import="import scipy.stats as st\nfrom scipy import stats as st")
    bare = _source(scipy_import="import scipy")
    assert _analyze(rebound).state == "unsupported"
    assert _analyze(bare).state == "unsupported"


@pytest.mark.parametrize(
    "reader",
    [
        'rows = list(csv.DictReader(Path("inputs/data.csv").open()))',
        'rows = list(csv.DictReader(Path("inputs/data.csv").open(encoding="utf-8")))',
        'rows = list(csv.DictReader(Path("inputs/data.csv").read_text().splitlines()))',
    ],
)
def test_reader_without_exact_utf8_and_newline_binding_abstains(reader: str) -> None:
    assert _analyze(_source(reader=reader)).state == "unsupported"


def test_regression_r1_controller_alone_supplies_trusted_authority() -> None:
    source = _source()
    authorized_context = _context(source)
    analysis = analyze_dependence_python(authorized_context)
    assert analysis.state == "proposal"
    assert analysis.certificate is not None
    assert not hasattr(analysis.certificate.case_binding, "authority")

    discharged = discharge_dependence_proposal(analysis, authorized_context)
    assert discharged.state == "verified"
    assert len(discharged.trusted_authorizations) == 1

    no_trusted_authority = discharge_dependence_proposal(
        analysis,
        _context(source, authority=False),
    )
    assert no_trusted_authority.state == "unsupported"
    assert no_trusted_authority.verified_certificate is None


@pytest.mark.parametrize(
    "reader",
    [
        'rows = list(csv.DictReader(open("inputs/data.csv", encoding="utf-8")))',
        'rows = list(csv.DictReader(Path("inputs/data.csv").open(encoding="utf-8")))',
        'rows = list(csv.DictReader(open("inputs/data.csv", encoding="utf-8", newline=None)))',
        'rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8")))',
    ],
)
def test_regression_r5_universal_newline_reader_is_named_and_refused(reader: str) -> None:
    analysis = _analyze(_source(reader=reader))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert "universal-newline-reader" in analysis.unsupported_constructs


def test_unmaterialized_dictreader_iterator_cannot_claim_two_full_domain_operands() -> None:
    reader = 'rows = csv.DictReader(Path("inputs/data.csv").open(encoding="utf-8", newline=""))'
    analysis = _analyze(_source(reader=reader))
    assert analysis.state == "unsupported"
    assert "unmaterialized-csv-reader-iterator" in analysis.unsupported_constructs


def test_one_element_tuple_identity_is_the_only_tuple_passing_form() -> None:
    accepted = _analyze(_source(before_operands="unit_rows, = rows,", frame_name="unit_rows"))
    rejected = _analyze(_source(before_operands="left, right = rows, rows"))
    assert accepted.state == "proposal"
    assert accepted.certificate is not None
    assert [item.operation for item in accepted.certificate.frame_lineage.transforms] == [
        "identity"
    ]
    assert rejected.state == "unsupported"


@pytest.mark.parametrize(
    "transform",
    [
        'filtered = [row for row in rows if row["site_id"] == "s1"]',
        "filtered = rows.merge(rows)",
        "filtered = rows.sample(2)",
        'filtered = rows.drop_duplicates("participant_id")',
        "filtered = rows[1:]",
    ],
)
def test_filter_merge_sample_dedup_and_slice_all_abstain(transform: str) -> None:
    analysis = _analyze(_source(before_operands=transform))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None


@pytest.mark.parametrize("method", ["mean", "first"])
def test_regression_n3_groupby_is_a_named_future_route(method: str) -> None:
    source = _source(
        before_operands=f'unit_rows = rows.groupby("participant_id").{method}()',
        frame_name="unit_rows",
    )
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert "unit-level-aggregation-unrecognized" in analysis.unsupported_constructs
    assert analysis.effects
    assert all(effect.opaque and effect.writes == frozenset({"*"}) for effect in analysis.effects)


def test_groupby_on_non_authorized_key_never_discharges_the_safeguard() -> None:
    source = _source(
        before_operands='unit_rows = rows.groupby("site_id").mean()',
        frame_name="unit_rows",
    )
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.certificate is None
    assert "unit-level-aggregation-unrecognized" in analysis.unsupported_constructs


def test_pandas_reader_is_the_named_unsupported_gap() -> None:
    source = "\n".join(
        (
            "import pandas as pd",
            'rows = pd.read_csv("inputs/data.csv")',
            "result = rows",
        )
    )
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.unsupported_constructs == ("pandas-frame-model",)


def test_string_formula_cannot_be_treated_as_a_registered_procedure() -> None:
    analysis = _analyze(_source(call='result = st.ttest_ind("value ~ site_id", rows)'))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None


@pytest.mark.parametrize(
    "call",
    [
        "result = st.ttest_ind(group_a, group_b, group_a)",
        "result = st.ttest_ind(group_a, group_b, equal_var=False)",
        'result = getattr(st, "ttest_ind")(group_a, group_b)',
    ],
)
def test_unregistered_signature_or_dynamic_dispatch_abstains(call: str) -> None:
    analysis = _analyze(_source(call=call))
    assert analysis.state == "unsupported"
    assert analysis.certificate is None


def test_missing_or_multiple_authority_lists_candidates_without_selecting_one() -> None:
    no_authority = _analyze(_source(), authority=False)
    ambiguous = _analyze(_source(), second_authority=True)
    for analysis in (no_authority, ambiguous):
        assert analysis.state == "question"
        assert analysis.certificate is None
        assert {"participant_id", "site_id"} <= set(analysis.candidate_key_columns)
        assert "candidate_unit_key:none-of-these" in analysis.unresolved_dimensions
        assert analysis.case is not None
        assert evaluate_dependence_case(analysis.case).outcome == "question"


@pytest.mark.parametrize(
    "context_kwargs",
    [
        {"authority_input_path": "inputs/other.csv"},
        {"authority_input_digest": "sha256:" + "0" * 64},
    ],
)
def test_mismatched_authority_input_remains_a_key_question(
    context_kwargs: dict[str, object],
) -> None:
    analysis = _analyze(_source(), **context_kwargs)
    assert analysis.state == "question"
    assert analysis.certificate is None
    assert analysis.case is not None
    assert analysis.case.unit_definition_state == "unknown"
    assert "candidate_unit_key:none-of-these" in analysis.unresolved_dimensions


def test_multiple_procedure_calls_with_conflicting_frame_conclusions_are_a_question() -> None:
    source = _source(
        before_call="direct = st.mannwhitneyu(group_a, group_b)",
    )
    analysis = _analyze(source)
    assert analysis.state == "question"
    assert analysis.certificate is None
    assert "conflicting-procedure-calls" in analysis.unresolved_dimensions


def test_competing_diagnostic_sink_cannot_stand_in_for_the_selected_result() -> None:
    source = _source(
        after_call='Path("results/diagnostic.txt").write_text(str(result), encoding="utf-8")'
    )
    analysis = _analyze(source)
    assert analysis.state == "question"
    assert analysis.certificate is None
    assert "selected-result-sink" in analysis.unresolved_dimensions


def test_proven_dead_branch_does_not_invalidate_a_live_closed_lineage() -> None:
    source = _source(before_operands="if False:\n    rows.append({})")
    analysis = _analyze(source)
    assert analysis.state == "proposal"
    assert analysis.certificate is not None
    assert analysis.certificate.dead_syntactic_construct_tokens
    assert analysis.certificate.dead_syntactic_construct_tokens <= (
        analysis.certificate.all_syntactic_construct_tokens
    )


def test_try_except_around_fit_abstains() -> None:
    analysis = _analyze(
        _source(
            call="try:\n"
            "    result = st.ttest_ind(group_a, group_b)\n"
            "except Exception:\n"
            "    result = st.mannwhitneyu(group_a, group_b)"
        )
    )
    assert analysis.state == "unsupported"
    assert "try-except-around-analysis" in analysis.unsupported_constructs


@pytest.mark.parametrize(
    "injected",
    [
        "import os\nos.system('echo no')",
        "import subprocess\nsubprocess.run(['echo', 'no'])",
        "dynamic = __import__('scipy.stats')",
    ],
)
def test_os_system_subprocess_and_dynamic_import_hit_module_bans(injected: str) -> None:
    analysis = _analyze(_source(before_operands=injected))
    assert analysis.state == "unsupported"
    assert analysis.effects
    assert all(effect.writes == frozenset({"*"}) for effect in analysis.effects)


@pytest.mark.parametrize(
    "requirements",
    [b"scipy\n", b"scipy>=1.14\n", b"scipy==1.17.1\n", b""],
)
def test_unpinned_or_unsupported_scipy_version_is_unsupported(requirements: bytes) -> None:
    analysis = _analyze(_source(), requirements=requirements)
    assert analysis.state == "unsupported"
    assert "unsupported-or-unpinned-scipy-version" in analysis.unsupported_constructs


@pytest.mark.parametrize(
    "requirements",
    [
        b"scipy==1.14.0\nscipy>=1.14\n",
        b"scipy==1.14.0\nscipy==1.14.0\n",
        b"scipy[extra]==1.14.0\n",
    ],
)
def test_conflicting_or_nonexact_scipy_declarations_abstain(requirements: bytes) -> None:
    assert _analyze(_source(), requirements=requirements).state == "unsupported"


def test_dynamic_fstring_payload_cannot_establish_the_selected_sink() -> None:
    source = _source().replace(
        'Path("results/report.txt").write_text(str(result), encoding="utf-8")',
        'Path("results/report.txt").write_text(f"{result} {side_effect()}", encoding="utf-8")',
    )
    analysis = _analyze(source)
    assert analysis.state == "unsupported"
    assert analysis.certificate is None


def test_membership_scale_above_v1_bound_uses_the_named_unsupported_gap() -> None:
    rows = b"".join(f"p{index % 2},s1,{index},{index + 1}\n".encode() for index in range(10_001))
    context = _context(
        _source(),
        data=b"participant_id,site_id,a,b\n" + rows,
    )
    analysis = analyze_dependence_python(context)
    discharged = discharge_dependence_proposal(analysis, context)
    assert analysis.state == "proposal"
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("membership-scale-above-v1-bound",)
    assert evaluate_dependence_case(discharged.case).outcome == "unsupported"


def test_end_to_end_reaches_all_four_dependence_outcomes() -> None:
    repeated_context = _context(_source())
    repeated = discharge_dependence_proposal(
        analyze_dependence_python(repeated_context), repeated_context
    )
    assert repeated.state == "verified" and repeated.case is not None
    assert evaluate_dependence_case(repeated.case).outcome == "evaluation_candidate"

    unique_data = b"participant_id,site_id,a,b\np1,s1,1,2\np2,s1,2,3\np3,s2,4,5\n"
    unique_context = _context(_source(), data=unique_data)
    unique = discharge_dependence_proposal(
        analyze_dependence_python(unique_context), unique_context
    )
    assert unique.state == "verified" and unique.case is not None
    assert evaluate_dependence_case(unique.case).outcome == "covered_negative"

    question_context = _context(_source(), authority=False)
    question = discharge_dependence_proposal(
        analyze_dependence_python(question_context), question_context
    )
    assert question.case is not None
    assert evaluate_dependence_case(question.case).outcome == "question"

    unsupported_context = _context(_source(), requirements=b"scipy==1.17.1\n")
    unsupported = discharge_dependence_proposal(
        analyze_dependence_python(unsupported_context), unsupported_context
    )
    assert unsupported.case is not None
    assert evaluate_dependence_case(unsupported.case).outcome == "unsupported"


def test_controller_fact_channel_is_external_and_digest_drift_abstains() -> None:
    context = _context(_source())
    analysis = analyze_dependence_python(context)
    assert analysis.certificate is not None
    assert not hasattr(analysis.certificate, "proven_multiplicity_facts")
    assert verify_dependence_certificate(analysis.certificate) is None
    data_material = context.material_inputs[0]
    with pytest.raises(ValueError):
        replace(data_material, content=data_material.content + b"p3,s3,1,2\n")


def test_controller_refuses_cross_context_dependency_or_source_drift() -> None:
    context = _context(_source())
    analysis = analyze_dependence_python(context)
    requirements_drift = _context(_source(), requirements=b"scipy==1.17.1\n")
    source_drift = _context(_source(after_call="reported = result"))
    for drifted_context in (requirements_drift, source_drift):
        discharged = discharge_dependence_proposal(analysis, drifted_context)
        assert discharged.state == "unsupported"
        assert discharged.case is not None
        assert discharged.case.unsupported_constructs == ("frozen-context-drift",)


def test_controller_rechecks_the_bound_package_pin_evidence_identity() -> None:
    context = _context(_source())
    analysis = analyze_dependence_python(context)
    assert analysis.certificate is not None
    procedure = analysis.certificate.procedure_call
    forged_version = replace(procedure.package_version, evidence_ids=("dependency-pin:forged",))
    forged = replace(
        analysis,
        certificate=replace(
            analysis.certificate,
            procedure_call=replace(procedure, package_version=forged_version),
        ),
    )
    discharged = discharge_dependence_proposal(forged, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("frozen-context-drift",)


@pytest.mark.parametrize(
    ("record_type", "record_id"),
    [
        ("claim", "claim:forged"),
        ("result", "result:unrelated"),
    ],
)
def test_regression_n1_affected_target_must_match_the_selected_frozen_record(
    record_type: str,
    record_id: str,
) -> None:
    context = _context(_source())
    if record_id == "result:unrelated":
        unrelated_ref = RecordRef(record_type, record_id)
        context = replace(
            context,
            base_records=(
                *context.base_records,
                FrozenBaseRecord.from_record(
                    unrelated_ref,
                    {"result_id": record_id, "path": "results/unrelated.txt"},
                ),
            ),
        )
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    assert analysis.certificate is not None
    certificate = analysis.certificate
    forged_ref = replace(
        certificate.case_binding.affected_target_ref,
        record_type=record_type,
        record_id=record_id,
    )
    forged = replace(
        analysis,
        certificate=replace(
            certificate,
            case_binding=replace(certificate.case_binding, affected_target_ref=forged_ref),
            sinks=tuple(
                replace(sink, affected_target_ref=forged_ref) for sink in certificate.sinks
            ),
        ),
    )
    discharged = discharge_dependence_proposal(forged, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("frozen-context-drift",)


def test_regression_n2_trusted_procedure_record_mismatch_refuses_discharge() -> None:
    context = _context(_source(), procedure_callable="scipy.stats.ttest_rel")
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    discharged = discharge_dependence_proposal(analysis, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("frozen-context-drift",)


def test_regression_n2_missing_trusted_analysis_record_refuses_discharge() -> None:
    context = _context(_source())
    context = replace(
        context,
        base_records=tuple(
            record for record in context.base_records if record.ref.record_type != "analysis"
        ),
    )
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    discharged = discharge_dependence_proposal(analysis, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("frozen-context-drift",)


@pytest.mark.parametrize(
    "context_kwargs",
    [
        {"authority_analysis_id": "analysis:other"},
        {"authority_procedure_id": "procedure:other"},
    ],
)
def test_trusted_authority_reference_mismatch_refuses_at_controller(
    context_kwargs: dict[str, object],
) -> None:
    context = _context(_source(), **context_kwargs)
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    discharged = discharge_dependence_proposal(analysis, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("frozen-context-drift",)


def test_regression_n4_distinct_key_scale_has_its_own_named_gap() -> None:
    rows = b"".join(f"p{index},s1,{index},{index + 1}\n".encode() for index in range(5_001))
    context = _context(
        _source(),
        data=b"participant_id,site_id,a,b\n" + rows,
    )
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    discharged = discharge_dependence_proposal(analysis, context)
    assert discharged.state == "unsupported"
    assert discharged.case is not None
    assert discharged.case.unsupported_constructs == ("distinct-key-scale-above-v1-bound",)


def test_regression_n5_write_handle_has_its_own_non_reader_branch() -> None:
    direct_sink = 'Path("results/report.txt").write_text(str(result), encoding="utf-8")'
    write_handle_sink = (
        'with Path("results/report.txt").open("w", encoding="utf-8") as output:\n'
        "    output.write(str(result))"
    )
    source = _source().replace(direct_sink, write_handle_sink)
    context = _context(source)
    analysis = analyze_dependence_python(context)
    assert analysis.state == "proposal"
    assert discharge_dependence_proposal(analysis, context).state == "verified"

    dynamic_newline = write_handle_sink.replace(
        'encoding="utf-8")', 'encoding="utf-8", newline=setting)'
    )
    refused = _analyze(_source().replace(direct_sink, dynamic_newline))
    assert refused.state == "unsupported"
    assert "unsupported-write-handle" in refused.unsupported_constructs
    assert "universal-newline-reader" not in refused.unsupported_constructs
