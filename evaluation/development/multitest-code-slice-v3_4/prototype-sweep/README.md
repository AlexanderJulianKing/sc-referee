# Multiple-testing 3.4 comprehension, iterator, and cap prototype sweep

This directory is answer-visible development evidence for the 3.4 design. It is not imported by
production code.

The strict shadow implements five extensions. **Three are shipped**, one is specified and
deliberately not installed, and one is measured but not applied:

1. **A, shipped.** It lowers an exact contract-order dict or list comprehension to the equivalent
   explicit loop, so the frozen loop normalizer produces the same position-tagged record copies
   with p-origins that an author's hand-written loop already produces.
2. **B, specified and NOT installed.** It would widen the 3.3 terminal-`IfExp` proof to the
   compute-verdict-then-emit shape. `_extension_b_collision_probe` in `instrument.py` records why
   it is not shipped: on E16 P4 it admits one extra position, `prove_terminal_presentation` then
   sees two and returns `None`, and a pinned 3.3 candidate is lost.
3. **C, shipped.** It admits `enumerate(NAME)` and `enumerate(NAME, start=K)` as the AP row-table
   iterator, binding rows from the sequence order and never from the counter.
4. **D, shipped.** It absorbs the exact adjacent `X = p * F` / `if X > 1.0: X = 1.0` pair into one
   fold equivalent to `min(p * F, 1.0)`.
5. **E, measured and NOT applied.** It would route an abstention decided only by the
   outcome-headers branch of `_control_tracked` away from `hierarchical-gatekeeping-present`. The
   sweep records both `outcome` (unrouted, and the value every gate is computed on) and
   `outcome_with_reason_routing`. The routing relabels zero evidence cases and ten fixtures, eight
   of them frozen gatekeeping controls whose reason is already accurate, so the design recommends
   against applying it.

The ordering rule is load-bearing. A row the unchanged shipped 3.3 pipeline classifies is returned
untouched and no admission is attempted. A row it abstains on is re-analyzed with the shipped
admissions, and that result is adopted only if it is itself a classification; otherwise the frozen
3.3 reason is returned byte-for-byte. An earlier revision normalized unconditionally and lost the
pinned E16 P3 and E16 P4 candidates.

The shadow never classifies a family. The unchanged shipped 3.3 analyzer classifies every
normalized source.

`instrument_results.json` records the real 3.3 traces: E17 P3 stops at the line-71
`result['p'] < ALPHA` compare with **zero** p-origins, **no** correction control, and all six
outcome headers, which is the mislabel; E17 P6 tracks no hierarchy control at all. It also records
both mutation ladders, the `_dict_field_for_name` refusal, the grammar-level proof that the
specified B production refuses every named verdict-store shape, and the E16 P4 collision.

The sweep executes 170 evidence cases (120 opened E10-E17 plus 50 corpus cases) and 245 fixtures.
The fixtures comprise the frozen 203-row 3.3 population and 42 new 3.4 rows.

Run from the repository root:

```bash
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_4/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_4/prototype-sweep/sweep.py
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_4/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_4/prototype-sweep/verify.py
```

`results.json` and `instrument_results.json` are canonical JSON. `MANIFEST.json` binds every file
in this directory except itself and interpreter caches. There are no timestamps; identities, rows,
and digests derive only from checked-in input bytes and closed structural values.
