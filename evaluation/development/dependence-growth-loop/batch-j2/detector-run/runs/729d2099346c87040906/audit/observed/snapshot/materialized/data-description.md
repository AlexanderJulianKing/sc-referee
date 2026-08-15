# Porosity screening of laser powder-bed fusion coupons

Eight print runs of Ti-6Al-4V test coupons were built on a laser powder-bed
fusion machine. Four runs were built at the nominal laser-power setting and
four at the elevated setting. The setting is a property of the whole run: it
is programmed once before the build starts and cannot vary within a run, so
every coupon in a run also shares that run's powder lot, recoater condition,
chamber gas flow, and thermal history.

After each build, three coupons were cut from the plate, one from each of the
three plate zones, and every coupon was scored pass or fail on a CT porosity
screen. That gives 3 coupon rows per run and 24 rows in total.

Columns:
- coupon_id: identifier for a single cut coupon (C001 through C024).
- print_run_id: identifier of the print run the coupon was cut from; eight
  runs, R01 through R08, three coupons each.
- laser_setting: nominal or elevated; fixed for an entire print run.
- plate_zone: build-plate zone the coupon came from (A, B, or C).
- coupon_mass_g: as-cut coupon mass in grams.
- porosity_screen: pass or fail on the CT porosity screen.

Because the treatment is applied at the run level and the three coupons from a
run share all of that run's build conditions, coupon outcomes within a run are
not expected to be independent of each other.

One row is: one cut coupon scored pass or fail on the CT porosity screen
Independent unit column: print_run_id
One trial is: one row
