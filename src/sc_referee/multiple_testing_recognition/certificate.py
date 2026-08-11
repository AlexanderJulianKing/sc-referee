"""Trusted certificate kernel for multiple-testing recognition v1.

The future analyzer is proposal-only.  This module reparses one frozen Python
module under the Python 3.11 AST grammar, recognizes only the bounded shapes in
Experiment 0059, expands the list-comprehension battery against an independently
trusted ordered family fact, and derives every position and family relation.
It never imports or executes project-authored code.
"""

from __future__ import annotations

import ast
import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import cast

from sc_referee.calculation_checks.bh import benjamini_hochberg
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.multiple_testing_recognition.ir import (
    MAX_MULTIPLE_TESTING_AST_NODES,
    MAX_MULTIPLE_TESTING_EVIDENCE_DECLARATIONS,
    MAX_MULTIPLE_TESTING_SOURCE_BYTES,
    MAX_PVALUE_FAMILY_COLUMNS,
    MAX_PVALUE_FAMILY_FIELD_BYTES,
    MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES,
    MAX_PVALUE_FAMILY_ROWS,
    MAX_PVALUE_FAMILY_SOURCE_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_COLUMNS,
    MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_ROWS,
    MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES,
    RECOGNIZED_READER_MODELS,
    REQUIRED_SCOPE_BASES,
    CorrectionCall,
    EvidenceDeclaration,
    EvidencePoint,
    FamilyAuthorization,
    FamilyDomainObligation,
    FullFamilyProjectionObligation,
    MaterialInputBinding,
    MultipleTestingCaseBinding,
    MultipleTestingCertificate,
    MultipleTestingConclusion,
    PValueFamilyFact,
    RecordRef,
    ReportFamilyBinding,
    TestArgumentDomainFact,
    TestArgumentDomainObligation,
    TestBatteryObligation,
    TestResultPosition,
    VerifiedMultipleTestingCertificate,
)

_LOWER_HEX = frozenset("0123456789abcdef")
_PARSER_ID = "python-ast"
_PARSER_VERSION = "3.11"
_DIALECT = "excel"
_NORMALIZATIONS = {
    "splitlines": "splitlines_rejoined_utf8",
    "csv_newline": "byte_exact_utf8",
}
_READER_MODELS = dict(RECOGNIZED_READER_MODELS)
_TEST_CALLABLES = frozenset(
    {
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
    }
)
_REPOSITORY_BH_CALLABLE = "sc_referee.calculation_checks.bh.benjamini_hochberg"
_STATSMODELS_BH_CALLABLE = "statsmodels.stats.multitest.multipletests"
_CORRECTION_CALLABLES = frozenset({_STATSMODELS_BH_CALLABLE})
_UNSIGNED_FIXED_POINT_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?", flags=re.ASCII)
_MEASUREMENT_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", flags=re.ASCII)
_PROHIBITED_AST_TYPES = (
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.AsyncWith,
    ast.AugAssign,
    ast.Await,
    ast.ClassDef,
    ast.Delete,
    ast.For,
    ast.FunctionDef,
    ast.GeneratorExp,
    ast.If,
    ast.IfExp,
    ast.Lambda,
    ast.Match,
    ast.NamedExpr,
    ast.SetComp,
    ast.Try,
    ast.TryStar,
    ast.While,
    ast.With,
    ast.Yield,
    ast.YieldFrom,
)


@dataclass(frozen=True)
class _FactResolution:
    fact: PValueFamilyFact
    decimals: tuple[Decimal, ...]


@dataclass(frozen=True)
class _ArgumentFactResolution:
    fact: TestArgumentDomainFact
    cell_tokens: tuple[str, ...]
    vectors_by_hypothesis: dict[str, tuple[str, str]]


@dataclass(frozen=True)
class _SourceReplay:
    reader_token: str
    projection_token: str
    battery_construct_id: str
    element_call_template_token: str
    argument_template_tokens: tuple[str, str]
    measurement_reader_token: str
    left_projection_token: str
    right_projection_token: str
    measurement_rows_name: str
    left_argument_name: str
    right_argument_name: str
    correction_construct_token: str
    report_construct_token: str
    sink_token: str
    corrected_positions: tuple[int, ...]
    syntactic_construct_tokens: frozenset[str]
    complete_test_call_tokens: frozenset[str]


def verify_multiple_testing_certificate(
    certificate: MultipleTestingCertificate,
    *,
    frozen_source_bytes: bytes,
    trusted_family_facts: tuple[PValueFamilyFact, ...] = (),
    trusted_argument_facts: tuple[TestArgumentDomainFact, ...] = (),
    trusted_family_authorizations: tuple[FamilyAuthorization, ...] = (),
) -> VerifiedMultipleTestingCertificate | None:
    """Accept one closed subset/full-family proof or fail closed with ``None``."""

    source = _closed_source(certificate, frozen_source_bytes)
    if source is None or not _case_binding_is_closed(certificate.case_binding):
        return None
    authority = _trusted_authorization(
        certificate.case_binding,
        trusted_family_authorizations,
    )
    if authority is None:
        return None
    fact_resolution = _trusted_fact(
        certificate,
        trusted_family_facts,
        authority,
    )
    if fact_resolution is None:
        return None
    argument_resolution = _trusted_argument_fact(certificate, trusted_argument_facts)
    if argument_resolution is None:
        return None
    if not _argument_family_join_is_total(
        fact_resolution.fact,
        argument_resolution.fact,
    ):
        return None
    replay = _replay_bounded_source(
        certificate,
        source,
        fact_resolution.fact,
        argument_resolution.fact,
    )
    if replay is None or replay.battery_construct_id != authority.battery_construct_id:
        return None
    if not _scope_equation_is_closed(certificate, replay):
        return None

    positions = _derive_result_positions(
        certificate,
        fact_resolution.fact,
        argument_resolution,
        replay,
    )
    if positions is None:
        return None
    performed = tuple(item.result_token for item in positions)
    corrected = tuple(performed[index] for index in replay.corrected_positions)
    reported = performed
    is_subset = (
        0 < len(corrected) < len(performed)
        and Counter(corrected) <= Counter(performed)
        and Counter(corrected) != Counter(performed)
    )
    is_complete = bool(performed) and Counter(corrected) == Counter(performed)
    if not ((is_subset or is_complete) and Counter(reported) == Counter(performed)):
        return None
    conclusion: MultipleTestingConclusion = (
        "correction_subset" if is_subset else "complete_family_correction"
    )
    adjusted = _trusted_bh_recomputation(
        certificate.correction_calls[0],
        fact_resolution.decimals,
        replay.corrected_positions,
    )
    if adjusted is None:
        return None
    sink_tokens = _report_and_sink_are_closed(certificate, fact_resolution.fact, replay)
    if sink_tokens is None:
        return None
    if not _proof_slice_is_noninterfering(
        certificate,
        fact_resolution.fact,
        argument_resolution,
        replay,
        positions,
    ):
        return None
    if not _evidence_is_closed(
        certificate,
        fact_resolution.fact,
        argument_resolution.fact,
    ):
        return None

    return VerifiedMultipleTestingCertificate(
        source_path=certificate.source_path,
        source_digest=certificate.source_digest,
        conclusion=conclusion,
        case_binding=certificate.case_binding,
        family_authorization=authority,
        family_fact=fact_resolution.fact,
        test_argument_fact=argument_resolution.fact,
        test_result_positions=positions,
        performed_result_tokens=performed,
        corrected_result_tokens=corrected,
        reported_result_tokens=reported,
        corrected_positions=replay.corrected_positions,
        recomputed_adjusted_pvalues=adjusted,
        sink_tokens=sink_tokens,
        evidence=tuple(sorted(certificate.evidence)),
        proposed_case_digest=certificate.proposed_case_digest,
        output_ceiling=certificate.output_ceiling,
        wording_ceiling=certificate.wording_ceiling,
    )


def multiple_testing_case_digest(binding: MultipleTestingCaseBinding) -> str:
    """Return the exact proposal digest for one closed case binding."""

    return semantic_digest(asdict(binding))


def multiple_testing_replay_digest(certificate: MultipleTestingCertificate) -> str:
    """Bind parser/source identity and every analyzer-supplied completeness set."""

    scopes = [
        {
            "battery_construct_id": item.battery_construct_id,
            "iterable_row_domain": item.iterable_row_domain,
            "complete": sorted(item.complete_test_call_tokens),
            "modeled": sorted(item.modeled_test_call_tokens),
            "proven_dead": sorted(item.proven_dead_test_call_tokens),
            "corrected": sorted(item.corrected_test_call_tokens),
            "bases": list(item.bases),
        }
        for item in certificate.family_scope_checks
    ]
    return semantic_digest(
        {
            "source_path": certificate.source_path,
            "source_digest": certificate.source_digest,
            "parser_id": certificate.parser_id,
            "parser_version": certificate.parser_version,
            "source_extent": asdict(certificate.source_extent),
            "all_syntactic_construct_tokens": sorted(certificate.all_syntactic_construct_tokens),
            "dead_syntactic_construct_tokens": sorted(certificate.dead_syntactic_construct_tokens),
            "all_sink_tokens": sorted(certificate.all_sink_tokens),
            "dead_sink_tokens": sorted(certificate.dead_sink_tokens),
            "scope_checks": scopes,
            "test_argument_domain_obligations": [
                asdict(item) for item in certificate.test_argument_domain_obligations
            ],
        }
    )


def family_observation_token(
    path: str,
    content_digest: str,
    row_domain: str,
    row_ordinal: int,
) -> str:
    return "family-observation:" + semantic_digest(
        {
            "schema": "pvalue-family-observation-v1",
            "path": path,
            "content_digest": content_digest,
            "row_domain": row_domain,
            "row_ordinal": row_ordinal,
        }
    )


def family_hypothesis_token(
    key_columns: tuple[str, ...],
    key_values: tuple[str, ...],
) -> str:
    return "family-hypothesis:" + semantic_digest(
        {
            "schema": "pvalue-family-hypothesis-v1",
            "key_columns": key_columns,
            "key_values": key_values,
        }
    )


def family_pvalue_token(
    row_domain: str,
    position: int,
    hypothesis_token: str,
    pvalue_column: str,
) -> str:
    return "family-pvalue:" + semantic_digest(
        {
            "schema": "pvalue-family-position-v1",
            "row_domain": row_domain,
            "position": position,
            "hypothesis_token": hypothesis_token,
            "pvalue_column": pvalue_column,
        }
    )


def test_result_token(
    source_digest: str,
    battery_construct_id: str,
    element_call_template_token: str,
    iterable_row_domain: str,
    position: int,
    hypothesis_token: str,
) -> str:
    return "multiple-testing-result:" + semantic_digest(
        {
            "schema": "multiple-testing-result-position-v1",
            "source_digest": source_digest,
            "battery_construct_id": battery_construct_id,
            "element_call_template_token": element_call_template_token,
            "iterable_row_domain": iterable_row_domain,
            "sequence_position": position,
            "hypothesis_token": hypothesis_token,
        }
    )


def test_argument_cell_token(
    row_domain: str,
    hypothesis_token: str,
    side: str,
    column: str,
    binary64_hex: str,
) -> str:
    """Derive one kernel-owned measurement-cell identity."""

    return "test-argument-cell:" + semantic_digest(
        {
            "schema": "test-argument-cell-v1",
            "row_domain": row_domain,
            "hypothesis_token": hypothesis_token,
            "side": side,
            "column": column,
            "binary64_hex": binary64_hex,
        }
    )


def test_argument_vector_token(
    row_domain: str,
    hypothesis_token: str,
    side: str,
    columns: tuple[str, ...],
    binary64_hex: tuple[str, ...],
) -> str:
    """Derive one kernel-owned position-independent keyed operand vector."""

    return "test-argument-vector:" + semantic_digest(
        {
            "schema": "test-argument-vector-v1",
            "row_domain": row_domain,
            "hypothesis_token": hypothesis_token,
            "side": side,
            "columns": columns,
            "binary64_hex": binary64_hex,
        }
    )


def source_construct_token(kind: str, source_digest: str, point: EvidencePoint) -> str:
    """Return the stable static token formula also used by future proposers."""

    return _source_token(kind, source_digest, point)


def _closed_source(
    certificate: MultipleTestingCertificate,
    frozen_source_bytes: bytes,
) -> str | None:
    if (
        not isinstance(frozen_source_bytes, bytes)
        or not frozen_source_bytes
        or len(frozen_source_bytes) > MAX_MULTIPLE_TESTING_SOURCE_BYTES
        or frozen_source_bytes.startswith(b"\xef\xbb\xbf")
        or not _relative_path(certificate.source_path)
        or not _sha256(certificate.source_digest)
        or sha256_digest(frozen_source_bytes) != certificate.source_digest
        or certificate.parser_id != _PARSER_ID
        or certificate.parser_version != _PARSER_VERSION
        or not _sha256(certificate.dependency_closure_digest)
        or not _sha256(certificate.proposed_case_digest)
        or certificate.proposed_case_digest
        != multiple_testing_case_digest(certificate.case_binding)
        or certificate.replay_digest != multiple_testing_replay_digest(certificate)
        or certificate.output_ceiling != "report_only"
        or certificate.wording_ceiling != "supported_normal_path_static_relationship_only"
        or not _source_extent_is_closed(certificate.source_extent, certificate.source_path)
        or not certificate.all_syntactic_construct_tokens
        or certificate.dead_syntactic_construct_tokens
        or not certificate.all_sink_tokens
        or certificate.dead_sink_tokens
    ):
        return None
    try:
        source = frozen_source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if "\x00" in source or certificate.source_extent != _whole_source_extent(
        certificate.source_path, source
    ):
        return None
    return source


def _case_binding_is_closed(binding: MultipleTestingCaseBinding) -> bool:
    return (
        _present(binding.case_id)
        and _record_ref(binding.analysis_target_ref, "analysis")
        and _record_ref(binding.correction_procedure_ref, "procedure")
        and _record_ref(binding.affected_target_ref)
        and binding.affected_target_ref.record_type in {"result", "claim"}
        and _present(binding.family_definition_id)
        and _present(binding.battery_construct_id)
        and _present(binding.iterable_row_domain)
        and _nonempty_unique_strings(binding.authorized_family_key_columns, trimmed=False)
        and _relative_path(binding.family_input_path)
        and _sha256(binding.family_input_content_digest)
        and _relative_path(binding.measurement_input_path)
        and binding.measurement_input_path != binding.family_input_path
        and _sha256(binding.measurement_input_content_digest)
        and _nonempty_unique_strings(binding.measurement_key_columns, trimmed=False)
        and _nonempty_unique_strings(binding.left_measurement_columns, trimmed=False)
        and len(binding.left_measurement_columns) >= 2
        and _nonempty_unique_strings(binding.right_measurement_columns, trimmed=False)
        and len(binding.right_measurement_columns) >= 2
        and len(
            {
                *binding.measurement_key_columns,
                *binding.left_measurement_columns,
                *binding.right_measurement_columns,
            }
        )
        == len(binding.measurement_key_columns)
        + len(binding.left_measurement_columns)
        + len(binding.right_measurement_columns)
        and binding.measurement_reader_model in _READER_MODELS
    )


def _trusted_authorization(
    binding: MultipleTestingCaseBinding,
    trusted: tuple[FamilyAuthorization, ...],
) -> FamilyAuthorization | None:
    if len(trusted) != 1:
        return None
    authority = trusted[0]
    if not _authorization_is_closed(authority):
        return None
    if (
        authority.analysis_target_ref,
        authority.correction_procedure_ref,
        authority.family_definition_id,
        authority.battery_construct_id,
        authority.iterable_row_domain,
        authority.authorized_family_key_columns,
        authority.family_input_path,
        authority.family_input_content_digest,
    ) != (
        binding.analysis_target_ref,
        binding.correction_procedure_ref,
        binding.family_definition_id,
        binding.battery_construct_id,
        binding.iterable_row_domain,
        binding.authorized_family_key_columns,
        binding.family_input_path,
        binding.family_input_content_digest,
    ):
        return None
    return authority


def _authorization_is_closed(authority: FamilyAuthorization) -> bool:
    return (
        authority.record_type == "human_pvalue_family_authorization"
        and _present(authority.record_id)
        and _present(authority.actor_id)
        and authority.authority_state == "authorized"
        and _record_ref(authority.analysis_target_ref, "analysis")
        and _record_ref(authority.correction_procedure_ref, "procedure")
        and _present(authority.family_definition_id)
        and _present(authority.battery_construct_id)
        and _present(authority.iterable_row_domain)
        and _nonempty_unique_strings(authority.authorized_family_key_columns, trimmed=False)
        and authority.family_member_rule == "all_rows"
        and _relative_path(authority.family_input_path)
        and _sha256(authority.family_input_content_digest)
    )


def _trusted_fact(
    certificate: MultipleTestingCertificate,
    trusted: tuple[PValueFamilyFact, ...],
    authority: FamilyAuthorization,
) -> _FactResolution | None:
    if len(certificate.family_domain_obligations) != 1 or len(trusted) != 1:
        return None
    obligation = certificate.family_domain_obligations[0]
    fact = trusted[0]
    if not _domain_obligation_is_closed(obligation):
        return None
    expected_input = obligation.input_binding
    if (
        expected_input.path,
        expected_input.content_digest,
        obligation.iterable_row_domain,
        obligation.hypothesis_key_columns,
    ) != (
        authority.family_input_path,
        authority.family_input_content_digest,
        authority.iterable_row_domain,
        authority.authorized_family_key_columns,
    ):
        return None
    if (
        fact.path,
        fact.content_digest,
        fact.file_ref,
        fact.asset_identity_ref,
        fact.reader_form,
        fact.line_model,
        fact.dialect,
        fact.row_domain,
        fact.hypothesis_key_columns,
        fact.pvalue_column,
    ) != (
        expected_input.path,
        expected_input.content_digest,
        expected_input.file_ref,
        expected_input.asset_identity_ref,
        obligation.reader_form,
        obligation.line_model,
        obligation.dialect,
        obligation.iterable_row_domain,
        obligation.hypothesis_key_columns,
        obligation.pvalue_column,
    ):
        return None
    return _fact_is_closed(fact)


def _domain_obligation_is_closed(obligation: FamilyDomainObligation) -> bool:
    return (
        _material_input_is_closed(obligation.input_binding)
        and _reader_model(obligation.reader_form, obligation.line_model, obligation.dialect)
        and _present(obligation.iterable_row_domain)
        and _nonempty_unique_strings(obligation.hypothesis_key_columns, trimmed=False)
        and bool(obligation.pvalue_column)
        and obligation.pvalue_column not in obligation.hypothesis_key_columns
        and _evidence_point_is_closed(obligation.reader_assignment_span)
        and _nonempty_unique_strings(obligation.reader_evidence_ids)
    )


def _fact_is_closed(fact: PValueFamilyFact) -> _FactResolution | None:
    aligned_lengths = {
        fact.row_count,
        len(fact.observation_tokens),
        len(fact.key_value_tuples),
        len(fact.hypothesis_tokens),
        len(fact.raw_pvalue_lexemes),
        len(fact.canonical_pvalue_decimals),
        len(fact.pvalue_tokens),
    }
    if (
        not _present(fact.evidence_id)
        or not _relative_path(fact.path)
        or not _sha256(fact.content_digest)
        or not _record_ref(fact.file_ref, "file_record")
        or not _record_ref(fact.asset_identity_ref, "asset_identity")
        or not _reader_model(fact.reader_form, fact.line_model, fact.dialect)
        or fact.normalization != _NORMALIZATIONS.get(fact.line_model)
        or (fact.line_model == "splitlines" and not fact.splitlines_only_separators_absent)
        or not _present(fact.row_domain)
        or not 0 < fact.source_byte_count <= MAX_PVALUE_FAMILY_SOURCE_BYTES
        or not 0 < len(fact.header) <= MAX_PVALUE_FAMILY_COLUMNS
        or len(fact.header) != len(set(fact.header))
        or any(not value for value in fact.header)
        or not _nonempty_unique_strings(fact.hypothesis_key_columns, trimmed=False)
        or any(column not in fact.header for column in fact.hypothesis_key_columns)
        or not fact.pvalue_column
        or fact.pvalue_column not in fact.header
        or fact.pvalue_column in fact.hypothesis_key_columns
        or not _unique_strings(fact.declared_missing_value_tokens, trimmed=False)
        or fact.missing_key_value_count != 0
        or fact.missing_pvalue_count != 0
        or not fact.row_shape_complete
        or not 0 < fact.row_count <= MAX_PVALUE_FAMILY_ROWS
        or aligned_lengths != {fact.row_count}
        or len(set(fact.observation_tokens)) != fact.row_count
        or len(set(fact.key_value_tuples)) != fact.row_count
        or len(set(fact.hypothesis_tokens)) != fact.row_count
        or len(set(fact.pvalue_tokens)) != fact.row_count
        or _fact_record_size(fact) > MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES
    ):
        return None
    every_field = (
        *fact.header,
        *fact.declared_missing_value_tokens,
        *fact.raw_pvalue_lexemes,
        *fact.canonical_pvalue_decimals,
        *(value for key in fact.key_value_tuples for value in key),
    )
    if any(len(value.encode("utf-8")) > MAX_PVALUE_FAMILY_FIELD_BYTES for value in every_field):
        return None

    expected_observations: list[str] = []
    expected_hypotheses: list[str] = []
    expected_pvalues: list[str] = []
    decimals: list[Decimal] = []
    for position, (key_values, raw, canonical) in enumerate(
        zip(
            fact.key_value_tuples,
            fact.raw_pvalue_lexemes,
            fact.canonical_pvalue_decimals,
            strict=True,
        )
    ):
        if (
            len(key_values) != len(fact.hypothesis_key_columns)
            or any(not value or value in fact.declared_missing_value_tokens for value in key_values)
            or not raw
            or raw != raw.strip()
            or raw in fact.declared_missing_value_tokens
        ):
            return None
        parsed = _exact_decimal(raw)
        if parsed is None or canonical != _canonical_decimal(parsed):
            return None
        hypothesis = family_hypothesis_token(fact.hypothesis_key_columns, key_values)
        expected_observations.append(
            family_observation_token(
                fact.path,
                fact.content_digest,
                fact.row_domain,
                position + 1,
            )
        )
        expected_hypotheses.append(hypothesis)
        expected_pvalues.append(
            family_pvalue_token(
                fact.row_domain,
                position,
                hypothesis,
                fact.pvalue_column,
            )
        )
        decimals.append(parsed)
    if (
        fact.observation_tokens != tuple(expected_observations)
        or fact.hypothesis_tokens != tuple(expected_hypotheses)
        or fact.pvalue_tokens != tuple(expected_pvalues)
    ):
        return None
    return _FactResolution(fact, tuple(decimals))


def _trusted_argument_fact(
    certificate: MultipleTestingCertificate,
    trusted: tuple[TestArgumentDomainFact, ...],
) -> _ArgumentFactResolution | None:
    if len(certificate.test_argument_domain_obligations) != 1 or len(trusted) != 1:
        return None
    obligation = certificate.test_argument_domain_obligations[0]
    fact = trusted[0]
    binding = certificate.case_binding
    if not _argument_obligation_is_closed(obligation):
        return None
    expected = obligation.input_binding
    if (
        binding.measurement_input_path,
        binding.measurement_input_content_digest,
        binding.measurement_key_columns,
        binding.left_measurement_columns,
        binding.right_measurement_columns,
        binding.measurement_reader_model,
    ) != (
        expected.path,
        expected.content_digest,
        obligation.measurement_key_columns,
        obligation.left_measurement_columns,
        obligation.right_measurement_columns,
        obligation.reader_form,
    ):
        return None
    if (
        fact.path,
        fact.content_digest,
        fact.file_ref,
        fact.asset_identity_ref,
        fact.reader_form,
        fact.line_model,
        fact.dialect,
        fact.row_domain,
        fact.measurement_key_columns,
        fact.left_measurement_columns,
        fact.right_measurement_columns,
    ) != (
        expected.path,
        expected.content_digest,
        expected.file_ref,
        expected.asset_identity_ref,
        obligation.reader_form,
        obligation.line_model,
        obligation.dialect,
        obligation.measurement_row_domain,
        obligation.measurement_key_columns,
        obligation.left_measurement_columns,
        obligation.right_measurement_columns,
    ):
        return None
    return _argument_fact_is_closed(fact)


def _argument_obligation_is_closed(obligation: TestArgumentDomainObligation) -> bool:
    columns = (
        *obligation.measurement_key_columns,
        *obligation.left_measurement_columns,
        *obligation.right_measurement_columns,
    )
    points = (
        obligation.reader_assignment_span,
        obligation.left_projection_span,
        obligation.right_projection_span,
        obligation.left_key_span,
        obligation.right_key_span,
        obligation.left_value_span,
        obligation.right_value_span,
    )
    return (
        _material_input_is_closed(obligation.input_binding)
        and _reader_model(obligation.reader_form, obligation.line_model, obligation.dialect)
        and _present(obligation.measurement_row_domain)
        and _present(obligation.measurement_rows_name)
        and _present(obligation.left_argument_name)
        and _present(obligation.right_argument_name)
        and len(
            {
                obligation.measurement_rows_name,
                obligation.left_argument_name,
                obligation.right_argument_name,
            }
        )
        == 3
        and _nonempty_unique_strings(obligation.measurement_key_columns, trimmed=False)
        and _nonempty_unique_strings(obligation.left_measurement_columns, trimmed=False)
        and len(obligation.left_measurement_columns) >= 2
        and _nonempty_unique_strings(obligation.right_measurement_columns, trimmed=False)
        and len(obligation.right_measurement_columns) >= 2
        and len(columns) == len(set(columns))
        and all(_evidence_point_is_closed(point) for point in points)
        and len(obligation.evidence_ids) == len(points)
        and _nonempty_unique_strings(obligation.evidence_ids)
    )


def _argument_fact_is_closed(
    fact: TestArgumentDomainFact,
) -> _ArgumentFactResolution | None:
    aligned = {
        fact.row_count,
        len(fact.observation_tokens),
        len(fact.key_value_tuples),
        len(fact.hypothesis_tokens),
        len(fact.left_raw_measurement_lexemes),
        len(fact.right_raw_measurement_lexemes),
        len(fact.left_binary64_hex),
        len(fact.right_binary64_hex),
    }
    selected_columns = (
        *fact.measurement_key_columns,
        *fact.left_measurement_columns,
        *fact.right_measurement_columns,
    )
    if (
        not _present(fact.evidence_id)
        or not _relative_path(fact.path)
        or not _sha256(fact.content_digest)
        or not _record_ref(fact.file_ref, "file_record")
        or not _record_ref(fact.asset_identity_ref, "asset_identity")
        or not _reader_model(fact.reader_form, fact.line_model, fact.dialect)
        or fact.normalization != _NORMALIZATIONS.get(fact.line_model)
        or (fact.line_model == "splitlines" and not fact.splitlines_only_separators_absent)
        or not _present(fact.row_domain)
        or not 0 < fact.source_byte_count <= MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES
        or not 0 < len(fact.header) <= MAX_TEST_ARGUMENT_DOMAIN_COLUMNS
        or len(fact.header) != len(set(fact.header))
        or any(not value for value in fact.header)
        or not _nonempty_unique_strings(fact.measurement_key_columns, trimmed=False)
        or not _nonempty_unique_strings(fact.left_measurement_columns, trimmed=False)
        or len(fact.left_measurement_columns) < 2
        or not _nonempty_unique_strings(fact.right_measurement_columns, trimmed=False)
        or len(fact.right_measurement_columns) < 2
        or len(selected_columns) != len(set(selected_columns))
        or set(selected_columns) != set(fact.header)
        or len(selected_columns) != len(fact.header)
        or fact.declared_missing_value_tokens
        or fact.missing_key_value_count != 0
        or fact.missing_measurement_value_count != 0
        or not fact.row_shape_complete
        or not 0 < fact.row_count <= MAX_TEST_ARGUMENT_DOMAIN_ROWS
        or aligned != {fact.row_count}
        or len(set(fact.observation_tokens)) != fact.row_count
        or len(set(fact.key_value_tuples)) != fact.row_count
        or len(set(fact.hypothesis_tokens)) != fact.row_count
        or _argument_fact_record_size(fact) > MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES
    ):
        return None
    every_field = (
        *fact.header,
        *(value for row in fact.key_value_tuples for value in row),
        *(value for row in fact.left_raw_measurement_lexemes for value in row),
        *(value for row in fact.right_raw_measurement_lexemes for value in row),
        *(value for row in fact.left_binary64_hex for value in row),
        *(value for row in fact.right_binary64_hex for value in row),
    )
    if any(
        len(value.encode("utf-8")) > MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES for value in every_field
    ):
        return None
    observations: list[str] = []
    hypotheses: list[str] = []
    cell_tokens: list[str] = []
    vectors: dict[str, tuple[str, str]] = {}
    rows = zip(
        fact.key_value_tuples,
        fact.left_raw_measurement_lexemes,
        fact.right_raw_measurement_lexemes,
        fact.left_binary64_hex,
        fact.right_binary64_hex,
        strict=True,
    )
    for position, (key, left_raw, right_raw, left_hex, right_hex) in enumerate(rows):
        if (
            len(key) != len(fact.measurement_key_columns)
            or any(not value for value in key)
            or len(left_raw) != len(fact.left_measurement_columns)
            or len(right_raw) != len(fact.right_measurement_columns)
            or len(left_hex) != len(left_raw)
            or len(right_hex) != len(right_raw)
        ):
            return None
        hypothesis = family_hypothesis_token(fact.measurement_key_columns, key)
        observations.append(
            _argument_observation_token(
                fact.path,
                fact.content_digest,
                fact.row_domain,
                position + 1,
            )
        )
        hypotheses.append(hypothesis)
        for side, columns, raw_values, hex_values in (
            ("left", fact.left_measurement_columns, left_raw, left_hex),
            ("right", fact.right_measurement_columns, right_raw, right_hex),
        ):
            for column, raw, binary_hex in zip(columns, raw_values, hex_values, strict=True):
                parsed = _exact_measurement(raw)
                if parsed is None or parsed.hex() != binary_hex:
                    return None
                cell_tokens.append(
                    test_argument_cell_token(
                        fact.row_domain,
                        hypothesis,
                        side,
                        column,
                        binary_hex,
                    )
                )
        vectors[hypothesis] = (
            test_argument_vector_token(
                fact.row_domain,
                hypothesis,
                "left",
                fact.left_measurement_columns,
                left_hex,
            ),
            test_argument_vector_token(
                fact.row_domain,
                hypothesis,
                "right",
                fact.right_measurement_columns,
                right_hex,
            ),
        )
    if (
        fact.observation_tokens != tuple(observations)
        or fact.hypothesis_tokens != tuple(hypotheses)
        or len(vectors) != fact.row_count
        or len(set(cell_tokens)) != len(cell_tokens)
    ):
        return None
    return _ArgumentFactResolution(fact, tuple(cell_tokens), vectors)


def _argument_family_join_is_total(
    family_fact: PValueFamilyFact,
    argument_fact: TestArgumentDomainFact,
) -> bool:
    """Independently prove the keyed join without relying on row position."""

    return (
        argument_fact.measurement_key_columns == family_fact.hypothesis_key_columns
        and argument_fact.row_count == family_fact.row_count
        and len(set(argument_fact.hypothesis_tokens)) == argument_fact.row_count
        and Counter(argument_fact.hypothesis_tokens) == Counter(family_fact.hypothesis_tokens)
    )


def _replay_bounded_source(
    certificate: MultipleTestingCertificate,
    source: str,
    fact: PValueFamilyFact,
    argument_fact: TestArgumentDomainFact,
) -> _SourceReplay | None:
    if not (
        len(certificate.full_family_projections) == 1
        and len(certificate.test_argument_domain_obligations) == 1
        and len(certificate.test_batteries) == 1
        and len(certificate.correction_calls) == 1
        and len(certificate.family_scope_checks) == 1
        and len(certificate.report_bindings) == 1
    ):
        return None
    try:
        tree = ast.parse(
            source,
            filename=certificate.source_path,
            mode="exec",
            type_comments=False,
            feature_version=(3, 11),
        )
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    nodes = tuple(ast.walk(tree))
    if len(nodes) > MAX_MULTIPLE_TESTING_AST_NODES or any(
        isinstance(node, _PROHIBITED_AST_TYPES) for node in nodes
    ):
        return None
    list_comprehensions = [node for node in nodes if isinstance(node, ast.ListComp)]
    dict_comprehensions = [node for node in nodes if isinstance(node, ast.DictComp)]
    if len(list_comprehensions) != 2 or len(dict_comprehensions) != 2:
        return None

    projection = certificate.full_family_projections[0]
    argument = certificate.test_argument_domain_obligations[0]
    battery = certificate.test_batteries[0]
    correction = certificate.correction_calls[0]
    report = certificate.report_bindings[0]
    if (
        correction.correction_procedure_ref != certificate.case_binding.correction_procedure_ref
        or correction.battery_construct_id != certificate.case_binding.battery_construct_id
        or correction.iterable_row_domain != certificate.case_binding.iterable_row_domain
    ):
        return None
    projection_assign = _unique_node_at(tree, ast.Assign, projection.assignment_span)
    battery_assign = _unique_node_at(tree, ast.Assign, battery.assignment_span)
    correction_call_node = _unique_node_at(tree, ast.Call, correction.call_span)
    report_assign = _unique_node_at(tree, ast.Assign, report.assignment_span)
    sink_node = _unique_node_at(tree, ast.Expr, report.sink_span)
    if not all(
        item is not None
        for item in (
            projection_assign,
            battery_assign,
            correction_call_node,
            report_assign,
            sink_node,
        )
    ):
        return None
    projection_assign = cast(ast.Assign, projection_assign)
    battery_assign = cast(ast.Assign, battery_assign)
    correction_call_node = cast(ast.Call, correction_call_node)
    report_assign = cast(ast.Assign, report_assign)
    sink_node = cast(ast.Expr, sink_node)
    allowed_statements = {
        id(projection_assign),
        id(battery_assign),
        id(report_assign),
        id(sink_node),
    }
    domain = certificate.family_domain_obligations[0]
    reader_node = _unique_node_at(tree, ast.Assign, domain.reader_assignment_span)
    if not isinstance(reader_node, ast.Assign):
        return None
    reader_assign = reader_node
    reader_token = _reader_shape(
        reader_assign,
        domain,
        projection,
        fact,
        certificate.source_digest,
    )
    if reader_token is None:
        return None
    allowed_statements.add(id(reader_assign))
    measurement_reader_node = _unique_node_at(
        tree,
        ast.Assign,
        argument.reader_assignment_span,
    )
    left_projection_node = _unique_node_at(
        tree,
        ast.Assign,
        argument.left_projection_span,
    )
    right_projection_node = _unique_node_at(
        tree,
        ast.Assign,
        argument.right_projection_span,
    )
    if not all(
        isinstance(item, ast.Assign)
        for item in (measurement_reader_node, left_projection_node, right_projection_node)
    ):
        return None
    measurement_reader_assign = cast(ast.Assign, measurement_reader_node)
    left_projection_assign = cast(ast.Assign, left_projection_node)
    right_projection_assign = cast(ast.Assign, right_projection_node)
    measurement_reader_token = _measurement_reader_shape(
        measurement_reader_assign,
        argument,
        argument_fact,
        certificate.source_digest,
    )
    left_projection_checked = _argument_projection_shape(
        left_projection_assign,
        argument,
        argument_fact,
        side="left",
        source_digest=certificate.source_digest,
    )
    right_projection_checked = _argument_projection_shape(
        right_projection_assign,
        argument,
        argument_fact,
        side="right",
        source_digest=certificate.source_digest,
    )
    if (
        measurement_reader_token is None
        or left_projection_checked is None
        or right_projection_checked is None
    ):
        return None
    left_projection_token, left_generator_name = left_projection_checked
    right_projection_token, right_generator_name = right_projection_checked
    allowed_statements.update(
        {
            id(measurement_reader_assign),
            id(left_projection_assign),
            id(right_projection_assign),
        }
    )
    correction_parent = _assign_containing_call(tree, correction_call_node)
    if correction_parent is None:
        return None
    allowed_statements.add(id(correction_parent))
    if any(
        not isinstance(statement, (ast.Import, ast.ImportFrom))
        and id(statement) not in allowed_statements
        for statement in tree.body
    ):
        return None
    if not _required_imports_are_exact(
        tree,
        correction.resolved_callable,
        reader_required=True,
    ):
        return None

    projection_checked = _projection_shape(
        projection_assign,
        projection,
        fact,
        certificate.source_digest,
    )
    if projection_checked is None:
        return None
    projection_token, projection_generator_name = projection_checked
    battery_checked = _battery_shape(
        battery_assign,
        battery,
        projection,
        argument,
        certificate.source_digest,
    )
    if battery_checked is None:
        return None
    (
        derived_battery_id,
        element_call_template_token,
        argument_template_tokens,
        battery_generator_name,
    ) = battery_checked
    if (
        len(
            {
                projection_generator_name,
                left_generator_name,
                right_generator_name,
                battery_generator_name,
            }
        )
        != 4
    ):
        return None

    correction_checked = _correction_shape(
        correction_parent,
        correction_call_node,
        correction,
        battery,
        fact.row_count,
        certificate.source_digest,
    )
    if correction_checked is None:
        return None
    correction_construct_token, corrected_positions = correction_checked
    report_checked = _report_shape(
        report_assign,
        sink_node,
        report,
        projection,
        battery,
        correction,
        certificate.source_path,
        fact.path,
        argument_fact.path,
        certificate.source_digest,
    )
    if report_checked is None:
        return None
    report_construct_token, sink_token = report_checked
    ordered_statements = (
        reader_assign,
        projection_assign,
        measurement_reader_assign,
        left_projection_assign,
        right_projection_assign,
        battery_assign,
        correction_parent,
        report_assign,
        sink_node,
    )
    if not _supported_statement_order(*ordered_statements):
        return None
    correction_local_name = (
        "benjamini_hochberg"
        if correction.resolved_callable == _REPOSITORY_BH_CALLABLE
        else "multipletests"
    )
    assignment_names = tuple(
        _single_name_target(statement)
        for statement in (
            reader_assign,
            projection_assign,
            measurement_reader_assign,
            left_projection_assign,
            right_projection_assign,
            battery_assign,
            correction_parent,
            report_assign,
        )
    )
    comprehension_names = (
        projection_generator_name,
        left_generator_name,
        right_generator_name,
        battery_generator_name,
    )
    fixed_names = ("csv", "scipy", "Path", correction_local_name, "float")
    if (
        any(name is None for name in assignment_names)
        or len(set(assignment_names)) != len(assignment_names)
        or len(set((*assignment_names, *comprehension_names, *fixed_names)))
        != len(assignment_names) + len(comprehension_names) + len(fixed_names)
    ):
        return None
    relevant_names = {
        projection.source_rows_name,
        projection.projected_family_name,
        battery.battery_result_name,
        correction.result_name,
        report.reported_name,
        projection_generator_name,
        left_generator_name,
        right_generator_name,
        battery_generator_name,
        argument.measurement_rows_name,
        argument.left_argument_name,
        argument.right_argument_name,
        "scipy",
        "benjamini_hochberg",
        "Path",
    }
    imported_names = {"scipy", "Path"}
    relevant_names.add(correction_local_name)
    imported_names.add(correction_local_name)
    relevant_names.add("csv")
    imported_names.add("csv")
    if not _relevant_names_have_exact_bindings(
        tree,
        relevant_names,
        allowed_statements,
        imported_names,
    ):
        return None

    complete_calls = frozenset(
        _source_token(
            "test-call-template", certificate.source_digest, _span(node, certificate.source_path)
        )
        for node in nodes
        if isinstance(node, ast.Call)
        and isinstance(_parent_attribute(tree, node), ast.Attribute)
        and cast(ast.Attribute, _parent_attribute(tree, node)).attr == "pvalue"
    )
    derived_constructs = frozenset(
        {
            projection_token,
            derived_battery_id,
            element_call_template_token,
            correction_construct_token,
            report_construct_token,
            sink_token,
            reader_token,
            measurement_reader_token,
            left_projection_token,
            right_projection_token,
        }
    )
    if certificate.all_syntactic_construct_tokens != derived_constructs:
        return None
    return _SourceReplay(
        reader_token=reader_token,
        projection_token=projection_token,
        battery_construct_id=derived_battery_id,
        element_call_template_token=element_call_template_token,
        argument_template_tokens=argument_template_tokens,
        measurement_reader_token=measurement_reader_token,
        left_projection_token=left_projection_token,
        right_projection_token=right_projection_token,
        measurement_rows_name=argument.measurement_rows_name,
        left_argument_name=argument.left_argument_name,
        right_argument_name=argument.right_argument_name,
        correction_construct_token=correction_construct_token,
        report_construct_token=report_construct_token,
        sink_token=sink_token,
        corrected_positions=corrected_positions,
        syntactic_construct_tokens=derived_constructs,
        complete_test_call_tokens=complete_calls,
    )


def _projection_shape(
    assignment: ast.Assign,
    obligation: FullFamilyProjectionObligation,
    fact: PValueFamilyFact,
    source_digest: str,
) -> tuple[str, str] | None:
    target = _single_name_target(assignment)
    value = assignment.value
    if (
        target != obligation.projected_family_name
        or not isinstance(value, ast.ListComp)
        or _span(value, obligation.listcomp_span.path) != obligation.listcomp_span
        or len(value.generators) != 1
        or value.generators[0].is_async
        or value.generators[0].ifs
        or not isinstance(value.generators[0].target, ast.Name)
        or not isinstance(value.generators[0].iter, ast.Name)
        or value.generators[0].iter.id != obligation.source_rows_name
        or obligation.iterable_row_domain != fact.row_domain
        or obligation.hypothesis_key_columns != fact.hypothesis_key_columns
        or obligation.battery_construct_id == ""
    ):
        return None
    row_name = value.generators[0].target.id
    if not _projection_element_matches(
        value.elt,
        row_name,
        obligation.hypothesis_key_columns,
    ):
        return None
    if _span(value.elt, obligation.element_span.path) != obligation.element_span:
        return None
    return (
        _source_token("full-family-projection", source_digest, obligation.assignment_span),
        row_name,
    )


def _reader_shape(
    assignment: ast.Assign,
    obligation: FamilyDomainObligation,
    projection: FullFamilyProjectionObligation,
    fact: PValueFamilyFact,
    source_digest: str,
) -> str | None:
    if (
        _single_name_target(assignment) != projection.source_rows_name
        or _span(assignment, obligation.reader_assignment_span.path)
        != obligation.reader_assignment_span
        or obligation.input_binding.path != fact.path
        or obligation.input_binding.content_digest != fact.content_digest
    ):
        return None
    value = assignment.value
    if not (
        isinstance(value, ast.Call)
        and _dotted_name(value.func) == "list"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Call)
        and _dotted_name(value.args[0].func) == "csv.DictReader"
        and len(value.args[0].args) == 1
        and not value.args[0].keywords
    ):
        return None
    source = value.args[0].args[0]
    if obligation.line_model == "splitlines":
        if not (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "splitlines"
            and not source.args
            and not source.keywords
            and isinstance(source.func.value, ast.Call)
            and isinstance(source.func.value.func, ast.Attribute)
            and source.func.value.func.attr == "read_text"
            and not source.func.value.args
            and _exact_utf8_keyword(source.func.value.keywords)
            and _literal_path_call(source.func.value.func.value, fact.path)
        ):
            return None
    elif obligation.line_model == "csv_newline":
        if not (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "open"
            and not source.args
            and _exact_open_keywords(source.keywords)
            and _literal_path_call(source.func.value, fact.path)
        ):
            return None
    else:
        return None
    return _source_token("family-domain-reader", source_digest, obligation.reader_assignment_span)


def _measurement_reader_shape(
    assignment: ast.Assign,
    obligation: TestArgumentDomainObligation,
    fact: TestArgumentDomainFact,
    source_digest: str,
) -> str | None:
    if (
        _single_name_target(assignment) != obligation.measurement_rows_name
        or _span(assignment, obligation.reader_assignment_span.path)
        != obligation.reader_assignment_span
        or obligation.input_binding.path != fact.path
        or obligation.input_binding.content_digest != fact.content_digest
    ):
        return None
    value = assignment.value
    if not (
        isinstance(value, ast.Call)
        and _dotted_name(value.func) == "list"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Call)
        and _dotted_name(value.args[0].func) == "csv.DictReader"
        and len(value.args[0].args) == 1
        and not value.args[0].keywords
    ):
        return None
    source = value.args[0].args[0]
    if obligation.line_model == "splitlines":
        if not (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "splitlines"
            and not source.args
            and not source.keywords
            and isinstance(source.func.value, ast.Call)
            and isinstance(source.func.value.func, ast.Attribute)
            and source.func.value.func.attr == "read_text"
            and not source.func.value.args
            and _exact_utf8_keyword(source.func.value.keywords)
            and _literal_path_call(source.func.value.func.value, fact.path)
        ):
            return None
    elif obligation.line_model == "csv_newline":
        if not (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "open"
            and not source.args
            and _exact_open_keywords(source.keywords)
            and _literal_path_call(source.func.value, fact.path)
        ):
            return None
    else:
        return None
    return _source_token(
        "test-argument-domain-reader",
        source_digest,
        obligation.reader_assignment_span,
    )


def _argument_projection_shape(
    assignment: ast.Assign,
    obligation: TestArgumentDomainObligation,
    fact: TestArgumentDomainFact,
    *,
    side: str,
    source_digest: str,
) -> tuple[str, str] | None:
    if side == "left":
        expected_target = obligation.left_argument_name
        expected_columns = obligation.left_measurement_columns
        expected_projection_span = obligation.left_projection_span
        expected_key_span = obligation.left_key_span
        expected_value_span = obligation.left_value_span
    elif side == "right":
        expected_target = obligation.right_argument_name
        expected_columns = obligation.right_measurement_columns
        expected_projection_span = obligation.right_projection_span
        expected_key_span = obligation.right_key_span
        expected_value_span = obligation.right_value_span
    else:
        return None
    value = assignment.value
    if (
        _single_name_target(assignment) != expected_target
        or _span(assignment, expected_projection_span.path) != expected_projection_span
        or not isinstance(value, ast.DictComp)
        or len(value.generators) != 1
        or value.generators[0].is_async
        or value.generators[0].ifs
        or not isinstance(value.generators[0].target, ast.Name)
        or not isinstance(value.generators[0].iter, ast.Name)
        or value.generators[0].iter.id != obligation.measurement_rows_name
        or not isinstance(value.value, ast.Tuple)
        or len(value.value.elts) != len(expected_columns)
        or len(expected_columns) < 2
        or _span(value.key, expected_key_span.path) != expected_key_span
        or _span(value.value, expected_value_span.path) != expected_value_span
    ):
        return None
    row_name = value.generators[0].target.id
    if row_name in {
        "float",
        "csv",
        "Path",
        "scipy",
        "multipletests",
        "benjamini_hochberg",
    }:
        return None
    if not _projection_element_matches(
        value.key,
        row_name,
        obligation.measurement_key_columns,
    ):
        return None
    for cell, column in zip(value.value.elts, expected_columns, strict=True):
        if not (
            isinstance(cell, ast.Call)
            and isinstance(cell.func, ast.Name)
            and cell.func.id == "float"
            and len(cell.args) == 1
            and not cell.keywords
            and isinstance(cell.args[0], ast.Subscript)
            and isinstance(cell.args[0].value, ast.Name)
            and cell.args[0].value.id == row_name
            and isinstance(cell.args[0].slice, ast.Constant)
            and cell.args[0].slice.value == column
        ):
            return None
    if (
        obligation.measurement_row_domain != fact.row_domain
        or obligation.measurement_key_columns != fact.measurement_key_columns
        or obligation.left_measurement_columns != fact.left_measurement_columns
        or obligation.right_measurement_columns != fact.right_measurement_columns
    ):
        return None
    return (
        _source_token(
            f"{side}-test-argument-projection",
            source_digest,
            expected_projection_span,
        ),
        row_name,
    )


def _battery_shape(
    assignment: ast.Assign,
    obligation: TestBatteryObligation,
    projection: FullFamilyProjectionObligation,
    argument: TestArgumentDomainObligation,
    source_digest: str,
) -> tuple[str, str, tuple[str, str], str] | None:
    target = _single_name_target(assignment)
    value = assignment.value
    if (
        target != obligation.battery_result_name
        or obligation.resolved_test_callable not in _TEST_CALLABLES
        or obligation.projected_family_name != projection.projected_family_name
        or obligation.iterable_row_domain != projection.iterable_row_domain
        or not isinstance(value, ast.ListComp)
        or _span(value, obligation.listcomp_span.path) != obligation.listcomp_span
        or len(value.generators) != 1
        or value.generators[0].is_async
        or value.generators[0].ifs
        or not isinstance(value.generators[0].target, ast.Name)
        or not isinstance(value.generators[0].iter, ast.Name)
        or value.generators[0].iter.id != projection.projected_family_name
        or _span(value.generators[0].iter, obligation.iterable_span.path)
        != obligation.iterable_span
        or not isinstance(value.elt, ast.Attribute)
        or value.elt.attr != "pvalue"
        or not isinstance(value.elt.value, ast.Call)
    ):
        return None
    generator_name = value.generators[0].target.id
    call = value.elt.value
    if (
        _span(call, obligation.element_call_span.path) != obligation.element_call_span
        or _dotted_name(call.func) != obligation.resolved_test_callable
        or len(call.args) != 2
        or call.keywords
    ):
        return None
    arguments: list[str] = []
    argument_bases: list[str] = []
    for argument_node in call.args:
        if (
            not isinstance(argument_node, ast.Subscript)
            or not isinstance(argument_node.value, ast.Name)
            or not isinstance(argument_node.slice, ast.Name)
            or argument_node.slice.id != generator_name
        ):
            return None
        argument_bases.append(argument_node.value.id)
        arguments.append(
            _source_token(
                "test-argument-template",
                source_digest,
                _span(argument_node, obligation.element_call_span.path),
            )
        )
    if (
        len(set(arguments)) != 2
        or len(set(argument_bases)) != 2
        or tuple(argument_bases) != (argument.left_argument_name, argument.right_argument_name)
    ):
        return None
    derived_id = _source_token("battery-construct", source_digest, obligation.assignment_span)
    if (
        derived_id != obligation.battery_construct_id
        or derived_id != projection.battery_construct_id
    ):
        return None
    return (
        derived_id,
        _source_token("test-call-template", source_digest, obligation.element_call_span),
        (arguments[0], arguments[1]),
        generator_name,
    )


def _correction_shape(
    assignment: ast.Assign,
    call: ast.Call,
    obligation: CorrectionCall,
    battery: TestBatteryObligation,
    family_count: int,
    source_digest: str,
) -> tuple[str, tuple[int, ...]] | None:
    if (
        _single_name_target(assignment) != obligation.result_name
        or assignment.value is not call
        or obligation.battery_construct_id != battery.battery_construct_id
        or obligation.iterable_row_domain != battery.iterable_row_domain
        or obligation.resolved_callable not in _CORRECTION_CALLABLES
        or not obligation.asserts_trusted_bh_recomputation
        or _dotted_name(call.func)
        != (
            "benjamini_hochberg"
            if obligation.resolved_callable == _REPOSITORY_BH_CALLABLE
            else "multipletests"
        )
        or len(call.args) != 1
    ):
        return None
    if obligation.resolved_callable == _REPOSITORY_BH_CALLABLE:
        if call.keywords:
            return None
    elif not (
        len(call.keywords) == 1
        and call.keywords[0].arg == "method"
        and isinstance(call.keywords[0].value, ast.Constant)
        and call.keywords[0].value.value == "fdr_bh"
    ):
        return None
    positions = _correction_input_positions(
        call.args[0],
        battery.battery_result_name,
        family_count,
    )
    input_node = call.args[0]
    if positions is None:
        return None
    if isinstance(input_node, ast.Name):
        if len(positions) != family_count:
            return None
    elif isinstance(input_node, ast.Subscript):
        if not 0 < len(positions) < family_count:
            return None
    else:
        return None
    return (
        _source_token("correction-call", source_digest, obligation.call_span),
        positions,
    )


def _report_shape(
    assignment: ast.Assign,
    sink_statement: ast.Expr,
    obligation: ReportFamilyBinding,
    projection: FullFamilyProjectionObligation,
    battery: TestBatteryObligation,
    correction: CorrectionCall,
    source_path: str,
    input_path: str,
    measurement_input_path: str,
    source_digest: str,
) -> tuple[str, str] | None:
    value = assignment.value
    if (
        _single_name_target(assignment) != obligation.reported_name
        or obligation.iterable_row_domain != projection.iterable_row_domain
        or obligation.hypothesis_key_columns != projection.hypothesis_key_columns
        or not obligation.pvalue_column
        or not obligation.selected_result
        or not _record_ref(obligation.affected_target_ref)
        or obligation.affected_target_ref.record_type not in {"result", "claim"}
        or not _relative_path(obligation.path)
        or obligation.path in {source_path, input_path, measurement_input_path}
        or not isinstance(value, ast.Call)
        or _dotted_name(value.func) != "tuple"
        or len(value.args) != 1
        or value.keywords
        or not isinstance(value.args[0], ast.Call)
        or _dotted_name(value.args[0].func) != "zip"
        or len(value.args[0].args) != 2
        or value.args[0].keywords
        or not all(isinstance(item, ast.Name) for item in value.args[0].args)
        or tuple(cast(ast.Name, item).id for item in value.args[0].args)
        != (projection.projected_family_name, battery.battery_result_name)
    ):
        return None
    sink = sink_statement.value
    if not (
        isinstance(sink, ast.Call)
        and len(sink.keywords) == 1
        and sink.keywords[0].arg == "encoding"
        and isinstance(sink.keywords[0].value, ast.Constant)
        and sink.keywords[0].value.value == "utf-8"
    ):
        return None
    if (
        not isinstance(sink.func, ast.Attribute)
        or sink.func.attr != "write_text"
        or not isinstance(sink.func.value, ast.Call)
        or _dotted_name(sink.func.value.func) != "Path"
        or len(sink.func.value.args) != 1
        or sink.func.value.keywords
        or not isinstance(sink.func.value.args[0], ast.Constant)
        or sink.func.value.args[0].value != obligation.path
        or len(sink.args) != 1
        or not isinstance(sink.args[0], ast.Call)
        or _dotted_name(sink.args[0].func) != "str"
        or len(sink.args[0].args) != 1
        or sink.args[0].keywords
        or not isinstance(sink.args[0].args[0], ast.Tuple)
        or len(sink.args[0].args[0].elts) != 2
        or not all(isinstance(item, ast.Name) for item in sink.args[0].args[0].elts)
        or tuple(cast(ast.Name, item).id for item in sink.args[0].args[0].elts)
        != (obligation.reported_name, correction.result_name)
    ):
        return None
    report_token = _source_token(
        "reported-family-binding", source_digest, obligation.assignment_span
    )
    sink_token = _source_token("selected-report-sink", source_digest, obligation.sink_span)
    if obligation.token != sink_token:
        return None
    return report_token, sink_token


def _scope_equation_is_closed(
    certificate: MultipleTestingCertificate,
    replay: _SourceReplay,
) -> bool:
    check = certificate.family_scope_checks[0]
    active = check.complete_test_call_tokens - check.proven_dead_test_call_tokens
    return (
        check.battery_construct_id == replay.battery_construct_id
        and check.iterable_row_domain == certificate.case_binding.iterable_row_domain
        and check.bases == REQUIRED_SCOPE_BASES
        and check.complete_test_call_tokens == replay.complete_test_call_tokens
        and check.modeled_test_call_tokens == active
        and not check.proven_dead_test_call_tokens
        and check.corrected_test_call_tokens == frozenset({replay.element_call_template_token})
        and check.corrected_test_call_tokens <= check.modeled_test_call_tokens
        and replay.complete_test_call_tokens == frozenset({replay.element_call_template_token})
        and _nonempty_unique_strings(check.evidence_ids)
    )


def _derive_result_positions(
    certificate: MultipleTestingCertificate,
    fact: PValueFamilyFact,
    argument_resolution: _ArgumentFactResolution,
    replay: _SourceReplay,
) -> tuple[TestResultPosition, ...] | None:
    positions: list[TestResultPosition] = []
    for position, hypothesis in enumerate(fact.hypothesis_tokens):
        vectors = argument_resolution.vectors_by_hypothesis.get(hypothesis)
        if vectors is None:
            return None
        positions.append(
            TestResultPosition(
                position=position,
                row_ordinal=position + 1,
                hypothesis_token=hypothesis,
                source_observation_token=fact.observation_tokens[position],
                element_call_template_token=replay.element_call_template_token,
                argument_template_tokens=replay.argument_template_tokens,
                argument_vector_tokens=vectors,
                result_token=test_result_token(
                    certificate.source_digest,
                    replay.battery_construct_id,
                    replay.element_call_template_token,
                    fact.row_domain,
                    position,
                    hypothesis,
                ),
            )
        )
    return tuple(positions)


def _trusted_bh_recomputation(
    correction: CorrectionCall,
    raw_values: tuple[Decimal, ...],
    positions: tuple[int, ...],
) -> tuple[str, ...] | None:
    try:
        recomputed = benjamini_hochberg(tuple(raw_values[index] for index in positions))
    except (ArithmeticError, ValueError):
        return None
    canonical = tuple(_canonical_decimal(value) for value in recomputed)
    if correction.asserted_adjusted_pvalues != canonical:
        return None
    return canonical


def _report_and_sink_are_closed(
    certificate: MultipleTestingCertificate,
    fact: PValueFamilyFact,
    replay: _SourceReplay,
) -> tuple[str, ...] | None:
    report = certificate.report_bindings[0]
    argument = certificate.test_argument_domain_obligations[0]
    if (
        report.affected_target_ref != certificate.case_binding.affected_target_ref
        or report.iterable_row_domain != fact.row_domain
        or report.hypothesis_key_columns != fact.hypothesis_key_columns
        or report.pvalue_column != fact.pvalue_column
        or report.token != replay.sink_token
        or certificate.all_sink_tokens != frozenset({replay.sink_token})
        or not _nonempty_token_set(report.relevant_origins)
        or not _nonempty_token_set(report.relevant_bindings)
    ):
        return None
    required_origins = {
        certificate.source_path,
        fact.path,
        fact.row_domain,
        argument.input_binding.path,
        argument.measurement_row_domain,
        report.path,
    }
    required_bindings = {
        replay.battery_construct_id,
        replay.element_call_template_token,
        replay.correction_construct_token,
        replay.report_construct_token,
        replay.sink_token,
        replay.measurement_reader_token,
        replay.left_projection_token,
        replay.right_projection_token,
        argument.measurement_rows_name,
        argument.left_argument_name,
        argument.right_argument_name,
        certificate.test_batteries[0].battery_result_name,
        certificate.correction_calls[0].result_name,
        report.reported_name,
    }
    if (
        not required_origins <= report.relevant_origins
        or not required_bindings <= report.relevant_bindings
    ):
        return None
    return (replay.sink_token,)


def _proof_slice_is_noninterfering(
    certificate: MultipleTestingCertificate,
    fact: PValueFamilyFact,
    argument_resolution: _ArgumentFactResolution,
    replay: _SourceReplay,
    positions: tuple[TestResultPosition, ...],
) -> bool:
    report = certificate.report_bindings[0]
    projection = certificate.full_family_projections[0]
    argument = certificate.test_argument_domain_obligations[0]
    argument_fact = argument_resolution.fact
    relevant_origins = {
        certificate.source_path,
        fact.path,
        fact.row_domain,
        argument_fact.path,
        argument_fact.row_domain,
        report.path,
        *report.relevant_origins,
    }
    relevant_bindings = {
        *replay.syntactic_construct_tokens,
        *fact.observation_tokens,
        *fact.hypothesis_tokens,
        *fact.pvalue_tokens,
        *argument_fact.observation_tokens,
        *argument_fact.hypothesis_tokens,
        *argument_resolution.cell_tokens,
        *(token for pair in argument_resolution.vectors_by_hypothesis.values() for token in pair),
        *(item.result_token for item in positions),
        *(token for item in positions for token in item.argument_vector_tokens),
        projection.source_rows_name,
        projection.projected_family_name,
        argument.measurement_rows_name,
        argument.left_argument_name,
        argument.right_argument_name,
        certificate.test_batteries[0].battery_result_name,
        certificate.correction_calls[0].result_name,
        report.reported_name,
        report.token,
        *report.relevant_bindings,
    }
    relevant = relevant_origins | relevant_bindings
    for effect in certificate.effects:
        if (
            not _token_set(effect.reads)
            or not _token_set(effect.writes)
            or not _token_set(effect.aliases)
            or not _present(effect.reason)
            or (effect.opaque and "*" not in effect.writes)
            or "*" in effect.writes
            or bool(effect.writes & relevant)
            or "*" in effect.aliases
            or bool(effect.aliases & relevant)
            or (effect.may_raise and ("*" in effect.reads or bool(effect.reads & relevant)))
        ):
            return False
    for unknown in certificate.unknowns:
        if (
            not _present(unknown.reason)
            or "*" in unknown.origins
            or bool(unknown.origins & relevant)
        ):
            return False
    return True


def _evidence_is_closed(
    certificate: MultipleTestingCertificate,
    fact: PValueFamilyFact,
    argument_fact: TestArgumentDomainFact,
) -> bool:
    declarations = certificate.evidence
    by_id = {item.evidence_id: item for item in declarations}
    if (
        not declarations
        or len(declarations) > MAX_MULTIPLE_TESTING_EVIDENCE_DECLARATIONS
        or len(by_id) != len(declarations)
        or len(set(declarations)) != len(declarations)
    ):
        return False
    uses = [
        *(
            item
            for record in certificate.family_domain_obligations
            for item in record.reader_evidence_ids
        ),
        *(item for record in certificate.full_family_projections for item in record.evidence_ids),
        *(
            item
            for record in certificate.test_argument_domain_obligations
            for item in record.evidence_ids
        ),
        *(item for record in certificate.test_batteries for item in record.evidence_ids),
        *(item for record in certificate.correction_calls for item in record.evidence_ids),
        *(item for record in certificate.family_scope_checks for item in record.evidence_ids),
        *(item for record in certificate.report_bindings for item in record.evidence_ids),
    ]
    if (
        any(not _present(item) for item in uses)
        or len(uses) != len(set(uses))
        or set(by_id) != {fact.evidence_id, argument_fact.evidence_id, *uses}
    ):
        return False
    code_points: list[EvidencePoint] = []
    for declaration in declarations:
        point = declaration.point
        if not _evidence_point_is_closed(point):
            return False
        if declaration.evidence_id == fact.evidence_id:
            if point.path != fact.path:
                return False
        elif declaration.evidence_id == argument_fact.evidence_id:
            if point.path != argument_fact.path:
                return False
        else:
            if point.path != certificate.source_path or not _point_within(
                point, certificate.source_extent
            ):
                return False
            code_points.append(point)
    if len(code_points) != len(set(code_points)):
        return False
    projection = certificate.full_family_projections[0]
    domain = certificate.family_domain_obligations[0]
    argument = certificate.test_argument_domain_obligations[0]
    battery = certificate.test_batteries[0]
    correction = certificate.correction_calls[0]
    report = certificate.report_bindings[0]
    return (
        _ids_cover_points(
            domain.reader_evidence_ids,
            (domain.reader_assignment_span,),
            by_id,
        )
        and _ids_cover_points(
            projection.evidence_ids,
            (projection.assignment_span, projection.listcomp_span, projection.element_span),
            by_id,
        )
        and _ids_cover_points(
            argument.evidence_ids,
            (
                argument.reader_assignment_span,
                argument.left_projection_span,
                argument.right_projection_span,
                argument.left_key_span,
                argument.right_key_span,
                argument.left_value_span,
                argument.right_value_span,
            ),
            by_id,
        )
        and _ids_cover_points(
            battery.evidence_ids,
            (
                battery.assignment_span,
                battery.listcomp_span,
                battery.element_call_span,
                battery.iterable_span,
            ),
            by_id,
        )
        and _ids_cover_points(correction.evidence_ids, (correction.call_span,), by_id)
        and _ids_cover_points(
            report.evidence_ids,
            (report.assignment_span, report.sink_span),
            by_id,
        )
    )


def _projection_element_matches(
    node: ast.expr,
    row_name: str,
    columns: tuple[str, ...],
) -> bool:
    elements = node.elts if isinstance(node, ast.Tuple) else [node]
    if len(elements) != len(columns) or isinstance(node, ast.Tuple) != (len(columns) > 1):
        return False
    return all(
        isinstance(element, ast.Subscript)
        and isinstance(element.value, ast.Name)
        and element.value.id == row_name
        and isinstance(element.slice, ast.Constant)
        and element.slice.value == column
        for element, column in zip(elements, columns, strict=True)
    )


def _required_imports_are_exact(
    tree: ast.Module,
    correction_callable: str,
    *,
    reader_required: bool,
) -> bool:
    csv_count = 0
    scipy = 0
    path = 0
    bh = 0
    multipletests = 0
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "csv" and alias.asname is None:
                    csv_count += 1
                elif alias.name == "scipy.stats" and alias.asname is None:
                    scipy += 1
                else:
                    return False
        elif isinstance(statement, ast.ImportFrom):
            if statement.level != 0:
                return False
            if statement.module == "pathlib" and len(statement.names) == 1:
                alias = statement.names[0]
                if alias.name != "Path" or alias.asname is not None:
                    return False
                path += 1
            elif statement.module == "sc_referee.calculation_checks.bh":
                if len(statement.names) != 1:
                    return False
                alias = statement.names[0]
                if alias.name != "benjamini_hochberg" or alias.asname is not None:
                    return False
                bh += 1
            elif statement.module == "statsmodels.stats.multitest":
                if len(statement.names) != 1:
                    return False
                alias = statement.names[0]
                if alias.name != "multipletests" or alias.asname is not None:
                    return False
                multipletests += 1
            else:
                return False
    expected_correction = (1, 0) if correction_callable == _REPOSITORY_BH_CALLABLE else (0, 1)
    return (
        csv_count,
        scipy,
        path,
        bh,
        multipletests,
    ) == (
        1 if reader_required else 0,
        1,
        1,
        *expected_correction,
    )


def _supported_statement_order(*statements: ast.stmt) -> bool:
    starts = [(item.lineno, item.col_offset) for item in statements]
    return starts == sorted(starts) and len(starts) == len(set(starts))


def _relevant_names_have_exact_bindings(
    tree: ast.Module,
    names: set[str],
    allowed_statement_ids: set[int],
    imported_names: set[str],
) -> bool:
    for statement in tree.body:
        if id(statement) in allowed_statement_ids or isinstance(
            statement, (ast.Import, ast.ImportFrom)
        ):
            continue
        if _assigned_names(statement) & names:
            return False
    assigned: Counter[str] = Counter()
    for statement in tree.body:
        assigned.update(_assigned_names(statement))
    for name in names - imported_names:
        if assigned[name] > 1:
            return False
    return True


def _correction_input_positions(
    node: ast.expr,
    battery_name: str,
    family_count: int,
) -> tuple[int, ...] | None:
    if isinstance(node, ast.Name) and node.id == battery_name:
        return tuple(range(family_count))
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == battery_name
        and isinstance(node.slice, ast.Slice)
    ):
        lower = _literal_nonnegative_bound(node.slice.lower)
        upper = _literal_nonnegative_bound(node.slice.upper)
        if lower is False or upper is False or node.slice.step is not None:
            return None
        positions = tuple(range(family_count)[slice(lower, upper, None)])
        return positions if 0 < len(positions) < family_count else None
    return None


def _literal_path_call(node: ast.expr, path: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and _dotted_name(node.func) == "Path"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == path
    )


def _exact_utf8_keyword(keywords: list[ast.keyword]) -> bool:
    return (
        len(keywords) == 1
        and keywords[0].arg == "encoding"
        and isinstance(keywords[0].value, ast.Constant)
        and keywords[0].value.value == "utf-8"
    )


def _exact_open_keywords(keywords: list[ast.keyword]) -> bool:
    values = {item.arg: item.value for item in keywords if item.arg is not None}
    return (
        len(values) == len(keywords) == 2
        and set(values) == {"encoding", "newline"}
        and isinstance(values["encoding"], ast.Constant)
        and values["encoding"].value == "utf-8"
        and isinstance(values["newline"], ast.Constant)
        and values["newline"].value == ""
    )


def _assigned_names(statement: ast.stmt) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(statement):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            result.add(node.id)
    return result


def _assign_containing_call(tree: ast.Module, target: ast.Call) -> ast.Assign | None:
    matches = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign) and any(node is target for node in ast.walk(statement))
    ]
    return matches[0] if len(matches) == 1 else None


def _parent_attribute(tree: ast.Module, target: ast.Call) -> ast.Attribute | None:
    matches = [
        node for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.value is target
    ]
    return matches[0] if len(matches) == 1 else None


def _unique_node_at(
    tree: ast.Module,
    node_type: type[ast.AST],
    point: EvidencePoint,
) -> ast.AST | None:
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, node_type)
        and isinstance(node, (ast.expr, ast.stmt))
        and _span(node, point.path) == point
    ]
    return matches[0] if len(matches) == 1 else None


def _single_name_target(assignment: ast.Assign) -> str | None:
    if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
        return None
    return assignment.targets[0].id


def _literal_nonnegative_bound(node: ast.expr | None) -> int | bool | None:
    if node is None:
        return None
    if (
        not isinstance(node, ast.Constant)
        or not isinstance(node.value, int)
        or isinstance(node.value, bool)
        or node.value < 0
    ):
        return False
    return node.value


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent is not None else None
    return None


def _span(node: ast.expr | ast.stmt, path: str) -> EvidencePoint:
    return EvidencePoint(
        path=path,
        start_line=node.lineno,
        end_line=cast(int, node.end_lineno),
        start_column=node.col_offset + 1,
        end_column=cast(int, node.end_col_offset) + 1,
    )


def _source_token(kind: str, source_digest: str, point: EvidencePoint) -> str:
    return f"{kind}:" + semantic_digest(
        {
            "schema": "multiple-testing-source-token-v1",
            "kind": kind,
            "source_digest": source_digest,
            "point": asdict(point),
        }
    )


def _whole_source_extent(path: str, source: str) -> EvidencePoint:
    lines = source.splitlines()
    if not lines:
        return EvidencePoint(path, 1, 1, 1, 1)
    return EvidencePoint(path, 1, len(lines), 1, len(lines[-1]) + 1)


def _canonical_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _exact_decimal(value: str) -> Decimal | None:
    if _UNSIGNED_FIXED_POINT_DECIMAL.fullmatch(value) is None:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed < 0 or parsed > 1:
        return None
    return parsed


def _exact_measurement(value: str) -> float | None:
    if _MEASUREMENT_DECIMAL.fullmatch(value) is None:
        return None
    try:
        exact = Decimal(value)
        parsed = float(value)
    except (InvalidOperation, ValueError, OverflowError):
        return None
    if not math.isfinite(parsed) or (exact != 0 and parsed == 0.0):
        return None
    return parsed


def _argument_observation_token(
    path: str,
    content_digest: str,
    row_domain: str,
    row_ordinal: int,
) -> str:
    return "test-argument-observation:" + semantic_digest(
        {
            "schema": "test-argument-observation-v1",
            "path": path,
            "content_digest": content_digest,
            "row_domain": row_domain,
            "row_ordinal": row_ordinal,
        }
    )


def _fact_record_size(fact: PValueFamilyFact) -> int:
    return len(canonical_json(asdict(fact)).encode("utf-8"))


def _argument_fact_record_size(fact: TestArgumentDomainFact) -> int:
    return len(canonical_json(asdict(fact)).encode("utf-8"))


def _material_input_is_closed(binding: MaterialInputBinding) -> bool:
    return (
        _relative_path(binding.path)
        and _sha256(binding.content_digest)
        and _record_ref(binding.file_ref, "file_record")
        and _record_ref(binding.asset_identity_ref, "asset_identity")
    )


def _reader_model(reader_form: str, line_model: str, dialect: str) -> bool:
    return (
        reader_form in _READER_MODELS
        and _READER_MODELS[reader_form] == line_model
        and dialect == _DIALECT
    )


def _record_ref(value: RecordRef, expected: str | None = None) -> bool:
    return (
        _present(value.record_type)
        and _present(value.record_id)
        and (expected is None or value.record_type == expected)
    )


def _source_extent_is_closed(point: EvidencePoint, source_path: str) -> bool:
    return point.path == source_path and point.start_line == 1 and point.start_column == 1


def _evidence_point_is_closed(point: EvidencePoint) -> bool:
    return (
        _relative_path(point.path)
        and point.start_line >= 1
        and point.end_line >= point.start_line
        and point.start_column >= 1
        and point.end_column >= 1
        and (point.end_line > point.start_line or point.end_column >= point.start_column)
    )


def _ids_cover_points(
    evidence_ids: tuple[str, ...],
    points: tuple[EvidencePoint, ...],
    declarations: dict[str, EvidenceDeclaration],
) -> bool:
    return _nonempty_unique_strings(evidence_ids) and set(points) <= {
        declarations[item].point for item in evidence_ids
    }


def _point_within(point: EvidencePoint, extent: EvidencePoint) -> bool:
    return (
        (extent.start_line, extent.start_column)
        <= (point.start_line, point.start_column)
        <= (point.end_line, point.end_column)
        <= (extent.end_line, extent.end_column)
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
    suffix = value.removeprefix("sha256:")
    return (
        value.startswith("sha256:")
        and len(suffix) == 64
        and all(character in _LOWER_HEX for character in suffix)
    )


def _present(value: str) -> bool:
    return bool(value) and value == value.strip()


def _nonempty_unique_strings(
    values: tuple[str, ...],
    *,
    trimmed: bool = True,
) -> bool:
    return bool(values) and _unique_strings(values, trimmed=trimmed)


def _unique_strings(values: tuple[str, ...], *, trimmed: bool = True) -> bool:
    valid = all(bool(value) and (not trimmed or _present(value)) for value in values)
    return valid and len(values) == len(set(values))


def _nonempty_token_set(values: frozenset[str]) -> bool:
    return bool(values) and _token_set(values)


def _token_set(values: frozenset[str]) -> bool:
    return all(_present(value) for value in values)


__all__ = [
    "family_hypothesis_token",
    "family_observation_token",
    "family_pvalue_token",
    "multiple_testing_case_digest",
    "multiple_testing_replay_digest",
    "source_construct_token",
    "test_argument_cell_token",
    "test_argument_vector_token",
    "test_result_token",
    "verify_multiple_testing_certificate",
]
