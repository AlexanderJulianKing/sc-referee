"""Exact, digest-bound discharge providers. Policies contain no computation."""
from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from hashlib import sha256
from inspect import getsource
from math import comb
from typing import Mapping, Protocol

from sc_referee.inference.claims.sensitivity import (
    exact_rational_rank, exact_rational_rank_sensitive, unit_partition_sensitive,
)
from sc_referee.inference.domains.unit import UnitRelationFact


@dataclass(frozen=True)
class ProviderIdentity:
    id: str
    version: str
    implementation_digest: str
    input_schema_digest: str
    output_schema_digest: str


@dataclass(frozen=True)
class ProviderRequest:
    provider: ProviderIdentity
    inputs: Mapping[str, object]
    assumptions: frozenset[str]
    request_digest: str
    expected_relation: str


@dataclass(frozen=True)
class ProviderResult:
    status: str
    relation: str
    typed_outputs: Mapping[str, object]
    derivation: tuple[object, ...]
    provider: ProviderIdentity
    input_digest: str
    obligations: tuple[str, ...] = ()


class DischargeProvider(Protocol):
    identity: ProviderIdentity
    output_relations: frozenset[str]

    def discharge(self, request: ProviderRequest) -> ProviderResult: ...


def _jsonable(value):
    if dataclasses.is_dataclass(value):
        return {item.name: _jsonable(getattr(value, item.name)) for item in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_jsonable(item) for item in value), key=repr)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"provider input is outside immutable typed subset: {type(value)!r}")


def _digest(value) -> str:
    payload = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"))
    return "sha256:" + sha256(payload.encode()).hexdigest()


def _identity(provider_id: str, implementation_source: str = "",
              input_fields=(), output_relations=()) -> ProviderIdentity:
    implementation = "sha256:" + sha256(implementation_source.encode()).hexdigest()
    input_schema = "sha256:" + sha256(json.dumps(
        sorted(input_fields), separators=(",", ":")
    ).encode()).hexdigest()
    output_schema = "sha256:" + sha256(json.dumps(
        sorted(output_relations), separators=(",", ":")
    ).encode()).hexdigest()
    return ProviderIdentity(provider_id, "1", implementation, input_schema, output_schema)


def _result(request: ProviderRequest, status: str, outputs=None, obligations=()):
    outputs = outputs or {}
    derivation = (request.provider.id, request.provider.version, request.expected_relation,
                  request.request_digest, _digest(outputs))
    return ProviderResult(status, request.expected_relation, outputs, derivation,
                          request.provider, _digest(request.inputs), tuple(obligations))


class DischargeRegistry:
    def __init__(self):
        self._providers: dict[tuple[str, str, str], DischargeProvider] = {}

    @property
    def providers(self):
        return tuple(self._providers.values())

    def register(self, provider: DischargeProvider) -> None:
        key = (provider.identity.id, provider.identity.version, provider.identity.implementation_digest)
        if key in self._providers:
            raise ValueError(f"duplicate provider identity: {provider.identity.id}")
        self._providers[key] = provider

    def resolve_exact(self, provider_id: str, version: str, digest: str):
        return self._providers.get((provider_id, version, digest))

    def invoke(self, invocation, bound_facts: Mapping[str, object]) -> ProviderResult:
        provider = self.resolve_exact(invocation.provider_id, invocation.provider_version,
                                      invocation.provider_digest)
        if provider is None:
            identity = ProviderIdentity(invocation.provider_id, invocation.provider_version,
                                        invocation.provider_digest, "", "")
            try:
                input_digest = _digest(bound_facts)
            except TypeError:
                input_digest = "sha256:unsupported"
            return ProviderResult("UNKNOWN", invocation.expected_relation, {},
                                  ("provider_resolution_failed",), identity, input_digest,
                                  ("provider identity/version/digest did not resolve exactly",))
        try:
            request_digest = _digest({"inputs": bound_facts, "relation": invocation.expected_relation})
        except TypeError as error:
            request_digest = "sha256:unsupported"
            return ProviderResult("UNKNOWN", invocation.expected_relation, {},
                                  (provider.identity.id, "unsupported_input"), provider.identity,
                                  request_digest, (str(error),))
        request = ProviderRequest(provider.identity, dict(bound_facts), frozenset(),
                                  request_digest, invocation.expected_relation)
        if invocation.expected_relation not in provider.output_relations:
            return _result(request, "UNKNOWN", obligations=("provider does not emit requested relation",))
        try:
            return provider.discharge(request)
        except (TypeError, ValueError, KeyError, ZeroDivisionError, IndexError) as error:
            return _result(request, "UNKNOWN", obligations=(f"unsupported typed input: {error}",))


def _q(value) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("booleans are not rational observations")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if (isinstance(value, tuple) and len(value) == 2
            and all(isinstance(item, int) and not isinstance(item, bool) for item in value)):
        return Fraction(value[0], value[1])
    raise TypeError("exact rational inputs must be integers or Fractions")


def _matrix(value, rows=None):
    matrix = tuple(tuple(_q(item) for item in row) for row in value)
    if rows is not None and len(matrix) != rows:
        raise ValueError("matrix row count mismatch")
    if matrix and any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError("ragged matrix")
    return matrix


def _transpose(matrix):
    return tuple(tuple(row[index] for row in matrix) for index in range(len(matrix[0]))) if matrix else ()


def _solve(matrix, vector):
    rows = [list(row) + [value] for row, value in zip(matrix, vector)]
    if not rows:
        return ()
    width = len(matrix[0])
    pivot_row = 0
    pivots = []
    for column in range(width):
        pivot = next((index for index in range(pivot_row, len(rows)) if rows[index][column] != 0), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        divisor = rows[pivot_row][column]
        rows[pivot_row] = [item / divisor for item in rows[pivot_row]]
        for index, row in enumerate(rows):
            if index == pivot_row or row[column] == 0:
                continue
            factor = row[column]
            rows[index] = [item - factor * base for item, base in zip(row, rows[pivot_row])]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    if any(all(item == 0 for item in row[:width]) and row[width] != 0 for row in rows):
        raise ValueError("linear system inconsistent")
    solution = [Fraction(0) for _ in range(width)]
    for row_index, column in enumerate(pivots):
        solution[column] = rows[row_index][width]
    return tuple(solution)


def _matvec(matrix, vector):
    return tuple(sum((item * vector[index] for index, item in enumerate(row)), Fraction(0))
                 for row in matrix)


def _least_squares(response, design):
    if not design or not design[0]:
        return tuple(response), ()
    xt = _transpose(design)
    xtx = tuple(tuple(sum((xt[i][k] * design[k][j] for k in range(len(design))), Fraction(0))
                      for j in range(len(xt))) for i in range(len(xt)))
    xty = tuple(sum((column[k] * response[k] for k in range(len(response))), Fraction(0))
                for column in xt)
    beta = _solve(xtx, xty)
    fitted = _matvec(design, beta)
    return tuple(y - yhat for y, yhat in zip(response, fitted)), beta


def _with_intercept(matrix, n):
    return tuple((Fraction(1),) + tuple(matrix[index]) for index in range(n))


def _r2(response, predictors):
    n = len(response)
    mean = sum(response, Fraction(0)) / n
    tss = sum(((item - mean) ** 2 for item in response), Fraction(0))
    if tss == 0:
        return None
    residual, _ = _least_squares(response, _with_intercept(predictors, n))
    rss = sum((item ** 2 for item in residual), Fraction(0))
    return Fraction(1) - rss / tss


def _residualize_columns(matrix, design):
    if not matrix or not matrix[0]:
        return matrix
    columns = _transpose(matrix)
    residual_columns = tuple(_least_squares(column, design)[0] for column in columns)
    return _transpose(residual_columns)


class ExactRankProvider:
    identity = _identity("exact_rational_rank.v1")
    input_fields = frozenset({"matrix", "target_column"})
    output_relations = frozenset({"TargetEstimable", "TargetAliased"})

    def discharge(self, request):
        matrix = _matrix(request.inputs["matrix"])
        target = request.inputs["target_column"]
        sensitive = exact_rational_rank_sensitive(matrix, target_column=target)
        if sensitive is None:
            return _result(request, "UNKNOWN", obligations=("rank sensitivity unsupported",))
        truth = sensitive if request.expected_relation == "TargetEstimable" else not sensitive
        return _result(request, "PROVED" if truth else "REFUTED",
                       {"rank": exact_rational_rank(matrix), "target_estimable": sensitive})


class ConfoundingMetricsQProvider:
    identity = _identity("confounding_metrics_q.v1")
    input_fields = frozenset({
        "target", "included", "omitted", "nuisance", "omitted_r2_threshold", "vif_threshold",
    })
    output_relations = frozenset({"OmittedNuisancePresent", "OmittedPartialR2AtLeast", "VifAtLeast",
                                  "OmittedPartialR2Below", "VifBelow"})

    def discharge(self, request):
        target = tuple(_q(item) for item in request.inputs["target"])
        n = len(target)
        if n == 0:
            return _result(request, "UNKNOWN", obligations=("empty target",))
        included = _matrix(request.inputs["included"], n)
        omitted = _matrix(request.inputs["omitted"], n)
        nuisance = _matrix(request.inputs["nuisance"], n)
        omitted_threshold = _q(request.inputs["omitted_r2_threshold"])
        vif_threshold = _q(request.inputs["vif_threshold"])

        nuisance_r2 = _r2(target, nuisance)
        if nuisance_r2 is None:
            return _result(request, "UNKNOWN", obligations=("target has no variation",))
        vif = "inf" if nuisance_r2 == 1 else Fraction(1) / (Fraction(1) - nuisance_r2)

        w = _with_intercept(included, n)
        target_residual, _ = _least_squares(target, w)
        target_ss = sum((item ** 2 for item in target_residual), Fraction(0))
        if omitted and omitted[0] and target_ss != 0:
            omitted_residual = _residualize_columns(omitted, w)
            residual, _ = _least_squares(target_residual, omitted_residual)
            rss = sum((item ** 2 for item in residual), Fraction(0))
            partial_r2 = Fraction(1) - rss / target_ss
        else:
            partial_r2 = Fraction(0)

        leakage = {}
        if omitted and omitted[0]:
            design = tuple(tuple(w[index]) + (target[index],) for index in range(n))
            for index, column in enumerate(_transpose(omitted)):
                _, beta = _least_squares(column, design)
                leakage[f"omitted_{index}"] = beta[-1]

        relation = request.expected_relation
        truth = {
            "OmittedNuisancePresent": bool(omitted and omitted[0]),
            "OmittedPartialR2AtLeast": partial_r2 >= omitted_threshold,
            "OmittedPartialR2Below": partial_r2 < omitted_threshold,
            "VifAtLeast": vif == "inf" or vif >= vif_threshold,
            "VifBelow": vif != "inf" and vif < vif_threshold,
        }[relation]
        outputs = {"r2": nuisance_r2, "vif": vif, "omitted_partial_r2": partial_r2,
                   "ovb_multipliers": leakage, "omitted_r2_threshold": omitted_threshold,
                   "vif_threshold": vif_threshold}
        return _result(request, "PROVED" if truth else "REFUTED", outputs)


class OraJointCorrectionProvider:
    identity = _identity("ora_joint_correction.v1")
    input_fields = frozenset({
        "population", "term_size", "draws", "overlap", "family_raw_pvalues",
        "target_index", "procedure", "alpha", "reported_adjusted_p",
        "reported_significant", "family_complete",
    })
    output_relations = frozenset({"ReportedMoreSignificantThanCorrected",
                                  "ReportedNotMoreSignificantThanCorrected"})

    def discharge(self, request):
        population = request.inputs["population"]
        term_size = request.inputs["term_size"]
        draws = request.inputs["draws"]
        overlap = request.inputs["overlap"]
        family = request.inputs["family_raw_pvalues"]
        target_index = request.inputs["target_index"]
        procedure = request.inputs["procedure"]
        alpha = _q(request.inputs["alpha"])
        reported = _q(request.inputs["reported_adjusted_p"])
        reported_significant = request.inputs["reported_significant"]
        family_complete = request.inputs["family_complete"]
        if (not all(isinstance(item, int) and not isinstance(item, bool)
                    for item in (population, term_size, draws, overlap, target_index))
                or population <= 0 or not 0 <= term_size <= population
                or not 0 <= draws <= population or not 0 <= overlap <= min(term_size, draws)
                or not isinstance(family, tuple) or not family
                or not 0 <= target_index < len(family)
                or not isinstance(reported_significant, bool)
                or family_complete is not True
                or procedure not in {"bh", "bonferroni"}
                or not 0 < alpha < 1 or not 0 <= reported <= 1):
            return _result(request, "UNKNOWN", obligations=("unsupported ORA cells",))
        try:
            raw_family = tuple(_q(item) for item in family)
        except (TypeError, ValueError, ZeroDivisionError):
            return _result(request, "UNKNOWN", obligations=("p-value family is not exact rational",))
        if any(item < 0 or item > 1 for item in raw_family):
            return _result(request, "UNKNOWN", obligations=("p-value outside [0,1]",))

        def adjust(values):
            m = len(values)
            if procedure == "bonferroni":
                return tuple(min(Fraction(1), item * m) for item in values)
            ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
            adjusted = [Fraction(1)] * m
            running = Fraction(1)
            for rank_from_zero in range(m - 1, -1, -1):
                original_index, raw = ordered[rank_from_zero]
                rank = rank_from_zero + 1
                running = min(running, Fraction(m, rank) * raw, Fraction(1))
                adjusted[original_index] = running
            return tuple(adjusted)

        original_adjusted = adjust(raw_family)[target_index]
        if original_adjusted != reported or reported_significant != (reported < alpha):
            return _result(
                request,
                "UNKNOWN",
                obligations=("reported decision does not bind to declared complete procedure",),
            )
        denominator = comb(population, draws)
        tail = Fraction(0)
        for k in range(overlap, min(term_size, draws) + 1):
            if draws - k > population - term_size:
                continue
            tail += Fraction(comb(term_size, k) * comb(population - term_size, draws - k), denominator)
        corrected_family = list(raw_family)
        corrected_family[target_index] = tail
        corrected_adjusted = adjust(tuple(corrected_family))[target_index]
        more = reported_significant and corrected_adjusted >= alpha
        truth = more if request.expected_relation == "ReportedMoreSignificantThanCorrected" else not more
        outputs = {"population": population, "term_size": term_size, "draws": draws,
                   "overlap": overlap, "tail_p": tail,
                   "original_adjusted_p": original_adjusted,
                   "corrected_adjusted_p": corrected_adjusted,
                   "reported_adjusted_p": reported, "procedure": procedure,
                   "alpha": alpha, "target_index": target_index,
                   "significant_before": reported_significant,
                   "significant_after": corrected_adjusted < alpha}
        return _result(request, "PROVED" if truth else "REFUTED", outputs)


class SignParityProvider:
    identity = _identity("sign_parity.v1")
    input_fields = frozenset({"required_factors", "applied_multiplier"})
    output_relations = frozenset({"JointSignConsistent", "JointSignInconsistent"})

    def discharge(self, request):
        factors = tuple(request.inputs["required_factors"])
        applied = request.inputs["applied_multiplier"]
        if any(factor not in (-1, 1) for factor in factors) or applied not in (-1, 1):
            return _result(request, "UNKNOWN", obligations=("signs must be exact nonzero parity",))
        required = 1
        for factor in factors:
            required *= factor
        consistent = required == applied
        truth = consistent if request.expected_relation == "JointSignConsistent" else not consistent
        return _result(request, "PROVED" if truth else "REFUTED",
                       {"required_multiplier": required, "applied_multiplier": applied,
                        "joint_consistent": consistent})


class FiniteSetProvider:
    identity = _identity("finite_set_relations.v1")
    input_fields = frozenset({"left", "right", "member", "cardinality"})
    output_relations = frozenset({"Subset", "Equal", "Disjoint", "Intersects", "Member",
                                  "CardinalityEqual"})

    def discharge(self, request):
        left = request.inputs.get("left")
        right = request.inputs.get("right")
        if not isinstance(left, frozenset) or (right is not None and not isinstance(right, frozenset)):
            return _result(request, "UNKNOWN", obligations=("finite sets must be frozenset",))
        relation = request.expected_relation
        if relation == "Member":
            truth = request.inputs.get("member") in left
        elif relation == "CardinalityEqual":
            truth = len(left) == request.inputs.get("cardinality")
        elif right is None:
            return _result(request, "UNKNOWN", obligations=("binary set relation requires right",))
        elif relation == "Subset":
            truth = left <= right
        elif relation == "Equal":
            truth = left == right
        elif relation == "Disjoint":
            truth = left.isdisjoint(right)
        else:
            truth = not left.isdisjoint(right)
        return _result(request, "PROVED" if truth else "REFUTED",
                       {"intersection": left & right if right is not None else frozenset(),
                        "left_cardinality": len(left),
                        "right_cardinality": len(right) if right is not None else None})


@dataclass(frozen=True)
class ConsumerCoordinateContract:
    id: str
    coordinate_role: str
    lower: int
    lower_inclusive: bool
    upper_from_contig_length: int
    upper_inclusive: bool
    topology: str
    implementation_digest: str


def _coordinate_contract(contract_id, role, lower, lower_inclusive,
                         upper_offset, upper_inclusive, topology):
    payload = (f"{contract_id}|{role}|{lower}|{lower_inclusive}|{upper_offset}|"
               f"{upper_inclusive}|{topology}")
    return ConsumerCoordinateContract(
        contract_id, role, lower, lower_inclusive, upper_offset, upper_inclusive,
        topology, "sha256:" + sha256(payload.encode()).hexdigest(),
    )


_COORDINATE_CONTRACTS = {
    item.id: item for item in (
        _coordinate_contract("zero_based_half_open.linear.v1", "base_coordinate",
                             0, True, 0, False, "linear"),
        _coordinate_contract("one_based_closed.linear.v1", "base_coordinate",
                             1, True, 0, True, "linear"),
        _coordinate_contract("past_end_sentinel.linear.v1", "slice_boundary",
                             0, True, 0, True, "linear"),
    )
}


class IntervalBoundsProvider:
    identity = _identity("interval_bounds.v1")
    input_fields = frozenset({
        "value", "contig_length", "coordinate_role", "consumer_contract_id",
    })
    output_relations = frozenset({"CoordinateLegal", "CoordinateIllegal"})

    def discharge(self, request):
        value = _q(request.inputs["value"])
        length = request.inputs["contig_length"]
        contract = _COORDINATE_CONTRACTS.get(request.inputs.get("consumer_contract_id"))
        if (contract is None or request.inputs.get("coordinate_role") != contract.coordinate_role
                or not isinstance(length, int) or isinstance(length, bool) or length <= 0
                or contract.topology != "linear"):
            return _result(request, "UNKNOWN", obligations=(
                "consumer contract is not a registered code-owned coordinate contract",
            ))
        lower = Fraction(contract.lower)
        upper = Fraction(length + contract.upper_from_contig_length)
        lower_ok = value >= lower if contract.lower_inclusive else value > lower
        upper_ok = value <= upper if contract.upper_inclusive else value < upper
        legal = lower_ok and upper_ok
        truth = legal if request.expected_relation == "CoordinateLegal" else not legal
        return _result(request, "PROVED" if truth else "REFUTED",
                       {"legal": legal, "value": value, "lower": lower, "upper": upper,
                        "consumer_contract_id": contract.id,
                        "coordinate_role": contract.coordinate_role,
                        "topology": contract.topology,
                        "consumer_contract_digest": contract.implementation_digest})


class UnitPartitionProvider:
    identity = _identity("unit_partition.v1")
    input_fields = frozenset({"relation", "expected_kind"})
    output_relations = frozenset({"UnitRelationProved"})

    def discharge(self, request):
        relation = request.inputs.get("relation")
        if not isinstance(relation, UnitRelationFact) or unit_partition_sensitive(relation) is not True:
            return _result(request, "UNKNOWN", obligations=("unit relation lacks exact evidence",))
        expected = request.inputs.get("expected_kind")
        truth = relation.kind.value == expected
        return _result(request, "PROVED" if truth else "REFUTED",
                       {"relation_kind": relation.kind.value, "evidence_id": relation.evidence_id})


def builtin_registry() -> DischargeRegistry:
    registry = DischargeRegistry()
    for provider in (ExactRankProvider(), ConfoundingMetricsQProvider(), OraJointCorrectionProvider(),
                     SignParityProvider(), FiniteSetProvider(), IntervalBoundsProvider(),
                     UnitPartitionProvider()):
        provider.identity = _identity(
            provider.identity.id, getsource(sys.modules[__name__]), provider.input_fields,
            provider.output_relations,
        )
        registry.register(provider)
    return registry
