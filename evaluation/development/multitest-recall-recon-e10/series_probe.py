import ast, sys
sys.path.insert(0, "/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/src")
sys.path.insert(0, ".")
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as M
from harness import analyze
from pathlib import Path

orig = M._MtEngine._series
def traced(self, node, active, depth):
    r = orig(self, node, active, depth)
    if depth <= 3:
        try:
            txt = ast.unparse(node)
        except Exception:
            txt = "?"
        print(f"    {'  '*depth}_series depth={depth} {txt[:80]!r} -> {r}")
    return r
M._MtEngine._series = traced
orig_frame = M._MtEngine._frame
def traced_frame(self, node, active, depth):
    r = orig_frame(self, node, active, depth)
    if depth <= 4:
        try: txt = ast.unparse(node)
        except Exception: txt = "?"
        print(f"    {'  '*depth}_frame depth={depth} {txt[:80]!r} -> {r}")
    return r
M._MtEngine._frame = traced_frame
case, path = sys.argv[1], sys.argv[2]
r = analyze(case, Path(path))
print("RESULT", r.reason)
