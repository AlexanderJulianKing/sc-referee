from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVALUATION_SRC = ROOT / "evaluation" / "src"
sys.path[:0] = [str(SRC), str(EVALUATION_SRC)]

from sc_referee_evaluation.prospective_study_scaffold import (  # noqa: E402
    ProspectiveStudyScaffoldError,
    build_prospective_study_scaffold,
    load_json_object,
    write_study_scaffold_once,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a role-separated 10 x 2 x 7 prospective qualification assignment scaffold."
        )
    )
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--authoring-template", required=True, type=Path)
    parser.add_argument("--setup", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        files = build_prospective_study_scaffold(
            load_json_object(arguments.template),
            load_json_object(arguments.authoring_template),
            load_json_object(arguments.setup),
        )
        output = write_study_scaffold_once(arguments.output_root, files)
    except (OSError, ValueError, ProspectiveStudyScaffoldError) as error:
        print(f"build-prospective-study-scaffold: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
