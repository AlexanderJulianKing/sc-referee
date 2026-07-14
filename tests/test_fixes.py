"""`fix` — the actionable other half of a verdict. A linter that only flags is half a tool.

For each check that can flag, `fix_for` returns a correction generated from the confirmed design (no
LLM): for pseudoreplication, a RUNNABLE pseudobulk reanalysis script; for the others, the exact
edit/code to apply. A verdict the analyst can't act on is a verdict half-delivered.
"""
import ast

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.fixes import fix_for
from tests.factories import make_design


def test_pseudoreplication_fix_is_a_runnable_pseudobulk_script():
    f = Finding("experimental_unit", S.BLOCKER, "claims collapse at the donor level", metrics={})
    d = make_design(condition="condition", reference="ctrl", test="stim",
                    replicate_unit=("donor_id",), model="~ donor_id + condition")
    script = fix_for(f, d)

    assert script is not None
    ast.parse(script)                                   # it is valid Python
    for token in ("DeseqDataSet", "groupby", "donor_id", "condition", "stim", "ctrl", "~ donor_id + condition"):
        assert token in script, token


def test_confounding_alias_fix_says_re_run_the_experiment():
    f = Finding("confounding", S.BLOCKER, "aliased", metrics={"r2": 1.0})
    assert "re-run" in fix_for(f, make_design()).lower()


def test_confounding_omitted_batch_fix_adds_the_term_to_the_model():
    f = Finding("confounding", S.MAJOR, "omitted batch", metrics={"omitted": ["run"], "omitted_partial_r2": 0.3})
    fix = fix_for(f, make_design(condition="condition"))
    assert "run" in fix and "condition" in fix and "~" in fix


def test_multiple_testing_fix_mentions_benjamini_hochberg():
    assert "fdr_bh" in fix_for(Finding("multiple_testing", S.MAJOR, "uncorrected"), make_design())


def test_count_model_fix_points_at_a_count_model():
    fix = fix_for(Finding("count_model", S.MAJOR, "t-test on counts"), make_design())
    assert "DESeq2" in fix or "edgeR" in fix


def test_effect_size_fix_adds_a_fold_change_floor():
    fix = fix_for(Finding("effect_size_threshold", S.MAJOR, "negligible effects"), make_design())
    assert "log2FC" in fix or "log2fc" in fix.lower()


def test_double_dipping_fix_points_at_a_selection_aware_method():
    fix = fix_for(Finding("double_dipping", S.BLOCKER, "post-clustering"), make_design())
    assert "count-split" in fix.lower() or "held-out" in fix.lower() or "clusterde" in fix.lower()


def test_a_passing_or_abstaining_finding_has_no_fix():
    assert fix_for(Finding("confounding", S.PASS, "estimable"), make_design()) is None
    assert fix_for(Finding("experimental_unit", S.NEEDS_EVIDENCE, "underpowered"), make_design()) is None


def test_cli_fix_prints_a_correction_for_a_flagged_folder(tmp_path):
    from typer.testing import CliRunner

    from fixtures.confounding_alias.make_fixture import build
    from sc_referee.cli import app

    build(tmp_path)                       # ships a CONFIRMED sc-referee.yaml -> confounding = blocker
    result = CliRunner().invoke(app, ["fix", str(tmp_path), "--engine", "simple"])
    assert result.exit_code == 0
    out = result.stdout.lower()
    assert "confounding" in out and "re-run" in out
