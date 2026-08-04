from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.prospective_qualification_v2 import (
    ProspectiveQualificationV2Error,
    freeze_case_evidence_contract,
    freeze_stage2_scientific_label,
    validate_case_evidence_contract,
)
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    ProspectiveSelectedResultVerifierError,
    freeze_independent_selected_result_derivation,
    freeze_selected_result_validation,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

CASE_ID = "case:0123456789abcdefabcd"
ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"
DIGEST_A = "sha256:" + "a" * 64
REPORT = b"[selected-result] all,100\n"
PRODUCER = (
    b"from pathlib import Path\n"
    b"table = Path('inputs/map.csv').read_text()\n"
    b"value = table.splitlines()[1]\n"
    b"report = f'[selected-result] {value}\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)
ALTERNATIVE = (
    b"from pathlib import Path\n"
    b"rows = Path('inputs/map.csv').read_text().splitlines()\n"
    b"report = '[selected-result] ' + rows[1] + '\\n'\n"
    b"Path('results/report.md').write_text(report)\n"
)
SOURCE = b"declared-domain,total\nall,100\n"
DIGEST_B = sha256_digest(REPORT)
DIGEST_C = sha256_digest(PRODUCER)
DIGEST_D = sha256_digest(SOURCE)


def _case_spec() -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "envelope": {
            "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
            "check_id": "check:complete-domain-exposure-denominator",
            "candidate_id": "complete-declared-domain-exposure",
            "binding_digest": DIGEST_A,
        },
        "canonical_issue_class": ISSUE_CLASS,
        "selected_result_binding": {
            "binding_profile": "exact_selected_report_result_static_producer_v1",
            "selection_status": "one_selected_result",
            "report_locator": {
                "path": "results/report.md",
                "content_digest": DIGEST_B,
                "start_line": 1,
                "end_line": 1,
            },
            "result_locator": {
                "path": "results/report.md",
                "content_digest": DIGEST_B,
                "start_line": 1,
                "end_line": 1,
            },
            "producer_locator": {
                "path": "workflow/analysis.py",
                "content_digest": DIGEST_C,
                "start_line": 5,
                "end_line": 5,
            },
            "source_operands": [
                {
                    "operand_id": stable_id("operand", "inputs/map.csv", sha256_digest(SOURCE)),
                    "record_ref": {
                        "record_type": "file_record",
                        "record_id": stable_id("file", "inputs/map.csv", sha256_digest(SOURCE)),
                    },
                    "source_locator": {
                        "path": "inputs/map.csv",
                        "content_digest": DIGEST_D,
                        "start_line": 1,
                        "end_line": 2,
                    },
                }
            ],
            "alternative_producer_locators": [],
            "declared_dynamic_selection": False,
        },
        "authorship": {
            "author_id": "actor:prospective-author",
            "provider": "Author Provider",
            "execution_context_id": "context:author-a",
            "identity_evidence_digest": DIGEST_A,
        },
        "authored_at": "2026-08-05T00:00:00Z",
    }


def _digested(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = semantic_digest(result)
    return result


def _review(
    *,
    reviewer_id: str,
    provider: str,
    binding_digest: str,
    label: str = "issue_present",
    issue_class: str | None = ISSUE_CLASS,
    description: str,
) -> dict[str, Any]:
    return _digested(
        {
            "reviewer_id": reviewer_id,
            "provider": provider,
            "completed_at": "2026-08-06T00:00:00Z",
            "scientific_label": label,
            "issue_class_id": issue_class,
            "selected_result_binding_digest": binding_digest,
            "selected_result_binding_status": "verified",
            "finite_counterevidence_status": "complete",
            "bounded_description": description,
        },
        "review_digest",
    )


def _write_verification_case(root: Path, *, include_alternative: bool = False) -> Path:
    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / "workflow").mkdir(exist_ok=True)
    (root / "inputs").mkdir(exist_ok=True)
    (root / "results" / "report.md").write_bytes(REPORT)
    (root / "workflow" / "analysis.py").write_bytes(PRODUCER)
    (root / "inputs" / "map.csv").write_bytes(SOURCE)
    if include_alternative:
        (root / "workflow" / "alternative.py").write_bytes(ALTERNATIVE)
    return root


def _case_root(tmp_path: Path) -> Path:
    return tmp_path / "selected-result-verification"


def _validation(
    contract: dict[str, Any],
    tmp_path: Path,
    *,
    status: str = "verified_complete",
    validator_id: str = "actor:independent-evidence-validator",
    validator_provider: str = "Provider C",
) -> dict[str, Any]:
    include_alternative = status == "ambiguous_selected_result"
    producer = PRODUCER
    if status == "insufficient_evidence":
        producer = (
            b"from pathlib import Path\n"
            b"report = '[selected-result] fixed\\n'\n"
            b"Path('results/report.md').write_text(report)\n"
        )
    elif status == "unsupported_structure":
        producer = (
            b"from pathlib import Path\n"
            b"target = 'results/report.md'\n"
            b"source = Path('inputs/map.csv').read_text()\n"
            b"Path(target).write_text(source)\n"
        )
    root = _write_verification_case(
        _case_root(tmp_path),
        include_alternative=include_alternative,
    )
    (root / "workflow" / "analysis.py").write_bytes(producer)
    if status not in {
        "verified_complete",
        "ambiguous_selected_result",
        "insufficient_evidence",
        "unsupported_structure",
    }:
        raise AssertionError(f"unsupported validation fixture status: {status}")

    derivation = freeze_independent_selected_result_derivation(
        root,
        {
            "case_id": contract["case_id"],
            "validator_identity": {
                "validator_id": validator_id,
                "provider": validator_provider,
                "execution_context_id": "context:selected-result-validator",
                "identity_evidence_digest": "sha256:" + "c" * 64,
            },
            "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
            "selected_report_path": "results/report.md",
            "derived_at": "2026-08-05T22:00:00Z",
        },
        frozen_at="2026-08-05T23:00:00Z",
    )
    return freeze_selected_result_validation(
        root,
        contract,
        derivation,
        declaration_revealed_at="2026-08-05T23:30:00Z",
        compared_at="2026-08-06T01:00:00Z",
    )


def _label_spec(
    contract: dict[str, Any],
    tmp_path: Path,
    *,
    reviews: list[dict[str, Any]] | None = None,
    validation_status: str = "verified_complete",
    validator_id: str = "actor:independent-evidence-validator",
    validator_provider: str = "Provider C",
) -> dict[str, Any]:
    binding_digest = str(contract["selected_result_binding_digest"])
    if reviews is None:
        reviews = [
            _review(
                reviewer_id="actor:stage2-a",
                provider="Provider A",
                binding_digest=binding_digest,
                description="The selected denominator omits declared intervals.",
            ),
            _review(
                reviewer_id="actor:stage2-b",
                provider="Provider B",
                binding_digest=binding_digest,
                description="Exposure uses only the observed subset of the governed domain.",
            ),
        ]
    return {
        "case_id": contract["case_id"],
        "envelope_id": contract["envelope"]["envelope_id"],
        "case_contract_digest": contract["contract_digest"],
        "reviews": reviews,
        "independent_evidence_validation": _validation(
            contract,
            tmp_path,
            status=validation_status,
            validator_id=validator_id,
            validator_provider=validator_provider,
        ),
    }


def test_case_contract_freezes_exact_selected_result_and_replays() -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")

    assert contract["evidence_status"] == "unverified_author_declaration"
    assert contract["qualification_authority"] == "none_case_contract_only"
    assert contract["selected_result_binding_digest"] == semantic_digest(
        contract["selected_result_binding"]
    )
    assert validate_case_evidence_contract(contract) == contract


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("missing_source_operand", "requires source operands"),
        ("dynamic_selection", "Dynamic selected-result paths"),
        ("result_outside_report", "inside the exact selected report"),
        ("result_span_outside_report", "inside the selected report span"),
        ("duplicate_alternative", "must be unique"),
        ("absolute_path", "normalized relative path"),
        ("directory_locator", "normalized relative path"),
        ("future_authorship", "before authorship"),
    ),
)
def test_case_contract_rejects_unusable_selected_result_bindings(
    mutation: str, message: str
) -> None:
    spec = _case_spec()
    if mutation == "missing_source_operand":
        spec["selected_result_binding"]["source_operands"] = []
    elif mutation == "dynamic_selection":
        spec["selected_result_binding"]["declared_dynamic_selection"] = True
    elif mutation == "result_outside_report":
        spec["selected_result_binding"]["result_locator"]["path"] = "other.md"
    elif mutation == "result_span_outside_report":
        spec["selected_result_binding"]["result_locator"]["end_line"] = 2
    elif mutation == "duplicate_alternative":
        producer = deepcopy(spec["selected_result_binding"]["producer_locator"])
        producer["path"] = "workflow/alternative.py"
        spec["selected_result_binding"]["alternative_producer_locators"] = [
            producer,
            deepcopy(producer),
        ]
    elif mutation == "absolute_path":
        spec["selected_result_binding"]["producer_locator"]["path"] = "/tmp/analysis.py"
    elif mutation == "directory_locator":
        spec["selected_result_binding"]["producer_locator"]["path"] = "."
    else:
        spec["authored_at"] = "2026-08-07T00:00:00Z"

    with pytest.raises(ProspectiveQualificationV2Error, match=message):
        freeze_case_evidence_contract(spec, frozen_at="2026-08-05T01:00:00Z")


def test_synonymous_descriptions_resolve_through_canonical_issue_class(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")

    label = freeze_stage2_scientific_label(
        _label_spec(contract, tmp_path),
        case_root=_case_root(tmp_path),
        case_contract=contract,
        frozen_at="2026-08-06T02:00:00Z",
    )

    assert label["scientific_label"] == "issue_present"
    assert label["canonical_issue_class"] == ISSUE_CLASS
    assert label["free_text_used_for_label_resolution"] is False


@pytest.mark.parametrize(
    ("participant", "message"),
    (
        ("author_reviewer_identity", "reviewers must be independent"),
        ("author_reviewer_provider", "reviewers must be independent"),
        ("reviewer_validator_identity", "validator must be independent"),
        ("reviewer_validator_provider", "validator must be independent"),
        ("author_validator_identity", "validator must be independent"),
        ("author_validator_provider", "validator must be independent"),
    ),
)
def test_author_reviewers_and_evidence_validator_are_independent(
    participant: str, message: str, tmp_path: Path
) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    validator_id = "actor:independent-evidence-validator"
    validator_provider = "Provider C"
    if participant == "reviewer_validator_identity":
        validator_id = "actor:stage2-a"
    elif participant == "reviewer_validator_provider":
        validator_provider = "Provider A"
    elif participant == "author_validator_identity":
        validator_id = str(contract["authorship"]["author_id"])
    elif participant == "author_validator_provider":
        validator_provider = str(contract["authorship"]["provider"])
    with pytest.raises(
        (ProspectiveQualificationV2Error, ProspectiveSelectedResultVerifierError), match=message
    ):
        spec = _label_spec(
            contract,
            tmp_path,
            validator_id=validator_id,
            validator_provider=validator_provider,
        )
        if participant == "author_reviewer_identity":
            spec["reviews"][0]["reviewer_id"] = contract["authorship"]["author_id"]
            spec["reviews"][0] = _digested(
                {key: value for key, value in spec["reviews"][0].items() if key != "review_digest"},
                "review_digest",
            )
        elif participant == "author_reviewer_provider":
            spec["reviews"][0]["provider"] = contract["authorship"]["provider"]
            spec["reviews"][0] = _digested(
                {key: value for key, value in spec["reviews"][0].items() if key != "review_digest"},
                "review_digest",
            )
        freeze_stage2_scientific_label(
            spec,
            case_root=_case_root(tmp_path),
            case_contract=contract,
            frozen_at="2026-08-06T02:00:00Z",
        )


def test_issue_class_alias_is_rejected_instead_of_silently_disagreeing(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    binding_digest = str(contract["selected_result_binding_digest"])
    reviews = [
        _review(
            reviewer_id="actor:stage2-a",
            provider="Provider A",
            binding_digest=binding_digest,
            description="First wording.",
        ),
        _review(
            reviewer_id="actor:stage2-b",
            provider="Provider B",
            binding_digest=binding_digest,
            issue_class="issue-class:subset-denominator-alias",
            description="Second wording.",
        ),
    ]

    with pytest.raises(ProspectiveQualificationV2Error, match="frozen canonical"):
        freeze_stage2_scientific_label(
            _label_spec(contract, tmp_path, reviews=reviews),
            case_root=_case_root(tmp_path),
            case_contract=contract,
            frozen_at="2026-08-06T02:00:00Z",
        )


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        ("ambiguous_selected_result", "conditional_or_unknown"),
        ("insufficient_evidence", "insufficient_evidence"),
        ("unsupported_structure", "unsupported"),
    ),
)
def test_incomplete_selected_result_evidence_never_becomes_issue_present(
    status: str, expected: str, tmp_path: Path
) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")

    label = freeze_stage2_scientific_label(
        _label_spec(contract, tmp_path, validation_status=status),
        case_root=_case_root(tmp_path),
        case_contract=contract,
        frozen_at="2026-08-06T02:00:00Z",
    )

    assert label["scientific_label"] == expected
    assert label["canonical_issue_class"] is None


def test_review_disagreement_is_retained_as_disagreement(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    binding_digest = str(contract["selected_result_binding_digest"])
    reviews = [
        _review(
            reviewer_id="actor:stage2-a",
            provider="Provider A",
            binding_digest=binding_digest,
            description="Conflict present.",
        ),
        _review(
            reviewer_id="actor:stage2-b",
            provider="Provider B",
            binding_digest=binding_digest,
            label="issue_absent",
            issue_class=None,
            description="Conflict absent.",
        ),
    ]

    label = freeze_stage2_scientific_label(
        _label_spec(contract, tmp_path, reviews=reviews),
        case_root=_case_root(tmp_path),
        case_contract=contract,
        frozen_at="2026-08-06T02:00:00Z",
    )

    assert label["scientific_label"] == "review_disagreement"
    assert label["canonical_issue_class"] is None


def test_mutated_review_digest_is_rejected(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    spec = _label_spec(contract, tmp_path)
    spec["reviews"][0]["bounded_description"] = "Mutated after review."

    with pytest.raises(ProspectiveQualificationV2Error, match="review digest"):
        freeze_stage2_scientific_label(
            spec,
            case_root=_case_root(tmp_path),
            case_contract=contract,
            frozen_at="2026-08-06T02:00:00Z",
        )


def test_v2_template_binds_ten_current_generic_relations() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "prospective-qualification-v2"
        / "ten-envelope-study.template.json"
    )
    template = json.loads(path.read_text(encoding="utf-8"))
    expected_digest = template.pop("template_digest")
    assert expected_digest == semantic_digest(template)
    template["template_digest"] = expected_digest

    assert template["template_version"] == "2.0.0"
    assert template["minimum_frozen_case_count"] == 140
    assert len(template["envelopes"]) == 10
    assert len({item["canonical_issue_class"] for item in template["envelopes"]}) == 10
    check_ids = {item["check_id"] for item in template["envelopes"]}
    assert "check:complete-domain-exposure-denominator" in check_ids
    assert "check:full-map-ancestry-exposure" not in check_ids

    current = {
        binding.check_id: binding.binding_digest
        for binding in scientific_check_release_registry().method_conflict_bindings
    }
    assert all(
        current[item["check_id"]] == item["binding_digest"] for item in template["envelopes"]
    )
