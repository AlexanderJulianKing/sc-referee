# Biermann et al. — experimental-unit correction

**Status:** runnable compact published-human-data demo.

The original tumor-cell differential-expression analysis tested cells as independent observations.
Referee recomputes the same Brain-versus-Peripheral comparison using patients as independent units.

```bash
.venv/bin/referee demos/biermann-pseudoreplication
```

Expected measured result: **16,289 reported discoveries → 770 patient-level survivors**. In other
words, **95.3% lose significance after correcting the experimental unit**. Referee withholds a hard
blocker because the corrected patient-level analysis is underpowered; that qualification is part of
the finding, not a footnote.

See [`ATTRIBUTION.md`](ATTRIBUTION.md) for data and analysis-code provenance.

This folder ships the 27-patient pseudobulk sufficient for the corrected DE test so it runs
immediately. To rebuild from the official 145,555-cell GEO count matrix and run Referee on the
82,783-cell tumor subset itself, use
[`../biermann-pseudoreplication-full/`](../biermann-pseudoreplication-full/).
