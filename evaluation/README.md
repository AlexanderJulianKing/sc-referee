# sc-referee evaluation package

This is the isolated answer-side package for benchmark and detector-qualification evidence. It may
depend on the production `sc-referee` record validator; the production package must never import
this package.

The first slices reconcile a `BenchmarkFixture`, `BenchmarkAdjudication`, and their exact linked
`AgentReview` panel; resolve full-digest file-span evidence against an immutable fixture snapshot;
persist a canonical validation report through `sc-referee-eval`; and construct an allowlisted blind
review workspace after exact path, digest, multi-encoding marker, declared-hidden-content, and
symlink checks.

Digest-bound Stage-1 and Stage-2 packet APIs enforce independent contexts, the 2x2 plus 1x2
cross-provider panel, falsification records, and a scientific-label freeze that precedes any
detector comparison. The same artifact operations are available without model invocation through:

```text
sc-referee-eval build-workspace ...
sc-referee-eval preflight-genebench-public ...
sc-referee-eval prepare-genebench-public-case ...
sc-referee-eval stage1-packet ...
sc-referee-eval capture-review ...
sc-referee-eval freeze-stage1 ...
sc-referee-eval stage2-packet ...
sc-referee-eval reconcile-root-cause ...
sc-referee-eval freeze-label ...
sc-referee-eval replay-label-freeze ...
sc-referee-eval compare-stage3 ...
sc-referee-eval grade-json ...
sc-referee-eval grade-genebench-public-numeric ...
sc-referee-eval grade-genebench-public-answer ...
sc-referee-eval probe-python-method-shapes ...
sc-referee-eval generate-ambiguous-fixture ...
sc-referee-eval generate-positive-fixture ...
sc-referee-eval generate-control-fixture ...
sc-referee-eval freeze-static-profile ...
sc-referee-eval verify-static-case ...
sc-referee-eval freeze-analysis-method-static-profile ...
sc-referee-eval assign-analysis-method-static-case ...
sc-referee-eval verify-analysis-method-static-case ...
sc-referee-eval freeze-typed-method-static-profile ...
sc-referee-eval assign-typed-method-static-case ...
sc-referee-eval verify-typed-method-static-case ...
sc-referee-eval replay-typed-method-static-case ...
sc-referee-eval generate-static-control-fixture ...
sc-referee-eval stage3-packet ...
sc-referee-eval reconcile-stage3 ...
sc-referee-eval calculate-metrics ...
sc-referee-eval validate-case ...
```

Every output path is write-once. `capture-review` stores exactly one canonical review, its packet,
the digest-matching transcript bytes, and a self-digested capture manifest. CLI panel freezes and
Stage-2 packet construction consume those verified capture directories rather than loose review
JSON. The CLI constructs and validates protocol artifacts; it does not invoke reviewers, execute
project code, authenticate transcript authorship, or independently prove reviewer independence.

`reconcile-root-cause` deterministically constructs an exact public `AdjudicatedRootCause` from a
closed Stage-1/Stage-2 panel, and `freeze-label` admits a positive label only after those records and
all declared source evidence validate. `replay-label-freeze` reconstructs that freeze byte-for-byte
without model access. Admission is limited to the declared fixture scope; it is not a detector
score, a production Finding, or a correctness certificate.

`compare-stage3` is an observation-only experimental boundary. It binds one exact public
AuditBundle to the already frozen scientific label and records exact result/Finding scope, but it
does not classify detector-to-root-cause equivalence or contribute qualification metrics.

`grade-json` is the first non-executing grader experiment. It reconstructs an immutable
content-addressed snapshot manifest, resolves one strict JSON Pointer, and observes exact canonical
value match or mismatch. It emits value digests and explicit non-inferences; neither outcome is a
scientific label, detector metric, or Finding.

The fixture generators now emit public-development ambiguous, positive, verified-good,
scope-verified-good, and hard-negative records under the accepted v0.12.0 proof contract. Accepted
v0.15.0 additionally permits distinct static-scope verified-good and hard-negative records only
after `freeze-static-profile` and `verify-static-case` bind and independently replay the exact
bounded direction-detector closure. Accepted v0.16.0 adds a separately discriminated
`bounded_analysis_method_conflict_v1` profile. Its independent verifier rederives the selected
Markdown report operand, the Python source operand and unique literal report writer, and the exact
scope-bound human Question, Answer, ScientificContract, and accepted requirement assertion. It does
not reuse the production parser, adapter, detector, or semantic-fact helpers. These commands read
immutable bytes but never import or execute the inspected project. Unsupported, ambiguous,
weak-identity, over-budget, or mutated cases remain unavailable rather than becoming controls.
Those v0.16 commands remain a historical replay surface for detector v0.1.0.

Accepted v0.17.0 adds the current `typed_static_method_conflict_v1` profile for detector v0.2.0.
The typed CLI freezes one exact content-addressed method binding and explicitly registered
independent adapter, creates an opaque assignment without a scientific label or detector output,
independently verifies retained bytes and human authority, and byte-replays the resulting proof.
It does not discover ambient adapters or execute inspected code. Experiment 0027 freezes the
current pre-case profile and prompts but contains no assigned case, reviewer identity, transcript,
threshold, metric, qualification, or promotion claim.

Complete fixtures bind exact captures, packets, transcripts, workspaces, snapshot chronology, public
records, and source-validation evidence. Clean controls additionally require an already supplied
successful authorized project-workflow Execution with a qualifying rootless-OCI
SandboxCapability. Fixture generation validates those records but never launches project code.

`preflight-genebench-public` is an evaluation-private, non-executing inventory for an already-local
pinned public case-study package. It verifies the closed manifest/checksum/config contract, emits no
ground-truth values, keeps grader/config/report material runner-side, and fixes every case to
`public_development`. The pinned official initial revision has consistent CC-BY-4.0 identifiers and
passes all 77 checksums; the current MIT-labelled head is rejected because its checksum inventory
is stale. Preflight never grants redistribution. Public ground truth also makes these cases
ineligible for held-out promotion evidence.

`prepare-genebench-public-case` reruns that exact preflight, derives one task and its declared data
allowlist, snapshots the visible and runner-only source material, and applies the existing blind
workspace scanner. Only its `workspace/` subdirectory is agent-eligible; config, canonical ground
truth, reference grader/report, snapshot materialization, and receipts remain runner-side. The
command invokes neither a model nor project-authored code. Experiment 0012 records the exact
boundary and its first real public-development case preparation and independent agent run.

`grade-genebench-public-numeric` is Experiment 0013's closed answer-side comparison. It verifies a
terminal audit, semantic lock, report/storage/SQLite integrity, the full-digest `answer.json`
snapshot identity, and the exact package preflight before reading a supported single- or multi-key
absolute-tolerance contract. `grade-genebench-public-answer` additionally supports the two exact
encountered composite forms: required case-sensitive strings plus bounded numerics, or exact JSON
integers plus numerics. Unknown fields and comparison shapes fail closed. Neither command imports
or executes the reference grader, and each emits a self-digested public-development grade that is
ineligible for Findings, metrics, held-out status, or promotion. A mismatch establishes neither a
production Finding nor its scientific root cause.

`probe-python-method-shapes` is an evaluation-only Python-AST inspection. Experiment 0016 defines
four named closed profiles; Experiment 0019 adds three fixed-workspace profiles for founder
orientation before HMM emission, full-map ancestry exposure, and LD-covariance whitening before a
robust fit. The command preserves unrecognized forms as `unsupported_path`, imports and executes no
submitted source, and cannot create a Finding or qualification evidence. Experiment 0017's three
targeted follow-up workflows were unsupported by all four original profiles, so none was broadened
or promoted. The three Experiment 0019 profiles remain one-case public-development adapters rather
than production capabilities.
Experiment 0018 applies the same four profiles to the three remaining public workflows; all twelve
results are again `unsupported_path`. Its grader `0.4.0` extension accepts only a declared
minimum-only range in the existing multi-key numeric profile and continues to reject a
maximum-only range or broader comparison grammar. The expanded profile is versioned
`genebench_multi_numeric_absolute_tolerance_v3`; new stable grade IDs bind that profile and the
grader version, and historical `v2` records are not rewritten.

`compile-posthoc-validation-review` is Experiment 0019's evaluation-only Answer-binding compiler.
It verifies one immutable source-probe digest and one exact case-scoped human Answer before calling
the production post-hoc ledger core. Structured values must equal the selected closed profile's
expected form and use an allowed existing ScientificContract dimension. An unknown Answer must not
name a profile, dimension, comparison form, or value. Outputs are canonical, write-once, replay-
equivalent, and explicitly Finding-, metric-, held-out-, and promotion-ineligible. The fixed QTL
and pulse-admixture reviews produce exact conflict candidates, MVMR produces a covered negative,
and CRISPRi/CasRx remains unresolved. These records establish neither execution nor historical or
universal scientific intent. A bounded optional self-declaration control preserves the exact
report span but never lets the declaration override a contradictory static source shape. The
command is not a general raw-repository audit adapter.

The blind-workspace scanner is bounded and does not detect paraphrases, partial transformations,
compression, encryption, or undisclosed answer-side content. It checks UTF-8/UTF-16 exact text
variants, Unicode/newline-normalized full hidden text, and raw bytes; those limits remain
machine-readable. Real cross-provider reviewer independence and transcript authorship are external
qualification gates and are not inferred from the locally validated artifact protocol.
