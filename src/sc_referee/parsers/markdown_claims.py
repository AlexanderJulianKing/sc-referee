from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.method_contracts import build_expected_count_profile
from sc_referee.version import SCHEMA_VERSION, __version__

_TIMESTAMP = "2026-07-27T20:00:00Z"
_PARSER_VERSION = "0.2.0"
_DIRECTIONAL_SENTENCE = re.compile(
    r"^(?P<subject>[A-Za-z][A-Za-z0-9 _-]*?) "
    r"(?P<verb>increased|decreased) "
    r"(?P<object>.+?) relative to (?P<comparison>[A-Za-z][A-Za-z0-9 _-]*?)[.]?$",
    re.IGNORECASE,
)
_NUMBER = r"-?(?:0|[1-9][0-9]*)(?:[.][0-9]+)?"
_QUANTITATIVE_SENTENCE = re.compile(
    r"At the queried (?P<resolution>[1-9][0-9]*) kb pixel, the mean "
    r"(?P<left_label>[A-Za-z][A-Za-z0-9_-]*) "
    r"(?P<measure>[A-Za-z][A-Za-z0-9 _/-]*?) is [*][*](?P<left_value>"
    + _NUMBER
    + r")[*][*], the mean (?P<right_label>[A-Za-z][A-Za-z0-9_-]*) "
    r"(?P=measure) is [*][*](?P<right_value>"
    + _NUMBER
    + r")[*][*], and the (?P<contrast_label>[A-Za-z][A-Za-z0-9_-]*) "
    r"difference is [*][*](?P<estimate>" + _NUMBER + r")[*][*] log2 units[.]"
)
_SAME_STRATUM_MEAN_SENTENCE = re.compile(
    r"For each replicate independently, I used the arithmetic mean of all other "
    r"(?P<resolution>[1-9][0-9]*) kb pixels at the same "
    r"(?P<stratum>[a-z0-9]+(?:-[a-z0-9]+)*) separation as the expected count[.]"
)
_TARGET_EXCLUSION_SENTENCE = re.compile(
    r"The focal pixel was left out(?: so that a true loop could not raise its own "
    r"expected value in this small matrix)?[.]"
)
_MAPPABILITY_EXCLUSION_SENTENCE = re.compile(
    r"Pairs incident to bins with mappability below (?P<threshold>"
    + _NUMBER
    + r") were excluded from the background[.]"
)
_SENSITIVITY_SENTENCES = (
    (
        "unfiltered_leave_one_out_mean",
        re.compile(
            r"An unfiltered leave-one-out mean gives case=(?P<case>"
            + _NUMBER
            + r"), control=(?P<control>"
            + _NUMBER
            + r"), and delta=(?P<delta>"
            + _NUMBER
            + r")[.]"
        ),
    ),
    (
        "quality_filtered_robust_median",
        re.compile(
            r"A robust median on the quality-filtered background gives case=(?P<case>"
            + _NUMBER
            + r"), control=(?P<control>"
            + _NUMBER
            + r"), and delta=(?P<delta>"
            + _NUMBER
            + r")[.]"
        ),
    ),
)


def inspect_markdown(path: Path, run_id: str, *, source_path: str | None = None) -> dict[str, Any]:
    logical_path = _logical_path(path, source_path)
    try:
        payload = path.read_bytes()
    except OSError as error:
        return _read_error_result(path, run_id, logical_path, error)
    digest = sha256_digest(payload)
    source_ref: dict[str, Any] = {
        "source_kind": "file_span",
        "locator": logical_path,
        "path": logical_path,
        "content_digest": digest,
    }
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return _decode_error_result(path, run_id, source_ref, digest)

    lines = text.splitlines()
    line_count = max(1, len(lines))
    source_ref.update(
        {
            "locator": f"{logical_path}:1-{line_count}",
            "start_line": 1,
            "end_line": line_count,
        }
    )
    nonempty = [
        {
            "start_line": index,
            "end_line": index,
            "start_column": len(line) - len(line.lstrip()) + 1,
            "end_column": len(line.rstrip()) + 1,
            "text": line.strip(),
        }
        for index, line in enumerate(lines, start=1)
        if line.strip() and not line.lstrip().startswith("#")
    ]
    explicit_directional_claims = [
        claim
        for span in nonempty
        if (claim := _explicit_directional_claim(span, source_ref)) is not None
    ]
    explicit_quantitative_claims = [
        claim
        for span in nonempty
        if (claim := _explicit_quantitative_claim(span, source_ref)) is not None
    ]
    expected_count_declarations = _expected_count_declarations(nonempty, source_ref)
    expected_count_sensitivities = _expected_count_sensitivities(nonempty, source_ref)
    opaque_constructs = [
        {
            "kind": "embedded_html",
            "reason": (
                "Embedded HTML is inventoried as text but its rendered semantics are not "
                "interpreted."
            ),
            "source_ref": {
                **source_ref,
                "locator": f"{logical_path}:{index}",
                "start_line": index,
                "end_line": index,
            },
        }
        for index, line in enumerate(lines, start=1)
        if line.lstrip().startswith("<") and ">" in line
    ]
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": stable_id("parser-result", logical_path, digest),
        "audit_run_id": run_id,
        "parser_id": "parser:markdown-inventory",
        "parser_version": _PARSER_VERSION,
        "source_ref": source_ref,
        "state": "parsed",
        "coverage_status": "partially_covered" if opaque_constructs else "covered",
        "emitted_record_refs": [],
        "syntax_issues": [],
        "opaque_constructs": opaque_constructs,
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": {
            "x-candidate-spans": nonempty,
            "x-explicit-directional-claims": explicit_directional_claims,
            "x-explicit-quantitative-claims": explicit_quantitative_claims,
            "x-expected-count-method-declarations": expected_count_declarations,
            "x-explicit-expected-count-sensitivities": expected_count_sensitivities,
        },
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": "parser:markdown-inventory"},
            "method": "static_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _read_error_result(
    path: Path, run_id: str, logical_path: str, error: OSError
) -> dict[str, Any]:
    source_ref = {"source_kind": "file_span", "locator": logical_path, "path": logical_path}
    return _error_result(
        path,
        run_id,
        source_ref,
        stable_id("parser-result", logical_path, type(error).__name__),
        f"Markdown source could not be read: {type(error).__name__}",
    )


def _decode_error_result(
    path: Path, run_id: str, source_ref: dict[str, Any], digest: str
) -> dict[str, Any]:
    return _error_result(
        path,
        run_id,
        source_ref,
        stable_id("parser-result", str(path), digest),
        "Markdown source is not valid UTF-8.",
    )


def _error_result(
    path: Path,
    run_id: str,
    source_ref: dict[str, Any],
    result_id: str,
    message: str,
) -> dict[str, Any]:
    return {
        "record_type": "parser_result",
        "schema_version": SCHEMA_VERSION,
        "parser_result_id": result_id,
        "audit_run_id": run_id,
        "parser_id": "parser:markdown-inventory",
        "parser_version": _PARSER_VERSION,
        "source_ref": source_ref,
        "state": "error",
        "coverage_status": "not_covered",
        "emitted_record_refs": [],
        "syntax_issues": [{"message": message, "source_ref": source_ref, "recoverable": True}],
        "opaque_constructs": [],
        "parser_disagreement": None,
        "started_at": _TIMESTAMP,
        "completed_at": _TIMESTAMP,
        "extensions": {
            "x-candidate-spans": [],
            "x-explicit-directional-claims": [],
            "x-explicit-quantitative-claims": [],
            "x-expected-count-method-declarations": [],
            "x-explicit-expected-count-sensitivities": [],
            "x-path": source_ref["path"],
        },
        "provenance": {
            "actor": {"actor_kind": "parser", "actor_id": "parser:markdown-inventory"},
            "method": "static_inventory",
            "created_at": _TIMESTAMP,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _logical_path(path: Path, source_path: str | None) -> str:
    value = source_path or path.name
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("source_path must be a safe repository-relative POSIX path")
    return candidate.as_posix()


def _explicit_directional_claim(
    span: dict[str, Any], source_ref: dict[str, Any]
) -> dict[str, Any] | None:
    text = str(span["text"])
    match = _DIRECTIONAL_SENTENCE.fullmatch(text)
    if match is None:
        return None
    verb = match.group("verb").lower()
    exact_ref = {
        **source_ref,
        "locator": f"{source_ref['path']}:{span['start_line']}",
        "start_line": span["start_line"],
        "end_line": span["end_line"],
        "start_column": span["start_column"],
        "end_column": span["end_column"],
        "quoted_text": text,
    }
    subject = match.group("subject")
    object_text = match.group("object")
    comparison = match.group("comparison")
    return {
        "text": text,
        "source_ref": exact_ref,
        "literal_subject": subject,
        "literal_predicate": f"{verb} {object_text}",
        "literal_object": object_text,
        "literal_comparison": f"{subject} versus {comparison}",
        "direction": "positive" if verb == "increased" else "negative",
        "extraction_basis": "bounded_directional_sentence_grammar_v1",
    }


def _explicit_quantitative_claim(
    span: dict[str, Any], source_ref: dict[str, Any]
) -> dict[str, Any] | None:
    text = str(span["text"])
    match = _QUANTITATIVE_SENTENCE.fullmatch(text)
    if match is None:
        return None
    left_label = match.group("left_label")
    right_label = match.group("right_label")
    if match.group("contrast_label") != f"{left_label}-minus-{right_label}":
        return None
    return {
        "text": text,
        "source_ref": _matched_source_ref(span, source_ref, match),
        "left_label": left_label,
        "right_label": right_label,
        "measure": match.group("measure"),
        "left_value_text": match.group("left_value"),
        "right_value_text": match.group("right_value"),
        "estimate_text": match.group("estimate"),
        "resolution_bp": int(match.group("resolution")) * 1_000,
        "unit": "log2 units",
        "extraction_basis": "bounded_expected_count_quantitative_sentence_v1",
    }


def _expected_count_declarations(
    spans: list[dict[str, Any]], source_ref: dict[str, Any]
) -> list[dict[str, Any]]:
    mean_matches = _all_matches(spans, _SAME_STRATUM_MEAN_SENTENCE)
    target_matches = _all_matches(spans, _TARGET_EXCLUSION_SENTENCE)
    mappability_matches = _all_matches(spans, _MAPPABILITY_EXCLUSION_SENTENCE)
    if not all(
        len(matches) == 1 for matches in (mean_matches, target_matches, mappability_matches)
    ):
        return []
    mean_span, mean_match = mean_matches[0]
    target_span, target_match = target_matches[0]
    mappability_span, mappability_match = mappability_matches[0]
    resolution_bp = int(mean_match.group("resolution")) * 1_000
    profile = build_expected_count_profile(
        estimator_family="same_stratum_arithmetic_mean",
        likelihood_family="not_applicable",
        link_function="not_applicable",
        background_scope="other_same_stratum_observations",
        grouping_structure="replicate_specific_background",
        covariate_terms=["distance", "mappability"],
        group_specific_terms=[],
        training_exclusions=["low_mappability", "target_observation"],
        target_excluded=True,
        analysis_resolution_bp=resolution_bp,
    )
    return [
        {
            "profile": profile,
            "source_refs": [
                _matched_source_ref(mean_span, source_ref, mean_match),
                _matched_source_ref(target_span, source_ref, target_match),
                _matched_source_ref(mappability_span, source_ref, mappability_match),
            ],
            "extraction_basis": "bounded_expected_count_report_profile_v1",
            "normalization_basis": {
                "distance": mean_match.group("stratum"),
                "mappability_threshold_text": mappability_match.group("threshold"),
            },
        }
    ]


def _expected_count_sensitivities(
    spans: list[dict[str, Any]], source_ref: dict[str, Any]
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for alternative, pattern in _SENSITIVITY_SENTENCES:
        matches = _all_matches(spans, pattern)
        if len(matches) != 1:
            continue
        span, match = matches[0]
        values.append(
            {
                "alternative": alternative,
                "values": {
                    "case": match.group("case"),
                    "control": match.group("control"),
                    "delta": match.group("delta"),
                },
                "source_ref": _matched_source_ref(span, source_ref, match),
                "extraction_basis": "bounded_expected_count_sensitivity_sentence_v1",
            }
        )
    return values


def _all_matches(
    spans: list[dict[str, Any]], pattern: re.Pattern[str]
) -> list[tuple[dict[str, Any], re.Match[str]]]:
    return [(span, match) for span in spans for match in pattern.finditer(str(span["text"]))]


def _matched_source_ref(
    span: dict[str, Any], source_ref: dict[str, Any], match: re.Match[str]
) -> dict[str, Any]:
    text = match.group(0)
    start_column = int(span["start_column"]) + match.start()
    return {
        **source_ref,
        "locator": f"{source_ref['path']}:{span['start_line']}",
        "start_line": span["start_line"],
        "end_line": span["end_line"],
        "start_column": start_column,
        "end_column": start_column + len(text),
        "quoted_text": text,
    }
