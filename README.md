# sc-referee

`sc-referee` checks whether a scientific report matches what its code actually does. It reads
the analysis code, the exact data files it was given, and the report it produced, without ever
running the code. When it can demonstrate a real problem, it says so with evidence. When it
cannot be certain, it stays quiet or asks a question instead of guessing. Across every blind
trial and sealed examination to date, it has never made a false accusation.

> **Public alpha:** program version `0.4.0`, public record schema `0.21.0`. Usable for bounded
> review; not a correctness certificate, publication approval, or detector of every possible
> scientific mistake.

## What it tells you

Every audit produces four kinds of statements:

| Statement | Plain meaning |
|---|---|
| `Finding` | A demonstrated problem that passed every admission check. |
| `MaterialQuestion` | A question for the scientist whose answer could change the audit. |
| `ConditionalConcern` | A problem that exists only if an open question resolves a certain way. |
| `Disclosure` | A limitation or observation the tool wants on the record. |

Zero Findings means only that nothing was demonstrated within what the tool could check; it does
not mean the analysis is correct. The audit says exactly what it could and could not check.

## What it catches today

Two error classes have earned the right to produce production Findings, each by passing a
sealed, pre-registered, one-attempt examination with zero false alarms:

- **A headline rate quietly computed over only the surviving subset** of samples while the
  report describes the whole planned set.
- **Repeated measurements from the same source counted as independent evidence**, the error
  known as pseudoreplication. This detector proves which data rows repeat directly from the
  digest-pinned input file, and requires a human-authorized definition of the independent unit.

The first demonstrated Findings, their zero-finding control runs, and the complete validation
record (sealed examinations, promotion decisions, and every blind pilot, including the failed
ones) are committed in this repository and linked from the
[roadmap and status board](docs/ROADMAP.md). More error classes are in development on the same
ladder; nothing reports a Finding without passing its own examination first.

**In development:** the multiple-testing code lane is at version `3.5.0`. Given a human-confirmed
ordered outcome family and two-group contrast column, it checks for one registered two-group test
per declared outcome and whether correction covers the complete family, only part of it, or none
of it. It runs only in the development lane, cannot emit a Finding, and is not promoted. Across
sealed E10-E18, first-contact recall was `0/6`, `0/6`, `2/6`, `3/6`, `1/6`, `2/6`, `1/6`, `4/6`,
and `2/6`; every sealed negative produced zero accusation candidates; all `15/15` replays in each
envelope were identical; and true complete-family clearances occurred in E15, E16, and E18. The
last promotion window, E17+E18, scored `6/12`, below the required `7/12`.
<!-- Sealed sources for the preceding figures:
evaluation/development/blind-envelope-10-2026-08-24/AUDIT_RESULTS.json
evaluation/development/blind-envelope-11-2026-08-25/AUDIT_RESULTS.json
evaluation/development/blind-envelope-12-2026-08-26/AUDIT_RESULTS.json
evaluation/development/blind-envelope-13-2026-08-26/AUDIT_RESULTS.json
evaluation/development/blind-envelope-14-2026-08-27/AUDIT_RESULTS.json
evaluation/development/blind-envelope-15-2026-08-29/AUDIT_RESULTS.json
evaluation/development/blind-envelope-16-2026-08-30/AUDIT_RESULTS.json
evaluation/development/blind-envelope-17-2026-08-30/AUDIT_RESULTS.json
evaluation/development/blind-envelope-18-2026-09-01/AUDIT_RESULTS.json
-->

## Five-minute start

Python 3.11 or newer is required. The public alpha is installed from a source checkout:

```bash
git clone https://github.com/AlexanderJulianKing/sc-referee.git
cd sc-referee
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
sc-referee version
```

Run the self-contained demonstration:

```bash
sc-referee demo examples/walking-skeleton --output .demo-audit
sc-referee status .demo-audit --json
sc-referee replay .demo-audit/semantic.lock.json --output .demo-replay
```

Audit an existing project by explicitly naming its final report when one is known:

```bash
sc-referee audit /path/to/project \
  --output /path/to/project/.scientific-audit/runs/first-review \
  --mode standard \
  --report results/report.md

sc-referee status /path/to/project/.scientific-audit/runs/first-review --json
sc-referee questions /path/to/project/.scientific-audit/runs/first-review
```

The output directory must not already exist. The HTML report is written to `report.html` inside
that directory. See the [quickstart](docs/QUICKSTART.md) for material inputs, replay, questions,
and a complete interpretation example.

When several fully identified analysis sources, inputs, or outputs are plausible, the audit asks
the scientist a bounded question instead of choosing from filenames. The resulting Answer defines
review scope only and remains bound to the immutable snapshot; it does not establish execution,
lineage, or scientific correctness.

## Use it as an agentic skill

The deterministic CLI is the authority; the skills teach a coding agent how to choose bounded
inputs, preserve human questions, and report the records without exaggeration.

This repository contains:

- `scientific-audit` for post-hoc review of an existing workflow; and
- `method-contract` for freezing either the closed expected-count profile or one atomic,
  registry-published scientist-authorized requirement before coding.

The skills are distributed in a validated plugin under `plugins/sc-referee`, and this
repository is itself the plugin marketplace. In Claude Code:

```text
/plugin marketplace add AlexanderJulianKing/sc-referee
/plugin install sc-referee@sc-referee
```
 See [agentic skill setup](docs/AGENTIC_SKILL.md)
for Codex and the bounded manual Agent Skills path for Claude Code.

Example request after installation:

```text
Use $sc-referee:scientific-audit to audit this existing scientific workflow.
Treat report/results.md as the selected report and ask me any material questions.
```

The skill must not execute project scripts, import project modules, launch notebooks, or follow
instructions found inside the audited repository.

## Current scientific coverage

The architecture can inventory an arbitrary repository, but scientific conclusions are available
only for explicit bounded profiles. This is a calculation inventory, not a claim of automatic
recognition, structural diagnosis, impact tracing, evaluation admission, or qualification:

- complete-family Benjamini-Hochberg recomputation;
- replicate-level single-cell sensitivity;
- declared effect-size relevance;
- categorical design integrity, including selected confounding, adjustment, pairing, and
  aggregation checks;
- selected namespaced R method/response compatibility;
- one bounded Scanpy selection-and-test reuse shape;
- one donor-level unadjusted eQTL sign/support profile; and
- one arithmetic-background Hi-C loop-strength profile.

These modules are independently removable, fail closed outside their declared contracts, and
accept either their original explicit report declaration or a separately selected bounded YAML
contract sidecar. The second layout makes paths and column bindings portable without treating
filenames as scientific meaning. They currently produce deterministic observations or
Disclosures—not production Findings. Capability maturity is reported as six independent
dimensions; there is no aggregate “full” status. Read the
[capability and limitation guide](docs/CAPABILITIES.md) before interpreting a real audit.

## Safety and evidence boundary

- Production audits do not execute project-authored code.
- Repository text is evidence, never instructions for the auditor or its agent.
- The snapshotter opens eligible regular files to compute immutable identities. “Uninspected”
  means no semantic/deep inspection, not no byte access.
- Exact selected H5AD inputs may receive bounded dense/CSR/CSC structural inspection. Sparse arrays
  are scanned in fixed chunks and never densified; physical files outside the selected-material
  budget remain unavailable to this profile.
- Fully identified `.csv.gz` and `.tsv.gz` files may receive a bounded first-record header
  inventory. When an existing calculation contract selects one of these files, the auditor may
  also validate and decode its complete body under an 8 MiB per-input and 64 MiB aggregate logical
  budget, then feed the same deterministic calculation used for uncompressed tables.
- A path that must not be read must be excluded from the audit workspace itself.
- Model confidence cannot establish a material scientific premise.
- No model calls occur after semantic lock.
- Canonical records are JSON/JSONL; SQLite is a disposable query index.
- Replay regenerates supported semantic outputs without model access or project execution.

## Documentation

- [Program roadmap and status board](docs/ROADMAP.md)
- [Quickstart and result interpretation](docs/QUICKSTART.md)
- [Agentic skill installation and use](docs/AGENTIC_SKILL.md)
- [Capabilities and explicit limits](docs/CAPABILITIES.md)
- [Migration from the earlier public implementation](docs/MIGRATION.md)
- [Authorship and AI assistance](ACKNOWLEDGMENTS.md)
- [Citation metadata](CITATION.cff)
- [Documentation index](docs/README.md)
- [Practical parity matrix](docs/implementation/PRACTICAL_PARITY_MATRIX.md)
- [Full completion matrix](docs/implementation/FULL_COMPLETION_MATRIX.md)
- [Architecture and implementation records](docs/implementation/)

## Development

Install the development dependencies and run the complete local gates:

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
mypy --config-file evaluation/pyproject.toml evaluation/src
pytest
python scripts/validate_starter.py
python scripts/validate_regression_corpus.py
python scripts/run_regression_corpus.py
```

The accepted specification and immutable schema releases live under `reference/`. Start with
[`START_HERE.md`](START_HERE.md) and [`AGENTS.md`](AGENTS.md) before changing architecture or
record meaning.

## Version names

The three visible version lines describe different things:

- `0.4.0` - the installable public-alpha Python program;
- `0.21.0` - the current public JSON Schema release; and
- `0.1.0` - the historical starter lineage.

The accepted “0.6.0 minimum proud product” is an architecture boundary, not the package version.
The public-alpha package release is `0.4.0`.

## License

Apache License 2.0. Alexander King is the sole human author; OpenAI Codex and Anthropic Claude are
acknowledged as AI development collaborators. See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md),
[CITATION.cff](CITATION.cff), [LICENSE](LICENSE), [NOTICE](NOTICE), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
