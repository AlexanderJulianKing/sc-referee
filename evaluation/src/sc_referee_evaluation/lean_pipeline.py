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
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import jsonschema

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.dependence_recognition.authority_lock import (
    AUTHORITY_LIMITATIONS,
    DECLARED_EXECUTION_ROOT,
    LOCK_KIND,
    approval_projection,
    lock_projection,
    verify_dependence_authorization_lock,
)
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

SCHEMA_RELATIVE = Path("reference/schemas-v0.19.0")
DEVELOPMENT_MODEL_CALL_CONCURRENCY = 3
CALIBRATION_REGISTRY_RELATIVE = Path("evaluation/qualification/calibration-registry.json")
MANIFEST_NAME = "MANIFEST.json"
DETECTOR_ID = "detector:bounded-analysis-method-conflict"
DEPENDENCE_RECOGNITION_CHECK_ID = (
    "check:authorized-independent-unit-entry-into-row-independent-procedure"
)
CLI_TIMEOUT_SECONDS = 3600
SANDBOX_TIMEOUT_SECONDS = 30
MAX_INPUT_BYTES = 65536
MAX_PRODUCER_BYTES = 16384
MAX_REPORT_BYTES = 32768
SELECTED_RESULT_MARKER = "[selected-result]"
HOSTILE_PACKET_V1 = "1.0.0"
HOSTILE_PACKET_V2_RECEIPT = "2.0.0-receipt"
HOSTILE_PACKET_V2_DIGEST_DOMAIN = "sc-referee:development-hostile-answer-key-packet:v2"

VISIBLE_FILES = (
    {"path": "task.md", "role": "scientific_task"},
    {"path": "inputs/data.csv", "role": "staged_data"},
    {"path": "workflow/analysis.py", "role": "workflow_source"},
    {"path": "results/report.md", "role": "report"},
)


def _visible_files(config: EnvelopeConfig) -> tuple[dict[str, str], ...]:
    files = tuple(
        {**item, "path": config.authored_input_csv_path}
        if item["role"] == "staged_data"
        else dict(item)
        for item in VISIBLE_FILES
    )
    if config.authored_data_description_path is None:
        return files
    return (
        files[0],
        {
            "path": config.authored_data_description_path,
            "role": "data_description",
        },
        *files[1:],
    )


DEFAULT_ALLOWED_IMPORT_ROOTS = frozenset(
    {
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
)
_ALLOWED_IMPORT_ROOTS = DEFAULT_ALLOWED_IMPORT_ROOTS
_FORBIDDEN_NAMES = {"eval", "exec", "__import__", "compile", "globals", "locals", "vars"}
_DEPENDENCE_INPUT_HEADER = ("k1", "k2", "tag", "a", "b")
_MARKER_CONFUSABLES = str.maketrans(
    {
        "\u0430": "a",
        "\u0435": "e",
        "\u043e": "o",
        "\u0440": "p",
        "\u0441": "c",
        "\u0445": "x",
        "\u0443": "y",
        "\u0456": "i",
        "\u0458": "j",
        "\u03b1": "a",
        "\u03b2": "b",
        "\u03b5": "e",
        "\u03b9": "i",
        "\u03ba": "k",
        "\u03bf": "o",
        "\u03c1": "p",
        "\u03c4": "t",
        "\u03c5": "y",
        "\u03c7": "x",
    }
)
_RUNTIME_PROBE = """import importlib
import importlib.metadata
import json
import sys

required = json.loads(sys.argv[1])
distributions = {}
for name in sorted(required):
    module = importlib.import_module(name)
    distributions[name] = {
        "distribution_version": importlib.metadata.version(name),
        "module_version": getattr(module, "__version__", None),
        "module_path": getattr(module, "__file__", None),
    }
print(json.dumps({
    "python_version": sys.version,
    "sys_prefix": sys.prefix,
    "distributions": distributions,
}, sort_keys=True, separators=(",", ":")))
"""
_MAPPED_RUNTIME_PROBE = """import importlib
import importlib.metadata
import json
import sys

required = json.loads(sys.argv[1])
distributions = {}
for module_name in sorted(required):
    distribution_name = required[module_name]["distribution_name"]
    module = importlib.import_module(module_name)
    distributions[module_name] = {
        "distribution_name": distribution_name,
        "distribution_version": importlib.metadata.version(distribution_name),
        "module_version": getattr(module, "__version__", None),
        "module_path": getattr(module, "__file__", None),
    }
print(json.dumps({
    "python_version": sys.version,
    "sys_prefix": sys.prefix,
    "distributions": distributions,
}, sort_keys=True, separators=(",", ":")))
"""

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
ALLOWED_LABEL_STATUSES = frozenset(
    {
        "positive_demonstrated",
        "verified_good_eligible",
        "ambiguous_control",
        "unsupported_control",
    }
)
CODEX_CLI_BINARY = Path.home() / ".local/bin/codex"
CODEX_SCRATCH_ROOT = Path(
    "/private/tmp/claude-501/"
    "-Users-alexanderking-Desktop-random-stuff-sc-referee-implementation-v0-1-0/"
    "17c1734d-3826-4971-b383-843103dee23c/scratchpad"
)
CODEX_ANSWER_FILE = "answer.json"
CODEX_ANSWER_INSTRUCTION = (
    "Write your complete JSON answer as the only content of a file named answer.json in the "
    "current working directory. Do not print the JSON to the transcript."
)


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
    transport: str = "claude-cli"

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
            "transport": self.transport,
        }


# The per-envelope authoring file contract. Everything an author must build,
# and every accounting a case report must state, is envelope-specific: the
# default below is the ADR-0069 envelope-10 contract, and a new envelope
# supplies its own through EnvelopeConfig.author_case_requirements.
DEFAULT_AUTHOR_CASE_REQUIREMENTS = """Author every assigned case as a small, real, runnable analysis workflow. For each case you
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
1-based line number of the `[selected-result]` line inside report_md."""


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
    # Sealed held-out extensions. Every one defaults to the pilot behavior.
    sealed_case_assignments: dict[str, str] | None = None
    case_briefs: dict[str, dict[str, Any]] | None = None
    expected_verdict_by_role: dict[str, str] | None = None
    label_status_by_role: dict[str, str] | None = None
    author_case_requirements: str = DEFAULT_AUTHOR_CASE_REQUIREMENTS
    mq_tolerant_roles: set[str] = field(default_factory=set)
    contract_free_roles: set[str] = field(default_factory=set)
    opening_record_relative: str | None = None
    allowed_import_roots: frozenset[str] = DEFAULT_ALLOWED_IMPORT_ROOTS
    detector_id: str = DETECTOR_ID
    sandbox_python: Path | None = None
    required_sandbox_distributions: dict[str, str] = field(default_factory=dict)
    # Opt-in module/distribution split for packages whose import root differs
    # from their installed distribution name.  None retains the legacy probe
    # script and byte-identical intake-ledger projection.
    required_sandbox_module_distributions: dict[str, tuple[str, str]] | None = None
    controller_material_files: dict[str, bytes] = field(default_factory=dict)
    material_input_paths: tuple[str, ...] = ()
    input_csv_row_bounds: tuple[int, int] | None = None
    frozen_workflow_template: str | None = None
    frozen_workflow_procedure_by_role: dict[str, str] = field(default_factory=dict)
    authored_data_description_path: str | None = None
    authored_input_csv_path: str = "inputs/data.csv"
    required_input_csv_header: tuple[str, ...] | None = None
    allow_unprescribed_input_csv_header: bool = False
    dependence_authority_from_description: bool = False
    forbidden_artifact_markers: frozenset[str] = frozenset()
    record_purpose: str | None = None
    stateless_review_per_case: bool = False
    hostile_answer_key_reviewer: ModelParticipant | None = None
    freeze_role_key_in_review_protocol: bool = False
    halt_on_false_accusation: bool = False
    publish_count_metrics_only: bool = False
    authored_role_ratification: bool = False
    separately_reported_role: str | None = None
    development_loop: bool = False
    # Evaluation-only growth hook. The controller accepts only an opaque observer
    # callback and never imports or selects the unregistered v2 recognizer.
    dependence_v2_development_shadow: bool = False
    # Development-only distinct authority line. False preserves every v1 lane.
    dependence_v2_lock_line: bool = False
    reviewer_task_text: str | None = None
    utf8_authored_paths: frozenset[str] = frozenset()
    whole_token_role_markers: bool = False
    # Opt-in outside dependence, whose authority lock already requires it.
    # False preserves every pre-existing envelope's intake projection.
    record_expected_audit_snapshot_digest: bool = False
    # Development-loop formatting hardening. Qualification envelopes retain
    # their historical transport and retained-call identities byte-for-byte.
    enforce_cli_review_json_schema: bool = False

    @property
    def roles(self) -> list[str]:
        return sorted({role for roles in self.author_roles.values() for role in roles})

    @property
    def requires_dependence_authority(self) -> bool:
        return self.check_id == DEPENDENCE_RECOGNITION_CHECK_ID

    def expected_verdict(self, role: str) -> str:
        table = (
            EXPECTED_VERDICT_BY_ROLE
            if self.expected_verdict_by_role is None
            else self.expected_verdict_by_role
        )
        if role not in table:
            raise LeanPipelineError(f"No expected verdict is configured for role {role!r}.")
        return table[role]

    def label_status(self, role: str) -> str:
        table = (
            LABEL_STATUS_BY_ROLE if self.label_status_by_role is None else self.label_status_by_role
        )
        if role not in table:
            raise LeanPipelineError(f"No label status is configured for role {role!r}.")
        status = table[role]
        if status not in ALLOWED_LABEL_STATUSES:
            raise LeanPipelineError(f"Label status {status!r} is outside the frozen vocabulary.")
        return status


def _stamp_record_purpose(record: dict[str, Any], config: EnvelopeConfig) -> None:
    """Add the opt-in development-plane marker before a record is digested."""

    if config.record_purpose is not None:
        record["record_purpose"] = config.record_purpose


def _case_task_text(config: EnvelopeConfig, role: str) -> str:
    return config.reviewer_task_text or config.task_by_role[role]


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
        manifest = {
            "artifact_kind": "lean_pipeline_manifest",
            "manifest_version": "1.0.0",
            "envelope_id": config.envelope_id,
            "steps": {},
        }
        _stamp_record_purpose(manifest, config)
        return manifest
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
    review_participants = [config.reviewer, config.escalation_reviewer]
    if config.hostile_answer_key_reviewer is not None:
        review_participants.append(config.hostile_answer_key_reviewer)
    for participant in review_participants:
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
    response_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch one one-shot model call onto the participant's transport."""

    if participant.transport == "claude-cli":
        return _call_claude_cli(
            config, participant, prompt, session_id, capture_root, response_schema
        )
    if participant.transport == "codex-cli":
        return _call_codex(config, participant, prompt, session_id, capture_root)
    raise LeanPipelineError(f"Unknown participant transport {participant.transport!r}.")


def _run_stage_model_calls(
    config: EnvelopeConfig,
    callback: Callable[[Any], Any],
    items: list[Any],
) -> list[Any]:
    """Run development-only stateless calls concurrently, preserving item order."""

    if not config.development_loop or len(items) < 2:
        return [callback(item) for item in items]
    with ThreadPoolExecutor(
        max_workers=min(DEVELOPMENT_MODEL_CALL_CONCURRENCY, len(items))
    ) as executor:
        return list(executor.map(callback, items))


def _call_claude_cli(
    config: EnvelopeConfig,
    participant: ModelParticipant,
    prompt: str,
    session_id: str,
    capture_root: Path,
    response_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_capture_root = capture_root
    if response_schema is not None and _retained_claude_schema_meta_rejection(
        participant, prompt, session_id, capture_root
    ):
        # Client-side schema validation reached no model, so it consumed no
        # reviewer attempt; preserve that capture and bind the retry separately.
        active_capture_root = capture_root / "schema-compatible-retry"
    retained = _retained_call(participant, prompt, session_id, active_capture_root)
    if retained is not None:
        return retained
    active_capture_root.mkdir(parents=True, exist_ok=True)
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
        ]
        if response_schema is not None:
            argv.extend(
                ["--json-schema", canonical_json(_claude_cli_response_schema(response_schema))]
            )
        argv.append(prompt)
        completed = subprocess.run(
            argv,
            cwd=temporary,
            env=environment,
            capture_output=True,
            check=False,
            timeout=CLI_TIMEOUT_SECONDS,
        )
    completed_at = _now()
    atomic_write_bytes(active_capture_root / "stdout.bin", completed.stdout)
    atomic_write_bytes(active_capture_root / "stderr.bin", completed.stderr)
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
    write_normalized_json_once(active_capture_root / "capture.json", process_record)
    return {
        "raw_response": raw_response,
        "transport_error": transport_error,
        "process_record": process_record,
        "started_at": started_at,
        "completed_at": completed_at,
    }


_CLAUDE_SCHEMA_META_REJECTION = (
    "Error: --json-schema is not a valid JSON Schema: no schema with key or ref "
    '"https://json-schema.org/draft/2020-12/schema"'
)


def _claude_cli_response_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return the installed Claude CLI's accepted implicit-dialect form."""

    return {key: value for key, value in schema.items() if key != "$schema"}


def _retained_claude_schema_meta_rejection(
    participant: ModelParticipant,
    prompt: str,
    session_id: str,
    capture_root: Path,
) -> bool:
    """Recognize only the retained, pre-model 2020-12 meta-schema rejection."""

    capture_path = capture_root / "capture.json"
    if not capture_path.exists():
        return False
    record = _load(capture_path)
    if (
        record.get("participant_id") != participant.participant_id
        or record.get("session_id") != session_id
        or record.get("prompt_digest") != sha256_digest(prompt)
        or record.get("transport_error") != "provider_cli_exit_code:1"
    ):
        return False
    stderr = (capture_root / "stderr.bin").read_bytes()
    stdout = (capture_root / "stdout.bin").read_bytes()
    if sha256_digest(stderr) != record.get("stderr_digest") or sha256_digest(stdout) != record.get(
        "stdout_digest"
    ):
        raise LeanPipelineError("A retained schema-rejection capture's bytes drifted.")
    return _CLAUDE_SCHEMA_META_REJECTION in stderr.decode("utf-8", errors="replace")


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
    if participant.transport == "codex-cli":
        answer = (capture_root / CODEX_ANSWER_FILE).read_bytes()
        if sha256_digest(answer) != record.get("answer_digest"):
            raise LeanPipelineError("A retained call capture's answer bytes drifted.")
        raw_response = answer.decode("utf-8")
    else:
        envelope = json.loads(stdout.decode("utf-8"))
        raw_response = str(envelope.get("result"))
    return {
        "raw_response": raw_response,
        "transport_error": None,
        "process_record": record,
        "started_at": record["started_at"],
        "completed_at": record["completed_at"],
    }


def _codex_banner_model_line(stdout: bytes) -> str | None:
    """The first stdout line mentioning a model, retained as banner-only evidence."""

    for line in stdout.decode("utf-8", "replace").splitlines():
        if "model" in line.lower() and line.strip():
            return line.strip()
    return None


_CODEX_HEAD_SWAP = (
    """You have no tools, no filesystem, no shell, and no execution environment; do not attempt to
run, test, or verify anything externally, and do not narrate tool use. Construct the files in
your head, check the arithmetic mentally, and reply with exactly one JSON object and nothing
else: no prose before or after it, no markdown fences, no tool-call blocks.""",
    """You are working in an isolated scratch workspace with no network access. You may use it
only to draft and verify your own files (running your workflow to check its output is fine)
and to write your answer file; touch nothing outside the working directory and do not narrate
tool use in your answer.""",
)


def _call_codex(
    config: EnvelopeConfig,
    participant: ModelParticipant,
    prompt: str,
    session_slug: str,
    capture_root: Path,
) -> dict[str, Any]:
    """One one-shot Codex CLI call whose answer arrives as a file, not a transcript.

    The Codex transport has no served-model field in its machine output, so the
    served model is recorded as ``banner_only``: the model flag this process
    actually passed plus the first banner line mentioning a model. That is
    weaker evidence than the Claude transport's per-call ``modelUsage`` map and
    is labelled as such rather than asserted as verification. The shared
    no-tools instruction head is swapped for a workspace-scoped variant so the
    transmitted prompt never contradicts the answer-file instruction.
    """
    prompt = prompt.replace(_CODEX_HEAD_SWAP[0], _CODEX_HEAD_SWAP[1])

    retained = _retained_call(participant, prompt, session_slug, capture_root)
    if retained is not None:
        return retained
    capture_root.mkdir(parents=True, exist_ok=True)
    scratch = CODEX_SCRATCH_ROOT / f"codex-author-{session_slug}"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    transmitted = prompt.rstrip() + "\n\n" + CODEX_ANSWER_INSTRUCTION + "\n"
    atomic_write_bytes(scratch / "prompt.txt", transmitted.encode("utf-8"))
    model_flag = ["-m", participant.model_id]
    argv = [
        str(CODEX_CLI_BINARY),
        "exec",
        *model_flag,
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        transmitted,
    ]
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    started_at = _now()
    try:
        completed = subprocess.run(
            argv,
            cwd=scratch,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=CLI_TIMEOUT_SECONDS,
        )
        return_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        transport_error: str | None = (
            None if return_code == 0 else f"provider_cli_exit_code:{return_code}"
        )
    except subprocess.TimeoutExpired as error:
        return_code = 124
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        transport_error = f"timeout_{CLI_TIMEOUT_SECONDS}_seconds"
    completed_at = _now()
    atomic_write_bytes(capture_root / "stdout.bin", stdout)
    atomic_write_bytes(capture_root / "stderr.bin", stderr)
    answer_path = scratch / CODEX_ANSWER_FILE
    answer = answer_path.read_bytes() if answer_path.is_file() else b""
    if answer:
        atomic_write_bytes(capture_root / CODEX_ANSWER_FILE, answer)
    raw_response = ""
    if transport_error is None:
        try:
            json.loads(answer.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            transport_error = "missing_answer_file"
        else:
            raw_response = answer.decode("utf-8")
    process_record = {
        "artifact_kind": "lean_pipeline_cli_process_capture",
        "capture_version": "1.0.0",
        "transport": "codex-cli",
        "participant_id": participant.participant_id,
        "session_id": session_slug,
        "argv_digest": semantic_digest(argv),
        "prompt_digest": sha256_digest(prompt),
        "transmitted_prompt_digest": sha256_digest(transmitted),
        "answer_file_relative": CODEX_ANSWER_FILE,
        "answer_digest": sha256_digest(answer) if answer else None,
        "return_code": return_code,
        "transport_error": transport_error,
        "model_flag": model_flag,
        "served_model_verification": "banner_only",
        "served_model_banner_line": _codex_banner_model_line(stdout),
        "stdout_digest": sha256_digest(stdout),
        "stderr_digest": sha256_digest(stderr),
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


# ---------------------------------------------------------------------------
# Step 1: blind authoring of executable workflows.


def _author_output_schema(
    participant_id: str, case_ids: list[str], config: EnvelopeConfig
) -> dict[str, Any]:
    case_schema: dict[str, Any] = {
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
    if config.authored_data_description_path is not None:
        case_schema["required"].append("data_description")
        case_schema["properties"]["data_description"] = {
            "type": "string",
            "minLength": 1,
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

{case_requirements}

{task}

Case assignments:
{assignments}

Return only one unfenced JSON object matching this exact schema:
{schema}
"""


def _case_brief_block(config: EnvelopeConfig, case_id: str, role: str) -> str:
    """One per-case authoring block: role constraints, or a sealed brief verbatim.

    The sealed brief's ``required_artifacts`` is deliberately not quoted: the
    ADR-0069 file contract in the shared instructions governs what the author
    returns, and the sealed artifact list predates it.
    """

    if config.case_briefs is None:
        constraints = "\n".join(f"  - {line}" for line in config.role_constraints[role])
        return f"- case_id {case_id}:\n{constraints}"
    brief = config.case_briefs[case_id]
    lines = [f"- case_id {case_id}:", f"  scientific task: {brief['scientific_task']}"]
    lines.append("  available inputs:")
    lines.extend(f"    - {item}" for item in brief["available_inputs"])
    lines.append("  construction constraints:")
    lines.extend(f"    - {item}" for item in brief["construction_constraints"])
    return "\n".join(lines)


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
    if binding.get("detector_id") != config.detector_id:
        raise LeanPipelineError(
            "The configured detector id does not match the registered method-conflict binding."
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
    if config.requires_dependence_authority:
        detector_tuple["detector_id"] = config.detector_id
    tuple_digest = semantic_digest(detector_tuple)

    if config.sealed_case_assignments is None:
        case_ids = {
            role: stable_id("case", config.envelope_id, "lean-pipeline", role, tuple_digest)
            for role in config.roles
        }
        role_by_case = {case_id: role for role, case_id in case_ids.items()}
    else:
        role_by_case = dict(config.sealed_case_assignments)
        case_ids = {role: case_id for case_id, role in role_by_case.items()}
        if len(case_ids) != len(role_by_case):
            raise LeanPipelineError("The sealed case assignments repeat a role.")
        if sorted(case_ids) != config.roles:
            raise LeanPipelineError(
                "The sealed case assignments do not cover exactly the authored roles."
            )

    assignments: list[dict[str, Any]] = []
    for participant_id in sorted(config.authors):
        participant = config.authors[participant_id]
        roles = config.author_roles[participant_id]
        assigned = sorted(case_ids[role] for role in roles)
        brief_lines = []
        for case_id in assigned:
            brief_lines.append(_case_brief_block(config, case_id, role_by_case[case_id]))
        schema = _author_output_schema(participant_id, assigned, config)
        prompt = _AUTHOR_INSTRUCTIONS.format(
            case_requirements=config.author_case_requirements,
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
    if config.development_loop and config.reviewer_task_text is not None:
        protocol["task_binding_disclosure"] = (
            "The governing task.md is a neutral reviewer-directed sentence rather than a "
            "scientific target, unlike qualification envelopes; the method contract binds "
            "the candidate id explicitly."
        )
    if config.case_briefs is not None:
        protocol["sealed_brief_digests"] = {
            case_id: semantic_digest(config.case_briefs[case_id])
            for case_id in sorted(role_by_case)
        }
    if config.opening_record_relative is not None:
        protocol["heldout_opening_reference"] = config.opening_record_relative
    _stamp_record_purpose(protocol, config)
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

    results = _run_stage_model_calls(config, _run, assignments)
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


def _static_guard(source: str, allowed_import_roots: frozenset[str]) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise LeanPipelineError(f"Authored workflow does not parse: {error}") from error
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed_import_roots:
                    raise LeanPipelineError(
                        f"Authored workflow imports a forbidden module: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            root_name = (node.module or "").split(".")[0]
            if node.level or root_name not in allowed_import_roots:
                raise LeanPipelineError(
                    f"Authored workflow imports a forbidden module: {node.module}"
                )
        elif isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise LeanPipelineError(f"Authored workflow uses a forbidden builtin: {node.id}")


def _sandbox_run(case_root: Path, sandbox_python: Path) -> bytes:
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
            [str(sandbox_python), "-I", "workflow/analysis.py"],
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


def _resolve_sandbox_python(project_root: Path, config: EnvelopeConfig) -> Path:
    configured = config.sandbox_python or Path(sys.executable)
    expanded = configured.expanduser()
    candidate = expanded if expanded.is_absolute() else project_root / expanded
    # Keep the venv entry path rather than resolving its symlink: CPython uses
    # that entry path to locate pyvenv.cfg and establish the intended prefix.
    candidate = Path(os.path.abspath(candidate))
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise LeanPipelineError("The configured sandbox interpreter is not executable.")
    return candidate


def _probe_sandbox_runtime(
    sandbox_python: Path,
    required_distributions: Mapping[str, str],
    required_module_distributions: Mapping[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    if required_module_distributions is not None and required_distributions:
        raise LeanPipelineError("Sandbox probe pin channels cannot be combined.")
    if required_module_distributions is None and not required_distributions:
        raise LeanPipelineError("A sandbox probe requires at least one pinned distribution.")
    if required_module_distributions is not None and not required_module_distributions:
        raise LeanPipelineError("A sandbox probe requires at least one pinned distribution.")
    if required_module_distributions is None and any(
        not isinstance(name, str)
        or not name
        or name != name.strip()
        or not isinstance(version, str)
        or not version
        or version != version.strip()
        for name, version in required_distributions.items()
    ):
        raise LeanPipelineError("Sandbox distribution pins are invalid.")
    if required_module_distributions is not None and any(
        not isinstance(module_name, str)
        or not module_name
        or module_name != module_name.strip()
        or not isinstance(pin, tuple)
        or len(pin) != 2
        or not isinstance(pin[0], str)
        or not pin[0]
        or pin[0] != pin[0].strip()
        or not isinstance(pin[1], str)
        or not pin[1]
        or pin[1] != pin[1].strip()
        for module_name, pin in required_module_distributions.items()
    ):
        raise LeanPipelineError("Sandbox module-to-distribution pins are invalid.")
    mapped_requirements = (
        {
            module_name: {
                "distribution_name": distribution_name,
                "required_version": required_version,
            }
            for module_name, (distribution_name, required_version) in sorted(
                required_module_distributions.items()
            )
        }
        if required_module_distributions is not None
        else None
    )
    probe_script = _RUNTIME_PROBE if mapped_requirements is None else _MAPPED_RUNTIME_PROBE
    probe_argument: dict[str, Any] = (
        dict(sorted(required_distributions.items()))
        if mapped_requirements is None
        else mapped_requirements
    )
    interpreter_digest = sha256_digest(sandbox_python.read_bytes())
    completed = subprocess.run(
        [
            str(sandbox_python),
            "-I",
            "-c",
            probe_script,
            canonical_json(probe_argument),
        ],
        env={"NO_COLOR": "1"},
        capture_output=True,
        check=False,
        timeout=SANDBOX_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0 or completed.stderr:
        raise LeanPipelineError("The isolated sandbox runtime probe failed.")
    if sha256_digest(sandbox_python.read_bytes()) != interpreter_digest:
        raise LeanPipelineError("The sandbox interpreter drifted during its isolated probe.")
    try:
        observed = json.loads(completed.stdout.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LeanPipelineError("The sandbox runtime probe returned invalid JSON.") from error
    if not isinstance(observed, dict) or set(observed) != {
        "python_version",
        "sys_prefix",
        "distributions",
    }:
        raise LeanPipelineError("The sandbox runtime probe returned an open record.")
    distributions = observed.get("distributions")
    expected_names = (
        set(required_distributions)
        if required_module_distributions is None
        else set(required_module_distributions)
    )
    if not isinstance(distributions, dict) or set(distributions) != expected_names:
        raise LeanPipelineError("The sandbox runtime probe covered the wrong distributions.")
    pins = (
        {name: (name, version) for name, version in required_distributions.items()}
        if required_module_distributions is None
        else required_module_distributions
    )
    for name, (distribution_name, required_version) in pins.items():
        item = distributions.get(name)
        expected_item_keys = {
            "distribution_version",
            "module_version",
            "module_path",
        }
        if required_module_distributions is not None:
            expected_item_keys.add("distribution_name")
        if not isinstance(item, dict) or set(item) != expected_item_keys:
            raise LeanPipelineError("The sandbox runtime probe distribution record is open.")
        if (
            (
                required_module_distributions is not None
                and item.get("distribution_name") != distribution_name
            )
            or item.get("distribution_version") != required_version
            or item.get("module_version") != required_version
            or not isinstance(item.get("module_path"), str)
            or not item["module_path"]
        ):
            pin_label = (
                name if required_module_distributions is None else f"{name}/{distribution_name}"
            )
            raise LeanPipelineError(
                "The sandbox runtime does not satisfy the exact "
                f"{pin_label}=={required_version} pin."
            )
    if not isinstance(observed.get("sys_prefix"), str) or not observed["sys_prefix"]:
        raise LeanPipelineError("The sandbox runtime probe omitted sys.prefix.")
    if not isinstance(observed.get("python_version"), str) or not observed["python_version"]:
        raise LeanPipelineError("The sandbox runtime probe omitted the Python version.")
    record: dict[str, Any] = {
        "interpreter_path": sandbox_python.as_posix(),
        "interpreter_digest": interpreter_digest,
        "sys_prefix": observed["sys_prefix"],
        "python_version": observed["python_version"],
        "required_distributions": dict(sorted(required_distributions.items())),
        "observed_distributions": distributions,
        "probe_script_digest": sha256_digest(probe_script),
    }
    if mapped_requirements is not None:
        record["required_module_distributions"] = mapped_requirements
    record["probe_digest"] = semantic_digest(record)
    return record


def _validate_bounded_input_csv(input_csv: str, config: EnvelopeConfig) -> None:
    bounds = config.input_csv_row_bounds
    if bounds is None:
        return
    lower, upper = bounds
    if lower < 0 or upper < lower:
        raise LeanPipelineError("The configured input CSV row bounds are invalid.")
    try:
        rows = list(csv.reader(io.StringIO(input_csv, newline=""), strict=True))
    except csv.Error as error:
        raise LeanPipelineError("The authored input CSV is malformed.") from error
    if not rows or not rows[0] or any(not item for item in rows[0]):
        raise LeanPipelineError("The authored input CSV header is empty.")
    header = tuple(rows[0])
    if len(header) != len(set(header)):
        raise LeanPipelineError("The authored input CSV header is duplicated.")
    required_header = config.required_input_csv_header
    if (
        required_header is None
        and config.requires_dependence_authority
        and not config.allow_unprescribed_input_csv_header
    ):
        required_header = _DEPENDENCE_INPUT_HEADER
    if required_header is not None and header != required_header:
        raise LeanPipelineError("The input CSV header is outside the frozen envelope.")
    data_rows = rows[1:]
    if not lower <= len(data_rows) <= upper:
        raise LeanPipelineError("The authored input CSV row count is outside its bound.")
    if any(len(row) != len(header) or any(cell == "" for cell in row) for row in data_rows):
        raise LeanPipelineError("The authored input CSV contains an empty or ragged row.")


def _require_probed_interpreter_unchanged(
    sandbox_python: Path, runtime_probe: dict[str, Any] | None
) -> None:
    if (
        runtime_probe is not None
        and sha256_digest(sandbox_python.read_bytes()) != runtime_probe["interpreter_digest"]
    ):
        raise LeanPipelineError("The sandbox interpreter drifted after its intake probe.")


def _controller_material_files(config: EnvelopeConfig) -> tuple[tuple[str, bytes], ...]:
    visible_paths = {str(item["path"]) for item in _visible_files(config)}
    entries: list[tuple[str, bytes]] = []
    for path_value, payload in sorted(config.controller_material_files.items()):
        path = Path(path_value)
        if (
            not path_value
            or path.is_absolute()
            or "." in path.parts
            or ".." in path.parts
            or path_value in visible_paths
            or not isinstance(payload, bytes)
        ):
            raise LeanPipelineError("A controller material file escapes the private envelope.")
        entries.append((path_value, payload))
    if len(config.material_input_paths) != len(set(config.material_input_paths)):
        raise LeanPipelineError("The material input paths are duplicated.")
    available = visible_paths | {path for path, _payload in entries}
    if any(path not in available for path in config.material_input_paths):
        raise LeanPipelineError("A material input path is not present in the admitted case.")
    return tuple(entries)


def _expected_frozen_workflow(config: EnvelopeConfig, role: str) -> str | None:
    """Close one optional authored-workflow template over its role substitution."""

    template = config.frozen_workflow_template
    procedures = config.frozen_workflow_procedure_by_role
    if template is None:
        if procedures:
            raise LeanPipelineError("frozen-workflow-template-configuration-invalid")
        return None
    if (
        template.count("{procedure}") != 1
        or set(procedures) != set(config.roles)
        or role not in procedures
        or not procedures[role].isidentifier()
    ):
        raise LeanPipelineError("frozen-workflow-template-configuration-invalid")
    return template.replace("{procedure}", procedures[role])


def _normalized_marker_text(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", value)
        .translate(_MARKER_CONFUSABLES)
        .casefold()
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )


def _validate_authored_case(
    config: EnvelopeConfig,
    *,
    case_id: str,
    role: str,
    item: Mapping[str, Any],
    authored_files: list[tuple[str, str, int]],
    analysis_py: str,
    input_csv: str,
    report_md: str,
) -> list[int]:
    role_markers = (
        set(config.roles)
        if config.authored_data_description_path is not None or config.forbidden_artifact_markers
        else set()
    )
    default_markers = set(config.forbidden_artifact_markers)
    for name, payload_text, limit in authored_files:
        encoded = payload_text.encode("utf-8")
        if len(encoded) > limit:
            raise LeanPipelineError(f"Authored file {name} exceeds its size bound.")
        if name not in config.utf8_authored_paths and not payload_text.isascii():
            raise LeanPipelineError(f"Authored file {name} is not ASCII.")
        normalized = _normalized_marker_text(payload_text)
        if any(
            _normalized_marker_text(marker) in normalized for marker in default_markers if marker
        ):
            raise LeanPipelineError(f"Authored file {name} contains a forbidden marker.")
        if config.whole_token_role_markers:
            folded = (
                unicodedata.normalize("NFKC", payload_text)
                .translate(_MARKER_CONFUSABLES)
                .casefold()
            )
            if any(
                re.search(rf"(?<![0-9a-z]){re.escape(marker.casefold())}(?![0-9a-z])", folded)
                for marker in role_markers
            ):
                raise LeanPipelineError(f"Authored file {name} contains a forbidden marker.")
        elif any(
            _normalized_marker_text(marker) in normalized for marker in role_markers if marker
        ):
            raise LeanPipelineError(f"Authored file {name} contains a forbidden marker.")
    expected_workflow = _expected_frozen_workflow(config, role)
    if expected_workflow is not None and analysis_py.encode("utf-8") != expected_workflow.encode(
        "utf-8"
    ):
        raise LeanPipelineError("frozen-workflow-template-mismatch")
    _static_guard(analysis_py, config.allowed_import_roots)
    _validate_bounded_input_csv(input_csv, config)
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
    return marker_lines


def step_intake(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    output_root = root / "authoring"
    _entry, protocol = _manifest_require(project_root, config, "authoring")
    if (root / "authoring" / "INTAKE_LEDGER.json").exists():
        raise LeanPipelineError("The intake step already has output.")
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    sandbox_python = _resolve_sandbox_python(project_root, config)
    runtime_probe = (
        _probe_sandbox_runtime(
            sandbox_python,
            config.required_sandbox_distributions,
            config.required_sandbox_module_distributions,
        )
        if config.required_sandbox_distributions
        or config.required_sandbox_module_distributions is not None
        else None
    )
    controller_files = _controller_material_files(config)
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
            if not config.development_loop:
                raise LeanPipelineError(
                    f"An author response is not valid JSON: {participant_id}"
                ) from error
            for case_id_value in assignment["case_ids"]:
                case_id = str(case_id_value)
                rows.append(
                    {
                        "case_id": case_id,
                        "case_role": roles[case_id],
                        "author_participant_id": participant_id,
                        "intake_admission_state": "refused_but_case_retained",
                        "intake_admission_reason": "author response is not valid JSON",
                        "file_digests": {},
                        "sandbox_runs": 0,
                        "sandbox_report_digest": None,
                        "deterministic": False,
                    }
                )
            continue
        if config.development_loop:
            cases = payload.get("cases", []) if isinstance(payload, dict) else []
            if not isinstance(cases, list):
                cases = []
        else:
            try:
                jsonschema.validate(payload, assignment["output_schema"])
            except jsonschema.ValidationError as error:
                raise LeanPipelineError(
                    f"An author response fails its frozen schema: {error.message}"
                ) from error
            cases = payload["cases"]
        returned_ids = sorted(
            str(item.get("case_id", "")) for item in cases if isinstance(item, dict)
        )
        if not config.development_loop and returned_ids != sorted(
            str(v) for v in assignment["case_ids"]
        ):
            raise LeanPipelineError("An author response covers the wrong case ids.")
        cases_by_id = {str(item.get("case_id")): item for item in cases if isinstance(item, dict)}
        selected_cases = (
            [
                cases_by_id.get(str(case_id), {"case_id": case_id})
                for case_id in assignment["case_ids"]
            ]
            if config.development_loop
            else cases
        )
        for item in selected_cases:
            case_id = str(item.get("case_id", ""))
            if config.development_loop:
                try:
                    jsonschema.validate(
                        item, assignment["output_schema"]["properties"]["cases"]["items"]
                    )
                except jsonschema.ValidationError as error:
                    rows.append(
                        {
                            "case_id": case_id,
                            "case_role": roles[case_id],
                            "author_participant_id": participant_id,
                            "intake_admission_state": "refused_but_case_retained",
                            "intake_admission_reason": f"author response fails case schema: {error.message}",
                            "file_digests": {},
                            "sandbox_runs": 0,
                            "sandbox_report_digest": None,
                            "deterministic": False,
                        }
                    )
                    continue
            input_csv = str(item["input_csv"])
            analysis_py = str(item["analysis_py"])
            report_md = str(item["report_md"])
            authored_files = [
                (config.authored_input_csv_path, input_csv, MAX_INPUT_BYTES),
                ("workflow/analysis.py", analysis_py, MAX_PRODUCER_BYTES),
                ("results/report.md", report_md, MAX_REPORT_BYTES),
            ]
            description_path = config.authored_data_description_path
            if description_path is not None:
                authored_files.append(
                    (description_path, str(item["data_description"]), MAX_REPORT_BYTES)
                )
            try:
                marker_lines = _validate_authored_case(
                    config,
                    case_id=case_id,
                    role=roles[case_id],
                    item=item,
                    authored_files=authored_files,
                    analysis_py=analysis_py,
                    input_csv=input_csv,
                    report_md=report_md,
                )
            except (Exception, RecursionError) as error:
                if not config.development_loop:
                    raise
                rows.append(
                    {
                        "case_id": case_id,
                        "case_role": roles[case_id],
                        "author_participant_id": participant_id,
                        "intake_admission_state": "refused_but_case_retained",
                        "intake_admission_reason": str(error),
                        "file_digests": {
                            name: sha256_digest(payload_text.encode("utf-8"))
                            for name, payload_text, _limit in authored_files
                        },
                        "sandbox_runs": 0,
                        "sandbox_report_digest": None,
                        "deterministic": False,
                    }
                )
                continue
            execution_error: str | None = None
            case_root = output_root / "cases" / case_id.removeprefix("case:")
            try:
                (case_root / config.authored_input_csv_path).parent.mkdir(
                    parents=True, exist_ok=True
                )
                (case_root / "workflow").mkdir(parents=True, exist_ok=True)
                (case_root / "results").mkdir(parents=True, exist_ok=True)
                (case_root / config.authored_input_csv_path).write_bytes(input_csv.encode("utf-8"))
                (case_root / "workflow/analysis.py").write_bytes(analysis_py.encode("utf-8"))
                (case_root / "results/report.md").write_bytes(report_md.encode("utf-8"))
                if description_path is not None:
                    description_destination = case_root / description_path
                    description_destination.parent.mkdir(parents=True, exist_ok=True)
                    description_destination.write_bytes(
                        str(item["data_description"]).encode("utf-8")
                    )
                for path_value, payload in controller_files:
                    destination = case_root / path_value
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if destination.is_symlink() or (
                        destination.exists() and destination.read_bytes() != payload
                    ):
                        raise LeanPipelineError(
                            "A controller material file collides with case bytes."
                        )
                    if not destination.exists():
                        atomic_write_bytes(destination, payload)
                _require_probed_interpreter_unchanged(sandbox_python, runtime_probe)
                first = _sandbox_run(case_root, sandbox_python)
                _require_probed_interpreter_unchanged(sandbox_python, runtime_probe)
                second = _sandbox_run(case_root, sandbox_python)
                _require_probed_interpreter_unchanged(sandbox_python, runtime_probe)
                if first != second:
                    raise LeanPipelineError(f"Case {case_id} is not deterministic.")
                if first != report_md.encode("utf-8"):
                    raise LeanPipelineError(
                        f"Case {case_id} report does not equal its executed output."
                    )
            except (Exception, RecursionError) as error:
                if not config.development_loop:
                    raise
                execution_error = str(error)
                first = b""
            row: dict[str, Any] = {
                "case_id": case_id,
                "case_role": roles[case_id],
                "author_participant_id": participant_id,
                "selected_result_line": marker_lines[0],
                "file_digests": {
                    name: sha256_digest(payload_text.encode("utf-8"))
                    for name, payload_text, _limit in authored_files
                },
                "sandbox_runs": 0 if execution_error is not None else 2,
                "sandbox_report_digest": (
                    None if execution_error is not None else sha256_digest(first)
                ),
                "deterministic": execution_error is None,
                **(
                    {
                        "intake_admission_state": "refused_but_case_retained",
                        "intake_admission_reason": execution_error,
                    }
                    if execution_error is not None
                    else ({"intake_admission_state": "admitted"} if config.development_loop else {})
                ),
            }
            if controller_files:
                row["controller_material_file_digests"] = {
                    path_value: sha256_digest(payload) for path_value, payload in controller_files
                }
            if execution_error is None and (
                config.requires_dependence_authority or config.record_expected_audit_snapshot_digest
            ):
                row["expected_audit_snapshot_digest"] = _prospective_audit_snapshot_digest(
                    case_root,
                    task_payload=(_case_task_text(config, roles[case_id]).rstrip() + "\n").encode(
                        "utf-8"
                    ),
                    material_input_paths=config.material_input_paths,
                )
            rows.append(row)
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
    if runtime_probe is not None:
        ledger["sandbox_runtime_probe"] = runtime_probe
    _stamp_record_purpose(ledger, config)
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


def _prospective_audit_snapshot_digest(
    case_root: Path,
    *,
    task_payload: bytes,
    material_input_paths: tuple[str, ...],
) -> str:
    """Freeze the content identity of the exact future detector repository."""

    with tempfile.TemporaryDirectory(prefix="sc-referee-dependence-snapshot-") as raw_root:
        temporary_root = Path(raw_root)
        repository = temporary_root / "project"
        shutil.copytree(case_root, repository)
        atomic_write_bytes(repository / "task.md", task_payload)
        captured = capture_repository(
            repository,
            temporary_root / "snapshot",
            "lean-pipeline-prospective-dependence-snapshot",
            captured_at="1970-01-01T00:00:00Z",
            preferred_full_digest_paths=("results/report.md",),
            material_full_digest_paths=material_input_paths,
        )
        return str(captured.snapshot_record["snapshot_digest"])


# ---------------------------------------------------------------------------
# Conditional dependence authority freeze: after intake, before review.


_DESCRIPTION_UNIT_COLUMN = re.compile(
    r"(?im)^[ \t]*independent unit column[ \t]*:[ \t]+`?([A-Za-z_][A-Za-z0-9_]*)`?[ \t\r]*$"
)
_DESCRIPTION_ROW = re.compile(r"(?im)^[ \t]*one row is[ \t]*:[ \t]+(\S[^\r\n]*?)[ \t\r]*$")
_DESCRIPTION_TRIAL_ROW = re.compile(r"(?m)^One trial is: one row\r?$")
_REGISTERED_DEPENDENCE_CALLABLES = frozenset(
    {"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu", "scipy.stats.ttest_rel"}
)


def _description_unit_column(description: str) -> str | None:
    matches = _DESCRIPTION_UNIT_COLUMN.findall(description)
    rows = _DESCRIPTION_ROW.findall(description)
    if len(matches) != 1 or len(rows) != 1:
        return None
    return str(matches[0])


def _registered_dependence_callable(
    source: str,
    registry: frozenset[str] = _REGISTERED_DEPENDENCE_CALLABLES,
) -> tuple[str | None, str]:
    """Resolve one direct registered SciPy call without executing authored code."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, "procedure-unresolved-by-lock-schema-resolver"
    bindings: dict[str, str] = {}
    calls: list[str] = []
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "scipy.stats":
                    if alias.asname is None:
                        bindings["scipy"] = "scipy"
                    else:
                        bindings[alias.asname] = "scipy.stats"
        elif isinstance(statement, ast.ImportFrom) and statement.level == 0:
            if statement.module == "scipy":
                for alias in statement.names:
                    if alias.name == "stats":
                        bindings[alias.asname or alias.name] = "scipy.stats"
            elif statement.module == "scipy.stats":
                for alias in statement.names:
                    candidate = f"scipy.stats.{alias.name}"
                    bindings[alias.asname or alias.name] = candidate

    def resolve_callable(node: ast.expr) -> str | None:
        attributes: list[str] = []
        while isinstance(node, ast.Attribute):
            attributes.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        resolved = bindings.get(node.id)
        if resolved is None:
            return None
        return ".".join((resolved, *reversed(attributes)))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        resolved_call = resolve_callable(node.func)
        if resolved_call is not None and resolved_call.startswith("scipy.stats."):
            calls.append(str(resolved_call))
    if not calls:
        return None, "procedure-unresolved-by-lock-schema-resolver"
    if len(calls) > 1:
        return None, "procedure-ambiguous-multiple-statistical-calls"
    if calls[0] not in registry:
        return None, "procedure-unavailable-to-closed-lock-schema"
    return calls[0], "lock-minted"


_V2_DISTRIBUTION_HELPERS = frozenset(
    f"scipy.stats.{distribution}.{method}"
    for distribution in ("t", "norm")
    for method in ("ppf", "cdf", "sf")
)


def _registered_dependence_callable_set_v2(source: str) -> tuple[tuple[str, ...] | None, str]:
    """Translate only the reviewed v2 procedure-set census into a lock record."""

    from sc_referee.dependence_recognition_v2.authority_lock import V2_PROCEDURES

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, "procedure-unresolved-by-lock-schema-resolver"
    bindings: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "scipy.stats":
                    bindings[alias.asname or "scipy"] = "scipy.stats" if alias.asname else "scipy"
        elif isinstance(statement, ast.ImportFrom) and statement.level == 0:
            if statement.module == "scipy":
                for alias in statement.names:
                    if alias.name == "stats":
                        bindings[alias.asname or alias.name] = "scipy.stats"
            elif statement.module == "scipy.stats":
                for alias in statement.names:
                    bindings[alias.asname or alias.name] = f"scipy.stats.{alias.name}"

    def resolve(node: ast.expr) -> str | None:
        attributes: list[str] = []
        while isinstance(node, ast.Attribute):
            attributes.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name) or node.id not in bindings:
            return None
        return ".".join((bindings[node.id], *reversed(attributes)))

    procedures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        resolved = resolve(node.func)
        if resolved is None or not resolved.startswith("scipy.stats."):
            continue
        if resolved in _V2_DISTRIBUTION_HELPERS:
            continue
        if resolved not in V2_PROCEDURES:
            return None, "procedure-unavailable-to-closed-lock-schema"
        variant = resolved
        if resolved == "scipy.stats.ttest_ind":
            for keyword in node.keywords:
                if (
                    keyword.arg == "equal_var"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is False
                ):
                    variant = "scipy.stats.ttest_ind:welch"
        procedures.append(variant)
    if not procedures:
        return None, "procedure-unresolved-by-lock-schema-resolver"
    if any(item in {"scipy.stats.binomtest", "scipy.stats.fisher_exact"} for item in procedures):
        if len(procedures) != 1:
            return None, "procedure-set-count-member-unsupported"
    ordered_unique = tuple(dict.fromkeys(procedures))
    return ordered_unique, "lock-minted"


def _description_authority_lock(
    *,
    case_id: str,
    case_root: Path,
    intake_row: Mapping[str, Any],
    intake_recorded_at: str,
    description_path: str,
    input_path: str,
) -> tuple[dict[str, Any] | None, str, str | None]:
    description = (case_root / description_path).read_text(encoding="utf-8")
    unit_column = _description_unit_column(description)
    if unit_column is None:
        return None, "unit-declaration-missing-or-malformed", None
    try:
        with (case_root / input_path).open("r", encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle, strict=True))
    except (OSError, StopIteration, UnicodeDecodeError, csv.Error):
        return None, "frozen-csv-header-unavailable", unit_column
    if (
        not header
        or len(header) != len(set(header))
        or any(not item for item in header)
        or unit_column not in header
    ):
        return None, "unit-column-absent-from-frozen-header", unit_column
    procedure, procedure_reason = _registered_dependence_callable(
        (case_root / "workflow/analysis.py").read_text(encoding="ascii")
    )
    if procedure is None:
        return None, procedure_reason, unit_column
    slug = case_id.removeprefix("case:")
    actor_id = f"scientist:dependence-free-author-{slug}"
    value: dict[str, Any] = {
        "lock_kind": LOCK_KIND,
        "case_id": case_id,
        "snapshot_digest": intake_row["expected_audit_snapshot_digest"],
        "intake_recorded_at": intake_recorded_at,
        "declared_execution_root": DECLARED_EXECUTION_ROOT,
        "records": [
            {
                "record_type": "analysis",
                "record_id": f"analysis:{slug}",
                "path": "workflow/analysis.py",
            },
            {
                "record_type": "procedure",
                "record_id": f"procedure:{slug}",
                "resolved_callable": procedure,
            },
            {
                "record_type": "result",
                "record_id": f"result:{slug}",
                "path": "results/report.md",
            },
            {
                "record_type": "human_method_authorization",
                "record_id": f"authorization:{slug}",
                "actor_id": actor_id,
                "authority_state": "authorized",
                "analysis_target_ref": {
                    "record_type": "analysis",
                    "record_id": f"analysis:{slug}",
                },
                "procedure_ref": {
                    "record_type": "procedure",
                    "record_id": f"procedure:{slug}",
                },
                "independent_unit_definition_id": stable_id(
                    "unit-definition", case_id, unit_column
                ),
                "authorized_key_columns": [unit_column],
                "input_path": input_path,
                "input_content_digest": intake_row["file_digests"][input_path],
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
    return value, "lock-minted", unit_column


def _description_v2_authority_lock(
    *,
    case_id: str,
    case_root: Path,
    intake_row: Mapping[str, Any],
    intake_recorded_at: str,
    description_path: str,
    input_path: str,
) -> tuple[dict[str, Any] | None, str, str | None]:
    """Translate the same declaration into the distinct development v2 line."""

    from sc_referee.dependence_recognition_v2.authority_lock import (
        build_dependence_v2_authorization_lock,
    )
    from sc_referee.dependence_recognition_v2.intake_declaration import translate_unit_declaration

    description_bytes = (case_root / description_path).read_bytes()
    translated = translate_unit_declaration(
        description_bytes,
        (case_root / input_path).read_bytes(),
        "growth-loop-standalone-v1",
    )
    if translated.reason is not None:
        return None, translated.reason, None
    unit_column = translated.unit_column
    assert unit_column is not None
    description = description_bytes.decode("utf-8")
    if len(_DESCRIPTION_ROW.findall(description)) != 1:
        return None, "unit-declaration-missing-or-malformed", unit_column
    procedures, reason = _registered_dependence_callable_set_v2(
        (case_root / "workflow/analysis.py").read_text(encoding="ascii")
    )
    if procedures is None:
        return None, reason, unit_column
    if (
        procedures[0] in {"scipy.stats.binomtest", "scipy.stats.fisher_exact"}
        and len(_DESCRIPTION_TRIAL_ROW.findall(description)) != 1
    ):
        return None, "count-procedure-trial-declaration-missing", unit_column
    return (
        build_dependence_v2_authorization_lock(
            case_id=case_id,
            snapshot_digest=str(intake_row["expected_audit_snapshot_digest"]),
            intake_recorded_at=intake_recorded_at,
            procedure=procedures[0] if len(procedures) == 1 else procedures,
            unit_column=unit_column,
            input_path=input_path,
            input_content_digest=str(intake_row["file_digests"][input_path]),
        ),
        "lock-minted",
        unit_column,
    )


def step_authority(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    if not config.requires_dependence_authority:
        raise LeanPipelineError("This envelope does not require a dependence authority step.")
    root = project_root / config.pipeline_relative
    authority_root = root / "authority"
    ledger_path = authority_root / "AUTHORITY_LEDGER.json"
    if ledger_path.exists():
        raise LeanPipelineError("The authority step already has output.")
    if (authority_root / "locks").exists():
        raise LeanPipelineError("The authority freeze directory already exists.")
    if config.dependence_v2_lock_line and not config.development_loop:
        raise LeanPipelineError("The v2 authority line is development-loop only.")
    if config.dependence_v2_lock_line and (authority_root / "locks-v2").exists():
        raise LeanPipelineError("The v2 authority freeze directory already exists.")
    _authoring_entry, protocol = _manifest_require(project_root, config, "authoring")
    _intake_entry, intake = _manifest_require(project_root, config, "intake")
    roles = {str(key): str(value) for key, value in protocol["case_role_assignments"].items()}
    intake_rows = {str(row["case_id"]): row for row in intake["entries"]}
    if set(intake_rows) != set(roles):
        raise LeanPipelineError("The authority step received a different admitted case set.")
    incoming_root = authority_root / "incoming"
    v2_values: dict[str, dict[str, Any]] = {}
    if config.dependence_authority_from_description:
        description_path = config.authored_data_description_path
        if description_path is None or incoming_root.exists():
            raise LeanPipelineError("Description-derived authority configuration is invalid.")
        incoming_root.mkdir(parents=True)
        generated_lock_names: set[str] = set()
        translation_by_case: dict[str, dict[str, Any]] = {}
        for case_id in sorted(roles):
            if intake_rows[case_id].get("intake_admission_state") == "refused_but_case_retained":
                continue
            slug = case_id.removeprefix("case:")
            case_root = root / "authoring" / "cases" / slug
            value, reason, declared_column = _description_authority_lock(
                case_id=case_id,
                case_root=case_root,
                intake_row=intake_rows[case_id],
                intake_recorded_at=str(intake["recorded_at"]),
                description_path=description_path,
                input_path=config.authored_input_csv_path,
            )
            description_bytes = (case_root / description_path).read_bytes()
            input_bytes = (case_root / config.authored_input_csv_path).read_bytes()
            translation = {
                "artifact_kind": "dependence_description_authority_translation",
                "translation_version": (
                    "2.0.0-development" if config.development_loop else "1.0.0"
                ),
                "case_id": case_id,
                "description_path": description_path,
                "description_content_digest": sha256_digest(description_bytes),
                "input_path": config.authored_input_csv_path,
                "input_content_digest": intake_rows[case_id]["file_digests"][
                    config.authored_input_csv_path
                ],
                "declared_column": declared_column,
                "translation_outcome": reason,
                "lock_digest": value.get("lock_digest") if value is not None else None,
                "role_information_used": False,
                "translated_at": _now(),
            }
            if config.development_loop:
                from sc_referee.dependence_recognition_v2.intake_declaration import (
                    receipt_dict,
                    translate_unit_declaration,
                )

                v1_receipt_source = translate_unit_declaration(
                    description_bytes,
                    input_bytes,
                    "growth-loop-standalone-v1",
                )
                translation.update(
                    {
                        "parsed_header_digest": v1_receipt_source.parsed_header_digest,
                        "lock_projection_digest": (
                            value.get("lock_digest") if value is not None else None
                        ),
                        "v1_declared_column": declared_column,
                        "v1_translation_outcome": reason,
                        "v1_lock_digest": (value.get("lock_digest") if value is not None else None),
                        "v1_lock_projection_digest": (
                            value.get("lock_digest") if value is not None else None
                        ),
                        "v1_translation_receipt": (
                            receipt_dict(v1_receipt_source) if value is not None else None
                        ),
                    }
                )
            if config.dependence_v2_lock_line:
                from sc_referee.dependence_recognition_v2.authority_lock import (
                    lock_projection as v2_lock_projection,
                )

                v2_value, v2_reason, v2_column = _description_v2_authority_lock(
                    case_id=case_id,
                    case_root=case_root,
                    intake_row=intake_rows[case_id],
                    intake_recorded_at=str(intake["recorded_at"]),
                    description_path=description_path,
                    input_path=config.authored_input_csv_path,
                )
                v2_receipt_source = translate_unit_declaration(
                    description_bytes,
                    input_bytes,
                    "growth-loop-standalone-v1",
                )
                v2_lock_projection_digest = (
                    semantic_digest(v2_lock_projection(v2_value)) if v2_value is not None else None
                )
                translation.update(
                    {
                        "v2_lock_line": "dependence_semantic_v2_growth_2",
                        "v2_declared_column": v2_column,
                        "v2_translation_outcome": v2_reason,
                        "v2_translation_reason": (
                            None if v2_reason == "lock-minted" else v2_reason
                        ),
                        "v2_translation_receipt": (
                            receipt_dict(v2_receipt_source) if v2_value is not None else None
                        ),
                        "v2_lock_digest": (
                            v2_value.get("lock_digest") if v2_value is not None else None
                        ),
                        "v2_lock_projection_digest": v2_lock_projection_digest,
                    }
                )
                if translation["parsed_header_digest"] is None:
                    translation["parsed_header_digest"] = v2_receipt_source.parsed_header_digest
                if translation["lock_projection_digest"] is None:
                    translation["lock_projection_digest"] = v2_lock_projection_digest
                if v2_value is not None:
                    v2_values[case_id] = v2_value
            _stamp_record_purpose(translation, config)
            translation["translation_digest"] = semantic_digest(translation)
            translation_path = authority_root / "translations" / f"{slug}.json"
            write_normalized_json_once(translation_path, translation)
            translation_by_case[case_id] = translation
            if value is not None:
                name = f"{slug}.json"
                write_normalized_json_once(incoming_root / name, value)
                generated_lock_names.add(name)
        expected_lock_names = generated_lock_names
    else:
        translation_by_case = {}
        expected_lock_names = {
            f"{case_id.removeprefix('case:')}.json"
            for case_id, role in roles.items()
            if role not in config.contract_free_roles
        }
    actual_lock_names = (
        {path.name for path in incoming_root.iterdir() if path.is_file() and not path.is_symlink()}
        if incoming_root.is_dir()
        else set()
    )
    if actual_lock_names != expected_lock_names or (
        incoming_root.exists()
        and any(not path.is_file() or path.is_symlink() for path in incoming_root.iterdir())
    ):
        raise LeanPipelineError("The authority inbox is not keyed by the exact opaque case set.")

    entries: list[dict[str, Any]] = []
    frozen_payloads: list[tuple[Path, bytes]] = []
    for case_id in sorted(roles):
        role = roles[case_id]
        slug = case_id.removeprefix("case:")
        incoming = authority_root / "incoming" / f"{slug}.json"
        if intake_rows[case_id].get("intake_admission_state") == "refused_but_case_retained":
            entries.append(
                {
                    "case_id": case_id,
                    "authority_state": "excluded_intake_refusal",
                    "frozen_lock_relative": None,
                    "lock_digest": None,
                    "approved_projection_digest": None,
                    "snapshot_digest": None,
                    "intake_admission_reason": intake_rows[case_id]["intake_admission_reason"],
                }
            )
            continue
        if role in config.contract_free_roles or (
            config.dependence_authority_from_description and not incoming.is_file()
        ):
            if incoming.exists() or incoming.is_symlink():
                raise LeanPipelineError(
                    "A contract-free case must not receive a fabricated authority lock."
                )
            entries.append(
                {
                    "case_id": case_id,
                    "authority_state": "unresolved_or_withheld",
                    "frozen_lock_relative": None,
                    "lock_digest": None,
                    "approved_projection_digest": None,
                    "snapshot_digest": None,
                    **(
                        {
                            "translation_digest": translation_by_case[case_id][
                                "translation_digest"
                            ],
                            "translation_outcome": translation_by_case[case_id][
                                "translation_outcome"
                            ],
                            **(
                                {
                                    "v1_translation_outcome": translation_by_case[case_id][
                                        "v1_translation_outcome"
                                    ],
                                    "v1_lock_digest": translation_by_case[case_id][
                                        "v1_lock_digest"
                                    ],
                                }
                                if config.development_loop
                                else {}
                            ),
                        }
                        if case_id in translation_by_case
                        else {}
                    ),
                }
            )
            continue
        if not incoming.is_file():
            raise LeanPipelineError(f"Case {case_id} lacks its separately approved authority lock.")

        case_root = root / "authoring" / "cases" / slug
        intake_row = intake_rows[case_id]
        admitted_digests = {
            **dict(intake_row["file_digests"]),
            **dict(intake_row.get("controller_material_file_digests", {})),
        }
        for path_value, digest in admitted_digests.items():
            path = case_root / str(path_value)
            if not path.is_file() or sha256_digest(path.read_bytes()) != digest:
                raise LeanPipelineError(f"Admitted authority-bound bytes drifted for {case_id}.")
        verified = verify_dependence_authorization_lock(
            incoming,
            expected_case_id=case_id,
            expected_snapshot_digest=str(intake_row["expected_audit_snapshot_digest"]),
            expected_intake_recorded_at=str(intake["recorded_at"]),
            source_paths=("workflow/analysis.py",),
            selected_report_path="results/report.md",
            material_input_digests=admitted_digests,
            forbidden_role_markers=config.roles,
        )
        relative = Path("authority") / "locks" / f"{slug}.json"
        frozen_payloads.append((root / relative, verified.canonical_payload))
        entries.append(
            {
                "case_id": case_id,
                "authority_state": "authorized",
                "frozen_lock_relative": relative.as_posix(),
                "lock_digest": verified.lock_digest,
                "approved_projection_digest": verified.approved_projection_digest,
                "snapshot_digest": verified.snapshot_digest,
                **(
                    {
                        "translation_digest": translation_by_case[case_id]["translation_digest"],
                        "translation_outcome": translation_by_case[case_id]["translation_outcome"],
                        **(
                            {
                                "v1_translation_outcome": translation_by_case[case_id][
                                    "v1_translation_outcome"
                                ],
                                "v1_lock_digest": translation_by_case[case_id]["v1_lock_digest"],
                            }
                            if config.development_loop
                            else {}
                        ),
                    }
                    if case_id in translation_by_case
                    else {}
                ),
            }
        )

    for path, payload in frozen_payloads:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(path, payload)
    if config.dependence_v2_lock_line:
        from sc_referee.dependence_recognition_v2.authority_lock import (
            verify_dependence_v2_authorization_lock,
        )

        entries_by_case = {str(item["case_id"]): item for item in entries}
        for case_id in sorted(roles):
            entry = entries_by_case[case_id]
            translation = translation_by_case.get(case_id, {})
            entry["v2_lock_line"] = "dependence_semantic_v2_growth_2"
            entry["v2_translation_outcome"] = translation.get(
                "v2_translation_outcome",
                "excluded-intake-refusal",
            )
            if case_id not in v2_values:
                entry.update(
                    {
                        "v2_authority_state": "unresolved_or_withheld",
                        "v2_frozen_lock_relative": None,
                        "v2_lock_digest": None,
                        "v2_approved_projection_digest": None,
                    }
                )
                continue
            slug = case_id.removeprefix("case:")
            staged = authority_root / "incoming-v2" / f"{slug}.json"
            write_normalized_json_once(staged, v2_values[case_id])
            case_root = root / "authoring" / "cases" / slug
            input_path = config.authored_input_csv_path
            try:
                with (case_root / input_path).open("r", encoding="utf-8", newline="") as handle:
                    header = tuple(next(csv.reader(handle, strict=True)))
            except (OSError, StopIteration, UnicodeDecodeError, csv.Error) as error:
                raise LeanPipelineError("The v2 authority header cannot replay.") from error
            verified_v2 = verify_dependence_v2_authorization_lock(
                staged,
                expected_case_id=case_id,
                expected_snapshot_digest=str(
                    intake_rows[case_id]["expected_audit_snapshot_digest"]
                ),
                expected_intake_recorded_at=str(intake["recorded_at"]),
                material_input_digests={
                    **dict(intake_rows[case_id]["file_digests"]),
                    **dict(intake_rows[case_id].get("controller_material_file_digests", {})),
                },
                frozen_input_headers={input_path: header},
                forbidden_role_markers=config.roles,
            )
            relative = Path("authority") / "locks-v2" / f"{slug}.json"
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_bytes(destination, verified_v2.canonical_payload)
            entry.update(
                {
                    "v2_authority_state": "authorized",
                    "v2_frozen_lock_relative": relative.as_posix(),
                    "v2_lock_digest": verified_v2.lock_digest,
                    "v2_approved_projection_digest": verified_v2.approved_projection_digest,
                }
            )
    ledger: dict[str, Any] = {
        "artifact_kind": "lean_pipeline_dependence_authority_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "authoring_protocol_digest": protocol["protocol_digest"],
        "intake_ledger_digest": intake["ledger_digest"],
        "intake_recorded_at": intake["recorded_at"],
        "entries": entries,
        "case_count": len(entries),
        "authorized_count": sum(item["authority_state"] == "authorized" for item in entries),
        "withheld_count": sum(
            item["authority_state"] == "unresolved_or_withheld" for item in entries
        ),
        "frozen_before_review": True,
        "frozen_at": _now(),
        "qualification_authority": "human_method_authorization_freeze_only",
    }
    if config.dependence_authority_from_description:
        ledger["authority_source"] = "post_intake_authored_data_description_projection"
    _stamp_record_purpose(ledger, config)
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)
    _manifest_record(
        project_root,
        config,
        "authority",
        digest=ledger["ledger_digest"],
        relative_path="authority/AUTHORITY_LEDGER.json",
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
    # A quote that is one unique byte substring of the file (for example a
    # sentence whose last line is only the first word of a longer file line)
    # widens to the complete lines covering that occurrence.
    text = "\n".join(lines)
    if quoted:
        first = text.find(quoted)
        if first != -1 and text.find(quoted, first + 1) == -1:
            start_line = text.count("\n", 0, first) + 1
            end_line = text.count("\n", 0, first + len(quoted)) + 1
            span["start_line"] = start_line
            span["end_line"] = end_line
            span["quoted_text"] = "\n".join(lines[start_line - 1 : end_line])
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
    return cast(dict[str, Any], anchored)


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
    task_payload = (_case_task_text(config, role).rstrip() + "\n").encode("utf-8")
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
    }
    for role_value in config.roles:
        forbidden_markers.add(role_value)
        forbidden_markers.add(role_value.replace("_", "-"))
        forbidden_markers.add(role_value.replace("-", "_"))
    workspace_manifest = build_blind_workspace(
        runner_source,
        preparation_root / "blind-workspace",
        preparation_root / "blind-workspace-manifest.json",
        [dict(item) for item in _visible_files(config)],
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
            for item in _visible_files(config)
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

    # The projection requires the workspace-payload case set to equal the packet case
    # set. An escalation call reviews a strict subset of cases, so restrict the payload
    # mapping to the subset here; the prompt below already iterates case_subset only.
    workspace_payloads = {case_id: workspace_payloads[case_id] for case_id in case_subset}
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
                and candidate.get("prompt") == prompt
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
    call_arguments = (
        config,
        participant,
        prompt,
        call_identity,
        review_root / "process-captures" / f"{label}-{participant.slug}",
    )
    call = (
        _call_cli(*call_arguments, response_schema=schema)
        if config.development_loop and config.enforce_cli_review_json_schema
        else _call_cli(*call_arguments)
    )
    if call["transport_error"] is not None:
        raise LeanPipelineError(
            f"The {label} review call failed and was retained: {call['transport_error']}"
        )
    raw_response = str(call["raw_response"]).encode("utf-8")
    response_stage = "json"
    try:
        parsed_payload = json.loads(raw_response)
        if not isinstance(parsed_payload, dict):
            raise ValueError("review response root is not an object")
        response_stage = "evidence-anchoring"
        anchored_payload = _anchor_review_spans(parsed_payload, workspace_payloads)
        response_stage = "response-schema"
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
    except (json.JSONDecodeError, ValueError, TypeError, KeyError, AttributeError) as error:
        if not (config.development_loop and label.startswith("primary") and len(case_subset) == 1):
            raise
        case_id = case_subset[0]
        refusal = {
            "case_id": case_id,
            "response_state": "review-response-malformed",
            "failure_class": (
                "invalid-json"
                if isinstance(error, json.JSONDecodeError)
                else "evidence-anchoring-failed"
                if response_stage == "evidence-anchoring"
                else "response-schema-invalid"
            ),
            "participant_id": participant.participant_id,
            "call_identity_id": call_identity,
            "prompt_digest": sha256_digest(prompt),
            "output_schema_digest": semantic_digest(schema),
            "shared_transcript_digest": sha256_digest(raw_response),
            "packet_digest": packets[case_id]["packet_digest"],
            "process_capture_digest": call.get("process_record", {}).get("capture_digest"),
        }
        refusal["refusal_digest"] = semantic_digest(refusal)
        return {
            "entries": [],
            "call_identity_id": call_identity,
            "prompt_digest": sha256_digest(prompt),
            "output_schema_digest": semantic_digest(schema),
            "shared_transcript_digest": sha256_digest(raw_response),
            "packet_digests": {case_id: packets[case_id]["packet_digest"]},
            "review_response_refusals": [refusal],
        }
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
    expected = config.expected_verdict(role)
    issue_clean = (
        entry["issue_class"] == config.canonical_issue_class
        if entry["verdict"] == "demonstrated_issue"
        else entry["issue_class"] is None
    )
    # A role whose sealed construction is deliberately unresolvable (two equally
    # authoritative scope records, a runtime-selected producer) is clean on its
    # verdict alone; raising the material question there is the correct review.
    questions_clean = (
        entry["unresolved_material_question_count"] == 0 or role in config.mq_tolerant_roles
    )
    return bool(entry["verdict"] == expected and issue_clean and questions_clean)


def _review_call_ledger_projection(call: dict[str, Any]) -> dict[str, Any]:
    projected = {
        key: call[key]
        for key in (
            "call_identity_id",
            "prompt_digest",
            "output_schema_digest",
            "shared_transcript_digest",
            "packet_digests",
        )
    }
    if call.get("review_response_refusals"):
        projected["review_response_refusals"] = call["review_response_refusals"]
    return projected


def _run_hostile_answer_key_review(
    project_root: Path,
    config: EnvelopeConfig,
    review_root: Path,
    case_order: list[str],
    roles: Mapping[str, str],
) -> dict[str, Any] | None:
    """Run the opt-in role-blind, per-case answer-key audit before blind review."""

    participant = config.hostile_answer_key_reviewer
    if participant is None:
        return None
    root = project_root / config.pipeline_relative
    retained_path = review_root / "hostile-answer-key" / "HOSTILE_REVIEW_LEDGER.json"
    retained = _load(retained_path) if retained_path.exists() else None
    if retained is not None:
        packet_version = str(retained.get("packet_version", HOSTILE_PACKET_V1))
    elif config.development_loop:
        packet_version = HOSTILE_PACKET_V2_RECEIPT
    else:
        packet_version = HOSTILE_PACKET_V1
    if packet_version not in {HOSTILE_PACKET_V1, HOSTILE_PACKET_V2_RECEIPT}:
        raise LeanPipelineError("The hostile answer-key packet version is unsupported.")
    authority = _load(root / "authority/AUTHORITY_LEDGER.json")
    all_authority_by_case = {str(entry["case_id"]): entry for entry in authority.get("entries", [])}
    if len(all_authority_by_case) != len(authority.get("entries", [])) or any(
        case_id not in all_authority_by_case for case_id in case_order
    ):
        raise LeanPipelineError("The hostile review authority states do not cover its cases.")
    authority_by_case = {case_id: all_authority_by_case[case_id] for case_id in case_order}

    def _prepare(case_id: str) -> dict[str, Any]:
        slug = case_id.removeprefix("case:")
        case_root = root / "authoring" / "cases" / slug
        visible: list[str] = []
        for item in _visible_files(config):
            path = str(item["path"])
            if path == "task.md":
                payload = (_case_task_text(config, roles[case_id]).rstrip() + "\n").encode("utf-8")
            else:
                payload = (case_root / path).read_bytes()
            visible.append(f"--- file {path} ---\n{payload.decode('utf-8')}")
        lock_path = root / "authority" / "locks" / f"{slug}.json"
        authority_state = authority_by_case[case_id].get("authority_state")
        if authority_state == "authorized":
            if not lock_path.is_file():
                raise LeanPipelineError("An authorized hostile-review case lacks its lock.")
            has_lock = True
        elif authority_state == "unresolved_or_withheld":
            if lock_path.exists() or lock_path.is_symlink():
                raise LeanPipelineError("A lock-less hostile-review case unexpectedly has a lock.")
            has_lock = False
        else:
            raise LeanPipelineError("The hostile review received an ineligible authority state.")
        lock_text = lock_path.read_text(encoding="utf-8") if has_lock else "NO LOCK MINTED"
        lock_question = (
            "(3) does the minted lock's unit-key authorization follow from the declaration alone?"
            if has_lock
            else "(3) no lock was minted; answer exactly not-applicable-no-lock."
        )
        prompt = (
            "You are a hostile, role-blind answer-key reviewer. Review exactly one case for "
            "repeated measurements from the same independent unit entered into a "
            "row-independent statistical procedure as if independent. "
            "The check's standard is whether the issue or its absence is demonstrated in "
            "the selected report. Answer: (1) is the declared independent-unit column "
            "consistent with the frozen data, considering both procedure arms; (2) is the "
            "issue or its absence demonstrated in the selected report; "
            + lock_question
            + "\n\n"
            + "\n\n".join(visible)
            + "\n\n--- minted authority lock ---\n"
            + lock_text
            + "\n\nReturn only JSON with exact keys declaration_consistent, "
            "selected_report_demonstration, lock_follows_declaration, and reasons. The first "
            "value is a boolean. lock_follows_declaration is a boolean when a lock is shown "
            "and exactly not-applicable-no-lock when no lock was minted. "
            "selected_report_demonstration is exactly issue, absence, or neither; reasons "
            "is a nonempty array of strings."
        )
        packet_digest: str | None = None
        if packet_version == HOSTILE_PACKET_V2_RECEIPT:
            translation_path = root / "authority" / "translations" / f"{slug}.json"
            if not translation_path.is_file():
                raise LeanPipelineError("A v2 hostile packet lacks its translation record.")
            translation = _load(translation_path)
            disclosure = {
                "v1_translation_outcome": translation.get("v1_translation_outcome"),
                "v1_lock_digest": translation.get("v1_lock_digest"),
                "v1_translation_receipt": translation.get("v1_translation_receipt"),
                "v2_translation_outcome": translation.get("v2_translation_outcome"),
                "v2_translation_reason": translation.get("v2_translation_reason"),
                "v2_lock_digest": translation.get("v2_lock_digest"),
                "v2_translation_receipt": translation.get("v2_translation_receipt"),
            }
            prompt = prompt.replace(
                "\n\nReturn only JSON",
                "\n\n--- deterministic translation receipt (lane-qualified) ---\n"
                + canonical_json(disclosure)
                + "\n\nReturn only JSON",
                1,
            )
            packet_digest = semantic_digest(
                {
                    "digest_domain": HOSTILE_PACKET_V2_DIGEST_DOMAIN,
                    "packet_version": packet_version,
                    "case_id": case_id,
                    "prompt": prompt,
                }
            )
        hostile_schema: dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "declaration_consistent",
                "selected_report_demonstration",
                "lock_follows_declaration",
                "reasons",
            ],
            "properties": {
                "declaration_consistent": {"type": "boolean"},
                "selected_report_demonstration": {
                    "type": "string",
                    "enum": ["issue", "absence", "neither"],
                },
                "lock_follows_declaration": (
                    {"type": "boolean"} if has_lock else {"const": "not-applicable-no-lock"}
                ),
                "reasons": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
            },
        }
        return {
            "case_id": case_id,
            "has_lock": has_lock,
            "prompt": prompt,
            "packet_version": packet_version,
            "packet_digest": packet_digest,
            "schema": hostile_schema,
            "session_id": str(
                uuid5(
                    NAMESPACE_URL,
                    f"sc-referee:dependence-free-hostile:{config.envelope_id}:{case_id}",
                )
            ),
            "capture_root": review_root / "hostile-answer-key" / "process-captures" / slug,
        }

    prepared = [_prepare(case_id) for case_id in case_order]
    if retained is not None:
        retained_entries = {str(item["case_id"]): item for item in retained.get("entries", [])}
        if set(retained_entries) != set(case_order) or any(
            retained_entries[str(item["case_id"])].get("prompt_digest")
            != sha256_digest(str(item["prompt"]))
            or (
                packet_version == HOSTILE_PACKET_V2_RECEIPT
                and retained_entries[str(item["case_id"])].get("packet_digest")
                != item["packet_digest"]
            )
            for item in prepared
        ):
            raise LeanPipelineError("The retained hostile answer-key prompts do not match.")
        supplied = retained.pop("ledger_digest", None)
        if supplied != semantic_digest(retained):
            raise LeanPipelineError("The retained hostile answer-key ledger does not replay.")
        retained["ledger_digest"] = supplied
        return retained

    def _run(prepared_case: dict[str, Any]) -> dict[str, Any]:
        case_id = str(prepared_case["case_id"])
        has_lock = bool(prepared_case["has_lock"])
        prompt = str(prepared_case["prompt"])
        session_id = str(prepared_case["session_id"])
        capture_root = cast(Path, prepared_case["capture_root"])
        call = (
            _call_cli(
                config,
                participant,
                prompt,
                session_id,
                capture_root,
                response_schema=cast(dict[str, Any], prepared_case["schema"]),
            )
            if config.development_loop and config.enforce_cli_review_json_schema
            else _call_cli(config, participant, prompt, session_id, capture_root)
        )
        if call["transport_error"] is not None:
            raise LeanPipelineError(
                f"The hostile answer-key call failed and was retained for {case_id}."
            )
        try:
            answer = json.loads(_strip_single_fence(str(call["raw_response"])))
        except json.JSONDecodeError as error:
            raise LeanPipelineError("The hostile answer-key response is not JSON.") from error
        if (
            not isinstance(answer, dict)
            or set(answer)
            != {
                "declaration_consistent",
                "selected_report_demonstration",
                "lock_follows_declaration",
                "reasons",
            }
            or not isinstance(answer["declaration_consistent"], bool)
            or (has_lock and not isinstance(answer["lock_follows_declaration"], bool))
            or (not has_lock and answer["lock_follows_declaration"] != "not-applicable-no-lock")
            or answer["selected_report_demonstration"] not in {"issue", "absence", "neither"}
            or not isinstance(answer["reasons"], list)
            or not answer["reasons"]
            or any(
                not isinstance(reason, str) or not reason.strip() for reason in answer["reasons"]
            )
        ):
            raise LeanPipelineError("The hostile answer-key response is outside its closed shape.")
        expected_demonstration = (
            "issue"
            if config.expected_verdict(roles[case_id]) == "demonstrated_issue"
            else "absence"
        )
        burn_reasons = []
        if not answer["declaration_consistent"]:
            burn_reasons.append("unit-declaration-inconsistent")
        if answer["selected_report_demonstration"] != expected_demonstration:
            burn_reasons.append("answer-key-refuted")
        if has_lock and answer["lock_follows_declaration"] is False:
            burn_reasons.append("unit-key-authorization-not-derived-from-declaration-alone")
        entry = {
            "case_id": case_id,
            "answer": answer,
            "burned_before_blind_review": bool(burn_reasons),
            "burn_reasons": burn_reasons,
            "prompt_digest": sha256_digest(prompt),
            "response_digest": sha256_digest(str(call["raw_response"])),
            "process_capture_digest": call["process_record"]["capture_digest"],
        }
        if packet_version == HOSTILE_PACKET_V2_RECEIPT:
            entry.update(
                {
                    "packet_version": packet_version,
                    "packet_digest": prepared_case["packet_digest"],
                }
            )
        entry["entry_digest"] = semantic_digest(entry)
        return entry

    entries = _run_stage_model_calls(config, _run, prepared)
    ledger: dict[str, Any] = {
        "artifact_kind": "dependence_free_hostile_answer_key_ledger",
        "ledger_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "reviewer": participant.to_dict(),
        "role_blind": True,
        "one_stateless_call_per_case": True,
        "entries": entries,
        "burned_case_ids": [
            entry["case_id"] for entry in entries if entry["burned_before_blind_review"]
        ],
        "recorded_at": _now(),
        "qualification_authority": "none_development_answer_key_screen_only",
    }
    _stamp_record_purpose(ledger, config)
    if packet_version == HOSTILE_PACKET_V2_RECEIPT:
        ledger["packet_version"] = packet_version
        ledger["packet_digest_domain"] = HOSTILE_PACKET_V2_DIGEST_DOMAIN
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(
        review_root / "hostile-answer-key" / "HOSTILE_REVIEW_LEDGER.json", ledger
    )
    return ledger


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
            keep = child.name in {
                "process-captures",
                "hostile-answer-key",
            } or child.name.startswith(("packets-", "prompt-"))
            if not keep:
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    calibrations = ensure_calibrations(project_root, config)
    _auth_entry, protocol = _manifest_require(project_root, config, "authoring")
    _intake_entry, intake = _manifest_require(project_root, config, "intake")
    authority = None
    if config.requires_dependence_authority:
        _authority_entry, authority = _manifest_require(project_root, config, "authority")
        if authority.get("frozen_before_review") is not True:
            raise LeanPipelineError("Dependence authority was not frozen before review.")
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    intake_rows = {str(row["case_id"]): row for row in intake["entries"]}
    review_root.mkdir(parents=True, exist_ok=True)

    preparations = [
        _prepare_blind_case(
            project_root, config, review_root, case_id, roles[case_id], intake_rows[case_id]
        )
        for case_id in sorted(roles)
        if intake_rows[case_id].get("intake_admission_state") != "refused_but_case_retained"
    ]
    case_order = [str(item["case_id"]) for item in preparations]
    workspace_payloads: dict[str, dict[str, bytes]] = {}
    for item in preparations:
        case_id = str(item["case_id"])
        workspace_root = review_root / str(item["workspace_relative"])
        workspace_payloads[case_id] = {
            str(entry["path"]): (workspace_root / str(entry["path"])).read_bytes()
            for entry in _visible_files(config)
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
        **(
            {
                "role_expected_verdict_map": {
                    role: config.expected_verdict(role) for role in sorted(set(roles.values()))
                },
                "role_label_status_map": {
                    role: config.label_status(role) for role in sorted(set(roles.values()))
                },
            }
            if config.freeze_role_key_in_review_protocol
            else {}
        ),
        "escalation_policy": (
            "One merged blind review per case; a second blind review from the "
            "escalation reviewer runs only for non-clean cases per ADR-0067, and a "
            "case whose two reviews genuinely disagree is retained as unresolved."
        ),
        "frozen_at": _now(),
        "qualification_authority": "none_review_protocol_only",
    }
    if authority is not None:
        review_protocol["authority_ledger_digest"] = authority["ledger_digest"]
    _stamp_record_purpose(review_protocol, config)
    review_protocol["protocol_digest"] = semantic_digest(review_protocol)
    write_normalized_json_once(review_root / "REVIEW_PROTOCOL.json", review_protocol)

    hostile = _run_hostile_answer_key_review(project_root, config, review_root, case_order, roles)
    burned_case_ids = set((hostile or {}).get("burned_case_ids", []))
    blind_case_order = [case_id for case_id in case_order if case_id not in burned_case_ids]

    review_call_binding = (
        semantic_digest(
            {
                "detector_tuple_digest": protocol["detector_tuple_digest"],
                "role_expected_verdict_map": review_protocol["role_expected_verdict_map"],
                "role_label_status_map": review_protocol["role_label_status_map"],
            }
        )
        if config.freeze_role_key_in_review_protocol
        else str(protocol["detector_tuple_digest"])
    )
    if config.stateless_review_per_case:

        def _run_primary(case_id: str) -> dict[str, Any]:
            return _run_review_call(
                project_root,
                config,
                review_root,
                config.reviewer,
                [case_id],
                preparations_by_case,
                workspace_payloads,
                review_call_binding,
                f"primary-{case_id.removeprefix('case:')}",
            )

        primary_calls = _run_stage_model_calls(config, _run_primary, blind_case_order)
        primary = {
            "entries": [
                {**entry, "review_role": "primary"}
                for call in primary_calls
                for entry in call["entries"]
            ],
            "per_case_calls": [_review_call_ledger_projection(call) for call in primary_calls],
            "review_response_refusals": [
                refusal
                for call in primary_calls
                for refusal in call.get("review_response_refusals", [])
            ],
        }
    else:
        primary = _run_review_call(
            project_root,
            config,
            review_root,
            config.reviewer,
            blind_case_order,
            preparations_by_case,
            workspace_payloads,
            review_call_binding,
            "primary",
        )
    primary_by_case = {str(entry["case_id"]): entry for entry in primary["entries"]}
    review_response_refusals = list(primary.get("review_response_refusals", []))
    malformed_case_ids = {
        str(entry["case_id"])
        for entry in review_response_refusals
        if entry.get("response_state") == "review-response-malformed"
    }
    burned_case_ids.update(malformed_case_ids)
    non_clean = sorted(
        case_id
        for case_id, entry in primary_by_case.items()
        if not _entry_clean(config, entry, roles[case_id])
    )
    escalation: dict[str, Any] | None = None
    if non_clean and not config.authored_role_ratification:
        if config.stateless_review_per_case:
            escalation_calls = [
                _run_review_call(
                    project_root,
                    config,
                    review_root,
                    config.escalation_reviewer,
                    [case_id],
                    preparations_by_case,
                    workspace_payloads,
                    review_call_binding,
                    f"escalation-{case_id.removeprefix('case:')}",
                )
                for case_id in non_clean
            ]
            escalation = {
                "entries": [
                    {**entry, "review_role": "escalation"}
                    for call in escalation_calls
                    for entry in call["entries"]
                ],
                "per_case_calls": [
                    {
                        key: call[key]
                        for key in (
                            "call_identity_id",
                            "prompt_digest",
                            "output_schema_digest",
                            "shared_transcript_digest",
                            "packet_digests",
                        )
                    }
                    for call in escalation_calls
                ],
            }
        else:
            escalation = _run_review_call(
                project_root,
                config,
                review_root,
                config.escalation_reviewer,
                non_clean,
                preparations_by_case,
                workspace_payloads,
                review_call_binding,
                "escalation",
            )
    escalation_by_case = {
        str(entry["case_id"]): entry for entry in (escalation or {}).get("entries", [])
    }
    unblinding: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for case_id in case_order:
        role = roles[case_id]
        if case_id in malformed_case_ids:
            unblinding.append(
                {
                    "case_id": case_id,
                    "case_role": role,
                    "expected_verdict": config.expected_verdict(role),
                    "primary_verdict": None,
                    "primary_issue_class": None,
                    "primary_clean": None,
                    "escalation_verdict": None,
                    "escalation_clean": None,
                    "review_response_state": "review-response-malformed",
                    "resolution": "burned_review_response_malformed",
                }
            )
            continue
        if case_id in burned_case_ids:
            unblinding.append(
                {
                    "case_id": case_id,
                    "case_role": role,
                    "expected_verdict": config.expected_verdict(role),
                    "primary_verdict": None,
                    "primary_issue_class": None,
                    "primary_clean": None,
                    "escalation_verdict": None,
                    "escalation_clean": None,
                    "resolution": "burned_by_hostile_answer_key_review",
                }
            )
            continue
        primary_entry = primary_by_case[case_id]
        primary_clean = _entry_clean(config, primary_entry, role)
        if config.authored_role_ratification:
            resolution = "authored_role_ratified" if primary_clean else "authored_role_refuted"
            unblinding.append(
                {
                    "case_id": case_id,
                    "case_role": role,
                    "expected_verdict": config.expected_verdict(role),
                    "primary_verdict": primary_entry["verdict"],
                    "primary_issue_class": primary_entry["issue_class"],
                    "primary_clean": primary_clean,
                    "escalation_verdict": None,
                    "escalation_clean": None,
                    "resolution": resolution,
                }
            )
            continue
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
                "expected_verdict": config.expected_verdict(role),
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
        "primary_call": (
            {"per_case_calls": primary["per_case_calls"]}
            if config.stateless_review_per_case
            else {
                key: primary[key]
                for key in (
                    "call_identity_id",
                    "prompt_digest",
                    "output_schema_digest",
                    "shared_transcript_digest",
                    "packet_digests",
                )
            }
        ),
        "escalation_call": (
            (
                {"per_case_calls": escalation["per_case_calls"]}
                if config.stateless_review_per_case
                else {
                    key: escalation[key]
                    for key in (
                        "call_identity_id",
                        "prompt_digest",
                        "output_schema_digest",
                        "shared_transcript_digest",
                        "packet_digests",
                    )
                }
            )
            if escalation is not None
            else None
        ),
        "entries": primary["entries"] + (escalation or {}).get("entries", []),
        "unblinding_record": unblinding,
        "escalation_ran": escalation is not None,
        "unresolved_case_ids": unresolved,
        "burned_case_ids": sorted(burned_case_ids),
        "recorded_at": _now(),
        "qualification_authority": "none_lean_review_only",
    }
    if authority is not None:
        ledger["authority_ledger_digest"] = authority["ledger_digest"]
    if hostile is not None:
        ledger["hostile_answer_key_ledger_digest"] = hostile["ledger_digest"]
    if review_response_refusals:
        ledger["review_response_refusals"] = review_response_refusals
    _stamp_record_purpose(ledger, config)
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
    intake_refused: dict[str, dict[str, Any]] = {}
    if config.development_loop:
        _intake_entry, intake_ledger = _manifest_require(project_root, config, "intake")
        intake_refused = {
            str(row["case_id"]): row
            for row in intake_ledger["entries"]
            if row.get("intake_admission_state") == "refused_but_case_retained"
        }
    if review_ledger["unresolved_case_ids"]:
        raise LeanPipelineError("Labels cannot freeze while unresolved cases are retained.")
    resolutions = {
        str(row["case_id"]): str(row["resolution"]) for row in review_ledger["unblinding_record"]
    }
    resolving_role = {
        case_id: (
            None
            if resolution
            in {"burned_by_hostile_answer_key_review", "burned_review_response_malformed"}
            else "primary"
            if resolution in {"clean", "authored_role_ratified", "authored_role_refuted"}
            else "escalation"
        )
        for case_id, resolution in resolutions.items()
    }
    malformed_refusals = {
        str(entry["case_id"]): entry
        for entry in review_ledger.get("review_response_refusals", [])
        if entry.get("response_state") == "review-response-malformed"
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
    for case_id, intake_row in sorted(intake_refused.items()):
        role = roles[case_id]
        label_rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "label_status": config.label_status(role),
                "issue_class": (
                    config.canonical_issue_class
                    if config.label_status(role) == "positive_demonstrated"
                    else None
                ),
                "measurement_state": "refused_at_intake",
                "intake_admission_reason": intake_row["intake_admission_reason"],
                "review_basis": "intake_refusal_retained_without_review",
                "review_id": None,
                "review_digest": None,
                "reviewer_model_family": None,
                "agent_only_disclosure": "Refused at intake and excluded from measurement.",
            }
        )
    for case_id, review_role in resolving_role.items():
        if review_role is not None:
            continue
        role = roles[case_id]
        label_status = config.label_status(role)
        malformed = resolutions[case_id] == "burned_review_response_malformed"
        refusal = malformed_refusals.get(case_id)
        if malformed and refusal is None:
            raise LeanPipelineError("A malformed-review burn lacks its retained refusal record.")
        label_rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "label_status": label_status,
                "issue_class": (
                    config.canonical_issue_class
                    if label_status == "positive_demonstrated"
                    else None
                ),
                "measurement_state": (
                    "burned_review_response_malformed"
                    if malformed
                    else "burned_before_blind_review"
                ),
                "review_basis": (
                    "primary_blind_review_response_malformed_retained_without_label"
                    if malformed
                    else "hostile_answer_key_review_refuted_frozen_role"
                ),
                "review_id": None,
                "review_digest": (
                    refusal["refusal_digest"]
                    if refusal is not None
                    else review_ledger["hostile_answer_key_ledger_digest"]
                ),
                "reviewer_model_family": None,
                "agent_only_disclosure": (
                    "Primary blind-review output was malformed; no response content was parsed "
                    "as a label, and the case was burned before measurement."
                    if malformed
                    else "Burned before blind review; authored role retained."
                ),
            }
        )
    for entry in review_ledger["entries"]:
        case_id = str(entry["case_id"])
        if str(entry["review_role"]) != resolving_role[case_id]:
            continue
        role = roles[case_id]
        label_status = config.label_status(role)
        label_rows.append(
            {
                "case_id": case_id,
                "case_role": role,
                "label_status": label_status,
                "issue_class": (
                    config.canonical_issue_class
                    if label_status == "positive_demonstrated"
                    else None
                ),
                "review_basis": "single_calibrated_blind_review_adr_0067",
                **(
                    {
                        "measurement_state": (
                            "burned_refuted_authored_role"
                            if resolutions[case_id] == "authored_role_refuted"
                            else "eligible"
                        )
                    }
                    if config.authored_role_ratification
                    else {}
                ),
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
    if len(label_rows) != len(resolving_role) + len(intake_refused):
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
    _stamp_record_purpose(ledger, config)
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


def _write_false_accusation_halt(
    output_root: Path, config: EnvelopeConfig, row: Mapping[str, Any]
) -> None:
    halt = {
        "artifact_kind": "dependence_growth_loop_false_accusation_halt",
        "halt_version": "1.0.0",
        "envelope_id": config.envelope_id,
        "case_id": row["case_id"],
        "frozen_label_status": row["frozen_label_status"],
        "case_result_digest": row["case_result_digest"],
        "rule": "any_accusation_on_frozen_negative_halts_without_reclassification",
        "reclassification_permitted": False,
        "halted_at": _now(),
    }
    _stamp_record_purpose(halt, config)
    halt["halt_digest"] = semantic_digest(halt)
    write_normalized_json(output_root / "FALSE_ACCUSATION_HALT.json", halt)


def _development_nonpositive_outcome(
    *, expected_positive: bool, shadow_payload: Mapping[str, Any] | None, has_authority: bool
) -> str:
    state = str((shadow_payload or {}).get("state", ""))
    observations = (shadow_payload or {}).get("observations", [])
    covered = any(
        isinstance(item, dict)
        and (item.get("observed_operand") or {}).get("value")
        == "one_analyzed_row_per_authorized_independent_unit"
        for item in observations
    )
    if not has_authority:
        subtype = "no_authority"
    elif covered:
        subtype = "covered_negative"
    elif state == "ambiguous":
        subtype = "ambiguous"
    else:
        subtype = "unsupported"
    return (
        f"missed_{subtype}"
        if expected_positive
        else ("true_negative" if subtype == "covered_negative" else f"abstained_{subtype}")
    )


def step_detector(project_root: Path, config: EnvelopeConfig) -> dict[str, Any]:
    root = project_root / config.pipeline_relative
    output_root = root / "detector-run"
    final_ledger_path = output_root / "DETECTOR_RUN_LEDGER.json"
    if final_ledger_path.exists():
        raise LeanPipelineError("The detector step already has output.")
    if (output_root / "FALSE_ACCUSATION_HALT.json").exists():
        raise LeanPipelineError("The development growth loop remains halted on false accusation.")
    _auth_entry, protocol = _manifest_require(project_root, config, "authoring")
    _label_entry, label_ledger = _manifest_require(project_root, config, "labels")
    if label_ledger["detector_output_observed"] is not False:
        raise LeanPipelineError("Labels were not frozen before detector observation.")
    detector_tuple = protocol["detector_tuple"]
    detector_id = str(detector_tuple.get("detector_id", config.detector_id))
    if detector_id != config.detector_id:
        raise LeanPipelineError("The frozen detector id differs from the envelope configuration.")
    authority_entries: dict[str, dict[str, Any]] = {}
    authority_ledger: dict[str, Any] | None = None
    if config.requires_dependence_authority:
        _authority_entry, authority_ledger = _manifest_require(project_root, config, "authority")
        _review_entry, review_ledger = _manifest_require(project_root, config, "review")
        if review_ledger.get("authority_ledger_digest") != authority_ledger["ledger_digest"]:
            raise LeanPipelineError("The detector authority digest differs from blind review.")
        authority_entries = {
            str(item["case_id"]): item for item in authority_ledger.get("entries", [])
        }
        if len(authority_entries) != len(authority_ledger.get("entries", [])):
            raise LeanPipelineError("The authority ledger repeats an opaque case id.")
    registry_path = (
        project_root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
    )
    if sha256_digest(registry_path.read_bytes()) != detector_tuple["registry_content_digest"]:
        raise LeanPipelineError(
            "The current check registry drifted from the frozen detector tuple."
        )
    roles = {str(k): str(v) for k, v in protocol["case_role_assignments"].items()}
    if config.requires_dependence_authority and set(authority_entries) != set(roles):
        raise LeanPipelineError("The authority ledger does not cover the exact opaque case set.")
    labels_by_case = {str(row["case_id"]): row for row in label_ledger["entries"]}
    intake_by_case: dict[str, dict[str, Any]] = {}
    if config.record_expected_audit_snapshot_digest:
        _intake_entry, intake_ledger = _manifest_require(project_root, config, "intake")
        intake_by_case = {str(row["case_id"]): row for row in intake_ledger.get("entries", [])}
        if set(intake_by_case) != set(roles):
            raise LeanPipelineError("The intake snapshot bindings cover the wrong case set.")
    schema_root = project_root / SCHEMA_RELATIVE
    output_root.mkdir(parents=True, exist_ok=True)
    case_result_root = output_root / "case-results"
    case_result_root.mkdir(exist_ok=True)
    rows: list[dict[str, Any]] = []
    if config.dependence_v2_development_shadow and not config.development_loop:
        raise LeanPipelineError(
            "The dependence v2 shadow is restricted to development-loop envelopes."
        )
    for case_id in sorted(roles):
        slug = case_id.removeprefix("case:")
        role = roles[case_id]
        retained_path = case_result_root / f"{slug}.json"
        if retained_path.exists():
            retained = _load(retained_path)
            supplied = retained.pop("case_result_digest", None)
            if supplied != semantic_digest(retained):
                raise LeanPipelineError("A retained per-case detector result does not replay.")
            retained["case_result_digest"] = supplied
            if retained.get("scientific_label_ledger_digest") != label_ledger[
                "ledger_digest"
            ] or retained.get("authority_ledger_digest") != (authority_ledger or {}).get(
                "ledger_digest"
            ):
                raise LeanPipelineError("A retained per-case detector result has stale bindings.")
            if (
                retained.get("comparison_outcome") == "false_accusation"
                and config.halt_on_false_accusation
            ):
                _write_false_accusation_halt(output_root, config, retained)
                raise LeanPipelineError(
                    f"development growth loop halted on false accusation for {case_id}"
                )
            if config.dependence_v2_development_shadow and retained.get(
                "development_shadow_adapter"
            ) != _dependence_v2_identity(config):
                raise LeanPipelineError(
                    "A retained detector result has stale dependence v2 shadow identity."
                )
            rows.append(retained)
            continue
        if labels_by_case[case_id].get("measurement_state") == "refused_at_intake":
            refused_row = {
                "case_id": case_id,
                "case_role": role,
                "frozen_label_status": str(labels_by_case[case_id]["label_status"]),
                "measurement_state": "refused_at_intake",
                "intake_admission_reason": labels_by_case[case_id]["intake_admission_reason"],
                "comparison_outcome": "refused_at_intake",
                "finding_candidate_count": 0,
                "detector_positive": False,
                "production_findings": 0,
                "project_code_executions": 0,
                "replay_equal": False,
                "shadow_payload": None,
                "scientific_label_ledger_digest": label_ledger["ledger_digest"],
                "authority_ledger_digest": (authority_ledger or {}).get("ledger_digest"),
                **_dependence_v2_row_identity(config),
            }
            _stamp_record_purpose(refused_row, config)
            refused_row["case_result_digest"] = semantic_digest(refused_row)
            write_normalized_json_once(retained_path, refused_row)
            rows.append(refused_row)
            continue
        if str(labels_by_case[case_id].get("measurement_state", "eligible")).startswith("burned"):
            burned_row = {
                "case_id": case_id,
                "case_role": role,
                "frozen_label_status": str(labels_by_case[case_id]["label_status"]),
                "measurement_state": labels_by_case[case_id]["measurement_state"],
                "contract_candidate_id": None,
                "method_contract_applied": False,
                "finding_candidate_count": 0,
                "detector_positive": False,
                "comparison_outcome": "burned_before_measurement",
                "production_findings": 0,
                "project_code_executions": 0,
                "replay_equal": False,
                "shadow_payload": None,
                "scientific_label_ledger_digest": label_ledger["ledger_digest"],
                "authority_ledger_digest": (authority_ledger or {}).get("ledger_digest"),
                **_dependence_v2_row_identity(config),
            }
            _stamp_record_purpose(burned_row, config)
            burned_row["case_result_digest"] = semantic_digest(burned_row)
            write_normalized_json_once(retained_path, burned_row)
            rows.append(burned_row)
            continue
        case_source = root / "authoring" / "cases" / slug
        case_root = output_root / "runs" / slug
        repository = case_root / "project"
        shutil.copytree(case_source, repository)
        task_payload = (_case_task_text(config, role).rstrip() + "\n").encode("utf-8")
        atomic_write_bytes(repository / "task.md", task_payload)
        # A contract-free role has no human-authorized method choice to freeze:
        # its expected detector behavior is abstention, so the audit runs
        # without a method-contract lock and can only ever come back negative
        # or, if it fires, count as a false accusation like any other control.
        contract_free = role in config.contract_free_roles
        candidate_id = None if contract_free else config.candidate_by_role[role]
        contract_lock: Path | None = None
        dependence_lock: Path | None = None
        if config.requires_dependence_authority:
            authority_entry = authority_entries.get(case_id)
            if authority_entry is None:
                raise LeanPipelineError(f"The authority ledger omits case {case_id}.")
            if authority_entry.get("authority_state") == "authorized":
                if authority_ledger is None:
                    raise LeanPipelineError("An authorized case has no authority ledger.")
                relative = authority_entry.get("frozen_lock_relative")
                if not isinstance(relative, str):
                    raise LeanPipelineError("An authorized case lacks its frozen lock path.")
                expected_relative = f"authority/locks/{slug}.json"
                if relative != expected_relative:
                    raise LeanPipelineError(
                        "An authority lock path is outside its opaque case key."
                    )
                dependence_lock = root / relative
                material_digests = {
                    path_value: sha256_digest((repository / path_value).read_bytes())
                    for path_value in config.material_input_paths
                    if (repository / path_value).is_file()
                }
                verified_lock = verify_dependence_authorization_lock(
                    dependence_lock,
                    expected_case_id=case_id,
                    expected_snapshot_digest=str(authority_entry["snapshot_digest"]),
                    expected_intake_recorded_at=str(authority_ledger["intake_recorded_at"]),
                    source_paths=("workflow/analysis.py",),
                    selected_report_path="results/report.md",
                    material_input_digests=material_digests,
                    forbidden_role_markers=config.roles,
                )
                if verified_lock.lock_digest != authority_entry.get(
                    "lock_digest"
                ) or verified_lock.approved_projection_digest != authority_entry.get(
                    "approved_projection_digest"
                ):
                    raise LeanPipelineError("The frozen authority lock drifted after review.")
            elif authority_entry.get("authority_state") != "unresolved_or_withheld":
                raise LeanPipelineError("The authority ledger contains an unknown state.")
            if not config.dependence_authority_from_description and contract_free != (
                dependence_lock is None
            ):
                raise LeanPipelineError(
                    "The method-contract and dependence-authority states do not align."
                )
        if not contract_free:
            contract = run_method_contract(
                repository,
                "task.md",
                case_root / "contract",
                schema_root,
                profile={
                    "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
                    "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
                    "check_id": config.check_id,
                    "candidate_id": candidate_id,
                },
                actor_id=f"scientist:lean-pipeline-{config.envelope_id}",
            )
            if contract["findings"]:
                raise LeanPipelineError(f"The method-contract step emitted findings for {case_id}.")
            contract_lock = case_root / "contract" / "semantic.lock.json"
        development_v2_payloads: list[dict[str, Any]] = []
        v2_lock: Path | None = None
        v2_authority_reason: str | None = None
        if config.dependence_v2_development_shadow:
            authority_entry = authority_entries.get(case_id)
            if authority_entry is None:
                raise LeanPipelineError("The v2 shadow has no authority-ledger entry.")
            v2_relative = authority_entry.get("v2_frozen_lock_relative")
            if isinstance(v2_relative, str):
                expected_v2_relative = f"authority/locks-v2/{slug}.json"
                if v2_relative != expected_v2_relative:
                    raise LeanPipelineError("A v2 lock path is outside its opaque case key.")
                v2_lock = root / v2_relative
            else:
                outcome = authority_entry.get("v2_translation_outcome")
                if isinstance(outcome, str) and outcome in {
                    "count-procedure-trial-declaration-missing",
                }:
                    v2_authority_reason = outcome
        evaluation_observer = _dependence_v2_observer(
            config,
            development_v2_payloads,
            lock_path=v2_lock,
            expected_case_id=case_id,
            expected_intake_recorded_at=(
                str(authority_ledger["intake_recorded_at"])
                if authority_ledger is not None
                else None
            ),
            authority_refusal_reason=v2_authority_reason,
        )

        try:
            bundle = run_audit(
                repository,
                case_root / "audit",
                schema_root,
                report="results/report.md",
                method_contract_lock=contract_lock,
                material_inputs=config.material_input_paths,
                dependence_authorization_lock=dependence_lock,
                dependence_authorization_case_id=(case_id if dependence_lock is not None else None),
                evaluation_inspection_observer=evaluation_observer,
            )
        except (Exception, RecursionError) as error:
            if not config.development_loop:
                raise
            failure_row = {
                "case_id": case_id,
                "case_role": role,
                "frozen_label_status": str(labels_by_case[case_id]["label_status"]),
                "contract_candidate_id": candidate_id,
                "method_contract_applied": not contract_free,
                "finding_candidate_count": 0,
                "detector_positive": False,
                "comparison_outcome": (
                    "missed_detector_exception"
                    if labels_by_case[case_id]["label_status"] == "positive_demonstrated"
                    else "detector_exception"
                ),
                "production_findings": 0,
                "project_code_executions": 0,
                "replay_equal": False,
                "detector_failure_class": type(error).__name__,
                "shadow_payload": {
                    "outcome": "unsupported",
                    "coverage_class": "detector-case-exception",
                    "reason_codes": ["detector-case-exception"],
                },
                "scientific_label_ledger_digest": label_ledger["ledger_digest"],
                "authority_ledger_digest": (authority_ledger or {}).get("ledger_digest"),
                **_dependence_v2_row_identity(config),
            }
            _stamp_record_purpose(failure_row, config)
            failure_row["case_result_digest"] = semantic_digest(failure_row)
            write_normalized_json_once(retained_path, failure_row)
            rows.append(failure_row)
            continue
        if config.record_expected_audit_snapshot_digest:
            audit_lock = _load(case_root / "audit" / "semantic.lock.json")
            if audit_lock.get("snapshot_digest") != intake_by_case[case_id].get(
                "expected_audit_snapshot_digest"
            ):
                raise LeanPipelineError("The audit snapshot drifted from the intake-bound digest.")
        replayed = replay(
            case_root / "audit" / "semantic.lock.json", case_root / "replay", schema_root
        )
        if replayed["detector_results"] != bundle["detector_results"]:
            raise LeanPipelineError(f"The detector run does not replay for {case_id}.")
        fired = [
            result
            for result in bundle.get("detector_results", [])
            if result.get("detector_id") == detector_id
            and result.get("state") in {"evaluation_finding_candidate", "finding_candidate"}
        ]
        label_status = str(labels_by_case[case_id]["label_status"])
        detector_positive = bool(fired)
        expected_positive = label_status == "positive_demonstrated"
        audit_lock = _load(case_root / "audit" / "semantic.lock.json")
        shadow_modules = [
            item
            for item in audit_lock.get("scientific_check_registry", {})
            .get("evaluation", {})
            .get("modules", [])
            if item.get("check_id") == config.check_id
        ]
        shadow_payload = shadow_modules[0] if len(shadow_modules) == 1 else None
        development_v2_shadow_payload: dict[str, Any] | None = None
        development_v2_comparison_outcome: str | None = None
        if config.dependence_v2_development_shadow:
            if len(development_v2_payloads) != 1:
                raise LeanPipelineError(
                    "The development v2 shadow did not inspect exactly one frozen context."
                )
            development_v2_shadow_payload = development_v2_payloads[0]
            development_v2_positive = (
                development_v2_shadow_payload.get("outcome") == "evaluation_candidate"
            )
            if development_v2_positive:
                development_v2_comparison_outcome = (
                    "caught" if expected_positive else "false_accusation"
                )
            else:
                development_v2_comparison_outcome = _development_nonpositive_outcome(
                    expected_positive=expected_positive,
                    shadow_payload=development_v2_shadow_payload,
                    has_authority=dependence_lock is not None,
                )
        if detector_positive:
            outcome = (
                "caught"
                if expected_positive and config.development_loop
                else ("true_positive" if expected_positive else "false_accusation")
            )
        elif config.development_loop:
            outcome = _development_nonpositive_outcome(
                expected_positive=expected_positive,
                shadow_payload=shadow_payload,
                has_authority=dependence_lock is not None,
            )
        else:
            outcome = "missed_error" if expected_positive else "true_negative"
        row = {
            "case_id": case_id,
            "case_role": role,
            "frozen_label_status": label_status,
            "contract_candidate_id": candidate_id,
            "method_contract_applied": not contract_free,
            "finding_candidate_count": len(fired),
            "detector_positive": detector_positive,
            "comparison_outcome": outcome,
            "production_findings": len(bundle.get("findings", [])),
            "project_code_executions": len(bundle.get("executions", [])),
            "audit_lock_digest": sha256_digest(
                (case_root / "audit" / "semantic.lock.json").read_bytes()
            ),
            "replay_equal": True,
            "shadow_payload": shadow_payload,
            **(
                {
                    "development_v2_shadow_payload": development_v2_shadow_payload,
                    "development_v2_comparison_outcome": development_v2_comparison_outcome,
                    "development_v2_scored_for_qualification": False,
                }
                if config.dependence_v2_development_shadow
                else {}
            ),
            **_dependence_v2_row_identity(config),
            "scientific_label_ledger_digest": label_ledger["ledger_digest"],
            "authority_ledger_digest": (authority_ledger or {}).get("ledger_digest"),
        }
        _stamp_record_purpose(row, config)
        row["case_result_digest"] = semantic_digest(row)
        write_normalized_json_once(retained_path, row)
        rows.append(row)
        if outcome == "false_accusation" and config.halt_on_false_accusation:
            _write_false_accusation_halt(output_root, config, row)
            raise LeanPipelineError(
                f"development growth loop halted on false accusation for {case_id}"
            )
    outcomes = [str(row["comparison_outcome"]) for row in rows]
    metrics: dict[str, Any] = {
        "opportunity_count": len(rows),
        "true_positive_count": outcomes.count("true_positive") + outcomes.count("caught"),
        "true_negative_count": outcomes.count("true_negative"),
        "false_accusation_count": outcomes.count("false_accusation"),
        "missed_error_count": outcomes.count("missed_error"),
    }
    if config.dependence_v2_development_shadow:
        v2_outcomes = [
            str(row["development_v2_comparison_outcome"])
            for row in rows
            if row.get("development_v2_comparison_outcome") is not None
        ]
        metrics["side_by_side_development_outcomes"] = {
            "registered_v1_scored": {
                outcome: outcomes.count(outcome) for outcome in sorted(set(outcomes))
            },
            "dependence_v2_development_shadow_not_qualification_scored": {
                outcome: v2_outcomes.count(outcome) for outcome in sorted(set(v2_outcomes))
            },
        }
    if config.publish_count_metrics_only:
        metrics["rates_published"] = False
        metrics["outcome_counts"] = {
            outcome: outcomes.count(outcome) for outcome in sorted(set(outcomes))
        }
        metrics["per_miss_module_states"] = {
            str(row["case_id"]): (
                (row.get("shadow_payload") or {}).get("state")
                or row.get("detector_failure_class")
                or "no-positive-detector-output"
            )
            for row in rows
            if str(row["comparison_outcome"]).startswith("missed_")
        }
        if config.separately_reported_role is not None:
            metrics["separately_reported_role_outcome"] = next(
                (
                    row["comparison_outcome"]
                    for row in rows
                    if row["case_role"] == config.separately_reported_role
                ),
                None,
            )
    else:
        metrics["sensitivity"] = outcomes.count("true_positive") / max(
            1, outcomes.count("true_positive") + outcomes.count("missed_error")
        )
        metrics["false_accusation_rate"] = outcomes.count("false_accusation") / max(
            1, outcomes.count("false_accusation") + outcomes.count("true_negative")
        )
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
        "detector_id": detector_id,
        "entries": rows,
        "pilot_metrics": metrics,
        "production_finding_count": sum(int(row["production_findings"]) for row in rows),
        "project_code_executed": False,
        "deterministic_replay_verified": True,
        "run_at": _now(),
        "qualification_authority": "none_pilot_detector_run_only",
    }
    if authority_ledger is not None:
        ledger["authority_ledger_digest"] = authority_ledger["ledger_digest"]
    _stamp_record_purpose(ledger, config)
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


def _dependence_v2_observer(
    config: EnvelopeConfig,
    payloads: list[dict[str, Any]],
    *,
    lock_path: Path | None = None,
    expected_case_id: str | None = None,
    expected_intake_recorded_at: str | None = None,
    authority_refusal_reason: str | None = None,
) -> Callable[[Any], None] | None:
    """Construct the opt-in evaluation observer without exposing v2 to production."""

    if not config.dependence_v2_development_shadow:
        return None
    if not config.development_loop:
        raise LeanPipelineError(
            "The dependence v2 shadow is restricted to development-loop envelopes."
        )
    from sc_referee.dependence_recognition_v2.adapter import (
        DependenceRecognitionV2ShadowAdapter,
    )

    adapter = DependenceRecognitionV2ShadowAdapter()

    def observe(context: Any) -> None:
        if authority_refusal_reason is not None:
            payloads.append(adapter.controller_abstention(authority_refusal_reason))
            return
        if lock_path is not None:
            if expected_case_id is None or expected_intake_recorded_at is None:
                raise LeanPipelineError("The v2 lock lacks its frozen case bindings.")
            from sc_referee.dependence_recognition_v2.authority_lock import (
                apply_dependence_v2_authorization_lock,
            )

            context = apply_dependence_v2_authorization_lock(
                context,
                lock_path,
                expected_case_id=expected_case_id,
                expected_intake_recorded_at=expected_intake_recorded_at,
            )
        payloads.append(adapter.inspect(context))

    return observe


def _dependence_v2_identity(config: EnvelopeConfig) -> dict[str, str]:
    if not config.development_loop or not config.dependence_v2_development_shadow:
        raise LeanPipelineError("The dependence v2 identity is development-loop-only.")
    from sc_referee.dependence_recognition_v2.adapter import (
        DependenceRecognitionV2ShadowAdapter,
        dependence_v2_dependency_closure,
    )

    adapter = DependenceRecognitionV2ShadowAdapter()
    return {
        "adapter_id": adapter.adapter_id,
        "adapter_version": adapter.adapter_version,
        "adapter_implementation_digest": semantic_digest(
            {"dependency_closure": dependence_v2_dependency_closure()}
        ),
    }


def _dependence_v2_row_identity(config: EnvelopeConfig) -> dict[str, Any]:
    return (
        {"development_shadow_adapter": _dependence_v2_identity(config)}
        if config.dependence_v2_development_shadow
        else {}
    )


# ---------------------------------------------------------------------------
# Held-out opening record: written by the driver before the first step.


def write_heldout_opening(
    project_root: Path, config: EnvelopeConfig, payload: dict[str, Any]
) -> dict[str, Any]:
    """Stamp and write the opening record once, before any author call.

    The record states what was opened and what was changed at opening time,
    and it is written before authoring so it cannot be edited into agreement
    with the outcome afterwards.
    """

    root = project_root / config.pipeline_relative
    record = dict(payload)
    record["envelope_id"] = config.envelope_id
    record["recorded_at"] = _now()
    record["semantic_digest"] = semantic_digest(record)
    root.mkdir(parents=True, exist_ok=True)
    relative = config.opening_record_relative or "HELDOUT_OPENING.json"
    output_path = root / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output_path, record)
    return record


STEP_FUNCTIONS = {
    "authoring": step_authoring,
    "intake": step_intake,
    "authority": step_authority,
    "review": step_review,
    "labels": step_labels,
    "detector": step_detector,
}
STEP_ORDER = ("authoring", "intake", "review", "labels", "detector")


def pipeline_step_order(config: EnvelopeConfig) -> tuple[str, ...]:
    if config.requires_dependence_authority:
        return ("authoring", "intake", "authority", "review", "labels", "detector")
    return STEP_ORDER


def run_pipeline(
    project_root: Path, config: EnvelopeConfig, steps: list[str] | None = None
) -> dict[str, Any]:
    manifest = _manifest_read(project_root, config)
    selected = steps or [
        step for step in pipeline_step_order(config) if step not in manifest["steps"]
    ]
    results: dict[str, Any] = {}
    for step in selected:
        if step not in STEP_FUNCTIONS:
            raise LeanPipelineError(f"Unknown pipeline step {step!r}.")
        results[step] = STEP_FUNCTIONS[step](project_root, config)
    return results
