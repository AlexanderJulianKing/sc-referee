# Reference baselines

- `specification-v0.5.0-draft/` is the architecture and product baseline.
- `schemas-v0.5.0/` is the immutable public record-schema baseline.
- `schemas-v0.6.0/` is the accepted local public schema release implementing ADR-0002.
- `schemas-v0.7.0/` is the immutable accepted interaction release implementing ADR-0004;
  v0.6.0 remains immutable.
- `schemas-v0.8.0/` is the accepted local public multidimensional-lineage release implementing
  ADR-0005; v0.7.0 and earlier accepted releases remain immutable.
- The adjacent ZIP files are the original packaged distributions and checksums.
- `../BASELINE_LOCK.json` records the exact digests embedded in this starter.

Do not edit immutable baseline copies to make implementation code pass. Propose an ADR and schema
revision instead. W3ID deployment and publication of a local release remain separate gates.
Implementation-only record experiments belong under `provisional-schemas/`.
