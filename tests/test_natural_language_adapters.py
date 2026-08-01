from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
    ScientificCheckRegistry,
)
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_checks.registry import ModuleEvaluation
from sc_referee.scientific_checks.scope_joins import build_static_scope_join_graph
from sc_referee.scientific_checks.selected_report_adapter import SelectedReportMethodAdapter

CORPUS_ROOT = Path(__file__).resolve().parents[1] / "evaluation" / "natural-language-adapter-v1"
DIRECT_STANDARDIZATION_CHECK = "check:direct-standardization-conditioning-set"
PULSE_EXPOSURE_CHECK = "check:full-map-ancestry-exposure"
COPY_DOSAGE_CHECK = "check:classifier-derived-copy-dosage-representation"


def _manifest() -> dict[str, Any]:
    value = json.loads((CORPUS_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _case(case_id: str) -> tuple[dict[str, Any], str]:
    case = next(item for item in _manifest()["cases"] if item["case_id"] == case_id)
    path = CORPUS_ROOT / case["path"]
    return case, path.read_text(encoding="utf-8")


def _context(report_text: str) -> FrozenInspectionContext:
    report = report_text.encode("utf-8")
    snapshot_digest = sha256_digest("natural-language-adapter-snapshot")
    surface_ref = RecordRef("publication_surface", "publication-surface:natural-language")
    artifact_ref = RecordRef("artifact", "artifact:natural-language-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:natural-language-report")
    file_ref = RecordRef("file_record", "file:natural-language-report")
    parser_ref = RecordRef("parser_result", "parser-result:natural-language-report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:natural-language")
    parser = canonical_json(
        {
            "parser_id": "parser:markdown-inventory",
            "parser_version": "0.2.0",
            "state": "parsed",
        }
    ).encode("utf-8")
    records = (
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        (
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": artifact_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": sha256_digest(report),
                },
            },
        ),
        (snapshot_ref, {"snapshot_id": snapshot_ref.record_id}),
        (file_ref, {"file_record_id": file_ref.record_id, "path": "report.md"}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
    )
    context = FrozenInspectionContext(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="report.md",
                file_ref=file_ref,
                content=report,
                content_digest=sha256_digest(report),
                media_type="text/markdown",
                parser_result_ref=parser_ref,
                parser_result_payload=parser,
                parser_result_digest=sha256_digest(parser),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
    )
    graph = build_static_scope_join_graph(
        snapshot_digest=snapshot_digest,
        snapshot_ref=snapshot_ref,
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=context.documents,
        base_records=context.base_records,
    )
    return replace(context, scope_join_graph=graph)


def _module(report_text: str, check_id: str) -> ModuleEvaluation:
    evaluation = default_scientific_check_registry().evaluate(_context(report_text))
    return next(item for item in evaluation.modules if item.check_id == check_id)


def _audit(
    root: Path,
    schema_root: Path,
    *,
    report_text: str,
    registry: ScientificCheckRegistry | None = None,
) -> dict[str, Any]:
    repository = root / "repository"
    repository.mkdir(parents=True)
    (repository / "report.md").write_text(report_text, encoding="utf-8")
    (repository / "analysis.py").write_text("descriptive_value = 1\n", encoding="utf-8")
    return run_audit(
        repository,
        root / "audit",
        schema_root,
        report="report.md",
        scientific_check_registry=registry or default_scientific_check_registry(),
    )


def _scientific_question_ids(bundle: dict[str, Any]) -> set[str]:
    return {
        str(item["extensions"]["x-scientific-check-id"])
        for item in bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
    }


def test_frozen_natural_language_corpus_identity_and_authority_ceiling() -> None:
    manifest = _manifest()
    projection = copy.deepcopy(manifest)
    recorded_digest = projection.pop("manifest_digest")

    assert manifest["qualification_use_permitted"] is False
    assert semantic_digest(projection) == recorded_digest
    assert len(manifest["cases"]) == 3
    for case in manifest["cases"]:
        path = CORPUS_ROOT / case["path"]
        assert path.is_file()
        assert sha256_digest(path.read_bytes()) == case["content_digest"]
        assert case["benchmark_derived"] is True
        assert case["qualification_status"] == "excluded"
        assert case["origin_report_digest"].startswith("sha256:")


@pytest.mark.parametrize(
    ("case_id", "check_id", "state", "operand"),
    [
        (
            "natural-language:carrier-poststrata:positive",
            DIRECT_STANDARDIZATION_CHECK,
            "applicable",
            "include_named_availability_variables_in_direct_standardization_cells",
        ),
        (
            "natural-language:popgen-called-exposure:positive",
            PULSE_EXPOSURE_CHECK,
            "applicable",
            "high_confidence_called_tract_exposure_only",
        ),
        (
            "natural-language:structural-dosage-unlinked:close-negative",
            COPY_DOSAGE_CHECK,
            "unsupported",
            None,
        ),
    ],
)
def test_frozen_natural_language_adapter_conformance(
    case_id: str,
    check_id: str,
    state: str,
    operand: str | None,
) -> None:
    _, text = _case(case_id)
    module = _module(text, check_id)

    assert module.state == state
    observed = [
        item.observed_operand.value for item in module.observations if item.observed_operand
    ]
    assert observed == ([operand] if operand is not None else [])


@pytest.mark.parametrize(
    ("case_id", "check_id", "mutation"),
    [
        (
            "natural-language:carrier-poststrata:positive",
            DIRECT_STANDARDIZATION_CHECK,
            (
                "is weighted by that cell's share of all 250 ancestry-specific roster rows",
                "was tabulated across all 250 ancestry-specific roster rows without a stated "
                "target weight",
            ),
        ),
        (
            "natural-language:popgen-called-exposure:positive",
            PULSE_EXPOSURE_CHECK,
            (
                "were omitted from ancestry exposure",
                "were listed for QC but their exposure handling was not specified",
            ),
        ),
    ],
)
def test_wording_mutation_removes_one_required_premise(
    case_id: str,
    check_id: str,
    mutation: tuple[str, str],
) -> None:
    case, text = _case(case_id)
    mutated = text.replace(*mutation)

    assert mutated != text
    assert sha256_digest(mutated) != case["content_digest"]
    module = _module(mutated, check_id)
    assert module.state == "unsupported"
    assert all(item.observed_operand is None for item in module.observations)


@pytest.mark.parametrize(
    ("case_id", "check_id", "conflict"),
    [
        (
            "natural-language:carrier-poststrata:positive",
            DIRECT_STANDARDIZATION_CHECK,
            (
                "Completed partners were analyzed by ancestry and family-history tier and "
                "standardized to the full roster. Site and wave were testing-selection "
                "variables, not biological risk predictors.\n"
            ),
        ),
        (
            "natural-language:popgen-called-exposure:positive",
            PULSE_EXPOSURE_CHECK,
            (
                "Transition exposure used the complete chromosome-map length, so pulse timing "
                "used t = N_switch / (2 m (1-m) L_map).\n"
            ),
        ),
    ],
)
def test_competing_natural_declarations_remain_ambiguous(
    case_id: str,
    check_id: str,
    conflict: str,
) -> None:
    _, text = _case(case_id)
    module = _module(f"{text}\n\n{conflict}", check_id)

    assert module.state == "ambiguous"


@pytest.mark.parametrize(
    ("case_id", "removed_check_id"),
    [
        ("natural-language:carrier-poststrata:positive", DIRECT_STANDARDIZATION_CHECK),
        ("natural-language:popgen-called-exposure:positive", PULSE_EXPOSURE_CHECK),
    ],
)
def test_adapter_removal_is_sibling_isolated(case_id: str, removed_check_id: str) -> None:
    _, text = _case(case_id)
    context = _context(text)
    full_registry = default_scientific_check_registry()
    reduced_registry = ScientificCheckRegistry(
        modules=tuple(
            item for item in full_registry.modules if item.manifest.check_id != removed_check_id
        ),
        unavailable_manifests=full_registry.unavailable_manifests,
        method_conflict_bindings=tuple(
            item
            for item in full_registry.method_conflict_bindings
            if item.check_id != removed_check_id
        ),
    )
    full = {
        item.check_id: canonical_json(item.to_dict())
        for item in full_registry.evaluate(context).modules
        if item.check_id != removed_check_id
    }
    reduced = {
        item.check_id: canonical_json(item.to_dict())
        for item in reduced_registry.evaluate(context).modules
    }

    assert reduced == full


@pytest.mark.parametrize(
    ("case_id", "check_id"),
    [
        ("natural-language:carrier-poststrata:positive", DIRECT_STANDARDIZATION_CHECK),
        ("natural-language:popgen-called-exposure:positive", PULSE_EXPOSURE_CHECK),
    ],
)
def test_missing_publication_scope_counterevidence_abstains(case_id: str, check_id: str) -> None:
    _, text = _case(case_id)
    context = replace(_context(text), scope_join_graph=None)
    evaluation = default_scientific_check_registry().evaluate(context)
    module = next(item for item in evaluation.modules if item.check_id == check_id)

    assert module.state == "unsupported"
    assert all(item.observed_operand is None for item in module.observations)


@pytest.mark.parametrize(
    ("case_id", "expected_question_ids"),
    [
        (
            "natural-language:carrier-poststrata:positive",
            {DIRECT_STANDARDIZATION_CHECK},
        ),
        (
            "natural-language:popgen-called-exposure:positive",
            {PULSE_EXPOSURE_CHECK},
        ),
        (
            "natural-language:structural-dosage-unlinked:close-negative",
            set(),
        ),
    ],
)
def test_corpus_level_question_and_finding_ceiling(
    tmp_path: Path,
    schema_root: Path,
    case_id: str,
    expected_question_ids: set[str],
) -> None:
    _, text = _case(case_id)
    bundle = _audit(tmp_path, schema_root, report_text=text)
    lock = json.loads((tmp_path / "audit" / "semantic.lock.json").read_text(encoding="utf-8"))

    assert _scientific_question_ids(bundle) == expected_question_ids
    assert bundle["findings"] == []
    assert bundle["executions"] == []
    assert bundle["project_execution_authorizations"] == []
    assert bundle["performance_records"][0]["model_usage"]["calls"] == 0
    assert lock["model_access_after_lock"] is False

    replayed = replay(tmp_path / "audit" / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "semantic_assertions",
        "material_questions",
        "disclosures",
        "findings",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]


def test_adapter_grammars_do_not_depend_on_corpus_identity() -> None:
    manifest = _manifest()
    forbidden = {
        str(value)
        for case in manifest["cases"]
        for key, value in case.items()
        if key in manifest["adapter_identity_keys_forbidden"] and value is not None
    }
    registry = default_scientific_check_registry()
    grammar = canonical_json(
        [
            {
                "check_id": module.manifest.check_id,
                "adapters": [
                    {
                        "adapter_id": adapter.adapter_id,
                        "rules": [item.to_dict() for item in adapter.rules],
                        "triggers": list(adapter.trigger_patterns),
                    }
                    for adapter in module.adapters
                    if isinstance(adapter, SelectedReportMethodAdapter)
                ],
            }
            for module in registry.modules
            if module.manifest.check_id in {DIRECT_STANDARDIZATION_CHECK, PULSE_EXPOSURE_CHECK}
        ]
    )

    assert all(value not in grammar for value in forbidden)
    assert "0.23952115899731413" not in grammar
    assert "10.866334" not in grammar


def test_frozen_corpus_manifest_mutation_is_detectable() -> None:
    manifest = _manifest()
    mutated = copy.deepcopy(manifest)
    recorded_digest = mutated.pop("manifest_digest")
    mutated["cases"][0]["expected_operand"] = "mutated_operand"

    assert semantic_digest(mutated) != recorded_digest
