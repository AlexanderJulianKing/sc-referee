from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.candidate import (
    EvaluationCandidateProjectionError,
    project_evaluation_candidate,
)
from sc_referee_evaluation.cli import main as evaluation_main

from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.admission import AdmissionContext, admit_finding


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.18.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _inputs(project_root: Path) -> dict[str, Any]:
    result = _example(project_root, "detector-result.evaluation-candidate.example.json")
    fixture = _example(project_root, "benchmark-fixture.example.json")
    fixture["declared_scope"]["detector_ids"] = [result["detector_id"]]
    bundle = _example(project_root, "audit-bundle.example.json")
    bundle["detector_results"] = [deepcopy(result)]
    finding_draft = _example(project_root, "finding.example.json")
    finding_draft.pop("admission")
    finding_draft["detector_result_ids"] = [result["result_id"]]
    finding_draft["evidence"] = deepcopy(result["evidence"])
    label_freeze: dict[str, Any] = {
        "evaluation_protocol_version": "0.1.0",
        "record_type": "evaluation_scientific_label_freeze",
        "case_id": "case:evaluation-projection",
        "stage1_freeze_digest": "sha256:" + "1" * 64,
        "stage2_reviews": [],
        "adjudication_ref": deepcopy(fixture["adjudication_ref"]),
        "adjudication_digest": "sha256:" + "2" * 64,
        "adjudicated_root_causes": [],
        "label_status": "positive_demonstrated",
        "frozen_at": "2026-07-28T19:00:00Z",
        "detector_output_observed": False,
    }
    label_freeze["freeze_digest"] = semantic_digest(label_freeze)
    context = AdmissionContext(
        finding_draft=finding_draft,
        source_references_resolved=True,
        detector_qualification_applies=False,
        wording_constraints_satisfied=True,
        expected_deterministic_input_digest=result["deterministic_input_digest"],
        required_counterevidence_check_ids=(
            "check:orientation",
            "check:report-qualification",
        ),
        non_inferences=("No global workflow correctness claim is established.",),
    )
    return {
        "result": result,
        "fixture": fixture,
        "bundle": bundle,
        "label_freeze": label_freeze,
        "context": context,
    }


def _project(
    inputs: dict[str, Any], schema_root: Path, output: Path | None = None
) -> dict[str, Any]:
    return project_evaluation_candidate(
        inputs["result"],
        inputs["context"],
        inputs["fixture"],
        inputs["label_freeze"],
        inputs["bundle"],
        schema_root,
        candidate_created_at="2026-07-28T20:00:00Z",
        output=output,
    )


def test_experimental_result_projects_stable_nonproduction_candidate(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root)

    candidate = _project(inputs, schema_root, tmp_path / "candidate.json")
    replayed = project_evaluation_candidate(
        inputs["result"],
        inputs["context"],
        inputs["fixture"],
        inputs["label_freeze"],
        inputs["bundle"],
        schema_root,
        candidate_created_at="2026-07-28T20:00:00Z",
        expected_candidate=candidate,
    )

    assert replayed == candidate
    assert candidate["maturity_gate_bypassed_for_evaluation"] is True
    assert candidate["production_admission_permitted"] is False
    assert candidate["production_finding_ref"] is None
    assert candidate["source_detector_result_digest"] == semantic_digest(inputs["result"])


def test_production_admission_always_rejects_evaluation_state(
    project_root: Path,
) -> None:
    inputs = _inputs(project_root)
    context = inputs["context"]
    production_context = AdmissionContext(
        **{**context.__dict__, "detector_qualification_applies": True}
    )

    assert admit_finding(inputs["result"], production_context) is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda result: result["applicability"].update(status="uncertain"),
        lambda result: result["coverage"].update(status="not_covered"),
        lambda result: result["candidate"]["material_premise_ids"].clear(),
        lambda result: result["candidate"]["unresolved_material_premise_ids"].append(
            "premise:unknown"
        ),
        lambda result: result["counterevidence_execution"][0].update(
            outcome="counterevidence_found"
        ),
        lambda result: result.update(deterministic_input_digest="sha256:" + "0" * 64),
    ],
)
def test_projection_fails_closed_for_shared_non_maturity_gate(
    project_root: Path, schema_root: Path, mutation: Any
) -> None:
    inputs = _inputs(project_root)
    mutation(inputs["result"])
    inputs["bundle"]["detector_results"] = [deepcopy(inputs["result"])]

    with pytest.raises(EvaluationCandidateProjectionError):
        _project(inputs, schema_root)


def test_projection_rejects_source_bundle_digest_drift(
    project_root: Path, schema_root: Path
) -> None:
    inputs = _inputs(project_root)
    inputs["bundle"]["detector_results"][0]["evidence"][0]["description"] = "drifted"

    with pytest.raises(EvaluationCandidateProjectionError, match="exact source"):
        _project(inputs, schema_root)


def test_candidate_cli_projects_and_replays_without_a_new_timestamp(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root)
    paths = {}
    for name in ("result", "fixture", "bundle", "label_freeze"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(inputs[name]), encoding="utf-8")
        paths[name] = path
    context = inputs["context"]
    draft_path = tmp_path / "finding-draft.json"
    draft_path.write_text(json.dumps(dict(context.finding_draft)), encoding="utf-8")
    context_path = tmp_path / "admission-context.json"
    context_path.write_text(
        json.dumps(
            {
                "source_references_resolved": context.source_references_resolved,
                "wording_constraints_satisfied": context.wording_constraints_satisfied,
                "expected_deterministic_input_digest": context.expected_deterministic_input_digest,
                "required_counterevidence_check_ids": list(
                    context.required_counterevidence_check_ids
                ),
                "non_inferences": list(context.non_inferences),
            }
        ),
        encoding="utf-8",
    )
    shared = [
        "--detector-result",
        str(paths["result"]),
        "--finding-draft",
        str(draft_path),
        "--admission-context",
        str(context_path),
        "--fixture",
        str(paths["fixture"]),
        "--label-freeze",
        str(paths["label_freeze"]),
        "--audit-bundle",
        str(paths["bundle"]),
        "--schema-root",
        str(schema_root),
    ]
    candidate_path = tmp_path / "candidate.json"
    assert (
        evaluation_main(
            [
                "project-candidate",
                *shared,
                "--created-at",
                "2026-07-28T20:00:00Z",
                "--output",
                str(candidate_path),
            ]
        )
        == 0
    )
    replay_path = tmp_path / "candidate-replay.json"
    assert (
        evaluation_main(
            [
                "replay-candidate",
                *shared,
                "--source-candidate",
                str(candidate_path),
                "--output",
                str(replay_path),
            ]
        )
        == 0
    )
    assert replay_path.read_bytes() == candidate_path.read_bytes()
