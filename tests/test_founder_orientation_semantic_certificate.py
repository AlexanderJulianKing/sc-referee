"""Mutation tests for the small founder-orientation v3 certificate kernel."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sc_referee.scientific_checks.founder_orientation_certificate import (
    verify_orientation_certificate,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    CsvBinaryDomainFact,
    Effect,
    Eq,
    ExactNumber,
    Fold,
    OrientationCertificate,
    Predicate,
    PrimitiveTransform,
    Projection,
    Selector,
    SinkProof,
    TransformDomainObligation,
)

_DOMAIN_DIGEST = "sha256:" + "a" * 64


def _certificate() -> OrientationCertificate:
    direct = Projection(
        "inputs/data.csv",
        "rows",
        "observed",
        0,
        "int",
        (
            PrimitiveTransform("csv_subscript", "row", "str", 0),
            PrimitiveTransform("builtin_int", "str", "int", 0),
        ),
    )
    complemented = Projection(
        "inputs/data.csv",
        "rows",
        "founder",
        1,
        "int",
        (
            PrimitiveTransform("csv_subscript", "row", "str", 0),
            PrimitiveTransform("builtin_int", "str", "int", 0),
            PrimitiveTransform("one_minus", "int", "int", 1),
        ),
    )
    comparison = Eq(direct, complemented, "csv-order", "comparison")
    selector = Selector(
        Predicate(comparison),
        ExactNumber("int", "0/1"),
        ExactNumber("int", "1/1"),
        "selector",
    )
    fold = Fold(
        "sum",
        "rows",
        selector,
        ExactNumber("int", "0/1"),
        "csv-order",
        "fold",
        frozenset({"selector"}),
    )
    sink = SinkProof(
        "results/report.md",
        frozenset({"fold"}),
        frozenset({"selector"}),
        frozenset({"comparison"}),
        frozenset({"inputs/data.csv", "rows"}),
        frozenset({"score", "report"}),
    )
    observed_fact = CsvBinaryDomainFact(
        "inputs/data.csv", _DOMAIN_DIGEST, "observed", 4, ("0", "1")
    )
    founder_fact = CsvBinaryDomainFact("inputs/data.csv", _DOMAIN_DIGEST, "founder", 4, ("0", "1"))
    obligations = (
        TransformDomainObligation(
            "inputs/data.csv",
            _DOMAIN_DIGEST,
            "rows",
            "founder",
            ("csv_subscript", "builtin_int", "one_minus"),
            founder_fact,
        ),
        TransformDomainObligation(
            "inputs/data.csv",
            _DOMAIN_DIGEST,
            "rows",
            "observed",
            ("csv_subscript", "builtin_int"),
            observed_fact,
        ),
    )
    return OrientationCertificate(
        source_path="workflow/analysis.py",
        comparisons=(comparison,),
        selectors=(selector,),
        folds=(fold,),
        sinks=(sink,),
        reaching_path_orientations=(frozenset({"repaired"}),),
        effects=(),
        transform_domain_obligations=obligations,
        proven_domain_facts=(founder_fact, observed_fact),
        all_report_comparison_tokens=frozenset({"comparison"}),
        dead_comparison_tokens=frozenset(),
        evidence=(),
    )


def test_kernel_accepts_one_closed_repaired_certificate() -> None:
    certificate = _certificate()
    verified = verify_orientation_certificate(
        certificate, trusted_domain_facts=certificate.proven_domain_facts
    )
    assert verified is not None
    assert verified.orientation == "repaired"


@pytest.mark.parametrize(
    "mutation",
    [
        "row-domain",
        "transform",
        "selector",
        "sink-lineage",
        "path-agreement",
        "relevant-effect",
        "competing-comparison",
    ],
)
def test_kernel_rejects_each_broken_proof_obligation(mutation: str) -> None:
    certificate = _certificate()
    comparison = certificate.comparisons[0]
    selector = certificate.selectors[0]
    fold = certificate.folds[0]
    sink = certificate.sinks[0]
    if mutation == "row-domain":
        wrong = replace(comparison.right, row_domain="other-rows")
        comparison = replace(comparison, right=wrong)
        selector = replace(selector, predicate=Predicate(comparison))
        fold = replace(fold, element=selector)
        certificate = replace(
            certificate,
            comparisons=(comparison,),
            selectors=(selector,),
            folds=(fold,),
        )
    elif mutation == "transform":
        wrong = replace(
            comparison.right,
            transforms=(
                *comparison.right.transforms[:-1],
                PrimitiveTransform("opaque", "int", "int", 1),
            ),
        )
        comparison = replace(comparison, right=wrong)
        selector = replace(selector, predicate=Predicate(comparison))
        fold = replace(fold, element=selector)
        certificate = replace(
            certificate,
            comparisons=(comparison,),
            selectors=(selector,),
            folds=(fold,),
        )
    elif mutation == "selector":
        selector = replace(selector, true_value=ExactNumber("int", "0/1"))
        fold = replace(fold, element=selector)
        certificate = replace(certificate, selectors=(selector,), folds=(fold,))
    elif mutation == "sink-lineage":
        certificate = replace(certificate, sinks=(replace(sink, fold_tokens=frozenset()),))
    elif mutation == "path-agreement":
        certificate = replace(
            certificate,
            reaching_path_orientations=(frozenset({"direct", "repaired"}),),
        )
    elif mutation == "relevant-effect":
        certificate = replace(
            certificate,
            effects=(
                Effect(frozenset(), frozenset({"score"}), frozenset(), False, True, "opaque"),
            ),
        )
    else:
        certificate = replace(
            certificate,
            all_report_comparison_tokens=frozenset({"comparison", "competitor"}),
        )
    assert (
        verify_orientation_certificate(
            certificate, trusted_domain_facts=certificate.proven_domain_facts
        )
        is None
    )


@pytest.mark.parametrize("operation", ["bitxor_one", "abs_difference_one", "boolean_not"])
def test_kernel_rejects_a_binary_only_recode_without_a_binary_domain(operation: str) -> None:
    certificate = _certificate()
    comparison = certificate.comparisons[0]
    output_type = "bool" if operation == "boolean_not" else "int"
    transform = PrimitiveTransform(operation, "int", output_type, 1)
    right = replace(
        comparison.right,
        runtime_type=output_type,
        parity=1,
        transforms=(*comparison.right.transforms[:-1], transform),
    )
    bad_comparison = replace(comparison, right=right)
    assert (
        verify_orientation_certificate(
            replace(certificate, comparisons=(bad_comparison,)),
            trusted_domain_facts=certificate.proven_domain_facts,
        )
        is None
    )


@pytest.mark.parametrize("mutation", ["path", "digest", "column"])
def test_kernel_rejects_a_domain_discharge_for_the_wrong_binding(mutation: str) -> None:
    certificate = _certificate()
    obligation = certificate.transform_domain_obligations[0]
    fact = obligation.domain_fact
    assert fact is not None
    if mutation == "path":
        wrong_fact = replace(fact, path="inputs/other.csv")
    elif mutation == "digest":
        wrong_fact = replace(fact, content_digest="sha256:" + "b" * 64)
    else:
        wrong_fact = replace(fact, column="other")
    mutated = replace(
        certificate,
        transform_domain_obligations=(
            replace(obligation, domain_fact=wrong_fact),
            *certificate.transform_domain_obligations[1:],
        ),
        proven_domain_facts=(wrong_fact, *certificate.proven_domain_facts[1:]),
    )
    assert (
        verify_orientation_certificate(mutated, trusted_domain_facts=mutated.proven_domain_facts)
        is None
    )
