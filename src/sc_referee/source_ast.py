"""The ONE shared front-end: normalize sources (notebook JSON, magics), parse to AST, and enumerate
call sites with stable ids.

Two layers sit on top of this: `provenance.py` (flow-sensitive taint over grouping columns) and
`sink_use.py` (bind calls to typed sink contracts). If each parsed and walked the code its own way they
could disagree about what code exists or which calls are present — a marker call provenance tainted
might get no `SinkUse`, or vice versa. So both consume THIS module: the same notebook/magic
normalization and the same call-site id scheme (`source_index:lineno:col`). A `MarkerTest` and the
`SinkUse` for the same call carry the same `callsite_id`, which is how the selection-inference check
later joins a naive p-value to its grouping's taint origin. (adversarial design consult, Q1.)

Parsing is AST-only — code is never executed.
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass

_MAGIC_RE = re.compile(r"^\s*[%!].*$", re.M)   # notebook magics / shell escapes — strip before parsing


def strip_magics(code: str) -> str:
    return _MAGIC_RE.sub("", code)


def to_python(src: str) -> str:
    """A `.ipynb` step arrives as JSON — extract its code cells so downstream sees real Python. A
    non-notebook string is returned unchanged. (A marker test hidden in a notebook must never vanish.)"""
    s = src.lstrip()
    if not s.startswith("{"):
        return src
    try:
        nb = json.loads(src)
    except (ValueError, TypeError):
        return src
    if not (isinstance(nb, dict) and isinstance(nb.get("cells"), list)):
        return src
    cells = []
    for c in nb["cells"]:
        if isinstance(c, dict) and c.get("cell_type") == "code":
            body = c.get("source", "")
            if isinstance(body, list):
                # tolerate a malformed cell (non-string entries) at the parser boundary — never crash
                cells.append("".join(x for x in body if isinstance(x, str)))
            elif isinstance(body, str):
                cells.append(body)
    return "\n".join(cells)


def ordered_statements(body):
    """Yield statements in SOURCE order, descending into compound-statement bodies — taint must
    propagate forward through assignments, which `ast.walk` (breadth-first) would not preserve."""
    for stmt in body:
        yield stmt
        for fld in ("body", "orelse", "finalbody"):
            inner = getattr(stmt, fld, None)
            if isinstance(inner, list):
                yield from ordered_statements(inner)
        for handler in getattr(stmt, "handlers", []):
            yield from ordered_statements(handler.body)


def func_name(call: ast.Call) -> str:
    """The called symbol, lowercased: last attr of a dotted chain, or a bare Name."""
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr.lower()
    if isinstance(f, ast.Name):
        return f.id.lower()
    return ""


def const_str(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _dotted_prefix(call: ast.Call):
    """The attribute path written before the symbol as `(root_name, [middle_attrs...])`, or None when
    the call's receiver is not a plain dotted name (a bare `Name` call, or a call on an expression like
    `x.first().second()`). For `sc.tl.rank_genes_groups(...)` -> ("sc", ["tl"])."""
    f = call.func
    if isinstance(f, ast.Name):
        return None                      # bare name call — no dotted prefix
    if not isinstance(f, ast.Attribute):
        return None
    mids = []
    node = f.value
    while isinstance(node, ast.Attribute):
        mids.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None                      # receiver is an expression (e.g. a call result), not a name
    return node.id, list(reversed(mids))


def _module_hint(call: ast.Call):
    """The dotted prefix as a string (`sc.tl` for `sc.tl.rank_genes_groups`), or None. Kept for
    display; callee IDENTITY is resolved import-aware via `resolve_callee`, not from this raw text."""
    pref = _dotted_prefix(call)
    if pref is None:
        return None
    root, mids = pref
    return ".".join([root, *mids]) or None


def callsite_id(source_index: int, node: ast.AST) -> str:
    """The stable join key for a call. Includes the FULL span, not just the start: in a chained call
    `x.a().b()` the outer and inner Call share (lineno, col_offset), so start-only ids collide and a
    taint origin could join to the wrong call (adversarial review #4). Both this module and provenance build
    ids through THIS function so the two never diverge."""
    return (f"{source_index}:{node.lineno}:{node.col_offset}:"
            f"{getattr(node, 'end_lineno', node.lineno)}:{getattr(node, 'end_col_offset', node.col_offset)}")


@dataclass
class ParsedSource:
    source_index: int
    tree: ast.Module | None
    parse_error: str | None = None


def terminal_symbol(call: ast.Call) -> str:
    """The called symbol in its ORIGINAL case (`DeseqDataSet`, not `deseqdataset`). Case matters for
    contract identity — Python is case-sensitive, so `DESEQDATASET` is not `DeseqDataSet` (adversarial review #7)."""
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


@dataclass
class CallSite:
    id: str                              # "<source_index>:<lineno>:<col_offset>:..." — stable join key
    source_index: int
    lineno: int
    col_offset: int
    symbol: str                          # lowercased called symbol (for provenance / candidate matching)
    symbol_cased: str                    # ORIGINAL-case symbol (for exact contract identity)
    module_hint: str | None              # dotted prefix as written, or None
    call: ast.Call                       # the node itself, for argument binding


def parse_sources(sources) -> list:
    """Normalize + parse each source. A step that will not parse is kept as a `ParsedSource` with a
    `parse_error` (never dropped — a caller decides whether an unanalyzable step is a silent clean)."""
    out = []
    for i, src in enumerate(sources):
        code = strip_magics(to_python(src))
        try:
            out.append(ParsedSource(i, ast.parse(code)))
        except SyntaxError as e:
            out.append(ParsedSource(i, None, parse_error=str(e)))
    return out


def iter_call_sites(parsed) -> list:
    """Every `ast.Call` in every parsed source, each exactly once, with a stable full-span id, in
    (source_index, document) order — `ast.walk` is breadth-first, so we sort by start position to make
    the documented order true (adversarial review #7)."""
    sites = []
    for ps in parsed:
        if ps.tree is None:
            continue
        calls = [n for n in ast.walk(ps.tree) if isinstance(n, ast.Call)]
        calls.sort(key=lambda n: (n.lineno, n.col_offset, n.end_lineno or 0, n.end_col_offset or 0))
        for node in calls:
            sites.append(CallSite(
                id=callsite_id(ps.source_index, node),
                source_index=ps.source_index, lineno=node.lineno, col_offset=node.col_offset,
                symbol=func_name(node), symbol_cased=terminal_symbol(node),
                module_hint=_module_hint(node), call=node))
    return sites


@dataclass
class ImportBinding:
    local: str                           # the name bound in this program
    module: str                          # canonical module it refers to
    symbol: str | None = None            # the imported symbol, or None for a module import


@dataclass
class SourceEnv:
    """Per-source name environment (imports/shadows are per source, NOT unioned across the bundle — a
    notebook's cells are already flattened into one source, while separate scripts have independent
    namespaces; unioning would let one file's `import ... as stats` bind another file's custom `stats`,
    adversarial re-review blocker #1)."""
    imports: dict                        # local name -> ImportBinding, THIS source only (unambiguous)
    bound: set                           # names bound by a NON-import construct or MULTIPLY imported
    patched: set                         # dotted attr-assignment paths on an imported root (monkey-patch)
    patched_attrs: set                   # attr NAMES ever written on any object (conservative sink havoc)
    alias_symbols: dict                  # local name -> {original imported symbols}, incl. relative/ambiguous


def _attr_path(node):
    """The dotted path of an Attribute/Name chain (`sc.tl.x` -> 'sc.tl.x'), or None when the base is not
    a plain Name."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def _expr_root(node):
    """The root Name id of an Attribute/Name expression (`sc.tl` -> 'sc'), else None."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _arg_names(a: ast.arguments) -> set:
    names = {x.arg for x in (a.posonlyargs + a.args + a.kwonlyargs)}
    if a.vararg:
        names.add(a.vararg.arg)
    if a.kwarg:
        names.add(a.kwarg.arg)
    return names


def _collect_bound(tree) -> set:
    """Every name bound by a NON-import construct. The GENERAL rule — any `Name` in a Store context —
    covers assignment / for / with-as / walrus / comprehension / aug targets uniformly (no per-statement
    enumeration to fall behind). Plus def/class/lambda names & params, match captures, and
    global/nonlocal declarations. A name both imported and bound here is AMBIGUOUS -> not resolved to a
    library sink (sound over complete; adversarial re-review #2/#3)."""
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
            names |= _arg_names(node.args)
        elif isinstance(node, ast.Lambda):
            names |= _arg_names(node.args)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.update(node.names)
        elif isinstance(node, ast.MatchAs) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
    return names


def _is_namespace_expr(node) -> bool:
    """A `__dict__` attribute, or a `globals()`/`vars(...)`/`locals()` call — a namespace whose string
    subscript writes rebind by name."""
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return True
    return isinstance(node, ast.Call) and terminal_symbol(node) in ("globals", "vars", "locals")


_MUTATOR_FUNCS = frozenset({"setattr", "__setattr__", "object", "update", "setdefault"})


def _mutation_targets(call, import_locals) -> set:
    """Names a namespace/import mutation CALL could rebind. Only fires for a recognized mutator whose
    target is an imported object or a namespace: `setattr(mod,"n",v)`, `patch.object(mod,attribute="n")`,
    `globals().update(n=v)`, `mod.__dict__.update({"n": v})`. Collects positional string args, keyword
    NAMES, keyword string VALUES, and dict-literal keys — closing the keyword/receiver/`.update()` forms
    the positional rule alone misses (adversarial re-review round 4-5). Gated so it does not fire on ordinary
    keyword calls."""
    fn = terminal_symbol(call)
    recv = call.func.value if isinstance(call.func, ast.Attribute) else None
    fires = (
        (fn in ("setattr", "__setattr__") and call.args and _expr_root(call.args[0]) in import_locals)
        or fn == "object"                                    # patch.object / mock.patch.object
        or (fn in ("update", "setdefault") and recv is not None
            and (_is_namespace_expr(recv) or _expr_root(recv) in import_locals))
    )
    if not fires:
        return set()
    names: set = set()
    for a in call.args:
        s = const_str(a)
        if s is not None:
            names.add(s)
        if isinstance(a, ast.Dict):
            names.update(k for k in (const_str(x) for x in a.keys) if k is not None)
    for kw in call.keywords:
        if kw.arg is not None:
            names.add(kw.arg)
        s = const_str(kw.value)
        if s is not None:
            names.add(s)
    return names


def _collect_patched(tree, import_locals):
    """(patched_paths, patched_attrs, ambiguous_locals). Enumerating patch SYNTAX is unbounded, so use
    GENERAL rules that collapse the class (adversarial re-review #4):
      - any `Attribute` in a Store context (`sc.tl.x = ..`, `for sc.tl.x in ..`, `with cm() as sc.tl.x:`)
        records .attr in patched_attrs and, if rooted at an import, the dotted path in patched_paths;
      - a namespace subscript store (`globals()["stats"]=..`, `sc.tl.__dict__["rgg"]=..`, `vars(m)[k]=..`)
        havocs that string key, and if the key is an imported local, marks it ambiguous;
      - a call `f(obj, "name", ..)` whose first arg roots at an imported module (setattr / patch.object /
        any aliased patcher) havocs attr "name".
    patched_attrs over-abstains only on a store to a namespace-dict key that happens to equal a sink
    symbol — safe (the call becomes a review candidate) and vanishingly rare in analysis code."""
    patched: set = set()
    patched_attrs: set = set()
    ambiguous: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            patched_attrs.add(node.attr)
            p = _attr_path(node)
            if p is not None and p.split(".")[0] in import_locals:
                patched.add(p)
        elif isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store) \
                and _is_namespace_expr(node.value):
            key = const_str(node.slice)
            if key is not None:
                patched_attrs.add(key)
                if key in import_locals:
                    ambiguous.add(key)
        elif isinstance(node, ast.Call):
            if len(node.args) >= 2:                 # generic positional: f(imported_obj, "name", v)
                name = const_str(node.args[1])      # setattr / patch.object / any aliased patcher
                if name is not None and _expr_root(node.args[0]) in import_locals:
                    patched_attrs.add(name)
            for nm in _mutation_targets(node, import_locals):   # keyword/receiver/.update() forms
                patched_attrs.add(nm)
                if nm in import_locals:
                    ambiguous.add(nm)
    return patched, patched_attrs, ambiguous


def source_env(ps) -> SourceEnv:
    """Build one source's name environment. A name imported under two DISTINCT canonical targets (a
    try/except fallback, a re-import) is ambiguous -> demoted to `bound`, never binding a wrong contract
    (blocker #2). Relative (`from . import x`) and ambiguous imports still record their original symbol in
    `alias_symbols` so an abstained sink alias is diagnosed, never silently lost (blocker #1/miss). A
    `*`-import creates no binding."""
    imports: dict = {}
    ambiguous: set = set()
    alias_symbols: dict = {}
    if ps.tree is None:
        return SourceEnv(imports, set(), set(), set(), alias_symbols)
    for node in ast.walk(ps.tree):
        if isinstance(node, ast.Import):
            for alias in node.names:              # `import scanpy` / `import scanpy.tl as tl`
                local = alias.asname or alias.name.split(".")[0]
                module = alias.name if alias.asname else alias.name.split(".")[0]
                _record_import(imports, ambiguous, ImportBinding(local, module, None))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:              # `from scipy.stats import ttest_ind as welch`
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                alias_symbols.setdefault(local, set()).add(alias.name)   # original symbol, for diagnosis
                if node.level == 0 and node.module:                      # absolute import: resolvable
                    _record_import(imports, ambiguous, ImportBinding(local, node.module, alias.name))
                # relative imports (level>0) record the symbol for diagnosis but never resolve to a sink
    patched, patched_attrs, ns_ambiguous = _collect_patched(ps.tree, set(imports))
    bound = _collect_bound(ps.tree) | ambiguous | ns_ambiguous
    return SourceEnv(imports, bound, patched, patched_attrs, alias_symbols)


def _record_import(imports: dict, ambiguous: set, b: ImportBinding):
    prev = imports.get(b.local)
    if prev is not None and (prev.module, prev.symbol) != (b.module, b.symbol):
        ambiguous.add(b.local)                    # two different targets under one name -> ambiguous
    imports[b.local] = b


def resolve_callee(site, env: SourceEnv):
    """Canonical (module, symbol) for a call, or None when its identity is not PROVED. Requires an
    unambiguous per-source import binding (imported, and NOT otherwise bound in the source), no
    monkey-patch of the exact path. The returned module is canonical and compared EXACTLY to a contract
    module downstream, so `project.scipy.stats` does not masquerade as `scipy.stats` (blocker #4)."""
    call = site.call
    # a monkey-patch of this symbol — by exact path, by a patched prefix (`sc.tl = ...`), or reaching it
    # through an alias/setattr (any write to an attr of this name) — invalidates the library contract.
    if site.symbol_cased in env.patched_attrs:
        return None
    if isinstance(call.func, ast.Attribute):
        written = _attr_path(call.func)               # e.g. 'sc.tl.rank_genes_groups'
        if written is not None and any(written == p or written.startswith(p + ".") for p in env.patched):
            return None
    pref = _dotted_prefix(call)
    if pref is not None:
        root, mids = pref
        if root in env.bound or root not in env.imports:
            return None                               # shadowed/ambiguous, or root never imported
        b = env.imports[root]
        # module import -> scanpy(.tl...); from-import -> `from scipy import stats` treated as a module
        # namespace (scipy.stats), accepted only if the full path exactly matches a registry contract.
        base = [b.module] if b.symbol is None else [b.module, b.symbol]
        return ".".join([*base, *mids]), site.symbol_cased
    if isinstance(call.func, ast.Name):
        name = call.func.id
        if name in env.bound or name not in env.imports:
            return None
        b = env.imports[name]
        if b.symbol is not None:                      # a from-imported symbol (ttest_ind / welch)
            return b.module, b.symbol
    return None
