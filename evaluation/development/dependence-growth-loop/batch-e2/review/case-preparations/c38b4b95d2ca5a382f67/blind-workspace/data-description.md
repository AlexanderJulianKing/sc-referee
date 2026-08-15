# What is in data/input.csv

These are the daily water-use logs from a small crossover trial on a rooftop
planter array. Fourteen modular planters (P01 to P14) were metered on six
consecutive days in July 2025. Each planter spent three of those days under a
perforated shade screen and three days with its top open. Which days were
screened was counterbalanced across the array: P01 to P07 were screened on the
odd-numbered dates and P08 to P14 on the even-numbered dates.

Because every planter appears six times, the file is in long format and the
rows are repeated measurements of the same fourteen planters, not eighty-four
independent observations.

One row is: one planter module's water-use log for a single day, under whichever top treatment that module had on that day

Independent unit column: module_id

Columns

- module_id: label of the planter module, P01 to P14; each label appears six times
- screen_state: "screened" if the perforated shade screen was fitted that day, "open" if the module was uncovered
- session_index: 1, 2 or 3, counting the module's logging days within the given screen_state
- log_date: calendar date of the log, ISO format
- mean_air_temp_c: mean daytime air temperature at the module, in degrees Celsius
- et_mm_day: measured evapotranspiration for that module-day, in millimetres per day

Any comparison of the screened and open conditions has to respect that
structure: the fourteen planters, and not the eighty-four daily logs, are the
independent units of the trial.
