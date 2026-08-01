from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.agent_protocol import load_open_questions
from sc_referee.cli import app
from sc_referee.controller import replay, run_audit
from sc_referee.core.control import RunControl
from sc_referee.core.errors import CancellationRequestedError
from sc_referee.core.ids import semantic_digest
from sc_referee.interaction import (
    InteractionProtocolError,
    create_candidate_answer,
    create_scope_selection_answer,
    lock_semantics,
    record_answer,
    resume_semantics,
    submit_proposal,
    work_packet,
    work_queue,
)
from sc_referee.scope_selection import (
    SCOPE_SELECTION_PROFILE,
    validate_scope_selection_question,
)
from sc_referee.version import SCHEMA_VERSION


def _write_scope_project(root: Path) -> None:
    (root / "report.md").write_text("# Results\n\nDescriptive audit fixture.\n", encoding="utf-8")
    for suffix in ("a", "b"):
        (root / f"data_{suffix}.csv").write_text("id,value\n1,2\n", encoding="utf-8")
        (root / f"result_{suffix}.json").write_text(
            json.dumps({"result": suffix}), encoding="utf-8"
        )
        (root / f"analysis_{suffix}.py").write_text(
            "from pathlib import Path\n"
            f"payload = Path('data_{suffix}.csv').read_text()\n"
            f"Path('result_{suffix}.json').write_text(payload)\n",
            encoding="utf-8",
        )
    (root / "source-link.py").symlink_to(root / "analysis_a.py")


def _selection_questions(bundle: dict[str, object]) -> dict[str, dict[str, object]]:
    questions = bundle["material_questions"]
    assert isinstance(questions, list)
    return {
        str(item["extensions"]["x-selection-kind"]): item
        for item in questions
        if isinstance(item, dict)
        and isinstance(item.get("extensions"), dict)
        and item["extensions"].get("x-selection-profile") == SCOPE_SELECTION_PROFILE
    }


def _proposal(packet: dict[str, object], assertion_id: str) -> dict[str, object]:
    item = packet["work_item"]
    assert isinstance(item, dict)
    bounded = item["packet"]
    assert isinstance(bounded, dict)
    source_refs = bounded["source_refs"]
    target_refs = item["target_refs"]
    assert isinstance(source_refs, list) and source_refs
    assert isinstance(target_refs, list) and target_refs
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": assertion_id,
        "audit_run_id": packet["audit_run_id"],
        "subject_ref": copy.deepcopy(target_refs[0]),
        "predicate": "proposed_review_scope_candidates",
        "object": {"candidate_count": len(source_refs)},
        "semantic_role": "inferred",
        "assertion_class": "implicit_scientific_inference",
        "epistemic_status": "proposed",
        "authority_scope": "none",
        "independently_checkable": False,
        "finding_eligibility": "ineligible",
        "verification": {"status": "not_checked", "method": "not_applicable"},
        "certainty": {
            "level": "unknown",
            "basis": "The proposal has no authority to select review scope.",
        },
        "rationale": "The packet contains a finite immutable candidate inventory.",
        "source_refs": [copy.deepcopy(source_refs[0])],
        "provenance": {
            "actor": {"actor_kind": "model", "actor_id": "model:test"},
            "method": "bounded_semantic_proposal",
            "created_at": "2026-08-01T18:01:00Z",
            "tool": "test-model-adapter",
            "tool_version": "1.0.0",
        },
        "extensions": {
            "x-work-item-ref": {
                "record_type": "work_item",
                "record_id": item["work_item_id"],
            },
            "x-packet-digest": bounded["packet_digest"],
            "x-prompt-template-digest": bounded["prompt_template_digest"],
        },
    }


def _submit_for_question(
    session: Path,
    schema_root: Path,
    question: dict[str, object],
    assertion_id: str,
) -> dict[str, object]:
    queue = work_queue(session, schema_root)
    item = next(
        value
        for value in queue["work_items"]
        if value["material_question_refs"][0]["record_id"] == question["question_id"]
    )
    packet = work_packet(session, str(item["work_item_id"]), schema_root)
    submit_proposal(
        session,
        str(item["work_item_id"]),
        _proposal(packet, assertion_id),
        schema_root,
    )
    return item


def test_scope_inventory_has_zero_one_many_and_rejects_symlink(
    schema_root: Path, tmp_path: Path
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "report.md").write_text("# Report\n", encoding="utf-8")
    empty_bundle = run_audit(empty, tmp_path / "empty-audit", schema_root, report="report.md")
    empty_projection = json.loads(
        (tmp_path / "empty-audit" / "semantic.lock.json").read_text(encoding="utf-8")
    )["scope_selections"]
    assert _selection_questions(empty_bundle) == {}
    assert {key: value["status"] for key, value in empty_projection["selections"].items()} == {
        "analysis_output": "unavailable",
        "analysis_source": "unavailable",
        "material_input": "unavailable",
    }

    one = tmp_path / "one"
    one.mkdir()
    (one / "report.md").write_text("# Report\n", encoding="utf-8")
    (one / "analysis.py").write_text("value = 1\n", encoding="utf-8")
    one_bundle = run_audit(one, tmp_path / "one-audit", schema_root, report="report.md")
    one_projection = json.loads(
        (tmp_path / "one-audit" / "semantic.lock.json").read_text(encoding="utf-8")
    )["scope_selections"]
    assert _selection_questions(one_bundle) == {}
    assert one_projection["selections"]["analysis_source"]["status"] == (
        "unique_candidate_unselected"
    )

    many = tmp_path / "many"
    many.mkdir()
    _write_scope_project(many)
    bundle = run_audit(many, tmp_path / "many-audit", schema_root, report="report.md")
    questions = _selection_questions(bundle)
    assert set(questions) == {"analysis_source", "material_input", "analysis_output"}
    assert [
        item["path"] for item in questions["analysis_source"]["extensions"]["x-candidate-bindings"]
    ] == ["analysis_a.py", "analysis_b.py"]
    assert "source-link.py" not in [
        item["label"] for item in questions["analysis_source"]["candidate_answers"]
    ]
    projected = load_open_questions(tmp_path / "many-audit", schema_root).model_dump()
    assert projected["protocol_version"] == "0.2.0"
    source_projection = next(
        item for item in projected["questions"] if item["selection_kind"] == "analysis_source"
    )
    assert source_projection["selection_profile"] == SCOPE_SELECTION_PROFILE
    assert source_projection["multiple_selection_allowed"] is True
    assert source_projection["max_selections"] == 2
    assert "review scope only" in source_projection["authority_limitation"]

    over_budget = tmp_path / "over-budget"
    over_budget.mkdir()
    (over_budget / "report.md").write_text("# Report\n", encoding="utf-8")
    for index in range(65):
        (over_budget / f"analysis_{index:02d}.py").write_text(
            f"value = {index}\n", encoding="utf-8"
        )
    over_budget_bundle = run_audit(
        over_budget,
        tmp_path / "over-budget-audit",
        schema_root,
        report="report.md",
    )
    over_budget_projection = json.loads(
        (tmp_path / "over-budget-audit" / "semantic.lock.json").read_text(encoding="utf-8")
    )["scope_selections"]
    assert "analysis_source" not in _selection_questions(over_budget_bundle)
    assert over_budget_projection["selections"]["analysis_source"]["status"] == (
        "selection_over_budget"
    )


def test_multi_scope_answer_locks_replays_and_survives_next_linked_segment(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_scope_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    parent_lock = (source / "semantic.lock.json").read_bytes()
    questions = _selection_questions(source_bundle)
    source_question = questions["analysis_source"]

    first = tmp_path / "first"
    resumed = resume_semantics(
        source,
        repository,
        first,
        schema_root,
        question_id=str(source_question["question_id"]),
        created_at="2026-08-01T18:00:00Z",
    )
    assert len(resumed["work_item_ids"]) == 1
    _submit_for_question(first, schema_root, source_question, "assertion:scope-source")
    source_options = [
        str(item["answer_id"])
        for item in source_question["candidate_answers"]
        if isinstance(item.get("value"), dict)
        and len(item["value"].get("selected_candidate_refs", [])) == 1
    ]
    source_answer = create_scope_selection_answer(
        first,
        str(source_question["question_id"]),
        tuple(source_options),
        "scientist:test",
        schema_root,
        answered_at="2026-08-01T18:02:00Z",
    )
    assert source_answer["authority_scope"]["authority_kind"] == "metadata_definition"
    record_answer(first, source_answer, schema_root)
    first_bundle = lock_semantics(first, schema_root, locked_at="2026-08-01T18:03:00Z")
    first_lock = json.loads((first / "semantic.lock.json").read_text(encoding="utf-8"))
    selected_sources = first_lock["scope_selections"]["selections"]["analysis_source"]
    assert selected_sources["status"] == "selected"
    assert selected_sources["selected_paths"] == ["analysis_a.py", "analysis_b.py"]
    assert (source / "semantic.lock.json").read_bytes() == parent_lock
    assert {
        item["extensions"]["x-selection-kind"]
        for item in first_bundle["material_questions"]
        if item["status"] == "open"
        and item.get("extensions", {}).get("x-selection-profile") == SCOPE_SELECTION_PROFILE
    } == {"material_input", "analysis_output"}

    input_question = _selection_questions(first_bundle)["material_input"]
    second = tmp_path / "second"
    resume_semantics(
        first,
        repository,
        second,
        schema_root,
        question_id=str(input_question["question_id"]),
        created_at="2026-08-01T19:00:00Z",
    )
    _submit_for_question(second, schema_root, input_question, "assertion:scope-input")
    selected_option = next(
        item for item in input_question["candidate_answers"] if item["label"] == "data_a.csv"
    )
    input_answer = create_candidate_answer(
        second,
        str(input_question["question_id"]),
        str(selected_option["answer_id"]),
        "scientist:test",
        schema_root,
        answered_at="2026-08-01T19:02:00Z",
    )
    record_answer(second, input_answer, schema_root)
    second_bundle = lock_semantics(second, schema_root, locked_at="2026-08-01T19:03:00Z")
    second_lock = json.loads((second / "semantic.lock.json").read_text(encoding="utf-8"))
    assert second_bundle["answers"] == [source_answer, input_answer]
    rebound_sources = second_lock["scope_selections"]["selections"]["analysis_source"]
    for field in (
        "status",
        "selected_record_refs",
        "selected_paths",
        "selection_authority",
        "answer_ref",
        "question_ref",
    ):
        assert rebound_sources[field] == selected_sources[field]
    current_identity_ids = {item["asset_identity_id"] for item in second_lock["asset_identities"]}
    assert all(
        item["record_id"] in current_identity_ids
        for item in rebound_sources["selected_identity_refs"]
    )
    assert second_lock["scope_selections"]["selections"]["material_input"]["selected_paths"] == [
        "data_a.csv"
    ]
    replayed = replay(second / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["answers"] == second_bundle["answers"]
    assert replayed["material_questions"] == second_bundle["material_questions"]


def test_unanswered_scope_question_rebinds_after_unrelated_linked_answer(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_scope_project(repository)
    (repository / "README.md").write_text("# Supporting notes\n", encoding="utf-8")
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root)
    publication_question = next(
        item
        for item in source_bundle["material_questions"]
        if item["unknown_semantic_dimension"] == "publication_surface"
    )
    original_scope = _selection_questions(source_bundle)["analysis_source"]

    first = tmp_path / "first"
    resume_semantics(
        source,
        repository,
        first,
        schema_root,
        created_at="2026-08-01T20:00:00Z",
    )
    _submit_for_question(
        first,
        schema_root,
        publication_question,
        "assertion:publication-before-scope",
    )
    report_option = next(
        item for item in publication_question["candidate_answers"] if item["label"] == "report.md"
    )
    publication_answer = create_candidate_answer(
        first,
        str(publication_question["question_id"]),
        str(report_option["answer_id"]),
        "scientist:test",
        schema_root,
        answered_at="2026-08-01T20:02:00Z",
    )
    record_answer(first, publication_answer, schema_root)
    first_bundle = lock_semantics(first, schema_root, locked_at="2026-08-01T20:03:00Z")
    refreshed_scope = _selection_questions(first_bundle)["analysis_source"]

    assert refreshed_scope["question_id"] != original_scope["question_id"]
    assert [
        item["record_ref"] for item in refreshed_scope["extensions"]["x-candidate-bindings"]
    ] == [item["record_ref"] for item in original_scope["extensions"]["x-candidate-bindings"]]
    assert [
        item["asset_identity_ref"] for item in refreshed_scope["extensions"]["x-candidate-bindings"]
    ] != [
        item["asset_identity_ref"] for item in original_scope["extensions"]["x-candidate-bindings"]
    ]

    second = tmp_path / "second"
    resumed = resume_semantics(
        first,
        repository,
        second,
        schema_root,
        created_at="2026-08-01T21:00:00Z",
    )
    queue = work_queue(second, schema_root)
    assert len(resumed["work_item_ids"]) == len(
        [item for item in first_bundle["material_questions"] if item["status"] == "open"]
    )
    assert any(
        item["material_question_refs"]
        == [
            {
                "record_type": "material_question",
                "record_id": refreshed_scope["question_id"],
            }
        ]
        for item in queue["work_items"]
    )


def test_scope_answer_rejects_stale_conflicting_missing_and_drifted_state(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_scope_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = _selection_questions(source_bundle)["analysis_source"]
    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        question_id=str(question["question_id"]),
    )
    _submit_for_question(session, schema_root, question, "assertion:scope-stale")
    option = next(
        item for item in question["candidate_answers"] if item["label"] == "analysis_a.py"
    )
    answer = create_candidate_answer(
        session,
        str(question["question_id"]),
        str(option["answer_id"]),
        "scientist:test",
        schema_root,
    )
    stale = copy.deepcopy(answer)
    stale["source_snapshot_digest"] = "sha256:" + "0" * 64
    stale.pop("answer_digest")
    stale["answer_digest"] = semantic_digest(stale)
    with pytest.raises(InteractionProtocolError, match="snapshot binding mismatch"):
        record_answer(session, stale, schema_root)

    record_answer(session, answer, schema_root)
    other = copy.deepcopy(answer)
    other["answer_id"] = "answer:conflicting"
    other.pop("answer_digest")
    other["answer_digest"] = semantic_digest(other)
    with pytest.raises(InteractionProtocolError, match="proposal must be submitted"):
        record_answer(session, other, schema_root)

    missing = copy.deepcopy(source_bundle)
    missing["file_records"] = [
        item
        for item in missing["file_records"]
        if item["file_record_id"]
        != question["extensions"]["x-candidate-bindings"][0]["record_ref"]["record_id"]
    ]
    with pytest.raises(ValueError, match="record or identity is missing"):
        validate_scope_selection_question(
            missing,
            question,
            source_bundle["repository_snapshots"][0]["snapshot_digest"],
        )

    unsafe_question = copy.deepcopy(question)
    unsafe_question["extensions"]["x-candidate-bindings"][0]["path"] = "../outside.py"
    with pytest.raises(ValueError, match="incomplete or unsafe"):
        validate_scope_selection_question(
            source_bundle,
            unsafe_question,
            source_bundle["repository_snapshots"][0]["snapshot_digest"],
        )

    weak_bundle = copy.deepcopy(source_bundle)
    identity_id = question["extensions"]["x-candidate-bindings"][0]["asset_identity_ref"][
        "record_id"
    ]
    weak_identity = next(
        item for item in weak_bundle["asset_identities"] if item["asset_identity_id"] == identity_id
    )
    weak_identity["tier"] = "sampled_fingerprint"
    with pytest.raises(ValueError, match="identity binding is inconsistent"):
        validate_scope_selection_question(
            weak_bundle,
            question,
            source_bundle["repository_snapshots"][0]["snapshot_digest"],
        )

    drifted_repository = tmp_path / "drifted"
    drifted_repository.mkdir()
    _write_scope_project(drifted_repository)
    drifted_source = tmp_path / "drifted-source"
    run_audit(
        drifted_repository,
        drifted_source,
        schema_root,
        report="report.md",
    )
    (drifted_repository / "analysis_a.py").write_text("value = 2\n", encoding="utf-8")
    with pytest.raises(InteractionProtocolError, match="snapshot differs"):
        resume_semantics(
            drifted_source,
            drifted_repository,
            tmp_path / "drifted-session",
            schema_root,
        )


@pytest.mark.parametrize(
    ("kind", "option_label", "expected_status"),
    [
        ("material_input", "None of these candidates", "selected_none"),
        ("analysis_output", "Retain as unknown", "unknown"),
    ],
)
def test_scope_selection_can_explicitly_select_none_or_retain_unknown(
    schema_root: Path,
    tmp_path: Path,
    kind: str,
    option_label: str,
    expected_status: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_scope_project(repository)
    source = tmp_path / "source"
    source_bundle = run_audit(repository, source, schema_root, report="report.md")
    question = _selection_questions(source_bundle)[kind]
    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        question_id=str(question["question_id"]),
    )
    _submit_for_question(session, schema_root, question, f"assertion:{kind}")
    option = next(item for item in question["candidate_answers"] if item["label"] == option_label)
    answer = create_candidate_answer(
        session,
        str(question["question_id"]),
        str(option["answer_id"]),
        "scientist:test",
        schema_root,
    )
    record_answer(session, answer, schema_root)
    lock_semantics(session, schema_root)
    locked = json.loads((session / "semantic.lock.json").read_text(encoding="utf-8"))
    selection = locked["scope_selections"]["selections"][kind]
    assert selection["status"] == expected_status
    assert selection["selected_record_refs"] == []


def test_linked_resume_reuses_original_material_identity_budget(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "report.md").write_text("# Descriptive report\n", encoding="utf-8")
    (repository / "large.csv").write_bytes(b"id,value\n" + b"1,2\n" * 1_400_000)
    for suffix in ("a", "b"):
        (repository / f"analysis_{suffix}.py").write_text(
            "from pathlib import Path\npayload = Path('large.csv').read_text()\n",
            encoding="utf-8",
        )
    source = tmp_path / "source"
    bundle = run_audit(
        repository,
        source,
        schema_root,
        report="report.md",
        material_inputs=("large.csv",),
    )
    question = _selection_questions(bundle)["analysis_source"]
    result = resume_semantics(
        source,
        repository,
        tmp_path / "session",
        schema_root,
        question_id=str(question["question_id"]),
    )
    assert result["source_snapshot_digest"] == bundle["repository_snapshots"][0]["snapshot_digest"]


def test_record_scope_answer_cli_accepts_repeated_exact_options(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_scope_project(repository)
    source = tmp_path / "source"
    bundle = run_audit(repository, source, schema_root, report="report.md")
    question = _selection_questions(bundle)["analysis_source"]
    session = tmp_path / "session"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        question_id=str(question["question_id"]),
    )
    _submit_for_question(session, schema_root, question, "assertion:scope-cli")
    option_ids = [
        str(item["answer_id"])
        for item in question["candidate_answers"]
        if isinstance(item.get("value"), dict)
        and len(item["value"].get("selected_candidate_refs", [])) == 1
    ]
    result = CliRunner().invoke(
        app,
        [
            "record-scope-answer",
            str(session),
            "--question-id",
            str(question["question_id"]),
            "--select-option",
            option_ids[0],
            "--select-option",
            option_ids[1],
            "--actor-id",
            "scientist:test",
            "--schema-root",
            str(schema_root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Recorded scope Answer" in result.output
    locked = lock_semantics(session, schema_root)
    assert len(locked["answers"]) == 1


def test_cancellation_before_scope_selection_fabricates_no_answer(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_scope_project(repository)
    control = RunControl()

    def cancel_after_inventory(state: str, active: RunControl) -> None:
        if state == "inventoried":
            active.request_cancellation()

    with pytest.raises(CancellationRequestedError):
        run_audit(
            repository,
            tmp_path / "cancelled",
            schema_root,
            report="report.md",
            run_control=control,
            stage_hook=cancel_after_inventory,
        )
    assert not (tmp_path / "cancelled" / "semantic.lock.json").exists()
    answer_path = tmp_path / "cancelled" / "derived" / "answer.jsonl"
    assert not answer_path.exists()
