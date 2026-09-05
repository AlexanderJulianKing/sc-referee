# Chick condition in the near and far sub-colonies

## Data

The data file is `penguin_chick_condition.csv`. One row is one Adelie penguin chick,
measured once at about 25 days of age. There are 48 chicks: 25 in the near sub-colony
and 23 in the far sub-colony of the same breeding site. Every chick has a value in
every column, and there are no blank cells.

| Column | Meaning | Unit |
| --- | --- | --- |
| `chick_id` | Identifier for the chick, unique across the file | none (text label) |
| `sub_colony` | Sub-colony the chick belongs to: `near` (adults forage a short distance away) or `far` (adults commute much further) | none (group label) |
| `body_mass_g` | Body mass of the chick | grams (g) |
| `flipper_length_mm` | Flipper length of the chick | millimetres (mm) |
| `haemoglobin_g_dl` | Blood haemoglobin concentration | grams per decilitre (g/dL) |
| `corticosterone_ng_ml` | Plasma corticosterone concentration | nanograms per millilitre (ng/mL) |

The four outcome columns appear in the order declared in the study plan: body mass,
flipper length, haemoglobin, corticosterone.

## Method

`analysis.py` reads the CSV and compares the near and far sub-colonies on each of the
four declared outcomes. The same test is used for every outcome: a two-sided Welch's
two-sample t-test, which does not assume the two groups have equal variances. Each
outcome answers its own biological question about chick condition, so each comparison
is judged on its own terms at the conventional 0.05 threshold.

## Results

### 1. Body mass (`body_mass_g`, g)

n = 25 near, 23 far. Mean near 2665.680 g, mean far 2487.522 g, a difference of
178.158 g. Welch t = 2.6720, p = 0.0104.

Verdict at 0.05: significant. The near and far sub-colonies differ in body mass.
Chicks in the near sub-colony are on average about 178 g heavier, which is what you
would expect if their parents deliver food after shorter foraging trips. Body mass at
this age is the most direct measure of how much food a chick has been getting.

### 2. Flipper length (`flipper_length_mm`, mm)

n = 25 near, 23 far. Mean near 139.060 mm, mean far 135.674 mm, a difference of
3.386 mm. Welch t = 1.6497, p = 0.1058.

Verdict at 0.05: not significant. There is no clear difference in flipper length. The
near chicks average about 3.4 mm longer, but the spread within each group is wide
enough that this size of gap is not unusual by chance. Skeletal growth appears similar
in the two sub-colonies, which fits the idea that structural size responds more slowly
than mass to short-term differences in food delivery.

### 3. Blood haemoglobin (`haemoglobin_g_dl`, g/dL)

n = 25 near, 23 far. Mean near 16.528 g/dL, mean far 16.230 g/dL, a difference of
0.298 g/dL. Welch t = 0.7854, p = 0.4365.

Verdict at 0.05: not significant. Haemoglobin looks the same in the two sub-colonies.
The gap of about 0.3 g/dL is small next to the within-group spread. Oxygen-carrying
capacity, which matters for diving later in life, is not detectably affected by which
sub-colony a chick was reared in.

### 4. Plasma corticosterone (`corticosterone_ng_ml`, ng/mL)

n = 25 near, 23 far. Mean near 7.172 ng/mL, mean far 8.289 ng/mL, a difference of
-1.117 ng/mL. Welch t = -1.3797, p = 0.1743.

Verdict at 0.05: not significant. Corticosterone, the main stress hormone measured
here, does not differ clearly between the sub-colonies. Far chicks average about
1.1 ng/mL higher, the direction you would expect if longer waits between meals were
stressful, but the difference is not large enough relative to the scatter to be
distinguished from chance in this sample.

## Conclusion

Of the four declared aspects of chick condition, only body mass separates the two
sub-colonies at the 0.05 threshold: chicks in the near sub-colony are heavier than
chicks in the far sub-colony. Flipper length, haemoglobin, and corticosterone show
differences in the expected directions but none reach significance in this sample of
48 chicks. The picture is one of a difference in current energy stores rather than in
skeletal growth, blood oxygen capacity, or measured stress hormone level.
