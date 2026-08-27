# MT 3.0 audit-fix round-1 independent oracle

This directory is the independent expected-row authority for the fourteen MT 3.0 audit-fix
round-1 fixtures.

The provenance chain is:

1. `docs/implementation/MULTITEST-CODE-SLICE-3.0-RECORD-MODEL-DESIGN-2026-08-28.md`,
   Revision 1b, section 6.4 (record mutation closure) and section 4.1 (the record merge
   lattice, together with its unchanged threshold component grammar);
2. the matching probe rows in the MT 3.0 round-1 audit dated 2026-08-28; and
3. `EXPECTED_ROWS.json`, which transcribes those design-mandated outcomes and the probe shapes.

The artifact was authored from the approved design text and the audit probe table, not from detector
or adapter output. The test module owns only the mechanical source-mutation recipes. At test time it
joins those recipes to these expected rows by fixture name, verifies the generated source SHA-256,
and then compares analyzer and adapter output with this oracle.

