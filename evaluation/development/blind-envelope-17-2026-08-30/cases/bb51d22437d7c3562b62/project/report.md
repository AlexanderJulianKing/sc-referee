# Juvenile axolotl feed trial: live blackworms vs. formulated pellet

## Aim and feeds

The facility keeps juvenile axolotls for research supply and wanted to know which
of two feeds to standardise on. Sixty-four juveniles from one spawning were each
housed alone in an identical container on the same water system and at the same
temperature, and were fed for ten weeks. Thirty-two received live blackworms and
thirty-two received a formulated sinking pellet. The two feeds are the only
comparison in the study. Each animal was weighed and sampled individually at the
end of the ten weeks.

## Data

File: `axolotl_feed_trial.csv`. One row is one juvenile axolotl: its feed
assignment and its five end-of-trial outcome values. There are 64 data rows, 32
per feed group, every cell filled, and no animal appears twice.

| Column | Meaning |
| --- | --- |
| `animal_id` | Animal identifier, `ax001` through `ax064`, unique per row. |
| `feed_group` | Feed received for the ten weeks. Two values: `blackworm` (32 animals) and `pellet` (32 animals). |
| `specific_growth_rate_pct_per_day` | Specific growth rate over the ten weeks, in percent body mass per day. |
| `final_body_mass_g` | Body mass at the end of the ten weeks, in grams. |
| `feed_conversion_ratio` | Dry feed offered divided by mass gained, unitless. Lower is more efficient. |
| `whole_body_lipid_pct` | Whole-body lipid content at the end of the trial, as a percentage of wet mass. |
| `cortisol_release_ng_per_l_per_h` | Water-borne cortisol release rate at the end of the trial, in nanograms per litre per hour. |

The five outcome columns are in the order declared in the trial protocol.

## How the analysis was done

All analysis code is in `analysis.py`.

For each of the five declared outcomes we computed the observed two-group test
statistic comparing blackworm-fed with pellet-fed animals (a Welch two-sample t
statistic, blackworm minus pellet).

We then shuffled the feed-group labels across all sixty-four animals **5,000
times**, using the fixed random seed 20260830 stated in the script so the result
reproduces. For each shuffle we recomputed the test statistic for **every one of
the five outcomes** on the shuffled labels and recorded the **single largest
absolute statistic anywhere in the family** for that shuffle. That gives one
reference distribution of 5,000 family maxima, built directly in the script
rather than taken from a correction routine.

Each outcome was then judged against that family-maximum reference. Its
family-wise p-value is the share of the 5,000 shuffles whose recorded family
maximum is at least as large as that outcome's observed absolute statistic, and
its verdict comes from comparing that family-wise p-value with the conventional
0.05 threshold. No outcome was judged against an unshuffled per-outcome p-value.

The observed reference distribution of family maxima ran from 0.206 to 4.200,
with a median of 1.464 and a 95th percentile of 2.639.

### Why taking the maximum controls the family-wise error rate

Shuffling the labels breaks any real link between feed and outcome, so each
shuffled data set is a picture of what the trial would look like if the two feeds
made no difference at all. Because we look at five outcomes, the fair question is
not "how big a statistic can one outcome reach by chance?" but "how big a
statistic can the *best of five* reach by chance?" Recording only the largest
absolute statistic across the whole family in every shuffle answers exactly that
question: the reference distribution is the distribution of the best-looking
result out of five when nothing is going on. Comparing each real outcome with
that yardstick means the chance of calling *any* of the five outcomes a real
difference when none of them is stands at about 5 percent for the family as a
whole, not 5 percent per outcome. That is what family-wise error control means
here, and it is why a statistic that would look convincing on its own can still
fall short once it has to beat the best of five.

## Results

Reported in the declared protocol order. Means are group means over the 32
animals in each group.

**1. Specific growth rate (percent body mass per day).** Blackworm 1.025, pellet
0.980. Family-wise p = 0.9454. Not significant after family-wise control.

**2. Final body mass (g).** Blackworm 36.184, pellet 33.550. Family-wise
p = 0.3254. Not significant after family-wise control.

**3. Feed conversion ratio (unitless).** Blackworm 1.709, pellet 1.956.
Family-wise p = 0.0648. Not significant after family-wise control.

**4. Whole-body lipid content (percent of wet mass).** Blackworm 6.622, pellet
8.450. Family-wise p = 0.0000 (no shuffle out of 5,000 produced a family maximum
as large as the observed statistic). Significant after family-wise control.

**5. Water-borne cortisol release rate (ng/L/h).** Blackworm 3.272, pellet 3.759.
Family-wise p = 0.0910. Not significant after family-wise control.

One of the five declared outcomes clears the 0.05 threshold against the
family-maximum reference: whole-body lipid content, which is lower in
blackworm-fed animals. Feed conversion ratio (0.0648) and cortisol release
(0.0910) sit just above the threshold and do not clear it. Growth rate and final
body mass point in the blackworm direction but are well inside the range that
label shuffling produces by chance.

## Feeding recommendation

On this trial, the only difference that survives family-wise control over the
five declared outcomes is body composition: pellet-fed juveniles carried about
1.8 percentage points more whole-body lipid. Growth rate and final mass were not
separated by the two feeds once the whole family was accounted for, so the
facility should not expect faster or larger juveniles from either feed on the
strength of these data.

Where lean juveniles matter for the supply line, blackworms are the better
choice. Where they do not, the pellet is a reasonable option and carries the
usual husbandry advantages of a formulated diet, since nothing in this trial
showed it costing growth. The near-threshold results for feed conversion and
cortisol release are worth a second, larger trial aimed at those two outcomes
rather than being read as differences now.
