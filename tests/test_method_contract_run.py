from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.agent_protocol import load_audit_status
from sc_referee.cli import app
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.method_contract_run import run_method_contract
from sc_referee.method_contracts import build_expected_count_profile
from sc_referee.scientific_checks import ScientificCheckRegistry
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    ScientificRequirementContractError,
)

FOUNDER_CHECK = "check:founder-orientation-before-hmm-emission"


def _founder_requirement_profile() -> dict[str, str]:
    return {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        "check_id": FOUNDER_CHECK,
        "candidate_id": "repair-before-emission",
    }


def _expected_count_requirement_profile() -> dict[str, str]:
    return {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        "check_id": "check:expected-count-background-construction",
        "candidate_id": "negative-binomial-model-prediction",
    }


def _write_founder_workflow(repository: Path, *, repaired: bool) -> None:
    if repaired:
        method = "Founder alleles were reoriented before the HMM emission."
        preparation = (
            "    repaired = orient_ril_founder_alleles(sample.founder_alleles)\n"
            "    return emission_matrix(observed, repaired[0], 0.01)\n"
        )
    else:
        method = "The founder-origin HMM was fitted using the supplied founder alleles."
        preparation = "    return emission_matrix(observed, sample.founder_alleles[0], 0.01)\n"
    (repository / "report.md").write_text(method + "\n", encoding="utf-8")
    (repository / "analysis.py").write_text(
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n\n"
        "def emission_matrix(observed, founder_state, error):\n"
        "    return observed == founder_state\n\n"
        "def fit(sample, observed):\n"
        f"{preparation}\n"
        "def main():\n"
        f"    (ROOT / 'report.md').write_text({method!r} + '\\n')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )


def _negative_binomial_profile() -> dict[str, object]:
    return build_expected_count_profile(
        estimator_family="negative_binomial_glm",
        likelihood_family="negative_binomial",
        link_function="log",
        background_scope="model_predicted_expected_count",
        grouping_structure="replicate_intercepts",
        covariate_terms=[
            "distance",
            "exposure",
            "gc",
            "mappability",
            "restriction_site_count",
        ],
        group_specific_terms=["distance", "gc"],
        training_exclusions=[
            "case_specific_structural_variant",
            "low_mappability",
            "target_observation",
        ],
        target_excluded=True,
        analysis_resolution_bp=20_000,
    )


def _write_report(repository: Path) -> None:
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


def test_claimless_method_contract_preserves_an_unresolved_profile(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Estimate observed-over-expected loop strength.\n", encoding="utf-8"
    )
    marker = repository / "must-not-exist"
    (repository / "analysis.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
        encoding="utf-8",
    )

    output = tmp_path / "contract"
    bundle = run_method_contract(
        repository,
        "task.md",
        output,
        schema_root,
    )

    assert bundle["claims"] == []
    assert bundle["publication_surfaces"] == []
    assert bundle["semantic_assertions"] == []
    assert len(bundle["scientific_contracts"]) == 1
    contract = bundle["scientific_contracts"][0]
    assert contract["scope"]["level"] == "analysis"
    assert contract["extensions"]["x-method-profile-resolution-status"] == "unresolved"
    assert bundle["material_questions"][0]["status"] == "open"
    assert bundle["findings"] == []
    assert not marker.exists()
    assert load_audit_status(output, schema_root).integrity == "verified"

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "scientific_contracts",
        "semantic_assertions",
        "claims",
        "material_questions",
        "answers",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]


def test_claimless_method_contract_freezes_human_intent_without_resolving_unrelated_dimensions(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Estimate observed-over-expected loop strength.\n", encoding="utf-8"
    )

    output = tmp_path / "contract"
    bundle = run_method_contract(
        repository,
        "task.md",
        output,
        schema_root,
        profile=_negative_binomial_profile(),
        actor_id="scientist:alex",
    )

    assert bundle["claims"] == []
    assert bundle["publication_surfaces"] == []
    assert len(bundle["answers"]) == 1
    assert bundle["material_questions"][0]["status"] == "answered"
    declarations = [
        item
        for item in bundle["semantic_assertions"]
        if item["assertion_class"] == "scientist_declaration"
    ]
    derivations = [
        item
        for item in bundle["semantic_assertions"]
        if item["assertion_class"] == "deterministic_derivation"
    ]
    assert len(declarations) == len(derivations) == 6
    assert {item["finding_eligibility"] for item in declarations} == {"ineligible"}
    assert {item["finding_eligibility"] for item in derivations} == {"eligible"}
    contract = bundle["scientific_contracts"][0]
    assert contract["status"] == "draft"
    assert contract["extensions"]["x-method-profile-resolution-status"] == "resolved"
    assert contract["dimensions"]["target_population"]["state"] == "unknown"
    assert bundle["findings"] == []

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["scientific_contracts"] == bundle["scientific_contracts"]
    assert replayed["semantic_assertions"] == bundle["semantic_assertions"]
    assert replayed["answers"] == bundle["answers"]


def test_claimless_scientific_requirement_resolves_only_a_published_atomic_choice(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Reconstruct founder-origin hidden states under the specified orientation rule.\n",
        encoding="utf-8",
    )

    output = tmp_path / "contract"
    bundle = run_method_contract(
        repository,
        "task.md",
        output,
        schema_root,
        profile=_founder_requirement_profile(),
        actor_id="scientist:alex",
    )

    assert bundle["claims"] == []
    assert bundle["publication_surfaces"] == []
    assert bundle["findings"] == []
    assert len(bundle["answers"]) == 1
    assert bundle["answers"][0]["answer_value"] == {
        "scale_and_orientation": "repair_ril_founder_orientation_before_hmm_emission"
    }
    assert bundle["material_questions"][0]["status"] == "answered"
    contract = bundle["scientific_contracts"][0]
    assert contract["dimensions"]["scale_and_orientation"]["state"] == "known"
    assert contract["dimensions"]["measurement_model"]["state"] == "unknown"
    assert contract["extensions"]["x-scientific-check-id"] == FOUNDER_CHECK
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    frozen = lock["method_contract_profile"]["profile_manifest"]
    assert frozen["check_manifest_digest"] == semantic_digest(frozen["check_manifest"])
    assert frozen["selected_candidate"]["candidate_id"] == "repair-before-emission"

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "scientific_contracts",
        "semantic_assertions",
        "material_questions",
        "answers",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]


def test_scientific_requirement_rejects_an_unpublished_candidate(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text("Define the analysis.\n", encoding="utf-8")
    profile = _founder_requirement_profile()
    profile["candidate_id"] = "benchmark-correct-answer"

    with pytest.raises(ScientificRequirementContractError, match="not published"):
        run_method_contract(
            repository,
            "task.md",
            tmp_path / "contract",
            schema_root,
            profile=profile,
            actor_id="scientist:alex",
        )


def test_scientific_requirement_parent_rejects_rehashed_candidate_tampering(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text("Define the analysis.\n", encoding="utf-8")
    parent = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        parent,
        schema_root,
        profile=_founder_requirement_profile(),
        actor_id="scientist:alex",
    )
    lock = json.loads((parent / "semantic.lock.json").read_text(encoding="utf-8"))
    lock["method_contract_profile"]["profile_manifest"]["selected_candidate"]["operand"][
        "value"
    ] = "use_supplied_founder_alleles_directly_in_hmm_emission"
    lock["method_contract_profile"]["profile_manifest_digest"] = semantic_digest(
        lock["method_contract_profile"]["profile_manifest"]
    )
    digest_input = dict(lock)
    digest_input.pop("semantic_lock_digest")
    lock["semantic_lock_digest"] = semantic_digest(digest_input)
    tampered = tmp_path / "tampered.lock.json"
    tampered.write_text(canonical_json(lock) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not uniquely published"):
        replay(tampered, tmp_path / "replay", schema_root)


def test_scientific_requirement_binding_rejects_active_registry_drift(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text("Define the analysis.\n", encoding="utf-8")
    parent = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        parent,
        schema_root,
        profile=_founder_requirement_profile(),
        actor_id="scientist:alex",
    )
    _write_founder_workflow(repository, repaired=False)
    default = default_scientific_check_registry()
    without_founder = ScientificCheckRegistry(
        tuple(module for module in default.modules if module.manifest.check_id != FOUNDER_CHECK)
    )

    with pytest.raises(ValueError, match="does not resolve to one installed"):
        run_audit(
            repository,
            tmp_path / "audit",
            schema_root,
            report="report.md",
            method_contract_lock=parent / "semantic.lock.json",
            scientific_check_registry=without_founder,
        )


def test_scientific_requirement_is_nonapplicable_when_current_evidence_has_no_target(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text("Define the analysis.\n", encoding="utf-8")
    parent = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        parent,
        schema_root,
        profile=_founder_requirement_profile(),
        actor_id="scientist:alex",
    )
    (repository / "report.md").write_text("No founder HMM was analyzed.\n", encoding="utf-8")
    (repository / "analysis.py").write_text("value = 1\n", encoding="utf-8")

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=parent / "semantic.lock.json",
    )

    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    binding = lock["parent_method_contract_binding"]
    assert binding["binding_status"] == "not_applicable"
    assert binding["bound_question_ids"] == []
    assert not [
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    ]
    assert bundle["findings"] == []


def test_same_contract_and_detector_core_handles_a_report_only_second_check(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Estimate observed-over-expected strength under the specified background model.\n",
        encoding="utf-8",
    )
    parent = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        parent,
        schema_root,
        profile=_expected_count_requirement_profile(),
        actor_id="scientist:alex",
    )
    (repository / "report.md").write_text(
        "For each replicate separately, the expected value was the arithmetic mean of counts "
        "on the same diagonal.\n",
        encoding="utf-8",
    )
    (repository / "analysis.py").write_text("value = 1\n", encoding="utf-8")

    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        method_contract_lock=parent / "semantic.lock.json",
    )

    result = next(
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert result["state"] == "evaluation_finding_candidate"
    ledger = next(
        item
        for item in result["evidence"]
        if item["evidence_id"] == "evidence:analysis-method-ledger"
    )
    assert ledger["observed_value"]["requirement"] == (
        "negative_binomial_glm_predicted_expected_count"
    )
    assert ledger["observed_value"]["observed"] == "same_stratum_arithmetic_mean_expected_count"
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("repaired", "expected_state"),
    [
        (False, "evaluation_finding_candidate"),
        (True, "no_issue_detected_within_coverage"),
    ],
)
def test_frozen_scientific_requirement_automatically_resolves_the_later_audit(
    schema_root: Path,
    tmp_path: Path,
    repaired: bool,
    expected_state: str,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Reconstruct founder-origin hidden states under the specified orientation rule.\n",
        encoding="utf-8",
    )
    parent = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        parent,
        schema_root,
        profile=_founder_requirement_profile(),
        actor_id="scientist:alex",
    )
    _write_founder_workflow(repository, repaired=repaired)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=parent / "semantic.lock.json",
    )

    questions = [
        item
        for item in bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id") == FOUNDER_CHECK
    ]
    assert len(questions) == 1
    assert questions[0]["status"] == "answered"
    answer = next(
        item
        for item in bundle["answers"]
        if item["question_ref"]["record_id"] == questions[0]["question_id"]
    )
    assert answer["response_source"] == "prior_scientist_record"
    assert answer["respondent"] == {
        "actor_kind": "human",
        "actor_id": "scientist:alex",
    }
    result = next(
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert result["state"] == expected_state
    assert bundle["findings"] == []
    replayed = replay(output / "semantic.lock.json", tmp_path / "audit-replay", schema_root)
    for field in (
        "scientific_contracts",
        "semantic_assertions",
        "material_questions",
        "answers",
        "detector_results",
    ):
        assert replayed[field] == bundle[field]


def test_later_audit_binds_frozen_analysis_contract_and_localizes_exact_conflict(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Estimate observed-over-expected loop strength.\n", encoding="utf-8"
    )
    contract_output = tmp_path / "contract"
    contract_bundle = run_method_contract(
        repository,
        "task.md",
        contract_output,
        schema_root,
        profile=_negative_binomial_profile(),
        actor_id="scientist:alex",
    )
    parent_contract_id = contract_bundle["scientific_contracts"][0]["contract_id"]
    _write_report(repository)

    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        method_contract_lock=contract_output / "semantic.lock.json",
    )

    claim = bundle["claims"][0]
    contract = next(
        item
        for item in bundle["scientific_contracts"]
        if item["contract_id"] == claim["scientific_contract_id"]
    )
    assert contract["scope"]["parent_contract_id"] == parent_contract_id
    assert claim["extensions"]["x-expected-count-profile-resolved"] is True
    intended = [
        item
        for item in bundle["semantic_assertions"]
        if item["predicate"].startswith("verified_intended_")
    ]
    assert len(intended) == 6
    parent_lock = json.loads(
        contract_output.joinpath("semantic.lock.json").read_text(encoding="utf-8")
    )
    assert all(
        item["extensions"]["x-parent-semantic-lock-digest"] == parent_lock["semantic_lock_digest"]
        for item in intended
    )
    result = next(
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-reported-method-contract-conflict"
    )
    assert result["state"] == "evaluation_finding_candidate"
    assert bundle["findings"] == []
    assert not any(
        question["status"] == "open"
        and question.get("extensions", {}).get("x-method-profile-id")
        == "expected_count_background_v1"
        for question in bundle["material_questions"]
    )

    replayed = replay(output / "semantic.lock.json", tmp_path / "audit-replay", schema_root)
    for field in (
        "claims",
        "scientific_contracts",
        "semantic_assertions",
        "material_questions",
        "detector_results",
        "findings",
    ):
        assert replayed[field] == bundle[field]


def test_later_binding_rejects_a_changed_governing_task(schema_root: Path, tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    task = repository / "task.md"
    task.write_text("Estimate observed-over-expected loop strength.\n", encoding="utf-8")
    contract_output = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        contract_output,
        schema_root,
        profile=_negative_binomial_profile(),
        actor_id="scientist:alex",
    )
    task.write_text("Use a different governing analysis.\n", encoding="utf-8")
    _write_report(repository)

    with pytest.raises(ValueError, match="governing task file changed"):
        run_audit(
            repository,
            tmp_path / "audit",
            schema_root,
            report="report.md",
            method_contract_lock=contract_output / "semantic.lock.json",
        )


def test_method_contract_cli_creates_a_claimless_resolved_run(tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Estimate observed-over-expected loop strength.\n", encoding="utf-8"
    )
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps(_negative_binomial_profile()), encoding="utf-8")
    output = tmp_path / "contract"

    result = CliRunner().invoke(
        app,
        [
            "method-contract",
            str(repository),
            "--task",
            "task.md",
            "--profile",
            str(profile),
            "--actor-id",
            "scientist:alex",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "resolved" in result.output
    assert "0 Claims, 0 publication surfaces" in result.output
    bundle = json.loads((output / "audit.bundle.json").read_text(encoding="utf-8"))
    assert bundle["claims"] == []
    assert bundle["publication_surfaces"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        "post_lock_model_access",
        "profile_manifest",
        "answer_value",
        "missing_human_declaration",
        "task_scope",
    ],
)
def test_later_binding_rejects_rehashed_parent_authority_mutations(
    schema_root: Path, tmp_path: Path, mutation: str
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Estimate observed-over-expected loop strength.\n", encoding="utf-8"
    )
    parent = tmp_path / "contract"
    run_method_contract(
        repository,
        "task.md",
        parent,
        schema_root,
        profile=_negative_binomial_profile(),
        actor_id="scientist:alex",
    )
    lock = json.loads((parent / "semantic.lock.json").read_text(encoding="utf-8"))
    if mutation == "post_lock_model_access":
        lock["model_access_after_lock"] = True
    elif mutation == "profile_manifest":
        lock["method_contract_profile"]["profile_manifest_digest"] = "sha256:" + "0" * 64
    elif mutation == "answer_value":
        lock["answers"][0]["answer_value"]["control_set"]["background_scope"] = (
            "other_same_stratum_observations"
        )
        answer_input = dict(lock["answers"][0])
        answer_input.pop("answer_digest")
        lock["answers"][0]["answer_digest"] = semantic_digest(answer_input)
    elif mutation == "missing_human_declaration":
        lock["semantic_assertions"] = [
            item
            for item in lock["semantic_assertions"]
            if item["predicate"] != "intended_control_set"
        ]
    elif mutation == "task_scope":
        lock["scientific_contracts"][0]["scope"]["subject_refs"] = [
            {"record_type": "file_record", "record_id": "file:missing"}
        ]
    digest_input = dict(lock)
    digest_input.pop("semantic_lock_digest")
    lock["semantic_lock_digest"] = semantic_digest(digest_input)
    mutated = tmp_path / "mutated.lock.json"
    mutated.write_text(canonical_json(lock) + "\n", encoding="utf-8")
    _write_report(repository)

    with pytest.raises(ValueError):
        run_audit(
            repository,
            tmp_path / "audit",
            schema_root,
            report="report.md",
            method_contract_lock=mutated,
        )
