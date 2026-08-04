from pathlib import Path

counts = Path("inputs.csv").read_text().strip()
report = f"""[selected-result] {counts}
# Route-wide occurrence summary

The selected rate estimate is presented for the complete declared monitoring route. It uses the 60 retained transects as its exposure denominator. The 20 missing and filtered transects were left out of the denominator.
"""
Path("report.md").write_text(report)
