# Sprout suppressant storage trial: orange oil versus spearmint oil

Six month store trial on ware potatoes of a single cultivar, assessed crate by crate against a
pre-declared family of six outcomes.

## Data

The analysis reads one file, `storage_trial.csv`, which has a header row and 60 data rows with no
blank cells.

**A single row is one individually tracked storage crate.** Each crate holds 25 kg of tubers from
the same harvest lot. The six outcome columns in that row are that crate's assessment values at the
end of storage, so the crate is both the unit of randomisation and the unit of measurement.

| Column | Units | What it holds |
| --- | --- | --- |
| `crate_id` | none | Crate label, `C01` through `C60`, unique per row. |
| `suppressant` | none | Treatment group. Exactly two values: `orange_oil` and `spearmint_oil`. |
| `sprout_length_mm` | mm | Declared outcome 1. Mean sprout length across the tubers in the crate. |
| `weight_loss_pct` | percent | Declared outcome 2. Cumulative weight loss of the crate over storage. |
| `firmness_n` | newtons | Declared outcome 3. Penetrometer firmness, crate mean. |
| `reducing_sugars_mg_per_g` | mg per g fresh weight | Declared outcome 4. Reducing sugars in the crate sample. |
| `sprouted_tubers_pct` | percent of the crate | Declared outcome 5. Share of tubers showing any sprouting. |
| `soft_rot_pct` | percent of the crate | Declared outcome 6. Share of tubers with soft rot. |

Columns 3 through 8 are the declared outcome family, in the declared order.

## Design

Sixty crates were randomly assigned to one of two sprout suppressant treatments: 30 crates to the
orange oil based suppressant and 30 crates to the spearmint oil based suppressant. All 60 crates
were then held together in the same store for six months at 8 degrees Celsius and 95 percent
relative humidity, and assessed at the end for the whole declared outcome family. Every crate has a
value for every outcome, so all six comparisons use the same 30 versus 30 split.

Each outcome was compared between the two groups with a Welch two-sample t-test, which does not
assume the two groups share a variance.

## Multiple comparison control

**All six declared outcomes were adjusted together as one family.** The complete set of six raw
p-values was passed in a single call to `pingouin.multicomp` (pingouin 0.5.5), using Holm's
step-down procedure at alpha = 0.05. Pingouin is the specialist third-party statistics package that
performed the adjustment. Holm's procedure gives strong control of the family-wise error rate over
the whole family, which is what the study protocol requires. None of the six outcomes was left out
of the adjusted set, and no outcome outside the declared family was added to it.

Every significance verdict in this report is read off the Holm-adjusted p-values. The raw p-values
are shown for transparency only and were not used to decide anything.

## Results

Difference is the orange oil group mean minus the spearmint oil group mean. Group sizes are 30 and
30 for every row.

| # | Outcome | Units | Orange oil mean | Spearmint oil mean | Difference | Raw p | Holm-adjusted p | Verdict at alpha = 0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `sprout_length_mm` | mm | 3.80 | 11.93 | -8.13 | 0.00000003 | 0.0000002 | Significant |
| 2 | `weight_loss_pct` | percent | 4.23 | 6.03 | -1.80 | 0.0000002 | 0.0000008 | Significant |
| 3 | `firmness_n` | N | 21.90 | 21.20 | +0.70 | 0.344 | 0.687 | Not significant |
| 4 | `reducing_sugars_mg_per_g` | mg/g FW | 1.47 | 1.95 | -0.47 | 0.00093 | 0.0028 | Significant |
| 5 | `sprouted_tubers_pct` | percent of crate | 10.87 | 25.54 | -14.67 | 0.0000003 | 0.0000012 | Significant |
| 6 | `soft_rot_pct` | percent of crate | 2.62 | 2.40 | +0.22 | 0.726 | 0.726 | Not significant |

Four of the six declared outcomes stay significant after the family-wise correction.

## Conclusion for each outcome

Each conclusion below follows from the Holm-adjusted p-value in the table, not from the raw one.

1. **Mean sprout length.** Adjusted p = 0.0000002. The two suppressants clearly differ. Orange oil
   crates averaged 3.80 mm of sprout against 11.93 mm under spearmint oil, so orange oil held
   sprouting back by about 8.1 mm per crate.
2. **Cumulative weight loss.** Adjusted p = 0.0000008. The two suppressants clearly differ. Orange
   oil crates lost 4.23 percent of their weight against 6.03 percent under spearmint oil, a saving
   of about 1.8 percentage points over six months.
3. **Tuber firmness.** Adjusted p = 0.687. No difference was shown. The 0.70 N gap in favour of
   orange oil is small next to the crate-to-crate spread and is not distinguishable from chance.
4. **Reducing sugars.** Adjusted p = 0.0028. The two suppressants differ. Orange oil crates ended at
   1.47 mg/g fresh weight against 1.95 mg/g under spearmint oil, about 0.47 mg/g lower.
5. **Tubers showing any sprouting.** Adjusted p = 0.0000012. The two suppressants clearly differ.
   Orange oil crates had 10.87 percent of tubers sprouting against 25.54 percent under spearmint
   oil, roughly 14.7 percentage points fewer.
6. **Soft rot incidence.** Adjusted p = 0.726. No difference was shown. The two suppressants look
   effectively the same on rot, 2.62 percent against 2.40 percent.

The correction did not change any verdict in this trial. The four significant outcomes had raw
p-values at or below 0.00093, and the two non-significant outcomes had raw p-values of 0.344 and
0.726, so nothing sat close enough to 0.05 for Holm's adjustment to flip it. That is a property of
this particular result and not a reason to skip the correction. The adjustment still has to be
applied across the whole declared family before any verdict is read, because the protocol declared
the six outcomes as one family in advance.

Two cautions on reading the table. First, these are group comparisons on crate means, and the
outcomes measured on the same crate are related to each other, so the six results are not six
independent pieces of evidence about the store. Second, "no difference was shown" for firmness and
soft rot means the trial did not detect one at 30 crates per group. It is not evidence that the two
suppressants are identical on those outcomes.

## Storage management interpretation

For this cultivar under this store regime, the orange oil suppressant is the better choice on
dormancy control. It gave shorter sprouts, a smaller share of sprouted tubers, and less weight loss
over the six months, and all three of those hold up after correcting across the full declared
family. The lower reducing sugars under orange oil also survive correction, which matters for any
lot heading to frying, since higher reducing sugars drive darker fry colour.

The two outcomes where nothing was shown are worth reading as absence of a penalty rather than as a
benefit. Orange oil did not cost firmness and did not raise soft rot, so the dormancy gain does not
appear to come with a quality or breakdown trade-off in this trial.

The practical reading for the store manager is that orange oil should be the default suppressant for
six month holding of this cultivar at 8 degrees Celsius, with the largest single gain being roughly
1.8 percentage points less shrinkage on a 25 kg crate. Firmness and rot should still be monitored as
usual, since this trial was sized to compare treatments rather than to rule out small differences on
those two outcomes.

## Software

The analysis script `analysis.py` requires:

- `pandas` (data loading)
- `scipy` (Welch two-sample t-test)
- `pingouin` (multiple comparison correction, `pingouin.multicomp`, Holm)
