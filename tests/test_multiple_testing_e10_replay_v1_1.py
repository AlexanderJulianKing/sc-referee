from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v1 import (
    BoundedCodeCsvMultipleTestingConflictV1Detector,
)
from sc_referee.method_contract_run import (
    preflight_frozen_scientific_requirement,
    run_method_contract,
)
from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v1 as adapter_v1
from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v1 as dataflow_v1
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    RequirementCandidate,
    ScientificCheckModule,
)
from sc_referee.scientific_checks.integration import build_frozen_inspection_context
from sc_referee.scientific_checks.registry import ScientificCheckRegistry

_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
_ROOT = Path("evaluation/development/blind-envelope-10-2026-08-24")
_HISTORICAL_E10_DESIGN_DIGEST = (
    "sha256:8adddfaca6729e4cf7e87ba0044c295b848d29eba37ae7003a5a6e4c4888a303"
)
# E10 custody retains the pre-header-correction bytes; the current normative base is ac3306f3....
_CURRENT_V1_DESIGN_DIGEST = (
    "sha256:ac3306f3e58248ac03fee9c75f06d7a9f8a045547ae84f85baae56ecc98fb651"
)


def _historical_v1_module(lock: dict[str, Any]) -> ScientificCheckModule:
    stored = next(
        item
        for item in lock["scientific_check_registry"]["enabled_modules"]
        if item["manifest"]["check_id"] == _CHECK_ID
    )
    manifest_value = stored["manifest"]
    candidate_value = manifest_value["requirement_candidates"][0]
    candidate = RequirementCandidate(
        candidate_id=candidate_value["candidate_id"],
        label=candidate_value["label"],
        operand=CanonicalOperand.scalar(candidate_value["operand"]["value"]),
        authority_basis=candidate_value["authority_basis"],
    )
    check_manifest = CheckManifest(
        check_id=manifest_value["check_id"],
        check_version=manifest_value["check_version"],
        implementation_digest=manifest_value["implementation_digest"],
        maturity_tier=manifest_value["maturity_tier"],
        dimension=manifest_value["dimension"],
        comparison_form=manifest_value["comparison_form"],
        requirement_candidates=(candidate,),
        semantic_roles=tuple(manifest_value["semantic_roles"]),
        required_record_types=tuple(manifest_value["required_record_types"]),
        permitted_wording=manifest_value["permitted_wording"],
        prohibited_inferences=tuple(manifest_value["prohibited_inferences"]),
        production_finding_permitted=manifest_value["production_finding_permitted"],
    )
    adapter_value = stored["adapter_manifests"][0]
    adapter_manifest = AdapterManifest(
        adapter_id=adapter_value["adapter_id"],
        adapter_version=adapter_value["adapter_version"],
        implementation_digest=adapter_value["implementation_digest"],
        recognition_grammar_digest=adapter_value["recognition_grammar_digest"],
        parser_id=adapter_value["parser_id"],
        parser_version=adapter_value["parser_version"],
        source_language=adapter_value["source_language"],
        evidence_plane=adapter_value["evidence_plane"],
        semantic_roles=tuple(adapter_value["semantic_roles"]),
        applicability_profile=adapter_value["applicability_profile"],
        counterevidence_profiles=tuple(adapter_value["counterevidence_profiles"]),
        known_gaps=tuple(adapter_value["known_gaps"]),
    )
    adapter = adapter_v1.CodeCsvMultipleTestingAdapter(
        check_manifest=check_manifest,
        adapter_manifest=adapter_manifest,
        complete_operand=candidate.operand,
        none_operand=CanonicalOperand.scalar(adapter_v1.NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(
            adapter_v1.STRICT_SUBSET_FAMILY_CORRECTION_OPERAND
        ),
        role_bindings=adapter_v1.MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    assert check_manifest.to_dict() == manifest_value
    assert check_manifest.manifest_digest == stored["manifest_digest"]
    assert adapter_manifest.to_dict() == adapter_value
    return ScientificCheckModule(
        manifest=check_manifest,
        declared_manifest_digest=check_manifest.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _historical_v1_registry(lock: dict[str, Any]) -> ScientificCheckRegistry:
    module = _historical_v1_module(lock)
    return ScientificCheckRegistry(
        modules=(module,),
        development_modules=(module,),
    )


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("ebbb8a5dbc2664257144", "authorized-reader-lineage-unavailable"),
        ("104493a5d99796a002c0", "test-battery-cardinality-unresolved"),
        ("3ff45fce2a45e0959fdb", "test-battery-cardinality-unresolved"),
        ("7296b0e2cf7faeefca64", "test-battery-cardinality-unresolved"),
        ("c51d08801b3d0ba4e532", "analysis-scope-structure-unsupported"),
        ("f4cf62caeb8ad68dc5b3", "analysis-scope-structure-unsupported"),
        ("cb2e207276a0dc3247bb", "helper-call-site-reentry-unsupported"),
        ("9be74afbe9659bd50580", "test-battery-cardinality-unresolved"),
        ("b787314c170f8f690060", "test-battery-cardinality-unresolved"),
        ("60f96fabb7129d662b23", "extra-registered-test-outside-authorized-family"),
        ("8d83210468ecde012e4a", "test-battery-cardinality-unresolved"),
        ("4907932548f745afe942", "authorized-family-test-census-incomplete"),
        ("6d2fdc67ab98bc0e0e6e", "statistics-api-imported-outside-analysis-py"),
        ("dfc9f20a94ecefc7f7b5", "analysis-scope-structure-unsupported"),
        ("e1bce32a32e3b2df475e", "test-battery-cardinality-unresolved"),
    ],
)
def test_opened_e10_public_adapter_oracle_and_replay(
    case_id: str, expected: str, schema_root: Path, tmp_path: Path
) -> None:
    source_case = _ROOT / "cases" / case_id
    project = tmp_path / "project"
    shutil.copytree(source_case / "project", project)
    (project / "auditor-task.txt").write_bytes((source_case / "PROMPT.txt").read_bytes())
    profile: dict[str, Any] = json.loads(
        (source_case / "profile_1_2_0.json").read_text(encoding="utf-8")
    )
    material_path = profile["semantic_role_authority"]["authorized_test_family"][
        "material_input_path"
    ]
    contract = tmp_path / "contract"
    run_method_contract(
        project,
        "auditor-task.txt",
        contract,
        schema_root,
        profile=profile,
        actor_id="human:e10-replay",
        created_at="2026-08-25T00:00:00Z",
    )
    audit = tmp_path / "audit"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=(material_path,),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    module = next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == _CHECK_ID
    )
    assert module["state"] == "unsupported"
    assert module["observations"][0]["abstention_reason"] == expected
    assert [
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-code-csv-multiple-testing-conflict"
    ] == []
    assert bundle["findings"] == []

    replayed = replay(audit / "semantic.lock.json", tmp_path / "replay", schema_root)
    replay_lock = json.loads(
        (tmp_path / "replay" / "semantic.lock.json").read_text(encoding="utf-8")
    )
    replay_module = next(
        item
        for item in replay_lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == _CHECK_ID
    )
    assert canonical_json(replay_module) == canonical_json(module)
    assert replayed["findings"] == []


def test_historical_e10_artifact_anchor_is_immutable() -> None:
    expected = {
        "AUDIT_RESULTS.json": "sha256:6bfd70dda4d7977b1ad3e1729722179f03381714c7fef74e9781091752ca6b5b",
        "ROLE_MAP.json": "sha256:ced43841cb53e3527812e6dc5b4e361e635ca77fc7ca64129cae80d5c226c648",
        "ENVELOPE_MANIFEST.json": "sha256:a0223468c9ee76d07cb5717f975c4a0e34ec9c44ad64f674ea671c14f5020af2",
    }
    for name, digest in expected.items():
        assert sha256_digest((_ROOT / name).read_bytes()) == digest

    audit = json.loads((_ROOT / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    for item in audit["cases"]:
        case = _ROOT / "cases" / item["case_id"]
        first = json.loads((case / "audit-run-1" / "semantic.lock.json").read_text())
        second = json.loads((case / "audit-run-2" / "semantic.lock.json").read_text())
        first_module = next(
            value
            for value in first["scientific_check_registry"]["evaluation"]["modules"]
            if value["check_id"] == _CHECK_ID
        )
        second_module = next(
            value
            for value in second["scientific_check_registry"]["evaluation"]["modules"]
            if value["check_id"] == _CHECK_ID
        )
        assert first_module["module_evaluation_digest"] == second_module["module_evaluation_digest"]


def test_frozen_v1_adapter_replays_all_historical_e10_module_bytes(
    schema_root: Path,
) -> None:
    assert sha256_digest(Path(dataflow_v1.__file__).read_bytes()) == (
        "sha256:44a4ad39dbcb2c37a2b3532bf0dc85c7144199fb71094a312b55ab8ddf900b1a"
    )
    assert sha256_digest(Path(adapter_v1.__file__).read_bytes()) == (
        "sha256:3e8b474432d4c1d7ea1471f7dce4aec42dac4921380ebaf5110d978d62e90aa2"
    )
    assert BoundedCodeCsvMultipleTestingConflictV1Detector.implementation_digest() == (
        "sha256:76d7ec5c6ca0a44e2a0842adbfac7494af09429f3ddf20ed6a161f3da212124b"
    )
    assert (
        sha256_digest(
            Path("docs/implementation/MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md").read_bytes()
        )
        == _CURRENT_V1_DESIGN_DIGEST
    )
    custody = json.loads((_ROOT / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    assert _HISTORICAL_E10_DESIGN_DIGEST in custody["design"]

    for case_record in custody["cases"]:
        case = _ROOT / "cases" / case_record["case_id"]
        first_lock = json.loads(
            (case / "audit-run-1" / "semantic.lock.json").read_text(encoding="utf-8")
        )
        second_lock = json.loads(
            (case / "audit-run-2" / "semantic.lock.json").read_text(encoding="utf-8")
        )
        context = build_frozen_inspection_context(
            snapshot_root=case / "audit-run-1" / "observed" / "snapshot" / "materialized",
            snapshot_digest=first_lock["snapshot_digest"],
            file_records=first_lock["file_records"],
            asset_identities=first_lock["asset_identities"],
            parser_results=first_lock["parser_results"],
            operations=first_lock["operations"],
            artifacts=first_lock["artifacts"],
            publication_surface=first_lock["publication_surfaces"][0],
            repository_snapshot=first_lock["repository_snapshot"],
            executions=first_lock["executions"],
            environments=first_lock["environments"],
            scope_selections=first_lock["scope_selections"],
            selection_evidence_records=first_lock["material_questions"],
        )
        assert context is not None
        registry = _historical_v1_registry(first_lock)
        context = preflight_frozen_scientific_requirement(
            lock_path=case / "method-contract" / "semantic.lock.json",
            schema_root=schema_root,
            context=context,
            file_records=first_lock["file_records"],
            asset_identities=first_lock["asset_identities"],
            scientific_check_registry=registry,
            scientific_check_lane="development",
        )
        actual_module = registry.evaluate(context, lane="development").modules[0].to_dict()
        first_expected = next(
            item
            for item in first_lock["scientific_check_registry"]["evaluation"]["modules"]
            if item["check_id"] == _CHECK_ID
        )
        second_expected = next(
            item
            for item in second_lock["scientific_check_registry"]["evaluation"]["modules"]
            if item["check_id"] == _CHECK_ID
        )
        actual_bytes = canonical_json(actual_module).encode("utf-8")
        assert actual_bytes == canonical_json(first_expected).encode("utf-8")
        assert actual_bytes == canonical_json(second_expected).encode("utf-8")
