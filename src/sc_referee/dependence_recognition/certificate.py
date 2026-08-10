"""Small trusted certificate kernel for dependence semantic v1.

The future static analyzer is a proposing component only.  This module knows
none of its lowering machinery: it accepts closed records from :mod:`ir`,
recomputes obligations O1-O13, and either returns one bounded report-only proof
or abstains with ``None``.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import dataclass

from sc_referee.core.ids import semantic_digest
from sc_referee.dependence_core import SAFEGUARD_IDS
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
    RECOGNIZED_READER_MODELS,
    BoundPackageVersion,
    DependenceCaseBinding,
    DependenceCertificate,
    DependenceConclusion,
    FrameLineage,
    FrameTransform,
    HumanMethodAuthorization,
    MaterialInputBinding,
    ProcedureCall,
    ReaderBinding,
    RecordRef,
    SafeguardCheckObligation,
    SinkLineageObligation,
    UnitKeyMultiplicityFact,
    UnitKeyMultiplicityObligation,
    VerifiedDependenceCertificate,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import EvidencePoint

_RECOGNIZED_READER_MODELS = dict(RECOGNIZED_READER_MODELS)
_RECOGNIZED_DIALECT = "excel"
_RECOGNIZED_TRANSFORMS = frozenset({"identity"})
_UNIT_AGGREGATION_SAFEGUARD = "safeguard:unit-level-aggregation"
_PAIRED_SAFEGUARD = "safeguard:paired-or-blocked-procedure"
_LOWER_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class _ProcedureRegistryEntry:
    resolved_callable: str
    positional_argument_count: int
    keyword_argument_names: tuple[str, ...]
    independence_model: str
    required_safeguard_id: str | None
    supported_versions: frozenset[str]


@dataclass(frozen=True)
class _MultiplicityResolution:
    fact: UnitKeyMultiplicityFact
    source_unit_ids: tuple[str, ...]
    source_repeated_unit_ids: tuple[str, ...]


@dataclass(frozen=True)
class _FrameResolution:
    analyzed_unit_ids: tuple[str, ...]


_PROCEDURE_REGISTRY: tuple[_ProcedureRegistryEntry, ...] = (
    _ProcedureRegistryEntry(
        resolved_callable="scipy.stats.ttest_ind",
        positional_argument_count=2,
        keyword_argument_names=(),
        independence_model="row_independent",
        required_safeguard_id=None,
        supported_versions=frozenset({"1.14.0"}),
    ),
    _ProcedureRegistryEntry(
        resolved_callable="scipy.stats.mannwhitneyu",
        positional_argument_count=2,
        keyword_argument_names=(),
        independence_model="row_independent",
        required_safeguard_id=None,
        supported_versions=frozenset({"1.14.0"}),
    ),
    _ProcedureRegistryEntry(
        resolved_callable="scipy.stats.ttest_rel",
        positional_argument_count=2,
        keyword_argument_names=(),
        independence_model="paired",
        required_safeguard_id=_PAIRED_SAFEGUARD,
        supported_versions=frozenset({"1.14.0"}),
    ),
)


def verify_dependence_certificate(
    certificate: DependenceCertificate,
    *,
    trusted_multiplicity_facts: tuple[UnitKeyMultiplicityFact, ...] = (),
    trusted_authorizations: tuple[HumanMethodAuthorization, ...] = (),
) -> VerifiedDependenceCertificate | None:
    """Accept one complete internally consistent static proof or abstain."""

    if not _certificate_identity_is_closed(certificate):
        return None
    if not _case_binding_is_closed(certificate.case_binding):
        return None
    authority = _trusted_authorization_is_discharged(
        certificate.case_binding,
        trusted_authorizations,
    )
    if authority is None:
        return None

    multiplicity = _multiplicity_fact_is_discharged(
        certificate,
        trusted_multiplicity_facts,
        authority,
    )
    if multiplicity is None:
        return None
    frame = _frame_lineage_is_closed(
        certificate.frame_lineage,
        multiplicity,
        certificate.procedure_call,
    )
    if frame is None:
        return None
    procedure_entry = _procedure_call_is_registered(
        certificate.procedure_call,
        certificate.case_binding,
        certificate.frame_lineage,
    )
    if procedure_entry is None:
        return None

    expected_safeguard_matches = _expected_safeguard_matches(
        certificate.procedure_call,
        procedure_entry,
    )
    if expected_safeguard_matches is None:
        return None
    applicable_safeguards = _safeguard_protocol_is_closed(
        certificate,
        expected_safeguard_matches,
    )
    if applicable_safeguards is None:
        return None

    analyzed_counts = Counter(frame.analyzed_unit_ids)
    analyzed_repeated = tuple(
        sorted(unit_id for unit_id, count in analyzed_counts.items() if count > 1)
    )
    conclusion: DependenceConclusion = (
        "repeated_units" if analyzed_repeated else "one_observation_per_unit"
    )
    active_sink_tokens = _sinks_are_closed(certificate, conclusion)
    if active_sink_tokens is None:
        return None
    if not _proof_slice_is_noninterfering(certificate, multiplicity.fact):
        return None
    if not _evidence_is_closed(certificate, multiplicity.fact):
        return None

    return VerifiedDependenceCertificate(
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        case_binding=certificate.case_binding,
        frame_lineage=certificate.frame_lineage,
        procedure_call=certificate.procedure_call,
        conclusion=conclusion,
        repeated_unit_ids=analyzed_repeated,
        source_frame_repeated_unit_ids=multiplicity.source_repeated_unit_ids,
        applicable_safeguard_ids=applicable_safeguards,
        domain_fact=multiplicity.fact,
        sink_tokens=active_sink_tokens,
        evidence=tuple(sorted(certificate.evidence)),
        proposed_case_digest=certificate.proposed_case_digest,
        output_ceiling=certificate.output_ceiling,
        wording_ceiling=certificate.wording_ceiling,
    )


def dependence_replay_digest(certificate: DependenceCertificate) -> str:
    """Canonical digest over the parser/source and all completeness token sets."""

    safeguard_sets = [
        {
            "safeguard_id": check.safeguard_id,
            "complete": sorted(check.complete_syntactic_construct_tokens),
            "modeled": sorted(check.modeled_construct_tokens),
            "proven_dead": sorted(check.proven_dead_construct_tokens),
            "matched": sorted(check.matched_construct_tokens),
        }
        for check in sorted(certificate.safeguard_checks, key=lambda item: item.safeguard_id)
    ]
    return semantic_digest(
        {
            "source_digest": certificate.source_digest,
            "parser_id": certificate.parser_id,
            "parser_version": certificate.parser_version,
            "source_extent": {
                "path": certificate.source_extent.path,
                "start_line": certificate.source_extent.start_line,
                "end_line": certificate.source_extent.end_line,
                "start_column": certificate.source_extent.start_column,
                "end_column": certificate.source_extent.end_column,
            },
            "all_syntactic_construct_tokens": sorted(certificate.all_syntactic_construct_tokens),
            "dead_syntactic_construct_tokens": sorted(certificate.dead_syntactic_construct_tokens),
            "all_sink_tokens": sorted(certificate.all_sink_tokens),
            "dead_sink_tokens": sorted(certificate.dead_sink_tokens),
            "safeguard_completeness": safeguard_sets,
        }
    )


def _certificate_identity_is_closed(certificate: DependenceCertificate) -> bool:
    if (
        not _relative_path(certificate.source_path)
        or not _sha256(certificate.source_digest)
        or not _present(certificate.parser_id)
        or not _present(certificate.parser_version)
        or not _source_extent_is_closed(certificate)
        or not _sha256(certificate.dependency_closure_digest)
        or not _sha256(certificate.proposed_case_digest)
        or certificate.replay_digest != dependence_replay_digest(certificate)
        or certificate.safeguard_registry_ids != SAFEGUARD_IDS
        or certificate.output_ceiling != "evaluation_candidate"
        or certificate.wording_ceiling != "static_code_relationship_only"
    ):
        return False
    all_constructs = certificate.all_syntactic_construct_tokens
    dead_constructs = certificate.dead_syntactic_construct_tokens
    if (
        not _nonempty_token_set(all_constructs)
        or not _token_set(dead_constructs)
        or not dead_constructs <= all_constructs
        or not all_constructs - dead_constructs
        or not certificate.dead_sink_tokens <= dead_constructs
    ):
        return False
    return True


def _case_binding_is_closed(binding: DependenceCaseBinding) -> bool:
    return (
        _present(binding.case_id)
        and _record_ref_is_closed(binding.analysis_target_ref, "analysis")
        and _record_ref_is_closed(binding.procedure_ref, "procedure")
        and _record_ref_is_closed(binding.affected_target_ref)
        and binding.affected_target_ref.record_type in {"result", "claim"}
        and _present(binding.independent_unit_definition_id)
        and _nonempty_unique_strings(binding.authorized_key_columns, trimmed=False)
    )


def _authority_is_closed(authority: HumanMethodAuthorization) -> bool:
    return (
        authority.record_type == "human_method_authorization"
        and _present(authority.record_id)
        and _present(authority.actor_id)
        and authority.authority_state == "authorized"
        and _record_ref_is_closed(authority.analysis_target_ref, "analysis")
        and _record_ref_is_closed(authority.procedure_ref, "procedure")
        and _present(authority.independent_unit_definition_id)
        and _nonempty_unique_strings(authority.authorized_key_columns, trimmed=False)
        and _relative_path(authority.input_path)
        and _sha256(authority.input_content_digest)
    )


def _authority_key(
    authority: HumanMethodAuthorization,
) -> tuple[RecordRef, RecordRef, str]:
    return (
        authority.analysis_target_ref,
        authority.procedure_ref,
        authority.independent_unit_definition_id,
    )


def _case_authority_key(
    binding: DependenceCaseBinding,
) -> tuple[RecordRef, RecordRef, str]:
    return (
        binding.analysis_target_ref,
        binding.procedure_ref,
        binding.independent_unit_definition_id,
    )


def _trusted_authorization_is_discharged(
    binding: DependenceCaseBinding,
    trusted_authorizations: tuple[HumanMethodAuthorization, ...],
) -> HumanMethodAuthorization | None:
    if (
        len(trusted_authorizations) != 1
        or len(set(trusted_authorizations)) != len(trusted_authorizations)
        or not all(_authority_is_closed(item) for item in trusted_authorizations)
    ):
        return None
    authority = trusted_authorizations[0]
    if _authority_key(authority) != _case_authority_key(binding):
        return None
    if authority.authorized_key_columns != binding.authorized_key_columns:
        return None
    return authority


def _multiplicity_fact_is_discharged(
    certificate: DependenceCertificate,
    trusted_facts: tuple[UnitKeyMultiplicityFact, ...],
    authority: HumanMethodAuthorization,
) -> _MultiplicityResolution | None:
    if len(set(trusted_facts)) != len(trusted_facts):
        return None
    resolutions = tuple(_multiplicity_fact_resolution(fact) for fact in trusted_facts)
    if any(item is None for item in resolutions):
        return None
    closed_resolutions = tuple(item for item in resolutions if item is not None)
    facts_by_key = {_multiplicity_fact_key(item.fact): item for item in closed_resolutions}
    if len(facts_by_key) != len(closed_resolutions):
        return None

    obligations = certificate.multiplicity_obligations
    obligation_keys = tuple(_multiplicity_obligation_key(item) for item in obligations)
    expected_key = _lineage_obligation_key(
        certificate.frame_lineage,
        certificate.case_binding.authorized_key_columns,
    )
    if (
        len(obligation_keys) != len(set(obligation_keys))
        or set(obligation_keys) != {expected_key}
        or set(facts_by_key) != set(obligation_keys)
        or len(obligations) != 1
    ):
        return None

    obligation = obligations[0]
    resolution = facts_by_key.get(obligation_keys[0])
    if resolution is None or not _fact_matches_obligation(resolution.fact, obligation):
        return None
    fact = resolution.fact
    if not (
        authority.authorized_key_columns
        == certificate.case_binding.authorized_key_columns
        == obligation.key_columns
        == fact.key_columns
        and authority.input_path == obligation.input_binding.path == fact.path
        and authority.input_content_digest
        == obligation.input_binding.content_digest
        == fact.content_digest
    ):
        return None
    return resolution


def _lineage_obligation_key(
    lineage: FrameLineage,
    key_columns: tuple[str, ...],
) -> tuple[str, str, tuple[str, ...], str, str]:
    return (
        lineage.input_binding.path,
        lineage.input_binding.content_digest,
        key_columns,
        lineage.source_row_domain,
        lineage.reader.line_model,
    )


def _multiplicity_obligation_key(
    obligation: UnitKeyMultiplicityObligation,
) -> tuple[str, str, tuple[str, ...], str, str]:
    return (
        obligation.input_binding.path,
        obligation.input_binding.content_digest,
        obligation.key_columns,
        obligation.row_domain,
        obligation.reader.line_model,
    )


def _multiplicity_fact_key(
    fact: UnitKeyMultiplicityFact,
) -> tuple[str, str, tuple[str, ...], str, str]:
    return (
        fact.path,
        fact.content_digest,
        fact.key_columns,
        fact.row_domain,
        fact.line_model,
    )


def _fact_matches_obligation(
    fact: UnitKeyMultiplicityFact,
    obligation: UnitKeyMultiplicityObligation,
) -> bool:
    binding = obligation.input_binding
    reader = obligation.reader
    return (
        _material_input_binding_is_closed(binding)
        and _reader_binding_is_closed(reader)
        and fact.path == binding.path
        and fact.content_digest == binding.content_digest
        and fact.file_ref == binding.file_ref
        and fact.asset_identity_ref == binding.asset_identity_ref
        and fact.reader_form == reader.reader_form
        and fact.line_model == reader.line_model
        and fact.dialect == reader.dialect
        and fact.row_domain == obligation.row_domain
        and fact.key_columns == obligation.key_columns
    )


def _multiplicity_fact_resolution(
    fact: UnitKeyMultiplicityFact,
) -> _MultiplicityResolution | None:
    if (
        not _present(fact.evidence_id)
        or not _relative_path(fact.path)
        or not _sha256(fact.content_digest)
        or not _record_ref_is_closed(fact.file_ref, "file_record")
        or not _record_ref_is_closed(fact.asset_identity_ref, "asset_identity")
        or not _reader_model_is_recognized(fact.reader_form, fact.line_model, fact.dialect)
        or (fact.line_model == "splitlines" and not fact.splitlines_only_separators_absent)
        or not _present(fact.row_domain)
        or fact.source_byte_count < 1
        or fact.source_byte_count > MAX_DEPENDENCE_CSV_DOMAIN_BYTES
        or not fact.header
        or len(fact.header) > MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
        or len(set(fact.header)) != len(fact.header)
        or any(
            not item or len(item.encode("utf-8")) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
            for item in fact.header
        )
        or not _nonempty_unique_strings(fact.key_columns, trimmed=False)
        or not set(fact.key_columns) <= set(fact.header)
        or fact.normalization
        != ("splitlines_rejoined_utf8" if fact.line_model == "splitlines" else "byte_exact_utf8")
        or not _unique_strings(fact.declared_missing_value_tokens, trimmed=False)
        or any(not item for item in fact.declared_missing_value_tokens)
        or fact.missing_key_value_count != 0
        or not fact.row_shape_complete
        or fact.row_count < 1
        or fact.row_count > MAX_DEPENDENCE_CSV_DOMAIN_ROWS
        or len(fact.observation_ids) != fact.row_count
        or not _nonempty_unique_strings(fact.observation_ids)
        or len(fact.key_value_tuples) != fact.row_count
        or len(fact.unit_ids) != fact.row_count
    ):
        return None
    for key in fact.key_value_tuples:
        if len(key) != len(fact.key_columns) or any(
            not value
            or len(value.encode("utf-8")) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
            or value in fact.declared_missing_value_tokens
            for value in key
        ):
            return None

    derived_unit_ids = tuple(_unit_id(fact.key_columns, key) for key in fact.key_value_tuples)
    counts = Counter(derived_unit_ids)
    expected_multiplicities = tuple(sorted(counts.items()))
    expected_repeated = tuple(sorted(unit_id for unit_id, count in counts.items() if count > 1))
    if not (
        fact.unit_ids == derived_unit_ids
        and fact.distinct_key_count == len(counts)
        and fact.multiplicities == expected_multiplicities
        and fact.repeated_unit_ids == expected_repeated
    ):
        return None
    return _MultiplicityResolution(fact, derived_unit_ids, expected_repeated)


def _unit_id(key_columns: tuple[str, ...], key: tuple[str, ...]) -> str:
    return f"unit-key:{semantic_digest({'key_columns': key_columns, 'key_values': key})}"


def _frame_lineage_is_closed(
    lineage: FrameLineage,
    multiplicity: _MultiplicityResolution,
    procedure: ProcedureCall,
) -> _FrameResolution | None:
    fact = multiplicity.fact
    if (
        not _present(lineage.token)
        or not _material_input_binding_is_closed(lineage.input_binding)
        or not _reader_binding_is_closed(lineage.reader)
        or lineage.input_binding
        != MaterialInputBinding(
            fact.path,
            fact.content_digest,
            fact.file_ref,
            fact.asset_identity_ref,
        )
        or lineage.reader
        != ReaderBinding(
            lineage.reader.token,
            fact.reader_form,
            fact.line_model,
            fact.dialect,
        )
        or lineage.source_row_domain != fact.row_domain
        or lineage.source_observation_ids != fact.observation_ids
        or lineage.procedure_call_token != procedure.token
        or not _nonempty_token_set(lineage.relevant_origins)
        or not _nonempty_token_set(lineage.relevant_bindings)
    ):
        return None

    transform_tokens = tuple(item.token for item in lineage.transforms)
    if len(transform_tokens) != len(set(transform_tokens)):
        return None
    current_domain = fact.row_domain
    all_row_domains = {fact.row_domain, lineage.source_row_domain, lineage.analyzed_row_domain}
    for transform in lineage.transforms:
        all_row_domains.update({transform.input_row_domain, transform.output_row_domain})
        checked = _apply_frame_transform(
            transform,
            current_domain=current_domain,
        )
        if checked is None:
            return None
        current_domain = checked

    expected_output_token = (
        lineage.transforms[-1].token if lineage.transforms else lineage.reader.token
    )
    required_origins = {fact.path, *all_row_domains}
    required_bindings = {
        lineage.reader.token,
        lineage.token,
        lineage.output_token,
        procedure.token,
        procedure.result_token,
        *procedure.positional_argument_tokens,
        *transform_tokens,
    }
    if (
        current_domain != lineage.analyzed_row_domain
        or lineage.output_token != expected_output_token
        or not required_origins <= lineage.relevant_origins
        or not required_bindings <= lineage.relevant_bindings
    ):
        return None

    analyzed_unit_ids = multiplicity.source_unit_ids
    expected_observations = fact.observation_ids
    if (
        lineage.analyzed_observation_ids != expected_observations
        or len(lineage.analyzed_observation_ids) > MAX_V1_MEMBERSHIPS
        or procedure.analyzed_row_domain != lineage.analyzed_row_domain
        or procedure.frame_lineage_token != lineage.token
    ):
        return None
    return _FrameResolution(analyzed_unit_ids)


def _apply_frame_transform(
    transform: FrameTransform,
    *,
    current_domain: str,
) -> str | None:
    if (
        not _present(transform.token)
        or transform.operation not in _RECOGNIZED_TRANSFORMS
        or transform.input_row_domain != current_domain
        or not _present(transform.output_row_domain)
        or not _nonempty_unique_strings(transform.evidence_ids)
    ):
        return None
    if transform.operation == "identity":
        if transform.grouping_columns or transform.output_row_domain != current_domain:
            return None
        return current_domain
    return None


def _procedure_call_is_registered(
    procedure: ProcedureCall,
    case_binding: DependenceCaseBinding,
    lineage: FrameLineage,
) -> _ProcedureRegistryEntry | None:
    matches = [
        item
        for item in _PROCEDURE_REGISTRY
        if item.resolved_callable == procedure.resolved_callable
    ]
    if len(matches) != 1:
        return None
    registered = matches[0]
    argument_bindings = procedure.positional_argument_frame_bindings
    binding_keys = tuple(item[0] for item in argument_bindings)
    if (
        not _present(procedure.token)
        or procedure.analysis_target_ref != case_binding.analysis_target_ref
        or procedure.procedure_ref != case_binding.procedure_ref
        or len(procedure.positional_argument_tokens) != registered.positional_argument_count
        or not _nonempty_unique_strings(procedure.positional_argument_tokens)
        or len(binding_keys) != len(set(binding_keys))
        or set(binding_keys) != set(procedure.positional_argument_tokens)
        or any(
            not _present(argument) or frame_token != lineage.output_token
            for argument, frame_token in argument_bindings
        )
        or procedure.keyword_argument_names != registered.keyword_argument_names
        or procedure.frame_lineage_token != lineage.token
        or procedure.analyzed_row_domain != lineage.analyzed_row_domain
        or not _bound_package_version_is_closed(procedure.package_version)
        or procedure.package_version.version not in registered.supported_versions
        or not _present(procedure.result_token)
        or not _nonempty_unique_strings(procedure.evidence_ids)
    ):
        return None
    if registered.independence_model == "paired":
        if procedure.unit_operand_columns != case_binding.authorized_key_columns:
            return None
    elif procedure.unit_operand_columns:
        return None
    return registered


def _bound_package_version_is_closed(version: BoundPackageVersion) -> bool:
    return (
        version.package_name == "scipy"
        and _exact_package_version(version.version)
        and _nonempty_unique_strings(version.evidence_ids)
    )


def _expected_safeguard_matches(
    procedure: ProcedureCall,
    registered: _ProcedureRegistryEntry,
) -> dict[str, frozenset[str]] | None:
    matches: dict[str, set[str]] = {item: set() for item in SAFEGUARD_IDS}
    if _UNIT_AGGREGATION_SAFEGUARD not in matches or _PAIRED_SAFEGUARD not in matches:
        return None
    # Unit-level aggregation is a named future route. No v1 transform can
    # establish this safeguard on the certified list-bound CSV readers.
    if registered.required_safeguard_id is not None:
        matches[registered.required_safeguard_id].add(procedure.token)
    return {key: frozenset(value) for key, value in matches.items()}


def _safeguard_protocol_is_closed(
    certificate: DependenceCertificate,
    expected_matches: dict[str, frozenset[str]],
) -> tuple[str, ...] | None:
    checks = certificate.safeguard_checks
    checks_by_id = {item.safeguard_id: item for item in checks}
    if len(checks_by_id) != len(checks) or set(checks_by_id) != set(SAFEGUARD_IDS):
        return None

    all_constructs = certificate.all_syntactic_construct_tokens
    dead_constructs = certificate.dead_syntactic_construct_tokens
    active_constructs = all_constructs - dead_constructs
    required_tokens = (
        certificate.frame_lineage.reader.token,
        certificate.frame_lineage.token,
        certificate.procedure_call.token,
        *(item.token for item in certificate.frame_lineage.transforms),
        *(item.token for item in certificate.sinks),
    )
    if (
        len(required_tokens) != len(set(required_tokens))
        or not set(required_tokens) <= active_constructs
    ):
        return None

    present: list[str] = []
    for safeguard_id in SAFEGUARD_IDS:
        check = checks_by_id[safeguard_id]
        expected = expected_matches[safeguard_id]
        expected_basis = (
            "recognized-collapse"
            if expected and safeguard_id == _UNIT_AGGREGATION_SAFEGUARD
            else "registry-match"
            if expected
            else "completeness-equation"
        )
        if not _safeguard_binding_is_exact(check, certificate.case_binding):
            return None
        if (
            not _nonempty_unique_strings(check.evidence_ids)
            or check.basis != expected_basis
            or check.complete_syntactic_construct_tokens != all_constructs
            or check.proven_dead_construct_tokens != dead_constructs
            or check.modeled_construct_tokens != active_constructs
            or check.matched_construct_tokens != expected
            or not check.matched_construct_tokens <= active_constructs
        ):
            return None
        if expected:
            if check.state != "present":
                return None
            present.append(safeguard_id)
        elif check.state not in {"absent", "not_applicable"}:
            return None
    return tuple(sorted(present))


def _safeguard_binding_is_exact(
    check: SafeguardCheckObligation,
    case_binding: DependenceCaseBinding,
) -> bool:
    return (
        check.analysis_target_ref == case_binding.analysis_target_ref
        and check.procedure_ref == case_binding.procedure_ref
        and check.independent_unit_definition_id == case_binding.independent_unit_definition_id
    )


def _sinks_are_closed(
    certificate: DependenceCertificate,
    conclusion: DependenceConclusion,
) -> tuple[str, ...] | None:
    sinks = certificate.sinks
    sink_tokens = tuple(item.token for item in sinks)
    if not sinks or len(sink_tokens) != len(set(sink_tokens)):
        return None
    if (
        not _nonempty_token_set(certificate.all_sink_tokens)
        or not _token_set(certificate.dead_sink_tokens)
        or not certificate.dead_sink_tokens <= certificate.all_sink_tokens
        or not certificate.dead_sink_tokens <= certificate.dead_syntactic_construct_tokens
    ):
        return None
    active_sink_tokens = certificate.all_sink_tokens - certificate.dead_sink_tokens
    if set(sink_tokens) != active_sink_tokens:
        return None

    for sink in sinks:
        if not _sink_is_closed(
            sink,
            case_binding=certificate.case_binding,
            procedure=certificate.procedure_call,
            conclusion=conclusion,
            source_path=certificate.source_path,
            input_path=certificate.frame_lineage.input_binding.path,
        ):
            return None
    if {item.conclusion for item in sinks} != {conclusion}:
        return None
    if not certificate.reaching_path_conclusions or any(
        states != frozenset({conclusion}) for states in certificate.reaching_path_conclusions
    ):
        return None
    return tuple(sorted(active_sink_tokens))


def _sink_is_closed(
    sink: SinkLineageObligation,
    *,
    case_binding: DependenceCaseBinding,
    procedure: ProcedureCall,
    conclusion: DependenceConclusion,
    source_path: str,
    input_path: str,
) -> bool:
    return (
        _present(sink.token)
        and _present(sink.path)
        and _relative_path(sink.path)
        and sink.path not in {source_path, input_path}
        and sink.affected_target_ref == case_binding.affected_target_ref
        and sink.affected_target_ref.record_type in {"result", "claim"}
        and sink.procedure_call_token == procedure.token
        and sink.procedure_result_token == procedure.result_token
        and _nonempty_token_set(sink.payload_tokens)
        and procedure.result_token in sink.payload_tokens
        and sink.selected_result
        and sink.conclusion == conclusion
        and _nonempty_unique_strings(sink.evidence_ids)
        and _nonempty_token_set(sink.relevant_origins)
        and _nonempty_token_set(sink.relevant_bindings)
    )


def _derived_slice_sets(
    certificate: DependenceCertificate,
    fact: UnitKeyMultiplicityFact,
) -> tuple[set[str], set[str]]:
    lineage = certificate.frame_lineage
    procedure = certificate.procedure_call
    relevant_origins = {
        fact.path,
        fact.row_domain,
        lineage.source_row_domain,
        lineage.analyzed_row_domain,
        *(item.input_row_domain for item in lineage.transforms),
        *(item.output_row_domain for item in lineage.transforms),
        *lineage.relevant_origins,
        *(sink.path for sink in certificate.sinks),
        *(origin for sink in certificate.sinks for origin in sink.relevant_origins),
    }
    relevant_bindings = {
        lineage.reader.token,
        lineage.token,
        lineage.output_token,
        procedure.token,
        procedure.result_token,
        *procedure.positional_argument_tokens,
        *(item.token for item in lineage.transforms),
        *(sink.token for sink in certificate.sinks),
        *(token for sink in certificate.sinks for token in sink.payload_tokens),
        *lineage.relevant_bindings,
        *(binding for sink in certificate.sinks for binding in sink.relevant_bindings),
    }
    return relevant_origins, relevant_bindings


def _proof_slice_is_noninterfering(
    certificate: DependenceCertificate,
    fact: UnitKeyMultiplicityFact,
) -> bool:
    relevant_origins, relevant_bindings = _derived_slice_sets(certificate, fact)
    relevant_values = relevant_origins | relevant_bindings
    for effect in certificate.effects:
        if (
            not _token_set(effect.reads)
            or not _token_set(effect.writes)
            or not _token_set(effect.aliases)
            or not _present(effect.reason)
            or (effect.opaque and "*" not in effect.writes)
        ):
            return False
        touches_write = "*" in effect.writes or bool(effect.writes & relevant_values)
        touches_alias = "*" in effect.aliases or bool(effect.aliases & relevant_values)
        raising_on_slice = effect.may_raise and (
            "*" in effect.reads or bool(effect.reads & relevant_values)
        )
        if touches_write or touches_alias or raising_on_slice:
            return False
    for unknown in certificate.unknowns:
        if not _present(unknown.reason) or "*" in unknown.origins:
            return False
        if unknown.origins & relevant_values:
            return False
    return True


def _evidence_is_closed(
    certificate: DependenceCertificate,
    fact: UnitKeyMultiplicityFact,
) -> bool:
    declarations = certificate.evidence
    evidence_by_id = {item.evidence_id: item for item in declarations}
    if (
        not declarations
        or len(evidence_by_id) != len(declarations)
        or len(set(declarations)) != len(declarations)
    ):
        return False
    for declaration in declarations:
        point = declaration.point
        if (
            not _present(declaration.evidence_id)
            or (
                point.path != fact.path
                if declaration.evidence_id == fact.evidence_id
                else point.path != certificate.source_path
            )
            or point.start_line < 1
            or point.end_line < point.start_line
            or point.start_column < 1
            or point.end_column < 1
            or (point.end_line == point.start_line and point.end_column < point.start_column)
            or (
                declaration.evidence_id != fact.evidence_id
                and not _point_within(declaration.point, certificate.source_extent)
            )
        ):
            return False

    code_evidence_id_uses = [
        *(
            evidence_id
            for check in certificate.safeguard_checks
            for evidence_id in check.evidence_ids
        ),
        *(
            evidence_id
            for transform in certificate.frame_lineage.transforms
            for evidence_id in transform.evidence_ids
        ),
        *certificate.procedure_call.package_version.evidence_ids,
        *certificate.procedure_call.evidence_ids,
        *(evidence_id for sink in certificate.sinks for evidence_id in sink.evidence_ids),
    ]
    if fact.evidence_id in code_evidence_id_uses or len(code_evidence_id_uses) != len(
        set(code_evidence_id_uses)
    ):
        return False
    required_ids = {fact.evidence_id, *code_evidence_id_uses}
    if not required_ids <= set(evidence_by_id):
        return False
    code_points = [
        evidence_by_id[evidence_id].point for evidence_id in required_ids - {fact.evidence_id}
    ]
    return len(code_points) == len(set(code_points))


def _source_extent_is_closed(certificate: DependenceCertificate) -> bool:
    extent = certificate.source_extent
    return (
        extent.path == certificate.source_path
        and extent.start_line == 1
        and extent.start_column == 1
        and extent.end_line >= extent.start_line
        and extent.end_column >= 1
    )


def _point_within(point: EvidencePoint, extent: EvidencePoint) -> bool:
    point_start = (point.start_line, point.start_column)
    point_end = (point.end_line, point.end_column)
    extent_start = (extent.start_line, extent.start_column)
    extent_end = (extent.end_line, extent.end_column)
    return extent_start <= point_start <= point_end <= extent_end


def _material_input_binding_is_closed(binding: MaterialInputBinding) -> bool:
    return (
        _relative_path(binding.path)
        and _sha256(binding.content_digest)
        and _record_ref_is_closed(binding.file_ref, "file_record")
        and _record_ref_is_closed(binding.asset_identity_ref, "asset_identity")
    )


def _reader_binding_is_closed(reader: ReaderBinding) -> bool:
    return _present(reader.token) and _reader_model_is_recognized(
        reader.reader_form,
        reader.line_model,
        reader.dialect,
    )


def _reader_model_is_recognized(reader_form: str, line_model: str, dialect: str) -> bool:
    return (
        reader_form in _RECOGNIZED_READER_MODELS
        and _RECOGNIZED_READER_MODELS[reader_form] == line_model
        and dialect == _RECOGNIZED_DIALECT
    )


def _record_ref_is_closed(value: RecordRef, expected_type: str | None = None) -> bool:
    return (
        _present(value.record_type)
        and _present(value.record_id)
        and (expected_type is None or value.record_type == expected_type)
    )


def _relative_path(value: str) -> bool:
    segments = value.split("/")
    return (
        _present(value)
        and not value.startswith("/")
        and "\\" not in value
        and "\x00" not in value
        and not any(unicodedata.category(character).startswith("C") for character in value)
        and not any(unicodedata.category(character) in {"Zl", "Zp"} for character in value)
        and all(segment not in {"", ".", ".."} for segment in segments)
        and not (len(value) >= 2 and value[0].isalpha() and value[1] == ":")
    )


def _sha256(value: str) -> bool:
    payload = value.removeprefix("sha256:")
    return (
        value.startswith("sha256:")
        and len(payload) == 64
        and all(character in _LOWER_HEX for character in payload)
    )


def _present(value: str) -> bool:
    return bool(value) and value == value.strip()


def _exact_package_version(value: str) -> bool:
    if not _present(value) or not value[0].isdigit():
        return False
    forbidden = frozenset("<>=*^~,; ")
    allowed_punctuation = frozenset(".!+-_")
    return not any(item in forbidden for item in value) and all(
        item.isalnum() or item in allowed_punctuation for item in value
    )


def _nonempty_unique_strings(values: tuple[str, ...], *, trimmed: bool = True) -> bool:
    return bool(values) and _unique_strings(values, trimmed=trimmed)


def _unique_strings(values: tuple[str, ...], *, trimmed: bool = True) -> bool:
    valid = all(bool(value) and (not trimmed or _present(value)) for value in values)
    return valid and len(values) == len(set(values))


def _nonempty_token_set(values: frozenset[str]) -> bool:
    return bool(values) and _token_set(values)


def _token_set(values: frozenset[str]) -> bool:
    return all(_present(value) for value in values)
