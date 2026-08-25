# Cereal rye cover crop and soil health after three seasons

## Design

Forty-eight field plots on one silt loam at the agronomy station, 24 under a winter
cereal rye cover crop and 24 left as bare winter fallow, sampled by soil core at
0-15 cm the following spring. Five soil measures were compared between systems with
Welch's two-sample t-test.

## Multiple comparison handling

Testing five outcomes at five percent each would let the study claim a false difference
about twenty-three percent of the time. All five raw p-values were therefore collected
into one ordered list and passed together, in a single call, to `multipletests` from
`statsmodels.stats.multitest` with a family-wide level of five percent. The routine's
default method was used: **Holm-Sidak** (`method='hs'`), a step-down procedure that
controls the family-wise error rate. The five outcomes are one family. Every decision
below is the routine's reject-or-not output on the adjusted p-value.

## Results

| Outcome | Fallow | Rye | Raw p | Holm-Sidak p | Decision |
|---|---|---|---|---|---|
| soil_organic_c_pct | 1.425 | 1.603 | 0.0073 | 0.0216 | reject H0 |
| bulk_density_g_cm3 | 1.387 | 1.348 | 0.0954 | 0.1259 | keep H0 |
| aggregate_stability_pct | 37.28 | 53.59 | 6.9e-07 | 3.5e-06 | reject H0 |
| microbial_biomass_c_mg_kg | 340.4 | 382.0 | 0.0651 | 0.1259 | keep H0 |
| nitrate_n_mg_kg | 16.62 | 9.78 | 1.3e-04 | 5.1e-04 | reject H0 |

Three of the five differences survive correction. Rye plots hold more soil organic
carbon (+0.18 percentage points), have far more water-stable aggregates (+16.3
percentage points, the largest and cleanest effect in the set), and carry a little over
40 percent less residual nitrate nitrogen. Bulk density and microbial biomass carbon
both moved in the expected direction but stayed inside the noise.

Reading the raw p-values directly would have produced the same three claims here, since
the two non-significant outcomes sit at 0.065 and 0.095 and clear neither threshold;
the correction cost nothing on this dataset but is what keeps the three-out-of-five
claim honest.

## Interpretation

The aggregate stability and nitrate results are the operationally useful ones. Better
aggregation after three rye seasons means a more resilient seedbed and less erosion
risk on this silt loam, and the drop in spring residual nitrate is the scavenging
effect the cover crop is planted for. The organic carbon gain is real but small, which
is what three seasons should buy. Bulk density is the outcome to keep watching: the
0.04 g/cm3 difference is in the right direction but would need either more plots or
more seasons to be worth a claim.
