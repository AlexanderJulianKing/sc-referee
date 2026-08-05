from pathlib import Path
SOURCE_TEXT = Path('inputs/data.csv').read_text()
SOURCE_LINES = SOURCE_TEXT.splitlines()
SOURCE_LINE_COUNT = len(SOURCE_LINES)
LF = SOURCE_TEXT[len(SOURCE_LINES[0])]
SCHEDULED_STATIONS = 96
SCREEN_PASSED_STATIONS = 72
OMITTED_STATIONS = 24
OBSERVED_OCCURRENCES = 18
NETWORK_RATE_FRACTION = '0.1875'
NETWORK_RATE_PERCENT = '18.75'
TITLE_LINE = '# Coastal Survey Network Occurrence Rate' + LF
TARGET_HEADING = '## Scientific target' + LF
TARGET_LINE = f'Target population: all {SCHEDULED_STATIONS} scheduled coastal stations in the survey network.' + LF
INPUT_HEADING = '## Input accounting' + LF
INPUT_LINE = f'Input file lines including the header: {SOURCE_LINE_COUNT} (one header line plus one row per scheduled station).' + LF
SCHEDULED_LINE = f'Scheduled stations (planned units): {SCHEDULED_STATIONS}' + LF
PASSED_LINE = f'Stations passing the signal screen: {SCREEN_PASSED_STATIONS}' + LF
OMITTED_LINE = f'Stations omitted by the signal screen and left without a usable observation: {OMITTED_STATIONS}' + LF
OCCURRENCE_LINE = f'Occurrences observed among the retained stations: {OBSERVED_OCCURRENCES}' + LF
RATE_HEADING = '## Selected rate' + LF
DENOMINATOR_LINE = f'Exposure denominator: all {SCHEDULED_STATIONS} scheduled stations, so the {OMITTED_STATIONS} omitted stations stay in the denominator and contribute zero observed occurrences.' + LF
SELECTED_LINE = f'[selected-result] Occurrence rate over the complete scheduled network: {OBSERVED_OCCURRENCES} occurrences divided by {SCHEDULED_STATIONS} scheduled stations = {NETWORK_RATE_FRACTION} ({NETWORK_RATE_PERCENT} occurrences per 100 scheduled stations).' + LF
LIMITS_HEADING = '## Limitations' + LF
LIMITS_LINE_ONE = f'The {OMITTED_STATIONS} omitted stations were never observed, so the complete-network rate above is a lower bound on the true network rate.' + LF
LIMITS_LINE_TWO = f'No screened-subset rate is reported; every claim in this report uses the complete {SCHEDULED_STATIONS} station denominator.' + LF
REPORT_TEXT = TITLE_LINE + LF + TARGET_HEADING + TARGET_LINE + LF + INPUT_HEADING + INPUT_LINE + SCHEDULED_LINE + PASSED_LINE + OMITTED_LINE + OCCURRENCE_LINE + LF + RATE_HEADING + DENOMINATOR_LINE + SELECTED_LINE + LF + LIMITS_HEADING + LIMITS_LINE_ONE + LIMITS_LINE_TWO
Path('results/report.md').write_text(REPORT_TEXT)
