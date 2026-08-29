from __future__ import annotations

import ast
import copy
import json
import runpy
from pathlib import Path
from typing import Any, cast

import pytest

import sc_referee.interaction as interaction_module
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.multiple_testing_scope_attestations_v1 import (
    ATTESTATION_PROFILE,
    ATTESTATION_PROFILE_VERSION,
    CERTAINTY_BASIS,
    CLOSED_ATTESTATION_ERROR_CATEGORIES,
    COMPLETE_OPTION,
    INCOMPLETE_OPTION,
    MAX_ATTESTATION_BYTES,
    UNKNOWN_OPTION,
    MultipleTestingAttestationError,
    apply_attestation,
    load_attestation_file,
    parse_attestation_bytes,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    ScopeQuestionRecords,
    SourceSpan,
    build_scope_question_records,
    existing_complete_coverage_recheck,
    locate_correction_scope_witness,
)

_SCHEMAS = Path("reference/schemas-v0.21.0")
_HARNESS = runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")
_ENVELOPE_INPUTS = cast(Any, _HARNESS["envelope_inputs"])
_ORACLE = json.loads(
    Path("evaluation/development/multitest-code-slice-v3_1/ATTESTATION_ORACLE.json").read_text(
        encoding="utf-8"
    )
)


def test_attestation_error_categories_are_exactly_closed() -> None:
    assert CLOSED_ATTESTATION_ERROR_CATEGORIES == {
        "attestations-file-unavailable",
        "attestations-file-path-unsafe",
        "attestations-file-outside-size-bound",
        "attestations-json-invalid",
        "attestations-schema-invalid",
        "attestations-question-not-open",
        "attestations-answer-cardinality-invalid",
        "attestations-snapshot-binding-mismatch",
        "attestations-analysis-binding-mismatch",
        "attestations-evidence-binding-mismatch",
        "attestations-authority-binding-mismatch",
        "attestations-supersession-invalid",
        "attestations-claimed-correction-invalid",
    }


def test_private_attestation_schema_pins_the_closed_input_surface() -> None:
    schema = json.loads(
        Path(
            "src/sc_referee/resources/input-schemas-v1/"
            "multiple-testing-correction-scope-attestations-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert schema["additionalProperties"] is False
    answers = schema["properties"]["answers"]
    assert (answers["minItems"], answers["maxItems"]) == (1, 1)
    entry = schema["$defs"]["attestation"]
    assert entry["additionalProperties"] is False
    assert set(entry["properties"]["answer"]["enum"]) == {
        INCOMPLETE_OPTION,
        COMPLETE_OPTION,
        UNKNOWN_OPTION,
    }
    factor = schema["$defs"]["claimed_correction"]["properties"]["factor"]
    assert set(factor["properties"]["kind"]["enum"]) == {
        "literal_multiplier",
        "resolved_constant_integer",
        "contract_family_size",
        "correction_input_count",
        "threshold_divisor",
    }


def _opened_records(
    envelope: str, case_id: str, reason: str
) -> tuple[ScopeQuestionRecords, bytes, tuple[str, ...]]:
    case = Path("evaluation/development") / envelope / "cases" / case_id
    inputs = _ENVELOPE_INPUTS(case)
    content = cast(bytes, inputs.pop("content"))
    outcomes = cast(tuple[str, ...], inputs["outcome_columns"])
    witness = locate_correction_scope_witness(
        content,
        qualifying_reason=reason,
        authorized_count=len(outcomes),
        outcome_columns=outcomes,
    )
    assert witness is not None
    return _records(witness), content, outcomes


def _records(witness: Any) -> ScopeQuestionRecords:
    return build_scope_question_records(
        witness,
        run_id="audit:multiple-testing-attestation-test",
        created_at="2026-08-29T00:00:00Z",
        source_snapshot_digest="sha256:" + "1" * 64,
        authority_binding_digest="sha256:" + "2" * 64,
        analysis_ref={"record_type": "file_record", "record_id": "file:analysis"},
        contract_ref={
            "record_type": "scientific_contract",
            "record_id": "scientific-contract:multiple-testing",
        },
        detector_manifest_digest="sha256:" + "3" * 64,
    )


def _manual_complete_records() -> tuple[ScopeQuestionRecords, bytes, tuple[str, ...]]:
    content = (
        b"import scipy.stats\n"
        b"OUTCOMES = ['o1', 'o2', 'o3']\n"
        b"raw_p = []\n"
        b"for col in OUTCOMES:\n"
        b"    p = scipy.stats.ttest_ind(a[col], b[col]).pvalue\n"
        b"    raw_p.append(p)\n"
        b"adjusted_p = [min(1.0, raw_p[i] * len(OUTCOMES)) "
        b"for i in range(len(OUTCOMES))]\n"
        b"print(adjusted_p[0] < 0.05)\n"
        b"print(adjusted_p[1] < 0.05)\n"
        b"print(adjusted_p[2] < 0.05)\n"
    )
    outcomes = ("o1", "o2", "o3")
    witness = locate_correction_scope_witness(
        content,
        qualifying_reason="unresolved-manual-correction-present",
        authorized_count=3,
        outcome_columns=outcomes,
    )
    assert witness is not None
    return _records(witness), content, outcomes


def _attestation_value(
    records: ScopeQuestionRecords,
    *,
    option: str,
    content: bytes,
    claim_span: SourceSpan | None = None,
    factor_value: int | None = None,
    factor_kind: str = "correction_input_count",
    factor_span: SourceSpan | None = None,
) -> dict[str, Any]:
    question = records.question
    extensions = question["extensions"]
    claim: dict[str, Any] | None = None
    if option == COMPLETE_OPTION:
        assert claim_span is not None
        count = int(extensions["x-authorized-count"])
        claim = {
            "path": "analysis.py",
            "analysis_content_digest": sha256_digest(content),
            "source_span": claim_span.to_dict(),
            "factor": {
                "kind": factor_kind,
                "value": factor_value if factor_value is not None else count,
                "source_span": (factor_span or claim_span).to_dict(),
            },
        }
    return {
        "profile": ATTESTATION_PROFILE,
        "profile_version": ATTESTATION_PROFILE_VERSION,
        "answers": [
            {
                "question_id": question["question_id"],
                "source_snapshot_digest": extensions["x-source-snapshot-digest"],
                "analysis_content_digest": extensions["x-analysis-content-digest"],
                "question_evidence_digest": extensions["x-question-evidence-digest"],
                "authority_binding_digest": extensions["x-authority-binding-digest"],
                "answer": option,
                "respondent": {
                    "actor_kind": "human",
                    "actor_id": "human:fixture-author",
                    "display_name": "Fixture Author",
                },
                "certainty": {"level": "explicit", "basis": CERTAINTY_BASIS},
                "timestamp_status": "unavailable",
                "supersedes_answer_digest": None,
                "claimed_correction": claim,
            }
        ],
    }


def _apply(
    records: ScopeQuestionRecords,
    content: bytes,
    outcomes: tuple[str, ...],
    *,
    option: str,
    span: SourceSpan | None = None,
    factor_value: int | None = None,
) -> Any:
    factor_kind = "correction_input_count"
    factor_span = span
    if option == COMPLETE_OPTION and span is not None:
        factor_kind, factor_span = _factor_pointer(content, span)
    value = _attestation_value(
        records,
        option=option,
        content=content,
        claim_span=span,
        factor_value=factor_value,
        factor_kind=factor_kind,
        factor_span=factor_span,
    )
    loaded = parse_attestation_bytes(canonical_json(value).encode())
    return apply_attestation(
        loaded,
        question=records.question,
        initial_concern=records.concern,
        analysis_content=content,
        outcome_columns=outcomes,
        created_at="2026-08-29T00:00:00Z",
    )


def _factor_pointer(content: bytes, correction_span: SourceSpan) -> tuple[str, SourceSpan]:
    text = content.decode("utf-8")
    tree = ast.parse(text)
    roots = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.expr) and _test_span(node, text) == correction_span
    ]
    assert len(roots) == 1
    root = roots[0]
    if isinstance(root, ast.Call):
        terminal = (
            root.func.id
            if isinstance(root.func, ast.Name)
            else root.func.attr
            if isinstance(root.func, ast.Attribute)
            else ""
        )
        if terminal not in {"min", "minimum"}:
            return "correction_input_count", correction_span
    for node in ast.walk(root):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len":
            return "contract_family_size", _test_span(node, text)
    for node in ast.walk(root):
        if isinstance(node, ast.Name):
            bindings = [
                statement.value
                for statement in ast.walk(tree)
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                and statement.value is not None
                and any(
                    isinstance(target, ast.Name) and target.id == node.id
                    for target in (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                )
            ]
            if (
                len(bindings) == 1
                and isinstance(bindings[0], ast.Constant)
                and isinstance(bindings[0].value, int)
                and not isinstance(bindings[0].value, bool)
                and bindings[0].value > 0
            ):
                return "resolved_constant_integer", _test_span(node, text)
            if (
                len(bindings) == 1
                and isinstance(bindings[0], ast.Call)
                and isinstance(bindings[0].func, ast.Name)
                and bindings[0].func.id == "len"
                and len(bindings[0].args) == 1
                and not bindings[0].keywords
            ):
                return "contract_family_size", _test_span(node, text)
    for node in ast.walk(root):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, int)
            and not isinstance(node.value, bool)
            and node.value > 0
        ):
            return "literal_multiplier", _test_span(node, text)
    raise AssertionError("fixture has no closed factor pointer")


def _test_span(node: ast.AST, text: str) -> SourceSpan:
    positioned = cast(Any, node)
    lines = text.splitlines()
    start = lines[positioned.lineno - 1].encode()[: positioned.col_offset]
    end = lines[positioned.end_lineno - 1].encode()[: positioned.end_col_offset]
    return SourceSpan(
        positioned.lineno,
        len(start.decode()) + 1,
        positioned.end_lineno,
        len(end.decode()) + 1,
    )


def _validate_application(application: Any) -> None:
    registry = LocalSchemaRegistry(_SCHEMAS)
    registry.validate(application.question)
    registry.validate(application.answer)
    if application.concern is not None:
        registry.validate(application.concern)
    if application.disclosure is not None:
        registry.validate(application.disclosure)


def test_a_answer_is_visibly_author_attributed_and_never_a_finding() -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-15-2026-08-29",
        "3d2f92807b8138de6463",
        "record-family-mutation-unresolved",
    )
    application = _apply(records, content, outcomes, option=INCOMPLETE_OPTION)
    _validate_application(application)
    assert application.question["status"] == "answered"
    assert application.guided_proof is None
    assert application.disclosure is None
    assert application.concern is not None
    assert application.concern["condition"]["premise_state"] == "unknown"
    assert application.concern["extensions"] == {
        "x-report-label": "Author attestation — not a tool Finding",
        "x-basis": "author_attestation",
        "x-attestation-class": "admission-against-interest",
        "x-author-attested-misstep": True,
        "x-answer-digest": application.answer["answer_digest"],
        "x-analysis-content-digest": application.answer["extensions"]["x-analysis-content-digest"],
        "x-question-evidence-digest": application.answer["extensions"][
            "x-question-evidence-digest"
        ],
        "x-authority-binding-digest": application.answer["extensions"][
            "x-authority-binding-digest"
        ],
    }
    assert "severity" not in application.concern
    assert application.lock_receipt["source_classification_changed"] is False


@pytest.mark.parametrize(
    ("envelope", "case_id", "reason"),
    [
        (
            "blind-envelope-15-2026-08-29",
            "81980e878c1bc8cc216b",
            "unresolved-manual-correction-present",
        ),
        (
            "blind-envelope-13-2026-08-26",
            "b7d38f6e9284abfd3ee6",
            "correction-family-lineage-unresolved",
        ),
    ],
)
def test_a_answer_remains_author_attributed_even_when_source_shape_differs(
    envelope: str, case_id: str, reason: str
) -> None:
    records, content, outcomes = _opened_records(envelope, case_id, reason)
    application = _apply(records, content, outcomes, option=INCOMPLETE_OPTION)
    _validate_application(application)
    assert application.question["status"] == "answered"
    assert application.concern is not None
    assert application.concern["extensions"]["x-report-label"] == (
        "Author attestation — not a tool Finding"
    )
    assert application.concern["condition"]["premise_state"] == "unknown"
    assert application.guided_proof is None
    assert application.disclosure is None
    assert application.lock_receipt["source_classification_changed"] is False


@pytest.mark.parametrize(
    "fixture",
    [
        "answer-b-proves-e13-n1-default-multipletests",
        "answer-b-proves-complete-manual-grammar-control",
    ],
)
def test_b_proves_complete_and_answer_removal_equivalence(fixture: str) -> None:
    if fixture.endswith("default-multipletests"):
        records, content, outcomes = _opened_records(
            "blind-envelope-13-2026-08-26",
            "b7d38f6e9284abfd3ee6",
            "correction-family-lineage-unresolved",
        )
    else:
        records, content, outcomes = _manual_complete_records()
    span = records.witness.source_span
    application = _apply(records, content, outcomes, option=COMPLETE_OPTION, span=span)
    _validate_application(application)
    assert application.guided_proof is not None
    assert application.guided_proof.status == "complete"
    assert application.guided_proof.corrected_positions == tuple(range(len(outcomes)))
    assert application.question["status"] == "answered"
    assert application.concern is None
    assert application.disclosure is None

    answer_removed = existing_complete_coverage_recheck(
        content,
        source_span=span,
        authorized_count=len(outcomes),
        outcome_columns=outcomes,
    )
    assert answer_removed.status == application.guided_proof.status
    assert answer_removed.corrected_positions == application.guided_proof.corrected_positions
    assert answer_removed.proof_digest == application.guided_proof.proof_digest
    assert application.lock_receipt["guided_proof"]["answer_removal_equivalent"] is True


def _synthetic_question(
    source: str, reason: str, outcomes: tuple[str, ...]
) -> tuple[ScopeQuestionRecords, bytes, tuple[str, ...]]:
    content = source.encode()
    witness = locate_correction_scope_witness(
        content,
        qualifying_reason=reason,
        authorized_count=len(outcomes),
        outcome_columns=outcomes,
    )
    assert witness is not None
    return _records(witness), content, outcomes


@pytest.mark.parametrize(
    ("fixture", "builder", "expected_positions"),
    [
        (
            "answer-b-fails-partial-holm-e15-p5",
            lambda: _opened_records(
                "blind-envelope-15-2026-08-29",
                "3d2f92807b8138de6463",
                "record-family-mutation-unresolved",
            ),
            (0, 1),
        ),
        (
            "answer-b-fails-partial-manual-e15-p6",
            lambda: _opened_records(
                "blind-envelope-15-2026-08-29",
                "81980e878c1bc8cc216b",
                "unresolved-manual-correction-present",
            ),
            (),
        ),
        (
            "answer-b-fails-unused-complete-call",
            lambda: _synthetic_question(
                "from statsmodels.stats.multitest import multipletests\n"
                "OUTCOMES = ['o1', 'o2', 'o3']\nraw_p = []\n"
                "for col in OUTCOMES:\n"
                "    p = scipy.stats.ttest_ind(a[col], b[col]).pvalue\n"
                "    raw_p.append(p)\n"
                "reject, adjusted, _, _ = multipletests(raw_p)\n"
                "for p in raw_p:\n    print(p < 0.05)\n",
                "correction-family-lineage-unresolved",
                ("o1", "o2", "o3"),
            ),
            (0, 1, 2),
        ),
        (
            "answer-b-fails-off-registry-complete-call",
            lambda: _synthetic_question(
                "import pingouin\nOUTCOMES = ['o1', 'o2', 'o3']\nraw_p = []\n"
                "for col in OUTCOMES:\n"
                "    p = scipy.stats.ttest_ind(a[col], b[col]).pvalue\n"
                "    raw_p.append(p)\n"
                "reject, adjusted = pingouin.multicomp(raw_p)\n"
                "for p in adjusted:\n    print(p < 0.05)\n",
                "unresolved-manual-correction-present",
                ("o1", "o2", "o3"),
            ),
            (),
        ),
        (
            "answer-b-fails-raw-adjusted-merge",
            lambda: _synthetic_question(
                "from statsmodels.stats.multitest import multipletests\n"
                "OUTCOMES = ['o1', 'o2', 'o3']\nraw_p = []\n"
                "for col in OUTCOMES:\n"
                "    p = scipy.stats.ttest_ind(a[col], b[col]).pvalue\n"
                "    raw_p.append(p)\n"
                "reject, adjusted, _, _ = multipletests(raw_p)\n"
                "used = adjusted[0] if choose_adjusted else raw_p[0]\n"
                "print(used < 0.05)\n",
                "correction-family-lineage-unresolved",
                ("o1", "o2", "o3"),
            ),
            (0, 1, 2),
        ),
        (
            "answer-b-fails-factor-n-but-subset-flow",
            lambda: _synthetic_question(
                "from statsmodels.stats.multitest import multipletests\n"
                "OUTCOMES = ['o1', 'o2', 'o3']\nraw_p = []\n"
                "for col in OUTCOMES:\n"
                "    p = scipy.stats.ttest_ind(a[col], b[col]).pvalue\n"
                "    raw_p.append(p)\n"
                "reject, adjusted, _, _ = multipletests(raw_p[:2])\n"
                "print(adjusted[0] < 0.05)\nprint(adjusted[1] < 0.05)\n",
                "correction-family-lineage-unresolved",
                ("o1", "o2", "o3"),
            ),
            (0, 1),
        ),
    ],
)
def test_b_fails_matrix_stays_open_and_nonaccusatory(
    fixture: str,
    builder: Any,
    expected_positions: tuple[int, ...],
) -> None:
    assert fixture in {row["name"] for row in _ORACLE["rows"]}
    records, content, outcomes = builder()
    application = _apply(
        records,
        content,
        outcomes,
        option=COMPLETE_OPTION,
        span=records.witness.source_span,
    )
    _validate_application(application)
    assert application.guided_proof is not None
    assert application.guided_proof.status == "unverified"
    assert application.guided_proof.corrected_positions == expected_positions
    assert application.question["status"] == "open"
    assert application.concern is not None
    assert application.concern["condition"]["premise_state"] == "conflicted"
    assert application.disclosure is not None
    assert application.disclosure["non_accusatory"] is True
    assert application.lock_receipt["source_classification_changed"] is False


def test_claimed_factor_is_never_a_resolved_value() -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-15-2026-08-29",
        "3d2f92807b8138de6463",
        "record-family-mutation-unresolved",
    )
    proofs = []
    for value in range(1, len(outcomes) + 1):
        application = _apply(
            records,
            content,
            outcomes,
            option=COMPLETE_OPTION,
            span=records.witness.source_span,
            factor_value=value,
        )
        assert application.guided_proof is not None
        proofs.append(
            (
                application.guided_proof.status,
                application.guided_proof.corrected_positions,
                application.guided_proof.proof_digest,
            )
        )
    assert len(set(proofs)) == 1


def test_b_wrong_witness_pointer_stays_open_without_clearance() -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    text = content.decode("utf-8")
    tree = ast.parse(text)
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "len"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "OUTCOMES"
    ]
    assert len(candidates) == 1
    wrong_span = _test_span(candidates[0], text)
    value = _attestation_value(
        records,
        option=COMPLETE_OPTION,
        content=content,
        claim_span=wrong_span,
        factor_kind="contract_family_size",
        factor_span=wrong_span,
    )
    application = apply_attestation(
        parse_attestation_bytes(canonical_json(value).encode()),
        question=records.question,
        initial_concern=records.concern,
        analysis_content=content,
        outcome_columns=outcomes,
        created_at="2026-08-29T00:00:00Z",
    )
    _validate_application(application)
    assert application.guided_proof is not None
    assert application.guided_proof.status == "unverified"
    assert application.guided_proof.corrected_positions == ()
    assert application.question["status"] == "open"
    assert application.concern is not None
    assert application.disclosure is not None
    assert application.disclosure["non_accusatory"] is True
    assert application.lock_receipt["source_classification_changed"] is False


def test_unknown_answer_retains_the_open_question() -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    application = _apply(records, content, outcomes, option=UNKNOWN_OPTION)
    _validate_application(application)
    assert application.question["status"] == "open"
    assert application.concern == records.concern
    assert application.guided_proof is None
    assert application.disclosure is None


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        ("source_snapshot_digest", "attestations-snapshot-binding-mismatch"),
        ("analysis_content_digest", "attestations-analysis-binding-mismatch"),
        ("question_evidence_digest", "attestations-evidence-binding-mismatch"),
        ("authority_binding_digest", "attestations-authority-binding-mismatch"),
        ("question_id", "attestations-question-not-open"),
    ],
)
def test_stale_and_wrong_bindings_refuse_exactly(mutation: str, category: str) -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    value = _attestation_value(records, option=INCOMPLETE_OPTION, content=content)
    value["answers"][0][mutation] = "sha256:" + "f" * 64
    loaded = parse_attestation_bytes(canonical_json(value).encode())
    with pytest.raises(MultipleTestingAttestationError) as caught:
        apply_attestation(
            loaded,
            question=records.question,
            initial_concern=records.concern,
            analysis_content=content,
            outcome_columns=outcomes,
            created_at="2026-08-29T00:00:00Z",
        )
    assert caught.value.category == category


@pytest.mark.parametrize("answers", [[], [{}, {}]])
def test_answer_cardinality_refuses(answers: list[dict[str, Any]]) -> None:
    value = {
        "profile": ATTESTATION_PROFILE,
        "profile_version": ATTESTATION_PROFILE_VERSION,
        "answers": answers,
    }
    with pytest.raises(MultipleTestingAttestationError) as caught:
        parse_attestation_bytes(canonical_json(value).encode())
    assert caught.value.category == "attestations-answer-cardinality-invalid"


def test_attestation_shape_supersession_and_claim_refusals_are_closed() -> None:
    records, content, _outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    base = _attestation_value(records, option=INCOMPLETE_OPTION, content=content)
    variants: list[tuple[dict[str, Any], str]] = []
    extra = copy.deepcopy(base)
    extra["answers"][0]["extra"] = True
    variants.append((extra, "attestations-schema-invalid"))
    superseded = copy.deepcopy(base)
    superseded["answers"][0]["supersedes_answer_digest"] = "sha256:" + "a" * 64
    variants.append((superseded, "attestations-supersession-invalid"))
    missing_claim = copy.deepcopy(base)
    missing_claim["answers"][0]["answer"] = COMPLETE_OPTION
    variants.append((missing_claim, "attestations-schema-invalid"))
    a_claim = _attestation_value(
        records,
        option=COMPLETE_OPTION,
        content=content,
        claim_span=records.witness.source_span,
    )
    a_claim["answers"][0]["answer"] = INCOMPLETE_OPTION
    variants.append((a_claim, "attestations-schema-invalid"))
    for value, category in variants:
        with pytest.raises(MultipleTestingAttestationError) as caught:
            parse_attestation_bytes(canonical_json(value).encode())
        assert caught.value.category == category


def test_available_timestamp_requires_a_real_offset_timestamp() -> None:
    records, content, _outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    value = _attestation_value(records, option=INCOMPLETE_OPTION, content=content)
    value["answers"][0]["timestamp_status"] = "available"
    value["answers"][0]["answered_at"] = "not-a-timestamp"
    with pytest.raises(MultipleTestingAttestationError) as caught:
        parse_attestation_bytes(canonical_json(value).encode())
    assert caught.value.category == "attestations-schema-invalid"


@pytest.mark.parametrize("option", [INCOMPLETE_OPTION, COMPLETE_OPTION])
def test_external_input_path_never_enters_record_bytes(tmp_path: Path, option: str) -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    span = records.witness.source_span if option == COMPLETE_OPTION else None
    factor_kind = "correction_input_count"
    factor_span = span
    value = _attestation_value(
        records,
        option=option,
        content=content,
        claim_span=span,
        factor_kind=factor_kind,
        factor_span=factor_span,
    )
    payload = canonical_json(value).encode()
    project = tmp_path / "project"
    project.mkdir()
    first_path = tmp_path / "first-answer.json"
    second_path = tmp_path / "second-answer.json"
    first_path.write_bytes(payload)
    second_path.write_bytes(payload)
    applications = []
    for path in (first_path, second_path):
        loaded = load_attestation_file(path.resolve(), project_root=project)
        applications.append(
            apply_attestation(
                loaded,
                question=records.question,
                initial_concern=records.concern,
                analysis_content=content,
                outcome_columns=outcomes,
                created_at="2026-08-29T00:00:00Z",
            )
        )
    assert canonical_json(applications[0].question) == canonical_json(applications[1].question)
    assert canonical_json(applications[0].answer) == canonical_json(applications[1].answer)
    assert canonical_json(applications[0].concern) == canonical_json(applications[1].concern)
    assert canonical_json(applications[0].disclosure) == canonical_json(applications[1].disclosure)
    assert canonical_json(applications[0].lock_receipt) == canonical_json(
        applications[1].lock_receipt
    )


def test_human_display_name_cannot_change_guided_proof() -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    base = _attestation_value(
        records,
        option=COMPLETE_OPTION,
        content=content,
        claim_span=records.witness.source_span,
    )
    projections = []
    answer_digests = []
    for display_name in ("First Human", "Holm Bonferroni Report Label"):
        value = copy.deepcopy(base)
        value["answers"][0]["respondent"]["display_name"] = display_name
        application = apply_attestation(
            parse_attestation_bytes(canonical_json(value).encode()),
            question=records.question,
            initial_concern=records.concern,
            analysis_content=content,
            outcome_columns=outcomes,
            created_at="2026-08-29T00:00:00Z",
        )
        assert application.guided_proof is not None
        projections.append(
            (
                application.guided_proof.status,
                application.guided_proof.corrected_positions,
                application.guided_proof.proof_digest,
            )
        )
        answer_digests.append(application.answer["answer_digest"])
    assert len(set(projections)) == 1
    assert len(set(answer_digests)) == 2


def test_claim_span_and_factor_source_mismatches_refuse() -> None:
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    base = _attestation_value(
        records,
        option=COMPLETE_OPTION,
        content=content,
        claim_span=records.witness.source_span,
    )
    bad_span = copy.deepcopy(base)
    bad_span["answers"][0]["claimed_correction"]["source_span"] = {
        "start_line": 9999,
        "start_column": 1,
        "end_line": 9999,
        "end_column": 2,
    }
    mismatch = copy.deepcopy(base)
    mismatch["answers"][0]["claimed_correction"]["factor"]["source_span"] = {
        "start_line": 22,
        "start_column": 9,
        "end_line": 22,
        "end_column": 13,
    }
    for value in (bad_span, mismatch):
        loaded = parse_attestation_bytes(canonical_json(value).encode())
        with pytest.raises(MultipleTestingAttestationError) as caught:
            apply_attestation(
                loaded,
                question=records.question,
                initial_concern=records.concern,
                analysis_content=content,
                outcome_columns=outcomes,
                created_at="2026-08-29T00:00:00Z",
            )
        assert caught.value.category == "attestations-claimed-correction-invalid"


def test_external_file_boundary_refuses_project_file_symlink_and_size(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    value = {
        "profile": ATTESTATION_PROFILE,
        "profile_version": ATTESTATION_PROFILE_VERSION,
        "answers": [],
    }
    project_file = project / "answer.json"
    project_file.write_text(canonical_json(value), encoding="utf-8")
    with pytest.raises(MultipleTestingAttestationError) as project_error:
        load_attestation_file(project_file.resolve(), project_root=project)
    assert project_error.value.category == "attestations-file-path-unsafe"

    external = tmp_path / "external.json"
    external.write_text(canonical_json(value), encoding="utf-8")
    symlink = tmp_path / "answer-link.json"
    symlink.symlink_to(external)
    with pytest.raises(MultipleTestingAttestationError) as symlink_error:
        load_attestation_file(symlink.absolute(), project_root=project)
    assert symlink_error.value.category == "attestations-file-path-unsafe"

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"{" + b" " * MAX_ATTESTATION_BYTES + b"}")
    with pytest.raises(MultipleTestingAttestationError) as size_error:
        load_attestation_file(oversized.resolve(), project_root=project)
    assert size_error.value.category == "attestations-file-outside-size-bound"


@pytest.mark.parametrize(
    "payload",
    [
        b'{"profile":"x","profile":"y"}',
        b'{"profile":NaN}',
        b"\xff",
    ],
)
def test_invalid_json_channels_refuse_deterministically(payload: bytes) -> None:
    with pytest.raises(MultipleTestingAttestationError) as caught:
        parse_attestation_bytes(payload)
    assert caught.value.category == "attestations-json-invalid"


def test_fifteen_attested_rows_replay_byte_identically() -> None:
    assert len(_ORACLE["rows"]) == 15
    records, content, outcomes = _opened_records(
        "blind-envelope-13-2026-08-26",
        "b7d38f6e9284abfd3ee6",
        "correction-family-lineage-unresolved",
    )
    for row in _ORACLE["rows"]:
        route = row["route"]
        if route is None:
            first = canonical_json(records.question)
            second = canonical_json(copy.deepcopy(records.question))
        else:
            span = records.witness.source_span if route == COMPLETE_OPTION else None
            first_application = _apply(records, content, outcomes, option=route, span=span)
            second_application = _apply(records, content, outcomes, option=route, span=span)
            first = canonical_json(
                {
                    "question": first_application.question,
                    "concern": first_application.concern,
                    "answer": first_application.answer,
                    "disclosure": first_application.disclosure,
                    "receipt": first_application.lock_receipt,
                }
            )
            second = canonical_json(
                {
                    "question": second_application.question,
                    "concern": second_application.concern,
                    "answer": second_application.answer,
                    "disclosure": second_application.disclosure,
                    "receipt": second_application.lock_receipt,
                }
            )
        assert first == second, row["name"]


@pytest.mark.parametrize(
    ("function_name", "arguments"),
    [
        (
            "create_candidate_answer",
            ("correction-scope-unknown", "human:fixture-author"),
        ),
        ("create_structured_answer", ({"coverage": "unknown"}, "human:fixture-author")),
        (
            "create_scope_selection_answer",
            (("correction-scope-unknown",), "human:fixture-author"),
        ),
    ],
)
def test_generic_interaction_routes_refuse_scope_question_subtype(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    arguments: tuple[Any, ...],
) -> None:
    question = {
        "question_id": "material-question:multiple-testing-correction-scope:" + "a" * 24,
        "status": "open",
        "extensions": {"x-question-purpose": "multiple_testing_correction_scope"},
    }
    monkeypatch.setattr(
        interaction_module,
        "_load_session",
        lambda *_args, **_kwargs: {
            "parent_bundle": {"material_questions": [question]},
        },
    )
    function = getattr(interaction_module, function_name)
    with pytest.raises(
        interaction_module.InteractionProtocolError,
        match="multiple-testing correction-scope questions require the digest-bound attestations input",
    ):
        function(
            Path("unused-session"),
            question["question_id"],
            *arguments,
            _SCHEMAS,
        )
