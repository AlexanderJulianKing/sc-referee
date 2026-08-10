"""Six-role pilot fixtures for the dependence-recognition envelope.

Provider transport is recorded in-process, while every deterministic pipeline
step remains real.  Intake executes only the fixture workflows commissioned in
this file, under the dedicated SciPy 1.14.0 qualification interpreter.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline
from sc_referee_evaluation.lean_pipeline import (
    DEFAULT_ALLOWED_IMPORT_ROOTS,
    _probe_sandbox_runtime,
    step_authoring,
    step_authority,
    step_detector,
    step_intake,
    step_labels,
    step_review,
)

from sc_referee.controller import replay
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    LOCK_KIND,
    approval_projection,
    lock_projection,
    verify_dependence_authorization_lock,
)
from scripts.lean_pipeline import (
    DEPENDENCE_SANDBOX_PYTHON,
    ENVELOPE_CONFIGS,
    default_dependence_config,
)

_ROLES = (
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
)
_CASE_BY_ROLE = {role: f"case:{index:020x}" for index, role in enumerate(_ROLES, start=1)}
_ROLE_BY_CASE = {case_id: role for role, case_id in _CASE_BY_ROLE.items()}
_LEFT = tuple(float(index) for index in range(1, 13))
_RIGHT = (2.0, 4.0, 3.0, 5.0, 7.0, 6.0, 9.0, 8.0, 11.0, 10.0, 13.0, 12.0)
_RESULTS = {
    "error_bearing": (
        "TtestResult(statistic=np.float64(-0.9823619317924353), "
        "pvalue=np.float64(0.33106037814548595), df=np.float64(46.0))"
    ),
    "corrected_twin": (
        "TtestResult(statistic=np.float64(-0.6793662204867575), "
        "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
    ),
    "valid_alternative": (
        "MannwhitneyuResult(statistic=np.float64(60.5), pvalue=np.float64(0.5243792697676437))"
    ),
    "hard_negative": (
        "TtestResult(statistic=np.float64(-0.6793662204867575), "
        "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
    ),
    "ambiguous": (
        "TtestResult(statistic=np.float64(-0.6793662204867575), "
        "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
    ),
    "unsupported": (
        "TtestResult(statistic=np.float64(-3.63318042491699), "
        "pvalue=np.float64(0.00393470596182021), df=np.int64(11))"
    ),
}
_CALLABLE_BY_ROLE = {
    "error_bearing": "scipy.stats.ttest_ind",
    "corrected_twin": "scipy.stats.ttest_ind",
    "valid_alternative": "scipy.stats.mannwhitneyu",
    "hard_negative": "scipy.stats.ttest_ind",
    "ambiguous": "scipy.stats.ttest_ind",
    "unsupported": "scipy.stats.ttest_rel",
}
_PROCEDURE_ATTRIBUTE_BY_ROLE = {
    role: value.rsplit(".", maxsplit=1)[-1] for role, value in _CALLABLE_BY_ROLE.items()
}


def _unique_rows(*, shared_tag: bool = False) -> list[tuple[str, str, str, float, float]]:
    return [
        (
            f"u{index:02d}",
            f"v{index:02d}",
            "shared" if shared_tag else f"t{index:02d}",
            _LEFT[index - 1],
            _RIGHT[index - 1],
        )
        for index in range(1, 13)
    ]


def _rows(role: str) -> list[tuple[str, str, str, float, float]]:
    if role == "error_bearing":
        return [row for row in _unique_rows() for _copy in range(2)]
    if role == "hard_negative":
        return _unique_rows(shared_tag=True)
    if role == "ambiguous":
        keys = (
            ("u01", "v01"),
            ("u01", "v02"),
            ("u02", "v03"),
            ("u02", "v04"),
            ("u03", "v01"),
            ("u03", "v03"),
            ("u04", "v02"),
            ("u04", "v04"),
            ("u05", "v01"),
            ("u05", "v04"),
            ("u06", "v02"),
            ("u06", "v03"),
        )
        return [
            (k1, k2, f"g{1 + (index % 2):02d}", _LEFT[index], _RIGHT[index])
            for index, (k1, k2) in enumerate(keys)
        ]
    return _unique_rows()


def _csv(role: str) -> str:
    lines = ["k1,k2,tag,a,b"]
    lines.extend(f"{k1},{k2},{tag},{a:.1f},{b:.1f}" for k1, k2, tag, a, b in _rows(role))
    return "\n".join(lines) + "\n"


def _workflow(role: str) -> str:
    procedure = _PROCEDURE_ATTRIBUTE_BY_ROLE[role]
    return (
        "import csv\n"
        "from pathlib import Path\n"
        "import scipy.stats as st\n"
        'rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", '
        'encoding="utf-8")))\n'
        'left = [float(row["a"]) for row in rows]\n'
        'right = [float(row["b"]) for row in rows]\n'
        f"result = st.{procedure}(left, right)\n"
        'Path("results/report.md").write_text(f"[selected-result] {result}\\n", '
        'encoding="utf-8")\n'
    )


def _authored_case(role: str) -> dict[str, Any]:
    return {
        "case_id": _CASE_BY_ROLE[role],
        "input_csv": _csv(role),
        "analysis_py": _workflow(role),
        "report_md": f"[selected-result] {_RESULTS[role]}\n",
        "selected_result_line": 1,
    }


def _authority_lock(
    case_id: str,
    role: str,
    input_digest: str,
    *,
    snapshot_digest: str,
    intake_recorded_at: str,
) -> dict[str, Any]:
    slug = case_id.removeprefix("case:")
    analysis_id = f"analysis:{slug}"
    procedure_id = f"procedure:{slug}"
    result_id = f"result:{slug}"
    authorization_id = f"authorization:{slug}"
    actor_id = "scientist:dependence-a-method-owner-01"
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
        "snapshot_digest": snapshot_digest,
        "intake_recorded_at": intake_recorded_at,
        "records": [
            {
                "record_type": "analysis",
                "record_id": analysis_id,
                "path": "workflow/analysis.py",
            },
            {
                "record_type": "procedure",
                "record_id": procedure_id,
                "resolved_callable": _CALLABLE_BY_ROLE[role],
            },
            {
                "record_type": "result",
                "record_id": result_id,
                "path": "results/report.md",
            },
            {
                "record_type": "human_method_authorization",
                "record_id": authorization_id,
                "actor_id": actor_id,
                "authority_state": "authorized",
                "analysis_target_ref": {
                    "record_type": "analysis",
                    "record_id": analysis_id,
                },
                "procedure_ref": {
                    "record_type": "procedure",
                    "record_id": procedure_id,
                },
                "independent_unit_definition_id": "unit-definition:ordered-k1-k2-source",
                "authorized_key_columns": ["k1", "k2"],
                "input_path": "inputs/data.csv",
                "input_content_digest": input_digest,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": actor_id,
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": intake_recorded_at,
        },
        "authority_limitations": list(AUTHORITY_LIMITATIONS),
        "lock_digest": "sha256:" + "0" * 64,
    }
    value["approval"]["approved_projection_digest"] = semantic_digest(approval_projection(value))
    value["lock_digest"] = semantic_digest(lock_projection(value))
    return value


def _isolated_project_root(tmp_path: Path, project_root: Path) -> Path:
    (tmp_path / "src").symlink_to(project_root / "src")
    (tmp_path / "reference").symlink_to(project_root / "reference")
    return tmp_path


def test_dependence_envelope_configuration_and_actor_seats() -> None:
    config = default_dependence_config()
    assert ENVELOPE_CONFIGS["dependence"] is default_dependence_config
    assert config.canonical_issue_class == (
        "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
    )
    assert config.common_task == (
        "Choose a neutral scientific subject area and instantiate the assigned small table. "
        "Treat `k1`, `k2`, and `tag` as opaque codes and `a` and `b` as two finite numeric "
        "measurements. Apply the procedure named in the case instructions to the complete "
        "staged row sequence and write its single selected result."
    )
    assert config.roles == sorted(_ROLES)
    assert set(config.candidate_by_role) == set(_ROLES) - {"ambiguous"}
    assert set(config.candidate_by_role.values()) == {
        "one-analyzed-row-per-authorized-independent-unit"
    }
    assert config.mq_tolerant_roles == {"ambiguous"}
    assert config.contract_free_roles == {"ambiguous"}
    assert config.allowed_import_roots == DEFAULT_ALLOWED_IMPORT_ROOTS | {"scipy"}
    assert config.sandbox_python == DEPENDENCE_SANDBOX_PYTHON
    assert config.required_sandbox_distributions == {"scipy": "1.14.0"}
    assert config.controller_material_files == {"requirements.txt": b"scipy==1.14.0\n"}
    assert config.material_input_paths == ("inputs/data.csv", "requirements.txt")
    assert config.input_csv_row_bounds == (1, 64)
    assert config.detector_id == "detector:bounded-analysis-method-conflict"
    assert sorted(config.authors) == [
        "actor:dependence-a-author-opus-13",
        "actor:dependence-a-author-opus-14",
    ]
    assert config.author_roles["actor:dependence-a-author-opus-13"] == [
        "error_bearing",
        "corrected_twin",
    ]
    assert config.author_roles["actor:dependence-a-author-opus-14"] == [
        "valid_alternative",
        "hard_negative",
        "ambiguous",
        "unsupported",
    ]
    assert config.reviewer.participant_id == "actor:dependence-a-reviewer-fable-10"
    assert config.escalation_reviewer.participant_id == ("actor:dependence-a-reviewer-opus-07")
    assert "scipy.stats.ttest_ind" in config.author_case_requirements
    assert "scipy.stats.mannwhitneyu" in config.author_case_requirements
    assert "scipy.stats.ttest_rel" in config.author_case_requirements
    for role, result in _RESULTS.items():
        assert result in "\n".join(config.role_constraints[role])


@pytest.mark.skipif(
    not DEPENDENCE_SANDBOX_PYTHON.is_file(),
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_dependence_dedicated_runtime_probe_passes_for_real() -> None:
    record = _probe_sandbox_runtime(DEPENDENCE_SANDBOX_PYTHON, {"scipy": "1.14.0"})
    assert record["interpreter_path"] == DEPENDENCE_SANDBOX_PYTHON.as_posix()
    assert record["python_version"].startswith("3.11.15 ")
    assert record["required_distributions"] == {"scipy": "1.14.0"}
    assert record["observed_distributions"]["scipy"]["distribution_version"] == "1.14.0"
    assert record["observed_distributions"]["scipy"]["module_version"] == "1.14.0"
    assert record["probe_digest"] == semantic_digest(
        {key: value for key, value in record.items() if key != "probe_digest"}
    )


@pytest.mark.skipif(
    not DEPENDENCE_SANDBOX_PYTHON.is_file(),
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_dependence_six_role_fixture_runs_real_pipeline_without_findings(
    tmp_path: Path,
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    isolated_root = _isolated_project_root(tmp_path, project_root)
    base = default_dependence_config()
    config = replace(
        base,
        pipeline_relative=Path("evaluation/qualification/dependence-stage3-six-role-fixture"),
        sealed_case_assignments={case_id: role for role, case_id in sorted(_CASE_BY_ROLE.items())},
    )
    monkeypatch.setattr(lean_pipeline, "ensure_calibrations", lambda _root, _config: {})

    def _recorded_author_transport(
        selected: Any,
        participant: Any,
        _prompt: str,
        _session_id: str,
        capture_root: Path,
    ) -> dict[str, Any]:
        roles = selected.author_roles[participant.participant_id]
        payload = {
            "participant_id": participant.participant_id,
            "cases": [_authored_case(role) for role in roles],
        }
        capture_root.mkdir(parents=True, exist_ok=True)
        return {
            "raw_response": canonical_json(payload),
            "transport_error": None,
            "process_record": {"capture_digest": semantic_digest(payload)},
            "started_at": "2026-08-10T12:01:00Z",
            "completed_at": "2026-08-10T12:01:01Z",
        }

    monkeypatch.setattr(lean_pipeline, "_call_cli", _recorded_author_transport)
    protocol = step_authoring(isolated_root, config)
    assert protocol["case_role_assignments"] == {
        case_id: _ROLE_BY_CASE[case_id] for case_id in sorted(_ROLE_BY_CASE)
    }

    intake = step_intake(isolated_root, config)
    assert intake["case_count"] == 6
    assert intake["ground_truth_execution"]["executed"] is True
    assert intake["ground_truth_execution"]["runs_per_case"] == 2
    assert intake["sandbox_runtime_probe"]["required_distributions"] == {"scipy": "1.14.0"}
    intake_by_case = {str(row["case_id"]): row for row in intake["entries"]}

    incoming_root = isolated_root / config.pipeline_relative / "authority/incoming"
    incoming_root.mkdir(parents=True)
    for case_id, role in sorted(_ROLE_BY_CASE.items()):
        if role == "ambiguous":
            continue
        input_digest = str(intake_by_case[case_id]["file_digests"]["inputs/data.csv"])
        lock = _authority_lock(
            case_id,
            role,
            input_digest,
            snapshot_digest=str(intake_by_case[case_id]["expected_audit_snapshot_digest"]),
            intake_recorded_at=str(intake["recorded_at"]),
        )
        lock_path = incoming_root / f"{case_id.removeprefix('case:')}.json"
        lock_path.write_text(canonical_json(lock) + "\n", encoding="utf-8")
        verified = verify_dependence_authorization_lock(
            lock_path,
            expected_case_id=case_id,
            expected_snapshot_digest=str(intake_by_case[case_id]["expected_audit_snapshot_digest"]),
            expected_intake_recorded_at=str(intake["recorded_at"]),
            source_paths=("workflow/analysis.py",),
            selected_report_path="results/report.md",
            material_input_digests={
                "inputs/data.csv": input_digest,
                "requirements.txt": str(
                    intake_by_case[case_id]["controller_material_file_digests"]["requirements.txt"]
                ),
            },
            forbidden_role_markers=config.roles,
        )
        assert verified.lock_digest == lock["lock_digest"]

    authority = step_authority(isolated_root, config)
    assert authority["frozen_before_review"] is True
    assert authority["authorized_count"] == 5
    assert authority["withheld_count"] == 1
    assert all("case_role" not in entry for entry in authority["entries"])
    assert {
        Path(str(entry["frozen_lock_relative"])).stem
        for entry in authority["entries"]
        if entry["frozen_lock_relative"] is not None
    } == {
        case_id.removeprefix("case:")
        for case_id, role in _ROLE_BY_CASE.items()
        if role != "ambiguous"
    }

    review_observed_frozen_authority: list[bool] = []

    def _recorded_review_transport(
        _project_root: Path,
        selected: Any,
        _review_root: Path,
        participant: Any,
        case_subset: list[str],
        _preparations_by_case: dict[str, dict[str, Any]],
        workspace_payloads: dict[str, dict[str, bytes]],
        _tuple_digest: str,
        label: str,
    ) -> dict[str, Any]:
        review_observed_frozen_authority.append(
            (isolated_root / config.pipeline_relative / "authority/AUTHORITY_LEDGER.json").is_file()
        )
        assert label == "primary"
        assert all(
            set(payloads)
            == {"task.md", "inputs/data.csv", "workflow/analysis.py", "results/report.md"}
            for payloads in workspace_payloads.values()
        )
        entries = []
        for index, case_id in enumerate(case_subset, start=1):
            role = _ROLE_BY_CASE[case_id]
            verdict = selected.expected_verdict(role)
            entries.append(
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": f"review:{index:020x}",
                    "review_digest": "sha256:" + f"{index:064x}",
                    "packet_digest": "sha256:" + f"{index + 10:064x}",
                    "capture_digest": "sha256:" + f"{index + 20:064x}",
                    "verdict": verdict,
                    "issue_class": (
                        selected.canonical_issue_class if verdict == "demonstrated_issue" else None
                    ),
                    "unresolved_material_question_count": 0,
                }
            )
        return {
            "entries": entries,
            "call_identity_id": f"call:{label}",
            "prompt_digest": "sha256:" + "1" * 64,
            "output_schema_digest": "sha256:" + "2" * 64,
            "shared_transcript_digest": "sha256:" + "3" * 64,
            "packet_digests": {
                case_id: "sha256:" + f"{index + 10:064x}"
                for index, case_id in enumerate(case_subset, start=1)
            },
        }

    monkeypatch.setattr(lean_pipeline, "_run_review_call", _recorded_review_transport)
    review = step_review(isolated_root, config)
    assert review_observed_frozen_authority == [True]
    assert review["authority_ledger_digest"] == authority["ledger_digest"]
    assert review["unresolved_case_ids"] == []
    labels = step_labels(isolated_root, config)
    assert labels["label_count"] == 6

    detector = step_detector(isolated_root, config)
    rows_by_role = {str(row["case_role"]): row for row in detector["entries"]}
    assert rows_by_role["error_bearing"]["comparison_outcome"] == "true_positive"
    assert rows_by_role["error_bearing"]["finding_candidate_count"] == 1
    for role in set(_ROLES) - {"error_bearing"}:
        assert rows_by_role[role]["comparison_outcome"] == "true_negative"
        assert rows_by_role[role]["finding_candidate_count"] == 0
    assert detector["pilot_metrics"] == {
        "opportunity_count": 6,
        "true_positive_count": 1,
        "true_negative_count": 5,
        "false_accusation_count": 0,
        "missed_error_count": 0,
        "sensitivity": 1.0,
        "false_accusation_rate": 0.0,
    }
    assert detector["production_finding_count"] == 0
    assert all(row["production_findings"] == 0 for row in detector["entries"])
    assert all(row["replay_equal"] is True for row in detector["entries"])

    replayed_by_role: dict[str, dict[str, Any]] = {}
    semantic_locks_by_role: dict[str, dict[str, Any]] = {}
    for role, case_id in _CASE_BY_ROLE.items():
        slug = case_id.removeprefix("case:")
        lock_path = (
            isolated_root
            / config.pipeline_relative
            / "detector-run/runs"
            / slug
            / "audit/semantic.lock.json"
        )
        semantic_locks_by_role[role] = json.loads(lock_path.read_bytes())
        replayed_by_role[role] = replay(
            lock_path,
            isolated_root / "fixture-replay" / slug,
            isolated_root / "reference/schemas-v0.18.0",
        )

    detector_id = config.detector_id
    states_by_role = {
        role: [
            str(result["state"])
            for result in bundle["detector_results"]
            if result.get("detector_id") == detector_id
        ]
        for role, bundle in replayed_by_role.items()
    }
    assert states_by_role["error_bearing"] == ["evaluation_finding_candidate"]
    for role in ("corrected_twin", "valid_alternative", "hard_negative"):
        assert states_by_role[role] == ["no_issue_detected_within_coverage"]
    assert states_by_role["ambiguous"] == []
    assert states_by_role["unsupported"] == []
    ambiguous_module = next(
        item
        for item in semantic_locks_by_role["ambiguous"]["scientific_check_registry"]["evaluation"][
            "modules"
        ]
        if item["check_id"] == config.check_id
    )
    assert ambiguous_module["state"] == "ambiguous"
    assert [item["abstention_reason"] for item in ambiguous_module["observations"]] == [
        "independent-unit-definition-unresolved"
    ]
    assert any(
        disclosure.get("extensions", {}).get("x-scientific-check-id") == config.check_id
        and disclosure["extensions"]["x-scientific-check-state"] == "ambiguous"
        for disclosure in replayed_by_role["ambiguous"]["disclosures"]
    )
    assert not [
        assertion
        for assertion in replayed_by_role["unsupported"]["semantic_assertions"]
        if assertion.get("extensions", {}).get("x-scientific-check-id") == config.check_id
    ]
    assert all(not bundle["findings"] for bundle in replayed_by_role.values())

    # The runtime and authored bytes are both bound into intake, while production
    # audit remains non-executing and replay-stable.
    for role, case_id in _CASE_BY_ROLE.items():
        intake_row = intake_by_case[case_id]
        assert intake_row["sandbox_report_digest"] == sha256_digest(
            f"[selected-result] {_RESULTS[role]}\n"
        )
        assert intake_row["sandbox_runs"] == 2
        assert rows_by_role[role]["project_code_executions"] == 0
