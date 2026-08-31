# Rearing substrate trial: fine sand versus coarse gravel

## Aim

The hatchery rears juvenile freshwater pearl mussels for reintroduction to the river. This trial
asks which of two rearing substrates produces better twelve-month outcomes: a fine sand bed or a
coarse gravel bed. Sixty-six individually tagged juveniles from one captive cohort were held for
twelve months in flow-through rearing cells supplied from the same header tank, thirty-three cells
with fine sand and thirty-three with coarse gravel. The two substrates are the only comparison in
the study.

## Data

File: `mussel_rearing_data.csv`. One row is one individually tagged juvenile, measured at the end
of the twelve-month rearing period. There are 66 rows, 33 sand and 33 gravel, with no missing
cells.

Columns:

- `mussel_tag` - individual tag identifier, prefix `PM` plus a zero-padded three-digit serial.
- `substrate` - rearing substrate group, either `sand` or `gravel`.
- `shell_length_increment_mm` - shell length increment over the twelve months, in millimetres.
- `wet_mass_gain_g` - wet mass gain over the twelve months, in grams.
- `condition_index_pct` - condition index, soft tissue dry mass as a percentage of shell dry mass.
- `foot_glycogen_mg_per_g` - foot tissue glycogen concentration, in milligrams per gram dry mass.
- `clearance_rate_l_per_h` - clearance rate from the standard feeding assay, in litres per hour per
  individual.

## How the comparison was done

The five outcomes above were declared as one outcome family in the rearing protocol before the
trial began, in the order listed. Each outcome was compared between the two substrates with a
two-sample t-test.

Because all five comparisons belong to one family, the family-wise error rate was controlled with
the Sidak correction. The per-comparison threshold was computed in `analysis.py` from the
family-wise level of 0.05 and the five outcomes in the declared family:

    threshold = 1 - (1 - 0.05) ** (1 / 5) = 0.010206

Every outcome was judged against that threshold of 0.010206. No outcome was judged against 0.05.

## Results

Outcomes are reported in the declared order.

1. **Shell length increment (mm).** Sand mean 4.5624, gravel mean 5.9682. p = 0.0000498.
   Below the Sidak threshold of 0.010206: **significant**.
2. **Wet mass gain (g).** Sand mean 0.4138, gravel mean 0.5979. p = 0.0000039.
   Below the Sidak threshold of 0.010206: **significant**.
3. **Condition index (%).** Sand mean 6.4652, gravel mean 7.2561. p = 0.017153.
   Above the Sidak threshold of 0.010206: **not significant**.
4. **Foot glycogen (mg/g dry mass).** Sand mean 22.3333, gravel mean 26.4758. p = 0.015813.
   Above the Sidak threshold of 0.010206: **not significant**.
5. **Clearance rate (L/h per individual).** Sand mean 0.3732, gravel mean 0.4456. p = 0.014592.
   Above the Sidak threshold of 0.010206: **not significant**.

## Conclusion

Gravel-reared juveniles had the higher mean on all five outcomes. Two of the five, shell length
increment and wet mass gain, cleared the Sidak threshold. The other three, condition index, foot
glycogen and clearance rate, did not clear the threshold once the family of five was accounted for,
so this trial does not establish a substrate difference on them.

On the growth outcomes that did clear the threshold, coarse gravel is the better rearing substrate,
and it is what we recommend for juveniles destined for reintroduction. The condition, glycogen and
clearance results point the same way but are not established here; a larger trial would be needed
to settle them.
