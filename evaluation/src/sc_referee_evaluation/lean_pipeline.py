"""ADR-0068 lean qualification pipeline.

One parameterized implementation drives an envelope's blind pilot end to end:
executable-case authoring (ADR-0069), sandboxed ground-truth intake, a single
blind merged review with escalation (ADR-0067), the lean label freeze, the
detector run with deterministic replay, and pilot metrics.

Process properties this module encodes structurally:

- Digest chaining flows through the envelope ``MANIFEST.json``; steps read
  their upstream digests from it, never from hand-edited constants.
- Every timestamp is recorded from the clock at artifact-write time;
  declaring a timestamp in advance is impossible here by construction.
- Reviewer calibrations are consulted from the shared calibration registry
  keyed by (model id, pinned binary version, calibration suite); an identical
  calibration is never re-run for a fresh participant label.
- Authored cases are real runnable workflows. Intake executes each authored
  workflow twice in an isolated sandbox and admits the case only when the
  committed report equals the executed output byte for byte. This bounded
  execution of program-commissioned code is the ADR-0069 ground-truth check;
  the production audit of scientists' repositories remains non-executing.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import jsonschema

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.method_contract_run import run_method_contract
from sc_referee.records.normalization import (
    normalized_json_bytes,
    write_normalized_json,
    write_normalized_json_once,
)
from sc_referee.records.observed import build_file_records
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)
from sc_referee.snapshot.repository import AssetIdentityPolicy, capture_repository
from sc_referee.storage.atomic import atomic_write_bytes
from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.review_protocol import build_stage1_review_packet
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
    project_stage1_semantic_batch_v2,
)
from sc_referee_evaluation.workspace import build_blind_workspace

SCHEMA_RELATIVE = Path("reference/schemas-v0.18.0")
CALIBRATION_REGISTRY_RELATIVE = Path("evaluation/qualification/calibration-registry.json")
MANIFEST_NAME = "MANIFEST.json"
DETECTOR_ID = "detector:bounded-analysis-method-conflict"
CLI_TIMEOUT_SECONDS = 3600
SANDBOX_TIMEOUT_SECONDS = 30
MAX_INPUT_BYTES = 65536
MAX_PRODUCER_BYTES = 16384
MAX_REPORT_BYTES = 32768
SELECTED_RESULT_MARKER = "[selected-result]"

VISIBLE_FILES = (
    {"path": "task.md", "role": "scientific_task"},
    {"path": "inputs/data.csv", "role": "staged_data"},
    {"path": "workflow/analysis.py", "role": "workflow_source"},
    {"path": "results/report.md", "role": "report"},
)

_ALLOWED_IMPORT_ROOTS = {
    "csv",
    "math",
    "statistics",
    "pathlib",
    "collections",
    "fractions",
    "decimal",
    "itertools",
    "functools",
    "json",
    "re",
}
_FORBIDDEN_NAMES = {"eval", "exec", "__import__", "compile", "globals", "locals", "vars"}

EXPECTED_VERDICT_BY_ROLE = {
    "error_bearing": "demonstrated_issue",
    "corrected_twin": "no_demonstrated_issue_within_scope",
    "valid_alternative": "no_demonstrated_issue_within_scope",
}
LABEL_STATUS_BY_ROLE = {
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "valid_alternative": "verified_good_eligible",
}


class LeanPipelineError(ValueError):
    """Fail-closed pipeline boundary."""


@dataclass(frozen=True)
class ModelParticipant:
    participant_id: str
    model_id: str
    model_name: str
    model_alias: str
    provider: str = "Anthropic"
    reasoning_configuration: str = "high"

    @property
    def slug(self) -> str:
        return self.participant_id.removeprefix("actor:")

    def to_dict(self) -> dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_alias": self.model_alias,
            "provider": self.provider,
            "reasoning_configuration": self.reasoning_configuration,
        }


@dataclass(frozen=True)
class EnvelopeConfig:
    envelope_id: str
    pipeline_relative: Path
    check_id: str
    canonical_issue_class: str
    candidate_by_role: dict[str, str]
    task_by_role: dict[str, str]
    role_constraints: dict[str, list[str]]
    common_task: str
    authors: dict[str, ModelParticipant]
    author_roles: dict[str, list[str]]
    reviewer: ModelParticipant
    escalation_reviewer: ModelParticipant
    review_instructions: str
    cli_binary: Path
    cli_binary_version: str
    calibration_suite: str
    adr_references: list[str] = field(
        default_factory=lambda: [
            "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md",
            "ADR-0068-QUALIFICATION-PROCESS-CONSOLIDATION.md",
            "ADR-0069-OPERATIONS-BASED-DETECTION-AND-EXECUTABLE-CASES.md",
        ]
    )

    @property
    def roles(self) -> list[str]:
        return sorted({role for roles in self.author_roles.values() for role in roles})


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _write_canonical(path: Path, value: dict[str, Any]) -> None:
    atomic_write_bytes(path, (canonical_json(value) + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# Envelope manifest: the ADR-0068 digest chain.


def _manifest_path(project_root: Path, config: EnvelopeConfig) -> Path:
    return project_root / config.pipeline_relative / MANIFEST_NAME


def _manifest_read(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    path = _manifest_path(project_root, config)
    if not path.exists():
        return {
            "artifact_kind": "lean_pipeline_manifest",
            "manifest_version": "1.0.0",
            "envelope_id": config.envelope_id,
            "steps": {},
        }
    manifest = _load(path)
    if manifest.get("envelope_id") != config.envelope_id:
        raise LeanPipelineError("The envelope manifest belongs to another envelope.")
    return manifest


def _manifest_record(
    project_root: Path,
    config: EnvelopeConfig,
    step: str,
    *,
    digest: str,
    relative_path: str,
) -> None:
    manifest = _manifest_read(project_root, config)
    if step in manifest["steps"]:
        raise LeanPipelineError(f"Pipeline step {step!r} is already recorded.")
    manifest["steps"][step] = {
        "digest": digest,
        "relative_path": relative_path,
        "completed_at": _now(),
    }
    _write_canonical(_manifest_path(project_root, config), manifest)


def _manifest_require(
    project_root: Path, config: EnvelopeConfig, step: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _manifest_read(project_root, config)
    entry = manifest["steps"].get(step)
    if entry is None:
        raise LeanPipelineError(f"Pipeline step {step!r} has not completed.")
    artifact = _load(project_root / config.pipeline_relative / str(entry["relative_path"]))
    digest_field = next(
        (name for name in ("ledger_digest", "protocol_digest") if name in artifact), None
    )
    if digest_field is None:
        raise LeanPipelineError(f"Step artifact for {step!r} carries no digest field.")
    supplied = artifact.pop(digest_field)
    if supplied != entry["digest"] or supplied != semantic_digest(artifact):
        raise LeanPipelineError(f"Step artifact for {step!r} does not replay.")
    artifact[digest_field] = supplied
    return entry, artifact


# ---------------------------------------------------------------------------
# Calibration registry: reuse until the bound configuration changes.


def calibration_key(model_id: str, binary_version: str, suite: str) -> str:
    return f"{model_id}|{binary_version}|{suite}"


def ensure_calibrations(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    registry_path = project_root / CALIBRATION_REGISTRY_RELATIVE
    if not registry_path.exists():
        raise LeanPipelineError(
            "The calibration registry does not exist; seed it from the retained "
            "calibration ledgers before running the pipeline."
        )
    registry = _load(registry_path)
    entries = {str(item["key"]): item for item in registry.get("entries", [])}
    resolved: dict[str, Any] = {}
    for participant in (config.reviewer, config.escalation_reviewer):
        key = calibration_key(
            participant.model_id, config.cli_binary_version, config.calibration_suite
        )
        entry = entries.get(key)
        if entry is None or entry.get("passed") is not True:
            raise LeanPipelineError(
                f"No passing calibration entry for {key!r}; run the calibration "
                "suite once for this configuration and record it in the registry."
            )
        resolved[participant.participant_id] = entry
    return resolved


# ---------------------------------------------------------------------------
# CLI transport with served-model post-verification.


def _call_cli(
    config: EnvelopeConfig,
    participant: ModelParticipant,
    prompt: str,
    session_id: str,
    capture_root: Path,
) -> dict[str, Any]:
    retained = _retained_call(participant, prompt, session_id, capture_root)
    if retained is not None:
        return retained
    capture_root.mkdir(parents=True, exist_ok=True)
    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-lean-cli-") as temporary:
        argv = [
            str(config.cli_binary),
            "--safe-mode",
            "--print",
            "--model",
            participant.model_alias,
            "--effort",
            participant.reasoning_configuration,
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--permission-mode",
            "dontAsk",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--session-id",
            session_id,
            prompt,
        ]
        completed = subprocess.run(
            argv,
            cwd=temporary,
            env=environment,
            capture_output=True,
            check=False,
            timeout=CLI_TIMEOUT_SECONDS,
        )
    completed_at = _now()
    atomic_write_bytes(capture_root / "stdout.bin", completed.stdout)
    atomic_write_bytes(capture_root / "stderr.bin", completed.stderr)
    transport_error = None
    raw_response = ""
    metadata: dict[str, Any] = {}
    if completed.returncode != 0:
        transport_error = f"provider_cli_exit_code:{completed.returncode}"
    else:
        try:
            envelope = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            envelope = {}
            transport_error = f"envelope_parse:{type(error).__name__}"
        if transport_error is None:
            metadata = {
                "reported_session_id": envelope.get("session_id"),
                "served_model_ids": sorted(set(envelope.get("modelUsage", {}))),
            }
            if envelope.get("is_error") is not False:
                transport_error = "provider_reported_error"
            elif envelope.get("session_id") != session_id:
                transport_error = "reported_session_id_mismatch"
            elif participant.model_id not in set(envelope.get("modelUsage", {})):
                transport_error = "served_model_mismatch"
            else:
                text = envelope.get("result")
                if isinstance(text, str) and text.strip():
                    raw_response = text
                else:
                    transport_error = "missing_result_text"
    process_record = {
        "artifact_kind": "lean_pipeline_cli_process_capture",
        "capture_version": "1.0.0",
        "participant_id": participant.participant_id,
        "session_id": session_id,
        "argv_digest": semantic_digest(argv),
        "prompt_digest": sha256_digest(prompt),
        "return_code": completed.returncode,
        "transport_error": transport_error,
        "reported_session_id": metadata.get("reported_session_id"),
        "served_model_ids": metadata.get("served_model_ids"),
        "stdout_digest": sha256_digest(completed.stdout),
        "stderr_digest": sha256_digest(completed.stderr),
        "started_at": started_at,
        "completed_at": completed_at,
        "project_code_executed": False,
        "qualification_authority": "none_process_capture_only",
    }
    process_record["capture_digest"] = semantic_digest(process_record)
    write_normalized_json_once(capture_root / "capture.json", process_record)
    return {
        "raw_response": raw_response,
        "transport_error": transport_error,
        "process_record": process_record,
        "started_at": started_at,
        "completed_at": completed_at,
    }


def _retained_call(
    participant: ModelParticipant,
    prompt: str,
    session_id: str,
    capture_root: Path,
) -> dict[str, Any] | None:
    """Reuse a retained one-shot response when its capture already exists.

    Projection and recording are deterministic post-processing; re-running
    them against the retained bytes is not a second model attempt. The
    retained capture must bind the exact same prompt and session identity
    and must have completed cleanly, or it cannot be reused.
    """

    capture_path = capture_root / "capture.json"
    if not capture_path.exists():
        return None
    record = _load(capture_path)
    if (
        record.get("participant_id") != participant.participant_id
        or record.get("session_id") != session_id
        or record.get("prompt_digest") != sha256_digest(prompt)
        or record.get("transport_error") is not None
    ):
        raise LeanPipelineError("A retained call capture exists but does not bind this exact call.")
    stdout = (capture_root / "stdout.bin").read_bytes()
    if sha256_digest(stdout) != record.get("stdout_digest"):
        raise LeanPipelineError("A retained call capture's bytes drifted.")
    envelope = json.loads(stdout.decode("utf-8"))
    return {
        "raw_response": str(envelope.get("result")),
        "transport_error": None,
        "process_record": record,
        "started_at": record["started_at"],
        "completed_at": record["completed_at"],
    }


# ---------------------------------------------------------------------------
# Step 1: blind authoring of executable workflows.


def _author_output_schema(participant_id: str, case_ids: list[str]) -> dict[str, Any]:
    case_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "case_id",
            "input_csv",
            "analysis_py",
            "report_md",
            "selected_result_line",
        ],
        "properties": {
            "case_id": {"type": "string", "enum": case_ids},
            "input_csv": {"type": "string", "minLength": 1},
            "analysis_py": {"type": "string", "minLength": 1},
            "report_md": {"type": "string", "minLength": 1},
            "selected_result_line": {"type": "integer", "minimum": 1},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["participant_id", "cases"],
        "properties": {
            "participant_id": {"type": "string", "const": participant_id},
            "cases": {
                "type": "array",
                "minItems": len(case_ids),
                "maxItems": len(case_ids),
                "items": case_schema,
            },
        },
    }


_AUTHOR_INSTRUCTIONS = """You are one blind scientific case author running non-interactively.
You have no tools, no filesystem, no shell, and no execution environment; do not attempt to
run, test, or verify anything externally, and do not narrate tool use. Construct the files in
your head, check the arithmetic mentally, and reply with exactly one JSON object and nothing
else: no prose before or after it, no markdown fences, no tool-call blocks.

Author every assigned case as a small, real, runnable analysis workflow. For each case you
produce exactly three files.

inputs/data.csv: an ASCII CSV with a header row and one data row per planned observation unit,
containing the complete planned-unit accounting including the units the screening step removes.

workflow/analysis.py: a deterministic Python script using only the standard library modules
csv, math, statistics, pathlib, collections, fractions, decimal, itertools, functools, json,
and re. It must read inputs/data.csv, compute every count and the rate it reports from that
data (never hard-code a result number), and write results/report.md. No randomness, no clock,
no network, no other files, no command-line arguments. The intake pipeline (not you) will later
execute it twice from the case root with `python -I workflow/analysis.py`; both runs must
produce byte-identical output, and the report_md you return must equal that output exactly,
byte for byte, so compute every reported number with exact care.

results/report.md: an ASCII Markdown report whose lines exactly equal the script output. It
must contain exactly one line beginning with `[selected-result]` stating the single selected
result, and it must state the complete accounting in numbers: the planned unit count, the
retained count after screening, the removed count, and the event count.

Keep every number internally consistent with the CSV. Report selected_result_line as the
1-based line number of the `[selected-result]` line inside report_md.

{task}

Case assignments:
{assignments}

Return only one unfenced JSON object matching this exact schema:
{schema}
"""


def step_authoring(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    output_root = root / "authoring"
    if output_root.exists():
        raise LeanPipelineError("The authoring step already has output.")
    ensure_calibrations(project_root, config)
    registry = _load(
        project_root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
    )
    module = next(item for item in registry["modules"] if item["check_id"] == config.check_id)
    binding = next(
        item for item in registry["method_conflict_bindings"] if item["check_id"] == config.check_id
    )
    detector_tuple = {
        "check_id": config.check_id,
        "check_version": module["check_version"],
        "check_manifest_digest": module["manifest_digest"],
        "adapters": module["adapters"],
        "method_conflict_binding_digest": semantic_digest(binding),
        "registry_content_digest": sha256_digest(
            (
                project_root
                / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
            ).read_bytes()
        ),
        "production_finding_permitted": False,
    }
    tuple_digest = semantic_digest(detector_tuple)

    case_ids = {
        role: stable_id("case", config.envelope_id, "lean-pipeline", role, tuple_digest)
        for role in config.roles
    }
    role_by_case = {case_id: role for role, case_id in case_ids.items()}

    assignments: list[dict[str, Any]] = []
    for participant_id in sorted(config.authors):
        participant = config.authors[participant_id]
        roles = config.author_roles[participant_id]
        assigned = sorted(case_ids[role] for role in roles)
        brief_lines = []
        for case_id in assigned:
            constraints = "\n".join(
                f"  - {line}" for line in config.role_constraints[role_by_case[case_id]]
            )
            brief_lines.append(f"- case_id {case_id}:\n{constraints}")
        schema = _author_output_schema(participant_id, assigned)
        prompt = _AUTHOR_INSTRUCTIONS.format(
            task=config.common_task,
            assignments="\n".join(brief_lines),
            schema=canonical_json(schema),
        )
        assignments.append(
            {
                "participant": participant.to_dict(),
                "case_ids": assigned,
                "prompt": prompt,
                "prompt_digest": sha256_digest(prompt),
                "output_schema": schema,
                "output_schema_digest": semantic_digest(schema),
                "call_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee:lean-pipeline-authoring:{config.envelope_id}:"
                        f"{participant_id}:{tuple_digest}",
                    )
                ),
            }
        )

    protocol: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_authoring_protocol",
        "protocol_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "adr_references": config.adr_references,
        "detector_tuple": detector_tuple,
        "detector_tuple_digest": tuple_digest,
        "case_role_assignments": {
            case_id: role_by_case[case_id] for case_id in sorted(role_by_case)
        },
        "author_assignments": assignments,
        "execution_policy": {
            "one_attempt_per_author_context": True,
            "all_attempts_retained": True,
            "executable_workflow_required": True,
            "sandbox_ground_truth_execution_required": True,
        },
        "frozen_at": _now(),
        "qualification_authority": "none_authoring_protocol_only",
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    output_root.mkdir(parents=True)
    write_normalized_json_once(output_root / "AUTHORING_PROTOCOL.json", protocol)

    def _run(assignment: dict[str, Any]) -> dict[str, Any]:
        participant = config.authors[str(assignment["participant"]["participant_id"])]
        return {
            "assignment": assignment,
            "call": _call_cli(
                config,
                participant,
                str(assignment["prompt"]),
                str(assignment["call_identity_id"]),
                output_root / "process-captures" / participant.slug,
            ),
        }

    with ThreadPoolExecutor(max_workers=len(assignments)) as executor:
        results = list(executor.map(_run, assignments))
    failures = [
        f"{result['assignment']['participant']['participant_id']}:"
        f"{result['call']['transport_error']}"
        for result in results
        if result["call"]["transport_error"] is not None
    ]
    for result in results:
        slug = str(result["assignment"]["participant"]["participant_id"]).removeprefix("actor:")
        attempt = {
            "participant_id": result["assignment"]["participant"]["participant_id"],
            "call_identity_id": result["assignment"]["call_identity_id"],
            "protocol_digest": protocol["protocol_digest"],
            "prompt_digest": result["assignment"]["prompt_digest"],
            "transport_error": result["call"]["transport_error"],
            "raw_response": result["call"]["raw_response"],
            "started_at": result["call"]["started_at"],
            "completed_at": result["call"]["completed_at"],
            "process_capture_digest": result["call"]["process_record"]["capture_digest"],
        }
        write_normalized_json_once(output_root / "incoming" / f"{slug}.json", attempt)
    if failures:
        raise LeanPipelineError(
            "Author calls failed and were retained: " + ", ".join(sorted(failures))
        )
    _manifest_record(
        project_root,
        config,
        "authoring",
        digest=protocol["protocol_digest"],
        relative_path="authoring/AUTHORING_PROTOCOL.json",
    )
    return protocol


# ---------------------------------------------------------------------------
# Step 2: intake with sandboxed ground-truth execution.


def _strip_single_fence(text: str) -> str:
    """Mechanical transport normalization: unwrap one whole-body markdown fence."""

    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        body = stripped[3:-3]
        first_newline = body.find("\n")
        if first_newline != -1 and body[:first_newline].strip().isalpha():
            body = body[first_newline + 1 :]
        return body.strip()
    return stripped


def _static_guard(source: str) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise LeanPipelineError(f"Authored workflow does not parse: {error}") from error
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in _ALLOWED_IMPORT_ROOTS:
                    raise LeanPipelineError(
                        f"Authored workflow imports a forbidden module: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            root_name = (node.module or "").split(".")[0]
            if node.level or root_name not in _ALLOWED_IMPORT_ROOTS:
                raise LeanPipelineError(
                    f"Authored workflow imports a forbidden module: {node.module}"
                )
        elif isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise LeanPipelineError(f"Authored workflow uses a forbidden builtin: {node.id}")


def _sandbox_run(case_root: Path) -> bytes:
    """Execute the authored workflow once in an isolated copy; return report bytes."""

    with tempfile.TemporaryDirectory(prefix="sc-referee-lean-sandbox-") as temporary:
        sandbox = Path(temporary) / "case"
        shutil.copytree(case_root, sandbox)
        before = {
            path.relative_to(sandbox).as_posix(): sha256_digest(path.read_bytes())
            for path in sandbox.rglob("*")
            if path.is_file()
        }
        completed = subprocess.run(
            [sys.executable, "-I", "workflow/analysis.py"],
            cwd=sandbox,
            env={"NO_COLOR": "1"},
            capture_output=True,
            check=False,
            timeout=SANDBOX_TIMEOUT_SECONDS,
        )
        if completed.returncode != 0:
            raise LeanPipelineError(
                "Authored workflow failed in the sandbox: "
                + completed.stderr.decode("utf-8", "replace")[:500]
            )
        after = {
            path.relative_to(sandbox).as_posix(): sha256_digest(path.read_bytes())
            for path in sandbox.rglob("*")
            if path.is_file()
        }
        changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
        if changed - {"results/report.md"}:
            raise LeanPipelineError(
                f"Authored workflow touched files beyond the report: {sorted(changed)}"
            )
        report = sandbox / "results/report.md"
        if not report.is_file():
            raise LeanPipelineError("Authored workflow produced no report.")
        return report.read_bytes()


def step_intake(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    output_root = root / "authoring"
    _entry, protocol = _manifest_require(project_root, config, "authoring")
    if (root / "authoring" / "INTAKE_LEDGER.json").exists():
        raise LeanPipelineError("The intake step already has output.")
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    rows: list[dict[str, Any]] = []
    for assignment in protocol["author_assignments"]:
        participant_id = str(assignment["participant"]["participant_id"])
        slug = participant_id.removeprefix("actor:")
        attempt = _load(output_root / "incoming" / f"{slug}.json")
        if attempt["protocol_digest"] != protocol["protocol_digest"]:
            raise LeanPipelineError("An author attempt is outside the frozen protocol.")
        try:
            payload = json.loads(_strip_single_fence(str(attempt["raw_response"])))
        except json.JSONDecodeError as error:
            raise LeanPipelineError(
                f"An author response is not valid JSON: {participant_id}"
            ) from error
        try:
            jsonschema.validate(payload, assignment["output_schema"])
        except jsonschema.ValidationError as error:
            raise LeanPipelineError(
                f"An author response fails its frozen schema: {error.message}"
            ) from error
        cases = payload["cases"]
        returned_ids = sorted(str(item["case_id"]) for item in cases)
        if returned_ids != sorted(str(v) for v in assignment["case_ids"]):
            raise LeanPipelineError("An author response covers the wrong case ids.")
        for item in cases:
            case_id = str(item["case_id"])
            input_csv = str(item["input_csv"])
            analysis_py = str(item["analysis_py"])
            report_md = str(item["report_md"])
            for name, payload_text, limit in (
                ("inputs/data.csv", input_csv, MAX_INPUT_BYTES),
                ("workflow/analysis.py", analysis_py, MAX_PRODUCER_BYTES),
                ("results/report.md", report_md, MAX_REPORT_BYTES),
            ):
                encoded = payload_text.encode("utf-8")
                if len(encoded) > limit:
                    raise LeanPipelineError(f"Authored file {name} exceeds its size bound.")
                if not payload_text.isascii():
                    raise LeanPipelineError(f"Authored file {name} is not ASCII.")
            _static_guard(analysis_py)
            marker_lines = [
                index + 1
                for index, line in enumerate(report_md.splitlines())
                if line.startswith(SELECTED_RESULT_MARKER)
            ]
            if len(marker_lines) != 1:
                raise LeanPipelineError(
                    f"Case {case_id} does not contain exactly one selected-result line."
                )
            if marker_lines[0] != int(item["selected_result_line"]):
                raise LeanPipelineError(f"Case {case_id} misdeclares its selected-result line.")
            case_root = output_root / "cases" / case_id.removeprefix("case:")
            (case_root / "inputs").mkdir(parents=True)
            (case_root / "workflow").mkdir(parents=True)
            (case_root / "results").mkdir(parents=True)
            (case_root / "inputs/data.csv").write_bytes(input_csv.encode("utf-8"))
            (case_root / "workflow/analysis.py").write_bytes(analysis_py.encode("utf-8"))
            (case_root / "results/report.md").write_bytes(report_md.encode("utf-8"))
            first = _sandbox_run(case_root)
            second = _sandbox_run(case_root)
            if first != second:
                raise LeanPipelineError(f"Case {case_id} is not deterministic.")
            if first != report_md.encode("utf-8"):
                raise LeanPipelineError(
                    f"Case {case_id} report does not equal its executed output."
                )
            rows.append(
                {
                    "case_id": case_id,
                    "case_role": roles[case_id],
                    "author_participant_id": participant_id,
                    "selected_result_line": marker_lines[0],
                    "file_digests": {
                        "inputs/data.csv": sha256_digest(input_csv.encode("utf-8")),
                        "workflow/analysis.py": sha256_digest(analysis_py.encode("utf-8")),
                        "results/report.md": sha256_digest(report_md.encode("utf-8")),
                    },
                    "sandbox_runs": 2,
                    "sandbox_report_digest": sha256_digest(first),
                    "deterministic": True,
                }
            )
    if sorted(row["case_id"] for row in rows) != sorted(roles):
        raise LeanPipelineError("Intake did not admit the exact authored case set.")
    ledger: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_intake_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "authoring_protocol_digest": protocol["protocol_digest"],
        "entries": sorted(rows, key=lambda row: str(row["case_id"])),
        "case_count": len(rows),
        "ground_truth_execution": {
            "executed": True,
            "scope": "qualification_sandbox_of_program_commissioned_code_only",
            "runs_per_case": 2,
            "timeout_seconds": SANDBOX_TIMEOUT_SECONDS,
            "production_audit_execution": False,
        },
        "recorded_at": _now(),
        "qualification_authority": "none_intake_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(output_root / "INTAKE_LEDGER.json", ledger)
    _manifest_record(
        project_root,
        config,
        "intake",
        digest=ledger["ledger_digest"],
        relative_path="authoring/INTAKE_LEDGER.json",
    )
    return ledger


# ---------------------------------------------------------------------------
# Step 3: single blind merged review with escalation.


def _anchor_span(span: dict[str, Any], lines: list[str]) -> None:
    """Deterministically anchor one quoted span to true file bytes.

    The model's quote is a locator, never authority: the recorded evidence
    always equals exact complete lines of the visible file. Resolution order:
    exact match at the claimed lines; a quote that is an exact substring of
    the claimed lines widens to those complete lines; a unique exact
    consecutive-line match elsewhere rebinds the line numbers; a unique
    whitespace-normalized consecutive-line match rebinds and requotes. A
    span that resolves none of these ways is left untouched so the frozen
    projector fails closed on it.
    """

    start = int(span.get("start_line", 0))
    end = int(span.get("end_line", 0))
    quoted = str(span.get("quoted_text", ""))
    if not (1 <= start <= end <= len(lines)):
        claimed = None
    else:
        claimed = "\n".join(lines[start - 1 : end])
    if claimed is not None and quoted == claimed:
        return
    if claimed is not None and quoted and quoted in claimed:
        span["quoted_text"] = claimed
        return
    quote_lines = quoted.splitlines()
    if quote_lines:
        exact_hits = [
            i + 1
            for i in range(len(lines) - len(quote_lines) + 1)
            if lines[i : i + len(quote_lines)] == quote_lines
        ]
        if len(exact_hits) == 1:
            span["start_line"] = exact_hits[0]
            span["end_line"] = exact_hits[0] + len(quote_lines) - 1
            return
        normalized_quote = [line.strip() for line in quote_lines]
        normalized_lines = [line.strip() for line in lines]
        normalized_hits = [
            i + 1
            for i in range(len(normalized_lines) - len(normalized_quote) + 1)
            if normalized_lines[i : i + len(normalized_quote)] == normalized_quote
        ]
        if len(normalized_hits) == 1:
            first = normalized_hits[0]
            span["start_line"] = first
            span["end_line"] = first + len(quote_lines) - 1
            span["quoted_text"] = "\n".join(lines[first - 1 : first + len(quote_lines) - 1])
            return


def _anchor_review_spans(
    payload: dict[str, Any], workspace_payloads: dict[str, dict[str, bytes]]
) -> dict[str, Any]:
    """Anchor every quoted source span in a review response to true bytes."""

    anchored = json.loads(json.dumps(payload))
    for review in anchored.get("reviews", []):
        case_id = str(review.get("case_id", ""))
        payloads = workspace_payloads.get(case_id, {})
        lines_by_path = {
            path: content.decode("utf-8", "replace").splitlines()
            for path, content in payloads.items()
        }

        def _walk(node: Any, table: dict[str, list[str]]) -> None:
            if isinstance(node, dict):
                if {"path", "start_line", "end_line", "quoted_text"} <= set(node):
                    lines = table.get(str(node["path"]))
                    if lines is not None:
                        _anchor_span(node, lines)
                else:
                    for value in node.values():
                        _walk(value, table)
            elif isinstance(node, list):
                for value in node:
                    _walk(value, table)

        _walk(review, lines_by_path)
    return anchored


def _reviewer_agent(config: EnvelopeConfig, participant: ModelParticipant) -> dict[str, Any]:
    """The complete replay-identity record for one CLI reviewer configuration."""

    return {
        "provider": participant.provider,
        "agent_surface": "Claude Code CLI",
        "model_name": participant.model_name,
        "model_id": participant.model_id,
        "agent_version": config.cli_binary_version,
        "reasoning_configuration": participant.reasoning_configuration,
        "execution_context_id": f"context:{participant.slug}-v1",
        "independent_context": True,
        "system_prompt_digest": sha256_digest(
            canonical_json({"system_prompt": None}).encode("utf-8")
        ),
        "tool_policy_digest": sha256_digest(
            canonical_json(
                {
                    "mcp_set": "empty_mcpServers_record_strict",
                    "permission_mode": "dontAsk",
                    "safe_mode": True,
                    "tool_set": "empty",
                }
            ).encode("utf-8")
        ),
        "environment_digest": sha256_digest(
            canonical_json({"NO_COLOR": "1", "session_persistence": False}).encode("utf-8")
        ),
    }


def _prepare_blind_case(
    project_root: Path,
    config: EnvelopeConfig,
    review_root: Path,
    case_id: str,
    role: str,
    intake_row: dict[str, Any],
) -> dict[str, Any]:
    slug = case_id.removeprefix("case:")
    case_root = project_root / config.pipeline_relative / "authoring" / "cases" / slug
    preparation_root = review_root / "case-preparations" / slug
    runner_source = preparation_root / "runner-source"
    runner_source.mkdir(parents=True)
    task_payload = (config.task_by_role[role].rstrip() + "\n").encode("utf-8")
    atomic_write_bytes(runner_source / "task.md", task_payload)
    for path_value, digest in sorted(dict(intake_row["file_digests"]).items()):
        payload = (case_root / path_value).read_bytes()
        if sha256_digest(payload) != digest:
            raise LeanPipelineError(f"Admitted case bytes drifted for {case_id}.")
        destination = runner_source / path_value
        destination.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(destination, payload)
    snapshot_at = _now()
    budget = sum(path.stat().st_size for path in runner_source.rglob("*") if path.is_file())
    captured = capture_repository(
        runner_source,
        preparation_root / "snapshot",
        f"lean-pipeline-review:{case_id}",
        captured_at=snapshot_at,
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=budget,
            sampled_fingerprint_byte_budget=0,
        ),
    )
    file_records = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        snapshot_at,
    )
    write_normalized_json(preparation_root / "snapshot.json", captured.snapshot_record)
    atomic_write_bytes(
        preparation_root / "file-records.jsonl",
        b"".join(normalized_json_bytes(record) for record in file_records),
    )
    forbidden_markers = {
        config.canonical_issue_class,
        config.check_id,
        config.envelope_id,
        "error-bearing",
        "error_bearing",
        "corrected_twin",
        "corrected-twin",
        "valid_alternative",
        "valid-alternative",
    }
    workspace_manifest = build_blind_workspace(
        runner_source,
        preparation_root / "blind-workspace",
        preparation_root / "blind-workspace-manifest.json",
        [dict(item) for item in VISIBLE_FILES],
        snapshot=captured.snapshot_record,
        file_records=file_records,
        asset_identities=captured.asset_identity_records,
        created_at=_now(),
        forbidden_markers=forbidden_markers,
    )
    return {
        "case_id": case_id,
        "workspace_manifest": workspace_manifest,
        "workspace_relative": (preparation_root / "blind-workspace")
        .relative_to(review_root)
        .as_posix(),
    }


def _review_prompt(
    config: EnvelopeConfig,
    participant: ModelParticipant,
    case_order: list[str],
    workspace_payloads: dict[str, dict[str, bytes]],
    schema: dict[str, Any],
) -> str:
    sections = []
    for index, case_id in enumerate(case_order, start=1):
        file_sections = "\n".join(
            f"--- file {item['path']} ---\n"
            + workspace_payloads[case_id][str(item["path"])].decode("utf-8")
            for item in VISIBLE_FILES
        )
        sections.append(f"=== workflow {index}: {case_id} ===\n{file_sections}")
    return (
        config.review_instructions.format(issue_class=config.canonical_issue_class)
        + f"\n\nReviewer participant identity: {participant.participant_id}\n\n"
        + "\n\n".join(sections)
        + "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
    ).strip()


def _run_review_call(
    project_root: Path,
    config: EnvelopeConfig,
    review_root: Path,
    participant: ModelParticipant,
    case_subset: list[str],
    preparations_by_case: dict[str, dict[str, Any]],
    workspace_payloads: dict[str, dict[str, bytes]],
    tuple_digest: str,
    label: str,
) -> dict[str, Any]:
    """One frozen blind batched review call: packets, transport, projection, captures."""

    schema = build_stage1_batch_output_schema_v2(
        participant.participant_id, case_subset, config.canonical_issue_class
    )
    prompt = _review_prompt(config, participant, case_subset, workspace_payloads, schema)
    reviewer_agent = _reviewer_agent(config, participant)
    packets: dict[str, dict[str, Any]] = {}
    for case_id in case_subset:
        packet_path = review_root / f"packets-{label}" / f"{case_id.removeprefix('case:')}.json"
        packet = None
        if packet_path.exists():
            candidate = _load(packet_path)
            supplied = candidate.pop("packet_digest", None)
            if supplied != semantic_digest(candidate):
                raise LeanPipelineError("A retained review packet does not replay.")
            candidate["packet_digest"] = supplied
            expected = candidate.get("expected_reviewer_agent", {})
            if (
                candidate.get("case_id") == case_id
                and expected.get("execution_context_id") == reviewer_agent["execution_context_id"]
            ):
                packet = candidate
            else:
                # A retained packet from a retired reviewer attempt: move it
                # aside as evidence and rebuild for the current participant.
                retired_root = review_root / f"packets-{label}-retired"
                retired_root.mkdir(exist_ok=True)
                packet_path.rename(retired_root / packet_path.name)
        if packet is None:
            packet = build_stage1_review_packet(
                case_id,
                preparations_by_case[case_id]["workspace_manifest"],
                reviewer_agent,
                prompt,
                created_at=_now(),
            )
            write_normalized_json_once(packet_path, packet)
        packets[case_id] = packet
    call_identity = str(
        uuid5(
            NAMESPACE_URL,
            f"sc-referee:lean-pipeline-review:{config.envelope_id}:{label}:"
            f"{participant.participant_id}:{tuple_digest}",
        )
    )
    atomic_write_bytes(review_root / f"prompt-{label}.txt", prompt.encode("utf-8"))
    call = _call_cli(
        config,
        participant,
        prompt,
        call_identity,
        review_root / "process-captures" / f"{label}-{participant.slug}",
    )
    if call["transport_error"] is not None:
        raise LeanPipelineError(
            f"The {label} review call failed and was retained: {call['transport_error']}"
        )
    raw_response = str(call["raw_response"]).encode("utf-8")
    anchored_payload = _anchor_review_spans(json.loads(raw_response), workspace_payloads)
    reviews = project_stage1_semantic_batch_v2(
        anchored_payload,
        output_schema=schema,
        participant_id=participant.participant_id,
        participant_reviewer_agent=reviewer_agent,
        packets_by_case=packets,
        workspace_payloads_by_case=workspace_payloads,
        canonical_issue_class=config.canonical_issue_class,
        transcript=raw_response,
        completed_at=str(call["completed_at"]),
        schema_root=project_root / SCHEMA_RELATIVE,
    )
    entries = []
    with tempfile.TemporaryDirectory(prefix="sc-referee-lean-review-") as temporary:
        transcript_path = Path(temporary) / "transcript.bin"
        transcript_path.write_bytes(raw_response)
        for review in reviews:
            case_id = str(review["case_id"])
            destination = review_root / f"captures-{label}" / case_id.removeprefix("case:")
            manifest = capture_review_submission(
                review,
                packets[case_id],
                transcript_path,
                project_root / SCHEMA_RELATIVE,
                captured_at=_now(),
                destination=destination,
            )
            load_review_capture(destination, project_root / SCHEMA_RELATIVE)
            entries.append(
                {
                    "case_id": case_id,
                    "review_role": label,
                    "participant_id": participant.participant_id,
                    "review_id": review["review_id"],
                    "review_digest": semantic_digest(review),
                    "packet_digest": packets[case_id]["packet_digest"],
                    "capture_digest": manifest["capture_digest"],
                    "verdict": review["verdict"],
                    "issue_class": review.get("issue_class"),
                    "unresolved_material_question_count": len(
                        review.get("unresolved_material_questions") or []
                    ),
                }
            )
    return {
        "entries": sorted(entries, key=lambda item: str(item["case_id"])),
        "call_identity_id": call_identity,
        "prompt_digest": sha256_digest(prompt),
        "output_schema_digest": semantic_digest(schema),
        "shared_transcript_digest": sha256_digest(raw_response),
        "packet_digests": {case_id: packets[case_id]["packet_digest"] for case_id in case_subset},
    }


def _entry_clean(config: EnvelopeConfig, entry: dict[str, Any], role: str) -> bool:
    expected = EXPECTED_VERDICT_BY_ROLE[role]
    issue_clean = (
        entry["issue_class"] == config.canonical_issue_class
        if entry["verdict"] == "demonstrated_issue"
        else entry["issue_class"] is None
    )
    return bool(
        entry["verdict"] == expected
        and issue_clean
        and entry["unresolved_material_question_count"] == 0
    )


def step_review(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    review_root = root / "review"
    if (review_root / "REVIEW_LEDGER.json").exists():
        raise LeanPipelineError("The review step already has output.")
    if review_root.exists():
        # A prior run crashed after its call: keep the retained process
        # captures (the one-shot evidence) and rebuild the deterministic
        # remainder from the admitted cases.
        for child in review_root.iterdir():
            keep = child.name == "process-captures" or child.name.startswith(
                ("packets-", "prompt-")
            )
            if not keep:
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    calibrations = ensure_calibrations(project_root, config)
    _auth_entry, protocol = _manifest_require(project_root, config, "authoring")
    _intake_entry, intake = _manifest_require(project_root, config, "intake")
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    intake_rows = {str(row["case_id"]): row for row in intake["entries"]}
    review_root.mkdir(parents=True, exist_ok=True)

    preparations = [
        _prepare_blind_case(
            project_root, config, review_root, case_id, roles[case_id], intake_rows[case_id]
        )
        for case_id in sorted(roles)
    ]
    case_order = [str(item["case_id"]) for item in preparations]
    workspace_payloads: dict[str, dict[str, bytes]] = {}
    for item in preparations:
        case_id = str(item["case_id"])
        workspace_root = review_root / str(item["workspace_relative"])
        workspace_payloads[case_id] = {
            str(entry["path"]): (workspace_root / str(entry["path"])).read_bytes()
            for entry in VISIBLE_FILES
        }

    preparations_by_case = {str(item["case_id"]): item for item in preparations}
    review_protocol: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_review_protocol",
        "protocol_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "adr_references": config.adr_references,
        "authoring_protocol_digest": protocol["protocol_digest"],
        "intake_ledger_digest": intake["ledger_digest"],
        "reviewer": config.reviewer.to_dict(),
        "escalation_reviewer": config.escalation_reviewer.to_dict(),
        "reviewer_calibration_keys": {
            participant_id: entry["key"] for participant_id, entry in calibrations.items()
        },
        "case_order": case_order,
        "escalation_policy": (
            "One merged blind review per case; a second blind review from the "
            "escalation reviewer runs only for non-clean cases per ADR-0067, and a "
            "case whose two reviews genuinely disagree is retained as unresolved."
        ),
        "frozen_at": _now(),
        "qualification_authority": "none_review_protocol_only",
    }
    review_protocol["protocol_digest"] = semantic_digest(review_protocol)
    write_normalized_json_once(review_root / "REVIEW_PROTOCOL.json", review_protocol)

    primary = _run_review_call(
        project_root,
        config,
        review_root,
        config.reviewer,
        case_order,
        preparations_by_case,
        workspace_payloads,
        str(protocol["detector_tuple_digest"]),
        "primary",
    )
    primary_by_case = {str(entry["case_id"]): entry for entry in primary["entries"]}
    non_clean = sorted(
        case_id
        for case_id, entry in primary_by_case.items()
        if not _entry_clean(config, entry, roles[case_id])
    )
    escalation: dict[str, Any] | None = None
    if non_clean:
        escalation = _run_review_call(
            project_root,
            config,
            review_root,
            config.escalation_reviewer,
            non_clean,
            preparations_by_case,
            workspace_payloads,
            str(protocol["detector_tuple_digest"]),
            "escalation",
        )
    escalation_by_case = {
        str(entry["case_id"]): entry for entry in (escalation or {}).get("entries", [])
    }
    unblinding = []
    unresolved: list[str] = []
    for case_id in case_order:
        role = roles[case_id]
        primary_entry = primary_by_case[case_id]
        primary_clean = _entry_clean(config, primary_entry, role)
        escalation_entry = escalation_by_case.get(case_id)
        escalation_clean = (
            _entry_clean(config, escalation_entry, role) if escalation_entry is not None else None
        )
        resolution = (
            "clean"
            if primary_clean
            else "resolved_by_escalation"
            if escalation_clean
            else "unresolved_disagreement_retained"
        )
        if resolution == "unresolved_disagreement_retained":
            unresolved.append(case_id)
        unblinding.append(
            {
                "case_id": case_id,
                "case_role": role,
                "expected_verdict": EXPECTED_VERDICT_BY_ROLE[role],
                "primary_verdict": primary_entry["verdict"],
                "primary_issue_class": primary_entry["issue_class"],
                "primary_clean": primary_clean,
                "escalation_verdict": (
                    escalation_entry["verdict"] if escalation_entry is not None else None
                ),
                "escalation_clean": escalation_clean,
                "resolution": resolution,
            }
        )
    ledger: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_review_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "review_protocol_digest": review_protocol["protocol_digest"],
        "primary_call": {
            key: primary[key]
            for key in (
                "call_identity_id",
                "prompt_digest",
                "output_schema_digest",
                "shared_transcript_digest",
                "packet_digests",
            )
        },
        "escalation_call": (
            {
                key: escalation[key]
                for key in (
                    "call_identity_id",
                    "prompt_digest",
                    "output_schema_digest",
                    "shared_transcript_digest",
                    "packet_digests",
                )
            }
            if escalation is not None
            else None
        ),
        "entries": primary["entries"] + (escalation or {}).get("entries", []),
        "unblinding_record": unblinding,
        "escalation_ran": escalation is not None,
        "unresolved_case_ids": unresolved,
        "recorded_at": _now(),
        "qualification_authority": "none_lean_review_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(review_root / "REVIEW_LEDGER.json", ledger)
    _manifest_record(
        project_root,
        config,
        "review",
        digest=ledger["ledger_digest"],
        relative_path="review/REVIEW_LEDGER.json",
    )
    if unresolved:
        raise LeanPipelineError(
            "Reviews disagree after escalation; these cases are retained as "
            f"unresolved and block labels: {unresolved}"
        )
    return ledger


# ---------------------------------------------------------------------------
# Step 4: lean label freeze (before any detector observation).


def step_labels(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    output_path = root / "SCIENTIFIC_LABEL_LEDGER.json"
    if output_path.exists():
        raise LeanPipelineError("The label step already has output.")
    _auth_entry, protocol = _manifest_require(project_root, config, "authoring")
    _review_entry, review_ledger = _manifest_require(project_root, config, "review")
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    if review_ledger["unresolved_case_ids"]:
        raise LeanPipelineError("Labels cannot freeze while unresolved cases are retained.")
    resolutions = {
        str(row["case_id"]): str(row["resolution"]) for row in review_ledger["unblinding_record"]
    }
    resolving_role = {
        case_id: ("primary" if resolution == "clean" else "escalation")
        for case_id, resolution in resolutions.items()
    }
    family_by_participant = {
        config.reviewer.participant_id: (
            f"{config.reviewer.provider}:{config.reviewer.model_name}"
        ),
        config.escalation_reviewer.participant_id: (
            f"{config.escalation_reviewer.provider}:{config.escalation_reviewer.model_name}"
        ),
    }
    label_rows = []
    for entry in review_ledger["entries"]:
        case_id = str(entry["case_id"])
        if str(entry["review_role"]) != resolving_role[case_id]:
            continue
        role = roles[case_id]
        label_rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "label_status": LABEL_STATUS_BY_ROLE[role],
                "issue_class": (config.canonical_issue_class if role == "error_bearing" else None),
                "review_basis": "single_calibrated_blind_review_adr_0067",
                "review_id": entry["review_id"],
                "review_digest": entry["review_digest"],
                "reviewer_model_family": family_by_participant[str(entry["participant_id"])],
                "agent_only_disclosure": (
                    "Established under ADR-0067 by one calibrated blind reviewer with "
                    "escalation reserved for non-clean results, and under ADR-0066 "
                    "without cross-provider review."
                ),
            }
        )
    if len(label_rows) != len(resolving_role):
        raise LeanPipelineError("The label freeze did not cover every resolved case.")
    ledger: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_scientific_label_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "adr_references": config.adr_references,
        "authoring_protocol_digest": protocol["protocol_digest"],
        "review_ledger_digest": review_ledger["ledger_digest"],
        "canonical_issue_class_scope": config.canonical_issue_class,
        "entries": sorted(label_rows, key=lambda row: str(row["case_id"])),
        "label_count": len(label_rows),
        "detector_output_observed": False,
        "frozen_at": _now(),
        "qualification_authority": "none_scientific_labels_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(output_path, ledger)
    _manifest_record(
        project_root,
        config,
        "labels",
        digest=ledger["ledger_digest"],
        relative_path="SCIENTIFIC_LABEL_LEDGER.json",
    )
    return ledger


# ---------------------------------------------------------------------------
# Step 5: detector run with deterministic replay, then pilot metrics.


def step_detector(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    output_root = root / "detector-run"
    if output_root.exists():
        raise LeanPipelineError("The detector step already has output.")
    _auth_entry, protocol = _manifest_require(project_root, config, "authoring")
    _label_entry, label_ledger = _manifest_require(project_root, config, "labels")
    if label_ledger["detector_output_observed"] is not False:
        raise LeanPipelineError("Labels were not frozen before detector observation.")
    detector_tuple = protocol["detector_tuple"]
    registry_path = (
        project_root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
    )
    if sha256_digest(registry_path.read_bytes()) != detector_tuple["registry_content_digest"]:
        raise LeanPipelineError(
            "The current check registry drifted from the frozen detector tuple."
        )
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    labels_by_case = {str(row["case_id"]): row for row in label_ledger["entries"]}
    schema_root = project_root / SCHEMA_RELATIVE
    output_root.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    for case_id in sorted(roles):
        slug = case_id.removeprefix("case:")
        role = roles[case_id]
        case_source = root / "authoring" / "cases" / slug
        case_root = output_root / "runs" / slug
        repository = case_root / "project"
        shutil.copytree(case_source, repository)
        task_payload = (config.task_by_role[role].rstrip() + "\n").encode("utf-8")
        atomic_write_bytes(repository / "task.md", task_payload)
        contract = run_method_contract(
            repository,
            "task.md",
            case_root / "contract",
            schema_root,
            profile={
                "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
                "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                "check_id": config.check_id,
                "candidate_id": config.candidate_by_role[role],
            },
            actor_id=f"scientist:lean-pipeline-{config.envelope_id}",
        )
        if contract["findings"]:
            raise LeanPipelineError(f"The method-contract step emitted findings for {case_id}.")
        bundle = run_audit(
            repository,
            case_root / "audit",
            schema_root,
            report="results/report.md",
            method_contract_lock=case_root / "contract" / "semantic.lock.json",
        )
        replayed = replay(
            case_root / "audit" / "semantic.lock.json", case_root / "replay", schema_root
        )
        if replayed["detector_results"] != bundle["detector_results"]:
            raise LeanPipelineError(f"The detector run does not replay for {case_id}.")
        fired = [
            result
            for result in bundle.get("detector_results", [])
            if result.get("detector_id") == DETECTOR_ID
            and result.get("state") == "evaluation_finding_candidate"
        ]
        label_status = str(labels_by_case[case_id]["label_status"])
        detector_positive = bool(fired)
        expected_positive = label_status == "positive_demonstrated"
        outcome = (
            "true_positive"
            if detector_positive and expected_positive
            else "false_accusation"
            if detector_positive and not expected_positive
            else "missed_error"
            if not detector_positive and expected_positive
            else "true_negative"
        )
        rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "frozen_label_status": label_status,
                "contract_candidate_id": config.candidate_by_role[role],
                "finding_candidate_count": len(fired),
                "detector_positive": detector_positive,
                "comparison_outcome": outcome,
                "production_findings": len(bundle.get("findings", [])),
                "project_code_executions": len(bundle.get("executions", [])),
                "audit_lock_digest": sha256_digest(
                    (case_root / "audit" / "semantic.lock.json").read_bytes()
                ),
                "replay_equal": True,
            }
        )
    outcomes = [str(row["comparison_outcome"]) for row in rows]
    metrics = {
        "opportunity_count": len(rows),
        "true_positive_count": outcomes.count("true_positive"),
        "true_negative_count": outcomes.count("true_negative"),
        "false_accusation_count": outcomes.count("false_accusation"),
        "missed_error_count": outcomes.count("missed_error"),
        "sensitivity": (
            outcomes.count("true_positive")
            / max(1, outcomes.count("true_positive") + outcomes.count("missed_error"))
        ),
        "false_accusation_rate": (
            outcomes.count("false_accusation")
            / max(1, outcomes.count("false_accusation") + outcomes.count("true_negative"))
        ),
    }
    ledger: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_detector_run_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "adr_references": config.adr_references,
        "authoring_protocol_digest": protocol["protocol_digest"],
        "detector_tuple_digest": protocol["detector_tuple_digest"],
        "scientific_label_ledger_digest": label_ledger["ledger_digest"],
        "labels_frozen_before_detector_observation": True,
        "check_id": config.check_id,
        "check_version": detector_tuple["check_version"],
        "detector_id": DETECTOR_ID,
        "entries": rows,
        "pilot_metrics": metrics,
        "production_finding_count": sum(int(row["production_findings"]) for row in rows),
        "project_code_executed": False,
        "deterministic_replay_verified": True,
        "run_at": _now(),
        "qualification_authority": "none_pilot_detector_run_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(output_root / "DETECTOR_RUN_LEDGER.json", ledger)
    _manifest_record(
        project_root,
        config,
        "detector",
        digest=ledger["ledger_digest"],
        relative_path="detector-run/DETECTOR_RUN_LEDGER.json",
    )
    return ledger


STEP_FUNCTIONS = {
    "authoring": step_authoring,
    "intake": step_intake,
    "review": step_review,
    "labels": step_labels,
    "detector": step_detector,
}
STEP_ORDER = ("authoring", "intake", "review", "labels", "detector")


def run_pipeline(
    project_root: Path, config: EnvelopeConfig, steps: list[str] | None = None
) -> dict[str, Any]:
    manifest = _manifest_read(project_root, config)
    selected = steps or [step for step in STEP_ORDER if step not in manifest["steps"]]
    results: dict[str, Any] = {}
    for step in selected:
        if step not in STEP_FUNCTIONS:
            raise LeanPipelineError(f"Unknown pipeline step {step!r}.")
        results[step] = STEP_FUNCTIONS[step](project_root, config)
    return results
