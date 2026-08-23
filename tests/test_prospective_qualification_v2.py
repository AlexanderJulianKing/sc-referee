from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.prospective_qualification_v2 import (
    ProspectiveQualificationV2Error,
    freeze_author_selected_result_declaration,
    freeze_case_evidence_contract,
    freeze_stage2_scientific_label,
    validate_author_selected_result_declaration,
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
from scripts.build_prospective_qualification_v2_template import build_template

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
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "reference" / "schemas-v0.20.0"
STAGE2_EXAMPLE = SCHEMA_ROOT / "examples" / "agent-review.stage2.example.json"


def _author_declaration_spec() -> dict[str, Any]:
    return {
        "case_id": CASE_ID,
        "declaration_state": "one_selected_result",
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
        "candidate_result_locators": [],
        "unsupported_producer_locators": [],
        "authorship": {
            "author_id": "actor:prospective-author",
            "provider": "Author Provider",
            "execution_context_id": "context:author-a",
            "identity_evidence_digest": DIGEST_A,
        },
        "authored_at": "2026-08-05T00:00:00Z",
    }


def _case_spec(
    author_declaration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    declaration = author_declaration or freeze_author_selected_result_declaration(
        _author_declaration_spec(), frozen_at="2026-08-05T00:30:00Z"
    )
    return {
        "case_id": CASE_ID,
        "envelope": {
            "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
            "check_id": "check:complete-domain-exposure-denominator",
            "candidate_id": "complete-declared-domain-exposure",
            "binding_digest": DIGEST_A,
        },
        "canonical_issue_class": ISSUE_CLASS,
        "author_declaration": declaration,
        "coordinated_at": "2026-08-05T00:45:00Z",
    }


def _digested(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = semantic_digest(result)
    return result


def _review(
    *,
    reviewer_id: str,
    provider: str,
    binding_digest: str | None,
    label: str = "issue_present",
    issue_class: str | None = ISSUE_CLASS,
    description: str,
    execution_context_id: str | None = None,
    binding_status: str | None = None,
) -> dict[str, Any]:
    context = execution_context_id or f"context:{reviewer_id.removeprefix('actor:')}"
    review = json.loads(STAGE2_EXAMPLE.read_text(encoding="utf-8"))
    review["case_id"] = CASE_ID
    review["review_id"] = f"review:{reviewer_id.removeprefix('actor:')}"
    review["reviewer_agent"]["provider"] = provider
    review["reviewer_agent"]["execution_context_id"] = context
    review["completed_at"] = "2026-08-06T00:00:00Z"
    review["bounded_statement"] = description
    review["issue_class"] = issue_class
    review["extensions"] = {
        "x-reviewer-actor-id": reviewer_id,
        "x-selected-result-binding-digest": binding_digest,
        "x-selected-result-binding-status": binding_status
        or ("verified" if binding_digest is not None else "unverified"),
        "x-finite-counterevidence-status": "complete",
    }
    if label == "issue_present":
        review["verdict"] = "demonstrated_issue"
    elif label == "issue_absent":
        review["verdict"] = "no_demonstrated_issue_within_scope"
        review["root_cause"] = None
        review["root_cause_identity"] = None
        review["evidence"] = []
    else:
        raise AssertionError(f"unsupported test review label: {label}")
    return review


def _scientific_panel_freeze(
    contract: dict[str, Any], reviews: list[dict[str, Any]]
) -> dict[str, Any]:
    panel = {
        "evaluation_protocol_version": "0.2.0",
        "record_type": "evaluation_scientific_label_freeze",
        "case_id": contract["case_id"],
        "stage1_freeze_digest": "sha256:" + "1" * 64,
        "stage2_reviews": sorted(
            [
                {
                    "review_ref": {
                        "record_type": "agent_review",
                        "record_id": review["review_id"],
                    },
                    "review_digest": semantic_digest(review),
                    "packet_digest": "sha256:" + "2" * 64,
                    "capture_id": f"capture:{review['review_id']}",
                    "capture_digest": "sha256:" + "3" * 64,
                    "transcript_digest": "sha256:" + "4" * 64,
                    "captured_at": review["completed_at"],
                    "provider": review["reviewer_agent"]["provider"],
                    "execution_context_id": review["reviewer_agent"]["execution_context_id"],
                    "completed_at": review["completed_at"],
                }
                for review in reviews
            ],
            key=lambda item: str(item["review_ref"]["record_id"]),
        ),
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": "adjudication:test",
        },
        "adjudication_digest": "sha256:" + "5" * 64,
        "adjudicated_root_causes": [],
        "label_status": "positive",
        "frozen_at": "2026-08-06T01:30:00Z",
        "detector_output_observed": False,
    }
    return _digested(panel, "freeze_digest")


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
    validator_context: str = "context:selected-result-validator",
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
                "execution_context_id": validator_context,
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
    validator_context: str = "context:selected-result-validator",
    panel_freeze: dict[str, Any] | None = None,
) -> dict[str, Any]:
    binding_digest = contract["selected_result_binding_digest"]
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
        "scientific_panel_freeze": panel_freeze or _scientific_panel_freeze(contract, reviews),
        "full_stage2_reviews": reviews,
        "independent_evidence_validation": _validation(
            contract,
            tmp_path,
            status=validation_status,
            validator_id=validator_id,
            validator_provider=validator_provider,
            validator_context=validator_context,
        ),
    }


def test_case_contract_freezes_exact_selected_result_and_replays() -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")

    assert contract["evidence_status"] == "coordinator_bound_unverified_author_declaration"
    assert contract["qualification_authority"] == "none_case_contract_only"
    assert contract["selected_result_binding_digest"] == semantic_digest(
        contract["selected_result_binding"]
    )
    assert (
        contract["author_declaration_digest"]
        == contract["author_declaration"]["declaration_digest"]
    )
    assert validate_case_evidence_contract(contract) == contract


def test_author_declaration_excludes_coordinator_only_scientific_fields() -> None:
    declaration = freeze_author_selected_result_declaration(
        _author_declaration_spec(), frozen_at="2026-08-05T00:30:00Z"
    )

    assert validate_author_selected_result_declaration(declaration) == declaration
    serialized = json.dumps(declaration, sort_keys=True)
    for hidden_value in (
        "canonical_issue_class",
        "envelope_id",
        "check_id",
        "candidate_id",
        ISSUE_CLASS,
        "check:complete-domain-exposure-denominator",
    ):
        assert hidden_value not in serialized

    leaked = _author_declaration_spec()
    leaked["canonical_issue_class"] = ISSUE_CLASS
    with pytest.raises(ProspectiveQualificationV2Error, match="unexpected fields"):
        freeze_author_selected_result_declaration(leaked, frozen_at="2026-08-05T00:30:00Z")


@pytest.mark.parametrize(
    ("state", "expected_validation", "expected_label"),
    (
        (
            "multiple_candidate_results",
            "ambiguous_selected_result",
            "conditional_or_unknown",
        ),
        ("unsupported_producer_surface", "unsupported_structure", "unsupported"),
    ),
)
def test_nonunique_author_declarations_need_no_fabricated_single_binding(
    state: str, expected_validation: str, expected_label: str, tmp_path: Path
) -> None:
    author_spec = _author_declaration_spec()
    author_spec["declaration_state"] = state
    author_spec["selected_result_binding"] = None
    if state == "multiple_candidate_results":
        first = deepcopy(_author_declaration_spec()["selected_result_binding"]["result_locator"])
        second = deepcopy(first)
        second["path"] = "results/alternative.md"
        second["content_digest"] = "sha256:" + "e" * 64
        author_spec["candidate_result_locators"] = [first, second]
    else:
        author_spec["unsupported_producer_locators"] = [
            deepcopy(_author_declaration_spec()["selected_result_binding"]["producer_locator"])
        ]
    declaration = freeze_author_selected_result_declaration(
        author_spec, frozen_at="2026-08-05T00:30:00Z"
    )
    contract = freeze_case_evidence_contract(
        _case_spec(declaration), frozen_at="2026-08-05T01:00:00Z"
    )

    assert declaration["selected_result_binding"] is None
    assert declaration["selected_result_binding_digest"] is None
    assert contract["selected_result_binding"] is None
    assert contract["selected_result_binding_digest"] is None

    validation = _validation(contract, tmp_path)
    assert validation["status"] == expected_validation
    assert validation["selected_result_binding_digest"] is None
    label = freeze_stage2_scientific_label(
        _label_spec(
            contract,
            tmp_path,
            validation_status=expected_validation,
        ),
        case_root=_case_root(tmp_path),
        case_contract=contract,
        schema_root=SCHEMA_ROOT,
        frozen_at="2026-08-06T02:00:00Z",
    )
    assert label["scientific_label"] == expected_label


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
    author_spec = _author_declaration_spec()
    if mutation == "missing_source_operand":
        author_spec["selected_result_binding"]["source_operands"] = []
    elif mutation == "dynamic_selection":
        author_spec["selected_result_binding"]["declared_dynamic_selection"] = True
    elif mutation == "result_outside_report":
        author_spec["selected_result_binding"]["result_locator"]["path"] = "other.md"
    elif mutation == "result_span_outside_report":
        author_spec["selected_result_binding"]["result_locator"]["end_line"] = 2
    elif mutation == "duplicate_alternative":
        producer = deepcopy(author_spec["selected_result_binding"]["producer_locator"])
        producer["path"] = "workflow/alternative.py"
        author_spec["selected_result_binding"]["alternative_producer_locators"] = [
            producer,
            deepcopy(producer),
        ]
    elif mutation == "absolute_path":
        author_spec["selected_result_binding"]["producer_locator"]["path"] = "/tmp/analysis.py"
    elif mutation == "directory_locator":
        author_spec["selected_result_binding"]["producer_locator"]["path"] = "."
    else:
        author_spec["authored_at"] = "2026-08-07T00:00:00Z"

    with pytest.raises(ProspectiveQualificationV2Error, match=message):
        freeze_author_selected_result_declaration(author_spec, frozen_at="2026-08-05T00:30:00Z")


def test_synonymous_descriptions_resolve_through_canonical_issue_class(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    spec = _label_spec(contract, tmp_path)

    label = freeze_stage2_scientific_label(
        spec,
        case_root=_case_root(tmp_path),
        case_contract=contract,
        schema_root=SCHEMA_ROOT,
        frozen_at="2026-08-06T02:00:00Z",
    )

    assert label["scientific_label"] == "issue_present"
    assert label["canonical_issue_class"] == ISSUE_CLASS
    assert label["free_text_used_for_label_resolution"] is False
    assert (
        label["scientific_panel_freeze_digest"] == spec["scientific_panel_freeze"]["freeze_digest"]
    )


@pytest.mark.parametrize(
    ("participant", "message"),
    (
        ("author_reviewer_identity", "identities and contexts"),
        ("author_reviewer_context", "identities and contexts"),
        ("reviewer_validator_identity", "identity and context"),
        ("reviewer_validator_context", "identity and context"),
        ("author_validator_identity", "identity and context"),
        ("author_validator_context", "identity and context"),
    ),
)
def test_author_reviewers_and_evidence_validator_have_disjoint_identities_and_contexts(
    participant: str, message: str, tmp_path: Path
) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    validator_id = "actor:independent-evidence-validator"
    validator_provider = "Provider C"
    validator_context = "context:selected-result-validator"
    if participant == "reviewer_validator_identity":
        validator_id = "actor:stage2-a"
    elif participant == "reviewer_validator_context":
        validator_context = "context:stage2-a"
    elif participant == "author_validator_identity":
        validator_id = str(contract["authorship"]["author_id"])
    elif participant == "author_validator_context":
        validator_context = str(contract["authorship"]["execution_context_id"])
    with pytest.raises(
        (ProspectiveQualificationV2Error, ProspectiveSelectedResultVerifierError), match=message
    ):
        spec = _label_spec(
            contract,
            tmp_path,
            validator_id=validator_id,
            validator_provider=validator_provider,
            validator_context=validator_context,
        )
        if participant == "author_reviewer_identity":
            spec["full_stage2_reviews"][0]["extensions"]["x-reviewer-actor-id"] = contract[
                "authorship"
            ]["author_id"]
        elif participant == "author_reviewer_context":
            spec["full_stage2_reviews"][0]["reviewer_agent"]["execution_context_id"] = contract[
                "authorship"
            ]["execution_context_id"]
        if participant in {"author_reviewer_identity", "author_reviewer_context"}:
            spec["scientific_panel_freeze"] = _scientific_panel_freeze(
                contract, spec["full_stage2_reviews"]
            )
        freeze_stage2_scientific_label(
            spec,
            case_root=_case_root(tmp_path),
            case_contract=contract,
            schema_root=SCHEMA_ROOT,
            frozen_at="2026-08-06T02:00:00Z",
        )


def test_case_author_and_validator_may_share_stage2_provider_families(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    binding_digest = str(contract["selected_result_binding_digest"])
    reviews = [
        _review(
            reviewer_id="actor:stage2-a",
            provider=str(contract["authorship"]["provider"]),
            binding_digest=binding_digest,
            description="First independent review.",
        ),
        _review(
            reviewer_id="actor:stage2-b",
            provider="Provider B",
            binding_digest=binding_digest,
            description="Second independent review.",
        ),
    ]

    label = freeze_stage2_scientific_label(
        _label_spec(
            contract,
            tmp_path,
            reviews=reviews,
            validator_provider=str(contract["authorship"]["provider"]),
        ),
        case_root=_case_root(tmp_path),
        case_contract=contract,
        schema_root=SCHEMA_ROOT,
        frozen_at="2026-08-06T02:00:00Z",
    )

    assert label["scientific_label"] == "issue_present"


def test_stage2_reviewers_still_require_two_provider_families(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    binding_digest = str(contract["selected_result_binding_digest"])
    reviews = [
        _review(
            reviewer_id="actor:stage2-a",
            provider="Provider A",
            binding_digest=binding_digest,
            description="First review.",
        ),
        _review(
            reviewer_id="actor:stage2-b",
            provider="Provider A",
            binding_digest=binding_digest,
            description="Second review.",
        ),
    ]

    with pytest.raises(ProspectiveQualificationV2Error, match="must use two providers"):
        freeze_stage2_scientific_label(
            _label_spec(contract, tmp_path, reviews=reviews),
            case_root=_case_root(tmp_path),
            case_contract=contract,
            schema_root=SCHEMA_ROOT,
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
            schema_root=SCHEMA_ROOT,
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
        schema_root=SCHEMA_ROOT,
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
        schema_root=SCHEMA_ROOT,
        frozen_at="2026-08-06T02:00:00Z",
    )

    assert label["scientific_label"] == "review_disagreement"
    assert label["canonical_issue_class"] is None


def test_mutated_review_digest_is_rejected(tmp_path: Path) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    spec = _label_spec(contract, tmp_path)
    spec["full_stage2_reviews"][0]["bounded_statement"] = "Mutated after panel freeze."

    with pytest.raises(ProspectiveQualificationV2Error, match="frozen full review"):
        freeze_stage2_scientific_label(
            spec,
            case_root=_case_root(tmp_path),
            case_contract=contract,
            schema_root=SCHEMA_ROOT,
            frozen_at="2026-08-06T02:00:00Z",
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("self_digest", "freeze digest does not replay"),
        ("wrong_case", "case-contract identities differ"),
        ("detector_observed", "precede detector-output observation"),
        ("missing_stage1", "stage1_freeze_digest"),
        ("one_stage2", "exactly two Stage-2"),
        ("one_provider", "must use two providers"),
    ),
)
def test_v2_label_requires_a_complete_pre_detector_4_plus_2_freeze(
    mutation: str, message: str, tmp_path: Path
) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    spec = _label_spec(contract, tmp_path)
    panel = deepcopy(spec["scientific_panel_freeze"])
    panel.pop("freeze_digest")
    if mutation == "self_digest":
        panel["frozen_at"] = "2026-08-06T01:31:00Z"
        panel["freeze_digest"] = spec["scientific_panel_freeze"]["freeze_digest"]
    elif mutation == "wrong_case":
        panel["case_id"] = "case:ffffffffffffffffffff"
        panel = _digested(panel, "freeze_digest")
    elif mutation == "detector_observed":
        panel["detector_output_observed"] = True
        panel = _digested(panel, "freeze_digest")
    elif mutation == "missing_stage1":
        panel["stage1_freeze_digest"] = ""
        panel = _digested(panel, "freeze_digest")
    elif mutation == "one_stage2":
        panel["stage2_reviews"] = panel["stage2_reviews"][:1]
        panel = _digested(panel, "freeze_digest")
    else:
        panel["stage2_reviews"][1]["provider"] = panel["stage2_reviews"][0]["provider"]
        panel = _digested(panel, "freeze_digest")
    spec["scientific_panel_freeze"] = panel

    with pytest.raises(ProspectiveQualificationV2Error, match=message):
        freeze_stage2_scientific_label(
            spec,
            case_root=_case_root(tmp_path),
            case_contract=contract,
            schema_root=SCHEMA_ROOT,
            frozen_at="2026-08-06T02:00:00Z",
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "review_id",
        "review_bytes",
        "provider",
        "context",
        "completed_at",
        "issue_class",
        "binding_status",
    ),
)
def test_v3_label_semantics_are_derived_from_exact_frozen_full_reviews(
    mutation: str, tmp_path: Path
) -> None:
    contract = freeze_case_evidence_contract(_case_spec(), frozen_at="2026-08-05T01:00:00Z")
    spec = _label_spec(contract, tmp_path)
    review = spec["full_stage2_reviews"][0]
    if mutation == "review_id":
        review["review_id"] = "review:different"
    elif mutation == "review_bytes":
        review["bounded_statement"] = "Changed semantic assertion."
    elif mutation == "provider":
        review["reviewer_agent"]["provider"] = "Provider Z"
    elif mutation == "context":
        review["reviewer_agent"]["execution_context_id"] = "context:different"
    elif mutation == "completed_at":
        review["completed_at"] = "2026-08-06T00:01:00Z"
    elif mutation == "issue_class":
        review["issue_class"] = "issue-class:different"
    else:
        review["extensions"]["x-selected-result-binding-status"] = "unverified"

    with pytest.raises(
        ProspectiveQualificationV2Error,
        match=r"exact frozen Stage-2 review set|does not match its frozen full review",
    ):
        freeze_stage2_scientific_label(
            spec,
            case_root=_case_root(tmp_path),
            case_contract=contract,
            schema_root=SCHEMA_ROOT,
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

    assert template == build_template()
    assert template["template_version"] == "3.0.0"
    assert template["template_id"].endswith("-v3")
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
    assert {item["case_evidence_contract_version"] for item in template["envelopes"]} == {"3.0.0"}
