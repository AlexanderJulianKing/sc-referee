# Condition of roe deer yearlings in two neighbouring hunting districts

## Data

The analysis uses `deer_condition.csv`, which holds condition measurements from
one autumn cull of roe deer yearlings. **One row is one deer**: a single animal,
weighed and sampled once at the game larder, with the same set of measurements
taken on every animal. No animal appears twice and there are no follow-up
visits. The file has a header row and 96 data rows, and every cell is filled.

| # | Column | Units | What it holds |
|---|--------|-------|---------------|
| 1 | `deer_id` | none | Animal identifier, `RD-001` to `RD-096`, in larder processing order. |
| 2 | `district` | none | Group label, either `north` or `south`. |
| 3 | `carcass_mass_kg` | kg | Dressed carcass mass, to 0.1 kg. |
| 4 | `kidney_fat_index` | ratio | Perirenal fat mass divided by trimmed kidney mass, to two decimals. |
| 5 | `back_fat_mm` | mm | Subcutaneous back fat depth at the rump, to 0.1 mm; `0.0` means no measurable layer. |
| 6 | `jaw_length_mm` | mm | Lower jaw (mandible) length, to 0.1 mm. |
| 7 | `haemoglobin_g_per_dl` | g/dL | Blood haemoglobin concentration, to 0.1 g/dL. |
| 8 | `serum_urea_mmol_per_l` | mmol/L | Serum urea concentration, to 0.1 mmol/L. |
| 9 | `faecal_egg_count_epg` | eggs per gram | Faecal strongyle egg count, McMaster method, whole numbers in steps of 25. |

Columns 3 to 9 are the seven condition outcomes the agency declared before the
season, and the file lists them in that declared order.

## Design

Two hunting districts are compared, side by side, in the same autumn cull.
Ninety-six yearlings were sampled: **48 from the northern district and 48 from
the southern district**. The districts are separate sets of animals, so each
outcome is compared with a two-sample test between the two groups.

Six outcomes (carcass mass, kidney fat index, back fat, jaw length,
haemoglobin, serum urea) are continuous measurements and are compared with
Welch's two-sample t-test. Welch's version does not assume the two districts
have the same spread. The seventh outcome, the faecal egg count, is a
right-skewed count with many low values and a few very high ones, so it is
compared with the Mann-Whitney U test, which ranks the animals instead of
relying on their averages.

An outcome is declared significantly different between the districts when its
p-value falls below 0.05.

## Results

Group means and p-values for the seven declared outcomes, in declared order.
The difference column is the northern mean minus the southern mean.

| # | Outcome | North mean | South mean | Difference | p-value | Test |
|---|---------|-----------:|-----------:|-----------:|--------:|------|
| 1 | Dressed carcass mass (kg) | 16.606 | 14.904 | +1.702 | <0.001 | Welch t-test |
| 2 | Kidney fat index (ratio) | 1.571 | 1.212 | +0.358 | <0.001 | Welch t-test |
| 3 | Back fat depth at rump (mm) | 5.404 | 5.321 | +0.083 | 0.868 | Welch t-test |
| 4 | Lower jaw length (mm) | 150.748 | 149.167 | +1.581 | 0.047 | Welch t-test |
| 5 | Blood haemoglobin (g/dL) | 14.048 | 13.927 | +0.121 | 0.620 | Welch t-test |
| 6 | Serum urea (mmol/L) | 5.354 | 6.054 | -0.700 | 0.004 | Welch t-test |
| 7 | Faecal strongyle egg count (epg) | 96.354 | 228.125 | -131.771 | <0.001 | Mann-Whitney U |

Exact p-values for the three smallest: carcass mass 0.0000063, kidney fat index
0.000072, faecal egg count 0.00000035. For the egg count the medians are 75 epg
in the north and 175 epg in the south, which is the comparison the rank test
actually rests on; the means are shown for consistency with the other rows.

## Conclusion for each outcome

1. **Dressed carcass mass** (p < 0.001): significantly different. Northern
   yearlings are heavier by about 1.7 kg on average.
2. **Kidney fat index** (p < 0.001): significantly different. Northern
   yearlings carry more perirenal fat, by about 0.36 index units.
3. **Back fat depth at the rump** (p = 0.868): not significantly different. The
   two districts are effectively the same, a gap of less than 0.1 mm.
4. **Lower jaw length** (p = 0.047): significantly different, but only just.
   The p-value sits a hair under the 0.05 threshold, and the gap is about
   1.6 mm.
5. **Blood haemoglobin** (p = 0.620): not significantly different. The means
   differ by about 0.12 g/dL.
6. **Serum urea** (p = 0.004): significantly different. Southern yearlings run
   about 0.7 mmol/L higher.
7. **Faecal strongyle egg count** (p < 0.001): significantly different.
   Southern yearlings shed far more strongyle eggs, with a median of 175 epg
   against 75 epg in the north.

Five of the seven declared outcomes came out significantly different at the
0.05 threshold; two did not.

## Management interpretation

The picture that comes out of these seven measures is a southern district whose
yearlings are in poorer shape. They are lighter, they carry less kidney fat,
their serum urea is higher, which fits animals drawing on their own tissue
rather than feeding well, and they carry a heavier strongyle worm burden. Those
four signals point the same way, and the worm burden is the one a manager can
act on directly.

Two measures do not separate the districts. Rump back fat is essentially
identical, and haemoglobin is close enough to call the same. Back fat at the
rump is a coarse measure in autumn yearlings, so its silence here does not
undercut the kidney fat result; it is the less sensitive of the two fat
measures.

Jaw length is the one to treat carefully. It cleared the threshold, but barely,
at p = 0.047. Jaw length reflects growth over the animal's whole life rather
than this season's feeding, so a real 1.6 mm gap would suggest the southern
shortfall is not new. On this season's sample alone the result is too close to
the line to build a decision on, and it is worth re-measuring next season.

Suggested next steps for the agency: run faecal sampling and a targeted
anthelmintic review in the southern district, check southern winter feed
availability and browse pressure against the northern district, and keep the
same seven measures on the next cull so the marginal jaw length result can be
checked against a second season.
