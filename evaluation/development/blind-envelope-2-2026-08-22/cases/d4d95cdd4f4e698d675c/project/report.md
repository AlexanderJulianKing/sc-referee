# Barrier-risk tight-junction genotype and day-7 TEER in donor-derived intestinal organoids

## Background and expectation

The intestinal epithelium keeps lumen and tissue apart, and the seal that does this sits in the
tight junction: a belt of claudins, occludin, and ZO scaffolding proteins that staples neighbouring
enterocytes together at their apical margin and sets how much ion flux can slip between cells. A
variant that changes the amount, the stability, or the strand architecture of one of these proteins
changes the electrical resistance of that seal in a fairly direct way, because transepithelial
electrical resistance (TEER) is essentially a readout of paracellular ion conductance: the tighter
the junctional strands, the fewer paths ions have between cells, and the higher the measured
resistance. Barrier-risk alleles in tight-junction genes have been of interest precisely because a
leakier epithelium is a plausible mechanistic step toward inflammatory disease. Biopsy-derived
intestinal organoids let us ask whether that liability is carried by the donor's cells themselves,
rather than by inflammation or by the luminal environment, because the organoid is grown out of the
donor's own stem cells in a controlled medium. So the expectation going in was that organoids from
carriers of the barrier-risk variant would form a measurably weaker barrier, that is, a lower day-7
TEER, than organoids from non-carriers.

## Data description

The data file is `organoid_teer.csv`: 108 data rows plus a header, 6 columns, comma separated. It
is simulated data with a realistic structure, not measurements from a real experiment.

**A single row is one well of organoids, measured once on day 7 after seeding.** The row carries
that well's TEER together with the properties of the donor the well came from. A well is not a
person. Each donor's cell preparation was seeded into 6 wells on the same plate layout, so **each
donor contributes six rows**, and those six rows repeat the same donor label, genotype, passage
number, and donor age. There are 18 donors and therefore 108 wells, with no missing values.

| Column | Type | Varies at | What it is |
|---|---|---|---|
| `donor_id` | text | donor | Donor label, `D01`-`D18`. Repeats across the six rows of that donor. This is the experimental unit. |
| `genotype` | text | donor | The donor's tight-junction genotype group: `non_carrier` (D01-D09) or `carrier` (D10-D18). Constant across a donor's six wells. |
| `well_position` | text | well | Where the well sat on the culture plate: `A1`, `A2`, `A3`, `B1`, `B2`, `B3`. Every donor used the same six-position layout, so each donor contributes each position once. |
| `passage_number` | integer | donor | Passage number of the organoid preparation that was seeded, range 2-5. One preparation per donor, so it is constant across that donor's six wells. |
| `donor_age_years` | integer | donor | Age of the biopsy donor in whole years, range 26-68. Constant across that donor's six wells. |
| `teer_day7_ohm_cm2` | number, 1 decimal | well | The outcome: transepithelial electrical resistance on day 7 after seeding, in ohm-cm-squared. One measurement per well; observed range 181.6 to 550.6. Higher means a tighter barrier. |

### Genotype varies between donors, not between wells

This is the fact that governs the whole analysis. Genotype is a fixed property of the person the
cells came from. It cannot differ between two wells seeded from the same preparation, and it does
not differ within any donor in this file. The six wells of a donor are **technical replicates**:
repeated measurements of one biological sample, sharing that donor's genetic background and one
common cell preparation. They tell us how precisely we measured that donor. They do not add
independent donors.

The numbers show the same thing. The standard deviation of the nine donor means is 45.6 ohm-cm-2 in
non-carriers and 39.8 in carriers, while the average spread of wells within a donor is only 28.2 and
30.2. Donor-to-donor differences are the larger source of variation, which is another way of saying
that two wells from the same donor resemble each other more than two wells picked at random. They
are correlated, so counting them as separate observations would be double-counting.

| Group | Donors | Wells | Mean TEER (ohm-cm-2) | Between-donor SD | Mean within-donor SD | Donor means span |
|---|---|---|---|---|---|---|
| `non_carrier` | 9 | 54 | 410.1 | 45.6 | 28.2 | 349.3 - 478.5 |
| `carrier` | 9 | 54 | 319.7 | 39.8 | 30.2 | 267.9 - 367.7 |

Because the design is balanced at six wells per donor, the group mean over wells and the mean of the
donor means are the same number.

## Primary analysis: donor-level resampling

The comparison was made by resampling at the level of the donor, written out by hand in
`analysis.py`. The idea is simple. To ask how much the observed difference would wobble if we had
happened to recruit a different set of nine carriers and nine non-carriers, we build many pretend
studies out of the donors we actually have. In each pretend study we draw nine donors with
replacement from the non-carrier group and nine with replacement from the carrier group, and
**whenever a donor is drawn, all six of that donor's wells come along as one block**, never a well
on its own, never a mixed handful of wells from different people. If a donor gets drawn twice, both
of his six-well blocks go in. We then recompute the difference in group means for that pretend
study, and repeat.

Keeping a donor's wells glued together is what makes the procedure honest. The wells inside a donor
are correlated, so a resampling scheme that shuffled individual wells would treat a donor's six
measurements as six chances to have recruited a different person. It would report a difference far
more precisely pinned down than the 18 donors can actually support. Resampling whole donors makes
the donor the thing that varies, which is what it is in the experiment, so the resulting spread
reflects the uncertainty that comes from having only nine donors per group.

The run used 20,000 resamples with a fixed random seed (20260822), so the numbers below reproduce
exactly on re-running.

**Result.** Non-carrier organoids averaged **410.1** ohm-cm-2 and carrier organoids **319.7**
ohm-cm-2. The observed difference, carriers minus non-carriers, is **-90.4 ohm-cm-2**, with a **95%
percentile bootstrap confidence interval of -127.8 to -53.2 ohm-cm-2**, from 20,000 donor-level
resamples. The sample size for this analysis is **9 donors per group, 18 donors in total.**

The interval lies entirely below zero, so at the donor level the data support a real reduction in
day-7 barrier resistance in organoids from carriers. In relative terms the point estimate is a drop
of about 22% from the non-carrier level, and the interval is consistent with a drop anywhere from
roughly 13% to 31%. That interval is wide, and its width is the honest consequence of having nine
donors per group. This resampling result is the inferential result of the project; the conclusions
below rest on it and on nothing else.

### Subordinate: the well-level comparison, shown only for illustration

For contrast only, the script also runs a plain independent two-sample t-test on the 108 individual
wells, as if every well were a separate subject. It returns t = -9.492 and **p = 7.8e-16**.

**That p-value is not valid for inference here and no conclusion in this report uses it.** It
assumes 108 independent observations when the study has 18 independent donors. Genotype varies
between donors and never between wells, so the extra wells inside a donor say something about
measurement precision for that donor and nothing further about whether carriers differ from
non-carriers. It is reported purely to show the size of the inflation: the same data, analysed at
the donor level where the biology actually varies, give an interval that is clearly separated from
zero but plainly finite in its confidence, while the well-level test manufactures a p-value near
1e-15 by counting nine people's replicate wells as fifty-four subjects. The evidence did not get
stronger; only the assumed sample size did.

## Interpretation and caveats

Taken at the donor level, organoids from carriers of the barrier-risk tight-junction variant formed
a weaker day-7 barrier, by roughly 90 ohm-cm-2 on a non-carrier baseline near 410. That the effect
survives in organoids, grown out of donor stem cells in a common medium and away from any
inflammatory milieu, points to a cell-intrinsic property of the epithelium that travels with the
donor's genotype rather than a consequence of the tissue environment. The direction fits the
mechanism: a variant that weakens tight-junction assembly should widen the paracellular ion path and
lower resistance. The size is also biologically plausible rather than trivial, being a fifth or so
of the baseline resistance.

Several limits should temper this.

- **Only 18 donors.** Nine per group is a modest sample, and the confidence interval says so: the
  true difference could plausibly be about half or about a third larger than the point estimate.
- **A single timepoint.** TEER was read only on day 7. We cannot tell whether carrier organoids
  build a weaker barrier or simply build it more slowly, which a time course would separate.
- **A single tissue source.** All organoids came from intestinal biopsies handled by one laboratory
  with one plate layout, so laboratory-specific culture and measurement effects cannot be separated
  from the biology.
- **Genotype was not randomised.** It is an observational property of the donors. Carriers and
  non-carriers differed somewhat in mean age (47.9 versus 51.6 years) and in mean passage number
  (3.33 versus 3.78), and with 18 donors those imbalances cannot be adjusted away with any
  confidence, so an unmeasured donor characteristic could contribute to the difference.
- **One preparation per donor.** Each donor contributed a single cell preparation, so preparation
  effects and donor effects are confounded; a second independent preparation per donor would let
  them be told apart.
- **Simulated data.** The values in `organoid_teer.csv` were generated to carry the described
  nested structure. The numbers above are real computations on that file, but they are not
  measurements from a real experiment.

A useful next step would be more donors rather than more wells per donor. Wells cheaply refine the
estimate for a donor already enrolled; only new donors narrow the interval that matters.

## Files

- `organoid_teer.csv` - the data, one row per well.
- `analysis.py` - the analysis script; run with `/usr/local/bin/python3 analysis.py`.
- `report.md` - this report.
