# Cinder Flats seed-coating trial data

The file data/input.csv holds the third-season results of a dryland restoration
trial on the Cinder Flats terrace. Twenty-four abandoned crop plots, each about
20 m by 20 m and separated from its neighbours by untreated buffer strips, were
sown a single time with a native perennial seed mix. Half the plots received
seed carried on a fungal-inoculant coating and half received uncoated seed; the
assignment was drawn at random plot by plot. At the end of the third growing
season a surveyor visited each plot once and recorded the percentage of ground
covered by established native perennials. No plot was sown twice, visited twice,
or split into subsamples, so there is exactly one measurement and exactly one
row per plot.

One row is: one abandoned dryland plot in the trial, sown once and scored once at the end of the third growing season

Independent unit column: plot_id

## Columns

- plot_id: the label painted on the plot's corner stake (CF-01 through CF-24).
  Every label appears once and identifies one physical patch of ground.
- treatment: which seed lot the plot was sown with, either inoculant_coated or
  uncoated.
- perennial_cover_pct: the share of the plot's surface, in percent, covered by
  established native perennials at the single third-season survey.

## How the numbers are read

The restoration permit sets 40 percent perennial cover as the pass mark, so each
plot is either at or above that mark or below it. Counting passes and failures
within each seed lot gives a two-by-two table whose four cells together contain
all 24 plots and no plot twice.
