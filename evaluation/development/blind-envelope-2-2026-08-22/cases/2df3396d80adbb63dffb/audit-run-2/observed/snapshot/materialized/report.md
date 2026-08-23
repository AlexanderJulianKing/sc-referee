# Daily milk yield on two total mixed rations differing in rumen-undegradable protein source

## Why the protein source matters

Milk protein synthesis in the high-producing dairy cow depends on the supply of amino acids
absorbed from the small intestine, and that supply comes from two places: microbial protein leaving
the rumen, and dietary protein that escapes ruminal degradation. Once a cow is past peak intake,
microbial protein alone rarely covers her requirement, so the rumen-undegradable fraction of the
ration becomes the lever a nutritionist can actually pull. Soybean meal is the conventional
workhorse in North American total mixed rations, but a large share of its protein is degraded in the
rumen and returns to the animal as ammonia and, ultimately, as urea in urine. Heat and moisture
treatment of canola meal shifts a larger fraction of its protein past the rumen, and canola protein
carries a favourable methionine and histidine profile relative to soybean meal. The practical
question for a herd nutritionist is whether that shift in escape protein converts into milk in the
bulk tank. This trial was run to answer that question directly, under commercial freestall
conditions, in mid-lactation Holstein cows.

## Trial and data

Twenty lactating Holstein cows in a single research herd were enrolled between 90 and 148 days in
milk and housed together in one freestall barn. Ten cows were fed the conventional soybean-meal
total mixed ration and ten were fed the treated-canola total mixed ration. Each cow stayed on her
assigned ration for the whole trial. Daily milk yield was recorded on six consecutive weekly test
days, producing 120 test-day records in the data file.

### The data file

`milk_yield.csv` holds 120 data rows and one header row, in six columns, comma separated.

**One row is one cow on one weekly test day**: a single animal's recorded daily milk yield for a
single test day, together with her identity, her ration, the test week, her days in milk on that
day, and her parity. There are 20 distinct cows and 6 test weeks, so each cow appears in 6 rows.

| Column | Type | Values in this file | Meaning |
| --- | --- | --- | --- |
| `cow_tag` | text | `HO-2101` through `HO-2120`, 20 distinct values, each appearing 6 times | Ear-tag identifier of the individual Holstein cow. |
| `ration` | text | `conventional_soybean_meal` or `treated_canola` | The total mixed ration formulation the cow was fed. It is the same in all 6 rows for a given cow. |
| `test_week` | integer | 1 through 6 | Which of the six consecutive weekly test days the row records. Week 1 is the first test day after enrolment. |
| `days_in_milk` | integer | 90 to 183 | Days since calving as of that test day. The range at week 1 is 90 to 148 days, and it advances by 7 days for each later test week. |
| `parity` | integer | 1 to 4 (10 cows in parity 1, 7 in parity 2, 2 in parity 3, 1 in parity 4) | Number of times the cow has calved. |
| `milk_yield_kg` | decimal, one place | 23.8 to 42.9 | The outcome: daily milk yield in kilograms on that test day. |

## Statistical comparison

Daily milk yield was compared between the two rations with a single independent two-sample t-test
(Student's t, pooled variance, two-sided). Each test-day record in the table entered that comparison
as one observation. The sample size for the comparison is therefore 60 test-day records in the
conventional soybean-meal group and 60 test-day records in the treated-canola group, 120 test-day
records in total, giving 118 degrees of freedom. The analysis is implemented in `analysis.py`, which
reads `milk_yield.csv` and prints every number quoted below.

## Results

| Ration | n (test-day records) | Mean yield (kg/d) | SD (kg/d) |
| --- | --- | --- | --- |
| Conventional soybean meal | 60 | 30.60 | 3.11 |
| Treated canola | 60 | 32.73 | 4.08 |

The treated-canola ration produced a mean daily yield 2.12 kg higher than the conventional
soybean-meal ration (32.73 versus 30.60 kg/d). The two-sample t-test gives t = 3.205 on 118 degrees
of freedom, p = 0.0017.

## Interpretation

A 2.12 kg/d advantage is a meaningful response for a protein-source substitution in mid lactation.
It represents a 6.9 percent increase over the 30.60 kg/d achieved on the conventional ration. Across
the six-week observation window the advantage amounts to roughly 89 kg of additional milk per cow,
and in a 100-cow milking string it is on the order of 212 kg of additional milk per day.

The economics follow from that quantity in a straightforward way. The gross return is 2.12 kg
multiplied by the farmgate milk price a given operation receives, per cow per day, and the decision
turns on whether that gross return clears the cost gap between treated canola meal and soybean meal
at the inclusion rates used here. Treated canola typically carries a premium per tonne of product,
so a herd should price both ingredients delivered, convert the difference to a cost per cow per day
at its own inclusion rate, and compare it against the milk revenue above. Component yield and milk
urea nitrogen were not measured in this trial, so the value of the ration change is assessed on
volume alone; a nitrogen-efficiency benefit, if present, would sit on top of the figure above.

Several practical caveats apply to how far these results should be carried.

The trial ran six weeks. That window is long enough to see a persistent shift in yield rather than a
transient response to a ration change, but it is not long enough to speak to persistency over a full
lactation, to body condition, or to reproductive outcomes. A response measured in mid lactation does
not automatically hold through late lactation, when intake and yield both decline.

All cows were in one herd, in one freestall barn, on one forage base. Forage quality and the
composition of the basal ration set the background against which any protein-source effect is
expressed, and a herd on a different corn silage or a different starch level could see a smaller or
larger response. Single-herd trials also carry whatever is idiosyncratic about that herd's genetics,
management, and cow comfort.

Enrolment was restricted to 90 to 148 days in milk, and no cow passed 183 days in milk during the
trial. The result therefore speaks to mid-lactation cows. Fresh cows in the first 60 days, where
metabolizable protein supply is most limiting and negative energy balance dominates, were not
represented, and neither were late-lactation cows. Extending this ration change to the whole herd is
a reasonable operational decision, but the direct evidence here covers the mid-lactation group.

Parity was mixed, with half the cows in first lactation, and the trial was not sized to separate a
primiparous from a multiparous response. Nothing in these data argues that the response differs by
parity, and nothing in them establishes that it does not.

## Conclusion

Replacing soybean meal with treated canola meal as the rumen-undegradable protein source raised
daily milk yield by 2.12 kg/d in mid-lactation Holstein cows (32.73 versus 30.60 kg/d, p = 0.0017).
The response is large enough to justify the substitution wherever the delivered price of treated
canola meal leaves room for it, and it warrants confirmation over a longer window and across more
than one forage base before it is treated as a general recommendation.
