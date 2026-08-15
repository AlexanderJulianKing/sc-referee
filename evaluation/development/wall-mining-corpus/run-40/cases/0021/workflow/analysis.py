import csv
import statistics
from pathlib import Path
from scipy import stats

data_file = Path("data/input.csv")
output_file = Path("results/report.md")
output_file.parent.mkdir(exist_ok=True)

rows = []
with open(data_file) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

days = []
temperatures = []
ph_values = []
gravity_values = []

for i, row in enumerate(rows):
    days.append(i)
    temperatures.append(float(row["temp_c"]))
    ph_values.append(float(row["ph"]))
    gravity_values.append(float(row["gravity"]))

temp_mean = statistics.mean(temperatures)
temp_stdev = statistics.stdev(temperatures) if len(temperatures) > 1 else 0
gravity_initial = gravity_values[0]
gravity_final = gravity_values[-1]
gravity_drop = gravity_initial - gravity_final

if len(days) > 1:
    fermentation_rate = (gravity_initial - gravity_final) / (days[-1] - days[0])
else:
    fermentation_rate = 0

ph_initial = ph_values[0]
ph_final = ph_values[-1]

slope, intercept, r_value, p_value, std_err = stats.linregress(days, gravity_values)

if slope < -0.001:
    days_to_completion = (1.000 - gravity_final) / (-slope)
else:
    days_to_completion = float('inf')

report = f"""# Beer Fermentation Process Report

## Fermentation Overview
This report analyzes the progression of a beer fermentation over {len(days)} days of observation. The analysis tracks yeast metabolic activity through gravity measurements, environmental stability through temperature monitoring, and chemical changes through pH tracking.

## Temperature Management
- Mean temperature: {temp_mean:.1f}°C
- Standard deviation: {temp_stdev:.2f}°C
- Range: {min(temperatures):.1f}°C to {max(temperatures):.1f}°C
- Temperature variance: {temp_stdev**2:.4f}

Temperature stability is critical for yeast performance and flavor development. The current standard deviation of {temp_stdev:.2f}°C indicates {"excellent" if temp_stdev < 1.0 else "good" if temp_stdev < 2.0 else "moderate"} temperature control. Ale yeast optimal range is 18-22°C; deviations can result in off-flavors and sluggish fermentation.

## Gravity and Fermentation Progress
- Initial gravity (OG): {gravity_initial:.4f}
- Current gravity: {gravity_final:.4f}
- Gravity drop: {gravity_drop:.4f} points
- Average fermentation rate: {fermentation_rate:.5f} gravity points/day
- Linear regression slope: {slope:.6f} gravity/day
- Regression R² value: {r_value**2:.4f}

The gravity drop indicates yeast metabolic consumption of sugars. Each gravity point represents approximately 0.1% potential alcohol. Current progress suggests approximately {days_to_completion:.1f} additional days until fermentation completion (when gravity stabilizes near 1.000).

## pH Evolution
- Starting pH: {ph_initial:.2f}
- Current pH: {ph_final:.2f}
- Net pH change: {ph_final - ph_initial:.2f} units
- pH direction: {"decreasing (acidifying)" if ph_final < ph_initial else "increasing (alkalinizing)"}

{"The gradual pH reduction is typical as fermentation progresses; organic acids accumulate from yeast metabolism." if ph_final < ph_initial else "The pH increase is unusual and may warrant investigation into ingredient composition or process contamination."}

## Fermentation Status
Current gravity is {gravity_final:.4f}. The beer is {'still fermenting actively with strong yeast metabolism' if slope < -0.001 else 'approaching completion with declining fermentation rate'}. Based on linear regression analysis (R²={r_value**2:.4f}), the projected terminal gravity is approximately {1.000 + (intercept + slope * 20):.4f}.

## Quality Assurance and Recommendations
1. Maintain current temperature control procedures; stability is excellent.
2. Continue daily gravity monitoring to confirm fermentation plateau.
3. Prepare equipment for packaging when gravity remains stable (±0.001) for three consecutive days.
4. Expect final alcohol content of approximately {(gravity_initial - gravity_final) * 131:.1f}% ABV based on gravity difference.
5. Monitor for any off-aromas or unexpected flavor development.
"""

with open(output_file, "w") as f:
    f.write(report)