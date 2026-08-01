import json

import pytest

from sc_referee.controller import run_demo
from sc_referee.core.control import RunControl
from sc_referee.core.errors import CancellationRequestedError
from sc_referee.records.schema_registry import LocalSchemaRegistry


def test_prelock_cancellation_is_durable_and_does_not_invent_bundle(
    project_root, schema_root, tmp_path
) -> None:
    control = RunControl()

    def cancel_after_inventory(state: str, active: RunControl) -> None:
        if state == "inventoried":
            active.request_cancellation()

    output = tmp_path / "cancelled"
    with pytest.raises(CancellationRequestedError):
        run_demo(
            project_root / "examples" / "walking-skeleton",
            output,
            schema_root,
            run_control=control,
            stage_hook=cancel_after_inventory,
        )

    assert _run_states(output)[-1] == "cancelled"
    final_stage = _records(output / "observed" / "stage-result.jsonl")[-1]
    assert final_stage["stage"] == "parsing"
    assert final_stage["status"] == "skipped"
    assert not (output / "audit.bundle.json").exists()


def test_postlock_host_limit_emits_truthful_partial_bundle(
    project_root, schema_root, tmp_path
) -> None:
    control = RunControl()

    def exhaust_after_lock(state: str, active: RunControl) -> None:
        if state == "semantics_locked":
            active.report_host_model_limit()

    output = tmp_path / "host-limit"
    bundle = run_demo(
        project_root / "examples" / "walking-skeleton",
        output,
        schema_root,
        run_control=control,
        stage_hook=exhaust_after_lock,
    )

    LocalSchemaRegistry(schema_root).validate(bundle)
    coverage = bundle["coverage_records"][0]
    assert coverage["overall_status"] == "partial_budget_exhausted"
    assert coverage["extensions"]["x-run-state"] == "partial_host_limit"
    assert coverage["extensions"]["x-termination-reason"] == "host_model_limit"
    assert bundle["findings"] == []
    assert _run_states(output)[-1] == "partial_host_limit"
    detection_stage = _records(output / "observed" / "stage-result.jsonl")[-1]
    assert detection_stage["error"]["code"] == "host_model_limit"
    assert len(bundle["storage_manifests"]) == 1


def test_general_controller_failure_is_durably_propagated(
    project_root, schema_root, tmp_path
) -> None:
    def fail_after_inventory(state: str, active: RunControl) -> None:
        del active
        if state == "inventoried":
            raise RuntimeError("injected controller failure")

    output = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="injected controller failure"):
        run_demo(
            project_root / "examples" / "walking-skeleton",
            output,
            schema_root,
            stage_hook=fail_after_inventory,
        )

    assert _run_states(output)[-1] == "failed_controller"
    final_stage = _records(output / "observed" / "stage-result.jsonl")[-1]
    assert final_stage["stage"] == "controller"
    assert final_stage["status"] == "failed"
    assert final_stage["error"]["code"] == "controller_integrity_failure"
    assert "injected controller failure" not in final_stage["details"]


def test_snapshot_capture_failure_has_public_pre_snapshot_terminal_record(
    project_root, schema_root, tmp_path, monkeypatch
) -> None:
    def fail_capture(*args, **kwargs):
        del args, kwargs
        raise OSError("injected snapshot failure")

    monkeypatch.setattr("sc_referee.controller.capture_repository", fail_capture)
    output = tmp_path / "snapshot-failed"
    with pytest.raises(OSError, match="injected snapshot failure"):
        run_demo(
            project_root / "examples" / "walking-skeleton",
            output,
            schema_root,
        )

    records = _records(output / "observed" / "audit-run.jsonl")
    assert [record["state"] for record in records] == ["created", "failed_controller"]
    assert "snapshot_ref" not in records[-1]
    LocalSchemaRegistry(schema_root).validate(records[-1])


def _run_states(output):
    return [record["state"] for record in _records(output / "observed" / "audit-run.jsonl")]


def _records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
