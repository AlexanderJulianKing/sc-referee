# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (seed `20260825`, NumPy). Running it recreates `donor_biomarkers.csv` exactly. |
| `donor_biomarkers.csv` | The study data file: 120 data rows plus one header row. |

## `donor_biomarkers.csv`

One row per blood donor. Each row holds the single donation-session sample for
that donor: the five protocol-declared biomarker values measured on that sample,
the donor's smoking status, and the study half the donor was assigned to before
any measurement was made. Every donor appears exactly once, and no cell is
missing.

Columns, in file order:

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `donor_id` | text | none | Donor identifier, `BD001` through `BD120`. Unique across rows. |
| `crp_mg_l` | number, 2 decimals | mg/L | Plasma C-reactive protein. Declared outcome 1. |
| `wbc_count_10e9_per_l` | number, 1 decimal | 10^9 cells/L | White blood cell count. Declared outcome 2. |
| `fibrinogen_g_l` | number, 2 decimals | g/L | Plasma fibrinogen. Declared outcome 3. |
| `hdl_cholesterol_mmol_l` | number, 2 decimals | mmol/L | HDL cholesterol. Declared outcome 4. |
| `vitamin_c_umol_l` | number, 1 decimal | umol/L | Serum vitamin C. Declared outcome 5. |
| `smoking_status` | text | none | Grouping factor, exactly two values: `smoker` (current daily cigarette smoker) or `never_smoker`. |
| `study_stage` | text | none | The fixed pre-measurement split, exactly two values: `discovery` or `validation`. |

The five outcome columns appear in the declared protocol order (C-reactive
protein, white blood cell count, fibrinogen, HDL cholesterol, vitamin C).

## Cohort composition

| | discovery | validation | total |
| --- | --- | --- | --- |
| `smoker` | 30 | 30 | 60 |
| `never_smoker` | 30 | 30 | 60 |
| total | 60 | 60 | 120 |

Rows are stored in donor-identifier order; the smoking groups and the two halves
are interleaved rather than blocked.

## How the values were produced

`make_data.py` draws each outcome from a fixed distribution that depends only on
smoking status, never on the half, so the discovery and validation halves are
drawn from the same populations.

- C-reactive protein is drawn from a lognormal distribution, matching the
  right-skewed shape of real CRP panels, with group means near 2.4 mg/L
  (smokers) and 1.5 mg/L (never-smokers) and a spread near 1.1 mg/L.
- The other four outcomes are drawn from normal distributions at the levels and
  spreads listed below.
- Every draw is clipped to a physiologically sane range, so no value is negative
  or absurd, and then rounded to the number of decimals a laboratory report
  would carry.

Target group levels used by the generator:

| Outcome | Smokers | Never-smokers | Spread |
| --- | --- | --- | --- |
| `crp_mg_l` | 2.40 | 1.50 | 1.10 |
| `wbc_count_10e9_per_l` | 7.80 | 6.50 | ~1.5 |
| `fibrinogen_g_l` | 3.34 | 3.10 | ~0.5 |
| `hdl_cholesterol_mmol_l` | 1.29 | 1.41 | 0.30 |
| `vitamin_c_umol_l` | 42.0 | 55.0 | ~14 |

The realised separation between the two smoking groups therefore varies by
outcome: some outcomes separate clearly, and fibrinogen and HDL cholesterol
differ only slightly.
