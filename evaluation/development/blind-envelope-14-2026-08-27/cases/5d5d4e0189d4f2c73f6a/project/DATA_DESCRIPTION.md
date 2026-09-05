# Data description

**File:** `carpal_tunnel_splint_trial.csv` (one CSV, comma separated, with a header row)

**What one row is:** one adult participant in the hand therapy trial, holding that person's
allocation and their end-of-week-six assessment. Each participant was assessed once, at the end of
week six, and the same set of measurements was recorded for everyone, so there is exactly one row
per participant and no repeated measures.

**Size:** 66 rows plus the header. 33 participants in the `night_splint` arm and 33 in the
`no_splint` arm. Every participant has a value for every outcome; there are no blank cells.

## Columns

| # | Column | Type | Description |
|---|--------|------|-------------|
| 1 | `participant_id` | text | Unique participant label, `P001` through `P066`, in enrollment order. |
| 2 | `allocation` | text | Group assignment. Exactly two values: `night_splint` (neutral-position night splint worn on the affected wrist for six weeks) and `no_splint` (same advice and ergonomic education, no splint). |
| 3 | `symptom_severity_score` | number, 1 decimal place | Declared outcome 1. Symptom severity on a 1 to 5 scale; higher means worse symptoms. Observed range 1.4 to 4.2. |
| 4 | `functional_status_score` | number, 1 decimal place | Declared outcome 2. Functional status on a 1 to 5 scale; higher means more difficulty with everyday hand tasks. Observed range 1.4 to 3.8. |
| 5 | `night_awakenings_per_week` | whole number | Declared outcome 3. Nights in the past week with symptom-related awakening, 0 to 7. |
| 6 | `two_point_discrimination_mm` | number, recorded to the nearest 0.5 mm | Declared outcome 4. Static two-point discrimination at the index fingertip, in millimetres; higher means coarser sensation. Observed range 2.5 to 8.0. |
| 7 | `distal_motor_latency_ms` | number, 2 decimal places | Declared outcome 5. Distal motor latency of the median nerve, in milliseconds; higher means slower conduction. Observed range 3.40 to 6.35. |

Columns 3 through 7 appear in the order the protocol declared the five outcomes.

## Recording conventions

- The two 1-to-5 clinical scales are reported to one decimal place, as the questionnaire scoring
  gives them.
- Night awakenings are counted in whole nights, capped at the 7 nights in a week.
- Two-point discrimination is read off a graded caliper, so it is recorded on a 0.5 mm grid.
- Distal motor latency comes from the nerve conduction machine, which reports two decimal places.
