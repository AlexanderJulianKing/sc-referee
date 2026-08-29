from __future__ import annotations

import json
import runpy
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3 as frozen_v3
from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_1 as v3_1
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_1 import (
    CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    NONQUALIFYING_REASON_NAMES,
    QUALIFYING_REASON_NAMES,
    REASON_QUESTION_CLASS,
    build_scope_question_records,
    locate_correction_scope_witness,
    question_wording_profile,
)

_ORACLE_ROOT = Path("evaluation/development/multitest-code-slice-v3_1")
_ORACLE = json.loads((_ORACLE_ROOT / "QUESTION_ORACLE.json").read_text(encoding="utf-8"))
_QUESTION_ROWS = {row["key"]: row for row in _ORACLE["rows"]}
_FIXTURE_MATRIX = json.loads((_ORACLE_ROOT / "FIXTURE_MATRIX.json").read_text(encoding="utf-8"))
_HARNESS = runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")
_ENVELOPE_INPUTS = cast(Callable[[Path], dict[str, Any]], _HARNESS["envelope_inputs"])
_ADAPTER_ENVELOPE = cast(Callable[[Path, bytes], dict[str, Any]], _HARNESS["adapter_envelope"])
_CORPUS_AUTHORITY = cast(
    Callable[[Path], tuple[str, tuple[str, ...]]], _HARNESS["corpus_authority"]
)
_ROOTS = {
    "E10": Path("evaluation/development/blind-envelope-10-2026-08-24"),
    "E11": Path("evaluation/development/blind-envelope-11-2026-08-25"),
    "E12": Path("evaluation/development/blind-envelope-12-2026-08-26"),
    "E13": Path("evaluation/development/blind-envelope-13-2026-08-26"),
    "E14": Path("evaluation/development/blind-envelope-14-2026-08-27"),
    "E15": Path("evaluation/development/blind-envelope-15-2026-08-29"),
}
_CORPUS = Path("evaluation/development/multitest-open-corpus-v1")
_FROZEN_RESULTS = json.loads(
    Path("evaluation/development/multitest-code-slice-v3_0/prototype-sweep/results.json").read_text(
        encoding="utf-8"
    )
)
_FROZEN_ROWS = {row["key"]: row["outcome"] for row in _FROZEN_RESULTS["cases"]}


@pytest.fixture(scope="module")
def executed_140_case_census() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for envelope, root in _ROOTS.items():
        audit = json.loads((root / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
        for metadata in audit["cases"]:
            case = root / "cases" / metadata["case_id"]
            inputs = _ENVELOPE_INPUTS(case)
            content = cast(bytes, inputs.pop("content"))
            outcome_columns = cast(tuple[str, ...], inputs["outcome_columns"])
            key = f"{envelope}:{metadata['role']}:{metadata['case_id']}"
            if envelope == "E15":
                source_reason = (
                    metadata["dev_reason_or_classification"]
                    if metadata["dev_outcome"] == "abstain"
                    else None
                )
            else:
                frozen_outcome = _FROZEN_ROWS[key]
                source_reason = frozen_outcome[1] if frozen_outcome[0] == "abstain" else None
            witness = locate_correction_scope_witness(
                content,
                qualifying_reason=source_reason or "",
                authorized_count=len(outcome_columns),
                outcome_columns=outcome_columns,
            )
            rows[key] = {
                "content": content,
                "outcome_columns": outcome_columns,
                "source_reason": source_reason,
                "witness": witness,
            }
    for index in range(1, 51):
        spec = f"spec-{index:02d}"
        case = _CORPUS / "cases" / spec
        _group_column, outcome_columns = _CORPUS_AUTHORITY(case)
        frozen_outcome = _FROZEN_ROWS[f"corpus:{spec}"]
        source_reason = frozen_outcome[1] if frozen_outcome[0] == "abstain" else None
        content = (case / "analysis.py").read_bytes()
        witness = locate_correction_scope_witness(
            content,
            qualifying_reason=source_reason or "",
            authorized_count=len(outcome_columns),
            outcome_columns=outcome_columns,
        )
        rows[f"corpus:{spec}"] = {
            "content": content,
            "outcome_columns": outcome_columns,
            "source_reason": source_reason,
            "witness": witness,
        }
    assert len(rows) == 140
    return rows


def test_reason_sets_are_closed_and_recounted() -> None:
    assert len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) == 61
    assert QUALIFYING_REASON_NAMES == {
        "correction-family-lineage-unresolved",
        "record-family-lineage-unresolved",
        "record-family-mutation-unresolved",
        "unresolved-decision-threshold",
        "unresolved-manual-correction-present",
    }
    assert NONQUALIFYING_REASON_NAMES == (
        CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS - QUALIFYING_REASON_NAMES
    )
    assert len(NONQUALIFYING_REASON_NAMES) == 56
    assert set(REASON_QUESTION_CLASS) == CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS
    assert {
        reason
        for reason, classification in REASON_QUESTION_CLASS.items()
        if classification == "correction_scope_witness_required"
    } == QUALIFYING_REASON_NAMES
    assert {classification for classification in REASON_QUESTION_CLASS.values()} == {
        "correction_scope_witness_required",
        "not_correction_scope_question",
    }


def test_frozen_v3_anchor_bytes_are_unchanged() -> None:
    expected = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3.py": "sha256:498bf5c22305270fe64ed1ef73b7ac8a7a2637ce4f64520e8d9ca4ac15166618",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3.py": "sha256:f9f96c6e4bf861d9c186cb19685c74723d5fc6f9da4fcd1eaaada14d39230534",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3.py": "sha256:cddc845c2f404938ab86b8d87a79b4eb763090dfdfbb33854038998520728f53",
        "src/sc_referee/scientific_checks/integration_multiple_testing_v3.py": "sha256:1a340ab3b124994c88dbf7c08e21be11a8c2795198afc49a182ff8abcc74ac47",
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3.py": "sha256:3284e70646d48039f42d2bcf6790c92910de43785f3d03701e5b6cf1ac1eb437",
        "docs/implementation/MULTITEST-CODE-SLICE-3.0-RECORD-MODEL-DESIGN-2026-08-28.md": "sha256:e950b6015198c92e7f7f16d30f901be9f131c0145e96524a22df4e33ed6ec166",
        "evaluation/development/multitest-code-slice-v3_0/prototype-sweep/results.json": "sha256:762d6e7a5ee563c1f36bfecd1d3a8e9ac97ca943defd7a80f823ca3b5824e18b",
        "evaluation/development/blind-envelope-15-2026-08-29/AUDIT_RESULTS.json": "sha256:ad0b30b8ebdf6d4a799628b5a6eb37ac7742d93f441ec604a0d6b81a34db142e",
        "tests/test_multiple_testing_opened_envelopes_v3.py": "sha256:4901d301b3601b1fa7e3cb210cbb11dbe2404c27f885f1cb54f7da48931062a1",
        "tests/test_multiple_testing_open_corpus_v3.py": "sha256:ce9d14ea55c8746c3f40813f71690d91c5826b86a9f224b8b4ff3d784310a7bf",
        "tests/test_code_csv_multiple_testing_record_model_v3.py": "sha256:8bf778b83ec5030940e9406f524e94b9c54a0c23c646ddda76f3786b7fc08a8f",
        "evaluation/development/multitest-code-slice-v3_0/audit-fix-r1-oracle/EXPECTED_ROWS.json": "sha256:d3376525fa208c01b03efb7832d56ee2aa5ac939c299ceeeef35ed894ff6abb7",
        "evaluation/development/multitest-code-slice-v3_0/audit-fix-r2-oracle/EXPECTED_ROWS.json": "sha256:c189f2bb59bb8e84a59016dbaca1fd8315963551053523743eb56060c8a4f111",
        "evaluation/development/multitest-code-slice-v3_0/audit-fix-r3-oracle/EXPECTED_ROWS.json": "sha256:99a1a3d39f4956fbd95dc710ff3aa03496920ddf32e94c32ef5f5d2ec4365d2a",
        "evaluation/development/multitest-open-corpus-v1/adapter_replay_records_v2_1.json": "sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502",
        "evaluation/development/blind-envelope-12-2026-08-26/adapter_replay_records_v2_2.json": "sha256:f8b7808b3baee264e9c496e2e899686af235e72c37b9647ce4255d10adbb02d8",
        "evaluation/development/blind-envelope-13-2026-08-26/adapter_replay_records_v2_3.json": "sha256:d171c40e0715ff2b0f4c65bb667e817b78575ea1f2d73a8bc9af0869d3143489",
    }
    assert {path: sha256_digest(Path(path).read_bytes()) for path in expected} == expected


def test_frozen_v3_source_analysis_is_the_exact_v3_1_delegate() -> None:
    assert (
        v3_1.analyze_code_csv_multiple_testing_dataflow
        is frozen_v3.analyze_code_csv_multiple_testing_dataflow
    )


def test_executed_140_case_question_census_matches_independent_oracle(
    executed_140_case_census: dict[str, dict[str, Any]],
) -> None:
    observed = {key for key, row in executed_140_case_census.items() if row["witness"] is not None}
    assert observed == set(_QUESTION_ROWS)
    assert sum(key.startswith("E") for key in observed) == 14
    assert sum(key.startswith("corpus:") for key in observed) == 10
    assert "E15:P3:afe47b2a7ea87ed21a69" not in observed

    reasons: Counter[str] = Counter()
    for key, expected in _QUESTION_ROWS.items():
        row = executed_140_case_census[key]
        witness = row["witness"]
        assert witness is not None
        assert sha256_digest(row["content"]) == expected["source_sha256"]
        assert row["source_reason"] == expected["reason"]
        assert len(row["outcome_columns"]) == expected["authorized_count"]
        assert witness.witness_kind == expected["witness_kind"]
        assert witness.source_span.to_dict() == expected["source_span"]
        assert witness.qualifying_reason == expected["reason"]
        reasons[expected["reason"]] += 1
    assert reasons == {
        "correction-family-lineage-unresolved": 6,
        "record-family-mutation-unresolved": 1,
        "unresolved-decision-threshold": 9,
        "unresolved-manual-correction-present": 8,
    }
    assert tuple(
        reasons[name]
        for name in (
            "correction-family-lineage-unresolved",
            "record-family-lineage-unresolved",
            "record-family-mutation-unresolved",
            "unresolved-decision-threshold",
            "unresolved-manual-correction-present",
        )
    ) == (6, 0, 1, 9, 8)


def test_question_records_use_only_the_closed_two_slots(
    executed_140_case_census: dict[str, dict[str, Any]],
) -> None:
    row = executed_140_case_census["E13:N1:b7d38f6e9284abfd3ee6"]
    witness = row["witness"]
    assert witness is not None
    records = build_scope_question_records(
        witness,
        run_id="audit:question-wording-test",
        created_at="2026-08-29T00:00:00Z",
        source_snapshot_digest="sha256:" + "1" * 64,
        authority_binding_digest="sha256:" + "2" * 64,
        analysis_ref={"record_type": "file_record", "record_id": "file:analysis"},
        contract_ref={
            "record_type": "scientific_contract",
            "record_id": "scientific-contract:mt",
        },
        detector_manifest_digest="sha256:" + "3" * 64,
    )
    profile = question_wording_profile()
    question = records.question
    visible_wording = canonical_json(
        {
            "question": question["question"],
            "why_it_matters": question["why_it_matters"],
            "candidate_answers": question["candidate_answers"],
            "evidence_searched": question["evidence_searched"],
        }
    )
    assert profile["slots"] == ["AUTHORIZED_COUNT", "SOURCE_LOCATION"]
    assert question["question"] == "Does this correction cover all 5 declared outcomes?"
    assert "analysis.py:79:39" in question["why_it_matters"]
    assert question["extensions"]["x-authorized-count"] == 5
    assert "correction-family-lineage-unresolved" not in visible_wording
    source_text = row["content"].decode("utf-8")
    assert "multipletests(raw_p_values)" not in visible_wording
    assert source_text not in visible_wording
    assert records.detector_result["state"] == "material_question_candidate"
    assert records.concern["condition"]["premise_state"] == "unknown"


def test_question_identity_and_evidence_exclude_run_time_and_output_identity(
    executed_140_case_census: dict[str, dict[str, Any]],
) -> None:
    row = executed_140_case_census["E13:N1:b7d38f6e9284abfd3ee6"]
    witness = row["witness"]
    assert witness is not None

    def records(run_id: str, created_at: str) -> Any:
        return build_scope_question_records(
            witness,
            run_id=run_id,
            created_at=created_at,
            source_snapshot_digest="sha256:" + "1" * 64,
            authority_binding_digest="sha256:" + "2" * 64,
            analysis_ref={"record_type": "file_record", "record_id": "file:analysis"},
            contract_ref={
                "record_type": "scientific_contract",
                "record_id": "scientific-contract:mt",
            },
            detector_manifest_digest="sha256:" + "3" * 64,
        )

    first = records("audit:first-output", "2026-08-29T00:00:00Z")
    second = records("audit:second-output", "2031-01-01T12:34:56Z")
    assert first.question["question_id"] == second.question["question_id"]
    assert (
        first.question["extensions"]["x-question-evidence-digest"]
        == second.question["extensions"]["x-question-evidence-digest"]
    )


def test_e15_p3_reason_without_a_structural_witness_emits_no_question(
    executed_140_case_census: dict[str, dict[str, Any]],
) -> None:
    row = executed_140_case_census["E15:P3:afe47b2a7ea87ed21a69"]
    assert row["source_reason"] == "unresolved-manual-correction-present"
    assert row["witness"] is None


def test_all_fifteen_e15_source_rows_remain_the_sealed_adapter_rows() -> None:
    root = _ROOTS["E15"]
    audit = json.loads((root / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    observed: dict[str, list[str]] = {}
    for row in audit["cases"]:
        case = root / "cases" / row["case_id"]
        actual = _ADAPTER_ENVELOPE(case, (case / "project/analysis.py").read_bytes())
        expected = [row["dev_outcome"], row["dev_reason_or_classification"]]
        if row["dev_outcome"] == "covered_complete":
            expected = ["covered", "complete"]
        assert actual["outcome"] == expected, row["case_id"]
        assert actual["finding_count"] == 0, row["case_id"]
        observed[row["case_id"]] = actual["outcome"]
    assert len(observed) == 15


@pytest.mark.parametrize(
    ("source", "reason", "expected"),
    [
        (
            "p = scipy.stats.ttest_ind(a, b).pvalue\nx = p * 5\nprint(x < 0.05)\n",
            "unresolved-manual-correction-present",
            "manual-adjusted-p-arithmetic",
        ),
        (
            "p = scipy.stats.ttest_ind(a, b).pvalue\n"
            "result = {'p_value': p}\n"
            "result['p_adjusted'] = min(1.0, result['p_value'] * 5)\n"
            "print(result['p_adjusted'] < 0.05)\n",
            "record-family-lineage-unresolved",
            "record-correction-store",
        ),
        (
            "p = scipy.stats.ttest_ind(a, b).pvalue\n"
            "result = {'p_value': p}\n"
            "result['p_value'] = min(1.0, result['p_value'] * 5)\n"
            "print(result['p_value'] < 0.05)\n",
            "record-family-mutation-unresolved",
            "record-correction-store",
        ),
    ],
)
def test_isolated_manual_and_record_witnesses(source: str, reason: str, expected: str) -> None:
    witness = locate_correction_scope_witness(
        source.encode(),
        qualifying_reason=reason,
        authorized_count=5,
        outcome_columns=("o1", "o2", "o3", "o4", "o5"),
    )
    assert witness is not None
    assert witness.witness_kind == expected


def test_independent_named_question_fixture_matrix_is_exact() -> None:
    rows = _FIXTURE_MATRIX["rows"]
    assert len(rows) == 16
    observed_reasons: set[str] = set()
    observed_names: set[str] = set()
    for row in rows:
        source_path = (_ORACLE_ROOT / row["source_path"]).resolve()
        content = source_path.read_bytes()
        assert sha256_digest(content) == row["source_sha256"], row["name"]
        witness = locate_correction_scope_witness(
            content,
            qualifying_reason=row["reason"],
            authorized_count=5,
            outcome_columns=tuple(_FIXTURE_MATRIX["outcome_columns"]),
        )
        expected_kind = row["expected_witness_kind"]
        assert (None if witness is None else witness.witness_kind) == expected_kind, row["name"]
        observed_names.add(row["name"])
        if witness is not None:
            observed_reasons.add(witness.qualifying_reason)
    assert len(observed_names) == len(rows)
    assert observed_reasons == QUALIFYING_REASON_NAMES


def test_independent_v3_1_evaluation_manifest_is_complete() -> None:
    manifest = json.loads((_ORACLE_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    expected_paths = {
        path.relative_to(_ORACLE_ROOT).as_posix()
        for path in _ORACLE_ROOT.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    rows = {row["path"]: row for row in manifest["files"]}
    assert manifest["file_count"] == len(expected_paths) == 19
    assert set(rows) == expected_paths
    for relative, row in rows.items():
        payload = (_ORACLE_ROOT / relative).read_bytes()
        assert sha256_digest(payload)[7:] == row["sha256"]
        assert len(payload) == row["size_bytes"]


@pytest.mark.parametrize(
    "expression",
    [
        "p * 5",
        "5 * p",
        "min(p * 5, 1)",
        "min(5 * p, 1.0)",
        "min(1, p * 5)",
        "min(1.0, 5 * p)",
        "np.minimum(p * 5, 1)",
        "np.minimum(5 * p, 1.0)",
        "np.minimum(1, p * 5)",
        "np.minimum(1.0, 5 * p)",
        "p * len(OUTCOMES)",
    ],
)
def test_every_manual_adjustment_production_is_admitted(expression: str) -> None:
    source = (
        "import numpy as np\nfrom scipy import stats\n"
        "OUTCOMES = ['m1', 'm2', 'm3', 'm4', 'm5']\n"
        "p = stats.ttest_ind(a, b).pvalue\n"
        f"adjusted = {expression}\nprint(adjusted < 0.05)\n"
    )
    witness = locate_correction_scope_witness(
        source.encode(),
        qualifying_reason="unresolved-manual-correction-present",
        authorized_count=5,
        outcome_columns=("m1", "m2", "m3", "m4", "m5"),
    )
    assert witness is not None
    assert witness.witness_kind == "manual-adjusted-p-arithmetic"


@pytest.mark.parametrize(
    "expression",
    [
        "p / 5",
        "p + 5",
        "p ** 5",
        "min(p * 5, 0.9)",
        "max(p * 5, 1.0)",
        "np.clip(p * 5, 0.0, 1.0)",
        "p * len(results)",
        "p * make_factor()",
        "p * (2 + 3)",
    ],
)
def test_manual_adjustment_near_neighbors_are_refused(expression: str) -> None:
    source = (
        "import numpy as np\nfrom scipy import stats\n"
        "results = [1, 2, 3, 4, 5]\n"
        "def make_factor():\n    return 5\n"
        "p = stats.ttest_ind(a, b).pvalue\n"
        f"adjusted = {expression}\nprint(adjusted < 0.05)\n"
    )
    assert (
        locate_correction_scope_witness(
            source.encode(),
            qualifying_reason="unresolved-manual-correction-present",
            authorized_count=5,
            outcome_columns=("m1", "m2", "m3", "m4", "m5"),
        )
        is None
    )


@pytest.mark.parametrize(
    ("threshold", "comparison"),
    [
        ("ALPHA / 5", "p < threshold"),
        ("ALPHA / len(OUTCOMES)", "threshold >= p"),
        ("1 - (1 - ALPHA) ** (1 / 5)", "p <= threshold"),
        ("1 - (1 - ALPHA) ** (1 / len(OUTCOMES))", "threshold > p"),
    ],
)
def test_every_manual_threshold_production_and_reversed_order_is_admitted(
    threshold: str, comparison: str
) -> None:
    source = (
        "from scipy import stats\nALPHA = 5e-2\n"
        "OUTCOMES = ['m1', 'm2', 'm3', 'm4', 'm5']\n"
        "p = stats.ttest_ind(a, b).pvalue\n"
        f"threshold = {threshold}\nprint({comparison})\n"
    )
    witness = locate_correction_scope_witness(
        source.encode(),
        qualifying_reason="unresolved-decision-threshold",
        authorized_count=5,
        outcome_columns=("m1", "m2", "m3", "m4", "m5"),
    )
    assert witness is not None
    assert witness.witness_kind == "manual-decision-threshold-arithmetic"
    assert witness.threshold_operator in {"<", "<=", ">", ">="}


@pytest.mark.parametrize(
    "setup",
    [
        "threshold = 0.01",
        "threshold = ALPHA / (2 + 3)",
        "threshold = ALPHA / len(results)",
        "threshold = make_threshold()",
        "threshold = ALPHA / 5\nALPHA = 0.1",
        "if choose:\n    threshold = ALPHA / 5",
    ],
)
def test_manual_threshold_near_neighbors_and_rebindings_are_refused(setup: str) -> None:
    source = (
        "from scipy import stats\nALPHA = 0.05\nresults = [1, 2, 3, 4, 5]\n"
        "def make_threshold():\n    return 0.01\n"
        "p = stats.ttest_ind(a, b).pvalue\n"
        f"{setup}\nprint(p < threshold)\n"
    )
    assert (
        locate_correction_scope_witness(
            source.encode(),
            qualifying_reason="unresolved-decision-threshold",
            authorized_count=5,
            outcome_columns=("m1", "m2", "m3", "m4", "m5"),
        )
        is None
    )


def test_prose_and_noncallee_identifier_tripwire_does_not_create_a_witness() -> None:
    base = (
        "bonferroni = 'report label'\n"
        "holm = 'another label'\n"
        "sidak = 'display only'\n"
        "benjamini_hochberg = 'display only'\n"
        "print('correction covers every result')\n"
    )
    mutated = "'''The report says primary and exploratory correction.'''\n" + base.replace(
        "report label", "manual correction report label"
    )
    for source in (base, mutated):
        assert (
            locate_correction_scope_witness(
                source.encode(),
                qualifying_reason="unresolved-manual-correction-present",
                authorized_count=5,
                outcome_columns=("o1", "o2", "o3", "o4", "o5"),
            )
            is None
        )


def test_positive_prose_noncallee_and_numeric_spelling_tripwire_is_structural() -> None:
    base = (
        "from scipy import stats\n"
        "p = stats.ttest_ind(a, b).pvalue\n"
        "adjusted = min(1.0, p * 5)\n"
        "print(adjusted < 0.05)\n"
    )
    mutated = (
        "'''Bonferroni and Holm report prose.'''\n"
        "from scipy import stats\n"
        "bonferroni = stats.ttest_ind(a, b).pvalue\n"
        "holm = min(1.00, bonferroni * 5)\n"
        "print('primary exploratory correction', holm < 5e-2)\n"
    )

    def projection(source: str) -> tuple[str, str | None, int | None]:
        witness = locate_correction_scope_witness(
            source.encode(),
            qualifying_reason="unresolved-manual-correction-present",
            authorized_count=5,
            outcome_columns=("m1", "m2", "m3", "m4", "m5"),
        )
        assert witness is not None
        return witness.witness_kind, witness.factor_kind, witness.factor_value

    assert (
        projection(base)
        == projection(mutated)
        == (
            "manual-adjusted-p-arithmetic",
            "literal_multiplier",
            5,
        )
    )


def test_paired_callee_terminal_and_structural_deletion_controls() -> None:
    prefix = "from scipy import stats\nimport package as pg\np = stats.ttest_ind(a, b).pvalue\n"
    matched = prefix + "pg.multicomp([p])\n"
    renamed = prefix + "pg.multi_comp([p])\n"
    deleted = "import package as pg\npg.multicomp([0.1])\n"
    witness = locate_correction_scope_witness(
        matched.encode(),
        qualifying_reason="unresolved-manual-correction-present",
        authorized_count=5,
        outcome_columns=("m1", "m2", "m3", "m4", "m5"),
    )
    assert witness is not None
    assert witness.witness_kind == "closed-terminal-correction-call"
    for source in (renamed, deleted):
        assert (
            locate_correction_scope_witness(
                source.encode(),
                qualifying_reason="unresolved-manual-correction-present",
                authorized_count=5,
                outcome_columns=("m1", "m2", "m3", "m4", "m5"),
            )
            is None
        )
