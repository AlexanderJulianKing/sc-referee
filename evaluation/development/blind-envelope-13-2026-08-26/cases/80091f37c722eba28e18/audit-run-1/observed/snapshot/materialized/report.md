# Twelve-week hand-skin study in apprentice hairdressers: glove protocol comparison

## What the data are

The file `hand_skin_study.csv` holds the week-12 measurements from a twelve-week hand-skin study in
54 apprentice hairdressers at a salon chain. Each apprentice was assigned to one of two glove
protocols, 27 per protocol, and was measured once at the end of week 12.

**One row is one apprentice**: their identifier, their glove protocol, and their seven week-12
outcome measurements. There are 54 data rows plus a header, and every cell is filled.

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `participant_id` | Anonymous apprentice identifier, `AP001` to `AP054`, one per row | none (text label) |
| `glove_protocol` | Assigned protocol: `liner_under_nitrile` (thin cotton liners under disposable nitrile gloves) or `nitrile_only` (disposable nitrile gloves alone) | none (group label) |
| `transepidermal_water_loss_g_m2_h` | Water lost through the skin on the back of the dominant hand. Declared **primary** barrier outcome 1. Higher means a leakier barrier | grams per square metre per hour (g/m²/h) |
| `stratum_corneum_hydration_au` | Moisture held in the outer skin layer of the dominant hand. Declared **primary** barrier outcome 2. Higher means better hydrated | arbitrary capacitance units (a.u.) |
| `hand_eczema_severity_score_points` | Clinician's hand eczema severity rating, whole numbers. Secondary outcome. Higher means worse | points on a 0 to 30 scale |
| `self_reported_itch_score_points` | The apprentice's own itch rating, whole numbers. Secondary outcome. Higher means more itch | points on a 0 to 10 scale |
| `skin_surface_ph` | Skin surface pH of the dominant hand. Secondary outcome. Higher means more alkaline and less protective | pH (dimensionless) |
| `erythema_index_au` | Skin redness index. Secondary outcome. Higher means more redness | arbitrary units (a.u.) |
| `hand_symptom_days_last_4_weeks_days` | Days with hand symptoms in the previous four weeks, whole numbers. Secondary outcome | days (0 to 28) |

The seven outcomes sit in the columns in the order the study protocol declared before recruitment:
water loss, hydration, eczema severity, itch, pH, erythema, symptom days. The first two are the
primary barrier-function outcomes and the other five are secondary.

## How the comparison was done

`analysis.py` compares the two protocols on each outcome with the same test throughout: a two-sample
Student t-test (`scipy.stats.ttest_ind`). Group sizes are 27 and 27 for every outcome.

The two primary barrier-function outcomes carry the protocol's main claim, so their two p-values were
adjusted together with the Holm routine from `statsmodels.stats.multitest.multipletests`, and their
verdicts rest on the adjusted values. The five secondary outcomes are reported with their plain
unadjusted p-values and given a significant or not significant verdict at the usual 0.05 threshold.

All numbers below are the values `analysis.py` prints.

## Results

### Primary barrier-function outcomes (Holm-adjusted across the two)

**1. Transepidermal water loss (g/m²/h).** Liners under nitrile 11.770, nitrile alone 12.837, a
difference of -1.067. t = -1.777, unadjusted p = 0.0814, Holm-adjusted p = 0.1628. **Not
significant.** The liner group's barrier leaked about one unit less water on average, which is the
direction you would want, but the study cannot rule out chance as the reason. For skin protection at
work, this means the trial gives no dependable evidence that liners keep the barrier tighter.

**2. Stratum corneum hydration (a.u.).** Liners under nitrile 39.015, nitrile alone 37.222, a
difference of +1.793. t = 1.670, unadjusted p = 0.1008, Holm-adjusted p = 0.1628. **Not
significant.** Hands in the liner group read as slightly better hydrated, again in the hoped-for
direction, but the gap is small next to the spread between apprentices. On its own this outcome does
not support a claim that liners keep hands moister.

Neither primary outcome clears the threshold, so the protocol's main barrier-function claim is not
supported by this study.

### Secondary outcomes (unadjusted p-values, threshold 0.05)

**3. Hand eczema severity score (0-30 points).** Liners 4.815, nitrile alone 6.704, a difference of
-1.889. t = -4.429, p = 0.0000490. **Significant.** Clinicians rated liner-group hands close to two
points less severe on the 30-point scale. In a salon that is the difference between hands that look
irritated and hands that look sore, and it is the clearest signal in the study.

**4. Self-reported itch score (0-10 points).** Liners 3.111, nitrile alone 3.444, a difference of
-0.333. t = -1.233, p = 0.2232. **Not significant.** Apprentices in both groups reported roughly the
same itch. Whatever the clinician sees, the apprentices themselves did not feel a clear difference in
day-to-day discomfort.

**5. Skin surface pH.** Liners 5.261, nitrile alone 5.401, a difference of -0.140. t = -2.939,
p = 0.0049. **Significant.** The liner group's skin stayed slightly more acidic. An acidic surface is
the skin's normal state and supports its defence against irritants, so this points the same way as
the eczema scores.

**6. Erythema index (a.u.).** Liners 8.593, nitrile alone 9.530, a difference of -0.937. t = -3.870,
p = 0.000305. **Significant.** Hands in the liner group were visibly less red. Redness tracks
irritation, so this again lines up with the lower eczema severity.

**7. Hand symptom days in the last 4 weeks (days).** Liners 6.407, nitrile alone 6.889, a difference
of -0.481. t = -0.743, p = 0.4611. **Not significant.** Both groups reported symptoms on roughly
six to seven days out of the previous 28. Liners did not measurably cut the number of bad days.

## Conclusion and recommendation

The two primary barrier-function outcomes both favoured cotton liners worn under nitrile gloves, but
neither reached significance after adjustment, so the study's main claim about barrier function
stands unproven. Three of the five secondary outcomes did reach significance and all three point the
same way: apprentices wearing liners had lower clinical eczema severity, less redness, and a slightly
more acidic skin surface. The two outcomes that depend on what apprentices report about themselves,
itch and symptom days, showed no clear difference.

For the chain, the practical recommendation is to adopt thin cotton liners under disposable nitrile
gloves as the standard protocol for apprentices doing wet work. The measured clinical benefit is
modest and rests on secondary outcomes rather than the primary barrier measures, but liners are cheap
and low-risk, no outcome favoured nitrile alone, and every difference ran in the protective
direction. Because the primary barrier outcomes did not settle the question at 54 apprentices, the
chain should treat this as a supported operational preference rather than a proven barrier effect,
and should confirm it in a larger study before making any stronger claim.
