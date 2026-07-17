"""Phase 1 of the roles refactor (design doc 2026-07-08, §4). RED-first.

The model proposes ROLES; deterministic code synthesizes every formula. These tests pin the
invariants from §5 that make an LLM-authored, data-contradicting formula UNREPRESENTABLE rather
than merely validated. Each test names the false verdict it prevents.
"""
import json

import numpy as np
import pandas as pd
import pytest

from sc_referee.checks.confounding import evaluate_confounding
from sc_referee.design import model_terms
from tests.factories import make_design


# --------------------------------------------------------------------------- #
# I1 — an LLM can no longer author a formula, a coefficient, or the analyst-model claim
# --------------------------------------------------------------------------- #
def test_tool_schema_forbids_llm_authored_formulas():
    """Bug 4: the model returned `model="rank_genes_groups (wilcoxon) on cells grouped by 'group'"`,
    schema-valid as a string, and it reached pydeseq2. Those fields must be ABSENT from the tool
    schema — unrepresentable, not regex-checked."""
    from sc_referee.init import proposal_tool_schema

    schema = proposal_tool_schema()
    blob = json.dumps(schema)
    for forbidden in ("model", "target_coefficient", "analyst_model",
                      "contrasts", "sample_unit", "pairing_unit"):
        assert forbidden not in schema["properties"], (
            f"{forbidden!r} must not be authorable as a top-level analysis field"
        )
    # Executable formula/model fields remain unrepresentable at every nesting level. The additive
    # batch-component proposal may name a target coefficient only as a closed scope label.
    assert '"model"' not in blob and '"analyst_model"' not in blob


# --------------------------------------------------------------------------- #
# synthesis derives the formula from the DATA, per contrast
# --------------------------------------------------------------------------- #
def _levels_obs(donor_to_conditions):
    rows = []
    for donor, conds in donor_to_conditions.items():
        rows += [(donor, c) for c in conds]
    return pd.DataFrame(rows, columns=["donor_id", "condition"])


def _roles(**kw):
    from sc_referee.roles import Roles

    base = dict(analysis_type="condition_contrast_DE", condition="condition",
                replicate_unit=("donor_id",), batch=(), reference=None, unit_of_test=None,
                type_confidence="high", type_evidence=("evidence",), plain_summary="a contrast",
                confidence={"replicate_unit": "high", "condition": "high"}, unresolved=())
    return Roles(**{**base, **kw})


def test_synthesis_never_adds_replicate_to_an_unpaired_model():
    """I4. Unpaired donors (each in one arm) is the muscat/Squair design. An LLM-added
    `~ donor_id + condition` there makes confounding r2=1.0 -> FALSE BLOCKER. Synthesis must emit
    `~ condition` and confounding must then pass."""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({f"D{i}": ["ctrl"] for i in range(4)} | {f"D{i}": ["stim"] for i in range(4, 8)})
    cfg = synthesize_config(_roles(reference="ctrl"), obs)

    (c,) = cfg["contrasts"]
    assert "donor_id" not in model_terms(c["model"])
    assert c["model"] == "~ condition"
    assert c["pairing_unit"] == []


def test_synthesis_keeps_the_replicate_on_a_genuinely_paired_full_rank_design():
    """I4b. The rank check must not strip a legitimate donor term: every donor spans both arms."""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({f"D{i}": ["ctrl", "stim"] for i in range(4)})
    cfg = synthesize_config(_roles(reference="ctrl"), obs)

    (c,) = cfg["contrasts"]
    assert model_terms(c["model"]) == {"donor_id", "condition"}
    assert c["pairing_unit"] == ["donor_id"]


def test_pairing_is_decided_per_contrast_not_globally():
    """The 3-level false-blocker: is_paired is TRUE globally (every donor spans 2 levels), but on
    the c_vs_a slice each donor sits in one arm. A global paired decision blocks BOTH contrasts.
    Per-contrast synthesis must emit `~ condition` for c_vs_a and confounding must pass it."""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({"D1": ["a", "b"], "D2": ["a", "b"], "D3": ["b", "c"], "D4": ["b", "c"]})
    cfg = synthesize_config(_roles(reference="a"), obs)

    by_name = {c["name"]: c for c in cfg["contrasts"]}
    # b_vs_a: D1,D2 span it -> paired ok;  c_vs_a: no donor spans it -> must drop the donor term
    assert "donor_id" not in model_terms(by_name["c_vs_a"]["model"])

    for c in cfg["contrasts"]:
        d = make_design(condition="condition", batch=(), sample_unit=tuple(c["sample_unit"]),
                        reference=c["reference"], test=c["test"], model=c["model"],
                        target_coefficient=c["target_coefficient"])
        f = evaluate_confounding(obs[obs["condition"].isin([c["reference"], c["test"]])], d)
        assert f.status != "blocker", f"{c['name']} false-blocked: {f.verdict}"


def test_all_levels_become_contrasts_even_past_the_examples_truncation():
    """I5. `examples[:5]` truncation drops a contrast on a 6-level condition. Levels come from the
    data, so N levels -> N-1 contrasts."""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({f"D{i}": [lv] for i, lv in enumerate("abcdef" * 2)})
    cfg = synthesize_config(_roles(reference="a"), obs)
    assert len(cfg["contrasts"]) == 5
    assert cfg["contrasts"][0]["target_coefficient"] == f"condition[T.{cfg['contrasts'][0]['test']}]"


def test_an_unrecognized_reference_is_left_unresolved_not_guessed():
    """I6. Levels A/B have no control-like name; `sorted()[0]` is a coin flip that silently flips
    the sign of every log2FC. An unrecognized pair must force `reference` into unresolved."""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({"D1": ["A"], "D2": ["A"], "D3": ["B"], "D4": ["B"]})
    cfg = synthesize_config(_roles(reference=None, condition="condition"), obs)
    assert "reference" in cfg["unresolved"]
    assert cfg["confidence"].get("reference") == "low"


# --------------------------------------------------------------------------- #
# Codex Phase-1 review findings (2026-07-08)
# --------------------------------------------------------------------------- #
def test_explicit_unpaired_pairing_unit_survives_config_load(tmp_path):
    """synthesize_config emits `pairing_unit: []` for an unpaired contrast. config.load_designs did
    `_as_list(c.get("pairing_unit")) or replicate_unit`, so [] (falsy) was clobbered back to the
    replicate — silently flipping an UNPAIRED design to paired, which the `simple` engine would then
    group as pairs. `[]` must survive. (Codex Phase-1 review.)"""
    import yaml
    from sc_referee.config import load_designs

    cfg = {"analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
           "design": {"replicate_unit": ["donor_id"], "condition": "condition", "batch": []},
           "contrasts": [{"name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
                          "replicate_unit": ["donor_id"], "sample_unit": ["donor_id", "condition"],
                          "pairing_unit": [], "model": "~ condition",
                          "target_coefficient": "condition[T.stim]"}]}
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg))
    assert load_designs(p)[0].pairing_unit == []      # NOT ['donor_id']


def test_absent_pairing_unit_defaults_to_unpaired_not_replicate(tmp_path):
    """Absence cannot assert that the analyst fit a paired model. The pairing check still uses the
    replicate key to diagnose paired-capable data when the loaded declaration is unpaired."""
    import yaml
    from sc_referee.config import load_designs

    cfg = {"analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
           "design": {"replicate_unit": ["donor_id"], "condition": "condition", "batch": []},
           "contrasts": [{"name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
                          "replicate_unit": ["donor_id"], "sample_unit": ["donor_id", "condition"],
                          "model": "~ condition", "target_coefficient": "condition[T.stim]"}]}
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg))

    assert load_designs(p)[0].pairing_unit == []


def test_a_hallucinated_column_demotes_to_unresolved(tmp_path):
    """§4.6 / Q1. A model can name a column that does not exist. It must be dropped, flagged
    `unresolved`, and confidence lowered — never left as a `high`-confidence phantom. (Codex.)"""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({"D1": ["ctrl"], "D2": ["stim"]})       # the real column is `condition`
    cfg = synthesize_config(_roles(condition="not_a_column", reference=None), obs)
    assert "condition" in cfg["unresolved"]
    assert cfg["confidence"].get("condition") == "low"
    assert cfg["contrasts"] == []                              # no contrasts for a phantom condition


def test_composite_replicate_role_is_atomic_when_one_component_is_phantom():
    from sc_referee.init import synthesize_config

    obs = _levels_obs({"D1": ["ctrl"], "D2": ["stim"]})
    cfg = synthesize_config(
        _roles(reference="ctrl", replicate_unit=("donor_id", "site_typo")), obs)
    assert cfg["design"]["replicate_unit"] == []
    assert cfg["confidence"]["replicate_unit"] == "low"
    assert "replicate_unit" in cfg["unresolved"]


def test_valid_composite_replicate_role_is_preserved_complete():
    from sc_referee.init import synthesize_config

    obs = _levels_obs({"D1": ["ctrl", "stim"], "D2": ["ctrl", "stim"]})
    obs["site"] = ["A", "A", "B", "B"]
    cfg = synthesize_config(
        _roles(reference="ctrl", replicate_unit=("donor_id", "site")), obs)
    assert cfg["design"]["replicate_unit"] == ["donor_id", "site"]
    assert cfg["contrasts"][0]["replicate_unit"] == ["donor_id", "site"]


def test_deterministic_unit_of_test_overrides_the_models_value():
    """Q_uot, pinned. The model must not change WHICH checks run: a code-derived unit wins."""
    from sc_referee.init import synthesize_config

    obs = _levels_obs({"D1": ["ctrl"], "D2": ["stim"]})
    cfg = synthesize_config(_roles(reference="ctrl", unit_of_test="sample"), obs,
                            code_signals={"de_calls": ["rank_genes_groups"]})
    assert cfg["reported_results"]["unit_of_test"] == "cell"   # code (cell) beats model (sample)
