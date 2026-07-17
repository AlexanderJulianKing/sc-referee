"""Latent-stratum materialization (v0) — evidence only, no judgment.

Sits UPSTREAM of policy evaluation. It does not decide anything.

Why it exists
-------------
Five independent frontier-model runs on one donor-level cis-eQTL all missed the same defect: a
donor-level stratum recoverable only as an *aggregate of a quantity the analysis computes for
another purpose*. Measured on that task: reviewing the code alone surfaces it ~2% of the time;
merely printing the donor-level summary into the code lifts that to 46% (p<0.0001). Prompt wording
is worth <=9 points; adversarial framing is 0/24.

So the intervention is to *materialise the candidate*, not to reason harder about it. This module
computes the summaries. It renders no verdict, and it cannot: nothing here is a `ValidityPolicy`, a
`ProofRule`, or a routed `Finding`.

What it deliberately is NOT
--------------------------
* Not a `DischargeProvider`. Providers compute over already-bound typed facts and reject floats;
  they never load data. A data-bound scan is a different component.
* Not a rule on `confounding.v2`. That policy's `OmittedNuisancePresent` means an *established*
  nuisance. A screen-discovered association does not satisfy those semantics, and weakening them
  would silently alter the canonical policy identity.
* Not a detector. Whether a materialised quantity is a confounder or a mediator is causally
  undecidable from these data. This module never says.

Scope of v0: one pinned aggregation (unweighted arithmetic mean), a restricted expression grammar,
and loud abstention outside it. Every candidate that is eligible is emitted. There is no
significance filter — filtering would be a judgment.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

from sc_referee.inference.calibration import calibrate

MATERIALIZER_VERSION = "latent_stratum_materialization.v0"

# Mechanically determined. NO STATUS MEANS "clean", "pass", or "no issue" -- a scan that finds
# nothing is reporting on its own reach, not on the analysis.
STATUS_NO_IN_SCOPE_CONSTRUCT = "NO_IN_SCOPE_CONSTRUCT"   # discovered == 0
STATUS_ABSTAINED = "ABSTAINED"                           # discovered > 0, emitted == 0
STATUS_PARTIAL = "PARTIAL"                               # emitted > 0, abstentions > 0
STATUS_COMPLETE = "COMPLETE"                             # emitted > 0, abstentions == 0
STATUS_PRECONDITION_FAILED = "PRECONDITION_FAILED"       # binding/parsing could not begin


def _status(discovered: int, emitted: int, abstained: int) -> str:
    """Status of the whole scan, counted uniformly across every tier.

    Tier 1 (unread data columns) and tier 2 (derived quantities) both contribute to all three
    counts. A tier-1 column that abstained -- a multi-level nominal, where a Pearson correlation
    would measure row order -- counts as abstained exactly like a tier-2 candidate outside the
    grammar.

    Counting tiers uniformly matters: if status were computed from tier 2 alone, a scan that
    surfaced three unread columns would report NO_IN_SCOPE_CONSTRUCT, which is the silent-zero bug
    wearing a different hat.
    """
    if discovered == 0:
        return STATUS_NO_IN_SCOPE_CONSTRUCT
    if emitted == 0:
        return STATUS_ABSTAINED
    return STATUS_PARTIAL if abstained else STATUS_COMPLETE

# The only aggregation v0 will perform. Pinned so the protocol digest means something.
AGGREGATION = "unweighted_arithmetic_mean"

# The only association v0 reports. Descriptive; not a test, not a threshold, not a decision.
ASSOCIATION = "pearson_r_on_unit_summaries"

UNREAD_DISCLOSURE = (
    "Column {name} is present in {table} and is never read by this analysis. Its association with "
    "the declared exposure {exposure}, summarized at {unit} level, is reported below. This "
    "diagnostic does not establish that the column should have been used, nor that the analysis is "
    "incorrect."
)

DISCLOSURE = (
    "Derived quantity {name} was summarized at {unit} level ({aggregation}) and its association "
    "with the declared exposure {exposure} is reported below. This diagnostic does not establish "
    "confounding, mediation, or invalidity, and no verdict is implied by its presence here."
)


# --------------------------------------------------------------------------- records


@dataclass(frozen=True)
class Candidate:
    """A row-level derived quantity found in the source. Eligible or not; never judged."""

    name: str
    expression: str
    lineno: int
    eligible: bool
    ineligible_reason: str | None = None


@dataclass(frozen=True)
class UnreadColumn:
    """A column present in the bound data that the analysis never reads.

    Tier 1 of three. The analysis's own derived quantities are tier 2 (`Summary`); latent structure
    recoverable only as an aggregate of a tier-2 quantity is tier 3. Only tier 3 needs anything
    clever. This one is schema minus reads, and it is the cheapest evidence in the system.
    """

    name: str
    table: str
    unit: str
    aggregation: str
    n_units: int
    varies_within_unit: bool
    association: dict
    disclosure: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Summary:
    """One materialised candidate. Every field the witness-hygiene rule demands is recorded."""

    name: str
    expression: str
    lineno: int
    unit: str
    aggregation: str
    subset: str
    n_units: int
    n_rows: int
    n_missing: int
    n_clipped_low: int
    n_clipped_high: int
    values: dict          # unit key -> summary value
    association: dict     # method, statistic, n, null_sd  (descriptive only)
    disclosure: str


@dataclass(frozen=True)
class MaterializationRecord:
    """The whole output. Identity fields make the computation reproducible and auditable."""

    materializer_version: str
    materializer_digest: str
    data_digest: str
    binding_digest: str
    protocol_digest: str
    output_digest: str
    source_digest: str
    status: str
    scan_scope: tuple
    unit: str
    exposure: str
    subset: str
    candidates: tuple = ()
    summaries: tuple = ()
    abstentions: tuple = ()
    unread_columns: tuple = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True, default=str)


class Abstain(Exception):
    """Raised whenever v0 cannot proceed exactly. Never swallowed silently."""


# --------------------------------------------------------------------------- digests


def _digest(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _self_digest() -> str:
    return _file_digest(Path(__file__))


def _protocol_digest() -> str:
    return _digest("|".join((MATERIALIZER_VERSION, AGGREGATION, ASSOCIATION, _GRAMMAR_ID)))


_GRAMMAR_ID = "restricted-row-expr-v0"


# --------------------------------------------------------------------------- grammar
#
# v0 evaluates only this grammar. Anything else abstains loudly rather than guessing:
#   col      := FRAME.NAME | FRAME["NAME"]
#   scalar   := number | DICT["KEY"]   (DICT resolved from a recognised producer)
#   expr     := col | scalar | expr (+|-|*|/) expr | -expr
#             | np.clip(expr, scalar, scalar) | np.maximum(expr, scalar) | np.minimum(expr, scalar)


def _col_name(node, frames):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in frames:
        return node.attr
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in frames
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, str)
    ):
        return node.slice.value
    return None


def _eval(node, df, frames, env, stats):
    """Evaluate a restricted row-level expression against a dataframe. Abstain outside grammar."""
    col = _col_name(node, frames)
    if col is not None:
        if col not in df.columns:
            raise Abstain(f"column {col!r} not present in bound data")
        return df[col].astype(float)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    # scalar dict lookup, e.g. p_amb["HBB"]
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and isinstance(node.slice, ast.Constant)
    ):
        d = env.get(node.value.id)
        if isinstance(d, dict):
            key = node.slice.value
            if key not in d:
                raise Abstain(f"{node.value.id}[{key!r}] not resolvable")
            return float(d[key])
        raise Abstain(f"{node.value.id!r} is not a resolved scalar mapping")

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand, df, frames, env, stats)

    if isinstance(node, ast.BinOp):
        left = _eval(node.left, df, frames, env, stats)
        right = _eval(node.right, df, frames, env, stats)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise Abstain(f"binary operator {type(node.op).__name__} outside grammar")

    if isinstance(node, ast.Call):
        fn = _dotted(node.func)
        if fn in ("np.clip", "numpy.clip") and len(node.args) == 3:
            x = _eval(node.args[0], df, frames, env, stats)
            lo = _eval(node.args[1], df, frames, env, stats)
            hi = _eval(node.args[2], df, frames, env, stats)
            stats["n_clipped_low"] = int((x < lo).sum())
            stats["n_clipped_high"] = int((x > hi).sum())
            return x.clip(lower=lo, upper=hi)
        if fn in ("np.maximum", "numpy.maximum") and len(node.args) == 2:
            x = _eval(node.args[0], df, frames, env, stats)
            lo = _eval(node.args[1], df, frames, env, stats)
            stats["n_clipped_low"] = int((x < lo).sum())
            return x.clip(lower=lo)
        if fn in ("np.minimum", "numpy.minimum") and len(node.args) == 2:
            x = _eval(node.args[0], df, frames, env, stats)
            hi = _eval(node.args[1], df, frames, env, stats)
            stats["n_clipped_high"] = int((x > hi).sum())
            return x.clip(upper=hi)
        raise Abstain(f"call {fn!r} outside grammar")

    raise Abstain(f"{type(node).__name__} outside grammar")


def _dotted(node) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


# --------------------------------------------------------------------------- producers


def _resolve_str_lists(tree):
    """NAME = ["a", "b", ...] — the only name binding v0 resolves. Last write wins."""
    out = {}
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        if not isinstance(stmt.targets[0], ast.Name) or not isinstance(stmt.value, ast.List):
            continue
        items = [e.value for e in stmt.value.elts
                 if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if items and len(items) == len(stmt.value.elts):
            out[stmt.targets[0].id] = items
    return out


def _resolve_rate_dicts(tree, tables):
    """Recognise per-key rate dicts built from a frame.

    Exactly one pattern in v0:
        NAME = {k: FRAME[k].sum() / FRAME.COL.sum() for k in KEYS}

    where KEYS is a list literal or a name bound to one. This is the ambient-profile idiom (a
    per-key rate over a pooled reference table). Anything else is left unresolved, and expressions
    depending on it abstain.
    """
    env = {}
    str_lists = _resolve_str_lists(tree)
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        if not isinstance(stmt.targets[0], ast.Name) or not isinstance(stmt.value, ast.DictComp):
            continue
        dc = stmt.value
        gen = dc.generators[0]
        if not isinstance(gen.target, ast.Name):
            continue
        keyvar = gen.target.id

        if isinstance(gen.iter, ast.List):
            keys = [e.value for e in gen.iter.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        elif isinstance(gen.iter, ast.Name):
            keys = str_lists.get(gen.iter.id)
        else:
            keys = None
        if not keys or not isinstance(dc.value, ast.BinOp) or not isinstance(dc.value.op, ast.Div):
            continue

        num = _frame_key_sum(dc.value.left, keyvar)   # FRAME[k].sum()
        den = _frame_col_sum(dc.value.right)          # FRAME.COL.sum()
        if num is None or den is None or num != den[0] or num not in tables:
            continue
        df = tables[num]
        if den[1] not in df.columns:
            continue
        total = float(df[den[1]].sum())
        if total == 0:
            continue
        env[stmt.targets[0].id] = {
            k: float(df[k].sum()) / total for k in keys if k in df.columns
        }
    return env


def _frame_key_sum(node, keyvar):
    """Match `FRAME[keyvar].sum()` -> FRAME. The comprehension key must be the subscript."""
    if not (isinstance(node, ast.Call) and not node.args and isinstance(node.func, ast.Attribute)):
        return None
    if node.func.attr != "sum":
        return None
    sub = node.func.value
    if not (isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Name)):
        return None
    if not (isinstance(sub.slice, ast.Name) and sub.slice.id == keyvar):
        return None
    return sub.value.id


def _frame_col_sum(node):
    """Match `FRAME.COL.sum()` -> (FRAME, COL)."""
    if not (isinstance(node, ast.Call) and not node.args and isinstance(node.func, ast.Attribute)):
        return None
    if node.func.attr != "sum":
        return None
    col = node.func.value
    if not (isinstance(col, ast.Attribute) and isinstance(col.value, ast.Name)):
        return None
    return col.value.id, col.attr


def _find_read_columns(tree, frames):
    """Every column name the source reads off a bound frame, by any syntax it uses.

    Over-approximate on purpose: a name counted as read that is not simply drops a candidate from
    the report. Under-approximating would invent one.
    """
    read = set()
    for node in ast.walk(tree):
        nm = _col_name(node, frames)
        if nm is not None:
            read.add(nm)
            continue
        # FRAME[["a","b"]] and FRAME[LIST]
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) \
                and node.value.id in frames:
            sl = node.slice
            if isinstance(sl, ast.List):
                read.update(e.value for e in sl.elts
                            if isinstance(e, ast.Constant) and isinstance(e.value, str))
    # bare string literals anywhere are treated as potential column references
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            read.add(node.value)
    return read


def _find_authored_unit_aggregates(tree, frames, unit):
    """Aggregates the analysis itself already built at the declared unit.

    Matches `NAME = FRAME.groupby('<unit>').<anything>`. These are recognised structurally and
    recorded, never recomputed. Run A of the motivating benchmark computes exactly this
    (`rho_by_donor = allc.groupby('donor').apply(...)`), prints it, cross-tabs it against the
    exposure, and still reports a wrong answer -- so materialisation is neither necessary nor
    sufficient. Recording it keeps the record from falsely stating that nothing relevant existed.
    """
    out = []
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        if not isinstance(stmt.targets[0], ast.Name):
            continue
        for sub in ast.walk(stmt.value):
            if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)):
                continue
            if sub.func.attr != "groupby" or not isinstance(sub.func.value, ast.Name):
                continue
            if sub.func.value.id not in frames or not sub.args:
                continue
            key = sub.args[0]
            if isinstance(key, ast.Constant) and key.value == unit:
                out.append((stmt.targets[0].id, ast.unparse(stmt.value),
                            getattr(stmt, "lineno", 0)))
                break
    return out


def _find_candidates(tree, frames):
    """Every row-level derived assignment onto a bound frame. Eligibility is grammar-only."""
    out = []
    for stmt in ast.walk(tree):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        tgt = stmt.targets[0]
        name = _col_name(tgt, frames)
        if name is None:
            continue
        out.append((name, stmt.value, getattr(stmt, "lineno", 0)))
    return out


# --------------------------------------------------------------------------- association


def _pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


# --------------------------------------------------------------------------- entry


def materialize(source: str, tables: dict, unit: str, exposure: str,
                subset: str = "all rows", data_paths: tuple = ()) -> MaterializationRecord:
    """Summarise every eligible derived quantity at `unit` and report its association with `exposure`.

    `tables` maps the source's frame variable names to bound dataframes. Renders no judgment.
    """
    tree = ast.parse(source)
    frames = set(tables)
    env = _resolve_rate_dicts(tree, tables)

    # Multiple source names can be aliases for the same live frame.  Scan that artifact once and
    # retain every alias as provenance; a copied frame has a new identity and remains independently
    # auditable.
    frame_groups = []
    by_identity = {}
    for name, df in tables.items():
        identity = id(df)
        if identity not in by_identity:
            by_identity[identity] = len(frame_groups)
            frame_groups.append([df, [name]])
        else:
            frame_groups[by_identity[identity]][1].append(name)

    def _exposure_by_unit(df, table_name):
        if unit not in df.columns or exposure not in df.columns:
            raise Abstain(f"bound table {table_name!r} does not carry both {unit!r} and {exposure!r}")
        scoped = df.loc[df[unit].notna(), [unit, exposure]]
        grouped = scoped.groupby(unit, sort=True, observed=True, dropna=False)[exposure]
        bad = [key for key, values in grouped
               if values.isna().any() or values.nunique(dropna=False) != 1]
        if bad:
            preview = ", ".join(repr(item) for item in bad[:5])
            raise Abstain(
                f"exposure {exposure!r} is not constant and non-missing within declared unit "
                f"{unit!r} in table {table_name!r}; affected units: {preview}"
            )
        return grouped.first()

    def _numeric_values(raw):
        if raw.dtype != object:
            return raw.astype(float)
        levels = sorted(raw.dropna().unique(), key=lambda item: (type(item).__name__, repr(item)))
        return raw.map({value: index for index, value in enumerate(levels)}).astype(float)

    base = None
    for df, aliases in frame_groups:
        nm = aliases[0]
        if unit in df.columns and exposure in df.columns:
            base, base_name = df, nm
            break
    if base is None:
        raise Abstain(f"no bound table carries both unit {unit!r} and exposure {exposure!r}")
    base_exposure = _exposure_by_unit(base, base_name)

    # What the scan looked at, by construct class. Reported whether or not anything was found, so a
    # zero result describes the scan's reach rather than implying the analysis is clean.
    row_level = _find_candidates(tree, frames)
    authored = _find_authored_unit_aggregates(tree, frames, unit)
    # ---- tier 1: columns present in the data that the analysis never reads ----
    read = _find_read_columns(tree, frames)
    unread = []
    for df, alias_names in frame_groups:
        tname = alias_names[0]
        aliases = tuple(alias_names)
        if unit not in df.columns or exposure not in df.columns:
            continue
        table_exposure = _exposure_by_unit(df, tname)
        for col in df.columns:
            if col in read or col in (unit, exposure):
                continue
            raw = df[col]
            nominal_reason = None
            if raw.dtype == object:
                # A multi-level nominal column has no meaningful Pearson correlation. factorize()
                # assigns codes in order of appearance, so a "correlation" measures the file's row
                # order and nothing else. On the motivating benchmark this produced cell_id at
                # r=+0.947 (4.5 sd) -- an artifact outranking the real finding at 3.5 sd. Binary
                # is exempt: two levels factorize to a genuine 0/1 indicator.
                if raw.nunique() > 2:
                    nominal_reason = (
                        f"multi-level nominal ({raw.nunique()} levels); Pearson correlation on an "
                        "arbitrary integer encoding would measure row order, not association"
                    )
                    vals = None
                else:
                    vals = _numeric_values(raw)
            else:
                try:
                    vals = raw.astype(float)
                except Exception:
                    continue
            if unit not in df.columns or exposure not in df.columns:
                continue
            if nominal_reason is not None:
                unread.append(UnreadColumn(
                    name=col, table=tname, unit=unit, aggregation="not_applicable",
                    n_units=int(df[unit].nunique()), varies_within_unit=True,
                    association={"method": ASSOCIATION, "statistic": None,
                                 "n_units": int(df[unit].nunique()),
                                 "null_sd_under_no_association": None,
                                 "abstained": nominal_reason},
                    disclosure=UNREAD_DISCLOSURE.format(name=col, table=tname, unit=unit,
                                                        exposure=exposure),
                    aliases=aliases,
                ))
                continue
            grp = vals.groupby(df[unit])
            varies = bool((grp.nunique() > 1).any())
            per_unit = grp.mean() if varies else grp.first()
            expo = table_exposure.reindex(per_unit.index).astype(float)
            r = _pearson(list(per_unit.values), list(expo.values))
            n_u = int(len(per_unit))
            unread.append(UnreadColumn(
                name=col, table=tname, unit=unit,
                aggregation=AGGREGATION if varies else "constant_within_unit",
                n_units=n_u, varies_within_unit=varies,
                association={
                    "method": ASSOCIATION,
                    "statistic": None if r is None else round(r, 6),
                    "n_units": n_u,
                    "null_sd_under_no_association":
                        None if n_u < 4 else round(1 / math.sqrt(n_u - 1), 4),
                    "note": "Descriptive. Not a hypothesis test. No threshold is applied.",
                },
                disclosure=UNREAD_DISCLOSURE.format(name=col, table=tname, unit=unit,
                                                    exposure=exposure),
                aliases=aliases,
            ))


    scan_scope = (
        {"construct_class": "row_level_frame_assignment", "found": len(row_level),
         "in_scope": True},
        {"construct_class": "unread_data_column", "found": len(unread), "in_scope": True,
         "note": "Present in the bound data, never read by the analysis. Schema minus reads."},
        {"construct_class": "authored_unit_aggregate", "found": len(authored),
         "in_scope": False,
         "note": "Already summarised at the declared unit by the analysis itself; recorded, not "
                 "recomputed."},
    )

    candidates, summaries, abstentions = [], [], []

    # Collect the per-unit summary vectors and a live reference to each association dict, so the
    # whole candidate set can be calibrated jointly (§5.1): a lone null_sd prices one test, and a
    # candidate set needs a family-wise correction or it cries wolf.
    calib_vectors: dict = {}
    calib_targets: dict = {}
    canon = sorted(base[unit].dropna().unique(), key=lambda item: (type(item).__name__, repr(item)))
    exposure_by_unit = base_exposure.reindex(canon).astype(float)

    def _register(cid, per_unit_series, assoc):
        v = per_unit_series.reindex(canon)
        if v.notna().all() and v.nunique() > 1:
            calib_vectors[cid] = v.values
            calib_targets[cid] = assoc

    # tier-1 unread columns emitted above: register their vectors for joint calibration
    for u in unread:
        if u.association.get("statistic") is None:
            continue
        df = tables[u.table]
        col = u.name
        raw = df[col]
        if raw.dtype == object:
            raw = _numeric_values(raw)
        s = raw.astype(float).groupby(df[unit]).mean()
        _register(f"tier1:{u.table}:{col}", s, u.association)

    # Surface aggregates the analysis already built at the declared unit. v0 does not recompute
    # them; it records that they exist, so the scan never reports nothing where something does.
    for name, expr, lineno in authored:
        candidates.append(Candidate(name, expr, lineno, False, "AUTHORED_UNIT_AGGREGATE"))
        abstentions.append({
            "name": name, "lineno": lineno,
            "reason": "AUTHORED_UNIT_AGGREGATE: the analysis already summarises this at the "
                      "declared unit; v0 records its presence and does not recompute it.",
        })

    for name, value, lineno in row_level:
        expr = ast.unparse(value)
        stats = {"n_clipped_low": 0, "n_clipped_high": 0}
        try:
            series = _eval(value, base, frames, env, stats)
        except Abstain as exc:
            candidates.append(Candidate(name, expr, lineno, False, str(exc)))
            abstentions.append({"name": name, "lineno": lineno, "reason": str(exc)})
            continue
        if not hasattr(series, "groupby"):
            candidates.append(Candidate(name, expr, lineno, False, "not row-level"))
            abstentions.append({"name": name, "lineno": lineno, "reason": "not row-level"})
            continue

        candidates.append(Candidate(name, expr, lineno, True, None))
        n_missing = int(series.isna().sum())
        grouped = series.groupby(base[unit]).mean()
        expo = base_exposure.reindex(grouped.index)

        r = _pearson(list(grouped.values), list(expo.values.astype(float)))
        n_units = int(len(grouped))
        assoc = {
            "method": ASSOCIATION,
            "statistic": None if r is None else round(r, 6),
            "n_units": n_units,
            # Reported so the reader can price chance. At n=24 this is ~0.21.
            "null_sd_under_no_association": None if n_units < 4 else round(1 / math.sqrt(n_units - 1), 4),
            "note": "Descriptive. Not a hypothesis test. No threshold is applied.",
        }
        summaries.append(Summary(
            name=name, expression=expr, lineno=lineno, unit=unit,
            aggregation=AGGREGATION, subset=subset,
            n_units=n_units, n_rows=int(len(series)), n_missing=n_missing,
            n_clipped_low=stats["n_clipped_low"], n_clipped_high=stats["n_clipped_high"],
            values={str(k): round(float(v), 6) for k, v in grouped.items()},
            association=assoc,
            disclosure=DISCLOSURE.format(name=name, unit=unit, aggregation=AGGREGATION,
                                         exposure=exposure),
        ))
        _register(f"tier2:{name}", grouped, assoc)

    # Joint permutation calibration over the whole candidate set (§5.1). Mutates each association
    # dict in place (frozen records hold a reference to the same dict), so the calibration is in the
    # record and its digest below.
    if calib_vectors:
        cal = calibrate(calib_vectors, exposure_by_unit.values)
        for cid, assoc in calib_targets.items():
            assoc["calibration"] = cal[cid].as_dict()

    data_digest = _digest("|".join(sorted(_file_digest(Path(p)) for p in data_paths))) \
        if data_paths else _digest("unbound")
    binding_digest = _digest(json.dumps({"unit": unit, "exposure": exposure, "subset": subset,
                                         "frames": sorted(frames)}, sort_keys=True))
    unread_emitted = sum(1 for u in unread if u.association.get("statistic") is not None)
    unread_abstained = len(unread) - unread_emitted
    status = _status(
        discovered=len(candidates) + len(unread),
        emitted=len(summaries) + unread_emitted,
        abstained=len(abstentions) + unread_abstained,
    )
    # Digest the whole result. Digesting summaries alone let two materially different empty scans
    # collide, which is exactly the case where the record has to be trustworthy.
    body = json.dumps({
        "status": status,
        "scan_scope": list(scan_scope),
        "candidates": [asdict(c) for c in candidates],
        "summaries": [asdict(s) for s in summaries],
        "abstentions": list(abstentions),
        "unread_columns": [asdict(u) for u in unread],
    }, sort_keys=True, default=str)
    return MaterializationRecord(
        materializer_version=MATERIALIZER_VERSION,
        materializer_digest=_self_digest(),
        data_digest=data_digest,
        binding_digest=binding_digest,
        protocol_digest=_protocol_digest(),
        output_digest=_digest(body),
        source_digest=_digest(source),
        status=status,
        scan_scope=tuple(scan_scope),
        unit=unit, exposure=exposure, subset=subset,
        candidates=tuple(candidates), summaries=tuple(summaries),
        abstentions=tuple(abstentions), unread_columns=tuple(unread),
    )


# --------------------------------------------------------------------------- dual population


@dataclass(frozen=True)
class DualScan:
    """Leg 1 on both the pre-gate and post-gate population, with the delta (§5.2).

    The analyst's model fits a subset (a gate). The gate can itself be a defect -- if it conditions
    on something correlated with the outcome, it induces associations that are not in the full data.
    Scanning only the fitted population would faithfully diagnose a population a broken gate created.
    So this reports both, and the per-candidate delta. A large delta is a signal about the GATE, not
    the candidate, and is surfaced as such rather than folded into the candidate's score.
    """

    pre_gate: MaterializationRecord
    post_gate: MaterializationRecord
    deltas: tuple
    gate_note: str

    def to_json(self) -> str:
        return json.dumps({
            "pre_gate": json.loads(self.pre_gate.to_json()),
            "post_gate": json.loads(self.post_gate.to_json()),
            "deltas": list(self.deltas),
            "gate_note": self.gate_note,
        }, indent=2, sort_keys=True)


def _assoc_by_name(rec: MaterializationRecord) -> dict:
    out = {}
    for u in rec.unread_columns:
        out[f"tier1:{u.name}"] = u.association
    for s in rec.summaries:
        out[f"tier2:{s.name}"] = s.association
    return out


def dual_materialize(source: str, tables: dict, unit: str, exposure: str,
                     fitted_mask, *, data_paths: tuple = ()) -> DualScan:
    """Run leg 1 on the full data and on the fitted subset; report both and the delta.

    `fitted_mask` is a boolean Series aligned to the base table's index -- the analyst's own
    subsetting (e.g. `c.activated == 1`). The caller supplies it; identifying it automatically from
    the code is the must-slicer's job, not this module's.
    """
    pre = materialize(source, tables, unit, exposure, subset="all rows (pre-gate)",
                      data_paths=data_paths)

    masked = {}
    base_name = None
    for nm, df in tables.items():
        if unit in df.columns and exposure in df.columns and base_name is None:
            base_name = nm
    for nm, df in tables.items():
        if nm == base_name:
            masked[nm] = df[fitted_mask.reindex(df.index).fillna(False).astype(bool)]
        else:
            masked[nm] = df
    post = materialize(source, masked, unit, exposure, subset="fitted population (post-gate)",
                       data_paths=data_paths)

    pre_a, post_a = _assoc_by_name(pre), _assoc_by_name(post)
    deltas = []
    for cid in sorted(set(pre_a) | set(post_a)):
        rp = pre_a.get(cid, {}).get("calibration", {}).get("statistic")
        rq = post_a.get(cid, {}).get("calibration", {}).get("statistic")
        if rp is None and rq is None:
            continue
        d = None if (rp is None or rq is None) else round(rq - rp, 6)
        deltas.append({
            "candidate": cid, "pre_gate_r": rp, "post_gate_r": rq, "delta": d,
            "note": "A large delta is evidence about the gate/selection, not the candidate. "
                    "The gate conditions the fitted population; a candidate whose association "
                    "appears only after gating may be induced by the gate."
                    if d is not None and abs(d) >= (1 / math.sqrt(max(post.summaries[0].n_units, 2) - 1)
                                                    if post.summaries else 1.0)
                    else "",
        })

    return DualScan(
        pre_gate=pre, post_gate=post, deltas=tuple(deltas),
        gate_note="Legs 2a and 2b describe the post-gate (fitted) population. Their output is "
                  "conditional on this gate. Pre-gate associations are reported so a gate-induced "
                  "association is visible as a large pre/post delta rather than absorbed silently.",
    )
