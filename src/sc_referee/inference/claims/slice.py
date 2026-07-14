"""Possible-producer traversal and universal whole-sub-DAG must-consumption proofs."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Mapping

from sc_referee.inference.analysis.dependence import (
    AllOf, Alternative, Atom, ChoiceOf, DependenceProgram, DepExpr, Unknown,
)
from sc_referee.inference.claims.inventory import ReportClaim
from sc_referee.inference.claims.sensitivity import (
    CanonicalForm, LeafForm, SolverApplication, apply_transform, form_sensitive,
)


@dataclass(frozen=True)
class Boundary:
    id: str
    reason: str


@dataclass(frozen=True)
class UnknownProducer:
    boundary_id: str


@dataclass(frozen=True)
class CompleteSubDAG:
    producer: str
    root: str
    alternative_id: str
    reachable_nodes: frozenset[str]
    whole_subdag: bool = True


@dataclass(frozen=True)
class CompositionProof:
    status: str  # PROVED | REFUTED | UNKNOWN
    reason: str | None
    whole_subdag: bool
    canonical_forms: tuple[CanonicalForm, ...] = ()
    subdags: tuple[CompleteSubDAG, ...] = ()


@dataclass(frozen=True)
class ClaimSlice:
    claim_id: str
    possible_producers: frozenset[object]
    unavoidable_producers: frozenset[str]
    unknown_boundaries: tuple[Boundary, ...]
    derivation: DependenceProgram
    coverage_complete: bool
    composition_proofs: Mapping[str, CompositionProof]


def _possible_expr(expression: DepExpr, program: DependenceProgram, stack=frozenset()):
    producers: set[object] = set()
    boundaries: set[Boundary] = set()
    if isinstance(expression, Unknown):
        boundary = Boundary(expression.boundary_id, expression.reason)
        return {UnknownProducer(expression.boundary_id)}, {boundary}
    if isinstance(expression, Atom):
        if expression.node in program.producers:
            return {expression.node}, set()
        if expression.node in stack:
            boundary = Boundary(f"cycle:{expression.node}", "cyclic_dependence")
            return {UnknownProducer(boundary.id)}, {boundary}
        derivation = program.derivations.get(expression.node)
        if derivation is None:
            boundary = Boundary(f"missing:{expression.node}", "producer_or_derivation_not_registered")
            return {UnknownProducer(boundary.id)}, {boundary}
        for alternative in derivation.alternatives:
            if alternative.guard.feasible is False:
                continue
            found, unknown = _possible_expr(alternative.requirements, program,
                                            stack | {expression.node})
            producers |= found
            boundaries |= unknown
        return producers, boundaries
    if isinstance(expression, (AllOf, ChoiceOf)):
        for item in expression.items:
            found, unknown = _possible_expr(item, program, stack)
            producers |= found
            boundaries |= unknown
        return producers, boundaries
    boundary = Boundary("dep-expr", "unsupported_dependence_expression")
    return {UnknownProducer(boundary.id)}, {boundary}


def possible_producers(root: str, program: DependenceProgram):
    if root in program.producers:
        return {root}, set()
    derivation = program.derivations.get(root)
    if derivation is None:
        boundary = Boundary(f"root:{root}", "claim_root_has_no_derivation")
        return {UnknownProducer(boundary.id)}, {boundary}
    producers: set[object] = set()
    boundaries: set[Boundary] = set()
    for alternative in derivation.alternatives:
        if alternative.guard.feasible is False:
            continue
        found, unknown = _possible_expr(alternative.requirements, program, frozenset({root}))
        producers |= found
        boundaries |= unknown
    return producers, boundaries


def _collect_nodes(expression: DepExpr, program: DependenceProgram, nodes: set[str], stack: set[str]):
    if isinstance(expression, Atom):
        nodes.add(expression.node)
        if expression.node in stack:
            return
        derivation = program.derivations.get(expression.node)
        if derivation is not None:
            for alternative in derivation.alternatives:
                if alternative.guard.feasible is not False:
                    _collect_nodes(alternative.requirements, program, nodes,
                                   stack | {expression.node})
    elif isinstance(expression, (AllOf, ChoiceOf)):
        for item in expression.items:
            _collect_nodes(item, program, nodes, stack)


def complete_subdag(producer: str, root: str, alternative: Alternative,
                    program: DependenceProgram) -> CompleteSubDAG:
    """Construct the complete reconvergent/alternative sub-DAG before any sensitivity decision."""
    nodes = {root}
    _collect_nodes(alternative.requirements, program, nodes, {root})
    return CompleteSubDAG(producer, root, alternative.id, frozenset(nodes), True)


class _Canonicalizer:
    def __init__(self, program: DependenceProgram):
        self.program = program
        self.nodes_seen = 0
        self.failure: str | None = None

    def _tick(self):
        self.nodes_seen += 1
        if self.nodes_seen > self.program.max_canonical_nodes:
            self.failure = "canonicalization_resource_exhaustion"
            return False
        return True

    def atom_forms(self, atom: Atom, stack: frozenset[str]):
        if not self._tick():
            return ()
        if not atom.evidence.sound_for_must():
            self.failure = "uncertified_or_imprecise_edge"
            return ()
        if atom.node in self.program.producers:
            return (LeafForm(frozenset({atom.node})),)
        if atom.node in stack:
            self.failure = "cyclic_dependence"
            return ()
        derivation = self.program.derivations.get(atom.node)
        if derivation is None:
            self.failure = "missing_derivation"
            return ()
        forms = []
        feasible = False
        for alternative in derivation.alternatives:
            if alternative.guard.feasible is False:
                continue
            feasible = True
            if alternative.guard.feasible is None or not alternative.guard.pinned:
                self.failure = "unresolved_branch_or_config_feasibility"
                return ()
            forms.extend(self.alternative_forms(alternative, stack | {atom.node}))
            if self.failure:
                return ()
        if not feasible:
            self.failure = "no_pinned_feasible_alternative"
            return ()
        return tuple(forms)

    def input_combinations(self, expression: DepExpr, stack: frozenset[str]):
        if isinstance(expression, Unknown):
            self.failure = "unknown_or_havoc_boundary"
            return ()
        if isinstance(expression, Atom):
            return tuple((form,) for form in self.atom_forms(expression, stack))
        if isinstance(expression, ChoiceOf):
            combinations = []
            for item in expression.items:
                combinations.extend(self.input_combinations(item, stack))
                if self.failure:
                    return ()
            return tuple(combinations)
        if isinstance(expression, AllOf):
            if not expression.consumption_complete:
                self.failure = "allof_consumption_certificate_incomplete"
                return ()
            choices = []
            for item in expression.items:
                item_combinations = self.input_combinations(item, stack)
                if self.failure:
                    return ()
                # Nested AllOf is conservatively unsupported: an enclosing transform cannot recover
                # the missing grouping without a verified algebra bridge.
                flattened = tuple(combo[0] for combo in item_combinations if len(combo) == 1)
                if len(flattened) != len(item_combinations):
                    self.failure = "nested_allof_requires_verified_bridge"
                    return ()
                choices.append(flattened)
            return tuple(tuple(combo) for combo in product(*choices))
        self.failure = "unsupported_dependence_expression"
        return ()

    def alternative_forms(self, alternative: Alternative, stack: frozenset[str]):
        if not self._tick():
            return ()
        if alternative.guard.feasible is None or not alternative.guard.pinned:
            self.failure = "unresolved_branch_or_config_feasibility"
            return ()
        if alternative.constraints:
            self.failure = "alternative_constraints_outside_closed_solver"
            return ()
        combinations = self.input_combinations(alternative.requirements, stack)
        if self.failure:
            return ()
        forms = []
        for children in combinations:
            applied: SolverApplication = apply_transform(alternative.transform, children)
            if applied.status != "PROVED" or applied.form is None:
                self.failure = applied.reason or "sensitivity_solver_unknown"
                return ()
            forms.append(applied.form)
        return tuple(forms)


def prove_must_consumption(producer: str, root: str, program: DependenceProgram) -> CompositionProof:
    if root in program.producers:
        status = "PROVED" if root == producer else "REFUTED"
        return CompositionProof(status, None if status == "PROVED" else "different_root_producer",
                                True)
    derivation = program.derivations.get(root)
    if derivation is None:
        return CompositionProof("UNKNOWN", "claim_root_has_no_derivation", True)

    all_forms: list[CanonicalForm] = []
    subdags: list[CompleteSubDAG] = []
    feasible = False
    for alternative in derivation.alternatives:
        if alternative.guard.feasible is False:
            continue
        feasible = True
        if alternative.guard.feasible is None or not alternative.guard.pinned:
            return CompositionProof("UNKNOWN", "unresolved_branch_or_config_feasibility", True,
                                    tuple(all_forms), tuple(subdags))
        subdag = complete_subdag(producer, root, alternative, program)
        subdags.append(subdag)
        canonicalizer = _Canonicalizer(program)
        forms = canonicalizer.alternative_forms(alternative, frozenset({root}))
        if canonicalizer.failure:
            return CompositionProof("UNKNOWN", canonicalizer.failure, True,
                                    tuple(all_forms), tuple(subdags))
        if not forms:
            return CompositionProof("UNKNOWN", "canonicalization_produced_no_form", True,
                                    tuple(all_forms), tuple(subdags))
        for form in forms:
            sensitive = form_sensitive(form, producer)
            if sensitive is None:
                return CompositionProof("UNKNOWN", "end_to_end_sensitivity_unknown", True,
                                        tuple(all_forms), tuple(subdags))
            if sensitive is False:
                return CompositionProof("REFUTED", "one_feasible_alternative_is_not_sensitive", True,
                                        tuple(all_forms + list(forms)), tuple(subdags))
        all_forms.extend(forms)
    if not feasible:
        return CompositionProof("UNKNOWN", "no_pinned_feasible_root_alternative", True,
                                tuple(all_forms), tuple(subdags))
    return CompositionProof("PROVED", None, True, tuple(all_forms), tuple(subdags))


def slice_claim(program: DependenceProgram, claim: ReportClaim) -> ClaimSlice:
    possible, boundaries = possible_producers(claim.value, program)
    unavoidable = set()
    proofs = {}
    if claim.root_exact:
        for producer in sorted(item for item in possible if isinstance(item, str)):
            proof = prove_must_consumption(producer, claim.value, program)
            proofs[producer] = proof
            if proof.status == "PROVED":
                unavoidable.add(producer)
            elif proof.status == "UNKNOWN":
                boundaries.add(Boundary(f"composition:{producer}",
                                        proof.reason or "composition_unknown"))
    else:
        boundaries.add(Boundary(f"claim:{claim.claim_id}", "claim_root_not_exact"))
    coverage_complete = not boundaries and claim.root_exact
    return ClaimSlice(claim.claim_id, frozenset(possible), frozenset(unavoidable),
                      tuple(sorted(boundaries, key=lambda boundary: boundary.id)),
                      program, coverage_complete, dict(proofs))
