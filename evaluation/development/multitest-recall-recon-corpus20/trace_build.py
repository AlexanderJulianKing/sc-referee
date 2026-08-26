"""Build a traced copy of the v2 dataflow module that reports the emitting source line."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(
    "/Users/alexanderking/.cache/recon-scratch/vnext/src/sc_referee/scientific_checks/"
    "code_csv_multiple_testing_dataflow_v2.py"
)
OUT = Path("/Users/alexanderking/.cache/recon-scratch/work/traced_dataflow_v2.py")

HEADER = '''
import os as _os


def _REASON_TRACE(reason, line):
    if _os.environ.get("MT_TRACE"):
        print(f"    [trace] {reason} @ detector line {line}")
    return reason
'''

lines = SRC.read_text().splitlines()
out: list[str] = []
pattern = re.compile(r'^(\s*)return "([a-z0-9-]+)"\s*$')
pattern2 = re.compile(r'^(\s*)(\w+)\(None, "([a-z0-9-]+)"\)\s*$')
pattern3 = re.compile(r'^(\s*)return (\w+)\(None, "([a-z0-9-]+)"\)\s*$')
for index, line in enumerate(lines, start=1):
    m = pattern.match(line)
    if m:
        out.append(f'{m.group(1)}return _REASON_TRACE("{m.group(2)}", {index})')
        continue
    m = pattern3.match(line)
    if m:
        out.append(f'{m.group(1)}return {m.group(2)}(None, _REASON_TRACE("{m.group(3)}", {index}))')
        continue
    m = pattern2.match(line)
    if m:
        out.append(f'{m.group(1)}{m.group(2)}(None, _REASON_TRACE("{m.group(3)}", {index}))')
        continue
    out.append(line)

text = "\n".join(out) + "\n"
# insert the helper after the import block (before the first module constant)
marker = "CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST"
position = text.index(marker)
text = text[:position] + HEADER + "\n\n" + text[position:]
OUT.write_text(text)
print("wrote", OUT, len(out), "lines")
