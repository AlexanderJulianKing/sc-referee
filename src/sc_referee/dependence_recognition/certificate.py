"""Small trusted certificate kernel for dependence semantic v1.

The future static analyzer is a proposing component only.  This module knows
none of its lowering machinery: it accepts closed records from :mod:`ir`,
recomputes obligations O1-O13, and either returns one bounded report-only proof
or abstains with ``None``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sc_referee.dependence_core import SAFEGUARD_IDS
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
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

_RECOGNIZED_READER_MODELS = {
    "csv_dictreader_splitlines": "splitlines",
    "csv_dictreader_file": "csv_newline",
}
_RECOGNIZED_DIALECT = "excel"
_RECOGNIZED_TRANSFORMS = frozenset({"identity", "unit_groupby_mean", "unit_groupby_first"})
_UNIT_AGGREGATION_SAFEGUARD = "safeguard:unit-level-aggregation"
_PAIRED_SAFEGUARD = "safeguard:paired-or-blocked-procedure"


@dataclass(frozen=True)
class _ProcedureRegistryEntry:
    resolved_callable: str
    positional_argument_count: int
    keyword_argument_names: tuple[str, ...]
    independence_model: str
    required_safeguard_id: str | None


_PROCEDURE_REGISTRY: tuple[_ProcedureRegistryEntry, ...] = (
    _ProcedureRegistryEntry(
        resolved_callable="scipy.stats.ttest_ind",
        positional_argument_count=2,
        keyword_argument_names=(),
        independence_model="row_independent",
        required_safeguard_id=None,
    ),
    _ProcedureRegistryEntry(
        resolved_callable="scipy.stats.mannwhitneyu",
        positional_argument_count=2,
        keyword_argument_names=(),
        independence_model="row_independent",
        required_safeguard_id=None,
    ),
    _ProcedureRegistryEntry(
        resolved_callable="scipy.stats.ttest_rel",
        positional_argument_count=2,
        keyword_argument_names=(),
        independence_model="paired",
        required_safeguard_id=_PAIRED_SAFEGUARD,
    ),
)


def verify_dependence_certificate(
    certificate: DependenceCertificate,
    *,
    trusted_multiplicity_facts: tuple[UnitKeyMultiplicityFact, ...] = (),
) -> VerifiedDependenceCertificate | None:
    """Accept one complete internally consistent static proof or abstain."""

    if not _certificate_identity_is_closed(certificate):
        return None
    if not _case_binding_is_closed(certificate.case_binding):
        return None

    fact = _multiplicity_fact_is_discharged(
        certificate,
        trusted_multiplicity_facts,
    )
    if fact is None:
        return None
    if not _frame_lineage_is_closed(
        certificate.frame_lineage,
        certificate.case_binding,
        fact,
        certificate.procedure_call,
    ):
        return None
    procedure_entry = _procedure_call_is_registered(
        certificate.procedure_call,
        certificate.case_binding,
        certificate.frame_lineage,
    )
    if procedure_entry is None:
        return None

    expected_safeguard_matches = _expected_safeguard_matches(
        certificate.frame_lineage.transforms,
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

    conclusion: DependenceConclusion = (
        "repeated_units" if fact.repeated_unit_ids else "one_observation_per_unit"
    )
    active_sink_tokens = _sinks_are_closed(certificate, conclusion)
    if active_sink_tokens is None:
        return None
    if not _proof_slice_is_noninterfering(certificate):
        return None
    if not _evidence_is_closed(certificate):
        return None

    return VerifiedDependenceCertificate(
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        case_binding=certificate.case_binding,
        frame_lineage=certificate.frame_lineage,
        procedure_call=certificate.procedure_call,
        conclusion=conclusion,
        repeated_unit_ids=fact.repeated_unit_ids,
        applicable_safeguard_ids=applicable_safeguards,
        domain_fact=fact,
        sink_tokens=active_sink_tokens,
        evidence=tuple(sorted(certificate.evidence)),
        proposed_case_digest=certificate.proposed_case_digest,
        output_ceiling=certificate.output_ceiling,
        wording_ceiling=certificate.wording_ceiling,
    )


def _certificate_identity_is_closed(certificate: DependenceCertificate) -> bool:
    if (
        not _relative_path(certificate.source_path)
        or not _sha256(certificate.source_digest)
        or not _present(certificate.parser_id)
        or not _present(certificate.parser_version)
        or not _sha256(certificate.dependency_closure_digest)
        or not _sha256(certificate.proposed_case_digest)
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
    ):
        return False
    return True


def _case_binding_is_closed(binding: DependenceCaseBinding) -> bool:
    authority = binding.authority
    if (
        not _present(binding.case_id)
        or not _record_ref_is_closed(binding.analysis_target_ref, "analysis")
        or not _record_ref_is_closed(binding.procedure_ref, "procedure")
        or not _record_ref_is_closed(binding.affected_target_ref)
        or binding.affected_target_ref.record_type not in {"result", "claim"}
        or not _present(binding.independent_unit_definition_id)
        or not _nonempty_unique_strings(binding.authorized_key_columns, trimmed=False)
        or not _authority_is_closed(authority)
    ):
        return False
    return (
        authority.analysis_target_ref == binding.analysis_target_ref
        and authority.procedure_ref == binding.procedure_ref
        and authority.independent_unit_definition_id == binding.independent_unit_definition_id
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
    )


def _multiplicity_fact_is_discharged(
    certificate: DependenceCertificate,
    trusted_facts: tuple[UnitKeyMultiplicityFact, ...],
) -> UnitKeyMultiplicityFact | None:
    trusted = set(trusted_facts)
    declared = set(certificate.proven_multiplicity_facts)
    if (
        len(trusted) != len(trusted_facts)
        or len(declared) != len(certificate.proven_multiplicity_facts)
        or trusted != declared
        or len(trusted) != 1
        or any(not _multiplicity_fact_is_closed(fact) for fact in trusted)
    ):
        return None

    obligations = certificate.multiplicity_obligations
    obligation_keys = tuple(_multiplicity_obligation_key(item) for item in obligations)
    expected_key = (
        certificate.frame_lineage.input_binding,
        certificate.frame_lineage.reader,
        certificate.frame_lineage.source_row_domain,
        certificate.case_binding.authorized_key_columns,
    )
    if (
        len(obligation_keys) != len(set(obligation_keys))
        or set(obligation_keys) != {expected_key}
        or len(obligations) != 1
    ):
        return None

    obligation = obligations[0]
    fact = obligation.fact
    if fact is None or fact not in trusted or not _fact_matches_obligation(fact, obligation):
        return None
    used = {fact}
    if used != declared:
        return None
    return fact


def _multiplicity_obligation_key(
    obligation: UnitKeyMultiplicityObligation,
) -> tuple[MaterialInputBinding, ReaderBinding, str, tuple[str, ...]]:
    return (
        obligation.input_binding,
        obligation.reader,
        obligation.row_domain,
        obligation.key_columns,
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


def _multiplicity_fact_is_closed(fact: UnitKeyMultiplicityFact) -> bool:
    if (
        not _present(fact.evidence_id)
        or not _relative_path(fact.path)
        or not _sha256(fact.content_digest)
        or not _record_ref_is_closed(fact.file_ref, "file_record")
        or not _record_ref_is_closed(fact.asset_identity_ref, "asset_identity")
        or not _reader_model_is_recognized(
            fact.reader_form,
            fact.line_model,
            fact.dialect,
        )
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
        or fact.normalization != "byte_exact_utf8"
        or not _unique_strings(fact.declared_missing_value_tokens, trimmed=False)
        or any(not item for item in fact.declared_missing_value_tokens)
        or fact.missing_key_value_count != 0
        or not fact.row_shape_complete
        or fact.row_count < 1
        or fact.row_count > MAX_DEPENDENCE_CSV_DOMAIN_ROWS
        or len(fact.observation_ids) != fact.row_count
        or not _nonempty_unique_strings(fact.observation_ids)
        or len(fact.unit_ids) != fact.row_count
        or any(not _present(item) for item in fact.unit_ids)
    ):
        return False

    counts = Counter(fact.unit_ids)
    expected_multiplicities = tuple(sorted(counts.items()))
    expected_repeated = tuple(sorted(item for item, count in counts.items() if count > 1))
    return (
        fact.distinct_key_count == len(counts)
        and fact.multiplicities == expected_multiplicities
        and fact.repeated_unit_ids == expected_repeated
    )


def _frame_lineage_is_closed(
    lineage: FrameLineage,
    case_binding: DependenceCaseBinding,
    fact: UnitKeyMultiplicityFact,
    procedure: ProcedureCall,
) -> bool:
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
        or len(lineage.analyzed_observation_ids) > MAX_V1_MEMBERSHIPS
        or lineage.procedure_call_token != procedure.token
        or not _nonempty_token_set(lineage.relevant_origins)
        or not _nonempty_token_set(lineage.relevant_bindings)
        or not {fact.path, fact.row_domain} <= lineage.relevant_origins
    ):
        return False

    transform_tokens = tuple(item.token for item in lineage.transforms)
    if len(transform_tokens) != len(set(transform_tokens)):
        return False
    current_domain = fact.row_domain
    aggregation_seen = False
    for transform in lineage.transforms:
        checked = _apply_frame_transform(
            transform,
            current_domain=current_domain,
            authorized_key_columns=case_binding.authorized_key_columns,
            aggregation_seen=aggregation_seen,
        )
        if checked is None:
            return False
        current_domain, collapsed = checked
        aggregation_seen = aggregation_seen or collapsed

    if current_domain != lineage.analyzed_row_domain:
        return False
    expected_observations = (
        _ordered_unique(fact.unit_ids) if aggregation_seen else fact.observation_ids
    )
    return (
        lineage.analyzed_observation_ids == expected_observations
        and procedure.analyzed_row_domain == lineage.analyzed_row_domain
        and procedure.frame_lineage_token == lineage.token
    )


def _apply_frame_transform(
    transform: FrameTransform,
    *,
    current_domain: str,
    authorized_key_columns: tuple[str, ...],
    aggregation_seen: bool,
) -> tuple[str, bool] | None:
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
        return current_domain, False
    if (
        aggregation_seen
        or transform.grouping_columns != authorized_key_columns
        or transform.output_row_domain == current_domain
    ):
        return None
    return transform.output_row_domain, True


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
    if (
        not _present(procedure.token)
        or procedure.analysis_target_ref != case_binding.analysis_target_ref
        or procedure.procedure_ref != case_binding.procedure_ref
        or len(procedure.positional_argument_tokens) != registered.positional_argument_count
        or any(not _present(item) for item in procedure.positional_argument_tokens)
        or procedure.keyword_argument_names != registered.keyword_argument_names
        or procedure.frame_lineage_token != lineage.token
        or procedure.analyzed_row_domain != lineage.analyzed_row_domain
        or not _bound_package_version_is_closed(procedure.package_version)
        or procedure.package_version.package_name != "scipy"
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
    transforms: tuple[FrameTransform, ...],
    procedure: ProcedureCall,
    registered: _ProcedureRegistryEntry,
) -> dict[str, frozenset[str]] | None:
    matches: dict[str, set[str]] = {item: set() for item in SAFEGUARD_IDS}
    if _UNIT_AGGREGATION_SAFEGUARD not in matches or _PAIRED_SAFEGUARD not in matches:
        return None
    matches[_UNIT_AGGREGATION_SAFEGUARD].update(
        transform.token
        for transform in transforms
        if transform.operation in {"unit_groupby_mean", "unit_groupby_first"}
    )
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
    required_active = {
        certificate.frame_lineage.reader.token,
        certificate.frame_lineage.token,
        certificate.procedure_call.token,
        *(item.token for item in certificate.frame_lineage.transforms),
        *(item.token for item in certificate.sinks),
    }
    required_tokens = (
        certificate.frame_lineage.reader.token,
        certificate.frame_lineage.token,
        certificate.procedure_call.token,
        *(item.token for item in certificate.frame_lineage.transforms),
        *(item.token for item in certificate.sinks),
    )
    if (
        len(required_tokens) != len(set(required_tokens))
        or not required_active <= active_constructs
    ):
        return None

    present: list[str] = []
    for safeguard_id in SAFEGUARD_IDS:
        check = checks_by_id[safeguard_id]
        expected = expected_matches[safeguard_id]
        if not _safeguard_binding_is_exact(check, certificate.case_binding):
            return None
        if (
            not _nonempty_unique_strings(check.evidence_ids)
            or not _present(check.basis)
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
) -> bool:
    return (
        _present(sink.token)
        and _relative_path(sink.path)
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


def _proof_slice_is_noninterfering(certificate: DependenceCertificate) -> bool:
    relevant_origins = {
        certificate.frame_lineage.input_binding.path,
        certificate.frame_lineage.source_row_domain,
        certificate.frame_lineage.analyzed_row_domain,
        *certificate.frame_lineage.relevant_origins,
        *(origin for sink in certificate.sinks for origin in sink.relevant_origins),
    }
    relevant_bindings = {
        certificate.frame_lineage.token,
        certificate.procedure_call.token,
        certificate.procedure_call.result_token,
        *certificate.frame_lineage.relevant_bindings,
        *(binding for sink in certificate.sinks for binding in sink.relevant_bindings),
    }
    for effect in certificate.effects:
        if (
            not _token_set(effect.reads)
            or not _token_set(effect.writes)
            or not _token_set(effect.aliases)
            or not _present(effect.reason)
        ):
            return False
        touches_binding = "*" in effect.writes or bool(effect.writes & relevant_bindings)
        touches_origin = "*" in effect.aliases or bool(effect.aliases & relevant_origins)
        raising_on_slice = effect.may_raise and bool(effect.reads & relevant_origins)
        if touches_binding or touches_origin or raising_on_slice:
            return False
    for unknown in certificate.unknowns:
        if not _present(unknown.reason) or "*" in unknown.origins:
            return False
        if unknown.origins & relevant_origins:
            return False
    return True


def _evidence_is_closed(certificate: DependenceCertificate) -> bool:
    if not certificate.evidence or len(set(certificate.evidence)) != len(certificate.evidence):
        return False
    for point in certificate.evidence:
        if (
            point.path != certificate.source_path
            or point.start_line < 1
            or point.end_line < point.start_line
            or point.start_column < 1
            or point.end_column < 1
            or (point.end_line == point.start_line and point.end_column < point.start_column)
        ):
            return False
    return True


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


def _ordered_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _relative_path(value: str) -> bool:
    return bool(value) and not value.startswith("/") and ".." not in value.split("/")


def _sha256(value: str) -> bool:
    if not value.startswith("sha256:") or len(value) != 71:
        return False
    try:
        int(value.removeprefix("sha256:"), 16)
    except ValueError:
        return False
    return True


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
