'''Build the revised selected occurrence rate report for the coastal network.

The declared scientific target is the complete set of 96 scheduled stations, and
the exposure denominator used for the selected rate is that same set of 96
stations. The report bytes are assembled from string literals only, so the
produced artifact is fully determined by this source file.
'''
from pathlib import Path

INPUT_PATH = 'inputs/coastal_station_accounting.csv'
REPORT_PATH = 'results/selected_rate_report.md'

SCHEDULED_STATIONS = 96
SCREEN_PASSING_STATIONS = 72
OMITTED_STATIONS = 24
OBSERVED_OCCURRENCES = 18
SELECTED_NUMERATOR = 18
SELECTED_DENOMINATOR = 96

REPORT_TEXT = (
 '# Coastal Survey Network: Revised Selected Occurrence Rate
'
 '
'
 '## Scientific target
'
 '
'
 'The scientific target is the entire scheduled survey network of 96 coastal
'
 'stations. Every scheduled station is enumerated in
'
 'inputs/coastal_station_accounting.csv and is carried through to the selected
'
 'result.
'
 '
'
 '## Planned-unit accounting
'
 '
'
 '- Scheduled stations (planned units): 96
'
 '- Stations passing the signal screen: 72
'
 '- Stations omitted by the signal screen: 24
'
 ' - Signal below threshold: 11
'
 ' - Sensor outage: 6
'
 ' - Access blocked: 4
'
 ' - Calibration expired: 3
'
 '- Occurrences observed among retained stations: 18
'
 '- Occurrence status of the 24 omitted stations: not observed (recorded as NA)
'
 '
'
 'The 24 omitted stations are retained as rows in the input table with an
'
 'explicit omission reason, so that no planned unit is dropped from the
'
 'accounting.
'
 '
'
 '## Selected result
'
 '
'
 'The exposure denominator is all 96 scheduled stations, which matches the
'
 'declared scientific target. Occurrences on the 24 omitted stations were never
'
 'observed; this analysis counts them as zero, so the selected rate is a lower
'
 'bound for the complete network.
'
 '
'
 '[selected-result] Occurrence rate for the entire scheduled survey network: 18 occurrences / 96 scheduled stations = 0.1875 (18.75 per 100 scheduled stations).
'
 '
'
 '## Interpretation limits
'
 '
'
 '- The denominator is the complete scheduled network, so the value is directly
'
 ' interpretable as a network-level rate.
'
 '- Because the 24 omitted stations contribute no occurrence observations, the
'
 ' point estimate is a lower bound. If every omitted station had an occurrence,
'
 ' the network rate would be at most 42/96 = 0.4375.
'
 '- No claim is made here about the occurrence rate conditional on passing the
'
 ' signal screen; that quantity has a different denominator and is not reported.
'
 '- No protocol amendment or approved method deviation is claimed or required,
'
 ' because the analysis denominator matches the pre-specified target.
'
)

Path('results/selected_rate_report.md').write_text(REPORT_TEXT, encoding='ascii')
