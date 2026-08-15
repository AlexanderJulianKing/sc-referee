# Tidal-cue arm choice in juvenile mangrove mud crabs

## Design

Each of the 24 crabs contributed exactly one Y-maze trial, so every row in
the data file is an independent experimental unit. No crab was retested and
no trial was split across rows, so the counted choices are 24 independent
Bernoulli outcomes.

## Sample

- Crabs tested (independent units): 24
- Rows in data file: 24
- Females / males: 12 / 12
- Mean carapace width: 40.03 mm (range 34.9-46.0 mm)

## Outcome

- Chose the tidal-cue arm: 19
- Chose the control arm: 5
- Observed proportion choosing the tidal-cue arm: 0.7917

Descriptive split by sex (no inferential test was run on the subgroups):

| Sex | Tidal-cue choices | Trials | Proportion |
| --- | --- | --- | --- |
| F | 8 | 12 | 0.6667 |
| M | 11 | 12 | 0.9167 |

## Analysis

Exact two-sided binomial test (scipy.stats.binomtest) of the 19 tidal-cue
choices among 24 crabs against the no-preference expectation p = 0.5.

[selected-result] Exact two-sided binomial test, 19/24 crabs chose the tidal-cue arm (proportion 0.7917) against the chance expectation of 0.5: p = 0.006611; the preference is significant at alpha = 0.05.

## Interpretation

Juvenile crabs entered the arm carrying the tidal cue more often than
chance predicts. Because each crab supplied exactly one trial, the
independence assumption of the binomial test is met by the design itself
and no clustering correction is needed.
