from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.capability_maturity_ledger import (
    DIMENSIONS,
    _calculation_entries,
    _capability_profile_entries,
    _scientific_check_entries,
    build_capability_maturity_ledger,
    default_capability_maturity_source_root,
)


def test_checked_in_sources_generate_six_independent_dimensions() -> None:
    ledger = build_capability_maturity_ledger(default_capability_maturity_source_root())
    assert ledger["dimensions"] == list(DIMENSIONS)
    assert ledger["entries"]
    assert all(tuple(entry["dimensions"]) == DIMENSIONS for entry in ledger["entries"])
    assert all("status" not in entry and "maturity" not in entry for entry in ledger["entries"])
    qualified = [
        entry
        for entry in ledger["entries"]
        if entry["dimensions"]["finding_qualified"]["state"] == "supported"
    ]
    assert {entry["capability_id"] for entry in qualified} == {
        "check:authorized-independent-unit-entry-into-row-independent-procedure",
        "check:complete-domain-exposure-denominator",
    }


def test_checked_in_private_ledger_matches_current_source_manifests() -> None:
    root = Path(__file__).resolve().parents[1]
    checked_in = json.loads(
        (root / "docs/implementation/CAPABILITY_MATURITY_LEDGER.json").read_text(encoding="utf-8")
    )

    assert checked_in == build_capability_maturity_ledger(default_capability_maturity_source_root())


def test_calculation_recognition_does_not_infer_candidate() -> None:
    registry: dict[str, Any] = {
        "production_finding_permitted": False,
        "modules": [
            {
                "check_manifest": {"check_id": "calculation-check:example"},
                "adapter_manifests": [{"adapter_id": "adapter:example"}],
                "comparison_relation": "exact_example_comparison",
                "output_ceiling": "disclosure_only",
            }
        ],
    }
    dimensions = _calculation_entries(registry)[0]["dimensions"]
    assert dimensions["recognized"]["state"] == "supported"
    assert dimensions["impact_tested"]["state"] == "supported"
    assert dimensions["evaluation_candidate"]["state"] == "not_evidenced"
    assert dimensions["finding_qualified"]["state"] == "not_evidenced"


def test_scientific_binding_does_not_infer_candidate_or_qualification() -> None:
    registry: dict[str, Any] = {
        "modules": [
            {
                "check_id": "check:example",
                "check_version": "1.0.0",
                "manifest_digest": "sha256:module",
                "adapters": [{"adapter_id": "adapter:example"}],
            }
        ],
        "method_conflict_bindings": [
            {
                "binding_id": "binding:example",
                "check_id": "check:example",
                "check_version": "1.0.0",
                "check_manifest_digest": "sha256:module",
                "detector_id": "detector:example",
                "counterevidence_predicates": ["counterevidence"],
                "required_assertion_roles": ["reported"],
                "required_evidence_planes": ["reported_text"],
                "required_semantic_roles": ["method"],
            }
        ],
    }
    dimensions = _scientific_check_entries(registry)[0]["dimensions"]
    assert dimensions["structurally_verified"]["state"] == "supported"
    assert dimensions["evaluation_candidate"]["state"] == "not_evidenced"
    assert dimensions["finding_qualified"]["state"] == "not_evidenced"


def test_scientific_binding_reports_only_an_exact_installed_grant() -> None:
    registry: dict[str, Any] = {
        "modules": [
            {
                "check_id": "check:example",
                "check_version": "1.0.0",
                "manifest_digest": "sha256:module",
                "adapters": [{"adapter_id": "adapter:example"}],
            }
        ],
        "method_conflict_bindings": [
            {
                "binding_id": "binding:example",
                "check_id": "check:example",
                "check_version": "1.0.0",
                "check_manifest_digest": "sha256:module",
                "detector_id": "detector:example",
                "counterevidence_predicates": ["counterevidence"],
                "required_assertion_roles": ["reported"],
                "required_evidence_planes": ["reported_text"],
                "required_semantic_roles": ["method"],
            }
        ],
    }
    dimensions = _scientific_check_entries(registry, {"binding:example": "qualification:example"})[
        0
    ]["dimensions"]
    assert dimensions["finding_qualified"] == {
        "state": "supported",
        "basis": ["binding binding:example", "installed qualification qualification:example"],
    }


def test_profile_dimensions_fail_closed_without_cross_dimension_inference() -> None:
    profile: dict[str, Any] = {
        "capability_entry_id": "capability:example",
        "parser_refs": [{"record_type": "parser_manifest", "record_id": "parser:example"}],
        "detector_refs": [{"record_type": "detector_manifest", "record_id": "detector:example"}],
        "syntax_recognition": "partial",
        "operation_extraction": "partial",
        "semantic_modeling": "partial",
    }
    detector: dict[str, Any] = {
        "detector_id": "detector:example",
        "maturity": "experimental",
        "counterevidence_protocol": [{"check_id": "counterevidence"}],
        "required_evidence": ["exact evidence"],
        "test_fixtures": {
            "positive": ["test_positive"],
            "counterevidence": ["test_counterevidence"],
            "verified_good_negative": ["test_negative"],
        },
        "validation": {
            "status": "development_only",
            "evaluation_ref": "evaluation:example",
            "qualification_record_ref": None,
        },
        "extensions": {"x-production-finding-permitted": False},
    }
    no_recognition = deepcopy(profile)
    no_recognition["operation_extraction"] = "not_started"
    projected = _capability_profile_entries([no_recognition], [detector], [])[0]
    assert projected["dimensions"]["recognized"]["state"] == "not_evidenced"
    assert projected["dimensions"]["structurally_verified"]["state"] == "supported"
    assert projected["dimensions"]["evaluation_candidate"]["state"] == "supported"

    no_positive = deepcopy(detector)
    no_positive["test_fixtures"]["positive"] = []
    projected = _capability_profile_entries([profile], [no_positive], [])[0]
    assert projected["dimensions"]["evaluation_candidate"]["state"] == "not_evidenced"
    assert projected["dimensions"]["recognized"]["state"] == "supported"
    assert projected["dimensions"]["finding_qualified"]["state"] == "not_evidenced"
