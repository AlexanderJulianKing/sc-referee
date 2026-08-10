"""Typed semantic IR and proof records for founder-orientation v3.

The analyzer in :mod:`founder_orientation_semantic` is deliberately allowed
to be ambitious: it composes operations, follows helpers, and proposes proof
records.  Nothing in that analyzer is authority by itself.  The compact
kernel in :mod:`founder_orientation_certificate` accepts only a closed
``OrientationCertificate`` over the records in this module.

The public value names mirror the v3 design contract.  A few lowering-only
values live in the analyzer rather than here so that the kernel's input
surface remains small.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NumberType = Literal["int", "float", "decimal", "fraction"]
RuntimeType = Literal["str", "int", "float", "bool", "decimal", "fraction"]
FoldOperation = Literal["sum", "product"]
Orientation = Literal["direct", "repaired"]

# The exact runtime line model a certified staged CSV reader uses.  ``splitlines``
# is ``<path-like>.read_text(...).splitlines()`` fed to ``csv.DictReader``; the
# runtime row boundaries are Python ``str.splitlines()`` boundaries, which break
# on more code points than ``csv``'s own ``\r``/``\n``/``\r\n`` newline handling.
# ``csv_newline`` is ``csv.DictReader`` over an open file handle, whose row
# boundaries are ``csv``'s newline model.  The prover must reproduce the exact
# model the analyzer certified, and the kernel binds the two together so a fact
# proven under one line model can never discharge an obligation certified under
# the other.
LineModel = Literal["splitlines", "csv_newline"]


@dataclass(frozen=True, order=True)
class PrimitiveTransform:
    """One exact primitive-Python transfer on a projection path."""

    operation: str
    input_type: str
    output_type: str
    parity_delta: int


@dataclass(frozen=True, order=True)
class Projection:
    """One staged CSV column at one row position."""

    asset: str
    row_domain: str
    column: str
    parity: int
    runtime_type: RuntimeType
    transforms: tuple[PrimitiveTransform, ...]


@dataclass(frozen=True, order=True)
class CsvBinaryDomainFact:
    """A bounded proof about one exact column in one digest-bound CSV.

    ``line_model`` names the exact runtime line model the prover reproduced to
    enumerate the rows (:data:`LineModel`).  A fact carries the model it was
    proven under so the kernel can refuse a discharge whose obligation was
    certified under a different model.
    """

    path: str
    content_digest: str
    column: str
    row_count: int
    recognized_values: tuple[str, ...]
    line_model: str


@dataclass(frozen=True, order=True)
class TransformDomainObligation:
    """One compared projection whose runtime transforms require a domain proof.

    ``line_model`` is the runtime line model the analyzer certified for the
    staged read that produced this projection's rows (:data:`LineModel`).  The
    prover must prove the domain fact under exactly this model.
    """

    asset: str
    content_digest: str
    row_domain: str
    column: str
    operations: tuple[str, ...]
    line_model: str
    domain_fact: CsvBinaryDomainFact | None = None


@dataclass(frozen=True, order=True)
class ExactNumber:
    """An exact finite numeric value, retaining its Python runtime type.

    ``value`` is a canonical rational spelling: ``numerator/denominator``.
    Even a float literal is stored as its exact binary rational value.  This
    lets the verifier compare selector branches without a tolerance.
    """

    number_type: NumberType
    value: str


@dataclass(frozen=True, order=True)
class Eq:
    """Exact equality between two aligned staged projections."""

    left: Projection
    right: Projection
    index_map: str
    token: str


@dataclass(frozen=True, order=True)
class Predicate:
    """A single boolean predicate used by an extensional selector."""

    expression: Eq


@dataclass(frozen=True, order=True)
class Selector:
    """The exact false/true values of a pure one-predicate expression."""

    predicate: Predicate
    false_value: ExactNumber
    true_value: ExactNumber
    token: str


@dataclass(frozen=True)
class Gated:
    """An exact numeric projection multiplied by proven selector values."""

    projection: Projection
    row_domain: str
    index_map: str
    selector_tokens: frozenset[str]


@dataclass(frozen=True)
class Sequence:
    """An order-preserving element sequence over one proven index map."""

    index_map: str
    element_value: object


@dataclass(frozen=True)
class Fold:
    """A finite fold whose element carries one or more selectors."""

    op: FoldOperation
    row_domain: str
    element: object
    initial_value: ExactNumber
    index_map: str
    token: str
    selector_tokens: frozenset[str]


@dataclass(frozen=True, order=True)
class Effect:
    """A conservative read/write/alias summary for one operation."""

    reads: frozenset[str]
    writes: frozenset[str]
    aliases: frozenset[str]
    may_raise: bool
    opaque: bool
    reason: str


@dataclass(frozen=True, order=True)
class Unknown:
    """An unresolved value and the exact origins it may affect."""

    reason: str
    origins: frozenset[str]


@dataclass(frozen=True, order=True)
class EvidencePoint:
    """A source node sufficient for an eventual public evidence span."""

    path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int


@dataclass(frozen=True)
class SinkProof:
    """One exact report write and the semantic producers in its payload."""

    path: str
    fold_tokens: frozenset[str]
    selector_tokens: frozenset[str]
    predicate_tokens: frozenset[str]
    relevant_origins: frozenset[str]
    relevant_bindings: frozenset[str]


@dataclass(frozen=True)
class OrientationCertificate:
    """An analyzer proposal; only the independent kernel may accept it."""

    source_path: str
    comparisons: tuple[Eq, ...]
    selectors: tuple[Selector, ...]
    folds: tuple[Fold, ...]
    sinks: tuple[SinkProof, ...]
    reaching_path_orientations: tuple[frozenset[Orientation], ...]
    effects: tuple[Effect, ...]
    transform_domain_obligations: tuple[TransformDomainObligation, ...]
    proven_domain_facts: tuple[CsvBinaryDomainFact, ...]
    all_report_comparison_tokens: frozenset[str]
    dead_comparison_tokens: frozenset[str]
    evidence: tuple[EvidencePoint, ...]


@dataclass(frozen=True)
class VerifiedOrientationCertificate:
    """The small kernel's accepted singleton orientation proof."""

    orientation: Orientation
    source_path: str
    evidence: tuple[EvidencePoint, ...]
    comparison_tokens: tuple[str, ...]
    selector_tokens: tuple[str, ...]
    fold_tokens: tuple[str, ...]
    domain_facts: tuple[CsvBinaryDomainFact, ...]
