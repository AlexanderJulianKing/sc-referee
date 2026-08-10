# sc-referee

`sc-referee` is a conservative auditor for scientific-analysis repositories. It takes an immutable
snapshot, inspects supported files without running project-authored code, records exactly what it
could and could not establish, and produces a replayable audit report.

> **Public alpha:** the current program version is `0.3.0` and the public record schema
> is `0.18.0`. The overhaul is usable for bounded review, but it is not a correctness certificate,
> publication approval, or general detector of every possible scientific mistake.

## Why it exists

Scientific workflows often combine code, notebooks, reports, intermediate tables, large datasets,
and undocumented choices. A reviewer may be able to demonstrate one narrow mismatch while many
other questions remain unresolved. `sc-referee` preserves that distinction.

Its public assessment types are:

| Assessment | Meaning |
|---|---|
| `Finding` | A narrowly worded demonstrated issue that passed every admission requirement. |
| `ConditionalConcern` | A stated consequence that applies only if an unresolved premise is later established. |
| `MaterialQuestion` | A bounded question whose answer can change the audit. |
| `Disclosure` | A relevant limitation, unsupported boundary, or deterministic observation below Finding authority. |

Zero Findings means only that no issue was admitted within the audit's declared evidence and
coverage. It does not mean the workflow is correct.

## Program status and validation record

Every claim in this section is traceable to a committed record in this repository.

- **One detector has passed a sealed qualification examination, 7 of 7, and holds a recorded,
  independently verified maintainer promotion.** The complete-domain exposure-denominator
  detector (a headline rate computed over only the surviving subset of units but reported as
  covering the whole planned set) was examined against seven sealed, pre-registered assignments:
  both planted errors caught, zero false alarms on five controls, one attempt, no repair. See
  [ADR-0070](docs/implementation/ADR-0070-HELDOUT-THRESHOLD-COMPLETE-DOMAIN-ENVELOPE.md) for the
  examination and [ADR-0071](docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md)
  for the promotion decision. The promotion grants no production authority yet: wiring a real
  audit run to publish that Finding is separately gated future work, and the installed
  qualification manifest remains empty until it lands.
- **The no-false-accusation record is intact.** Across every blind trial and adversarial review
  round conducted to date, the detectors under development have produced zero false accusations.
  Where the tool cannot be certain, it abstains or asks.
- **A general recognition engine, independently reviewed.** The founder-orientation detector
  interprets what a program's operations mean rather than matching code by appearance, and
  asserts a result only when a small, separately written verification kernel accepts a formal
  proof. See
  [EXPERIMENT-0057](docs/implementation/EXPERIMENT-0057-FOUNDER-ORIENTATION-SEMANTIC-V3-SHADOW.md).
- **A dependence / pseudoreplication recognizer is built, reviewed, and registered
  question-only.** It requires a human-authorized unit definition on a trusted channel, proves
  from the digest-fixed input file which column's values repeat, and abstains outside a narrow
  certified envelope. Four rounds of independent adversarial review plus a targeted verification
  pass closed every constructed wrong answer as a permanent regression test. See
  [EXPERIMENT-0058](docs/implementation/EXPERIMENT-0058-DEPENDENCE-SEMANTIC-V1-SHADOW.md).
- The full program plan and per-capability maturity are in [docs/ROADMAP.md](docs/ROADMAP.md).

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

The skills are distributed in a validated Codex plugin under `plugins/sc-referee`. A repo
marketplace is included for local installation. See [agentic skill setup](docs/AGENTIC_SKILL.md)
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
dimensions; there is no aggregate “full” status. The only
complete Finding-producing path remains a synthetic test fixture; the promoted detector's
production wiring is separately gated future work recorded in ADR-0071. Read the
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

- `0.3.0` — the installable public-alpha Python program;
- `0.18.0` — the current public JSON Schema release; and
- `0.1.0` — the historical starter lineage.

The accepted “0.6.0 minimum proud product” is an architecture boundary, not the package version.
The public-alpha package release is `0.3.0`.

## License

Apache License 2.0. Alexander King is the sole human author; OpenAI Codex and Anthropic Claude are
acknowledged as AI development collaborators. See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md),
[CITATION.cff](CITATION.cff), [LICENSE](LICENSE), [NOTICE](NOTICE), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
