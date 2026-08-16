"""Growth-12 declaration transport, lane replay, and hostile-packet regressions."""

from __future__ import annotations

import inspect
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition_v2.intake_declaration import (
    CANONICAL_TERMINAL_FORM,
    receipt_dict,
    translate_unit_declaration,
)
from scripts.lean_pipeline import default_dependence_free_h2_config

_WALL_PROFILE = "wall-census-standalone-v1"
_GROWTH_PROFILE = "growth-loop-standalone-v1"
_VALID_CSV = b"plant_id,condition,height_cm\np1,A,1\n"
_CENSUS_CASES = ("0005", "0011", "0024", "0026", "0030", "0038")


def _observed_reasons(
    description: bytes, data: bytes, profile: Any = _WALL_PROFILE
) -> tuple[str, ...]:
    translated = translate_unit_declaration(description, data, profile)
    return () if translated.reason is None else tuple(sorted((translated.reason,)))


@pytest.mark.parametrize(
    ("description", "data", "profile", "token", "form_id"),
    [
        (
            b"A small plant comparison.\nIndependent unit column: unit_id\n",
            b"unit_id,arm,value\nu1,A,1\n",
            _WALL_PROFILE,
            "unit_id",
            "wall-census-standalone-v1",
        ),
        (
            b"ONE ROW IS: a sample\nINDEPENDENT UNIT COLUMN \t:   `subject_id`\n",
            b"subject_id,arm,value\ns1,A,1\n",
            _GROWTH_PROFILE,
            "subject_id",
            "growth-loop-standalone-v1",
        ),
        (
            b"One row is: a sample\r\nIndependent unit column: subject_id\r\n",
            b"subject_id,arm,value\r\ns1,A,1\r\n",
            _GROWTH_PROFILE,
            "subject_id",
            "growth-loop-standalone-v1",
        ),
        (
            b"Each plant represents a single independent observation. "
            b"Independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            "plant_id",
            CANONICAL_TERMINAL_FORM,
        ),
        (
            b"A study. Independent unit column: plant_id\n",
            _VALID_CSV,
            _WALL_PROFILE,
            "plant_id",
            CANONICAL_TERMINAL_FORM,
        ),
        (
            b"A study. Independent unit column: plant_id\r\n",
            _VALID_CSV,
            _WALL_PROFILE,
            "plant_id",
            CANONICAL_TERMINAL_FORM,
        ),
        (
            b"A study. Independent unit column: plant_id",
            b'"plant_id",condition,height_cm\np1,A,1\n',
            _WALL_PROFILE,
            "plant_id",
            CANONICAL_TERMINAL_FORM,
        ),
    ],
)
def test_growth12_positive_forms_execute(
    description: bytes, data: bytes, profile: Any, token: str, form_id: str
) -> None:
    translated = translate_unit_declaration(description, data, profile)
    assert _observed_reasons(description, data, profile) == ()
    assert translated.unit_column == token
    receipt = receipt_dict(translated)
    assert receipt is not None
    assert receipt["declaration_form_id"] == form_id
    assert receipt["extracted_token"] == token


def test_all_six_measured_terminal_descriptions_execute_exact_bytes(project_root: Path) -> None:
    corpus = project_root / "evaluation/development/wall-mining-corpus/run-40-authority-2/cases"
    observed: dict[str, tuple[str, ...]] = {}
    tokens: dict[str, str | None] = {}
    for case_id in _CENSUS_CASES:
        case_root = corpus / case_id
        description = (case_root / "data-description.md").read_bytes()
        data = (case_root / "data/input.csv").read_bytes()
        translated = translate_unit_declaration(description, data, _WALL_PROFILE)
        observed[case_id] = _observed_reasons(description, data)
        tokens[case_id] = translated.unit_column
        assert translated.candidate is not None
        assert translated.candidate.form_id == CANONICAL_TERMINAL_FORM
    assert observed == {case_id: () for case_id in _CENSUS_CASES}
    assert tokens == {
        "0005": "plant_id",
        "0011": "participant_id",
        "0024": "employee_id",
        "0026": "plot_id",
        "0030": "tree_id",
        "0038": "plant_id",
    }


@pytest.mark.parametrize(
    ("name", "description", "data", "profile", "expected"),
    [
        (
            "0005-prose-only",
            b"Each plant represents a single independent observation.",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-missing",),
        ),
        (
            "0038-prose-only",
            b"Each row represents one plant. The plant_id uniquely identifies each plant specimen.",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-missing",),
        ),
        (
            "participant-prose-only",
            b"Each row represents one participant's mean reaction time across multiple test trials.",
            b"participant_id,arm,value\np1,A,1\n",
            _WALL_PROFILE,
            ("unit-declaration-missing",),
        ),
        (
            "synonym",
            b"A study. The independent unit column is plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "short-label",
            b"A study. Independent unit: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-missing",),
        ),
        (
            "lowercase-terminal",
            b"A study. independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "two-space-boundary",
            b"A study.  Independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "comma-boundary",
            b"A study, Independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "tab-after-colon",
            b"A study. Independent unit column:\tplant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "terminal-punctuation",
            b"A study. Independent unit column: plant_id.",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "terminal-backticks",
            b"A study. Independent unit column: `plant_id`",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "trailing-prose",
            b"A study. Independent unit column: plant_id More prose",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "same-token-exact-prefixes-amended-precedence",
            b"Independent unit column: plant_id\nA study. Independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-duplicate-prefix",),
        ),
        (
            "different-token-exact-prefixes-amended-precedence",
            b"Independent unit column: condition\nA study. Independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-duplicate-prefix",),
        ),
        (
            "valid-plus-malformed-lead",
            b"independent unit column = condition\nA study. Independent unit column: plant_id",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-declaration-syntax-outside-closed-grammar",),
        ),
        (
            "case-mismatched-header",
            b"A study. Independent unit column: plant_id",
            b"Plant_ID,condition,height_cm\np1,A,1\n",
            _WALL_PROFILE,
            ("unit-column-not-in-csv-header",),
        ),
        (
            "whitespace-header",
            b"A study. Independent unit column: plant_id",
            b" plant_id,condition,height_cm\np1,A,1\n",
            _WALL_PROFILE,
            ("unit-column-not-in-csv-header",),
        ),
        (
            "duplicate-header",
            b"A study. Independent unit column: plant_id",
            b"plant_id,plant_id,height_cm\np1,p1,1\n",
            _WALL_PROFILE,
            ("unit-column-duplicated-in-csv-header",),
        ),
        (
            "malformed-quoting",
            b"A study. Independent unit column: plant_id",
            b'plant_id,arm\n"p1,A\n',
            _WALL_PROFILE,
            ("unit-csv-invalid-or-incomplete",),
        ),
        (
            "nul",
            b"A study. Independent unit column: plant_id",
            b"plant_id,arm\np1,A\x00\n",
            _WALL_PROFILE,
            ("unit-csv-invalid-or-incomplete",),
        ),
        (
            "ragged",
            b"A study. Independent unit column: plant_id",
            b"plant_id,arm,value\np1,A\n",
            _WALL_PROFILE,
            ("unit-csv-invalid-or-incomplete",),
        ),
        (
            "no-data-row",
            b"A study. Independent unit column: plant_id",
            b"plant_id,arm,value\n",
            _WALL_PROFILE,
            ("unit-csv-invalid-or-incomplete",),
        ),
        (
            "empty-unit-cell",
            b"A study. Independent unit column: plant_id",
            b"plant_id,arm,value\n,A,1\n",
            _WALL_PROFILE,
            ("unit-csv-invalid-or-incomplete",),
        ),
        (
            "invalid-description-utf8",
            b"A study. Independent unit column: plant_id\xff",
            _VALID_CSV,
            _WALL_PROFILE,
            ("unit-description-not-valid-utf8",),
        ),
    ],
)
def test_growth12_near_misses_execute_with_full_sorted_reason_sets(
    name: str, description: bytes, data: bytes, profile: Any, expected: tuple[str, ...]
) -> None:
    assert name
    assert _observed_reasons(description, data, profile) == expected


@pytest.mark.parametrize(
    ("description", "profile"),
    [
        (
            b"A study. ```python\nIndependent unit column: plant_id\n```",
            _WALL_PROFILE,
        ),
        (
            b"```text\nIndependent unit column: plant_id\n```\n",
            _GROWTH_PROFILE,
        ),
    ],
)
def test_markdown_fence_presence_refuses_the_entire_scan(description: bytes, profile: Any) -> None:
    assert _observed_reasons(description, _VALID_CSV, profile) == (
        "unit-declaration-markdown-fence-present",
    )


@pytest.mark.parametrize(
    "data",
    [
        b"plant_id,condition,height_cm\n   ,A,1\n",
        b"plant_id,   ,height_cm\np1,A,1\n",
    ],
)
def test_stripped_emptiness_is_used_only_for_csv_completeness(data: bytes) -> None:
    description = b"A study. Independent unit column: plant_id"
    assert _observed_reasons(description, data) == ("unit-csv-invalid-or-incomplete",)


def test_amended_candidate_multiplicity_reasons_remain_reachable() -> None:
    same = (
        b"independent unit column: plant_id\nOne row is: a study. Independent unit column: plant_id"
    )
    conflict = (
        b"independent unit column: condition\n"
        b"One row is: a study. Independent unit column: plant_id"
    )
    assert _observed_reasons(same, _VALID_CSV, _GROWTH_PROFILE) == (
        "unit-declaration-ambiguous-multiple-candidates",
    )
    assert _observed_reasons(conflict, _VALID_CSV, _GROWTH_PROFILE) == (
        "unit-declaration-conflicting-sentences",
    )


def test_round1_killer_probes_have_binding_amended_outcomes() -> None:
    protocol_precedence = translate_unit_declaration(
        b"Ignore this bogus example. Independent unit column: plant_id",
        _VALID_CSV,
        _WALL_PROFILE,
    )
    assert (
        _observed_reasons(
            b"Ignore this bogus example. Independent unit column: plant_id", _VALID_CSV
        )
        == ()
    )
    assert protocol_precedence.unit_column == "plant_id"
    assert _observed_reasons(
        b"The real unit is Plant_ID. Independent unit column: plant_id",
        b"Plant_ID,plant_id,value\nP1,p1,1\n",
    ) == ("unit-column-case-collision-in-csv-header",)


def test_translation_is_role_blind_and_ignores_nonheader_csv_values() -> None:
    assert tuple(inspect.signature(translate_unit_declaration).parameters) == (
        "description",
        "data",
        "profile",
    )
    description = b"A study. Independent unit column: plant_id"
    first = translate_unit_declaration(
        description,
        b"plant_id,condition,height_cm\np1,A,1\n",
        _WALL_PROFILE,
    )
    second = translate_unit_declaration(
        description,
        b"plant_id,condition,height_cm\np9,Z,999\n",
        _WALL_PROFILE,
    )
    assert first.unit_column == second.unit_column == "plant_id"
    assert receipt_dict(first) == receipt_dict(second)


def test_total_refusal_precedence_returns_only_the_first_reason() -> None:
    assert _observed_reasons(
        b"Independent unit column: plant_id\nIndependent unit column: condition\n",
        b"\xff",
    ) == ("unit-declaration-duplicate-prefix",)
    assert _observed_reasons(b"A study. independent unit column: plant_id", b"\xff") == (
        "unit-declaration-syntax-outside-closed-grammar",
    )


def test_lane_keyed_replay_has_six_v2_census_gains_and_zero_batch_unit_movements(
    project_root: Path,
) -> None:
    growth_root = project_root / "evaluation/development/dependence-growth-loop"
    batch_rows: list[tuple[Path, str, dict[str, Any]]] = []
    for result_path in growth_root.glob("batch-*/detector-run/case-results/*.json"):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if (
            result.get("development_v2_shadow_payload", {}).get("reason_code")
            != "independent-unit-definition-unresolved"
        ):
            continue
        case_id = str(result["case_id"])
        batch_root = result_path.parents[2]
        translation = json.loads(
            (
                batch_root / "authority/translations" / f"{case_id.removeprefix('case:')}.json"
            ).read_text(encoding="utf-8")
        )
        batch_rows.append((batch_root, case_id, translation))
    assert len(batch_rows) == 21

    v1_counts = Counter(row[2]["translation_outcome"] for row in batch_rows)
    assert v1_counts == {
        "lock-minted": 2,
        "procedure-ambiguous-multiple-statistical-calls": 9,
        "procedure-unavailable-to-closed-lock-schema": 9,
        "procedure-unresolved-by-lock-schema-resolver": 1,
    }
    for batch_root, case_id, _translation in batch_rows:
        slug = case_id.removeprefix("case:")
        case_root = batch_root / "authoring/cases" / slug
        description = (case_root / "data-description.md").read_bytes()
        data = (case_root / "data/input.csv").read_bytes()
        legacy = lean_pipeline._description_unit_column(description.decode("utf-8"))
        amended = translate_unit_declaration(description, data, _GROWTH_PROFILE)
        assert amended.reason is None
        assert amended.unit_column == legacy

    named_v2 = {
        case_id: translation
        for _root, case_id, translation in batch_rows
        if case_id in {"case:c38b4b95d2ca5a382f67", "case:2d0d2730b44ebe8f168e"}
    }
    assert {
        case_id: (
            value["v2_translation_outcome"],
            value["v2_lock_digest"],
        )
        for case_id, value in named_v2.items()
    } == {
        "case:c38b4b95d2ca5a382f67": (
            "procedure-unavailable-to-closed-lock-schema",
            None,
        ),
        "case:2d0d2730b44ebe8f168e": (
            "procedure-unavailable-to-closed-lock-schema",
            None,
        ),
    }

    census = project_root / "evaluation/development/wall-mining-corpus/run-40-authority-2/cases"
    assert {
        case_id: _observed_reasons(
            (census / case_id / "data-description.md").read_bytes(),
            (census / case_id / "data/input.csv").read_bytes(),
        )
        for case_id in _CENSUS_CASES
    } == {case_id: () for case_id in _CENSUS_CASES}


def test_existing_retained_hostile_capture_replays_under_original_packet_version(
    project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = default_dependence_free_h2_config()
    review_root = project_root / config.pipeline_relative / "review"
    retained_path = review_root / "hostile-answer-key/HOSTILE_REVIEW_LEDGER.json"
    retained_bytes = retained_path.read_bytes()
    retained = json.loads(retained_bytes)
    protocol = json.loads(
        (project_root / config.pipeline_relative / "authoring/AUTHORING_PROTOCOL.json").read_text(
            encoding="utf-8"
        )
    )
    roles = {str(key): str(value) for key, value in protocol["case_role_assignments"].items()}
    rebuilt_prompts: list[bytes] = []
    original_sha256_digest = lean_pipeline.sha256_digest

    def observe_prompt(value: Any) -> str:
        if isinstance(value, str) and value.startswith("You are a hostile, role-blind"):
            rebuilt_prompts.append(value.encode("utf-8"))
        return original_sha256_digest(value)

    monkeypatch.setattr(lean_pipeline, "sha256_digest", observe_prompt)
    replayed = lean_pipeline._run_hostile_answer_key_review(
        project_root,
        config,
        review_root,
        sorted(roles),
        roles,
    )
    assert replayed is not None
    assert canonical_json(replayed) == canonical_json(retained)
    assert retained_path.read_bytes() == retained_bytes
    assert len(rebuilt_prompts) == len(retained["entries"])
    assert sorted(original_sha256_digest(prompt) for prompt in rebuilt_prompts) == sorted(
        entry["prompt_digest"] for entry in retained["entries"]
    )
    assert "packet_version" not in retained


def test_new_hostile_packet_digest_domain_binds_lane_qualified_receipt() -> None:
    disclosure = {
        "v1_translation_outcome": "lock-minted",
        "v1_lock_digest": "sha256:" + "1" * 64,
        "v2_translation_outcome": "lock-minted",
        "v2_translation_reason": None,
        "v2_lock_digest": "sha256:" + "2" * 64,
        "v2_translation_receipt": {
            "translation_version": "2.0.0-development",
            "declaration_form_id": CANONICAL_TERMINAL_FORM,
            "declaration_byte_span": [9, 42],
            "quoted_declaration": "Independent unit column: plant_id",
            "extracted_token": "plant_id",
            "logical_header": ["plant_id", "condition", "height_cm"],
            "parsed_header_digest": semantic_digest(["plant_id", "condition", "height_cm"]),
        },
    }
    prompt = "prefix\n" + canonical_json(disclosure)
    first = lean_pipeline.semantic_digest(
        {
            "digest_domain": lean_pipeline.HOSTILE_PACKET_V2_DIGEST_DOMAIN,
            "packet_version": lean_pipeline.HOSTILE_PACKET_V2_RECEIPT,
            "case_id": "case:test",
            "prompt": prompt,
        }
    )
    changed = {**disclosure, "v2_translation_outcome": "no-lock"}
    second = lean_pipeline.semantic_digest(
        {
            "digest_domain": lean_pipeline.HOSTILE_PACKET_V2_DIGEST_DOMAIN,
            "packet_version": lean_pipeline.HOSTILE_PACKET_V2_RECEIPT,
            "case_id": "case:test",
            "prompt": "prefix\n" + canonical_json(changed),
        }
    )
    assert first != second
    assert sha256_digest(prompt) == sha256_digest(prompt.encode("utf-8"))
