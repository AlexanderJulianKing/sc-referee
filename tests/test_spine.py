"""Phase 2 — the verifier spine's SAFETY INVARIANT, made explicit and enforced.

The rule that keeps a general, LLM-proposing system specific (design doc §9.3):
  - a verifier may emit a `blocker` only if it is ENTITLED to (structural, or a pydeseq2 recompute);
  - the `simple` engine may NEVER block;
  - an LLM-proposed value can only SOFTEN a verdict, never manufacture one;
  - nothing blocks before a human confirms.

These were all true but implicit, scattered across check internals. Here they are declared
(`Check.max_status`), enforced (`audit._safe_run` clamps), and pinned.
"""
import pytest

from sc_referee import statuses as S
from sc_referee.checks.base import Finding


def test_every_registered_verifier_declares_a_max_status():
    from sc_referee.registry import build_checks

    for c in build_checks("pydeseq2"):
        assert getattr(c, "max_status", None) in S.STATUSES, f"{c.id} has no valid max_status"


def test_block_entitlement_depends_on_the_verifier_and_the_engine():
    """Which verifiers may block, and when:
      - confounding (structural) and multiple_testing (recomputes BH itself) block ENGINE-
        INDEPENDENTLY — neither uses the DE recompute engine;
      - experimental_unit blocks only on the pydeseq2 recompute, never on `simple`;
      - count_model never blocks (a wrong test model is `major`).
    (multiple_testing=BLOCKER corrects a mislabel Codex caught: it DOES earn a blocker for a
    confirmed uncorrected analysis whose claims don't survive BH.)"""
    from sc_referee.registry import build_checks

    py = {c.id: c.max_status for c in build_checks("pydeseq2")}
    simple = {c.id: c.max_status for c in build_checks("simple")}

    assert py["confounding"] == S.BLOCKER
    assert py["experimental_unit"] == S.BLOCKER
    assert py["multiple_testing"] == S.BLOCKER        # earns a blocker for uncorrected + non-surviving
    assert py["count_model"] == S.MAJOR               # a wrong test model is never a blocker
    assert simple["experimental_unit"] == S.MAJOR     # the `simple` engine may NEVER block
    # engine-independent blockers survive the `simple` engine; engine-dependent ones do not
    assert simple["confounding"] == S.BLOCKER and simple["multiple_testing"] == S.BLOCKER
    assert simple["count_model"] == S.MAJOR


def test_multiple_testing_blocker_is_not_clamped_away(tmp_path):
    """Codex Phase-2 review. multiple_testing earns a blocker (confirmed, uncorrected p-values, ≤10%
    survive BH). Labelling it max_status=major would have CLAMPED that real blocker to major — a
    SILENCED true positive, the false-negative direction. Pin that the entitlement is `blocker` and
    the spine does not clamp it."""
    import numpy as np
    import pandas as pd

    from sc_referee.audit import _clamp_to_entitlement
    from sc_referee.checks.multiple_testing import MultipleTestingCheck, evaluate_multiple_testing
    from sc_referee.design import MultiplicityContract
    from tests.factories import make_design

    rng = np.random.default_rng(0)
    p_all = np.concatenate([np.full(40, 0.04), rng.uniform(0.06, 1.0, 400)])   # 40 claims, none survive BH
    reported = pd.DataFrame({"feature_id": [f"g{i}" for i in range(len(p_all))],
                             "pvalue": p_all, "padj": p_all, "effect": np.ones(len(p_all))})

    finding = evaluate_multiple_testing(reported, make_design(
        multiplicity_contract=MultiplicityContract(
            claim_type="error_controlled_discovery", error_criterion="fdr",
            adjustment_method="benjamini_hochberg", family_complete=True,
        )
    ))
    assert finding.status == S.BLOCKER                                    # the check earns it
    assert _clamp_to_entitlement(MultipleTestingCheck(), finding).status == S.BLOCKER  # spine keeps it


def test_a_verifier_cannot_exceed_its_declared_max_status():
    """Enforcement, not just documentation: a verifier that tries to emit above its entitlement is
    clamped down by the spine. A blocker a verifier is not entitled to is the worst failure mode."""
    from sc_referee.audit import _safe_run

    class OverEager:
        id = "over"
        max_status = S.MAJOR
        def run(self, *a, **k):
            return Finding("over", S.BLOCKER, "I tried to manufacture a blocker")

    f = _safe_run(OverEager(), None, None, None)
    assert f.status == S.MAJOR                        # clamped: major-capped verifier cannot block

    class Entitled:
        id = "structural"
        max_status = S.BLOCKER
        def run(self, *a, **k):
            return Finding("structural", S.BLOCKER, "the data is rank-deficient")

    assert _safe_run(Entitled(), None, None, None).status == S.BLOCKER   # entitled: not clamped


def test_no_verifier_blocks_before_a_human_confirms(tmp_path):
    """The confounding_alias fixture is an unarguable blocker once confirmed. Before confirmation,
    NO registered verifier may emit `blocker` — the whole-audit form of the invariant."""
    from fixtures.confounding_alias.make_fixture import build
    from sc_referee.audit import run_audit
    from sc_referee.init import confirm_config, propose, write_config

    build(tmp_path)
    proposal, _ = propose(tmp_path, client=None)
    cfg = write_config(proposal, tmp_path / "sc-referee.yaml")

    before = run_audit(tmp_path, cfg)
    assert not any(f.status == S.BLOCKER for f in before.findings)

    confirm_config(cfg)
    after = run_audit(tmp_path, cfg)
    assert any(f.status == S.BLOCKER for f in after.findings)   # ...and it DOES block once confirmed


def test_a_model_proposed_reference_cannot_manufacture_a_blocker():
    """An LLM proposes which level is the reference. On a CLEAN, estimable design that choice can
    only flip a sign convention — it must never create a `blocker` where the data supports none."""
    import pandas as pd

    from sc_referee.checks.confounding import evaluate_confounding
    from tests.factories import make_design

    obs = pd.DataFrame({"donor_id": [f"D{i}" for i in range(6)],
                        "condition": ["ctrl", "ctrl", "ctrl", "stim", "stim", "stim"]})
    for ref, test in (("ctrl", "stim"), ("stim", "ctrl")):
        f = evaluate_confounding(obs, make_design(batch=(), sample_unit=("donor_id",),
                                                  reference=ref, test=test))
        assert f.status != S.BLOCKER, f"reference={ref} manufactured a blocker on a clean design"
