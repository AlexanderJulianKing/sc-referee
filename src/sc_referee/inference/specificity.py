"""Hard-decoy specificity harness (§7).

The decoys that shipped with GB-P07 -- sex, age, bmi -- are donor-level CONSTANTS. A cell-level gate
cannot move a donor constant, so they are immune to the risky path by construction: they are a smoke
test for schema handling, not a specificity measurement. A constant that cannot be fooled proves
nothing about a diagnostic whose danger is cell-level evaluation -> gate -> aggregation -> correlate.

A HARD decoy travels that whole path and is causally null by construction:

* take a real cell-level nuisance column (preserving its within-donor variance, cell counts,
  missingness, and gate-survival distribution);
* randomly reassign whole donors' blocks among donors, independent of genotype and outcome;
* run it through the same gate and the same leg-1 calibration.

Because the reassignment is independent of the exposure, any association it shows is null -- finite
sample, aggregation, gate structure, or multiplicity. The family-wise false-positive rate over
independently generated null families is the number that decides whether leg 1 may ever phrase a
finding as more than
"associated". If the permutation calibration (§5.1) is honest, the scan-wide false-positive rate
sits at or below its nominal level.

This module renders no judgment about any analysis. It measures the diagnostic itself.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sc_referee.inference.calibration import calibrate


@dataclass(frozen=True)
class SpecificityResult:
    n_decoys_per_family: int
    n_families: int
    alpha: float
    per_test_false_positive_rate: float
    within_family_rejected_fraction: float
    family_wise_error_rate: float
    fwer_ci_low: float
    fwer_ci_high: float
    n_permutations: int
    seed: int

    @property
    def n_decoys(self) -> int:
        """Backward-compatible count, now explicitly interpreted per null family."""
        return self.n_decoys_per_family

    def as_dict(self) -> dict:
        return {
            "n_decoys_per_family": self.n_decoys_per_family,
            "n_families": self.n_families,
            "alpha": self.alpha,
            "per_test_false_positive_rate": round(self.per_test_false_positive_rate, 4),
            "within_family_rejected_fraction": round(self.within_family_rejected_fraction, 4),
            "family_wise_error_rate": round(self.family_wise_error_rate, 4),
            "fwer_95pct_ci": [round(self.fwer_ci_low, 4), round(self.fwer_ci_high, 4)],
            "n_permutations": self.n_permutations,
            "seed": self.seed,
            "note": "Each independently generated null family contributes one FWER event: whether "
                    "any scan-wide-adjusted decoy was rejected. The within-family rejected fraction "
                    "is descriptive and is not labelled FWER.",
        }


def _wilson_interval(events: int, families: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if families <= 0:
        return 0.0, 1.0
    p = events / families
    denominator = 1 + z * z / families
    centre = (p + z * z / (2 * families)) / denominator
    margin = z * np.sqrt(p * (1 - p) / families + z * z / (4 * families * families)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _summarize_families(per_test_families, scanwide_families, alpha):
    per_test = [p for family in per_test_families for p in family]
    scanwide = [p for family in scanwide_families for p in family]
    events = sum(any(p < alpha for p in family) for family in scanwide_families)
    n_families = len(scanwide_families)
    low, high = _wilson_interval(events, n_families)
    return (
        sum(p < alpha for p in per_test) / max(len(per_test), 1),
        sum(p < alpha for p in scanwide) / max(len(scanwide), 1),
        events / max(n_families, 1),
        low,
        high,
    )


def _block_permute(cell_values, cell_unit, cell_exposure, rng):
    """Reassign whole units' value-blocks among units, holding block contents intact.

    Preserves within-unit variance, block sizes, and the value distribution. Destroys any real
    association between the candidate and the exposure, because the block a unit receives is chosen
    independent of that unit's exposure.
    """
    units = list(dict.fromkeys(cell_unit))
    perm = rng.permutation(len(units))
    remap = {units[i]: units[perm[i]] for i in range(len(units))}
    # each unit u now carries the block that originally belonged to remap[u]
    src_blocks = {u: cell_values[cell_unit == u] for u in units}
    out = np.empty_like(cell_values, dtype=float)
    for u in units:
        idx = np.where(cell_unit == u)[0]
        block = src_blocks[remap[u]]
        # tile/truncate the source block to this unit's cell count (sizes may differ)
        take = np.resize(block, len(idx))
        out[idx] = take
    return out


def run(cell_values, cell_unit, cell_exposure, *, n_decoys=200, alpha=0.05,
        gate_mask=None, n_permutations=2000, n_families=20,
        seed=20260717) -> SpecificityResult:
    """Measure the false-positive rate of leg-1 calibration over hard decoys.

    `cell_values`/`cell_unit`/`cell_exposure` are cell-level arrays. `gate_mask`, if given, is a
    boolean cell-level array = the analyst's subsetting; the decoy is evaluated on the gated
    population, so the decoy travels the real risky path.
    """
    if isinstance(n_families, bool) or not isinstance(n_families, int) or n_families < 1:
        raise ValueError("n_families must be a positive integer predeclared before the run")
    if isinstance(n_decoys, bool) or not isinstance(n_decoys, int) or n_decoys < 1:
        raise ValueError("n_decoys must be a positive integer per family")
    cell_values = np.asarray(cell_values, dtype=float)
    cell_unit = np.asarray(cell_unit)
    cell_exposure = np.asarray(cell_exposure, dtype=float)
    if gate_mask is not None:
        m = np.asarray(gate_mask, dtype=bool)
        cell_values, cell_unit, cell_exposure = cell_values[m], cell_unit[m], cell_exposure[m]

    units = list(dict.fromkeys(cell_unit))
    expo_by_unit = np.array([cell_exposure[cell_unit == u][0] for u in units], dtype=float)

    per_test_families, scanwide_families = [], []
    seeds = np.random.SeedSequence(seed).spawn(n_families)
    for family_seed in seeds:
        rng = np.random.default_rng(family_seed)
        summaries = {}
        for d in range(n_decoys):
            decoy = _block_permute(cell_values, cell_unit, cell_exposure, rng)
            per_unit = np.array([decoy[cell_unit == u].mean() for u in units], dtype=float)
            summaries[f"decoy{d}"] = per_unit
        calibration_seed = int(family_seed.generate_state(1, dtype=np.uint32)[0])
        cal = calibrate(summaries, expo_by_unit, n_permutations=n_permutations,
                        seed=calibration_seed)
        per_test_families.append(tuple(
            c.permutation_p for c in cal.values() if c.permutation_p is not None
        ))
        scanwide_families.append(tuple(
            c.scanwide_p for c in cal.values() if c.scanwide_p is not None
        ))

    per_test_rate, within_family_rate, fwer, ci_low, ci_high = _summarize_families(
        per_test_families, scanwide_families, alpha
    )
    return SpecificityResult(
        n_decoys_per_family=n_decoys,
        n_families=n_families,
        alpha=alpha,
        per_test_false_positive_rate=per_test_rate,
        within_family_rejected_fraction=within_family_rate,
        family_wise_error_rate=fwer,
        fwer_ci_low=ci_low,
        fwer_ci_high=ci_high,
        n_permutations=n_permutations, seed=seed,
    )
