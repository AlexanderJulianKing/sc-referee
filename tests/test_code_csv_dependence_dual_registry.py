from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.method_conflict_finding import (
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST,
)
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    installed_pin_matches_live_identity,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from sc_referee.scientific_checks.registry import ScientificCheckRegistry

_CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
_BINDING_ID = (
    "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
)
_TITLE = "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"
_ENVELOPE_5 = Path("evaluation/development/blind-envelope-5-2026-08-22/cases")
_CANDIDATES = (
    "0b4876ceca6b0a9aede7",
    "1975f22bc0022b19331f",
    "2448bea72701b75fce2a",
    "a1541d5c671f3d6d58ce",
)
_FROZEN = Path("src/sc_referee/resources/frozen-code-csv-dependence-v2.1.0")
_K_CASE = Path(
    "evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f"
)
_K_DEVELOPMENT_LOCK = Path(
    "evaluation/development/pseudorep-code-slice-v2_2/"
    "k-method-contracts/6b2da0c7167dbba3738f/semantic.lock.json"
)


def _material_path(case_root: Path) -> str:
    return _material_path_from_lock(case_root / "method-contract/semantic.lock.json")


def _material_path_from_lock(lock_path: Path) -> str:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    return str(
        lock["method_contract_profile"]["profile_manifest"]["authority_binding_snapshot"][
            "authorized_independent_unit_key"
        ]["material_input_path"]
    )


def test_registry_carries_exact_qualified_and_development_bindings() -> None:
    registry = scientific_check_release_registry()
    qualified = next(
        item for item in registry.method_conflict_bindings if item.check_id == _CHECK_ID
    )
    development = next(
        item for item in registry.development_method_conflict_bindings if item.check_id == _CHECK_ID
    )
    assert (qualified.check_version, qualified.detector_version) == ("2.1.0", "2.1.0")
    assert qualified.binding_id == _BINDING_ID
    assert qualified.binding_digest == GRANT_PINS[_BINDING_ID].binding_digest
    assert installed_pin_matches_live_identity(GRANT_PINS[_BINDING_ID]) is True
    assert (development.check_version, development.detector_version) == ("3.0.0", "3.0.0")
    assert development.binding_id == f"{_BINDING_ID}:development"
    assert registry.modules_for_lane("qualified") != registry.modules_for_lane("development")


def test_development_identity_change_cannot_change_qualified_pin_or_findings(
    schema_root: Path, tmp_path: Path
) -> None:
    registry = scientific_check_release_registry()
    development = list(registry.development_method_conflict_bindings)
    index = next(i for i, item in enumerate(development) if item.check_id == _CHECK_ID)
    development[index] = replace(development[index], binding_id=f"{_BINDING_ID}:development-probe")
    changed = ScientificCheckRegistry(
        registry.modules,
        unavailable_manifests=registry.unavailable_manifests,
        method_conflict_bindings=registry.method_conflict_bindings,
        development_modules=registry.development_modules,
        development_method_conflict_bindings=tuple(development),
    )
    assert changed.method_conflict_bindings == registry.method_conflict_bindings
    assert changed.registry_digest != registry.registry_digest
    assert installed_pin_matches_live_identity(GRANT_PINS[_BINDING_ID]) is True
    for case_id in _CANDIDATES:
        source = _ENVELOPE_5 / case_id
        project = tmp_path / f"changed-development-project-{case_id}"
        shutil.copytree(source / "project", project)
        bundle = run_audit(
            project,
            tmp_path / f"changed-development-audit-{case_id}",
            schema_root,
            material_inputs=(_material_path(source),),
            method_contract_lock=source / "method-contract/semantic.lock.json",
            scientific_check_registry=changed,
        )
        assert [item["title"] for item in bundle["findings"]] == [_TITLE]


def test_envelope_5_frozen_2_1_sources_and_wording_are_exact() -> None:
    assert sha256_digest((_FROZEN / "code_csv_dependence_adapter.py").read_bytes()) == (
        "sha256:064413da6821c59bf02a8deef4675a9e63ec8699a4146e2854c20792777de0c5"
    )
    assert sha256_digest((_FROZEN / "code_csv_dependence_dataflow.py").read_bytes()) == (
        "sha256:22b85efb45c41602d45f93855a327bb1d83321f653d5470f6c8946c8003e6c29"
    )
    assert sha256_digest((_FROZEN / "report_csv_dependence_adapter.py").read_bytes()) == (
        "sha256:e9cfe98905661238865401aba1c4eeb14a431bfae76f12094381eea7ac8516af"
    )
    assert (
        sha256_digest(
            Path(
                "src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_1.py"
            ).read_bytes()
        )
        == "sha256:9c30154639e1fc013a0f82a5ee3d767202c121f42626b2c6497436e9305f2452"
    )
    assert CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST == (
        "sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288"
    )


def test_all_2_x_development_sources_remain_byte_exact_after_v3_registration() -> None:
    expected = {
        "src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py": (
            "sha256:68f5c5c665c17175627c8586c45670a931829897df8dedb64046e76be2341505"
        ),
        "src/sc_referee/scientific_checks/code_csv_dependence_adapter.py": (
            "sha256:d04cd373a11f39d34065295dcb65c84a806a5ac8c4fd2e8174cb407bbb3e40ce"
        ),
        "src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v2_1.py": (
            "sha256:22b85efb45c41602d45f93855a327bb1d83321f653d5470f6c8946c8003e6c29"
        ),
        "src/sc_referee/scientific_checks/code_csv_dependence_adapter_v2_1.py": (
            "sha256:d6350bc9a2fc454d11888ac6984b5cee25a0b34873acd8e264a741471fb2769c"
        ),
        "src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_1.py": (
            "sha256:9c30154639e1fc013a0f82a5ee3d767202c121f42626b2c6497436e9305f2452"
        ),
        "src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_2.py": (
            "sha256:f2aab5efb1e02d3bae88800dea31c1707644fb36b6de48abfb612e7f426f71be"
        ),
        "src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_3.py": (
            "sha256:529c60dd57db912656d809a8d4dbb4be950a46ed0dc311c31f6b3ebd0a38cc3b"
        ),
    }
    assert {path: sha256_digest(Path(path).read_bytes()) for path in expected} == expected


def test_qualified_facade_has_only_the_closed_import_and_identity_normalization() -> None:
    runtime = Path(
        "src/sc_referee/scientific_checks/code_csv_dependence_adapter_v2_1.py"
    ).read_text(encoding="utf-8")
    runtime = runtime.replace(
        "sc_referee.scientific_checks.code_csv_dependence_dataflow_v2_1",
        "sc_referee.scientific_checks.code_csv_dependence_dataflow",
    ).replace(
        "sc_referee.scientific_checks.report_csv_dependence_adapter_v2_1",
        "sc_referee.scientific_checks.report_csv_dependence_adapter",
    )
    identity_start = runtime.index("_FROZEN_ADAPTER_SOURCE = (")
    identity_end = runtime.index("\n\n\n@dataclass", identity_start)
    runtime = (
        runtime[:identity_start] + "CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST = "
        "adapter_implementation_digest(Path(__file__))" + runtime[identity_end:]
    )
    frozen = (_FROZEN / "code_csv_dependence_adapter.py").read_text(encoding="utf-8")
    assert runtime == frozen


@pytest.mark.parametrize("case_id", _CANDIDATES)
def test_normal_qualified_path_restores_one_envelope_5_finding_and_replay(
    schema_root: Path, tmp_path: Path, case_id: str
) -> None:
    source = _ENVELOPE_5 / case_id
    project = tmp_path / f"project-{case_id}"
    shutil.copytree(source / "project", project)
    output = tmp_path / f"audit-{case_id}"
    bundle = run_audit(
        project,
        output,
        schema_root,
        material_inputs=(_material_path(source),),
        method_contract_lock=source / "method-contract/semantic.lock.json",
    )
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    assert lock["scientific_check_registry"]["binding_lane"] == "qualified"
    assert lock["scientific_check_registry"]["production_promotion_permitted"] is True
    assert [item["title"] for item in bundle["findings"]] == [_TITLE]
    replayed = replay(output / "semantic.lock.json", tmp_path / f"replay-{case_id}", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]


def test_qualified_lane_never_backward_migrates_a_development_contract(
    schema_root: Path, tmp_path: Path
) -> None:
    project = tmp_path / "newer-contract-project"
    shutil.copytree(_K_CASE, project)
    seen = []
    bundle = run_audit(
        project,
        tmp_path / "newer-contract-audit",
        schema_root,
        report="results/report.md",
        material_inputs=(_material_path_from_lock(_K_DEVELOPMENT_LOCK),),
        method_contract_lock=_K_DEVELOPMENT_LOCK,
        evaluation_inspection_observer=seen.append,
    )
    assert len(seen) == 1
    assert seen[0].shared_derivations == ()
    assert bundle["findings"] == []


def test_cli_development_lane_is_explicit_and_never_promotes(
    schema_root: Path, tmp_path: Path
) -> None:
    case_id = _CANDIDATES[0]
    source = _ENVELOPE_5 / case_id
    project = tmp_path / "project-development"
    shutil.copytree(source / "project", project)
    output = tmp_path / "audit-development"
    result = CliRunner().invoke(
        app,
        [
            "audit",
            str(project),
            "--output",
            str(output),
            "--schema-root",
            str(schema_root),
            "--method-contract-lock",
            str(source / "method-contract/semantic.lock.json"),
            "--material-input",
            _material_path(source),
            "--development-lane",
        ],
    )
    assert result.exit_code == 0, result.output
    bundle = json.loads((output / "audit.bundle.json").read_text(encoding="utf-8"))
    lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    assert lock["scientific_check_registry"]["binding_lane"] == "development"
    assert lock["scientific_check_registry"]["production_promotion_permitted"] is False
    assert bundle["findings"] == []
    dependence_results = [
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == "detector:bounded-code-csv-dependence-conflict"
    ]
    assert len(dependence_results) == 1
    assert dependence_results[0]["detector_version"] == "3.0.0"
