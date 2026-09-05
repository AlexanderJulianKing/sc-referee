# Permeable paving trial, municipal car park: single-storm runoff monitoring report

## 1. Purpose and scheme

The drainage authority is evaluating permeable paving for its car parks. Thirty-six individual
parking bays in one municipal car park were surfaced either with conventional dense asphalt or with
permeable concrete block paving laid over a gravel reservoir, eighteen bays of each surface. The two
surfaces are interleaved bay by bay across the car park, so both see the same traffic loading and the
same weather. Each bay drains to its own small collection sump. After one heavy summer storm the
sump of every bay was sampled and gauged once.

The bay is the unit of the study. Thirty-six bays were monitored and thirty-six bays are analysed.

## 2. Data description

The monitoring table is `runoff_bays.csv`: comma separated, one header row, 36 data rows, no missing
values and no blank cells. It was produced by the seeded generator `make_data.py` described in
`DATA_DESCRIPTION.md`.

**What one row represents.** One row is one individual parking bay in the car park, together with the
four outcomes measured from that bay's own collection sump after the single heavy summer storm. Each
bay appears exactly once, and every value on a row belongs to that one bay and that one storm.

**Columns, in file order:**

| Column | What it holds | Unit |
| --- | --- | --- |
| `bay_id` | Bay identifier, `BAY-01` to `BAY-36`, unique across the file. Numbering follows the physical order of the bays across the car park, starting at the entrance. | none (text label) |
| `group` | Surface type of the bay. Exactly two entries occur: `asphalt` for the conventional dense asphalt bays and `permeable` for the permeable block paving over gravel. 18 bays carry each entry. | none (text label) |
| `tss_mg_l` | Total suspended solids in the runoff collected from that bay's sump. | milligrams per litre (mg/L) |
| `zinc_ug_l` | Total zinc in the runoff collected from that bay's sump. | micrograms per litre (ug/L) |
| `peak_volume_l` | Peak runoff volume leaving that bay during the storm. | litres (L) |
| `runoff_temp_c` | Runoff temperature at peak flow. | degrees Celsius (deg C) |

The four outcome columns stand in the declared monitoring order: suspended solids, zinc, peak volume,
temperature. `BAY-01` and `BAY-02`, the two bays nearest the car park entrance, take the heaviest
turning movements and the most tracked-in street grit, and read dirtier than the rest of their own
surface group.

## 3. Method

The monitoring plan declared one family of four outcomes, and the authority asked that the chance of
any false claim across the whole family be held at five percent. The family size is therefore

    m = 4

and the family-wise level is `alpha_fw = 0.05`. The per-comparison threshold was computed by hand
inside `analysis.py` from the Sidak relation, one minus the family-size root of one minus the
family-wise level:

    alpha_pc = 1 - (1 - 0.05) ^ (1/4) = 0.012741

Every declared outcome is judged against this value, **0.012741**, and not against the conventional
0.05. The reason is multiplicity: with four outcomes each tested at five percent, the chance of at
least one false positive somewhere in the family runs close to nineteen percent. Tightening each
individual test to 0.012741 pulls the whole-family risk back to the five percent the authority asked
for. The threshold is not a fixed number typed into the script; the script holds the family size as a
value, does the arithmetic, and prints both, so a reader can trace where 0.012741 came from.

Each outcome was compared between the two surfaces with a standard two-group comparison of the 18
asphalt bay values against the 18 permeable bay values: a two-sample t-test in Welch form, which does
not assume the two surfaces share a variance.

## 4. Results

All four declared outcomes, in the declared order. Means are over the 18 bays of each surface.

| # | Outcome | Unit | Mean, asphalt | Mean, permeable | p-value | Sidak threshold | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `tss_mg_l` total suspended solids | mg/L | 142.76 | 43.52 | 2.74e-08 | 0.012741 | significant |
| 2 | `zinc_ug_l` total zinc | ug/L | 127.23 | 70.11 | 1.40e-05 | 0.012741 | significant |
| 3 | `peak_volume_l` peak runoff volume | L | 238.34 | 68.69 | 7.09e-11 | 0.012741 | significant |
| 4 | `runoff_temp_c` runoff temperature at peak flow | deg C | 25.76 | 21.63 | 9.61e-09 | 0.012741 | significant |

Outcome by outcome:

1. **Total suspended solids.** Asphalt bays averaged 142.76 mg/L, permeable bays 43.52 mg/L, a
   reduction of 99.24 mg/L, about 69.5 percent. p = 2.74e-08, below the 0.012741 threshold:
   significant.
2. **Total zinc.** Asphalt bays averaged 127.23 ug/L, permeable bays 70.11 ug/L, a reduction of
   57.13 ug/L, about 44.9 percent. p = 1.40e-05, below the threshold: significant.
3. **Peak runoff volume.** Asphalt bays averaged 238.34 L, permeable bays 68.69 L, a reduction of
   169.66 L, about 71.2 percent. p = 7.09e-11, below the threshold: significant.
4. **Runoff temperature at peak flow.** Asphalt bays averaged 25.76 deg C, permeable bays
   21.63 deg C, a reduction of 4.13 deg C, about 16.0 percent. p = 9.61e-09, below the threshold:
   significant.

All four p-values clear the Sidak threshold by a wide margin, so the verdicts do not turn on the
choice between 0.012741 and 0.05.

## 5. Conclusion

Across this one storm, the permeable bays differed from the adjacent asphalt bays on all four
declared outcomes, and each difference held up against the family-controlled threshold of 0.012741.
Permeable paving cut the solids load in the collected runoff by roughly two thirds and the zinc
concentration by roughly a half, cut peak volume leaving the bay by roughly seven tenths, and
delivered runoff about 4 deg C cooler. The volume reduction is consistent with a gravel reservoir
that holds and releases water rather than shedding it, and the cooler discharge is what would be
expected when water passes through the pavement and sub-base instead of running over a hot dense
asphalt surface.

Two limits should be read alongside these numbers. This is one storm at one car park, sampled once
per bay, so it shows what the surfaces did on that occasion and does not establish year-round or
cross-site performance. And the bays are interleaved but not randomised in the record available here,
so position effects across the car park, of the kind visible in the two dirty entrance bays, cannot be
separated from surface effects by this analysis alone. A multi-storm monitoring round covering a
range of rainfall depths and antecedent dry periods would be the next step before the authority sizes
a wider permeable paving programme.

---

*Analysis script: `analysis.py` (run from the project root; reads `runoff_bays.csv`). All figures in
this report are taken from its printed output.*
