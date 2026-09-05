# Bee-friendly field margins and pollinator visits

## What we did

Wildflower margins were sown on 23 of the estate's 46 arable fields in autumn 2023;
the other 23 kept the standard grass margin. Over the 2024 season we ran ten-minute
pollinator transects along each margin, counted flowering plant species in the margin
itself, took oilseed rape seed set from the adjacent crop, and pulled establishment
costs from the contractor invoices. One row per field, five outcomes, `analysis.py`
tests each with a Welch two-sample t-test.

## Results

| Outcome | Grass | Wildflower | p | Verdict at 0.05 |
|---|---|---|---|---|
| Bee visits per 10 min | 13.26 | 19.56 | 1.4e-05 | significant |
| Hoverflies per transect | 6.52 | 9.04 | 0.0064 | significant |
| Flowering species in margin | 5.65 | 13.65 | 1.4e-13 | significant |
| Oilseed rape seed set (%) | 71.45 | 73.02 | 0.48 | not significant |
| Establishment cost (GBP/ha) | 81.91 | 270.09 | 2.8e-17 | significant |

The margin itself changed a lot. Wildflower strips carried roughly two and a half
times as many flowering species as the grass strips, and both bee and hoverfly
activity along them was clearly higher. Seed set in the neighbouring rape crop was
about 1.6 points higher next to wildflower margins, but that gap sits comfortably
inside the field-to-field scatter (SD around 8 points) and the test does not separate
it from zero. Wildflower margins cost about GBP 188/ha more to establish.

## Advice to the estate

Expand the wildflower margins, but expand them for the biodiversity, not for the
yield. The pollinator and botanical gains are large and consistent across fields, and
they are what the agri-environment payments are actually for. What one season of data
does not show is a crop return: we cannot say from these fields that seed set rises
next to a wildflower margin, and the estate should not build a business case on that
number. If the payment rate covers the extra GBP ~190/ha of establishment, the
expansion pays for itself on the environmental outcome alone.

Two caveats worth carrying forward. Fields were not randomised to margin type by us,
so any pre-existing difference between the two halves of the estate (soil, hedgerow
structure, past cropping) rides along in these comparisons. And five outcomes were
tested here one after another; the seed-set result in particular should be revisited
with more seasons before it is treated as settled either way.
