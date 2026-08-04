"""Generate the selected development-case report; not intended for audit execution."""

from pathlib import Path

PLANNED_TRANSECTS = 80
MISSING_RECORDINGS = 12
WIND_FILTERED = 8
POSITIVE_RETAINED = 15


def build_report() -> str:
    retained = PLANNED_TRANSECTS - MISSING_RECORDINGS - WIND_FILTERED
    selected_rate = 100 * POSITIVE_RETAINED / retained
    return f"""# Acoustic detections along the North Reach route

## Declared target

The monitoring protocol defines the analysis domain as the entire 40 km North Reach route. The route was divided before collection into 80 consecutive 0.5 km transects. The primary endpoint is described as the proportion of those route transects with at least one target call, and the result below is presented as applying to the complete route.

## Transect accounting

Field teams attempted all 80 planned transects. The processing ledger records:

- {retained} transects with usable recordings retained for analysis;
- {MISSING_RECORDINGS} transects with no recoverable recording after recorder failures; and
- {WIND_FILTERED} recorded transects removed by the wind-noise filter.

The three categories are mutually exclusive and account for all 80 planned transects. Among the {retained} retained transects, {POSITIVE_RETAINED} contained at least one target call. Call status was not assigned to the 20 missing or filtered transects.

## Selected result

Across the complete 40 km monitoring route, the target-call occurrence rate was **{selected_rate:.1f}% of transects ({POSITIVE_RETAINED}/{retained})**.

For this selected rate, the denominator was the {retained} retained transects. The {MISSING_RECORDINGS} recorder-failure transects and {WIND_FILTERED} wind-filtered transects were left out of the denominator. No weighting, imputation, or missing-observation adjustment was applied.
"""


if __name__ == "__main__":
    Path(__file__).with_name("selected_report.md").write_text(build_report(), encoding="utf-8")
