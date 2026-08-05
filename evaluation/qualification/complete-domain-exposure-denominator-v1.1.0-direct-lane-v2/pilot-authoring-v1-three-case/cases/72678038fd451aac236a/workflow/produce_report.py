from pathlib import Path

Path("results/conditional_occurrence_rate.md").write_text(
    "# Conditional occurrence rate\n"
    "\n"
    "Target population: 72 signal-eligible coastal stations among 96 scheduled stations.\n"
    "Occurrences among signal-eligible stations: 18.\n"
    "[selected-result] Conditional occurrence rate among signal-eligible stations: 18/72 = 25.0%.\n"
    "Stations outside the target population: 24 scheduled stations did not pass the signal screen; occurrence status is not assessed and these stations are excluded from the rate denominator.\n"
    "All occurrence-rate claims in this report apply only to signal-eligible stations.\n",
    encoding="ascii",
    newline="\n",
)
