# Weekly gas sampling of twelve lab-scale anaerobic digesters

Twelve 5 L bench-top anaerobic digesters were run side by side in a feeding trial. Six vessels were fed the standard maize-silage ration and six the enriched ration (maize silage plus mineral-supplemented cattle manure and biochar fines). Every vessel was sampled once a week for five consecutive weeks (run weeks 3 to 7, i.e. after acclimation), so the file stores each vessel five times over, once per sampling week. The weekly records belonging to a vessel are repeated measures on that same reactor, not separate experiments.

One row is: one weekly headspace gas sample taken from one digester vessel in one run week
Independent unit column: vessel_id

## Columns

- vessel_id: label of the digester vessel, D01 to D12. A vessel was built, inoculated and fed once; it is the thing that was assigned to a ration and it is what varies independently.
- feed_blend: the ration the vessel received, either standard or enriched. Constant across all weeks of a given vessel.
- run_week: week number since start-up on which the sample was taken (3 to 7).
- ch4_percent: methane fraction of the headspace gas for that sample, in percent by volume.
- digestate_ph: pH of the digestate measured during the same visit.

## Size and scope

The file has 60 data rows: 12 vessels multiplied by 5 weekly samples. Any statement made at the ration level rests on 12 values, one per vessel, rather than on the 60 stored rows.
