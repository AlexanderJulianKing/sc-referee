# sc-referee demo gallery

Each directory has one job in the story. A demo is either **runnable**, **mechanism-only**, or
**gated**; those labels are evidence boundaries, not marketing qualifiers.

| Demo | Status | What it demonstrates | Run |
|---|---|---|---|
| [`biermann-pseudoreplication/`](biermann-pseudoreplication/) | runnable · compact published-data demo | 16,289 cell-level discoveries become 770 after patient-level recomputation | `.venv/bin/referee demos/biermann-pseudoreplication` |
| [`biermann-pseudoreplication-full/`](biermann-pseudoreplication-full/) | reproducible full build · official public matrix | downloads GSE200218, reconstructs 82,783 tumor nuclei, proves exact equality with the compact capsule, and runs Referee on the sparse cell matrix | see its README |
| [`kang-paired-ifnb/`](kang-paired-ifnb/) | runnable after local build · published human data | a strong IFN-β response partly survives donor-level correction, separating true biology from cell-count inflation | see its README |
| [`multi-claim-pipeline/`](multi-claim-pipeline/) | runnable · synthetic | one project, three separately routed claims: gene expression, alternative splicing, and cluster abundance | `.venv/bin/referee demos/multi-claim-pipeline` |
| [`genebench-gbp07/`](genebench-gbp07/) | gated · public benchmark data | the real latent ambient-contamination failure chain that motivated contamination contracts | see its README |

## Rules for adding a demo

1. State whether the data are published, synthetic, or externally supplied.
2. Name the exact claim Referee evaluates and the exact thing the demo proves.
3. Freeze any headline number with a regression test.
4. Never describe `needs_evidence` or a mechanism component as an end-to-end catch.
5. Keep every report artifact bound to its own claim and producing code path.
