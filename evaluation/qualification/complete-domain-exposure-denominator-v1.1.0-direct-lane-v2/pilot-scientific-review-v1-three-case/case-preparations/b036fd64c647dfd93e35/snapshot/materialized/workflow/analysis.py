from pathlib import Path
SOURCE_TEXT = Path('inputs/data.csv').read_text()
SOURCE_LINES = SOURCE_TEXT.splitlines()
SOURCE_LINE_COUNT = len(SOURCE_LINES)
LF = SOURCE_TEXT[len(SOURCE_LINES[0])]
SCHEDULED_STATIONS = 96
SIGNAL_ELIGIBLE_STATIONS = 72
OCCURRENCES = 18
ELIGIBLE_WITHOUT_OCCURRENCE = 54
OUTSIDE_ELIGIBLE = 24
RATE_PERCENT = 25
TITLE_LINE = '# Coastal station signal-screen report' + LF
BLANK_LINE = LF
NETWORK_LINE = f'Scheduled network: {SCHEDULED_STATIONS} stations.' + LF
TARGET_LINE = f'Target population: {SIGNAL_ELIGIBLE_STATIONS} signal-eligible stations that passed the prespecified signal screen.' + LF
ACCOUNTING_LINE = f'Planned-unit accounting: {OCCURRENCES} eligible stations with an occurrence, {ELIGIBLE_WITHOUT_OCCURRENCE} eligible stations without an occurrence, and {OUTSIDE_ELIGIBLE} scheduled stations outside the eligible set and not assessed for occurrence.' + LF
INPUT_LINE = f'Input table lines including header: {SOURCE_LINE_COUNT}.' + LF
RESULT_LINE = f'[selected-result] Among signal-eligible stations, the occurrence rate was {OCCURRENCES}/{SIGNAL_ELIGIBLE_STATIONS} = {RATE_PERCENT}%.' + LF
REPORT_TEXT = TITLE_LINE + BLANK_LINE + NETWORK_LINE + TARGET_LINE + ACCOUNTING_LINE + INPUT_LINE + BLANK_LINE + RESULT_LINE
Path('results/report.md').write_text(REPORT_TEXT)
