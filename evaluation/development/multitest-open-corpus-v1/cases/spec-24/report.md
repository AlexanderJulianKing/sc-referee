# Antibiotic-free broiler production

One hundred and forty birds were reared on one farm through a single 42-day cycle, 70 on a
conventional programme including in-feed antibiotics and 70 on an antibiotic-free programme
with the same base diet. Six production outcomes were compared between programmes with
two-sample t-tests. The six raw p-values were kept in outcome order and passed as one list to
`statsmodels.stats.multitest.multipletests` with the default method and a family-wide error
rate of 0.05.

The default method that statsmodels applied is **Holm-Sidak** (`method='hs'`), a step-down
procedure. All six outcomes were corrected as a single family. An outcome is called different
between programmes only where the routine returned a rejection.

| Outcome | Conventional | Antibiotic-free | Raw p | Adjusted p | Decision |
|---|---:|---:|---:|---:|---|
| Final weight, day 42 (g) | 2685.0 | 2589.9 | 0.047 | 0.174 | no difference |
| Feed conversion ratio | 1.580 | 1.641 | 0.0045 | 0.027 | different |
| Breast yield (% carcass) | 22.40 | 21.90 | 0.109 | 0.205 | no difference |
| Footpad lesion score (0-4) | 0.86 | 1.16 | 0.053 | 0.174 | no difference |
| Caecal Campylobacter (log10 CFU/g) | 5.10 | 5.60 | 0.019 | 0.093 | no difference |
| Mortality day | 40.8 | 41.2 | 0.587 | 0.587 | no difference |

For reference, the routine also reported a single-step Sidak alpha of 0.0085 and a
Bonferroni alpha of 0.0083 for this family.

## Production implications

One outcome is different between programmes: feed conversion. Birds on the antibiotic-free
programme needed 1.641 units of feed per unit of gain against 1.580 on the conventional
programme, a penalty of 0.061, or about 3.9 percent. On a flock of this size that is the
difference that shows up directly in feed cost, which is the largest single input in broiler
production.

Three outcomes moved in the direction that concerns producers but do not survive correction.
Final weight was 95 g lower, footpad lesion scores were 0.30 points higher, and caecal
Campylobacter was 0.5 log10 CFU/g higher on the antibiotic-free programme. The raw p-values
for all three fall between 0.019 and 0.053, so each would have been called significant, or
nearly so, had it been tested alone. Reading them as established findings from this trial
would not be supported. The Campylobacter result deserves particular attention in follow-up
work, since half a log10 is a food safety quantity rather than a production one, and this
single-cycle single-farm design is not well placed to settle it.

Breast yield and mortality day showed no meaningful difference. The overall picture is that
removing in-feed antibiotics cost feed efficiency, with several other outcomes trending
unfavourably at a size this trial cannot confirm.
