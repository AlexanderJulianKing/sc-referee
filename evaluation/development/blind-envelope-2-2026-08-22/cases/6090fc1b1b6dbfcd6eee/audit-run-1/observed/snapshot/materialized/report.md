# Sensitive invertebrate richness in restored and channelised stream reaches

## Why sensitive taxa are the measure

Mayflies, stoneflies and caddisflies (the EPT orders) are the standard biological readout for
stream habitat condition because their life histories tie them tightly to the physical structure
of the channel. Most of these taxa need well oxygenated water moving over clean, loose gravel;
their nymphs and larvae shelter in the spaces between stones, graze the biofilm on stable
surfaces, or spin nets in fast riffle flow. Channelisation removes that structure. A straightened,
uniform, over-widened channel loses its riffle and pool sequence, fills its interstitial spaces
with fine sediment, and drops the near-bed oxygen supply, and the sensitive taxa drop out first
while tolerant worms and midge larvae persist. Because the sensitive taxa disappear early and
recolonise only once the physical habitat is genuinely rebuilt, counting how many of them are
present in a kick-net sample gives a direct, integrative measure of whether restoration has put
back the habitat it was meant to put back. That is the reasoning behind the survey reported here.

## Data description

The analysis draws on two files. They describe the same survey at two different levels.

### `kicknet_samples_raw.csv` (raw, sample level)

**One row is one kick-net sample.** The file holds 240 data rows, which is twelve rows for each of
the 20 reaches.

| Column | What it holds |
| --- | --- |
| `reach_id` | The reach the sample came from, labelled `R01` to `R20`. Each label appears on twelve rows. |
| `restoration_group` | The treatment of the whole reach, either `restored` or `channelised`. It is constant within a reach. |
| `sample_id` | The sample's identifier within its reach, written as `<reach_id>_S01` to `<reach_id>_S12`. It is unique across the file. |
| `distance_m` | Distance in metres upstream of the reach start at which the kick-net was taken. Values run from 5.6 to 194.4 m along the roughly 200 m reach. |
| `mean_depth_cm` | Mean water depth in centimetres at the sampling point. Values run from 12.1 to 45.9 cm. |
| `sensitive_taxa_count` | The number of mayfly, stonefly and caddisfly taxa found in that kick-net sample, as a whole number. Values run from 2 to 18. |

### `reach_summary.csv` (per-reach summary)

**One row is one reach.** The file holds exactly 20 data rows, one for each reach, so each reach
that fills twelve rows of the raw file fills a single row here.

| Column | What it holds |
| --- | --- |
| `reach_id` | The reach identifier, `R01` to `R20`. The same labels and the same meaning as in the raw file. |
| `restoration_group` | `restored` or `channelised`. The same labels and the same meaning as in the raw file. |
| `n_samples` | The number of kick-net samples that reach contributed. It is 12 for every reach. |
| `mean_sensitive_taxa` | The reach's mean `sensitive_taxa_count` across its twelve raw rows, rounded to two decimal places. |

The summary file is computed from the raw file, so every `mean_sensitive_taxa` value equals the
mean of that reach's rows in `kicknet_samples_raw.csv`.

## Design and the unit of analysis

Restoration was applied to whole reaches. Each intervention ran along roughly 200 m of channel, so
every kick-net sample taken inside a reach shares the same treatment, the same rebuilt channel
form, and the same upstream catchment. There are 20 reaches, 10 restored and 10 left channelised.

The twelve kick-nets within a reach are subsamples of that reach. They were not assigned to a
treatment individually and they are not independent replicates of the restoration effect; they
measure how patchy the invertebrate community is along a single stretch of river. Treating them as
240 independent observations would count the same treatment decision twelve times over and would
give a p-value far smaller than the design earns.

The inferential comparison therefore uses the per-reach values from `reach_summary.csv`, one value
per reach, and the sample size is counted in reaches: 10 per group, 20 in total. The raw
sample-level file is used only to count samples and to check that the summary file is consistent
with it. No group comparison is run on the raw rows.

## Results

### Descriptive checks on the raw file

* 240 kick-net samples in total, 120 from restored reaches and 120 from channelised reaches.
* All 20 reaches contributed exactly 12 samples, with no reach short or over.
* For all 20 reaches, `n_samples` in the summary file matched the number of raw rows, and
  `mean_sensitive_taxa` matched the mean of that reach's raw `sensitive_taxa_count` values to two
  decimal places. There were no mismatches.

### Reach-level comparison

The comparison is an independent two-sample t-test (Welch's version, which does not assume equal
variances) on the 20 reach mean richness values.

| Quantity | Restored | Channelised |
| --- | --- | --- |
| Number of reaches | 10 | 10 |
| Mean sensitive taxa per kick-net | 11.24 | 7.02 |
| Standard deviation of reach means | 1.77 | 1.87 |
| Range of reach means | 8.83 to 14.58 | 4.25 to 9.67 |

* Difference in means (restored minus channelised): **4.22 taxa** (4.215 before rounding).
* Welch's t = 5.175 on 17.95 degrees of freedom.
* p = 6.4e-05.
* Total sample size for the test: 20 reaches.

## Interpretation

Restored reaches carried about 4.2 more sensitive taxa per kick-net than channelised reaches, which
is a rise of roughly 60 percent over the channelised level of 7.0 taxa. On a scale where a
kick-net in this river system yields somewhere between 2 and 18 sensitive taxa, that difference is
large enough to matter in the field and not only on paper. It is the kind of shift that separates a
moderately impacted community from one approaching good ecological status under the usual EPT-based
indices.

Ecologically the result is consistent with the physical habitat having been rebuilt rather than
merely rearranged. Gaining several sensitive taxa, rather than gaining more individuals of the few
taxa already present, points to new functional niches: stable gravel for the burrowing and clinging
mayflies, faster riffle flow for net-spinning caddis, and cleaner interstitial spaces with enough
oxygen for stonefly nymphs. Restoration appears to have restored the range of microhabitats, not
just the average depth or width of the channel.

The reach means also show that reaches differ substantially from one another within a group. Reach
means spread across about 5.8 taxa in the restored group and about 5.4 taxa in the channelised
group, which is well beyond what kick-net to kick-net variation alone would produce. Catchment
setting, upstream water quality and the local recolonisation source pool plainly still shape what
any single reach supports, and the restoration effect sits on top of that variation rather than
erasing it.

## Caveats

* **A single survey season.** All 240 kick-nets came from one summer survey. Sensitive taxa have
  strong seasonal emergence patterns, so a single summer snapshot may over- or under-represent
  taxa whose adults had already flown. Repeat surveys across seasons and years would be needed to
  show that the difference persists.
* **No pre-restoration baseline.** The design compares restored reaches against channelised
  reaches at one point in time. It does not compare each reach against its own earlier state.
  If restoration schemes were preferentially placed on reaches that already had better water
  quality or a better upstream source pool, part of the measured difference would reflect that
  choice rather than the works themselves. A before-after-control-impact design would separate the
  two.
* **Regional scope.** The 20 reaches come from one monitoring programme in one region. Geology,
  land use and the regional species pool set an upper limit on how many sensitive taxa any reach
  can support, so the size of the effect found here should not be transferred to other catchments
  without local data.
* **Modest replication.** Ten reaches per group is a workable but small number of independent
  units. The effect is clear at this size, but the estimate of its magnitude carries meaningful
  uncertainty, and smaller effects on other endpoints could easily go undetected in a design of
  this size.
* **Richness only.** Counting taxa treats every sensitive taxon as equivalent. It says nothing
  about abundance, about which particular taxa returned, or about whether the most demanding
  indicator species are among them. A trait-based or index-based follow-up would add that detail.

## Reproducing the analysis

Run `analysis.py` from the project root with `/usr/local/bin/python3`. The script reads both CSV
files, prints the descriptive counts and consistency checks from the raw file, then runs and prints
the reach-level two-group comparison reported above.
