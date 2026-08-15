"""Closed development-only v2 dependence authority lock.

This distinct lock line can authorize only the unregistered v2 shadow.  It is
never accepted by the v1 loader or the production controller entry point.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.dependence_recognition.authority_lock import (
    DECLARED_EXECUTION_ROOT,
    bind_dependence_selected_writer_scope,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    RecordRef,
)

LOCK_KIND = "dependence_method_authorization_v2_development"
LOCK_LINE = "dependence_semantic_v2_growth_2"
V2_PROCEDURES = frozenset(
    {
        "scipy.stats.binomtest",
        "scipy.stats.fisher_exact",
        "scipy.stats.mannwhitneyu",
        "scipy.stats.ttest_ind",
    }
)
V2_PROCEDURE_VARIANTS = frozenset({"scipy.stats.ttest_ind:welch"})
V2_GROUP_PROCEDURES = frozenset(
    {"scipy.stats.ttest_ind", "scipy.stats.ttest_ind:welch", "scipy.stats.mannwhitneyu"}
)
AUTHORITY_LIMITATIONS = (
    "This lock is development-shadow-only and cannot authorize v1 or production output.",
    "Authorization is limited to this case, snapshot, input digest, procedure and unit key.",
    "It establishes no execution, numerical impact or general scientific correctness.",
)
_ROOT_KEYS = frozenset(
    {
        "lock_kind",
        "lock_line",
        "case_id",
        "snapshot_digest",
        "intake_recorded_at",
        "declared_execution_root",
        "records",
        "approval",
        "authority_limitations",
        "lock_digest",
    }
)
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")


class DependenceV2AuthorizationLockError(ValueError):
    """Raised when a v2 development lock fails closed."""


@dataclass(frozen=True)
class VerifiedDependenceV2AuthorizationLock:
    case_id: str
    snapshot_digest: str
    records: tuple[dict[str, Any], ...]
    lock_digest: str
    approved_projection_digest: str
    canonical_payload: bytes


def approval_projection(lock: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact human-approved v2 projection."""

    return {
        key: lock.get(key)
        for key in (
            "lock_kind",
            "lock_line",
            "case_id",
            "snapshot_digest",
            "intake_recorded_at",
            "declared_execution_root",
            "records",
            "authority_limitations",
        )
    }


def lock_projection(lock: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in lock.items() if key != "lock_digest"}


def build_dependence_v2_authorization_lock(
    *,
    case_id: str,
    snapshot_digest: str,
    intake_recorded_at: str,
    procedure: str | tuple[str, ...],
    unit_column: str,
    input_path: str,
    input_content_digest: str,
) -> dict[str, Any]:
    """Build the sole closed v2 lock shape from controller-frozen declarations."""

    procedures = (procedure,) if isinstance(procedure, str) else procedure
    if (
        not procedures
        or any(item not in V2_PROCEDURES | V2_PROCEDURE_VARIANTS for item in procedures)
        or len(procedures) != len(set(procedures))
        or (len(procedures) > 1 and any(item not in V2_GROUP_PROCEDURES for item in procedures))
    ):
        raise DependenceV2AuthorizationLockError("v2 procedure is outside the closed registry")
    slug = case_id.removeprefix("case:")
    actor_id = f"scientist:dependence-free-author-{slug}"
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "lock_line": LOCK_LINE,
        "case_id": case_id,
        "snapshot_digest": snapshot_digest,
        "intake_recorded_at": intake_recorded_at,
        "declared_execution_root": DECLARED_EXECUTION_ROOT,
        "records": [
            {
                "record_type": "analysis",
                "record_id": f"analysis-v2:{slug}",
                "path": "workflow/analysis.py",
            },
            (
                {
                    "record_type": "procedure",
                    "record_id": f"procedure-v2:{slug}",
                    "resolved_callable": procedures[0],
                }
                if len(procedures) == 1
                else {
                    "record_type": "procedure",
                    "record_id": f"procedure-v2:{slug}",
                    "resolved_callables": list(procedures),
                }
            ),
            {
                "record_type": "result",
                "record_id": f"result-v2:{slug}",
                "path": "results/report.md",
            },
            {
                "record_type": "human_method_authorization",
                "record_id": f"authorization-v2:{slug}",
                "actor_id": actor_id,
                "authority_state": "authorized",
                "analysis_target_ref": {
                    "record_type": "analysis",
                    "record_id": f"analysis-v2:{slug}",
                },
                "procedure_ref": {
                    "record_type": "procedure",
                    "record_id": f"procedure-v2:{slug}",
                },
                "independent_unit_definition_id": stable_id(
                    "unit-definition-v2", case_id, unit_column
                ),
                "authorized_key_columns": [unit_column],
                "input_path": input_path,
                "input_content_digest": input_content_digest,
            },
        ],
        "approval": {
            "actor_kind": "human",
            "actor_id": actor_id,
            "approved_projection_digest": "sha256:" + "0" * 64,
            "approved_at": intake_recorded_at,
        },
        "authority_limitations": list(AUTHORITY_LIMITATIONS),
        "lock_digest": "sha256:" + "0" * 64,
    }
    value["approval"]["approved_projection_digest"] = semantic_digest(approval_projection(value))
    value["lock_digest"] = semantic_digest(lock_projection(value))
    return value


def verify_dependence_v2_authorization_lock(
    lock_path: Path,
    *,
    expected_case_id: str,
    expected_snapshot_digest: str,
    expected_intake_recorded_at: str,
    material_input_digests: Mapping[str, str],
    frozen_input_headers: Mapping[str, tuple[str, ...]],
    forbidden_role_markers: Iterable[str] = (),
) -> VerifiedDependenceV2AuthorizationLock:
    """Validate the exact v2 schema and all frozen case bindings."""

    try:
        payload = lock_path.read_bytes()
        value = json.loads(payload.decode("utf-8", errors="strict"), object_pairs_hook=_closed)
    except Exception as error:
        raise DependenceV2AuthorizationLockError("v2 lock is not strict JSON") from error
    if not isinstance(value, dict) or frozenset(value) != _ROOT_KEYS:
        raise DependenceV2AuthorizationLockError("v2 lock root is not closed")
    if value.get("lock_kind") != LOCK_KIND or value.get("lock_line") != LOCK_LINE:
        raise DependenceV2AuthorizationLockError("v2 lock discriminator is invalid")
    if value.get("case_id") != expected_case_id:
        raise DependenceV2AuthorizationLockError("v2 lock names another case")
    if value.get("snapshot_digest") != expected_snapshot_digest:
        raise DependenceV2AuthorizationLockError("v2 lock names another snapshot")
    if value.get("intake_recorded_at") != expected_intake_recorded_at:
        raise DependenceV2AuthorizationLockError("v2 lock names another intake freeze")
    if value.get("declared_execution_root") != DECLARED_EXECUTION_ROOT:
        raise DependenceV2AuthorizationLockError("v2 execution root is not closed")
    records = value.get("records")
    if not isinstance(records, list) or [
        item.get("record_type") if isinstance(item, dict) else None for item in records
    ] != ["analysis", "procedure", "result", "human_method_authorization"]:
        raise DependenceV2AuthorizationLockError("v2 lock record set is not closed")
    analysis, procedure, result, authority = records
    if analysis != {
        "record_type": "analysis",
        "record_id": analysis.get("record_id"),
        "path": "workflow/analysis.py",
    }:
        raise DependenceV2AuthorizationLockError("v2 analysis record is invalid")
    if result != {
        "record_type": "result",
        "record_id": result.get("record_id"),
        "path": "results/report.md",
    }:
        raise DependenceV2AuthorizationLockError("v2 result record is invalid")
    singular = (
        frozenset(procedure) == {"record_type", "record_id", "resolved_callable"}
        and procedure.get("resolved_callable") in V2_PROCEDURES | V2_PROCEDURE_VARIANTS
    )
    plural = procedure.get("resolved_callables")
    set_form = (
        frozenset(procedure) == {"record_type", "record_id", "resolved_callables"}
        and isinstance(plural, list)
        and len(plural) > 1
        and len(plural) == len(set(plural))
        and all(item in V2_GROUP_PROCEDURES for item in plural)
    )
    if procedure.get("record_type") != "procedure" or not (singular or set_form):
        raise DependenceV2AuthorizationLockError("v2 procedure record is invalid")
    if frozenset(authority) != {
        "record_type",
        "record_id",
        "actor_id",
        "authority_state",
        "analysis_target_ref",
        "procedure_ref",
        "independent_unit_definition_id",
        "authorized_key_columns",
        "input_path",
        "input_content_digest",
    }:
        raise DependenceV2AuthorizationLockError("v2 authority record is not closed")
    if (
        authority.get("record_type") != "human_method_authorization"
        or authority.get("authority_state") != "authorized"
        or authority.get("analysis_target_ref")
        != {"record_type": "analysis", "record_id": analysis.get("record_id")}
        or authority.get("procedure_ref")
        != {"record_type": "procedure", "record_id": procedure.get("record_id")}
    ):
        raise DependenceV2AuthorizationLockError("v2 authority references are invalid")
    key_columns = authority.get("authorized_key_columns")
    input_path = authority.get("input_path")
    if (
        not isinstance(key_columns, list)
        or len(key_columns) != 1
        or not isinstance(key_columns[0], str)
        or not isinstance(input_path, str)
        or authority.get("input_content_digest") != material_input_digests.get(input_path)
        or key_columns[0] not in frozen_input_headers.get(input_path, ())
    ):
        raise DependenceV2AuthorizationLockError("v2 material/key binding is invalid")
    markers = tuple(str(item).casefold() for item in forbidden_role_markers)
    if any(marker and marker in canonical_json(value).casefold() for marker in markers):
        raise DependenceV2AuthorizationLockError("v2 lock leaks a case role")
    approval = value.get("approval")
    if not isinstance(approval, dict) or frozenset(approval) != {
        "actor_kind",
        "actor_id",
        "approved_projection_digest",
        "approved_at",
    }:
        raise DependenceV2AuthorizationLockError("v2 approval is not closed")
    expected_approval = semantic_digest(approval_projection(value))
    expected_lock = semantic_digest(lock_projection(value))
    if (
        approval.get("actor_kind") != "human"
        or approval.get("actor_id") != authority.get("actor_id")
        or approval.get("approved_projection_digest") != expected_approval
        or value.get("authority_limitations") != list(AUTHORITY_LIMITATIONS)
        or value.get("lock_digest") != expected_lock
        or _SHA256.fullmatch(expected_lock) is None
    ):
        raise DependenceV2AuthorizationLockError("v2 approval or digest does not replay")
    return VerifiedDependenceV2AuthorizationLock(
        case_id=expected_case_id,
        snapshot_digest=expected_snapshot_digest,
        records=tuple(dict(item) for item in records),
        lock_digest=expected_lock,
        approved_projection_digest=expected_approval,
        canonical_payload=(canonical_json(value) + "\n").encode("utf-8"),
    )


def apply_dependence_v2_authorization_lock(
    context: FrozenInspectionContext,
    lock_path: Path,
    *,
    expected_case_id: str,
    expected_intake_recorded_at: str,
) -> FrozenInspectionContext:
    """Append one verified v2 record set to the observer's frozen context."""

    headers: dict[str, tuple[str, ...]] = {}
    for material in context.material_inputs:
        try:
            header = next(
                csv.reader(material.content.decode("utf-8", errors="strict").splitlines())
            )
        except (UnicodeError, StopIteration, csv.Error):
            continue
        headers[material.path] = tuple(header)
    verified = verify_dependence_v2_authorization_lock(
        lock_path,
        expected_case_id=expected_case_id,
        expected_snapshot_digest=context.snapshot_digest,
        expected_intake_recorded_at=expected_intake_recorded_at,
        material_input_digests={item.path: item.content_digest for item in context.material_inputs},
        frozen_input_headers=headers,
    )
    existing = {item.ref for item in context.base_records}
    additions: list[FrozenBaseRecord] = []
    for record in verified.records:
        ref = RecordRef(str(record["record_type"]), str(record["record_id"]))
        if ref in existing or any(item.ref == ref for item in additions):
            raise DependenceV2AuthorizationLockError("v2 record reference collides")
        additions.append(FrozenBaseRecord.from_record(ref, record))
    updated = replace(
        context,
        base_records=tuple(sorted((*context.base_records, *additions), key=lambda item: item.ref)),
    )
    return bind_dependence_selected_writer_scope(
        updated, declared_execution_root=DECLARED_EXECUTION_ROOT
    )


def _closed(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DependenceV2AuthorizationLockError("v2 lock has duplicate keys")
        result[key] = value
    return result
