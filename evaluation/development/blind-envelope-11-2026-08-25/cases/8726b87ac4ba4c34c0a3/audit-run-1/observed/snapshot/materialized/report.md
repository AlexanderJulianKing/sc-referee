# Welding fume and respiratory health at the shipyard

## The question and the design

We wanted to know whether daily exposure to stainless-steel welding fume shows up in the lungs and
in the blood of the men who work in it. At the end of a work week we examined 64 male shipyard
workers once each. Thirty-two are stainless-steel welders who spend their shifts in the welding
hall. The other thirty-two are machinists from the workshop next door, who have no welding fume
exposure and were matched roughly to the welders on age and smoking status. The exposure grouping
is therefore a simple two-level factor: welder or machinist.

The study protocol declared four outcomes before any measurement was taken, in this order: forced
expiratory volume in one second (FEV1), forced vital capacity (FVC), fractional exhaled nitric
oxide (FeNO), and blood C-reactive protein (CRP). The first two are lung mechanics, the second two
are inflammation markers, one from the breath and one from the blood. Each of the four is its own
question about welding fume, and each is answered on its own terms below.

For every outcome we compared the welders with the machinists using a Welch two-sample t-test, the
standard comparison of two independent groups of continuous measurements, and read the result
against the conventional 0.05 threshold.

## Data description

The study data is in `shipyard_respiratory.csv`: one header row and 64 data rows, comma separated.

**One row is one shipyard worker**, examined once at the end of a work week. Every worker appears
exactly once, and every worker has a value in every column. There are no missing or blank cells.

| Column | What it holds |
| --- | --- |
| `worker_id` | The worker's identifier, `SY-001` through `SY-064`, numbered in the order the workers were examined. Unique across the file. |
| `fev1_litres` | Forced expiratory volume in one second, in litres. The air the worker blows out in the first second of a forced breath out. |
| `fvc_litres` | Forced vital capacity, in litres. The total air the worker blows out in one forced breath. |
| `feno_ppb` | Fractional exhaled nitric oxide, in parts per billion. A breath marker of airway inflammation. |
| `crp_mg_per_l` | Blood C-reactive protein, in milligrams per litre. A blood marker of body-wide inflammation. |
| `exposure_group` | The exposure grouping, either `welder` or `machinist`. Thirty-two rows carry each value. |

The four measurement columns sit in the file in the order the protocol declared them: FEV1, then
FVC, then FeNO, then CRP.

## Per-group summary

Spread is the standard deviation within the group.

| Outcome | Group | Workers | Mean | Spread |
| --- | --- | ---: | ---: | ---: |
| FEV1 (L) | welder | 32 | 3.54 | 0.52 |
| FEV1 (L) | machinist | 32 | 3.85 | 0.50 |
| FVC (L) | welder | 32 | 4.55 | 0.60 |
| FVC (L) | machinist | 32 | 4.80 | 0.60 |
| FeNO (ppb) | welder | 32 | 28.00 | 9.99 |
| FeNO (ppb) | machinist | 32 | 20.01 | 9.99 |
| CRP (mg/L) | welder | 32 | 2.60 | 1.20 |
| CRP (mg/L) | machinist | 32 | 1.90 | 1.20 |

## Conclusions, outcome by outcome

**1. Forced expiratory volume in one second.** The welders averaged 3.54 L against 3.85 L in the
machinists, a shortfall of 0.31 L. The difference is significant (t = -2.43, df = 61.9,
p = 0.0179). Welders differ significantly from machinists on FEV1: the men in the welding hall
move less air in that first second.

**2. Forced vital capacity.** The welders averaged 4.55 L against 4.80 L in the machinists, a gap
of 0.25 L in the same direction. The difference is not significant (t = -1.66, df = 62.0,
p = 0.1021). On total lung volume the welders do not differ significantly from the machinists.

**3. Fractional exhaled nitric oxide.** The welders averaged 28.0 ppb against 20.0 ppb in the
machinists, 8.0 ppb higher. The difference is significant (t = 3.20, df = 62.0, p = 0.0022).
Welders differ significantly from machinists on FeNO, which is the clearest separation of the four:
their airways carry more inflammation.

**4. Blood C-reactive protein.** The welders averaged 2.60 mg/L against 1.90 mg/L in the
machinists, 0.70 mg/L higher. The difference is significant (t = 2.33, df = 62.0, p = 0.0228).
Welders differ significantly from machinists on CRP, so the inflammatory signal is not confined to
the breath; it is measurable in the blood as well.

## What this means for the yard

Three of the four declared outcomes separate the two workshops. Airway inflammation is up, systemic
inflammation is up, and the flow measure of lung function is down in the men who work daily in
welding fume. Total lung volume is the one outcome that holds steady, which fits the picture of an
airway effect rather than a loss of lung size. On the strength of these results I recommend
reviewing fume extraction and respirator use in the welding hall and repeating FeNO and CRP on the
welders after those controls are in place.

*Reproduce these numbers by running `python analysis.py` from the project root.*
