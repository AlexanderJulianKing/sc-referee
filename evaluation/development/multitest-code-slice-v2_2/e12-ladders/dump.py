"""Dump the expanded scope the _MtEngine sees, by intercepting _MtEngine.__init__."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 as M  # noqa: E402

CAPTURED: dict[str, object] = {}
_orig = M._MtEngine.__init__


def _patched(self, **kw):
    CAPTURED.update(kw)
    CAPTURED["engine"] = self
    return _orig(self, **kw)


M._MtEngine.__init__ = _patched


def dump(case_dir=None, spec=None, source=None):
    CAPTURED.clear()
    if spec is not None:
        r = h.analyze_corpus(spec, source)
    else:
        r = h.analyze_envelope(case_dir, source)
    return r, CAPTURED


def unparse_scope():
    scope = CAPTURED.get("scope")
    if scope is None:
        return "<engine not reached>"
    return "\n".join(ast.unparse(s) for s in scope)
