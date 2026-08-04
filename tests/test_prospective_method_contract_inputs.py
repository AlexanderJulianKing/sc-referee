from __future__ import annotations

import json
import stat
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.prospective_method_contract_inputs import (
    ProspectiveMethodContractInputError,
    build_prospective_method_contract_inputs,
    write_prospective_method_contract_inputs_once,
)
from sc_referee_evaluation.prospective_study_scaffold import (
    build_prospective_study_scaffold,
)

from sc_referee.core.ids import semantic_digest, sha256_digest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = (
    ROOT / "evaluation" / "prospective-qualification-v1" / "ten-envelope-study.template.json"
)
AUTHORING_TEMPLATE_PATH = (
    ROOT
    / "evaluation"
    / "prospective-qualification-v1"
    / "benchmark-blind-authoring-briefs.template.json"
)


def test_standalone_contract_input_cli_bootstraps_checkout_imports() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_prospective_method_contract_inputs.py"),
            "--help",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "--allow-heldout" in completed.stdout


def _participant(identifier: str, role: str, provider: str) -> dict[str, str]:
    return {
        "participant_id": identifier,
        "role": role,
        "provider": provider,
        "execution_context_id": f"context:{identifier}",
        "identity_evidence_digest": sha256_digest(f"identity:{identifier}"),
    }


def _setup() -> dict[str, Any]:
    participants = [
        _participant("actor:pilot-primary", "author", "author-provider-a"),
        _participant("actor:pilot-rewrite", "author", "author-provider-b"),
        _participant("actor:heldout-primary", "author", "author-provider-c"),
        _participant("actor:heldout-rewrite", "author", "author-provider-d"),
        _participant("actor:s1-a1", "stage1_reviewer", "review-provider-a"),
        _participant("actor:s1-a2", "stage1_reviewer", "review-provider-a"),
        _participant("actor:s1-b1", "stage1_reviewer", "review-provider-b"),
        _participant("actor:s1-b2", "stage1_reviewer", "review-provider-b"),
        _participant("actor:s2-c", "stage2_reviewer", "review-provider-c"),
        _participant("actor:s2-d", "stage2_reviewer", "review-provider-d"),
        _participant("actor:detector", "detector_implementer", "implementation-provider"),
    ]
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    authoring = json.loads(AUTHORING_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return {
        "study_id": "study:prospective-ten-envelope-v1",
        "protocol_id": "prospective-protocol:ten-envelope-v1",
        "template_digest": template["template_digest"],
        "authoring_template_digest": authoring["template_digest"],
        "detector_lock": {
            "detector_id": "detector:generic-method-conflict",
            "detector_version": "0.3.0",
            "detector_manifest_digest": sha256_digest("detector-manifest"),
            "implementation_digest": sha256_digest("detector-implementation"),
            "frozen_at": "2026-08-04T12:00:00Z",
        },
        "participants": participants,
        "block_assignments": [
            {
                "block_id": "block:pilot",
                "evidence_role": "threshold_pilot",
                "primary_author_ids": ["actor:pilot-primary"],
                "renamed_author_ids": ["actor:pilot-rewrite"],
                "submission_deadline": "2026-08-05T12:00:00Z",
                "submission_channel": "channel:author-submission-a",
            },
            {
                "block_id": "block:heldout",
                "evidence_role": "qualification_heldout",
                "primary_author_ids": ["actor:heldout-primary"],
                "renamed_author_ids": ["actor:heldout-rewrite"],
                "submission_deadline": "2026-08-06T12:00:00Z",
                "submission_channel": "channel:author-submission-b",
            },
        ],
        "stage1_reviewer_ids": [
            "actor:s1-a1",
            "actor:s1-a2",
            "actor:s1-b1",
            "actor:s1-b2",
        ],
        "stage2_reviewer_ids": ["actor:s2-c", "actor:s2-d"],
        "case_id_key": "7a" * 32,
        "assigned_at": "2026-08-04T12:30:00Z",
        "protocol_frozen_at": "2026-08-04T13:00:00Z",
    }


def _scaffold() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    authoring = json.loads(AUTHORING_TEMPLATE_PATH.read_text(encoding="utf-8"))
    files = build_prospective_study_scaffold(template, authoring, _setup())
    protocol = json.loads(files["coordinator/protocol.json"])
    relation_map = json.loads(files["coordinator/relation-binding-map.json"])
    briefs = [
        json.loads(payload)
        for path, payload in files.items()
        if path.startswith("coordinator/authoring-briefs/")
    ]
    return protocol, relation_map, briefs


def _build(
    *,
    block_id: str = "block:pilot",
    allow_heldout: bool = False,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    protocol, relation_map, briefs = _scaffold()
    files = build_prospective_method_contract_inputs(
        protocol,
        relation_map,
        briefs,
        block_id=block_id,
        scientist_id="scientist:example",
        allow_heldout=allow_heldout,
    )
    return files, protocol


def test_builds_seventy_digest_bound_project_shells_without_case_outputs() -> None:
    files, protocol = _build()
    manifest = json.loads(files["INPUT_MANIFEST.json"])
    declared = manifest.pop("manifest_digest")
    assert semantic_digest(manifest) == declared
    assert manifest["validated_matrix"] == {
        "relation_count": 10,
        "cell_types_per_relation": 7,
        "case_count": 70,
        "complete": True,
    }
    assert manifest["qualification_authority"] == "none_evaluation_input_only"
    assert manifest["creation_boundary"] == {
        "write_policy": "new_absent_output_root_only",
        "task_file_policy": "write_once_digest_bound_and_read_only",
        "contains_case_implementation": False,
        "contains_report_material": False,
        "contains_scientific_labels": False,
        "contains_detector_observations": False,
        "contains_method_contract_locks": False,
        "project_authored_code_executed": False,
    }
    assert len([path for path in files if path.endswith("/TASK.md")]) == 70
    assert len([path for path in files if path.endswith("method-contract-profile.json")]) == 70

    envelopes = {item["envelope_id"]: item for item in protocol["envelopes"]}
    for record in manifest["projects"]:
        root = record["project_path"]
        task = files[f"{root}/TASK.md"]
        profile = json.loads(files[f"{root}/method-contract-profile.json"])
        envelope = envelopes[record["envelope_id"]]
        assert set(profile) == {"profile_id", "profile_version", "check_id", "candidate_id"}
        assert profile == {
            "profile_id": "scientific_check_requirement_v1",
            "profile_version": "1.0.0",
            "check_id": envelope["check_id"],
            "candidate_id": envelope["candidate_id"],
        }
        assert record["task_content_digest"] == sha256_digest(task)
        assert record["profile_semantic_digest"] == semantic_digest(profile)

    combined = b"\n".join(files.values()).lower()
    for forbidden in (
        b'"cell_type"',
        b'"scientific_label"',
        b'"detector_observation"',
        b'"issue_present"',
        b'"issue_absent"',
        b'"evaluation_finding_candidate"',
    ):
        assert forbidden not in combined
    assert not any(path.endswith((".py", ".r", ".ipynb")) for path in files)
    assert files == _build()[0]


def test_each_task_uses_only_its_frozen_human_premise() -> None:
    files, _ = _build()
    protocol, _, briefs = _scaffold()
    pilot_assignments = {
        item["case_id"]: item
        for item in protocol["assignments"]
        if item["block_id"] == "block:pilot"
    }
    briefs_by_case = {item["opaque_case_id"]: item for item in briefs}
    manifest = json.loads(files["INPUT_MANIFEST.json"])
    for record in manifest["projects"]:
        case_id = record["case_id"]
        task = files[f"{record['project_path']}/TASK.md"].decode("utf-8")
        relation = briefs_by_case[case_id]["one_relation_brief"]
        assert relation["governed_premise"] in task
        assert relation["contrasting_construction"] not in task
        assert (
            pilot_assignments[case_id]["authoring_brief_digest"] == record["authoring_brief_digest"]
        )
        assert "not a universal scientific claim" in task
        assert "No project-authored code was executed" in task


def test_rejects_tampered_protocol_map_and_assignment_brief() -> None:
    protocol, relation_map, briefs = _scaffold()

    bad_protocol = deepcopy(protocol)
    bad_protocol["protocol_id"] = "changed"
    with pytest.raises(ProspectiveMethodContractInputError, match="digest does not replay"):
        build_prospective_method_contract_inputs(
            bad_protocol,
            relation_map,
            briefs,
            block_id="block:pilot",
            scientist_id="scientist:example",
        )

    bad_map = deepcopy(relation_map)
    bad_map["protocol_ref"]["protocol_id"] = "changed"
    bad_map_without_digest = {
        key: value for key, value in bad_map.items() if key != "mapping_digest"
    }
    bad_map["mapping_digest"] = semantic_digest(bad_map_without_digest)
    with pytest.raises(ProspectiveMethodContractInputError, match="not bound"):
        build_prospective_method_contract_inputs(
            protocol,
            bad_map,
            briefs,
            block_id="block:pilot",
            scientist_id="scientist:example",
        )

    pilot_case = next(
        item["case_id"] for item in protocol["assignments"] if item["block_id"] == "block:pilot"
    )
    bad_briefs = deepcopy(briefs)
    target = next(item for item in bad_briefs if item["opaque_case_id"] == pilot_case)
    target["one_relation_brief"]["governed_premise"] += " changed"
    target_without_digest = {key: value for key, value in target.items() if key != "brief_digest"}
    target["brief_digest"] = semantic_digest(target_without_digest)
    with pytest.raises(ProspectiveMethodContractInputError, match="frozen assignment digest"):
        build_prospective_method_contract_inputs(
            protocol,
            relation_map,
            bad_briefs,
            block_id="block:pilot",
            scientist_id="scientist:example",
        )


def test_heldout_shells_are_sealed_by_default_and_require_explicit_opt_in() -> None:
    protocol, relation_map, briefs = _scaffold()
    with pytest.raises(ProspectiveMethodContractInputError, match="remain sealed"):
        build_prospective_method_contract_inputs(
            protocol,
            relation_map,
            briefs,
            block_id="block:heldout",
            scientist_id="scientist:example",
        )
    files, _ = _build(block_id="block:heldout", allow_heldout=True)
    manifest = json.loads(files["INPUT_MANIFEST.json"])
    assert manifest["block_ref"] == {
        "block_id": "block:heldout",
        "evidence_role": "qualification_heldout",
    }
    assert len(manifest["projects"]) == 70


def test_write_is_create_once_and_marks_contract_inputs_read_only(tmp_path: Path) -> None:
    files, _ = _build()
    output = tmp_path / "contract-inputs"
    assert write_prospective_method_contract_inputs_once(output, files) == output.resolve()
    for relative, payload in files.items():
        path = output / relative
        assert path.read_bytes() == payload
        if path.name in {"TASK.md", "method-contract-profile.json"}:
            assert stat.S_IMODE(path.stat().st_mode) == 0o444
    with pytest.raises(ProspectiveMethodContractInputError, match="already exists"):
        write_prospective_method_contract_inputs_once(output, files)
