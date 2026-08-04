from __future__ import annotations

import ast
import locale
import os
import re
import stat
import sys
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal, overload

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id

VERIFIER_VERSION = "1.0.0"
DERIVATION_VERSION = "1.0.0"
VALIDATION_VERSION = "1.0.0"

PYTHON_STATIC_MARKED_REPORT_PROFILE = "selected-result-profile:python-static-marked-report-v1"
_SELECTED_RESULT_PREFIX = "[selected-result]"
_PROFILE_MANIFEST: dict[str, Any] = {
    "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
    "profile_version": "1.0.0",
    "selected_result_grammar": "one-or-more-exact-prefixed-report-lines",
    "selected_result_prefix": _SELECTED_RESULT_PREFIX,
    "producer_grammar": "python-path-literal-write-text-v1",
    "operand_grammar": "finite-static-python-expression-evaluation-v1",
    "writer_scope": "unconditional-module-level-only",
    "writer_payload": "exact-retained-report-byte-equality-and-source-operand-required",
    "candidate_enumeration": "all-strict-utf8-python-files-in-complete-case-tree",
    "case_file_roles": "every-file-is-python-producer-selected-report-or-rederived-operand",
    "non_python_source_artifacts": "unsupported",
    "source_operand_grammar": "nonexecutable-nonshebang-ascii-lf-csv-or-tsv-v1",
    "selected_report_role": "nonexecutable-nonshebang-ascii-lf-md-or-txt-v1",
    "dynamic_or_unparsed_flow": "unsupported",
    "tree_budgets": "32-files-32-directories-64-entries-depth-8",
    "text_line_budget": "10000-lines-before-splitting",
    "module_statement_budget": "64-top-level-statements",
    "python_source_budget": "1048576-bytes-and-50000-ast-nodes",
    "python_source_encoding": "default-utf8-without-bom-or-pep263-cookie",
    "static_evaluation_budget": "100000-steps-10485760-value-bytes-4096-integer-bits",
}
_PROFILE_DIGEST = semantic_digest(_PROFILE_MANIFEST)
_POTENTIAL_OUTPUT_METHODS = {
    "dump",
    "save",
    "savefig",
    "to_csv",
    "to_json",
    "to_parquet",
    "write",
    "write_bytes",
    "write_text",
    "writelines",
}
_NON_PYTHON_SOURCE_SUFFIXES = {
    ".bash",
    ".c",
    ".cc",
    ".clj",
    ".cpp",
    ".cs",
    ".cwl",
    ".do",
    ".fish",
    ".fs",
    ".fsx",
    ".go",
    ".groovy",
    ".h",
    ".hpp",
    ".ipynb",
    ".java",
    ".jl",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".lua",
    ".m",
    ".nf",
    ".php",
    ".pl",
    ".pm",
    ".r",
    ".rb",
    ".rmd",
    ".rs",
    ".sas",
    ".scala",
    ".sh",
    ".smk",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".wdl",
    ".zsh",
}
_NON_PYTHON_SOURCE_NAMES = {
    "dockerfile",
    "jenkinsfile",
    "makefile",
    "nextflow.config",
    "snakefile",
}
_SOURCE_OPERAND_SUFFIXES = {".csv", ".tsv"}
_SELECTED_REPORT_SUFFIXES = {".md", ".txt"}
_RESERVED_PYTHON_BINDINGS = {"Path", "float", "int", "len", "str"}
_PYTHON_ENCODING_COOKIE = re.compile(rb"^[ \t\f]*\#.*?coding[:=][ \t]*[-_.a-zA-Z0-9]+")

MAX_CASE_FILES = 32
MAX_CASE_DIRECTORIES = 32
MAX_CASE_ENTRIES = 64
MAX_CASE_DEPTH = 8
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_CANDIDATE_BINDINGS = 16
MAX_TEXT_LINES = 10_000
MAX_PYTHON_SOURCE_BYTES = 1024 * 1024
MAX_PYTHON_AST_NODES = 50_000
MAX_STATIC_EVALUATION_STEPS = 100_000
MAX_STATIC_VALUE_BYTES = MAX_FILE_BYTES
MAX_STATIC_SEQUENCE_ITEMS = MAX_TEXT_LINES
MAX_STATIC_INTEGER_BITS = 4096
MAX_MODULE_STATEMENTS = 64

DerivationStatus = Literal[
    "one_selected_result_rederived",
    "ambiguous_selected_result",
    "insufficient_evidence",
    "unsupported_structure",
]
ValidationStatus = Literal[
    "verified_complete",
    "ambiguous_selected_result",
    "insufficient_evidence",
    "unsupported_structure",
]


class ProspectiveSelectedResultVerifierError(ValueError):
    """Raised when selected-result evidence is not closed and replayable."""


class _Unsupported(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class _Insufficient(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


@dataclass(frozen=True)
class _Writer:
    path: str
    start_line: int
    end_line: int
    source_paths: tuple[str, ...]


@dataclass
class _EvaluationBudget:
    steps: int = 0


def freeze_independent_selected_result_derivation(
    case_root: Path,
    spec: Mapping[str, Any],
    *,
    frozen_at: str,
) -> dict[str, Any]:
    """Independently enumerate one finite selected-result grammar from case bytes.

    The caller supplies only opaque case identity, operator identity, a frozen verifier profile,
    and the selected report path. Candidate bindings, author declarations, issue classes, labels,
    and detector results are not accepted as inputs.
    """

    value = deepcopy(dict(spec))
    _exact_keys(
        value,
        {
            "case_id",
            "validator_identity",
            "profile_id",
            "selected_report_path",
            "derived_at",
        },
        "independent selected-result derivation",
    )
    case_id = _case_id(value["case_id"])
    identity = _validator_identity(value["validator_identity"])
    profile_id = _single_line(value["profile_id"], "profile_id")
    if profile_id != PYTHON_STATIC_MARKED_REPORT_PROFILE:
        raise ProspectiveSelectedResultVerifierError(
            "Unsupported selected-result verifier profile."
        )
    selected_report = _relative_path(value["selected_report_path"], "selected_report_path")
    derived = _timestamp(_text(value["derived_at"], "derived_at"))
    frozen = _timestamp(frozen_at)
    if derived > frozen:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation cannot be frozen before it was completed."
        )

    retained_files, payloads, executable_paths = _inventory_case_tree(case_root)
    candidates: list[dict[str, Any]] = []
    status: DerivationStatus
    reasons: list[str]
    try:
        candidates = _derive_python_static_marked_report_bindings(
            selected_report,
            payloads,
            executable_paths,
        )
        if len(candidates) > MAX_CANDIDATE_BINDINGS:
            raise _Unsupported("selected_result_candidate_ceiling_exceeded")
        if len(candidates) == 1:
            status = "one_selected_result_rederived"
            reasons = ["one_selected_result_binding_rederived"]
        else:
            status = "ambiguous_selected_result"
            reasons = ["multiple_selected_result_bindings_rederived"]
    except _Unsupported as error:
        status = "unsupported_structure"
        reasons = [error.reason]
    except _Insufficient as error:
        status = "insufficient_evidence"
        reasons = [error.reason]

    receipts: dict[str, dict[str, Any]] = {}
    canonical_candidates = [
        _selected_result_binding(item, payloads=payloads, receipts=receipts) for item in candidates
    ]
    candidate_digests = [semantic_digest(item) for item in canonical_candidates]
    if len(set(candidate_digests)) != len(candidate_digests):
        raise ProspectiveSelectedResultVerifierError(
            "Independently derived selected-result candidates must be unique."
        )

    record: dict[str, Any] = {
        "artifact_kind": "prospective_selected_result_derivation",
        "derivation_version": DERIVATION_VERSION,
        "verifier_version": VERIFIER_VERSION,
        "profile_id": profile_id,
        "profile_digest": _PROFILE_DIGEST,
        "case_id": case_id,
        "validator_identity": identity,
        "selected_report_path": selected_report,
        "candidate_bindings": sorted(canonical_candidates, key=semantic_digest),
        "candidate_binding_digests": sorted(candidate_digests),
        "derivation_status": status,
        "reason_codes": reasons,
        "retained_files": retained_files,
        "case_tree_digest": semantic_digest(retained_files),
        "locator_receipts": sorted(
            receipts.values(),
            key=lambda item: (
                str(item["path"]),
                int(item["start_line"]),
                int(item["end_line"]),
                str(item["locator_digest"]),
            ),
        ),
        "implementation_lock": _implementation_lock(),
        "derived_at": _iso(derived),
        "frozen_at": _iso(frozen),
        "project_code_executed": False,
        "qualification_authority": "none_verifier_derivation_only",
    }
    record["derivation_digest"] = semantic_digest(record)
    return record


def revalidate_independent_selected_result_derivation(
    derivation: Mapping[str, Any], case_root: Path
) -> dict[str, Any]:
    """Rebuild a selected-result derivation from the retained case bytes."""

    current = validate_independent_selected_result_derivation(derivation)
    rebuilt = freeze_independent_selected_result_derivation(
        case_root,
        {
            "case_id": current["case_id"],
            "validator_identity": current["validator_identity"],
            "profile_id": current["profile_id"],
            "selected_report_path": current["selected_report_path"],
            "derived_at": current["derived_at"],
        },
        frozen_at=str(current["frozen_at"]),
    )
    if rebuilt != current:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation does not replay from the supplied case bytes."
        )
    return rebuilt


def validate_independent_selected_result_derivation(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the closed shape and internally replayable semantics of a derivation."""

    derivation = deepcopy(dict(value))
    expected = derivation.pop("derivation_digest", None)
    if expected != semantic_digest(derivation):
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation digest does not replay."
        )
    derivation["derivation_digest"] = expected
    _exact_keys(
        derivation,
        {
            "artifact_kind",
            "derivation_version",
            "verifier_version",
            "profile_id",
            "profile_digest",
            "case_id",
            "validator_identity",
            "selected_report_path",
            "candidate_bindings",
            "candidate_binding_digests",
            "derivation_status",
            "reason_codes",
            "retained_files",
            "case_tree_digest",
            "locator_receipts",
            "implementation_lock",
            "derived_at",
            "frozen_at",
            "project_code_executed",
            "qualification_authority",
            "derivation_digest",
        },
        "selected-result derivation artifact",
    )
    if (
        derivation["artifact_kind"] != "prospective_selected_result_derivation"
        or derivation["derivation_version"] != DERIVATION_VERSION
        or derivation["verifier_version"] != VERIFIER_VERSION
        or derivation["profile_id"] != PYTHON_STATIC_MARKED_REPORT_PROFILE
        or derivation["profile_digest"] != _PROFILE_DIGEST
        or derivation["qualification_authority"] != "none_verifier_derivation_only"
        or derivation["project_code_executed"] is not False
    ):
        raise ProspectiveSelectedResultVerifierError(
            "Unsupported selected-result derivation artifact."
        )
    if derivation["implementation_lock"] != _implementation_lock():
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result verifier implementation lock has drifted."
        )
    _case_id(derivation["case_id"])
    _validator_identity(derivation["validator_identity"])
    _relative_path(derivation["selected_report_path"], "selected_report_path")
    derived = _timestamp(_text(derivation["derived_at"], "derived_at"))
    frozen = _timestamp(_text(derivation["frozen_at"], "frozen_at"))
    if derived > frozen:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation chronology is invalid."
        )
    retained = _retained_files(derivation["retained_files"])
    if retained != derivation["retained_files"]:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result retained-file inventory is not canonical."
        )
    if derivation["case_tree_digest"] != semantic_digest(retained):
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result case-tree digest does not replay."
        )
    candidates = [
        _selected_result_binding(item)
        for item in _sequence(derivation["candidate_bindings"], "candidate_bindings")
    ]
    digests = sorted(semantic_digest(item) for item in candidates)
    if (
        candidates != derivation["candidate_bindings"]
        or digests != derivation["candidate_binding_digests"]
    ):
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result candidate bindings or digests do not replay."
        )
    _validate_status(candidates, derivation["derivation_status"], derivation["reason_codes"])
    _locator_receipts(derivation["locator_receipts"])
    return derivation


def freeze_selected_result_validation(
    case_root: Path,
    case_contract: Mapping[str, Any],
    derivation: Mapping[str, Any],
    *,
    declaration_revealed_at: str,
    compared_at: str,
) -> dict[str, Any]:
    """Compare a replayed prior blind derivation with one author declaration."""

    contract = _case_contract(case_contract)
    derived = revalidate_independent_selected_result_derivation(derivation, case_root)
    if derived["case_id"] != contract["case_id"]:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation and case-contract identities differ."
        )
    author = _mapping(contract["authorship"], "case-contract authorship")
    validator = _mapping(derived["validator_identity"], "validator_identity")
    if validator["validator_id"] == author.get("author_id") or validator["provider"] == author.get(
        "provider"
    ):
        raise ProspectiveSelectedResultVerifierError(
            "The selected-result validator must be independent of the case author."
        )

    revealed = _timestamp(declaration_revealed_at)
    compared = _timestamp(compared_at)
    derivation_frozen = _timestamp(str(derived["frozen_at"]))
    contract_frozen = _timestamp(str(contract["frozen_at"]))
    if revealed < derivation_frozen:
        raise ProspectiveSelectedResultVerifierError(
            "The author declaration was revealed before the blind derivation was frozen."
        )
    if revealed < contract_frozen:
        raise ProspectiveSelectedResultVerifierError(
            "The author declaration cannot be revealed before its contract was frozen."
        )
    if compared < revealed:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result comparison predates declaration reveal."
        )

    status, selected_digest, reasons = _comparison_status(contract, derived)
    record: dict[str, Any] = {
        "artifact_kind": "prospective_selected_result_validation",
        "validation_version": VALIDATION_VERSION,
        "verifier_version": VERIFIER_VERSION,
        "validator_id": validator["validator_id"],
        "provider": validator["provider"],
        "execution_context_id": validator["execution_context_id"],
        "identity_evidence_digest": validator["identity_evidence_digest"],
        "completed_at": _iso(compared),
        "case_contract_digest": contract["contract_digest"],
        "status": status,
        "selected_result_binding_digest": selected_digest,
        "case_tree_digest": derived["case_tree_digest"],
        "derivation_digest": derived["derivation_digest"],
        "independent_derivation": derived,
        "declaration_revealed_at": _iso(revealed),
        "reason_codes": reasons,
        "qualification_authority": "none_selected_result_validation_only",
    }
    record["validation_digest"] = semantic_digest(record)
    return record


def validate_selected_result_validation(
    value: Mapping[str, Any], *, case_root: Path, case_contract: Mapping[str, Any]
) -> dict[str, Any]:
    """Replay a validation from its case bytes, derivation, and contract."""

    current = deepcopy(dict(value))
    expected = current.pop("validation_digest", None)
    if expected != semantic_digest(current):
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result validation digest does not replay."
        )
    current["validation_digest"] = expected
    if (
        current.get("artifact_kind") != "prospective_selected_result_validation"
        or current.get("validation_version") != VALIDATION_VERSION
        or current.get("verifier_version") != VERIFIER_VERSION
        or current.get("qualification_authority") != "none_selected_result_validation_only"
    ):
        raise ProspectiveSelectedResultVerifierError(
            "Unsupported selected-result validation artifact."
        )
    derivation = _mapping(current.get("independent_derivation"), "independent_derivation")
    rebuilt = freeze_selected_result_validation(
        case_root,
        case_contract,
        derivation,
        declaration_revealed_at=str(current.get("declaration_revealed_at", "")),
        compared_at=str(current.get("completed_at", "")),
    )
    if rebuilt != current:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result validation semantics do not replay."
        )
    return current


def _derive_python_static_marked_report_bindings(
    selected_report: str,
    payloads: Mapping[str, bytes],
    executable_paths: set[str],
) -> list[dict[str, Any]]:
    if os.linesep != "\n" or not _runtime_encoding_preserves_ascii():
        raise _Unsupported("text_io_runtime_unsupported")
    report_payload = payloads.get(selected_report)
    if report_payload is None:
        raise _Insufficient("selected_report_missing")
    if (
        PurePosixPath(selected_report).suffix.lower() not in _SELECTED_REPORT_SUFFIXES
        or selected_report in executable_paths
        or report_payload.startswith(b"#!")
        or b"\x00" in report_payload
    ):
        raise _Unsupported("unsupported_selected_report_role")
    report_lines = _bounded_splitlines(
        _strict_ascii_lf_text(report_payload),
        keepends=True,
    )
    if not report_lines:
        raise _Insufficient("selected_report_empty")
    result_lines: list[int] = []
    for index, line in enumerate(report_lines, start=1):
        if not line.strip().startswith(_SELECTED_RESULT_PREFIX):
            continue
        if len(result_lines) == MAX_CANDIDATE_BINDINGS:
            raise _Unsupported("selected_result_candidate_ceiling_exceeded")
        result_lines.append(index)
    if not result_lines:
        raise _Insufficient("selected_result_marker_missing")

    writers: list[_Writer] = []
    unsupported_source_paths = sorted(
        path
        for path in payloads
        if not path.endswith(".py")
        and (
            PurePosixPath(path).suffix.lower() in _NON_PYTHON_SOURCE_SUFFIXES
            or PurePosixPath(path).name.lower() in _NON_PYTHON_SOURCE_NAMES
        )
    )
    if unsupported_source_paths:
        raise _Unsupported("unsupported_non_python_source_artifact")
    python_paths = sorted(path for path in payloads if path.endswith(".py"))
    if not python_paths:
        raise _Unsupported("python_source_absent")
    for path in python_paths:
        if len(payloads[path]) > MAX_PYTHON_SOURCE_BYTES:
            raise _Unsupported("python_source_byte_ceiling_exceeded")
        text = _strict_python_source(payloads[path], path)
        _bounded_line_count(text)
        try:
            tree = ast.parse(text, filename=path)
        except (MemoryError, RecursionError, SyntaxError, ValueError) as error:
            raise _Unsupported("python_source_parse_failed") from error
        if sum(1 for _ in ast.walk(tree)) > MAX_PYTHON_AST_NODES:
            raise _Unsupported("python_ast_node_ceiling_exceeded")
        found = _python_writers(path, tree, selected_report, payloads)
        if not found:
            raise _Unsupported("python_module_without_selected_report_writer")
        writers.extend(found)
        if len(writers) > MAX_CANDIDATE_BINDINGS:
            raise _Unsupported("selected_result_candidate_ceiling_exceeded")
    if not writers:
        raise _Insufficient("selected_report_writer_not_rederived")
    if len(writers) > MAX_CANDIDATE_BINDINGS // len(result_lines):
        raise _Unsupported("selected_result_candidate_ceiling_exceeded")

    source_paths = {source for writer in writers for source in writer.source_paths}
    for source_path in source_paths:
        source_payload = payloads[source_path]
        if (
            PurePosixPath(source_path).suffix.lower() not in _SOURCE_OPERAND_SUFFIXES
            or source_path in executable_paths
            or source_payload.startswith(b"#!")
            or b"\x00" in source_payload
        ):
            raise _Unsupported("unsupported_source_operand_role")
        _bounded_line_count(_strict_ascii_lf_text(source_payload))
    classified_paths = {*python_paths, selected_report, *source_paths}
    if set(payloads) != classified_paths:
        raise _Unsupported("unclassified_case_artifact")

    producer_locators = [
        _locator_value(
            path=item.path, payload=payloads[item.path], start=item.start_line, end=item.end_line
        )
        for item in writers
    ]
    candidates: list[dict[str, Any]] = []
    for writer, producer in zip(writers, producer_locators, strict=True):
        sources: list[dict[str, Any]] = []
        for source_path in writer.source_paths:
            source_lines = _bounded_splitlines(
                _strict_text(payloads[source_path], source_path),
                keepends=True,
            )
            if not source_lines:
                raise _Insufficient("selected_report_source_operand_empty")
            sources.append(
                {
                    "operand_id": stable_id(
                        "operand", source_path, sha256_digest(payloads[source_path])
                    ),
                    "record_ref": {
                        "record_type": "file_record",
                        "record_id": stable_id(
                            "file", source_path, sha256_digest(payloads[source_path])
                        ),
                    },
                    "source_locator": _locator_value(
                        path=source_path,
                        payload=payloads[source_path],
                        start=1,
                        end=len(source_lines),
                    ),
                }
            )
        for result_line in result_lines:
            candidates.append(
                {
                    "binding_profile": "exact_selected_report_result_static_producer_v1",
                    "selection_status": "one_selected_result",
                    "report_locator": _locator_value(
                        path=selected_report,
                        payload=report_payload,
                        start=1,
                        end=len(report_lines),
                    ),
                    "result_locator": _locator_value(
                        path=selected_report,
                        payload=report_payload,
                        start=result_line,
                        end=result_line,
                    ),
                    "producer_locator": producer,
                    "source_operands": sources,
                    "alternative_producer_locators": [
                        item for item in producer_locators if item != producer
                    ],
                    "declared_dynamic_selection": False,
                }
            )
    return sorted(candidates, key=semantic_digest)


def _python_writers(
    source_path: str,
    tree: ast.Module,
    selected_report: str,
    payloads: Mapping[str, bytes],
) -> list[_Writer]:
    parents = _parent_map(tree)
    _validate_closed_python_calls(tree)
    writers: list[_Writer] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and any(keyword.arg == "file" for keyword in node.keywords)
        ):
            raise _Unsupported("unsupported_possible_report_writer")
        if not isinstance(node.func, ast.Attribute):
            if isinstance(node.func, ast.Name) and node.func.id == "Path":
                continue
            if _call_contains_path_literal(node, selected_report):
                raise _Unsupported("unsupported_possible_report_writer")
            continue
        if node.func.attr not in {"write_text", "write_bytes"}:
            if node.func.attr in _POTENTIAL_OUTPUT_METHODS or _call_contains_path_literal(
                node, selected_report
            ):
                raise _Unsupported("unsupported_possible_report_writer")
            continue
        target = _resolve_path_expression(node.func.value)
        if target is None:
            raise _Unsupported("dynamic_or_unsupported_report_writer")
        if target != selected_report:
            continue
        if len(node.args) != 1 or node.keywords:
            raise _Unsupported("unsupported_selected_report_writer_signature")
        environment, budget = _validate_straight_line_module(tree, node, payloads)
        if _enclosing_function(node, parents) is not None or any(
            isinstance(parent, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match))
            for parent in _ancestors(node, parents)
        ):
            raise _Unsupported("conditional_or_nested_selected_report_writer")
        rendered, sources = _evaluate_static_expression(
            node.args[0],
            payloads,
            environment,
            budget,
        )
        if not sources:
            raise _Insufficient("selected_report_source_operand_not_rederived")
        if node.func.attr == "write_text":
            if not isinstance(rendered, str):
                raise _Unsupported("selected_report_writer_value_type_unsupported")
            try:
                rendered_bytes = rendered.encode("utf-8")
            except UnicodeEncodeError as error:
                raise _Unsupported("selected_report_text_not_utf8_encodable") from error
        else:
            if not isinstance(rendered, bytes):
                raise _Unsupported("selected_report_writer_value_type_unsupported")
            rendered_bytes = rendered
        if rendered_bytes != payloads[selected_report]:
            raise _Insufficient("selected_report_bytes_do_not_match_static_writer")
        for path in sources:
            if path == selected_report:
                raise _Unsupported("selected_report_self_dependency")
            if path not in payloads:
                raise _Insufficient("selected_report_source_operand_missing")
        writers.append(
            _Writer(
                path=source_path,
                start_line=int(node.lineno),
                end_line=int(node.end_lineno or node.lineno),
                source_paths=tuple(sorted(sources)),
            )
        )
    return writers


def _call_contains_path_literal(node: ast.Call, path: str) -> bool:
    return any(isinstance(child, ast.Constant) and child.value == path for child in ast.walk(node))


def _validate_closed_python_calls(tree: ast.Module) -> None:
    allowed_names = {"Path", "float", "int", "len", "str"}
    allowed_attributes = {
        "lstrip",
        "read_bytes",
        "read_text",
        "rstrip",
        "splitlines",
        "strip",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in allowed_names:
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in allowed_attributes:
            continue
        raise _Unsupported("opaque_or_unallowlisted_python_call")


def _validate_straight_line_module(
    tree: ast.Module,
    writer: ast.Call,
    payloads: Mapping[str, bytes],
) -> tuple[dict[str, tuple[_StaticValue, frozenset[str]]], _EvaluationBudget]:
    if len(tree.body) > MAX_MODULE_STATEMENTS:
        raise _Unsupported("python_module_statement_ceiling_exceeded")
    writer_statements = [
        (index, statement)
        for index, statement in enumerate(tree.body)
        if any(node is writer for node in ast.walk(statement))
    ]
    if len(writer_statements) != 1:
        raise _Unsupported("non_straight_line_module_statement")
    writer_index, writer_statement = writer_statements[0]
    if not (isinstance(writer_statement, ast.Expr) and writer_statement.value is writer):
        raise _Unsupported("non_straight_line_module_statement")
    path_import_count = 0
    environment: dict[str, tuple[_StaticValue, frozenset[str]]] = {}
    budget = _EvaluationBudget()
    for index, statement in enumerate(tree.body):
        if index > writer_index:
            raise _Unsupported("non_straight_line_module_statement")
        if isinstance(statement, ast.ImportFrom):
            if (
                statement.module != "pathlib"
                or statement.level != 0
                or len(statement.names) != 1
                or statement.names[0].name != "Path"
                or statement.names[0].asname is not None
                or index != 0
                or index >= writer_index
            ):
                raise _Unsupported("unsupported_python_import_binding")
            path_import_count += 1
            continue
        if isinstance(statement, ast.Import):
            raise _Unsupported("non_straight_line_module_statement")
        target_names: list[str] = []
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if not isinstance(target, ast.Name):
                    raise _Unsupported("non_straight_line_module_statement")
                target_names.append(target.id)
            if not target_names:
                raise _Unsupported("non_straight_line_module_statement")
            if any(name in _RESERVED_PYTHON_BINDINGS for name in target_names):
                raise _Unsupported("reserved_python_binding_reassigned")
            value = statement.value
        elif isinstance(statement, ast.AnnAssign):
            if not isinstance(statement.target, ast.Name) or statement.value is None:
                raise _Unsupported("non_straight_line_module_statement")
            if statement.target.id in _RESERVED_PYTHON_BINDINGS:
                raise _Unsupported("reserved_python_binding_reassigned")
            target_names.append(statement.target.id)
            value = statement.value
        elif index == writer_index and statement is writer_statement:
            continue
        else:
            raise _Unsupported("non_straight_line_module_statement")
        evaluated, sources = _evaluate_static_expression(value, payloads, environment, budget)
        for name in target_names:
            environment[name] = (evaluated, frozenset(sources))
    if path_import_count != 1:
        raise _Unsupported("unsupported_python_import_binding")
    return environment, budget


_StaticValue = str | bytes | int | float | list[Any] | tuple[Any, ...]


def _evaluate_static_expression(
    expression: ast.AST,
    payloads: Mapping[str, bytes],
    environment: Mapping[str, tuple[_StaticValue, frozenset[str]]],
    budget: _EvaluationBudget,
) -> tuple[_StaticValue, set[str]]:
    sources: set[str] = set()

    def bounded(value: _StaticValue) -> _StaticValue:
        if isinstance(value, str):
            try:
                byte_length = len(value.encode("utf-8"))
            except UnicodeEncodeError as error:
                raise _Unsupported("selected_report_text_not_utf8_encodable") from error
            if byte_length > MAX_STATIC_VALUE_BYTES:
                raise _Unsupported("static_value_byte_ceiling_exceeded")
        elif isinstance(value, bytes):
            if len(value) > MAX_STATIC_VALUE_BYTES:
                raise _Unsupported("static_value_byte_ceiling_exceeded")
        elif isinstance(value, (list, tuple)):
            if len(value) > MAX_STATIC_SEQUENCE_ITEMS:
                raise _Unsupported("static_sequence_item_ceiling_exceeded")
        elif isinstance(value, int) and value.bit_length() > MAX_STATIC_INTEGER_BITS:
            raise _Unsupported("static_integer_bit_ceiling_exceeded")
        return value

    def evaluate(node: ast.AST) -> _StaticValue:
        budget.steps += 1
        if budget.steps > MAX_STATIC_EVALUATION_STEPS:
            raise _Unsupported("static_evaluation_step_ceiling_exceeded")
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes, int, float)):
            return bounded(node.value)
        if isinstance(node, ast.Name):
            resolved = environment.get(node.id)
            if resolved is None:
                raise _Unsupported("unsupported_selected_report_dependency_flow")
            value, inherited_sources = resolved
            sources.update(inherited_sources)
            return value
        if isinstance(node, ast.JoinedStr):
            parts = [evaluate(item) for item in node.values]
            if any(not isinstance(item, str) for item in parts):
                raise _Unsupported("unsupported_formatted_selected_result")
            text_parts = [item for item in parts if isinstance(item, str)]
            _preflight_static_concatenation(text_parts)
            return bounded("".join(text_parts))
        if isinstance(node, ast.FormattedValue):
            if node.format_spec is not None or node.conversion not in {-1, 115}:
                raise _Unsupported("unsupported_formatted_selected_result")
            value = evaluate(node.value)
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                raise _Unsupported("unsupported_formatted_selected_result")
            return bounded(value if isinstance(value, str) else str(value))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(left, str) and isinstance(right, str):
                _preflight_static_concatenation((left, right))
                return bounded(left + right)
            if isinstance(left, bytes) and isinstance(right, bytes):
                _preflight_static_concatenation((left, right))
                return bounded(left + right)
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return bounded(left + right)
            raise _Unsupported("unsupported_selected_report_addition")
        if isinstance(node, ast.Subscript):
            value = evaluate(node.value)
            index = evaluate(node.slice)
            if not isinstance(index, int) or not isinstance(value, (str, bytes, list, tuple)):
                raise _Unsupported("unsupported_selected_report_subscript")
            try:
                return bounded(value[index])
            except IndexError as error:
                raise _Insufficient("selected_report_subscript_out_of_range") from error
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                if method in {"read_text", "read_bytes"}:
                    path = _direct_path_call(node.func.value)
                    if path is None or node.args or node.keywords:
                        raise _Unsupported("unsupported_static_source_read")
                    normalized = _relative_path(path, "source input path")
                    payload = payloads.get(normalized)
                    if payload is None:
                        raise _Insufficient("selected_report_source_operand_missing")
                    sources.add(normalized)
                    return bounded(
                        _strict_ascii_lf_text(payload) if method == "read_text" else payload
                    )
                receiver = evaluate(node.func.value)
                arguments = [evaluate(item) for item in node.args]
                if node.keywords:
                    raise _Unsupported("unsupported_selected_report_keyword_argument")
                if method == "splitlines" and not arguments and isinstance(receiver, (str, bytes)):
                    return bounded(list(_bounded_splitlines(receiver, keepends=False)))
                if (
                    method in {"strip", "lstrip", "rstrip"}
                    and not arguments
                    and isinstance(receiver, (str, bytes))
                ):
                    if method == "strip":
                        return bounded(receiver.strip())
                    if method == "lstrip":
                        return bounded(receiver.lstrip())
                    return bounded(receiver.rstrip())
                raise _Unsupported("unsupported_selected_report_method")
            if isinstance(node.func, ast.Name) and len(node.args) == 1 and not node.keywords:
                value = evaluate(node.args[0])
                if node.func.id == "str":
                    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                        raise _Unsupported("unsupported_selected_report_call")
                    return bounded(value if isinstance(value, str) else str(value))
                if node.func.id == "int" and isinstance(value, (str, int, float)):
                    try:
                        return bounded(int(value))
                    except (ValueError, OverflowError) as error:
                        raise _Insufficient("static_numeric_conversion_failed") from error
                if node.func.id == "float" and isinstance(value, (str, int, float)):
                    try:
                        return bounded(float(value))
                    except (ValueError, OverflowError) as error:
                        raise _Insufficient("static_numeric_conversion_failed") from error
                if node.func.id == "len" and isinstance(value, (str, bytes, list, tuple)):
                    return bounded(len(value))
            raise _Unsupported("unsupported_selected_report_call")
        raise _Unsupported("unsupported_selected_report_expression")

    return evaluate(expression), sources


def _preflight_static_concatenation(values: Sequence[str] | Sequence[bytes]) -> None:
    total = 0
    for value in values:
        length = len(value) if isinstance(value, bytes) else len(value.encode("utf-8"))
        if length > MAX_STATIC_VALUE_BYTES - total:
            raise _Unsupported("static_value_byte_ceiling_exceeded")
        total += length


def _resolve_path_expression(expression: ast.AST) -> str | None:
    direct = _direct_path_call(expression)
    if direct is not None:
        try:
            return _relative_path(direct, "writer target path")
        except ProspectiveSelectedResultVerifierError:
            return None
    return None


def _direct_path_call(expression: ast.AST) -> str | None:
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "Path"
        and len(expression.args) == 1
        and not expression.keywords
        and isinstance(expression.args[0], ast.Constant)
        and isinstance(expression.args[0].value, str)
    ):
        return expression.args[0].value
    return None


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _ancestors(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> list[ast.AST]:
    ancestors: list[ast.AST] = []
    current = node
    while current in parents:
        current = parents[current]
        ancestors.append(current)
    return ancestors


def _enclosing_function(
    node: ast.AST, parents: Mapping[ast.AST, ast.AST]
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def _comparison_status(
    contract: Mapping[str, Any], derivation: Mapping[str, Any]
) -> tuple[ValidationStatus, str | None, list[str]]:
    status = str(derivation["derivation_status"])
    if status == "unsupported_structure":
        return "unsupported_structure", None, list(derivation["reason_codes"])
    if status == "insufficient_evidence":
        return "insufficient_evidence", None, list(derivation["reason_codes"])
    if status == "ambiguous_selected_result":
        return "ambiguous_selected_result", None, list(derivation["reason_codes"])
    candidates = _sequence(derivation["candidate_bindings"], "candidate_bindings")
    if len(candidates) != 1:
        raise ProspectiveSelectedResultVerifierError(
            "A complete selected-result derivation must contain exactly one binding."
        )
    candidate = _selected_result_binding(candidates[0])
    declared = _selected_result_binding(contract["selected_result_binding"])
    declared_digest = str(contract["selected_result_binding_digest"])
    if candidate != declared or semantic_digest(candidate) != declared_digest:
        return (
            "insufficient_evidence",
            None,
            ["independent_binding_differs_from_author_declaration"],
        )
    return "verified_complete", declared_digest, ["exact_independent_binding_match"]


def _validate_status(candidates: list[dict[str, Any]], status: Any, reasons: Any) -> None:
    reason_values = [
        _single_line(item, "reason code") for item in _sequence(reasons, "reason_codes")
    ]
    if len(reason_values) != 1:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation requires one closed reason code."
        )
    expected: tuple[str, str]
    if len(candidates) == 1:
        expected = ("one_selected_result_rederived", "one_selected_result_binding_rederived")
    elif len(candidates) > 1:
        expected = ("ambiguous_selected_result", "multiple_selected_result_bindings_rederived")
    elif status == "unsupported_structure":
        expected = ("unsupported_structure", reason_values[0])
    else:
        expected = ("insufficient_evidence", reason_values[0])
    if (status, reason_values[0]) != expected:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result derivation status does not match its candidates."
        )


def _inventory_case_tree(
    case_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, bytes], set[str]]:
    if case_root.is_symlink():
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result case root cannot be a symbolic link."
        )
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        root_descriptor = os.open(case_root, directory_flags)
    except OSError as error:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result case root cannot be opened as a non-symlink directory."
        ) from error
    files: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    executable_paths: set[str] = set()
    total = 0
    directory_count = 1
    entry_count = 0

    def scan(directory_descriptor: int, prefix: PurePosixPath, depth: int) -> None:
        nonlocal directory_count, entry_count, total
        if depth > MAX_CASE_DEPTH:
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case tree exceeds the finite depth ceiling."
            )
        before = os.fstat(directory_descriptor)
        if not stat.S_ISDIR(before.st_mode):
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case entry is not a directory."
            )
        try:
            names = sorted(os.listdir(directory_descriptor))
        except OSError as error:
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case tree cannot be enumerated."
            ) from error
        for name in names:
            entry_count += 1
            if entry_count > MAX_CASE_ENTRIES:
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case tree exceeds the finite entry-count ceiling."
                )
            try:
                entry = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            except OSError as error:
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case entry changed during enumeration."
                ) from error
            if stat.S_ISLNK(entry.st_mode):
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case trees cannot contain symbolic links."
                )
            relative = (prefix / name).as_posix()
            _relative_path(relative, "case file path")
            if stat.S_ISDIR(entry.st_mode):
                directory_count += 1
                if directory_count > MAX_CASE_DIRECTORIES:
                    raise ProspectiveSelectedResultVerifierError(
                        "Selected-result case tree exceeds the finite directory-count ceiling."
                    )
                try:
                    child_descriptor = os.open(
                        name,
                        directory_flags,
                        dir_fd=directory_descriptor,
                    )
                except OSError as error:
                    raise ProspectiveSelectedResultVerifierError(
                        "Selected-result child directory cannot be opened safely."
                    ) from error
                try:
                    opened = os.fstat(child_descriptor)
                    if (opened.st_dev, opened.st_ino) != (entry.st_dev, entry.st_ino):
                        raise ProspectiveSelectedResultVerifierError(
                            "Selected-result child directory changed before traversal."
                        )
                    scan(child_descriptor, prefix / name, depth + 1)
                finally:
                    os.close(child_descriptor)
                continue
            if not stat.S_ISREG(entry.st_mode):
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case trees may contain only regular files."
                )
            payload = _read_stable_regular_file(
                name,
                directory_descriptor=directory_descriptor,
                expected=entry,
            )
            if len(payload) > MAX_FILE_BYTES:
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case file exceeds the finite byte ceiling."
                )
            total += len(payload)
            if total > MAX_TOTAL_BYTES:
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case tree exceeds the finite total-byte ceiling."
                )
            payloads[relative] = payload
            if entry.st_mode & 0o111:
                executable_paths.add(relative)
            files.append(
                {
                    "path": relative,
                    "content_digest": sha256_digest(payload),
                    "byte_length": len(payload),
                    "executable": bool(entry.st_mode & 0o111),
                }
            )
            if len(files) > MAX_CASE_FILES:
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case tree exceeds the finite file-count ceiling."
                )
        after = os.fstat(directory_descriptor)
        if _stat_fingerprint(before) != _stat_fingerprint(after):
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case tree changed while it was being read."
            )

    try:
        scan(root_descriptor, PurePosixPath(), 0)
        if not files:
            raise ProspectiveSelectedResultVerifierError("Selected-result case tree is empty.")
        return files, payloads, executable_paths
    finally:
        os.close(root_descriptor)


def _read_stable_regular_file(
    name: str,
    *,
    directory_descriptor: int,
    expected: os.stat_result,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except OSError as error:
        raise ProspectiveSelectedResultVerifierError(
            "Selected-result case file cannot be opened safely."
        ) from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case entry is not a regular file."
            )
        if _stat_fingerprint(before) != _stat_fingerprint(expected):
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case file changed before it was read."
            )
        if before.st_size > MAX_FILE_BYTES:
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case file exceeds the finite byte ceiling."
            )
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, MAX_FILE_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_FILE_BYTES:
                raise ProspectiveSelectedResultVerifierError(
                    "Selected-result case file exceeds the finite byte ceiling."
                )
        after = os.fstat(descriptor)
        if _stat_fingerprint(before) != _stat_fingerprint(after):
            raise ProspectiveSelectedResultVerifierError(
                "Selected-result case file changed while it was being read."
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _stat_fingerprint(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _retained_files(value: Any) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for item in _sequence(value, "retained_files"):
        record = _mapping(item, "retained file")
        _exact_keys(
            record,
            {"path", "content_digest", "byte_length", "executable"},
            "retained file",
        )
        path = _relative_path(record["path"], "retained file path")
        digest = _digest(record["content_digest"], "retained file digest")
        length = record["byte_length"]
        if not isinstance(length, int) or isinstance(length, bool) or length < 0:
            raise ProspectiveSelectedResultVerifierError("Retained file byte length is invalid.")
        executable = record["executable"]
        if not isinstance(executable, bool):
            raise ProspectiveSelectedResultVerifierError(
                "Retained file executable flag is invalid."
            )
        files.append(
            {
                "path": path,
                "content_digest": digest,
                "byte_length": length,
                "executable": executable,
            }
        )
    if len(files) > MAX_CASE_FILES or len({item["path"] for item in files}) != len(files):
        raise ProspectiveSelectedResultVerifierError(
            "Retained file inventory is not finite and unique."
        )
    return sorted(files, key=lambda item: str(item["path"]))


def _locator_receipts(value: Any) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for item in _sequence(value, "locator_receipts"):
        receipt = _mapping(item, "locator receipt")
        _exact_keys(
            receipt,
            {"path", "content_digest", "start_line", "end_line", "locator_digest", "span_digest"},
            "locator receipt",
        )
        locator = {
            key: receipt[key] for key in ("path", "content_digest", "start_line", "end_line")
        }
        canonical = _locator(locator, "locator receipt", payloads=None, receipts=None)
        if receipt["locator_digest"] != semantic_digest(canonical):
            raise ProspectiveSelectedResultVerifierError("Locator receipt digest does not replay.")
        _digest(receipt["span_digest"], "locator receipt span_digest")
        receipts.append(receipt)
    if len({str(item["locator_digest"]) for item in receipts}) != len(receipts):
        raise ProspectiveSelectedResultVerifierError("Locator receipts must be unique.")
    return receipts


def _selected_result_binding(
    value: Any,
    *,
    payloads: Mapping[str, bytes] | None = None,
    receipts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    binding = deepcopy(_mapping(value, "selected_result_binding"))
    _exact_keys(
        binding,
        {
            "binding_profile",
            "selection_status",
            "report_locator",
            "result_locator",
            "producer_locator",
            "source_operands",
            "alternative_producer_locators",
            "declared_dynamic_selection",
        },
        "selected_result_binding",
    )
    if binding["binding_profile"] != "exact_selected_report_result_static_producer_v1":
        raise ProspectiveSelectedResultVerifierError("Unsupported selected-result binding profile.")
    if binding["selection_status"] != "one_selected_result":
        raise ProspectiveSelectedResultVerifierError("One selected result must be derived exactly.")
    if binding["declared_dynamic_selection"] is not False:
        raise ProspectiveSelectedResultVerifierError(
            "Dynamic selected-result paths are unsupported."
        )
    report = _locator(
        binding["report_locator"], "report_locator", payloads=payloads, receipts=receipts
    )
    result = _locator(
        binding["result_locator"], "result_locator", payloads=payloads, receipts=receipts
    )
    producer = _locator(
        binding["producer_locator"], "producer_locator", payloads=payloads, receipts=receipts
    )
    if report["path"] != result["path"] or report["content_digest"] != result["content_digest"]:
        raise ProspectiveSelectedResultVerifierError(
            "Selected result must be inside the exact selected report bytes."
        )
    if int(result["start_line"]) < int(report["start_line"]) or int(result["end_line"]) > int(
        report["end_line"]
    ):
        raise ProspectiveSelectedResultVerifierError(
            "Selected result must be contained inside the selected report span."
        )
    operands = [
        _source_operand(item, payloads=payloads, receipts=receipts)
        for item in _sequence(binding["source_operands"], "source_operands")
    ]
    if not operands:
        raise ProspectiveSelectedResultVerifierError("Selected result requires source operands.")
    if len({str(item["operand_id"]) for item in operands}) != len(operands):
        raise ProspectiveSelectedResultVerifierError("Source operand identities must be unique.")
    alternatives = [
        _locator(
            item,
            "alternative_producer_locator",
            payloads=payloads,
            receipts=receipts,
        )
        for item in _sequence(
            binding["alternative_producer_locators"], "alternative_producer_locators"
        )
    ]
    if any(item == producer for item in alternatives):
        raise ProspectiveSelectedResultVerifierError(
            "Selected producer cannot also be an alternative producer."
        )
    if len({semantic_digest(item) for item in alternatives}) != len(alternatives):
        raise ProspectiveSelectedResultVerifierError(
            "Alternative producer locators must be unique."
        )
    return {
        **binding,
        "report_locator": report,
        "result_locator": result,
        "producer_locator": producer,
        "source_operands": sorted(operands, key=lambda item: str(item["operand_id"])),
        "alternative_producer_locators": sorted(
            alternatives,
            key=lambda item: (
                str(item["path"]),
                int(item["start_line"]),
                int(item["end_line"]),
                str(item["content_digest"]),
            ),
        ),
    }


def _source_operand(
    value: Any,
    *,
    payloads: Mapping[str, bytes] | None,
    receipts: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    operand = deepcopy(_mapping(value, "source operand"))
    _exact_keys(operand, {"operand_id", "record_ref", "source_locator"}, "source operand")
    _text(operand["operand_id"], "operand_id")
    record_ref = deepcopy(_mapping(operand["record_ref"], "source operand record_ref"))
    _exact_keys(record_ref, {"record_type", "record_id"}, "source operand record_ref")
    _text(record_ref["record_type"], "source operand record_type")
    _text(record_ref["record_id"], "source operand record_id")
    return {
        **operand,
        "record_ref": record_ref,
        "source_locator": _locator(
            operand["source_locator"],
            "source operand locator",
            payloads=payloads,
            receipts=receipts,
        ),
    }


def _locator_value(*, path: str, payload: bytes, start: int, end: int) -> dict[str, Any]:
    return {
        "path": path,
        "content_digest": sha256_digest(payload),
        "start_line": start,
        "end_line": end,
    }


def _locator(
    value: Any,
    label: str,
    *,
    payloads: Mapping[str, bytes] | None,
    receipts: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    locator = deepcopy(_mapping(value, label))
    _exact_keys(locator, {"path", "content_digest", "start_line", "end_line"}, label)
    path = _relative_path(locator["path"], f"{label} path")
    digest = _digest(locator["content_digest"], f"{label} content_digest")
    start = locator["start_line"]
    end = locator["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise ProspectiveSelectedResultVerifierError(f"{label} start_line is invalid.")
    if not isinstance(end, int) or isinstance(end, bool) or end < start:
        raise ProspectiveSelectedResultVerifierError(f"{label} end_line is invalid.")
    normalized = {
        "path": path,
        "content_digest": digest,
        "start_line": start,
        "end_line": end,
    }
    if payloads is not None:
        payload = payloads.get(path)
        if payload is None:
            raise ProspectiveSelectedResultVerifierError(
                f"{label} does not resolve to a retained case file."
            )
        if sha256_digest(payload) != digest:
            raise ProspectiveSelectedResultVerifierError(f"{label} content digest does not match.")
        text = _strict_text(payload, path)
        lines = _bounded_splitlines(text, keepends=True)
        if end > len(lines):
            raise ProspectiveSelectedResultVerifierError(f"{label} line span exceeds the file.")
        if receipts is None:
            raise ProspectiveSelectedResultVerifierError("Locator receipt collector is absent.")
        locator_digest = semantic_digest(normalized)
        receipts[locator_digest] = {
            **normalized,
            "locator_digest": locator_digest,
            "span_digest": sha256_digest("".join(lines[start - 1 : end]).encode("utf-8")),
        }
    return normalized


def _strict_text(payload: bytes, label: str) -> str:
    try:
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _Unsupported("non_utf8_selected_result_evidence") from error


def _strict_python_source(payload: bytes, label: str) -> str:
    first_two_lines = payload.split(b"\n", maxsplit=2)[:2]
    if payload.startswith(b"\xef\xbb\xbf") or any(
        _PYTHON_ENCODING_COOKIE.match(line) for line in first_two_lines
    ):
        raise _Unsupported("unsupported_python_encoding_declaration")
    return _strict_text(payload, label)


def _strict_ascii_lf_text(payload: bytes) -> str:
    if b"\r" in payload:
        raise _Unsupported("non_lf_normalized_text_evidence")
    try:
        return payload.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise _Unsupported("non_ascii_text_evidence") from error


def _runtime_encoding_preserves_ascii() -> bool:
    encoding = locale.getencoding()
    ascii_bytes = bytes(range(128))
    ascii_text = "".join(chr(value) for value in range(128))
    try:
        decoded = ascii_bytes.decode(encoding)
        return decoded == ascii_text and decoded.encode(encoding) == ascii_bytes
    except (LookupError, UnicodeError):
        return False


@overload
def _bounded_splitlines(value: str, *, keepends: bool) -> list[str]: ...


@overload
def _bounded_splitlines(value: bytes, *, keepends: bool) -> list[bytes]: ...


def _bounded_splitlines(
    value: str | bytes,
    *,
    keepends: bool,
) -> list[str] | list[bytes]:
    _bounded_line_count(value)
    return value.splitlines(keepends=keepends)


def _bounded_line_count(value: str | bytes) -> int:
    """Count a superset of Python line boundaries without allocating a line list."""

    if not value:
        return 0
    if isinstance(value, bytes):
        boundaries: set[str] | set[int] = {10, 11, 12, 13, 28, 29, 30, 133}
        carriage_return: str | int = 13
        line_feed: str | int = 10
    else:
        boundaries = {"\n", "\v", "\f", "\r", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"}
        carriage_return = "\r"
        line_feed = "\n"
    count = 0
    index = 0
    line_start = 0
    while index < len(value):
        current = value[index]
        if current not in boundaries:
            index += 1
            continue
        count += 1
        index += 1
        if current == carriage_return and index < len(value) and value[index] == line_feed:
            index += 1
        line_start = index
        if count > MAX_TEXT_LINES:
            raise _Unsupported("selected_result_line_ceiling_exceeded")
    if line_start < len(value):
        count += 1
    if count > MAX_TEXT_LINES:
        raise _Unsupported("selected_result_line_ceiling_exceeded")
    return count


def _case_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    contract = deepcopy(dict(value))
    expected = contract.pop("contract_digest", None)
    if expected != semantic_digest(contract):
        raise ProspectiveSelectedResultVerifierError("Case-contract digest does not replay.")
    contract["contract_digest"] = expected
    if (
        contract.get("artifact_kind") != "prospective_case_evidence_contract"
        or contract.get("contract_version") != "2.0.0"
        or contract.get("evidence_status") != "unverified_author_declaration"
        or contract.get("qualification_authority") != "none_case_contract_only"
    ):
        raise ProspectiveSelectedResultVerifierError("Unsupported case-contract artifact.")
    _case_id(contract.get("case_id"))
    binding = _selected_result_binding(contract.get("selected_result_binding"))
    if binding != contract.get("selected_result_binding"):
        raise ProspectiveSelectedResultVerifierError("Case-contract binding is not canonical.")
    if contract.get("selected_result_binding_digest") != semantic_digest(binding):
        raise ProspectiveSelectedResultVerifierError(
            "Case-contract selected-result binding digest does not replay."
        )
    return contract


def _validator_identity(value: Any) -> dict[str, Any]:
    identity = deepcopy(_mapping(value, "validator_identity"))
    _exact_keys(
        identity,
        {"validator_id", "provider", "execution_context_id", "identity_evidence_digest"},
        "validator_identity",
    )
    for key in ("validator_id", "provider", "execution_context_id"):
        _text(identity[key], key)
    _digest(identity["identity_evidence_digest"], "identity_evidence_digest")
    return identity


def _implementation_lock() -> list[dict[str, str]]:
    runtime = (
        f"{sys.implementation.name}:{sys.version}:"
        f"{sys.platform}:{os.linesep!r}:{locale.getencoding()}"
    )
    return [
        {
            "dependency_kind": "implementation",
            "path": "sc_referee_evaluation/prospective_selected_result_verifier.py",
            "content_digest": sha256_digest(Path(__file__).read_bytes()),
        },
        {
            "dependency_kind": "runtime",
            "path": "python-runtime",
            "content_digest": sha256_digest(runtime.encode("utf-8")),
        },
    ]


def _case_id(value: Any) -> str:
    case_id = _single_line(value, "case_id")
    if not case_id.startswith("case:") or len(case_id) != 25:
        raise ProspectiveSelectedResultVerifierError("Invalid opaque case identity.")
    return case_id


def _relative_path(value: Any, label: str) -> str:
    path = _single_line(value, label)
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or path != pure.as_posix()
        or path in {"", "."}
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise ProspectiveSelectedResultVerifierError(f"{label} is not a normalized relative path.")
    return path


def _digest(value: Any, label: str) -> str:
    digest = _single_line(value, label)
    if len(digest) != 71 or not digest.startswith("sha256:"):
        raise ProspectiveSelectedResultVerifierError(f"{label} is not a sha256 digest.")
    try:
        int(digest[7:], 16)
    except ValueError as error:
        raise ProspectiveSelectedResultVerifierError(f"{label} is not hexadecimal.") from error
    return digest


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProspectiveSelectedResultVerifierError("Invalid timestamp.") from error
    if parsed.tzinfo is None:
        raise ProspectiveSelectedResultVerifierError("Timestamp must include a timezone.")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProspectiveSelectedResultVerifierError(f"{label} must be an object.")
    return deepcopy(dict(value))


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProspectiveSelectedResultVerifierError(f"{label} must be an array.")
    return list(value)


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ProspectiveSelectedResultVerifierError(f"{label} has an unsupported shape.")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProspectiveSelectedResultVerifierError(f"{label} must be non-empty text.")
    return value


def _single_line(value: Any, label: str) -> str:
    text = _text(value, label)
    if "\n" in text or "\r" in text:
        raise ProspectiveSelectedResultVerifierError(f"{label} must be one line.")
    return text
