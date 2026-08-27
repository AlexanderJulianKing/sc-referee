"""Executed recon-only prototype for the narrow E14 singleton-binding admission."""

from __future__ import annotations

import ast
import copy
from collections.abc import Callable
from typing import Any, cast

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_3 as mt

Analyzer = Callable[..., mt.MultipleTestingDataflowResult]


def _pure_projection(node: ast.expr, outcome_name: str) -> bool:
    return bool(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and isinstance(node.slice, ast.Name)
        and node.slice.id == outcome_name
    )


def admit_singleton_projection_generator(content: bytes, outcome_columns: tuple[str, ...]) -> bytes:
    """Remove only one exact singleton projection-binding generator.

    This prototype substitutes pure frame projections to exercise the installed analyzer. A final
    implementation would retain one symbolic binding occurrence so its evaluation count remains
    exact; this recon does not propose source execution or a general comprehension evaluator.
    """

    tree = mt._bounded_parse(content)
    scope = tuple(item for item in tree.body if not mt._is_docstring(item))
    resolver, reason = mt._resolver(scope)
    if reason is not None or resolver is None:
        return content
    changed = False

    class Rewrite(ast.NodeTransformer):
        def _rewrite(self, node: ast.expr) -> ast.expr:
            nonlocal changed
            if not isinstance(node, ast.DictComp):
                return cast(ast.expr, self.generic_visit(node))
            if len(node.generators) != 2:
                return cast(ast.expr, self.generic_visit(node))
            first, second = node.generators
            rows = mt._mt_outcome_iteration_bindings(
                first.iter, first.target, resolver, outcome_columns
            )
            if (
                rows is None
                or len(rows) != len(outcome_columns)
                or first.is_async
                or first.ifs
                or second.is_async
                or second.ifs
                or not isinstance(second.iter, (ast.List, ast.Tuple))
                or len(second.iter.elts) != 1
                or not isinstance(second.target, (ast.List, ast.Tuple))
                or not isinstance(second.iter.elts[0], type(second.target))
            ):
                return cast(ast.expr, self.generic_visit(node))
            row = cast(ast.List | ast.Tuple, second.iter.elts[0])
            if (
                len(row.elts) != len(second.target.elts)
                or not row.elts
                or not all(isinstance(item, ast.Name) for item in second.target.elts)
            ):
                return cast(ast.expr, self.generic_visit(node))
            names = [cast(ast.Name, item).id for item in second.target.elts]
            if len(names) != len(set(names)):
                return cast(ast.expr, self.generic_visit(node))
            outcome_names = [
                name
                for name in rows[0]
                if {values[name] for values in rows} == set(outcome_columns)
            ]
            if len(outcome_names) != 1:
                return cast(ast.expr, self.generic_visit(node))
            outcome_name = outcome_names[0]
            values = [cast(ast.expr, item) for item in row.elts]
            if not all(_pure_projection(item, outcome_name) for item in values):
                return cast(ast.expr, self.generic_visit(node))
            bindings = dict(zip(names, values, strict=True))

            class Substitute(ast.NodeTransformer):
                def visit_Name(self, item: ast.Name) -> ast.AST:
                    if isinstance(item.ctx, ast.Load) and item.id in bindings:
                        return ast.copy_location(copy.deepcopy(bindings[item.id]), item)
                    return item

            substitute = Substitute()
            node.key = cast(ast.expr, substitute.visit(node.key))
            node.value = cast(ast.expr, substitute.visit(node.value))
            node.generators = [first]
            changed = True
            return cast(ast.expr, self.generic_visit(node))

        def visit_DictComp(self, node: ast.DictComp) -> ast.AST:
            return self._rewrite(node)

    rewritten = Rewrite().visit(copy.deepcopy(tree))
    if not changed:
        return content
    ast.fix_missing_locations(rewritten)
    return (ast.unparse(rewritten) + "\n").encode("utf-8")


def singleton_generator_analyzer(content: bytes, **kwargs: Any) -> mt.MultipleTestingDataflowResult:
    outcomes = tuple(cast(tuple[str, ...], kwargs["outcome_columns"]))
    rewritten = admit_singleton_projection_generator(content, outcomes)
    return mt.analyze_code_csv_multiple_testing_dataflow(rewritten, **kwargs)


PROTOTYPES: dict[str, Analyzer] = {
    "baseline-2.3": mt.analyze_code_csv_multiple_testing_dataflow,
    "D14-A-singleton-projection-generator": singleton_generator_analyzer,
}
