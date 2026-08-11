# Capability maturity ledger

The canonical private projection is
[`CAPABILITY_MATURITY_LEDGER.json`](CAPABILITY_MATURITY_LEDGER.json). Regenerate it with:

```bash
python scripts/build_capability_maturity_ledger.py
```

Each entry reports six independent dimensions. `supported` describes a bounded implementation
path, not completion in every audit. `not_evidenced` is not a pass or scientific conclusion. The
ledger has no aggregate status. Exactly the complete-domain and dependence method-conflict
bindings have `finding_qualified: supported`, backed by their installed digest-closed Round-2
grants; every sibling binding and generic capability profile remains `not_evidenced`.

The ADR-0071 and ADR-0073 Round-2 records now enter this manifest-derived ledger through the
closed grant resource. Authority remains exact-binding-scoped: the shared detector stays
experimental, and its other twenty bindings receive no Finding capability.

This is a documentation artifact governed by
[ADR-0063](ADR-0063-INDEPENDENT-CAPABILITY-MATURITY-DIMENSIONS.md), not a v0.18 public record or a
source of detector authority.
