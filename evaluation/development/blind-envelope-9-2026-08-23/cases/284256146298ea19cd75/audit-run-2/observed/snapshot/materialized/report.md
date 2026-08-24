# Fenced buffer strips and the body condition of smooth newts on farm ponds

## Why we did the survey

The catchment restoration scheme fences a grass buffer strip around farm ponds to keep stock off
the margin. We wanted to know whether that fencing shows up in the animals themselves, so we
surveyed fifteen ponds on working farms and weighed adult male smooth newts in each one. Eight
ponds were ringed by a fenced buffer strip; at the other seven, livestock could walk to the water's
edge.

## What we did

In every pond we set bottle traps and weighed five adult male newts on a field balance reading to
the centigram, releasing each animal on the spot after measurement. That gives 75 weighed newts.

Each weighed newt is one observation. We compared body mass between the buffered and unfenced
groups with an independent two-sample t-test, with all 40 buffered observations and all 35
unfenced observations entering the test, 75 in total. The analysis is in `analysis.py`.

## The data

The survey produced one CSV file, `newt_body_mass.csv`, with 75 rows and a header.

**A single row is one adult male smooth newt: one animal, caught in one pond and weighed once.**
A row is not a pond and not a summary of anything.

The file has four columns:

| Column | Type | What it holds |
| --- | --- | --- |
| `pond_code` | text | The pond the newt was caught in, `PND-01` through `PND-15`. |
| `buffer_strip` | text | Condition of that pond's margin: `buffered` for a fenced grass buffer strip, `unfenced` for livestock access to the water's edge. |
| `newt_number` | integer | Which of the five newts weighed in that pond this row is, 1 to 5. It is a capture label within the pond, not an animal identity carried between ponds. |
| `body_mass_g` | number | Body mass of the newt in grams, to two decimal places. |

Recorded masses run from 1.79 g to 4.29 g. Nothing is missing: every pond contributed exactly five
weighed newts and every cell is filled.

## Results

| Group | n | Mean body mass | SD | Range |
| --- | --- | --- | --- | --- |
| `buffered` | 40 | 3.374 g | 0.708 g | 1.97 to 4.29 g |
| `unfenced` | 35 | 2.874 g | 0.719 g | 1.79 to 4.13 g |

Newts from buffered ponds were heavier by 0.500 g on average (95% CI 0.171 to 0.829 g). The
independent two-sample t-test gives t(73) = 3.032, p = 0.0034, with Cohen's d = 0.702.

## What we take from it

Adult male smooth newts in ponds with a fenced grass buffer strip are heavier than those in ponds
open to livestock, by half a gram on a mean of about three grams. That is a difference of roughly
17% in body mass, and the effect size of 0.70 puts it in the range that field ecologists would call
a substantial difference. With 75 weighed animals behind the comparison and a p-value of 0.0034,
the result is clear.

The practical reading for the scheme is straightforward: fencing the margin is associated with
better-conditioned newts, and the buffer strips appear to be doing what they were installed to do.
A useful next step would be to repeat the weighing in the same ponds after a few more seasons of
fencing, to see whether the gap widens as the buffer vegetation establishes.
