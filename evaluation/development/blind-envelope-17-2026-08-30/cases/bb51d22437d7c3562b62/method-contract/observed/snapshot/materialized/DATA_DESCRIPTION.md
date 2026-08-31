# Data description

File: `axolotl_feed_trial.csv`

## What one row represents

One row is one juvenile axolotl. Sixty-four juveniles from a single spawning were
each housed alone in an identical container on the same water system and at the
same temperature, and were fed for ten weeks. Thirty-two were fed live
blackworms and thirty-two were fed a formulated sinking pellet. Each animal was
weighed and sampled individually at the end of the ten weeks, so a row holds one
animal's feed assignment and its five end-of-trial outcome values. There are 64
data rows plus one header row, every cell is filled, and no animal appears twice.

## Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `animal_id` | text | none | Animal identifier: the prefix `ax` plus a zero-padded three-digit serial number, `ax001` through `ax064`. Unique for every row. |
| `feed_group` | text | none | Feed the animal received for the ten weeks. Exactly two distinct values: `blackworm` (live blackworms, 32 animals) and `pellet` (formulated sinking pellet, 32 animals). |
| `specific_growth_rate_pct_per_day` | number | percent body mass per day | Specific growth rate over the ten weeks. Reported to two decimal places. |
| `final_body_mass_g` | number | grams | Body mass of the animal at the end of the ten weeks, from the facility scale. Reported to one decimal place (0.1 g). |
| `feed_conversion_ratio` | number | none (a ratio) | Dry feed offered to that animal divided by the mass it gained. Lower means the animal turned feed into body mass more efficiently. Reported to two decimal places. |
| `whole_body_lipid_pct` | number | percent of wet mass | Whole-body lipid content measured at the end of the trial, as a percentage of wet mass. Reported to one decimal place. |
| `cortisol_release_ng_per_l_per_h` | number | nanograms per litre per hour | Water-borne cortisol release rate measured at the end of the trial. Reported to two decimal places. |

The five outcome columns appear in the order declared in the trial protocol:
specific growth rate, final body mass, feed conversion ratio, whole-body lipid
content, then water-borne cortisol release rate.

## Notes on the values

Values carry the within-animal scatter expected of siblings reared individually,
and the two feed groups overlap on every outcome. Growth rate, final mass and
feed conversion move together within an animal, since a fast-growing animal is
also a heavier and more efficient one; lipid content and cortisol release track
that pattern only weakly. Any single animal's numbers should be read as one
measured animal, not as a summary of its feed group.
