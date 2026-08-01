from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest
from sc_referee.qualification_metrics import (
    METRIC_NAMES,
    QualificationMetricInvariantError,
    bootstrap_cluster_index,
    bootstrap_problem_sample,
    compile_qualification_evidence,
)
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION

QualificationMetricError = QualificationMetricInvariantError


def build_qualification_metric_set(
    case_outcomes: list[dict[str, Any]],
    benchmark_fixtures: list[dict[str, Any]],
    qualification_envelope: dict[str, Any],
    schema_root: Path,
    *,
    generated_at: str,
    output: Path | None = None,
    expected_metric_set: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile accepted metrics after independently resolving exact fixture inputs."""

    if output is not None and (output.exists() or output.is_symlink()):
        raise QualificationMetricError(f"QualificationMetricSet output already exists: {output}")
    registry = LocalSchemaRegistry(schema_root)
    outcomes = sorted(deepcopy(case_outcomes), key=lambda value: str(value.get("case_outcome_id")))
    for outcome in outcomes:
        try:
            registry.validate(outcome)
        except RecordValidationError as error:
            raise QualificationMetricError(str(error)) from error
    _validate_fixture_inputs(outcomes, benchmark_fixtures, registry)

    evidence = compile_qualification_evidence(outcomes, qualification_envelope)
    metric_set: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "qualification_metric_set",
        **evidence,
        "metric_profile": "root-cause-clustered-metrics-v1",
        "numeric_threshold_policy": "deferred_until_pilot_threshold_adr",
        "promotion_permitted": False,
        "generated_at": generated_at,
        "non_inferences": [
            "Qualification metrics do not qualify or promote the detector while numeric thresholds are deferred.",
            "A point estimate or zero observed false positives is not a correctness certificate.",
        ],
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_clustered_metric_calculation",
            "created_at": generated_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
    }
    try:
        registry.validate(metric_set)
    except RecordValidationError as error:  # pragma: no cover - construction invariant
        raise QualificationMetricError(str(error)) from error
    if expected_metric_set is not None and metric_set != expected_metric_set:
        raise QualificationMetricError("Model-free metric replay does not equal the source set.")
    if output is not None:
        write_normalized_json_once(output, metric_set)
    return metric_set


def _validate_fixture_inputs(
    outcomes: list[dict[str, Any]],
    fixtures: list[dict[str, Any]],
    registry: LocalSchemaRegistry,
) -> None:
    if not fixtures:
        raise QualificationMetricError(
            "Metric compilation requires the exact BenchmarkFixture for every case outcome."
        )
    by_id: dict[str, dict[str, Any]] = {}
    for fixture in fixtures:
        try:
            registry.validate(fixture)
        except RecordValidationError as error:
            raise QualificationMetricError(str(error)) from error
        fixture_id = str(fixture["fixture_id"])
        if fixture_id in by_id:
            raise QualificationMetricError(f"Duplicate BenchmarkFixture {fixture_id!r}.")
        by_id[fixture_id] = fixture
    referenced: set[str] = set()
    for outcome in outcomes:
        fixture_ref = outcome.get("fixture_ref")
        if (
            not isinstance(fixture_ref, dict)
            or fixture_ref.get("record_type") != "benchmark_fixture"
        ):
            raise QualificationMetricError("Case outcome fixture_ref is malformed.")
        fixture_id = str(fixture_ref.get("record_id", ""))
        resolved_fixture = by_id.get(fixture_id)
        if resolved_fixture is None:
            raise QualificationMetricError(
                f"Case outcome has no exact BenchmarkFixture {fixture_id!r}."
            )
        referenced.add(fixture_id)
        status = resolved_fixture.get("qualification_proof_status")
        if (
            outcome.get("fixture_semantic_digest") != semantic_digest(resolved_fixture)
            or outcome.get("qualification_proof_status") != status
            or outcome.get("problem_id") != resolved_fixture.get("problem_id")
            or outcome.get("corpus_partition") != resolved_fixture.get("corpus_partition")
            or outcome.get("fixture_kind") != resolved_fixture.get("fixture_kind")
        ):
            raise QualificationMetricError(
                "Case outcome does not equal its exact fixture digest, status, and scope projection."
            )
        fixture_proof_inputs = resolved_fixture.get("proof_evidence")
        fixture_public_inputs = (
            fixture_proof_inputs.get("public_inputs")
            if isinstance(fixture_proof_inputs, dict)
            else None
        )
        static_proofs = (
            fixture_public_inputs.get("static_qualification_proofs")
            if isinstance(fixture_public_inputs, dict)
            else []
        )
        expected_static_ref = (
            static_proofs[0].get("record_ref")
            if isinstance(static_proofs, list)
            and len(static_proofs) == 1
            and isinstance(static_proofs[0], dict)
            else None
        )
        if outcome.get("static_qualification_proof_ref") != expected_static_ref:
            raise QualificationMetricError(
                "Case outcome static proof does not equal its exact fixture proof input."
            )
        is_complete = status == "complete"
        if is_complete != (outcome.get("metric_input_status") == "complete"):
            raise QualificationMetricError(
                "Case outcome metric-input status conflicts with fixture proof completeness."
            )
        if not is_complete and (
            outcome.get("metric_eligible") is not False
            or outcome.get("promotion_evidence_eligible") is not False
        ):
            raise QualificationMetricError(
                "An incomplete fixture cannot enter authoritative or promotion metrics."
            )
        if (
            resolved_fixture.get("corpus_partition") == "public_development"
            and outcome.get("promotion_evidence_eligible") is not False
        ):
            raise QualificationMetricError(
                "A public-development fixture cannot become promotion evidence."
            )
    if referenced != set(by_id):
        raise QualificationMetricError(
            "Supplied BenchmarkFixtures do not exactly equal metric case dependencies."
        )


__all__ = [
    "METRIC_NAMES",
    "QualificationMetricError",
    "bootstrap_cluster_index",
    "bootstrap_problem_sample",
    "build_qualification_metric_set",
]
