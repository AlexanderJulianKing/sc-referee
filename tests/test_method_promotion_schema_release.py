from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from sc_referee.core.ids import semantic_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_method_promotion_schema_release import (
    BASELINE_VERSION,
    RELEASE_VERSION,
    SOURCE_ADRS,
    build_release,
)
from scripts.migrate_round1_method_promotion_records import (
    migrate_round1_method_promotion_records,
)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    }


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def release(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("method-promotion-release") / "schemas-v0.19.0"
    assert build_release(output) == 79
    return output


def test_release_is_complete_accepted_and_self_validating(release: Path) -> None:
    assert _load(release / "RELEASE_STATUS.json") == {
        "accepted": True,
        "baseline_version": BASELINE_VERSION,
        "public_release": True,
        "release_version": RELEASE_VERSION,
        "source_adrs": SOURCE_ADRS,
    }
    assert (release / "VERSION").read_text(encoding="utf-8") == "0.19.0\n"
    assert "Accepted forward-only public schema release" in (release / "README.md").read_text(
        encoding="utf-8"
    )
    for name in (
        "CHANGELOG.md",
        "CONTROLLER_INVARIANTS.md",
        "MIGRATION_v0.18.0_to_v0.19.0.md",
        "VALIDATION.txt",
        "pyproject.toml",
        "tools/validate_records.py",
        "tests/test_v019_invariants.py",
    ):
        assert (release / name).is_file(), name

    for path in sorted((release / "schemas" / "v0.19.0").glob("*.json")):
        Draft202012Validator.check_schema(_load(path))
    assert LocalSchemaRegistry(release).validate_example_directory() == 79

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(release / "tests"), "-q", "-p", "no:cacheprovider"],
        cwd=release,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "139 passed" in completed.stdout


def test_release_manifest_covers_every_generated_artifact_except_itself(
    release: Path,
) -> None:
    entries: dict[str, str] = {}
    for line in (release / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        entries[relative] = digest
    expected_paths = {
        path.relative_to(release).as_posix()
        for path in release.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.sha256"
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
    }
    assert set(entries) == expected_paths
    for relative, digest in entries.items():
        assert hashlib.sha256((release / relative).read_bytes()).hexdigest() == digest


def test_release_adds_closed_approval_and_static_disclosure_shapes(release: Path) -> None:
    schema = _load(release / "schemas" / "v0.19.0" / "detector-qualification.schema.json")
    approval = schema["properties"]["software_maintainer_approvals"]["items"]
    assert approval["required"] == ["actor", "approved_on", "decision_ref"]
    assert approval["additionalProperties"] is False
    static = next(
        branch
        for branch in schema["properties"]["static_scope_disclosure"]["oneOf"]
        if branch.get("type") == "object"
    )
    assert static["properties"]["stage3_comparison_artifact_exists"] == {"type": "boolean"}
    assert "stage3_comparison_artifact_exists" in static["required"]

    evaluation_minimums = []
    for branch in schema["allOf"]:
        properties = branch.get("then", {}).get("properties", {})
        if "minItems" in properties.get("evaluation_refs", {}):
            evaluation_minimums.append(properties["evaluation_refs"]["minItems"])
        assert "minItems" not in properties.get("agent_adjudication_refs", {})
    assert evaluation_minimums == [1, 1, 1, 1, 2]


@pytest.mark.parametrize(
    ("lane", "exam", "expected_authors"),
    [
        (
            "complete-domain-exposure-denominator-v1.1.0-direct-lane-v2",
            "heldout-v207-seven-case",
            {
                "actor:heldout-claude-04",
                "actor:heldout-claude-05",
                "actor:heldout-claude-06",
                "actor:heldout-codex-04",
                "actor:heldout-codex-05",
                "actor:heldout-codex-06",
            },
        ),
        (
            "authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane",
            "heldout-seven-case",
            {
                "actor:dependence-heldout-author-opus-23",
                "actor:dependence-heldout-author-opus-24",
            },
        ),
    ],
)
def test_round1_records_validate_after_fail_closed_migration(
    project_root: Path,
    release: Path,
    tmp_path: Path,
    lane: str,
    exam: str,
    expected_authors: set[str],
) -> None:
    lane_root = project_root / "evaluation" / "qualification" / lane
    metric_set, qualification = migrate_round1_method_promotion_records(
        lane_root / "promotion" / "DETECTOR_QUALIFICATION.json",
        lane_root / "promotion" / "QUALIFICATION_METRIC_SET.json",
        lane_root / exam / "authoring" / "AUTHORING_PROTOCOL.json",
        release,
        tmp_path / lane,
    )
    registry = LocalSchemaRegistry(release)
    registry.validate(metric_set)
    registry.validate(qualification)
    assert qualification["schema_version"] == "0.19.0"
    assert metric_set["schema_version"] == "0.19.0"
    assert qualification["agent_adjudication_refs"] == []
    assert len(qualification["evaluation_refs"]) == 2
    assert set(qualification["author_actor_ids"]) == expected_authors
    assert qualification["human_scientific_approvals"] == []
    assert qualification["qualification_proof_families"] == ["static_closed_scope"]
    assert set(qualification["software_maintainer_approvals"][0]) == {
        "actor",
        "approved_on",
        "decision_ref",
    }
    assert qualification["numeric_threshold_policy"] == metric_set["numeric_threshold_policy"]
    policy = dict(metric_set["numeric_threshold_policy"])
    policy_digest = policy.pop("policy_semantic_digest")
    assert policy_digest == semantic_digest(policy)
    assert "absolute_count_requirements" not in policy
    assert "no_missed_roots" not in qualification["safety_gates"]

    report = _load(tmp_path / lane / "MIGRATION_REPORT.json")
    assert report["agent_adjudication_record_invented"] is False
    assert report["human_scientific_approval_invented"] is False
    assert report["qualification_grant_installed"] is False
    assert report["finding_authority_created"] is False
    assert report["execution_launched"] is False


def test_release_construction_never_touches_v018_or_installs_v019(
    project_root: Path, tmp_path: Path
) -> None:
    baseline = project_root / "reference" / "schemas-v0.18.0"
    before = _tree_bytes(baseline)
    output = tmp_path / "constructed-only-v019"
    build_release(output)
    assert _tree_bytes(baseline) == before
    assert not (project_root / "reference" / "schemas-v0.19.0").exists()
    with pytest.raises(ValueError, match="absent or empty"):
        build_release(output)
