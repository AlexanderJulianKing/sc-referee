# Vessel-noise playback and ventilation in shore crabs

## Design

Twelve shore crabs (Carcinus maenas) were each held in a separate flow-through
chamber and run through four playback sessions on consecutive days: two quiet
control sessions and two vessel-noise sessions, with the starting condition
alternated between animals. Scaphognathite beat rate (ventilation, beats per
minute) was counted over the final minute of each session. The stored table is
long format: 48 rows, one row per crab per session.

## Analysis

Sessions repeat on the same animal and are not independent of one another, so the
two quiet sessions and the two noise sessions of each crab were averaged first.
That leaves one quiet mean and one noise mean per crab, and the noise-minus-quiet
contrast was formed within crab. The reported test uses 12 paired values, one per
crab, so the independent units and the analysed rows coincide.

## Crab-level means (beats per minute)

| crab_id | quiet | vessel noise | difference |
| --- | --- | --- | --- |
| CM-01 | 63.50 | 72.00 | +8.50 |
| CM-02 | 59.00 | 65.00 | +6.00 |
| CM-03 | 70.50 | 82.00 | +11.50 |
| CM-04 | 66.50 | 71.00 | +4.50 |
| CM-05 | 55.50 | 64.50 | +9.00 |
| CM-06 | 70.50 | 83.50 | +13.00 |
| CM-07 | 60.50 | 63.00 | +2.50 |
| CM-08 | 65.00 | 72.00 | +7.00 |
| CM-09 | 57.50 | 67.50 | +10.00 |
| CM-10 | 73.50 | 79.00 | +5.50 |
| CM-11 | 61.50 | 73.50 | +12.00 |
| CM-12 | 67.50 | 74.00 | +6.50 |

## Result

Averaged over animals, ventilation was 64.25 beats/min under quiet playback and
72.25 beats/min under vessel noise. The within-crab increase averaged
8.00 beats/min (SD 3.23).

[selected-result] Paired t-test on crab-level mean ventilation (n = 12 crabs, one paired value per crab): vessel-noise playback increased ventilation by 8.00 beats/min (95% CI 5.95 to 10.05), t(11) = 8.5896, p < 0.001, dz = 2.48.

A distribution-free check agrees: the two-sided signed-rank statistic on the same 12
crab-level differences is W = 0.0, with all 12 differences positive.
Because the repeated sessions were collapsed within animal before testing, the
degrees of freedom track the 12 crabs (df = 11) rather than the 48 stored session
rows.
