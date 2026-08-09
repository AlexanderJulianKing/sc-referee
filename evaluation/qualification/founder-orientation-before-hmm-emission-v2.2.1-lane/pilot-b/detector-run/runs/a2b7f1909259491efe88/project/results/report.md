# blaKPC Allele Concordance Audit

## Scope

Measured units: 24 clinical Klebsiella pneumoniae isolates staged in inputs/data.csv.
Observed call: per-isolate blaKPC PCR call, staged in column pcr_call as 0 or 1.
Reference panel: per-isolate blaKPC allele supplied in column panel_allele as 0 or 1.
The comparison reads each column in the coding in which inputs/data.csv stages it.

## Concordance accounting

Total measured units: 24
Units whose pcr_call equals the staged panel_allele: 19
Units carrying the mismatch credit: 5
Match credit per agreeing unit: 1
Mismatch credit per remaining unit: 0
Per-unit agreement rate used in the emission accumulation: 0.791667 (19/24)
Accumulated concordance emission: 19.000 credits

## Selected result

[selected-result] Observed-versus-panel concordance across 24 measured isolates: 19 agreeing units at a per-unit agreement rate of 0.791667 (19/24), for an accumulated concordance emission of 19.000 credits.

## Provenance

Every number above is computed by workflow/analysis.py from inputs/data.csv.
No protocol amendment or approved method deviation exists.
