# Hydrophilic coating and biofilm on silicone catheter coupons

## Study and design

A hospital microbiology laboratory tested whether a hydrophilic surface coating
reduces bacterial biofilm on urinary catheter material. Forty-four sterile
silicone catheter coupons of identical size were prepared: 22 uncoated and 22
with the hydrophilic coating. Each coupon was incubated on its own in an
identical flow cell, with the same reference bacterial strain and the same
artificial urine medium, for 48 hours. Each coupon was then removed and measured
for the whole declared outcome family.

Group sizes: 22 uncoated coupons and 22 hydrophilic-coated coupons, 44 in total.

## Data

The data live in `biofilm_coupons.csv`. One row is one coupon, holding the
complete outcome family for that coupon; no coupon appears twice. Every cell is
filled, so there are no blanks.

| Column | Units | What it holds |
| --- | --- | --- |
| `coupon_id` | — | Coupon label, `CP-01` through `CP-44`, unique per row. |
| `surface` | — | Group, either `uncoated` or `hydrophilic`. |
| `biofilm_od590` | optical density at 590 nm | Declared outcome 1: biofilm biomass by crystal violet staining. |
| `viable_log10_cfu_per_cm2` | log10 CFU per cm^2 | Declared outcome 2: viable cells recovered from the coupon surface. |
| `thickness_um` | micrometres | Declared outcome 3: mean biofilm thickness by confocal imaging. |
| `eps_protein_ug_per_cm2` | micrograms per cm^2 | Declared outcome 4: extracellular polymeric substance protein on the coupon. |

## Analysis

For each declared outcome, the two surfaces were compared with a two-sample
Welch t-test, which is the two-sample test for a continuous measurement that
does not assume the two groups share a variance. Each declared outcome is its
own scientific question and stands on its own. An outcome is declared
significantly affected by the coating when its p-value is below 0.05.

## Results

Outcomes appear in the declared order. The difference is the hydrophilic mean
minus the uncoated mean, so a negative value means less biofilm on the coated
coupons.

| Declared outcome | Uncoated mean | Hydrophilic mean | Difference | p-value | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1. Biofilm biomass (OD590) | 0.980 | 0.460 | -0.520 | 2.7e-11 | significant |
| 2. Viable cells (log10 CFU/cm^2) | 6.420 | 6.030 | -0.391 | 0.0428 | significant |
| 3. Mean biofilm thickness (um) | 48.49 | 47.59 | -0.90 | 0.8274 | not significant |
| 4. EPS protein (ug/cm^2) | 27.50 | 15.84 | -11.66 | 6.9e-08 | significant |

## Conclusions

- **Biofilm biomass (OD590).** The coating significantly affects this outcome
  (p = 2.7e-11). Coated coupons carried about half the crystal violet signal of
  uncoated coupons, 0.460 against 0.980.
- **Viable cells (log10 CFU/cm^2).** The coating significantly affects this
  outcome (p = 0.0428). Coated coupons yielded 0.39 log10 CFU/cm^2 fewer viable
  cells, which is a small margin and sits just under the 0.05 threshold.
- **Mean biofilm thickness (um).** The coating does not significantly affect
  this outcome (p = 0.8274). The two surfaces were effectively the same, 47.6 um
  against 48.5 um.
- **EPS protein (ug/cm^2).** The coating significantly affects this outcome
  (p = 6.9e-08). Coated coupons carried 11.7 ug/cm^2 less EPS protein, about
  42 percent below the uncoated mean.

Taken outcome by outcome, the coating cut biofilm biomass and EPS protein
clearly, cut viable counts by a small margin, and left mean biofilm thickness
unchanged.
