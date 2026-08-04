# Prospective author-submission ingestion

`scripts/seal_prospective_author_submissions.py` is an evaluation-private, non-executing intake
boundary for one frozen `prospective_author_queue`. It requires the queue's externally retained
digest, the named author's execution-context identifier, an explicit seal timestamp, and one
submission directory named exactly for every opaque case in the queue.

Each case directory is named by the 20 lowercase hexadecimal characters after `case:` and contains
`SUBMISSION.json` with exactly the fields frozen by `AUTHOR_DELIVERY_PROTOCOL.md`:

```json
{
  "opaque_case_id": "case:0123456789abcdefabcd",
  "assignment_token": "assignment:opaque-token",
  "execution_context_id": "context:isolated-context",
  "authored_at": "2026-08-05T09:00:00Z",
  "selected_report_path": "REPORT.md",
  "source_path": "analysis.py",
  "data_dictionary_path": "DATA_DICTIONARY.md"
}
```

The author JSON need not be canonical or self-digested. It is parsed as strict JSON with duplicate
keys rejected, and its exact original bytes are retained. The three selected paths must be the
fixed root files shown above. A root `COORDINATOR_CHANGE_NOTE.md` is required for a corrected twin
and forbidden for every other cell. No additional file or nested directory is accepted. Path
escapes, links, special files, identity or token changes, missing/replacement cases, and timestamps
outside `authored_at <= sealed_at <= frozen deadline` fail closed. The coordinator—not the author—
computes every accepted file's byte size and digest and records the bounds in the canonical,
self-digested seal manifest.

Example:

```bash
python scripts/seal_prospective_author_submissions.py \
  --author-queue frozen-author-queue.json \
  --expected-queue-digest sha256:... \
  --submission-root author-submissions \
  --author-execution-context-id context:isolated-context \
  --sealed-at 2026-08-05T11:00:00Z \
  --output-root coordinator/sealed-author-submission
```

The destination must not exist. The command copies the accepted bytes, emits a self-digested
manifest, and marks copied files read-only. It does not execute project code, review scientific
meaning, determine whether an intended cell is correct, create a label or detector output, emit a
Finding, or make a qualification decision.
