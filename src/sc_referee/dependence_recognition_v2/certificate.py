"""Small trusted kernel for dependence growth group and symbolic-count certificates."""

from __future__ import annotations

import ast
import copy
import csv
import io
import json
import math
import posixpath
import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from typing import Any, Literal, cast

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
    SPLITLINES_ONLY_SEPARATORS,
    HumanMethodAuthorization,
    RecordRef,
)
from sc_referee.dependence_recognition_v2.ir import (
    DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS,
    MAX_V2_AST_NODES,
    MAX_V2_GROUPS,
    MAX_V2_INLINE_DEPTH,
    MAX_V2_SOURCE_BYTES,
    AbortOnlyGuardNameRole,
    AbortOnlyGuardToken,
    AuthorizedProcedureSet,
    CountDependenceCertificate,
    CountGroupDomainObligation,
    CountOperandObligation,
    CountPredicateAtom,
    CountProcedureFact,
    DependenceGrowthCertificate,
    GroupValueSequence,
    GroupValueSequenceFact,
    GroupValueSequenceObligation,
    PairedDependenceCertificate,
    PairedObservation,
    PairedValueSequenceFact,
    PairedValueSequenceObligation,
    PandasOperandProjection,
    PandasPackageIdentity,
    PandasSourceDescriptor,
    VerifiedCountDependenceCertificate,
    VerifiedDependenceGrowthCertificate,
    VerifiedPairedDependenceCertificate,
)
from sc_referee.dependence_recognition_v2.pandas_runtime_premise import (
    PANDAS_3_0_5_DEFAULT_MISSING_TOKENS,
    PANDAS_DEVELOPMENT_RUNTIME_PREMISE,
    PANDAS_DEVELOPMENT_RUNTIME_PREMISE_DIGEST,
    PANDAS_GROUP_CASEFOLD_REFUSALS,
    PANDAS_GROUP_LITERAL_PATTERN,
    PANDAS_VALUE_PATTERN,
)
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput

_PROCEDURE_ARITY = {
    "scipy.stats.ttest_ind": 2,
    "scipy.stats.ttest_ind:welch": 2,
    "scipy.stats.mannwhitneyu": 2,
}
_ROW_INDEPENDENT_VARIANTS = frozenset(_PROCEDURE_ARITY)
_GROUP_BASE_PROCEDURES = frozenset({"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"})
_COUNT_PROCEDURES = frozenset({"scipy.stats.binomtest", "scipy.stats.fisher_exact"})
_PAIRED_PROCEDURES = frozenset({"scipy.stats.ttest_rel", "scipy.stats.wilcoxon"})
_ALL_PROCEDURES = frozenset((*_PROCEDURE_ARITY, *_COUNT_PROCEDURES, *_PAIRED_PROCEDURES))
_DISTRIBUTION_HELPER_METHODS = frozenset(
    f"scipy.stats.{distribution}.{method}"
    for distribution in ("t", "norm")
    for method in ("ppf", "cdf", "sf")
)
assert not (_GROUP_BASE_PROCEDURES | _COUNT_PROCEDURES) & _DISTRIBUTION_HELPER_METHODS


@dataclass(frozen=True)
class _KernelGuardReplay:
    token: AbortOnlyGuardToken
    condition: ast.expr


@dataclass(frozen=True)
class _KernelSourceReplay:
    body: tuple[ast.stmt, ...]
    operand_names: frozenset[str]
    guards: tuple[_KernelGuardReplay, ...]


@dataclass(frozen=True)
class _KernelPandasSourceReplay:
    descriptor: PandasSourceDescriptor
    body: tuple[ast.stmt, ...]
    procedure_statement: ast.Assign
    procedure_call: ast.Call
    writer_statement: ast.With
    write_call: ast.Call
    projections: tuple[tuple[str, str], ...]
    operand_bindings: tuple[tuple[int, str, str], ...]


def _kernel_pandas_source_shape(descriptor: PandasSourceDescriptor) -> tuple[object, ...]:
    """Project only source-form fields; lineage and result flow have later rows."""

    return (
        descriptor.package_identity,
        descriptor.import_span,
        descriptor.reader_span,
        descriptor.reader_path,
        descriptor.group_column,
        descriptor.value_column,
        tuple(
            (
                item.group_key,
                item.projection,
                item.selection_span,
                item.projection_span,
            )
            for item in descriptor.operands
        ),
        descriptor.procedure_variant,
        descriptor.procedure_call_span,
        descriptor.procedure_target_span,
        descriptor.summary_spans,
        descriptor.directory_preparation_spans,
        descriptor.writer_span,
        descriptor.write_span,
        descriptor.writer_path,
        descriptor.executable_statement_tokens,
    )


def _kernel_pandas_partition_lineage(
    descriptor: PandasSourceDescriptor,
) -> tuple[object, ...]:
    return (
        descriptor.frame_name,
        tuple((item.base_series_name, item.operand_name) for item in descriptor.operands),
    )


def _kernel_pandas_result_shape(descriptor: PandasSourceDescriptor) -> tuple[object, ...]:
    return (descriptor.procedure_result_names, descriptor.writer_handle)


def verify_dependence_growth_certificate(
    certificate: DependenceGrowthCertificate,
    *,
    trusted_group_facts: tuple[GroupValueSequenceFact, ...],
    trusted_material_inputs: tuple[FrozenMaterialInput, ...],
    trusted_authorizations: tuple[HumanMethodAuthorization, ...],
    trusted_procedure_sets: tuple[AuthorizedProcedureSet, ...] = (),
    source_bytes: bytes,
    trusted_base_records: tuple[FrozenBaseRecord, ...] = (),
    trusted_file_manifest_input: object | None = None,
    _failure_reasons: list[str] | None = None,
) -> VerifiedDependenceGrowthCertificate | None:
    """Discharge every equation from source bytes and one trusted material replay."""

    def refuse(obligation: str) -> VerifiedDependenceGrowthCertificate | None:
        if obligation not in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS:
            raise AssertionError(f"unknown kernel refusal obligation: {obligation}")
        if _failure_reasons is not None:
            _failure_reasons.append(obligation)
        return None

    pandas_mode = certificate.obligation.pandas_source is not None
    if (
        len(trusted_group_facts) != 1
        or len(trusted_material_inputs) != 1
        or len(trusted_authorizations) != 1
        or not isinstance(trusted_material_inputs[0], FrozenMaterialInput)
        or sha256_digest(source_bytes) != certificate.source_digest
        or certificate.source_extent != (0, len(source_bytes))
        or not certificate.resolved_callables
        or any(item not in _PROCEDURE_ARITY for item in certificate.resolved_callables)
        or len(certificate.resolved_callables) != len(certificate.procedure_call_tokens)
        or (
            not pandas_mode and len(certificate.resolved_callables) != len(certificate.result_names)
        )
        or (
            pandas_mode
            and (len(certificate.resolved_callables) != 1 or len(certificate.result_names) != 2)
        )
        or not certificate.authority_record_id
        or not certificate.independent_unit_definition_id
    ):
        return refuse("envelope-binding")
    supplied_fact = trusted_group_facts[0]
    material = trusted_material_inputs[0]
    authority = trusted_authorizations[0]
    obligation = certificate.obligation
    if (
        authority.record_type != "human_method_authorization"
        or authority.authority_state != "authorized"
        or authority.record_id != certificate.authority_record_id
        or authority.analysis_target_ref != certificate.analysis_target_ref
        or authority.procedure_ref != certificate.procedure_ref
        or authority.independent_unit_definition_id != certificate.independent_unit_definition_id
        or authority.authorized_key_columns != (obligation.authorized_unit_column,)
        or authority.input_path != obligation.path
        or authority.input_content_digest != obligation.content_digest
    ):
        return refuse("authority-binding")
    if trusted_procedure_sets:
        authorized_callables = trusted_procedure_sets[0].resolved_callables
        certificate_authority_callables = tuple(dict.fromkeys(certificate.resolved_callables))
        if pandas_mode:
            authorized_callables = tuple(item.split(":", 1)[0] for item in authorized_callables)
            certificate_authority_callables = tuple(
                item.split(":", 1)[0] for item in certificate_authority_callables
            )
        if (
            len(trusted_procedure_sets) != 1
            or trusted_procedure_sets[0].record_id != authority.procedure_ref.record_id
            or authorized_callables != certificate_authority_callables
        ):
            return refuse("authority-binding")
    elif len(certificate.resolved_callables) != 1:
        # Legacy hand-built single-call certificates predate the set channel;
        # no multi-call claim can use that compatibility path.
        return refuse("authority-binding")
    if any(item not in _ROW_INDEPENDENT_VARIANTS for item in certificate.resolved_callables):
        return refuse("procedure-set-homogeneity")
    if pandas_mode:
        verified, failure = _verify_pandas_dependence_certificate(
            certificate,
            supplied_fact=supplied_fact,
            material=material,
            authority=authority,
            source_bytes=source_bytes,
            trusted_base_records=trusted_base_records,
            trusted_file_manifest_input=trusted_file_manifest_input,
        )
        if failure is not None:
            return refuse(failure)
        return verified
    replayed_fact = _kernel_replay_group_fact(material, obligation)
    if replayed_fact is None or supplied_fact != replayed_fact:
        return refuse("fact-closure")
    fact = replayed_fact
    if (
        fact.evidence_id != f"dependence-growth-group-proof:{semantic_digest(asdict(obligation))}"
        or fact.row_count <= 0
        or fact.row_count > 10_000
        or len(fact.groups) > 256
        or not fact.header
        or len(fact.header) != len(set(fact.header))
        or any(not item for item in fact.header)
        or not {
            fact.authorized_unit_column,
            fact.group_key_column,
            fact.value_column,
        }
        <= set(fact.header)
        or fact.path != obligation.path
        or fact.content_digest != obligation.content_digest
        or fact.line_model != obligation.line_model
        or fact.reader_form != obligation.reader_form
        or fact.encoding != obligation.encoding
        or fact.authorized_unit_column != obligation.authorized_unit_column
        or fact.group_key_column != obligation.group_key_column
        or fact.value_column != obligation.value_column
        or fact.cast_kind != obligation.cast_kind
        or fact.predeclared_bucket_keys != obligation.predeclared_bucket_keys
        or (fact.encoding == "ascii" and not fact.ascii_bytes_proven)
    ):
        return refuse("fact-closure")
    try:
        tree = ast.parse(source_bytes.decode("utf-8", errors="strict"))
        compile(tree, certificate.source_path, "exec")
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError, RecursionError):
        return refuse("source-parse")
    if len(source_bytes) > MAX_V2_SOURCE_BYTES or sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return refuse("source-size")
    tree = _kernel_without_docstrings(tree)
    if _kernel_abort_only_raise_wall(tree):
        return refuse("source-semantic-replay")
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("rename-injectivity")
    source_replay = _kernel_replay_source_claims(tree, certificate, fact)
    if source_replay is None:
        return refuse("source-semantic-replay")
    if not _kernel_sink_partition_matches(
        tree,
        certificate,
        precomputed_partition=(list(source_replay.body), set(source_replay.operand_names)),
        abort_only_guards=tuple(item.token for item in source_replay.guards),
    ):
        return refuse("sink-partition")

    groups = {item.group_key: item for item in fact.groups}
    if len(groups) != len(fact.groups) or not groups:
        return refuse("group-partition")
    all_rows = [index for group in fact.groups for index in group.row_indices]
    if sorted(all_rows) != list(range(1, fact.row_count + 1)) or len(all_rows) != fact.row_count:
        return refuse("group-partition")
    all_observations = [item for group in fact.groups for item in group.observation_ids]
    if len(all_observations) != len(set(all_observations)) or any(
        not item for item in all_observations
    ):
        return refuse("observation-identity")
    for group in fact.groups:
        length = len(group.row_indices)
        if not (
            length
            == len(group.observation_ids)
            == len(group.authorized_unit_ids)
            == len(group.source_values)
            == len(group.cast_value_reprs)
        ):
            return refuse("group-length-equation")

    if len({_PROCEDURE_ARITY[item] for item in certificate.resolved_callables}) != 1:
        return refuse("operand-binding")
    arity = _PROCEDURE_ARITY[certificate.resolved_callables[0]]
    bindings = certificate.operand_bindings
    if (
        len(bindings) != arity
        or tuple(item.position for item in bindings) != tuple(range(arity))
        or len({item.group_key for item in bindings}) != len(bindings)
        or {item.group_key for item in bindings} != set(groups)
    ):
        return refuse("operand-binding")

    unit_operand_memberships: dict[str, set[int]] = {}
    repeated: set[str] = set()
    for binding in bindings:
        sequence = groups[binding.group_key]
        counts = Counter(sequence.authorized_unit_ids)
        repeated.update(unit for unit, count in counts.items() if count > 1)
        for unit in counts:
            unit_operand_memberships.setdefault(unit, set()).add(binding.position)
    if any(len(positions) > 1 for positions in unit_operand_memberships.values()):
        return refuse("operand-disjointness")
    guard_truths = [
        _kernel_abort_only_guard_truth(item, fact, bindings) for item in source_replay.guards
    ]
    if any(item is None for item in guard_truths):
        return refuse("source-semantic-replay")
    if any(item is True for item in guard_truths):
        if _failure_reasons is not None:
            _failure_reasons.append("sink-controls-operand-flow")
        return None
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    if certificate.conclusion != conclusion:
        return refuse("conclusion-equation")

    renames = certificate.alpha_renames
    if len({item.fresh_name for item in renames}) != len(renames):
        return refuse("alpha-renaming")
    if any(
        not item.fresh_name.startswith("__dependence_v2_")
        or item.original_name == item.fresh_name
        or not item.call_path_id
        or len(item.call_span) != 4
        for item in renames
    ):
        return refuse("alpha-renaming")
    if len(set(certificate.dead_syntactic_construct_tokens)) != len(
        certificate.dead_syntactic_construct_tokens
    ):
        return refuse("dead-construct-completeness")
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("dead-construct-completeness")

    expected_id = f"dependence-growth-certificate:{semantic_digest({'source_digest': certificate.source_digest, 'fact': fact.evidence_id, 'bindings': [asdict(item) for item in bindings], 'abort_only_guard_tokens': [asdict(item) for item in certificate.abort_only_guard_tokens], 'conclusion': conclusion})}"
    if certificate.certificate_id != expected_id:
        return refuse("certificate-identity")
    return VerifiedDependenceGrowthCertificate(
        certificate_id=certificate.certificate_id,
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        resolved_callables=certificate.resolved_callables,
        conclusion=conclusion,
        fact=fact,
        operand_bindings=bindings,
        repeated_unit_ids=tuple(sorted(repeated)),
        alpha_renames=renames,
        operand_slice_statement_tokens=certificate.operand_slice_statement_tokens,
        sink_bound_statement_tokens=certificate.sink_bound_statement_tokens,
        dead_syntactic_construct_tokens=certificate.dead_syntactic_construct_tokens,
        abort_only_guard_tokens=certificate.abort_only_guard_tokens,
    )


def _verify_pandas_dependence_certificate(
    certificate: DependenceGrowthCertificate,
    *,
    supplied_fact: GroupValueSequenceFact,
    material: FrozenMaterialInput,
    authority: HumanMethodAuthorization,
    source_bytes: bytes,
    trusted_base_records: tuple[FrozenBaseRecord, ...],
    trusted_file_manifest_input: object | None,
) -> tuple[VerifiedDependenceGrowthCertificate | None, str | None]:
    """Apply Growth-14's fixed six-obligation kernel in total order."""

    obligation = certificate.obligation
    proposed_source = obligation.pandas_source
    if proposed_source is None:
        return None, "pandas-source-closure"

    package_identity = _kernel_pandas_package_identity(
        trusted_base_records,
        file_manifest_input=trusted_file_manifest_input,
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        material=material,
    )
    if package_identity is None or package_identity != proposed_source.package_identity:
        return None, "pandas-package-identity"

    try:
        source = source_bytes.decode("utf-8", errors="strict")
        tree = ast.parse(source)
        compile(tree, certificate.source_path, "exec")
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError, RecursionError):
        return None, "pandas-source-closure"
    if len(source_bytes) > MAX_V2_SOURCE_BYTES or sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return None, "pandas-source-closure"
    replay_rows: list[_KernelPandasSourceReplay] = []
    replay_failures: list[str] = []
    partition = _kernel_partition_body(
        tree,
        certificate,
        pandas_source_path=certificate.source_path,
        pandas_package_identity=package_identity,
        pandas_replay_out=replay_rows,
        pandas_failure_out=replay_failures,
    )
    if replay_failures:
        return None, replay_failures[0]
    if len(replay_rows) != 1:
        return None, "pandas-source-closure"
    replay = replay_rows[0]
    if (
        _kernel_pandas_source_shape(replay.descriptor)
        != _kernel_pandas_source_shape(proposed_source)
        or certificate.resolved_callables != (replay.descriptor.procedure_variant,)
        or certificate.procedure_call_tokens
        != (_kernel_node_token(certificate.source_path, replay.procedure_call, "procedure-call"),)
        or certificate.alpha_renames
        or certificate.dead_syntactic_construct_tokens
    ):
        return None, "pandas-source-closure"

    expected_bindings = tuple(
        (item.position, item.argument_name, item.group_key) for item in certificate.operand_bindings
    )
    if (
        partition is None
        or _kernel_pandas_partition_lineage(replay.descriptor)
        != _kernel_pandas_partition_lineage(proposed_source)
        or expected_bindings != replay.operand_bindings
        or certificate.group_container_name != replay.descriptor.frame_name
        or certificate.group_container_kind != "pandas_series"
        or not _kernel_sink_partition_matches(
            tree,
            certificate,
            precomputed_partition=partition,
            pandas_replay=replay,
        )
    ):
        return None, "pandas-single-partition"

    rebuilt_fact = _kernel_replay_pandas_group_fact(material, obligation)
    if rebuilt_fact is None:
        return None, "pandas-material-domain"
    material_fields_match = (
        supplied_fact.path == rebuilt_fact.path
        and supplied_fact.content_digest == rebuilt_fact.content_digest
        and supplied_fact.file_ref == rebuilt_fact.file_ref
        and supplied_fact.asset_identity_ref == rebuilt_fact.asset_identity_ref
        and supplied_fact.line_model == rebuilt_fact.line_model
        and supplied_fact.reader_form == rebuilt_fact.reader_form
        and supplied_fact.encoding == rebuilt_fact.encoding
        and supplied_fact.ascii_bytes_proven == rebuilt_fact.ascii_bytes_proven
        and supplied_fact.header == rebuilt_fact.header
        and supplied_fact.authorized_unit_column == rebuilt_fact.authorized_unit_column
        and supplied_fact.group_key_column == rebuilt_fact.group_key_column
        and supplied_fact.value_column == rebuilt_fact.value_column
        and supplied_fact.cast_kind == rebuilt_fact.cast_kind
        and supplied_fact.row_count == rebuilt_fact.row_count
        and supplied_fact.predeclared_bucket_keys == rebuilt_fact.predeclared_bucket_keys
    )
    if not material_fields_match:
        return None, "pandas-material-domain"
    if supplied_fact != rebuilt_fact:
        return None, "pandas-operand-values"
    fact = rebuilt_fact

    if _kernel_pandas_result_shape(replay.descriptor) != _kernel_pandas_result_shape(
        proposed_source
    ) or not _kernel_pandas_result_sink_closed(tree, certificate, replay):
        return None, "pandas-result-sink"

    groups = {item.group_key: item for item in fact.groups}
    if (
        len(groups) != 2
        or len(groups) != len(fact.groups)
        or tuple(item.position for item in certificate.operand_bindings) != (0, 1)
        or {item.group_key for item in certificate.operand_bindings} != set(groups)
    ):
        return None, "pandas-operand-values"
    physical_rows = [index for group in fact.groups for index in group.row_indices]
    if sorted(physical_rows) != list(range(1, fact.row_count + 1)) or len(physical_rows) != len(
        set(physical_rows)
    ):
        return None, "pandas-operand-values"
    for group in fact.groups:
        size = len(group.row_indices)
        if not (
            size
            == len(group.observation_ids)
            == len(group.authorized_unit_ids)
            == len(group.source_values)
            == len(group.cast_value_reprs)
        ):
            return None, "pandas-operand-values"

    unit_positions: dict[str, set[int]] = {}
    repeated: set[str] = set()
    for binding in certificate.operand_bindings:
        counts = Counter(groups[binding.group_key].authorized_unit_ids)
        repeated.update(unit for unit, count in counts.items() if count > 1)
        for unit in counts:
            unit_positions.setdefault(unit, set()).add(binding.position)
    if any(len(positions) > 1 for positions in unit_positions.values()):
        return None, "operand-disjointness"
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    if certificate.conclusion != conclusion:
        return None, "conclusion-equation"

    expected_projection = {
        "source_digest": certificate.source_digest,
        "fact": fact.evidence_id,
        "bindings": [asdict(item) for item in certificate.operand_bindings],
        "abort_only_guard_tokens": [asdict(item) for item in certificate.abort_only_guard_tokens],
        "conclusion": conclusion,
        "pandas_replayed_fact": asdict(fact),
        "pandas_source": asdict(proposed_source),
    }
    expected_id = f"dependence-growth-certificate:{semantic_digest(expected_projection)}"
    if certificate.certificate_id != expected_id:
        return None, "certificate-identity"
    return (
        VerifiedDependenceGrowthCertificate(
            certificate_id=certificate.certificate_id,
            source_path=certificate.source_path,
            source_digest=certificate.source_digest,
            resolved_callables=certificate.resolved_callables,
            conclusion=cast(Any, conclusion),
            fact=fact,
            operand_bindings=certificate.operand_bindings,
            repeated_unit_ids=tuple(sorted(repeated)),
            alpha_renames=(),
            operand_slice_statement_tokens=certificate.operand_slice_statement_tokens,
            sink_bound_statement_tokens=certificate.sink_bound_statement_tokens,
            dead_syntactic_construct_tokens=(),
            abort_only_guard_tokens=certificate.abort_only_guard_tokens,
        ),
        None,
    )


def _kernel_pandas_package_identity(
    base_records: tuple[FrozenBaseRecord, ...],
    *,
    file_manifest_input: object | None,
    source_path: str,
    source_digest: str,
    material: FrozenMaterialInput,
) -> PandasPackageIdentity | None:
    """Independently join the snapshot, complete manifest records, and identities."""

    try:
        snapshot_pairs = [
            (record, json.loads(record.canonical_payload))
            for record in base_records
            if record.ref.record_type == "repository_snapshot"
        ]
        if len(snapshot_pairs) != 1:
            return None
        snapshot_record, snapshot = snapshot_pairs[0]
        if not isinstance(snapshot, dict):
            return None
        snapshot_digest = snapshot.get("snapshot_digest")
        manifest_ref = snapshot.get("file_manifest_ref")
        if (
            snapshot.get("included_roots") != ["."]
            or snapshot.get("immutability") is not True
            or not isinstance(snapshot_digest, str)
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", snapshot_digest)
            or not isinstance(manifest_ref, str)
            or not manifest_ref
        ):
            return None
        input_ref = getattr(file_manifest_input, "file_manifest_ref", None)
        manifest_bytes = getattr(file_manifest_input, "canonical_jsonl_bytes", None)
        manifest_digest = getattr(file_manifest_input, "manifest_digest", None)
        if (
            input_ref != manifest_ref
            or not isinstance(manifest_bytes, bytes)
            or not isinstance(manifest_digest, str)
        ):
            return None
        file_records = _kernel_manifest_record_bijection(
            base_records,
            snapshot_record=snapshot_record,
            manifest_bytes=manifest_bytes,
            manifest_digest=manifest_digest,
        )
        if file_records is None:
            return None
        identity_by_ref: dict[tuple[str, str], FrozenBaseRecord] = {}
        for record in base_records:
            if record.ref.record_type != "asset_identity":
                continue
            key = (record.ref.record_type, record.ref.record_id)
            if key in identity_by_ref:
                return None
            identity_by_ref[key] = record
        identity_claims: Counter[tuple[str, str]] = Counter()
        for identity_record in identity_by_ref.values():
            value = json.loads(identity_record.canonical_payload)
            claimed = value.get("asset_ref") if isinstance(value, dict) else None
            if (
                isinstance(claimed, dict)
                and claimed.get("record_type") == "file_record"
                and isinstance(claimed.get("record_id"), str)
            ):
                identity_claims[("file_record", str(claimed["record_id"]))] += 1
        entries: list[tuple[str, str]] = []
        seen_paths: set[str] = set()
        source_match = 0
        material_match = 0
        for record, payload in file_records:
            path = cast(str, payload["path"])
            if payload["entry_kind"] != "regular_file" or path in seen_paths:
                return None
            seen_paths.add(path)
            identity_ref = payload.get("asset_identity_ref")
            assert isinstance(identity_ref, dict)
            ref = (
                str(identity_ref.get("record_type", "")),
                str(identity_ref.get("record_id", "")),
            )
            matched_identity_record = identity_by_ref.get(ref)
            if matched_identity_record is None:
                return None
            identity = json.loads(matched_identity_record.canonical_payload)
            evidence = identity.get("identity_evidence") if isinstance(identity, dict) else None
            digest = evidence.get("digest") if isinstance(evidence, dict) else None
            if (
                not isinstance(identity, dict)
                or identity.get("record_type") != "asset_identity"
                or identity.get("asset_identity_id") != matched_identity_record.ref.record_id
                or identity.get("tier") != "full_digest"
                or identity.get("asset_ref") != record.ref.to_dict()
                or identity_claims[record.ref.record_type, record.ref.record_id] != 1
                or not isinstance(evidence, dict)
                or evidence.get("kind") != "full_digest"
                or not isinstance(digest, str)
                or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest)
            ):
                return None
            entries.append((path, digest))
            source_match += int(path == source_path and digest == source_digest)
            material_match += int(path == material.path and digest == material.content_digest)
        if (
            not entries
            or source_match != 1
            or material_match != 1
            or _kernel_pandas_inventory_forbidden(seen_paths, source_path)
        ):
            return None
        inventory_projection = [
            {"path": path, "digest": digest}
            for path, digest in sorted(entries, key=lambda item: tuple(item[0].split("/")))
        ]
        return PandasPackageIdentity(
            runtime_premise_id=PANDAS_DEVELOPMENT_RUNTIME_PREMISE.premise_id,
            runtime_premise_digest=PANDAS_DEVELOPMENT_RUNTIME_PREMISE_DIGEST,
            snapshot_ref=RecordRef(snapshot_record.ref.record_type, snapshot_record.ref.record_id),
            snapshot_digest=snapshot_digest,
            file_manifest_ref=manifest_ref,
            file_manifest_digest=manifest_digest,
            inventory_digest=semantic_digest(inventory_projection),
            regular_file_count=len(entries),
        )
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return None


def _kernel_manifest_record_bijection(
    base_records: tuple[FrozenBaseRecord, ...],
    *,
    snapshot_record: FrozenBaseRecord,
    manifest_bytes: bytes,
    manifest_digest: str,
) -> tuple[tuple[FrozenBaseRecord, dict[str, Any]], ...] | None:
    """Kernel-local canonical JSONL parse and all-entry file-record bijection."""

    try:
        raw = manifest_bytes
        if (
            not re.fullmatch(r"sha256:[a-f0-9]{64}", manifest_digest)
            or sha256_digest(raw) != manifest_digest
            or not raw
            or raw[-1:] != b"\n"
        ):
            return None
        expected_snapshot_ref = snapshot_record.ref.to_dict()
        base_rows: list[tuple[FrozenBaseRecord, dict[str, Any]]] = []
        base_ids: set[str] = set()
        base_paths: set[str] = set()
        for candidate in base_records:
            if candidate.ref.record_type != "file_record":
                continue
            value = json.loads(candidate.canonical_payload)
            if not isinstance(value, dict) or value.get("snapshot_ref") != expected_snapshot_ref:
                continue
            identifier = value.get("file_record_id")
            path = value.get("path")
            kind = value.get("entry_kind")
            byte_size = value.get("byte_size")
            identity_ref = value.get("asset_identity_ref")
            if (
                value.get("record_type") != "file_record"
                or identifier != candidate.ref.record_id
                or not isinstance(identifier, str)
                or identifier in base_ids
                or not isinstance(path, str)
                or not path
                or path.startswith("/")
                or ".." in path.split("/")
                or path == "."
                or posixpath.normpath(path) != path
                or path in base_paths
                or not isinstance(kind, str)
                or not kind
                or not isinstance(byte_size, int)
                or isinstance(byte_size, bool)
                or byte_size < 0
                or not isinstance(identity_ref, dict)
                or identity_ref.get("record_type") != "asset_identity"
                or not isinstance(identity_ref.get("record_id"), str)
                or not identity_ref["record_id"]
            ):
                return None
            base_ids.add(identifier)
            base_paths.add(path)
            base_rows.append((candidate, value))
        if not base_rows:
            return None
        by_identifier = {row[0].ref.record_id: row for row in base_rows}

        ordered_matches: list[tuple[FrozenBaseRecord, dict[str, Any]]] = []
        parsed_ids: set[str] = set()
        parsed_paths: set[str] = set()
        for encoded in raw[:-1].split(b"\n"):
            if not encoded:
                return None
            decoded = encoded.decode("utf-8", errors="strict")
            value = json.loads(decoded)
            if not isinstance(value, dict) or canonical_json(value).encode("utf-8") != encoded:
                return None
            identifier = value.get("file_record_id")
            path = value.get("path")
            if (
                value.get("record_type") != "file_record"
                or value.get("snapshot_ref") != expected_snapshot_ref
                or not isinstance(identifier, str)
                or identifier in parsed_ids
                or not isinstance(path, str)
                or path in parsed_paths
            ):
                return None
            match = by_identifier.get(identifier)
            if match is None or match[0].canonical_payload != encoded:
                return None
            parsed_ids.add(identifier)
            parsed_paths.add(path)
            ordered_matches.append(match)
        if parsed_ids != base_ids or len(ordered_matches) != len(base_rows):
            return None
        return tuple(ordered_matches)
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return None


def _kernel_pandas_inventory_forbidden(paths: set[str], source_path: str) -> bool:
    ancestors: set[str] = {""}
    current = posixpath.dirname(source_path)
    while current:
        ancestors.add(current)
        current = posixpath.dirname(current)
    for path in paths:
        directory, _, basename = path.rpartition("/")
        if directory in ancestors and (
            basename
            in {
                "pandas.py",
                "pandas.pyc",
                "sitecustomize.py",
                "usercustomize.py",
            }
            or basename.endswith(".pth")
        ):
            return True
        components = path.split("/")
        if any(
            component == "pandas" and "/".join(components[:index]) in ancestors
            for index, component in enumerate(components[:-1])
        ):
            return True
    return False


def _kernel_pandas_source_replay(
    tree: ast.Module,
    source_path: str,
    package_identity: PandasPackageIdentity,
) -> tuple[_KernelPandasSourceReplay | None, str | None]:
    """Independently reconstruct the closed pandas source descriptor."""

    try:
        top_level = _kernel_without_leading_docstring_statements(tree.body)
        pandas_imports = [
            statement
            for statement in top_level
            if isinstance(statement, ast.Import)
            and len(statement.names) == 1
            and statement.names[0].name == "pandas"
            and statement.names[0].asname == "pd"
        ]
        every_pandas_import = [
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Import)
                and any(
                    alias.name == "pandas" or alias.name.startswith("pandas.")
                    for alias in node.names
                )
            )
            or (
                isinstance(node, ast.ImportFrom)
                and isinstance(node.module, str)
                and (node.module == "pandas" or node.module.startswith("pandas."))
            )
        ]
        if len(pandas_imports) != 1 or len(every_pandas_import) != 1:
            return None, "pandas-source-closure"
        if not _kernel_pandas_imports_closed(top_level, pandas_imports[0]):
            return None, "pandas-source-closure"
        if any(
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            for node in ast.walk(tree)
        ):
            return None, "pandas-source-closure"
        if any(
            isinstance(node, ast.AnnAssign | ast.AugAssign | ast.NamedExpr | ast.Delete)
            for node in ast.walk(tree)
        ):
            return None, "pandas-source-closure"

        imports = _kernel_imports(tree)
        nonimports = [
            statement
            for statement in top_level
            if not isinstance(statement, ast.Import | ast.ImportFrom)
        ]
        reader_candidates = [
            (index, statement)
            for index, statement in enumerate(nonimports)
            if _kernel_pandas_reader_call(statement) is not None
        ]
        if len(reader_candidates) != 1:
            return None, "pandas-source-closure"
        reader_index, reader_statement_value = reader_candidates[0]
        reader_statement = cast(ast.Assign, reader_statement_value)
        constants, constant_indices = _kernel_pandas_constants(nonimports, reader_index)
        body = [
            statement for index, statement in enumerate(nonimports) if index not in constant_indices
        ]
        call = cast(ast.Call, reader_statement.value)
        reader_path = _kernel_path_value(call.args[0], constants) if len(call.args) == 1 else None
        if call.keywords or not isinstance(reader_path, str):
            return None, "pandas-source-closure"
        frame_name = cast(ast.Name, reader_statement.targets[0]).id
        if (
            sum(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "pd"
                for node in ast.walk(tree)
            )
            != 1
        ):
            return None, "pandas-source-closure"

        selection_rows: list[tuple[ast.Assign, ast.expr, str, str, str, str]] = []
        for statement in body:
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                continue
            parsed = _kernel_pandas_selection(statement.value, frame_name, constants)
            if parsed is None:
                continue
            base, group_column, value_column, group_key, projection = parsed
            selection_rows.append(
                (
                    statement,
                    base,
                    group_column,
                    value_column,
                    group_key,
                    projection,
                )
            )
        if (
            len(selection_rows) != 2
            or len({row[2] for row in selection_rows}) != 1
            or len({row[3] for row in selection_rows}) != 1
            or len({row[4] for row in selection_rows}) != 2
        ):
            return None, "pandas-source-closure"
        operand_rows: list[tuple[PandasOperandProjection, ast.Assign, ast.Assign | None]] = []
        for statement, _base, _group_column, _value_column, group_key, projection in selection_rows:
            base_name = cast(ast.Name, statement.targets[0]).id
            operand_name = base_name
            projection_statement: ast.Assign | None = None
            final_projection = projection
            if projection == "series":
                aliases = [
                    item
                    for item in body
                    if isinstance(item, ast.Assign)
                    and len(item.targets) == 1
                    and isinstance(item.targets[0], ast.Name)
                    and isinstance(item.value, ast.Attribute)
                    and item.value.attr == "values"
                    and isinstance(item.value.value, ast.Name)
                    and item.value.value.id == base_name
                ]
                if len(aliases) > 1:
                    return None, "pandas-source-closure"
                if aliases:
                    projection_statement = aliases[0]
                    operand_name = cast(ast.Name, aliases[0].targets[0]).id
                    final_projection = "values_alias"
            operand_rows.append(
                (
                    PandasOperandProjection(
                        base_series_name=base_name,
                        operand_name=operand_name,
                        group_key=group_key,
                        projection=cast(Any, final_projection),
                        selection_span=_kernel_source_span(statement.value),
                        projection_span=_kernel_source_span(
                            projection_statement or statement.value
                        ),
                    ),
                    statement,
                    projection_statement,
                )
            )
        procedure_matches: list[tuple[ast.Assign, ast.Call, str]] = []
        for statement in body:
            for candidate in (node for node in ast.walk(statement) if isinstance(node, ast.Call)):
                resolved = _kernel_scipy_stats_callable(candidate.func, imports)
                if resolved in _GROUP_BASE_PROCEDURES:
                    if not isinstance(statement, ast.Assign) or statement.value is not candidate:
                        return None, "pandas-source-closure"
                    procedure_matches.append((statement, candidate, resolved))
                elif resolved is not None and resolved not in _DISTRIBUTION_HELPER_METHODS:
                    return None, "pandas-source-closure"
        if len(procedure_matches) != 1:
            return None, "pandas-source-closure"
        procedure_statement, procedure_call, resolved = procedure_matches[0]
        variant = _kernel_group_variant(procedure_call, resolved)
        if variant is None:
            return None, "pandas-source-closure"
        target = procedure_statement.targets[0] if len(procedure_statement.targets) == 1 else None
        if not (
            isinstance(target, ast.Tuple | ast.List)
            and len(target.elts) == 2
            and all(isinstance(item, ast.Name) for item in target.elts)
            and len({cast(ast.Name, item).id for item in target.elts}) == 2
        ):
            return None, "pandas-result-sink"
        result_names = cast(tuple[str, str], tuple(cast(ast.Name, item).id for item in target.elts))
        writer_replay = _kernel_pandas_writer_structure(body, constants)
        if writer_replay is None:
            return None, "pandas-source-closure"
        writer_statement, write_call, writer_handle, writer_path = writer_replay
        projection_map = _kernel_pandas_projection_map(tuple(row[0] for row in operand_rows))
        summary_calls = _kernel_pandas_operand_method_calls(body, projection_map)
        directory_statements = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _kernel_attribute_chain(statement.value.func) == ("os", "makedirs")
        )
        if len(directory_statements) > 1:
            return None, "pandas-result-sink"

        allowed = {
            reader_statement,
            procedure_statement,
            writer_statement,
            *(row[1] for row in operand_rows),
            *(row[2] for row in operand_rows if row[2] is not None),
            *directory_statements,
        }
        for statement in body:
            if statement in allowed:
                continue
            if isinstance(
                statement,
                ast.For
                | ast.AsyncFor
                | ast.While
                | ast.Assert
                | ast.Try
                | ast.TryStar
                | ast.Match
                | ast.With
                | ast.AsyncWith
                | ast.Global
                | ast.Nonlocal
                | ast.If,
            ) or any(
                isinstance(
                    node,
                    ast.Lambda
                    | ast.ListComp
                    | ast.SetComp
                    | ast.DictComp
                    | ast.GeneratorExp
                    | ast.Yield
                    | ast.YieldFrom
                    | ast.Await
                    | ast.Raise,
                )
                for node in ast.walk(statement)
            ):
                return None, "pandas-source-closure"
            if _kernel_pandas_statement_has_operand_mutator(statement, set(projection_map)):
                # The single partition below owns mutation classification.
                continue
            if not isinstance(statement, ast.Assign):
                return None, "pandas-source-closure"
            if not _kernel_pandas_frame_uses_closed(statement, frame_name):
                return None, "pandas-source-closure"

        descriptor = PandasSourceDescriptor(
            package_identity=package_identity,
            import_span=_kernel_source_span(pandas_imports[0]),
            reader_span=_kernel_source_span(reader_statement),
            frame_name=frame_name,
            reader_path=reader_path,
            group_column=selection_rows[0][2],
            value_column=selection_rows[0][3],
            operands=tuple(row[0] for row in operand_rows),
            procedure_variant=variant,
            procedure_call_span=_kernel_source_span(procedure_call),
            procedure_target_span=_kernel_source_span(target),
            procedure_result_names=result_names,
            summary_spans=tuple(
                _kernel_source_span(item) for item in sorted(summary_calls, key=_kernel_source_span)
            ),
            directory_preparation_spans=tuple(
                _kernel_source_span(item) for item in directory_statements
            ),
            writer_span=_kernel_source_span(writer_statement),
            write_span=_kernel_source_span(write_call),
            writer_handle=writer_handle,
            writer_path=writer_path,
            executable_statement_tokens=tuple(
                _kernel_statement_token(statement, index) for index, statement in enumerate(body)
            ),
        )
        key_by_operand = {row[0].operand_name: row[0].group_key for row in operand_rows}
        bindings = tuple(
            (
                position,
                argument.id if isinstance(argument, ast.Name) else "",
                key_by_operand.get(argument.id, "") if isinstance(argument, ast.Name) else "",
            )
            for position, argument in enumerate(procedure_call.args)
        )
        return (
            _KernelPandasSourceReplay(
                descriptor=descriptor,
                body=tuple(body),
                procedure_statement=procedure_statement,
                procedure_call=procedure_call,
                writer_statement=writer_statement,
                write_call=write_call,
                projections=tuple(sorted(projection_map.items())),
                operand_bindings=bindings,
            ),
            None,
        )
    except (IndexError, KeyError, TypeError, ValueError, RecursionError):
        return None, "pandas-source-closure"


def _kernel_without_leading_docstring_statements(body: list[ast.stmt]) -> list[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _kernel_pandas_imports_closed(body: list[ast.stmt], pandas_import: ast.Import) -> bool:
    allowed_imports = {
        ("numpy", "np"),
        ("math", None),
        ("pathlib", None),
        ("csv", None),
        ("os", None),
        ("statistics", None),
    }
    for statement in body:
        if statement is pandas_import:
            continue
        if isinstance(statement, ast.Import):
            if len(statement.names) != 1:
                return False
            alias = statement.names[0]
            if (alias.name, alias.asname) not in allowed_imports:
                return False
        elif isinstance(statement, ast.ImportFrom):
            if statement.level or len(statement.names) != 1:
                return False
            alias = statement.names[0]
            if alias.asname is not None or alias.name == "*":
                return False
            if (statement.module, alias.name) not in {
                ("scipy", "stats"),
                ("pathlib", "Path"),
                ("collections", "defaultdict"),
                ("collections", "OrderedDict"),
                ("__future__", "annotations"),
            } and not (
                statement.module == "statistics"
                and alias.name in {"fmean", "mean", "stdev", "median", "variance"}
            ):
                return False
    if any(
        isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del) and node.id == "pd"
        for node in ast.walk(ast.Module(body=body, type_ignores=[]))
    ):
        return False
    return True


def _kernel_pandas_reader_call(statement: ast.stmt) -> ast.Call | None:
    if not (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, ast.Call)
        and _kernel_attribute_chain(statement.value.func) == ("pd", "read_csv")
    ):
        return None
    return statement.value


def _kernel_pandas_constants(
    body: list[ast.stmt], reader_index: int
) -> tuple[dict[str, object], set[int]]:
    constants: dict[str, object] = {}
    indices: set[int] = set()
    for index, statement in enumerate(body[:reader_index]):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            continue
        value = statement.value
        folded: object | None = None
        if isinstance(value, ast.Constant) and type(value.value) in {str, int, float}:
            folded = value.value
        elif (path := _kernel_path_value(value, constants)) is not None:
            folded = path
        if folded is not None:
            constants[statement.targets[0].id] = folded
            indices.add(index)
    return constants, indices


def _kernel_pandas_selection(
    expression: ast.expr, frame_name: str, constants: dict[str, object]
) -> tuple[ast.expr, str, str, str, str] | None:
    projection = "series"
    base = expression
    if isinstance(base, ast.Attribute) and base.attr == "values":
        projection = "values"
        base = base.value
    elif (
        isinstance(base, ast.Call)
        and isinstance(base.func, ast.Attribute)
        and base.func.attr == "dropna"
        and not base.args
        and not base.keywords
    ):
        projection = "dropna"
        base = base.func.value
    if not (
        isinstance(base, ast.Subscript)
        and isinstance(base.slice, ast.Constant)
        and isinstance(base.slice.value, str)
        and isinstance(base.value, ast.Subscript)
        and isinstance(base.value.value, ast.Name)
        and base.value.value.id == frame_name
        and isinstance(base.value.slice, ast.Compare)
    ):
        return None
    comparison = base.value.slice
    if not (
        len(comparison.ops) == len(comparison.comparators) == 1
        and isinstance(comparison.ops[0], ast.Eq)
        and isinstance(comparison.left, ast.Subscript)
        and isinstance(comparison.left.value, ast.Name)
        and comparison.left.value.id == frame_name
        and isinstance(comparison.left.slice, ast.Constant)
        and isinstance(comparison.left.slice.value, str)
    ):
        return None
    key = _kernel_string_value(comparison.comparators[0], constants)
    if key is None:
        return None
    return (
        base,
        comparison.left.slice.value,
        base.slice.value,
        key,
        projection,
    )


def _kernel_pandas_writer_structure(
    body: list[ast.stmt], constants: dict[str, object]
) -> tuple[ast.With, ast.Call, str, str] | None:
    withs = [item for item in body if isinstance(item, ast.With)]
    writes = [
        node
        for statement in body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write", "writelines", "write_text"}
    ]
    if len(withs) != 1 or len(writes) != 1:
        return None
    statement = withs[0]
    if len(statement.items) != 1 or len(statement.body) != 1:
        return None
    item = statement.items[0]
    if not (
        isinstance(item.context_expr, ast.Call)
        and isinstance(item.context_expr.func, ast.Name)
        and item.context_expr.func.id == "open"
        and len(item.context_expr.args) == 2
        and not item.context_expr.keywords
        and isinstance(item.context_expr.args[1], ast.Constant)
        and item.context_expr.args[1].value == "w"
        and isinstance(item.optional_vars, ast.Name)
        and isinstance(statement.body[0], ast.Expr)
        and isinstance(statement.body[0].value, ast.Call)
    ):
        return None
    write = statement.body[0].value
    handle = item.optional_vars.id
    path = _kernel_path_value(item.context_expr.args[0], constants)
    if not (
        isinstance(path, str)
        and isinstance(write.func, ast.Attribute)
        and isinstance(write.func.value, ast.Name)
        and write.func.value.id == handle
        and write.func.attr == "write"
        and len(write.args) == 1
        and not write.keywords
        and writes[0] is write
    ):
        return None
    return statement, write, handle, path


def _kernel_pandas_projection_map(operands: tuple[PandasOperandProjection, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in operands:
        result[item.base_series_name] = "series"
        result[item.operand_name] = (
            "series" if item.projection in {"series", "dropna"} else "values"
        )
    return result


def _kernel_pandas_operand_method_calls(
    body: list[ast.stmt], projections: dict[str, str]
) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for statement in body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in projections
    )


def _kernel_pandas_frame_uses_closed(statement: ast.stmt, frame_name: str) -> bool:
    parents = {
        child: parent for parent in ast.walk(statement) for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(statement):
        if not (
            isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == frame_name
        ):
            continue
        parent = parents.get(node)
        if (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Name)
            and parent.func.id == "len"
            and parent.args == [node]
            and not parent.keywords
        ) or (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and statement.value is node
        ):
            continue
        return False
    return True


def _kernel_pandas_statement_has_operand_mutator(
    statement: ast.stmt,
    operand_names: set[str],
) -> bool:
    mutators = {
        "drop",
        "dropna",
        "fillna",
        "rename",
        "sort_values",
        "update",
        "insert",
        "pop",
        "set_index",
        "reset_index",
        "clear",
        "extend",
    }
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in operand_names
        and node.func.attr in mutators
        for node in ast.walk(statement)
    )


def _kernel_real_builtin_unbound(tree: ast.Module, name: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store | ast.Del)
            and node.id == name
        ):
            return False
        if isinstance(node, ast.arg) and node.arg == name:
            return False
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node.name == name
        ):
            return False
        if isinstance(node, ast.alias) and (node.asname or node.name.split(".", 1)[0]) == name:
            return False
        if isinstance(node, ast.ExceptHandler) and node.name == name:
            return False
        if isinstance(node, ast.Global | ast.Nonlocal) and name in node.names:
            return False
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Store | ast.Del)
            and isinstance(node.value, ast.Name)
            and node.value.id == "builtins"
            and node.attr == name
        ):
            return False
    return True


def _kernel_pandas_result_sink_closed(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate,
    replay: _KernelPandasSourceReplay,
) -> bool:
    descriptor = replay.descriptor
    expected_descriptor = certificate.obligation.pandas_source
    if expected_descriptor is None:
        return False
    projections = dict(replay.projections)
    if (
        certificate.result_names != descriptor.procedure_result_names
        or certificate.sink_token
        != _kernel_node_token(certificate.source_path, replay.write_call, "selected-sink")
        or descriptor.writer_path != expected_descriptor.writer_path
        or not _kernel_real_builtin_unbound(tree, "open")
    ):
        return False
    for builtin_name in ("len", "float"):
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == builtin_name
            for node in ast.walk(tree)
        ) and not _kernel_real_builtin_unbound(tree, builtin_name):
            return False
    allowed = {
        "series": {"mean", "median", "min", "max", "std"},
        "values": {"mean", "min", "max", "std"},
    }
    for call in _kernel_pandas_operand_method_calls(list(replay.body), projections):
        receiver = cast(ast.Name, cast(ast.Attribute, call.func).value).id
        method = cast(ast.Attribute, call.func).attr
        if method not in allowed[projections[receiver]]:
            return False
        if method == "std":
            valid = (not call.args and not call.keywords) or (
                not call.args
                and len(call.keywords) == 1
                and call.keywords[0].arg == "ddof"
                and isinstance(call.keywords[0].value, ast.Constant)
                and type(call.keywords[0].value.value) is int
                and call.keywords[0].value.value == 1
            )
        else:
            valid = not call.args and not call.keywords
        if not valid:
            return False
    constants = _kernel_pandas_constants(
        [
            item
            for item in _kernel_without_leading_docstring_statements(tree.body)
            if not isinstance(item, ast.Import | ast.ImportFrom)
        ],
        next(
            index
            for index, item in enumerate(
                [
                    value
                    for value in _kernel_without_leading_docstring_statements(tree.body)
                    if not isinstance(value, ast.Import | ast.ImportFrom)
                ]
            )
            if _kernel_pandas_reader_call(item) is not None
        ),
    )[0]
    directory_calls: list[ast.Call] = [
        item.value
        for item in replay.body
        if isinstance(item, ast.Expr)
        and isinstance(item.value, ast.Call)
        and _kernel_attribute_chain(item.value.func) == ("os", "makedirs")
    ]
    if any(
        not _kernel_closed_makedirs(call, constants)
        or not call.args
        or _kernel_path_value(call.args[0], constants) != posixpath.dirname(descriptor.writer_path)
        for call in directory_calls
    ):
        return False
    definitions = {
        item.targets[0].id: item.value
        for item in replay.body
        if isinstance(item, ast.Assign)
        and len(item.targets) == 1
        and isinstance(item.targets[0], ast.Name)
    }
    pending = [
        node.id for node in ast.walk(replay.write_call.args[0]) if isinstance(node, ast.Name)
    ]
    reads: set[str] = set()
    while pending:
        name = pending.pop()
        if name in reads:
            continue
        reads.add(name)
        value = definitions.get(name)
        if value is not None:
            pending.extend(node.id for node in ast.walk(value) if isinstance(node, ast.Name))
    return set(descriptor.procedure_result_names) <= reads


def _kernel_source_span(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", 0),
        getattr(node, "col_offset", 0),
        getattr(node, "end_lineno", 0),
        getattr(node, "end_col_offset", 0),
    )


def _kernel_replay_pandas_group_fact(
    material: FrozenMaterialInput,
    obligation: GroupValueSequenceObligation,
) -> GroupValueSequenceFact | None:
    """Kernel-local raw-byte scanner for the exact Growth-14 material domain."""

    descriptor = obligation.pandas_source
    try:
        if (
            descriptor is None
            or material.path != obligation.path
            or material.content_digest != obligation.content_digest
            or sha256_digest(material.content) != obligation.content_digest
            or obligation.line_model != "pandas_no_terminal_lf"
            or obligation.reader_form != "pandas_read_csv_simple"
            or obligation.encoding != "ascii"
            or obligation.cast_kind != "pandas_numeric"
            or obligation.path != descriptor.reader_path
            or obligation.group_key_column != descriptor.group_column
            or obligation.value_column != descriptor.value_column
        ):
            return None
        content = material.content
        if (
            not content
            or len(content) > MAX_DEPENDENCE_CSV_DOMAIN_BYTES
            or not content.isascii()
            or content[:3] == b"\xef\xbb\xbf"
            or content[0] == 0x0A
            or content[-1] == 0x0A
            or b"\r" in content
            or b"\x00" in content
            or b'"' in content
            or b"\\" in content
        ):
            return None
        records: list[bytes] = []
        record_start = 0
        previous_lf = False
        for offset, byte in enumerate(content):
            if byte != 0x0A:
                previous_lf = False
                continue
            if previous_lf or offset == record_start:
                return None
            records.append(content[record_start:offset])
            record_start = offset + 1
            previous_lf = True
        if not records or record_start >= len(content):
            return None
        records.append(content[record_start:])
        if any(not record for record in records):
            return None
        table = [record.split(b",") for record in records]
        column_count = len(table[0])
        if (
            column_count == 0
            or column_count > MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
            or len(table) - 1 > MAX_DEPENDENCE_CSV_DOMAIN_ROWS
            or len(table) - 1 > MAX_V1_MEMBERSHIPS
            or any(len(row) != column_count for row in table)
            or any(
                len(cell) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES for row in table for cell in row
            )
        ):
            return None
        header = tuple(cell.decode("ascii", errors="strict") for cell in table[0])
        required = {
            obligation.authorized_unit_column,
            obligation.group_key_column,
            obligation.value_column,
        }
        if (
            any(
                not item or item != item.strip() or item in PANDAS_3_0_5_DEFAULT_MISSING_TOKENS
                for item in header
            )
            or len(header) != len(set(header))
            or len({item.casefold() for item in header}) != len(header)
            or len(required) != 3
            or not required <= set(header)
        ):
            return None
        positions = {name: header.index(name) for name in required}
        group_keys = tuple(item.group_key for item in descriptor.operands)
        if (
            len(group_keys) != 2
            or len(set(group_keys)) != 2
            or obligation.predeclared_bucket_keys != group_keys
            or any(
                re.fullmatch(PANDAS_GROUP_LITERAL_PATTERN, item, flags=re.ASCII) is None
                or item.casefold() in PANDAS_GROUP_CASEFOLD_REFUSALS
                for item in group_keys
            )
        ):
            return None
        rows: list[tuple[str, ...]] = []
        all_integer = True
        for raw in table[1:]:
            values = tuple(cell.decode("ascii", errors="strict") for cell in raw)
            if any(
                not value or value != value.strip() or value in PANDAS_3_0_5_DEFAULT_MISSING_TOKENS
                for value in values
            ):
                return None
            group = values[positions[obligation.group_key_column]]
            value = values[positions[obligation.value_column]]
            if (
                group not in group_keys
                or re.fullmatch(PANDAS_VALUE_PATTERN, value, flags=re.ASCII) is None
            ):
                return None
            all_integer = all_integer and "." not in value
            rows.append(values)
        if not rows:
            return None
        grouped: dict[str, list[tuple[int, str, str, str, str]]] = {key: [] for key in group_keys}
        seen_units: set[str] = set()
        for row_number, row in enumerate(rows, start=1):
            group = row[positions[obligation.group_key_column]]
            unit = row[positions[obligation.authorized_unit_column]]
            value = row[positions[obligation.value_column]]
            seen_units.add(unit)
            if len(seen_units) > 5_000:
                return None
            grouped[group].append(
                (
                    row_number,
                    "observation:"
                    + semantic_digest(
                        {
                            "path": obligation.path,
                            "digest": obligation.content_digest,
                            "row": row_number,
                        }
                    ),
                    "unit-key:"
                    + semantic_digest({"column": obligation.authorized_unit_column, "value": unit}),
                    value,
                    repr(float(value)),
                )
            )
        if any(not grouped[key] for key in group_keys):
            return None
        groups = tuple(
            GroupValueSequence(
                group_key=key,
                row_indices=tuple(value[0] for value in grouped[key]),
                observation_ids=tuple(value[1] for value in grouped[key]),
                authorized_unit_ids=tuple(value[2] for value in grouped[key]),
                source_values=tuple(value[3] for value in grouped[key]),
                cast_value_reprs=tuple(value[4] for value in grouped[key]),
            )
            for key in sorted(grouped)
        )
        return GroupValueSequenceFact(
            evidence_id="dependence-growth-group-proof:" + semantic_digest(asdict(obligation)),
            path=obligation.path,
            content_digest=obligation.content_digest,
            file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
            asset_identity_ref=RecordRef(
                material.asset_identity_ref.record_type,
                material.asset_identity_ref.record_id,
            ),
            line_model=obligation.line_model,
            reader_form=obligation.reader_form,
            encoding=obligation.encoding,
            ascii_bytes_proven=True,
            header=header,
            authorized_unit_column=obligation.authorized_unit_column,
            group_key_column=obligation.group_key_column,
            value_column=obligation.value_column,
            cast_kind=obligation.cast_kind,
            row_count=len(rows),
            groups=groups,
            predeclared_bucket_keys=obligation.predeclared_bucket_keys,
            pandas_value_dtype="int64" if all_integer else "float64",
        )
    except (IndexError, KeyError, TypeError, ValueError, UnicodeError, OverflowError):
        return None


def _kernel_replay_group_fact(
    material: FrozenMaterialInput,
    obligation: GroupValueSequenceObligation,
) -> GroupValueSequenceFact | None:
    """Reconstruct the complete ordinary group fact inside the certificate kernel."""

    if (
        material.path != obligation.path
        or material.content_digest != obligation.content_digest
        or sha256_digest(material.content) != obligation.content_digest
        or not obligation.path.lower().endswith(".csv")
        or len(material.content) > MAX_DEPENDENCE_CSV_DOMAIN_BYTES
        or obligation.line_model not in {"splitlines", "csv_newline"}
        or obligation.encoding not in {"utf-8", "ascii"}
        or not obligation.authorized_unit_column
        or obligation.group_key_column == obligation.value_column
        or obligation.group_key_column == obligation.authorized_unit_column
    ):
        return None
    ascii_proven = material.content.isascii()
    try:
        text = material.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if text.startswith("\ufeff") or (obligation.encoding == "ascii" and not ascii_proven):
        return None
    if obligation.line_model == "splitlines":
        if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
            return None
        reader = csv.DictReader(text.splitlines())
    else:
        reader = csv.DictReader(io.StringIO(text, newline=""))
    try:
        header = tuple(reader.fieldnames or ())
        required = {
            obligation.authorized_unit_column,
            obligation.group_key_column,
            obligation.value_column,
        }
        if (
            not header
            or len(header) > MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
            or len(header) != len(set(header))
            or not required <= set(header)
            or any(
                not item or len(item.encode("utf-8")) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
                for item in header
            )
        ):
            return None
        rows: list[dict[str, str]] = []
        for row_index, row in enumerate(reader, start=1):
            if row_index > MAX_DEPENDENCE_CSV_DOMAIN_ROWS or None in row:
                return None
            values = tuple(row.get(column) for column in header)
            if any(value is None or not isinstance(value, str) for value in values):
                return None
            fields = tuple(value for value in values if isinstance(value, str))
            if len(fields) != len(header) or any(
                len(value.encode("utf-8")) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
                for value in fields
            ):
                return None
            rows.append({column: cast(str, row[column]) for column in header})
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None
    if not rows or len(rows) > MAX_V1_MEMBERSHIPS:
        return None

    grouped: dict[str, list[tuple[int, str, str, str, str]]] = {}
    distinct_units: set[str] = set()
    for index, row in enumerate(rows, start=1):
        group = row[obligation.group_key_column]
        value = row[obligation.value_column]
        unit = row[obligation.authorized_unit_column]
        if not group or not unit or not value:
            return None
        distinct_units.add(unit)
        if len(distinct_units) > 5_000:
            return None
        try:
            converted = _kernel_group_cast(value, obligation.cast_kind)
        except (TypeError, ValueError, OverflowError):
            return None
        grouped.setdefault(group, []).append(
            (
                index,
                f"observation:{semantic_digest({'path': obligation.path, 'digest': obligation.content_digest, 'row': index})}",
                f"unit-key:{semantic_digest({'column': obligation.authorized_unit_column, 'value': unit})}",
                value,
                repr(converted),
            )
        )
        if len(grouped) > MAX_V2_GROUPS:
            return None
    observed_keys = set(grouped)
    if obligation.predeclared_bucket_keys and not observed_keys <= set(
        obligation.predeclared_bucket_keys
    ):
        return None
    if obligation.predeclared_bucket_keys and observed_keys != set(
        obligation.predeclared_bucket_keys
    ):
        return None
    groups = tuple(
        GroupValueSequence(
            group_key=group_key,
            row_indices=tuple(item[0] for item in grouped[group_key]),
            observation_ids=tuple(item[1] for item in grouped[group_key]),
            authorized_unit_ids=tuple(item[2] for item in grouped[group_key]),
            source_values=tuple(item[3] for item in grouped[group_key]),
            cast_value_reprs=tuple(item[4] for item in grouped[group_key]),
        )
        for group_key in sorted(grouped)
    )
    return GroupValueSequenceFact(
        evidence_id=f"dependence-growth-group-proof:{semantic_digest(asdict(obligation))}",
        path=obligation.path,
        content_digest=obligation.content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type,
            material.asset_identity_ref.record_id,
        ),
        line_model=obligation.line_model,
        reader_form=obligation.reader_form,
        encoding=obligation.encoding,
        ascii_bytes_proven=ascii_proven,
        header=header,
        authorized_unit_column=obligation.authorized_unit_column,
        group_key_column=obligation.group_key_column,
        value_column=obligation.value_column,
        cast_kind=obligation.cast_kind,
        row_count=len(rows),
        groups=groups,
        predeclared_bucket_keys=obligation.predeclared_bucket_keys,
    )


def _kernel_group_cast(value: str, kind: str) -> float | int:
    if kind == "float":
        return float(value)
    if kind == "int":
        return int(value)
    raise ValueError("unsupported ordinary group cast")


def verify_paired_dependence_certificate(
    certificate: PairedDependenceCertificate,
    *,
    trusted_paired_facts: tuple[PairedValueSequenceFact, ...],
    trusted_material_inputs: tuple[FrozenMaterialInput, ...],
    trusted_authorizations: tuple[HumanMethodAuthorization, ...],
    trusted_procedure_sets: tuple[AuthorizedProcedureSet, ...],
    source_bytes: bytes,
    _failure_reasons: list[str] | None = None,
) -> VerifiedPairedDependenceCertificate | None:
    """Independently verify the direct-row paired-position equations."""

    def refuse(obligation: str) -> VerifiedPairedDependenceCertificate | None:
        if obligation not in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS:
            raise AssertionError(f"unknown kernel refusal obligation: {obligation}")
        if _failure_reasons is not None:
            _failure_reasons.append(obligation)
        return None

    if (
        len(trusted_paired_facts) != 1
        or len(trusted_material_inputs) != 1
        or sha256_digest(source_bytes) != certificate.source_digest
        or certificate.source_extent != (0, len(source_bytes))
        or certificate.resolved_callable != "scipy.stats.ttest_rel"
        or not certificate.authority_record_id
        or not certificate.independent_unit_definition_id
    ):
        return refuse("paired-envelope-binding")
    fact = trusted_paired_facts[0]
    material = trusted_material_inputs[0]
    obligation = certificate.obligation
    if len(trusted_authorizations) != 1 or len(trusted_procedure_sets) != 1:
        return refuse("paired-authority-binding")
    authority = trusted_authorizations[0]
    procedure_set = trusted_procedure_sets[0]
    if (
        authority.record_id != certificate.authority_record_id
        or authority.authority_state != "authorized"
        or authority.analysis_target_ref != certificate.analysis_target_ref
        or authority.procedure_ref != certificate.procedure_ref
        or authority.procedure_ref.record_id != procedure_set.record_id
        or procedure_set.resolved_callables != ("scipy.stats.ttest_rel",)
        or authority.independent_unit_definition_id != certificate.independent_unit_definition_id
        or authority.authorized_key_columns != (obligation.authorized_unit_column,)
        or authority.input_path != obligation.path
        or authority.input_content_digest != obligation.content_digest
    ):
        return refuse("paired-authority-binding")
    try:
        tree = ast.parse(source_bytes.decode("utf-8", errors="strict"))
        compile(tree, certificate.source_path, "exec")
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError, RecursionError):
        return refuse("paired-source-parse")
    if len(source_bytes) > MAX_V2_SOURCE_BYTES or sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return refuse("paired-source-size")
    tree = _kernel_without_docstrings(tree)
    expected_dead = _kernel_expected_dead_constructs(tree)
    if not _kernel_replay_function_bookkeeping(
        tree, replace(certificate, dead_syntactic_construct_tokens=expected_dead)
    ):
        return refuse("paired-alpha-renaming")
    body = _kernel_flattened_module(tree, certificate)
    if body is None:
        return refuse("paired-alpha-renaming")
    imports = _kernel_imports(tree)
    matches = [
        (statement, statement.value)
        for statement in body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and isinstance(statement.value, ast.Call)
        and _kernel_resolved_call(statement.value.func, imports) == "scipy.stats.ttest_rel"
    ]
    all_inferential = [
        call
        for statement in body
        for call in (node for node in ast.walk(statement) if isinstance(node, ast.Call))
        if (_kernel_resolved_call(call.func, imports) or "") in _ALL_PROCEDURES
    ]
    if len(matches) != 1 or len(all_inferential) != 1:
        return refuse("paired-procedure-class")
    procedure, call = matches[0]
    if (
        call is not all_inferential[0]
        or len(call.args) != 2
        or call.keywords
        or not all(isinstance(item, ast.Name) for item in call.args)
        or tuple(cast(ast.Name, item).id for item in call.args)
        != (certificate.left_vector_name, certificate.right_vector_name)
        or cast(ast.Name, procedure.targets[0]).id != certificate.result_name
        or _kernel_node_token(certificate.source_path, call, "procedure-call")
        != certificate.procedure_call_token
    ):
        return refuse("paired-procedure-class")
    replayed_fact = _kernel_replay_paired_fact(material, obligation)
    if replayed_fact is None or fact != replayed_fact:
        return refuse("paired-fact-closure")
    replay = _kernel_paired_vectors(body, certificate, imports)
    if replay is None:
        return refuse("paired-vector-completeness")
    left_column, right_column, left_cast, right_cast = replay
    if (
        (left_column, right_column, left_cast, right_cast)
        != (
            obligation.left_value_column,
            obligation.right_value_column,
            obligation.left_cast_kind,
            obligation.right_cast_kind,
        )
        or left_column == right_column
        or obligation.authorized_unit_column in {left_column, right_column}
    ):
        return refuse("paired-position-equation")
    if len(fact.observations) != fact.row_count or tuple(
        item.row_index for item in fact.observations
    ) != tuple(range(1, fact.row_count + 1)):
        return refuse("paired-position-equation")
    if not _kernel_sink_partition_matches(tree, certificate):
        return refuse("paired-sink-partition")
    counts = Counter(item.authorized_unit_id for item in fact.observations)
    repeated = tuple(sorted(unit for unit, count in counts.items() if count > 1))
    conclusion = "repeated_unit_across_pair_positions" if repeated else "one_pair_position_per_unit"
    if certificate.conclusion != conclusion:
        return refuse("paired-conclusion-equation")
    expected_id = f"dependence-growth-paired-certificate:{semantic_digest({'source_digest': certificate.source_digest, 'fact': fact.evidence_id, 'left': certificate.left_vector_name, 'right': certificate.right_vector_name, 'conclusion': conclusion})}"
    if certificate.certificate_id != expected_id:
        return refuse("paired-certificate-identity")
    if len({item.fresh_name for item in certificate.alpha_renames}) != len(
        certificate.alpha_renames
    ):
        return refuse("paired-alpha-renaming")
    if (
        len(set(certificate.dead_syntactic_construct_tokens))
        != len(certificate.dead_syntactic_construct_tokens)
        or certificate.dead_syntactic_construct_tokens != expected_dead
    ):
        return refuse("paired-dead-construct-completeness")
    return VerifiedPairedDependenceCertificate(
        certificate_id=certificate.certificate_id,
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        resolved_callable="scipy.stats.ttest_rel",
        conclusion=certificate.conclusion,
        fact=fact,
        repeated_unit_ids=repeated,
        left_vector_name=certificate.left_vector_name,
        right_vector_name=certificate.right_vector_name,
        alpha_renames=certificate.alpha_renames,
        operand_slice_statement_tokens=certificate.operand_slice_statement_tokens,
        sink_bound_statement_tokens=certificate.sink_bound_statement_tokens,
        dead_syntactic_construct_tokens=certificate.dead_syntactic_construct_tokens,
    )


def _kernel_replay_paired_fact(
    material: FrozenMaterialInput,
    obligation: PairedValueSequenceObligation,
) -> PairedValueSequenceFact | None:
    """Reconstruct the complete strict-CSV paired fact inside the kernel."""

    if (
        material.path != obligation.path
        or material.content_digest != obligation.content_digest
        or sha256_digest(material.content) != obligation.content_digest
        or obligation.encoding not in {"utf-8", "ascii"}
        or obligation.reader_form != "csv_dictreader_direct_file"
        or obligation.line_model != "csv_newline"
    ):
        return None
    ascii_proven = material.content.isascii()
    try:
        text = material.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if text.startswith("\ufeff") or (obligation.encoding == "ascii" and not ascii_proven):
        return None
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        header = tuple(reader.fieldnames or ())
        required = {
            obligation.authorized_unit_column,
            obligation.left_value_column,
            obligation.right_value_column,
        }
        if (
            not header
            or len(header) != len(set(header))
            or any(not item for item in header)
            or not required <= set(header)
            or len(required) != 3
        ):
            return None
        rows = list(reader)
    except (csv.Error, UnicodeError):
        return None
    if not rows or len(rows) > 10_000 or len(rows) > MAX_V1_MEMBERSHIPS:
        return None
    observations: list[PairedObservation] = []
    for index, row in enumerate(rows, start=1):
        if None in row or any(row.get(column) is None for column in header):
            return None
        unit = row[obligation.authorized_unit_column]
        left_source = row[obligation.left_value_column]
        right_source = row[obligation.right_value_column]
        if not unit or not left_source or not right_source:
            return None
        try:
            left = _kernel_paired_cast(left_source, obligation.left_cast_kind)
            right = _kernel_paired_cast(right_source, obligation.right_cast_kind)
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(left) or not math.isfinite(right):
            return None
        observations.append(
            PairedObservation(
                row_index=index,
                observation_id=f"paired-observation:{semantic_digest({'path': obligation.path, 'digest': obligation.content_digest, 'row': index})}",
                authorized_unit_id=f"unit-key:{semantic_digest({'column': obligation.authorized_unit_column, 'value': unit})}",
                left_source_value=left_source,
                right_source_value=right_source,
                left_cast_value_repr=repr(left),
                right_cast_value_repr=repr(right),
            )
        )
    return PairedValueSequenceFact(
        evidence_id=f"dependence-growth-paired-proof:{semantic_digest(asdict(obligation))}",
        path=obligation.path,
        content_digest=obligation.content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type, material.asset_identity_ref.record_id
        ),
        line_model=obligation.line_model,
        reader_form=obligation.reader_form,
        encoding=obligation.encoding,
        ascii_bytes_proven=ascii_proven,
        header=header,
        authorized_unit_column=obligation.authorized_unit_column,
        left_value_column=obligation.left_value_column,
        right_value_column=obligation.right_value_column,
        left_cast_kind=obligation.left_cast_kind,
        right_cast_kind=obligation.right_cast_kind,
        row_count=len(observations),
        observations=tuple(observations),
    )


def _kernel_paired_cast(value: str, kind: str) -> float | int:
    if kind == "float":
        return float(value)
    if kind == "int":
        return int(value)
    raise ValueError("unsupported paired cast")


def _kernel_expected_dead_constructs(tree: ast.Module) -> tuple[str, ...]:
    functions = {item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)}
    graph = {
        name: {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
        }
        for name, function in functions.items()
    }
    roots = {
        node.func.id
        for statement in tree.body
        if not isinstance(statement, ast.FunctionDef)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    }
    called: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in called:
            continue
        called.add(name)
        pending.extend(graph[name])
    return tuple(sorted(f"dead-function:{name}" for name in set(functions) - called))


def _kernel_paired_vectors(
    body: list[ast.stmt],
    certificate: PairedDependenceCertificate,
    imports: dict[str, str],
) -> tuple[str, str, str, str] | None:
    procedures = [
        statement
        for statement in body
        if isinstance(statement, ast.Assign)
        and isinstance(statement.value, ast.Call)
        and _kernel_resolved_call(statement.value.func, imports) == "scipy.stats.ttest_rel"
    ]
    if len(procedures) != 1:
        return None
    withs = [statement for statement in body if isinstance(statement, ast.With)]
    if len(withs) != 1 or len(withs[0].items) != 1 or len(withs[0].body) != 1:
        return None
    with_statement = withs[0]
    loop = with_statement.body[0]
    if not isinstance(loop, ast.For) or not isinstance(loop.target, ast.Name) or loop.orelse:
        return None
    if not (
        isinstance(loop.iter, ast.Call)
        and _kernel_resolved_call(loop.iter.func, imports) == "csv.DictReader"
        and len(loop.iter.args) == 1
        and not loop.iter.keywords
    ):
        return None
    names = (certificate.left_vector_name, certificate.right_vector_name)
    for name in names:
        definitions = [
            statement
            for statement in body[: body.index(with_statement)]
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
            and isinstance(statement.value, ast.List)
            and not statement.value.elts
        ]
        if len(definitions) != 1:
            return None
    if len(loop.body) != 2:
        return None
    values: dict[str, tuple[str, str]] = {}
    for statement in loop.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            return None
        append = statement.value
        if not (
            isinstance(append.func, ast.Attribute)
            and isinstance(append.func.value, ast.Name)
            and append.func.value.id in names
            and append.func.attr == "append"
            and len(append.args) == 1
            and not append.keywords
            and isinstance(append.args[0], ast.Call)
            and isinstance(append.args[0].func, ast.Name)
            and append.args[0].func.id in {"float", "int"}
            and len(append.args[0].args) == 1
            and not append.args[0].keywords
        ):
            return None
        column = _kernel_row_column(append.args[0].args[0], loop.target.id)
        if column is None or append.func.value.id in values:
            return None
        values[append.func.value.id] = (column, append.args[0].func.id)
    if set(values) != set(names):
        return None
    return (
        values[names[0]][0],
        values[names[1]][0],
        values[names[0]][1],
        values[names[1]][1],
    )


def verify_count_dependence_certificate(
    certificate: CountDependenceCertificate,
    *,
    trusted_count_facts: tuple[CountProcedureFact, ...],
    trusted_authorizations: tuple[HumanMethodAuthorization, ...],
    source_bytes: bytes,
    _failure_reasons: list[str] | None = None,
) -> VerifiedCountDependenceCertificate | None:
    """Replay symbolic count obligations and recompute every row set in-kernel."""

    def refuse(obligation: str) -> VerifiedCountDependenceCertificate | None:
        if obligation not in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS:
            raise AssertionError(f"unknown kernel refusal obligation: {obligation}")
        if _failure_reasons is not None:
            _failure_reasons.append(obligation)
        return None

    if (
        len(trusted_count_facts) != 1
        or len(trusted_authorizations) != 1
        or sha256_digest(source_bytes) != certificate.source_digest
        or certificate.source_extent != (0, len(source_bytes))
        or certificate.resolved_callable
        not in {"scipy.stats.binomtest", "scipy.stats.fisher_exact"}
    ):
        return refuse("envelope-binding")
    fact = trusted_count_facts[0]
    authority = trusted_authorizations[0]
    obligation = certificate.obligation
    if (
        authority.record_type != "human_method_authorization"
        or authority.authority_state != "authorized"
        or authority.record_id != certificate.authority_record_id
        or authority.analysis_target_ref != certificate.analysis_target_ref
        or authority.procedure_ref != certificate.procedure_ref
        or authority.independent_unit_definition_id != certificate.independent_unit_definition_id
        or authority.authorized_key_columns != (obligation.authorized_unit_column,)
        or authority.input_path != obligation.path
        or authority.input_content_digest != obligation.content_digest
    ):
        return refuse("authority-binding")
    if (
        fact.evidence_id != f"dependence-growth-count-proof:{semantic_digest(asdict(obligation))}"
        or fact.path != obligation.path
        or fact.content_digest != obligation.content_digest
        or fact.line_model != obligation.line_model
        or fact.reader_form != obligation.reader_form
        or fact.encoding != obligation.encoding
        or fact.authorized_unit_column != obligation.authorized_unit_column
        or fact.row_count <= 0
        or fact.row_count != len(fact.rows)
        or len(fact.header) != len(set(fact.header))
        or any(not item for item in fact.header)
        or fact.authorized_unit_column not in fact.header
        or (fact.encoding == "ascii" and not fact.ascii_bytes_proven)
    ):
        return refuse("count-fact-closure")
    if tuple(row.row_index for row in fact.rows) != tuple(range(1, fact.row_count + 1)):
        return refuse("count-fact-closure")
    for row in fact.rows:
        values = dict(row.values)
        if (
            tuple(values) != fact.header
            or len(values) != len(row.values)
            or values[fact.authorized_unit_column] == ""
            or row.observation_id
            != "observation:"
            + semantic_digest(
                {
                    "path": fact.path,
                    "digest": fact.content_digest,
                    "row": row.row_index,
                }
            )
            or row.authorized_unit_id
            != "unit-key:"
            + semantic_digest(
                {
                    "column": fact.authorized_unit_column,
                    "value": values[fact.authorized_unit_column],
                }
            )
        ):
            return refuse("count-fact-closure")
    for group in obligation.group_domains:
        if (
            group.group_key_column not in fact.header
            or not group.predeclared_bucket_keys
            or len(group.predeclared_bucket_keys) != len(set(group.predeclared_bucket_keys))
            or any(
                dict(row.values)[group.group_key_column] not in group.predeclared_bucket_keys
                for row in fact.rows
            )
        ):
            return refuse("count-set-equations")
    expected_universe = _kernel_matching_rows(fact, obligation.universe_atoms)
    if tuple(fact.universe_row_indices) != expected_universe:
        return refuse("count-set-equations")
    if len(fact.operands) != len(obligation.operands):
        return refuse("count-fact-closure")
    by_identity = {(item.operand_id, item.position): item for item in fact.operands}
    if len(by_identity) != len(fact.operands):
        return refuse("count-fact-closure")
    for operand in obligation.operands:
        proof = by_identity.get((operand.operand_id, operand.position))
        if proof is None:
            return refuse("count-fact-closure")
        expected_rows = _kernel_matching_rows(
            fact, (*operand.domain_atoms, *operand.predicate_atoms)
        )
        expected_domain_rows = _kernel_matching_rows(fact, operand.domain_atoms)
        rows_by_index = {row.row_index: row for row in fact.rows}
        if (
            proof.row_indices != expected_rows
            or proof.cardinality != len(expected_rows)
            or proof.observation_ids
            != tuple(rows_by_index[index].observation_id for index in expected_rows)
            or proof.authorized_unit_ids
            != tuple(rows_by_index[index].authorized_unit_id for index in expected_rows)
            or not set(expected_rows) <= set(expected_domain_rows)
        ):
            return refuse("count-set-equations")
    try:
        tree = ast.parse(source_bytes.decode("utf-8", errors="strict"))
        compile(tree, certificate.source_path, "exec")
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError, RecursionError):
        return refuse("source-parse")
    if sum(1 for _ in ast.walk(tree)) > MAX_V2_AST_NODES:
        return refuse("source-size")
    tree = _kernel_without_docstrings(tree)
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("rename-injectivity")
    if not _kernel_replay_count_claims(tree, certificate):
        return refuse("count-source-semantic-replay")
    if not _kernel_sink_partition_matches(tree, certificate):
        return refuse("sink-partition")

    proofs = {item.position: item for item in fact.operands}
    repeated: set[str] = set()
    if certificate.resolved_callable == "scipy.stats.binomtest":
        if (
            set(proofs) != {0, 1}
            or any(not proofs[position].row_indices for position in (0, 1))
            or not set(proofs[0].row_indices) <= set(proofs[1].row_indices)
        ):
            return refuse("count-subset-partition")
        repeated.update(
            unit for unit, count in Counter(proofs[1].authorized_unit_ids).items() if count > 1
        )
    else:
        if set(proofs) != {0, 1, 2, 3} or not fact.universe_row_indices:
            return refuse("count-subset-partition")
        cell_sets = [set(proofs[index].row_indices) for index in range(4)]
        if any(
            left & right for index, left in enumerate(cell_sets) for right in cell_sets[index + 1 :]
        ) or set().union(*cell_sets) != set(fact.universe_row_indices):
            return refuse("count-subset-partition")
        if not _kernel_fisher_atoms_are_factorial(certificate.obligation.operands):
            return refuse("count-cells-factorial")
        unit_cells: dict[str, set[int]] = {}
        for proof in fact.operands:
            for unit in proof.authorized_unit_ids:
                unit_cells.setdefault(unit, set()).add(proof.position)
        if any(len(cells) > 1 for cells in unit_cells.values()):
            return refuse("count-unit-nonspanning")
        repeated.update(
            unit
            for proof in fact.operands
            for unit, count in Counter(proof.authorized_unit_ids).items()
            if count > 1
        )
    conclusion = "repeated_units" if repeated else "one_observation_per_unit"
    if certificate.conclusion != conclusion:
        return refuse("conclusion-equation")
    if not _kernel_replay_function_bookkeeping(tree, certificate):
        return refuse("dead-construct-completeness")
    expected_id = "dependence-growth-count-certificate:" + semantic_digest(
        {
            "source_digest": certificate.source_digest,
            "fact": fact.evidence_id,
            "procedure": certificate.resolved_callable,
            "conclusion": conclusion,
        }
    )
    if certificate.certificate_id != expected_id:
        return refuse("certificate-identity")
    return VerifiedCountDependenceCertificate(
        certificate_id=certificate.certificate_id,
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        resolved_callable=certificate.resolved_callable,
        conclusion=conclusion,
        fact=fact,
        repeated_unit_ids=tuple(sorted(repeated)),
        alpha_renames=certificate.alpha_renames,
        operand_slice_statement_tokens=certificate.operand_slice_statement_tokens,
        sink_bound_statement_tokens=certificate.sink_bound_statement_tokens,
        dead_syntactic_construct_tokens=certificate.dead_syntactic_construct_tokens,
    )


def _kernel_fisher_atoms_are_factorial(
    operands: tuple[CountOperandObligation, ...],
) -> bool:
    """Independently establish the exact two-column, two-level cell product."""

    if len(operands) != 4:
        return False
    combinations: set[tuple[tuple[str, str], ...]] = set()
    levels: dict[str, set[str]] = {}
    for operand in operands:
        atoms = operand.predicate_atoms
        if (
            len(atoms) != 2
            or any(atom.operator != "eq" for atom in atoms)
            or len({atom.column for atom in atoms}) != 2
        ):
            return False
        combination = tuple(sorted((atom.column, atom.literal) for atom in atoms))
        combinations.add(combination)
        for column, literal in combination:
            levels.setdefault(column, set()).add(literal)
    if len(levels) != 2 or any(len(values) != 2 for values in levels.values()):
        return False
    columns = tuple(sorted(levels))
    expected = {
        tuple(sorted(((columns[0], left), (columns[1], right))))
        for left in levels[columns[0]]
        for right in levels[columns[1]]
    }
    return len(combinations) == 4 and combinations == expected


def _kernel_without_docstrings(tree: ast.Module) -> ast.Module:
    """Independently erase only leading module and function docstrings."""

    normalized = copy.deepcopy(tree)

    def without_leading_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[1:]
        return body

    normalized.body = without_leading_docstring(normalized.body)
    for statement in normalized.body:
        if isinstance(statement, ast.FunctionDef):
            statement.body = without_leading_docstring(statement.body)
    return normalized


def _kernel_matching_rows(
    fact: CountProcedureFact, atoms: tuple[CountPredicateAtom, ...]
) -> tuple[int, ...]:
    matches: list[int] = []
    for row in fact.rows:
        values = dict(row.values)
        if all(
            (values.get(atom.column) == atom.literal)
            if atom.operator == "eq"
            else (values.get(atom.column) != atom.literal)
            for atom in atoms
        ):
            matches.append(row.row_index)
    return tuple(matches)


def _kernel_replay_count_claims(tree: ast.Module, certificate: CountDependenceCertificate) -> bool:
    """Independently reconstruct the symbolic count shapes from source AST."""

    if not _kernel_import_forms_closed(tree) or not _kernel_typing_uses_closed(tree):
        return False
    module_assignment_names = [
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ]
    if len(module_assignment_names) != len(set(module_assignment_names)):
        return False
    imports = _kernel_imports(tree)
    if set(module_assignment_names) & set(imports):
        return False
    constants = _kernel_constants(tree)
    if not _kernel_module_collection_uses_closed(tree, constants):
        return False
    partition = _kernel_partition_body(tree, certificate)
    if partition is None:
        return False
    flattened, _operand_names = partition
    tree = ast.Module(body=flattened, type_ignores=[])
    if not _kernel_count_live_syntax_closed(tree, certificate, imports, constants):
        return False
    if _kernel_count_group_obligations(tree, certificate) != certificate.obligation.group_domains:
        return False
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
    procedures = [
        node
        for node in assignments
        if len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Call)
        and _kernel_callable(node.value.func, imports)
        in {"scipy.stats.binomtest", "scipy.stats.fisher_exact"}
    ]
    if len(procedures) != 1:
        return False
    procedure = procedures[0]
    if not isinstance(procedure.value, ast.Call):
        return False
    call = procedure.value
    assert isinstance(call, ast.Call)
    resolved = _kernel_callable(call.func, imports)
    target = procedure.targets[0]
    assert isinstance(target, ast.Name)
    if (
        resolved != certificate.resolved_callable
        or _kernel_node_token(certificate.source_path, call, "procedure-call")
        != certificate.procedure_call_token
        or _kernel_renamed_name(tree, certificate, procedure, target.id) != certificate.result_name
        or not _kernel_count_options_closed(call, certificate.resolved_callable, constants)
    ):
        return False
    expressions = _kernel_count_call_expressions(call, certificate.resolved_callable, assignments)
    if expressions is None or len(expressions) != len(certificate.obligation.operands):
        return False
    domains = _kernel_count_domains(tree, certificate, constants)
    replayed: list[CountOperandObligation] = []
    for position, (expression, _proposed) in enumerate(
        zip(expressions, certificate.obligation.operands, strict=True)
    ):
        if not isinstance(expression, ast.Name):
            return False
        resolved_name = _kernel_renamed_name(tree, certificate, call, expression.id)
        derivation = _kernel_count_derivation(tree, certificate, resolved_name, domains, constants)
        if derivation is None:
            return False
        domain_kind, domain_atoms, predicate_atoms = derivation
        replayed.append(
            CountOperandObligation(
                operand_id=resolved_name,
                position=position,
                domain_kind=cast(Literal["rows", "group_rows", "filtered_rows"], domain_kind),
                domain_atoms=domain_atoms,
                predicate_atoms=predicate_atoms,
            )
        )
    if tuple(replayed) != certificate.obligation.operands:
        return False
    if certificate.resolved_callable == "scipy.stats.binomtest":
        universe = replayed[1].domain_atoms
    else:
        common = set(replayed[0].domain_atoms)
        for item in replayed[1:]:
            common.intersection_update(item.domain_atoms)
        universe = tuple(atom for atom in replayed[0].domain_atoms if atom in common)
    if universe != certificate.obligation.universe_atoms:
        return False
    if not _kernel_count_reader_matches(tree, certificate, constants):
        return False
    return _kernel_count_sink_matches(tree, certificate, constants)


def _kernel_count_group_obligations(
    tree: ast.Module, certificate: CountDependenceCertificate
) -> tuple[CountGroupDomainObligation, ...]:
    obligations: list[CountGroupDomainObligation] = []
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
        if not _kernel_count_group_loop_allowed(loop, certificate):
            continue
        assert isinstance(loop.target, ast.Name)
        call = cast(ast.Call, cast(ast.Expr, loop.body[0]).value)
        target = cast(ast.Subscript, cast(ast.Attribute, call.func).value)
        column = _kernel_row_column(target.slice, loop.target.id)
        if column is None or not isinstance(target.value, ast.Name):
            return ()
        group_name = _kernel_renamed_name(tree, certificate, target, target.value.id)
        declarations = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and _kernel_renamed_name(tree, certificate, node, node.targets[0].id) == group_name
            and isinstance(node.value, ast.Dict)
        ]
        if len(declarations) != 1:
            return ()
        declaration = declarations[0]
        if not declaration.keys or any(
            not isinstance(key, ast.Constant)
            or not isinstance(key.value, str)
            or not isinstance(value, ast.List)
            or value.elts
            for key, value in zip(declaration.keys, declaration.values, strict=True)
        ):
            return ()
        obligations.append(
            CountGroupDomainObligation(
                group_key_column=column,
                predeclared_bucket_keys=tuple(
                    cast(str, cast(ast.Constant, key).value) for key in declaration.keys
                ),
            )
        )
    return tuple(sorted(obligations))


def _kernel_count_live_syntax_closed(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    imports: dict[str, str],
    constants: dict[str, object],
) -> bool:
    functions = {item.name for item in tree.body if isinstance(item, ast.FunctionDef)}
    operand_names = {item.operand_id for item in certificate.obligation.operands}
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
    procedure_assignments = {
        id(node)
        for node in assignments
        if len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Call)
        and _kernel_callable(node.value.func, imports) in _COUNT_PROCEDURES
    }
    derivation_roots = [
        node
        for node in (*assignments, *(item for item in ast.walk(tree) if isinstance(item, ast.For)))
        if any(
            isinstance(candidate, ast.Name)
            and isinstance(candidate.ctx, ast.Store)
            and _kernel_renamed_name(tree, certificate, candidate, candidate.id) in operand_names
            for candidate in ast.walk(node)
        )
    ]
    used_source_names = {
        candidate.id
        for root in derivation_roots
        for candidate in ast.walk(root)
        if isinstance(candidate, ast.Name) and isinstance(candidate.ctx, ast.Load)
    }
    forbidden = (
        ast.While,
        ast.AsyncFor,
        ast.AsyncWith,
        ast.Try,
        ast.Match,
        ast.SetComp,
        ast.DictComp,
        ast.Raise,
        ast.Assert,
        ast.Yield,
        ast.YieldFrom,
        ast.Await,
        ast.AugAssign,
        ast.AnnAssign,
        ast.NamedExpr,
        ast.Delete,
    )
    if any(isinstance(node, forbidden) for node in ast.walk(tree)):
        return False
    group_domains_used = any(
        item.domain_kind == "group_rows" for item in certificate.obligation.operands
    )
    group_loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and _kernel_count_group_loop_allowed(node, certificate)
    ]
    if (group_domains_used and len(group_loops) != 1) or (not group_domains_used and group_loops):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            entry = isinstance(call.func, ast.Name) and call.func.id in functions
            sink = isinstance(call.func, ast.Attribute) and call.func.attr == "write_text"
            path_prep = _kernel_closed_makedirs(call, constants)
            grouped = any(
                _kernel_count_for_allowed(loop, tree, certificate) and node in set(ast.walk(loop))
                for loop in ast.walk(tree)
                if isinstance(loop, ast.For)
            )
            if not (entry or sink or path_prep or grouped):
                return False
        if isinstance(node, ast.If) and not _kernel_main_guard(node):
            if not any(
                _kernel_count_for_allowed(loop, tree, certificate) and node in set(ast.walk(loop))
                for loop in ast.walk(tree)
                if isinstance(loop, ast.For)
            ):
                return False
        if isinstance(node, ast.Call):
            resolved = _kernel_callable(node.func, imports)
            if resolved in _COUNT_PROCEDURES:
                continue
            if isinstance(node.func, ast.Name) and node.func.id in functions | {
                "Path",
                "list",
                "len",
                "sum",
                "str",
            }:
                continue
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and imports.get(node.func.value.id) == "csv"
                    and node.func.attr == "DictReader"
                ):
                    continue
                if node.func.attr in {"open", "read_text", "splitlines", "write_text"}:
                    continue
                if node.func.attr == "append":
                    continue
            if _kernel_path_value(node, constants) is not None or _kernel_closed_makedirs(
                node, constants
            ):
                continue
            return False
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                return False
            value = node.value
            renamed_target = _kernel_renamed_name(tree, certificate, node, node.targets[0].id)
            if node.targets[0].id in constants:
                continue
            if (
                isinstance(value, ast.Constant)
                and value.value == 0
                and renamed_target in operand_names
            ):
                continue
            if (
                isinstance(value, ast.Dict)
                and value.keys
                and all(
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(item, ast.List)
                    and not item.elts
                    for key, item in zip(value.keys, value.values, strict=True)
                )
            ) and any(item.domain_kind == "group_rows" for item in certificate.obligation.operands):
                continue
            if isinstance(value, ast.List) and any(
                isinstance(call.func, ast.Attribute | ast.Name)
                and _kernel_callable(call.func, imports) == "scipy.stats.fisher_exact"
                and len(call.args) == 1
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id == node.targets[0].id
                for call in ast.walk(tree)
                if isinstance(call, ast.Call)
            ):
                continue
            if isinstance(value, ast.ListComp) and node.targets[0].id in used_source_names:
                continue
            if id(node) in procedure_assignments:
                continue
            if (
                renamed_target in operand_names
                and isinstance(value, ast.Call)
                and (isinstance(value.func, ast.Name) and value.func.id in {"list", "len", "sum"})
            ):
                continue
            if _kernel_is_reader_assignment(node):
                continue
            return False
        if isinstance(node, ast.For):
            if not _kernel_count_for_allowed(node, tree, certificate):
                return False
    return bool(certificate.procedure_call_token and certificate.sink_token)


def _kernel_count_for_allowed(
    loop: ast.For, tree: ast.Module, certificate: CountDependenceCertificate
) -> bool:
    if not isinstance(loop.target, ast.Name) or loop.orelse:
        return False
    operand_names = {item.operand_id for item in certificate.obligation.operands}
    stored = {
        _kernel_renamed_name(tree, certificate, node, node.id)
        for node in ast.walk(loop)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    if stored & operand_names:
        return bool(
            len(loop.body) == 1
            and isinstance(loop.body[0], ast.If)
            and not loop.body[0].orelse
            and len(loop.body[0].body) == 1
            and isinstance(loop.body[0].body[0], ast.AugAssign)
            and isinstance(loop.body[0].body[0].target, ast.Name)
            and _kernel_renamed_name(
                tree,
                certificate,
                loop.body[0].body[0],
                loop.body[0].body[0].target.id,
            )
            in operand_names
            and isinstance(loop.body[0].body[0].op, ast.Add)
            and isinstance(loop.body[0].body[0].value, ast.Constant)
            and type(loop.body[0].body[0].value.value) is int
            and loop.body[0].body[0].value.value == 1
        )
    return _kernel_count_group_loop_allowed(loop, certificate)


def _kernel_count_group_loop_allowed(
    loop: ast.For, certificate: CountDependenceCertificate
) -> bool:
    if not isinstance(loop.target, ast.Name):
        return False
    columns = {
        atom.column
        for item in certificate.obligation.operands
        if item.domain_kind == "group_rows"
        for atom in item.domain_atoms
    }
    return bool(
        columns
        and len(loop.body) == 1
        and isinstance(loop.body[0], ast.Expr)
        and isinstance(loop.body[0].value, ast.Call)
        and isinstance(loop.body[0].value.func, ast.Attribute)
        and loop.body[0].value.func.attr == "append"
        and len(loop.body[0].value.args) == 1
        and not loop.body[0].value.keywords
        and isinstance(loop.body[0].value.args[0], ast.Name)
        and loop.body[0].value.args[0].id == loop.target.id
        and isinstance(loop.body[0].value.func.value, ast.Subscript)
        and _kernel_row_column(loop.body[0].value.func.value.slice, loop.target.id) in columns
    )


def _kernel_count_options_closed(
    call: ast.Call, resolved: str, constants: dict[str, object]
) -> bool:
    keywords = {item.arg: item.value for item in call.keywords if item.arg is not None}
    if len(keywords) != len(call.keywords):
        return False
    alternative = keywords.pop("alternative", None)
    if alternative is not None and not (
        isinstance(alternative, ast.Constant) and alternative.value == "two-sided"
    ):
        return False
    if resolved == "scipy.stats.binomtest":
        if len(call.args) not in {2, 3} or set(keywords) - {"p"}:
            return False
        if len(call.args) == 3 and "p" in keywords:
            return False
        p_value = call.args[2] if len(call.args) == 3 else keywords.get("p")
        if p_value is not None and _kernel_numeric_constant(p_value, constants) is None:
            return False
        return True
    return len(call.args) == 1 and not keywords


def _kernel_count_call_expressions(
    call: ast.Call, resolved: str, assignments: list[ast.Assign]
) -> tuple[ast.expr, ...] | None:
    if resolved == "scipy.stats.binomtest":
        return tuple(call.args[:2])
    table: ast.expr = call.args[0]
    if isinstance(table, ast.Name):
        matches = [
            item.value
            for item in assignments
            if len(item.targets) == 1
            and isinstance(item.targets[0], ast.Name)
            and item.targets[0].id == table.id
        ]
        if len(matches) != 1:
            return None
        table = matches[0]
    if not (
        isinstance(table, ast.List)
        and len(table.elts) == 2
        and all(isinstance(row, ast.List) and len(row.elts) == 2 for row in table.elts)
    ):
        return None
    return tuple(cell for row in table.elts if isinstance(row, ast.List) for cell in row.elts)


def _kernel_count_domains(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    constants: dict[str, object],
) -> dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]]:
    domains: dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]] = {}
    for assignment in (node for node in ast.walk(tree) if isinstance(node, ast.Assign)):
        if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
            continue
        target = _kernel_renamed_name(tree, certificate, assignment, assignment.targets[0].id)
        if _kernel_is_reader_assignment(assignment):
            domains[target] = ("rows", (), 0)
    changed = True
    while changed:
        changed = False
        for assignment in (node for node in ast.walk(tree) if isinstance(node, ast.Assign)):
            if (
                len(assignment.targets) != 1
                or not isinstance(assignment.targets[0], ast.Name)
                or not isinstance(assignment.value, ast.ListComp)
            ):
                continue
            target = _kernel_renamed_name(tree, certificate, assignment, assignment.targets[0].id)
            if target in domains:
                continue
            comp = assignment.value
            if (
                len(comp.generators) != 1
                or comp.generators[0].is_async
                or len(comp.generators[0].ifs) != 1
                or not isinstance(comp.generators[0].target, ast.Name)
                or not isinstance(comp.elt, ast.Name)
                or comp.elt.id != comp.generators[0].target.id
            ):
                continue
            source = _kernel_count_domain_expr(
                tree, certificate, comp.generators[0].iter, domains, constants
            )
            atoms = _kernel_count_predicate(comp.generators[0].ifs[0], comp.generators[0].target.id)
            if source is None or source[2] != 0 or atoms is None:
                continue
            domains[target] = ("filtered_rows", (*source[1], *atoms), 1)
            changed = True
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
        if not (
            isinstance(loop.target, ast.Name)
            and len(loop.body) == 1
            and isinstance(loop.body[0], ast.Expr)
            and isinstance(loop.body[0].value, ast.Call)
        ):
            continue
        call = loop.body[0].value
        if not (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "append"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == loop.target.id
            and isinstance(call.func.value, ast.Subscript)
            and isinstance(call.func.value.value, ast.Name)
        ):
            continue
        column = _kernel_row_column(call.func.value.slice, loop.target.id)
        if column is not None:
            group_name = _kernel_renamed_name(tree, certificate, call, call.func.value.value.id)
            declarations = [
                item.value
                for item in ast.walk(tree)
                if isinstance(item, ast.Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], ast.Name)
                and _kernel_renamed_name(tree, certificate, item, item.targets[0].id) == group_name
                and isinstance(item.value, ast.Dict)
                and item.value.keys
                and all(
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.List)
                    and not value.elts
                    for key, value in zip(item.value.keys, item.value.values, strict=True)
                )
            ]
            if len(declarations) == 1:
                domains[f"__group__:{group_name}:{column}"] = ("group_rows", (), 0)
    return domains


def _kernel_is_reader_assignment(assignment: ast.Assign) -> bool:
    value = assignment.value
    return bool(
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "list"
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Call)
        and isinstance(value.args[0].func, ast.Attribute)
        and value.args[0].func.attr == "DictReader"
    )


def _kernel_count_domain_expr(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    expression: ast.expr,
    domains: dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]],
    constants: dict[str, object],
) -> tuple[str, tuple[CountPredicateAtom, ...], int] | None:
    if isinstance(expression, ast.Name):
        name = _kernel_renamed_name(tree, certificate, expression, expression.id)
        return domains.get(name)
    if isinstance(expression, ast.Subscript) and isinstance(expression.value, ast.Name):
        group_name = _kernel_renamed_name(tree, certificate, expression, expression.value.id)
        key = _kernel_string_value(expression.slice, constants)
        candidates = [
            (token, domain)
            for token, domain in domains.items()
            if token.startswith(f"__group__:{group_name}:")
        ]
        if key is None or len(candidates) != 1:
            return None
        token, domain = candidates[0]
        return (
            domain[0],
            (CountPredicateAtom(token.rsplit(":", 1)[1], "eq", key),),
            0,
        )
    return None


def _kernel_count_derivation(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    name: str,
    domains: dict[str, tuple[str, tuple[CountPredicateAtom, ...], int]],
    constants: dict[str, object],
) -> tuple[str, tuple[CountPredicateAtom, ...], tuple[CountPredicateAtom, ...]] | None:
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and _kernel_renamed_name(tree, certificate, node, node.targets[0].id) == name
    ]
    for assignment in assignments:
        expression = assignment.value
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "len"
            and len(expression.args) == 1
            and not expression.keywords
        ):
            domain = _kernel_count_domain_expr(
                tree, certificate, expression.args[0], domains, constants
            )
            return (domain[0], domain[1], ()) if domain is not None else None
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "sum"
            and len(expression.args) == 1
            and isinstance(expression.args[0], ast.GeneratorExp)
        ):
            generator = expression.args[0]
            if (
                not isinstance(generator.elt, ast.Constant)
                or generator.elt.value != 1
                or len(generator.generators) != 1
                or not isinstance(generator.generators[0].target, ast.Name)
            ):
                return None
            domain = _kernel_count_domain_expr(
                tree, certificate, generator.generators[0].iter, domains, constants
            )
            predicates = (
                _kernel_count_predicate(
                    generator.generators[0].ifs[0], generator.generators[0].target.id
                )
                if len(generator.generators[0].ifs) == 1
                else (() if not generator.generators[0].ifs else None)
            )
            if domain is None or predicates is None:
                return None
            return domain[0], domain[1], predicates
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
        increments = [
            node
            for node in ast.walk(loop)
            if isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and _kernel_renamed_name(tree, certificate, node, node.target.id) == name
        ]
        if len(increments) != 1 or not isinstance(loop.target, ast.Name):
            continue
        if (
            len(loop.body) != 1
            or not isinstance(loop.body[0], ast.If)
            or loop.body[0].orelse
            or len(loop.body[0].body) != 1
            or loop.body[0].body[0] is not increments[0]
        ):
            return None
        domain = _kernel_count_domain_expr(tree, certificate, loop.iter, domains, constants)
        predicates = _kernel_count_predicate(loop.body[0].test, loop.target.id)
        if domain is None or predicates is None:
            return None
        return domain[0], domain[1], predicates
    return None


def _kernel_count_predicate(
    expression: ast.expr, row_name: str
) -> tuple[CountPredicateAtom, ...] | None:
    parts = (
        expression.values
        if isinstance(expression, ast.BoolOp) and isinstance(expression.op, ast.And)
        else [expression]
    )
    result: list[CountPredicateAtom] = []
    for part in parts:
        if not (
            isinstance(part, ast.Compare)
            and len(part.ops) == len(part.comparators) == 1
            and isinstance(part.ops[0], ast.Eq | ast.NotEq)
        ):
            return None
        column = _kernel_row_column(part.left, row_name)
        literal = part.comparators[0]
        if (
            column is None
            or not isinstance(literal, ast.Constant)
            or not isinstance(literal.value, str)
        ):
            return None
        result.append(
            CountPredicateAtom(
                column,
                "eq" if isinstance(part.ops[0], ast.Eq) else "ne",
                literal.value,
            )
        )
    return tuple(result)


def _kernel_count_reader_matches(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    constants: dict[str, object],
) -> bool:
    obligation = certificate.obligation
    paths: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "DictReader"
            and len(node.args) == 1
        ):
            continue
        source = node.args[0]
        if isinstance(source, ast.Name):
            for with_node in (item for item in ast.walk(tree) if isinstance(item, ast.With)):
                for item in with_node.items:
                    if (
                        isinstance(item.optional_vars, ast.Name)
                        and item.optional_vars.id == source.id
                        and isinstance(item.context_expr, ast.Call)
                        and isinstance(item.context_expr.func, ast.Attribute)
                        and item.context_expr.func.attr == "open"
                    ):
                        values = {
                            keyword.arg: keyword.value
                            for keyword in item.context_expr.keywords
                            if keyword.arg is not None
                        }
                        path = _kernel_path_value(item.context_expr.func.value, constants)
                        encoding = _kernel_string_value(values.get("encoding"), constants)
                        if (
                            path is not None
                            and encoding is not None
                            and _kernel_string_value(values.get("newline"), constants) == ""
                        ):
                            paths.append((path, encoding))
        elif (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "splitlines"
            and isinstance(source.func.value, ast.Call)
            and isinstance(source.func.value.func, ast.Attribute)
            and source.func.value.func.attr == "read_text"
        ):
            read = source.func.value
            values = {
                keyword.arg: keyword.value for keyword in read.keywords if keyword.arg is not None
            }
            assert isinstance(read.func, ast.Attribute)
            path = _kernel_path_value(read.func.value, constants)
            encoding = _kernel_string_value(values.get("encoding"), constants)
            if path is not None and encoding is not None:
                paths.append((path, encoding))
    return paths == [(obligation.path, obligation.encoding)]


def _kernel_count_sink_matches(
    tree: ast.Module,
    certificate: CountDependenceCertificate,
    constants: dict[str, object],
) -> bool:
    writes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if len(writes) != 1:
        return False
    write = writes[0]
    if len(write.args) != 1:
        return False
    return (
        _kernel_path_value(cast(ast.Attribute, write.func).value, constants)
        == certificate.obligation.result_path
        and _kernel_node_token(certificate.source_path, write, "selected-sink")
        == certificate.sink_token
    )


def _kernel_node_token(path: str, node: ast.AST, kind: str) -> str:
    return f"{kind}:{semantic_digest({'path': path, 'line': getattr(node, 'lineno', 0), 'column': getattr(node, 'col_offset', 0)})}"


def _kernel_replay_source_claims(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
) -> _KernelSourceReplay | None:
    """Independently replay the bounded grouping, binding, reader, and sink shapes."""

    all_constants = _kernel_constants(tree)
    if not _kernel_module_collection_uses_closed(tree, all_constants):
        return None
    constants = {name: value for name, value in all_constants.items() if isinstance(value, str)}
    if not _kernel_import_forms_closed(tree) or not _kernel_typing_uses_closed(tree):
        return None
    imports = _kernel_imports(tree)
    partition = _kernel_partition_body(tree, certificate)
    if partition is None:
        return None
    flattened, operand_names = partition
    flattened_tree = ast.Module(body=flattened, type_ignores=[])
    if not _kernel_live_syntax_closed(flattened_tree, certificate, fact):
        return None
    appends = [
        node
        for node in ast.walk(flattened_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
    ]
    if len(appends) != 1 or len(appends[0].args) != 1 or appends[0].keywords:
        return None
    append = appends[0]
    loop = next(
        (
            parent
            for parent in ast.walk(flattened_tree)
            if isinstance(parent, ast.For) and append in set(ast.walk(parent))
        ),
        None,
    )
    if loop is None or not isinstance(loop.target, ast.Name):
        return None
    if (
        loop.orelse
        or len(loop.body) != 1
        or not isinstance(loop.body[0], ast.Expr)
        or loop.body[0].value is not append
    ):
        return None
    row_name = loop.target.id
    value = _kernel_row_value(append.args[0], row_name)
    if not isinstance(append.func, ast.Attribute):
        return None
    receiver = append.func.value
    group_name: str | None = None
    key_column: str | None = None
    if (
        isinstance(receiver, ast.Call)
        and isinstance(receiver.func, ast.Attribute)
        and receiver.func.attr == "setdefault"
        and isinstance(receiver.func.value, ast.Name)
        and len(receiver.args) == 2
        and not receiver.keywords
        and isinstance(receiver.args[1], ast.List)
        and not receiver.args[1].elts
    ):
        group_name = receiver.func.value.id
        key_column = _kernel_row_column(receiver.args[0], row_name)
    elif isinstance(receiver, ast.Subscript) and isinstance(receiver.value, ast.Name):
        group_name = receiver.value.id
        key_column = _kernel_row_column(receiver.slice, row_name)
    if group_name is None or (
        value != (fact.value_column, fact.cast_kind)
        or _kernel_renamed_name(flattened_tree, certificate, append, group_name)
        != certificate.group_container_name
        or key_column != fact.group_key_column
    ):
        return None
    declarations = [
        node.value
        for node in ast.walk(flattened_tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and _kernel_renamed_name(flattened_tree, certificate, node, node.targets[0].id)
        == certificate.group_container_name
    ]
    if len(declarations) != 1:
        return None
    declared_kind = (
        "defaultdict_list"
        if isinstance(declarations[0], ast.Call)
        and isinstance(declarations[0].func, ast.Name)
        and imports.get(declarations[0].func.id) == "collections.defaultdict"
        and len(declarations[0].args) == 1
        and isinstance(declarations[0].args[0], ast.Name)
        and declarations[0].args[0].id == "list"
        and not declarations[0].keywords
        else "dict"
        if isinstance(declarations[0], ast.Dict)
        or (
            isinstance(declarations[0], ast.Call)
            and isinstance(declarations[0].func, ast.Name)
            and imports.get(declarations[0].func.id) == "collections.OrderedDict"
            and not declarations[0].args
            and not declarations[0].keywords
        )
        else None
    )
    if declared_kind != certificate.group_container_kind:
        return None

    census = _kernel_group_census(flattened_tree.body, imports, certificate)
    if census is None:
        return None
    procedure_assignments, _helpers = census
    aliases = _kernel_group_aliases(flattened_tree, group_name, constants, fact)
    expected_keys = tuple(item.group_key for item in certificate.operand_bindings)
    expected_shapes: tuple[str, ...] | None = None
    for procedure_assignment in procedure_assignments:
        call = cast(ast.Call, procedure_assignment.value)
        if len(call.args) != len(certificate.operand_bindings):
            return None
        replayed_keys: list[str] = []
        shapes: list[str] = []
        for argument in call.args:
            key = _kernel_group_key(argument, group_name, constants)
            if isinstance(argument, ast.Name):
                key = aliases.get(argument.id, key)
            if key is None:
                return None
            replayed_keys.append(key)
            shapes.append(ast.dump(argument, include_attributes=False))
        if tuple(replayed_keys) != expected_keys:
            return None
        if expected_shapes is None:
            expected_shapes = tuple(shapes)
        elif tuple(shapes) != expected_shapes:
            return None

    writes = [
        node
        for node in ast.walk(flattened_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ]
    if len(writes) != 1:
        return None
    write = writes[0]
    if len(write.args) != 1:
        return None
    reader_claim = _kernel_reader_claim(flattened_tree, constants)
    if (
        reader_claim is None
        or reader_claim[1:]
        != (
            fact.path,
            fact.encoding,
            fact.line_model,
            fact.reader_form,
        )
        or not isinstance(loop.iter, ast.Name)
        or loop.iter.id != reader_claim[0]
    ):
        return None
    guards = _kernel_collect_full_abort_only_guards(
        source_tree=tree,
        body=flattened_tree.body,
        certificate=certificate,
        rows_name=reader_claim[0],
        group_name=group_name,
        procedure_assignments=procedure_assignments,
        operand_names=operand_names,
        sink=write,
    )
    if guards is None:
        return None
    return _KernelSourceReplay(tuple(flattened_tree.body), frozenset(operand_names), guards)


def _kernel_collect_full_abort_only_guards(
    *,
    source_tree: ast.Module,
    body: list[ast.stmt],
    certificate: DependenceGrowthCertificate,
    rows_name: str,
    group_name: str,
    procedure_assignments: tuple[ast.Assign, ...],
    operand_names: set[str],
    sink: ast.Call,
) -> tuple[_KernelGuardReplay, ...] | None:
    if _kernel_abort_only_raise_wall(source_tree):
        return None
    raises = {
        node for statement in body for node in ast.walk(statement) if isinstance(node, ast.Raise)
    }
    guards: list[ast.If] = [
        cast(ast.If, statement)
        for statement in body
        if _kernel_abort_only_guard_statement(statement, allow_not_name=False)
    ]
    if raises != {cast(ast.Raise, guard.body[0]) for guard in guards}:
        return None
    if not guards:
        return () if not certificate.abort_only_guard_tokens else None
    procedure_indices = [body.index(item) for item in procedure_assignments]
    sink_statement = next((item for item in body if sink in set(ast.walk(item))), None)
    if not procedure_indices or sink_statement is None:
        return None
    terminal_index = min(*procedure_indices, body.index(sink_statement))
    operand_role_names: dict[str, set[int]] = {}
    for procedure in procedure_assignments:
        call = cast(ast.Call, procedure.value)
        for position, argument in enumerate(call.args):
            if isinstance(argument, ast.Name):
                operand_role_names.setdefault(argument.id, set()).add(position)
    if any(len(positions) != 1 for positions in operand_role_names.values()):
        return None
    binding_positions = {item.position for item in certificate.operand_bindings}
    replayed: list[_KernelGuardReplay] = []
    for ordinal, guard in enumerate(guards):
        guard_index = body.index(guard)
        names = _kernel_abort_condition_names(guard.test, allow_not_name=False)
        if guard_index >= terminal_index or names is None:
            return None
        roles: list[AbortOnlyGuardNameRole] = []
        for name in names:
            candidates: list[AbortOnlyGuardNameRole] = []
            if name == rows_name:
                candidates.append(AbortOnlyGuardNameRole(name, "row_sequence"))
            if name == group_name:
                candidates.append(AbortOnlyGuardNameRole(name, "group_container"))
            for position in sorted(operand_role_names.get(name, ())):
                if position in binding_positions:
                    candidates.append(AbortOnlyGuardNameRole(name, "procedure_operand", position))
            if (
                len(candidates) != 1
                or name not in operand_names
                or not _kernel_name_bound_before(body, name, guard_index)
            ):
                return None
            roles.append(candidates[0])
        raised = cast(ast.Raise, guard.body[0])
        token = AbortOnlyGuardToken(
            source_path=certificate.source_path,
            source_span=(
                getattr(guard, "lineno", 0),
                getattr(guard, "col_offset", 0),
                getattr(guard, "end_lineno", 0),
                getattr(guard, "end_col_offset", 0),
            ),
            lexical_scope=cast(str, getattr(guard, "_dependence_v2_lexical_scope", "module")),
            call_path_id=cast(str, getattr(guard, "_dependence_v2_call_path_id", "module")),
            guard_ordinal=ordinal,
            condition_ast_digest=semantic_digest(
                {"syntax": ast.dump(guard.test, include_attributes=False)}
            ),
            raise_ast_digest=semantic_digest(
                {"syntax": ast.dump(raised, include_attributes=False)}
            ),
            name_roles=tuple(roles),
        )
        replayed.append(_KernelGuardReplay(token, guard.test))
    tokens = tuple(item.token for item in replayed)
    return tuple(replayed) if tokens == certificate.abort_only_guard_tokens else None


def _kernel_abort_only_raise_wall(tree: ast.Module) -> bool:
    functions = {item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)}
    module_body = _kernel_live_main_body(tree.body)
    module_executable = [item for item in module_body if not isinstance(item, ast.FunctionDef)]
    module_binds_len = _kernel_scope_binds_len(tree)
    path_states: dict[str, set[bool]] = {name: set() for name in functions}
    pending: list[tuple[str, bool]] = []
    for call in _kernel_user_calls(module_executable, set(functions)):
        assert isinstance(call.func, ast.Name)
        pending.append((call.func.id, not _kernel_direct_uncaught_call(call, module_executable)))
    while pending:
        name, obstructed = pending.pop()
        if obstructed in path_states[name]:
            continue
        path_states[name].add(obstructed)
        function = functions[name]
        for call in _kernel_user_calls(function.body, set(functions)):
            assert isinstance(call.func, ast.Name)
            pending.append(
                (
                    call.func.id,
                    obstructed or not _kernel_direct_uncaught_call(call, function.body),
                )
            )

    reachable_raises: set[ast.Raise] = set()
    candidates: list[tuple[ast.If, ast.Module | ast.FunctionDef, bool]] = []
    for statement in module_executable:
        reachable_raises.update(
            node for node in _kernel_scope_nodes(statement) if isinstance(node, ast.Raise)
        )
        if isinstance(statement, ast.If):
            candidates.append((statement, tree, False))
    for name, states in path_states.items():
        if not states:
            continue
        function = functions[name]
        reachable_raises.update(
            node for node in _kernel_scope_nodes(function) if isinstance(node, ast.Raise)
        )
        for statement in function.body:
            if isinstance(statement, ast.If):
                candidates.append((statement, function, True in states))
    supported: set[ast.Raise] = set()
    for guard, scope, obstructed in candidates:
        if obstructed or not _kernel_abort_only_guard_statement(guard, allow_not_name=True):
            continue
        if _kernel_condition_uses_len(guard.test) and (
            module_binds_len
            or (isinstance(scope, ast.FunctionDef) and _kernel_scope_binds_len(scope))
        ):
            continue
        supported.add(cast(ast.Raise, guard.body[0]))
    return supported != reachable_raises


def _kernel_live_main_body(body: list[ast.stmt]) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for statement in body:
        if isinstance(statement, ast.If) and _kernel_main_guard(statement):
            result.extend(statement.body)
        elif (
            isinstance(statement, ast.If)
            and isinstance(statement.test, ast.Constant)
            and not statement.test.value
        ):
            continue
        else:
            result.append(statement)
    return result


def _kernel_scope_nodes(root: ast.AST) -> tuple[ast.AST, ...]:
    nodes: list[ast.AST] = []

    def visit(node: ast.AST, *, root_node: bool = False) -> None:
        nodes.append(node)
        if not root_node and isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda
        ):
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(root, root_node=True)
    return tuple(nodes)


def _kernel_user_calls(body: list[ast.stmt], functions: set[str]) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for statement in body
        for node in _kernel_scope_nodes(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    )


def _kernel_direct_uncaught_call(call: ast.Call, body: list[ast.stmt]) -> bool:
    owner = next((statement for statement in body if call in set(ast.walk(statement))), None)
    if owner is None or any(
        isinstance(node, ast.Try | ast.TryStar) and call in set(ast.walk(node))
        for statement in body
        for node in ast.walk(statement)
    ):
        return False
    if isinstance(owner, ast.Expr) and owner.value is call:
        return True
    if isinstance(owner, ast.Assign) and owner.value is call:
        return True
    if (
        isinstance(owner, ast.Return)
        and owner.value is not None
        and call in set(ast.walk(owner.value))
    ):
        return True
    return bool(
        isinstance(owner, ast.Expr)
        and isinstance(owner.value, ast.Call)
        and isinstance(owner.value.func, ast.Attribute)
        and owner.value.func.attr == "write_text"
        and owner.value.args
        and call in set(ast.walk(owner.value.args[0]))
    )


def _kernel_scope_binds_len(scope: ast.Module | ast.FunctionDef) -> bool:
    if isinstance(scope, ast.FunctionDef):
        arguments = scope.args
        parameters = (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
        if (
            any(item.arg == "len" for item in parameters)
            or (arguments.vararg is not None and arguments.vararg.arg == "len")
            or (arguments.kwarg is not None and arguments.kwarg.arg == "len")
        ):
            return True

    class KernelBindingVisitor(ast.NodeVisitor):
        bound = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node is scope:
                for statement in node.body:
                    self.visit(statement)
            elif node.name == "len":
                self.bound = True

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node.name == "len":
                self.bound = True

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            if node.name == "len":
                self.bound = True

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_Name(self, node: ast.Name) -> None:
            if node.id == "len" and isinstance(node.ctx, ast.Store | ast.Del):
                self.bound = True

        def visit_alias(self, node: ast.alias) -> None:
            if (node.asname or node.name.split(".", 1)[0]) == "len":
                self.bound = True

        def visit_Global(self, node: ast.Global) -> None:
            if "len" in node.names:
                self.bound = True

        def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
            if "len" in node.names:
                self.bound = True

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name == "len":
                self.bound = True
            self.generic_visit(node)

        def visit_comprehension(self, node: ast.comprehension) -> None:
            self.visit(node.target)
            self.visit(node.iter)
            for condition in node.ifs:
                self.visit(condition)

        def visit_MatchAs(self, node: ast.MatchAs) -> None:
            if node.name == "len":
                self.bound = True
            self.generic_visit(node)

        def visit_MatchStar(self, node: ast.MatchStar) -> None:
            if node.name == "len":
                self.bound = True

        def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
            if node.rest == "len":
                self.bound = True
            self.generic_visit(node)

    visitor = KernelBindingVisitor()
    if isinstance(scope, ast.Module):
        for statement in scope.body:
            visitor.visit(statement)
    else:
        visitor.visit(scope)
    return visitor.bound


def _kernel_abort_only_guard_statement(statement: ast.stmt, *, allow_not_name: bool) -> bool:
    if not (
        isinstance(statement, ast.If)
        and not statement.orelse
        and len(statement.body) == 1
        and isinstance(statement.body[0], ast.Raise)
    ):
        return False
    raised = statement.body[0]
    if raised.cause is not None or not isinstance(raised.exc, ast.Call):
        return False
    exception = raised.exc
    return bool(
        isinstance(exception.func, ast.Name)
        and exception.func.id in {"ValueError", "SystemExit"}
        and len(exception.args) == 1
        and not exception.keywords
        and _kernel_abort_condition_names(statement.test, allow_not_name=allow_not_name) is not None
        and _kernel_sink_expression_closed(statement.test, set(), set())
        and _kernel_sink_expression_closed(exception.args[0], set(), set())
    )


def _kernel_abort_condition_names(
    expression: ast.expr, *, allow_not_name: bool
) -> tuple[str, ...] | None:
    if (
        allow_not_name
        and isinstance(expression, ast.UnaryOp)
        and isinstance(expression.op, ast.Not)
        and isinstance(expression.operand, ast.Name)
        and isinstance(expression.operand.ctx, ast.Load)
    ):
        return (expression.operand.id,)
    if isinstance(expression, ast.BoolOp) and isinstance(expression.op, ast.Or):
        names: list[str] = []
        for value in expression.values:
            parsed = _kernel_abort_condition_names(value, allow_not_name=allow_not_name)
            if parsed is None:
                return None
            names.extend(parsed)
        return tuple(dict.fromkeys(names))
    if not (
        isinstance(expression, ast.Compare)
        and len(expression.ops) == len(expression.comparators) == 1
        and isinstance(expression.ops[0], ast.Lt | ast.NotEq)
        and isinstance(expression.comparators[0], ast.Constant)
        and type(expression.comparators[0].value) is int
        and expression.comparators[0].value == 2
        and isinstance(expression.left, ast.Call)
        and isinstance(expression.left.func, ast.Name)
        and expression.left.func.id == "len"
        and len(expression.left.args) == 1
        and not expression.left.keywords
        and isinstance(expression.left.args[0], ast.Name)
        and isinstance(expression.left.args[0].ctx, ast.Load)
    ):
        return None
    return (expression.left.args[0].id,)


def _kernel_condition_uses_len(expression: ast.expr) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"
        for node in ast.walk(expression)
    )


def _kernel_name_bound_before(body: list[ast.stmt], name: str, guard_index: int) -> bool:
    return any(
        isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == name
        for statement in body[:guard_index]
        for node in ast.walk(statement)
    )


def _kernel_abort_only_guard_truth(
    guard: _KernelGuardReplay,
    fact: GroupValueSequenceFact,
    bindings: tuple[Any, ...],
) -> bool | None:
    groups = {item.group_key: item for item in fact.groups}
    binding_by_position = {item.position: item for item in bindings}
    roles = {item.name: item for item in guard.token.name_roles}

    def cardinality(name: str) -> int | None:
        role = roles.get(name)
        if role is None:
            return None
        if role.role_kind == "row_sequence":
            return fact.row_count
        if role.role_kind == "group_container":
            return len(fact.groups)
        if role.role_kind != "procedure_operand" or role.operand_position is None:
            return None
        binding = binding_by_position.get(role.operand_position)
        sequence = groups.get(binding.group_key) if binding is not None else None
        return len(sequence.row_indices) if sequence is not None else None

    def evaluate(expression: ast.expr) -> bool | None:
        if isinstance(expression, ast.BoolOp) and isinstance(expression.op, ast.Or):
            values = [evaluate(value) for value in expression.values]
            if any(value is None for value in values):
                return None
            return any(value is True for value in values)
        names = _kernel_abort_condition_names(expression, allow_not_name=False)
        if names is None or len(names) != 1 or not isinstance(expression, ast.Compare):
            return None
        length = cardinality(names[0])
        if length is None:
            return None
        if isinstance(expression.ops[0], ast.Lt):
            return length < 2
        if isinstance(expression.ops[0], ast.NotEq):
            return length != 2
        return None

    return evaluate(guard.condition)


def _kernel_renamed_name(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate
    | CountDependenceCertificate
    | PairedDependenceCertificate,
    node: ast.AST,
    original: str,
) -> str:
    owner = next(
        (
            function.name
            for function in tree.body
            if isinstance(function, ast.FunctionDef) and node in set(ast.walk(function))
        ),
        None,
    )
    if owner is None:
        return original
    function = next(
        item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == owner
    )
    parameters = [item.arg for item in function.args.args]
    if original in parameters:
        position = parameters.index(original)
        calls = [
            call
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == owner
            and len(call.args) > position
        ]
        if len(calls) == 1 and isinstance(calls[0].args[position], ast.Name):
            argument = calls[0].args[position]
            assert isinstance(argument, ast.Name)
            return _kernel_renamed_name(tree, certificate, calls[0], argument.id)
    matches = [
        item.fresh_name
        for item in certificate.alpha_renames
        if item.function_name == owner and item.original_name == original
    ]
    return matches[0] if len(matches) == 1 else original


def _kernel_string_constants(tree: ast.Module) -> dict[str, str]:
    return {
        name: value for name, value in _kernel_constants(tree).items() if isinstance(value, str)
    }


def _kernel_constants(tree: ast.Module) -> dict[str, object]:
    values: dict[str, object] = {}
    for statement in tree.body:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            continue
        value = statement.value
        if isinstance(value, ast.Constant) and type(value.value) in {str, int, float}:
            values[statement.targets[0].id] = value.value
        elif (
            isinstance(value, ast.Tuple | ast.List)
            and value.elts
            and all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in value.elts
            )
        ):
            items = [cast(str, cast(ast.Constant, item).value) for item in value.elts]
            values[statement.targets[0].id] = (
                tuple(items) if isinstance(value, ast.Tuple) else items
            )
        elif (
            isinstance(value, ast.Dict)
            and value.keys
            and all(
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and isinstance(item, ast.Constant)
                and isinstance(item.value, str)
                for key, item in zip(value.keys, value.values, strict=True)
            )
        ):
            pairs = [
                (
                    cast(str, cast(ast.Constant, key).value),
                    cast(str, cast(ast.Constant, item).value),
                )
                for key, item in zip(value.keys, value.values, strict=True)
            ]
            if len({key for key, _item in pairs}) != len(pairs):
                continue
            values[statement.targets[0].id] = dict(pairs)
        elif isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            folded = _kernel_collection_subscript(values.get(value.value.id), value.slice, values)
            if folded is not None:
                values[statement.targets[0].id] = folded
        elif (path_value := _kernel_path_value(value, values)) is not None:
            values[statement.targets[0].id] = path_value
    return values


def _kernel_constant_expression(value: object) -> ast.expr:
    if isinstance(value, tuple):
        return ast.Tuple(elts=[ast.Constant(item) for item in value], ctx=ast.Load())
    if isinstance(value, list):
        return ast.List(elts=[ast.Constant(item) for item in value], ctx=ast.Load())
    if isinstance(value, dict):
        return ast.Dict(
            keys=[ast.Constant(item) for item in value],
            values=[ast.Constant(item) for item in value.values()],
        )
    return ast.Constant(cast(Any, value))


def _kernel_collection_subscript(
    collection: object, key: ast.expr, constants: dict[str, object]
) -> str | None:
    if isinstance(key, ast.Name):
        key = ast.Constant(cast(Any, constants.get(key.id)))
    if isinstance(collection, tuple | list):
        if not isinstance(key, ast.Constant) or type(key.value) is not int:
            return None
        index = key.value
        return collection[index] if 0 <= index < len(collection) else None
    if isinstance(collection, dict):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return None
        value = collection.get(key.value)
        return value if isinstance(value, str) else None
    return None


def _kernel_module_collection_uses_closed(tree: ast.Module, constants: dict[str, object]) -> bool:
    collections = {
        name: value for name, value in constants.items() if isinstance(value, tuple | list | dict)
    }
    if not collections:
        return True
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in collections
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Subscript) and parent.value is node:
            if _kernel_collection_subscript(collections[node.id], parent.slice, constants) is None:
                return False
            continue
        if isinstance(parent, ast.For | ast.comprehension) and parent.iter is node:
            continue
        if (
            isinstance(parent, ast.Compare)
            and node in parent.comparators
            and any(isinstance(operator, ast.In | ast.NotIn) for operator in parent.ops)
        ):
            continue
        return False
    return True


def _kernel_string_value(expression: ast.expr | None, constants: dict[str, object]) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.Name):
        value = constants.get(expression.id)
        return value if isinstance(value, str) else None
    return None


def _kernel_numeric_constant(
    expression: ast.expr, constants: dict[str, object]
) -> int | float | None:
    if isinstance(expression, ast.Constant) and type(expression.value) in {int, float}:
        return cast(int | float, expression.value)
    if isinstance(expression, ast.Name):
        value = constants.get(expression.id)
        return cast(int | float, value) if type(value) in {int, float} else None
    return None


def _kernel_path_value(expression: ast.expr, constants: dict[str, object]) -> str | None:
    divided = _kernel_path_division_value(expression)
    if divided is not None:
        return divided
    direct = _kernel_string_value(expression, constants)
    if direct is not None:
        return direct
    if (
        isinstance(expression, ast.Call)
        and (
            (isinstance(expression.func, ast.Name) and expression.func.id == "Path")
            or _kernel_attribute_chain(expression.func) == ("pathlib", "Path")
        )
        and len(expression.args) == 1
        and not expression.keywords
    ):
        return _kernel_string_value(expression.args[0], constants)
    if (
        isinstance(expression, ast.Call)
        and _kernel_attribute_chain(expression.func) == ("os", "path", "join")
        and len(expression.args) >= 2
        and not expression.keywords
        and all(
            isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            for argument in expression.args
        )
    ):
        return posixpath.join(
            *(
                str(argument.value)
                for argument in expression.args
                if isinstance(argument, ast.Constant)
            )
        )
    if (
        isinstance(expression, ast.Call)
        and _kernel_attribute_chain(expression.func) == ("os", "path", "dirname")
        and len(expression.args) == 1
        and not expression.keywords
    ):
        path = _kernel_path_value(expression.args[0], constants)
        return posixpath.dirname(path) if path is not None else None
    return None


def _kernel_path_division_value(expression: ast.expr) -> str | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "Path"
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.Constant)
        and isinstance(expression.args[0].value, str)
    ):
        return expression.args[0].value
    if not (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Div)
        and isinstance(expression.right, ast.Constant)
        and isinstance(expression.right.value, str)
    ):
        return None
    left = _kernel_path_division_value(expression.left)
    return posixpath.join(left, expression.right.value) if left is not None else None


def _kernel_attribute_chain(expression: ast.expr) -> tuple[str, ...] | None:
    parts: list[str] = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    return (expression.id, *reversed(parts)) if isinstance(expression, ast.Name) else None


def _kernel_imports(tree: ast.Module) -> dict[str, str]:
    values: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom) and statement.level == 0:
            for alias in statement.names:
                local = alias.asname or alias.name
                values[local] = f"{statement.module}.{alias.name}"
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                values[alias.asname or alias.name.split(".")[0]] = alias.name
    return values


def _kernel_import_forms_closed(tree: ast.Module) -> bool:
    allowed_imports = {
        ("numpy", "np"),
        ("math", None),
        ("pathlib", None),
        ("csv", None),
        ("os", None),
        ("statistics", None),
    }
    future_index = (
        1
        if tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
        else 0
    )
    future_statement = tree.body[future_index] if future_index < len(tree.body) else None
    future_annotations = bool(
        isinstance(future_statement, ast.ImportFrom)
        and future_statement.level == 0
        and future_statement.module == "__future__"
        and len(future_statement.names) == 1
        and future_statement.names[0].name == "annotations"
        and future_statement.names[0].asname is None
    )
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            if len(statement.names) != 1:
                return False
            alias = statement.names[0]
            if (alias.name, alias.asname) not in allowed_imports:
                return False
        elif isinstance(statement, ast.ImportFrom):
            if statement.level or not statement.names:
                return False
            if (
                statement.module in {"__future__", "dataclasses", "scipy"}
                and len(statement.names) != 1
            ):
                return False
            for alias in statement.names:
                if alias.asname is not None or alias.name == "*":
                    return False
                if statement.module == "typing":
                    if not future_annotations:
                        return False
                    continue
                if (statement.module, alias.name) not in {
                    ("__future__", "annotations"),
                    ("dataclasses", "dataclass"),
                    ("pathlib", "Path"),
                    ("scipy", "stats"),
                    ("collections", "defaultdict"),
                    ("collections", "OrderedDict"),
                    *(
                        ("statistics", name)
                        for name in {"fmean", "mean", "stdev", "median", "variance"}
                    ),
                    *(
                        ("scipy.stats", name.rsplit(".", 1)[1])
                        for name in (
                            _GROUP_BASE_PROCEDURES | _COUNT_PROCEDURES | _PAIRED_PROCEDURES
                        )
                    ),
                }:
                    return False
    return True


def _kernel_annotation_nodes(root: ast.AST) -> set[ast.AST]:
    expressions: list[ast.expr] = []
    for node in ast.walk(root):
        if isinstance(node, ast.AnnAssign):
            expressions.append(node.annotation)
        elif isinstance(node, ast.arg) and node.annotation is not None:
            expressions.append(node.annotation)
        elif isinstance(node, ast.FunctionDef) and node.returns is not None:
            expressions.append(node.returns)
    return {node for expression in expressions for node in ast.walk(expression)}


def _kernel_typing_uses_closed(tree: ast.Module) -> bool:
    imports = _kernel_imports(tree)
    typing_names = {name for name, target in imports.items() if target.startswith("typing.")}
    if not typing_names:
        return True
    annotation_nodes = _kernel_annotation_nodes(tree)
    return not any(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id in typing_names
        and node not in annotation_nodes
        for node in ast.walk(tree)
    )


def _kernel_partition_operand_names(
    body: list[ast.stmt],
    procedures: tuple[ast.Assign, ...],
    *,
    excluded_control_statements: frozenset[ast.stmt] = frozenset(),
) -> set[str]:
    """Derive the sole kernel-side operand definition used by the sink partition."""

    definitions: dict[str, list[ast.expr]] = {}
    for statement in body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            definitions.setdefault(statement.targets[0].id, []).append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            definitions.setdefault(statement.target.id, []).append(statement.value)
    operands = {
        node.id
        for procedure in procedures
        for node in ast.walk(procedure.value)
        if isinstance(node, ast.Name)
    }
    operands.update(
        node.id
        for statement in body
        if isinstance(statement, ast.With | ast.For)
        and statement not in excluded_control_statements
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
    )
    changed = True
    while changed:
        changed = False
        for name in tuple(operands):
            values = definitions.get(name)
            if values is None:
                continue
            for value in values:
                for node in ast.walk(value):
                    if isinstance(node, ast.Name) and node.id not in operands:
                        operands.add(node.id)
                        changed = True
        for name, values in definitions.items():
            if name in operands:
                continue
            if any(
                isinstance(value, ast.Subscript)
                and isinstance(value.value, ast.Name)
                and value.value.id in operands
                and not isinstance(value.slice, ast.Slice)
                for value in values
            ):
                operands.add(name)
                changed = True
    return operands


def _kernel_partition_operand_aliases(body: list[ast.stmt], operands: set[str]) -> set[str]:
    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        protected = operands | aliases
        for statement in body:
            target: ast.Name | None = None
            value: ast.expr | None = None
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                target, value = statement.targets[0], statement.value
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                target, value = statement.target, statement.value
            if (
                target is not None
                and isinstance(value, ast.Name)
                and value.id in protected
                and target.id not in protected
            ):
                aliases.add(target.id)
                changed = True
    return aliases


def _kernel_scipy_stats_callable(expression: ast.expr, imports: dict[str, str]) -> str | None:
    parts: list[str] = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    if not isinstance(expression, ast.Name):
        return None
    root = imports.get(expression.id)
    if root is None:
        return None
    value = ".".join((root, *reversed(parts)))
    return value if value.startswith("scipy.stats.") else None


def _kernel_group_variant(call: ast.Call, resolved: str) -> str | None:
    if resolved == "scipy.stats.ttest_ind":
        if len(call.args) != 2 or any(
            item.arg not in {"equal_var", "alternative"} for item in call.keywords
        ):
            return None
        equal_var = True
        for item in call.keywords:
            if item.arg == "equal_var":
                if not isinstance(item.value, ast.Constant) or type(item.value.value) is not bool:
                    return None
                equal_var = bool(item.value.value)
            elif item.arg == "alternative" and not (
                isinstance(item.value, ast.Constant)
                and item.value.value in {"two-sided", "less", "greater"}
            ):
                return None
        return resolved if equal_var else "scipy.stats.ttest_ind:welch"
    if resolved == "scipy.stats.mannwhitneyu":
        if len(call.args) != 2:
            return None
        allowed = {
            "alternative": {"two-sided", "less", "greater"},
            "method": {"auto", "exact", "asymptotic"},
        }
        if any(item.arg not in allowed for item in call.keywords):
            return None
        if any(
            not isinstance(item.value, ast.Constant)
            or not isinstance(item.value.value, str)
            or item.value.value not in allowed[cast(str, item.arg)]
            for item in call.keywords
        ):
            return None
        return resolved
    return None


def _kernel_group_census(
    body: list[ast.stmt],
    imports: dict[str, str],
    certificate: DependenceGrowthCertificate,
) -> tuple[tuple[ast.Assign, ...], tuple[tuple[ast.Assign, str, ast.Call], ...]] | None:
    """Re-derive H-1's ordered census without trusting analyzer classification."""

    parents = {
        child: parent
        for statement in body
        for parent in ast.walk(statement)
        for child in ast.iter_child_nodes(parent)
    }
    procedures: list[ast.Assign] = []
    variants: list[str] = []
    helpers: list[tuple[ast.Assign, str, ast.Call]] = []
    for statement in body:
        for call in (node for node in ast.walk(statement) if isinstance(node, ast.Call)):
            resolved = _kernel_scipy_stats_callable(call.func, imports)
            if resolved is None:
                continue
            if resolved in _GROUP_BASE_PROCEDURES:
                if not (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.value is call
                ):
                    return None
                variant = _kernel_group_variant(call, resolved)
                if variant is None:
                    return None
                procedures.append(statement)
                variants.append(variant)
            elif resolved in _COUNT_PROCEDURES:
                return None
            elif resolved in _DISTRIBUTION_HELPER_METHODS:
                if not (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.value is call
                ):
                    return None
                helpers.append((statement, statement.targets[0].id, call))
            elif not (isinstance(parents.get(call), ast.Attribute) and parents[call] is call.func):
                return None
    if (
        not procedures
        or tuple(variants) != certificate.resolved_callables
        or tuple(
            _kernel_node_token(certificate.source_path, statement.value, "procedure-call")
            for statement in procedures
            if isinstance(statement.value, ast.Call)
        )
        != certificate.procedure_call_tokens
        or tuple(cast(ast.Name, statement.targets[0]).id for statement in procedures)
        != certificate.result_names
    ):
        return None
    helper_targets = {target for _statement, target, _call in helpers}
    if any(
        sum(
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == target
            for statement in body
        )
        != 1
        for target in helper_targets
    ):
        return None
    return tuple(procedures), tuple(helpers)


def _kernel_lower_annotations_for_partition(
    body: list[ast.stmt], operands: set[str]
) -> list[ast.stmt] | None:
    normalized: list[ast.stmt] = []
    for statement in body:
        if not isinstance(statement, ast.AnnAssign):
            normalized.append(statement)
            continue
        if not isinstance(statement.target, ast.Name) or statement.target.id in operands:
            return None
        if statement.value is None:
            continue
        normalized.append(
            ast.copy_location(
                ast.Assign(targets=[copy.deepcopy(statement.target)], value=statement.value),
                statement,
            )
        )
    return normalized


def _kernel_partition_body(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate
    | CountDependenceCertificate
    | PairedDependenceCertificate,
    *,
    pandas_body: list[ast.stmt] | None = None,
    pandas_procedure: ast.Assign | None = None,
    pandas_writer: ast.With | None = None,
    pandas_source_path: str | None = None,
    pandas_package_identity: PandasPackageIdentity | None = None,
    pandas_replay_out: list[_KernelPandasSourceReplay] | None = None,
    pandas_failure_out: list[str] | None = None,
) -> tuple[list[ast.stmt], set[str]] | None:
    pandas_replay: _KernelPandasSourceReplay | None = None
    if pandas_source_path is not None:
        if (
            pandas_package_identity is None
            or pandas_replay_out is None
            or pandas_failure_out is None
            or pandas_body is not None
            or pandas_procedure is not None
            or pandas_writer is not None
        ):
            if pandas_failure_out is not None:
                pandas_failure_out.append("pandas-source-closure")
            return None
        replay, replay_failure = _kernel_pandas_source_replay(
            tree,
            pandas_source_path,
            pandas_package_identity,
        )
        if replay is None:
            pandas_failure_out.append(replay_failure or "pandas-source-closure")
            return None
        pandas_replay = replay
        pandas_replay_out.append(replay)
        pandas_body = list(replay.body)
        pandas_procedure = replay.procedure_statement
        pandas_writer = replay.writer_statement
    pandas_mode = pandas_body is not None
    body: list[ast.stmt]
    if pandas_body is not None:
        if not (
            isinstance(certificate, DependenceGrowthCertificate)
            and pandas_procedure is not None
            and pandas_writer is not None
            and pandas_procedure in pandas_body
            and pandas_writer in pandas_body
        ):
            return None
        body = list(pandas_body)
    else:
        flattened_body = _kernel_flattened_module(tree, certificate)
        if flattened_body is None:
            return None
        body = flattened_body
    imports = _kernel_imports(tree)
    helpers: tuple[tuple[ast.Assign, str, ast.Call], ...] = ()
    procedures: tuple[ast.Assign, ...]
    if pandas_mode:
        assert pandas_procedure is not None
        procedures = (pandas_procedure,)
    elif isinstance(certificate, CountDependenceCertificate):
        procedures = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and _kernel_resolved_call(statement.value.func, imports)
            == certificate.resolved_callable
        )
        if len(procedures) != 1:
            return None
    elif isinstance(certificate, PairedDependenceCertificate):
        procedures = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Call)
            and _kernel_resolved_call(statement.value.func, imports)
            == certificate.resolved_callable
        )
        if len(procedures) != 1:
            return None
    else:
        census = _kernel_group_census(body, imports, certificate)
        if census is None:
            return None
        procedures, helpers = census
    operands = _kernel_partition_operand_names(
        body,
        procedures,
        excluded_control_statements=(
            frozenset({pandas_writer}) if pandas_writer is not None else frozenset()
        ),
    )
    if pandas_replay is not None:
        expected_operand_names = {item.operand_name for item in pandas_replay.descriptor.operands}
        actual_arguments = tuple(
            item.id for item in pandas_replay.procedure_call.args if isinstance(item, ast.Name)
        )
        required_names = {
            pandas_replay.descriptor.frame_name,
            *(item.base_series_name for item in pandas_replay.descriptor.operands),
            *expected_operand_names,
        }
        if (
            len(actual_arguments) != len(pandas_replay.procedure_call.args)
            or len(actual_arguments) != 2
            or set(actual_arguments) != expected_operand_names
            or len(set(actual_arguments)) != 2
            or not required_names <= operands
        ):
            return None
    if _kernel_rebound_operand_names(body, operands):
        return None
    if isinstance(certificate, DependenceGrowthCertificate) and any(
        target in operands for _statement, target, _call in helpers
    ):
        return None
    aliases = _kernel_partition_operand_aliases(body, operands)
    if pandas_mode and aliases:
        return None
    if pandas_mode and any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in operands
        and node.func.attr
        in {
            "drop",
            "dropna",
            "fillna",
            "rename",
            "sort_values",
            "update",
            "insert",
            "pop",
            "set_index",
            "reset_index",
            "clear",
            "extend",
        }
        for statement in body
        for node in ast.walk(statement)
    ):
        return None
    annotation_protected_names = operands | aliases
    normalized = _kernel_lower_annotations_for_partition(body, annotation_protected_names)
    return (normalized, operands) if normalized is not None else None


def _kernel_rebound_operand_names(body: list[ast.stmt], operands: set[str]) -> set[str]:
    """Independently reject every multiply bound partition operand name."""

    def bound_names(target: ast.expr) -> set[str]:
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, ast.List | ast.Tuple):
            return set().union(*(bound_names(item) for item in target.elts))
        if isinstance(target, ast.Starred):
            return bound_names(target.value)
        return set()

    counts: Counter[str] = Counter()
    for statement in body:
        for node in ast.walk(statement):
            targets: tuple[ast.expr, ...] = ()
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
            elif isinstance(node, ast.AnnAssign | ast.AugAssign | ast.NamedExpr):
                targets = (node.target,)
            elif isinstance(node, ast.For | ast.AsyncFor):
                targets = (node.target,)
            elif isinstance(node, ast.With | ast.AsyncWith):
                targets = tuple(
                    item.optional_vars for item in node.items if item.optional_vars is not None
                )
            for target in targets:
                counts.update(bound_names(target) & operands)
    return {name for name, count in counts.items() if count > 1}


def _kernel_live_syntax_closed(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate,
    fact: GroupValueSequenceFact,
) -> bool:
    """Close statement syntax before the dedicated semantic replayers run."""

    if sum(isinstance(node, ast.For) for node in ast.walk(tree)) != 1:
        return False
    if any(
        isinstance(
            node,
            ast.While
            | ast.AsyncFor
            | ast.AsyncWith
            | ast.Try
            | ast.Match
            | ast.SetComp
            | ast.DictComp
            | ast.GeneratorExp
            | ast.Assert
            | ast.Yield
            | ast.YieldFrom
            | ast.Await,
        )
        for node in ast.walk(tree)
    ):
        return False
    if any(
        isinstance(node, ast.ListComp) and not _kernel_reader_copy_comprehension(node)
        for node in ast.walk(tree)
    ):
        return False
    group_originals = {
        item.original_name
        for item in certificate.alpha_renames
        if item.fresh_name == certificate.group_container_name
    }
    group_names = {*group_originals, certificate.group_container_name}
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign | ast.AnnAssign | ast.NamedExpr | ast.Delete):
            return False
    return set(fact.predeclared_bucket_keys) == _kernel_predeclared_keys(tree, group_names)


def _kernel_reader_copy_comprehension(node: ast.ListComp) -> bool:
    """Replay the exact G9-L DictReader shallow-copy materialization premise."""

    return bool(
        len(node.generators) == 1
        and not node.generators[0].is_async
        and not node.generators[0].ifs
        and isinstance(node.generators[0].target, ast.Name)
        and isinstance(node.generators[0].iter, ast.Call)
        and isinstance(node.generators[0].iter.func, ast.Attribute)
        and isinstance(node.generators[0].iter.func.value, ast.Name)
        and node.generators[0].iter.func.value.id == "csv"
        and node.generators[0].iter.func.attr == "DictReader"
        and len(node.generators[0].iter.args) == 1
        and not node.generators[0].iter.keywords
        and isinstance(node.elt, ast.Call)
        and isinstance(node.elt.func, ast.Name)
        and node.elt.func.id == "dict"
        and len(node.elt.args) == 1
        and not node.elt.keywords
        and isinstance(node.elt.args[0], ast.Name)
        and node.elt.args[0].id == node.generators[0].target.id
    )


def _kernel_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == len(test.comparators) == 1
        and isinstance(test.ops[0], ast.Eq)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
        and not node.orelse
    )


def _kernel_call_allowed(
    node: ast.Call,
    functions: set[str],
    group_names: set[str],
    imports: dict[str, str],
    constants: dict[str, object],
) -> bool:
    if _kernel_path_value(node, constants) is not None or _kernel_closed_makedirs(node, constants):
        return True
    if isinstance(node.func, ast.Name):
        return (
            node.func.id
            in functions
            | {"Path", "list", "float", "int", "str", "sorted", "dict", "any", "all", "tuple"}
            or imports.get(node.func.id) in _PROCEDURE_ARITY
        )
    if not isinstance(node.func, ast.Attribute):
        return False
    resolved_stats = _kernel_scipy_stats_callable(node.func, imports)
    if resolved_stats in _DISTRIBUTION_HELPER_METHODS:
        return True
    if isinstance(node.func.value, ast.Name):
        base = node.func.value.id
        if base in group_names and node.func.attr in {"setdefault", "items"}:
            return True
        if imports.get(base) == "csv" and node.func.attr == "DictReader":
            return True
        if (
            imports.get(base) == "scipy.stats"
            and f"scipy.stats.{node.func.attr}" in _PROCEDURE_ARITY
        ):
            return True
        if imports.get(base) == "numpy" and node.func.attr in {"array", "asarray"}:
            return True
        if imports.get(base) == "pathlib" and node.func.attr == "Path":
            return True
        if node.func.attr in {"open", "read_text", "write_text"}:
            return True
    if isinstance(node.func.value, ast.Call) and node.func.attr == "append":
        inner = node.func.value
        return (
            isinstance(inner.func, ast.Attribute)
            and isinstance(inner.func.value, ast.Name)
            and inner.func.value.id in group_names
            and inner.func.attr == "setdefault"
        )
    if isinstance(node.func.value, ast.Subscript) and node.func.attr == "append":
        return (
            isinstance(node.func.value.value, ast.Name) and node.func.value.value.id in group_names
        )
    return (
        node.func.attr == "items"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in group_names
    )


def _kernel_closed_makedirs(node: ast.Call, constants: dict[str, object]) -> bool:
    return bool(
        _kernel_attribute_chain(node.func) == ("os", "makedirs")
        and len(node.args) == 1
        and len(node.keywords) == 1
        and node.keywords[0].arg == "exist_ok"
        and isinstance(node.keywords[0].value, ast.Constant)
        and node.keywords[0].value.value is True
        and _kernel_path_value(node.args[0], constants) is not None
    )


def _kernel_assignment_allowed(
    node: ast.Assign,
    functions: set[str],
    group_names: set[str],
    constants: dict[str, object],
    imports: dict[str, str],
) -> bool:
    if len(node.targets) != 1:
        return False
    target = node.targets[0]
    if isinstance(target, ast.Name) and target.id in constants:
        return True
    if (
        isinstance(target, ast.Name)
        and target.id in group_names
        and isinstance(node.value, ast.Dict)
    ):
        return True
    if isinstance(target, ast.Tuple):
        return (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "sorted"
        )
    if not isinstance(target, ast.Name):
        return False
    if isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name) and node.value.func.id in functions | {"list"}:
            return True
        if _kernel_callable(node.value.func, imports) is not None or (
            _kernel_scipy_stats_callable(node.value.func, imports) in _DISTRIBUTION_HELPER_METHODS
        ):
            return True
    return any(
        _kernel_group_key(node.value, group_name, cast(dict[str, str], constants)) is not None
        for group_name in group_names
    )


def _kernel_predeclared_keys(tree: ast.Module, group_names: set[str]) -> set[str]:
    keys: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in group_names
            and isinstance(node.value, ast.Dict)
        ):
            keys.update(
                item.value
                for item in node.value.keys
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            )
    return keys


def _kernel_callable(expression: ast.expr, imports: dict[str, str]) -> str | None:
    if isinstance(expression, ast.Name):
        value = imports.get(expression.id)
        return value if value in _ALL_PROCEDURES else None
    if isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name):
        base = imports.get(expression.value.id)
        value = f"{base}.{expression.attr}"
        return value if value in _ALL_PROCEDURES else None
    return None


def _kernel_row_column(expression: ast.expr, row_name: str) -> str | None:
    if (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == row_name
        and isinstance(expression.slice, ast.Constant)
        and isinstance(expression.slice.value, str)
    ):
        return expression.slice.value
    return None


def _kernel_row_value(expression: ast.expr, row_name: str) -> tuple[str, str] | None:
    direct = _kernel_row_column(expression, row_name)
    if direct is not None:
        return direct, "none"
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in {"float", "int"}
        and len(expression.args) == 1
        and not expression.keywords
    ):
        column = _kernel_row_column(expression.args[0], row_name)
        if column is not None:
            return column, expression.func.id
    return None


def _kernel_group_key(
    expression: ast.expr, group_name: str, constants: dict[str, str]
) -> str | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and isinstance(expression.func.value, ast.Name)
        and expression.func.value.id == "np"
        and expression.func.attr in {"array", "asarray"}
        and len(expression.args) == 1
    ):
        if any(item.arg != "dtype" for item in expression.keywords):
            return None
        if expression.keywords and not (
            len(expression.keywords) == 1
            and isinstance(expression.keywords[0].value, ast.Name)
            and expression.keywords[0].value.id == "float"
        ):
            return None
        expression = expression.args[0]
    if not (
        isinstance(expression, ast.Subscript)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == group_name
    ):
        return None
    if isinstance(expression.slice, ast.Constant) and isinstance(expression.slice.value, str):
        return expression.slice.value
    if isinstance(expression.slice, ast.Name):
        return constants.get(expression.slice.id)
    return None


def _kernel_group_aliases(
    tree: ast.Module,
    group_name: str,
    constants: dict[str, str],
    fact: GroupValueSequenceFact,
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name):
                key = _kernel_group_key(node.value, group_name, constants)
                if key is not None:
                    aliases[node.targets[0].id] = key
            if (
                isinstance(node.targets[0], ast.Tuple)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "sorted"
                and len(node.value.args) == 1
                and not node.value.keywords
                and isinstance(node.value.args[0], ast.Call)
                and isinstance(node.value.args[0].func, ast.Attribute)
                and isinstance(node.value.args[0].func.value, ast.Name)
                and node.value.args[0].func.value.id == group_name
                and node.value.args[0].func.attr == "items"
                and not node.value.args[0].args
                and not node.value.args[0].keywords
            ):
                keys = sorted(item.group_key for item in fact.groups)
                if len(node.targets[0].elts) != len(keys):
                    return {}
                for index, element in enumerate(node.targets[0].elts):
                    if (
                        not isinstance(element, ast.Tuple)
                        or len(element.elts) != 2
                        or not isinstance(element.elts[1], ast.Name)
                    ):
                        return {}
                    aliases[element.elts[1].id] = keys[index]
    return aliases


def _kernel_reader_claim(
    tree: ast.Module, constants: dict[str, str]
) -> tuple[str, str, str, str, str] | None:
    """Independently replay the complete reader obligation from flattened source."""

    def encoding(expression: ast.expr | None) -> str | None:
        if isinstance(expression, ast.Constant) and expression.value in {"utf-8", "UTF-8"}:
            return "utf-8"
        if isinstance(expression, ast.Constant) and expression.value == "ascii":
            return "ascii"
        return None

    handles: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            call = item.context_expr
            if not (
                isinstance(item.optional_vars, ast.Name)
                and isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "open"
                and not call.args
            ):
                continue
            keywords = {part.arg: part.value for part in call.keywords if part.arg is not None}
            path = _kernel_path_value(call.func.value, cast(dict[str, object], constants))
            opened_encoding = encoding(keywords.get("encoding"))
            if (
                set(keywords) == {"newline", "encoding"}
                and isinstance(keywords["newline"], ast.Constant)
                and keywords["newline"].value == ""
                and path is not None
                and opened_encoding is not None
            ):
                handles[item.optional_vars.id] = (path, opened_encoding)

    matches: list[tuple[str, str, str, str, str]] = []
    for statement in ast.walk(tree):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            continue
        reader_call: ast.expr | None = None
        if (
            isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "list"
            and len(statement.value.args) == 1
            and not statement.value.keywords
        ):
            reader_call = statement.value.args[0]
        elif isinstance(statement.value, ast.ListComp) and _kernel_reader_copy_comprehension(
            statement.value
        ):
            reader_call = statement.value.generators[0].iter
        if not (
            isinstance(reader_call, ast.Call)
            and isinstance(reader_call.func, ast.Attribute)
            and isinstance(reader_call.func.value, ast.Name)
            and reader_call.func.value.id == "csv"
            and reader_call.func.attr == "DictReader"
            and len(reader_call.args) == 1
            and not reader_call.keywords
        ):
            continue
        source = reader_call.args[0]
        if isinstance(source, ast.Name) and source.id in handles:
            path, claimed_encoding = handles[source.id]
            matches.append(
                (
                    statement.targets[0].id,
                    path,
                    claimed_encoding,
                    "csv_newline",
                    "csv_dictreader_file",
                )
            )
            continue
        if not (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "splitlines"
            and not source.args
            and not source.keywords
            and isinstance(source.func.value, ast.Call)
        ):
            continue
        read = source.func.value
        if not (
            isinstance(read.func, ast.Attribute) and read.func.attr == "read_text" and not read.args
        ):
            continue
        keywords = {part.arg: part.value for part in read.keywords if part.arg is not None}
        path = _kernel_path_value(read.func.value, cast(dict[str, object], constants))
        split_encoding = encoding(keywords.get("encoding"))
        if set(keywords) == {"encoding"} and path is not None and split_encoding is not None:
            matches.append(
                (
                    statement.targets[0].id,
                    path,
                    split_encoding,
                    "splitlines",
                    "csv_dictreader_splitlines",
                )
            )
    if len(matches) != 1:
        return None
    match = matches[0]
    current = match[0]
    while True:
        aliases = [
            statement.targets[0].id
            for statement in tree.body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Name)
            and statement.value.id == current
        ]
        if not aliases:
            break
        if len(aliases) != 1:
            return None
        current = aliases[0]
    return (current, *match[1:])


def _kernel_parameter_string(
    tree: ast.Module,
    node: ast.AST,
    name: str,
    constants: dict[str, str],
) -> str | None:
    owner = next(
        (
            function
            for function in tree.body
            if isinstance(function, ast.FunctionDef) and node in set(ast.walk(function))
        ),
        None,
    )
    if owner is None:
        return constants.get(name)
    parameters = [item.arg for item in owner.args.args]
    if name not in parameters:
        return constants.get(name)
    position = parameters.index(name)
    calls = [
        call
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == owner.name
        and len(call.args) > position
    ]
    if len(calls) != 1:
        return None
    argument = calls[0].args[position]
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    if isinstance(argument, ast.Name):
        return _kernel_parameter_string(tree, calls[0], argument.id, constants)
    return None


def _kernel_replay_function_bookkeeping(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate
    | CountDependenceCertificate
    | PairedDependenceCertificate,
) -> bool:
    functions = {item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)}
    imports = _kernel_imports(tree)
    import_names = set(imports)
    typing_names = {name for name, target in imports.items() if target.startswith("typing.")}
    constants = set(_kernel_constants(tree))
    if any(
        isinstance(node, ast.Name) and node.id.startswith("__dependence_v2_")
        for node in ast.walk(tree)
    ):
        return False
    if any(
        not _kernel_function_shape_closed(
            item, import_names, typing_names, constants, set(functions)
        )
        for item in functions.values()
    ):
        return False
    graph = {
        name: {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
        }
        for name, function in functions.items()
    }
    if _kernel_graph_cyclic(graph):
        return False
    roots = {
        node.func.id
        for statement in tree.body
        if not isinstance(statement, ast.FunctionDef)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    }
    user_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in functions
    ]
    for call in user_calls:
        function = functions[cast(ast.Name, call.func).id]
        if (
            call.keywords
            or len(call.args) != len(function.args.args)
            or any(isinstance(item, ast.Starred) for item in call.args)
        ):
            return False
        if any(not _kernel_simple_argument(item, constants) for item in call.args) and any(
            not _kernel_sink_expression_closed(item, set(), set()) for item in call.args
        ):
            return False
    called: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in called:
            continue
        called.add(name)
        pending.extend(graph[name])
    if any(_kernel_graph_depth(root, graph) > 3 for root in roots):
        return False
    sites = _kernel_call_sites(tree, functions)
    expected_pairs: set[tuple[str, str, str, str, tuple[int, int, int, int]]] = set()
    for name, call_path_id, span in sites:
        function = functions[name]
        originals = {item.arg for item in function.args.args}
        originals.update(
            node.id
            for node in ast.walk(function)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        )
        call_number = call_path_id.rsplit(":", 1)[-1]
        expected_pairs.update(
            (
                name,
                call_path_id,
                original,
                f"__dependence_v2_{call_number}_{original}",
                span,
            )
            for original in originals
        )
    actual_pairs = {
        (
            item.function_name,
            item.call_path_id,
            item.original_name,
            item.fresh_name,
            item.call_span,
        )
        for item in certificate.alpha_renames
    }
    caller_visible = (
        {
            node.id
            for statement in tree.body
            for node in ast.walk(statement)
            if isinstance(node, ast.Name)
        }
        | set(functions)
        | import_names
        | constants
    )
    fresh = [item.fresh_name for item in certificate.alpha_renames]
    expected_dead = tuple(sorted(f"dead-function:{name}" for name in set(functions) - called))
    return (
        actual_pairs == expected_pairs
        and len(fresh) == len(set(fresh))
        and not set(fresh) & caller_visible
        and certificate.dead_syntactic_construct_tokens == expected_dead
    )


class _KernelInlineTransformer(ast.NodeTransformer):
    def __init__(self, arguments: dict[str, ast.expr], names: dict[str, str]) -> None:
        self.arguments = arguments
        self.names = names

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.arguments:
            return ast.copy_location(copy.deepcopy(self.arguments[node.id]), node)
        if node.id in self.names:
            return ast.copy_location(ast.Name(self.names[node.id], node.ctx), node)
        return node


def _kernel_simple_argument(expression: ast.expr, constants: set[str]) -> bool:
    return isinstance(expression, ast.Constant) or (
        isinstance(expression, ast.Name)
        and (expression.id in constants or expression.id.isidentifier())
    )


def _kernel_flattened_module(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate
    | CountDependenceCertificate
    | PairedDependenceCertificate,
) -> list[ast.stmt] | None:
    """Independently replay inlining; certificate names are used only after injectivity replay."""

    functions = {item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)}
    constants = _kernel_constants(tree)
    rename_map = {
        (item.function_name, item.call_path_id, item.original_name): item.fresh_name
        for item in certificate.alpha_renames
    }
    counter = 0

    def inline(
        statements: list[ast.stmt], parent: tuple[str, ...], depth: int
    ) -> list[ast.stmt] | None:
        nonlocal counter
        result: list[ast.stmt] = []
        for statement in statements:
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Attribute)
                and statement.value.func.attr == "write_text"
                and statement.value.args
            ):
                sink_result = inline_sink_expression(statement.value.args[0], parent, depth)
                if sink_result is None:
                    return None
                prefix, payload = sink_result
                if prefix or ast.dump(payload, include_attributes=False) != ast.dump(
                    statement.value.args[0], include_attributes=False
                ):
                    sink_statement = copy.deepcopy(statement)
                    assert isinstance(sink_statement, ast.Expr)
                    assert isinstance(sink_statement.value, ast.Call)
                    sink_statement.value.args[0] = payload
                    result.extend(prefix)
                    result.append(sink_statement)
                    continue
            target: ast.expr | None = None
            call: ast.Call | None = None
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                call = statement.value
            elif (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.value, ast.Call)
            ):
                target, call = statement.targets[0], statement.value
            if not (
                call is not None and isinstance(call.func, ast.Name) and call.func.id in functions
            ):
                result.append(copy.deepcopy(statement))
                continue
            if depth >= MAX_V2_INLINE_DEPTH:
                return None
            function = functions[call.func.id]
            if (
                call.keywords
                or len(call.args) != len(function.args.args)
                or any(isinstance(item, ast.Starred) for item in call.args)
            ):
                return None
            has_expression_argument = any(
                not _kernel_simple_argument(item, set(constants)) for item in call.args
            )
            if has_expression_argument and any(
                not _kernel_sink_expression_closed(item, set(), set()) for item in call.args
            ):
                return None
            counter += 1
            path = (*parent, f"{call.func.id}:{counter}")
            path_id = "inline-call-path:" + "/".join(path)
            parameters = [item.arg for item in function.args.args]
            argument_prefix: list[ast.stmt] = []
            arguments: dict[str, ast.expr]
            if has_expression_argument:
                argument_names: list[ast.Name] = []
                for index, item in enumerate(call.args):
                    temporary = f"__dependence_v2_argument_{counter}_{index}"
                    value = (
                        copy.deepcopy(_kernel_constant_expression(constants[item.id]))
                        if isinstance(item, ast.Name) and item.id in constants
                        else copy.deepcopy(item)
                    )
                    argument_prefix.append(ast.Assign([ast.Name(temporary, ast.Store())], value))
                    argument_names.append(ast.Name(temporary, ast.Load()))
                arguments = dict(zip(parameters, argument_names, strict=True))
            else:
                arguments = {
                    name: copy.deepcopy(_kernel_constant_expression(constants[item.id]))
                    if isinstance(item, ast.Name) and item.id in constants
                    else copy.deepcopy(item)
                    for name, item in zip(parameters, call.args, strict=True)
                }
            stored = {
                node.id
                for node in ast.walk(function)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
            }
            originals = [*parameters, *sorted(stored - set(parameters))]
            names = {
                name: rename_map[(function.name, path_id, name)]
                for name in originals
                if (function.name, path_id, name) in rename_map
            }
            if len(names) != len(originals):
                return None
            # Replay module-constant substitution in callee scope before alpha
            # renaming, excluding parameter/local shadows.
            bound_names = set(parameters) | stored
            callee_constants = {
                name: value for name, value in constants.items() if name not in bound_names
            }
            constant_transformer = _KernelConstantTransformer(callee_constants)
            constant_body = [
                constant_transformer.visit(copy.deepcopy(item)) for item in function.body
            ]
            transformer = _KernelInlineTransformer(arguments, names)
            nested = [
                ast.fix_missing_locations(cast(ast.stmt, transformer.visit(item)))
                for item in constant_body
            ]
            for statement in nested:
                _annotate_kernel_guard_context(statement, function.name, path_id)
            return_value: ast.expr | None = None
            nested_return: str | None = None
            if nested and isinstance(nested[-1], ast.Return):
                return_value = cast(ast.Return, nested.pop()).value
            elif (
                nested
                and isinstance(nested[-1], ast.With)
                and nested[-1].body
                and isinstance(nested[-1].body[-1], ast.Return)
            ):
                returned = cast(ast.Return, nested[-1].body.pop())
                if returned.value is not None:
                    nested_return = f"__dependence_v2_{counter}_return"
                    nested[-1].body.append(
                        ast.Assign([ast.Name(nested_return, ast.Store())], returned.value)
                    )
            flattened = inline(nested, path, depth + 1)
            if flattened is None:
                return None
            result.extend(argument_prefix)
            result.extend(flattened)
            if return_value is not None:
                return_result = inline_sink_expression(return_value, path, depth + 1)
                if return_result is None:
                    return None
                return_prefix, return_value = return_result
                result.extend(return_prefix)
            if target is not None:
                value = (
                    ast.Name(nested_return, ast.Load())
                    if nested_return is not None
                    else return_value
                    if return_value is not None
                    else ast.Constant(None)
                )
                result.append(ast.Assign([copy.deepcopy(target)], value))
            elif nested_return is not None:
                result.append(ast.Expr(ast.Name(nested_return, ast.Load())))
            elif return_value is not None:
                result.append(ast.Expr(return_value))
        return result

    def inline_sink_expression(
        expression: ast.expr, parent: tuple[str, ...], depth: int
    ) -> tuple[list[ast.stmt], ast.expr] | None:
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id in functions
        ):
            placeholder = ast.Name("__dependence_v2_sink_placeholder", ast.Store())
            flattened = inline(
                [ast.Assign([placeholder], copy.deepcopy(expression))], parent, depth
            )
            if not flattened or not isinstance(flattened[-1], ast.Assign):
                return None
            final_assignment = flattened.pop()
            assert isinstance(final_assignment, ast.Assign)
            replacement = final_assignment.value
            nested_result = inline_sink_expression(replacement, parent, depth)
            if nested_result is None:
                return None
            nested_prefix, replacement = nested_result
            return [*flattened, *nested_prefix], replacement

        prefix: list[ast.stmt] = []
        normalized = copy.deepcopy(expression)
        for field, value in ast.iter_fields(normalized):
            if isinstance(value, ast.expr):
                nested_result = inline_sink_expression(value, parent, depth)
                if nested_result is None:
                    return None
                nested, replacement = nested_result
                prefix.extend(nested)
                setattr(normalized, field, replacement)
            elif isinstance(value, list):
                replacements: list[object] = []
                for item in value:
                    if isinstance(item, ast.expr):
                        nested_result = inline_sink_expression(item, parent, depth)
                        if nested_result is None:
                            return None
                        nested, replacement = nested_result
                        prefix.extend(nested)
                        replacements.append(replacement)
                    else:
                        replacements.append(item)
                setattr(normalized, field, replacements)
        return prefix, normalized

    executable: list[ast.stmt] = []
    for item in tree.body:
        if isinstance(item, ast.FunctionDef | ast.Import | ast.ImportFrom):
            continue
        if (
            isinstance(item, ast.Assign)
            and len(item.targets) == 1
            and isinstance(item.targets[0], ast.Name)
            and item.targets[0].id in constants
        ):
            continue
        if isinstance(item, ast.If) and _kernel_main_guard(item):
            executable.extend(item.body)
        else:
            executable.append(item)
    flattened = inline(executable, (), 0)
    if flattened is None:
        return None
    _annotate_kernel_module_guard_context(flattened)
    transformer = _KernelConstantTransformer(constants)
    return [
        ast.fix_missing_locations(cast(ast.stmt, transformer.visit(copy.deepcopy(item))))
        for item in flattened
    ]


def _annotate_kernel_guard_context(
    statement: ast.stmt, lexical_scope: str, call_path_id: str
) -> None:
    for node in ast.walk(statement):
        if isinstance(node, ast.If) and any(
            isinstance(child, ast.Raise) for child in ast.walk(node)
        ):
            node.__dict__["_dependence_v2_lexical_scope"] = lexical_scope
            node.__dict__["_dependence_v2_call_path_id"] = call_path_id


def _annotate_kernel_module_guard_context(body: list[ast.stmt]) -> None:
    for statement in body:
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.If)
                and any(isinstance(child, ast.Raise) for child in ast.walk(node))
                and not hasattr(node, "_dependence_v2_lexical_scope")
            ):
                node.__dict__["_dependence_v2_lexical_scope"] = "module"
                node.__dict__["_dependence_v2_call_path_id"] = "module"


class _KernelConstantTransformer(ast.NodeTransformer):
    def __init__(self, constants: dict[str, object]) -> None:
        self.constants = constants

    def visit_Name(self, node: ast.Name) -> ast.expr:
        if isinstance(node.ctx, ast.Load) and node.id in self.constants:
            return ast.copy_location(_kernel_constant_expression(self.constants[node.id]), node)
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
        original_value = node.value
        visited = cast(ast.Subscript, self.generic_visit(node))
        if isinstance(original_value, ast.Name) and original_value.id in self.constants:
            folded = _kernel_collection_subscript(
                self.constants[original_value.id], visited.slice, self.constants
            )
            if folded is not None:
                return ast.copy_location(ast.Constant(folded), node)
        return visited


def _kernel_statement_token(statement: ast.stmt, index: int) -> str:
    return "flattened-statement:" + semantic_digest(
        {"index": index, "syntax": ast.dump(statement, include_attributes=False)}
    )


def _kernel_sink_expression_closed(
    expression: ast.expr,
    operands: set[str],
    scalar_sequences: set[str],
    *,
    pandas_projections: dict[str, str] | None = None,
) -> bool:
    def closed(value: ast.expr) -> bool:
        return _kernel_sink_expression_closed(
            value,
            operands,
            scalar_sequences,
            pandas_projections=pandas_projections,
        )

    if isinstance(expression, ast.Name | ast.Constant):
        return True
    if isinstance(expression, ast.Slice):
        return all(
            item is None or closed(item)
            for item in (expression.lower, expression.upper, expression.step)
        )
    if isinstance(expression, ast.Subscript):
        return (
            (
                not (isinstance(expression.value, ast.Name) and expression.value.id in operands)
                or (
                    isinstance(expression.slice, ast.Slice)
                    and expression.value.id in scalar_sequences
                )
            )
            and closed(expression.value)
            and closed(expression.slice)
        )
    if isinstance(expression, ast.List | ast.Tuple | ast.Set):
        return all(
            not (isinstance(item, ast.Name) and item.id in operands) and closed(item)
            for item in expression.elts
        )
    if isinstance(expression, ast.Dict):
        return all(
            item is None
            or (not (isinstance(item, ast.Name) and item.id in operands) and closed(item))
            for item in (*expression.keys, *expression.values)
        )
    if isinstance(expression, ast.BinOp):
        return closed(expression.left) and closed(expression.right)
    if isinstance(expression, ast.UnaryOp):
        return closed(expression.operand)
    if isinstance(expression, ast.BoolOp):
        return all(closed(item) for item in expression.values)
    if isinstance(expression, ast.Compare):
        return closed(expression.left) and all(closed(item) for item in expression.comparators)
    if isinstance(expression, ast.JoinedStr):
        return all(
            not isinstance(item, ast.FormattedValue)
            or (closed(item.value) and (item.format_spec is None or closed(item.format_spec)))
            for item in expression.values
        )
    if isinstance(expression, ast.IfExp):
        return all(closed(item) for item in (expression.test, expression.body, expression.orelse))
    if not isinstance(expression, ast.Call):
        return False
    helper_chain = _kernel_attribute_chain(expression.func)
    if (
        helper_chain is not None
        and len(helper_chain) == 3
        and (f"scipy.stats.{helper_chain[1]}.{helper_chain[2]}" in _DISTRIBUTION_HELPER_METHODS)
    ):
        return all(closed(item) for item in expression.args) and all(
            closed(item.value) for item in expression.keywords
        )
    name_calls = {
        "len",
        "min",
        "max",
        "sum",
        "sorted",
        "round",
        "abs",
        "list",
        "str",
        "fmean",
        "mean",
        "stdev",
        "median",
        "variance",
        "any",
        "all",
        "tuple",
    }
    if pandas_projections is not None:
        name_calls.add("float")
    module_calls = {
        "statistics.mean",
        "statistics.fmean",
        "statistics.stdev",
        "statistics.median",
        "statistics.variance",
        "np.mean",
        "np.std",
        "np.var",
        "np.median",
        "math.sqrt",
        "math.isnan",
    }
    string_methods = {
        "format",
        "join",
        "lower",
        "upper",
        "strip",
        "lstrip",
        "rstrip",
        "replace",
        "split",
    }
    if isinstance(expression.func, ast.Name):
        if expression.func.id not in name_calls or expression.keywords:
            return False
        if (
            expression.func.id in {"list", "sorted"}
            and expression.args
            and isinstance(expression.args[0], ast.Name)
            and expression.args[0].id in operands
            and expression.args[0].id not in scalar_sequences
        ):
            return False
    elif isinstance(expression.func, ast.Attribute):
        if isinstance(expression.func.value, ast.Name) and expression.func.value.id in (
            pandas_projections or {}
        ):
            # The sole partition classifies this call as sink-bound.  Exact
            # projection/method/argument semantics are checked later by the
            # fixed pandas-result-sink obligation.
            return all(closed(item) for item in expression.args) and all(
                closed(item.value) for item in expression.keywords
            )
        if (
            isinstance(expression.func.value, ast.Name)
            and f"{expression.func.value.id}.{expression.func.attr}" in module_calls
        ):
            if expression.keywords:
                return False
        elif expression.func.attr not in string_methods:
            return False
        if not closed(expression.func.value):
            return False
    else:
        return False
    return all(closed(item) for item in expression.args) and all(
        closed(item.value) for item in expression.keywords
    )


def _kernel_sink_partition_matches(
    tree: ast.Module,
    certificate: DependenceGrowthCertificate
    | CountDependenceCertificate
    | PairedDependenceCertificate,
    *,
    precomputed_partition: tuple[list[ast.stmt], set[str]] | None = None,
    abort_only_guards: tuple[AbortOnlyGuardToken, ...] = (),
    pandas_replay: _KernelPandasSourceReplay | None = None,
) -> bool:
    partition = (
        precomputed_partition
        if precomputed_partition is not None
        else _kernel_partition_body(
            tree,
            certificate,
            pandas_body=(list(pandas_replay.body) if pandas_replay is not None else None),
            pandas_procedure=(
                pandas_replay.procedure_statement if pandas_replay is not None else None
            ),
            pandas_writer=(pandas_replay.writer_statement if pandas_replay is not None else None),
        )
    )
    if partition is None:
        return False
    body, operands = partition
    imports = _kernel_imports(tree)
    procedures: tuple[ast.Assign, ...]
    if pandas_replay is not None:
        if not isinstance(certificate, DependenceGrowthCertificate):
            return False
        procedures = (pandas_replay.procedure_statement,)
    elif isinstance(certificate, CountDependenceCertificate):
        procedures = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and _kernel_resolved_call(statement.value.func, imports)
            == certificate.resolved_callable
        )
        if len(procedures) != 1:
            return False
    elif isinstance(certificate, PairedDependenceCertificate):
        procedures = tuple(
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Call)
            and _kernel_resolved_call(statement.value.func, imports)
            == certificate.resolved_callable
        )
        if len(procedures) != 1:
            return False
    else:
        census = _kernel_group_census(body, imports, certificate)
        if census is None:
            return False
        procedures, _helpers = census
    writes = (
        [(pandas_replay.writer_statement, pandas_replay.write_call)]
        if pandas_replay is not None
        else [
            (statement, node)
            for statement in body
            for node in ast.walk(statement)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_text"
        ]
    )
    if not procedures or len(writes) != 1:
        return False
    scalar_sequences = {
        argument.id
        for procedure in procedures
        for argument in cast(ast.Call, procedure.value).args
        if isinstance(argument, ast.Name)
    }
    pandas_projections = dict(pandas_replay.projections) if pandas_replay is not None else None
    if pandas_projections and any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in operands
        and node.func.attr
        in {
            "drop",
            "dropna",
            "fillna",
            "rename",
            "sort_values",
            "update",
            "insert",
            "pop",
            "set_index",
            "reset_index",
            "clear",
            "extend",
        }
        for statement in body
        for node in ast.walk(statement)
    ):
        return False
    if any(
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id.startswith("__dependence_v2_argument_")
        and _kernel_expression_roots_in_operand_container(statement.value, operands)
        for statement in body
    ):
        return False
    sink_statement, sink = writes[0]
    if (
        (pandas_replay is None and not isinstance(sink_statement, ast.Expr))
        or (pandas_replay is not None and sink_statement is not pandas_replay.writer_statement)
        or len(sink.args) != 1
    ):
        return False
    definitions = {
        statement.targets[0].id: statement.value
        for statement in body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }
    for statement in body:
        if (
            isinstance(statement, ast.If)
            and len(statement.body) == len(statement.orelse) == 1
            and isinstance(statement.body[0], ast.Assign)
            and isinstance(statement.orelse[0], ast.Assign)
            and len(statement.body[0].targets) == len(statement.orelse[0].targets) == 1
            and isinstance(statement.body[0].targets[0], ast.Name)
            and isinstance(statement.orelse[0].targets[0], ast.Name)
            and statement.body[0].targets[0].id == statement.orelse[0].targets[0].id
        ):
            definitions[statement.body[0].targets[0].id] = ast.IfExp(
                statement.test, statement.body[0].value, statement.orelse[0].value
            )
    operand_indices: set[int] = set()
    for index, statement in enumerate(body):
        stores = {
            node.id
            for node in ast.walk(statement)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        }
        if (
            statement in procedures
            or (
                isinstance(statement, ast.With | ast.For)
                and (pandas_replay is None or statement is not pandas_replay.writer_statement)
            )
            or stores & operands
        ):
            operand_indices.add(index)
    sink_index = body.index(sink_statement)
    sink_indices = {sink_index}
    pending = [node.id for node in ast.walk(sink.args[0]) if isinstance(node, ast.Name)]
    sink_names: set[str] = set()
    while pending:
        name = pending.pop()
        if name in sink_names:
            continue
        sink_names.add(name)
        if name in definitions:
            pending.extend(
                node.id for node in ast.walk(definitions[name]) if isinstance(node, ast.Name)
            )
    sink_names -= operands
    for index, statement in enumerate(body):
        if index in operand_indices or index in sink_indices:
            continue
        if (
            isinstance(certificate, DependenceGrowthCertificate)
            and abort_only_guards
            and _kernel_abort_only_guard_statement(statement, allow_not_name=False)
        ):
            continue
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and _kernel_closed_makedirs(statement.value, _kernel_constants(tree))
        ):
            sink_indices.add(index)
            continue
        if isinstance(statement, ast.If):
            branches = [*statement.body, *statement.orelse]
            if not (
                len(statement.body) == len(statement.orelse) == 1
                and all(
                    isinstance(branch, ast.Assign)
                    and len(branch.targets) == 1
                    and isinstance(branch.targets[0], ast.Name)
                    and branch.targets[0].id in sink_names
                    and _kernel_sink_expression_closed(
                        branch.value,
                        operands,
                        scalar_sequences,
                        pandas_projections=pandas_projections,
                    )
                    for branch in branches
                )
                and _kernel_sink_expression_closed(
                    statement.test,
                    operands,
                    scalar_sequences,
                    pandas_projections=pandas_projections,
                )
            ):
                return False
            sink_indices.add(index)
            continue
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in sink_names
            and not (isinstance(statement.value, ast.Name) and statement.value.id in operands)
            and _kernel_sink_expression_closed(
                statement.value,
                operands,
                scalar_sequences,
                pandas_projections=pandas_projections,
            )
        ):
            return False
        sink_indices.add(index)
    if not _kernel_sink_expression_closed(
        sink.args[0],
        operands,
        scalar_sequences,
        pandas_projections=pandas_projections,
    ):
        return False
    return certificate.operand_slice_statement_tokens == tuple(
        _kernel_statement_token(body[index], index) for index in sorted(operand_indices)
    ) and certificate.sink_bound_statement_tokens == tuple(
        _kernel_statement_token(body[index], index) for index in sorted(sink_indices)
    )


def _kernel_expression_roots_in_operand_container(expression: ast.expr, operands: set[str]) -> bool:
    value = expression
    while isinstance(value, ast.Subscript):
        value = value.value
    return isinstance(value, ast.Name) and value.id in operands


def _kernel_resolved_call(expression: ast.expr, imports: dict[str, str]) -> str | None:
    if isinstance(expression, ast.Name):
        return imports.get(expression.id)
    if isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name):
        prefix = imports.get(expression.value.id)
        return f"{prefix}.{expression.attr}" if prefix is not None else None
    return None


def _kernel_call_sites(
    tree: ast.Module, functions: dict[str, ast.FunctionDef]
) -> tuple[tuple[str, str, tuple[int, int, int, int]], ...]:
    """Independently enumerate the bounded acyclic call-path identities."""

    counter = 0
    result: list[tuple[str, str, tuple[int, int, int, int]]] = []

    def walk(statements: list[ast.stmt], parent: tuple[str, ...], depth: int) -> None:
        nonlocal counter
        if depth > MAX_V2_INLINE_DEPTH:
            return
        for statement in statements:
            calls: list[ast.Call] = []
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                if isinstance(statement.value.func, ast.Name):
                    calls.append(statement.value)
                elif (
                    isinstance(statement.value.func, ast.Attribute)
                    and statement.value.func.attr == "write_text"
                    and statement.value.args
                ):
                    calls.extend(
                        node
                        for node in ast.walk(statement.value.args[0])
                        if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id in functions
                    )
            elif (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.value, ast.Call)
            ):
                calls.append(statement.value)
            elif isinstance(statement, ast.Return) and statement.value is not None:
                calls.extend(
                    node
                    for node in ast.walk(statement.value)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in functions
                )
            for call in calls:
                if not isinstance(call.func, ast.Name) or call.func.id not in functions:
                    continue
                counter += 1
                component = f"{call.func.id}:{counter}"
                path = (*parent, component)
                result.append(
                    (
                        call.func.id,
                        "inline-call-path:" + "/".join(path),
                        (
                            getattr(call, "lineno", 0),
                            getattr(call, "col_offset", 0),
                            getattr(call, "end_lineno", 0),
                            getattr(call, "end_col_offset", 0),
                        ),
                    )
                )
                walk(functions[call.func.id].body, path, depth + 1)

    executable: list[ast.stmt] = []
    for item in tree.body:
        if isinstance(item, ast.FunctionDef | ast.Import | ast.ImportFrom):
            continue
        if isinstance(item, ast.If) and _kernel_main_guard(item):
            executable.extend(item.body)
        else:
            executable.append(item)
    walk(executable, (), 0)
    return tuple(result)


def _kernel_function_shape_closed(
    function: ast.FunctionDef,
    import_names: set[str],
    typing_names: set[str],
    constants: set[str],
    function_names: set[str],
) -> bool:
    args = function.args
    if (
        args.posonlyargs
        or args.kwonlyargs
        or args.defaults
        or args.kw_defaults
        or args.vararg is not None
        or args.kwarg is not None
    ):
        return False
    if any(
        isinstance(node, ast.Global | ast.Nonlocal | ast.Lambda)
        or (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node is not function
        )
        for node in ast.walk(function)
    ):
        return False
    parameters = {item.arg for item in args.args}
    stored = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    if parameters & stored or (parameters | stored) & import_names:
        return False
    annotation_nodes = _kernel_annotation_nodes(function)
    loads = {
        node.id
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node not in annotation_nodes
    }
    loads -= {
        node.id
        for raised in (item for item in ast.walk(function) if isinstance(item, ast.Raise))
        for node in ast.walk(raised)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    if loads & typing_names:
        return False
    allowed = (
        parameters
        | stored
        | constants
        | import_names
        | function_names
        | {
            "list",
            "set",
            "float",
            "int",
            "sorted",
            "str",
            "len",
            "min",
            "max",
            "sum",
            "round",
            "abs",
            "range",
            "enumerate",
            "dict",
            "any",
            "all",
            "tuple",
        }
    )
    if loads - allowed:
        return False
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    return len(returns) <= 1 and (not returns or _kernel_final_return(function.body, returns[0]))


def _kernel_final_return(body: list[ast.stmt], target: ast.Return) -> bool:
    return bool(
        (body and body[-1] is target)
        or (
            body
            and isinstance(body[-1], ast.With)
            and body[-1].body
            and body[-1].body[-1] is target
        )
    )


def _kernel_graph_cyclic(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(name: str) -> bool:
        if name in visiting:
            return True
        if name in done:
            return False
        visiting.add(name)
        if any(visit(child) for child in graph[name]):
            return True
        visiting.remove(name)
        done.add(name)
        return False

    return any(visit(name) for name in graph)


def _kernel_graph_depth(name: str, graph: dict[str, set[str]]) -> int:
    return 1 + max((_kernel_graph_depth(child, graph) for child in graph[name]), default=0)
