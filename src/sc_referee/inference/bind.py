"""Bind a recovered ModelSpec's variables to data by evaluating the analyst's own definitions.

model_recovery gives code-level names (`amb`, `Nfree`, `y`, `g`). This resolves each back through the
analyst's assignments and evaluates it against the bound data, so the caller does not hand-build
`{"amb": ..., "Nfree": ...}`. It reuses the materialization grammar (columns, arithmetic, clip,
rate-dict lookups) and adds what a real fit chain needs:

* module-scope assignments        `amb = rho*tu*p_amb["CXCL10"]`
* derived columns                 `c["rho"] = np.clip(c.HBB/(c.total_umi*p_amb["HBB"]), 0, 1)`
* a fitted-population subset       `act = c[c.activated==1]`  -> the caller's `fitted_mask`
* `.values` / `.astype(...)` / `.copy()` / `.reset_index(...)` accessor noise

The subset mask (`c.activated==1`) is usually opaque -- a GMM label, not grammar. The caller already
supplies `fitted_mask` for the dual-population scan, and it IS that subset, so the binder trusts it
rather than re-deriving it. Anything outside this bounded evaluator raises Abstain: sound over
complete, exactly like the materializer.
"""
from __future__ import annotations

import ast

import numpy as np
import pandas as pd

from sc_referee.inference.materialization import Abstain, _resolve_rate_dicts

_STRIP_ATTRS = ("values", "copy", "to_numpy", "flatten", "ravel")
_STRIP_CALLS = ("astype", "copy", "reset_index", "to_numpy", "flatten", "ravel", "values")


def _dotted(node) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


class _Binder:
    def __init__(self, tree, tables, fitted_mask):
        self.tables = tables
        self.frames = set(tables)
        self.mask = None if fitted_mask is None else np.asarray(fitted_mask, dtype=bool)
        self.rate_dicts = _resolve_rate_dicts(tree, tables)
        self.module_defs: dict = {}         # name -> expr (last module-scope assignment)
        self.derived_cols: dict = {}        # (frame, col) -> expr
        self.subsets: dict = {}             # subset name -> base frame name (masked by fitted_mask)
        self._resolving: set = set()
        for stmt in ast.walk(tree):
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            tgt = stmt.targets[0]
            if isinstance(tgt, ast.Name):
                # sub = FRAME[<mask>]  (a fitted-population subset)
                base = self._subset_base(stmt.value)
                if base is not None:
                    self.subsets[tgt.id] = base
                else:
                    self.module_defs[tgt.id] = stmt.value
            elif (isinstance(tgt, ast.Subscript) and isinstance(tgt.value, ast.Name)
                  and isinstance(tgt.slice, ast.Constant) and isinstance(tgt.slice.value, str)):
                self.derived_cols[(tgt.value.id, tgt.slice.value)] = stmt.value

    def _subset_base(self, value):
        """`FRAME[<boolean>]` possibly chained with .copy()/.reset_index() -> FRAME name, else None."""
        node = self._strip_accessors(value)
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and node.value.id in self.frames
                and not (isinstance(node.slice, ast.Constant))):
            return node.value.id
        return None

    def _strip_accessors(self, node):
        """Peel .values / .astype(...) / .copy() / .reset_index(...) noise off the front."""
        while True:
            if isinstance(node, ast.Attribute) and node.attr in _STRIP_ATTRS:
                node = node.value
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr in _STRIP_CALLS):
                node = node.func.value
            else:
                return node

    # ------------------------------------------------------------------ evaluation

    def eval_name(self, name):
        if name in self._resolving:
            raise Abstain(f"cyclic definition of {name!r}")
        if name not in self.module_defs:
            raise Abstain(f"{name!r} is not a module-scope assignment")
        self._resolving.add(name)
        try:
            return self._eval(self.module_defs[name])
        finally:
            self._resolving.discard(name)

    def _column(self, frame, col):
        """A column of a frame -- real, or a derived column evaluated on that frame, then masked
        if the frame is a fitted-population subset."""
        masked = frame in self.subsets
        base = self.subsets.get(frame, frame)
        if base in self.tables and col in self.tables[base].columns:
            series = self.tables[base][col]
        elif (base, col) in self.derived_cols:
            series = pd.Series(self._eval(self.derived_cols[(base, col)], on=base),
                               index=self.tables[base].index)
        else:
            raise Abstain(f"column {col!r} of {base!r} is neither bound nor a derived column")
        vals = np.asarray(series, dtype=float)
        if masked:
            if self.mask is None:
                raise Abstain(f"{frame!r} is a fitted subset but no fitted_mask was supplied")
            if len(self.mask) != len(vals):
                raise Abstain("fitted_mask length does not match the base frame")
            vals = vals[self.mask]
        return vals

    def _eval(self, node, on=None):
        node = self._strip_accessors(node)

        # FRAME.col  or  FRAME["col"]  (or a subset frame)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in self.frames or node.value.id in self.subsets:
                return self._column(node.value.id, node.attr)
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and (node.value.id in self.frames or node.value.id in self.subsets)
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str)):
            return self._column(node.value.id, node.slice.value)

        if isinstance(node, ast.Name):
            if on is not None and node.id in self.tables.get(on, pd.DataFrame()).columns:
                return self._column(on, node.id)
            return self.eval_name(node.id)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        # scalar rate-dict lookup: p_amb["CXCL10"]
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and isinstance(node.slice, ast.Constant)):
            d = self.rate_dicts.get(node.value.id)
            if isinstance(d, dict):
                key = node.slice.value
                if key not in d:
                    raise Abstain(f"{node.value.id}[{key!r}] not resolvable")
                return float(d[key])
            raise Abstain(f"{node.value.id!r} is not a resolved mapping")

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._eval(node.operand, on)

        if isinstance(node, ast.BinOp):
            l, r = self._eval(node.left, on), self._eval(node.right, on)
            if isinstance(node.op, ast.Add):
                return l + r
            if isinstance(node.op, ast.Sub):
                return l - r
            if isinstance(node.op, ast.Mult):
                return l * r
            if isinstance(node.op, ast.Div):
                return l / r
            raise Abstain(f"operator {type(node.op).__name__} outside the binder grammar")

        if isinstance(node, ast.Call):
            fn = _dotted(node.func).split(".")[-1]
            if fn == "clip" and len(node.args) == 3:
                x = self._eval(node.args[0], on)
                lo, hi = node.args[1], node.args[2]
                lo = None if _is_none(lo) else self._eval(lo, on)
                hi = None if _is_none(hi) else self._eval(hi, on)
                return np.clip(x, lo, hi)
            if fn in ("maximum",) and len(node.args) == 2:
                return np.maximum(self._eval(node.args[0], on), self._eval(node.args[1], on))
            if fn in ("minimum",) and len(node.args) == 2:
                return np.minimum(self._eval(node.args[0], on), self._eval(node.args[1], on))
            raise Abstain(f"call {fn!r} outside the binder grammar")

        raise Abstain(f"{type(node).__name__} outside the binder grammar")


def _is_none(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def bind_fit_data(source: str, names, tables: dict, fitted_mask=None) -> dict:
    """Resolve and evaluate each name in `names` against the bound data. Abstains loudly.

    `names` are the code-level variables a recovered ModelSpec references (response, offset,
    additive_reference, predictors). Returns {name: 1-D float array}, all aligned to the fitted
    population when a `fitted_mask` is given.
    """
    tree = ast.parse(source)
    binder = _Binder(tree, tables, fitted_mask)
    out = {}
    for name in names:
        if name in tables:                       # a bare frame is not a fittable vector
            raise Abstain(f"{name!r} is a frame, not a model variable")
        # a direct column of a bound/subset frame, referenced by bare name, is not resolvable here;
        # ModelSpec names are module-scope variables or resolvable columns via their definitions.
        out[name] = np.asarray(binder.eval_name(name), dtype=float) \
            if name in binder.module_defs else _bind_bare_column(binder, name)
    return out


def _bind_bare_column(binder: _Binder, name):
    """A ModelSpec name that is itself a subset-column extraction, e.g. `y = act.CXCL10.values`."""
    raise Abstain(f"{name!r} is not a module-scope assignment and not directly bindable")
