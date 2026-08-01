# Experiment 0016: Static method-shape and causal repair probes

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Governing decisions:** Accepted ADR-0017 and ADR-0018
- **Corpus ceiling:** Public development; not held out, qualification eligible, or promotion eligible
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged

## Purpose

Test whether Experiment 0015's proposed failure descriptions identify the exact submitted source
shapes and whether the corresponding method repairs recover the released answers. The experiment
must not execute or import the submitted workflows, mutate their frozen audits, infer production
scientific intent from an answer key, or promote an evaluation mismatch into a Finding.

## Closed evaluation-only source profiles

The evaluation package adds `probe-python-method-shapes`, a Python-AST-only diagnostic with four
closed profiles:

1. `directional_measurement_error_v1` compares distinct direction-specific misclassification rates
   with one average rate applied symmetrically;
2. `phased_composite_marker_v1` compares an all-marker, same-nonmissing-phase obligation with a
   submitted either-single-marker or same-phase-pair expression;
3. `mutually_exclusive_class_calibration_v1` compares a joint shared-noncarrier multiclass
   calibration obligation with independent per-class binary inversion; and
4. `cellwise_calibration_before_standardization_v1` compares calibration inside each target-
   population cell before weighting with raw-positive-rate weighting followed by aggregate
   calibration.

Each profile returns only `exact_static_conflict`, `covered_negative`, or `unsupported_path`. The
diagnostic binds the complete source digest, exact AST spans, closed profile-manifest digest,
answer-side reference identity and digest, and a self-digest. It states that static source does not
prove execution, answer-side evidence does not establish production intent, and static conflict
does not by itself establish numeric causality. It invokes no model, executes no submitted source,
is metric- and promotion-ineligible, and cannot produce a production Finding.

## Exact source results

The probes were run against the unchanged Experiment 0015 workspaces after semantic lock.

| Case | Source digest | Probe and diagnostic digest | Result |
|---|---|---|---|
| `wf_selection` | `sha256:b63ebd40b214725e3df81fcc70b3d3514f86e2bea84a46463957bfcfe2fe36a2` | `evaluation-python-source-method-probe:0420ac2d603dfefc2d1d`; `sha256:a2100a0bad6d2dc4d3f29c758fa2dcabcb4bcb183150ac1a8d802380262bd5e1` | Exact symmetric-average conflict at `analyze.py:110` and `analyze.py:114`. |
| `carrier_cnv_pseudogene_residual_risk` | `sha256:cc7cb70aca4a6d60d1ce02a7bf0198a1ec2ab43958563735268eecceb3c8eacc` | `evaluation-python-source-method-probe:bc447695a881be1e08d0`; `sha256:c523b9069118d8ce001775a4c39718ebe9b3ae9de1474d1e026e5a3eb942d7bc` | Exact phased-marker conflict at lines 94–98, independent-calibration conflict at lines 107–117 and 217–220, and aggregate-before-calibration conflict at lines 285–321. |

The positive fixture copies the exact submitted source shapes. The corrected control uses two
directional error rates, all markers on one nonmissing phase set, one joint nonnegative class
solver, and calibrated within-cell values before weighting. All four positives localize, all four
corrected controls produce `covered_negative`, unrelated code stays `unsupported_path`, and
duplicate profiles, unknown profiles, unsafe paths, symlinks, and existing outputs fail closed.

## Numeric causal checks

### Directional measurement error

Experiment 0015's full-digest answer-side report already supplies an exact ablation. The submitted
symmetric formula gives `s = 0.063559`, matching the submitted `0.0636`; substituting the declared
directional rates `0.31` and `0.01` in the same Wright–Fisher emission gives `s = 0.101255`, matching
the released `0.101256`. This establishes numeric causality for this fixed public-development case,
not a production obligation.

### Carrier call, coupled calibration, and cellwise order

A separate evaluation-owned reconstruction read the five full-digest TSV inputs but did not import
or execute `analysis.py`. The reconstruction retained the submitted sequence and CNV call shapes
only where their fixed-data detected counts already matched the reference, changed the founder call
to require both high markers on the same nonmissing phase set, solved

`q_k = p_k s_k + (1 - sum_l p_l) f_k`

with a nonnegative active set, and compared calibration after raw-rate weighting with calibration
inside each partner cell. The evaluator script digest was
`sha256:42ec4c48b4938a80e86e2a195fbc7652073a5c86eba6ad11b192bf3aa6ee7140`.

The corrected founder definition changed the submitted cohort founder positive rates from
`0.0125` to `0.0075` for AFR and from `0.04` to `0.0325` for EUR. Its control sensitivities became
the reference values `0.733333` and `0.833333`. With those calls:

| Reconstruction stage | AFR total or residual | Partner full-roster frequency | Couple risk |
|---|---:|---:|---:|
| Independent per-class calibration | carrier total `0.096280`; residual `0.037477` | aggregate-after-weighting `0.253358` | not treated as corrected |
| Coupled calibration after raw-rate weighting | carrier total `0.100298`; residual `0.039644` | `0.263249` | not treated as corrected |
| Coupled calibration inside each cell, then weighting | carrier total `0.100298`; residual `0.039644` | `0.2792493901` | `0.0027676607` |

The last row reproduces all five released values: AFR `0.1002983313`, EUR `0.0772984133`, residual
`0.0396442862`, partner `0.2792493901`, and couple `0.0027676607`. Therefore the permissive founder
call, uncoupled calibration, and the evaluator's cellwise constrained-estimation choice all differ
from the submitted source; the complete three-part change recovers the fixed-case target.

**Later correction from Experiment 0025:** the last contrast is not step order alone. The
inside-cell reconstruction uses a nonnegative active-set solver, while the aggregate reconstruction
uses one fixed linear mapping. A fixed linear inverse commutes with weighted averaging. The
`0.263249` versus `0.279249` difference therefore contrasts aggregate joint inversion with
nonnegative constrained estimation inside each post-stratum. The public task does not establish
which estimator is scientifically governing, and the released answer is not production intent
authority. The legacy evaluation-only profile name remains an immutable description of the
original fixed-case probe, not permission to report an order-only issue.

## Acceptance evidence

- **Change:** one evaluation-only, no-execution Python source diagnostic and CLI with four closed
  profiles.
- **Tests:** `tests/test_evaluation_source_method_probe.py` covers all four exact positives, all
  four corrected controls, unsupported code, CLI persistence, duplicate/unknown profiles, path
  traversal, symlink rejection, and write-once output.
- **Acceptance criterion satisfied:** each proposed failure description localizes the exact
  submitted source span, rejects a closed corrected form, preserves unknown source shapes, and
  remains incapable of issuing a Finding or executing the workflow.
- **Remaining coverage limitation:** the profiles recognize a narrow Python grammar, have only one
  public-development positive each, and use answer-side obligations. They do not establish what
  ran, infer a method obligation in an undocumented repository, cover equivalent refactorings,
  qualify a detector, or prove broader scientific correctness.

## Decision

The proposed errors are real and repair-relevant, so they remain viable experimental detector
candidates. They are not added to the production detector manifest or capability matrix. The next
step is to seek independent recurrence and hard negatives for these exact abstract obligations,
not to broaden the AST grammar or publish a production Finding rule from these two cases alone.
