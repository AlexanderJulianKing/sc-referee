# blaKPC Allele Concordance Audit

## Scope

Measured units: 24 clinical Klebsiella pneumoniae isolates staged in inputs/data.csv.
Observed call: per-isolate blaKPC PCR call, staged in column pcr_call as 0 or 1.
Reference panel: per-isolate blaKPC allele supplied in column panel_allele as 0 or 1.
The analysis uses the supplied reference panel in the coding in which it is supplied.

## Concordance accounting

Total measured units: 24
Units whose pcr_call equals the panel_allele as staged in inputs/data.csv: 19
Match credit per agreeing unit: 1
Mismatch credit per remaining unit: 0
Per-unit agreement rate used in the emission accumulation: 0.208333 (5/24)
Accumulated concordance emission: 5.000 credits

## Selected result

[selected-result] Observed-versus-panel concordance across 24 measured isolates: per-unit agreement rate 0.208333 (5/24), for an accumulated concordance emission of 5.000 credits.

## Provenance

Every number above is computed by workflow/analysis.py from inputs/data.csv.
No protocol amendment or approved method deviation exists.
