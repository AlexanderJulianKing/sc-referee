"""Build a patched copy of MT 2.1 dataflow in scratch and expose an analyzer per delta set.

The repository is never modified. The module source is read, edited in memory, and
executed under a distinct module name.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402  (puts src on sys.path)
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 as BASE  # noqa: E402

SRC_PATH = Path(BASE.__file__)
SRC = SRC_PATH.read_text()

# --------------------------------------------------------------------------------------
# Delta 1: pure closed-scalar project-local helper becomes relevant (so it is inlined).
# --------------------------------------------------------------------------------------
D1_ANCHOR = """def _helper_relevant(
    *,
    call: ast.Call,
    target: ast.expr | None,
    helper: ast.FunctionDef,
    statements: Sequence[ast.stmt],
    statement_index: int,
    resolver: _Resolver,
) -> bool:
    if _constant_only_print_helper(helper, resolver) and all(
        _closed_constant_expression(argument, resolver) for argument in call.args
    ):
        return False
"""
D1_NEW = D1_ANCHOR + """    if _mt_d1_closed_scalar_helper(helper, resolver):
        return True
"""

D1_DEF = '''

def _mt_d1_closed_scalar_helper(helper: ast.FunctionDef, resolver: _Resolver) -> bool:
    """D1: a project-local helper that is one closed scalar expression of its parameters.

    Body is exactly one `return <expr>`; parameters are plain positionals with no
    defaults; the returned expression calls nothing but unshadowed builtins, contains
    no comprehension/lambda/await, and every free name is a parameter or a module name
    the resolver already carries. Inlining such a helper is a textual substitution of a
    closed expression: it can only expose more of the slice, never admit an unresolved
    edge silently.
    """

    body = [item for item in helper.body if not _is_docstring(item)]
    if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
        return False
    args = helper.args
    if (
        args.posonlyargs
        or args.kwonlyargs
        or args.vararg is not None
        or args.kwarg is not None
        or args.defaults
        or args.kw_defaults
    ):
        return False
    if not args.args:
        return False
    expression = body[0].value
    for node in ast.walk(expression):
        if isinstance(
            node,
            (
                ast.ListComp,
                ast.SetComp,
                ast.DictComp,
                ast.GeneratorExp,
                ast.Lambda,
                ast.Await,
                ast.Yield,
                ast.YieldFrom,
                ast.NamedExpr,
                ast.Starred,
            ),
        ):
            return False
        if isinstance(node, ast.Call):
            api = resolver.qualified(node.func)
            if api not in _UNSHADOWED_BUILTINS:
                return False
    return True

'''

# --------------------------------------------------------------------------------------
# Delta 2: hoist family-test calls out of proper sub-expression positions.
# --------------------------------------------------------------------------------------
D2_ANCHOR = """        normalized = _mt_expand_outcome_iterations(
            nested.scope,
            resolver=resolver,
            outcome_columns=outcome_columns,
            helpers=helpers,
        )
        if normalized is None:
            return MultipleTestingDataflowResult(None, "test-battery-cardinality-unresolved")
"""
D2_NEW = D2_ANCHOR + """        normalized = _mt_d2_hoist_family_calls(normalized, resolver, helpers)
"""

D2_DEF = '''

def _mt_d2_family_call_names(
    helpers: Mapping[str, ast.FunctionDef], resolver: _Resolver
) -> frozenset[str]:
    """Project-local helper names whose body syntactically contains a registered test."""

    return frozenset(
        name
        for name, helper in helpers.items()
        if any(
            isinstance(node, ast.Call) and resolver.qualified(node.func) in _MT_TEST_APIS
            for node in ast.walk(helper)
        )
    )


def _mt_d2_hoist_family_calls(
    scope: tuple[ast.stmt, ...],
    resolver: _Resolver,
    helpers: Mapping[str, ast.FunctionDef],
) -> tuple[ast.stmt, ...]:
    """D2: give every family-test call a statement-level binding.

    A registered test call (or a call to a project-local helper that contains one) that
    sits in a proper sub-expression position is replaced by a fresh name and preceded by
    `<fresh> = <call>`. Unconditional evaluation is preserved: a call under an IfExp, a
    BoolOp, a Lambda or a comprehension is left alone. This is a normalization, not an
    admission: it changes no acceptance rule, it only stops later record and loop
    expansion from cloning one runtime call into several syntactic copies.
    """

    family_helpers = _mt_d2_family_call_names(helpers, resolver)

    def is_family_call(node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False
        if resolver.qualified(node.func) in _MT_TEST_APIS:
            return True
        return isinstance(node.func, ast.Name) and node.func.id in family_helpers

    counter = [0]
    result: list[ast.stmt] = []
    for statement in scope:
        # Only simple statements are rewritten. A compound statement (For/While/If/Try/
        # With/def/class) keeps its own control flow: hoisting a call out of a loop or a
        # branch body would change how many times it runs, so those are left alone.
        if not isinstance(
            statement, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return)
        ):
            result.append(statement)
            continue
        # Do not hoist when the call is already the whole right-hand side.
        whole: set[int] = set()
        if isinstance(statement, ast.Assign) and is_family_call(statement.value):
            whole.add(id(statement.value))
        guarded: set[int] = set()
        for parent in ast.walk(statement):
            if isinstance(parent, (ast.IfExp, ast.BoolOp, ast.Lambda)) or isinstance(
                parent, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
            ):
                for node in ast.walk(parent):
                    guarded.add(id(node))
        prelude: list[ast.stmt] = []

        class Hoist(ast.NodeTransformer):
            def visit_Call(self, node: ast.Call) -> ast.AST:
                self.generic_visit(node)
                if id(node) in whole or id(node) in guarded or not is_family_call(node):
                    return node
                counter[0] += 1
                name = f"__sc_mt_hoist_{counter[0]}"
                assignment = ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store())], value=node
                )
                ast.copy_location(assignment, node)
                ast.copy_location(assignment.targets[0], node)
                ast.fix_missing_locations(assignment)
                prelude.append(assignment)
                replacement = ast.Name(id=name, ctx=ast.Load())
                ast.copy_location(replacement, node)
                for key in ("_sc_v22_loop_binding_ordinal",):
                    if key in node.__dict__:
                        replacement.__dict__[key] = node.__dict__[key]
                        assignment.__dict__[key] = node.__dict__[key]
                        assignment.targets[0].__dict__[key] = node.__dict__[key]
                return replacement

        rewritten = Hoist().visit(statement)
        assert isinstance(rewritten, ast.stmt)
        result.extend(prelude)
        result.append(rewritten)
    return tuple(result)

'''

# --------------------------------------------------------------------------------------
# Delta 3: closed contract-domain sequence length counts as the exact family size.
# --------------------------------------------------------------------------------------
D3_ANCHOR = """    def _exact_family_size(self, node: ast.expr) -> bool:
        if _mt_exact_int(node, self.resolver, len(self.outcome_columns)):
            return True
"""
D3_NEW = D3_ANCHOR + """        if self._mt_d3_contract_domain_length(node):
            return True
"""

D3_DEF = '''
    def _mt_d3_contract_domain_length(self, node: ast.expr) -> bool:
        """D3: `len(X)` where X is the frozen contract-domain outcome table itself.

        The multiplier is proved equal to the family size from frozen bytes: X must be a
        closed sequence (or closed table) whose members (or first column) are exactly the
        authorized outcome columns, in the authorized order. Nothing else is admitted;
        a `len()` of any other container still fails closed.
        """

        if not (
            isinstance(node, ast.Call)
            and self.resolver.qualified(node.func) == "len"
            and len(node.args) == 1
            and not node.keywords
        ):
            return False
        argument = node.args[0]
        sequence = self.resolver.sequence(argument)
        if sequence is not None and tuple(sequence) == self.outcome_columns:
            return True
        table = self.resolver.table(argument)
        if table is not None and tuple(row[0] for row in table if row) == self.outcome_columns:
            return True
        return False

'''


# --------------------------------------------------------------------------------------
# Delta 4: substitute closed-scalar helper calls in place (expression-level inlining).
# --------------------------------------------------------------------------------------
D4_ANCHOR = """        nested = _mt_v2_expand_nested_family_helper_arguments(
            scope,
            helpers=helpers,
            resolver=resolver,
        )
"""
D4_NEW = """        scope, helpers = _mt_d4_substitute_closed_scalar_helpers(scope, helpers, resolver)
        resolver, reason = _resolver((*setup, *scope))
        if reason is not None or resolver is None:
            return MultipleTestingDataflowResult(None, reason or "api-resolution-ambiguous")
""" + D4_ANCHOR

D4_DEF = '''

class _MtD4Substitute(ast.NodeTransformer):
    def __init__(self, bindings: Mapping[str, ast.expr]) -> None:
        self.bindings = bindings

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Load) and node.id in self.bindings:
            return copy.deepcopy(self.bindings[node.id])
        return node


def _mt_d4_substitute_closed_scalar_helpers(
    scope: tuple[ast.stmt, ...],
    helpers: Mapping[str, ast.FunctionDef],
    resolver: _Resolver,
) -> tuple[tuple[ast.stmt, ...], dict[str, ast.FunctionDef]]:
    """D4: replace `f(a)` by f's one closed return expression, wherever `f` is closed-scalar.

    Applies only to helpers admitted by `_mt_d1_closed_scalar_helper`, called with exactly
    as many positional arguments as parameters and no keywords, where every parameter is
    read at most once in the body (so no argument expression is ever duplicated) and no
    argument carries a registered-test call (so the family census is untouched). The
    substitution is applied inside helper bodies too, so a decision helper called from a
    presentation helper is resolved as well.
    """

    closed = {
        name: helper
        for name, helper in helpers.items()
        if _mt_d1_closed_scalar_helper(helper, resolver)
    }
    if not closed:
        return scope, dict(helpers)

    class Inline(ast.NodeTransformer):
        def visit_Call(self, node: ast.Call) -> ast.AST:
            self.generic_visit(node)
            if not (isinstance(node.func, ast.Name) and node.func.id in closed):
                return node
            helper = closed[node.func.id]
            parameters = [item.arg for item in helper.args.args]
            if node.keywords or len(node.args) != len(parameters):
                return node
            if any(isinstance(item, ast.Starred) for item in node.args):
                return node
            if any(
                isinstance(child, ast.Call) and resolver.qualified(child.func) in _MT_TEST_APIS
                for argument in node.args
                for child in ast.walk(argument)
            ):
                return node
            if not _mt_d4_single_use_parameters(helper) and not all(
                _mt_d4_duplicable(argument) for argument in node.args
            ):
                return node
            body = [item for item in helper.body if not _is_docstring(item)]
            expression = copy.deepcopy(cast(ast.Return, body[0]).value)
            assert expression is not None
            bindings = dict(zip(parameters, node.args, strict=True))
            replaced = _MtD4Substitute(bindings).visit(expression)
            assert isinstance(replaced, ast.expr)
            ast.copy_location(replaced, node)
            ast.fix_missing_locations(replaced)
            for item in ast.walk(replaced):
                for key in ("_sc_v22_loop_binding_ordinal",):
                    if key in node.__dict__ and key not in item.__dict__:
                        item.__dict__[key] = node.__dict__[key]
            return replaced

    rewritten_scope = tuple(
        cast(ast.stmt, Inline().visit(copy.deepcopy(item))) for item in scope
    )
    rewritten_helpers = {
        name: (
            helper
            if name in closed
            else cast(ast.FunctionDef, Inline().visit(copy.deepcopy(helper)))
        )
        for name, helper in helpers.items()
    }
    return rewritten_scope, rewritten_helpers


def _mt_d4_duplicable(node: ast.expr) -> bool:
    """A pure argument expression that may safely appear more than once after inlining."""

    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Subscript):
        return _mt_literal_member(node.slice) is not None and _mt_d4_duplicable(node.value)
    if isinstance(node, ast.Attribute):
        return _mt_d4_duplicable(node.value)
    return False


def _mt_d4_single_use_parameters(helper: ast.FunctionDef) -> bool:
    parameters = {item.arg for item in helper.args.args}
    counts: dict[str, int] = {name: 0 for name in parameters}
    for node in ast.walk(helper):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in counts:
            counts[node.id] += 1
    return all(value <= 1 for value in counts.values())

'''


# --------------------------------------------------------------------------------------
# Delta 5: closed frozen SET literal admitted for membership decisions only.
# --------------------------------------------------------------------------------------
D5_ANCHOR = """    if not (
        isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], (ast.In, ast.NotIn))
        and len(statement.test.comparators) == 1
        and isinstance(statement.test.left, ast.Constant)
        and isinstance(statement.test.left.value, str)
        and (sequence := resolver.sequence(statement.test.comparators[0])) is not None
    ):
        return (statement,)
"""
D5_NEW = """    if not (
        isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], (ast.In, ast.NotIn))
        and len(statement.test.comparators) == 1
        and isinstance(statement.test.left, ast.Constant)
        and isinstance(statement.test.left.value, str)
        and (
            sequence := (
                resolver.sequence(statement.test.comparators[0])
                or _mt_d5_membership_set(statement.test.comparators[0], resolver)
            )
        )
        is not None
    ):
        return (statement,)
"""

D5_DEF = '''

_MT_D5_SETS: dict[str, tuple[object, ...]] = {}

_MT_D5_SET_MUTATORS = frozenset(
    {
        "add",
        "discard",
        "remove",
        "pop",
        "clear",
        "update",
        "difference_update",
        "intersection_update",
        "symmetric_difference_update",
    }
)


def _mt_d5_membership_set(node: ast.expr, resolver: _Resolver) -> tuple[object, ...] | None:
    """D5: a closed set of string literals, for MEMBERSHIP decisions only.

    A set literal carries no order, so it is deliberately NOT routed through
    `_Resolver.sequence`: it can never become an iteration domain or an outcome
    ordering. It answers exactly one question, `is this literal a member`, which a set
    answers as decidably as a list. Admission requires the name to be bound once at
    module setup to a set of string constants and never mutated or rebound anywhere in
    the module.
    """

    members = _MT_D5_SETS
    if isinstance(node, ast.Set):
        values = _closed_sequence_elements(node.elts)
        return tuple(values) if values is not None else None
    if isinstance(node, ast.Name):
        return members.get(node.id)
    return None


def _mt_d5_collect_sets(tree: ast.Module) -> dict[str, tuple[object, ...]]:
    candidates: dict[str, tuple[object, ...]] = {}
    for statement in tree.body:
        target, value = _mt_setup_target_value(statement)
        if target is None or value is None:
            continue
        if isinstance(value, ast.Set):
            values = _closed_sequence_elements(value.elts)
            if values is not None and all(isinstance(item, str) for item in values):
                candidates[target.id] = tuple(values)
        elif (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in {"set", "frozenset"}
            and len(value.args) == 1
            and not value.keywords
            and isinstance(value.args[0], (ast.List, ast.Tuple, ast.Set))
        ):
            values = _closed_sequence_elements(cast(Any, value.args[0]).elts)
            if values is not None and all(isinstance(item, str) for item in values):
                candidates[target.id] = tuple(values)
    if not candidates:
        return {}
    # Whole-module non-mutation / non-rebinding proof.
    binding_counts: dict[str, int] = {name: 0 for name in candidates}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            for item in targets:
                for name in _store_names(item):
                    if name in binding_counts:
                        binding_counts[name] += 1
        if isinstance(node, (ast.For, ast.comprehension)):
            for name in _store_names(node.target):
                if name in binding_counts:
                    binding_counts[name] += 1
        if isinstance(node, ast.FunctionDef):
            for item in node.args.args:
                if item.arg in binding_counts:
                    binding_counts[item.arg] += 1
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in binding_counts
            and node.func.attr in _MT_D5_SET_MUTATORS
        ):
            binding_counts[node.func.value.id] += 99
        if isinstance(node, ast.Delete):
            for item in node.targets:
                for name in _store_names(item):
                    if name in binding_counts:
                        binding_counts[name] += 99
    return {
        name: values for name, values in candidates.items() if binding_counts.get(name, 0) == 1
    }

'''

D5_INSTALL_ANCHOR = """        if _mt_v2_integrity_census(tree, full_resolver):
            return MultipleTestingDataflowResult(None, "api-resolution-ambiguous")
"""
D5_INSTALL_NEW = D5_INSTALL_ANCHOR + """        _MT_D5_SETS.clear()
        _MT_D5_SETS.update(_mt_d5_collect_sets(tree))
"""


# --------------------------------------------------------------------------------------
# Delta 6: run the terminal presentation/verdict-helper rewrite a second time, after
# project-local helper inlining, so a presentation helper called from inside another
# helper is rewritten too. No new grammar: the same closed transformer, applied again.
# --------------------------------------------------------------------------------------
D6_ANCHOR = """        expanded_once = _mt_v2_expand_literal_destructuring(expansion.scope)
"""
D6_NEW = """        expanded_once = _mt_v2_expand_literal_destructuring(
            _mt_v2_expand_terminal_helpers(expansion.scope, helpers, resolver)
        )
"""


def build(deltas: str) -> types.ModuleType:
    text = SRC
    if "4" in deltas and "1" not in deltas:
        deltas = deltas + "1"
    if "1" in deltas:
        assert D1_ANCHOR in text
        text = text.replace(D1_ANCHOR, D1_NEW)
        text = text.replace("\ndef _constant_only_print_helper(", D1_DEF + "\ndef _constant_only_print_helper(", 1)
    if "2" in deltas:
        assert D2_ANCHOR in text
        text = text.replace(D2_ANCHOR, D2_NEW)
        text = text.replace("\ndef _mt_expand_outcome_iterations(", D2_DEF + "\ndef _mt_expand_outcome_iterations(", 1)
    if "3" in deltas:
        assert D3_ANCHOR in text
        text = text.replace(D3_ANCHOR, D3_NEW)
        text = text.replace(
            "    def _closed_builder_positions(self, name: str) -> tuple[int, ...] | None:",
            D3_DEF + "    def _closed_builder_positions(self, name: str) -> tuple[int, ...] | None:",
            1,
        )
    if "4" in deltas:
        assert D4_ANCHOR in text
        text = text.replace(D4_ANCHOR, D4_NEW, 1)
        text = text.replace(
            "\ndef _mt_expand_outcome_iterations(",
            D4_DEF + "\ndef _mt_expand_outcome_iterations(",
            1,
        )
    if "5" in deltas:
        assert D5_ANCHOR in text
        text = text.replace(D5_ANCHOR, D5_NEW, 1)
        assert D5_INSTALL_ANCHOR in text
        text = text.replace(D5_INSTALL_ANCHOR, D5_INSTALL_NEW, 1)
        text = text.replace(
            "\ndef _mt_expand_outcome_iterations(",
            D5_DEF + "\ndef _mt_expand_outcome_iterations(",
            1,
        )
    if "6" in deltas:
        assert D6_ANCHOR in text
        text = text.replace(D6_ANCHOR, D6_NEW, 1)
    name = f"mt_patched_{''.join(sorted(deltas)) or 'none'}"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).parent / f"{name}.py"
    path.write_text(text)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def analyzer(deltas: str):
    return build(deltas).analyze_code_csv_multiple_testing_dataflow
