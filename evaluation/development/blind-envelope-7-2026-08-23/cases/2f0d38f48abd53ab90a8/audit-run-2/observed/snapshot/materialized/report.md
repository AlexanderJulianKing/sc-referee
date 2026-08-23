# Do complex high-relief reef modules hold more fish than simple blocks?

## Study design

Sixteen artificial reef modules were deployed on sandy seabed at similar depth and
spacing: eight simple concrete blocks and eight complex high-relief units with many
interstitial spaces. Divers surveyed every module five times over one summer, counting
all fish inside a fixed radius on each dive, for 80 dive surveys in total.

The module is the unit that was assigned to a design, so **the module is the
independent unit: 16 modules, 8 per design.** A module's five surveys are repeat
visits to the same patch of reef and are correlated with one another.

## Data description

The file `reef_fish_surveys.csv` has a header line and 80 data rows.

**One row is one dive survey of one reef module** — the fish counted inside the fixed
radius around that module on that occasion.

| Column | Type | Meaning |
| ------ | ---- | ------- |
| `module_id` | text | Reef module surveyed (`MOD01`–`MOD16`, 16 values, 5 rows each). Constant across a module's five surveys. |
| `reef_design` | text | Design of the module: `simple_block` or `complex_high_relief`. A property of the module, so identical on all five of its rows. The group compared. |
| `survey_number` | integer | Which survey occasion this row is (`1`–`5`), in time order within the module. |
| `fish_count` | integer | Outcome. Total fish counted within the fixed radius on that dive. Whole fish, never negative. |

No missing values; every module has all five surveys.

## Method

The primary analysis is a cluster bootstrap written into `analysis.py`. It draws whole
modules with replacement, separately within each design, keeping all of a drawn
module's surveys together, and recomputes the difference in mean fish per survey
(complex minus simple) each time: 20,000 resamples, seed 20260823. The interval is the
2.5th and 97.5th percentiles of those replicates. The two-sided p-value recentres the
replicates on zero and asks how often a null replicate falls at least as far from zero
as the observed difference.

## Result

Simple modules averaged 21.7 fish per survey, complex modules 29.9.

**Difference: +8.20 fish per survey (complex minus simple).**
Bootstrap standard error 4.13; test statistic (difference / bootstrap SE) = 1.99;
95% CI +0.25 to +16.35 fish; **p = 0.046**. Sample size: **16 modules**, 8 per design,
5 surveys each (80 survey rows).

### Illustration only — not a valid basis for inference here

A plain independent two-sample t-test across all 80 survey rows gives t = 3.72,
df = 78, p = 0.00037. **This number is shown only for illustration and is not a valid
basis for inference here**, because it counts the five repeat surveys of one module as
five independent observations. That inflates the apparent sample size from 16 modules
to 80 rows, and the p-value comes out roughly 120 times smaller than the module-level
result.

## Interpretation

Complex high-relief modules held more fish than simple blocks, but the evidence is
thin. About eight extra fish per survey is a large effect against a simple-block
baseline near 22, and the module-level interval excludes zero, barely. Its lower end
sits at a quarter of one fish, so the data are also compatible with a difference too
small to matter ecologically. The reason is the spread between modules: module means
run from 7.0 to 37.6 fish among simple blocks and 19.0 to 42.4 among complex units, so
the designs overlap heavily and the best simple module out-fished half the complex
ones. Eight modules per design is not enough replication to pin the effect down. I
read this as encouraging support for high-relief design, and would size a follow-up on
more modules rather than more dives on these sixteen.
