# Orb-weaving spiders at lit and unlit park sites

## What was compared and why

Streetlights change how much light, and how many flying insects, reach a spider's web
at night. We asked whether adult female orb-weavers living under streetlights differ
from those at unlit sites in the same city park system. Sixty spiders were collected on
consecutive still nights, thirty from lit sites and thirty from unlit sites at least two
hundred metres away. Each spider and its web were measured once, at dawn, before
collection. The field plan declared five outcomes in advance and fixed their order:
body mass, cephalothorax width, web capture area, mesh width, and prey items in the web.

## The data file

`data.csv` has a header row and 60 data rows. One row is one adult female spider
together with the single web that spider occupied when it was measured. Each spider
appears once, and there are no blank cells. The columns are:

- `spider_id`: identifier for the individual spider, `SP01` through `SP60`.
- `site_lighting`: the lighting condition of the collection site, either `lit` or
  `unlit`, with thirty rows carrying each value.
- `body_mass_mg`: body mass in milligrams.
- `cephalothorax_width_mm`: width of the cephalothorax at its widest point, in millimetres.
- `web_capture_area_cm2`: area of the capture spiral of the web, in square centimetres.
- `mesh_width_mm`: spacing between neighbouring capture threads, in millimetres.
- `prey_items`: count of prey items present in the web at dawn.

## The overall screen

Before looking at any single outcome, the plan calls for one overall screening number
built from all five outcomes at once. For each outcome we take the gap between the two
group means, ignore its sign, and divide it by the pooled standard deviation of that
outcome. That turns each gap into a common currency, roughly "how many typical spiders
apart the two groups sit." Averaging those five numbers gives the screen. The cut-off
was fixed at 0.40 before the analysis.

For this data set the five standardised differences are 1.9280 for body mass, 0.1482 for
cephalothorax width, 0.0606 for web capture area, 0.2154 for mesh width, and 1.7477 for
prey items. Their average is 0.8200, which is above the 0.40 cut-off, so the screen
passes.

The per-outcome comparisons run only when the screen passes. The screen acts as a gate
on the whole declared family: if the groups look alike overall, the family is not pursued
and no individual outcome is tested or reported. Because the screen passed here, all five
comparisons were carried out with a two-sample t-test at the conventional 0.05 threshold.

## Results by outcome

1. **Body mass (mg).** Lit sites averaged 152.83 (SD 21.71), unlit sites 112.91
   (SD 19.65). p = 4.8e-10, significant. Spiders under streetlights were clearly heavier.
2. **Cephalothorax width (mm).** Lit 3.52 (SD 0.54), unlit 3.45 (SD 0.36). p = 0.568,
   not significant.
3. **Web capture area (cm2).** Lit 422.61 (SD 106.40), unlit 429.19 (SD 110.34).
   p = 0.815, not significant.
4. **Mesh width (mm).** Lit 4.18 (SD 0.73), unlit 4.04 (SD 0.57). p = 0.407, not
   significant.
5. **Prey items (count).** Lit 7.27 (SD 2.59), unlit 3.37 (SD 1.81). p = 7.2e-09,
   significant. Webs under streetlights held more prey at dawn.
