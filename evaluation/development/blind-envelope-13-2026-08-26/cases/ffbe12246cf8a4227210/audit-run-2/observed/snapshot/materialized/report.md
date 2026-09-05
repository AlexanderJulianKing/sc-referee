# Ostrich chick grower trial: standard versus lucerne-enriched ration

## Data

The data file is `ostrich_chick_grower_trial.csv`. One row is one ostrich chick. Sixty-four
individually identified chicks were reared on a commercial farm to 90 days of age, 32 on the
farm's standard grower ration and 32 on the lucerne-enriched, higher-fibre grower ration. Each
chick was measured once at the end of the rearing period, so the file holds 64 data rows plus a
header row and every chick has a value in every outcome column.

| Column | Meaning | Unit |
|--------|---------|------|
| `bird_id` | Identifier of the individual chick, `OS001` through `OS064` | none (identifier) |
| `diet_group` | Rearing diet the chick was allocated to: `standard` or `lucerne_enriched` | none (group label) |
| `body_weight_kg` | Live body weight at 90 days of age | kilograms (kg) |
| `average_daily_gain_g_per_day` | Average daily live-weight gain over the rearing period | grams per day (g/day) |
| `feed_conversion_ratio` | Feed consumed per unit of live-weight gain; lower is more efficient | none (kg feed per kg gain) |
| `tibiotarsus_length_cm` | Length of the tibiotarsus, the main lower leg bone, at 90 days | centimetres (cm) |
| `hock_circumference_cm` | Circumference of the hock joint at 90 days | centimetres (cm) |
| `serum_total_protein_g_per_l` | Total protein concentration in blood serum | grams per litre (g/L) |
| `serum_calcium_mmol_per_l` | Calcium concentration in blood serum | millimoles per litre (mmol/L) |
| `packed_cell_volume_percent` | Packed cell volume, the share of blood volume made up of red cells | percent (%) |

The measurements are invented for this project rather than collected from real birds.

## Method

`analysis.py` reads the CSV and compares the two diets on each of the eight outcomes declared in
the trial protocol, in the declared order. Every outcome is tested the same way, with a two-sided
two-sample Welch t-test, and the verdict for each outcome is read at the conventional 0.05
threshold. Group sizes are 32 standard and 32 lucerne-enriched for all eight outcomes. The
difference reported below is the lucerne-enriched mean minus the standard mean.

## Results by outcome

### 1. Body weight at 90 days (kg)

Standard 48.7406, lucerne-enriched 46.7687, difference -1.9719. t = -2.8719, p = 0.0056.

Significant at 0.05. Chicks on the lucerne-enriched ration were about 2 kg lighter at the end of
rearing. On a slaughter-weight basis that is a real loss of saleable body mass per bird, and it
would either shave the carcass weight at a fixed age or push back the age at which target weight
is reached.

### 2. Average daily gain (g/day)

Standard 481.6250, lucerne-enriched 462.0000, difference -19.6250. t = -3.6047, p = 0.0007.

Significant at 0.05. Growth was about 20 g/day slower on the lucerne-enriched ration, which is
the same story as the body weight result seen as a rate. Sustained over a rearing period this is
what produces the lighter final birds.

### 3. Feed conversion ratio (kg feed per kg gain)

Standard 3.1525, lucerne-enriched 3.3937, difference 0.2412. t = 5.5527, p = 0.0000 (below
0.0001).

Significant at 0.05. Birds on the lucerne-enriched ration needed about 0.24 kg more feed for each
kilogram of gain, so they were less efficient. Feed is the dominant cost in growing ostriches, and
a gap this size raises the feed bill per kilogram produced. This is the most clear-cut difference
in the trial.

### 4. Tibiotarsus length (cm)

Standard 38.2594, lucerne-enriched 38.2781, difference 0.0187. t = 0.0622, p = 0.9506.

Not significant at 0.05. Long-bone growth was effectively identical on the two rations. The
higher-fibre diet did not hold back skeletal length, which matters because stunted leg growth in
fast-growing ratites is associated with leg disorders.

### 5. Hock circumference (cm)

Standard 12.8844, lucerne-enriched 13.3156, difference 0.4313. t = 3.2208, p = 0.0021.

Significant at 0.05. Hocks were about 0.43 cm thicker on the lucerne-enriched ration. A thicker
hock joint alongside unchanged bone length is consistent with a slightly sturdier leg conformation
rather than with the classic mismatch of heavy body on slender legs. It should still be watched,
because hock swelling can also be a sign of joint problems, and this measurement alone cannot tell
sturdier apart from swollen.

### 6. Serum total protein (g/L)

Standard 35.4844, lucerne-enriched 36.2750, difference 0.7906. t = 1.7412, p = 0.0866.

Not significant at 0.05. Protein status in blood looked the same on both rations. Both group means
sit inside the range expected for healthy growing ostriches, so there is no sign that the
higher-fibre ration compromised protein nutrition.

### 7. Serum calcium (mmol/L)

Standard 2.3684, lucerne-enriched 2.4569, difference 0.0884. t = 3.8780, p = 0.0003.

Significant at 0.05. Serum calcium was about 0.09 mmol/L higher on the lucerne-enriched ration,
which fits lucerne being a calcium-rich forage. Both means remain within the normal range, so this
reads as a mild dietary shift in mineral supply rather than a disorder. It is worth keeping in view
when setting the calcium and phosphorus balance of the ration, since an oversupply of calcium can
interfere with phosphorus and trace mineral uptake.

### 8. Packed cell volume (%)

Standard 30.1250, lucerne-enriched 30.4563, difference 0.3313. t = 0.9816, p = 0.3302.

Not significant at 0.05. Red cell volume was comparable on both rations and both means fall in the
normal range for growing ostriches, giving no indication of anaemia or dehydration on either diet.

## Conclusion

Five of the eight declared outcomes differed significantly at the 0.05 threshold: body weight,
average daily gain, feed conversion ratio, hock circumference and serum calcium. Tibiotarsus
length, serum total protein and packed cell volume did not differ.

The pattern splits cleanly. On production, the lucerne-enriched ration was worse on all three
measures: lighter birds, slower gain, and more feed needed per kilogram of gain. On health and
skeletal development, it was neutral to mildly favourable: bone length, blood protein and packed
cell volume were unchanged, hock circumference was slightly larger, and serum calcium was slightly
higher while staying in the normal range.

## Recommendation for the farm

Keep the standard grower ration as the default for chicks reared to 90 days. The lucerne-enriched
ration cost roughly 2 kg of body weight and 0.24 kg of feed per kilogram of gain without buying any
measured health advantage in return.

Lucerne need not be abandoned outright. Two narrower uses are worth testing before any change to
the standard programme:

1. A lower lucerne inclusion rate, aimed at keeping the calcium and fibre contribution while
   recovering most of the growth and efficiency lost at the rate used here.
2. Lucerne later in the growing period, once the fastest growth phase is past and cheaper bulk feed
   is more attractive.

Whichever is tried, record hock condition alongside circumference. The larger hocks on the
lucerne-enriched ration are compatible with sturdier joints and with early joint swelling, and this
trial cannot separate the two. A follow-up trial should also confirm the calcium and phosphorus
balance of any lucerne-containing ration before it goes into routine use.
