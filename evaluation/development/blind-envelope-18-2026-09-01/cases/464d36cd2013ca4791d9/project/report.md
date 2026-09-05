# Post-operative analgesia after elective ovariohysterectomy in dogs

## What was compared, and why

Sixty-four healthy adult bitches were enrolled after routine elective ovariohysterectomy and
recovered on one of two post-operative analgesia protocols, thirty-two dogs on each. Protocol A was
a systemic opioid alone. Protocol B added a local incisional block to that same opioid. The
practical question was whether the added block buys a calmer, more comfortable first day for the
patient. Every dog recovered in the same ward and was assessed by the same nursing team, so the
analgesia protocol is the difference we are reading. The study protocol declared seven outcomes in
advance and named the first two of them as primary.

## The data

`data.csv` holds 64 data rows plus a header. One row is one dog: its identifier, the protocol it
was recovered on, and its value for each declared outcome. No values are missing. The columns are
`dog_id` (identifier, D01 to D64), `protocol` (`A` or `B`), `pain_score_6h` (composite behavioural
pain score at 6 hours, on a 0 to 24 clinical scale), `rescue_analgesia_24h_mg` (rescue analgesia
given in the first 24 hours, in milligrams), `serum_cortisol_6h_ug_dl` (serum cortisol at 6 hours,
in micrograms per decilitre), `heart_rate_6h_bpm` (heart rate at 6 hours, in beats per minute),
`respiratory_rate_6h_brpm` (respiratory rate at 6 hours, in breaths per minute),
`food_intake_24h_g` (food eaten in the first 24 hours, in grams), and `rectal_temperature_6h_c`
(rectal temperature at 6 hours, in degrees Celsius).

## What the analysis did

`analysis.py` reads `data.csv` and compares the two protocols on each of the seven outcomes with a
two-sample t-test, 32 dogs against 32. The two primary p-values, for pain score and for rescue
analgesia, were then passed together through the Holm procedure in `statsmodels`
(`multipletests`), and those two outcomes were judged at the 0.05 threshold on the adjusted values
the routine returned. The five other declared outcomes were each judged at the 0.05 threshold on
their own unadjusted p-value. For every outcome the script prints the group sizes, the group means
and standard deviations, the p-value used for the verdict, and the verdict.

## Results, in the declared order

1. **Pain score at 6 hours.** A 8.12 (SD 2.04), B 5.38 (SD 1.74). Holm-adjusted p = 4.8e-07.
   Protocol B scored 2.75 points lower, a clear difference.
2. **Rescue analgesia in 24 hours.** A 1.95 mg (SD 2.23), B 1.35 mg (SD 1.76). Holm-adjusted
   p = 0.2369. No difference at the 0.05 threshold.
3. **Serum cortisol at 6 hours.** A 7.11 ug/dL (SD 1.90), B 6.41 ug/dL (SD 1.94). p = 0.1479. No
   difference.
4. **Heart rate at 6 hours.** A 106.06 bpm (SD 13.99), B 100.88 bpm (SD 12.30). p = 0.1202. No
   difference.
5. **Respiratory rate at 6 hours.** A 24.41 brpm (SD 6.44), B 26.56 brpm (SD 5.17). p = 0.1447. No
   difference.
6. **Food intake in 24 hours.** A 135.38 g (SD 65.00), B 236.59 g (SD 59.05). p = 1.4e-08. Dogs on
   protocol B ate about 101 g more, a clear difference.
7. **Rectal temperature at 6 hours.** A 38.49 C (SD 0.33), B 38.40 C (SD 0.30). p = 0.2356. No
   difference.

Adding the local incisional block lowered the 6-hour pain score and raised first-day food intake.
The other five declared outcomes landed close between the two protocols.
