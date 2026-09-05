# Hoverflies on arable field margins: flowering mix versus grass-only mix

## Data

`data.csv` has 40 data rows and one header row. One row is one margin strip, holding that strip's
identifier, the seed mix sown on it, and its value for each of the five outcomes declared in the
survey protocol. There are no repeated rows, no summary rows, and no blank cells.

The columns, in file order, are: `strip_id`, the strip identifier (`strip_01` to `strip_40`, no
unit); `sown_mix`, the seed mix sown at establishment, holding the two labels `flower_mix` and
`grass_only` (no unit); `hoverfly_individuals`, hoverfly individuals counted on a fixed 50 m walk
along the strip (a count); `hoverfly_species_richness`, hoverfly species recorded on the strip (a
count of species); `flowering_plant_cover_pct`, flowering plant cover as a share of ground area
(percent); `aphid_colonies_with_hoverfly_larvae`, aphid colonies containing hoverfly larvae per 20
crop plants inspected at the field edge (a count per 20 plants inspected); and
`seed_set_seeds_per_head`, seed set of sentinel phytometer plants placed on the strip (seeds per
flower head).

## Design

Forty 100 m margin strips on commercial farms, each on a separate field, were surveyed once in
midsummer by the same protocol on comparable weather days. Twenty strips carry a multi-species
flowering mix and twenty carry the standard grass-only mix, assigned at establishment three years
before the survey. The survey protocol declared one outcome family, in this fixed order: hoverfly
individuals, hoverfly species richness, flowering plant cover, aphid colonies with hoverfly larvae,
and sentinel plant seed set.

## How the comparison was done

Each declared outcome was compared between the two mixes with one test, a two-sided Welch
two-sample t test, pre-specified for all five outcomes. Because the five outcomes form one declared
family, the family-wise error rate was set at 0.05 and spread across the family with a Sidak
correction. With family size 5, the per-comparison level is 1 minus the fifth root of 0.95, which
is 0.010206. Every conclusion below was judged against that per-comparison level of 0.010206. No
outcome was judged against 0.05.

## Results

Group sizes were 20 flowering-mix strips and 20 grass-only strips. Values below are means with
standard deviations in brackets.

| Declared outcome | Flower mix | Grass only | Difference | Welch t | p | Conclusion at 0.010206 |
|---|---|---|---|---|---|---|
| Hoverfly individuals | 24.10 (7.77) | 11.65 (7.76) | +12.45 | 5.071 | 1.06e-05 | significant |
| Hoverfly species richness | 7.30 (1.98) | 4.90 (2.05) | +2.40 | 3.770 | 0.00056 | significant |
| Flowering plant cover (%) | 32.60 (8.71) | 12.65 (8.74) | +19.95 | 7.230 | 1.20e-08 | significant |
| Aphid colonies with hoverfly larvae | 4.90 (2.25) | 3.45 (1.88) | +1.45 | 2.216 | 0.03298 | not significant |
| Seed set (seeds per head) | 39.97 (8.70) | 34.47 (9.23) | +5.50 | 1.940 | 0.05991 | not significant |

Three of the five declared outcomes separate the two mixes at the Sidak per-comparison level:
hoverfly abundance, hoverfly species richness, and flowering plant cover. The two remaining
outcomes do not. Aphid colonies containing hoverfly larvae averaged 1.45 more per 20 plants on
flowering-mix strips, and seed set averaged 5.50 more seeds per head, but each of those p-values
sits above 0.010206 and neither is called a difference here.

## What the study found

Margin strips sown with the multi-species flowering mix carried more flowering plant cover, more
hoverfly individuals, and more hoverfly species than strips sown with the standard grass-only mix,
and each of those three differences holds up under the family-wise correction. The two outcomes
that sit further downstream of the insects themselves, hoverfly larvae in aphid colonies at the
field edge and seed set of sentinel plants on the strip, both favour the flowering mix by a modest
amount, but this survey of 40 strips does not establish either difference at the declared level.
