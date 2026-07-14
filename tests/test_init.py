"""`init` — Claude proposes, a person confirms. The one load-bearing use of the model.

Hard signals run FIRST and skip Claude when the folder is unambiguous. Claude is called only
where the deterministic classifier cannot resolve a role — which is exactly where a
name-matching regex would guess wrong. Nothing can be blocked until a human ratifies.
"""
import json
from types import SimpleNamespace

import pytest
import yaml

from fixtures.ambiguous_group.make_fixture import build as build_ambiguous
from fixtures.confounding_alias.make_fixture import build as build_clear
from sc_referee.audit import run_audit
from sc_referee.code_signals import parse_code_signals, unit_of_test_from
from sc_referee.init import (
    build_init_input,
    confirm_config,
    hard_signal_proposal,
    propose,
    write_config,
)
from sc_referee.schema_validation import validate


# --------------------------------------------------------------------------- #
# code signals — parsed, never executed
# --------------------------------------------------------------------------- #
def test_detects_a_per_cell_de_call(tmp_path):
    (tmp_path / "analysis.py").write_text(
        "import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'group', method='wilcoxon')\n")
    cs = parse_code_signals(tmp_path)
    assert "rank_genes_groups" in cs["de_calls"]
    assert "scanpy" in cs["imports"]
    assert unit_of_test_from(cs) == "cell"


def test_detects_a_pseudobulk_de_call(tmp_path):
    (tmp_path / "run.py").write_text(
        "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts=pb, metadata=m)\n")
    cs = parse_code_signals(tmp_path)
    assert unit_of_test_from(cs) == "sample"


def test_ambiguous_or_absent_code_yields_no_unit_rather_than_a_guess(tmp_path):
    """`ttest_ind` is applied to cells and to pseudobulk alike. Guessing "cell" mis-routed the
    checks and made `count_model` unreachable. None is the honest answer; the human resolves it.
    (Opus review 2026-07-08.)"""
    assert unit_of_test_from(parse_code_signals(tmp_path)) is None      # no code at all
    assert unit_of_test_from({"de_calls": ["ttest_ind"]}) is None       # ambiguous
    assert unit_of_test_from({"de_calls": ["mannwhitneyu"]}) is None
    assert unit_of_test_from({"de_calls": ["rank_genes_groups"]}) == "cell"
    assert unit_of_test_from({"de_calls": ["pseudobulk", "ttest_ind"]}) == "sample"


# --------------------------------------------------------------------------- #
# hard signals resolve the easy case without ever calling Claude
# --------------------------------------------------------------------------- #
def test_unambiguous_folder_resolves_deterministically(tmp_path):
    build_clear(tmp_path)
    proposal, source = propose(tmp_path, client=None)

    assert source == "hard_signals"
    assert proposal["design"]["condition"] == "culture_condition"
    assert proposal["design"]["replicate_unit"] == ["donor_id"]
    assert proposal["design"]["batch"] == ["processing_run"]
    assert proposal["contrasts"][0]["reference"] == "ctrl"   # control-ish level wins
    assert proposal["contrasts"][0]["test"] == "stim"
    assert proposal["confidence"]["condition"] == "high"
    # The fixture ships no analysis code and the no-LLM path cannot capture the fitted covariates.
    assert proposal["unresolved"] == ["unit_of_test", "analyst_adjusted_for"]


def test_a_column_named_group_is_deliberately_ambiguous(tmp_path):
    """`group` is NOT a condition token. A regex cannot know whether it means condition,
    cluster, or batch — so the hard classifier must decline and hand off to Claude."""
    build_ambiguous(tmp_path)
    assert hard_signal_proposal(build_init_input(tmp_path)) is None


def test_without_a_model_the_ambiguous_case_degrades_honestly(tmp_path):
    build_ambiguous(tmp_path)
    proposal, source = propose(tmp_path, client=None)

    assert source == "heuristic_no_llm"
    assert "condition" in proposal["unresolved"]
    assert proposal["confidence"]["condition"] == "low"      # low confidence => cannot block
    assert proposal["design"]["replicate_unit"] == ["donor_id"]   # what IS resolvable, is resolved


# --------------------------------------------------------------------------- #
# the Claude path
# --------------------------------------------------------------------------- #
def _fake_client(payload):
    """Replays a `tool_use` roles payload (dict) or bare prose (str). The create() shim asserts the
    call shape the REAL API demands — no `temperature` (deprecated for claude-opus-4-8; bug 1), a
    forced `tool_choice` — because a mock that accepts anything is what let four real bugs ship."""
    def create(**kw):
        assert "temperature" not in kw, "init must not send `temperature` (deprecated for this model)"
        if isinstance(payload, str):
            content = [SimpleNamespace(type="text", text=payload)]        # prose: no tool_use block
        else:
            assert kw.get("tool_choice"), "init must FORCE the propose_design tool call"
            content = [SimpleNamespace(type="tool_use", name="propose_design", input=payload)]
        return SimpleNamespace(content=content)

    return SimpleNamespace(messages=SimpleNamespace(create=create))


def _valid_claude_payload():
    """ROLES only — no `model`, `contrasts`, `target_coefficient`. The model assigns roles; arithmetic
    synthesizes the formula. (design doc §4.2.)"""
    return {
        "analysis_type": "condition_contrast_DE",
        "type_confidence": "high",
        "type_evidence": ["obs has donor_id + a 2-level `group` column", "code calls rank_genes_groups"],
        "plain_summary": "This looks like a condition comparison across 6 donors; `group` is the condition.",
        "design": {"replicate_unit": ["donor_id"], "condition": "group", "batch": ["processing_run"]},
        "reference": "A",
        "unit_of_test": "cell",
        "analyst_adjusted_for": ["processing_run", "group"],
        "confidence": {"replicate_unit": "high", "condition": "high",
                       "analyst_adjusted_for": "high"},
        "unresolved": [],
    }


def test_claude_resolves_the_ambiguous_column(tmp_path):
    build_ambiguous(tmp_path)
    proposal, source = propose(tmp_path, client=_fake_client(_valid_claude_payload()))

    assert source == "claude"
    assert proposal["design"]["condition"] == "group"
    assert proposal["plain_summary"]                      # a human-ratifiable sentence
    assert len(proposal["type_evidence"]) >= 1            # ...with its evidence
    validate(proposal, "sc_referee.schema.json")


def test_claude_output_is_schema_validated_and_prose_is_rejected(tmp_path):
    build_ambiguous(tmp_path)
    with pytest.raises(ValueError):
        propose(tmp_path, client=_fake_client("Sure! Here's my analysis of your data..."))


def test_claude_unknown_analysis_type_is_normalized_to_safe_other(tmp_path):
    build_ambiguous(tmp_path)
    bad = _valid_claude_payload() | {"analysis_type": "vibes_based_DE"}
    proposal, source = propose(tmp_path, client=_fake_client(bad))
    assert source == "claude"
    assert proposal["analysis_type"] == "other"
    assert "analysis_type" in proposal["unresolved"]


def test_claude_medium_role_confidence_is_conservatively_normalized_before_validation(tmp_path):
    """Provider enum drift must not crash init or manufacture high confidence."""
    build_ambiguous(tmp_path)
    payload = _valid_claude_payload()
    payload["confidence"] = {"replicate_unit": "medium", "condition": "high"}

    proposal, source = propose(tmp_path, client=_fake_client(payload))
    out = write_config(proposal, tmp_path / "sc-referee.yaml")
    raw = yaml.safe_load(out.read_text())

    assert source == "claude"
    assert raw["confidence"] == {"replicate_unit": "low", "condition": "high",
                                 "analyst_adjusted_for": "low"}
    assert raw["confirmed_by_human"] is False
    validate(raw, "sc_referee.schema.json")


@pytest.mark.parametrize("value", ["high", "low"])
def test_valid_claude_role_confidence_is_unchanged(tmp_path, value):
    build_ambiguous(tmp_path)
    payload = _valid_claude_payload()
    payload["confidence"] = {"replicate_unit": value, "condition": value,
                             "analyst_adjusted_for": value}

    proposal, source = propose(tmp_path, client=_fake_client(payload))

    assert source == "claude"
    assert proposal["confidence"] == {"replicate_unit": value, "condition": value,
                                      "analyst_adjusted_for": value}


def test_all_proposer_enum_drift_fails_closed_instead_of_crashing_init(tmp_path):
    """Unknown enum values become the non-accusatory alternatives before schema validation."""
    build_ambiguous(tmp_path)
    payload = _valid_claude_payload() | {
        "analysis_type": "novel_analysis",
        "type_confidence": "certain",
        "unit_of_test": "organism",
        "confidence": {"replicate_unit": "certain", "condition": None},
        "unresolved": ["new_role"],
    }

    proposal, source = propose(tmp_path, client=_fake_client(payload))

    assert source == "claude"
    assert proposal["analysis_type"] == "other"
    assert proposal["type_confidence"] == "low"
    # The provider's unknown unit becomes None, then the existing deterministic code signal wins.
    assert proposal["reported_results"]["unit_of_test"] == "cell"
    assert proposal["confidence"] == {"replicate_unit": "low", "condition": "low",
                                      "analyst_adjusted_for": "low"}
    assert set(proposal["unresolved"]) == {
        "analysis_type", "condition", "replicate_unit", "batch", "analyst_adjusted_for",
        "reference", "unit_of_test",
    }


# --------------------------------------------------------------------------- #
# confirm — and the invariant that nothing blocks before it
# --------------------------------------------------------------------------- #
def test_written_config_is_schema_valid_and_starts_unconfirmed(tmp_path):
    build_clear(tmp_path)
    proposal, _ = propose(tmp_path, client=None)
    out = write_config(proposal, tmp_path / "proposed.yaml")

    raw = yaml.safe_load(out.read_text())
    validate(raw, "sc_referee.schema.json")
    assert raw["confirmed_by_human"] is False


def test_confirm_flips_the_flag(tmp_path):
    build_clear(tmp_path)
    proposal, _ = propose(tmp_path, client=None)
    out = write_config(proposal, tmp_path / "proposed.yaml")
    confirm_config(out)
    assert yaml.safe_load(out.read_text())["confirmed_by_human"] is True


def test_nothing_blocks_before_a_human_confirms(tmp_path):
    """THE INVARIANT. The confounding_alias fixture is an unarguable blocker — but on a
    freshly-proposed, unconfirmed config it must downgrade to needs_evidence."""
    build_clear(tmp_path)
    proposal, _ = propose(tmp_path, client=None)
    cfg = write_config(proposal, tmp_path / "sc-referee.yaml")

    before = run_audit(tmp_path, cfg)
    assert before.worst_status() == "needs_evidence"
    assert before.ci_fails() is False

    confirm_config(cfg)
    after = run_audit(tmp_path, cfg)
    assert after.worst_status() == "blocker"
    assert after.ci_fails() is True
