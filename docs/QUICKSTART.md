# Quickstart

This guide runs the current development alpha from source, audits a repository without executing
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
sc-referee 0.3.0 (schema 0.18.0; starter lineage 0.1.0)
```

The version is intentionally a development version. Do not infer release stability from the schema
version.

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

## 6. Answer a material question

The ordinary agentic workflow manages linked question segments. For direct CLI use, create a new
segment rather than editing the completed audit:

```bash
sc-referee resume /path/to/project/.scientific-audit/runs/first-review \
  --repository /path/to/project \
  --output /path/to/project/.scientific-audit/runs/first-answer

sc-referee work-queue /path/to/project/.scientific-audit/runs/first-answer
```

Use `work-packet` for a ready item. A scientist—not the model—must select an existing answer option.
After recording the answer, lock semantics and verify the linked segment. The complete typed
interaction protocol is in the bundled `scientific-audit` skill.

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
