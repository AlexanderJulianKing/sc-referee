import json, sys, io, csv, re
from collections import Counter
from pathlib import Path
from decimal import Decimal, InvalidOperation

REPO = Path("/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext")
CASES = REPO/"evaluation/development/blind-envelope-10-2026-08-24/cases"
sys.path.insert(0, str(REPO/"src"))
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 import (
    analyze_code_csv_multiple_testing_dataflow as run,
)

def parse_csv(content, group_column, outcome_columns):
    text = content.decode("utf-8")
    rows = list(csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True))
    header = tuple(rows[0])
    gi = header.index(group_column)
    counts = Counter(r[gi] for r in rows[1:])
    gv = tuple(sorted(counts, key=lambda v: v.encode("utf-8")))
    assert len(gv) == 2, counts
    return header, (gv[0], gv[1])

def case_inputs(case_id, source=None):
    d = CASES/case_id
    prof = json.loads((d/"profile_1_2_0.json").read_text())
    auth = prof["semantic_role_authority"]["authorized_test_family"]
    path = auth["material_input_path"]
    gcol = auth["group_contrast_column"]
    outs = tuple(auth["outcome_columns"])
    csv_content = (d/"project"/path).read_bytes()
    header, gvals = parse_csv(csv_content, gcol, outs)
    content = (source or (d/"project/analysis.py")).read_bytes()
    return dict(content=content, authorized_path=path, group_column=gcol,
                outcome_columns=outs, csv_header=header, group_values=gvals,
                csv_content=csv_content)

def analyze(case_id, source=None):
    kw = case_inputs(case_id, source)
    content = kw.pop("content")
    return run(content, **kw)

ROLES = json.loads((CASES.parent/"ROLE_MAP.json").read_text())["case_roles_in_fixed_order"]
if __name__ == "__main__":
    for item in ROLES:
        r = analyze(item["case_id"])
        print(f"{item['role']:3} {item['case_id']} -> reason={r.reason} facts={'yes' if r.facts else 'no'}")
