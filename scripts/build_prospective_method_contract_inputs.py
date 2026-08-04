from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EVALUATION_SRC = ROOT / "evaluation" / "src"
sys.path[:0] = [str(SRC), str(EVALUATION_SRC)]

from sc_referee_evaluation.prospective_method_contract_inputs import (  # noqa: E402
    ProspectiveMethodContractInputError,
    build_prospective_method_contract_inputs,
    load_authoring_briefs,
    load_json_object,
    write_prospective_method_contract_inputs_once,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build create-once, coordinator-only prospective method-contract input shells."
        )
    )
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--relation-binding-map", required=True, type=Path)
    parser.add_argument("--authoring-briefs-root", required=True, type=Path)
    parser.add_argument("--block-id", required=True)
    parser.add_argument("--scientist-id", required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--allow-heldout",
        action="store_true",
        help=(
            "Permit coordinator-only held-out shell preparation. This does not authorize release "
            "to authors or opening labels."
        ),
    )
    arguments = parser.parse_args()
    try:
        files = build_prospective_method_contract_inputs(
            load_json_object(arguments.protocol),
            load_json_object(arguments.relation_binding_map),
            load_authoring_briefs(arguments.authoring_briefs_root),
            block_id=arguments.block_id,
            scientist_id=arguments.scientist_id,
            allow_heldout=arguments.allow_heldout,
        )
        output = write_prospective_method_contract_inputs_once(arguments.output_root, files)
    except (OSError, ValueError, ProspectiveMethodContractInputError) as error:
        print(f"build-prospective-method-contract-inputs: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
