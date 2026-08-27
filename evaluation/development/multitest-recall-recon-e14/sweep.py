"""Execute the E14 proposal against frozen corpus, opened negatives, and FA fixtures."""

from __future__ import annotations

import json
from typing import Any

from fa_e14 import d14_fixtures, historical_fixtures
from h import (
    CORPUS,
    ENVELOPE_ROOTS,
    analyze_corpus,
    analyze_envelope,
    audit_rows,
    classify,
)
from prototypes import PROTOTYPES


def execute() -> dict[str, Any]:
    labels = json.loads((CORPUS / "specs/labels.json").read_text(encoding="utf-8"))
    correct_specs = sorted(spec for spec, value in labels.items() if value["label"] == "correct")
    all_specs = sorted(labels)
    negative_rows = [
        (envelope, row)
        for envelope, root in ENVELOPE_ROOTS.items()
        for row in audit_rows(root)
        if row["designed_class"] == "negative"
    ]
    if len(correct_specs) != 25 or len(negative_rows) != 45:
        raise ValueError("none-flip census changed")
    historic_fa = historical_fixtures()
    new_fa = d14_fixtures()
    if len(historic_fa) != 22 or len(new_fa) != 6:
        raise ValueError("FA-fixture census changed")

    output: dict[str, Any] = {
        "method": (
            "real frozen 2.3 analyzer invoked through adapter-equivalent authority/CSV inputs; "
            "sealed ladders are separately executed through the real adapter"
        ),
        "fixture_census": {"historical": len(historic_fa), "d14": len(new_fa)},
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
            for envelope, root in ENVELOPE_ROOTS.items()
            for row in audit_rows(root)
        }
        historic_values = {
            label: classify(analyze_envelope(case, source.encode(), fn=analyzer))
            for label, case, source in historic_fa
        }
        new_values = {
            label: classify(analyze_envelope(case, source.encode(), fn=analyzer))
            for label, case, source in new_fa
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
            "historical_fa": {
                "executed": len(historic_fa),
                "candidates": sum(value[0] == "candidate" for value in historic_values.values()),
                "outcomes": {key: list(value) for key, value in historic_values.items()},
            },
            "d14_fa": {
                "executed": len(new_fa),
                "candidates": sum(value[0] == "candidate" for value in new_values.values()),
                "outcomes": {key: list(value) for key, value in new_values.items()},
            },
        }

    baseline_opened = opened_results["baseline-2.3"]
    baseline_corpus = corpus_results["baseline-2.3"]
    for variant in PROTOTYPES:
        if variant == "baseline-2.3":
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
        ("P2", "4fc0f5c1ef2d0e2cd5b6"),
        ("P3", "502687d9137dab93ff99"),
        ("P4", "cccde3c60f936e077f80"),
        ("P5", "5e33841b96d85ffe67be"),
        ("P6", "94786af7eca95fff6d78"),
    ):
        key = f"E14:{role}:{case_id}"
        output["miss_projection"][role] = {
            variant: list(opened_results[variant][key]) for variant in PROTOTYPES
        }
    return output


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
