# ScienceAgentBench verified task 12

## Task

Train a drug-target interaction model using the DAVIS dataset to determine binding affinities
between several drugs and targets. Then use the trained model to predict binding affinities between
the antiviral drugs and the COVID-19 target. Rank the antiviral drugs by predicted affinity and
save the ordered drug names to `pred_results/davis_dti_repurposing.txt`, one name per line.

## Author-visible domain knowledge

A drug-target interaction model receives a drug represented by a SMILES string and a target protein
represented by its amino-acid sequence, then predicts a binding-affinity score. The DeepPurpose
library can be used for this task.

Typical drug encoders include ECFP fingerprints and message-passing neural networks over 2D
molecular graphs. Typical target encoders include 1D convolutional neural networks over amino-acid
sequences. DeepPurpose's `utils.data_process` can encode drug and target inputs using the selected
representations.

The model is normally trained as a regression on binding-affinity values, commonly with mean
squared error. At inference time, its predicted scores for one target are used to rank the drugs.

## Available inputs

```text
dti/
  antiviral_drugs.tab
  covid_seq.txt
  DAVIS/
    target_seq.json
    affinity_train.csv
    drug_train.txt
    drug_val.txt
    affinity_val.csv
```

The affinity files are numeric matrices, the drug files contain SMILES strings, the target JSON
maps target names to amino-acid sequences, the antiviral table contains `Name`, `Pubchem CID`, and
`SMILES`, and `covid_seq.txt` contains a sequence and target name on separate lines.

The task's gold program, evaluator, expected output, benchmark-paper case study, and prior solutions
are deliberately not available in the author workspace.

## Deliverable for this recurrence experiment

Create a small reviewable repository containing:

- `analysis.py`, implementing the requested workflow against the listed local input files;
- `REPORT.md`, stating the inputs, encodings, train/validation construction, affinity scale,
  inference target, ranking direction, and output format; and
- `requirements.txt`, listing necessary third-party packages.

Do not execute the analysis. Do not use sc-referee while authoring. Do not consult external
solutions or benchmark answer-side material.

## Provenance and ceiling

The task text is adapted from the ScienceAgentBench verified split at dataset revision
`9c6e96c9e74572e979b0930ee735041cef528cb7` under CC BY 4.0. This retained packet is public,
benchmark-derived, answer-side excluded, and ineligible for detector qualification or promotion.
