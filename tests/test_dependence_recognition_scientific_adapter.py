"""Stage 5 evaluation-only registration for dependence recognition."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import run_audit
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.dependence_recognition.adapter import (
    DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ADAPTER_ID,
    CODE_CSV_DEPENDENCE_ADAPTER_VERSION,
    CodeCsvDependenceAdapter,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    DEPENDENCE_RECOGNITION_CHECK_VERSION as ACTIVE_DEPENDENCE_CHECK_VERSION,
)
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
    ScopeJoinEdge,
    ScopeJoinProof,
    StaticScopeJoinGraph,
)
from sc_referee.scientific_checks.dependence_recognition_adapter import (
    DEPENDENCE_RECOGNITION_ADAPTER_ID,
    DEPENDENCE_RECOGNITION_ADAPTER_VERSION,
    DEPENDENCE_RECOGNITION_CANDIDATE_ID,
    DEPENDENCE_RECOGNITION_CHECK_ID,
    DEPENDENCE_RECOGNITION_CHECK_VERSION,
    DEPENDENCE_RECOGNITION_COUNTEREVIDENCE,
    DEPENDENCE_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST,
    MULTIPLE_ROWS_PER_AUTHORIZED_UNIT,
    ONE_ROW_PER_AUTHORIZED_UNIT,
    DependenceRecognitionScientificAdapter,
    dependence_recognition_grammar_digest,
)
from sc_referee.scientific_checks.founder_orientation_semantic_adapter import (
    FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.profiles import (
    default_scientific_check_registry,
    scientific_check_release_projection,
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

_SOURCE = b"result = procedure(rows)\n"
_SOURCE_PATH = "workflow/analysis.py"
_SOURCE_DIGEST = sha256_digest(_SOURCE)
_SNAPSHOT_DIGEST = sha256_digest(b"dependence-registration-snapshot")


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
    surface_ref = RecordRef("publication_surface", "surface:dependence-stage5")
    artifact_ref = RecordRef("artifact", "artifact:selected-report")
    source_ref = RecordRef("file_record", "file:dependence-analysis")
    operation_ref = RecordRef("operation", "operation:selected-writer")
    parser_ref = RecordRef("parser_result", "parser:dependence-analysis")
    parser = {
        "parser_id": parser_id,
        "parser_version": parser_version,
        "state": "parsed",
    }
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
        for module in scientific_check_release_registry().development_modules
        if module.manifest.check_id == DEPENDENCE_RECOGNITION_CHECK_ID
    ]
    assert len(matches) == 1
    return matches[0]


def _withdrawn_report_lane_adapter_for_replay() -> DependenceRecognitionScientificAdapter:
    active = _module()
    check = replace(active.manifest, check_version=DEPENDENCE_RECOGNITION_CHECK_VERSION)
    one_row = check.requirement_candidates[0].operand
    manifest = AdapterManifest(
        adapter_id=DEPENDENCE_RECOGNITION_ADAPTER_ID,
        adapter_version=DEPENDENCE_RECOGNITION_ADAPTER_VERSION,
        implementation_digest=DEPENDENCE_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=dependence_recognition_grammar_digest(),
        parser_id="parser:python-ast-tokenize",
        parser_version="0.15.1",
        source_language="python",
        evidence_plane="static_source",
        semantic_roles=check.semantic_roles,
        applicability_profile="bounded-dependence-semantic-certificate-v1",
        counterevidence_profiles=DEPENDENCE_RECOGNITION_COUNTEREVIDENCE,
        known_gaps=(),
    )
    return DependenceRecognitionScientificAdapter(
        check_manifest=check,
        adapter_manifest=manifest,
        one_row_operand=one_row,
        multiple_rows_operand=CanonicalOperand.scalar(MULTIPLE_ROWS_PER_AUTHORIZED_UNIT),
    )


def _common_certificate_projection(record_type: str) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "report_only": True,
        "source_path": _SOURCE_PATH,
        "source_digest": _SOURCE_DIGEST,
        "analysis_target_ref": {"record_type": "analysis", "record_id": "analysis:primary"},
        "procedure_ref": {"record_type": "procedure", "record_id": "procedure:test"},
        "affected_target_ref": {"record_type": "result", "record_id": "result:report"},
        "independent_unit_definition_id": "unit-definition:participant",
        "authorized_key_columns": ["participant_id"],
        "input_binding": {
            "path": "inputs/data.csv",
            "content_digest": sha256_digest(b"participant_id,a,b\np1,1,2\n"),
        },
        "resolved_callable": "scipy.stats.ttest_ind",
        "sink_tokens": ["sink:report-write"],
        "proposed_case_digest": sha256_digest(b"proposed-case"),
        "evidence_declarations": [
            {
                "evidence_id": "procedure-call",
                "path": _SOURCE_PATH,
                "start_line": 1,
                "end_line": 1,
                "start_column": 10,
                "end_column": 19,
            },
            {
                "evidence_id": "unit-key-data-fact",
                "path": "inputs/data.csv",
                "start_line": 1,
                "end_line": 1,
                "start_column": 1,
                "end_column": 1,
            },
        ],
    }


def _shadow_payload(payload_type: str) -> dict[str, Any]:
    if payload_type == "shadow_candidate":
        body = _common_certificate_projection("dependence_shadow_candidate")
        body.update(
            {
                "candidate_id": "dependence-shadow-candidate:test",
                "promotion_state": "unregistered_shadow_only",
                "statement": "Bounded static relationship.",
                "repeated_independent_unit_ids": ["unit:p1"],
                "applicable_safeguard_ids": [],
            }
        )
        outcome = "evaluation_candidate"
    elif payload_type == "coverage_note":
        body = _common_certificate_projection("dependence_shadow_coverage_note")
        body.update(
            {
                "coverage_class": "one_observation_per_independent_unit",
                "core_reason_code": "covered_no_repeated_unit",
                "statement": "One row per authorized unit.",
                "repeated_independent_unit_ids": [],
                "applicable_safeguard_ids": ["no-repeated-independent-unit"],
            }
        )
        outcome = "covered_negative"
    elif payload_type == "material_question":
        body = {
            "record_type": "dependence_shadow_material_question",
            "candidate_key_columns": ["participant_id", "sample_id"],
            "ranking": None,
        }
        outcome = "question"
    elif payload_type == "no_lineage":
        body = {
            "record_type": "dependence_recognition_shadow_abstention",
            "coverage_classes": ["no-supported-dependence-lineage"],
        }
        payload_type = "abstention"
        outcome = "unsupported"
    else:
        body = {
            "record_type": "dependence_recognition_shadow_abstention",
            "coverage_classes": ["pandas-frame-model"],
        }
        payload_type = "abstention"
        outcome = "unsupported"
    return {
        "record_type": "dependence_recognition_shadow_result",
        "schema_version": "1.1.0",
        "adapter_id": "dependence-recognition-semantic-shadow",
        "adapter_version": "1.1.0",
        "adapter_implementation_digest": DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
        "delivery_plane": "unregistered_shadow_report_only",
        "outcome": outcome,
        "payload_type": payload_type,
        "reason_code": "test-route",
        "basis": "test projection",
        "case_digest": sha256_digest(b"case"),
        "output_ceiling": "evaluation_candidate",
        "wording_ceiling": "static_code_relationship_only",
        "non_inferences": [],
        "payload": body,
    }


@pytest.mark.parametrize(
    ("payload_type", "applicability", "operand"),
    [
        ("shadow_candidate", "applicable", MULTIPLE_ROWS_PER_AUTHORIZED_UNIT),
        ("coverage_note", "applicable", ONE_ROW_PER_AUTHORIZED_UNIT),
        ("material_question", "ambiguous", None),
        ("no_lineage", "not_applicable", None),
        ("unsupported", "unsupported", None),
    ],
)
@pytest.mark.retired_report_lane
def test_all_shadow_routes_normalize_once_under_question_only_ceiling(
    payload_type: str,
    applicability: str,
    operand: str | None,
) -> None:
    adapter = _withdrawn_report_lane_adapter_for_replay()
    shadow = _CountingShadow(_shadow_payload(payload_type))
    adapter = replace(adapter, shadow_adapter=shadow)

    observation = adapter.inspect(_context())

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
                    "record_id": "file:dependence-analysis",
                },
                "path": _SOURCE_PATH,
                "content_digest": _SOURCE_DIGEST,
                "start_line": 1,
                "end_line": 1,
                "start_column": 10,
                "end_column": 19,
                "parser_result_ref": {
                    "record_type": "parser_result",
                    "record_id": "parser:dependence-analysis",
                },
            }
        ]
        assert len(observation.scope_join_path) == 3
    else:
        assert observation.evidence_spans == ()
        assert observation.scope_join_path == ()


@pytest.mark.retired_report_lane
def test_historical_report_lane_legacy_python_ast_parser_identity_is_unsupported() -> None:
    adapter = _withdrawn_report_lane_adapter_for_replay()
    adapter = replace(
        adapter,
        shadow_adapter=_CountingShadow(_shadow_payload("material_question")),
    )

    observation = adapter.inspect(_context(parser_id="python-ast", parser_version="3.11"))

    assert observation.applicability == "unsupported"
    assert observation.abstention_reason == "dependence-source-or-parser-identity-mismatch"


@pytest.mark.retired_report_lane
def test_historical_report_lane_paired_procedure_gap_retains_named_abstention() -> None:
    adapter = _withdrawn_report_lane_adapter_for_replay()
    shadow = _shadow_payload("unsupported")
    shadow["payload"]["coverage_classes"] = ["paired-procedure-operand-unverified"]

    observation = replace(
        adapter,
        shadow_adapter=_CountingShadow(shadow),
    ).inspect(_context())

    assert observation.applicability == "unsupported"
    assert observation.abstention_reason == "paired-procedure-operand-unverified"


@pytest.mark.retired_report_lane
def test_historical_report_lane_without_exact_writer_scope_is_unsupported() -> None:
    adapter = _withdrawn_report_lane_adapter_for_replay()
    shadow = _CountingShadow(_shadow_payload("shadow_candidate"))

    observation = replace(adapter, shadow_adapter=shadow).inspect(_context(scoped=False))

    assert shadow.calls == 1
    assert observation.applicability == "unsupported"
    assert observation.observed_operand is None
    assert observation.output_ceiling == "question_only"


def test_registered_dependence_module_has_exact_single_adapter_identity() -> None:
    module = _module()

    assert module.manifest.check_id == DEPENDENCE_RECOGNITION_CHECK_ID
    assert module.manifest.check_version == ACTIVE_DEPENDENCE_CHECK_VERSION
    assert module.manifest.dimension == "dependence_structure"
    assert module.manifest.maturity_tier == "question_only"
    assert module.manifest.production_finding_permitted is False
    assert len(module.manifest.requirement_candidates) == 1
    assert module.manifest.requirement_candidates[0].candidate_id == (
        DEPENDENCE_RECOGNITION_CANDIDATE_ID
    )
    assert len(module.adapters) == len(module.adapter_manifests) == 1
    assert isinstance(module.adapters[0], CodeCsvDependenceAdapter)
    assert module.adapter_manifests[0].adapter_id == CODE_CSV_DEPENDENCE_ADAPTER_ID
    assert module.adapter_manifests[0].adapter_version == CODE_CSV_DEPENDENCE_ADAPTER_VERSION
    assert module.adapter_manifests[0].evidence_plane == "static_source"


def test_registered_code_adapter_uses_only_static_python_evidence() -> None:
    module = _module()
    adapter = module.adapters[0]
    assert isinstance(adapter, CodeCsvDependenceAdapter)
    assert adapter.adapter_manifest.parser_id == "parser:python-ast-tokenize"
    assert adapter.adapter_manifest.source_language == "python"
    assert adapter.adapter_manifest.evidence_plane == "static_source"


def test_registered_code_adapter_has_no_report_or_shadow_lane() -> None:
    adapter = _module().adapters[0]
    assert isinstance(adapter, CodeCsvDependenceAdapter)
    assert not hasattr(adapter, "shadow_adapter")
    assert all("report" not in role for role in adapter.adapter_manifest.semantic_roles)


def test_registered_development_code_adapter_is_question_only() -> None:
    module = _module()
    adapter = module.adapters[0]
    assert isinstance(adapter, CodeCsvDependenceAdapter)
    assert module.manifest.production_finding_permitted is False
    assert module.manifest.maturity_tier == "question_only"
    assert adapter.check_manifest.manifest_digest == module.manifest.manifest_digest


def test_registered_code_adapter_counterevidence_is_closed_and_prose_free() -> None:
    adapter = _module().adapters[0]
    assert isinstance(adapter, CodeCsvDependenceAdapter)
    profiles = adapter.adapter_manifest.counterevidence_profiles
    assert profiles
    assert len(profiles) == len(set(profiles))
    assert all("report" not in value for value in profiles)
    assert "prose-free-source-view" in profiles


def test_published_dependence_candidate_resolves_through_requirement_profile() -> None:
    resolved = resolve_scientific_requirement_profile(
        {
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": DEPENDENCE_RECOGNITION_CHECK_ID,
            "candidate_id": DEPENDENCE_RECOGNITION_CANDIDATE_ID,
            "semantic_role_authority": {
                "authorized_independent_unit_key": {
                    "material_input_path": "data/input.csv",
                    "column_name": "participant_id",
                    "group_contrast_column": "group",
                }
            },
        },
        registry=scientific_check_release_registry(),
    )

    assert resolved.check_id == DEPENDENCE_RECOGNITION_CHECK_ID
    assert resolved.candidate_id == DEPENDENCE_RECOGNITION_CANDIDATE_ID
    assert resolved.value == ONE_ROW_PER_AUTHORIZED_UNIT


def test_registered_dependence_route_emits_zero_findings(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "analysis.py").write_text("result = procedure(rows)\n", encoding="utf-8")
    (repository / "report.md").write_text("[selected-result] unavailable\n", encoding="utf-8")
    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        scientific_check_registry=default_scientific_check_registry(),
    )

    assert bundle["findings"] == []


def test_founder_core_and_shared_integration_closure_are_content_addressed() -> None:
    founder = next(
        module
        for module in scientific_check_release_registry().modules
        if module.manifest.check_id == "check:founder-orientation-before-hmm-emission"
    )
    assert founder.manifest.manifest_digest == (
        "sha256:d3e05926aff2f2473498db83fb8e36a6e6f87b66542ee198ec79a6bdfd7192eb"
    )
    assert [item.manifest_digest for item in founder.adapter_manifests] == [
        "sha256:cd13024eb42264d78ba410e8fe6eb914f8188f3b693f4939835af73526e52097",
        "sha256:a909ed1d991b5c35ad2aa0b73501aa387064c036e8e572235c7f47ff15949267",
    ]
    assert FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST == (
        "sha256:d8cc85e94a68d5778a8633ce756f18eac959683050df0c51d0821d4e72dc9c44"
    )


def test_founder_closure_core_is_byte_identical_and_integration_is_release_bound() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = {
        "src/sc_referee/scientific_checks/core.py": (
            "sha256:91271b8c2a007c460a35134ff1c207424a99cf269c78d638557ffad330192c92"
        ),
        "src/sc_referee/scientific_checks/integration.py": (
            "sha256:55ac1a3dcef282445eb75f2edb55a0f518f8649cbc3b028b148862ed7afb93da"
        ),
    }
    assert {path: sha256_digest((root / path).read_bytes()) for path in expected} == expected
    release = scientific_check_release_registry()
    assert (
        scientific_check_release_projection(release)["implementation_files"][
            "scientific_checks/integration.py"
        ]
        == expected["src/sc_referee/scientific_checks/integration.py"]
    )
