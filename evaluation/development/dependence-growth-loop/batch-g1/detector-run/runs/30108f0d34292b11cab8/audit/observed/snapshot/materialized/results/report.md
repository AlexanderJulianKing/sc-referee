# Does thermal-hydrolysis pretreatment lift weekly methane yield?

Each logged session pairs a pretreated train against a control train fed in
parallel on the same day, so every session returns one win-or-loss verdict
for the pretreatment step.

## Session counts

- Sessions read from `data/input.csv`: 20
- Distinct digester identifiers in the file: 5
- Sessions won by the pretreated train: 15

| digester_id | sessions | pretreated wins |
| --- | --- | --- |
| D-01 | 4 | 4 |
| D-02 | 4 | 4 |
| D-03 | 4 | 3 |
| D-04 | 4 | 3 |
| D-05 | 4 | 1 |

## Analysis

Every logged session is treated as one independent Bernoulli trial and the
win tally is tested against a fair-coin null of 0.5 with the exact two-sided
binomial test `scipy.stats.binomtest`.

- Observed win proportion: 0.750
- Exact two-sided p-value: 0.0414

[selected-result] Exact two-sided binomial test (scipy.stats.binomtest) over 20 weekly sampling sessions: the pretreated train won 15 of 20 sessions, proportion 0.750, p = 0.0414, which is below 0.05, so the log is read as evidence that thermal-hydrolysis pretreatment raises specific methane yield.
