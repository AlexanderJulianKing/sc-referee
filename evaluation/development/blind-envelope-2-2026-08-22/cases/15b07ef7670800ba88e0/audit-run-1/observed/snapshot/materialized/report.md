# Maternal protein restriction during gestation and rat pup body mass at weaning

## Background

Protein supplied to the dam during gestation is the raw material for fetal tissue accretion, and the
fetus has no independent source of amino acids. When dietary protein is restricted, placental
transfer of amino acids falls, fetal insulin and insulin-like growth factor 1 signalling is
downregulated, and the growth trajectory of the fetus is reset downward. That reset is not confined
to the prenatal window. Pups born small from a protein-restricted dam typically start suckling with
less lean mass and a smaller gut and liver, and the same dam is often less able to sustain milk
output, so the deficit acquired in utero tends to persist or widen across the suckling period rather
than close. Body mass at postnatal day 21, the conventional weaning point in the rat, is therefore a
sensitive summary of how well the prenatal protein supply and the ensuing lactational environment
supported growth. The question addressed here is whether gestational protein restriction lowers pup
body mass at that timepoint.

## Design

Sixteen dams were fed one of two diets throughout gestation: eight received the control diet and
eight received the protein-restricted diet. Each dam produced one litter. Every litter was culled to
eight pups on postnatal day 2, and all eight of those pups were weighed on postnatal day 21, giving
128 weighed pups in total.

The diet was fed to the dam, not to the pup. A pup could not be assigned to a diet independently of
its littermates: the treatment arrived through the dam, and the eight pups in a litter also share
parents and a single nursing environment. The litter is therefore the unit that was randomised and
the unit that can be treated as independent. Consequently the analysis reduced each litter to one
number before any group comparison, and the sample size reported below counts litters, not pups.

### Note on data provenance

The values in `pup_masses.csv` are simulated by `make_data.py` from a two-level model with a known
group difference, a litter-level random shift and pup-level noise. They illustrate the design and
the analysis. They are not measurements from real animals and carry no evidence about real rats. The
biological interpretation below should be read as the interpretation such a result would carry, not
as a finding.

## Data description

The project contains one data file, `pup_masses.csv`. It holds the raw pup-level records.

**A single row is one weaned rat pup, weighed once on postnatal day 21.** A row is not a litter.
Because every litter was culled to eight pups and all eight were weighed, **each litter contributes
eight rows** and its `litter_id` value repeats eight times. The file has 128 data rows plus one
header row, and there are no missing values.

The file has exactly five columns, in this order.

| Column | Type | What it holds |
| --- | --- | --- |
| `litter_id` | string | The litter, equivalently the dam, since each dam produced one litter. Values `L01` through `L16`, each appearing 8 times. This is the clustering variable and the label of the experimental unit. |
| `diet_group` | string | Maternal diet during gestation: `control` or `protein_restricted`. A property of the dam, so it is constant across all 8 rows of a litter. `L01`–`L08` are control, `L09`–`L16` are protein-restricted. |
| `pup_id` | string | The pup's identifier within its litter, written as the litter label, a hyphen, then `P1` to `P8`, for example `L03-P5`. Because the litter label is embedded, all 128 values are distinct. It is a label only; the trailing digit is an arbitrary index and encodes no birth order or ranking. |
| `sex` | string | `F` or `M`. Each litter holds exactly 4 females and 4 males, so the file holds 64 of each. |
| `body_mass_g` | number | The outcome: the pup's body mass in grams on postnatal day 21, rounded to one decimal place. One measurement per pup. Observed range in this file: 31.5 g to 60.0 g. |

There is no second, pre-summarised file on disk. The litter averages used for testing are formed by
`analysis.py` from these raw rows each time it runs.

## Analysis

`analysis.py` reads `pup_masses.csv`, averages the eight day-21 body masses within each `litter_id`
to give one value per litter, and compares the eight control litter averages against the eight
protein-restricted litter averages with an independent two-sample Welch t-test. Welch's version was
used rather than the pooled-variance version because it does not require the two groups to share a
variance, and it costs little when they do. The reported sample size is the number of litters.

## Results

The 128 pup records describe how many animals were weighed. They are not the sample size of the
comparison. The comparison used 8 litters per group, 16 litters in total.

| Quantity | Control | Protein-restricted |
| --- | --- | --- |
| Litters (sample size) | 8 | 8 |
| Pups weighed | 64 | 64 |
| Mean of litter averages | 53.09 g | 44.58 g |
| SD of litter averages | 3.71 g | 4.18 g |

| Comparison of the 16 litter averages | Value |
| --- | --- |
| Difference in means (control minus protein-restricted) | 8.51 g |
| 95% confidence interval for the difference | 4.27 g to 12.75 g |
| Welch t statistic | 4.311 |
| Degrees of freedom | 13.80 |
| Two-sided p-value | 0.00074 |

Litters from protein-restricted dams weighed 8.51 g less at weaning on average, which is 16.0% of
the control mean. Litter averages ranged from 45.50 g to 56.42 g in the control group and from
34.81 g to 47.80 g in the protein-restricted group, so the groups overlap at their edges even though
their centres are well separated. Within a litter, pups scattered around their own litter's level
with a standard deviation of about 2.4 g in both groups, which is smaller than the 3.7 g to 4.2 g
spread between litter averages. That ordering is the quantitative reason littermates cannot be
counted as independent animals: a large part of a pup's mass is the level of the litter it belongs
to, shared with its seven siblings.

## Interpretation

An 8.5 g shortfall at day 21, roughly one sixth of control body mass, is a substantial growth
deficit for a rat pup at weaning, and it is consistent with a prenatal constraint that was never
made up during suckling. The direction and the magnitude fit the expected mechanism: less maternal
protein means less substrate for fetal tissue accretion, a downshifted somatotropic axis, and a pup
that enters the suckling period already behind. Because the whole litter is shifted together, the
effect reads as something acting on the dam and her uterine and lactational environment, rather than
as something varying pup by pup.

Several practical limits apply. Only one rat strain was studied, and strains differ in how strongly
they respond to gestational protein restriction, so the size of the deficit should not be
transferred to another strain without checking. Litters were culled to a fixed eight pups, which
removes litter size as a competing explanation but also removes the chance to see how the diet
affects litter size itself, and it means the results speak to a standardised nursing load rather
than to whatever load each dam would naturally have carried. Body mass was recorded at a single
timepoint, day 21, so these data cannot say when during gestation or suckling the deficit opened up,
whether it was still widening at weaning, or whether the pups would have caught up later. Body mass
is also a gross measure and does not distinguish lean mass from fat, nor say which organs bore the
shortfall. Sex was recorded and balanced within every litter, but it was not examined as a factor
here; with eight litters per group the design is powered for the diet contrast at the litter level
and not for a sex-by-diet interaction. Answering those questions would need serial weights, body
composition or organ measures, and more litters.
