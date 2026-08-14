# Bench-scale anaerobic digestion trial: feedstock pretreatment and methane yield

Ten identical 5 L bench-scale mesophilic digesters (operated at 35 degrees C) were
inoculated from a single shared batch of digestate and then run in parallel on a
wheat-straw feedstock. Five vessels were fed untreated straw and five were fed
steam-exploded straw. The pretreatment was assigned to the whole vessel at the
start of the trial and never changed, so a digester belongs to exactly one
treatment group for the whole experiment.

Each digester was then operated for four consecutive semi-continuous feeding
cycles. At the end of every cycle the biogas produced during that cycle was
quantified with a wet gas meter and its methane fraction determined by offline gas
chromatography, giving one specific methane yield per cycle.

The file is stored in long format: one line per digester per cycle, so each of the
ten vessels contributes four lines and the file has forty lines of data.

Columns
- digester_id: label of the physical reactor vessel, D01 to D10.
- pretreatment: feedstock treatment of that vessel, "untreated" or "steam_exploded".
- feed_cycle: cycle number within the vessel, 1 to 4, in chronological order.
- vs_loading_g_per_l_d: organic loading rate during the cycle, g volatile solids per litre of working volume per day.
- ch4_yield_ml_per_g_vs: specific methane yield of the cycle, mL of methane per g of volatile solids fed.

One row is: one feeding cycle of one digester, with the specific methane yield measured at the end of that cycle
Independent unit column: digester_id

Because both the randomisation and the treatment act on the vessel, the four lines
that share a digester label are repeated measurements of the same unit rather than
four separate samples: cycles from one vessel share its inoculum, its seal, its
mixing and its temperature history. There are ten independent units in the file,
not forty, so any comparison between the two feedstock groups should be carried
out on ten values, one summary per vessel.
