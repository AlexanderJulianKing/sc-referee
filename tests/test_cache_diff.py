from __future__ import annotations

import json
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import sc_referee.controller as controller
from sc_referee.audit_diff import build_audit_diff, verify_audit_diff
from sc_referee.cache import acquire_project_cache_lease
from sc_referee.cache_auth import (
    CACHE_AUTHENTICATION_PROFILE,
    InMemoryCacheKeyProvider,
    UnavailableCacheKeyProvider,
    encode_cache_authentication_key,
)
from sc_referee.cli import app
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json


def _write_project(root: Path, *, python_value: int = 1) -> None:
    root.mkdir()
    (root / "report.md").write_text(
        "# Results\n\nTreatment increased yield relative to control.\n",
        encoding="utf-8",
    )
    (root / "analysis.py").write_text(f"value = {python_value}\n", encoding="utf-8")


def _cache_statuses(bundle: dict[str, object]) -> dict[str, str]:
    records = bundle["cache_entries"]
    assert isinstance(records, list)
    return {
        str(record["extensions"]["x-source-path"]): str(record["extensions"]["x-cache-status"])
        for record in records
        if "x-source-path" in record.get("extensions", {})
    }


def _descendant_cache_statuses(bundle: dict[str, object]) -> dict[str, str]:
    records = bundle["cache_entries"]
    assert isinstance(records, list)
    return {
        f"{record['extensions']['x-cache-category']}:{record['extensions']['x-cache-scope-key']}": str(
            record["extensions"]["x-cache-status"]
        )
        for record in records
        if "x-cache-category" in record.get("extensions", {})
    }


def _performance_cache_usage(bundle: dict[str, object]) -> dict[str, int]:
    records = bundle["performance_records"]
    assert isinstance(records, list) and len(records) == 1
    usage = records[0]["cache_usage"]
    assert isinstance(usage, dict)
    return {key: int(value) for key, value in usage.items()}


def test_project_local_cache_hits_and_targeted_invalidation(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)

    first_root = tmp_path / "first"
    first = run_audit(repository, first_root, schema_root)
    assert _cache_statuses(first) == {"analysis.py": "miss", "report.md": "miss"}
    assert _performance_cache_usage(first) == {
        "hits": 0,
        "misses": 2,
        "invalidations": 0,
    }
    assert (repository / ".sc-referee" / "cache" / "v1" / "parser-index.json").is_file()
    assert first["repository_snapshots"][0]["live_workspace_state"]["status"] == "unchanged"

    second_root = tmp_path / "second"
    second = run_audit(repository, second_root, schema_root)
    assert _cache_statuses(second) == {"analysis.py": "hit", "report.md": "hit"}
    assert _performance_cache_usage(second) == {
        "hits": 2,
        "misses": 0,
        "invalidations": 0,
    }
    assert _descendant_cache_statuses(second) == {
        "bounded_lineage:repository": "hit",
        "static_graph:analysis.py": "hit",
    }
    assert [item["parser_result_id"] for item in first["parser_results"]] == [
        item["parser_result_id"] for item in second["parser_results"]
    ]
    assert {item["audit_run_id"] for item in second["parser_results"]} == {second["audit_run_id"]}

    (repository / "analysis.py").write_text("value = 2\n", encoding="utf-8")
    third_root = tmp_path / "third"
    third = run_audit(repository, third_root, schema_root)
    assert _cache_statuses(third) == {"analysis.py": "miss", "report.md": "hit"}
    assert _performance_cache_usage(third) == {
        "hits": 1,
        "misses": 1,
        "invalidations": 1,
    }
    assert _descendant_cache_statuses(third) == {
        "bounded_lineage:repository": "miss",
        "static_graph:analysis.py": "miss",
    }
    analysis_entry = next(
        item
        for item in third["cache_entries"]
        if item["extensions"]["x-source-path"] == "analysis.py"
    )
    assert analysis_entry["extensions"]["x-replaced-prior-key"] is True

    diff = build_audit_diff(second_root, third_root, schema_root)
    verify_audit_diff(diff)
    assert diff["paths"]["changed"] == ["analysis.py"]
    assert diff["paths"]["unchanged"] == ["report.md"]
    assert diff["cache"] == {
        "hits": 1,
        "misses": 1,
        "invalidations": 1,
        "hit_paths": ["report.md"],
        "miss_paths": ["analysis.py"],
        "invalidated_paths": ["analysis.py"],
        "scope": "after-run project-local parser cache only",
    }
    assert build_audit_diff(second_root, third_root, schema_root) == diff

    (repository / "analysis.py").unlink()
    fourth_root = tmp_path / "fourth"
    fourth = run_audit(repository, fourth_root, schema_root)
    assert _cache_statuses(fourth) == {"report.md": "hit"}
    fourth_lock = json.loads((fourth_root / "semantic.lock.json").read_text())
    assert fourth_lock["cache_summary"]["descendants"]["invalidated_keys"] == [
        "bounded_lineage:repository",
        "static_graph:analysis.py",
    ]
    removal_diff = build_audit_diff(third_root, fourth_root, schema_root)
    assert removal_diff["paths"]["removed"] == ["analysis.py"]
    assert removal_diff["cache"]["invalidations"] == 1
    assert removal_diff["cache"]["invalidated_paths"] == ["analysis.py"]

    replayed = replay(third_root / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["cache_entries"] == third["cache_entries"]
    assert replayed["cache_policies"] == third["cache_policies"]
    assert replayed["performance_records"] == third["performance_records"]


def test_identical_content_in_another_repository_is_not_a_cache_hit(
    schema_root: Path, tmp_path: Path
) -> None:
    first_repository = tmp_path / "first-project"
    second_repository = tmp_path / "second-project"
    _write_project(first_repository)
    _write_project(second_repository)

    first = run_audit(first_repository, tmp_path / "first-audit", schema_root)
    second = run_audit(second_repository, tmp_path / "second-audit", schema_root)

    assert set(_cache_statuses(first).values()) == {"miss"}
    assert set(_cache_statuses(second).values()) == {"miss"}
    assert (
        first["cache_policies"][0]["extensions"]["x-project-identity"]
        != second["cache_policies"][0]["extensions"]["x-project-identity"]
    )


def test_python_cache_key_tracks_exact_literal_data_dependencies(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    shutil.copytree(project_root / "examples" / "general-static", repository)

    first = run_audit(repository, tmp_path / "first", schema_root, report="report.md")
    second = run_audit(repository, tmp_path / "second", schema_root, report="report.md")
    assert _cache_statuses(second) == {
        "README.md": "hit",
        "analysis.py": "hit",
        "report.md": "hit",
    }
    assert _descendant_cache_statuses(second) == {
        "bounded_lineage:repository": "hit",
        "static_graph:analysis.py": "hit",
    }
    first_value = first["observed_results"][0]["scalar_value"]

    data_path = repository / "data.csv"
    data_path.write_text(
        data_path.read_text(encoding="utf-8").replace("treatment,3", "treatment,9"),
        encoding="utf-8",
    )
    third = run_audit(repository, tmp_path / "third", schema_root, report="report.md")

    assert _cache_statuses(third) == {
        "README.md": "hit",
        "analysis.py": "miss",
        "report.md": "hit",
    }
    assert _descendant_cache_statuses(third) == {
        "bounded_lineage:repository": "miss",
        "static_graph:analysis.py": "miss",
    }
    assert third["observed_results"][0]["scalar_value"] != first_value
    analysis_entry = next(
        item
        for item in third["cache_entries"]
        if item["extensions"]["x-source-path"] == "analysis.py"
    )
    assert analysis_entry["extensions"]["x-source-dependencies"] == ["data.csv"]
    assert analysis_entry["extensions"]["x-replaced-prior-key"] is True
    descendant_entries = [
        item for item in third["cache_entries"] if "x-cache-category" in item["extensions"]
    ]
    assert all(item["extensions"]["x-replaced-prior-key"] for item in descendant_entries)
    third_lock = json.loads((tmp_path / "third" / "semantic.lock.json").read_text())
    assert third_lock["cache_summary"]["descendants"] == {
        "cache_format": "sc-referee-project-descendant-cache-v2",
        "hits": 0,
        "misses": 2,
        "invalidations": 2,
        "hit_keys": [],
        "miss_keys": ["bounded_lineage:repository", "static_graph:analysis.py"],
        "invalidated_keys": ["bounded_lineage:repository", "static_graph:analysis.py"],
        "uncacheable_keys": [],
    }


def test_report_only_change_preserves_python_descendant_hits(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    shutil.copytree(project_root / "examples" / "general-static", repository)
    run_audit(repository, tmp_path / "first", schema_root, report="report.md")

    report = repository / "report.md"
    report.write_text(
        report.read_text(encoding="utf-8") + "\nAn additional descriptive sentence.\n",
        encoding="utf-8",
    )
    second = run_audit(repository, tmp_path / "second", schema_root, report="report.md")

    assert _cache_statuses(second) == {
        "README.md": "hit",
        "analysis.py": "hit",
        "report.md": "miss",
    }
    assert _descendant_cache_statuses(second) == {
        "bounded_lineage:repository": "hit",
        "static_graph:analysis.py": "hit",
    }


def test_unsafe_project_cache_symlink_is_not_followed(schema_root: Path, tmp_path: Path) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    outside = tmp_path / "outside"
    outside.mkdir()
    (repository / ".sc-referee").symlink_to(outside, target_is_directory=True)

    bundle = run_audit(repository, tmp_path / "audit", schema_root)

    assert bundle["cache_entries"] == []
    reason = bundle["cache_policies"][0]["extensions"]["x-unavailable-reason"]
    assert "symbolic-link" in reason
    assert list(outside.iterdir()) == []


def test_contended_cache_writer_lease_fails_open_for_audit_and_preserves_index(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    run_audit(repository, tmp_path / "first", schema_root)
    cache_root = repository / ".sc-referee" / "cache" / "v1"
    parser_index = cache_root / "parser-index.json"
    descendant_index = cache_root / "descendant-index.json"
    parser_before = parser_index.read_bytes()
    descendant_before = descendant_index.read_bytes()
    (repository / "analysis.py").write_text("value = 2\n", encoding="utf-8")

    lease = acquire_project_cache_lease(cache_root)
    busy_output = tmp_path / "busy-audit"
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "sc_referee.cli",
                "audit",
                str(repository),
                "--output",
                str(busy_output),
                "--schema-root",
                str(schema_root),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    finally:
        lease.close()

    assert completed.returncode == 0, completed.stderr
    busy_bundle = json.loads((busy_output / "audit.bundle.json").read_text(encoding="utf-8"))
    assert busy_bundle["cache_entries"] == []
    assert (
        busy_bundle["cache_policies"][0]["extensions"]["x-unavailable-reason"]
        == "Project-local cache is busy in another audit."
    )
    assert busy_bundle["cache_policies"][0]["extensions"]["x-contended-run-behavior"] == (
        "cache_unavailable_no_wait"
    )
    assert parser_index.read_bytes() == parser_before
    assert descendant_index.read_bytes() == descendant_before

    changed = run_audit(repository, tmp_path / "changed", schema_root)
    assert _cache_statuses(changed) == {"analysis.py": "miss", "report.md": "hit"}
    assert _descendant_cache_statuses(changed) == {
        "bounded_lineage:repository": "miss",
        "static_graph:analysis.py": "miss",
    }
    warm = run_audit(repository, tmp_path / "warm", schema_root)
    assert _cache_statuses(warm) == {"analysis.py": "hit", "report.md": "hit"}
    assert _descendant_cache_statuses(warm) == {
        "bounded_lineage:repository": "hit",
        "static_graph:analysis.py": "hit",
    }


def test_cache_writer_lease_symlink_is_rejected(schema_root: Path, tmp_path: Path) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    cache_root = repository / ".sc-referee" / "cache" / "v1"
    cache_root.mkdir(parents=True)
    outside = tmp_path / "outside-lock"
    outside.write_text("preserve", encoding="utf-8")
    (cache_root / ".writer.lock").symlink_to(outside)

    bundle = run_audit(repository, tmp_path / "audit", schema_root)

    assert bundle["cache_entries"] == []
    reason = bundle["cache_policies"][0]["extensions"]["x-unavailable-reason"]
    assert reason == "Project-local cache writer lease unavailable: OSError"
    assert outside.read_text(encoding="utf-8") == "preserve"


def test_warm_descendant_cache_skips_static_promotion_and_bounded_verification(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "project"
    shutil.copytree(project_root / "examples" / "general-static", repository)
    first = run_audit(repository, tmp_path / "first", schema_root, report="report.md")

    def fail_if_recomputed(*args: object, **kwargs: object) -> object:
        raise AssertionError("an exact warm descendant was recomputed")

    monkeypatch.setattr(controller, "build_public_static_graph", fail_if_recomputed)
    monkeypatch.setattr(controller, "reconstruct_bounded_results", fail_if_recomputed)
    second = run_audit(repository, tmp_path / "second", schema_root, report="report.md")

    assert _descendant_cache_statuses(second) == {
        "bounded_lineage:repository": "hit",
        "static_graph:analysis.py": "hit",
    }
    assert (
        second["observed_results"][0]["scalar_value"]
        == first["observed_results"][0]["scalar_value"]
    )
    assert {item["audit_run_id"] for item in second["observed_results"]} == {second["audit_run_id"]}


def test_authenticated_parser_blob_tamper_is_a_miss_even_with_recomputed_plain_digest(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    provider = InMemoryCacheKeyProvider(secrets.token_bytes(32))
    run_audit(
        repository,
        tmp_path / "first",
        schema_root,
        cache_key_provider=provider,
    )
    cache_root = repository / ".sc-referee" / "cache" / "v1"
    parser_index = json.loads((cache_root / "parser-index.json").read_text(encoding="utf-8"))
    analysis_entry = parser_index["entries"]["parser:python-ast-tokenize:analysis.py"]
    digest = str(analysis_entry["cache_key"]).removeprefix("sha256:")
    blob = cache_root / "parser" / digest[:2] / f"{digest}.json"
    tampered = json.loads(blob.read_text(encoding="utf-8"))
    tampered["parser_result"]["extensions"]["x-token-count"] = 999_999
    tampered["result_digest"] = semantic_digest(tampered["parser_result"])
    write_normalized_json(blob, tampered)

    second = run_audit(
        repository,
        tmp_path / "second",
        schema_root,
        cache_key_provider=provider,
    )

    assert _cache_statuses(second) == {"analysis.py": "miss", "report.md": "hit"}
    assert second["findings"] == []
    assert (
        next(
            result
            for result in second["parser_results"]
            if result["source_ref"]["path"] == "analysis.py"
        )["extensions"]["x-token-count"]
        != 999_999
    )


def test_authenticated_index_tamper_forces_fail_closed_recomputation(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    provider = InMemoryCacheKeyProvider(secrets.token_bytes(32))
    run_audit(
        repository,
        tmp_path / "first",
        schema_root,
        cache_key_provider=provider,
    )
    cache_root = repository / ".sc-referee" / "cache" / "v1"
    parser_index_path = cache_root / "parser-index.json"
    parser_index = json.loads(parser_index_path.read_text(encoding="utf-8"))
    parser_index["entries"] = {}
    write_normalized_json(parser_index_path, parser_index)

    second = run_audit(
        repository,
        tmp_path / "second",
        schema_root,
        cache_key_provider=provider,
    )
    assert set(_cache_statuses(second).values()) == {"miss"}

    descendant_index_path = cache_root / "descendant-index.json"
    descendant_index = json.loads(descendant_index_path.read_text(encoding="utf-8"))
    descendant_index["entries"] = {}
    write_normalized_json(descendant_index_path, descendant_index)

    third = run_audit(
        repository,
        tmp_path / "third",
        schema_root,
        cache_key_provider=provider,
    )
    assert set(_cache_statuses(third).values()) == {"hit"}
    assert set(_descendant_cache_statuses(third).values()) == {"miss"}
    assert third["findings"] == []


def test_cache_key_rotation_makes_old_entries_miss_and_never_persists_key_bytes(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    first_secret = secrets.token_bytes(32)
    second_secret = secrets.token_bytes(32)
    first_provider = InMemoryCacheKeyProvider(first_secret)
    second_provider = InMemoryCacheKeyProvider(second_secret)
    first = run_audit(
        repository,
        tmp_path / "first",
        schema_root,
        cache_key_provider=first_provider,
    )
    second = run_audit(
        repository,
        tmp_path / "second",
        schema_root,
        cache_key_provider=second_provider,
    )
    third = run_audit(
        repository,
        tmp_path / "third",
        schema_root,
        cache_key_provider=second_provider,
    )

    assert set(_cache_statuses(second).values()) == {"miss"}
    assert set(_descendant_cache_statuses(second).values()) == {"miss"}
    assert set(_cache_statuses(third).values()) == {"hit"}
    assert set(_descendant_cache_statuses(third).values()) == {"hit"}
    first_policy = first["cache_policies"][0]["extensions"]
    second_policy = second["cache_policies"][0]["extensions"]
    assert first_policy["x-authentication-key-id"] != second_policy["x-authentication-key-id"]
    assert second_policy["x-authentication-profile"] == CACHE_AUTHENTICATION_PROFILE

    forbidden = {
        first_secret,
        second_secret,
        encode_cache_authentication_key(first_secret).encode("ascii"),
        encode_cache_authentication_key(second_secret).encode("ascii"),
        first_secret.hex().encode("ascii"),
        second_secret.hex().encode("ascii"),
    }
    durable_files = [
        path
        for root in (repository / ".sc-referee", tmp_path / "first", tmp_path / "second")
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    ]
    for path in durable_files:
        payload = path.read_bytes()
        assert all(secret not in payload for secret in forbidden)


def test_missing_authentication_key_disables_persistent_cache_without_failing_audit(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    provider = UnavailableCacheKeyProvider("Test credential is unavailable.")

    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        cache_key_provider=provider,
    )

    assert bundle["cache_entries"] == []
    assert bundle["findings"] == []
    policy = bundle["cache_policies"][0]["extensions"]
    assert policy["x-authentication-profile"] == CACHE_AUTHENTICATION_PROFILE
    assert policy["x-authentication-key-id"] == "unavailable"
    assert policy["x-authentication-provider"] == "unavailable"
    assert policy["x-unavailable-reason"] == "Test credential is unavailable."
    assert not (repository / ".sc-referee").exists()


def test_authenticated_cache_never_follows_a_project_authored_blob_shard_symlink(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    provider = InMemoryCacheKeyProvider(secrets.token_bytes(32))
    run_audit(
        repository,
        tmp_path / "first",
        schema_root,
        cache_key_provider=provider,
    )
    cache_root = repository / ".sc-referee" / "cache" / "v1"
    parser_index = json.loads((cache_root / "parser-index.json").read_text(encoding="utf-8"))
    analysis_entry = parser_index["entries"]["parser:python-ast-tokenize:analysis.py"]
    digest = str(analysis_entry["cache_key"]).removeprefix("sha256:")
    shard = cache_root / "parser" / digest[:2]
    shutil.rmtree(shard)
    outside = tmp_path / "outside-cache-target"
    outside.mkdir()
    sentinel = outside / "preserve.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    shard.symlink_to(outside, target_is_directory=True)

    second_root = tmp_path / "second"
    second = run_audit(
        repository,
        second_root,
        schema_root,
        cache_key_provider=provider,
    )

    assert "analysis.py" not in _cache_statuses(second)
    lock = json.loads((second_root / "semantic.lock.json").read_text(encoding="utf-8"))
    assert "analysis.py" in lock["cache_summary"]["miss_paths"]
    assert "analysis.py" in lock["cache_summary"]["uncacheable_paths"]
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert list(outside.iterdir()) == [sentinel]


def test_diff_cli_writes_digest_bound_noncertifying_document(
    schema_root: Path, tmp_path: Path
) -> None:
    repository = tmp_path / "project"
    _write_project(repository)
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_audit(repository, first, schema_root)
    run_audit(repository, second, schema_root)
    output = tmp_path / "audit-diff.json"

    result = CliRunner().invoke(
        app,
        [
            "diff",
            str(first),
            str(second),
            "--output",
            str(output),
            "--schema-root",
            str(schema_root),
        ],
    )

    assert result.exit_code == 0, result.output
    value = json.loads(output.read_text(encoding="utf-8"))
    verify_audit_diff(value)
    assert value["paths"]["changed"] == []
    assert "not a correctness comparison" in value["limitations"][0]
