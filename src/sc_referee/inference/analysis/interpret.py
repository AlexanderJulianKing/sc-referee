from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Mapping

from sc_referee.inference.analysis.memory import AbstractHeap, opaque_call
from sc_referee.inference.domains.effects import EffectValue
from sc_referee.inference.domains.origin import OriginAtom, unknown_origin
from sc_referee.inference.domains.value import AbsValue
from sc_referee.source_ast import callsite_id, ordered_statements


@dataclass(frozen=True)
class AbstractState:
    env: Mapping[str, AbsValue]
    heap: AbstractHeap = field(compare=False)
    effects: tuple[EffectValue, ...] = ()


def _location(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_location(node.value)}.{node.attr}"
    return "<unknown-heap>"


def _field(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
        return str(node.value)
    return None


def interpret(program):
    """A deliberately may-only forward pass. It consumes AST objects but never executes them."""
    states = {}
    for unit in program.sources:
        heap = AbstractHeap()
        env: dict[str, AbsValue] = {}
        effects: list[EffectValue] = []

        def value(node):
            if isinstance(node, ast.Constant):
                return AbsValue(literals=frozenset({node.value}),
                                origins=frozenset({OriginAtom("literal", f"{unit.source_index}:{node.lineno}")}))
            if isinstance(node, ast.Name):
                if node.id not in env:
                    location = heap.allocate(f"global:{unit.source_index}:{node.id}")
                    env[node.id] = AbsValue(points_to=frozenset({location}),
                                            origins=frozenset({unknown_origin(f"name:{node.id}")}),
                                            unknown=True)
                return env[node.id]
            if isinstance(node, ast.Attribute):
                base = value(node.value)
                return heap.read(base.points_to, node.attr).join(base)
            if isinstance(node, ast.Subscript):
                base = value(node.value)
                return heap.read(base.points_to, _field(node.slice)).join(base)
            if isinstance(node, ast.Call):
                args = tuple(value(argument) for argument in node.args)
                args += tuple(value(keyword.value) for keyword in node.keywords)
                returned, effect = opaque_call(callsite_id(unit.source_index, node), args, heap)
                effects.append(effect)
                return returned
            children = [value(child) for child in ast.iter_child_nodes(node)
                        if isinstance(child, ast.expr)]
            if not children:
                return AbsValue(unknown=True)
            result = children[0]
            for child in children[1:]:
                result = result.join(child)
            return result

        if unit.parsed.tree is not None:
            for statement in ordered_statements(unit.parsed.tree.body):
                if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    rhs = value(statement.value)
                    targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                    for target in targets:
                        leaves = target.elts if isinstance(target, (ast.Tuple, ast.List)) else [target]
                        for leaf in leaves:
                            if isinstance(leaf, ast.Name):
                                env[leaf.id] = rhs
                            elif isinstance(leaf, ast.Subscript):
                                base = value(leaf.value)
                                heap.write(base.points_to, _field(leaf.slice), rhs,
                                           definition=f"def:{unit.source_index}:{leaf.lineno}", definite=True)
                            elif isinstance(leaf, ast.Attribute):
                                base = value(leaf.value)
                                heap.write(base.points_to, leaf.attr, rhs,
                                           definition=f"def:{unit.source_index}:{leaf.lineno}", definite=True)
                elif isinstance(statement, ast.Expr):
                    value(statement.value)
        state = AbstractState(dict(env), heap, tuple(effects))
        states[f"source:{unit.source_index}:exit"] = state
    return states
