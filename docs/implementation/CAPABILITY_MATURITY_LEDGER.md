# Capability maturity ledger

The canonical private projection is
[`CAPABILITY_MATURITY_LEDGER.json`](CAPABILITY_MATURITY_LEDGER.json). Regenerate it with:

```bash
python scripts/build_capability_maturity_ledger.py
```

Each entry reports six independent dimensions. `supported` describes a bounded implementation
path, not completion in every audit. `not_evidenced` is not a pass or scientific conclusion. The
ledger has no aggregate status, and all current `finding_qualified` values are `not_evidenced`.

Evaluation-private binding promotions in ADR-0071 and ADR-0073 deliberately do not enter this
manifest-derived ledger: neither private record is installed in `qualification-manifests.json`,
and neither grants production Finding authority.  The dependence binding is now maintainer-
promoted in the Track 2 roadmap while its `finding_qualified` ledger dimension truthfully remains
`not_evidenced` until Round-2 grant installation and production wiring.

This is a documentation artifact governed by
[ADR-0063](ADR-0063-INDEPENDENT-CAPABILITY-MATURITY-DIMENSIONS.md), not a v0.18 public record or a
source of detector authority.
