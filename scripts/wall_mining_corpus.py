#!/usr/bin/env python3
"""Build a development-only, non-measurement corpus for v2 wall-frequency mining."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.authority_lock import (
    apply_dependence_v2_authorization_lock,
    build_dependence_v2_authorization_lock,
    lock_projection,
)
from sc_referee.dependence_recognition_v2.intake_declaration import (
    receipt_dict,
    translate_unit_declaration,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = Path("evaluation/development/wall-mining-corpus")
CLAUDE_PINNED = Path.home() / ".local/share/claude/versions/2.1.221"
MODEL_ALIAS = "haiku"
MAX_CONCURRENCY = 3
RECORD_PURPOSE = "development_wall_mining"
NON_MEASUREMENT = (
    "OPEN DEVELOPMENT WALL CENSUS ONLY. This corpus is non-measurement, carries no labels, "
    "and is unreachable from qualification and production lanes."
)
_RUN_NAME = re.compile(r"run-[a-z0-9][a-z0-9-]{0,62}\Z")
_GROUP_CALLABLES = {
    "ttest_ind": "scipy.stats.ttest_ind",
    "mannwhitneyu": "scipy.stats.mannwhitneyu",
}
_DYNAMIC_IDENTIFIERS = frozenset(
    {
        "exec",
        "eval",
        "compile",
        "globals",
        "locals",
        "vars",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
    }
)
_DYNAMIC_IMPORT_ROOTS = frozenset(
    {"builtins", "importlib", "sys", "inspect", "types", "code", "codeop", "runpy", "ctypes"}
)
_FORBIDDEN_BINDINGS = _DYNAMIC_IDENTIFIERS | {"stats"}
_INTAKE_RECORDED_AT = "1970-01-01T00:00:00Z"

# This is deliberately a literal Python 3.11 mapping. Runtime field drift is refusal,
# not an invitation to inherit a newer interpreter's syntax.
_ADMITTED_AST_FIELDS: dict[type[ast.AST], tuple[str, ...]] = {
    ast.Module: ("body", "type_ignores"),
    ast.Expr: ("value",),
    ast.Import: ("names",),
    ast.ImportFrom: ("module", "names", "level"),
    ast.Assign: ("targets", "value", "type_comment"),
    ast.AnnAssign: ("target", "annotation", "value", "simple"),
    ast.AugAssign: ("target", "op", "value"),
    ast.FunctionDef: ("name", "args", "body", "decorator_list", "returns", "type_comment"),
    ast.ClassDef: ("name", "bases", "keywords", "body", "decorator_list"),
    ast.Return: ("value",),
    ast.Raise: ("exc", "cause"),
    ast.Assert: ("test", "msg"),
    ast.Pass: (),
    ast.Break: (),
    ast.Continue: (),
    ast.If: ("test", "body", "orelse"),
    ast.For: ("target", "iter", "body", "orelse", "type_comment"),
    ast.While: ("test", "body", "orelse"),
    ast.With: ("items", "body", "type_comment"),
    ast.Try: ("body", "handlers", "orelse", "finalbody"),
    ast.arguments: (
        "posonlyargs",
        "args",
        "vararg",
        "kwonlyargs",
        "kw_defaults",
        "kwarg",
        "defaults",
    ),
    ast.arg: ("arg", "annotation", "type_comment"),
    ast.keyword: ("arg", "value"),
    ast.alias: ("name", "asname"),
    ast.withitem: ("context_expr", "optional_vars"),
    ast.ExceptHandler: ("type", "name", "body"),
    ast.Constant: ("value", "kind"),
    ast.Name: ("id", "ctx"),
    ast.Attribute: ("value", "attr", "ctx"),
    ast.Subscript: ("value", "slice", "ctx"),
    ast.Slice: ("lower", "upper", "step"),
    ast.Call: ("func", "args", "keywords"),
    ast.BinOp: ("left", "op", "right"),
    ast.UnaryOp: ("op", "operand"),
    ast.BoolOp: ("op", "values"),
    ast.Compare: ("left", "ops", "comparators"),
    ast.IfExp: ("test", "body", "orelse"),
    ast.List: ("elts", "ctx"),
    ast.Tuple: ("elts", "ctx"),
    ast.Set: ("elts",),
    ast.Dict: ("keys", "values"),
    ast.Starred: ("value", "ctx"),
    ast.NamedExpr: ("target", "value"),
    ast.Lambda: ("args", "body"),
    ast.ListComp: ("elt", "generators"),
    ast.SetComp: ("elt", "generators"),
    ast.DictComp: ("key", "value", "generators"),
    ast.GeneratorExp: ("elt", "generators"),
    ast.comprehension: ("target", "iter", "ifs", "is_async"),
    ast.JoinedStr: ("values",),
    ast.FormattedValue: ("value", "conversion", "format_spec"),
    ast.Load: (),
    ast.Store: (),
    ast.Add: (),
    ast.Sub: (),
    ast.Mult: (),
    ast.Div: (),
    ast.FloorDiv: (),
    ast.Mod: (),
    ast.Pow: (),
    ast.MatMult: (),
    ast.LShift: (),
    ast.RShift: (),
    ast.BitOr: (),
    ast.BitXor: (),
    ast.BitAnd: (),
    ast.UAdd: (),
    ast.USub: (),
    ast.Not: (),
    ast.Invert: (),
    ast.And: (),
    ast.Or: (),
    ast.Eq: (),
    ast.NotEq: (),
    ast.Lt: (),
    ast.LtE: (),
    ast.Gt: (),
    ast.GtE: (),
    ast.Is: (),
    ast.IsNot: (),
    ast.In: (),
    ast.NotIn: (),
}

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["domain", "analysis_py", "data_csv", "data_description_md"],
    "properties": {
        "domain": {"type": "string", "minLength": 3, "maxLength": 80},
        "analysis_py": {"type": "string", "minLength": 200, "maxLength": 20000},
        "data_csv": {"type": "string", "minLength": 20, "maxLength": 30000},
        "data_description_md": {
            "type": "string",
            "minLength": 20,
            "maxLength": 4000,
            "description": (
                "Plain-language study metadata ending with exactly one "
                "Independent unit column: COLUMN line naming a complete CSV header."
            ),
        },
    },
}


def _prompt(index: int, count: int) -> str:
    return f"""Create one realistic, self-contained Python scientific analysis, item {index + 1} of {count} in a varied collection.

Choose an ordinary empirical domain and coding style for a realistic analysis of two independent groups. Vary domains, program structure, naming, group construction, filtering, validation, reporting, and data shape across the collection. The program must read data/input.csv and write a substantive Markdown report to results/report.md.

Use ordinary synchronous Python without exec, eval, reflection, import hooks, monkeypatching, frame or traceback access, or namespace rewriting. Include exactly one canonical module-level `from scipy import stats` import and exactly one direct call written as either `stats.ttest_ind(...)` or `stats.mannwhitneyu(...)`.

Include a small realistic CSV that makes the program runnable. The plain-language data description must end with exactly one line `Independent unit column: COLUMN`, where COLUMN is the exact CSV header whose complete, nonempty values identify independent observational units. Return only the requested JSON object. Do not wrap code or CSV in Markdown fences."""


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    if value.get("record_purpose") != RECORD_PURPOSE:
        raise ValueError("every wall-mining record must carry the development purpose")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _call_haiku(run_name: str, index: int, count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = _prompt(index, count)
    case_identity = f"{run_name}:{index + 1:04d}"
    session_id = str(
        uuid5(
            NAMESPACE_URL,
            f"wall-mining:{run_name}:{count}:{index}:{sha256_digest(prompt)}",
        )
    )
    argv = [
        str(CLAUDE_PINNED),
        "--safe-mode",
        "--print",
        "--model",
        MODEL_ALIAS,
        "--effort",
        "low",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--permission-mode",
        "dontAsk",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        canonical_json(_RESPONSE_SCHEMA),
        "--session-id",
        session_id,
        prompt,
    ]
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-wall-mining-") as temporary:
        completed = subprocess.run(
            argv,
            cwd=temporary,
            env=environment,
            capture_output=True,
            check=False,
            timeout=600,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"haiku generation {index + 1} failed with exit {completed.returncode}")
    try:
        envelope = json.loads(completed.stdout.decode("utf-8", errors="strict"))
        result = json.loads(str(envelope["result"]))
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(f"haiku generation {index + 1} returned malformed JSON") from error
    if not isinstance(result, dict) or set(result) != set(_RESPONSE_SCHEMA["required"]):
        raise RuntimeError(f"haiku generation {index + 1} violated the closed response shape")
    served_model_ids = sorted(set(cast(dict[str, Any], envelope).get("modelUsage", {})))
    if not served_model_ids or any("haiku" not in item.casefold() for item in served_model_ids):
        raise RuntimeError(f"haiku generation {index + 1} reported another served model")
    generation = {
        "record_type": "development_wall_mining_generation",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": run_name,
        "case_identity": case_identity,
        "case_index": index,
        "model_alias": MODEL_ALIAS,
        "session_id": session_id,
        "prompt_digest": sha256_digest(prompt),
        "argv_digest": semantic_digest(argv),
        "stdout_digest": sha256_digest(completed.stdout),
        "stderr_digest": sha256_digest(completed.stderr),
        "served_model_ids": served_model_ids,
        "generated_at": _now(),
        "project_code_executed": False,
        "measurement_authority": "none",
    }
    return cast(dict[str, Any], result), generation


def _validate_ast_envelope(node: ast.AST) -> bool:
    expected_fields = _ADMITTED_AST_FIELDS.get(type(node))
    if expected_fields is None or type(node)._fields != expected_fields:
        return False
    for field in expected_fields:
        value = getattr(node, field)
        if isinstance(value, ast.AST):
            if not _validate_ast_envelope(value):
                return False
        elif isinstance(value, list):
            if any(
                not isinstance(item, ast.AST) or not _validate_ast_envelope(item) for item in value
            ):
                return False
    return True


def _canonical_procedure_call(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    root = node.func.value
    if (
        not isinstance(root, ast.Name)
        or root.id != "stats"
        or not isinstance(root.ctx, ast.Load)
        or not isinstance(node.func.ctx, ast.Load)
    ):
        return None
    return _GROUP_CALLABLES.get(node.func.attr)


def _procedure_transport(source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return (), ("procedure-source-not-compilable",)
    try:
        compile(tree, "workflow/analysis.py", "exec")
    except (SyntaxError, TypeError, ValueError):
        return (), ("procedure-source-not-compilable",)
    if not _validate_ast_envelope(tree):
        return (), ("procedure-authority-ast-outside-safe-language",)

    reasons: set[str] = set()
    canonical_imports: list[ast.ImportFrom] = []
    canonical_call_nodes: list[ast.Call] = []
    procedures: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root == "scipy" or root in _DYNAMIC_IMPORT_ROOTS or alias.name == "*":
                    reasons.add("procedure-import-not-canonical")
                bound = alias.asname if alias.asname is not None else root
                if bound in _FORBIDDEN_BINDINGS:
                    reasons.add("procedure-authority-root-not-closed")
        elif isinstance(node, ast.ImportFrom):
            canonical = (
                node.module == "scipy"
                and node.level == 0
                and len(node.names) == 1
                and node.names[0].name == "stats"
                and node.names[0].asname is None
            )
            if canonical:
                canonical_imports.append(node)
            module_root = (node.module or "").split(".", 1)[0]
            if (
                node.level != 0
                or any(alias.name == "*" for alias in node.names)
                or (module_root == "scipy" and not canonical)
                or module_root in _DYNAMIC_IMPORT_ROOTS
            ):
                reasons.add("procedure-import-not-canonical")
            for alias in node.names:
                bound = alias.asname or alias.name
                if bound in _FORBIDDEN_BINDINGS and not canonical:
                    reasons.add("procedure-authority-root-not-closed")
        if isinstance(node, ast.Call):
            procedure = _canonical_procedure_call(node)
            if procedure is not None:
                canonical_call_nodes.append(node)
                procedures.append(procedure)
        if isinstance(node, ast.Name) and node.id in _DYNAMIC_IDENTIFIERS:
            reasons.add("procedure-authority-root-not-closed")
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("__")
            or node.attr.endswith("__")
            or node.attr in {"tb_frame", "f_globals", "f_locals"}
        ):
            reasons.add("procedure-authority-root-not-closed")
        if isinstance(node, ast.arg) and node.arg in _FORBIDDEN_BINDINGS:
            reasons.add("procedure-authority-root-not-closed")
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in _FORBIDDEN_BINDINGS:
            reasons.add("procedure-authority-root-not-closed")
        if isinstance(node, ast.ExceptHandler) and node.name in _FORBIDDEN_BINDINGS:
            reasons.add("procedure-authority-root-not-closed")

    if len(canonical_imports) != 1 or canonical_imports[0] not in tree.body:
        reasons.add("procedure-import-not-canonical")
    if len(canonical_call_nodes) != 1:
        reasons.add("procedure-call-missing-or-ambiguous")
    allowed_stats_root: ast.AST | None = None
    if len(canonical_call_nodes) == 1 and isinstance(canonical_call_nodes[0].func, ast.Attribute):
        allowed_stats_root = canonical_call_nodes[0].func.value
    if any(
        isinstance(node, ast.Name) and node.id == "stats" and node is not allowed_stats_root
        for node in ast.walk(tree)
    ):
        reasons.add("procedure-authority-root-not-closed")
    if reasons:
        return (), tuple(sorted(reasons))
    return (procedures[0],), ()


def _unit_transport(description: str, data: bytes) -> tuple[str | None, tuple[str, ...]]:
    translated = translate_unit_declaration(
        description.encode("utf-8"), data, "wall-census-standalone-v1"
    )
    reasons = () if translated.reason is None else (translated.reason,)
    return translated.unit_column, reasons


def _context(
    source: str, data: bytes, run_name: str, case_identity: str
) -> FrozenInspectionContext:
    source_bytes = source.encode("utf-8")
    requirements = b"scipy==1.14.0\n"
    data_digest = sha256_digest(data)
    source_digest = sha256_digest(source_bytes)
    requirements_digest = sha256_digest(requirements)
    snapshot_digest = semantic_digest(
        {
            "run_name": run_name,
            "case_identity": case_identity,
            "source_digest": source_digest,
            "data_digest": data_digest,
            "requirements_digest": requirements_digest,
            "purpose": RECORD_PURPOSE,
        }
    )
    identity_suffix = f"wall-mining:{case_identity}"
    surface = RecordRef("publication_surface", f"surface:{identity_suffix}")
    artifact = RecordRef("artifact", f"artifact:{identity_suffix}")
    snapshot = RecordRef("repository_snapshot", f"snapshot:{identity_suffix}")
    source_file = RecordRef("file_record", f"file:source:{identity_suffix}")
    parser = RecordRef("parser_result", f"parser:source:{identity_suffix}")
    data_file = RecordRef("file_record", f"file:data:{identity_suffix}")
    data_identity = RecordRef("asset_identity", f"asset:data:{identity_suffix}")
    requirements_file = RecordRef("file_record", f"file:requirements:{identity_suffix}")
    requirements_identity = RecordRef("asset_identity", f"asset:requirements:{identity_suffix}")
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    values: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface,
            {
                "publication_surface_id": surface.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact.to_dict()]},
            },
        ),
        (
            artifact,
            {"artifact_id": artifact.record_id, "kind": "report", "path": "results/report.md"},
        ),
        (
            snapshot,
            {
                "snapshot_id": snapshot.record_id,
                "extensions": {
                    "x-material-full-digest-paths": ["data/input.csv", "requirements.txt"]
                },
            },
        ),
        (
            data_file,
            {
                "file_record_id": data_file.record_id,
                "path": "data/input.csv",
                "entry_kind": "regular_file",
                "asset_identity_ref": data_identity.to_dict(),
            },
        ),
        (
            data_identity,
            {
                "asset_identity_id": data_identity.record_id,
                "tier": "full_digest",
                "asset_ref": data_file.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
        (
            requirements_file,
            {
                "file_record_id": requirements_file.record_id,
                "path": "requirements.txt",
                "entry_kind": "regular_file",
                "asset_identity_ref": requirements_identity.to_dict(),
            },
        ),
        (
            requirements_identity,
            {
                "asset_identity_id": requirements_identity.record_id,
                "tier": "full_digest",
                "asset_ref": requirements_file.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": requirements_digest},
            },
        ),
        (source_file, {"file_record_id": source_file.record_id}),
        (parser, {"parser_result_id": parser.record_id}),
    ]
    return FrozenInspectionContext(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=surface,
        selected_artifact_ref=artifact,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=source_file,
                content=source_bytes,
                content_digest=source_digest,
                media_type="text/x-python",
                parser_result_ref=parser,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in values),
        material_inputs=(
            FrozenMaterialInput(
                path="data/input.csv",
                file_ref=data_file,
                asset_identity_ref=data_identity,
                content=data,
                content_digest=data_digest,
            ),
            FrozenMaterialInput(
                path="requirements.txt",
                file_ref=requirements_file,
                asset_identity_ref=requirements_identity,
                content=requirements,
                content_digest=requirements_digest,
            ),
        ),
    )


def _write_case(
    run_root: Path,
    run_name: str,
    index: int,
    result: dict[str, Any],
    generation: dict[str, Any],
) -> dict[str, Any]:
    case_root = run_root / "cases" / f"{index + 1:04d}"
    case_identity = f"{run_name}:{index + 1:04d}"
    case_id = f"case:wall-mining:{case_identity}"
    source = str(result["analysis_py"])
    data = str(result["data_csv"]).encode("utf-8")
    description = str(result["data_description_md"])
    (case_root / "workflow").mkdir(parents=True)
    (case_root / "data").mkdir()
    (case_root / "workflow/analysis.py").write_text(source, encoding="utf-8")
    (case_root / "data/input.csv").write_bytes(data)
    (case_root / "data-description.md").write_text(description, encoding="utf-8")
    _write_json(case_root / "generation.json", generation)
    unit_translation = translate_unit_declaration(
        description.encode("utf-8"), data, "wall-census-standalone-v1"
    )
    unit_column = unit_translation.unit_column
    unit_reasons = () if unit_translation.reason is None else (unit_translation.reason,)
    procedures, procedure_reasons = _procedure_transport(source) if not unit_reasons else ((), ())
    translation_reasons = tuple(sorted(set(procedure_reasons) | set(unit_reasons)))
    projected = unit_column is not None and len(procedures) == 1 and not translation_reasons
    base_context = _context(source, data, run_name, case_identity)
    translation: dict[str, Any] = {
        "record_type": "development_wall_mining_lock_translation",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": run_name,
        "case_identity": case_identity,
        "case_index": index,
        "role_information_used": False,
        "translation_version": unit_translation.translation_version,
        "description_content_digest": sha256_digest(description.encode("utf-8")),
        "input_content_digest": sha256_digest(data),
        "parsed_header_digest": unit_translation.parsed_header_digest,
        "lock_projection_digest": None,
        "declared_unit_column": unit_column,
        "resolved_procedures": list(procedures),
        "translation_outcome": "lock-projected" if projected else "no-lock",
        "translation_reasons": list(translation_reasons),
        "v1_translation_outcome": None,
        "v1_translation_reasons": [],
        "v1_lock_digest": None,
        "v2_translation_outcome": "lock-projected" if projected else "no-lock",
        "v2_translation_reasons": list(translation_reasons),
        "v2_unit_translation_reason": unit_translation.reason,
        "v2_translation_receipt": receipt_dict(unit_translation) if projected else None,
        "v2_lock_digest": None,
        "v2_lock_projection_digest": None,
    }
    lock_digest: str | None = None
    inspection_context = base_context
    if projected:
        assert unit_column is not None
        lock = build_dependence_v2_authorization_lock(
            case_id=case_id,
            snapshot_digest=base_context.snapshot_digest,
            intake_recorded_at=_INTAKE_RECORDED_AT,
            procedure=procedures[0],
            unit_column=unit_column,
            input_path="data/input.csv",
            input_content_digest=sha256_digest(data),
        )
        lock_path = case_root / "authorization-lock.json"
        lock_payload = (canonical_json(lock) + "\n").encode("utf-8")
        lock_path.write_bytes(lock_payload)
        inspection_context = apply_dependence_v2_authorization_lock(
            base_context,
            lock_path,
            expected_case_id=case_id,
            expected_intake_recorded_at=_INTAKE_RECORDED_AT,
        )
        lock_digest = str(lock["lock_digest"])
        lock_projection_digest = semantic_digest(lock_projection(lock))
        translation["authorization_lock_path"] = str(lock_path.relative_to(run_root))
        translation["authorization_case_id"] = case_id
        translation["authorization_snapshot_digest"] = lock["snapshot_digest"]
        translation["lock_digest"] = lock_digest
        translation["lock_projection_digest"] = lock_projection_digest
        translation["v2_lock_digest"] = lock_digest
        translation["v2_lock_projection_digest"] = lock_projection_digest
        translation["approved_projection_digest"] = lock["approval"]["approved_projection_digest"]
        translation["authorization_lock_content_digest"] = sha256_digest(lock_payload)
    translation["translation_digest"] = semantic_digest(translation)
    _write_json(case_root / "lock-translation.json", translation)
    payload = DependenceRecognitionV2ShadowAdapter().inspect(inspection_context)
    payload["record_purpose"] = RECORD_PURPOSE
    payload["measurement_authority"] = "none"
    shadow = {
        "record_type": "development_wall_mining_shadow_observation",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": run_name,
        "case_identity": case_identity,
        "case_index": index,
        "domain": str(result["domain"]),
        "lock_translation_outcome": translation["translation_outcome"],
        "translation_reasons": list(translation_reasons),
        "lock_digest": lock_digest,
        "translation_digest": translation["translation_digest"],
        "shadow_payload": payload,
        "measurement_authority": "none",
    }
    shadow["observation_digest"] = semantic_digest(shadow)
    _write_json(case_root / "shadow-result.json", shadow)
    return shadow


def _validate_run_request(count: int, run_name: str) -> None:
    if count < 1:
        raise ValueError("count must be positive")
    if _RUN_NAME.fullmatch(run_name) is None:
        raise ValueError("run_name must match run-[a-z0-9][a-z0-9-]{0,62}")


def _allocate_run_root(project_root: Path, run_name: str) -> Path:
    resolved_project = project_root.resolve(strict=True)
    if not resolved_project.is_dir():
        raise NotADirectoryError(f"project root is not a directory: {resolved_project}")
    corpus_root = resolved_project
    missing: list[Path] = []
    for component in CORPUS_ROOT.parts:
        corpus_root /= component
        if os.path.lexists(corpus_root):
            if corpus_root.is_symlink() or not corpus_root.is_dir():
                raise ValueError(f"unsafe wall-mining corpus component: {corpus_root}")
        else:
            missing.append(corpus_root)
    intended = corpus_root.resolve(strict=False)
    if not intended.is_relative_to(resolved_project):
        raise ValueError("wall-mining corpus root escapes the project root")
    run_root = corpus_root / run_name
    if os.path.lexists(run_root):
        raise FileExistsError(f"wall-mining run already exists: {run_root}")
    for directory in missing:
        directory.mkdir()
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"unsafe wall-mining corpus component: {directory}")
    if not corpus_root.resolve(strict=True).is_relative_to(resolved_project):
        raise ValueError("wall-mining corpus root escapes the project root")
    try:
        run_root.mkdir()
    except FileExistsError:
        raise FileExistsError(f"wall-mining run already exists: {run_root}") from None
    return run_root


def build_corpus(project_root: Path, count: int, run_name: str) -> Path:
    _validate_run_request(count, run_name)
    if not CLAUDE_PINNED.is_file():
        raise FileNotFoundError(f"Claude CLI is missing: {CLAUDE_PINNED}")
    run_root = _allocate_run_root(project_root, run_name)
    with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENCY, count)) as executor:
        generated = list(
            executor.map(lambda index: _call_haiku(run_name, index, count), range(count))
        )
    observations = [
        _write_case(run_root, run_name, index, result, generation)
        for index, (result, generation) in enumerate(generated)
    ]
    wall_frequencies: dict[str, int] = {}
    transport_frequencies: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    for observation in observations:
        payload = cast(dict[str, Any], observation["shadow_payload"])
        outcome = str(payload.get("outcome", "missing"))
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        for reason in observation["translation_reasons"]:
            key = str(reason)
            transport_frequencies[key] = transport_frequencies.get(key, 0) + 1
        if observation["lock_translation_outcome"] != "lock-projected":
            continue
        for reason in payload.get("abstention_reasons", []):
            key = str(reason)
            wall_frequencies[key] = wall_frequencies.get(key, 0) + 1
    census = {
        "record_type": "development_wall_mining_census",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": run_name,
        "case_count": count,
        "model_alias": MODEL_ALIAS,
        "generation_calls": count,
        "maximum_generation_concurrency": MAX_CONCURRENCY,
        "outcome_frequencies": dict(sorted(outcomes.items())),
        "transport_failure_frequencies": dict(
            sorted(transport_frequencies.items(), key=lambda item: (-item[1], item[0]))
        ),
        "wall_frequencies": dict(
            sorted(wall_frequencies.items(), key=lambda item: (-item[1], item[0]))
        ),
        "measurement_authority": "none",
        "completed_at": _now(),
    }
    census["census_digest"] = semantic_digest(census)
    _write_json(run_root / "wall-frequency-census.json", census)
    rows = [
        "# Development wall-frequency census",
        "",
        f"> {NON_MEASUREMENT}",
        "",
        "| Wall | Frequency |",
        "| --- | ---: |",
        *[
            f"| `{reason}` | {frequency} |"
            for reason, frequency in sorted(
                wall_frequencies.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        "",
        "| Transport refusal | Frequency |",
        "| --- | ---: |",
        *[
            f"| `{reason}` | {frequency} |"
            for reason, frequency in sorted(
                transport_frequencies.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        "",
        "Outcomes: " + ", ".join(f"`{key}` {value}" for key, value in sorted(outcomes.items())),
        "",
    ]
    (run_root / "wall-frequency-census.md").write_text("\n".join(rows), encoding="utf-8")
    run_record = {
        "record_type": "development_wall_mining_run",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": run_name,
        "case_count": count,
        "census_digest": census["census_digest"],
        "measurement_authority": "none",
    }
    run_record["run_digest"] = semantic_digest(run_record)
    _write_json(run_root / "RUN.json", run_record)
    return run_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--count", type=int, default=40)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    arguments = parser.parse_args()
    print(build_corpus(arguments.project_root, arguments.count, arguments.run_name))


if __name__ == "__main__":
    main()
