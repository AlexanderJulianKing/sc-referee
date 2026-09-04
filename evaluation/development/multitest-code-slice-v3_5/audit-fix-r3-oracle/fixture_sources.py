"""Deterministic source recipes for the MT 3.5 audit-fix round-3 oracle.

Every row is an anchored edit of sealed E18 N1.  Source construction is independent of the
analyzer: expected outcomes live in ``EXPECTED_ROWS.json`` and no implementation output is
used to create either file.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E18 = REPO / "evaluation/development/blind-envelope-18-2026-09-01/cases"

E18_N1_KEY = "E18:N1:5c091f9052becdb5c3ea"
E18_N1 = E18 / "5c091f9052becdb5c3ea/project/analysis.py"
E18_N1_SHA256 = "e9b7355f0aba7a5c4f8c230a8f64f422e84993d1c64bca50229b53e9626948ff"

N1_CALL = b"    reject, adjusted_p_values, _, _ = multipletests(raw_p_values)\n"
N1_VERDICT = b'        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"\n'
N1_LOOP_BODY = b"""    for result, adjusted_p, rejected in zip(results, adjusted_p_values, reject):
        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"
        print("%s [%s]" % (result["label"], result["column"]))
        print(
            "  %-17s n = %2d   mean = %8.3f   sd = %7.3f"
            % (GROUP_A, result["n_a"], result["mean_a"], result["sd_a"])
        )
        print(
            "  %-17s n = %2d   mean = %8.3f   sd = %7.3f"
            % (GROUP_B, result["n_b"], result["mean_b"], result["sd_b"])
        )
        print("  raw p-value      = %.6g" % result["raw_p"])
        print("  adjusted value   = %.6g" % adjusted_p)
        print("  verdict          = %s (adjusted value vs %.2f)" % (verdict, ALPHA))
        print()
"""


def _once(data: bytes, needle: bytes) -> None:
    if data.count(needle) != 1:
        raise ValueError(f"anchor is not unique: {needle!r}")


def _replace(data: bytes, old: bytes, new: bytes) -> bytes:
    _once(data, old)
    return data.replace(old, new)


def _n1(
    *,
    after_call: bytes = b"",
    verdict: bytes | None = None,
    whole_loop: bytes | None = None,
) -> bytes:
    data = E18_N1.read_bytes()
    if after_call:
        data = _replace(data, N1_CALL, N1_CALL + after_call)
    if whole_loop is not None:
        data = _replace(data, N1_LOOP_BODY, whole_loop)
    elif verdict is not None:
        data = _replace(data, N1_VERDICT, verdict)
    return data


def _unrolled(template: bytes) -> bytes:
    return b"".join(template.replace(b"@", str(index).encode()) for index in range(5))


ALIGNED_UNROLLED = _unrolled(
    b'    print(results[@]["label"], "DIFFERENT" if reject[@] else "NO DIFFERENCE")\n'
)

SWAPPED_UNROLLED = b"".join(
    f'    print(results[{index}]["label"], "DIFFERENT" if reject[{1 - index if index < 2 else index}] else "NO DIFFERENCE")\n'.encode()
    for index in range(5)
)

SWAPPED_WITH_DISPLAY = b"".join(
    f'    print(results[{index}]["label"], reject[{index}], "DIFFERENT" if reject[{1 - index if index < 2 else index}] else "NO DIFFERENCE")\n'.encode()
    for index in range(5)
)

# Digests published in the round-2 verdict.  These rows are the verdict's exact bytes, not
# merely shape reproductions.
CODEX_DIGESTS = {
    "codex-r3-scope-unused-nested-parameter-unrolled": (
        "a82a609dfc6e2882b3fffe9cd9acde699c8da6f842458678d9da1cb63fd5c0d1"
    ),
    "codex-r3-scope-unused-nested-local-unrolled": (
        "263534f0b91da705ab164b3d82c604699a659a2fb81b3024b76a530d35c3657f"
    ),
    "codex-r3-scope-unused-class-attribute-unrolled": (
        "9ed6639e50bd1a53770e1e060fa37b3e3394782f95582a8963cd3955410a7d92"
    ),
    "codex-r3-scope-unused-nested-parameter-normal-loop": (
        "b1a36a1fce43a72c25c2b6a98e8eb290434cc616640f593e20779ba44522cec4"
    ),
    "codex-r3-scope-unused-nested-local-normal-loop": (
        "40e4cff5642afd9b468abceca7934a012997152789feca5f43f0e4da4010592d"
    ),
    "codex-r3-match-capture-rebinds-reject": (
        "b829ae7c606ea8a9a587a544bef22f924d3abd3d22a4322ad74d7850bc0b7047"
    ),
    "codex-r3-unrolled-results-swapped-decisions": (
        "2236ac08310c21a7f54f79776d9721277c0788a89ea0a71a7f92e4ca781830dc"
    ),
    "codex-r3-unrolled-results-swapped-with-correct-display": (
        "548618cb2313ccab9c6d8b8becd336df31f4c351ef81d24144d88c9d5afd63fc"
    ),
}


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    """Return every round-3 row as ``(reference case key, source bytes)``."""

    rejected_verdict = b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
    return {
        "sealed-e18-n1-unaltered": (E18_N1_KEY, E18_N1.read_bytes()),
        "codex-r3-scope-unused-nested-parameter-unrolled": (
            E18_N1_KEY,
            _n1(
                after_call=b"    def identity(reject):\n        return reject\n",
                whole_loop=ALIGNED_UNROLLED,
            ),
        ),
        "codex-r3-scope-unused-nested-local-unrolled": (
            E18_N1_KEY,
            _n1(
                after_call=b"    def identity():\n        reject = 1\n        return reject\n",
                whole_loop=ALIGNED_UNROLLED,
            ),
        ),
        "codex-r3-scope-unused-class-attribute-unrolled": (
            E18_N1_KEY,
            _n1(
                after_call=b"    class Reader:\n        reject = None\n",
                whole_loop=ALIGNED_UNROLLED,
            ),
        ),
        "codex-r3-scope-unused-nested-parameter-normal-loop": (
            E18_N1_KEY,
            _n1(
                after_call=b"    def identity(reject):\n        return reject\n",
                verdict=rejected_verdict,
            ),
        ),
        "codex-r3-scope-unused-nested-local-normal-loop": (
            E18_N1_KEY,
            _n1(
                after_call=b"    def identity():\n        reject = 1\n        return reject\n",
                verdict=rejected_verdict,
            ),
        ),
        "codex-r3-match-capture-rebinds-reject": (
            E18_N1_KEY,
            _n1(
                after_call=(
                    b"    match [p < ALPHA for p in raw_p_values]:\n"
                    b"        case reject:\n"
                    b"            pass\n"
                ),
                verdict=rejected_verdict,
            ),
        ),
        "codex-r3-unrolled-results-swapped-decisions": (
            E18_N1_KEY,
            _n1(whole_loop=SWAPPED_UNROLLED),
        ),
        "codex-r3-unrolled-results-swapped-with-correct-display": (
            E18_N1_KEY,
            _n1(whole_loop=SWAPPED_WITH_DISPLAY),
        ),
        "control-aligned-hand-unrolled-results": (
            E18_N1_KEY,
            _n1(whole_loop=ALIGNED_UNROLLED),
        ),
        "control-nested-nonlocal-rebinding": (
            E18_N1_KEY,
            _n1(
                after_call=(
                    b"    def replace_reject():\n"
                    b"        nonlocal reject\n"
                    b"        reject = [p < ALPHA for p in raw_p_values]\n"
                    b"    replace_reject()\n"
                ),
                whole_loop=ALIGNED_UNROLLED,
            ),
        ),
        "control-class-method-parameter-is-a-different-scope": (
            E18_N1_KEY,
            _n1(
                after_call=(
                    b"    class Reader:\n"
                    b"        def identity(self, reject):\n"
                    b"            return reject\n"
                ),
                whole_loop=ALIGNED_UNROLLED,
            ),
        ),
        "control-comprehension-target-is-a-different-scope": (
            E18_N1_KEY,
            _n1(
                after_call=(
                    b"    raw_flags = [p < ALPHA for p in raw_p_values]\n"
                    b"    copied_flags = [reject for reject in raw_flags]\n"
                ),
                verdict=rejected_verdict,
            ),
        ),
        "control-for-target-rebinds-in-the-function-scope": (
            E18_N1_KEY,
            _n1(
                after_call=(
                    b"    raw_flags = [p < ALPHA for p in raw_p_values]\n"
                    b"    for reject in raw_flags:\n"
                    b"        pass\n"
                ),
                verdict=rejected_verdict,
            ),
        ),
        "control-match-captures-unrelated-names": (
            E18_N1_KEY,
            _n1(
                after_call=(
                    b"    raw_flags = [p < ALPHA for p in raw_p_values]\n"
                    b"    match raw_flags:\n"
                    b"        case [first, *rest]:\n"
                    b"            pass\n"
                ),
                whole_loop=ALIGNED_UNROLLED,
            ),
        ),
        "control-intermediate-record-names": (
            E18_N1_KEY,
            _n1(
                whole_loop=(
                    _unrolled(b"    row@ = results[@]\n")
                    + _unrolled(
                        b'    print(row@["label"], "DIFFERENT" if reject[@] else "NO DIFFERENCE")\n'
                    )
                )
            ),
        ),
        "control-provably-constant-record-index": (
            E18_N1_KEY,
            _n1(
                whole_loop=(
                    _unrolled(b"    index@ = @\n")
                    + _unrolled(
                        b'    print(results[index@]["label"], "DIFFERENT" if reject[@] else "NO DIFFERENCE")\n'
                    )
                )
            ),
        ),
        "control-unresolved-record-index-refuses": (
            E18_N1_KEY,
            _n1(
                whole_loop=(
                    b"    index0 = len([])\n"
                    b'    print(results[index0]["label"], "DIFFERENT" if reject[0] else "NO DIFFERENCE")\n'
                    + _unrolled(
                        b'    print(results[@]["label"], "DIFFERENT" if reject[@] else "NO DIFFERENCE")\n'
                    ).replace(
                        b'    print(results[0]["label"], "DIFFERENT" if reject[0] else "NO DIFFERENCE")\n',
                        b"",
                    )
                )
            ),
        ),
    }


def source_digests() -> dict[str, str]:
    return {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_key, source) in fixture_sources().items()
    }


if __name__ == "__main__":
    for name, digest in source_digests().items():
        print(f"{name:62s} {digest}")
