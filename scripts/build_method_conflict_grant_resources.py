from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.detectors.method_conflict_grant_pins import live_adapter_identity
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "src/sc_referee/resources/qualification-grants-v1"
QUALIFICATIONS = (
    ROOT / "src/sc_referee/resources/capability-manifests-v1/qualification-manifests.json"
)
SCHEMA_ROOT = ROOT / "reference/schemas-v0.19.0"
METRIC_PATHS = (
    ROOT
    / "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-direct-lane/promotion-round2/QUALIFICATION_METRIC_SET.json",
    ROOT
    / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/promotion-round2/QUALIFICATION_METRIC_SET.json",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or path.read_text(encoding="utf-8") != canonical_json(value) + "\n"
    ):
        raise RuntimeError(f"input is not canonical JSON: {path}")
    return value


def build_grant_resources(output: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if output.exists() and (output.is_symlink() or any(output.iterdir())):
        raise RuntimeError(f"grant output must be absent or empty: {output}")
    qualification_collection = _load(QUALIFICATIONS)
    qualifications = qualification_collection.get("records")
    if not isinstance(qualifications, list) or len(qualifications) != 2:
        raise RuntimeError("exactly two installed qualifications are required")
    metric_sets = sorted(
        (_load(path) for path in METRIC_PATHS), key=lambda item: item["metric_set_id"]
    )
    qualification_by_binding = {
        item["binding_scope"]["binding_id"]: item for item in qualifications
    }
    metric_by_binding = {item["binding_scope"]["binding_id"]: item for item in metric_sets}
    if set(qualification_by_binding) != set(metric_by_binding) or len(metric_by_binding) != 2:
        raise RuntimeError("qualification and metric-set binding domains must match exactly")

    schema_registry = LocalSchemaRegistry(SCHEMA_ROOT)
    registry = scientific_check_release_registry()
    binding_by_id = {item.binding_id: item for item in registry.method_conflict_bindings}
    grants: list[dict[str, Any]] = []
    for binding_id in sorted(qualification_by_binding):
        qualification = qualification_by_binding[binding_id]
        metric_set = metric_by_binding[binding_id]
        binding = binding_by_id.get(binding_id)
        identities = live_adapter_identity(binding) if binding is not None else None
        counts = metric_set.get("counts")
        policy = metric_set.get("numeric_threshold_policy")
        if (
            binding is None
            or identities is None
            or not isinstance(counts, dict)
            or not isinstance(policy, dict)
        ):
            raise RuntimeError("grant evidence cannot be bound to the live registry")
        schema_registry.validate(qualification)
        schema_registry.validate(metric_set)
        if (
            qualification.get("binding_scope") != metric_set.get("binding_scope")
            or qualification["binding_scope"]["production_binding_digest"] != binding.binding_digest
            or qualification["binding_scope"]["detector_manifest_digest"]
            != binding.detector_manifest_digest
            or counts.get("missed_roots") != 0
            or counts.get("adjudicated_roots") != 2
        ):
            raise RuntimeError("grant evidence does not satisfy the installed absolute gates")
        grants.append(
            {
                "absolute_missed_roots": 0,
                "binding_digest": binding.binding_digest,
                "binding_id": binding.binding_id,
                "check_id": binding.check_id,
                "check_manifest_digest": binding.check_manifest_digest,
                "check_version": binding.check_version,
                "detector_id": binding.detector_id,
                "detector_manifest_digest": binding.detector_manifest_digest,
                "detector_version": binding.detector_version,
                "exam_adapter_identity": [asdict(item) for item in identities],
                "metric_set_digest": semantic_digest(metric_set),
                "metric_set_id": metric_set["metric_set_id"],
                "qualification_digest": semantic_digest(qualification),
                "qualification_id": qualification["qualification_id"],
                "required_roots": 2,
                "threshold_policy_digest": policy["policy_semantic_digest"],
            }
        )

    metric_collection = {
        "manifest_kind": "qualification_metric_set_collection",
        "manifest_version": "1.0.0",
        "records": metric_sets,
    }
    metric_payload = (canonical_json(metric_collection) + "\n").encode()
    descriptor = {
        "grant_set_kind": "method_conflict_qualification_grant_set_v1",
        "grant_set_version": "1.0.0",
        "grants": grants,
        "metric_set_collection": {
            "digest": sha256_digest(metric_payload),
            "path": "metric-sets.json",
        },
        "qualification_manifest_digest": sha256_digest(QUALIFICATIONS.read_bytes()),
        "schema_version": "0.19.0",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "metric-sets.json").write_bytes(metric_payload)
    (output / "grant-set.json").write_text(canonical_json(descriptor) + "\n", encoding="utf-8")
    return descriptor, metric_collection


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the installed method-conflict grant set")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    descriptor, _ = build_grant_resources(args.output)
    print(f"Built {len(descriptor['grants'])} binding-scoped qualification grants.")


if __name__ == "__main__":
    main()
