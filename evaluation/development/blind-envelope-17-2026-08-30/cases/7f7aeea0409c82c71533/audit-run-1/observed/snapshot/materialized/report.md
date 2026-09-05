# Fish presence in the larval pond and the condition of newly emerged damselflies

## Question and design

Does the presence of fish in a pond go with a difference in the condition of the adult
damselflies that emerge from it? Seventy adult male blue-tailed damselflies were hand-netted
within two days of emergence: 35 at fish-free ponds (ponds holding no fish) and 35 at
fish-stocked ponds. All ponds lie in one lowland landscape and were sampled in the same
fortnight. The two pond types are the only comparison in the study. Each damselfly is one
subject, measured individually in the laboratory on the day of capture.

## Data

File: `damselfly_condition.csv`, 70 data rows and one header row. **One row is one adult male
damselfly.** No insect appears twice, and every insect has a value in every column, so there are
no missing cells.

Columns:

| Column | Meaning |
| --- | --- |
| `specimen_id` | Unique specimen identifier, prefix `dam` plus a zero-padded serial number in capture order. |
| `pond_type` | Group column, exactly two values: `fish_free` (pond holding no fish) and `fish` (pond stocked with fish). |
| `body_length_mm` | Total body length in millimetres, digital callipers, 0.1 mm. |
| `hindwing_length_mm` | Hind-wing length in millimetres, digital callipers, 0.1 mm. |
| `abdominal_fat_mg` | Abdominal fat content in milligrams, dry mass of the extracted fat body, 0.01 mg. |
| `mite_count` | Ectoparasitic water-mite load, whole mites counted on the individual. |
| `encapsulation_grey` | Immune encapsulation response to a nylon implant, 8-bit greyscale darkness value, 0-255. Higher is a stronger response. |

The five outcome columns appear in the order fixed by the field protocol before sampling:
body length, hind-wing length, abdominal fat, mite load, encapsulation response.

## How the comparison was done

The five outcomes were declared in the field protocol as **one outcome family**, so the error
rate is controlled across the complete family rather than outcome by outcome.

Each outcome was compared between the two pond types with a two-sample t-test, and the five
p-values were kept together in the declared order. All five were then adjusted in a single call,
as one complete family, with the Holm step-down method from **pingouin** (`pingouin.multicomp`,
version 0.5.5), a specialist Python statistics package used here for the multiple-comparison
correction. Holm gives strong control of the family-wise error rate.

Every verdict below was read only from the adjusted p-value, at the conventional 0.05 threshold.
No outcome was called from an unadjusted p-value. The analysis is in `analysis.py`.

## Results

In the declared order (means are group means; p is the family-adjusted p-value):

1. **Total body length (mm).** Fish-free 30.186, fish 29.574. Adjusted p = 0.0789.
   **Not significant.**
2. **Hind-wing length (mm).** Fish-free 16.714, fish 16.334. Adjusted p = 0.0750.
   **Not significant.**
3. **Abdominal fat (mg).** Fish-free 1.413, fish 1.062. Adjusted p = 0.0002.
   **Significant.**
4. **Water-mite load (mites).** Fish-free 2.914, fish 4.514. Adjusted p = 0.0104.
   **Significant.**
5. **Encapsulation response (greyscale).** Fish-free 130.600, fish 114.629. Adjusted p = 0.0283.
   **Significant.**

Hind-wing length had an unadjusted p of 0.0375, which would have cleared 0.05 on its own, but it
does not clear the threshold once the complete family of five is accounted for, so it is reported
as not significant.

## Conclusion

Adults emerging from fish-stocked ponds carried less abdominal fat, more ectoparasitic water
mites, and mounted a weaker immune encapsulation response than adults from fish-free ponds.
The two size measures, body length and hind-wing length, ran in the same direction but did not
separate the groups once the whole declared family was corrected together. Fish presence in the
larval pond is therefore associated with poorer adult condition in the energetic, parasite, and
immune measures, while overall adult size looks much the same. This is an observational field
comparison of ponds, not an experiment, so it shows an association and does not establish that
fish cause the difference.
