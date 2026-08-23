"""Generate the synthetic tube-weaning feeding dataset.

Creates feeding_sessions.csv: 26 preterm infants (13 per protocol), six
consecutive oral feeding sessions per infant, 156 rows total.

Standard library only. Fixed seed, so the file is reproducible:
    /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260823
N_PER_GROUP = 13
N_SESSIONS = 6
OUT_NAME = "feeding_sessions.csv"

# Milk transfer rate model (millilitres per minute)
GROUP_MEAN = {"standard": 2.10, "new": 2.70}
BETWEEN_INFANT_SD = 0.42   # large, persistent differences between infants
WITHIN_INFANT_SD = 0.30    # session-to-session variation inside one infant
SESSION_GAIN = 0.055       # slight improvement per session as the infant matures
RATE_MIN, RATE_MAX = 0.8, 4.5

# Sessions are observed on consecutive days, so postmenstrual age creeps up.
PMA_STEP_WEEKS = 1.0 / 7.0


def make_infants(rng):
    """One record per infant: id, protocol, and its stable infant-level traits."""
    infants = []
    protocols = ["standard"] * N_PER_GROUP + ["new"] * N_PER_GROUP
    for i, protocol in enumerate(protocols, start=1):
        infants.append(
            {
                "infant_id": "INF%02d" % i,
                "protocol": protocol,
                # persistent offset for this baby, shared by all six of its rows
                "infant_offset": rng.gauss(0.0, BETWEEN_INFANT_SD),
                "birth_weight_g": int(round(rng.uniform(1100, 2300))),
                "pma_start_weeks": rng.uniform(34.0, 38.2),
                # typical length of an oral feed for this baby, in minutes
                "feed_minutes": rng.uniform(13.0, 24.0),
            }
        )
    rng.shuffle(infants)
    # Re-label so protocol is not simply the first 13 ids.
    for i, infant in enumerate(infants, start=1):
        infant["infant_id"] = "INF%02d" % i
    infants.sort(key=lambda r: r["infant_id"])
    return infants


def make_rows(infants, rng):
    """Six session rows per infant."""
    rows = []
    for infant in infants:
        base = GROUP_MEAN[infant["protocol"]] + infant["infant_offset"]
        for session in range(1, N_SESSIONS + 1):
            rate = base + SESSION_GAIN * (session - 1) + rng.gauss(0.0, WITHIN_INFANT_SD)
            rate = min(max(rate, RATE_MIN), RATE_MAX)

            pma = infant["pma_start_weeks"] + PMA_STEP_WEEKS * (session - 1)
            pma = min(max(pma, 34.0), 39.0)

            minutes = infant["feed_minutes"] * rng.uniform(0.85, 1.15)
            volume = rate * minutes

            rows.append(
                {
                    "infant_id": infant["infant_id"],
                    "protocol": infant["protocol"],
                    "session_number": session,
                    "transfer_rate_ml_per_min": round(rate, 2),
                    "pma_weeks": round(pma, 1),
                    "birth_weight_g": infant["birth_weight_g"],
                    "volume_taken_ml": round(volume, 1),
                }
            )
    return rows


def main():
    rng = random.Random(SEED)
    infants = make_infants(rng)
    rows = make_rows(infants, rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fields = [
        "infant_id",
        "protocol",
        "session_number",
        "transfer_rate_ml_per_min",
        "pma_weeks",
        "birth_weight_g",
        "volume_taken_ml",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows, %d infants)" % (out_path, len(rows), len(infants)))


if __name__ == "__main__":
    main()
