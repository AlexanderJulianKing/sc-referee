"""One development-only Slice-B verification/composition/render transaction."""

from __future__ import annotations

from collections.abc import Callable
from typing import Final, cast

from sc_referee.controller import ManifestBoundFrozenInspectionContext
from sc_referee_evaluation.audit_ladder.slice_b.composition import (
    SliceBCompositionResultV1,
    compose_slice_b_question_v1,
)
from sc_referee_evaluation.audit_ladder.slice_b.primary import (
    CsvQuestionRequestV1,
    SliceBContractError,
    SliceBPrimaryObservationResult,
    canonical_observation_bytes,
    verify_csv_comparison_group_sizes_v1,
    verify_csv_selected_cardinalities_v1,
    verify_csv_table_shape_v1,
    verify_csv_unit_comparison_incidence_v1,
)
from sc_referee_evaluation.audit_ladder.slice_b.renderer import (
    PRIMARY_REFUSAL_PRECEDENCE,
    CsvComparisonGroupSizesObservationV1,
    CsvSelectedCardinalitiesObservationV1,
    CsvTableShapeObservationV1,
    CsvUnitComparisonIncidenceObservationV1,
    SliceBObservationSetV1,
    SliceBPrimaryRefusalReasonV1,
    render_slice_b_component_v1,
)

_PrimaryVerifier = Callable[
    [ManifestBoundFrozenInspectionContext, CsvQuestionRequestV1],
    SliceBPrimaryObservationResult,
]
_ORDERED_PRIMARY_VERIFIERS: Final[tuple[_PrimaryVerifier, ...]] = (
    verify_csv_table_shape_v1,
    verify_csv_selected_cardinalities_v1,
    verify_csv_comparison_group_sizes_v1,
    verify_csv_unit_comparison_incidence_v1,
)
_ORDERED_OBSERVATION_TYPES: Final[tuple[type[object], ...]] = (
    CsvTableShapeObservationV1,
    CsvSelectedCardinalitiesObservationV1,
    CsvComparisonGroupSizesObservationV1,
    CsvUnitComparisonIncidenceObservationV1,
)


def render_slice_b_report_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
) -> bytes:
    """Verify frozen CSV bytes, independently compose, and render one report.

    The transaction accepts no observation, question, answer, template, parser,
    callback, or cached fact.  Each primary verifier starts again from the frozen
    context; composition then performs its separate manifest/byte/table replay.
    """

    results = tuple(verifier(context, request) for verifier in _ORDERED_PRIMARY_VERIFIERS)
    if any(type(result) is not SliceBPrimaryObservationResult for result in results):
        return _render_primary_refusal(
            context,
            SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH,
        )

    refusals = {result.refusal for result in results if result.refusal is not None}
    first_refusal = next(
        (reason for reason in PRIMARY_REFUSAL_PRECEDENCE if reason in refusals), None
    )
    if first_refusal is not None:
        return _render_primary_refusal(context, first_refusal)

    primary_values = tuple(result.observation for result in results)
    if len(primary_values) != 4 or any(
        type(observation) is not expected_type
        for observation, expected_type in zip(
            primary_values,
            _ORDERED_OBSERVATION_TYPES,
            strict=True,
        )
    ):
        return _render_primary_refusal(
            context,
            SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH,
        )
    try:
        for observation in primary_values:
            canonical_observation_bytes(observation)  # type: ignore[arg-type]
    except SliceBContractError:
        return _render_primary_refusal(
            context,
            SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH,
        )
    primary_observations = cast(SliceBObservationSetV1, primary_values)

    composed = compose_slice_b_question_v1(
        context=context,
        selected_path=request.selected_path,
        candidate_unit_column_index=request.candidate_unit_column_index,
        comparison_column_index=request.comparison_column_index,
        primary_observations=primary_observations,
    )
    if type(composed) is not SliceBCompositionResultV1:
        return _render_primary_refusal(
            context,
            SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH,
        )
    return render_slice_b_component_v1(
        snapshot_digest=context.snapshot_digest,
        primary_refusal=composed.primary_refusal,
        observations=composed.observations,
        question=composed.question,
        question_scope_unresolved=composed.question_scope_unresolved,
    )


def _render_primary_refusal(
    context: ManifestBoundFrozenInspectionContext,
    refusal: SliceBPrimaryRefusalReasonV1,
) -> bytes:
    return render_slice_b_component_v1(
        snapshot_digest=context.snapshot_digest,
        primary_refusal=refusal,
        observations=None,
        question=None,
        question_scope_unresolved=False,
    )
