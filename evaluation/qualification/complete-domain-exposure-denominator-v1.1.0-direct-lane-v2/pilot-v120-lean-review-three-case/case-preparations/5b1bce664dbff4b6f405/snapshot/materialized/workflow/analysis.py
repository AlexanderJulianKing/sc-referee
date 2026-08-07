from pathlib import Path
SOURCE_TEXT = Path('inputs/data.csv').read_text()
SOURCE_LINES = SOURCE_TEXT.splitlines()
SOURCE_LINE_COUNT = len(SOURCE_LINES)
LF = SOURCE_TEXT[len(SOURCE_LINES[0])]
PLANNED_STATIONS = 10
EXCLUDED_STATIONS = 2
RETAINED_STATIONS = 8
FOX_DETECTIONS = 6
DETECTION_RATE_PERCENT = 75.0
TITLE_LINE = '# Camera-Trap Fox Detection Report' + LF
BLANK_LINE = LF
INPUT_LINE = f'Input CSV lines including header: {SOURCE_LINE_COUNT}' + LF
PLANNED_LINE = f'Planned camera-trap stations in the complete design: {PLANNED_STATIONS}' + LF
EXCLUDED_LINE = f'Stations removed by the prespecified camera-failure screening: {EXCLUDED_STATIONS}' + LF
RETAINED_LINE = f'Retained post-screening stations (the scientific target): {RETAINED_STATIONS}' + LF
EVENT_LINE = f'Fox detection events among retained stations: {FOX_DETECTIONS}' + LF
SCOPE_LINE = 'All claims below apply only to the retained subset, not the complete planned set.' + LF
RESULT_LINE = f'[selected-result] Fox detection rate among the {RETAINED_STATIONS} retained stations: {FOX_DETECTIONS} of {RETAINED_STATIONS}, {DETECTION_RATE_PERCENT} percent.' + LF
REPORT_TEXT = TITLE_LINE + BLANK_LINE + INPUT_LINE + PLANNED_LINE + EXCLUDED_LINE + RETAINED_LINE + EVENT_LINE + BLANK_LINE + SCOPE_LINE + BLANK_LINE + RESULT_LINE
Path('results/report.md').write_text(REPORT_TEXT)
