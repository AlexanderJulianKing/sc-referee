"""Mutation tests for the small founder-orientation v3 certificate kernel."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sc_referee.scientific_checks.founder_orientation_certificate import (
    verify_orientation_certificate,
)
from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
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
)


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
    return OrientationCertificate(
        "workflow/analysis.py",
        (comparison,),
        (selector,),
        (fold,),
        (sink,),
        (frozenset({"repaired"}),),
        (),
        frozenset({"comparison"}),
        frozenset(),
        (),
    )


def test_kernel_accepts_one_closed_repaired_certificate() -> None:
    verified = verify_orientation_certificate(_certificate())
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
    assert verify_orientation_certificate(certificate) is None


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
        verify_orientation_certificate(replace(certificate, comparisons=(bad_comparison,))) is None
    )
