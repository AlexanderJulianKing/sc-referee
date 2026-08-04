from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from sc_referee_evaluation.selected_result_qualification_runner import (
    _fresh_replay_case_projection,
    _pilot_diversity,
    _run_target_worker_in_oci,
    _safe_pack_path,
    _validated_assignments,
    _validated_pilot_decision,
)

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest


def _assignments_path(project_root: Path) -> Path:
    return (
        project_root
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.1.0-study"
        / "opaque-assignments.json"
    )


def test_assignment_self_digest_is_replayed_before_execution(
    project_root: Path, tmp_path: Path
) -> None:
    original = json.loads(_assignments_path(project_root).read_text(encoding="utf-8"))
    mutated = dict(original)
    mutated["case_count"] = 95
    path = tmp_path / "assignments.json"
    path.write_text(json.dumps(mutated), encoding="utf-8")

    with pytest.raises(ValueError, match="self-digest"):
        _validated_assignments(path)


@pytest.mark.parametrize("raw", ["/absolute/file.json", "../escape.json", "a/../../escape"])
def test_phase_paths_cannot_escape_their_root(tmp_path: Path, raw: str) -> None:
    with pytest.raises(ValueError, match="escapes"):
        _safe_pack_path(tmp_path, raw, "test path")


def test_phase_paths_cannot_traverse_symlinks(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(ValueError, match="symbolic link"):
        _safe_pack_path(tmp_path, "link/record.json", "test path")


def test_held_out_gate_rejects_evidence_free_passing_pilot_decision(
    project_root: Path, tmp_path: Path
) -> None:
    assignments = _validated_assignments(_assignments_path(project_root))
    runner_digest = "sha256:" + "b" * 64
    decision: dict[str, object] = {
        "artifact_kind": "selected_result_verifier_pilot_qualification_decision",
        "decision": "pass",
        "held_out_open_authorized": True,
        "assignment_digest": assignments["assignment_digest"],
        "runner_freeze_digest": runner_digest,
        "pilot_case_count": 48,
        "exact_match_count": 48,
        "failure_count": 0,
        "qualification_authority": "none_pilot_decision_only",
    }
    decision["pilot_decision_digest"] = semantic_digest(decision)
    path = tmp_path / "pilot-decision.json"
    path.write_text(json.dumps(decision), encoding="utf-8")

    with pytest.raises(ValueError, match="evidence-backed"):
        _validated_pilot_decision(
            path,
            assignments=assignments,
            runner_freeze={},
            runner_freeze_digest=runner_digest,
            provider_run_roots=[],
        )


def test_phase_paths_reject_a_symlinked_root(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    (actual / "record.json").write_text("{}", encoding="utf-8")
    link = tmp_path / "root-link"
    try:
        os.symlink(actual, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(ValueError, match="root must be a real non-symlink"):
        _safe_pack_path(link, "record.json", "test path")


def test_runner_parser_has_four_separate_phases() -> None:
    from sc_referee_evaluation.selected_result_qualification_runner import _parser

    parser = _parser()
    phase_action = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._StoreAction) and action.dest == "phase"
    )
    assert tuple(phase_action.choices) == (
        "freeze-oracles",
        "run-targets",
        "run-validations",
        "compare",
    )
    pack_action = next(action for action in parser._actions if action.dest == "pack_root")
    assert pack_action.required is False


def test_target_phase_cli_rejects_provider_pack_exposure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sc_referee_evaluation import selected_result_qualification_runner as runner

    monkeypatch.setattr(
        runner,
        "_validated_assignments",
        lambda _path: {"case_count": 96, "assignment_digest": "sha256:" + "b" * 64},
    )
    monkeypatch.setattr(
        runner,
        "_validated_runner_freeze",
        lambda *_args, **_kwargs: {"runner_freeze_digest": "sha256:" + "a" * 64},
    )
    monkeypatch.setattr(runner, "_validated_frozen_identity_registry", lambda _freeze: {})
    monkeypatch.setattr(
        runner,
        "_validated_launch_receipt",
        lambda *_args, **_kwargs: {"issued_at": "2026-08-04T23:00:00Z"},
    )
    argv = [
        "run-targets",
        "--assignments",
        str(tmp_path / "assignments.json"),
        "--runner-freeze",
        str(tmp_path / "freeze.json"),
        "--phase-launch-receipt",
        str(tmp_path / "phase-receipt.json"),
        "--pack-root",
        str(tmp_path / "provider-pack"),
        "--block",
        "pilot",
        "--provider-slot",
        "provider-a",
        "--output",
        str(tmp_path / "output"),
        "--oracle-phase",
        str(tmp_path / "oracle"),
    ]

    with pytest.raises(ValueError, match="forbids --pack-root"):
        runner.main(argv)


def test_pilot_diversity_is_global_across_both_provider_bundles() -> None:
    states = ["V"] * 12 + ["A"] * 8 + ["I"] * 8 + ["U"] * 20
    u_cells = (
        "dynamic_or_opaque_structure",
        "role_or_source_artifact_boundary",
        "encoding_newline_or_runtime_boundary",
        "syntax_value_or_finite_budget_boundary",
        "mode_or_role_boundary",
    )
    seen: dict[str, int] = {state: 0 for state in ("V", "A", "I", "U")}
    cases: list[dict[str, object]] = []
    for index, state in enumerate(states):
        state_index = seen[state]
        seen[state] += 1
        cases.append(
            {
                "expected_state": state,
                "u_cell": u_cells[state_index % 5] if state == "U" else None,
                "construction_family": f"family-{index % 2}",
                "construction_cluster": f"{state}-cluster-{state_index % 4}",
            }
        )

    _, _, cluster_counts, passed = _pilot_diversity(cases)
    assert passed is True
    assert cluster_counts == {"V": 4, "A": 4, "I": 4, "U": 4}

    collapsed = [dict(item) for item in cases]
    for item in collapsed:
        if item["expected_state"] == "A":
            item["construction_cluster"] = "one-shared-A-cluster"
    assert _pilot_diversity(collapsed)[3] is False

    concentrated = [dict(item, construction_family="one-family") for item in cases]
    assert _pilot_diversity(concentrated)[3] is False


def test_fresh_replay_projection_ignores_only_runtime_identity_fields() -> None:
    review = {
        "case_inventory": [{"path": "analysis.py", "content_digest": "sha256:" + "a" * 64}],
        "semantic_conclusion": {
            "expected_state": "I",
            "reason_codes": ["selected_report_missing"],
            "positive_binding_digest": None,
        },
        "binding_evidence": None,
        "rule_trace": [{"rule_id": "selected_report_missing", "outcome": "matched"}],
        "independence_declaration": {"target_output_seen": False},
        "validator_identity": {"actor_id": "runtime-specific"},
        "completed_at": "2026-08-04T23:00:00Z",
    }
    reconciliation = {
        "blind_review": review,
        "certificate_conclusion": review["semantic_conclusion"],
        "agrees_with_construction_certificate": True,
    }
    oracle = {
        "semantic_reconciliations": [reconciliation, reconciliation],
        "oracle_result": {
            "case_id": "case:" + "1" * 20,
            "expected_state": "I",
            "reason_codes": ["selected_report_missing"],
        },
    }
    target_derivation = {
        "profile_id": "profile",
        "profile_digest": "sha256:" + "2" * 64,
        "case_id": "case:" + "1" * 20,
        "selected_report_path": "report.txt",
        "candidate_bindings": [],
        "candidate_binding_digests": [],
        "derivation_status": "insufficient_evidence",
        "reason_codes": ["selected_report_missing"],
        "retained_files": [],
        "case_tree_digest": "sha256:" + "3" * 64,
        "locator_receipts": [],
        "implementation_lock": {"content_digest": "sha256:" + "4" * 64},
        "project_code_executed": False,
        "validator_identity": {"actor_id": "runtime-specific"},
        "derived_at": "2026-08-04T23:01:00Z",
    }
    target = {"target_derivation": target_derivation}
    validation = {
        "case_contract": {"case_id": "case:" + "1" * 20},
        "target_validation": {
            "case_contract_digest": "sha256:" + "5" * 64,
            "status": "insufficient_evidence",
            "selected_result_binding_digest": None,
            "case_tree_digest": "sha256:" + "3" * 64,
            "reason_codes": ["selected_report_missing"],
            "qualification_authority": "none_selected_result_validation_only",
            "execution_context_id": "runtime-specific",
            "completed_at": "2026-08-04T23:02:00Z",
        },
    }
    comparison = {
        "case_id": "case:" + "1" * 20,
        "assignment_binding": {"assignment_position": 1},
        "expected_state": "I",
        "observed_state": "I",
        "expected_reason_codes": ["selected_report_missing"],
        "observed_reason_codes": ["selected_report_missing"],
        "expected_validation_status": "insufficient_evidence",
        "observed_validation_status": "insufficient_evidence",
        "expected_validation_reason_codes": ["selected_report_missing"],
        "observed_validation_reason_codes": ["selected_report_missing"],
        "state_matches": True,
        "reason_codes_match": True,
        "validation_matches": True,
        "binding_matches": True,
        "comparison_outcome": "exact_match",
        "comparison_identity": {"actor_id": "runtime-specific"},
        "compared_at": "2026-08-04T23:03:00Z",
    }

    first = _fresh_replay_case_projection(
        oracle_proof=oracle,
        target_record=target,
        validation_record=validation,
        comparison_record=comparison,
    )
    review["validator_identity"] = {"actor_id": "different-runtime"}
    target_derivation["validator_identity"] = {"actor_id": "different-runtime"}
    second = _fresh_replay_case_projection(
        oracle_proof=oracle,
        target_record=target,
        validation_record=validation,
        comparison_record=comparison,
    )
    assert first == second

    target_derivation["reason_codes"] = ["selected_report_empty"]
    drifted = _fresh_replay_case_projection(
        oracle_proof=oracle,
        target_record=target,
        validation_record=validation,
        comparison_record=comparison,
    )
    assert drifted["projection_digest"] != first["projection_digest"]


def test_target_worker_oci_launch_mounts_no_oracle_or_provider_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = tmp_path / "podman"
    runtime.write_text("runtime", encoding="utf-8")
    authorization_root = tmp_path / "input"
    snapshots = tmp_path / "snapshots"
    output = tmp_path / "output"
    authorization_root.mkdir()
    snapshots.mkdir()
    output.mkdir()
    authorization = authorization_root / "TARGET_AUTHORIZATION.json"
    authorization.write_text("{}", encoding="utf-8")
    image_digest = "sha256:" + "e" * 64
    runtime_manifest: dict[str, object] = {
        "artifact_kind": "selected_result_verifier_target_runtime_manifest",
        "runtime_manifest_version": "1.0.0",
        "input_projection": "installed_runtime_only",
        "project_code_executed": False,
    }
    runtime_manifest["target_runtime_manifest_digest"] = semantic_digest(runtime_manifest)
    runtime_payload = (canonical_json(runtime_manifest) + "\n").encode("utf-8")
    freeze = {
        "isolation_backend": {
            "runtime_profile": "podman-rootless-v1",
            "runtime_executable": {
                "path": str(runtime),
                "content_digest": "sha256:" + "d" * 64,
                "version_output": "podman version test-1.0",
            },
            "image_digest": image_digest,
            "target_runtime_manifest": {
                "target_runtime_manifest_digest": runtime_manifest[
                    "target_runtime_manifest_digest"
                ],
                "content_digest": sha256_digest(runtime_payload),
                "probe_command_profile": "rootless-oci-runtime-manifest-v1",
            },
        }
    }
    commands: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        commands.append(command)
        if command[1] == "info":
            return SimpleNamespace(returncode=0, stdout="true\n", stderr="")
        if command[1:3] == ["image", "inspect"]:
            return SimpleNamespace(returncode=0, stdout=image_digest + "\n", stderr="")
        if "--runtime-manifest" in command:
            volume = command[command.index("--volume") + 1]
            output_root = Path(volume.split(":", 1)[0])
            (output_root / "runtime-manifest.json").write_bytes(runtime_payload)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(os, "geteuid", lambda: 501)
    monkeypatch.setattr(os, "getegid", lambda: 20)
    _run_target_worker_in_oci(
        freeze=freeze,
        authorization_path=authorization,
        snapshot_root=snapshots,
        output_parent=output,
        snapshot_inventory_digest="sha256:" + "c" * 64,
    )

    launch = commands[-1]
    joined = " ".join(launch).casefold()
    assert "oracle" not in joined
    assert "provider-pack" not in joined
    assert "semantic-panel" not in joined
    assert "--network=none" in launch
    assert "--read-only" in launch
    assert "--pull=never" in launch
    assert "--cap-drop=all" in launch
    assert "--unsetenv-all" in launch
    assert "--env=PYTHONNOUSERSITE=1" in launch
    assert image_digest in launch


def test_target_worker_oci_launch_rejects_non_rootless_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = tmp_path / "podman"
    runtime.write_text("runtime", encoding="utf-8")
    freeze = {
        "isolation_backend": {
            "runtime_executable": {"path": str(runtime)},
            "image_digest": "sha256:" + "e" * 64,
        }
    }
    monkeypatch.setattr(os, "geteuid", lambda: 501)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="false\n", stderr=""),
    )

    with pytest.raises(ValueError, match="not operating rootlessly"):
        _run_target_worker_in_oci(
            freeze=freeze,
            authorization_path=tmp_path / "input.json",
            snapshot_root=tmp_path / "snapshots",
            output_parent=tmp_path / "output",
            snapshot_inventory_digest="sha256:" + "c" * 64,
        )
