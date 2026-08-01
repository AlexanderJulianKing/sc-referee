# Single-cell material inputs

Use this reference only when the user explicitly asks to audit named H5AD or single-cell result
artifacts.

## Material selection

Pass each user-identified artifact separately:

```text
--material-input path/to/counts.h5ad \
--material-input path/to/results.csv
```

Selection grants a separate bounded full-digest read. It does not establish that the file was an
analysis input or output, that it drove the selected report, or that its fields have a scientific
meaning. Unselected H5AD files receive no H5AD semantic inspection. Supported initial H5AD
structure is one dense integer `X`, string/categorical `obs` fields, and one unique `var` feature
index within the finite material budget. Sparse matrices, layers, raw slots, remote/backed arrays,
multi-file assembly, duplicate features, and oversized inputs abstain.

## Closed sensitivity declaration

The replicate-level calculation runs only when the already selected report contains exactly one
fenced block with this complete shape:

````text
```sc-referee-single-cell-sensitivity-v1
reported_table: path/to/results.csv
count_matrix: path/to/counts.h5ad
feature_id_column: feature_id
reported_adjusted_p_column: adjusted_p_value
reported_effect_column: effect
matrix_feature_index: var/_index
replicate_field: obs/replicate_id
condition_field: obs/condition
reference_level: control
test_level: treated
model: ~ condition
alpha: 0.05
reference_effect: 1.0
target_power: 0.8
minimum_powered_fraction: 0.8
reported_unit: observation
producer_binding: unresolved
dependence_semantics: unresolved
```
````

The nested fence above describes literal report text; do not copy the outer four-backtick fence.

Accepted closed values are:

- `reported_unit`: `observation`, `biological_replicate`, or `unresolved`;
- `producer_binding`: `exact` or `unresolved`; and
- `dependence_semantics`: `iid_rows`, `dependence_aware`, or `unresolved`.

Do not add or edit this declaration based on filename guesses, repository assertions, model
confidence, common practice, or the result you expect. Every scientific value must already be
present in the selected surface or be supplied explicitly by the scientist in a new review-scoped
surface. If a scientist supplies values, display the exact proposed block before any file change
and preserve `unresolved` for every unanswered field.

The initial model is deliberately limited to one already aggregated row per unique biological
replicate and one two-level condition model. The optional `single-cell-recompute` package extra is
required for PyDESeq2. Do not install it silently during an audit.

## Interpretation

The observation compares the reported discovery family with an auditor-owned replicate-level
negative-binomial Wald sensitivity calculation. It records matching/testability, survivors,
survival, and power separately. It does not prove:

- which project code executed;
- that the report table came from the inspected source excerpt;
- that the original model treated observations as independent;
- that a dependence-aware observation-level model is invalid;
- that disappearance in an underpowered calculation is evidence against the effect; or
- that the workflow or publication is correct or incorrect.

The module is Disclosure-only and cannot emit a production Finding.
