import ast
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.founder_orientation_adapter import (
    FounderOrientationQualificationAdapter,
    founder_orientation_dependency_closure,
)
from sc_referee_evaluation.qualification_adapter_registry import (
    registered_qualification_adapter,
)
from sc_referee_evaluation.typed_method_qualification import (
    IndependentDeclaration,
    IndependentObservation,
    TypedMethodQualificationError,
    inspect_with_independent_adapter,
    qualify_typed_method_observations,
    verify_typed_method_case,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _binding(
    *,
    comparison_form: str = "value_equals",
    operand_kind: str = "canonical_scalar",
    planes: tuple[str, ...] = ("reported_text", "static_source"),
    forbidden: tuple[str, ...] = (),
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "binding_id": f"method-conflict-binding:test-{comparison_form}-v1",
        "check_id": f"check:test-{comparison_form}",
        "check_version": "1.0.0",
        "check_manifest_digest": "sha256:" + "1" * 64,
        "detector_id": "detector:bounded-analysis-method-conflict",
        "detector_version": "0.2.0",
        "detector_manifest_digest": "sha256:" + "2" * 64,
        "dimension": "measurement_model",
        "comparison_form": comparison_form,
        "operand_kind": operand_kind,
        "required_evidence_planes": list(planes),
        "required_semantic_roles": ["method_input", "method_target"],
        "required_assertion_roles": [
            role
            for plane, role in (
                ("reported_text", "reported"),
                ("static_source", "observed"),
            )
            if plane in planes
        ],
        "counterevidence_predicates": [
            "approved_method_deviation",
            "governing_protocol_amendment",
            "method_obligation_applicability",
        ],
        "forbidden_members": list(forbidden),
        "production_finding_permitted": False,
        "qualification_adapter": {
            "adapter_id": "qualification-adapter:test-r-v1",
            "adapter_version": "1.0.0",
            "entry_point": "sc_referee_evaluation.test_adapter:TestRAdapter",
            "implementation_digest": "sha256:" + "3" * 64,
            "dependency_closure": [
                {
                    "path": "sc_referee_evaluation/test_adapter.py",
                    "content_digest": "sha256:" + "3" * 64,
                }
            ],
            "imports_production_semantic_implementation": False,
        },
    }
    value["binding_digest"] = semantic_digest(value)
    return value


def _observation(plane: str, kind: str, value: object) -> IndependentObservation:
    return IndependentObservation(
        evidence_plane=plane,  # type: ignore[arg-type]
        operand_kind=kind,  # type: ignore[arg-type]
        operand=value,
        declarations=(
            IndependentDeclaration(
                evidence_plane=plane,  # type: ignore[arg-type]
                path="report.md" if plane == "reported_text" else "analysis.R",
                start_line=1,
                end_line=1,
                retained_text="independently retained declaration",
            ),
        ),
        candidate_paths=("analysis.R", "report.md"),
        scope_join_path=(
            {
                "source_ref": {"record_type": "artifact", "record_id": "artifact:source"},
                "relation": "selected_by_publication_surface",
                "target_ref": {
                    "record_type": "publication_surface",
                    "record_id": "surface:selected",
                },
            },
        ),
    )


def _checks(outcome: str) -> list[dict[str, str]]:
    return [
        {
            "check_id": "closed-check",
            "completion_status": "completed",
            "outcome": outcome,
        }
    ]


def _authority() -> dict[str, dict[str, object]]:
    return {
        "governing_question": {
            "record_ref": {"record_type": "material_question", "record_id": "question:test"},
            "semantic_digest": "sha256:" + "4" * 64,
        },
        "governing_answer": {
            "record_ref": {"record_type": "answer", "record_id": "answer:test"},
            "semantic_digest": "sha256:" + "5" * 64,
        },
        "governing_contract": {
            "record_ref": {
                "record_type": "scientific_contract",
                "record_id": "contract:test",
            },
            "semantic_digest": "sha256:" + "6" * 64,
        },
        "requirement_assertion": {
            "record_ref": {
                "record_type": "semantic_assertion",
                "record_id": "assertion:test",
            },
            "semantic_digest": "sha256:" + "7" * 64,
        },
    }


def test_report_only_scalar_extension_uses_configuration_and_closed_algebra() -> None:
    binding = _binding(planes=("reported_text",))
    result = qualify_typed_method_observations(
        binding=binding,
        requirement="method_a",
        observations=(_observation("reported_text", "canonical_scalar", "method_a"),),
        applicability_results=_checks("agreement"),
        counterevidence_results=_checks("counterevidence_absent"),
        authority_records=_authority(),
    )

    assert result["proof_status"] == "complete"
    assert result["qualification_outcome"] == "covered_negative"


class _IndependentRAdapter:
    adapter_id = "qualification-adapter:test-r-v1"
    adapter_version = "1.0.0"
    implementation_digest = "sha256:" + "3" * 64

    def inspect(
        self,
        retained_bytes: dict[str, bytes],
        assignment: dict[str, Any],
        binding: dict[str, Any],
    ) -> tuple[IndependentObservation, ...]:
        assert retained_bytes["analysis.R"] == b"observed <- 'method_b'\n"
        assert assignment["selected_report_path"] == "report.md"
        assert binding["check_id"] == "check:test-value_equals"
        return (
            _observation("reported_text", "canonical_scalar", "method_b"),
            _observation("static_source", "canonical_scalar", "method_b"),
        )


def test_second_language_adapter_is_explicitly_bound_and_independent() -> None:
    binding = _binding()
    observations = inspect_with_independent_adapter(
        adapter=_IndependentRAdapter(),
        retained_bytes={"analysis.R": b"observed <- 'method_b'\n"},
        assignment={"selected_report_path": "report.md"},
        binding=binding,
    )
    result = qualify_typed_method_observations(
        binding=binding,
        requirement="method_a",
        observations=observations,
        applicability_results=_checks("agreement"),
        counterevidence_results=_checks("counterevidence_absent"),
        authority_records=_authority(),
    )

    assert result["qualification_outcome"] == "exact_conflict_candidate"
    assert {item.evidence_plane for item in observations} == {
        "reported_text",
        "static_source",
    }


def test_ambient_or_unknown_qualification_adapter_is_not_discovered() -> None:
    with pytest.raises(TypedMethodQualificationError, match="explicit registry"):
        registered_qualification_adapter(_binding())


def test_founder_adapter_independently_rederives_both_planes_and_scope() -> None:
    adapter = FounderOrientationQualificationAdapter()
    binding = _binding()
    binding["check_id"] = "check:founder-orientation-before-hmm-emission"
    binding["dimension"] = "scale_and_orientation"
    binding["qualification_adapter"] = {
        "adapter_id": adapter.adapter_id,
        "adapter_version": adapter.adapter_version,
        "entry_point": (
            "sc_referee_evaluation.founder_orientation_adapter:"
            "FounderOrientationQualificationAdapter"
        ),
        "implementation_digest": adapter.implementation_digest,
        "dependency_closure": list(founder_orientation_dependency_closure()),
        "imports_production_semantic_implementation": False,
    }
    binding.pop("binding_digest")
    binding["binding_digest"] = semantic_digest(binding)
    file_ref = {"record_type": "file_record", "record_id": "file:analysis"}
    operation_ref = {"record_type": "operation", "record_id": "operation:writer"}
    artifact_ref = {"record_type": "artifact", "record_id": "artifact:report"}
    surface_ref = {
        "record_type": "publication_surface",
        "record_id": "surface:selected",
    }
    scope_path = [
        {
            "source_ref": file_ref,
            "relation": "contains_unique_static_selected_output_writer",
            "target_ref": operation_ref,
        },
        {
            "source_ref": operation_ref,
            "relation": "declares_selected_output_artifact",
            "target_ref": artifact_ref,
        },
        {
            "source_ref": artifact_ref,
            "relation": "selected_by_publication_surface",
            "target_ref": surface_ref,
        },
    ]
    source = (
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def emission(observed, founder_state):\n"
        "    return observed == founder_state\n"
        "def fit(sample, observed):\n"
        "    return emission(observed, sample.founder_alleles[0])\n"
        "def main():\n"
        "    (ROOT / 'report.md').write_text('report')\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )
    observations = inspect_with_independent_adapter(
        adapter=adapter,
        retained_bytes={
            "analysis.py": source.encode(),
            "report.md": (
                b"The founder-origin HMM was fitted using the supplied founder alleles.\n"
            ),
        },
        assignment={
            "selected_report_path": "report.md",
            "scope_source_path": "analysis.py",
            "scope_artifact_path": "report.md",
            "scope_join_path": scope_path,
            "scope_join_digest": semantic_digest(scope_path),
        },
        binding=binding,
    )

    assert [item.evidence_plane for item in observations] == [
        "reported_text",
        "static_source",
    ]
    assert {item.operand for item in observations} == {
        "use_supplied_founder_alleles_directly_in_hmm_emission"
    }
    assert len(observations[0].scope_join_path) == 1
    assert len(observations[1].scope_join_path) == 3


def test_step_relation_abstains_on_ambiguity_and_counterevidence() -> None:
    binding = _binding(comparison_form="step_precedes", operand_kind="ordered_step_names")
    report = _observation("reported_text", "ordered_step_names", ["calibrate", "weight"])
    source = _observation("static_source", "ordered_step_names", ["calibrate", "weight"])

    ambiguous = qualify_typed_method_observations(
        binding=binding,
        requirement=["weight", "calibrate"],
        observations=(report, report, source),
        applicability_results=_checks("agreement"),
        counterevidence_results=_checks("counterevidence_absent"),
        authority_records=_authority(),
    )
    counterevidence = qualify_typed_method_observations(
        binding=binding,
        requirement=["weight", "calibrate"],
        observations=(report, source),
        applicability_results=_checks("agreement"),
        counterevidence_results=_checks("counterevidence_present"),
        authority_records=_authority(),
    )
    conflict = qualify_typed_method_observations(
        binding=binding,
        requirement=["weight", "calibrate"],
        observations=(report, source),
        applicability_results=_checks("agreement"),
        counterevidence_results=_checks("counterevidence_absent"),
        authority_records=_authority(),
    )

    assert ambiguous["proof_status"] == "unavailable"
    assert counterevidence["proof_status"] == "unavailable"
    assert conflict["qualification_outcome"] == "exact_conflict_candidate"


def test_generic_engine_builds_one_public_v017_proof(project_root: Path) -> None:
    example_path = (
        project_root
        / "reference"
        / "schemas-v0.19.0"
        / "examples"
        / "static-qualification-proof.analysis-method.example.json"
    )
    example = json.loads(example_path.read_text(encoding="utf-8"))
    envelope_fields = {
        "schema_version",
        "record_type",
        "proof_id",
        "profile",
        "case_assignment_artifact",
        "label_freeze_artifact",
        "snapshot",
        "retained_bytes",
        "dependency_graph",
        "chronology",
        "provenance",
    }
    envelope = {field: deepcopy(example[field]) for field in envelope_fields}
    applicability = [
        {
            "check_id": "unique_selected_output_writer",
            "completion_status": "completed",
            "detail_code": "unique_supported_closure",
            "evidence_paths": ["analysis.R", "report.md"],
            "outcome": "agreement",
        }
    ]
    counterevidence = [
        {
            "check_id": "approved_method_deviation",
            "completion_status": "completed",
            "detail_code": "closed_search_complete",
            "evidence_paths": ["analysis.R", "report.md"],
            "outcome": "counterevidence_absent",
        }
    ]
    proof = verify_typed_method_case(
        proof_envelope=envelope,
        binding=_binding(),
        requirement="method_a",
        observations=(
            _observation("reported_text", "canonical_scalar", "method_b"),
            _observation("static_source", "canonical_scalar", "method_b"),
        ),
        applicability_results=applicability,
        counterevidence_results=counterevidence,
        authority_records=_authority(),
    )

    LocalSchemaRegistry(project_root / "reference" / "schemas-v0.19.0").validate(proof)
    assert proof["proof_status"] == "complete"
    assert proof["derived_facts"]["comparison"]["outcome"] == "exact_conflict_candidate"


def test_independent_engine_does_not_import_production_semantic_implementations() -> None:
    root = Path(__file__).resolve().parents[1] / "evaluation" / "src" / "sc_referee_evaluation"
    paths = [
        root / "typed_method_qualification.py",
        root / "qualification_adapter_registry.py",
        root / "founder_orientation_adapter.py",
    ]
    imported = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported.update(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )

    assert not any(
        name.startswith(
            (
                "sc_referee.detectors",
                "sc_referee.posthoc_method_ledger",
                "sc_referee.scientific_checks",
            )
        )
        for name in imported
    )
    assert all(sha256_digest(path.read_bytes()).startswith("sha256:") for path in paths)
