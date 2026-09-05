# Wetland restoration and amphibian recovery in a floodplain pond network

Fifty-four ponds in one river floodplain were surveyed over a single spring with the standard
amphibian protocol: 27 restored under the wetland programme five years earlier and 27 unrestored.
Five outcomes were recorded per pond: amphibian species detected, egg masses counted, emergent
vegetation cover, dissolved oxygen, and hydroperiod.

Correction for multiplicity happened upstream of this report. The complete family of five
outcomes was tested between restored and unrestored ponds with a Welch two-sample test, and a
Holm correction was applied across all five p-values at once at a five-percent family level. That
step wrote `adjusted_results.csv`, one row per outcome carrying the group means, the raw p-value,
the adjusted p-value, the decision, and the method name. `analysis.py` reads `data.csv` only for
the descriptive summaries and takes every inferential statement from `adjusted_results.csv`; it
runs no test of its own.

| Outcome | Unrestored | Restored | Raw p | Holm p | Decision |
|---|---|---|---|---|---|
| Amphibian species | 2.81 | 4.67 | 2.6e-05 | 7.2e-05 | significant |
| Egg masses | 18.4 | 41.1 | 2.4e-05 | 7.2e-05 | significant |
| Emergent vegetation (%) | 24.1 | 52.0 | 2.6e-09 | 1.3e-08 | significant |
| Dissolved oxygen (mg/L) | 5.40 | 7.10 | 7.2e-05 | 7.2e-05 | significant |
| Hydroperiod (days) | 118 | 165 | 2.7e-06 | 1.1e-05 | significant |

All five outcomes clear the family-wide five-percent level. The margins are wide enough that
Holm's ladder changes nothing about which outcomes are called: the largest raw p-value in the
family is 7.2e-05, three orders of magnitude below the level.

## Interpretation for the programme

Restored ponds hold water 47 days longer and carry more than twice the emergent vegetation cover
of unrestored ponds. Those two are the levers the restoration works actually pulled, through
regrading and re-profiling, so they are the outcomes most directly attributable to the programme
rather than to pond-to-pond variation. The biological outcomes follow the same ordering: 1.9 more
species per pond and roughly 2.2 times the egg mass count. Dissolved oxygen is 1.7 mg/L higher,
which is consistent with the vegetation and depth changes.

The programme is doing what it was funded to do, and the sensible reading is that hydroperiod and
vegetation structure are the mechanism. Two caveats limit how far this goes. Ponds were not
randomised to treatment, so restoration sites may have been chosen for characteristics that also
favour amphibians, and a single spring of survey cannot separate a lasting change from one good
breeding season. A second survey year, and a comparison of pre-restoration baselines where they
exist, would settle both.
