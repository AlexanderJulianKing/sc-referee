# Data description

## The file

`zebrafish_activity.csv` holds the novel-tank swimming data from the 14-day
low-dose fluoxetine exposure in adult zebrafish (*Danio rerio*). It is a plain
comma-separated file with a header line and 96 data rows.

## What one row is

One row is one fish. It carries that fish's identity, the tank it lived in, the
water condition that tank received, the fish's body size, and the total distance
it swam during its own 6-minute novel-tank video trial. Every fish was recorded
individually, so a fish appears exactly once in the file.

## Units and counts

- 8 tanks (3 L each), labelled `TNK-01` through `TNK-08`.
- 12 fish per tank, labelled `F01` through `F12` inside each tank.
- 96 rows in total, one per fish (8 tanks x 12 fish).
- Fluoxetine was dosed into the tank water, so the water condition was set once
  per tank and shared by all 12 fish in that tank.
- Rows are stored in collection order, tank by tank, starting at `TNK-01`.

## The two groups

The `exposure` column splits the file into two conditions, assigned whole tanks
at a time:

- **control** - clean system water. Tanks `TNK-01`, `TNK-02`, `TNK-03`, `TNK-04`;
  4 tanks, 48 fish.
- **fluoxetine** - 5 micrograms per litre waterborne fluoxetine for 14 days.
  Tanks `TNK-05`, `TNK-06`, `TNK-07`, `TNK-08`; 4 tanks, 48 fish.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `aquarium_ref` | text | The 3 L tank the fish lived in, written `TNK-01` through `TNK-08`. All 12 fish sharing a value here shared the same water. |
| `exposure` | text | The water condition that tank received: `control` or `fluoxetine`. Constant within a tank. |
| `fish_label` | text | Identifier for the individual fish, `F01` through `F12`. Unique within its tank, so a fish is identified by the pair (`aquarium_ref`, `fish_label`), not by `fish_label` alone. |
| `body_length_mm` | number | Standard length of the fish in millimetres, measured at the end of the exposure. Values run from 31.4 to 39.1 mm, one decimal place. |
| `distance_cm` | number | Total distance the fish moved during its 6-minute novel-tank trial, in centimetres. This is the outcome of interest. Values run from 838.7 to 1693.8 cm, one decimal place. |

## Missing data

None. All 96 rows have a value in all five columns.
