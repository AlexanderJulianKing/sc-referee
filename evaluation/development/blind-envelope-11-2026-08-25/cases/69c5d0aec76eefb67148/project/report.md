# Avocado pulp shelf life at 21 days: high-pressure processing versus mild thermal pasteurisation

## Question and design

We wanted to know how our two stabilisation routes for retail avocado pulp compare after three
weeks on a chilled shelf. Thirty-six sealed retail pouches were filled from a single homogenised
batch on one production day. Eighteen pouches were stabilised by high-pressure processing and
eighteen by conventional mild thermal pasteurisation, and the two methods were assigned across the
fill order at random. Every pouch was held at 4 degrees Celsius and opened once, after 21 days of
chilled storage, for measurement.

The shelf-life protocol declared three outcomes before any pouch was opened, in this order: pulp
greenness as the colour a* coordinate, residual polyphenol oxidase (PPO) activity as a percent of
the raw pulp, and total aerobic plate count in log10 CFU per gram. Each of these is a separate
quality question for this product. Greenness is what the shopper sees, residual PPO tells us
whether the pulp will brown later in the pack, and plate count is the microbiological standard the
pouch has to meet. A pouch can pass on one and fail on another, so each outcome is answered on its
own terms with its own two-group comparison of the methods.

## Data description

The study data are in `pouch_shelf_life.csv`. **One row is one sealed retail pouch**: a single
pouch filled from the one homogenised batch, stabilised by one of the two methods, held at 4
degrees Celsius, and opened once at day 21. The three measured columns are the readings taken from
that pouch at that single opening. Each pouch appears exactly once, and there are no missing cells.

| Column | What it holds |
| --- | --- |
| `pouch_id` | Pouch identifier, `P01` through `P36`, unique, following the fill order of the batch. |
| `colour_a_star` | Greenness of the pulp, the a* coordinate of instrumental colour, unitless, two decimals. Negative means green, so a more negative number is a greener pulp. |
| `residual_ppo_activity_percent` | Residual polyphenol oxidase activity, as a percent of the activity in the unprocessed raw pulp, one decimal. |
| `aerobic_plate_count_log10_cfu_per_g` | Total aerobic plate count, in log base ten colony forming units per gram of pulp, two decimals. |
| `processing_method` | The stabilisation method applied, with exactly two values: `high_pressure` and `thermal_pasteurised`. |

The three measured columns sit in the order the protocol declares them: colour, then residual
enzyme activity, then plate count.

## Per-group summary

Group sizes came out as planned: 18 pouches under high pressure and 18 under thermal
pasteurisation, 36 in total. Spread below is the standard deviation across pouches within the
method.

| Declared outcome | Method | Pouches | Mean | SD |
| --- | --- | ---: | ---: | ---: |
| 1. Colour a* (unitless) | high_pressure | 18 | -8.57 | 0.96 |
| | thermal_pasteurised | 18 | -5.06 | 0.99 |
| 2. Residual PPO activity (% of raw) | high_pressure | 18 | 22.57 | 5.33 |
| | thermal_pasteurised | 18 | 10.21 | 4.42 |
| 3. Aerobic plate count (log10 CFU/g) | high_pressure | 18 | 1.90 | 0.30 |
| | thermal_pasteurised | 18 | 1.78 | 0.39 |

Each outcome was compared between the two methods with a two-sample t test of the Welch form,
which does not assume the two methods share a variance, and judged against the conventional 0.05
threshold.

## Conclusions, in the declared order

**1. Greenness of the pulp (colour a*).** The methods differ significantly (p = 1.7e-12).
High-pressure pouches averaged -8.57 against -5.06 for the pasteurised pouches, a gap of about 3.5
a* units, so the high-pressure pulp held roughly three and a half units more green after three
weeks. The two groups barely overlap. On appearance, high-pressure processing is clearly the
better route.

**2. Residual polyphenol oxidase activity.** The methods differ significantly (p = 1.1e-08).
High-pressure pouches retained 22.57 percent of the raw pulp's PPO activity, while pasteurised
pouches were down to 10.21 percent, so the heat step inactivates the browning enzyme far more
thoroughly. That is a real concern for high-pressure pouches later in life: the enzyme that drives
browning is still largely there, and today's better colour rests on it not having acted yet.

**3. Total aerobic plate count.** The methods do not differ significantly (p = 0.29).
High-pressure pouches averaged 1.90 log10 CFU/g and pasteurised pouches 1.78, a difference of about
0.12 log, which is small next to the pouch-to-pouch spread of roughly 0.3 to 0.4 log. Both methods
sit low on the plate, and at 21 days neither has a microbiological advantage over the other that
this study can see.

Taken together, high-pressure processing wins on the colour the customer judges the pack by, loses
on residual browning enzyme, and ties on microbial load at three weeks.
