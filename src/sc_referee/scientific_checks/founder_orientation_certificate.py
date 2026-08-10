"""Small trusted certificate kernel for founder-orientation semantic v3.

The semantic analyzer may discover candidates in any order and with any
amount of internal bookkeeping.  This module intentionally knows none of
that machinery.  It accepts only closed IR proof records and recomputes the
properties that can authorize an orientation observation.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Protocol, TypeVar

from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    CsvBinaryDomainFact,
    Eq,
    ExactNumber,
    Fold,
    Gated,
    Orientation,
    OrientationCertificate,
    PrimitiveTransform,
    Projection,
    Selector,
    TransformDomainObligation,
    VerifiedOrientationCertificate,
)

_NUMERIC_TYPES = frozenset({"int", "float", "decimal", "fraction"})
_TokenValue = TypeVar("_TokenValue", bound="_Tokenized")


class _Tokenized(Protocol):
    @property
    def token(self) -> str: ...


_TRANSFORMS: dict[str, tuple[frozenset[str], str | None, int]] = {
    "csv_subscript": (frozenset({"row"}), "str", 0),
    "builtin_int": (frozenset({"str", "bool", "int"}), "int", 0),
    "builtin_float": (
        frozenset({"str", "bool", "int", "float"}),
        "float",
        0,
    ),
    "builtin_decimal": (
        frozenset({"str", "int", "decimal"}),
        "decimal",
        0,
    ),
    "builtin_fraction": (
        frozenset({"str", "int", "fraction"}),
        "fraction",
        0,
    ),
    "builtin_str": (
        frozenset({"str", "bool", "int", "float", "decimal", "fraction"}),
        "str",
        0,
    ),
    "one_minus": (_NUMERIC_TYPES, None, 1),
    "whitespace_strip": (frozenset({"str"}), "str", 0),
}


def verify_orientation_certificate(
    certificate: OrientationCertificate,
    *,
    trusted_domain_facts: tuple[CsvBinaryDomainFact, ...] = (),
) -> VerifiedOrientationCertificate | None:
    """Accept one complete, internally consistent singleton proof or abstain."""

    if not certificate.source_path or not certificate.sinks:
        return None
    comparisons = _unique_by_token(certificate.comparisons)
    selectors = _unique_by_token(certificate.selectors)
    folds = _unique_by_token(certificate.folds)
    if comparisons is None or selectors is None or folds is None:
        return None
    if not comparisons or not selectors or not folds:
        return None
    if not _transform_domains_are_discharged(
        certificate,
        comparisons,
        trusted_domain_facts,
    ):
        return None

    orientations: dict[str, Orientation] = {}
    for token, comparison in comparisons.items():
        candidate_orientation = _comparison_orientation(comparison)
        if candidate_orientation is None:
            return None
        orientations[token] = candidate_orientation

    for selector in selectors.values():
        selector_comparison = comparisons.get(selector.predicate.expression.token)
        if selector_comparison != selector.predicate.expression or not _selector_is_canonical(
            selector
        ):
            return None

    for fold in folds.values():
        if not _fold_is_closed(fold, selectors):
            return None

    sink_fold_tokens: set[str] = set()
    sink_selector_tokens: set[str] = set()
    sink_predicate_tokens: set[str] = set()
    relevant_origins: set[str] = set()
    relevant_bindings: set[str] = set()
    for sink in certificate.sinks:
        if not sink.path or not sink.fold_tokens:
            return None
        if not sink.fold_tokens <= folds.keys():
            return None
        fold_selectors = {
            selector_token
            for fold_token in sink.fold_tokens
            for selector_token in folds[fold_token].selector_tokens
        }
        if not sink.selector_tokens or not sink.selector_tokens <= fold_selectors:
            return None
        expected_predicates = {
            selectors[token].predicate.expression.token for token in sink.selector_tokens
        }
        if sink.predicate_tokens != expected_predicates:
            return None
        sink_fold_tokens.update(sink.fold_tokens)
        sink_selector_tokens.update(sink.selector_tokens)
        sink_predicate_tokens.update(sink.predicate_tokens)
        relevant_origins.update(sink.relevant_origins)
        relevant_bindings.update(sink.relevant_bindings)

    active_comparisons = (
        certificate.all_report_comparison_tokens - certificate.dead_comparison_tokens
    )
    if active_comparisons != sink_predicate_tokens:
        return None
    if not sink_predicate_tokens <= comparisons.keys():
        return None
    if not sink_selector_tokens <= selectors.keys():
        return None

    resolved = {orientations[token] for token in sink_predicate_tokens}
    if len(resolved) != 1:
        return None
    verified_orientation: Orientation = next(iter(resolved))
    for path_states in certificate.reaching_path_orientations:
        if path_states != frozenset({verified_orientation}):
            return None
    if not certificate.reaching_path_orientations:
        return None

    for effect in certificate.effects:
        touches_binding = "*" in effect.writes or bool(effect.writes & relevant_bindings)
        touches_origin = bool(effect.aliases & relevant_origins)
        raising_on_slice = effect.may_raise and bool(effect.reads & relevant_origins)
        if touches_binding or touches_origin or raising_on_slice:
            return None

    comparison_tokens = tuple(sorted(sink_predicate_tokens))
    selector_tokens = tuple(sorted(sink_selector_tokens))
    fold_tokens = tuple(sorted(sink_fold_tokens))
    if {item.token for item in certificate.comparisons if item.token in comparison_tokens} != set(
        comparison_tokens
    ):
        return None
    return VerifiedOrientationCertificate(
        orientation=verified_orientation,
        source_path=certificate.source_path,
        evidence=tuple(sorted(certificate.evidence)),
        comparison_tokens=comparison_tokens,
        selector_tokens=selector_tokens,
        fold_tokens=fold_tokens,
        domain_facts=certificate.proven_domain_facts,
    )


def _transform_domains_are_discharged(
    certificate: OrientationCertificate,
    comparisons: dict[str, Eq],
    trusted_domain_facts: tuple[CsvBinaryDomainFact, ...],
) -> bool:
    trusted = set(trusted_domain_facts)
    declared = set(certificate.proven_domain_facts)
    if (
        len(trusted) != len(trusted_domain_facts)
        or len(declared) != len(certificate.proven_domain_facts)
        or trusted != declared
    ):
        return False
    if any(not _binary_domain_fact_is_closed(fact) for fact in trusted):
        return False

    obligations = certificate.transform_domain_obligations
    obligation_keys = [_obligation_key(item) for item in obligations]
    if len(obligation_keys) != len(set(obligation_keys)):
        return False
    expected: dict[tuple[str, str, str, tuple[str, ...]], Projection] = {}
    for comparison in comparisons.values():
        for projection in (comparison.left, comparison.right):
            key = _projection_obligation_key(projection)
            expected[key] = projection
    if set(obligation_keys) != set(expected):
        return False

    used_facts: set[CsvBinaryDomainFact] = set()
    row_bindings: dict[tuple[str, str], tuple[str, int]] = {}
    for obligation in obligations:
        fact = obligation.domain_fact
        if fact is None or fact not in trusted:
            return False
        matched_projection = expected.get(_obligation_key(obligation))
        if matched_projection is None or not _projection_is_exact(matched_projection):
            return False
        if (
            fact.path != obligation.asset
            or fact.content_digest != obligation.content_digest
            or fact.column != obligation.column
        ):
            return False
        binding_key = (obligation.asset, obligation.row_domain)
        binding = (obligation.content_digest, fact.row_count)
        previous = row_bindings.setdefault(binding_key, binding)
        if previous != binding:
            return False
        used_facts.add(fact)
    return used_facts == declared


def _projection_obligation_key(
    projection: Projection,
) -> tuple[str, str, str, tuple[str, ...]]:
    return (
        projection.asset,
        projection.row_domain,
        projection.column,
        tuple(item.operation for item in projection.transforms),
    )


def _obligation_key(
    obligation: TransformDomainObligation,
) -> tuple[str, str, str, tuple[str, ...]]:
    return (
        obligation.asset,
        obligation.row_domain,
        obligation.column,
        obligation.operations,
    )


def _binary_domain_fact_is_closed(fact: CsvBinaryDomainFact) -> bool:
    if (
        not fact.path
        or fact.path.startswith("/")
        or ".." in fact.path.split("/")
        or not fact.column
        or fact.row_count < 1
        or fact.recognized_values != ("0", "1")
        or not fact.content_digest.startswith("sha256:")
        or len(fact.content_digest) != 71
    ):
        return False
    try:
        int(fact.content_digest.removeprefix("sha256:"), 16)
    except ValueError:
        return False
    return True


def _unique_by_token(
    items: tuple[_TokenValue, ...],
) -> dict[str, _TokenValue] | None:
    by_token = {item.token: item for item in items}
    return by_token if len(by_token) == len(items) else None


def _comparison_orientation(comparison: Eq) -> Orientation | None:
    left = comparison.left
    right = comparison.right
    if not comparison.token or not comparison.index_map:
        return None
    if left.asset != right.asset or left.row_domain != right.row_domain:
        return None
    if left.column == right.column:
        return None
    if not _projection_is_exact(left) or not _projection_is_exact(right):
        return None
    if left.runtime_type != right.runtime_type:
        return None
    return "repaired" if (left.parity + right.parity) % 2 else "direct"


def _projection_is_exact(projection: Projection) -> bool:
    if not projection.asset or not projection.row_domain or not projection.column:
        return False
    if not projection.transforms or projection.transforms[0].operation != "csv_subscript":
        return False
    current = "row"
    parity = 0
    for position, transform in enumerate(projection.transforms):
        if transform.operation == "whitespace_strip":
            if position + 1 >= len(projection.transforms) or projection.transforms[
                position + 1
            ].operation not in {
                "builtin_int",
                "builtin_float",
                "builtin_decimal",
                "builtin_fraction",
            }:
                return False
        checked = _apply_transform(current, transform)
        if checked is None:
            return False
        current, delta = checked
        parity += delta
    return current == projection.runtime_type and parity % 2 == projection.parity % 2


def _apply_transform(current: str, transform: PrimitiveTransform) -> tuple[str, int] | None:
    rule = _TRANSFORMS.get(transform.operation)
    if rule is None:
        return None
    allowed_inputs, fixed_output, parity_delta = rule
    if (
        transform.input_type != current
        or current not in allowed_inputs
        or transform.parity_delta != parity_delta
    ):
        return None
    output = current if fixed_output is None else fixed_output
    if transform.output_type != output:
        return None
    return output, parity_delta


def _selector_is_canonical(selector: Selector) -> bool:
    if not selector.token:
        return False
    false = _fraction(selector.false_value)
    true = _fraction(selector.true_value)
    if false is None or true is None:
        return False
    if selector.false_value.number_type != selector.true_value.number_type:
        return False
    return true > false


def _fraction(number: ExactNumber) -> Fraction | None:
    try:
        numerator, denominator = number.value.split("/", 1)
        value = Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError):
        return None
    if f"{value.numerator}/{value.denominator}" != number.value:
        return None
    return value


def _fold_is_closed(fold: Fold, selectors: dict[str, Selector]) -> bool:
    if not fold.token or not fold.row_domain or not fold.index_map or not fold.selector_tokens:
        return False
    if not fold.selector_tokens <= selectors.keys():
        return False
    for token in fold.selector_tokens:
        comparison = selectors[token].predicate.expression
        if comparison.left.row_domain != fold.row_domain or comparison.index_map != fold.index_map:
            return False
    element_type: str | None = None
    if isinstance(fold.element, Selector):
        if fold.selector_tokens != frozenset({fold.element.token}):
            return False
        element_type = fold.element.false_value.number_type
    elif isinstance(fold.element, Gated):
        if (
            fold.element.selector_tokens != fold.selector_tokens
            or fold.element.row_domain != fold.row_domain
            or fold.element.index_map != fold.index_map
            or not _projection_is_exact(fold.element.projection)
            or fold.element.projection.row_domain != fold.row_domain
        ):
            return False
        selector_types = {
            selectors[token].false_value.number_type for token in fold.selector_tokens
        }
        if len(selector_types) != 1:
            return False
        selector_type = next(iter(selector_types))
        element_type = _numeric_result_type(
            fold.element.projection.runtime_type,
            selector_type,
        )
    if element_type is None:
        return False
    initial_type = (
        fold.initial_value.number_type if _fraction(fold.initial_value) is not None else None
    )
    if initial_type is None:
        return False
    first_result = _numeric_result_type(initial_type, element_type)
    return first_result is not None and _numeric_result_type(first_result, element_type) is not None


def _numeric_result_type(left: str, right: str) -> str | None:
    """The result type of Python addition/multiplication for supported numbers."""

    if left not in _NUMERIC_TYPES or right not in _NUMERIC_TYPES:
        return None
    if "decimal" in {left, right}:
        return "decimal" if {left, right} <= {"int", "decimal"} else None
    if "float" in {left, right}:
        return "float"
    if "fraction" in {left, right}:
        return "fraction"
    return "int"
