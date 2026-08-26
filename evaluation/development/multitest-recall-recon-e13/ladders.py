"""Executed one-construct ladders from the three sealed E13 misses."""

from __future__ import annotations

import hashlib
import json

from h import E13, adapter_envelope


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"ladder replacement expected exactly once: {old[:60]!r}")
    return source.replace(old, new)


def p2_rungs() -> list[tuple[str, str, str]]:
    case = E13 / "c336be2521785ab6a954"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    start_marker = '    print()\n    print("=" * 78)\n    print("Summary table")'
    end_marker = '\n\nif __name__ == "__main__":'
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    deduplicated = source[:start] + source[end:]
    direct_path = _replace_once(
        deduplicated,
        "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)\n"
        "    return pd.read_csv(path)",
        "    return pd.read_csv(\n"
        "        os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)\n"
        "    )",
    )
    return [
        ("P2-r0-real", "sealed source", source),
        ("P2-r1-one-family-pass", "delete only the duplicate summary family pass", deduplicated),
        ("P2-r2-direct-reader-path", "inline only the static local path alias", direct_path),
    ]


def p5_rungs() -> list[tuple[str, str, str]]:
    case = E13 / "80091f37c722eba28e18"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    direct_path = _replace_once(
        source,
        "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)\n"
        "    frame = pd.read_csv(path)",
        "    frame = pd.read_csv(\n"
        "        os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)\n"
        "    )",
    )
    verdict_block = """    if adjusted_p is None:
        print("  verdict at alpha=%.2f  : %s (unadjusted p)" % (ALPHA, verdict(result["p_value"])))
    else:
        print("  p-value (%s-adjusted, primary pair): %.4f" % (ADJUST_METHOD, adjusted_p))
        print("  verdict at alpha=%.2f  : %s (adjusted p)" % (ALPHA, verdict(adjusted_p)))"""
    direct_rendering = """    if adjusted_p is None:
        if result["p_value"] < ALPHA:
            print("SIGNIFICANT")
        else:
            print("not significant")
    else:
        print("  p-value (%s-adjusted, primary pair): %.4f" % (ADJUST_METHOD, adjusted_p))
        if adjusted_p < ALPHA:
            print("SIGNIFICANT")
        else:
            print("not significant")"""
    direct_verdict = _replace_once(direct_path, verdict_block, direct_rendering)
    return [
        ("P5-r0-real", "sealed source", source),
        ("P5-r1-direct-reader-path", "inline only the static local path alias", direct_path),
        (
            "P5-r2-direct-verdict-rendering",
            "replace only the pure two-string verdict-helper transport with admitted direct If sinks",
            direct_verdict,
        ),
    ]


def p6_rungs() -> list[tuple[str, str, str]]:
    case = E13 / "d0f9fcd52f47e4d64668"
    source = (case / "project" / "analysis.py").read_text(encoding="utf-8")
    direct_path = _replace_once(
        source,
        "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)\n"
        "    return pd.read_csv(path)",
        "    return pd.read_csv(\n"
        "        os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)\n"
        "    )",
    )
    list_display = """CORRECTED_OUTCOMES = [
    "symptom_severity_score_0_500",
    "worst_abdominal_pain_0_10",
    "bloating_days_per_week",
]"""
    set_display = """CORRECTED_OUTCOMES = {
    "symptom_severity_score_0_500",
    "worst_abdominal_pain_0_10",
    "bloating_days_per_week",
}"""
    as_set = _replace_once(direct_path, list_display, set_display)
    no_iteration = _replace_once(
        as_set,
        '"Correction: p-values for {} are multiplied by {} "\n'
        '        "and capped at 1.".format(", ".join(CORRECTED_OUTCOMES), N_CORRECTED)',
        '"Correction: three selected p-values are multiplied by {} "\n'
        '        "and capped at 1.".format(N_CORRECTED)',
    )
    literal_subset_size = _replace_once(
        no_iteration, "N_CORRECTED = len(CORRECTED_OUTCOMES)", "N_CORRECTED = 3"
    )
    full_factor = _replace_once(literal_subset_size, "N_CORRECTED = 3", "N_CORRECTED = 5")
    return [
        ("P6-r0-real", "sealed source", source),
        ("P6-r1-direct-reader-path", "inline only the static local path alias", direct_path),
        ("P6-r2-set-membership", "change only the corrected-membership List to Set", as_set),
        (
            "P6-r3-membership-only-set",
            "remove only the set's presentation-order iteration",
            no_iteration,
        ),
        (
            "P6-r4-literal-subset-size",
            "replace only len(CORRECTED_OUTCOMES) with its literal subset size 3",
            literal_subset_size,
        ),
        (
            "P6-r5-full-family-factor-control",
            "replace only multiplier 3 with the recognized full-family factor 5",
            full_factor,
        ),
    ]


def execute() -> dict[str, object]:
    result: dict[str, object] = {"adapter_version": "2.2.0", "ladders": {}}
    for role, case_id, factory in (
        ("P2", "c336be2521785ab6a954", p2_rungs),
        ("P5", "80091f37c722eba28e18", p5_rungs),
        ("P6", "d0f9fcd52f47e4d64668", p6_rungs),
    ):
        rows = []
        for rung, mutation, source in factory():
            observed = adapter_envelope(E13 / case_id, source.encode("utf-8"))
            rows.append(
                {
                    "rung": rung,
                    "mutation": mutation,
                    "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                    **observed,
                }
            )
        result["ladders"][role] = rows  # type: ignore[index]
    return result


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
