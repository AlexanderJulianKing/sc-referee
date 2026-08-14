"""Unregistered development-only shadow adapter for dependence growth-1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition_v2.python_analyzer import (
    analyze_dependence_growth_python,
    discharge_dependence_growth_analysis,
)
from sc_referee.scientific_checks.core import FrozenInspectionContext

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
_EXPERIMENT = "docs/implementation/EXPERIMENT-0060-DEPENDENCE-SEMANTIC-V2-GROWTH.md"
DEPENDENCE_V2_PACKAGE_FILES = (
    "__init__.py",
    "adapter.py",
    "certificate.py",
    "csv_domain.py",
    "ir.py",
    "python_analyzer.py",
)
DEPENDENCE_V2_DEPENDENCY_FILES = (
    *(f"src/sc_referee/dependence_recognition_v2/{name}" for name in DEPENDENCE_V2_PACKAGE_FILES),
    "src/sc_referee/dependence_recognition/csv_domain.py",
    "src/sc_referee/dependence_recognition/ir.py",
    "src/sc_referee/dependence_recognition/python_analyzer.py",
    _EXPERIMENT,
)


def dependence_v2_dependency_closure() -> dict[str, str]:
    return {
        path: sha256_digest((_ROOT / path).read_bytes()) for path in DEPENDENCE_V2_DEPENDENCY_FILES
    }


@dataclass(frozen=True)
class DependenceRecognitionV2ShadowAdapter:
    """Inspect one frozen context; every uncertainty is non-accusatory."""

    adapter_id: str = "dependence-recognition-semantic-v2-growth-shadow"
    adapter_version: str = "2.0.0-development"

    def inspect(self, context: FrozenInspectionContext) -> dict[str, Any]:
        try:
            analysis = analyze_dependence_growth_python(context)
            discharged = discharge_dependence_growth_analysis(analysis, context)
        except BaseException:
            return self._abstention(("v2-shadow-pipeline-exception",))
        closure = dependence_v2_dependency_closure()
        common = {
            "record_type": "dependence_recognition_v2_shadow_result",
            "schema_version": "2.0.0-development",
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "adapter_implementation_digest": semantic_digest({"dependency_closure": closure}),
            "implementation_dependency_closure": closure,
            "delivery_plane": "unregistered_development_shadow_only",
            "report_only": True,
            "production_finding_permitted": False,
        }
        if discharged.state == "question":
            return {
                **common,
                "payload_type": "material_question",
                "outcome": "question",
                "reason_code": "independent-unit-definition-unresolved",
                "candidate_key_columns": list(discharged.candidate_key_columns),
                "abstention_reasons": [],
            }
        verified = discharged.verified_certificate
        if discharged.state != "verified" or verified is None:
            return {**common, **self._abstention(discharged.abstention_reasons)}
        fact = verified.fact
        projection = {
            "source_path": verified.source_path,
            "source_digest": verified.source_digest,
            "resolved_callable": verified.resolved_callable,
            "input_path": fact.path,
            "input_content_digest": fact.content_digest,
            "authorized_unit_column": fact.authorized_unit_column,
            "group_key_column": fact.group_key_column,
            "value_column": fact.value_column,
            "bound_group_keys": [item.group_key for item in verified.operand_bindings],
            "certificate_id": verified.certificate_id,
        }
        if verified.conclusion == "repeated_units":
            return {
                **common,
                "payload_type": "shadow_candidate",
                "outcome": "evaluation_candidate",
                "reason_code": "repeated-unit-within-bound-operand",
                "abstention_reasons": [],
                "repeated_unit_ids": list(verified.repeated_unit_ids),
                "payload": projection,
            }
        return {
            **common,
            "payload_type": "coverage_note",
            "outcome": "covered_negative",
            "reason_code": "one-observation-per-unit-in-disjoint-bound-operands",
            "abstention_reasons": [],
            "repeated_unit_ids": [],
            "payload": projection,
        }

    def _abstention(self, reasons: tuple[str, ...]) -> dict[str, Any]:
        values = sorted(set(reasons or ("dependence-v2-shadow-abstention",)))
        return {
            "payload_type": "abstention",
            "outcome": "unsupported",
            "reason_code": values[0],
            "abstention_reasons": values,
            "accusatory_output": False,
        }
