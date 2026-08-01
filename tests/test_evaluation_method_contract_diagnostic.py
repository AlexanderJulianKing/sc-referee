from __future__ import annotations

import json
from pathlib import Path

from sc_referee_evaluation.method_contract_diagnostic import (
    diagnose_genebench_method_contract_conflict,
)

from sc_referee.controller import run_audit
from sc_referee.core.ids import sha256_digest
from sc_referee.method_contracts import build_expected_count_profile


def _reference_profile() -> dict[str, object]:
    return build_expected_count_profile(
        estimator_family="negative_binomial_glm",
        likelihood_family="negative_binomial",
        link_function="log",
        background_scope="model_predicted_expected_count",
        grouping_structure="replicate_intercepts",
        covariate_terms=["distance", "gc", "restriction_site_count"],
        group_specific_terms=["distance", "gc"],
        training_exclusions=[
            "case_specific_structural_variant",
            "low_mappability",
            "target_observation",
        ],
        target_excluded=True,
        analysis_resolution_bp=20_000,
    )


def test_genebench_answer_side_diagnostic_localizes_without_mutating_production_audit(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "workspace"
    repository.mkdir()
    (repository / "report.md").write_text(
        "# Result\n\n"
        "At the queried 20 kb pixel, the mean case loop strength is **2.018599**, "
        "the mean control loop strength is **0.027571**, and the case-minus-control "
        "difference is **1.991029** log2 units.\n\n"
        "# Method\n\n"
        "For each replicate independently, I used the arithmetic mean of all other "
        "20 kb pixels at the same nine-bin separation as the expected count. The focal "
        "pixel was left out so that a true loop could not raise its own expected value "
        "in this small matrix.\n\n"
        "Pairs incident to bins with mappability below 0.80 were excluded from the "
        "background.\n",
        encoding="utf-8",
    )
    audit_root = tmp_path / "audit"
    production = run_audit(repository, audit_root, schema_root, report="report.md")
    before_bundle = (audit_root / "audit.bundle.json").read_bytes()
    before_lock = (audit_root / "semantic.lock.json").read_bytes()
    locked_at = str(json.loads(before_lock)["locked_at"])
    production_result = next(
        item
        for item in production["detector_results"]
        if item["detector_id"] == "detector:bounded-reported-method-contract-conflict"
    )
    assert production_result["state"] == "insufficient_semantics"
    assert production["findings"] == []

    reference_payload = json.dumps(_reference_profile(), sort_keys=True).encode("utf-8")
    diagnostic = diagnose_genebench_method_contract_conflict(
        audit_root,
        schema_root,
        _reference_profile(),
        reference_id="genebench-public:hic_sv_masked_loop_strength:reference-method",
        reference_content_digest=sha256_digest(reference_payload),
        diagnosed_at=locked_at,
        output=tmp_path / "diagnostic.json",
    )

    assert diagnostic["case"]["corpus_partition"] == "public_development"
    assert diagnostic["production_audit"]["finding_count"] == 0
    assert diagnostic["production_audit"]["detector_state"] == "insufficient_semantics"
    assert diagnostic["diagnostic_detector_result"]["state"] == ("evaluation_finding_candidate")
    assert diagnostic["metric_eligible"] is False
    assert diagnostic["promotion_evidence_eligible"] is False
    assert diagnostic["project_code_executed_by_diagnostic"] is False
    assert diagnostic["model_invoked_by_diagnostic"] is False
    assert (audit_root / "audit.bundle.json").read_bytes() == before_bundle
    assert (audit_root / "semantic.lock.json").read_bytes() == before_lock
