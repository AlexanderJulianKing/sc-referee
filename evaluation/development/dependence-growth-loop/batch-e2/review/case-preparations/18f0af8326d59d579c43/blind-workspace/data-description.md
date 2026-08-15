# Ti-6Al-4V coupon microhardness survey

Twelve titanium alloy (Ti-6Al-4V) coupons were printed in a single laser
powder-bed build. Six coupons were kept in the as-built condition and six were
given a 730 C stress-relief anneal. Every coupon was then sectioned, mounted,
polished, and indented four times with a Vickers microhardness tester (0.5 kgf
load) at four positions across the polished face, so each physical coupon
contributes four hardness numbers to the table.

One row is: one Vickers microhardness indentation made on one coupon
Independent unit column: coupon_id

Columns in data/input.csv:

- coupon_id: label of the physical coupon that was indented (C01 through C12).
  Each label appears on four different rows, one per indentation.
- condition: heat treatment given to that coupon, either as_built or
  stress_relieved. It is a property of the coupon, so it is identical on all
  four rows that share a coupon_id.
- indent_index: 1 to 4, identifying which of the four indentations on that
  coupon the row records.
- hardness_hv: the measured Vickers hardness for that single indentation, in
  HV0.5.

The coupon is the thing that was randomly assigned to a heat treatment; the
four indentations on a coupon are repeated measurements of that same piece of
metal.
