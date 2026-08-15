# Dune slack restoration survey

A coastal dune system was restored in phases between 2015 and 2022. Twenty-four
separate dune slacks (the damp hollows lying between dune ridges) were
re-created, each by one of two engineering methods: deep topsoil inversion,
which buries the nutrient-enriched surface layer and brings calcareous sand back
to the top, or turf stripping, which simply scrapes the enriched layer away.
Which method a slack received was fixed by its phase contract and was not chosen
by the surveyor.

In July 2025 every slack was walked once and scored for the presence of marsh
helleborine, the target orchid of the scheme. A slack was scored `yes` if at
least one flowering spike was found anywhere inside its mapped boundary and `no`
otherwise. The slacks are separated by dune ridges, were restored under separate
contracts, and none of them was surveyed or entered twice, so each site yields a
single yes/no outcome and nothing more.

## Columns

- `site_id` - unique code for the slack, DS01 to DS24; appears on one row only.
- `restoration_method` - `inversion` or `stripping`.
- `slack_area_m2` - mapped area of the restored hollow, in square metres.
- `years_since_works` - whole years between the restoration works and the 2025
  survey.
- `helleborine_present` - `yes` or `no`, the single survey outcome for that
  slack.

The area and age columns are recorded for context and are not used by the test.

One row is: one restored dune slack, surveyed once in July 2025
Independent unit column: site_id
One trial is: one row
