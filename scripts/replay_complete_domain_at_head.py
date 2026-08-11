"""Emit the non-blind current-byte replay required before an env-10 drift ruling."""

from __future__ import annotations

import argparse
from pathlib import Path

from sc_referee_evaluation.complete_domain_replay_at_head import (
    REPLAY_ARTIFACT_NAME,
    REPLAY_OUTPUT_RELATIVE,
    write_complete_domain_replay_at_head,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    output_root = (
        arguments.output_root.resolve()
        if arguments.output_root is not None
        else project_root / REPLAY_OUTPUT_RELATIVE
    )
    record = write_complete_domain_replay_at_head(project_root, output_root)
    print(f"artifact: {output_root / REPLAY_ARTIFACT_NAME}")
    print(f"semantic_digest: {record['semantic_digest']}")
    print(f"agreement: {record['agreement_count']}/{record['case_count']}")
    return 0 if record["all_cases_agree"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
