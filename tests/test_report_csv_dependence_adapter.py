from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.detectors.method_conflict_finding import (
    _CODE_DEPENDENCE_SLOT_SCHEMA,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST,
    CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID,
    _code_dependence_row_entry_facts,
    draft_method_conflict_finding,
)
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_checks.core import InspectionDocument, RecordRef
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from sc_referee.scientific_checks.report_csv_dependence_adapter import (
    _inspect_report,
    _parse_csv,
)
from sc_referee.scientific_requirement_contract import (
    LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
    ScientificRequirementContractError,
    resolve_scientific_requirement_profile,
)

CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
CANDIDATE_ID = "one-analyzed-row-per-authorized-independent-unit"


def _profile(unit: str, group: str) -> dict[str, object]:
    return {
        "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
        "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
        "check_id": CHECK_ID,
        "candidate_id": CANDIDATE_ID,
        "semantic_role_authority": {
            "authorized_independent_unit_key": {
                "material_input_path": "data/input.csv",
                "column_name": unit,
                "group_contrast_column": group,
            }
        },
    }


def _document(text: str) -> InspectionDocument:
    content = text.encode("utf-8")
    return InspectionDocument(
        path="results/report.md",
        file_ref=RecordRef("file_record", "file:report"),
        content=content,
        content_digest=sha256_digest(content),
        media_type="text/markdown",
        parser_result_ref=RecordRef("parser_result", "parser-result:report"),
        parser_result_payload=b'{"parser_id":"parser:markdown-inventory","parser_version":"0.2.0","state":"parsed"}',
        parser_result_digest=sha256_digest(
            b'{"parser_id":"parser:markdown-inventory","parser_version":"0.2.0","state":"parsed"}'
        ),
    )


def test_d1_prime_excludes_high_cardinality_columns_and_keeps_label_collision() -> None:
    accepted = _parse_csv(
        b"unit,group,visit,response\nA,x,1,10\nA,x,2,11\nB,y,1,20\nB,y,2,21\n",
        "unit",
        "group",
    )
    assert not isinstance(accepted, str)
    assert accepted.candidate_columns == ("visit",)
    assert accepted.distinct_excluded_columns == ("response",)
    assert accepted.within_unit_index_columns == ("visit",)
    assert accepted.unique_nonindex_columns == ()

    collision = _parse_csv(
        b"colony,group,site,response\nA,x,north,10\nA,x,south,11\nB,y,north,20\n",
        "colony",
        "group",
    )
    assert not isinstance(collision, str)
    assert collision.candidate_columns == ("site",)
    assert collision.unique_nonindex_columns == ("site",)


@pytest.mark.parametrize(
    ("case_id", "batch", "unit", "group", "candidates", "excluded", "within"),
    [
        (
            "0de3a6061d3bb4056306",
            "batch-k1",
            "plot_id",
            "management",
            ("visit",),
            ("ch4_flux_mg_m2_h", "water_table_cm"),
            ("visit",),
        ),
        (
            "6b2da0c7167dbba3738f",
            "batch-k1",
            "reactor_id",
            "carbon_source",
            ("run_day",),
            ("nitrate_removal_mg_n_per_l_per_h",),
            ("run_day",),
        ),
        (
            "e9e2718573bb47f7d17b",
            "batch-k1",
            "colony_id",
            "reef_zone",
            ("depth_m",),
            ("nubbin_code", "symbiont_density_e6_per_cm2"),
            (),
        ),
        (
            "3ae92d0bb421d6eee99e",
            "batch-k2",
            "plot_id",
            "water_table_regime",
            ("survey_round",),
            ("ch4_flux_mg_m2_h", "chamber_temp_c"),
            ("survey_round",),
        ),
    ],
)
def test_d1_prime_exact_batch_k_column_classification(
    case_id: str,
    batch: str,
    unit: str,
    group: str,
    candidates: tuple[str, ...],
    excluded: tuple[str, ...],
    within: tuple[str, ...],
) -> None:
    path = (
        Path("evaluation/development/dependence-growth-loop")
        / batch
        / "authoring/cases"
        / case_id
        / "data/input.csv"
    )
    result = _parse_csv(path.read_bytes(), unit, group)
    assert not isinstance(result, str)
    assert result.candidate_columns == candidates
    assert result.distinct_excluded_columns == excluded
    assert result.within_unit_index_columns == within
    assert result.unique_nonindex_columns == ()


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        (b"\xef\xbb\xbfunits,group\nA,x\nA,x\n", "unsupported-csv-encoding"),
        (b"units,group\nA,x\x00\nA,x\n", "unsupported-csv-encoding"),
        (b"units,group\rA,x\rA,x\r", "unsupported-csv-newline"),
        (b"units,units,group\nA,A,x\nA,A,x\n", "malformed-csv-domain"),
        (b"units,,group\nA,1,x\nA,2,x\n", "malformed-csv-domain"),
        (b"units,group\nA,x\nA\n", "malformed-csv-domain"),
        (b"units,group\n,x\nA,x\n", "missing-or-trimmed-authorized-unit"),
        (b"units,group\n A,x\nA,x\n", "missing-or-trimmed-authorized-unit"),
        (b"units,group\nA,x\nB,y\n", "no-repeated-authorized-unit"),
    ],
)
def test_csv_fail_closed_matrix(content: bytes, reason: str) -> None:
    assert _parse_csv(content, "units", "group") == reason


def test_csv_row_column_and_field_limit_boundaries() -> None:
    one_row = b"unit,group\nA,x\n"
    two_rows = b"unit,group\nA,x\nA,x\n"
    assert _parse_csv(one_row, "unit", "group") == "csv-row-count-outside-bound"
    assert _parse_csv(two_rows, "unit", "group") != "csv-row-count-outside-bound"

    at_row_limit = (
        "unit,group\n" + "".join(f"{'A' if index % 2 == 0 else 'B'},x\n" for index in range(100000))
    ).encode()
    above_row_limit = at_row_limit + b"A,x\n"
    assert not isinstance(_parse_csv(at_row_limit, "unit", "group"), str)
    assert _parse_csv(above_row_limit, "unit", "group") == "csv-row-count-outside-bound"

    columns = ["unit", "group", *(f"c{index}" for index in range(510))]
    row = ["A", "x", *("v" for _ in range(510))]
    other = ["B", "y", *("v" for _ in range(510))]
    at_column_limit = (
        ",".join(columns)
        + "\n"
        + ",".join(row)
        + "\n"
        + ",".join(row)
        + "\n"
        + ",".join(other)
        + "\n"
    ).encode()
    above_column_limit = at_column_limit.replace(b"\n", b",c510\n", 1)
    assert not isinstance(_parse_csv(at_column_limit, "unit", "group"), str)
    assert _parse_csv(above_column_limit, "unit", "group") == "malformed-csv-header"

    at_field_limit = "z" * (1 << 20)
    exact_field = (
        f"unit,group,response\nA,x,{at_field_limit}\nA,x,{at_field_limit}\nB,y,{at_field_limit}\n"
    ).encode()
    above_field = exact_field.replace(at_field_limit.encode(), (at_field_limit + "z").encode(), 1)
    assert not isinstance(_parse_csv(exact_field, "unit", "group"), str)
    assert _parse_csv(above_field, "unit", "group") == "malformed-csv"


@pytest.mark.parametrize(
    ("report", "template"),
    [
        (
            "Source file: `data/input.csv`\n\n"
            "A two-sample Student t-test found that each of the 8 measurement rows entered "
            "the test as one observation, t(6) = 2.0, p < 0.05\n",
            "numbered_measurement_rows",
        ),
        (
            "Source file: `data/input.csv`\n\nMeasurement rows analysed: 8\n\n"
            "Welch's two-sample t-test found that each sampling-day measurement in the file "
            "was entered as one observation, Welch t = 2.0, p < 0.05\n",
            "sampling_day_file_rows",
        ),
        (
            "Every nubbin record in data/input.csv contributed one observation to the test.\n\n"
            "| zone | n |\n| --- | --- |\n| lagoon | 4 |\n| forereef | 4 |\n\n"
            "Welch's two-sample t-test compared lagoon with forereef, Welch t = 2.0, "
            "p < 0.05\n",
            "selected_path_nubbin_rows",
        ),
        (
            "The file `data/input.csv` records the selected table.\n\n"
            "A two-sample Student t-test on the 8 individual chamber readings gave "
            "t(6) = 2.0, p < 0.05\n",
            "individual_chamber_readings",
        ),
    ],
)
def test_all_four_literal_admission_families(report: str, template: str) -> None:
    result = _inspect_report(
        _document(report),
        selected_csv_path="data/input.csv",
        unit_column="unit_id",
        n_csv=8,
    )
    assert not isinstance(result, str), result
    assert result.admission_template_id == template
    assert result.reported_n == 8


def test_group_table_inside_base_envelope_is_mandatory_corroboration() -> None:
    report = (
        "Source file: `data/input.csv`\n\n"
        "Each of the 8 measurement rows entered the test as one observation.\n\n"
        "| group | n |\n| --- | --- |\n| left | 4 |\n| right | 4 |\n\n"
        "The left and right results from the two-sample Student t-test were "
        "t(6) = 2.0, p < 0.05\n"
    )
    result = _inspect_report(
        _document(report), selected_csv_path="data/input.csv", unit_column="unit_id", n_csv=8
    )
    assert not isinstance(result, str), result
    assert result.group_counts == (("left", 4), ("right", 4))


@pytest.mark.parametrize(
    "construct",
    [
        "<em>Source file: data/input.csv</em>",
        "[Source file](data/input.csv: data/input.csv",
    ],
)
def test_unsupported_inline_html_or_unclassified_link_syntax_abstains(construct: str) -> None:
    report = (
        f"{construct}\n\n"
        "A two-sample Student t-test found that each of the 8 measurement rows entered "
        "the test as one observation, t = 2.0, p = 0.05\n"
    )
    assert (
        _inspect_report(
            _document(report),
            selected_csv_path="data/input.csv",
            unit_column="unit_id",
            n_csv=8,
        )
        == "unsupported-report-composition"
    )


@pytest.mark.parametrize(
    "spelling",
    [
        "two-sample Student t-test",
        "two-sample Student t test",
        "Welch's two-sample t-test",
        "Welch's two-sample t test",
        "scipy.stats.ttest_ind",
    ],
)
def test_every_accepted_test_spelling_is_closed_and_positive(spelling: str) -> None:
    report = (
        "Source file: `data/input.csv`\n\n"
        f"{spelling}: each of the 8 measurement rows entered the test as one observation, "
        "t = 2.0, p = 0.05\n"
    )
    result = _inspect_report(
        _document(report), selected_csv_path="data/input.csv", unit_column="plot_id", n_csv=8
    )
    assert not isinstance(result, str), result


@pytest.mark.parametrize(
    "phrase",
    [
        "pseudobulk",
        "pseudo-bulk",
        "aggregated",
        "plot mean",
        "plot collapsed",
        "matched pairs",
        "within-subject",
        "split-plot",
        "sub-plot",
        "whole-plot",
        "nested",
        "technical replicates",
        "mixed effects",
        "random intercept",
        "cluster-robust",
        "GEE",
        "generalized estimating equations",
        "sandwich variance",
        "repeated measures",
        "correlated errors",
        "plot bootstrap",
        "plot permutation",
        "plot resampling",
        "plot shuffle",
        "randomized at",
        "randomised at",
        "sensitivity analysis",
        "sensitivity-only",
        "secondary analysis",
        "exploratory",
        "descriptive only",
        "illustrative-only",
        "not the primary analysis",
        "approved deviation",
        "protocol amendment",
        "amended protocol",
        "revised protocol",
        "revised analysis plan",
        "revised SAP",
    ],
)
def test_every_report_suppressor_family_abstains(phrase: str) -> None:
    report = (
        f"Context: {phrase}.\n\nSource file: `data/input.csv`\n\n"
        "A two-sample Student t-test found that each of the 8 measurement rows entered the "
        "test as one observation, t = 2.0, p = 0.05\n"
    )
    assert (
        _inspect_report(
            _document(report),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "report-wide-scientific-suppressor-present"
    )


def test_random_effect_glob_suppresses_singular_and_plural() -> None:
    for phrase in ("random effect", "random effects"):
        report = (
            f"Context: {phrase}.\n\nSource file: `data/input.csv`\n\n"
            "A two-sample Student t-test found that each of the 8 measurement rows entered the "
            "test as one observation, t = 2.0, p = 0.05\n"
        )
        assert (
            _inspect_report(
                _document(report),
                selected_csv_path="data/input.csv",
                unit_column="plot_id",
                n_csv=8,
            )
            == "report-wide-scientific-suppressor-present"
        )


@pytest.mark.parametrize(
    "phrase",
    [
        "summary",
        "summarised",
        "model",
        "checksum",
        "sum",
        "pseudo bulkhead",
        "technically replicate",
        "mixedly effects",
        "pooled variance",
    ],
)
def test_suppressor_token_boundaries_do_not_widen(phrase: str) -> None:
    report = (
        f"Context: {phrase}.\n\nSource file: `data/input.csv`\n\n"
        "A two-sample Student t-test found that each of the 8 measurement rows entered the "
        "test as one observation, t = 2.0, p = 0.05\n"
    )
    result = _inspect_report(
        _document(report),
        selected_csv_path="data/input.csv",
        unit_column="plot_id",
        n_csv=8,
    )
    assert not isinstance(result, str), result


@pytest.mark.parametrize(
    ("replacement", "reason"),
    [
        ("independent-samples t-test", "selected-result-test-co-reference-unavailable"),
        ("two independent groups", "selected-result-test-co-reference-unavailable"),
        ("paired t-test", "report-wide-scientific-suppressor-present"),
        ("Mann-Whitney", "competing-procedure-present"),
    ],
)
def test_unaccepted_or_competing_procedure_wording_abstains(replacement: str, reason: str) -> None:
    report = (
        "Source file: `data/input.csv`\n\n"
        f"{replacement}: each of the 8 measurement rows entered the test as one observation, "
        "t = 2.0, p = 0.05\n"
    )
    assert (
        _inspect_report(
            _document(report),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == reason
    )


def test_numeric_right_boundary_accepts_sentence_period_but_rejects_decimal_continuation() -> None:
    base = (
        "Source file: `data/input.csv`\n\n"
        "A two-sample Student t-test found that each of the 8 measurement rows entered the test "
        "as one observation, t(6) = 2.0, p < 5e-2"
    )
    accepted = _inspect_report(
        _document(base + "; t(6) = 2.0, p < 5e-2\n"),
        selected_csv_path="data/input.csv",
        unit_column="plot_id",
        n_csv=8,
    )
    assert not isinstance(accepted, str), accepted
    sentence_period = _inspect_report(
        _document(base + ".\n"),
        selected_csv_path="data/input.csv",
        unit_column="plot_id",
        n_csv=8,
    )
    assert not isinstance(sentence_period, str), sentence_period
    assert (
        _inspect_report(
            _document(base + ".5\n"),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "inferential-result-witness-unavailable"
    )


def test_report_wide_method_node_and_single_non_neutral_class() -> None:
    report = (
        "Source file: `data/input.csv`\n\n"
        "Each of the 8 measurement rows entered the test as one observation.\n\n"
        "The planned procedure was a two-sample Student t-test.\n\n"
        "The result was t(6) = 2.0, p = 0.05.\n"
    )
    accepted = _inspect_report(
        _document(report), selected_csv_path="data/input.csv", unit_column="plot_id", n_csv=8
    )
    assert not isinstance(accepted, str), accepted
    assert (
        _inspect_report(
            _document(report + "A Welch's two-sample t-test was also named.\n"),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "selected-result-test-co-reference-unavailable"
    )


def _anchored_report(*, anchor: str, gap: int = 0, extra: str = "") -> str:
    return (
        anchor
        + "\n"
        + ("\n" * gap)
        + "A two-sample Student t-test found that each of the 8 measurement rows entered the "
        + "test as one observation, t(6) = 2.0, p = 0.05.\n"
        + extra
    )


def test_path_anchor_absent_mismatched_duplicate_and_second_csv_abstain() -> None:
    cases = (
        (
            _anchored_report(anchor="Dataset: `data/input.csv`"),
            "literal-path-bound-row-entry-admission-unavailable",
        ),
        (
            _anchored_report(anchor="Source file: `data/other.csv`")
            + "Selected table: `data/input.csv`.\n",
            "selected-csv-path-ambiguous",
        ),
        (
            _anchored_report(
                anchor="Source file: `data/input.csv`\n\nSource file: `data/input.csv`"
            ),
            "literal-path-bound-row-entry-admission-unavailable",
        ),
        (
            _anchored_report(
                anchor="Source file: `data/input.csv`", extra="Other: `data/other.csv`.\n"
            ),
            "selected-csv-path-ambiguous",
        ),
    )
    for report, reason in cases:
        assert (
            _inspect_report(
                _document(report),
                selected_csv_path="data/input.csv",
                unit_column="plot_id",
                n_csv=8,
            )
            == reason
        )


def test_path_anchor_distance_16_accepts_and_17_abstains() -> None:
    at_sixteen = _inspect_report(
        _document(_anchored_report(anchor="Source file: `data/input.csv`", gap=16)),
        selected_csv_path="data/input.csv",
        unit_column="plot_id",
        n_csv=8,
    )
    assert not isinstance(at_sixteen, str), at_sixteen
    assert (
        _inspect_report(
            _document(_anchored_report(anchor="Source file: `data/input.csv`", gap=17)),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "literal-path-bound-row-entry-admission-unavailable"
    )


def test_selected_path_matching_is_byte_exact_after_visible_text_parsing() -> None:
    exact = _inspect_report(
        _document(_anchored_report(anchor="Source file: `data/Input.csv`")),
        selected_csv_path="data/Input.csv",
        unit_column="plot_id",
        n_csv=8,
    )
    assert not isinstance(exact, str), exact
    assert (
        _inspect_report(
            _document(_anchored_report(anchor="Source file: `data/input.csv`")),
            selected_csv_path="data/Input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "selected-csv-path-ambiguous"
    )


def _bounded_join_report(*, result_line: int, headings: tuple[int, ...]) -> str:
    lines = [""] * result_line
    lines[0] = "Source file: `data/input.csv`"
    lines[16] = "Each sampling-day measurement in the file was entered as one observation"
    lines[24] = "Measurement rows analysed: 8"
    lines[result_line - 1] = "Welch's two-sample t-test gave Welch t = 2.0, p = 0.05"
    for number in headings:
        lines[number - 1] = f"## Heading {number}"
    return "\n".join(lines) + "\n"


def test_join_envelope_accepts_40_lines_without_whole_heading_cap_and_rejects_41() -> None:
    accepted = _inspect_report(
        _document(_bounded_join_report(result_line=40, headings=(10, 20, 30))),
        selected_csv_path="data/input.csv",
        unit_column="plot_id",
        n_csv=8,
    )
    assert not isinstance(accepted, str), accepted
    assert (
        _inspect_report(
            _document(_bounded_join_report(result_line=41, headings=(10, 20, 30))),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "bounded-minimal-join-envelope-failed"
    )
    assert (
        _inspect_report(
            _document(_bounded_join_report(result_line=40, headings=(10, 30, 32))),
            selected_csv_path="data/input.csv",
            unit_column="plot_id",
            n_csv=8,
        )
        == "bounded-minimal-join-adjacency-failed"
    )


def test_requirement_profile_1_1_shape_and_legacy_reader_are_version_dispatched() -> None:
    resolved = resolve_scientific_requirement_profile(_profile("unit_id", "group"))
    assert resolved.profile_version == SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
    assert (
        resolved.semantic_role_authority == _profile("unit_id", "group")["semantic_role_authority"]
    )

    legacy = resolve_scientific_requirement_profile(
        {
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": CHECK_ID,
            "candidate_id": CANDIDATE_ID,
        }
    )
    assert legacy.profile_version == LEGACY_SCIENTIFIC_REQUIREMENT_PROFILE_VERSION
    assert legacy.semantic_role_authority == {}


@pytest.mark.parametrize(
    "mutation",
    [
        {
            "material_input_path": "../data/input.csv",
            "column_name": "unit_id",
            "group_contrast_column": "group",
        },
        {
            "material_input_path": "data/input.tsv",
            "column_name": "unit_id",
            "group_contrast_column": "group",
        },
        {
            "material_input_path": "data/input.csv",
            "column_name": "1unit",
            "group_contrast_column": "group",
        },
        {
            "material_input_path": "data/input.csv",
            "column_name": "unit_id",
            "group_contrast_column": "unit_id",
        },
    ],
)
def test_requirement_profile_rejects_every_unsafe_authority_shape(
    mutation: dict[str, str],
) -> None:
    profile = _profile("unit_id", "group")
    profile["semantic_role_authority"] = {"authorized_independent_unit_key": mutation}
    with pytest.raises(ScientificRequirementContractError):
        resolve_scientific_requirement_profile(profile)


def test_normal_audit_lifecycle_promotes_the_exact_qualified_code_lane(
    schema_root: Path, tmp_path: Path
) -> None:
    project = tmp_path / "project"
    (project / "data").mkdir(parents=True)
    (project / "results").mkdir()
    (project / "task.md").write_text("Compare the two assigned groups.\n", encoding="utf-8")
    (project / "data" / "input.csv").write_text(
        "unit_id,group,visit,response\n"
        "A,left,1,10\nA,left,2,11\nB,left,1,12\nB,left,2,13\n"
        "C,right,1,20\nC,right,2,21\nD,right,1,22\nD,right,2,23\n",
        encoding="utf-8",
    )
    (project / "results" / "report.md").write_text(
        "This prose is deliberately unrelated to detector admission.\n",
        encoding="utf-8",
    )
    (project / "analysis.py").write_text(
        "import pandas as pd\n"
        "from scipy import stats\n\n"
        'frame = pd.read_csv("data/input.csv")\n'
        'left = frame.loc[frame["group"] == "left", "response"]\n'
        'right = frame.loc[frame["group"] == "right", "response"]\n'
        "result = stats.ttest_ind(left, right)\n"
        "print(result.pvalue)\n",
        encoding="utf-8",
    )
    contract = tmp_path / "contract"
    run_method_contract(
        project,
        "task.md",
        contract,
        schema_root,
        profile=_profile("unit_id", "group"),
        actor_id="scientist:alex",
    )
    parent_lock = json.loads((contract / "semantic.lock.json").read_text(encoding="utf-8"))
    authority_snapshot = parent_lock["method_contract_profile"]["profile_manifest"][
        "authority_binding_snapshot"
    ]["authorized_independent_unit_key"]
    assert authority_snapshot["material_input_path"] == "data/input.csv"
    assert authority_snapshot["column_name"] == "unit_id"
    assert authority_snapshot["group_contrast_column"] == "group"
    assert authority_snapshot["material_input_content_digest"] == sha256_digest(
        (project / "data/input.csv").read_bytes()
    )
    audit = tmp_path / "audit"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        material_inputs=("data/input.csv",),
        method_contract_lock=contract / "semantic.lock.json",
    )
    dependence_results = [
        item
        for item in bundle["detector_results"]
        if item.get("extensions", {}).get("x-scientific-check-ids")
        and CHECK_ID in item["extensions"]["x-scientific-check-ids"]
    ]
    assert [item.get("state") for item in dependence_results].count("finding_candidate") == 1
    assert [item["title"] for item in bundle["findings"]] == [
        "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"
    ]

    packet = {
        "semantic_assertions": bundle["semantic_assertions"],
        "answers": bundle["answers"],
    }
    facts = _code_dependence_row_entry_facts(packet)
    assert facts is not None
    assert facts["analysis_path"] == "analysis.py"
    assert facts["reader_api"] == "pandas_read_csv_v1"
    assert facts["composite_key_candidate_columns"] == ["visit"]
    assert facts["distinct_count_excluded_columns"] == ["response"]
    for field, invalid in (
        ("analysis_path", "workflow/analysis.py"),
        ("reader_api", "custom_reader"),
        ("procedure_id", "scipy.stats.binomtest"),
        ("accepted_reader_count", 2),
        ("all_csv_rows_partitioned", False),
    ):
        mutated = deepcopy(packet)
        observed = next(
            item
            for item in mutated["semantic_assertions"]
            if item.get("extensions", {}).get("x-code-csv-row-entry-evidence") is not None
        )
        projection = observed["extensions"]["x-code-csv-row-entry-evidence"]
        projection[field] = invalid
        observed["extensions"]["x-code-csv-row-entry-evidence-digest"] = semantic_digest(projection)
        assert _code_dependence_row_entry_facts(mutated) is None

    replayed = replay(audit / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]


def test_code_lane_finding_draft_pins_title_and_slot_types(
    schema_root: Path, tmp_path: Path
) -> None:
    project = tmp_path / "project"
    (project / "data").mkdir(parents=True)
    (project / "task.md").write_text("Compare the two assigned groups.\n", encoding="utf-8")
    (project / "data" / "input.csv").write_text(
        "unit_id,group,visit,response\n"
        "A,left,1,10\nA,left,2,11\nB,left,1,12\nB,left,2,13\n"
        "C,right,1,20\nC,right,2,21\nD,right,1,22\nD,right,2,23\n",
        encoding="utf-8",
    )
    (project / "analysis.py").write_text(
        "import pandas as pd\n"
        "from scipy import stats\n\n"
        'frame = pd.read_csv("data/input.csv")\n'
        'left = frame.loc[frame["group"] == "left", "response"]\n'
        'right = frame.loc[frame["group"] == "right", "response"]\n'
        "result = stats.ttest_ind(left, right)\n"
        "print(result.pvalue)\n",
        encoding="utf-8",
    )
    contract = tmp_path / "contract"
    run_method_contract(
        project,
        "task.md",
        contract,
        schema_root,
        profile=_profile("unit_id", "group"),
        actor_id="scientist:alex",
    )
    bundle = run_audit(
        project,
        tmp_path / "audit",
        schema_root,
        material_inputs=("data/input.csv",),
        method_contract_lock=contract / "semantic.lock.json",
        scientific_check_lane="development",
    )
    result = next(
        item
        for item in bundle["detector_results"]
        if item.get("detector_id") == "detector:bounded-code-csv-dependence-conflict"
        and item.get("state") == "evaluation_finding_candidate"
    )
    binding = next(
        item
        for item in scientific_check_release_registry().development_method_conflict_bindings
        if item.check_id == CHECK_ID
        and item.detector_id == "detector:bounded-code-csv-dependence-conflict"
    )
    packet = {
        "semantic_assertions": bundle["semantic_assertions"],
        "answers": bundle["answers"],
    }

    draft = draft_method_conflict_finding(result, binding, work_packet=packet)

    assert draft["title"] == (
        "Analysis code contradicts the frozen one-row-per-authorized-unit requirement"
    )
    assert draft["extensions"]["x-finding-wording-profile-id"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID
    )
    assert draft["extensions"]["x-finding-wording-profile-digest"] == (
        CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST
    )
    assert draft["summary"].endswith(
        "The declared unit column may be one component of a composite key."
    )
    assert _CODE_DEPENDENCE_SLOT_SCHEMA == {
        "CSV_PATH": "safe-normalized-material-path-string",
        "UNIT_COLUMN": "safe-authorized-column-string",
        "GROUP_COLUMN": "safe-authorized-column-string",
        "PROCEDURE_ID": "registered-two-sample-api-identity",
        "N_csv": "checked-positive-integer-equal-to-data-row-count",
        "U": "checked-positive-distinct-unit-count",
        "R": "checked-positive-repeated-unit-count",
        "M": "checked-positive-maximum-unit-multiplicity",
    }
    facts = _code_dependence_row_entry_facts(packet)
    assert facts is not None
    assert all(
        type(facts[field]) is str
        for field in (
            "material_input_path",
            "authorized_unit_column",
            "group_contrast_column",
            "procedure_id",
        )
    )
    assert all(
        type(facts[field]) is int
        for field in (
            "data_row_count",
            "distinct_unit_count",
            "repeated_unit_count",
            "maximum_unit_multiplicity",
        )
    )


@pytest.mark.parametrize(
    ("case_id", "batch", "unit", "group", "expected_candidate", "reason"),
    [
        (
            "0de3a6061d3bb4056306",
            "batch-k1",
            "plot_id",
            "management",
            False,
            "analysis-source-envelope-unavailable",
        ),
        (
            "6b2da0c7167dbba3738f",
            "batch-k1",
            "reactor_id",
            "carbon_source",
            False,
            "analysis-source-envelope-unavailable",
        ),
        (
            "e9e2718573bb47f7d17b",
            "batch-k1",
            "colony_id",
            "reef_zone",
            False,
            "analysis-source-envelope-unavailable",
        ),
        (
            "3ae92d0bb421d6eee99e",
            "batch-k2",
            "plot_id",
            "water_table_regime",
            False,
            "analysis-source-envelope-unavailable",
        ),
    ],
)
def test_batch_k_ttest_cases_follow_documented_normal_path_outcomes(
    schema_root: Path,
    tmp_path: Path,
    case_id: str,
    batch: str,
    unit: str,
    group: str,
    expected_candidate: bool,
    reason: str | None,
) -> None:
    source = (
        Path("evaluation/development/dependence-growth-loop") / batch / "authoring/cases" / case_id
    )
    project = tmp_path / case_id
    shutil.copytree(source, project)
    contract = tmp_path / f"contract-{case_id}"
    run_method_contract(
        project,
        "data-description.md",
        contract,
        schema_root,
        profile=_profile(unit, group),
        actor_id="scientist:alex",
    )
    audit = tmp_path / f"audit-{case_id}"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        report="results/report.md",
        material_inputs=("data/input.csv",),
        method_contract_lock=contract / "semantic.lock.json",
    )
    semantic_lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = semantic_lock["scientific_check_registry"]["evaluation"]
    dependence = next(item for item in evaluation["modules"] if item["check_id"] == CHECK_ID)
    assert dependence["state"] == ("applicable" if expected_candidate else "unsupported")
    if reason is not None:
        assert dependence["observations"][0]["abstention_reason"] == reason
    candidates = [
        item
        for item in bundle["detector_results"]
        if CHECK_ID in item.get("extensions", {}).get("x-scientific-check-ids", [])
        and item.get("state") == "evaluation_finding_candidate"
    ]
    assert bool(candidates) is expected_candidate
    assert not any(
        CHECK_ID in item.get("extensions", {}).get("x-scientific-check-ids", [])
        and item.get("state") == "accepted"
        for item in bundle["detector_results"]
    )
    assert bundle["findings"] == []

    replayed = replay(audit / "semantic.lock.json", tmp_path / f"replay-{case_id}", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]


@pytest.mark.parametrize(
    ("case_id", "unit", "group"),
    [
        ("556f3545bebb45a3b005", "fish_tag", "water_temp_c"),
        ("2c458d2b523ea8c1bd90", "gearbox_id", "wind_bin"),
    ],
)
def test_batch_k_binomial_cases_abstain_through_normal_path_and_replay(
    schema_root: Path,
    tmp_path: Path,
    case_id: str,
    unit: str,
    group: str,
) -> None:
    source = (
        Path("evaluation/development/dependence-growth-loop")
        / "batch-k2"
        / "authoring/cases"
        / case_id
    )
    project = tmp_path / case_id
    shutil.copytree(source, project)
    contract = tmp_path / f"contract-{case_id}"
    run_method_contract(
        project,
        "data-description.md",
        contract,
        schema_root,
        profile=_profile(unit, group),
        actor_id="scientist:alex",
    )
    audit = tmp_path / f"audit-{case_id}"
    bundle = run_audit(
        project,
        audit,
        schema_root,
        report="results/report.md",
        material_inputs=("data/input.csv",),
        method_contract_lock=contract / "semantic.lock.json",
    )
    semantic_lock = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))
    evaluation = semantic_lock["scientific_check_registry"]["evaluation"]
    dependence = next(item for item in evaluation["modules"] if item["check_id"] == CHECK_ID)
    assert dependence["state"] == "unsupported"
    assert (
        dependence["observations"][0]["abstention_reason"]
        == "authorized-group-domain-not-exactly-two"
    )
    assert bundle["findings"] == []

    replayed = replay(audit / "semantic.lock.json", tmp_path / f"replay-{case_id}", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == bundle["findings"]
    assert replayed["coverage_records"] == bundle["coverage_records"]


def test_all_108_lifetime_blind_cases_remain_zero_finding_and_replay_identical(
    schema_root: Path, tmp_path: Path
) -> None:
    growth_root = Path("evaluation/development/dependence-growth-loop")
    cases = sorted(growth_root.glob("batch-*/authoring/cases/*"))
    refused_intake = json.loads(
        (growth_root / "batch-d/authoring/INTAKE_LEDGER.json").read_text(encoding="utf-8")
    )
    refused = [
        item
        for item in refused_intake["entries"]
        if item["intake_admission_state"] == "refused_but_case_retained"
    ]
    assert len(cases) == 107
    assert [item["case_id"] for item in refused] == ["case:dc2b31d5da33d148736a"]
    assert len(cases) + len(refused) == 108

    for case in cases:
        case_key = f"{case.parents[2].name}-{case.name}"
        project = tmp_path / f"project-{case_key}"
        shutil.copytree(case, project)
        audit = tmp_path / f"audit-{case_key}"
        bundle = run_audit(
            project,
            audit,
            schema_root,
            report="results/report.md",
            material_inputs=("data/input.csv",),
        )
        evaluation = json.loads((audit / "semantic.lock.json").read_text(encoding="utf-8"))[
            "scientific_check_registry"
        ]["evaluation"]
        dependence = next(item for item in evaluation["modules"] if item["check_id"] == CHECK_ID)
        assert dependence["state"] == "unsupported", case_key
        assert (
            dependence["observations"][0]["abstention_reason"]
            == "verified-contract-authority-unavailable"
        ), case_key
        assert bundle["findings"] == [], case_key

        replayed = replay(
            audit / "semantic.lock.json",
            tmp_path / f"replay-{case_key}",
            schema_root,
        )
        assert replayed["detector_results"] == bundle["detector_results"], case_key
        assert replayed["findings"] == bundle["findings"], case_key
        assert replayed["coverage_records"] == bundle["coverage_records"], case_key
