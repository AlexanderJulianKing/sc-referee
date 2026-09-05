# Trickling filter pilot: crushed rock media against plastic cross-flow media

## Question and design

We needed to know whether swapping the conventional crushed rock packing for plastic cross-flow
packing changes how a trickling filter performs at this works. I ran a pilot bank of 32 columns
for ten weeks. All 32 were fed the same settled sewage from one common header tank, so the feed is
not a source of difference between them. Sixteen columns were packed with crushed rock and sixteen
with plastic cross-flow media, and packing media is the only grouping factor in the study. Each
column gave one set of steady-state numbers, averaged over the final two weeks of the run, so each
column contributes exactly one row of results.

Four outcomes were written into the pilot plan before commissioning, and they are examined here in
that same declared order: BOD removal, ammonium nitrogen removal, effluent suspended solids, and
attached biofilm dry mass.

## Data description

The data file is `pilot_columns.csv`. It holds 32 data rows and one header row. **One row is one
pilot column**, holding that column's steady-state values averaged over the last two weeks. No
column appears twice and no cell is empty.

| Column | What it holds |
| --- | --- |
| `pilot_column_id` | Identifier of the pilot unit, `TF-01` through `TF-32`, one per row. |
| `bod_removal_percent` | Biochemical oxygen demand removal across the column, in percent. |
| `ammonium_nitrogen_removal_percent` | Ammonium nitrogen removal across the column, in percent. |
| `effluent_suspended_solids_mg_per_l` | Suspended solids in the column effluent, in milligrams per litre. |
| `biofilm_dry_mass_g_per_m2` | Attached biofilm dry mass per unit of media surface area, in grams per square metre. |
| `packing_media` | The packing the column was filled with. Two values only: `crushed_rock` and `plastic_cross_flow`. |

The four measurement columns sit in the file in the order the outcomes were declared in the pilot
plan.

## Per-group summary

Group sizes: 16 columns on crushed rock, 16 columns on plastic cross-flow, 32 in total. Spread
below is the standard deviation within each group of 16.

| Outcome | Crushed rock (n, mean, sd) | Plastic cross-flow (n, mean, sd) |
| --- | --- | --- |
| BOD removal (%) | 16, 81.72, 5.62 | 16, 77.46, 6.59 |
| Ammonium nitrogen removal (%) | 16, 66.71, 7.70 | 16, 54.02, 8.07 |
| Effluent suspended solids (mg/L) | 16, 17.32, 4.45 | 16, 29.32, 10.29 |
| Biofilm dry mass (g/m2) | 16, 44.27, 9.32 | 16, 36.00, 8.03 |

## How the four outcomes were tested together

Each of the four outcomes was compared between the two media with a Welch two-sample t-test, which
is the ordinary two-group test for continuous measurements and does not assume the two groups have
matching variability. That matters here, since the suspended solids spread on plastic is more than
twice the spread on rock.

Testing four outcomes gives four chances to turn up a difference that is really just noise. To keep
that in check, I treated all four declared outcomes as a single family and put the four raw p-values
through one Holm-Bonferroni adjustment in a single pass, at the conventional family level of 0.05.
Think of it as one 0.05 budget of error shared across all four questions rather than a fresh 0.05
handed to each one. Every conclusion below rests on the adjusted value. The raw p-values are shown
for transparency, and none of them decides anything on its own.

| # | Outcome | Raw p | Adjusted p | Verdict at family alpha 0.05 |
| --- | --- | --- | --- | --- |
| 1 | BOD removal (%) | 0.05858 | 0.05858 | Not significant |
| 2 | Ammonium nitrogen removal (%) | 0.00008 | 0.00033 | Significant |
| 3 | Effluent suspended solids (mg/L) | 0.00035 | 0.00105 | Significant |
| 4 | Biofilm dry mass (g/m2) | 0.01163 | 0.02326 | Significant |

## Conclusions, in the declared order

1. **BOD removal.** Rock columns averaged 81.72 percent against 77.46 percent on plastic, about 4.3
   points higher. After the family adjustment this does not reach the 0.05 level, so on this
   evidence I cannot claim the two media differ in BOD removal.
2. **Ammonium nitrogen removal.** Rock columns averaged 66.71 percent against 54.02 percent on
   plastic, about 12.7 points higher, and the difference holds after adjustment. Rock media
   nitrifies better in this pilot.
3. **Effluent suspended solids.** Rock columns averaged 17.32 mg/L against 29.32 mg/L on plastic,
   about 12.0 mg/L lower, and the difference holds after adjustment. Rock media produced the
   cleaner effluent.
4. **Biofilm dry mass.** Rock columns averaged 44.27 g/m2 against 36.00 g/m2 on plastic, about 8.3
   g/m2 higher, and the difference holds after adjustment. Rock media carried more attached
   biomass per unit of surface area.

## Robustness check on the suspended solids result (not an inferential result)

One record deserves a note. Pilot unit TF-07, a plastic column, recorded 58.6 mg/L of effluent
suspended solids. The next highest reading in the whole bank is 40.3 mg/L, and no column running at
steady state should be putting out that much. The operator's log says the grab sample for that unit
was disturbed during collection. The value stays in the data file as recorded, and it stays in the
declared analysis above.

To see whether that one reading is carrying the suspended solids result, I re-ran that single
comparison once with TF-07 dropped. With 16 rock columns and 15 plastic columns, the means were
17.32 mg/L against 27.37 mg/L, a gap of about 10.1 mg/L, with an unadjusted p-value of 0.00008. The
gap is a little smaller without that reading and still points the same way, so the conclusion for
suspended solids is not resting on the one suspect sample.

This re-run is a robustness check on an outcome that was already decided in the section above. It
is not an inferential result. It received no multiplicity adjustment, it carries no significance
verdict, and it adds no conclusion of its own. The conclusion for effluent suspended solids is the
one stated in item 3 above, based on the adjusted family analysis of the full data set.
