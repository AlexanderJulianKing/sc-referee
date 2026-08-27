"""Execute the untouched-tree 2.3 test census over all fifteen E14 cases."""

from __future__ import annotations

import json
from typing import Any

from h import E14, audit_rows, envelope_inputs

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_3 as mt


def execute() -> dict[str, Any]:
    output: dict[str, Any] = {"adapter_version": "2.3.0", "cases": []}
    for row in audit_rows(E14):
        case = E14 / row["case_id"]
        inputs = envelope_inputs(case)
        content = inputs["content"]
        outcomes = tuple(inputs["outcome_columns"])
        tree = mt._bounded_parse(content)
        scope = tuple(item for item in tree.body if not mt._is_docstring(item))
        resolver, resolver_reason = mt._resolver(scope)
        if resolver is None:
            census = None
            reason = resolver_reason
        else:
            census, reason = mt._mt_call_census(tree, resolver=resolver, outcome_columns=outcomes)
        output["cases"].append(
            {
                "role": row["role"],
                "case_id": row["case_id"],
                "authorized_count": len(outcomes),
                "resolved_call_count": None if census is None else len(census),
                "census_reason": reason,
                "adapter_outcome": row["dev_outcome"],
                "adapter_reason_or_classification": row["dev_reason_or_classification"],
            }
        )
    return output


if __name__ == "__main__":
    print(json.dumps(execute(), indent=2, sort_keys=True))
