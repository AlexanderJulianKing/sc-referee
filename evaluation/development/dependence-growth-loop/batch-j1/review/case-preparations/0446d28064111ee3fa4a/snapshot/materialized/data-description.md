# Modal impact tests on machine-tool bases

A machine shop wanted to know whether machine-tool bases poured from polymer
concrete damp vibration better than bases cast from gray iron. Twelve finished
bases were built: six gray cast iron and six polymer concrete. Each base was
suspended on air springs, fitted with a single accelerometer, and struck with an
instrumented modal hammer. A test engineer kept five usable strikes on every
base, so the table contains several rows that come from the same physical base.

One row is: one instrumented hammer strike on one machine-tool base
Independent unit column: base_id

Columns

- base_id: label of the physical base that was struck (CI-01..CI-06 are the gray
  cast iron bases, PC-01..PC-06 the polymer concrete ones)
- base_material: the material the base was made from, gray_cast_iron or
  polymer_concrete
- strike_index: which of the five recorded strikes on that base this row holds
- mount_preload_nm: bolt preload used on the mounting fixture, newton-metres
- peak_accel_g: peak accelerometer response for the strike, in g
- damping_ratio_pct: first-mode damping ratio fitted from the strike response,
  as a percentage of critical damping

The material is a property of the base, not of the individual strike: every
strike on a given base carries the same base_material value.
