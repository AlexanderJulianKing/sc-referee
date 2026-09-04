from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.core.ids import semantic_digest
from sc_referee.method_contract_draft import (
    DRAFT_PROVENANCE_EXTENSION_KEY,
    DRAFT_RULE_ID,
    MULTIPLE_TESTING_CANDIDATE_ID,
    MULTIPLE_TESTING_CHECK_ID,
    MethodContractDraftError,
    confirmed_draft_provenance,
    draft_scientific_requirement_profile,
    validate_draft_provenance,
)

_PROTOCOL = """# Study protocol

This study compares the two groups recorded in the `arm` column of `data.csv`.
The pre-declared outcome family, in this fixed order, is: alpha_mg, beta_pct, gamma_score.
Each outcome is compared between the two groups. The named outcomes form one outcome
family; per-outcome comparisons over this family require complete-family control of the
family-wise error from multiple comparisons.
"""

_HEADER = "subject_id,arm,study_half,alpha_mg,beta_pct,gamma_score\n"


def _project(root: Path, *, protocol: str = _PROTOCOL, header: str = _HEADER) -> Path:
    project = root / "project"
    project.mkdir(parents=True, exist_ok=True)
    (project / "PROTOCOL.md").write_text(protocol, encoding="utf-8")
    (project / "data.csv").write_text(header + "s1,a,1,1.0,2.0,3.0\n", encoding="utf-8")
    (project / "analysis.py").write_text(
        "# outcome_columns = ['not_an_outcome']\nprint('never read')\n", encoding="utf-8"
    )
    return project


def test_named_outcome_family_drafts_the_exact_profile(tmp_path: Path) -> None:
    draft = draft_scientific_requirement_profile(
        _project(tmp_path), task="PROTOCOL.md", material_input="data.csv"
    )

    assert draft.profile == {
        "profile_id": "scientific_check_requirement_v1",
        "profile_version": "1.2.0",
        "check_id": MULTIPLE_TESTING_CHECK_ID,
        "candidate_id": MULTIPLE_TESTING_CANDIDATE_ID,
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": "data.csv",
                "group_contrast_column": "arm",
                "outcome_columns": ["alpha_mg", "beta_pct", "gamma_score"],
                "family_member_rule": "one-two-group-test-per-named-outcome-column",
                "correction_scope": "complete-authorized-family",
            }
        },
    }
    assert draft.protocol_order_matches_header_order
    assert draft.provenance["draft_rule"] == DRAFT_RULE_ID
    assert draft.provenance["confirmed_by"] is None
    assert draft.provenance["drafted_profile_digest"] == semantic_digest(draft.profile)


def test_identifier_and_design_label_columns_are_never_outcomes(tmp_path: Path) -> None:
    draft = draft_scientific_requirement_profile(
        _project(tmp_path), task="PROTOCOL.md", material_input="data.csv"
    )
    authority = draft.profile["semantic_role_authority"]["authorized_test_family"]

    assert "subject_id" not in authority["outcome_columns"]
    assert "study_half" not in authority["outcome_columns"]
    assert "arm" not in authority["outcome_columns"]
    excluded = {item.column: item.reason for item in draft.excluded}
    assert set(excluded) == {"subject_id", "arm", "study_half"}
    assert "identifier-shaped" in excluded["subject_id"]
    assert "two-group contrast" in excluded["arm"]
    assert "does not name it as an outcome" in excluded["study_half"]


def test_protocol_naming_no_outcome_family_refuses_to_draft(tmp_path: Path) -> None:
    protocol = (
        "# Study protocol\n\nThis study compares the two groups recorded in the `arm` column of "
        "`data.csv`. Measurements were taken at every visit.\n"
    )
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, protocol=protocol),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "does not name an outcome family" in str(error.value)


def test_protocol_naming_no_group_column_refuses_to_draft(tmp_path: Path) -> None:
    protocol = (
        "# Study protocol\n\nThe pre-declared outcome family, in this fixed order, is: "
        "alpha_mg, beta_pct, gamma_score.\n"
    )
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, protocol=protocol),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "does not name a two-group contrast column" in str(error.value)


def test_outcome_name_absent_from_the_header_refuses_to_draft(tmp_path: Path) -> None:
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, header="subject_id,arm,alpha_mg,beta_pct,delta_units\n"),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "not in the header" in str(error.value)
    assert "gamma_score" in str(error.value)


def test_group_name_absent_from_the_header_refuses_to_draft(tmp_path: Path) -> None:
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, header="subject_id,cohort,alpha_mg,beta_pct,gamma_score\n"),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "names group column arm" in str(error.value)


def test_protocol_naming_an_identifier_as_an_outcome_refuses_to_draft(tmp_path: Path) -> None:
    protocol = _PROTOCOL.replace("alpha_mg,", "subject_id, alpha_mg,")
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, protocol=protocol),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "identifier-shaped columns as outcomes" in str(error.value)


def test_protocol_naming_the_group_column_as_an_outcome_refuses_to_draft(tmp_path: Path) -> None:
    protocol = _PROTOCOL.replace("alpha_mg,", "arm, alpha_mg,")
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, protocol=protocol),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "group column arm as an outcome" in str(error.value)


def test_fewer_than_three_named_outcomes_refuses_to_draft(tmp_path: Path) -> None:
    protocol = _PROTOCOL.replace("alpha_mg, beta_pct, gamma_score", "alpha_mg, beta_pct")
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, protocol=protocol),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "fewer than three outcomes" in str(error.value)


def test_protocol_naming_a_different_material_input_refuses_to_draft(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "adjusted_pvalues.csv").write_text(
        "subject_id,arm,study_half,alpha_mg,beta_pct,gamma_score\n", encoding="utf-8"
    )
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            project, task="PROTOCOL.md", material_input="adjusted_pvalues.csv"
        )

    assert "names data.csv as the material input" in str(error.value)


def test_conflicting_named_families_refuse_to_draft(tmp_path: Path) -> None:
    protocol = _PROTOCOL + (
        "\nThe pre-declared outcome family, in this fixed order, is: alpha_mg, beta_pct.\n"
    )
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path, protocol=protocol),
            task="PROTOCOL.md",
            material_input="data.csv",
        )

    assert "more than one different outcome family" in str(error.value)


def test_unsupported_check_and_candidate_refuse_to_draft(tmp_path: Path) -> None:
    with pytest.raises(MethodContractDraftError) as error:
        draft_scientific_requirement_profile(
            _project(tmp_path),
            task="PROTOCOL.md",
            material_input="data.csv",
            check_id="check:founder-orientation-before-hmm-emission",
            candidate_id="repair-before-emission",
        )

    assert "the draft rule covers only" in str(error.value)


def test_paths_outside_the_repository_are_refused(tmp_path: Path) -> None:
    project = _project(tmp_path)
    with pytest.raises(MethodContractDraftError):
        draft_scientific_requirement_profile(
            project, task="../PROTOCOL.md", material_input="data.csv"
        )
    with pytest.raises(MethodContractDraftError):
        draft_scientific_requirement_profile(
            project, task="PROTOCOL.md", material_input="/etc/hosts"
        )


def _sealed_multiple_testing_cases(project_root: Path) -> list[tuple[str, Path]]:
    envelopes = (
        "blind-envelope-17-2026-08-30",
        "blind-envelope-18-2026-09-01",
    )
    cases: list[tuple[str, Path]] = []
    for envelope in envelopes:
        root = project_root / "evaluation" / "development" / envelope / "cases"
        for case in sorted(root.iterdir()):
            if (case / "profile_1_2_0.json").is_file():
                cases.append((f"{envelope}/{case.name}", case))
    return cases


def test_draft_rule_reproduces_every_sealed_envelope_profile(project_root: Path) -> None:
    cases = _sealed_multiple_testing_cases(project_root)
    assert len(cases) == 30

    differences: list[str] = []
    for label, case in cases:
        sealed = (case / "profile_1_2_0.json").read_bytes()
        authority = json.loads(sealed)["semantic_role_authority"]["authorized_test_family"]
        try:
            draft = draft_scientific_requirement_profile(
                case / "project",
                task="PROTOCOL.md",
                material_input=authority["material_input_path"],
            )
        except MethodContractDraftError as error:  # pragma: no cover - reported, not expected
            differences.append(f"{label}: refused ({error})")
            continue
        if draft.profile_bytes() != sealed:
            differences.append(f"{label}: drafted profile differs from the sealed profile")

    assert not differences, "\n".join(differences)


def test_draft_provenance_validation_is_closed(tmp_path: Path) -> None:
    draft = draft_scientific_requirement_profile(
        _project(tmp_path), task="PROTOCOL.md", material_input="data.csv"
    )
    assert validate_draft_provenance(draft.provenance) == draft.provenance

    for mutate in (
        lambda value: value.update({"draft_rule": "other/v9"}),
        lambda value: value.update({"provenance_version": "9.9.9"}),
        lambda value: value.update({"confirmed_by": "scientist:self"}),
        lambda value: value.pop("drafted_profile_digest"),
        lambda value: value.update({"unexpected": 1}),
    ):
        broken = json.loads(json.dumps(draft.provenance))
        mutate(broken)
        with pytest.raises(MethodContractDraftError):
            validate_draft_provenance(broken)

    broken_header = json.loads(json.dumps(draft.provenance))
    broken_header["draft_sources"]["material_input_header"] = ["renamed"]
    with pytest.raises(MethodContractDraftError):
        validate_draft_provenance(broken_header)


def test_confirmation_records_whether_the_human_edited_the_draft(tmp_path: Path) -> None:
    draft = draft_scientific_requirement_profile(
        _project(tmp_path), task="PROTOCOL.md", material_input="data.csv"
    )

    unedited = confirmed_draft_provenance(
        draft.provenance, profile=draft.profile, actor_id="scientist:alex"
    )
    assert unedited["human_edited_after_draft"] is False
    assert unedited["confirmed_by"] == {"actor_kind": "human", "actor_id": "scientist:alex"}
    assert unedited["confirmed_profile_digest"] == unedited["drafted_profile_digest"]

    edited = json.loads(json.dumps(draft.profile))
    edited["semantic_role_authority"]["authorized_test_family"]["outcome_columns"] = [
        "alpha_mg",
        "beta_pct",
        "gamma_score",
    ][::-1]
    confirmed = confirmed_draft_provenance(
        draft.provenance, profile=edited, actor_id="scientist:alex"
    )
    assert confirmed["human_edited_after_draft"] is True
    assert confirmed["confirmed_profile_digest"] != confirmed["drafted_profile_digest"]


def test_cli_drafts_then_confirms_and_the_lock_records_the_confirmation(tmp_path: Path) -> None:
    project = _project(tmp_path)
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    provenance_path = tmp_path / "profile.json.provenance.json"

    drafted = runner.invoke(
        app,
        [
            "draft-profile",
            str(project),
            "--task",
            "PROTOCOL.md",
            "--material-input",
            "data.csv",
            "-o",
            str(profile_path),
        ],
    )
    assert drafted.exit_code == 0, drafted.output
    assert (
        "Outcome family (3, in protocol order): alpha_mg, beta_pct, gamma_score" in drafted.stdout
    )
    assert "Group column (two-group contrast): arm" in drafted.stdout
    assert "Excluded columns and why:" in drafted.stdout
    assert "No analysis code was read." in drafted.stdout
    assert profile_path.is_file()
    assert provenance_path.is_file()

    frozen = runner.invoke(
        app,
        [
            "method-contract",
            str(project),
            "--task",
            "PROTOCOL.md",
            "--profile",
            str(profile_path),
            "--draft-provenance",
            str(provenance_path),
            "--actor-id",
            "scientist:alex",
            "--output",
            str(tmp_path / "method-contract"),
        ],
    )
    assert frozen.exit_code == 0, frozen.output
    assert "Confirmed the unedited draft" in frozen.stdout

    bundle = json.loads((tmp_path / "method-contract" / "audit.bundle.json").read_text())
    extensions = bundle["scientific_contracts"][0]["extensions"]
    provenance = extensions[DRAFT_PROVENANCE_EXTENSION_KEY]
    assert provenance["draft_rule"] == DRAFT_RULE_ID
    assert provenance["confirmed_by"] == {"actor_kind": "human", "actor_id": "scientist:alex"}
    assert provenance["human_edited_after_draft"] is False
    assert provenance["draft_sources"]["material_input_header"] == [
        "subject_id",
        "arm",
        "study_half",
        "alpha_mg",
        "beta_pct",
        "gamma_score",
    ]
    assert extensions["x-method-profile-resolution-status"] == "resolved"
    assert bundle["claims"] == []
    assert bundle["publication_surfaces"] == []


def test_cli_refusal_prints_the_material_question_path_and_writes_nothing(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        protocol="# Study protocol\n\nWe compare the arms on several measurements.\n",
    )
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"

    result = runner.invoke(
        app,
        [
            "draft-profile",
            str(project),
            "--task",
            "PROTOCOL.md",
            "--material-input",
            "data.csv",
            "-o",
            str(profile_path),
        ],
    )

    assert result.exit_code == 2
    assert "Refused to draft a profile" in result.output
    assert "sc-referee questions <new-output>" in result.output
    assert "Do not answer it yourself." in result.output
    assert not profile_path.exists()
    assert not (tmp_path / "profile.json.provenance.json").exists()


def test_confirmation_freeze_without_provenance_is_unchanged(tmp_path: Path) -> None:
    project = _project(tmp_path)
    draft = draft_scientific_requirement_profile(
        project, task="PROTOCOL.md", material_input="data.csv"
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_bytes(draft.profile_bytes())
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "method-contract",
            str(project),
            "--task",
            "PROTOCOL.md",
            "--profile",
            str(profile_path),
            "--actor-id",
            "scientist:alex",
            "--output",
            str(tmp_path / "method-contract"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Confirmed the" not in result.stdout
    bundle = json.loads((tmp_path / "method-contract" / "audit.bundle.json").read_text())
    assert DRAFT_PROVENANCE_EXTENSION_KEY not in bundle["scientific_contracts"][0]["extensions"]


def test_draft_provenance_requires_a_scientific_requirement_profile(tmp_path: Path) -> None:
    project = _project(tmp_path)
    draft = draft_scientific_requirement_profile(
        project, task="PROTOCOL.md", material_input="data.csv"
    )
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(draft.provenance), encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "method-contract",
            str(project),
            "--task",
            "PROTOCOL.md",
            "--draft-provenance",
            str(provenance_path),
            "--output",
            str(tmp_path / "method-contract"),
        ],
    )

    assert result.exit_code != 0
    assert "draft provenance is accepted only" in result.output
