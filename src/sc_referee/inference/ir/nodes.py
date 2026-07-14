from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Mapping

from sc_referee.inference.frontend.common import SourceUnit


@dataclass(frozen=True, order=True)
class SourceSpan:
    source_index: int
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int

    @classmethod
    def from_ast(cls, source_index: int, node: ast.AST):
        return cls(source_index, getattr(node, "lineno", 0), getattr(node, "col_offset", 0),
                   getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                   getattr(node, "end_col_offset", getattr(node, "col_offset", 0)))


@dataclass(frozen=True)
class Barrier:
    id: str
    kind: str
    reason: str
    span: SourceSpan
    ast_kind: str | None = None


@dataclass(frozen=True)
class IRInstruction:
    id: str
    op: str
    span: SourceSpan
    result: str | None = None
    target: str | None = None
    operands: tuple[str, ...] = ()
    memory_version: str | None = None
    callsite_id: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ValueDefinition:
    id: str
    variable: str
    span: SourceSpan
    dependencies: tuple[str, ...] = ()
    instruction_id: str | None = None


@dataclass(frozen=True)
class MemoryVersion:
    id: str
    location: str
    field: str
    span: SourceSpan
    previous: tuple[str, ...]
    strong_update: bool


@dataclass(frozen=True)
class IRCall:
    callsite_id: str
    source_index: int
    symbol: str
    symbol_cased: str
    module_hint: str | None
    span: SourceSpan


@dataclass(frozen=True)
class BasicBlock:
    id: str
    instructions: tuple[IRInstruction, ...]
    successors: tuple[str, ...] = ()
    exceptional_successors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ControlFlowGraph:
    blocks: Mapping[str, BasicBlock]
    entries: tuple[str, ...]
    exits: tuple[str, ...]


@dataclass(frozen=True)
class ProgramIR:
    sources: tuple[SourceUnit, ...]
    cfg: ControlFlowGraph
    value_definitions: Mapping[str, ValueDefinition]
    memory_versions: Mapping[str, MemoryVersion]
    barriers: tuple[Barrier, ...]
    calls: tuple[IRCall, ...]

