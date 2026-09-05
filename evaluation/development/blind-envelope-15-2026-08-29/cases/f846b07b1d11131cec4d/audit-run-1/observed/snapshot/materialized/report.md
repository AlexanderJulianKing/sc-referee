# Planting depth in saffron: a single-season corm trial

## Data

`data.csv` holds 64 data rows and one header row. A single row is one saffron corm: its bed
identifier, the depth it was planted at, and its four protocol outcome measurements taken over one
flowering season and the following lift.

| Column | Meaning | Unit |
| --- | --- | --- |
| `corm_id` | Corm identifier, `corm_` plus a zero-padded bed position number, unique across rows | none |
| `planting_depth` | Planting depth group, either `shallow` (10 cm) or `deep` (20 cm) | none |
| `flower_count` | Flowers the corm produced in the first season | flowers |
| `stigma_yield_mg` | Dry stigma yield harvested from that corm | mg |
| `daughter_corm_mass_g` | Total mass of the daughter corms attached at lifting | g |
| `time_to_first_flower_d` | Days from planting to the corm's first flower | days |

## Design

Sixty-four corms of the same size grade were each planted singly in their own bed position.
Thirty-two were planted shallow at 10 cm and thirty-two deep at 20 cm. Soil, spacing, irrigation
and lifting date were the same for every corm. Four outcomes were declared in the protocol before
planting, in this fixed order: flower count, stigma yield, daughter corm mass, and time to first
flower.

## How the comparison was done

Each outcome was compared between the two depths with a Welch two-sample t-test, which treats the
groups as independent and does not assume equal variances. The four outcomes are one declared
family, so the four raw p-values were collected and passed together, in a single call, to the
`multipletests` routine of the `statsmodels` library. The routine was called in its default form
with no correction method named or supplied, and the adjustment it applies by default was accepted.
Every conclusion below rests on an adjusted p-value judged at the 0.05 family level. Raw p-values
are quoted for transparency only, and no verdict is drawn from one.

## Results

Flower count averaged 2.91 flowers per corm when shallow (sd 1.06) and 3.22 when deep (sd 1.16), a
difference of +0.31 flowers. Raw p = 0.2639, adjusted p = 0.3601, so no difference between depths
was demonstrated.

Stigma yield averaged 20.99 mg when shallow (sd 7.72) and 28.20 mg when deep (sd 8.43), a
difference of +7.21 mg. Raw p = 0.0007, adjusted p = 0.0021, so deep planting gave a higher stigma
yield.

Daughter corm mass averaged 15.40 g when shallow (sd 4.47) and 16.90 g when deep (sd 4.77), a
difference of +1.50 g. Raw p = 0.2001, adjusted p = 0.3601, so no difference between depths was
demonstrated.

Time to first flower averaged 62.31 days when shallow (sd 4.87) and 67.88 days when deep (sd 5.25),
a difference of +5.56 days. Raw p < 0.0001, adjusted p = 0.0002, so deep planting delayed first
flowering.

## What the trial found

Planting depth separated the two groups on two of the four declared outcomes. Corms planted at
20 cm yielded about 7.2 mg more dry stigma each and took about 5.6 days longer to reach first
flower than corms planted at 10 cm. On the other two outcomes, flower count and daughter corm mass,
the deep group ran slightly higher in this season but the difference did not survive the
family-wide adjustment, so this trial does not establish an effect of depth on either. Deeper
planting therefore bought stigma yield at the cost of a later start, with no demonstrated change in
how many flowers a corm produced or how much daughter corm mass it built.
