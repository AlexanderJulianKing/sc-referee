# Reduced stocking density and shell height in Pacific oysters

## Question

Does growing Pacific oysters at a reduced stocking density produce taller shells than the farm's
standard stocking density after a twenty-week grow-out?

## The trial

Fourteen mesh grow-out baskets were hung along a single longline. Seven baskets were stocked at the
farm's standard density and seven at a reduced density, alternating along the line. After twenty
weeks the baskets were lifted and twelve oysters were taken from each basket and measured for shell
height in millimetres, to one decimal place. That gives 168 measured oysters, 84 in each density
group.

## Data description

The data live in `oyster_shell_height.csv`, one header row and 168 data rows.

**One row is one measured Pacific oyster.**

| Column | Type | Values | Meaning |
|---|---|---|---|
| `basket_id` | text label | `B01` through `B14` | The grow-out basket the oyster was taken from. |
| `density_group` | text label | `standard`, `reduced` | The stocking density the oyster was grown at. |
| `oyster_number` | integer | 1 through 12 | Counter for the oysters taken from one basket; it restarts at 1 in each basket. |
| `shell_height_mm` | decimal number | 45.1 to 82.5 | Shell height of that oyster in millimetres, to one decimal place. |

There are no missing values.

## Analysis

Shell heights of the 84 reduced-density oysters were compared with those of the 84 standard-density
oysters using an independent two-sample t-test on the group means, run over every measured oyster in
the table. The script is `analysis.py`.

## Results

| Group | Oysters | Mean shell height (mm) | SD (mm) | Range (mm) |
|---|---|---|---|---|
| Standard density | 84 | 61.61 | 6.76 | 45.1 to 76.7 |
| Reduced density | 84 | 67.92 | 6.24 | 53.9 to 82.5 |

Total oysters measured: **168**.

Difference in means (reduced minus standard): **6.30 mm**.

Two-sample t-test: **t(166) = 6.280, p = 2.86 x 10^-9**.

## Conclusion

Reduced stocking density increased shell height. Oysters grown at the reduced density were 6.30 mm
taller on average than oysters grown at the farm's standard density, 67.92 mm against 61.61 mm, and
the difference is statistically significant at p = 2.86 x 10^-9. Over a twenty-week grow-out, giving
the animals more room in the basket buys about six millimetres of shell height.
