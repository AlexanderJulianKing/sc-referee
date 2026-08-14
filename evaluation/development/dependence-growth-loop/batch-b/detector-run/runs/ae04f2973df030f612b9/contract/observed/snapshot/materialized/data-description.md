# Hooked-stick choice assay in juvenile New Caledonian crows

Six hand-raised juvenile crows were each offered the same two-option foraging
puzzle four times: a baited log with one hooked stick and one straight stick
laid beside it. An observer recorded which stick the bird lifted first and how
long it took to make that first lift.

The file data/input.csv has 24 rows and six columns:

- bird_id: identity code of the crow (NC01 through NC06).
- trial_no: the trial number for that bird, 1 to 4.
- session: whether the trial ran in the morning or the afternoon block.
- hooked_stick_side: the side of the log the hooked stick was laid on.
- chose_hooked: 1 if the bird lifted the hooked stick first, 0 if it lifted the
  straight stick first.
- latency_s: seconds from the bird landing on the log to the first lift.

One row is: one tool-choice trial performed by one crow.
Independent unit column: bird_id

Every crow contributes four trials, so the rows arrive in clusters of four that
share the same bird, and birds differ markedly in how strongly they favour the
hooked stick.
