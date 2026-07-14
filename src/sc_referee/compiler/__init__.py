"""Opt-in, deterministic compiler surface.

Nothing in this package is imported by the ordinary audit path.  Compilation starts only when a
caller explicitly invokes :func:`resolve_for_compile` (or the ``sc-referee compile`` command).
"""

from sc_referee.compiler.resolve import CompileNeeded, NoCompileNeeded, resolve_for_compile
from sc_referee.compiler.pipeline import CompileAuditResult, run_compile_audit

__all__ = [
    "CompileAuditResult", "CompileNeeded", "NoCompileNeeded", "resolve_for_compile",
    "run_compile_audit",
]
