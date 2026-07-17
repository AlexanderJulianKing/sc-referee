# sc-referee — the coverage boundary (what it catches, what it can't, and why)

**Living doc. Last updated 2026-07-11.** The honest account of sc-referee's reach. If a claim here drifts
from the code, fix the claim. Companion to [backlog](planning/backlog.md) and the empirical
[GeneBench error-class map](research/2026-07-11-genebench-error-classes.md).

## The one-sentence thesis

Coverage is bounded by **which decision-types have a check** — not by how clever the referee is. GB-P07's
answer-changing error (a latent contamination batch confounded with genotype) was *invisible* to sc-referee
until we built the check for it, and it was invisible not because the arithmetic was hard but because nothing
in the tool was *looking at that decision*. Every gain in coverage is a new decision-type brought under a
witnessed or ratified check. There is no general "catch bad analyses" move; there is only the accumulating
set of decisions we can either **prove**, **surface for ratification**, or **honestly decline**.

## The prime directive that shapes everything

**Specificity = 1: never false-accuse a correct analysis.** This is not one goal among several; it is the
constraint that determines the *shape* of every check. A referee that occasionally cries wolf on a correct
analysis is worse than useless to a working scientist — one false accusation destroys trust in all the true
ones. So wherever the referee cannot *prove* a defect, it must **abstain and say so**, never guess. Abstention
is a first-class, honorable output, rendered `not_checked` — not a failure of the tool.

This is why the interesting design question is never "can we flag X?" It is "can we flag X **without any
path to false-accusing a correct analysis that merely looks like X?**" The answer to that question sorts every
candidate check into one of three tiers.

## The three tiers of what a check can be

### Tier A — autonomous witnessed catch (thin slice)

The referee can render a verdict **by itself**, because the defect is a matter of **arithmetic, geometry, or
estimability** that is decidable from the confirmed inputs alone. No opinion, no causal judgment — a
recomputable or pure-algebra fact with an immutable witness.

- **Examples in the tool:** the `confounding` estimability BLOCKER (target aliased with a nuisance,
  R²=1 — no model can separate them; power-independent); the `confounding` omitted-variable MAJOR on a
  *named*, ratified-omitted, materially-associated batch (P01's shape); the matrix-version domain algebra;
  the calibration/scale contracts; **`confounding_strong`** (the fixed-effect column-space certificate — does
  the analyst's actual fitted design span the declared batch?).
- **Why it's thin:** very few answer-changing errors reduce to a fact the referee can decide *without* knowing
  something only the analyst knows (the intended estimand, the causal role of a variable, whether a step was
  done upstream). The moment a verdict needs one of those, it leaves Tier A.

### Tier B — witnessed proposal for ratification (the bulk; the actual product)

The referee can **surface the decision and the arithmetic**, but the verdict turns on a fact that is
**not decidable from the data** — the causal role of a variable, the intended target population, whether
between-batch differences must be removed without relying on random-effect exogeneity. For these, the referee
computes and displays the witness (the association, the geometry, the mismatch), asks the analyst to **ratify**
the load-bearing fact **once**, and then lets deterministic arithmetic decide. **No LLM in the verdict.** The
LLM only *proposes structured facts* (column names, closed enums, evidence locations — never a formula); a
human confirms; the arithmetic renders the verdict.

- **This is where most in-domain value lives.** The causal-contract wizard (task C) *is* the product here.
- **Examples on the roadmap:** latent-confounder v3 (the GB-P07 chain); the random-intercept/Hausman adverse
  verdict (task B — "your only adjustment for this confounded batch is a random intercept, which is
  partial-pooling, not projection"); target-population/standardization.
- **The soundness of every Tier-B verdict rests entirely on the ratification being *meant*.** See below.

### Tier C — honest abstention (large slice)

The referee **declines**, and says why. Either the decision-type has no check yet, or the only sound answer
requires a full domain recompute the referee doesn't do, or the question is **causally undecidable** from the
folder no matter what. Rendered `not_checked` (`NOT_AUDITED` = benign / out-of-scope, or
`NEEDS_EVIDENCE + coverage=NOT_RUN` = we need one input from you).

- **Examples:** recompute-heavy domain modeling (HMM founder reconstruction, Wright-Fisher selection, MVMR
  scaling, Hi-C background models, tract-timing); causal **mediation / target attribution** (P09 — transcript
  vs locus — the same undecidability wall as a latent confounder); anything where the confirmed inputs simply
  don't pin the answer.

## Why the wall exists: causal undecidability

The reason Tier A is thin and Tier B needs a human is not engineering laziness — it is a real identifiability
wall. **Confounder, mediator, consequence, and chance-imbalance are observationally identical.** A variable Z
associated with both the exposure and the outcome could be a confounder (adjust for it), a mediator (adjusting
*destroys* the effect you want), a downstream consequence (adjusting induces collider bias), or a chance
imbalance in a valid randomization (adjusting is optional). **The data cannot tell these apart.** Therefore any
detector that *autonomously accuses* on this structure is unsound — it will false-accuse the mediator case and
the valid-randomization case. The only sound move is to **surface the association and ask the analyst which
role Z plays** — which is exactly Tier B. This is the lesson that reshaped the latent-confounder round from an
"accusing detector" into an "abstention-only propose-for-ratification" check.

## The load-bearing risk of Tier B: ratification integrity

Tier B trades an *undecidable* question for a *human-answerable* one. But that trade is only sound if the human
answer is genuinely **meant**. The facts we elicit are sophisticated — "is Z a confounder or a mediator?",
"must batch differences be removed without relying on random-effect exogeneity?", "is the estimand
population-average over these census strata?" A non-expert analyst who *rubber-stamps* a jargon question
converts a careful abstention into a **false accusation** — the cardinal sin, now laundered through a
confirmation dialog. So the wizard (task C) is not UI polish; it is a **soundness component**. Its discipline:

- **Abstention is the default.** A flag requires an affirmative, comprehensible, in-domain confirmation.
  Silence / "not sure" / low-confidence / skipped → abstain, never flag.
- **Questions are posed in the analyst's own terms,** not econometric jargon, with the *consequence* of
  ratifying made transparent ("confirming this may flag your analysis").
- **"Not sure" is a first-class answer** that routes to abstention.
- **A bare `batch` (or any low-confidence) declaration never stands in for a sophisticated obligation.**

## Mapping the GeneBench-Pro public set onto the tiers

From the [error-class map](research/2026-07-11-genebench-error-classes.md) (Opus passed 2/10; the 8 failures
are the material). The recurring in-domain classes, by tier:

| Class | Problems | Tier | Status |
|---|---|---|---|
| Confounding — **named** nuisance omitted | P01 | **A** | ✅ existing `confounding` MAJOR |
| Confounding — fixed-effect **geometry** (span, not names) | (general) | **A** | 🔨 `confounding_strong` (in build) |
| Confounding — **latent** contamination axis | P07 | **B** | 🧊 latent-v3 (spec GO, blocked on infra) |
| Confounding via **random-intercept** on a confounded batch | (ubiquitous in scRNA) | **B** | 🔨 task B (spec critiqued; Stage-2 gated on C) |
| **Target-population / denominator / standardization** | P08, P04, P03 | **B** | ⬜ *strongest next candidate* — sound w/o a causal contract |
| **Selection / ascertainment weighting** (IPW/IPTW/IPCW) | P03, P04 | **B** | ⬜ fold into target-population |
| **Inclusion-set / exposure-definition** | P08, P04, P09 | **B** | ⬜ inclusion-set (draft; needs lineage) |
| Label / **orientation** | P10, P01 | **A/B** | existing `allele_orientation` family; rarer than expected |
| **Background / normalization** model | P06, P07 | **A/C** | partial (Hi-C vertical); else recompute-heavy |
| **Mediation / target attribution** | P09 | **C** | abstention — same undecidability wall |
| Recompute-heavy domain modeling | P01(HMM), P05(WF), P02(MVMR), P10(tracts) | **C** | out of scope by design |

**Two strategic reads fall out of this table:**

1. **Confounding is the single most common failure across the benchmark** — but its *sound, cheap* form is the
   **named / geometric** one (Tier A, P01 and `confounding_strong`). The *latent* form (P07) is a genuine
   multi-part Tier-B build.
2. **Target-population / standardization is the strongest next investment.** It recurs (3 problems), it is
   arithmetic-witnessable, and it is **sound without a causal contract** — because the correct target
   population is a *declared estimand fact*, not an inferred causal role. It sidesteps the exact undecidability
   wall that makes latent-confounding hard. This is the clearest "more coverage per unit of soundness risk"
   move on the board.

## What sc-referee catches **today** (Tier A, shipped)

- **Estimability BLOCKER** — target perfectly aliased with a nuisance; power-independent; re-run required.
- **Named omitted-variable MAJOR** — a ratified-omitted, materially-associated batch (partial R² ≥ cut).
- **Fixed-effect conditioning geometry** (`confounding_strong`, in build) — does the analyst's *actual fitted
  design* span the declared batch, by column space (not by name)? Certified / not-certified / abstain.
- **Matrix-version domain algebra**, **calibration/scale contracts**, and the **validation scorecard**
  (false-alarm count held at 0 — the specificity floor, measured).

## The honest limits (the abstention frontier)

sc-referee will **not** catch, and will abstain on:

- **Atlas-scale sparse ingestion (ING-13).** AnnData sparse matrices are currently densified at the
  `Bundle.Measure` boundary because the shipped recompute engines require an ndarray. Safe sparse support
  requires a matrix-contract and engine architecture change; this phase does not add a memory heuristic
  that could unpredictably accept or refuse the same scientific input.
- **Upstream-corrected data it can't independently verify.** A high-confidence declaration that a load-bearing
  batch was handled upstream (ComBat-seq, Harmony, scVI, regress-out, or another operator) makes both fixed-
  design confounding layers abstain for the whole check: `batch corrected upstream — a design-matrix check
  cannot verify it`. This prevents a false omission accusation. The sensitivity cost is explicit: if another
  batch was genuinely omitted, this pass does not partition that fixed-design accusation from the invisible
  upstream operator.
- **Only additive identity fixed effects are reconstructed.** `ordinary_fixed_effects` means an intercept plus
  additive, identity-coded declared sources. Interactions, products, transforms, weights, offsets, and general
  submitted model matrices are unsupported and return `not_checked`; they are never forced into an additive
  certificate.
- **Below-cut confounding is association-only.** A PASS says only that the measured conditional exposure–batch
  association is below the frozen policy cut. It does not measure batch effects on outcomes, establish absence
  of bias, or rule out omitted variables. Outcome-aware adjudication from ERCCs, negative controls, or
  sensitivity fits remains outside coverage.
- **Target-population selection (HC-4) is not shipped.** The referee has no autonomous universe or target-
  population check. A future implementation requires an explicit ratified population contract; this pass does
  not infer the intended population from observed outcomes or labels.
- **Causally-undecidable roles** — mediator vs confounder vs consequence vs chance. Surfaced for ratification,
  never autonomously accused.
- **Recompute-heavy domain modeling** — HMM/founder reconstruction, selection coefficients, MVMR scaling,
  Hi-C background, tract timing. Out of scope; a specialized recompute, not a referee.
- **Anything the confirmed inputs don't pin.** Missing evidence is `not_checked`, never a warning-as-flag.

## Trust boundary

`sc-referee.yaml` is a **trusted analyst assertion**. The wizard is the intended authoring and confirmation
path because it presents closed choices, exact consequences, and non-authorizing “not sure” routes. The loader
does not require wizard provenance, however: a person can hand-author the same closed YAML assertions.

Confirmation stores a canonical integrity digest over verdict-driving design, role, confidence, CSP, threshold,
and reported-claim semantics. Later semantic drift invalidates that authority while formatting-only changes do
not. CSP provenance fields—evidence locations, presentation/answer/confirmation events, actor, and timestamp—make
a fabricated record visible and auditable. They do **not** cryptographically prove who authored it, that the
assertion was true, or that the wizard created it. There is intentionally no provenance token, HMAC, secret,
RBAC layer, or wizard-only loader in this trust model.

## Numerical decision boundary for partial R²

The reported partial-R² point estimate is unchanged. Its materiality decision uses numeric policy
`partial-r2-decision-v2`: an error envelope of 64 float64 machine epsilons with a 64× safety margin, giving
epsilon `9.094947017729282e-13`. A computed value within `0.01 ± epsilon` is
`indeterminate_near_cut` and every consumer renders `not_checked`, while retaining the measured point value in
metrics. This band covers the realistic 80-sample 22/18-versus-18/22 table whose exact partial R² is 0.01 but
whose float64 least-squares value is `0.009999999999999454`. Values such as 0.009 and 0.011 remain ordinary
immaterial/material decisions. No broader scientific ambiguity band is implied.

## Confirmed scientific premise boundary

The between-group adjustment teach-back requires **exact fixed-effect-equivalent projection**. A random
intercept never satisfies that obligation, however close its estimates appear, and a tolerance-level fixed-
effect sensitivity is not equivalent. Choosing “my sensitivity at tolerance is sufficient” is explicitly
non-authorizing and routes the consumer to `not_checked`; variance components and sensitivity outcomes are not
consumed.

## Positioning

The LLM analyst (Claude Science) is the *proposer* — it reads the directory, does the analysis, and can
*suggest* what to check. sc-referee is the **deterministic external referee**: it never runs an LLM in a
verdict, it proves what it can (Tier A), it surfaces-and-ratifies what it can't prove but can witness (Tier B),
and it **abstains honestly** on the rest (Tier C). Its value is not breadth of accusation; it is a **specificity
floor you can trust** — every flag is arithmetic, every abstention is honest, and a correct analysis is never
told it is wrong. That trust is the whole product, and it is why the tier discipline is not negotiable.
