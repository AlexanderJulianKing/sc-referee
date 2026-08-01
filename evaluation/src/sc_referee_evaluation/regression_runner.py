from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, cast

from sc_referee.calculation_checks.profiles import calculation_check_release_registry
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.version import SCHEMA_VERSION
from sc_referee_evaluation.regression_corpus import (
    DEFAULT_REGRESSION_CORPUS_LEDGER,
    validate_regression_corpus_ledger,
)

REGRESSION_CORPUS_RUNNER_VERSION = "1.0.0"
REGRESSION_CORPUS_EXECUTION_PLAN_VERSION = "1.0.0"
DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN = Path(
    "evaluation/regression-corpus-v1/execution-plan.json"
)

_MAX_PLAN_BYTES = 4_194_304
_DIGEST_PREFIX = "sha256:"
_PLAN_KEYS = {
    "plan_id",
    "plan_version",
    "record_type",
    "ledger_digest",
    "audit_replay_cases",
    "limitations",
    "plan_digest",
}
_CASE_KEYS = {
    "case_id",
    "report_path",
    "material_inputs",
    "registry_profile",
    "expected",
}
_OUTCOME_KEYS = {
    "final_state",
    "assessment_counts",
    "question_dimensions",
    "disclosure_title_counts",
    "calculation_observations",
    "coverage_termination_reasons",
    "execution_count",
    "project_execution_authorization_count",
    "model_call_count",
    "model_access_after_lock",
    "replay_equal",
}
_ASSESSMENT_KEYS = {
    "findings",
    "conditional_concerns",
    "material_questions",
    "disclosures",
}
_TITLE_COUNT_KEYS = {"title", "count"}
_CALCULATION_OBSERVATION_KEYS = {
    "check_id",
    "applicability",
    "comparison_outcome",
    "output_ceiling",
}
_DIRECT_REGISTRY_PROFILE = "calculation_check_release_v1"

PytestRunner = Callable[[tuple[str, ...]], None]


class RegressionCorpusRunnerError(ValueError):
    """A corpus run or comparison escaped its closed development contract."""


def validate_regression_corpus_execution_plan(
    plan_path: Path = DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN,
    *,
    ledger_path: Path = DEFAULT_REGRESSION_CORPUS_LEDGER,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Validate the immutable direct-audit plan against the current corpus ledger."""

    root = (project_root or Path.cwd()).resolve()
    ledger = validate_regression_corpus_ledger(ledger_path, project_root=root)
    path = _resolve_file(plan_path, root, "regression-corpus execution plan")
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise RegressionCorpusRunnerError(
            "Regression-corpus execution plan is unreadable."
        ) from error
    if len(payload) > _MAX_PLAN_BYTES:
        raise RegressionCorpusRunnerError(
            "Regression-corpus execution plan exceeds its byte limit."
        )
    plan = _load_canonical_object(payload)
    _require_exact_keys(plan, _PLAN_KEYS, "regression-corpus execution plan")
    _require_text(plan.get("plan_id"), "plan_id")
    if plan.get("plan_version") != REGRESSION_CORPUS_EXECUTION_PLAN_VERSION:
        raise RegressionCorpusRunnerError("Unsupported regression-corpus execution plan version.")
    if plan.get("record_type") != "regression_corpus_execution_plan":
        raise RegressionCorpusRunnerError(
            "Unexpected regression-corpus execution plan record type."
        )
    if plan.get("ledger_digest") != ledger["ledger_digest"]:
        raise RegressionCorpusRunnerError("Execution plan ledger digest mismatch.")

    sources = {str(item["source_id"]): item for item in ledger["sources"]}
    cases = {str(item["case_id"]): item for item in ledger["cases"]}
    expected_direct_ids = {
        case_id
        for case_id, case in cases.items()
        if sources[str(case["source_ref"])]["source_kind"] == "repository_tree"
    }
    direct_items = _object_array(plan.get("audit_replay_cases"), "audit_replay_cases")
    direct_ids: list[str] = []
    for item in direct_items:
        _require_exact_keys(item, _CASE_KEYS, "audit/replay case")
        case_id = _require_text(item.get("case_id"), "case_id")
        direct_ids.append(case_id)
        case = cases.get(case_id)
        if case is None or case_id not in expected_direct_ids:
            raise RegressionCorpusRunnerError(
                f"Audit/replay case {case_id!r} is not a local repository-tree case."
            )
        if item.get("registry_profile") != _DIRECT_REGISTRY_PROFILE:
            raise RegressionCorpusRunnerError(
                f"Audit/replay case {case_id!r} uses an unsupported registry profile."
            )
        source = sources[str(case["source_ref"])]
        workspace = _resolve_workspace(root, source, case)
        report_path = _require_safe_relative(item.get("report_path"), "report_path")
        _require_workspace_file(workspace, report_path, "report")
        material_inputs = _string_array(
            item.get("material_inputs"), "material_inputs", require_nonempty=True
        )
        if material_inputs != sorted(material_inputs):
            raise RegressionCorpusRunnerError(f"Material inputs for {case_id!r} must be sorted.")
        for material_input in material_inputs:
            _require_workspace_file(
                workspace,
                _require_safe_relative(material_input, "material input"),
                "material input",
            )
        expected = _validate_expected_outcome(item.get("expected"), case_id)
        expected_check_ids = {
            str(entry["check_id"]) for entry in expected["calculation_observations"]
        }
        if expected_check_ids != set(case["component_refs"]):
            raise RegressionCorpusRunnerError(
                f"Audit/replay case {case_id!r} does not exactly cover its ledger components."
            )
        observed_states = {
            str(entry["applicability"]) for entry in expected["calculation_observations"]
        }
        if not observed_states.issubset(set(case["expected_applicability"])):
            raise RegressionCorpusRunnerError(
                f"Audit/replay case {case_id!r} exceeds its ledger applicability declaration."
            )

    if direct_ids != sorted(direct_ids) or len(direct_ids) != len(set(direct_ids)):
        raise RegressionCorpusRunnerError("Audit/replay cases must be sorted and unique.")
    if set(direct_ids) != expected_direct_ids:
        missing = sorted(expected_direct_ids - set(direct_ids))
        extra = sorted(set(direct_ids) - expected_direct_ids)
        raise RegressionCorpusRunnerError(
            "Execution plan does not exactly cover repository-tree cases; "
            f"missing={missing!r}, extra={extra!r}."
        )

    limitations = _string_array(plan.get("limitations"), "limitations", require_nonempty=True)
    if limitations != sorted(limitations):
        raise RegressionCorpusRunnerError("Execution-plan limitations must be sorted.")
    digest_input = dict(plan)
    declared_digest = digest_input.pop("plan_digest")
    _require_digest(declared_digest, "plan_digest")
    if declared_digest != semantic_digest(digest_input):
        raise RegressionCorpusRunnerError("Regression-corpus execution plan digest mismatch.")
    return plan


def corpus_semantic_projection(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Project stable assessment meaning without IDs, timestamps, reports, or SQLite."""

    question_dimensions = sorted(
        str(item.get("unknown_semantic_dimension"))
        for item in _mapping_array(bundle.get("material_questions"), "material_questions")
    )
    title_counts = Counter(
        str(item.get("title")) for item in _mapping_array(bundle.get("disclosures"), "disclosures")
    )
    calculation_observations = []
    for observation in _mapping_array(
        bundle.get("deterministic_check_observations"), "deterministic_check_observations"
    ):
        check_manifest = _mapping(observation.get("check_manifest"), "check_manifest")
        comparison = _mapping(observation.get("comparison"), "comparison")
        calculation_observations.append(
            {
                "check_id": str(check_manifest.get("check_id")),
                "applicability": str(observation.get("applicability")),
                "comparison_outcome": str(comparison.get("outcome")),
                "output_ceiling": str(observation.get("output_ceiling")),
            }
        )
    calculation_observations.sort(
        key=lambda item: (
            item["check_id"],
            item["applicability"],
            item["comparison_outcome"],
            item["output_ceiling"],
        )
    )
    coverage_reasons = sorted(
        {
            reason
            for item in _mapping_array(bundle.get("coverage_records"), "coverage_records")
            if (
                reason := _mapping(item.get("extensions"), "coverage extensions").get(
                    "x-termination-reason"
                )
            )
            is not None
        }
    )
    return {
        "assessment_counts": {
            "findings": len(_mapping_array(bundle.get("findings"), "findings")),
            "conditional_concerns": len(
                _mapping_array(bundle.get("conditional_concerns"), "conditional_concerns")
            ),
            "material_questions": len(
                _mapping_array(bundle.get("material_questions"), "material_questions")
            ),
            "disclosures": len(_mapping_array(bundle.get("disclosures"), "disclosures")),
        },
        "question_dimensions": question_dimensions,
        "disclosure_title_counts": [
            {"title": title, "count": count} for title, count in sorted(title_counts.items())
        ],
        "calculation_observations": calculation_observations,
        "coverage_termination_reasons": coverage_reasons,
        "execution_count": len(_mapping_array(bundle.get("executions"), "executions")),
        "project_execution_authorization_count": len(
            _mapping_array(
                bundle.get("project_execution_authorizations"),
                "project_execution_authorizations",
            )
        ),
    }


def compare_corpus_semantic_outcome(
    expected: Mapping[str, Any], observed: Mapping[str, Any]
) -> None:
    """Fail with a precise regression class for one declared semantic outcome."""

    expected_counts = _mapping(expected.get("assessment_counts"), "expected assessment_counts")
    observed_counts = _mapping(observed.get("assessment_counts"), "observed assessment_counts")
    if int(observed_counts.get("findings", -1)) > int(expected_counts.get("findings", -1)):
        raise RegressionCorpusRunnerError("unexpected Finding")
    if int(observed_counts.get("conditional_concerns", -1)) > int(
        expected_counts.get("conditional_concerns", -1)
    ):
        raise RegressionCorpusRunnerError("unexpected ConditionalConcern")

    expected_questions = Counter(cast(Sequence[str], expected.get("question_dimensions", ())))
    observed_questions = Counter(cast(Sequence[str], observed.get("question_dimensions", ())))
    if expected_questions - observed_questions:
        raise RegressionCorpusRunnerError("lost question")
    if observed_questions - expected_questions:
        raise RegressionCorpusRunnerError("new false question")

    expected_disclosures = _title_count_counter(expected.get("disclosure_title_counts"))
    observed_disclosures = _title_count_counter(observed.get("disclosure_title_counts"))
    if expected_disclosures - observed_disclosures:
        raise RegressionCorpusRunnerError("missing Disclosure")
    if observed_disclosures - expected_disclosures:
        raise RegressionCorpusRunnerError("new Disclosure")

    expected_observations = _observation_index(expected.get("calculation_observations"))
    observed_observations = _observation_index(observed.get("calculation_observations"))
    if set(expected_observations) != set(observed_observations):
        raise RegressionCorpusRunnerError("calculation observation inventory changed")
    for check_id in sorted(expected_observations):
        expected_observation = expected_observations[check_id]
        observed_observation = observed_observations[check_id]
        if expected_observation["output_ceiling"] != observed_observation["output_ceiling"]:
            raise RegressionCorpusRunnerError("changed output ceiling")
        if expected_observation["applicability"] != observed_observation["applicability"]:
            raise RegressionCorpusRunnerError("applicability changed")
        if expected_observation["comparison_outcome"] != observed_observation["comparison_outcome"]:
            raise RegressionCorpusRunnerError("calculation comparison outcome changed")

    if (
        int(observed.get("execution_count", -1)) != 0
        or int(observed.get("project_execution_authorization_count", -1)) != 0
    ):
        raise RegressionCorpusRunnerError("project execution detected")
    if int(observed.get("model_call_count", -1)) != 0:
        raise RegressionCorpusRunnerError("model access detected")
    if observed.get("model_access_after_lock") is not False:
        raise RegressionCorpusRunnerError("post-lock model call detected")
    if observed.get("replay_equal") is not True:
        raise RegressionCorpusRunnerError("replay difference")
    if observed.get("final_state") != expected.get("final_state"):
        raise RegressionCorpusRunnerError("final audit state changed")
    if observed.get("coverage_termination_reasons") != expected.get("coverage_termination_reasons"):
        raise RegressionCorpusRunnerError("partial coverage changed")
    if observed_counts != expected_counts:
        raise RegressionCorpusRunnerError("assessment counts changed")
    if observed != expected:
        raise RegressionCorpusRunnerError("semantic outcome changed")


def run_regression_corpus(
    *,
    project_root: Path | None = None,
    ledger_path: Path = DEFAULT_REGRESSION_CORPUS_LEDGER,
    plan_path: Path = DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN,
    output: Path | None = None,
    pytest_runner: PytestRunner | None = None,
) -> dict[str, Any]:
    """Run all local retained cases without executing target-project code or calling models."""

    root = (project_root or Path.cwd()).resolve()
    destination: Path | None = None
    if output is not None:
        destination = output if output.is_absolute() else root / output
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"regression-corpus receipt already exists: {destination}")
    ledger = validate_regression_corpus_ledger(ledger_path, project_root=root)
    plan = validate_regression_corpus_execution_plan(
        plan_path, ledger_path=ledger_path, project_root=root
    )
    sources = {str(item["source_id"]): item for item in ledger["sources"]}
    cases = {str(item["case_id"]): item for item in ledger["cases"]}
    external_sources = sorted(
        source_id
        for source_id, source in sources.items()
        if source["source_kind"] == "external_revision"
    )
    if external_sources:
        raise RegressionCorpusRunnerError(
            "External corpus sources require a separately pinned offline preparation step: "
            + ", ".join(external_sources)
        )

    pytest_node_ids = tuple(_pytest_node_ids(ledger, sources))
    (pytest_runner or _run_pytest_subprocess)(pytest_node_ids)

    direct_results: list[dict[str, Any]] = []
    schema_root = root / "reference" / f"schemas-v{SCHEMA_VERSION}"
    with tempfile.TemporaryDirectory(prefix="sc-referee-regression-corpus-") as temporary:
        temporary_root = Path(temporary)
        for item in plan["audit_replay_cases"]:
            case_id = str(item["case_id"])
            case = cases[case_id]
            source = sources[str(case["source_ref"])]
            retained_workspace = _resolve_workspace(root, source, case)
            case_root = temporary_root / case_id.replace(":", "-")
            workspace = case_root / "workspace"
            shutil.copytree(retained_workspace, workspace)
            audit_root = case_root / "audit"
            replay_root = audit_root.parent / "replay"
            bundle = run_audit(
                workspace,
                audit_root,
                schema_root,
                report=str(item["report_path"]),
                material_inputs=tuple(cast(list[str], item["material_inputs"])),
                calculation_check_registry=calculation_check_release_registry(),
            )
            lock = _load_json_file(audit_root / "semantic.lock.json", "semantic lock")
            replayed = replay(audit_root / "semantic.lock.json", replay_root, schema_root)
            semantic = corpus_semantic_projection(bundle)
            replay_semantic = corpus_semantic_projection(replayed)
            audit_runs = _mapping_array(bundle.get("audit_runs"), "audit_runs")
            final_state = str(audit_runs[-1].get("state")) if audit_runs else "missing"
            observed = {
                "final_state": final_state,
                **semantic,
                "model_call_count": len(
                    _mapping_array(lock.get("model_calls"), "semantic-lock model_calls")
                ),
                "model_access_after_lock": lock.get("model_access_after_lock"),
                "replay_equal": semantic == replay_semantic,
            }
            compare_corpus_semantic_outcome(cast(Mapping[str, Any], item["expected"]), observed)
            direct_results.append(
                {
                    "case_id": case_id,
                    "semantic_outcome": observed,
                    "semantic_outcome_digest": semantic_digest(observed),
                }
            )

    role_counts = Counter(str(item["case_role"]) for item in ledger["cases"])
    receipt: dict[str, Any] = {
        "record_type": "regression_corpus_run_receipt",
        "runner_version": REGRESSION_CORPUS_RUNNER_VERSION,
        "ledger_id": ledger["ledger_id"],
        "ledger_digest": ledger["ledger_digest"],
        "plan_id": plan["plan_id"],
        "plan_digest": plan["plan_digest"],
        "ledger_case_count": len(ledger["cases"]),
        "pytest_case_count": sum(
            1
            for case in ledger["cases"]
            if sources[str(case["source_ref"])]["source_kind"] == "pytest_module"
        ),
        "pytest_selector_count": len(pytest_node_ids),
        "audit_replay_case_count": len(direct_results),
        "case_role_counts": dict(sorted(role_counts.items())),
        "pytest_status": "passed",
        "audit_replay_results": direct_results,
        "target_project_code_executed": False,
        "model_access_after_lock": False,
        "qualification_evidence_created": False,
        "limitations": plan["limitations"],
    }
    receipt["receipt_digest"] = semantic_digest(receipt)
    if destination is not None:
        write_normalized_json_once(destination, receipt)
    return receipt


def _run_pytest_subprocess(node_ids: tuple[str, ...]) -> None:
    if not node_ids:
        raise RegressionCorpusRunnerError("Regression corpus contains no local pytest cases.")
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *node_ids],
        check=False,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if completed.returncode != 0:
        details = "\n".join((completed.stdout + "\n" + completed.stderr).splitlines()[-40:])
        raise RegressionCorpusRunnerError(
            "Retained pytest corpus failed. Last bounded output:\n" + details
        )


def _pytest_node_ids(
    ledger: Mapping[str, Any], sources: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    node_ids = {
        f"{sources[str(case['source_ref'])]['path']}::{case['selector']}"
        for case in cast(list[dict[str, Any]], ledger["cases"])
        if sources[str(case["source_ref"])]["source_kind"] == "pytest_module"
    }
    return sorted(node_ids)


def _resolve_workspace(root: Path, source: Mapping[str, Any], case: Mapping[str, Any]) -> Path:
    source_root = root.joinpath(*_safe_relative(str(source["path"]), "source path").parts)
    selected = source_root.joinpath(*_safe_relative(str(case["selector"]), "case selector").parts)
    workspace = selected / "workspace"
    if workspace.is_symlink() or not workspace.is_dir():
        raise RegressionCorpusRunnerError(
            f"Repository-tree case {case['case_id']!r} lacks a safe workspace directory."
        )
    if not workspace.resolve().is_relative_to(source_root.resolve()):
        raise RegressionCorpusRunnerError("Repository-tree workspace escapes its retained source.")
    return workspace


def _require_workspace_file(workspace: Path, relative: PurePosixPath, label: str) -> None:
    current = workspace
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RegressionCorpusRunnerError(
                f"{label.capitalize()} paths cannot traverse symlinks."
            )
    resolved = current.resolve()
    if not resolved.is_relative_to(workspace.resolve()) or not resolved.is_file():
        raise RegressionCorpusRunnerError(
            f"{label.capitalize()} must resolve to one regular workspace file."
        )


def _validate_expected_outcome(value: object, case_id: str) -> dict[str, Any]:
    expected = _mapping(value, "expected outcome")
    _require_exact_keys(expected, _OUTCOME_KEYS, "expected outcome")
    if expected.get("final_state") != "complete":
        raise RegressionCorpusRunnerError(f"Expected outcome for {case_id!r} must complete.")
    counts = _mapping(expected.get("assessment_counts"), "assessment_counts")
    _require_exact_keys(counts, _ASSESSMENT_KEYS, "assessment_counts")
    for key in sorted(_ASSESSMENT_KEYS):
        if type(counts.get(key)) is not int or int(counts[key]) < 0:
            raise RegressionCorpusRunnerError(f"Assessment count {key!r} must be nonnegative.")
    if counts["findings"] != 0 or counts["conditional_concerns"] != 0:
        raise RegressionCorpusRunnerError(
            f"Expected outcome for {case_id!r} cannot authorize Findings or concerns."
        )
    questions = _string_array(
        expected.get("question_dimensions"), "question_dimensions", require_nonempty=False
    )
    if questions != sorted(questions) or len(questions) != counts["material_questions"]:
        raise RegressionCorpusRunnerError(
            f"Expected question dimensions for {case_id!r} are unsorted or miscounted."
        )
    title_counts = _object_array(
        expected.get("disclosure_title_counts"),
        "disclosure_title_counts",
        require_nonempty=counts["disclosures"] > 0,
    )
    titles: list[str] = []
    disclosure_total = 0
    for item in title_counts:
        _require_exact_keys(item, _TITLE_COUNT_KEYS, "disclosure title count")
        title = _require_text(item.get("title"), "disclosure title")
        count = item.get("count")
        if type(count) is not int or count <= 0:
            raise RegressionCorpusRunnerError("Disclosure title count must be positive.")
        titles.append(title)
        disclosure_total += count
    if titles != sorted(titles) or len(titles) != len(set(titles)):
        raise RegressionCorpusRunnerError("Disclosure title counts must be sorted and unique.")
    if disclosure_total != counts["disclosures"]:
        raise RegressionCorpusRunnerError("Disclosure title counts do not match assessment counts.")
    observations = _object_array(
        expected.get("calculation_observations"),
        "calculation_observations",
        require_nonempty=True,
    )
    check_ids: list[str] = []
    for item in observations:
        _require_exact_keys(item, _CALCULATION_OBSERVATION_KEYS, "calculation observation")
        check_ids.append(_require_text(item.get("check_id"), "check_id"))
        if item.get("applicability") not in {
            "applicable",
            "not_applicable",
            "ambiguous",
            "unsupported",
        }:
            raise RegressionCorpusRunnerError("Unknown expected calculation applicability.")
        if item.get("comparison_outcome") not in {
            "conformant",
            "nonconformant",
            "not_applicable",
            "unknown",
        }:
            raise RegressionCorpusRunnerError("Unknown expected calculation comparison outcome.")
        if item.get("output_ceiling") != "disclosure_only":
            raise RegressionCorpusRunnerError("Direct corpus cases cannot exceed disclosure-only.")
    if check_ids != sorted(check_ids) or len(check_ids) != len(set(check_ids)):
        raise RegressionCorpusRunnerError("Calculation observations must be sorted and unique.")
    coverage = _string_array(
        expected.get("coverage_termination_reasons"),
        "coverage_termination_reasons",
        require_nonempty=True,
    )
    if coverage != sorted(coverage):
        raise RegressionCorpusRunnerError("Coverage termination reasons must be sorted.")
    for count_key in (
        "execution_count",
        "project_execution_authorization_count",
        "model_call_count",
    ):
        if expected.get(count_key) != 0:
            raise RegressionCorpusRunnerError(
                f"Expected outcome for {case_id!r} cannot authorize {count_key}."
            )
    if expected.get("model_access_after_lock") is not False:
        raise RegressionCorpusRunnerError("Expected outcome cannot authorize late model access.")
    if expected.get("replay_equal") is not True:
        raise RegressionCorpusRunnerError("Expected outcome must require exact semantic replay.")
    return dict(expected)


def _title_count_counter(value: object) -> Counter[str]:
    result: Counter[str] = Counter()
    for item in _mapping_array(value, "disclosure_title_counts"):
        result[str(item.get("title"))] = int(item.get("count", 0))
    return result


def _observation_index(value: object) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in _mapping_array(value, "calculation_observations"):
        check_id = str(item.get("check_id"))
        if check_id in result:
            raise RegressionCorpusRunnerError("Duplicate calculation observation in outcome.")
        result[check_id] = item
    return result


def _resolve_file(path: Path, root: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else root / path
    if candidate.is_symlink() or not candidate.is_file():
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must be one non-symlink file.")
    return candidate.resolve()


def _load_json_file(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RegressionCorpusRunnerError(
            f"{label.capitalize()} is unavailable or invalid."
        ) from error
    if not isinstance(value, dict):
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must contain one object.")
    return cast(dict[str, Any], value)


def _load_canonical_object(payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RegressionCorpusRunnerError) as error:
        raise RegressionCorpusRunnerError(
            f"Regression-corpus execution plan is not strict JSON: {error}"
        ) from error
    if not isinstance(value, dict):
        raise RegressionCorpusRunnerError("Execution plan must contain one JSON object.")
    if payload != canonical_json(value).encode("utf-8") + b"\n":
        raise RegressionCorpusRunnerError(
            "Execution plan must be canonical JSON ending in one newline."
        )
    return cast(dict[str, Any], value)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RegressionCorpusRunnerError(f"Duplicate JSON key {key!r} is not permitted.")
        value[key] = item
    return value


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must be one object.")
    return cast(Mapping[str, Any], value)


def _mapping_array(value: object, label: str) -> list[Mapping[str, Any]]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, Mapping) for item in value)
    ):
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must be an array of objects.")
    return [cast(Mapping[str, Any], item) for item in value]


def _object_array(
    value: object, label: str, *, require_nonempty: bool = True
) -> list[dict[str, Any]]:
    items = _mapping_array(value, label)
    if require_nonempty and not items:
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must not be empty.")
    return [dict(item) for item in items]


def _string_array(value: object, label: str, *, require_nonempty: bool) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or (require_nonempty and not value)
        or not all(isinstance(item, str) and item and item.strip() == item for item in value)
    ):
        raise RegressionCorpusRunnerError(f"{label} must be an array of normalized strings.")
    result = [str(item) for item in value]
    if len(result) != len(set(result)):
        raise RegressionCorpusRunnerError(f"{label} entries must be unique.")
    return result


def _safe_relative(value: str, label: str) -> PurePosixPath:
    if "\\" in value:
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must use POSIX separators.")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RegressionCorpusRunnerError(f"{label.capitalize()} must be bounded and relative.")
    return path


def _require_safe_relative(value: object, label: str) -> PurePosixPath:
    return _safe_relative(_require_text(value, label), label)


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise RegressionCorpusRunnerError(f"{label.capitalize()} has unexpected fields.")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise RegressionCorpusRunnerError(f"{label} must be nonempty normalized text.")
    return value


def _require_digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith(_DIGEST_PREFIX)
        or len(value) != len(_DIGEST_PREFIX) + 64
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise RegressionCorpusRunnerError(f"{label} must be one lowercase sha256 digest.")
    return value
