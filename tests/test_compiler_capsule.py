"""Frozen proposal/answer capsules replay the compiler without Claude."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.compiler.capsule import (
    InvalidationReason,
    ReplayStatus,
    freeze_capsule,
    replay_capsule,
)
from sc_referee.compiler import capsule as capsule_module
from sc_referee.csp_contracts.contamination_condensed_ceremony import (
    CondensedAnswer,
    CondensedGroup,
)
from sc_referee.derivations.contamination_compile import CompiledDerivation, compile_from_proposal
from tests.test_compile_from_proposal import _answers, _proposal, _write_synthetic


GBP07_ZIP = Path(os.environ.get(
    "GBP07_ZIP", "~/Desktop/genebench_phase1_inputs/GB-P07-data.zip"
)).expanduser()


def _synthetic_capsule(folder: Path, answer=CondensedAnswer.YES):
    _write_synthetic(folder)
    proposal = _proposal(cell_donor="subject", donor_id="subject", genotype="dose")
    answers = _answers(answer)
    compilation = compile_from_proposal(proposal, folder, answers)
    assert isinstance(compilation, CompiledDerivation)
    return freeze_capsule(compilation, proposal, answers, folder)


def test_freeze_then_replay_matches_and_never_constructs_model_client(tmp_path):
    capsule = _synthetic_capsule(tmp_path)

    with patch("anthropic.Anthropic", side_effect=AssertionError("model client constructed")) as client:
        replay = replay_capsule(capsule, tmp_path)

    assert client.call_count == 0
    assert replay.status is ReplayStatus.MATCH
    assert replay.byte_identical_guaranteed is True
    assert replay.finding.status == capsule.finding["status"]
    assert replay.finding.metrics["row_ledger_identity"] == capsule.finding["row_ledger_identity"]
    assert replay.finding.metrics["fitted_design_identity"] == capsule.finding["fitted_design_identity"]


def test_one_changed_source_byte_invalidates_without_refresh(tmp_path):
    capsule = _synthetic_capsule(tmp_path)
    source = tmp_path / "cells.csv.gz"
    raw = source.read_bytes()
    source.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))

    replay = replay_capsule(capsule, tmp_path)

    assert replay.status is ReplayStatus.INVALIDATED
    assert replay.reason is InvalidationReason.SOURCE_DRIFT
    assert replay.finding is None
    assert capsule.source_digests["cell_table"] != ""


def test_changed_answer_invalidates_but_a_frozen_no_answer_replays_stably(tmp_path):
    yes_capsule = _synthetic_capsule(tmp_path)
    changed_answers = dict(yes_capsule.answers)
    changed_answers[CondensedGroup.MEASUREMENT.value] = CondensedAnswer.NO.value
    changed_capsule = replace(yes_capsule, answers=changed_answers)

    changed = replay_capsule(changed_capsule, tmp_path)
    assert changed.status is ReplayStatus.INVALIDATED
    assert changed.reason is InvalidationReason.ANSWER_CHANGED

    no_answers = _answers()
    no_answers[CondensedGroup.MEASUREMENT] = CondensedAnswer.NO
    proposal = yes_capsule.proposal
    compilation = compile_from_proposal(proposal, tmp_path, no_answers)
    no_capsule = freeze_capsule(compilation, proposal, no_answers, tmp_path)
    replay = replay_capsule(no_capsule, tmp_path)

    assert replay.status is ReplayStatus.MATCH
    assert replay.finding.status == S.NEEDS_EVIDENCE
    assert S.human_state(replay.finding) == S.NOT_CHECKED


def test_semantic_root_ignores_wall_clock_timestamp(tmp_path):
    capsule = _synthetic_capsule(tmp_path)

    early = replace(capsule, frozen_at="2026-07-12T01:02:03Z")
    late = replace(capsule, frozen_at="2036-01-01T00:00:00Z")

    assert early.root_digest == late.root_digest == capsule.root_digest
    assert early.to_json() != late.to_json()
    assert replay_capsule(early, tmp_path).status is ReplayStatus.MATCH


def test_environment_mismatch_still_replays_without_exact_identity_guarantee(tmp_path):
    capsule = _synthetic_capsule(tmp_path)
    different = dict(capsule.environment)
    different["numpy"] = "different-environment"

    with patch.object(capsule_module, "environment_identity", return_value=different):
        replay = replay_capsule(capsule, tmp_path)

    assert replay.status is ReplayStatus.ENVIRONMENT_MISMATCH
    assert replay.reason is InvalidationReason.ENVIRONMENT_CHANGED
    assert replay.finding.status == capsule.finding["status"]
    assert replay.byte_identical_guaranteed is False


def test_synthetic_renamed_folder_replays_from_proposal_not_literal_names(tmp_path):
    renamed = tmp_path / "arbitrary-study-name"
    renamed.mkdir()
    capsule = _synthetic_capsule(renamed)

    replay = replay_capsule(capsule, renamed)

    assert replay.status is ReplayStatus.MATCH
    assert replay.compilation.design.genotype_column == "dose"
    assert replay.compilation.design.replicate_unit == ["subject"]


@pytest.mark.skipif(not GBP07_ZIP.exists(), reason="GB-P07 data not present — set GBP07_ZIP")
def test_real_release_bytes_freeze_and_replay(tmp_path):
    with ZipFile(GBP07_ZIP) as archive:
        for member in ("cells.csv.gz", "donors.csv.gz", "empty_drops.csv.gz"):
            (tmp_path / member).write_bytes(archive.read(member))
    pd.DataFrame({"coefficient": [0.4839]}).to_csv(tmp_path / "submission.csv", index=False)
    (tmp_path / "method.txt").write_text("no ambient adjustment", encoding="utf-8")
    proposal = _proposal()
    answers = _answers()
    compilation = compile_from_proposal(proposal, tmp_path, answers)
    capsule = freeze_capsule(compilation, proposal, answers, tmp_path)

    replay = replay_capsule(capsule, tmp_path)

    assert replay.status is ReplayStatus.MATCH
    assert replay.finding.status == compilation.finding.status
    assert replay.finding.metrics == compilation.finding.metrics
