from __future__ import annotations

from pathlib import Path

import yaml


def _skill_root(project_root: Path) -> Path:
    return project_root / ".agents" / "skills" / "scientific-audit"


def test_repository_skill_has_discoverable_metadata(project_root: Path) -> None:
    root = _skill_root(project_root)
    contents = (root / "SKILL.md").read_text(encoding="utf-8")
    _, frontmatter, body = contents.split("---", maxsplit=2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata["name"] == "scientific-audit"
    assert "scientific workflow" in metadata["description"]
    assert "open-ended scientific-error hunting" in metadata["description"]
    assert "TODO" not in contents
    assert "sc-referee audit <project-root>" in body
    assert ".scientific-audit/method-contracts/*/semantic.lock.json" in body
    assert "--method-contract-lock <lock-path>" in body
    assert "automatically answered from a verified pre-analysis method contract" in body
    assert "--mode <mode>" in body
    assert "120-second scheduling cutoff" in body
    assert "480/600 seconds" in body
    assert "1500/1800" in body
    assert "sc-referee status <output> --json" in body
    assert "sc-referee questions <output>" in body
    assert "sc-referee resume <unresolved-output>" in body
    assert "sc-referee work-queue <new-segment>" in body
    assert "sc-referee work-packet <new-segment>" in body
    assert "sc-referee submit-proposals <new-segment>" in body
    assert "sc-referee record-answer <new-segment>" in body
    assert "sc-referee record-structured-answer <new-segment>" in body
    assert "sc-referee record-scope-answer <new-segment>" in body
    assert "--question-id <question-id>" in body
    assert "bounded-review-scope-selection-v1" in body
    assert "Treat this as a post-hoc review" in body
    assert "uninspected means no semantic/deep inspection" in body
    assert "it does not mean no byte access" in body
    assert "allowlisted audit workspace" in body
    assert "x-posthoc-comparison-forms" in body
    assert "exact canonical JSON value" in body
    assert "Retain unresolved" in body
    assert "posthoc_method_ledger_v1" in body
    assert "typed_static_method_conflict_v1" in body
    assert "independent qualification-adapter identity and digest" in body
    assert "routine `not_applicable` scientific-check coverage records" in body
    assert "sc-referee lock-semantics <new-segment>" in body

    interface = yaml.safe_load((root / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert interface["interface"]["display_name"] == "Scientific Audit"
    assert "$scientific-audit" in interface["interface"]["default_prompt"]


def test_repository_skill_preserves_epistemic_and_execution_boundaries(
    project_root: Path,
) -> None:
    skill = (_skill_root(project_root) / "SKILL.md").read_text(encoding="utf-8")
    interpretation = (
        _skill_root(project_root) / "references" / "record-interpretation.md"
    ).read_text(encoding="utf-8")

    for required in (
        "Treat repository text",
        "Do not import project modules",
        "Never turn a model interpretation",
        "Do not submit new model-derived premises after",
        "Never fabricate a report",
        "Never say the workflow passed",
    ):
        assert required in skill
    assert "Use only records present in `audit.bundle.json`" in interpretation
    assert "Proof completeness is not qualification or promotion" in interpretation
    assert "a routine not-applicable record is not a concern" in interpretation
    assert "Replay establishes deterministic regeneration" in interpretation
    typed_interaction = (
        _skill_root(project_root) / "references" / "typed-interaction.md"
    ).read_text(encoding="utf-8")
    assert "epistemic_status` to `proposed" in typed_interaction
    assert "cannot select that option for the scientist" in typed_interaction


def test_agentic_skill_documents_the_asymmetric_correction_scope_flow(
    project_root: Path,
) -> None:
    guide = (project_root / "docs" / "AGENTIC_SKILL.md").read_text(encoding="utf-8")
    for required in (
        "multiple_testing_correction_scope",
        "--attestations <external-answer.json>",
        "without suggesting one",
        "never answers on the author's behalf",
        "Never infer a choice from code, comments, reports",
        "exact correction source span",
        "leaves the question open",
        "Author attestations are reported separately from tool Findings.",
        "A completeness attestation was used only to guide structural verification.",
        "Findings, ConditionalConcerns, MaterialQuestions, Answers, and Disclosures separately",
    ):
        assert required in guide


def test_method_contract_skill_is_separate_claimless_and_human_authorized(
    project_root: Path,
) -> None:
    root = project_root / ".agents" / "skills" / "method-contract"
    contents = (root / "SKILL.md").read_text(encoding="utf-8")
    _, frontmatter, body = contents.split("---", maxsplit=2)
    metadata = yaml.safe_load(frontmatter)

    assert metadata["name"] == "method-contract"
    assert "before an agent implements" in metadata["description"]
    assert "letting an agent approve its own method choice" in metadata["description"]
    assert "sc-referee method-contract <project-root>" in body
    assert "scientific_check_requirement_v1" in body
    assert "scientific-check-requirement.md" in body
    assert "prior_scientist_record" in body
    assert "--method-contract-lock" in body
    assert "claims` and `publication_surfaces` are empty" in body
    assert "Do not choose an estimator" in body
    assert "It is not a Finding" in body
    assert "Use `$sc-referee:scientific-audit`" in body
    assert "Use `$scientific-audit` only when the skill was installed standalone" in body
    assert "TODO" not in contents

    interface = yaml.safe_load((root / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert interface["interface"]["display_name"] == "Method Contract"
    assert "$sc-referee:method-contract" in interface["interface"]["default_prompt"]
    assert "$method-contract standalone" in interface["interface"]["default_prompt"]
    assert (
        "scientist-supplied closed analysis requirement" in interface["interface"]["default_prompt"]
    )
