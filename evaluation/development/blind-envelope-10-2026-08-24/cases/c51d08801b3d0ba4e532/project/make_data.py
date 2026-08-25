"""Deterministic generator for the indoor-pool lifeguard airway dataset.

Writes lifeguard_airway.csv next to this script: one row per lifeguard,
23 lifeguards working at municipal pools disinfected with chlorine alone
and 23 working at pools using combined chlorine and ultraviolet treatment.
Each lifeguard is assessed once, at the end of a working week, after at
least six months at the facility.

Two latent per-lifeguard traits are drawn first so that the seven outcomes
are correlated the way repeated airway measures on one person are:

  irritation  higher means a more irritated airway (raises exhaled nitric
              oxide, symptoms, eye irritation and cough days, lowers serum
              CC16)
  lung        higher means better spirometry (raises both FEV1 % predicted
              and FVC % predicted, which is why those two track each other)

Run:  python make_data.py
"""

import csv
import os

import numpy as np

# Fixed so the CSV regenerates byte-for-byte. Chosen from a small set of
# candidate seeds so that the realized group differences line up with the
# effect pattern encoded in OUTCOMES below rather than with an unlucky draw.
SEED = 6
N_PER_GROUP = 23

# Outcome parameters: mean at chlorine-only pools, mean at chlorine+UV pools,
# within-group standard deviation, lower bound, upper bound, decimal places.
OUTCOMES = {
    "feno_ppb":             (22.5, 17.6, 6.5, 5.0, 45.0, 1),
    "fev1_pct_pred":        (96.2, 99.4, 7.5, 80.0, 115.0, 1),
    "fvc_pct_pred":         (100.4, 101.1, 7.0, 85.0, 118.0, 1),
    "airway_symptom_score": (8.1, 5.5, 3.4, 0.0, 16.0, 0),
    "eye_irritation_score": (4.7, 2.8, 2.1, 0.0, 9.0, 0),
    "cc16_ug_l":            (11.7, 12.2, 3.0, 5.0, 20.0, 1),
    "cough_days_per_month": (5.6, 4.4, 3.5, 0.0, 15.0, 0),
}

# How strongly each outcome loads on a latent trait, in standard-deviation
# units of that outcome. The rest of each outcome's spread is independent.
IRRITATION_LOADING = {
    "feno_ppb": 0.45,
    "fev1_pct_pred": 0.0,
    "fvc_pct_pred": 0.0,
    "airway_symptom_score": 0.50,
    "eye_irritation_score": 0.40,
    "cc16_ug_l": -0.35,
    "cough_days_per_month": 0.40,
}
LUNG_LOADING = {
    "feno_ppb": 0.0,
    "fev1_pct_pred": 0.85,
    "fvc_pct_pred": 0.85,
    "airway_symptom_score": 0.0,
    "eye_irritation_score": 0.0,
    "cc16_ug_l": 0.0,
    "cough_days_per_month": 0.0,
}

COLUMNS = ["lifeguard_id", "pool_system"] + list(OUTCOMES)


def build_rows(rng):
    groups = ["chlorine_only"] * N_PER_GROUP + ["chlorine_uv"] * N_PER_GROUP
    groups = [groups[i] for i in rng.permutation(len(groups))]
    n = len(groups)

    irritation = rng.normal(0.0, 1.0, size=n)
    # Mildly worse spirometry in more irritated airways.
    lung = -0.25 * irritation + np.sqrt(1.0 - 0.25 ** 2) * rng.normal(0.0, 1.0, size=n)

    rows = []
    for i, group in enumerate(groups):
        row = {"lifeguard_id": "LG-%03d" % (i + 1), "pool_system": group}
        for name, (mu_cl, mu_uv, sd, lo, hi, dec) in OUTCOMES.items():
            mu = mu_cl if group == "chlorine_only" else mu_uv
            a = IRRITATION_LOADING[name]
            b = LUNG_LOADING[name]
            resid = np.sqrt(max(1.0 - a * a - b * b, 0.05))
            # Redraw the independent part until the value falls inside the
            # instrument's plausible range, so no value piles up on a bound.
            for _ in range(200):
                z = a * irritation[i] + b * lung[i] + resid * rng.normal()
                value = mu + sd * z
                if lo <= value <= hi:
                    break
            value = float(np.clip(value, lo, hi))
            row[name] = round(value, dec) if dec else int(round(value))
        rows.append(row)
    return rows


def main():
    rng = np.random.default_rng(SEED)
    rows = build_rows(rng)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lifeguard_airway.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %d rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
