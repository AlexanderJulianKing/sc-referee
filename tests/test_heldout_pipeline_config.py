"""ADR-0070 held-out configuration controls for the lean pipeline.

The model-call steps are exercised by the real held-out run; these tests lock
the deterministic layers the sealed block depends on: sealed case identities
reaching the frozen authoring protocol unchanged, sealed brief text reaching
the author prompt verbatim, the one superseded construction constraint with
its original retained, the two control label statuses, and the contract-free
detector branch that must audit without a method-contract lock.

No provider CLI runs here: the one-shot transport is replaced by a recorder.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    LeanPipelineError,
    _manifest_record,
    step_authoring,
    step_detector,
    step_labels,
    write_heldout_opening,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.heldout_run import (
    LANE_RELATIVE,
    UNSUPPORTED_REPLACEMENT,
    HeldoutConfigurationError,
    heldout_config,
)

REGISTRY_RELATIVE = Path("src/sc_referee/resources/scientific-check-manifests-v1/registry.json")
ERROR_CASE_ID = "case:670f4b5b1a48188a8973"
AMBIGUOUS_CASE_ID = "case:79bba09d589444884c44"
UNSUPPORTED_CASE_ID = "case:0e8a84e424013c876694"

MINIMAL_CSV = "slot,valid,failure\n" + "".join(
    f"s{index},{'yes' if index <= 6 else 'no'},{'yes' if index <= 2 else 'no'}\n"
    for index in range(1, 9)
)
MINIMAL_WORKFLOW = """import csv
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/data.csv').open()))
valid = [row for row in rows if row['valid'] == 'yes']
failures = sum(1 for row in valid if row['failure'] == 'yes')
report = (
    '# Slot summary\\n\\n'
    f'Commissioned slots: {len(rows)}\\n'
    f'Valid-telemetry slots: {len(valid)}\\n'
    f'Removed slots: {len(rows) - len(valid)}\\n'
    f'Failures among valid slots: {failures}\\n\\n'
    f'[selected-result] The failure intensity is {failures / len(valid):.3f}.\\n'
)
Path('results/report.md').write_text(report, encoding='utf-8')
"""
MINIMAL_REPORT = (
    "# Slot summary\n\n"
    "Commissioned slots: 8\n"
    "Valid-telemetry slots: 6\n"
    "Removed slots: 2\n"
    "Failures among valid slots: 2\n\n"
    "[selected-result] The failure intensity is 0.333.\n"
)


@pytest.fixture
def sealed_root(tmp_path: Path, project_root: Path) -> Path:
    """A throwaway project root carrying the sealed lane inputs read-only."""

    lane = tmp_path / LANE_RELATIVE
    lane.mkdir(parents=True)
    for name in ("LANE_FREEZE.json", "AUTHORING_BRIEF_MANIFEST.json"):
        shutil.copy2(project_root / LANE_RELATIVE / name, lane / name)
    (tmp_path / "reference").symlink_to(project_root / "reference")
    (tmp_path / "src").symlink_to(project_root / "src")
    return tmp_path


def _record_step(
    project_root: Path,
    config: Any,
    step: str,
    artifact: dict[str, Any],
    relative_path: str,
    digest_field: str,
) -> dict[str, Any]:
    artifact[digest_field] = semantic_digest(artifact)
    path = project_root / config.pipeline_relative / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact), encoding="utf-8")
    _manifest_record(
        project_root,
        config,
        step,
        digest=artifact[digest_field],
        relative_path=relative_path,
    )
    return artifact


def test_sealed_case_ids_and_brief_text_reach_the_frozen_authoring_protocol(
    sealed_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, payload = heldout_config(sealed_root)
    sealed = json.loads((sealed_root / LANE_RELATIVE / "LANE_FREEZE.json").read_text("utf-8"))
    sealed_ids = [str(value) for value in sealed["heldout_seal"]["case_ids"]]
    prompts: dict[str, str] = {}

    def _recorded_call(
        _config: Any, participant: Any, prompt: str, _session: str, capture_root: Path
    ) -> dict[str, Any]:
        prompts[participant.participant_id] = prompt
        capture_root.mkdir(parents=True, exist_ok=True)
        return {
            "raw_response": "{}",
            "transport_error": None,
            "process_record": {"capture_digest": "sha256:" + "0" * 64},
            "started_at": "2026-08-08T00:00:00Z",
            "completed_at": "2026-08-08T00:00:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda root, config: {})
    monkeypatch.setattr(lean_pipeline, "_call_cli", _recorded_call)
    protocol = step_authoring(sealed_root, config)

    assert sorted(protocol["case_role_assignments"]) == sorted(sealed_ids)
    assert protocol["case_role_assignments"][ERROR_CASE_ID] == "error_bearing"
    assert protocol["case_role_assignments"][AMBIGUOUS_CASE_ID] == "ambiguous"
    assert protocol["heldout_opening_reference"] == "HELDOUT_OPENING.json"
    # Sealed identities are never regenerated: no stable_id derived value appears.
    assert all(case_id in sealed_ids for case_id in protocol["case_role_assignments"])

    sealed_digests = {
        str(row["case_id"]): str(row["authoring_brief_digest"])
        for row in sealed["prospective_protocol"]["assignments"]
        if str(row["case_id"]) in set(sealed_ids)
    }
    recorded = protocol["sealed_brief_digests"]
    unchanged = [case_id for case_id in sealed_ids if case_id != UNSUPPORTED_CASE_ID]
    assert {case_id: recorded[case_id] for case_id in unchanged} == {
        case_id: sealed_digests[case_id] for case_id in unchanged
    }
    supersession = payload["brief_supersessions"][0]
    assert recorded[UNSUPPORTED_CASE_ID] == supersession["superseded_brief_digest"]
    assert recorded[UNSUPPORTED_CASE_ID] != sealed_digests[UNSUPPORTED_CASE_ID]

    error_prompt = prompts["actor:heldout-codex-04"]
    assert "168 commissioned hourly slots" in error_prompt
    assert (
        "Build a compact instrument-uptime workflow that reports one failure intensity for "
        "the complete commissioned observation calendar." in error_prompt
    )
    assert "Use the 126 telemetry-screened slots as the exposure denominator" in error_prompt
    assert ERROR_CASE_ID in error_prompt
    # The sealed required_artifacts list is withheld; ADR-0069 file rules govern.
    assert "author-only selected-result declaration" not in error_prompt
    assert "workflow/analysis.py" in error_prompt


def test_unsupported_constraint_is_superseded_and_its_original_is_retained(
    sealed_root: Path, project_root: Path
) -> None:
    config, payload = heldout_config(sealed_root)
    supersessions = payload["brief_supersessions"]
    assert len(supersessions) == 1
    supersession = supersessions[0]
    assert supersession["case_id"] == UNSUPPORTED_CASE_ID
    assert supersession["case_role"] == "unsupported"
    assert supersession["fields"] == ["construction_constraints[0]", "scientific_task"]
    assert "runtime environment value" in supersession["original_task"]
    assert "runtime data value carried in the input CSV" in supersession["replacement_task"]
    assert "runtime environment value" in supersession["original_text"]
    assert supersession["replacement_text"] == UNSUPPORTED_REPLACEMENT
    assert "results/report.md" in supersession["replacement_text"]
    assert "ADR-0069 intake guard bans environment access" in supersession["reason"]

    assert config.case_briefs is not None
    constraints = config.case_briefs[UNSUPPORTED_CASE_ID]["construction_constraints"]
    assert constraints[0] == UNSUPPORTED_REPLACEMENT
    assert supersession["original_text"] not in constraints
    assert len(constraints) == 3

    # The sealed manifest on disk is evidence and is never rewritten.
    manifest = json.loads(
        (project_root / LANE_RELATIVE / "AUTHORING_BRIEF_MANIFEST.json").read_text("utf-8")
    )
    entry = next(item for item in manifest["briefs"] if item["case_id"] == UNSUPPORTED_CASE_ID)
    assert (
        entry["author_visible_brief"]["construction_constraints"][0]
        == (supersession["original_text"])
    )
    assert entry["brief_digest"] == supersession["sealed_brief_digest"]


def test_heldout_opening_is_written_once_and_replays(sealed_root: Path) -> None:
    config, payload = heldout_config(sealed_root)
    record = write_heldout_opening(sealed_root, config, payload)
    stored = json.loads(
        (sealed_root / config.pipeline_relative / "HELDOUT_OPENING.json").read_text("utf-8")
    )
    supplied = dict(stored)
    assert supplied.pop("semantic_digest") == semantic_digest(supplied)
    assert stored["artifact_kind"] == "heldout_opening"
    assert stored["adr_reference"]["accepted_on"] == "2026-08-08"
    assert stored["lane"]["heldout_seal_block_ids"] == ["block:88d0fdb420461a3f"]
    assert len(stored["sealed_assignment_table"]) == 7
    honored = {row["case_id"]: row for row in stored["sealed_assignment_table"]}
    assert honored[ERROR_CASE_ID]["sealed_author_id"] == "actor:sealed-author-codex-04"
    assert honored[ERROR_CASE_ID]["honoring_participant_id"] == "actor:heldout-codex-04"
    assert honored[ERROR_CASE_ID]["transport"] == "codex-cli"
    supersession = stored["reviewer_supersession"]
    assert supersession["sealed_stage1_reviewer_ids"] == [
        "actor:stage1-claude-01",
        "actor:stage1-claude-02",
        "actor:stage1-codex-01",
        "actor:stage1-codex-02",
    ]
    assert supersession["sealed_stage2_reviewer_ids"] == [
        "actor:stage2-claude-01",
        "actor:stage2-codex-01",
    ]
    assert "ADR-0067" in supersession["superseding_adr"]
    assert "detector run itself happens exactly once" in stored["one_shot_scope_note"]
    assert record["semantic_digest"] == stored["semantic_digest"]
    with pytest.raises(FileExistsError):
        write_heldout_opening(sealed_root, config, payload)


def test_heldout_opening_honors_configured_relative_path(sealed_root: Path) -> None:
    config, payload = heldout_config(sealed_root)
    relative = "opening/DEPENDENCE_HELDOUT_OPENING.json"
    configured = replace(config, opening_record_relative=relative)

    record = write_heldout_opening(sealed_root, configured, payload)

    path = sealed_root / configured.pipeline_relative / relative
    assert path.is_file()
    assert not (sealed_root / configured.pipeline_relative / "HELDOUT_OPENING.json").exists()
    assert json.loads(path.read_text("utf-8")) == record


def test_sealed_inputs_fail_closed_when_a_brief_digest_drifts(sealed_root: Path) -> None:
    path = sealed_root / LANE_RELATIVE / "AUTHORING_BRIEF_MANIFEST.json"
    manifest = json.loads(path.read_text("utf-8"))
    entry = next(item for item in manifest["briefs"] if item["case_id"] == ERROR_CASE_ID)
    entry["author_visible_brief"]["scientific_task"] = "A quietly edited task."
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(HeldoutConfigurationError, match="does not replay"):
        heldout_config(sealed_root)


def test_label_freeze_accepts_the_two_control_statuses(sealed_root: Path) -> None:
    config, _payload = heldout_config(sealed_root)
    assert config.label_status("ambiguous") == "ambiguous_control"
    assert config.label_status("unsupported") == "unsupported_control"
    assert config.label_status("renamed_implementation") == "positive_demonstrated"

    assert config.sealed_case_assignments is not None
    roles = dict(config.sealed_case_assignments)
    protocol = _record_step(
        sealed_root,
        config,
        "authoring",
        {
            "artifact_kind": "lean_pipeline_authoring_protocol",
            "envelope_id": config.envelope_id,
            "case_role_assignments": roles,
        },
        "authoring/AUTHORING_PROTOCOL.json",
        "protocol_digest",
    )
    entries = [
        {
            "case_id": case_id,
            "review_role": "primary",
            "participant_id": config.reviewer.participant_id,
            "review_id": f"review:{index:04d}",
            "review_digest": "sha256:" + f"{index:064d}",
        }
        for index, case_id in enumerate(sorted(roles))
    ]
    _record_step(
        sealed_root,
        config,
        "review",
        {
            "artifact_kind": "lean_pipeline_review_ledger",
            "envelope_id": config.envelope_id,
            "review_protocol_digest": protocol["protocol_digest"],
            "entries": entries,
            "unblinding_record": [
                {"case_id": case_id, "resolution": "clean"} for case_id in sorted(roles)
            ],
            "unresolved_case_ids": [],
        },
        "review/REVIEW_LEDGER.json",
        "ledger_digest",
    )

    ledger = step_labels(sealed_root, config)
    rows = {str(row["case_id"]): row for row in ledger["entries"]}
    assert ledger["label_count"] == 7
    assert rows[AMBIGUOUS_CASE_ID]["label_status"] == "ambiguous_control"
    assert rows[AMBIGUOUS_CASE_ID]["issue_class"] is None
    assert rows[UNSUPPORTED_CASE_ID]["label_status"] == "unsupported_control"
    assert rows[UNSUPPORTED_CASE_ID]["issue_class"] is None
    positives = [row for row in ledger["entries"] if row["label_status"] == "positive_demonstrated"]
    assert sorted(str(row["case_role"]) for row in positives) == [
        "error_bearing",
        "renamed_implementation",
    ]
    assert all(row["issue_class"] == config.canonical_issue_class for row in positives)


def _fake_codex(answer: bytes | None, banner: bytes = b"codex CLI\nmodel: gpt-5.6-sol\n") -> Any:
    """A stand-in for the Codex process that writes its answer file and exits."""

    seen: dict[str, Any] = {}

    def _run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        seen["argv"] = argv
        seen["kwargs"] = kwargs
        if answer is not None:
            (Path(kwargs["cwd"]) / "answer.json").write_bytes(answer)
        return subprocess.CompletedProcess(argv, 0, banner, b"")

    _run.seen = seen  # type: ignore[attr-defined]
    return _run


def test_codex_transport_reads_its_answer_file_and_records_banner_only_verification(
    sealed_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _payload = heldout_config(sealed_root)
    participant = config.authors["actor:heldout-codex-04"]
    assert participant.transport == "codex-cli"
    scratch_root = sealed_root / "scratch"
    monkeypatch.setattr(lean_pipeline, "CODEX_SCRATCH_ROOT", scratch_root)
    runner = _fake_codex(b'{"participant_id":"actor:heldout-codex-04","cases":[]}')
    monkeypatch.setattr(lean_pipeline.subprocess, "run", runner)

    capture_root = sealed_root / "capture"
    result = lean_pipeline._call_cli(
        config, participant, "AUTHOR PROMPT", "session-01", capture_root
    )

    assert result["transport_error"] is None
    assert json.loads(result["raw_response"])["participant_id"] == "actor:heldout-codex-04"
    argv = runner.seen["argv"]
    assert argv[1:6] == ["exec", "-m", "gpt-5.6-sol", "--sandbox", "workspace-write"]
    assert argv[6] == "--skip-git-repo-check"
    assert argv[7].startswith("AUTHOR PROMPT")
    assert (
        argv[7]
        .rstrip()
        .endswith(
            "Write your complete JSON answer as the only content of a file named answer.json in "
            "the current working directory. Do not print the JSON to the transcript."
        )
    )
    assert runner.seen["kwargs"]["stdin"] is subprocess.DEVNULL
    assert runner.seen["kwargs"]["timeout"] == lean_pipeline.CLI_TIMEOUT_SECONDS
    scratch = scratch_root / "codex-author-session-01"
    assert Path(runner.seen["kwargs"]["cwd"]) == scratch
    assert (scratch / "prompt.txt").read_text(encoding="utf-8") == argv[7]

    record = json.loads((capture_root / "capture.json").read_text("utf-8"))
    assert record["transport"] == "codex-cli"
    assert record["model_flag"] == ["-m", "gpt-5.6-sol"]
    assert record["served_model_verification"] == "banner_only"
    assert record["served_model_banner_line"] == "model: gpt-5.6-sol"
    assert record["prompt_digest"] == sha256_digest("AUTHOR PROMPT")
    assert record["answer_digest"] == sha256_digest((capture_root / "answer.json").read_bytes())
    assert (capture_root / "answer.json").read_bytes() == result["raw_response"].encode("utf-8")

    # A crash resume replays the retained answer bytes without a second call.
    def _forbidden(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("A retained Codex call must never run a second process.")

    monkeypatch.setattr(lean_pipeline.subprocess, "run", _forbidden)
    resumed = lean_pipeline._call_cli(
        config, participant, "AUTHOR PROMPT", "session-01", capture_root
    )
    assert resumed["raw_response"] == result["raw_response"]
    assert resumed["transport_error"] is None


def test_codex_transport_retains_a_capture_when_no_answer_file_appears(
    sealed_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _payload = heldout_config(sealed_root)
    participant = config.authors["actor:heldout-codex-06"]
    monkeypatch.setattr(lean_pipeline, "CODEX_SCRATCH_ROOT", sealed_root / "scratch")
    monkeypatch.setattr(lean_pipeline.subprocess, "run", _fake_codex(None))
    capture_root = sealed_root / "capture"
    result = lean_pipeline._call_cli(config, participant, "PROMPT", "session-02", capture_root)
    assert result["transport_error"] == "missing_answer_file"
    assert result["raw_response"] == ""
    record = json.loads((capture_root / "capture.json").read_text("utf-8"))
    assert record["transport_error"] == "missing_answer_file"
    assert record["answer_digest"] is None
    assert record["stdout_digest"] == sha256_digest((capture_root / "stdout.bin").read_bytes())
    assert not (capture_root / "answer.json").exists()


def test_unknown_transport_fails_closed(sealed_root: Path) -> None:
    config, _payload = heldout_config(sealed_root)
    participant = replace(config.reviewer, transport="carrier-pigeon")
    with pytest.raises(LeanPipelineError, match="Unknown participant transport"):
        lean_pipeline._call_cli(config, participant, "PROMPT", "session-03", sealed_root / "x")


def test_label_status_vocabulary_is_closed(sealed_root: Path) -> None:
    config, _payload = heldout_config(sealed_root)
    widened = {**dict(config.label_status_by_role or {}), "ambiguous": "probably_fine"}
    reconfigured = replace(config, label_status_by_role=widened)
    with pytest.raises(LeanPipelineError, match="outside the frozen vocabulary"):
        reconfigured.label_status("ambiguous")
    with pytest.raises(LeanPipelineError, match="No label status is configured"):
        config.label_status("not_a_role")


def test_contract_free_role_audits_without_a_method_contract_lock(sealed_root: Path) -> None:
    config, _payload = heldout_config(sealed_root)
    assert "ambiguous" in config.contract_free_roles
    assert "ambiguous" not in config.candidate_by_role

    root = sealed_root / config.pipeline_relative
    slug = AMBIGUOUS_CASE_ID.removeprefix("case:")
    case_root = root / "authoring" / "cases" / slug
    (case_root / "inputs").mkdir(parents=True)
    (case_root / "workflow").mkdir()
    (case_root / "results").mkdir()
    (case_root / "inputs/data.csv").write_text(MINIMAL_CSV, encoding="utf-8")
    (case_root / "workflow/analysis.py").write_text(MINIMAL_WORKFLOW, encoding="utf-8")
    (case_root / "results/report.md").write_text(MINIMAL_REPORT, encoding="utf-8")

    registry_bytes = (sealed_root / REGISTRY_RELATIVE).read_bytes()
    protocol = _record_step(
        sealed_root,
        config,
        "authoring",
        {
            "artifact_kind": "lean_pipeline_authoring_protocol",
            "envelope_id": config.envelope_id,
            "case_role_assignments": {AMBIGUOUS_CASE_ID: "ambiguous"},
            "detector_tuple": {
                "check_id": config.check_id,
                "check_version": "2.0.7",
                "registry_content_digest": sha256_digest(registry_bytes),
            },
            "detector_tuple_digest": "sha256:" + "1" * 64,
        },
        "authoring/AUTHORING_PROTOCOL.json",
        "protocol_digest",
    )
    _record_step(
        sealed_root,
        config,
        "labels",
        {
            "artifact_kind": "lean_pipeline_scientific_label_ledger",
            "envelope_id": config.envelope_id,
            "authoring_protocol_digest": protocol["protocol_digest"],
            "detector_output_observed": False,
            "entries": [
                {
                    "case_id": AMBIGUOUS_CASE_ID,
                    "case_role": "ambiguous",
                    "label_status": "ambiguous_control",
                    "issue_class": None,
                }
            ],
        },
        "SCIENTIFIC_LABEL_LEDGER.json",
        "ledger_digest",
    )

    ledger = step_detector(sealed_root, config)
    row = ledger["entries"][0]
    assert row["case_role"] == "ambiguous"
    assert row["method_contract_applied"] is False
    assert row["contract_candidate_id"] is None
    assert not (root / "detector-run" / "runs" / slug / "contract").exists()
    assert (root / "detector-run" / "runs" / slug / "audit" / "semantic.lock.json").is_file()
    assert row["detector_positive"] is False
    assert row["comparison_outcome"] == "true_negative"
    assert row["production_findings"] == 0
    assert row["replay_equal"] is True
    metrics = ledger["pilot_metrics"]
    assert metrics["false_accusation_count"] == 0
    assert metrics["true_negative_count"] == 1
