# Wholegrain rye bread versus refined wheat bread: an eight-week parallel-group feeding study

## Study

A human nutrition unit ran an eight-week parallel-group feeding study comparing a
wholegrain rye bread with a refined wheat bread at the same daily portion. Fifty-eight
healthy adults took part: 29 were allocated to the rye bread and 29 to the refined
wheat bread. All other foods were left to the participants' usual habits. Every
participant completed a measurement week at the end of the eight weeks and contributes
one set of end-of-study values. The participant is the unit of the study.

The protocol declared five outcomes, in this fixed order, measured on every
participant: stool frequency, whole-gut transit time, fasting LDL cholesterol, fasting
insulin and faecal butyrate concentration.

## Data description

The analysis reads a single table, `bread_study_data.csv`. **One row is one
participant**, holding that person's end-of-study values from the measurement week at
the end of the eight weeks. Each participant appears exactly once. The file has 58 data
rows plus a header row, and no cell is blank.

| # | Column | What it holds | Unit |
| --- | --- | --- | --- |
| 1 | `participant_id` | Participant identifier, `P01` to `P58`, unique in the file | none (text label) |
| 2 | `group` | The bread eaten for the eight weeks. Exactly two entries appear: `rye` (wholegrain rye bread) and `refined_wheat` (refined wheat bread) | none (text label) |
| 3 | `stool_freq_per_week` | Stool frequency during the measurement week | bowel movements per week |
| 4 | `transit_time_h` | Whole-gut transit time from the swallowed marker study | hours |
| 5 | `ldl_mmol_l` | Fasting low-density lipoprotein cholesterol | millimoles per litre |
| 6 | `insulin_pmol_l` | Fasting insulin | picomoles per litre |
| 7 | `butyrate_mmol_kg` | Faecal butyrate concentration | millimoles per kilogram of wet faeces |

Columns 3 to 7 are the five protocol outcomes, and they appear in the file in the order
the protocol declares them.

## Statistical analysis

Each declared outcome was compared between the two bread groups with a standard
two-sample t-test on the participant values (29 per group), and the raw p-value was
kept.

**The five outcomes were declared as one outcome family, so they were adjusted
together, not judged one at a time.** All five raw p-values were passed in a single
call to the multiple-comparisons routine of the statsmodels library
(`statsmodels.stats.multitest.multipletests`) with no method argument, so the library's
own default correction was applied; that default is the method statsmodels labels
`'hs'`. Every significance verdict below comes from the adjusted p-values the routine
returned, judged at the conventional five percent threshold. The raw p-values are shown
for information only and are not the basis of any verdict.

## Results

Results for all five declared outcomes, in the declared order. Means are group means of
the end-of-study values.

| # | Outcome (unit) | Mean, rye (n=29) | Mean, refined wheat (n=29) | Raw p | Adjusted p | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Stool frequency (per week) | 9.92 | 7.50 | 0.0001 | 0.0005 | Significant |
| 2 | Whole-gut transit time (h) | 38.77 | 47.07 | 0.0013 | 0.0051 | Significant |
| 3 | Fasting LDL cholesterol (mmol/L) | 3.15 | 3.13 | 0.9427 | 0.9619 | Not significant |
| 4 | Fasting insulin (pmol/L) | 60.66 | 59.54 | 0.8047 | 0.9619 | Not significant |
| 5 | Faecal butyrate (mmol/kg wet faeces) | 15.09 | 11.99 | 0.0027 | 0.0082 | Significant |

Outcome by outcome:

1. **Stool frequency.** Rye 9.92 versus refined wheat 7.50 bowel movements per week, a
   difference of +2.42 in favour of rye. Raw p = 0.0001, adjusted p = 0.0005:
   significant.
2. **Whole-gut transit time.** Rye 38.77 h versus refined wheat 47.07 h, a difference of
   -8.30 h, that is, faster transit on rye. Raw p = 0.0013, adjusted p = 0.0051:
   significant.
3. **Fasting LDL cholesterol.** Rye 3.15 mmol/L versus refined wheat 3.13 mmol/L, a
   difference of +0.01 mmol/L. Raw p = 0.9427, adjusted p = 0.9619: not significant.
4. **Fasting insulin.** Rye 60.66 pmol/L versus refined wheat 59.54 pmol/L, a difference
   of +1.11 pmol/L. Raw p = 0.8047, adjusted p = 0.9619: not significant.
5. **Faecal butyrate.** Rye 15.09 mmol/kg versus refined wheat 11.99 mmol/kg, a
   difference of +3.10 mmol/kg. Raw p = 0.0027, adjusted p = 0.0082: significant.

## Conclusion

Over eight weeks at a matched daily portion, the wholegrain rye bread changed gut
function. Compared with the refined wheat bread, participants on rye passed stools
about 2.4 more times per week, moved material through the gut about 8 hours faster, and
had faecal butyrate about 3.1 mmol/kg higher. All three differences survived adjustment
across the declared family of five outcomes.

The rye bread did not change the two fasting blood markers. Group means for LDL
cholesterol and insulin were within about 0.01 mmol/L and 1.1 pmol/L of each other, and
neither approached significance before or after adjustment. On this evidence the benefit
of the rye bread in these healthy adults sits in bowel function and colonic fermentation
rather than in lipid or glycaemic control.

Two limits are worth stating. This is a parallel-group comparison of end-of-study values
only, with no baseline values in the table, so the comparison rests on the groups being
comparable at the start. Diet outside the study bread was left to usual habits and was
not recorded, so it is not controlled for here.

## Reproducing

From this directory:

```
python analysis.py
```

The script reads `bread_study_data.csv` and prints the table above.
