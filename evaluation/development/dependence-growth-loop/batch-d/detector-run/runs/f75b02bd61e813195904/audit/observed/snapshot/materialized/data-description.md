# Biocrust monitoring data: inoculated rangeland plots

Twelve degraded rangeland plots, each 5 m x 5 m, were seeded once in September
2022 with a locally cultured cyanobacterial slurry. The plots lie at least 200 m
apart across the same station; each plot was fenced, treated and sampled on its
own, so no two plots share a treatment application, a fence or a handler.

Every plot was visited four times: immediately before seeding (the baseline
visit, month 0) and again 6, 12 and 18 months later. At each visit a composite of
ten shallow surface cores was assayed for chlorophyll a, consolidated crust cover
was scored inside the plot frame, and the surface temperature was read while the
cores were taken. The table is stored long, so the four visits to a plot appear
as four separate lines carrying the same plot identifier; those four lines are
repeated measurements of the same patch of ground, not four separate plots.

One row is: one monitoring visit to one restoration plot at one time point
Independent unit column: plot_id

Columns
- plot_id: label of the restoration plot; repeats across that plot's four visits.
- session_label: which visit the line records (baseline, followup_1, followup_2, followup_3).
- months_since_inoculation: whole months between seeding and the visit (0, 6, 12, 18).
- survey_date: calendar date of the visit (YYYY-MM-DD).
- chlorophyll_a_mg_m2: areal chlorophyll a density of the crust, in mg per square metre.
- crust_cover_pct: percentage of the plot frame covered by consolidated crust.
- surface_temp_c: soil surface temperature in degrees Celsius at the time of sampling.

Anything claimed about the effect of inoculation is a statement about plots, of
which there are twelve; the forty-eight lines are not forty-eight independent
observations, so the visits belonging to a plot have to be pooled into a single
plot-level value before any test that assumes independent rows is applied.
