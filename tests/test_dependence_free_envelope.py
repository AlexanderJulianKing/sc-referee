"""Development-only tests for the dependence-free growth envelope."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import pytest
from sc_referee_evaluation import dependence_promotion, lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    LeanPipelineError,
    step_authoring,
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
    default_dependence_free_b_config,
    default_dependence_free_config,
    default_dependence_free_e1_config,
    default_dependence_free_e2_config,
    default_dependence_free_f1_config,
    default_dependence_free_f2_config,
    default_dependence_free_g1_config,
    default_dependence_free_g2_config,
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
    assert "__future__" in config.allowed_import_roots
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
    lean_pipeline._static_guard("from __future__ import annotations\n", config.allowed_import_roots)
    with pytest.raises(LeanPipelineError, match="imports a forbidden module"):
        lean_pipeline._static_guard(
            "from __future__ import annotations\n",
            default_dependence_config().allowed_import_roots,
        )
    assert default_founder_orientation_f_config().frozen_workflow_template is None

    batch_b = default_dependence_free_b_config()
    assert ENVELOPE_CONFIGS["dependence-free-b"] is default_dependence_free_b_config
    assert batch_b.pipeline_relative == Path(
        "evaluation/development/dependence-growth-loop/batch-b"
    )
    assert batch_b.dependence_v2_development_shadow is True
    assert ENVELOPE_CONFIGS["dependence-free-e1"] is default_dependence_free_e1_config
    assert ENVELOPE_CONFIGS["dependence-free-e2"] is default_dependence_free_e2_config
    assert ENVELOPE_CONFIGS["dependence-free-f1"] is default_dependence_free_f1_config
    assert ENVELOPE_CONFIGS["dependence-free-f2"] is default_dependence_free_f2_config
    assert ENVELOPE_CONFIGS["dependence-free-g1"] is default_dependence_free_g1_config
    assert ENVELOPE_CONFIGS["dependence-free-g2"] is default_dependence_free_g2_config


def test_task_binding_disclosure_is_digest_bound_only_for_development_loop(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda _root, _config: {})

    def retained_failure(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {
            "raw_response": "",
            "transport_error": "test-stop-after-protocol",
            "process_record": {"capture_digest": "sha256:" + "1" * 64},
            "started_at": "2026-08-14T00:00:00Z",
            "completed_at": "2026-08-14T00:00:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", retained_failure)
    configurations = (
        default_dependence_free_config(),
        replace(
            default_dependence_config(),
            pipeline_relative=Path("evaluation/test-only/qualification-disclosure-control"),
        ),
    )
    protocols = []
    for config in configurations:
        with pytest.raises(LeanPipelineError, match="Author calls failed and were retained"):
            step_authoring(isolated, config)
        protocol = json.loads(
            (isolated / config.pipeline_relative / "authoring/AUTHORING_PROTOCOL.json").read_text(
                encoding="utf-8"
            )
        )
        supplied = protocol.pop("protocol_digest")
        assert supplied == semantic_digest(protocol)
        protocols.append(protocol)
    assert protocols[0]["task_binding_disclosure"] == (
        "The governing task.md is a neutral reviewer-directed sentence rather than a "
        "scientific target, unlike qualification envelopes; the method contract binds "
        "the candidate id explicitly."
    )
    assert "task_binding_disclosure" not in protocols[1]


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
    config = replace(_fixture_config(), dependence_v2_development_shadow=True)
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
    rq1_translation = json.loads(
        (
            isolated
            / config.pipeline_relative
            / "authority/translations"
            / f"{_CASE_BY_ROLE['rq1'].removeprefix('case:')}.json"
        ).read_text(encoding="utf-8")
    )
    assert rq1_translation["v1_translation_outcome"] == "lock-minted"
    assert rq1_translation["v1_lock_digest"] == rq1_translation["lock_digest"]
    assert rq1_translation["v1_translation_receipt"]["extracted_token"] == "bird_code"
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
    assert all(
        by_role[role]["development_v2_scored_for_qualification"] is False for role in _FIXTURE_ROLES
    )
    assert all(
        by_role[role]["shadow_payload"]["state"]
        in {"evaluation_candidate", "applicable", "ambiguous", "unsupported"}
        for role in _FIXTURE_ROLES
    )
    assert all(
        by_role[role]["development_v2_shadow_payload"]["delivery_plane"]
        == "unregistered_development_shadow_only"
        for role in _FIXTURE_ROLES
    )
    assert detector["pilot_metrics"]["side_by_side_development_outcomes"] == {
        "registered_v1_scored": {
            "abstained_no_authority": 2,
            "abstained_unsupported": 1,
            "caught": 3,
            "true_negative": 3,
        },
        "dependence_v2_development_shadow_not_qualification_scored": {
            "abstained_no_authority": 2,
            "abstained_unsupported": 4,
            "missed_unsupported": 3,
        },
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
    assert (
        lean_pipeline._description_unit_column(
            "One row is: a sample\r\nIndependent unit column: subject_id\r\n"
        )
        == "subject_id"
    )


def test_dependence_lock_procedure_resolution_has_three_closed_failure_reasons() -> None:
    assert lean_pipeline._registered_dependence_callable(
        "import statsmodels.stats.multitest as mt\nmt.multipletests(values)\n"
    ) == (None, "procedure-unresolved-by-lock-schema-resolver")
    assert lean_pipeline._registered_dependence_callable(
        "import scipy.stats as st\na=st.pearsonr(x,y)\nb=st.ttest_ind(x,y)\n"
    ) == (None, "procedure-ambiguous-multiple-statistical-calls")
    assert lean_pipeline._registered_dependence_callable(
        "from scipy.stats import pearsonr\npearsonr(x, y)\n"
    ) == (None, "procedure-unavailable-to-closed-lock-schema")
    assert lean_pipeline._registered_dependence_callable(
        "import scipy.stats\nscipy.stats.ttest_ind(x, y)\n"
    ) == ("scipy.stats.ttest_ind", "lock-minted")


def test_covered_negative_requires_authority_in_development_scoring() -> None:
    payload = {
        "state": "applicable",
        "observations": [
            {"observed_operand": {"value": "one_analyzed_row_per_authorized_independent_unit"}}
        ],
    }
    assert (
        lean_pipeline._development_nonpositive_outcome(
            expected_positive=False,
            shadow_payload=payload,
            has_authority=False,
        )
        == "abstained_no_authority"
    )
    assert (
        lean_pipeline._development_nonpositive_outcome(
            expected_positive=False,
            shadow_payload=payload,
            has_authority=True,
        )
        == "true_negative"
    )


@pytest.mark.skipif(not _RUNTIME_AVAILABLE, reason="dedicated SciPy 1.14.0 runtime is absent")
def test_hostile_answer_key_lock_question_is_tri_state(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    roles = ("rq1", "fx1", "fx2")
    config = replace(
        _fixture_config(roles),
        pipeline_relative=Path("evaluation/development-fixtures/hostile-tristate"),
        hostile_answer_key_reviewer=default_dependence_free_config().hostile_answer_key_reviewer,
    )
    _freeze_fixture_inputs(isolated, config)
    step_intake(isolated, config)
    step_authority(isolated, config)
    prompts: list[str] = []

    def hostile_transport(
        _selected: Any,
        _participant: Any,
        prompt: str,
        _session: str,
        _capture: Path,
    ) -> dict[str, Any]:
        prompts.append(prompt)
        if "NO LOCK MINTED" not in prompt:
            answer = {
                "declaration_consistent": True,
                "selected_report_demonstration": "issue",
                "lock_follows_declaration": False,
                "reasons": ["locked fixture deliberately fails question three"],
            }
        elif "ks_2samp" in prompt:
            answer = {
                "declaration_consistent": True,
                "selected_report_demonstration": "absence",
                "lock_follows_declaration": "not-applicable-no-lock",
                "reasons": ["lock-less fixture survives questions one and two"],
            }
        else:
            answer = {
                "declaration_consistent": False,
                "selected_report_demonstration": "absence",
                "lock_follows_declaration": "not-applicable-no-lock",
                "reasons": ["lock-less fixture fails question one"],
            }
        return {
            "raw_response": canonical_json(answer),
            "transport_error": None,
            "process_record": {"capture_digest": semantic_digest(answer)},
            "completed_at": "2026-08-14T00:00:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", hostile_transport)
    case_order = [_CASE_BY_ROLE[role] for role in roles]
    ledger = lean_pipeline._run_hostile_answer_key_review(
        isolated,
        config,
        isolated / config.pipeline_relative / "review",
        case_order,
        {_CASE_BY_ROLE[role]: role for role in roles},
    )
    assert ledger is not None
    entries = {entry["case_id"]: entry for entry in ledger["entries"]}
    assert entries[_CASE_BY_ROLE["rq1"]]["burn_reasons"] == [
        "unit-key-authorization-not-derived-from-declaration-alone"
    ]
    assert entries[_CASE_BY_ROLE["fx1"]]["burned_before_blind_review"] is False
    assert entries[_CASE_BY_ROLE["fx1"]]["answer"]["lock_follows_declaration"] == (
        "not-applicable-no-lock"
    )
    assert entries[_CASE_BY_ROLE["fx2"]]["burn_reasons"] == ["unit-declaration-inconsistent"]
    assert sum("answer exactly not-applicable-no-lock" in prompt for prompt in prompts) == 2
    assert ledger["packet_version"] == lean_pipeline.HOSTILE_PACKET_V2_RECEIPT
    assert ledger["packet_digest_domain"] == lean_pipeline.HOSTILE_PACKET_V2_DIGEST_DOMAIN
    assert all("deterministic translation receipt (lane-qualified)" in prompt for prompt in prompts)
    assert all(entry["packet_digest"].startswith("sha256:") for entry in entries.values())


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


def _direct_review_inputs(
    config: Any, review_root: Path
) -> tuple[str, dict[str, dict[str, Any]], dict[str, dict[str, bytes]]]:
    case_id = "case:malformed_review_fixture"
    payloads = {
        str(item["path"]): f"fixture content for {item['path']}\n".encode()
        for item in lean_pipeline._visible_files(config)
    }
    manifest: dict[str, Any] = {
        "record_type": "evaluation_blind_workspace_manifest",
        "workspace_id": "workspace:malformed-review-fixture",
        "created_at": "2026-08-14T00:00:00Z",
        "source_snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": "snapshot:malformed-review-fixture",
        },
        "source_snapshot_digest": "sha256:" + "a" * 64,
        "files": [
            {
                "path": path,
                "content_digest": sha256_digest(payload),
                "byte_size": len(payload),
            }
            for path, payload in sorted(payloads.items())
        ],
        "answer_side_content_copied": False,
        "project_code_executed": False,
    }
    manifest["manifest_digest"] = semantic_digest(manifest)
    review_root.mkdir()
    return case_id, {case_id: {"workspace_manifest": manifest}}, {case_id: payloads}


def test_malformed_primary_capture_replays_as_the_same_per_case_refusal(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = default_dependence_free_config()
    review_root = tmp_path / "review"
    case_id, preparations, workspaces = _direct_review_inputs(config, review_root)
    fresh_calls = 0

    def retained_prose_transport(
        _config: Any,
        participant: Any,
        prompt: str,
        session_id: str,
        capture_root: Path,
    ) -> dict[str, Any]:
        nonlocal fresh_calls
        retained = lean_pipeline._retained_call(participant, prompt, session_id, capture_root)
        if retained is not None:
            return retained
        fresh_calls += 1
        capture_root.mkdir(parents=True)
        stdout = canonical_json({"result": "A prose answer, not JSON."}).encode()
        lean_pipeline.atomic_write_bytes(capture_root / "stdout.bin", stdout)
        lean_pipeline.atomic_write_bytes(capture_root / "stderr.bin", b"")
        capture = {
            "participant_id": participant.participant_id,
            "session_id": session_id,
            "prompt_digest": sha256_digest(prompt),
            "transport_error": None,
            "stdout_digest": sha256_digest(stdout),
            "started_at": "2026-08-14T00:00:01Z",
            "completed_at": "2026-08-14T00:00:02Z",
        }
        capture["capture_digest"] = semantic_digest(capture)
        lean_pipeline.write_normalized_json_once(capture_root / "capture.json", capture)
        replayed = lean_pipeline._retained_call(participant, prompt, session_id, capture_root)
        assert replayed is not None
        return replayed

    monkeypatch.setattr(lean_pipeline, "_call_cli", retained_prose_transport)
    monkeypatch.setattr(lean_pipeline, "_now", lambda: "2026-08-14T00:00:02Z")
    arguments = (
        project_root,
        config,
        review_root,
        config.reviewer,
        [case_id],
        preparations,
        workspaces,
        "sha256:" + "b" * 64,
        "primary-malformed-review-fixture",
    )
    first = lean_pipeline._run_review_call(*arguments)
    second = lean_pipeline._run_review_call(*arguments)
    assert first == second
    assert fresh_calls == 1
    assert first["entries"] == []
    assert first["review_response_refusals"][0]["response_state"] == ("review-response-malformed")
    assert "A prose answer" not in canonical_json(first)


def test_qualification_review_path_still_raises_on_prose_response(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = default_dependence_config()
    review_root = tmp_path / "qualification-review"
    case_id, preparations, workspaces = _direct_review_inputs(config, review_root)
    monkeypatch.setattr(
        lean_pipeline,
        "_call_cli",
        lambda *_args, **_kwargs: {
            "raw_response": "A prose answer, not JSON.",
            "transport_error": None,
            "completed_at": "2026-08-14T00:00:02Z",
        },
    )
    with pytest.raises(json.JSONDecodeError):
        lean_pipeline._run_review_call(
            project_root,
            config,
            review_root,
            config.reviewer,
            [case_id],
            preparations,
            workspaces,
            "sha256:" + "c" * 64,
            "primary",
        )


def test_development_primary_schema_failure_is_a_per_case_refusal(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = default_dependence_free_config()
    review_root = tmp_path / "schema-invalid-review"
    case_id, preparations, workspaces = _direct_review_inputs(config, review_root)
    monkeypatch.setattr(
        lean_pipeline,
        "_call_cli",
        lambda *_args, **_kwargs: {
            "raw_response": canonical_json(
                {
                    "reviewer_participant_id": config.reviewer.participant_id,
                    "reviews": [],
                }
            ),
            "transport_error": None,
            "process_record": {"capture_digest": "sha256:" + "d" * 64},
            "completed_at": "2026-08-14T00:00:02Z",
        },
    )
    result = lean_pipeline._run_review_call(
        project_root,
        config,
        review_root,
        config.reviewer,
        [case_id],
        preparations,
        workspaces,
        "sha256:" + "e" * 64,
        "primary-schema-invalid-fixture",
    )
    assert result["entries"] == []
    assert result["review_response_refusals"][0]["failure_class"] == ("response-schema-invalid")


def test_development_primary_anchoring_failure_has_specific_refusal(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = default_dependence_free_config()
    review_root = tmp_path / "anchoring-invalid-review"
    case_id, preparations, workspaces = _direct_review_inputs(config, review_root)
    monkeypatch.setattr(
        lean_pipeline,
        "_call_cli",
        lambda *_args, **_kwargs: {
            "raw_response": canonical_json(
                {
                    "reviewer_participant_id": config.reviewer.participant_id,
                    "reviews": [{"case_id": case_id}],
                }
            ),
            "transport_error": None,
            "process_record": {"capture_digest": "sha256:" + "a" * 64},
            "completed_at": "2026-08-15T00:00:02Z",
        },
    )

    def anchoring_failure(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ValueError("fixture evidence span does not anchor")

    monkeypatch.setattr(lean_pipeline, "_anchor_review_spans", anchoring_failure)
    result = lean_pipeline._run_review_call(
        project_root,
        config,
        review_root,
        config.reviewer,
        [case_id],
        preparations,
        workspaces,
        "sha256:" + "f" * 64,
        "primary-anchoring-invalid-fixture",
    )
    assert result["entries"] == []
    assert result["review_response_refusals"][0]["failure_class"] == ("evidence-anchoring-failed")


def test_development_call_concurrency_preserves_fixture_captures_and_ledger_order(
    tmp_path: Path,
) -> None:
    case_ids = [f"case:fixture_concurrency_{index}" for index in range(6)]

    def run(config: Any, root: Path) -> tuple[dict[str, bytes], bytes, int]:
        active = 0
        maximum = 0
        lock = threading.Lock()

        def callback(case_id: str) -> dict[str, str]:
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            try:
                time.sleep(0.02)
                row = {"case_id": case_id, "state": "retained"}
                destination = root / "process-captures" / case_id.removeprefix("case:")
                destination.mkdir(parents=True)
                (destination / "capture.json").write_text(
                    canonical_json(row) + "\n", encoding="utf-8"
                )
                return row
            finally:
                with lock:
                    active -= 1

        rows = lean_pipeline._run_stage_model_calls(config, callback, case_ids)
        ledger = (
            canonical_json({"entries": sorted(rows, key=lambda row: row["case_id"])}) + "\n"
        ).encode()
        captures = {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("capture.json"))
        }
        return captures, ledger, maximum

    development = default_dependence_free_config()
    sequential = replace(development, development_loop=False)
    concurrent_artifacts = run(development, tmp_path / "fixture-lane-concurrent")
    sequential_artifacts = run(sequential, tmp_path / "fixture-lane-sequential")
    assert concurrent_artifacts[:2] == sequential_artifacts[:2]
    assert concurrent_artifacts[2] == 3
    assert sequential_artifacts[2] == 1


@pytest.mark.skipif(not _RUNTIME_AVAILABLE, reason="dedicated SciPy 1.14.0 runtime is absent")
def test_malformed_primary_burns_one_case_while_labels_and_detector_continue(
    tmp_path: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated = _isolated_root(tmp_path, project_root)
    roles = ("rq1", "rq4")
    config = replace(
        _fixture_config(roles),
        pipeline_relative=Path("evaluation/development-fixtures/malformed-primary"),
        hostile_answer_key_reviewer=None,
    )
    _freeze_fixture_inputs(isolated, config)
    step_intake(isolated, config)
    step_authority(isolated, config)
    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda _root, _config: {})
    monkeypatch.setattr(
        lean_pipeline, "_run_hostile_answer_key_review", lambda *_args, **_kwargs: None
    )

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
        case_id = case_subset[0]
        standard = {
            "call_identity_id": label,
            "prompt_digest": "sha256:" + "4" * 64,
            "output_schema_digest": "sha256:" + "5" * 64,
            "shared_transcript_digest": "sha256:" + "6" * 64,
            "packet_digests": {case_id: "sha256:" + "2" * 64},
        }
        if case_id == _CASE_BY_ROLE["rq1"]:
            refusal = {
                "case_id": case_id,
                "response_state": "review-response-malformed",
                "failure_class": "invalid-json",
                "refusal_digest": "sha256:" + "7" * 64,
            }
            return {"entries": [], **standard, "review_response_refusals": [refusal]}
        return {
            "entries": [
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": f"review:{case_id}",
                    "review_digest": "sha256:" + "8" * 64,
                    "packet_digest": "sha256:" + "2" * 64,
                    "capture_digest": "sha256:" + "9" * 64,
                    "verdict": selected.expected_verdict("rq4"),
                    "issue_class": None,
                    "unresolved_material_question_count": 0,
                }
            ],
            **standard,
        }

    monkeypatch.setattr(lean_pipeline, "_run_review_call", review_call)
    review = step_review(isolated, config)
    assert review["burned_case_ids"] == [_CASE_BY_ROLE["rq1"]]
    assert review["review_response_refusals"][0]["response_state"] == ("review-response-malformed")
    assert [entry["case_id"] for entry in review["entries"]] == [_CASE_BY_ROLE["rq4"]]
    labels = step_labels(isolated, config)
    labels_by_role = {entry["case_role"]: entry for entry in labels["entries"]}
    assert labels_by_role["rq1"]["measurement_state"] == ("burned_review_response_malformed")
    assert labels_by_role["rq1"]["review_basis"] == (
        "primary_blind_review_response_malformed_retained_without_label"
    )
    detector = step_detector(isolated, config)
    detector_by_role = {entry["case_role"]: entry for entry in detector["entries"]}
    assert detector_by_role["rq1"]["comparison_outcome"] == "burned_before_measurement"
    assert detector_by_role["rq1"]["shadow_payload"] is None
    assert detector_by_role["rq4"]["comparison_outcome"] != "burned_before_measurement"


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
