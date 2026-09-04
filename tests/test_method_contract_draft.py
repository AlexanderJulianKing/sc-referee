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
    validate_draft_provenance,
    validate_proposed_requirement_profile,
)

_PROTOCOL = """# Study protocol

This study compares the two groups recorded in the `arm` column of `data.csv`.
The pre-declared outcome family, in this fixed order, is: alpha_mg, beta_pct, gamma_score.
Each outcome is compared between the two groups. The named outcomes form one outcome
family; per-outcome comparisons over this family require complete-family control of the
family-wise error from multiple comparisons.
"""

_HEADER = "subject_id,arm,study_half,alpha_mg,beta_pct,gamma_score\n"
_OUTCOMES = ["alpha_mg", "beta_pct", "gamma_score"]
_AGENT = "agent:claude-code"


def _project(root: Path, *, protocol: str = _PROTOCOL, header: str = _HEADER) -> Path:
    project = root / "project"
    project.mkdir(parents=True, exist_ok=True)
    (project / "PROTOCOL.md").write_text(protocol, encoding="utf-8")
    (project / "data.csv").write_text(header + "s1,a,1,1.0,2.0,3.0\n", encoding="utf-8")
    (project / "analysis.py").write_text(
        "# outcome_columns = ['not_an_outcome']\nprint('never read')\n", encoding="utf-8"
    )
    return project


def _validate(project: Path, **overrides: object) -> object:
    kwargs: dict[str, object] = {
        "task": "PROTOCOL.md",
        "material_input": "data.csv",
        "group_column": "arm",
        "outcome_columns": list(_OUTCOMES),
        "proposed_by": _AGENT,
    }
    kwargs.update(overrides)
    return validate_proposed_requirement_profile(project, **kwargs)  # type: ignore[arg-type]


def _refusal(project: Path, **overrides: object) -> str:
    with pytest.raises(MethodContractDraftError) as error:
        _validate(project, **overrides)
    return str(error.value)


# --- accepted proposal -------------------------------------------------------------------


def test_a_grounded_proposal_is_accepted_exactly_as_proposed(tmp_path: Path) -> None:
    draft = _validate(_project(tmp_path))

    assert draft.profile == {  # type: ignore[attr-defined]
        "profile_id": "scientific_check_requirement_v1",
        "profile_version": "1.2.0",
        "check_id": MULTIPLE_TESTING_CHECK_ID,
        "candidate_id": MULTIPLE_TESTING_CANDIDATE_ID,
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": "data.csv",
                "group_contrast_column": "arm",
                "outcome_columns": _OUTCOMES,
                "family_member_rule": "one-two-group-test-per-named-outcome-column",
                "correction_scope": "complete-authorized-family",
            }
        },
    }
    provenance = draft.provenance  # type: ignore[attr-defined]
    assert provenance["draft_rule"] == DRAFT_RULE_ID
    assert provenance["proposed_by"] == _AGENT
    assert provenance["drafted_by"]["tool"] == "sc-referee"
    assert provenance["confirmed_by"] is None
    assert provenance["drafted_profile_digest"] == semantic_digest(draft.profile)  # type: ignore[attr-defined]
    assert provenance["grounding"] == {
        "alpha_mg": [4],
        "arm": [3],
        "beta_pct": [4],
        "gamma_score": [4],
    }


def test_the_proposed_order_is_preserved_and_never_reordered(tmp_path: Path) -> None:
    reversed_family = list(reversed(_OUTCOMES))
    draft = _validate(_project(tmp_path), outcome_columns=reversed_family)

    authority = draft.profile["semantic_role_authority"]["authorized_test_family"]  # type: ignore[attr-defined]
    assert authority["outcome_columns"] == reversed_family


def test_design_columns_are_accepted_when_the_protocol_names_them_and_the_caller_does_not_exclude(
    tmp_path: Path,
) -> None:
    protocol = (
        "# Study protocol\n\n"
        "Two groups are recorded in the `arm` column of `data.csv`.\n"
        "The outcome family is plot, replicate, alpha_mg.\n"
    )
    project = _project(
        tmp_path, protocol=protocol, header="plot,replicate,arm,alpha_mg,subject_id\n"
    )

    draft = _validate(project, outcome_columns=["plot", "replicate", "alpha_mg"])

    authority = draft.profile["semantic_role_authority"]["authorized_test_family"]  # type: ignore[attr-defined]
    assert authority["outcome_columns"] == ["plot", "replicate", "alpha_mg"]


# --- one test per refusal ----------------------------------------------------------------


def test_refuses_a_column_missing_from_the_header(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), outcome_columns=["alpha_mg", "beta_pct", "delta_units"])
    assert "proposed column delta_units is not in the material input header" in reason


def test_refuses_a_case_mismatched_column_and_names_the_header_spelling(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), outcome_columns=["Alpha_mg", "beta_pct", "gamma_score"])
    assert "proposed column Alpha_mg is not in the material input header" in reason
    assert "the header has alpha_mg" in reason


def test_refuses_a_header_with_case_folded_duplicate_names(tmp_path: Path) -> None:
    reason = _refusal(
        _project(tmp_path, header="subject_id,arm,alpha_mg,Alpha_mg,beta_pct,gamma_score\n")
    )
    assert "differ only by case" in reason
    assert "alpha_mg" in reason and "Alpha_mg" in reason


def test_refuses_a_header_with_exact_duplicate_names(tmp_path: Path) -> None:
    reason = _refusal(
        _project(tmp_path, header="subject_id,arm,alpha_mg,alpha_mg,beta_pct,gamma_score\n")
    )
    assert "duplicate column names" in reason


def test_refuses_a_header_with_a_blank_column_name(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path, header="subject_id,,arm,alpha_mg,beta_pct,gamma_score\n"))
    assert "blank column name" in reason


def test_refuses_a_byte_order_marked_header(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "data.csv").write_bytes(
        b"\xef\xbb\xbf" + _HEADER.encode("utf-8") + b"s1,a,1,1.0,2.0,3.0\n"
    )
    reason = _refusal(project)
    assert "byte-order mark" in reason


def test_refuses_a_column_that_does_not_occur_verbatim_in_the_protocol(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), outcome_columns=["alpha_mg", "beta_pct", "study_half"])
    assert "proposed column study_half does not occur verbatim in PROTOCOL.md" in reason


def test_refuses_a_group_column_that_does_not_occur_verbatim_in_the_protocol(
    tmp_path: Path,
) -> None:
    protocol = _PROTOCOL.replace("`arm` column", "`treatment assignment` column")
    project = _project(
        tmp_path, protocol=protocol, header="subject_id,arm,alpha_mg,beta_pct,gamma_score\n"
    )
    reason = _refusal(project)
    assert "proposed column arm does not occur verbatim" in reason


def test_refuses_when_the_group_column_is_also_proposed_as_an_outcome(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), outcome_columns=["arm", "beta_pct", "gamma_score"])
    assert "the group column arm is also proposed as an outcome" in reason


def test_refuses_an_identifier_shaped_column_as_an_outcome(tmp_path: Path) -> None:
    protocol = _PROTOCOL.replace("alpha_mg,", "subject_id, alpha_mg,")
    reason = _refusal(
        _project(tmp_path, protocol=protocol),
        outcome_columns=["subject_id", "alpha_mg", "beta_pct"],
    )
    assert "identifier-shaped columns are proposed as outcomes: subject_id" in reason


def test_refuses_a_caller_excluded_column_as_an_outcome(tmp_path: Path) -> None:
    protocol = (
        "# Study protocol\n\n"
        "Two groups are recorded in the `arm` column of `data.csv`.\n"
        "The outcome family is plot, replicate, alpha_mg.\n"
    )
    project = _project(
        tmp_path, protocol=protocol, header="plot,replicate,arm,alpha_mg,subject_id\n"
    )
    reason = _refusal(
        project,
        outcome_columns=["plot", "replicate", "alpha_mg"],
        exclusions={"replicate": "design label, not a measured outcome"},
    )
    assert "columns flagged with --exclude are proposed as outcomes" in reason
    assert "replicate: design label, not a measured outcome" in reason


def test_refuses_an_exclusion_for_a_column_absent_from_the_header(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), exclusions={"nowhere": "not a real column"})
    assert "--exclude names nowhere, which is not a header column" in reason


def test_refuses_an_exclusion_with_an_empty_reason(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), exclusions={"study_half": "   "})
    assert "--exclude study_half has an empty reason" in reason


def test_refuses_a_repeated_outcome_column(tmp_path: Path) -> None:
    reason = _refusal(
        _project(tmp_path), outcome_columns=["alpha_mg", "alpha_mg", "beta_pct", "gamma_score"]
    )
    assert "repeats a column" in reason


def test_refuses_fewer_than_three_outcomes(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), outcome_columns=["alpha_mg", "beta_pct"])
    assert "fewer than three columns" in reason


def test_refuses_when_the_protocol_names_another_csv(tmp_path: Path) -> None:
    protocol = _PROTOCOL + "\nAdjusted p-values are written to `adjusted_pvalues.csv`.\n"
    reason = _refusal(_project(tmp_path, protocol=protocol))
    assert "protocol names another material input: adjusted_pvalues.csv" in reason


def test_refuses_when_the_protocol_names_only_another_csv(tmp_path: Path) -> None:
    protocol = (
        "# Study protocol\n\nThe material input is `other.csv`. "
        "The group comparison column is `arm`.\n"
        "The pre-declared outcome family is: alpha_mg, beta_pct, gamma_score.\n"
    )
    reason = _refusal(_project(tmp_path, protocol=protocol))
    assert "protocol names another material input: other.csv" in reason


@pytest.mark.parametrize(
    ("sentence", "column"),
    [
        ("The following are excluded: gamma_score.", "gamma_score"),
        ("They are not declared outcomes: alpha_mg.", "alpha_mg"),
        ("Every outcome except beta_pct is analysed.", "beta_pct"),
        ("Secondary outcomes are gamma_score and others.", "gamma_score"),
        ("We exclude alpha_mg from the family.", "alpha_mg"),
    ],
)
def test_refuses_when_a_tripwire_word_shares_a_sentence_with_a_proposed_column(
    tmp_path: Path, sentence: str, column: str
) -> None:
    reason = _refusal(_project(tmp_path, protocol=_PROTOCOL + "\n" + sentence + "\n"))
    assert f"protocol qualifies {column}; confirm by hand" in reason


def test_refuses_a_negated_two_group_statement_about_the_group_column(tmp_path: Path) -> None:
    protocol = (
        "# Study protocol\n\n"
        "There are not two groups recorded in the `arm` column; it has three levels.\n"
        "The outcome family is: alpha_mg, beta_pct, gamma_score.\n"
    )
    reason = _refusal(_project(tmp_path, protocol=protocol))
    assert "protocol qualifies arm; confirm by hand" in reason


def test_refuses_a_missing_proposed_by(tmp_path: Path) -> None:
    reason = _refusal(_project(tmp_path), proposed_by="   ")
    assert "--proposed-by must identify the proposing agent" in reason


def test_refuses_an_unsupported_check_and_candidate(tmp_path: Path) -> None:
    reason = _refusal(
        _project(tmp_path),
        check_id="check:founder-orientation-before-hmm-emission",
        candidate_id="repair-before-emission",
    )
    assert "the validation rule covers only" in reason


def test_refuses_paths_outside_the_repository(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert "must be a normalized repository-relative path" in _refusal(
        project, task="../PROTOCOL.md"
    )
    assert "repository-relative POSIX path" in _refusal(project, material_input="/etc/hosts")


def test_refuses_a_material_input_that_is_not_a_csv(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "data.tsv").write_text("subject_id\tarm\n", encoding="utf-8")
    assert "must name a .csv file" in _refusal(project, material_input="data.tsv")


# --- sealed-envelope reproduction --------------------------------------------------------


def _sealed_multiple_testing_cases(project_root: Path) -> list[tuple[str, Path]]:
    envelopes = ("blind-envelope-17-2026-08-30", "blind-envelope-18-2026-09-01")
    cases: list[tuple[str, Path]] = []
    for envelope in envelopes:
        root = project_root / "evaluation" / "development" / envelope / "cases"
        for case in sorted(root.iterdir()):
            if (case / "profile_1_2_0.json").is_file():
                cases.append((f"{envelope}/{case.name}", case))
    return cases


def test_every_sealed_envelope_proposal_is_accepted_byte_for_byte(project_root: Path) -> None:
    cases = _sealed_multiple_testing_cases(project_root)
    assert len(cases) == 30

    differences: list[str] = []
    for label, case in cases:
        sealed = (case / "profile_1_2_0.json").read_bytes()
        authority = json.loads(sealed)["semantic_role_authority"]["authorized_test_family"]
        try:
            draft = validate_proposed_requirement_profile(
                case / "project",
                task="PROTOCOL.md",
                material_input=authority["material_input_path"],
                group_column=authority["group_contrast_column"],
                outcome_columns=authority["outcome_columns"],
                proposed_by=_AGENT,
            )
        except MethodContractDraftError as error:  # pragma: no cover - reported, not expected
            differences.append(f"{label}: refused ({error})")
            continue
        if draft.profile_bytes() != sealed:
            differences.append(f"{label}: validated profile differs from the sealed profile")

    assert not differences, "\n".join(differences)


# --- provenance --------------------------------------------------------------------------


def test_draft_provenance_validation_is_closed(tmp_path: Path) -> None:
    draft = _validate(_project(tmp_path))
    assert validate_draft_provenance(draft.provenance) == draft.provenance  # type: ignore[attr-defined]

    for mutate in (
        lambda value: value.update({"draft_rule": "method-contract-draft/outcome-family/v1"}),
        lambda value: value.update({"provenance_version": "1.0.0"}),
        lambda value: value.update({"confirmed_by": "scientist:self"}),
        lambda value: value.update({"proposed_by": "  "}),
        lambda value: value.update({"drafted_by": {"tool": "forger", "tool_version": "x"}}),
        lambda value: value.update({"grounding": {}}),
        lambda value: value.pop("drafted_profile_digest"),
        lambda value: value.update({"unexpected": 1}),
    ):
        broken = json.loads(json.dumps(draft.provenance))  # type: ignore[attr-defined]
        mutate(broken)
        with pytest.raises(MethodContractDraftError):
            validate_draft_provenance(broken)

    for field, value in (
        ("task_content_digest", "not-a-digest"),
        ("material_input_header", ["renamed"]),
    ):
        broken = json.loads(json.dumps(draft.provenance))  # type: ignore[attr-defined]
        broken["draft_sources"][field] = value
        with pytest.raises(MethodContractDraftError):
            validate_draft_provenance(broken)


def test_confirmation_refuses_a_sidecar_bound_to_other_sources(tmp_path: Path) -> None:
    project = _project(tmp_path)
    draft = _validate(project)

    other = _project(tmp_path / "other")
    (other / "PROTOCOL.md").write_text(_PROTOCOL + "\nA later revision.\n", encoding="utf-8")
    with pytest.raises(MethodContractDraftError) as changed:
        confirmed_draft_provenance(
            draft.provenance,  # type: ignore[attr-defined]
            repository=other,
            task="PROTOCOL.md",
            profile=draft.profile,  # type: ignore[attr-defined]
            actor_id="scientist:alex",
        )
    assert "changed after the draft" in str(changed.value)

    (project / "data.csv").write_text(
        "subject_id,arm,study_half,alpha_mg,beta_pct,gamma_score,delta\n", encoding="utf-8"
    )
    with pytest.raises(MethodContractDraftError) as header:
        confirmed_draft_provenance(
            draft.provenance,  # type: ignore[attr-defined]
            repository=project,
            task="PROTOCOL.md",
            profile=draft.profile,  # type: ignore[attr-defined]
            actor_id="scientist:alex",
        )
    assert "header changed after the draft" in str(header.value)


def test_confirmation_records_whether_the_human_edited_the_proposal(tmp_path: Path) -> None:
    project = _project(tmp_path)
    draft = _validate(project)

    unedited = confirmed_draft_provenance(
        draft.provenance,  # type: ignore[attr-defined]
        repository=project,
        task="PROTOCOL.md",
        profile=draft.profile,  # type: ignore[attr-defined]
        actor_id="scientist:alex",
    )
    assert unedited["human_edited_after_draft"] is False
    assert unedited["confirmed_by"] == {"actor_kind": "human", "actor_id": "scientist:alex"}
    assert unedited["proposed_by"] == _AGENT
    assert unedited["grounding"]["alpha_mg"] == [4]

    edited = json.loads(json.dumps(draft.profile))  # type: ignore[attr-defined]
    edited["semantic_role_authority"]["authorized_test_family"]["outcome_columns"] = list(
        reversed(_OUTCOMES)
    )
    confirmed = confirmed_draft_provenance(
        draft.provenance,  # type: ignore[attr-defined]
        repository=project,
        task="PROTOCOL.md",
        profile=edited,
        actor_id="scientist:alex",
    )
    assert confirmed["human_edited_after_draft"] is True
    assert confirmed["confirmed_profile_digest"] != confirmed["drafted_profile_digest"]


# --- CLI ---------------------------------------------------------------------------------


def _draft_argv(
    project: Path, output: Path, *extra: str, outcomes: list[str] | None = None
) -> list[str]:
    return [
        "draft-profile",
        str(project),
        "--task",
        "PROTOCOL.md",
        "--material-input",
        "data.csv",
        "--group-column",
        "arm",
        "--outcome-columns",
        ",".join(outcomes if outcomes is not None else _OUTCOMES),
        "--proposed-by",
        _AGENT,
        "-o",
        str(output),
        *extra,
    ]


def test_cli_drafts_then_confirms_and_the_lock_records_the_confirmation(tmp_path: Path) -> None:
    project = _project(tmp_path)
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"
    provenance_path = tmp_path / "profile.json.provenance.json"

    drafted = runner.invoke(app, _draft_argv(project, profile_path))
    assert drafted.exit_code == 0, drafted.output
    assert (
        "Outcome family (3, in proposed order): alpha_mg, beta_pct, gamma_score" in drafted.stdout
    )
    assert "Group column (two-group contrast): arm" in drafted.stdout
    assert "Proposed by: agent:claude-code" in drafted.stdout
    assert "Excluded columns and why:" in drafted.stdout
    assert "occurs verbatim in PROTOCOL.md, at these lines:" in drafted.stdout
    assert "did not read the protocol's prose and did not choose these columns" in drafted.stdout
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
    assert provenance["proposed_by"] == _AGENT
    assert provenance["confirmed_by"] == {"actor_kind": "human", "actor_id": "scientist:alex"}
    assert provenance["human_edited_after_draft"] is False
    assert provenance["grounding"]["arm"] == [3]
    assert extensions["x-method-profile-resolution-status"] == "resolved"
    assert bundle["claims"] == []
    assert bundle["publication_surfaces"] == []


def test_cli_exclude_flag_requires_a_reason(tmp_path: Path) -> None:
    project = _project(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app, _draft_argv(project, tmp_path / "profile.json", "--exclude", "study_half")
    )

    assert result.exit_code != 0
    assert "--exclude must be <name>=<reason>" in result.output


def test_cli_refusal_prints_the_material_question_path_and_writes_nothing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    runner = CliRunner()
    profile_path = tmp_path / "profile.json"

    result = runner.invoke(
        app,
        _draft_argv(project, profile_path, outcomes=["alpha_mg", "beta_pct", "study_half"]),
    )

    assert result.exit_code == 2
    assert "Refused the proposed profile" in result.output
    assert "Do not edit the protocol to make this refusal go away." in result.output
    assert "sc-referee questions <new-output>" in result.output
    assert "Do not answer it yourself." in result.output
    assert not profile_path.exists()
    assert not (tmp_path / "profile.json.provenance.json").exists()


def test_confirmation_freeze_without_provenance_is_unchanged(tmp_path: Path) -> None:
    project = _project(tmp_path)
    draft = _validate(project)
    profile_path = tmp_path / "profile.json"
    profile_path.write_bytes(draft.profile_bytes())  # type: ignore[attr-defined]
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
    draft = _validate(project)
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(draft.provenance), encoding="utf-8")  # type: ignore[attr-defined]
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
