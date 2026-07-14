"""Total isolated evaluator for declarative policies; not wired to analyze or audit."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from sc_referee.inference.policy.schema import (
    FactRef, Judgment, ProofRule, RelationPremise, ValidityPolicy, validate_policy,
)


@dataclass(frozen=True)
class PolicySnapshot:
    inventory_complete: bool
    possible_producers: frozenset[str]
    covered_producers: frozenset[str]
    unknown_producers: frozenset[str]
    coverage: frozenset[str]
    relations: Mapping[object, str]
    facts: Mapping[str, object]
    assumptions: frozenset[str] = frozenset()


_MISSING = object()


def _fact_value(source: FactRef, snapshot: PolicySnapshot, claim, producer):
    value = snapshot.facts.get(source.fact_type, _MISSING)
    if value is _MISSING:
        return _MISSING
    if isinstance(value, Mapping) and producer is not None and producer in value:
        value = value[producer]
    if source.selector:
        selector = tuple(sorted(
            (name, claim if selected == "$claim" else producer if selected == "$producer" else selected)
            for name, selected in source.selector.items()
        ))
        if not isinstance(value, Mapping) or selector not in value:
            return _MISSING
        value = value[selector]
    return value


def _bound_value(source, snapshot: PolicySnapshot, claim, producer):
    if isinstance(source, FactRef):
        return _fact_value(source, snapshot, claim, producer)
    if source == "$claim":
        return claim
    if source == "$producer":
        return producer
    return source


def _relation_status(premise: RelationPremise, snapshot: PolicySnapshot,
                     producer: str | None, claim) -> str:
    if premise.arguments:
        arguments = tuple(_bound_value(item, snapshot, claim, producer)
                          for item in premise.arguments)
        if _MISSING in arguments:
            return "UNKNOWN"
        keys = (((premise.relation, arguments, producer), (premise.relation, arguments))
                if producer is not None else ((premise.relation, arguments),))
        for key in keys:
            try:
                if key in snapshot.relations:
                    return snapshot.relations[key]
            except TypeError:
                return "UNKNOWN"
        return "UNKNOWN"
    if producer is not None and (premise.relation, producer) in snapshot.relations:
        return snapshot.relations[(premise.relation, producer)]
    return snapshot.relations.get(premise.relation, "UNKNOWN")


def _bind_inputs(invocation, snapshot: PolicySnapshot, claim, producer):
    bound = {}
    for name, source in invocation.inputs.items():
        if isinstance(source, FactRef):
            value = _fact_value(source, snapshot, claim, producer)
            bound[name] = None if value is _MISSING else value
        elif source == "$claim":
            bound[name] = claim
        elif source == "$producer":
            bound[name] = producer
        else:
            bound[name] = source
    return bound


def _rule_proved(rule: ProofRule, snapshot: PolicySnapshot, claim,
                 producer: str | None, registry) -> tuple[bool, tuple[object, ...]]:
    if not set(rule.required_assumptions) <= snapshot.assumptions:
        return False, ()
    if any(_relation_status(premise, snapshot, producer, claim) != "PROVED"
           for premise in rule.premises):
        return False, ()
    provider_results = []
    for invocation in rule.discharge:
        if registry is None:
            return False, tuple(provider_results)
        try:
            result = registry.invoke(invocation, _bind_inputs(invocation, snapshot, claim, producer))
        except Exception as error:  # provider failure loses a proof but cannot escape evaluation
            provider_results.append(("PROVIDER_ERROR", type(error).__name__))
            return False, tuple(provider_results)
        provider_results.append(result)
        if result.status != "PROVED":
            return False, tuple(provider_results)
    return True, tuple(provider_results)


_STATUS_RANK = {"pass": 0, "informational": 1, "needs_evidence": 2,
                "major": 3, "blocker": 4, "not_audited": 5}


def _worst_status(statuses):
    return max(statuses, key=lambda status: _STATUS_RANK.get(status, 2), default="pass")


def evaluate(policy: ValidityPolicy, claim, snapshot: PolicySnapshot, registry=None) -> Judgment:
    validate_policy(policy)
    if any(_relation_status(premise, snapshot, None, claim) != "PROVED"
           for premise in policy.scope):
        return Judgment("ABSTAIN", "not_audited", obligations=("OUT_OF_SCOPE_OR_UNKNOWN",))

    producers = tuple(sorted(snapshot.possible_producers)) or (None,)
    clean_proofs = []
    violation_proofs = []
    for rule in policy.rules:
        for producer in producers:
            proved, provider_results = _rule_proved(rule, snapshot, claim, producer, registry)
            if not proved:
                continue
            proof = (rule, producer, provider_results)
            if rule.outcome == "CLEAN_PROOF":
                clean_proofs.append(proof)
            elif rule.outcome == "VIOLATION_WITNESS":
                violation_proofs.append(proof)

    if clean_proofs and violation_proofs:
        return Judgment("ABSTAIN", "needs_evidence",
                        derivation=tuple(item[0].id for item in clean_proofs + violation_proofs),
                        assumptions=snapshot.assumptions,
                        obligations=("INCONSISTENT_EVIDENCE",))

    if violation_proofs:
        rule = violation_proofs[0][0]  # declaration order is policy precedence
        return Judgment("VIOLATION_WITNESS", rule.max_external_status,
                        derivation=(rule.id,), assumptions=snapshot.assumptions)

    coverage_ok = (
        snapshot.inventory_complete
        and not snapshot.unknown_producers
        and policy.required_coverage <= snapshot.coverage
        and snapshot.possible_producers <= snapshot.covered_producers
    )
    clean_by_producer = {producer for _, producer, _ in clean_proofs}
    producer_clean = (None in clean_by_producer if not snapshot.possible_producers
                      else snapshot.possible_producers <= clean_by_producer)
    if coverage_ok and producer_clean:
        statuses = [rule.max_external_status for rule, _, _ in clean_proofs]
        return Judgment("CLEAN_PROOF", _worst_status(statuses),
                        derivation=tuple(dict.fromkeys(rule.id for rule, _, _ in clean_proofs)),
                        assumptions=snapshot.assumptions)

    obligations = []
    if not snapshot.inventory_complete:
        obligations.append("INVENTORY_INCOMPLETE")
    if snapshot.unknown_producers:
        obligations.append("UNKNOWN_PRODUCER")
    if not policy.required_coverage <= snapshot.coverage:
        obligations.append("COVERAGE_INCOMPLETE")
    if not snapshot.possible_producers <= snapshot.covered_producers:
        obligations.append("PRODUCER_UNCOVERED")
    if not producer_clean:
        obligations.append("CLEAN_RULE_UNPROVED")
    return Judgment("ABSTAIN", "not_audited", assumptions=snapshot.assumptions,
                    obligations=tuple(obligations or ("NO_RULE_PROVED",)))
