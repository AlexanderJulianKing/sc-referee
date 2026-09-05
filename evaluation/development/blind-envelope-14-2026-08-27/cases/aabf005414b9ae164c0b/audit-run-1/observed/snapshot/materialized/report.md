# Radon mitigation survey: active sub-slab depressurisation vs enhanced passive stack

## Data

The analysis reads one file, `radon_mitigation_survey.csv`: a header row plus 56 data
rows, comma separated, with no blank cells.

**One row is one single-family house.** Each house was fitted with a single mitigation
system, then surveyed once over one ninety-day measurement period twelve months after
installation. The four outcome values in a row are that one survey of that one house,
and each house appears exactly once, so the two mitigation groups are independent
samples of houses.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `house_id` | text | none | House identifier, `H-001` through `H-056`, unique in the file |
| `mitigation` | text | none | Which system was installed: `active_subslab` or `passive_stack` |
| `living_room_radon_bq_per_m3` | integer | Bq/m3 | Declared outcome 1: living room radon over the ninety-day period |
| `bedroom_radon_bq_per_m3` | integer | Bq/m3 | Declared outcome 2: main bedroom radon over the same period |
| `air_change_rate_ach` | decimal | air changes per hour | Declared outcome 3: whole-house air change rate |
| `indoor_rh_pct` | decimal | percent | Declared outcome 4: mean indoor relative humidity over the period |

## Design

All 56 houses sit on the same permeable gravel subsoil and all had confirmed elevated
indoor radon before installation. Twenty-eight houses received the active sub-slab
depressurisation fan system and twenty-eight received the enhanced passive stack with
sealed floor penetrations, so the group sizes are 28 and 28.

The service declared a family of four house-level outcomes before installation, in this
order: living room radon, bedroom radon, air change rate, indoor relative humidity. The
same four measurements were taken in every house.

Each outcome was compared between the two groups with a two-sided Welch two-sample
t-test. Welch's version does not assume the two groups share a variance, and here they
plainly do not: living room radon has a standard deviation of about 21 Bq/m3 in the
active group against about 56 Bq/m3 in the passive group.

## Multiple comparisons

The whole declared family of four outcomes was adjusted together for multiple
comparisons. The four raw p-values were collected and passed as one complete set, in a
single call, to `statsmodels.stats.multitest.multipletests` with no method argument, so
the family-wise adjustment applied is that routine's own default. No outcome was left
out of the set, and no outcome was judged on its raw p-value: every conclusion below is
read from the adjusted p-values at alpha = 0.05.

## Results

Group means are shown for each system. The difference is active sub-slab minus passive
stack, so a negative number means the active system read lower.

| # | Outcome | Active sub-slab mean | Passive stack mean | Difference | Raw p | Adjusted p | Conclusion at alpha = 0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Living room radon (Bq/m3) | 86.3 | 145.6 | -59.3 | 0.0000087 | 0.000035 | Significant: active sub-slab is lower |
| 2 | Bedroom radon (Bq/m3) | 79.3 | 119.7 | -40.4 | 0.00013 | 0.00040 | Significant: active sub-slab is lower |
| 3 | Air change rate (ACH) | 0.606 | 0.514 | +0.093 | 0.047 | 0.092 | Not significant after adjustment |
| 4 | Indoor relative humidity (%) | 46.56 | 46.23 | +0.34 | 0.82 | 0.82 | Not significant |

Outcome by outcome:

1. **Living room radon.** Houses with the active system averaged 86.3 Bq/m3 against
   145.6 Bq/m3 with the passive stack, a gap of 59.3 Bq/m3. The adjusted p-value is
   0.000035, so the difference survives the family-wise adjustment.
2. **Bedroom radon.** The same pattern, 79.3 Bq/m3 against 119.7 Bq/m3, a gap of
   40.4 Bq/m3, adjusted p = 0.00040. Also significant.
3. **Air change rate.** The active houses ventilated a little faster, 0.606 against
   0.514 air changes per hour. The raw p-value of 0.047 sits just under the
   conventional threshold, but it does not survive adjustment for the family of four
   (adjusted p = 0.092). This outcome is not declared significant.
4. **Indoor relative humidity.** The two systems are effectively the same, 46.56 percent
   against 46.23 percent, a gap of 0.34 percentage points, adjusted p = 0.82. Not
   significant.

## Interpretation for the mitigation programme

The clear result is on radon itself. In both measured rooms, houses with the active
sub-slab depressurisation fan read substantially lower than houses with the enhanced
passive stack, and both gaps hold up once the whole declared family is adjusted
together. On this gravel subsoil the active system is the stronger radon control, and
the size of the gap, roughly 40 to 60 Bq/m3, is large enough to matter for programme
targets rather than being a statistical curiosity alone.

The other two outcomes should not be reported as differences. Air change rate is the
one to be careful about: the raw p-value of 0.047 would read as significant if that
outcome were looked at on its own, but it was one of four pre-declared outcomes, and
after the family-wise adjustment it is 0.092. The honest reading is that this survey
does not establish a ventilation difference between the two systems; it is a candidate
for a study designed and powered around that question. Indoor humidity shows no
difference at all, which is reassuring for occupant comfort: the active fan system does
not appear to dry out or dampen the houses relative to the passive stack.

Two limits are worth stating. Houses were surveyed once each, over a single ninety-day
window twelve months after installation, so these are single-window readings rather than
a picture of how each system performs across seasons. And all 56 houses sit on the same
permeable gravel subsoil, so the comparison speaks to that ground condition and should
not be extended to other subsoils without further survey work.
