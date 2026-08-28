# Peatland restoration monitoring: rewetted and drained blocks compared

## Data

`data.csv` is the record of one midsummer monitoring campaign. **One row is one permanent
gas sampling collar, holding the single set of measurements taken at that collar during the
campaign.** There are 32 rows, one per collar. The columns are:

| Column | Meaning | Unit |
| --- | --- | --- |
| `collar_id` | Identifier of the collar, unique in the file | none |
| `drainage_status` | Drainage status of the block the collar sits in, either `rewetted` or `drained` | none |
| `methane_flux_mgc_m2_h` | Methane flux at the collar, expressed as methane carbon | mg C m-2 h-1 |
| `respiration_co2_flux_mgc_m2_h` | Ecosystem respiration at the collar as carbon dioxide flux, expressed as carbon dioxide carbon | mg C m-2 h-1 |
| `water_table_depth_cm` | Depth of the water table below the peat surface, so larger values mean drier | cm |
| `sphagnum_cover_pct` | Sphagnum cover on the collar area | % of ground area |

## Design

Thirty-two collars were measured once each in the same campaign. Sixteen sit in a block of
bog rewetted by ditch blocking eight years ago, and sixteen in an adjacent block still
drained. The two blocks share climate, peat type and management history apart from
drainage. The monitoring plan declared four outcomes in this fixed order, and they form one
family: methane flux, ecosystem respiration as carbon dioxide flux, water table depth, and
Sphagnum cover.

## How the comparison was done

Each outcome was compared between the two blocks with a two-sided Welch two-sample t-test,
which does not assume the blocks share a variance. The same test was used for all four
outcomes, fixed in advance.

Because the four outcomes are one declared family, all four raw p-values were passed
together in a single call to `pingouin.multicomp` (pingouin version 0.5.5), using the Holm
step-down method at a family-wise level of 0.05. Every conclusion below rests on the
adjusted p-values that call returned. The raw p-values are shown for transparency and were
not used to decide anything.

## Results

Values are mean and standard deviation across the 16 collars in each block.

| Outcome | Rewetted | Drained | t | Raw p | Adjusted p | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| Methane flux (mg C m-2 h-1) | 3.80 (1.53) | 0.38 (0.26) | +8.821 | 1.637e-07 | 4.912e-07 | Higher on rewetted collars |
| Respiration CO2 flux (mg C m-2 h-1) | 73.33 (18.59) | 86.24 (16.20) | -2.093 | 0.0450 | 0.0450 | Lower on rewetted collars, marginal |
| Water table depth (cm) | 4.59 (3.49) | 37.01 (7.69) | -15.363 | 7.214e-13 | 2.886e-12 | Much shallower on rewetted collars |
| Sphagnum cover (%) | 45.00 (13.44) | 16.88 (9.03) | +6.949 | 2.114e-07 | 4.912e-07 | Higher on rewetted collars |

All four outcomes are significant at the 0.05 family level after the correction. The three
large separations are water table depth, methane flux and Sphagnum cover. Respiration is
the weak one. Its adjusted p-value of 0.0450 sits just under the threshold, the difference
of about 13 mg C m-2 h-1 is small against a within-block spread near 16 to 19, and the two
blocks overlap heavily, so it should be read as thin evidence rather than a firm result.
Under Holm, the largest p-value in a family is compared with the unadjusted level, which is
why the respiration value is unchanged by the correction.

## What the monitoring found

Eight years after ditch blocking, the rewetted block holds its water table about 32 cm
nearer the peat surface than the drained block, carries about 2.7 times the Sphagnum
cover, and emits about ten times the methane. That pattern matches a bog surface
that has returned to wet, Sphagnum-forming conditions, with the higher methane emission
that wet peat brings. The lower ecosystem respiration on rewetted collars points the same
way but rests on a marginal result and needs more campaigns before it can be relied on.

One caveat applies to all four outcomes. Drainage status was not assigned at random, and
each status covers a single contiguous block, so any block difference other than drainage
would be indistinguishable from the drainage effect in these data.
