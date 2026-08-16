import csv
import statistics
from pathlib import Path
from scipy import stats


def main():
    input_file = Path("data/input.csv")
    output_file = Path("results/report.md")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read and organize data by treatment group
    groups = {}
    with open(input_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row["treatment_group"]
            reaction_time = float(row["reaction_time_ms"])
            if group not in groups:
                groups[group] = []
            groups[group].append(reaction_time)
    
    # Extract reaction times by group
    control_times = groups.get("control", [])
    caffeine_times = groups.get("caffeine", [])
    
    # Validate that both groups have data
    if not control_times or not caffeine_times:
        raise ValueError("Both control and caffeine groups required")
    
    # Calculate summary statistics
    control_mean = statistics.mean(control_times)
    caffeine_mean = statistics.mean(caffeine_times)
    control_std = statistics.stdev(control_times)
    caffeine_std = statistics.stdev(caffeine_times)
    
    # Perform independent samples t-test
    t_statistic, p_value = stats.ttest_ind(control_times, caffeine_times)
    
    # Build markdown report
    report = f"""# Caffeine and Cognitive Processing Speed

## Study Design
Participants were randomly assigned to receive either 100mg of caffeine or a placebo.
Each participant completed a visual reaction time task.
Reaction times were measured in milliseconds, with lower values indicating faster responses.

## Results

### Descriptive Statistics

| Group | N | Mean (ms) | SD (ms) |
|-------|---|-----------|---------|
| Control | {len(control_times)} | {control_mean:.2f} | {control_std:.2f} |
| Caffeine | {len(caffeine_times)} | {caffeine_mean:.2f} | {caffeine_std:.2f} |
| Difference | | {control_mean - caffeine_mean:.2f} | |

### Inferential Statistics
An independent samples t-test was conducted to compare reaction times between groups.

**Test Results:**
- t-statistic: {t_statistic:.4f}
- p-value: {p_value:.4f}

## Interpretation
"""
    
    if p_value < 0.05:
        if caffeine_mean < control_mean:
            report += f"Caffeine significantly improved reaction time (p = {p_value:.4f}). "
            report += f"The caffeine group was {control_mean - caffeine_mean:.2f} ms faster on average."
        else:
            report += f"Caffeine significantly slowed reaction time (p = {p_value:.4f}). "
            report += f"The caffeine group was {caffeine_mean - control_mean:.2f} ms slower on average."
    else:
        report += f"No significant difference in reaction time was observed between groups (p = {p_value:.4f}). "
        report += "The observed difference is consistent with random variation."
    
    with open(output_file, "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()