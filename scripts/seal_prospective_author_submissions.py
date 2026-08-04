from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVALUATION_SRC = ROOT / "evaluation" / "src"
sys.path[:0] = [str(SRC), str(EVALUATION_SRC)]

from sc_referee_evaluation.prospective_submission_ingestion import (  # noqa: E402
    ProspectiveSubmissionIngestionError,
    build_prospective_submission_seal,
    load_canonical_json_object,
    write_prospective_submission_seal_once,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and create-once seal one complete prospective author submission queue "
            "without executing or scientifically reviewing submitted code."
        )
    )
    parser.add_argument("--author-queue", required=True, type=Path)
    parser.add_argument("--expected-queue-digest", required=True)
    parser.add_argument("--submission-root", required=True, type=Path)
    parser.add_argument("--author-execution-context-id", required=True)
    parser.add_argument("--sealed-at", required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        queue = load_canonical_json_object(arguments.author_queue, label="author queue")
        files = build_prospective_submission_seal(
            queue,
            arguments.submission_root,
            expected_queue_digest=arguments.expected_queue_digest,
            author_execution_context_id=arguments.author_execution_context_id,
            sealed_at=arguments.sealed_at,
        )
        output = write_prospective_submission_seal_once(arguments.output_root, files)
    except (OSError, ValueError, ProspectiveSubmissionIngestionError) as error:
        print(f"seal-prospective-author-submissions: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
