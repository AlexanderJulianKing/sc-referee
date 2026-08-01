# Experiment 0031: Practical public-feature parity closure

- **Status:** Completed locally
- **Date:** 2026-07-31
- **Decision:** Accepted ADR-0046 under the standing authorization
- **Schema:** Unchanged at `0.18.0`

## Question

Can the useful verifier families advertised by the public implementation be recovered through the
overhaul's immutable snapshot, explicit material-input, modular calculation-check, semantic-lock,
and Disclosure-only boundaries without copying its controller or executing project code?

## Result

Yes, for explicit bounded profiles. The default deterministic calculation registry now contains
eight independently removable modules:

1. complete-family Benjamini–Hochberg conformance;
2. replicate-level single-cell sensitivity;
3. declared effect-size relevance;
4. tabular design integrity;
5. namespaced R method/response-scale compatibility;
6. Scanpy same-data selection/test reuse;
7. donor-level eQTL sign and genotype support; and
8. arithmetic-background Hi-C loop-strength conformance.

These complement the existing bounded scientific-method and lineage modules. They provide practical
feature parity, not universal workflow understanding. Each remains removable, content-addressed,
finite, non-executing, and unable to emit a production Finding.

## Controls and acceptance criteria

| Module | Added tests | Acceptance criterion satisfied | Remaining limitation |
|---|---|---|---|
| Effect-size relevance | `tests/test_effect_size_summary.py` | Exact positive summary, corrected twin, significance-only hard negative, unresolved/missing abstention, unselected input, removal | One declared log2-fold-change family only |
| Design integrity | `tests/test_design_integrity.py` | Exact categorical alias, omitted adjustment, pairing, merge, missing-key positive; corrected and genuine-unpaired negatives; ambiguity/removal | Categorical main effects and two-arm tabular metadata only |
| R count model | `tests/test_count_model_compatibility.py` | Raw-count/generic-test mismatch, DESeq2 corrected twin, continuous hard negative, repeated/unresolved abstention, nonexecution, removal | Finite namespaced R registry; no general dataflow |
| Selection reuse | `tests/test_selection_reuse.py` | Same-object Scanpy positive, disjoint held-out twin, predefined/descriptive hard negatives, safeguard/repetition abstention, removal | One literal Scanpy shape; safeguard contract unverified |
| eQTL sign | `tests/test_eqtl_sign.py` | Oriented sign mismatch, matching twin, donor-class support, unresolved/insufficient abstention, removal | Direction-only unadjusted donor OLS |
| Hi-C loop | `tests/test_hic_loop_strength_calculation.py` | Exact mismatch, matching twin, descriptive hard negative, incomplete-distance-stratum abstention, removal | One unbalanced single-pixel arithmetic-background estimator |

The combined focused parity suite passed 49 tests after the Hi-C module was added. Every positive
has zero Findings and `production_finding_permitted: false`.

## Biermann regression

The broadened default registry was rerun on the staged Biermann capsule as `biermann-parity-v8b`.
Integrity is verified with 0 Findings, 0 ConditionalConcerns, 0 MaterialQuestions, and 20
Disclosures. It reproduced exactly:

- 16,289 matched/testable reported discoveries;
- 770 replicate-level survivors;
- survival rate `0.047271164589600345`;
- powered fraction `0.38166861071889`; and
- `recompute_powered: false`.

Replay preserved the deterministic calculation observation exactly. No project code or model was
called. A preceding `biermann-parity-v8` attempt ended after parsing while Matplotlib initialized an
unwritable default cache and therefore has no bundle; it was preserved as an incomplete run. The
new run used a writable temporary Matplotlib cache and completed normally.

## Coverage conclusion

“Practical parity” means every advertised public verifier family now has a usable bounded path in
the overhaul. It does not mean arbitrary repositories will automatically supply the required
contracts, inputs, or producer lineage. The agentic skill must ask the scientist for missing
scientific premises rather than inventing them. Broad formulas, wrappers, sparse/oversized assets,
runtime behavior, implicit scientific relevance, and unverified safeguards remain explicit gaps.

## Release and skill verification

The final repository gates pass with 1,212 tests, 79 accepted public schema examples, strict Ruff
and mypy checks, starter validation, clean wheel construction, semantic-lock replay, storage
integrity, and the complete handoff verifier. The authoritative and packaged skills are exact
copies and both pass skill validation. Plugin package
`0.3.0-dev.0+codex.20260801021301` passes plugin validation, is installed and enabled from the
personal marketplace, and its installed cache is byte-identical to the repository package.

A fresh-context agent invoked that installed skill against the staged Biermann capsule using only
the scientist-selected report and material inputs. The new integrity-verified run reproduced all
frozen operands exactly, emitted 0 Findings, 0 ConditionalConcerns, 0 MaterialQuestions, and 20
Disclosures, made 0 model calls, and executed no project-authored code. The forward test therefore
satisfies agentic-skill transport and usability for this bounded profile. It does not establish
automatic premise discovery, broad repository recognition, detector qualification, or scientific
correctness.

The first clean GitHub-worktree `.[dev]` installation also exposed that mypy could not resolve the
optional PyDESeq2 imports when the recomputation extra was intentionally absent. The runtime now
loads those modules through one lazy import boundary, and
`test_optional_recompute_dependency_failure_is_localized` proves that absence remains a local
unsupported result. Immutable calculation manifest v2 was not rewritten; maintenance manifest v9
binds the new implementation digest, and the default registry advances from profile v8 to v9 with
no schema or scientific-record meaning change.

The first hosted Python 3.12 job then installed NumPy 2.5.1 transitively through h5py. Its stubs use
syntax unavailable under the project's deliberate mypy Python-3.11 target, so the hosted type gate
failed before tests. Because production modules import NumPy directly, `pyproject.toml` now declares
the dependency directly as `numpy>=1.26,<2.5`; this is a packaging correction rather than a hidden
scientific default. `test_numpy_is_a_direct_python_311_compatible_dependency` freezes the bound.
