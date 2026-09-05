# Multiple-testing Envelope 13 recall recon (2026-08-26)

Status: executed recon only; no detector, adapter, test, registry, qualification, or sealed-envelope
bytes changed.

Detector under study: `code_csv_multiple_testing` 2.2.0 on the development lane. This recon follows
the executed-ladder discipline in `FINDINGS-PLAYBOOK.md` and the artifact format of
`MULTITEST-RECALL-RECON-E12-2026-08-26.md`.

## 0. Provenance and result reproduced

The sealed source is
`evaluation/development/blind-envelope-13-2026-08-26/AUDIT_RESULTS.json`, SHA-256
`dce37ab885bf077ee29692bfe00680ae6d21c1d7ead8559539d62061c200ec76`. Its role map is SHA-256
`456780e6ab2a5decb7c99d31de9a6e898b7f3936e40bf378932aa51e3cda74cb`. The frozen analyzer and
adapter bytes used here are respectively SHA-256
`c34c7ab4872923aeb4271e537905cda9c519646bfa996ad1e99ef149c11cc325` and
`155770410e48a238df81cc87b521c8ac2bf526ce7bdf03c49c372c9bb5da7337`.

The sealed first-contact result reproduced at the real adapter boundary is `3/6`: P1, P3, and P4
are `candidate/none`; P2 abstains `extra-registered-test-outside-authorized-family`; P5 and P6
abstain `authorized-reader-lineage-unavailable`. All three real-source rung-zero executions emitted
zero candidate records and zero Findings. The nine negatives remain noncandidates in the sealed
record.

Executed artifacts are under
`evaluation/development/multitest-recall-recon-e13/`. `h.py` invokes the real development adapter by
running the contract and audit path in an external temporary directory. `ladders.py` constructs each
rung from the sealed source with checked exact replacements; `ladder_results.json` records every
adapter result and source digest. `prototypes.py` contains the two recon-only prototypes;
`sweep_results.json` records the none-flip and movement sweeps. Project-authored code was parsed but
never executed.

## 1. Headline

The two reader misses share one exact idiom:

```python
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
return pd.read_csv(path)
```

P5 assigns the reader result after the same local path binding; P6 returns it. The existing static
path grammar already recognizes the nested `os.path.join(...)` expression by value, but the reader
census applies `_static_path` to the reader's direct argument, the local `Name path`. The resolver's
string lookup does not chase that local computed-path assignment. Inlining only the RHS at the
reader changes both cases from `authorized-reader-lineage-unavailable` to an executed deeper wall.
P2 uses the same local-path idiom, but its earlier `2N` call census hides it.

This wall is also present in three E13 negatives, but only two share the pandas path form: N1 binds
`Path(__file__).resolve().parent / CSV_NAME` to a local Name and N9 uses the same `os.path.join`
shape. N6 uses `csv.DictReader`; it is a different, deliberately unsupported value model and does
not enter the proposed admission.

The proposed next delta has two parts:

1. **D13-A — exact static local reader-path binding.** Resolve one immutable local path Name at a
   recognized reader call through the already-installed `_static_path` grammar.
2. **D13-B — terminal-rendering clone provenance closure.** Match an already-recognized R1 percent
   rendering and already-tagged two-string terminal `IfExp` to its unique p-eligible sink clone by
   source position plus structure. This changes no presentation, threshold, or conclusion grammar.

Together they move P5 to `candidate/strict_subset`, corrected positions `{0,1}` of seven. They do
not admit P2's duplicate test pass or P6's hand `P*3` adjustment. The latter two remain deliberate
residuals.

## 2. Executed mutation ladders

Every row below is an observed real-2.2-adapter result, not an inferred intermediate. Each rung
changes one named construct from the previous rung. Complete canonical output and source hashes are
in `ladder_results.json`.

### 2.1 P2 — cotton density, `c336be2521785ab6a954`

| Rung | Single mutation | Executed adapter result |
|---|---|---|
| P2-r0-real | sealed source | abstain `extra-registered-test-outside-authorized-family` |
| P2-r1-one-family-pass | delete only the second summary-table family pass | abstain `authorized-reader-lineage-unavailable` |
| P2-r2-direct-reader-path | inline only the exact static local path RHS | candidate `none`, `0/6` corrected |

Observed diagnosis: the script contains two complete executions of the same six registered tests,
and both passes make p-derived verdicts. The whole-module census therefore resolves 12 calls for
contract `N=6`; the first reason is exactly the designed `>N` guard. Removing the second pass exposes
the shared path wall; resolving that wall exposes no further one.

Decision: **bin C**. The second pass is not presentation-only: it recomputes every p-value and emits
a second decision branch. Collapsing it would contradict the call-count rule in the 2.0 design
section 3.1, the `performed_count == authorized_count` evidence invariant, and the 2.2 section 9.2
sensitivity ownership. The strongest correct neighbor is a complete corrected family plus a
sensitivity rerun; the same global `>N` guard is its intended protection. A future guard refinement
would require a new evidence/wording policy for `2N` performed calls and its own ADR. This recon does
not propose it.

### 2.2 P5 — hand skin, `80091f37c722eba28e18`

| Rung | Single mutation | Executed adapter result |
|---|---|---|
| P5-r0-real | sealed source | abstain `authorized-reader-lineage-unavailable` |
| P5-r1-direct-reader-path | inline only the exact static local path RHS | abstain `unresolved-manual-correction-present` |
| P5-r2-direct-verdict-rendering | replace only the pure two-string verdict-helper transport with already-admitted direct `If` sinks | candidate `strict_subset`, corrected positions `{0,1}` of `7` |

The second reason does not come from the recognized `multipletests` call: tracing the real engine
showed that call resolves positions `{0,1}` and method `holm`. The stopping node is the R1 percent
rendering containing the transformed, tagged two-string verdict `IfExp`. Expansion cloned the
node, while total sink reachability still compared AST object identity. Matching the already-tagged
node to its unique sink clone by source position clears the wall; the unchanged conclusion census
then credits the same comparison. This is a provenance closure, not presentation-helper inlining
and not a verdict grammar expansion.

Decision: **bin A**, adopting D13-A plus D13-B. P5 then proves two Holm-covered positions and five
raw positions, with complete conclusions over all seven.

### 2.3 P6 — IBS diet, `d0f9fcd52f47e4d64668`

| Rung | Single mutation | Executed adapter result |
|---|---|---|
| P6-r0-real | sealed source | abstain `authorized-reader-lineage-unavailable` |
| P6-r1-direct-reader-path | inline only the exact static local path RHS | abstain `unresolved-manual-correction-present` |
| P6-r2-set-membership | change only the corrected-membership List to a Set | abstain `analysis-scope-structure-unsupported` |
| P6-r3-membership-only-set | remove only presentation-order iteration of that Set | abstain `analysis-scope-structure-unsupported` |
| P6-r4-literal-subset-size | replace only `len(CORRECTED_OUTCOMES)` with literal `3` | abstain `unresolved-manual-correction-present` |
| P6-r5-full-family-factor-control | replace only multiplier `3` with recognized family size `5` | candidate `strict_subset`, corrected positions `{0,1,2}` of `5` |

Observed diagnosis: the read-path idiom is the arrival wall. Past it, the actual correction is
outside the sole manual grammar. The 2.0 design section 4.7 recognizes only
`min(P*N,1)`/`numpy.minimum(P*N,1)` with `N` exactly equal to the authorized family census. The
script's `N_CORRECTED=3` is a proper-subset factor while the contract census is five. The Set rungs
also demonstrate the 2.2 D5 boundary: a Set is a membership oracle only, never an iteration or
general cardinality source. Only changing the scientific multiplier to five reaches the existing
strict-subset recognizer.

Decision: **bin C** after applying shared D13-A. The pinned deeper reason is
`unresolved-manual-correction-present`. Admitting a proper-subset factor would widen correction
acceptance and create new `strict_subset` accusation surface; it is outside this recognizer recon
and requires separate policy/ADR review. This case does not use the four 2.2 section-12 deferred
models (DataFrame p-table, positional-record subset, record-flag fold, or zip write-back), so none
is designed here by proxy.

## 3. Proposed delta grammars

### 3.1 D13-A — exact static local reader-path binding

D13-A adds one backward reader-path edge. It applies only when all conditions hold:

1. The reader call is already accepted by the unchanged reader API/keyword grammar and its sole
   path positional argument is a simple `Name` whose direct `_static_path(Name)` result is
   unresolved.
2. That Name has exactly one `Assign` or closed `AnnAssign` binding in the parsed module. Its RHS,
   without substitution or arithmetic, resolves under the existing `_static_path` grammar to the
   exact contract path. For E13 this means either the exact `os.path.join(os.path.dirname(
   os.path.abspath(__file__)), SAFE_STRING)` form or the already-supported
   `Path(__file__).resolve().parent / SAFE_STRING` form.
3. The Name and every exact identity alias have no rebind, `AugAssign`, `NamedExpr`, `del`,
   attribute/subscript store, mutating receiver call, or unresolved call-argument escape anywhere.
   The one reader argument is the only value-bearing consumer. No helper formal, return frame,
   reader API, keyword, or `None` path is admitted by this clause.
4. Substituting the RHS at that one reader argument yields the same safe relative path bytes as the
   contract. The assignment does not create a reader frame; the accepted reader call remains the
   sole root. Operand identity and row-completeness proofs are unchanged.

The whole-module reader census still sees every reader call. A second reader, different resolved
path, unknown local RHS, multiple binding, mutation, alias escape, or dynamic path abstains under
the existing reasons. The prototype performs only this exact normalization and never unparses or
rewrites unrelated source.

False-accusation analysis:

- E13 N1 is the strongest complete-correction neighbor with a local `Path` binding. D13-A advances
  it only to `correction-family-lineage-unresolved`; it remains a noncandidate.
- E13 N9 is a correct pre-registered `0.01` family threshold with the `os.path.join` binding.
  D13-A advances it only to `unresolved-decision-threshold`; the threshold narrowing still wins.
- A local path that points to a second file remains `additional-accepted-reader-present` or
  `authorized-reader-lineage-unavailable`; D13-A compares resolved bytes to authority and cannot
  turn path existence into operand lineage.
- `csv.DictReader`, including E13 N6, is not a recognized reader and is unaffected.

### 3.2 D13-B — terminal clone provenance closure

D13-B changes zero grammar. It closes identity across normalization clones only when:

1. the node already satisfies the installed R1 literal-percent structural grammar or already
   carries `_sc_mt_terminal_rendering=True` from the installed, closed two-string verdict-helper
   transformer;
2. its comparison already resolves through the unchanged direct-p threshold grammar to exactly one
   family position;
3. exactly one structurally equal clone with the same source start/end position occurs beneath one
   p-result-eligible registered sink payload; and
4. every consumer of the original and clone is accounted by the existing total rendering/sink
   transports. No call, store, container, export, second emission, control, or escape is dropped.

The same resolved clone identity must be used in the off-grammar transform check, hierarchy
exclusion, and conclusion census. Disagreement abstains `unresolved-pvalue-consumer` or
`pvalue-control-dependence-unresolved`; it never defaults to a conclusion. This is the safe
transformer/provenance route emphasized by the 2.2 D4 withdrawal: helper bodies are not generally
inlined and no numeric evidence is manufactured.

False-accusation analysis:

- `correct-terminal-clone-whole-family-bonferroni` executes as `covered/complete`, not a candidate.
- `correct-terminal-clone-preregistered-001-N5` executes as
  `unresolved-decision-threshold`; source-text Decimal/product and the `{0.05}` uncorrected-family
  threshold narrowing are unchanged.
- The existing FA-6 hidden-correction presentation helper remains
  `unresolved-pvalue-consumer`; it never receives the terminal marker required here.
- A helper returning arithmetic, a call, a number/container, two emissions, or a dynamic arm is
  not tagged by the installed transformer and therefore cannot enter D13-B.

## 4. Executed none-flip checks

The sweep ran the baseline, D13-A alone, D13-B alone, and D13-A+B. Each prototype was executed over
the same three mandatory sets. These are analyzer executions with adapter-equivalent frozen
authority/CSV inputs. This is conservative for the none-flip claim because the real adapter can
only add an earlier source-envelope abstention; it cannot turn an analyzer noncandidate into a
candidate. The P2/P5/P6 ladders and the five pinned E13 movement cases were separately re-executed
through the real adapter.

| Prototype | Corpus correct | Opened negatives E10-E13 | Six FA fixtures |
|---|---:|---:|---:|
| D13-A | `0/25` candidates | `0/36` candidates | `0/6` candidates |
| D13-B | `0/25` candidates | `0/36` candidates | `0/6` candidates |
| D13-A+B | `0/25` candidates | `0/36` candidates | `0/6` candidates |

Thus each proposal and their conjunction passed `67/67` mandatory noncandidate executions. Across
the three proposal runs this is 201 noncandidate checks. The baseline also reproduced `0/25`,
`0/36`, and `0/6`.

The six FA outcomes were byte-identical across all four runs:

- FA-2: abstain `unresolved-manual-correction-present`;
- FA-3: covered `complete`;
- FA-3b: abstain `unresolved-manual-correction-present`;
- FA-5: abstain `analysis-scope-structure-unsupported`;
- FA-5b: covered `complete`; and
- FA-6: abstain `unresolved-pvalue-consumer`.

The four targeted E13 attacks in `fa_results.json` also produced zero candidates: the two actual
correct reader-path cases abstained at their designed deeper walls, the whole-family Bonferroni
terminal-clone fixture was covered/complete, and the N=5 `0.01` fixture abstained at the threshold
guard.

## 5. Next-delta pinned expectations

The pin below assumes D13-A and D13-B only. P2's census and P6's manual grammar remain unchanged.

| Miss | Next-delta adapter outcome | Exact reason/classification |
|---|---|---|
| P2 `c336be2521785ab6a954` | abstain | `extra-registered-test-outside-authorized-family` |
| P5 `80091f37c722eba28e18` | candidate | `strict_subset`, corrected positions `{0,1}` of `7` |
| P6 `d0f9fcd52f47e4d64668` | abstain | `unresolved-manual-correction-present` |

Exactly two other opened cases change first reason:

| Case | 2.2 | Projected next delta |
|---|---|---|
| E13 N1 `b7d38f6e9284abfd3ee6` | `authorized-reader-lineage-unavailable` | `correction-family-lineage-unresolved` |
| E13 N9 `ab70cdb37bb2977d725c` | `authorized-reader-lineage-unavailable` | `unresolved-decision-threshold` |

The real adapter re-executed all five rows above with those exact results. Every other opened E10,
E11, E12, and E13 row is projected byte-semantically unchanged. In particular E13 P1/P3/P4 remain
`candidate/none`; N2 remains `unresolved-decision-threshold`; N3 remains
`unresolved-manual-correction-present`; N4 remains
`extra-registered-test-outside-authorized-family`; N5/N8 remain
`test-battery-cardinality-unresolved`; N6 remains `authorized-reader-lineage-unavailable`; and N7
remains `authorized-family-test-census-incomplete`.

## 6. Bin table and considered-but-not-proposed changes

| Miss | Bin | Proposed delta or residual pointer |
|---|---|---|
| P2 cotton density | C | Retain the exact global call-count rule: 2.0 section 3.1 and 2.2 section 9.2. A duplicate-pass policy needs new evidence wording and sensitivity adversaries. |
| P5 hand skin | A | D13-A exact static local reader path plus D13-B zero-grammar terminal-clone provenance closure -> `candidate/strict_subset {0,1}/7`. |
| P6 IBS diet | C | Apply D13-A only, then retain `unresolved-manual-correction-present` under 2.0 section 4.7's exact full-family `N` manual grammar. Proper-subset factors require a correction-surface ADR. |

Two tempting changes are explicitly rejected here:

1. **Do not collapse P2's two passes as one test battery.** The real source executes 12 registered
   calls and two decision emissions. Treating this as six would make current evidence bytes and
   wording false and would weaken the sensitivity guard.
2. **Do not recognize P6's `P*3` as manual family coverage in this recon.** Widening correction
   acceptance can create `strict_subset` candidates. The rung is evidence for a future policy
   review, not authority to change that surface.

## 7. Honest read and arrival economics

The D13-A+B prototype moves **zero of 50** open-corpus rows. The committed 2.1/2.2 corpus replay
therefore stays the byte-identity gate: `0/25` correct candidates and `19/25` misstep candidates.
No replay record should be regenerated for this recon. This is a one-opened-case recall gain, not a
measured improvement on the unbiased corpus estimator.

Retrospectively on E13, the proposed delta changes the opened score from `3/6` to `4/6`; blind
credit remains the sealed `3/6`. The running blind window remains E12 `2/6` plus E13 `3/6` = `5/12`,
so E14 still needs at least `4/6` for the `9/18` bar.

The arrival prior remains conservative. One new path-binding idiom accounted for two positive
misses and three negative first walls in E13, but clearing it catches only P5 because P6 immediately
hits the deliberate manual-correction boundary. Since the corpus score is unchanged and fresh
authors historically introduce new idioms as old ones clear, the planning expectation for E14 is
around the current `3/6`, with high uncertainty—not the answer-visible E13 ceiling of `4/6` and not
a pass prediction. Envelope 14 must report fresh first contact regardless.

## 8. Observed, inferred, and still requiring review

Observed in executed output:

- all ladder outcomes and source digests in `ladder_results.json`;
- D13-A/D13-B individual and combined none-flip counts in `sweep_results.json`;
- zero corpus movements, exactly four combined opened analyzer movements (P5, P6, N1, N9), and
  exact real-adapter replay of those rows plus unchanged P2; and
- all targeted FA outcomes in `fa_results.json`.

Inferred from those executions and frozen grammar:

- D13-A is a reader-path value edge, not a new reader or row-selection grammar;
- D13-B is a clone-provenance repair because both structural tags already exist before the failed
  identity lookup; and
- P2/P6 require policy changes rather than more incidental syntax normalization.

Needs independent design review before build:

- the exact alias-escape and unique-clone proof obligations for D13-A/B;
- whether D13-B should use source position plus canonical structural digest or carry an explicit
  origin token through each transformer; and
- any future duplicate-pass or proper-subset manual-correction policy. Neither is commissioned by
  this recon.
