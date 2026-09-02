import secrets
from pathlib import Path

import pytest

from sc_referee.cache_auth import CACHE_AUTHENTICATION_ENV, encode_cache_authentication_key


@pytest.fixture(autouse=True)
def isolated_cache_authentication_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests and their subprocesses out of the user's platform credential store."""

    monkeypatch.setenv(
        CACHE_AUTHENTICATION_ENV,
        encode_cache_authentication_key(secrets.token_bytes(32)),
    )


@pytest.fixture(autouse=True)
def pin_frozen_stage1_projection_schema(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replay frozen Stage-1 controllers with the v0.20 record version they bind."""

    if request.path.name not in {
        "test_first_direct_three_case_stage1_codex_recovery.py",
        "test_first_direct_three_case_stage1_protocol.py",
        "test_first_direct_three_case_stage1_semantic_recovery_clean_recorder.py",
        "test_first_direct_three_case_stage1_semantic_recovery_recorder.py",
    }:
        return
    from sc_referee_evaluation import review_semantic_payload

    monkeypatch.setattr(review_semantic_payload, "SCHEMA_VERSION", "0.20.0")


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def schema_root(project_root: Path) -> Path:
    return project_root / "reference" / "schemas-v0.21.0"


# ---------------------------------------------------------------------------
# Parallel-execution safety. Test infrastructure only: no test file changes,
# and nothing any test asserts is touched.
#
# `pytest` with no flags is unchanged -- every test still runs, in collected
# order, in one process. Parallelism is opt-in:
#
#     pytest -n auto --dist loadfile --serial-lane=exclude
#     pytest --serial-lane=only
#
# `--serial-lane` exists instead of a `-m "not serial"` recipe because pytest's
# `-m` holds a single value: a `-m` on the command line REPLACES the
# `-m 'not retired_report_lane'` already in addopts, silently re-admitting the
# retired report lane. A caller who prefers markers must therefore spell out
# `-m "not retired_report_lane and not serial"`. This option composes instead
# of overriding, so the default marker expression always survives.
#
# `--dist loadfile` is required, not cosmetic. The default `--dist load` splits
# one file across workers, which re-runs module-scoped fixtures in every worker
# and breaks modules whose later tests read state an earlier test wrote.
#
# A test is listed below when its outcome depends on wall-clock progress (a
# thread barrier, a future deadline, a subprocess timeout) or on module state
# an earlier test in the same file established. Process-global state that is
# merely shared *inside* one worker -- the 3.4 admission census,
# `monkeypatch.chdir`, `monkeypatch.setenv` -- is deliberately NOT listed:
# xdist workers are separate processes and tests inside a worker still run one
# at a time, so that state is already isolated.

_SERIAL_MODULES = frozenset(
    {
        # threading.Barrier(2, timeout=2), Event.wait(timeout=2/3) and
        # Future.result(timeout=4): two threads must reach a rendezvous inside
        # a two-second budget.
        "test_first_direct_three_case_stage1_semantic_recovery_clean_transports.py",
        "test_first_direct_three_case_stage1_semantic_recovery_transports.py",
        "test_first_direct_stage1_recovery_codex_replacement_calibration_transport.py",
        # ThreadPoolExecutor(max_workers=2) asserting a concurrent-registration
        # outcome.
        "test_execution_authorization_registry.py",
        # subprocess.run(..., timeout=5) around a pinned-runtime recompute.
        "test_founder_orientation_semantic_v301_hardening.py",
        # subprocess.run(..., timeout=30) x3 spawning the multiple-testing
        # sandbox interpreter.
        "test_multiple_testing_recognition_analyzer.py",
        # subprocess.run(..., timeout=120) x9 spawning the dependence sandbox
        # interpreter.
        "test_dependence_recognition_v2_growth14.py",
        # SubprocessExecutionRuntime wall-timeout adapter tests.
        "test_execution_runtime.py",
        # subprocess.run(..., timeout=30) against the pinned dosage sandbox
        # interpreter. Observed failing with TimeoutExpired under `-n 6` while
        # passing serially 3/3.
        "test_dosage_pilot_envelope.py",
        # Spawns a child interpreter whose importlib.metadata scan must see the
        # evaluation egg-info. Observed returning an incomplete distribution
        # closure under `-n 6` while passing serially 3/3; the precise mechanism
        # is not established, so it is kept out of the parallel lane.
        "test_evaluation_lazy_init.py",
        # REVEAL_EVIDENCE is written by one test in this module and read by a
        # later one, so the file must keep its collected order in one process.
        "test_selected_result_verifier_qualification_controller.py",
    }
)

_SERIAL_TESTS = frozenset(
    {
        # Holds a real project cache writer lease while a child sc-referee
        # audit must finish inside subprocess.run(..., timeout=30).
        (
            "test_cache_diff.py",
            "test_contended_cache_writer_lease_fails_open_for_audit_and_preserves_index",
        ),
    }
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--serial-lane",
        action="store",
        default="all",
        choices=("all", "exclude", "only"),
        help=(
            "Which half of the serial lane to run: 'all' (default) runs everything, "
            "'exclude' drops the tests marked serial for a parallel pass, 'only' keeps "
            "just those. Composes with the marker expression in addopts, unlike -m."
        ),
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        name = getattr(item, "originalname", None) or item.name
        if item.path.name in _SERIAL_MODULES or (item.path.name, name) in _SERIAL_TESTS:
            item.add_marker(pytest.mark.serial)

    lane = config.getoption("--serial-lane")
    if lane == "all":
        return
    wanted = lane == "only"
    keep: list[pytest.Item] = []
    dropped: list[pytest.Item] = []
    for item in items:
        is_serial = item.get_closest_marker("serial") is not None
        (keep if is_serial == wanted else dropped).append(item)
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = keep
