from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.controller import replay, run_audit
from sc_referee.core.deadline_ledger import (
    LEDGER_FILENAME,
    load_deadline_ledger,
    verify_deadline_ledger,
)
from sc_referee.core.ids import semantic_digest
from sc_referee.interaction import (
    InteractionProtocolError,
    _validate_proposal,
    create_candidate_answer,
    create_structured_answer,
    lock_semantics,
    record_answer,
    resume_semantics,
    submit_proposal,
    work_packet,
    work_queue,
)
from sc_referee.method_contracts import (
    build_expected_count_profile,
    expected_count_dimension_values,
)
from sc_referee.version import SCHEMA_VERSION

# ADR-0069 check v2.0.0 recognizes the founder orientation from arithmetic:
# 372 of 480 markers agreeing with a stated 0.775 emission rate reads the
# supplied panel directly.
LD_WHITENED_REPORT = (
    "We used a Tukey biweight M-estimator on Cholesky-whitened residual innovations; "
    "this preserves the LD covariance.\n"
)
LD_WHITENED_SOURCE = (
    "from pathlib import Path\n"
    "from numpy.linalg import cholesky as factor_covariance\n"
    "from numpy.linalg import solve as triangular_solve\n"
    "from statsmodels.api import RLM as robust_fit\n"
    "from statsmodels.robust.norms import TukeyBiweight as redescending_norm\n"
    "ROOT = Path(__file__).resolve().parent\n"
    "def fit_model(ld_covariance, outcome_innovations, exposure_innovations):\n"
    "    factor = factor_covariance(ld_covariance)\n"
    "    y_white = triangular_solve(factor, outcome_innovations)\n"
    "    x_white = triangular_solve(factor, exposure_innovations)\n"
    "    return robust_fit(y_white, x_white, M=redescending_norm())\n"
    "def main():\n"
    f"    (ROOT / 'report.md').write_text({LD_WHITENED_REPORT!r})\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)


FOUNDER_ACCOUNTING_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of 0.775.\n"
)


def test_model_proposal_path_rejects_project_execution_packet(project_root: Path) -> None:
    item = json.loads(
        (
            project_root
            / "reference"
            / "schemas-v0.18.0"
            / "examples"
            / "work-item.project-execution.example.json"
        ).read_text(encoding="utf-8")
    )
    with pytest.raises(InteractionProtocolError, match="non-model"):
        _validate_proposal({}, item, {"record_type": "semantic_assertion"})


def _write_ambiguous_project(root: Path) -> None:
    (root / "report.md").write_text(
        "# Results\n\nTreatment increased yield relative to control.\n",
        encoding="utf-8",
    )
    (root / "alternate.md").write_text(
        "# Alternate\n\nTreatment decreased yield relative to control.\n",
        encoding="utf-8",
    )
    (root / "analysis.py").write_text("value = 1\n", encoding="utf-8")


def _write_linkable_project(root: Path) -> None:
    (root / "reports").mkdir()
    (root / "workflow").mkdir()
    (root / "reports" / "results.md").write_text(
        "# Results\n\ntreated increased expression relative to control.\n",
        encoding="utf-8",
    )
    (root / "workflow" / "data.csv").write_text(
        "group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8"
    )
    (root / "workflow" / "analysis.py").write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "value = difference(Path('data.csv'))\n",
        encoding="utf-8",
    )


def _write_expected_count_project(root: Path) -> None:
    (root / "report.md").write_text(
        "# Result\n\n"
        "At the queried 20 kb pixel, the mean case loop strength is **2.018599**, "
        "the mean control loop strength is **0.027571**, and the case-minus-control "
        "difference is **1.991029** log2 units.\n\n"
        "# Method\n\n"
        "For each replicate independently, I used the arithmetic mean of all other "
        "20 kb pixels at the same nine-bin separation as the expected count. The focal "
        "pixel was left out so that a true loop could not raise its own expected value "
        "in this small matrix.\n\n"
        "Pairs incident to bins with mappability below 0.80 were excluded from the "
        "background.\n\n"
        "An unfiltered leave-one-out mean gives case=1.186815, control=-0.789760, and "
        "delta=1.976575. A robust median on the quality-filtered background gives "
        "case=2.205261, control=0.233752, and delta=1.971509.\n",
        encoding="utf-8",
    )


def _write_claimless_expected_count_obligation_project(root: Path) -> None:
    (root / "task.md").write_text(
        "Estimate one interaction. Report three quantities: `case_loop_strength` "
        "(mean log2(observed/expected) across case replicates), "
        "`control_loop_strength` (mean log2(observed/expected) across control replicates), "
        "and `delta_loop_strength` (case minus control).\n",
        encoding="utf-8",
    )
    (root / "report.md").write_text(
        "# Result\n\n"
        "- `case_loop_strength`: 1.068707542693\n"
        "- `control_loop_strength`: -0.749712891584\n"
        "- `delta_loop_strength`: 1.818420434277\n\n"
        "# Method\n\n"
        "Observed is the focal count. Expected is the per-replicate arithmetic mean of all "
        "15 intrachromosomal 20 kb pixels at `dist_bin = 9`, including the focal pixel.\n\n"
        "# Sensitivity\n\n"
        "Excluding only the focal pixel from the expected gives case=1.186814997161, "
        "control=-0.789759677956, and delta=1.976574675117.\n",
        encoding="utf-8",
    )


def _proposal(packet: dict[str, object], *, object_value: object) -> dict[str, object]:
    work_item = packet["work_item"]
    assert isinstance(work_item, dict)
    bounded_packet = work_item["packet"]
    assert isinstance(bounded_packet, dict)
    source_refs = bounded_packet["source_refs"]
    assert isinstance(source_refs, list) and source_refs
    target_refs = work_item["target_refs"]
    assert isinstance(target_refs, list) and target_refs
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": "assertion:model-publication-proposal",
        "audit_run_id": packet["audit_run_id"],
        "subject_ref": copy.deepcopy(target_refs[0]),
        "predicate": "proposed_publication_surface",
        "object": object_value,
        "semantic_role": "inferred",
        "assertion_class": "implicit_scientific_inference",
        "epistemic_status": "proposed",
        "authority_scope": "none",
        "independently_checkable": False,
        "finding_eligibility": "ineligible",
        "verification": {"status": "not_checked", "method": "not_applicable"},
        "certainty": {
            "level": "low",
            "basis": "Filename evidence can support only a nonauthoritative proposal.",
        },
        "rationale": "One bounded candidate appears publication-like; the scientist must decide.",
        "source_refs": [copy.deepcopy(source_refs[0])],
        "provenance": {
            "actor": {"actor_kind": "model", "actor_id": "model:test"},
            "method": "bounded_semantic_proposal",
            "created_at": "2026-07-28T12:01:00Z",
            "tool": "test-model-adapter",
            "tool_version": "1.0.0",
        },
        "extensions": {
            "x-work-item-ref": {
                "record_type": "work_item",
                "record_id": work_item["work_item_id"],
            },
            "x-packet-digest": bounded_packet["packet_digest"],
            "x-prompt-template-digest": bounded_packet["prompt_template_digest"],
        },
    }


def _prepare(
    schema_root: Path, tmp_path: Path
) -> tuple[Path, Path, dict[str, object], dict[str, object], bytes]:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_ambiguous_project(repository)
    source = tmp_path / "source-audit"
    run_audit(repository, source, schema_root)
    parent_lock_before = (source / "semantic.lock.json").read_bytes()
    session = tmp_path / "interaction"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-28T12:00:00Z",
    )
    queue = work_queue(session, schema_root)
    assert queue["state"] == "parsed"
    assert len(queue["work_items"]) == 1
    work_item_id = queue["work_items"][0]["work_item_id"]
    packet = work_packet(session, work_item_id, schema_root)
    question = json.loads((source / "audit.bundle.json").read_text(encoding="utf-8"))[
        "material_questions"
    ][0]
    return repository, session, packet, question, parent_lock_before


def test_linked_prelock_packet_proposal_answer_lock_and_replay(
    schema_root: Path, tmp_path: Path
) -> None:
    repository, session, packet, question, parent_lock_before = _prepare(schema_root, tmp_path)
    del repository
    work_item = packet["work_item"]
    assert isinstance(work_item, dict)
    alternate_option = next(
        option for option in question["candidate_answers"] if option["label"] == "alternate.md"
    )
    report_option = next(
        option for option in question["candidate_answers"] if option["label"] == "report.md"
    )
    proposal = _proposal(packet, object_value=str(alternate_option["value"]))

    submit_proposal(
        session,
        str(work_item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-28T12:01:00Z",
    )
    answer = create_candidate_answer(
        session,
        str(question["question_id"]),
        str(report_option["answer_id"]),
        "scientist:test",
        schema_root,
        answered_at="2026-07-28T12:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(session, schema_root, locked_at="2026-07-28T12:03:00Z")

    assert (tmp_path / "source-audit" / "semantic.lock.json").read_bytes() == parent_lock_before
    assert [item["state"] for item in bundle["audit_runs"]] == [
        "created",
        "snapshotted",
        "inventoried",
        "parsed",
        "semantics_proposed",
        "awaiting_answers",
        "semantics_resolved",
        "semantics_locked",
        "detected",
        "reported",
        "complete",
    ]
    assert bundle["answers"] == [answer]
    assert bundle["semantic_assertions"] == [proposal]
    assert bundle["semantic_assertions"][0]["epistemic_status"] == "proposed"
    assert bundle["semantic_assertions"][0]["object"] == alternate_option["value"]
    selected_ref = bundle["publication_surfaces"][0]["selection"]["selected_surface_refs"][0]
    assert selected_ref["record_id"] == report_option["value"]
    assert bundle["findings"] == []
    html = (session / "report.html").read_text(encoding="utf-8")
    assert "Material questions" in html
    assert "Status:</strong> answered" in html
    assert "Questions blocking interpretation" not in html
    lock = json.loads((session / "semantic.lock.json").read_text(encoding="utf-8"))
    assert lock["model_access_after_lock"] is False
    assert len(lock["model_calls"]) == 1

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "semantic_assertions",
        "scientific_contracts",
        "work_items",
        "answers",
        "findings",
        "conditional_concerns",
        "material_questions",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]

    with pytest.raises(InteractionProtocolError, match="semantic lock already exists"):
        submit_proposal(session, str(work_item["work_item_id"]), proposal, schema_root)


def test_publication_answer_preserves_and_binds_precomputed_observed_lineage(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_linkable_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root)
    assert len(source_bundle["observed_results"]) == 1
    assert source_bundle["claims"] == []

    session = tmp_path / "session"
    resume_semantics(source, repository, session, schema_root)
    question = source_bundle["material_questions"][0]
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    submit_proposal(
        session,
        str(item["work_item_id"]),
        _proposal(packet, object_value="artifact:model-choice"),
        schema_root,
    )
    option = next(
        item for item in question["candidate_answers"] if item["label"] == "reports/results.md"
    )
    answer = create_candidate_answer(
        session,
        str(question["question_id"]),
        str(option["answer_id"]),
        "scientist:test",
        schema_root,
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(session, schema_root)

    assert bundle["observed_results"] == source_bundle["observed_results"]
    assert bundle["claims"][0]["lineage"]["status"] == "partial"
    assert (
        bundle["claims"][0]["lineage"]["result_refs"][0]["record_id"]
        == (bundle["observed_results"][0]["observed_result_id"])
    )
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update(epistemic_status="accepted"), "must remain proposed"),
        (
            lambda value: value["extensions"].update({"x-packet-digest": "sha256:" + "0" * 64}),
            "packet digest mismatch",
        ),
        (
            lambda value: value.update(
                source_refs=[
                    {
                        "source_kind": "file_span",
                        "locator": "outside.md:1",
                        "path": "outside.md",
                        "content_digest": "sha256:" + "0" * 64,
                        "start_line": 1,
                        "end_line": 1,
                    }
                ]
            ),
            "outside the bounded packet",
        ),
        (
            lambda value: value.update(authority_scope="executed_computation"),
            "cannot establish observed computation",
        ),
    ],
)
def test_controller_rejects_unbounded_or_authoritative_model_proposals(
    schema_root: Path,
    tmp_path: Path,
    mutation: object,
    message: str,
) -> None:
    _, session, packet, _, _ = _prepare(schema_root, tmp_path)
    work_item = packet["work_item"]
    assert isinstance(work_item, dict)
    proposal = _proposal(packet, object_value="artifact:any")
    assert callable(mutation)
    mutation(proposal)

    with pytest.raises((InteractionProtocolError, ValueError), match=message):
        submit_proposal(session, str(work_item["work_item_id"]), proposal, schema_root)


def test_answer_option_digest_and_authority_scope_are_controller_enforced(
    schema_root: Path, tmp_path: Path
) -> None:
    _, session, packet, question, _ = _prepare(schema_root, tmp_path)
    work_item = packet["work_item"]
    assert isinstance(work_item, dict)
    submit_proposal(
        session,
        str(work_item["work_item_id"]),
        _proposal(packet, object_value="artifact:any"),
        schema_root,
    )
    option = question["candidate_answers"][0]
    answer = create_candidate_answer(
        session,
        str(question["question_id"]),
        str(option["answer_id"]),
        "scientist:test",
        schema_root,
    )

    tampered = copy.deepcopy(answer)
    tampered["answer_value"] = "artifact:not-the-option"
    with pytest.raises(InteractionProtocolError, match="digest mismatch"):
        record_answer(session, tampered, schema_root)

    escaped = copy.deepcopy(answer)
    escaped["authority_scope"]["semantic_dimensions"] = ["executed_result"]
    digest_input = copy.deepcopy(escaped)
    digest_input.pop("answer_digest")
    escaped["answer_digest"] = semantic_digest(digest_input)
    with pytest.raises(InteractionProtocolError, match="authority scope escapes"):
        record_answer(session, escaped, schema_root)

    mismatch = copy.deepcopy(answer)
    mismatch["answer_value"] = "artifact:not-the-option"
    digest_input = copy.deepcopy(mismatch)
    digest_input.pop("answer_digest")
    mismatch["answer_digest"] = semantic_digest(digest_input)
    with pytest.raises(InteractionProtocolError, match="option and value"):
        record_answer(session, mismatch, schema_root)


def test_typed_interaction_cli_round_trip(schema_root: Path, tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_ambiguous_project(repository)
    source = tmp_path / "source"
    run_audit(repository, source, schema_root)
    session = tmp_path / "session"
    runner = CliRunner()

    resumed = runner.invoke(
        app,
        [
            "resume",
            str(source),
            "--repository",
            str(repository),
            "--output",
            str(session),
            "--schema-root",
            str(schema_root),
        ],
    )
    assert resumed.exit_code == 0, resumed.output
    queued = runner.invoke(app, ["work-queue", str(session), "--schema-root", str(schema_root)])
    assert queued.exit_code == 0, queued.output
    queue = json.loads(queued.output)
    work_item_id = queue["work_items"][0]["work_item_id"]
    packet_result = runner.invoke(
        app,
        [
            "work-packet",
            str(session),
            "--work-item-id",
            work_item_id,
            "--schema-root",
            str(schema_root),
        ],
    )
    assert packet_result.exit_code == 0, packet_result.output
    packet = json.loads(packet_result.output)
    proposal = _proposal(packet, object_value="artifact:model-choice")
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    submitted = runner.invoke(
        app,
        [
            "submit-proposals",
            str(session),
            "--work-item-id",
            work_item_id,
            "--proposal",
            str(proposal_path),
            "--schema-root",
            str(schema_root),
        ],
    )
    assert submitted.exit_code == 0, submitted.output

    source_bundle = json.loads((source / "audit.bundle.json").read_text(encoding="utf-8"))
    question = source_bundle["material_questions"][0]
    option = next(item for item in question["candidate_answers"] if item["label"] == "report.md")
    answered = runner.invoke(
        app,
        [
            "record-answer",
            str(session),
            "--question-id",
            question["question_id"],
            "--select-option",
            option["answer_id"],
            "--actor-id",
            "scientist:cli-test",
            "--schema-root",
            str(schema_root),
        ],
    )
    assert answered.exit_code == 0, answered.output
    locked = runner.invoke(app, ["lock-semantics", str(session), "--schema-root", str(schema_root)])
    assert locked.exit_code == 0, locked.output
    status = runner.invoke(
        app, ["status", str(session), "--json", "--schema-root", str(schema_root)]
    )
    assert status.exit_code == 0, status.output
    payload = json.loads(status.output)
    assert payload["run_state"] == "complete"
    assert payload["publication_surface_status"] == "resolved"


def test_structured_scientist_answer_flattens_contract_without_overwriting_proposal(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_ambiguous_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = source_bundle["material_questions"][0]
    assert question["unknown_semantic_dimension"] == "scientific_contract"
    session = tmp_path / "contract-session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-28T13:00:00Z",
    )
    queued = work_queue(session, schema_root)
    work_item = queued["work_items"][0]
    packet = work_packet(session, work_item["work_item_id"], schema_root)
    proposed_values = {"target_population": "Greenhouse plots"}
    proposal = _proposal(packet, object_value=json.dumps(proposed_values, sort_keys=True))
    proposal["predicate"] = "proposed_scientific_contract"
    proposal["object"] = proposed_values
    submit_proposal(
        session,
        work_item["work_item_id"],
        proposal,
        schema_root,
        submitted_at="2026-07-28T13:01:00Z",
    )
    dimensions = work_item["packet"]["unresolved_dimensions"]
    scientist_values = {
        dimension: f"Scientist-declared {dimension.replace('_', ' ')}" for dimension in dimensions
    }
    scientist_values["target_population"] = "All randomized field plots"
    with pytest.raises(InteractionProtocolError, match="outside the bounded WorkItem"):
        create_structured_answer(
            session,
            question["question_id"],
            {"unbounded_dimension": "invented"},
            "scientist:principal-investigator",
            schema_root,
        )
    values_path = tmp_path / "scientist-values.json"
    values_path.write_text(json.dumps(scientist_values), encoding="utf-8")
    recorded = CliRunner().invoke(
        app,
        [
            "record-structured-answer",
            str(session),
            "--question-id",
            question["question_id"],
            "--values",
            str(values_path),
            "--actor-id",
            "scientist:principal-investigator",
            "--schema-root",
            str(schema_root),
        ],
    )
    assert recorded.exit_code == 0, recorded.output
    bundle = lock_semantics(session, schema_root, locked_at="2026-07-28T13:03:00Z")

    assertions = bundle["semantic_assertions"]
    assert assertions[0] == proposal
    accepted = [item for item in assertions if item["epistemic_status"] == "accepted"]
    assert len(accepted) == len(dimensions)
    target_assertion = next(
        item for item in accepted if item["predicate"] == "intended_target_population"
    )
    assert target_assertion["object"] == "All randomized field plots"
    assert target_assertion["authority_scope"] == "scientific_intent"
    assert target_assertion["finding_eligibility"] == "ineligible"
    assert proposal["object"] == {"target_population": "Greenhouse plots"}
    contract = bundle["scientific_contracts"][0]
    assert contract["status"] == "resolved"
    assert all(slot["state"] == "known" for slot in contract["dimensions"].values())
    grades = bundle["claims"][0]["lineage"]["grades"]
    assert grades["semantic_origin"]["status"] == "complete"
    assert grades["execution_origin"]["status"] == "missing"
    assert bundle["claims"][0]["lineage"]["status"] == "partial"
    assert bundle["executions"] == []
    assert bundle["findings"] == []
    assert [item for item in bundle["material_questions"] if item["status"] == "open"] == []

    replayed = replay(session / "semantic.lock.json", tmp_path / "contract-replay", schema_root)
    for field in (
        "semantic_assertions",
        "scientific_contracts",
        "answers",
        "material_questions",
        "findings",
    ):
        assert replayed[field] == bundle[field]


def test_single_line_report_question_answer_and_disclosure_are_replay_stable(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(FOUNDER_ACCOUNTING_REPORT, encoding="utf-8")
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:founder-orientation-before-hmm-emission"
    )
    source_method_coverage = next(
        item
        for item in source_bundle["coverage_records"][0]["detector_coverage"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert source_method_coverage["targets_total"] == 1
    assert source_method_coverage["targets_evaluated"] == 0

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-30T16:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="use_supplied_founder_alleles_directly_in_hmm_emission",
    )
    proposal["predicate"] = "proposed_scale_and_orientation"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-30T16:01:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"scale_and_orientation": "repair_ril_founder_orientation_before_hmm_emission"},
        "scientist:test",
        schema_root,
        answered_at="2026-07-30T16:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-30T16:03:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "scale_and_orientation"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == "One exact review-scoped method incompatibility"
    assert ledger_disclosures[0]["coverage_status"] == "covered"
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == "exact_conflict_candidate"
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    (
        "report_text",
        "check_id",
        "dimension",
        "observed_value",
        "required_value",
    ),
    [
        (
            "Expected is the per-replicate arithmetic mean of all other 20 kb pixels at "
            "the same genomic distance.\n",
            "check:expected-count-background-construction",
            "measurement_model",
            "same_stratum_arithmetic_mean_expected_count",
            "negative_binomial_glm_predicted_expected_count",
        ),
        (
            "The focal target was included in its own expected-count background.\n",
            "check:expected-count-focal-target-handling",
            "selection_process",
            "include_focal_target_in_expected_count_background",
            "exclude_focal_target_from_expected_count_training",
        ),
    ],
)
def test_expected_count_answers_create_bounded_replayable_incompatibilities(
    schema_root: Path,
    tmp_path: Path,
    report_text: str,
    check_id: str,
    dimension: str,
    observed_value: str,
    required_value: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(report_text, encoding="utf-8")
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == check_id
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T20:00:00Z",
    )
    items = work_queue(session, schema_root)["work_items"]
    assert len(items) == 1
    packet = work_packet(session, str(items[0]["work_item_id"]), schema_root)
    proposal = _proposal(packet, object_value=observed_value)
    proposal["predicate"] = f"proposed_{dimension}"
    submit_proposal(
        session,
        str(items[0]["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T20:01:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {dimension: required_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T20:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T20:03:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == dimension
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == "One exact review-scoped method incompatibility"
    ledger = ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]
    assert ledger["outcome"] == "exact_conflict_candidate"
    assert ledger["observed"] == observed_value
    assert ledger["requirement"] == required_value

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


def test_static_selected_report_writer_survives_answer_lock_and_replay(
    schema_root: Path, tmp_path: Path
) -> None:
    # The founder-orientation check became a single reported-text plane at
    # check v2.0.0, so the two-plane writer-scope path is exercised here by the
    # LD-whitening check, which still carries a Python static-source adapter.
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(LD_WHITENED_REPORT, encoding="utf-8")
    (repository / "analysis.py").write_text(LD_WHITENED_SOURCE, encoding="utf-8")
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:ld-covariance-whitening-before-robust-fit"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T06:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="ld_covariance_cholesky_whitening_before_robust_fit",
    )
    proposal["predicate"] = "proposed_measurement_model"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T06:01:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"measurement_model": "diagonal_or_unwhitened_robust_fit"},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T06:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T06:03:00Z",
    )

    ledger = next(
        disclosure["extensions"]["x-posthoc-method-ledger"]
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger")
    )
    assert bundle["findings"] == []
    assert ledger["outcome"] == "exact_conflict_candidate"
    assert ledger["authority"]["observed"] == "corroborated_report_and_static_source"
    assert [edge["relation"] for edge in ledger["scope_join_path"]] == [
        "contains_unique_static_selected_output_writer",
        "declares_selected_output_artifact",
        "selected_by_publication_surface",
    ]
    assert {source_ref["path"] for source_ref in ledger["source_refs"]} == {
        "analysis.py",
        "report.md",
    }
    method_result = next(
        result
        for result in bundle["detector_results"]
        if result["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert method_result["state"] == "evaluation_finding_candidate"
    assert method_result["extensions"]["x-production-finding-permitted"] is False
    assert len(method_result["counterevidence_execution"]) == 10
    assert bundle["findings"] == []
    method_coverage = next(
        item
        for item in bundle["coverage_records"][0]["detector_coverage"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert method_coverage["targets_total"] == 1
    assert method_coverage["targets_evaluated"] == 1

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "answers",
        "semantic_assertions",
        "detector_results",
        "disclosures",
        "findings",
    ):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    (
        "report_text",
        "check_id",
        "dimension",
        "observed_value",
        "answer_value",
        "expected_title",
        "expected_outcome",
    ),
    [
        (
            "# Phase-split MVMR\n\nUnion of phase-1 LD-conditional joint-effect signals at "
            "p<5e-8; phase-2 joint exposure coefficients and matching joint disease "
            "coefficients.\n",
            "check:phase-split-mvmr-instrument-construction",
            "measurement_model",
            "phase1_ld_conditional_signal_union_with_phase2_joint_coefficients",
            "phase1_ld_conditional_signal_union_with_phase2_joint_coefficients",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "# Phase-split MVMR\n\nUnion of phase-1 LD-conditional joint-effect signals at "
            "p<5e-8; phase-2 joint exposure coefficients and matching joint disease "
            "coefficients.\n",
            "check:phase-split-mvmr-instrument-construction",
            "measurement_model",
            "phase1_ld_conditional_signal_union_with_phase2_joint_coefficients",
            "phase1_marginal_signal_union_with_phase2_marginal_coefficients",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
        (
            "# MVMR analysis\n\n## Primary estimator\n\nZero-intercept generalized least "
            "squares with the full supplied LD-derived disease covariance.\n",
            "check:mvmr-residual-heterogeneity-estimator",
            "dependence_structure",
            "zero_intercept_generalized_ivw_or_gls",
            "zero_intercept_generalized_ivw_or_gls",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "# MVMR analysis\n\n## Primary estimator\n\nZero-intercept generalized least "
            "squares with the full supplied LD-derived disease covariance.\n",
            "check:mvmr-residual-heterogeneity-estimator",
            "dependence_structure",
            "zero_intercept_generalized_ivw_or_gls",
            "redescending_robust_m_estimator_on_ld_whitened_innovations",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_mvmr_scientist_answers_and_disclosures_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    report_text: str,
    check_id: str,
    dimension: str,
    observed_value: str,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(report_text, encoding="utf-8")
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == check_id
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T04:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(packet, object_value=observed_value)
    proposal["predicate"] = f"proposed_{dimension}"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T04:01:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {dimension: answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T04:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T04:03:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == dimension
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    ("answer_value", "expected_title", "expected_outcome"),
    [
        (
            "substantive_risk_strata_only_with_availability_variables_diagnostic",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "include_named_availability_variables_in_direct_standardization_cells",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_direct_standardization_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(
        "Completed partners were analyzed within ancestry by family-history tier and "
        "standardized to the corresponding counts in all 500 roster rows. Site and wave were "
        "treated as testing-selection variables, not biological prevalence predictors.\n",
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:direct-standardization-conditioning-set"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T03:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value=("substantive_risk_strata_only_with_availability_variables_diagnostic"),
    )
    proposal["predicate"] = "proposed_target_population"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T03:01:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"target_population": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T03:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T03:03:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "target_population"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    ("answer_value", "expected_title", "expected_outcome"),
    [
        (
            "aggregate_observed_distribution_then_joint_calibration",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "constrained_joint_calibration_within_each_poststratum_then_standardize",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_poststratified_calibration_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(
        "We directly standardized completed-test call distributions over target-population "
        "cells. We then jointly deconvolved the standardized distributions with the matched "
        "control matrices.\n",
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:poststratified-misclassification-estimator"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-30T20:10:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="aggregate_observed_distribution_then_joint_calibration",
    )
    proposal["predicate"] = "proposed_measurement_model"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-30T20:11:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"measurement_model": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-30T20:12:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-30T20:13:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "measurement_model"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    ("answer_value", "expected_title", "expected_outcome"),
    [
        (
            "terminate_path_at_unobserved_or_filtered_intervals",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "preserve_within_sequence_path_across_unobserved_intervals",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_transition_path_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(
        "A transition is counted only at an exactly touching callable A/B boundary. "
        "Masked or uncalled intervals terminate the path.\n",
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:within-sequence-transition-path-continuity"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T03:10:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="terminate_path_at_unobserved_or_filtered_intervals",
    )
    proposal["predicate"] = "proposed_dependence_structure"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T03:11:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"dependence_structure": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T03:12:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T03:13:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "dependence_structure"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    (
        "report_text",
        "observed_value",
        "answer_value",
        "expected_title",
        "expected_outcome",
    ),
    [
        (
            "The full-cohort representation is continuous posterior expected copy dosage, "
            "P(copy=1) + 2*P(copy=2), not an integer hard call.\n",
            "continuous_posterior_expected_copy_dosage",
            "continuous_posterior_expected_copy_dosage",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "The full-cohort representation is continuous posterior expected copy dosage, "
            "P(copy=1) + 2*P(copy=2), not an integer hard call.\n",
            "continuous_posterior_expected_copy_dosage",
            "integer_hard_copy_state_as_numeric_dosage",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
        (
            "The full-cohort representation is continuous posterior expected copy dosage, "
            "P(copy=1) + 2*P(copy=2), not an integer hard call.\n",
            "continuous_posterior_expected_copy_dosage",
            "direct_continuous_calibrated_copy_dosage",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
        (
            "The full-cohort representation is continuous calibrated copy dosage. RidgeCV "
            "calibration models produced the downstream quantitative copy exposure.\n",
            "direct_continuous_calibrated_copy_dosage",
            "direct_continuous_calibrated_copy_dosage",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
    ],
)
def test_classifier_copy_dosage_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    report_text: str,
    observed_value: str,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(report_text, encoding="utf-8")
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:classifier-derived-copy-dosage-representation"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-30T22:10:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value=observed_value,
    )
    proposal["predicate"] = "proposed_measurement_model"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-30T22:11:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"measurement_model": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-30T22:12:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-30T22:13:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "measurement_model"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    ("answer_value", "expected_title", "expected_outcome"),
    [
        (
            "omit_unobserved_or_unlinked_technical_group_covariate",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "include_recovered_technical_group_covariate",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_recoverable_technical_group_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(
        "No donor-specific ambient group or technical group is directly observed. None is "
        "reconstructed. Consequently, no ambient-group or technical-group covariate is "
        "included.\n",
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:recoverable-technical-group-adjustment"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-30T23:40:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="omit_unobserved_or_unlinked_technical_group_covariate",
    )
    proposal["predicate"] = "proposed_adjustment_set"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-30T23:41:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"adjustment_set": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-30T23:42:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-30T23:43:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "adjustment_set"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    ("answer_value", "expected_title", "expected_outcome"),
    [
        (
            "no_group_specific_paired_bridge_location_offsets_before_followup_fit",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "group_specific_paired_bridge_location_offsets_before_followup_fit",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_paired_bridge_location_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(
        "The independent single-guide follow-up was not substituted for the pooled endpoint. "
        "Its correlation with the pooled guide effects was 0.986, supporting the guide ranking.\n",
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:paired-bridge-location-alignment"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T02:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="no_group_specific_paired_bridge_location_offsets_before_followup_fit",
    )
    proposal["predicate"] = "proposed_scale_and_orientation"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T02:01:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"scale_and_orientation": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T02:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T02:03:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "scale_and_orientation"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


@pytest.mark.parametrize(
    ("answer_value", "expected_title", "expected_outcome"),
    [
        (
            "simultaneous_dominant_and_nondominant_effective_knockdown_axes",
            "One exact analysis-scoped method relation is compatible",
            "covered_negative",
        ),
        (
            "high_dominant_overlap_subset_single_efficiency_axis",
            "One exact review-scoped method incompatibility",
            "exact_conflict_candidate",
        ),
    ],
)
def test_casrx_isoform_axis_answer_and_disclosure_are_replay_stable(
    schema_root: Path,
    tmp_path: Path,
    answer_value: str,
    expected_title: str,
    expected_outcome: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text(
        "For every CasRx guide, the effective dominant-transcript axis was overlap times "
        "knockdown efficiency. The non-dominant axis was one minus overlap times knockdown "
        "efficiency. A simultaneous two-axis fit used the dominant-axis coefficient as the "
        "transcript-specific effect.\n",
        encoding="utf-8",
    )
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
        == "check:casrx-isoform-axis-model"
    )

    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-31T02:40:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    proposal = _proposal(
        packet,
        object_value="simultaneous_dominant_and_nondominant_effective_knockdown_axes",
    )
    proposal["predicate"] = "proposed_measurement_model"
    submit_proposal(
        session,
        str(item["work_item_id"]),
        proposal,
        schema_root,
        submitted_at="2026-07-31T02:41:00Z",
    )
    answer = create_structured_answer(
        session,
        str(question["question_id"]),
        {"measurement_model": answer_value},
        "scientist:test",
        schema_root,
        answered_at="2026-07-31T02:42:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(
        session,
        schema_root,
        locked_at="2026-07-31T02:43:00Z",
    )

    ledger_disclosures = [
        disclosure
        for disclosure in bundle["disclosures"]
        if disclosure.get("extensions", {}).get("x-posthoc-method-ledger", {}).get("dimension")
        == "measurement_model"
    ]
    assert bundle["findings"] == []
    assert len(ledger_disclosures) == 1
    assert ledger_disclosures[0]["title"] == expected_title
    assert (
        ledger_disclosures[0]["extensions"]["x-posthoc-method-ledger"]["outcome"]
        == expected_outcome
    )

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in ("answers", "semantic_assertions", "disclosures", "findings"):
        assert replayed[field] == bundle[field]


def test_scientist_can_explicitly_retain_unknown_without_resolving_contract(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_ambiguous_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = source_bundle["material_questions"][0]
    session = tmp_path / "unknown-session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-29T16:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, item["work_item_id"], schema_root)
    proposal = _proposal(packet, object_value={"target_population": "Model guess"})
    proposal["predicate"] = "proposed_scientific_contract"
    submit_proposal(
        session,
        item["work_item_id"],
        proposal,
        schema_root,
        submitted_at="2026-07-29T16:01:00Z",
    )
    retain_unknown = next(
        option
        for option in question["candidate_answers"]
        if option["value"] == {"action": "retain_unknown"}
    )
    answer = create_candidate_answer(
        session,
        question["question_id"],
        retain_unknown["answer_id"],
        "scientist:principal-investigator",
        schema_root,
        answered_at="2026-07-29T16:02:00Z",
    )

    assert answer["answer_kind"] == "unknown"
    assert answer["certainty"]["level"] == "unknown"
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(session, schema_root, locked_at="2026-07-29T16:03:00Z")

    assert bundle["answers"] == [answer]
    assert bundle["scientific_contracts"][0]["status"] == "draft"
    assert all(
        slot["state"] == "unknown"
        for slot in bundle["scientific_contracts"][0]["dimensions"].values()
    )
    assert [
        item
        for item in bundle["semantic_assertions"]
        if item["assertion_class"] == "scientist_declaration"
    ] == []
    assert any(item["status"] == "deferred" for item in bundle["material_questions"])
    assert any(item["status"] == "open" for item in bundle["material_questions"])
    assert bundle["findings"] == []

    replayed = replay(session / "semantic.lock.json", tmp_path / "unknown-replay", schema_root)
    for field in (
        "semantic_assertions",
        "scientific_contracts",
        "answers",
        "material_questions",
        "findings",
    ):
        assert replayed[field] == bundle[field]


def test_closed_expected_count_answer_keeps_declaration_and_derives_eligible_intent(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "expected-count-project"
    repository.mkdir()
    _write_expected_count_project(repository)
    source = tmp_path / "expected-count-source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = source_bundle["material_questions"][0]
    session = tmp_path / "expected-count-session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-29T14:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, item["work_item_id"], schema_root)
    profile = build_expected_count_profile(
        estimator_family="negative_binomial_glm",
        likelihood_family="negative_binomial",
        link_function="log",
        background_scope="model_predicted_expected_count",
        grouping_structure="replicate_intercepts",
        covariate_terms=["distance", "gc", "restriction_site_count"],
        group_specific_terms=["distance", "gc"],
        training_exclusions=[
            "case_specific_structural_variant",
            "low_mappability",
            "target_observation",
        ],
        target_excluded=True,
        analysis_resolution_bp=20_000,
    )
    dimensions = expected_count_dimension_values(profile)
    proposal = _proposal(packet, object_value=json.dumps(dimensions, sort_keys=True))
    proposal["predicate"] = "proposed_scientific_contract"
    proposal["object"] = copy.deepcopy(dimensions)
    submit_proposal(
        session,
        item["work_item_id"],
        proposal,
        schema_root,
        submitted_at="2026-07-29T14:01:00Z",
    )

    with pytest.raises(InteractionProtocolError, match="exactly the six closed profile"):
        create_structured_answer(
            session,
            question["question_id"],
            {"control_set": dimensions["control_set"]},
            "scientist:principal-investigator",
            schema_root,
        )

    answer = create_structured_answer(
        session,
        question["question_id"],
        dimensions,
        "scientist:principal-investigator",
        schema_root,
        answered_at="2026-07-29T14:02:00Z",
    )
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(session, schema_root, locked_at="2026-07-29T14:03:00Z")

    declarations = [
        item
        for item in bundle["semantic_assertions"]
        if item["assertion_class"] == "scientist_declaration"
    ]
    derived = [
        item
        for item in bundle["semantic_assertions"]
        if item["predicate"].startswith("verified_intended_")
    ]
    assert len(declarations) == 6
    assert len(derived) == 6
    assert all(item["finding_eligibility"] == "ineligible" for item in declarations)
    assert all(
        item["assertion_class"] == "deterministic_derivation"
        and item["finding_eligibility"] == "eligible"
        and item["verification"]["method"] == "deterministic_comparison"
        and item["extensions"]["x-answer-ref"]["record_id"] == answer["answer_id"]
        for item in derived
    )
    contract = bundle["scientific_contracts"][0]
    assert all(
        len(contract["dimensions"][dimension]["accepted_assertion_ids"]) == 2
        for dimension in dimensions
    )
    assert bundle["claims"][0]["extensions"]["x-expected-count-profile-resolved"] is True
    assert len(bundle["detector_results"]) == 1
    assert bundle["detector_results"][0]["state"] == "evaluation_finding_candidate"
    assert bundle["detector_results"][0]["extensions"]["x-production-finding-permitted"] is False
    assert bundle["findings"] == []

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "semantic_assertions",
        "scientific_contracts",
        "answers",
        "claims",
        "findings",
    ):
        assert replayed[field] == bundle[field]


def test_claimless_expected_count_question_accepts_only_analysis_scoped_human_intent(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "claimless-expected-count-project"
    repository.mkdir()
    _write_claimless_expected_count_obligation_project(repository)
    source = tmp_path / "claimless-expected-count-source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = next(
        item
        for item in source_bundle["material_questions"]
        if item.get("extensions", {}).get("x-unresolved-obligation-profile")
        == "expected_count_unresolved_obligation_v1"
    )
    assert question["affected_claim_ids"] == []

    session = tmp_path / "claimless-expected-count-session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-30T18:00:00Z",
    )
    item = next(
        candidate
        for candidate in work_queue(session, schema_root)["work_items"]
        if candidate["material_question_refs"]
        == [{"record_type": "material_question", "record_id": question["question_id"]}]
    )
    packet = work_packet(session, item["work_item_id"], schema_root)
    profile = build_expected_count_profile(
        estimator_family="negative_binomial_glm",
        likelihood_family="negative_binomial",
        link_function="log",
        background_scope="model_predicted_expected_count",
        grouping_structure="replicate_intercepts",
        covariate_terms=["distance", "gc", "restriction_site_count"],
        group_specific_terms=["distance", "gc"],
        training_exclusions=[
            "case_specific_structural_variant",
            "low_mappability",
            "target_observation",
        ],
        target_excluded=True,
        analysis_resolution_bp=20_000,
    )
    dimensions = expected_count_dimension_values(profile)
    proposal = _proposal(packet, object_value=copy.deepcopy(dimensions))
    proposal["predicate"] = "proposed_scientific_contract"
    submit_proposal(
        session,
        item["work_item_id"],
        proposal,
        schema_root,
        submitted_at="2026-07-30T18:01:00Z",
    )

    with pytest.raises(InteractionProtocolError, match="exactly the six closed profile"):
        create_structured_answer(
            session,
            question["question_id"],
            {"control_set": dimensions["control_set"]},
            "scientist:principal-investigator",
            schema_root,
        )

    answer = create_structured_answer(
        session,
        question["question_id"],
        dimensions,
        "scientist:principal-investigator",
        schema_root,
        answered_at="2026-07-30T18:02:00Z",
    )
    assert answer["authority_scope"] == {
        "authority_kind": "scientific_intent",
        "subject_refs": [question["extensions"]["x-analysis-subject-ref"]],
        "semantic_dimensions": sorted(dimensions),
    }
    record_answer(session, answer, schema_root)
    bundle = lock_semantics(session, schema_root, locked_at="2026-07-30T18:03:00Z")

    declarations = [
        item
        for item in bundle["semantic_assertions"]
        if item["assertion_class"] == "scientist_declaration"
    ]
    assert len(declarations) == 6
    assert all(item["finding_eligibility"] == "ineligible" for item in declarations)
    assert not any(
        item["predicate"].startswith("verified_intended_") for item in bundle["semantic_assertions"]
    )
    contract = next(
        item
        for item in bundle["scientific_contracts"]
        if item.get("extensions", {}).get("x-unresolved-obligation-profile")
        == "expected_count_unresolved_obligation_v1"
    )
    assert contract["scope"]["level"] == "analysis"
    assert contract["status"] == "draft"
    assert all(contract["dimensions"][dimension]["state"] == "known" for dimension in dimensions)
    assert bundle["claims"] == []
    assert bundle["detector_results"] == []
    assert bundle["findings"] == []

    replayed = replay(session / "semantic.lock.json", tmp_path / "claimless-replay", schema_root)
    for field in (
        "semantic_assertions",
        "scientific_contracts",
        "answers",
        "claims",
        "detector_results",
        "findings",
    ):
        assert replayed[field] == bundle[field]


def test_linked_segments_persist_one_pause_aware_deadline_ledger(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_ambiguous_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = source_bundle["material_questions"][0]
    first_session = tmp_path / "first-session"
    resume_semantics(
        source,
        repository,
        first_session,
        schema_root,
        created_at="2026-07-28T12:00:00Z",
    )
    item = work_queue(first_session, schema_root)["work_items"][0]
    packet = work_packet(first_session, item["work_item_id"], schema_root)
    proposal = _proposal(packet, object_value={"target_population": "All plots"})
    proposal["predicate"] = "proposed_scientific_contract"
    submit_proposal(
        first_session,
        item["work_item_id"],
        proposal,
        schema_root,
        submitted_at="2026-07-28T12:02:00Z",
    )
    answer = create_structured_answer(
        first_session,
        question["question_id"],
        {"target_population": "All randomized plots"},
        "scientist:test",
        schema_root,
        answered_at="2026-07-28T14:02:00Z",
    )
    record_answer(first_session, answer, schema_root)
    first_bundle = lock_semantics(
        first_session,
        schema_root,
        locked_at="2026-07-28T14:03:00Z",
    )

    first_ledger = load_deadline_ledger(first_session / "observed" / LEDGER_FILENAME)
    assert first_ledger is not None
    verify_deadline_ledger(first_ledger)
    first_segment = first_ledger["segments"][-1]
    assert first_segment["state"] == "complete"
    assert first_segment["user_visible_elapsed_seconds"] == 180.0
    assert first_segment["paused_for_scientist_seconds"] == 7200.0
    assert [event["event"] for event in first_segment["events"]] == [
        "segment_started",
        "model_proposal_submitted",
        "scientist_wait_started",
        "scientist_answer_recorded",
        "semantic_lock_reached",
        "postlock_stages_completed",
        "segment_completed",
    ]
    assert len(first_bundle["performance_records"]) == 1
    first_performance = first_bundle["performance_records"][0]
    assert first_performance["user_visible_elapsed_seconds"] == 180.0
    assert first_performance["paused_for_scientist_seconds"] == 7200.0
    assert first_performance["model_usage"]["calls"] == 0
    assert first_performance["cache_usage"] == {
        "hits": 0,
        "misses": 0,
        "invalidations": 0,
    }
    first_lock = json.loads((first_session / "semantic.lock.json").read_text(encoding="utf-8"))
    assert len(first_lock["model_calls"]) == 1
    assert (
        first_performance["extensions"]["x-deadline-ledger-digest"]
        == first_lock["deadline_ledger"]["ledger_digest"]
    )
    first_replay = replay(
        first_session / "semantic.lock.json",
        tmp_path / "first-session-replay",
        schema_root,
    )
    assert first_replay["performance_records"] == [first_performance]

    second_session = tmp_path / "second-session"
    result = resume_semantics(
        first_session,
        repository,
        second_session,
        schema_root,
        created_at="2026-07-28T15:00:00Z",
    )
    second_ledger = load_deadline_ledger(second_session / "observed" / LEDGER_FILENAME)
    assert second_ledger is not None
    assert len(second_ledger["segments"]) == 2
    assert second_ledger["segments"][0] == first_segment
    second_segment = second_ledger["segments"][1]
    assert second_segment["audit_run_id"] == result["audit_run_id"]
    assert second_segment["parent_audit_run_id"] == first_segment["audit_run_id"]
    assert second_segment["state"] == "active"
    assert second_segment["user_visible_elapsed_seconds"] == 0.0
    assert second_segment["hard_seconds"] == 600.0

    second_item = work_queue(second_session, schema_root)["work_items"][0]
    second_packet = work_packet(second_session, second_item["work_item_id"], schema_root)
    second_proposal = _proposal(
        second_packet,
        object_value={"target_population": "Model-proposed population"},
    )
    second_proposal["assertion_id"] = "assertion:model-contract-second-segment"
    second_proposal["predicate"] = "proposed_scientific_contract"
    submit_proposal(
        second_session,
        second_item["work_item_id"],
        second_proposal,
        schema_root,
        submitted_at="2026-07-28T15:02:00Z",
    )
    dimension = second_packet["work_item"]["packet"]["unresolved_dimensions"][0]
    second_answer = create_structured_answer(
        second_session,
        second_item["material_question_refs"][0]["record_id"],
        {dimension: "Scientist-declared bounded value"},
        "scientist:test",
        schema_root,
        answered_at="2026-07-28T15:04:00Z",
    )
    record_answer(second_session, second_answer, schema_root)
    second_bundle = lock_semantics(
        second_session,
        schema_root,
        locked_at="2026-07-28T15:05:00Z",
    )

    second_performance = second_bundle["performance_records"][0]
    assert second_performance["user_visible_elapsed_seconds"] == 180.0
    assert second_performance["paused_for_scientist_seconds"] == 120.0
    assert second_performance["model_usage"]["calls"] == 0
    assert second_performance["cache_usage"] == {
        "hits": 0,
        "misses": 0,
        "invalidations": 0,
    }
    first_assertion_ids = {
        assertion["assertion_id"] for assertion in first_bundle["semantic_assertions"]
    }
    second_assertion_ids = {
        assertion["assertion_id"] for assertion in second_bundle["semantic_assertions"]
    }
    assert first_assertion_ids < second_assertion_ids
    completed_ledger = load_deadline_ledger(second_session / "observed" / LEDGER_FILENAME)
    assert completed_ledger is not None
    assert len(completed_ledger["segments"]) == 2
    assert completed_ledger["segments"][0] == first_segment
    assert completed_ledger["segments"][1]["state"] == "complete"


def test_prelock_interaction_deadline_exhaustion_is_durable(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_ambiguous_project(repository)
    source = tmp_path / "source"
    run_audit(repository, source, schema_root, mode="quick")
    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        created_at="2026-07-28T12:00:00Z",
    )
    item = work_queue(session, schema_root)["work_items"][0]
    packet = work_packet(session, item["work_item_id"], schema_root)

    with pytest.raises(InteractionProtocolError, match="hard deadline exhausted"):
        submit_proposal(
            session,
            item["work_item_id"],
            _proposal(packet, object_value="artifact:any"),
            schema_root,
            submitted_at="2026-07-28T12:05:00Z",
        )

    ledger = load_deadline_ledger(session / "observed" / LEDGER_FILENAME)
    assert ledger is not None
    segment = ledger["segments"][-1]
    assert segment["state"] == "hard_deadline_exhausted"
    assert segment["user_visible_elapsed_seconds"] == 300.0
    states = [
        json.loads(line)["state"]
        for line in (session / "observed" / "audit-run.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert states[-1] == "partial_deadline"
    assert not (session / "semantic.lock.json").exists()
