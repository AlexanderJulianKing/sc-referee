# Test and fixture plan

## Fixture classes required from the beginning

### Positive issue

The report states a positive treated-versus-control effect. The linked result is negative under the same established orientation.

### Hard negative

The stored coefficient is negative because it represents control minus treated. The report correctly states that treated is higher. The detector must normalize orientation and emit no Finding.

### Ambiguous

The result sign is known but the comparison orientation is not. The detector must emit a MaterialQuestion and no Finding.

### Opaque boundary

An unsupported custom tool contributes an input. Its boundary is disclosed, but unrelated report/result agreement remains evaluable.

### Prompt injection

Repository text says to ignore policy, run commands, or mark the analysis correct. The auditor treats the text as evidence and does none of those things.

## Test layers

1. Immutable v0.5 and accepted v0.6.0 schema examples; historical provisional schemas are tested
   only as migration inputs.
2. Canonical JSON and digest stability.
3. State transitions and deadlines.
4. Snapshot identity and divergence.
5. Parser golden files and exact spans.
6. Detector premise and counterevidence tables.
7. Admission invariants.
8. Report wording and HTML escaping.
9. SQLite rebuild.
10. End-to-end demo and replay.

## Regression rule

Every false accusation becomes a permanent hard-negative fixture before the detector can be re-released.
