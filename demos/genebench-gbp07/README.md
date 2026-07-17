# GeneBench-Pro GB-P07 — latent ambient contamination

**Status:** runnable end-to-end compiler and model-free replay demo.

```bash
GBP07_ZIP="$HOME/Desktop/genebench_phase1_inputs/GB-P07-data.zip" \
  PYTHONPATH=src:. .venv/bin/python demos/genebench-gbp07/compile_demo.py
```

The script builds `raw_compile_input/` idempotently, uses live Claude structural binding proposals
when `ANTHROPIC_API_KEY` is present (and a bundled canned proposal otherwise), runs the four-YES
scientific ceremony, freezes the capsule, and verifies a model-free `MATCH` replay. If the public
archive is unavailable, it prints a skip message and exits cleanly.

The public bytes are expected by default at
`~/Desktop/genebench_phase1_inputs/GB-P07-data.zip`; `GBP07_ZIP` overrides that location.

GB-P07 asks for the per-allele CXCL10 effect in activated monocytes. Claude Science submitted a
positive estimate while the graded reference is negative. The repository's earliest anchor blamed
allele orientation; the official walkthrough showed that diagnosis was wrong. The actual failure is
a latent technical contamination axis derived from ambient RNA.

The public benchmark zip is expected outside the repository:

```bash
export GBP07_ZIP="$HOME/Desktop/genebench_phase1_inputs/GB-P07-data.zip"
PYTHONPATH=src:. .venv/bin/python bench/gbp07_anchor.py
```

That anchor exercises an orientation gate and must **not** be presented as proof that Referee caught
GB-P07's true failure. The empty-droplet adapter and contamination contracts are implemented and
tested; the remaining gallery gate is a single, runnable folder whose ratified ambient basis reaches
the final latent-confounding verdict on the real bytes.

The compiler finding is deliberately narrow and conditional: it certifies exact basis containment
under ratified premises. It does not claim that the omission caused the submitted effect or that an
adjusted fit reproduces a benchmark answer.
