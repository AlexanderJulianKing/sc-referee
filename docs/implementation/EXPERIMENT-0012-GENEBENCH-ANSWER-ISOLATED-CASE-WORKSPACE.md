# Experiment 0012: GeneBench answer-isolated case workspace

- **Status:** Active evaluation-private experiment; first real agent run completed and audited
- **Date:** 2026-07-29
- **Scope:** Deterministic preparation of one public-development agent workspace from an admitted
  GeneBench-Pro package preflight

## Purpose

Close the mechanical boundary between the verified public corpus and an external workflow-producing
agent without exposing the package's public ground truth, grader, reference report, or answer-side
configuration to that agent. This experiment does not invoke a model, execute the reference grader,
execute a scientific workflow, label a detector result, or create qualification evidence.

## Accepted experimental envelope

`sc-referee-eval prepare-genebench-public-case` consumes:

- one already-local package;
- its exact canonical Experiment 0005 preflight;
- one `eval_id` from that preflight;
- one explicit timestamp; and
- one absent output root outside the package.

Before writing, it validates the preflight digest and all public-development ceilings, reruns the
full package preflight against the same revision and payload digests, and selects exactly one case.
It then:

- derives `task.md` from the verified config task string;
- copies exactly the preflight-declared visible data files under `data_files/`;
- keeps the exact config, canonical ground truth, reference grader, and reference report under a
  runner-only `.answer-side/` tree;
- captures a full-digest immutable snapshot of both visible and runner-only source material;
- passes only the task and staged data through the existing bounded blind-workspace scanner;
- rejects an exact hidden payload, hidden digest, or canonical ground-truth object in a selected
  workspace file;
- writes the resulting `workspace/` separately from runner-side records and materialization; and
- emits a self-digested case-preparation record that contains identities and paths but no answer
  values.

Only `workspace/` is agent-eligible. The rest of the output root is runner-side and must not be
mounted or exposed to the external agent. A real runner still needs a filesystem/process boundary
that enforces that separation.

## Real public-development preparation

The valid official baseline from Experiment 0005 was used to prepare:

- case: `hic_sv_masked_loop_strength`;
- visible files: `task.md`, `data_files/bins_20kb.tsv.gz`, `bins_40kb.tsv.gz`,
  `contacts_20kb.tsv.gz`, and `contacts_40kb.tsv.gz`;
- workspace manifest digest:
  `sha256:ebc9f553114d069590d3ef54782c77d87e84ca8c18b2e6412cca04f93be7512a`;
- case-preparation digest:
  `sha256:1736e4b2dff633e2d0e3c694b95f28a46a3bd205611961fb7f073ad7467efee5`;
- `ground_truth_disclosed_to_agent_workspace:false`;
- `project_code_executed:false`; and
- `model_invoked:false`.

The package and prepared case remain in temporary local storage and are not bundled with the
repository.

The agent-visible workspace was also passed through `sc-referee audit` and model-free replay before
any generated workflow existed. The audit inventoried all five files, deeply inspected `task.md`,
left all four gzip inputs explicitly uninspected, emitted no Claim, DetectorResult, or Finding, and
reported one unresolved publication-surface question plus one disclosure. Replay preserved the
evidence records exactly. This is a useful negative control: a benchmark task is not mistaken for a
completed scientific result, and unsupported compressed inputs do not become negative detector
coverage.

After explicit authorization, a fresh-context independent agent received only a separately copied
five-file workspace. All runner-side and prior answer-bearing temporary paths were removed before
the agent started. The agent wrote and twice reran its own `analysis.py`; both runs were byte
identical. It reported case `2.018599308977125`, control `0.027570777096230376`, and delta
`1.9910285318808945`, using a replicate-wise low-mappability-filtered same-distance mean as the
expected count.

The generated repository was then audited and replayed before runner-side answers were reacquired.
The frozen audit was complete and integrity-verified, selected `report.md`, recorded zero model
calls and no post-lock model access, and emitted 145 Operations, three Artifacts, zero Claims, zero
ObservedResults, zero DetectorResults, and zero Findings. This was not a clean result: the answer,
diagnostics, gzip inputs, and supporting result files remained explicitly uninspected, so the audit
reported partial evidence unavailable.

Only after semantic lock and replay was the exact public package reacquired runner-side. Experiment
0013's non-executing grader bound the frozen `answer.json` to the verified public contract and
recorded absolute errors `0.13780558924821396`, `0.5461243400592221`, and
`0.408318750811008`, each beyond its `0.02` tolerance. The canonical outcome is therefore a real
public-development workflow error that the current production detector did not localize.

## Exit evidence

- `test_cli_prepares_exact_answer_isolated_public_case` verifies the exact visible allowlist,
  absence of a known answer and malicious grader marker, runner/agent separation, public-only
  ceiling, and non-execution/non-model flags.
- `test_public_case_preparation_rechecks_preflight_and_package` mutates the preflight and package
  independently and verifies that neither creates an output.
- `test_public_case_preparation_is_write_once` verifies that an existing destination is never
  replaced.
- `test_prepared_public_case_enters_static_audit_and_replay` verifies that only visible files enter
  the production audit, no answer-side path leaks into records, no claim or detector result is
  invented before a workflow exists, and replay preserves the evidence-bearing fields.
- The real public case above passed the same CLI path after its 77-file package preflight.
- The authorized fresh-context run proved that the workspace boundary supports an independent
  reproducible workflow without exposing runner-only paths.
- Its frozen audit/replay and Experiment 0013 grade establish the current coverage miss without
  converting the hidden answer or public-development case into a production Finding.

## Remaining limitation

The case's gzip inputs, numeric answer envelope, transformed loop-strength quantity, and stated
same-distance expected-count method fall outside the current production parser/detector envelope.
The official public report demonstrates answer-side that the intended method instead uses a masked
negative-binomial expected-count model with replicate intercepts and condition-specific GC and
distance terms. The visible prompt alone does not state that model, so a production Finding still
requires an explicit authoritative method contract plus bounded implemented-method evidence; the
answer key cannot be smuggled into detector inputs. Public data and answers make this development
evidence only, never held-out qualification evidence.
