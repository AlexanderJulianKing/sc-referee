from __future__ import annotations

import json
import stat
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial as bind_args
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

import yaml

from sc_referee.agent_protocol import load_audit_status
from sc_referee.cache import (
    DescendantCacheSession,
    ParserCacheResult,
    inspect_supported_sources_with_cache,
    rebind_run,
)
from sc_referee.cache_auth import CacheKeyProvider
from sc_referee.calculation_checks import CalculationCheckRegistry
from sc_referee.calculation_checks.feature_identifier_identity import (
    FEATURE_IDENTIFIER_IDENTITY_CHECK_ID,
    partition_feature_identifier_identity_evaluation,
)
from sc_referee.calculation_checks.integration import (
    build_calculation_context,
    compile_calculation_records,
)
from sc_referee.calculation_checks.profiles import default_calculation_check_registry
from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.core.control import RunControl
from sc_referee.core.deadline import AuditDeadline, AuditMode
from sc_referee.core.errors import (
    CancellationRequestedError,
    DeadlineExceededError,
    ErrorCode,
    HostModelLimitError,
)
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.core.state import AuditState, transition
from sc_referee.delimited_io import classify_delimited_path
from sc_referee.detectors import method_conflict_grant_pins
from sc_referee.detectors.admission import AdmissionContext, admit_finding
from sc_referee.detectors.bounded_analysis_method_conflict import (
    BoundedAnalysisMethodConflictDetector,
)
from sc_referee.detectors.bounded_report_mean_direction import (
    BoundedReportMeanDirectionDetector,
)
from sc_referee.detectors.bounded_reported_method_contract import (
    BoundedReportedMethodContractConflictDetector,
)
from sc_referee.detectors.claim_result_agreement import ClaimResultDirectionDetector
from sc_referee.detectors.feature_identifier_identity import (
    BoundedFeatureIdentifierIdentityDetector,
)
from sc_referee.detectors.manifest import (
    fixture_envelope_applies,
    load_fixture_detector_envelope,
    locked_counterevidence_check_ids,
)
from sc_referee.detectors.method_conflict_finding import (
    code_dependence_wording_profile,
    draft_method_conflict_finding,
)
from sc_referee.detectors.method_conflict_qualification import (
    project_qualified_method_conflict_candidate,
    resolve_method_conflict_qualification,
)
from sc_referee.detectors.method_conflict_registry import (
    MethodConflictEvaluation,
    evaluate_registered_method_conflicts,
    locked_method_conflict_bindings,
    validate_registered_method_conflict_manifests,
)
from sc_referee.detectors.sample_unit_dependence import SampleUnitDependenceQuestionDetector
from sc_referee.expected_count_obligation import (
    EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST,
    EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID,
    compile_unresolved_expected_count_obligation,
)
from sc_referee.h5ad_inventory import inspect_h5ad_inventory
from sc_referee.lineage import (
    LINEAGE_GRADE_DIMENSIONS,
    BoundedLineageOutput,
    bind_bounded_claim_lineage,
    bounded_lineage_from_payload,
    bounded_lineage_payload,
    bounded_lineage_runtime_digest,
    reconstruct_bounded_results,
)
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_REQUIRED_DIMENSIONS,
)
from sc_referee.nextflow_trace import NEXTFLOW_TRACE_PARSER_ID, inspect_nextflow_trace
from sc_referee.parsers.cell_language_bridge import (
    inspect_embedded_cell_sources,
    parser_scope_key,
)
from sc_referee.parsers.claim_builder import build_directional_claim
from sc_referee.parsers.jupyter_inventory import inspect_jupyter
from sc_referee.parsers.markdown_claims import inspect_markdown
from sc_referee.parsers.python_ast import inspect_python
from sc_referee.parsers.quarto_inventory import inspect_quarto
from sc_referee.parsers.r_dual import inspect_r
from sc_referee.parsers.rmarkdown_inventory import inspect_rmarkdown
from sc_referee.parsers.scalar_verification import verify_mean_difference
from sc_referee.parsers.tabular import inspect_repeated_identifier
from sc_referee.performance import build_semantic_lock_performance_record
from sc_referee.posthoc_method_ledger import (
    PosthocMethodLedgerError,
    posthoc_form_allowed,
    project_analysis_posthoc_method_ledger,
    project_posthoc_method_ledger,
)
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.observed import (
    PublicStaticGraph,
    build_audit_run_record,
    build_file_records,
    build_public_observed_graph,
    build_public_static_graph,
    build_stage_result_record,
    controller_provenance,
    typed_ref,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report
from sc_referee.reproduction import (
    build_reproduction_requests,
    inspect_project_environments,
)
from sc_referee.scientific_checks.core import (
    FrozenInspectionContext,
    ScientificCheckContractError,
)
from sc_referee.scientific_checks.integration import (
    build_frozen_inspection_context,
    compile_scientific_check_records,
)
from sc_referee.scientific_checks.integration_multiple_testing_v2 import (
    compile_multiple_testing_development_records,
)
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_checks.registry import ScientificCheckLane, ScientificCheckRegistry
from sc_referee.scope_selection import build_scope_selection_contracts
from sc_referee.snapshot.identity import build_asset_identity, full_digest_evidence
from sc_referee.snapshot.repository import (
    AssetIdentityPolicy,
    SnapshotOutput,
    capture_repository,
    detect_workspace_divergence,
    merge_workspace_state,
)
from sc_referee.storage.integrity import (
    build_storage_manifest,
    verify_sqlite_index,
    verify_storage_manifest,
)
from sc_referee.storage.jsonl import JsonlRecordStore
from sc_referee.storage.layout import AuditLayout
from sc_referee.storage.sqlite_index import rebuild_sqlite
from sc_referee.tabular_inventory import inspect_delimited_inventory
from sc_referee.version import SCHEMA_VERSION, __version__


@dataclass(frozen=True)
class FrozenFileManifestInput:
    """Exact persisted file-manifest bytes with path and digest binding only."""

    file_manifest_ref: str
    canonical_jsonl_bytes: bytes
    manifest_digest: str

    def __post_init__(self) -> None:
        relative = PurePosixPath(self.file_manifest_ref)
        if (
            not self.file_manifest_ref
            or relative.is_absolute()
            or relative.as_posix() != self.file_manifest_ref
            or ".." in self.file_manifest_ref.split("/")
        ):
            raise ScientificCheckContractError(
                "inspection file-manifest path must be relative and bounded"
            )
        if (
            not self.manifest_digest.startswith("sha256:")
            or len(self.manifest_digest) != 71
            or any(character not in "0123456789abcdef" for character in self.manifest_digest[7:])
        ):
            raise ScientificCheckContractError("inspection file-manifest digest is invalid")
        if sha256_digest(self.canonical_jsonl_bytes) != self.manifest_digest:
            raise ScientificCheckContractError("inspection file-manifest digest mismatch")

    def digest_projection(self) -> dict[str, str]:
        return {
            "file_manifest_ref": self.file_manifest_ref,
            "manifest_digest": self.manifest_digest,
        }


@dataclass(frozen=True)
class ManifestBoundFrozenInspectionContext(FrozenInspectionContext):
    """Add one frozen manifest capability without changing the pinned v1 base context."""

    file_manifest_input: FrozenFileManifestInput | None = None


def _bind_frozen_file_manifest_input(
    context: FrozenInspectionContext,
    *,
    manifest_root: Path,
    repository_snapshot: dict[str, Any],
) -> FrozenInspectionContext:
    """Capture the referenced manifest once and return only an immutable byte value."""

    manifest_input = _capture_frozen_file_manifest_input(
        manifest_root=manifest_root,
        repository_snapshot=repository_snapshot,
    )
    if manifest_input is None:
        return context
    return ManifestBoundFrozenInspectionContext(
        snapshot_digest=context.snapshot_digest,
        selected_surface_ref=context.selected_surface_ref,
        selected_artifact_ref=context.selected_artifact_ref,
        documents=context.documents,
        base_records=context.base_records,
        material_inputs=context.material_inputs,
        shared_derivations=context.shared_derivations,
        scope_join_graph=context.scope_join_graph,
        file_manifest_input=manifest_input,
    )


def _capture_frozen_file_manifest_input(
    *,
    manifest_root: Path,
    repository_snapshot: dict[str, Any],
) -> FrozenFileManifestInput | None:
    """Read exact controller-persisted bytes without interpreting JSONL entries."""

    manifest_ref = repository_snapshot.get("file_manifest_ref")
    if not isinstance(manifest_ref, str):
        return None
    relative = PurePosixPath(manifest_ref)
    if (
        not manifest_ref
        or relative.is_absolute()
        or relative.as_posix() != manifest_ref
        or ".." in manifest_ref.split("/")
    ):
        return None
    try:
        if manifest_root.is_symlink():
            return None
        resolved_root = manifest_root.resolve(strict=True)
        candidate = resolved_root
        for component in relative.parts:
            candidate = candidate / component
            if candidate.is_symlink():
                return None
        if not candidate.resolve(strict=True).is_relative_to(resolved_root):
            return None
        before = candidate.stat()
        if not stat.S_ISREG(before.st_mode):
            return None
        content = candidate.read_bytes()
        after = candidate.stat()
    except (OSError, ValueError):
        return None
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity or len(content) != before.st_size:
        return None
    try:
        return FrozenFileManifestInput(
            file_manifest_ref=manifest_ref,
            canonical_jsonl_bytes=content,
            manifest_digest=sha256_digest(content),
        )
    except ValueError:
        return None


_ARRAY_FIELDS = [
    "scientific_contracts",
    "semantic_assertions",
    "claims",
    "detector_manifests",
    "detector_results",
    "findings",
    "conditional_concerns",
    "material_questions",
    "disclosures",
    "scientist_dispositions",
    "adjudications",
    "coverage_records",
    "audit_plans",
    "asset_identities",
    "publication_surfaces",
    "external_evidence",
    "environment_reconstructions",
    "reproduction_requests",
    "causal_contracts",
    "repository_snapshots",
    "parser_manifests",
    "parser_results",
    "sandbox_capabilities",
    "project_execution_authorizations",
    "cache_entries",
    "performance_records",
    "detector_qualifications",
    "tool_identities",
    "cache_policies",
    "storage_manifests",
    "agent_reviews",
    "adjudicated_root_causes",
    "detector_evaluation_candidates",
    "stage3_comparison_reviews",
    "detector_case_outcomes",
    "qualification_metric_sets",
    "static_qualification_profiles",
    "static_qualification_proofs",
    "deterministic_check_observations",
    "benchmark_adjudications",
    "benchmark_fixtures",
    "capability_matrices",
    "ro_crate_exports",
    "audit_runs",
    "stage_results",
    "file_records",
    "operations",
    "artifacts",
    "observed_results",
    "data_assets",
    "variables",
    "analysis_decisions",
    "selection_envelopes",
    "executions",
    "environments",
    "work_items",
    "answers",
]

_SCIENTIFIC_CONTRACT_DIMENSIONS = (
    "target_population",
    "analysis_population",
    "unit_of_analysis",
    "exposure_or_treatment",
    "outcome",
    "estimand",
    "comparison",
    "time_definition",
    "scale_and_orientation",
    "adjustment_set",
    "denominator_or_universe",
    "control_set",
    "dependence_structure",
    "measurement_model",
    "missingness_and_transport",
    "uncertainty_target",
    "selection_process",
)


_PENDING_DETECTOR_WORK = [
    "detector:claim-result-direction on claim:walking-skeleton-direction",
    "detector:sample-unit-dependence on operation:compute-difference",
]


@dataclass
class _RunJournal:
    store: JsonlRecordStore
    validator: LocalSchemaRegistry
    run_id: str
    created_at: str
    snapshot_id: str | None
    parent_run_id: str | None = None
    state: AuditState = AuditState.CREATED
    _stage_sequence: int = field(default=0, init=False)
    _last_stage_details: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._append_run_state()

    def transition_to(self, target: AuditState) -> None:
        self.state = transition(self.state, target)
        self._append_run_state()

    def record_stage(
        self,
        stage: str,
        status: str,
        details: str,
        error_code: ErrorCode | None = None,
    ) -> None:
        self._stage_sequence += 1
        self._last_stage_details = details
        record = build_stage_result_record(
            self.run_id,
            f"stage-result:{self.run_id}:{self._stage_sequence}:{stage}",
            stage,
            self._stage_sequence,
            status,
            details,
            self.created_at,
            error_code=error_code.value if error_code is not None else None,
        )
        self.validator.validate(record)
        self.store.append(record)

    def _append_run_state(self) -> None:
        record = build_audit_run_record(
            self.run_id,
            self.state.value,
            self.created_at,
            snapshot_id=self.snapshot_id,
            parent_run_id=self.parent_run_id,
            terminal_reason=self._last_stage_details,
        )
        self.validator.validate(record)
        self.store.append(record)


@dataclass(frozen=True)
class _GeneralCoverageDisposition:
    overall_status: str = "partial_evidence_unavailable"
    run_state: str = "complete"
    termination_reason: str = "semantic_inputs_unresolved"
    pending_work: tuple[str, ...] = ()


def _append_checksum_manifest_inspection_gaps(
    known_gaps: list[str], bundle: dict[str, Any]
) -> None:
    snapshots = bundle.get("repository_snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != 1:
        return
    snapshot = snapshots[0]
    if not isinstance(snapshot, dict):
        return
    extensions = snapshot.get("extensions")
    if not isinstance(extensions, dict):
        return
    inspection = extensions.get("x-checksum-manifest-inspection")
    if not isinstance(inspection, dict):
        return
    invalid_paths = inspection.get("invalid_paths")
    unavailable_paths = inspection.get("unavailable_paths")
    ambiguous_targets = inspection.get("ambiguous_targets")
    invalid_count = len(invalid_paths) if isinstance(invalid_paths, list) else 0
    unavailable_count = len(unavailable_paths) if isinstance(unavailable_paths, list) else 0
    ambiguous_count = len(ambiguous_targets) if isinstance(ambiguous_targets, list) else 0
    if invalid_count or unavailable_count:
        known_gaps.append(
            f"Checksum-manifest inspection could not admit {invalid_count} invalid and "
            f"{unavailable_count} over-budget or unavailable candidate(s); no identities were "
            "inferred from them."
        )
    if ambiguous_count:
        known_gaps.append(
            f"Checksum manifests declared {ambiguous_count} target(s) more than once; those "
            "targets retained their independently observed weaker identity."
        )


def _append_tabular_inventory_gaps(known_gaps: list[str], bundle: dict[str, Any]) -> None:
    delimited_paths = {
        str(record["path"])
        for record in bundle.get("file_records", [])
        if isinstance(record, dict)
        and isinstance(record.get("path"), str)
        and classify_delimited_path(str(record["path"])) is not None
    }
    data_assets = [
        record
        for record in bundle.get("data_assets", [])
        if isinstance(record, dict) and record.get("format") in {"csv", "tsv"}
    ]
    represented_paths = {
        str(record["path"]) for record in data_assets if isinstance(record.get("path"), str)
    }
    partial_count = sum(record.get("structure_status") == "partial" for record in data_assets)
    opaque_count = sum(
        record.get("structure_status") in {"opaque", "unavailable"} for record in data_assets
    )
    unavailable_count = len(delimited_paths - represented_paths)
    if partial_count:
        known_gaps.append(
            f"{partial_count} delimited table(s) have header-only structural inventory; row "
            "shape, values, storage types, and scientific meanings remain unknown."
        )
    if opaque_count:
        known_gaps.append(
            f"{opaque_count} fully captured delimited table(s) had opaque or unavailable "
            "headers; no variables were inferred from them."
        )
    if unavailable_count:
        known_gaps.append(
            f"{unavailable_count} delimited table(s) were not structurally inspected because "
            "their complete immutable bytes were unavailable or their artifact linkage was "
            "ambiguous."
        )


def _append_h5ad_inventory_gaps(known_gaps: list[str], bundle: dict[str, Any]) -> None:
    snapshots = bundle.get("repository_snapshots", [])
    selected_paths: set[str] = set()
    if isinstance(snapshots, list) and len(snapshots) == 1 and isinstance(snapshots[0], dict):
        extensions = snapshots[0].get("extensions", {})
        if isinstance(extensions, dict):
            values = extensions.get("x-material-full-digest-paths", [])
            if isinstance(values, list):
                selected_paths = {
                    str(value)
                    for value in values
                    if isinstance(value, str) and PurePosixPath(value).suffix.casefold() == ".h5ad"
                }
    h5ad_assets = [
        record
        for record in bundle.get("data_assets", [])
        if isinstance(record, dict)
        and record.get("format") == "matrix"
        and isinstance(record.get("path"), str)
        and str(record["path"]) in selected_paths
    ]
    represented_paths = {str(record["path"]) for record in h5ad_assets}
    if h5ad_assets:
        known_gaps.append(
            f"{len(h5ad_assets)} explicitly selected H5AD input(s) received bounded physical "
            "structure inventory only; scientific meaning, analysis use, biological-replicate "
            "semantics, and experimental unit require separate evidence."
        )
    unavailable_count = len(selected_paths - represented_paths)
    if unavailable_count:
        known_gaps.append(
            f"{unavailable_count} explicitly selected H5AD input(s) were unavailable or outside "
            "the supported dense/CSR/CSC integer profile; no H5AD structure was inferred for them."
        )


def _append_nextflow_trace_gaps(known_gaps: list[str], bundle: dict[str, Any]) -> None:
    trace_results = [
        record
        for record in bundle.get("parser_results", [])
        if isinstance(record, dict) and record.get("parser_id") == NEXTFLOW_TRACE_PARSER_ID
    ]
    if not trace_results:
        return
    result = trace_results[0]
    imported_count = sum(
        record.get("execution_kind") == "imported"
        for record in bundle.get("executions", [])
        if isinstance(record, dict)
    )
    if imported_count:
        known_gaps.append(
            f"{imported_count} terminal Nextflow task row(s) were imported as weak external "
            "assertions; they are not controller-observed execution, output lineage, clean-control "
            "evidence, or Finding premises."
        )
    if result.get("state") in {"unsupported", "parser_unavailable", "error"}:
        known_gaps.append(
            "The default Nextflow trace candidate was unsupported or unavailable; no execution "
            "fact was inferred from it."
        )
    opaque_count = len(result.get("opaque_constructs", []))
    if opaque_count and result.get("state") == "partially_parsed":
        known_gaps.append(
            f"{opaque_count} Nextflow trace row boundary or truncation marker(s) remained opaque; "
            "only admitted terminal rows were imported."
        )


def run_demo(
    repository: Path,
    output: Path,
    schema_root: Path,
    *,
    deadline: AuditDeadline | None = None,
    after_snapshot: Callable[[Path], None] | None = None,
    run_control: RunControl | None = None,
    stage_hook: Callable[[str, RunControl], None] | None = None,
) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"demo output already exists: {output}")
    layout = AuditLayout(output)
    layout.create()
    validator = LocalSchemaRegistry(schema_root)
    active_deadline = deadline or AuditDeadline.for_mode("standard")
    locked_case = yaml.safe_load((repository / "fixture.lock.yaml").read_text(encoding="utf-8"))
    if locked_case.get("fixture_mode") is not True:
        raise ValueError(
            "The demo command accepts only an explicitly marked synthetic fixture lock"
        )
    run_id = locked_case["audit_run_id"]

    file_store = JsonlRecordStore(layout.observed)
    journal = _RunJournal(
        file_store,
        validator,
        run_id,
        locked_case["locked_at"],
        None,
    )
    active_control = run_control or RunControl()
    try:
        _check_run_control(active_control, journal, "snapshot")
        snapshot = capture_repository(
            repository,
            layout.observed / "snapshot",
            run_id,
            captured_at=locked_case["locked_at"],
        )
        journal.snapshot_id = snapshot.snapshot_record["snapshot_id"]
        write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)
        return _continue_demo_run(
            repository,
            output,
            schema_root,
            layout,
            locked_case,
            snapshot,
            file_store,
            journal,
            active_deadline,
            active_control,
            after_snapshot,
            stage_hook,
        )
    except (CancellationRequestedError, HostModelLimitError, DeadlineExceededError):
        raise
    except Exception:
        if journal.state not in {
            AuditState.COMPLETE,
            AuditState.PARTIAL_DEADLINE,
            AuditState.PARTIAL_HOST_LIMIT,
            AuditState.CANCELLED,
            AuditState.FAILED_CONTROLLER,
        }:
            journal.record_stage(
                "controller",
                "failed",
                "The controller failed after the initial snapshot; completed records were preserved.",
                ErrorCode.CONTROLLER_INTEGRITY_FAILURE,
            )
            journal.transition_to(AuditState.FAILED_CONTROLLER)
        raise


def run_audit(
    repository: Path,
    output: Path,
    schema_root: Path,
    *,
    report: str | None = None,
    mode: AuditMode = "standard",
    deadline: AuditDeadline | None = None,
    after_snapshot: Callable[[Path], None] | None = None,
    run_control: RunControl | None = None,
    stage_hook: Callable[[str, RunControl], None] | None = None,
    cache_key_provider: CacheKeyProvider | None = None,
    method_contract_lock: Path | None = None,
    scientific_check_registry: ScientificCheckRegistry | None = None,
    calculation_check_registry: CalculationCheckRegistry | None = None,
    material_inputs: tuple[str, ...] = (),
    dependence_authorization_lock: Path | None = None,
    dependence_authorization_case_id: str | None = None,
    evaluation_inspection_observer: Callable[[FrozenInspectionContext], None] | None = None,
    scientific_check_lane: ScientificCheckLane = "qualified",
) -> dict[str, Any]:
    """Run a conservative static audit over an arbitrary repository.

    This path inventories every file, parses the currently supported Python and Markdown
    surfaces, and records unsupported scope. It intentionally emits no production Finding until
    claim contracts and qualified detector envelopes are available.
    """

    if (dependence_authorization_lock is None) != (dependence_authorization_case_id is None):
        raise ValueError(
            "a dependence authorization lock and its expected case id must be supplied together"
        )
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"audit output already exists: {output}")
    report = _normalize_optional_relative_path(report)
    active_deadline = deadline or AuditDeadline.for_mode(mode)
    active_control = run_control or RunControl()
    repository = repository.resolve()
    created_at = _timestamp_now()
    run_id = f"audit:{uuid4().hex}"
    layout = AuditLayout(output)
    layout.create()
    validator = LocalSchemaRegistry(schema_root)
    observed_store = JsonlRecordStore(layout.observed)
    journal = _RunJournal(
        observed_store,
        validator,
        run_id,
        created_at,
        None,
        None,
    )
    parser_cache: ParserCacheResult | None = None
    active_scientific_checks = scientific_check_registry or default_scientific_check_registry()
    selected_scientific_modules = active_scientific_checks.modules_for_lane(scientific_check_lane)
    selected_method_conflict_bindings = active_scientific_checks.bindings_for_lane(
        scientific_check_lane
    )
    active_scientific_lane_registry = ScientificCheckRegistry(
        selected_scientific_modules,
        unavailable_manifests=active_scientific_checks.unavailable_manifests,
        method_conflict_bindings=selected_method_conflict_bindings,
    )
    active_calculation_checks = calculation_check_registry or default_calculation_check_registry()

    try:
        snapshot = capture_repository(
            repository,
            layout.observed / "snapshot",
            run_id,
            captured_at=created_at,
            preferred_full_digest_paths=(report,) if report is not None else (),
            material_full_digest_paths=material_inputs,
        )
        journal.snapshot_id = str(snapshot.snapshot_record["snapshot_id"])
        validator.validate(snapshot.snapshot_record)
        write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)
        if after_snapshot is not None:
            after_snapshot(repository)
        _check_run_control(active_control, journal, "snapshot")
        journal.record_stage("snapshot", "completed", "Immutable repository snapshot persisted.")
        journal.transition_to(AuditState.SNAPSHOTTED)
        _notify_stage(stage_hook, journal, active_control)
        _check_run_control(active_control, journal, "inventory")
        _check_prelock_deadline(active_deadline, journal, "inventory")

        public_file_records = build_file_records(
            snapshot.file_records,
            snapshot.asset_identity_records,
            snapshot.snapshot_record["snapshot_id"],
            created_at,
        )
        for record in [*public_file_records, *snapshot.asset_identity_records]:
            validator.validate(record)
            observed_store.append(record)
        journal.record_stage(
            "inventory",
            "completed",
            "Whole-repository inventory and tiered identities persisted.",
        )
        journal.transition_to(AuditState.INVENTORIED)
        _notify_stage(stage_hook, journal, active_control)
        _check_run_control(active_control, journal, "parsing")
        _check_prelock_deadline(active_deadline, journal, "parsing")

        parser_cache = inspect_supported_sources_with_cache(
            snapshot,
            repository,
            run_id,
            created_at,
            key_provider=cache_key_provider,
        )
        parser_results = parser_cache.parser_results
        descendant_cache = DescendantCacheSession.from_parser_cache(parser_cache, created_at)
        static_graph, parser_results, graph_gap_paths = _promote_static_parser_graphs(
            parser_results,
            created_at,
            descendant_cache=descendant_cache,
            parser_cache_keys=parser_cache.cache_keys_by_path,
        )
        python_scopes = sorted(
            parser_scope_key(result)
            for result in parser_results
            if result.get("parser_id") == "parser:python-ast-tokenize"
        )
        static_cache_keys = [
            str(descendant_cache.current_index[f"static_graph:{scope}"]["cache_key"])
            for scope in python_scopes
            if f"static_graph:{scope}" in descendant_cache.current_index
        ]
        lineage_inputs = (
            [*static_cache_keys, bounded_lineage_runtime_digest()]
            if len(static_cache_keys) == len(python_scopes) and python_scopes
            else []
        )
        lineage_payload, lineage_cache_handle = descendant_cache.resolve(
            category="bounded_lineage",
            scope_key="repository",
            component_id="verifier:bounded-lineage-plane",
            component_version="1.0.0",
            input_digests=lineage_inputs,
            compute=bind_args(
                _build_bounded_lineage_payload,
                snapshot.materialized_root,
                parser_results,
                static_graph["operations"],
                static_graph["artifacts"],
                run_id,
                created_at,
            ),
        )
        bounded_lineage = bounded_lineage_from_payload(
            lineage_payload,
            run_id,
            created_at,
        )
        descendant_cache.record_outputs(
            lineage_cache_handle,
            _bounded_lineage_records(bounded_lineage),
        )

        def large_artifact_read_checkpoint() -> None:
            _check_run_control(active_control, journal, "parsing")
            _check_prelock_deadline(active_deadline, journal, "parsing")

        tabular_inventory = inspect_delimited_inventory(
            snapshot,
            static_graph["artifacts"],
            bounded_lineage.data_assets,
            run_id,
            created_at,
            read_checkpoint=large_artifact_read_checkpoint,
        )
        if tabular_inventory.read_receipts:
            snapshot.snapshot_record["extensions"]["x-delimited-read-receipts"] = [
                item.to_dict() for item in tabular_inventory.read_receipts
            ]

        h5ad_inventory = inspect_h5ad_inventory(
            snapshot,
            [*static_graph["artifacts"], *tabular_inventory.artifacts],
            run_id,
            created_at,
            read_checkpoint=large_artifact_read_checkpoint,
        )
        if h5ad_inventory.read_receipts:
            snapshot.snapshot_record["extensions"]["x-h5ad-read-receipts"] = [
                item.to_dict() for item in h5ad_inventory.read_receipts
            ]
        nextflow_trace = inspect_nextflow_trace(snapshot, run_id, created_at)
        if nextflow_trace.parser_result is not None:
            parser_results = sorted(
                [*parser_results, nextflow_trace.parser_result],
                key=lambda item: (
                    str(item.get("source_ref", {}).get("path", "")),
                    str(item.get("parser_id", "")),
                ),
            )
        data_assets_by_id = {
            str(item["data_asset_id"]): item
            for item in [
                *bounded_lineage.data_assets,
                *tabular_inventory.data_assets,
                *h5ad_inventory.data_assets,
            ]
        }
        data_assets = [data_assets_by_id[key] for key in sorted(data_assets_by_id)]
        variables_by_id = {
            str(item["variable_id"]): item
            for item in [
                *bounded_lineage.variables,
                *tabular_inventory.variables,
                *h5ad_inventory.variables,
            ]
        }
        variables = [variables_by_id[key] for key in sorted(variables_by_id)]
        project_environments = inspect_project_environments(
            snapshot,
            public_file_records,
            run_id,
            created_at,
        )
        environments_by_id = {
            str(item["environment_id"]): item
            for item in [
                *bounded_lineage.environments,
                *project_environments,
                *nextflow_trace.environments,
            ]
        }
        environments = [environments_by_id[key] for key in sorted(environments_by_id)]
        executions = sorted(
            [*bounded_lineage.executions, *nextflow_trace.executions],
            key=lambda item: str(item["execution_id"]),
        )
        descendant_cache_summary = descendant_cache.finalize()
        parser_cache.close()
        cache_entries = [*parser_cache.cache_entries, *descendant_cache.cache_entries]
        graph_gap_paths = sorted(set(graph_gap_paths) | set(bounded_lineage.promotion_gap_paths))
        publication_artifacts, publication_identities = _build_publication_candidates(
            snapshot,
            parser_results,
            run_id,
            created_at,
            explicit_report=report,
            static_artifacts=static_graph["artifacts"],
            static_asset_identities=static_graph["asset_identities"],
        )
        artifacts_by_id = {
            str(item["artifact_id"]): item
            for item in [
                *static_graph["artifacts"],
                *tabular_inventory.artifacts,
                *h5ad_inventory.artifacts,
            ]
        }
        artifacts_by_id.update({str(item["artifact_id"]): item for item in publication_artifacts})
        all_artifacts = [artifacts_by_id[key] for key in sorted(artifacts_by_id)]
        asset_identities_by_id = {
            str(item["asset_identity_id"]): item
            for item in [
                *static_graph["asset_identities"],
                *tabular_inventory.asset_identities,
                *h5ad_inventory.asset_identities,
                *publication_identities,
            ]
        }
        all_graph_asset_identities = [
            asset_identities_by_id[key] for key in sorted(asset_identities_by_id)
        ]
        for record in [
            *parser_results,
            *static_graph["operations"],
            *all_artifacts,
            *all_graph_asset_identities,
            *bounded_lineage.observed_results,
            *data_assets,
            *variables,
            *bounded_lineage.analysis_decisions,
            *bounded_lineage.selection_envelopes,
            *executions,
            *environments,
            parser_cache.cache_policy,
            *cache_entries,
        ]:
            validator.validate(record)
            observed_store.append(record)
        journal.record_stage(
            "parsing",
            "completed",
            "Supported Python and Markdown files were statically inspected, bounded CSV/TSV or "
            "gzip-compressed headers and explicitly selected dense or sparse H5AD inputs were "
            "inventoried, the default "
            "Nextflow trace profile was imported when available, and unsupported paths were "
            "retained as coverage gaps.",
        )
        journal.transition_to(AuditState.PARSED)
        _notify_stage(stage_hook, journal, active_control)
        _check_run_control(active_control, journal, "semantic_lock")
        semantic_lock_elapsed = _check_prelock_deadline(active_deadline, journal, "semantic_lock")

        snapshot.snapshot_record["live_workspace_state"] = merge_workspace_state(
            snapshot.snapshot_record["live_workspace_state"],
            detect_workspace_divergence(
                repository,
                snapshot.file_records,
                detected_at=created_at,
                initial_asset_identities=snapshot.asset_identity_records,
                identity_policy=snapshot.identity_policy,
            ),
        )
        write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)

        publication_surface, questions = _resolve_publication_surface(
            run_id,
            created_at,
            publication_artifacts,
            explicit_report=report,
        )
        answers: list[dict[str, Any]] = []
        scope_selection_build = build_scope_selection_contracts(
            run_id=run_id,
            created_at=created_at,
            repository_snapshot=snapshot.snapshot_record,
            file_records=public_file_records,
            asset_identities=[
                *snapshot.asset_identity_records,
                *all_graph_asset_identities,
            ],
            parser_results=parser_results,
            artifacts=all_artifacts,
            explicit_material_inputs=material_inputs,
        )
        questions.extend(scope_selection_build.questions)
        claims, scientific_contracts, semantic_assertions = _extract_resolved_literal_claims(
            run_id,
            created_at,
            parser_results,
            publication_artifacts,
            publication_surface,
        )
        scientific_check_lock: dict[str, Any] = {
            "profile_id": active_scientific_checks.profile_id,
            "registry_digest": active_scientific_checks.registry_digest,
            "binding_lane": scientific_check_lane,
            "production_promotion_permitted": scientific_check_lane == "qualified",
            "enabled_modules": [
                {
                    "manifest": module.manifest.to_dict(),
                    "manifest_digest": module.declared_manifest_digest,
                    "adapter_manifests": [
                        adapter.to_dict() for adapter in module.adapter_manifests
                    ],
                }
                for module in selected_scientific_modules
            ],
            "unavailable_modules": [
                {
                    "manifest": manifest.to_dict(),
                    "manifest_digest": manifest.manifest_digest,
                }
                for manifest in sorted(
                    active_scientific_checks.unavailable_manifests,
                    key=lambda item: item.check_id,
                )
            ],
            "method_conflict_bindings": [
                binding.to_dict()
                for binding in sorted(
                    selected_method_conflict_bindings,
                    key=lambda item: item.binding_id,
                )
            ],
            "evaluation": None,
            "non_inferences": [
                "Installed checks do not establish scientific intent.",
                "Unavailable adapters do not imply that a method is absent or correct.",
                "Question-only checks cannot emit Findings.",
            ],
        }
        scientific_check_disclosures: list[dict[str, Any]] = []
        calculation_observations: list[dict[str, Any]] = []
        calculation_disclosures: list[dict[str, Any]] = []
        calculation_check_lock: dict[str, Any] = {
            "profile_id": active_calculation_checks.profile_id,
            "registry_digest": active_calculation_checks.registry_digest,
            "enabled_modules": [
                {
                    "check_manifest": module.manifest.to_dict(),
                    "adapter_manifests": [
                        adapter.manifest.to_dict() for adapter in module.adapters
                    ],
                }
                for module in sorted(
                    active_calculation_checks.modules,
                    key=lambda item: item.manifest.check_id,
                )
            ],
            "evaluation": None,
            "non_inferences": [
                "Calculation observations do not establish project-code execution.",
                "A numerical mismatch does not establish publication use or scientific intent.",
                "Unqualified calculation checks cannot emit Findings.",
            ],
        }
        scientific_context = build_frozen_inspection_context(
            snapshot_root=snapshot.materialized_root,
            snapshot_digest=str(snapshot.snapshot_record["snapshot_digest"]),
            file_records=public_file_records,
            asset_identities=[
                *snapshot.asset_identity_records,
                *all_graph_asset_identities,
            ],
            parser_results=parser_results,
            operations=static_graph["operations"],
            artifacts=all_artifacts,
            publication_surface=publication_surface,
            repository_snapshot=snapshot.snapshot_record,
            executions=executions,
            environments=environments,
            scope_selections=scope_selection_build.projection,
            selection_evidence_records=questions,
        )
        if scientific_context is not None and evaluation_inspection_observer is not None:
            scientific_context = _bind_frozen_file_manifest_input(
                scientific_context,
                manifest_root=layout.root,
                repository_snapshot=snapshot.snapshot_record,
            )
        if scientific_context is not None and method_contract_lock is not None:
            from sc_referee.method_contract_run import (
                preflight_frozen_scientific_requirement,
            )

            scientific_context = preflight_frozen_scientific_requirement(
                lock_path=method_contract_lock,
                schema_root=schema_root,
                context=scientific_context,
                file_records=public_file_records,
                asset_identities=snapshot.asset_identity_records,
                scientific_check_registry=active_scientific_checks,
                scientific_check_lane=scientific_check_lane,
            )
        if dependence_authorization_lock is not None:
            if scientific_context is None:
                raise ValueError(
                    "a dependence authorization lock requires one frozen inspection context"
                )
            from sc_referee.dependence_recognition.authority_lock import (
                apply_dependence_authorization_lock_with_receipt,
                bind_dependence_selected_writer_scope,
                dependence_authorization_disclosure,
            )

            assert dependence_authorization_case_id is not None
            scientific_context, verified_authority = (
                apply_dependence_authorization_lock_with_receipt(
                    scientific_context,
                    dependence_authorization_lock,
                    expected_case_id=dependence_authorization_case_id,
                )
            )
            scientific_check_disclosures.append(
                dependence_authorization_disclosure(
                    verified_authority,
                    run_id=run_id,
                    created_at=created_at,
                    affected_ref=scientific_context.selected_surface_ref,
                )
            )
            scientific_context = bind_dependence_selected_writer_scope(
                scientific_context,
                declared_execution_root=verified_authority.declared_execution_root,
            )
            dependence_records = {
                (item.ref.record_type, item.ref.record_id): json.loads(item.canonical_payload)
                for item in scientific_context.base_records
                if item.ref.record_type in {"operation", "artifact"}
            }
            static_graph["operations"] = [
                dependence_records.get(("operation", str(item["operation_id"])), item)
                for item in static_graph["operations"]
            ]
            all_artifacts = [
                dependence_records.get(("artifact", str(item["artifact_id"])), item)
                for item in all_artifacts
            ]
        if scientific_context is not None:
            if evaluation_inspection_observer is not None:
                evaluation_inspection_observer(scientific_context)
            scientific_evaluation = active_scientific_checks.evaluate(
                scientific_context, lane=scientific_check_lane
            )
            compile_records = (
                compile_multiple_testing_development_records
                if scientific_check_lane == "development"
                else compile_scientific_check_records
            )
            scientific_compilation = compile_records(
                registry=active_scientific_checks,
                evaluation=scientific_evaluation,
                context=scientific_context,
                run_id=run_id,
                created_at=created_at,
            )
            scientific_contracts.extend(scientific_compilation.contracts)
            semantic_assertions.extend(scientific_compilation.assertions)
            questions.extend(scientific_compilation.questions)
            scientific_check_disclosures.extend(scientific_compilation.disclosures)
            scientific_check_lock["evaluation"] = scientific_evaluation.to_dict()
            scientific_check_lock["context_digest"] = scientific_context.context_digest
            assert scientific_context.scope_join_graph is not None
            scientific_check_lock["scope_join_graph"] = (
                scientific_context.scope_join_graph.to_lock_projection()
            )
            expected_count_obligation = compile_unresolved_expected_count_obligation(
                context=scientific_context,
                run_id=run_id,
                created_at=created_at,
            )
            if expected_count_obligation is not None:
                scientific_contracts.append(expected_count_obligation.contract)
                questions.append(expected_count_obligation.question)
            scientific_check_lock["expected_count_unresolved_obligation"] = {
                "profile_id": EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID,
                "profile_digest": EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST,
                "applicable": expected_count_obligation is not None,
                **(
                    {
                        "evidence_digest": expected_count_obligation.question["extensions"][
                            "x-unresolved-obligation-evidence-digest"
                        ]
                    }
                    if expected_count_obligation is not None
                    else {}
                ),
            }
            calculation_context_build = build_calculation_context(
                snapshot=snapshot,
                scientific_context=scientific_context,
                artifacts=all_artifacts,
                read_checkpoint=large_artifact_read_checkpoint,
            )
            if calculation_context_build is not None:
                calculation_context = calculation_context_build.context
                if calculation_context_build.read_receipts:
                    snapshot.snapshot_record["extensions"][
                        "x-delimited-calculation-read-receipts"
                    ] = list(calculation_context_build.read_receipts)
                calculation_evaluation = active_calculation_checks.evaluate(calculation_context)
                legacy_calculation_evaluation, feature_identity_compilation = (
                    partition_feature_identifier_identity_evaluation(
                        calculation_evaluation,
                        run_id=run_id,
                        created_at=created_at,
                    )
                )
                calculation_compilation = compile_calculation_records(
                    legacy_calculation_evaluation,
                    run_id=run_id,
                    created_at=created_at,
                )
                calculation_observations.extend(calculation_compilation.observations)
                calculation_observations.extend(feature_identity_compilation.observations)
                questions.extend(calculation_compilation.questions)
                questions.extend(feature_identity_compilation.questions)
                calculation_disclosures.extend(calculation_compilation.disclosures)
                calculation_disclosures.extend(feature_identity_compilation.disclosures)
                calculation_check_lock["evaluation"] = calculation_evaluation.to_dict()
                calculation_check_lock["context_digest"] = calculation_context.context_digest
            else:
                calculation_check_lock["evaluation_limitation"] = (
                    "A calculation-check context requires one immutable selected report."
                )
        else:
            scientific_check_lock["evaluation_limitation"] = (
                "A scientific-check base view requires one resolved selected publication surface."
            )
            calculation_check_lock["evaluation_limitation"] = (
                "A calculation-check context requires one resolved selected publication surface."
            )
        method_contract_binding: dict[str, Any] | None = None
        if method_contract_lock is not None:
            from sc_referee.method_contract_run import bind_frozen_method_contract

            method_contract_binding = bind_frozen_method_contract(
                lock_path=method_contract_lock,
                schema_root=schema_root,
                snapshot_record=snapshot.snapshot_record,
                file_records=public_file_records,
                asset_identities=snapshot.asset_identity_records,
                claims=claims,
                contracts=scientific_contracts,
                assertions=semantic_assertions,
                questions=questions,
                answers=answers,
                scientific_check_registry=active_scientific_lane_registry,
                run_id=run_id,
                created_at=created_at,
                material_inputs=(
                    scientific_context.material_inputs if scientific_context is not None else ()
                ),
            )
        claims = bind_bounded_claim_lineage(
            claims,
            bounded_lineage.observed_results,
            static_graph["operations"],
            data_assets,
            bounded_lineage.executions,
            all_artifacts,
        )
        reproduction_requests = build_reproduction_requests(
            claims,
            environments,
            str(snapshot.snapshot_record["snapshot_digest"]),
            run_id,
            created_at,
        )
        for record in reproduction_requests:
            validator.validate(record)
        questions.extend(
            _build_contract_questions(
                run_id,
                created_at,
                claims,
                scientific_contracts,
                semantic_assertions,
            )
        )
        for record in [
            *claims,
            *scientific_contracts,
            *semantic_assertions,
            *questions,
            *answers,
            *calculation_observations,
        ]:
            validator.validate(record)
        for record in calculation_observations:
            observed_store.append(record)
        unsupported_paths = _unsupported_source_paths(snapshot.file_records)
        disclosures = [
            *_general_disclosures(
                run_id,
                created_at,
                publication_artifacts,
                public_file_records,
                static_graph["operations"],
                unsupported_paths,
                graph_gap_paths,
            ),
            *scientific_check_disclosures,
            *calculation_disclosures,
        ]
        coverage_inputs = _general_coverage_inputs(
            snapshot,
            public_file_records,
            parser_results,
            publication_artifacts,
            publication_surface,
            static_graph["operations"],
            data_assets,
            bounded_lineage.selection_envelopes,
            unsupported_paths,
            graph_gap_paths,
        )
        locked_at = _timestamp_now()
        performance_record = build_semantic_lock_performance_record(
            audit_run_id=run_id,
            recorded_at=locked_at,
            user_visible_elapsed_seconds=semantic_lock_elapsed,
            paused_for_scientist_seconds=0.0,
            snapshot_record=snapshot.snapshot_record,
            cache_summary=parser_cache.summary,
        )
        validator.validate(performance_record)
        bounded_direction_manifest = load_capability_detector_manifest(
            default_capability_manifest_root(),
            schema_root,
            BoundedReportMeanDirectionDetector.detector_id,
        )
        # Fail before locking if packaged implementation identity drifted from its public manifest.
        BoundedReportMeanDirectionDetector(bounded_direction_manifest)
        bounded_method_manifest = load_capability_detector_manifest(
            default_capability_manifest_root(),
            schema_root,
            BoundedReportedMethodContractConflictDetector.detector_id,
        )
        BoundedReportedMethodContractConflictDetector(bounded_method_manifest)
        feature_identity_manifest = load_capability_detector_manifest(
            default_capability_manifest_root(),
            schema_root,
            BoundedFeatureIdentifierIdentityDetector.detector_id,
        )
        BoundedFeatureIdentifierIdentityDetector(feature_identity_manifest)
        registered_method_conflict_manifests = validate_registered_method_conflict_manifests(
            active_scientific_checks,
            schema_root,
            lane=scientific_check_lane,
        )
        locked_case: dict[str, Any] = {
            "lock_kind": "general_static_v1",
            "lock_version": "0.1.0",
            "audit_run_id": run_id,
            "locked_at": locked_at,
            "snapshot_digest": snapshot.snapshot_record["snapshot_digest"],
            "model_calls": [],
            "model_access_after_lock": False,
            "deadline_policy": {
                "mode": mode,
                "scheduling_cutoff_seconds": active_deadline.scheduling_cutoff_seconds,
                "hard_seconds": active_deadline.hard_seconds,
                "scientist_wait_pauses_elapsed_time": True,
            },
            "agent_inputs": [],
            "repository_snapshot": snapshot.snapshot_record,
            "file_records": public_file_records,
            "asset_identities": [
                *snapshot.asset_identity_records,
                *all_graph_asset_identities,
            ],
            "parser_results": parser_results,
            "operations": static_graph["operations"],
            "artifacts": all_artifacts,
            "observed_results": bounded_lineage.observed_results,
            "deterministic_check_observations": calculation_observations,
            "data_assets": data_assets,
            "variables": variables,
            "analysis_decisions": bounded_lineage.analysis_decisions,
            "selection_envelopes": bounded_lineage.selection_envelopes,
            "executions": executions,
            "project_execution_authorizations": [],
            "environments": environments,
            "reproduction_requests": reproduction_requests,
            "performance_records": [performance_record],
            "scientific_contracts": scientific_contracts,
            "semantic_assertions": semantic_assertions,
            "claims": claims,
            "detector_manifests": [
                *registered_method_conflict_manifests,
                bounded_direction_manifest,
                bounded_method_manifest,
                feature_identity_manifest,
            ],
            "publication_surfaces": [publication_surface],
            "material_questions": questions,
            "answers": answers,
            "disclosures": disclosures,
            "cache_entries": cache_entries,
            "cache_policies": [parser_cache.cache_policy],
            "cache_summary": {
                **parser_cache.summary,
                "descendants": descendant_cache_summary,
            },
            "coverage_inputs": coverage_inputs,
            "scope_selections": scope_selection_build.projection,
            "scientific_check_registry": scientific_check_lock,
            "calculation_check_registry": calculation_check_lock,
            **(
                {"parent_method_contract_binding": method_contract_binding}
                if method_contract_binding is not None
                else {}
            ),
        }
        locked_case["semantic_lock_digest"] = semantic_digest(locked_case)
        write_normalized_json(layout.lock_path, locked_case)
        journal.record_stage(
            "semantic_lock",
            "completed",
            "Static records, unresolved semantics, and coverage inputs were locked without model-derived premises.",
        )
        journal.transition_to(AuditState.SEMANTICS_LOCKED)
        _notify_stage(stage_hook, journal, active_control)

        partial = _general_postlock_checkpoint(
            locked_case,
            output,
            schema_root,
            journal,
            active_deadline,
            active_control,
            next_stage="detection",
        )
        if partial is not None:
            return partial

        detector_evaluation = _evaluate_general_detectors(locked_case)
        detector_results = list(detector_evaluation.results)
        detector_findings = list(detector_evaluation.findings)
        candidate_count = sum(
            result.get("state") == "evaluation_finding_candidate" for result in detector_results
        )
        finding_count = len(detector_findings)
        journal.record_stage(
            "detection",
            "completed",
            (
                f"Evaluated {len(detector_results)} bounded experimental detector target(s); "
                f"{candidate_count} evaluation candidate(s) remain ineligible for production "
                f"Findings; {finding_count} qualified Finding(s) admitted."
                if finding_count
                else f"Evaluated {len(detector_results)} bounded experimental detector target(s); "
                f"{candidate_count} evaluation candidate(s) remain ineligible for production Findings."
            ),
        )
        journal.transition_to(AuditState.DETECTED)
        _notify_stage(stage_hook, journal, active_control)
        partial = _general_postlock_checkpoint(
            locked_case,
            output,
            schema_root,
            journal,
            active_deadline,
            active_control,
            next_stage="report",
        )
        if partial is not None:
            return partial
        bundle = _derive_general_from_lock(
            locked_case,
            output,
            schema_root,
            finalize=False,
            detector_results=detector_results,
            detector_findings=detector_findings,
        )
        journal.record_stage("report", "completed", "Canonical bundle, SQLite, and HTML persisted.")
        journal.transition_to(AuditState.REPORTED)
        _notify_stage(stage_hook, journal, active_control)
        partial = _general_postlock_checkpoint(
            locked_case,
            output,
            schema_root,
            journal,
            active_deadline,
            active_control,
            next_stage="integrity",
        )
        if partial is not None:
            return partial
        journal.record_stage(
            "integrity", "completed", "Public records validated before completion."
        )
        journal.transition_to(AuditState.COMPLETE)
        return _finalize_bundle(
            bundle,
            locked_case,
            layout,
            validator,
            JsonlRecordStore(layout.derived),
        )
    except Exception:
        if journal.state not in {
            AuditState.COMPLETE,
            AuditState.PARTIAL_DEADLINE,
            AuditState.PARTIAL_HOST_LIMIT,
            AuditState.CANCELLED,
            AuditState.FAILED_CONTROLLER,
        }:
            journal.record_stage(
                "controller",
                "failed",
                "The controller could not complete the general static audit; completed records were preserved.",
                ErrorCode.CONTROLLER_INTEGRITY_FAILURE,
            )
            journal.transition_to(AuditState.FAILED_CONTROLLER)
        raise
    finally:
        if parser_cache is not None:
            parser_cache.close()


def _continue_demo_run(
    repository: Path,
    output: Path,
    schema_root: Path,
    layout: AuditLayout,
    locked_case: dict[str, Any],
    snapshot: SnapshotOutput,
    file_store: JsonlRecordStore,
    journal: _RunJournal,
    active_deadline: AuditDeadline,
    run_control: RunControl,
    after_snapshot: Callable[[Path], None] | None,
    stage_hook: Callable[[str, RunControl], None] | None,
) -> dict[str, Any]:
    run_id = locked_case["audit_run_id"]
    validator = journal.validator
    if after_snapshot is not None:
        after_snapshot(repository)
    _observe_live_workspace(
        repository,
        snapshot.snapshot_record,
        snapshot.file_records,
        snapshot.asset_identity_records,
        snapshot.identity_policy,
        locked_case,
    )
    write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)
    _check_run_control(run_control, journal, "snapshot")
    journal.record_stage("snapshot", "completed", "Immutable repository snapshot persisted.")
    journal.transition_to(AuditState.SNAPSHOTTED)
    _notify_stage(stage_hook, journal, run_control)
    _check_run_control(run_control, journal, "inventory")
    _check_prelock_deadline(active_deadline, journal, "inventory")

    public_file_records = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        snapshot.snapshot_record["snapshot_id"],
        locked_case["locked_at"],
    )
    for record in public_file_records:
        validator.validate(record)
        file_store.append(record)
    for record in snapshot.asset_identity_records:
        validator.validate(record)
        file_store.append(record)
    journal.record_stage(
        "inventory",
        "completed",
        "Repository file inventory and tiered asset identities persisted.",
    )
    journal.transition_to(AuditState.INVENTORIED)
    _notify_stage(stage_hook, journal, run_control)
    _check_run_control(run_control, journal, "parsing")
    _check_prelock_deadline(active_deadline, journal, "parsing")

    python_result = inspect_python(snapshot.materialized_root / "analysis.py", run_id)
    markdown_result = inspect_markdown(snapshot.materialized_root / "report.md", run_id)
    observed_graph = _derive_repository_observed_graph(
        locked_case,
        snapshot.materialized_root,
        python_result,
        markdown_result,
    )
    for record in [
        *observed_graph["operations"],
        *observed_graph["artifacts"],
        observed_graph["observed_result"],
        *observed_graph["asset_identities"],
    ]:
        validator.validate(record)
        file_store.append(record)
    write_normalized_json(layout.observed / "python-parse.json", python_result)
    write_normalized_json(layout.observed / "markdown-inventory.json", markdown_result)
    journal.record_stage(
        "parsing",
        "completed",
        "Python operations, verified scalar lineage, and exact Markdown claim span persisted.",
    )
    journal.transition_to(AuditState.PARSED)
    _notify_stage(stage_hook, journal, run_control)
    _check_run_control(run_control, journal, "semantic_lock")
    _check_prelock_deadline(active_deadline, journal, "semantic_lock")

    _observe_live_workspace(
        repository,
        snapshot.snapshot_record,
        snapshot.file_records,
        snapshot.asset_identity_records,
        snapshot.identity_policy,
        locked_case,
    )
    write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)

    locked_case["snapshot_digest"] = snapshot.snapshot_record["snapshot_digest"]
    locked_case["observed_graph"] = observed_graph
    locked_case["repeated_identifier_observation"] = inspect_repeated_identifier(
        snapshot.materialized_root / "data.csv", "sample_id", run_id
    )
    locked_case["source_references_verified"] = _verify_locked_sources(
        locked_case, snapshot.materialized_root
    )
    fixture_manifest = load_fixture_detector_envelope(
        snapshot.materialized_root / locked_case["detector_manifest_path"],
        locked_case["detector_manifest_digest"],
    )
    locked_case["fixture_detector_envelope"] = fixture_manifest.to_lock_record()
    _record_inventory_coverage_inputs(
        locked_case,
        snapshot.file_records,
        [python_result, markdown_result],
        observed_graph["observed_result"],
    )
    locked_case["workspace_divergence"] = snapshot.snapshot_record["live_workspace_state"]
    locked_case["asset_identities"] = [
        *snapshot.asset_identity_records,
        *observed_graph["asset_identities"],
    ]
    locked_case["file_records"] = public_file_records
    locked_case["semantic_lock_digest"] = semantic_digest(locked_case)
    write_normalized_json(layout.lock_path, locked_case)
    journal.record_stage("semantic_lock", "completed", "Semantic lock persisted.")
    journal.transition_to(AuditState.SEMANTICS_LOCKED)
    _notify_stage(stage_hook, journal, run_control)

    if run_control.cancellation_requested:
        _check_run_control(run_control, journal, "detection")
    if run_control.host_model_limit_reached:
        return _finish_partial_run(
            locked_case,
            output,
            schema_root,
            snapshot.snapshot_record,
            [python_result, markdown_result],
            journal,
            termination_reason="host_model_limit",
        )

    try:
        active_deadline.check()
    except DeadlineExceededError:
        return _finish_partial_run(
            locked_case,
            output,
            schema_root,
            snapshot.snapshot_record,
            [python_result, markdown_result],
            journal,
            termination_reason="hard_deadline",
        )
    if active_deadline.scheduling_cutoff_reached:
        return _finish_partial_run(
            locked_case,
            output,
            schema_root,
            snapshot.snapshot_record,
            [python_result, markdown_result],
            journal,
            termination_reason="scheduling_cutoff",
        )

    bundle = _derive_from_lock(
        locked_case,
        output,
        schema_root,
        snapshot.snapshot_record,
        [python_result, markdown_result],
        finalize=False,
    )
    journal.record_stage("detection", "completed", "Scheduled detector targets evaluated.")
    journal.transition_to(AuditState.DETECTED)
    _notify_stage(stage_hook, journal, run_control)
    _check_run_control(run_control, journal, "report")
    journal.record_stage("report", "completed", "Bundle, SQLite index, and HTML persisted.")
    journal.transition_to(AuditState.REPORTED)
    _notify_stage(stage_hook, journal, run_control)
    _check_run_control(run_control, journal, "integrity")
    journal.record_stage("integrity", "completed", "Public records validated before completion.")
    journal.transition_to(AuditState.COMPLETE)
    return _finalize_bundle(
        bundle,
        locked_case,
        layout,
        LocalSchemaRegistry(schema_root),
        JsonlRecordStore(layout.derived),
    )


def _inspect_supported_repository_sources(
    snapshot: SnapshotOutput, run_id: str
) -> list[dict[str, Any]]:
    parser_results: list[dict[str, Any]] = []
    for file_record in sorted(snapshot.file_records, key=lambda item: str(item["path"])):
        if file_record.get("entry_kind") != "regular_file":
            continue
        relative_path = str(file_record["path"])
        materialized = snapshot.materialized_root / relative_path
        if not materialized.is_file() or materialized.is_symlink():
            continue
        suffix = PurePosixPath(relative_path).suffix.lower()
        if suffix == ".ipynb":
            parent = inspect_jupyter(materialized, run_id, source_path=relative_path)
            parser_results.extend(
                [parent, *inspect_embedded_cell_sources(materialized, parent, run_id)]
            )
        elif suffix == ".py":
            parser_results.append(inspect_python(materialized, run_id, source_path=relative_path))
        elif suffix == ".qmd":
            parent = inspect_quarto(materialized, run_id, source_path=relative_path)
            parser_results.extend(
                [parent, *inspect_embedded_cell_sources(materialized, parent, run_id)]
            )
        elif suffix == ".r":
            parser_results.extend(inspect_r(materialized, run_id, source_path=relative_path))
        elif suffix in {".md", ".markdown"}:
            parser_results.append(inspect_markdown(materialized, run_id, source_path=relative_path))
        elif suffix == ".rmd":
            parent = inspect_rmarkdown(materialized, run_id, source_path=relative_path)
            parser_results.extend(
                [parent, *inspect_embedded_cell_sources(materialized, parent, run_id)]
            )
    return parser_results


def _promote_static_parser_graphs(
    parser_results: list[dict[str, Any]],
    created_at: str,
    *,
    descendant_cache: DescendantCacheSession | None = None,
    parser_cache_keys: dict[str, str] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[str]]:
    operations: dict[str, dict[str, Any]] = {}
    artifacts: dict[str, dict[str, Any]] = {}
    identities: dict[str, dict[str, Any]] = {}
    normalized_results: list[dict[str, Any]] = []
    gap_paths: list[str] = []
    for parser_result in parser_results:
        if parser_result.get("parser_id") != "parser:python-ast-tokenize":
            normalized_results.append(parser_result)
            continue
        try:
            path = str(parser_result.get("source_ref", {}).get("path", "unknown"))
            scope_key = parser_scope_key(parser_result)
            input_digest = (parser_cache_keys or {}).get(path)
            if descendant_cache is None:
                graph = build_public_static_graph([parser_result], created_at)
                cache_handle = None
            else:
                payload, cache_handle = descendant_cache.resolve(
                    category="static_graph",
                    scope_key=scope_key,
                    component_id="promoter:public-static-graph",
                    component_version="1.0.0",
                    input_digests=[input_digest] if input_digest is not None else [],
                    compute=bind_args(
                        _build_static_graph_payload,
                        parser_result,
                        created_at,
                    ),
                )
                payload = rebind_run(
                    payload,
                    str(parser_result["audit_run_id"]),
                    controller_created_at=created_at,
                )
                graph = _static_graph_from_payload(payload)
            candidate_operations = dict(operations)
            candidate_artifacts = deepcopy(artifacts)
            candidate_identities = dict(identities)
            for operation in graph.operations:
                operation_id = str(operation["operation_id"])
                if (
                    operation_id in candidate_operations
                    and candidate_operations[operation_id] != operation
                ):
                    raise ValueError(f"conflicting Operation identity {operation_id}")
                candidate_operations[operation_id] = operation
            for artifact in graph.artifacts:
                artifact_id = str(artifact["artifact_id"])
                existing = candidate_artifacts.get(artifact_id)
                candidate_artifacts[artifact_id] = (
                    artifact if existing is None else _merge_public_artifact(existing, artifact)
                )
            for identity in graph.artifact_identities:
                identity_id = str(identity["asset_identity_id"])
                if (
                    identity_id in candidate_identities
                    and candidate_identities[identity_id] != identity
                ):
                    raise ValueError(f"conflicting AssetIdentity {identity_id}")
                candidate_identities[identity_id] = identity
            operations = candidate_operations
            artifacts = candidate_artifacts
            identities = candidate_identities
            if descendant_cache is not None and cache_handle is not None:
                descendant_cache.record_outputs(
                    cache_handle,
                    [*graph.operations, *graph.artifacts, *graph.artifact_identities],
                )
        except (KeyError, TypeError, ValueError) as error:
            gap_paths.append(parser_scope_key(parser_result))
            parser_result = _parser_graph_gap(parser_result, error)
        normalized_results.append(parser_result)
    return (
        {
            "operations": [operations[key] for key in sorted(operations)],
            "artifacts": [artifacts[key] for key in sorted(artifacts)],
            "asset_identities": [identities[key] for key in sorted(identities)],
        },
        normalized_results,
        sorted(set(gap_paths)),
    )


def _static_graph_payload(graph: PublicStaticGraph) -> dict[str, Any]:
    return {
        "operations": graph.operations,
        "artifacts": graph.artifacts,
        "artifact_identities": graph.artifact_identities,
    }


def _build_static_graph_payload(parser_result: dict[str, Any], created_at: str) -> dict[str, Any]:
    return _static_graph_payload(build_public_static_graph([parser_result], created_at))


def _build_bounded_lineage_payload(
    materialized_root: Path,
    parser_results: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    return bounded_lineage_payload(
        reconstruct_bounded_results(
            materialized_root,
            parser_results,
            operations,
            artifacts,
            run_id,
            created_at,
        )
    )


def _bounded_lineage_records(output: BoundedLineageOutput) -> list[dict[str, Any]]:
    return [
        *output.observed_results,
        *output.data_assets,
        *output.variables,
        *output.analysis_decisions,
        *output.selection_envelopes,
        *output.executions,
        *output.environments,
    ]


def _static_graph_from_payload(payload: dict[str, Any]) -> PublicStaticGraph:
    fields = ("operations", "artifacts", "artifact_identities")
    if any(not isinstance(payload.get(field), list) for field in fields):
        raise ValueError("cached static graph payload is malformed")
    return PublicStaticGraph(
        operations=deepcopy(payload["operations"]),
        artifacts=deepcopy(payload["artifacts"]),
        artifact_identities=deepcopy(payload["artifact_identities"]),
    )


def _merge_public_artifact(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    scalar_keys = {
        "schema_version",
        "record_type",
        "artifact_id",
        "audit_run_id",
        "kind",
        "observed_role",
        "asset_identity_ref",
        "path",
        "provenance",
    }
    if any(existing.get(key) != incoming.get(key) for key in scalar_keys):
        raise ValueError(f"conflicting Artifact identity {existing.get('artifact_id')}")
    merged = deepcopy(existing)
    for key in (
        "source_refs",
        "producer_operation_refs",
        "consumer_operation_refs",
        "limitations",
    ):
        by_value = {
            canonical_json(value) if isinstance(value, dict) else str(value): value
            for value in [*existing.get(key, []), *incoming.get(key, [])]
        }
        merged[key] = [by_value[value] for value in sorted(by_value)]
    return merged


def _parser_graph_gap(parser_result: dict[str, Any], error: Exception) -> dict[str, Any]:
    result = deepcopy(parser_result)
    source_ref = deepcopy(result["source_ref"])
    result["state"] = "partially_parsed"
    result["coverage_status"] = "partially_covered"
    result["emitted_record_refs"] = []
    result["opaque_constructs"] = [
        *result.get("opaque_constructs", []),
        {
            "kind": "static_graph_promotion_gap",
            "reason": (
                "The parser result was retained, but its operation graph could not be promoted "
                f"without ambiguity ({type(error).__name__})."
            ),
            "source_ref": source_ref,
        },
    ]
    result["extensions"] = {
        **result.get("extensions", {}),
        "x-operations": [],
        "x-artifacts": [],
    }
    return result


def _build_publication_candidates(
    snapshot: SnapshotOutput,
    parser_results: list[dict[str, Any]],
    run_id: str,
    created_at: str,
    *,
    explicit_report: str | None,
    static_artifacts: list[dict[str, Any]] | None = None,
    static_asset_identities: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    explicit_path = _normalize_optional_relative_path(explicit_report)
    parser_by_path: dict[str, dict[str, Any]] = {}
    for result in parser_results:
        source_ref = result.get("source_ref", {})
        if source_ref.get("source_kind") != "file_span":
            continue
        path = source_ref.get("path")
        if not isinstance(path, str):
            continue
        current = parser_by_path.get(path)
        if current is None or result.get("parser_id") == "parser:r-tree-sitter-inventory":
            parser_by_path[path] = result
    report_suffixes = {
        ".md",
        ".markdown",
        ".qmd",
        ".rmd",
        ".ipynb",
        ".html",
        ".htm",
        ".pdf",
        ".tex",
        ".docx",
    }
    artifacts: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    identity_by_id = {
        str(item["asset_identity_id"]): item for item in (static_asset_identities or [])
    }
    for observed in sorted(snapshot.file_records, key=lambda item: str(item["path"])):
        path = str(observed["path"])
        candidate = observed.get("entry_kind") == "regular_file" and (
            PurePosixPath(path).suffix.lower() in report_suffixes
            or observed.get("role") == "report_candidate"
            or path == explicit_path
        )
        digest = observed.get("digest")
        if not candidate or not isinstance(digest, str):
            continue
        static_matches = [
            item
            for item in (static_artifacts or [])
            if item.get("path") == path
            and item.get("kind") == "result_file"
            and item.get("producer_operation_refs")
            and _artifact_has_full_digest(item, identity_by_id, digest)
        ]
        if len(static_matches) == 1:
            linked = deepcopy(static_matches[0])
            linked["kind"] = "report"
            linked["observed_role"] = "publication_surface_candidate_with_static_output_path"
            linked["limitations"] = [
                *linked.get("limitations", []),
                "A static source operation targets this exact report path, but no project Execution establishes that the operation produced the snapshotted bytes or wording.",
            ]
            artifacts.append(linked)
            continue
        artifact_id = stable_id("artifact-publication", path, digest)
        parser_result = parser_by_path.get(path)
        source_ref = (
            deepcopy(parser_result["source_ref"])
            if parser_result is not None
            else {
                "source_kind": "file_span",
                "locator": path,
                "path": path,
                "content_digest": digest,
            }
        )
        identity = build_asset_identity(
            audit_run_id=run_id,
            asset_record_type="artifact",
            asset_record_id=artifact_id,
            evidence=full_digest_evidence(digest),
            created_at=created_at,
        )
        artifacts.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "artifact",
                "artifact_id": artifact_id,
                "audit_run_id": run_id,
                "kind": "report",
                "observed_role": "publication_surface_candidate",
                "path": path,
                "source_refs": [source_ref],
                "producer_operation_refs": [],
                "consumer_operation_refs": [],
                "asset_identity_ref": typed_ref(
                    "asset_identity", str(identity["asset_identity_id"])
                ),
                "limitations": [
                    "File identity and candidacy do not establish that this is the selected final publication surface."
                ],
                "provenance": controller_provenance(
                    "deterministic_publication_candidate_inventory", created_at
                ),
            }
        )
        identities.append(identity)
    if explicit_path is not None and all(item.get("path") != explicit_path for item in artifacts):
        raise ValueError(
            f"explicit report {explicit_path!r} was not a fully identified regular file in the immutable snapshot"
        )
    return artifacts, identities


def _artifact_has_full_digest(
    artifact: dict[str, Any],
    identity_by_id: dict[str, dict[str, Any]],
    digest: str,
) -> bool:
    identity_id = str(artifact.get("asset_identity_ref", {}).get("record_id", ""))
    identity = identity_by_id.get(identity_id)
    return bool(
        identity is not None
        and identity.get("asset_ref", {}).get("record_type") == "artifact"
        and identity.get("asset_ref", {}).get("record_id") == artifact.get("artifact_id")
        and identity.get("tier") == "full_digest"
        and identity.get("identity_evidence", {}).get("kind") == "full_digest"
        and identity.get("identity_evidence", {}).get("digest") == digest
    )


def _normalize_optional_relative_path(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("report must be a safe repository-relative POSIX path")
    return candidate.as_posix()


def _resolve_publication_surface(
    run_id: str,
    created_at: str,
    artifacts: list[dict[str, Any]],
    *,
    explicit_report: str | None,
    scientist_answer_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    explicit_path = _normalize_optional_relative_path(explicit_report)
    artifact_refs = [typed_ref("artifact", str(item["artifact_id"])) for item in artifacts]
    candidates = [
        {
            "surface_ref": typed_ref("artifact", str(item["artifact_id"])),
            "evidence": [
                "explicit_user_target" if item.get("path") == explicit_path else "filename_signal"
            ],
            "notes": (
                "Explicitly selected by the invoking user."
                if item.get("path") == explicit_path
                else "Inventoried as a candidate only; filename is not decisive."
            ),
        }
        for item in artifacts
    ]
    provenance = controller_provenance("publication_surface_precedence", created_at)
    if explicit_path is not None:
        selected = next(item for item in artifacts if item.get("path") == explicit_path)
        resolved_selection: dict[str, Any] = {
            "kind": "resolved",
            "selected_surface_refs": [typed_ref("artifact", str(selected["artifact_id"]))],
            "rationale": (
                "The scientist selected this candidate through a typed answer bound to the "
                "source audit."
                if scientist_answer_id is not None
                else "The invoking user explicitly selected this repository-relative report path."
            ),
        }
        if scientist_answer_id is not None:
            resolved_selection["scientist_answer_id"] = scientist_answer_id
        surface = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "publication_surface",
            "publication_surface_id": stable_id("publication-surface", run_id, explicit_path),
            "audit_run_id": run_id,
            "status": "resolved",
            "candidates": candidates,
            "precedence_policy": [
                "explicit_user_target_or_active_workspace",
                "declared_build_target",
                "explicit_task_or_repository_statement",
                "unique_lineage_evidence",
                "filename_and_time_supporting_only",
            ],
            "selection": resolved_selection,
            "publication_materiality_assessable": True,
            "created_at": created_at,
            "provenance": provenance,
        }
        return surface, []

    unavailable = not artifacts
    question_id = stable_id(
        "question-publication-surface", run_id, *(str(item["artifact_id"]) for item in artifacts)
    )
    candidate_answers = [
        {
            "answer_id": stable_id("answer-option", question_id, str(item["artifact_id"])),
            "label": str(item["path"]),
            "value": str(item["artifact_id"]),
            "consequence": "This artifact becomes the selected publication surface for claim-centric inspection.",
        }
        for item in artifacts
    ]
    if unavailable:
        candidate_answers.append(
            {
                "answer_id": stable_id("answer-option", question_id, "no-surface"),
                "label": "No in-repository final surface",
                "value": "none",
                "consequence": (
                    "Publication materiality remains unassessed and the unavailable surface "
                    "state is retained."
                ),
            }
        )
    candidate_answers.append(
        {
            "answer_id": stable_id("answer-option", question_id, "none-or-unknown"),
            "label": "None or unknown",
            "value": "unknown",
            "consequence": "Publication materiality remains unassessed and candidate audits remain separate.",
        }
    )
    question = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": (
            "Is there an in-repository final publication surface for this audit?"
            if unavailable
            else "Which inventoried artifact is the final publication surface for this audit?"
        ),
        "unknown_semantic_dimension": "publication_surface",
        "why_it_matters": (
            "Without an identified final surface, publication claims and their backward lineage cannot be selected for assessment."
            if unavailable
            else "The selected surface determines which final claims and backward lineage paths are material."
        ),
        "candidate_answers": candidate_answers,
        "evidence_searched": [
            {
                "source": "whole-repository file inventory",
                "result": (
                    "No fully identified publication-like artifact was available."
                    if unavailable
                    else "Filename signals identified candidates but are not sufficient to select one."
                ),
            }
        ],
        "blocked_detector_ids": [
            "detector:claim-result-direction",
            "detector:population-comparison-estimand",
            "detector:denominator-control-set",
            "detector:explicit-dependence",
            "detector:lineage-completeness",
        ],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "high",
        "status": "open",
        "answer_ids": [],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_material_question_generation", created_at
        ),
    }
    selection: dict[str, Any] = {
        "kind": "unresolved",
        "reason": (
            "No fully identified publication-like artifact was available."
            if unavailable
            else "Filename signals cannot establish the final publication surface."
        ),
        "material_question_id": question_id,
    }
    if len(artifact_refs) >= 2:
        selection["candidate_surface_refs"] = artifact_refs
    surface = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "publication_surface",
        "publication_surface_id": stable_id("publication-surface", run_id, "unresolved"),
        "audit_run_id": run_id,
        "status": "unresolved",
        "candidates": candidates,
        "precedence_policy": [
            "explicit_user_target_or_active_workspace",
            "declared_build_target",
            "explicit_task_or_repository_statement",
            "unique_lineage_evidence",
            "filename_and_time_supporting_only",
        ],
        "selection": selection,
        "publication_materiality_assessable": False,
        "created_at": created_at,
        "provenance": provenance,
    }
    return surface, [question]


def _extract_resolved_literal_claims(
    run_id: str,
    created_at: str,
    parser_results: list[dict[str, Any]],
    publication_artifacts: list[dict[str, Any]],
    publication_surface: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Promote only explicit deterministic literals from a resolved Markdown surface."""

    if publication_surface.get("status") != "resolved":
        return [], [], []
    selected_refs = publication_surface.get("selection", {}).get("selected_surface_refs", [])
    if len(selected_refs) != 1:
        return [], [], []
    selected_artifact_id = selected_refs[0].get("record_id")
    artifact = next(
        (item for item in publication_artifacts if item.get("artifact_id") == selected_artifact_id),
        None,
    )
    if artifact is None:
        return [], [], []
    selected_path = artifact.get("path")
    parser_result = next(
        (
            item
            for item in parser_results
            if item.get("parser_id") == "parser:markdown-inventory"
            and item.get("source_ref", {}).get("path") == selected_path
        ),
        None,
    )
    if parser_result is None:
        return [], [], []

    claims: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    assertions: list[dict[str, Any]] = []
    for literal in parser_result.get("extensions", {}).get("x-explicit-directional-claims", []):
        source_ref = deepcopy(literal["source_ref"])
        claim_id = stable_id(
            "claim",
            str(source_ref["content_digest"]),
            str(source_ref["start_line"]),
            str(literal["text"]),
        )
        contract_id = stable_id("scientific-contract", claim_id)
        missing_link = (
            "No unique observed result, producing operation, or input artifact was bound to this "
            "literal claim."
        )
        claim = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "claim",
            "claim_id": claim_id,
            "audit_run_id": run_id,
            "report_ref": typed_ref("artifact", str(selected_artifact_id)),
            "claim_status": "final",
            "claim_kind": "directional",
            "text": literal["text"],
            "source_refs": [source_ref],
            "scientific_contract_id": contract_id,
            "proposition": {
                "subject": literal["literal_subject"],
                "predicate": literal["literal_predicate"],
                "claim_strength": "ambiguous",
                "comparison": literal["literal_comparison"],
                "direction": literal["direction"],
            },
            "lineage": {
                "status": "missing",
                "result_refs": [],
                "operation_refs": [],
                "input_refs": [],
                "missing_links": [missing_link],
                "opaque_dependency_refs": [],
            },
            "extraction": {
                "method": "deterministic",
                "explicit_source_meaning": True,
                "independently_verified": True,
                "semantic_assertion_ids": [],
            },
            "extensions": {
                "x-extraction-basis": literal["extraction_basis"],
                "x-literal-object": literal["literal_object"],
                "x-scientific-semantics-unresolved": True,
            },
        }
        unknown_reason = (
            "This scientific dimension was not established by bounded literal extraction."
        )
        contract = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "scientific_contract",
            "contract_id": contract_id,
            "audit_run_id": run_id,
            "title": f"Unresolved contract for literal claim {claim_id}",
            "status": "draft",
            "scope": {
                "level": "claim",
                "subject_refs": [typed_ref("claim", claim_id)],
            },
            "dimensions": {
                dimension: {
                    "state": "unknown",
                    "reason": unknown_reason,
                    "searched_source_refs": [deepcopy(source_ref)],
                }
                for dimension in _SCIENTIFIC_CONTRACT_DIMENSIONS
            },
            "source_refs": [deepcopy(source_ref)],
            "created_at": created_at,
            "notes": (
                "The explicit claim text is independently checkable; its scientific contract "
                "and computational lineage remain unresolved."
            ),
        }
        claims.append(claim)
        contracts.append(contract)

    extensions = parser_result.get("extensions", {})
    quantitative_literals = extensions.get("x-explicit-quantitative-claims", [])
    method_declarations = extensions.get("x-expected-count-method-declarations", [])
    sensitivities = extensions.get("x-explicit-expected-count-sensitivities", [])
    for literal in quantitative_literals:
        source_ref = deepcopy(literal["source_ref"])
        claim_id = stable_id(
            "claim",
            str(source_ref["content_digest"]),
            str(source_ref["start_line"]),
            str(literal["text"]),
        )
        contract_id = stable_id("scientific-contract", claim_id)
        claim_assertions: list[dict[str, Any]] = []
        if len(quantitative_literals) == 1 and len(method_declarations) == 1:
            declaration = method_declarations[0]
            claim_assertions.append(
                _reported_parser_assertion(
                    run_id=run_id,
                    created_at=created_at,
                    claim_id=claim_id,
                    predicate="reported_expected_count_background_profile",
                    value=deepcopy(declaration["profile"]),
                    source_refs=deepcopy(declaration["source_refs"]),
                    extraction_basis=str(declaration["extraction_basis"]),
                )
            )
            for sensitivity in sensitivities:
                claim_assertions.append(
                    _reported_parser_assertion(
                        run_id=run_id,
                        created_at=created_at,
                        claim_id=claim_id,
                        predicate="reported_expected_count_sensitivity",
                        value={
                            "profile_id": "expected_count_sensitivity_v1",
                            "alternative": sensitivity["alternative"],
                            "values": deepcopy(sensitivity["values"]),
                            "unit": "log2 units",
                        },
                        source_refs=[deepcopy(sensitivity["source_ref"])],
                        extraction_basis=str(sensitivity["extraction_basis"]),
                    )
                )
        assertion_ids = [str(assertion["assertion_id"]) for assertion in claim_assertions]
        missing_link = (
            "No unique observed result, producing operation, or input artifact was bound to this "
            "literal quantitative claim."
        )
        estimate = float(str(literal["estimate_text"]))
        direction = "positive" if estimate > 0 else "negative" if estimate < 0 else "null"
        claim = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "claim",
            "claim_id": claim_id,
            "audit_run_id": run_id,
            "report_ref": typed_ref("artifact", str(selected_artifact_id)),
            "claim_status": "final",
            "claim_kind": "quantitative",
            "text": literal["text"],
            "source_refs": [source_ref],
            "scientific_contract_id": contract_id,
            "proposition": {
                "subject": f"{literal['left_label']} versus {literal['right_label']}",
                "predicate": f"difference in {literal['measure']}",
                "claim_strength": "descriptive",
                "comparison": f"{literal['left_label']} versus {literal['right_label']}",
                "direction": direction,
                "estimate": estimate,
                "scale": "log2",
                "unit": str(literal["unit"]),
            },
            "lineage": {
                "status": "missing",
                "result_refs": [],
                "operation_refs": [],
                "input_refs": [],
                "missing_links": [missing_link],
                "opaque_dependency_refs": [],
            },
            "extraction": {
                "method": "deterministic",
                "explicit_source_meaning": True,
                "independently_verified": True,
                "semantic_assertion_ids": assertion_ids,
            },
            "extensions": {
                "x-extraction-basis": literal["extraction_basis"],
                "x-left-value-text": literal["left_value_text"],
                "x-right-value-text": literal["right_value_text"],
                "x-estimate-text": literal["estimate_text"],
                "x-analysis-resolution-bp": literal["resolution_bp"],
                "x-scientific-semantics-unresolved": True,
                **(
                    {"x-method-profile-id": EXPECTED_COUNT_PROFILE_ID}
                    if any(
                        assertion.get("predicate") == "reported_expected_count_background_profile"
                        for assertion in claim_assertions
                    )
                    else {}
                ),
            },
        }
        unknown_reason = (
            "This scientific dimension was not established by bounded literal extraction."
        )
        contract = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "scientific_contract",
            "contract_id": contract_id,
            "audit_run_id": run_id,
            "title": f"Unresolved expected-count contract for claim {claim_id}",
            "status": "draft",
            "scope": {
                "level": "claim",
                "subject_refs": [typed_ref("claim", claim_id)],
            },
            "dimensions": {
                dimension: {
                    "state": "unknown",
                    "reason": unknown_reason,
                    "searched_source_refs": [deepcopy(source_ref)],
                }
                for dimension in _SCIENTIFIC_CONTRACT_DIMENSIONS
            },
            "source_refs": [deepcopy(source_ref)],
            "created_at": created_at,
            "notes": (
                "The quantitative report wording and any exact method declarations are "
                "reported evidence only; the governing intended method remains unresolved."
            ),
        }
        claims.append(claim)
        contracts.append(contract)
        assertions.extend(claim_assertions)
    return claims, contracts, assertions


def _reported_parser_assertion(
    *,
    run_id: str,
    created_at: str,
    claim_id: str,
    predicate: str,
    value: object,
    source_refs: list[dict[str, Any]],
    extraction_basis: str,
) -> dict[str, Any]:
    assertion_id = stable_id(
        "assertion-reported-method",
        claim_id,
        predicate,
        extraction_basis,
        canonical_json(value),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": assertion_id,
        "audit_run_id": run_id,
        "subject_ref": typed_ref("claim", claim_id),
        "predicate": predicate,
        "object": deepcopy(value),
        "semantic_role": "reported",
        "assertion_class": "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {
            "status": "verified",
            "method": "structural_parser",
            "validator_id": "parser:markdown-inventory:bounded-expected-count-v1",
            "verified_at": created_at,
        },
        "certainty": {
            "level": "explicit",
            "basis": "A closed deterministic grammar reproduced the exact normalized value.",
        },
        "rationale": (
            "The assertion records only the report's exact supported wording and does not "
            "establish intended method or executed computation."
        ),
        "source_refs": source_refs,
        "provenance": {
            "actor": {
                "actor_kind": "parser",
                "actor_id": "parser:markdown-inventory",
            },
            "method": extraction_basis,
            "created_at": created_at,
            "source_refs": deepcopy(source_refs),
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-extraction-profile": extraction_basis,
            "x-authority-limitation": "Reported wording only.",
        },
    }


def _build_contract_questions(
    run_id: str,
    created_at: str,
    claims: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create one bounded structured-intent question for each incomplete claim contract."""

    claims_by_contract = {str(claim["scientific_contract_id"]): claim for claim in claims}
    questions: list[dict[str, Any]] = []
    for contract in contracts:
        contract_id = str(contract["contract_id"])
        claim = claims_by_contract.get(contract_id)
        if claim is None:
            continue
        is_expected_count_profile = (
            claim.get("extensions", {}).get("x-method-profile-id") == EXPECTED_COUNT_PROFILE_ID
        )
        relevant_dimensions = (
            EXPECTED_COUNT_REQUIRED_DIMENSIONS
            if is_expected_count_profile
            else _SCIENTIFIC_CONTRACT_DIMENSIONS
        )
        unresolved = [
            dimension
            for dimension in relevant_dimensions
            if contract.get("dimensions", {}).get(dimension, {}).get("state")
            not in {"known", "not_applicable"}
        ]
        if not unresolved:
            continue
        claim_id = str(claim["claim_id"])
        question_id = stable_id("question-scientific-contract", run_id, contract_id, *unresolved)
        claim_assertions = [
            assertion
            for assertion in assertions
            if assertion.get("subject_ref") == typed_ref("claim", claim_id)
        ]
        reported_method_ids = [
            str(assertion["assertion_id"])
            for assertion in claim_assertions
            if assertion.get("predicate") == "reported_expected_count_background_profile"
        ]
        sensitivity_assertions = [
            assertion
            for assertion in claim_assertions
            if assertion.get("predicate") == "reported_expected_count_sensitivity"
        ]
        posthoc_forms: dict[str, str] = {}
        posthoc_report_ids: dict[str, list[str]] = {}
        for dimension in unresolved:
            candidates = [
                assertion
                for assertion in claim_assertions
                if assertion.get("predicate") == f"reported_{dimension}"
                and assertion.get("semantic_role") == "reported"
                and assertion.get("assertion_class") == "explicit_text_extraction"
                and assertion.get("epistemic_status") == "accepted"
                and assertion.get("authority_scope") == "reported_wording"
                and assertion.get("independently_checkable") is True
                and assertion.get("verification", {}).get("status") == "verified"
                and isinstance(
                    assertion.get("extensions", {}).get("x-posthoc-comparison-form"), str
                )
            ]
            if len(candidates) != 1:
                continue
            comparison_form = str(candidates[0]["extensions"]["x-posthoc-comparison-form"])
            if not posthoc_form_allowed(dimension, comparison_form):
                continue
            posthoc_forms[dimension] = comparison_form
            posthoc_report_ids[dimension] = [str(candidates[0]["assertion_id"])]
        if is_expected_count_profile:
            question_text = (
                "Which expected-count/background profile governs the requested values for "
                f"claim {claim_id}?"
            )
            why_it_matters = (
                "The selected report states one expected-count method, but no authoritative "
                "intended profile is bound to this Claim, so method compatibility cannot yet be "
                "evaluated."
            )
            evidence_searched = [
                {
                    "source": "exact selected-report method spans",
                    "result": (
                        "A closed parser verified one reported expected-count profile; reported "
                        "wording does not establish the governing intended method."
                    ),
                },
                {
                    "source": "exact selected-report sensitivity spans",
                    "result": (
                        f"The report states {len(sensitivity_assertions)} named alternative "
                        "result set(s). These exact values do not establish which profile governs."
                    ),
                },
            ]
            blocked_detector_ids = ["detector:bounded-reported-method-contract-conflict"]
            answer_shape = "expected_count_background_v1-dimension-values"
        else:
            question_text = (
                "Which intended scientific-contract dimensions can the scientist declare "
                f"for claim {claim_id}?"
            )
            why_it_matters = (
                "Detector applicability and interpretation remain unavailable until the "
                "material contract dimensions are explicitly resolved or retained as unknown."
            )
            evidence_searched = [
                {
                    "source": "exact literal claim span",
                    "result": (
                        "Literal wording established the reported claim but did not establish "
                        f"the intended values of {len(unresolved)} contract dimension(s)."
                    ),
                }
            ]
            blocked_detector_ids = [
                "detector:claim-result-direction",
                "detector:population-comparison-estimand",
                "detector:denominator-control-set",
                "detector:explicit-dependence",
                "detector:lineage-completeness",
            ]
            if posthoc_forms:
                evidence_searched.append(
                    {
                        "source": "exact closed reported-method assertions",
                        "result": (
                            f"A closed verifier established {len(posthoc_forms)} reported "
                            "dimension value(s); governing review requirements remain unresolved."
                        ),
                    }
                )
            answer_shape = "object-mapping-dimension-to-scientist-intended-value"
        questions.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "material_question",
                "question_id": question_id,
                "audit_run_id": run_id,
                "question": question_text,
                "unknown_semantic_dimension": "scientific_contract",
                "why_it_matters": why_it_matters,
                "candidate_answers": [
                    {
                        "answer_id": stable_id(
                            "answer-option", question_id, "provide-structured-intent"
                        ),
                        "label": "Provide structured intent",
                        "value": {"action": "provide_structured_intent"},
                        "consequence": (
                            "Only named dimensions enter the contract as scientist declarations; "
                            "every omitted dimension remains unknown."
                        ),
                    },
                    {
                        "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                        "label": "Retain unresolved",
                        "value": {"action": "retain_unknown"},
                        "consequence": (
                            "The contract remains incomplete and dependent detector targets stay "
                            "ineligible."
                        ),
                    },
                ],
                "evidence_searched": evidence_searched,
                "blocked_detector_ids": blocked_detector_ids,
                "affected_claim_ids": [claim_id],
                "linked_conditional_concern_ids": [],
                "priority": "high",
                "status": "open",
                "answer_ids": [],
                "created_at": created_at,
                "provenance": controller_provenance(
                    "deterministic_contract_question_generation", created_at
                ),
                "extensions": {
                    "x-contract-ref": typed_ref("scientific_contract", contract_id),
                    "x-unresolved-dimensions": unresolved,
                    "x-answer-shape": answer_shape,
                    **(
                        {
                            "x-method-profile-id": EXPECTED_COUNT_PROFILE_ID,
                            "x-reported-method-assertion-ids": reported_method_ids,
                            "x-sensitivity-assertion-ids": [
                                str(assertion["assertion_id"])
                                for assertion in sensitivity_assertions
                            ],
                        }
                        if is_expected_count_profile
                        else {}
                    ),
                    **(
                        {
                            "x-posthoc-ledger-profile": "posthoc_method_ledger_v1",
                            "x-posthoc-comparison-forms": posthoc_forms,
                            "x-posthoc-reported-assertion-ids": posthoc_report_ids,
                        }
                        if posthoc_forms
                        else {}
                    ),
                },
            }
        )
    return questions


def _unsupported_source_paths(file_records: list[dict[str, Any]]) -> list[str]:
    unsupported_suffixes = {
        ".sh",
        ".bash",
        ".zsh",
        ".smk",
        ".snakefile",
        ".nf",
    }
    unsupported_names = {"snakefile", "nextflow.config"}
    return sorted(
        str(item["path"])
        for item in file_records
        if item.get("entry_kind") == "regular_file"
        and (
            PurePosixPath(str(item["path"])).suffix.lower() in unsupported_suffixes
            or PurePosixPath(str(item["path"])).name.lower() in unsupported_names
        )
    )


def _general_disclosures(
    run_id: str,
    created_at: str,
    publication_artifacts: list[dict[str, Any]],
    file_records: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    unsupported_paths: list[str],
    graph_gap_paths: list[str],
) -> list[dict[str, Any]]:
    publication_refs = [
        typed_ref("artifact", str(item["artifact_id"])) for item in publication_artifacts
    ]
    disclosures = [
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "disclosure",
            "disclosure_id": stable_id("disclosure-detector-gap", run_id),
            "audit_run_id": run_id,
            "disclosure_kind": "detector_gap",
            "title": "No production detector was eligible in the general static audit",
            "description": "The repository was inventoried and supported source files were parsed, but a qualified production detector envelope was not available; incomplete claim contracts or lineage may additionally restrict targets.",
            "importance": "material",
            "non_accusatory": True,
            "affected_refs": publication_refs,
            "source_refs": [],
            "coverage_status": "not_covered",
            "interpretive_consequence": "Zero Findings from this run cannot be interpreted as evidence that the scientific workflow is correct.",
            "created_at": created_at,
            "provenance": controller_provenance("deterministic_coverage_disclosure", created_at),
        }
    ]
    path_to_ref = {
        str(item["path"]): typed_ref("file_record", str(item["file_record_id"]))
        for item in file_records
    }
    parser_gap_paths = sorted(set(unsupported_paths) | set(graph_gap_paths))
    if parser_gap_paths:
        disclosures.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "disclosure",
                "disclosure_id": stable_id("disclosure-parser-gap", run_id, *parser_gap_paths),
                "audit_run_id": run_id,
                "disclosure_kind": "parser_gap",
                "title": "Some scientific source paths lack a production parser envelope",
                "description": f"{len(parser_gap_paths)} inventoried source path(s) were not promoted into the common observed-operation graph.",
                "importance": "important",
                "non_accusatory": True,
                "affected_refs": [
                    path_to_ref[path] for path in parser_gap_paths if path in path_to_ref
                ],
                "source_refs": [],
                "coverage_status": "not_covered",
                "interpretive_consequence": "Claims or decisions depending on those paths remain outside detector coverage.",
                "created_at": created_at,
                "provenance": controller_provenance(
                    "deterministic_parser_gap_disclosure", created_at
                ),
                "extensions": {"x-paths": parser_gap_paths},
            }
        )
    opaque_operations = [
        operation for operation in operations if operation.get("inspection_status") == "opaque"
    ]
    if opaque_operations:
        source_refs_by_value = {
            canonical_json(source_ref): source_ref
            for operation in opaque_operations
            for source_ref in operation.get("source_refs", [])
        }
        disclosures.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "disclosure",
                "disclosure_id": stable_id(
                    "disclosure-opaque-operations",
                    run_id,
                    *(str(item["operation_id"]) for item in opaque_operations),
                ),
                "audit_run_id": run_id,
                "disclosure_kind": "opaque_boundary",
                "title": "Some Python operations remain opaque to static inspection",
                "description": f"{len(opaque_operations)} operation(s) were preserved with unresolved callable or runtime semantics.",
                "importance": "important",
                "non_accusatory": True,
                "affected_refs": [
                    typed_ref("operation", str(item["operation_id"])) for item in opaque_operations
                ],
                "source_refs": [source_refs_by_value[key] for key in sorted(source_refs_by_value)],
                "coverage_status": "partially_covered",
                "interpretive_consequence": "The internal scientific behavior of those operations was not established.",
                "created_at": created_at,
                "provenance": controller_provenance(
                    "deterministic_opaque_boundary_disclosure", created_at
                ),
            }
        )
    return disclosures


def _general_coverage_inputs(
    snapshot: SnapshotOutput,
    file_records: list[dict[str, Any]],
    parser_results: list[dict[str, Any]],
    publication_artifacts: list[dict[str, Any]],
    publication_surface: dict[str, Any],
    operations: list[dict[str, Any]],
    data_assets: list[dict[str, Any]],
    selection_envelopes: list[dict[str, Any]],
    unsupported_paths: list[str],
    graph_gap_paths: list[str],
) -> dict[str, Any]:
    deeply_inspected_paths = {
        str(result["source_ref"]["path"])
        for result in parser_results
        if result.get("state") in {"parsed", "partially_parsed"}
        and result.get("parser_id") != NEXTFLOW_TRACE_PARSER_ID
    }
    deeply_inspected_paths.update(
        str(record["path"])
        for record in data_assets
        if record.get("structure_status") == "complete" and isinstance(record.get("path"), str)
    )
    partially_inspected_paths = {
        str(record["path"])
        for record in data_assets
        if record.get("structure_status") != "complete" and isinstance(record.get("path"), str)
    }
    partially_inspected_paths.update(
        str(result["source_ref"]["path"])
        for result in parser_results
        if result.get("parser_id") == NEXTFLOW_TRACE_PARSER_ID
        and result.get("state") in {"parsed", "partially_parsed"}
        and isinstance(result.get("source_ref", {}).get("path"), str)
    )
    deeply_inspected = sorted(deeply_inspected_paths)
    inventory_paths = sorted(str(record["path"]) for record in file_records)
    parser_coverage = [
        {
            "surface": f"{result['parser_id']}:{result['source_ref']['path']}",
            "status": result["coverage_status"],
            "details": f"State {result['state']}; {len(result.get('syntax_issues', []))} syntax issue(s) and {len(result.get('opaque_constructs', []))} opaque construct(s).",
        }
        for result in parser_results
    ]
    if unsupported_paths:
        parser_coverage.append(
            {
                "surface": "unsupported scientific source adapters",
                "status": "not_covered",
                "details": f"{len(unsupported_paths)} source path(s) require adapters not implemented in this slice.",
            }
        )
    if graph_gap_paths:
        parser_coverage.append(
            {
                "surface": "static operation graph promotion",
                "status": "partially_covered",
                "details": f"{len(graph_gap_paths)} parser result(s) could not be promoted without ambiguity.",
            }
        )
    if not parser_coverage:
        parser_coverage.append(
            {
                "surface": "Python and Markdown static parsers",
                "status": "not_covered",
                "details": "No fully materialized supported source file was available.",
            }
        )
    opaque_refs = [
        typed_ref("operation", str(operation["operation_id"]))
        for operation in operations
        if operation.get("inspection_status") == "opaque"
    ]
    return {
        "inventory_summary": {
            "files_total": len(file_records),
            "files_classified": len(file_records),
            "files_deeply_inspected": len(set(deeply_inspected) & set(inventory_paths)),
        },
        "parser_coverage": parser_coverage,
        "deeply_inspected_paths": deeply_inspected,
        "partially_inspected_paths": sorted(partially_inspected_paths),
        "uninspected_paths": sorted(
            set(inventory_paths) - set(deeply_inspected) - partially_inspected_paths
        ),
        "publication_surface_refs": [
            typed_ref("artifact", str(item["artifact_id"])) for item in publication_artifacts
        ],
        "publication_surface_status": (
            "unavailable" if not publication_artifacts else str(publication_surface["status"])
        ),
        "opaque_boundary_refs": opaque_refs,
        "known_gaps": [
            *([] if selection_envelopes else ["No SelectionEnvelope was reconstructed."]),
            "No final claim was bound to a complete ScientificContract.",
            "No qualified production detector target was eligible.",
            *(
                ["No fully identified publication-like artifact was available."]
                if not publication_artifacts
                else []
            ),
            *(
                [
                    f"{len(unsupported_paths)} scientific source path(s) have no active parser adapter."
                ]
                if unsupported_paths
                else []
            ),
            *(
                [f"{len(graph_gap_paths)} static parser graph(s) could not be promoted."]
                if graph_gap_paths
                else []
            ),
        ],
        "workspace_divergence": snapshot.snapshot_record["live_workspace_state"],
    }


def _timestamp_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _notify_stage(
    stage_hook: Callable[[str, RunControl], None] | None,
    journal: _RunJournal,
    run_control: RunControl,
) -> None:
    if stage_hook is not None:
        stage_hook(journal.state.value, run_control)


def _check_run_control(
    run_control: RunControl,
    journal: _RunJournal,
    next_stage: str,
) -> None:
    if run_control.cancellation_requested:
        journal.record_stage(
            next_stage,
            "skipped",
            "The user requested cancellation; completed records were preserved.",
        )
        journal.transition_to(AuditState.CANCELLED)
        raise CancellationRequestedError("Audit cancellation was requested")
    if run_control.host_model_limit_reached:
        journal.record_stage(
            next_stage,
            "skipped",
            "The host model limit was reached; completed records were preserved.",
            ErrorCode.HOST_MODEL_LIMIT,
        )
        journal.transition_to(AuditState.PARTIAL_HOST_LIMIT)
        raise HostModelLimitError("Host model limit was reached")


def _check_prelock_deadline(
    deadline: AuditDeadline,
    journal: _RunJournal,
    next_stage: str,
) -> float:
    try:
        deadline.check()
    except DeadlineExceededError:
        journal.record_stage(
            next_stage,
            "timed_out",
            "The hard deadline was reached before a public partial bundle could be emitted.",
            ErrorCode.DEADLINE_EXHAUSTED,
        )
        journal.transition_to(AuditState.PARTIAL_DEADLINE)
        raise
    return deadline.observed_elapsed


def _general_postlock_checkpoint(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    journal: _RunJournal,
    deadline: AuditDeadline,
    run_control: RunControl,
    *,
    next_stage: str,
) -> dict[str, Any] | None:
    if run_control.cancellation_requested:
        _check_run_control(run_control, journal, next_stage)
    if run_control.host_model_limit_reached:
        return _finish_general_partial_run(
            locked_case,
            output,
            schema_root,
            journal,
            termination_reason="host_model_limit",
            next_stage=next_stage,
        )
    try:
        deadline.check()
    except DeadlineExceededError:
        return _finish_general_partial_run(
            locked_case,
            output,
            schema_root,
            journal,
            termination_reason="hard_deadline",
            next_stage=next_stage,
        )
    return None


def _finish_general_partial_run(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    journal: _RunJournal,
    *,
    termination_reason: str,
    next_stage: str,
) -> dict[str, Any]:
    if termination_reason == "host_model_limit":
        stage_status = "skipped"
        details = f"{next_stage.capitalize()} stopped because the host model limit was reached."
        error_code = ErrorCode.HOST_MODEL_LIMIT
        terminal_state = AuditState.PARTIAL_HOST_LIMIT
        run_state = "partial_host_limit"
    else:
        stage_status = "timed_out"
        details = f"{next_stage.capitalize()} stopped because the hard deadline was reached."
        error_code = ErrorCode.DEADLINE_EXHAUSTED
        terminal_state = AuditState.PARTIAL_DEADLINE
        run_state = "partial_deadline"
    disposition = _GeneralCoverageDisposition(
        overall_status="partial_budget_exhausted",
        run_state=run_state,
        termination_reason=termination_reason,
        pending_work=(f"Complete the interrupted {next_stage} stage.",),
    )
    bundle = _derive_general_from_lock(
        locked_case,
        output,
        schema_root,
        finalize=False,
        coverage_disposition=disposition,
    )
    journal.record_stage(next_stage, stage_status, details, error_code)
    journal.record_stage(
        "partial_report",
        "completed",
        "Checkpointed locked records, explicit pending coverage, SQLite, and HTML persisted.",
    )
    journal.transition_to(terminal_state)
    layout = AuditLayout(output)
    return _finalize_bundle(
        bundle,
        locked_case,
        layout,
        LocalSchemaRegistry(schema_root),
        JsonlRecordStore(layout.derived),
    )


def _finish_partial_run(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    snapshot_record: dict[str, Any],
    parser_results: list[dict[str, Any]],
    journal: _RunJournal,
    *,
    termination_reason: str,
) -> dict[str, Any]:
    if termination_reason == "host_model_limit":
        stage_status = "skipped"
        details = "Detector scheduling stopped because the host model limit was reached."
        error_code = ErrorCode.HOST_MODEL_LIMIT
        terminal_state = AuditState.PARTIAL_HOST_LIMIT
        run_state = "partial_host_limit"
    elif termination_reason == "hard_deadline":
        stage_status = "timed_out"
        details = "Detector scheduling stopped because the hard deadline was reached."
        error_code = ErrorCode.DEADLINE_EXHAUSTED
        terminal_state = AuditState.PARTIAL_DEADLINE
        run_state = "partial_deadline"
    else:
        stage_status = "skipped"
        details = "Optional detector work was not started after the scheduling cutoff."
        error_code = None
        terminal_state = AuditState.PARTIAL_DEADLINE
        run_state = "partial_deadline"
    bundle = _derive_partial_from_lock(
        locked_case,
        output,
        schema_root,
        snapshot_record,
        parser_results,
        termination_reason=termination_reason,
        overall_status="partial_budget_exhausted",
        run_state=run_state,
    )
    journal.record_stage(
        "partial_report",
        "completed",
        "Checkpointed records, explicit pending coverage, SQLite, and HTML persisted.",
    )
    journal.record_stage("detection", stage_status, details, error_code)
    journal.transition_to(terminal_state)
    return _finalize_bundle(
        bundle,
        locked_case,
        AuditLayout(output),
        LocalSchemaRegistry(schema_root),
        JsonlRecordStore(AuditLayout(output).derived),
    )


def replay(lock_path: Path, output: Path, schema_root: Path) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"replay output already exists: {output}")
    locked_case = json.loads(lock_path.read_text(encoding="utf-8"))
    if locked_case.get("lock_kind") == "method_contract_v1":
        from sc_referee.method_contract_run import replay_method_contract

        return replay_method_contract(lock_path, output, schema_root)
    if locked_case.get("lock_kind") == "linked_project_execution_v1":
        from sc_referee.execution_evidence import replay_linked_execution

        return replay_linked_execution(lock_path, output, schema_root)
    coverage_disposition = (
        _general_source_coverage_disposition(lock_path.parent, schema_root)
        if locked_case.get("lock_kind") == "general_static_v1"
        else None
    )
    layout = AuditLayout(output)
    layout.create()
    if locked_case.get("lock_kind") == "general_static_v1":
        return _replay_general_lock(
            locked_case,
            output,
            schema_root,
            coverage_disposition=coverage_disposition,
        )
    if locked_case.get("fixture_mode") is not True:
        raise ValueError(
            "The starter replay command accepts only an explicitly marked synthetic fixture lock"
        )
    if "semantic_lock_digest" not in locked_case:
        locked_case["semantic_lock_digest"] = semantic_digest(locked_case)
    write_normalized_json(layout.lock_path, locked_case)
    observed_store = JsonlRecordStore(layout.observed)
    validator = LocalSchemaRegistry(schema_root)
    for record in [
        *locked_case.get("asset_identities", []),
        *locked_case.get("file_records", []),
    ]:
        validator.validate(record)
        observed_store.append(record)
    observed_graph = locked_case.get("observed_graph", {})
    for record in [
        *observed_graph.get("operations", []),
        *observed_graph.get("artifacts", []),
        *(
            [observed_graph["observed_result"]]
            if isinstance(observed_graph.get("observed_result"), dict)
            else []
        ),
    ]:
        validator.validate(record)
        observed_store.append(record)
    return _derive_from_lock(locked_case, output, schema_root, None, [])


def _replay_general_lock(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    *,
    coverage_disposition: _GeneralCoverageDisposition | None = None,
) -> dict[str, Any]:
    layout = AuditLayout(output)
    if "semantic_lock_digest" not in locked_case:
        locked_case["semantic_lock_digest"] = semantic_digest(locked_case)
    write_normalized_json(layout.lock_path, locked_case)
    validator = LocalSchemaRegistry(schema_root)
    snapshot_record = locked_case["repository_snapshot"]
    validator.validate(snapshot_record)
    write_normalized_json(layout.observed / "snapshot.json", snapshot_record)
    observed_store = JsonlRecordStore(layout.observed)
    for record in [
        *locked_case.get("asset_identities", []),
        *locked_case.get("file_records", []),
        *locked_case.get("parser_results", []),
        *locked_case.get("operations", []),
        *locked_case.get("artifacts", []),
        *locked_case.get("observed_results", []),
        *locked_case.get("deterministic_check_observations", []),
        *locked_case.get("data_assets", []),
        *locked_case.get("variables", []),
        *locked_case.get("analysis_decisions", []),
        *locked_case.get("selection_envelopes", []),
        *locked_case.get("executions", []),
        *locked_case.get("project_execution_authorizations", []),
        *locked_case.get("environments", []),
        *locked_case.get("cache_entries", []),
        *locked_case.get("cache_policies", []),
    ]:
        validator.validate(record)
        observed_store.append(record)
    return _derive_general_from_lock(
        locked_case,
        output,
        schema_root,
        coverage_disposition=coverage_disposition,
    )


def _general_source_coverage_disposition(
    source_root: Path, schema_root: Path
) -> _GeneralCoverageDisposition | None:
    bundle_path = source_root / "audit.bundle.json"
    if not bundle_path.is_file() or bundle_path.is_symlink():
        return None
    status = load_audit_status(source_root, schema_root)
    if status.run_state == "complete":
        return None
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    coverage = bundle["coverage_records"][0]
    extensions = coverage["extensions"]
    pending_work = tuple(
        str(item)
        for item in extensions.get("x-pending-work", [])
        if str(item).startswith("Complete the interrupted ")
    )
    return _GeneralCoverageDisposition(
        overall_status=str(coverage["overall_status"]),
        run_state=status.run_state,
        termination_reason=str(extensions["x-termination-reason"]),
        pending_work=pending_work,
    )


def _derive_general_from_lock(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    *,
    finalize: bool = True,
    coverage_disposition: _GeneralCoverageDisposition | None = None,
    detector_results: list[dict[str, Any]] | None = None,
    detector_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if (detector_results is None) != (detector_findings is None):
        raise ValueError("detector results and findings must be supplied together")
    layout = AuditLayout(output)
    validator = LocalSchemaRegistry(schema_root)
    bundle = _empty_bundle(locked_case)
    bundle["repository_snapshots"] = [locked_case["repository_snapshot"]]
    for bundle_field in (
        "scientific_contracts",
        "semantic_assertions",
        "claims",
        "detector_manifests",
        "asset_identities",
        "file_records",
        "parser_results",
        "operations",
        "artifacts",
        "observed_results",
        "deterministic_check_observations",
        "data_assets",
        "variables",
        "analysis_decisions",
        "selection_envelopes",
        "executions",
        "project_execution_authorizations",
        "environments",
        "publication_surfaces",
        "material_questions",
        "work_items",
        "answers",
        "disclosures",
        "cache_entries",
        "cache_policies",
        "reproduction_requests",
        "performance_records",
    ):
        bundle[bundle_field] = deepcopy(locked_case.get(bundle_field, []))
    bundle["disclosures"].extend(_derive_posthoc_ledger_disclosures(locked_case))
    if detector_results is None:
        if coverage_disposition is not None and coverage_disposition.run_state != "complete":
            detector_results = []
            detector_findings = []
        else:
            evaluation = _evaluate_general_detectors(locked_case)
            detector_results = list(evaluation.results)
            detector_findings = list(evaluation.findings)
    assert detector_findings is not None
    bundle["detector_results"] = deepcopy(detector_results)
    bundle["findings"] = deepcopy(detector_findings)
    coverage = _general_coverage_record(
        locked_case,
        bundle,
        coverage_disposition=coverage_disposition,
    )
    bundle["coverage_records"] = [coverage]

    for record in [
        locked_case["repository_snapshot"],
        *bundle["asset_identities"],
        *bundle["scientific_contracts"],
        *bundle["semantic_assertions"],
        *bundle["claims"],
        *bundle["detector_manifests"],
        *bundle["detector_results"],
        *bundle["findings"],
        *bundle["file_records"],
        *bundle["parser_results"],
        *bundle["operations"],
        *bundle["artifacts"],
        *bundle["observed_results"],
        *bundle["deterministic_check_observations"],
        *bundle["data_assets"],
        *bundle["variables"],
        *bundle["analysis_decisions"],
        *bundle["selection_envelopes"],
        *bundle["executions"],
        *bundle["project_execution_authorizations"],
        *bundle["environments"],
        *bundle["publication_surfaces"],
        *bundle["material_questions"],
        *bundle["work_items"],
        *bundle["answers"],
        *bundle["disclosures"],
        *bundle["cache_entries"],
        *bundle["cache_policies"],
        *bundle["reproduction_requests"],
        *bundle["performance_records"],
        coverage,
    ]:
        validator.validate(record)

    derived_store = JsonlRecordStore(layout.derived)
    for bundle_field in (
        "semantic_assertions",
        "detector_manifests",
        "detector_results",
        "findings",
        "publication_surfaces",
        "material_questions",
        "work_items",
        "answers",
        "disclosures",
        "reproduction_requests",
        "performance_records",
    ):
        for record in bundle[bundle_field]:
            derived_store.append(record)
    derived_store.append(coverage)
    if finalize:
        return _finalize_bundle(bundle, locked_case, layout, validator, derived_store)
    return _write_preliminary_outputs(bundle, layout, validator)


@dataclass(frozen=True)
class _GeneralDetectorEvaluation:
    results: tuple[dict[str, Any], ...]
    findings: tuple[dict[str, Any], ...]


def _evaluate_general_detectors(locked_case: dict[str, Any]) -> _GeneralDetectorEvaluation:
    method_evaluations = evaluate_registered_method_conflicts(locked_case)
    results: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    registry_lock = locked_case.get("scientific_check_registry")
    production_promotion_permitted = bool(
        isinstance(registry_lock, dict)
        and (
            (
                registry_lock.get("binding_lane") == "qualified"
                and registry_lock.get("production_promotion_permitted") is True
            )
            or (
                "binding_lane" not in registry_lock
                and "production_promotion_permitted" not in registry_lock
            )
        )
    )
    for evaluation in method_evaluations:
        result, finding = (
            _promote_method_conflict_evaluation(locked_case, evaluation)
            if production_promotion_permitted
            else (deepcopy(evaluation.result), None)
        )
        results.append(result)
        if finding is not None:
            findings.append(finding)
    direction_manifests = [
        item
        for item in locked_case.get("detector_manifests", [])
        if item.get("detector_id") == BoundedReportMeanDirectionDetector.detector_id
    ]
    if len(direction_manifests) > 1:
        raise ValueError("general semantic lock has duplicate bounded direction manifests")
    if direction_manifests:
        direction_detector = BoundedReportMeanDirectionDetector(direction_manifests[0])
        targets = sorted(
            (
                claim
                for claim in locked_case.get("claims", [])
                if claim.get("claim_status") == "final" and claim.get("claim_kind") == "directional"
            ),
            key=lambda claim: str(claim.get("claim_id")),
        )
        results.extend(direction_detector.evaluate(locked_case, claim) for claim in targets)
    method_manifests = [
        item
        for item in locked_case.get("detector_manifests", [])
        if item.get("detector_id") == BoundedReportedMethodContractConflictDetector.detector_id
    ]
    if len(method_manifests) > 1:
        raise ValueError("general semantic lock has duplicate bounded method manifests")
    if method_manifests:
        method_detector = BoundedReportedMethodContractConflictDetector(method_manifests[0])
        targets = sorted(
            (
                claim
                for claim in locked_case.get("claims", [])
                if claim.get("claim_status") == "final"
                and claim.get("claim_kind") == "quantitative"
                and claim.get("extensions", {}).get("x-method-profile-id")
                == EXPECTED_COUNT_PROFILE_ID
            ),
            key=lambda claim: str(claim.get("claim_id")),
        )
        results.extend(method_detector.evaluate(locked_case, claim) for claim in targets)
    feature_manifests = [
        item
        for item in locked_case.get("detector_manifests", [])
        if item.get("detector_id") == BoundedFeatureIdentifierIdentityDetector.detector_id
    ]
    if len(feature_manifests) > 1:
        raise ValueError("general semantic lock has duplicate feature-identity manifests")
    if feature_manifests:
        feature_detector = BoundedFeatureIdentifierIdentityDetector(feature_manifests[0])
        targets = sorted(
            (
                observation
                for observation in locked_case.get("deterministic_check_observations", [])
                if observation.get("check_manifest", {}).get("check_id")
                == FEATURE_IDENTIFIER_IDENTITY_CHECK_ID
                and observation.get("comparison", {}).get("outcome") == "nonconformant"
            ),
            key=lambda observation: str(observation.get("deterministic_check_observation_id")),
        )
        results.extend(feature_detector.evaluate(locked_case, target) for target in targets)
    return _GeneralDetectorEvaluation(tuple(results), tuple(findings))


def _promote_method_conflict_evaluation(
    locked_case: dict[str, Any],
    evaluation: MethodConflictEvaluation,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Replace one candidate only after an installed pin resolves and admission succeeds."""

    original = deepcopy(evaluation.result)
    if original.get("state") != "evaluation_finding_candidate":
        return original, None
    pin = method_conflict_grant_pins.GRANT_PINS.get(evaluation.binding.binding_id)
    if pin is None:
        return original, None
    expected_wording: tuple[str, str, tuple[str, ...], bool] | None = None
    if evaluation.binding.check_id == (
        "check:authorized-independent-unit-entry-into-row-independent-procedure"
    ):
        expected_wording = code_dependence_wording_profile(evaluation.binding)
        if (
            expected_wording is None
            or pin.finding_profile_id != expected_wording[0]
            or pin.finding_profile_digest != expected_wording[1]
        ):
            return original, None
    evidence = method_conflict_grant_pins.load_method_conflict_grant_evidence(pin)
    if evidence is None:
        return original, None
    qualification, metric_set = evidence
    manifests = [
        item
        for item in locked_case.get("detector_manifests", [])
        if item.get("detector_id") == evaluation.binding.detector_id
        and item.get("detector_version") == evaluation.binding.detector_version
        and semantic_digest(item) == evaluation.binding.detector_manifest_digest
    ]
    if len(manifests) != 1:
        return original, None
    grant = resolve_method_conflict_qualification(
        binding=evaluation.binding,
        detector_manifest=manifests[0],
        qualification=qualification,
        metric_set=metric_set,
        pin=pin,
    )
    if grant is None:
        return original, None
    promoted = project_qualified_method_conflict_candidate(
        original,
        evaluation.binding,
        grant,
        work_packet=evaluation.work_packet,
    )
    if promoted is None:
        return original, None
    try:
        draft = draft_method_conflict_finding(
            promoted,
            evaluation.binding,
            work_packet=evaluation.work_packet,
        )
    except (KeyError, TypeError, ValueError):
        return original, None
    if expected_wording is not None:
        if (
            pin.finding_profile_digest != expected_wording[1]
            or draft.get("extensions", {}).get("x-finding-wording-profile-id")
            != expected_wording[0]
            or draft.get("extensions", {}).get("x-finding-wording-profile-digest")
            != expected_wording[1]
            or not isinstance(promoted.get("candidate"), dict)
            or not isinstance(draft.get("title"), str)
            or not isinstance(draft.get("summary"), str)
        ):
            return original, None
        promoted["candidate"]["title"] = draft["title"]
        promoted["candidate"]["bounded_statement"] = draft["summary"]
    finding = admit_finding(
        promoted,
        AdmissionContext(
            finding_draft=draft,
            source_references_resolved=_method_conflict_evidence_resolves(promoted),
            detector_qualification_applies=True,
            wording_constraints_satisfied=True,
            expected_deterministic_input_digest=semantic_digest(evaluation.work_packet),
            required_counterevidence_check_ids=(BoundedAnalysisMethodConflictDetector.check_ids),
            non_inferences=(
                "Static evidence does not establish that project code executed.",
                "The Finding does not establish numerical causality, bias direction, universal "
                "scientific correctness, or effects outside the selected analysis.",
            ),
        ),
    )
    if finding is None:
        return original, None
    return promoted, finding


def _method_conflict_evidence_resolves(result: dict[str, Any]) -> bool:
    evidence = result.get("evidence")
    return (
        isinstance(evidence, list)
        and bool(evidence)
        and any(isinstance(item, dict) and bool(item.get("source_refs")) for item in evidence)
        and all(
            isinstance(item, dict) and bool(item.get("source_refs") or item.get("record_refs"))
            for item in evidence
        )
    )


def _derive_posthoc_ledger_disclosures(locked_case: dict[str, Any]) -> list[dict[str, Any]]:
    assertions = [
        item for item in locked_case.get("semantic_assertions", []) if isinstance(item, dict)
    ]
    contracts = {
        str(item.get("contract_id")): item
        for item in locked_case.get("scientific_contracts", [])
        if isinstance(item, dict)
    }
    disclosures: list[dict[str, Any]] = []
    for claim in locked_case.get("claims", []):
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        contract = contracts.get(str(claim.get("scientific_contract_id", "")))
        if not claim_id or contract is None:
            continue
        bindings: set[tuple[str, str]] = set()
        for assertion in assertions:
            predicate = str(assertion.get("predicate", ""))
            comparison_form = assertion.get("extensions", {}).get("x-posthoc-comparison-form")
            if (
                assertion.get("subject_ref") != typed_ref("claim", claim_id)
                or not predicate.startswith("reported_")
                or not isinstance(comparison_form, str)
            ):
                continue
            dimension = predicate.removeprefix("reported_")
            if posthoc_form_allowed(dimension, comparison_form):
                bindings.add((dimension, comparison_form))
        for dimension, comparison_form in sorted(bindings):
            try:
                ledger = project_posthoc_method_ledger(
                    claim=claim,
                    contract=contract,
                    assertions=assertions,
                    dimension=dimension,
                    comparison_form=comparison_form,
                )
            except PosthocMethodLedgerError as error:
                ledger = {
                    "projection_profile": "posthoc_method_ledger_v1",
                    "claim_id": claim_id,
                    "contract_id": str(contract.get("contract_id")),
                    "dimension": dimension,
                    "comparison_form": comparison_form,
                    "outcome": "unsupported_path",
                    "basis": f"The closed post-hoc ledger rejected this input: {error}",
                    "source_refs": [],
                    "assertion_refs": [],
                    "production_finding_permitted": False,
                }
                ledger["ledger_digest"] = semantic_digest(ledger)
            disclosures.append(
                _posthoc_ledger_disclosure(
                    str(locked_case["audit_run_id"]),
                    str(locked_case["locked_at"]),
                    claim_id,
                    ledger,
                )
            )
    questions_by_contract = {
        str(item.get("extensions", {}).get("x-contract-ref", {}).get("record_id")): item
        for item in locked_case.get("material_questions", [])
        if isinstance(item, dict)
        and item.get("unknown_semantic_dimension") == "scientific_contract"
    }
    for contract_id, contract in sorted(contracts.items()):
        scope = contract.get("scope", {})
        subject_refs = scope.get("subject_refs", []) if isinstance(scope, dict) else []
        if (
            not isinstance(scope, dict)
            or scope.get("level") != "analysis"
            or len(subject_refs) != 1
            or subject_refs[0].get("record_type") != "publication_surface"
        ):
            continue
        question = questions_by_contract.get(contract_id)
        if question is None:
            continue
        extensions = question.get("extensions", {})
        forms = extensions.get("x-posthoc-comparison-forms", {})
        observed_by_dimension = extensions.get("x-posthoc-reported-assertion-ids", {})
        scope_path = extensions.get("x-scientific-check-scope-join-path")
        scope_digest = extensions.get("x-scientific-check-scope-join-digest")
        if (
            not isinstance(forms, dict)
            or not isinstance(observed_by_dimension, dict)
            or not isinstance(scope_path, list)
            or not isinstance(scope_digest, str)
        ):
            continue
        for dimension, comparison_form in sorted(forms.items()):
            observed_ids = observed_by_dimension.get(dimension)
            if (
                not isinstance(comparison_form, str)
                or not isinstance(observed_ids, list)
                or not all(isinstance(value, str) for value in observed_ids)
            ):
                continue
            try:
                ledger = project_analysis_posthoc_method_ledger(
                    analysis_subject_ref=subject_refs[0],
                    contract=contract,
                    assertions=assertions,
                    observed_assertion_ids=observed_ids,
                    dimension=str(dimension),
                    comparison_form=comparison_form,
                    scope_join_path=scope_path,
                    scope_join_digest=scope_digest,
                )
            except PosthocMethodLedgerError as error:
                ledger = {
                    "projection_profile": "posthoc_method_ledger_v1",
                    "analysis_subject_ref": deepcopy(subject_refs[0]),
                    "contract_id": contract_id,
                    "dimension": str(dimension),
                    "comparison_form": comparison_form,
                    "outcome": "unsupported_path",
                    "basis": f"The closed analysis-scoped ledger rejected this input: {error}",
                    "source_refs": [],
                    "assertion_refs": [],
                    "production_finding_permitted": False,
                }
                ledger["ledger_digest"] = semantic_digest(ledger)
            disclosures.append(
                _analysis_posthoc_ledger_disclosure(
                    str(locked_case["audit_run_id"]),
                    str(locked_case["locked_at"]),
                    subject_refs[0],
                    ledger,
                )
            )
    return disclosures


def _analysis_posthoc_ledger_disclosure(
    run_id: str,
    created_at: str,
    subject_ref: dict[str, str],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(ledger["outcome"])
    dimension = str(ledger["dimension"])
    form = str(ledger["comparison_form"])
    observed_authority = str(ledger.get("authority", {}).get("observed", ""))
    static = "static_source" in observed_authority
    if outcome == "covered_negative":
        title = "One exact analysis-scoped method relation is compatible"
        description = (
            f"The exact {dimension} operand under {form} is compatible with the "
            "scientist-specified requirement governing this review."
        )
        importance = "informational"
        coverage_status = "covered"
        consequence = (
            "This covered relation is not a correctness certificate and says nothing about "
            "unchecked method dimensions."
        )
    elif outcome == "exact_conflict_candidate":
        title = "One exact review-scoped method incompatibility"
        evidence_label = (
            "statically inspected source shape" if static else "selected report wording"
        )
        description = (
            f"The exact {evidence_label} for {dimension} under {form} is incompatible with the "
            "scientist-specified requirement governing this review. This is an experimental "
            "compatibility Disclosure, not a Finding."
        )
        importance = "material"
        coverage_status = "covered"
        consequence = (
            "The incompatibility does not establish execution, historical intent, numerical "
            "causality, or universal scientific correctness."
        )
    elif outcome == "not_applicable":
        title = "One analysis-scoped method relation is not applicable"
        description = f"The {dimension} relation under {form} is explicitly not applicable."
        importance = "informational"
        coverage_status = "not_applicable"
        consequence = "No compatibility conclusion is drawn for this relation."
    elif outcome == "unresolved_obligation":
        title = "One analysis-scoped method obligation remains unresolved"
        description = f"The {dimension} relation under {form} lacks one governing requirement."
        importance = "important"
        coverage_status = "unknown"
        consequence = "The unresolved premise cannot support an incompatibility or Finding."
    else:
        title = "One analysis-scoped method path remains unsupported"
        description = f"The {dimension} relation under {form} could not be verified exactly."
        importance = "important"
        coverage_status = "not_covered"
        consequence = "The unsupported path cannot support an incompatibility or Finding."
    source_refs = [deepcopy(ref) for ref in ledger.get("source_refs", []) if isinstance(ref, dict)]
    affected_refs = [deepcopy(subject_ref)]
    affected_refs.extend(
        deepcopy(ref) for ref in ledger.get("assertion_refs", []) if isinstance(ref, dict)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id(
            "disclosure-analysis-posthoc-method-ledger", run_id, str(ledger["ledger_digest"])
        ),
        "audit_run_id": run_id,
        "disclosure_kind": "other",
        "title": title,
        "description": description,
        "importance": importance,
        "non_accusatory": True,
        "affected_refs": affected_refs,
        "source_refs": source_refs,
        "coverage_status": coverage_status,
        "interpretive_consequence": consequence,
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_analysis_posthoc_method_ledger_projection_v1", created_at
        ),
        "extensions": {"x-posthoc-method-ledger": deepcopy(ledger)},
    }


def _posthoc_ledger_disclosure(
    run_id: str,
    created_at: str,
    claim_id: str,
    ledger: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(ledger["outcome"])
    dimension = str(ledger["dimension"])
    form = str(ledger["comparison_form"])
    if outcome == "covered_negative":
        title = "One exact post-hoc method relation is compatible"
        description = (
            f"For Claim {claim_id}, the exact {dimension} relation under {form} is compatible "
            "with the scientist-specified requirement governing this review."
        )
        importance = "informational"
        coverage_status = "covered"
        consequence = (
            "This covered relation is not a correctness certificate and says nothing about "
            "unchecked method dimensions."
        )
    elif outcome == "exact_conflict_candidate":
        title = "One exact post-hoc method relation conflicts"
        description = (
            f"For Claim {claim_id}, the exact reported {dimension} relation under {form} "
            "conflicts with the scientist-specified requirement governing this review. This is "
            "an experimental compatibility disclosure, not a Finding."
        )
        importance = "material"
        coverage_status = "covered"
        consequence = (
            "The conflict does not prove historical intent, execution, numerical error, or that "
            "the scientist-specified method is universally correct."
        )
    elif outcome == "not_applicable":
        title = "One post-hoc method relation is not applicable"
        description = f"The {dimension} relation under {form} is explicitly not applicable."
        importance = "informational"
        coverage_status = "not_applicable"
        consequence = "No compatibility conclusion is drawn for this relation."
    elif outcome == "unresolved_obligation":
        title = "One post-hoc method obligation remains unresolved"
        description = f"The {dimension} relation under {form} lacks one unambiguous requirement."
        importance = "important"
        coverage_status = "unknown"
        consequence = "The unresolved premise cannot support a compatibility conflict or Finding."
    else:
        title = "One post-hoc method path remains unsupported"
        description = f"The {dimension} relation under {form} could not be verified exactly."
        importance = "important"
        coverage_status = "not_covered"
        consequence = "The unsupported path cannot support a compatibility conflict or Finding."
    source_refs = [deepcopy(ref) for ref in ledger.get("source_refs", []) if isinstance(ref, dict)]
    affected_refs = [typed_ref("claim", claim_id)]
    affected_refs.extend(
        deepcopy(ref) for ref in ledger.get("assertion_refs", []) if isinstance(ref, dict)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": stable_id(
            "disclosure-posthoc-method-ledger", run_id, str(ledger["ledger_digest"])
        ),
        "audit_run_id": run_id,
        "disclosure_kind": "other",
        "title": title,
        "description": description,
        "importance": importance,
        "non_accusatory": True,
        "affected_refs": affected_refs,
        "source_refs": source_refs,
        "coverage_status": coverage_status,
        "interpretive_consequence": consequence,
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_posthoc_method_ledger_projection_v1", created_at
        ),
        "extensions": {"x-posthoc-method-ledger": deepcopy(ledger)},
    }


def _general_coverage_record(
    locked_case: dict[str, Any],
    bundle: dict[str, Any],
    *,
    coverage_disposition: _GeneralCoverageDisposition | None = None,
) -> dict[str, Any]:
    disposition = coverage_disposition or _GeneralCoverageDisposition()
    inputs = locked_case["coverage_inputs"]
    method_conflict_bindings = locked_method_conflict_bindings(locked_case)
    registered_method_detector_ids = sorted(
        {binding.detector_id for binding in method_conflict_bindings}
    )
    method_check_ids_by_detector: dict[str, set[str]] = {}
    for binding in method_conflict_bindings:
        method_check_ids_by_detector.setdefault(binding.detector_id, set()).add(binding.check_id)
    detector_ids = [
        *registered_method_detector_ids,
        BoundedReportMeanDirectionDetector.detector_id,
        BoundedReportedMethodContractConflictDetector.detector_id,
        BoundedFeatureIdentifierIdentityDetector.detector_id,
        "detector:population-comparison-estimand",
        "detector:denominator-control-set",
        "detector:explicit-dependence",
        "detector:lineage-completeness",
    ]
    evaluated_by_detector: dict[str, list[dict[str, Any]]] = {}
    for result in bundle["detector_results"]:
        evaluated_by_detector.setdefault(str(result["detector_id"]), []).append(result)
    known_gaps = list(inputs["known_gaps"])
    weak_identity_count = sum(
        1 for item in bundle["asset_identities"] if item.get("tier") == "weak_fingerprint"
    )
    manifest_identity_count = sum(
        1 for item in bundle["asset_identities"] if item.get("tier") == "manifest"
    )
    unidentified_count = sum(
        1 for item in bundle["asset_identities"] if item.get("tier") == "unidentified"
    )
    if weak_identity_count:
        known_gaps.append(
            f"{weak_identity_count} asset(s) have only weak fingerprints; exact identity is "
            "unavailable and only dependent conclusions are limited."
        )
    if manifest_identity_count:
        known_gaps.append(
            f"{manifest_identity_count} asset(s) use repository-supplied manifest digests; "
            "the target bytes were not independently hashed and only dependent exact-byte "
            "verification is limited."
        )
    if unidentified_count:
        known_gaps.append(
            f"{unidentified_count} asset(s) are unidentified; dependent conclusions remain unavailable."
        )
    _append_checksum_manifest_inspection_gaps(known_gaps, bundle)
    _append_tabular_inventory_gaps(known_gaps, bundle)
    _append_h5ad_inventory_gaps(known_gaps, bundle)
    _append_nextflow_trace_gaps(known_gaps, bundle)
    workspace_state = inputs.get("workspace_divergence", {})
    if workspace_state.get("status") == "workspace_diverged":
        known_gaps.append(
            "The live workspace diverged after capture; this audit remained bound to the immutable snapshot."
        )
    pending_work: list[str] = []
    unresolved_surfaces = [
        item for item in bundle["publication_surfaces"] if item.get("status") == "unresolved"
    ]
    if any(item.get("candidates") for item in unresolved_surfaces):
        pending_work.append("Resolve the ambiguous publication surface.")
    elif unresolved_surfaces:
        pending_work.append(
            "Identify an in-repository final publication surface if one exists; otherwise retain the explicit unavailable state."
        )
    if bundle["claims"]:
        incomplete_contracts = [
            item for item in bundle["scientific_contracts"] if item.get("status") != "resolved"
        ]
        if incomplete_contracts:
            pending_work.append(
                "Complete ScientificContracts before scheduling contract-dependent detectors; "
                "the bounded mechanical direction detector does not resolve scientific meaning."
            )
        else:
            pending_work.append(
                "Reconstruct observed computational lineage before detector scheduling; resolved scientist intent alone is insufficient."
            )
    elif any(
        item.get("status") == "open"
        and isinstance(item.get("extensions", {}).get("x-scientific-check-id"), str)
        for item in bundle["material_questions"]
    ):
        pending_work.append(
            "Ask the scientist to select one listed review-scoped method requirement or retain "
            "it as unknown; this enables only the bounded compatibility comparison."
        )
    elif any(item.get("status") == "resolved" for item in bundle["publication_surfaces"]):
        pending_work.append(
            "If claim-level review is required, provide a supported provenance-bearing Claim "
            "representation for the selected publication surface."
        )
    else:
        pending_work.append(
            "Extract provenance-bearing final claims after the publication surface is resolved."
        )
    pending_work.extend(
        [
            "Run only detectors whose qualified envelopes apply to the locked records.",
            *disposition.pending_work,
        ]
    )
    if any(
        result.get("state") == "evaluation_finding_candidate"
        for result in bundle["detector_results"]
    ):
        pending_work.append(
            "Evaluate experimental candidates through the answer-blind qualification "
            "protocol; they are not production Findings."
        )
        known_gaps.append(
            "An experimental detector emitted evaluation-only candidate output; no detector is "
            "qualified and no production Finding was admitted."
        )
    if disposition.run_state != "complete":
        known_gaps.append(
            f"The run stopped in state {disposition.run_state} before all deterministic terminal stages completed."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "coverage_record",
        "coverage_id": f"coverage:{locked_case['audit_run_id']}",
        "audit_run_id": locked_case["audit_run_id"],
        "generated_at": locked_case["locked_at"],
        "overall_status": disposition.overall_status,
        "scope": {
            "inventory_scope": "whole_repository",
            "deep_inspection_scope": (
                "Static Python and Markdown inspection plus bounded CSV/TSV header inventory "
                "with partial selection evidence; final claim lineage remains unresolved."
                if bundle["selection_envelopes"]
                else "Static Python and Markdown inspection plus bounded CSV/TSV header "
                "inventory; final claim lineage and selection envelope remain unresolved."
            ),
            "publication_surface_refs": deepcopy(inputs["publication_surface_refs"]),
            "publication_surface_status": inputs["publication_surface_status"],
            "selection_envelope_included": bool(bundle["selection_envelopes"]),
        },
        "inventory_summary": deepcopy(inputs["inventory_summary"]),
        "assessment_counts": {
            "findings": len(bundle["findings"]),
            "conditional_concerns": len(bundle["conditional_concerns"]),
            "material_questions": len(bundle["material_questions"]),
            "disclosures": len(bundle["disclosures"]),
        },
        "claim_coverage": {
            "claims_total": len(bundle["claims"]),
            "claims_inspected": len(bundle["claims"]),
            "claims_with_complete_lineage": sum(
                item.get("lineage", {}).get("status") == "complete" for item in bundle["claims"]
            ),
            "lineage_grade_counts": _lineage_grade_counts(bundle["claims"]),
        },
        "parser_coverage": deepcopy(inputs["parser_coverage"]),
        "detector_coverage": [
            _general_detector_coverage_item(
                detector_id,
                _general_detector_target_total(
                    detector_id,
                    bundle,
                    method_check_ids_by_detector,
                ),
                evaluated_by_detector.get(detector_id, []),
                disposition.run_state,
            )
            for detector_id in detector_ids
        ],
        "unknown_semantic_ids": [
            str(item["question_id"])
            for item in bundle["material_questions"]
            if item.get("status") in {"open", "deferred"}
        ],
        "opaque_boundary_refs": deepcopy(inputs["opaque_boundary_refs"]),
        "uninspected_paths": deepcopy(inputs["uninspected_paths"]),
        "known_gaps": known_gaps,
        "interpretation_policy": {
            "correctness_conclusion_allowed": False,
            "global_risk_rating_allowed": False,
            "absence_of_finding_statement": "No finding means only that no issue was admitted within the declared evidence and validated detector coverage.",
        },
        "provenance": controller_provenance(
            "deterministic_general_coverage_calculation", locked_case["locked_at"]
        ),
        "extensions": {
            "x-run-state": disposition.run_state,
            "x-termination-reason": disposition.termination_reason,
            "x-pending-work": pending_work,
            "x-deeply-inspected-paths": deepcopy(inputs["deeply_inspected_paths"]),
            "x-partially-inspected-paths": deepcopy(inputs["partially_inspected_paths"]),
            "x-uninspected-path-policy": "Inventoried paths outside supported static parser envelopes remain explicit and are not negative detector results.",
        },
    }


def _general_detector_target_total(
    detector_id: str,
    bundle: dict[str, Any],
    method_check_ids_by_detector: dict[str, set[str]],
) -> int:
    if detector_id == BoundedFeatureIdentifierIdentityDetector.detector_id:
        return sum(
            1
            for observation in bundle["deterministic_check_observations"]
            if observation.get("check_manifest", {}).get("check_id")
            == FEATURE_IDENTIFIER_IDENTITY_CHECK_ID
            and observation.get("comparison", {}).get("outcome") == "nonconformant"
        )
    method_check_ids = method_check_ids_by_detector.get(detector_id)
    if method_check_ids is None:
        return len(bundle["claims"])
    return sum(
        1
        for question in bundle["material_questions"]
        if question.get("extensions", {}).get("x-scientific-check-id") in method_check_ids
    )


def _general_detector_coverage_item(
    detector_id: str,
    targets_total: int,
    results: list[dict[str, Any]],
    run_state: str,
) -> dict[str, Any]:
    if results:
        coverage_states = {str(result["coverage"]["status"]) for result in results}
        status = (
            "covered"
            if coverage_states == {"covered"}
            else "partially_covered"
            if "covered" in coverage_states or "partially_covered" in coverage_states
            else "not_covered"
        )
        candidate_count = sum(
            result.get("state") == "evaluation_finding_candidate" for result in results
        )
        admitted_count = sum(
            result.get("state") == "finding_candidate"
            and result.get("extensions", {}).get("x-production-finding-permitted") is True
            for result in results
        )
        return {
            "detector_id": detector_id,
            "status": status,
            "targets_total": targets_total,
            "targets_evaluated": len(results),
            "details": (
                f"The bounded mechanical profile evaluated {len(results)} target(s); "
                f"{candidate_count} evaluation candidate(s) retain no production Finding "
                f"authority and {admitted_count} qualified result(s) were admitted."
                if admitted_count
                else f"The experimental bounded mechanical profile evaluated {len(results)} target(s); "
                f"{candidate_count} evaluation candidate(s) have no production Finding authority."
            ),
        }
    return {
        "detector_id": detector_id,
        "status": "not_covered",
        "targets_total": targets_total,
        "targets_evaluated": 0,
        "details": (
            "No target was evaluated before the run stopped."
            if run_state != "complete"
            else "No target entered an applicable qualified or declared experimental detector envelope."
        ),
    }


def _derive_from_lock(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    snapshot_record: dict[str, Any] | None,
    parser_results: list[dict[str, Any]],
    *,
    finalize: bool = True,
) -> dict[str, Any]:
    layout = AuditLayout(output)
    validator = LocalSchemaRegistry(schema_root)
    detector = ClaimResultDirectionDetector()
    detection = detector.evaluate(locked_case)
    finding = None
    if detection.finding_draft is not None:
        finding = admit_finding(
            detection.detector_result,
            AdmissionContext(
                finding_draft=detection.finding_draft,
                source_references_resolved=locked_case.get("source_references_verified") is True,
                detector_qualification_applies=(
                    fixture_envelope_applies(
                        locked_case,
                        detector_id=detector.detector_id,
                        detector_version=detector.detector_version,
                        fixture_id=detector.fixture_id,
                    )
                ),
                wording_constraints_satisfied=True,
                expected_deterministic_input_digest=semantic_digest(locked_case),
                required_counterevidence_check_ids=locked_counterevidence_check_ids(locked_case),
                non_inferences=detector.non_inferences,
            ),
        )
    dependence_detector = SampleUnitDependenceQuestionDetector()
    dependence_result, conditional_concern = dependence_detector.evaluate(locked_case)

    standing_questions = _standing_questions(locked_case, detection.material_question)
    disclosure = locked_case["disclosure"]

    bundle = _empty_bundle(locked_case)
    bundle["scientific_contracts"] = [locked_case["scientific_contract"]]
    bundle["claims"] = [locked_case["claim"]]
    bundle["detector_results"] = [detection.detector_result, dependence_result]
    bundle["findings"] = [finding] if finding else []
    bundle["material_questions"] = standing_questions
    bundle["conditional_concerns"] = [conditional_concern] if conditional_concern else []
    bundle["disclosures"] = [disclosure]
    bundle["repository_snapshots"] = [snapshot_record] if snapshot_record else []
    if snapshot_record is None:
        snapshot_digest = locked_case.get("snapshot_digest")
        workspace_state = locked_case.get("workspace_divergence")
        if isinstance(snapshot_digest, str) and isinstance(workspace_state, dict):
            workspace_status = workspace_state.get("status")
            if isinstance(workspace_status, str):
                bundle["extensions"] = {
                    "x-report-snapshot-projection": {
                        "snapshot_digest": snapshot_digest,
                        "live_workspace_status": workspace_status,
                    }
                }
    bundle["parser_results"] = parser_results
    bundle["asset_identities"] = list(locked_case.get("asset_identities", []))
    bundle["file_records"] = list(locked_case.get("file_records", []))
    bundle["operations"] = list(locked_case.get("observed_graph", {}).get("operations", []))
    bundle["artifacts"] = list(locked_case.get("observed_graph", {}).get("artifacts", []))
    observed_result = locked_case.get("observed_graph", {}).get("observed_result")
    bundle["observed_results"] = [observed_result] if isinstance(observed_result, dict) else []
    coverage = _coverage_record(
        locked_case,
        bundle,
        detector_results=[detection.detector_result, dependence_result],
        overall_status="complete_within_plan",
        termination_reason="completed",
        pending_work=[],
        run_state="complete",
    )
    bundle["coverage_records"] = [coverage]

    public_records = [
        locked_case["claim"],
        locked_case["scientific_contract"],
        detection.detector_result,
        dependence_result,
        *standing_questions,
        disclosure,
        coverage,
        *bundle["asset_identities"],
        *parser_results,
    ]
    if finding:
        public_records.append(finding)
    if conditional_concern:
        public_records.append(conditional_concern)
    if snapshot_record is not None:
        public_records.append(snapshot_record)
    for record in public_records:
        validator.validate(record)

    derived_store = JsonlRecordStore(layout.derived)
    derived_store.append(detection.detector_result)
    derived_store.append(dependence_result)
    if finding:
        derived_store.append(finding)
    for question in standing_questions:
        derived_store.append(question)
    if conditional_concern:
        derived_store.append(conditional_concern)
    derived_store.append(disclosure)
    derived_store.append(coverage)
    if finalize:
        return _finalize_bundle(bundle, locked_case, layout, validator, derived_store)
    return _write_preliminary_outputs(bundle, layout, validator)


def _derive_partial_from_lock(
    locked_case: dict[str, Any],
    output: Path,
    schema_root: Path,
    snapshot_record: dict[str, Any],
    parser_results: list[dict[str, Any]],
    *,
    termination_reason: str,
    overall_status: str,
    run_state: str,
) -> dict[str, Any]:
    layout = AuditLayout(output)
    validator = LocalSchemaRegistry(schema_root)
    questions = _standing_questions(locked_case, None)
    disclosure = locked_case["disclosure"]

    bundle = _empty_bundle(locked_case)
    bundle["scientific_contracts"] = [locked_case["scientific_contract"]]
    bundle["claims"] = [locked_case["claim"]]
    bundle["material_questions"] = questions
    bundle["disclosures"] = [disclosure]
    bundle["repository_snapshots"] = [snapshot_record]
    bundle["parser_results"] = parser_results
    bundle["asset_identities"] = list(locked_case.get("asset_identities", []))
    bundle["file_records"] = list(locked_case.get("file_records", []))
    bundle["operations"] = list(locked_case.get("observed_graph", {}).get("operations", []))
    bundle["artifacts"] = list(locked_case.get("observed_graph", {}).get("artifacts", []))
    observed_result = locked_case.get("observed_graph", {}).get("observed_result")
    bundle["observed_results"] = [observed_result] if isinstance(observed_result, dict) else []
    coverage = _coverage_record(
        locked_case,
        bundle,
        detector_results=[],
        overall_status=overall_status,
        termination_reason=termination_reason,
        pending_work=_PENDING_DETECTOR_WORK,
        run_state=run_state,
    )
    bundle["coverage_records"] = [coverage]

    for record in [
        locked_case["claim"],
        locked_case["scientific_contract"],
        *questions,
        disclosure,
        snapshot_record,
        *parser_results,
        *bundle["asset_identities"],
        coverage,
    ]:
        validator.validate(record)
    derived_store = JsonlRecordStore(layout.derived)
    for question in questions:
        derived_store.append(question)
    derived_store.append(disclosure)
    derived_store.append(coverage)
    return _write_preliminary_outputs(bundle, layout, validator)


def _write_preliminary_outputs(
    bundle: dict[str, Any], layout: AuditLayout, validator: LocalSchemaRegistry
) -> dict[str, Any]:
    validator.validate(bundle)
    write_normalized_json(layout.bundle_path, bundle)
    all_records = [record for field in _ARRAY_FIELDS for record in bundle[field]]
    rebuild_sqlite(layout.sqlite_path, all_records)
    render_report(bundle, layout.report_path)
    return bundle


def _finalize_bundle(
    bundle: dict[str, Any],
    locked_case: dict[str, Any],
    layout: AuditLayout,
    validator: LocalSchemaRegistry,
    derived_store: JsonlRecordStore,
) -> dict[str, Any]:
    _refresh_observed_bundle_arrays(bundle, layout.observed)
    storage_manifest = build_storage_manifest(
        layout, locked_case["audit_run_id"], locked_case["locked_at"]
    )
    validator.validate(storage_manifest)
    bundle["storage_manifests"] = [storage_manifest]
    validator.validate(bundle)
    derived_store.append(storage_manifest)
    write_normalized_json(layout.bundle_path, bundle)
    all_records = [record for field in _ARRAY_FIELDS for record in bundle[field]]
    rebuild_sqlite(layout.sqlite_path, all_records)
    verify_storage_manifest(layout, storage_manifest)
    verify_sqlite_index(layout.sqlite_path, all_records)
    render_report(bundle, layout.report_path)
    return bundle


def _refresh_observed_bundle_arrays(bundle: dict[str, Any], observed_root: Path) -> None:
    store = JsonlRecordStore(observed_root)
    mapping = {
        "audit_run": "audit_runs",
        "stage_result": "stage_results",
        "file_record": "file_records",
        "operation": "operations",
        "artifact": "artifacts",
        "observed_result": "observed_results",
        "deterministic_check_observation": "deterministic_check_observations",
        "data_asset": "data_assets",
        "variable": "variables",
        "analysis_decision": "analysis_decisions",
        "selection_envelope": "selection_envelopes",
        "execution": "executions",
        "project_execution_authorization": "project_execution_authorizations",
        "environment": "environments",
        "cache_entry": "cache_entries",
        "cache_policy": "cache_policies",
    }
    for record_type, array_name in mapping.items():
        records = list(store.iter_records(record_type))
        if records:
            bundle[array_name] = records


def _standing_questions(
    locked_case: dict[str, Any],
    detector_question: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    questions = list(locked_case.get("material_questions", [locked_case["material_question"]]))
    if detector_question and all(
        item["question_id"] != detector_question["question_id"] for item in questions
    ):
        questions.append(detector_question)
    return questions


def _coverage_record(
    locked_case: dict[str, Any],
    bundle: dict[str, Any],
    *,
    detector_results: list[dict[str, Any]],
    overall_status: str,
    termination_reason: str,
    pending_work: list[str],
    run_state: str,
) -> dict[str, Any]:
    evaluated_by_id = {result["detector_id"]: result for result in detector_results}
    detector_targets = [
        (
            "detector:claim-result-direction",
            "Claim/result direction was evaluated under the locked orientation.",
        ),
        (
            "detector:sample-unit-dependence",
            "Repeated-identifier dependence prerequisites were evaluated.",
        ),
    ]
    detector_coverage = []
    for detector_id, completed_details in detector_targets:
        result = evaluated_by_id.get(detector_id)
        if result is None:
            detector_coverage.append(
                {
                    "detector_id": detector_id,
                    "status": "not_covered",
                    "targets_total": 1,
                    "targets_evaluated": 0,
                    "details": "The target remained pending when deadline scheduling stopped.",
                }
            )
        else:
            detector_coverage.append(
                {
                    "detector_id": detector_id,
                    "status": result["coverage"]["status"],
                    "targets_total": 1,
                    "targets_evaluated": 1,
                    "details": completed_details,
                }
            )

    inventory_summary = locked_case.get(
        "inventory_summary",
        {"files_total": 0, "files_classified": 0, "files_deeply_inspected": 0},
    )
    parser_coverage = locked_case.get(
        "parser_coverage",
        [
            {
                "surface": "locked fixture inputs",
                "status": "covered",
                "details": "Replay used the parser coverage fixed in the supplied lock.",
            }
        ],
    )
    question_ids = [item["question_id"] for item in bundle["material_questions"]]
    known_gaps = [
        "The custom normalizer internal transformation and error model were not inspected.",
        "No selection envelope was reconstructed for the selected claim path.",
    ]
    weak_identity_count = sum(
        1 for item in bundle["asset_identities"] if item.get("tier") == "weak_fingerprint"
    )
    manifest_identity_count = sum(
        1 for item in bundle["asset_identities"] if item.get("tier") == "manifest"
    )
    unidentified_count = sum(
        1 for item in bundle["asset_identities"] if item.get("tier") == "unidentified"
    )
    if weak_identity_count:
        known_gaps.append(
            f"{weak_identity_count} asset(s) have only weak fingerprints; exact identity is "
            "unavailable and only dependent conclusions are limited."
        )
    if manifest_identity_count:
        known_gaps.append(
            f"{manifest_identity_count} asset(s) use repository-supplied manifest digests; "
            "the target bytes were not independently hashed and only dependent exact-byte "
            "verification is limited."
        )
    if unidentified_count:
        known_gaps.append(
            f"{unidentified_count} asset(s) remain unidentified; only conclusions that depend "
            "on their exact identity are limited."
        )
    _append_checksum_manifest_inspection_gaps(known_gaps, bundle)
    _append_nextflow_trace_gaps(known_gaps, bundle)
    workspace_state = locked_case.get("workspace_divergence", {})
    if workspace_state.get("status") == "workspace_diverged":
        changed_paths = workspace_state.get("changed_paths", [])
        known_gaps.append(
            "The live workspace diverged after snapshot capture; this run continued only against "
            f"the immutable snapshot ({len(changed_paths)} changed path(s))."
        )
    if pending_work:
        known_gaps.append(
            f"{len(pending_work)} detector targets remain unevaluated because scheduling stopped."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "coverage_record",
        "coverage_id": f"coverage:{locked_case['audit_run_id']}",
        "audit_run_id": locked_case["audit_run_id"],
        "generated_at": locked_case["locked_at"],
        "overall_status": overall_status,
        "scope": {
            "inventory_scope": "whole_repository",
            "deep_inspection_scope": (
                "single extracted walking-skeleton final-claim path; selection envelope unavailable"
            ),
            "publication_surface_refs": [locked_case["claim"]["report_ref"]],
            "publication_surface_status": "resolved",
            "selection_envelope_included": False,
        },
        "inventory_summary": inventory_summary,
        "assessment_counts": {
            "findings": len(bundle["findings"]),
            "conditional_concerns": len(bundle["conditional_concerns"]),
            "material_questions": len(bundle["material_questions"]),
            "disclosures": len(bundle["disclosures"]),
        },
        "claim_coverage": {
            "claims_total": len(bundle["claims"]),
            "claims_inspected": len(bundle["claims"]),
            "claims_with_complete_lineage": sum(
                claim["lineage"]["status"] == "complete" for claim in bundle["claims"]
            ),
            "lineage_grade_counts": _lineage_grade_counts(bundle["claims"]),
        },
        "parser_coverage": parser_coverage,
        "detector_coverage": detector_coverage,
        "unknown_semantic_ids": question_ids,
        "opaque_boundary_refs": _opaque_boundary_refs(locked_case, bundle),
        "uninspected_paths": list(locked_case.get("uninspected_paths", [])),
        "known_gaps": known_gaps,
        "interpretation_policy": {
            "correctness_conclusion_allowed": False,
            "global_risk_rating_allowed": False,
            "absence_of_finding_statement": (
                "No finding means only that no issue was admitted within the declared evidence "
                "and validated detector coverage."
            ),
        },
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_coverage_calculation",
            "created_at": locked_case["locked_at"],
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-run-state": run_state,
            "x-termination-reason": termination_reason,
            "x-pending-work": pending_work,
            "x-deeply-inspected-paths": list(locked_case.get("deeply_inspected_paths", [])),
            "x-uninspected-path-policy": (
                "Inventoried but outside the selected final-claim parser/verifier path."
            ),
        },
    }


def _lineage_grade_counts(claims: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    statuses = ("complete", "partial", "missing", "unavailable", "opaque")
    result: dict[str, dict[str, int]] = {}
    for dimension in LINEAGE_GRADE_DIMENSIONS:
        counts = {status: 0 for status in statuses}
        for claim in claims:
            status = claim.get("lineage", {}).get("grades", {}).get(dimension, {}).get("status")
            if status not in counts:
                raise ValueError(f"Claim lacks a valid {dimension} lineage grade")
            counts[str(status)] += 1
        counts["total"] = len(claims)
        result[dimension] = counts
    return result


def _empty_bundle(locked_case: dict[str, Any]) -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "audit_bundle",
        "bundle_id": f"bundle:{locked_case['audit_run_id']}",
        "audit_run_id": locked_case["audit_run_id"],
        "generated_at": locked_case["locked_at"],
        "semantic_lock_digest": locked_case["semantic_lock_digest"],
    }
    for array_field in _ARRAY_FIELDS:
        bundle[array_field] = []
    return bundle


def _derive_repository_observed_graph(
    locked_case: dict[str, Any],
    materialized_root: Path,
    python_result: dict[str, Any],
    markdown_result: dict[str, Any],
) -> dict[str, Any]:
    """Replace fixture-assembled claim/result values with bounded source-derived records."""

    python_extensions = python_result.get("extensions", {})
    markdown_extensions = markdown_result.get("extensions", {})
    operations = list(python_extensions.get("x-operations", []))
    artifacts = list(python_extensions.get("x-artifacts", []))
    literals = list(markdown_extensions.get("x-explicit-directional-claims", []))
    if len(literals) != 1:
        raise ValueError("fixture requires exactly one explicit directional Markdown claim")
    estimate_operations = [
        operation
        for operation in operations
        if operation.get("implementation") == "python.function:compute_difference"
        and operation.get("kind") == "estimate"
    ]
    if len(estimate_operations) != 1:
        raise ValueError("fixture requires exactly one supported compute_difference operation")
    operation = estimate_operations[0]
    input_artifact_ids = list(operation.get("input_refs", []))
    if not input_artifact_ids:
        raise ValueError("verified estimate operation has no exact input artifact")

    observed_result = verify_mean_difference(
        materialized_root / "analysis.py", locked_case["audit_run_id"]
    )
    literal = literals[0]
    report_source = markdown_result["source_ref"]
    report_digest = report_source.get("content_digest")
    if not isinstance(report_digest, str):
        raise ValueError("report parser did not establish content identity")
    report_artifact_id = stable_id("artifact", "report.md", report_digest)
    report_artifact = {
        "record_type": "artifact",
        "artifact_id": report_artifact_id,
        "run_id": locked_case["audit_run_id"],
        "kind": "publication_report",
        "path": "report.md",
        "identity": report_digest,
        "producer_operation_ids": [],
    }
    artifacts.append(report_artifact)

    contract = deepcopy(locked_case["scientific_contract"])
    declared_comparison = locked_case["claim"].get("proposition", {}).get("comparison")
    if not isinstance(declared_comparison, str):
        raise ValueError("fixture semantic declaration does not establish the claim comparison")
    claim = build_directional_claim(
        literal=literal,
        audit_run_id=locked_case["audit_run_id"],
        scientific_contract_id=contract["contract_id"],
        report_artifact_id=report_artifact_id,
        result_record_id=observed_result["result_id"],
        operation_record_id=operation["operation_id"],
        input_artifact_ids=input_artifact_ids,
        result_scale=observed_result["scale"],
        declared_comparison=declared_comparison,
    )
    claim_ref = {"record_type": "claim", "record_id": claim["claim_id"]}
    contract["scope"]["subject_refs"] = [claim_ref]
    contract["source_refs"] = [dict(literal["source_ref"])]
    locked_case["scientific_contract"] = contract
    locked_case["claim"] = claim
    public_graph = build_public_observed_graph(
        operations,
        artifacts,
        observed_result,
        python_result,
        claim,
        locked_case["locked_at"],
    )
    operations = public_graph.operations
    artifacts = public_graph.artifacts
    observed_result = public_graph.observed_result
    python_extensions["x-operations"] = operations
    python_extensions["x-artifacts"] = artifacts
    locked_case["observed_result"] = observed_result
    locked_case["dependence_operation_ref"] = {
        "record_type": "operation",
        "record_id": operation["operation_id"],
    }
    _retarget_fixture_questions(locked_case, claim["claim_id"])
    markdown_result["emitted_record_refs"] = [claim_ref]
    markdown_extensions["x-claims"] = [claim]

    return {
        "operations": operations,
        "artifacts": artifacts,
        "observed_result": observed_result,
        "asset_identities": public_graph.artifact_identities,
        "claim_id": claim["claim_id"],
        "operation_id": operation["operation_id"],
    }


def _record_inventory_coverage_inputs(
    locked_case: dict[str, Any],
    file_records: list[dict[str, Any]],
    parser_results: list[dict[str, Any]],
    observed_result: dict[str, Any],
) -> None:
    deeply_inspected_paths = {
        str(result["source_ref"]["path"])
        for result in parser_results
        if result.get("state") in {"parsed", "partially_parsed"}
        and isinstance(result.get("source_ref", {}).get("path"), str)
    }
    deeply_inspected_paths.update(
        str(source_ref["path"])
        for source_ref in observed_result.get("source_refs", [])
        if isinstance(source_ref.get("path"), str)
    )
    inventory_paths = {str(record["path"]) for record in file_records}
    locked_case["deeply_inspected_paths"] = sorted(deeply_inspected_paths)
    locked_case["uninspected_paths"] = sorted(inventory_paths - deeply_inspected_paths)
    locked_case["inventory_summary"] = {
        "files_total": len(file_records),
        "files_classified": sum(isinstance(record.get("role"), str) for record in file_records),
        "files_deeply_inspected": len(deeply_inspected_paths & inventory_paths),
    }
    parser_coverage = []
    for result in parser_results:
        source_ref = result.get("source_ref", {})
        source_path = source_ref.get("path", "unresolved source")
        parser_coverage.append(
            {
                "surface": f"{result['parser_id']}:{source_path}",
                "status": result["coverage_status"],
                "details": (
                    f"Exact parser result {result['parser_result_id']} recorded state "
                    f"{result['state']}; {len(result.get('syntax_issues', []))} syntax issue(s) "
                    f"and {len(result.get('opaque_constructs', []))} opaque construct(s)."
                ),
            }
        )
    parser_coverage.append(
        {
            "surface": "custom executable:opaque-normalizer",
            "status": "not_covered",
            "details": "The custom normalizer was retained as an opaque boundary.",
        }
    )
    locked_case["parser_coverage"] = parser_coverage


def _opaque_boundary_refs(
    locked_case: dict[str, Any], bundle: dict[str, Any]
) -> list[dict[str, Any]]:
    candidates = list(locked_case["claim"].get("lineage", {}).get("opaque_dependency_refs", []))
    for disclosure in bundle["disclosures"]:
        if disclosure.get("disclosure_kind") == "opaque_boundary":
            candidates.extend(disclosure.get("affected_refs", []))
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for reference in candidates:
        record_type = reference.get("record_type")
        record_id = reference.get("record_id")
        if isinstance(record_type, str) and isinstance(record_id, str):
            unique[(record_type, record_id)] = dict(reference)
    return [unique[key] for key in sorted(unique)]


def _retarget_fixture_questions(locked_case: dict[str, Any], claim_id: str) -> None:
    for key in ("material_question", "orientation_question"):
        value = locked_case.get(key)
        if isinstance(value, dict) and "affected_claim_ids" in value:
            updated = deepcopy(value)
            updated["affected_claim_ids"] = [claim_id]
            locked_case[key] = updated
    if isinstance(locked_case.get("material_questions"), list):
        updated_questions = []
        for question in locked_case["material_questions"]:
            updated = deepcopy(question)
            if "affected_claim_ids" in updated:
                updated["affected_claim_ids"] = [claim_id]
            updated_questions.append(updated)
        locked_case["material_questions"] = updated_questions


def _verify_locked_sources(locked_case: dict[str, Any], materialized_root: Path) -> bool:
    refs: list[dict[str, Any]] = []
    refs.extend(locked_case["claim"].get("source_refs", []))
    refs.extend(locked_case["scientific_contract"].get("source_refs", []))
    refs.extend(locked_case["observed_result"].get("source_refs", []))
    refs.extend(locked_case["disclosure"].get("source_refs", []))
    refs.extend(locked_case.get("repeated_identifier_observation", {}).get("source_refs", []))
    for ref in refs:
        path_value = ref.get("path")
        expected_digest = ref.get("content_digest")
        if not isinstance(path_value, str) or not isinstance(expected_digest, str):
            return False
        path = (materialized_root / path_value).resolve()
        try:
            path.relative_to(materialized_root.resolve())
        except ValueError:
            return False
        if not path.is_file() or path.is_symlink():
            return False
        payload = path.read_bytes()
        if sha256_digest(payload) != expected_digest:
            return False
        quoted = ref.get("quoted_text")
        start = ref.get("start_line")
        end = ref.get("end_line")
        if isinstance(quoted, str) and isinstance(start, int) and isinstance(end, int):
            lines = payload.decode("utf-8", errors="strict").splitlines()
            if start < 1 or end < start or end > len(lines):
                return False
            excerpt = "\n".join(lines[start - 1 : end])
            if quoted.strip() not in excerpt:
                return False
    manifest_pairs = [
        (locked_case.get("detector_manifest_path"), locked_case.get("detector_manifest_digest")),
        (
            locked_case.get("dependence_detector_manifest_path"),
            locked_case.get("dependence_detector_manifest_digest"),
        ),
    ]
    for manifest_path, expected_manifest_digest in manifest_pairs:
        if not isinstance(manifest_path, str) or not isinstance(expected_manifest_digest, str):
            return False
        manifest = materialized_root / manifest_path
        if (
            not manifest.is_file()
            or manifest.is_symlink()
            or sha256_digest(manifest.read_bytes()) != expected_manifest_digest
        ):
            return False
    return True


def _observe_live_workspace(
    repository: Path,
    snapshot_record: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identity_records: list[dict[str, Any]],
    identity_policy: AssetIdentityPolicy,
    locked_case: dict[str, Any],
) -> None:
    observed = detect_workspace_divergence(
        repository,
        file_records,
        detected_at=locked_case["locked_at"],
        initial_asset_identities=asset_identity_records,
        identity_policy=identity_policy,
    )
    snapshot_record["live_workspace_state"] = merge_workspace_state(
        snapshot_record["live_workspace_state"], observed
    )
