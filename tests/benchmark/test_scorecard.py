from pathlib import Path

import pytest

from tests.benchmark.scenarios import SCENARIOS, evaluate_battery, render_scorecard


@pytest.fixture(scope="session")
def benchmark_scorecard(tmp_path_factory):
    root = tmp_path_factory.mktemp("sc_referee_benchmark")
    scorecard = evaluate_battery(root, emit=print)
    return scorecard


def test_correct_analyses_have_zero_false_alarms(benchmark_scorecard):
    assert benchmark_scorecard.false_alarm_count == 0, "\n" + "\n".join(
        row.diagnostic for row in benchmark_scorecard.false_alarms
    )


def test_scorecard_records_every_declared_expectation(benchmark_scorecard):
    expected_rows = sum(len(scenario.expectations) for scenario in SCENARIOS)
    assert len(benchmark_scorecard.rows) == expected_rows


def test_checked_in_scorecard_matches_the_shipped_engine(benchmark_scorecard):
    scorecard_path = Path(__file__).with_name("SCORECARD.md")
    assert scorecard_path.read_text() == render_scorecard(benchmark_scorecard)
def test_scorecard_has_no_ratified_conditional_obligation(benchmark_scorecard):
    scenario_source = Path("tests/benchmark/scenarios.py").read_text()
    assert "between_group_adjustment_obligation/v1" not in scenario_source
    assert all(
        row.invariant != "confounding_random_intercept_conditional"
        for row in benchmark_scorecard.rows
    )
    assert benchmark_scorecard.false_alarm_count == 0
