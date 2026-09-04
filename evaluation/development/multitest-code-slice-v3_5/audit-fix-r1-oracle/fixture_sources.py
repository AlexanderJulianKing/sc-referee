"""Deterministic source recipes for the MT 3.5 audit-fix round-1 oracle.

Every recipe is an anchored edit of one sealed envelope case source, exactly as the MT 3.4
fix-round oracles are.  The recipes own source selection and mutation only; the expected rows
live in `EXPECTED_ROWS.json` and are authored from the design and from each row's own frozen
3.4 sibling, never from analyzer output.

Three groups of sources are carried.

* The four audit reproducers, reconstructed from the recipes in the Codex 3.5 verdict.  Each
  one's SHA-256 is asserted against the digest the verdict published, so a recipe that drifts
  fails here rather than quietly testing a different program.
* The three custodian false-clearance probes, whose control is the sealed E18 N1 source
  itself and whose two mutants move the verdict on to the raw p-value.
* Fresh adversarial variants of the same sealed E18 N1 source, one per way a correction output
  can or cannot reach a verdict, plus the sealed movement rows carried unaltered.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
E15 = REPO / "evaluation/development/blind-envelope-15-2026-08-29/cases"
E17 = REPO / "evaluation/development/blind-envelope-17-2026-08-30/cases"
E18 = REPO / "evaluation/development/blind-envelope-18-2026-09-01/cases"

E15_N1_KEY = "E15:N1:f846b07b1d11131cec4d"
E15_P3_KEY = "E15:P3:afe47b2a7ea87ed21a69"
E17_N1_KEY = "E17:N1:e2d8b1bdf4baa671a1b4"
E18_N1_KEY = "E18:N1:5c091f9052becdb5c3ea"
E18_P2_KEY = "E18:P2:5a9277448db34379ce78"
E18_P3_KEY = "E18:P3:d1b1fc47ccdabd0c2f22"

E15_N1 = E15 / "f846b07b1d11131cec4d/project/analysis.py"
E15_P3 = E15 / "afe47b2a7ea87ed21a69/project/analysis.py"
E17_N1 = E17 / "e2d8b1bdf4baa671a1b4/project/analysis.py"
E18_N1 = E18 / "5c091f9052becdb5c3ea/project/analysis.py"
E18_P2 = E18 / "5a9277448db34379ce78/project/analysis.py"
E18_P3 = E18 / "d1b1fc47ccdabd0c2f22/project/analysis.py"

# --- anchors -----------------------------------------------------------------------------
#
# The sealed E18 N1 correction statement and the presentation loop that reads its outputs.
# Every E18 N1 recipe below replaces one or both, and nothing else.
N1_CALL = b"    reject, adjusted_p_values, _, _ = multipletests(raw_p_values)\n"
N1_LOOP = b"""    for result, adjusted_p, rejected in zip(results, adjusted_p_values, reject):
        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"
"""
# The raw-p presentation loop the custodian's two probes and the first Codex reproducer use.
N1_PLAIN_LOOP = b"""    for result, adjusted_p, rejected in zip(results, raw_p_values, raw_p_values):
        verdict = "DIFFERENT" if result["raw_p"] < ALPHA else "NO DIFFERENCE"
"""
N1_FORMAT_LOOP = b"""    for result, adjusted_p, rejected in zip(results, raw_p_values, raw_p_values):
        verdict = (
            "DIFFERENT at {}".format(ALPHA)
            if result["raw_p"] < ALPHA
            else "NO DIFFERENCE at {}".format(ALPHA)
        )
"""
N1_IMPORT = b"from statsmodels.stats.multitest import multipletests\n"

# The Codex reproducers 2 and 4 add an import and one dead correction call immediately after
# the `results` comprehension closes.
SCIPY_IMPORT = b"from scipy import stats\n"
SCIPY_IMPORT_WITH_MULTITEST = (
    b"from scipy import stats\nfrom statsmodels.stats.multitest import multipletests\n"
)
DEAD_CALL = (
    b'    reject, adjusted, _, _ = multipletests([item["p_value"] for item in results],'
    b" alpha=ALPHA)\n"
)
COMPREHENSION_CLOSE = b"\n    ]\n"


def _once(data: bytes, needle: bytes) -> None:
    if data.count(needle) != 1:
        raise ValueError(f"anchor is not unique: {needle!r}")


def _replace(data: bytes, old: bytes, new: bytes) -> bytes:
    _once(data, old)
    return data.replace(old, new)


def _dead_library_call(source: bytes) -> bytes:
    """Codex reproducers 2 and 4: import the routine and call it over the whole family."""

    data = _replace(source, SCIPY_IMPORT, SCIPY_IMPORT_WITH_MULTITEST)
    return _replace(data, COMPREHENSION_CLOSE, COMPREHENSION_CLOSE + DEAD_CALL)


def _n1(loop: bytes | None = None, call: bytes | None = None, after_call: bytes = b"") -> bytes:
    data = E18_N1.read_bytes()
    if call is not None:
        data = _replace(data, N1_CALL, call)
    elif after_call:
        data = _replace(data, N1_CALL, N1_CALL + after_call)
    if loop is not None:
        data = _replace(data, N1_LOOP, loop)
    return data


#: The four SHA-256 digests the Codex 3.5 verdict published for its reproducers.  A recipe
#: that no longer produces its published bytes is a broken oracle, not a passing test.
CODEX_DIGESTS = {
    "codex-blocker-1-e18n1-format-arms-on-raw-p": (
        "24787652107eb660fae9e5b1dae2c2ced8cd2162aac8cac418d0b28ed7a9f0b1"
    ),
    "codex-blocker-2-e18p3-dead-library-call": (
        "abed51d5ac05a95f43b814b7ff845dddccad89ea66d85d12eee35c1734eee717"
    ),
    "codex-blocker-3-e18p3-dead-call-string-group-tokens": (
        "67e3a64f7f5afd2edd62616d71038e692fd057654515b40693bbbdb570cafbe6"
    ),
    "codex-blocker-4-e15p3-dead-library-call": (
        "c48b659f5b0b91412134c204050808b47aa60009c4dfd96d73cf87677dd6c0da"
    ),
}


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    """Every round-1 row, as `(reference case key, source bytes)`."""

    blocker_2 = _dead_library_call(E18_P3.read_bytes())
    blocker_3 = _replace(
        blocker_2,
        b"LOW_SALT = 2.0\nHIGH_SALT = 3.0\n",
        b'LOW_SALT = "2.0"\nHIGH_SALT = "3.0"\n',
    )
    rows: dict[str, tuple[str, bytes]] = {
        # --- the four audit reproducers ---------------------------------------------------
        "codex-blocker-1-e18n1-format-arms-on-raw-p": (E18_N1_KEY, _n1(loop=N1_FORMAT_LOOP)),
        "codex-blocker-2-e18p3-dead-library-call": (E18_P3_KEY, blocker_2),
        "codex-blocker-3-e18p3-dead-call-string-group-tokens": (E18_P3_KEY, blocker_3),
        "codex-blocker-4-e15p3-dead-library-call": (
            E15_P3_KEY,
            _dead_library_call(E15_P3.read_bytes()),
        ),
        # --- the three custodian false-clearance probes -----------------------------------
        "custodian-n1-control": (E18_N1_KEY, E18_N1.read_bytes()),
        "custodian-n1-raw-plain-arms": (E18_N1_KEY, _n1(loop=N1_PLAIN_LOOP)),
        # `custodian-n1-raw-format-arms` is byte-identical to Codex reproducer 1 and is
        # carried once, under the reproducer's name.
        # --- the reason authority ---------------------------------------------------------
        # The identical raw-p program with the correction statement and its import deleted.
        # Whatever the two raw-arm probes are, they must be this, because the only difference
        # between them is a statement whose results nothing reads.
        "authority-n1-raw-plain-arms-without-the-correction": (
            E18_N1_KEY,
            _n1(loop=N1_PLAIN_LOOP, call=b"").replace(N1_IMPORT, b""),
        ),
        # --- consumption forms that must keep their clearance -----------------------------
        "control-verdict-from-the-zip-bound-reject-element": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "control-second-call-consumed-first-call-dead": (
            E18_N1_KEY,
            _n1(
                call=(
                    N1_CALL + b"    reject2, adjusted2, _, _ = multipletests"
                    b'(raw_p_values, method="bonferroni")\n'
                ),
                loop=(
                    b"    for result, adjusted_p, rejected in zip(results, adjusted2, reject2):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                ),
            ),
        ),
        # --- consumption forms that must not clear ----------------------------------------
        "adversarial-reject-printed-verdict-from-raw-p": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if result["raw_p"] < ALPHA'
                    b' else "NO DIFFERENCE"\n'
                ),
                after_call=b'    print("rejections: %s" % list(reject))\n',
            ),
        ),
        "adversarial-outputs-loaded-only-into-a-display": (
            E18_N1_KEY,
            _n1(
                loop=N1_PLAIN_LOOP,
                after_call=(
                    b'    print("adjusted: %s" % list(adjusted_p_values))\n'
                    b'    print("rejections: %s" % list(reject))\n'
                ),
            ),
        ),
        "adversarial-adjusted-compared-at-the-wrong-index": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, reject):\n"
                    b'        verdict = "DIFFERENT" if adjusted_p_values[0] < ALPHA'
                    b' else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "adversarial-reject-through-a-helper-that-returns-it": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    for result, adjusted_p, rejected in zip"
                    b"(results, adjusted_p_values, decisions(reject)):\n"
                    b'        verdict = "DIFFERENT" if rejected else "NO DIFFERENCE"\n'
                )
            ).replace(
                b"\n\ndef main():\n",
                b'\n\ndef decisions(flags):\n    """Return the rejection decisions unchanged."""\n'
                b"    return flags\n\n\ndef main():\n",
            ),
        ),
        "adversarial-outputs-consumed-in-a-displayed-comprehension": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b'    verdicts = ["DIFFERENT" if item else "NO DIFFERENCE" for item in reject]\n'
                    b"    for result, adjusted_p, verdict in zip"
                    b"(results, adjusted_p_values, verdicts):\n"
                )
            ),
        ),
        "adversarial-outputs-through-a-dataframe-column": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    frame = pd.DataFrame(results)\n"
                    b'    frame["adjusted"] = adjusted_p_values\n'
                    b'    for result, adjusted_p in zip(results, list(frame["adjusted"])):\n'
                    b'        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "adversarial-adjusted-indexed-by-name-not-position": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    for column, adjusted_p in zip"
                    b"([item[0] for item in DECLARED_OUTCOMES], adjusted_p_values):\n"
                    b'        result = {"label": column, "column": column, "n_a": 0, "n_b": 0,\n'
                    b'                  "mean_a": 0.0, "sd_a": 0.0, "mean_b": 0.0, "sd_b": 0.0,'
                    b' "raw_p": 0.0}\n'
                    b'        verdict = "DIFFERENT" if adjusted_p < ALPHA else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "adversarial-reject-indexed-by-an-enumerate-target": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    for index, (result, adjusted_p) in enumerate"
                    b"(zip(results, adjusted_p_values)):\n"
                    b'        verdict = "DIFFERENT" if reject[index] else "NO DIFFERENCE"\n'
                )
            ),
        ),
        "adversarial-reject-consumed-at-three-of-five-positions": (
            E18_N1_KEY,
            _n1(
                loop=(
                    b"    verdicts = [\n"
                    b'        "DIFFERENT" if reject[0] else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if reject[1] else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if reject[2] else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if raw_p_values[3] < ALPHA else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if raw_p_values[4] < ALPHA else "NO DIFFERENCE",\n'
                    b"    ]\n"
                    b"    for result, adjusted_p, verdict in zip"
                    b"(results, adjusted_p_values, verdicts):\n"
                )
            ),
        ),
        "adversarial-correction-over-three-of-five-inputs": (
            E18_N1_KEY,
            _n1(
                call=(
                    b"    reject, adjusted_p_values, _, _ = multipletests(\n"
                    b"        [raw_p_values[0], raw_p_values[1], raw_p_values[2]]\n"
                    b"    )\n"
                ),
                loop=(
                    b"    verdicts = [\n"
                    b'        "DIFFERENT" if reject[0] else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if reject[1] else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if reject[2] else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if results[3]["raw_p"] < ALPHA else "NO DIFFERENCE",\n'
                    b'        "DIFFERENT" if results[4]["raw_p"] < ALPHA else "NO DIFFERENCE",\n'
                    b"    ]\n"
                    b"    for result, adjusted_p, verdict in zip"
                    b"(results, raw_p_values, verdicts):\n"
                ),
            ),
        ),
        # --- the sealed movement rows, carried unaltered ----------------------------------
        "sealed-e15-n1-unaltered": (E15_N1_KEY, E15_N1.read_bytes()),
        "sealed-e15-p3-unaltered": (E15_P3_KEY, E15_P3.read_bytes()),
        "sealed-e17-n1-unaltered": (E17_N1_KEY, E17_N1.read_bytes()),
        "sealed-e18-p2-unaltered": (E18_P2_KEY, E18_P2.read_bytes()),
        "sealed-e18-p3-unaltered": (E18_P3_KEY, E18_P3.read_bytes()),
    }
    for name, digest in CODEX_DIGESTS.items():
        if name == "codex-blocker-3-e18p3-dead-call-string-group-tokens":
            continue
        measured = hashlib.sha256(rows[name][1]).hexdigest()
        if measured != digest:
            raise ValueError(f"{name} no longer reproduces the verdict's published bytes")
    measured = hashlib.sha256(
        rows["codex-blocker-3-e18p3-dead-call-string-group-tokens"][1]
    ).hexdigest()
    if measured != CODEX_DIGESTS["codex-blocker-3-e18p3-dead-call-string-group-tokens"]:
        raise ValueError("codex reproducer 3 no longer reproduces the verdict's published bytes")
    return rows
