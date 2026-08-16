"""Development-only deterministic independent-unit declaration translation."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Literal

from .ir import require_registered_v2_reason

TRANSLATION_VERSION = "2.0.0-development"
CANONICAL_TERMINAL_FORM = "canonical-terminal-sentence-v2"

CompatibilityProfile = Literal["growth-loop-standalone-v1", "wall-census-standalone-v1"]

_LITERAL_PREFIX = b"Independent unit column:"
_ASCII_ID = rb"[A-Za-z_][A-Za-z0-9_]*"
_TERMINAL = re.compile(
    rb"\. (?P<clause>Independent unit column: (?P<token>" + _ASCII_ID + rb"))(?P<ending>\r\n|\n)?\Z"
)
_GROWTH_STANDALONE = re.compile(
    rb"(?im)^[ \t]*(?P<clause>independent unit column[ \t]*:[ \t]+"
    rb"`?(?P<token>" + _ASCII_ID + rb")`?)[ \t\r]*$"
)
_WALL_STANDALONE = re.compile(
    rb"(?m)^(?P<clause>Independent unit column:[ \t]*(?P<token>[^\r\n]*?))[ \t]*\r?$"
)
_RESERVED_LEAD = re.compile(rb"independent unit column", re.IGNORECASE | re.ASCII)


@dataclass(frozen=True)
class DeclarationCandidate:
    """One complete declaration form and its byte-exact receipt fields."""

    form_id: str
    span_start: int
    span_end: int
    quoted_declaration: str
    token: str
    lead_start: int
    lead_end: int


@dataclass(frozen=True)
class UnitTranslation:
    """One primary unit-transport decision under the amended total order."""

    unit_column: str | None
    reason: str | None
    candidate: DeclarationCandidate | None
    logical_header: tuple[str, ...] | None
    translation_version: str = TRANSLATION_VERSION


def _candidate(match: re.Match[bytes], form_id: str) -> DeclarationCandidate:
    clause = match.group("clause")
    token = match.group("token")
    clause_start, clause_end = match.span("clause")
    lead_relative = clause.lower().find(b"independent unit column")
    return DeclarationCandidate(
        form_id=form_id,
        span_start=clause_start,
        span_end=clause_end,
        quoted_declaration=clause.decode("utf-8"),
        token=token.decode("utf-8"),
        lead_start=clause_start + lead_relative,
        lead_end=clause_start + lead_relative + len(b"independent unit column"),
    )


def _complete_candidates(
    description: bytes, profile: CompatibilityProfile
) -> tuple[DeclarationCandidate, ...]:
    candidates: list[DeclarationCandidate] = []
    standalone = _GROWTH_STANDALONE if profile == "growth-loop-standalone-v1" else _WALL_STANDALONE
    for match in standalone.finditer(description):
        if profile == "wall-census-standalone-v1" and not match.group("token").strip():
            continue
        candidate = _candidate(match, profile)
        if profile == "wall-census-standalone-v1":
            stripped = candidate.token.strip()
            leading = len(candidate.token) - len(candidate.token.lstrip())
            candidate = DeclarationCandidate(
                form_id=candidate.form_id,
                span_start=candidate.span_start,
                span_end=candidate.span_end - (len(candidate.token) - leading - len(stripped)),
                quoted_declaration=candidate.quoted_declaration.rstrip(),
                token=stripped,
                lead_start=candidate.lead_start,
                lead_end=candidate.lead_end,
            )
        candidates.append(candidate)
    terminal = _TERMINAL.search(description)
    if terminal is not None:
        candidates.append(_candidate(terminal, CANONICAL_TERMINAL_FORM))
    return tuple(
        sorted(candidates, key=lambda item: (item.span_start, item.span_end, item.form_id))
    )


def _ascii_lower(value: str) -> str:
    return "".join(chr(ord(char) + 32) if "A" <= char <= "Z" else char for char in value)


def _refusal(reason: str) -> UnitTranslation:
    return UnitTranslation(
        unit_column=None,
        reason=require_registered_v2_reason(reason),
        candidate=None,
        logical_header=None,
    )


def translate_unit_declaration(
    description: bytes, data: bytes, profile: CompatibilityProfile
) -> UnitTranslation:
    """Apply the Growth-12 amended first-match refusal chain without role input."""

    try:
        description.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _refusal("unit-description-not-valid-utf8")

    if description.count(_LITERAL_PREFIX) >= 2:
        return _refusal("unit-declaration-duplicate-prefix")

    candidates = _complete_candidates(description, profile)
    leads = tuple(_RESERVED_LEAD.finditer(description))
    if any(
        sum(
            candidate.lead_start == lead.start() and candidate.lead_end == lead.end()
            for candidate in candidates
        )
        != 1
        for lead in leads
    ):
        return _refusal("unit-declaration-syntax-outside-closed-grammar")
    if not candidates:
        return _refusal("unit-declaration-missing")
    if len(candidates) > 1:
        tokens = {candidate.token for candidate in candidates}
        if len(tokens) > 1:
            return _refusal("unit-declaration-conflicting-sentences")
        return _refusal("unit-declaration-ambiguous-multiple-candidates")

    candidate = candidates[0]
    try:
        decoded = data.decode("utf-8", errors="strict")
        if "\x00" in decoded:
            raise csv.Error("NUL is outside the accepted CSV transport")
        rows = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
        if len(rows) < 2 or not rows[0] or any(not field for field in rows[0]):
            raise csv.Error("CSV requires a nonempty header and at least one data row")
        header = rows[0]
        if any(len(row) != len(header) for row in rows[1:]):
            raise csv.Error("CSV rows must have equal widths")
        matching_indexes = [index for index, field in enumerate(header) if field == candidate.token]
        if matching_indexes and any(
            not row[index] for row in rows[1:] for index in matching_indexes
        ):
            raise csv.Error("declared unit cells must be nonempty")
    except (UnicodeDecodeError, csv.Error):
        return _refusal("unit-csv-invalid-or-incomplete")

    if len(header) != len(set(header)):
        return _refusal("unit-column-duplicated-in-csv-header")
    if candidate.token not in header:
        return _refusal("unit-column-not-in-csv-header")
    folded_token = _ascii_lower(candidate.token)
    if any(field != candidate.token and _ascii_lower(field) == folded_token for field in header):
        return _refusal("unit-column-case-collision-in-csv-header")
    return UnitTranslation(
        unit_column=candidate.token,
        reason=None,
        candidate=candidate,
        logical_header=tuple(header),
    )


def receipt_dict(translation: UnitTranslation) -> dict[str, object] | None:
    """Return the deterministic disclosure receipt for a successful translation."""

    candidate = translation.candidate
    if candidate is None or translation.logical_header is None:
        return None
    return {
        "translation_version": translation.translation_version,
        "declaration_form_id": candidate.form_id,
        "declaration_byte_span": [candidate.span_start, candidate.span_end],
        "quoted_declaration": candidate.quoted_declaration,
        "extracted_token": candidate.token,
        "logical_header": list(translation.logical_header),
    }
