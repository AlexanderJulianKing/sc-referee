# Pilot f review, attempt 1 retirement disclosure

Under the envelope-10 retired-attempt precedent, the first primary review attempt
for pilot f is retired, not repaired, and re-run once with a fresh reviewer
identity that has observed no case.

## Retired attempt

- Reviewer identity: `actor:founder-f-reviewer-fable-08`
- Model: `claude-fable-5` (pinned binary `2.1.221`)
- Session id: `164023d9-e564-5108-ae9e-7d821df5b14d`
- Prompt digest: `sha256:c9882c7ba8464f18612e42f85b6d9f30cd23ebdbd8c86df1004c2d0176b7e4ed`
- Stdout digest: `sha256:f8057a2edb9e69b782fc2ff44d3dc7257ef46cd8c88ce1f2bb760fec9eda88ab`
- Transport error: none (the one-shot call completed cleanly)

## Why it was retired

The one-shot call completed transport-clean and returned a well-formed batch
review payload, but the payload was wrapped in a triple-backtick ```json ...```
markdown code fence. The frozen review path parses the returned text as JSON
directly and strips no fence, so the payload could not be projected into review
records. This is the same failure class the precedent covers: a review call that
completed but whose single output cannot pass deterministic projection. It
differs from pilot d only in cause -- there a quoted evidence span matched no
visible line; here the whole payload is unparseable JSON because of the fence.

Re-firing the retained call is forbidden. The process-capture path, session
identity, and transmitted prompt are all keyed by participant, so the retry
under `actor:founder-f-reviewer-fable-09` gets its own capture path and cannot
reuse attempt 1's retained bytes.

## Retained evidence in this lane

- `review/process-captures/primary-founder-f-reviewer-fable-08/` (stdout, stderr, capture.json)
- `review/prompt-primary-attempt-1-retired.txt`
- `review/packets-primary-retired/` (attempt-1 packets, moved aside by the pipeline
  when the reviewer identity changed)

## Escalation reviewer

`actor:founder-f-reviewer-opus-06` keeps its ordinal. It never ran in attempt 1
and observed no case, so its identity is unspent.
