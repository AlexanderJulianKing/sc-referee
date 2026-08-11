from __future__ import annotations

import copy
import inspect
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import sc_referee.controller as controller
import sc_referee.detectors.method_conflict_grant_pins as grant_pins
from sc_referee.controller import (
    _derive_general_from_lock,
    _evaluate_general_detectors,
    replay,
    run_audit,
)
from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.method_conflict_qualification import (
    project_qualified_method_conflict_candidate,
    resolve_method_conflict_qualification,
)
from sc_referee.detectors.method_conflict_registry import (
    evaluate_registered_method_conflicts,
)
from sc_referee.reporting.policy import ReportContractError, _validate_detector_projection
from scripts.build_method_promotion_schema_candidate import build_candidate
from tests.test_evaluation_control_fixture import _lock_method_authority
from tests.test_method_conflict_qualification_authority import (
    _locked_candidate_case,
    _pin,
    _records,
)


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    output = tmp_path / "candidate"
    build_candidate(output)
    return output


def _write_method_conflict_repository(repository: Path) -> None:
    repository.mkdir()
    (repository / "analysis.py").write_text(
        "import csv\n"
        "import math\n"
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def emission_matrix(observed, founder_state, error):\n"
        "    return observed == founder_state\n"
        "def fit(sample, observed):\n"
        "    return emission_matrix(observed, sample.founder_alleles[0], 0.01)\n"
        "def main():\n"
        "    (ROOT / 'report.md').write_text(\n"
        "        'The parental marker panel as supplied and the progeny calls were compared marker by marker: 372 of the 480 markers agree.\\n\\nThe emission model used a per-marker agreement rate of 0.225.\\n'\n"
        "    )\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
        "rows = list(csv.DictReader((ROOT / 'markers.csv').open()))\n"
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "LIKELIHOOD = math.prod(\n"
        "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in panel\n"
        ")\n"
        "(ROOT / 'likelihood.txt').write_text(str(LIKELIHOOD))\n",
        encoding="utf-8",
    )
    (repository / "markers.csv").write_text("call,founder\n0,0\n1,1\n", encoding="utf-8")
    (repository / "report.md").write_text(
        "The parental marker panel as supplied and the progeny calls were compared marker "
        "by marker: 372 of the 480 markers agree.\n\n"
        "The emission model used a per-marker agreement rate of 0.225.\n",
        encoding="utf-8",
    )


def _resolver_arguments(
    project_root: Path, candidate: Path
) -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, Any], Any]:
    binding, manifest, metric_set, qualification = _records(project_root, candidate)
    return binding, manifest, metric_set, qualification, _pin(binding, metric_set, qualification)


def test_installed_grants_never_admit_an_ungranted_method_candidate(
    schema_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str | None] = []
    real_admit = controller.admit_finding

    def traced(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any] | None:
        calls.append(result.get("result_id"))
        return real_admit(result, context)

    monkeypatch.setattr(controller, "admit_finding", traced)
    repository = tmp_path / "founder"
    _write_method_conflict_repository(repository)

    bundle = _lock_method_authority(repository, schema_root, tmp_path)

    assert len(grant_pins.GRANT_PINS) == 2
    assert calls == []
    assert bundle["findings"] == []
    assert any(
        result["state"] == "evaluation_finding_candidate" for result in bundle["detector_results"]
    )


def test_installed_grants_preserve_unrelated_walking_skeleton_audit_replay(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str | None] = []
    real_admit = controller.admit_finding

    def traced(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any] | None:
        calls.append(result.get("result_id"))
        return real_admit(result, context)

    monkeypatch.setattr(controller, "admit_finding", traced)
    repository = tmp_path / "general-static"
    shutil.copytree(project_root / "examples" / "general-static", repository)
    output = tmp_path / "audit"
    bundle = run_audit(repository, output, schema_root, report="report.md")
    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)

    assert len(grant_pins.GRANT_PINS) == 2
    assert calls == []
    assert bundle["findings"] == []
    for field in (
        "detector_results",
        "findings",
        "coverage_records",
        "material_questions",
        "disclosures",
    ):
        assert replayed[field] == bundle[field]


def test_production_call_sites_expose_no_external_grant_parameter() -> None:
    assert "grant" not in inspect.signature(run_audit).parameters
    assert "grant" not in inspect.signature(_evaluate_general_detectors).parameters
    assert "grant" not in inspect.signature(_derive_general_from_lock).parameters


def test_forged_validated_result_without_installed_grant_is_rejected(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    del metric_set, qualification, pin
    result = _evaluate_general_detectors(_locked_candidate_case(manifest, binding)).results[0]
    forged = copy.deepcopy(result)
    forged["state"] = "finding_candidate"
    forged["detector_maturity"] = "validated"
    forged["extensions"]["x-production-finding-permitted"] = True
    forged["extensions"]["x-evaluation-only"] = False

    with pytest.raises(ReportContractError, match="installed exact grant"):
        _validate_detector_projection(
            {
                "detector_manifests": [manifest],
                "detector_results": [forged],
                "findings": [],
            }
        )


def test_mutated_qualification_digest_pin_cannot_resolve(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=replace(pin, qualification_digest="sha256:" + "0" * 64),
        )
        is None
    )


def test_mutated_metric_set_digest_pin_cannot_resolve(project_root: Path, candidate: Path) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=replace(pin, metric_set_digest="sha256:" + "0" * 64),
        )
        is None
    )


def test_mutated_threshold_policy_digest_pin_cannot_resolve(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=replace(pin, threshold_policy_digest="sha256:" + "0" * 64),
        )
        is None
    )


def test_mutated_live_adapter_identity_pin_cannot_resolve(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    adapter = replace(pin.exam_adapter_identity[0], implementation_digest="sha256:" + "0" * 64)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=replace(pin, exam_adapter_identity=(adapter, *pin.exam_adapter_identity[1:])),
        )
        is None
    )


def test_mutated_binding_digest_pin_cannot_resolve(project_root: Path, candidate: Path) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=replace(pin, binding_digest="sha256:" + "0" * 64),
        )
        is None
    )


def test_failed_safety_gate_cannot_resolve_even_with_original_pin(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    qualification["safety_gates"]["no_known_high_or_critical_false_accusations"] = False
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is None
    )


def test_missed_roots_above_pin_cannot_resolve_with_rebound_metric_digest(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    metric_set["counts"]["missed_roots"] = 1
    pin = replace(pin, metric_set_digest=semantic_digest(metric_set))
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is None
    )


def test_adjudicated_roots_must_equal_pin_with_rebound_metric_digest(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    metric_set["counts"]["adjudicated_roots"] = 3
    pin = replace(pin, metric_set_digest=semantic_digest(metric_set))
    assert (
        resolve_method_conflict_qualification(
            binding=binding,
            detector_manifest=manifest,
            qualification=qualification,
            metric_set=metric_set,
            pin=pin,
        )
        is None
    )


def test_mutated_work_packet_cannot_project_a_resolved_grant(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=manifest,
        qualification=qualification,
        metric_set=metric_set,
        pin=pin,
    )
    assert grant is not None
    evaluation = evaluate_registered_method_conflicts(_locked_candidate_case(manifest, binding))[0]
    packet = copy.deepcopy(evaluation.work_packet)
    packet["target_question"]["status"] = "open"

    assert (
        project_qualified_method_conflict_candidate(
            evaluation.result,
            evaluation.binding,
            grant,
            work_packet=packet,
        )
        is None
    )


def test_mutated_grant_binding_cannot_project_a_candidate(
    project_root: Path, candidate: Path
) -> None:
    binding, manifest, metric_set, qualification, pin = _resolver_arguments(project_root, candidate)
    grant = resolve_method_conflict_qualification(
        binding=binding,
        detector_manifest=manifest,
        qualification=qualification,
        metric_set=metric_set,
        pin=pin,
    )
    assert grant is not None
    evaluation = evaluate_registered_method_conflicts(_locked_candidate_case(manifest, binding))[0]

    assert (
        project_qualified_method_conflict_candidate(
            evaluation.result,
            evaluation.binding,
            replace(grant, binding_id="binding:forged"),
            work_packet=evaluation.work_packet,
        )
        is None
    )


def test_detector_results_without_findings_raise_contract_violation(
    schema_root: Path, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="detector results and findings must be supplied together"):
        _derive_general_from_lock(
            {},
            tmp_path / "must-not-be-created",
            schema_root,
            detector_results=[],
        )
    assert not (tmp_path / "must-not-be-created").exists()
