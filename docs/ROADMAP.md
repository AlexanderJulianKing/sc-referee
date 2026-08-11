# sc-referee

**A conservative referee for computational science.** sc-referee reads a scientific analysis — the
code, the exact data it was given, and the report it produced — and checks whether the method the
report describes is the method the code actually performed. It never executes the author's code,
and it is engineered around a single non-negotiable property: **it does not raise false alarms.**
When it cannot be certain, it says nothing.

That constraint is the whole design philosophy. A tool that wrongly tells a scientist their result
is broken destroys trust faster than no tool at all. So every detector must either match what the
code truly does or stay silent, and every engineering decision resolves ambiguity toward silence.

---

## Delivered

- **Two product-wired binding-level envelopes.** The complete-domain rate error and the narrow
  dependence/pseudoreplication family each passed a sealed, pre-registered examination **7 of 7**:
  both planted errors caught, zero false alarms on five controls, one attempt, no repair. Their
  exact grants are installed, and each has now published one policy-valid, replay-stable Finding
  through the real production audit path while its matched control twin published none.

- **A no-false-alarm record that has never broken.** Across every blind trial and every
  adversarial review conducted to date, the detectors under development have produced **zero false
  accusations**. This is the product's core promise, and it is intact.

- **A general recognition engine, independently reviewed.** The current detector interprets what a
  program's operations *mean* rather than matching code by appearance, and it only asserts a result
  when a small, independently written verification kernel accepts a formal proof of it. It has been
  through three separate rounds of adversarial review by models that did not build it; its latest
  build passed with a clean verdict.

- **Depth of validation.** Over **3,000 automated tests**, including a 433-test adversarial suite
  for the flagship detector alone, every one of which is a program that once defeated an earlier
  version and now guards against its return.

---

## How the engine works

**Operations, not vocabulary.** A naive checker keys on names — a column called `dosage`, a
variable called `patient_id`. That matches spelling, not science, and breaks the moment someone
names things differently. sc-referee recognizes the *operations* a workflow performs, so it is
blind to domain, naming, and coding style.

**Propose, then verify.** An aggressive analyzer reads the code and proposes a proof that a
particular error is or is not present. A much smaller, separately written kernel then decides
whether to accept that proof. Keeping the powerful, fallible part away from the part with authority
to speak is what makes the no-false-alarm guarantee auditable rather than hoped-for.

**Some facts live in the data.** Proving that "1 minus x" is a genuine complement requires knowing
the column only ever holds 0 and 1 — a fact the source code cannot supply. sc-referee proves it by
reading the input file itself, which is data and not execution: the file is fixed by cryptographic
digest at intake, and the proof is only ever "this column contains these values," never "these
numbers look like an error."

**Design insight worth stating plainly:** across this program the bottleneck was never the
arithmetic. Computing a statistical correction exactly is easy and often already done. Recognizing,
in someone else's code and someone else's style, *which* computation is the one that matters — that
is the hard problem, and solving it generally is the engineering contribution here.

---

## Roadmap and status board

Two tracks. Each capability advances only by climbing the ladder described in the next section,
and the **Stage** column below names the highest rung each one has actually reached:

`Planned → Recon → Build → Adversarial review → Blind pilots → Sealed exam → Qualified → Promoted → Product-wired`

"Qualified" means the detector passed its sealed examination. "Promoted" means the maintainer's
promotion decision is formally recorded. "Product-wired" means a real audit run can publish the
result. The complete-domain and dependence bindings have reached that rung; no sibling binding has.

### Track 1 — ten scientific error classes

| Error class | Stage | Next step |
|---|---|---|
| Rate reported over the whole planned set but computed over the surviving subset | **Product-wired** (sealed exam 7/7; exact grant installed; production Finding and zero-Finding control replayed) | Preserve exact pins and qualify any broader envelope separately |
| Reference panel silently complemented before comparison | **Blind pilots** (six run, zero false accusations; every miss a documented abstention) | Close the one named coverage class, or continue pilots |
| Hard or binned category used where a continuous measure was declared | **Adversarial review passed** (round five closed both final findings; verified ready) | Blind pilots |
| Plain group average used as a model-expected background | **Recon** (design complete; rebuild on the recognition engine queued) | Build |
| Directional measurement-error interpretation | Planned | |
| Poststratified misclassification estimator | Planned | |
| Recoverable technical-group adjustment | Planned | |
| Phase-split instrument construction | Planned | |
| Somatic clonality representation | Planned | |
| Local perturbation regression specification | Planned | |

### Track 2 — six capability families

Broader capabilities from the original design. Several already have exact, working arithmetic; the
frontier is the recognition that finds what to compute over.

| Family | What it catches | Built today | Stage | Next step |
|---|---|---|---|---|
| **Dependence / pseudoreplication** | Repeated measurements from one subject counted as independent (300 cells from 3 mice reported as n=300) | Evaluator, safeguard registry, data provers, full recognizer, pilot pipeline, installed grant, and production controller path | **Product-wired** (sealed exam 7/7 at the strict two-of-two bar; exact grant installed; production Finding and zero-Finding control replayed) | Preserve exact pins and qualify any broader envelope separately |
| **Multiple testing** | An incomplete or mis-scoped correction across a family of tests | Exact complete-family Benjamini-Hochberg recomputation | Recon | Recognizer build (next family in the queue) |
| **Design integrity & aggregation** | Aggregation that merges or drops design groups; broken pairing | Exact categorical design, pairing, and aggregation calculations | Recon | Queued third; reuses dependence evidence |
| **Model / response compatibility** | A model fitted on a scale incompatible with its response | Exact call registry and response-scale comparison | Planned | |
| **Circular selection ("double dipping")** | Selecting features with the same data later used to test them | A working selection-reuse observation | Planned | |
| **Identifier integrity** | Sample identifiers that silently fail to match across files | Exact set comparison across tabular and matrix inputs | Planned | |

### The queue right now (as of 2026-08-11)

| Slot | Work |
|---|---|
| Reached | Exact product wiring and first production Findings for complete-domain and dependence |
| Next | Copy-dosage blind pilots |
| Then | Multiple-testing recognizer build (recon complete) |

Verification reviews gate every hand-off in this queue: no item advances past a review that found
something until the finding is fixed and re-checked.

**Product-wired at one exact binding:** dependence / pseudoreplication. The original design named it the
first complete vertical, and its decision rule, safeguard registry, and evaluator were already
built and passing. The new piece is the recognizer: the component that reads an author's code and
produces proven evidence for that evaluator. It is now built on the same propose-then-verify
engine described above, with one addition specific to this error class. The hardest way to be
wrong here is guessing *which* column identifies the repeated unit (the subject, the animal, the
batch). Instead of guessing, the recognizer requires a human-authorized unit definition on a
trusted channel and then proves from the digest-fixed input file itself that the authorized
column's values actually repeat. Where either piece is missing, it stays silent or asks. The
build went through four rounds of independent adversarial review plus a targeted verification
pass; every reviewer-constructed wrong answer became a permanent regression test, and the final
verdict found no known route to a wrong answer. It remains deliberately narrow (it abstains outside
a small certified envelope), passed two completed blind pilots, a threshold rehearsal, and the
sealed two-positive examination, and now has the exact ADR-0073 binding-level promotion. Public
grant installation and production Finding wiring are now present only for that exact binding. The
canonical production demonstration publishes one replay-stable Finding for repeated authorized
`k1` units and zero Findings for its one-row-per-unit control; it does not widen the grammar or
authorize any sibling binding.

---

## How a capability earns "qualified"

Nothing counts as working because it passed the tests its own author wrote. A detector is qualified
only after, in order:

1. **Recon** — state the error as operations, never vocabulary.
2. **Build** — implement the recognizer.
3. **Adversarial review** — an independent model tries to construct programs where the detector is
   confidently wrong. Every such program becomes a permanent test. This happens *before* any
   measurement, because measurement cases are single-use.
4. **Blind trials** — a fresh model invents its own study, domain, and coding style from a brief
   that names no vocabulary, and writes real runnable code and a real report. A separate blind
   reviewer labels the cases; labels are frozen before the detector runs; the detector gets one
   attempt.
5. **Sealed examination** — roles are frozen and sealed in advance; the seal opens only after a
   pass/fail threshold is accepted in writing; one shot, published whatever the outcome.

Every case that ever defeated a detector stays in the suite forever, so a closed weakness cannot
silently reopen. And the pipeline enforces its own integrity: when a blind reviewer's cited
evidence did not match the source file exactly, the pipeline refused it rather than proceeding —
which is what makes the sealed exam trustworthy.

---

*This summary is written for readers new to the project. Every claim is traceable in this
repository to a commit, a content digest, and a test.*
