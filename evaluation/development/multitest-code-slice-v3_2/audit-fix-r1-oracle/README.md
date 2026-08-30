# MT 3.2 audit-fix round-1 independent oracle

This directory is the independent expected-row authority for the MT 3.2 conclusion-consumption
audit fix.

The provenance chain is:

1. `docs/implementation/MULTITEST-3.2-CORRECTION-RECOGNITION-DESIGN-2026-08-29.md`,
   Revision 1a, section 6;
2. the A/B, mixed-origin, threshold, and exact-reject-transport probe rows in the MT 3.2
   round-1 audit dated 2026-08-29; and
3. `EXPECTED_ROWS.json`, which transcribes those design-mandated outcomes and probe shapes.

This artifact was authored from the approved design text and audit probe table, not from detector,
adapter, guided-recheck, or implementation output. `implementation_output_used` is therefore
`false`. `fixture_sources.py` owns only deterministic source-selection and mutation recipes. At
test time the suite joins those recipes to the rows by fixture name, checks every source SHA-256,
and compares the final analyzer and guided-recheck results against this oracle.
