from __future__ import annotations

import ast
import hashlib
import json
import runpy
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.detectors import bounded_code_csv_multiple_testing_conflict_v2_3 as frozen_detector
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_adapter_v2_3 as frozen_adapter,
)
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_dataflow_v2_3 as frozen_dataflow,
)
from sc_referee.scientific_checks import integration_multiple_testing_v2_3 as frozen_integration
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import _CLOSED_REASONS
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3 import (
    analyze_record_model,
    strict_trigger_shapes,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_0/prototype-sweep")
_RESULTS = json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))
_HARNESS = runpy.run_path(str(_ROOT / "harness.py"))
_ADAPTER_HARNESS = runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")
_CORPUS_HARNESS = runpy.run_path(
    "evaluation/development/multitest-open-corpus-v1/adapter_replay.py"
)
_ALL_CASES = cast(Callable[[], tuple[Any, ...]], _HARNESS["all_cases"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _HARNESS["inputs"])
_CLASSIFY = cast(Callable[[MultipleTestingDataflowResult], Any], _HARNESS["classify"])
_ADAPTER = cast(
    Callable[[Path, bytes], dict[str, Any]],
    _ADAPTER_HARNESS["adapter_envelope"],
)
_CASES = {case.key: case for case in _ALL_CASES()}
_AUDIT_FIX_R1_ORACLE_PATH = Path(
    "evaluation/development/multitest-code-slice-v3_0/audit-fix-r1-oracle/EXPECTED_ROWS.json"
)
_AUDIT_FIX_R1_ORACLE = json.loads(_AUDIT_FIX_R1_ORACLE_PATH.read_text(encoding="utf-8"))
_AUDIT_FIX_R1_EXPECTED_ROWS = cast(list[dict[str, Any]], _AUDIT_FIX_R1_ORACLE["rows"])
_AUDIT_FIX_R1_SOURCES = (
    {
        "name": "correct-record-p-field-hand-bonferroni-augassign",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["p_value"] *= 7\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-alias-field-hand-bonferroni",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": "        alias = result\n"
        '        alias["p_value"] = min(1.0, result["p_value"] * 7)\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-unresolved-in-place-call",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": "        adjust_in_place(result)\n"
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-update-receiver-call",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result.update({"p_value": min(1.0, result["p_value"] * 7)})\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-pop-receiver-call",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result.pop("difference")\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-p-field-augassign",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["p_value"] += 0.5\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-field-delete",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        del result["difference"]\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-store-after-p-consumer",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        _seen = result["p_value"]\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    },
    {
        "name": "correct-record-store-after-append-consumer",
        "anchor": "        results.append((label, result))\n",
        "replacement": '        results.append((label, result))\n        result["extra"] = 1\n',
    },
    {
        "name": "correct-record-two-position-field-merge",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["significant"] = (\n'
        '            (results[0][1]["p_value"] if results else result["p_value"]) < ALPHA\n'
        "        )\n",
    },
    {
        "name": "correct-record-raw-adjusted-decision-merge",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["significant"] = (\n'
        '            (result["p_value"] < ALPHA)\n'
        "            if column == OUTCOMES[0][0]\n"
        '            else (min(1.0, result["p_value"] * 7) < ALPHA)\n'
        "        )\n",
    },
    {
        "name": "correct-record-incompatible-decision-polarity-merge",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["significant"] = (\n'
        '            (result["p_value"] < ALPHA)\n'
        "            if column == OUTCOMES[0][0]\n"
        '            else (result["p_value"] > ALPHA)\n'
        "        )\n",
    },
    {
        "name": "correct-record-unresolved-decision-merge",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["significant"] = (\n'
        '            (result["p_value"] < ALPHA)\n'
        "            if unresolved_choice(column)\n"
        '            else unresolved_decision(result["p_value"])\n'
        "        )\n",
    },
    {
        "name": "correct-record-two-threshold-decision-merge",
        "anchor": '        result["significant"] = result["p_value"] < ALPHA\n',
        "replacement": '        result["significant"] = (\n'
        '            (result["p_value"] < ALPHA)\n'
        "            if column == OUTCOMES[0][0]\n"
        '            else (result["p_value"] < 0.01)\n'
        "        )\n",
    },
)


class _PresentationTextMutation(ast.NodeTransformer):
    @staticmethod
    def _arm(node: ast.expr, marker: str) -> ast.expr:
        class _ArmMutation(ast.NodeTransformer):
            def visit_Constant(self, item: ast.Constant) -> ast.AST:
                if isinstance(item.value, str):
                    return ast.copy_location(
                        ast.Constant(marker * len(item.value)),
                        item,
                    )
                return item

        return cast(ast.expr, _ArmMutation().visit(node))

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST:
        node = cast(ast.IfExp, self.generic_visit(node))
        node.body = self._arm(node.body, "A")
        node.orelse = self._arm(node.orelse, "B")
        return node


def _run(case_key: str, source: bytes) -> list[object]:
    values = _INPUTS(_CASES[case_key], source)
    content = cast(bytes, values.pop("content"))
    return cast(
        list[object],
        _CLASSIFY(analyze_code_csv_multiple_testing_dataflow(content, **values)).as_json(),
    )


def _audit_fix_r1_source(fixture_name: str) -> tuple[str, bytes]:
    row = next(item for item in _AUDIT_FIX_R1_SOURCES if item["name"] == fixture_name)
    base = next(
        item for item in _RESULTS["fixtures"] if item["name"] == "positive-record-dict-flag-fold"
    )
    source = (_ROOT / base["source_path"]).read_text(encoding="utf-8")
    assert source.count(row["anchor"]) == 1, fixture_name
    return cast(str, base["case_key"]), source.replace(row["anchor"], row["replacement"]).encode()


def _adapter_case(case: Any, source: bytes) -> dict[str, Any]:
    if case.envelope is not None:
        return _ADAPTER(case.case_dir, source)
    with tempfile.TemporaryDirectory(prefix="sc-referee-mt30-fixture-", dir="/tmp") as raw:
        root = Path(raw)
        envelope_case = root / "case"
        project = envelope_case / "project"
        shutil.copytree(case.case_dir, project)
        (project / "analysis.py").write_bytes(source)
        prompt = Path("evaluation/development/multitest-open-corpus-v1/specs") / f"{case.role}.txt"
        (envelope_case / "PROMPT.txt").write_bytes(prompt.read_bytes())
        group_column, outcomes = cast(
            Callable[[Path], tuple[str, tuple[str, ...]]],
            _CORPUS_HARNESS["_authority"],
        )(case.case_dir)
        profile = cast(
            Callable[[str, tuple[str, ...]], dict[str, Any]],
            _CORPUS_HARNESS["_profile"],
        )(group_column, outcomes)
        (envelope_case / "profile_1_2_0.json").write_text(
            json.dumps(profile, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return _ADAPTER(envelope_case, source)


@pytest.mark.parametrize("row", _RESULTS["fixtures"], ids=lambda row: row["name"])
def test_all_48_record_model_fixtures_execute(row: dict[str, Any]) -> None:
    source = (_ROOT / row["source_path"]).read_bytes()
    assert hashlib.sha256(source).hexdigest() == row["source_sha256"]
    assert _run(row["case_key"], source) == row["outcome"]


def test_fixture_population_and_none_flip_counts_are_exact() -> None:
    fixtures = _RESULTS["fixtures"]
    assert len(fixtures) == 48
    assert sum(row["correct_analysis"] for row in fixtures) == 39
    assert sum(not row["correct_analysis"] for row in fixtures) == 9
    assert not [
        row
        for row in fixtures
        if row["correct_analysis"]
        and _run(row["case_key"], (_ROOT / row["source_path"]).read_bytes())[0] == "candidate"
    ]


@pytest.fixture(scope="module")
def fixture_adapter_rows() -> dict[str, dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = {}
    for row in _RESULTS["fixtures"]:
        case = _CASES[row["case_key"]]
        observed[row["name"]] = _adapter_case(
            case,
            (_ROOT / row["source_path"]).read_bytes(),
        )
    return observed


def test_all_48_fixtures_execute_through_the_real_adapter(
    fixture_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    for row in _RESULTS["fixtures"]:
        actual = fixture_adapter_rows[row["name"]]
        assert actual["outcome"] == row["outcome"][:2], row["name"]
        assert actual["finding_count"] == 0, row["name"]
        if row["outcome"][0] in {"candidate", "covered"}:
            coverage = row["outcome"][2]
            assert actual["corrected_positions"] == coverage["corrected_positions"]
            assert actual["authorized_count"] == coverage["authorized_count"]
        assert actual["candidate_records"] == (row["outcome"][0] == "candidate")


def test_fixture_none_flip_and_positive_control_adapter_counts_are_exact(
    fixture_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    correct = [row for row in _RESULTS["fixtures"] if row["correct_analysis"]]
    positive = [row for row in _RESULTS["fixtures"] if not row["correct_analysis"]]
    assert (len(correct), len(positive)) == (39, 9)
    assert not [
        row["name"]
        for row in correct
        if fixture_adapter_rows[row["name"]]["outcome"][0] == "candidate"
    ]
    assert all(fixture_adapter_rows[row["name"]]["outcome"][0] == "candidate" for row in positive)


@pytest.mark.parametrize(
    "row",
    [item for item in _RESULTS["fixtures"] if not item["correct_analysis"]],
    ids=lambda row: row["name"],
)
def test_each_admitted_model_is_structurally_idempotent(row: dict[str, Any]) -> None:
    source = (_ROOT / row["source_path"]).read_bytes()
    values = _INPUTS(_CASES[row["case_key"]], source)
    content = cast(bytes, values.pop("content"))
    first = analyze_record_model(content, **values)
    second = analyze_record_model(content, **values)
    assert first == second
    assert first.outcome.state == "candidate"
    assert first.outcome.reason_or_classification == row["outcome"][1]


def test_store_after_same_p_field_consumer_is_refused_even_without_position_overlap() -> None:
    row = next(
        item for item in _RESULTS["fixtures"] if item["name"] == "positive-record-dict-flag-fold"
    )
    source = (_ROOT / row["source_path"]).read_text(encoding="utf-8")
    source = source.replace(
        '        result["significant"] = result["p_value"] < ALPHA\n',
        "",
    ).replace(
        '        state = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"\n',
        '        state = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"\n'
        '        result["significant"] = result["p_value"] < ALPHA\n',
    )
    assert _run(row["case_key"], source.encode()) == [
        "abstain",
        "record-family-mutation-unresolved",
    ]


@pytest.mark.parametrize(
    "row",
    _AUDIT_FIX_R1_EXPECTED_ROWS,
    ids=lambda row: row["fixture_name"],
)
def test_all_14_audit_fix_round_1_record_refusals_execute(row: dict[str, Any]) -> None:
    case_key, source = _audit_fix_r1_source(row["fixture_name"])
    assert f"sha256:{hashlib.sha256(source).hexdigest()}" == row["fixture_source_sha256"]
    assert _run(case_key, source) == [row["expected_outcome"], row["expected_reason"]]


@pytest.fixture(scope="module")
def audit_fix_r1_adapter_rows() -> dict[str, dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = {}
    for row in _AUDIT_FIX_R1_EXPECTED_ROWS:
        case_key, source = _audit_fix_r1_source(row["fixture_name"])
        assert f"sha256:{hashlib.sha256(source).hexdigest()}" == row["fixture_source_sha256"]
        observed[row["fixture_name"]] = _adapter_case(_CASES[case_key], source)
    return observed


def test_all_14_audit_fix_round_1_refusals_execute_through_real_adapter(
    audit_fix_r1_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    assert len(_AUDIT_FIX_R1_EXPECTED_ROWS) == 14
    for row in _AUDIT_FIX_R1_EXPECTED_ROWS:
        actual = audit_fix_r1_adapter_rows[row["fixture_name"]]
        assert actual["outcome"] == [
            row["expected_outcome"],
            row["expected_reason"],
        ], row["fixture_name"]
        assert actual["candidate_records"] == 0, row["fixture_name"]
        assert actual["finding_count"] == 0, row["fixture_name"]


def test_fixture_matrix_names_all_62_fixtures_and_recounts_correct_analyses() -> None:
    matrix = json.loads(
        Path("evaluation/development/multitest-code-slice-v3/FIXTURE_MATRIX.json").read_text(
            encoding="utf-8"
        )
    )
    old_names = [row["name"] for row in _RESULTS["fixtures"]]
    new_names = [row["fixture_name"] for row in _AUDIT_FIX_R1_EXPECTED_ROWS]
    source_names = [row["name"] for row in _AUDIT_FIX_R1_SOURCES]
    assert source_names == new_names
    assert {row["expected_outcome"] for row in _AUDIT_FIX_R1_EXPECTED_ROWS} == {"abstain"}
    for row in _AUDIT_FIX_R1_EXPECTED_ROWS:
        derivation = row["derivation"]
        assert derivation["design_clause"].startswith(("§4.1", "§6.4"))
        assert derivation["design_text"]
        assert derivation["audit_probe_shape"]
    assert matrix["fixture_names"] == old_names + new_names
    assert matrix["audit_fix_round_1_expected_rows_source"] == {
        "path": str(_AUDIT_FIX_R1_ORACLE_PATH),
        "sha256": f"sha256:{hashlib.sha256(_AUDIT_FIX_R1_ORACLE_PATH.read_bytes()).hexdigest()}",
    }
    assert _AUDIT_FIX_R1_ORACLE["provenance"]["implementation_output_used"] is False
    assert _AUDIT_FIX_R1_ORACLE["provenance"]["design_revision"] == "1b"
    assert matrix["audit_fix_round_1_fixture_count"] == 14
    assert matrix["fixture_count"] == 62
    assert matrix["correct_fixture_count"] == 53
    assert matrix["positive_control_count"] == 9


def test_v3_closed_reason_registry_has_61_exact_members() -> None:
    additions = {
        "family-test-api-dispatch-unresolved",
        "multiple-registered-tests-for-family-member",
        "record-family-lineage-unresolved",
        "record-family-mutation-unresolved",
        "record-decision-polarity-unresolved",
        "record-duplicate-conclusion-ambiguous",
        "record-subset-position-unresolved",
        "dataframe-pvalue-table-unresolved",
    }
    assert len(_CLOSED_REASONS) == 61
    assert additions <= _CLOSED_REASONS
    assert "mixed-test-api-family" not in _CLOSED_REASONS


def test_frozen_2_3_anchor_bytes_are_unchanged() -> None:
    expected = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2_3.py": "70d8fd3c8f61e8726379c582e420700ea3babd0c45468e22b6f5b6f3b05dff28",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2_3.py": "e5c2a05e87fdec206460ccf73343e4dd158a7c311979208939f217a97f603023",
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2_3.py": "9de2e519e600546e2e57d4b29f0894375dcdd9455bdbf51bc951390a79f56e82",
        "src/sc_referee/scientific_checks/integration_multiple_testing_v2_3.py": "dfd23cdc5c87b894bff5ff147d77a3ee8418cd2a06cc9ba9af18bfebbcf4a1e7",
    }
    for path, digest in expected.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest

    case = _CASES["E13:P1:686d1432762cd49d9b54"]
    values = _INPUTS(case, None)
    content = cast(bytes, values.pop("content"))
    frozen = frozen_dataflow.analyze_code_csv_multiple_testing_dataflow(content, **values)
    assert cast(Any, _CLASSIFY)(frozen).as_json() == [
        "candidate",
        "none",
        {"authorized_count": 4, "corrected_positions": []},
    ]
    assert frozen_adapter.MULTIPLE_TESTING_CODE_ADAPTER_VERSION == "2.3.0"
    assert frozen_detector.BoundedCodeCsvMultipleTestingConflictV2_3Detector.detector_version == (
        "2.3.0"
    )
    assert frozen_integration.MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST.startswith(
        "sha256:"
    )


def test_v3_development_artifact_manifest_is_complete() -> None:
    root = Path("evaluation/development/multitest-code-slice-v3")
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["profile"] == "multitest-code-slice-v3-artifact-manifest-v1"
    assert set(manifest["files"]) == {
        "DEVELOPMENT_LEDGER.json",
        "FIXTURE_MATRIX.json",
        "ORACLE_MANIFEST.json",
        "TRIGGER_CENSUS.json",
    }
    for path, digest in manifest["files"].items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest


def test_trigger_shape_census_has_41_exact_rows_and_32_surviving_walls() -> None:
    expected_rows = _RESULTS["trigger_census"]["rows"]
    assert _RESULTS["trigger_census"]["count"] == 41
    observed: dict[str, tuple[str, ...]] = {}
    for row in expected_rows:
        case = _CASES[row["key"]]
        values = _INPUTS(case, None)
        content = cast(bytes, values["content"])
        observed[row["key"]] = strict_trigger_shapes(
            content,
            cast(tuple[str, ...], values["outcome_columns"]),
        )
        assert list(observed[row["key"]]) == row["trigger_shapes"], row["key"]
        if row["key"] != "E10:N7:6d2fdc67ab98bc0e0e6e":
            assert _run(row["key"], content) == row["outcome"], row["key"]
    assert len(observed) == 41
    assert sum(row["movement"] for row in expected_rows) == 9
    assert sum(not row["movement"] for row in expected_rows) == 32
    assert _run(
        "corpus:spec-22",
        _CASES["corpus:spec-22"].source_path.read_bytes(),
    ) == ["abstain", "authorized-family-test-census-incomplete"]
    assert _run(
        "corpus:spec-44",
        _CASES["corpus:spec-44"].source_path.read_bytes(),
    ) == ["abstain", "authorized-family-test-census-incomplete"]


def test_dataframe_population_is_nine_exact_cases_with_two_candidate_rows() -> None:
    expected = {
        "E10:N7:6d2fdc67ab98bc0e0e6e",
        "E11:P5:114782f595d9c24b923d",
        "E11:N3:479317f1706d4fb929e5",
        "E12:P1:f9ce4de5e21d9015ecd9",
        "E12:N1:45c4b9a19d0a630f1cb0",
        "E12:N2:f256af2f5c5d98f37e65",
        "E12:N3:678e94e79226936fd647",
        "E12:N9:62aa3748aa0c7c2607d3",
        "E14:N3:2327c03c4ddd02a36b97",
    }
    rows = [
        row
        for row in _RESULTS["trigger_census"]["rows"]
        if "dataframe-table" in row["trigger_shapes"]
    ]
    assert {row["key"] for row in rows} == expected
    assert {row["key"] for row in rows if row["outcome"][0] == "candidate"} == {
        "E11:P5:114782f595d9c24b923d",
        "E12:P1:f9ce4de5e21d9015ecd9",
    }


@pytest.mark.parametrize("row", _RESULTS["fixtures"], ids=lambda row: row["name"])
def test_record_predicates_are_invariant_to_prose_and_display_text(row: dict[str, Any]) -> None:
    source = (_ROOT / row["source_path"]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    tree = cast(ast.Module, _PresentationTextMutation().visit(tree))
    tree.body.insert(
        0,
        ast.Expr(
            ast.Constant("A report-only narrative with primary, score, and correction words.")
        ),
    )
    ast.fix_missing_locations(tree)
    mutated = "# narrative: significant exploratory score and Bonferroni\n" + ast.unparse(tree)
    assert _run(row["case_key"], mutated.encode()) == row["outcome"]
