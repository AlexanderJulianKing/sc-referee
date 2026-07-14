"""Build-time purity validation for declarative policy modules."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

from sc_referee.inference.policy.schema import ValidityPolicy, validate_policy
from sc_referee.inference.proof.discharge import builtin_registry


class PolicyPurityError(ValueError):
    pass


_ALLOWED_IMPORTS = frozenset({
    "sc_referee.inference.policy.schema",
    "sc_referee.inference.refinement.types",
    "sc_referee.inference.ids",
})
_FORBIDDEN_NAMES = frozenset({
    "ast", "numpy", "scipy", "pandas", "code_signals", "source_ast", "provenance",
    "sink_use", "bundles", "adapters", "engines", "filesystem", "subprocess", "socket",
    "urllib", "requests", "http", "pathlib", "os",
})
_FORBIDDEN_NODES = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
    ast.For, ast.AsyncFor, ast.While, ast.If, ast.IfExp, ast.Try, ast.With,
    ast.AsyncWith, ast.Match, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
)
_ALLOWED_CONSTRUCTORS = frozenset({
    "FactRef", "RelationPremise", "ProviderInvocation", "ProofRule", "ValidityPolicy",
    "frozenset",
})


def definition_directory() -> Path:
    return Path(__file__).with_name("definitions")


def policy_definition_files() -> tuple[Path, ...]:
    return tuple(sorted(path for path in definition_directory().glob("*.py")
                        if path.name != "__init__.py"))


def lint_policy_source(source: str, *, filename: str = "<policy>") -> None:
    tree = ast.parse(source, filename=filename)
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                errors.append(f"forbidden import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module not in _ALLOWED_IMPORTS or any(part in _FORBIDDEN_NAMES for part in module.split(".")):
                errors.append(f"forbidden import {module}")
        if isinstance(node, _FORBIDDEN_NODES):
            errors.append(f"forbidden syntax {type(node).__name__}")
        if isinstance(node, ast.Call):
            called = node.func.id if isinstance(node.func, ast.Name) else type(node.func).__name__
            if called not in _ALLOWED_CONSTRUCTORS:
                errors.append(f"forbidden call {called}")
    for statement in tree.body:
        is_docstring = (
            isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
        if not isinstance(statement, (ast.ImportFrom, ast.Assign, ast.AnnAssign)) and not is_docstring:
            errors.append(f"forbidden top-level statement {type(statement).__name__}")
    if errors:
        raise PolicyPurityError(f"{filename}: " + "; ".join(dict.fromkeys(errors)))


def validate_policy_module(path: Path) -> ValidityPolicy:
    lint_policy_source(path.read_text(), filename=str(path))
    spec = importlib.util.spec_from_file_location(f"_sc_policy_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise PolicyPurityError(f"cannot load policy declaration: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = getattr(module, "POLICY", None)
    if not isinstance(policy, ValidityPolicy):
        raise PolicyPurityError(f"{path}: POLICY is not a ValidityPolicy")
    validate_policy(policy)
    registry = builtin_registry()
    for rule in policy.rules:
        for invocation in rule.discharge:
            if registry.resolve_exact(invocation.provider_id, invocation.provider_version,
                                      invocation.provider_digest) is None:
                raise PolicyPurityError(
                    f"{path}: unresolved provider {invocation.provider_id}@{invocation.provider_version}"
                )
    return policy
