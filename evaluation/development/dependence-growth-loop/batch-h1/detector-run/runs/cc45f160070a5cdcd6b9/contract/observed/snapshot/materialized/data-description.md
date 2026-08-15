# Weekly monitoring log of the pilot digester trial

`data/input.csv` records the routine weekly gas analysis of a twelve-vessel
pilot plant for anaerobic digestion. Each of the twelve digesters (D01-D12) was
seeded, sealed, fed and monitored separately; the vessels share only the
feedstock recipe and the laboratory that runs the gas chromatography. The trial
ran for eight weeks per digester: weeks 1-4 on the standard maize-silage feed,
weeks 5-8 on the same feed blended with a cobalt/selenium trace-element
supplement.

The file is stored in long form, one reading per line, so each digester appears
on eight separate lines. Those eight lines are repeated measurements of the same
vessel and track its individual inoculum, headspace and loading history; they
are not eight independent pieces of evidence about the supplement.

One row is: one weekly biogas methane reading taken from one digester during one phase of the trial
Independent unit column: digester_id

Columns:

- `digester_id`: label of the pilot digester the sample came from (D01-D12);
  twelve distinct vessels, eight rows each.
- `run_week`: week of the trial in which the sample was drawn, 1 to 8.
- `phase`: `baseline` for weeks 1-4 (standard feed) or `amended` for weeks 5-8
  (feed plus trace-element supplement).
- `ch4_percent`: methane content of the biogas at that weekly sampling, percent
  by volume, measured on a single grab sample.

Anything reported about the supplement should treat the digester as the unit of
analysis: collapse a digester's weekly readings to one value per digester per
phase, or to one paired change per digester, before applying a procedure that
assumes independent rows.
