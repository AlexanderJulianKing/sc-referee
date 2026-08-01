# Milestone 0 build specification

## Objective

Prove that the evidence-compiler architecture can produce a conservative, reproducible assessment from a minimal repository before implementing broad language, workflow, or scientific-domain support.

## Deliverable

An installable local CLI and Python package that audits the bundled walking-skeleton repository and produces:

```text
output/
├── semantic.lock.json
├── audit.bundle.json
├── report.html
├── audit.db
├── observed/
│   ├── snapshot.json
│   ├── files.jsonl
│   └── parser-results.jsonl
└── derived/
    ├── detector-results.jsonl
    ├── findings.jsonl
    ├── material-questions.jsonl
    └── disclosures.jsonl
```

## In scope

- Python 3.11+ controller.
- One Python source file and one Markdown report.
- One publication surface selected explicitly by fixture configuration.
- One directional quantitative claim.
- One resolved scientific contract.
- One observed scalar result with explicit comparison orientation.
- One deterministic detector.
- One Finding-admission implementation.
- One unresolved semantic question.
- One opaque-boundary disclosure.
- JSON/JSONL storage, generated SQLite index, and static HTML.
- Model-free replay.

## Out of scope

- General claim extraction.
- R, notebooks, Quarto, workflow engines, HPC execution, and domain packs.
- Arbitrary project-code execution.
- Dependency installation.
- MCP or slash-command packaging.
- Detector validation or public capability claims.
- Open-ended issue search.
- Numerical promotion thresholds.

## Package boundaries

```text
sc_referee.core       state, deadline, errors, stable identity
sc_referee.records    schema registry and normalization
sc_referee.storage    canonical JSONL and generated SQLite
sc_referee.snapshot   immutable materialization and file manifest
sc_referee.parsers    lightweight source inspection
sc_referee.detectors  deterministic applicability and assessment
sc_referee.reporting  offline HTML generation
sc_referee.cli        reproducible command-line facade
```

No package under `sc_referee.core` may import evaluation or Claude integration code.

## Public interfaces for this milestone

```python
class RecordValidator:
    def validate(self, record: Mapping[str, object]) -> None: ...

class RepositorySnapshotter:
    def capture(self, source: Path, destination: Path, run_id: str) -> dict[str, object]: ...

class Parser:
    def inspect(self, path: Path, run_id: str) -> dict[str, object]: ...

class Detector:
    def evaluate(self, locked_case: LockedDirectionalCase) -> DetectionOutput: ...

class RecordStore:
    def append(self, record: Mapping[str, object]) -> None: ...
    def iter_records(self, record_type: str | None = None) -> Iterator[dict[str, object]]: ...

class ReportRenderer:
    def render(self, bundle: Mapping[str, object], destination: Path) -> None: ...
```

Interfaces may gain methods, but their deterministic meaning cannot change without updating tests and this document.

## Controller states

```text
CREATED
→ SNAPSHOTTED
→ INVENTORIED
→ PARSED
→ SEMANTICS_LOCKED
→ DETECTED
→ REPORTED
→ COMPLETE
```

Permitted terminal variants:

```text
PARTIAL_DEADLINE
PARTIAL_HOST_LIMIT
CANCELLED
FAILED_CONTROLLER
```

Parser and detector failures are records inside a partial run; they are not automatically controller failures.

## Finding admission

The detector may create a Finding only when all are true:

1. The report proposition and normalized result directly contradict.
2. Comparison orientation and scale are established.
3. No unknown could reverse the contradiction.
4. The detector manifest covers the exact construct.
5. Every finite counterevidence check completed.
6. The Finding wording does not infer biological truth, bias direction, or effect of correction.
7. The same lock produces the same normalized output without a model.

## Determinism contract

Normalize records using UTF-8 JSON with sorted keys and compact separators. Exclude volatile execution metrics and output-directory paths from semantic digests. Timestamps used in locked semantic records come from the lock, not the replay wall clock.

## Security contract

Milestone 0 performs static reads only. It never imports project modules, executes the analysis, deserializes executable formats, installs dependencies, or follows repository instructions. The bundled `analysis.py` is parsed, not executed by the auditor.

## Acceptance tests

| ID | Test |
|---|---|
| M0-01 | Clean editable install on Python 3.11+ |
| M0-02 | All public v0.5 schema examples validate locally without network |
| M0-03 | Snapshot digest is stable for unchanged input |
| M0-04 | Python parser returns exact line spans and does not execute source |
| M0-05 | Contradiction fixture yields exactly one Finding |
| M0-06 | Hard-negative fixture yields zero Findings |
| M0-07 | Unknown-orientation fixture yields a MaterialQuestion and zero Findings |
| M0-08 | Opaque tool yields one non-accusatory Disclosure |
| M0-09 | Generated HTML is self-contained and escapes repository text |
| M0-10 | Deleting `audit.db` and rebuilding preserves record counts and identities |
| M0-11 | Replay creates byte-identical normalized detector and assessment records |
| M0-12 | No report text says pass, correct, safe, publication-ready, or low risk as a global status |
| M0-13 | Repository prompt-injection text does not alter policy or execution |
| M0-14 | Forced deadline creates a partial run with explicit uninspected scope |

## Exit criterion

Milestone 0 is complete only when every acceptance test passes and a coding agent unfamiliar with the design can reproduce the demo from `README.md` without inventing record shapes or policy.
