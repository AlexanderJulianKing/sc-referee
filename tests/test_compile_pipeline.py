"""End-to-end orchestration for the explicit compiler path."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path

import pytest

from sc_referee import statuses as S
from sc_referee.compiler.capsule import ReplayStatus, replay_capsule
from sc_referee.compiler.pipeline import run_compile_audit
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from tests.test_compile_from_proposal import _answers, _proposal, _unpack_real_folder


GBP07_ZIP = Path(os.environ.get(
    "GBP07_ZIP", "~/Desktop/genebench_phase1_inputs/GB-P07-data.zip"
)).expanduser()
HAS_GBP07 = GBP07_ZIP.exists()


def _fake_proposer(_inventory):
    return _proposal()


@pytest.mark.skipif(not HAS_GBP07, reason="GB-P07 data not present — set GBP07_ZIP")
def test_end_to_end_fake_proposer_yields_conditional_major_and_model_free_match(tmp_path):
    _unpack_real_folder(tmp_path)

    result = run_compile_audit(tmp_path, answers=_answers(), proposer=_fake_proposer)

    assert result.normal_audit_applies is False
    assert result.finding.status == S.MAJOR
    assert result.finding.conditional_on is not None
    assert result.replay_status is ReplayStatus.MATCH
    replay = replay_capsule(result.capsule, tmp_path)
    assert replay.status is ReplayStatus.MATCH
    assert replay.finding.status == S.MAJOR


@pytest.mark.skipif(not HAS_GBP07, reason="GB-P07 data not present — set GBP07_ZIP")
def test_single_no_is_not_checked_end_to_end(tmp_path):
    _unpack_real_folder(tmp_path)
    answers = _answers()
    answers[CondensedGroup.TIMING] = CondensedAnswer.NO

    result = run_compile_audit(tmp_path, answers=answers, proposer=_fake_proposer)

    assert S.human_state(result.finding) == S.NOT_CHECKED
    assert result.finding.coverage == S.NOT_RUN
    assert result.replay_status is ReplayStatus.MATCH


def test_no_compile_needed_signals_normal_path_without_calling_proposer(tmp_path):
    from fixtures.confounding_alias.make_fixture import build

    build(tmp_path)

    def forbidden(_inventory):
        raise AssertionError("proposer must not be called for a recognized single-matrix folder")

    result = run_compile_audit(tmp_path, answers={}, proposer=forbidden)

    assert result.normal_audit_applies is True
    assert result.proposal is None
    assert result.finding is None
    assert result.capsule is None
    assert result.replay_status is None
    assert "normal deterministic audit path" in result.summary


@pytest.mark.skipif(not HAS_GBP07, reason="GB-P07 data not present — set GBP07_ZIP")
def test_compile_abstention_is_a_typed_not_checked_result(tmp_path):
    _unpack_real_folder(tmp_path)

    def invalid_table_proposer(_inventory):
        proposal = _proposal()
        bindings = tuple(
            replace(binding, candidate_value={"artifact_path": "empty_drops.csv.gz"})
            if binding.destination.field == "empty_droplet_table" else binding
            for binding in proposal.requested_bindings
        )
        return replace(proposal, requested_bindings=bindings)

    result = run_compile_audit(
        tmp_path, answers=_answers(), proposer=invalid_table_proposer
    )

    assert result.abstention is not None
    assert result.abstention.reason_code.value == "invalid_binding"
    assert result.finding is None
    assert result.capsule is None
    assert result.summary.startswith("NOT_CHECKED / could not compile: invalid_binding:")


@pytest.mark.skipif(not HAS_GBP07, reason="GB-P07 data not present — set GBP07_ZIP")
def test_rendered_summary_is_conditional_and_contains_no_causal_overclaim(tmp_path):
    _unpack_real_folder(tmp_path)

    summary = run_compile_audit(
        tmp_path, answers=_answers(), proposer=_fake_proposer
    ).rendered_summary

    assert (
        "Conditional on the ratified premises, the submitted fitted design does not contain "
        "the exact ratified contamination basis"
    ) in summary
    assert "proposed by Claude" in summary
    assert "replayed without a model: MATCH" in summary
    lowered = summary.lower()
    for forbidden in (
        "caused the sign error",
        "caused a sign error",
        "sign error",
        "reproduces the reference answer",
        "reproduce the reference answer",
        "reference answer",
    ):
        assert forbidden not in lowered


@pytest.mark.skipif(not HAS_GBP07, reason="GB-P07 data not present — set GBP07_ZIP")
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="needs live Claude API key")
def test_live_end_to_end_compile_pipeline(tmp_path):
    _unpack_real_folder(tmp_path)

    result = run_compile_audit(tmp_path, answers=_answers())

    assert result.finding.status == S.MAJOR
    assert result.proposal.proposer.kind == "claude"
    assert result.replay_status is ReplayStatus.MATCH
