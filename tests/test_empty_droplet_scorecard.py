from pathlib import Path

from sc_referee.registry import build_checks
from tests.benchmark.scenarios import evaluate_battery


def test_feeder_is_not_registered_as_a_scientific_check():
    ids = {check.id for check in build_checks(engine="simple")}
    assert "empty_droplet_raw_counts" not in ids
    assert "ambient_tracer_fraction" not in ids


def test_empty_droplet_package_has_no_finding_emitter():
    root = Path("src/sc_referee/empty_droplet")
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(root.glob("*.py")))
    assert "Finding(" not in source
    assert "checks.base import Finding" not in source
    assert not (root / "consumer.py").exists()


def test_scorecard_false_alarms_remain_zero(tmp_path):
    scorecard = evaluate_battery(tmp_path / "scorecard")
    assert scorecard.false_alarm_count == 0
