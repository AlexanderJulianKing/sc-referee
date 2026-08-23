# Data description

## Files

| File | What it is |
| --- | --- |
| `pup_masses.csv` | The one and only data file. Raw pup-level records. |
| `make_data.py` | The script that generated `pup_masses.csv`. Standard library only, fixed seed. |

There is no second, pre-summarised CSV. Litter averages are not stored on disk; the analysis
script forms them from `pup_masses.csv` at run time.

## What one row represents

**One row is one weaned rat pup, weighed once on postnatal day 21.**

A litter is *not* one row. Each litter was culled to 8 pups on postnatal day 2 and all 8 were
weighed, so **every litter occupies 8 consecutive rows** and its `litter_id` repeats 8 times.
Rows within a litter are therefore not independent of one another.

## Counts

| Quantity | Value |
| --- | --- |
| Dams | 16 |
| Litters (one per dam) | 16 |
| Litters per diet group | 8 control, 8 protein-restricted |
| Pups weighed per litter | 8 (fixed cull size, no variation) |
| Data rows | 128 |
| Lines in the file | 129 (128 data rows plus one header row) |

**Experimental unit: the litter.** The diet was fed to the dam, so treatment was assigned 16
times, not 128 times. Littermates additionally share genetics and one nursing dam. The 128 pups
are repeated measurements clustered inside 16 independently treated units. Any group comparison
that treats the 128 pups as 128 independent observations inflates the sample size roughly
eight-fold and is wrong for this design.

## The two groups

| `diet_group` value | Meaning | Litters | Rows |
| --- | --- | --- | --- |
| `control` | Dam fed the control diet throughout gestation. Litters `L01`–`L08`. | 8 | 64 |
| `protein_restricted` | Dam fed the protein-restricted diet throughout gestation. Litters `L09`–`L16`. | 8 | 64 |

The group is a property of the dam, so it is constant across all 8 rows of a litter.

## Columns

The file has exactly five columns, in this order.

### `litter_id`
String. Identifies the litter, and equivalently the dam, since each dam produced exactly one
litter. Values are `L01` through `L16`, zero-padded to two digits so they sort correctly as text.
Appears 8 times each. This is the clustering variable and the label of the experimental unit.

### `diet_group`
String, two levels: `control` or `protein_restricted`. The maternal dietary treatment during
gestation. Constant within a litter.

### `pup_id`
String. Identifies the pup **within its litter**, formatted as the litter label, a hyphen, then
`P1` to `P8`, for example `L03-P5`. Because the litter label is embedded, the value is also unique
across the whole file, giving 128 distinct values. It is a label, not a quantity; the trailing
number is an arbitrary index and carries no ordering, birth order, or ranking information.

### `sex`
String, two levels: `F` (female) or `M` (male). Each litter contains exactly 4 females and 4
males, assigned in shuffled order, so the file holds 64 of each overall. Sex was given no effect
in the generating model, so it is balanced nuisance information rather than a factor the data
support studying.

### `body_mass_g`
Number. The outcome: the pup's body mass in **grams** on postnatal day 21, at weaning. Rounded to
one decimal place. One measurement per pup; there are no missing values, and no pup was weighed
more than once. Observed range in this file: 31.5 g to 60.0 g.

## How the values were generated

The data are simulated, not measured. `make_data.py` draws each pup's mass as

    mass = group_mean + litter_effect + pup_noise

with `group_mean` set to 52.0 g for control and 45.0 g for protein-restricted, `litter_effect`
drawn once per litter from a Normal distribution with SD 3.5 g, and `pup_noise` drawn once per pup
from a Normal distribution with SD 2.5 g. The result is rounded to one decimal.

That two-part error is what makes the litter the unit: a litter's whole set of 8 pups is shifted
up or down together by its shared `litter_effect`, and only the smaller `pup_noise` separates
littermates from one another.

Realized values in this particular file, for reference:

| Group | Mean of the 8 litter averages | SD between litter averages | Mean within-litter SD |
| --- | --- | --- | --- |
| `control` | 53.09 g | 3.71 g | 2.43 g |
| `protein_restricted` | 44.58 g | 4.18 g | 2.41 g |

**Seed and seed selection, disclosed.** The generator uses the fixed seed 20260827 and reproduces
the file byte-for-byte. That seed was not the first one tried. Seeds were scanned upward from
20260822 and the first kept whose realized spread matched the design: between-litter SD of the 8
litter averages within [2.8, 4.3] g and mean within-litter SD within [2.1, 2.9] g, in both groups.
The screen inspects spread only. It never looks at the group means, their difference, or any test
statistic, and it cannot see them even indirectly, because the group mean is added after the
random draws and shifts every pup in a group by the same constant, which leaves all the spread
figures unchanged. The screen does condition on between-litter spread, so litter averages here are
mildly less dispersed than a completely unscreened draw, and anyone reasoning about the sampling
behaviour of this generator should allow for that.

Because the numbers are simulated from a known model, they can illustrate the analysis but cannot
be evidence about real rats.
