# Record and storage contract

## Canonical layer

- One JSON object per line for record collections.
- Human-editable YAML only for policy and scientist answers.
- UTF-8, sorted-key canonical JSON for digests.
- Stable record identities independent of SQLite row IDs.
- Large blobs stored by digest with explicit media type and provenance.
- Public `AdjudicatedRootCause` records use the same canonical JSONL layer; their review and
  adjudication references remain ordinary typed edges and SQLite remains a disposable projection.

## Generated layer

SQLite contains:

```text
records(record_type, record_id, json_text, digest)
edges(source_type, source_id, relation, target_type, target_id)
```

It is an index, not an authority. Rebuilding it from JSONL must be lossless with respect to queryable record content.

## Semantic lock

The lock includes:

- accepted claims and contracts;
- accepted assertions and remaining unknowns;
- observed result semantics used by detectors;
- detector-manifest digests;
- source snapshot digest;
- normalization version.

The lock excludes volatile timing, output paths, and provider session identifiers from the semantic digest.

The isolated qualification package also creates a separate scientific-label freeze. It binds the
exact Stage-1 freeze, Stage-2 review and packet digests, BenchmarkAdjudication digest, and every
AdjudicatedRootCause digest before detector output is visible. Its model-free replay is not a
replacement for the production audit semantic lock and grants no execution authority.
