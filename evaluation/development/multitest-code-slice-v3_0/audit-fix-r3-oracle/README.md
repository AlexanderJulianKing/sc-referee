# MT 3.0 audit-fix round-3 independent oracle

This directory is the independent expected-row authority for the five new MT 3.0 audit-fix
round-3 refusal fixtures and the pre-existing bare-transport positive control.

The provenance chain is:

1. `docs/implementation/MULTITEST-CODE-SLICE-3.0-RECORD-MODEL-DESIGN-2026-08-28.md`,
   Revision 1b, sections 6.4 and 6.5;
2. the matching B5 and section-6.4 probe rows in the MT 3.0 round-3 audit dated 2026-08-28; and
3. `EXPECTED_ROWS.json`, which transcribes those design-mandated outcomes and the probe shapes.

The artifact was authored from the approved design text and the audit probe table, not from detector
or adapter output. The test module owns only the mechanical source-mutation recipes. At test time it
joins those recipes to these expected rows by fixture name, verifies each source SHA-256, and compares
analyzer and adapter output with this oracle. The positive row reuses the already checked-in
`positive-record-prefix-holm-strict-subset` source; it proves that the exact bare same-record
`p_used = p_raw` transport remains admitted while derived cross-field expressions fail closed.
