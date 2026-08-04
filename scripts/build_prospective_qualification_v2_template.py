from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sc_referee.core.ids import canonical_json, semantic_digest  # noqa: E402
from sc_referee.scientific_checks.profiles import (  # noqa: E402
    scientific_check_release_registry,
)

OUTPUT = ROOT / "evaluation" / "prospective-qualification-v2" / "ten-envelope-study.template.json"

TARGETS = (
    (
        "founder-orientation-before-hmm-emission",
        "check:founder-orientation-before-hmm-emission",
        "repair-before-emission",
        "issue-class:unrepaired-inherited-orientation",
    ),
    (
        "directional-measurement-error-interpretation",
        "check:directional-measurement-error-interpretation",
        "direction-specific-decomposition",
        "issue-class:symmetric-error-used-for-directional-process",
    ),
    (
        "poststratified-misclassification-estimator",
        "check:poststratified-misclassification-estimator",
        "constrained-cellwise-calibration-then-standardize",
        "issue-class:pool-before-cellwise-correction",
    ),
    (
        "expected-count-background-construction",
        "check:expected-count-background-construction",
        "negative-binomial-model-prediction",
        "issue-class:arithmetic-mean-used-for-model-expected-count",
    ),
    (
        "recoverable-technical-group-adjustment",
        "check:recoverable-technical-group-adjustment",
        "include-recovered-technical-group",
        "issue-class:recoverable-technical-group-omitted",
    ),
    (
        "phase-split-mvmr-instrument-construction",
        "check:phase-split-mvmr-instrument-construction",
        "phase1-ld-conditional-signals-phase2-joint-coefficients",
        "issue-class:marginal-instruments-used-for-conditional-joint-target",
    ),
    (
        "classifier-derived-copy-dosage-representation",
        "check:classifier-derived-copy-dosage-representation",
        "direct-continuous-calibrated-copy-dosage",
        "issue-class:hard-or-binned-dosage-used-for-continuous-target",
    ),
    (
        "somatic-clonality-representation",
        "check:somatic-clonality-representation",
        "purity-copy-adjusted-clonal-fraction-window",
        "issue-class:raw-eligibility-used-for-adjusted-clonality-target",
    ),
    (
        "local-perturbation-regression-specification",
        "check:local-perturbation-regression-specification",
        "joint-target-axes-with-guide-nuisance-terms",
        "issue-class:reduced-residualized-fit-used-for-joint-target",
    ),
    (
        "complete-domain-exposure-denominator",
        "check:complete-domain-exposure-denominator",
        "complete-declared-domain-exposure",
        "issue-class:retained-subset-for-complete-domain",
    ),
)


def main() -> None:
    registry = scientific_check_release_registry()
    modules = {module.manifest.check_id: module for module in registry.modules}
    bindings = {binding.check_id: binding for binding in registry.method_conflict_bindings}
    envelopes: list[dict[str, str]] = []
    for suffix, check_id, candidate_id, issue_class in TARGETS:
        module = modules[check_id]
        if candidate_id not in {
            candidate.candidate_id for candidate in module.manifest.requirement_candidates
        }:
            raise ValueError(f"Unknown candidate {candidate_id!r} for {check_id!r}.")
        envelopes.append(
            {
                "envelope_id": f"relation-envelope:{suffix}",
                "check_id": check_id,
                "candidate_id": candidate_id,
                "binding_digest": bindings[check_id].binding_digest,
                "canonical_issue_class": issue_class,
                "case_evidence_contract_version": "2.0.0",
            }
        )
    template: dict[str, object] = {
        "artifact_kind": "prospective_qualification_study_template",
        "template_version": "2.0.0",
        "template_id": "prospective-template:ten-generic-relation-envelopes-v2",
        "qualification_authority": "none_template_only",
        "expected_envelope_count": 10,
        "envelopes": envelopes,
        "required_blocks": ["threshold_pilot", "qualification_heldout"],
        "required_cell_types": [
            "error_bearing",
            "corrected_twin",
            "valid_alternative",
            "hard_negative",
            "ambiguous",
            "unsupported",
            "renamed_implementation",
        ],
        "minimum_frozen_case_count": 140,
        "required_prelabel_artifacts": [
            "canonical_issue_class_registry",
            "exact_case_evidence_contract",
            "independent_selected_result_binding_validation",
        ],
        "label_resolution_fields": [
            "scientific_label_enum",
            "canonical_issue_class_id",
            "selected_result_binding_digest",
            "finite_counterevidence_status",
        ],
        "label_resolution_excluded_fields": ["bounded_description"],
        "heldout_state": "must_remain_sealed_until_pilot_threshold_decision",
        "external_evidence_required": [
            "prospectively_authored_case_material",
            "authenticated_cross-provider_stage1_reviews",
            "authenticated_cross-provider_stage2_reviews",
            "independent_selected_result_evidence_validation",
            "pilot_threshold_decision",
            "heldout_metric_record",
            "ten_envelope_specific_maintainer_promotion_decisions",
        ],
    }
    template["template_digest"] = semantic_digest(template)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(canonical_json(template) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
