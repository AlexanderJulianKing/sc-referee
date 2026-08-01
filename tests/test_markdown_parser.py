from sc_referee.parsers.markdown_claims import inspect_markdown
from sc_referee.records.schema_registry import LocalSchemaRegistry


def test_markdown_inventory_is_a_schema_valid_parser_result(project_root, schema_root) -> None:
    path = project_root / "examples" / "walking-skeleton" / "report.md"
    result = inspect_markdown(path, "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "parsed"
    assert result["coverage_status"] == "covered"
    assert result["extensions"]["x-candidate-spans"]


def test_embedded_html_is_explicitly_opaque(schema_root, tmp_path) -> None:
    path = tmp_path / "report.md"
    path.write_text("# Report\n\n<div data-result='dynamic'></div>\n", encoding="utf-8")
    result = inspect_markdown(path, "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    assert result["coverage_status"] == "partially_covered"
    assert result["opaque_constructs"][0]["kind"] == "embedded_html"


def test_invalid_utf8_markdown_is_localized(schema_root, tmp_path) -> None:
    path = tmp_path / "report.md"
    path.write_bytes(b"# Report\n\xff\n")
    result = inspect_markdown(path, "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "error"
    assert result["coverage_status"] == "not_covered"


def test_explicit_directional_claim_has_exact_span_and_only_literal_semantics(
    project_root, schema_root
) -> None:
    path = project_root / "examples" / "walking-skeleton" / "report.md"
    result = inspect_markdown(path, "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    claims = result["extensions"]["x-explicit-directional-claims"]
    assert len(claims) == 1
    claim = claims[0]
    assert claim["text"] == "Treatment increased expression relative to control."
    assert claim["direction"] == "positive"
    assert claim["literal_subject"] == "Treatment"
    assert claim["literal_object"] == "expression"
    assert claim["literal_comparison"] == "Treatment versus control"
    assert claim["source_ref"]["locator"] == "report.md:3"
    assert claim["source_ref"]["start_column"] == 1
    assert claim["source_ref"]["end_column"] == 52


def test_markdown_parser_preserves_repository_relative_nested_path(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    path = reports / "results.md"
    path.write_text("Treatment increased yield relative to control.\n", encoding="utf-8")

    result = inspect_markdown(path, "audit:nested", source_path="reports/results.md")

    assert result["source_ref"]["path"] == "reports/results.md"
    claim = result["extensions"]["x-explicit-directional-claims"][0]
    assert claim["source_ref"]["path"] == "reports/results.md"
    assert claim["source_ref"]["locator"] == "reports/results.md:1"


def test_expected_count_profile_and_sensitivity_require_exact_supported_sentences(
    schema_root, tmp_path
) -> None:
    path = tmp_path / "report.md"
    path.write_text(
        "# Result\n\n"
        "At the queried 20 kb pixel, the mean case loop strength is **2.018599**, "
        "the mean control loop strength is **0.027571**, and the case-minus-control "
        "difference is **1.991029** log2 units.\n\n"
        "# Method\n\n"
        "For each replicate independently, I used the arithmetic mean of all other "
        "20 kb pixels at the same nine-bin separation as the expected count. The focal "
        "pixel was left out so that a true loop could not raise its own expected value "
        "in this small matrix.\n\n"
        "Pairs incident to bins with mappability below 0.80 were excluded from the "
        "background.\n\n"
        "An unfiltered leave-one-out mean gives case=1.186815, control=-0.789760, and "
        "delta=1.976575. A robust median on the quality-filtered background gives "
        "case=2.205261, control=0.233752, and delta=1.971509.\n",
        encoding="utf-8",
    )

    result = inspect_markdown(path, "run:expected-count")

    LocalSchemaRegistry(schema_root).validate(result)
    quantitative = result["extensions"]["x-explicit-quantitative-claims"]
    assert len(quantitative) == 1
    assert quantitative[0]["resolution_bp"] == 20_000
    assert quantitative[0]["estimate_text"] == "1.991029"
    assert quantitative[0]["source_ref"]["quoted_text"].startswith("At the queried 20 kb")

    declarations = result["extensions"]["x-expected-count-method-declarations"]
    assert len(declarations) == 1
    profile = declarations[0]["profile"]
    assert profile["estimator_family"] == "same_stratum_arithmetic_mean"
    assert profile["grouping_structure"] == "replicate_specific_background"
    assert profile["covariate_terms"] == ["distance", "mappability"]
    assert profile["training_exclusions"] == [
        "low_mappability",
        "target_observation",
    ]
    assert profile["analysis_resolution_bp"] == 20_000
    assert len(declarations[0]["source_refs"]) == 3

    sensitivities = result["extensions"]["x-explicit-expected-count-sensitivities"]
    assert [item["alternative"] for item in sensitivities] == [
        "unfiltered_leave_one_out_mean",
        "quality_filtered_robust_median",
    ]
    assert sensitivities[0]["values"]["control"] == "-0.789760"
    assert sensitivities[1]["values"]["delta"] == "1.971509"


def test_expected_count_profile_abstains_on_paraphrase_or_partial_evidence(
    schema_root, tmp_path
) -> None:
    path = tmp_path / "report.md"
    path.write_text(
        "For each replicate, expected counts were approximately averaged from nearby "
        "pixels. The focal pixel may have been left out.\n"
        "Pairs with low mappability were generally excluded.\n",
        encoding="utf-8",
    )

    result = inspect_markdown(path, "run:unsupported-wording")

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["extensions"]["x-expected-count-method-declarations"] == []
    assert result["extensions"]["x-explicit-expected-count-sensitivities"] == []
    assert result["extensions"]["x-explicit-quantitative-claims"] == []
