from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest


class DetectorManifestError(ValueError):
    """Raised when a detector manifest cannot support its declared fixture envelope."""


@dataclass(frozen=True)
class FixtureDetectorEnvelope:
    fixture_id: str
    detector_id: str
    detector_version: str
    simulated_maturity: str
    manifest_digest: str
    counterevidence_check_ids: tuple[str, ...]
    public_qualification_claimed: bool

    def to_lock_record(self) -> dict[str, Any]:
        return {
            "envelope_kind": "synthetic_fixture_test_double",
            "fixture_id": self.fixture_id,
            "detector_id": self.detector_id,
            "detector_version": self.detector_version,
            "simulated_maturity": self.simulated_maturity,
            "manifest_digest": self.manifest_digest,
            "counterevidence_check_ids": list(self.counterevidence_check_ids),
            "public_qualification_claimed": self.public_qualification_claimed,
            "finding_permission": "synthetic_fixture_only",
        }


def load_fixture_detector_envelope(path: Path, expected_digest: str) -> FixtureDetectorEnvelope:
    payload = path.read_bytes()
    actual_digest = sha256_digest(payload)
    if actual_digest != expected_digest:
        raise DetectorManifestError("fixture detector manifest digest mismatch")
    try:
        manifest = json.loads(payload)
    except json.JSONDecodeError as error:
        raise DetectorManifestError("fixture detector manifest is not valid JSON") from error
    if not isinstance(manifest, dict):
        raise DetectorManifestError("fixture detector manifest must be an object")

    required_strings = {
        field: manifest.get(field)
        for field in (
            "manifest_kind",
            "fixture_id",
            "detector_id",
            "detector_version",
            "schema_maturity_simulated",
            "purpose",
            "prohibited_use",
        )
    }
    if not all(isinstance(value, str) and value for value in required_strings.values()):
        raise DetectorManifestError("fixture detector manifest is missing required text fields")
    if manifest["manifest_kind"] != "synthetic_fixture_test_double":
        raise DetectorManifestError("detector manifest is not an isolated synthetic fixture")
    if manifest.get("public_qualification_claimed") is not False:
        raise DetectorManifestError("fixture detector manifest must deny public qualification")
    maturity = manifest["schema_maturity_simulated"]
    if maturity not in {"validated", "publication_grade"}:
        raise DetectorManifestError("fixture maturity cannot exercise Finding admission")
    checks = manifest.get("counterevidence_checks")
    if (
        not isinstance(checks, list)
        or not checks
        or not all(isinstance(check, str) and check for check in checks)
        or len(set(checks)) != len(checks)
    ):
        raise DetectorManifestError("fixture counterevidence protocol is invalid")
    return FixtureDetectorEnvelope(
        fixture_id=manifest["fixture_id"],
        detector_id=manifest["detector_id"],
        detector_version=manifest["detector_version"],
        simulated_maturity=maturity,
        manifest_digest=actual_digest,
        counterevidence_check_ids=tuple(f"check:{check}" for check in checks),
        public_qualification_claimed=False,
    )


def fixture_envelope_applies(
    locked_case: dict[str, Any],
    *,
    detector_id: str,
    detector_version: str,
    fixture_id: str,
) -> bool:
    envelope = locked_case.get("fixture_detector_envelope")
    if not isinstance(envelope, dict):
        return False
    return (
        locked_case.get("fixture_mode") is True
        and locked_case.get("fixture_id") == fixture_id
        and envelope.get("envelope_kind") == "synthetic_fixture_test_double"
        and envelope.get("fixture_id") == fixture_id
        and envelope.get("detector_id") == detector_id
        and envelope.get("detector_version") == detector_version
        and envelope.get("simulated_maturity") in {"validated", "publication_grade"}
        and envelope.get("manifest_digest") == locked_case.get("detector_manifest_digest")
        and envelope.get("public_qualification_claimed") is False
        and envelope.get("finding_permission") == "synthetic_fixture_only"
    )


def locked_counterevidence_check_ids(locked_case: dict[str, Any]) -> tuple[str, ...]:
    envelope = locked_case.get("fixture_detector_envelope")
    if not isinstance(envelope, dict):
        return ()
    checks = envelope.get("counterevidence_check_ids")
    if not isinstance(checks, list) or not all(isinstance(check, str) for check in checks):
        return ()
    return tuple(checks)
