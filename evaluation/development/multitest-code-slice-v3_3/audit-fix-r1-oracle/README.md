# MT 3.3 audit-fix round-1 independent oracle

This directory is the independent expected-row authority for the MT 3.3 terminal-presentation
audit fix.

The provenance chain is:

1. `docs/implementation/MULTITEST-3.3-TERMINAL-PRESENTATION-DESIGN-2026-08-30.md`, section 4.1
   conditions 2, 4, and 5; section 4.3's one-output rule; section 4.4's count-consumer rule; and
   section 5's single-call-site helper rule;
2. the MT 3.3 adversarial audit and supervisor fix disposition dated 2026-08-30; and
3. `EXPECTED_ROWS.json`, which transcribes those design-mandated outcomes and attack shapes.

The artifact is authored from the approved design and audit table, not from implementation output.
`fixture_sources.py` owns deterministic source-selection and mutation recipes only. The
twice-print helper row is a positive control: it changes only presentation in sealed E16 P4, a
role-map positive whose family still makes raw-p conclusions. It therefore pins the inherited
frozen-path candidate as a genuine uncorrected misstep rather than treating it as a correct-case
refusal.
