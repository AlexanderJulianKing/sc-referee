# data.csv

Hoverfly survey of arable field margins. Forty 100 m margin strips on commercial farms, each
strip on a separate field, surveyed once in midsummer under the same protocol on comparable
weather days. Twenty strips were sown with a multi-species flowering mix and twenty with the
standard grass-only margin mix, assigned at establishment three years before the survey.

**One row is one margin strip**, holding that strip's identifier, its sown mix, and its value for
each of the five outcomes declared in the survey protocol. The file has 40 data rows and one
header row. There are no repeated rows, no summary rows, and no blank cells: every strip has a
value for every outcome.

## Columns

Columns appear in this order. The five outcome columns follow the order in which the outcomes were
declared in the protocol.

| # | Column | Meaning | Unit | Type |
|---|---|---|---|---|
| 1 | `strip_id` | Identifier of the margin strip, `strip_01` through `strip_40` | none | text |
| 2 | `sown_mix` | Seed mix sown on the strip at establishment | none | text, `flower_mix` or `grass_only` |
| 3 | `hoverfly_individuals` | Hoverfly individuals counted on a fixed 50 m walk along the strip | count | whole number |
| 4 | `hoverfly_species_richness` | Hoverfly species recorded on the strip | count of species | whole number |
| 5 | `flowering_plant_cover_pct` | Flowering plant cover on the strip, as a share of ground area | percent (%) | whole number |
| 6 | `aphid_colonies_with_hoverfly_larvae` | Aphid colonies containing hoverfly larvae, per 20 crop plants inspected at the field edge | count per 20 plants inspected | whole number |
| 7 | `seed_set_seeds_per_head` | Seed set of sentinel phytometer plants placed on the strip | seeds per flower head | number, one decimal place |

## Group labels

`sown_mix` holds exactly two labels:

- `flower_mix` — the multi-species flowering mix (20 strips)
- `grass_only` — the standard grass-only margin mix (20 strips)

## Recording notes

Counts and species richness are whole numbers, as recorded in the field. Flowering plant cover was
estimated to the nearest whole percent. Seed set is a per-strip mean over the sentinel plants' flower
heads and is recorded to one decimal place. Species richness on a strip never exceeds the number of
individuals counted there.
