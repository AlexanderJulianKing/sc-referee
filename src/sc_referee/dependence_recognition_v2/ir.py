"""Frozen proof records for the unregistered dependence growth shadow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sc_referee.dependence_recognition.ir import RecordRef

MAX_V2_SOURCE_BYTES = 1 * 1024 * 1024
MAX_V2_AST_NODES = 50_000
MAX_V2_INLINE_DEPTH = 3
MAX_V2_GROUPS = 256

DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS = frozenset(
    {
        "alpha-renaming",
        "authority-binding",
        "certificate-identity",
        "count-fact-closure",
        "count-cells-factorial",
        "count-set-equations",
        "count-source-semantic-replay",
        "count-subset-partition",
        "count-unit-nonspanning",
        "conclusion-equation",
        "dead-construct-completeness",
        "envelope-binding",
        "fact-closure",
        "group-length-equation",
        "group-partition",
        "observation-identity",
        "operand-binding",
        "operand-disjointness",
        "procedure-set-homogeneity",
        "rename-injectivity",
        "sink-partition",
        "source-parse",
        "source-semantic-replay",
        "source-size",
    }
)

# One closed vocabulary for every reason_code the development adapter can emit.
DEPENDENCE_V2_REASON_REGISTRY = frozenset(
    {
        "ast-node-ceiling",
        "annotated-assignment-not-modeled",
        "augmented-assignment-not-modeled",
        "authority-material-binding-mismatch",
        "authorized-composite-unit-key-unsupported",
        "bom-unsupported",
        "count-cell-derived-by-arithmetic",
        "count-cells-not-factorial",
        "count-cells-not-partition",
        "count-domain-not-row-bound",
        "count-increment-not-total",
        "count-multiple-increment-sites",
        "count-predicate-literal-not-string",
        "count-predicate-not-closed",
        "count-procedure-trial-declaration-missing",
        "count-set-degenerate",
        "count-success-not-subset",
        "dataclass-use-not-modeled",
        "defaultdict-key-not-proven",
        "dependence-v2-shadow-abstention",
        "duplicate-header",
        "delete-not-modeled",
        "function-argument-not-simple",
        "function-argument-starred",
        "function-closure",
        "function-default-params",
        "function-entry-not-closed",
        "function-globals-read",
        "function-globals-write",
        "function-inline-depth-exceeded",
        "function-rename-collision",
        "function-nonpositional-params",
        "function-not-provably-dead",
        "function-parameter-rebound",
        "function-recursive",
        "function-return-shape",
        "function-star-params",
        "group-accumulator-not-total",
        "group-bucket-unpopulated",
        "group-container-aliased",
        "group-container-not-list",
        "group-domain-binding-mismatch",
        "group-domain-unproven",
        "group-key-equals-value-column",
        "group-key-is-unit-column",
        "group-key-or-unit-cell-empty",
        "group-operand-arity-mismatch",
        "group-operand-sliced",
        "group-set-not-closed",
        "group-value-cast-absent",
        "group-value-cast-unproven",
        "group-value-expression-unsupported",
        "import-name-collision",
        "import-use-outside-grammar",
        "independent-unit-definition-unresolved",
        "module-constant-not-closed",
        "module-collection-use-not-modeled",
        "named-expression-not-modeled",
        "one-observation-per-unit-in-disjoint-bound-operands",
        "one-row-per-unit-in-proven-count-sets",
        "operand-name-rebound",
        "procedure-call-unresolved",
        "distribution-helper-not-bound",
        "distribution-helper-reaches-operand",
        # No registered inferential call plus a contested scipy.stats call leaves
        # the entire procedure census unresolved.
        "procedure-census-unresolved",
        "procedure-alternative-not-default",
        "procedure-keyword-not-closed",
        "procedure-set-count-member-unsupported",
        # Once a registered member establishes a procedure set, any additional
        # contested/unregistered member is a specifically unregistered set member.
        "procedure-set-member-unregistered",
        "procedure-set-mixed-independence-models",
        "procedure-set-operands-diverge",
        "procedure-version-unpinned",
        "python-parse-unsupported",
        "ragged-row",
        "raise-guard-not-modeled",
        "reader-bytes-not-ascii",
        "reader-form-unsupported",
        "repeated-unit-within-bound-operand",
        "repeated-unit-rows-counted-as-independent-binomtest-trials",
        "repeated-unit-rows-enter-independent-fisher-cells",
        "report-composition-not-modeled",
        "sink-aliases-operand-object",
        "sink-call-keyword-argument",
        "sink-call-not-whitelisted",
        "sink-classification-unresolved",
        "sink-controls-operand-flow",
        "sink-flow-escapes",
        "sink-mutates-operand-name",
        "sink-writes-outside-report",
        "single-python-module-required",
        "source-binding-mismatch",
        "source-byte-ceiling",
        "unit-spans-multiple-operands",
        "unit-spans-multiple-cells",
        "unsupported-import-form",
        "unsupported-reader-encoding",
        "v2-shadow-pipeline-exception",
        *(
            f"certificate-kernel-refusal:{obligation}"
            for obligation in DEPENDENCE_V2_KERNEL_REFUSAL_OBLIGATIONS
        ),
    }
)


def require_registered_v2_reason(reason: str) -> str:
    """Refuse development-code drift outside the single reason vocabulary."""

    if reason not in DEPENDENCE_V2_REASON_REGISTRY:
        raise AssertionError(f"unregistered dependence v2 reason: {reason}")
    return reason


CastKind = Literal["none", "float", "int"]
CountPredicateOperator = Literal["eq", "ne"]
GrowthConclusion = Literal["repeated_units", "one_observation_per_unit"]


@dataclass(frozen=True, order=True)
class CountPredicateAtom:
    """One byte-exact row-column predicate replayed by the kernel."""

    column: str
    operator: CountPredicateOperator
    literal: str


@dataclass(frozen=True, order=True)
class CountOperandObligation:
    """One symbolic count operand; it carries no analyzer-supplied count value."""

    operand_id: str
    position: int
    domain_kind: Literal["rows", "group_rows", "filtered_rows"]
    domain_atoms: tuple[CountPredicateAtom, ...]
    predicate_atoms: tuple[CountPredicateAtom, ...]


@dataclass(frozen=True, order=True)
class CountGroupDomainObligation:
    """One predeclared T-group key domain used by symbolic counts."""

    group_key_column: str
    predeclared_bucket_keys: tuple[str, ...]


@dataclass(frozen=True, order=True)
class CountProcedureObligation:
    """Digest-bound symbolic count request for one registered procedure."""

    path: str
    content_digest: str
    line_model: str
    reader_form: str
    encoding: str
    result_path: str
    authorized_unit_column: str
    resolved_callable: Literal["scipy.stats.binomtest", "scipy.stats.fisher_exact"]
    operands: tuple[CountOperandObligation, ...]
    universe_atoms: tuple[CountPredicateAtom, ...]
    group_domains: tuple[CountGroupDomainObligation, ...]


@dataclass(frozen=True, order=True)
class CountSetProof:
    """Kernel-consumed row set recomputed over frozen CSV bytes."""

    operand_id: str
    position: int
    row_indices: tuple[int, ...]
    observation_ids: tuple[str, ...]
    authorized_unit_ids: tuple[str, ...]
    cardinality: int


@dataclass(frozen=True, order=True)
class CountDomainRow:
    """One ordered byte-exact CSV row independently proven by the domain prover."""

    row_index: int
    values: tuple[tuple[str, str], ...]
    observation_id: str
    authorized_unit_id: str


@dataclass(frozen=True)
class CountProcedureFact:
    """Trusted byte-domain proof for all symbolic count operands."""

    evidence_id: str
    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef
    line_model: str
    reader_form: str
    encoding: str
    ascii_bytes_proven: bool
    header: tuple[str, ...]
    authorized_unit_column: str
    row_count: int
    rows: tuple[CountDomainRow, ...]
    operands: tuple[CountSetProof, ...]
    universe_row_indices: tuple[int, ...]


@dataclass(frozen=True, order=True)
class GroupValueSequence:
    """One byte-exact group and its ordered, multiplicity-preserving rows."""

    group_key: str
    row_indices: tuple[int, ...]
    observation_ids: tuple[str, ...]
    authorized_unit_ids: tuple[str, ...]
    source_values: tuple[str, ...]
    cast_value_reprs: tuple[str, ...]


@dataclass(frozen=True)
class GroupValueSequenceFact:
    """Trusted frozen-CSV fact used by the growth certificate kernel."""

    evidence_id: str
    path: str
    content_digest: str
    file_ref: RecordRef
    asset_identity_ref: RecordRef
    line_model: str
    reader_form: str
    encoding: str
    ascii_bytes_proven: bool
    header: tuple[str, ...]
    authorized_unit_column: str
    group_key_column: str
    value_column: str
    cast_kind: CastKind
    row_count: int
    groups: tuple[GroupValueSequence, ...]
    predeclared_bucket_keys: tuple[str, ...]


@dataclass(frozen=True, order=True)
class GroupValueSequenceObligation:
    """Analyzer request discharged only from controller-frozen bytes."""

    path: str
    content_digest: str
    line_model: str
    reader_form: str
    encoding: str
    authorized_unit_column: str
    group_key_column: str
    value_column: str
    cast_kind: CastKind
    predeclared_bucket_keys: tuple[str, ...]


@dataclass(frozen=True, order=True)
class OperandGroupBinding:
    """One procedure positional argument bound to one proven group key."""

    position: int
    argument_name: str
    group_key: str


@dataclass(frozen=True, order=True)
class AlphaRename:
    """One fresh-name witness keyed by function and acyclic call path."""

    function_name: str
    call_path_id: str
    call_span: tuple[int, int, int, int]
    original_name: str
    fresh_name: str


@dataclass(frozen=True, order=True)
class AuthorizedProcedureSet:
    """Controller-decoded callable set from the digest-sealed v2 procedure record."""

    record_id: str
    resolved_callables: tuple[str, ...]


@dataclass(frozen=True)
class DependenceGrowthCertificate:
    """Untrusted proposal checked against source and a trusted group fact."""

    certificate_id: str
    source_path: str
    source_digest: str
    source_extent: tuple[int, int]
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    authority_record_id: str
    independent_unit_definition_id: str
    obligation: GroupValueSequenceObligation
    resolved_callables: tuple[str, ...]
    procedure_call_tokens: tuple[str, ...]
    result_names: tuple[str, ...]
    sink_token: str
    group_container_name: str
    group_container_kind: Literal["dict", "defaultdict_list"]
    operand_bindings: tuple[OperandGroupBinding, ...]
    alpha_renames: tuple[AlphaRename, ...]
    operand_slice_statement_tokens: tuple[str, ...]
    sink_bound_statement_tokens: tuple[str, ...]
    dead_syntactic_construct_tokens: tuple[str, ...]
    conclusion: GrowthConclusion


@dataclass(frozen=True)
class CountDependenceCertificate:
    """Untrusted symbolic count proposal independently replayed by the kernel."""

    certificate_id: str
    source_path: str
    source_digest: str
    source_extent: tuple[int, int]
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    authority_record_id: str
    independent_unit_definition_id: str
    obligation: CountProcedureObligation
    resolved_callable: Literal["scipy.stats.binomtest", "scipy.stats.fisher_exact"]
    procedure_call_token: str
    result_name: str
    sink_token: str
    alpha_renames: tuple[AlphaRename, ...]
    operand_slice_statement_tokens: tuple[str, ...]
    sink_bound_statement_tokens: tuple[str, ...]
    dead_syntactic_construct_tokens: tuple[str, ...]
    conclusion: GrowthConclusion


@dataclass(frozen=True)
class VerifiedDependenceGrowthCertificate:
    """Kernel-authorized growth conclusion and its exact bound fact."""

    certificate_id: str
    source_path: str
    source_digest: str
    resolved_callables: tuple[str, ...]
    conclusion: GrowthConclusion
    fact: GroupValueSequenceFact
    operand_bindings: tuple[OperandGroupBinding, ...]
    repeated_unit_ids: tuple[str, ...]
    alpha_renames: tuple[AlphaRename, ...]
    operand_slice_statement_tokens: tuple[str, ...]
    sink_bound_statement_tokens: tuple[str, ...]
    dead_syntactic_construct_tokens: tuple[str, ...]


@dataclass(frozen=True)
class VerifiedCountDependenceCertificate:
    """Kernel-authorized count conclusion over exact frozen row sets."""

    certificate_id: str
    source_path: str
    source_digest: str
    resolved_callable: Literal["scipy.stats.binomtest", "scipy.stats.fisher_exact"]
    conclusion: GrowthConclusion
    fact: CountProcedureFact
    repeated_unit_ids: tuple[str, ...]
    alpha_renames: tuple[AlphaRename, ...]
    operand_slice_statement_tokens: tuple[str, ...]
    sink_bound_statement_tokens: tuple[str, ...]
    dead_syntactic_construct_tokens: tuple[str, ...]


@dataclass(frozen=True)
class GrowthAnalysis:
    """Untrusted analyzer result before controller-side proof discharge."""

    state: Literal["proposal", "question", "unsupported", "not_applicable"]
    certificate: DependenceGrowthCertificate | CountDependenceCertificate | None
    obligation: GroupValueSequenceObligation | CountProcedureObligation | None
    abstention_reasons: tuple[str, ...]
    candidate_key_columns: tuple[str, ...]
    basis: str


@dataclass(frozen=True)
class DischargedGrowthAnalysis:
    """Controller-side proof and kernel outcome."""

    state: Literal["verified", "question", "unsupported", "not_applicable"]
    verified_certificate: (
        VerifiedDependenceGrowthCertificate | VerifiedCountDependenceCertificate | None
    )
    abstention_reasons: tuple[str, ...]
    candidate_key_columns: tuple[str, ...]
    basis: str
