from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.agent_protocol import load_audit_status
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.layout import AuditLayout
from sc_referee_evaluation.genebench_workspace import (
    GeneBenchWorkspaceError,
    verify_genebench_public_preflight,
)
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)


class GeneBenchNumericGradeError(ValueError):
    """A public GeneBench answer grade violates the closed experimental profile."""


_GRADE_VERSION = "0.4.0"
_SINGLE_NUMERIC_COMPARISON_PROFILE = "genebench_single_numeric_absolute_tolerance_v1"
_NUMERIC_COMPARISON_PROFILE = "genebench_multi_numeric_absolute_tolerance_v3"
_COMPOSITE_COMPARISON_PROFILE = "genebench_composite_exact_string_numeric_absolute_tolerance_v1"
_INTEGER_COMPOSITE_COMPARISON_PROFILE = (
    "genebench_composite_integer_exact_numeric_absolute_tolerance_v1"
)
_ANSWER_PATH = "answer.json"
_MAX_JSON_BYTES = 1_048_576


def grade_genebench_public_numeric_answer(
    package_root: Path,
    preflight: dict[str, Any],
    eval_id: str,
    audit_root: Path,
    schema_root: Path,
    *,
    graded_at: str,
    output: Path,
) -> dict[str, Any]:
    """Compare a frozen answer with one exact public absolute-tolerance contract."""

    return _grade_genebench_public_answer(
        package_root,
        preflight,
        eval_id,
        audit_root,
        schema_root,
        graded_at=graded_at,
        output=output,
        allow_composite=False,
        generic_record=False,
    )


def grade_genebench_public_answer(
    package_root: Path,
    preflight: dict[str, Any],
    eval_id: str,
    audit_root: Path,
    schema_root: Path,
    *,
    graded_at: str,
    output: Path,
) -> dict[str, Any]:
    """Compare a frozen answer under one closed numeric or mixed GeneBench contract."""

    return _grade_genebench_public_answer(
        package_root,
        preflight,
        eval_id,
        audit_root,
        schema_root,
        graded_at=graded_at,
        output=output,
        allow_composite=True,
        generic_record=True,
    )


def _grade_genebench_public_answer(
    package_root: Path,
    preflight: dict[str, Any],
    eval_id: str,
    audit_root: Path,
    schema_root: Path,
    *,
    graded_at: str,
    output: Path,
    allow_composite: bool,
    generic_record: bool,
) -> dict[str, Any]:
    """Execute the shared, non-executing answer-grade boundary."""

    if output.exists() or output.is_symlink():
        raise GeneBenchNumericGradeError(f"GeneBench grade output already exists: {output}")
    try:
        verified = verify_genebench_public_preflight(package_root.resolve(), preflight)
        status = load_audit_status(audit_root, schema_root)
    except (GeneBenchWorkspaceError, OSError, ValueError) as error:
        raise GeneBenchNumericGradeError(str(error)) from error
    if not status.terminal:
        raise GeneBenchNumericGradeError("GeneBench grading requires a terminal audit.")
    if status.model_access_after_lock is not False:
        raise GeneBenchNumericGradeError(
            "GeneBench grading requires verified absence of post-lock model access."
        )

    layout = AuditLayout(audit_root.resolve())
    bundle = _read_object(layout.bundle_path, "audit bundle")
    locked = _read_object(layout.lock_path, "semantic lock")
    locked_at = str(locked.get("locked_at", ""))
    if _timestamp(graded_at) < _timestamp(locked_at):
        raise GeneBenchNumericGradeError("GeneBench grading cannot precede semantic lock.")
    snapshot, file_records, asset_identities = _locked_snapshot_records(bundle, locked)
    snapshot_identity_ids = {
        str(record.get("asset_identity_ref", {}).get("record_id", "")) for record in file_records
    }
    snapshot_asset_identities = [
        record
        for record in asset_identities
        if record.get("asset_identity_id") in snapshot_identity_ids
    ]
    try:
        snapshot_index = validate_content_addressed_snapshot(
            snapshot, file_records, snapshot_asset_identities
        )
        file_record, identity, answer_payload, answer_digest = read_full_digest_snapshot_file(
            snapshot_index,
            layout.observed / "snapshot" / "materialized",
            _ANSWER_PATH,
        )
    except (KeyError, SnapshotEvidenceError) as error:
        raise GeneBenchNumericGradeError(str(error)) from error

    problem, config = _verified_case_config(package_root.resolve(), verified, eval_id)
    ground_truth, field_specs, comparison_profile, grader_contract_digest = _answer_contract(
        config,
        problem,
        allow_composite=allow_composite,
    )
    answer = _answer_values(answer_payload, sorted(ground_truth))

    comparisons: list[dict[str, Any]] = []
    for key in sorted(ground_truth):
        spec = field_specs[key]
        comparison_kind = spec["comparison_kind"]
        if comparison_kind == "numeric_absolute_tolerance":
            comparisons.append(_numeric_comparison(key, answer[key], ground_truth[key], spec))
        elif comparison_kind == "integer_exact":
            comparisons.append(_integer_comparison(key, answer[key], ground_truth[key], spec))
        elif comparison_kind == "exact_string":
            comparisons.append(_exact_string_comparison(key, answer[key], ground_truth[key]))
        else:  # pragma: no cover - field specs are closed above
            raise GeneBenchNumericGradeError(
                f"Unsupported comparison kind {comparison_kind!r} for {key!r}."
            )

    all_fields_match = all(item["matches_contract"] for item in comparisons)
    record_type = (
        "evaluation_genebench_answer_grade"
        if generic_record
        else "evaluation_genebench_multi_numeric_grade"
    )
    grade_id_prefix = (
        "genebench-answer-grade" if generic_record else "genebench-multi-numeric-grade"
    )
    grade: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        (
            "genebench_answer_grade_version"
            if generic_record
            else "genebench_numeric_grade_version"
        ): _GRADE_VERSION,
        "record_type": record_type,
        "grade_id": stable_id(
            grade_id_prefix,
            _GRADE_VERSION,
            comparison_profile,
            str(verified["preflight_id"]),
            eval_id,
            str(locked["semantic_lock_digest"]),
            answer_digest,
            grader_contract_digest,
        ),
        "graded_at": graded_at,
        "source": {
            "uri": verified["source"]["uri"],
            "revision": verified["source"]["revision"],
            "preflight_id": verified["preflight_id"],
            "preflight_digest": verified["preflight_digest"],
        },
        "case": {
            "eval_id": eval_id,
            "eval_uuid": problem["eval_uuid"],
            "corpus_partition": "public_development",
        },
        "audit": {
            "audit_run_id": status.audit_run_id,
            "run_state": status.run_state,
            "semantic_lock_digest": status.semantic_lock_digest,
            "locked_at": locked_at,
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
            "snapshot_digest": snapshot["snapshot_digest"],
            "model_access_after_lock": False,
        },
        "answer": {
            "path": _ANSWER_PATH,
            "json_pointer": "/answer",
            "content_digest": answer_digest,
            "file_record_ref": {
                "record_type": "file_record",
                "record_id": file_record["file_record_id"],
            },
            "asset_identity_ref": {
                "record_type": "asset_identity",
                "record_id": identity["asset_identity_id"],
            },
        },
        "grader_contract": {
            "comparison_profile": comparison_profile,
            "contract_digest": grader_contract_digest,
            "config_content_digest": problem["eval_config"]["content_digest"],
            "ground_truth_value_disclosed": False,
            "reference_grader_executed": False,
        },
        "comparisons": comparisons,
        "grade_status": (
            "within_contract"
            if generic_record and all_fields_match
            else "outside_contract"
            if generic_record
            else "within_tolerance"
            if all_fields_match
            else "outside_tolerance"
        ),
        ("all_fields_match" if generic_record else "all_within_tolerance"): all_fields_match,
        "metric_eligible": False,
        "held_out_eligible": False,
        "promotion_evidence_eligible": False,
        "project_code_executed_by_grader": False,
        "model_invoked_by_grader": False,
        "non_inferences": [
            "An answer-grade mismatch is not itself a demonstrated scientific issue or Finding.",
            "This grade does not establish the method, premise, implementation step, or scientific interpretation that caused a mismatch.",
            "A public-development case cannot establish independent qualification or detector promotion.",
        ],
    }
    grade["grade_digest"] = semantic_digest(grade)
    write_normalized_json_once(output, grade)
    return grade


def _locked_snapshot_records(
    bundle: dict[str, Any], locked: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    snapshot = locked.get("repository_snapshot")
    file_records = locked.get("file_records")
    asset_identities = locked.get("asset_identities")
    if (
        not isinstance(snapshot, dict)
        or not isinstance(file_records, list)
        or not all(isinstance(item, dict) for item in file_records)
        or not isinstance(asset_identities, list)
        or not all(isinstance(item, dict) for item in asset_identities)
    ):
        raise GeneBenchNumericGradeError("Semantic lock lacks exact snapshot evidence records.")
    if (
        bundle.get("repository_snapshots") != [snapshot]
        or bundle.get("file_records") != file_records
        or bundle.get("asset_identities") != asset_identities
    ):
        raise GeneBenchNumericGradeError(
            "Audit bundle snapshot evidence differs from the semantic lock."
        )
    return snapshot, file_records, asset_identities


def _verified_case_config(
    package_root: Path, preflight: dict[str, Any], eval_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    matches = [item for item in preflight.get("problems", []) if item.get("eval_id") == eval_id]
    if len(matches) != 1:
        raise GeneBenchNumericGradeError(f"Unknown or ambiguous GeneBench eval_id {eval_id!r}.")
    problem = dict(matches[0])
    config_record = problem.get("eval_config")
    if not isinstance(config_record, dict):
        raise GeneBenchNumericGradeError("Verified case has no exact config identity.")
    path_value = str(config_record.get("path", ""))
    payload = _read_package_file(package_root, path_value)
    if sha256_digest(payload) != config_record.get("content_digest"):
        raise GeneBenchNumericGradeError("GeneBench case config changed after preflight.")
    config = _load_json_object(payload, path_value, max_bytes=_MAX_JSON_BYTES)
    if semantic_digest(config) != config_record.get("semantic_digest"):
        raise GeneBenchNumericGradeError("GeneBench case config semantics changed after preflight.")
    return problem, config


def _answer_contract(
    config: dict[str, Any],
    problem: dict[str, Any],
    *,
    allow_composite: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str, str]:
    ground_truth = config.get("ground_truth")
    grader = config.get("grader")
    if not isinstance(ground_truth, dict) or not isinstance(grader, dict):
        raise GeneBenchNumericGradeError("GeneBench answer contract is malformed.")
    grader_config = grader.get("config")
    if set(grader) != {"type", "config"} or not isinstance(grader_config, dict):
        raise GeneBenchNumericGradeError(
            "GeneBench grader metadata is outside the closed answer-grade profiles."
        )
    answer_fields = problem.get("answer_fields")
    if not isinstance(answer_fields, list) or set(ground_truth) != set(answer_fields):
        raise GeneBenchNumericGradeError(
            "GeneBench ground truth, manifest fields, and grader keys do not match exactly."
        )
    grader_type = grader.get("type")
    if grader_type == "numeric_tolerance":
        fields = _single_numeric_field_specs(ground_truth, grader_config)
        comparison_profile = _SINGLE_NUMERIC_COMPARISON_PROFILE
    elif grader_type == "multi_numeric_tolerance":
        if set(grader_config) != {"keys"} or not isinstance(grader_config.get("keys"), dict):
            raise GeneBenchNumericGradeError(
                "Only the closed multi_numeric_tolerance absolute-tolerance profile is supported."
            )
        fields = _numeric_field_specs(
            ground_truth,
            grader_config["keys"],
            require_required_flag=False,
            allow_minimum_only=True,
        )
        comparison_profile = _NUMERIC_COMPARISON_PROFILE
    elif grader_type == "composite" and allow_composite:
        fields, comparison_profile = _composite_field_specs(ground_truth, grader_config)
    else:
        raise GeneBenchNumericGradeError(
            "Only the closed numeric profile and explicitly enabled mixed exact-string/numeric "
            "profile are supported."
        )
    if set(fields) != set(ground_truth):
        raise GeneBenchNumericGradeError(
            "GeneBench ground truth, manifest fields, and grader keys do not match exactly."
        )
    contract_digest = semantic_digest(
        {"ground_truth": ground_truth, "grader": grader, "answer_fields": answer_fields}
    )
    return ground_truth, fields, comparison_profile, contract_digest


def _single_numeric_field_specs(
    ground_truth: dict[str, Any], grader_config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    if set(grader_config) != {"answer_field", "key", "absolute_tolerance"}:
        raise GeneBenchNumericGradeError("GeneBench single-numeric grader fields changed.")
    if grader_config.get("answer_field") != "answer":
        raise GeneBenchNumericGradeError(
            "GeneBench single-numeric answer_field must be exactly 'answer'."
        )
    key = grader_config.get("key")
    if not isinstance(key, str) or not key or set(ground_truth) != {key}:
        raise GeneBenchNumericGradeError(
            "GeneBench single-numeric key must match the sole ground-truth field."
        )
    return _numeric_field_specs(
        ground_truth,
        {key: {"absolute_tolerance": grader_config["absolute_tolerance"]}},
        require_required_flag=False,
        allow_bounds=False,
    )


def _numeric_field_specs(
    ground_truth: dict[str, Any],
    key_configs: dict[str, Any],
    *,
    require_required_flag: bool,
    allow_bounds: bool = True,
    allow_minimum_only: bool = False,
) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    if set(key_configs) != set(ground_truth):
        return specs
    for key in sorted(key_configs):
        if not isinstance(key, str) or not key:
            raise GeneBenchNumericGradeError("GeneBench numeric keys must be nonempty strings.")
        expected = _finite_number(ground_truth[key], f"ground-truth field {key!r}")
        key_config = key_configs[key]
        allowed_keys = {"absolute_tolerance"}
        if allow_bounds:
            allowed_keys.update({"min_value", "max_value"})
        if require_required_flag:
            allowed_keys.add("required")
        base_keys = {"absolute_tolerance", *(["required"] if require_required_flag else [])}
        allowed_key_sets = [base_keys, allowed_keys]
        if allow_bounds and allow_minimum_only:
            allowed_key_sets.append(base_keys | {"min_value"})
        if not isinstance(key_config, dict) or set(key_config) not in allowed_key_sets:
            raise GeneBenchNumericGradeError(
                f"GeneBench grader key {key!r} is outside the absolute-tolerance profile."
            )
        if require_required_flag and key_config.get("required") is not True:
            raise GeneBenchNumericGradeError(
                f"GeneBench composite numeric key {key!r} must be explicitly required."
            )
        tolerance = _finite_number(
            key_config["absolute_tolerance"], f"absolute tolerance for {key!r}"
        )
        if tolerance < 0:
            raise GeneBenchNumericGradeError(f"Absolute tolerance for {key!r} must be nonnegative.")
        minimum: float | None = None
        maximum: float | None = None
        if "min_value" in key_config or "max_value" in key_config:
            if "min_value" not in key_config or (
                "max_value" not in key_config and not allow_minimum_only
            ):
                raise GeneBenchNumericGradeError(
                    f"GeneBench grader bounds for {key!r} are outside the closed profile."
                )
            minimum = _finite_number(key_config["min_value"], f"minimum for {key!r}")
            maximum = (
                _finite_number(key_config["max_value"], f"maximum for {key!r}")
                if "max_value" in key_config
                else None
            )
            if expected < minimum or (
                maximum is not None and (minimum > maximum or expected > maximum)
            ):
                raise GeneBenchNumericGradeError(
                    f"GeneBench grader bounds for {key!r} are inconsistent."
                )
        specs[key] = {
            "comparison_kind": "numeric_absolute_tolerance",
            "absolute_tolerance": tolerance,
            "min_value": minimum,
            "max_value": maximum,
        }
    return specs


def _composite_field_specs(
    ground_truth: dict[str, Any], grader_config: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], str]:
    if set(grader_config) == {"exact_match_keys", "numeric_keys"}:
        return (
            _string_numeric_composite_field_specs(ground_truth, grader_config),
            _COMPOSITE_COMPARISON_PROFILE,
        )
    allowed_integer_profiles = (
        {"integer_keys", "numeric_keys"},
        {"integer_keys", "numeric_keys", "forbid_extra_keys", "strict_answer_schema"},
    )
    if set(grader_config) in allowed_integer_profiles:
        return (
            _integer_numeric_composite_field_specs(ground_truth, grader_config),
            _INTEGER_COMPOSITE_COMPARISON_PROFILE,
        )
    raise GeneBenchNumericGradeError("GeneBench composite grader fields changed.")


def _string_numeric_composite_field_specs(
    ground_truth: dict[str, Any], grader_config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    exact_configs = grader_config.get("exact_match_keys")
    numeric_configs = grader_config.get("numeric_keys")
    if not isinstance(exact_configs, dict) or not isinstance(numeric_configs, dict):
        raise GeneBenchNumericGradeError("GeneBench composite grader maps are malformed.")
    if set(exact_configs) & set(numeric_configs):
        raise GeneBenchNumericGradeError("GeneBench composite grader keys overlap.")
    numeric_ground_truth = {
        key: ground_truth[key] for key in numeric_configs if key in ground_truth
    }
    specs = _numeric_field_specs(
        numeric_ground_truth,
        numeric_configs,
        require_required_flag=True,
    )
    for key in sorted(exact_configs):
        config = exact_configs[key]
        if key not in ground_truth or not isinstance(key, str) or not key:
            raise GeneBenchNumericGradeError("GeneBench exact-match keys are inconsistent.")
        if (
            not isinstance(config, dict)
            or set(config) != {"case_sensitive", "required"}
            or config.get("case_sensitive") is not True
            or config.get("required") is not True
            or not isinstance(ground_truth[key], str)
        ):
            raise GeneBenchNumericGradeError(
                f"GeneBench exact-match key {key!r} is outside the required case-sensitive "
                "string profile."
            )
        specs[key] = {"comparison_kind": "exact_string"}
    return specs


def _integer_numeric_composite_field_specs(
    ground_truth: dict[str, Any], grader_config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    for flag in ("forbid_extra_keys", "strict_answer_schema"):
        if flag in grader_config and grader_config[flag] is not True:
            raise GeneBenchNumericGradeError(
                f"GeneBench integer composite flag {flag!r} must be exactly true."
            )
    integer_configs = grader_config.get("integer_keys")
    numeric_configs = grader_config.get("numeric_keys")
    if (
        not isinstance(integer_configs, dict)
        or not integer_configs
        or not isinstance(numeric_configs, dict)
        or not numeric_configs
    ):
        raise GeneBenchNumericGradeError("GeneBench integer composite grader maps are malformed.")
    if set(integer_configs) & set(numeric_configs):
        raise GeneBenchNumericGradeError("GeneBench composite grader keys overlap.")
    numeric_ground_truth = {
        key: ground_truth[key] for key in numeric_configs if key in ground_truth
    }
    specs = _numeric_field_specs(
        numeric_ground_truth,
        numeric_configs,
        require_required_flag=False,
        allow_bounds=False,
    )
    for key in sorted(integer_configs):
        key_config = integer_configs[key]
        if key not in ground_truth or not isinstance(key, str) or not key:
            raise GeneBenchNumericGradeError("GeneBench integer keys are inconsistent.")
        if not isinstance(key_config, dict) or set(key_config) not in (
            {"min_value"},
            {"min_value", "max_value"},
        ):
            raise GeneBenchNumericGradeError(
                f"GeneBench integer key {key!r} is outside the closed exact-integer profile."
            )
        expected = _json_integer(ground_truth[key], f"ground-truth field {key!r}")
        minimum = _json_integer(key_config["min_value"], f"minimum for {key!r}")
        maximum = (
            _json_integer(key_config["max_value"], f"maximum for {key!r}")
            if "max_value" in key_config
            else None
        )
        if expected < minimum or (
            maximum is not None and (minimum > maximum or expected > maximum)
        ):
            raise GeneBenchNumericGradeError(
                f"GeneBench integer bounds for {key!r} are inconsistent."
            )
        specs[key] = {
            "comparison_kind": "integer_exact",
            "min_value": minimum,
            "max_value": maximum,
        }
    return specs


def _numeric_comparison(
    key: str,
    actual: Any,
    expected: Any,
    spec: dict[str, Any],
) -> dict[str, Any]:
    actual_value = _finite_number(actual, f"answer field {key!r}")
    expected_value = _finite_number(expected, f"ground-truth field {key!r}")
    tolerance = float(spec["absolute_tolerance"])
    absolute_error = abs(actual_value - expected_value)
    if not math.isfinite(absolute_error):
        raise GeneBenchNumericGradeError(
            f"Numeric comparison for {key!r} overflowed the finite profile."
        )
    minimum = spec.get("min_value")
    maximum = spec.get("max_value")
    within_range = (minimum is None or actual_value >= float(minimum)) and (
        maximum is None or actual_value <= float(maximum)
    )
    within_tolerance = absolute_error <= tolerance
    comparison: dict[str, Any] = {
        "key": key,
        "comparison_kind": "numeric_absolute_tolerance",
        "actual_value_digest": semantic_digest({"value": actual}),
        "expected_value_digest": semantic_digest({"value": expected}),
        "absolute_error": absolute_error,
        "absolute_tolerance": tolerance,
        "within_allowed_range": within_range,
        "within_tolerance": within_tolerance,
        "matches_contract": within_range and within_tolerance,
    }
    if minimum is not None:
        comparison["allowed_range"] = {"minimum": minimum}
        if maximum is not None:
            comparison["allowed_range"]["maximum"] = maximum
    return comparison


def _exact_string_comparison(key: str, actual: Any, expected: Any) -> dict[str, Any]:
    if not isinstance(actual, str) or not isinstance(expected, str):
        raise GeneBenchNumericGradeError(
            f"Exact-string comparison field {key!r} must contain strings."
        )
    exact_match = actual == expected
    return {
        "key": key,
        "comparison_kind": "exact_string",
        "actual_value_digest": semantic_digest({"value": actual}),
        "expected_value_digest": semantic_digest({"value": expected}),
        "case_sensitive": True,
        "exact_match": exact_match,
        "matches_contract": exact_match,
    }


def _integer_comparison(
    key: str,
    actual: Any,
    expected: Any,
    spec: dict[str, Any],
) -> dict[str, Any]:
    actual_value = _json_integer(actual, f"answer field {key!r}")
    expected_value = _json_integer(expected, f"ground-truth field {key!r}")
    minimum = int(spec["min_value"])
    maximum = spec.get("max_value")
    within_range = actual_value >= minimum and (maximum is None or actual_value <= int(maximum))
    exact_match = actual_value == expected_value
    comparison: dict[str, Any] = {
        "key": key,
        "comparison_kind": "integer_exact",
        "actual_value_digest": semantic_digest({"value": actual}),
        "expected_value_digest": semantic_digest({"value": expected}),
        "exact_match": exact_match,
        "within_allowed_range": within_range,
        "matches_contract": within_range and exact_match,
        "allowed_range": {"minimum": minimum},
    }
    if maximum is not None:
        comparison["allowed_range"]["maximum"] = int(maximum)
    return comparison


def _answer_values(payload: bytes, expected_keys: list[str]) -> dict[str, Any]:
    submission = _load_json_object(payload, _ANSWER_PATH, max_bytes=_MAX_JSON_BYTES)
    if set(submission) != {"answer", "reasoning"}:
        raise GeneBenchNumericGradeError(
            "GeneBench answer must contain exactly 'answer' and 'reasoning'."
        )
    answer = submission.get("answer")
    if not isinstance(answer, dict) or set(answer) != set(expected_keys):
        raise GeneBenchNumericGradeError(
            "GeneBench answer keys do not exactly match the verified contract."
        )
    if not isinstance(submission.get("reasoning"), str):
        raise GeneBenchNumericGradeError("GeneBench answer reasoning must be a string.")
    return answer


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeneBenchNumericGradeError(f"{label} must be one JSON number.")
    try:
        number = float(value)
    except OverflowError as error:
        raise GeneBenchNumericGradeError(
            f"{label} is outside the finite numeric profile."
        ) from error
    if not math.isfinite(number):
        raise GeneBenchNumericGradeError(f"{label} must be finite.")
    return number


def _json_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GeneBenchNumericGradeError(f"{label} must be one JSON integer.")
    return value


def _read_package_file(root: Path, path_value: str) -> bytes:
    relative = PurePosixPath(path_value)
    if (
        not path_value
        or relative.is_absolute()
        or relative.as_posix() != path_value
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise GeneBenchNumericGradeError(f"Unsafe GeneBench package path {path_value!r}.")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise GeneBenchNumericGradeError(
                f"GeneBench package path {path_value!r} crosses a symbolic link."
            )
    if not current.is_file():
        raise GeneBenchNumericGradeError(
            f"GeneBench package path {path_value!r} is not a regular file."
        )
    return current.read_bytes()


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise GeneBenchNumericGradeError(f"Required {label} is unavailable or unsafe.")
    return _load_json_object(path.read_bytes(), label)


def _load_json_object(
    payload: bytes, label: str, *, max_bytes: int | None = None
) -> dict[str, Any]:
    if max_bytes is not None and len(payload) > max_bytes:
        raise GeneBenchNumericGradeError(f"JSON input {label!r} exceeds the read limit.")

    def reject_constant(value: str) -> None:
        raise GeneBenchNumericGradeError(
            f"JSON input {label!r} contains non-finite constant {value!r}."
        )

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise GeneBenchNumericGradeError(
                    f"JSON input {label!r} contains duplicate key {key!r}."
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
    except UnicodeDecodeError as error:
        raise GeneBenchNumericGradeError(f"JSON input {label!r} is not UTF-8.") from error
    except json.JSONDecodeError as error:
        raise GeneBenchNumericGradeError(f"JSON input {label!r} is invalid.") from error
    if not isinstance(value, dict):
        raise GeneBenchNumericGradeError(f"JSON input {label!r} must be one object.")
    return value


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise GeneBenchNumericGradeError(f"Invalid GeneBench grade timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise GeneBenchNumericGradeError("GeneBench grade timestamps must include an offset.")
    return parsed


__all__ = [
    "GeneBenchNumericGradeError",
    "grade_genebench_public_answer",
    "grade_genebench_public_numeric_answer",
]
