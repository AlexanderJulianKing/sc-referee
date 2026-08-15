# What is in data/input.csv

A materials lab asked whether a post-print annealing step raises the tensile
strength of 3D-printed PLA. Twelve filament spools were purchased as separate
lots (SP01-SP12). Each spool was printed into six identical dogbone coupons on
the same printer with the same slicer profile, and the spool as a whole was
assigned to one post-print condition: left as printed, or annealed at 90 C for
two hours and cooled slowly. Every coupon was then pulled to failure at
5 mm/min and its ultimate tensile strength was recorded in megapascals.

Because the treatment was applied per spool, the six coupons that share a
spool_id come from the same material lot and the same treatment run; they are
repeated measurements of that spool rather than separate lots.

One row is: one tensile coupon pulled to failure, listing the spool it was printed from, its post-print condition, its mass, and its ultimate tensile strength
Independent unit column: spool_id

Columns:
- spool_id: the filament spool (SP01-SP12) the coupon was printed from; six coupons share each spool.
- anneal_condition: as_printed or annealed; fixed for a whole spool.
- coupon_id: label of the coupon within its spool (C1-C6).
- coupon_mass_g: mass of the machined coupon, in grams.
- uts_mpa: ultimate tensile strength of the coupon, in megapascals.
