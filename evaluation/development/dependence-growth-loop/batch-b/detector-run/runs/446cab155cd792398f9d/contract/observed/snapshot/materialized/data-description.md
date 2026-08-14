# Fernbrook bioretention monitoring pilot: storm-event effluent samples

Eight bioretention cells built as part of the Fernbrook stormwater retrofit
were monitored through the 2024 wet season. Every cell has an underdrain
sampling port, and a grab sample of the cell's effluent was collected during
each of three monitored storms (S1 on 2024-05-14, S2 on 2024-07-02, and S3 on
2024-09-19). Each cell therefore contributes three samples to the file, and
the same eight cells reappear across the three storms.

Columns:

- cell_id: label of the bioretention cell the sample came from, BR-01 through BR-08. Each cell is a separate structure with its own soil column, planting and drainage.
- storm_id: label of the monitored storm during which the sample was taken (S1, S2 or S3). The same three storms were sampled at every cell.
- sample_date: calendar date of that storm.
- media_mix: filter media blend installed in the cell, either sand-compost or sand-biochar. This is a fixed property of the cell, so it repeats across all three of that cell's samples.
- antecedent_dry_days: whole days without measurable rainfall before the storm, recorded at the site rain gauge that serves all eight cells.
- effluent_tp_mgl: total phosphorus concentration measured in that effluent grab sample, in milligrams per litre.

The interim discharge target used by the pilot is 0.100 mg/L of total
phosphorus; a sample is spoken of as an exceedance when its measured
concentration is strictly above that value.

One row is: one storm-event effluent grab sample taken from one bioretention cell during one monitored storm
Independent unit column: cell_id
