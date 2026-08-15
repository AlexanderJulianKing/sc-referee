# Photovoltaic anti-soiling field trial

This file records a dust-accumulation trial run on a single utility-scale solar
array in a semi-arid site. Twelve photovoltaic modules were enrolled in the
trial: six of them received a nanocoat anti-soiling surface layer, and six were
left bare to serve as controls. Every enrolled module was visited once a week
for five consecutive weeks. At each visit the field crew measured how much
power that module was losing to accumulated dust, expressed as a percentage of
what the same module produces when freshly cleaned.

What the columns mean:

- module_id: the label stencilled on the physical module that was inspected.
  PV-C01 through PV-C06 are the coated modules; PV-U01 through PV-U06 are the
  bare controls.
- coating: whether that module carries the nanocoat layer ("nanocoat") or no
  treatment at all ("bare").
- inspection_week: which of the five weekly inspection rounds the reading comes
  from, numbered 1 through 5.
- power_loss_pct: the soiling-induced power loss recorded at that inspection,
  in percent.

Because the same twelve modules were revisited week after week rather than
replaced, each module supplies five separate rows to the file, and readings
that share a module label describe the same piece of hardware at different
points in time.

One row is: one weekly soiling inspection of one photovoltaic module
Independent unit column: module_id
