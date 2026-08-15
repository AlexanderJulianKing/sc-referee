# Cave cricket stridulation recordings

Twelve adult cave crickets from a single laboratory colony were kept for eight
weeks in one of two rearing chambers: an ambient chamber and a water-saturated
chamber, six animals in each. At the end of the rearing period every cricket
was moved to a recording box and its stridulation was recorded four separate
times, with the animal returned to its chamber between takes. From each
recording the peak frequency of the dominant stridulation band was read off the
spectrum and written down in kilohertz.

The file data/input.csv has a header and 48 data lines, with these columns:

- cricket_tag: the permanent paint tag of the animal (CK-01 to CK-12). The same
  tag appears on four lines, one line per recording of that animal.
- chamber_humidity: the rearing chamber the animal lived in, either "ambient"
  or "saturated". It is a property of the animal, not of the single recording,
  so it is the same on all four lines that carry a given tag.
- take_no: which of that animal's four recordings the line reports (1 to 4).
- peak_khz: peak frequency of the dominant stridulation band in that recording,
  in kilohertz, to one decimal place.

One row is: one stridulation recording (one take) of one cricket
Independent unit column: cricket_tag
