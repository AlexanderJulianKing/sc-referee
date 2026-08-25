"""Generate the alpine marmot piste-disturbance field dataset.

Deterministic: a fixed seed reproduces marmots.csv byte for byte.

Fifty-eight adult marmots trapped, measured once and released over one summer
season; twenty-nine from colonies whose burrow systems sit within 100 m of a
groomed piste and twenty-nine from undisturbed alpine meadow colonies at
similar elevation and aspect. Five outcomes are recorded per animal.

This script only writes the field data file. It performs no comparison
between the two colony types.
"""

import csv
import os

import numpy as np

SEED = 20260824
N_PER_GROUP = 29

# Plausible field ranges from the trapping protocol; values are clipped to
# these limits so that no recorded measurement falls outside the instrument
# and observation windows actually used.
LIMITS = {
    "body_mass_kg": (2.8, 5.6),
    "fgm_ng_per_g": (50.0, 400.0),
    "emergence_doy": (95, 135),
    "vigilance_pct": (3.0, 30.0),
    "ectoparasite_count": (0, 25),
}

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marmots.csv")


def draw_group(rng, n, params):
    """Draw one colony type's five outcomes for n marmots."""
    mass = rng.normal(params["mass_mu"], params["mass_sd"], n)

    # Glucocorticoid metabolites are right-skewed in faecal assays, so draw on
    # the log scale and exponentiate.
    fgm = np.exp(rng.normal(params["fgm_log_mu"], params["fgm_log_sd"], n))

    emergence = rng.normal(params["emerg_mu"], params["emerg_sd"], n)

    # Vigilance is a bounded percentage of the observation period and is also
    # right-skewed; gamma keeps it positive with a long upper tail.
    shape = (params["vig_mu"] / params["vig_sd"]) ** 2
    scale = params["vig_sd"] ** 2 / params["vig_mu"]
    vigilance = rng.gamma(shape, scale, n)

    # Ectoparasite burdens are overdispersed counts: Poisson counts with a
    # gamma-distributed individual susceptibility (negative binomial).
    susceptibility = rng.gamma(params["tick_shape"], 1.0 / params["tick_shape"], n)
    ticks = rng.poisson(params["tick_mu"] * susceptibility)

    return {
        "body_mass_kg": np.round(np.clip(mass, *LIMITS["body_mass_kg"]), 2),
        "fgm_ng_per_g": np.round(np.clip(fgm, *LIMITS["fgm_ng_per_g"]), 1),
        "emergence_doy": np.clip(np.rint(emergence), *LIMITS["emergence_doy"]).astype(int),
        "vigilance_pct": np.round(np.clip(vigilance, *LIMITS["vigilance_pct"]), 1),
        "ectoparasite_count": np.clip(ticks, *LIMITS["ectoparasite_count"]).astype(int),
    }


# Colony-type parameters. Piste-adjacent animals carry a modestly lower
# pre-hibernation mass, higher glucocorticoid metabolites and more vigilance;
# emergence timing and ectoparasite burden are set to differ little between
# the two colony types.
PISTE = {
    "mass_mu": 4.02,
    "mass_sd": 0.46,
    "fgm_log_mu": np.log(196.0),
    "fgm_log_sd": 0.34,
    "emerg_mu": 115.4,
    "emerg_sd": 7.6,
    "vig_mu": 15.1,
    "vig_sd": 5.2,
    "tick_mu": 8.4,
    "tick_shape": 4.0,
}

UNDISTURBED = {
    "mass_mu": 4.38,
    "mass_sd": 0.44,
    "fgm_log_mu": np.log(152.0),
    "fgm_log_sd": 0.32,
    "emerg_mu": 114.1,
    "emerg_sd": 7.9,
    "vig_mu": 11.6,
    "vig_sd": 4.3,
    "tick_mu": 7.9,
    "tick_shape": 4.0,
}

FIELDS = [
    "marmot_id",
    "disturbance_group",
    "body_mass_kg",
    "fgm_ng_per_g",
    "emergence_doy",
    "vigilance_pct",
    "ectoparasite_count",
]


def main():
    rng = np.random.default_rng(SEED)

    piste = draw_group(rng, N_PER_GROUP, PISTE)
    undisturbed = draw_group(rng, N_PER_GROUP, UNDISTURBED)

    rows = []
    for i in range(N_PER_GROUP):
        rows.append(("piste_adjacent", {k: v[i] for k, v in piste.items()}))
    for i in range(N_PER_GROUP):
        rows.append(("undisturbed", {k: v[i] for k, v in undisturbed.items()}))

    # Trapping alternated between colony types through the season, so the
    # capture order in the field notebook is not blocked by group.
    order = rng.permutation(len(rows))
    rows = [rows[i] for i in order]

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        for n, (group, vals) in enumerate(rows, start=1):
            writer.writerow(
                [
                    "MAR-{:03d}".format(n),
                    group,
                    "{:.2f}".format(vals["body_mass_kg"]),
                    "{:.1f}".format(vals["fgm_ng_per_g"]),
                    int(vals["emergence_doy"]),
                    "{:.1f}".format(vals["vigilance_pct"]),
                    int(vals["ectoparasite_count"]),
                ]
            )

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
