from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from sc_referee.capability_matrix import (
    CapabilityMatrixError,
    default_capability_manifest_root,
    generate_capability_matrix,
    load_capability_detector_manifest,
    validate_capability_matrix,
    write_capability_matrix,
)
from sc_referee.cli import app
from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import canonical_json, sha256_digest
from scripts.build_capability_source_manifests import _upsert


def _schema_root(project_root: Path) -> Path:
    return project_root / "reference" / "schemas-v0.20.0"


def _write_canonical(path: Path, value: object) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _rebind_collection(root: Path, kind: str, value: dict[str, object]) -> None:
    manifest_set = _load(root / "manifest-set.json")
    descriptors = manifest_set["collections"]
    assert isinstance(descriptors, list)
    descriptor = next(item for item in descriptors if item["kind"] == kind)
    path = root / str(descriptor["path"])
    _write_canonical(path, value)
    descriptor["digest"] = sha256_digest(path.read_bytes())
    _write_canonical(root / "manifest-set.json", manifest_set)


def _copied_manifest_root(tmp_path: Path) -> Path:
    target = tmp_path / "manifests"
    shutil.copytree(default_capability_manifest_root(), target)
    return target


def test_code_detector_manifest_history_is_versioned_and_live_projection_is_latest(
    project_root: Path,
) -> None:
    root = default_capability_manifest_root()
    collection = _load(root / "detector-manifests.json")
    history = [
        item
        for item in collection["records"]
        if item["detector_id"] == "detector:bounded-code-csv-dependence-conflict"
    ]
    assert [item["detector_version"] for item in history] == [
        "1.0.0",
        "1.1.0",
        "1.2.0",
        "1.3.0",
        "2.0.0",
        "2.1.0",
        "2.2.0",
        "2.3.0",
    ]
    assert [item["implementation"]["implementation_digest"] for item in history[:-1]] == [
        "sha256:e52a367ffb97ca6706d6d2cfd621f0283cb12d99d1483304142d365aad25f86e",
        "sha256:3b136e2dcb33023c3f9abc0eb962b8120cda836e74bf715fd8c7c5383799da57",
        "sha256:ab6e90b5496996f769cb4af0b5ab60082778f0adf4378b1bb127c63ffb81da14",
        "sha256:4d004c513761e382bbb49ea0633d1d7b3ee07f91cdba91adf837b48902d2f816",
        "sha256:261bfa27092c528cd86fb3905ced2fb1b2f296852f688ab4be3abaa94d57e901",
        "sha256:9c30154639e1fc013a0f82a5ee3d767202c121f42626b2c6497436e9305f2452",
        "sha256:f2aab5efb1e02d3bae88800dea31c1707644fb36b6de48abfb612e7f426f71be",
    ]
    live = load_capability_detector_manifest(
        root,
        _schema_root(project_root),
        "detector:bounded-code-csv-dependence-conflict",
    )
    assert live["detector_version"] == "2.3.0"
    assert live == history[-1]


def test_detector_upsert_keys_on_identity_and_version() -> None:
    collection: dict[str, Any] = {
        "records": [
            {"detector_id": "detector:a", "detector_version": "1.1.0", "value": 1},
            {"detector_id": "detector:a", "detector_version": "1.2.0", "value": 2},
        ]
    }
    _upsert(
        collection,
        "detector_id",
        {"detector_id": "detector:a", "detector_version": "1.2.0", "value": 3},
    )
    assert collection["records"] == [
        {"detector_id": "detector:a", "detector_version": "1.1.0", "value": 1},
        {"detector_id": "detector:a", "detector_version": "1.2.0", "value": 3},
    ]


def test_bundled_matrix_is_deterministic_and_publishes_only_live_binding_grants(
    project_root,
) -> None:
    root = default_capability_manifest_root()
    first = generate_capability_matrix(root, _schema_root(project_root))
    second = generate_capability_matrix(root, _schema_root(project_root))

    assert canonical_json(first) == canonical_json(second)
    assert first["domain_wide_support_claim_allowed"] is False
    assert len(first["entries"]) == 17
    assert first["generated_from_manifest_refs"] == [
        {
            "record_type": "detector_manifest",
            "record_id": "detector:bounded-analysis-method-conflict",
        },
        {
            "record_type": "detector_manifest",
            "record_id": "detector:bounded-code-csv-dependence-conflict",
        },
        {
            "record_type": "detector_manifest",
            "record_id": "detector:bounded-feature-identifier-identity",
        },
        {
            "record_type": "detector_manifest",
            "record_id": "detector:bounded-report-mean-direction",
        },
        {
            "record_type": "detector_manifest",
            "record_id": "detector:bounded-reported-method-contract-conflict",
        },
        {
            "record_type": "detector_qualification",
            "record_id": (
                "qualification:authorized-independent-unit-entry-v210-code-csv-envelope5"
            ),
        },
        {
            "record_type": "detector_qualification",
            "record_id": "qualification:complete-domain-exposure-denominator-v207-round2",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:container-cell-language-bridge",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:jupyter-notebook-inventory",
        },
        {"record_type": "parser_manifest", "record_id": "parser:markdown-inventory"},
        {
            "record_type": "parser_manifest",
            "record_id": "parser:nextflow-default-trace",
        },
        {"record_type": "parser_manifest", "record_id": "parser:python-ast-tokenize"},
        {
            "record_type": "parser_manifest",
            "record_id": "parser:quarto-source-inventory",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:r-base-parse-data",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:r-tree-sitter-inventory",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:rmarkdown-selected-report-inventory",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:selected-feature-identifier-axes",
        },
        {
            "record_type": "parser_manifest",
            "record_id": "parser:tabular-delimited-header-inventory",
        },
    ]
    detector_entry = next(
        entry
        for entry in first["entries"]
        if entry["entry_id"] == "capability:bounded-report-mean-direction-v1"
    )
    assert detector_entry["language"] is None
    assert detector_entry["detectors"] == [
        {
            "detector_id": "detector:bounded-report-mean-direction",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "disclosure",
        }
    ]
    assert any("cannot emit a production Finding" in gap for gap in detector_entry["known_gaps"])
    analysis_entry = next(
        entry
        for entry in first["entries"]
        if entry["entry_id"] == "capability:bounded-analysis-method-conflict-v1"
    )
    assert analysis_entry["language"] is None
    assert analysis_entry["detectors"] == [
        {
            "binding_grants": [
                {
                    "binding_id": (
                        "method-conflict-binding:complete-domain-exposure-denominator-v1"
                    ),
                    "check_id": "check:complete-domain-exposure-denominator",
                    "qualification_ref": (
                        "qualification:complete-domain-exposure-denominator-v207-round2"
                    ),
                    "strongest_output_type": "finding",
                },
            ],
            "detector_id": "detector:bounded-analysis-method-conflict",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "disclosure",
        }
    ]
    assert (
        sum(
            len(detector.get("binding_grants", []))
            for entry in first["entries"]
            for detector in entry["detectors"]
        )
        == 2
    )
    assert any("cannot emit a production Finding" in gap for gap in analysis_entry["known_gaps"])
    code_entry = next(
        entry
        for entry in first["entries"]
        if entry["entry_id"] == "capability:bounded-code-csv-dependence-conflict-v1"
    )
    assert code_entry["detectors"] == [
        {
            "binding_grants": [
                {
                    "binding_id": (
                        "method-conflict-binding:authorized-independent-unit-entry-into-"
                        "row-independent-procedure-v1"
                    ),
                    "check_id": (
                        "check:authorized-independent-unit-entry-into-row-independent-procedure"
                    ),
                    "qualification_ref": (
                        "qualification:authorized-independent-unit-entry-v210-code-csv-envelope5"
                    ),
                    "strongest_output_type": "finding",
                }
            ],
            "detector_id": "detector:bounded-code-csv-dependence-conflict",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "disclosure",
        }
    ]
    feature_entry = next(
        entry
        for entry in first["entries"]
        if entry["entry_id"] == "capability:bounded-feature-identifier-identity-v1"
    )
    assert feature_entry["language"] is None
    assert feature_entry["detectors"] == [
        {
            "detector_id": "detector:bounded-feature-identifier-identity",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "disclosure",
        }
    ]
    assert any("cannot emit a production Finding" in gap for gap in feature_entry["known_gaps"])
    method_entry = next(
        entry
        for entry in first["entries"]
        if entry["entry_id"] == "capability:bounded-expected-count-method-contract-v1"
    )
    assert method_entry["language"] == "markdown"
    assert method_entry["detectors"] == [
        {
            "detector_id": "detector:bounded-reported-method-contract-conflict",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "disclosure",
        }
    ]
    assert any("cannot emit a production Finding" in gap for gap in method_entry["known_gaps"])
    obligation_entry = next(
        entry
        for entry in first["entries"]
        if entry["entry_id"] == "capability:bounded-expected-count-unresolved-obligation-v1"
    )
    assert obligation_entry["language"] == "markdown"
    assert obligation_entry["detectors"] == []
    assert obligation_entry["operation_scope"] == [
        "bounded_expected_count_unresolved_obligation_v1"
    ]
    assert any("MaterialQuestion" in gap for gap in obligation_entry["known_gaps"])
    assert not any(
        operation == "bounded_expected_count_unresolved_obligation_v1"
        for operation in method_entry["operation_scope"]
    )

    for entry in first["entries"]:
        assert entry["domain_wide_validation_claim_allowed"] is False
        assert entry["tested_versions"] == []
        assert entry["inferred_compatibility"] == []
        if any(
            entry is candidate
            for candidate in (
                analysis_entry,
                code_entry,
                detector_entry,
                feature_entry,
                method_entry,
            )
        ):
            continue
        assert entry["detectors"] == []
        assert any(
            "no detector-dependent issue class was checked" in gap for gap in entry["known_gaps"]
        )
        assert any(
            "Detector-dependent assessment is unavailable" in item
            for item in entry["abstention_conditions"]
        )

    delimited = next(entry for entry in first["entries"] if entry["language"] == "delimited_table")
    assert delimited["syntax_recognition"] == "partial"
    assert delimited["operation_extraction"] == "not_started"
    assert delimited["semantic_modeling"] == "not_started"
    assert delimited["operation_scope"] == ["bounded_delimited_header_inventory_v1"]

    trace = next(entry for entry in first["entries"] if entry["language"] == "nextflow_trace")
    assert trace["syntax_recognition"] == "partial"
    assert trace["operation_extraction"] == "not_started"
    assert trace["semantic_modeling"] == "not_started"
    assert trace["operation_scope"] == ["bounded_imported_terminal_task_trace_v1"]
    assert any("weak external assertions" in gap for gap in trace["known_gaps"])

    rmarkdown = next(entry for entry in first["entries"] if entry["language"] == "r_markdown")
    assert rmarkdown["syntax_recognition"] == "partial"
    assert rmarkdown["operation_extraction"] == "not_started"
    assert rmarkdown["semantic_modeling"] == "not_started"
    assert rmarkdown["operation_scope"] == ["bounded_rmarkdown_source_chunk_inventory_v2"]
    assert any("question-only" in gap for gap in rmarkdown["known_gaps"])

    r_profiles = {entry["package"]: entry for entry in first["entries"] if entry["language"] == "r"}
    assert set(r_profiles) == {"DESeq2", "edgeR", "limma"}
    assert all(
        entry["domain"] == "bulk_rna_seq_differential_expression"
        and entry["syntax_recognition"] == "partial"
        and entry["operation_extraction"] == "partial"
        and entry["semantic_modeling"] == "not_started"
        and entry["detectors"] == []
        for entry in r_profiles.values()
    )
    assert r_profiles["DESeq2"]["operation_scope"] == [
        "r_literal_call_deseqdatasetfrommatrix_v1",
        "r_literal_call_deseq_v1",
        "r_literal_call_results_v1",
    ]
    assert r_profiles["edgeR"]["operation_scope"] == [
        "r_literal_call_dgelist_v1",
        "r_literal_call_filterbyexpr_v1",
        "r_literal_call_glmqlfit_v1",
        "r_literal_call_glmqlftest_v1",
    ]
    assert r_profiles["limma"]["operation_scope"] == [
        "r_literal_call_dgelist_v1",
        "r_literal_call_filterbyexpr_v1",
        "r_literal_call_calcnormfactors_v1",
        "r_literal_call_voom_v1",
        "r_literal_call_lmfit_v1",
        "r_literal_call_ebayes_v1",
        "r_literal_call_toptable_v1",
    ]
    assert all(entry["tested_versions"] == [] for entry in r_profiles.values())
    assert all(entry["inferred_compatibility"] == [] for entry in r_profiles.values())

    notebook = next(entry for entry in first["entries"] if entry["language"] == "jupyter_notebook")
    assert notebook["entry_id"] == "capability:jupyter-notebook-inventory-v1"
    assert notebook["domain"] == "domain_neutral_scientific_analysis"
    assert notebook["operation_scope"] == ["bounded_nbformat4_cell_output_inventory_v1"]
    assert notebook["syntax_recognition"] == "partial"
    assert notebook["operation_extraction"] == "not_started"
    assert notebook["semantic_modeling"] == "not_started"
    assert notebook["detectors"] == []
    assert notebook["tested_versions"] == []
    assert notebook["inferred_compatibility"] == []

    quarto = next(entry for entry in first["entries"] if entry["language"] == "quarto")
    assert quarto["entry_id"] == "capability:quarto-source-inventory-v1"
    assert quarto["domain"] == "domain_neutral_scientific_analysis"
    assert quarto["operation_scope"] == ["bounded_quarto_source_cell_inventory_v1"]
    assert quarto["syntax_recognition"] == "partial"
    assert quarto["operation_extraction"] == "not_started"
    assert quarto["semantic_modeling"] == "not_started"
    assert quarto["detectors"] == []
    assert quarto["tested_versions"] == []
    assert quarto["inferred_compatibility"] == []

    bridge = next(entry for entry in first["entries"] if entry["language"] == "container_cell")
    assert bridge["entry_id"] == "capability:container-cell-static-language-bridge-v1"
    assert bridge["operation_extraction"] == "partial"
    assert bridge["semantic_modeling"] == "not_started"
    assert bridge["detectors"] == []
    assert bridge["tested_versions"] == []
    assert bridge["inferred_compatibility"] == []
    assert "bounded_container_cell_static_language_bridge_v2" in bridge["operation_scope"]

    parser_collection = _load(root / "parser-manifests.json")
    bridge_parser = next(
        record
        for record in parser_collection["records"]
        if record["parser_id"] == "parser:container-cell-language-bridge"
    )
    assert bridge_parser["executes_project_code"] is False
    assert bridge_parser["parser_version"] == "0.2.0"
    r_parsers = {
        record["parser_id"]: record
        for record in parser_collection["records"]
        if record["language_or_surface"] == "r"
    }
    assert set(r_parsers) == {
        "parser:r-base-parse-data",
        "parser:r-tree-sitter-inventory",
    }
    assert r_parsers["parser:r-base-parse-data"]["backend"] == "base_r_parse_data"
    assert r_parsers["parser:r-tree-sitter-inventory"]["backend"] == "tree_sitter_r"
    assert all(record["executes_project_code"] is False for record in r_parsers.values())
    assert len({record["implementation_digest"] for record in r_parsers.values()}) == 1
    supported = {
        version
        for record in parser_collection["records"]
        for version in record["supported_versions"]
    }
    published_versions = {
        version
        for entry in first["entries"]
        for field in ("tested_versions", "inferred_compatibility")
        for version in entry[field]
    }
    assert supported
    assert published_versions.isdisjoint(supported)


def test_manifest_digest_canonicalization_and_reference_mutations_fail_closed(
    project_root, tmp_path
) -> None:
    schema_root = _schema_root(project_root)

    digest_root = _copied_manifest_root(tmp_path / "digest")
    with (digest_root / "profile-manifests.json").open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(CapabilityMatrixError, match="digest mismatch"):
        generate_capability_matrix(digest_root, schema_root)

    canonical_root = _copied_manifest_root(tmp_path / "canonical")
    profiles = _load(canonical_root / "profile-manifests.json")
    profile_path = canonical_root / "profile-manifests.json"
    profile_path.write_text(json.dumps(profiles, indent=2) + "\n", encoding="utf-8")
    manifest_set = _load(canonical_root / "manifest-set.json")
    descriptor = next(
        item for item in manifest_set["collections"] if item["kind"] == "profile_manifests"
    )
    descriptor["digest"] = sha256_digest(profile_path.read_bytes())
    _write_canonical(canonical_root / "manifest-set.json", manifest_set)
    with pytest.raises(CapabilityMatrixError, match="canonical JSON"):
        generate_capability_matrix(canonical_root, schema_root)

    reference_root = _copied_manifest_root(tmp_path / "reference")
    profiles = _load(reference_root / "profile-manifests.json")
    profiles["records"][0]["parser_refs"][0]["record_id"] = "parser:missing"
    _rebind_collection(reference_root, "profile_manifests", profiles)
    with pytest.raises(CapabilityMatrixError, match="unresolved parser"):
        generate_capability_matrix(reference_root, schema_root)


def test_experimental_detector_has_no_qualification_or_finding_permission(
    project_root, tmp_path
) -> None:
    root = _copied_manifest_root(tmp_path)
    example = _load(_schema_root(project_root) / "examples" / "detector-manifest.example.json")
    detector = deepcopy(example)
    detector.update(
        {
            "detector_id": "detector:bounded-static-development-only",
            "detector_version": "0.2.0",
            "maturity": "experimental",
            "domains": ["domain_neutral_scientific_analysis"],
            "languages": ["python"],
            "supported_operations": [
                "bounded_literal_filter_predicates",
                "bounded_literal_two_group_mean_difference",
                "bounded_linear_single_result_renderer_lineage",
                "python_ast_and_token_inventory",
                "static_literal_and_source_parent_relative_write_paths_v2",
            ],
            "package_constraints": [],
            "permitted_output_types": [
                "conditional_concern",
                "material_question",
                "disclosure",
            ],
            "validation": {"status": "development_only"},
        }
    )
    detectors = _load(root / "detector-manifests.json")
    detectors["records"].append(detector)
    detectors["records"].sort(key=lambda item: item["detector_id"])
    _rebind_collection(root, "detector_manifests", detectors)
    profiles = _load(root / "profile-manifests.json")
    python_profile = next(
        item
        for item in profiles["records"]
        if item["profile_id"] == "semantic-profile:python-bounded-static-inspection-v1"
    )
    python_profile["detector_refs"] = [
        {
            "record_type": "detector_manifest",
            "record_id": "detector:bounded-static-development-only",
        }
    ]
    _rebind_collection(root, "profile_manifests", profiles)

    matrix = generate_capability_matrix(root, _schema_root(project_root))
    entry = next(
        item
        for item in matrix["entries"]
        if item["entry_id"] == "capability:python-bounded-static-inspection-v1"
    )
    assert entry["detectors"] == [
        {
            "detector_id": "detector:bounded-static-development-only",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "conditional_concern",
        }
    ]


def test_write_validate_cli_and_no_replace(project_root, tmp_path) -> None:
    schema_root = _schema_root(project_root)
    output = tmp_path / "capability-matrix.json"
    first = write_capability_matrix(output, default_capability_manifest_root(), schema_root)
    assert (
        validate_capability_matrix(output, default_capability_manifest_root(), schema_root) == first
    )
    with pytest.raises(FileExistsError):
        write_capability_matrix(output, default_capability_manifest_root(), schema_root)

    tampered = tmp_path / "tampered.json"
    changed = deepcopy(first)
    changed["entries"][0]["known_gaps"].append("Unbound added claim")
    _write_canonical(tampered, changed)
    with pytest.raises(CapabilityMatrixError, match="deterministic manifest projection"):
        validate_capability_matrix(tampered, default_capability_manifest_root(), schema_root)

    cli_output = tmp_path / "cli-matrix.json"
    runner = CliRunner()
    generated = runner.invoke(app, ["generate-capability-matrix", "--output", str(cli_output)])
    assert generated.exit_code == 0, generated.output
    validated = runner.invoke(app, ["validate-capability-matrix", str(cli_output)])
    assert validated.exit_code == 0, validated.output
    assert json.loads(validated.output) == first


def test_new_capability_claim_mutations_do_not_validate(project_root, tmp_path) -> None:
    root = default_capability_manifest_root()
    schema_root = _schema_root(project_root)
    original = generate_capability_matrix(root, schema_root)
    r_index = next(
        index
        for index, entry in enumerate(original["entries"])
        if entry["entry_id"] == "capability:r-deseq2-call-inventory-v1"
    )
    mutations = []
    changed_scope = deepcopy(original)
    changed_scope["entries"][r_index]["operation_scope"] = ["all_deseq2_operations"]
    mutations.append(changed_scope)
    invented_version = deepcopy(original)
    invented_version["entries"][r_index]["tested_versions"] = ["DESeq2 99.0"]
    mutations.append(invented_version)
    invented_detector = deepcopy(original)
    invented_detector["entries"][r_index]["detectors"] = [
        {
            "detector_id": "detector:invented-r-correctness",
            "maturity": "experimental",
            "qualification_ref": None,
            "review_basis": "not_qualified",
            "strongest_output_type": "disclosure",
        }
    ]
    mutations.append(invented_detector)
    widened_domain = deepcopy(original)
    widened_domain["entries"][r_index]["domain_wide_validation_claim_allowed"] = True
    mutations.append(widened_domain)
    notebook_scope = deepcopy(original)
    notebook_index = next(
        index
        for index, entry in enumerate(original["entries"])
        if entry["entry_id"] == "capability:jupyter-notebook-inventory-v1"
    )
    notebook_scope["entries"][notebook_index]["operation_extraction"] = (
        "complete_for_declared_forms"
    )
    mutations.append(notebook_scope)
    quarto_scope = deepcopy(original)
    quarto_index = next(
        index
        for index, entry in enumerate(original["entries"])
        if entry["entry_id"] == "capability:quarto-source-inventory-v1"
    )
    quarto_scope["entries"][quarto_index]["semantic_modeling"] = "complete_for_declared_forms"
    mutations.append(quarto_scope)

    for index, mutation in enumerate(mutations):
        path = tmp_path / f"mutated-{index}.json"
        _write_canonical(path, mutation)
        with pytest.raises((CapabilityMatrixError, RecordValidationError)):
            validate_capability_matrix(path, root, schema_root)
