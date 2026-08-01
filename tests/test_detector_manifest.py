import json

import pytest

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.manifest import (
    DetectorManifestError,
    fixture_envelope_applies,
    load_fixture_detector_envelope,
)


def test_fixture_manifest_loads_pinned_nonpublic_envelope(project_root) -> None:
    path = project_root / "examples" / "walking-skeleton" / "fixture-detector-manifest.json"
    digest = sha256_digest(path.read_bytes())
    envelope = load_fixture_detector_envelope(path, digest)
    lock = {
        "fixture_mode": True,
        "fixture_id": envelope.fixture_id,
        "detector_manifest_digest": digest,
        "fixture_detector_envelope": envelope.to_lock_record(),
    }
    assert envelope.public_qualification_claimed is False
    assert envelope.counterevidence_check_ids == (
        "check:orientation",
        "check:scale",
        "check:report-qualification",
        "check:lineage-target",
    )
    assert fixture_envelope_applies(
        lock,
        detector_id="detector:claim-result-direction",
        detector_version="0.1.0",
        fixture_id="fixture:walking-skeleton-direction",
    )


def test_fixture_manifest_rejects_digest_or_public_qualification(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "manifest_kind": "synthetic_fixture_test_double",
                "fixture_id": "fixture:test",
                "detector_id": "detector:test",
                "detector_version": "0.1.0",
                "schema_maturity_simulated": "validated",
                "public_qualification_claimed": True,
                "purpose": "test",
                "counterevidence_checks": ["one"],
                "prohibited_use": "public use",
            }
        ),
        encoding="utf-8",
    )
    digest = sha256_digest(path.read_bytes())
    with pytest.raises(DetectorManifestError, match="deny public qualification"):
        load_fixture_detector_envelope(path, digest)
    with pytest.raises(DetectorManifestError, match="digest mismatch"):
        load_fixture_detector_envelope(path, "sha256:" + "0" * 64)
