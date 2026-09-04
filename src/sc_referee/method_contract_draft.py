"""Deterministic validation of one proposed scientific-requirement profile.

Reading a protocol and proposing an outcome family is the agent's job, carried out with the
scientist. This module does not read prose and does not propose anything. It takes an explicit
proposal, checks it against the protocol text and the material-input header under a closed set of
fail-closed rules, and either writes the profile plus a provenance sidecar or refuses.

Rule ``method-contract-draft/outcome-family/v1`` derived the family from prose anchors and was
withdrawn: a regular expression over free prose cannot fail closed. See ADR-0082.

Nothing here reads project-authored code, and nothing reads a data value below the header row.
The drafted profile remains a proposal. Only the later ``method-contract`` freeze, carried out
under a named human actor id, confirms it.
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

DRAFT_RULE_ID = "method-contract-draft/outcome-family/v2"
WITHDRAWN_DRAFT_RULE_ID = "method-contract-draft/outcome-family/v1"
DRAFT_PROVENANCE_PROFILE = "method_contract_draft_provenance_v1"
DRAFT_PROVENANCE_VERSION = "2.0.0"
DRAFT_TOOL_NAME = "sc-referee"

MULTIPLE_TESTING_CHECK_ID = "check:authorized-complete-family-correction-over-code-test-battery"
MULTIPLE_TESTING_CANDIDATE_ID = "complete-correction-over-authorized-outcome-family"
_MULTIPLE_TESTING_PROFILE_VERSION = "1.2.0"
_FAMILY_MEMBER_RULE = "one-two-group-test-per-named-outcome-column"
_CORRECTION_SCOPE = "complete-authorized-family"

__all__ = [
    "DRAFT_PROVENANCE_EXTENSION_KEY",
    "DRAFT_PROVENANCE_PROFILE",
    "DRAFT_PROVENANCE_VERSION",
    "DRAFT_RULE_ID",
    "MULTIPLE_TESTING_CANDIDATE_ID",
    "MULTIPLE_TESTING_CHECK_ID",
    "QUALIFYING_VOCABULARY",
    "WITHDRAWN_DRAFT_RULE_ID",
    "DraftedProfile",
    "ExcludedColumn",
    "MethodContractDraftError",
    "confirmed_draft_provenance",
    "draft_summary_text",
    "refusal_text",
    "validate_draft_provenance",
    "validate_proposed_requirement_profile",
    "verify_draft_provenance_sources",
]

_COLUMN_TOKEN = r"[A-Za-z][A-Za-z0-9_.-]{0,127}"
_SAFE_COLUMN = re.compile(rf"{_COLUMN_TOKEN}\Z")
_CSV_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}\.csv", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"[.!?\n]")
_WORD_CHARS = re.compile(r"[A-Za-z0-9_]")

# Closed conservative tripwire vocabulary. A proposed column standing in the same sentence as one
# of these words is not parsed; it is refused, so a human reads the sentence.
QUALIFYING_VOCABULARY: tuple[str, ...] = ("not", "excluded", "exclude", "except", "secondary")
_VOCABULARY_PATTERN = re.compile(r"\b(?:" + "|".join(QUALIFYING_VOCABULARY) + r")\b", re.IGNORECASE)

_IDENTIFIER_SUFFIXES = ("_id", "_uid", "_tag", "_key")
_MINIMUM_FAMILY_SIZE = 3
_BOM = "﻿"


class MethodContractDraftError(ValueError):
    """Raised when the closed validation rule refuses a proposed requirement."""


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
    grounding: dict[str, list[int]]
    task_path: str
    material_input_path: str
    proposed_by: str

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
    if not resolved.is_relative_to(repository.resolve()):
        raise MethodContractDraftError(f"{label} escapes the repository root")
    if resolved.is_symlink() or not resolved.is_file():
        raise MethodContractDraftError(f"{label} is not a regular file inside the repository")
    return pure.as_posix()


def _read_protocol_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MethodContractDraftError("the task file is not valid UTF-8 text") from error
    return text, sha256_digest(raw)


def read_material_input_header(path: Path) -> list[str]:
    """Read and fail-closed validate the first row of one material input."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        try:
            first = next(csv.reader(handle))
        except StopIteration as error:
            raise MethodContractDraftError("the material input has no header row") from error
        except UnicodeDecodeError as error:
            raise MethodContractDraftError(
                "the material input header is not valid UTF-8 text"
            ) from error
    if first and first[0].startswith(_BOM):
        raise MethodContractDraftError(
            "the material input header begins with a byte-order mark; save it as plain UTF-8"
        )
    header = [name.strip() for name in first]
    if not header:
        raise MethodContractDraftError("the material input has an empty header row")
    if any(not name for name in header):
        raise MethodContractDraftError("the material input header has a blank column name")
    if len(header) != len(set(header)):
        raise MethodContractDraftError("the material input header has duplicate column names")
    folded = [name.casefold() for name in header]
    if len(folded) != len(set(folded)):
        collisions = sorted({name for name in header if folded.count(name.casefold()) > 1})
        raise MethodContractDraftError(
            "the material input header has column names that differ only by case: "
            + ", ".join(collisions)
        )
    unsupported = [name for name in header if _SAFE_COLUMN.fullmatch(name) is None]
    if unsupported:
        raise MethodContractDraftError(
            "the material input header has column names the contract cannot carry: "
            + ", ".join(sorted(unsupported))
        )
    return header


def _verbatim_lines(protocol: str, name: str) -> list[int]:
    """Line numbers where ``name`` occurs verbatim as a whole token, case-sensitive."""

    lines: list[int] = []
    for number, line in enumerate(protocol.splitlines(), start=1):
        start = 0
        while True:
            index = line.find(name, start)
            if index < 0:
                break
            before = line[index - 1] if index > 0 else ""
            after_index = index + len(name)
            after = line[after_index] if after_index < len(line) else ""
            if not _WORD_CHARS.fullmatch(before or " ") and not _WORD_CHARS.fullmatch(after or " "):
                lines.append(number)
                break
            start = index + 1
    return lines


def _qualifying_sentences(protocol: str, name: str) -> list[str]:
    """Sentences that contain ``name`` verbatim and a closed tripwire word."""

    hits: list[str] = []
    for sentence in _SENTENCE_SPLIT.split(protocol):
        if not _verbatim_lines(sentence, name):
            continue
        if _VOCABULARY_PATTERN.search(sentence):
            hits.append(" ".join(sentence.split()))
    return hits


def _is_identifier_shape(name: str) -> bool:
    lowered = name.lower()
    return lowered == "id" or lowered.endswith(_IDENTIFIER_SUFFIXES)


def _normalized_exclusions(exclusions: Mapping[str, str] | None) -> dict[str, str]:
    declared: dict[str, str] = {}
    for column, reason in (exclusions or {}).items():
        name = column.strip()
        text = reason.strip()
        if not name:
            raise MethodContractDraftError("an --exclude entry has an empty column name")
        if not text:
            raise MethodContractDraftError(f"--exclude {name} has an empty reason")
        declared[name] = text
    return declared


def validate_proposed_requirement_profile(
    repository: Path,
    *,
    task: str,
    material_input: str,
    group_column: str,
    outcome_columns: Sequence[str],
    proposed_by: str,
    exclusions: Mapping[str, str] | None = None,
    check_id: str = MULTIPLE_TESTING_CHECK_ID,
    candidate_id: str = MULTIPLE_TESTING_CANDIDATE_ID,
) -> DraftedProfile:
    """Validate one proposed outcome family against the protocol text and the CSV header.

    Every failure raises :class:`MethodContractDraftError`. Nothing is inferred, repaired, or
    reordered: the proposal is accepted exactly as given or refused.
    """

    if check_id != MULTIPLE_TESTING_CHECK_ID or candidate_id != MULTIPLE_TESTING_CANDIDATE_ID:
        raise MethodContractDraftError(
            "the validation rule covers only "
            f"{MULTIPLE_TESTING_CHECK_ID} / {MULTIPLE_TESTING_CANDIDATE_ID}"
        )
    actor = proposed_by.strip()
    if not actor:
        raise MethodContractDraftError("--proposed-by must identify the proposing agent")
    root = repository.resolve()
    if not root.is_dir():
        raise MethodContractDraftError("repository must be an existing directory")
    task_path = _repository_relative(root, task, label="--task")
    material_path = _repository_relative(root, material_input, label="--material-input")
    if PurePosixPath(material_path).suffix.lower() != ".csv":
        raise MethodContractDraftError("--material-input must name a .csv file")

    protocol, task_digest = _read_protocol_text(root / task_path)
    header = read_material_input_header(root / material_path)
    declared_exclusions = _normalized_exclusions(exclusions)

    group = group_column.strip()
    outcomes = [name.strip() for name in outcome_columns]
    if not group:
        raise MethodContractDraftError("--group-column must name one header column")
    if not outcomes or any(not name for name in outcomes):
        raise MethodContractDraftError("--outcome-columns must name header columns")

    _refuse_other_material_inputs(protocol, material_path)

    header_set = set(header)
    for name in declared_exclusions:
        if name not in header_set:
            raise MethodContractDraftError(f"--exclude names {name}, which is not a header column")
    for name in [group, *outcomes]:
        if name not in header_set:
            folded = [item for item in header if item.casefold() == name.casefold()]
            hint = f"; the header has {folded[0]}" if folded else ""
            raise MethodContractDraftError(
                f"proposed column {name} is not in the material input header{hint}"
            )

    if len(outcomes) != len(set(outcomes)):
        raise MethodContractDraftError("the proposed outcome family repeats a column")
    if group in outcomes:
        raise MethodContractDraftError(f"the group column {group} is also proposed as an outcome")
    identifier_named = [name for name in outcomes if _is_identifier_shape(name)]
    if identifier_named:
        raise MethodContractDraftError(
            "identifier-shaped columns are proposed as outcomes: " + ", ".join(identifier_named)
        )
    flagged = [name for name in outcomes if name in declared_exclusions]
    if flagged:
        detail = "; ".join(f"{name}: {declared_exclusions[name]}" for name in flagged)
        raise MethodContractDraftError(
            f"columns flagged with --exclude are proposed as outcomes ({detail})"
        )
    if len(outcomes) < _MINIMUM_FAMILY_SIZE:
        raise MethodContractDraftError(
            "the proposed outcome family has fewer than three columns; this contract requires "
            "at least three"
        )

    grounding: dict[str, list[int]] = {}
    for name in [group, *outcomes]:
        lines = _verbatim_lines(protocol, name)
        if not lines:
            raise MethodContractDraftError(
                f"proposed column {name} does not occur verbatim in {task_path}"
            )
        grounding[name] = lines
    for name in [group, *outcomes]:
        qualified = _qualifying_sentences(protocol, name)
        if qualified:
            raise MethodContractDraftError(
                f"protocol qualifies {name}; confirm by hand ({qualified[0]})"
            )

    profile = {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": _MULTIPLE_TESTING_PROFILE_VERSION,
        "check_id": check_id,
        "candidate_id": candidate_id,
        "semantic_role_authority": {
            "authorized_test_family": {
                "material_input_path": material_path,
                "group_contrast_column": group,
                "outcome_columns": list(outcomes),
                "family_member_rule": _FAMILY_MEMBER_RULE,
                "correction_scope": _CORRECTION_SCOPE,
            }
        },
    }
    try:
        resolve_scientific_requirement_profile(profile)
    except ScientificRequirementContractError as error:
        raise MethodContractDraftError(
            f"the proposed profile is not accepted by the installed registry: {error}"
        ) from error

    excluded = _excluded_columns(header, outcomes, group, declared_exclusions)
    provenance = {
        "provenance_profile": DRAFT_PROVENANCE_PROFILE,
        "provenance_version": DRAFT_PROVENANCE_VERSION,
        "proposed_by": actor,
        "drafted_by": {"tool": DRAFT_TOOL_NAME, "tool_version": __version__},
        "draft_rule": DRAFT_RULE_ID,
        "draft_sources": {
            "task_path": task_path,
            "task_content_digest": task_digest,
            "material_input_path": material_path,
            "material_input_header": list(header),
            "material_input_header_digest": semantic_digest(list(header)),
        },
        "grounding": {name: list(lines) for name, lines in sorted(grounding.items())},
        "declared_exclusions": dict(sorted(declared_exclusions.items())),
        "drafted_profile_digest": semantic_digest(profile),
        "confirmed_by": None,
    }
    return DraftedProfile(
        profile=profile,
        provenance=provenance,
        header=list(header),
        outcome_columns=list(outcomes),
        group_column=group,
        excluded=excluded,
        grounding=grounding,
        task_path=task_path,
        material_input_path=material_path,
        proposed_by=actor,
    )


def _refuse_other_material_inputs(protocol: str, material_path: str) -> None:
    permitted = {material_path, PurePosixPath(material_path).name}
    others = sorted(
        {match.group(0) for match in _CSV_TOKEN.finditer(protocol)} - permitted,
    )
    if others:
        raise MethodContractDraftError(
            "protocol names another material input: " + ", ".join(others)
        )


def _excluded_columns(
    header: Sequence[str],
    outcomes: Sequence[str],
    group_column: str,
    declared_exclusions: Mapping[str, str],
) -> list[ExcludedColumn]:
    chosen = set(outcomes)
    excluded: list[ExcludedColumn] = []
    for name in header:
        if name in chosen:
            continue
        if name == group_column:
            excluded.append(ExcludedColumn(name, "proposed as the two-group contrast column"))
        elif name in declared_exclusions:
            excluded.append(
                ExcludedColumn(name, f"flagged by the caller: {declared_exclusions[name]}")
            )
        elif _is_identifier_shape(name):
            excluded.append(
                ExcludedColumn(name, "identifier-shaped column not proposed as an outcome")
            )
        else:
            excluded.append(ExcludedColumn(name, "not proposed as an outcome"))
    return excluded


def draft_summary_text(draft: DraftedProfile, *, profile_path: str, provenance_path: str) -> str:
    """Plain-language summary a scientist reads before confirming or editing the proposal."""

    lines = [
        f"Validated the proposed method-contract profile under rule {DRAFT_RULE_ID}.",
        f"Proposed by: {draft.proposed_by}",
        f"Protocol read: {draft.task_path}",
        f"Material input header read: {draft.material_input_path}",
        "",
        (
            f"Outcome family ({len(draft.outcome_columns)}, in proposed order): "
            + ", ".join(draft.outcome_columns)
        ),
        f"Group column (two-group contrast): {draft.group_column}",
        "Excluded columns and why:",
    ]
    if draft.excluded:
        lines.extend(f"  {item.column}: {item.reason}" for item in draft.excluded)
    else:
        lines.append("  none; every header column is a proposed outcome")
    lines.append("")
    lines.append(f"Every name above occurs verbatim in {draft.task_path}, at these lines:")
    for name in [draft.group_column, *draft.outcome_columns]:
        numbers = ", ".join(str(number) for number in draft.grounding[name])
        lines.append(f"  {name}: line {numbers}")
    lines.extend(
        [
            "",
            "This tool did not read the protocol's prose and did not choose these columns.",
            "It checked a proposal against the protocol text and the header row.",
            "No analysis code was read. No data value below the header row was read.",
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
    """Message printed when the closed validation rule refuses a proposal."""

    return "\n".join(
        [
            f"Refused the proposed profile: {reason}.",
            "No profile was written. Nothing was guessed, repaired, or reordered.",
            "",
            "Do not edit the protocol to make this refusal go away.",
            "Present this refusal to the scientist. If the scientist cannot resolve it by",
            "correcting the proposal, use the unresolved-contract path and let the scientist",
            "answer the exact question:",
            f"  sc-referee method-contract <project-root> --task {task} --output <new-output>",
            "  sc-referee questions <new-output>",
            "",
            "Present the exact open MaterialQuestion to the scientist. Do not answer it yourself.",
        ]
    )


_PROVENANCE_FIELDS = frozenset(
    {
        "provenance_profile",
        "provenance_version",
        "proposed_by",
        "drafted_by",
        "draft_rule",
        "draft_sources",
        "grounding",
        "declared_exclusions",
        "drafted_profile_digest",
        "confirmed_by",
    }
)
_SOURCE_FIELDS = frozenset(
    {
        "task_path",
        "task_content_digest",
        "material_input_path",
        "material_input_header",
        "material_input_header_digest",
    }
)


def validate_draft_provenance(value: object) -> dict[str, Any]:
    """Validate one provenance sidecar's shape and internal consistency."""

    if not isinstance(value, Mapping):
        raise MethodContractDraftError("draft provenance must be an object")
    if set(value) != _PROVENANCE_FIELDS:
        raise MethodContractDraftError("draft provenance has the wrong exact field set")
    if value.get("provenance_profile") != DRAFT_PROVENANCE_PROFILE:
        raise MethodContractDraftError("unsupported draft-provenance profile")
    if value.get("provenance_version") != DRAFT_PROVENANCE_VERSION:
        raise MethodContractDraftError("unsupported draft-provenance version")
    if value.get("draft_rule") == WITHDRAWN_DRAFT_RULE_ID:
        raise MethodContractDraftError(
            f"{WITHDRAWN_DRAFT_RULE_ID} was withdrawn (ADR-0082); draft the profile again"
        )
    if value.get("draft_rule") != DRAFT_RULE_ID:
        raise MethodContractDraftError(
            f"unsupported draft rule id; this build writes and accepts only {DRAFT_RULE_ID}"
        )
    proposed_by = value.get("proposed_by")
    if not isinstance(proposed_by, str) or not proposed_by.strip():
        raise MethodContractDraftError("draft provenance must name the proposing agent")
    drafted_by = value.get("drafted_by")
    if not isinstance(drafted_by, Mapping) or set(drafted_by) != {"tool", "tool_version"}:
        raise MethodContractDraftError("draft provenance drafted_by is malformed")
    if drafted_by.get("tool") != DRAFT_TOOL_NAME:
        raise MethodContractDraftError("draft provenance was not written by sc-referee")
    sources = value.get("draft_sources")
    if not isinstance(sources, Mapping) or set(sources) != _SOURCE_FIELDS:
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
    task_digest = sources.get("task_content_digest")
    if not isinstance(task_digest, str) or not _is_sha256(task_digest):
        raise MethodContractDraftError("draft provenance task digest is malformed")
    grounding = value.get("grounding")
    if not isinstance(grounding, Mapping) or not grounding:
        raise MethodContractDraftError("draft provenance grounding is malformed")
    normalized_grounding: dict[str, list[int]] = {}
    for name, numbers in grounding.items():
        if (
            not isinstance(name, str)
            or not isinstance(numbers, Sequence)
            or isinstance(numbers, (str, bytes))
            or not numbers
            or not all(isinstance(item, int) and item > 0 for item in numbers)
        ):
            raise MethodContractDraftError("draft provenance grounding is malformed")
        normalized_grounding[name] = [int(item) for item in numbers]
    exclusions = value.get("declared_exclusions")
    if not isinstance(exclusions, Mapping) or not all(
        isinstance(name, str) and isinstance(reason, str) and name and reason
        for name, reason in exclusions.items()
    ):
        raise MethodContractDraftError("draft provenance declared_exclusions is malformed")
    digest = value.get("drafted_profile_digest")
    if not isinstance(digest, str) or not _is_sha256(digest):
        raise MethodContractDraftError("draft provenance profile digest is malformed")
    if value.get("confirmed_by") is not None:
        raise MethodContractDraftError("draft provenance must be unconfirmed before the freeze")
    return {
        "provenance_profile": DRAFT_PROVENANCE_PROFILE,
        "provenance_version": DRAFT_PROVENANCE_VERSION,
        "proposed_by": proposed_by.strip(),
        "drafted_by": {
            "tool": DRAFT_TOOL_NAME,
            "tool_version": str(drafted_by["tool_version"]),
        },
        "draft_rule": DRAFT_RULE_ID,
        "draft_sources": {
            "task_path": str(sources["task_path"]),
            "task_content_digest": task_digest,
            "material_input_path": str(sources["material_input_path"]),
            "material_input_header": [str(item) for item in header],
            "material_input_header_digest": str(sources["material_input_header_digest"]),
        },
        "grounding": {name: normalized_grounding[name] for name in sorted(normalized_grounding)},
        "declared_exclusions": {
            str(name): str(reason) for name, reason in sorted(exclusions.items())
        },
        "drafted_profile_digest": digest,
        "confirmed_by": None,
    }


def _is_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def verify_draft_provenance_sources(
    provenance: Mapping[str, Any],
    *,
    repository: Path,
    task: str,
    profile: Mapping[str, Any],
) -> dict[str, Any]:
    """Re-read the bound sources and refuse a sidecar that does not match them.

    A sidecar is a record, not a credential. This check makes it unforgeable without the real
    files and unreplayable into another repository: the task path and its bytes, and the material
    input's path and header row, must still be exactly what the sidecar names.
    """

    validated = validate_draft_provenance(provenance)
    sources = validated["draft_sources"]
    root = repository.resolve()
    task_path = _repository_relative(root, task, label="--task")
    if sources["task_path"] != task_path:
        raise MethodContractDraftError(
            f"draft provenance was drafted for {sources['task_path']}, not {task_path}"
        )
    _, task_digest = _read_protocol_text(root / task_path)
    if sources["task_content_digest"] != task_digest:
        raise MethodContractDraftError(f"{task_path} changed after the draft; draft it again")
    authority = _authorized_test_family(profile)
    confirmed_material = str(authority.get("material_input_path", ""))
    if sources["material_input_path"] != confirmed_material:
        raise MethodContractDraftError(
            f"draft provenance was drafted for {sources['material_input_path']}, but the profile "
            f"authorizes {confirmed_material}"
        )
    material_path = _repository_relative(root, confirmed_material, label="material input")
    if read_material_input_header(root / material_path) != sources["material_input_header"]:
        raise MethodContractDraftError(
            f"{material_path} header changed after the draft; draft it again"
        )
    return validated


def _authorized_test_family(profile: Mapping[str, Any]) -> Mapping[str, Any]:
    authority = profile.get("semantic_role_authority")
    if not isinstance(authority, Mapping):
        raise MethodContractDraftError("the confirmed profile carries no semantic role authority")
    family = authority.get("authorized_test_family")
    if not isinstance(family, Mapping):
        raise MethodContractDraftError("the confirmed profile carries no authorized test family")
    return family


def confirmed_draft_provenance(
    provenance: Mapping[str, Any],
    *,
    repository: Path,
    task: str,
    profile: Mapping[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Project one verified sidecar into the confirmed lock extension value."""

    validated = verify_draft_provenance_sources(
        provenance, repository=repository, task=task, profile=profile
    )
    confirmed_digest = semantic_digest(dict(profile))
    return {
        "draft_rule": validated["draft_rule"],
        "proposed_by": validated["proposed_by"],
        "drafted_by": validated["drafted_by"],
        "draft_sources": validated["draft_sources"],
        "grounding": validated["grounding"],
        "declared_exclusions": validated["declared_exclusions"],
        "drafted_profile_digest": validated["drafted_profile_digest"],
        "confirmed_profile_digest": confirmed_digest,
        "human_edited_after_draft": confirmed_digest != validated["drafted_profile_digest"],
        "confirmed_by": {"actor_kind": "human", "actor_id": actor_id},
    }
