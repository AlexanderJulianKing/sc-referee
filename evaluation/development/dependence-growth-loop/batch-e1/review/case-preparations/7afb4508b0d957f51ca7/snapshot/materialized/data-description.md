# What is in data/input.csv

Each heat-ramp trial run on a tagged shore periwinkle is recorded on its own
line. Twelve snails were collected from one rocky platform, six from the
high-shore band and six from the low-shore band, and each snail was ramped on
four separate trial days. A line gives the snail tag, the shore band the snail
was collected from, which of the four trial days the ramp happened on, the
snail's shell length in millimetres, and ctmax_c, the body temperature in
degrees Celsius at which that snail lost its righting response during that
particular ramp.

One row is: one heat-ramp trial on one tagged periwinkle on one trial day
Independent unit column: snail_id

Column guide:
- snail_id: tag of the individual snail (12 distinct tags, 4 lines each)
- shore_zone: "high" or "low", the band the snail was collected from
- trial_day: 1 to 4, which repeat ramp the line comes from
- shell_length_mm: shell length of that snail, in millimetres
- ctmax_c: critical thermal maximum on that ramp, in degrees Celsius
