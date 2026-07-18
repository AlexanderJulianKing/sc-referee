# GB-P07: latent ambient-RNA confounding

This is a runnable, end-to-end demonstration of Referee's workflow compiler on the public
GeneBench-Pro GB-P07 benchmark. It requires the externally supplied `GB-P07-data.zip`; benchmark
bytes are not redistributed in this repository.

```bash
GBP07_ZIP="$HOME/Desktop/genebench_phase1_inputs/GB-P07-data.zip" \
  PYTHONPATH=src:. .venv/bin/python demos/genebench-gbp07/compile_demo.py
```

The script:

1. materializes the benchmark's cell, donor, and empty-droplet tables locally;
2. asks Claude to bind the unfamiliar files to Referee's typed inputs, or uses the bundled
   evidence-bound proposal when no API key is exported;
3. records the four scientific confirmations required for this demonstration;
4. deterministically reconstructs the published ambient-contamination basis;
5. checks whether the submitted fitted design contains that exact basis; and
6. freezes and replays the result without a model.

On the released benchmark bytes, the demo reports a **conditional major finding**: conditional on
the ratified scientific premises, the submitted fitted design omits the exact ratified contamination
basis. This is a structural containment result. It does **not** claim that the omission caused the
submitted sign error, or that adding this basis alone reproduces the benchmark reference answer.

`raw_compile_input/` is generated idempotently and ignored by Git. Set `GBP07_ZIP` to another path
if the archive is stored elsewhere. If the archive is absent or unreadable, the demo exits cleanly
with an explanatory message.

For the corrected investigation of the failure mode, see
[`docs/research/2026-07-11-gbp07-repro-results.md`](../../docs/research/2026-07-11-gbp07-repro-results.md).
