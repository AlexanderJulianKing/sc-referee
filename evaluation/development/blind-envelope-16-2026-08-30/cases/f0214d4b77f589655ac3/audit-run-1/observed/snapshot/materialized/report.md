# Girth padding trial in working donkeys: foam pad vs traditional sacking-wrapped girth

## Data

The analysis uses `girth_pad_trial.csv`. **One row is one donkey**: a single adult
working donkey assessed once, after four weeks of normal brick-cart work, with its
harness group and its five declared outcome measurements from that one assessment.
There are 48 rows, 24 donkeys per group, and no missing values.

| Column | Description |
| --- | --- |
| `donkey_id` | Per-donkey identifier, `D01` to `D48` |
| `girth_type` | Harness group: `foam_pad` (24 donkeys) or `sacking_wrap` (24 donkeys) |
| `lesion_score_pts` | Girth-region skin lesion score, points on a 0 to 5 scale |
| `hair_loss_cm2` | Area of girth-region hair loss, square centimetres |
| `nociceptive_threshold_n` | Mechanical nociceptive threshold at the girth, newtons |
| `body_condition_pts` | Body condition score, points on a 1 to 9 scale |
| `rectal_temp_c` | Rectal temperature 15 minutes after the working day, degrees Celsius |

The five outcome columns appear in the order the trial declared them.

## Methods

Each of the five declared outcomes was compared between the two harness groups with a
two-sample t-test.

The five outcomes form one declared family, so the family-wise error rate was controlled
with a Sidak per-comparison threshold:

- family-wise error level: 0.05
- family size: 5 declared outcomes
- Sidak per-comparison threshold: 1 - (1 - 0.05)^(1/5) = **0.010206**

Every outcome was judged against that computed threshold of 0.010206, not against 0.05.

## Results

| Outcome | Mean, foam pad | Mean, sacking wrap | p-value | Sidak threshold | Verdict |
| --- | --- | --- | --- | --- | --- |
| `lesion_score_pts` | 0.917 | 2.333 | 3.30e-07 | 0.010206 | significant |
| `hair_loss_cm2` | 11.875 | 27.475 | 5.12e-06 | 0.010206 | significant |
| `nociceptive_threshold_n` | 24.471 | 20.129 | 0.001163 | 0.010206 | significant |
| `body_condition_pts` | 4.333 | 4.229 | 0.6109 | 0.010206 | not significant |
| `rectal_temp_c` | 38.400 | 38.492 | 0.3830 | 0.010206 | not significant |

Per-outcome conclusions, in the declared order:

1. **Lesion score.** Donkeys in the foam pad scored 1.42 points lower on the 0 to 5
   lesion scale. The p-value is below the Sidak threshold, so significant.
2. **Hair loss.** Foam-pad donkeys lost 15.6 cm2 less hair in the girth region, about
   57% less than the sacking-wrapped group. Below the threshold, so significant.
3. **Nociceptive threshold.** Foam-pad donkeys tolerated 4.34 N more pressure before
   responding, meaning less girth-region sensitivity. Below the threshold, so significant.
4. **Body condition.** The groups differed by 0.10 points on the 1 to 9 scale. Above
   the threshold, so not significant.
5. **Rectal temperature.** The groups differed by 0.09 degrees Celsius. Above the
   threshold, so not significant.

## Interpretation

All three girth-region outcomes moved in the direction that favours the closed-cell foam
pad: less visible skin damage, less hair loss, and less pressure sensitivity after four
weeks of work. Each cleared the stricter Sidak threshold, so the pattern is not an
artefact of testing five outcomes at once.

The two whole-animal outcomes, body condition and rectal temperature, were essentially
unchanged. That is what a welfare programme should expect over four weeks: the pad
changes the harness contact area, not the donkey's nutrition or thermal load. It also
suggests the girth-region gains are local effects of the padding rather than a general
difference between the two groups of animals.

For a working-animal welfare programme, this supports rolling out the closed-cell foam
girth pad as a low-cost change aimed at girth lesions, a common harness injury site. The
caveats are the ones this design carries: 48 animals assessed at a single four-week time
point, so the results say nothing about durability of the pad, longer-term body
condition, or whether the same benefit holds under different cart loads or climates.
