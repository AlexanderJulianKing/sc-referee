from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.corpus import (
    GENEBENCH_PUBLIC_SOURCE_URI,
    CorpusPreflightError,
    preflight_genebench_public_package,
)
from sc_referee_evaluation.genebench_grader import (
    GeneBenchNumericGradeError,
    grade_genebench_public_answer,
    grade_genebench_public_numeric_answer,
)
from sc_referee_evaluation.genebench_workspace import (
    GeneBenchWorkspaceError,
    prepare_genebench_public_case,
)

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id

_REVISION = "8bb6cde6ab0b0554e867c46f5698fd953bf2c68a"
_SECRET_ANSWER = "SECRET-ANSWER-DO-NOT-DISCLOSE"


def _write_public_package(
    root: Path,
    *,
    metadata_license: str = "cc-by-4.0",
    license_identifier: str = "MIT",
    numeric_contract: bool = False,
    bounded_numeric_contract: bool = False,
    minimum_only_numeric_contract: bool = False,
    composite_contract: bool = False,
    single_numeric_contract: bool = False,
    integer_composite_contract: bool = False,
) -> tuple[str, str]:
    problem_dir = root / "problems" / "synthetic_case"
    data_dir = problem_dir / "data_files"
    data_dir.mkdir(parents=True)
    (root / ".gitattributes").write_text("*.gz filter=lfs diff=lfs merge=lfs\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"---\nlicense: {metadata_license}\n---\n# Synthetic public package\n",
        encoding="utf-8",
    )
    license_text = (
        "MIT License\n\nCopyright (c) 2026 Test\n"
        if license_identifier == "MIT"
        else "Creative Commons Attribution 4.0 International\n"
    )
    (root / "LICENSE").write_text(license_text, encoding="utf-8")
    (root / "problems.csv").write_text("id\nsynthetic_case\n", encoding="utf-8")
    (root / "reference_definitions.md").write_text("Reference definitions.\n", encoding="utf-8")
    (root / "reference_grader.py").write_text(
        "from pathlib import Path\nPath(__file__).with_name('EXECUTED').write_text('unsafe')\n",
        encoding="utf-8",
    )
    data_path = data_dir / "observations.tsv"
    data_path.write_text("sample\tvalue\nA\t1\n", encoding="utf-8")
    if integer_composite_contract:
        ground_truth = {"estimate_a": 1.25, "sample_count": 3, "support_code": 1}
        grader = {
            "type": "composite",
            "config": {
                "forbid_extra_keys": True,
                "strict_answer_schema": True,
                "integer_keys": {
                    "sample_count": {"min_value": 0},
                    "support_code": {"min_value": 0, "max_value": 1},
                },
                "numeric_keys": {"estimate_a": {"absolute_tolerance": 0.02}},
            },
        }
    elif composite_contract:
        ground_truth: dict[str, Any] = {"estimate_a": 1.25, "selected_group": "A"}
        grader = {
            "type": "composite",
            "config": {
                "exact_match_keys": {"selected_group": {"case_sensitive": True, "required": True}},
                "numeric_keys": {
                    "estimate_a": {
                        "absolute_tolerance": 0.02,
                        "min_value": -1.0,
                        "max_value": 2.0,
                        "required": True,
                    }
                },
            },
        }
    elif single_numeric_contract:
        ground_truth = {"estimate_a": 1.25}
        grader = {
            "type": "numeric_tolerance",
            "config": {
                "absolute_tolerance": 0.02,
                "answer_field": "answer",
                "key": "estimate_a",
            },
        }
    elif numeric_contract:
        ground_truth = {"estimate_a": 1.25, "estimate_b": -0.5}
        numeric_key_configs: dict[str, dict[str, Any]] = {
            "estimate_a": {"absolute_tolerance": 0.02},
            "estimate_b": {"absolute_tolerance": 0.05},
        }
        if bounded_numeric_contract:
            numeric_key_configs = {
                key: {**value, "min_value": -2.0, "max_value": 2.0}
                for key, value in numeric_key_configs.items()
            }
        elif minimum_only_numeric_contract:
            numeric_key_configs["estimate_b"] = {
                **numeric_key_configs["estimate_b"],
                "min_value": -2.0,
            }
        grader = {
            "type": "multi_numeric_tolerance",
            "config": {"keys": numeric_key_configs},
        }
    else:
        ground_truth = {"estimate": _SECRET_ANSWER}
        grader = {"type": "exact_match", "config": {"keys": ["estimate"]}}
    config = {
        "id": "synthetic_case",
        "eval_uuid": "f8a2c4e1-9b3d-4f7a-8c5e-2d1f0a3b6c9e",
        "task": "Estimate the declared quantity and return the required JSON object.",
        "data_files": ["data_files/observations.tsv"],
        "ground_truth": ground_truth,
        "grader": grader,
    }
    config_path = problem_dir / "eval_config.json"
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    report_path = problem_dir / "report_public.pdf"
    report_path.write_bytes(b"%PDF-1.4\nsynthetic runner-only report\n")
    manifest = {
        "name": "Synthetic GeneBench-Pro public case studies",
        "version": "2026-06-26",
        "description": "Synthetic package for preflight tests.",
        "problem_count": 1,
        "layout": {
            "problem_directories": "problems/<eval_id>/",
            "required_files_per_problem": [
                "eval_config.json",
                "data_files/",
                "report_public.pdf",
            ],
            "top_level_reference_files": [
                ".gitattributes",
                "README.md",
                "LICENSE",
                "problems.csv",
                "checksums.sha256",
                "manifest.json",
                "reference_definitions.md",
                "reference_grader.py",
            ],
        },
        "problems": [
            {
                "release_order": 0,
                "eval_id": "synthetic_case",
                "title": "Synthetic case",
                "domain": "Testing",
                "eval_uuid": config["eval_uuid"],
                "problem_dir": "problems/synthetic_case",
                "eval_config": "problems/synthetic_case/eval_config.json",
                "report": "problems/synthetic_case/report_public.pdf",
                "data_files": ["problems/synthetic_case/data_files/observations.tsv"],
                "grader_type": grader["type"],
                "answer_fields": sorted(ground_truth),
                "files": [
                    _manifest_file(root, config_path),
                    _manifest_file(root, report_path),
                    _manifest_file(root, data_path),
                ],
            }
        ],
    }
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    _rewrite_checksums(root)
    return _current_digests(root)


def _manifest_file(root: Path, path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _rewrite_checksums(root: Path) -> None:
    paths = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.name not in {"checksums.sha256", ".DS_Store", "EXECUTED"}
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    (root / "checksums.sha256").write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
            f"{path.relative_to(root).as_posix()}\n"
            for path in paths
        ),
        encoding="utf-8",
    )


def _current_digests(root: Path) -> tuple[str, str]:
    return (
        sha256_digest((root / "manifest.json").read_bytes()),
        sha256_digest((root / "checksums.sha256").read_bytes()),
    )


def _preflight(root: Path, output: Path | None = None) -> dict[str, Any]:
    manifest_digest, checksums_digest = _current_digests(root)
    return preflight_genebench_public_package(
        root,
        source_revision=_REVISION,
        expected_manifest_digest=manifest_digest,
        expected_checksums_digest=checksums_digest,
        output=output,
    )


def test_public_corpus_preflight_is_answer_blind_nonexecuting_and_public_only(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package)

    report = _preflight(package)

    assert report["corpus_preflight_version"] == "0.2.0"
    assert report["source"]["uri"] == GENEBENCH_PUBLIC_SOURCE_URI
    assert report["source"]["revision"] == _REVISION
    assert report["integrity"] == {
        "status": "verified",
        "checked_file_count": 10,
        "checked_byte_count": sum(
            path.stat().st_size
            for path in package.rglob("*")
            if path.is_file() and path.name != "checksums.sha256"
        ),
        "unexpected_file_count": 0,
        "ignored_platform_metadata_paths": [],
    }
    assert report["license"]["status"] == "conflicted_metadata_and_license_file"
    assert report["run_admission_status"] == "requires_human_license_resolution"
    assert report["corpus_partition_ceiling"] == "public_development"
    assert report["held_out_eligible"] is False
    assert report["promotion_evidence_eligible"] is False
    assert report["answer_side_artifact"] is True
    assert report["agent_workspace_eligible"] is False
    assert report["ground_truth_disclosed_to_agent_workspace"] is False
    assert report["project_code_executed"] is False
    assert report["model_invoked"] is False
    problem = report["problems"][0]
    assert problem["blind_workspace_plan"] == {
        "task_output_path": "task.md",
        "visible_data_paths": ["data_files/observations.tsv"],
        "answer_side_config_copied": False,
        "reference_report_copied": False,
        "reference_grader_copied": False,
        "project_code_execution_authorized": False,
    }
    serialized = json.dumps(report, sort_keys=True)
    assert _SECRET_ANSWER not in serialized
    assert not (package / "EXECUTED").exists()


def test_consistent_license_allows_only_public_development_preparation(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package, metadata_license="mit", license_identifier="MIT")

    report = _preflight(package)

    assert report["license"]["status"] == "consistent"
    assert report["run_admission_status"] == "admitted_for_public_development_preparation"
    assert report["held_out_eligible"] is False


def test_public_corpus_preflight_rejects_stale_license_inventory(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package, metadata_license="mit", license_identifier="MIT")
    manifest_digest, checksums_digest = _current_digests(package)
    (package / "LICENSE").write_text(
        "MIT License\n\nCopyright (c) 2026 Changed after inventory\n",
        encoding="utf-8",
    )

    with pytest.raises(CorpusPreflightError, match=r"LICENSE.*checksum drift"):
        preflight_genebench_public_package(
            package,
            source_revision=_REVISION,
            expected_manifest_digest=manifest_digest,
            expected_checksums_digest=checksums_digest,
        )


def test_cli_prepares_exact_answer_isolated_public_case(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package, metadata_license="mit", license_identifier="MIT")
    preflight = _preflight(package)
    preflight_path = tmp_path / "preflight.json"
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    output = tmp_path / "prepared-case"

    assert (
        evaluation_main(
            [
                "prepare-genebench-public-case",
                "--package-root",
                str(package),
                "--preflight",
                str(preflight_path),
                "--eval-id",
                "synthetic_case",
                "--created-at",
                "2026-07-29T18:00:00Z",
                "--output-root",
                str(output),
            ]
        )
        == 0
    )

    workspace = output / "workspace"
    assert sorted(
        path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()
    ) == ["data_files/observations.tsv", "task.md"]
    workspace_payload = b"\n".join(
        path.read_bytes() for path in workspace.rglob("*") if path.is_file()
    )
    assert _SECRET_ANSWER.encode() not in workspace_payload
    assert b"EXECUTED" not in workspace_payload
    assert not (package / "EXECUTED").exists()

    preparation = json.loads((output / "case-preparation.json").read_text(encoding="utf-8"))
    assert preparation["source"]["preflight_digest"] == preflight["preflight_digest"]
    assert preparation["corpus_partition"] == "public_development"
    assert preparation["held_out_eligible"] is False
    assert preparation["promotion_evidence_eligible"] is False
    assert preparation["ground_truth_disclosed_to_agent_workspace"] is False
    assert preparation["project_code_executed"] is False
    assert preparation["model_invoked"] is False
    assert preparation["workspace"]["visible_paths"] == [
        "data_files/observations.tsv",
        "task.md",
    ]
    manifest = json.loads((output / "workspace-manifest.json").read_text(encoding="utf-8"))
    assert manifest["answer_side_content_copied"] is False
    assert manifest["scanner"]["forbidden_path_count"] == 4


@pytest.mark.parametrize("mutation", ["preflight", "package"])
def test_public_case_preparation_rechecks_preflight_and_package(
    tmp_path: Path, mutation: str
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package, metadata_license="mit", license_identifier="MIT")
    preflight = _preflight(package)
    if mutation == "preflight":
        preflight["held_out_eligible"] = True
    else:
        (package / "problems/synthetic_case/data_files/observations.tsv").write_text(
            "sample\tvalue\nA\t999\n", encoding="utf-8"
        )
    output = tmp_path / "prepared-case"

    with pytest.raises(GeneBenchWorkspaceError):
        prepare_genebench_public_case(
            package,
            preflight,
            "synthetic_case",
            output,
            created_at="2026-07-29T18:00:00Z",
        )
    assert not output.exists()


def test_public_case_preparation_is_write_once(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package, metadata_license="mit", license_identifier="MIT")
    preflight = _preflight(package)
    output = tmp_path / "prepared-case"
    output.mkdir()

    with pytest.raises(GeneBenchWorkspaceError, match="already exists"):
        prepare_genebench_public_case(
            package,
            preflight,
            "synthetic_case",
            output,
            created_at="2026-07-29T18:00:00Z",
        )


def test_prepared_public_case_enters_static_audit_and_replay(
    tmp_path: Path, schema_root: Path
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package, metadata_license="mit", license_identifier="MIT")
    prepared = tmp_path / "prepared-case"
    prepare_genebench_public_case(
        package,
        _preflight(package),
        "synthetic_case",
        prepared,
        created_at="2026-07-29T18:00:00Z",
    )

    audit_root = tmp_path / "input-audit"
    bundle = run_audit(prepared / "workspace", audit_root, schema_root)

    assert bundle["findings"] == []
    assert bundle["claims"] == []
    assert bundle["detector_results"] == []
    assert {record["path"] for record in bundle["file_records"]} == {
        "data_files/observations.tsv",
        "task.md",
    }
    assert all(
        ".answer-side" not in json.dumps(record, sort_keys=True)
        for records in bundle.values()
        if isinstance(records, list)
        for record in records
        if isinstance(record, dict)
    )
    assert not (package / "EXECUTED").exists()
    replayed = replay(audit_root / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "file_records",
        "asset_identities",
        "publication_surfaces",
        "parser_results",
        "claims",
        "detector_results",
        "findings",
        "material_questions",
        "disclosures",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]


def test_public_corpus_cli_is_canonical_write_once_and_model_free(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    manifest_digest, checksums_digest = _write_public_package(package)
    output = tmp_path / "preflight.json"
    arguments = [
        "preflight-genebench-public",
        "--package-root",
        str(package),
        "--source-revision",
        _REVISION,
        "--expected-manifest-digest",
        manifest_digest,
        "--expected-checksums-digest",
        checksums_digest,
        "--output",
        str(output),
    ]

    assert evaluation_main(arguments) == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted == _preflight(package)
    assert persisted["preflight_digest"]
    assert evaluation_main(arguments) == 2
    assert not (package / "EXECUTED").exists()


@pytest.mark.parametrize("mutation", ["checksum", "symlink", "unexpected", "unsafe_manifest"])
def test_public_corpus_preflight_rejects_integrity_or_path_mutation(
    tmp_path: Path, mutation: str
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package)
    if mutation == "checksum":
        (package / "problems/synthetic_case/data_files/observations.tsv").write_text(
            "mutated\n", encoding="utf-8"
        )
    elif mutation == "symlink":
        (package / "link").symlink_to(package / "README.md")
    elif mutation == "unexpected":
        (package / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
    else:
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        manifest["problems"][0]["files"][0]["path"] = "../eval_config.json"
        (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        _rewrite_checksums(package)

    with pytest.raises(CorpusPreflightError):
        _preflight(package)


def test_public_corpus_preflight_rejects_self_consistent_answer_side_contract_drift(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _write_public_package(package)
    config_path = package / "problems/synthetic_case/eval_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["unexpected_authority"] = True
    config_path.write_text(json.dumps(config), encoding="utf-8")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"][0] = _manifest_file(package, config_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _rewrite_checksums(package)

    with pytest.raises(CorpusPreflightError, match="config fields changed"):
        _preflight(package)


def test_public_corpus_preflight_requires_full_external_identity_and_outside_output(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    manifest_digest, checksums_digest = _write_public_package(package)

    with pytest.raises(CorpusPreflightError, match="full lowercase Git"):
        preflight_genebench_public_package(
            package,
            source_revision=_REVISION[:7],
            expected_manifest_digest=manifest_digest,
            expected_checksums_digest=checksums_digest,
        )
    with pytest.raises(CorpusPreflightError, match="external digest"):
        preflight_genebench_public_package(
            package,
            source_revision=_REVISION,
            expected_manifest_digest="sha256:" + "0" * 64,
            expected_checksums_digest=checksums_digest,
        )
    with pytest.raises(CorpusPreflightError, match="outside the package"):
        preflight_genebench_public_package(
            package,
            source_revision=_REVISION,
            expected_manifest_digest=manifest_digest,
            expected_checksums_digest=checksums_digest,
            output=package / "preflight.json",
        )


def _numeric_case_audit(
    tmp_path: Path,
    schema_root: Path,
    answer: dict[str, Any],
    *,
    name: str,
    bounded_numeric_contract: bool = False,
    minimum_only_numeric_contract: bool = False,
    composite_contract: bool = False,
    single_numeric_contract: bool = False,
    integer_composite_contract: bool = False,
) -> tuple[Path, dict[str, Any], Path, str]:
    package = tmp_path / f"package-{name}"
    package.mkdir()
    _write_public_package(
        package,
        metadata_license="mit",
        license_identifier="MIT",
        numeric_contract=not (
            composite_contract or single_numeric_contract or integer_composite_contract
        ),
        bounded_numeric_contract=bounded_numeric_contract,
        minimum_only_numeric_contract=minimum_only_numeric_contract,
        composite_contract=composite_contract,
        single_numeric_contract=single_numeric_contract,
        integer_composite_contract=integer_composite_contract,
    )
    preflight = _preflight(package)
    workspace = tmp_path / f"workspace-{name}"
    workspace.mkdir()
    (workspace / "task.md").write_text("Return the required numeric estimates.\n", encoding="utf-8")
    (workspace / "answer.json").write_text(json.dumps(answer), encoding="utf-8")
    audit_root = tmp_path / f"audit-{name}"
    run_audit(workspace, audit_root, schema_root, report="task.md")
    locked = json.loads((audit_root / "semantic.lock.json").read_text(encoding="utf-8"))
    return package, preflight, audit_root, str(locked["locked_at"])


def test_genebench_numeric_grader_records_exact_match_and_mismatch_without_execution(
    tmp_path: Path, schema_root: Path
) -> None:
    mismatching_answer = {
        "answer": {"estimate_a": 1.4, "estimate_b": 0.1},
        "reasoning": "A deterministic but incorrect public-development answer.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path, schema_root, mismatching_answer, name="mismatch"
    )
    mismatch = grade_genebench_public_numeric_answer(
        package,
        preflight,
        "synthetic_case",
        audit_root,
        schema_root,
        graded_at=locked_at,
        output=tmp_path / "mismatch-grade.json",
    )

    assert mismatch["grade_status"] == "outside_tolerance"
    assert mismatch["all_within_tolerance"] is False
    assert [item["within_tolerance"] for item in mismatch["comparisons"]] == [False, False]
    assert [item["key"] for item in mismatch["comparisons"]] == ["estimate_a", "estimate_b"]
    assert mismatch["grader_contract"]["reference_grader_executed"] is False
    assert mismatch["project_code_executed_by_grader"] is False
    assert mismatch["metric_eligible"] is False
    assert mismatch["promotion_evidence_eligible"] is False
    assert not (package / "EXECUTED").exists()
    digest = mismatch.pop("grade_digest")
    assert digest == semantic_digest(mismatch)

    matching_answer = {
        "answer": {"estimate_a": 1.26, "estimate_b": -0.54},
        "reasoning": "Both values are inside the declared tolerances.",
    }
    match_package, match_preflight, match_audit, match_locked_at = _numeric_case_audit(
        tmp_path, schema_root, matching_answer, name="match"
    )
    match = grade_genebench_public_numeric_answer(
        match_package,
        match_preflight,
        "synthetic_case",
        match_audit,
        schema_root,
        graded_at=match_locked_at,
        output=tmp_path / "match-grade.json",
    )
    assert match["grade_status"] == "within_tolerance"
    assert match["all_within_tolerance"] is True
    assert all(item["within_tolerance"] for item in match["comparisons"])
    assert not (match_package / "EXECUTED").exists()


def test_genebench_numeric_grader_accepts_closed_range_metadata(
    tmp_path: Path, schema_root: Path
) -> None:
    submission = {
        "answer": {"estimate_a": 1.26, "estimate_b": -0.54},
        "reasoning": "Both values satisfy the bounded tolerance contract.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        submission,
        name="bounded-numeric",
        bounded_numeric_contract=True,
    )

    grade = grade_genebench_public_numeric_answer(
        package,
        preflight,
        "synthetic_case",
        audit_root,
        schema_root,
        graded_at=locked_at,
        output=tmp_path / "bounded-numeric-grade.json",
    )

    assert grade["grade_status"] == "within_tolerance"
    assert grade["all_within_tolerance"] is True
    assert all(item["within_allowed_range"] for item in grade["comparisons"])
    assert all(item["matches_contract"] for item in grade["comparisons"])
    assert all(
        item["allowed_range"] == {"minimum": -2.0, "maximum": 2.0} for item in grade["comparisons"]
    )


def test_genebench_numeric_grader_accepts_minimum_only_range_and_rejects_maximum_only(
    tmp_path: Path, schema_root: Path
) -> None:
    submission = {
        "answer": {"estimate_a": 1.26, "estimate_b": -0.54},
        "reasoning": "Both values satisfy the declared tolerance contract.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        submission,
        name="minimum-only-numeric",
        minimum_only_numeric_contract=True,
    )

    grade = grade_genebench_public_numeric_answer(
        package,
        preflight,
        "synthetic_case",
        audit_root,
        schema_root,
        graded_at=locked_at,
        output=tmp_path / "minimum-only-numeric-grade.json",
    )

    comparisons = {item["key"]: item for item in grade["comparisons"]}
    assert grade["grade_status"] == "within_tolerance"
    assert grade["grader_contract"]["comparison_profile"] == (
        "genebench_multi_numeric_absolute_tolerance_v3"
    )
    assert grade["grade_id"] == stable_id(
        "genebench-multi-numeric-grade",
        "0.4.0",
        "genebench_multi_numeric_absolute_tolerance_v3",
        str(preflight["preflight_id"]),
        "synthetic_case",
        str(grade["audit"]["semantic_lock_digest"]),
        str(grade["answer"]["content_digest"]),
        str(grade["grader_contract"]["contract_digest"]),
    )
    assert comparisons["estimate_a"]["within_allowed_range"] is True
    assert "allowed_range" not in comparisons["estimate_a"]
    assert comparisons["estimate_b"]["allowed_range"] == {"minimum": -2.0}

    config_path = package / "problems/synthetic_case/eval_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["grader"]["config"]["keys"]["estimate_b"] = {
        "absolute_tolerance": 0.05,
        "max_value": 2.0,
    }
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"][0] = _manifest_file(package, config_path)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    _rewrite_checksums(package)

    with pytest.raises(GeneBenchNumericGradeError, match=r"outside the .*profile"):
        grade_genebench_public_numeric_answer(
            package,
            _preflight(package),
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=locked_at,
            output=tmp_path / "maximum-only-numeric-grade.json",
        )


def test_genebench_single_numeric_grader_accepts_only_the_closed_legacy_shape(
    tmp_path: Path, schema_root: Path
) -> None:
    submission = {
        "answer": {"estimate_a": 1.26},
        "reasoning": "The sole numeric value is inside its declared tolerance.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        submission,
        name="single-numeric",
        single_numeric_contract=True,
    )
    grade = grade_genebench_public_answer(
        package,
        preflight,
        "synthetic_case",
        audit_root,
        schema_root,
        graded_at=locked_at,
        output=tmp_path / "single-numeric-grade.json",
    )

    assert grade["grade_status"] == "within_contract"
    assert grade["all_fields_match"] is True
    assert grade["grader_contract"]["comparison_profile"] == (
        "genebench_single_numeric_absolute_tolerance_v1"
    )
    assert grade["comparisons"][0]["comparison_kind"] == "numeric_absolute_tolerance"
    assert not (package / "EXECUTED").exists()

    config_path = package / "problems/synthetic_case/eval_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["grader"]["config"]["answer_field"] = "result"
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"][0] = _manifest_file(package, config_path)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    _rewrite_checksums(package)
    mutated_preflight = _preflight(package)
    with pytest.raises(GeneBenchNumericGradeError, match="answer_field"):
        grade_genebench_public_answer(
            package,
            mutated_preflight,
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=locked_at,
            output=tmp_path / "invalid-single-numeric-grade.json",
        )


def test_genebench_integer_numeric_composite_is_exact_and_type_strict(
    tmp_path: Path, schema_root: Path
) -> None:
    matching = {
        "answer": {"estimate_a": 1.26, "sample_count": 3, "support_code": 1},
        "reasoning": "The numeric estimate and integer-valued outputs match.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        matching,
        name="integer-composite",
        integer_composite_contract=True,
    )
    grade = grade_genebench_public_answer(
        package,
        preflight,
        "synthetic_case",
        audit_root,
        schema_root,
        graded_at=locked_at,
        output=tmp_path / "integer-composite-grade.json",
    )

    assert grade["grade_status"] == "within_contract"
    assert grade["all_fields_match"] is True
    assert grade["grader_contract"]["comparison_profile"] == (
        "genebench_composite_integer_exact_numeric_absolute_tolerance_v1"
    )
    comparisons = {item["key"]: item for item in grade["comparisons"]}
    assert comparisons["sample_count"]["allowed_range"] == {"minimum": 0}
    assert comparisons["support_code"]["allowed_range"] == {"minimum": 0, "maximum": 1}
    assert comparisons["sample_count"]["comparison_kind"] == "integer_exact"

    invalid = {
        "answer": {"estimate_a": 1.26, "sample_count": 3.0, "support_code": 1},
        "reasoning": "A JSON float must not satisfy an integer field.",
    }
    invalid_package, invalid_preflight, invalid_audit, invalid_locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        invalid,
        name="integer-composite-float",
        integer_composite_contract=True,
    )
    with pytest.raises(GeneBenchNumericGradeError, match="JSON integer"):
        grade_genebench_public_answer(
            invalid_package,
            invalid_preflight,
            "synthetic_case",
            invalid_audit,
            schema_root,
            graded_at=invalid_locked_at,
            output=tmp_path / "integer-composite-float-grade.json",
        )
    assert not (invalid_package / "EXECUTED").exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("forbid_extra_keys", False, "must be exactly true"),
        ("unexpected", True, "fields changed"),
    ],
)
def test_genebench_integer_composite_rejects_profile_broadening(
    tmp_path: Path,
    schema_root: Path,
    field: str,
    value: bool,
    message: str,
) -> None:
    submission = {
        "answer": {"estimate_a": 1.25, "sample_count": 3, "support_code": 1},
        "reasoning": "Exact values under an unsupported profile mutation.",
    }
    package, _preflight_record, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        submission,
        name=f"integer-profile-{field}",
        integer_composite_contract=True,
    )
    config_path = package / "problems/synthetic_case/eval_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["grader"]["config"][field] = value
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"][0] = _manifest_file(package, config_path)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    _rewrite_checksums(package)
    mutated_preflight = _preflight(package)

    with pytest.raises(GeneBenchNumericGradeError, match=message):
        grade_genebench_public_answer(
            package,
            mutated_preflight,
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=locked_at,
            output=tmp_path / f"invalid-integer-profile-{field}.json",
        )


def test_genebench_composite_grader_records_exact_and_numeric_outcomes(
    tmp_path: Path, schema_root: Path
) -> None:
    matching = {
        "answer": {"estimate_a": 1.26, "selected_group": "A"},
        "reasoning": "The numeric and exact-string fields match.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        matching,
        name="composite-match",
        composite_contract=True,
    )
    match = grade_genebench_public_answer(
        package,
        preflight,
        "synthetic_case",
        audit_root,
        schema_root,
        graded_at=locked_at,
        output=tmp_path / "composite-match-grade.json",
    )

    assert match["record_type"] == "evaluation_genebench_answer_grade"
    assert match["grade_status"] == "within_contract"
    assert match["all_fields_match"] is True
    assert {item["comparison_kind"] for item in match["comparisons"]} == {
        "exact_string",
        "numeric_absolute_tolerance",
    }
    preflight_path = tmp_path / "composite-preflight.json"
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    cli_output = tmp_path / "composite-cli-grade.json"
    assert (
        evaluation_main(
            [
                "grade-genebench-public-answer",
                "--package-root",
                str(package),
                "--preflight",
                str(preflight_path),
                "--eval-id",
                "synthetic_case",
                "--audit-root",
                str(audit_root),
                "--schema-root",
                str(schema_root),
                "--graded-at",
                locked_at,
                "--output",
                str(cli_output),
            ]
        )
        == 0
    )
    assert json.loads(cli_output.read_text(encoding="utf-8"))["all_fields_match"] is True

    mismatching = {
        "answer": {"estimate_a": 1.5, "selected_group": "a"},
        "reasoning": "A deterministic mismatching mixed answer.",
    }
    mismatch_package, mismatch_preflight, mismatch_audit, mismatch_locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        mismatching,
        name="composite-mismatch",
        composite_contract=True,
    )
    mismatch = grade_genebench_public_answer(
        mismatch_package,
        mismatch_preflight,
        "synthetic_case",
        mismatch_audit,
        schema_root,
        graded_at=mismatch_locked_at,
        output=tmp_path / "composite-mismatch-grade.json",
    )

    assert mismatch["grade_status"] == "outside_contract"
    assert mismatch["all_fields_match"] is False
    assert all(not item["matches_contract"] for item in mismatch["comparisons"])


def test_genebench_composite_grader_rejects_self_consistent_profile_broadening(
    tmp_path: Path, schema_root: Path
) -> None:
    submission = {
        "answer": {"estimate_a": 1.25, "selected_group": "A"},
        "reasoning": "Exact values under a profile mutation.",
    }
    package, _preflight_record, audit_root, locked_at = _numeric_case_audit(
        tmp_path,
        schema_root,
        submission,
        name="composite-unsupported",
        composite_contract=True,
    )
    config_path = package / "problems/synthetic_case/eval_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["grader"]["config"]["exact_match_keys"]["selected_group"]["case_sensitive"] = False
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"][0] = _manifest_file(package, config_path)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    _rewrite_checksums(package)
    mutated_preflight = _preflight(package)

    with pytest.raises(GeneBenchNumericGradeError, match="case-sensitive string profile"):
        grade_genebench_public_answer(
            package,
            mutated_preflight,
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=locked_at,
            output=tmp_path / "composite-unsupported-grade.json",
        )
    assert not (tmp_path / "composite-unsupported-grade.json").exists()
    assert not (package / "EXECUTED").exists()


@pytest.mark.parametrize(
    "mutation", ["answer", "package", "preflight", "semantic_lock", "timestamp"]
)
def test_genebench_numeric_grader_rejects_identity_and_chronology_mutation(
    tmp_path: Path, schema_root: Path, mutation: str
) -> None:
    submission = {
        "answer": {"estimate_a": 1.25, "estimate_b": -0.5},
        "reasoning": "Exact values for mutation testing.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path, schema_root, submission, name=mutation
    )
    graded_at = locked_at
    if mutation == "answer":
        (audit_root / "observed/snapshot/materialized/answer.json").write_text(
            json.dumps({**submission, "reasoning": "mutated after snapshot"}),
            encoding="utf-8",
        )
    elif mutation == "package":
        (package / "problems/synthetic_case/eval_config.json").write_text("{}", encoding="utf-8")
    elif mutation == "preflight":
        preflight["held_out_eligible"] = True
    elif mutation == "semantic_lock":
        lock_path = audit_root / "semantic.lock.json"
        locked = json.loads(lock_path.read_text(encoding="utf-8"))
        locked["locked_at"] = "2026-01-01T00:00:00Z"
        lock_path.write_text(json.dumps(locked), encoding="utf-8")
    else:
        graded_at = "2000-01-01T00:00:00Z"

    with pytest.raises(GeneBenchNumericGradeError):
        grade_genebench_public_numeric_answer(
            package,
            preflight,
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=graded_at,
            output=tmp_path / f"grade-{mutation}.json",
        )
    assert not (tmp_path / f"grade-{mutation}.json").exists()
    assert not (package / "EXECUTED").exists()


def test_genebench_numeric_grader_rejects_unsupported_self_consistent_contract(
    tmp_path: Path, schema_root: Path
) -> None:
    submission = {
        "answer": {"estimate_a": 1.25, "estimate_b": -0.5},
        "reasoning": "Exact values under an unsupported contract mutation.",
    }
    package, _preflight_record, audit_root, locked_at = _numeric_case_audit(
        tmp_path, schema_root, submission, name="unsupported-contract"
    )
    config_path = package / "problems/synthetic_case/eval_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["grader"]["config"]["keys"]["estimate_a"]["relative_tolerance"] = 0.01
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"][0] = _manifest_file(package, config_path)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    _rewrite_checksums(package)
    mutated_preflight = _preflight(package)

    with pytest.raises(GeneBenchNumericGradeError, match="absolute-tolerance profile"):
        grade_genebench_public_numeric_answer(
            package,
            mutated_preflight,
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=locked_at,
            output=tmp_path / "unsupported-contract-grade.json",
        )
    assert not (package / "EXECUTED").exists()


@pytest.mark.parametrize(
    "invalid_answer",
    [
        {"answer": {"estimate_a": 1.25}, "reasoning": "missing key"},
        {
            "answer": {"estimate_a": 1.25, "estimate_b": -0.5, "extra": 0.0},
            "reasoning": "extra key",
        },
        {"answer": {"estimate_a": True, "estimate_b": -0.5}, "reasoning": "boolean"},
        {"answer": {"estimate_a": "1.25", "estimate_b": -0.5}, "reasoning": "string"},
    ],
)
def test_genebench_numeric_grader_rejects_nonexact_answer_schema(
    tmp_path: Path, schema_root: Path, invalid_answer: dict[str, Any]
) -> None:
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path, schema_root, invalid_answer, name=semantic_digest(invalid_answer)[-8:]
    )
    with pytest.raises(GeneBenchNumericGradeError):
        grade_genebench_public_numeric_answer(
            package,
            preflight,
            "synthetic_case",
            audit_root,
            schema_root,
            graded_at=locked_at,
            output=tmp_path / f"invalid-{semantic_digest(invalid_answer)[-8:]}.json",
        )
    assert not (package / "EXECUTED").exists()


def test_genebench_numeric_grader_cli_is_canonical_and_write_once(
    tmp_path: Path, schema_root: Path
) -> None:
    submission = {
        "answer": {"estimate_a": 1.25, "estimate_b": -0.5},
        "reasoning": "Exact public-development values.",
    }
    package, preflight, audit_root, locked_at = _numeric_case_audit(
        tmp_path, schema_root, submission, name="cli"
    )
    preflight_path = tmp_path / "numeric-preflight.json"
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    output = tmp_path / "numeric-grade.json"
    arguments = [
        "grade-genebench-public-numeric",
        "--package-root",
        str(package),
        "--preflight",
        str(preflight_path),
        "--eval-id",
        "synthetic_case",
        "--audit-root",
        str(audit_root),
        "--schema-root",
        str(schema_root),
        "--graded-at",
        locked_at,
        "--output",
        str(output),
    ]

    assert evaluation_main(arguments) == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    digest = persisted.pop("grade_digest")
    assert digest == semantic_digest(persisted)
    original = output.read_bytes()
    assert evaluation_main(arguments) == 2
    assert output.read_bytes() == original
    assert not (package / "EXECUTED").exists()
