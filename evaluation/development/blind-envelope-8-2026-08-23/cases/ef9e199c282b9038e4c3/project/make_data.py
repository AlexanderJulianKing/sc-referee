"""Generate the synthetic zebra finch song-bout dataset.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design mirrored by the generator
--------------------------------
14 adult male zebra finches, housed individually: 7 in a chronic low-frequency
noise room, 7 in a quiet room. Twelve complete song bouts recorded per bird
after six weeks => 168 rows, one row per bout.

Bout duration is drawn from a two-level model:

    duration_ij = mu[condition_i] + b_i + e_ij

where b_i is a stable per-bird offset (individual finches have characteristic
song lengths) and e_ij is bout-to-bout variation within a bird.

    mu[quiet] = 2.50 s      mu[noise] = 2.00 s
    SD(b_i)   = 0.42 s      SD(e_ij)  = 0.35 s

Durations are restricted to the plausible measurement range 0.8-4.2 s by
rejection sampling, so no values pile up on the boundary.
"""

import csv
import os
import random

SEED = 20260823

N_BIRDS_PER_GROUP = 7
N_BOUTS_PER_BIRD = 12

MEAN_QUIET_S = 2.50
MEAN_NOISE_S = 2.00
SD_BETWEEN_BIRDS_S = 0.42
SD_WITHIN_BIRD_S = 0.35

MIN_DURATION_S = 0.80
MAX_DURATION_S = 4.20

MIN_PEAK_KHZ = 2.50
MAX_PEAK_KHZ = 6.00

OUT_NAME = "zebra_finch_song_bouts.csv"


def clip(value, low, high):
    return max(low, min(high, value))


def draw_in_range(rng, mean, sd, low, high, max_tries=100):
    """Normal draw restricted to [low, high] by rejection.

    Rejection rather than clipping keeps the tails from piling up on the
    boundary, which would otherwise produce repeated identical values at the
    limits of the measurement range.
    """
    for _ in range(max_tries):
        value = rng.gauss(mean, sd)
        if low <= value <= high:
            return value
    return clip(rng.gauss(mean, sd), low, high)


def main():
    rng = random.Random(SEED)

    # Assign conditions to bird numbers 1..14 by shuffling, so group membership
    # is not confounded with the ordering of the identifiers.
    bird_numbers = list(range(1, 2 * N_BIRDS_PER_GROUP + 1))
    rng.shuffle(bird_numbers)
    noise_birds = set(bird_numbers[:N_BIRDS_PER_GROUP])

    birds = []
    for n in range(1, 2 * N_BIRDS_PER_GROUP + 1):
        condition = "noise" if n in noise_birds else "quiet"
        group_mean = MEAN_NOISE_S if condition == "noise" else MEAN_QUIET_S
        birds.append(
            {
                "bird_id": "BRD%02d" % n,
                "noise_condition": condition,
                # Stable per-bird deviation from the group mean.
                "bird_offset_s": rng.gauss(0.0, SD_BETWEEN_BIRDS_S),
                "group_mean_s": group_mean,
                # Age is a fixed attribute of the bird, repeated on each row.
                "age_days": rng.randint(180, 900),
                # Characteristic peak frequency of this bird's song.
                "bird_peak_khz": rng.gauss(4.30, 0.55),
                # Recording session start time, in minutes after midnight.
                "session_start_min": rng.randint(7 * 60 + 30, 11 * 60),
            }
        )

    rows = []
    for bird in birds:
        minute = bird["session_start_min"]
        for bout in range(1, N_BOUTS_PER_BIRD + 1):
            duration = draw_in_range(
                rng,
                bird["group_mean_s"] + bird["bird_offset_s"],
                SD_WITHIN_BIRD_S,
                MIN_DURATION_S,
                MAX_DURATION_S,
            )

            # Longer bouts contain more motifs; roughly one motif per ~0.5 s,
            # with rounding jitter. At least one motif per bout.
            motifs = int(round(duration / 0.50 + rng.gauss(0.0, 0.45)))
            motifs = max(1, motifs)

            peak = draw_in_range(
                rng, bird["bird_peak_khz"], 0.22, MIN_PEAK_KHZ, MAX_PEAK_KHZ
            )

            # Successive bouts of a session are a few minutes apart.
            minute += rng.randint(2, 9)
            recording_time = "%02d:%02d" % (minute // 60, minute % 60)

            rows.append(
                {
                    "bird_id": bird["bird_id"],
                    "noise_condition": bird["noise_condition"],
                    "bout_number": bout,
                    "bout_duration_s": round(duration, 3),
                    "motif_count": motifs,
                    "peak_frequency_khz": round(peak, 2),
                    "recording_time": recording_time,
                    "age_days": bird["age_days"],
                }
            )

    fieldnames = [
        "bird_id",
        "noise_condition",
        "bout_number",
        "bout_duration_s",
        "motif_count",
        "peak_frequency_khz",
        "recording_time",
        "age_days",
    ]

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
