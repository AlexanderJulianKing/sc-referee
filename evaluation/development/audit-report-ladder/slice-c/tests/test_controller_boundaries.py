from __future__ import annotations

import os

import pytest
from sc_referee_evaluation.audit_ladder.slice_c.core import RefusalFacetV1
from sc_referee_evaluation.audit_ladder.slice_c.launcher import (
    _process_facets_v1,
    _resource_facets_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.protocol import validate_worker_response_v1


@pytest.mark.parametrize(
    ("field", "limit", "facet"),
    [
        ("cpu", 60, RefusalFacetV1.CPU),
        ("wall", 90, RefusalFacetV1.WALL),
        ("rss", 1_073_741_824, RefusalFacetV1.RSS),
        ("stdout", 8_388_608, RefusalFacetV1.STDOUT),
        ("stderr", 0, RefusalFacetV1.STDERR),
        ("nofile", 128, RefusalFacetV1.NOFILE),
        ("fsize", 0, RefusalFacetV1.FSIZE),
        ("core", 0, RefusalFacetV1.CORE),
    ],
)
def test_every_numeric_resource_limit_and_limit_plus_one(
    field: str,
    limit: int,
    facet: RefusalFacetV1,
) -> None:
    counters: dict[str, int | float] = {
        "cpu": 0,
        "wall": 0,
        "rss": 0,
        "stdout": 75,
        "stderr": 0,
        "nofile": 3,
        "fsize": 0,
        "core": 0,
    }
    counters[field] = limit
    assert facet not in _resource_facets_v1(**counters)  # type: ignore[arg-type]
    counters[field] = limit + 1
    assert facet in _resource_facets_v1(**counters)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("wrote", "status", "stderr_size", "expected"),
    [
        (True, 0, 0, set()),
        (False, 0, 0, {RefusalFacetV1.PROCESS_STATUS}),
        (True, None, 0, {RefusalFacetV1.PROCESS_STATUS}),
        (True, 7 << 8, 0, {RefusalFacetV1.PROCESS_STATUS}),
        (True, 9, 0, {RefusalFacetV1.PROCESS_STATUS}),
        (True, 0, 1, {RefusalFacetV1.STDERR}),
        (
            False,
            9,
            1,
            {RefusalFacetV1.STDERR, RefusalFacetV1.PROCESS_STATUS},
        ),
    ],
)
def test_write_crash_signal_status_and_stderr_siblings(
    wrote: bool,
    status: int | None,
    stderr_size: int,
    expected: set[RefusalFacetV1],
) -> None:
    assert (
        _process_facets_v1(
            wrote_request=wrote,
            status=status,
            stderr_size=stderr_size,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("response", "facet"),
    [
        (b"", RefusalFacetV1.RESPONSE_FRAME),
        (b"{}", RefusalFacetV1.RESPONSE_FRAME),
        (b"{}\n\n", RefusalFacetV1.RESPONSE_FRAME),
        (b"\xff\n", RefusalFacetV1.RESPONSE_FRAME),
        (b'{"schema":"unknown"}\n', RefusalFacetV1.RESPONSE_PROTOCOL),
        (
            b'{"facet":"unknown","schema":"slice-c-worker-refusal-v1"}\n',
            RefusalFacetV1.RESPONSE_PROTOCOL,
        ),
        (
            b'{"facet":"worker-internal","schema":"slice-c-worker-refusal-v1"}\ntrailing',
            RefusalFacetV1.RESPONSE_FRAME,
        ),
    ],
)
def test_stdout_empty_malformed_unknown_and_trailing_siblings(
    response: bytes,
    facet: RefusalFacetV1,
) -> None:
    result = validate_worker_response_v1(
        request_value={},
        request_raw=b"request\n",
        response_raw=response,
        require_world1_success=False,
    )
    assert result.facts is None
    assert result.refusal is facet


def test_wait_status_encodings_used_by_controller_are_distinct() -> None:
    assert os.WIFEXITED(0)
    assert os.WEXITSTATUS(7 << 8) == 7
    assert os.WIFSIGNALED(9)
