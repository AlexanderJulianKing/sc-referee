# Quickstart

This guide runs the current public alpha from source, audits a repository without executing
its code, and explains the result categories.

## 1. Install the CLI

Requirements:

- Python 3.11 or newer;
- Git for obtaining the source; and
- no container runtime for the supported production audit path.

```bash
git clone https://github.com/AlexanderJulianKing/sc-referee.git
cd sc-referee
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
sc-referee version
```

Expected version shape:

```text
sc-referee 0.3.0 (schema 0.20.0; starter lineage 0.1.0)
```

Program `0.3.0` is a public-alpha release. The schema version is a separate record-format identity;
do not infer program stability or scientific coverage from it.

## 2. Run the deterministic demo

From the source checkout:

```bash
sc-referee validate-schemas
sc-referee demo examples/walking-skeleton --output .demo-audit
sc-referee status .demo-audit --json
sc-referee replay .demo-audit/semantic.lock.json --output .demo-replay
```

Both output paths must be absent before the command runs. The demo is a synthetic fixture that
exercises Finding admission; it is not evidence that a production scientific detector is
qualified.

The checkout also includes a small ordinary static-audit example:

```bash
sc-referee audit examples/general-static \
  --output .general-audit \
  --mode quick \
  --report report.md \
  --material-input data.csv
sc-referee status .general-audit --json
sc-referee replay .general-audit/semantic.lock.json --output .general-replay
```

Unlike the walking skeleton, this path does not enable the fixture-only Finding detector.

## 3. Audit an existing repository

Choose an output directory that does not exist. If you know which in-repository file is the final
report, name it explicitly with a safe repository-relative path:

```bash
sc-referee audit /path/to/project \
  --output /path/to/project/.scientific-audit/runs/first-review \
  --mode standard \
  --report results/report.md
```

Do not choose a report merely because its filename looks plausible. Omitting `--report` is valid;
the audit then preserves publication-surface selection as unresolved when it cannot establish one.

Before running on sensitive material, understand the snapshot boundary: the auditor opens every
eligible regular file under the project root to compute its immutable identity. A later
`uninspected` label means no semantic/deep inspection, not no byte access. Build an allowlisted
workspace first if some paths must not be read at all.

### Modes

| Mode | Scheduling cutoff | Hard deadline | Intended use |
|---|---:|---:|---|
| `quick` | 120 s | 300 s | Fast inventory and bounded first look. |
| `standard` | 480 s | 600 s | Normal review. |
| `publication` | 1,500 s | 1,800 s | Broader bounded review of a named publication surface. |

These are audit-controller deadlines, not promises about total wall-clock time. Reporting and
post-lock integrity work are outside the semantic-lock timing record.

## 4. Select material inputs only when they matter

Some deterministic calculation modules require the scientist to identify exact material files.
Pass each safe repository-relative path separately:

```bash
sc-referee audit /path/to/project \
  --output /path/to/project/.scientific-audit/runs/material-review \
  --mode standard \
  --report results/report.md \
  --material-input results/results.csv \
  --material-input data/counts.h5ad
```

At most eight paths and 16 MiB total receive the separate material-input budget. Selection permits
a bounded exact read; it does not prove that the file was used, that its declared role is true, or
that its scientific interpretation is correct. Large or unsupported inputs should become explicit
coverage limitations rather than forcing a full rerun.

The optional single-cell recomputation engine is installed explicitly:

```bash
python -m pip install -e '.[single-cell-recompute]'
```

Do not install that extra silently during an audit.

### Optional portable calculation sidecar

The eight bounded calculation families can read an explicitly selected YAML contract instead of
requiring a purpose-built declaration inside the report. The filename and directory are arbitrary.
For example, a complete-family BH binding may contain:

```yaml
sc_referee_calculation_contracts: 1
contracts:
  - check_id: calculation-check:benjamini-hochberg-complete-family-v1
    contract:
      procedure: benjamini_hochberg
      family: complete
      alpha: "0.05"
      table: exported/hypotheses.tsv
      id_column: feature_id
      raw_pvalue_column: p_raw
      adjusted_pvalue_column: q_reported
      call_column: discovered
```

Select both the sidecar and its material table:

```bash
sc-referee audit /path/to/project \
  --output /path/to/project/.scientific-audit/runs/bh-review \
  --report results/report.md \
  --material-input review/calculations.yaml \
  --material-input exported/hypotheses.tsv
```

The same existing table-consuming contracts accept exact `.csv.gz` or `.tsv.gz` paths. Complete
gzip calculation input is decoded in 64 KiB chunks under an 8 MiB per-input and 64 MiB aggregate
logical-read budget. The audit records physical and decoded digests separately; compression does
not change the scientific contract or make undocumented columns authoritative.

Do not let an auditing agent invent the scientific values in this file. They must already be
explicitly documented or supplied by the scientist. A sidecar is a review-scoped declaration, not
proof of execution, correctness, or method adequacy. If both the report and sidecar declare the
same check, that check fails closed as competing evidence.

## 5. Verify and read the result

```bash
sc-referee status /path/to/project/.scientific-audit/runs/first-review --json
sc-referee questions /path/to/project/.scientific-audit/runs/first-review
```

Stop if integrity is not `verified`. The durable sources are:

- `audit.bundle.json` — validated typed records;
- `semantic.lock.json` — the locked semantic boundary;
- `report.html` — the human-readable report;
- `canonical/` — canonical JSON/JSONL evidence; and
- `audit.db` — a disposable index that can be rebuilt from canonical records.

Read assessments in this order:

1. Findings: demonstrated issues only.
2. MaterialQuestions: facts or intent still needed from the scientist.
3. ConditionalConcerns: consequences that depend on unresolved premises.
4. Disclosures: unsupported areas, opaque boundaries, or bounded observations below Finding
   authority.
5. Coverage: what was selected, inspected, unsupported, or left unavailable.

Never summarize zero Findings as “passed,” “correct,” or “publication-ready.”

### Worked interpretation example

For the bundled `examples/general-static` command above, sc-referee 0.3.0 reports verified
integrity, `partial_evidence_unavailable` coverage, zero Findings, one MaterialQuestion,
and twenty-one Disclosures. A conservative summary is:

> Integrity is verified, and no issue was admitted as a Finding within this audit's declared
> evidence and qualified-detector coverage. One scientist question remains open, twenty-one
> Disclosures describe bounded observations or coverage limits, and overall coverage is partial.
> This result does not establish that the workflow is correct or publication-ready.

That summary reports what the audit established without turning zero Findings into a pass. Read the
question and material Disclosures next; do not collapse them into a score.

## 6. Answer a material question

The ordinary agentic workflow manages linked question segments. For direct CLI use, create a new
segment rather than editing the completed audit:

```bash
sc-referee resume /path/to/project/.scientific-audit/runs/first-review \
  --repository /path/to/project \
  --output /path/to/project/.scientific-audit/runs/first-answer \
  --question-id <question-id>

sc-referee work-queue /path/to/project/.scientific-audit/runs/first-answer
```

For each ready item returned by `work-queue`, inspect its exact digest-bound packet:

```bash
sc-referee work-packet /path/to/project/.scientific-audit/runs/first-answer \
  --work-item-id <work-item-id>
```

If the item requests a bounded semantic proposal, give only that packet to the coding agent. Save
the agent's schema-valid proposed record as `proposal.json`, then submit it against the same work
item. The proposal remains proposed and cannot select an answer for the scientist:

```bash
sc-referee submit-proposals /path/to/project/.scientific-audit/runs/first-answer \
  --work-item-id <work-item-id> \
  --proposal proposal.json

sc-referee questions /path/to/project/.scientific-audit/runs/first-answer
```

After the scientist chooses an existing candidate answer, record its exact IDs and a stable human
actor identity:

```bash
sc-referee record-answer /path/to/project/.scientific-audit/runs/first-answer \
  --question-id <question-id> \
  --select-option <answer-option-id> \
  --actor-id scientist:<stable-id>
```

For a question that explicitly requests named ScientificContract dimensions, save only the values
actually supplied by the scientist as one JSON object and use the structured form instead:

```bash
sc-referee record-structured-answer \
  /path/to/project/.scientific-audit/runs/first-answer \
  --question-id <question-id> \
  --values scientist-values.json \
  --actor-id scientist:<stable-id>
```

If a `bounded-review-scope-selection-v1` question asks which exact source, input, or output
identities belong in review scope, one listed candidate, none, or unknown still uses
`record-answer`. To select several listed identities, repeat their exact option IDs:

```bash
sc-referee record-scope-answer \
  /path/to/project/.scientific-audit/runs/first-answer \
  --question-id <question-id> \
  --select-option <first-answer-option-id> \
  --select-option <second-answer-option-id> \
  --actor-id scientist:<stable-id>
```

The selection is bound to the immutable source snapshot and defines this audit's review scope
only. It does not prove that source code ran, produced an output, used an input, or was
scientifically correct. Resolve another open question in a fresh linked segment created from this
segment after it is locked.

Never translate the agent's preference into either Answer. When the queue is resolved—or the
scientist has explicitly retained an available unknown option—lock and verify the linked segment:

```bash
sc-referee lock-semantics /path/to/project/.scientific-audit/runs/first-answer
sc-referee status /path/to/project/.scientific-audit/runs/first-answer --json
```

Stop if final integrity is not `verified`. The bundled `scientific-audit` skill contains the full
typed interaction policy and failure handling.

## 7. Replay or compare

Replay writes a new output directory and makes no model call:

```bash
sc-referee replay \
  /path/to/project/.scientific-audit/runs/first-review/semantic.lock.json \
  --output /path/to/project/.scientific-audit/runs/first-replay
```

Compare two integrity-verified runs without issuing a correctness judgment:

```bash
sc-referee diff \
  /path/to/project/.scientific-audit/runs/first-review \
  /path/to/project/.scientific-audit/runs/first-replay \
  --output /path/to/project/.scientific-audit/first-diff.json
```

Replay demonstrates deterministic regeneration from the lock. It does not prove that the locked
scientific premises are true or that detector coverage is complete.

## Next

- Install the [agentic skill](AGENTIC_SKILL.md) for guided post-hoc review.
- Check the exact [capability limits](CAPABILITIES.md).
- Read the [migration guide](MIGRATION.md) before replacing an older installation.
