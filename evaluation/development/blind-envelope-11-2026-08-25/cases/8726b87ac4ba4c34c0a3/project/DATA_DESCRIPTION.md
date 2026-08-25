# Data description

## Files

### `shipyard_respiratory.csv`

The study data. 64 data rows plus one header row, comma separated, UTF-8.

One row is one shipyard worker, examined once at the end of a work week. Every worker appears
exactly once, and every worker has a value in every column: there are no missing or blank cells.
Thirty-two of the workers are stainless-steel welders from the welding hall and thirty-two are
machinists from the adjacent workshop, who have no welding fume exposure and were matched roughly
on age and smoking status.

Columns, in file order:

| Column | Type | Description |
| --- | --- | --- |
| `worker_id` | text | Identifier for the worker, in the form `SY-001` through `SY-064`. Numbered in the order the workers were examined, so the two workshops are interleaved. Unique across the file. |
| `fev1_litres` | number, 2 decimals | Forced expiratory volume in one second, in litres. The air the worker can blow out in the first second of a forced breath out. Range in this file 2.53 to 5.34. |
| `fvc_litres` | number, 2 decimals | Forced vital capacity, in litres. The total air the worker can blow out in one forced breath. Always at least as large as `fev1_litres` for the same worker. Range in this file 2.70 to 6.60. |
| `feno_ppb` | number, 1 decimal | Fractional exhaled nitric oxide, in parts per billion. A breath marker of airway inflammation. Right-skewed: most values are moderate and a few are much higher. Range in this file 6.9 to 57.4. |
| `crp_mg_per_l` | number, 2 decimals | Blood C-reactive protein, in milligrams per litre. A blood marker of body-wide inflammation. Also right-skewed. Range in this file 0.40 to 6.14. |
| `exposure_group` | text | The exposure grouping, with exactly two distinct values: `welder` (stainless-steel welder, exposed to welding fume) or `machinist` (unexposed comparison worker). Thirty-two rows carry each value. |

The four measurement columns appear in the order the study protocol declared them: FEV1, then FVC,
then FeNO, then CRP.

## How the file was made

### `make_data.py`

The generator that writes `shipyard_respiratory.csv`. It is seeded (`SEED = 20260825`) and
deterministic, so rerunning it reproduces the same CSV byte for byte:

```
/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/.venv/bin/python make_data.py
```

The values are synthetic. Each group's outcomes are drawn around the levels and spreads the study
describes, then rounded the way the instruments report them. The two spirometry columns are drawn
as a correlated pair, because both come from the same chest, and each worker's FEV1 is held inside
a sensible fraction of that same worker's FVC. The two inflammation markers are drawn on a log
scale, which gives them the long right tail these markers have in real blood and breath samples.
