# Duck mussel warming trial: clearance-run records

Twelve adult duck mussels (Anodonta anatina) were collected from a single lowland canal,
tagged, and housed one animal per flow-through chamber. Each animal was given three
baseline clearance runs (days 0, 2 and 4), then a 10-day exposure to water held about
3 degrees Celsius above its acclimation temperature, then three further clearance runs
(days 16, 18 and 20). Every run was carried out at the same test temperature, near
15 degrees Celsius, and clearance was estimated from the fall in algal cell concentration
over a fixed run window.

The file `data/input.csv` is stored in long format: the same mussel appears six times,
once per clearance run.

One row is: a single clearance run on one tagged mussel on one measurement day
Independent unit column: mussel_id

Columns:

- `mussel_id`: tag code of the animal (MU-01 to MU-12); the same code marks every run from that animal
- `session_no`: run number within the animal, 1 to 6 in time order
- `phase`: `pre` for baseline runs, `post` for runs after the warming exposure
- `days_from_baseline`: whole days elapsed since that animal's first run
- `shell_length_mm`: shell length measured at tagging, repeated on all runs of the animal
- `test_temp_c`: water temperature during the run, in degrees Celsius
- `clearance_rate_l_h`: particle clearance rate for the run, in litres per hour

Because the six records of a mussel are repeated measurements of the same animal in the
same chamber, they are not six independent observations. A comparison of the two phases
has to work from a single summary per animal per phase, which yields twelve independent
within-animal changes.
