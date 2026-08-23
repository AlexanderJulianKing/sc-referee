# Five-year diameter growth of tagged Douglas-fir overstory trees following commercial thinning

## Background

A mature Douglas-fir stand carries far more stems than the site can supply with light, water, and
nutrients. Crowns interlock, live crown ratios shorten, and the annual carbon gain of each tree is
divided among more competitors than the growing space can support. Commercial thinning removes part
of that competition. The trees left standing recover growing space on all sides: more light reaches
the retained crowns, root systems face less demand on the same soil water, and the crown that
survives the entry begins to expand into the openings its neighbours left behind. Because a tree
allocates a large share of its surplus carbon to the bole, that release from competition is expected
to show up directly as faster diameter growth at breast height in the years after the entry. The
size of the response, and how quickly it appears, is what a thinning trial is built to measure.

This report covers a network of 14 Douglas-fir stands that I established and remeasured. Seven were
commercially thinned and seven were left unthinned. Ten mature overstory trees were tagged in each
stand and remeasured five years later.

## Data description

The analysis uses one file, `tagged_tree_increment.csv`, with a header row and 140 data rows.

**A single row is one tagged overstory tree**, remeasured once at the end of the five-year
monitoring period. The row carries that tree's own starting diameter, crown class, and five-year
diameter increment, along with the code of the stand it grows in and the treatment that stand
received.

| Column | Type | Units | Description |
|---|---|---|---|
| `stand_code` | text | — | Identifier of the forest stand the tree grows in. Values `ST-01` through `ST-14`. |
| `treatment` | text | — | Treatment applied to the stand: `thinned` or `unthinned`. |
| `tree_tag` | text | — | Tag number of the individual tree, written as the stand code plus the within-stand tag, e.g. `ST-01-T01` through `ST-01-T10`. Unique across all 140 rows. |
| `start_dbh_cm` | number | centimetres | Diameter at breast height measured on the tree at the beginning of the monitoring period. One decimal place. Range 23.2 to 55.8, mean 37.5. |
| `crown_class` | text | — | Crown position of the tagged tree at the start of the period: `dominant` (37 trees), `codominant` (73 trees), or `intermediate` (30 trees). All tagged trees are overstory trees; suppressed trees were not tagged. |
| `dbh_increment_cm` | number | centimetres | The outcome. Growth in diameter at breast height over the five-year monitoring period. Two decimal places, never negative. Range 0.90 to 6.90. |

Tagging was spread across the overstory rather than confined to the largest stems, so the crown
classes present in the file span dominant through intermediate positions. Starting diameters were
similar in the two groups, averaging 37.0 cm in the thinned group and 38.0 cm in the unthinned
group.

## Statistical comparison

Five-year diameter increment was compared between thinned and unthinned forest with a single
independent two-sample t-test. Each tagged tree is one observation in that comparison. The sample
size is 70 tagged trees in the thinned group and 70 tagged trees in the unthinned group, 140 tagged
trees in total. The analysis is carried out in `analysis.py`, which reads the CSV, forms the two
groups, and prints the sample sizes, group means, group standard deviations, difference in means,
and p-value.

## Results

| Group | Tagged trees | Mean increment (cm) | SD (cm) |
|---|---|---|---|
| Thinned | 70 | 4.63 | 0.90 |
| Unthinned | 70 | 3.24 | 1.09 |

Tagged trees in thinned forest grew 1.39 cm more in diameter over five years than tagged trees in
unthinned forest. The two-sample t-test gives t(138) = 8.20, p = 1.5 x 10^-13.

## Interpretation

The response is large in silvicultural terms. An increment of 4.63 cm against 3.24 cm is a 43 per
cent gain in five-year diameter growth, and it is already fully expressed within the first five
years after the entry, which is consistent with retained crowns beginning to occupy released growing
space in the first two or three seasons. Spread over the period, thinned trees put on roughly 0.93
cm of diameter per year against 0.65 cm in unthinned forest.

For a manager, growth of that order shortens the time to merchantable size classes and shifts the
volume that does accumulate onto fewer, larger, higher-value stems. The gain is per tree rather than
per hectare: thinning removes basal area, so a per-tree response of this size does not by itself
mean the thinned stands are producing more total volume than the unthinned ones over the same
period. It means the growth that is produced is being concentrated on the retained crop trees, which
is what the prescription is meant to achieve.

The usual practical caveats apply. Five years is a short window against the length of a Douglas-fir
rotation, and it captures the early, strongest part of a release response; whether the differential
holds, narrows, or widens as crowns close again is a question for the next remeasurement. The
network sits in a single region, so the response is anchored to the site quality, climate, and
stocking history found there, and transfer to drier or more productive ground should be made with
care. The tagged trees are overstory trees only, dominant through intermediate, so nothing here
describes how suppressed stems respond to the same entry. Finally, the outcome is diameter at breast
height, which is a good index of bole growth but not a substitute for a full volume or taper
assessment.

Within those bounds, the result is clear: commercial thinning increased the five-year diameter
growth of the Douglas-fir left standing by about 1.4 cm.
