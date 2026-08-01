import pytest

from sc_referee.parsers.python_ast import PARSER_VERSION, inspect_python
from sc_referee.parsers.scalar_verification import (
    UnsupportedScalarVerification,
    verify_mean_difference,
)
from sc_referee.records.observed import build_public_static_graph
from sc_referee.records.schema_registry import LocalSchemaRegistry


def test_python_parser_finds_calls_without_execution(project_root) -> None:
    path = project_root / "examples" / "walking-skeleton" / "analysis.py"
    result = inspect_python(path, "run:test")
    assert result["state"] == "parsed"
    assert any(item["name"] == "Path" for item in result["extensions"]["x-calls"])
    assert len(result["extensions"]["x-calls"]) > 0
    first_sum = next(item for item in result["extensions"]["x-calls"] if item["name"] == "sum")
    assert first_sum == {
        "name": "sum",
        "start_line": 15,
        "end_line": 15,
        "start_column": 12,
        "end_column": 24,
    }


def test_python_parser_resolves_exact_source_parent_output_writer(tmp_path) -> None:
    (tmp_path / "report.md").write_text("Result\n", encoding="utf-8")
    source = tmp_path / "analysis.py"
    source.write_text(
        "from pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def main():\n"
        "    report = 'Result\\n'\n"
        "    (ROOT / 'report.md').write_text(report)\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )

    result = inspect_python(source, "audit:selected-writer", source_path="analysis.py")
    artifact = next(
        item for item in result["extensions"]["x-artifacts"] if item.get("path") == "report.md"
    )
    writer = next(
        item
        for item in result["extensions"]["x-operations"]
        if artifact["artifact_id"] in item["output_refs"]
    )

    assert result["parser_version"] == PARSER_VERSION == "0.15.1"
    assert artifact["kind"] == "output_file"
    assert artifact["producer_operation_ids"] == [writer["operation_id"]]
    assert writer["kind"] == "write"
    assert writer["source_refs"][0]["path"] == "analysis.py"


@pytest.mark.parametrize(
    "root_expression",
    [
        "Path.cwd()",
        "Path(__file__).resolve().parent.parent",
        "Path('/tmp')",
    ],
)
def test_python_parser_rejects_non_source_parent_output_roots(
    tmp_path, root_expression: str
) -> None:
    (tmp_path / "report.md").write_text("Result\n", encoding="utf-8")
    source = tmp_path / "analysis.py"
    source.write_text(
        "from pathlib import Path\n"
        f"ROOT = {root_expression}\n"
        "(ROOT / 'report.md').write_text('Result\\n')\n",
        encoding="utf-8",
    )

    result = inspect_python(source, "audit:unsafe-root", source_path="analysis.py")

    assert not any(
        item.get("path") == "report.md" and item.get("kind") == "output_file"
        for item in result["extensions"]["x-artifacts"]
    )


def test_malformed_python_emits_localized_coverage_record(schema_root, tmp_path) -> None:
    path = tmp_path / "malformed.py"
    path.write_text("def broken(:\n    pass\n", encoding="utf-8")
    result = inspect_python(path, "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "partially_parsed"
    assert result["coverage_status"] == "partially_covered"
    assert len(result["syntax_issues"]) == 1
    assert result["syntax_issues"][0]["source_ref"]["start_line"] == 1
    assert result["emitted_record_refs"] == []


def test_opaque_python_constructs_are_explicit_and_never_executed(schema_root, tmp_path) -> None:
    path = tmp_path / "opaque.py"
    marker = tmp_path / "must-not-exist"
    path.write_text(
        "from package import *\n"
        "factory()()\n"
        f"exec(\"open({str(marker)!r}, 'w').write('executed')\")\n",
        encoding="utf-8",
    )
    result = inspect_python(path, "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "parsed"
    assert result["coverage_status"] == "partially_covered"
    assert {item["kind"] for item in result["opaque_constructs"]} == {
        "dynamic_call_target",
        "runtime_code_generation",
        "wildcard_import",
    }
    assert not marker.exists()


def test_unreadable_python_path_is_a_record_not_an_exception(schema_root, tmp_path) -> None:
    result = inspect_python(tmp_path / "missing.py", "run:test")
    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "error"
    assert result["coverage_status"] == "not_covered"
    assert result["syntax_issues"][0]["recoverable"] is True


def test_python_parser_extracts_exact_operation_and_artifact_graph(project_root) -> None:
    path = project_root / "examples" / "walking-skeleton" / "analysis.py"
    result = inspect_python(path, "run:test")
    operations = result["extensions"]["x-operations"]
    artifacts = result["extensions"]["x-artifacts"]
    estimate = next(
        operation
        for operation in operations
        if operation["implementation"] == "python.function:compute_difference"
    )
    assert estimate["kind"] == "estimate"
    assert estimate["inspection_status"] == "supported"
    assert estimate["source_refs"][0]["start_line"] == 11
    assert estimate["source_refs"][0]["end_line"] == 15
    assert "return sum(treated)" in estimate["source_refs"][0]["quoted_text"]
    assert estimate["input_refs"]
    assert estimate["output_refs"]
    assert estimate["literal_parameters"] == {
        "outcome_column": "expression",
        "left_group": "treated",
        "right_group": "control",
    }
    assert any(operation["kind"] == "read" for operation in operations)
    assert any(operation["kind"] == "write" for operation in operations)
    assert all(
        "<dynamic>" not in operation["implementation"]
        for operation in operations
        if operation["inspection_status"] == "supported"
    )
    assert any(artifact.get("path") == "data.csv" for artifact in artifacts)
    result_artifact = next(
        artifact for artifact in artifacts if artifact.get("path") == "result.json"
    )
    write_operation = next(
        operation
        for operation in operations
        if operation["kind"] == "write"
        and result_artifact["artifact_id"] in operation["output_refs"]
    )
    assert result_artifact["producer_operation_ids"] == [write_operation["operation_id"]]
    emitted = {
        (record["record_type"], record["record_id"]) for record in result["emitted_record_refs"]
    }
    assert ("operation", estimate["operation_id"]) in emitted


def test_python_parser_links_only_supported_result_expressions_into_literal_report_writes(
    tmp_path,
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Result 2.0\n", encoding="utf-8")
    (tmp_path / "other.md").write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "Path('report.md').write_text(f\"Result {difference(Path('data.csv'))}\\n\")\n"
        "value = difference(Path('data.csv'))\n"
        "Path('other.md').write_text(f\"Result {value}\\n\")\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:static-flow", source_path="analysis.py")
    assert result["parser_version"] == PARSER_VERSION
    operations = result["extensions"]["x-operations"]
    artifacts = result["extensions"]["x-artifacts"]
    estimate = next(
        operation
        for operation in operations
        if operation["implementation"] == "python.function:difference"
    )
    computed_artifact_id = estimate["output_refs"][0]
    artifacts_by_path = {
        artifact.get("path"): artifact for artifact in artifacts if artifact.get("path")
    }
    report_write = next(
        operation
        for operation in operations
        if artifacts_by_path["report.md"]["artifact_id"] in operation["output_refs"]
    )
    variable_write = next(
        operation
        for operation in operations
        if artifacts_by_path["other.md"]["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == [computed_artifact_id]
    assert report_write["literal_parameters"] == {
        "static_result_artifact_flow": "direct_supported_call"
    }
    assert variable_write["input_refs"] == [computed_artifact_id]
    assert variable_write["literal_parameters"] == {
        "static_result_artifact_flow": "single_assignment_alias"
    }


def test_python_parser_abstains_from_result_flow_when_function_binding_is_ambiguous(
    tmp_path,
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    function = (
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
    )
    path.write_text(
        "from pathlib import Path\nimport csv\n"
        + function
        + function
        + "Path('report.md').write_text(str(difference(Path('data.csv'))))\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:ambiguous-flow", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


def test_python_parser_links_only_one_module_assignment_alias_before_the_writer(
    tmp_path,
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    for name in ("report.md", "mutated.md", "conditional.md", "early.md"):
        (tmp_path / name).write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "early = difference(Path('data.csv'))\n"
        "Path('early.md').write_text(f\"Result {later}\\n\")\n"
        "later = difference(Path('data.csv'))\n"
        "value = difference(Path('data.csv'))\n"
        "Path('report.md').write_text(f\"Result {value}\\n\")\n"
        "changed = difference(Path('data.csv'))\n"
        "changed = 0.0\n"
        "Path('mutated.md').write_text(f\"Result {changed}\\n\")\n"
        "conditional = difference(Path('data.csv'))\n"
        "if enabled:\n"
        "    Path('conditional.md').write_text(f\"Result {conditional}\\n\")\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:alias-flow", source_path="analysis.py")
    artifacts_by_path = {
        artifact.get("path"): artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path")
    }
    writes = {
        artifact_path: next(
            operation
            for operation in result["extensions"]["x-operations"]
            if artifact["artifact_id"] in operation["output_refs"]
        )
        for artifact_path, artifact in artifacts_by_path.items()
        if artifact_path.endswith(".md")
    }
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert writes["report.md"]["input_refs"] == estimate["output_refs"]
    assert writes["report.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "single_assignment_alias"
    }
    for unresolved in ("early.md", "mutated.md", "conditional.md"):
        assert writes[unresolved]["input_refs"] == []
        assert writes[unresolved]["literal_parameters"] == {}


def test_python_parser_follows_only_bounded_module_assignment_chains(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Result 2.0\n", encoding="utf-8")
    (tmp_path / "over-limit.md").write_text("Result 2.0\n", encoding="utf-8")
    function = (
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
    )
    bounded_chain = (
        "value = difference(Path('data.csv'))\n"
        'rendered = f"Result {value}\\n"\n'
        'document = "" + rendered\n'
        "Path('report.md').write_text(document)\n"
    )
    over_limit_chain = "deep_1 = difference(Path('data.csv'))\n" + "".join(
        f"deep_{index} = deep_{index - 1}\n" for index in range(2, 10)
    )
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\nimport csv\n"
        + function
        + bounded_chain
        + over_limit_chain
        + "Path('over-limit.md').write_text(str(deep_9))\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:alias-chain", source_path="analysis.py")
    assert result["parser_version"] == PARSER_VERSION
    artifacts_by_path = {
        artifact.get("path"): artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path")
    }
    writes = {
        artifact_path: next(
            operation
            for operation in result["extensions"]["x-operations"]
            if artifact["artifact_id"] in operation["output_refs"]
        )
        for artifact_path, artifact in artifacts_by_path.items()
        if artifact_path.endswith(".md")
    }
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert writes["report.md"]["input_refs"] == estimate["output_refs"]
    assert writes["report.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "single_assignment_alias_chain"
    }
    assert writes["over-limit.md"]["input_refs"] == []
    assert writes["over-limit.md"]["literal_parameters"] == {}


def test_python_parser_links_only_bounded_straight_line_function_local_result_flow(
    tmp_path,
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    for name in ("direct.md", "alias.md", "chain.md"):
        (tmp_path / name).write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def render_reports():\n"
        "    Path('direct.md').write_text(str(difference(Path('data.csv'))))\n"
        "    value = difference(Path('data.csv'))\n"
        "    Path('alias.md').write_text(f'Result {value}\\n')\n"
        "    rendered = f'Result {value}\\n'\n"
        "    document = '' + rendered\n"
        "    Path('chain.md').write_text(document)\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:function-local-flow", source_path="analysis.py")
    assert result["parser_version"] == PARSER_VERSION
    artifacts_by_path = {
        artifact.get("path"): artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path")
    }
    writes = {
        artifact_path: next(
            operation
            for operation in result["extensions"]["x-operations"]
            if artifact["artifact_id"] in operation["output_refs"]
        )
        for artifact_path, artifact in artifacts_by_path.items()
        if artifact_path.endswith(".md")
    }
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert writes["direct.md"]["input_refs"] == estimate["output_refs"]
    assert writes["direct.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_local_direct_supported_call"
    }
    assert writes["alias.md"]["input_refs"] == estimate["output_refs"]
    assert writes["alias.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_local_single_assignment_alias"
    }
    assert writes["chain.md"]["input_refs"] == estimate["output_refs"]
    assert writes["chain.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_local_single_assignment_alias_chain"
    }


def test_python_parser_links_one_exact_result_through_one_parameter_renderer_call(
    tmp_path,
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    for name in ("direct.md", "alias-chain.md"):
        (tmp_path / name).write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def render_direct(value):\n"
        "    Path('direct.md').write_text(str(value))\n"
        "def render_alias(value):\n"
        "    rendered = f'Result {value}\\n'\n"
        "    document = '' + rendered\n"
        "    Path('alias-chain.md').write_text(document)\n"
        "render_direct(difference(Path('data.csv')))\n"
        "result = difference(Path('data.csv'))\n"
        "render_alias(result)\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:parameter-renderer-flow", source_path="analysis.py")
    artifacts_by_path = {
        artifact.get("path"): artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path")
    }
    writes = {
        artifact_path: next(
            operation
            for operation in result["extensions"]["x-operations"]
            if artifact["artifact_id"] in operation["output_refs"]
        )
        for artifact_path, artifact in artifacts_by_path.items()
        if artifact_path.endswith(".md")
    }
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert writes["direct.md"]["input_refs"] == estimate["output_refs"]
    assert writes["direct.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_parameter_bound_direct"
    }
    assert writes["alias-chain.md"]["input_refs"] == estimate["output_refs"]
    assert writes["alias-chain.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_parameter_bound_alias_chain"
    }


def test_python_parser_links_one_result_plus_exact_literal_renderer_arguments(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    for name in ("direct.md", "alias-chain.md"):
        (tmp_path / name).write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def render_direct(value, label):\n"
        "    Path('direct.md').write_text(f'{label}: {value}\\n')\n"
        "def render_alias(label, value, precision):\n"
        "    rendered = f'{label}: {value} ({precision})\\n'\n"
        "    document = '' + rendered\n"
        "    Path('alias-chain.md').write_text(document)\n"
        "render_direct(difference(Path('data.csv')), 'Difference')\n"
        "result = difference(Path('data.csv'))\n"
        "render_alias('Difference', result, str(2))\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:literal-parameter-renderer", source_path="analysis.py")
    artifacts_by_path = {
        artifact.get("path"): artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path")
    }
    writes = {
        artifact_path: next(
            operation
            for operation in result["extensions"]["x-operations"]
            if artifact["artifact_id"] in operation["output_refs"]
        )
        for artifact_path, artifact in artifacts_by_path.items()
        if artifact_path.endswith(".md")
    }
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert writes["direct.md"]["input_refs"] == estimate["output_refs"]
    assert writes["direct.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_result_literal_parameters_bound_direct"
    }
    assert writes["alias-chain.md"]["input_refs"] == estimate["output_refs"]
    assert writes["alias-chain.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_result_literal_parameters_bound_alias_chain"
    }


def test_python_parser_resolves_one_exact_literal_renderer_output_path(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def render(target, label, value):\n"
        "    rendered = f'{label}: {value}\\n'\n"
        "    Path(target).write_text(rendered, encoding='utf-8')\n"
        "result = difference(Path('data.csv'))\n"
        "render('report.md', 'Difference', result)\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:path-parameter-renderer", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert report_artifact["kind"] == "output_file"
    assert report_write["input_refs"] == estimate["output_refs"]
    assert report_write["literal_parameters"] == {
        "static_result_artifact_flow": ("function_result_literal_path_parameters_bound_alias_chain")
    }


def test_python_parser_binds_exact_renderer_keywords_to_required_parameters(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    for name in ("direct.md", "keyword-path.md"):
        (tmp_path / name).write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def render_direct(label, value):\n"
        "    Path('direct.md').write_text(f'{label}: {value}\\n')\n"
        "def render_path(target, label, value):\n"
        "    rendered = f'{label}: {value}\\n'\n"
        "    Path(target).write_text(rendered)\n"
        "render_direct(value=difference(Path('data.csv')), label='Difference')\n"
        "result = difference(Path('data.csv'))\n"
        "render_path(value=result, target='keyword-path.md', label='Difference')\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:keyword-renderer", source_path="analysis.py")
    artifacts_by_path = {
        artifact.get("path"): artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path")
    }
    writes = {
        artifact_path: next(
            operation
            for operation in result["extensions"]["x-operations"]
            if artifact["artifact_id"] in operation["output_refs"]
        )
        for artifact_path, artifact in artifacts_by_path.items()
        if artifact_path.endswith(".md")
    }
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert writes["direct.md"]["input_refs"] == estimate["output_refs"]
    assert writes["direct.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_keyword_bound_result_flow_direct"
    }
    assert writes["keyword-path.md"]["input_refs"] == estimate["output_refs"]
    assert writes["keyword-path.md"]["literal_parameters"] == {
        "static_result_artifact_flow": "function_keyword_bound_result_flow_alias_chain"
    }


def test_python_parser_links_one_direct_unique_static_formatter_call(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def format_report(label, value):\n"
        "    return f'{label}: {value}\\n'\n"
        "result = difference(Path('data.csv'))\n"
        "Path('report.md').write_text(format_report(value=result, label='Difference'))\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:static-formatter", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert report_write["input_refs"] == estimate["output_refs"]
    assert report_write["literal_parameters"] == {
        "static_result_artifact_flow": "direct_static_formatter_call"
    }


@pytest.mark.parametrize(
    "formatter_and_write",
    [
        (
            "def format_report(label, value):\n"
            "    return f'{label}: {value}'\n"
            "result = difference(Path('data.csv'))\n"
            "format_report('Unused', result)\n"
            "Path('report.md').write_text(format_report('Difference', result))\n"
        ),
        (
            "def format_report(label, value):\n"
            "    rendered = f'{label}: {value}'\n"
            "    return rendered\n"
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
        ),
        (
            "@decorate\n"
            "def format_report(label, value):\n"
            "    return f'{label}: {value}'\n"
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
        ),
        (
            "def format_report(label: str, value):\n"
            "    return f'{label}: {value}'\n"
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
        ),
        (
            "def format_report(label, value=0.0):\n"
            "    return f'{label}: {value}'\n"
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
        ),
        (
            "def format_report(label, value):\n"
            "    return normalize(label, value)\n"
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
        ),
        (
            "def format_report(label, value):\n"
            "    return f'{label}: no result'\n"
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
        ),
        (
            "def format_report(left, right):\n"
            "    return f'{left}: {right}'\n"
            "Path('report.md').write_text(format_report("
            "difference(Path('data.csv')), difference(Path('data.csv'))))\n"
        ),
        (
            "label = get_label()\n"
            "def format_report(label, value):\n"
            "    return f'{label}: {value}'\n"
            "Path('report.md').write_text("
            "format_report(label, difference(Path('data.csv'))))\n"
        ),
        (
            "Path('report.md').write_text("
            "format_report('Difference', difference(Path('data.csv'))))\n"
            "def format_report(label, value):\n"
            "    return f'{label}: {value}'\n"
        ),
        (
            "def format_report(str, value):\n"
            "    return str(value)\n"
            "Path('report.md').write_text("
            "format_report('not-builtin', difference(Path('data.csv'))))\n"
        ),
    ],
)
def test_python_parser_rejects_ambiguous_or_opaque_static_formatter_flow(
    tmp_path, formatter_and_write: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        + formatter_and_write,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:static-formatter-abstain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


def test_python_parser_links_one_static_formatter_assignment_to_one_writer(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def format_report(label, value):\n"
        "    return f'{label}: {value}\\n'\n"
        "result = difference(Path('data.csv'))\n"
        "rendered = format_report(value=result, label='Difference')\n"
        "Path('report.md').write_text(rendered)\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:formatter-alias", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert report_write["input_refs"] == estimate["output_refs"]
    assert report_write["literal_parameters"] == {
        "static_result_artifact_flow": "single_static_formatter_assignment"
    }


@pytest.mark.parametrize(
    "assignment_and_write",
    [
        (
            "rendered = format_report('Difference', result)\n"
            "rendered = 'changed'\n"
            "Path('report.md').write_text(rendered)\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "print(rendered)\n"
            "Path('report.md').write_text(rendered)\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "Path('report.md').write_text(rendered)\n"
            "Path('other.md').write_text(rendered)\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "Path('report.md').write_text(str(rendered))\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "if enabled:\n"
            "    Path('report.md').write_text(rendered)\n"
        ),
        (
            "Path('report.md').write_text(rendered)\n"
            "rendered = format_report('Difference', result)\n"
        ),
        (
            "rendered, = (format_report('Difference', result),)\n"
            "Path('report.md').write_text(rendered)\n"
        ),
    ],
)
def test_python_parser_rejects_mutated_reused_or_indirect_static_formatter_assignment(
    tmp_path, assignment_and_write: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    for name in ("report.md", "other.md"):
        (tmp_path / name).write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def format_report(label, value):\n"
        "    return f'{label}: {value}\\n'\n"
        "result = difference(Path('data.csv'))\n" + assignment_and_write,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:formatter-alias-abstain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


def test_python_parser_links_one_linear_static_formatter_assignment_chain(tmp_path) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def format_report(label, value):\n"
        "    return f'{label}: {value}\\n'\n"
        "result = difference(Path('data.csv'))\n"
        "rendered = format_report(value=result, label='Difference')\n"
        "document = '' + rendered\n"
        "payload = f'{document}'\n"
        "Path('report.md').write_text(payload)\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:formatter-chain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    estimate = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"] == "python.function:difference"
    )

    assert result["parser_version"] == PARSER_VERSION
    assert report_write["input_refs"] == estimate["output_refs"]
    assert report_write["literal_parameters"] == {
        "static_result_artifact_flow": "static_formatter_assignment_chain"
    }


@pytest.mark.parametrize(
    "assignment_and_write",
    [
        (
            "rendered = format_report('Difference', result)\n"
            "left = '' + rendered\n"
            "right = '' + rendered\n"
            "Path('report.md').write_text(left)\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "left = '' + rendered\n"
            "right = '' + rendered\n"
            "document = left + right\n"
            "Path('report.md').write_text(document)\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "document = '' + rendered\n"
            "document = 'changed'\n"
            "Path('report.md').write_text(document)\n"
        ),
        (
            "rendered = format_report('Difference', result)\n"
            "a1 = '' + rendered\n"
            "a2 = '' + a1\n"
            "a3 = '' + a2\n"
            "a4 = '' + a3\n"
            "a5 = '' + a4\n"
            "a6 = '' + a5\n"
            "Path('report.md').write_text(a6)\n"
        ),
    ],
)
def test_python_parser_rejects_non_linear_or_over_limit_static_formatter_chain(
    tmp_path, assignment_and_write: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "def format_report(label, value):\n"
        "    return f'{label}: {value}\\n'\n"
        "result = difference(Path('data.csv'))\n" + assignment_and_write,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:formatter-chain-abstain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


@pytest.mark.parametrize(
    "renderer_and_call",
    [
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render(value=difference(Path('data.csv')))\n"
        ),
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render('Difference', difference(Path('data.csv')), extra='unexpected')\n"
        ),
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render('Difference', label='Duplicate', value=difference(Path('data.csv')))\n"
        ),
        (
            "def render(value, /, label):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render(value=difference(Path('data.csv')), label='Difference')\n"
        ),
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "arguments = {}\n"
            "render(**arguments)\n"
        ),
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "label = get_label()\n"
            "render(value=difference(Path('data.csv')), label=label)\n"
        ),
        (
            "def render(value, *, label):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render(value=difference(Path('data.csv')), label='Difference')\n"
        ),
    ],
)
def test_python_parser_rejects_inexact_renderer_keyword_binding(
    tmp_path, renderer_and_call: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        + renderer_and_call,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:keyword-renderer-abstain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


@pytest.mark.parametrize(
    "renderer_and_call",
    [
        (
            "def render(target, value):\n"
            "    Path(target).write_text(str(value))\n"
            "target = 'report.md'\n"
            "render(target, difference(Path('data.csv')))\n"
        ),
        (
            "def render(target, value):\n"
            "    Path(target).write_text(str(value))\n"
            "render('../report.md', difference(Path('data.csv')))\n"
        ),
        (
            "def render(target, value):\n"
            "    Path(target).write_text(str(value))\n"
            "render(str('report.md'), difference(Path('data.csv')))\n"
        ),
        (
            "def render(target, value):\n"
            "    target = 'report.md'\n"
            "    Path(target).write_text(str(value))\n"
            "render('report.md', difference(Path('data.csv')))\n"
        ),
        (
            "def render(target, value):\n"
            "    Path(target).write_text(str(value))\n"
            "render('report.md', 'not a result')\n"
        ),
        (
            "def render(target, other, value):\n"
            "    Path(target).write_text(str(value))\n"
            "    Path(other).write_text(str(value))\n"
            "render('report.md', 'other.md', difference(Path('data.csv')))\n"
        ),
    ],
)
def test_python_parser_abstains_from_dynamic_unsafe_or_unbound_renderer_output_paths(
    tmp_path, renderer_and_call: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        + renderer_and_call,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:path-parameter-abstain", source_path="analysis.py")
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["implementation"].endswith(".write_text")
    )

    assert all(
        artifact.get("path") != "report.md" for artifact in result["extensions"]["x-artifacts"]
    )
    assert report_write["input_refs"] == []
    assert report_write["output_refs"] == []
    assert report_write["literal_parameters"] == {}


@pytest.mark.parametrize(
    "renderer_and_call",
    [
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "label = get_label()\n"
            "render(label, difference(Path('data.csv')))\n"
        ),
        (
            "def render(left, right):\n"
            "    Path('report.md').write_text(f'{left}: {right}')\n"
            "render(difference(Path('data.csv')), difference(Path('data.csv')))\n"
        ),
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render('Difference', 'not a result')\n"
        ),
        (
            "def render(label='Difference', value=0.0):\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render('Difference', difference(Path('data.csv')))\n"
        ),
        (
            "def render(label, value):\n"
            "    label = 'Changed'\n"
            "    Path('report.md').write_text(f'{label}: {value}')\n"
            "render('Difference', difference(Path('data.csv')))\n"
        ),
        (
            "def render(label, value):\n"
            "    Path('report.md').write_text(f'{label.upper()}: {value}')\n"
            "render('Difference', difference(Path('data.csv')))\n"
        ),
    ],
)
def test_python_parser_abstains_from_nonliteral_or_ambiguous_renderer_arguments(
    tmp_path, renderer_and_call: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Difference: 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        + renderer_and_call,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:literal-renderer-abstain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )

    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


@pytest.mark.parametrize(
    "renderer_and_call",
    [
        "def render(value):\n    Path('report.md').write_text(str(value))\n",
        (
            "def render(value):\n"
            "    Path('report.md').write_text(str(value))\n"
            "render(difference(Path('data.csv')))\n"
            "render(difference(Path('data.csv')))\n"
        ),
        (
            "def render(value):\n"
            "    Path('report.md').write_text(str(value))\n"
            "if enabled:\n"
            "    render(difference(Path('data.csv')))\n"
        ),
        (
            "def render(value=0.0):\n"
            "    Path('report.md').write_text(str(value))\n"
            "render(difference(Path('data.csv')))\n"
        ),
        (
            "def render(value):\n"
            "    value = 0.0\n"
            "    Path('report.md').write_text(str(value))\n"
            "render(difference(Path('data.csv')))\n"
        ),
        (
            "def render(value):\n"
            "    Path('report.md').write_text(str(abs(value)))\n"
            "render(difference(Path('data.csv')))\n"
        ),
        (
            "def render(str, value):\n"
            "    Path('report.md').write_text(str(value))\n"
            "render('not-builtin', difference(Path('data.csv')))\n"
        ),
        (
            "def render(Path, value):\n"
            "    Path('report.md').write_text(str(value))\n"
            "render('not-pathlib', difference(Path('data.csv')))\n"
        ),
    ],
)
def test_python_parser_abstains_from_unbound_ambiguous_or_mutated_parameter_renderer(
    tmp_path, renderer_and_call: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        + renderer_and_call,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:parameter-renderer-abstain", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


@pytest.mark.parametrize(
    "render_function",
    [
        (
            "def render_report(value):\n"
            "    Path('report.md').write_text(str(difference(Path('data.csv'))))\n"
        ),
        (
            "def render_report():\n"
            "    value = difference(Path('data.csv'))\n"
            "    if enabled:\n"
            "        Path('report.md').write_text(str(value))\n"
        ),
        (
            "def render_report():\n"
            "    value = difference(Path('data.csv'))\n"
            "    value = 0.0\n"
            "    Path('report.md').write_text(str(value))\n"
        ),
        (
            "def outer():\n"
            "    def render_report():\n"
            "        value = difference(Path('data.csv'))\n"
            "        Path('report.md').write_text(str(value))\n"
        ),
        (
            "def render_report():\n"
            "    deep_1 = difference(Path('data.csv'))\n"
            + "".join(f"    deep_{index} = deep_{index - 1}\n" for index in range(2, 10))
            + "    Path('report.md').write_text(str(deep_9))\n"
        ),
        (
            "def render_report():\n"
            "    value = difference(Path('data.csv'))\n"
            "    str = value\n"
            "    Path('report.md').write_text(str(value))\n"
        ),
    ],
)
def test_python_parser_abstains_from_parameterized_branched_mutated_nested_or_deep_local_flow(
    tmp_path, render_function: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Result 2.0\n", encoding="utf-8")
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n" + render_function,
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:function-local-abstention", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


@pytest.mark.parametrize(
    "source",
    [
        ("Path('report.md').write_text(str(difference(Path('data.csv'))))\n{function}"),
        (
            "{function}"
            "difference = replacement\n"
            "Path('report.md').write_text(str(difference(Path('data.csv'))))\n"
        ),
        (
            "{function}"
            "str = custom_renderer\n"
            "Path('report.md').write_text(str(difference(Path('data.csv'))))\n"
        ),
        (
            "{function}"
            "def render(difference):\n"
            "    Path('report.md').write_text(str(difference(Path('data.csv'))))\n"
        ),
    ],
)
def test_python_parser_abstains_from_out_of_order_shadowed_or_nested_result_flow(
    tmp_path, source: str
) -> None:
    (tmp_path / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    (tmp_path / "report.md").write_text("Result 2.0\n", encoding="utf-8")
    function = (
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
    )
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\nimport csv\n" + source.format(function=function),
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:scope-abstention", source_path="analysis.py")
    report_artifact = next(
        artifact
        for artifact in result["extensions"]["x-artifacts"]
        if artifact.get("path") == "report.md"
    )
    report_write = next(
        operation
        for operation in result["extensions"]["x-operations"]
        if report_artifact["artifact_id"] in operation["output_refs"]
    )
    assert report_write["input_refs"] == []
    assert report_write["literal_parameters"] == {}


def test_auditor_owned_scalar_verifier_replays_mean_difference_without_execution(
    project_root,
) -> None:
    path = project_root / "examples" / "walking-skeleton" / "analysis.py"
    result = verify_mean_difference(path, "run:test")
    assert result["value"] == pytest.approx(-0.42)
    assert result["comparison"] == "treated versus control"
    assert result["orientation"] == "treated_minus_control"
    assert result["scale"] == "expression"
    assert {ref["path"] for ref in result["source_refs"]} == {"analysis.py", "data.csv"}


def test_scalar_verifier_rejects_unrecognized_code_instead_of_executing(tmp_path) -> None:
    path = tmp_path / "analysis.py"
    path.write_text("value = external_model('data.csv')\n", encoding="utf-8")
    with pytest.raises(UnsupportedScalarVerification, match="exactly one"):
        verify_mean_difference(path, "run:test")


def test_python_parser_preserves_repository_relative_nested_paths(tmp_path) -> None:
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    (workflow / "data.csv").write_text("value\n1\n", encoding="utf-8")
    path = workflow / "analysis.py"
    path.write_text(
        "from pathlib import Path\npayload = Path('data.csv').read_text()\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:nested", source_path="workflow/analysis.py")

    assert result["source_ref"]["path"] == "workflow/analysis.py"
    assert {
        ref["path"]
        for operation in result["extensions"]["x-operations"]
        for ref in operation["source_refs"]
    } == {"workflow/analysis.py"}
    assert {artifact["path"] for artifact in result["extensions"]["x-artifacts"]} == {
        "workflow/data.csv"
    }


def test_python_parser_promotes_a_schema_valid_static_graph(schema_root, tmp_path) -> None:
    path = tmp_path / "analysis.py"
    path.write_text(
        "from pathlib import Path\n"
        "payload = Path('data.csv').read_text()\n"
        "Path('result.txt').write_text(payload)\n",
        encoding="utf-8",
    )
    (tmp_path / "data.csv").write_text("value\n1\n", encoding="utf-8")
    parser_result = inspect_python(path, "audit:static", source_path="analysis.py")

    graph = build_public_static_graph([parser_result], "2026-07-28T12:00:00Z")

    registry = LocalSchemaRegistry(schema_root)
    for record in [*graph.operations, *graph.artifacts, *graph.artifact_identities]:
        registry.validate(record)
    assert graph.operations
    assert {artifact.get("path") for artifact in graph.artifacts} == {
        "data.csv",
        "result.txt",
    }


def test_python_parser_extracts_only_exact_literal_filter_parameters(tmp_path) -> None:
    path = tmp_path / "analysis.py"
    path.write_text(
        "selected = [row for row in rows if row['age'] >= 18]\n"
        "unresolved = [row for row in rows if row['score'] >= cutoff]\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:filter", source_path="analysis.py")
    filters = [
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["kind"] == "filter"
    ]

    assert filters[0]["literal_parameters"] == {
        "filter_field": "age",
        "filter_operator": "greater_than_or_equal",
        "filter_value": 18,
    }
    assert filters[1]["literal_parameters"] == {}


def test_python_parser_extracts_exact_comprehension_and_subscription_filters(
    tmp_path,
) -> None:
    path = tmp_path / "analysis.py"
    path.write_text(
        "generated = (row for row in rows if row['age'] >= 18)\n"
        "unique = {row['id'] for row in rows if row['status'] == 'included'}\n"
        "mapping = {row['id']: row for row in rows if row['site'] != 'excluded'}\n"
        "selected = frame[frame['score'] > 0.5]\n"
        "located = frame.loc[frame['group'] == 'treated']\n"
        "unresolved = frame[frame['score'] >= cutoff]\n"
        "compound = frame[(frame['score'] >= 0.5) & (frame['age'] >= 18)]\n"
        "multi = [row for row in rows if row['age'] >= 18 if row['status'] == 'included']\n",
        encoding="utf-8",
    )

    result = inspect_python(path, "audit:filter-shapes", source_path="analysis.py")
    filters = [
        operation
        for operation in result["extensions"]["x-operations"]
        if operation["kind"] == "filter"
    ]

    assert [operation["implementation"] for operation in filters] == [
        "python.generator_expression",
        "python.set_comprehension",
        "python.dict_comprehension",
        "python.boolean_subscription",
        "python.boolean_subscription",
        "python.boolean_subscription",
        "python.boolean_subscription",
        "python.list_comprehension",
    ]
    assert [operation["literal_parameters"] for operation in filters] == [
        {
            "filter_field": "age",
            "filter_operator": "greater_than_or_equal",
            "filter_value": 18,
        },
        {
            "filter_field": "status",
            "filter_operator": "equal",
            "filter_value": "included",
        },
        {
            "filter_field": "site",
            "filter_operator": "not_equal",
            "filter_value": "excluded",
        },
        {
            "filter_field": "score",
            "filter_operator": "greater_than",
            "filter_value": 0.5,
        },
        {
            "filter_field": "group",
            "filter_operator": "equal",
            "filter_value": "treated",
        },
        {},
        {
            "filter_fields": ["score", "age"],
            "filter_operators": ["greater_than_or_equal", "greater_than_or_equal"],
            "filter_values": [0.5, 18],
            "filter_logical_operator": "and",
        },
        {
            "filter_fields": ["age", "status"],
            "filter_operators": ["greater_than_or_equal", "equal"],
            "filter_values": [18, "included"],
            "filter_logical_operator": "and",
        },
    ]
    assert "frame[(frame['score']" in filters[-2]["source_refs"][0]["quoted_text"]


def test_scalar_verifier_preserves_nested_logical_paths(tmp_path) -> None:
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    (workflow / "data.csv").write_text("group,expression\ntreated,3\ncontrol,1\n", encoding="utf-8")
    analysis = workflow / "analysis.py"
    analysis.write_text(
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "value = difference(Path('data.csv'))\n",
        encoding="utf-8",
    )

    result = verify_mean_difference(analysis, "audit:nested", source_path="workflow/analysis.py")

    assert result["analysis_path"] == "workflow/analysis.py"
    assert result["input_path"] == "workflow/data.csv"
    assert {ref["path"] for ref in result["source_refs"]} == {
        "workflow/analysis.py",
        "workflow/data.csv",
    }
