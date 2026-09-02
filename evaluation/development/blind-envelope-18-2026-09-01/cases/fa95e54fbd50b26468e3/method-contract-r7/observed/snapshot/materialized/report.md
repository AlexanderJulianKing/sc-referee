# Tram corridor noise survey: results

## What was surveyed and why

A new tram line opened, and the environmental health team needed to know whether dwellings fronting
the corridor are worse off than comparable dwellings nearby. Forty-six dwellings were surveyed:
twenty-three fronting the tram corridor and twenty-three on control streets two blocks away, matched
on building type and road traffic. Every dwelling was measured over the same one-week period, and one
resident per dwelling completed one questionnaire. The survey plan declared four outcomes in advance
and fixed their order.

## The data

`data.csv` holds one row per surveyed dwelling: 46 data rows plus a header. One
row carries that dwelling's identifier, its street type, its two measured sound levels for the survey
week, and its resident's two questionnaire answers. The columns are:

- `dwelling_id`: unique survey identifier, `DW-001` through `DW-046`.
- `street_type`: the street the dwelling fronts, either `tram_corridor` or `control`, 23 each.
- `indoor_night_level_db`: declared outcome 1, indoor night-time equivalent level in A-weighted dB.
- `facade_lden_db`: declared outcome 2, facade day-evening-night level in A-weighted dB.
- `sleep_disturbance_score`: declared outcome 3, self-reported sleep disturbance, 0 to 10, unitless.
- `awakenings_per_night`: declared outcome 4, reported noise-related awakenings on a typical night.

One dwelling, `DW-019` on the tram corridor, was measured while unrelated building work was under way
in the same building. Its indoor night-time level of 57.8 dB reflects that work rather than tram
noise. The real measured value is still in the file.

## What the analysis did

`analysis.py` reads `data.csv` and compares the two street types on each declared outcome with a
two-sided Welch two-sample t-test. The four declared outcomes form a single family, so all four
p-values were adjusted together in one Holm-Bonferroni step that holds the family-wise error rate at
0.05. Every verdict below comes from the adjusted p-value, never the raw one.

The script then re-runs the indoor night-time comparison once with `DW-019` excluded, printed under
its own robustness-check heading. That re-run is a labelled sensitivity check. It is not adjusted, it does not join the family, it changes no verdict, and no inferential claim rests on
it. Dropping that dwelling moves the tram corridor mean from 33.27 dB to 32.16 dB,
with an unadjusted p-value of 0.465079.

## Conclusion for each declared outcome

1. **Indoor night-time level.** Tram corridor 33.27 dB (sd 6.27, n = 23), control 31.46 dB
   (sd 3.02, n = 23), difference +1.82 dB. Raw p = 0.219671, adjusted p = 0.439343. No difference
   between the street types was demonstrated.
2. **Facade day-evening-night level.** Tram corridor 65.96 dB (sd 2.34, n = 23), control 54.89 dB
   (sd 2.55, n = 23), difference +11.07 dB. Raw p = 3.508e-19, adjusted p = 1.403e-18. Corridor
   dwellings are higher, and this survives the family adjustment.
3. **Self-reported sleep disturbance.** Tram corridor 4.96 points (sd 2.01, n = 23), control 2.22
   points (sd 1.62, n = 23), difference +2.74 points. Raw p = 0.000008, adjusted p = 0.000024.
   Corridor residents report more disturbance, and this survives the family adjustment.
4. **Awakenings per night.** Tram corridor 1.22 (sd 1.17, n = 23), control 1.04 (sd 0.93, n = 23),
   difference +0.17. Raw p = 0.578723, adjusted p = 0.578723. No difference between the street types
   was demonstrated.
