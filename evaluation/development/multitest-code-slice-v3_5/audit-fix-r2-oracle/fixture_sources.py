"""Deterministic source recipes for the MT 3.5 audit-fix round-2 oracle.

Every recipe is an anchored edit of the sealed E18 N1 envelope source, exactly as the round-1
oracle and the MT 3.4 fix-round oracles are.  The recipes own source selection and mutation
only; the expected rows live in `EXPECTED_ROWS.json` and are authored from the round-2 design
and from each row's own frozen 3.4 sibling, never from analyzer output.

Four groups of sources are carried.

* The five audit blocker sources, reconstructed from the recipes in the round-1 Codex verdict.
  Each one's SHA-256 is asserted against the digest the verdict published.
* The five inline-verdict variants the round-1 fix regressed on.  Two of them are the verdict's
  own published bytes; the other three are the unrolled and `.format()` spellings the verdict
  names but publishes only digests for, so they are rebuilt by shape and carry their own
  digests.  `CODEX_DIGESTS` says which is which and the test asserts it.
* Correct consumption forms from the verdict's own probe table that this round must not move.
  The verdict published digests without sources for that table, so these are shape
  reproductions and are labelled as such in `EXPECTED_ROWS.json`.
* Fresh adversarial variants, one per way a return name can be rebound or a correction output
  can reach the wrong outcome.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E18 = REPO / "evaluation/development/blind-envelope-18-2026-09-01/cases"

E18_N1_KEY = "E18:N1:5c091f9052becdb5c3ea"
E18_N1 = E18 / "5c091f9052becdb5c3ea/project/analysis.py"

# --- anchors -----------------------------------------------------------------------------
#
# The sealed E18 N1 correction statement, the two-line opening of its presentation loop, and
# the whole presentation loop.  Every recipe replaces one of the three and nothing else.
N1_CALL = b"    reject, adjusted_p_values, _, _ = multipletests(raw_p_values)\n"
N1_LOOP_HEAD = b"""    for result, adjusted_p, rejected in zip(results, adjusted_p_values, reject):
        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"
"""
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
SCIPY_IMPORT = b"from scipy import stats\n"


def _once(data: bytes, needle: bytes) -> None:
    if data.count(needle) != 1:
        raise ValueError(f"anchor is not unique: {needle!r}")


def _replace(data: bytes, old: bytes, new: bytes) -> bytes:
    _once(data, old)
    return data.replace(old, new)


def _n1(
    *,
    after_call: bytes = b"",
    before_call: bytes = b"",
    loop_head: bytes | None = None,
    verdict: bytes | None = None,
    whole_loop: bytes | None = None,
    imports: bytes = b"",
) -> bytes:
    data = E18_N1.read_bytes()
    if imports:
        data = _replace(data, SCIPY_IMPORT, SCIPY_IMPORT + imports)
    if before_call or after_call:
        data = _replace(data, N1_CALL, before_call + N1_CALL + after_call)
    if whole_loop is not None:
        data = _replace(data, N1_LOOP_BODY, whole_loop)
    elif loop_head is not None:
        data = _replace(data, N1_LOOP_HEAD, loop_head)
    elif verdict is not None:
        data = _replace(data, N1_VERDICT, verdict)
    return data


def _inline_loop(body: bytes) -> bytes:
    """Replace the whole presentation loop with a two-line loop that prints one verdict."""

    return b"    for i, result in enumerate(results):\n" + body


def _unrolled(line: bytes) -> bytes:
    return b"".join(line.replace(b"@", str(index).encode()) for index in range(5))


#: The seven SHA-256 digests the round-1 Codex verdict published.  A recipe that no longer
#: produces its published bytes is a broken oracle, not a passing test.
CODEX_DIGESTS = {
    "codex-r2-blocker-1-adjusted-rebound-to-raw-p": (
        "f8c58b1d8fef72e2926bb513b14251ea38f9a66259bdac06d04dc74200207e70"
    ),
    "codex-r2-blocker-2-reject-rebound-to-raw-decisions": (
        "d23bca1d3c769427090126f445aee5add7b68d944b3083083a71e98786a3527a"
    ),
    "codex-r2-blocker-3-permuted-reject-vector": (
        "9e146287981c3906b6d3877dbf3d40aac6a81fb7f232130f83323e100ac91a31"
    ),
    "codex-r2-blocker-3-permuted-adjusted-vector": (
        "749a74fc0d46f53806f788f49864d2028923a4ba8273ab8b5cd20d6afd3b2655"
    ),
    "codex-r2-blocker-5-threshold-alpha-times-two": (
        "31709e3ce99c107ce5b9be4da596558f10f1c5d841c32cf0581bd1d784a5fc82"
    ),
    "control-inline-verdict-fstring-enumerate": (
        "242a7f94b7756ebff630f4a57a99b24216ee80887ae07931de3866844dab4723"
    ),
    "control-inline-verdict-plain-print-enumerate": (
        "5cc2ff12712a83ae0e059d1a0886c22e8d5eef9005ffdaeb116555abc02b1372"
    ),
    # The verdict's own "conservative `adjusted_p < ALPHA / 2`" probe, rebuilt by shape and
    # found to be byte-identical to the digest it published.
    "control-conservative-half-alpha-threshold": (
        "22683c97dbf1689017fd11f5e45f0f6e642f001108189feb4b659684d7d5fa29"
    ),
}

#: The variants the verdict names but publishes no source for.  They are
#: rebuilt by shape, so their digests are this oracle's own and are pinned here rather than
#: against the verdict.
SHAPE_REPRODUCED = frozenset(
    {
        "control-inline-verdict-format-enumerate",
        "control-inline-verdict-unrolled-plain-print",
        "control-inline-verdict-unrolled-fstring",
        "control-verdict-name-assigned-before-printing",
        "control-reject-helper-receiving-the-zip-bound-scalar",
        "control-float-adjusted-transport",
        "control-swapped-verdict-text-polarity",
        "probe-three-corrected-two-raw-decisions",
    }
)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    """Every round-2 row, as `(reference case key, source bytes)`."""

    rows: dict[str, tuple[str, bytes]] = {
        # --- the sealed control -----------------------------------------------------------
        "sealed-e18-n1-unaltered": (E18_N1_KEY, E18_N1.read_bytes()),
        # --- the five audit blocker sources -----------------------------------------------
        "codex-r2-blocker-1-adjusted-rebound-to-raw-p": (
            E18_N1_KEY,
            _n1(after_call=b"    adjusted_p_values = raw_p_values\n"),
        ),
        "codex-r2-blocker-2-reject-rebound-to-raw-decisions": (
            E18_N1_KEY,
            _n1(
                after_call=b"    reject = [p < ALPHA for p in raw_p_values]\n",
                loop_head=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ),
        ),
        "codex-r2-blocker-3-permuted-reject-vector": (
            E18_N1_KEY,
            _n1(
                loop_head=(
                    b"    wrong_reject = [reject[1], reject[0], reject[2],"
                    b" reject[3], reject[4]]\n"
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, wrong_reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "codex-r2-blocker-3-permuted-adjusted-vector": (
            E18_N1_KEY,
            _n1(
                loop_head=(
                    b"    wrong_adjusted = [adjusted_p_values[1], adjusted_p_values[0],"
                    b" adjusted_p_values[2], adjusted_p_values[3], adjusted_p_values[4]]\n"
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, wrong_adjusted, reject):\n"
                    b'        verdict = "DIFFERENT" if adjusted_p < ALPHA'
                    b' else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "codex-r2-blocker-5-threshold-alpha-times-two": (
            E18_N1_KEY,
            _n1(
                verdict=b'        verdict = "DIFFERENT" if adjusted_p < ALPHA * 2'
                b' else "NO DIFFERENCE"\n'
            ),
        ),
        # --- the five inline-verdict variants round 1 regressed on ------------------------
        "control-inline-verdict-fstring-enumerate": (
            E18_N1_KEY,
            _n1(
                whole_loop=_inline_loop(
                    b"        print(f\"{result['label']}: "
                    b"{'DIFFERENT' if reject[i] else 'NO DIFFERENCE'}\")\n"
                )
            ),
        ),
        "control-inline-verdict-plain-print-enumerate": (
            E18_N1_KEY,
            _n1(
                whole_loop=_inline_loop(
                    b'        print(result["label"], "DIFFERENT" if reject[i]'
                    b' else "NO DIFFERENCE")\n'
                )
            ),
        ),
        "control-inline-verdict-format-enumerate": (
            E18_N1_KEY,
            _n1(
                whole_loop=_inline_loop(
                    b'        print("{}: {}".format(result["label"], "DIFFERENT" if reject[i]'
                    b' else "NO DIFFERENCE"))\n'
                )
            ),
        ),
        "control-inline-verdict-unrolled-plain-print": (
            E18_N1_KEY,
            _n1(
                whole_loop=_unrolled(
                    b'    print(results[@]["label"], "DIFFERENT" if reject[@]'
                    b' else "NO DIFFERENCE")\n'
                )
            ),
        ),
        "control-inline-verdict-unrolled-fstring": (
            E18_N1_KEY,
            _n1(
                whole_loop=_unrolled(
                    b"    print(f\"{results[@]['label']}: "
                    b"{'DIFFERENT' if reject[@] else 'NO DIFFERENCE'}\")\n"
                )
            ),
        ),
        # --- correct consumption forms from the verdict's probe table ---------------------
        "control-verdict-name-assigned-before-printing": (
            E18_N1_KEY,
            _n1(
                whole_loop=_inline_loop(
                    b"        verdict = f\"{'DIFFERENT' if reject[i]"
                    b" else 'NO DIFFERENCE'}\"\n"
                    b'        print(result["label"], verdict)\n'
                )
            ),
        ),
        "control-reject-helper-receiving-the-zip-bound-scalar": (
            E18_N1_KEY,
            _n1(
                verdict=b"        verdict = _label(rejected)\n",
                before_call=b"",
            ).replace(
                b"def main():\n",
                b'def _label(rejected):\n    return "DIFFERENT" if rejected'
                b' else "NO DIFFERENCE"\n\n\ndef main():\n',
            ),
        ),
        "control-float-adjusted-transport": (
            E18_N1_KEY,
            _n1(
                verdict=b'        verdict = "DIFFERENT" if float(adjusted_p) < ALPHA'
                b' else "NO DIFFERENCE"\n'
            ),
        ),
        "control-swapped-verdict-text-polarity": (
            E18_N1_KEY,
            _n1(
                verdict=b'        verdict = "NO DIFFERENCE" if adjusted_p >= ALPHA'
                b' else "DIFFERENT"\n'
            ),
        ),
        "control-conservative-half-alpha-threshold": (
            E18_N1_KEY,
            _n1(
                verdict=b'        verdict = "DIFFERENT" if adjusted_p < ALPHA / 2'
                b' else "NO DIFFERENCE"\n'
            ),
        ),
        "probe-three-corrected-two-raw-decisions": (
            E18_N1_KEY,
            _n1(
                verdict=b"        verdict = (\n"
                b'            "DIFFERENT"\n'
                b'            if (adjusted_p < ALPHA if result["column"] != "peak_tvoc_mg_m3"'
                b' and result["column"] != "eye_skin_irritation_score"'
                b' else result["raw_p"] < ALPHA)\n'
                b'            else "NO DIFFERENCE"\n'
                b"        )\n"
            ),
        ),
        # --- fresh adversarial rebinding and misplacement variants ------------------------
        "adversarial-reject-rebound-inside-a-branch": (
            E18_N1_KEY,
            _n1(
                after_call=b"    if len(raw_p_values) == 5:\n"
                b"        reject = [p < ALPHA for p in raw_p_values]\n",
                loop_head=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ),
        ),
        "adversarial-reject-rebound-in-a-helper-that-returns-it": (
            E18_N1_KEY,
            _n1(
                after_call=b"    reject = _raw_decisions(raw_p_values)\n",
                loop_head=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ).replace(
                b"def main():\n",
                b"def _raw_decisions(raw_p_values):\n"
                b"    return [p < ALPHA for p in raw_p_values]\n\n\ndef main():\n",
            ),
        ),
        "adversarial-permutation-via-sorted-zip": (
            E18_N1_KEY,
            _n1(
                loop_head=(
                    b"    ordered = [item[1] for item in sorted(zip(adjusted_p_values, reject))]\n"
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, ordered):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "adversarial-index-expression-rotated": (
            E18_N1_KEY,
            _n1(
                whole_loop=_inline_loop(
                    b'        print(result["label"], "DIFFERENT" if reject[(i + 1) % 5]'
                    b' else "NO DIFFERENCE")\n'
                )
            ),
        ),
        "adversarial-index-expression-i-plus-zero": (
            E18_N1_KEY,
            _n1(
                whole_loop=_inline_loop(
                    b'        print(result["label"], "DIFFERENT" if reject[i + 0]'
                    b' else "NO DIFFERENCE")\n'
                )
            ),
        ),
        "adversarial-by-name-dict-lookup-with-the-correct-key": (
            E18_N1_KEY,
            _n1(
                loop_head=(
                    b"    decisions = {}\n"
                    b"    for item, flag in zip(results, reject):\n"
                    b'        decisions[item["column"]] = flag\n'
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if decisions[result["column"]]'
                    b' else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "adversarial-by-name-dict-lookup-with-a-rotated-key": (
            E18_N1_KEY,
            _n1(
                loop_head=(
                    b"    decisions = {}\n"
                    b"    for item, flag in zip(results, reject):\n"
                    b'        decisions[item["column"]] = flag\n'
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if decisions[OTHER_COLUMN[result["column"]]]'
                    b' else "NO DIFFERENCE"\n'
                )
            ).replace(
                b"ALPHA = 0.05\n",
                b"ALPHA = 0.05\nOTHER_COLUMN = {\n"
                b'    "fev1_l": "feno_ppb",\n'
                b'    "feno_ppb": "fev1_l",\n'
                b'    "airway_symptom_score": "airway_symptom_score",\n'
                b'    "peak_tvoc_mg_m3": "peak_tvoc_mg_m3",\n'
                b'    "eye_skin_irritation_score": "eye_skin_irritation_score",\n'
                b"}\n",
            ),
        ),
        "adversarial-del-reject-then-a-new-reject": (
            E18_N1_KEY,
            _n1(
                after_call=b"    del reject\n    reject = [p < ALPHA for p in raw_p_values]\n",
                loop_head=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ),
        ),
        "adversarial-reject-reassigned-to-a-slice": (
            E18_N1_KEY,
            _n1(
                after_call=b"    reject = reject[:]\n",
                loop_head=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ),
        ),
        "adversarial-reject-reassigned-to-a-list-copy": (
            E18_N1_KEY,
            _n1(
                after_call=b"    reject = list(reject)\n",
                loop_head=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ),
        ),
        "adversarial-adjusted-rebound-to-numpy-asarray-of-itself": (
            E18_N1_KEY,
            _n1(
                imports=b"import numpy as np\n",
                after_call=b"    adjusted_p_values = np.asarray(adjusted_p_values)\n",
            ),
        ),
    }
    return rows


def source_digests() -> dict[str, str]:
    return {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_key, source) in fixture_sources().items()
    }


if __name__ == "__main__":
    for name, digest in source_digests().items():
        print(f"{name:56s} {digest}")
