import json
from pathlib import Path

from sc_referee.controller import run_demo
from sc_referee.core.deadline import AuditDeadline, AuditMode
from sc_referee.records.schema_registry import LocalSchemaRegistry


class Clock:
    value = 0.0

    def __call__(self) -> float:
        return self.value


class ScriptedClock:
    def __init__(self, values: list[float]) -> None:
        self._values = iter(values)
        self._last = values[-1]

    def __call__(self) -> float:
        self._last = next(self._values, self._last)
        return self._last


def test_scientist_wait_pauses_deadline() -> None:
    clock = Clock()
    deadline = AuditDeadline(10.0, now=clock)
    clock.value = 3.0
    deadline.pause_for_scientist()
    clock.value = 103.0
    deadline.resume_after_scientist()
    clock.value = 108.0
    assert deadline.elapsed == 8.0
    assert deadline.remaining == 2.0


def test_scheduling_cutoff_closes_only_optional_work() -> None:
    clock = Clock()
    deadline = AuditDeadline(10.0, now=clock, scheduling_cutoff_seconds=4.0)
    clock.value = 4.0
    assert deadline.scheduling_cutoff_reached
    assert not deadline.optional_scheduling_open
    assert not deadline.expired


def test_mode_deadline_defaults_match_normative_trial_pairs() -> None:
    assert _deadline_pair("quick") == (120.0, 300.0)
    assert _deadline_pair("standard") == (480.0, 600.0)
    assert _deadline_pair("publication") == (1500.0, 1800.0)


def test_forced_deadline_writes_partial_bundle_and_explicit_coverage(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    clock = ScriptedClock([0.0, 0.0, 0.0, 0.0, 11.0])
    deadline = AuditDeadline(10.0, now=clock, scheduling_cutoff_seconds=8.0)
    output = tmp_path / "partial"

    bundle = run_demo(
        project_root / "examples" / "walking-skeleton",
        output,
        schema_root,
        deadline=deadline,
    )

    LocalSchemaRegistry(schema_root).validate(bundle)
    assert bundle["findings"] == []
    assert bundle["detector_results"] == []
    assert len(bundle["material_questions"]) == 1
    assert len(bundle["disclosures"]) == 1
    coverage = bundle["coverage_records"][0]
    assert coverage["overall_status"] == "partial_budget_exhausted"
    assert coverage["extensions"]["x-run-state"] == "partial_deadline"
    assert coverage["extensions"]["x-termination-reason"] == "hard_deadline"
    assert coverage["extensions"]["x-pending-work"] == [
        "detector:claim-result-direction on claim:walking-skeleton-direction",
        "detector:sample-unit-dependence on operation:compute-difference",
    ]
    assert all(item["targets_evaluated"] == 0 for item in coverage["detector_coverage"])

    run_states = [
        record["state"] for record in _read_jsonl(output / "observed" / "audit-run.jsonl")
    ]
    assert run_states == [
        "created",
        "snapshotted",
        "inventoried",
        "parsed",
        "semantics_locked",
        "partial_deadline",
    ]
    stage_results = _read_jsonl(output / "observed" / "stage-result.jsonl")
    assert stage_results[-1]["stage"] == "detection"
    assert stage_results[-1]["status"] == "timed_out"
    assert stage_results[-1]["error"]["code"] == "deadline_exhausted"
    _validate_public_records(schema_root, "audit-run", output)
    _validate_public_records(schema_root, "stage-result", output)

    html = (output / "report.html").read_text(encoding="utf-8")
    assert "Partial audit" in html
    assert "2 detector targets remain unevaluated" in html
    assert (
        "No claims needing correction were identified among completed detector evaluations" in html
    )
    assert (output / "semantic.lock.json").is_file()
    assert (output / "audit.db").is_file()


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _deadline_pair(mode: AuditMode) -> tuple[float, float]:
    deadline = AuditDeadline.for_mode(mode)
    cutoff = deadline.scheduling_cutoff_seconds
    assert cutoff is not None
    return cutoff, deadline.hard_seconds


def _validate_public_records(schema_root: Path, record_name: str, output: Path) -> None:
    registry = LocalSchemaRegistry(schema_root)
    for record in _read_jsonl(output / "observed" / f"{record_name}.jsonl"):
        registry.validate(record)
