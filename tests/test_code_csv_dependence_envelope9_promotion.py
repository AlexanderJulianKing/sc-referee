from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.method_conflict_finding import (
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
)
from sc_referee.detectors.method_conflict_grant_pins import (
    GRANT_PINS,
    installed_pin_matches_live_identity,
)

_BINDING_ID = (
    "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
)
_PROVENANCE = (
    "derived by Codex from envelope 9; installed under Alex's standing full-steam "
    "authorization via Fable"
)
_TITLE = "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"
_ENVELOPE = Path("evaluation/development/blind-envelope-9-2026-08-23")
_PROMOTION = Path(
    "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v3.1.0-code-csv-lane/envelope-9-promotion-v021"
)
_HISTORY = Path(
    "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v2.1.0-code-csv-lane/envelope-5-promotion-v020/RETIRED_DEPENDENCE_PIN.json"
)
_POSITIVES = (
    "fe7eeea19d8fddd7811e",
    "14af9fba001740a9e72a",
    "a72fdcf9cfa1784e9315",
    "b8b21229f40a115d5e69",
    "2657fda9a6eea027c423",
    "284256146298ea19cd75",
)
_NEGATIVES = (
    "ceb266a478e7ff5d4618",
    "6dffe3d7986dc5675127",
    "fd2f52a4099e1cbdfc8a",
    "4e9bd2ac9d532a4b45e8",
    "1feb6d2c4e4dce950eae",
    "3f12b75d274abe3a875f",
)
_NONCANONICAL_REPLAY_FIELDS = {"storage_manifests", "audit_runs", "stage_results"}


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _material_path(case_root: Path) -> str:
    lock = _load(case_root / "method-contract/semantic.lock.json")
    profile = lock["method_contract_profile"]
    assert isinstance(profile, dict)
    manifest = profile["profile_manifest"]
    assert isinstance(manifest, dict)
    snapshot = manifest["authority_binding_snapshot"]
    assert isinstance(snapshot, dict)
    authority = snapshot["authorized_independent_unit_key"]
    assert isinstance(authority, dict)
    return str(authority["material_input_path"])


def test_envelope9_step10_artifacts_and_retired_pin_are_exact() -> None:
    qualification = _load(_PROMOTION / "DETECTOR_QUALIFICATION.json")
    metric = _load(_PROMOTION / "QUALIFICATION_METRIC_SET.json")
    threshold = _load(_PROMOTION / "THRESHOLD_RECORD.json")
    finding_profile = _load(_PROMOTION / "FINDING_PROFILE_BINDING.json")
    replacement = _load(_PROMOTION / "REPLACEMENT_DEPENDENCE_PIN.json")
    retired = _load(_HISTORY)

    assert semantic_digest(qualification) == (
        "sha256:a25edd25e5198a75d436a335313c7e40a695bac63860bc0e3af4ebb9b01b33f0"
    )
    assert semantic_digest(metric) == (
        "sha256:494ee752e8a62770f444f62c5b1b317b52477ea2ad03c3a922e4285830a53f41"
    )
    assert threshold["threshold_policy"]["policy_semantic_digest"] == (
        "sha256:819973ff04ad136c7b80bb23cb46ab67b5cfd3d3384656488094950498291d57"
    )
    assert finding_profile["finding_profile_digest"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST
    )
    assert replacement["pin_payload_semantic_digest"] == (
        "sha256:3a7eb7d64e8084967f44635ac144b204ba1f1f7de85754bcb3ddc786dc8f9295"
    )
    assert replacement["provenance_statement"] == _PROVENANCE
    assert replacement["replaces_installed_qualification_id"] == (
        "qualification:authorized-independent-unit-entry-v210-code-csv-envelope5"
    )
    assert retired["retired_pin_payload"]["detector_version"] == "2.1.0"
    assert retired["retired_pin_payload"]["qualification_id"] == (
        "qualification:authorized-independent-unit-entry-v210-code-csv-envelope5"
    )
    assert metric["counts"]["bounded_root_matches"] == 6
    assert metric["counts"]["false_root_localizations"] == 0
    assert metric["counts"]["missed_roots"] == 0

    pin = GRANT_PINS[_BINDING_ID]
    assert pin.detector_version == "3.1.0"
    assert pin.finding_profile_digest == CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST
    assert installed_pin_matches_live_identity(pin) is True
    assert (
        installed_pin_matches_live_identity(
            GRANT_PINS["method-conflict-binding:complete-domain-exposure-denominator-v1"]
        )
        is True
    )


@pytest.mark.parametrize(
    ("case_id", "expected_findings"),
    [(case_id, 1) for case_id in _POSITIVES] + [(case_id, 0) for case_id in _NEGATIVES],
)
def test_envelope9_qualified_audit_and_model_free_replay_are_exact(
    schema_root: Path,
    tmp_path: Path,
    case_id: str,
    expected_findings: int,
) -> None:
    source = _ENVELOPE / "cases" / case_id
    project = tmp_path / f"project-{case_id}"
    shutil.copytree(source / "project", project)
    audit_output = tmp_path / f"audit-{case_id}"
    bundle = run_audit(
        project,
        audit_output,
        schema_root,
        material_inputs=(_material_path(source),),
        method_contract_lock=source / "method-contract/semantic.lock.json",
    )

    assert len(bundle["findings"]) == expected_findings
    if expected_findings:
        finding = bundle["findings"][0]
        assert finding["title"] == _TITLE
        assert finding["summary"].endswith(
            "The declared unit column may be one component of a composite key."
        )
        assert finding["extensions"]["x-finding-wording-profile-digest"] == (
            CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST
        )

    replayed = replay(
        audit_output / "semantic.lock.json",
        tmp_path / f"replay-{case_id}",
        schema_root,
    )
    canonical_fields = {
        key
        for key, value in bundle.items()
        if isinstance(value, (dict, list)) and key not in _NONCANONICAL_REPLAY_FIELDS
    }
    assert {key: replayed[key] for key in canonical_fields} == {
        key: bundle[key] for key in canonical_fields
    }
