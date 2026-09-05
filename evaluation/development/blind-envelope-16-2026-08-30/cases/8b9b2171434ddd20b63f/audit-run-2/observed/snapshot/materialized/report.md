# Hare condition on mixed farmland versus intensive arable land

## Data

The analysis reads `hares.csv`. One row is one adult European hare, live-trapped
once in late winter, measured and sampled at the trap site, then released. Each
hare appears exactly once, and every hare has a value for all five outcomes.
There are 64 hares in total, 32 from each landscape.

| Column | Unit | Description |
| --- | --- | --- |
| `hare_id` | none | Short per-hare identifier, `H01` to `H64`. |
| `landscape` | none | Landscape of capture. Two values: `mixed_farmland` (32 hares) and `intensive_arable` (32 hares). |
| `body_mass_kg` | kilograms | Body mass at capture. |
| `hind_foot_mm` | millimetres | Hind foot length. |
| `cortisol_ng_g` | ng per gram dry faeces | Faecal cortisol metabolite concentration. |
| `haemoglobin_g_dl` | grams per decilitre | Blood haemoglobin concentration. |
| `egg_count_epg` | eggs per gram of faeces | Gastrointestinal nematode egg count. |

The five outcomes are listed in the order the study declared them in advance:
body mass, hind foot length, faecal cortisol, haemoglobin, nematode egg count.

## Methods

For each of the five declared outcomes we computed a Welch two-sample t
statistic comparing mixed farmland with intensive arable, signed as mixed
farmland minus intensive arable.

Testing five outcomes at once raises the chance that at least one of them looks
different by luck alone. We controlled that risk with a label-shuffling
procedure written out by hand in `analysis.py`, not taken from a ready-made
correction routine. The procedure was fixed in advance:

1. Shuffle the `landscape` labels across all 64 hares. All five outcomes are
   re-tested under the same shuffled labels, so the way the outcomes move
   together in the real animals is preserved.
2. Recompute the t statistic for all five declared outcomes.
3. Keep only the single largest absolute statistic seen anywhere in the family
   of five on that shuffle.
4. Repeat for the pre-declared count of 4000 shuffles.

The 4000 kept values form one reference distribution of family maxima. Each
outcome is then judged against that single shared reference, and the resulting
value is that outcome's family-wise adjusted significance, read at 0.05. Keeping
only the largest statistic across the whole family on each shuffle is what holds
the family-wise error rate at 0.05 across all five outcomes. The reference
describes the biggest result that pure label noise produces anywhere among the
five, so the chance that noise alone beats it in even one of the five outcomes
is 0.05, rather than 0.05 for each outcome separately. The observed labelling is
counted as one extra draw, the usual convention, so no reported value can be
exactly zero.

The shuffling seed is fixed (20260830), so the run repeats exactly. Verdicts come
only from this family-maximum reference. No unshuffled per-outcome p-value was
computed or used.

Across the 4000 shuffles the family maxima reached 4.4010 at the largest, with a
95th percentile of 2.6222.

## Results

Means are group means on the original measurement scale. `fwer_p` is the
family-wise adjusted value from the 4000-shuffle family-maximum reference.

| Outcome | Mixed farmland | Intensive arable | Welch t | fwer_p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- |
| `body_mass_kg` | 3.7859 | 3.4059 | 4.4719 | 0.00025 | Significant |
| `hind_foot_mm` | 143.1562 | 141.9375 | 1.0573 | 0.83054 | Not significant |
| `cortisol_ng_g` | 107.0625 | 188.0250 | -5.0252 | 0.00025 | Significant |
| `haemoglobin_g_dl` | 13.7812 | 13.2406 | 2.1751 | 0.14796 | Not significant |
| `egg_count_epg` | 171.7188 | 221.2812 | -0.9027 | 0.90202 | Not significant |

Per-outcome conclusions, in the declared order:

1. **Body mass.** Hares on mixed farmland averaged 3.7859 kg against 3.4059 kg on
   intensive arable, a gap of 0.38 kg. The observed statistic of 4.4719 sits
   beyond almost the whole family-maximum reference, giving a family-wise value
   of 0.00025. Significant at the family-wise 0.05 level.
2. **Hind foot length.** 143.1562 mm against 141.9375 mm, statistic 1.0573,
   family-wise value 0.83054. Not significant.
3. **Faecal cortisol.** 107.0625 ng/g against 188.0250 ng/g, so hares on
   intensive arable carried the higher concentration. The observed statistic of
   -5.0252 is larger in absolute size than every one of the 4000 family maxima,
   giving a family-wise value of 0.00025. Significant at the family-wise 0.05
   level.
4. **Haemoglobin.** 13.7812 g/dl against 13.2406 g/dl, statistic 2.1751,
   family-wise value 0.14796. Not significant once the whole family of five is
   accounted for.
5. **Nematode egg count.** 171.7188 epg against 221.2812 epg, statistic -0.9027,
   family-wise value 0.90202. Not significant. Egg counts scatter very widely
   between individual hares, which swamps the gap in group averages.

## Interpretation for farmland wildlife management

Two of the five declared outcomes separate the landscapes after full family-wise
control. Hares caught on mixed farmland with uncropped fallow strips were about
0.38 kg heavier than hares caught on intensively cropped arable land with no
fallow, and they carried faecal cortisol metabolite concentrations about 43
percent lower. Both results stand out against the biggest effect that label
noise produces anywhere across all five outcomes, so neither is an artefact of
testing five things at once.

The other three outcomes do not separate the landscapes at this standard.
Skeletal size, measured by hind foot length, is close to identical in the two
groups. That is a useful check: it suggests the two catches are the same kind of
animal, so the body mass gap reflects condition rather than a difference in
frame size. Haemoglobin runs in the expected direction, 0.54 g/dl higher on
mixed farmland, but the gap is not large enough to clear the family-wise bar
with 64 hares. Parasite egg counts average higher on intensive arable, but
individual hares vary so much that this study cannot separate that from chance.

For management, the practical reading is that uncropped fallow strips on
otherwise farmed land go together with heavier hares carrying a lower chronic
stress load in late winter. This is a trapping snapshot rather than an
experiment, so it cannot show that the strips caused the difference. Haemoglobin
and parasite burden are worth revisiting with a larger sample before any claim
is made about them.
