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
