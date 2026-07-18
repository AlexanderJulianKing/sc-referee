"""Tests for wiring the confounder-candidate diagnostic into the audit review flow.

The diagnostic is EVIDENCE, not a gate. These pin that the hook runs from an audit context, abstains
loudly (never silently) when inputs are missing, and never breaks the audit.
"""
import json
import types

import numpy as np
import pandas as pd

from sc_referee.inference.audit_hook import run_confounder_diagnostic


def _bundle(source, cells, counts, feats):
    b = types.SimpleNamespace()
    b.observations = cells
    m = types.SimpleNamespace(counts=counts, feature_index=feats, long=None, kind="counts")
    b.measure = m
    b.code_signals = {"sources": [source]}
    return b


def _eqtl_context(seed=0):
    rng = np.random.default_rng(seed)
    n = 240
    cells = pd.DataFrame({
        "donor": np.repeat(np.arange(24), 10),
        "total_umi": rng.integers(800, 1200, n).astype(float),
    })
    cells["g"] = (cells.donor % 3).astype(float)
    feats = ["HBB", "CXCL10", "IFI6"]
    counts = rng.integers(0, 50, (n, 3)).astype(float)
    source = '''
p_amb = {gene: empty[gene].sum()/empty.total_umi.sum() for gene in ["HBB","CXCL10"]}
c["rho"] = np.clip(c.HBB/(c.total_umi*p_amb["HBB"]), 0, 1)
'''
    bundle = _bundle(source, cells, counts, feats)
    design = types.SimpleNamespace(genotype_column="g", exposure_column=None,
                                   unit_of_test="donor", analysis_type="eqtl")
    return bundle, design


def test_runs_from_an_eqtl_audit_context():
    bundle, design = _eqtl_context()
    out = run_confounder_diagnostic(bundle, design)
    assert out["ran"] is True
    assert out["unit"] == "donor"
    assert out["exposure"] == "g"
    # it surfaced the derived candidate the source computes (rho) as leg-1 evidence
    rec = json.loads(out["record"])
    r = json.loads(rec["leg1"]["record"])
    pop = r if "summaries" in r else r.get("post_gate", r.get("pre_gate", {}))
    names = {s["name"] for s in pop.get("summaries", [])}
    assert "rho" in names
    assert "markdown" in out and "evidence, not a verdict" in out["markdown"]


def test_abstains_without_an_exposure():
    bundle, design = _eqtl_context()
    design.genotype_column = None
    out = run_confounder_diagnostic(bundle, design)
    assert out["ran"] is False
    assert "no declared exposure" in out["abstained"]


def test_abstains_without_a_resolvable_unit():
    bundle, design = _eqtl_context()
    design.unit_of_test = None
    bundle.code_signals = {"sources": ["x = 1"]}     # nothing to infer a unit from
    out = run_confounder_diagnostic(bundle, design)
    assert out["ran"] is False
    assert "unit of test" in out["abstained"]


def test_abstains_when_the_frame_lacks_the_exposure_or_unit():
    bundle, design = _eqtl_context()
    bundle.observations = bundle.observations.drop(columns=["g"])   # exposure gone from the data
    out = run_confounder_diagnostic(bundle, design)
    assert out["ran"] is False
    assert "missing required column" in out["abstained"]


def test_abstains_without_source_but_does_not_throw():
    bundle, design = _eqtl_context()
    bundle.code_signals = {"sources": []}
    out = run_confounder_diagnostic(bundle, design)
    assert out["ran"] is False
    assert "source" in out["abstained"]


def test_never_throws_on_a_malformed_bundle():
    design = types.SimpleNamespace(genotype_column="g", exposure_column=None,
                                   unit_of_test="donor", analysis_type="eqtl")
    broken = types.SimpleNamespace(observations=None, measure=None, code_signals=None)
    out = run_confounder_diagnostic(broken, design)
    assert out["ran"] is False          # abstains, does not raise


def test_audit_result_has_a_non_gating_diagnostics_field():
    from sc_referee.audit import AuditResult
    r = AuditResult()
    assert r.diagnostics == []
    before = r.ci_fails()
    # Diagnostics never participate in the gate; the empty/unconfirmed audit already fails closed.
    r.diagnostics.append({"diagnostic": "confounder_candidate", "ran": True})
    assert r.ci_fails() is before          # diagnostics are evidence, never gating
    assert r.worst_status()  # does not consult diagnostics


def test_report_json_carries_diagnostics_as_evidence():
    from sc_referee.audit import AuditResult
    from sc_referee.report import to_json
    r = AuditResult(diagnostics=[{"diagnostic": "confounder_candidate", "ran": False,
                                  "abstained": "test"}])
    blob = json.loads(to_json(r))
    assert "diagnostics" in blob
    assert blob["diagnostics"][0]["diagnostic"] == "confounder_candidate"
