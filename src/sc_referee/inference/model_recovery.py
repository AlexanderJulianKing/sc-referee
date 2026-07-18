"""Reconstruct a ModelSpec from analyst code.

This is the plumbing that turns the diagnostic from "give me a ModelSpec and I compute the legs" into
"give me the analyst's code and I recover the ModelSpec myself". Until this exists, a human hand-sets
the response / offset / reference / target for every run -- exactly the labour the tool is meant to
remove.

It is a RECOGNISER, not a general parser. It matches a bounded set of fit patterns and abstains
loudly on everything else (returning `recognised=False` with reasons). Sound-over-complete: when it
fires it is right; when it is unsure it says so and the human sets the spec by hand.

Recognised patterns:

1. Hand-rolled negative-binomial / Poisson NLL minimised with scipy (a common shape when a log
   link cannot express additive contamination, so the likelihood is hand-rolled). Mean form:
   mu = [reference +] offset * exp(linear_predictor). EXACT replay.

2. statsmodels formula GLM:  smf.glm("y ~ a + b", family=..., offset=...). EXACT-ish replay.

3. A general count GLM read from the design formula wherever one appears -- an R glm/DESeq2/edgeR
   (`design = ~ g`, `glm.nb(y ~ g)`, `model.matrix(~ g)`), a pydeseq2 `design_factors=` /
   `contrast=`, or a statsmodels array GLM. R source is read by regex (it does not parse as Python).
   These are marked `proxy=True`: the exact size-factor + dispersion fit is NOT reproduced in Python,
   so the replay is only an approximation. Legs 2a/2b run on a proxy ONLY when a reported effect is
   available to gate the replay's faithfulness (replay must reproduce it, else abstain). Leg 1, which
   needs no fit, runs regardless.

Output is code-level: response/offset/reference/predictors are the VARIABLE OR COLUMN NAMES the code
uses. Binding those to data (resolving `amb` back to `rho*tu*p_amb[...]`) is a separate step; this
module recovers the STRUCTURE, which is the hard part and the part a human should not have to redo.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecoveredModel:
    recognised: bool
    pattern: str | None = None          # "handrolled_nll" | "statsmodels_formula"
    family: str | None = None           # "nb" | "poisson"
    response: str | None = None
    offset: str | None = None
    additive_reference: str | None = None
    predictors: tuple = ()
    target_term: str | None = None      # the predictor matching the declared exposure
    fit_symbol: str | None = None       # the variable the fit result is bound to
    proxy: bool = False                 # True when the Python replay only APPROXIMATES the analyst's fit
    reasons: tuple = ()                 # why it abstained, or notes when it recognised

    def to_model_spec(self):
        """Build a replay.ModelSpec from the recovered structure. Raises if not recognised."""
        from sc_referee.inference.replay import ModelSpec
        if not self.recognised:
            raise ValueError(f"cannot build a ModelSpec: {'; '.join(self.reasons)}")
        return ModelSpec(
            response=self.response, predictors=tuple(self.predictors),
            target_term=self.target_term, family=self.family,
            exposure_offset=self.offset, additive_reference=self.additive_reference,
        )

    def as_dict(self) -> dict:
        return {
            "recognised": self.recognised, "pattern": self.pattern, "family": self.family,
            "response": self.response, "offset": self.offset,
            "additive_reference": self.additive_reference, "predictors": list(self.predictors),
            "target_term": self.target_term, "fit_symbol": self.fit_symbol, "proxy": self.proxy,
            "reasons": list(self.reasons),
        }


def _abstain(*reasons) -> RecoveredModel:
    return RecoveredModel(recognised=False, reasons=tuple(reasons))


def _bare(expr: str) -> str:
    """Strip a frame qualifier to a bindable column name: `df.logN` / `df["logN"]` -> `logN`."""
    expr = expr.strip()
    if expr.endswith("]") and "[" in expr:
        inner = expr[expr.index("[") + 1:-1].strip().strip("'\"")
        return inner or expr
    if "." in expr:
        return expr.rsplit(".", 1)[-1]
    return expr


def _dotted(node) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _calls_np_exp(node) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and _dotted(sub.func).split(".")[-1] == "exp":
            return True
    return False


def _find_exp_call(node):
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and _dotted(sub.func).split(".")[-1] == "exp" and sub.args:
            return sub
    return None


# --------------------------------------------------------------------------- hand-rolled NLL


_SAFETY = ("clip", "maximum", "minimum")


def _is_self_safety(name, value) -> bool:
    """`mu = np.clip(mu, ...)` -- a numerical-safety re-binding of `name` to itself. A passthrough."""
    if not (isinstance(value, ast.Call) and _dotted(value.func).split(".")[-1] in _SAFETY):
        return False
    return bool(value.args) and isinstance(value.args[0], ast.Name) and value.args[0].id == name


def _unclip(node):
    """Strip an outer clip/maximum/minimum wrapper: np.clip(X, lo, hi) -> X."""
    while (isinstance(node, ast.Call) and _dotted(node.func).split(".")[-1] in _SAFETY
           and node.args):
        node = node.args[0]
    return node


def _resolve_local(name, func_body, seen=None):
    """The effective last definition of a local name, seeing through self-referential clips.

    `mu = amb + mu_e` then `mu = np.clip(mu, 1e-9, None)` resolves to `amb + mu_e`, not the clip.
    """
    seen = seen or set()
    expr = None
    for stmt in func_body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == name:
            if _is_self_safety(name, stmt.value):
                continue                          # passthrough; keep the prior real definition
            expr = stmt.value
    return _unclip(expr) if expr is not None else None


def _substitute(expr, func_body, depth=0):
    """Inline local intermediate names (mu_e -> its definition), bounded."""
    if depth > 8 or expr is None:
        return expr

    class _Inline(ast.NodeTransformer):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                d = _resolve_local(node.id, func_body)
                if d is not None and not (isinstance(d, ast.Name) and d.id == node.id):
                    return _substitute(d, func_body, depth + 1)
            return node

    return ast.fix_missing_locations(_Inline().visit(ast.parse(ast.unparse(expr), mode="eval").body))


def _param_names(func):
    """Names bound from the params vector: `alpha, beta = params[0], params[1]` and `t = exp(params[2])`."""
    params = set()
    pvar = func.args.args[0].arg if func.args.args else None
    for stmt in ast.walk(func):
        if not isinstance(stmt, ast.Assign):
            continue
        # tuple unpack: alpha, beta = params[0], params[1]
        if isinstance(stmt.targets[0], ast.Tuple):
            for t in stmt.targets[0].elts:
                if isinstance(t, ast.Name):
                    params.add(t.id)
            continue
        # single: theta = np.exp(params[2])  or  al = params[0]
        if isinstance(stmt.targets[0], ast.Name):
            for sub in ast.walk(stmt.value):
                if isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Name) \
                        and sub.value.id == pvar:
                    params.add(stmt.targets[0].id)
    return params


def _linear_predictor_terms(lp, params):
    """Parse `alpha + beta*g (+ ...)` -> the non-param variables. Abstain-signalling on anything else."""
    terms, ok = [], True
    stack = [lp]
    additive = []
    while stack:
        node = stack.pop()
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            stack.append(node.left); stack.append(node.right)
        else:
            additive.append(node)
    for term in additive:
        if isinstance(term, ast.Name):
            if term.id in params:
                continue                      # lone param = intercept
            terms.append(term.id)             # a bare variable term
        elif isinstance(term, ast.BinOp) and isinstance(term.op, ast.Mult):
            names = [n.id for n in (term.left, term.right) if isinstance(n, ast.Name)]
            pnames = [n for n in names if n in params]
            vnames = [n for n in names if n not in params]
            if len(pnames) == 1 and len(vnames) == 1:
                terms.append(vnames[0])       # param * variable
            elif len(pnames) == 1 and not vnames:
                continue                       # param * constant -> intercept-like
            else:
                ok = False
        elif isinstance(term, ast.UnaryOp):
            stack_inner = term.operand
            if isinstance(stack_inner, ast.Name) and stack_inner.id not in params:
                terms.append(stack_inner.id)
        else:
            ok = False
    return terms, ok


def _recover_handrolled(tree, exposure) -> RecoveredModel | None:
    fits = [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _dotted(n.func).split(".")[-1] == "minimize" and n.args]
    if not fits:
        return None
    funcs = {f.name: f for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)}

    for fit in fits:
        target = fit.args[0]
        fname = target.id if isinstance(target, ast.Name) else None
        func = funcs.get(fname)
        if func is None:
            continue
        params = _param_names(func)

        mu_expr = _resolve_local("mu", func.body)
        if mu_expr is None:
            continue
        mu = _substitute(mu_expr, func.body)

        # decompose  [reference +] offset*exp(lp)
        reference, endo = None, mu
        if isinstance(mu, ast.BinOp) and isinstance(mu.op, ast.Add):
            l_exp, r_exp = _calls_np_exp(mu.left), _calls_np_exp(mu.right)
            if l_exp and not r_exp:
                endo, reference = mu.left, mu.right
            elif r_exp and not l_exp:
                endo, reference = mu.right, mu.left
            else:
                continue
        exp_call = _find_exp_call(endo)
        if exp_call is None:
            continue
        lp = exp_call.args[0]

        # offset = the factor multiplying exp(...)
        offset = None
        if isinstance(endo, ast.BinOp) and isinstance(endo.op, ast.Mult):
            for side in (endo.left, endo.right):
                if not _calls_np_exp(side):
                    offset = ast.unparse(side)

        preds, ok = _linear_predictor_terms(lp, params)
        if not ok or not preds:
            continue

        # family from the return loglik: gammaln with a dispersion parameter -> nb; poisson form
        # otherwise. NB is identified STRUCTURALLY -- a fitted parameter that is not part of the
        # linear predictor is the dispersion -- not by the parameter's name (Poisson has no such
        # extra parameter). This does not assume the analyst named their coefficients any particular way.
        family = None
        src = ast.unparse(func)
        if "gammaln" in src and any(p not in preds for p in params):
            family = "nb"
        elif "np.log(mu)" in src or "log(mu) -" in src:
            family = "poisson"
        if family is None:
            continue

        # response: the count variable in the loglik (heuristic: a bare name multiplied by log(mu)/appearing in gammaln(y+...))
        response = _response_var(func, params)
        if response is None:
            continue

        reference_name = ast.unparse(reference) if reference is not None else None
        target = exposure if exposure in preds else None
        reasons = (f"hand-rolled {family} NLL minimised via `{fname}`; "
                   f"mean = {reference_name + ' + ' if reference_name else ''}"
                   f"{offset + '*' if offset else ''}exp({ast.unparse(lp)})",)
        if target is None:
            reasons = reasons + (f"declared exposure {exposure!r} not among predictors {preds}; "
                                 "target_term unresolved",)
        return RecoveredModel(
            recognised=target is not None, pattern="handrolled_nll", family=family,
            response=response, offset=offset, additive_reference=reference_name,
            predictors=tuple(preds), target_term=target,
            fit_symbol=_fit_symbol(tree, fit), reasons=reasons,
        )
    return None


def _response_var(func, params):
    """The count response in the loglik: appears as `y*np.log(mu)` or `gammaln(y+theta)`."""
    for ret in [n for n in ast.walk(func) if isinstance(n, ast.Return)]:
        for sub in ast.walk(ret):
            # gammaln(y + ...) -> y
            if isinstance(sub, ast.Call) and _dotted(sub.func).split(".")[-1] == "gammaln" and sub.args:
                a = sub.args[0]
                if isinstance(a, ast.BinOp) and isinstance(a.op, ast.Add):
                    for side in (a.left, a.right):
                        if isinstance(side, ast.Name) and side.id not in params and side.id != "mu":
                            return side.id
            # y * np.log(mu)
            if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Mult):
                names = [n.id for n in (sub.left, sub.right) if isinstance(n, ast.Name)]
                if any("log" in _dotted(s.func) for s in ast.walk(sub)
                       if isinstance(s, ast.Call)):
                    for n in names:
                        if n not in params and n != "mu":
                            return n
    return None


def _fit_symbol(tree, fit_call):
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Assign) and stmt.value is fit_call \
                and isinstance(stmt.targets[0], ast.Name):
            return stmt.targets[0].id
    return None


# --------------------------------------------------------------------------- statsmodels formula


def _recover_statsmodels(tree, exposure) -> RecoveredModel | None:
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _dotted(node.func).split(".")[-1] in ("glm", "GLM")):
            continue
        formula = None
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) and "~" in a.value:
                formula = a.value
        family, offset = None, None
        for kw in node.keywords:
            if kw.arg == "family":
                fam = _dotted(kw.value.func) if isinstance(kw.value, ast.Call) else _dotted(kw.value)
                fam = fam.split(".")[-1].lower()
                family = "nb" if "negativebinomial" in fam or fam == "nb" else \
                         "poisson" if "poisson" in fam else None
            if kw.arg == "offset":
                offset = ast.unparse(kw.value)
        if formula is None or family is None:
            continue
        lhs, rhs = formula.split("~", 1)
        response = lhs.strip()
        offset = _bare(offset) if offset else None       # df.logN -> logN, a bindable column name
        preds = [t.strip() for t in rhs.replace("+", " ").split() if t.strip() not in ("1", "0")]
        if exposure not in preds:
            return RecoveredModel(
                recognised=False, pattern="statsmodels_formula", family=family, response=response,
                predictors=tuple(preds),
                reasons=(f"declared exposure {exposure!r} not in formula predictors {preds}",))
        return RecoveredModel(
            recognised=True, pattern="statsmodels_formula", family=family, response=response,
            offset=offset, additive_reference=None, predictors=tuple(preds), target_term=exposure,
            reasons=(f"statsmodels {family} GLM, formula {formula.strip()!r}",))
    return None


# --------------------------------------------------------------------------- general count-GLM
#
# A large fraction of real DE/eQTL work fits a count GLM through one of a handful of APIs. They vary
# wildly in syntax but encode the same structure: an NB or Poisson GLM of an outcome on an exposure,
# usually with a size/library offset. This recogniser extracts (family, predictors, offset) from a
# design formula wherever one appears -- an R `glm(y ~ g, ...)`, a DESeq2 `design = ~ g`, an edgeR
# `model.matrix(~ g)`, a pydeseq2 `design_factors="g"` / `contrast=["g", ...]`, or a statsmodels
# array GLM. The response is named from the declared `outcome` (the target gene) when the fit works
# on a count matrix rather than a single vector.
#
# Soundness for the proxy cases (DESeq2/edgeR/pydeseq2, whose exact size-factor + dispersion fit is
# not reproduced here): recognition only names the structure. Whether the Python NB replay is a
# faithful proxy is decided downstream by the faithfulness gate (`replay(..., reported_effect=...)`),
# which abstains if the replay does not reproduce the reported number.

_COUNT_GLM_CALLS = ("glm", "GLM", "DESeq", "DESeqDataSetFromMatrix", "glmQLFit", "glmFit",
                    "DeseqDataSet", "DeseqStats", "estimateDisp")
_R_FAMILY_NB = ("negativebinomial", "negative.binomial", "nbinom", "nb", "deseq", "edger",
                "glm.nb", "glmqlfit", "glmfit", "estimatedisp")
_R_FAMILY_POIS = ("poisson", "quasipoisson")


def _formula_terms(s: str):
    """`y ~ a + b*c` or `~ a + b` -> (response|None, [predictor terms]). Interactions kept whole."""
    if "~" not in s:
        return None, None
    lhs, rhs = s.split("~", 1)
    response = lhs.strip() or None
    terms = [t.strip() for t in rhs.replace("+", " ").split()
             if t.strip() and t.strip() not in ("1", "0", ".")]
    return response, terms


def _classify_family(text: str):
    low = text.lower()
    if any(tok in low for tok in _R_FAMILY_NB):
        return "nb"
    if any(tok in low for tok in _R_FAMILY_POIS):
        return "poisson"
    return None


def _find_formula_string(tree):
    """Any string literal or design= kwarg carrying a `~` formula, plus pydeseq2 design_factors."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "~" in node.value:
            return node.value, "formula_string"
        if isinstance(node, ast.keyword) and node.arg in ("design", "formula") \
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value, "design_kwarg"
    # pydeseq2 design_factors="g" / contrast=["g", ...]
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "design_factors":
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return "~ " + node.value.value, "design_factors"
        if isinstance(node, ast.keyword) and node.arg == "contrast" and isinstance(node.value, ast.List) \
                and node.value.elts and isinstance(node.value.elts[0], ast.Constant):
            return "~ " + str(node.value.elts[0].value), "contrast"
    return None, None


def _recover_count_glm(tree, exposure, outcome) -> RecoveredModel | None:
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and _dotted(n.func).split(".")[-1] in _COUNT_GLM_CALLS]
    if not calls:
        return None
    src = ast.unparse(tree)
    formula, formula_src = _find_formula_string(tree)
    if formula is None:
        return _abstain("a count-GLM fit call was found but no design formula could be extracted")
    response, preds = _formula_terms(formula)
    if not preds:
        return _abstain(f"design formula {formula!r} has no usable predictors")
    if exposure not in preds:
        return RecoveredModel(
            recognised=False, pattern="count_glm", predictors=tuple(preds),
            reasons=(f"declared exposure {exposure!r} not in design predictors {preds}",))

    family = _classify_family(src) or "nb"       # count GLMs default to NB when unstated (DESeq/edgeR)
    # offset from an offset= kwarg, if any
    offset = None
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "offset":
            offset = _bare(ast.unparse(node.value))
    response = response or outcome                # count-matrix fits name the response via the outcome
    if response is None:
        return RecoveredModel(
            recognised=False, pattern="count_glm", family=family, predictors=tuple(preds),
            target_term=exposure,
            reasons=("recognised a count GLM but the response is unnamed (a count matrix) and no "
                     "outcome/target feature was declared to name it",))
    return RecoveredModel(
        recognised=True, pattern="count_glm", family=family, response=response,
        offset=offset, additive_reference=None, predictors=tuple(preds), target_term=exposure,
        proxy=True,
        reasons=(f"count GLM ({family}); design {formula.strip()!r}; response {response!r}; "
                 f"a size-factor/library offset is not reproduced here -- the faithfulness gate "
                 f"decides whether the Python replay is a faithful proxy.",))


# --------------------------------------------------------------------------- text (R + Python)
#
# R source (DESeq2, edgeR, limma, base glm) does not parse as Python, and its exact fit is not
# reproduced in Python anyway. So R -- and any count-GLM whose AST form we did not match -- is read
# from raw text by regex: extract the design formula, the family, and the fit call. The response is
# named from the declared outcome. Replay of these is a Python NB proxy, faithfulness-gated.

import re as _re

_FORMULA_RE = _re.compile(r"(?:([\w.]+)\s*)?~\s*([\w.\s+*:()-]+?)(?=[,)\n]|$)")
_FIT_TOKENS = ("deseq", "glmqlfit", "glmfit", "glm(", "glm.nb", "model.matrix", "deseqdataset",
               "deseqstats", "estimatedisp", "edger", "smf.glm", "sm.glm",
               "voom", "lmfit", "ebayes", "toptable")
_LIMMA_TOKENS = ("voom", "lmfit", "ebayes", "toptable")


def _recover_count_glm_text(source: str, exposure: str, outcome) -> RecoveredModel | None:
    low = source.lower()
    if not any(tok in low for tok in _FIT_TOKENS):
        return None
    # the formula whose RHS actually contains the exposure (skip unrelated `~` uses)
    chosen = None
    for m in _FORMULA_RE.finditer(source):
        resp = (m.group(1) or "").strip() or None
        rhs = m.group(2).strip()
        preds = [t.strip() for t in rhs.replace("+", " ").split()
                 if t.strip() and t.strip() not in ("1", "0", ".")]
        if exposure in preds:
            chosen = (resp, preds)
            break
    if chosen is None:
        return _abstain("a count-GLM fit was found in the source text but no design formula "
                        f"containing the declared exposure {exposure!r} could be extracted")
    resp, preds = chosen
    low_all = source.lower()
    is_limma = any(tok in low_all for tok in _LIMMA_TOKENS)
    family = "limma_voom" if is_limma else (_classify_family(source) or "nb")
    # offset: capture a balanced call or bare name. A log(X) offset is on the link scale; the replay
    # uses a MULTIPLICATIVE offset (exp scale), so unwrap log(X) -> X.
    off = _re.search(r"offset\s*=\s*(log\s*\(\s*[\w.]+\s*\)|[\w.]+\s*\([^)]*\)|[\w.]+)", source)
    offset = None
    if off:
        raw = off.group(1).strip()
        m = _re.fullmatch(r"log\s*\(\s*([\w.]+)\s*\)", raw)
        offset = _bare(m.group(1)) if m else (_bare(raw) if "(" not in raw else None)
    response = resp or outcome
    if response is None:
        return RecoveredModel(
            recognised=False, pattern="count_glm_text", family=family, predictors=tuple(preds),
            target_term=exposure,
            reasons=("recognised a count GLM in the source text but the response is unnamed and no "
                     "outcome/target feature was declared to name it",))
    label = ("limma-voom (weighted linear model on log2-CPM)" if family == "limma_voom"
             else f"count GLM ({family})")
    return RecoveredModel(
        recognised=True,
        pattern=("limma_voom" if family == "limma_voom" else "count_glm_text"),
        family=family, response=response,
        offset=offset, additive_reference=None, predictors=tuple(preds), target_term=exposure,
        proxy=True,
        reasons=(f"{label} read from source text; design ~ {' + '.join(preds)}; "
                 f"response {response!r}; a size-factor/library offset is not reproduced here -- the "
                 f"faithfulness gate decides whether the Python replay is a faithful proxy.",))


# --------------------------------------------------------------------------- entry


def recover(source: str, exposure: str, outcome: str | None = None) -> RecoveredModel:
    """Recover a ModelSpec structure from analyst code. Abstains loudly on anything unrecognised.

    `outcome` (the declared target feature) names the response for count-matrix fits (DESeq2 etc.)
    whose formula has no left-hand side.
    """
    parsed = None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        parsed = None                            # R or other non-Python source -> text path only

    if parsed is not None:
        for recogniser in (_recover_handrolled, _recover_statsmodels):
            out = recogniser(parsed, exposure)
            if out is not None:
                return out
        out = _recover_count_glm(parsed, exposure, outcome)
        if out is not None and out.recognised:
            return out

    text = _recover_count_glm_text(source, exposure, outcome)
    if text is not None:
        return text
    return _abstain("no recognised fit pattern (hand-rolled NB/Poisson NLL, statsmodels GLM, or a "
                    "count-GLM fit: R glm/DESeq2/edgeR, pydeseq2)")
