from __future__ import annotations

import json
import secrets
import shutil
import sys
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

import typer

from sc_referee.agent_protocol import (
    load_audit_status,
    load_open_questions,
)
from sc_referee.audit_diff import build_audit_diff
from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    validate_capability_matrix,
    write_capability_matrix,
)
from sc_referee.controller import replay as replay_controller
from sc_referee.controller import run_audit, run_demo
from sc_referee.core.deadline import AuditDeadline, AuditMode
from sc_referee.execution_authorization import (
    authorize_execution_draft,
    prepare_authorization_draft,
)
from sc_referee.execution_capability import ProbeLimits
from sc_referee.execution_probe import probe_podman_backend, write_unavailable_capability
from sc_referee.execution_request import (
    create_execution_request,
    parse_execution_request_draft,
)
from sc_referee.interaction import (
    create_candidate_answer,
    create_scope_selection_answer,
    create_structured_answer,
    resume_semantics,
    submit_proposal,
)
from sc_referee.interaction import (
    lock_semantics as lock_semantics_controller,
)
from sc_referee.interaction import (
    record_answer as record_answer_controller,
)
from sc_referee.interaction import (
    work_packet as load_work_packet,
)
from sc_referee.interaction import (
    work_queue as load_work_queue,
)
from sc_referee.method_contract_run import run_method_contract
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.ro_crate import export_ro_crate, validate_ro_crate
from sc_referee.storage.atomic import atomic_write_bytes
from sc_referee.version import SCHEMA_VERSION, STARTER_VERSION, __version__

app = typer.Typer(no_args_is_help=True, help="Conservative scientific-analysis audit CLI")


class _AuditModeOption(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    PUBLICATION = "publication"


_AUDIT_MODES: dict[_AuditModeOption, AuditMode] = {
    _AuditModeOption.QUICK: "quick",
    _AuditModeOption.STANDARD: "standard",
    _AuditModeOption.PUBLICATION: "publication",
}


def _default_schema_root() -> Path:
    candidates = [
        Path(__file__).resolve().parent / "resources" / f"schemas-v{SCHEMA_VERSION}",
        Path.cwd() / "reference" / f"schemas-v{SCHEMA_VERSION}",
        Path(__file__).resolve().parents[2] / "reference" / f"schemas-v{SCHEMA_VERSION}",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise typer.BadParameter("Could not locate vendored schema package; pass --schema-root")


@app.command()
def version() -> None:
    """Print program, schema, and starter-lineage versions."""
    typer.echo(
        f"sc-referee {__version__} (schema {SCHEMA_VERSION}; starter lineage {STARTER_VERSION})"
    )


@app.command()
def status(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    output_json: bool = typer.Option(False, "--json", help="Emit the typed JSON status payload."),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Validate an audit and report its bounded machine-readable status."""
    try:
        audit_status = load_audit_status(
            audit_root,
            schema_root or _default_schema_root(),
        )
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    if output_json:
        typer.echo(audit_status.model_dump_json())
        return
    counts = audit_status.assessment_counts
    typer.echo(
        f"{audit_status.audit_run_id}: {audit_status.run_state} "
        f"({audit_status.overall_status}, integrity {audit_status.integrity}); "
        f"{counts.findings} finding(s), {counts.conditional_concerns} conditional concern(s), "
        f"{counts.material_questions} question(s), {counts.disclosures} disclosure(s)"
    )


@app.command()
def questions(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Return integrity-verified open MaterialQuestions as typed JSON."""
    try:
        batch = load_open_questions(audit_root, schema_root or _default_schema_root())
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(batch.model_dump_json())


@app.command("diff")
def audit_diff(
    before: Path = typer.Argument(..., exists=True, file_okay=False),
    after: Path = typer.Argument(..., exists=True, file_okay=False),
    output: Path | None = typer.Option(None, "--output", "-o", dir_okay=False),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Compare two integrity-verified audits without issuing a correctness judgment."""
    try:
        result = build_audit_diff(before, after, schema_root or _default_schema_root())
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if output is None:
        typer.echo(payload, nl=False)
        return
    if output.exists() or output.is_symlink():
        raise typer.BadParameter(f"diff output already exists: {output}")
    atomic_write_bytes(output, payload.encode("utf-8"))
    typer.echo(f"Wrote {output}")


@app.command()
def resume(
    source_audit: Path = typer.Argument(..., exists=True, file_okay=False),
    repository: Path = typer.Option(..., "--repository", exists=True, file_okay=False),
    output: Path = typer.Option(..., "--output", "-o"),
    question_id: str | None = typer.Option(
        None,
        "--question-id",
        help="Exact open MaterialQuestion to resolve; required when several are open.",
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Create a linked exact-snapshot pre-lock semantic interaction segment."""
    try:
        result = resume_semantics(
            source_audit,
            repository,
            output,
            schema_root or _default_schema_root(),
            question_id=question_id,
        )
    except (FileExistsError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        f"Created {result['audit_run_id']} from {result['parent_audit_run_id']} "
        f"with {len(result['work_item_ids'])} work item(s)"
    )


@app.command("work-queue")
def work_queue(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Return the durable latest WorkItem queue as JSON."""
    try:
        payload = load_work_queue(audit_root, schema_root or _default_schema_root())
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))


@app.command("work-packet")
def work_packet(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    work_item_id: str = typer.Option(..., "--work-item-id"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Return one digest-bound work packet and normalized prompt template."""
    try:
        payload = load_work_packet(audit_root, work_item_id, schema_root or _default_schema_root())
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))


@app.command("submit-proposals")
def submit_proposals(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    work_item_id: str = typer.Option(..., "--work-item-id"),
    proposal_path: Path = typer.Option(..., "--proposal", exists=True, dir_okay=False),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Append one bounded model proposal after controller validation."""
    try:
        value = json.loads(proposal_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("proposal file must contain one JSON object")
        proposal = submit_proposal(
            audit_root,
            work_item_id,
            value,
            schema_root or _default_schema_root(),
        )
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Recorded proposed SemanticAssertion {proposal['assertion_id']}")


@app.command("record-answer")
def record_answer(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    question_id: str = typer.Option(..., "--question-id"),
    selected_option_id: str = typer.Option(..., "--select-option"),
    actor_id: str = typer.Option(..., "--actor-id"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Create, validate, and append one public scope-bound scientist Answer."""
    active_schemas = schema_root or _default_schema_root()
    try:
        answer = create_candidate_answer(
            audit_root,
            question_id,
            selected_option_id,
            actor_id,
            active_schemas,
        )
        record_answer_controller(audit_root, answer, active_schemas)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Recorded Answer {answer['answer_id']}")


@app.command("record-structured-answer")
def record_structured_answer(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    question_id: str = typer.Option(..., "--question-id"),
    values_path: Path = typer.Option(..., "--values", exists=True, dir_okay=False),
    actor_id: str = typer.Option(..., "--actor-id"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Append a public scientist Answer for named ScientificContract dimensions."""
    active_schemas = schema_root or _default_schema_root()
    try:
        values = json.loads(values_path.read_text(encoding="utf-8"))
        if not isinstance(values, dict):
            raise ValueError("structured Answer values must be one JSON object")
        answer = create_structured_answer(
            audit_root,
            question_id,
            values,
            actor_id,
            active_schemas,
        )
        record_answer_controller(audit_root, answer, active_schemas)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Recorded structured Answer {answer['answer_id']}")


@app.command("record-scope-answer")
def record_scope_answer(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    question_id: str = typer.Option(..., "--question-id"),
    selected_option: list[str] = typer.Option(
        ...,
        "--select-option",
        help="One listed candidate option; repeat to select several exact identities.",
    ),
    actor_id: str = typer.Option(..., "--actor-id"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Append one bounded multi-candidate review-scope Answer."""

    active_schemas = schema_root or _default_schema_root()
    try:
        answer = create_scope_selection_answer(
            audit_root,
            question_id,
            tuple(selected_option),
            actor_id,
            active_schemas,
        )
        record_answer_controller(audit_root, answer, active_schemas)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Recorded scope Answer {answer['answer_id']}")


@app.command("lock-semantics")
def lock_semantics(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Create semantic lock, then complete deterministic detection and reporting."""
    try:
        bundle = lock_semantics_controller(audit_root, schema_root or _default_schema_root())
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        f"Locked and completed {bundle['audit_run_id']}: "
        f"{len(bundle['findings'])} finding(s), {len(bundle['answers'])} answer(s)"
    )


@app.command("validate-schemas")
def validate_schemas(
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Validate all vendored public schema examples offline."""
    registry = LocalSchemaRegistry(schema_root or _default_schema_root())
    count = registry.validate_example_directory()
    typer.echo(f"Validated {count} public schema examples")


@app.command("probe-execution-capability", hidden=True)
def probe_execution_capability(
    output: Path = typer.Option(..., "--output", "-o"),
    audit_run_id: str = typer.Option("audit:capability-probe", "--audit-run-id"),
    image_reference: str | None = typer.Option(
        None,
        "--image",
        help="Already-present digest-pinned auditor probe image; image retrieval is not performed.",
    ),
    podman_executable: Path | None = typer.Option(
        None,
        "--podman-executable",
        exists=True,
        dir_okay=False,
        help="Podman client to probe; defaults to PATH discovery.",
    ),
    wall_time_seconds: int = typer.Option(2, min=1, max=30),
    cpu_quota_millis: int = typer.Option(500, min=1),
    memory_bytes: int = typer.Option(67_108_864, min=16_777_216),
    process_count: int = typer.Option(16, min=1),
    open_files: int = typer.Option(32, min=8),
    writable_bytes: int = typer.Option(1_048_576, min=131_072),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Run only sc-referee-owned code to test effective rootless-OCI controls."""

    active_schemas = schema_root or _default_schema_root()
    captured = datetime.now(UTC).replace(microsecond=0)
    captured_at = captured.isoformat().replace("+00:00", "Z")
    expires_at = (captured + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    discovered = podman_executable or (
        Path(candidate) if (candidate := shutil.which("podman")) is not None else None
    )
    try:
        if discovered is None:
            record = write_unavailable_capability(
                output,
                captured_at=captured_at,
                reason="No supported rootless Podman executable was found; static audit remains available.",
                schema_root=active_schemas,
            )
        elif image_reference is None:
            record = write_unavailable_capability(
                output,
                captured_at=captured_at,
                reason=(
                    "No already-present digest-pinned auditor probe image was supplied; "
                    "the controller did not retrieve one."
                ),
                schema_root=active_schemas,
            )
        else:
            package = probe_podman_backend(
                discovered,
                image_reference,
                audit_run_id,
                output,
                captured_at,
                expires_at,
                ProbeLimits(
                    wall_time_seconds=wall_time_seconds,
                    cpu_quota_millis=cpu_quota_millis,
                    memory_bytes=memory_bytes,
                    process_count=process_count,
                    open_files=open_files,
                    writable_bytes=writable_bytes,
                ),
                active_schemas,
            )
            record = package.capability
    except (FileExistsError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        f"Wrote {output} ({record['capability_evidence_status']}; "
        f"project execution supported: {str(record['project_code_execution_supported']).lower()})"
    )


@app.command("request-execution", hidden=True)
def request_execution(
    source_audit: Path = typer.Argument(..., exists=True, file_okay=False),
    request_path: Path = typer.Option(..., "--request", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output", "-o"),
    created_at: str | None = typer.Option(
        None,
        "--created-at",
        help="Injected UTC timestamp for deterministic automation; defaults to current UTC.",
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Lock one bounded project-execution request without authorizing or launching it."""

    timestamp = created_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    try:
        request_value = json.loads(request_path.read_text(encoding="utf-8"))
        draft = parse_execution_request_draft(request_value)
        result = create_execution_request(
            source_audit,
            output,
            draft,
            schema_root or _default_schema_root(),
            created_at=timestamp,
        )
    except (FileExistsError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        f"Locked {result.work_item_id} in {result.audit_run_id}; "
        "awaiting direct authorization (no project code executed)"
    )


@app.command("authorize-execution", hidden=True)
def authorize_execution(
    request_audit: Path = typer.Argument(..., exists=True, file_okay=False),
    work_item_id: str = typer.Option(..., "--work-item-id"),
    capability_path: Path = typer.Option(..., "--capability", exists=True, dir_okay=False),
    launch_path: Path = typer.Option(..., "--launch", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output", "-o"),
    linked_audit_run_id: str = typer.Option(..., "--linked-audit-run-id"),
    expires_at: str = typer.Option(..., "--expires-at"),
    actor_id: str = typer.Option(..., "--actor-id"),
    actor_display_name: str = typer.Option(..., "--actor-display-name"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Create a test-only authorization envelope; real launch remains disabled."""

    confirmed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        launch_value = json.loads(launch_path.read_text(encoding="utf-8"))
        draft = prepare_authorization_draft(
            request_audit,
            work_item_id,
            capability_path,
            launch_value,
            output,
            linked_audit_run_id,
            expires_at=expires_at,
            actor_id=actor_id,
            actor_display_name=actor_display_name,
        )
        result = authorize_execution_draft(
            draft,
            schema_root or _default_schema_root(),
            terminal_input=sys.stdin,
            terminal_output=sys.stdout,
            confirmed_at=confirmed_at,
            nonce_factory=lambda: "nonce-" + secrets.token_urlsafe(24),
            challenge_factory=lambda: "challenge-" + secrets.token_urlsafe(18),
        )
    except (FileExistsError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        f"Recorded test-only authorization {result.authorization['authorization_id']}; "
        "real launch is post-MPP and disabled by accepted ADR-0017"
    )


@app.command("execute-authorized", hidden=True)
def execute_authorized(
    linked_audit: Path = typer.Argument(..., exists=True, file_okay=False),
    capability_path: Path = typer.Option(..., "--capability", exists=True, dir_okay=False),
    snapshot_root: Path = typer.Option(
        ...,
        "--snapshot-root",
        exists=True,
        file_okay=False,
        help="Materialized immutable snapshot; exact bytes are verified and privately restaged.",
    ),
    podman_executable: Path = typer.Option(..., "--podman-executable", exists=True, dir_okay=False),
    max_log_bytes: int = typer.Option(1_048_576, min=0, max=67_108_864),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Refuse real launch until trusted capability-probe admission is implemented."""

    del linked_audit, capability_path, snapshot_root, podman_executable, max_log_bytes, schema_root
    raise typer.BadParameter(
        "project execution is disabled by ADR-0017 (post-MPP); deferred ADR-0015 and ADR-0016 "
        "remain unresolved, and standalone capability JSON cannot establish a launch premise"
    )


@app.command("generate-capability-matrix")
def generate_capability_matrix_command(
    output: Path = typer.Option(..., "--output", "-o", dir_okay=False),
    manifest_root: Path | None = typer.Option(
        None,
        "--manifest-root",
        exists=True,
        file_okay=False,
        help="Closed capability source manifest set; defaults to the bundled release set.",
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Generate a fail-closed public capability matrix from exact release manifests."""

    try:
        matrix = write_capability_matrix(
            output,
            manifest_root or default_capability_manifest_root(),
            schema_root or _default_schema_root(),
        )
    except (FileExistsError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Wrote {output} ({len(matrix['entries'])} narrow capability entries)")


@app.command("validate-capability-matrix")
def validate_capability_matrix_command(
    matrix: Path = typer.Argument(..., exists=True, dir_okay=False),
    manifest_root: Path | None = typer.Option(
        None,
        "--manifest-root",
        exists=True,
        file_okay=False,
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Validate and reproduce one manifest-derived public capability matrix."""

    try:
        record = validate_capability_matrix(
            matrix,
            manifest_root or default_capability_manifest_root(),
            schema_root or _default_schema_root(),
        )
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(record, sort_keys=True, separators=(",", ":")))


@app.command("export-ro-crate")
def export_ro_crate_command(
    audit_root: Path = typer.Argument(..., exists=True, file_okay=False),
    output: Path = typer.Option(..., "--output", "-o", dir_okay=False),
    author_name: str = typer.Option(
        ...,
        "--author-name",
        help="Declared author of the exported audit package; not authenticated.",
    ),
    license_uri: str = typer.Option(
        ...,
        "--license-uri",
        help="Absolute URI for the exported audit package license, not the audited project.",
    ),
    license_name: str = typer.Option(
        ...,
        "--license-name",
        help="Human-readable name for the declared export-package license.",
    ),
    author_id: str = typer.Option(
        "#author",
        "--author-id",
        help="Absolute URI or fragment identifier for the declared crate author.",
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Export an integrity-verified audit as a deterministic attached RO-Crate 1.3 ZIP."""

    try:
        record = export_ro_crate(
            audit_root,
            output,
            schema_root or _default_schema_root(),
            author_name=author_name,
            license_uri=license_uri,
            license_name=license_name,
            author_id=author_id,
        )
    except (FileExistsError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Wrote {output} ({record['export_id']}; valid RO-Crate 1.3 profile)")


@app.command("validate-ro-crate")
def validate_ro_crate_command(
    archive: Path = typer.Argument(..., exists=True, dir_okay=False),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Validate a bounded sc-referee attached RO-Crate 1.3 archive offline."""

    try:
        record = validate_ro_crate(archive, schema_root or _default_schema_root())
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(record, sort_keys=True, separators=(",", ":")))


@app.command()
def method_contract(
    repository: Path = typer.Argument(..., exists=True, file_okay=False),
    task: str = typer.Option(
        ...,
        "--task",
        help="Repository-relative governing task or protocol file.",
    ),
    output: Path = typer.Option(Path(".sc-referee/method-contract"), "--output", "-o"),
    profile: Path | None = typer.Option(
        None,
        "--profile",
        exists=True,
        dir_okay=False,
        help=(
            "Complete expected_count_background_v1 or scientific_check_requirement_v1 JSON "
            "supplied by the scientist."
        ),
    ),
    actor_id: str | None = typer.Option(
        None,
        "--actor-id",
        help="Identity of the scientist who supplied --profile.",
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Freeze a claimless analysis method contract without executing project code."""

    try:
        profile_value: object | None = None
        if profile is not None:
            profile_value = json.loads(profile.read_text(encoding="utf-8"))
        bundle = run_method_contract(
            repository,
            task,
            output,
            schema_root or _default_schema_root(),
            profile=profile_value,
            actor_id=actor_id,
        )
    except (FileExistsError, OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error)) from error
    contract = bundle["scientific_contracts"][0]
    resolution = contract["extensions"]["x-method-profile-resolution-status"]
    typer.echo(
        f"Wrote claimless method contract {output} ({resolution}); "
        "0 Claims, 0 publication surfaces, project execution disabled."
    )


@app.command()
def audit(
    repository: Path = typer.Argument(..., exists=True, file_okay=False),
    output: Path = typer.Option(Path(".sc-referee/audit"), "--output", "-o"),
    report: str | None = typer.Option(
        None,
        "--report",
        help="Repository-relative final publication surface selected by the user.",
    ),
    mode: _AuditModeOption = typer.Option(
        _AuditModeOption.STANDARD,
        "--mode",
        help="User-visible elapsed-time policy.",
    ),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
    method_contract_lock: Path | None = typer.Option(
        None,
        "--method-contract-lock",
        exists=True,
        dir_okay=False,
        help=(
            "Frozen claimless method-contract semantic lock to bind to later Claims or one "
            "matching analysis-scoped scientific-check question."
        ),
    ),
    attestations: Path | None = typer.Option(
        None,
        "--attestations",
        exists=True,
        dir_okay=False,
        help=(
            "External digest-bound multiple-testing correction-scope attestations file; "
            "development lane only."
        ),
    ),
    material_input: list[str] | None = typer.Option(
        None,
        "--material-input",
        help=(
            "Repository-relative material input selected for a separate bounded exact snapshot "
            "read; repeat at most eight times. Selection does not validate scientific meaning."
        ),
    ),
    development_lane: bool = typer.Option(
        False,
        "--development-lane",
        help=(
            "Run the newest scientific-check development binding for evaluation only; "
            "this lane can never emit Findings."
        ),
    ),
) -> None:
    """Inventory and statically inspect an arbitrary scientific project."""
    active_mode = _AUDIT_MODES[mode]
    active_deadline = AuditDeadline.for_mode(active_mode)
    typer.echo(
        f"Mode {active_mode}: scheduling cutoff "
        f"{active_deadline.scheduling_cutoff_seconds:g}s; hard deadline "
        f"{active_deadline.hard_seconds:g}s; project execution disabled."
    )
    try:
        bundle = run_audit(
            repository,
            output,
            schema_root or _default_schema_root(),
            report=report,
            mode=active_mode,
            deadline=active_deadline,
            method_contract_lock=method_contract_lock,
            attestations=attestations,
            material_inputs=tuple(material_input or ()),
            scientific_check_lane="development" if development_lane else "qualified",
        )
    except (FileExistsError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    coverage_status = bundle["coverage_records"][0]["overall_status"]
    answer_summary = f", {len(bundle['answers'])} answer(s)" if bundle["answers"] else ""
    typer.echo(
        f"Wrote {output} ({coverage_status}): {len(bundle['findings'])} finding(s), "
        f"{len(bundle['conditional_concerns'])} conditional concern(s), "
        f"{len(bundle['material_questions'])} question(s)"
        f"{answer_summary}, {len(bundle['disclosures'])} disclosure(s)"
    )


@app.command()
def demo(
    repository: Path = typer.Argument(..., exists=True, file_okay=False),
    output: Path = typer.Option(Path(".demo-audit"), "--output", "-o"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Run the bundled deterministic walking-skeleton audit."""
    try:
        bundle = run_demo(repository, output, schema_root or _default_schema_root())
    except (FileExistsError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    coverage_status = bundle["coverage_records"][0]["overall_status"]
    typer.echo(
        f"Wrote {output} ({coverage_status}): {len(bundle['findings'])} finding(s), "
        f"{len(bundle['conditional_concerns'])} conditional concern(s), "
        f"{len(bundle['material_questions'])} question(s), {len(bundle['disclosures'])} disclosure(s)"
    )


@app.command()
def replay(
    lock: Path = typer.Argument(..., exists=True, dir_okay=False),
    output: Path = typer.Option(Path(".demo-replay"), "--output", "-o"),
    schema_root: Path | None = typer.Option(None, exists=True, file_okay=False),
) -> None:
    """Regenerate detector and report outputs from a semantic lock without model access."""
    try:
        bundle = replay_controller(lock, output, schema_root or _default_schema_root())
    except (FileExistsError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Replayed {bundle['audit_run_id']} into {output}")


if __name__ == "__main__":
    app()
