"""Deterministic pre-analysis draft of one scientific-requirement profile.

The draft step reads exactly two things: the governing protocol or task text, and the header
row of the authorized material input. It never reads project-authored code, never reads a data
value below the header row, and never guesses an outcome family that the protocol does not name.
A refused draft is a normal outcome: the caller falls back to the unresolved-contract
MaterialQuestion path so a human resolves the family explicitly.

The drafted profile is a proposal. Only the later ``method-contract`` freeze, carried out under a
named human actor id, confirms it.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_requirement_contract import (
    DRAFT_PROVENANCE_EXTENSION_KEY,
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    ScientificRequirementContractError,
    resolve_scientific_requirement_profile,
)
from sc_referee.version import __version__

DRAFT_RULE_ID = "method-contract-draft/outcome-family/v1"
DRAFT_PROVENANCE_PROFILE = "method_contract_draft_provenance_v1"
DRAFT_PROVENANCE_VERSION = "1.0.0"

__all__ = [
    "DRAFT_PROVENANCE_EXTENSION_KEY",
    "DRAFT_PROVENANCE_PROFILE",
    "DRAFT_PROVENANCE_VERSION",
    "DRAFT_RULE_ID",
    "DraftedProfile",
    "ExcludedColumn",
    "MethodContractDraftError",
    "confirmed_draft_provenance",
    "draft_scientific_requirement_profile",
    "draft_summary_text",
    "refusal_text",
    "validate_draft_provenance",
]

MULTIPLE_TESTING_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
MULTIPLE_TESTING_CANDIDATE_ID = "complete-correction-over-authorized-outcome-family"
_MULTIPLE_TESTING_PROFILE_VERSION = "1.2.0"
_FAMILY_MEMBER_RULE = "one-two-group-test-per-named-outcome-column"
_CORRECTION_SCOPE = "complete-authorized-family"

_COLUMN_TOKEN = r"[A-Za-z][A-Za-z0-9_.-]{0,127}"
_QUOTED_COLUMN = rf"[`'\"]?({_COLUMN_TOKEN})[`'\"]?"
_QUOTED_FILE = r"[`'\"]?([A-Za-z0-9][A-Za-z0-9_./-]{0,255}\.csv)[`'\"]?"

# Closed anchor set for the two-group contrast column. Each anchor must name the column
# explicitly; no anchor infers a group column from position, dtype, or cardinality.
_GROUP_ANCHORS: tuple[re.Pattern[str], ...] = (
    re.compile(
        rf"two\s+groups\s+recorded\s+in\s+(?:the\s+)?{_QUOTED_COLUMN}\s+column"
        rf"(?:\s+of\s+{_QUOTED_FILE})?",
        re.IGNORECASE,
    ),
    re.compile(
        rf"group[\s_-]?(?:contrast|comparison)\s+column\s*(?:is|:)\s*{_QUOTED_COLUMN}",
        re.IGNORECASE,
    ),
)

# Closed anchor set for the named outcome family. Each anchor captures one comma-separated
# list that ends at the first sentence-terminating period.
_OUTCOME_ANCHORS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"outcome\s+family\s*(?:,[^:.]*?,)?\s*(?:(?:is|are)\s*:?|:)\s*(?P<list>[^.]+)\.",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:pre-declared|pre-specified|predeclared|prespecified|declared)\s+outcomes?\s*"
        r"(?:,[^:.]*?,)?\s*(?:(?:is|are)\s*:?|:)\s*(?P<list>[^.]+)\.",
        re.IGNORECASE,
    ),
)

_IDENTIFIER_SUFFIXES = ("_id", "_uid", "_tag", "_key")
_SAFE_COLUMN = re.compile(rf"{_COLUMN_TOKEN}\Z")

_MINIMUM_FAMILY_SIZE = 3


class MethodContractDraftError(ValueError):
    """Raised when the closed draft rule refuses to derive a profile."""


@dataclass(frozen=True)
class ExcludedColumn:
    column: str
    reason: str


@dataclass(frozen=True)
class DraftedProfile:
    profile: dict[str, Any]
    provenance: dict[str, Any]
    header: list[str]
    outcome_columns: list[str]
    group_column: str
    excluded: list[ExcludedColumn]
    task_path: str
    material_input_path: str
    protocol_order_matches_header_order: bool

    def profile_bytes(self) -> bytes:
        return (json.dumps(self.profile, indent=2) + "\n").encode("utf-8")


def _repository_relative(repository: Path, value: str, *, label: str) -> str:
    text = value.strip()
    if not text:
        raise MethodContractDraftError(f"{label} must be a repository-relative path")
    if text.startswith("/") or "\\" in text:
        raise MethodContractDraftError(f"{label} must be a repository-relative POSIX path")
    pure = PurePosixPath(text)
    if pure.as_posix() != text or any(part in {".", ".."} for part in pure.parts):
        raise MethodContractDraftError(f"{label} must be a normalized repository-relative path")
    resolved = (repository / pure).resolve()
    root = repository.resolve()
    if not resolved.is_relative_to(root):
        raise MethodContractDraftError(f"{label} escapes the repository root")
    if not resolved.is_file() or resolved.is_symlink():
        raise MethodContractDraftError(f"{label} is not a regular file inside the repository")
    return pure.as_posix()


def _read_protocol_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:  # pragma: no cover - exercised through the CLI
        raise MethodContractDraftError("the task file is not valid UTF-8 text") from error
    return text, sha256_digest(raw)


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        try:
            first = next(csv.reader(handle))
        except StopIteration as error:
            raise MethodContractDraftError("the material input has no header row") from error
    header = [name.strip() for name in first]
    if not header:
        raise MethodContractDraftError("the material input has an empty header row")
    if any(not name for name in header):
        raise MethodContractDraftError("the material input header has a blank column name")
    if len(header) != len(set(header)):
        raise MethodContractDraftError("the material input header has duplicate column names")
    unsupported = [name for name in header if _SAFE_COLUMN.fullmatch(name) is None]
    if unsupported:
        raise MethodContractDraftError(
            "the material input header has column names the contract cannot carry: "
            + ", ".join(sorted(unsupported))
        )
    return header


def _named_group_column(protocol: str) -> tuple[str, str | None]:
    columns: list[str] = []
    files: list[str] = []
    for anchor in _GROUP_ANCHORS:
        for match in anchor.finditer(protocol):
            groups = match.groups()
            columns.append(groups[0])
            if len(groups) > 1 and groups[1]:
                files.append(groups[1])
    distinct = sorted(set(columns))
    if not distinct:
        raise MethodContractDraftError(
            "the protocol does not name a two-group contrast column in a recognized form"
        )
    if len(distinct) > 1:
        raise MethodContractDraftError(
            "the protocol names more than one two-group contrast column: " + ", ".join(distinct)
        )
    distinct_files = sorted(set(files))
    if len(distinct_files) > 1:
        raise MethodContractDraftError(
            "the protocol names more than one material input file: " + ", ".join(distinct_files)
        )
    return distinct[0], (distinct_files[0] if distinct_files else None)


def _split_named_list(span: str) -> list[str]:
    flattened = " ".join(span.split())
    names: list[str] = []
    for chunk in flattened.split(","):
        item = chunk.strip()
        for lead in ("and ", "And "):
            if item.startswith(lead):
                item = item[len(lead) :].strip()
        item = item.strip("`'\"")
        if item:
            names.append(item)
    return names


def _named_outcome_columns(protocol: str) -> list[str]:
    lists: list[list[str]] = []
    for anchor in _OUTCOME_ANCHORS:
        for match in anchor.finditer(protocol):
            names = _split_named_list(match.group("list"))
            if names:
                lists.append(names)
    if not lists:
        raise MethodContractDraftError(
            "the protocol does not name an outcome family in a recognized form"
        )
    first = lists[0]
    if any(other != first for other in lists[1:]):
        raise MethodContractDraftError("the protocol names more than one different outcome family")
    return first


def draft_scientific_requirement_profile(
    repository: Path,
    *,
    task: str,
    material_input: str,
    check_id: str = MULTIPLE_TESTING_CHECK_ID,
    candidate_id: str = MULTIPLE_TESTING_CANDIDATE_ID,
) -> DraftedProfile:
    """Derive one ``scientific_check_requirement_v1`` 1.2.0 profile under the closed draft rule.

    Only the protocol text and the material-input header row are read. Every refusal raises
    :class:`MethodContractDraftError`; nothing is guessed.
    """

    if check_id != MULTIPLE_TESTING_CHECK_ID or candidate_id != MULTIPLE_TESTING_CANDIDATE_ID:
        raise MethodContractDraftError(
            "the draft rule covers only "
            f"{MULTIPLE_TESTING_CHECK_ID} / {MULTIPLE_TESTING_CANDIDATE_ID}"
        )
    root = repository.resolve()
    if not root.is_dir():
        raise MethodContractDraftError("repository must be an existing directory")
    task_path = _repository_relative(root, task, label="--task")
    material_path = _repository_relative(root, material_input, label="--material-input")
    if PurePosixPath(material_path).suffix.lower() != ".csv":
        raise MethodContractDraftError("--material-input must name a .csv file")

    protocol, task_digest = _read_protocol_text(root / task_path)
    header = _read_header(root / material_path)

    group_column, named_file = _named_group_column(protocol)
    if named_file is not None and named_file not in {
        material_path,
        PurePosixPath(material_path).name,
    }:
        raise MethodContractDraftError(
            f"the protocol names {named_file} as the material input, not {material_path}"
        )
    outcome_columns = _named_outcome_columns(protocol)

    if group_column not in header:
        raise MethodContractDraftError(
            f"the protocol names group column {group_column}, which is not in the header"
        )
    missing = [name for name in outcome_columns if name not in header]
    if missing:
        raise MethodContractDraftError(
            "the protocol names outcome columns that are not in the header: " + ", ".join(missing)
        )
    if len(outcome_columns) != len(set(outcome_columns)):
        raise MethodContractDraftError("the protocol names a duplicate outcome column")
    if group_column in outcome_columns:
        raise MethodContractDraftError(
            f"the protocol names the group column {group_column} as an outcome"
        )
    identifier_named = [name for name in outcome_columns if _is_identifier_shape(name)]
    if identifier_named:
        raise MethodContractDraftError(
            "the protocol names identifier-shaped columns as outcomes: "
            + ", ".join(identifier_named)
        )
    if len(outcome_columns) < _MINIMUM_FAMILY_SIZE:
        raise MethodContractDraftError(
            "the protocol names fewer than three outcomes; this contract requires at least three"
        )

    profile = {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": _MULTIPLE_TESTING_PROFILE_VERSION,
        "check_id": check_id,
        "candidate_id": candidate_id,
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": material_path,
                "group_contrast_column": group_column,
                "outcome_columns": list(outcome_columns),
                "family_member_rule": _FAMILY_MEMBER_RULE,
                "correction_scope": _CORRECTION_SCOPE,
            }
        },
    }
    try:
        resolve_scientific_requirement_profile(profile)
    except ScientificRequirementContractError as error:
        raise MethodContractDraftError(
            f"the drafted profile is not accepted by the installed registry: {error}"
        ) from error

    excluded = _excluded_columns(header, outcome_columns, group_column)
    header_order = [name for name in header if name in set(outcome_columns)]
    provenance = {
        "provenance_profile": DRAFT_PROVENANCE_PROFILE,
        "provenance_version": DRAFT_PROVENANCE_VERSION,
        "drafted_by": {"tool": "sc-referee", "tool_version": __version__},
        "draft_rule": DRAFT_RULE_ID,
        "draft_sources": {
            "task_path": task_path,
            "task_content_digest": task_digest,
            "material_input_path": material_path,
            "material_input_header": list(header),
            "material_input_header_digest": semantic_digest(list(header)),
        },
        "drafted_profile_digest": semantic_digest(profile),
        "confirmed_by": None,
    }
    return DraftedProfile(
        profile=profile,
        provenance=provenance,
        header=list(header),
        outcome_columns=list(outcome_columns),
        group_column=group_column,
        excluded=excluded,
        task_path=task_path,
        material_input_path=material_path,
        protocol_order_matches_header_order=header_order == list(outcome_columns),
    )


def _is_identifier_shape(name: str) -> bool:
    lowered = name.lower()
    return lowered == "id" or lowered.endswith(_IDENTIFIER_SUFFIXES)


def _excluded_columns(
    header: Sequence[str], outcomes: Sequence[str], group_column: str
) -> list[ExcludedColumn]:
    chosen = set(outcomes)
    excluded: list[ExcludedColumn] = []
    for name in header:
        if name in chosen:
            continue
        if name == group_column:
            excluded.append(
                ExcludedColumn(name, "the protocol names it as the two-group contrast column")
            )
        elif _is_identifier_shape(name):
            excluded.append(
                ExcludedColumn(
                    name, "identifier-shaped column the protocol does not name as an outcome"
                )
            )
        else:
            excluded.append(ExcludedColumn(name, "the protocol does not name it as an outcome"))
    return excluded


def draft_summary_text(draft: DraftedProfile, *, profile_path: str, provenance_path: str) -> str:
    """Plain-language summary a scientist reads before confirming or editing the draft."""

    lines = [
        f"Drafted method-contract profile under rule {DRAFT_RULE_ID}.",
        f"Protocol read: {draft.task_path}",
        f"Material input header read: {draft.material_input_path}",
        "",
        (
            f"Outcome family ({len(draft.outcome_columns)}, in protocol order): "
            + ", ".join(draft.outcome_columns)
        ),
        f"Group column (two-group contrast): {draft.group_column}",
        "Excluded columns and why:",
    ]
    if draft.excluded:
        lines.extend(f"  {item.column}: {item.reason}" for item in draft.excluded)
    else:
        lines.append("  none; every header column is a named outcome")
    if not draft.protocol_order_matches_header_order:
        lines.append("")
        lines.append(
            "Note: the protocol order differs from the header order. The protocol order was used."
        )
    lines.extend(
        [
            "",
            "No analysis code was read. No data value below the header row was read.",
            "Nothing was inferred from column types, positions, or value counts.",
            "",
            f"Wrote {profile_path}",
            f"Wrote {provenance_path}",
            "",
            "Read every line above. Edit the profile JSON if any line is wrong, then confirm it:",
            "  sc-referee method-contract <project-root> --task "
            f"{draft.task_path} --profile {profile_path} \\",
            f"    --draft-provenance {provenance_path} --actor-id <scientist-id> "
            "--output <new-output>",
        ]
    )
    return "\n".join(lines)


def refusal_text(reason: str, *, task: str) -> str:
    """Message printed when the closed rule refuses to draft a profile."""

    return "\n".join(
        [
            f"Refused to draft a profile: {reason}.",
            "No profile was written. Nothing was guessed from code, filenames, or data values.",
            "",
            "Use the unresolved-contract path instead, and let the scientist answer the question:",
            f"  sc-referee method-contract <project-root> --task {task} --output <new-output>",
            "  sc-referee questions <new-output>",
            "",
            "Present the exact open MaterialQuestion to the scientist. Do not answer it yourself.",
            "Re-run draft-profile only after the protocol itself names the outcome family and the",
            "two-group contrast column.",
        ]
    )


def validate_draft_provenance(value: object) -> dict[str, Any]:
    """Validate one draft-provenance object supplied to the confirmation freeze."""

    if not isinstance(value, Mapping):
        raise MethodContractDraftError("draft provenance must be an object")
    expected = {
        "provenance_profile",
        "provenance_version",
        "drafted_by",
        "draft_rule",
        "draft_sources",
        "drafted_profile_digest",
        "confirmed_by",
    }
    if set(value) != expected:
        raise MethodContractDraftError("draft provenance has the wrong exact field set")
    if value.get("provenance_profile") != DRAFT_PROVENANCE_PROFILE:
        raise MethodContractDraftError("unsupported draft-provenance profile")
    if value.get("provenance_version") != DRAFT_PROVENANCE_VERSION:
        raise MethodContractDraftError("unsupported draft-provenance version")
    if value.get("draft_rule") != DRAFT_RULE_ID:
        raise MethodContractDraftError("unsupported draft rule id")
    drafted_by = value.get("drafted_by")
    if not isinstance(drafted_by, Mapping) or set(drafted_by) != {"tool", "tool_version"}:
        raise MethodContractDraftError("draft provenance drafted_by is malformed")
    sources = value.get("draft_sources")
    if not isinstance(sources, Mapping) or set(sources) != {
        "task_path",
        "task_content_digest",
        "material_input_path",
        "material_input_header",
        "material_input_header_digest",
    }:
        raise MethodContractDraftError("draft provenance draft_sources is malformed")
    header = sources.get("material_input_header")
    if (
        not isinstance(header, Sequence)
        or isinstance(header, (str, bytes))
        or not all(isinstance(item, str) for item in header)
    ):
        raise MethodContractDraftError("draft provenance header is malformed")
    if semantic_digest(list(header)) != sources.get("material_input_header_digest"):
        raise MethodContractDraftError("draft provenance header digest drifted")
    digest = value.get("drafted_profile_digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise MethodContractDraftError("draft provenance profile digest is malformed")
    if value.get("confirmed_by") is not None:
        raise MethodContractDraftError("draft provenance must be unconfirmed before the freeze")
    return {
        "provenance_profile": DRAFT_PROVENANCE_PROFILE,
        "provenance_version": DRAFT_PROVENANCE_VERSION,
        "drafted_by": {
            "tool": str(drafted_by["tool"]),
            "tool_version": str(drafted_by["tool_version"]),
        },
        "draft_rule": DRAFT_RULE_ID,
        "draft_sources": {
            "task_path": str(sources["task_path"]),
            "task_content_digest": str(sources["task_content_digest"]),
            "material_input_path": str(sources["material_input_path"]),
            "material_input_header": [str(item) for item in header],
            "material_input_header_digest": str(sources["material_input_header_digest"]),
        },
        "drafted_profile_digest": digest,
        "confirmed_by": None,
    }


def confirmed_draft_provenance(
    provenance: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Project one validated draft provenance into the confirmed lock extension value."""

    validated = validate_draft_provenance(provenance)
    confirmed_digest = semantic_digest(dict(profile))
    return {
        "draft_rule": validated["draft_rule"],
        "drafted_by": validated["drafted_by"],
        "draft_sources": validated["draft_sources"],
        "drafted_profile_digest": validated["drafted_profile_digest"],
        "confirmed_profile_digest": confirmed_digest,
        "human_edited_after_draft": confirmed_digest != validated["drafted_profile_digest"],
        "confirmed_by": {"actor_kind": "human", "actor_id": actor_id},
    }
