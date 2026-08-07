from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.prospective_qualification_v2 import (
    AUTHOR_DECLARATION_VERSION,
    CASE_EVIDENCE_CONTRACT_VERSION,
    SCIENTIFIC_LABEL_VERSION,
)
from sc_referee_evaluation.prospective_selected_result_verifier import VERIFIER_VERSION

from sc_referee.core.ids import semantic_digest, sha256_digest

EXPECTED_FREEZE_DIGEST = "sha256:2526c7d710705bc8705ffc8dbc062f233c5555f8e9445d1ffea23c50a68a14d6"


def _freeze(project_root: Path) -> dict[str, Any]:
    path = (
        project_root
        / "evaluation"
        / "qualification"
        / "complete-domain-exposure-denominator-v1.1.0-v3-precase"
        / "FREEZE_MANIFEST.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_content_digest(project_root: Path, path: str, digest: str) -> None:
    assert sha256_digest((project_root / path).read_bytes()) == digest


def test_v3_precase_freeze_is_self_authenticating_and_supersedes_v2(
    project_root: Path,
) -> None:
    freeze = _freeze(project_root)
    declared_digest = freeze.pop("freeze_digest")

    assert declared_digest == semantic_digest(freeze)
    assert declared_digest == EXPECTED_FREEZE_DIGEST
    assert freeze["freeze_version"] == "2.0.0"
    assert freeze["source_commit"] == "b723f000bccff18d49efca64a4d6ece92e2b5dd2"
    assert freeze["supersedes_freeze_digest"] == (
        "sha256:55a515535246aa1a4d1c091ed020e8a087b78552b727ee947439b26a01142ae8"
    )


def test_v3_precase_freeze_binds_current_contract_and_tuple(project_root: Path) -> None:
    freeze = _freeze(project_root)
    envelope = freeze["envelope"]
    contract = freeze["evidence_contract"]

    assert envelope == {
        "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
        "canonical_issue_class": "issue-class:retained-subset-for-complete-domain",
        "check_id": "check:complete-domain-exposure-denominator",
        "candidate_id": "complete-declared-domain-exposure",
        "binding_digest": (
            "sha256:127306babb8127dc820ea2d3f322ca47e7da0af976ea771eb7ef10e445fcb4f5"
        ),
        "case_evidence_contract_version": CASE_EVIDENCE_CONTRACT_VERSION,
    }
    assert contract["author_declaration_version"] == AUTHOR_DECLARATION_VERSION
    assert contract["case_evidence_contract_version"] == CASE_EVIDENCE_CONTRACT_VERSION
    assert contract["scientific_label_version"] == SCIENTIFIC_LABEL_VERSION
    assert freeze["selected_result_comparator"]["verifier_version"] == VERIFIER_VERSION

    template = json.loads(
        (project_root / contract["study_template_path"]).read_text(encoding="utf-8")
    )
    # The v1.2.0 repair regenerated the study template, so the frozen tuple's
    # declared template digest is historical: the current template must still
    # carry this envelope, but under a successor binding digest.
    assert template["template_digest"] != contract["study_template_declared_digest"]
    successor = next(
        item for item in template["envelopes"] if item["envelope_id"] == envelope["envelope_id"]
    )
    assert successor["binding_digest"] != envelope["binding_digest"]
    assert successor["case_evidence_contract_version"] == CASE_EVIDENCE_CONTRACT_VERSION


def test_v3_precase_freeze_is_historical_after_the_v120_detector_repair(
    project_root: Path,
) -> None:
    """The v1.1.0 tuple is invalidated, not silently retargeted, by the repair.

    The failed v1.1.0 pilot was completed and retained under this tuple. The
    detector grammar repair that followed created check/adapter version 1.2.0,
    so the frozen profile-source binding must no longer equal the current
    bytes: the tuple is historical evidence for the failing measurement, and a
    fresh tuple must be frozen before any v1.2.0 qualification work.
    """

    freeze = _freeze(project_root)
    record = freeze["scientific_check"]
    assert (
        sha256_digest((project_root / record["profile_source_path"]).read_bytes())
        != record["profile_source_digest"]
    )
    contract = freeze["evidence_contract"]
    assert (
        sha256_digest((project_root / contract["study_template_path"]).read_bytes())
        != contract["study_template_content_digest"]
    )


def test_v3_precase_freeze_binds_exact_unrepaired_source_bytes(project_root: Path) -> None:
    freeze = _freeze(project_root)
    for section, path_key, digest_key in (
        ("detector", "implementation_path", "implementation_digest"),
        ("adapter", "implementation_path", "implementation_source_digest"),
        ("selected_result_comparator", "implementation_path", "implementation_digest"),
        ("evidence_contract", "implementation_path", "implementation_digest"),
        ("direct_lane", "implementation_path", "implementation_digest"),
        ("direct_lane", "prospective_allocator_path", "prospective_allocator_digest"),
        ("direct_lane", "review_protocol_path", "review_protocol_digest"),
        ("direct_lane", "stage1_prompt_path", "stage1_prompt_digest"),
        ("direct_lane", "stage2_prompt_path", "stage2_prompt_digest"),
        ("development_control_ref", "path", "content_digest"),
    ):
        record = freeze[section]
        _assert_content_digest(project_root, record[path_key], record[digest_key])


def test_v3_precase_freeze_has_no_case_or_finding_authority(project_root: Path) -> None:
    freeze = _freeze(project_root)

    assert freeze["metric_case_count"] == 0
    assert freeze["scientific_label_count"] == 0
    assert freeze["detector_outcome_count"] == 0
    assert freeze["qualification_authority"] == "none_precase_freeze_only"
    assert freeze["detector"]["production_finding_permitted"] is False
    assert freeze["selected_result_comparator"]["scientific_label_authority"] is False
    assert freeze["development_control_ref"]["metric_eligible"] is False
