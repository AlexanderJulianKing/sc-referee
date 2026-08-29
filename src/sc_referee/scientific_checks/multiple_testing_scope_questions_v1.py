"""Closed multiple-testing correction-scope question layer.

This module consumes the already-frozen 3.0 first abstention and never changes that source
classification.  It reads Python AST structure, exact API identities, contract columns, source
coordinates, and digests only.  Comments, docstrings, report text, and identifier prose do not
enter its wording or evidence decisions.
"""

from __future__ import annotations

import ast
import copy
import json
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.observed import controller_provenance
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_1 import (
    CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS,
    MULTIPLE_TESTING_CODE_ADAPTER_ID,
    MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
    MULTIPLE_TESTING_CODE_CHECK_ID,
    MULTIPLE_TESTING_CODE_CHECK_VERSION,
)
from sc_referee.version import SCHEMA_VERSION, __version__

QUESTION_PROFILE_ID = "material-question:multiple-testing-correction-scope-v1"
QUESTION_PROFILE_VERSION = "1.0.0"
DETECTOR_ID = "detector:bounded-code-csv-multiple-testing-conflict"
DETECTOR_VERSION = "3.1.0"
GRAMMAR_ID = "bounded-code-csv-multiple-testing-conflict-v1"
GRAMMAR_VERSION = "3.1.0"
QUESTION_PURPOSE = "multiple_testing_correction_scope"

QUALIFYING_REASON_NAMES = frozenset(
    {
        "correction-family-lineage-unresolved",
        "record-family-lineage-unresolved",
        "record-family-mutation-unresolved",
        "unresolved-decision-threshold",
        "unresolved-manual-correction-present",
    }
)
NONQUALIFYING_REASON_NAMES = CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS - QUALIFYING_REASON_NAMES
REASON_QUESTION_CLASS = {
    reason: (
        "correction_scope_witness_required"
        if reason in QUALIFYING_REASON_NAMES
        else "not_correction_scope_question"
    )
    for reason in sorted(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS)
}
if len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) != 61 or len(NONQUALIFYING_REASON_NAMES) != 56:
    raise RuntimeError("multiple-testing correction-scope reason registry drifted")
if set(REASON_QUESTION_CLASS) != CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS:
    raise RuntimeError("multiple-testing question reason classification is incomplete")

_REGISTERED_TEST_APIS = frozenset({"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"})
_REGISTERED_CORRECTION_APIS = frozenset(
    {
        "statsmodels.stats.multitest.multipletests",
        "statsmodels.stats.multitest.fdrcorrection",
        "scipy.stats.false_discovery_control",
        "sc_referee.calculation_checks.bh.benjamini_hochberg",
    }
)
_CORRECTION_TERMINALS = frozenset(
    {
        "multipletests",
        "fdrcorrection",
        "false_discovery_control",
        "multicomp",
        "fdr_correction",
        "p_adjust",
        "padjust",
        "bonferroni",
        "holm",
        "sidak",
    }
)
_ALPHAS = frozenset({Decimal("0.01"), Decimal("0.05"), Decimal("0.1")})
_MAX_BYTES = 1 << 20
_MAX_NODES = 50_000
_MAX_RESOLUTION_DEPTH = 16
_WITNESS_RANK = {
    "record-correction-store": 0,
    "manual-adjusted-p-arithmetic": 1,
    "registered-correction-call": 2,
    "closed-terminal-correction-call": 3,
    "manual-decision-threshold-arithmetic": 4,
}


class CorrectionScopeQuestionError(ValueError):
    """Raised when a question-layer value escapes its closed profile."""


@dataclass(frozen=True, order=True)
class SourceSpan:
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __post_init__(self) -> None:
        if (
            self.start_line < 1
            or self.start_column < 1
            or self.end_line < self.start_line
            or self.end_column < 1
            or (self.end_line == self.start_line and self.end_column <= self.start_column)
        ):
            raise CorrectionScopeQuestionError("correction-scope source span is invalid")

    def to_dict(self) -> dict[str, int]:
        return {
            "start_line": self.start_line,
            "start_column": self.start_column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }


WitnessKind = Literal[
    "registered-correction-call",
    "closed-terminal-correction-call",
    "manual-adjusted-p-arithmetic",
    "manual-decision-threshold-arithmetic",
    "record-correction-store",
]


@dataclass(frozen=True)
class CorrectionScopeWitness:
    witness_kind: WitnessKind
    qualifying_reason: str
    analysis_path: str
    analysis_content_digest: str
    source_span: SourceSpan
    source_span_digest: str
    authorized_count: int
    family_position_origins: tuple[int, ...]
    correction_input_positions: tuple[int, ...]
    threshold_operator: str | None
    factor_kind: str | None
    factor_value: int | None
    callee_identity: str | None
    association_digest: str

    def __post_init__(self) -> None:
        valid_positions = set(range(self.authorized_count))
        if (
            self.witness_kind not in _WITNESS_RANK
            or self.qualifying_reason not in QUALIFYING_REASON_NAMES
            or self.analysis_path != "analysis.py"
            or not self.analysis_content_digest.startswith("sha256:")
            or not self.source_span_digest.startswith("sha256:")
            or not self.association_digest.startswith("sha256:")
            or self.authorized_count < 3
            or self.family_position_origins != tuple(sorted(set(self.family_position_origins)))
            or self.correction_input_positions
            != tuple(sorted(set(self.correction_input_positions)))
            or not set(self.family_position_origins).issubset(valid_positions)
            or not set(self.correction_input_positions).issubset(valid_positions)
            or self.threshold_operator not in {None, "<", "<=", ">", ">="}
            or (self.factor_kind is None) != (self.factor_value is None)
            or (self.factor_value is not None and self.factor_value < 1)
        ):
            raise CorrectionScopeQuestionError("correction-scope witness is outside the profile")

    def to_dict(self) -> dict[str, Any]:
        return {
            "witness_kind": self.witness_kind,
            "qualifying_reason": self.qualifying_reason,
            "analysis_path": self.analysis_path,
            "analysis_content_digest": self.analysis_content_digest,
            "source_span": self.source_span.to_dict(),
            "source_span_digest": self.source_span_digest,
            "authorized_count": self.authorized_count,
            "family_position_origins": list(self.family_position_origins),
            "correction_input_positions": list(self.correction_input_positions),
            "threshold_operator": self.threshold_operator,
            "factor_kind": self.factor_kind,
            "factor_value": self.factor_value,
            "callee_identity": self.callee_identity,
            "association_digest": self.association_digest,
        }


@dataclass(frozen=True)
class ScopeQuestionRecords:
    detector_result: dict[str, Any]
    question: dict[str, Any]
    concern: dict[str, Any]
    witness: CorrectionScopeWitness


@dataclass(frozen=True)
class GuidedCoverageProof:
    status: Literal["complete", "unverified"]
    corrected_positions: tuple[int, ...]
    proof_root_span: SourceSpan
    proof_digest: str
    failure_code: str | None


@dataclass(frozen=True)
class _Candidate:
    kind: WitnessKind
    node: ast.expr
    callee: str | None = None
    threshold_operator: str | None = None
    factor_kind: str | None = None
    factor_value: int | None = None
    input_positions: tuple[int, ...] = ()
    origin_positions: tuple[int, ...] = ()


@dataclass
class _AstFacts:
    content: bytes
    text: str
    tree: ast.Module
    imports: dict[str, str]
    binding_counts: Counter[str]
    assignments: dict[str, ast.expr]
    functions: dict[str, ast.FunctionDef]
    p_names: set[str]
    p_containers: set[str]
    record_names: set[str]
    record_collections: set[str]
    p_tables: set[str]
    test_results: set[str]
    outcome_columns: tuple[str, ...]

    def qualified(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return self.imports.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            parent = self.qualified(node.value)
            return f"{parent}.{node.attr}" if parent else None
        return None


def question_wording_profile() -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[1]
        / "resources"
        / "multiple-testing-question-profiles-v1"
        / "correction-scope-v1.json"
    )
    value = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    expected = value.pop("semantic_digest", None)
    actual = semantic_digest(value)
    if (
        expected != actual
        or value.get("profile_id") != QUESTION_PROFILE_ID
        or value.get("profile_version") != QUESTION_PROFILE_VERSION
        or value.get("slots") != ["AUTHORIZED_COUNT", "SOURCE_LOCATION"]
        or value.get("source_text_allowed") is not False
    ):
        raise RuntimeError("multiple-testing question wording profile drifted")
    value["semantic_digest"] = actual
    return value


QUESTION_PROFILE_SEMANTIC_DIGEST = cast(str, question_wording_profile()["semantic_digest"])


def locate_correction_scope_witness(
    content: bytes,
    *,
    qualifying_reason: str,
    authorized_count: int,
    outcome_columns: tuple[str, ...],
) -> CorrectionScopeWitness | None:
    """Return exactly one closed correction witness or conservatively return ``None``."""

    if (
        REASON_QUESTION_CLASS.get(qualifying_reason) != "correction_scope_witness_required"
        or authorized_count < 3
    ):
        return None
    try:
        facts = _ast_facts(content, outcome_columns)
    except (SyntaxError, UnicodeError, ValueError):
        return None
    candidates = _correction_call_candidates(facts, authorized_count)
    candidates.extend(_manual_adjustment_candidates(facts, authorized_count))
    candidates.extend(_manual_threshold_candidates(facts, authorized_count))
    if qualifying_reason in {
        "record-family-lineage-unresolved",
        "record-family-mutation-unresolved",
    }:
        candidates = [
            _Candidate(
                "record-correction-store",
                item.node,
                item.callee,
                item.threshold_operator,
                item.factor_kind,
                item.factor_value,
                item.input_positions,
                item.origin_positions,
            )
            for item in candidates
            if item.kind
            in {
                "registered-correction-call",
                "closed-terminal-correction-call",
                "manual-adjusted-p-arithmetic",
            }
            and _candidate_feeds_record_store(item, facts)
        ]
    if qualifying_reason == "unresolved-decision-threshold":
        candidates = [
            item for item in candidates if item.kind == "manual-decision-threshold-arithmetic"
        ]
    if qualifying_reason == "correction-family-lineage-unresolved":
        candidates = [
            item
            for item in candidates
            if item.kind in {"registered-correction-call", "closed-terminal-correction-call"}
        ]

    # The source occurrence, not a helper/loop clone, is the correction identity.
    canonical: dict[tuple[Any, ...], _Candidate] = {}
    for item in candidates:
        span = _node_span(facts, item.node)
        structure = ast.dump(item.node, annotate_fields=True, include_attributes=False)
        key = (span, item.kind, structure, item.callee)
        previous = canonical.get(key)
        if previous is None:
            canonical[key] = item
        else:
            canonical[key] = _Candidate(
                item.kind,
                item.node,
                item.callee,
                item.threshold_operator,
                item.factor_kind,
                item.factor_value,
                tuple(sorted(set(previous.input_positions) | set(item.input_positions))),
                tuple(sorted(set(previous.origin_positions) | set(item.origin_positions))),
            )

    # Dominance coalesces nested descriptors for one outer occurrence.
    dominated: list[_Candidate] = []
    for item in sorted(
        canonical.values(),
        key=lambda value: (_WITNESS_RANK[value.kind], _node_span(facts, value.node)),
    ):
        item_span = _node_span(facts, item.node)
        if any(
            _span_contains(_node_span(facts, prior.node), item_span)
            or _span_contains(item_span, _node_span(facts, prior.node))
            for prior in dominated
        ):
            continue
        dominated.append(item)
    if len(dominated) != 1:
        return None
    candidate = dominated[0]
    span = _node_span(facts, candidate.node)
    selected = _source_bytes(facts, candidate.node)
    span_digest = sha256_digest(selected)
    association = {
        "witness_kind": candidate.kind,
        "source_span": span.to_dict(),
        "structure": ast.dump(candidate.node, annotate_fields=True, include_attributes=False),
        "family_position_origins": list(candidate.origin_positions),
        "correction_input_positions": list(candidate.input_positions),
        "callee_identity": candidate.callee,
    }
    return CorrectionScopeWitness(
        witness_kind=candidate.kind,
        qualifying_reason=qualifying_reason,
        analysis_path="analysis.py",
        analysis_content_digest=sha256_digest(content),
        source_span=span,
        source_span_digest=span_digest,
        authorized_count=authorized_count,
        family_position_origins=candidate.origin_positions,
        correction_input_positions=candidate.input_positions,
        threshold_operator=candidate.threshold_operator,
        factor_kind=candidate.factor_kind,
        factor_value=candidate.factor_value,
        callee_identity=candidate.callee,
        association_digest=semantic_digest(association),
    )


def build_scope_question_records(
    witness: CorrectionScopeWitness,
    *,
    run_id: str,
    created_at: str,
    source_snapshot_digest: str,
    authority_binding_digest: str,
    analysis_ref: dict[str, str],
    contract_ref: dict[str, str],
    detector_manifest_digest: str,
) -> ScopeQuestionRecords:
    """Construct one schema-compatible question, concern, and question-candidate result."""

    identities = {
        "profile": QUESTION_PROFILE_ID,
        "profile_version": QUESTION_PROFILE_VERSION,
        "question_profile_semantic_digest": QUESTION_PROFILE_SEMANTIC_DIGEST,
        "check_id": MULTIPLE_TESTING_CODE_CHECK_ID,
        "check_version": MULTIPLE_TESTING_CODE_CHECK_VERSION,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "adapter_id": MULTIPLE_TESTING_CODE_ADAPTER_ID,
        "adapter_version": MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        "grammar_id": GRAMMAR_ID,
        "grammar_version": GRAMMAR_VERSION,
        "source_snapshot_digest": source_snapshot_digest,
        "analysis_content_digest": witness.analysis_content_digest,
        "authority_binding_digest": authority_binding_digest,
        "qualifying_reason": witness.qualifying_reason,
        "authorized_count": witness.authorized_count,
        "witness_kind": witness.witness_kind,
        "source_span": witness.source_span.to_dict(),
        "source_span_digest": witness.source_span_digest,
        "association_digest": witness.association_digest,
    }
    identity_digest = semantic_digest(identities)
    question_id = f"material-question:multiple-testing-correction-scope:{identity_digest[7:31]}"
    evidence_projection = {
        "witness": witness.to_dict(),
        "identities": {
            key: identities[key]
            for key in (
                "check_id",
                "check_version",
                "detector_id",
                "detector_version",
                "adapter_id",
                "adapter_version",
                "grammar_id",
                "grammar_version",
            )
        },
        "question_profile_semantic_digest": QUESTION_PROFILE_SEMANTIC_DIGEST,
    }
    question_evidence_digest = semantic_digest(evidence_projection)
    concern_digest = semantic_digest(
        {"domain": "multiple-testing-correction-scope-open-concern", "question_id": question_id}
    )
    result_digest = semantic_digest(
        {"domain": "multiple-testing-correction-scope-result", "identity": identities}
    )
    premise_digest = semantic_digest(
        {"domain": "multiple-testing-correction-scope-premise", "identity": identities}
    )
    evidence_digest = semantic_digest(
        {"domain": "multiple-testing-correction-scope-evidence", "identity": identities}
    )
    concern_id = f"conditional-concern:multiple-testing-correction-scope:{concern_digest[7:31]}"
    result_id = f"detector-result:multiple-testing-correction-scope:{result_digest[7:31]}"
    location = f"analysis.py:{witness.source_span.start_line}:{witness.source_span.start_column}"
    source_ref = {
        "source_kind": "file_span",
        "locator": location,
        "path": "analysis.py",
        "content_digest": witness.analysis_content_digest,
        **witness.source_span.to_dict(),
    }
    evidence_id = f"evidence:multiple-testing-correction-scope:{evidence_digest[7:31]}"
    premise_id = f"premise:multiple-testing-correction-scope:{premise_digest[7:31]}"
    detector_result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "detector_result",
        "result_id": result_id,
        "audit_run_id": run_id,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "detector_manifest_digest": detector_manifest_digest,
        "detector_maturity": "experimental",
        "target_refs": [copy.deepcopy(analysis_ref), copy.deepcopy(contract_ref)],
        "state": "material_question_candidate",
        "evaluated_at": created_at,
        "runtime_mode": "static",
        "deterministic_input_digest": semantic_digest(evidence_projection),
        "applicability": {
            "status": "uncertain",
            "basis": "A local correction occurrence is structurally located; complete-family scope remains unresolved.",
            "unsupported_constructs": [witness.qualifying_reason],
        },
        "premise_evaluations": [
            {
                "premise_id": premise_id,
                "statement": "The located correction covers all declared outcomes.",
                "state": "unknown",
                "material": True,
                "evidence_ids": [evidence_id],
            }
        ],
        "evidence": [
            {
                "evidence_id": evidence_id,
                "description": "A bounded correction-related AST occurrence was located at the recorded source span.",
                "support_role": "context",
                "source_refs": [source_ref],
                "record_refs": [copy.deepcopy(contract_ref)],
                "observed_value": {
                    "authorized_count": witness.authorized_count,
                    "source_span": witness.source_span.to_dict(),
                },
            }
        ],
        "counterevidence_execution": [
            {
                "check_id": "check:complete-family-correction-scope",
                "status": "unavailable",
                "outcome": "inconclusive",
                "evidence_ids": [evidence_id],
            }
        ],
        "coverage": {
            "status": "unknown",
            "basis": "The correction occurrence is located, but its complete-family position coverage is unresolved.",
            "gaps": ["Complete-family correction-position equality is unresolved."],
        },
        "unavailable_evidence": ["A complete structural correction-position proof."],
        "candidate": {
            "assessment_type": "material_question",
            "title": "Correction scope requires clarification",
            "bounded_statement": "Static analysis located correction-related computation but did not establish complete-family coverage.",
            "material_premise_ids": [premise_id],
            "unresolved_material_premise_ids": [premise_id],
        },
        "provenance": {
            "actor": {"actor_kind": "detector", "actor_id": DETECTOR_ID},
            "method": "deterministic_detection",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-question-purpose": QUESTION_PURPOSE,
            "x-question-evidence-digest": question_evidence_digest,
            "x-source-result-unchanged": True,
        },
    }
    question = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": (
            f"Does this correction cover all {witness.authorized_count} declared outcomes?"
        ),
        "unknown_semantic_dimension": QUESTION_PURPOSE,
        "why_it_matters": (
            f"Static analysis located correction-related computation at {location}, but could "
            f"not prove whether it covers all {witness.authorized_count} outcomes in the "
            "declared family. The answer can change how this unresolved case is recorded; it "
            "cannot create a tool Finding by itself."
        ),
        "candidate_answers": [
            {
                "answer_id": "correction-scope-incomplete",
                "label": "No — it does not cover all declared outcomes",
                "value": {"coverage": "incomplete"},
                "consequence": "Records an author attestation of incomplete scope as a non-Finding conditional concern.",
            },
            {
                "answer_id": "correction-scope-complete",
                "label": "Yes — it covers all declared outcomes",
                "value": {"coverage": "complete"},
                "consequence": "Guides a structural recheck; the claim alone cannot establish complete coverage.",
            },
            {
                "answer_id": "correction-scope-unknown",
                "label": "Unknown",
                "value": {"coverage": "unknown"},
                "consequence": "Leaves the question open.",
            },
        ],
        "evidence_searched": [
            {
                "source": location,
                "result": (
                    "A closed correction occurrence was located; complete-family coverage "
                    "remains unresolved."
                ),
            }
        ],
        "blocked_detector_ids": [DETECTOR_ID],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [concern_id],
        "priority": "high",
        "status": "open",
        "answer_ids": [],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_multiple_testing_scope_question_v1", created_at
        ),
        "extensions": {
            "x-question-purpose": QUESTION_PURPOSE,
            "x-question-profile-id": QUESTION_PROFILE_ID,
            "x-question-profile-version": QUESTION_PROFILE_VERSION,
            "x-check-id": MULTIPLE_TESTING_CODE_CHECK_ID,
            "x-check-version": MULTIPLE_TESTING_CODE_CHECK_VERSION,
            "x-detector-id": DETECTOR_ID,
            "x-detector-version": DETECTOR_VERSION,
            "x-qualifying-reason": witness.qualifying_reason,
            "x-authorized-count": witness.authorized_count,
            "x-witness-kind": witness.witness_kind,
            "x-source-span": witness.source_span.to_dict(),
            "x-source-span-digest": witness.source_span_digest,
            "x-analysis-content-digest": witness.analysis_content_digest,
            "x-authority-binding-digest": authority_binding_digest,
            "x-question-evidence-digest": question_evidence_digest,
            "x-source-snapshot-digest": source_snapshot_digest,
            "x-analysis-subject-ref": copy.deepcopy(analysis_ref),
            "x-contract-ref": copy.deepcopy(contract_ref),
            "x-detector-result-id": result_id,
        },
    }
    concern = _open_concern(
        question=question,
        result_id=result_id,
        analysis_ref=analysis_ref,
        contract_ref=contract_ref,
        created_at=created_at,
        location=location,
    )
    return ScopeQuestionRecords(detector_result, question, concern, witness)


def existing_complete_coverage_recheck(
    content: bytes,
    *,
    source_span: SourceSpan,
    authorized_count: int,
    outcome_columns: tuple[str, ...],
) -> GuidedCoverageProof:
    """Run the answer-independent, existing-grammar proof at one already-known AST node.

    The caller may use an answer only to select ``source_span``.  This function accepts no answer,
    factor claim, method name, or claimed positions, which makes answer-removal equivalence
    structural rather than conventional.
    """

    facts = _ast_facts(content, outcome_columns)
    nodes = [
        node
        for node in ast.walk(facts.tree)
        if isinstance(node, ast.expr) and _node_span(facts, node) == source_span
    ]
    if len(nodes) != 1:
        return _unverified_proof(source_span, "guided-proof-root-unavailable")
    root = nodes[0]
    if not isinstance(root, ast.Call):
        return _manual_complete_coverage_recheck(
            root,
            facts=facts,
            source_span=source_span,
            authorized_count=authorized_count,
        )
    call = root
    api = facts.qualified(call.func)
    if api not in _REGISTERED_CORRECTION_APIS:
        manual = _match_manual_adjustment(call, facts, authorized_count)
        if manual is not None:
            return _manual_complete_coverage_recheck(
                call,
                facts=facts,
                source_span=source_span,
                authorized_count=authorized_count,
            )
        return _unverified_proof(source_span, "guided-proof-api-unrecognized")
    argument = _correction_input(call, api)
    if argument is None:
        return _unverified_proof(source_span, "guided-proof-input-unresolved")
    positions = _container_positions(argument, facts, authorized_count)
    if positions != tuple(range(authorized_count)):
        return GuidedCoverageProof(
            "unverified",
            positions,
            source_span,
            semantic_digest(
                {
                    "root": source_span.to_dict(),
                    "api": api,
                    "positions": list(positions),
                    "status": "unverified",
                }
            ),
            "guided-proof-family-incomplete",
        )
    if not _correction_outputs_reach_all_conclusions(
        call, facts, authorized_count
    ) or _raw_p_directly_reaches_a_conclusion(facts):
        return GuidedCoverageProof(
            "unverified",
            positions,
            source_span,
            semantic_digest(
                {
                    "root": source_span.to_dict(),
                    "api": api,
                    "positions": list(positions),
                    "status": "unverified-output",
                }
            ),
            "guided-proof-conclusions-incomplete",
        )
    digest = semantic_digest(
        {
            "root": source_span.to_dict(),
            "api": api,
            "positions": list(positions),
            "status": "complete",
            "grammar": "frozen-multiple-testing-v3",
        }
    )
    return GuidedCoverageProof("complete", positions, source_span, digest, None)


def _manual_complete_coverage_recheck(
    root: ast.expr,
    *,
    facts: _AstFacts,
    source_span: SourceSpan,
    authorized_count: int,
) -> GuidedCoverageProof:
    """Reuse the closed manual-adjustment grammar at one known expression root."""

    matched = _match_manual_adjustment(root, facts, authorized_count)
    if matched is None:
        return _unverified_proof(source_span, "guided-proof-api-unrecognized")
    factor_kind, factor_value = matched
    positions = _manual_comprehension_positions(root, facts, authorized_count)
    complete_positions = tuple(range(authorized_count))
    if factor_value != authorized_count or positions != complete_positions:
        return GuidedCoverageProof(
            "unverified",
            positions,
            source_span,
            semantic_digest(
                {
                    "root": source_span.to_dict(),
                    "grammar": "frozen-multiple-testing-v3-manual-adjustment",
                    "factor_kind": factor_kind,
                    "factor_value": factor_value,
                    "positions": list(positions),
                    "status": "unverified",
                }
            ),
            "guided-proof-family-incomplete",
        )
    if not _manual_comprehension_outputs_reach_all_conclusions(root, facts, authorized_count):
        return GuidedCoverageProof(
            "unverified",
            positions,
            source_span,
            semantic_digest(
                {
                    "root": source_span.to_dict(),
                    "grammar": "frozen-multiple-testing-v3-manual-adjustment",
                    "positions": list(positions),
                    "status": "unverified-output",
                }
            ),
            "guided-proof-conclusions-incomplete",
        )
    digest = semantic_digest(
        {
            "root": source_span.to_dict(),
            "grammar": "frozen-multiple-testing-v3-manual-adjustment",
            "factor_kind": factor_kind,
            "factor_value": factor_value,
            "positions": list(positions),
            "status": "complete",
        }
    )
    return GuidedCoverageProof("complete", positions, source_span, digest, None)


def _open_concern(
    *,
    question: dict[str, Any],
    result_id: str,
    analysis_ref: dict[str, str],
    contract_ref: dict[str, str],
    created_at: str,
    location: str,
) -> dict[str, Any]:
    count = int(question["extensions"]["x-authorized-count"])
    question_id = str(question["question_id"])
    concern_id = str(question["linked_conditional_concern_ids"][0])
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "conditional_concern",
        "concern_id": concern_id,
        "audit_run_id": question["audit_run_id"],
        "grouping_key": semantic_digest(
            {"question_id": question_id, "detector_result_id": result_id}
        ),
        "issue_class": "x-multiple-testing-correction-scope",
        "title": (
            f"If the located correction does not cover all {count} declared outcomes, the "
            "declared family may be incompletely corrected."
        ),
        "conditional_statement": (
            f"If the correction at {location} does not cover all {count} declared outcomes, "
            "some family conclusions may be based on incomplete multiple-testing control."
        ),
        "condition": {
            "premise_id": f"premise:{question_id}",
            "premise_state": "unknown",
            "if_true": f"The correction at {location} does not cover all {count} declared outcomes.",
        },
        "material_question_id": question_id,
        "potential_impact": {
            "level": "material_if_true",
            "rationale": "Complete-family correction scope determines whether the declared multiplicity requirement was satisfied.",
        },
        "review_priority": "high",
        "subject_refs": [copy.deepcopy(analysis_ref), copy.deepcopy(contract_ref)],
        "affected_descendants": [],
        "evidence": [],
        "why_material": "Complete-family coverage determines whether the declared multiple-testing requirement was satisfied.",
        "next_evidence_needed": [
            "Select one of the question's three bounded answers.",
            "For a complete-scope answer, identify the correction span and closed factor for structural recheck.",
        ],
        "detector_result_ids": [result_id],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_multiple_testing_scope_concern_v1", created_at
        ),
        "extensions": {
            "x-question-purpose": QUESTION_PURPOSE,
            "x-assessment-separation": "conditional-concern-not-finding",
        },
    }


def _ast_facts(content: bytes, outcome_columns: tuple[str, ...]) -> _AstFacts:
    if len(content) > _MAX_BYTES or b"\x00" in content:
        raise ValueError("question source is outside the byte bound")
    text = content.decode("utf-8", errors="strict")
    tree = ast.parse(text, filename="analysis.py", mode="exec", type_comments=True)
    nodes = tuple(ast.walk(tree))
    if len(nodes) > _MAX_NODES:
        raise ValueError("question source is outside the AST bound")
    imports = _imports(tree)
    counts = _binding_counts(tree)
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    assignments: dict[str, ast.expr] = {}
    for node in nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if not _is_unconditional_simple_statement(node, parents):
                continue
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if value is None:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and counts[target.id] == 1:
                    assignments[target.id] = value
    functions_by_name: dict[str, list[ast.FunctionDef]] = {}
    for node in nodes:
        if isinstance(node, ast.FunctionDef):
            functions_by_name.setdefault(node.name, []).append(node)
    functions = {name: values[0] for name, values in functions_by_name.items() if len(values) == 1}
    facts = _AstFacts(
        content,
        text,
        tree,
        imports,
        counts,
        assignments,
        functions,
        set(),
        set(),
        set(),
        set(),
        set(),
        set(),
        outcome_columns,
    )
    _populate_p_lineage(facts)
    return facts


def _imports(tree: ast.Module) -> dict[str, str]:
    values: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                values[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                if alias.name != "*":
                    values[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return values


def _binding_counts(tree: ast.Module) -> Counter[str]:
    values: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            values[node.id] += 1
        elif isinstance(node, ast.arg):
            values[node.arg] += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            values[node.name] += 1
        elif isinstance(node, ast.alias):
            values[node.asname or node.name.split(".")[0]] += 1
        elif isinstance(node, ast.ExceptHandler) and node.name:
            values[node.name] += 1
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                values[name] += 1
        elif isinstance(node, ast.MatchAs) and node.name:
            values[node.name] += 1
        elif isinstance(node, ast.MatchStar) and node.name:
            values[node.name] += 1
        elif isinstance(node, ast.MatchMapping) and node.rest:
            values[node.rest] += 1
    return values


def _is_unconditional_simple_statement(node: ast.stmt, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    if isinstance(parent, ast.Module):
        return node in parent.body
    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return node in parent.body
    return False


def _populate_p_lineage(facts: _AstFacts) -> None:
    nodes = tuple(ast.walk(facts.tree))
    for node in nodes:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if (
            isinstance(node.value, ast.Call)
            and facts.qualified(node.value.func) in _REGISTERED_TEST_APIS
        ):
            for target in targets:
                if isinstance(target, ast.Name):
                    facts.test_results.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) >= 2:
                    p_target = target.elts[1]
                    if isinstance(p_target, ast.Name):
                        facts.p_names.add(p_target.id)
    # Existing X4 semantics may expose a returned p-value as one element of a
    # destructured helper call.  Close only that exact return-position projection;
    # an arbitrary helper return never becomes p-derived.
    for node in nodes:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or len(node.targets) != 1:
            continue
        function = facts.functions.get(node.value.func.id)
        target = node.targets[0]
        if function is None or not isinstance(target, (ast.Tuple, ast.List)):
            continue
        returns = [item for item in function.body if isinstance(item, ast.Return)]
        if len(returns) != 1 or not isinstance(returns[0].value, (ast.Tuple, ast.List)):
            continue
        returned = returns[0].value.elts
        if len(returned) != len(target.elts):
            continue
        for returned_value, target_value in zip(returned, target.elts, strict=True):
            if _expr_pderived(returned_value, facts) and isinstance(target_value, ast.Name):
                facts.p_names.add(target_value.id)
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if _expr_is_p_table(node.value, facts):
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id not in facts.p_tables:
                            facts.p_tables.add(target.id)
                            changed = True
                elif _expr_is_p_record(node.value, facts):
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id not in facts.record_names:
                            facts.record_names.add(target.id)
                            changed = True
                elif _expr_is_record_collection(node.value, facts):
                    for target in targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id not in facts.record_collections
                        ):
                            facts.record_collections.add(target.id)
                            changed = True
                elif _expr_pderived(node.value, facts):
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id not in facts.p_names:
                            facts.p_names.add(target.id)
                            changed = True
                        elif isinstance(target, ast.Subscript) and isinstance(
                            target.value, ast.Name
                        ):
                            if target.value.id not in facts.record_names:
                                facts.record_names.add(target.value.id)
                                changed = True
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append"
                and isinstance(node.func.value, ast.Name)
                and len(node.args) == 1
                and not node.keywords
            ):
                if (
                    _expr_is_p_record(node.args[0], facts)
                    and node.func.value.id not in facts.record_collections
                ):
                    facts.record_collections.add(node.func.value.id)
                    changed = True
                elif (
                    _expr_pderived(node.args[0], facts)
                    and node.func.value.id not in facts.p_containers
                ):
                    facts.p_containers.add(node.func.value.id)
                    changed = True
            if (
                isinstance(node, ast.For)
                and isinstance(node.target, ast.Name)
                and isinstance(node.iter, ast.Name)
                and node.iter.id in facts.record_collections
                and node.target.id not in facts.record_names
            ):
                facts.record_names.add(node.target.id)
                changed = True
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
                for generator in node.generators:
                    if (
                        isinstance(generator.target, ast.Name)
                        and isinstance(generator.iter, ast.Name)
                        and generator.iter.id in facts.record_collections
                        and generator.target.id not in facts.record_names
                    ):
                        facts.record_names.add(generator.target.id)
                        changed = True
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                function = facts.functions.get(node.func.id)
                if function is None or len(function.args.args) != len(node.args):
                    continue
                calls = [
                    item
                    for item in nodes
                    if isinstance(item, ast.Call)
                    and isinstance(item.func, ast.Name)
                    and item.func.id == node.func.id
                ]
                if len(calls) != 1:
                    continue
                for parameter, argument in zip(function.args.args, node.args, strict=True):
                    if facts.binding_counts[parameter.arg] != 1:
                        continue
                    if _expr_is_p_table(argument, facts) and parameter.arg not in facts.p_tables:
                        facts.p_tables.add(parameter.arg)
                        changed = True
                    elif (
                        _expr_is_record_collection(argument, facts)
                        and parameter.arg not in facts.record_collections
                    ):
                        facts.record_collections.add(parameter.arg)
                        changed = True
                    elif (
                        _expr_is_p_record(argument, facts)
                        and parameter.arg not in facts.record_names
                    ):
                        facts.record_names.add(parameter.arg)
                        changed = True


def _expr_pderived(node: ast.AST, facts: _AstFacts) -> bool:
    if isinstance(node, ast.Name):
        if node.id in facts.p_names or node.id in facts.p_containers:
            return True
        argument = _closed_parameter_argument(node, facts)
        return bool(argument is not None and _expr_pderived(argument, facts))
    if isinstance(node, ast.Attribute) and node.attr == "pvalue":
        return (isinstance(node.value, ast.Name) and node.value.id in facts.test_results) or (
            isinstance(node.value, ast.Call)
            and facts.qualified(node.value.func) in _REGISTERED_TEST_APIS
        )
    if isinstance(node, ast.Subscript):
        key = _literal_key(node.slice)
        p_keys = {
            "p",
            "p_value",
            "p_raw",
            "raw_p",
            "p_used",
            "p_adjusted",
            "p_corrected",
            "adjusted_p",
        }
        if isinstance(node.value, ast.Name):
            if node.value.id in facts.p_containers:
                return True
            parameter_argument = _closed_parameter_argument(node.value, facts)
            return (
                node.value.id in facts.record_names
                or node.value.id in facts.p_tables
                or (
                    parameter_argument is not None
                    and (
                        _expr_is_p_record(parameter_argument, facts)
                        or _expr_is_p_table(parameter_argument, facts)
                    )
                )
            ) and key in p_keys
        return key in p_keys and _expr_record_derived(node.value, facts)
    return any(_expr_pderived(child, facts) for child in ast.iter_child_nodes(node))


def _expr_is_p_record(node: ast.AST, facts: _AstFacts) -> bool:
    if isinstance(node, ast.Dict):
        return any(_expr_pderived(value, facts) for value in node.values)
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_expr_pderived(value, facts) for value in node.elts)
    if isinstance(node, ast.Name):
        return node.id in facts.record_names
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = facts.functions.get(node.func.id)
        if function is None or len(function.args.args) != len(node.args):
            return False
        returns = [item for item in function.body if isinstance(item, ast.Return)]
        return bool(
            len(returns) == 1
            and isinstance(returns[0].value, (ast.Dict, ast.Tuple, ast.List))
            and _expr_is_p_record(returns[0].value, facts)
        )
    return False


def _expr_is_record_collection(node: ast.AST, facts: _AstFacts) -> bool:
    if isinstance(node, ast.Name):
        return node.id in facts.record_collections
    if isinstance(node, (ast.List, ast.Tuple)):
        return bool(node.elts) and all(_expr_is_p_record(item, facts) for item in node.elts)
    if not isinstance(node, ast.ListComp) or len(node.generators) != 1:
        return False
    generator = node.generators[0]
    if generator.is_async:
        return False
    if _expr_is_p_record(node.elt, facts):
        return True
    return bool(
        isinstance(generator.target, ast.Name)
        and isinstance(generator.iter, ast.Name)
        and generator.iter.id in facts.record_collections
        and isinstance(node.elt, ast.Name)
        and node.elt.id == generator.target.id
    )


def _expr_is_p_table(node: ast.AST, facts: _AstFacts) -> bool:
    if isinstance(node, ast.Name):
        if node.id in facts.p_tables:
            return True
        argument = _closed_parameter_argument(node, facts)
        return bool(argument is not None and _expr_is_p_table(argument, facts))
    if not isinstance(node, ast.Call):
        return False
    if facts.qualified(node.func) == "pandas.DataFrame":
        return bool(
            len(node.args) == 1
            and not node.keywords
            and _expr_is_record_collection(node.args[0], facts)
        )
    if not isinstance(node.func, ast.Name):
        return False
    function = facts.functions.get(node.func.id)
    if function is None or len(function.args.args) != len(node.args):
        return False
    returns = [item for item in function.body if isinstance(item, ast.Return)]
    return bool(
        len(returns) == 1
        and isinstance(returns[0].value, ast.Call)
        and facts.qualified(returns[0].value.func) == "pandas.DataFrame"
        and len(returns[0].value.args) == 1
        and not returns[0].value.keywords
        and _expr_is_record_collection(returns[0].value.args[0], facts)
    )


def _closed_parameter_argument(node: ast.Name, facts: _AstFacts) -> ast.expr | None:
    """Apply one unchanged-X4 positional argument edge at the node's exact scope."""

    functions = [
        function for function in facts.functions.values() if _ast_contains_position(function, node)
    ]
    if not functions:
        return None
    function = min(
        functions,
        key=lambda value: (
            (value.end_lineno or value.lineno) - value.lineno,
            value.lineno,
            value.col_offset,
        ),
    )
    indexes = [
        index for index, parameter in enumerate(function.args.args) if parameter.arg == node.id
    ]
    if len(indexes) != 1:
        return None
    calls = [
        call
        for call in ast.walk(facts.tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == function.name
        and not call.keywords
        and len(call.args) == len(function.args.args)
    ]
    return calls[0].args[indexes[0]] if len(calls) == 1 else None


def _expr_record_derived(node: ast.AST, facts: _AstFacts) -> bool:
    if isinstance(node, ast.Name):
        return node.id in facts.record_names
    return bool(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in facts.record_collections
    )


def _correction_call_candidates(facts: _AstFacts, count: int) -> list[_Candidate]:
    values: list[_Candidate] = []
    for node in ast.walk(facts.tree):
        if not isinstance(node, ast.Call):
            continue
        callee = facts.qualified(node.func)
        terminal = callee.rsplit(".", 1)[-1].lower() if callee else ""
        kind: WitnessKind | None = None
        if callee in _REGISTERED_CORRECTION_APIS:
            kind = "registered-correction-call"
        elif terminal in _CORRECTION_TERMINALS or terminal.startswith("benjamini"):
            kind = "closed-terminal-correction-call"
        if kind is None:
            continue
        arguments = [*node.args, *(keyword.value for keyword in node.keywords)]
        if not any(_expr_pderived(argument, facts) for argument in arguments):
            continue
        correction_input = _correction_input(node, callee)
        positions = (
            _container_positions(correction_input, facts, count)
            if correction_input is not None
            else ()
        )
        values.append(
            _Candidate(
                kind,
                node,
                callee,
                input_positions=positions,
                origin_positions=positions,
            )
        )
    return values


def _manual_adjustment_candidates(facts: _AstFacts, count: int) -> list[_Candidate]:
    parent = {child: node for node in ast.walk(facts.tree) for child in ast.iter_child_nodes(node)}
    decision_nodes = _backward_decision_nodes(facts)
    values: list[_Candidate] = []
    for node in ast.walk(facts.tree):
        if not isinstance(node, ast.expr):
            continue
        matched = _match_manual_adjustment(node, facts, count)
        if matched is None:
            continue
        if (
            isinstance(parent.get(node), ast.Call)
            and _match_manual_adjustment(cast(ast.expr, parent[node]), facts, count) is not None
        ):
            continue
        if not _manual_adjustment_is_maximal(node, parent):
            continue
        if node not in decision_nodes:
            continue
        factor_kind, factor_value = matched
        values.append(
            _Candidate(
                "manual-adjusted-p-arithmetic",
                node,
                factor_kind=factor_kind,
                factor_value=factor_value,
            )
        )
    return values


def _manual_adjustment_is_maximal(node: ast.expr, parents: dict[ast.AST, ast.AST]) -> bool:
    """Never extract an allowed multiply from inside an off-grammar transform."""

    parent = parents.get(node)
    return not isinstance(
        parent,
        (
            ast.BinOp,
            ast.BoolOp,
            ast.Call,
            ast.IfExp,
            ast.Lambda,
            ast.NamedExpr,
            ast.UnaryOp,
        ),
    )


def _candidate_feeds_record_store(candidate: _Candidate, facts: _AstFacts) -> bool:
    """Require the correction origin to reach the guarded record store structurally."""

    parents = {child: node for node in ast.walk(facts.tree) for child in ast.iter_child_nodes(node)}
    candidate_line = int(getattr(candidate.node, "lineno", 0))
    current: ast.AST = candidate.node
    while (parent := parents.get(current)) is not None:
        if isinstance(parent, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = parent.value
            targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
            if (
                value is not None
                and candidate.node in set(ast.walk(value))
                and any(isinstance(target, ast.Subscript) for target in targets)
            ):
                return True
            break
        current = parent

    origins: set[str] = set()
    for assignment in ast.walk(facts.tree):
        if not isinstance(assignment, (ast.Assign, ast.AnnAssign)) or assignment.value is None:
            continue
        if candidate.node not in set(ast.walk(assignment.value)):
            continue
        targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
        for target in targets:
            if isinstance(target, ast.Name):
                origins.add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                origins.update(item.id for item in target.elts if isinstance(item, ast.Name))
    if not origins or any(facts.binding_counts[name] != 1 for name in origins):
        return False

    changed = True
    while changed:
        changed = False
        for node in ast.walk(facts.tree):
            if int(getattr(node, "lineno", 0)) < candidate_line:
                continue
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                loaded = {
                    child.id
                    for child in ast.walk(node.value)
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
                }
                if not loaded & origins:
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and facts.binding_counts[target.id] == 1:
                        if target.id not in origins:
                            origins.add(target.id)
                            changed = True
            if (
                isinstance(node, ast.For)
                and isinstance(node.iter, ast.Call)
                and facts.qualified(node.iter.func) == "zip"
                and isinstance(node.target, (ast.Tuple, ast.List))
                and len(node.iter.args) == len(node.target.elts)
            ):
                for argument, target in zip(node.iter.args, node.target.elts, strict=True):
                    if not isinstance(target, ast.Name) or facts.binding_counts[target.id] != 1:
                        continue
                    loaded = {
                        child.id
                        for child in ast.walk(argument)
                        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
                    }
                    if loaded & origins and target.id not in origins:
                        origins.add(target.id)
                        changed = True

    for node in ast.walk(facts.tree):
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
            and int(getattr(node, "lineno", 0)) >= candidate_line
        ):
            if node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(target, ast.Subscript) for target in targets):
                continue
            loaded = {
                child.id
                for child in ast.walk(node.value)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
            }
            if loaded & origins:
                return True
    return False


def _match_manual_adjustment(
    node: ast.expr, facts: _AstFacts, count: int
) -> tuple[str, int] | None:
    multiply: ast.BinOp | None = None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        multiply = node
    elif isinstance(node, ast.Call):
        callee = facts.qualified(node.func)
        if callee not in {"min", "numpy.minimum"} or len(node.args) != 2 or node.keywords:
            return None
        for possible, one in ((node.args[0], node.args[1]), (node.args[1], node.args[0])):
            if (
                isinstance(possible, ast.BinOp)
                and isinstance(possible.op, ast.Mult)
                and _decimal_literal(one, facts) == Decimal("1")
            ):
                multiply = possible
                break
    if multiply is None:
        return None
    for p_side, factor_side in ((multiply.left, multiply.right), (multiply.right, multiply.left)):
        if _expr_pderived(p_side, facts):
            return _match_factor(factor_side, facts, count)
    return None


def _manual_threshold_candidates(facts: _AstFacts, count: int) -> list[_Candidate]:
    values: list[_Candidate] = []
    for node in ast.walk(facts.tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
            continue
        operator = _comparison_operator(node.ops[0])
        if operator is None:
            continue
        pairs = (
            (node.left, node.comparators[0], operator),
            (node.comparators[0], node.left, _reverse_operator(operator)),
        )
        for p_side, threshold, normalized_operator in pairs:
            if not _expr_pderived(p_side, facts):
                continue
            match = _match_threshold(threshold, facts, count, {}, frozenset())
            if match is None:
                continue
            origin, factor_kind, factor_value = match
            values.append(
                _Candidate(
                    "manual-decision-threshold-arithmetic",
                    origin,
                    threshold_operator=normalized_operator,
                    factor_kind=factor_kind,
                    factor_value=factor_value,
                )
            )
            break
    return values


def _match_threshold(
    node: ast.expr,
    facts: _AstFacts,
    count: int,
    substitutions: dict[str, ast.expr],
    seen: frozenset[str],
) -> tuple[ast.expr, str, int] | None:
    resolved = _resolve_name_or_helper(node, facts, substitutions, seen)
    if resolved is not None and resolved is not node:
        return _match_threshold(resolved, facts, count, substitutions, seen | _name_set(node))
    if isinstance(node, ast.IfExp):
        if not _closed_membership_test(node.test, facts):
            return None
        body = _match_threshold(node.body, facts, count, substitutions, seen)
        other = _match_threshold(node.orelse, facts, count, substitutions, seen)
        body_alpha = _match_alpha(node.body, facts, substitutions, seen)
        other_alpha = _match_alpha(node.orelse, facts, substitutions, seen)
        if body is not None and other_alpha is not None:
            return (node, body[1], body[2])
        if other is not None and body_alpha is not None:
            return (node, other[1], other[2])
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if _match_alpha(node.left, facts, substitutions, seen) is None:
            return None
        factor = _match_factor(node.right, facts, count, substitutions, seen)
        return (node, *factor) if factor is not None else None
    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Sub)
        and _decimal_literal(node.left, facts, substitutions, seen) == Decimal("1")
    ):
        power = _resolved_component(node.right, facts, substitutions, seen)
        if not isinstance(power, ast.BinOp) or not isinstance(power.op, ast.Pow):
            return None
        base = _resolved_component(power.left, facts, substitutions, seen)
        exponent = _resolved_component(power.right, facts, substitutions, seen)
        if not (
            isinstance(base, ast.BinOp)
            and isinstance(base.op, ast.Sub)
            and _decimal_literal(base.left, facts, substitutions, seen) == Decimal("1")
            and _match_alpha(base.right, facts, substitutions, seen) is not None
            and isinstance(exponent, ast.BinOp)
            and isinstance(exponent.op, ast.Div)
            and _decimal_literal(exponent.left, facts, substitutions, seen) == Decimal("1")
        ):
            return None
        factor = _match_factor(exponent.right, facts, count, substitutions, seen)
        return (node, *factor) if factor is not None else None
    return None


def _resolved_component(
    node: ast.expr,
    facts: _AstFacts,
    substitutions: dict[str, ast.expr],
    seen: frozenset[str],
) -> ast.expr:
    current = node
    local_seen = seen
    for _ in range(_MAX_RESOLUTION_DEPTH):
        resolved = _resolve_name_or_helper(current, facts, substitutions, local_seen)
        if resolved is None or resolved is current:
            return current
        local_seen = local_seen | _name_set(current)
        current = resolved
    return current


def _resolve_name_or_helper(
    node: ast.expr,
    facts: _AstFacts,
    substitutions: dict[str, ast.expr],
    seen: frozenset[str],
) -> ast.expr | None:
    if isinstance(node, ast.Name):
        if node.id in substitutions:
            return substitutions[node.id]
        if node.id in seen:
            return None
        if facts.binding_counts[node.id] != 1:
            # A substituted X4 argument keeps the source binding scope of the call
            # argument.  A same-spelled helper parameter has already been eliminated;
            # all non-substituted names retain the syntax-wide A5 count.
            if not getattr(node, "_mt_x4_argument", False):
                return None
            return _single_simple_assignment_in_source_scope(node, facts)
        return facts.assignments.get(node.id) or _single_direct_loop_assignment(node, facts)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = facts.functions.get(node.func.id)
        if function is None or node.keywords or len(function.args.args) != len(node.args):
            return None
        returns = [item for item in function.body if isinstance(item, ast.Return)]
        if len(returns) != 1 or returns[0].value is None:
            return None
        local_substitutions = dict(substitutions)
        local_substitutions.update(
            {
                parameter.arg: argument
                for parameter, argument in zip(function.args.args, node.args, strict=True)
            }
        )
        return _substitute_expression(returns[0].value, local_substitutions)
    return node


def _single_direct_loop_assignment(name: ast.Name, facts: _AstFacts) -> ast.expr | None:
    """Resolve the closed per-position threshold binding, never a conditional statement."""

    parents = {child: node for node in ast.walk(facts.tree) for child in ast.iter_child_nodes(node)}
    values: list[ast.expr] = []
    for node in ast.walk(facts.tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        if not any(isinstance(target, ast.Name) and target.id == name.id for target in targets):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.For) and node in parent.body:
            values.append(value)
    return values[0] if len(values) == 1 else None


def _substitute_expression(node: ast.expr, substitutions: dict[str, ast.expr]) -> ast.expr:
    class _Substituter(ast.NodeTransformer):
        def visit_Name(self, value: ast.Name) -> ast.AST:
            replacement = substitutions.get(value.id)
            if replacement is None:
                return value
            projected = copy.deepcopy(replacement)
            for item in ast.walk(projected):
                item.__dict__["_mt_x4_argument"] = True
            return projected

    replaced = _Substituter().visit(copy.deepcopy(node))
    assert isinstance(replaced, ast.expr)
    # Preserve the defining expression's public coordinates after substitution.
    ast.copy_location(replaced, node)
    if hasattr(node, "end_lineno"):
        replaced.end_lineno = node.end_lineno
        replaced.end_col_offset = node.end_col_offset
    return replaced


def _single_simple_assignment_in_source_scope(name: ast.Name, facts: _AstFacts) -> ast.expr | None:
    scopes = [
        node
        for node in ast.walk(facts.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
        and _ast_contains_position(node, name)
    ]
    scope: ast.AST = min(
        scopes,
        key=lambda node: (
            int(getattr(node, "end_lineno", 0)) - int(getattr(node, "lineno", 0)),
            int(getattr(node, "lineno", 0)),
        ),
        default=facts.tree,
    )
    values: list[ast.expr] = []
    other_bindings = 0
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name.id:
                    values.append(node.value)
                elif any(
                    isinstance(item, ast.Name)
                    and item.id == name.id
                    and isinstance(item.ctx, ast.Store)
                    for item in ast.walk(target)
                ):
                    other_bindings += 1
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name.id:
                if node.value is None:
                    other_bindings += 1
                else:
                    values.append(node.value)
        elif isinstance(node, (ast.AugAssign, ast.NamedExpr)):
            target = node.target
            if isinstance(target, ast.Name) and target.id == name.id:
                other_bindings += 1
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Del) and node.id == name.id:
            other_bindings += 1
    return values[0] if len(values) == 1 and other_bindings == 0 else None


def _ast_contains_position(outer: ast.AST, inner: ast.AST) -> bool:
    return (
        int(getattr(outer, "lineno", 0)),
        int(getattr(outer, "col_offset", 0)),
    ) <= (
        int(getattr(inner, "lineno", 0)),
        int(getattr(inner, "col_offset", 0)),
    ) and (
        int(getattr(outer, "end_lineno", 0)),
        int(getattr(outer, "end_col_offset", 0)),
    ) >= (
        int(getattr(inner, "end_lineno", 0)),
        int(getattr(inner, "end_col_offset", 0)),
    )


def _match_alpha(
    node: ast.expr,
    facts: _AstFacts,
    substitutions: dict[str, ast.expr] | None = None,
    seen: frozenset[str] = frozenset(),
) -> Decimal | None:
    value = _decimal_literal(node, facts, substitutions or {}, seen)
    return value if value in _ALPHAS else None


def _match_factor(
    node: ast.expr,
    facts: _AstFacts,
    count: int,
    substitutions: dict[str, ast.expr] | None = None,
    seen: frozenset[str] = frozenset(),
) -> tuple[str, int] | None:
    substitutions = substitutions or {}
    resolved: ast.expr | None = node
    if isinstance(node, ast.Name):
        if node.id in substitutions:
            resolved = substitutions[node.id]
        elif facts.binding_counts[node.id] == 1:
            resolved = facts.assignments.get(node.id)
        elif getattr(node, "_mt_x4_argument", False):
            resolved = _single_simple_assignment_in_source_scope(node, facts)
    if resolved is not None and resolved is not node:
        match = _match_factor(resolved, facts, count, substitutions, seen | _name_set(node))
        if match is not None and isinstance(node, ast.Name):
            return ("resolved_constant_integer", match[1])
        return match
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    ):
        return ("literal_multiplier", node.value) if node.value > 0 else None
    if (
        isinstance(node, ast.Call)
        and facts.qualified(node.func) == "len"
        and len(node.args) == 1
        and not node.keywords
    ):
        positions = _static_sequence_positions(node.args[0], facts)
        if positions:
            return (
                "contract_family_size" if len(positions) == count else "correction_input_count",
                len(positions),
            )
    return None


def _decimal_literal(
    node: ast.expr,
    facts: _AstFacts,
    substitutions: dict[str, ast.expr] | None = None,
    seen: frozenset[str] = frozenset(),
) -> Decimal | None:
    substitutions = substitutions or {}
    resolved = _resolve_name_or_helper(node, facts, substitutions, seen)
    if resolved is not None and resolved is not node:
        return _decimal_literal(resolved, facts, substitutions, seen | _name_set(node))
    if not isinstance(node, ast.Constant) or isinstance(node.value, (bool, str, bytes)):
        return None
    segment = ast.get_source_segment(facts.text, node)
    source = segment if segment is not None else repr(node.value)
    try:
        value = Decimal(source.replace("_", ""))
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def _static_sequence_positions(node: ast.expr, facts: _AstFacts) -> tuple[int, ...]:
    sequence = _resolve_static_sequence(node, facts, frozenset())
    if sequence is None:
        return ()
    positions: list[int] = []
    for item in sequence:
        header = item[0] if isinstance(item, tuple) and item else item
        if not isinstance(header, str) or header not in facts.outcome_columns:
            return ()
        positions.append(facts.outcome_columns.index(header))
    return tuple(positions) if len(set(positions)) == len(positions) else ()


def _resolve_static_sequence(
    node: ast.expr, facts: _AstFacts, seen: frozenset[str]
) -> tuple[object, ...] | None:
    if isinstance(node, ast.Name):
        if node.id in seen or facts.binding_counts[node.id] != 1:
            return None
        value = facts.assignments.get(node.id)
        return (
            _resolve_static_sequence(value, facts, seen | {node.id}) if value is not None else None
        )
    if isinstance(node, (ast.List, ast.Tuple)):
        values: list[object] = []
        for element in node.elts:
            if isinstance(element, ast.Constant):
                values.append(element.value)
            elif isinstance(element, (ast.List, ast.Tuple)):
                nested = _resolve_static_sequence(element, facts, seen)
                if nested is None:
                    return None
                values.append(tuple(nested))
            elif isinstance(element, ast.Name):
                scalar = _resolve_scalar(element, facts, seen)
                if scalar is None:
                    return None
                values.append(scalar)
            else:
                return None
        return tuple(values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _resolve_static_sequence(node.left, facts, seen)
        right = _resolve_static_sequence(node.right, facts, seen)
        return (*left, *right) if left is not None and right is not None else None
    return None


def _resolve_scalar(node: ast.expr, facts: _AstFacts, seen: frozenset[str]) -> object | None:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id not in seen and facts.binding_counts[node.id] == 1:
        value = facts.assignments.get(node.id)
        return _resolve_scalar(value, facts, seen | {node.id}) if value is not None else None
    return None


def _closed_membership_test(node: ast.expr, facts: _AstFacts) -> bool:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    return isinstance(node.ops[0], (ast.In, ast.NotIn)) and bool(
        _static_sequence_positions(node.comparators[0], facts)
    )


def _backward_decision_nodes(facts: _AstFacts) -> set[ast.AST]:
    decision_refs: set[tuple[str, str]] = set()
    nodes = tuple(ast.walk(facts.tree))
    for node in nodes:
        if isinstance(node, ast.Compare):
            for expression in (node.left, *node.comparators):
                decision_refs.update(_expression_refs(expression))
    changed = True
    included: set[ast.AST] = set()
    while changed:
        changed = False
        for node in nodes:
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                refs = {ref for target in targets if (ref := _target_ref(target)) is not None}
                if refs & decision_refs:
                    before = len(decision_refs)
                    decision_refs.update(_expression_refs(node.value))
                    included.update(ast.walk(node.value))
                    changed = changed or len(decision_refs) != before
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                function = facts.functions.get(node.func.id)
                if function is None:
                    continue
                parameter_refs = {
                    ("name", arg.arg): index for index, arg in enumerate(function.args.args)
                }
                for ref, index in parameter_refs.items():
                    if ref in decision_refs and index < len(node.args):
                        before = len(decision_refs)
                        decision_refs.update(_expression_refs(node.args[index]))
                        included.update(ast.walk(node.args[index]))
                        changed = changed or len(decision_refs) != before
    for node in nodes:
        if isinstance(node, ast.Compare):
            included.update(ast.walk(node))
    return included


def _expression_refs(node: ast.AST) -> set[tuple[str, str]]:
    values: set[tuple[str, str]] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            values.add(("name", child.id))
        elif isinstance(child, ast.Subscript) and isinstance(child.ctx, ast.Load):
            key = _literal_key(child.slice)
            if isinstance(key, str):
                values.add(("field", key))
    return values


def _target_ref(node: ast.expr) -> tuple[str, str] | None:
    if isinstance(node, ast.Name):
        return ("name", node.id)
    if isinstance(node, ast.Subscript):
        key = _literal_key(node.slice)
        return ("field", key) if isinstance(key, str) else None
    return None


def _correction_input(call: ast.Call, api: str | None) -> ast.expr | None:
    if call.args:
        return call.args[0]
    accepted = {"pvals", "p_values", "ps", "p"}
    for keyword in call.keywords:
        if keyword.arg in accepted:
            return keyword.value
    return None


def _container_positions(node: ast.expr, facts: _AstFacts, count: int) -> tuple[int, ...]:
    direct = _static_sequence_positions(node, facts)
    if direct:
        return direct
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Slice)
        and node.slice.lower is None
        and node.slice.step is None
        and isinstance(node.slice.upper, ast.Constant)
        and isinstance(node.slice.upper.value, int)
        and not isinstance(node.slice.upper.value, bool)
        and 0 < node.slice.upper.value <= count
    ):
        base = _container_positions(node.value, facts, count)
        if base:
            return base[: node.slice.upper.value]
    if isinstance(node, ast.Name):
        append_calls = [
            item
            for item in ast.walk(facts.tree)
            if isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "append"
            and isinstance(item.func.value, ast.Name)
            and item.func.value.id == node.id
            and len(item.args) == 1
            and _expr_pderived(item.args[0], facts)
        ]
        if len(append_calls) == 1 and _loop_over_contract_outcomes(append_calls[0], facts):
            return tuple(range(count))
        literal = facts.assignments.get(node.id)
        if isinstance(literal, ast.ListComp):
            filtered = _filtered_record_p_positions(literal, facts)
            if filtered:
                return filtered
        if isinstance(literal, (ast.List, ast.Tuple)) and len(literal.elts) <= count:
            if all(_expr_pderived(item, facts) for item in literal.elts):
                return tuple(range(len(literal.elts)))
        if node.id in facts.p_containers and _name_zipped_with_outcomes(node.id, facts):
            return tuple(range(count))
    if isinstance(node, (ast.List, ast.Tuple)) and all(
        _expr_pderived(item, facts) for item in node.elts
    ):
        return tuple(range(len(node.elts)))
    return ()


def _filtered_record_p_positions(comprehension: ast.ListComp, facts: _AstFacts) -> tuple[int, ...]:
    """Resolve the already-admitted record-filter projection used by the frozen 3.0 model."""

    if len(comprehension.generators) != 1:
        return ()
    generator = comprehension.generators[0]
    if generator.ifs or generator.is_async or not isinstance(generator.iter, ast.Name):
        return ()
    if not isinstance(generator.target, ast.Name):
        return ()
    target_name = generator.target.id
    if not (
        isinstance(comprehension.elt, ast.Subscript)
        and isinstance(comprehension.elt.value, ast.Name)
        and comprehension.elt.value.id == target_name
        and _literal_key(comprehension.elt.slice) in {"p", "p_value", "p_raw", "raw_p"}
    ):
        return ()
    filtered_assignment = facts.assignments.get(generator.iter.id)
    if (
        not isinstance(filtered_assignment, ast.ListComp)
        or len(filtered_assignment.generators) != 1
    ):
        return ()
    filtered_generator = filtered_assignment.generators[0]
    if (
        filtered_generator.is_async
        or len(filtered_generator.ifs) != 1
        or not isinstance(filtered_generator.target, ast.Name)
        or not isinstance(filtered_generator.iter, ast.Name)
        or not isinstance(filtered_assignment.elt, ast.Name)
        or filtered_assignment.elt.id != filtered_generator.target.id
    ):
        return ()
    flag_test = filtered_generator.ifs[0]
    if not (
        isinstance(flag_test, ast.Subscript)
        and isinstance(flag_test.value, ast.Name)
        and flag_test.value.id == filtered_generator.target.id
        and isinstance((flag_key := _literal_key(flag_test.slice)), str)
    ):
        return ()
    collection_name = filtered_generator.iter.id
    member_sequences: list[tuple[int, ...]] = []
    for append_call in ast.walk(facts.tree):
        if not (
            isinstance(append_call, ast.Call)
            and isinstance(append_call.func, ast.Attribute)
            and append_call.func.attr == "append"
            and isinstance(append_call.func.value, ast.Name)
            and append_call.func.value.id == collection_name
            and len(append_call.args) == 1
            and not append_call.keywords
            and isinstance(append_call.args[0], ast.Dict)
            and _loop_over_contract_outcomes(append_call, facts)
        ):
            continue
        record = append_call.args[0]
        fields = {
            key: value
            for raw_key, value in zip(record.keys, record.values, strict=True)
            if raw_key is not None and isinstance((key := _literal_key(raw_key)), str)
        }
        flag_value = fields.get(flag_key)
        if not isinstance(flag_value, ast.Compare) or len(flag_value.ops) != 1:
            continue
        if not isinstance(flag_value.ops[0], (ast.In, ast.NotIn)):
            continue
        sequence = _static_sequence_positions(flag_value.comparators[0], facts)
        if not sequence or isinstance(flag_value.ops[0], ast.NotIn):
            continue
        if not any(key in fields for key in {"column", "outcome", "name"}):
            continue
        member_sequences.append(sequence)
    unique = set(member_sequences)
    return next(iter(unique)) if len(unique) == 1 else ()


def _loop_over_contract_outcomes(call: ast.Call, facts: _AstFacts) -> bool:
    for loop in (node for node in ast.walk(facts.tree) if isinstance(node, ast.For)):
        if call not in set(ast.walk(loop)):
            continue
        positions = _static_sequence_positions(loop.iter, facts)
        if positions == tuple(range(len(facts.outcome_columns))):
            return True
    return False


def _name_zipped_with_outcomes(name: str, facts: _AstFacts) -> bool:
    for call in (node for node in ast.walk(facts.tree) if isinstance(node, ast.Call)):
        if facts.qualified(call.func) != "zip":
            continue
        if not any(isinstance(arg, ast.Name) and arg.id == name for arg in call.args):
            continue
        if any(
            _static_sequence_positions(arg, facts) == tuple(range(len(facts.outcome_columns)))
            for arg in call.args
        ):
            return True
    return False


def _correction_outputs_reach_all_conclusions(call: ast.Call, facts: _AstFacts, count: int) -> bool:
    output_names: set[str] = set()
    for node in ast.walk(facts.tree):
        if isinstance(node, ast.Assign) and node.value is call:
            for target in node.targets:
                if isinstance(target, (ast.Tuple, ast.List)):
                    for item in target.elts[:2]:
                        if isinstance(item, ast.Name):
                            output_names.add(item.id)
                elif isinstance(target, ast.Name):
                    output_names.add(target.id)
    if not output_names:
        return False
    indexed_positions = {
        key
        for compare in ast.walk(facts.tree)
        if isinstance(compare, ast.Compare)
        for child in ast.walk(compare)
        if isinstance(child, ast.Subscript)
        and isinstance(child.ctx, ast.Load)
        and isinstance(child.value, ast.Name)
        and child.value.id in output_names
        and isinstance((key := _literal_key(child.slice)), int)
    }
    if indexed_positions == set(range(count)):
        return True

    for loop in (node for node in ast.walk(facts.tree) if isinstance(node, ast.For)):
        if not isinstance(loop.iter, ast.Call) or facts.qualified(loop.iter.func) != "zip":
            continue
        if not isinstance(loop.target, (ast.Tuple, ast.List)):
            continue
        if len(loop.target.elts) != len(loop.iter.args):
            continue
        full_companion = any(
            _static_sequence_positions(argument, facts) == tuple(range(count))
            or _container_positions(argument, facts, count) == tuple(range(count))
            for argument in loop.iter.args
            if not (isinstance(argument, ast.Name) and argument.id in output_names)
        )
        if not full_companion:
            continue
        for argument, target in zip(loop.iter.args, loop.target.elts, strict=True):
            if not (
                isinstance(argument, ast.Name)
                and argument.id in output_names
                and isinstance(target, ast.Name)
            ):
                continue
            if _loop_target_reaches_verdict(target.id, loop.body):
                return True
    return False


def _loop_target_reaches_verdict(name: str, body: list[ast.stmt]) -> bool:
    """Require the per-position correction output to drive a verdict in the loop body."""

    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Compare) and any(
                isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id == name
                for child in ast.walk(node)
            ):
                return True
            if isinstance(node, ast.IfExp) and any(
                isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id == name
                for child in ast.walk(node.test)
            ):
                return True
            if isinstance(node, ast.If) and any(
                isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id == name
                for child in ast.walk(node.test)
            ):
                return True
    return False


def _raw_p_directly_reaches_a_conclusion(facts: _AstFacts) -> bool:
    raw_keys = {"p", "p_value", "p_raw", "raw_p"}
    for node in ast.walk(facts.tree):
        if not isinstance(node, ast.Compare):
            continue
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Attribute)
                and child.attr == "pvalue"
                and isinstance(child.ctx, ast.Load)
            ):
                return True
            if isinstance(child, ast.Subscript) and isinstance(child.ctx, ast.Load):
                if _literal_key(child.slice) in raw_keys:
                    return True
            if (
                isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
                and child.id in (facts.p_names | facts.p_containers)
            ):
                return True
    return False


def _manual_comprehension_positions(
    root: ast.expr, facts: _AstFacts, count: int
) -> tuple[int, ...]:
    parents = {child: node for node in ast.walk(facts.tree) for child in ast.iter_child_nodes(node)}
    current: ast.AST = root
    comprehension: ast.ListComp | None = None
    for _ in range(_MAX_RESOLUTION_DEPTH):
        parent = parents.get(current)
        if parent is None:
            break
        if isinstance(parent, ast.ListComp) and root in set(ast.walk(parent.elt)):
            comprehension = parent
            break
        current = parent
    if comprehension is None or len(comprehension.generators) != 1:
        return ()
    generator = comprehension.generators[0]
    if generator.ifs or generator.is_async:
        return ()
    if (
        isinstance(generator.iter, ast.Call)
        and facts.qualified(generator.iter.func) == "range"
        and len(generator.iter.args) == 1
        and not generator.iter.keywords
        and _match_factor(generator.iter.args[0], facts, count) is not None
    ):
        length = _match_factor(generator.iter.args[0], facts, count)
        assert length is not None
        if length[1] != count:
            return ()
    else:
        positions = _static_sequence_positions(generator.iter, facts)
        if positions != tuple(range(count)):
            return ()
    p_containers = {
        child.value.id
        for child in ast.walk(root)
        if isinstance(child, ast.Subscript)
        and isinstance(child.value, ast.Name)
        and child.value.id in facts.p_containers
    }
    if len(p_containers) != 1:
        return ()
    container = next(iter(p_containers))
    if _container_positions(ast.Name(id=container, ctx=ast.Load()), facts, count) != tuple(
        range(count)
    ):
        return ()
    return tuple(range(count))


def _manual_comprehension_outputs_reach_all_conclusions(
    root: ast.expr, facts: _AstFacts, count: int
) -> bool:
    parents = {child: node for node in ast.walk(facts.tree) for child in ast.iter_child_nodes(node)}
    current: ast.AST = root
    comprehension: ast.ListComp | None = None
    for _ in range(_MAX_RESOLUTION_DEPTH):
        parent = parents.get(current)
        if parent is None:
            break
        if isinstance(parent, ast.ListComp):
            comprehension = parent
            break
        current = parent
    if comprehension is None:
        return False
    output_names = {
        target.id
        for node in ast.walk(facts.tree)
        if isinstance(node, ast.Assign) and node.value is comprehension
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    if len(output_names) != 1:
        return False
    output_name = next(iter(output_names))
    indices = {
        key
        for compare in ast.walk(facts.tree)
        if isinstance(compare, ast.Compare)
        for child in ast.walk(compare)
        if isinstance(child, ast.Subscript)
        and isinstance(child.ctx, ast.Load)
        and isinstance(child.value, ast.Name)
        and child.value.id == output_name
        and isinstance((key := _literal_key(child.slice)), int)
    }
    return indices == set(range(count))


def _unverified_proof(span: SourceSpan, code: str) -> GuidedCoverageProof:
    return GuidedCoverageProof(
        "unverified",
        (),
        span,
        semantic_digest({"root": span.to_dict(), "status": "unverified", "code": code}),
        code,
    )


def _node_span(facts: _AstFacts, node: ast.AST) -> SourceSpan:
    if not all(
        hasattr(node, key) for key in ("lineno", "col_offset", "end_lineno", "end_col_offset")
    ):
        raise ValueError("AST node has no exact source coordinates")
    lines = facts.text.splitlines()
    positioned = cast(Any, node)
    start_line = int(positioned.lineno)
    end_line = int(positioned.end_lineno)
    start_prefix = lines[start_line - 1].encode("utf-8")[: int(positioned.col_offset)]
    end_prefix = lines[end_line - 1].encode("utf-8")[: int(positioned.end_col_offset)]
    start_column = len(start_prefix.decode("utf-8", errors="strict")) + 1
    end_column = len(end_prefix.decode("utf-8", errors="strict")) + 1
    return SourceSpan(start_line, start_column, end_line, end_column)


def _source_bytes(facts: _AstFacts, node: ast.AST) -> bytes:
    lines = facts.content.splitlines(keepends=True)
    positioned = cast(Any, node)
    start_line = int(positioned.lineno)
    end_line = int(positioned.end_lineno)
    start = len(b"".join(lines[: start_line - 1])) + int(positioned.col_offset)
    end = len(b"".join(lines[: end_line - 1])) + int(positioned.end_col_offset)
    if not 0 <= start < end <= len(facts.content):
        raise ValueError("AST node source slice is invalid")
    return facts.content[start:end]


def _span_contains(outer: SourceSpan, inner: SourceSpan) -> bool:
    return (outer.start_line, outer.start_column) <= (inner.start_line, inner.start_column) and (
        outer.end_line,
        outer.end_column,
    ) >= (inner.end_line, inner.end_column)


def _comparison_operator(node: ast.cmpop) -> str | None:
    return {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}.get(type(node))


def _reverse_operator(value: str) -> str:
    return {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[value]


def _literal_key(node: ast.expr) -> object | None:
    return node.value if isinstance(node, ast.Constant) else None


def _name_set(node: ast.expr) -> frozenset[str]:
    return frozenset({node.id}) if isinstance(node, ast.Name) else frozenset()


__all__ = [
    "CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS",
    "DETECTOR_ID",
    "DETECTOR_VERSION",
    "NONQUALIFYING_REASON_NAMES",
    "QUALIFYING_REASON_NAMES",
    "QUESTION_PROFILE_ID",
    "QUESTION_PROFILE_SEMANTIC_DIGEST",
    "QUESTION_PROFILE_VERSION",
    "QUESTION_PURPOSE",
    "REASON_QUESTION_CLASS",
    "CorrectionScopeQuestionError",
    "CorrectionScopeWitness",
    "GuidedCoverageProof",
    "ScopeQuestionRecords",
    "SourceSpan",
    "build_scope_question_records",
    "existing_complete_coverage_recheck",
    "locate_correction_scope_witness",
    "question_wording_profile",
]
