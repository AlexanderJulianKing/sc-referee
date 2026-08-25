# Data description

## Files

### `make_data.py`
Deterministic seeded generator (seed `20260824`, NumPy `default_rng`). Running it with the project
Python rewrites `chocolate_batches.csv` with identical contents every time. It takes no inputs.

### `chocolate_batches.csv`
The analysis input. 60 data rows plus one header row, comma separated, no missing cells.

**One row is one production batch of 70 percent dark chocolate from a single cocoa origin**, sampled
once after a fixed tempering and resting schedule. Thirty batches were conched at 50 degrees Celsius
and thirty at 65 degrees Celsius, run in alternating blocks of five batches, so the two group labels
are interleaved across the batch sequence.

Columns, in file order:

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `batch_id` | string | none | Batch identifier, `B001` through `B060`, unique, in production order. |
| `conche_group` | string | none | Conching temperature group for that batch. Exactly two values: `conche_50c` (30 rows) and `conche_65c` (30 rows). |
| `particle_d90_um` | number, 1 decimal | micrometres | Particle size at the ninetieth percentile of the batch particle size distribution. Observed range 19.6 to 27.3. |
| `hardness_n` | number, 1 decimal | newtons | Snap hardness, peak force in a three-point snap test on the tempered bar. Observed range 37.3 to 65.9. |
| `melt_peak_c` | number, 2 decimals | degrees Celsius | Melting peak temperature of the batch. Observed range 32.07 to 34.06. |
| `gloss_gu` | number, 1 decimal | gloss units | Surface gloss of the moulded bar. Observed range 71.0 to 138.7. |
| `bitterness_score` | number, 1 decimal | score points | Trained-panel bitterness score on a zero to ten scale. Observed range 3.1 to 6.4. |

Each of the five outcome columns is measured once per batch, so every outcome value in a row belongs
to the same batch and every batch contributes exactly one value per outcome.

## How the values were produced

Each outcome is drawn independently per batch from a normal distribution with a group-specific mean
and a common within-group standard deviation, then clipped to the plausible instrument range and
rounded to the decimals shown above. Two outcomes, `gloss_gu` and `melt_peak_c`, also carry a small
shared batch-level tempering-quality term; that term is drawn from the same distribution in both
groups. Group means differ modestly for some outcomes and are set close together for others; the exact
generating means and standard deviations are in the `OUTCOME_SPEC` table in `make_data.py`.
