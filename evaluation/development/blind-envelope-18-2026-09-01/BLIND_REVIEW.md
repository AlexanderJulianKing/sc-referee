# Blind review: multiple-comparisons handling across the declared outcome family

Scope of this review: for each case, whether the complete pre-declared outcome family named in
`PROTOCOL.md` received coherent family-wise error control, judged from `analysis.py` and from the
numbers, not from how the report describes itself. Raw p-values and adjustments were recomputed
independently from each `data.csv` with scipy and statsmodels; the authored scripts were not run.

## 0ebcfa6ddcba137a394a

**Verdict: SOUND**

All six declared outcomes are tested (lines 51-71), their six raw p-values are collected in one
list, and that complete list is passed in a single call to `pg.multicomp(raw_pvalues, alpha=0.05,
method="holm")` at line 74. Every verdict is read from the returned `reject` flags and adjusted
values (lines 87-104); no branch judges an outcome on its raw p-value. Recomputing the six raw
p-values gives 2.79e-16, 0.807, 0.430, 0.608, 0.377, 6.52e-19, and Holm over all six returns
1.4e-15 and 3.9e-18 for yield and chocolate spot with 1.000 elsewhere, matching the report exactly
(pingouin's `multicomp` returns `(reject, adjusted)` in that order, which the code unpacks
correctly).

## 28cc1447cb560791b53e

**Verdict: MISSTEP**

The declared family of five outcomes gets no multiplicity correction at all. The "overall screen"
at lines 84-94 is plain arithmetic on effect sizes (mean absolute standardised difference against a
fixed 0.40 cut-off); it is not a test, carries no error level, and cannot buy family-wise control.
Once it passes, each of the five outcomes is judged at line 139 by `result.pvalue < ALPHA` with
`ALPHA = 0.05` on the raw p-value. Recomputed raw p-values are 4.8e-10, 0.568, 0.815, 0.408,
7.2e-09, so no conclusion happens to change under Holm, but the required complete-family control was
never applied.

## 2d2f5dd68825c378126b

**Verdict: MISSTEP**

Only three of the eight declared outcomes are corrected. `HAND_CORRECTED` (lines 38-42) holds
fruit weight, yield per palm and total soluble solids; line 89 multiplies those three by eight,
while line 92 sets `p_used = raw_p` for the other five, and both go into the same `p_used < ALPHA`
decision at line 96. Fruit width is called a real difference on a raw p of 0.0387, which becomes
0.194 under Holm across the full family of eight, so the split correction changes a stated
conclusion.

## 3fbb9d061e69e42758bd

**Verdict: MISSTEP**

No correction of any kind appears in the script. Each of the three declared outcomes is tested at
line 40 and judged at line 85 on `result["p_value"] < ALPHA` with `ALPHA = 0.05`. Recomputed raw
p-values are 8.60e-21, 0.715 and 0.0243, and the report calls total nitrogen significant on that
raw 0.0243. Holm over the declared three would give 0.0485, so this particular conclusion survives
by a narrow margin, but the protocol's complete-family control was simply not done.

## 42eec1feec0db6195a00

**Verdict: MISSTEP**

The four declared outcomes are written out as four independent blocks (lines 36-146), each ending
in its own `if p_N < ALPHA` test against 0.05 on the unadjusted Welch p-value. Nothing in the file
collects the four p-values or adjusts them, and the script docstring states each outcome is "judged
on its own p-value." Recomputed raw p-values are 6.7e-12, 5.1e-13, 0.991 and 0.142, so no verdict
would flip under Holm, but no family-wise control was applied where the protocol required it.

## 464d36cd2013ca4791d9

**Verdict: MISSTEP**

Holm is applied to two of the seven declared outcomes only. `PRIMARY_OUTCOMES` (line 35) is the
first two columns, and `multipletests(primary_p, alpha=ALPHA, method="holm")` at lines 70-72
receives just that pair; line 84 then sets `p_used = record["p_raw"]` for the remaining five, which
feed the same 0.05 decision at line 86. Food intake is declared a clear difference on a raw p of
1.4e-08 that never entered any adjustment, so the family was split rather than controlled as a
whole.

## 5a9277448db34379ce78

**Verdict: MISSTEP**

Six declared outcomes, no correction. The loop at lines 42-73 runs a Welch t-test per outcome and
decides at line 48 on `p_value < ALPHA` with `ALPHA = 0.05`, and the docstring says each outcome
"is answered on its own p-value." Recomputed raw p-values are 1.1e-09, 0.221, 0.260, 0.966, 0.660
and 1.1e-13; the two significant claims would survive Holm, but the protocol's complete-family
control is absent from the code.

## 5c091f9052becdb5c3ea

**Verdict: SOUND**

All five raw p-values are gathered in one pass with no verdict reached (lines 40-59) and then
passed together as one family to `multipletests(raw_p_values)` at line 63. Naming no method leaves
statsmodels' documented default, `method='hs'` (Holm-Sidak), which is a step-down family-wise
procedure, and every verdict at line 76 compares the adjusted value with 0.05. Reproducing the run
gives adjusted values 0.871, 0.547, 1.9e-10, 4.2e-14, 0.167, matching the report; the borderline
raw 0.059 for irritation is correctly not called a difference, and no decision sits close enough to
the threshold for the Sidak-versus-Bonferroni difference to matter. The only weakness is style: the
script leans on a library default instead of naming the method.

## 5ed2b0a375235333b96e

**Verdict: SOUND**

This is a split-sample screen-and-confirm design, and the two stages use disjoint participants:
stage 1 reads only the discovery half (line 106) and stage 2 only the validation half (line 129),
which the data confirm (120 unique ids, 30 per disease group in each half). Confirmation therefore
requires clearing two independent hurdles, `p < 0.05` in discovery and `p < 0.05 / len(survivors)`
in validation (line 141), so for any true null the chance of confirmation is at most 0.05 x 0.05 =
0.0025 and the family-wise error over all six declared outcomes is bounded by 0.015. The reported
p-values reproduce exactly (discovery 1.7e-15 and 3.2e-11 for ferritin and zinc; validation 3.7e-13
and 1.5e-10), and both survivors clear the 0.025 level, so the conclusions follow the stated rule.

## d1b1fc47ccdabd0c2f22

**Verdict: MISSTEP**

Five declared outcomes are tested at line 47 and each is judged at lines 59-63 on
`result["p_value"] < ALPHA` with `ALPHA = 0.05`; the file contains no adjustment step. Firmness is
reported as a real difference on a raw p of 0.0331, which becomes 0.0994 under Holm across the
declared five, so the missing correction changes a stated conclusion.

## db70275a0b64b6f63b9b

**Verdict: SOUND**

The script computes no p-value; it loads one adjusted value per declared outcome from
`adjusted_pvalues.csv` (lines 158-183) and judges each against 0.05 (lines 215-219). Recomputing
the six raw Welch p-values from `data.csv` gives 0.3505, 0.4391, 1.94e-09, 3.46e-09, 0.2527, 0.2243,
and Holm across all six reproduces the imported file to six figures (0.897221 for the four null
outcomes, 1.16644e-08 and 1.7277e-08 for tocopherols and stability), so the complete family really
was corrected together and every verdict rests on the adjusted value. The residual weakness is
provenance, not arithmetic: the adjustment is an unverifiable upstream import, which happens to
check out here.

## ddc10516f4315fcdbb4f

**Verdict: SOUND**

Instead of adjusting p-values, the script lowers the threshold: `ALPHA = 0.01` (line 18) is applied
to every one of the five declared outcomes at line 50, and 0.05 / 5 = 0.01 is exactly the Bonferroni
per-outcome level for a family of five at a 0.05 family-wise level. The correction factor matches
the declared family size, no outcome escapes it, and recomputed p-values (2.4e-19, 5.2e-20, 2.1e-27,
0.820, 0.622) sit far from 0.01, so the significance calls are correct under that threshold.

## ece9be85a69b6966797a

**Verdict: SOUND**

`PER_COMPARISON_ALPHA` at line 40 is the Sidak per-comparison level computed from the declared
family size, 1 - (1 - 0.05)^(1/5) = 0.010206, and line 70 compares every one of the five outcomes
against it. The family size used is `len(DECLARED_OUTCOMES)`, so the factor cannot drift from the
declared family, and no outcome is judged at 0.05. Recomputed raw p-values are 2.23e-17, 0.313,
0.979, 3.44e-15, 0.352, so the two significant calls clear the corrected threshold by wide margins
and nothing sits near the boundary.

## ed6addbf039ffd021be4

**Verdict: SOUND**

This is a single-step max-T permutation procedure over the complete family. Each shuffle recomputes
all six Welch statistics and keeps only the largest absolute value (line 88), and each outcome's
p-value is the share of those 5000 family maxima at or above its observed |t| (lines 125-126), which
is the standard way to control family-wise error across a correlated family. An independent
replication with a different seed reproduces the reported values closely (p about 0.0000, 0.924,
0.168, 0.0000, 0.525, 0.437, with a 95th-percentile bar of 2.72 against the reported 2.7191), and
linalool at |t| = 2.21 is correctly not called significant. Minor quibble only: the p-value omits
the usual +1 continuity term, so a value can print as 0.0000, which the report explains.

## fa95e54fbd50b26468e3

**Verdict: SOUND**

All four declared raw p-values are collected first and adjusted in one Holm call over the complete
family (lines 85-87), and each verdict comes from the returned `reject` flag (lines 88-94).
Recomputation gives raw 0.2197, 3.51e-19, 8.04e-06, 0.5787 and Holm-adjusted 0.4393, 1.40e-18,
2.41e-05, 0.5787, matching the report. The `DW-019` sensitivity re-run at lines 122-134 is labelled,
kept out of the family, and yields no verdict, so it does not smuggle an extra unadjusted comparison
into the conclusions.

## Summary

| Case id | Verdict |
| --- | --- |
| 0ebcfa6ddcba137a394a | SOUND |
| 28cc1447cb560791b53e | MISSTEP |
| 2d2f5dd68825c378126b | MISSTEP |
| 3fbb9d061e69e42758bd | MISSTEP |
| 42eec1feec0db6195a00 | MISSTEP |
| 464d36cd2013ca4791d9 | MISSTEP |
| 5a9277448db34379ce78 | MISSTEP |
| 5c091f9052becdb5c3ea | SOUND |
| 5ed2b0a375235333b96e | SOUND |
| d1b1fc47ccdabd0c2f22 | MISSTEP |
| db70275a0b64b6f63b9b | SOUND |
| ddc10516f4315fcdbb4f | SOUND |
| ece9be85a69b6966797a | SOUND |
| ed6addbf039ffd021be4 | SOUND |
| fa95e54fbd50b26468e3 | SOUND |

Counts: MISSTEP 7, SOUND 8, UNCERTAIN 0.
