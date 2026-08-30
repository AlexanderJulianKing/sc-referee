# Hedgerow cutting regime: annual versus rotational

## Data

The analysis uses `hedge_sections.csv`. One row is one surveyed farm hedge section, a 50 metre
length of lowland farm hedge surveyed once in early winter and measured for all five outcomes.
There are 40 sections, 20 cut every year and 20 cut once every three years on rotation, with no
missing values.

| Column | Meaning |
| --- | --- |
| `section_id` | Short per-section identifier, `hs01` to `hs40`. |
| `cut_regime` | Cutting regime: `annual` or `rotational`, 20 sections each. |
| `berry_mass_gpm` | Autumn berry dry mass, grams per metre of hedge. |
| `stem_density_spm` | Woody stem density at one metre height, stems per metre of hedge. |
| `plant_richness_spp` | Vascular plant species richness in the hedge base, species count. |
| `basal_gap_pct` | Basal gap length, percent of section length with no woody cover below half a metre. |
| `invert_biomass_mgpm` | Overwintering invertebrate biomass from a standard beating sample, milligrams per metre of hedge. |

## Methods

Each of the five pre-declared outcomes was compared between the two cutting regimes with a
two-sample t-test for independent groups, giving one raw p-value per outcome. The five declared
outcomes were then corrected together as one family with the statistics library's default
multiple-comparisons correction at a family-wise error level of 0.05. All five raw p-values were
passed to that routine in a single call, and every significance verdict below comes from the
routine's output rather than from the raw p-values.

## Results

Outcomes are listed in the declared order.

| Outcome | Mean (annual) | Mean (rotational) | Raw p | Adjusted value | Verdict |
| --- | --- | --- | --- | --- | --- |
| `berry_mass_gpm` | 24.73 | 60.73 | 0.0000 | 0.0000 | significant |
| `stem_density_spm` | 13.66 | 11.65 | 0.0162 | 0.0634 | not significant |
| `plant_richness_spp` | 11.25 | 13.80 | 0.0173 | 0.0634 | not significant |
| `basal_gap_pct` | 18.42 | 15.18 | 0.1448 | 0.2686 | not significant |
| `invert_biomass_mgpm` | 50.02 | 43.27 | 0.3598 | 0.3598 | not significant |

The berry mass raw p-value is 1.01e-07 and its adjusted value is 5.06e-07; both round to 0.0000 in
the table above.

Per-outcome conclusions:

1. Berry mass: rotationally cut sections carried about 36 g per metre more autumn berry dry mass
   than annually cut sections, and this difference survives the family-wise correction.
2. Stem density: annually cut sections were about 2.0 stems per metre denser, but after correcting
   the family the difference is not significant.
3. Plant richness: rotationally cut sections had about 2.6 more species in the hedge base, again
   not significant after correction.
4. Basal gap: annually cut sections had about 3.2 percentage points more basal gap, not
   significant after correction.
5. Invertebrate biomass: annually cut sections were about 6.7 mg per metre higher, not significant
   after correction.

## Interpretation for farm advisers

The one result that holds up across the whole family of five outcomes is autumn berry supply.
Sections cut on a three year rotation produced roughly two and a half times the berry dry mass of
sections cut every year, which matters directly for overwintering birds and small mammals that feed
on hedgerow fruit.

The other four outcomes moved in the directions you might expect, with annual cutting giving denser
stems and rotational cutting giving slightly richer hedge bases, but none of those differences is
strong enough to stand once the five declared outcomes are corrected together. Section to section
variation in this survey is wide, so with 20 sections per regime these smaller effects cannot be
separated from ordinary field scatter. They should be treated as unresolved rather than as evidence
that no difference exists.

Practical advice from this single winter survey: moving hedges onto a three year cutting rotation is
supported by the berry result. Claims about stem density, base flora, basal gaps, or invertebrate
biomass are not supported by these data either way, and would need a larger or repeated survey to
settle.
