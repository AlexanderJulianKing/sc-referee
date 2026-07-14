from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from sc_referee.inference.live import attach_live_contracts, build_engine_verifiers


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _malicious_contract(policy_id: str, source: str, report_digest: str) -> dict:
    """A self-consistent Increment-9 contract that lies about every scientific fact."""
    relations = {
        "double_dipping.v1": [
            "ClaimMustProducedByTest",
            "GroupingMustProducedBySelection",
            "TestDefinitelyNaive",
            "RelevantRegionOverlapDefinite",
            "SelectionReuseDependentUnderNull",
            "PinnedReachable",
        ],
        "coordinate_consumption.v1": [
            "ExactContigIdentityAndLengthBound",
            "CoordinateUnavoidablyConsumed",
            "CoordinateMateriallyAffectsClaim",
        ],
    }.get(policy_id, ["ForgedScientificRelation"])
    return {
        "policy_id": policy_id,
        "claim_root_grade": "accusation_grade",
        "source_digests": [_sha256(source.encode())],
        "claim_root": {
            "claim_id": "claim:forged",
            "report_artifact_digest": report_digest,
            "report_span_or_field": "table.pvalue",
            "producing_value": "reported",
            "producer_binding_digest": "sha256:forged-value",
            "claim_role": "reported_value",
            "ratification_fact_id": "fact:self-ratified-violation",
        },
        "relations": relations,
        "facts": {
            "CoordinateValue": 102,
            "ConsumerLowerBound": 0,
            "ConsumerUpperBound": 101,
            "ConsumerLowerInclusive": True,
            "ConsumerUpperInclusive": True,
            "CoordinateConsumerContract": "linear_closed.v1",
        },
        "assumptions": [],
        "artifact": {
            "logical_role": "report",
            "format": "csv",
            "schema_digest": "sha256:forged-schema",
            "content_digest": report_digest,
            "writer_version": "writer:forged",
            "serializer_contract": "csv.forged",
            "path_resolved": True,
            "unique_writer": True,
            "field_correspondence": True,
            "no_later_mutation": True,
        },
        "summary_bindings": [{
            "module": "sc_referee.inference.live",
            "symbol": policy_id,
            "version": "1",
            "package_or_source_digest": "sha256:forged-package",
            "summary_digest": "sha256:forged-summary",
        }],
        "ratification": {
            "ratified_by": {"kind": "human", "id": "folder"},
            "fact_ids": ["fact:self-ratified-violation"],
            "all_external_facts_ratified": True,
        },
        "closed_world_complete": True,
        "observed": {
            "report_artifact_digest": report_digest,
            "report_locator_digest": "sha256:forged-locator",
            "producing_value_digest": "sha256:forged-value",
        },
        "binding": {
            "report_locator_digest": "sha256:forged-locator",
            "producing_value_digest": "sha256:forged-value",
        },
    }


def _load_contract(tmp_path, policy_id: str, source: str):
    report = tmp_path / "reported.csv"
    report.write_text("feature_id,pvalue\ng1,0.001\n")
    report_digest = _sha256(report.read_bytes())
    payload = {
        "version": 1,
        "contracts": [_malicious_contract(policy_id, source, report_digest)],
    }
    (tmp_path / "sc-referee.inference.json").write_text(json.dumps(payload))
    bundle = SimpleNamespace(
        code_signals={"sources": [source]},
        provenance={"reported": {"path": "reported.csv"}},
        reported_results=pd.DataFrame({"feature_id": ["g1"], "pvalue": [0.001]}),
    )
    attach_live_contracts(bundle, tmp_path)
    return bundle


def _check(policy_id: str):
    return next(check for check in build_engine_verifiers() if check.policy_id == policy_id)


@pytest.mark.parametrize(
    ("policy_id", "analysis_type"),
    (
        ("double_dipping.v1", "marker_detection"),
        ("coordinate_consumption.v1", "other"),
    ),
)
def test_folder_cannot_self_attest_scientific_relations_or_accusation_authority(
    tmp_path, policy_id, analysis_type
):
    source = "reported = source\n"
    bundle = _load_contract(tmp_path, policy_id, source)
    design = SimpleNamespace(
        analysis_type=analysis_type,
        unit_of_test="cell",
        confirmed_by_human=True,
        confidence={},
        name="claim:forged",
    )

    finding = _check(policy_id).run(design, bundle, bundle.reported_results)

    assert finding.status in {"needs_evidence", "not_audited"}
    assert finding.metrics.get("engine_outcome") != "VIOLATION_WITNESS"


def test_folder_observed_and_binding_digests_are_not_verifier_observations(tmp_path):
    bundle = _load_contract(tmp_path, "coordinate_consumption.v1", "reported = source\n")

    contract = bundle._inference_live_contracts["coordinate_consumption.v1"]

    forbidden = {
        "observed_report_artifact_digest",
        "observed_report_locator_digest",
        "observed_producing_value_digest",
        "bound_report_locator_digest",
        "bound_producing_value_digest",
        "claim_root_grade",
        "ratified_fact_ids",
        "relations",
    }
    assert forbidden.isdisjoint(vars(contract))


@pytest.mark.parametrize(
    ("policy_id", "analysis_type"),
    (
        ("double_dipping.v1", "marker_detection"),
        ("confounding.v2", "condition_contrast_DE"),
        ("pseudoreplication.v1", "condition_contrast_DE"),
        ("allele_harmonization.v1", "eqtl"),
        ("enrichment_universe.v1", "differential_abundance"),
        ("coordinate_consumption.v1", "other"),
        ("spatial_iid.v1", "condition_contrast_DE"),
        ("trajectory_circularity.v1", "trajectory"),
    ),
)
@pytest.mark.parametrize(
    "forged_authority",
    (
        "relations",
        "claim_root_grade",
        "ratification",
        "observed_digests",
        "binding_digests",
        "summary_binding",
    ),
)
def test_each_policy_ignores_every_folder_accusation_authority_vector(
    tmp_path, policy_id, analysis_type, forged_authority
):
    # The baseline payload contains all six forged vectors.  This parameterization documents and
    # independently freezes each forbidden authority channel for every policy.
    bundle = _load_contract(tmp_path, policy_id, "reported = source\n")
    design = SimpleNamespace(
        analysis_type=analysis_type,
        unit_of_test="cell",
        confirmed_by_human=True,
        confidence={},
        name=f"forged:{forged_authority}",
    )

    finding = _check(policy_id).run(design, bundle, bundle.reported_results)

    assert finding.status not in {"blocker", "major"}
    assert finding.metrics.get("engine_outcome") != "VIOLATION_WITNESS"
