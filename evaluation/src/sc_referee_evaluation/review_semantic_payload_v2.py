from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from sc_referee_evaluation.review_semantic_payload import (
    build_stage1_batch_output_schema,
    project_stage1_semantic_batch,
)


def build_stage1_batch_output_schema_v2(
    participant_id: str,
    case_ids: Sequence[str],
    canonical_issue_class: str,
) -> dict[str, Any]:
    """Add verdict/question consistency without changing the public AgentReview schema."""

    schema = deepcopy(
        build_stage1_batch_output_schema(participant_id, case_ids, canonical_issue_class)
    )
    review_schema = schema["properties"]["reviews"]["items"]
    review_schema["allOf"].append(
        {
            "if": {
                "properties": {
                    "verdict": {
                        "enum": [
                            "demonstrated_issue",
                            "no_demonstrated_issue_within_scope",
                        ]
                    }
                },
                "required": ["verdict"],
            },
            "then": {"properties": {"unresolved_material_questions": {"maxItems": 0}}},
        }
    )
    return schema


def project_stage1_semantic_batch_v2(
    payload: Mapping[str, Any],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Project a v2 semantic response through the unchanged fail-closed v1 compiler."""

    return project_stage1_semantic_batch(payload, **kwargs)
