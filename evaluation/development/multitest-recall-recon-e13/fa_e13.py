"""Targeted correct-analysis attacks for the two E13 prototype admissions."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

from h import E13, analyze_envelope, classify
from prototypes import combined_analyzer


def _e12_fa3() -> tuple[Path, str]:
    root = Path("evaluation/development/multitest-code-slice-v2_2/e12-ladders")
    sys.path.insert(0, str(root.resolve()))
    values = runpy.run_path(str(root / "fa.py"))
    return values["P6"], values["FA3"]


def _verdict_helper(source: str, *, corrected: bool) -> str:
    source = source.replace(
        "\ndef main():",
        "\ndef verdict(p):\n"
        "    return 'significant' if p < ALPHA else 'not significant'\n\n\n"
        "def main():",
    )
    if not corrected:
        source = source.replace("ALPHA = 0.05", "ALPHA = 0.01")
        source = source.replace(
            "p_used = min(1.0, float(result.pvalue) * n_comparisons)",
            "p_used = float(result.pvalue)",
        )
    return source.replace(
        'verdict = "significant" if p_used < ALPHA else "not significant"\n'
        '        print(f"{label}: corrected p = {p_used:.4f} -> {verdict}")',
        "decision = verdict(p_used)\n"
        '        print("%s: p = %.4f -> %s" % (label, p_used, decision))',
    )


def execute() -> dict[str, object]:
    case, base = _e12_fa3()
    fixtures = {
        "correct-terminal-clone-whole-family-bonferroni": (
            case,
            _verdict_helper(base, corrected=True),
        ),
        "correct-terminal-clone-preregistered-001-N5": (
            case,
            _verdict_helper(base, corrected=False),
        ),
    }
    results = {
        name: list(classify(analyze_envelope(case_dir, source.encode(), fn=combined_analyzer)))
        for name, (case_dir, source) in fixtures.items()
    }
    for role, case_id in (
        ("N1", "b7d38f6e9284abfd3ee6"),
        ("N9", "ab70cdb37bb2977d725c"),
    ):
        case_dir = E13 / case_id
        results[f"correct-reader-local-path-{role}"] = list(
            classify(analyze_envelope(case_dir, fn=combined_analyzer))
        )
    return {"adapter_version": "2.2.0", "prototype": "D-combined", "results": results}


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
