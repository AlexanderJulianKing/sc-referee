from __future__ import annotations

import ast
import re
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once

_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_PROBE_VERSION = "0.2.0"

PROFILE_MANIFEST: dict[str, dict[str, str]] = {
    "directional_measurement_error_v1": {
        "expected_form": "distinct_direction_specific_misclassification_rates",
        "conflict_form": "one_average_rate_applied_symmetrically",
        "issue_class": "measurement_error_directionality_mismatch",
    },
    "phased_composite_marker_v1": {
        "expected_form": "all_required_markers_on_one_nonmissing_phase_set",
        "conflict_form": "either_single_marker_or_same_phase_marker_pair",
        "issue_class": "composite_marker_definition_mismatch",
    },
    "mutually_exclusive_class_calibration_v1": {
        "expected_form": "joint_shared_noncarrier_multiclass_calibration",
        "conflict_form": "independent_per_class_binary_inversion",
        "issue_class": "coupled_calibration_mismatch",
    },
    "cellwise_calibration_before_standardization_v1": {
        "expected_form": "calibrate_inside_each_target_population_cell_then_weight",
        "conflict_form": "weight_raw_positive_rates_then_calibrate_the_aggregate",
        "issue_class": "calibration_standardization_order_mismatch",
    },
    "ril_founder_orientation_before_emission_v1": {
        "expected_form": "repair_ril_founder_orientation_before_hmm_emission",
        "conflict_form": "use_supplied_founder_alleles_directly_in_hmm_emission",
        "issue_class": "founder_allele_orientation_mismatch",
    },
    "full_map_ancestry_exposure_v1": {
        "expected_form": "full_chromosome_map_exposure",
        "conflict_form": "high_confidence_called_tract_exposure_only",
        "issue_class": "ancestry_exposure_denominator_mismatch",
    },
    "ld_covariance_before_robust_fit_v1": {
        "expected_form": "ld_covariance_cholesky_whitening_before_robust_fit",
        "conflict_form": "diagonal_or_unwhitened_robust_fit",
        "issue_class": "ld_covariance_omission",
    },
}


class SourceMethodProbeError(ValueError):
    """An evaluation-only static source-method probe violated its closed contract."""


def probe_python_method_shapes(
    source_root: Path,
    source_path: str,
    profile_ids: Sequence[str],
    *,
    reference_id: str,
    reference_content_digest: str,
    diagnosed_at: str,
    output: Path,
) -> dict[str, Any]:
    """Compare closed answer-side obligations with exact Python AST shapes without execution."""

    if output.exists() or output.is_symlink():
        raise SourceMethodProbeError(f"diagnostic output already exists: {output}")
    if not reference_id.strip() or not _DIGEST.fullmatch(reference_content_digest):
        raise SourceMethodProbeError(
            "reference method requires a durable identifier and canonical content digest"
        )
    _timestamp(diagnosed_at)
    selected_profiles = _validated_profiles(profile_ids)
    root = source_root.resolve()
    relative = _safe_relative_path(source_path)
    unresolved_source = root / relative
    if unresolved_source.is_symlink():
        raise SourceMethodProbeError("source path must identify one regular non-symlink file")
    source = unresolved_source.resolve()
    try:
        source.relative_to(root)
    except ValueError as error:
        raise SourceMethodProbeError("source path escapes the declared source root") from error
    if source.is_symlink() or not source.is_file():
        raise SourceMethodProbeError("source path must identify one regular non-symlink file")
    payload = source.read_bytes()
    source_digest = sha256_digest(payload)
    try:
        source_text = payload.decode("utf-8")
        tree = ast.parse(source_text, filename=relative.as_posix(), type_comments=True)
    except (SyntaxError, UnicodeDecodeError) as error:
        raise SourceMethodProbeError(
            f"Python source is not fully parseable: {type(error).__name__}"
        ) from error
    if not isinstance(tree, ast.Module):
        raise SourceMethodProbeError("Python source did not parse as one module")

    probes: dict[str, Callable[[ast.Module, str, str], dict[str, Any]]] = {
        "directional_measurement_error_v1": _probe_directional_measurement_error,
        "phased_composite_marker_v1": _probe_phased_composite_marker,
        "mutually_exclusive_class_calibration_v1": _probe_mutually_exclusive_calibration,
        "cellwise_calibration_before_standardization_v1": (
            _probe_calibration_standardization_order
        ),
        "ril_founder_orientation_before_emission_v1": _probe_ril_founder_orientation,
        "full_map_ancestry_exposure_v1": _probe_full_map_ancestry_exposure,
        "ld_covariance_before_robust_fit_v1": _probe_ld_covariance_before_robust_fit,
    }
    results = [
        probes[profile_id](tree, relative.as_posix(), source_digest)
        for profile_id in selected_profiles
    ]
    diagnostic: dict[str, Any] = {
        "evaluation_protocol_version": "0.2.0",
        "source_method_probe_version": _PROBE_VERSION,
        "record_type": "evaluation_python_source_method_probe",
        "probe_id": stable_id(
            "evaluation-python-source-method-probe",
            source_digest,
            reference_content_digest,
            *selected_profiles,
        ),
        "diagnosed_at": diagnosed_at,
        "source": {
            "path": relative.as_posix(),
            "content_digest": source_digest,
            "language": "python",
            "inspection_method": "python_ast_without_import_or_execution",
        },
        "answer_side_reference": {
            "reference_id": reference_id,
            "content_digest": reference_content_digest,
            "production_intent_authority": False,
        },
        "profile_manifest_digest": semantic_digest(PROFILE_MANIFEST),
        "results": results,
        "metric_eligible": False,
        "held_out_eligible": False,
        "promotion_evidence_eligible": False,
        "production_finding_eligible": False,
        "project_code_executed_by_probe": False,
        "model_invoked_by_probe": False,
        "non_inferences": [
            "A static source shape does not establish that the source executed.",
            "An answer-side reference does not establish production scientific intent.",
            "A localized structural conflict does not by itself establish numeric causality.",
            "A covered negative is not a scientific correctness certificate.",
        ],
    }
    diagnostic["diagnostic_digest"] = semantic_digest(diagnostic)
    write_normalized_json_once(output, diagnostic)
    return diagnostic


def _validated_profiles(profile_ids: Sequence[str]) -> list[str]:
    values = [str(value) for value in profile_ids]
    if not values or len(values) != len(set(values)):
        raise SourceMethodProbeError("one or more unique probe profiles are required")
    unsupported = sorted(set(values) - set(PROFILE_MANIFEST))
    if unsupported:
        raise SourceMethodProbeError(f"unsupported probe profiles: {unsupported}")
    return sorted(values)


def _safe_relative_path(value: str) -> PurePosixPath:
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or "." in candidate.parts
        or ".." in candidate.parts
        or candidate.suffix != ".py"
    ):
        raise SourceMethodProbeError("source path must be one relative Python path")
    return candidate


def _probe_directional_measurement_error(
    tree: ast.Module, path: str, digest: str
) -> dict[str, Any]:
    profile_id = "directional_measurement_error_v1"
    for function in _functions(tree):
        assignments = _simple_assignments(function)
        for rate_name, rate_node, rate_value in assignments:
            if not _contains_attribute(rate_value, "seq_error"):
                continue
            for _, probability_node, probability_value in assignments:
                if _is_symmetric_probability(probability_value, rate_name):
                    return _result(
                        profile_id,
                        "exact_static_conflict",
                        PROFILE_MANIFEST[profile_id]["conflict_form"],
                        [
                            _node_ref(path, digest, rate_node),
                            _node_ref(path, digest, probability_node),
                        ],
                    )
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is not None and _is_directional_probability(value):
                return _result(
                    profile_id,
                    "covered_negative",
                    PROFILE_MANIFEST[profile_id]["expected_form"],
                    [_node_ref(path, digest, node)],
                )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _probe_phased_composite_marker(tree: ast.Module, path: str, digest: str) -> dict[str, Any]:
    profile_id = "phased_composite_marker_v1"
    for function in _functions(tree):
        assignments = {name: (node, value) for name, node, value in _simple_assignments(function)}
        for _, final_node, final_value in _simple_assignments(function):
            if not isinstance(final_value, ast.BoolOp) or not isinstance(final_value.op, ast.Or):
                continue
            resolved = [_resolve_name(value, assignments) for value in final_value.values]
            xor = next((_xor_pair(value) for value in resolved if _xor_pair(value)), None)
            if xor is None:
                continue
            same_phase = next(
                (value for value in resolved if _same_phase_marker_branch(value, set(xor))),
                None,
            )
            if same_phase is not None:
                evidence = [_node_ref(path, digest, final_node)]
                for value in final_value.values:
                    if isinstance(value, ast.Name) and value.id in assignments:
                        evidence.append(_node_ref(path, digest, assignments[value.id][0]))
                return _result(
                    profile_id,
                    "exact_static_conflict",
                    PROFILE_MANIFEST[profile_id]["conflict_form"],
                    evidence,
                )
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.BoolOp)
            and isinstance(node.value.op, ast.And)
            and _matches_all_markers_same_nonmissing_phase(node.value)
        ):
            return _result(
                profile_id,
                "covered_negative",
                PROFILE_MANIFEST[profile_id]["expected_form"],
                [_node_ref(path, digest, node)],
            )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _probe_mutually_exclusive_calibration(
    tree: ast.Module, path: str, digest: str
) -> dict[str, Any]:
    profile_id = "mutually_exclusive_class_calibration_v1"
    calibrators = _independent_scalar_calibrators(tree)
    if calibrators:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ListComp):
                continue
            calls = [item for item in ast.walk(node.elt) if isinstance(item, ast.Call)]
            if any(_call_name(call) in calibrators for call in calls):
                calibrator = next(
                    calibrators[_call_name(call)]
                    for call in calls
                    if _call_name(call) in calibrators
                )
                return _result(
                    profile_id,
                    "exact_static_conflict",
                    PROFILE_MANIFEST[profile_id]["conflict_form"],
                    [
                        _node_ref(path, digest, calibrator),
                        _node_ref(path, digest, node),
                    ],
                )
    for node in _recognized_joint_solver_calls(tree):
        if isinstance(node, ast.Call):
            return _result(
                profile_id,
                "covered_negative",
                PROFILE_MANIFEST[profile_id]["expected_form"],
                [_node_ref(path, digest, node)],
            )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _probe_calibration_standardization_order(
    tree: ast.Module, path: str, digest: str
) -> dict[str, Any]:
    profile_id = "cellwise_calibration_before_standardization_v1"
    calibrators = set(_independent_scalar_calibrators(tree))
    for function in _functions(tree):
        aggregate_assignments = {
            name: node
            for name, node, _ in _simple_assignments(function)
            if "standardized_positive_rate" in name
        }
        for aggregate_name, aggregate_node in aggregate_assignments.items():
            updates = [
                node
                for node in ast.walk(function)
                if isinstance(node, ast.AugAssign) and _root_name(node.target) == aggregate_name
            ]
            if not updates:
                continue
            calls = [
                node
                for node in ast.walk(function)
                if isinstance(node, ast.Call)
                and _call_name(node) in calibrators
                and any(aggregate_name in _names(argument) for argument in node.args)
            ]
            if calls and min(call.lineno for call in calls) > max(
                update.lineno for update in updates
            ):
                return _result(
                    profile_id,
                    "exact_static_conflict",
                    PROFILE_MANIFEST[profile_id]["conflict_form"],
                    [
                        _node_ref(path, digest, aggregate_node),
                        _node_ref(path, digest, updates[0]),
                        _node_ref(path, digest, calls[0]),
                    ],
                )
    for loop in [node for node in ast.walk(tree) if isinstance(node, ast.For)]:
        joint_calls = [
            node for node in _recognized_joint_solver_calls(tree) if node in ast.walk(loop)
        ]
        calibrated_names = {
            _assignment_name(node)
            for node in ast.walk(loop)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(node.value, ast.Call)
            and _call_name(node.value) == "solve_coupled_class_prevalence"
        }
        calibrated_names.discard(None)
        weighted_updates = [
            node
            for node in ast.walk(loop)
            if isinstance(node, ast.AugAssign)
            and any(str(name) in _names(node.value) for name in calibrated_names)
        ]
        if joint_calls and weighted_updates:
            return _result(
                profile_id,
                "covered_negative",
                PROFILE_MANIFEST[profile_id]["expected_form"],
                [
                    _node_ref(path, digest, joint_calls[0]),
                    _node_ref(path, digest, weighted_updates[0]),
                ],
            )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _probe_ril_founder_orientation(tree: ast.Module, path: str, digest: str) -> dict[str, Any]:
    profile_id = "ril_founder_orientation_before_emission_v1"
    orientation_calls = {
        "orient_ril_founder_alleles",
        "repair_ril_founder_orientation",
    }
    oriented_assignments = {
        name: node
        for name, node, value in _simple_assignments(tree)
        if isinstance(value, ast.Call) and _call_name(value) in orientation_calls
    }
    for call in [node for node in ast.walk(tree) if isinstance(node, ast.Call)]:
        if _terminal_call_name(call) != "emission_matrix" or len(call.args) < 2:
            continue
        founder_arg = call.args[1]
        if any(name in oriented_assignments for name in _names(founder_arg)):
            name = next(name for name in _names(founder_arg) if name in oriented_assignments)
            return _result(
                profile_id,
                "covered_negative",
                PROFILE_MANIFEST[profile_id]["expected_form"],
                [
                    _node_ref(path, digest, oriented_assignments[name]),
                    _node_ref(path, digest, call),
                ],
            )
    emission = next(
        (function for function in _functions(tree) if function.name == "emission_matrix"),
        None,
    )
    if emission is None:
        return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])
    direct_comparisons = [
        node
        for node in ast.walk(emission)
        if isinstance(node, ast.Compare)
        and "obs" in _names(node)
        and "founder_alleles" in _names(node)
    ]
    direct_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _terminal_call_name(node) == "emission_matrix"
        and len(node.args) >= 2
        and not any(name in oriented_assignments for name in _names(node.args[1]))
    ]
    if direct_comparisons and direct_calls and not oriented_assignments:
        return _result(
            profile_id,
            "exact_static_conflict",
            PROFILE_MANIFEST[profile_id]["conflict_form"],
            [
                _node_ref(path, digest, direct_comparisons[0]),
                _node_ref(path, digest, direct_calls[0]),
            ],
        )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _probe_full_map_ancestry_exposure(tree: ast.Module, path: str, digest: str) -> dict[str, Any]:
    profile_id = "full_map_ancestry_exposure_v1"
    for function in _functions(tree):
        assignments = {name: (node, value) for name, node, value in _simple_assignments(function)}
        full_map_names = {
            name
            for name, (_, value) in assignments.items()
            if isinstance(value, ast.Call)
            and _terminal_call_name(value) in {"full_map_exposure", "chromosome_map_exposure"}
        }
        if full_map_names:
            denominator_uses = [
                node
                for node in ast.walk(function)
                if isinstance(node, ast.BinOp)
                and any(name in _names(node) for name in full_map_names)
            ]
            if denominator_uses:
                name = sorted(full_map_names)[0]
                return _result(
                    profile_id,
                    "covered_negative",
                    PROFILE_MANIFEST[profile_id]["expected_form"],
                    [
                        _node_ref(path, digest, assignments[name][0]),
                        _node_ref(path, digest, denominator_uses[0]),
                    ],
                )
        returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
        called_exposure = [
            node
            for node in returns
            if isinstance(node.value, ast.Dict)
            and any(
                isinstance(key, ast.Constant) and key.value == "called_exposure_morgan"
                for key in node.value.keys
            )
        ]
        la = assignments.get("LA")
        lb = assignments.get("LB")
        if called_exposure and la is not None and lb is not None:
            t_assignment = assignments.get("t")
            if t_assignment is not None and {"LA", "LB"} <= _names(t_assignment[1]):
                return _result(
                    profile_id,
                    "exact_static_conflict",
                    PROFILE_MANIFEST[profile_id]["conflict_form"],
                    [
                        _node_ref(path, digest, la[0]),
                        _node_ref(path, digest, lb[0]),
                        _node_ref(path, digest, t_assignment[0]),
                        _node_ref(path, digest, called_exposure[0]),
                    ],
                )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _probe_ld_covariance_before_robust_fit(
    tree: ast.Module, path: str, digest: str
) -> dict[str, Any]:
    profile_id = "ld_covariance_before_robust_fit_v1"
    assignments = {name: (node, value) for name, node, value in _simple_assignments(tree)}
    covariance = assignments.get("covariance_y")
    chol = assignments.get("chol")
    x_white = assignments.get("x_white")
    y_white = assignments.get("y_white")
    if covariance is None or chol is None or x_white is None or y_white is None:
        return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])
    covariance_uses_ld = "r_selected" in _names(covariance[1]) and any(
        isinstance(node, ast.MatMult) for node in ast.walk(covariance[1])
    )
    chol_uses_covariance = (
        isinstance(chol[1], ast.Call)
        and _terminal_call_name(chol[1]) == "cholesky"
        and "covariance_y" in _names(chol[1])
    )
    whitened = all(
        isinstance(value, ast.Call)
        and _terminal_call_name(value) == "solve"
        and "chol" in _names(value)
        for _, value in (x_white, y_white)
    )
    robust_uses_whitened = any(
        isinstance(node, ast.Assign)
        and node.value is not None
        and {"x_white", "y_white"} & _names(node.value)
        for node in ast.walk(tree)
    )
    if covariance_uses_ld and chol_uses_covariance and whitened and robust_uses_whitened:
        return _result(
            profile_id,
            "covered_negative",
            PROFILE_MANIFEST[profile_id]["expected_form"],
            [
                _node_ref(path, digest, covariance[0]),
                _node_ref(path, digest, chol[0]),
                _node_ref(path, digest, x_white[0]),
                _node_ref(path, digest, y_white[0]),
            ],
        )
    return _result(profile_id, "unsupported_path", "unrecognized_source_shape", [])


def _result(
    profile_id: str,
    state: str,
    observed_form: str,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    manifest = PROFILE_MANIFEST[profile_id]
    return {
        "profile_id": profile_id,
        "profile_version": _PROBE_VERSION,
        "issue_class": manifest["issue_class"],
        "state": state,
        "expected_form": manifest["expected_form"],
        "observed_form": observed_form,
        "evidence": evidence,
        "causal_attribution": "not_established_by_static_probe",
    }


def _functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _simple_assignments(
    node: ast.AST,
) -> list[tuple[str, ast.Assign | ast.AnnAssign, ast.expr]]:
    assignments: list[tuple[str, ast.Assign | ast.AnnAssign, ast.expr]] = []
    for item in ast.walk(node):
        if not isinstance(item, (ast.Assign, ast.AnnAssign)) or item.value is None:
            continue
        name = _assignment_name(item)
        if name is not None:
            assignments.append((name, item, item.value))
    return assignments


def _assignment_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    if isinstance(node, ast.AnnAssign):
        return node.target.id if isinstance(node.target, ast.Name) else None
    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _contains_attribute(node: ast.AST, attribute: str) -> bool:
    return any(
        isinstance(item, ast.Attribute) and item.attr == attribute for item in ast.walk(node)
    )


def _names(node: ast.AST) -> set[str]:
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def _is_symmetric_probability(node: ast.AST, rate_name: str) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
        return False
    sides = ((node.left, node.right), (node.right, node.left))
    for rate_side, product_side in sides:
        if not _is_name(rate_side, rate_name) or not isinstance(product_side, ast.BinOp):
            continue
        if not isinstance(product_side.op, ast.Mult):
            continue
        factors = (product_side.left, product_side.right)
        if any(_is_one_minus_twice_rate(factor, rate_name) for factor in factors):
            return True
    return False


def _is_one_minus_twice_rate(node: ast.AST, rate_name: str) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Sub):
        return False
    if not _is_number(node.left, 1.0) or not isinstance(node.right, ast.BinOp):
        return False
    if not isinstance(node.right.op, ast.Mult):
        return False
    return (_is_number(node.right.left, 2.0) and _is_name(node.right.right, rate_name)) or (
        _is_number(node.right.right, 2.0) and _is_name(node.right.left, rate_name)
    )


def _is_directional_probability(node: ast.AST) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
        return False
    terms = (node.left, node.right)
    return any(
        _matches_product(first, _one_minus_name("e_da"), _named("p"))
        and _matches_product(second, _named("e_ad"), _one_minus_name("p"))
        for first, second in (terms, tuple(reversed(terms)))
    )


def _matches_product(
    node: ast.AST,
    left_matcher: Callable[[ast.AST], bool],
    right_matcher: Callable[[ast.AST], bool],
) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return False
    return (left_matcher(node.left) and right_matcher(node.right)) or (
        left_matcher(node.right) and right_matcher(node.left)
    )


def _named(name: str) -> Callable[[ast.AST], bool]:
    return lambda node: _is_name(node, name)


def _one_minus_name(name: str) -> Callable[[ast.AST], bool]:
    return lambda node: (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Sub)
        and _is_number(node.left, 1.0)
        and _is_name(node.right, name)
    )


def _is_number(node: ast.AST, value: float) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and float(node.value) == value
    )


def _is_name(node: ast.AST, value: str) -> bool:
    return isinstance(node, ast.Name) and node.id == value


def _resolve_name(
    node: ast.expr,
    assignments: dict[str, tuple[ast.Assign | ast.AnnAssign, ast.expr]],
) -> ast.expr:
    if isinstance(node, ast.Name) and node.id in assignments:
        return assignments[node.id][1]
    return node


def _xor_pair(node: ast.AST) -> frozenset[str] | None:
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.NotEq)
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Name)
        and isinstance(node.comparators[0], ast.Name)
    ):
        return frozenset({node.left.id, node.comparators[0].id})
    return None


def _same_phase_marker_branch(node: ast.AST, marker_names: set[str]) -> bool:
    if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.And):
        return False
    direct_names = {value.id for value in node.values if isinstance(value, ast.Name)}
    return marker_names.issubset(direct_names) and any(
        _is_phase_equality(item) for item in ast.walk(node)
    )


def _matches_all_markers_same_nonmissing_phase(node: ast.BoolOp) -> bool:
    direct_names = {value.id for value in node.values if isinstance(value, ast.Name)}
    marker_names = {name for name in direct_names if name.startswith("high_")}
    comparisons = [item for item in ast.walk(node) if isinstance(item, ast.Compare)]
    phase_equal = any(_is_phase_equality(item) for item in comparisons)
    nonmissing = {
        item.left.id
        for item in comparisons
        if len(item.ops) == 1
        and isinstance(item.ops[0], (ast.IsNot, ast.NotEq))
        and len(item.comparators) == 1
        and isinstance(item.left, ast.Name)
        and item.left.id.startswith("phase_")
        and isinstance(item.comparators[0], ast.Constant)
        and item.comparators[0].value is None
    }
    return len(marker_names) >= 2 and phase_equal and len(nonmissing) >= 2


def _is_phase_equality(node: ast.AST) -> bool:
    if (
        not isinstance(node, ast.Compare)
        or len(node.ops) != 1
        or not isinstance(node.ops[0], ast.Eq)
        or len(node.comparators) != 1
    ):
        return False
    sides = (node.left, node.comparators[0])
    if all(isinstance(side, ast.Name) and side.id.startswith("phase_") for side in sides):
        return True
    return all(
        isinstance(side, ast.Subscript)
        and isinstance(side.slice, ast.Constant)
        and side.slice.value == "phase_set"
        for side in sides
    )


def _independent_scalar_calibrators(
    tree: ast.Module,
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    calibrators: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for function in _functions(tree):
        argument_names = {argument.arg for argument in function.args.args}
        for returned in [item for item in ast.walk(function) if isinstance(item, ast.Return)]:
            if returned.value is None:
                continue
            for division in [
                item
                for item in ast.walk(returned.value)
                if isinstance(item, ast.BinOp) and isinstance(item.op, ast.Div)
            ]:
                if not (
                    isinstance(division.left, ast.BinOp)
                    and isinstance(division.left.op, ast.Sub)
                    and isinstance(division.right, ast.BinOp)
                    and isinstance(division.right.op, ast.Sub)
                ):
                    continue
                numerator = _names(division.left)
                denominator = _names(division.right)
                if (
                    len(numerator & denominator) == 1
                    and len(numerator) == 2
                    and len(denominator) == 2
                    and (numerator | denominator).issubset(argument_names)
                ):
                    calibrators[function.name] = function
    return calibrators


def _recognized_joint_solver_calls(tree: ast.Module) -> list[ast.Call]:
    definitions = {
        function.name: function
        for function in _functions(tree)
        if function.name == "solve_coupled_class_prevalence"
        and any(
            isinstance(node, ast.Call) and _call_name(node) == "joint_nonnegative_solution"
            for node in ast.walk(function)
        )
    }
    if set(definitions) != {"solve_coupled_class_prevalence"}:
        return []
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _call_name(node) == "solve_coupled_class_prevalence"
        and len(node.args) == 3
    ]


def _call_name(node: ast.Call) -> str:
    return node.func.id if isinstance(node.func, ast.Name) else "<dynamic>"


def _terminal_call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return "<dynamic>"


def _root_name(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Subscript, ast.Attribute)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _node_ref(path: str, digest: str, node: ast.AST) -> dict[str, Any]:
    start_line = int(getattr(node, "lineno", 1))
    end_line = int(getattr(node, "end_lineno", start_line))
    return {
        "source_kind": "file_span",
        "path": path,
        "locator": f"{path}:{start_line}-{end_line}",
        "content_digest": digest,
        "start_line": start_line,
        "end_line": end_line,
        "start_column": int(getattr(node, "col_offset", 0)) + 1,
        "end_column": int(getattr(node, "end_col_offset", 0)) + 1,
    }


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SourceMethodProbeError(f"invalid timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        raise SourceMethodProbeError("timestamps must include a timezone")
    return parsed


__all__ = [
    "PROFILE_MANIFEST",
    "SourceMethodProbeError",
    "probe_python_method_shapes",
]
