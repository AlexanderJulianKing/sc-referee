from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    VERIFIER_VERSION,
    _implementation_lock,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.profiles import scientific_check_release_registry


def _freeze(project_root: Path) -> dict[str, Any]:
    path = (
        project_root
        / "evaluation"
        / "qualification"
        / "complete-domain-exposure-denominator-v1.1.0-precase"
        / "FREEZE_MANIFEST.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_complete_domain_precase_freeze_replays_exact_current_tuple(
    project_root: Path,
) -> None:
    freeze = _freeze(project_root)
    declared_digest = freeze.pop("freeze_digest")
    assert declared_digest == semantic_digest(freeze)
    freeze["freeze_digest"] = declared_digest

    registry = scientific_check_release_registry()
    check_id = freeze["envelope"]["check_id"]
    module = next(item for item in registry.modules if item.manifest.check_id == check_id)
    binding = next(item for item in registry.method_conflict_bindings if item.check_id == check_id)
    adapter = module.adapter_manifests[0]

    assert module.declared_manifest_digest == freeze["scientific_check"]["check_manifest_digest"]
    assert adapter.manifest_digest == freeze["adapter"]["adapter_manifest_digest"]
    assert adapter.recognition_grammar_digest == freeze["adapter"]["recognition_grammar_digest"]
    assert binding.binding_digest == freeze["binding"]["binding_digest"]
    assert binding.detector_manifest_digest == freeze["detector"]["detector_manifest_digest"]

    comparator = freeze["selected_result_comparator"]
    assert comparator["profile_id"] == PYTHON_STATIC_MARKED_REPORT_PROFILE
    assert comparator["verifier_version"] == VERIFIER_VERSION
    assert _implementation_lock() == [
        {
            "path": comparator["implementation_path"].removeprefix("evaluation/src/"),
            "content_digest": comparator["implementation_digest"],
            "dependency_kind": "implementation",
        },
        {
            "path": "python-runtime",
            "content_digest": comparator["python_runtime_digest"],
            "dependency_kind": "runtime",
        },
    ]


def test_complete_domain_precase_freeze_source_files_and_scope_have_not_drifted(
    project_root: Path,
) -> None:
    freeze = _freeze(project_root)
    path_digest_pairs = (
        (freeze["detector"]["implementation_path"], freeze["detector"]["implementation_digest"]),
        (
            freeze["scientific_check"]["profile_source_path"],
            freeze["scientific_check"]["profile_source_digest"],
        ),
        (
            freeze["adapter"]["implementation_path"],
            freeze["adapter"]["implementation_source_digest"],
        ),
        (
            freeze["selected_result_comparator"]["implementation_path"],
            freeze["selected_result_comparator"]["implementation_digest"],
        ),
        (
            freeze["evidence_contract"]["implementation_path"],
            freeze["evidence_contract"]["implementation_digest"],
        ),
        (
            freeze["evidence_contract"]["study_template_path"],
            freeze["evidence_contract"]["study_template_content_digest"],
        ),
        (
            freeze["development_control_ref"]["path"],
            freeze["development_control_ref"]["content_digest"],
        ),
        (
            freeze["build_identity"]["evaluation_pyproject_path"],
            freeze["build_identity"]["evaluation_pyproject_digest"],
        ),
    )
    for relative, expected in path_digest_pairs:
        assert sha256_digest((project_root / relative).read_bytes()) == expected

    template = json.loads(
        (project_root / freeze["evidence_contract"]["study_template_path"]).read_text(
            encoding="utf-8"
        )
    )
    envelope = next(
        item
        for item in template["envelopes"]
        if item["envelope_id"] == freeze["envelope"]["envelope_id"]
    )
    assert envelope == {
        "binding_digest": freeze["binding"]["binding_digest"],
        "candidate_id": freeze["envelope"]["candidate_id"],
        "canonical_issue_class": freeze["envelope"]["canonical_issue_class"],
        "case_evidence_contract_version": freeze["envelope"]["case_evidence_contract_version"],
        "check_id": freeze["envelope"]["check_id"],
        "envelope_id": freeze["envelope"]["envelope_id"],
    }
    assert freeze["metric_case_count"] == 0
    assert freeze["scientific_label_count"] == 0
    assert freeze["detector_outcome_count"] == 0
    assert freeze["detector"]["production_finding_permitted"] is False
