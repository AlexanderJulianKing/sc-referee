# Coral nubbin calcification data

The file `data/input.csv` comes from a 28-day aquarium heat-stress trial on the
branching coral Acropora. Six parent colonies were collected from a single reef
flat and assigned to tanks: three colonies were held at the ambient summer
temperature and three were held at an elevated temperature. Two nubbins were cut
from each colony, mounted separately, and weighed by the buoyant-weight method at
the start and the end of the trial, giving one net calcification rate per nubbin
in milligrams of CaCO3 per gram of skeleton per day.

The temperature treatment was applied to whole colonies, and the two nubbins from
a colony share that colony's genotype and its tank, so the two rows carrying the
same colony label are repeated measurements of the same coral rather than
separate corals.

Columns:

- colony_id: label of the parent colony that a nubbin was cut from
- thermal_regime: tank temperature treatment applied to that colony, either
  "ambient" or "heated"
- nubbin_id: label of the individual nubbin
- nubbin_area_cm2: skeletal surface area of the nubbin in square centimetres
- net_calcification_mg_g_d: measured net calcification rate of the nubbin

One row is: one nubbin's net calcification measurement, taken from one parent colony
Independent unit column: colony_id
