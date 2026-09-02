# Serum micronutrient status in treated coeliac disease

## What was compared, and why

Adults with coeliac disease can absorb nutrients poorly while the small bowel is damaged, and it is
not obvious how much of that shortfall is still present once a gluten-free diet has been in place
for a while. This clinic compared 60 adults with coeliac disease, all on a gluten-free diet for at
least one year, against 60 healthy adult controls matched on age band and sex. Each participant was
sampled once. The analysis plan declared six serum outcomes in advance and fixed their order:
ferritin, vitamin B12, folate, zinc, 25-hydroxyvitamin D, and magnesium.

## The data

`data.csv` has 120 rows plus a header. One row is one participant, sampled once, holding that
person's identifier, disease group, assigned study half, and all six serum measurements from that
single visit. There are no blank cells. The columns are:

- `participant_id`: participant identifier, `P001` to `P120`, unique in the file.
- `disease_group`: `coeliac` or `control`.
- `study_half`: `discovery` or `validation`, assigned by the study statistician before any
  measurement was taken.
- `serum_ferritin_ug_l`: serum ferritin, micrograms per litre.
- `serum_vitamin_b12_pmol_l`: serum vitamin B12, picomoles per litre.
- `serum_folate_nmol_l`: serum folate, nanomoles per litre.
- `serum_zinc_umol_l`: serum zinc, micromoles per litre.
- `serum_25oh_vitamin_d_nmol_l`: serum 25-hydroxyvitamin D, nanomoles per litre.
- `serum_magnesium_mmol_l`: serum magnesium, millimoles per litre.

The design is balanced: 60 participants per disease group, 60 per half, and 30 of each disease
group inside each half.

## The two-stage plan

The protocol fixed a screen-then-confirm plan before any data were seen. Stage one used the
discovery half only (30 coeliac, 30 control). All six declared outcomes were compared between the
groups with a two-sample t-test and screened at the conventional 0.05 level. Two outcomes passed:
ferritin (coeliac mean 27.2 ug/L, SD 10.7; control 74.5, SD 21.5; p = 1.7e-15) and zinc (coeliac
11.26 umol/L, SD 1.19; control 14.19, SD 1.57; p = 3.2e-11). Vitamin B12 (p = 0.62), folate
(p = 0.97), 25-hydroxyvitamin D (p = 0.77) and magnesium (p = 0.83) did not pass. Stage one is a
screen, so nothing there is confirmed.

Stage two used the validation half only (again 30 and 30) and tested only the two survivors. With
two outcomes carried forward, the 0.05 family error for the validation stage was split evenly, so
each survivor was judged against 0.05 / 2 = 0.025.

## Conclusions

Both survivors cleared the adjusted 0.025 level in the validation half. Ferritin was lower in the
coeliac group (mean 29.3 ug/L, SD 10.7, versus 73.6, SD 23.7; p = 3.7e-13). Zinc was also lower
(mean 11.44 umol/L, SD 1.11, versus 14.73, SD 2.04; p = 1.5e-10). Those two differences are the
confirmed findings.

Vitamin B12, folate, 25-hydroxyvitamin D and magnesium never reached the validation stage, so this
study confirms no difference between the groups on them. Ferritin and zinc are worth continued
monitoring in treated coeliac disease.
