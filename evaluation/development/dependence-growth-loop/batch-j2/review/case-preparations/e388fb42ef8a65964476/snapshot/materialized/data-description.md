# What `data/input.csv` contains

The file holds the 2024 end-of-season shoreline survey of restored coastal foredunes.
Field crews walked a 350 km stretch of open coast and stopped at a fixed marker every
3.5 km, which gave 100 restoration sites separated by at least 3.5 km of shoreline.
Each site was visited once, and the surveyor wrote down a single summary judgement of
the dune vegetation found there.

Columns:

- `site_id`: the permanent identifier of the restoration site, FD-001 through FD-100.
  Each identifier appears on exactly one line of the file.
- `shore_marker_km`: how far the site sits from the northern end of the surveyed coast,
  in kilometres.
- `foredune_width_m`: width of the vegetated foredune at the site, in metres.
- `sand_ph`: pH of a composite surface sand sample taken at the site.
- `cover_class`: the single vegetation cover class assigned to the site during the
  visit, one of `sparse`, `patchy` or `closed`.

There are no repeat visits, no subplots and no sub-samples anywhere in the file. Nothing
is nested inside anything else: the survey recorded one line per site, so the 100 lines
are 100 separate sites, and the cover-class tally is a tally over separate sites.

One row is: one restored coastal foredune site, visited once during the 2024 end-of-season survey and given a single vegetation cover class
Independent unit column: site_id
