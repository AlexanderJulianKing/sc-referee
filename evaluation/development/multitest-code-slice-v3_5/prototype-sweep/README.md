# Multiple-testing 3.5 recall-delta prototype sweep

This directory is answer-visible development evidence for the 3.5 design. It is not imported by
production code.

The strict shadow implements five closed productions. **Three are installed**, and two are
specified and deliberately not installed:

1. **D1, installed.** The three terminal-rendering *arm* positions admit two further display
   forms besides a bare string constant: `"<literal>".format(ARGVAL*)` and an f-string whose
   every interpolated value is an `ARGVAL`. `ARGVAL` is a scalar literal or a name bound exactly
   once at module level to a scalar literal, and an admitted arm must additionally carry no
   p-origin and no decision position.
2. **D2, specified and NOT installed.** A module-level set literal of unique string constants,
   every load of which is the right operand of an `in` / `not in` comparison, would be readable
   by the AP selector's per-row truth evaluation, and never as an ordered sequence.
   `instrument_results.json` records that it takes a pandas rung of E18 P6 from
   `unresolved-manual-correction-present` to the same `strict_subset` `(0, 3, 4)` of 8 the tuple
   spelling already reaches. It moves no sealed row, because the reader wall in front of it does
   not open (see D3).
3. **D3, specified and NOT installed.** `list(csv.DictReader(HANDLE))` / `list(csv.reader(HANDLE))`
   inside `with open(PATH, <text kwargs>) as HANDLE:` would be an authorized-reader lineage.
   A deliberately over-generous reader admission, strictly looser than this grammar, is executed
   on E18 P6 and lands on a third wall, `helper-free-name-unbound`, captured at the free name
   `row` in the helper `group_values`. So D3 cannot reach a classification and, under the
   ordering rule, changes no public byte.
4. **D4, installed as a pair.** D4a admits a numeric group-mask comparator that names exactly one
   CSV group token; D4b exempts a presentation loop's own iterator control from the hierarchy
   guard when nothing testable follows the loop, the loop carries no execution-prevention edge,
   nothing it binds escapes it, and it renders through a registered sink. D4a alone reaches only
   a different abstention, so the pair ships together or not at all.
5. **D5, installed.** `len(COLLECTION)` where `COLLECTION` is the fully reconstructed
   contract-order p-record family and the value reaches only a display sink is a cardinality
   read, not an unaccounted-for p transform.

The ordering rule is inherited from 3.4 and is load-bearing. A row the shipped 3.4 lane
classifies is returned untouched and no 3.5 production is attempted. A row it abstains on is
re-analysed with the installed productions, and that result is adopted only if it is itself a
classification; otherwise the frozen 3.4 reason is returned byte-for-byte.

The shadow never classifies a family. The unchanged shipped machinery classifies every source.

Run from the repository root:

```bash
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_5/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_5/prototype-sweep/sweep.py
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_5/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_5/prototype-sweep/verify.py
```

`results.json` and `instrument_results.json` are canonical JSON. `MANIFEST.json` binds every file
in this directory except itself and interpreter caches. There are no timestamps; identities, rows,
and digests derive only from checked-in input bytes and closed structural values.
