"""Execute E13 prototype none-flip and movement sweeps against frozen bytes."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

from h import CORPUS, E10, E11, E12, E13, analyze_corpus, analyze_envelope, classify
from prototypes import PROTOTYPES

ENVELOPES = {
    "E10": E10,
    "E11": E11,
    "E12": E12,
    "E13": E13,
}


def _audit_rows(cases_root: Path) -> list[dict[str, Any]]:
    payload = json.loads((cases_root.parent / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    return list(payload["cases"])


def _fa_fixtures() -> list[tuple[str, Path, str]]:
    root = Path("evaluation/development/multitest-code-slice-v2_2/e12-ladders")
    sys.path.insert(0, str(root.resolve()))
    payload = runpy.run_path(str(root / "fa.py"))
    return list(payload["FIXTURES"])


def execute() -> dict[str, Any]:
    labels = json.loads((CORPUS / "specs" / "labels.json").read_text(encoding="utf-8"))
    correct_specs = sorted(spec for spec, value in labels.items() if value["label"] == "correct")
    all_specs = sorted(labels)
    negative_rows = [
        (envelope, row)
        for envelope, root in ENVELOPES.items()
        for row in _audit_rows(root)
        if row["designed_class"] == "negative"
    ]
    if len(correct_specs) != 25 or len(negative_rows) != 36:
        raise ValueError("none-flip census changed")
    fixtures = _fa_fixtures()
    if len(fixtures) != 6:
        raise ValueError("FA-fixture census changed")

    output: dict[str, Any] = {
        "method": (
            "real frozen 2.2 analyzer invoked through adapter-equivalent authority/CSV inputs; "
            "the adapter can only add an earlier source-envelope abstention"
        ),
        "none_flip": {},
        "opened_movements": {},
        "corpus_movements": {},
        "miss_projection": {},
    }
    opened_results: dict[str, dict[str, tuple[str, str]]] = {}
    corpus_results: dict[str, dict[str, tuple[str, str]]] = {}

    for variant, analyzer in PROTOTYPES.items():
        corpus_values = {spec: classify(analyze_corpus(spec, fn=analyzer)) for spec in all_specs}
        opened_values = {
            f"{envelope}:{row['role']}:{row['case_id']}": classify(
                analyze_envelope(root / row["case_id"], fn=analyzer)
            )
            for envelope, root in ENVELOPES.items()
            for row in _audit_rows(root)
        }
        fa_values = {
            label: classify(analyze_envelope(case, source.encode("utf-8"), fn=analyzer))
            for label, case, source in fixtures
        }
        opened_results[variant] = opened_values
        corpus_results[variant] = corpus_values
        output["none_flip"][variant] = {
            "corpus_correct": {
                "executed": len(correct_specs),
                "candidates": sum(corpus_values[spec][0] == "candidate" for spec in correct_specs),
            },
            "opened_negatives": {
                "executed": len(negative_rows),
                "candidates": sum(
                    opened_values[f"{envelope}:{row['role']}:{row['case_id']}"][0] == "candidate"
                    for envelope, row in negative_rows
                ),
            },
            "fa_fixtures": {
                "executed": len(fixtures),
                "candidates": sum(value[0] == "candidate" for value in fa_values.values()),
                "outcomes": {key: list(value) for key, value in fa_values.items()},
            },
        }

    baseline_opened = opened_results["baseline-2.2"]
    baseline_corpus = corpus_results["baseline-2.2"]
    for variant in PROTOTYPES:
        if variant == "baseline-2.2":
            continue
        output["opened_movements"][variant] = {
            key: [list(baseline_opened[key]), list(value)]
            for key, value in opened_results[variant].items()
            if value != baseline_opened[key]
        }
        output["corpus_movements"][variant] = {
            key: [list(baseline_corpus[key]), list(value)]
            for key, value in corpus_results[variant].items()
            if value != baseline_corpus[key]
        }

    for role, case_id in (
        ("P2", "c336be2521785ab6a954"),
        ("P5", "80091f37c722eba28e18"),
        ("P6", "d0f9fcd52f47e4d64668"),
    ):
        key = f"E13:{role}:{case_id}"
        output["miss_projection"][role] = {
            variant: list(opened_results[variant][key]) for variant in PROTOTYPES
        }
    return output


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
