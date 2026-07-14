"""Evaluation-order lowering to a small CFG with value and field-sensitive memory SSA."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

from sc_referee.inference.ids import stable_id
from sc_referee.inference.ir.nodes import (
    Barrier,
    BasicBlock,
    ControlFlowGraph,
    IRCall,
    IRInstruction,
    MemoryVersion,
    ProgramIR,
    SourceSpan,
    ValueDefinition,
)
from sc_referee.source_ast import iter_call_sites


_DYNAMIC_EXECUTION = frozenset({"eval", "exec", "compile"})
_REFLECTION = frozenset({"getattr", "setattr", "__getattribute__", "__setattr__"})
_UNSUPPORTED_NODES = (
    ast.AsyncFunctionDef, ast.Await, ast.ClassDef, ast.Lambda, ast.Yield, ast.YieldFrom,
)


@dataclass
class _MutableBlock:
    id: str
    instructions: list[IRInstruction] = field(default_factory=list)
    successors: list[str] = field(default_factory=list)
    exceptional: list[str] = field(default_factory=list)


class _Lowerer:
    def __init__(self, sources):
        self.sources = sources
        self.blocks: dict[str, _MutableBlock] = {}
        self.values: dict[str, ValueDefinition] = {}
        self.memory: dict[str, MemoryVersion] = {}
        self.barriers: list[Barrier] = []
        self.entries: list[str] = []
        self.exits: list[str] = []
        self._block_no: dict[int, int] = {}
        self._instruction_no: dict[int, int] = {}
        self._value_no: dict[tuple[int, str], int] = {}
        self._memory_no: dict[tuple[int, str, str], int] = {}
        self._barrier_no: dict[int, int] = {}
        self._exception_block: dict[int, str] = {}

    def new_block(self, source_index: int, label: str) -> str:
        ordinal = self._block_no.get(source_index, 0)
        self._block_no[source_index] = ordinal + 1
        block_id = f"block:{source_index}:{ordinal}:{label}"
        self.blocks[block_id] = _MutableBlock(block_id)
        return block_id

    def instruction(self, block_id: str, source_index: int, node: ast.AST, op: str, **kwargs):
        span = SourceSpan.from_ast(source_index, node)
        ordinal = self._instruction_no.get(source_index, 0)
        self._instruction_no[source_index] = ordinal + 1
        instruction = IRInstruction(
            id=stable_id("ins", source_index, span.lineno, span.col_offset,
                         span.end_lineno, span.end_col_offset, ordinal),
            op=op, span=span, **kwargs)
        self.blocks[block_id].instructions.append(instruction)
        return instruction

    def barrier(self, source_index: int, node: ast.AST | None, kind: str, reason: str,
                ast_kind: str | None = None):
        span = (SourceSpan.from_ast(source_index, node) if node is not None
                else SourceSpan(source_index, 0, 0, 0, 0))
        ordinal = self._barrier_no.get(source_index, 0)
        self._barrier_no[source_index] = ordinal + 1
        barrier = Barrier(
            stable_id("barrier", source_index, span.lineno, span.col_offset,
                      span.end_lineno, span.end_col_offset, ordinal),
            kind, reason, span, ast_kind or (type(node).__name__ if node is not None else None))
        self.barriers.append(barrier)
        return barrier

    def value_id(self, source_index: int, variable: str, span: SourceSpan) -> str:
        key = (source_index, variable)
        ordinal = self._value_no.get(key, 0)
        self._value_no[key] = ordinal + 1
        return stable_id(f"value:{variable}", source_index, span.lineno, span.col_offset,
                         span.end_lineno, span.end_col_offset, ordinal)

    def define(self, block_id: str, source_index: int, node: ast.AST, variable: str,
               dependencies: tuple[str, ...], env: dict[str, str], op="assign") -> str:
        span = SourceSpan.from_ast(source_index, node)
        value_id = self.value_id(source_index, variable, span)
        instruction = self.instruction(block_id, source_index, node, op, result=value_id,
                                       target=variable, operands=dependencies)
        self.values[value_id] = ValueDefinition(value_id, variable, span, dependencies, instruction.id)
        env[variable] = value_id
        return value_id

    def dependencies(self, node: ast.AST | None, env: dict[str, str]) -> tuple[str, ...]:
        if node is None:
            return ()
        out = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id in env:
                if env[child.id] not in out:
                    out.append(env[child.id])
        return tuple(out)

    def _target_leaves(self, target):
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                yield from self._target_leaves(element)
        else:
            yield target

    def _memory_target(self, target):
        if isinstance(target, ast.Subscript):
            field = target.slice.value if (isinstance(target.slice, ast.Constant)
                                           and isinstance(target.slice.value, (str, int))) else "<unknown-field>"
            return self._location(target.value), str(field)
        if isinstance(target, ast.Attribute):
            return self._location(target.value), target.attr
        return None

    def _location(self, node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._location(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            field = node.slice.value if isinstance(node.slice, ast.Constant) else "<unknown-field>"
            return f"{self._location(node.value)}[{field!r}]"
        return "<unknown-heap>"

    def memory_write(self, block_id: str, source_index: int, target, definite: bool = True):
        spec = self._memory_target(target)
        if spec is None:
            return
        location, field = spec
        key = (source_index, location, field)
        ordinal = self._memory_no.get(key, 0)
        self._memory_no[key] = ordinal + 1
        span = SourceSpan.from_ast(source_index, target)
        previous = tuple(version.id for version in self.memory.values()
                         if version.location == location and (version.field == field
                                                              or field == "<unknown-field>"))
        strong = definite and field != "<unknown-field>" and location != "<unknown-heap>"
        version_id = stable_id(f"memory:{location}:{field}", source_index, span.lineno,
                               span.col_offset, span.end_lineno, span.end_col_offset, ordinal)
        self.memory[version_id] = MemoryVersion(version_id, location, field, span, previous, strong)
        self.instruction(block_id, source_index, target, "memory_write", memory_version=version_id,
                         details={"strong_update": strong, "field": field, "location": location})

    def scan_expression(self, block_id: str, source_index: int, node: ast.AST | None):
        if node is None:
            return
        for child in ast.walk(node):
            if isinstance(child, _UNSUPPORTED_NODES):
                self.barrier(source_index, child, "unsupported_syntax",
                             f"{type(child).__name__} is outside the supported frontend")
            if isinstance(child, ast.Call):
                symbol = child.func.id if isinstance(child.func, ast.Name) else (
                    child.func.attr if isinstance(child.func, ast.Attribute) else "")
                if symbol in _DYNAMIC_EXECUTION:
                    self.barrier(source_index, child, "dynamic_execution",
                                 f"{symbol} cannot be analyzed without executing code")
                elif symbol in _REFLECTION:
                    self.barrier(source_index, child, "reflection",
                                 f"{symbol} prevents exact static dispatch")
                self.instruction(block_id, source_index, child, "call")
                exceptional = self._exception_block[source_index]
                if exceptional not in self.blocks[block_id].exceptional:
                    self.blocks[block_id].exceptional.append(exceptional)

    def lower_statements(self, statements, block_id: str, source_index: int,
                         env: dict[str, str], *, definite=True):
        current = block_id
        for statement in statements:
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                value = statement.value
                self.scan_expression(current, source_index, value)
                dependencies = self.dependencies(value, env)
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                for target in targets:
                    for leaf in self._target_leaves(target):
                        if isinstance(leaf, ast.Name):
                            self.define(current, source_index, leaf, leaf.id, dependencies, env)
                        else:
                            self.memory_write(current, source_index, leaf, definite)
            elif isinstance(statement, ast.AugAssign):
                self.scan_expression(current, source_index, statement.value)
                dependencies = self.dependencies(statement, env)
                if isinstance(statement.target, ast.Name):
                    self.define(current, source_index, statement.target, statement.target.id,
                                dependencies, env, op="aug_assign")
                else:
                    self.memory_write(current, source_index, statement.target, False)
            elif isinstance(statement, ast.Expr):
                self.scan_expression(current, source_index, statement.value)
                self.instruction(current, source_index, statement, "expr",
                                 operands=self.dependencies(statement.value, env))
            elif isinstance(statement, ast.If):
                self.scan_expression(current, source_index, statement.test)
                self.instruction(current, source_index, statement.test, "branch",
                                 operands=self.dependencies(statement.test, env))
                then_block = self.new_block(source_index, "if_then")
                else_block = self.new_block(source_index, "if_else")
                merge_block = self.new_block(source_index, "if_merge")
                self.blocks[current].successors.extend([then_block, else_block])
                then_env, else_env = dict(env), dict(env)
                then_end = self.lower_statements(statement.body, then_block, source_index,
                                                 then_env, definite=False)
                else_end = self.lower_statements(statement.orelse, else_block, source_index,
                                                 else_env, definite=False)
                self.blocks[then_end].successors.append(merge_block)
                self.blocks[else_end].successors.append(merge_block)
                for variable in sorted(set(then_env) | set(else_env)):
                    incoming = tuple(dict.fromkeys(value for value in
                                     (then_env.get(variable), else_env.get(variable)) if value is not None))
                    if len(incoming) == 1:
                        env[variable] = incoming[0]
                    elif len(incoming) > 1:
                        self.define(merge_block, source_index, statement, variable,
                                    incoming, env, op="phi")
                current = merge_block
            elif isinstance(statement, (ast.While, ast.For)):
                header = self.new_block(source_index, "loop_header")
                body = self.new_block(source_index, "loop_body")
                exit_block = self.new_block(source_index, "loop_exit")
                self.blocks[current].successors.append(header)
                test = statement.test if isinstance(statement, ast.While) else statement.iter
                self.scan_expression(header, source_index, test)
                self.instruction(header, source_index, statement, "loop",
                                 operands=self.dependencies(test, env))
                self.blocks[header].successors.extend([body, exit_block])
                body_env = dict(env)
                body_end = self.lower_statements(statement.body, body, source_index,
                                                 body_env, definite=False)
                self.blocks[body_end].successors.append(header)
                for variable in sorted(set(env) | set(body_env)):
                    incoming = tuple(dict.fromkeys(value for value in
                                     (env.get(variable), body_env.get(variable)) if value is not None))
                    if len(incoming) > 1:
                        self.define(header, source_index, statement, variable, incoming, env, op="phi")
                current = exit_block
            elif isinstance(statement, (ast.Import, ast.ImportFrom, ast.Pass)):
                self.instruction(current, source_index, statement, "import" if not isinstance(statement, ast.Pass)
                                 else "pass")
            elif isinstance(statement, ast.Return):
                self.scan_expression(current, source_index, statement.value)
                self.instruction(current, source_index, statement, "return",
                                 operands=self.dependencies(statement.value, env))
            else:
                self.barrier(source_index, statement, "unsupported_syntax",
                             f"{type(statement).__name__} is outside the supported frontend")
                self.instruction(current, source_index, statement, "barrier")
        return current

    def run(self):
        for unit in self.sources:
            source_index = unit.source_index
            entry = self.new_block(source_index, "entry")
            exception = self.new_block(source_index, "exception")
            self._exception_block[source_index] = exception
            self.entries.append(entry)
            if unit.language != "python":
                self.barrier(source_index, None, "unsupported_language",
                             f"{unit.language} is outside the coverage-complete frontend")
                end = entry
            elif unit.parsed.tree is None:
                self.barrier(source_index, None, "parse_error", unit.parsed.parse_error or "parse failed")
                end = entry
            else:
                end = self.lower_statements(unit.parsed.tree.body, entry, source_index, {})
            exit_block = self.new_block(source_index, "exit")
            self.blocks[end].successors.append(exit_block)
            self.blocks[exception].successors.append(exit_block)
            self.exits.append(exit_block)

        calls = []
        for site in iter_call_sites([unit.parsed for unit in self.sources]):
            calls.append(IRCall(site.id, site.source_index, site.symbol, site.symbol_cased,
                                site.module_hint, SourceSpan.from_ast(site.source_index, site.call)))
        frozen_blocks = {block_id: BasicBlock(block.id, tuple(block.instructions),
                                              tuple(dict.fromkeys(block.successors)),
                                              tuple(dict.fromkeys(block.exceptional)))
                         for block_id, block in self.blocks.items()}
        return ProgramIR(
            tuple(self.sources), ControlFlowGraph(frozen_blocks, tuple(self.entries), tuple(self.exits)),
            dict(self.values), dict(self.memory), tuple(self.barriers), tuple(calls))


def lower(frontend_results) -> ProgramIR:
    sources = tuple(getattr(result, "unit", result) for result in frontend_results)
    return _Lowerer(sources).run()
