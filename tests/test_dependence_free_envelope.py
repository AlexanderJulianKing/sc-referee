"""Development-only tests for the dependence-free growth envelope."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import pytest
from sc_referee_evaluation import dependence_promotion, lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    LeanPipelineError,
    step_authority,
    step_detector,
    step_intake,
    step_labels,
    step_review,
)

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    installed_pin_matches_live_identity,
    load_method_conflict_grant_evidence,
)
from scripts.lean_pipeline import (
    DEPENDENCE_FREE_LANE_RELATIVE,
    DEPENDENCE_SANDBOX_PYTHON,
    ENVELOPE_CONFIGS,
    default_dependence_config,
    default_dependence_free_config,
    default_founder_orientation_config,
    default_founder_orientation_f_config,
)

_MEASUREMENT_ROLES = ("rq1", "rq2", "rq3", "rq4", "rq5", "rq6")
_FIXTURE_ROLES = (*_MEASUREMENT_ROLES, "fx1", "fx2", "fx3")
_CASE_BY_ROLE = {
    role: f"case:fixture_nm_{index:02d}_20260812"
    for index, role in enumerate(_FIXTURE_ROLES, start=1)
}
_FIXTURE_RELATIVE = Path("evaluation/development-fixtures/dependence-free-nonmeasurement-v2")
_RUNTIME_AVAILABLE = DEPENDENCE_SANDBOX_PYTHON.is_file()
_REPORT = (
    "[selected-result] TtestResult(statistic=np.float64(-0.9258200997725515), "
    "pvalue=np.float64(0.37634173801911863), df=np.float64(10.0))\n"
)


def _isolated_root(tmp_path: Path, project_root: Path) -> Path:
    (tmp_path / "src").symlink_to(project_root / "src")
    (tmp_path / "reference").symlink_to(project_root / "reference")
    return tmp_path


def _csv(role: str) -> str:
    repeated = role in {"rq1", "rq2", "rq3", "fx1", "fx2", "fx3"}
    units = ["owl-1", "owl-1", "owl-2", "owl-2", "owl-3", "owl-3"]
    if not repeated:
        units = [f"owl-{index}" for index in range(1, 7)]
    sessions = ["dawn", "dawn", "noon", "noon", "dusk", "dusk"]
    if role != "rq6":
        sessions = [f"flight-{index}" for index in range(1, 7)]
    rows = ["bird_code,session,signal,reference"]
    for index, (unit, session) in enumerate(zip(units, sessions, strict=True), start=1):
        rows.append(f"{unit},{session},{index}.0,{index + 1}.0")
    return "\n".join(rows) + "\n"


def _workflow(role: str) -> str:
    if role == "fx1":
        procedure = "ks_2samp"
    else:
        procedure = "ttest_ind"
    if role == "fx3":
        reader = """with Path("data/input.csv").open(encoding="utf-8", newline="") as handle:
    table = list(csv.reader(handle))
rows = [dict(zip(table[0], values, strict=True)) for values in table[1:]]"""
    else:
        reader = """rows = list(csv.DictReader(Path("data/input.csv").read_text(encoding="utf-8").splitlines()))"""
    return f"""import csv
from pathlib import Path
import scipy.stats as st

{reader}
observed = [float(row["signal"]) for row in rows]
reference = [float(row["reference"]) for row in rows]
result = st.{procedure}(observed, reference)
Path("results/report.md").write_text(f"[selected-result] {{result}}\\n", encoding="utf-8")
"""


def _report(role: str) -> str:
    if role == "fx1":
        return "[selected-result] KstestResult(statistic=np.float64(0.16666666666666666), pvalue=np.float64(0.9999999999999998), statistic_location=np.float64(5.0), statistic_sign=np.int8(1))\n"
    return _REPORT


def _description(role: str) -> str:
    if role == "fx2":
        return "One row represents a bird observation.\nIndependent unit columns: bird_code\n"
    return (
        "One row is: one recorded bird observation used by the analysis.\n"
        "Independent unit column: bird_code\n"
    )


def _case(role: str) -> dict[str, Any]:
    return {
        "case_id": _CASE_BY_ROLE[role],
        "input_csv": _csv(role),
        "analysis_py": _workflow(role),
        "report_md": _report(role),
        "data_description": _description(role),
        "selected_result_line": 1,
    }


def _fixture_config(roles: tuple[str, ...] = _FIXTURE_ROLES) -> Any:
    base = default_dependence_free_config()
    expected = {
        role: (
            "demonstrated_issue"
            if role in {"rq1", "rq2", "rq3"}
            else "no_demonstrated_issue_within_scope"
        )
        for role in roles
    }
    statuses = {
        role: (
            "positive_demonstrated" if role in {"rq1", "rq2", "rq3"} else "verified_good_eligible"
        )
        for role in roles
    }
    candidate = "one-analyzed-row-per-authorized-independent-unit"
    return replace(
        base,
        envelope_id="development-dependence-nonmeasurement-fixture-v2",
        pipeline_relative=_FIXTURE_RELATIVE,
        authors={},
        author_roles={},
        candidate_by_role={role: candidate for role in roles},
        task_by_role={role: base.common_task for role in roles},
        role_constraints={role: [] for role in roles},
        expected_verdict_by_role=expected,
        label_status_by_role=statuses,
        hostile_answer_key_reviewer=None,
        record_purpose="development_nonmeasurement_fixture",
    )


def _freeze_fixture_inputs(root: Path, config: Any) -> None:
    """Feed orchestrator-written bytes straight to intake without model identities."""

    registry_path = root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    module = next(item for item in registry["modules"] if item["check_id"] == config.check_id)
    binding = next(
        item for item in registry["method_conflict_bindings"] if item["check_id"] == config.check_id
    )
    detector_tuple = {
        "check_id": config.check_id,
        "check_version": module["check_version"],
        "check_manifest_digest": module["manifest_digest"],
        "adapters": module["adapters"],
        "method_conflict_binding_digest": semantic_digest(binding),
        "registry_content_digest": sha256_digest(registry_path.read_bytes()),
        "production_finding_permitted": False,
        "detector_id": config.detector_id,
    }
    roles = tuple((config.expected_verdict_by_role or {}).keys())
    case_ids = [_CASE_BY_ROLE[role] for role in roles]
    schema = lean_pipeline._author_output_schema(
        "controller:nonmeasurement-fixture", case_ids, config
    )
    protocol = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "protocol_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "adr_references": [],
        "detector_tuple": detector_tuple,
        "detector_tuple_digest": semantic_digest(detector_tuple),
        "case_role_assignments": {_CASE_BY_ROLE[role]: role for role in roles},
        "author_assignments": [
            {
                "participant": {"participant_id": "controller:nonmeasurement-fixture"},
                "case_ids": case_ids,
                "output_schema": schema,
            }
        ],
        "execution_policy": {
            "orchestrator_written_fixture": True,
            "model_calls": 0,
            "qualification_evidence": False,
        },
        "frozen_at": "2026-08-12T00:00:00Z",
        "qualification_authority": "none_fixture_only",
        "record_purpose": config.record_purpose,
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    authoring = root / config.pipeline_relative / "authoring"
    authoring.mkdir(parents=True)
    lean_pipeline.write_normalized_json_once(authoring / "AUTHORING_PROTOCOL.json", protocol)
    payload = {
        "participant_id": "controller:nonmeasurement-fixture",
        "cases": [_case(role) for role in roles],
    }
    attempt = {
        "participant_id": "controller:nonmeasurement-fixture",
        "protocol_digest": protocol["protocol_digest"],
        "raw_response": canonical_json(payload),
    }
    (authoring / "incoming").mkdir()
    lean_pipeline.write_normalized_json_once(
        authoring / "incoming" / "controller:nonmeasurement-fixture.json", attempt
    )
    lean_pipeline._manifest_record(
        root,
        config,
        "authoring",
        digest=protocol["protocol_digest"],
        relative_path="authoring/AUTHORING_PROTOCOL.json",
    )


def _freeze_fixture_labels(root: Path, config: Any, authority: dict[str, Any]) -> None:
    lane = root / config.pipeline_relative
    protocol = json.loads((lane / "authoring/AUTHORING_PROTOCOL.json").read_text(encoding="utf-8"))
    intake = json.loads((lane / "authoring/INTAKE_LEDGER.json").read_text(encoding="utf-8"))
    intake_by_role = {entry["case_role"]: entry for entry in intake["entries"]}
    review = {
        "artifact_kind": "lean_pipeline_review_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "authority_ledger_digest": authority["ledger_digest"],
        "entries": [],
        "unblinding_record": [],
        "unresolved_case_ids": [],
        "record_purpose": config.record_purpose,
    }
    review["ledger_digest"] = semantic_digest(review)
    (lane / "review").mkdir()
    lean_pipeline.write_normalized_json_once(lane / "review/REVIEW_LEDGER.json", review)
    lean_pipeline._manifest_record(
        root,
        config,
        "review",
        digest=review["ledger_digest"],
        relative_path="review/REVIEW_LEDGER.json",
    )
    labels = {
        "artifact_kind": "lean_pipeline_scientific_label_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "authoring_protocol_digest": protocol["protocol_digest"],
        "review_ledger_digest": review["ledger_digest"],
        "entries": [
            {
                "case_id": _CASE_BY_ROLE[role],
                "case_role": role,
                "label_status": config.label_status(role),
                **(
                    {
                        "measurement_state": "refused_at_intake",
                        "intake_admission_reason": intake_by_role[role]["intake_admission_reason"],
                    }
                    if intake_by_role[role].get("intake_admission_state")
                    == "refused_but_case_retained"
                    else {}
                ),
            }
            for role in (config.expected_verdict_by_role or {})
        ],
        "detector_output_observed": False,
        "record_purpose": config.record_purpose,
    }
    labels["ledger_digest"] = semantic_digest(labels)
    lean_pipeline.write_normalized_json_once(lane / "SCIENTIFIC_LABEL_LEDGER.json", labels)
    lean_pipeline._manifest_record(
        root,
        config,
        "labels",
        digest=labels["ledger_digest"],
        relative_path="SCIENTIFIC_LABEL_LEDGER.json",
    )


def test_dependence_free_config_conforms_to_closed_growth_envelope() -> None:
    config = default_dependence_free_config()
    assert ENVELOPE_CONFIGS["dependence-free"] is default_dependence_free_config
    assert config.pipeline_relative == Path("evaluation/development/dependence-growth-loop/batch-a")
    assert config.frozen_workflow_template is None
    assert config.authored_input_csv_path == "data/input.csv"
    assert config.authored_data_description_path == "data-description.md"
    assert config.input_csv_row_bounds == (1, 10_000)
    assert config.allow_unprescribed_input_csv_header is True
    assert set(config.roles) == set(_MEASUREMENT_ROLES)
    assert config.stateless_review_per_case is True
    assert config.freeze_role_key_in_review_protocol is True
    assert config.record_purpose == "development_growth_loop"
    assert config.development_loop is True
    assert config.hostile_answer_key_reviewer is not None
    assert config.hostile_answer_key_reviewer.participant_id.endswith("fable-17")
    assert set(config.allowed_import_roots) >= {"numpy", "scipy", "statsmodels"}
    assert {
        "os",
        "sys",
        "typing",
        "dataclasses",
        "warnings",
        "datetime",
        "operator",
        "math",
        "statistics",
        "itertools",
        "functools",
        "collections",
        "csv",
        "json",
        "pathlib",
        "random",
        "string",
        "textwrap",
    } <= set(config.allowed_import_roots)
    assert ", ".join(sorted(config.allowed_import_roots)) in config.author_case_requirements
    assert config.reviewer_task_text == (
        "Assess whether the selected report's stated statistical conclusion is supported "
        "by the provided workflow and input data."
    )
    assert "sc-referee" not in config.reviewer_task_text
    assert set(config.utf8_authored_paths) == {"data-description.md", "results/report.md"}
    assert len(set(config.task_by_role.values())) == 1
    assert len(set(config.candidate_by_role.values())) == 1
    author_visible = "\n".join(
        [config.common_task, config.author_case_requirements]
        + [line for role in config.roles for line in config.role_constraints[role]]
    ).casefold()
    assert all(word not in author_visible for word in ("positive", "control", "hard control"))
    assert default_dependence_config().frozen_workflow_template is not None
    assert default_dependence_config().authored_input_csv_path == "inputs/data.csv"
    assert default_dependence_config().development_loop is False
    assert default_founder_orientation_f_config().frozen_workflow_template is None


def test_installed_dependence_grant_refuses_recognition_grammar_drift() -> None:
    binding_id = "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
    pin = GRANT_PINS[binding_id]
    changed_identity = replace(
        pin.exam_adapter_identity[0], recognition_grammar_digest="sha256:" + "0" * 64
    )
    assert installed_pin_matches_live_identity(pin) is True
    assert (
        installed_pin_matches_live_identity(replace(pin, exam_adapter_identity=(changed_identity,)))
        is False
    )
    assert (
        load_method_conflict_grant_evidence(replace(pin, exam_adapter_identity=(changed_identity,)))
        is None
    )


def test_dependence_round2_rederivation_refuses_grammar_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dependence_promotion,
        "live_adapter_identity",
        lambda _binding: (),
    )
    with pytest.raises(
        dependence_promotion.DependencePromotionError, match="identity is not exact"
    ):
        dependence_promotion._round2_live_identity()


def test_existing_qualification_retained_review_capture_still_binds(
    project_root: Path,
) -> None:
    config = default_founder_orientation_config()
    review_root = project_root / (
        "evaluation/qualification/founder-orientation-before-hmm-emission-v2.1.5-lane/"
        "pilot-a/review"
    )
    capture_root = review_root / "process-captures/primary-founder-a-reviewer-fable-01"
    capture = json.loads((capture_root / "capture.json").read_text(encoding="utf-8"))
    protocol = json.loads(
        (review_root.parent / "authoring/AUTHORING_PROTOCOL.json").read_text(encoding="utf-8")
    )
    expected_call_id = str(
        uuid5(
            NAMESPACE_URL,
            f"sc-referee:lean-pipeline-review:{config.envelope_id}:primary:"
            f"{config.reviewer.participant_id}:{protocol['detector_tuple_digest']}",
        )
    )
    assert capture["session_id"] == expected_call_id
    retained = lean_pipeline._retained_call(
        config.reviewer,
        (review_root / "prompt-primary.txt").read_text(encoding="utf-8"),
        expected_call_id,
        capture_root,
    )
    assert retained is not None
    assert retained["process_record"]["capture_digest"] == capture["capture_digest"]


@pytest.mark.skipif(not _RUNTIME_AVAILABLE, reason="dedicated SciPy 1.14.0 runtime is absent")
def test_model_free_nonmeasurement_fixture_executes_and_records_abstentions(
    tmp_path: Path, project_root: Path
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    config = _fixture_config()
    assert not config.pipeline_relative.is_relative_to(DEPENDENCE_FREE_LANE_RELATIVE)
    marker = isolated / config.pipeline_relative / "NON_MEASUREMENT_FIXTURE.json"
    marker.parent.mkdir(parents=True)
    marker.write_text(
        canonical_json(
            {
                "artifact_kind": "dependence_free_nonmeasurement_fixture_marker",
                "measurement_lane_reachable": False,
                "model_calls": 0,
                "qualification_evidence": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _freeze_fixture_inputs(isolated, config)
    intake = step_intake(isolated, config)
    assert intake["case_count"] == 9
    assert all(entry["sandbox_runs"] == 2 for entry in intake["entries"])
    authority = step_authority(isolated, config)
    translations = {
        next(role for role, case_id in _CASE_BY_ROLE.items() if case_id == entry["case_id"]): entry
        for entry in authority["entries"]
    }
    assert (
        translations["fx1"]["translation_outcome"] == "procedure-unavailable-to-closed-lock-schema"
    )
    assert translations["fx2"]["translation_outcome"] == "unit-declaration-missing-or-malformed"
    assert translations["fx3"]["translation_outcome"] == "lock-minted"
    _freeze_fixture_labels(isolated, config, authority)
    detector = step_detector(isolated, config)
    by_role = {entry["case_role"]: entry for entry in detector["entries"]}
    assert {
        role: (
            by_role[role]["shadow_payload"]["state"],
            by_role[role]["shadow_payload"]["observations"][0]["abstention_reason"],
        )
        for role in ("fx1", "fx2", "fx3")
    } == {
        "fx1": ("unsupported", "dependence-shadow-abstention"),
        "fx2": ("ambiguous", "independent-unit-definition-unresolved"),
        "fx3": ("unsupported", "dependence-shadow-abstention"),
    }
    assert {role: by_role[role]["comparison_outcome"] for role in ("fx1", "fx2", "fx3")} == {
        "fx1": "abstained_no_authority",
        "fx2": "abstained_no_authority",
        "fx3": "abstained_unsupported",
    }
    assert {role: by_role[role]["comparison_outcome"] for role in _MEASUREMENT_ROLES} == {
        "rq1": "caught",
        "rq2": "caught",
        "rq3": "caught",
        "rq4": "true_negative",
        "rq5": "true_negative",
        "rq6": "true_negative",
    }
    assert all(by_role[role]["replay_equal"] is True for role in _FIXTURE_ROLES)
    assert marker.is_file()

    detector_root = isolated / config.pipeline_relative / "detector-run"
    (detector_root / "DETECTOR_RUN_LEDGER.json").unlink()
    manifest_path = isolated / config.pipeline_relative / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["steps"].pop("detector")
    lean_pipeline.write_normalized_json(manifest_path, manifest)
    retained_path = (
        detector_root / "case-results" / (_CASE_BY_ROLE["rq1"].removeprefix("case:") + ".json")
    )
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    retained.pop("case_result_digest")
    retained["scientific_label_ledger_digest"] = "sha256:" + "0" * 64
    retained["case_result_digest"] = semantic_digest(retained)
    lean_pipeline.write_normalized_json(retained_path, retained)
    with pytest.raises(LeanPipelineError, match="stale bindings"):
        step_detector(isolated, config)


def test_growth_intake_retains_one_crashing_case_without_changing_shared_path(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    config = _fixture_config(("rq1", "rq4", "rq5"))
    config = replace(
        config,
        pipeline_relative=Path("evaluation/development-fixtures/crash-retained"),
        record_purpose="development_growth_loop",
    )
    _freeze_fixture_inputs(isolated, config)
    incoming = (
        isolated
        / config.pipeline_relative
        / "authoring/incoming/controller:nonmeasurement-fixture.json"
    )
    attempt = json.loads(incoming.read_text(encoding="utf-8"))
    payload = json.loads(attempt["raw_response"])
    payload["cases"][0]["analysis_py"] = "raise RuntimeError('fixture crash')\n"
    attempt["raw_response"] = canonical_json(payload)
    lean_pipeline.write_normalized_json(incoming, attempt)
    intake = step_intake(isolated, config)
    first = next(entry for entry in intake["entries"] if entry["case_role"] == "rq1")
    assert first["intake_admission_state"] == "refused_but_case_retained"
    assert "fixture crash" in first["intake_admission_reason"]
    assert len(intake["entries"]) == 3
    lane = isolated / config.pipeline_relative
    (lane / "authoring/INTAKE_LEDGER.json").unlink()
    manifest_path = lane / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["steps"].pop("intake")
    lean_pipeline.write_normalized_json(manifest_path, manifest)
    intake = step_intake(isolated, config)
    assert [entry["intake_admission_state"] for entry in intake["entries"]] == [
        "refused_but_case_retained",
        "admitted",
        "admitted",
    ]
    authority = step_authority(isolated, config)
    authority_by_role = {
        next(role for role, value in _CASE_BY_ROLE.items() if value == entry["case_id"]): entry
        for entry in authority["entries"]
    }
    assert authority_by_role["rq1"]["authority_state"] == "excluded_intake_refusal"
    _freeze_fixture_labels(isolated, config, authority)
    original_run_audit = lean_pipeline.run_audit
    calls = 0

    def fail_one_case(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected per-case detector failure")
        return original_run_audit(*args, **kwargs)

    monkeypatch.setattr(lean_pipeline, "run_audit", fail_one_case)
    detector = step_detector(isolated, config)
    by_role = {entry["case_role"]: entry for entry in detector["entries"]}
    assert by_role["rq1"]["comparison_outcome"] == "refused_at_intake"
    assert by_role["rq4"]["detector_failure_class"] == "RuntimeError"
    assert by_role["rq5"]["replay_equal"] is True
    retained = isolated / config.pipeline_relative / "detector-run/case-results"
    assert len(list(retained.glob("*.json"))) == 3


def test_growth_intake_retains_static_refusal_and_accepts_utf8_prose_and_token_substrings(
    tmp_path: Path, project_root: Path
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    config = replace(
        _fixture_config(("rq1", "rq4")),
        pipeline_relative=Path("evaluation/development-fixtures/static-refusal-retained"),
        record_purpose="development_growth_loop",
        development_loop=True,
    )
    _freeze_fixture_inputs(isolated, config)
    incoming = (
        isolated
        / config.pipeline_relative
        / ("authoring/incoming/controller:nonmeasurement-fixture.json")
    )
    attempt = json.loads(incoming.read_text(encoding="utf-8"))
    payload = json.loads(attempt["raw_response"])
    rq1 = next(item for item in payload["cases"] if item["case_id"] == _CASE_BY_ROLE["rq1"])
    rq1["analysis_py"] = "import requests\n" + rq1["analysis_py"]
    rq4 = next(item for item in payload["cases"] if item["case_id"] == _CASE_BY_ROLE["rq4"])
    rq4["analysis_py"] = rq4["analysis_py"].replace(
        "{result}\\n", "{result} \\u2013 R\\u00e9sum\\u00e9 SRQ1\\n"
    )
    rq4["report_md"] = rq4["report_md"].replace(
        "\n", f" {chr(0x2013)} R{chr(0xE9)}sum{chr(0xE9)} SRQ1\n"
    )
    rq4["data_description"] = rq4["data_description"].replace("one recorded", "one café-recorded")
    rq4["selected_result_line"] = 1
    attempt["raw_response"] = canonical_json(payload)
    lean_pipeline.write_normalized_json(incoming, attempt)
    intake = step_intake(isolated, config)
    by_role = {entry["case_role"]: entry for entry in intake["entries"]}
    assert by_role["rq1"]["intake_admission_state"] == "refused_but_case_retained"
    assert by_role["rq4"]["intake_admission_state"] == "admitted"
    authority = step_authority(isolated, config)
    authority_by_case = {entry["case_id"]: entry for entry in authority["entries"]}
    assert authority_by_case[_CASE_BY_ROLE["rq1"]]["authority_state"] == "excluded_intake_refusal"


def test_description_is_required_by_the_author_schema() -> None:
    config = default_dependence_free_config()
    schema = lean_pipeline._author_output_schema("actor:test", ["case:test"], config)
    required = schema["properties"]["cases"]["items"]["required"]
    assert "data_description" in required
    with pytest.raises(LeanPipelineError, match="outside the frozen envelope"):
        lean_pipeline._validate_bounded_input_csv(
            "free,header\na,b\n",
            replace(config, allow_unprescribed_input_csv_header=False),
        )
    assert (
        lean_pipeline._description_unit_column(
            "ONE ROW IS: a sample\nINDEPENDENT UNIT COLUMN:    subject_id\n"
        )
        == "subject_id"
    )
    assert (
        lean_pipeline._description_unit_column(
            "One row is:\nvalue on next line\nIndependent unit column:\nsubject_id\n"
        )
        is None
    )
    assert lean_pipeline._registered_dependence_callable(
        "import scipy.stats as st\na=st.pearsonr(x,y)\nb=st.ttest_ind(x,y)\n"
    ) == (None, "procedure-ambiguous-multiple-statistical-calls")


@pytest.mark.skipif(not _RUNTIME_AVAILABLE, reason="dedicated SciPy 1.14.0 runtime is absent")
def test_review_key_is_presealed_and_primary_calls_are_stateless_per_case(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    config = _fixture_config(_MEASUREMENT_ROLES)
    config = replace(
        config,
        pipeline_relative=Path("evaluation/development-fixtures/review-protocol-mechanics"),
        hostile_answer_key_reviewer=default_dependence_free_config().hostile_answer_key_reviewer,
        record_purpose="development_growth_loop",
    )
    _freeze_fixture_inputs(isolated, config)
    step_intake(isolated, config)
    step_authority(isolated, config)
    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda _root, _config: {})
    hostile_prompts: list[str] = []

    def hostile_transport(
        _selected: Any,
        _participant: Any,
        prompt: str,
        _session: str,
        _capture: Path,
    ) -> dict[str, Any]:
        hostile_prompts.append(prompt)
        issue = prompt.count("owl-1,") == 2
        answer = {
            "declaration_consistent": True,
            "selected_report_demonstration": "issue" if issue else "absence",
            "lock_follows_declaration": True,
            "reasons": ["fixture answer-key review"],
        }
        return {
            "raw_response": canonical_json(answer),
            "transport_error": None,
            "process_record": {"capture_digest": semantic_digest(answer)},
            "completed_at": "2026-08-12T00:00:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", hostile_transport)
    calls: list[tuple[str, ...]] = []

    def review_call(
        _root: Path,
        selected: Any,
        _review_root: Path,
        participant: Any,
        case_subset: list[str],
        _preparations: dict[str, dict[str, Any]],
        _workspaces: dict[str, dict[str, bytes]],
        _binding_digest: str,
        label: str,
    ) -> dict[str, Any]:
        calls.append(tuple(case_subset))
        entries = []
        for case_id in case_subset:
            role = next(role for role, value in _CASE_BY_ROLE.items() if value == case_id)
            verdict = selected.expected_verdict(role)
            if role == "rq6":
                verdict = "demonstrated_issue"
            entries.append(
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": f"review:{case_id.removeprefix('case:')}",
                    "review_digest": "sha256:" + "1" * 64,
                    "packet_digest": "sha256:" + "2" * 64,
                    "capture_digest": "sha256:" + "3" * 64,
                    "verdict": verdict,
                    "issue_class": (
                        selected.canonical_issue_class if verdict == "demonstrated_issue" else None
                    ),
                    "unresolved_material_question_count": 0,
                }
            )
        return {
            "entries": entries,
            "call_identity_id": label,
            "prompt_digest": "sha256:" + "4" * 64,
            "output_schema_digest": "sha256:" + "5" * 64,
            "shared_transcript_digest": "sha256:" + "6" * 64,
            "packet_digests": {case_id: "sha256:" + "2" * 64 for case_id in case_subset},
        }

    monkeypatch.setattr(lean_pipeline, "_run_review_call", review_call)
    ledger = step_review(isolated, config)
    assert len(hostile_prompts) == 6
    assert all("considering both procedure arms" in prompt for prompt in hostile_prompts)
    assert all("unit-key authorization follow" in prompt for prompt in hostile_prompts)
    assert len(calls) == 6
    assert all(len(call) == 1 for call in calls)
    protocol = json.loads(
        (isolated / config.pipeline_relative / "review/REVIEW_PROTOCOL.json").read_text(
            encoding="utf-8"
        )
    )
    assert protocol["role_expected_verdict_map"] == config.expected_verdict_by_role
    assert protocol["role_label_status_map"] == config.label_status_by_role
    assert ledger["record_purpose"] == "development_growth_loop"
    resolution_by_role = {
        row["case_role"]: row["resolution"] for row in ledger["unblinding_record"]
    }
    assert resolution_by_role["rq6"] == "authored_role_refuted"
    assert all(
        resolution_by_role[role] == "authored_role_ratified"
        for role in _MEASUREMENT_ROLES
        if role != "rq6"
    )
    labels = step_labels(isolated, config)
    rq6_label = next(row for row in labels["entries"] if row["case_role"] == "rq6")
    assert rq6_label["label_status"] == "verified_good_eligible"
    assert rq6_label["measurement_state"] == "burned_refuted_authored_role"
    retained_hostile = lean_pipeline._run_hostile_answer_key_review(
        isolated,
        config,
        isolated / config.pipeline_relative / "review",
        [_CASE_BY_ROLE[role] for role in _MEASUREMENT_ROLES],
        {_CASE_BY_ROLE[role]: role for role in _MEASUREMENT_ROLES},
    )
    assert retained_hostile is not None
    assert len(hostile_prompts) == 6


@pytest.mark.skipif(not _RUNTIME_AVAILABLE, reason="dedicated SciPy 1.14.0 runtime is absent")
def test_false_accusation_halts_and_preserves_per_case_outputs(
    tmp_path: Path, project_root: Path
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    config = replace(
        _fixture_config(("rq1", "rq2", "rq3", "rq4")),
        pipeline_relative=Path("evaluation/development-fixtures/fa-halt"),
        record_purpose="development_growth_loop",
    )
    _freeze_fixture_inputs(isolated, config)
    incoming = (
        isolated
        / config.pipeline_relative
        / "authoring/incoming/controller:nonmeasurement-fixture.json"
    )
    attempt = json.loads(incoming.read_text(encoding="utf-8"))
    payload = json.loads(attempt["raw_response"])
    rq4 = next(item for item in payload["cases"] if item["case_id"] == _CASE_BY_ROLE["rq4"])
    rq4["input_csv"] = _csv("rq1")
    attempt["raw_response"] = canonical_json(payload)
    lean_pipeline.write_normalized_json(incoming, attempt)
    step_intake(isolated, config)
    authority = step_authority(isolated, config)
    _freeze_fixture_labels(isolated, config, authority)
    with pytest.raises(LeanPipelineError, match="halted on false accusation"):
        step_detector(isolated, config)
    detector_root = isolated / config.pipeline_relative / "detector-run"
    halt = json.loads((detector_root / "FALSE_ACCUSATION_HALT.json").read_text(encoding="utf-8"))
    assert halt["case_id"] == _CASE_BY_ROLE["rq4"]
    assert halt["reclassification_permitted"] is False
    assert len(list((detector_root / "case-results").glob("*.json"))) == 4
    (detector_root / "FALSE_ACCUSATION_HALT.json").unlink()
    with pytest.raises(LeanPipelineError, match="halted on false accusation"):
        step_detector(isolated, config)
    assert (detector_root / "FALSE_ACCUSATION_HALT.json").is_file()
