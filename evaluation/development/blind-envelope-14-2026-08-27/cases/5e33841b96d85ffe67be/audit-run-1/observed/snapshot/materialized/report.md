# Rice-based versus glucose-based oral rehydration solution in young children with acute watery gastroenteritis

## Design

Eighty-four children aged six to thirty-six months, admitted to the paediatric ward with acute
watery gastroenteritis, were allocated to one of two oral rehydration solutions: a standard
glucose-based reduced-osmolarity solution (n = 42) or a rice-based solution (n = 42). Care was
otherwise identical in the two groups. Each child was followed for the first forty-eight hours
after admission, and the same set of measurements was recorded for every child.

The protocol declared a family of six outcomes before recruitment, in a fixed order, and named
the first two as primary.

## Data

The analysis reads a single file, `ors_trial.csv`, at the project root. It has a header row and
84 data rows. **One row is one child.** All of that child's recorded outcomes sit on that row;
no child appears twice, and there are no repeated-measure rows. Every cell is filled.

| # | Column | Type | Unit | Meaning |
|---|--------|------|------|---------|
| 1 | `child_id` | text | none | Participant identifier, `C001` to `C084`, assigned in order of admission. Unique. |
| 2 | `solution` | text | none | Group. Exactly two values: `glucose_based` and `rice_based`. |
| 3 | `diarrhoea_duration_h` | integer | h | Declared outcome 1 (primary). Hours from admission until diarrhoea stopped. |
| 4 | `stool_output_g_per_kg_24h` | decimal | g/kg | Declared outcome 2 (primary). Total stool output over the first 24 h per kg of admission weight. |
| 5 | `ors_intake_ml_per_kg_24h` | integer | mL/kg | Declared outcome 3. Total solution taken over the first 24 h per kg of admission weight. |
| 6 | `vomiting_episodes_24h` | integer | count | Declared outcome 4. Vomiting episodes during the first 24 h, 0 to 7. |
| 7 | `weight_change_pct_48h` | decimal | % | Declared outcome 5. Weight at 48 h as a percentage change from admission weight; positive means weight gained. |
| 8 | `serum_sodium_mmol_per_l_24h` | integer | mmol/L | Declared outcome 6. Serum sodium at 24 h after admission. |

## Statistical methods

Each of the six declared outcomes was compared between the two solutions with a two-sample test.
The five continuous outcomes were compared with Welch's two-sample t-test, which does not assume
that the two groups share a variance. Vomiting episodes, a small bounded count, were compared
with the Mann-Whitney U test.

The two primary outcomes were handled as a pair: their two p-values were passed through the Holm
step-down procedure (`statsmodels.stats.multitest.multipletests`, `method="holm"`), and those two
outcomes were judged on the adjusted values against alpha = 0.05.

Declared outcomes 3 to 6 were each treated as a separate scientific question standing on its own.
Their raw p-values are reported, and an outcome was called significant when its raw p-value fell
below 0.05.

## Results

Group means are shown for both solutions. The difference is the rice-based mean minus the
glucose-based mean, so a negative number means the value was lower on the rice-based solution.
The "p used" column holds the value each outcome was judged on: Holm-adjusted for the two primary
outcomes, raw for the other four.

| # | Outcome | Unit | Glucose-based mean | Rice-based mean | Difference | Test | p (raw) | p used | Conclusion |
|---|---------|------|-----|-----|-----|------|---------|--------|------------|
| 1 | `diarrhoea_duration_h` (primary) | h | 63.05 | 52.00 | -11.05 | Welch t | 0.0002 | 0.0004 (Holm) | Significant |
| 2 | `stool_output_g_per_kg_24h` (primary) | g/kg | 84.00 | 68.01 | -16.00 | Welch t | 0.0004 | 0.0004 (Holm) | Significant |
| 3 | `ors_intake_ml_per_kg_24h` | mL/kg | 129.98 | 117.05 | -12.93 | Welch t | 0.0513 | 0.0513 (raw) | Not significant |
| 4 | `vomiting_episodes_24h` | count | 2.05 | 1.95 | -0.10 | Mann-Whitney U | 0.3694 | 0.3694 (raw) | Not significant |
| 5 | `weight_change_pct_48h` | % | 2.00 | 2.80 | +0.81 | Welch t | 0.0111 | 0.0111 (raw) | Significant |
| 6 | `serum_sodium_mmol_per_l_24h` | mmol/L | 137.29 | 137.64 | +0.36 | Welch t | 0.5742 | 0.5742 (raw) | Not significant |

Standard deviations, for scale: diarrhoea duration 13.9 h (glucose) and 12.1 h (rice); stool
output 21.0 and 19.0 g/kg; intake 30.0 and 29.9 mL/kg; vomiting episodes 1.7 and 2.1; weight
change 1.5 and 1.3 percentage points; serum sodium 2.9 and 2.9 mmol/L. Median vomiting episodes
were 2 on the glucose-based solution and 1 on the rice-based solution.

### Conclusion drawn for each outcome

1. **Duration of diarrhoea (primary).** Diarrhoea stopped about 11 hours sooner on the rice-based
   solution, 52.0 h against 63.0 h. Holm-adjusted p = 0.0004, so the difference is supported.
2. **Stool output in the first 24 hours (primary).** Stool output was about 16 g/kg lower on the
   rice-based solution, 68.0 against 84.0 g/kg. Holm-adjusted p = 0.0004, so the difference is
   supported.
3. **Solution intake in the first 24 hours.** Children on the rice-based solution took about
   13 mL/kg less, but the raw p-value of 0.0513 sits just above the 0.05 threshold, so this
   outcome is not called significant.
4. **Vomiting episodes in the first 24 hours.** The group means are 2.05 and 1.95 episodes, a gap
   of one tenth of an episode. Raw p = 0.3694, not significant. The two solutions look
   effectively the same on this outcome.
5. **Weight change at 48 hours.** Children on the rice-based solution gained about 0.8 percentage
   points more of their admission weight, 2.80 % against 2.00 %. Raw p = 0.0111, so this outcome
   is called significant.
6. **Serum sodium at 24 hours.** The means differ by 0.36 mmol/L, well inside laboratory and
   clinical noise. Raw p = 0.5742, not significant.

## Clinical interpretation

On both outcomes the protocol named as primary, the rice-based solution did better. Children
recovered from diarrhoea roughly half a day sooner and passed noticeably less stool in the first
day. Those two results point the same way, which is what one would expect if the rice-based
solution genuinely reduces stool losses: less stool output over the first day and a shorter
illness are two views of the same clinical improvement.

The supporting picture is consistent. Children on the rice-based solution gained slightly more
weight by 48 hours, which fits better hydration in a group that was losing less fluid. They also
drank somewhat less solution, which fits the same story, though that outcome landed just above
the threshold and is not called significant here.

Two outcomes show no separation. Vomiting was essentially identical on the two solutions, so the
rice-based solution neither helped nor hurt on tolerance. Serum sodium at 24 hours was also
effectively the same, and both group means, 137.3 and 137.6 mmol/L, sit comfortably in the normal
range. That matters for safety: the rice-based solution did not push children toward
hyponatraemia or hypernatraemia.

Taken together, these results favour the rice-based solution for young children admitted with
acute watery gastroenteritis. The benefit is on the clinically meaningful outcomes of illness
duration and stool volume, with no signal of harm on vomiting or on serum sodium. The effect
sizes are modest in absolute terms, and this is a single ward with 42 children per group, so
confirmation in a larger setting would strengthen the case.
