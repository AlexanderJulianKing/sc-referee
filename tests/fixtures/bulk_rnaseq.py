"""A second study class for the confounder-candidate diagnostic: bulk RNA-seq DE.

Structurally different from GB-P07 on purpose, so the diagnostic is exercised beyond one benchmark:

* FLAT samples, no cells-in-donors nesting (GB-P07 was nested).
* binary treatment exposure (GB-P07 was ordinal genotype dosage).
* the confounder is an UNREAD technical column -- tier 1 -- not a derived quantity (GB-P07's real
  signal was tier 2/3; here tier 1 carries it).
* an NB GLM with a library-size offset and NO additive-reference term (GB-P07 had contamination).

The workflow "source" is what the diagnostic scans: it reads treatment, library_size, and the gene,
and never reads the technical covariates. Ground truth is controlled by the generator so each
scenario's expected outcome can be asserted, not guessed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# What the diagnostic scans. It reads `treatment`, `library_size`, `y`; it never reads rin/batch/age.
WORKFLOW_SOURCE = '''
meta = pd.read_csv("meta.csv")
counts = pd.read_csv("counts.csv")
df = counts.merge(meta, on="sample")
# per-sample library size offset
df["logN"] = np.log(df.library_size)
# NB GLM: gene ~ treatment, offset log library_size
model = fit_nb(df.y, df[["treatment"]], offset=df.logN)
beta_treatment = model.params["treatment"]
'''


def _nb_counts(mu, rng, theta=8.0):
    mu = np.clip(mu, 1e-6, None)
    p = theta / (theta + mu)
    return rng.negative_binomial(theta, p).astype(float)


def make(scenario: str, n=48, seed=0):
    """Return (source, tables, model_spec_kwargs, fit_data, ground_truth) for a scenario.

    Scenarios:
      works       - RIN confounded with treatment and affecting the outcome; unread. Should be found.
      borderline  - RIN weakly confounded; near the detection boundary. Honestly ambiguous.
      blind       - confounder U-shaped in the exposure so Pearson-of-mean ~ 0; genuinely affects
                    the outcome. The documented leg-1 blind spot. Should be MISSED, and that miss is
                    correct behaviour, not a bug.
      clean       - a covariate independent of treatment and outcome. Should NOT be flagged.
    """
    rng = np.random.default_rng(seed)
    sample = np.arange(n)
    treatment = np.tile([0.0, 1.0], n // 2)
    library_size = rng.lognormal(mean=np.log(2_000_000), sigma=0.3, size=n)
    logN = np.log(library_size)

    base = -6.0
    beta_true = -0.6                      # the treatment effect the analysis wants

    # technical covariates: age is always a pure decoy; batch is a benign nuisance
    age = rng.normal(50, 10, n)
    batch = rng.integers(0, 3, n).astype(float)   # unrelated

    if scenario == "works":
        # treated samples processed later -> lower RIN (confounded); RIN raises expression
        rin = 8.0 - 1.5 * treatment + rng.normal(0, 0.4, n)
        rin_effect = 0.5 * (rin - rin.mean())
        gt = {"confounder": "rin", "expected": "found",
              "note": "unread technical column, confounded with treatment, affects outcome"}
    elif scenario == "borderline":
        rin = 8.0 - 0.35 * treatment + rng.normal(0, 1.1, n)   # weak confounding, high noise
        rin_effect = 0.12 * (rin - rin.mean())                 # weak effect
        gt = {"confounder": "rin", "expected": "borderline",
              "note": "weakly confounded, under-powered; the tool should NOT family-wise flag it"}
    elif scenario == "blind":
        # RIN is U-shaped in a 3-level dose: high at the extremes, low in the middle. Pearson(rin,
        # treatment_linear) ~ 0, so leg 1 (mean-Pearson) is blind, even though rin genuinely shifts
        # the outcome and is associated with the dose. This is the documented §3 blind spot.
        treatment = np.tile([0.0, 1.0, 2.0], n // 3)
        rin = 8.0 - 1.2 * (treatment == 1.0) + rng.normal(0, 0.3, n)
        rin_effect = 0.6 * (rin - rin.mean())
        gt = {"confounder": "rin", "expected": "missed_by_leg1",
              "note": "U-shaped in the exposure; Pearson-of-mean is blind by construction"}
    elif scenario == "unmeasured":
        # the real confounder is a LATENT variable in no table and derivable from no code. It biases
        # the estimate, but the diagnostic surfaces only what is materialisable, so it cannot see it.
        # Every MEASURED column here is a pure decoy, independent of the latent confounder. This is
        # the honest hard limit of any data-bound tool: an unmeasured confounder is invisible.
        rin = rng.normal(8.0, 0.5, n)             # decoy
        rin_effect = np.zeros(n)
        latent = 1.0 * treatment + rng.normal(0, 0.3, n)   # confounded with treatment, not a column
        latent_effect = 0.6 * (latent - latent.mean())
        gt = {"confounder": "latent (unmeasured)", "expected": "missed_unmeasured",
              "note": "confounder is not a column and not derivable; no data-bound tool can surface it"}
    elif scenario == "clean":
        rin = rng.normal(8.0, 0.5, n)         # independent of treatment
        rin_effect = np.zeros(n)              # and of the outcome
        gt = {"confounder": None, "expected": "nothing",
              "note": "rin independent of treatment and outcome; must not be flagged"}
    else:
        raise ValueError(scenario)

    lin = (base + beta_true * (treatment / 2.0) if scenario == "blind"
           else base + beta_true * (treatment > 0).astype(float))
    mu = library_size * np.exp(lin) * np.exp(rin_effect)
    if scenario == "unmeasured":
        mu = mu * np.exp(latent_effect)
    y = _nb_counts(mu, rng)

    meta = pd.DataFrame({"sample": sample, "treatment": treatment,
                         "library_size": library_size, "rin": rin, "batch": batch, "age": age})
    counts = pd.DataFrame({"sample": sample, "y": y})
    df = counts.merge(meta, on="sample")

    tables = {"df": df, "meta": meta, "counts": counts}

    model_spec_kwargs = dict(response="y", predictors=("treatment",), target_term="treatment",
                             family="nb", exposure_offset="library_size", additive_reference=None)
    fit_data = dict(y=y, treatment=treatment, library_size=library_size,
                    rin=rin, rin_c=rin - rin.mean(), age=age)

    return WORKFLOW_SOURCE, tables, model_spec_kwargs, fit_data, gt
