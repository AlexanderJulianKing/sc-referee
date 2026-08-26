# Oat drink reformulation: consumer sensory panel report

**Study:** blind comparison of the current oat drink formulation against a reformulation
with a different enzyme treatment.
**Design:** 60 trained-naive consumer panellists, one session, monadic serving.
Each panellist tasted exactly one formulation, 30 per formulation, blind under red light,
and rated it on the declared scales immediately after tasting.
**Unit of the study:** the panellist.
**Analysis file:** `analysis.py` (root of the project). **Data file:** `panel_data.csv`.

---

## 1. Data description

### What one row represents

One row is one consumer panellist: a single trained-naive panellist who tasted exactly one
of the two formulations in the single blind session, together with the five ratings that
panellist gave for that sample. Each panellist appears in exactly one row and contributes
ratings for exactly one formulation. The 60 rows are therefore 60 different people, 30 who
tasted the current formulation and 30 who tasted the reformulation. There are no blank
cells: every panellist has a value in every outcome column.

### Columns

The columns appear in this order, with the five outcome columns in the order declared in
the sensory plan.

| Column | What it holds | Unit or scale |
| --- | --- | --- |
| `panellist_id` | Panellist identifier | Text code, `P01` to `P60`, unique to one panellist |
| `group` | Which formulation this panellist tasted | Text, exactly two entries: `current` (current formulation) and `reformulation` (reformulated enzyme treatment) |
| `overall_liking` | Overall liking of the sample | Nine-point hedonic scale, whole numbers 1 to 9 (1 = dislike extremely, 9 = like extremely) |
| `sweetness` | Sweetness intensity | Unstructured line scale scored 0 to 100, one decimal place (0 = none, 100 = extremely intense) |
| `thickness` | Thickness in the mouth | Unstructured line scale scored 0 to 100, one decimal place (0 = very thin, 100 = very thick) |
| `cereal_off_note` | Cereal off-note intensity | Unstructured line scale scored 0 to 100, one decimal place (0 = none, 100 = extremely intense) |
| `purchase_intent` | Purchase intent for the sample | Seven-point scale, whole numbers 1 to 7 (1 = definitely would not buy, 7 = definitely would buy) |

`overall_liking` and `purchase_intent` are box scales, so their values are whole numbers and
cluster on the boxes. The three line-scale attributes are read from a ruled line, so they
carry one decimal place and can fall anywhere from 0.0 to 100.0.

---

## 2. How the five outcomes were tested together

All five outcomes were declared together, in advance, as one family. Testing five
attributes and then reacting to whichever one looks largest would inflate the chance of
calling at least one difference real when none is. The laboratory controls that risk with
its own resampling procedure rather than with a correction formula, and `analysis.py`
implements the procedure by hand.

**The test statistic.** For each outcome the script computes Welch's two-sample t
statistic, reformulation minus current. A t statistic is unitless, which matters here
because the five outcomes sit on three different scales: 15 points of a 0 to 100 line scale
and half a point of a nine-point hedonic scale cannot be compared as raw numbers, but their
t statistics can.

**The label shuffle.** The design randomised which formulation each panellist received,
so under the null hypothesis of no formulation effect a panellist's five ratings would have
come out the same whichever sample had been served. The script exploits that. It shuffles
the `group` labels across the 60 panellists, keeping each panellist's five ratings tied
together and moving only the formulation label. The number of shuffles was **fixed in
advance at 5,000**, and the random seed is fixed (`20260826`) so the run reproduces exactly.

**The family maximum.** After each shuffle the script recomputes all five t statistics,
then records **only the single largest absolute statistic across the whole family** from
that shuffle and discards the other four. The 5,000 shuffles therefore build a reference
distribution of 5,000 family maxima: what the biggest of five statistics looks like in a
world where the formulation makes no difference to anything.

**Reading a verdict.** Each outcome's observed statistic is compared against that one
family-maximum distribution. The proportion of the 5,000 shuffles whose family maximum
equals or exceeds an outcome's observed absolute statistic is that outcome's family-wise
adjusted significance value, judged at the conventional five percent level.

**Why this controls the family-wise error rate.** If the reformulation truly changed
nothing, then a false call on any one of the five outcomes requires that outcome's observed
statistic to be large. An observed statistic can only clear this threshold if it is also
larger than 95 percent of shuffled family maxima, and the family maximum is by construction
at least as large as any single member of the family. So the event "at least one of the five
outcomes is called significant" is contained in the event "the observed family maximum
exceeds the 95th percentile of the shuffled family maxima", which happens 5 percent of the
time by definition of a percentile. The 5 percent being held is therefore the rate of making
**any** false call across all five outcomes, not the rate per outcome. The threshold also
adapts to the data: because the outcomes are shuffled together, the reference distribution
absorbs whatever correlation exists between the five ratings, which a formula-based
correction applied outcome by outcome cannot do.

For this data set the 95th percentile of the family-maximum distribution is
**|t| = 2.688**. That is the single family-wise critical value every outcome must clear.

---

## 3. Results

Outcomes are given in the declared order. `FWE p` is the family-wise adjusted value from
the 5,000-shuffle family-maximum distribution and is read directly against 0.05, with no
further correction.

| # | Outcome | Current mean | Reformulation mean | Difference | Welch t | FWE p | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Overall liking (1-9) | 6.07 | 5.83 | -0.23 | -0.525 | 0.9918 | not significant |
| 2 | Sweetness intensity (0-100) | 59.26 | 56.82 | -2.45 | -0.809 | 0.9454 | not significant |
| 3 | Thickness in the mouth (0-100) | 52.68 | 37.29 | -15.39 | -5.749 | 0.0000 | **significant** |
| 4 | Cereal off-note intensity (0-100) | 21.42 | 33.38 | +11.97 | 4.267 | 0.0004 | **significant** |
| 5 | Purchase intent (1-7) | 4.57 | 4.13 | -0.43 | -1.237 | 0.7252 | not significant |

Each group has n = 30. Standard deviations: overall liking 1.70 current and 1.74
reformulation; sweetness 11.76 and 11.66; thickness 10.53 and 10.21; cereal off-note 9.14
and 12.34; purchase intent 1.50 and 1.20.

Notes on the two significant outcomes:

- **Thickness** is the largest effect in the study. The reformulation lost 15.4 line-scale
  points of in-mouth thickness, close to a third of the current formulation's mean. No
  shuffle out of 5,000 produced a family maximum as large as the observed |t| of 5.749, so
  the family-wise value is 0.0000. With 5,000 shuffles the smallest non-zero value the
  procedure can resolve is 1/5,000 = 0.0002, so this should be read as "below the resolution
  of the declared number of shuffles" rather than as an exact zero.
- **Cereal off-note** rose by 12.0 line-scale points, from 21.4 to 33.4, and 2 of the 5,000
  shuffled family maxima reached the observed |t| of 4.267.

Overall liking, sweetness and purchase intent all sit far inside the family-maximum
distribution. Their observed statistics are smaller than the great majority of maxima
produced by pure label shuffling, so the panel gives no evidence of a formulation
difference on those three attributes. That is an absence of demonstrated difference, not a
demonstration of equivalence. The study was not designed or powered as an equivalence test,
and a 60-panellist monadic design can leave a modest true shift in liking undetected.

---

## 4. Conclusion

On the evidence from this panel the reformulation is **not acceptable as a like-for-like
replacement** in its current state. Two of the five declared attributes moved, both in an
unfavourable direction and both surviving family-wise control across the whole declared
family. The enzyme change thinned the product substantially in the mouth and raised the
cereal off-note by roughly half again over the current formulation.

Overall liking and purchase intent did not shift measurably in this session, so the two
sensory changes have not yet translated into a measured hedonic penalty here. That is not
grounds to proceed. Both changed attributes are drivers of liking in this category, the
present study is a single blind session with no repeat exposure and no home use, and its
liking and purchase-intent readings are not precise enough to rule out a commercially
meaningful decline.

Recommended next step for the product team: send the enzyme treatment back for
reformulation work targeted at restoring in-mouth thickness and suppressing the cereal
off-note, then re-run this same declared five-outcome panel on the revised sample before any
consumer or shelf decision.
