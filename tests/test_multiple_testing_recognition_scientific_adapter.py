"""Question-only registration tests for multiple-testing recognition."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import run_audit
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.detectors.method_conflict_grant_pins import GRANT_PINS
from sc_referee.multiple_testing_recognition.adapter import (
    MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
    ScopeJoinEdge,
    ScopeJoinProof,
    StaticScopeJoinGraph,
)
from sc_referee.scientific_checks.multiple_testing_recognition_adapter import (
    COMPLETE_FAMILY_CORRECTION,
    MULTIPLE_TESTING_RECOGNITION_ADAPTER_ID,
    MULTIPLE_TESTING_RECOGNITION_ADAPTER_VERSION,
    MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID,
    MULTIPLE_TESTING_RECOGNITION_CHECK_ID,
    MULTIPLE_TESTING_RECOGNITION_CHECK_VERSION,
    STRICT_SUBSET_CORRECTION,
    MultipleTestingRecognitionScientificAdapter,
)
from sc_referee.scientific_checks.profiles import (
    default_scientific_check_registry,
    scientific_check_release_registry,
)
from sc_referee.scientific_checks.scope_joins import (
    PUBLICATION_PROFILE,
    STATIC_WRITER_OUTPUT_PROFILE,
    STATIC_WRITER_SOURCE_PROFILE,
)
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    resolve_scientific_requirement_profile,
)

_SOURCE = b"adjusted = correction(pvals)\n"
_SOURCE_PATH = "workflow/analysis.py"
_SOURCE_DIGEST = sha256_digest(_SOURCE)
_SNAPSHOT_DIGEST = sha256_digest(b"multiple-testing-registration-snapshot")


@dataclass
class _CountingShadow:
    payload: dict[str, Any]
    calls: int = 0

    def inspect(self, context: FrozenInspectionContext) -> dict[str, Any]:
        del context
        self.calls += 1
        return self.payload


def _proof(source: RecordRef, relation: str, target: RecordRef, profile: str) -> ScopeJoinProof:
    return ScopeJoinProof.create(
        edge=ScopeJoinEdge(source, relation, target),
        profile=profile,
        evidence_refs=(source, target),
        evidence_payload_digests=(sha256_digest(f"{source.record_id}:{target.record_id}"),),
        snapshot_digest=_SNAPSHOT_DIGEST,
        authority_limitations=(
            "Static connectivity does not establish execution or scientific correctness.",
        ),
    )


def _context(
    *,
    scoped: bool = True,
    parser_id: str = "parser:python-ast-tokenize",
    parser_version: str = "0.15.1",
) -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "surface:multiple-testing-stage5")
    artifact_ref = RecordRef("artifact", "artifact:selected-report")
    source_ref = RecordRef("file_record", "file:multiple-testing-analysis")
    operation_ref = RecordRef("operation", "operation:selected-writer")
    parser_ref = RecordRef("parser_result", "parser:multiple-testing-analysis")
    parser = {"parser_id": parser_id, "parser_version": parser_version, "state": "parsed"}
    parser_payload = canonical_json(parser).encode()
    records = (
        FrozenBaseRecord.from_record(
            surface_ref, {"publication_surface_id": surface_ref.record_id}
        ),
        FrozenBaseRecord.from_record(artifact_ref, {"artifact_id": artifact_ref.record_id}),
        FrozenBaseRecord.from_record(source_ref, {"file_record_id": source_ref.record_id}),
        FrozenBaseRecord.from_record(operation_ref, {"operation_id": operation_ref.record_id}),
        FrozenBaseRecord.from_record(parser_ref, parser),
    )
    proofs = (
        _proof(
            source_ref,
            "contains_unique_static_selected_output_writer",
            operation_ref,
            STATIC_WRITER_SOURCE_PROFILE,
        ),
        _proof(
            operation_ref,
            "declares_selected_output_artifact",
            artifact_ref,
            STATIC_WRITER_OUTPUT_PROFILE,
        ),
        _proof(
            artifact_ref,
            "selected_by_publication_surface",
            surface_ref,
            PUBLICATION_PROFILE,
        ),
    )
    graph = (
        StaticScopeJoinGraph(
            snapshot_digest=_SNAPSHOT_DIGEST,
            proofs=tuple(sorted(proofs, key=lambda item: canonical_json(item.to_dict()))),
        )
        if scoped
        else None
    )
    return FrozenInspectionContext(
        snapshot_digest=_SNAPSHOT_DIGEST,
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path=_SOURCE_PATH,
                file_ref=source_ref,
                content=_SOURCE,
                content_digest=_SOURCE_DIGEST,
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=records,
        scope_join_graph=graph,
    )


def _module():  # type: ignore[no-untyped-def]
    matches = [
        module
        for module in scientific_check_release_registry().modules
        if module.manifest.check_id == MULTIPLE_TESTING_RECOGNITION_CHECK_ID
    ]
    assert len(matches) == 1
    return matches[0]


def _certificate_projection(record_type: str, *, complete: bool) -> dict[str, Any]:
    corrected_positions = [0, 1, 2] if complete else [0, 1]
    return {
        "record_type": record_type,
        "report_only": True,
        "source_path": _SOURCE_PATH,
        "source_digest": _SOURCE_DIGEST,
        "analysis_target_ref": {"record_type": "analysis", "record_id": "analysis:primary"},
        "correction_procedure_ref": {
            "record_type": "procedure",
            "record_id": "procedure:correction",
        },
        "affected_target_ref": {"record_type": "result", "record_id": "result:report"},
        "family_definition_id": "family-definition:primary",
        "battery_construct_id": "battery-construct:primary",
        "iterable_row_domain": "row-domain:tests",
        "authorized_family_key_columns": ["gene"],
        "family_authorization": {
            "record_id": "family-authorization:primary",
            "actor_id": "actor:scientist",
            "family_member_rule": "all_rows_in_frozen_input",
        },
        "input_binding": {
            "path": "results/tests.csv",
            "content_digest": sha256_digest(b"gene,pvalue\ng1,0.01\n"),
        },
        "measurement_input_binding": {
            "path": "inputs/measurements.csv",
            "content_digest": sha256_digest(b"gene,x1,x2,y1,y2\ng1,1,2,2,3\n"),
        },
        "measurement_key_columns": ["gene"],
        "left_measurement_columns": ["x1", "x2"],
        "right_measurement_columns": ["y1", "y2"],
        "argument_vector_tokens": [
            ["argument-vector:left:0", "argument-vector:right:0"],
            ["argument-vector:left:1", "argument-vector:right:1"],
            ["argument-vector:left:2", "argument-vector:right:2"],
        ],
        "performed_count": 3,
        "corrected_count": len(corrected_positions),
        "corrected_positions": corrected_positions,
        "sink_tokens": ["sink:report-write"],
        "proposed_case_digest": sha256_digest(b"proposed-case"),
        "evidence_declarations": [
            {
                "evidence_id": "correction-call",
                "path": _SOURCE_PATH,
                "start_line": 1,
                "end_line": 1,
                "start_column": 12,
                "end_column": 29,
            },
            {
                "evidence_id": "family-data-fact",
                "path": "results/tests.csv",
                "start_line": 1,
                "end_line": 1,
                "start_column": 1,
                "end_column": 1,
            },
        ],
    }


def _shadow_payload(payload_type: str) -> dict[str, Any]:
    if payload_type == "shadow_candidate":
        body = _certificate_projection("multiple_testing_shadow_candidate", complete=False)
        body.update(
            {
                "candidate_id": "multiple-testing-shadow-candidate:test",
                "promotion_state": "unregistered_shadow_only",
                "statement": "Bounded static relationship.",
            }
        )
        outcome = "evaluation_candidate"
    elif payload_type == "coverage_note":
        body = _certificate_projection("multiple_testing_shadow_coverage_note", complete=True)
        body.update(
            {
                "coverage_class": "complete_family_correction",
                "statement": "Complete family correction.",
            }
        )
        outcome = "covered_negative"
    elif payload_type == "material_question":
        body = {
            "record_type": "multiple_testing_shadow_material_question",
            "candidate_batteries": [],
            "ranking": None,
        }
        outcome = "question"
    elif payload_type == "no_lineage":
        body = {
            "record_type": "multiple_testing_recognition_shadow_abstention",
            "coverage_classes": ["no-registered-test-battery"],
        }
        payload_type = "abstention"
        outcome = "unsupported"
    else:
        body = {
            "record_type": "multiple_testing_recognition_shadow_abstention",
            "coverage_classes": ["loop-built-test-battery-unrecognized"],
        }
        payload_type = "abstention"
        outcome = "unsupported"
    return {
        "record_type": "multiple_testing_recognition_shadow_result",
        "schema_version": "1.1.0",
        "adapter_id": "multiple-testing-recognition-semantic-shadow",
        "adapter_version": "1.2.0",
        "adapter_implementation_digest": MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
        "delivery_plane": "unregistered_shadow_report_only",
        "outcome": outcome,
        "payload_type": payload_type,
        "reason_code": "test-route",
        "basis": "test projection",
        "case_digest": sha256_digest(b"case"),
        "output_ceiling": "evaluation_candidate",
        "wording_ceiling": "supported_normal_path_static_relationship_only",
        "non_inferences": [],
        "payload": body,
    }


@pytest.mark.parametrize(
    ("payload_type", "applicability", "operand"),
    [
        ("shadow_candidate", "applicable", STRICT_SUBSET_CORRECTION),
        ("coverage_note", "applicable", COMPLETE_FAMILY_CORRECTION),
        ("material_question", "ambiguous", None),
        ("no_lineage", "not_applicable", None),
        ("unsupported", "unsupported", None),
    ],
)
def test_all_shadow_routes_normalize_once_under_question_only_ceiling(
    payload_type: str,
    applicability: str,
    operand: str | None,
) -> None:
    module = _module()
    adapter = module.adapters[0]
    assert isinstance(adapter, MultipleTestingRecognitionScientificAdapter)
    shadow = _CountingShadow(_shadow_payload(payload_type))
    observation = replace(adapter, shadow_adapter=shadow).inspect(_context())

    assert shadow.calls == 1
    assert observation.applicability == applicability
    assert observation.output_ceiling == "question_only"
    assert (
        str(observation.observed_operand.value)
        if observation.observed_operand is not None
        else None
    ) == operand
    if applicability == "applicable":
        assert [span.to_dict() for span in observation.evidence_spans] == [
            {
                "file_ref": {
                    "record_type": "file_record",
                    "record_id": "file:multiple-testing-analysis",
                },
                "path": _SOURCE_PATH,
                "content_digest": _SOURCE_DIGEST,
                "start_line": 1,
                "end_line": 1,
                "start_column": 12,
                "end_column": 29,
                "parser_result_ref": {
                    "record_type": "parser_result",
                    "record_id": "parser:multiple-testing-analysis",
                },
            }
        ]
        assert len(observation.scope_join_path) == 3
    else:
        assert observation.evidence_spans == ()
        assert observation.scope_join_path == ()


@pytest.mark.parametrize(
    "payload_type",
    ["shadow_candidate", "coverage_note", "material_question", "no_lineage", "unsupported"],
)
def test_every_branch_requires_the_registered_capture_parser(payload_type: str) -> None:
    adapter = _module().adapters[0]
    assert isinstance(adapter, MultipleTestingRecognitionScientificAdapter)
    observation = replace(
        adapter,
        shadow_adapter=_CountingShadow(_shadow_payload(payload_type)),
    ).inspect(_context(parser_id="python-ast", parser_version="3.11"))

    assert observation.applicability == "unsupported"
    assert observation.abstention_reason == "multiple-testing-source-or-parser-identity-mismatch"


def test_registered_module_has_one_adapter_and_one_published_candidate() -> None:
    module = _module()
    assert module.manifest.check_id == MULTIPLE_TESTING_RECOGNITION_CHECK_ID
    assert module.manifest.check_version == MULTIPLE_TESTING_RECOGNITION_CHECK_VERSION
    assert module.manifest.dimension == "selection_process"
    assert module.manifest.maturity_tier == "question_only"
    assert module.manifest.production_finding_permitted is False
    assert len(module.manifest.requirement_candidates) == 1
    assert module.manifest.requirement_candidates[0].candidate_id == (
        MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID
    )
    assert len(module.adapters) == len(module.adapter_manifests) == 1
    assert module.adapter_manifests[0].adapter_id == MULTIPLE_TESTING_RECOGNITION_ADAPTER_ID
    assert (
        module.adapter_manifests[0].adapter_version == MULTIPLE_TESTING_RECOGNITION_ADAPTER_VERSION
    )


def test_published_candidate_resolves_through_requirement_profile() -> None:
    resolved = resolve_scientific_requirement_profile(
        {
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "semantic_role_authority": {},
            "check_id": MULTIPLE_TESTING_RECOGNITION_CHECK_ID,
            "candidate_id": MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID,
        },
        registry=scientific_check_release_registry(),
    )
    assert resolved.check_id == MULTIPLE_TESTING_RECOGNITION_CHECK_ID
    assert resolved.candidate_id == MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID
    assert resolved.value == COMPLETE_FAMILY_CORRECTION


def test_registered_route_emits_zero_findings(tmp_path: Path, schema_root: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "analysis.py").write_text("adjusted = correction(pvals)\n", encoding="utf-8")
    (repository / "report.md").write_text("[selected-result] unavailable\n", encoding="utf-8")
    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        scientific_check_registry=default_scientific_check_registry(),
    )
    assert bundle["findings"] == []


def test_active_check_identities_match_the_release_registry() -> None:
    expected = {
        "check:authorized-independent-unit-entry-into-row-independent-procedure": (
            "sha256:57aaa1296e329a9cb27c839e1cb945e0df18d84ecb7a702009b632a0d269ac55",
            "sha256:7fcbf6165e3af9c7de531c53ac34c31d0b2ce215d1df7aa78844d3058e26c50b",
        ),
        "check:complete-domain-exposure-denominator": (
            "sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9",
            "sha256:231046e541e1e84671b7fe716a2454c67d2d931f1cfe432e7de80512987d3a20",
        ),
    }
    modules = {
        module.manifest.check_id: module for module in scientific_check_release_registry().modules
    }
    assert {
        check_id: (
            modules[check_id].manifest.manifest_digest,
            modules[check_id].adapter_manifests[0].manifest_digest,
        )
        for check_id in expected
    } == expected
    assert len(GRANT_PINS) == 2
    assert set(GRANT_PINS) == {
        "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1",
        "method-conflict-binding:complete-domain-exposure-denominator-v1",
    }


def test_qualification_manifest_bytes_match_same_commit_grant_rederivation() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/sc_referee/resources/capability-manifests-v1/qualification-manifests.json"
    assert sha256_digest(path.read_bytes()) == (
        "sha256:12f346ca44c2c88c202227ebcea076dfbaac78b69b5146303c8da4826a9496cf"
    )
