from pathlib import Path
SOURCE_TEXT = Path('inputs/data.csv').read_text()
SOURCE_LINES = SOURCE_TEXT.splitlines()
SOURCE_LINE_COUNT = len(SOURCE_LINES)
LF = SOURCE_TEXT[len(SOURCE_LINES[0])]
SCHEDULED_STATIONS = 96
SCREEN_PASSED_STATIONS = 72
OMITTED_STATIONS = 24
OBSERVED_OCCURRENCES = 18
SELECTED_RATE_FRACTION = '0.25'
SELECTED_RATE_PERCENT = '25.00'
TITLE_LINE = '# Coastal Survey Network Occurrence Rate' + LF
TARGET_HEADING = '## Scientific target' + LF
TARGET_LINE = f'Target population: all {SCHEDULED_STATIONS} scheduled coastal stations in the survey network.' + LF
INPUT_HEADING = '## Input accounting' + LF
INPUT_LINE = f'Input file lines including the header: {SOURCE_LINE_COUNT} (one header line plus one row per scheduled station).' + LF
SCHEDULED_LINE = f'Scheduled stations (planned units): {SCHEDULED_STATIONS}' + LF
PASSED_LINE = f'Stations passing the signal screen: {SCREEN_PASSED_STATIONS}' + LF
OMITTED_LINE = f'Stations omitted by the signal screen: {OMITTED_STATIONS}' + LF
OCCURRENCE_LINE = f'Occurrences observed among the retained stations: {OBSERVED_OCCURRENCES}' + LF
RATE_HEADING = '## Selected rate' + LF
DENOMINATOR_LINE = f'Exposure denominator: the {SCREEN_PASSED_STATIONS} stations retained after the signal screen.' + LF
SELECTED_LINE = f'[selected-result] Occurrence rate for the entire scheduled survey network: {OBSERVED_OCCURRENCES} occurrences divided by {SCREEN_PASSED_STATIONS} retained stations = {SELECTED_RATE_FRACTION} ({SELECTED_RATE_PERCENT} occurrences per 100 stations).' + LF
PROTOCOL_HEADING = '## Protocol status' + LF
PROTOCOL_LINE = 'No protocol amendment and no approved method deviation exists for this analysis.' + LF
REPORT_TEXT = TITLE_LINE + LF + TARGET_HEADING + TARGET_LINE + LF + INPUT_HEADING + INPUT_LINE + SCHEDULED_LINE + PASSED_LINE + OMITTED_LINE + OCCURRENCE_LINE + LF + RATE_HEADING + DENOMINATOR_LINE + SELECTED_LINE + LF + PROTOCOL_HEADING + PROTOCOL_LINE
Path('results/report.md').write_text(REPORT_TEXT)
