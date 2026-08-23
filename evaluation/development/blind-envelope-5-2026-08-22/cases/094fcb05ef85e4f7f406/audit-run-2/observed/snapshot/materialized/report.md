# Fast rotation versus set-stocking: standing herbage mass on upland sheep pasture

## Data description

The analysis reads one comma-separated file, `herbage_mass.csv`: a header line and 160 data rows.

**One row is one grid sampling point inside one paddock.** It is not a paddock and it is not a farm.
Ten sampling points were placed on a fixed grid inside every paddock, so **each paddock appears on
ten rows**. The ten rows that share a `paddock_name` are subsamples of the same fenced area, not ten
independent paddocks.

The columns, in file order:

| # | Column | Type | Meaning |
| --- | --- | --- | --- |
| 1 | `paddock_name` | text | Name of the fenced paddock the point sits in (for example `Whinny Knowe`). 16 distinct values, each on 10 rows. This identifies the experimental unit. |
| 2 | `rotation` | text | The grazing treatment the whole paddock was assigned. Two values, `fast_rotation` and `set_stocking`, 8 paddocks each. Constant within a paddock. |
| 3 | `grid_point` | whole number | Which of the ten fixed grid positions the sample came from, 1 to 10 within every paddock. It labels a position, so point 4 in one paddock has nothing to do with point 4 in another. |
| 4 | `sward_height_cm` | number, 1 decimal | Sward height at that point, in centimetres. Range in the file: 3.0 to 16.6. |
| 5 | `herbage_kg_dm_ha` | whole number | **The outcome.** Standing herbage mass at that point, kilograms of dry matter per hectare. Range in the file: 1021 to 3300. |

No values are missing: all 160 rows are complete in all five columns.

## Methods

The rotation was assigned to the whole fenced paddock, so the paddock is the experimental unit and
the ten grid points inside it are subsamples. The analysis runs in two separated steps.

1. **Reduction to the experimental unit.** `aggregate_to_paddocks()` averages the ten grid points
   within each paddock into a single herbage value and returns that 16-row per-paddock table.
2. **The test.** `compare_rotations()` takes that returned table and nothing else, so one paddock
   contributes one observation. It runs Welch's independent two-sample t-test, which is the
   two-sample t-test without the assumption that the two groups share a variance.

The sample size for the test is the number of paddocks, 16 in total and 8 per rotation. The 160 grid
points describe the sampling effort inside those units; they are not the sample size.

## Results

Sampling effort: 160 grid points, 16 paddocks, exactly 10 points per paddock.

Per-paddock mean herbage mass, kg DM/ha (spread is between paddocks, the units the test uses):

| Rotation | Paddocks (n) | Mean | SD | Range of paddock means |
| --- | --- | --- | --- | --- |
| `fast_rotation` | 8 | 2462.8 | 213.9 | 2173.2 to 2721.0 |
| `set_stocking` | 8 | 1522.7 | 125.9 | 1330.0 to 1658.0 |

Difference, fast rotation minus set-stocking: **940.1 kg DM/ha**.

Welch's independent two-sample t-test on the 16 paddock means: **t = 10.72, df = 11.33,
p = 0.00000028** (2.8 x 10^-7).

**Sample size: 16 paddocks (8 per rotation).**

Mean sward height follows the same pattern: 11.8 cm under the fast rotation against 6.4 cm under
set-stocking.

## Interpretation for grazing management

At the end of the growing season the fast rotation carried about 940 kg DM/ha more standing herbage
than the station's continuous set-stocking, roughly 62 percent more, and the gap is far larger than
the paddock-to-paddock variation within either group. Every fast-rotation paddock finished above
every set-stocked paddock, so the result does not rest on one or two unusual fields.

The likely mechanism is the long rest between short, intense grazing bouts: the sward gets an
uninterrupted stretch to regrow leaf, which the taller mean sward height under the fast rotation is
consistent with. For a manager, that extra standing herbage is feed available at the close of the
season, either as autumn grazing or as a bigger cover carried into winter.

Two cautions. The comparison rests on 8 paddocks per rotation at one station in one season, so it
says nothing directly about other sites, other years, or other stocking rates. And this study
measured standing herbage, not animal output, so it does not show that the extra mass was converted
into liveweight gain or wool.
