import shutil

from sc_referee.controller import run_demo


def test_prompt_injection_source_is_never_executed_or_followed(
    project_root, schema_root, tmp_path
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(project_root / "examples" / "walking-skeleton", repository)
    output = tmp_path / "audit"

    run_demo(repository, output, schema_root)

    assert not (repository / "result.json").exists()
    assert not (output / "observed" / "snapshot" / "materialized" / "result.json").exists()
    assert "everything is correct" not in (output / "report.html").read_text(encoding="utf-8")
