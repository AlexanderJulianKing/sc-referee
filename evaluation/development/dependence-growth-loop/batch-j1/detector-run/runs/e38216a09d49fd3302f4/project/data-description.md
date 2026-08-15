# Coupon tensile testing records

data/input.csv holds the measurements from a small additive-manufacturing
study. Twelve metal build plates were produced on the same laser powder-bed
fusion machine: six plates were printed lying flat and six were printed on
edge. After printing, each plate was sectioned into four tensile coupons taken
from fixed positions A, B, C and D across the plate, and every coupon was
pulled to failure on the same test frame.

Columns in the file:

- coupon_id: label for the individual tensile coupon.
- plate_id: label of the build plate the coupon was cut from. Each plate label
  appears four times, once per coupon cut from that plate.
- build_orientation: how the plate was oriented during printing, either flat
  or edge. The value is a property of the plate, so it is the same for all
  four coupons from a plate.
- coupon_slot: which of the four positions on the plate the coupon came from.
- tensile_strength_mpa: ultimate tensile strength of the coupon in megapascals.

One row is: one tensile coupon cut from a build plate and pulled to failure
Independent unit column: plate_id
