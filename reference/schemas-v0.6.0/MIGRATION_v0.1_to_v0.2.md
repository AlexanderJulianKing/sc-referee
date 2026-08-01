# Migration from schema 0.1.0 to 0.2.0

Version 0.2.0 is breaking.

## Assessment records

- Migrate only demonstrated, fully admitted v0.1 findings to `Finding`.
- Migrate conditional v0.1 records to `ConditionalConcern` plus a linked `MaterialQuestion`.
- Migrate unresolved semantic items to `MaterialQuestion`.
- Migrate lineage, coverage, opacity, unsupported-path, and reproducibility items to `Disclosure` or `CoverageRecord`.
- Do not migrate `supported` or `hypothesis` labels mechanically. They require reclassification. Production model-generated hypotheses are dropped from the v1 product path.

## Dispositions

Move scientist responses into `ScientistDisposition`. Replace a scientist-entered `false_positive` with `disputed` unless an independent adjudication exists. Store objective labels in `Adjudication`.

## Confidence and impact

Remove numeric finding confidence. Preserve qualitative assertion certainty only with a basis. Keep severity and publication materiality only on demonstrated findings. Use potential impact, question priority, or disclosure importance for other records.

## Detector records

Add explicit permitted output types, finite counterevidence protocol entries, fixture classes, and finding maturity restrictions. Re-run old detector results because 0.2.0 has a stricter admission contract.

## Canonical schemas

The record union references standalone canonical schemas. Implementations must not maintain separately embedded schema copies.
