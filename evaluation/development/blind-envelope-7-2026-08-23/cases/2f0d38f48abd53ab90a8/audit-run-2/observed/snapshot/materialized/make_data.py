"""Generate the artificial reef fish-count survey table.

Sixteen artificial reef modules (eight simple block modules, eight complex
high-relief modules) were each surveyed by divers five times over one summer.
One row of the output CSV is one dive survey of one module.

Structure of the simulated numbers:
  * design means: simple modules ~22 fish per survey, complex modules ~31
  * module-to-module differences: SD ~9 fish (a module keeps its own level
    across all five of its surveys)
  * survey-to-survey wobble within a module (tide, time of day): SD ~7 fish
  * counts are rounded to whole fish and floored at zero

Standard library only. Fixed seed, so re-running reproduces the CSV exactly.
"""

import csv
import os
import random

SEED = 20260823

N_MODULES_PER_DESIGN = 8
N_SURVEYS_PER_MODULE = 5

DESIGN_MEAN = {"simple_block": 22.0, "complex_high_relief": 31.0}
BETWEEN_MODULE_SD = 9.0
WITHIN_MODULE_SD = 7.0

OUT_NAME = "reef_fish_surveys.csv"


def build_rows(rng):
    rows = []
    module_number = 0
    for design in ("simple_block", "complex_high_relief"):
        for _ in range(N_MODULES_PER_DESIGN):
            module_number += 1
            module_id = "MOD{:02d}".format(module_number)
            # One draw per module: this module's own standing level.
            module_effect = rng.gauss(0.0, BETWEEN_MODULE_SD)
            for survey_number in range(1, N_SURVEYS_PER_MODULE + 1):
                survey_noise = rng.gauss(0.0, WITHIN_MODULE_SD)
                value = DESIGN_MEAN[design] + module_effect + survey_noise
                fish_count = int(round(value))
                if fish_count < 0:
                    fish_count = 0
                rows.append(
                    {
                        "module_id": module_id,
                        "reef_design": design,
                        "survey_number": survey_number,
                        "fish_count": fish_count,
                    }
                )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fieldnames = ["module_id", "reef_design", "survey_number", "fish_count"]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} ({} data rows)".format(out_path, len(rows)))


if __name__ == "__main__":
    main()
