#!/usr/bin/env python3
"""Build a development-only, non-measurement corpus for v2 wall-frequency mining."""

from __future__ import annotations

import argparse
import ast
import csv
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
    V2_GROUP_PROCEDURES,
    V2_PROCEDURES,
    build_dependence_v2_authorization_lock,
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
_UNIT_DECLARATION = re.compile(r"(?mi)^Independent unit column:[ \t]*([^\r\n]+)$")
_TRIAL_DECLARATION = re.compile(r"(?m)^One trial is: one row[ \t]*$")
_REGISTERED = frozenset(V2_PROCEDURES)

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["domain", "analysis_py", "data_csv", "data_description_md"],
    "properties": {
        "domain": {"type": "string", "minLength": 3, "maxLength": 80},
        "analysis_py": {"type": "string", "minLength": 200, "maxLength": 20000},
        "data_csv": {"type": "string", "minLength": 20, "maxLength": 30000},
        "data_description_md": {"type": "string", "minLength": 20, "maxLength": 4000},
    },
}


def _prompt(index: int, count: int) -> str:
    return f"""Create one realistic, self-contained Python scientific analysis, item {index + 1} of {count} in a varied collection.

Choose an ordinary empirical domain and coding style. Vary domains, statistical procedures, program structure, naming, validation, reporting, and data shape across the collection. The program must read data/input.csv and write a substantive Markdown report to results/report.md. Include a small realistic CSV that makes the program runnable and a plain-language data description. Prefer Python's standard library, pathlib, and scipy; do not use network access or external files. Return only the requested JSON object. Do not wrap code or CSV in Markdown fences."""


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    if value.get("record_purpose") != RECORD_PURPOSE:
        raise ValueError("every wall-mining record must carry the development purpose")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _call_haiku(index: int, count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = _prompt(index, count)
    session_id = str(uuid5(NAMESPACE_URL, f"wall-mining:{count}:{index}:{sha256_digest(prompt)}"))
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


def _resolved_procedures(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 0:
            module = node.module or ""
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{module}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = alias.name
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        resolved: str | None = None
        if isinstance(node.func, ast.Name):
            resolved = aliases.get(node.func.id)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            base = aliases.get(node.func.value.id)
            resolved = f"{base}.{node.func.attr}" if base is not None else None
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
        ):
            base = aliases.get(node.func.value.value.id)
            resolved = f"{base}.{node.func.value.attr}.{node.func.attr}" if base else None
        if resolved in _REGISTERED and resolved not in found:
            found.append(resolved)
    return tuple(found)


def _declared_unit(description: str, data: bytes) -> str | None:
    matches = [item.strip() for item in _UNIT_DECLARATION.findall(description)]
    if len(matches) != 1 or not matches[0]:
        return None
    try:
        header = next(csv.reader(data.decode("utf-8", errors="strict").splitlines()))
    except (UnicodeError, csv.Error, StopIteration):
        return None
    return matches[0] if matches[0] in header else None


def _context(
    source: str, data: bytes, unit_column: str | None, procedures: tuple[str, ...]
) -> FrozenInspectionContext:
    source_bytes = source.encode("utf-8")
    requirements = b"scipy==1.14.0\n"
    data_digest = sha256_digest(data)
    source_digest = sha256_digest(source_bytes)
    requirements_digest = sha256_digest(requirements)
    snapshot_digest = semantic_digest(
        {"source_digest": source_digest, "data_digest": data_digest, "purpose": RECORD_PURPOSE}
    )
    surface = RecordRef("publication_surface", "surface:wall-mining")
    artifact = RecordRef("artifact", "artifact:wall-mining-report")
    snapshot = RecordRef("repository_snapshot", "snapshot:wall-mining")
    source_file = RecordRef("file_record", "file:wall-mining-source")
    parser = RecordRef("parser_result", "parser:wall-mining-source")
    data_file = RecordRef("file_record", "file:wall-mining-data")
    data_identity = RecordRef("asset_identity", "asset:wall-mining-data")
    requirements_file = RecordRef("file_record", "file:wall-mining-requirements")
    requirements_identity = RecordRef("asset_identity", "asset:wall-mining-requirements")
    analysis = RecordRef("analysis", "analysis-v2:wall-mining")
    procedure = RecordRef("procedure", "procedure-v2:wall-mining")
    result = RecordRef("result", "result-v2:wall-mining")
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
        (analysis, {"analysis_id": analysis.record_id}),
        (
            procedure,
            {
                "procedure_id": procedure.record_id,
                **(
                    {"resolved_callable": procedures[0]}
                    if len(procedures) == 1
                    else {"resolved_callables": list(procedures)}
                ),
            },
        ),
        (result, {"result_id": result.record_id, "path": "results/report.md"}),
    ]
    if unit_column is not None and procedures:
        values.append(
            (
                RecordRef("human_method_authorization", "authorization-v2:wall-mining"),
                {
                    "record_type": "human_method_authorization",
                    "record_id": "authorization-v2:wall-mining",
                    "actor_id": "development-wall-mining-declaration-translator",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis.to_dict(),
                    "procedure_ref": procedure.to_dict(),
                    "independent_unit_definition_id": semantic_digest({"unit_column": unit_column}),
                    "authorized_key_columns": [unit_column],
                    "input_path": "data/input.csv",
                    "input_content_digest": data_digest,
                },
            )
        )
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
    run_root: Path, index: int, result: dict[str, Any], generation: dict[str, Any]
) -> dict[str, Any]:
    case_root = run_root / "cases" / f"{index + 1:04d}"
    source = str(result["analysis_py"])
    data = str(result["data_csv"]).encode("utf-8")
    description = str(result["data_description_md"])
    (case_root / "workflow").mkdir(parents=True)
    (case_root / "data").mkdir()
    (case_root / "workflow/analysis.py").write_text(source, encoding="utf-8")
    (case_root / "data/input.csv").write_bytes(data)
    (case_root / "data-description.md").write_text(description, encoding="utf-8")
    _write_json(case_root / "generation.json", generation)
    procedures = _resolved_procedures(source)
    unit_column = _declared_unit(description, data)
    if procedures and any(item not in V2_GROUP_PROCEDURES for item in procedures):
        if len(procedures) != 1 or not _TRIAL_DECLARATION.search(description):
            procedures = ()
    if len(procedures) > 1 and any(item not in V2_GROUP_PROCEDURES for item in procedures):
        procedures = ()
    translation: dict[str, Any] = {
        "record_type": "development_wall_mining_lock_translation",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "case_index": index,
        "role_information_used": False,
        "declared_unit_column": unit_column,
        "resolved_procedures": list(procedures),
        "translation_outcome": "lock-projected" if unit_column and procedures else "no-lock",
    }
    if unit_column and procedures:
        lock = build_dependence_v2_authorization_lock(
            case_id=f"case:wall-mining-{index + 1:04d}",
            snapshot_digest=semantic_digest(
                {"source": sha256_digest(source), "data": sha256_digest(data)}
            ),
            intake_recorded_at="1970-01-01T00:00:00Z",
            procedure=procedures[0] if len(procedures) == 1 else procedures,
            unit_column=unit_column,
            input_path="data/input.csv",
            input_content_digest=sha256_digest(data),
        )
        translation["lock_digest"] = lock["lock_digest"]
        translation["approved_projection_digest"] = lock["approval"]["approved_projection_digest"]
    translation["translation_digest"] = semantic_digest(translation)
    _write_json(case_root / "lock-translation.json", translation)
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(source, data, unit_column if procedures else None, procedures)
    )
    payload["record_purpose"] = RECORD_PURPOSE
    payload["measurement_authority"] = "none"
    shadow = {
        "record_type": "development_wall_mining_shadow_observation",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "case_index": index,
        "domain": str(result["domain"]),
        "lock_translation_outcome": translation["translation_outcome"],
        "shadow_payload": payload,
        "measurement_authority": "none",
    }
    shadow["observation_digest"] = semantic_digest(shadow)
    _write_json(case_root / "shadow-result.json", shadow)
    return shadow


def build_corpus(project_root: Path, count: int) -> Path:
    if count < 1:
        raise ValueError("count must be positive")
    if not CLAUDE_PINNED.is_file():
        raise FileNotFoundError(f"Claude CLI is missing: {CLAUDE_PINNED}")
    run_root = project_root / CORPUS_ROOT / f"run-{count}"
    if run_root.exists():
        raise FileExistsError(f"wall-mining run already exists: {run_root}")
    run_root.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENCY, count)) as executor:
        generated = list(executor.map(lambda index: _call_haiku(index, count), range(count)))
    observations = [
        _write_case(run_root, index, result, generation)
        for index, (result, generation) in enumerate(generated)
    ]
    frequencies: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    for observation in observations:
        payload = cast(dict[str, Any], observation["shadow_payload"])
        outcome = str(payload.get("outcome", "missing"))
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        for reason in payload.get("abstention_reasons", []):
            key = str(reason)
            frequencies[key] = frequencies.get(key, 0) + 1
    census = {
        "record_type": "development_wall_mining_census",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": f"run-{count}",
        "case_count": count,
        "model_alias": MODEL_ALIAS,
        "generation_calls": count,
        "maximum_generation_concurrency": MAX_CONCURRENCY,
        "outcome_frequencies": dict(sorted(outcomes.items())),
        "wall_frequencies": dict(sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))),
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
            for reason, frequency in census["wall_frequencies"].items()
        ],
        "",
        "Outcomes: "
        + ", ".join(f"`{key}` {value}" for key, value in census["outcome_frequencies"].items()),
        "",
    ]
    (run_root / "wall-frequency-census.md").write_text("\n".join(rows), encoding="utf-8")
    run_record = {
        "record_type": "development_wall_mining_run",
        "record_purpose": RECORD_PURPOSE,
        "non_measurement_notice": NON_MEASUREMENT,
        "run_name": f"run-{count}",
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
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    arguments = parser.parse_args()
    print(build_corpus(arguments.project_root.resolve(), arguments.count))


if __name__ == "__main__":
    main()
